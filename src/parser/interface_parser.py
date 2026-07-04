"""Parses show ip interface brief output."""

import re

from src.model.network_model import InterfaceEntry
from src.parser.base_parser import non_empty_lines, normalize_interface_name

INTERFACE_LINE = re.compile(
    r"^(\S+)\s+(\d+\.\d+\.\d+\.\d+|unassigned)\s+\S+\s+\S+\s+(\S+)\s+(\S+)\s*$"
)


def parse_interfaces(text: str) -> list[InterfaceEntry]:
    interfaces: list[InterfaceEntry] = []
    for raw_line in non_empty_lines(text):
        line = raw_line.strip()
        if line.lower().startswith("interface"):
            continue
        match = INTERFACE_LINE.match(line)
        if not match:
            continue
        name = normalize_interface_name(match.group(1))
        ip_address = None if match.group(2) == "unassigned" else match.group(2)
        prefix = f"{ip_address}/32" if ip_address else None
        interfaces.append(
            InterfaceEntry(
                interface=name,
                ip_address=ip_address,
                prefix=prefix,
                status=match.group(3).lower(),
                protocol=match.group(4).lower(),
            )
        )
    return interfaces
