"""Streamlit application entry point and page routing."""

import bootstrap  # noqa: F401

import streamlit as st

dashboard = st.Page("pages/01_dashboard.py", title="Dashboard", default=True)
inventory = st.Page("pages/02_inventory.py", title="Inventory")
live_collection = st.Page("pages/03_live_collection.py", title="Live Collection")
path_analysis = st.Page("pages/04_path_analysis.py", title="Path Analysis")
post_change = st.Page(
    "pages/05_post_change_simulation.py", title="Post-Change Simulation"
)
comparison = st.Page("pages/06_comparison.py", title="Comparison")
export_page = st.Page("pages/07_export.py", title="Export")

navigation = st.navigation(
    [
        dashboard,
        inventory,
        live_collection,
        path_analysis,
        post_change,
        comparison,
        export_page,
    ]
)
navigation.run()
