# -*- coding: utf-8 -*-
"""Contains sampling methods for RAT-SPNs for SPFlow in the ``torch`` backend.
"""
from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.contexts.dispatch_context import DispatchContext, init_default_dispatch_context
from spflow.meta.contexts.sampling_context import SamplingContext, init_default_sampling_context
from spflow.torch.structure.rat.rat_spn import RatSPN

import torch
from typing import Optional


@dispatch  # type: ignore
def sample(rat_spn: RatSPN, data: torch.Tensor, dispatch_ctx: Optional[DispatchContext]=None, sampling_ctx: Optional[SamplingContext]=None) -> torch.Tensor:
    r"""Samples from RAT-SPNs in the ``torch`` backend given potential evidence.

    Missing values (i.e., NaN) are filled with sampled values.

    Args:
        rat_spn:
            ``RatSpn`` instance to sample from.
        data:
            Two-dimensional PyTorch tensor containing potential evidence.
            Each row corresponds to a sample.
        dispatch_ctx:
            Optional dispatch context.
        sampling_ctx:
            Optional sampling context containing the instances (i.e., rows) of ``data`` to fill with sampled values and the output indices of the node to sample from.

    Returns:
        Two-dimensional PyTorch tensor containing the sampled values together with the specified evidence.
        Each row corresponds to a sample.
    """  
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)
    sampling_ctx = init_default_sampling_context(sampling_ctx, data.shape[0])

    return sample(rat_spn.root_node, data, dispatch_ctx=dispatch_ctx, sampling_ctx=sampling_ctx)