"""
agents/character_agent.py
──────────────────────────
Controls character arcs, motivations, dialogue authenticity,
relationships, and ensures characters behave consistently
with their established profiles.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from llm.client import call_llm


class CharacterAgent(BaseAgent):
    name = "CharacterAgent"
    role = "Character consistency, arcs, and dialogue"

    def communicate(self, story_context, conversation_log, character_profiles, world_bible) -> dict:
        system = """You are the Character Agent in a collaborative story system.
Your responsibility: character consistency, motivations, relationships, and authentic dialogue.
You must respond ONLY with valid JSON matching this exact schema:
{
  "agent": "CharacterAgent",
  "intent": "<what character development or action you want next>",
  "reasoning": "<why this fits the character's established profile and arc>",
  "concerns": "<any character inconsistencies you see in current story>"
}"""

        user = f"""Current story:
{story_context}

Agent discussion:
{self._format_log(conversation_log)}

Established character profiles:
{character_profiles}

What character action or development do you want next? Respond in JSON."""

        raw = call_llm(system, user, temperature=0.7, json_mode=True, model="smart")
        return self._parse_json_response(raw)

    def propose(self, story_context, conversation_log, character_profiles, world_bible) -> dict:
        system = """You are the Character Agent. Write the next story segment focused on character.
You must respond ONLY with valid JSON matching this exact schema:
{
  "agent": "CharacterAgent",
  "segment": "<200-400 word story continuation focused on character actions and dialogue>",
  "emotional_tone": "<one of: tense, hopeful, ominous, melancholic, triumphant, mysterious, peaceful>",
  "narrative_focus": "character",
  "tags": ["<keyword1>", "<keyword2>", "<keyword3>"],
  "character_updates": {
    "<character_name>": "<brief note on how this character changed or acted>"
  }
}"""

        user = f"""Story so far:
{story_context}

Agent discussion:
{self._format_log(conversation_log)}

Character profiles (stay consistent with these):
{character_profiles}

World context:
{world_bible}

Write the next character-driven segment. Respond in JSON."""

        raw = call_llm(system, user, temperature=0.8, json_mode=True, model="smart")
        return self._parse_json_response(raw)

    def _format_log(self, log: list[dict]) -> str:
        if not log:
            return "No discussion yet."
        return "\n".join(
            f"[{entry.get('agent', 'Unknown')}]: {entry.get('intent', entry.get('content', ''))}"
            for entry in log[-5:]
        )
