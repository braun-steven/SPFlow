import random
import unittest

import numpy as np

from spflow.base.learning import maximum_likelihood_estimation
from spflow.base.structure.spn import UniformLayer
from spflow.meta.data import Scope


class TestNode(unittest.TestCase):
    def test_mle(self):

        # set seed
        np.random.seed(0)
        random.seed(0)

        layer = UniformLayer(scope=[Scope([0]), Scope([1])], start=[-3.0, 0.0], end=[-1.0, 1.0])

        # simulate data
        data = np.hstack(
            [
                np.random.uniform(low=-3.0, high=-1.0, size=(100, 1)),
                np.random.uniform(low=0.0, high=1.0, size=(100, 1)),
            ]
        )

        # perform MLE
        maximum_likelihood_estimation(layer, data)

        self.assertTrue(np.all(layer.start == np.array([-3.0, 0.0])))
        self.assertTrue(np.all(layer.end == np.array([-1.0, 1.0])))


if __name__ == "__main__":
    unittest.main()
