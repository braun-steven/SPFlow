"""
Created on September 25, 2022

@authors: Philipp Deibert
"""
from typing import Optional, Union, Callable
import torch
from spflow.meta.dispatch.dispatch import dispatch
from spflow.torch.structure.layers.leaves.parametric.poisson import PoissonLayer


@dispatch(memoize=True) # TODO: swappable
def maximum_likelihood_estimation(layer: PoissonLayer, data: torch.Tensor, bias_correction: bool=True, nan_strategy: Optional[Union[str, Callable]]=None) -> None:
    """TODO."""

    # select relevant data for scope
    scope_data = torch.hstack([data[:, scope.query] for scope in layer.scopes_out])

    if torch.any(~layer.check_support(scope_data)):
        raise ValueError("Encountered values outside of the support for 'PoissonLayer'.")

    # NaN entries (no information)
    nan_mask = torch.isnan(scope_data)

    # check if any columns (i.e., data for a output scope) contain only NaN values
    if torch.any(nan_mask.sum(dim=0) == scope_data.shape[0]):
        raise ValueError("Cannot compute maximum-likelihood estimation on nan-only data for a specified scope.")

    if nan_strategy is None and torch.any(nan_mask):
        raise ValueError("Maximum-likelihood estimation cannot be performed on missing data by default. Set a strategy for handling missing values if this is intended.")
    
    if isinstance(nan_strategy, str):
        # simply ignore missing data
        if nan_strategy == "ignore":
            l_est = torch.nan_to_num(scope_data, nan=0.0).sum(dim=0)/(~nan_mask).sum(dim=0)
        else:
            raise ValueError("Unknown strategy for handling missing (NaN) values for 'Poisson'.")
    elif isinstance(nan_strategy, Callable) or nan_strategy is None:
        if isinstance(nan_strategy, Callable):
            scope_data = nan_strategy(scope_data)
        # estimate rate parameter from data
        l_est = scope_data.type(torch.get_default_dtype()).mean(dim=0)
    else:
        raise ValueError(f"Expected 'nan_strategy' to be of type '{type(str)}, or '{Callable}' or '{None}', but was of type {type(nan_strategy)}.")
    
    # edge case: if rate 0, set to larger value (should not happen, but just in case)
    l_est[torch.allclose(l_est, torch.tensor(0.0))] = 1e-8

    # set parameters of leaf node
    layer.set_params(l=l_est)