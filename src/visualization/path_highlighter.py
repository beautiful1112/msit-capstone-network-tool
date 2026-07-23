"""Colour-codes current and simulated paths on the topology view."""

from __future__ import annotations

import networkx as nx

# Architecture colour rules: green = current, blue = simulated, grey = other.
CURRENT_NODE_COLOR = "#27ae60"
SIMULATED_NODE_COLOR = "#2980b9"
BOTH_NODE_COLOR = "#8e44ad"
DEFAULT_NODE_COLOR = "#95a5a6"

CURRENT_EDGE_COLOR = "#27ae60"
SIMULATED_EDGE_COLOR = "#2980b9"
BOTH_EDGE_COLOR = "#8e44ad"
DEFAULT_EDGE_COLOR = "#bdc3c7"


def _path_edge_set(path_devices: list[str] | None) -> set[tuple[str, str]]:
    if not path_devices or len(path_devices) < 2:
        return set()
    edges: set[tuple[str, str]] = set()
    for index in range(len(path_devices) - 1):
        left = path_devices[index].upper()
        right = path_devices[index + 1].upper()
        edges.add((left, right))
        edges.add((right, left))
    return edges


def highlight_path(
    graph: nx.Graph,
    path_devices: list[str] | None,
    simulated_path: list[str] | None = None,
) -> tuple[list[str], list[str], list[tuple[str, str]], list[str]]:
    """Return node/edge lists and colours for current and optional simulated paths."""
    current_set = {device.upper() for device in (path_devices or [])}
    simulated_set = {device.upper() for device in (simulated_path or [])}
    current_edges = _path_edge_set(path_devices)
    simulated_edges = _path_edge_set(simulated_path)

    nodes = list(graph.nodes())
    node_colors: list[str] = []
    for node in nodes:
        key = node.upper()
        in_current = key in current_set
        in_simulated = key in simulated_set
        if in_current and in_simulated:
            node_colors.append(BOTH_NODE_COLOR)
        elif in_current:
            node_colors.append(CURRENT_NODE_COLOR)
        elif in_simulated:
            node_colors.append(SIMULATED_NODE_COLOR)
        else:
            node_colors.append(DEFAULT_NODE_COLOR)

    edges = list(graph.edges())
    edge_colors: list[str] = []
    for left, right in edges:
        pair = (left.upper(), right.upper())
        on_current = pair in current_edges
        on_simulated = pair in simulated_edges
        if on_current and on_simulated:
            edge_colors.append(BOTH_EDGE_COLOR)
        elif on_current:
            edge_colors.append(CURRENT_EDGE_COLOR)
        elif on_simulated:
            edge_colors.append(SIMULATED_EDGE_COLOR)
        else:
            edge_colors.append(DEFAULT_EDGE_COLOR)

    return nodes, node_colors, edges, edge_colors
