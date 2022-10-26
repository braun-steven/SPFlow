# -*- coding: utf-8 -*-
"""Contains inference methods for ``Geometric`` nodes for SPFlow in the 'base' backend.
"""
from spflow.meta.contexts.dispatch_context import DispatchContext, init_default_dispatch_context
from spflow.meta.dispatch.dispatch import dispatch
from spflow.base.structure.nodes.leaves.parametric.geometric import Geometric

from typing import Optional
import numpy as np


@dispatch(memoize=True)  # type: ignore
def log_likelihood(node: Geometric, data: np.ndarray, dispatch_ctx: Optional[DispatchContext]=None) -> np.ndarray:
    r"""Computes log-likelihoods for ``Geometric`` node in the 'base' backend given input data.

    Log-likelihood for ``Geometric`` is given by the logarithm of its probability distribution function (PDF):

    .. math::

        \log(\text{PMF}(k)) =  \log(p(1-p)^{k-1})

    where
        - :math:`k` is the number of trials
        - :math:`p` is the success probability of each trial

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

    # initialize probabilities
    probs = np.zeros((data.shape[0], 1))

    # select relevant data based on node's scope
    data = data[:, node.scope.query]

    # create mask based on marginalized instances (NaNs)
    # keeps default value of 1 (0 in log-space)
    marg_ids = np.isnan(data).sum(axis=-1).astype(bool)

    # create masked based on distribution's support
    valid_ids = node.check_support(data[~marg_ids]).squeeze(1)

    # TODO: suppress checks
    if not all(valid_ids):
        raise ValueError(
            f"Encountered data instances that are not in the support of the Geometric distribution."
        )

    # compute probabilities for all non-marginalized instances
    probs[~marg_ids] = node.dist.logpmf(k=data[~marg_ids])

    return probs
