"""Snapshot discovery and loading helpers shared by Streamlit pages."""

from pathlib import Path

from src.model.network_model import NetworkState
from src.parser.normaliser import build_network_state
from src.utils.file_loader import load_json


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def discover_snapshots(root: Path | None = None) -> list[Path]:
    base_root = root or project_root()
    candidates: list[Path] = []
    for base in (base_root / "snapshots", base_root / "data" / "sample_outputs"):
        if not base.exists():
            continue
        for path in base.iterdir():
            if not path.is_dir():
                continue
            if list(path.glob("*_ip_route.txt")) or (path / "manifest.json").exists():
                candidates.append(path)
    return sorted(candidates, key=lambda item: item.name, reverse=True)


def load_network_state(snapshot_path: Path) -> NetworkState:
    json_path = snapshot_path / "network_state.json"
    if json_path.exists():
        return NetworkState.from_dict(load_json(json_path))
    return build_network_state(snapshot_path)
