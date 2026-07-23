#!/usr/bin/env python3
"""Measure collection duration and path-analysis latency for Week 6 evaluation.

Usage (from Capstone repo root, with venv active):

    python scripts/measure_performance.py
    python scripts/measure_performance.py --snapshot snapshots/current_20260721_142059
"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.path_analyzer import analyze_path
from src.utils.snapshot_utils import discover_snapshots, load_network_state


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def collection_duration_seconds(snapshot: Path) -> float | None:
    manifest_path = snapshot / "manifest.json"
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    started = manifest.get("started_at")
    completed = manifest.get("completed_at")
    if not started or not completed:
        return None
    return (_parse_iso(completed) - _parse_iso(started)).total_seconds()


def measure_path_latency(
    snapshot: Path,
    source_ip: str,
    destination_ip: str,
    repeats: int,
) -> dict:
    network_state = load_network_state(snapshot)
    samples: list[float] = []
    result = None
    for _ in range(repeats):
        started = time.perf_counter()
        result = analyze_path(network_state, source_ip, destination_ip)
        samples.append((time.perf_counter() - started) * 1000.0)
    assert result is not None
    return {
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "reachable": result.reachable,
        "path": " → ".join(result.path_devices),
        "warnings": result.warnings,
        "latency_ms_samples": [round(value, 3) for value in samples],
        "latency_ms_mean": round(statistics.mean(samples), 3),
        "latency_ms_stdev": round(statistics.pstdev(samples), 3) if len(samples) > 1 else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot",
        default="",
        help="Snapshot directory (default: newest under snapshots/ or sample_outputs/)",
    )
    parser.add_argument("--source", default="10.1.1.10")
    parser.add_argument("--destination", default="8.8.8.8")
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument(
        "--json-out",
        default="",
        help="Optional path to write JSON metrics",
    )
    args = parser.parse_args()

    if args.snapshot:
        snapshot = Path(args.snapshot)
        if not snapshot.is_absolute():
            snapshot = ROOT / snapshot
    else:
        found = discover_snapshots(ROOT)
        if not found:
            print("No snapshots found.", file=sys.stderr)
            return 1
        snapshot = found[0]

    if not snapshot.exists():
        print(f"Snapshot not found: {snapshot}", file=sys.stderr)
        return 1

    collection_s = collection_duration_seconds(snapshot)
    path_metrics = measure_path_latency(
        snapshot,
        args.source,
        args.destination,
        max(1, args.repeats),
    )

    network_state = load_network_state(snapshot)
    route_count = sum(len(device.routes) for device in network_state.devices.values())

    report = {
        "snapshot_id": snapshot.name,
        "snapshot_path": str(snapshot),
        "device_count": len(network_state.devices),
        "route_count": route_count,
        "collection_duration_seconds": collection_s,
        "path_analysis": path_metrics,
    }

    print("=== Performance metrics ===")
    print(f"Snapshot: {snapshot.name}")
    print(f"Devices: {report['device_count']}  Routes: {route_count}")
    if collection_s is not None:
        print(f"Collection duration: {collection_s:.3f} s")
    else:
        print("Collection duration: n/a (no manifest timestamps)")
    print(
        f"Path {args.source} -> {args.destination}: {path_metrics['path']} "
        f"(reachable={path_metrics['reachable']})"
    )
    print(
        f"Path analysis latency: mean={path_metrics['latency_ms_mean']} ms "
        f"stdev={path_metrics['latency_ms_stdev']} ms "
        f"(n={args.repeats})"
    )

    if args.json_out:
        out = Path(args.json_out)
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
