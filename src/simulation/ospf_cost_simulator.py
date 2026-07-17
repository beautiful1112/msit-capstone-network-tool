"""Applies OSPF cost changes to a copied network model (approximate)."""

from src.analysis.next_hop_resolver import normalize_hostname, resolve_next_hop_device
from src.model.network_model import OspfCostEntry
from src.simulation.model_copy import OspfCostChange, find_device_key

DEFAULT_OSPF_COST = 1


def _normalize_iface(name: str) -> str:
    return name.strip().lower().replace(" ", "")


def _iface_matches(left: str | None, right: str) -> bool:
    if not left:
        return False
    return _normalize_iface(left) == _normalize_iface(right)


def _is_ospf_route(protocol: str | None) -> bool:
    value = (protocol or "").strip().upper()
    return value.startswith("O") or value == "OSPF"


def _current_cost(device, interface: str) -> int:
    for entry in device.ospf_costs:
        if _iface_matches(entry.interface, interface):
            return entry.cost
    return DEFAULT_OSPF_COST


def apply_ospf_cost_change(
    network_state,
    change: OspfCostChange,
    *,
    propagate_upstream: bool = True,
) -> list[str]:
    """Apply an OSPF cost change in-place and return warnings.

    Approximation (not full SPF):
    1. Record the new interface cost on the selected device.
    2. Adjust metrics of local OSPF routes that egress via that interface.
    3. Optionally add the same delta to OSPF routes on other devices whose
       next-hop resolves to this device (simplified upstream effect).
    """
    warnings: list[str] = [
        "OSPF cost simulation is an approximation; it does not run full SPF reconvergence."
    ]

    device_key = find_device_key(network_state, change.device)
    if device_key is None:
        warnings.append(f"Device {change.device} not found; OSPF cost change skipped.")
        return warnings

    if change.new_cost < 1:
        warnings.append("OSPF cost must be >= 1; change skipped.")
        return warnings

    device = network_state.devices[device_key]
    old_cost = _current_cost(device, change.interface)
    delta = change.new_cost - old_cost

    remaining = [
        entry
        for entry in device.ospf_costs
        if not _iface_matches(entry.interface, change.interface)
    ]
    remaining.append(OspfCostEntry(interface=change.interface, cost=change.new_cost))
    device.ospf_costs = remaining

    if delta == 0:
        warnings.append(
            f"OSPF cost on {device_key} {change.interface} unchanged ({old_cost})."
        )
        return warnings

    local_updated = 0
    for route in device.routes:
        if not _is_ospf_route(route.protocol):
            continue
        if not _iface_matches(route.out_interface, change.interface):
            continue
        if route.metric is None:
            route.metric = old_cost
        route.metric = max(1, route.metric + delta)
        local_updated += 1

    warnings.append(
        f"Updated {local_updated} local OSPF route metric(s) on {device_key} "
        f"({change.interface}: {old_cost} -> {change.new_cost}, delta={delta})."
    )

    if not propagate_upstream:
        return warnings

    target = normalize_hostname(device_key)
    upstream_updated = 0
    for hostname, other in network_state.devices.items():
        if normalize_hostname(hostname) == target:
            continue
        for route in other.routes:
            if not _is_ospf_route(route.protocol) or not route.next_hop:
                continue
            nexthop_device = resolve_next_hop_device(
                route.next_hop, hostname, network_state
            )
            if nexthop_device is None or normalize_hostname(nexthop_device) != target:
                continue
            if route.metric is None:
                route.metric = DEFAULT_OSPF_COST
            route.metric = max(1, route.metric + delta)
            upstream_updated += 1

    warnings.append(
        f"Propagated metric delta to {upstream_updated} upstream OSPF route(s) "
        f"that next-hop toward {device_key}."
    )
    return warnings
