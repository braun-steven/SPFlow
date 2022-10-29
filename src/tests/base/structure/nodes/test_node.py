from spflow.base.structure.nodes.node import (
    SPNSumNode,
    SPNProductNode,
    Node,
    marginalize,
)
from spflow.meta.scope.scope import Scope
from .dummy_node import DummyNode
import numpy as np
import unittest
import random


class TestNode(unittest.TestCase):
    def test_sum_node_initialization(self):

        # empty children
        self.assertRaises(ValueError, SPNSumNode, [], [])
        # non-Module children
        self.assertRaises(
            ValueError, SPNSumNode, [DummyNode(Scope([0])), 0], [0.5, 0.5]
        )
        # children with different scopes
        self.assertRaises(
            ValueError,
            SPNSumNode,
            [DummyNode(Scope([0])), DummyNode(Scope([1]))],
            [0.5, 0.5],
        )
        # number of child outputs not matching number of weights
        self.assertRaises(
            ValueError,
            SPNSumNode,
            [DummyNode(Scope([0])), DummyNode(Scope([0]))],
            [1.0],
        )
        # non-positive weights
        self.assertRaises(
            ValueError, SPNSumNode, [DummyNode(Scope([0]))], [0.0]
        )
        # weights not summing up to one
        self.assertRaises(
            ValueError,
            SPNSumNode,
            [DummyNode(Scope([0])), DummyNode(Scope([0]))],
            [0.3, 0.5],
        )
        # weights of invalid shape
        self.assertRaises(
            ValueError, SPNSumNode, [DummyNode(Scope([0]))], [[1.0]]
        )

        # weights as list of floats
        SPNSumNode([DummyNode(Scope([0])), DummyNode(Scope([0]))], [0.5, 0.5])
        # weights as numpy array
        SPNSumNode(
            [DummyNode(Scope([0])), DummyNode(Scope([0]))], np.array([0.5, 0.5])
        )
        # no weights
        SPNSumNode([DummyNode(Scope([0])), DummyNode(Scope([0]))])

    def test_sum_node_marginalization_1(self):

        s = SPNSumNode([DummyNode(Scope([0])), DummyNode(Scope([0]))])

        s_marg = marginalize(s, [1])
        self.assertEqual(s_marg.scopes_out, s.scopes_out)

        s_marg = marginalize(s, [0])
        self.assertEqual(s_marg, None)

    def test_sum_node_marginalization_2(self):

        s = SPNSumNode(
            [
                SPNProductNode([DummyNode(Scope([0])), DummyNode(Scope([1]))]),
                SPNProductNode([DummyNode(Scope([0])), DummyNode(Scope([1]))]),
            ]
        )

        s_marg = marginalize(s, [0])
        self.assertEqual(s_marg.scopes_out, [Scope([1])])

        s_marg = marginalize(s, [1])
        self.assertEqual(s_marg.scopes_out, [Scope([0])])

        s_marg = marginalize(s, [0, 1])
        self.assertEqual(s_marg, None)

    def test_product_node_initialization(self):

        # empty children
        self.assertRaises(ValueError, SPNProductNode, [])
        # non-Module children
        self.assertRaises(
            ValueError, SPNProductNode, [DummyNode(Scope([0])), 0]
        )
        # children with non-disjoint scopes
        self.assertRaises(
            ValueError,
            SPNProductNode,
            [DummyNode(Scope([0])), DummyNode(Scope([0]))],
        )

        # correct initialization
        SPNProductNode([DummyNode(Scope([0])), DummyNode(Scope([1]))])

    def test_product_node_marginalization_1(self):

        p = SPNProductNode([DummyNode(Scope([0])), DummyNode(Scope([1]))])

        p_marg = marginalize(p, [2])
        self.assertEqual(p_marg.scopes_out, p.scopes_out)

        p_marg = marginalize(p, [1], prune=False)
        self.assertEqual(p_marg.scopes_out, [Scope([0])])

        p_marg = marginalize(p, [1], prune=True)
        # pruning should return single child directly
        self.assertTrue(isinstance(p_marg, DummyNode))

    def test_product_node_marginalization_2(self):

        p = SPNProductNode(
            [
                SPNProductNode([DummyNode(Scope([0])), DummyNode(Scope([1]))]),
                SPNProductNode([DummyNode(Scope([2])), DummyNode(Scope([3]))]),
            ]
        )

        p_marg = marginalize(p, [2])
        self.assertEqual(p_marg.scopes_out, [Scope([0, 1, 3])])


if __name__ == "__main__":
    unittest.main()
