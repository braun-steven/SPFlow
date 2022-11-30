import unittest

import numpy as np
import torch

from spflow.base.structure.spn import Gaussian as BaseGaussian
from spflow.base.structure.spn import HadamardLayer as BaseHadamardLayer
from spflow.meta.data import Scope
from spflow.torch.structure import marginalize, toBase, toTorch
from spflow.torch.structure.spn import Gaussian, HadamardLayer

from ...general.nodes.dummy_node import DummyNode


class TestNode(unittest.TestCase):
    def test_hadamard_layer_initialization(self):

        # dummy partitios over pair-wise disjont scopes
        input_partitions = [
            [DummyNode(Scope([0]))],
            [
                DummyNode(Scope([1, 3])),
                DummyNode(Scope([1, 3])),
                DummyNode(Scope([1, 3])),
            ],
            [DummyNode(Scope([2]))],
            [
                DummyNode(Scope([4])),
                DummyNode(Scope([4])),
                DummyNode(Scope([4])),
            ],
        ]

        # ----- check attributes after correct initialization -----

        l = HadamardLayer(child_partitions=input_partitions)
        # make sure number of creates nodes is correct
        self.assertEqual(l.n_out, 3)
        # make sure scopes are correct
        self.assertTrue(np.all(l.scopes_out == [Scope([0, 1, 2, 3, 4]) for _ in range(l.n_out)]))

        # only one partition
        l = HadamardLayer(
            child_partitions=[
                [
                    DummyNode(Scope([1, 3])),
                    DummyNode(Scope([1, 3])),
                    DummyNode(Scope([1, 3])),
                ]
            ]
        )
        # make sure number of creates nodes is correct
        self.assertEqual(l.n_out, 3)
        # make sure scopes are correct
        self.assertTrue(np.all(l.scopes_out == [Scope([1, 3]) for _ in range(l.n_out)]))

        # ----- no child partitions -----
        self.assertRaises(ValueError, HadamardLayer, [])

        # ----- empty partition -----
        self.assertRaises(ValueError, HadamardLayer, [[]])

        # ----- scopes inside partition differ -----
        self.assertRaises(
            ValueError,
            HadamardLayer,
            [
                [DummyNode(Scope([0]))],
                [DummyNode(Scope([1])), DummyNode(Scope([2]))],
            ],
        )

        # ----- partitions of non-pair-wise disjoint scopes -----
        self.assertRaises(
            ValueError,
            HadamardLayer,
            [
                [DummyNode(Scope([0]))],
                [DummyNode(Scope([0])), DummyNode(Scope([0]))],
            ],
        )

        # ----- invalid total outputs of partitions -----
        self.assertRaises(
            ValueError,
            HadamardLayer,
            [
                [DummyNode(Scope([0])), DummyNode(Scope([0]))],
                [
                    DummyNode(Scope([1])),
                    DummyNode(Scope([1])),
                    DummyNode(Scope([1])),
                ],
            ],
        )

    def test_hadamard_layer_structural_marginalization(self):

        # dummy partitios over pair-wise disjont scopes
        input_partitions = [
            [DummyNode(Scope([0]))],
            [
                DummyNode(Scope([1, 3])),
                DummyNode(Scope([1, 3])),
                DummyNode(Scope([1, 3])),
            ],
            [DummyNode(Scope([2]))],
            [
                DummyNode(Scope([4])),
                DummyNode(Scope([4])),
                DummyNode(Scope([4])),
            ],
        ]

        l = HadamardLayer(child_partitions=input_partitions)
        # should marginalize entire module
        l_marg = marginalize(l, [0, 1, 2, 3, 4])
        self.assertTrue(l_marg is None)
        # should marginalize entire partition
        l_marg = marginalize(l, [2])
        self.assertTrue(l_marg.scope == Scope([0, 1, 3, 4]))
        # should partially marginalize one partition
        l_marg = marginalize(l, [3])
        self.assertTrue(l_marg.scope == Scope([0, 1, 2, 4]))

        # ----- marginalize over non-scope rvs -----
        l_marg = marginalize(l, [5])
        self.assertTrue(
            l_marg.scopes_out
            == [
                Scope([0, 1, 2, 3, 4]),
                Scope([0, 1, 2, 3, 4]),
                Scope([0, 1, 2, 3, 4]),
            ]
        )

        # ----- pruning -----
        l = HadamardLayer(child_partitions=input_partitions[:2])

        l_marg = marginalize(l, [1, 3], prune=True)
        self.assertTrue(isinstance(l_marg, DummyNode))

    def test_hadamard_layer_backend_conversion_1(self):

        torch_hadamard_layer = HadamardLayer(
            child_partitions=[
                [Gaussian(Scope([0])), Gaussian(Scope([0]))],
                [Gaussian(Scope([1]))],
                [Gaussian(Scope([2])), Gaussian(Scope([2]))],
            ]
        )

        base_hadamard_layer = toBase(torch_hadamard_layer)
        self.assertEqual(base_hadamard_layer.n_out, torch_hadamard_layer.n_out)

    def test_hadamard_layer_backend_conversion_2(self):

        base_hadamard_layer = BaseHadamardLayer(
            child_partitions=[
                [BaseGaussian(Scope([0])), BaseGaussian(Scope([0]))],
                [BaseGaussian(Scope([1]))],
                [BaseGaussian(Scope([2])), BaseGaussian(Scope([2]))],
            ]
        )

        torch_hadamard_layer = toTorch(base_hadamard_layer)
        self.assertEqual(base_hadamard_layer.n_out, torch_hadamard_layer.n_out)


if __name__ == "__main__":
    unittest.main()
