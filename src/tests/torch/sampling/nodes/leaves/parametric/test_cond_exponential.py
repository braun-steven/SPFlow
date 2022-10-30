from spflow.meta.data.scope import Scope
from spflow.meta.dispatch.sampling_context import SamplingContext
from spflow.torch.structure.nodes.leaves.parametric.cond_exponential import (
    CondExponential,
)
from spflow.torch.sampling.nodes.leaves.parametric.cond_exponential import (
    sample,
)
from spflow.torch.sampling.module import sample

import torch
import numpy as np
import random
import unittest


class TestExponential(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        torch.set_default_dtype(torch.float64)

    @classmethod
    def teardown_class(cls):
        torch.set_default_dtype(torch.float32)

    def test_sampling_1(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        # ----- l = 0 -----

        exponential = CondExponential(
            Scope([0]), cond_f=lambda data: {"l": 1.0}
        )

        data = torch.tensor([[float("nan")], [float("nan")], [float("nan")]])

        samples = sample(
            exponential, data, sampling_ctx=SamplingContext([0, 2])
        )

        self.assertTrue(
            all(samples.isnan() == torch.tensor([[False], [True], [False]]))
        )

        samples = sample(exponential, 1000)
        self.assertTrue(
            torch.isclose(samples.mean(), torch.tensor(1.0), rtol=0.1)
        )

    def test_sampling_2(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        # ----- l = 0.5 -----

        exponential = CondExponential(
            Scope([0]), cond_f=lambda data: {"l": 0.5}
        )
        samples = sample(exponential, 1000)
        self.assertTrue(
            torch.isclose(samples.mean(), torch.tensor(1.0 / 0.5), rtol=0.1)
        )

    def test_sampling_3(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)

        # ----- l = 2.5 -----

        exponential = CondExponential(
            Scope([0]), cond_f=lambda data: {"l": 2.5}
        )
        samples = sample(exponential, 1000)
        self.assertTrue(
            torch.isclose(samples.mean(), torch.tensor(1.0 / 2.5), rtol=0.1)
        )


if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    unittest.main()
