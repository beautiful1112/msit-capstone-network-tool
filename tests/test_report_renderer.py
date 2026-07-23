"""Unit tests for diagnostic report export helpers."""

from src.analysis.change_comparator import compare_paths
from src.analysis.path_analyzer import PathAnalysisResult, PathHop
from src.visualization.report_renderer import (
    build_export_payload,
    render_json_report,
    render_markdown_report,
)


def _sample_result(path: list[str], reachable: bool = True) -> PathAnalysisResult:
    hops = [
        PathHop(
            device=device,
            matched_prefix="8.8.8.8/32",
            route_protocol="O",
            next_hop="10.0.0.1" if index < len(path) - 1 else None,
            egress_interface="GigabitEthernet0/0",
            next_device=path[index + 1] if index < len(path) - 1 else None,
        )
        for index, device in enumerate(path)
    ]
    return PathAnalysisResult(
        source_ip="10.1.1.10",
        destination_ip="8.8.8.8",
        path_devices=path,
        hops=hops,
        warnings=[],
        reachable=reachable,
    )


def test_export_json_and_markdown_include_paths():
    current = _sample_result(["SW1", "R2", "R3"])
    simulated = _sample_result(["SW1", "R1", "R3"])
    comparison = compare_paths(current, simulated)
    payload = build_export_payload(
        snapshot_id="lab_snapshot_20260721",
        current=current,
        simulated=simulated,
        comparison=comparison,
        planned_change_notes=["Static add on SW1"],
    )
    json_text = render_json_report(payload)
    md_text = render_markdown_report(payload)
    assert "SW1" in json_text and "R1" in json_text
    assert "Current Path Analysis" in md_text
    assert "Change Impact Comparison" in md_text
    assert "lab_snapshot_20260721" in md_text
