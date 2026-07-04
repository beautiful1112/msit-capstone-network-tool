"""Unifies parser outputs into a NetworkState schema."""

import json
from pathlib import Path

from src.model.network_model import DeviceState, NetworkState
from src.parser.arp_parser import parse_arp
from src.parser.config_parser import parse_config
from src.parser.interface_parser import parse_interfaces
from src.parser.neighbor_parser import parse_neighbors
from src.parser.route_parser import parse_routes
from src.utils.file_loader import read_text


def _find_device_file(snapshot_path: Path, hostname: str, suffix: str) -> Path | None:
    candidate = snapshot_path / f"{hostname}_{suffix}"
    if candidate.exists():
        return candidate
    matches = list(snapshot_path.glob(f"{hostname}_*{suffix.split('.')[0]}*"))
    return matches[0] if matches else None


def parse_device_snapshot(snapshot_path: Path, hostname: str) -> DeviceState:
    device = DeviceState(hostname=hostname)

    route_file = _find_device_file(snapshot_path, hostname, "ip_route.txt")
    if route_file:
        device.routes = parse_routes(read_text(route_file), device=hostname)

    interface_file = _find_device_file(snapshot_path, hostname, "interfaces.txt")
    if interface_file:
        device.interfaces = parse_interfaces(read_text(interface_file))

    arp_file = _find_device_file(snapshot_path, hostname, "arp.txt")
    if arp_file:
        device.arp = parse_arp(read_text(arp_file))

    config_file = _find_device_file(snapshot_path, hostname, "running_config.txt")
    if config_file:
        static_routes, ospf_costs = parse_config(read_text(config_file))
        device.static_routes = static_routes
        device.ospf_costs = ospf_costs

    neighbor_file = _find_device_file(snapshot_path, hostname, "neighbors.txt")
    if neighbor_file:
        device.neighbors = parse_neighbors(read_text(neighbor_file))

    return device


def discover_hostnames(snapshot_path: Path) -> list[str]:
    hostnames = set()
    for path in snapshot_path.glob("*_ip_route.txt"):
        hostnames.add(path.name.replace("_ip_route.txt", ""))
    if hostnames:
        return sorted(hostnames)

    manifest_path = snapshot_path / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(read_text(manifest_path))
        return sorted(
            item["hostname"] for item in manifest.get("devices", []) if "hostname" in item
        )
    return []


def build_network_state(snapshot_path: str | Path) -> NetworkState:
    path = Path(snapshot_path)
    snapshot_id = path.name
    network_state = NetworkState(snapshot_id=snapshot_id)

    for hostname in discover_hostnames(path):
        network_state.devices[hostname] = parse_device_snapshot(path, hostname)

    return network_state


def save_network_state(network_state: NetworkState, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.write_text(
        json.dumps(network_state.to_dict(), indent=2),
        encoding="utf-8",
    )
    return output
