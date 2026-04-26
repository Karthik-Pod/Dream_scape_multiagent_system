"""
scripts/test_video.py
──────────────────────
Tests the video assembly pipeline.

Prerequisites:
  - At least one scene image in storage/images/
  - At least one mixed audio in storage/audio/
  OR just runs with fallback (color background + narration)

Usage:
    cd DreamScape
    .venv\\Scripts\\activate
    python scripts/test_video.py
"""
import sys, os, glob
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from rich.console import Console
from rich.panel import Panel
console = Console()


def find_latest_story() -> tuple[str, list, dict]:
    """Find the most recent story's scenes JSON."""
    import json, glob

    scene_files = glob.glob("./storage/scenes/*_scenes.json")
    if not scene_files:
        return None, [], {}

    latest = max(scene_files, key=os.path.getmtime)
    with open(latest) as f:
        data = json.load(f)

    story_id = data.get("story_id", "unknown")

    # Reconstruct Scene objects
    from scene.schemas import Scene
    scenes = []
    for s in data.get("scenes", []):
        try:
            scenes.append(Scene(**s))
        except Exception as e:
            console.print(f"  [yellow]Warning: Could not load scene: {e}[/yellow]")

    # Find mixed audio files
    mixed_audio = {}
    for scene in scenes:
        pattern = f"./storage/audio/{story_id}_scene_{scene.sequence_number:02d}_mixed.wav"
        if os.path.exists(pattern):
            mixed_audio[scene.sequence_number] = pattern

    return story_id, scenes, mixed_audio


def test_single_scene_assembly():
    console.print("\n[bold]Test 1: Single Scene Video Assembly[/bold]")

    story_id, scenes, mixed_audio = find_latest_story()

    if not scenes:
        console.print("  [yellow]No scenes found. Running with test scene...[/yellow]")
        return test_with_mock_scene()

    scene = scenes[0]
    audio = mixed_audio.get(scene.sequence_number)

    console.print(f"  Scene: [cyan]{scene.title}[/cyan]")
    console.print(f"  Image: [dim]{scene.image_path or 'none (using fallback)'}[/dim]")
    console.print(f"  Audio: [dim]{audio or 'none (silent)'}[/dim]")
    console.print("  [yellow]Generating video clip (~30s)...[/yellow]")

    try:
        from assembly.video_assembler import VideoAssembler
        assembler = VideoAssembler()
        path      = assembler.assemble_scene(scene, audio)

        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            console.print(f"  ✅ Scene video: {os.path.basename(path)} ({size_mb:.1f}MB)")
            return story_id, scenes, mixed_audio, [path]
        else:
            console.print("  ❌ Video file not found after assembly")
            return None, [], {}, []
    except Exception as e:
        console.print(f"  ❌ Assembly failed: {e}")
        import traceback; traceback.print_exc()
        return None, [], {}, []


def test_with_mock_scene():
    """Test with a minimal mock scene when no real story exists."""
    from scene.schemas import Scene, Setting, EmotionalTone, Pacing, NarrationStyle, TimeOfDay

    scene = Scene(
        scene_id="test_story_scene_01",
        story_id="test_story",
        sequence_number=1,
        title="The Storm Arrives",
        setting=Setting(
            location="rocky coastline",
            time_of_day=TimeOfDay.NIGHT,
            weather="stormy",
            atmosphere="dark",
            lighting="lightning",
        ),
        narration_text="The storm rolled in from the north.",
        emotional_tone=EmotionalTone.OMINOUS,
        pacing=Pacing.SLOW,
        tension_level=7,
        visual_prompt="stormy coastline",
        narration_style=NarrationStyle.DRAMATIC,
        music_mood="dark orchestral",
        music_tempo="slow",
    )

    # Check for any existing audio
    audio = None
    if os.path.exists("./storage/audio/test_story_scene_01_mixed.wav"):
        audio = "./storage/audio/test_story_scene_01_mixed.wav"

    try:
        from assembly.video_assembler import VideoAssembler
        assembler = VideoAssembler()
        path      = assembler.assemble_scene(scene, audio)

        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            console.print(f"  ✅ Test video: {os.path.basename(path)} ({size_mb:.1f}MB)")
            return "test_story", [scene], {}, [path]
    except Exception as e:
        console.print(f"  ❌ Failed: {e}")
        import traceback; traceback.print_exc()
    return None, [], {}, []


def test_full_video_stitch(story_id, scenes, mixed_audio):
    console.print("\n[bold]Test 2: Full Story Video Stitch[/bold]")

    if not scenes or len(scenes) < 2:
        console.print("  [yellow]Need at least 2 scenes for stitch test — skipping[/yellow]")
        return False

    console.print(f"  Stitching {len(scenes)} scenes into final video...")
    console.print("  [yellow]This takes 1-3 minutes...[/yellow]")

    try:
        from assembly.video_assembler import VideoAssembler
        assembler   = VideoAssembler()
        scene_paths = assembler.assemble_all_scenes(scenes, mixed_audio)
        final_path  = assembler.stitch_final_video(story_id, scene_paths)

        if os.path.exists(final_path):
            size_mb = os.path.getsize(final_path) / (1024 * 1024)
            console.print(f"  ✅ Final video: {os.path.basename(final_path)} ({size_mb:.1f}MB)")
            console.print(f"  [green]📁 storage/videos/{os.path.basename(final_path)}[/green]")
            return True
        return False
    except Exception as e:
        console.print(f"  ❌ Stitch failed: {e}")
        import traceback; traceback.print_exc()
        return False


if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold magenta]🌙 Dreamscape — Video Assembly Test[/bold magenta]",
        border_style="magenta",
    ))

    result = test_single_scene_assembly()

    if isinstance(result, tuple) and result[0]:
        story_id, scenes, mixed_audio, _ = result
        stitched = test_full_video_stitch(story_id, scenes, mixed_audio)
    else:
        stitched = False

    scene_ok = isinstance(result, tuple) and bool(result[3])

    console.print("\n[bold]═══ SUMMARY ═══[/bold]")
    console.print(f"  {'✅' if scene_ok else '❌'}  Scene Video Assembly")
    console.print(f"  {'✅' if stitched else '⏭️ '}  Full Story Stitch")

    if scene_ok:
        console.print("\n[bold green]Video pipeline working![/bold green]")
        console.print("[dim]Check storage/videos/ for generated files[/dim]")
    else:
        console.print("\n[bold red]Fix errors above before running main.py[/bold red]")
