"""Deep-copy helpers and planned-change dataclasses for simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.model.network_model import NetworkState


@dataclass
class StaticRouteChange:
    """Planned static route add / modify / remove on one device."""

    device: str
    action: Literal["add", "modify", "remove"]
    prefix: str
    next_hop: str | None = None
    interface: str | None = None
    administrative_distance: int = 1


@dataclass
class OspfCostChange:
    """Planned OSPF interface cost change on one device."""

    device: str
    interface: str
    new_cost: int


PlannedChange = StaticRouteChange | OspfCostChange


def copy_network_state(network_state: NetworkState) -> NetworkState:
    """Return an independent deep copy of the network model."""
    return NetworkState.from_dict(network_state.to_dict())


def find_device_key(network_state: NetworkState, hostname: str) -> str | None:
    """Resolve a hostname to the exact key used in NetworkState.devices."""
    target = hostname.split(".")[0].strip().upper()
    for key in network_state.devices:
        if key.split(".")[0].strip().upper() == target:
            return key
    return None
