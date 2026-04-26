"""
scripts/test_scene_pipeline.py
────────────────────────────────
Tests the scene pipeline in isolation using a sample story.
Run this BEFORE main.py to verify scene generation works.

Usage:
    cd DreamScape
    python scripts/test_scene_pipeline.py
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from rich.console import Console
console = Console()

SAMPLE_STORY = """
A lone astronaut discovers an abandoned space station orbiting a dying star.

As the astronaut ventured deeper into the space station, they stumbled upon a cryptic log entry
from the station's commander. The message spoke of Project Erebus — a top-secret experiment
meant to harness the dying star's energy. But something had gone horribly wrong.

The astronaut leaned in, trying to make out a distorted voice on the comms system.
'Hello?' they ventured, voice barely above a whisper. The voice on the other end
crackled and faded, only to return with a low, labored tone. 'P-please... help... me...'

As the astronaut's grip tightened on the console, the voice grew louder, more insistent.
'Stop... Erebus...' And then, like a cold breeze on a winter's night, the comms went silent.
The astronaut was left standing alone in the darkness.
""".strip()


def test_segmenter():
    console.print("\n[bold]Test 1: Scene Segmenter[/bold]")
    try:
        from scene.segmenter import SceneSegmenter
        seg = SceneSegmenter()
        scenes = seg.segment(SAMPLE_STORY, "test_story_001")
        assert len(scenes) >= 2, "Should produce at least 2 scenes"
        console.print(f"  ✅ Segmented into {len(scenes)} scenes")
        for s in scenes:
            console.print(f"     Scene {s['scene_number']}: {s['suggested_title']}")
        return scenes
    except Exception as e:
        console.print(f"  ❌ Segmenter failed: {e}")
        return None


def test_structurer(raw_scenes):
    console.print("\n[bold]Test 2: Scene Structurer[/bold]")
    try:
        from scene.structurer import SceneStructurer
        struct = SceneStructurer()
        scene = struct.structure(raw_scenes[0], {})
        assert scene.visual_prompt, "visual_prompt must not be empty"
        assert scene.narration_text, "narration_text must not be empty"
        console.print(f"  ✅ Scene structured: {scene.title}")
        console.print(f"     Tone: {scene.emotional_tone.value} | Tension: {scene.tension_level}/10")
        console.print(f"     Visual prompt: {scene.visual_prompt[:80]}...")
        console.print(f"     Music mood: {scene.music_mood}")
        console.print(f"     SFX cues: {scene.sfx_cues}")
        return True
    except Exception as e:
        console.print(f"  ❌ Structurer failed: {e}")
        return False


def test_full_pipeline():
    console.print("\n[bold]Test 3: Full Pipeline[/bold]")
    try:
        from scene.pipeline import ScenePipeline
        pipeline = ScenePipeline()
        scene_list = pipeline.run(SAMPLE_STORY, "test_story_001")
        assert scene_list.total_scenes >= 1
        console.print(f"  ✅ Full pipeline: {scene_list.total_scenes} scenes generated and saved")
        return True
    except Exception as e:
        console.print(f"  ❌ Pipeline failed: {e}")
        return False


if __name__ == "__main__":
    console.print("[bold magenta]🌙 Dreamscape — Scene Pipeline Test[/bold magenta]")
    console.print("=" * 50)

    raw_scenes = test_segmenter()
    structured  = test_structurer(raw_scenes) if raw_scenes else False
    pipeline    = test_full_pipeline()

    console.print("\n[bold]═══ SUMMARY ═══[/bold]")
    console.print(f"  {'✅' if raw_scenes else '❌'}  Segmenter")
    console.print(f"  {'✅' if structured else '❌'}  Structurer")
    console.print(f"  {'✅' if pipeline else '❌'}  Full Pipeline")

    if all([raw_scenes, structured, pipeline]):
        console.print("\n[bold green]All tests passed! Run: python backend/main.py[/bold green]")
    else:
        console.print("\n[bold red]Some tests failed. Check errors above.[/bold red]")
