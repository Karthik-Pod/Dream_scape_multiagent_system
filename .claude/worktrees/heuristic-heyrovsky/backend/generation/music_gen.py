"""
generation/music_gen.py
────────────────────────
Background music generation using Meta's MusicGen.

MusicGen is:
  - Local (runs on your GPU)
  - Text-conditioned (takes mood descriptions as input)
  - Generates 10-30 second music clips

For each scene it generates a background music track
matched to the scene's music_mood descriptor.

Model sizes:
  - facebook/musicgen-small  (300M params, fast, good quality) ← we use this
  - facebook/musicgen-medium (1.5B params, slower, better)
  - facebook/musicgen-large  (3.3B params, best, needs 16GB+)
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from config import get_settings
from scene.schemas import Scene


class MusicGenerator:
    """
    Generates background music for scenes using MusicGen.
    Uses musicgen-small for RTX 3060/3070/3080 compatibility.
    """

    def __init__(self, model_size: str = "small"):
        self.settings   = get_settings()
        self.output_dir = os.path.join(self.settings.storage_base, "audio")
        self.model_size = model_size
        self._model     = None
        self._processor = None
        os.makedirs(self.output_dir, exist_ok=True)

    def _load_model(self):
        """Lazy-load MusicGen — large model, only load when needed."""
        if self._model is None:
            logger.info(f"Loading MusicGen-{self.model_size} model (first run downloads ~2GB)...")
            try:
                from transformers import AutoProcessor, MusicgenForConditionalGeneration
                import torch

                model_id = f"facebook/musicgen-{self.model_size}"
                self._processor = AutoProcessor.from_pretrained(model_id)
                self._model     = MusicgenForConditionalGeneration.from_pretrained(model_id)

                # Use GPU if available
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self._model = self._model.to(device)
                self._device = device

                logger.info(f"MusicGen loaded on {device}.")
            except ImportError:
                raise RuntimeError(
                    "transformers not installed. Run: pip install transformers torch"
                )
        return self._model, self._processor

    def generate_for_scene(self, scene: Scene, duration_seconds: int = 20) -> str:
        """
        Generate background music for a scene.

        Args:
            scene:            Scene with music_mood and emotional_tone.
            duration_seconds: Length of music clip (10-30s recommended).

        Returns:
            Path to generated WAV file.
        """
        logger.info(f"Generating music for scene {scene.sequence_number}: {scene.title}")

        model, processor = self._load_model()

        # Build music prompt from scene data
        music_prompt = self._build_music_prompt(scene)
        logger.debug(f"Music prompt: {music_prompt}")

        import torch
        import scipy.io.wavfile

        # Tokenize the text prompt
        inputs = processor(
            text=[music_prompt],
            padding=True,
            return_tensors="pt",
        ).to(self._device)

        # Generate audio tokens
        # tokens_per_second ≈ 50 for musicgen-small
        max_new_tokens = duration_seconds * 50

        with torch.no_grad():
            audio_values = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                guidance_scale=3.0,
            )

        # Convert to numpy and save
        sampling_rate = model.config.audio_encoder.sampling_rate
        audio_data    = audio_values[0, 0].cpu().numpy()

        filename    = f"{scene.story_id}_scene_{scene.sequence_number:02d}_music.wav"
        output_path = os.path.join(self.output_dir, filename)

        scipy.io.wavfile.write(output_path, rate=sampling_rate, data=audio_data)
        logger.info(f"Music saved: {output_path}")
        return output_path

    def generate_for_all_scenes(self, scenes: list[Scene]) -> dict[int, str]:
        """
        Generate music for all scenes.
        Returns {sequence_number: audio_path}
        """
        results = {}
        total   = len(scenes)

        for i, scene in enumerate(scenes):
            logger.info(f"Music {i+1}/{total}: {scene.title}")
            try:
                path = self.generate_for_scene(scene)
                results[scene.sequence_number] = path
            except Exception as e:
                logger.error(f"Music failed for scene {scene.sequence_number}: {e}")
                results[scene.sequence_number] = None

        return results

    def _build_music_prompt(self, scene: Scene) -> str:
        """
        Build a detailed music generation prompt from scene data.
        MusicGen responds well to instrument + mood + tempo descriptions.
        """
        # Tone to instrument/style mapping
        tone_styles = {
            "tense":       "tense orchestral strings, low brass, suspenseful, no melody",
            "ominous":     "dark ambient drone, deep bass, eerie atmosphere, minimal",
            "hopeful":     "uplifting piano, warm strings, gentle and optimistic",
            "melancholic": "solo cello, minor key, slow and sorrowful, sparse piano",
            "triumphant":  "epic orchestral, full brass, soaring strings, heroic",
            "mysterious":  "ambient electronic, soft pads, mysterious, subtle melody",
            "peaceful":    "acoustic guitar, nature sounds, calm and serene, gentle",
            "fearful":     "dissonant strings, rapid percussion, horror atmosphere",
            "suspenseful": "staccato strings, building tension, thriller style",
            "joyful":      "upbeat acoustic, light percussion, cheerful and bright",
        }

        tone_style = tone_styles.get(scene.emotional_tone.value, "ambient atmospheric music")

        # Combine with scene's own music_mood descriptor
        prompt = f"{scene.music_mood}, {tone_style}, {scene.music_tempo} tempo, cinematic soundtrack"
        return prompt
