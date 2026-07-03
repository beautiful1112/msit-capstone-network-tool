# System Design Specification

## 1. Design Context

This document describes the detailed structural design for the capstone network path analysis tool. It expands the high-level architecture into four focused layers: device access (Netmiko), text parsing, graph-based analysis (NetworkX), and the Streamlit presentation layer. The design targets a lab topology with PC1 (10.1.1.10/24), PC2 (10.2.2.10/24), SW1 as default gateway, and routers R1–R4 running OSPF, with R3 loopback 8.8.8.8 and R4 loopback 1.1.1.1.

## 2. Layered Architecture Summary

| Layer | Responsibility | Key Components |
|-------|----------------|----------------|
| Presentation | User interaction and visual output | Streamlit pages, path/topology views |
| Application | Orchestration and workflow control | `app.py`, session state, page routing |
| Analysis & Simulation | Path logic and change prediction | Path analyzer, ECMP detector, simulators |
| Graph Model | Topology representation | NetworkX `DiGraph`, node/edge attributes |
| Parsing | CLI output normalisation | Route, interface, ARP, config, neighbour parsers |
| Collection | Live device access | Netmiko SSH session manager, command runner |
| Data Access | Inventory and credentials | JSON/YAML inventory, local credential loader |

## 3. Device Access Layer (Netmiko)

### 3.1 Purpose

The collection layer establishes read-only SSH sessions to lab devices and retrieves operational command output. Netmiko is selected because it is widely used in network automation and supports Cisco IOS-style syntax used in the lab.

### 3.2 Structural Components

```
src/collector/
├── connection_manager.py    # SSH connect, disconnect, retry, timeout handling
├── command_profiles.py      # Per-platform command sets (cisco_ios)
├── netmiko_collector.py     # Orchestrates multi-device collection
└── snapshot_writer.py         # Saves timestamped raw CLI output
```

### 3.3 Connection Workflow

1. Load device inventory and credentials from local files.
2. For each device, open a Netmiko SSH connection using `device_type`, `host`, `username`, `password`.
3. Execute the command profile (route table, interfaces, ARP, running-config, neighbours).
4. Capture raw text output per command.
5. Write outputs to `snapshots/<timestamp>/<hostname>_<command>.txt`.
6. Return a collection manifest (device list, snapshot path, success/failure status).

### 3.4 Lab Device Command Profile

| Command | Purpose |
|---------|---------|
| `show ip route` | Primary forwarding decision data |
| `show ip interface brief` | Interface IP and up/down status |
| `show ip arp` | Next-hop L2 resolution context |
| `show running-config` | Supporting route and OSPF context |
| `show cdp neighbors detail` | Topology adjacency discovery |

### 3.5 Error Handling

- Connection timeout → log warning, mark device as failed, continue other devices.
- Authentication failure → stop device collection, surface error to UI.
- Partial command failure → store successful outputs, flag incomplete snapshot.

## 4. Text Parsing Architecture

### 4.1 Purpose

Raw CLI text is converted into structured Python dictionaries that downstream modules can consume. Parsing is split by data type so each parser can evolve independently.

### 4.2 Parser Pipeline

```
Raw CLI text
    → TextFSM template OR regex parser
    → Validated record list
    → Normalised domain object (RouteEntry, InterfaceEntry, etc.)
    → JSON-serialisable model for snapshot reuse
```

### 4.3 Structural Components

```
src/parser/
├── base_parser.py           # Shared parsing utilities and validation hooks
├── route_parser.py          # Longest-prefix route entries
├── interface_parser.py      # Interface status and addressing
├── arp_parser.py            # IP-to-MAC mappings
├── config_parser.py         # Static routes and OSPF interface costs
├── neighbor_parser.py       # CDP/LLDP adjacency records
└── normaliser.py            # Unifies parser output into NetworkState schema
```

### 4.4 Parser Input/Output Contract

| Parser | Input | Output | Method |
|--------|-------|--------|--------|
| Route | `show ip route` text | List of route records with prefix, protocol, next-hop, metric | TextFSM / regex |
| Interface | `show ip interface brief` text | Interface name, IP, status | TextFSM / regex |
| ARP | `show ip arp` text | IP, MAC, interface | TextFSM / regex |
| Config | `show running-config` text | Static routes, OSPF cost lines | Section-based regex |
| Neighbour | CDP/LLDP text | Local/remote device, interfaces | TextFSM / regex |

### 4.5 Design Rule

The routing table parser output is the **primary source of truth** for current path analysis. Running configuration supports simulation inputs (static routes, OSPF costs) but does not override live installed routes for the current-state path.

## 5. NetworkX Algorithmic Framework

### 5.1 Purpose

NetworkX provides the graph data structure and algorithms for topology modelling, path exploration, and post-change edge attribute updates.

### 5.2 Graph Model

