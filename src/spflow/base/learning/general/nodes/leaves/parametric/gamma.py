"""Contains learning methods for ``Gamma`` nodes for SPFlow in the ``base`` backend.
"""
from typing import Optional, Union, Callable
import numpy as np
from scipy.stats import gamma
from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.dispatch.dispatch_context import (
    DispatchContext,
    init_default_dispatch_context,
)
from spflow.base.structure.general.nodes.leaves.parametric.gamma import Gamma
from scipy.special import digamma, polygamma


@dispatch(memoize=True)  # type: ignore
def maximum_likelihood_estimation(
    leaf: Gamma,
    data: np.ndarray,
    weights: Optional[np.ndarray] = None,
    bias_correction: bool = True,
    nan_strategy: Optional[Union[str, Callable]] = None,
    check_support: bool = True,
    dispatch_ctx: Optional[DispatchContext] = None,
) -> None:
    r"""Maximum (weighted) likelihood estimation (MLE) of ``Gamma`` node parameters in the ``base`` backend.

    Estimates the shape and rate parameters :math:`alpha`,:math:`beta` of a Gamma distribution from data, as described in (Minka, 2002): "Estimating a Gamma distribution" (adjusted to support weights).
    Weights are normalized to sum up to :math:`N`.

    Args:
        leaf:
            Leaf node to estimate parameters of.
        data:
            Two-dimensional NumPy array containing the input data.
            Each row corresponds to a sample.
        weights:
            Optional one-dimensional NumPy array containing non-negative weights for all data samples.
            Must match number of samples in ``data``.
            Defaults to None in which case all weights are initialized to ones.
        bias_corrections:
            Boolen indicating whether or not to correct possible biases.
            Has no effect for ``Gamma`` nodes.
            Defaults to True.
        nan_strategy:
            Optional string or callable specifying how to handle missing data.
            If 'ignore', missing values (i.e., NaN entries) are ignored.
            If a callable, it is called using ``data`` and should return another NumPy array of same size.
            Defaults to None.
        check_support:
            Boolean value indicating whether or not if the data is in the support of the leaf distributions.
            Defaults to True.
        dispatch_ctx:
            Optional dispatch context.

    Raises:
        ValueError: Invalid arguments.
    """
    # initialize dispatch context
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    # select relevant data for scope
    scope_data = data[:, leaf.scope.query]

    if weights is None:
        weights = np.ones(data.shape[0])

    if weights.ndim != 1 or weights.shape[0] != data.shape[0]:
        raise ValueError(
            "Number of specified weights for maximum-likelihood estimation does not match number of data points."
        )

    # reshape weights
    weights = weights.reshape(-1, 1)

    if check_support:
        if np.any(~leaf.check_support(scope_data, is_scope_data=True)):
            raise ValueError(
                "Encountered values outside of the support for 'Gamma'."
            )

    # NaN entries (no information)
    nan_mask = np.isnan(scope_data)

    if np.all(nan_mask):
        raise ValueError(
            "Cannot compute maximum-likelihood estimation on nan-only data."
        )

    if nan_strategy is None and np.any(nan_mask):
        raise ValueError(
            "Maximum-likelihood estimation cannot be performed on missing data by default. Set a strategy for handling missing values if this is intended."
        )

    if isinstance(nan_strategy, str):
        if nan_strategy == "ignore":
            # simply ignore missing data
            scope_data = scope_data[~nan_mask.squeeze(1)]
            weights = weights[~nan_mask.squeeze(1)]
        else:
            raise ValueError(
                "Unknown strategy for handling missing (NaN) values for 'Gamma'."
            )
    elif isinstance(nan_strategy, Callable):
        scope_data = nan_strategy(scope_data)
        # TODO: how to handle weights?
    elif nan_strategy is not None:
        raise ValueError(
            f"Expected 'nan_strategy' to be of type '{type(str)}, or '{Callable}' or '{None}', but was of type {type(nan_strategy)}."
        )

    # normalize weights to sum to n_samples
    weights /= weights.sum() / scope_data.shape[0]

    # scipy.stats.gamma does not support weights, we therefore implement it ourselves

    # compute two parameter gamma estimates according to (Minka, 2002): https://tminka.github.io/papers/minka-gamma.pdf
    # also see this VBA implementation for reference: https://github.com/jb262/MaximumLikelihoodGammaDist/blob/main/MLGamma.bas
    # adapted to take weights

    n_total = weights.sum()
    mean = (weights * scope_data).sum() / n_total
    log_mean = np.log(mean)
    mean_log = (weights * np.log(scope_data)).sum() / n_total

    # start values
    alpha_prev = 0.0
    alpha_est = 0.5 / (log_mean - mean_log)

    # iteratively compute alpha estimate
    while np.abs(alpha_prev - alpha_est) > 1e-6:
        alpha_prev = alpha_est
        alpha_est = 1.0 / (
            1.0 / alpha_prev
            + (mean_log - log_mean + np.log(alpha_prev) - digamma(alpha_prev))
            / (
                alpha_prev ** 2
                * (1.0 / alpha_prev - polygamma(n=1, x=alpha_prev))
            )
        )

    # compute beta estimate
    # NOTE: different to the original paper we compute the inverse since beta=1.0/scale
    beta_est = alpha_est / mean

    # TODO: bias correction?

    # edge case: if alpha/beta 0, set to larger value (should not happen, but just in case)
    if np.isclose(alpha_est, 0):
        alpha_est = 1e-8
    if np.isclose(beta_est, 0):
        beta_est = 1e-8

    # set parameters of leaf node
    leaf.set_params(alpha=alpha_est, beta=beta_est)