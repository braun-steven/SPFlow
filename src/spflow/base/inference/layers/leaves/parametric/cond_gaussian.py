# -*- coding: utf-8 -*-
"""Contains inference methods for ``CondGaussianLayer`` leaves for SPFlow in the 'base' backend.
"""
import numpy as np
from typing import Optional
from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.contexts.dispatch_context import DispatchContext, init_default_dispatch_context
from spflow.base.structure.layers.leaves.parametric.cond_gaussian import CondGaussianLayer


@dispatch(memoize=True)  # type: ignore
def log_likelihood(layer: CondGaussianLayer, data: np.ndarray, dispatch_ctx: Optional[DispatchContext]=None) -> np.ndarray:
    r"""Computes log-likelihoods for ``CondGaussianLayer`` leaves in the 'base' backend given input data.

    Log-likelihood for ``CondGaussianLayer`` is given by the logarithm of its individual probability distribution functions (PDFs):

    .. math::

        \log(\text{PDF}(x)) = \log(\frac{1}{\sqrt{2\pi\sigma^2}}\exp(-\frac{(x-\mu)^2}{2\sigma^2}))

    where
        - :math:`x` the observation
        - :math:`\mu` is the mean
        - :math:`\sigma` is the standard deviation

    Missing values (i.e., NaN) are marginalized over.

    Args:
        node:
            Leaf node to perform inference for.
        data:
            Two-dimensional NumPy array containing the input data.
            Each row corresponds to a sample.
        dispatch_ctx:
            Optional dispatch context.

    Returns:
        Two-dimensional NumPy array containing the log-likelihoods of the input data for the sum node.
        Each row corresponds to an input sample.

    Raises:
        ValueError: Data outside of support.
    """
    # initialize dispatch context
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    # retrieve values for 'mean','std'
    mean_values, std_values = layer.retrieve_params(data, dispatch_ctx)

    for node, mean, std in zip(layer.nodes, mean_values, std_values):
        dispatch_ctx.update_args(node, {'mean': mean, 'std': std})

    # weight child log-likelihoods (sum in log-space) and compute log-sum-exp
    return np.concatenate([log_likelihood(node, data, dispatch_ctx=dispatch_ctx) for node in layer.nodes], axis=1)
