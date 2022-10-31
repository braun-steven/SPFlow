from spflow.meta.data.scope import Scope
from spflow.meta.data.feature_types import FeatureTypes
from spflow.base.structure.autoleaf import AutoLeaf
from spflow.base.structure.nodes.node import marginalize
from spflow.base.structure.nodes.leaves.parametric.gaussian import Gaussian

import numpy as np
import unittest
import random
import math


class TestGaussian(unittest.TestCase):
    def test_initialization(self):

        # Valid parameters for Gaussian distribution: mean in (-inf,inf), stdev > 0

        mean = random.random()

        # mean = inf and mean = nan
        self.assertRaises(Exception, Gaussian, Scope([0]), np.inf, 1.0)
        self.assertRaises(Exception, Gaussian, Scope([0]), -np.inf, 1.0)
        self.assertRaises(Exception, Gaussian, Scope([0]), np.nan, 1.0)

        # stdev = 0 and stdev < 0
        self.assertRaises(Exception, Gaussian, Scope([0]), mean, 0.0)
        self.assertRaises(
            Exception, Gaussian, Scope([0]), mean, np.nextafter(0.0, -1.0)
        )
        # stdev = inf and stdev = nan
        self.assertRaises(Exception, Gaussian, Scope([0]), mean, np.inf)
        self.assertRaises(Exception, Gaussian, Scope([0]), mean, np.nan)

        # invalid scopes
        self.assertRaises(Exception, Gaussian, Scope([]), 0.0, 1.0)
        self.assertRaises(Exception, Gaussian, Scope([0, 1]), 0.0, 1.0)
        self.assertRaises(Exception, Gaussian, Scope([0], [1]), 0.0, 1.0)

    def test_accept(self):

        # continuous meta type
        self.assertTrue(Gaussian.accepts([([FeatureTypes.Continuous], Scope([0]))]))

        # Gaussian feature type class
        self.assertTrue(Gaussian.accepts([([FeatureTypes.Gaussian], Scope([0]))]))

        # Gaussian feature type instance
        self.assertTrue(Gaussian.accepts([([FeatureTypes.Gaussian(0.0, 1.0)], Scope([0]))]))

        # invalid feature type
        self.assertFalse(Gaussian.accepts([([FeatureTypes.Discrete], Scope([0]))]))

        # conditional scope
        self.assertFalse(Gaussian.accepts([([FeatureTypes.Continuous], Scope([0], [1]))]))

        # scope length does not match number of types
        self.assertFalse(Gaussian.accepts([([FeatureTypes.Continuous], Scope([0, 1]))]))

        # multivariate signature
        self.assertFalse(Gaussian.accepts([([FeatureTypes.Continuous, FeatureTypes.Continuous], Scope([0, 1]))]))

    def test_initialization_from_signatures(self):

        gaussian = Gaussian.from_signatures([([FeatureTypes.Continuous], Scope([0]))])
        self.assertEqual(gaussian.mean, 0.0)
        self.assertEqual(gaussian.std, 1.0)

        gaussian = Gaussian.from_signatures([([FeatureTypes.Gaussian], Scope([0]))])
        self.assertEqual(gaussian.mean, 0.0)
        self.assertEqual(gaussian.std, 1.0)
    
        gaussian = Gaussian.from_signatures([([FeatureTypes.Gaussian(-1.0, 1.5)], Scope([0]))])
        self.assertEqual(gaussian.mean, -1.0)
        self.assertEqual(gaussian.std, 1.5)

        # ----- invalid arguments -----

        # invalid feature type
        self.assertRaises(ValueError, Gaussian.from_signatures, [([FeatureTypes.Discrete], Scope([0]))])

        # conditional scope
        self.assertRaises(ValueError, Gaussian.from_signatures, [([FeatureTypes.Continuous], Scope([0], [1]))])

        # scope length does not match number of types
        self.assertRaises(ValueError, Gaussian.from_signatures, [([FeatureTypes.Continuous], Scope([0, 1]))])

        # multivariate signature
        self.assertRaises(ValueError, Gaussian.from_signatures, [([FeatureTypes.Continuous, FeatureTypes.Continuous], Scope([0, 1]))])

    def test_autoleaf(self):

        # make sure leaf is registered
        self.assertTrue(AutoLeaf.is_registered(Gaussian))

        # make sure leaf is correctly inferred
        self.assertEqual(Gaussian, AutoLeaf.infer([([FeatureTypes.Gaussian], Scope([0]))]))

        # make sure AutoLeaf can return correctly instantiated object
        gaussian = AutoLeaf([([FeatureTypes.Gaussian(mean=-1.0, std=0.5)], Scope([0]))])
        self.assertTrue(isinstance(gaussian, Gaussian))
        self.assertEqual(gaussian.mean, -1.0)
        self.assertEqual(gaussian.std, 0.5)

    def test_structural_marginalization(self):

        gaussian = Gaussian(Scope([0]), 0.0, 1.0)

        self.assertTrue(marginalize(gaussian, [1]) is not None)
        self.assertTrue(marginalize(gaussian, [0]) is None)


if __name__ == "__main__":
    unittest.main()
