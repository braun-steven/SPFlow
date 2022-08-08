from spflow.meta.scope.scope import Scope
from spflow.meta.contexts.sampling_context import SamplingContext
from spflow.torch.structure.nodes.leaves.parametric.bernoulli import Bernoulli
from spflow.torch.sampling.nodes.leaves.parametric.bernoulli import sample

import torch
import unittest


class TestBernoulli(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        torch.set_default_dtype(torch.float64)

    @classmethod
    def teardown_class(cls):
        torch.set_default_dtype(torch.float32)

    def test_sampling_0(self):

        # ----- p = 0 -----

        bernoulli = Bernoulli(Scope([0]), 0.0)

        data = torch.tensor([[float("nan")], [float("nan")], [float("nan")]])

        samples = sample(bernoulli, data, sampling_ctx=SamplingContext([0, 2]))

        self.assertTrue(all(samples.isnan() == torch.tensor([[False], [True], [False]])))
        self.assertTrue(all(samples[~samples.isnan()] == 0.0))

    def test_sampling_1(self):

        # ----- p = 1 -----

        bernoulli = Bernoulli(Scope([0]), 1.0)

        data = torch.tensor([[float("nan")], [float("nan")], [float("nan")]])

        samples = sample(bernoulli, data, sampling_ctx=SamplingContext([0, 2], [[0], [0]]))

        self.assertTrue(all(samples.isnan() == torch.tensor([[False], [True], [False]])))
        self.assertTrue(all(samples[~samples.isnan()] == 1.0))


if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    unittest.main()