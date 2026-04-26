"""
agents/audio_agent.py
──────────────────────
Controls audio atmosphere — music mood descriptors,
SFX cue lists, narration style, and voice direction.
Does NOT generate audio directly; produces structured
cues consumed by generation/tts_gen.py and music_gen.py.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from llm.client import call_llm


class AudioAgent(BaseAgent):
    name = "AudioAgent"
    role = "Audio atmosphere, music, SFX, and narration direction"

    def communicate(self, story_context, conversation_log, character_profiles, world_bible) -> dict:
        system = """You are the Audio Agent in a collaborative story system.
Your responsibility: background music, sound effects, narration style, and audio atmosphere.
You must respond ONLY with valid JSON matching this exact schema:
{
  "agent": "AudioAgent",
  "intent": "<what audio atmosphere you want to create>",
  "reasoning": "<how this audio direction supports the emotional and narrative goals>",
  "concerns": "<any audio-narrative mismatches you notice>"
}"""

        user = f"""Current story:
{story_context}

Agent discussion:
{self._format_log(conversation_log)}

What audio direction should the next scene have? Respond in JSON."""

        raw = call_llm(system, user, temperature=0.7, json_mode=True, model="fast")
        return self._parse_json_response(raw)

    def propose(self, story_context, conversation_log, character_profiles, world_bible) -> dict:
        system = """You are the Audio Agent. Write the next story segment and define its full audio landscape.
You must respond ONLY with valid JSON matching this exact schema:
{
  "agent": "AudioAgent",
  "segment": "<200-400 word story continuation with attention to sound and atmosphere>",
  "emotional_tone": "<one of: tense, hopeful, ominous, melancholic, triumphant, mysterious, peaceful>",
  "narrative_focus": "audio",
  "tags": ["<keyword1>", "<keyword2>", "<keyword3>"],
  "music_mood": "<descriptor for music generation, e.g. 'dark orchestral strings building tension'>",
  "music_tempo": "<one of: slow, moderate, fast, building>",
  "sfx_cues": ["<sound effect 1>", "<sound effect 2>", "<sound effect 3>"],
  "narration_style": "<one of: calm, urgent, whispered, dramatic, melancholic>",
  "ambient_sounds": ["<ambient sound 1>", "<ambient sound 2>"]
}"""

        user = f"""Story so far:
{story_context}

Agent discussion:
{self._format_log(conversation_log)}

Write the next segment and define the audio landscape. Respond in JSON."""

        raw = call_llm(system, user, temperature=0.8, json_mode=True, model="fast")
        return self._parse_json_response(raw)

    def _format_log(self, log: list[dict]) -> str:
        if not log:
            return "No discussion yet."
        return "\n".join(
            f"[{entry.get('agent', 'Unknown')}]: {entry.get('intent', entry.get('content', ''))}"
            for entry in log[-5:]
        )
