"""Hop-by-hop path analysis using route table longest prefix match."""

from dataclasses import dataclass, field

from src.analysis.ecmp_detector import group_ecmp_candidates
from src.analysis.next_hop_resolver import (
    find_gateway_device,
    normalize_hostname,
    resolve_next_hop_device,
)
from src.model.network_model import NetworkState, RouteEntry
from src.utils.ip_utils import ip_in_prefix, longest_prefix_match

MAX_HOPS = 20


@dataclass
class PathHop:
    device: str
    matched_prefix: str
    route_protocol: str
    next_hop: str | None
    egress_interface: str | None
    next_device: str | None


@dataclass
class PathAnalysisResult:
    source_ip: str
    destination_ip: str
    path_devices: list[str] = field(default_factory=list)
    hops: list[PathHop] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    reachable: bool = False
    ecmp_alternatives: list[str] = field(default_factory=list)


def _select_routes(routes: list[RouteEntry]) -> tuple[RouteEntry, list[RouteEntry]]:
    if not routes:
        raise ValueError("No matching route")
    ecmp = group_ecmp_candidates(routes)
    primary = ecmp[0] if ecmp else routes[0]
    return primary, ecmp[1:] if len(ecmp) > 1 else []


def _is_destination_local(device: str, destination_ip: str, network_state: NetworkState) -> bool:
    device_state = network_state.devices.get(device)
    if device_state is None:
        return False
    for route in device_state.routes:
        if route.is_connected and ip_in_prefix(destination_ip, route.prefix):
            return True
    return False


def analyze_path(
    network_state: NetworkState,
    source_ip: str,
    destination_ip: str,
) -> PathAnalysisResult:
    result = PathAnalysisResult(source_ip=source_ip, destination_ip=destination_ip)

    start_device = find_gateway_device(source_ip, network_state)
    if start_device is None:
        result.warnings.append(
            f"No connected route found for source IP {source_ip} in the collected snapshot."
        )
        return result

    current_device = start_device
    visited: set[str] = set()

    for _ in range(MAX_HOPS):
        if current_device in visited:
            result.warnings.append(f"Routing loop detected at {current_device}.")
            break
        visited.add(current_device)

        device_state = network_state.devices.get(current_device)
        if device_state is None:
            result.warnings.append(f"Device {current_device} not found in network model.")
            break

        route_candidates = longest_prefix_match(
            destination_ip,
            [(route.prefix, route) for route in device_state.routes],
        )
        if not route_candidates:
            result.warnings.append(
                f"No route to {destination_ip} on {current_device}."
            )
            break

        primary_route, alt_routes = _select_routes(route_candidates)
        next_device = None

        if primary_route.is_connected and ip_in_prefix(destination_ip, primary_route.prefix):
            result.path_devices.append(current_device)
            result.hops.append(
                PathHop(
                    device=current_device,
                    matched_prefix=primary_route.prefix,
                    route_protocol="connected",
                    next_hop=None,
                    egress_interface=primary_route.out_interface,
                    next_device=None,
                )
            )
            result.reachable = True
            break

        if not primary_route.next_hop:
            result.warnings.append(
                f"Matched route on {current_device} has no next-hop for {destination_ip}."
            )
            break

        next_device = resolve_next_hop_device(
            primary_route.next_hop, current_device, network_state
        )
        if next_device is None:
            result.warnings.append(
                f"Could not resolve next-hop {primary_route.next_hop} from {current_device}."
            )
            result.path_devices.append(current_device)
            result.hops.append(
                PathHop(
                    device=current_device,
                    matched_prefix=primary_route.prefix,
                    route_protocol=primary_route.protocol,
                    next_hop=primary_route.next_hop,
                    egress_interface=primary_route.out_interface,
                    next_device=None,
                )
            )
            break

        result.path_devices.append(current_device)
        result.hops.append(
            PathHop(
                device=current_device,
                matched_prefix=primary_route.prefix,
                route_protocol=primary_route.protocol,
                next_hop=primary_route.next_hop,
                egress_interface=primary_route.out_interface,
                next_device=next_device,
            )
        )

        if alt_routes:
            alt_devices = []
            for alt in alt_routes:
                alt_dev = resolve_next_hop_device(
                    alt.next_hop or "", current_device, network_state
                )
                if alt_dev:
                    alt_devices.append(f"{current_device} -> {alt_dev} via {alt.next_hop}")
            if alt_devices:
                result.ecmp_alternatives.extend(alt_devices)
                result.warnings.append(
                    "ECMP detected; displaying primary path only. Alternatives: "
                    + "; ".join(alt_devices)
                )

        if _is_destination_local(next_device, destination_ip, network_state):
            result.path_devices.append(next_device)
            result.hops.append(
                PathHop(
                    device=next_device,
                    matched_prefix=destination_ip + "/32",
                    route_protocol="connected",
                    next_hop=None,
                    egress_interface=None,
                    next_device=None,
                )
            )
            result.reachable = True
            break

        current_device = normalize_hostname(next_device)
    else:
        result.warnings.append(
            f"Path analysis stopped after {MAX_HOPS} hops (possible loop or incomplete model)."
        )

    return result
