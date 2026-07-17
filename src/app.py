"""Streamlit application entry point and page routing."""

import bootstrap  # noqa: F401

import streamlit as st

dashboard = st.Page("pages/01_dashboard.py", title="Dashboard", default=True)
path_analysis = st.Page("pages/04_path_analysis.py", title="Path Analysis")
post_change = st.Page(
    "pages/05_post_change_simulation.py", title="Post-Change Simulation"
)
comparison = st.Page("pages/06_comparison.py", title="Comparison")
live_collection = st.Page("pages/03_live_collection.py", title="Live Collection")

navigation = st.navigation(
    [dashboard, path_analysis, post_change, comparison, live_collection]
)
navigation.run()
