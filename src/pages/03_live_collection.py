"""Live Netmiko collection trigger page."""

import sys
from pathlib import Path

_src_dir = Path(__file__).resolve().parents[1]
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

import bootstrap  # noqa: F401

import streamlit as st

from src.collector.netmiko_collector import collect_live_state
from src.parser.normaliser import build_network_state, save_network_state
from src.utils.file_loader import load_credentials, load_inventory
from src.utils.snapshot_utils import discover_snapshots, project_root

PROJECT_ROOT = project_root()
DEFAULT_INVENTORY = PROJECT_ROOT / "data" / "inventory" / "inventory.json"
DEFAULT_CREDENTIALS = PROJECT_ROOT / "data" / "credentials.json"
SNAPSHOTS_DIR = PROJECT_ROOT / "snapshots"


st.title("Live Collection")
st.caption(
    "Collect routing tables, interfaces, ARP, neighbours, and running-config "
    "from lab devices over SSH, then parse them into a snapshot for path analysis."
)

inv_ok = DEFAULT_INVENTORY.exists()
cred_ok = DEFAULT_CREDENTIALS.exists()

status_cols = st.columns(2)
status_cols[0].markdown(
    f"**Inventory:** `{'found' if inv_ok else 'missing'}`  \n`{DEFAULT_INVENTORY}`"
)
status_cols[1].markdown(
    f"**Credentials:** `{'found' if cred_ok else 'missing'}`  \n`{DEFAULT_CREDENTIALS}`"
)

if not inv_ok:
    st.warning(
        "Copy `data/inventory/inventory.example.json` to "
        "`data/inventory/inventory.json` before collecting."
    )
if not cred_ok:
    st.warning(
        "Copy `data/credentials.example.json` to `data/credentials.json` "
        "and set the lab username / password (and enable secret if needed)."
    )

timeout = st.number_input("SSH timeout (seconds)", min_value=5, max_value=120, value=30)

if st.button(
    "Collect from lab now",
    type="primary",
    disabled=not (inv_ok and cred_ok),
):
    progress = st.progress(0, text="Loading inventory and credentials...")
    log_box = st.empty()
    try:
        inventory = load_inventory(DEFAULT_INVENTORY)
        credentials = load_credentials(DEFAULT_CREDENTIALS)
        progress.progress(10, text=f"Connecting to {len(inventory)} device(s)...")

        with st.spinner(
            "Running Netmiko collection. This usually takes 15–40 seconds..."
        ):
            manifest = collect_live_state(
                inventory=inventory,
                credentials=credentials,
                snapshots_dir=str(SNAPSHOTS_DIR),
                timeout=int(timeout),
            )

        progress.progress(70, text="Parsing collected CLI output...")
        snapshot_path = Path(manifest["snapshot_path"])
        network_state = build_network_state(snapshot_path)
        output_path = save_network_state(
            network_state,
            snapshot_path / "network_state.json",
        )
        progress.progress(100, text="Collection complete.")

        st.session_state["last_collection_snapshot"] = str(snapshot_path)
        st.session_state["current_snapshot"] = str(snapshot_path)

        success = [
            item for item in manifest.get("devices", []) if item.get("status") == "success"
        ]
        failed = [
            item for item in manifest.get("devices", []) if item.get("status") != "success"
        ]

        st.success(
            f"Snapshot saved: `{snapshot_path.name}` "
            f"({len(success)}/{len(manifest.get('devices', []))} devices OK)"
        )
        st.write(f"Parsed model: `{output_path}`")

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
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)

        if failed:
            st.error("Some devices failed:")
            for item in failed:
                st.write(
                    f"- **{item.get('hostname')}** ({item.get('mgmt_ip')}): "
                    f"{'; '.join(item.get('errors') or ['unknown error'])}"
                )

        log_box.json(
            {
                "snapshot_id": network_state.snapshot_id,
                "snapshot_path": str(snapshot_path),
                "device_count": len(network_state.devices),
            }
        )
        st.info("Use Path Analysis or Post-Change Simulation and select this snapshot.")
    except Exception as exc:  # noqa: BLE001 — show any collection failure in UI
        progress.progress(100, text="Collection failed.")
        st.error(f"Collection failed: {exc}")

st.divider()
st.subheader("Existing snapshots")
existing = discover_snapshots()
if existing:
    st.write(", ".join(path.name for path in existing[:12]))
    if len(existing) > 12:
        st.caption(f"...and {len(existing) - 12} more")
else:
    st.caption("No snapshots found yet.")

with st.expander("CLI alternative"):
    st.code(
        "cd Capstone\n"
        "source .venv/bin/activate\n"
        "python -m src.cli.collect",
        language="bash",
    )
