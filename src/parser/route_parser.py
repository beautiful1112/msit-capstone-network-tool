"""Parses show ip route output into structured route entries using TextFSM."""

from src.model.network_model import RouteEntry
from src.parser.base_parser import parse_prefix_and_mask
from src.parser.textfsm_engine import parse_with_textfsm

ROUTE_TEMPLATE = "cisco_ios_show_ip_route.textfsm"


def parse_routes(text: str, device: str | None = None) -> list[RouteEntry]:
    routes: list[RouteEntry] = []
    for row in parse_with_textfsm(ROUTE_TEMPLATE, text):
        protocol = row["PROTOCOL"]
        is_connected = protocol in {"C", "L"}
        if is_connected:
            if not row.get("NEXTHOP_IF"):
                continue
            routes.append(
                RouteEntry(
                    prefix=parse_prefix_and_mask(row["NETWORK"]),
                    protocol="connected",
                    next_hop=None,
                    out_interface=row["NEXTHOP_IF"],
                    metric=0,
                    administrative_distance=0,
                    is_connected=True,
                )
            )
            continue

        if not row.get("DISTANCE") or not row.get("METRIC"):
            continue

        routes.append(
            RouteEntry(
                prefix=parse_prefix_and_mask(row["NETWORK"]),
                protocol=protocol,
                next_hop=row.get("NEXTHOP_IP") or None,
                out_interface=row.get("NEXTHOP_IF") or None,
                metric=int(row["METRIC"]),
                administrative_distance=int(row["DISTANCE"]),
                is_connected=False,
            )
        )
    return routes
