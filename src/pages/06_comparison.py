"""Current versus simulated path comparison page."""

import sys
from pathlib import Path

_src_dir = Path(__file__).resolve().parents[1]
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import bootstrap  # noqa: F401

import streamlit as st

st.title("Change Impact Comparison")
st.caption("Shows the last post-change simulation run stored in this session.")

comparison = st.session_state.get("comparison_result")
current = st.session_state.get("current_path_result")
simulated = st.session_state.get("simulated_path_result")

if comparison is None:
    st.warning("No simulation result yet. Run a scenario on the Post-Change Simulation page.")
    st.stop()

st.subheader("Summary")
st.write(comparison.summary)

metrics = st.columns(4)
metrics[0].metric("Current reachable", "Yes" if comparison.current_reachable else "No")
metrics[1].metric("Simulated reachable", "Yes" if comparison.simulated_reachable else "No")
metrics[2].metric("Path changed", "Yes" if comparison.path_changed else "No")
metrics[3].metric(
    "Hop delta",
    str(len(comparison.simulated_path) - len(comparison.current_path)),
)

left, right = st.columns(2)
with left:
    st.markdown("**Current**")
    st.code(" → ".join(comparison.current_path) or "(none)")
    if comparison.removed_devices:
        st.write("Removed:", ", ".join(comparison.removed_devices))
with right:
    st.markdown("**Simulated**")
    st.code(" → ".join(comparison.simulated_path) or "(none)")
    if comparison.added_devices:
        st.write("Added:", ", ".join(comparison.added_devices))

if comparison.warnings:
    st.subheader("Warnings")
    for warning in comparison.warnings:
        st.warning(warning)

if current and current.hops:
    st.subheader("Current hop details")
    st.dataframe(
        [
            {
                "Device": hop.device,
                "Prefix": hop.matched_prefix,
                "Protocol": hop.route_protocol,
                "Next Hop": hop.next_hop or "",
            }
            for hop in current.hops
        ],
        use_container_width=True,
        hide_index=True,
    )

if simulated and simulated.hops:
    st.subheader("Simulated hop details")
    st.dataframe(
        [
            {
                "Device": hop.device,
                "Prefix": hop.matched_prefix,
                "Protocol": hop.route_protocol,
                "Next Hop": hop.next_hop or "",
            }
            for hop in simulated.hops
        ],
        use_container_width=True,
        hide_index=True,
    )
