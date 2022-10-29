from spflow.meta.scope.scope import Scope
from spflow.meta.contexts.sampling_context import SamplingContext
from spflow.base.structure.nodes.leaves.parametric.hypergeometric import (
    Hypergeometric,
)
from spflow.base.sampling.nodes.leaves.parametric.hypergeometric import sample
from spflow.base.sampling.module import sample

import numpy as np
import random

import unittest


class TestHypergeometric(unittest.TestCase):
    def test_sampling_1(self):

        # set seed
        np.random.seed(0)
        random.seed(0)

        # ----- configuration 1 -----
        N = 500
        M = 100
        n = 50

        hypergeometric = Hypergeometric(Scope([0]), N, M, n)

        samples = sample(hypergeometric, 100000)

        self.assertTrue(
            np.isclose(
                samples.mean(axis=0), np.array(n * M) / N, atol=0.01, rtol=0.1
            )
        )

    def test_sampling_2(self):

        # set seed
        np.random.seed(0)
        random.seed(0)

        # ----- configuration 2 -----
        N = 100
        M = 50
        n = 10

        hypergeometric = Hypergeometric(Scope([0]), N, M, n)

        samples = sample(hypergeometric, 100000)

        self.assertTrue(
            np.isclose(
                samples.mean(axis=0), np.array(n * M) / N, atol=0.01, rtol=0.1
            )
        )

    def test_sampling_5(self):

        hypergeometric = Hypergeometric(Scope([0]), 2, 2, 2)

        # make sure that instance ids out of bounds raise errors
        self.assertRaises(
            ValueError,
            sample,
            hypergeometric,
            np.array([[0]]),
            sampling_ctx=SamplingContext([1]),
        )


if __name__ == "__main__":
    unittest.main()
