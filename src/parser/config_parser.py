"""Parses running-config for static routes and OSPF interface costs using TextFSM."""

from src.model.network_model import OspfCostEntry, StaticRouteEntry
from src.parser.base_parser import normalize_interface_name
from src.parser.textfsm_engine import parse_with_textfsm

STATIC_ROUTE_TEMPLATE = "cisco_ios_running_config_static_route.textfsm"
OSPF_COST_TEMPLATE = "cisco_ios_running_config_ospf_cost.textfsm"


def _mask_to_prefix(ip: str, mask: str) -> str:
    octets = [int(x) for x in mask.split(".")]
    prefix_len = sum(bin(o).count("1") for o in octets)
    return f"{ip}/{prefix_len}"


def parse_config(text: str) -> tuple[list[StaticRouteEntry], list[OspfCostEntry]]:
    static_routes: list[StaticRouteEntry] = []
    for row in parse_with_textfsm(STATIC_ROUTE_TEMPLATE, text):
        prefix = _mask_to_prefix(row["NETWORK"], row["MASK"])
        next_hop = row["NEXTHOP"]
        distance = int(row["DISTANCE"]) if row.get("DISTANCE") else 1
        if _looks_like_ip(next_hop):
            static_routes.append(
                StaticRouteEntry(
                    prefix=prefix,
                    next_hop=next_hop,
                    administrative_distance=distance,
                )
            )
        else:
            static_routes.append(
                StaticRouteEntry(
                    prefix=prefix,
                    interface=normalize_interface_name(next_hop),
                    administrative_distance=distance,
                )
            )

    ospf_costs: list[OspfCostEntry] = []
    for row in parse_with_textfsm(OSPF_COST_TEMPLATE, text):
        ospf_costs.append(
            OspfCostEntry(
                interface=normalize_interface_name(row["INTERFACE"]),
                cost=int(row["COST"]),
            )
        )

    return static_routes, ospf_costs


def _looks_like_ip(value: str) -> bool:
    parts = value.split(".")
    return len(parts) == 4 and all(part.isdigit() for part in parts)
