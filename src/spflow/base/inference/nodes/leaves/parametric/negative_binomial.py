from spflow.base.structure.nodes.leaves.parametric import (
    NegativeBinomial,
    get_scipy_object,
    get_scipy_object_parameters,
)
from .parametric import MIN_NEG
from multipledispatch import dispatch  # type: ignore

import numpy as np
from typing import Optional


@dispatch(NegativeBinomial, data=np.ndarray)  # type: ignore[no-redef]
def node_likelihood(node: NegativeBinomial, data: np.ndarray = None) -> np.ndarray:
    probs = np.ones((data.shape[0], 1))
    data = data[:, node.scope]
    marg_ids = np.isnan(data)
    probs[~marg_ids] = get_scipy_object(node).pmf(
        k=data[~marg_ids], **get_scipy_object_parameters(node)
    )
    probs[probs == 1.0] = 0.999999999
    probs[np.isinf(probs)] = 0.000000001
    return probs


@dispatch(NegativeBinomial, data=np.ndarray)  # type: ignore[no-redef]
def node_log_likelihood(node: NegativeBinomial, data: np.ndarray = None) -> np.ndarray:
    probs = np.zeros((data.shape[0], 1))
    data = data[:, node.scope]
    marg_ids = np.isnan(data)
    probs[~marg_ids] = get_scipy_object(node).logpmf(
        k=data[~marg_ids], **get_scipy_object_parameters(node)
    )
    probs[np.isinf(probs)] = MIN_NEG
    return probs
