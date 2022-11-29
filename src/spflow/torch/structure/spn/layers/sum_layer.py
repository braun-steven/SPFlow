"""Contains SPN-like sum layer for SPFlow in the ``torch`` backend.
"""
from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.dispatch.dispatch_context import (
    DispatchContext,
    init_default_dispatch_context,
)
from spflow.meta.data.scope import Scope
from spflow.torch.structure.module import Module
from spflow.torch.structure.spn.nodes.sum_node import (
    proj_real_to_convex,
    proj_convex_to_real,
)
from spflow.base.structure.spn.layers.sum_layer import (
    SumLayer as BaseSumLayer,
)

from typing import List, Union, Optional, Iterable
from copy import deepcopy
import numpy as np
import torch


class SumLayer(Module):
    r"""Layer representing multiple SPN-like sum nodes over all children in the 'base' backend.

    Represents multiple convex combinations of its children over the same scope.
    Internally, the weights are represented as unbounded parameters that are projected onto convex combination for each node, representing the actual weights.

    Methods:
        children():
            Iterator over all modules that are children to the module in a directed graph.

    Attributes:
        weights_aux:
            Two-dimensional PyTorch tensor containing weights for each input and node.
            Each row corresponds to a node.
        weights:
            Two-dimensional PyTorch tensor containing non-negative weights for each input and node, summing up to one (projected from 'weights_aux').
            Each row corresponds to a node.
        n_out:
            Integer indicating the number of outputs. Equal to the number of nodes represented by the layer.
        scopes_out:
            List of scopes representing the output scopes.
    """

    def __init__(
        self,
        n_nodes: int,
        children: List[Module],
        weights: Optional[
            Union[np.ndarray, torch.Tensor, List[List[float]], List[float]]
        ] = None,
        **kwargs,
    ) -> None:
        r"""Initializes ``SumLayer`` object.

        Args:
            n_nodes:
                Integer specifying the number of nodes the layer should represent.
            children:
                Non-empty list of modules that are children to the layer.
                The output scopes for all child modules need to be equal.
            weights:
                Optional list of floats, list of lists of floats, one- to two-dimensional NumPy array or two-dimensional
                PyTorch tensor containing non-negative weights. There should be weights for each of the node and inputs.
                Each row corresponds to a sum node and values should sum up to one. If it is a list of floats, a one-dimensional
                NumPy array or a one-dimensonal PyTorch tensor, the same weights are reused for all sum nodes.
                Defaults to 'None' in which case weights are initialized to random weights in (0,1) and normalized per row.

        Raises:
            ValueError: Invalid arguments.
        """
        if n_nodes < 1:
            raise ValueError(
                "Number of nodes for 'SumLayer' must be greater of equal to 1."
            )

        if not children:
            raise ValueError(
                "'SumLayer' requires at least one child to be specified."
            )

        super().__init__(children=children, **kwargs)

        self._n_out = n_nodes
        self.n_in = sum(child.n_out for child in self.children())

        # parse weights
        if weights is None:
            weights = torch.rand(self.n_out, self.n_in) + 1e-08  # avoid zeros
            weights /= weights.sum(dim=-1, keepdims=True)

        # register auxiliary parameters for weights as torch parameters
        self.weights_aux = torch.nn.Parameter()
        # initialize weights
        self.weights = weights

        # compute scope
        scope = None

        for child in children:
            for s in child.scopes_out:
                if scope is None:
                    scope = s
                else:
                    if not scope.equal_query(s):
                        raise ValueError(
                            f"'SumLayer' requires child scopes to have the same query variables."
                        )

                scope = scope.join(s)

        self.scope = scope

    @property
    def n_out(self) -> int:
        """Returns the number of outputs for this module. Equal to the number of nodes represented by the layer."""
        return self._n_out

    @property
    def scopes_out(self) -> List[Scope]:
        """Returns the output scopes this layer represents."""
        return [self.scope for _ in range(self.n_out)]

    @property
    def weights(self) -> np.ndarray:
        """Returns the weights of all nodes as a two-dimensional PyTorch tensor."""
        # project auxiliary weights onto weights that sum up to one
        return proj_real_to_convex(self.weights_aux)

    @weights.setter
    def weights(
        self,
        values: Union[np.ndarray, torch.Tensor, List[List[float]], List[float]],
    ) -> None:
        """Sets the weights of all nodes to specified values.

        Args:
            values:
                List of floats, list of lists of floats, one- to two-dimensional NumPy array or two-dimensional
                PyTorch tensor containing non-negative weights. There should be weights for each of the node and inputs.
                Each row corresponds to a sum node and values should sum up to one. If it is a list of floats, a one-dimensional
                NumPy array or a one-dimensonal PyTorch tensor, the same weights are reused for all sum nodes.
                Defaults to 'None' in which case weights are initialized to random weights in (0,1) and normalized per row.

        Raises:
            ValueError: Invalid values.
        """
        if isinstance(values, list) or isinstance(values, np.ndarray):
            values = torch.tensor(values).type(torch.get_default_dtype())
        if values.ndim != 1 and values.ndim != 2:
            raise ValueError(
                f"Torch tensor of weight values for 'SumLayer' is expected to be one- or two-dimensional, but is {values.ndim}-dimensional."
            )
        if not torch.all(values > 0):
            raise ValueError("Weights for 'SumLayer' must be all positive.")
        if not torch.allclose(values.sum(dim=-1), torch.tensor(1.0)):
            raise ValueError(
                "Weights for 'SumLayer' must sum up to one in last dimension."
            )
        if not (values.shape[-1] == self.n_in):
            raise ValueError(
                "Number of weights for 'SumLayer' in last dimension does not match total number of child outputs."
            )

        # same weights for all sum nodes
        if values.ndim == 1:
            self.weights_aux.data = proj_convex_to_real(
                values.repeat((self.n_out, 1)).clone()
            )
        if values.ndim == 2:
            # same weights for all sum nodes
            if values.shape[0] == 1:
                self.weights_aux.data = proj_convex_to_real(
                    values.repeat((self.n_out, 1)).clone()
                )
            # different weights for all sum nodes
            elif values.shape[0] == self.n_out:
                self.weights_aux.data = proj_convex_to_real(values.clone())
            # incorrect number of specified weights
            else:
                raise ValueError(
                    f"Incorrect number of weights for 'SumLayer'. Size of first dimension must be either 1 or {self.n_out}, but is {values.shape[0]}."
                )