- **Graph type:** `networkx.DiGraph` (directed; forwarding is directional).
- **Nodes:** Device hostnames (SW1, R1, R2, R3, R4).
- **Edges:** Point-to-point links derived from interface subnets and neighbour data.
- **Edge attributes:** `local_if`, `remote_if`, `subnet`, `ospf_cost`, `status`.

### 5.3 Structural Components

```
src/model/
├── device_model.py          # Device metadata objects
├── interface_model.py       # Interface records
├── routing_model.py         # Route table in memory
├── network_model.py         # Aggregated NetworkState container
└── graph_builder.py         # Builds and updates NetworkX graph

src/analysis/
├── path_analyzer.py         # Hop-by-hop LPM path walk using route tables
├── ecmp_detector.py         # Equal-cost next-hop identification
├── next_hop_resolver.py     # Maps next-hop IP to neighbour device
└── change_comparator.py     # Current vs simulated path diff

src/simulation/
├── route_change_simulator.py  # Static route add/modify/remove on copied model
└── ospf_cost_simulator.py     # OSPF cost edge attribute update
```

### 5.4 Current-State Path Algorithm (Conceptual)

1. Resolve source device from source IP (e.g., PC1 → SW1 VLAN 10 gateway).
2. On current device, perform longest prefix match for destination IP.
3. Resolve next-hop IP to outgoing interface and neighbour device.
4. Repeat until destination subnet is reached or path fails.
5. If multiple equal-cost entries exist, record ECMP candidates.
6. Optionally use `nx.all_simple_paths` for topology-based alternative path hints (labelled as non-forwarding).

### 5.5 Post-Change Simulation Algorithm (Conceptual)

1. Deep-copy the current `NetworkState` and graph.
2. Apply planned change (static route entry or OSPF cost on edge).
3. Re-run path analyzer on the copied model.
4. Pass both path results to `change_comparator`.

## 6. Streamlit Front-End Architecture

### 6.1 Purpose

Streamlit provides a lightweight web dashboard without building a separate front-end stack. It suits a capstone prototype where the priority is functional demonstration rather than production UI polish.

### 6.2 Application Structure

```
src/
├── app.py                     # Streamlit entry point and sidebar navigation
├── pages/
│   ├── 01_dashboard.py
│   ├── 02_inventory.py
│   ├── 03_live_collection.py
│   ├── 04_path_analysis.py
│   ├── 05_post_change_simulation.py
│   ├── 06_comparison.py
│   └── 07_export.py
└── visualization/
    ├── topology_visualizer.py  # PyVis or NetworkX drawing for topology
    ├── path_highlighter.py     # Colour-coded current vs simulated paths
    └── report_renderer.py      # JSON/Markdown export formatting
```

### 6.3 Page Responsibilities

| Page | User Actions | Backend Modules Called |
|------|--------------|----------------------|
| Dashboard | View summary metrics | Reads session state / last snapshot |
| Inventory | Load inventory file | `file_loader`, inventory validator |
| Live Collection | Trigger SSH collection | `netmiko_collector`, `snapshot_writer` |
| Path Analysis | Enter source/dest IP, run analysis | Parsers → `graph_builder` → `path_analyzer` |
| Post-Change Simulation | Define static route or OSPF cost change | `route_change_simulator` / `ospf_cost_simulator` |
| Comparison | View side-by-side path results | `change_comparator`, `path_highlighter` |
| Export | Download report | `report_renderer` |

### 6.4 Session State Design

Streamlit `st.session_state` holds:

- `inventory` — loaded device list
- `current_snapshot` — path to latest collection folder
- `network_state` — parsed model after analysis
- `current_path` — result of live path analysis
- `simulated_path` — result after planned change
- `warnings` — diagnostic messages

### 6.5 Visualisation Colour Scheme

| Colour | Meaning |
|--------|---------|
| Green | Current active forwarding path |
| Blue | Simulated post-change path |
| Red | Removed or unreachable segment |
| Yellow | Warning or risk indicator |
| Grey | Topology elements not on selected path |

## 7. End-to-End Data Flow

```
User (Streamlit UI)
  → Inventory + credentials
  → Netmiko collection (SSH)
  → Raw CLI snapshots
  → Parsers (structured models)
  → NetworkState + NetworkX graph
  → Path analyzer (current path)
  → [Optional] Simulator (copied model)
  → Change comparator
  → Visualisation + export
```

## 8. Diagram Files

Mermaid source files for architecture figures are stored in `docs/diagrams/`:

- `system_architecture.mmd` — full system overview
- `netmiko_collection_layer.mmd` — SSH collection layer
- `parser_pipeline.mmd` — parsing architecture
- `networkx_framework.mmd` — graph and analysis framework
- `streamlit_frontend.mmd` — UI page flow
- `lab_topology.png` — physical lab topology reference
