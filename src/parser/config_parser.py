"""Parses running-config for static routes and OSPF interface costs."""

import re

from src.model.network_model import OspfCostEntry, StaticRouteEntry
from src.parser.base_parser import normalize_interface_name

STATIC_ROUTE = re.compile(
    r"^ip route\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)(?:\s+(\d+))?",
    re.IGNORECASE,
)
STATIC_ROUTE_INTF = re.compile(
    r"^ip route\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)\s+(\S+)(?:\s+(\d+))?",
    re.IGNORECASE,
)
OSPF_COST = re.compile(r"^\s*ip ospf cost\s+(\d+)\s*$", re.IGNORECASE)


def _mask_to_prefix(ip: str, mask: str) -> str:
    octets = [int(x) for x in mask.split(".")]
    prefix_len = sum(bin(o).count("1") for o in octets)
    return f"{ip}/{prefix_len}"


def parse_config(text: str) -> tuple[list[StaticRouteEntry], list[OspfCostEntry]]:
    static_routes: list[StaticRouteEntry] = []
    ospf_costs: list[OspfCostEntry] = []
    current_interface: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("!"):
            continue

        if stripped.startswith("interface "):
            current_interface = normalize_interface_name(stripped.split()[1])
            continue

        if current_interface:
            cost_match = OSPF_COST.match(line)
            if cost_match:
                ospf_costs.append(
                    OspfCostEntry(
                        interface=current_interface,
                        cost=int(cost_match.group(1)),
                    )
                )

        route_match = STATIC_ROUTE.match(stripped)
        if route_match:
            prefix = _mask_to_prefix(route_match.group(1), route_match.group(2))
            static_routes.append(
                StaticRouteEntry(
                    prefix=prefix,
                    next_hop=route_match.group(3),
                    administrative_distance=int(route_match.group(4))
                    if route_match.group(4)
                    else 1,
                )
            )
            continue

        route_intf_match = STATIC_ROUTE_INTF.match(stripped)
        if route_intf_match and not route_match:
            prefix = _mask_to_prefix(route_intf_match.group(1), route_intf_match.group(2))
            next_hop_or_intf = route_intf_match.group(3)
            if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", next_hop_or_intf):
                static_routes.append(
                    StaticRouteEntry(
                        prefix=prefix,
                        next_hop=next_hop_or_intf,
                        administrative_distance=int(route_intf_match.group(4))
                        if route_intf_match.group(4)
                        else 1,
                    )
                )
            else:
                static_routes.append(
                    StaticRouteEntry(
                        prefix=prefix,
                        interface=normalize_interface_name(next_hop_or_intf),
                        administrative_distance=int(route_intf_match.group(4))
                        if route_intf_match.group(4)
                        else 1,
                    )
                )

    return static_routes, ospf_costs
