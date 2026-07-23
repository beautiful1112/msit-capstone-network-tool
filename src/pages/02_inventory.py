"""Device inventory loading page."""

import sys
from pathlib import Path

_src_dir = Path(__file__).resolve().parents[1]
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import bootstrap  # noqa: F401

import streamlit as st

from src.utils.file_loader import load_inventory
from src.utils.snapshot_utils import project_root

PROJECT_ROOT = project_root()
DEFAULT_INVENTORY = PROJECT_ROOT / "data" / "inventory" / "inventory.json"
EXAMPLE_INVENTORY = PROJECT_ROOT / "data" / "inventory" / "inventory.example.json"

st.title("Device Inventory")
st.caption(
    "Inventory is file-based JSON (no database). Credentials stay in a separate "
    "gitignored file and are never shown here."
)

path_input = st.text_input(
    "Inventory file",
    value=str(DEFAULT_INVENTORY if DEFAULT_INVENTORY.exists() else EXAMPLE_INVENTORY),
)
inventory_path = Path(path_input.strip())

if not inventory_path.exists():
    st.error(f"Inventory file not found: `{inventory_path}`")
    st.code(
        "cp data/inventory/inventory.example.json data/inventory/inventory.json",
        language="bash",
    )
    st.stop()

try:
    devices = load_inventory(inventory_path)
except Exception as exc:  # noqa: BLE001
    st.error(f"Failed to load inventory: {exc}")
    st.stop()

st.success(f"Loaded {len(devices)} device(s) from `{inventory_path.name}`.")
st.session_state["inventory_path"] = str(inventory_path)

rows = []
for item in devices:
    rows.append(
        {
            "Hostname": item.get("hostname", ""),
            "Mgmt IP": item.get("mgmt_ip", ""),
            "Platform": item.get("platform", ""),
            "Role": item.get("role", ""),
        }
    )
st.dataframe(rows, use_container_width=True, hide_index=True)

with st.expander("Expected inventory format"):
    st.code(
        '[\n'
        '  {"hostname": "SW1", "mgmt_ip": "192.168.1.10", '
        '"platform": "cisco_ios", "role": "switch"}\n'
        "]",
        language="json",
    )

st.info("Open **Live Collection** to collect from these devices over SSH.")
