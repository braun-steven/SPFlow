from spflow.torch.structure.layers.leaves.parametric.cond_multivariate_gaussian import (
    CondMultivariateGaussianLayer,
    marginalize,
    toTorch,
    toBase,
)
from spflow.torch.structure.nodes.leaves.parametric.cond_multivariate_gaussian import (
    CondMultivariateGaussian,
)
from spflow.torch.structure.nodes.leaves.parametric.cond_gaussian import (
    CondGaussian,
)
from spflow.base.structure.layers.leaves.parametric.cond_multivariate_gaussian import (
    CondMultivariateGaussianLayer as BaseCondMultivariateGaussianLayer,
)
from spflow.meta.contexts.dispatch_context import DispatchContext
from spflow.meta.scope.scope import Scope
import torch
import numpy as np
import unittest


class TestNode(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        torch.set_default_dtype(torch.float64)

    @classmethod
    def teardown_class(cls):
        torch.set_default_dtype(torch.float32)

    def test_layer_initialization(self):

        # ----- check attributes after correct initialization -----

        l = CondMultivariateGaussianLayer(scope=Scope([1, 0]), n_nodes=3)
        # make sure number of creates nodes is correct
        self.assertEqual(len(l.scopes_out), 3)
        # make sure scopes are correct
        self.assertTrue(
            np.all(
                l.scopes_out == [Scope([1, 0]), Scope([1, 0]), Scope([1, 0])]
            )
        )

        # ---- different scopes -----
        l = CondMultivariateGaussianLayer(
            scope=[Scope([0, 1, 2]), Scope([1, 3]), Scope([2])], n_nodes=3
        )
        for node, node_scope in zip(l.nodes, l.scopes_out):
            self.assertEqual(node.scope, node_scope)

        # ----- invalid number of nodes -----
        self.assertRaises(
            ValueError,
            CondMultivariateGaussianLayer,
            Scope([0, 1, 2]),
            n_nodes=0,
        )

        # ----- invalid scope -----
        self.assertRaises(
            ValueError, CondMultivariateGaussianLayer, Scope([]), n_nodes=3
        )
        self.assertRaises(
            ValueError, CondMultivariateGaussianLayer, [], n_nodes=3
        )

        # ----- individual scopes and parameters -----
        scopes = [Scope([1, 2, 3]), Scope([0, 1, 4]), Scope([0, 2, 3])]
        l = CondMultivariateGaussianLayer(scope=scopes, n_nodes=3)
        for node, node_scope in zip(l.nodes, scopes):
            self.assertEqual(node.scope, node_scope)

        # -----number of cond_f functions -----
        CondMultivariateGaussianLayer(
            Scope([0]),
            n_nodes=2,
            cond_f=[
                lambda data: {"mean": [0.0], "cov": [[1.0]]},
                lambda data: {"mean": [0.0], "cov": [[1.0]]},
            ],
        )
        self.assertRaises(
            ValueError,
            CondMultivariateGaussianLayer,
            Scope([0]),
            n_nodes=2,
            cond_f=[lambda data: {"mean": [0.0], "cov": [[1.0]]}],
        )

    def test_retrieve_params(self):

        # ----- single mean/cov list parameter values -----
        mean_value = [0.0, -1.0, 2.3]
        cov_value = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        l = CondMultivariateGaussianLayer(
            scope=Scope([1, 0, 2]),
            n_nodes=3,
            cond_f=lambda data: {"mean": mean_value, "cov": cov_value},
        )

        for mean_node, cov_node in zip(
            *l.retrieve_params(torch.tensor([[1]]), DispatchContext())
        ):
            self.assertTrue(torch.all(mean_node == torch.tensor(mean_value)))
            self.assertTrue(torch.all(cov_node == torch.tensor(cov_value)))

        # ----- multiple mean/cov list parameter values -----
        mean_values = [[0.0, -1.0, 2.3], [1.0, 5.0, -3.0], [-7.1, 3.2, -0.9]]
        cov_values = [
            [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
            [[0.5, 0.0, 0.0], [0.0, 1.3, 0.0], [0.0, 0.0, 0.7]],
            [[3.1, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 0.3]],
        ]
        l.set_cond_f(lambda data: {"mean": mean_values, "cov": cov_values})

        for mean_actual, cov_actual, mean_node, cov_node in zip(
            mean_values,
            cov_values,
            *l.retrieve_params(torch.tensor([[1]]), DispatchContext())
        ):
            self.assertTrue(torch.all(mean_node == torch.tensor(mean_actual)))
            self.assertTrue(torch.allclose(cov_node, torch.tensor(cov_actual)))

        # wrong number of values
        l.set_cond_f(lambda data: {"mean": mean_values[:-1], "cov": cov_values})
        self.assertRaises(
            ValueError,
            l.retrieve_params,
            torch.tensor([[1]]),
            DispatchContext(),
        )

        l.set_cond_f(lambda data: {"mean": mean_values, "cov": cov_values[:-1]})
        self.assertRaises(
            ValueError,
            l.retrieve_params,
            torch.tensor([[1]]),
            DispatchContext(),
        )

        # wrong number of dimensions (nested list)
        l.set_cond_f(
            lambda data: {
                "mean": [mean_values for _ in range(3)],
                "cov": cov_values,
            }
        )
        self.assertRaises(
            ValueError,
            l.retrieve_params,
            torch.tensor([[1]]),
            DispatchContext(),
        )

        l.set_cond_f(
            lambda data: {
                "mean": mean_values,
                "cov": [cov_values for _ in range(3)],
            }
        )
        self.assertRaises(
            ValueError,
            l.retrieve_params,
            torch.tensor([[1]]),
            DispatchContext(),
        )

        # ----- numpy parameter values -----
        l.set_cond_f(
            lambda data: {
                "mean": np.array(mean_values),
                "cov": np.array(cov_values),
            }
        )
        for mean_actual, cov_actual, mean_node, cov_node in zip(
            mean_values,
            cov_values,
            *l.retrieve_params(torch.tensor([[1.0]]), DispatchContext())
        ):
            self.assertTrue(torch.all(mean_node == torch.tensor(mean_actual)))
            self.assertTrue(torch.allclose(cov_node, torch.tensor(cov_actual)))

        # wrong number of values
        l.set_cond_f(
            lambda data: {
                "mean": np.array(mean_values[:-1]),
                "cov": np.array(cov_values),
            }
        )
        self.assertRaises(
            ValueError,
            l.retrieve_params,
            torch.tensor([[1]]),
            DispatchContext(),
        )

        l.set_cond_f(
            lambda data: {
                "mean": np.array(mean_values),
                "cov": np.array(cov_values[:-1]),
            }
        )
        self.assertRaises(
            ValueError,
            l.retrieve_params,
            torch.tensor([[1]]),
            DispatchContext(),
        )

        # wrong number of dimensions (nested list)
        l.set_cond_f(
            lambda data: {
                "mean": np.array([mean_values for _ in range(3)]),
                "cov": np.array(cov_value),
            }
        )
        self.assertRaises(
            ValueError,
            l.retrieve_params,
            torch.tensor([[1]]),
            DispatchContext(),
        )

        l.set_cond_f(
            lambda data: {
                "mean": np.array(mean_values),
                "cov": np.array([cov_values for _ in range(3)]),
            }
        )
        self.assertRaises(
            ValueError,
            l.retrieve_params,
            torch.tensor([[1]]),
            DispatchContext(),
        )

    def test_layer_structural_marginalization(self):

        # ---------- same scopes -----------

        l = CondMultivariateGaussianLayer(scope=[Scope([0, 1]), Scope([0, 1])])
        # ----- marginalize over entire scope -----
        self.assertTrue(marginalize(l, [0, 1]) == None)

        # ----- marginalize over non-scope rvs -----
        l_marg = marginalize(l, [2])

        self.assertTrue(l_marg.scopes_out == [Scope([0, 1]), Scope([0, 1])])

        # ---------- different scopes -----------

        l = CondMultivariateGaussianLayer(scope=[Scope([0, 2]), Scope([1, 3])])

        # ----- marginalize over entire scope -----
        self.assertTrue(marginalize(l, [0, 1, 2, 3]) == None)

        # ----- partially marginalize -----
        l_marg = marginalize(l, [0, 2], prune=True)
        self.assertTrue(isinstance(l_marg, CondMultivariateGaussian))
        self.assertEqual(l_marg.scope, Scope([1, 3]))

        l_marg = marginalize(l, [0, 1, 2], prune=True)
        self.assertTrue(isinstance(l_marg, CondGaussian))
        self.assertEqual(l_marg.scope, Scope([3]))

        l_marg = marginalize(l, [0, 2], prune=False)
        self.assertTrue(isinstance(l_marg, CondMultivariateGaussianLayer))
        self.assertEqual(l_marg.scopes_out, [Scope([1, 3])])
        self.assertEqual(len(l_marg.nodes), 1)

        # ----- marginalize over non-scope rvs -----
        l_marg = marginalize(l, [4])

        self.assertTrue(l_marg.scopes_out == [Scope([0, 2]), Scope([1, 3])])

    def test_layer_dist(self):

        mean_values = torch.tensor(
            [[0.0, -1.0, 2.3], [1.0, 5.0, -3.0], [-7.1, 3.2, -0.9]]
        )
        cov_values = torch.tensor(
            [
                [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                [[0.5, 0.0, 0.0], [0.0, 1.3, 0.0], [0.0, 0.0, 0.7]],
                [[3.1, 0.0, 0.0], [0.0, 5.0, 0.0], [0.0, 0.0, 0.3]],
            ]
        )
        l = CondMultivariateGaussianLayer(scope=Scope([0, 1, 2]), n_nodes=3)

        # ----- full dist -----
        dist_list = l.dist(mean_values, cov_values)

        for mean_value, cov_value, dist in zip(
            mean_values, cov_values, dist_list
        ):
            self.assertTrue(torch.allclose(mean_value, dist.mean))
            self.assertTrue(torch.allclose(cov_value, dist.covariance_matrix))

        # ----- partial dist -----
        dist_list = l.dist(mean_values, cov_values, [1, 2])

        for mean_value, cov_value, dist in zip(
            mean_values[1:], cov_values[1:], dist_list
        ):
            self.assertTrue(torch.allclose(mean_value, dist.mean))
            self.assertTrue(torch.allclose(cov_value, dist.covariance_matrix))

        dist_list = l.dist(mean_values, cov_values, [1, 0])

        for mean_value, cov_value, dist in zip(
            reversed(mean_values[:-1]), reversed(cov_values[:-1]), dist_list
        ):
            self.assertTrue(torch.allclose(mean_value, dist.mean))
            self.assertTrue(torch.allclose(cov_value, dist.covariance_matrix))

    def test_layer_backend_conversion_1(self):

        torch_layer = CondMultivariateGaussianLayer(
            scope=[Scope([0, 1, 2]), Scope([1, 2, 3]), Scope([0, 1, 2])]
        )
        base_layer = toBase(torch_layer)

        self.assertTrue(np.all(base_layer.scopes_out == torch_layer.scopes_out))
        self.assertEqual(base_layer.n_out, torch_layer.n_out)

    def test_layer_backend_conversion_2(self):

        base_layer = BaseCondMultivariateGaussianLayer(
            scope=[Scope([0, 1, 2]), Scope([1, 2, 3]), Scope([0, 1, 2])]
        )
        torch_layer = toTorch(base_layer)

        self.assertTrue(np.all(base_layer.scopes_out == torch_layer.scopes_out))
        self.assertEqual(base_layer.n_out, torch_layer.n_out)


if __name__ == "__main__":
    torch.set_default_dtype(torch.float64)
    unittest.main()
