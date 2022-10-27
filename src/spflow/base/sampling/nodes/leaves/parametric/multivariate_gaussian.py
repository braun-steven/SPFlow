# -*- coding: utf-8 -*-
"""Contains sampling methods for ``MultivariateGaussian`` nodes for SPFlow in the ``base`` backend.
"""
from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.contexts.dispatch_context import DispatchContext, init_default_dispatch_context
from spflow.meta.contexts.sampling_context import SamplingContext, init_default_sampling_context
from spflow.base.structure.nodes.leaves.parametric.multivariate_gaussian import MultivariateGaussian

import numpy as np
from typing import Optional


@dispatch  # type: ignore
def sample(leaf: MultivariateGaussian, data: np.ndarray, dispatch_ctx: Optional[DispatchContext]=None, sampling_ctx: Optional[SamplingContext]=None) -> np.ndarray:
    r"""Samples from ``MultivariateGaussian`` nodes in the ``base`` backend given potential evidence.

    Samples missing values proportionally to its probability distribution function (PDF).
    If evidence is present, values are sampled from the conitioned marginal distribution.

    Args:
        leaf:
            Leaf node to sample from.
        data:
            Two-dimensional NumPy array containing potential evidence.
            Each row corresponds to a sample.
        dispatch_ctx:
            Optional dispatch context.
        sampling_ctx:
            Optional sampling context containing the instances (i.e., rows) of ``data`` to fill with sampled values and the output indices of the node to sample from.

    Returns:
        Two-dimensional NumPy array containing the sampled values together with the specified evidence.
        Each row corresponds to a sample.
    """
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)
    sampling_ctx = init_default_sampling_context(sampling_ctx, data.shape[0])

    if any([i >= data.shape[0] for i in sampling_ctx.instance_ids]):
        raise ValueError("Some instance ids are out of bounds for data tensor.")

    nan_data = np.isnan(data[np.ix_(sampling_ctx.instance_ids, leaf.scope.query)])

    # group by scope rvs to sample
    for nan_mask in np.unique(nan_data, axis=0):

        cond_mask = ~nan_mask

        # no 'NaN' values (nothing to sample)
        if(np.sum(nan_mask) == 0):
            continue
        # sample from full distribution
        elif(np.sum(nan_mask) == len(leaf.scope.query)):
            sampling_ids = np.array(sampling_ctx.instance_ids)[(nan_data == nan_mask).sum(axis=1) == nan_mask.shape[0]]

            data[np.ix_(sampling_ids, leaf.scope.query)] = leaf.dist.rvs(size=sampling_ids.shape[0])
        # sample from conditioned distribution
        else:
            # NOTE: the conditional sampling implemented here is based on the algorithm described in Arnaud Doucet (2010): "A Note on Efficient Conditional Simulation of Gaussian Distributions" (https://www.stats.ox.ac.uk/~doucet/doucet_simulationconditionalgaussian.pdf)
            sampling_ids = np.array(sampling_ctx.instance_ids)[(nan_data == nan_mask).sum(axis=1) == nan_mask.shape[0]]

            # sample from full distribution
            joint_samples = leaf.dist.rvs(size=sampling_ids.shape[0])

            # compute inverse of marginal covariance matrix of conditioning RVs
            marg_cov_inv = np.linalg.inv(leaf.cov[np.ix_(cond_mask, cond_mask)])

            # get conditional covariance matrix
            cond_cov = leaf.cov[np.ix_(cond_mask, ~cond_mask)]

            data[np.ix_(sampling_ids, ~cond_mask)] = joint_samples[:, ~cond_mask] + ((data[np.ix_(sampling_ids, cond_mask)]-joint_samples[:, cond_mask])@(marg_cov_inv@cond_cov))

    return data