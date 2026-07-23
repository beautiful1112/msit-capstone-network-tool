"""Report export page."""

import sys
from pathlib import Path

_src_dir = Path(__file__).resolve().parents[1]
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import bootstrap  # noqa: F401

import streamlit as st

from src.visualization.report_renderer import (
    build_export_payload,
    render_json_report,
    render_markdown_report,
)

st.title("Export Report")
st.caption(
    "Export the last path analysis and optional post-change comparison from this session "
    "as JSON or Markdown (FR11)."
)

current = st.session_state.get("current_path_result")
simulated = st.session_state.get("simulated_path_result")
comparison = st.session_state.get("comparison_result")
snapshot_hint = st.session_state.get("analysis_snapshot_id") or st.session_state.get(
    "current_snapshot"
)
snapshot_id = Path(str(snapshot_hint)).name if snapshot_hint else None

if current is None and comparison is None:
    st.warning(
        "No analysis results in this session yet. Run Path Analysis or Post-Change Simulation first."
    )
    st.stop()

payload = build_export_payload(
    snapshot_id=snapshot_id,
    current=current,
    simulated=simulated,
    comparison=comparison,
    planned_change_notes=st.session_state.get("planned_change_notes"),
)

st.subheader("Preview")
if current is not None:
    st.write(
        f"**Current:** `{current.source_ip}` → `{current.destination_ip}` = "
        f"`{' → '.join(current.path_devices) or '(none)'}`"
    )
if comparison is not None:
    st.write(f"**Comparison:** {comparison.summary}")

fmt = st.radio("Format", ["Markdown", "JSON"], horizontal=True)
if fmt == "JSON":
    body = render_json_report(payload)
    file_name = f"path_report_{snapshot_id or 'session'}.json"
    mime = "application/json"
else:
    body = render_markdown_report(payload)
    file_name = f"path_report_{snapshot_id or 'session'}.md"
    mime = "text/markdown"

st.download_button(
    "Download report",
    data=body.encode("utf-8"),
    file_name=file_name,
    mime=mime,
    type="primary",
)

with st.expander("Report content"):
    if fmt == "JSON":
        st.code(body, language="json")
    else:
        st.markdown(body)
