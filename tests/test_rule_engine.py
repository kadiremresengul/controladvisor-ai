from pathlib import Path

from controladvisor.knowledge_base import load_default_method_knowledge_base
from controladvisor.reasoning import evaluate_problem_against_methods
from controladvisor.schemas.problem import load_problem_from_yaml


EXAMPLE_PROBLEM_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "example_problems"
    / "indoor_diff_drive_agv.yaml"
)


def evaluate_example_problem():
    problem = load_problem_from_yaml(EXAMPLE_PROBLEM_PATH)
    knowledge_base = load_default_method_knowledge_base()

    return evaluate_problem_against_methods(problem, knowledge_base)


def reason_text(reasons: list[str]) -> str:
    return " ".join(reasons).lower()


def test_indoor_agv_example_produces_expected_method_signals() -> None:
    result = evaluate_example_problem()

    expected_method_ids = {
        "graph_slam",
        "ekf_slam",
        "astar",
        "dwa",
        "mpc",
        "pid",
        "pure_pursuit",
    }

    assert expected_method_ids.issubset(set(result.candidate_method_ids()))


def test_astar_receives_navigation_positive_and_unknown_map_caution() -> None:
    astar_signal = evaluate_example_problem().get_signal("astar")

    assert "navigation" in reason_text(astar_signal.positive_reasons)
    assert "map is not known" in reason_text(astar_signal.caution_reasons)


def test_dwa_receives_dynamic_obstacle_or_collision_avoidance_positive() -> None:
    dwa_signal = evaluate_example_problem().get_signal("dwa")

    positives = reason_text(dwa_signal.positive_reasons)

    assert "dynamic obstacles" in positives or "collision avoidance" in positives


def test_mpc_receives_safety_or_constraint_positive() -> None:
    mpc_signal = evaluate_example_problem().get_signal("mpc")

    positives = reason_text(mpc_signal.positive_reasons)

    assert "safety" in positives or "constraint" in positives


def test_pid_receives_payload_transport_caution() -> None:
    pid_signal = evaluate_example_problem().get_signal("pid")

    assert "payload" in reason_text(pid_signal.caution_reasons)


def test_no_signal_is_created_for_unknown_method_ids() -> None:
    result = evaluate_example_problem()

    assert "amcl" not in result.candidate_method_ids()
    assert "unknown" not in result.candidate_method_ids()


def test_candidate_method_ids_are_deterministically_sorted() -> None:
    result = evaluate_example_problem()

    assert result.candidate_method_ids() == sorted(result.candidate_method_ids())
