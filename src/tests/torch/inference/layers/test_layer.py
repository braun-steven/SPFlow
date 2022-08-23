from spflow.meta.scope.scope import Scope
from spflow.meta.contexts.dispatch_context import DispatchContext
from spflow.torch.structure.layers.layer import SPNSumLayer, SPNProductLayer, SPNPartitionLayer, SPNHadamardLayer
from spflow.torch.inference.layers.layer import log_likelihood
from spflow.torch.structure.nodes.node import SPNSumNode, SPNProductNode
from spflow.torch.inference.nodes.node import log_likelihood
from spflow.torch.structure.nodes.leaves.parametric.gaussian import Gaussian
from spflow.torch.inference.nodes.leaves.parametric.gaussian import log_likelihood
from spflow.torch.inference.module import log_likelihood
import torch
import unittest
import itertools


class TestNode(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        torch.set_default_dtype(torch.float64)

    @classmethod
    def teardown_class(cls):
        torch.set_default_dtype(torch.float32)

    def test_sum_layer_likelihood(self):

        input_nodes = [Gaussian(Scope([0])), Gaussian(Scope([0])), Gaussian(Scope([0]))]

        layer_spn = SPNSumNode(children=[
            SPNSumLayer(n_nodes=3,
                children=input_nodes,
                weights=[[0.8, 0.1, 0.1], [0.2, 0.3, 0.5], [0.2, 0.7, 0.1]]),
            ],
            weights = [0.3, 0.4, 0.3]
        )

        nodes_spn = SPNSumNode(children=[
                SPNSumNode(children=input_nodes, weights=[0.8, 0.1, 0.1]),
                SPNSumNode(children=input_nodes, weights=[0.2, 0.3, 0.5]),
                SPNSumNode(children=input_nodes, weights=[0.2, 0.7, 0.1]),
            ],
            weights = [0.3, 0.4, 0.3]
        )

        dummy_data = torch.tensor([[1.0], [0.0,], [0.25]])

        layer_ll = log_likelihood(layer_spn, dummy_data)
        nodes_ll = log_likelihood(nodes_spn, dummy_data)

        self.assertTrue(torch.allclose(layer_ll, nodes_ll))
    
    def test_product_layer_likelihood(self):

        input_nodes = [Gaussian(Scope([0])), Gaussian(Scope([1])), Gaussian(Scope([2]))]

        layer_spn = SPNSumNode(children=[
            SPNProductLayer(n_nodes=3, children=input_nodes)
            ],
            weights = [0.3, 0.4, 0.3]
        )

        nodes_spn = SPNSumNode(children=[
                SPNProductNode(children=input_nodes),
                SPNProductNode(children=input_nodes),
                SPNProductNode(children=input_nodes),
            ],
            weights = [0.3, 0.4, 0.3]
        )

        dummy_data = torch.tensor([[1.0, 0.25, 0.0], [0.0, 1.0, 0.25], [0.25, 0.0, 1.0]])

        layer_ll = log_likelihood(layer_spn, dummy_data)
        nodes_ll = log_likelihood(nodes_spn, dummy_data)

        self.assertTrue(torch.allclose(layer_ll, nodes_ll))

    def test_partition_layer_likelihood(self):

        input_partitions = [
            [Gaussian(Scope([0])), Gaussian(Scope([0]))],
            [Gaussian(Scope([1])), Gaussian(Scope([1])), Gaussian(Scope([1]))],
            [Gaussian(Scope([2]))]
        ]

        layer_spn = SPNSumNode(children=[
            SPNPartitionLayer(child_partitions=input_partitions)
            ],
            weights = [0.2, 0.1, 0.2, 0.2, 0.2, 0.1]
        )

        nodes_spn = SPNSumNode(children=[SPNProductNode(children=[input_partitions[0][i], input_partitions[1][j], input_partitions[2][k]]) for (i,j,k) in itertools.product([0,1], [0,1,2], [0])],
            weights = [0.2, 0.1, 0.2, 0.2, 0.2, 0.1]
        )

        dummy_data = torch.tensor([[1.0, 0.25, 0.0], [0.0, 1.0, 0.25], [0.25, 0.0, 1.0]])

        layer_ll = log_likelihood(layer_spn, dummy_data)
        nodes_ll = log_likelihood(nodes_spn, dummy_data)

        self.assertTrue(torch.allclose(layer_ll, nodes_ll))
    
    def test_hadamard_layer_likelihood(self):

        input_partitions = [
            [Gaussian(Scope([0]))],
            [Gaussian(Scope([1])), Gaussian(Scope([1])), Gaussian(Scope([1]))],
            [Gaussian(Scope([2]))],
            [Gaussian(Scope([3])), Gaussian(Scope([3])), Gaussian(Scope([3]))],
        ]

        layer_spn = SPNSumNode(children=[
            SPNHadamardLayer(child_partitions=input_partitions)
            ],
            weights = [0.3, 0.2, 0.5]
        )

        nodes_spn = SPNSumNode(children=[SPNProductNode(children=[input_partitions[0][i], input_partitions[1][j], input_partitions[2][k], input_partitions[3][l]]) for (i,j,k,l) in [[0,0,0,0], [0,1,0,1], [0,2,0,2]]],
            weights = [0.3, 0.2, 0.5]
        )

        dummy_data = torch.tensor([[1.0, 0.25, 0.0, -0.7], [0.0, 1.0, 0.25, 0.12], [0.25, 0.0, 1.0, 0.0]])

        layer_ll = log_likelihood(layer_spn, dummy_data)
        nodes_ll = log_likelihood(nodes_spn, dummy_data)

        self.assertTrue(torch.allclose(layer_ll, nodes_ll))


if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    unittest.main()