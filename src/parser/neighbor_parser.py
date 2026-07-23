"""Parses CDP/LLDP neighbour output using TextFSM."""

from src.model.network_model import NeighborEntry
from src.parser.base_parser import normalize_interface_name
from src.parser.textfsm_engine import parse_with_textfsm

NEIGHBOR_TEMPLATE = "cisco_ios_show_cdp_neighbors_detail.textfsm"


def parse_neighbors(text: str) -> list[NeighborEntry]:
    neighbors: list[NeighborEntry] = []
    seen: set[tuple[str, str, str]] = set()
    for row in parse_with_textfsm(NEIGHBOR_TEMPLATE, text):
        device_id = row["DEVICE_ID"].split(".")[0].strip()
        local_interface = normalize_interface_name(row["LOCAL_INTERFACE"].strip())
        remote_interface = normalize_interface_name(row["REMOTE_INTERFACE"].strip())
        remote_ip = row.get("IP_ADDRESS") or None
        # Skip incomplete CDP rows (empty local interface duplicates remote IP only).
        if not local_interface and not remote_interface:
            continue
        key = (local_interface, device_id.upper(), remote_interface)
        if key in seen:
            continue
        seen.add(key)
        neighbors.append(
            NeighborEntry(
                local_interface=local_interface,
                remote_device=device_id,
                remote_interface=remote_interface,
                remote_ip=remote_ip,
            )
        )
    return neighbors
