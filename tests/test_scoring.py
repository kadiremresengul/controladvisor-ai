from pathlib import Path

import pytest

from controladvisor.knowledge_base import load_default_method_knowledge_base
from controladvisor.reasoning import (
    RuleEngineResult,
    RuleSignal,
    ScoringResult,
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


def score_example_problem() -> ScoringResult:
    problem = load_problem_from_yaml(EXAMPLE_PROBLEM_PATH)
    knowledge_base = load_default_method_knowledge_base()
    rule_result = evaluate_problem_against_methods(problem, knowledge_base)

    return score_rule_engine_result(rule_result, knowledge_base)


def test_indoor_agv_example_produces_scored_methods() -> None:
    scoring_result = score_example_problem()

    assert scoring_result.scored_methods


def test_ranked_method_ids_are_sorted_by_descending_score() -> None:
    scoring_result = score_example_problem()
    ranked_ids = scoring_result.ranked_method_ids()
    expected_ids = [
        scored_method.method_id
        for scored_method in sorted(
            scoring_result.scored_methods,
            key=lambda scored_method: (-scored_method.score, scored_method.method_id),
        )
    ]

    assert ranked_ids == expected_ids


def test_top_methods_limit_returns_exactly_three_methods() -> None:
    scoring_result = score_example_problem()

    assert len(scoring_result.top_methods(limit=3)) == 3


def test_mpc_scores_above_baseline_for_indoor_agv_example() -> None:
    scoring_result = score_example_problem()

    assert scoring_result.get_scored_method("mpc").score > 50.0


def test_pid_keeps_positive_and_caution_reasons() -> None:
    scoring_result = score_example_problem()
    pid = scoring_result.get_scored_method("pid")

    assert pid.positive_reasons
    assert pid.caution_reasons


def test_get_scored_method_unknown_raises_key_error() -> None:
    scoring_result = score_example_problem()

    with pytest.raises(KeyError):
        scoring_result.get_scored_method("unknown")


def test_scores_are_clamped_between_zero_and_one_hundred() -> None:
    scoring_result = score_example_problem()

    assert all(0.0 <= method.score <= 100.0 for method in scoring_result.scored_methods)


def test_high_score_is_clamped_to_one_hundred() -> None:
    knowledge_base = load_default_method_knowledge_base()
    rule_result = RuleEngineResult(
        problem_id="high_score_problem",
        signals=[
            RuleSignal(
                method_id="mpc",
                positive_reasons=[f"positive reason {index}" for index in range(12)],
            )
        ],
    )

    mpc = score_rule_engine_result(rule_result, knowledge_base).get_scored_method("mpc")

    assert mpc.score == 100.0
    assert "Score clamped to 100.0" in mpc.scoring_notes


def test_low_score_is_clamped_to_zero() -> None:
    knowledge_base = load_default_method_knowledge_base()
    rule_result = RuleEngineResult(
        problem_id="low_score_problem",
        signals=[
            RuleSignal(
                method_id="pid",
                avoid_reasons=[f"avoid reason {index}" for index in range(8)],
            )
        ],
    )

    pid = score_rule_engine_result(rule_result, knowledge_base).get_scored_method("pid")

    assert pid.score == 0.0
    assert "Score clamped to 0.0" in pid.scoring_notes


def test_unknown_method_ids_in_rule_result_are_skipped_safely() -> None:
    knowledge_base = load_default_method_knowledge_base()
    rule_result = RuleEngineResult(
        problem_id="test_problem",
        signals=[
            RuleSignal(
                method_id="unknown_method",
                positive_reasons=["This method is intentionally missing."],
            ),
            RuleSignal(
                method_id="pid",
                positive_reasons=["Known method should still be scored."],
            ),
        ],
    )

    scoring_result = score_rule_engine_result(rule_result, knowledge_base)

    assert scoring_result.ranked_method_ids() == ["pid"]


def test_empty_rule_result_returns_empty_scoring_result() -> None:
    knowledge_base = load_default_method_knowledge_base()
    scoring_result = score_rule_engine_result(
        RuleEngineResult(problem_id="empty_problem"),
        knowledge_base,
    )

    assert scoring_result.problem_id == "empty_problem"
    assert scoring_result.scored_methods == []


def test_scoring_notes_include_formula_contributions() -> None:
    scoring_result = score_example_problem()
    mpc = scoring_result.get_scored_method("mpc")
    notes = " ".join(mpc.scoring_notes)

    assert "Base score: 50.0" in notes
    assert "Positive reasons:" in notes
    assert "Caution reasons:" in notes
