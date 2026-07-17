"""Streamlit dashboard summary page."""

import streamlit as st

st.title("Network Path Analysis Tool")
st.markdown(
    """
Use **Path Analysis** for the current forwarding path from a collected snapshot.

Use **Post-Change Simulation** to select any device and apply planned static-route
or OSPF-cost changes to a copied model (nothing is pushed to the lab), then
compare the predicted path on **Comparison**.
"""
)
st.info("Demo: `10.1.1.10` → `8.8.8.8`, then add a static on SW1 via `10.0.11.2` (R1).")
