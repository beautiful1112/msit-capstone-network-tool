"""Live Netmiko collection trigger page."""

import streamlit as st

st.title("Live Collection")
st.markdown(
    """
Run collection from the CLI for now:

```bash
cd Capstone
source .venv/bin/activate
python -m src.cli.collect
```

Parsed snapshots are saved under `snapshots/` and can be selected on the Path Analysis page.
"""
)
