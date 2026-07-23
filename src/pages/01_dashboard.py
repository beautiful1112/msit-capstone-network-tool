"""Streamlit dashboard summary page."""

import sys
from pathlib import Path

_src_dir = Path(__file__).resolve().parents[1]
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import bootstrap  # noqa: F401

import streamlit as st

from src.utils.snapshot_utils import discover_snapshots, load_network_state

st.title("Network Path Analysis Tool")
st.caption(
    "Live-state path analysis and Layer 3 change-impact simulation for the MSIT capstone lab."
)

st.markdown(
    """
**Workflow:** Inventory → Live Collection → Path Analysis → Post-Change Simulation →
Comparison → Export.

Nothing is pushed to devices. Simulation always runs on a copied model.
"""
)

snapshots = discover_snapshots()
if not snapshots:
    st.warning("No snapshots found yet. Run Live Collection or use a sample under `data/sample_outputs/`.")
    st.stop()

labels = [path.name for path in snapshots]
default_index = 0
last = st.session_state.get("current_snapshot")
if last:
    last_name = Path(str(last)).name
    if last_name in labels:
        default_index = labels.index(last_name)

selected_label = st.selectbox("Active snapshot", labels, index=default_index)
snapshot_path = snapshots[labels.index(selected_label)]
network_state = load_network_state(snapshot_path)

total_routes = sum(len(device.routes) for device in network_state.devices.values())
total_ifaces = sum(len(device.interfaces) for device in network_state.devices.values())
total_arp = sum(len(device.arp) for device in network_state.devices.values())
total_neighbors = sum(len(device.neighbors) for device in network_state.devices.values())

metrics = st.columns(4)
metrics[0].metric("Devices", len(network_state.devices))
metrics[1].metric("Routes parsed", total_routes)
metrics[2].metric("Interfaces", total_ifaces)
metrics[3].metric("ARP / CDP", f"{total_arp} / {total_neighbors}")

st.subheader("Per-device summary")
rows = []
for hostname, device in sorted(network_state.devices.items()):
    rows.append(
        {
            "Device": hostname,
            "Routes": len(device.routes),
            "Interfaces": len(device.interfaces),
            "ARP": len(device.arp),
            "Neighbors": len(device.neighbors),
        }
    )
st.dataframe(rows, use_container_width=True, hide_index=True)

st.subheader("Last analysis in this session")
current = st.session_state.get("current_path_result")
comparison = st.session_state.get("comparison_result")
if current is not None:
    path_text = " → ".join(current.path_devices) if current.path_devices else "(none)"
    st.write(
        f"**Current path** `{current.source_ip}` → `{current.destination_ip}`: "
        f"`{path_text}` "
        f"({'reachable' if current.reachable else 'unreachable'})"
    )
else:
    st.caption("No path analysis run yet in this browser session.")

if comparison is not None:
    st.write(f"**Last comparison:** {comparison.summary}")
else:
    st.caption("No post-change comparison stored yet.")

st.info(
    "Demo path: `10.1.1.10` → `8.8.8.8`. "
    "Try a static on SW1 via `10.0.11.2`, or raise OSPF cost on SW1 `GigabitEthernet0/3`."
)
