"""Streamlit dashboard summary page."""

import streamlit as st

st.title("Network Path Analysis Tool")
st.markdown(
    """
Use **Path Analysis** to trace a Layer 3 path between two IP addresses using a
collected device snapshot. Use **Live Collection** (CLI) or the collector page
to refresh snapshot data from the lab.
"""
)
st.info("Demo path: `10.1.1.10` → `8.8.8.8` (PC1 to R3 loopback).")
