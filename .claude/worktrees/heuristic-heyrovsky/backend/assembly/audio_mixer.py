"""
assembly/audio_mixer.py
────────────────────────
Mixes narration + music into a single scene audio track.
Uses numpy + soundfile only — no FFmpeg required.

Mixing strategy:
  - Narration: primary layer (full volume)
  - Music: background layer (ducked to 20% volume)
  - Music is looped/trimmed to match narration length
  - Music fades in/out at boundaries
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import soundfile as sf
from loguru import logger
from config import get_settings


class AudioMixer:
    """
    Mixes narration + music WAV files using numpy.
    No FFmpeg dependency — pure Python audio mixing.
    """

    def __init__(self):
        self.settings   = get_settings()
        self.output_dir = os.path.join(self.settings.storage_base, "audio")
        os.makedirs(self.output_dir, exist_ok=True)

    def mix_scene_audio(
        self,
        story_id: str,
        scene_number: int,
        narration_path: str,
        music_path: str = None,
        music_volume: float = 0.18,
    ) -> str:
        """
        Mix narration + background music into one WAV file.

        Args:
            story_id:       Story identifier.
            scene_number:   Scene sequence number.
            narration_path: Path to narration WAV.
            music_path:     Path to music WAV (optional).
            music_volume:   Music volume as fraction of narration (0.18 = 18%).

        Returns:
            Path to the mixed WAV file.
        """
        logger.info(f"Mixing audio for scene {scene_number}...")

        # Load narration
        narration, nar_sr = sf.read(narration_path, dtype='float32')

        # Normalize to mono if stereo
        if narration.ndim > 1:
            narration = narration.mean(axis=1)

        # If no music, return narration as-is
        if not music_path or not os.path.exists(music_path):
            logger.warning(f"Scene {scene_number}: No music. Using narration only.")
            filename    = f"{story_id}_scene_{scene_number:02d}_mixed.wav"
            output_path = os.path.join(self.output_dir, filename)
            sf.write(output_path, narration, nar_sr)
            return output_path

        # Load music
        music, music_sr = sf.read(music_path, dtype='float32')
        if music.ndim > 1:
            music = music.mean(axis=1)

        # Resample music to match narration sample rate if needed
        if music_sr != nar_sr:
            music = self._resample(music, music_sr, nar_sr)

        nar_len   = len(narration)
        music_len = len(music)

        # Loop music if shorter than narration
        if music_len < nar_len:
            repeats = (nar_len // music_len) + 1
            music   = np.tile(music, repeats)

        # Trim music to narration length
        music = music[:nar_len]

        # Apply fade in (1.5s) and fade out (2s) to music
        fade_in_samples  = int(1.5 * nar_sr)
        fade_out_samples = int(2.0 * nar_sr)

        fade_in  = np.linspace(0, 1, min(fade_in_samples, nar_len))
        fade_out = np.linspace(1, 0, min(fade_out_samples, nar_len))

        music[:len(fade_in)]  *= fade_in
        music[-len(fade_out):] *= fade_out

        # Duck music volume
        music *= music_volume

        # Mix: narration + background music
        mixed = narration + music

        # Normalize to prevent clipping
        max_val = np.abs(mixed).max()
        if max_val > 1.0:
            mixed = mixed / max_val * 0.95

        filename    = f"{story_id}_scene_{scene_number:02d}_mixed.wav"
        output_path = os.path.join(self.output_dir, filename)
        sf.write(output_path, mixed, nar_sr)

        logger.info(f"Mixed audio saved: {output_path}")
        return output_path

    def mix_all_scenes(
        self,
        story_id: str,
        tts_results: list[dict],
        music_paths: dict[int, str],
    ) -> dict[int, str]:
        """Mix audio for all scenes."""
        results = {}

        for tts in tts_results:
            scene_id  = tts.get("scene_id", "")
            try:
                scene_num = int(scene_id.split("_scene_")[-1])
            except (ValueError, IndexError):
                continue

            narration = tts.get("narration_path")
            music     = music_paths.get(scene_num)

            if not narration or not os.path.exists(narration):
                logger.warning(f"Scene {scene_num}: No narration file.")
                continue

            try:
                mixed = self.mix_scene_audio(
                    story_id=story_id,
                    scene_number=scene_num,
                    narration_path=narration,
                    music_path=music,
                )
                results[scene_num] = mixed
            except Exception as e:
                logger.error(f"Mixing failed for scene {scene_num}: {e}")
                results[scene_num] = narration  # fallback to narration only

        return results

    def _resample(self, audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Simple linear resampling when sample rates differ."""
        ratio      = target_sr / orig_sr
        new_length = int(len(audio) * ratio)
        old_indices = np.linspace(0, len(audio) - 1, new_length)
        return np.interp(old_indices, np.arange(len(audio)), audio).astype(np.float32)
