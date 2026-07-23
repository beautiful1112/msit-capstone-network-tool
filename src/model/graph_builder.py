"""Builds and updates the NetworkX topology graph."""

import networkx as nx

from src.analysis.next_hop_resolver import normalize_hostname
from src.model.network_model import NetworkState


def build_topology_graph(network_state: NetworkState) -> nx.Graph:
    """Build an undirected CDP neighbour graph from collected device state."""
    graph = nx.Graph()

    for hostname in network_state.devices:
        graph.add_node(normalize_hostname(hostname))

    for hostname, device in network_state.devices.items():
        local = normalize_hostname(hostname)
        for neighbor in device.neighbors:
            if not neighbor.remote_device:
                continue
            # Ignore incomplete CDP entries that have no local interface binding.
            if not (neighbor.local_interface or "").strip():
                continue
            remote = normalize_hostname(neighbor.remote_device)
            if remote == local:
                continue
            if graph.has_edge(local, remote):
                continue
            graph.add_edge(
                local,
                remote,
                local_interface=neighbor.local_interface,
                remote_interface=neighbor.remote_interface,
                remote_ip=neighbor.remote_ip,
            )

    return graph
