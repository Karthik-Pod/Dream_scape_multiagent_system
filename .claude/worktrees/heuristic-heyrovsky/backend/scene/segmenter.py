"""
scene/segmenter.py
───────────────────
Splits raw story text into scene boundary segments.

WHY LLM-BASED SEGMENTATION:
  Rule-based splitting (by paragraph, by sentence count) loses
  narrative context. Scenes should break at natural story beats —
  location changes, time jumps, emotional shifts — which only
  an LLM can reliably detect.

OUTPUT: List of raw text segments, one per scene.
These then go into SceneStructurer to become full Scene objects.
"""
import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from llm.client import call_llm


class SceneSegmenter:
    """
    Takes full story text and returns a list of scene text segments.
    Each segment becomes one Scene object downstream.
    """

    def segment(self, story_text: str, story_id: str) -> list[dict]:
        """
        Split story into scenes using LLM.

        Args:
            story_text: The complete story as a string.
            story_id:   Parent story identifier.

        Returns:
            List of dicts: [{scene_number, text, suggested_title}]
        """
        logger.info(f"Segmenting story {story_id} into scenes...")

        system = """You are a narrative structure expert.
Split the provided story into distinct scenes.
A new scene begins when ANY of these occur:
  - Location changes
  - Significant time jump
  - Major emotional shift
  - New plot event begins

Rules:
  - Minimum 2 scenes, maximum 8 scenes
  - Each scene must be self-contained and meaningful
  - Preserve ALL original text — do not summarize or rewrite
  - Keep scenes roughly equal in length when possible

Respond ONLY with valid JSON:
{
  "total_scenes": <number>,
  "scenes": [
    {
      "scene_number": 1,
      "suggested_title": "<short evocative title>",
      "text": "<exact story text for this scene>"
    }
  ]
}"""

        user = f"""Split this story into scenes:

{story_text}

Respond in JSON only."""

        raw = call_llm(system, user, temperature=0.3, max_tokens=4096, json_mode=True)

        try:
            data = json.loads(raw)
            scenes = data.get("scenes", [])

            # Validate all scenes have required fields
            validated = []
            for i, scene in enumerate(scenes):
                validated.append({
                    "scene_number": scene.get("scene_number", i + 1),
                    "suggested_title": scene.get("suggested_title", f"Scene {i + 1}"),
                    "text": scene.get("text", "").strip(),
                    "story_id": story_id,
                })

            logger.info(f"Story segmented into {len(validated)} scenes.")
            return validated

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Segmenter JSON parse failed: {e}. Falling back to paragraph split.")
            return self._fallback_split(story_text, story_id)

    def _fallback_split(self, story_text: str, story_id: str) -> list[dict]:
        """
        Rule-based fallback: split by double newlines (paragraphs).
        Used only if LLM segmentation fails.
        """
        paragraphs = [p.strip() for p in story_text.split("\n\n") if p.strip()]

        # Group into max 5 scenes
        chunk_size = max(1, len(paragraphs) // 5)
        scenes = []
        for i in range(0, len(paragraphs), chunk_size):
            chunk = "\n\n".join(paragraphs[i:i + chunk_size])
            scenes.append({
                "scene_number": len(scenes) + 1,
                "suggested_title": f"Scene {len(scenes) + 1}",
                "text": chunk,
                "story_id": story_id,
            })

        logger.info(f"Fallback split produced {len(scenes)} scenes.")
        return scenes
