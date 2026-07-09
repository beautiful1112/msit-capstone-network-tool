"""Colour-codes current and simulated paths on the topology view."""

import networkx as nx

PATH_NODE_COLOR = "#e74c3c"
DEFAULT_NODE_COLOR = "#3498db"
PATH_EDGE_COLOR = "#e74c3c"
DEFAULT_EDGE_COLOR = "#bdc3c7"


def highlight_path(
    graph: nx.Graph,
    path_devices: list[str] | None,
) -> tuple[list[str], list[str], list[str], list[str]]:
    """Return node and edge colour lists aligned with graph node/edge order."""
    path_set = {device.upper() for device in (path_devices or [])}
    nodes = list(graph.nodes())
    node_colors = [
        PATH_NODE_COLOR if node.upper() in path_set else DEFAULT_NODE_COLOR
        for node in nodes
    ]

    edges = list(graph.edges())
    edge_colors = []
    for left, right in edges:
        on_path = left.upper() in path_set and right.upper() in path_set
        edge_colors.append(PATH_EDGE_COLOR if on_path else DEFAULT_EDGE_COLOR)

    return nodes, node_colors, edges, edge_colors
