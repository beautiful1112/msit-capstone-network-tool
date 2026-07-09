"""IP address and subnet helper functions."""

import ipaddress


def ip_in_prefix(ip: str, prefix: str) -> bool:
    """Return True if ip belongs to prefix."""
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(prefix, strict=False)
    except ValueError:
        return False


def prefix_length(prefix: str) -> int:
    return ipaddress.ip_network(prefix, strict=False).prefixlen


def longest_prefix_match(
    target_ip: str, prefixes: list[tuple[str, object]]
) -> list[object]:
    """Return all entries whose prefix is the longest match for target_ip.

    Each item in prefixes is (prefix_string, payload_object).
    Multiple entries with the same longest prefix are returned (ECMP candidates).
    """
    target = ipaddress.ip_address(target_ip)
    best_len = -1
    matches: list[object] = []

    for prefix, payload in prefixes:
        try:
            network = ipaddress.ip_network(prefix, strict=False)
        except ValueError:
            continue
        if target not in network:
            continue
        plen = network.prefixlen
        if plen > best_len:
            best_len = plen
            matches = [payload]
        elif plen == best_len:
            matches.append(payload)

    return matches
