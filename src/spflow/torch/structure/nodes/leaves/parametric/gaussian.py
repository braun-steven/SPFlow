import numpy as np
import torch
import torch.distributions as D
from torch.nn.parameter import Parameter
from typing import List, Tuple
from .parametric import TorchParametricLeaf, proj_bounded_to_real, proj_real_to_bounded
from spflow.base.structure.nodes.leaves.parametric.statistical_types import ParametricType
from spflow.base.structure.nodes.leaves.parametric import Gaussian

from multipledispatch import dispatch  # type: ignore


class TorchGaussian(TorchParametricLeaf):
    """(Univariate) Normal distribution.
    PDF(x) =
        1/sqrt(2*pi*sigma^2) * exp(-(x-mu)^2/(2*sigma^2)), where
            - x is an observation
            - mu is the mean
            - sigma is the standard deviation
    Attributes:
        mean:
            mean (mu) of the distribution.
        stdev:
            standard deviation (sigma) of the distribution.
    """

    ptype = ParametricType.CONTINUOUS

    def __init__(self, scope: List[int], mean: float, stdev: float) -> None:

        if(len(scope) != 1):
            raise ValueError(f"Scope size for TorchGaussian should be 1, but was: {len(scope)}")

        super(TorchGaussian, self).__init__(scope)

        # register mean as torch parameter
        self.mean = Parameter()
        # register auxiliary torch paramter for standard deviation
        self.stdev_aux = Parameter()

        # set parameters
        self.set_params(mean, stdev)

    @property
    def stdev(self) -> torch.Tensor:
        # project auxiliary parameter onto actual parameter range
        return proj_real_to_bounded(self.stdev_aux, lb=0.0)  # type: ignore

    @property
    def dist(self) -> D.Distribution:
        return D.Normal(loc=self.mean, scale=self.stdev)

    def forward(self, data: torch.Tensor) -> torch.Tensor:

        batch_size: int = data.shape[0]

        # get information relevant for the scope
        scope_data = data[:, list(self.scope)]

        # initialize empty tensor (number of output values matches batch_size)
        log_prob: torch.Tensor = torch.empty(batch_size, 1)

        # ----- marginalization -----

        # if the scope variables are fully marginalized over (NaNs) return probability 1 (0 in log-space)
        log_prob[torch.isnan(scope_data).sum(dim=1) == len(self.scope)] = 0.0

        # ----- log probabilities -----

        # create Torch distribution with specified parameters
        dist = D.Normal(loc=self.mean, scale=self.stdev)

        # compute probabilities on data samples where we have all values
        prob_mask = torch.isnan(scope_data).sum(dim=1) == 0
        log_prob[prob_mask] = dist.log_prob(scope_data[prob_mask])

        return log_prob

    def set_params(self, mean: float, stdev: float) -> None:

        if not (np.isfinite(mean) and np.isfinite(stdev)):
            raise ValueError(
                f"Mean and standard deviation for Gaussian distribution must be finite, but were: {mean}, {stdev}"
            )
        if stdev <= 0.0:
            raise ValueError(
                f"Standard deviation for Gaussian distribution must be greater than 0.0, but was: {stdev}"
            )

        self.mean.data = torch.tensor(float(mean))
        self.stdev_aux.data = proj_bounded_to_real(torch.tensor(float(stdev)), lb=0.0)

    def get_params(self) -> Tuple[float, float]:
        return self.mean.data.cpu().numpy(), self.stdev.data.cpu().numpy()  # type: ignore


@dispatch(Gaussian)  # type: ignore[no-redef]
def toTorch(node: Gaussian) -> TorchGaussian:
    return TorchGaussian(node.scope, *node.get_params())


@dispatch(TorchGaussian)  # type: ignore[no-redef]
def toNodes(torch_node: TorchGaussian) -> Gaussian:
    return Gaussian(torch_node.scope, *torch_node.get_params())
