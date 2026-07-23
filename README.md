# Network Path Analysis and Change Impact Validation Tool

A Python-based MSIT capstone project that collects live operational state from network devices, analyses the current Layer 3 traffic path between source and destination IP addresses, and simulates the impact of planned routing changes without pushing configuration to devices.

**Repository:** https://github.com/beautiful1112/msit-capstone-network-tool

## Project Purpose

Network engineers often need to verify the current traffic path and predict routing change impact before applying changes to production devices. This prototype uses live device state collection as the baseline for path analysis, rather than relying on saved configuration files alone.

## Features

- Live network state collection via Netmiko (SSH)
- TextFSM parsing of routing tables, interfaces, ARP, running configuration (when privileged), and CDP neighbours
- Graph-based topology modelling with NetworkX
- Current-state path analysis with ECMP detection
- Post-change simulation for static routes and OSPF cost changes (copied model only)
- Path comparison and change impact summary
- Streamlit dashboard (inventory, collection, analysis, simulation, comparison, export)
- JSON / Markdown diagnostic export
- PyTest unit tests and GitHub Actions CI

## Lab Topology

| Device | Role | Notes |
|--------|------|-------|
| PC1 | Host | 10.1.1.10/24 |
| PC2 | Host | 10.2.2.10/24 |
| SW1 | Layer 3 gateway | VLAN 10 / VLAN 20 |
| R1–R4 | OSPF routers | R3 loopback 8.8.8.8, R4 loopback 1.1.1.1 |

OSPF exchanges routes between SW1 and the routers. The tool reads installed routes from live devices for current-path analysis.

**Canonical demo snapshot (Week 6):** `snapshots/current_20260721_142059`  
Offline copy for tests: `data/sample_outputs/lab_snapshot_20260721/`

Example observed path on that snapshot: `10.1.1.10` → `8.8.8.8` = **SW1 → R2 → R3** (ECMP also via R1).

## Repository Structure

```
├── README.md
├── requirements.txt
├── src/                 # Application source code
│   ├── app.py           # Streamlit entry point
│   ├── pages/           # Dashboard, inventory, collection, analysis, …
│   ├── collector/       # Netmiko live collection
│   ├── parser/          # TextFSM CLI parsers
│   ├── model/           # Network state + NetworkX graph
│   ├── analysis/        # Path analysis + comparison
│   ├── simulation/      # Static / OSPF change simulation
│   └── visualization/   # Topology figures + report export
├── data/
│   ├── inventory/       # Device inventory templates
│   ├── planned_changes/ # Example simulation scenarios (JSON)
│   └── sample_outputs/  # Offline lab snapshots for tests
├── scripts/
│   └── measure_performance.py
├── tests/
├── docs/diagrams/
└── snapshots/           # Live collection output (not committed)
```

## System Prerequisites

| Item | Requirement |
|------|-------------|
| OS | Linux (developed on Ubuntu) or macOS |
| Python | 3.10+ recommended |
| Lab access | Optional SSH reachability to EVE-NG / Cisco IOS-style devices |
| Browser | For Streamlit UI |

## Setup

```bash
cd Capstone
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy the example files and edit them for your lab (credentials stay local / gitignored):

```bash
cp data/inventory/inventory.example.json data/inventory/inventory.json
cp data/credentials.example.json data/credentials.json
```

## Collect Live Device State

```bash
source .venv/bin/activate
python -m src.cli.collect --inventory data/inventory/inventory.json
```

Optional flags:

- `--credentials data/credentials.json` — SSH credentials file (default)
- `--parse-only snapshots/<snapshot_id>` — parse an existing snapshot without collecting

Parsed output is written to `snapshots/<snapshot_id>/network_state.json`.

## Run the Streamlit Dashboard

```bash
source .venv/bin/activate
streamlit run src/app.py
```

Pages: Dashboard → Inventory → Live Collection → Path Analysis → Post-Change Simulation → Comparison → Export.

## Run Tests

```bash
source .venv/bin/activate
pytest -v
```

## Performance Metrics (evaluation helper)

```bash
python scripts/measure_performance.py --snapshot snapshots/current_20260721_142059
```

Writes optional JSON with `--json-out` for charts in the Week 6 report.

## Suggested Deployment (lab / workstation)

This prototype is intended for an **on-premise engineer workstation or lab host** next to EVE-NG (or equivalent):

1. Install Python dependencies in a virtual environment.
2. Place inventory and credentials on the host (credentials never in Git).
3. Collect snapshots over the management network.
4. Run Streamlit locally (`streamlit run src/app.py`) and open the UI in a browser.
5. Use Export to save Markdown/JSON diagnostics for change review.

Docker or cloud hosting is a possible future enhancement; it is not required for the capstone prototype.

## Security

Do not commit credentials or live snapshots to version control. Use read-only lab accounts where possible. The tool never pushes configuration changes to devices.

## License

Academic project — University of the People, MSIT 5910 Capstone.
