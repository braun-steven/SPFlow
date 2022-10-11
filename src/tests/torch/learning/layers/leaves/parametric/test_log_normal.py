from spflow.meta.scope.scope import Scope
from spflow.torch.structure.layers.leaves.parametric.log_normal import LogNormalLayer
from spflow.torch.learning.layers.leaves.parametric.log_normal import maximum_likelihood_estimation

import torch
import numpy as np
import unittest
import random


class TestNode(unittest.TestCase):
    @classmethod
    def setup_class(cls):
        torch.set_default_dtype(torch.float64)

    @classmethod
    def teardown_class(cls):
        torch.set_default_dtype(torch.float32)

    def test_mle(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)
        
        layer = LogNormalLayer(scope=[Scope([0]), Scope([1])])

        # simulate data
        data = np.hstack([np.random.lognormal(mean=-1.7, sigma=0.2, size=(20000, 1)), np.random.lognormal(mean=0.5, sigma=1.3, size=(20000, 1))])

        # perform MLE
        maximum_likelihood_estimation(layer, torch.tensor(data), bias_correction=True)

        self.assertTrue(torch.allclose(layer.mean, torch.tensor([-1.7, 0.5]), atol=1e-2, rtol=1e-2))
        self.assertTrue(torch.allclose(layer.std, torch.tensor([0.2, 1.3]), atol=1e-2, rtol=1e-2))
    
    def test_mle_bias_correction(self):

        layer = LogNormalLayer(Scope([0]))
        data = torch.exp(torch.tensor([[-1.0], [1.0]]))

        # perform MLE
        maximum_likelihood_estimation(layer, data, bias_correction=False)
        self.assertTrue(torch.isclose(layer.std, torch.sqrt(torch.tensor(1.0))))

        # perform MLE
        maximum_likelihood_estimation(layer, data, bias_correction=True)
        self.assertTrue(torch.isclose(layer.std, torch.sqrt(torch.tensor(2.0))))
    
    def test_mle_edge_std_0(self):

        # set seed
        torch.manual_seed(0)
        np.random.seed(0)
        random.seed(0)
        
        layer = LogNormalLayer(Scope([0]))

        # simulate data
        data = torch.exp(torch.randn(1, 1))

        # perform MLE
        maximum_likelihood_estimation(layer, data, bias_correction=False)

        self.assertTrue(torch.allclose(layer.mean, torch.log(data[0])))
        self.assertTrue(layer.std > 0)
    
    def test_mle_edge_std_nan(self):

        # set seed
        np.random.seed(0)
        random.seed(0)
        
        layer = LogNormalLayer(Scope([0]))

        # simulate data
        data = torch.exp(torch.randn(1, 1))

        # perform MLE (Torch does not throw a warning different to NumPy)
        maximum_likelihood_estimation(layer, data, bias_correction=True)

        self.assertTrue(torch.isclose(layer.mean, torch.log(data[0])))
        self.assertFalse(torch.isnan(layer.std))
        self.assertTrue(torch.all(layer.std > 0))

    def test_mle_only_nans(self):
        
        layer = LogNormalLayer(Scope([0]))

        # simulate data
        data = torch.tensor([[float("nan"), float("nan")], [float("nan"), 2.0]])

        # check if exception is raised
        self.assertRaises(ValueError, maximum_likelihood_estimation, layer, data, nan_strategy='ignore')
    
    def test_mle_invalid_support(self):

        layer = LogNormalLayer(Scope([0]))

        # perform MLE (should raise exceptions)
        self.assertRaises(ValueError, maximum_likelihood_estimation, layer, torch.tensor([[float("inf")]]), bias_correction=True)

    def test_mle_nan_strategy_none(self):

        layer = LogNormalLayer(Scope([0]))
        self.assertRaises(ValueError, maximum_likelihood_estimation, layer, torch.tensor([[float("nan")], [0.1], [-1.8], [0.7]]), nan_strategy=None)

    def test_mle_nan_strategy_ignore(self):

        layer = LogNormalLayer(Scope([0]))
        maximum_likelihood_estimation(layer, torch.exp(torch.tensor([[float("nan")], [0.1], [-1.8], [0.7]])), nan_strategy='ignore', bias_correction=False)
        self.assertTrue(torch.allclose(layer.mean, torch.tensor(-1.0/3.0)))
        self.assertTrue(torch.allclose(layer.std, torch.sqrt(1/3*torch.sum((torch.tensor([[0.1], [-1.8], [0.7]])+1.0/3.0)**2))))

    def test_mle_nan_strategy_callable(self):

        layer = LogNormalLayer(Scope([0]))
        # should not raise an issue
        maximum_likelihood_estimation(layer, torch.tensor([[0.5], [1]]), nan_strategy=lambda x: x)

    def test_mle_nan_strategy_invalid(self):

        layer = LogNormalLayer(Scope([0]))
        self.assertRaises(ValueError, maximum_likelihood_estimation, layer, torch.tensor([[float("nan")], [0.1], [1.9], [0.7]]), nan_strategy='invalid_string')
        self.assertRaises(ValueError, maximum_likelihood_estimation, layer, torch.tensor([[float("nan")], [1], [0], [1]]), nan_strategy=1)


if __name__ == "__main__":
    unittest.main()