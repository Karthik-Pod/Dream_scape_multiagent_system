"""
generation/video_gen.py
────────────────────────
Converts scene images into real animated video clips using Magic Hour API.

Why Magic Hour over Kling:
  - Official Python SDK (pip install magic-hour)
  - wait_for_completion=True — no manual polling loop needed
  - Auto-downloads the clip directly to local storage
  - Clean error handling with result.status

Flow per scene:
  1. Submit image + motion prompt to Magic Hour
  2. SDK blocks until complete (handles polling internally)
  3. MP4 clip auto-downloaded to storage/videos/clips/
  4. Video assembler uses clip + audio → final scene video
"""
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from config import get_settings
from scene.schemas import Scene


class VideoGenerator:
    """
    Generates animated 5-second video clips from scene images.
    Uses Magic Hour SDK — no manual polling, auto-download.
    """

    def __init__(self):
        self.settings  = get_settings()
        self.api_key   = self.settings.magic_hour_api_key
        self.clips_dir = os.path.join(self.settings.storage_base, "videos", "clips")
        os.makedirs(self.clips_dir, exist_ok=True)

    def _build_motion_prompt(self, scene: Scene) -> str:
        """Build a cinematic motion prompt matched to scene emotional tone."""
        tone_motions = {
            "tense":       "slow camera push-in, shadows deepening, tense subtle movement",
            "ominous":     "slow pan across scene, dark shadows shifting, ominous atmosphere",
            "hopeful":     "gentle zoom out, warm light rays, uplifting motion, soft wind",
            "melancholic": "slow dolly backward, soft focus drift, somber mood",
            "mysterious":  "slow orbital pan, mist swirling, ethereal floating movement",
            "triumphant":  "dramatic upward rise shot, epic cinematic sweep, heroic motion",
            "peaceful":    "gentle drift, soft breeze, leaves rustling, calm motion",
            "fearful":     "slow creeping zoom in, shadows closing in, tense movement",
            "suspenseful": "slow rack focus, subtle tension build, creeping motion",
            "joyful":      "bright zoom out, cheerful sweep, warm light, lively motion",
        }
        motion = tone_motions.get(scene.emotional_tone.value, "slow cinematic camera movement")
        return f"{motion}. {scene.visual_prompt[:120]}"

    def generate_clip_for_scene(self, scene: Scene, image_path: str) -> str | None:
        """
        Generate a 5-second animated video clip from a scene image.

        Args:
            scene:      Scene object with metadata
            image_path: Local path to the scene PNG image

        Returns:
            Local path to downloaded MP4 clip, or None if failed.
        """
        if not image_path or not os.path.exists(image_path):
            logger.error(f"Image not found for scene {scene.sequence_number}: {image_path}")
            return None

        try:
            from magic_hour import Client
        except ImportError:
            raise RuntimeError(
                "magic-hour not installed. Run: pip install magic-hour"
            )

        logger.info(f"Animating scene {scene.sequence_number}: {scene.title}")

        prompt     = self._build_motion_prompt(scene)
        clip_name  = f"{scene.story_id}_scene_{scene.sequence_number:02d}"
        clip_path  = os.path.join(self.clips_dir, f"{clip_name}_clip.mp4")

        try:
            client = Client(token=self.api_key)

            result = client.v1.image_to_video.generate(
                assets={
                    "image_file_path": image_path,   # local file — SDK handles upload
                },
                style={
                    "prompt": prompt,
                },
                end_seconds=5,
                name=clip_name,
                resolution="480p",                   # 480p = affordable credits, good quality
                wait_for_completion=True,             # blocks until done — no manual polling
                download_outputs=True,
                download_directory=self.clips_dir,
            )

            if result.status == "complete":
                # SDK downloads to clips_dir — find the file
                downloaded = result.downloaded_paths
                if downloaded:
                    # Rename to our standard naming convention
                    src = downloaded[0]
                    if src != clip_path and os.path.exists(src):
                        os.rename(src, clip_path)
                    size_mb = os.path.getsize(clip_path) / (1024 * 1024)
                    logger.info(f"Clip saved: {clip_path} ({size_mb:.1f}MB) | "
                                f"Credits used: {result.credits_charged}")
                    return clip_path
                else:
                    logger.error("Status complete but no downloaded paths returned.")
                    return None
            else:
                err = getattr(result, "error_message", "unknown error")
                logger.error(f"Scene {scene.sequence_number} failed: {result.status} — {err}")
                return None

        except Exception as e:
            logger.error(f"Magic Hour API error for scene {scene.sequence_number}: {e}")
            return None

    def generate_clips_for_all_scenes(
        self,
        scenes: list[Scene],
        image_paths: dict[int, str],
    ) -> dict[int, str]:
        """
        Generate animated clips for all scenes sequentially.

        Args:
            scenes:      List of Scene objects
            image_paths: {sequence_number: image_path}

        Returns:
            {sequence_number: clip_path}  — None = failed, uses static image fallback
        """
        results = {}
        total   = len(scenes)

        for i, scene in enumerate(scenes):
            img_path = image_paths.get(scene.sequence_number)
            logger.info(f"Animating scene {i+1}/{total}: {scene.title}")

            clip_path = self.generate_clip_for_scene(scene, img_path)
            results[scene.sequence_number] = clip_path

            if clip_path:
                logger.info(f"Scene {scene.sequence_number} clip done.")
            else:
                logger.warning(
                    f"Scene {scene.sequence_number} clip failed — "
                    "will use static image fallback in video assembly."
                )

        return results
