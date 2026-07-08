"""Recommendation reasoning components."""

from controladvisor.reasoning.recommender import (
    ArchitectureRecommendation,
    ArchitectureSlot,
    build_architecture_recommendation,
)
from controladvisor.reasoning.rule_engine import (
    RuleEngineResult,
    RuleSignal,
    evaluate_problem_against_methods,
)
from controladvisor.reasoning.scoring import (
    ScoredMethod,
    ScoringResult,
    score_rule_engine_result,
)

__all__ = [
    "ArchitectureRecommendation",
    "ArchitectureSlot",
    "RuleEngineResult",
    "RuleSignal",
    "ScoredMethod",
    "ScoringResult",
    "build_architecture_recommendation",
    "evaluate_problem_against_methods",
    "score_rule_engine_result",
]
