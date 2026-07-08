from pathlib import Path

import pytest
from pydantic import ValidationError
import yaml

from controladvisor.schemas.method_card import (
    MethodCard,
    MethodCategory,
    MethodMetric,
    MethodStrength,
    load_method_card_from_yaml,
)


METHOD_CARDS_DIR = Path(__file__).resolve().parents[1] / "data" / "method_cards"
METHOD_CARD_FILES = sorted(
    path for path in METHOD_CARDS_DIR.glob("*.yaml") if not path.name.startswith("_")
)


def load_cards_by_id() -> dict[str, MethodCard]:
    return {path.stem: load_method_card_from_yaml(path) for path in METHOD_CARD_FILES}


def test_each_method_card_yaml_loads_successfully() -> None:
    cards = [load_method_card_from_yaml(path) for path in METHOD_CARD_FILES]

    assert len(cards) == 8


def test_all_method_card_ids_are_unique() -> None:
    cards = [load_method_card_from_yaml(path) for path in METHOD_CARD_FILES]
    card_ids = [card.id for card in cards]

    assert len(card_ids) == len(set(card_ids))


@pytest.mark.parametrize(
    ("card_id", "expected_category"),
    [
        ("mpc", MethodCategory.optimal_control),
        ("pid", MethodCategory.low_level_control),
        ("astar", MethodCategory.global_planning),
        ("dwa", MethodCategory.local_planning),
        ("graph_slam", MethodCategory.slam),
    ],
)
def test_method_card_categories(
    card_id: str, expected_category: MethodCategory
) -> None:
    cards = load_cards_by_id()

    assert cards[card_id].category is expected_category


def test_mpc_strengths_include_handles_constraints() -> None:
    cards = load_cards_by_id()

    assert MethodStrength.handles_constraints in cards["mpc"].strengths


def test_pid_strengths_include_low_compute_cost() -> None:
    cards = load_cards_by_id()

    assert MethodStrength.low_compute_cost in cards["pid"].strengths


def test_astar_metrics_include_path_length() -> None:
    cards = load_cards_by_id()

    assert MethodMetric.path_length in cards["astar"].metrics


def test_method_card_rejects_unknown_yaml_fields(tmp_path: Path) -> None:
    source_data = yaml.safe_load(
        (METHOD_CARDS_DIR / "pid.yaml").read_text(encoding="utf-8")
    )
    source_data["unknown_field"] = "not allowed"
    invalid_card_path = tmp_path / "invalid_pid.yaml"
    invalid_card_path.write_text(yaml.safe_dump(source_data), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_method_card_from_yaml(invalid_card_path)
