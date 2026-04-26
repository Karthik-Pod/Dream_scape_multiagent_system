"""
generation/video_gen.py  —  Magic Hour API
Uses magic-hour Python SDK for image-to-video animation.
pip install magic-hour
Get free key at: magichour.ai/developer
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from config import get_settings
from scene.schemas import Scene


class VideoGenerator:
    def __init__(self):
        self.settings  = get_settings()
        self.api_key   = self.settings.magic_hour_api_key
        self.clips_dir = os.path.join(self.settings.storage_base, "videos", "clips")
        os.makedirs(self.clips_dir, exist_ok=True)

    def _build_motion_prompt(self, scene: Scene) -> str:
        tone_motions = {
            "tense":       "slow camera push-in, tense atmosphere, subtle movement",
            "ominous":     "slow pan, dark shadows shifting, ominous drift",
            "hopeful":     "gentle zoom out, warm light rays, uplifting motion",
            "melancholic": "slow dolly back, soft focus drift, somber mood",
            "mysterious":  "slow orbital pan, mist swirling, ethereal movement",
            "triumphant":  "dramatic rise shot, epic sweep, heroic motion",
            "peaceful":    "gentle drift, soft breeze, calm floating motion",
            "fearful":     "slow zoom in, shadows closing, tense movement",
            "suspenseful": "slow rack focus, subtle tension, creeping motion",
            "joyful":      "bright zoom out, cheerful sweep, lively motion",
        }
        motion = tone_motions.get(scene.emotional_tone.value, "slow cinematic camera movement")
        return f"{motion}. {scene.visual_prompt[:150]}"

    def generate_clip_for_scene(self, scene: Scene, image_path: str) -> str | None:
        if not image_path or not os.path.exists(image_path):
            logger.error(f"Image not found for scene {scene.sequence_number}")
            return None

        logger.info(f"Animating scene {scene.sequence_number}: {scene.title}")

        try:
            from magic_hour import Client
            client    = Client(token=self.api_key)
            clip_name = f"{scene.story_id}_scene_{scene.sequence_number:02d}"
            clip_path = os.path.join(self.clips_dir, f"{clip_name}_clip.mp4")

            result = client.v1.image_to_video.generate(
                assets={"image_file_path": image_path},
                style={"prompt": self._build_motion_prompt(scene)},
                end_seconds=5,
                name=clip_name,
                resolution="480p",
                wait_for_completion=True,
                download_outputs=True,
                download_directory=self.clips_dir,
            )

            if result.status == "complete":
                downloaded = result.downloaded_paths
                if downloaded:
                    src = downloaded[0]
                    if os.path.exists(src) and src != clip_path:
                        os.rename(src, clip_path)
                    size_mb = os.path.getsize(clip_path) / (1024 * 1024)
                    logger.info(f"Clip saved: {clip_path} ({size_mb:.1f}MB)")
                    return clip_path
                logger.error("Complete but no downloaded paths")
                return None
            else:
                err = getattr(result, "error_message", "unknown")
                logger.error(f"Scene {scene.sequence_number} failed: {result.status} — {err}")
                return None

        except ImportError:
            logger.error("magic-hour not installed. Run: pip install magic-hour")
            return None
        except Exception as e:
            logger.error(f"Magic Hour error scene {scene.sequence_number}: {e}")
            return None

    def generate_clips_for_all_scenes(
        self, scenes: list[Scene], image_paths: dict[int, str]
    ) -> dict[int, str]:
        results = {}
        for i, scene in enumerate(scenes):
            img_path = image_paths.get(scene.sequence_number)
            logger.info(f"Animating scene {i+1}/{len(scenes)}: {scene.title}")
            clip_path = self.generate_clip_for_scene(scene, img_path)
            results[scene.sequence_number] = clip_path
            if clip_path:
                logger.info(f"Scene {scene.sequence_number} clip done.")
            else:
                logger.warning(f"Scene {scene.sequence_number} failed — static image fallback.")
        return results
