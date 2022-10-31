from spflow.base.structure.layers.leaves.parametric.exponential import (
    ExponentialLayer,
    marginalize,
)
from spflow.base.structure.autoleaf import AutoLeaf
from spflow.base.structure.nodes.leaves.parametric.exponential import (
    Exponential,
)
from spflow.meta.data.scope import Scope
from spflow.meta.data.feature_types import FeatureTypes
import numpy as np
import unittest


class TestLayer(unittest.TestCase):
    def test_layer_initialization_1(self):

        # ----- check attributes after correct initialization -----

        l = ExponentialLayer(scope=Scope([1]), n_nodes=3, l=1.5)
        # make sure number of creates nodes is correct
        self.assertEqual(len(l.nodes), 3)
        # make sure scopes are correct
        self.assertTrue(
            np.all(l.scopes_out == [Scope([1]), Scope([1]), Scope([1])])
        )
        # make sure parameter properties works correctly
        l_values = l.l
        for node, node_l in zip(l.nodes, l_values):
            self.assertTrue(np.all(node.l == node_l))

        # ----- float/int parameter values -----
        l_value = 2
        l = ExponentialLayer(scope=Scope([1]), n_nodes=3, l=l_value)

        for node in l.nodes:
            self.assertTrue(np.all(node.l == l_value))

        # ----- list parameter values -----
        l_values = [1.0, 2.0, 3.0]
        l = ExponentialLayer(scope=Scope([1]), n_nodes=3, l=l_values)

        for node, node_l in zip(l.nodes, l_values):
            self.assertTrue(np.all(node.l == node_l))

        # wrong number of values
        self.assertRaises(
            ValueError, ExponentialLayer, Scope([0]), l_values[:-1], n_nodes=3
        )
        # wrong number of dimensions (nested list)
        self.assertRaises(
            ValueError,
            ExponentialLayer,
            Scope([0]),
            [l_values for _ in range(3)],
            n_nodes=3,
        )

        # ----- numpy parameter values -----

        l = ExponentialLayer(scope=Scope([1]), n_nodes=3, l=np.array(l_values))

        for node, node_l in zip(l.nodes, l_values):
            self.assertTrue(np.all(node.l == node_l))

        # wrong number of values
        self.assertRaises(
            ValueError,
            ExponentialLayer,
            Scope([0]),
            np.array(l_values[:-1]),
            n_nodes=3,
        )
        self.assertRaises(
            ValueError,
            ExponentialLayer,
            Scope([0]),
            np.array([l_values for _ in range(3)]),
            n_nodes=3,
        )

        # ---- different scopes -----
        l = ExponentialLayer(scope=Scope([1]), l=1.5, n_nodes=3)
        for node, node_scope in zip(l.nodes, l.scopes_out):
            self.assertEqual(node.scope, node_scope)

        # ----- invalid number of nodes -----
        self.assertRaises(
            ValueError, ExponentialLayer, Scope([0]), 1.5, n_nodes=0
        )

        # ----- invalid scope -----
        self.assertRaises(
            ValueError, ExponentialLayer, Scope([]), 1.5, n_nodes=3
        )
        self.assertRaises(ValueError, ExponentialLayer, [], n_nodes=3)

        # ----- individual scopes and parameters -----
        scopes = [Scope([1]), Scope([0]), Scope([0])]
        l = ExponentialLayer(scope=[Scope([1]), Scope([0])], l=1.5, n_nodes=3)
        for node, node_scope in zip(l.nodes, scopes):
            self.assertEqual(node.scope, node_scope)

    def test_accept(self):

        # continuous meta type
        self.assertTrue(ExponentialLayer.accepts([([FeatureTypes.Continuous], Scope([0])), ([FeatureTypes.Continuous], Scope([1]))]))

        # Exponential feature type class
        self.assertTrue(ExponentialLayer.accepts([([FeatureTypes.Exponential], Scope([0])), ([FeatureTypes.Continuous], Scope([1]))]))

        # Exponential feature type instance
        self.assertTrue(ExponentialLayer.accepts([([FeatureTypes.Exponential(1.0)], Scope([0])), ([FeatureTypes.Continuous], Scope([1]))]))

        # invalid feature type
        self.assertFalse(ExponentialLayer.accepts([([FeatureTypes.Discrete], Scope([0])), ([FeatureTypes.Continuous], Scope([1]))]))

        # conditional scope
        self.assertFalse(ExponentialLayer.accepts([([FeatureTypes.Continuous], Scope([0], [1]))]))

        # scope length does not match number of types
        self.assertFalse(ExponentialLayer.accepts([([FeatureTypes.Continuous], Scope([0, 1]))]))

        # multivariate signature
        self.assertFalse(ExponentialLayer.accepts([([FeatureTypes.Continuous, FeatureTypes.Continuous], Scope([0, 1]))]))

    def test_initialization_from_signatures(self):

        exponential = ExponentialLayer.from_signatures([([FeatureTypes.Continuous], Scope([0])), ([FeatureTypes.Continuous], Scope([1]))])
        self.assertTrue(np.all(exponential.l == np.array([1.0, 1.0])))
        self.assertTrue(exponential.scopes_out == [Scope([0]), Scope([1])])

        exponential = ExponentialLayer.from_signatures([([FeatureTypes.Exponential], Scope([0])), ([FeatureTypes.Exponential], Scope([1]))])
        self.assertTrue(np.all(exponential.l == np.array([1.0, 1.0])))
        self.assertTrue(exponential.scopes_out == [Scope([0]), Scope([1])])

        exponential = ExponentialLayer.from_signatures([([FeatureTypes.Exponential(l=1.5)], Scope([0])), ([FeatureTypes.Exponential(l=0.5)], Scope([1]))])
        self.assertTrue(np.all(exponential.l == np.array([1.5, 0.5])))
        self.assertTrue(exponential.scopes_out == [Scope([0]), Scope([1])])

        # ----- invalid arguments -----

        # invalid feature type
        self.assertRaises(ValueError, ExponentialLayer.from_signatures, [([FeatureTypes.Discrete], Scope([0]))])

        # conditional scope
        self.assertRaises(ValueError, ExponentialLayer.from_signatures, [([FeatureTypes.Continuous], Scope([0], [1]))])

        # scope length does not match number of types
        self.assertRaises(ValueError, ExponentialLayer.from_signatures, [([FeatureTypes.Continuous], Scope([0, 1]))])

        # multivariate signature
        self.assertRaises(ValueError, ExponentialLayer.from_signatures, [([FeatureTypes.Continuous, FeatureTypes.Continuous], Scope([0, 1]))])

    def test_autoleaf(self):

        # make sure leaf is registered
        self.assertTrue(AutoLeaf.is_registered(ExponentialLayer))

        # make sure leaf is correctly inferred
        self.assertEqual(ExponentialLayer, AutoLeaf.infer([([FeatureTypes.Exponential], Scope([0])), ([FeatureTypes.Exponential], Scope([1]))]))

        # make sure AutoLeaf can return correctly instantiated object
        exponential = AutoLeaf([([FeatureTypes.Exponential(l=1.5)], Scope([0])), ([FeatureTypes.Exponential(l=0.5)], Scope([1]))])
        self.assertTrue(np.all(exponential.l == np.array([1.5, 0.5])))
        self.assertTrue(exponential.scopes_out == [Scope([0]), Scope([1])])

    def test_layer_structural_marginalization(self):

        # ---------- same scopes -----------

        l = ExponentialLayer(scope=Scope([1]), l=[1.5, 2.0], n_nodes=2)

        # ----- marginalize over entire scope -----
        self.assertTrue(marginalize(l, [1]) == None)

        # ----- marginalize over non-scope rvs -----
        l_marg = marginalize(l, [2])

        self.assertTrue(l_marg.scopes_out == [Scope([1]), Scope([1])])
        self.assertTrue(np.all(l.l == l_marg.l))

        # ---------- different scopes -----------

        l = ExponentialLayer(scope=[Scope([1]), Scope([0])], l=[1.5, 2.0])

        # ----- marginalize over entire scope -----
        self.assertTrue(marginalize(l, [0, 1]) == None)

        # ----- partially marginalize -----
        l_marg = marginalize(l, [1], prune=True)
        self.assertTrue(isinstance(l_marg, Exponential))
        self.assertEqual(l_marg.scope, Scope([0]))
        self.assertEqual(l_marg.l, 2.0)

        l_marg = marginalize(l, [1], prune=False)
        self.assertTrue(isinstance(l_marg, ExponentialLayer))
        self.assertEqual(len(l_marg.nodes), 1)
        self.assertEqual(l_marg.l, np.array([2.0]))

        # ----- marginalize over non-scope rvs -----
        l_marg = marginalize(l, [2])

        self.assertTrue(l_marg.scopes_out == [Scope([1]), Scope([0])])
        self.assertTrue(np.all(l.l == l_marg.l))

    def test_get_params(self):

        layer = ExponentialLayer(scope=Scope([1]), l=[0.73, 0.29], n_nodes=2)

        l, *others = layer.get_params()

        self.assertTrue(len(others) == 0)
        self.assertTrue(np.allclose(l, np.array([0.73, 0.29])))


if __name__ == "__main__":
    unittest.main()
