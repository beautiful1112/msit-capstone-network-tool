"""Renders network topology graph for the dashboard."""

from __future__ import annotations

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from src.visualization.path_highlighter import (
    BOTH_NODE_COLOR,
    CURRENT_NODE_COLOR,
    DEFAULT_NODE_COLOR,
    SIMULATED_NODE_COLOR,
    highlight_path,
)


def render_topology_figure(
    graph: nx.Graph,
    path_devices: list[str] | None = None,
    simulated_path: list[str] | None = None,
    title: str = "CDP Topology",
) -> Figure:
    """Return a matplotlib figure of the topology with optional path highlights."""
    figure, axis = plt.subplots(figsize=(8, 5))
    if graph.number_of_nodes() == 0:
        axis.text(
            0.5,
            0.5,
            "No CDP neighbours found in snapshot.",
            ha="center",
            va="center",
        )
        axis.axis("off")
        return figure

    layout = nx.spring_layout(graph, seed=42)
    nodes, node_colors, edges, edge_colors = highlight_path(
        graph,
        path_devices,
        simulated_path=simulated_path,
    )

    nx.draw_networkx_edges(
        graph,
        layout,
        edgelist=edges,
        edge_color=edge_colors,
        width=2.2,
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

    if path_devices or simulated_path:
        legend_items = [
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=CURRENT_NODE_COLOR,
                markersize=10,
                label="Current path",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=SIMULATED_NODE_COLOR,
                markersize=10,
                label="Simulated path",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=BOTH_NODE_COLOR,
                markersize=10,
                label="On both paths",
            ),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor=DEFAULT_NODE_COLOR,
                markersize=10,
                label="Other device",
            ),
        ]
        axis.legend(handles=legend_items, loc="lower left", fontsize=8)

    figure.tight_layout()
    return figure
