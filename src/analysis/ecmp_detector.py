"""Identifies equal-cost multipath route candidates."""

from src.model.network_model import RouteEntry


def group_ecmp_candidates(routes: list[RouteEntry]) -> list[RouteEntry]:
    """Return unique ECMP next-hops for routes that share prefix and metric."""
    if not routes:
        return []
    primary = routes[0]
    return [
        route
        for route in routes
        if route.prefix == primary.prefix
        and route.metric == primary.metric
        and route.administrative_distance == primary.administrative_distance
        and route.next_hop
    ]
