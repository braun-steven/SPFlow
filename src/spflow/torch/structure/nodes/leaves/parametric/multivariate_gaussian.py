"""
Created on November 06, 2021

@authors: Philipp Deibert
"""
import numpy as np
import torch
import torch.distributions as D
from torch.nn.parameter import Parameter
from typing import List, Tuple, Union, Optional, Iterable
from .projections import proj_bounded_to_real, proj_real_to_bounded
from spflow.meta.scope.scope import Scope
from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.contexts.dispatch_context import DispatchContext
from spflow.torch.structure.nodes.node import LeafNode
from spflow.torch.structure.nodes.leaves.parametric.gaussian import Gaussian
from spflow.base.structure.nodes.leaves.parametric.multivariate_gaussian import MultivariateGaussian as BaseMultivariateGaussian


class MultivariateGaussian(LeafNode):
    r"""Multivariate Normal distribution for Torch backend.

    .. math::

        \text{PDF}(x) = \frac{1}{\sqrt{(2\pi)^d\det\Sigma}}\exp\left(-\frac{1}{2} (x-\mu)^T\Sigma^{-1}(x-\mu)\right)

    where
        - :math:`d` is the dimension of the distribution
        - :math:`x` is the :math:`d`-dim. vector of observations
        - :math:`\mu` is the :math:`d`-dim. mean vector
        - :math:`\Sigma` is the :math:`d\times d` covariance matrix

    Args:
        scope:
            List of integers specifying the variable scope.
        mean:
            A list, NumPy array or a torch tensor holding the means (:math:`\mu`) of each of the one-dimensional Normal distributions (defaults to all zeros).
            Has exactly as many elements as the scope of this leaf.
        cov:
            A list of lists, NumPy array or torch tensor (representing a two-dimensional :math:`d\times d` symmetric positive semi-definite matrix, where :math:`d` is the length
            of the scope) describing the covariances of the distribution (defaults to the identity matrix). The diagonal holds
            the variances (:math:`\sigma^2`) of each of the one-dimensional distributions.
    """
    def __init__(
        self,
        scope: Scope,
        mean: Optional[Union[List[float], torch.Tensor, np.ndarray]]=None,
        cov: Optional[Union[List[List[float]], torch.Tensor, np.ndarray]]=None,
    ) -> None:

        # check if scope contains duplicates
        if(len(set(scope.query)) != len(scope.query)):
            raise ValueError("Query scope for MultivariateGaussian contains duplicate variables.")
        if len(scope.evidence):
            raise ValueError(f"Evidence scope for MultivariateGaussian should be empty, but was {scope.evidence}.")

        super(MultivariateGaussian, self).__init__(scope=scope)

        if(mean is None):
            mean = torch.zeros((1,len(scope)))
        if(cov is None):
            cov = torch.eye(len(scope))

        # dimensions
        self.d = len(scope)

        # register mean vector as torch parameters
        self.mean = Parameter()

        # internally we use the lower triangular matrix (Cholesky decomposition) to encode the covariance matrix
        # register (auxiliary) values for diagonal and non-diagonal values of lower triangular matrix as torch parameters
        self.tril_diag_aux = Parameter()
        self.tril_nondiag = Parameter()

        # pre-compute and store indices of non-diagonal values for lower triangular matrix
        self.tril_nondiag_indices = torch.tril_indices(self.d, self.d, offset=-1)

        # set parameters
        self.set_params(mean, cov)

    @property
    def covariance_tril(self) -> torch.Tensor:
        # create zero matrix of appropriate dimension
        L_nondiag = torch.zeros(self.d, self.d)
        # fill non-diagonal values of lower triangular matrix
        L_nondiag[self.tril_nondiag_indices[0], self.tril_nondiag_indices[1]] = self.tril_nondiag  # type: ignore
        # add (projected) diagonal values
        L = L_nondiag + proj_real_to_bounded(self.tril_diag_aux, lb=0.0) * torch.eye(self.d)  # type: ignore
        # return lower triangular matrix
        return L

    @property
    def cov(self) -> torch.Tensor:
        # get lower triangular matrix
        L = self.covariance_tril
        # return covariance matrix
        return torch.matmul(L, L.T)

    @property
    def dist(self) -> D.Distribution:
        return D.MultivariateNormal(loc=self.mean, scale_tril=self.covariance_tril)

    def set_params(
        self,
        mean: Union[List[float], torch.Tensor, np.ndarray],
        cov: Union[List[List[float]], torch.Tensor, np.ndarray],
    ) -> None:

        if isinstance(mean, list):
            # convert float list to torch tensor
            mean = torch.tensor([float(v) for v in mean])
        elif isinstance(mean, np.ndarray):
            # convert numpy array to torch tensor
            mean = torch.from_numpy(mean).type(torch.get_default_dtype())

        if isinstance(cov, list):
            # convert numpy array to torch tensor
            cov = torch.tensor([[float(v) for v in row] for row in cov])
        elif isinstance(cov, np.ndarray):
            # convert numpy array to torch tensor
            cov = torch.from_numpy(cov).type(torch.get_default_dtype())

        # check mean vector for nan or inf values
        if torch.any(torch.isinf(mean)):
            raise ValueError(
                "Mean vector for MultivariateGaussian may not contain infinite values"
            )
        if torch.any(torch.isnan(mean)):
            raise ValueError("Mean vector for MultivariateGaussian may not contain NaN values")

        # dimensions
        d = mean.numel()

        # make sure that number of dimensions matches scope length
        if (
            (mean.ndim == 1 and mean.shape[0] != len(self.scope.query))
            or (mean.ndim == 2 and mean.shape[1] != len(self.scope.query))
            or mean.ndim > 2
        ):
            raise ValueError(
                f"Dimensions of mean vector for MultivariateGaussian should match scope size {len(self.scope.query)}, but was: {mean.shape}"
            )

        # make sure that dimensions of covariance matrix are correct
        if cov.ndim != 2 or (
            cov.ndim == 2
            and (
                cov.shape[0] != len(self.scope.query)
                or cov.shape[1] != len(self.scope.query)
            )
        ):
            raise ValueError(
                f"Covariance matrix for MultivariateGaussian expected to be of shape ({len(self.scope.query), len(self.scope.query)}), but was: {cov.shape}"
            )

        # set mean vector
        self.mean.data = mean

        # check covariance matrix for nan or inf values
        if torch.any(torch.isinf(cov)):
            raise ValueError(
                "Covariance matrix vector for MultivariateGaussian may not contain infinite values"
            )
        if torch.any(torch.isnan(cov)):
            raise ValueError(
                "Covariance matrix for MultivariateGaussian may not contain NaN values"
            )

        # compute lower triangular matrix (also check if covariance matrix is symmetric positive definite)
        L = torch.linalg.cholesky(cov)  # type: ignore

        # set diagonal and non-diagonal values of lower triangular matrix
        self.tril_diag_aux.data = proj_bounded_to_real(torch.diag(L), lb=0.0)
        self.tril_nondiag.data = L[self.tril_nondiag_indices[0], self.tril_nondiag_indices[1]]

    def get_params(self) -> Tuple[List[float], List[List[float]]]:
        return self.mean.data.cpu().tolist(), self.cov.data.cpu().tolist()  # type: ignore

    def check_support(self, scope_data: torch.Tensor) -> torch.Tensor:
        r"""Checks if instances are part of the support of the MultivariateGaussian distribution.

        .. math::

            \text{supp}(\text{MultivariateGaussian})=(-\infty,+\infty)^k

        Args:
            scope_data:
                Torch tensor containing possible distribution instances.
        Returns:
            Torch tensor indicating for each possible distribution instance, whether they are part of the support (True) or not (False).
        """

        if scope_data.ndim != 2 or scope_data.shape[1] != len(self.scopes_out[0].query):
            raise ValueError(
                f"Expected scope_data to be of shape (n,{len(self.scopes_out[0].query)}), but was: {scope_data.shape}"
            )

        valid = self.dist.support.check(scope_data)  # type: ignore

        # additionally check for infinite values (may return NaNs despite support)
        mask = valid.clone()
        valid[mask] &= ~scope_data[mask].isinf().sum(dim=-1).bool()

        return valid
    
    def marginalize(self, marg_rvs: Iterable[int]) -> Union["MultivariateGaussian", Gaussian, None]:
    
        # scope after marginalization (important: must remain order of scope indices since they map to the indices of the mean vector and covariance matrix!)
        marg_scope = [rv for rv in self.scope.query if rv not in marg_rvs]

        # return univariate Gaussian if one-dimensional
        if(len(marg_scope) == 1):
            # note: Gaussian requires standard deviations instead of variance (take square root)
            return Gaussian(Scope(marg_scope), self.mean[marg_scope[0]].detach().cpu().item(), torch.sqrt(self.cov[marg_scope[0]][marg_scope[0]].detach()).cpu().item())
        # entire node is marginalized over
        elif not marg_scope:
            return None
        # node is partially marginalized over
        else:
            # compute marginalized mean vector and covariance matrix
            marg_mean = self.mean[marg_scope]
            marg_cov = self.cov[marg_scope][:, marg_scope]

            return MultivariateGaussian(Scope(marg_scope), marg_mean, marg_cov)


@dispatch(memoize=True)
def marginalize(node: MultivariateGaussian, marg_rvs: Iterable[int], prune: bool=True, dispatch_ctx: Optional[DispatchContext]=None) -> Union[MultivariateGaussian,Gaussian,None]:
    return node.marginalize(marg_rvs)


@dispatch(memoize=True)
def toTorch(node: BaseMultivariateGaussian, dispatch_ctx: Optional[DispatchContext]=None) -> MultivariateGaussian:
    return MultivariateGaussian(node.scope, *node.get_params())


@dispatch(memoize=True)
def toBase(torch_node: MultivariateGaussian, dispatch_ctx: Optional[DispatchContext]=None) -> BaseMultivariateGaussian:
    return BaseMultivariateGaussian(torch_node.scope, *torch_node.get_params())