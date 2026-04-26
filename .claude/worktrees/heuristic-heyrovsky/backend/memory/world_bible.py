"""
memory/world_bible.py
──────────────────────
The World Bible — stores established facts about the story world.
No agent can contradict these. The Coordinator enforces this.

Examples:
  - "Magic requires physical contact"
  - "The city of Arath was destroyed 100 years ago"
  - "Guns don't exist in this world"
"""
from loguru import logger


class WorldBible:
    def __init__(self):
        self._facts: dict[str, str] = {}       # {fact_id: description}
        self._locations: dict[str, dict] = {}  # {name: {description, rules}}
        self._world_rules: list[str] = []      # hard rules of this world

    def add_fact(self, fact_id: str, description: str) -> None:
        self._facts[fact_id] = description
        logger.debug(f"World fact added: {fact_id}")

    def add_location(self, name: str, description: str, rules: list[str] = None) -> None:
        self._locations[name] = {
            "description": description,
            "rules": rules or [],
        }

    def add_rule(self, rule: str) -> None:
        """Add a hard world rule agents cannot violate."""
        self._world_rules.append(rule)

    def get_all(self) -> dict:
        """Return full world context as dict for LLM injection."""
        return {
            "facts": self._facts,
            "locations": self._locations,
            "rules": self._world_rules,
        }

    def is_empty(self) -> bool:
        return not self._facts and not self._locations and not self._world_rules

    def summary(self) -> str:
        if self.is_empty():
            return "World bible is empty — world details will emerge from the story."
        lines = []
        if self._world_rules:
            lines.append("WORLD RULES: " + "; ".join(self._world_rules))
        if self._locations:
            lines.append("LOCATIONS: " + ", ".join(self._locations.keys()))
        if self._facts:
            lines.append(f"ESTABLISHED FACTS: {len(self._facts)} recorded")
        return "\n".join(lines)
