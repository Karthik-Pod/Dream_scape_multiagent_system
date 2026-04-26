"""
scripts/test_image_gen.py
──────────────────────────
Tests the ComfyUI image generation integration.

Run ComfyUI first:
    cd C:\\Users\\karth\\ComfyUI
    venv\\Scripts\\activate
    python main.py --force-fp16

Then run this test:
    cd DreamScape
    .venv\\Scripts\\activate
    python scripts/test_image_gen.py
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from rich.console import Console
from rich.panel import Panel
console = Console()


def test_comfyui_connection():
    console.print("\n[bold]Test 1: ComfyUI Connection[/bold]")
    try:
        from generation.image_gen import ImageGenerator
        gen = ImageGenerator()
        if gen.check_comfyui_running():
            console.print("  ✅ ComfyUI is running at http://127.0.0.1:8188")
            return True
        else:
            console.print("  ❌ ComfyUI not reachable.")
            console.print("  → Start it: cd C:\\Users\\karth\\ComfyUI && python main.py --force-fp16")
            return False
    except Exception as e:
        console.print(f"  ❌ Error: {e}")
        return False


def test_single_image():
    console.print("\n[bold]Test 2: Generate Single Scene Image[/bold]")
    try:
        from generation.image_gen import ImageGenerator
        from scene.schemas import Scene, Setting, EmotionalTone, Pacing, NarrationStyle

        # Create a minimal test scene
        test_scene = Scene(
            scene_id        = "test_story_scene_01",
            story_id        = "test_story",
            sequence_number = 1,
            title           = "Tiger's Mercy",
            setting         = Setting(
                location    = "dense jungle at dusk",
                time_of_day = "dusk",
                weather     = "humid",
                atmosphere  = "tense and primal",
                lighting    = "golden hour filtering through canopy",
            ),
            narration_text  = "A lone tiger stands at the edge of a clearing.",
            emotional_tone  = EmotionalTone.TENSE,
            pacing          = Pacing.FAST,
            tension_level   = 8,
            visual_prompt   = (
                "a majestic tiger standing at edge of jungle clearing at dusk, "
                "golden light filtering through dense canopy, mist rising from ground, "
                "photorealistic wildlife photography, dramatic shadows"
            ),
            negative_prompt = "blurry, cartoon, anime, low quality, watermark",
            narration_style = NarrationStyle.DRAMATIC,
            music_mood      = "tense orchestral",
            music_tempo     = "fast",
        )

        console.print(f"  Generating image for: [cyan]{test_scene.title}[/cyan]")
        console.print(f"  Prompt: [dim]{test_scene.visual_prompt[:80]}...[/dim]")
        console.print("  [yellow]This takes 20-60 seconds on your GPU...[/yellow]")

        gen  = ImageGenerator()
        path = gen.generate_for_scene(test_scene)

        if path and os.path.exists(path):
            size_kb = os.path.getsize(path) // 1024
            console.print(f"  ✅ Image generated: {path} ({size_kb} KB)")
            return True
        else:
            console.print("  ❌ Image file not found after generation.")
            return False

    except Exception as e:
        console.print(f"  ❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    console.print(Panel.fit(
        "[bold magenta]🌙 Dreamscape — Image Generation Test[/bold magenta]",
        border_style="magenta",
    ))

    connected = test_comfyui_connection()

    if not connected:
        console.print("\n[red]Start ComfyUI first, then re-run this test.[/red]")
        sys.exit(1)

    generated = test_single_image()

    console.print("\n[bold]═══ SUMMARY ═══[/bold]")
    console.print(f"  {'✅' if connected else '❌'}  ComfyUI Connection")
    console.print(f"  {'✅' if generated else '❌'}  Image Generation")

    if connected and generated:
        console.print("\n[bold green]✅ Image generation working! Run: python backend/main.py[/bold green]")
    else:
        console.print("\n[bold red]Fix errors above before running main.py[/bold red]")
