from spflow.base.structure.layers.leaves.parametric.bernoulli import (
    BernoulliLayer,
    marginalize,
)
from spflow.base.structure.autoleaf import AutoLeaf
from spflow.base.structure.nodes.leaves.parametric.bernoulli import Bernoulli
from spflow.meta.data.scope import Scope
from spflow.meta.data.feature_types import FeatureTypes
import numpy as np
import unittest


class TestLayer(unittest.TestCase):
    def test_layer_initialization_1(self):

        # ----- check attributes after correct initialization -----

        l = BernoulliLayer(scope=Scope([1]), n_nodes=3)
        # make sure number of creates nodes is correct
        self.assertEqual(len(l.nodes), 3)
        # make sure scopes are correct
        self.assertTrue(
            np.all(l.scopes_out == [Scope([1]), Scope([1]), Scope([1])])
        )
        # make sure parameter properties works correctly
        p_values = l.p
        for node, node_p in zip(l.nodes, p_values):
            self.assertTrue(np.all(node.p == node_p))

        # ----- float/int parameter values -----
        p_value = 0.13
        l = BernoulliLayer(scope=Scope([1]), n_nodes=3, p=p_value)

        for node in l.nodes:
            self.assertTrue(np.all(node.p == p_value))

        # ----- list parameter values -----
        p_values = [0.17, 0.8, 0.53]
        l = BernoulliLayer(scope=Scope([1]), n_nodes=3, p=p_values)

        for node, node_p in zip(l.nodes, p_values):
            self.assertTrue(np.all(node.p == node_p))

        # wrong number of values
        self.assertRaises(
            ValueError, BernoulliLayer, Scope([0]), p_values[:-1], n_nodes=3
        )
        # wrong number of dimensions (nested list)
        self.assertRaises(
            ValueError,
            BernoulliLayer,
            Scope([0]),
            [p_values for _ in range(3)],
            n_nodes=3,
        )

        # ----- numpy parameter values -----

        l = BernoulliLayer(scope=Scope([1]), n_nodes=3, p=np.array(p_values))

        for node, node_p in zip(l.nodes, p_values):
            self.assertTrue(np.all(node.p == node_p))

        # wrong number of values
        self.assertRaises(
            ValueError,
            BernoulliLayer,
            Scope([0]),
            np.array(p_values[:-1]),
            n_nodes=3,
        )
        self.assertRaises(
            ValueError,
            BernoulliLayer,
            Scope([0]),
            np.array([p_values for _ in range(3)]),
            n_nodes=3,
        )

        # ---- different scopes -----
        l = BernoulliLayer(scope=Scope([1]), n_nodes=3)
        for node, node_scope in zip(l.nodes, l.scopes_out):
            self.assertEqual(node.scope, node_scope)

        # ----- invalid number of nodes -----
        self.assertRaises(ValueError, BernoulliLayer, Scope([0]), n_nodes=0)

        # ----- invalid scope -----
        self.assertRaises(ValueError, BernoulliLayer, Scope([]), n_nodes=3)
        self.assertRaises(ValueError, BernoulliLayer, [], n_nodes=3)

        # ----- individual scopes and parameters -----
        scopes = [Scope([1]), Scope([0]), Scope([0])]
        l = BernoulliLayer(scope=[Scope([1]), Scope([0])], n_nodes=3)
        for node, node_scope in zip(l.nodes, scopes):
            self.assertEqual(node.scope, node_scope)

    def test_accept(self):

        # discrete meta type
        self.assertTrue(BernoulliLayer.accepts([([FeatureTypes.Discrete], Scope([0])), ([FeatureTypes.Discrete], Scope([1]))]))

        # Bernoulli feature type class
        self.assertTrue(BernoulliLayer.accepts([([FeatureTypes.Bernoulli], Scope([0])), ([FeatureTypes.Discrete], Scope([1]))]))

        # Bernoulli feature type instance
        self.assertTrue(BernoulliLayer.accepts([([FeatureTypes.Bernoulli(0.5)], Scope([0])), ([FeatureTypes.Bernoulli(0.5)], Scope([1]))]))

        # invalid feature type
        self.assertFalse(BernoulliLayer.accepts([([FeatureTypes.Continuous], Scope([0])), ([FeatureTypes.Continuous], Scope([1]))]))

        # conditional scope
        self.assertFalse(BernoulliLayer.accepts([([FeatureTypes.Discrete], Scope([0], [1]))]))

        # scope length does not match number of types
        self.assertFalse(BernoulliLayer.accepts([([FeatureTypes.Discrete], Scope([0, 1]))]))

        # multivariate signature
        self.assertFalse(BernoulliLayer.accepts([([FeatureTypes.Discrete, FeatureTypes.Discrete], Scope([0, 1]))]))

    def test_initialization_from_signatures(self):

        bernoulli = BernoulliLayer.from_signatures([([FeatureTypes.Discrete], Scope([0])), ([FeatureTypes.Discrete], Scope([1]))])
        self.assertTrue(np.all(bernoulli.p == np.array([0.5, 0.5])))
        self.assertTrue(bernoulli.scopes_out == [Scope([0]), Scope([1])])

        bernoulli = BernoulliLayer.from_signatures([([FeatureTypes.Bernoulli], Scope([0])), ([FeatureTypes.Bernoulli], Scope([1]))])
        self.assertTrue(np.all(bernoulli.p == np.array([0.5, 0.5])))
        self.assertTrue(bernoulli.scopes_out == [Scope([0]), Scope([1])])
    
        bernoulli = BernoulliLayer.from_signatures([([FeatureTypes.Bernoulli(p=0.75)], Scope([0])), ([FeatureTypes.Bernoulli(p=0.25)], Scope([1]))])
        self.assertTrue(np.all(bernoulli.p == np.array([0.75, 0.25])))
        self.assertTrue(bernoulli.scopes_out == [Scope([0]), Scope([1])])

        # ----- invalid arguments -----

        # invalid feature type
        self.assertRaises(ValueError, BernoulliLayer.from_signatures, [([FeatureTypes.Continuous], Scope([0]))])

        # conditional scope
        self.assertRaises(ValueError, BernoulliLayer.from_signatures, [([FeatureTypes.Discrete], Scope([0], [1]))])

        # scope length does not match number of types
        self.assertRaises(ValueError, BernoulliLayer.from_signatures, [([FeatureTypes.Discrete], Scope([0, 1]))])

        # multivariate signature
        self.assertRaises(ValueError, BernoulliLayer.from_signatures, [([FeatureTypes.Discrete, FeatureTypes.Discrete], Scope([0, 1]))])

    def test_autoleaf(self):

        # make sure leaf is registered
        self.assertTrue(AutoLeaf.is_registered(BernoulliLayer))

        # make sure leaf is correctly inferred
        self.assertEqual(BernoulliLayer, AutoLeaf.infer([([FeatureTypes.Bernoulli()], Scope([0])), ([FeatureTypes.Bernoulli()], Scope([1]))]))

        # make sure AutoLeaf can return correctly instantiated object
        bernoulli = AutoLeaf([([FeatureTypes.Bernoulli(p=0.75)], Scope([0])), ([FeatureTypes.Bernoulli(p=0.25)], Scope([1]))])
        self.assertTrue(np.all(bernoulli.p == np.array([0.75, 0.25])))
        self.assertTrue(bernoulli.scopes_out == [Scope([0]), Scope([1])])

    def test_layer_structural_marginalization(self):

        # ---------- same scopes -----------

        l = BernoulliLayer(scope=Scope([1]), p=[0.73, 0.29], n_nodes=2)

        # ----- marginalize over entire scope -----
        self.assertTrue(marginalize(l, [1]) == None)

        # ----- marginalize over non-scope rvs -----
        l_marg = marginalize(l, [2])

        self.assertTrue(l_marg.scopes_out == [Scope([1]), Scope([1])])
        self.assertTrue(np.all(l.p == l_marg.p))

        # ---------- different scopes -----------

        l = BernoulliLayer(scope=[Scope([1]), Scope([0])], p=[0.73, 0.29])

        # ----- marginalize over entire scope -----
        self.assertTrue(marginalize(l, [0, 1]) == None)

        # ----- partially marginalize -----
        l_marg = marginalize(l, [1], prune=True)
        self.assertTrue(isinstance(l_marg, Bernoulli))
        self.assertEqual(l_marg.scope, Scope([0]))
        self.assertEqual(l_marg.p, np.array([0.29]))

        l_marg = marginalize(l, [1], prune=False)
        self.assertTrue(isinstance(l_marg, BernoulliLayer))
        self.assertEqual(len(l_marg.nodes), 1)
        self.assertEqual(l_marg.p, np.array([0.29]))

        # ----- marginalize over non-scope rvs -----
        l_marg = marginalize(l, [2])

        self.assertTrue(l_marg.scopes_out == [Scope([1]), Scope([0])])
        self.assertTrue(np.all(l.p == l_marg.p))

    def test_get_params(self):

        l = BernoulliLayer(scope=Scope([1]), p=[0.73, 0.29], n_nodes=2)

        p, *others = l.get_params()

        self.assertTrue(len(others) == 0)
        self.assertTrue(np.allclose(p, np.array([0.73, 0.29])))


if __name__ == "__main__":
    unittest.main()
