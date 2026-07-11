"""Parses show ip arp output using TextFSM."""

from src.model.network_model import ArpEntry
from src.parser.base_parser import normalize_interface_name
from src.parser.textfsm_engine import parse_with_textfsm

ARP_TEMPLATE = "cisco_ios_show_ip_arp.textfsm"


def parse_arp(text: str) -> list[ArpEntry]:
    entries: list[ArpEntry] = []
    for row in parse_with_textfsm(ARP_TEMPLATE, text):
        entries.append(
            ArpEntry(
                ip_address=row["IP"],
                mac_address=row["MAC"],
                entry_type=row["TYPE"],
                interface=normalize_interface_name(row["INTERFACE"]),
            )
        )
    return entries
