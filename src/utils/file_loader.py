"""Loads inventory, credentials, and snapshot files."""

import json
from pathlib import Path
from typing import Any

import yaml


def load_json(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def load_yaml(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_inventory(path: str | Path) -> list[dict[str, Any]]:
    data = load_json(path)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "devices" in data:
        devices = data["devices"]
        normalized = []
        for item in devices:
            normalized.append(
                {
                    "hostname": item.get("hostname") or item.get("name"),
                    "mgmt_ip": item.get("mgmt_ip") or item.get("host"),
                    "platform": item.get("platform") or item.get("device_type", "cisco_ios"),
                    "role": item.get("role", "router"),
                }
            )
        return normalized
    raise ValueError(f"Unsupported inventory format in {path}")


def load_credentials(path: str | Path) -> dict[str, str]:
    data = load_json(path)
    required = ["username", "password"]
    for key in required:
        if key not in data:
            raise ValueError(f"Credentials file missing required key: {key}")
    return {
        "username": str(data["username"]),
        "password": str(data["password"]),
        "secret": str(data.get("secret", "")),
    }


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")
