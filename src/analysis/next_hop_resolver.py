"""Maps next-hop IP addresses to neighbour devices."""

from src.model.network_model import NetworkState
from src.utils.ip_utils import ip_in_prefix, prefix_length


def normalize_hostname(name: str) -> str:
    return name.split(".")[0].strip().upper()


def resolve_next_hop_device(
    next_hop_ip: str,
    current_device: str,
    network_state: NetworkState,
) -> str | None:
    """Resolve a next-hop IP to a device hostname in the model."""
    current = network_state.devices.get(current_device)
    if current is None:
        return None

    for neighbor in current.neighbors:
        if neighbor.remote_ip == next_hop_ip and neighbor.remote_device:
            return normalize_hostname(neighbor.remote_device)

    for hostname, device in network_state.devices.items():
        for interface in device.interfaces:
            if interface.ip_address == next_hop_ip:
                return normalize_hostname(hostname)

    for arp_entry in current.arp:
        if arp_entry.ip_address != next_hop_ip:
            continue
        for hostname, device in network_state.devices.items():
            if hostname == current_device:
                continue
            for interface in device.interfaces:
                if (
                    interface.ip_address
                    and interface.prefix
                    and ip_in_prefix(next_hop_ip, interface.prefix)
                ):
                    return normalize_hostname(hostname)

    return None


def find_gateway_device(source_ip: str, network_state: NetworkState) -> str | None:
    """Find the device that owns the source IP subnet (first routing hop)."""
    best_match: tuple[int, str] | None = None
    for hostname, device in network_state.devices.items():
        for route in device.routes:
            if not route.is_connected:
                continue
            if not ip_in_prefix(source_ip, route.prefix):
                continue
            plen = prefix_length(route.prefix)
            if best_match is None or plen > best_match[0]:
                best_match = (plen, normalize_hostname(hostname))
    return best_match[1] if best_match else None
