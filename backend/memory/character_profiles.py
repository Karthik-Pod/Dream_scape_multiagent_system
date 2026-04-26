"""
memory/character_profiles.py
──────────────────────────────
Persistent character profile store.
Every agent reads this before generating to ensure
characters behave consistently across the entire story.
"""
import json
from dataclasses import dataclass, field
from typing import Optional
from loguru import logger


@dataclass
class CharacterProfile:
    name: str
    role: str                           # protagonist, antagonist, supporting
    traits: list[str]                   # personality traits
    goals: list[str]                    # what they want
    fears: list[str]                    # what they're afraid of
    speech_style: str                   # how they talk
    relationships: dict[str, str]       # {other_char: relationship_type}
    backstory: str                      # brief backstory
    current_state: dict = field(default_factory=dict)  # evolves during story


class CharacterProfileStore:
    """
    In-memory store for character profiles.
    Agents read this via get_all() and write via update().
    Week 2: This gets backed by ChromaDB for semantic retrieval.
    """

    def __init__(self):
        self._profiles: dict[str, CharacterProfile] = {}

    def add(self, profile: CharacterProfile) -> None:
        self._profiles[profile.name] = profile
        logger.debug(f"Character added: {profile.name}")

    def get(self, name: str) -> Optional[CharacterProfile]:
        return self._profiles.get(name)

    def get_all(self) -> dict:
        """Return all profiles as plain dicts for LLM injection."""
        return {
            name: {
                "role": p.role,
                "traits": p.traits,
                "goals": p.goals,
                "fears": p.fears,
                "speech_style": p.speech_style,
                "relationships": p.relationships,
                "backstory": p.backstory,
                "current_state": p.current_state,
            }
            for name, p in self._profiles.items()
        }

    def update(self, name: str, updates: dict) -> None:
        """Update a character's current_state during story progression."""
        if name in self._profiles:
            self._profiles[name].current_state.update(updates)
            logger.debug(f"Character updated: {name} → {updates}")

    def extract_from_prompt(self, prompt: str) -> None:
        """
        Auto-extract character names from the initial prompt using LLM.
        Called once at story start. Placeholder — implemented in Week 2
        with ChromaDB integration.
        """
        pass

    def to_json(self) -> str:
        return json.dumps(self.get_all(), indent=2)

    def is_empty(self) -> bool:
        return len(self._profiles) == 0
