"""Current-state path analysis page."""

import sys
from pathlib import Path

_src_dir = Path(__file__).resolve().parents[1]
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import bootstrap  # noqa: F401

import streamlit as st

from src.analysis.path_analyzer import analyze_path
from src.model.graph_builder import build_topology_graph
from src.utils.snapshot_utils import discover_snapshots, load_network_state
from src.visualization.topology_visualizer import render_topology_figure

st.title("Path Analysis")
st.caption("Hop-by-hop L3 path walk using collected route tables and CDP neighbours.")

snapshots = discover_snapshots()
if not snapshots:
    st.warning("No snapshots found. Run live collection first.")
    st.stop()

labels = [path.name for path in snapshots]
selected_label = st.selectbox("Snapshot", labels, index=0)
snapshot_path = snapshots[labels.index(selected_label)]

col1, col2 = st.columns(2)
with col1:
    source_ip = st.text_input("Source IP", value="10.1.1.10")
with col2:
    destination_ip = st.text_input("Destination IP", value="8.8.8.8")

if st.button("Analyze Path", type="primary"):
    with st.spinner("Loading snapshot and analysing path..."):
        network_state = load_network_state(snapshot_path)
        result = analyze_path(network_state, source_ip.strip(), destination_ip.strip())
        graph = build_topology_graph(network_state)

    st.subheader("Result")
    if result.reachable:
        st.success(f"Reachable: {' → '.join(result.path_devices)}")
    else:
        st.error("Destination not reachable with collected routing data.")

    if result.warnings:
        for warning in result.warnings:
            st.warning(warning)

    if result.hops:
        st.dataframe(
            [
                {
                    "Hop": index + 1,
                    "Device": hop.device,
                    "Matched Prefix": hop.matched_prefix,
                    "Protocol": hop.route_protocol,
                    "Next Hop": hop.next_hop or "",
                    "Egress Interface": hop.egress_interface or "",
                    "Next Device": hop.next_device or "",
                }
                for index, hop in enumerate(result.hops)
            ],
            use_container_width=True,
            hide_index=True,
        )

    figure = render_topology_figure(
        graph,
        path_devices=result.path_devices,
        title=f"Topology — {selected_label}",
    )
    st.pyplot(figure, clear_figure=True)
