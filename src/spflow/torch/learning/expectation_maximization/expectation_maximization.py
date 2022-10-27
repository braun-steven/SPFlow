# -*- coding: utf-8 -*-
"""Contains the expectation maximization optimization parameter learner for SPFlow in the ``torch`` backend.
"""
from typing import List
from spflow.meta.contexts.dispatch_context import DispatchContext
from spflow.torch.structure.module import Module
from spflow.torch.inference.module import log_likelihood
from spflow.torch.learning.nodes.leaves.parametric.bernoulli import em # TODO

import torch


def expectation_maximization(module: Module, data: torch.Tensor, max_steps: int=-1) -> torch.Tensor:
    """Performs partitioning usig randomized dependence coefficients (RDCs) to be used with the LearnSPN algorithm in the ``torch`` backend.

    Args:
        module:
            Module to perform EM optimization on.
        data:
            Two-dimensional PyTorch tensor containing the input data.
            Each row corresponds to a sample.
        max_steps:
            Integer representing the maximum number of iterations.
            Defaults to -1, in which case the optimization is performed until convergence. 

    Returns:
        One-dimensional PyTorch tensors, containing the average log-likelihood for each iteration step. 
    """
    prev_avg_ll = torch.tensor(-float("inf"))
    ll_history = []

    while True:

        # initialize new dispatch context
        dispatch_ctx = DispatchContext()

        # compute log likelihoods and sum them together
        acc_ll = log_likelihood(module, data, dispatch_ctx=dispatch_ctx).sum()

        avg_ll = acc_ll.detach().clone() / data.shape[0]
        ll_history.append(avg_ll)

        # end update loop if max steps reached or loss converged
        if n_steps == max_steps or avg_ll <= prev_avg_ll:
            break

        # retain gradients for all module log-likelihoods
        for ll in dispatch_ctx.cache['log_likelihood'].values():
            if ll.requires_grad:
                ll.retain_grad()

        # compute gradients (if there are differentiable parameters to begin with)
        if acc_ll.requires_grad:
            acc_ll.backward()

        # recursively perform expectation maximization
        em(module, data, dispatch_ctx=dispatch_ctx)

        prev_avg_ll = avg_ll
        # TODO: zero/None all gradients

        # increment steps counter
        n_steps += 1

    return torch.concat(ll_history)