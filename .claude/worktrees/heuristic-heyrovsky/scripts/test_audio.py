"""
scripts/test_audio.py
──────────────────────
Tests TTS narration and music generation.

Usage:
    cd DreamScape
    .venv\\Scripts\\activate
    python scripts/test_audio.py
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from rich.console import Console
from rich.panel import Panel
console = Console()

# Test scene
def make_test_scene():
    from scene.schemas import (
        Scene, Setting, EmotionalTone, Pacing,
        NarrationStyle, TimeOfDay
    )
    return Scene(
        scene_id        = "test_story_scene_01",
        story_id        = "test_story",
        sequence_number = 1,
        title           = "The Storm Arrives",
        setting         = Setting(
            location    = "rocky coastline at night",
            time_of_day = TimeOfDay.NIGHT,
            weather     = "stormy",
            atmosphere  = "dark and foreboding",
            lighting    = "lightning flashes",
        ),
        narration_text  = (
            "The storm rolled in from the north, bringing with it a darkness "
            "that seemed to swallow the lighthouse whole. Sarah stood at the "
            "window, watching the waves crash against the rocks below. "
            "Something was out there. She could feel it."
        ),
        emotional_tone  = EmotionalTone.OMINOUS,
        pacing          = Pacing.SLOW,
        tension_level   = 7,
        visual_prompt   = "stormy coastline, lighthouse, dramatic waves",
        narration_style = NarrationStyle.DRAMATIC,
        music_mood      = "dark orchestral, stormy atmosphere, low brass",
        music_tempo     = "slow",
        sfx_cues        = ["howling wind", "crashing waves", "thunder"],
    )


def test_tts():
    console.print("\n[bold]Test 1: Kokoro TTS Narration[/bold]")
    try:
        from generation.tts_gen import TTSGenerator
        scene = make_test_scene()
        gen   = TTSGenerator()

        console.print("  [yellow]Generating narration (30-60s first run — downloading model)...[/yellow]")
        path  = gen.generate_narration(scene)

        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            duration = size_kb / 48  # rough estimate: 48KB/s for WAV
            console.print(f"  ✅ Narration generated: {os.path.basename(path)}")
            console.print(f"     Size: {size_kb:.0f}KB | Est. duration: {duration:.1f}s")
            return path
        else:
            console.print("  ❌ File not found after generation")
            return None
    except Exception as e:
        console.print(f"  ❌ TTS failed: {e}")
        import traceback; traceback.print_exc()
        return None


def test_music():
    console.print("\n[bold]Test 2: MusicGen Background Music[/bold]")
    try:
        from generation.music_gen import MusicGenerator
        scene = make_test_scene()
        gen   = MusicGenerator(model_size="small")

        console.print("  [yellow]Generating music (first run downloads ~2GB model)...[/yellow]")
        console.print("  [yellow]This takes 2-5 minutes. Please wait...[/yellow]")
        path  = gen.generate_for_scene(scene, duration_seconds=15)

        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            console.print(f"  ✅ Music generated: {os.path.basename(path)}")
            console.print(f"     Size: {size_kb:.0f}KB")
            return path
        else:
            console.print("  ❌ File not found after generation")
            return None
    except Exception as e:
        console.print(f"  ❌ Music generation failed: {e}")
        console.print("  [dim]Install: pip install transformers scipy[/dim]")
        return None


def test_mixer(narration_path, music_path):
    console.print("\n[bold]Test 3: Audio Mixer[/bold]")
    try:
        from assembly.audio_mixer import AudioMixer
        mixer = AudioMixer()
        path  = mixer.mix_scene_audio(
            story_id       = "test_story",
            scene_number   = 1,
            narration_path = narration_path,
            music_path     = music_path,
        )
        if os.path.exists(path):
            size_kb = os.path.getsize(path) / 1024
            console.print(f"  ✅ Mixed audio: {os.path.basename(path)} ({size_kb:.0f}KB)")
            return True
        return False
    except Exception as e:
        console.print(f"  ❌ Mixer failed: {e}")
        return False


if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold magenta]🌙 Dreamscape — Audio Pipeline Test[/bold magenta]",
        border_style="magenta",
    ))

    narration = test_tts()
    music     = test_music()

    mixed = False
    if narration:
        mixed = test_mixer(narration, music)

    console.print("\n[bold]═══ SUMMARY ═══[/bold]")
    console.print(f"  {'✅' if narration else '❌'}  TTS Narration (Kokoro)")
    console.print(f"  {'✅' if music else '❌'}  Music Generation (MusicGen)")
    console.print(f"  {'✅' if mixed else '❌'}  Audio Mixing")

    if narration and mixed:
        console.print("\n[bold green]Audio pipeline working![/bold green]")
        console.print(f"[dim]Check storage/audio/ for generated files[/dim]")
    else:
        console.print("\n[bold red]Fix errors above before running main.py[/bold red]")
