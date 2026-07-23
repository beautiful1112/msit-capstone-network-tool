"""Formats analysis results for JSON and Markdown export."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from src.analysis.change_comparator import PathComparisonResult
from src.analysis.path_analyzer import PathAnalysisResult, PathHop


def _hop_dict(hop: PathHop) -> dict[str, Any]:
    return {
        "device": hop.device,
        "matched_prefix": hop.matched_prefix,
        "protocol": hop.route_protocol,
        "next_hop": hop.next_hop,
        "egress_interface": hop.egress_interface,
        "next_device": hop.next_device,
    }


def path_result_to_dict(result: PathAnalysisResult) -> dict[str, Any]:
    return {
        "source_ip": result.source_ip,
        "destination_ip": result.destination_ip,
        "reachable": result.reachable,
        "path_devices": list(result.path_devices),
        "path": " → ".join(result.path_devices) if result.path_devices else "",
        "hops": [_hop_dict(hop) for hop in result.hops],
        "ecmp_alternatives": list(result.ecmp_alternatives),
        "warnings": list(result.warnings),
    }


def comparison_to_dict(comparison: PathComparisonResult) -> dict[str, Any]:
    return {
        "source_ip": comparison.source_ip,
        "destination_ip": comparison.destination_ip,
        "current_path": list(comparison.current_path),
        "simulated_path": list(comparison.simulated_path),
        "current_reachable": comparison.current_reachable,
        "simulated_reachable": comparison.simulated_reachable,
        "path_changed": comparison.path_changed,
        "added_devices": list(comparison.added_devices),
        "removed_devices": list(comparison.removed_devices),
        "summary": comparison.summary,
        "warnings": list(comparison.warnings),
    }


def build_export_payload(
    *,
    snapshot_id: str | None = None,
    current: PathAnalysisResult | None = None,
    simulated: PathAnalysisResult | None = None,
    comparison: PathComparisonResult | None = None,
    planned_change_notes: list[str] | None = None,
) -> dict[str, Any]:
    """Build a structured diagnostic report for JSON export."""
    payload: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "snapshot_id": snapshot_id,
        "tool": "msit-capstone-network-tool",
        "limitations": [
            "Post-change results are simulations on a copied model; nothing is pushed to devices.",
            "OSPF cost simulation is an approximation and does not run full SPF reconvergence.",
            "ECMP hashing behaviour is not simulated.",
        ],
    }
    if planned_change_notes:
        payload["planned_change_notes"] = list(planned_change_notes)
    if current is not None:
        payload["current_path_analysis"] = path_result_to_dict(current)
    if simulated is not None:
        payload["simulated_path_analysis"] = path_result_to_dict(simulated)
    if comparison is not None:
        payload["comparison"] = comparison_to_dict(comparison)
    return payload


def render_json_report(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2)


def render_markdown_report(payload: dict[str, Any]) -> str:
    """Render a human-readable Markdown diagnostic report."""
    lines: list[str] = [
        "# Path Analysis and Change Impact Report",
        "",
        f"- Generated (UTC): `{payload.get('generated_at', '')}`",
        f"- Snapshot: `{payload.get('snapshot_id') or 'n/a'}`",
        "",
    ]

    current = payload.get("current_path_analysis")
    if current:
        lines.extend(
            [
                "## Current Path Analysis",
                "",
                f"- Source: `{current.get('source_ip')}`",
                f"- Destination: `{current.get('destination_ip')}`",
                f"- Reachable: **{'Yes' if current.get('reachable') else 'No'}**",
                f"- Path: `{current.get('path') or '(none)'}`",
                "",
            ]
        )
        hops = current.get("hops") or []
        if hops:
            lines.append("| Hop | Device | Prefix | Protocol | Next Hop | Egress |")
            lines.append("| --- | --- | --- | --- | --- | --- |")
            for index, hop in enumerate(hops, start=1):
                lines.append(
                    f"| {index} | {hop.get('device')} | {hop.get('matched_prefix')} | "
                    f"{hop.get('protocol')} | {hop.get('next_hop') or ''} | "
                    f"{hop.get('egress_interface') or ''} |"
                )
            lines.append("")
        warnings = current.get("warnings") or []
        if warnings:
            lines.append("### Warnings")
            lines.append("")
            for warning in warnings:
                lines.append(f"- {warning}")
            lines.append("")

    simulated = payload.get("simulated_path_analysis")
    if simulated:
        lines.extend(
            [
                "## Simulated Post-Change Path",
                "",
                f"- Reachable: **{'Yes' if simulated.get('reachable') else 'No'}**",
                f"- Path: `{simulated.get('path') or '(none)'}`",
                "",
            ]
        )

    comparison = payload.get("comparison")
    if comparison:
        lines.extend(
            [
                "## Change Impact Comparison",
                "",
                f"- Summary: {comparison.get('summary')}",
                f"- Path changed: **{'Yes' if comparison.get('path_changed') else 'No'}**",
                f"- Current: `{' → '.join(comparison.get('current_path') or []) or '(none)'}`",
                f"- Simulated: `{' → '.join(comparison.get('simulated_path') or []) or '(none)'}`",
                "",
            ]
        )
        if comparison.get("added_devices"):
            lines.append(f"- Devices added: {', '.join(comparison['added_devices'])}")
        if comparison.get("removed_devices"):
            lines.append(f"- Devices removed: {', '.join(comparison['removed_devices'])}")
        lines.append("")
        warnings = comparison.get("warnings") or []
        if warnings:
            lines.append("### Comparison warnings")
            lines.append("")
            for warning in warnings:
                lines.append(f"- {warning}")
            lines.append("")

    notes = payload.get("planned_change_notes") or []
    if notes:
        lines.append("## Planned change notes")
        lines.append("")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")

    limitations = payload.get("limitations") or []
    if limitations:
        lines.append("## Limitations")
        lines.append("")
        for item in limitations:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)
