from pathlib import Path

import pytest

from controladvisor.knowledge_base import (
    MethodCardKnowledgeBase,
    load_default_method_knowledge_base,
)
from controladvisor.schemas.method_card import (
    MethodCard,
    MethodCategory,
    MethodRequirement,
    MethodStrength,
    MethodTag,
)


METHOD_CARDS_DIR = Path(__file__).resolve().parents[1] / "data" / "method_cards"


def method_ids(method_cards: list[MethodCard]) -> set[str]:
    return {method_card.id for method_card in method_cards}


def test_default_knowledge_base_loads_all_method_cards() -> None:
    knowledge_base = load_default_method_knowledge_base()

    assert len(knowledge_base.get_all_methods()) == 8


def test_get_method_returns_mpc_card() -> None:
    knowledge_base = load_default_method_knowledge_base()

    assert knowledge_base.get_method("mpc").name == "Model Predictive Control"


def test_get_method_unknown_raises_key_error() -> None:
    knowledge_base = load_default_method_knowledge_base()

    with pytest.raises(KeyError):
        knowledge_base.get_method("unknown")


def test_has_method_reports_known_and_unknown_methods() -> None:
    knowledge_base = load_default_method_knowledge_base()

    assert knowledge_base.has_method("mpc") is True
    assert knowledge_base.has_method("unknown") is False


def test_filter_by_optimal_control_includes_mpc_and_lqr() -> None:
    knowledge_base = load_default_method_knowledge_base()

    filtered_ids = method_ids(
        knowledge_base.filter_by_category(MethodCategory.optimal_control)
    )

    assert {"mpc", "lqr"}.issubset(filtered_ids)


def test_filter_by_global_planning_includes_astar() -> None:
    knowledge_base = load_default_method_knowledge_base()

    filtered_ids = method_ids(
        knowledge_base.filter_by_category(MethodCategory.global_planning)
    )

    assert "astar" in filtered_ids


def test_filter_by_indoor_factory_tag_returns_multiple_mvp_methods() -> None:
    knowledge_base = load_default_method_knowledge_base()

    filtered_ids = method_ids(knowledge_base.filter_by_tag(MethodTag.indoor_factory))

    assert len(filtered_ids) >= 4
    assert {"astar", "dwa", "mpc"}.issubset(filtered_ids)


def test_filter_by_handles_constraints_strength_includes_mpc() -> None:
    knowledge_base = load_default_method_knowledge_base()

    filtered_ids = method_ids(
        knowledge_base.filter_by_strength(MethodStrength.handles_constraints)
    )

    assert "mpc" in filtered_ids


def test_filter_by_lidar_requirement_includes_mvp_navigation_methods() -> None:
    knowledge_base = load_default_method_knowledge_base()

    filtered_ids = method_ids(
        knowledge_base.filter_by_requirement(MethodRequirement.lidar)
    )

    assert {"dwa", "graph_slam"}.issubset(filtered_ids)


def test_duplicate_method_ids_raise_value_error(tmp_path: Path) -> None:
    first_duplicate = tmp_path / "a_pid.yaml"
    second_duplicate = tmp_path / "b_pid.yaml"

    source_text = (METHOD_CARDS_DIR / "pid.yaml").read_text(encoding="utf-8")
    first_duplicate.write_text(source_text, encoding="utf-8")
    second_duplicate.write_text(source_text, encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate method card IDs"):
        MethodCardKnowledgeBase.from_directory(tmp_path)


def test_empty_directory_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No method cards found"):
        MethodCardKnowledgeBase.from_directory(tmp_path)


def test_template_file_is_ignored(tmp_path: Path) -> None:
    template_text = (METHOD_CARDS_DIR / "_template.yaml").read_text(encoding="utf-8")
    (tmp_path / "_template.yaml").write_text(template_text, encoding="utf-8")

    with pytest.raises(ValueError, match="No method cards found"):
        MethodCardKnowledgeBase.from_directory(tmp_path)
