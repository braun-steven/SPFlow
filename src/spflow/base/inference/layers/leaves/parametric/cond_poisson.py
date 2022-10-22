"""
Created on October 18, 2022

@authors: Philipp Deibert
"""
import numpy as np
from typing import Optional
from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.contexts.dispatch_context import DispatchContext, init_default_dispatch_context
from spflow.base.structure.layers.leaves.parametric.cond_poisson import CondPoissonLayer


@dispatch(memoize=True)
def log_likelihood(layer: CondPoissonLayer, data: np.ndarray, dispatch_ctx: Optional[DispatchContext]=None) -> np.ndarray:
    """TODO"""
    # initialize dispatch context
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    # retrieve value for 'l'
    l_values = layer.retrieve_params(data, dispatch_ctx)

    for node, l in zip(layer.nodes, l_values):
        dispatch_ctx.args[node] = {'l': l}

    # weight child log-likelihoods (sum in log-space) and compute log-sum-exp
    return np.concatenate([log_likelihood(node, data, dispatch_ctx=dispatch_ctx) for node in layer.nodes], axis=1)
