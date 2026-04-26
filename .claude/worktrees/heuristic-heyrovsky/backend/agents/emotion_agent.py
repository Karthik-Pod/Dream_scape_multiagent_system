"""
agents/emotion_agent.py
────────────────────────
Controls emotional tone, pacing, tension/relief cycles,
and ensures the reader's emotional journey is intentional.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from llm.client import call_llm


class EmotionAgent(BaseAgent):
    name = "EmotionAgent"
    role = "Emotional tone, pacing, and atmospheric depth"

    def communicate(self, story_context, conversation_log, character_profiles, world_bible) -> dict:
        system = """You are the Emotion Agent in a collaborative story system.
Your responsibility: emotional tone, pacing, tension and relief cycles, atmosphere.
You must respond ONLY with valid JSON matching this exact schema:
{
  "agent": "EmotionAgent",
  "intent": "<what emotional shift or atmosphere you want to introduce>",
  "reasoning": "<why this emotional beat serves the story's pacing>",
  "concerns": "<any emotional flatness or pacing problems you notice>"
}"""

        user = f"""Current story:
{story_context}

Agent discussion:
{self._format_log(conversation_log)}

What emotional direction should the story take next? Respond in JSON."""

        raw = call_llm(system, user, temperature=0.7, json_mode=True, model="fast")
        return self._parse_json_response(raw)

    def propose(self, story_context, conversation_log, character_profiles, world_bible) -> dict:
        system = """You are the Emotion Agent. Write the next segment focused on emotional depth.
You must respond ONLY with valid JSON matching this exact schema:
{
  "agent": "EmotionAgent",
  "segment": "<200-400 word story continuation rich in emotional texture and atmosphere>",
  "emotional_tone": "<one of: tense, hopeful, ominous, melancholic, triumphant, mysterious, peaceful>",
  "narrative_focus": "emotion",
  "tags": ["<keyword1>", "<keyword2>", "<keyword3>"],
  "pacing": "<one of: slow, medium, fast>",
  "tension_level": "<integer 1-10>"
}"""

        user = f"""Story so far:
{story_context}

Agent discussion:
{self._format_log(conversation_log)}

Write an emotionally resonant next segment. Respond in JSON."""

        raw = call_llm(system, user, temperature=0.85, json_mode=True, model="fast")
        return self._parse_json_response(raw)

    def _format_log(self, log: list[dict]) -> str:
        if not log:
            return "No discussion yet."
        return "\n".join(
            f"[{entry.get('agent', 'Unknown')}]: {entry.get('intent', entry.get('content', ''))}"
            for entry in log[-5:]
        )
