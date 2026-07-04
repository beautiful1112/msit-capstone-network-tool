# Network Path Analysis and Change Impact Validation Tool

A Python-based MSIT capstone project that collects live operational state from network devices, analyses the current Layer 3 traffic path between source and destination IP addresses, and simulates the impact of planned routing changes.

## Project Purpose

Network engineers often need to verify the current traffic path and predict routing change impact before applying changes to production devices. This prototype uses live device state collection as the baseline for path analysis, rather than relying on saved configuration files alone.

## Features

- Live network state collection via Netmiko (SSH)
- Parsing of routing tables, interfaces, ARP, running configuration, and CDP neighbours
- Graph-based topology modelling with NetworkX (planned)
- Current-state path analysis with ECMP detection (planned)
- Post-change simulation for static routes and OSPF cost changes (planned)
- Path comparison and change impact reporting (planned)
- Streamlit dashboard for visualisation (planned)

## Lab Topology

| Device | Role | Notes |
|--------|------|-------|
| PC1 | Host | 10.1.1.10/24 |
| PC2 | Host | 10.2.2.10/24 |
| SW1 | Layer 3 gateway | VLAN 10 / VLAN 20 |
| R1–R4 | OSPF routers | R3 loopback 8.8.8.8, R4 loopback 1.1.1.1 |

OSPF is used for route exchange between SW1 and the routers. The tool reads installed routes from live devices for current-path analysis.

## Repository Structure

```
├── README.md
├── requirements.txt
├── src/                 # Application source code
│   ├── collector/       # Netmiko live collection
│   ├── parser/          # CLI output parsers
│   ├── model/           # Network state models
│   └── ...
├── data/
│   └── inventory/       # Device inventory templates
├── tests/
├── docs/diagrams/       # Architecture figures
└── snapshots/           # Timestamped collection output (not committed)
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
```

Copy the example files and edit them for your lab:

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

## Security

Do not commit credentials or live snapshots to version control. Use read-only lab accounts where possible.

## License

Academic project — University of the People, MSIT 5910 Capstone.
