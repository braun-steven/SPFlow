#from spflow.base.sampling.sampling_context import SamplingContext
from spflow.meta.scope.scope import Scope
from spflow.base.structure.nodes.leaves.parametric.gaussian import Gaussian as BaseGaussian
from spflow.base.inference.nodes.leaves.parametric.gaussian import log_likelihood
from spflow.torch.structure.nodes.leaves.parametric.gaussian import Gaussian, toBase, toTorch
from spflow.torch.inference.nodes.leaves.parametric.gaussian import log_likelihood
from spflow.torch.inference.module import likelihood
#from spflow.torch.sampling import sample

import torch
import numpy as np

import random
import unittest


class TestGaussian(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        torch.set_default_dtype(torch.float64)

    @classmethod
    def teardown_class(cls):
        torch.set_default_dtype(torch.float32)

    def test_inference(self):

        mean = random.random()
        std = random.random() + 1e-7  # offset by small number to avoid zero

        torch_gaussian = Gaussian(Scope([0]), mean, std)
        node_gaussian = BaseGaussian(Scope([0]), mean, std)

        # create dummy input data (batch size x random variables)
        data = np.random.randn(3, 1)

        log_probs = log_likelihood(node_gaussian, data)
        log_probs_torch = log_likelihood(torch_gaussian, torch.tensor(data))

        # make sure that probabilities match python backend probabilities
        self.assertTrue(np.allclose(log_probs, log_probs_torch.detach().cpu().numpy()))

    def test_gradient_computation(self):

        mean = random.random()
        std = random.random() + 1e-7  # offset by small number to avoid zero

        torch_gaussian = Gaussian(Scope([0]), mean, std)

        # create dummy input data (batch size x random variables)
        data = np.random.randn(3, 1)

        log_probs_torch = log_likelihood(torch_gaussian, torch.tensor(data))

        # create dummy targets
        targets_torch = torch.ones(3, 1)

        loss = torch.nn.MSELoss()(log_probs_torch, targets_torch)
        loss.backward()

        self.assertTrue(torch_gaussian.mean.grad is not None)
        self.assertTrue(torch_gaussian.std_aux.grad is not None)

        mean_orig = torch_gaussian.mean.detach().clone()
        std_aux_orig = torch_gaussian.std_aux.detach().clone()

        optimizer = torch.optim.SGD(torch_gaussian.parameters(), lr=1)
        optimizer.step()

        # make sure that parameters are correctly updated
        self.assertTrue(torch.allclose(mean_orig - torch_gaussian.mean.grad, torch_gaussian.mean))
        self.assertTrue(
            torch.allclose(std_aux_orig - torch_gaussian.std_aux.grad, torch_gaussian.std_aux)
        )

        # verify that distribution parameters match parameters
        self.assertTrue(torch.allclose(torch_gaussian.mean, torch_gaussian.dist.mean))
        self.assertTrue(torch.allclose(torch_gaussian.std, torch_gaussian.dist.stddev))

    def test_gradient_optimization(self):

        # initialize distribution
        torch_gaussian = Gaussian(Scope([0]), mean=1.0, std=2.0)

        torch.manual_seed(0)

        # create dummy data (unit variance Gaussian)
        data = torch.randn((100000, 1))
        data = (data - data.mean()) / data.std()

        # initialize gradient optimizer
        optimizer = torch.optim.SGD(torch_gaussian.parameters(), lr=0.5)

        # perform optimization (possibly overfitting)
        for i in range(20):

            # clear gradients
            optimizer.zero_grad()

            # compute negative log-likelihood
            nll = -log_likelihood(torch_gaussian, data).mean()
            nll.backward()

            # update parameters
            optimizer.step()

        self.assertTrue(
            torch.allclose(torch_gaussian.mean, torch.tensor(0.0), atol=1e-3, rtol=1e-3)
        )
        self.assertTrue(
            torch.allclose(torch_gaussian.std, torch.tensor(1.0), atol=1e-3, rtol=1e-3)
        )

    def test_likelihood_marginalization(self):

        gaussian = Gaussian(Scope([0]), 0.0, 1.0)
        data = torch.tensor([[float("nan")]])

        # should not raise and error and should return 1
        probs = likelihood(gaussian, data)

        self.assertTrue(torch.allclose(probs, torch.tensor(1.0)))

    def test_support(self):

        # Support for Gaussian distribution: floats (-inf, inf)

        gaussian = Gaussian(Scope([0]), 0.0, 1.0)

        # check infinite values
        self.assertRaises(ValueError, log_likelihood, gaussian, torch.tensor([[float("inf")]]))
        self.assertRaises(ValueError, log_likelihood, gaussian, torch.tensor([[-float("inf")]]))

"""
    def test_sampling(self):

        gaussian = Gaussian(Scope([0]), 0.0, 0.0005)

        data = torch.tensor([[float("nan")], [float("nan")], [float("nan")]])

        samples = sample(gaussian, data, ll_cache={}, sampling_ctx=SamplingContext([0, 2]))

        self.assertTrue(all(samples.isnan() == torch.tensor([[False], [True], [False]])))

        # ----- verify samples -----
        samples = sample(gaussian, 1000)
        self.assertTrue(torch.isclose(samples.mean(), torch.Tensor([0.0]), atol=0.01))
"""

if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    unittest.main()