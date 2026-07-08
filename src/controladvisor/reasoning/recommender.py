"""Architecture recommendation layer built from scored methods."""

from pydantic import BaseModel, ConfigDict, Field

from controladvisor.reasoning.scoring import ScoredMethod, ScoringResult
from controladvisor.schemas.method_card import MethodCategory


SLOT_ORDER = [
    "mapping_and_slam",
    "global_planning",
    "local_planning",
    "trajectory_tracking",
    "low_level_control",
    "optimal_or_constraint_control",
]

CATEGORY_TO_SLOT = {
    MethodCategory.slam: "mapping_and_slam",
    MethodCategory.mapping: "mapping_and_slam",
    MethodCategory.localization: "mapping_and_slam",
    MethodCategory.state_estimation: "mapping_and_slam",
    MethodCategory.global_planning: "global_planning",
    MethodCategory.local_planning: "local_planning",
    MethodCategory.trajectory_tracking: "trajectory_tracking",
    MethodCategory.low_level_control: "low_level_control",
    MethodCategory.optimal_control: "optimal_or_constraint_control",
    MethodCategory.robust_control: "optimal_or_constraint_control",
}

SLOT_SUMMARY_LABELS = {
    "mapping_and_slam": "mapping/SLAM",
    "global_planning": "global planning",
    "local_planning": "local planning",
    "trajectory_tracking": "trajectory tracking",
    "low_level_control": "low-level control",
    "optimal_or_constraint_control": "constraint-aware control",
}


class ArchitectureSlot(BaseModel):
    """Selected method and alternatives for one architecture layer."""

    model_config = ConfigDict(extra="forbid")

    slot_name: str
    category: MethodCategory | None
    selected_method_id: str | None
    selected_method_name: str | None
    selected_score: float | None
    alternatives: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)


class ArchitectureRecommendation(BaseModel):
    """Structured architecture recommendation for one problem."""

    model_config = ConfigDict(extra="forbid")

    problem_id: str
    slots: list[ArchitectureSlot]
    summary: str
    warnings: list[str] = Field(default_factory=list)

    def get_slot(self, slot_name: str) -> ArchitectureSlot:
        """Return an architecture slot by name."""

        for slot in self.slots:
            if slot.slot_name == slot_name:
                return slot

        raise KeyError(f"Unknown architecture slot: {slot_name}")

    def selected_method_ids(self) -> list[str]:
        """Return selected non-null method IDs in slot order."""

        return [
            slot.selected_method_id
            for slot in self.slots
            if slot.selected_method_id is not None
        ]


def build_architecture_recommendation(
    scoring_result: ScoringResult,
) -> ArchitectureRecommendation:
    """Build a deterministic architecture recommendation from scored methods."""

    methods_by_slot = _group_methods_by_slot(scoring_result.scored_methods)
    slots = [
        _build_slot(slot_name, methods_by_slot.get(slot_name, []))
        for slot_name in SLOT_ORDER
    ]
    warnings = _build_warnings(slots)

    return ArchitectureRecommendation(
        problem_id=scoring_result.problem_id,
        slots=slots,
        summary=_build_summary(scoring_result.problem_id, slots),
        warnings=warnings,
    )


def _group_methods_by_slot(
    scored_methods: list[ScoredMethod],
) -> dict[str, list[ScoredMethod]]:
    methods_by_slot: dict[str, list[ScoredMethod]] = {slot_name: [] for slot_name in SLOT_ORDER}

    for scored_method in scored_methods:
        slot_name = CATEGORY_TO_SLOT.get(scored_method.category)
        if slot_name is None:
            continue

        methods_by_slot[slot_name].append(scored_method)

    for slot_methods in methods_by_slot.values():
        slot_methods.sort(key=lambda method: (-method.score, method.method_id))

    return methods_by_slot


def _build_slot(
    slot_name: str,
    slot_methods: list[ScoredMethod],
) -> ArchitectureSlot:
    if not slot_methods:
        return ArchitectureSlot(
            slot_name=slot_name,
            category=None,
            selected_method_id=None,
            selected_method_name=None,
            selected_score=None,
            rationale=[f"No scored method was available for the {slot_name} slot."],
        )

    selected_method = slot_methods[0]
    alternatives = [method.method_id for method in slot_methods[1:]]

    return ArchitectureSlot(
        slot_name=slot_name,
        category=selected_method.category,
        selected_method_id=selected_method.method_id,
        selected_method_name=selected_method.name,
        selected_score=selected_method.score,
        alternatives=alternatives,
        rationale=_build_rationale(selected_method),
    )


def _build_rationale(scored_method: ScoredMethod) -> list[str]:
    rationale = [f"Selected score: {scored_method.score}"]

    for reason in scored_method.positive_reasons[:2]:
        rationale.append(f"Positive reason: {reason}")

    for reason in scored_method.caution_reasons[:2]:
        rationale.append(f"Caution reason: {reason}")

    return rationale


def _build_summary(problem_id: str, slots: list[ArchitectureSlot]) -> str:
    selected_phrases = [
        f"{slot.selected_method_name} for {SLOT_SUMMARY_LABELS[slot.slot_name]}"
        for slot in slots
        if slot.selected_method_name is not None
    ]

    if not selected_phrases:
        return f"Recommended architecture for {problem_id}: no methods were selected."

    if len(selected_phrases) == 1:
        selected_text = selected_phrases[0]
    else:
        selected_text = ", ".join(selected_phrases[:-1])
        selected_text = f"{selected_text}, and {selected_phrases[-1]}"

    return f"Recommended architecture for {problem_id}: {selected_text}."


def _build_warnings(slots: list[ArchitectureSlot]) -> list[str]:
    warnings: list[str] = []

    for slot in slots:
        if any(rationale.startswith("Caution reason:") for rationale in slot.rationale):
            warnings.append(
                f"Selected method {slot.selected_method_id} in slot {slot.slot_name} has caution reasons."
            )

    required_slots = {
        "mapping_and_slam": "The architecture has no mapping/SLAM method.",
        "local_planning": "The architecture has no local planning method.",
        "low_level_control": "The architecture has no low-level control method.",
    }
    for slot_name, warning in required_slots.items():
        slot = next(slot for slot in slots if slot.slot_name == slot_name)
        if slot.selected_method_id is None:
            warnings.append(warning)

    return warnings
