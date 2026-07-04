"""Parses CDP/LLDP neighbour output."""

import re

from src.model.network_model import NeighborEntry
from src.parser.base_parser import normalize_interface_name

DEVICE_ID = re.compile(r"^Device ID:\s*(.+)$", re.IGNORECASE)
IP_ADDRESS = re.compile(r"^IP address:\s*(\d+\.\d+\.\d+\.\d+)", re.IGNORECASE)
LOCAL_INTF = re.compile(
    r"^Interface:\s*([^,]+),\s*Port ID \(outgoing port\):\s*(.+)$",
    re.IGNORECASE,
)


def parse_neighbors(text: str) -> list[NeighborEntry]:
    neighbors: list[NeighborEntry] = []
    current_device: str | None = None
    current_ip: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        device_match = DEVICE_ID.match(line)
        if device_match:
            current_device = device_match.group(1).split(".")[0].strip()
            current_ip = None
            continue

        ip_match = IP_ADDRESS.match(line)
        if ip_match:
            current_ip = ip_match.group(1)
            continue

        intf_match = LOCAL_INTF.match(line)
        if intf_match and current_device:
            neighbors.append(
                NeighborEntry(
                    local_interface=normalize_interface_name(intf_match.group(1).strip()),
                    remote_device=current_device,
                    remote_interface=normalize_interface_name(intf_match.group(2).strip()),
                    remote_ip=current_ip,
                )
            )

    return neighbors
