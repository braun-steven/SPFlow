"""Contains the SPFlow architecture for Random and Tensorized Sum-Product Networks (RAT-SPNs) in the ``torch`` backend.
"""
from typing import Iterable, List, Optional, Union

from spflow.base.structure.spn.rat.rat_spn import RatSPN as BaseRatSPN
from spflow.base.structure.spn.rat.region_graph import Partition, Region, RegionGraph
from spflow.meta.data.feature_context import FeatureContext
from spflow.meta.data.scope import Scope
from spflow.meta.dispatch.dispatch import dispatch
from spflow.meta.dispatch.dispatch_context import (
    DispatchContext,
    init_default_dispatch_context,
)
from spflow.torch.structure.autoleaf import AutoLeaf
from spflow.torch.structure.module import Module
from spflow.torch.structure.spn.layers.cond_sum_layer import CondSumLayer, marginalize
from spflow.torch.structure.spn.layers.hadamard_layer import HadamardLayer, marginalize
from spflow.torch.structure.spn.layers.partition_layer import (
    PartitionLayer,
    marginalize,
)
from spflow.torch.structure.spn.layers.sum_layer import SumLayer, marginalize
from spflow.torch.structure.spn.nodes.cond_sum_node import CondSumNode, marginalize
from spflow.torch.structure.spn.nodes.sum_node import SumNode, marginalize


class RatSPN(Module):
    r"""Module architecture for Random and Tensorized Sum-Product Networks (RAT-SPNs) in the ``torch`` backend.

    Constructs a RAT-SPN from a specified ``RegionGraph`` instance.
    For details see (Peharz et al., 2020): "Random Sum-Product Networks: A Simple and Effective Approach to Probabilistic Deep Learning".

    Attributes:
        n_root_nodes:
            Integer specifying the number of sum nodes in the root region (C in the original paper).
        n_region_nodes:
            Integer specifying the number of sum nodes in each (non-root) region (S in the original paper).
        n_leaf_ndoes:
            Integer specifying the number of leaf nodes in each leaf region (I in the original paper).
        root_node:
            SPN-like sum node that represents the root of the model.
        root_region:
            SPN-like sum layer that represents the root region of the model.
    """

    def __init__(
        self,
        region_graph: RegionGraph,
        feature_ctx: FeatureContext,
        n_root_nodes: int,
        n_region_nodes: int,
        n_leaf_nodes: int,
    ) -> None:
        super().__init__(children=[])
        r"""Initializer for ``RatSPN`` object.

        Args:
            region_graph:
                ``RegionGraph`` instance to create RAT-SPN architecture from.
            feature_ctx:
                ``FeatureContext`` instance specifying the domains of the scopes.
                Scope must match the region graphs scope.
            n_root_nodes:
                Integer specifying the number of sum nodes in the root region (C in the original paper).
            n_region_nodes:
                Integer specifying the number of sum nodes in each (non-root) region (S in the original paper).
            n_leaf_ndoes:
                Integer specifying the number of leaf nodes in each leaf region (I in the original paper).

        Raises:
            ValueError: Invalid arguments.
        """
        self.n_root_nodes = n_root_nodes
        self.n_region_nodes = n_region_nodes
        self.n_leaf_nodes = n_leaf_nodes

        if n_root_nodes < 1:
            raise ValueError(f"Specified value of 'n_root_nodes' must be at least 1, but is {n_root_nodes}.")
        if n_region_nodes < 1:
            raise ValueError(f"Specified value for 'n_region_nodes' must be at least 1, but is {n_region_nodes}.")
        if n_leaf_nodes < 1:
            raise ValueError(f"Specified value for 'n_leaf_nodes' must be at least 1, but is {n_leaf_nodes}.")

        # create RAT-SPN from region graph
        self.from_region_graph(region_graph, feature_ctx)

    def from_region_graph(
        self,
        region_graph: RegionGraph,
        feature_ctx: FeatureContext,
    ) -> None:
        r"""Function to create explicit RAT-SPN from an abstract region graph.

        Args:
            region_graph:
                ``RegionGraph`` instance to create RAT-SPN architecture from.
            feature_ctx:
                ``FeatureContext`` instance specifying the domains of the scopes.
                Scope must match the region graphs scope.

        Raises:
            ValueError: Invalid arguments.
        """

        def convert_partition(partition: Partition) -> PartitionLayer:

            return PartitionLayer(
                child_partitions=[[convert_region(region, n_nodes=self.n_region_nodes)] for region in partition.regions]
            )

        def convert_region(region: Region, n_nodes: int) -> Union[SumLayer, HadamardLayer, Module]:

            # non-leaf region
            if region.partitions:
                children = [convert_partition(partition) for partition in region.partitions]
                sum_layer = (
                    CondSumLayer(children=children, n_nodes=n_nodes)
                    if region.scope.is_conditional()
                    else SumLayer(children=children, n_nodes=n_nodes)
                )
                return sum_layer
            # leaf region
            else:
                # split leaf scope into univariate ones and combine them element-wise
                if len(region.scope.query) > 1:
                    partition_signatures = [[feature_ctx.select([rv])] * self.n_leaf_nodes for rv in region.scope.query]
                    child_partitions = [[AutoLeaf(signatures)] for signatures in partition_signatures]
                    return HadamardLayer(child_partitions=child_partitions)
                # create univariate leaf region
                elif len(region.scope.query) == 1:
                    signatures = [feature_ctx.select(region.scope.query)] * self.n_leaf_nodes
                    return AutoLeaf(signatures)
                else:
                    raise ValueError(
                        "Query scope for region is empty and cannot be converted into appropriate RAT-SPN layer representation."
                    )

        if feature_ctx.scope != region_graph.scope:
            raise ValueError(
                f"Scope of specified feature context {feature_ctx.scope} does not match scope of specified region graph {region_graph.scope}."
            )

        if region_graph.root_region is not None:
            self.root_region = convert_region(region_graph.root_region, n_nodes=self.n_root_nodes)
            self.root_node = (
                CondSumNode(children=[self.root_region])
                if region_graph.scope.is_conditional()
                else SumNode(children=[self.root_region])
            )
        else:
            self.root_region = None
            self.root_node = None

    @property
    def n_out(self) -> int:
        """Returns the number of outputs for this module. Returns one since RAT-SPNs always have a single output."""
        return 1

    @property
    def scopes_out(self) -> List[Scope]:
        """Returns the output scopes of the RAT-SPN."""
        return self.root_node.scopes_out


