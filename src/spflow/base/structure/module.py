"""
Created on June 10, 2021

@authors: Philipp Deibert

This file provides the abstract Module class for building graph structures.
"""
from abc import ABC, abstractmethod
import spflow
from spflow.base.structure.nodes.node import INode, _get_node_counts
from spflow.base.structure.network_type import NetworkType
from typing import List, Tuple, Optional, cast
from multipledispatch import dispatch  # type: ignore


class Module(ABC):
    """Abstract module class for building graph structures.

    Attributes:
        children:
            List of child modules to form a graph of modules.
        nodes:
            List of INodes representing all Inodes encapsulated by this module.
        network_type:
            Network Type defining methods to use on this module.
        output_nodes:
            List of INodes representing the root nodes of the module to connect it to other modules.
        scope:
            List of ints representing the scope of all nodes in this module.
    """

    def __init__(
        self,
        children: List["Module"],
        scope: List[int],
        network_type: Optional[NetworkType] = None,
    ) -> None:
        self.nodes: List[INode] = []

        # Set network type - if none is specified, get default global network type
        if network_type is None:
            self.network_type = spflow.get_network_type()
        else:
            self.network_type = network_type
            self.network_type = cast(NetworkType, self.network_type)
        self.output_nodes: List[INode] = []
        self.children: List["Module"] = children
        self.scope: List[int] = scope

    @abstractmethod
    def __len__(self):
        pass


# multiple output nodes?
@dispatch(Module)  # type: ignore[no-redef]
def _get_node_counts(module: Module) -> Tuple[int, int, int]:
    """Wrapper for Modules"""
    return _get_node_counts(module.output_nodes)
