from spflow.meta.data import Scope
from spflow.meta.data.feature_types import FeatureTypes
from spflow.meta.data.feature_context import FeatureContext
from spflow.torch.structure.autoleaf import AutoLeaf
from spflow.meta.dispatch.dispatch_context import DispatchContext
from spflow.base.structure.general.nodes.leaves.parametric.cond_bernoulli import (
    CondBernoulli as BaseCondBernoulli,
)
from spflow.torch.structure.general.nodes.leaves.parametric.cond_bernoulli import (
    CondBernoulli,
    toBase,
    toTorch,
)
from spflow.torch.structure.spn.nodes.sum_node import marginalize
from typing import Callable

import torch
import numpy as np

import random
import unittest


class TestBernoulli(unittest.TestCase):
    def test_initialization(self):

        bernoulli = CondBernoulli(Scope([0], [1]))
        self.assertTrue(bernoulli.cond_f is None)
        bernoulli = CondBernoulli(Scope([0], [1]), lambda x: {"p": 0.5})
        self.assertTrue(isinstance(bernoulli.cond_f, Callable))

        # invalid scopes
        self.assertRaises(Exception, CondBernoulli, Scope([]))
        self.assertRaises(Exception, CondBernoulli, Scope([0, 1], [2]))
        self.assertRaises(Exception, CondBernoulli, Scope([0]))

    def test_retrieve_params(self):

        # Valid parameters for Bernoulli distribution: p in [0,1]

        bernoulli = CondBernoulli(Scope([0], [1]))

        # p = 0
        bernoulli.set_cond_f(lambda data: {"p": 0.0})
        self.assertTrue(
            bernoulli.retrieve_params(np.array([[1.0]]), DispatchContext())
            == 0.0
        )
        # p = 1
        bernoulli.set_cond_f(lambda data: {"p": 1.0})
        self.assertTrue(
            bernoulli.retrieve_params(np.array([[1.0]]), DispatchContext())
            == 1.0
        )
        # p < 0 and p > 1
        bernoulli.set_cond_f(
            lambda data: {
                "p": torch.nextafter(torch.tensor(1.0), torch.tensor(2.0))
            }
        )
        self.assertRaises(
            Exception,
            bernoulli.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )

        bernoulli.set_cond_f(
            lambda data: {
                "p": torch.nextafter(torch.tensor(0.0), -torch.tensor(1.0))
            }
        )
        self.assertRaises(
            Exception,
            bernoulli.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )

        # p = inf and p = nan
        bernoulli.set_cond_f(lambda data: {"p": np.inf})
        self.assertRaises(
            Exception,
            bernoulli.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )

        bernoulli.set_cond_f(lambda data: {"p": np.nan})
        self.assertRaises(
            Exception,
            bernoulli.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )

    def test_accept(self):

        # discrete meta type
        self.assertTrue(
            CondBernoulli.accepts(
                [FeatureContext(Scope([0], [1]), [FeatureTypes.Discrete])]
            )
        )

        # Bernoulli feature type class
        self.assertTrue(
            CondBernoulli.accepts(
                [FeatureContext(Scope([0], [1]), [FeatureTypes.Bernoulli])]
            )
        )

        # Bernoulli feature type instance
        self.assertTrue(
            CondBernoulli.accepts(
                [FeatureContext(Scope([0], [1]), [FeatureTypes.Bernoulli(0.5)])]
            )
        )

        # invalid feature type
        self.assertFalse(
            CondBernoulli.accepts(
                [FeatureContext(Scope([0], [1]), [FeatureTypes.Continuous])]
            )
        )

        # non-conditional scope
        self.assertFalse(
            CondBernoulli.accepts(
                [FeatureContext(Scope([0]), [FeatureTypes.Discrete])]
            )
        )

        # multivariate signature
        self.assertFalse(
            CondBernoulli.accepts(
                [
                    FeatureContext(
                        Scope([0, 1], [2]),
                        [FeatureTypes.Discrete, FeatureTypes.Discrete],
                    )
                ]
            )
        )

    def test_initialization_from_signatures(self):

        CondBernoulli.from_signatures(
            [FeatureContext(Scope([0], [1]), [FeatureTypes.Discrete])]
        )
        CondBernoulli.from_signatures(
            [FeatureContext(Scope([0], [1]), [FeatureTypes.Bernoulli])]
        )
        CondBernoulli.from_signatures(
            [FeatureContext(Scope([0], [1]), [FeatureTypes.Bernoulli(p=0.75)])]
        )

        # ----- invalid arguments -----

        # invalid feature type
        self.assertRaises(
            ValueError,
            CondBernoulli.from_signatures,
            [FeatureContext(Scope([0], [1]), [FeatureTypes.Continuous])],
        )

        # non-conditional scope
        self.assertRaises(
            ValueError,
            CondBernoulli.from_signatures,
            [FeatureContext(Scope([0]), [FeatureTypes.Discrete])],
        )

        # multivariate signature
        self.assertRaises(
            ValueError,
            CondBernoulli.from_signatures,
            [
                FeatureContext(
                    Scope([0, 1], [2]),
                    [FeatureTypes.Discrete, FeatureTypes.Discrete],
                )
            ],
        )

    def test_autoleaf(self):

        # make sure leaf is registered
        self.assertTrue(AutoLeaf.is_registered(CondBernoulli))

        # make sure leaf is correctly inferred
        self.assertEqual(
            CondBernoulli,
            AutoLeaf.infer(
                [FeatureContext(Scope([0], [1]), [FeatureTypes.Bernoulli])]
            ),
        )

        # make sure AutoLeaf can return correctly instantiated object
        bernoulli = AutoLeaf(
            [FeatureContext(Scope([0], [1]), [FeatureTypes.Bernoulli])]
        )
        self.assertTrue(isinstance(bernoulli, CondBernoulli))

    def test_structural_marginalization(self):

        bernoulli = CondBernoulli(Scope([0], [1]))

        self.assertTrue(marginalize(bernoulli, [1]) is not None)
        self.assertTrue(marginalize(bernoulli, [0]) is None)

    def test_base_backend_conversion(self):

        p = random.random()

        # test scope instead
        torch_bernoulli = CondBernoulli(Scope([0], [1]), p)
        node_bernoulli = BaseCondBernoulli(Scope([0], [1]), p)

        # check conversion from torch to python
        self.assertTrue(
            np.all(
                torch_bernoulli.scopes_out == toBase(torch_bernoulli).scopes_out
            )
        )
        # check conversion from python to torch
        self.assertTrue(
            np.all(
                node_bernoulli.scopes_out == toTorch(node_bernoulli).scopes_out
            )
        )


if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    unittest.main()