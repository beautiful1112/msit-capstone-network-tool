"""Renders network topology graph for the dashboard."""

from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.figure import Figure

from src.visualization.path_highlighter import highlight_path


def render_topology_figure(
    graph: nx.Graph,
    path_devices: list[str] | None = None,
    title: str = "CDP Topology",
) -> Figure:
    """Return a matplotlib figure of the topology with optional path highlight."""
    figure, axis = plt.subplots(figsize=(8, 5))
    if graph.number_of_nodes() == 0:
        axis.text(0.5, 0.5, "No CDP neighbours found in snapshot.", ha="center", va="center")
        axis.axis("off")
        return figure

    layout = nx.spring_layout(graph, seed=42)
    nodes, node_colors, edges, edge_colors = highlight_path(graph, path_devices)

    nx.draw_networkx_edges(
        graph,
        layout,
        edgelist=edges,
        edge_color=edge_colors,
        width=2.0,
        ax=axis,
    )
    nx.draw_networkx_nodes(
        graph,
        layout,
        nodelist=nodes,
        node_color=node_colors,
        node_size=1200,
        ax=axis,
    )
    nx.draw_networkx_labels(graph, layout, font_size=10, font_color="white", ax=axis)
    axis.set_title(title)
    axis.axis("off")
    figure.tight_layout()
    return figure
