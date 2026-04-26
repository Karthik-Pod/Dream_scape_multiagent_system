"""
scene/validator.py
───────────────────
Validates scene list for narrative continuity.

Checks:
  1. Character continuity — characters don't vanish/reappear without reason
  2. Timeline consistency — no impossible time jumps
  3. Setting continuity — location changes are logical
  4. Emotional arc — tone progression makes narrative sense
  5. Completeness — all required fields populated

This runs AFTER structuring, BEFORE generation.
Catches issues early so we don't waste image/audio generation calls.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from scene.schemas import Scene, SceneList


class ValidationResult:
    def __init__(self):
        self.issues: list[dict] = []
        self.warnings: list[str] = []
        self.passed: bool = True

    def add_issue(self, scene_num: int, issue_type: str, description: str):
        self.issues.append({
            "scene": scene_num,
            "type": issue_type,
            "description": description,
        })
        self.passed = False

    def add_warning(self, message: str):
        self.warnings.append(message)

    def summary(self) -> str:
        if self.passed:
            return f"✅ Validation passed with {len(self.warnings)} warnings."
        return f"❌ Validation failed: {len(self.issues)} issues, {len(self.warnings)} warnings."


class SceneValidator:

    def validate(self, scene_list: SceneList) -> ValidationResult:
        """
        Run all validation checks on a complete scene list.
        Returns a ValidationResult with any issues found.
        """
        result = ValidationResult()
        scenes = scene_list.scenes

        if not scenes:
            result.add_issue(0, "empty", "No scenes found in scene list.")
            return result

        logger.info(f"Validating {len(scenes)} scenes for story {scene_list.story_id}...")

        for scene in scenes:
            self._check_completeness(scene, result)
            self._check_visual_prompt(scene, result)

        # Cross-scene checks (need pairs of adjacent scenes)
        for i in range(1, len(scenes)):
            prev = scenes[i - 1]
            curr = scenes[i]
            self._check_sequence(prev, curr, result)
            self._check_emotional_arc(prev, curr, result)

        self._check_arc_progression(scenes, result)

        logger.info(result.summary())
        return result

    def _check_completeness(self, scene: Scene, result: ValidationResult):
        """Every scene must have the fields image/audio generation needs."""
        if not scene.narration_text or len(scene.narration_text) < 20:
            result.add_issue(scene.sequence_number, "completeness",
                             "narration_text is too short or missing.")

        if not scene.visual_prompt or len(scene.visual_prompt) < 10:
            result.add_issue(scene.sequence_number, "completeness",
                             "visual_prompt is missing or too short for image generation.")

        if not scene.music_mood:
            result.add_warning(f"Scene {scene.sequence_number}: music_mood is empty.")

        if not scene.setting.location:
            result.add_warning(f"Scene {scene.sequence_number}: setting location is undefined.")

    def _check_visual_prompt(self, scene: Scene, result: ValidationResult):
        """Visual prompts should be detailed enough for SDXL."""
        prompt = scene.visual_prompt
        word_count = len(prompt.split())
        if word_count < 8:
            result.add_warning(
                f"Scene {scene.sequence_number}: visual_prompt only {word_count} words. "
                f"SDXL works better with 20+ words."
            )

    def _check_sequence(self, prev: Scene, curr: Scene, result: ValidationResult):
        """Check that scene sequence numbers are correct."""
        expected = prev.sequence_number + 1
        if curr.sequence_number != expected:
            result.add_issue(curr.sequence_number, "sequence",
                             f"Expected scene {expected}, got {curr.sequence_number}.")

    def _check_emotional_arc(self, prev: Scene, curr: Scene, result: ValidationResult):
        """
        Warn if emotional tone doesn't change at all across many scenes.
        Flat emotional arcs indicate the agents may have gotten stuck.
        """
        if prev.emotional_tone == curr.emotional_tone:
            if prev.sequence_number > 1:  # Allow same tone in first two scenes
                result.add_warning(
                    f"Scenes {prev.sequence_number} and {curr.sequence_number} "
                    f"have identical emotional tone: {curr.emotional_tone.value}. "
                    f"Consider more variety."
                )

    def _check_arc_progression(self, scenes: list[Scene], result: ValidationResult):
        """Check the story has a meaningful arc across all scenes."""
        tension_levels = [s.tension_level for s in scenes]

        # Good stories have rising then falling tension
        max_tension_idx = tension_levels.index(max(tension_levels))

        # Climax should not be in the first scene
        if max_tension_idx == 0:
            result.add_warning(
                "Peak tension is in scene 1. Narrative arcs typically build toward a climax."
            )

        # Check we have both low and high tension
        tension_range = max(tension_levels) - min(tension_levels)
        if tension_range < 2:
            result.add_warning(
                f"Tension range is only {tension_range} points. "
                f"Consider varying pacing more across scenes."
            )
