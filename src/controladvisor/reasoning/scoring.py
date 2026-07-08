"""Scoring utilities for rule-engine recommendation signals."""

from pydantic import BaseModel, ConfigDict, Field

from controladvisor.knowledge_base import MethodCardKnowledgeBase
from controladvisor.reasoning.rule_engine import RuleEngineResult
from controladvisor.schemas.method_card import MethodCategory


BASE_SCORE = 50.0
POSITIVE_REASON_WEIGHT = 8.0
CAUTION_REASON_WEIGHT = -4.0
AVOID_REASON_WEIGHT = -15.0
METHOD_STRENGTH_WEIGHT = 2.0
METHOD_LIMITATION_WEIGHT = -1.5


class ScoredMethod(BaseModel):
    """Numeric suitability score for one method candidate."""

    model_config = ConfigDict(extra="forbid")

    method_id: str
    name: str
    category: MethodCategory
    score: float
    positive_reasons: list[str] = Field(default_factory=list)
    caution_reasons: list[str] = Field(default_factory=list)
    avoid_reasons: list[str] = Field(default_factory=list)
    scoring_notes: list[str] = Field(default_factory=list)


class ScoringResult(BaseModel):
    """Scored methods for one problem definition."""

    model_config = ConfigDict(extra="forbid")

    problem_id: str
    scored_methods: list[ScoredMethod] = Field(default_factory=list)

    def get_scored_method(self, method_id: str) -> ScoredMethod:
        """Return a scored method by ID."""

        for scored_method in self.scored_methods:
            if scored_method.method_id == method_id:
                return scored_method

        raise KeyError(f"Unknown scored method ID: {method_id}")

    def ranked_method_ids(self) -> list[str]:
        """Return method IDs in ranked order."""

        return [scored_method.method_id for scored_method in self.scored_methods]

    def top_methods(self, limit: int = 5) -> list[ScoredMethod]:
        """Return the top ranked methods up to a limit."""

        return self.scored_methods[: max(0, limit)]


def score_rule_engine_result(
    rule_result: RuleEngineResult,
    knowledge_base: MethodCardKnowledgeBase,
) -> ScoringResult:
    """Convert rule-engine signals into deterministic numeric scores."""

    scored_methods: list[ScoredMethod] = []

    for signal in rule_result.signals:
        if not knowledge_base.has_method(signal.method_id):
            continue

        method_card = knowledge_base.get_method(signal.method_id)
        positive_count = len(signal.positive_reasons)
        caution_count = len(signal.caution_reasons)
        avoid_count = len(signal.avoid_reasons)
        strength_count = len(method_card.strengths)
        limitation_count = len(method_card.limitations)

        raw_score = (
            BASE_SCORE
            + positive_count * POSITIVE_REASON_WEIGHT
            + caution_count * CAUTION_REASON_WEIGHT
            + avoid_count * AVOID_REASON_WEIGHT
            + strength_count * METHOD_STRENGTH_WEIGHT
            + limitation_count * METHOD_LIMITATION_WEIGHT
        )
        clamped_score = min(100.0, max(0.0, raw_score))
        scoring_notes = [
            f"Base score: {BASE_SCORE}",
            f"Positive reasons: {positive_count} x +{POSITIVE_REASON_WEIGHT}",
            f"Caution reasons: {caution_count} x {CAUTION_REASON_WEIGHT}",
            f"Avoid reasons: {avoid_count} x {AVOID_REASON_WEIGHT}",
            f"Method strengths: {strength_count} x +{METHOD_STRENGTH_WEIGHT}",
            f"Method limitations: {limitation_count} x {METHOD_LIMITATION_WEIGHT}",
        ]

        if clamped_score == 100.0 and raw_score > 100.0:
            scoring_notes.append("Score clamped to 100.0")
        if clamped_score == 0.0 and raw_score < 0.0:
            scoring_notes.append("Score clamped to 0.0")

        scored_methods.append(
            ScoredMethod(
                method_id=method_card.id,
                name=method_card.name,
                category=method_card.category,
                score=round(clamped_score, 2),
                positive_reasons=list(signal.positive_reasons),
                caution_reasons=list(signal.caution_reasons),
                avoid_reasons=list(signal.avoid_reasons),
                scoring_notes=scoring_notes,
            )
        )

    return ScoringResult(
        problem_id=rule_result.problem_id,
        scored_methods=sorted(
            scored_methods,
            key=lambda scored_method: (-scored_method.score, scored_method.method_id),
        ),
    )
