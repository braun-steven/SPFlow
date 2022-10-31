from spflow.meta.data.scope import Scope
from spflow.meta.data.feature_types import FeatureTypes
from spflow.torch.structure.autoleaf import AutoLeaf
from spflow.base.structure.nodes.leaves.parametric.hypergeometric import (
    Hypergeometric as BaseHypergeometric,
)
from spflow.base.inference.nodes.leaves.parametric.hypergeometric import (
    log_likelihood,
)
from spflow.torch.structure.nodes.leaves.parametric.hypergeometric import (
    Hypergeometric,
    toBase,
    toTorch,
)
from spflow.torch.structure.nodes.node import marginalize
from spflow.torch.inference.nodes.leaves.parametric.hypergeometric import (
    log_likelihood,
)
from spflow.torch.inference.module import likelihood

# from spflow.torch.sampling import sample

import torch
import numpy as np

import random
import unittest


class TestHypergeometric(unittest.TestCase):
    def test_initialization(self):

        # Valid parameters for Hypergeometric distribution: N in N U {0}, M in {0,...,N}, n in {0,...,N}, p in [0,1]

        # N = 0
        Hypergeometric(Scope([0]), 0, 0, 0)
        # N < 0
        self.assertRaises(Exception, Hypergeometric, Scope([0]), -1, 1, 1)
        # N = inf and N = nan
        self.assertRaises(Exception, Hypergeometric, Scope([0]), np.inf, 1, 1)
        self.assertRaises(Exception, Hypergeometric, Scope([0]), np.nan, 1, 1)
        # N float
        self.assertRaises(Exception, Hypergeometric, Scope([0]), 1.5, 1, 1)

        # M < 0 and M > N
        self.assertRaises(Exception, Hypergeometric, Scope([0]), 1, -1, 1)
        self.assertRaises(Exception, Hypergeometric, Scope([0]), 1, 2, 1)
        # 0 <= M <= N
        for i in range(4):
            Hypergeometric(Scope([0]), 3, i, 0)
        # M = inf and M = nan
        self.assertRaises(Exception, Hypergeometric, Scope([0]), 1, np.inf, 1)
        self.assertRaises(Exception, Hypergeometric, Scope([0]), 1, np.nan, 1)
        # M float
        self.assertRaises(Exception, Hypergeometric, Scope([0]), 1, 0.5, 1)

        # n < 0 and n > N
        self.assertRaises(Exception, Hypergeometric, Scope([0]), 1, 1, -1)
        self.assertRaises(Exception, Hypergeometric, Scope([0]), 1, 1, 2)
        # 0 <= n <= N
        for i in range(4):
            Hypergeometric(Scope([0]), 3, 0, i)
        # n = inf and n = nan
        self.assertRaises(Exception, Hypergeometric, Scope([0]), 1, 1, np.inf)
        self.assertRaises(Exception, Hypergeometric, Scope([0]), 1, 1, np.nan)
        # n float
        self.assertRaises(Exception, Hypergeometric, Scope([0]), 1, 1, 0.5)

        # invalid scopes
        self.assertRaises(Exception, Hypergeometric, Scope([]), 1, 1, 1)
        self.assertRaises(Exception, Hypergeometric, Scope([0, 1]), 1, 1, 1)
        self.assertRaises(Exception, Hypergeometric, Scope([0], [1]), 1, 1, 1)

    def test_structural_marginalization(self):

        hypergeometric = Hypergeometric(Scope([0]), 0, 0, 0)

        self.assertTrue(marginalize(hypergeometric, [1]) is not None)
        self.assertTrue(marginalize(hypergeometric, [0]) is None)

    def test_accept(self):

        # discrete meta type (should reject)
        self.assertFalse(Hypergeometric.accepts([([FeatureTypes.Discrete], Scope([0]))]))

        # Bernoulli feature type class (should reject)
        self.assertFalse(Hypergeometric.accepts([([FeatureTypes.Hypergeometric], Scope([0]))]))

        # Bernoulli feature type instance
        self.assertTrue(Hypergeometric.accepts([([FeatureTypes.Hypergeometric(N=4, M=2, n=3)], Scope([0]))]))

        # invalid feature type
        self.assertFalse(Hypergeometric.accepts([([FeatureTypes.Continuous], Scope([0]))]))

        # conditional scope
        self.assertFalse(Hypergeometric.accepts([([FeatureTypes.Hypergeometric(N=4, M=2, n=3)], Scope([0], [1]))]))

        # scope length does not match number of types
        self.assertFalse(Hypergeometric.accepts([([FeatureTypes.Hypergeometric(N=4, M=2, n=3)], Scope([0, 1]))]))

        # multivariate signature
        self.assertFalse(Hypergeometric.accepts([([FeatureTypes.Hypergeometric(N=4, M=2, n=3), FeatureTypes.Hypergeometric(N=4, M=2, n=3)], Scope([0, 1]))]))

    def test_initialization_from_signatures(self):

        hypergeometric = Hypergeometric.from_signatures([([FeatureTypes.Hypergeometric(N=4, M=2, n=3)], Scope([0]))])
        self.assertTrue(torch.all(hypergeometric.N == torch.tensor(4)))
        self.assertTrue(torch.all(hypergeometric.M == torch.tensor(2)))
        self.assertTrue(torch.all(hypergeometric.n == torch.tensor(3)))

        # ----- invalid arguments -----

        # discrete meta type
        self.assertRaises(ValueError, Hypergeometric.from_signatures, [([FeatureTypes.Discrete], Scope([0]))])

        # Bernoulli feature type class
        self.assertRaises(ValueError, Hypergeometric.from_signatures, [([FeatureTypes.Hypergeometric], Scope([0]))])

        # invalid feature type
        self.assertRaises(ValueError, Hypergeometric.from_signatures, [([FeatureTypes.Continuous], Scope([0]))])

        # conditional scope
        self.assertRaises(ValueError, Hypergeometric.from_signatures, [([FeatureTypes.Discrete], Scope([0], [1]))])

        # scope length does not match number of types
        self.assertRaises(ValueError, Hypergeometric.from_signatures, [([FeatureTypes.Discrete], Scope([0, 1]))])

        # multivariate signature
        self.assertRaises(ValueError, Hypergeometric.from_signatures, [([FeatureTypes.Discrete, FeatureTypes.Discrete], Scope([0, 1]))])

    def test_autoleaf(self):

        # make sure leaf is registered
        self.assertTrue(AutoLeaf.is_registered(Hypergeometric))

        # make sure leaf is correctly inferred
        self.assertEqual(Hypergeometric, AutoLeaf.infer([([FeatureTypes.Hypergeometric(N=4, M=2, n=3)], Scope([0]))]))

        # make sure AutoLeaf can return correctly instantiated object
        hypergeometric = AutoLeaf([([FeatureTypes.Hypergeometric(N=4, M=2, n=3)], Scope([0]))])
        self.assertTrue(isinstance(hypergeometric, Hypergeometric))
        self.assertTrue(torch.all(hypergeometric.N == torch.tensor(4)))
        self.assertTrue(torch.all(hypergeometric.M == torch.tensor(2)))
        self.assertTrue(torch.all(hypergeometric.n == torch.tensor(3)))

    def test_base_backend_conversion(self):

        N = 15
        M = 10
        n = 10

        torch_hypergeometric = Hypergeometric(Scope([0]), N, M, n)
        node_hypergeometric = BaseHypergeometric(Scope([0]), N, M, n)

        # check conversion from torch to python
        self.assertTrue(
            np.allclose(
                np.array([*torch_hypergeometric.get_params()]),
                np.array([*toBase(torch_hypergeometric).get_params()]),
            )
        )
        # check conversion from python to torch
        self.assertTrue(
            np.allclose(
                np.array([*node_hypergeometric.get_params()]),
                np.array([*toTorch(node_hypergeometric).get_params()]),
            )
        )


if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    unittest.main()
