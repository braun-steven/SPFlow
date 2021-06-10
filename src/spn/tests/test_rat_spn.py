import unittest
from spn.base.nodes.validity_checks import _isvalid_spn
from spn.base.rat.rat_spn import construct_spn
from spn.base.rat.region_graph import random_region_graph
from spn.base.nodes.node import _get_node_counts


class TestRatSpn(unittest.TestCase):
    def test_rat_spn_1(self):
        random_variables = set(range(1, 8))
        depth = 2
        replicas = 1
        region_graph = random_region_graph(random_variables, depth, replicas)

        num_nodes_root = 1
        num_nodes_region = 1
        num_nodes_leaf = 1
        rat_spn = construct_spn(
            region_graph, num_nodes_root, num_nodes_region, num_nodes_leaf
        )

        _isvalid_spn(rat_spn.root_nodes)
        sum_nodes, prod_nodes, leaf_nodes = _get_node_counts(rat_spn.root_nodes)
        self.assertEqual(sum_nodes, 3)
        self.assertEqual(prod_nodes, 3)
        self.assertEqual(leaf_nodes, 4)

    def test_rat_spn_2(self):
        random_variables = set(range(1, 8))
        depth = 3
        replicas = 1
        region_graph = random_region_graph(random_variables, depth, replicas)

        num_nodes_root = 1
        num_nodes_region = 1
        num_nodes_leaf = 1
        rat_spn = construct_spn(
            region_graph, num_nodes_root, num_nodes_region, num_nodes_leaf
        )

        _isvalid_spn(rat_spn)
        sum_nodes, prod_nodes, leaf_nodes = _get_node_counts(rat_spn.root_nodes)
        self.assertEqual(sum_nodes, 6)
        self.assertEqual(prod_nodes, 6)
        self.assertEqual(leaf_nodes, 7)

    def test_rat_spn_3(self):
        random_variables = set(range(1, 8))
        depth = 3
        replicas = 2
        region_graph = random_region_graph(random_variables, depth, replicas)

        num_nodes_root = 2
        num_nodes_region = 2
        num_nodes_leaf = 2
        rat_spn = construct_spn(
            region_graph, num_nodes_root, num_nodes_region, num_nodes_leaf
        )

        _isvalid_spn(rat_spn)
        sum_nodes, prod_nodes, leaf_nodes = _get_node_counts(rat_spn.root_nodes)
        self.assertEqual(sum_nodes, 22)
        self.assertEqual(prod_nodes, 48)
        self.assertEqual(leaf_nodes, 28)

    def test_rat_spn_4(self):
        random_variables = set(range(1, 8))
        depth = 3
        replicas = 3
        region_graph = random_region_graph(random_variables, depth, replicas)

        num_nodes_root = 3
        num_nodes_region = 3
        num_nodes_leaf = 3
        rat_spn = construct_spn(
            region_graph, num_nodes_root, num_nodes_region, num_nodes_leaf
        )

        _isvalid_spn(rat_spn)
        sum_nodes, prod_nodes, leaf_nodes = _get_node_counts(rat_spn.root_nodes)
        self.assertEqual(sum_nodes, 48)
        self.assertEqual(prod_nodes, 162)
        self.assertEqual(leaf_nodes, 63)


if __name__ == "__main__":
    unittest.main()