from spflow.meta.data.scope import Scope
from spflow.meta.data.feature_types import FeatureTypes
from spflow.meta.dispatch.dispatch_context import DispatchContext
from spflow.base.structure.autoleaf import AutoLeaf
from spflow.base.structure.nodes.node import marginalize
from spflow.base.structure.nodes.leaves.parametric.cond_exponential import (
    CondExponential,
)
from typing import Callable

import numpy as np
import unittest


class TestCondExponential(unittest.TestCase):
    def test_initialization(self):

        binomial = CondExponential(Scope([0], [1]))
        self.assertTrue(binomial.cond_f is None)
        binomial = CondExponential(Scope([0], [1]), cond_f=lambda x: {"l": 0.5})
        self.assertTrue(isinstance(binomial.cond_f, Callable))

        # invalid scopes
        self.assertRaises(Exception, CondExponential, Scope([]))
        self.assertRaises(Exception, CondExponential, Scope([0]))
        self.assertRaises(Exception, CondExponential, Scope([0, 1], [2]))

    def test_retrieve_params(self):

        # Valid parameters for Exponential distribution: l>0

        exponential = CondExponential(Scope([0], [1]))

        # l > 0
        exponential.set_cond_f(lambda data: {"l": np.nextafter(0.0, 1.0)})
        self.assertTrue(
            exponential.retrieve_params(np.array([[1.0]]), DispatchContext())
            == np.nextafter(0.0, 1.0)
        )
        # l = 0 and l < 0
        exponential.set_cond_f(lambda data: {"l": 0.0})
        self.assertRaises(
            ValueError,
            exponential.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )
        exponential.set_cond_f(lambda data: {"l": np.nextafter(0.0, -1.0)})
        self.assertRaises(
            ValueError,
            exponential.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )
        # l = inf and l = nan
        exponential.set_cond_f(lambda data: {"l": np.inf})
        self.assertRaises(
            ValueError,
            exponential.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )
        exponential.set_cond_f(lambda data: {"l": np.nan})
        self.assertRaises(
            ValueError,
            exponential.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )

    def test_accept(self):

        # continuous meta type
        self.assertTrue(CondExponential.accepts([([FeatureTypes.Continuous], Scope([0], [1]))]))

        # Exponential feature type class
        self.assertTrue(CondExponential.accepts([([FeatureTypes.Exponential], Scope([0], [1]))]))

        # Exponential feature type instance
        self.assertTrue(CondExponential.accepts([([FeatureTypes.Exponential(1.0)], Scope([0], [1]))]))

        # invalid feature type
        self.assertFalse(CondExponential.accepts([([FeatureTypes.Discrete], Scope([0], [1]))]))

        # non-conditional scope
        self.assertFalse(CondExponential.accepts([([FeatureTypes.Continuous], Scope([0]))]))

        # scope length does not match number of types
        self.assertFalse(CondExponential.accepts([([FeatureTypes.Continuous], Scope([0, 1], [2]))]))

        # multivariate signature
        self.assertFalse(CondExponential.accepts([([FeatureTypes.Continuous, FeatureTypes.Continuous], Scope([0, 1], [2]))]))

    def test_initialization_from_signatures(self):

        CondExponential.from_signatures([([FeatureTypes.Continuous], Scope([0], [1]))])
        CondExponential.from_signatures([([FeatureTypes.Exponential], Scope([0], [1]))])
        CondExponential.from_signatures([([FeatureTypes.Exponential(l=1.5)], Scope([0], [1]))])

        # ----- invalid arguments -----

        # invalid feature type
        self.assertRaises(ValueError, CondExponential.from_signatures, [([FeatureTypes.Discrete], Scope([0], [1]))])

        # non-conditional scope
        self.assertRaises(ValueError, CondExponential.from_signatures, [([FeatureTypes.Continuous], Scope([0]))])

        # scope length does not match number of types
        self.assertRaises(ValueError, CondExponential.from_signatures, [([FeatureTypes.Continuous], Scope([0, 1], [2]))])

        # multivariate signature
        self.assertRaises(ValueError, CondExponential.from_signatures, [([FeatureTypes.Continuous, FeatureTypes.Continuous], Scope([0, 1], [2]))])

    def test_autoleaf(self):

        # make sure leaf is registered
        self.assertTrue(AutoLeaf.is_registered(CondExponential))

        # make sure leaf is correctly inferred
        self.assertEqual(CondExponential, AutoLeaf.infer([([FeatureTypes.Exponential], Scope([0], [1]))]))

        # make sure AutoLeaf can return correctly instantiated object
        exponential = AutoLeaf([([FeatureTypes.Exponential], Scope([0], [1]))])
        self.assertTrue(isinstance(exponential, CondExponential))

    def test_structural_marginalization(self):

        exponential = CondExponential(Scope([0], [2]), 1.0)

        self.assertTrue(marginalize(exponential, [1]) is not None)
        self.assertTrue(marginalize(exponential, [0]) is None)


if __name__ == "__main__":
    unittest.main()
