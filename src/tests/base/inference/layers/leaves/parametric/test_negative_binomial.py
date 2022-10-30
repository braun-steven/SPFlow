from spflow.meta.data.scope import Scope
from spflow.meta.dispatch.dispatch_context import DispatchContext
from spflow.base.structure.layers.leaves.parametric.negative_binomial import (
    NegativeBinomialLayer,
)
from spflow.base.inference.layers.leaves.parametric.negative_binomial import (
    log_likelihood,
)
from spflow.base.structure.nodes.leaves.parametric.negative_binomial import (
    NegativeBinomial,
)
from spflow.base.inference.nodes.leaves.parametric.negative_binomial import (
    log_likelihood,
)
from spflow.base.structure.nodes.node import SPNProductNode, SPNSumNode
from spflow.base.inference.nodes.node import log_likelihood
from spflow.base.inference.module import log_likelihood
import numpy as np
import unittest


class TestNode(unittest.TestCase):
    def test_layer_likelihood_1(self):

        negative_binomial_layer = NegativeBinomialLayer(
            scope=Scope([0]), n=3, p=[0.8, 0.3], n_nodes=2
        )
        s1 = SPNSumNode(children=[negative_binomial_layer], weights=[0.3, 0.7])

        negative_binomial_nodes = [
            NegativeBinomial(Scope([0]), n=3, p=0.8),
            NegativeBinomial(Scope([0]), n=3, p=0.3),
        ]
        s2 = SPNSumNode(children=negative_binomial_nodes, weights=[0.3, 0.7])

        data = np.array([[0], [1], [0]])

        self.assertTrue(
            np.all(log_likelihood(s1, data) == log_likelihood(s2, data))
        )

    def test_layer_likelihood_2(self):

        negative_binomial_layer = NegativeBinomialLayer(
            scope=[Scope([0]), Scope([1])], n=[3, 5], p=[0.8, 0.3]
        )
        p1 = SPNProductNode(children=[negative_binomial_layer])

        negative_binomial_nodes = [
            NegativeBinomial(Scope([0]), n=3, p=0.8),
            NegativeBinomial(Scope([1]), n=5, p=0.3),
        ]
        p2 = SPNProductNode(children=negative_binomial_nodes)

        data = np.array([[0, 1], [1, 1], [0, 0]])

        self.assertTrue(
            np.all(log_likelihood(p1, data) == log_likelihood(p2, data))
        )


if __name__ == "__main__":
    unittest.main()