@dispatch(memoize=True)  # type: ignore
def marginalize(
    layer: SumLayer,
    marg_rvs: Iterable[int],
    prune: bool = True,
    dispatch_ctx: Optional[DispatchContext] = None,
) -> Union[None, SumLayer]:
    """Structural marginalization for SPN-like sum layer objects in the ``torch`` backend.

    Structurally marginalizes the specified layer module.
    If the layer's scope contains non of the random variables to marginalize, then the layer is returned unaltered.
    If the layer's scope is fully marginalized over, then None is returned.
    If the layer's scope is partially marginalized over, then a new sum layer over the marginalized child modules is returned.

    Args:
        layer:
            Layer module to marginalize.
        marg_rvs:
            Iterable of integers representing the indices of the random variables to marginalize.
        prune:
            Boolean indicating whether or not to prune nodes and modules where possible.
            Has no effect here. Defaults to True.
        dispatch_ctx:
            Optional dispatch context.

    Returns:
        (Marginalized) sum layer or None if it is completely marginalized.
    """
    # initialize dispatch context
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    # compute node scope (node only has single output)
    layer_scope = layer.scope

    mutual_rvs = set(layer_scope.query).intersection(set(marg_rvs))

    # node scope is being fully marginalized
    if len(mutual_rvs) == len(layer_scope.query):
        return None
    # node scope is being partially marginalized
    elif mutual_rvs:
        # TODO: pruning
        marg_children = []

        # marginalize child modules
        for child in layer.children():
            marg_child = marginalize(
                child, marg_rvs, prune=prune, dispatch_ctx=dispatch_ctx
            )

            # if marginalized child is not None
            if marg_child:
                marg_children.append(marg_child)

        return SumLayer(
            n_nodes=layer.n_out, children=marg_children, weights=layer.weights
        )
    else:
        return deepcopy(layer)


@dispatch(memoize=True)  # type: ignore
def toBase(
    sum_layer: SumLayer, dispatch_ctx: Optional[DispatchContext] = None
) -> BaseSumLayer:
    """Conversion for ``SumLayer`` from ``torch`` backend to ``base`` backend.

    Args:
        sum_layer:
            Layer to be converted.
        dispatch_ctx:
            Dispatch context.
    """
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)
    return BaseSumLayer(
        n_nodes=sum_layer.n_out,
        children=[
            toBase(child, dispatch_ctx=dispatch_ctx)
            for child in sum_layer.children()
        ],
        weights=sum_layer.weights.detach().cpu().numpy(),
    )


@dispatch(memoize=True)  # type: ignore
def toTorch(
    sum_layer: BaseSumLayer, dispatch_ctx: Optional[DispatchContext] = None
) -> SumLayer:
    """Conversion for ``SumLayer`` from ``base`` backend to ``torch`` backend.

    Args:
        sum_layer:
            Layer to be converted.
        dispatch_ctx:
            Dispatch context.
    """
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)
    return SumLayer(
        n_nodes=sum_layer.n_out,
        children=[
            toTorch(child, dispatch_ctx=dispatch_ctx)
            for child in sum_layer.children
        ],
        weights=sum_layer.weights,
    )