@dispatch(memoize=True)  # type: ignore
def marginalize(
    rat_spn: RatSPN,
    marg_rvs: Iterable[int],
    prune: bool = True,
    dispatch_ctx: Optional[DispatchContext] = None,
) -> Union[RatSPN, None]:
    r"""Structural marginalization for ``RatSPN`` objects in the ``torch`` backend.

    Args:
        rat_spn:
           ``RatSPN`` instance to marginalize.
        marg_rvs:
            Iterable of integers representing the indices of the random variables to marginalize.
        prune:
            Boolean indicating whether or not to prune nodes and modules where possible.
            Has no effect here. Defaults to True.
        dispatch_ctx:
            Optional dispatch context.

    Raises:
        (Marginalized) RAT-SPN or None (if completely maginalized over).
    """
    # since root node and root region all have the same scope, both are them are either fully marginalized or neither
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    marg_root_node = marginalize(rat_spn.root_node, marg_rvs, prune=False, dispatch_ctx=dispatch_ctx)

    if marg_root_node is None:
        return None
    else:
        # initialize new empty RAT-SPN
        marg_rat = RatSPN(
            RegionGraph(),
            n_root_nodes=rat_spn.n_root_nodes,
            n_region_nodes=rat_spn.n_region_nodes,
            n_leaf_nodes=rat_spn.n_leaf_nodes,
        )
        marg_rat.root_node = marg_root_node
        marg_rat.root_region = marg_root_node.children[0]

        return marg_rat


@dispatch(memoize=True)  # type: ignore
def toBase(rat_spn: RatSPN, dispatch_ctx: Optional[DispatchContext] = None) -> BaseRatSPN:
    r"""Conversion for ``RatSPN`` from ``torch`` backend to ``base`` backend.

    Args:
        sum_node:
            Sum node to be converted.
        dispatch_ctx:
            Optional dispatch context.
    """
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    # create RAT-SPN in base backend (using empty region graph)
    base_rat_spn = BaseRatSPN(
        RegionGraph(),
        feature_ctx=FeatureContext(Scope()),
        n_root_nodes=rat_spn.n_root_nodes,
        n_region_nodes=rat_spn.n_region_nodes,
        n_leaf_nodes=rat_spn.n_leaf_nodes,
    )

    # replace actual module graph
    base_rat_spn.root_node = toBase(rat_spn.root_node, dispatch_ctx=dispatch_ctx)
    # set root region
    base_rat_spn.root_region = base_rat_spn.root_node.children[0]

    return base_rat_spn


@dispatch(memoize=True)  # type: ignore
def toTorch(rat_spn: BaseRatSPN, dispatch_ctx: Optional[DispatchContext] = None) -> RatSPN:
    r"""Conversion for ``RatSPN`` from ``base`` backend to ``torch`` backend.

    Args:
        sum_node:
            Sum node to be converted.
        dispatch_ctx:
            Optional dispatch context.
    """
    dispatch_ctx = init_default_dispatch_context(dispatch_ctx)

    # create RAT-SPN in base backend (using empty region graph)
    torch_rat_spn = RatSPN(
        RegionGraph(),
        feature_ctx=FeatureContext(Scope()),
        n_root_nodes=rat_spn.n_root_nodes,
        n_region_nodes=rat_spn.n_region_nodes,
        n_leaf_nodes=rat_spn.n_leaf_nodes,
    )

    # replace actual module graph
    torch_rat_spn.root_node = toTorch(rat_spn.root_node, dispatch_ctx=dispatch_ctx)

    # set root region (root node only has a single region, therefore index root_node.chs[0])
    torch_rat_spn.root_region = torch_rat_spn.root_node.chs[0]

    return torch_rat_spn
