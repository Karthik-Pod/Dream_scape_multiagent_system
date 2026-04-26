"""
agents/visual_agent.py
───────────────────────
Controls visual storytelling — generates rich scene descriptions
and engineered image prompts for ComfyUI/SDXL.
This agent does NOT generate images directly; it produces
the visual_prompt that feeds into generation/image_gen.py.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.base_agent import BaseAgent
from llm.client import call_llm


class VisualAgent(BaseAgent):
    name = "VisualAgent"
    role = "Scene visualization and image prompt engineering"

    def communicate(self, story_context, conversation_log, character_profiles, world_bible) -> dict:
        system = """You are the Visual Agent in a collaborative story system.
Your responsibility: visual atmosphere, scene composition, lighting, and image generation prompts.
You must respond ONLY with valid JSON matching this exact schema:
{
  "agent": "VisualAgent",
  "intent": "<what visual elements and atmosphere you want to establish>",
  "reasoning": "<how this visual approach reinforces the narrative>",
  "concerns": "<any visual inconsistencies or missed opportunities>"
}"""

        user = f"""Current story:
{story_context}

Agent discussion:
{self._format_log(conversation_log)}

World context:
{world_bible}

What visual direction should the next scene have? Respond in JSON."""

        raw = call_llm(system, user, temperature=0.7, json_mode=True, model="fast")
        return self._parse_json_response(raw)

    def propose(self, story_context, conversation_log, character_profiles, world_bible) -> dict:
        system = """You are the Visual Agent. Write the next segment with rich visual description
AND generate an optimized image prompt for SDXL/Stable Diffusion.
You must respond ONLY with valid JSON matching this exact schema:
{
  "agent": "VisualAgent",
  "segment": "<200-400 word story continuation rich in visual detail and scene description>",
  "emotional_tone": "<one of: tense, hopeful, ominous, melancholic, triumphant, mysterious, peaceful>",
  "narrative_focus": "visual",
  "tags": ["<keyword1>", "<keyword2>", "<keyword3>"],
  "image_prompt": "<engineered SDXL prompt: style, lighting, composition, colors, mood — 50-100 words>",
  "negative_prompt": "<what to avoid in the image: blurry, low quality, etc>",
  "scene_setting": {
    "location": "<specific place>",
    "time_of_day": "<dawn/morning/afternoon/dusk/night>",
    "weather": "<clear/stormy/foggy/etc>",
    "lighting": "<dramatic/soft/harsh/candlelit/etc>"
  }
}"""

        user = f"""Story so far:
{story_context}

Agent discussion:
{self._format_log(conversation_log)}

Character profiles:
{character_profiles}

World context:
{world_bible}

Write a visually rich next segment and generate the SDXL image prompt. Respond in JSON."""

        raw = call_llm(system, user, temperature=0.8, json_mode=True, model="fast")
        return self._parse_json_response(raw)

    def _format_log(self, log: list[dict]) -> str:
        if not log:
            return "No discussion yet."
        return "\n".join(
            f"[{entry.get('agent', 'Unknown')}]: {entry.get('intent', entry.get('content', ''))}"
            for entry in log[-5:]
        )
