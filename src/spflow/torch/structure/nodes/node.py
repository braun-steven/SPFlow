"""
Created on May 27, 2021

@authors: Philipp Deibert

This file provides the torch variants of individual graph nodes.
"""
from abc import ABC
from typing import List, Union, Optional, Iterable
from copy import deepcopy

import torch
import numpy as np

from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.contexts.dispatch_context import DispatchContext, init_default_dispatch_context
from spflow.meta.scope.scope import Scope
from spflow.base.structure.nodes.node import SPNSumNode as BaseSPNSumNode
from spflow.base.structure.nodes.node import SPNProductNode as BaseSPNProductNode
from spflow.torch.structure.module import Module


# TODO: put projections somewhere else
def proj_convex_to_real(x: torch.Tensor) -> torch.Tensor:
    # convex coefficients are already normalized, so taking the log is sufficient
    return torch.log(x)


def proj_real_to_convex(x: torch.Tensor) -> torch.Tensor:
    return torch.nn.functional.softmax(x, dim=-1)


class Node(Module, ABC):
    """Torch version of an abstract node.

    Args:
        children: list of child modules (defaults to empty list).
    """
    def __init__(self, children: Optional[List[Module]]=None, **kwargs) -> None:
        """TODO"""
        if(children is None):
            children = []

        super(Node, self).__init__(children=children, **kwargs)

    @property
    def n_out(self) -> int:
        """Returns the number of outputs for this module. Returns one since nodes represent a single output."""
        return 1
    
    @property
    def scopes_out(self) -> List[Scope]:
        return [self.scope]


@dispatch(memoize=True)
def marginalize(node: Node, marg_rvs: Iterable[int], prune: bool=True, dispatch_ctx: Optional[DispatchContext]=None) -> Union[Node,None]:
    """TODO"""
    # initialize dispatch context
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    # compute node scope (node only has single output)
    node_scope = node.scope

    mutual_rvs = set(node_scope.query).intersection(set(marg_rvs))

    # node scope is being fully marginalized
    if(len(mutual_rvs) == len(node_scope.query)):
        return None
    # node scope is being partially marginalized
    elif mutual_rvs:
        raise NotImplementedError("Partial marginalization of 'Node' is not implemented for generic nodes. Dispatch an appropriate implementation for a specific node type.")
    else:
        return deepcopy(node)


class SPNSumNode(Node):
    """Torch version of a sum node.

    Args:
        children: non-empty list of child modules.
        weights: optional zero-dimensional float list, numpy array, or torch tensor containing non-negative weights for each child (defaults to 'None' in which case weights are initialized to random weights in (0,1) summing up to one).
    """
    def __init__(self, children: List[Module], weights: Optional[Union[np.ndarray, torch.Tensor, List[float]]]=None) -> None:
        """TODO"""
        super(SPNSumNode, self).__init__(children=children)

        if not children:
            raise ValueError("'SPNSumNode' requires at least one child to be specified.")
        
        scope = None

        for child in children:
            for s in child.scopes_out:
                if(scope is None):
                    scope = s
                else:
                    if not scope.equal_query(s):
                        raise ValueError(f"'SPNSumNode' requires child scopes to have the same query variables.")
                
                scope = scope.union(s)

        self.scope = scope
        self.n_in = sum(child.n_out for child in children)

        if weights is None:
            weights = torch.rand(self.n_in) + 1e-08  # avoid zeros
            weights /= weights.sum()

        # register auxiliary parameters for weights as torch parameters
        self.weights_aux = torch.nn.Parameter()
        # initialize weights
        self.weights = weights

    @property
    def weights(self) -> torch.Tensor:
        """TODO"""
        # project auxiliary weights onto weights that sum up to one
        return proj_real_to_convex(self.weights_aux)

    @weights.setter
    def weights(self, values: Union[np.ndarray, torch.Tensor, List[float]]) -> None:
        """TODO"""
        if isinstance(values, list) or isinstance(values, np.ndarray):
            values = torch.tensor(values).float()
        if(values.ndim != 1):
            raise ValueError(f"Torch tensor of weight values for 'SPNSumNode' is expected to be one-dimensional, but is {values.ndim}-dimensional.")
        if not torch.all(values > 0):
            raise ValueError("Weights for 'SPNSumNode' must be all positive.")
        if not torch.isclose(values.sum(), torch.tensor(1.0, dtype=values.dtype)):
            raise ValueError("Weights for 'SPNSumNode' must sum up to one.")
        if not len(values) == self.n_in:
            raise ValueError("Number of weights for 'SPNSumNode' does not match total number of child outputs.")

        self.weights_aux.data = proj_convex_to_real(values)


