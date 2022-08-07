from spflow.meta.scope.scope import Scope
from spflow.meta.contexts.sampling_context import SamplingContext
from spflow.torch.structure.nodes.node import SPNSumNode, SPNProductNode
from spflow.torch.inference.nodes.node import log_likelihood
from spflow.torch.sampling.nodes.node import sample
from spflow.torch.structure.nodes.leaves.parametric.gaussian import Gaussian
from spflow.torch.sampling.nodes.leaves.parametric.gaussian import sample
from spflow.torch.inference.nodes.leaves.parametric.gaussian import log_likelihood
from spflow.torch.sampling.module import sample

import torch
import numpy as np

import random
import unittest


class TestNode(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        torch.set_default_dtype(torch.float64)

    @classmethod
    def teardown_class(cls):
        torch.set_default_dtype(torch.float32)

    def test_spn_sampling(self):

        s = SPNSumNode(
            children=[
                SPNSumNode(
                    children=[
                        SPNProductNode(
                            children=[Gaussian(Scope([0]), -7.0, 1.0), Gaussian(Scope([1]), 7.0, 1.0)],
                        ),
                        SPNProductNode(
                            children=[Gaussian(Scope([0]), -5.0, 1.0), Gaussian(Scope([1]), 5.0, 1.0)],
                        ),
                    ],
                    weights=[0.2, 0.8],
                ),
                SPNSumNode(
                    children=[
                        SPNProductNode(
                            children=[Gaussian(Scope([0]), -3.0, 1.0), Gaussian(Scope([1]), 3.0, 1.0)],
                        ),
                        SPNProductNode(
                            children=[Gaussian(Scope([0]), -1.0, 1.0), Gaussian(Scope([1]), 1.0, 1.0)],
                        ),
                    ],
                    weights=[0.6, 0.4],
                ),
            ],
            weights=[0.7, 0.3],
        )

        samples = sample(s, 1000)
        expected_mean = 0.7 * (0.2 * torch.tensor([-7, 7]) + 0.8 * torch.tensor([-5, 5])) + 0.3 * (
            0.6 * torch.tensor([-3, 3]) + 0.4 * torch.tensor([-1, 1])
        )

        self.assertTrue(torch.allclose(samples.mean(dim=0), expected_mean, rtol=0.1))

    def test_sum_node_sampling(self):

        l1 = Gaussian(Scope([0]), -5.0, 1.0)
        l2 = Gaussian(Scope([0]), 5.0, 1.0)

        # ----- weights 0, 1 -----

        s = SPNSumNode([l1, l2], weights=[0.001, 0.999])

        samples = sample(s, 1000)
        self.assertTrue(torch.isclose(samples.mean(), torch.tensor(5.0), rtol=0.1))

        # ----- weights 1, 0 -----

        s = SPNSumNode([l1, l2], weights=[0.999, 0.001])

        samples = sample(s, 1000)
        self.assertTrue(torch.isclose(samples.mean(), torch.tensor(-5.0), rtol=0.1))

        # ----- weights 0.2, 0.8 -----

        s = SPNSumNode([l1, l2], weights=[0.2, 0.8])

        samples = sample(s, 1000)
        self.assertTrue(torch.isclose(samples.mean(), torch.tensor(3.0), rtol=0.1))


if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    unittest.main()