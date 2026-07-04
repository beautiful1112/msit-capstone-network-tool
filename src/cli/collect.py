"""Command-line entry point for live collection and parsing."""

import argparse
import json
import sys
from pathlib import Path

from src.collector.netmiko_collector import collect_live_state
from src.parser.normaliser import build_network_state, save_network_state
from src.utils.file_loader import load_credentials, load_inventory
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect live network device state and parse CLI output."
    )
    parser.add_argument(
        "--inventory",
        default=str(PROJECT_ROOT / "data" / "inventory" / "inventory.json"),
        help="Path to device inventory JSON file",
    )
    parser.add_argument(
        "--credentials",
        default=str(PROJECT_ROOT / "data" / "credentials.json"),
        help="Path to SSH credentials JSON file",
    )
    parser.add_argument(
        "--snapshots-dir",
        default=str(PROJECT_ROOT / "snapshots"),
        help="Directory for timestamped snapshots",
    )
    parser.add_argument(
        "--parse-only",
        help="Parse an existing snapshot directory instead of collecting live data",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="SSH and command timeout in seconds",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.parse_only:
        snapshot_path = Path(args.parse_only)
        if not snapshot_path.exists():
            logger.error("Snapshot path does not exist: %s", snapshot_path)
            return 1
    else:
        inventory_path = Path(args.inventory)
        credentials_path = Path(args.credentials)
        if not inventory_path.exists():
            logger.error(
                "Inventory file not found: %s (copy inventory.example.json first)",
                inventory_path,
            )
            return 1
        if not credentials_path.exists():
            logger.error(
                "Credentials file not found: %s (copy credentials.example.json first)",
                credentials_path,
            )
            return 1

        inventory = load_inventory(inventory_path)
        credentials = load_credentials(credentials_path)
        manifest = collect_live_state(
            inventory=inventory,
            credentials=credentials,
            snapshots_dir=args.snapshots_dir,
            timeout=args.timeout,
        )
        snapshot_path = Path(manifest["snapshot_path"])
        print(json.dumps(manifest, indent=2))

    network_state = build_network_state(snapshot_path)
    output_path = save_network_state(
        network_state,
        snapshot_path / "network_state.json",
    )

    summary = {
        "snapshot_id": network_state.snapshot_id,
        "device_count": len(network_state.devices),
        "devices": {
            hostname: {
                "routes": len(device.routes),
                "interfaces": len(device.interfaces),
                "arp": len(device.arp),
                "neighbors": len(device.neighbors),
            }
            for hostname, device in network_state.devices.items()
        },
        "network_state_file": str(output_path),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
