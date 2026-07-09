"""Parses show ip interface brief output using TextFSM."""

from src.model.network_model import InterfaceEntry
from src.parser.base_parser import normalize_interface_name
from src.parser.textfsm_engine import parse_with_textfsm

INTERFACE_TEMPLATE = "cisco_ios_show_ip_interface_brief.textfsm"


def parse_interfaces(text: str) -> list[InterfaceEntry]:
    interfaces: list[InterfaceEntry] = []
    for row in parse_with_textfsm(INTERFACE_TEMPLATE, text):
        ip_address = row["IPADDR"]
        if ip_address == "unassigned":
            ip_address = None
        prefix = f"{ip_address}/32" if ip_address else None
        interfaces.append(
            InterfaceEntry(
                interface=normalize_interface_name(row["INTERFACE"]),
                ip_address=ip_address,
                prefix=prefix,
                status=row["STATUS"].lower(),
                protocol=row["PROTOCOL"].lower(),
            )
        )
    return interfaces
