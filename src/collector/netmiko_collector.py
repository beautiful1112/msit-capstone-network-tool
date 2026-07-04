"""Orchestrates multi-device collection via Netmiko."""

from datetime import datetime, timezone
from typing import Any

from src.collector.command_profiles import get_command_profile
from src.collector.connection_manager import build_device_params, open_connection
from src.collector.snapshot_writer import SnapshotWriter
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)


def collect_live_state(
    inventory: list[dict[str, Any]],
    credentials: dict[str, str],
    snapshots_dir: str = "snapshots",
    timeout: int = 30,
) -> dict[str, Any]:
    writer = SnapshotWriter(snapshots_dir)
    started_at = datetime.now(timezone.utc).isoformat()
    device_results: list[dict[str, Any]] = []

    for device in inventory:
        hostname = device["hostname"]
        mgmt_ip = device["mgmt_ip"]
        platform = device.get("platform", "cisco_ios")
        result: dict[str, Any] = {
            "hostname": hostname,
            "mgmt_ip": mgmt_ip,
            "platform": platform,
            "status": "success",
            "commands": {},
            "errors": [],
        }

        try:
            command_profile = get_command_profile(platform)
        except ValueError as exc:
            result["status"] = "failed"
            result["errors"].append(str(exc))
            device_results.append(result)
            continue

        device_params = build_device_params(
            hostname=hostname,
            mgmt_ip=mgmt_ip,
            platform=platform,
            credentials=credentials,
            timeout=timeout,
        )

        try:
            with open_connection(device_params) as connection:
                for spec in command_profile:
                    try:
                        output = connection.send_command(
                            spec.command,
                            read_timeout=timeout,
                        )
                        output_path = writer.write_command_output(
                            hostname=hostname,
                            filename_suffix=spec.filename_suffix,
                            content=output,
                        )
                        result["commands"][spec.key] = {
                            "command": spec.command,
                            "file": str(output_path.name),
                            "status": "success",
                            "bytes": len(output.encode("utf-8")),
                        }
                    except Exception as exc:
                        logger.warning(
                            "Command '%s' failed on %s: %s",
                            spec.command,
                            hostname,
                            exc,
                        )
                        result["commands"][spec.key] = {
                            "command": spec.command,
                            "status": "failed",
                            "error": str(exc),
                        }
                        result["errors"].append(
                            f"{spec.command}: {exc}"
                        )
        except Exception as exc:
            logger.error("Collection failed for %s (%s): %s", hostname, mgmt_ip, exc)
            result["status"] = "failed"
            result["errors"].append(str(exc))

        if result["errors"] and result["status"] != "failed":
            result["status"] = "partial"

        device_results.append(result)

    completed_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "snapshot_id": writer.snapshot_id,
        "snapshot_path": str(writer.snapshot_path),
        "started_at": started_at,
        "completed_at": completed_at,
        "device_count": len(inventory),
        "devices": device_results,
    }
    writer.write_manifest(manifest)
    logger.info("Snapshot saved to %s", writer.snapshot_path)
    return manifest
