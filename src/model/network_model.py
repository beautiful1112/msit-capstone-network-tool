"""Network state domain models."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RouteEntry:
    prefix: str
    protocol: str
    next_hop: str | None = None
    out_interface: str | None = None
    metric: int | None = None
    administrative_distance: int | None = None
    is_connected: bool = False


@dataclass
class InterfaceEntry:
    interface: str
    ip_address: str | None = None
    prefix: str | None = None
    status: str | None = None
    protocol: str | None = None


@dataclass
class ArpEntry:
    ip_address: str
    mac_address: str | None = None
    interface: str | None = None
    entry_type: str | None = None


@dataclass
class StaticRouteEntry:
    prefix: str
    next_hop: str | None = None
    interface: str | None = None
    administrative_distance: int | None = None


@dataclass
class OspfCostEntry:
    interface: str
    cost: int


@dataclass
class NeighborEntry:
    local_interface: str
    remote_device: str
    remote_interface: str | None = None
    remote_ip: str | None = None


@dataclass
class DeviceState:
    hostname: str
    routes: list[RouteEntry] = field(default_factory=list)
    interfaces: list[InterfaceEntry] = field(default_factory=list)
    arp: list[ArpEntry] = field(default_factory=list)
    static_routes: list[StaticRouteEntry] = field(default_factory=list)
    ospf_costs: list[OspfCostEntry] = field(default_factory=list)
    neighbors: list[NeighborEntry] = field(default_factory=list)


@dataclass
class NetworkState:
    snapshot_id: str
    devices: dict[str, DeviceState] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NetworkState":
        devices: dict[str, DeviceState] = {}
        for hostname, payload in data.get("devices", {}).items():
            devices[hostname] = DeviceState(
                hostname=hostname,
                routes=[RouteEntry(**item) for item in payload.get("routes", [])],
                interfaces=[
                    InterfaceEntry(**item) for item in payload.get("interfaces", [])
                ],
                arp=[ArpEntry(**item) for item in payload.get("arp", [])],
                static_routes=[
                    StaticRouteEntry(**item)
                    for item in payload.get("static_routes", [])
                ],
                ospf_costs=[
                    OspfCostEntry(**item) for item in payload.get("ospf_costs", [])
                ],
                neighbors=[
                    NeighborEntry(**item) for item in payload.get("neighbors", [])
                ],
            )
        return cls(snapshot_id=data["snapshot_id"], devices=devices)
