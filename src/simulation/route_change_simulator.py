"""Applies static route changes to a copied network model."""

from src.model.network_model import RouteEntry, StaticRouteEntry
from src.simulation.model_copy import StaticRouteChange, find_device_key


def _is_static_route(route: RouteEntry) -> bool:
    protocol = (route.protocol or "").upper()
    return protocol in {"S", "STATIC"} or (
        route.administrative_distance == 1 and not route.is_connected
    )


def apply_static_route_change(
    network_state,
    change: StaticRouteChange,
) -> list[str]:
    """Apply one static-route change in-place. Returns warning messages."""
    warnings: list[str] = []
    device_key = find_device_key(network_state, change.device)
    if device_key is None:
        warnings.append(f"Device {change.device} not found; static route change skipped.")
        return warnings

    device = network_state.devices[device_key]
    prefix = change.prefix.strip()

    if change.action == "remove":
        before_routes = len(device.routes)
        device.routes = [
            route
            for route in device.routes
            if not (
                route.prefix == prefix
                and _is_static_route(route)
                and (change.next_hop is None or route.next_hop == change.next_hop)
            )
        ]
        device.static_routes = [
            entry
            for entry in device.static_routes
            if not (
                entry.prefix == prefix
                and (change.next_hop is None or entry.next_hop == change.next_hop)
            )
        ]
        if len(device.routes) == before_routes:
            warnings.append(
                f"No matching static route {prefix} found on {device_key} to remove."
            )
        return warnings

    if change.action == "modify":
        updated = False
        for route in device.routes:
            if route.prefix == prefix and _is_static_route(route):
                if change.next_hop is not None:
                    route.next_hop = change.next_hop
                if change.interface is not None:
                    route.out_interface = change.interface
                if change.administrative_distance is not None:
                    route.administrative_distance = change.administrative_distance
                updated = True
        for entry in device.static_routes:
            if entry.prefix == prefix:
                if change.next_hop is not None:
                    entry.next_hop = change.next_hop
                if change.interface is not None:
                    entry.interface = change.interface
                entry.administrative_distance = change.administrative_distance
                updated = True
        if not updated:
            warnings.append(
                f"No existing static route {prefix} on {device_key}; treating as add."
            )
            change = StaticRouteChange(
                device=change.device,
                action="add",
                prefix=prefix,
                next_hop=change.next_hop,
                interface=change.interface,
                administrative_distance=change.administrative_distance,
            )
        else:
            return warnings

    if change.action == "add":
        if not change.next_hop and not change.interface:
            warnings.append(
                f"Static route add on {device_key} requires next-hop or interface."
            )
            return warnings
        # Replace any existing static for the same prefix/next-hop to keep model clean.
        device.routes = [
            route
            for route in device.routes
            if not (
                route.prefix == prefix
                and _is_static_route(route)
                and (change.next_hop is None or route.next_hop == change.next_hop)
            )
        ]
        device.static_routes = [
            entry
            for entry in device.static_routes
            if not (
                entry.prefix == prefix
                and (change.next_hop is None or entry.next_hop == change.next_hop)
            )
        ]
        device.routes.append(
            RouteEntry(
                prefix=prefix,
                protocol="S",
                next_hop=change.next_hop,
                out_interface=change.interface,
                metric=0,
                administrative_distance=change.administrative_distance,
                is_connected=False,
            )
        )
        device.static_routes.append(
            StaticRouteEntry(
                prefix=prefix,
                next_hop=change.next_hop,
                interface=change.interface,
                administrative_distance=change.administrative_distance,
            )
        )

    return warnings
