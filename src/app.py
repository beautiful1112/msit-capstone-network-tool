"""Streamlit application entry point and page routing."""

import bootstrap  # noqa: F401

import streamlit as st

dashboard = st.Page("pages/01_dashboard.py", title="Dashboard", default=True)
path_analysis = st.Page("pages/04_path_analysis.py", title="Path Analysis")
live_collection = st.Page("pages/03_live_collection.py", title="Live Collection")

navigation = st.navigation([dashboard, path_analysis, live_collection])
navigation.run()
