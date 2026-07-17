"""Orchestrates planned-change application on a copied network model."""

from __future__ import annotations

from src.model.network_model import NetworkState
from src.simulation.model_copy import (
    OspfCostChange,
    PlannedChange,
    StaticRouteChange,
    copy_network_state,
)
from src.simulation.ospf_cost_simulator import apply_ospf_cost_change
from src.simulation.route_change_simulator import apply_static_route_change


def apply_planned_changes(
    network_state: NetworkState,
    changes: list[PlannedChange],
    *,
    propagate_ospf_upstream: bool = True,
) -> tuple[NetworkState, list[str]]:
    """Deep-copy the model, apply all planned changes, return (copy, warnings)."""
    simulated = copy_network_state(network_state)
    warnings: list[str] = []

    if not changes:
        warnings.append("No planned changes were provided.")
        return simulated, warnings

    for change in changes:
        if isinstance(change, StaticRouteChange):
            warnings.extend(apply_static_route_change(simulated, change))
        elif isinstance(change, OspfCostChange):
            warnings.extend(
                apply_ospf_cost_change(
                    simulated,
                    change,
                    propagate_upstream=propagate_ospf_upstream,
                )
            )
        else:
            warnings.append(f"Unsupported planned change type: {type(change)!r}")

    return simulated, warnings
