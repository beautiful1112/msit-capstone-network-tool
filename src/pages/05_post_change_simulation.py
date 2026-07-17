"""Post-change routing simulation page."""

import sys
from pathlib import Path

_src_dir = Path(__file__).resolve().parents[1]
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import bootstrap  # noqa: F401

import streamlit as st

from src.analysis.change_comparator import compare_paths
from src.analysis.path_analyzer import analyze_path
from src.model.graph_builder import build_topology_graph
from src.simulation.model_copy import OspfCostChange, StaticRouteChange
from src.simulation import apply_planned_changes
from src.utils.snapshot_utils import discover_snapshots, load_network_state
from src.visualization.topology_visualizer import render_topology_figure


def _device_interfaces(network_state, hostname: str) -> list[str]:
    device = network_state.devices.get(hostname)
    if device is None:
        return []
    names = {iface.interface for iface in device.interfaces if iface.interface}
    # Prefer L3-looking names first; keep stable sort.
    return sorted(names)


def _hops_table(hops):
    return [
        {
            "Hop": index + 1,
            "Device": hop.device,
            "Matched Prefix": hop.matched_prefix,
            "Protocol": hop.route_protocol,
            "Next Hop": hop.next_hop or "",
            "Egress Interface": hop.egress_interface or "",
            "Next Device": hop.next_device or "",
        }
        for index, hop in enumerate(hops)
    ]


st.title("Post-Change Simulation")
st.caption(
    "Apply planned static-route or OSPF-cost changes to a **copied** model "
    "(nothing is pushed to devices), then predict the new traffic path."
)

snapshots = discover_snapshots()
if not snapshots:
    st.warning("No snapshots found. Run live collection first.")
    st.stop()

labels = [path.name for path in snapshots]
selected_label = st.selectbox("Snapshot", labels, index=0, key="sim_snapshot")
snapshot_path = snapshots[labels.index(selected_label)]

col1, col2 = st.columns(2)
with col1:
    source_ip = st.text_input("Source IP", value="10.1.1.10", key="sim_src")
with col2:
    destination_ip = st.text_input("Destination IP", value="8.8.8.8", key="sim_dst")

network_state = load_network_state(snapshot_path)
devices = sorted(network_state.devices.keys())

st.subheader("Planned changes")
st.markdown(
    "Add one or more changes. Each change targets **one device**. "
    "You can modify any device in the snapshot."
)

if "planned_change_rows" not in st.session_state:
    st.session_state.planned_change_rows = 1

c_add, c_clear = st.columns(2)
with c_add:
    if st.button("Add another change"):
        st.session_state.planned_change_rows += 1
        st.rerun()
with c_clear:
    if st.button("Clear changes"):
        st.session_state.planned_change_rows = 1
        st.rerun()

planned_changes = []
for index in range(st.session_state.planned_change_rows):
    st.markdown(f"**Change {index + 1}**")
    left, right = st.columns(2)
    with left:
        device = st.selectbox(
            "Device",
            devices,
            key=f"chg_device_{index}",
        )
        change_type = st.selectbox(
            "Change type",
            ["Static route", "OSPF cost"],
            key=f"chg_type_{index}",
        )
    with right:
        if change_type == "Static route":
            action = st.selectbox(
                "Action",
                ["add", "modify", "remove"],
                key=f"chg_action_{index}",
            )
            prefix = st.text_input(
                "Prefix (CIDR)",
                value="8.8.8.8/32",
                key=f"chg_prefix_{index}",
            )
            next_hop = st.text_input(
                "Next-hop IP",
                value="10.0.11.2",
                key=f"chg_nh_{index}",
                help="Example: SW1 toward R1 uses 10.0.11.2",
            )
            planned_changes.append(
                StaticRouteChange(
                    device=device,
                    action=action,  # type: ignore[arg-type]
                    prefix=prefix.strip(),
                    next_hop=next_hop.strip() or None,
                )
            )
        else:
            interfaces = _device_interfaces(network_state, device) or ["GigabitEthernet0/0"]
            interface = st.selectbox(
                "Interface",
                interfaces,
                key=f"chg_iface_{index}",
            )
            new_cost = st.number_input(
                "New OSPF cost",
                min_value=1,
                value=100,
                step=1,
                key=f"chg_cost_{index}",
            )
            planned_changes.append(
                OspfCostChange(
                    device=device,
                    interface=interface,
                    new_cost=int(new_cost),
                )
            )

propagate = st.checkbox(
    "Propagate OSPF metric delta to upstream neighbours (approximation)",
    value=True,
)

if st.button("Run simulation", type="primary"):
    with st.spinner("Analysing current and simulated paths..."):
        current = analyze_path(network_state, source_ip.strip(), destination_ip.strip())
        simulated_state, sim_warnings = apply_planned_changes(
            network_state,
            planned_changes,
            propagate_ospf_upstream=propagate,
        )
        simulated = analyze_path(
            simulated_state, source_ip.strip(), destination_ip.strip()
        )
        comparison = compare_paths(current, simulated, extra_warnings=sim_warnings)
        graph = build_topology_graph(network_state)

    st.session_state["comparison_result"] = comparison
    st.session_state["current_path_result"] = current
    st.session_state["simulated_path_result"] = simulated

    st.subheader("Comparison summary")
    if comparison.path_changed:
        st.warning(comparison.summary)
    else:
        st.success(comparison.summary)

    left, right = st.columns(2)
    with left:
        st.markdown("**Current path**")
        if current.reachable:
            st.info(" → ".join(current.path_devices))
        else:
            st.error("Unreachable")
        if current.hops:
            st.dataframe(_hops_table(current.hops), use_container_width=True, hide_index=True)
    with right:
        st.markdown("**Simulated post-change path**")
        if simulated.reachable:
            st.info(" → ".join(simulated.path_devices))
        else:
            st.error("Unreachable")
        if simulated.hops:
            st.dataframe(
                _hops_table(simulated.hops), use_container_width=True, hide_index=True
            )

    if comparison.warnings:
        st.subheader("Warnings / notes")
        for warning in comparison.warnings:
            st.caption(f"• {warning}")

    st.subheader("Topology (simulated path highlighted)")
    figure = render_topology_figure(
        graph,
        path_devices=simulated.path_devices,
        title=f"Simulated path — {selected_label}",
    )
    st.pyplot(figure, clear_figure=True)

    st.info("Open the Comparison page for a side-by-side persisted view of the last run.")
