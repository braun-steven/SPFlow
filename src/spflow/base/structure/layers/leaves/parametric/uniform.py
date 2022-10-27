# -*- coding: utf-8 -*-
"""Contains conditional Uniform leaf node for SPFlow in the ``base`` backend.
"""
from typing import List, Union, Optional, Iterable, Tuple
import numpy as np

from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.contexts.dispatch_context import DispatchContext, init_default_dispatch_context
from spflow.meta.scope.scope import Scope
from spflow.base.structure.module import Module
from spflow.base.structure.nodes.leaves.parametric.uniform import Uniform


class UniformLayer(Module):
    r"""Layer of multiple (univariate) continuous Uniform distribution leaf nodes in the ``base`` backend.

    Represents multiple univariate Poisson distributions with independent scopes, each with the following probability distribution function (PDF):

    .. math::

        \text{PDF}(x) = \frac{1}{\text{end} - \text{start}}\mathbf{1}_{[\text{start}, \text{end}]}(x)

    where
        - :math:`x` is the input observation
        - :math:`\mathbf{1}_{[\text{start}, \text{end}]}` is the indicator function for the given interval (evaluating to 0 if x is not in the interval)

    Attributes:
        start:
            One-dimensional NumPy array containing the start of the intervals (including).
        end:
            One-dimensional NumPy array containing the end of the intervals (including). Must be larger than 'start'.
        support_outside:
            One-dimensional NumPy array containing booleans indicating whether or not values outside of the intervals are part of the support.
    """
    def __init__(self, scope: Union[Scope, List[Scope]], start: Union[int, float, List[float], np.ndarray], end: Union[int, float, List[float], np.ndarray], support_outside: Union[bool, List[bool], np.ndarray]=True, n_nodes: int=1, **kwargs) -> None:
        r"""Initializes ``UniformLayer`` leaf node.

        Args:
            scope:
                Scope object specifying the scope of the distribution.
            start:
                Floating point, list of floats or one-dimensional NumPy array containing the start of the intervals (including).
                If a single floating point value is given, it is broadcast to all nodes.
            end:
                Floating point, list of floats or one-dimensional NumPy array containing the end of the intervals (including). Must be larger than 'start'.
                If a single floating point value is given, it is broadcast to all nodes.
            support_outside:
                Boolean, list of booleans or one-dimensional NumPy array containing booleans indicating whether or not values outside of the intervals are part of the support.
                If a single boolean value is given, it is broadcast to all nodes.
                Defaults to True.
        """
        if isinstance(scope, Scope):
            if n_nodes < 1:
                raise ValueError(f"Number of nodes for 'UniformLayer' must be greater or equal to 1, but was {n_nodes}")

            scope = [scope for _ in range(n_nodes)]
            self._n_out = n_nodes
        else:
            if len(scope) == 0:
                raise ValueError("List of scopes for 'UniformLayer' was empty.")

            self._n_out = len(scope)

        super(UniformLayer, self).__init__(children=[], **kwargs)

        # create leaf nodes
        self.nodes = [Uniform(s, 0.0, 1.0) for s in scope]

        # compute scope
        self.scopes_out = scope

        # parse weights
        self.set_params(start, end, support_outside)

    @property
    def n_out(self) -> int:
        """Returns the number of outputs for this module. Equal to the number of nodes represented by the layer."""
        return self._n_out

    @property
    def start(self) -> np.ndarray:
        """Returns the starts of the intervals of the represented distributions."""
        return np.array([node.start for node in self.nodes])
    
    @property
    def end(self) -> np.ndarray:
        """Returns the ends of the intervals of the represented distributions."""
        return np.array([node.end for node in self.nodes])
    
    @property
    def support_outside(self) -> np.ndarray:
        """Returns the booleans indicating whether or not values outside of the intervals are part of the supports of the represented distributions."""
        return np.array([node.support_outside for node in self.nodes])

    def set_params(self, start: Union[int, float, List[float], np.ndarray], end: Union[int, float, List[float], np.ndarray], support_outside: Union[bool, List[bool], np.ndarray]=True) -> None:
        """Sets the parameters for the represented distributions in the ``base`` backend.

        Args:
            start:
                Floating point, list of floats or one-dimensional NumPy array containing the start of the intervals (including).
                If a single floating point value is given, it is broadcast to all nodes.
            end:
                Floating point, list of floats or one-dimensional NumPy array containing the end of the intervals (including). Must be larger than 'start'.
                If a single floating point value is given, it is broadcast to all nodes.
            support_outside:
                Boolean, list of booleans or one-dimensional NumPy array containing booleans indicating whether or not values outside of the intervals are part of the support.
                If a single boolean value is given, it is broadcast to all nodes.
                Defaults to True.
        """
        if isinstance(start, int) or isinstance(start, float):
            start = np.array([float(start) for _ in range(self.n_out)])
        if isinstance(start, list):
            start = np.array(start)
        if(start.ndim != 1):
            raise ValueError(f"Numpy array of start values for 'UniformLayer' is expected to be one-dimensional, but is {start.ndim}-dimensional.")
        if(start.shape[0] != self.n_out):
            raise ValueError(f"Length of numpy array of start values for 'UniformLayer' must match number of output nodes {self.n_out}, but is {start.shape[0]}")

        if isinstance(end, int) or isinstance(end, float):
            end = np.array([float(end) for _ in range(self.n_out)])
        if isinstance(end, list):
            end = np.array(end)
        if(end.ndim != 1):
            raise ValueError(f"Numpy array of end values for 'UniformLayer' is expected to be one-dimensional, but is {end.ndim}-dimensional.")
        if(end.shape[0] != self.n_out):
            raise ValueError(f"Length of numpy array of end values for 'UniformLayer' must match number of output nodes {self.n_out}, but is {end.shape[0]}")

        if isinstance(support_outside, bool):
            support_outside = np.array([support_outside for _ in range(self.n_out)])
        if isinstance(support_outside, list):
            support_outside = np.array(support_outside)
        if(support_outside.ndim != 1):
            raise ValueError(f"Numpy array of 'support_outside' values for 'UniformLayer' is expected to be one-dimensional, but is {support_outside.ndim}-dimensional.")
        if(support_outside.shape[0] != self.n_out):
            raise ValueError(f"Length of numpy array of 'support_outside' values for 'UniformLayer' must match number of output nodes {self.n_out}, but is {support_outside.shape[0]}")

        for node_start, node_end, node_support_outside, node in zip(start, end, support_outside, self.nodes):
            node.set_params(node_start, node_end, node_support_outside)
    
    def get_params(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Returns the parameters of the represented distribution.

        Returns:
            Tuple of three one-dimensional NumPy arrays representing the starts and ends of the intervals and the booleans indicating whether or not values outside of the intervals are part of the supports.
        """
        return self.start, self.end, self.support_outside

    # TODO: dist

    # TODO: check support


@dispatch(memoize=True)  # type: ignore
def marginalize(layer: UniformLayer, marg_rvs: Iterable[int], prune: bool=True, dispatch_ctx: Optional[DispatchContext]=None) -> Union[UniformLayer, Uniform, None]:
    """Structural marginalization for ``UniformLayer`` objects.

    Structurally marginalizes the specified layer module.
    If the layer's scope contains non of the random variables to marginalize, then the layer is returned unaltered.
    If the layer's scope is fully marginalized over, then None is returned.

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
        Unaltered leaf layer or None if it is completely marginalized.
    """
    # initialize dispatch context
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    # marginalize nodes
    marg_scopes = []
    marg_params = []

    for node in layer.nodes:
        marg_node = marginalize(node, marg_rvs, prune=prune)

        if marg_node is not None:
            marg_scopes.append(marg_node.scope)
            marg_params.append(marg_node.get_params())

    if len(marg_scopes) == 0:
        return None
    elif len(marg_scopes) == 1 and prune:
        new_node = Uniform(marg_scopes[0], *marg_params[0])
        return new_node
    else:
        new_layer = UniformLayer(marg_scopes, *[np.array(p) for p in zip(*marg_params)])
        return new_layer