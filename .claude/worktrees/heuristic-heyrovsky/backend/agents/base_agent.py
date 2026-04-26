"""
agents/base_agent.py
─────────────────────
Abstract base class for all Dreamscape agents.

DESIGN PRINCIPLES:
  - Every agent MUST return structured JSON (not raw text).
    This is the core contract that makes the scene pipeline possible.
  - communicate() = share intent with other agents (discussion phase)
  - propose()     = write actual story content (proposal phase)
  - Both return dicts, never raw strings.
"""
from abc import ABC, abstractmethod
from typing import Any
import json
from loguru import logger


class BaseAgent(ABC):
    """
    All agents inherit this. Enforces the structured output contract.
    """

    # Subclasses must define these
    name: str = "BaseAgent"
    role: str = "undefined"

    @abstractmethod
    def communicate(
        self,
        story_context: str,
        conversation_log: list[dict],
        character_profiles: dict,
        world_bible: dict,
    ) -> dict:
        """
        COMMUNICATION PHASE:
        Agent reads the full context and broadcasts its intent.
        What does it want to happen next, and why?

        Returns:
            {
                "agent": self.name,
                "intent": "...",        # What this agent wants
                "reasoning": "...",     # Why, based on story state
                "concerns": "..."       # Any narrative risks to flag
            }
        """
        raise NotImplementedError

    @abstractmethod
    def propose(
        self,
        story_context: str,
        conversation_log: list[dict],
        character_profiles: dict,
        world_bible: dict,
    ) -> dict:
        """
        PROPOSAL PHASE:
        Agent writes its version of the next story segment.

        Returns:
            {
                "agent": self.name,
                "segment": "...",           # The actual story text
                "emotional_tone": "...",    # e.g. tense, hopeful, ominous
                "narrative_focus": "...",   # e.g. character, plot, world
                "tags": ["..."]             # keywords for memory indexing
            }
        """
        raise NotImplementedError

    def _parse_json_response(self, raw: str, fallback_key: str = "content") -> dict:
        """
        Safely parse LLM JSON output.
        If parsing fails, wraps the raw string in a dict rather than crashing.
        """
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"[{self.name}] JSON parse failed. Wrapping raw output.")
            return {fallback_key: raw, "agent": self.name, "parse_error": True}
