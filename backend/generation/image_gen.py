"""
generation/image_gen.py  —  Pollinations.AI with smart retry
=============================================================
Gemini image gen requires paid key — skipped.
Pollinations is the only truly free option.

Fix for random 500s / timeouts:
- Longer timeout (90s)
- Longer waits between retries
- 4 different model endpoints (different server pools)
- PIL placeholder as final fallback — pipeline NEVER stops
"""
import sys, os, time, re, requests, hashlib
from urllib.parse import quote
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from config import get_settings
from scene.schemas import Scene


def _sanitize(prompt: str) -> str:
    p = re.sub(r'\bThe\s*,', '', prompt)
    p = re.sub(r',\s*,+', ',', p)
    p = re.sub(r',\s*\.', '.', p)
    p = re.sub(r'\s{2,}', ' ', p)
    return p.strip().strip(',').strip()


def _make_placeholder(out_path: str, scene: 'Scene') -> str:
    """Generate a gradient image locally — never fails."""
    from PIL import Image, ImageDraw
    tone_colors = {
        "tense":       ((20,20,40),   (80,20,20)),
        "ominous":     ((10,10,20),   (40,10,50)),
        "hopeful":     ((20,40,80),   (200,150,50)),
        "melancholic": ((30,30,50),   (60,60,80)),
        "mysterious":  ((10,20,40),   (40,20,80)),
        "triumphant":  ((40,20,10),   (180,120,20)),
        "peaceful":    ((20,60,80),   (80,160,120)),
        "fearful":     ((10,10,30),   (60,10,10)),
        "suspenseful": ((15,15,30),   (70,30,10)),
        "joyful":      ((40,80,160),  (220,160,40)),
    }
    c1, c2 = tone_colors.get(scene.emotional_tone.value, ((20,20,40),(60,40,80)))
    img  = Image.new("RGB", (1024, 1024))
    draw = ImageDraw.Draw(img)
    for y in range(1024):
        t = y / 1024
        draw.line([(0,y),(1024,y)], fill=(
            int(c1[0]+(c2[0]-c1[0])*t),
            int(c1[1]+(c2[1]-c1[1])*t),
            int(c1[2]+(c2[2]-c1[2])*t),
        ))
    try:
        draw.text((512, 490), scene.title[:35], fill=(255,255,255), anchor="mm")
        draw.text((512, 530), scene.emotional_tone.value, fill=(180,180,180), anchor="mm")
    except Exception:
        pass
    img.save(out_path)
    logger.warning(f"Placeholder image used for scene {scene.sequence_number}")
    return out_path


