"""
scene/structurer.py
────────────────────
Converts raw scene text segments into fully structured Scene objects.

This is the most important file in the scene pipeline.
It extracts ALL the metadata needed for multimodal generation:
  - Setting details → ComfyUI/SDXL image prompt
  - Characters + dialogue → TTS voice synthesis
  - Music mood + SFX cues → audio generation
  - Emotional tone + pacing → video assembly timing
"""
import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from llm.client import call_llm
from scene.schemas import (
    Scene, Setting, CharacterPresence, DialogueLine,
    EmotionalTone, TimeOfDay, NarrationStyle, Pacing
)


class SceneStructurer:
    """
    Takes a raw scene text segment and returns a fully populated Scene object.
    One LLM call per scene — extracts all metadata in a single structured prompt.
    """

    def structure(self, raw_scene: dict, character_profiles: dict) -> Scene:
        """
        Convert a raw scene dict into a Scene object.

        Args:
            raw_scene: {scene_number, suggested_title, text, story_id}
            character_profiles: Known characters to help with consistency.

        Returns:
            Fully populated Scene object.
        """
        scene_num = raw_scene["scene_number"]
        story_id  = raw_scene["story_id"]
        scene_id  = f"{story_id}_scene_{scene_num:02d}"

        logger.info(f"Structuring scene {scene_num}: {raw_scene['suggested_title']}")

        system = """You are a multimodal story director.
Analyze the scene text and extract structured metadata for:
  1. Setting and atmosphere
  2. Characters present and their states
  3. Dialogue lines
  4. Emotional tone and pacing
  5. A detailed SDXL image generation prompt
  6. Audio cues (music mood, SFX, ambient sounds)

Respond ONLY with valid JSON matching this exact schema:
{
  "title": "<evocative scene title>",
  "setting": {
    "location": "<specific place>",
    "time_of_day": "<dawn|morning|afternoon|dusk|night|unknown>",
    "weather": "<weather description>",
    "atmosphere": "<atmospheric description>",
    "lighting": "<lighting style>"
  },
  "characters": [
    {
      "name": "<character name>",
      "emotion": "<emotional state>",
      "action": "<what they are doing>",
      "location_in_scene": "<where in the scene>"
    }
  ],
  "narration_text": "<the scene text cleaned up for narration — no dialogue tags>",
  "dialogue": [
    {
      "character": "<name>",
      "text": "<exact dialogue>",
      "emotion": "<delivery emotion>"
    }
  ],
  "emotional_tone": "<tense|hopeful|ominous|melancholic|triumphant|mysterious|peaceful|fearful|joyful|suspenseful>",
  "pacing": "<slow|medium|fast>",
  "tension_level": <1-10>,
  "visual_prompt": "<detailed SDXL prompt: art style, lighting, composition, colors, mood, scene elements — 60-100 words>",
  "negative_prompt": "<what to avoid in image>",
  "narration_style": "<calm|urgent|whispered|dramatic|melancholic>",
  "music_mood": "<detailed music descriptor for generation, e.g. 'dark ambient electronic with distant strings'>",
  "music_tempo": "<slow|moderate|fast|building>",
  "sfx_cues": ["<sound 1>", "<sound 2>", "<sound 3>"],
  "ambient_sounds": ["<ambient 1>", "<ambient 2>"],
  "arc_stage": "<exposition|rising_action|climax|falling_action|resolution>",
  "tags": ["<tag1>", "<tag2>", "<tag3>"],
  "duration_estimate": <estimated seconds as float>
}"""

        user = f"""Scene text to analyze:

{raw_scene['text']}

Known characters (stay consistent):
{json.dumps(character_profiles, indent=2)[:600] if character_profiles else "No profiles yet — infer from text."}

Extract all structured metadata. Respond in JSON only."""

        raw = call_llm(system, user, temperature=0.3, max_tokens=2048, json_mode=True)

        try:
            data = json.loads(raw)
            return self._build_scene(data, scene_id, story_id, scene_num, raw_scene)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Scene structuring failed for scene {scene_num}: {e}")
            return self._minimal_scene(raw_scene, scene_id, story_id, scene_num)

    def _build_scene(
        self, data: dict, scene_id: str, story_id: str,
        scene_num: int, raw_scene: dict
    ) -> Scene:
        """Build a Scene object from LLM-extracted data."""

        # ── Setting ───────────────────────────────────────────────
        setting_data = data.get("setting", {})
        setting = Setting(
            location   = setting_data.get("location", "Unknown location"),
            time_of_day= self._safe_enum(TimeOfDay, setting_data.get("time_of_day"), TimeOfDay.UNKNOWN),
            weather    = setting_data.get("weather", "clear"),
            atmosphere = setting_data.get("atmosphere", "neutral"),
            lighting   = setting_data.get("lighting", "natural"),
        )

        # ── Characters ────────────────────────────────────────────
        characters = [
            CharacterPresence(
                name              = c.get("name", "Unknown"),
                emotion           = c.get("emotion", "neutral"),
                action            = c.get("action", "present"),
                location_in_scene = c.get("location_in_scene"),
            )
            for c in data.get("characters", [])
        ]

        # ── Dialogue ──────────────────────────────────────────────
        dialogue = [
            DialogueLine(
                character = d.get("character", "Unknown"),
                text      = d.get("text", ""),
                emotion   = d.get("emotion", "neutral"),
            )
            for d in data.get("dialogue", [])
        ]

        return Scene(
            scene_id        = scene_id,
            story_id        = story_id,
            sequence_number = scene_num,
            title           = data.get("title", raw_scene.get("suggested_title", f"Scene {scene_num}")),
            setting         = setting,
            characters      = characters,
            narration_text  = data.get("narration_text", raw_scene["text"]),
            dialogue        = dialogue,
            emotional_tone  = self._safe_enum(EmotionalTone, data.get("emotional_tone"), EmotionalTone.MYSTERIOUS),
            pacing          = self._safe_enum(Pacing, data.get("pacing"), Pacing.MEDIUM),
            tension_level   = max(1, min(10, int(data.get("tension_level", 5)))),
            visual_prompt   = data.get("visual_prompt", f"cinematic scene, {setting.location}, dramatic lighting"),
            negative_prompt = data.get("negative_prompt", "blurry, low quality, bad anatomy, watermark"),
            narration_style = self._safe_enum(NarrationStyle, data.get("narration_style"), NarrationStyle.CALM),
            music_mood      = data.get("music_mood", "ambient atmospheric"),
            music_tempo     = data.get("music_tempo", "moderate"),
            sfx_cues        = data.get("sfx_cues", []),
            ambient_sounds  = data.get("ambient_sounds", []),
            arc_stage       = data.get("arc_stage", "unknown"),
            tags            = data.get("tags", []),
            duration_estimate = float(data.get("duration_estimate", 30.0)),
        )

    def _minimal_scene(
        self, raw_scene: dict, scene_id: str, story_id: str, scene_num: int
    ) -> Scene:
        """Fallback: minimal Scene if LLM structuring fails."""
        return Scene(
            scene_id        = scene_id,
            story_id        = story_id,
            sequence_number = scene_num,
            title           = raw_scene.get("suggested_title", f"Scene {scene_num}"),
            setting         = Setting(location="Unknown", atmosphere="neutral"),
            narration_text  = raw_scene["text"],
            visual_prompt   = "cinematic scene, dramatic lighting, high quality",
            music_mood      = "ambient atmospheric music",
        )

    @staticmethod
    def _safe_enum(enum_class, value, default):
        """Safely convert string to enum, return default if invalid."""
        try:
            return enum_class(value)
        except (ValueError, TypeError):
            return default
