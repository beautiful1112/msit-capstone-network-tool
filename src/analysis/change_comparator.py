"""Compares current and simulated post-change paths."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.analysis.path_analyzer import PathAnalysisResult


@dataclass
class PathComparisonResult:
    source_ip: str
    destination_ip: str
    current_path: list[str]
    simulated_path: list[str]
    current_reachable: bool
    simulated_reachable: bool
    path_changed: bool
    added_devices: list[str] = field(default_factory=list)
    removed_devices: list[str] = field(default_factory=list)
    summary: str = ""
    warnings: list[str] = field(default_factory=list)


def compare_paths(
    current: PathAnalysisResult,
    simulated: PathAnalysisResult,
    extra_warnings: list[str] | None = None,
) -> PathComparisonResult:
    """Diff current and simulated path analysis results."""
    current_path = list(current.path_devices)
    simulated_path = list(simulated.path_devices)
    current_set = set(current_path)
    simulated_set = set(simulated.path_devices)

    added = [device for device in simulated_path if device not in current_set]
    removed = [device for device in current_path if device not in simulated_set]
    changed = current_path != simulated_path or current.reachable != simulated.reachable

    if not current.reachable and not simulated.reachable:
        summary = "Destination remains unreachable before and after the planned change."
    elif current.reachable and not simulated.reachable:
        summary = "WARNING: Planned change may break reachability to the destination."
    elif not current.reachable and simulated.reachable:
        summary = "Planned change restores reachability to the destination."
    elif not changed:
        summary = "Planned change does not alter the selected forwarding path."
    else:
        summary = (
            f"Path changes from {' → '.join(current_path) or '(none)'} "
            f"to {' → '.join(simulated_path) or '(none)'}."
        )

    warnings = list(current.warnings) + list(simulated.warnings)
    if extra_warnings:
        warnings.extend(extra_warnings)

    if len(simulated_path) > len(current_path) and current.reachable and simulated.reachable:
        warnings.append("Simulated path is longer than the current path.")
    if removed and current.reachable and simulated.reachable:
        warnings.append(f"Devices removed from path: {', '.join(removed)}")
    if added and current.reachable and simulated.reachable:
        warnings.append(f"Devices added to path: {', '.join(added)}")

    return PathComparisonResult(
        source_ip=current.source_ip,
        destination_ip=current.destination_ip,
        current_path=current_path,
        simulated_path=simulated_path,
        current_reachable=current.reachable,
        simulated_reachable=simulated.reachable,
        path_changed=changed,
        added_devices=added,
        removed_devices=removed,
        summary=summary,
        warnings=warnings,
    )
