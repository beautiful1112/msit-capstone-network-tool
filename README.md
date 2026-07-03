# Network Path Analysis and Change Impact Validation Tool

A Python-based capstone project for MSIT 5910. This tool collects live operational state from network devices, analyses the current traffic path between source and destination IP addresses, and simulates the impact of planned routing changes.

## Project Purpose

Network engineers often need to verify the current traffic path and predict routing change impact before applying changes to production devices. This prototype uses live device state collection (not static config files alone) as the baseline for path analysis.

## Features (Planned)

- Live network state collection via Netmiko (SSH)
- Routing table, interface, ARP, and neighbour parsing
- Graph-based topology modelling with NetworkX
- Current-state path analysis with ECMP detection
- Post-change simulation (static routes, OSPF cost changes)
- Path comparison and change impact reporting
- Streamlit dashboard for visualisation

## Repository Structure

```
Capstone/
├── README.md
├── requirements.txt
├── src/              # Application source code
├── data/             # Inventory templates and sample data
├── tests/            # Unit and system tests
├── docs/             # Diagrams, screenshots, evidence
├── snapshots/        # Timestamped collection outputs (gitignored)
└── presentation/     # Slides for final presentation
```

## Lab Topology

- PC1 (10.1.1.10/24) and PC2 (10.2.2.10/24) via SW1
- Routers R1–R4 with OSPF; R3 loopback 8.8.8.8, R4 loopback 1.1.1.1

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Branching Strategy

- `main` — stable, submission-ready code
- `development` — active feature work and integration

## Security Note

Do not commit credentials. Use `data/inventory/inventory.example.json` as a template only.

## Author

MSIT Capstone Project — UoPeople