@dispatch(memoize=True)
def marginalize(sum_node: SPNSumNode, marg_rvs: Iterable[int], prune: bool=True, dispatch_ctx: Optional[DispatchContext]=None):
    """TODO"""
    # initialize dispatch context
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    # compute node scope (node only has single output)
    node_scope = sum_node.scope

    mutual_rvs = set(node_scope.query).intersection(set(marg_rvs))

    # node scope is being fully marginalized
    if(len(mutual_rvs) == len(node_scope.query)):
        return None
    # node scope is being partially marginalized
    elif mutual_rvs:
        marg_children = []

        # marginalize child modules
        for child in sum_node.children():
            marg_child = marginalize(child, marg_rvs, prune=prune, dispatch_ctx=dispatch_ctx)

            # if marginalized child is not None
            if marg_child:
                marg_children.append(marg_child)
        
        return SPNSumNode(children=marg_children, weights=sum_node.weights)
    else:
        return deepcopy(sum_node)


@dispatch(memoize=True)
def toBase(sum_node: SPNSumNode, dispatch_ctx: Optional[DispatchContext]=None) -> BaseSPNSumNode:
    """TODO"""
    return BaseSPNSumNode(children=[toBase(child, dispatch_ctx=dispatch_ctx) for child in sum_node.children()], weights=sum_node.weights.detach().numpy())


@dispatch(memoize=True)
def toTorch(sum_node: BaseSPNSumNode, dispatch_ctx: Optional[DispatchContext]=None) -> SPNSumNode:
    """TODO"""
    return SPNSumNode(children=[toTorch(child, dispatch_ctx=dispatch_ctx) for child in sum_node.children], weights=sum_node.weights)


class SPNProductNode(Node):
    """Torch version of a product node.

    Args:
        children: non-empty list of child modules.
    """
    def __init__(self, children: List[Module]) -> None:
        """TODO"""
        super(SPNProductNode, self).__init__(children=children)

        if not children:
            raise ValueError("'SPNProductNode' requires at least one child to be specified.")

        scope = Scope()

        for child in children:
            for s in child.scopes_out:
                if not scope.isdisjoint(s):
                    raise ValueError(f"'SPNProductNode' requires child scopes to be pair-wise disjoint.")

                scope = scope.union(s)

        self.scope = scope


@dispatch(memoize=True)
def marginalize(product_node: SPNProductNode, marg_rvs: Iterable[int], prune: bool=True, dispatch_ctx: Optional[DispatchContext]=None) -> Union[Node,None]:
    """TODO"""
    # initialize dispatch context
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    # compute node scope (node only has single output)
    node_scope = product_node.scope

    mutual_rvs = set(node_scope.query).intersection(set(marg_rvs))

    # node scope is being fully marginalized
    if(len(mutual_rvs) == len(node_scope.query)):
        return None
    # node scope is being partially marginalized
    elif mutual_rvs:
        marg_children = []

        # marginalize child modules
        for child in product_node.children():
            marg_child = marginalize(child, marg_rvs, prune=prune, dispatch_ctx=dispatch_ctx)

            # if marginalized child is not None
            if marg_child:
                marg_children.append(marg_child)
        
        # if product node has only one child after marginalization and pruning is true, return child directly
        if(len(marg_children) == 1 and prune):
            return marg_children[0]
        else:
            return SPNProductNode(marg_children)
    else:
        return deepcopy(product_node)


@dispatch(memoize=True)
def toBase(product_node: SPNProductNode, dispatch_ctx: Optional[DispatchContext]=None) -> BaseSPNProductNode:
    """TODO"""
    return BaseSPNProductNode(children=[toBase(child, dispatch_ctx=dispatch_ctx) for child in product_node.children()])


@dispatch(memoize=True)
def toTorch(product_node: BaseSPNProductNode, dispatch_ctx: Optional[DispatchContext]=None) -> SPNProductNode:
    """TODO"""
    return SPNProductNode(children=[toTorch(child, dispatch_ctx=dispatch_ctx) for child in product_node.children])


class LeafNode(Node, ABC):
    """Torch version of an abstract leaf node.

    Args:
        scope: 'Scope' object representing the scope of this leaf node.
    """
    def __init__(self, scope: Scope, **kwargs) -> None:
        """TODO"""
        super(LeafNode, self).__init__(children=[], **kwargs)

        self.scope = scope