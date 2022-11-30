from spflow.meta.data import Scope
from spflow.meta.dispatch import SamplingContext
from spflow.base.structure.spn import MultivariateGaussian
from spflow.base.sampling import sample

import numpy as np
import unittest
import random


class TestMultivariateGaussian(unittest.TestCase):
    def test_joint_sampling(self):

        # set seed
        np.random.seed(0)
        random.seed(0)

        rng = np.random.default_rng(123)

        # generate mean vector
        mean = rng.standard_normal((1, 5)) * 0.1
        # generate p.s.d covariance matrix
        cov = rng.standard_normal((5, 5)) * 0.1
        cov = cov @ cov.T

        # create distribution
        mv = MultivariateGaussian(Scope([0, 1, 2, 3, 4]), mean=mean, cov=cov)

        # conditionally sample
        data = sample(mv, 100000)

        # estimate mean and covariance matrix for conditioned distribution from data
        mean_est = data.mean(axis=0)
        cov_est = np.cov(data.T)

        self.assertTrue(np.allclose(mean, mean_est, atol=0.01, rtol=0.1))
        self.assertTrue(np.allclose(cov, cov_est, atol=0.01, rtol=0.1))

    def test_conditional_sampling(self):

        # set seed
        np.random.seed(0)
        random.seed(0)

        rng = np.random.default_rng(123)

        # generate mean vector
        mean = rng.standard_normal((1, 5)) * 0.1
        # generate p.s.d covariance matrix
        cov = rng.standard_normal((5, 5)) * 0.1
        cov = cov @ cov.T

        # define which scope variabes are conditioned on
        cond_mask = np.array([True, False, True, True, False])

        # generate 10 different conditional values and repeat each 100 times
        cond_data = np.random.multivariate_normal(
            mean[:, cond_mask].squeeze(0),
            cov[cond_mask, :][:, cond_mask],
            size=10,
        )
        cond_data = np.repeat(cond_data, 10000, axis=0)

        # generate patially filled data array
        data = np.full((100000, 5), np.nan)
        data[:, cond_mask] = cond_data

        # create distribution
        mv = MultivariateGaussian(Scope([0, 1, 2, 3, 4]), mean=mean, cov=cov)

        # conditionally sample
        data = sample(mv, data)

        # for each conditional value
        for i in range(10):

            # estimate mean and covariance matrix for conditioned distribution from data
            mean_est = data[i * 10000 : (i + 1) * 10000, ~cond_mask].mean(
                axis=0
            )
            cov_est = np.cov(data[i * 10000 : (i + 1) * 10000, ~cond_mask].T)

            # compute analytical mean and covariance matrix for conditioned distribution
            marg_cov_inv = np.linalg.inv(cov[np.ix_(cond_mask, cond_mask)])
            cond_cov = cov[np.ix_(cond_mask, ~cond_mask)]

            mean_exact = mean[0, ~cond_mask] + (
                (data[i * 10000, cond_mask] - mean[:, cond_mask])
                @ (marg_cov_inv @ cond_cov)
            )
            cov_exact = cov[np.ix_(~cond_mask, ~cond_mask)] - (
                cond_cov.T @ marg_cov_inv @ cond_cov
            )

            self.assertTrue(
                np.allclose(mean_exact, mean_est, atol=0.01, rtol=0.1)
            )
            self.assertTrue(
                np.allclose(cov_exact, cov_est, atol=0.01, rtol=0.1)
            )

    def test_sampling(self):

        mv = MultivariateGaussian(Scope([0, 1]))

        # make sure that instance ids out of bounds raise errors
        self.assertRaises(
            ValueError,
            sample,
            mv,
            np.array([[0, 0]]),
            sampling_ctx=SamplingContext([1]),
        )

    def test_sampling_2(self):

        # set seed
        np.random.seed(0)
        random.seed(0)

        mv = MultivariateGaussian(Scope([0, 1]))
        data = np.array([[0.0, 0.0]])

        # make sure that data without any 'NaN' values is simply skipped
        data_ = sample(mv, data, sampling_ctx=SamplingContext([0]))

        self.assertTrue(np.allclose(data, data_))


if __name__ == "__main__":
    unittest.main()
