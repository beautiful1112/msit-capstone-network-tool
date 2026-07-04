"""Parses show ip route output into structured route entries."""

import re

from src.model.network_model import RouteEntry
from src.parser.base_parser import non_empty_lines, parse_prefix_and_mask

ROUTE_VIA = re.compile(
    r"^([A-Z\*]{1,3})\s+(\S+)\s+\[(\d+)/(\d+)\]\s+via\s+(\S+)(?:,.*,\s+(\S+))?\s*$"
)
ROUTE_CONNECTED = re.compile(
    r"^C\s+(\S+)\s+is directly connected,\s+(\S+)\s*$"
)
ROUTE_LOCAL = re.compile(
    r"^L\s+(\S+)\s+is directly connected,\s+(\S+)\s*$"
)
ROUTE_VIA_SHORT = re.compile(
    r"^([A-Z\*]{1,3})\s+(\S+)\s+\[(\d+)/(\d+)\]\s+via\s+(\S+)\s*$"
)


def parse_routes(text: str, device: str | None = None) -> list[RouteEntry]:
    routes: list[RouteEntry] = []
    for raw_line in non_empty_lines(text):
        line = raw_line.strip()
        if line.startswith("Codes:") or line.startswith("Gateway"):
            continue
        if "subnetted" in line or line.endswith("masks"):
            continue

        connected = ROUTE_CONNECTED.match(line) or ROUTE_LOCAL.match(line)
        if connected:
            prefix = parse_prefix_and_mask(connected.group(1))
            routes.append(
                RouteEntry(
                    prefix=prefix,
                    protocol="connected",
                    next_hop=None,
                    out_interface=connected.group(2),
                    metric=0,
                    administrative_distance=0,
                    is_connected=True,
                )
            )
            continue

        via_match = ROUTE_VIA.match(line) or ROUTE_VIA_SHORT.match(line)
        if via_match:
            protocol = via_match.group(1).strip()
            prefix = parse_prefix_and_mask(via_match.group(2))
            admin_distance = int(via_match.group(3))
            metric = int(via_match.group(4))
            next_hop = via_match.group(5)
            out_interface = via_match.group(6) if via_match.lastindex >= 6 else None
            routes.append(
                RouteEntry(
                    prefix=prefix,
                    protocol=protocol,
                    next_hop=next_hop,
                    out_interface=out_interface,
                    metric=metric,
                    administrative_distance=admin_distance,
                    is_connected=False,
                )
            )
    return routes
