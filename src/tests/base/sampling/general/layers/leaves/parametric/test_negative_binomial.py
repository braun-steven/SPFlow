import random
import unittest

import numpy as np

from spflow.base.inference import log_likelihood
from spflow.base.sampling import sample
from spflow.base.structure.spn import (
    NegativeBinomial,
    NegativeBinomialLayer,
    ProductNode,
    SumNode,
)
from spflow.meta.data import Scope


class TestNode(unittest.TestCase):
    def test_sampling_1(self):

        # set seed
        np.random.seed(0)
        random.seed(0)

        negative_binomial_layer = NegativeBinomialLayer(scope=Scope([0]), n=3, p=[0.8, 0.3], n_nodes=2)
        s1 = SumNode(children=[negative_binomial_layer], weights=[0.3, 0.7])

        negative_binomial_nodes = [
            NegativeBinomial(Scope([0]), n=3, p=0.8),
            NegativeBinomial(Scope([0]), n=3, p=0.3),
        ]
        s2 = SumNode(children=negative_binomial_nodes, weights=[0.3, 0.7])

        layer_samples = sample(s1, 10000)
        nodes_samples = sample(s2, 10000)
        self.assertTrue(
            np.allclose(
                layer_samples.mean(axis=0),
                nodes_samples.mean(axis=0),
                atol=0.01,
                rtol=0.1,
            )
        )

    def test_sampling_2(self):

        # set seed
        np.random.seed(0)
        random.seed(0)

        negative_binomial_layer = NegativeBinomialLayer(scope=[Scope([0]), Scope([1])], n=[3, 5], p=[0.8, 0.3])
        p1 = ProductNode(children=[negative_binomial_layer])

        negative_binomial_nodes = [
            NegativeBinomial(Scope([0]), n=3, p=0.8),
            NegativeBinomial(Scope([1]), n=5, p=0.3),
        ]
        p2 = ProductNode(children=negative_binomial_nodes)

        layer_samples = sample(p1, 10000)
        nodes_samples = sample(p2, 10000)
        self.assertTrue(
            np.allclose(
                layer_samples.mean(axis=0),
                nodes_samples.mean(axis=0),
                atol=0.01,
                rtol=0.1,
            )
        )

    def test_sampling_3(self):

        negative_binomial_layer = NegativeBinomialLayer(scope=Scope([0]), n=3, p=[0.8, 0.3], n_nodes=2)

        # check if empty output ids (i.e., []) works AND sampling from non-disjoint scopes fails
        self.assertRaises(ValueError, sample, negative_binomial_layer)


if __name__ == "__main__":
    unittest.main()
