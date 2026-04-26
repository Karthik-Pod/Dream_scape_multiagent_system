"""
assembly/video_assembler.py
────────────────────────────
Assembles final video from scene images/clips + audio.
Uses FFmpeg directly via subprocess — most reliable cross-platform approach.

Pipeline per scene:
  1. Kling clip + audio → scene MP4  (if clip available)
  2. image + audio → scene MP4       (fallback with Ken Burns zoom)
  3. All scene MP4s → final story MP4 (ffmpeg concat)
"""
import sys, os, subprocess
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from config import get_settings
from scene.schemas import Scene


def get_ffmpeg() -> str:
    try:
        import imageio_ffmpeg
        path = imageio_ffmpeg.get_ffmpeg_exe()
        logger.debug(f"Using imageio_ffmpeg: {path}")
        return path
    except Exception:
        return "ffmpeg"


class VideoAssembler:
    FPS        = 24
    RESOLUTION = "768:768"

    def __init__(self):
        self.settings   = get_settings()
        self.output_dir = os.path.join(self.settings.storage_base, "videos")
        self.ffmpeg     = get_ffmpeg()
        os.makedirs(self.output_dir, exist_ok=True)

    def assemble_all_scenes(self, scenes: list, mixed_audio: dict, clip_paths: dict = None) -> list:
        """
        Assemble MP4 for every scene.
        clip_paths: {sequence_number: kling_clip_path} — falls back to static image if None
        """
        clip_paths = clip_paths or {}
        paths      = []
        for scene in scenes:
            audio_path = mixed_audio.get(scene.sequence_number)
            clip_path  = clip_paths.get(scene.sequence_number)
            path = self.assemble_scene(scene=scene, audio_path=audio_path, clip_path=clip_path)
            paths.append(path)
        return paths

    def assemble_scene(self, scene: Scene, audio_path: str = None, clip_path: str = None) -> str:
        """
        Create scene MP4.
        Priority: Kling clip > static image+audio > static image only
        """
        logger.info(f"Assembling scene {scene.sequence_number}: {scene.title}")

        audio = audio_path or getattr(scene, "audio_path", None)
        if audio and not os.path.exists(audio):
            audio = None

        filename    = f"{scene.story_id}_scene_{scene.sequence_number:02d}.mp4"
        output_path = os.path.join(self.output_dir, filename)

        if clip_path and os.path.exists(clip_path):
            logger.info(f"Using Kling clip for scene {scene.sequence_number}")
            if audio and os.path.exists(audio):
                self._clip_audio_to_video(clip_path, audio, output_path)
            else:
                self._copy_clip(clip_path, output_path)
        else:
            image_path = (
                scene.image_path
                if scene.image_path and os.path.exists(scene.image_path or "")
                else None
            )
            if not image_path:
                image_path = self._create_fallback_image(scene)
            if audio and os.path.exists(audio):
                self._image_audio_to_video(image_path, audio, output_path)
            else:
                self._image_to_video(image_path, output_path, duration=8)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"Scene video saved: {output_path} ({size_mb:.1f}MB)")
            return output_path
        else:
            raise RuntimeError(f"FFmpeg produced empty/missing file: {output_path}")

    def stitch_final_video(self, story_id: str, scene_paths: list) -> str:
        """Concatenate all scene MP4s into final video using FFmpeg concat."""
        logger.info(f"Stitching {len(scene_paths)} scenes...")

        valid = [p for p in scene_paths if p and os.path.exists(p)]
        if not valid:
            raise RuntimeError("No valid scene clips to stitch.")

        list_path = os.path.join(self.output_dir, f"{story_id}_concat.txt")
        with open(list_path, "w") as f:
            for path in valid:
                abs_path = os.path.abspath(path).replace(chr(92), "/")
                f.write("file '" + abs_path + "'\n")

        output_path = os.path.join(self.output_dir, f"{story_id}_final.mp4")
        cmd = [
            self.ffmpeg, "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_path,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            output_path
        ]
        self._run(cmd)
        os.remove(list_path)

        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Final video: {output_path} ({size_mb:.1f}MB)")
        return output_path

    def _clip_audio_to_video(self, clip_path: str, audio_path: str, output_path: str):
        """
        Merge animated clip with OUR audio — strips Magic Hour generated audio.
        Uses -map 0:v to take video from clip, -map 1:a to take audio from our mix.
        This ensures our TTS narration + music plays, not Magic Hour AI audio.
        """
        cmd = [
            self.ffmpeg, "-y",
            "-i", clip_path,    # input 0: Magic Hour video clip
            "-i", audio_path,   # input 1: our mixed narration+music
            "-map", "0:v",    # take VIDEO from clip (strip Magic Hour audio)
            "-map", "1:a",    # take AUDIO from our mix
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",        # end at shorter of video/audio
            "-movflags", "+faststart",
            output_path
        ]
        self._run(cmd)

    def _copy_clip(self, clip_path: str, output_path: str):
        """Re-encode clip without audio."""
        cmd = [
            self.ffmpeg, "-y", "-i", clip_path,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an", "-movflags", "+faststart",
            output_path
        ]
        self._run(cmd)

    def _image_audio_to_video(self, image_path: str, audio_path: str, output_path: str):
        """Static image + audio → MP4 with Ken Burns zoom."""
        cmd = [
            self.ffmpeg, "-y",
            "-loop", "1", "-i", image_path,
            "-i", audio_path,
            "-filter_complex",
            f"[0:v]zoompan=z='min(zoom+0.0002,1.05)':d=1:s=768x768:fps={self.FPS},format=yuv420p[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest", "-movflags", "+faststart",
            output_path
        ]
        self._run(cmd)

    def _image_to_video(self, image_path: str, output_path: str, duration: int = 8):
        """Static image → silent MP4 (last resort fallback)."""
        cmd = [
            self.ffmpeg, "-y",
            "-loop", "1", "-i", image_path,
            "-filter_complex",
            f"[0:v]zoompan=z='min(zoom+0.0002,1.05)':d=1:s=768x768:fps={self.FPS},format=yuv420p[v]",
            "-map", "[v]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-t", str(duration), "-movflags", "+faststart",
            output_path
        ]
        self._run(cmd)

    def _run(self, cmd: list):
        logger.debug(f"FFmpeg: {' '.join(cmd[-6:])}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg stderr: {result.stderr[-500:]}")
            raise RuntimeError(f"FFmpeg failed (code {result.returncode})")

    def _create_fallback_image(self, scene: Scene) -> str:
        from PIL import Image, ImageDraw
        tone_colors = {
            "tense": (20,10,10), "ominous": (10,10,20),
            "hopeful": (20,30,40), "melancholic": (15,15,25),
            "mysterious": (10,15,20), "triumphant": (25,20,10),
            "peaceful": (15,25,20), "fearful": (20,5,5),
            "suspenseful": (15,10,5), "joyful": (25,25,15),
        }
        tone  = scene.emotional_tone.value if scene.emotional_tone else "mysterious"
        color = tone_colors.get(tone, (15,15,25))
        img   = Image.new("RGB", (768, 768), color)
        draw  = ImageDraw.Draw(img)
        draw.text((384, 384), scene.title, fill=(180,180,180), anchor="mm")
        temp  = os.path.join(self.output_dir, f"_fallback_{scene.sequence_number}.png")
        img.save(temp)
        return temp
