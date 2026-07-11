from pathlib import Path

import pytest

from src.analysis.path_analyzer import analyze_path
from src.parser.normaliser import build_network_state

LAB_SNAPSHOT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sample_outputs"
    / "lab_snapshot_20260707"
)


@pytest.fixture
def lab_state():
    if not (LAB_SNAPSHOT / "SW1_ip_route.txt").exists():
        pytest.skip("Lab snapshot not available")
    return build_network_state(LAB_SNAPSHOT)


def test_path_pc1_to_r3_loopback(lab_state):
    result = analyze_path(lab_state, "10.1.1.10", "8.8.8.8")
    assert result.reachable
    assert result.path_devices[0] == "SW1"
    assert result.path_devices[-1] == "R3"
    assert result.path_devices[1] in {"R1", "R2"}
    assert len(result.path_devices) == 3


def test_path_unknown_source(lab_state):
    result = analyze_path(lab_state, "192.0.2.50", "8.8.8.8")
    assert not result.reachable
    assert result.warnings
