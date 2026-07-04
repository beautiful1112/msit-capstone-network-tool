"""Parses show ip arp output."""

import re

from src.model.network_model import ArpEntry
from src.parser.base_parser import non_empty_lines, normalize_interface_name

ARP_LINE = re.compile(
    r"^(?:Internet\s+)?(\d+\.\d+\.\d+\.\d+)\s+[-\d]+\s+([0-9a-f\.]+)\s+(\S+)\s+(\S+)\s*$",
    re.IGNORECASE,
)


def parse_arp(text: str) -> list[ArpEntry]:
    entries: list[ArpEntry] = []
    for raw_line in non_empty_lines(text):
        line = raw_line.strip()
        if line.lower().startswith("protocol"):
            continue
        match = ARP_LINE.match(line)
        if not match:
            continue
        entries.append(
            ArpEntry(
                ip_address=match.group(1),
                mac_address=match.group(2),
                entry_type=match.group(3),
                interface=normalize_interface_name(match.group(4)),
            )
        )
    return entries
