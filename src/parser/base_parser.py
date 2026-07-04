"""Shared parser utilities."""

import re
from typing import Iterable


def non_empty_lines(text: str) -> Iterable[str]:
    for line in text.splitlines():
        stripped = line.rstrip()
        if stripped.strip():
            yield stripped


def normalize_interface_name(name: str) -> str:
    replacements = {
        "Gi": "GigabitEthernet",
        "Fa": "FastEthernet",
        "Eth": "Ethernet",
        "Lo": "Loopback",
        "Vl": "Vlan",
        "Se": "Serial",
    }
    for short, long in replacements.items():
        if name.startswith(short) and not name.startswith(long):
            suffix = name[len(short) :]
            if suffix.isdigit() or "/" in suffix:
                return f"{long}{suffix}"
    return name


def parse_prefix_and_mask(token: str) -> str:
    if "/" in token:
        return token
    if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", token):
        return f"{token}/32"
    return token
