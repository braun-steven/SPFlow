"""
Created on October 18, 2022

@authors: Philipp Deibert
"""
from typing import Tuple, Optional, Callable, Union
import numpy as np
from spflow.meta.scope.scope import Scope
from spflow.meta.contexts.dispatch_context import DispatchContext
from spflow.base.structure.nodes.node import LeafNode

from scipy.stats import bernoulli
from scipy.stats.distributions import rv_frozen


class CondBernoulli(LeafNode):
    r"""Conditional (univariate) Bernoulli distribution.

    .. math::

        \text{PMF}(k)=\begin{cases} p   & \text{if } k=1\\
                                    1-p & \text{if } k=0\end{cases}
        
    where
        - :math:`p` is the success probability
        - :math:`k` is the outcome of the trial (0 or 1)

    Args:
        scope:
            Scope object specifying the variable scope.
        cond_f:
            Callable that provides the conditional parameters (p) of this distribution. TODO
    """
    def __init__(self, scope: Scope, cond_f: Optional[Callable]=None) -> None:

        if len(scope.query) != 1:
            raise ValueError(f"Query scope size for CondBernoulli should be 1, but was {len(scope.query)}.")
        if len(scope.evidence):
            raise ValueError(f"Evidence scope for CondBernoulli should be empty, but was {scope.evidence}.")

        super(CondBernoulli, self).__init__(scope=scope)

        self.set_cond_f(cond_f)

    def set_cond_f(self, cond_f: Optional[Callable]=None) -> None:
        self.cond_f = cond_f

    def retrieve_params(self, data: np.ndarray, dispatch_ctx: DispatchContext) -> Tuple[Union[np.ndarray, float]]:
        
        p, cond_f = None, None

        # check dispatch cache for required conditional parameter 'p'
        if self in dispatch_ctx.args:
            args = dispatch_ctx.args[self]

            # check if a value for 'p' is specified (highest priority)
            if "p" in args:
                p = args["p"]
            # check if alternative function to provide 'p' is specified (second to highest priority)
            if "cond_f" in args:
                cond_f = args["cond_f"]
        elif self.cond_f:
            # check if module has a 'cond_f' to provide 'p' specified (lowest priority)
            cond_f = self.cond_f

        # if neither 'p' nor 'cond_f' is specified (via node or arguments)
        if p is None and cond_f is None:
            raise ValueError("'CondBernoulli' requires either 'p' or 'cond_f' to retrieve 'p' to be specified.")

        # if 'p' was not already specified, retrieve it
        if p is None:
            p = cond_f(data)['p']

        # check if value for 'p' is valid
        if p < 0.0 or p > 1.0 or not np.isfinite(p):
            raise ValueError(
                f"Value of p for conditional Bernoulli distribution must to be between 0.0 and 1.0, but was: {p}"
            )
        
        return p

    def get_params(self) -> Tuple:
        return tuple([])

    def dist(self, p: float) -> rv_frozen:
        return bernoulli(p=p)

    def check_support(self, scope_data: np.ndarray) -> np.ndarray:
        r"""Checks if instances are part of the support of the Bernoulli distribution.

        .. math::

            \text{supp}(\text{Bernoulli})=\{0,1\}
        
        Additionally, NaN values are regarded as being part of the support (they are marginalized over during inference).
    
        Args:
            data:
                Numpy array containing sample instances.
        Returns:
            Two dimensional Numpy array indicating for each instance, whether they are part of the support (True) or not (False).
        """

        if scope_data.ndim != 2 or scope_data.shape[1] != len(self.scope.query):
            raise ValueError(
                f"Expected scope_data to be of shape (n,{len(self.scope.query)}), but was: {scope_data.shape}"
            )

        # initialize mask for valid entries
        valid = np.ones(scope_data.shape, dtype=bool)

        # nan entries (regarded as valid)
        nan_mask = np.isnan(scope_data)

        # check for infinite values
        valid[~nan_mask] &= ~np.isinf(scope_data[~nan_mask])

        # check if all values are valid integers
        # TODO: runtime warning due to nan values
        valid[valid & ~nan_mask] &= np.remainder(scope_data[valid & ~nan_mask], 1) == 0

        # check if values are in valid range
        valid[valid & ~nan_mask] &= (scope_data[valid & ~nan_mask] >= 0) & (scope_data[valid & ~nan_mask] <= 1)

        return valid