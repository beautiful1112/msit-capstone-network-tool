import json
from pathlib import Path

import pytest

from src.parser.arp_parser import parse_arp
from src.parser.interface_parser import parse_interfaces
from src.parser.normaliser import build_network_state
from src.parser.route_parser import parse_routes

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_routes_from_fixture():
    text = (FIXTURES / "r1_ip_route.txt").read_text(encoding="utf-8")
    routes = parse_routes(text)
    prefixes = {route.prefix for route in routes}
    assert "10.1.1.0/24" in prefixes
    assert "10.2.2.0/24" in prefixes
    assert "8.8.8.8/32" in prefixes
    connected = [route for route in routes if route.is_connected]
    assert len(connected) == 1
    assert connected[0].out_interface == "Vlan10"


def test_parse_interfaces_from_fixture():
    text = (FIXTURES / "r1_interfaces.txt").read_text(encoding="utf-8")
    interfaces = parse_interfaces(text)
    assert len(interfaces) == 3
    assert interfaces[0].interface == "Vlan10"
    assert interfaces[0].ip_address == "10.1.1.1"


def test_parse_arp_from_fixture():
    text = (FIXTURES / "r1_arp.txt").read_text(encoding="utf-8")
    entries = parse_arp(text)
    assert len(entries) == 2
    assert entries[0].ip_address == "192.168.12.2"


def test_parse_routes_ecmp_continuation():
    text = (FIXTURES / "sw1_ecmp_route.txt").read_text(encoding="utf-8")
    routes = parse_routes(text)
    ecmp_routes = [r for r in routes if r.prefix == "8.8.8.8/32"]
    assert len(ecmp_routes) == 2
    next_hops = {route.next_hop for route in ecmp_routes}
    assert next_hops == {"10.0.12.2", "10.0.11.2"}


def test_parse_live_sw1_routes_from_lab_snapshot():
    root = Path(__file__).resolve().parents[1] / "data" / "sample_outputs"
    snapshot = root / "lab_snapshot_20260721"
    if not (snapshot / "SW1_ip_route.txt").exists():
        snapshot = root / "lab_snapshot_20260707"
    if not (snapshot / "SW1_ip_route.txt").exists():
        pytest.skip("Lab snapshot not available")
    text = (snapshot / "SW1_ip_route.txt").read_text(encoding="utf-8")
    routes = parse_routes(text, device="SW1")
    prefixes = {route.prefix for route in routes}
    assert "8.8.8.8/32" in prefixes
    assert "10.1.1.0/24" in prefixes
    assert len([r for r in routes if r.prefix == "8.8.8.8/32"]) >= 2


def test_parse_neighbors_skips_incomplete_duplicates():
    from src.parser.neighbor_parser import parse_neighbors

    snapshot = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "sample_outputs"
        / "lab_snapshot_20260721"
        / "SW1_neighbors.txt"
    )
    if not snapshot.exists():
        pytest.skip("Lab snapshot not available")
    neighbors = parse_neighbors(snapshot.read_text(encoding="utf-8"))
    assert neighbors
    assert all(item.local_interface for item in neighbors)
    pairs = {(item.local_interface, item.remote_device) for item in neighbors}
    assert len(pairs) == len(neighbors)


def test_build_network_state_from_snapshot(tmp_path: Path):
    snapshot = tmp_path / "current_test"
    snapshot.mkdir()
    for name in ["r1_ip_route.txt", "r1_interfaces.txt", "r1_arp.txt"]:
        (snapshot / name).write_text(
            (FIXTURES / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    (snapshot / "manifest.json").write_text(
        json.dumps({"devices": [{"hostname": "r1"}]}),
        encoding="utf-8",
    )

    state = build_network_state(snapshot)
    assert "r1" in state.devices
    assert len(state.devices["r1"].routes) >= 3
    assert len(state.devices["r1"].interfaces) == 3
