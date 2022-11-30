from spflow.meta.data import Scope, FeatureTypes, FeatureContext
from spflow.base.structure.spn import (
    NegativeBinomial,
    NegativeBinomialLayer,
    marginalize,
)
from spflow.base.structure import AutoLeaf
import numpy as np
import unittest


class TestLayer(unittest.TestCase):
    def test_layer_initialization_1(self):

        # ----- check attributes after correct initialization -----

        l = NegativeBinomialLayer(scope=Scope([1]), n_nodes=3, n=2)
        # make sure number of creates nodes is correct
        self.assertEqual(len(l.nodes), 3)
        # make sure scopes are correct
        self.assertTrue(
            np.all(l.scopes_out == [Scope([1]), Scope([1]), Scope([1])])
        )
        # make sure parameter properties works correctly
        n_values = l.n
        p_values = l.p
        for node, node_n, node_p in zip(l.nodes, n_values, p_values):
            self.assertTrue(np.all(node.n == node_n))
            self.assertTrue(np.all(node.p == node_p))

        # ----- float/int parameter values -----
        n_value = 2
        p_value = 0.5
        l = NegativeBinomialLayer(
            scope=Scope([1]), n_nodes=3, n=n_value, p=p_value
        )

        for node in l.nodes:
            self.assertTrue(np.all(node.n == n_value))
            self.assertTrue(np.all(node.p == p_value))

        # ----- list parameter values -----
        n_values = [1, 5, 4]
        p_values = [0.25, 0.5, 0.3]
        l = NegativeBinomialLayer(
            scope=[Scope([1]), Scope([0]), Scope([2])], n=n_values, p=p_values
        )

        for node, node_n, node_p in zip(l.nodes, n_values, p_values):
            self.assertTrue(np.all(node.n == node_n))
            self.assertTrue(np.all(node.p == node_p))

        # wrong number of values
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer,
            [Scope([1]), Scope([0]), Scope([2])],
            n_values[:-1],
            p_values,
            n_nodes=3,
        )
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer,
            [Scope([1]), Scope([0]), Scope([2])],
            n_values,
            p_values[:-1],
            n_nodes=3,
        )
        # wrong number of dimensions (nested list)
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer,
            [Scope([1]), Scope([0]), Scope([2])],
            [n_values for _ in range(3)],
            p_values,
            n_nodes=3,
        )
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer,
            [Scope([1]), Scope([0]), Scope([2])],
            n_values,
            [p_values for _ in range(3)],
            n_nodes=3,
        )

        # ----- numpy parameter values -----

        l = NegativeBinomialLayer(
            scope=[Scope([1]), Scope([0]), Scope([2])],
            n=np.array(n_values),
            p=np.array(p_values),
        )

        for node, node_n, node_p in zip(l.nodes, n_values, p_values):
            self.assertTrue(np.all(node.n == node_n))
            self.assertTrue(np.all(node.p == node_p))

        # wrong number of values
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer,
            [Scope([1]), Scope([0]), Scope([2])],
            np.array(n_values[:-1]),
            np.array(p_values),
            n_nodes=3,
        )
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer,
            [Scope([1]), Scope([0]), Scope([2])],
            np.array(n_values),
            np.array(p_values[:-1]),
            n_nodes=3,
        )
        # wrong number of dimensions (nested list)
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer,
            [Scope([1]), Scope([0]), Scope([2])],
            n_values,
            np.array([p_values for _ in range(3)]),
            n_nodes=3,
        )
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer,
            [Scope([1]), Scope([0]), Scope([2])],
            np.array([n_values for _ in range(3)]),
            p_values,
            n_nodes=3,
        )

        # ---- different scopes -----
        l = NegativeBinomialLayer(scope=Scope([1]), n=5, n_nodes=3)
        for node, node_scope in zip(l.nodes, l.scopes_out):
            self.assertEqual(node.scope, node_scope)

        # ----- invalid number of nodes -----
        self.assertRaises(
            ValueError, NegativeBinomialLayer, Scope([0]), 2, n_nodes=0
        )

        # ----- invalid scope -----
        self.assertRaises(
            ValueError, NegativeBinomialLayer, Scope([]), 2, n_nodes=3
        )
        self.assertRaises(ValueError, NegativeBinomialLayer, [], 2, n_nodes=3)

        # ----- invalid values for 'n' over same scope -----
        self.assertRaises(
            ValueError, NegativeBinomialLayer, Scope([0]), n=[2, 5], n_nodes=2
        )

        # ----- individual scopes and parameters -----
        scopes = [Scope([1]), Scope([0])]
        l = NegativeBinomialLayer(
            scope=[Scope([1]), Scope([0])], n=2, p=0.5, n_nodes=3
        )
        for node, node_scope in zip(l.nodes, scopes):
            self.assertEqual(node.scope, node_scope)

    def test_accept(self):

        # discrete meta type (should reject)
        self.assertFalse(
            NegativeBinomialLayer.accepts(
                [
                    FeatureContext(Scope([0]), [FeatureTypes.Discrete]),
                    FeatureContext(Scope([1]), [FeatureTypes.Discrete]),
                ]
            )
        )

        # feature type instance
        self.assertTrue(
            NegativeBinomialLayer.accepts(
                [
                    FeatureContext(
                        Scope([0]), [FeatureTypes.NegativeBinomial(n=3)]
                    ),
                    FeatureContext(
                        Scope([1]), [FeatureTypes.NegativeBinomial(n=3)]
                    ),
                ]
            )
        )

        # invalid feature type
        self.assertFalse(
            NegativeBinomialLayer.accepts(
                [
                    FeatureContext(Scope([0]), [FeatureTypes.Continuous]),
                    FeatureContext(
                        Scope([1]), [FeatureTypes.NegativeBinomial(n=3)]
                    ),
                ]
            )
        )

        # conditional scope
        self.assertFalse(
            NegativeBinomialLayer.accepts(
                [
                    FeatureContext(
                        Scope([0], [1]), [FeatureTypes.NegativeBinomial(n=3)]
                    )
                ]
            )
        )

        # multivariate signature
        self.assertFalse(
            NegativeBinomialLayer.accepts(
                [
                    FeatureContext(
                        Scope([0, 1]),
                        [
                            FeatureTypes.NegativeBinomial(n=3),
                            FeatureTypes.Binomial(n=3),
                        ],
                    )
                ]
            )
        )

    def test_initialization_from_signatures(self):

        negative_binomial = NegativeBinomialLayer.from_signatures(
            [
                FeatureContext(
                    Scope([0]), [FeatureTypes.NegativeBinomial(n=3)]
                ),
                FeatureContext(
                    Scope([1]), [FeatureTypes.NegativeBinomial(n=5)]
                ),
            ]
        )
        self.assertTrue(np.all(negative_binomial.n == np.array([3, 5])))
        self.assertTrue(np.all(negative_binomial.p == np.array([0.5, 0.5])))
        self.assertTrue(
            negative_binomial.scopes_out == [Scope([0]), Scope([1])]
        )

        # ----- invalid arguments -----

        # discrete meta type
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer.from_signatures,
            [FeatureContext(Scope([0]), [FeatureTypes.Discrete])],
        )

        # invalid feature type
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer.from_signatures,
            [FeatureContext(Scope([0]), [FeatureTypes.Continuous])],
        )

        # conditional scope
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer.from_signatures,
            [
                FeatureContext(
                    Scope([0], [1]), [FeatureTypes.NegativeBinomial(3)]
                )
            ],
        )

        # multivariate signature
        self.assertRaises(
            ValueError,
            NegativeBinomialLayer.from_signatures,
            [
                FeatureContext(
                    Scope([0, 1]),
                    [
                        FeatureTypes.NegativeBinomial(3),
                        FeatureTypes.NegativeBinomial(5),
                    ],
                )
            ],
        )

    def test_autoleaf(self):

        # make sure leaf is registered
        self.assertTrue(AutoLeaf.is_registered(NegativeBinomialLayer))

        # make sure leaf is correctly inferred
        self.assertEqual(
            NegativeBinomialLayer,
            AutoLeaf.infer(
                [
                    FeatureContext(
                        Scope([0]), [FeatureTypes.NegativeBinomial(n=3)]
                    ),
                    FeatureContext(
                        Scope([1]), [FeatureTypes.NegativeBinomial(n=5)]
                    ),
                ]
            ),
        )

        # make sure AutoLeaf can return correctly instantiated object
        negative_binomial = AutoLeaf(
            [
                FeatureContext(
                    Scope([0]), [FeatureTypes.NegativeBinomial(n=3, p=0.75)]
                ),
                FeatureContext(
                    Scope([1]), [FeatureTypes.NegativeBinomial(n=5, p=0.25)]
                ),
            ]
        )
        self.assertTrue(np.all(negative_binomial.n == np.array([3, 5])))
        self.assertTrue(np.all(negative_binomial.p == np.array([0.75, 0.25])))
        self.assertTrue(
            negative_binomial.scopes_out == [Scope([0]), Scope([1])]
        )

    def test_layer_structural_marginalization(self):

        # ---------- same scopes -----------

        l = NegativeBinomialLayer(
            scope=Scope([1]), n=2, p=[0.5, 0.3], n_nodes=2
        )

        # ----- marginalize over entire scope -----
        self.assertTrue(marginalize(l, [1]) == None)

        # ----- marginalize over non-scope rvs -----
        l_marg = marginalize(l, [2])

        self.assertTrue(l_marg.scopes_out == [Scope([1]), Scope([1])])
        self.assertTrue(np.all(l.n == l_marg.n))
        self.assertTrue(np.all(l.p == l_marg.p))

        # ---------- different scopes -----------

        l = NegativeBinomialLayer(
            scope=[Scope([1]), Scope([0])], n=[2, 6], p=[0.5, 0.3]
        )

        # ----- marginalize over entire scope -----
        self.assertTrue(marginalize(l, [0, 1]) == None)

        # ----- partially marginalize -----
        l_marg = marginalize(l, [1], prune=True)
        self.assertTrue(isinstance(l_marg, NegativeBinomial))
        self.assertEqual(l_marg.scope, Scope([0]))
        self.assertEqual(l_marg.n, np.array([6]))
        self.assertEqual(l_marg.p, np.array([0.3]))

        l_marg = marginalize(l, [1], prune=False)
        self.assertTrue(isinstance(l_marg, NegativeBinomialLayer))
        self.assertEqual(len(l_marg.nodes), 1)
        self.assertEqual(l_marg.n, np.array([6]))
        self.assertEqual(l_marg.p, np.array([0.3]))

        # ----- marginalize over non-scope rvs -----
        l_marg = marginalize(l, [2])

        self.assertTrue(l_marg.scopes_out == [Scope([1]), Scope([0])])
        self.assertTrue(np.all(l.n == l_marg.n))
        self.assertTrue(np.all(l.p == l_marg.p))

    def test_get_params(self):

        l = NegativeBinomialLayer(
            scope=Scope([1]), n=[2, 2], p=[0.73, 0.29], n_nodes=2
        )

        n, p, *others = l.get_params()

        self.assertTrue(len(others) == 0)
        self.assertTrue(np.allclose(n, np.array([2, 2])))
        self.assertTrue(np.allclose(p, np.array([0.73, 0.29])))


if __name__ == "__main__":
    unittest.main()
