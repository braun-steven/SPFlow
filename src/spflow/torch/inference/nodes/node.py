# -*- coding: utf-8 -*-
"""Contains inference methods for SPN-like nodes for SPFlow in the ``torch`` backend.
"""
import torch
from typing import Optional
from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.contexts.dispatch_context import DispatchContext, init_default_dispatch_context
from spflow.torch.structure.nodes.node import SPNProductNode, SPNSumNode


@dispatch(memoize=True)  # type: ignore
def log_likelihood(node: SPNProductNode, data: torch.Tensor, dispatch_ctx: Optional[DispatchContext]=None) -> torch.Tensor:
    """Computes log-likelihoods for SPN-like sum nodes in the ``torch`` backend given input data.

    Log-likelihood for sum node is the logarithm of the sum of weighted exponentials (LogSumExp) of its input likelihoods (weighted sum in linear space).
    Missing values (i.e., NaN) are marginalized over.

    Args:
        sum_node:
            Sum node to perform inference for.
        data:
            Two-dimensional PyTorch tensor containing the input data.
            Each row corresponds to a sample.
        dispatch_ctx:
            Optional dispatch context.

    Returns:
        Two-dimensional PyTorch tensor containing the log-likelihoods of the input data for the sum node.
        Each row corresponds to an input sample.
    """
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)
    inputs = torch.hstack([log_likelihood(child, data, dispatch_ctx=dispatch_ctx) for child in node.children()])

    # return product (sum in log space)
    return torch.sum(inputs, dim=-1, keepdims=True)


@dispatch(memoize=True)  # type: ignore
def log_likelihood(node: SPNSumNode, data: torch.Tensor, dispatch_ctx: Optional[DispatchContext]=None) -> torch.Tensor:
    """Computes log-likelihoods for SPN-like product nodes in the ``torch`` backend given input data.

    Log-likelihood for product node is the sum of its input likelihoods (product in linear space).
    Missing values (i.e., NaN) are marginalized over.

    Args:
        product_node:
            Product node to perform inference for.
        data:
            Two-dimensional PyTorch tensor containing the input data.
            Each row corresponds to a sample.
        dispatch_ctx:
            Optional dispatch context.

    Returns:
        Two-dimensional PyTorch tensor containing the log-likelihoods of the input data for the sum node.
        Each row corresponds to an input sample.
    """
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)
    inputs = torch.hstack([log_likelihood(child, data, dispatch_ctx=dispatch_ctx) for child in node.children()])

    # weight inputs in log-space
    weighted_inputs = inputs + node.weights.log()

    return torch.logsumexp(weighted_inputs, dim=-1, keepdims=True)