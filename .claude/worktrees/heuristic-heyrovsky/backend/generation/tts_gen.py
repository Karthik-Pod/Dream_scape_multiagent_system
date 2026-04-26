"""
generation/tts_gen.py
──────────────────────
Text-to-Speech narration using Kokoro TTS (local, offline, free).
"""
import sys, os, re, json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from config import get_settings
from scene.schemas import Scene, NarrationStyle

# ── Kokoro model files — resolve relative to DreamScape ROOT ─────────
# main.py runs from DreamScape/ so __file__ here is backend/generation/tts_gen.py
# Root = two levels up from this file
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KOKORO_MODEL  = os.path.join(_ROOT, "kokoro-v0_19.onnx")
KOKORO_VOICES = os.path.join(_ROOT, "voices.bin")

NARRATION_VOICES = {
    NarrationStyle.CALM:        "af_sarah",
    NarrationStyle.DRAMATIC:    "am_michael",
    NarrationStyle.URGENT:      "am_adam",
    NarrationStyle.WHISPERED:   "af_bella",
    NarrationStyle.MELANCHOLIC: "bf_emma",
}

CHARACTER_VOICES = [
    "am_adam", "af_bella", "bm_george",
    "bf_emma", "am_michael", "af_sarah",
]


class TTSGenerator:
    def __init__(self):
        self.settings   = get_settings()
        self.output_dir = os.path.join(self.settings.storage_base, "audio")
        os.makedirs(self.output_dir, exist_ok=True)
        self._pipeline        = None
        self._char_voice_map: dict[str, str] = {}

    def _get_pipeline(self):
        if self._pipeline is None:
            logger.info(f"Loading Kokoro TTS from: {KOKORO_MODEL}")
            if not os.path.exists(KOKORO_MODEL):
                raise FileNotFoundError(
                    f"Kokoro model not found at {KOKORO_MODEL}\n"
                    f"Expected kokoro-v0_19.onnx and voices.bin in DreamScape root."
                )
            from kokoro_onnx import Kokoro
            self._pipeline = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
            logger.info("Kokoro TTS loaded successfully.")
        return self._pipeline

    def generate_narration(self, scene: Scene) -> str:
        logger.info(f"Generating narration for scene {scene.sequence_number}: {scene.title}")
        pipeline = self._get_pipeline()
        voice    = NARRATION_VOICES.get(scene.narration_style, "af_sarah")
        text     = self._clean_text(scene.narration_text)

        filename    = f"{scene.story_id}_scene_{scene.sequence_number:02d}_narration.wav"
        output_path = os.path.join(self.output_dir, filename)
        self._synthesize(pipeline, text, voice, output_path)
        logger.info(f"Narration saved: {output_path}")
        return output_path

    def generate_dialogue(self, scene: Scene) -> list[dict]:
        if not scene.dialogue:
            return []
        pipeline = self._get_pipeline()
        results  = []
        for i, line in enumerate(scene.dialogue):
            voice = self._get_character_voice(line.character)
            text  = self._clean_text(line.text)
            filename = (
                f"{scene.story_id}_scene_{scene.sequence_number:02d}"
                f"_dialogue_{i:02d}_{line.character.replace(' ', '_')}.wav"
            )
            output_path = os.path.join(self.output_dir, filename)
            self._synthesize(pipeline, text, voice, output_path)
            results.append({
                "character":  line.character,
                "text":       line.text,
                "emotion":    line.emotion,
                "audio_path": output_path,
            })
        return results

    def generate_for_scene(self, scene: Scene) -> dict:
        result = {"scene_id": scene.scene_id, "narration_path": None, "dialogue": []}
        try:
            result["narration_path"] = self.generate_narration(scene)
        except Exception as e:
            logger.error(f"Narration failed for scene {scene.sequence_number}: {e}")
        try:
            result["dialogue"] = self.generate_dialogue(scene)
        except Exception as e:
            logger.error(f"Dialogue failed for scene {scene.sequence_number}: {e}")
        return result

    def generate_for_all_scenes(self, scenes: list[Scene]) -> list[dict]:
        results = []
        for i, scene in enumerate(scenes):
            logger.info(f"Audio {i+1}/{len(scenes)}: {scene.title}")
            result = self.generate_for_scene(scene)
            results.append(result)
            logger.info(f"Scene {scene.sequence_number} audio done.")
        return results

    def _synthesize(self, pipeline, text: str, voice: str, output_path: str) -> None:
        import soundfile as sf
        samples, sample_rate = pipeline.create(text, voice=voice, speed=1.0, lang="en-us")
        if samples is None or len(samples) == 0:
            raise RuntimeError(f"No audio generated for: {text[:50]}")
        sf.write(output_path, samples, samplerate=sample_rate)

    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'_+', '', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n+', ' ', text)
        return text.strip()

    def _get_character_voice(self, character_name: str) -> str:
        if character_name not in self._char_voice_map:
            idx = len(self._char_voice_map) % len(CHARACTER_VOICES)
            self._char_voice_map[character_name] = CHARACTER_VOICES[idx]
        return self._char_voice_map[character_name]
