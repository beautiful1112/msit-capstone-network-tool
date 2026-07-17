from pathlib import Path

import pytest

from src.analysis.change_comparator import compare_paths
from src.analysis.path_analyzer import analyze_path
from src.parser.normaliser import build_network_state
from src.simulation import apply_planned_changes
from src.simulation.model_copy import OspfCostChange, StaticRouteChange

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


def test_static_route_add_changes_path_toward_r1(lab_state):
    current = analyze_path(lab_state, "10.1.1.10", "8.8.8.8")
    assert current.reachable

    simulated_state, warnings = apply_planned_changes(
        lab_state,
        [
            StaticRouteChange(
                device="SW1",
                action="add",
                prefix="8.8.8.8/32",
                next_hop="10.0.11.2",
            )
        ],
    )
    assert not any("skipped" in item.lower() for item in warnings)

    simulated = analyze_path(simulated_state, "10.1.1.10", "8.8.8.8")
    assert simulated.reachable
    assert simulated.path_devices[0] == "SW1"
    assert simulated.path_devices[1] == "R1"
    assert simulated.path_devices[-1] == "R3"

    comparison = compare_paths(current, simulated)
    assert comparison.path_changed or current.path_devices[1] == "R1"


def test_static_route_remove_after_add(lab_state):
    added, _ = apply_planned_changes(
        lab_state,
        [
            StaticRouteChange(
                device="SW1",
                action="add",
                prefix="8.8.8.8/32",
                next_hop="10.0.11.2",
            )
        ],
    )
    removed, warnings = apply_planned_changes(
        added,
        [
            StaticRouteChange(
                device="SW1",
                action="remove",
                prefix="8.8.8.8/32",
                next_hop="10.0.11.2",
            )
        ],
    )
    static_left = [
        route
        for route in removed.devices["SW1"].routes
        if route.prefix == "8.8.8.8/32" and (route.protocol or "").upper().startswith("S")
    ]
    assert static_left == []
    assert not any("skipped" in item.lower() for item in warnings)


def test_ospf_cost_increase_prefers_other_ecmp(lab_state):
    # Raise cost on SW1 interface facing R2 so ECMP should prefer R1.
    simulated_state, warnings = apply_planned_changes(
        lab_state,
        [
            OspfCostChange(
                device="SW1",
                interface="GigabitEthernet0/3",
                new_cost=100,
            )
        ],
        propagate_ospf_upstream=False,
    )
    assert any("Updated" in item for item in warnings)

    simulated = analyze_path(simulated_state, "10.1.1.10", "8.8.8.8")
    assert simulated.reachable
    assert simulated.path_devices[1] == "R1"


def test_original_state_unchanged_after_simulation(lab_state):
    before = [
        (route.next_hop, route.metric)
        for route in lab_state.devices["SW1"].routes
        if route.prefix == "8.8.8.8/32"
    ]
    apply_planned_changes(
        lab_state,
        [
            StaticRouteChange(
                device="SW1",
                action="add",
                prefix="8.8.8.8/32",
                next_hop="10.0.11.2",
            )
        ],
    )
    after = [
        (route.next_hop, route.metric)
        for route in lab_state.devices["SW1"].routes
        if route.prefix == "8.8.8.8/32"
    ]
    assert before == after