class ImageGenerator:
    # Different model endpoints = different Pollinations server pools
    # If one pool is having a bad day, others usually work
    # Pollinations model pool — different entries hit different server pools.
    # If you see 404 on a model, it may have been renamed — remove it from the list.
    # As of April 2026: flux, turbo, flux-realism are stable. flux-cablyai may be flux-pro.
    MODELS = [
        ("flux",          90),   # primary — most stable
        ("turbo",         60),   # fastest, good fallback
        ("flux-realism",  90),   # photorealistic pool
        ("flux-pro",      90),   # formerly flux-cablyai in some regions
    ]

    def __init__(self):
        self.settings   = get_settings()
        self.output_dir = os.path.join(self.settings.storage_base, "images")
        os.makedirs(self.output_dir, exist_ok=True)

    def check_comfyui_running(self) -> bool:
        logger.info("Image generator: Pollinations.AI (free, no key needed)")
        return True

    def _fetch(self, prompt: str, model: str,
               seed: int, out_path: str, timeout: int) -> str:
        """
        Fetch image from Pollinations.
        Returns: "ok" | "404" | "fail"
        404 = model renamed/removed → skip immediately, no wait
        fail = server error/timeout → wait before retry
        """
        url = (
            f"https://image.pollinations.ai/prompt/{quote(prompt)}"
            f"?width=1024&height=1024&model={model}"
            f"&seed={seed}&nologo=true"
        )
        try:
            resp = requests.get(url, timeout=timeout, stream=True)
            if resp.status_code == 404:
                logger.warning(f"404 [{model}] — model may be renamed, skipping")
                return "404"
            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code} [{model}]")
                return "fail"
            ct = resp.headers.get("content-type", "")
            if "image" not in ct:
                logger.warning(f"Non-image response [{model}]: {ct}")
                return "fail"
            with open(out_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            size_kb = os.path.getsize(out_path) / 1024
            if size_kb < 5:
                logger.warning(f"Image too small ({size_kb:.0f}KB) [{model}]")
                return "fail"
            logger.info(f"Image saved ({size_kb:.0f}KB) [{model}]")
            return "ok"
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout after {timeout}s [{model}]")
            return "fail"
        except Exception as e:
            logger.warning(f"Error [{model}]: {e}")
            return "fail"

    def generate_for_scene(self, scene: Scene) -> str | None:
        logger.info(f"Generating image {scene.sequence_number}: {scene.title}")

        prompt     = _sanitize(self._build_prompt(scene))
        # Story-consistent seed: same story always produces same visual flavor
        # story_seed is unique per story_id, scene offset keeps scenes distinct
        story_seed = int(hashlib.md5(scene.story_id.encode()).hexdigest(), 16) % 10**6
        seed       = story_seed + scene.sequence_number
        filename   = f"{scene.story_id}_scene_{scene.sequence_number:02d}.png"
        out_path = os.path.join(self.output_dir, filename)

        for i, (model, timeout) in enumerate(self.MODELS):
            logger.debug(f"Attempt {i+1}/{len(self.MODELS)}: model={model}")
            result = self._fetch(prompt, model, seed, out_path, timeout)
            if result == "ok":
                return out_path
            if i < len(self.MODELS) - 1:
                # Skip wait on 404 (model renamed) — wait on 500/timeout
                wait = 0 if result == "404" else [8, 12, 15, 0][i]
                if wait:
                    logger.info(f"Waiting {wait}s before next model...")
                    time.sleep(wait)

        # All models failed — use local placeholder
        # Pipeline continues normally with Ken Burns on placeholder
        logger.warning(f"All Pollinations models failed — using placeholder")
        try:
            return _make_placeholder(out_path, scene)
        except ImportError:
            logger.error("Pillow not installed: pip install Pillow")
            return None
        except Exception as e:
            logger.error(f"Placeholder failed: {e}")
            return None

    def generate_for_all_scenes(self, scenes: list[Scene]) -> dict[int, str]:
        results = {}
        for i, scene in enumerate(scenes):
            logger.info(f"Generating image {i+1}/{len(scenes)}: {scene.title}")
            path = self.generate_for_scene(scene)
            results[scene.sequence_number] = path
            if path:
                logger.info(f"Scene {scene.sequence_number} done.")
            else:
                logger.warning(f"Scene {scene.sequence_number} failed.")
            if i < len(scenes) - 1:
                time.sleep(6)  # 6s gap — free tier rate limit safety (2026)
        return results

    def _build_prompt(self, scene: Scene) -> str:
        tone_keywords = {
            "tense":       "high contrast shadows, dramatic tension",
            "ominous":     "dark foreboding atmosphere, deep shadows",
            "hopeful":     "warm golden light, uplifting brightness",
            "melancholic": "desaturated colors, soft somber lighting",
            "mysterious":  "ethereal mist, mysterious atmosphere",
            "triumphant":  "epic lighting, heroic grand composition",
            "peaceful":    "soft natural light, serene calm",
            "fearful":     "harsh cold blue shadows, isolated figure",
            "suspenseful": "low key lighting, tense edge light",
            "joyful":      "vibrant warm colors, cheerful sunlight",
        }
        tone_kw = tone_keywords.get(scene.emotional_tone.value, "cinematic atmosphere")
        return (
            f"cinematic photography, {scene.visual_prompt[:180]}, "
            f"{tone_kw}, masterpiece, sharp focus, "
            f"professional color grading, dramatic lighting, high detail"
        )
