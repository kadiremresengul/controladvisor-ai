"""Knowledge base loader for method cards."""

from pathlib import Path

from controladvisor.schemas.method_card import (
    MethodCard,
    MethodCategory,
    MethodRequirement,
    MethodStrength,
    MethodTag,
    load_method_card_from_yaml,
)


class MethodCardKnowledgeBase:
    """Validated collection of method cards with simple lookup helpers."""

    def __init__(self, method_cards: list[MethodCard]) -> None:
        if not method_cards:
            raise ValueError("No method cards found.")

        sorted_cards = sorted(method_cards, key=lambda method_card: method_card.id)
        card_ids = [method_card.id for method_card in sorted_cards]
        duplicate_ids = sorted(
            method_id for method_id in set(card_ids) if card_ids.count(method_id) > 1
        )

        if duplicate_ids:
            duplicate_text = ", ".join(duplicate_ids)
            raise ValueError(f"Duplicate method card IDs found: {duplicate_text}")

        self._method_cards = tuple(sorted_cards)
        self._methods_by_id = {method_card.id: method_card for method_card in sorted_cards}

    @classmethod
    def from_directory(cls, directory: str | Path) -> "MethodCardKnowledgeBase":
        """Load all non-template YAML method cards from a directory."""

        method_cards_dir = Path(directory)
        method_card_paths = sorted(
            path
            for path in method_cards_dir.glob("*.yaml")
            if path.is_file() and not path.name.startswith("_")
        )

        if not method_card_paths:
            raise ValueError(f"No method cards found in directory: {method_cards_dir}")

        method_cards = [
            load_method_card_from_yaml(path) for path in method_card_paths
        ]
        return cls(method_cards)

    def get_all_methods(self) -> list[MethodCard]:
        """Return all method cards in deterministic ID order."""

        return list(self._method_cards)

    def get_method(self, method_id: str) -> MethodCard:
        """Return a method card by ID."""

        try:
            return self._methods_by_id[method_id]
        except KeyError as exc:
            raise KeyError(f"Unknown method card ID: {method_id}") from exc

    def has_method(self, method_id: str) -> bool:
        """Return whether the knowledge base contains a method ID."""

        return method_id in self._methods_by_id

    def filter_by_category(self, category: MethodCategory) -> list[MethodCard]:
        """Return method cards in a category."""

        return [
            method_card
            for method_card in self._method_cards
            if method_card.category is category
        ]

    def filter_by_tag(self, tag: MethodTag) -> list[MethodCard]:
        """Return method cards with a tag."""

        return [
            method_card for method_card in self._method_cards if tag in method_card.tags
        ]

    def filter_by_requirement(
        self, requirement: MethodRequirement
    ) -> list[MethodCard]:
        """Return method cards with a requirement."""

        return [
            method_card
            for method_card in self._method_cards
            if requirement in method_card.requirements
        ]

    def filter_by_strength(self, strength: MethodStrength) -> list[MethodCard]:
        """Return method cards with a strength."""

        return [
            method_card
            for method_card in self._method_cards
            if strength in method_card.strengths
        ]


def load_default_method_knowledge_base() -> MethodCardKnowledgeBase:
    """Load method cards from the repository default data directory."""

    project_root = Path(__file__).resolve().parents[3]
    return MethodCardKnowledgeBase.from_directory(
        project_root / "data" / "method_cards"
    )
