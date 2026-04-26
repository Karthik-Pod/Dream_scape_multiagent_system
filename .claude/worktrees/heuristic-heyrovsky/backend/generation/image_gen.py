"""
generation/image_gen.py  —  HuggingFace Router API
────────────────────────────────────────────────────
Uses the NEW HuggingFace router endpoint (api-inference.huggingface.co is gone).
New URL: https://router.huggingface.co/hf-inference/models/{model}

Install: pip install huggingface_hub
"""
import sys, os, time, io
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from config import get_settings
from scene.schemas import Scene

HF_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"  # SDXL — reliable free tier


class ImageGenerator:
    def __init__(self):
        self.settings   = get_settings()
        self.api_token  = self.settings.hf_api_token
        self.output_dir = os.path.join(self.settings.storage_base, "images")
        os.makedirs(self.output_dir, exist_ok=True)

    def check_comfyui_running(self) -> bool:
        if not self.api_token:
            logger.warning("HF_API_TOKEN not set — image generation will be skipped.")
            return False
        return True

    def generate_for_scene(self, scene: Scene) -> str | None:
        logger.info(f"Generating image {scene.sequence_number}: {scene.title}")

        try:
            from huggingface_hub import InferenceClient
            from PIL import Image

            client = InferenceClient(
                provider="hf-inference",
                api_key=self.api_token,
            )

            prompt   = self._build_prompt(scene)
            filename = f"{scene.story_id}_scene_{scene.sequence_number:02d}.png"
            out_path = os.path.join(self.output_dir, filename)

            # Returns a PIL Image directly
            image = client.text_to_image(
                prompt,
                model=HF_MODEL,
                negative_prompt=(
                    "blurry, low quality, watermark, text, ugly, "
                    "deformed, artifacts, chromatic aberration"
                ),
                guidance_scale=7.5,
                num_inference_steps=25,
                width=1024,
                height=1024,
            )

            image.save(out_path)
            size_kb = os.path.getsize(out_path) / 1024
            logger.info(f"Image saved: {out_path} ({size_kb:.0f}KB)")
            return out_path

        except Exception as e:
            logger.error(f"Image generation failed for scene {scene.sequence_number}: {e}")
            return None

    def generate_for_all_scenes(self, scenes: list[Scene]) -> dict[int, str]:
        results = {}
        total   = len(scenes)

        for i, scene in enumerate(scenes):
            logger.info(f"Generating image {i+1}/{total}: {scene.title}")
            path = self.generate_for_scene(scene)
            results[scene.sequence_number] = path

            if path:
                logger.info(f"Scene {scene.sequence_number} done.")
            else:
                logger.warning(f"Scene {scene.sequence_number} failed — using fallback.")

            if i < total - 1:
                time.sleep(2)

        return results

    def _build_prompt(self, scene: Scene) -> str:
        tone_keywords = {
            "tense":       "high contrast shadows, dramatic tension",
            "ominous":     "dark foreboding atmosphere, deep shadows",
            "hopeful":     "warm golden light, uplifting brightness",
            "melancholic": "desaturated colors, soft somber lighting",
            "mysterious":  "ethereal mist, mysterious fog",
            "triumphant":  "epic lighting, heroic grand composition",
            "peaceful":    "soft natural light, serene calm",
            "fearful":     "harsh cold blue shadows, isolated",
            "suspenseful": "low key lighting, tense edge light",
            "joyful":      "vibrant warm colors, cheerful sunlight",
        }
        tone_kw = tone_keywords.get(scene.emotional_tone.value, "cinematic atmosphere")
        return (
            f"cinematic photography, {scene.visual_prompt[:200]}, "
            f"{tone_kw}, masterpiece, sharp focus, "
            f"professional color grading, dramatic lighting, high detail"
        )
