"""
agents/plot_agent.py
─────────────────────
Controls narrative arc, story structure, plot escalation,
cause-and-effect chains, and branching decision points.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from llm.client import call_llm


class PlotAgent(BaseAgent):
    name = "PlotAgent"
    role = "Narrative arc and plot structure controller"

    def communicate(self, story_context, conversation_log, character_profiles, world_bible) -> dict:
        system = """You are the Plot Agent in a collaborative story system.
Your responsibility: narrative arc, plot logic, escalation, and story structure.
You must respond ONLY with valid JSON matching this exact schema:
{
  "agent": "PlotAgent",
  "intent": "<what plot development you want next>",
  "reasoning": "<why this serves the story arc>",
  "concerns": "<any plot holes or pacing issues you see>"
}"""

        user = f"""Current story:
{story_context}

Other agents' discussion so far:
{self._format_log(conversation_log)}

World rules:
{world_bible}

What plot development do you want next? Respond in JSON."""

        raw = call_llm(system, user, temperature=0.7, json_mode=True, model="smart")
        return self._parse_json_response(raw)

    def propose(self, story_context, conversation_log, character_profiles, world_bible) -> dict:
        system = """You are the Plot Agent. Write the next story segment focused on plot advancement.
You must respond ONLY with valid JSON matching this exact schema:
{
  "agent": "PlotAgent",
  "segment": "<200-400 word story continuation focused on plot events>",
  "emotional_tone": "<one of: tense, hopeful, ominous, melancholic, triumphant, mysterious, peaceful>",
  "narrative_focus": "plot",
  "tags": ["<keyword1>", "<keyword2>", "<keyword3>"]
}"""

        user = f"""Story so far:
{story_context}

Agent discussion:
{self._format_log(conversation_log)}

Character profiles:
{character_profiles}

Write the next plot-driven story segment. Respond in JSON."""

        raw = call_llm(system, user, temperature=0.8, json_mode=True, model="smart")
        return self._parse_json_response(raw)

    def _format_log(self, log: list[dict]) -> str:
        """Format conversation log into readable text."""
        if not log:
            return "No discussion yet."
        return "\n".join(
            f"[{entry.get('agent', 'Unknown')}]: {entry.get('intent', entry.get('content', ''))}"
            for entry in log[-5:]  # Only last 5 to avoid context explosion
        )
