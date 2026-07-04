"""Per-platform operational command definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSpec:
    key: str
    command: str
    filename_suffix: str


CISCO_IOS_COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec("ip_route", "show ip route", "ip_route.txt"),
    CommandSpec("interfaces", "show ip interface brief", "interfaces.txt"),
    CommandSpec("arp", "show ip arp", "arp.txt"),
    CommandSpec("running_config", "show running-config", "running_config.txt"),
    CommandSpec("neighbors", "show cdp neighbors detail", "neighbors.txt"),
)


def get_command_profile(platform: str) -> tuple[CommandSpec, ...]:
    platform_key = platform.lower()
    if platform_key in {"cisco_ios", "cisco_xe", "cisco_ios_telnet"}:
        return CISCO_IOS_COMMANDS
    raise ValueError(f"Unsupported platform for command profile: {platform}")
