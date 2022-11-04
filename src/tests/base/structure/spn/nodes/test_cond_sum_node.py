from spflow.base.structure.spn import ProductNode, CondSumNode, marginalize
from spflow.meta.dispatch import DispatchContext
from spflow.meta.data import Scope
from ...general.nodes.dummy_node import DummyNode
from typing import Callable

import numpy as np
import unittest


class TestSumNode(unittest.TestCase):
    def test_initialization(self):

        sum_node = CondSumNode([DummyNode(Scope([0])), DummyNode(Scope([0]))])
        self.assertTrue(sum_node.cond_f is None)
        sum_node = CondSumNode(
            [DummyNode(Scope([0])), DummyNode(Scope([0]))],
            lambda x: {"weights": [0.5, 0.5]},
        )
        self.assertTrue(isinstance(sum_node.cond_f, Callable))

        # empty children
        self.assertRaises(ValueError, CondSumNode, [], [])
        # non-Module children
        self.assertRaises(ValueError, CondSumNode, [DummyNode(Scope([0])), 0])
        # children with different scopes
        self.assertRaises(
            ValueError,
            CondSumNode,
            [DummyNode(Scope([0])), DummyNode(Scope([1]))],
        )

    def test_retrieve_params(self):

        sum_node = CondSumNode([DummyNode(Scope([0])), DummyNode(Scope([0]))])

        # number of child outputs not matching number of weights
        sum_node.set_cond_f(lambda data: {"weights": [1.0]})
        self.assertRaises(
            ValueError,
            sum_node.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )
        # non-positive weights
        sum_node.set_cond_f(lambda data: {"weights": [0.0, 1.0]})
        self.assertRaises(
            ValueError,
            sum_node.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )
        # weights not summing up to one
        sum_node.set_cond_f(lambda data: {"weights": [0.5, 0.3]})
        self.assertRaises(
            ValueError,
            sum_node.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )
        # weights of invalid shape
        sum_node.set_cond_f(lambda data: {"weights": [[0.5, 0.5]]})
        self.assertRaises(
            ValueError,
            sum_node.retrieve_params,
            np.array([[1.0]]),
            DispatchContext(),
        )

        # weights as list of floats
        sum_node.set_cond_f(lambda data: {"weights": [0.5, 0.5]})
        self.assertTrue(
            np.all(
                sum_node.retrieve_params(np.array([[1.0]]), DispatchContext())
                == np.array([0.5, 0.5])
            )
        )
        # weights as numpy array
        sum_node.set_cond_f(lambda data: {"weights": np.array([0.5, 0.5])})
        self.assertTrue(
            np.all(
                sum_node.retrieve_params(np.array([[1.0]]), DispatchContext())
                == np.array([0.5, 0.5])
            )
        )

    def test_marginalization_1(self):

        s = CondSumNode([DummyNode(Scope([0])), DummyNode(Scope([0]))])

        s_marg = marginalize(s, [1])
        self.assertEqual(s_marg.scopes_out, s.scopes_out)

        s_marg = marginalize(s, [0])
        self.assertEqual(s_marg, None)

    def test_marginalization_2(self):

        s = CondSumNode(
            [
                ProductNode([DummyNode(Scope([0])), DummyNode(Scope([1]))]),
                ProductNode([DummyNode(Scope([0])), DummyNode(Scope([1]))]),
            ]
        )

        s_marg = marginalize(s, [0])
        self.assertEqual(s_marg.scopes_out, [Scope([1])])

        s_marg = marginalize(s, [1])
        self.assertEqual(s_marg.scopes_out, [Scope([0])])

        s_marg = marginalize(s, [0, 1])
        self.assertEqual(s_marg, None)


if __name__ == "__main__":
    unittest.main()
