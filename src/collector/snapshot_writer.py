"""Writes timestamped raw CLI output to snapshots/."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SnapshotWriter:
    def __init__(self, base_dir: str | Path = "snapshots") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.snapshot_id = f"current_{timestamp}"
        self.snapshot_path = self.base_dir / self.snapshot_id
        self.snapshot_path.mkdir(parents=True, exist_ok=True)

    def write_command_output(
        self,
        hostname: str,
        filename_suffix: str,
        content: str,
    ) -> Path:
        output_path = self.snapshot_path / f"{hostname}_{filename_suffix}"
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def write_manifest(self, manifest: dict[str, Any]) -> Path:
        manifest_path = self.snapshot_path / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
        return manifest_path
