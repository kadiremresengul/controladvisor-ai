from pathlib import Path

import pytest

from controladvisor.knowledge_base import load_default_method_knowledge_base
from controladvisor.reasoning import (
    ArchitectureRecommendation,
    build_architecture_recommendation,
    evaluate_problem_against_methods,
    score_rule_engine_result,
)
from controladvisor.schemas.problem import load_problem_from_yaml


EXAMPLE_PROBLEM_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "example_problems"
    / "indoor_diff_drive_agv.yaml"
)

EXPECTED_SLOT_NAMES = {
    "mapping_and_slam",
    "global_planning",
    "local_planning",
    "trajectory_tracking",
    "low_level_control",
    "optimal_or_constraint_control",
}


def recommend_example_problem() -> ArchitectureRecommendation:
    problem = load_problem_from_yaml(EXAMPLE_PROBLEM_PATH)
    knowledge_base = load_default_method_knowledge_base()
    rule_result = evaluate_problem_against_methods(problem, knowledge_base)
    scoring_result = score_rule_engine_result(rule_result, knowledge_base)

    return build_architecture_recommendation(scoring_result)


def test_indoor_agv_example_produces_architecture_recommendation() -> None:
    recommendation = recommend_example_problem()

    assert isinstance(recommendation, ArchitectureRecommendation)
    assert recommendation.problem_id == "indoor_diff_drive_agv_factory_mvp"
    assert recommendation.summary.startswith("Recommended architecture for")


def test_architecture_recommendation_contains_all_mvp_slots() -> None:
    recommendation = recommend_example_problem()

    assert {slot.slot_name for slot in recommendation.slots} == EXPECTED_SLOT_NAMES


def test_mapping_and_slam_slot_selects_slam_method() -> None:
    recommendation = recommend_example_problem()
    mapping_slot = recommendation.get_slot("mapping_and_slam")

    assert mapping_slot.selected_method_id in {"ekf_slam", "graph_slam"}
    assert mapping_slot.selected_method_name is not None


def test_global_planning_slot_selects_astar() -> None:
    recommendation = recommend_example_problem()

    assert recommendation.get_slot("global_planning").selected_method_id == "astar"


def test_local_planning_slot_selects_dwa() -> None:
    recommendation = recommend_example_problem()

    assert recommendation.get_slot("local_planning").selected_method_id == "dwa"


def test_low_level_control_slot_selects_pid() -> None:
    recommendation = recommend_example_problem()

    assert recommendation.get_slot("low_level_control").selected_method_id == "pid"


def test_optimal_or_constraint_control_slot_selects_mpc() -> None:
    recommendation = recommend_example_problem()

    assert (
        recommendation.get_slot("optimal_or_constraint_control").selected_method_id
        == "mpc"
    )


def test_selected_method_ids_returns_selected_non_null_method_ids() -> None:
    recommendation = recommend_example_problem()
    selected_method_ids = recommendation.selected_method_ids()

    assert selected_method_ids
    assert all(method_id is not None for method_id in selected_method_ids)
    assert "mpc" in selected_method_ids


def test_get_slot_global_planning_works() -> None:
    recommendation = recommend_example_problem()

    assert recommendation.get_slot("global_planning").slot_name == "global_planning"


def test_get_slot_unknown_raises_key_error() -> None:
    recommendation = recommend_example_problem()

    with pytest.raises(KeyError):
        recommendation.get_slot("unknown")


def test_warnings_are_present_for_selected_methods_with_cautions() -> None:
    recommendation = recommend_example_problem()

    assert recommendation.warnings
    assert any("caution" in warning.lower() for warning in recommendation.warnings)
