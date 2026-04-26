"""
backend/main.py
────────────────
DreamScape — Multi-Agent AI Storytelling Platform

CORRECT Pipeline Order:
  Phase 1  : Multi-agent story generation
  Phase 1B : Interactive story review loop
  Phase 2  : Scene pipeline (segment → structure → validate)
  Phase 3  : Image generation (Pollinations.AI — free, no key)
  Phase 4  : Audio generation FIRST (Kokoro TTS + MusicGen + mixer)
             ↑ Must happen before video so we have our audio ready
  Phase 5  : Video clip generation (Magic Hour — image → animated clip)
             Magic Hour generates clip with its own audio — we REPLACE it
  Phase 6  : Final video assembly (FFmpeg merges clip + OUR audio)

Run from DreamScape root:
    python backend/main.py
"""
import sys, os, json, uuid
sys.path.append(os.path.dirname(__file__))

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table

from agents.plot_agent import PlotAgent
from agents.character_agent import CharacterAgent
from agents.emotion_agent import EmotionAgent
from agents.visual_agent import VisualAgent
from agents.audio_agent import AudioAgent
from coordinator.round_manager import RoundManager
from memory.story_state import StoryState
from memory.character_profiles import CharacterProfileStore
from memory.world_bible import WorldBible
from scene.pipeline import ScenePipeline
from generation.image_gen import ImageGenerator
from generation.video_gen import VideoGenerator
from generation.tts_gen import TTSGenerator
from generation.music_gen import MusicGenerator
from assembly.audio_mixer import AudioMixer
from assembly.video_assembler import VideoAssembler
from config import get_settings

console = Console()


# ── Story Generation ───────────────────────────────────────────────────

def run_story_rounds(rounds, story_state, character_profiles, world_bible):
    agents = [
        PlotAgent(), CharacterAgent(), EmotionAgent(),
        VisualAgent(), AudioAgent(),
    ]
    manager = RoundManager(
        agents=agents,
        story_state=story_state,
        character_profiles=character_profiles,
        world_bible=world_bible,
        total_rounds=rounds,
    )
    manager.run_all_rounds()


# ── Story Review Loop ──────────────────────────────────────────────────

def story_review_loop(story_id, story_state, character_profiles, world_bible):
    while True:
        full_story = story_state.get_full_story()

        console.print("\n" + "=" * 60)
        console.print("[bold magenta]GENERATED STORY[/bold magenta]")
        console.print("=" * 60)
        console.print(full_story)
        console.print("\n" + "=" * 60)

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("[dim]Rounds[/dim]",     f"[cyan]{story_state.get_round()}[/cyan]")
        table.add_row("[dim]Word count[/dim]", f"[cyan]{len(full_story.split())}[/cyan]")
        arc = story_state.get_arc_history()
        if arc:
            table.add_row("[dim]Arc stage[/dim]", f"[yellow]{arc[-1]['arc']}[/yellow]")
        console.print(table)

        console.print("\n[bold cyan]What would you like to do?[/bold cyan]")
        console.print("  [green]1[/green] → Approve — continue to video production")
        console.print("  [yellow]2[/yellow] → Continue story (more rounds)")
        console.print("  [blue]3[/blue] → Add specific content")
        console.print("  [red]4[/red] → Start over")

        choice = Prompt.ask("\n[bold]Your choice[/bold]", choices=["1","2","3","4"], default="1")

        if choice == "1":
            console.print("\n[bold green]Story approved![/bold green]")
            return full_story

        elif choice == "2":
            extra = int(Prompt.ask("How many more rounds?", default="2"))
            run_story_rounds(extra, story_state, character_profiles, world_bible)

        elif choice == "3":
            console.print("\n[dim]Examples: 'Add a betrayal', 'Make ending hopeful', 'Add a villain'[/dim]")
            user_addition = Prompt.ask("[bold]What to add?[/bold]")
            from llm.client import call_llm
            import json as jmod
            system = """Write a new story segment incorporating the user's addition.
Respond ONLY in JSON: {"segment": "...", "emotional_tone": "...", "arc_stage": "..."}"""
            raw = call_llm(
                system,
                f"Story so far:\n{full_story[-800:]}\n\nAdd: {user_addition}",
                temperature=0.8, json_mode=True, model="smart"
            )
            try:
                data = jmod.loads(raw)
                if data.get("segment"):
                    story_state.add_segment(
                        text=data["segment"],
                        agent="UserDirected",
                        arc_stage=data.get("arc_stage", "rising_action"),
                        emotional_tone=data.get("emotional_tone", "mysterious"),
                    )
                    console.print("[green]Content added![/green]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        elif choice == "4":
            new_prompt = Prompt.ask("[bold]New story prompt[/bold]")
            new_rounds = int(Prompt.ask("Rounds?", default="3"))
            story_state.__init__(initial_prompt=new_prompt)
            character_profiles.__init__()
            world_bible.__init__()
            run_story_rounds(new_rounds, story_state, character_profiles, world_bible)


# ── Main Pipeline ──────────────────────────────────────────────────────

def main():
    console.print(Panel.fit(
        "[bold magenta]DREAMSCAPE[/bold magenta]\n"
        "[dim]Multi-Agent AI Storytelling Platform[/dim]",
        border_style="magenta",
    ))

    prompt   = Prompt.ask("\n[cyan]Enter your story prompt[/cyan]")
    rounds   = int(Prompt.ask("[cyan]Story rounds?[/cyan]", default="3"))
    story_id = f"story_{uuid.uuid4().hex[:8]}"
    console.print(f"[dim]Story ID: {story_id}[/dim]\n")

    os.makedirs("./storage/stories", exist_ok=True)
    os.makedirs("./storage/scenes",  exist_ok=True)

    # ── PHASE 1: Story Generation ──────────────────────────────────────
    console.print("[bold magenta]=== PHASE 1: STORY GENERATION ===[/bold magenta]")
    story_state        = StoryState(initial_prompt=prompt)
    character_profiles = CharacterProfileStore()
    world_bible        = WorldBible()
    run_story_rounds(rounds, story_state, character_profiles, world_bible)

    # ── PHASE 1B: Story Review ─────────────────────────────────────────
    console.print("\n[bold magenta]=== PHASE 1B: STORY REVIEW ===[/bold magenta]")
    full_story = story_review_loop(story_id, story_state, character_profiles, world_bible)

    with open(f"./storage/stories/{story_id}.json", "w") as f:
        json.dump(story_state.to_dict(), f, indent=2)
    console.print(f"[dim]Story saved: ./storage/stories/{story_id}.json[/dim]")

    # ── PHASE 2: Scene Pipeline ────────────────────────────────────────
    console.print("\n[bold cyan]=== PHASE 2: SCENE PIPELINE ===[/bold cyan]")
    pipeline   = ScenePipeline()
    scene_list = pipeline.run(
        story_text=full_story,
        story_id=story_id,
        character_profiles=character_profiles.get_all(),
    )
    console.print(f"[green]OK {scene_list.total_scenes} scenes structured[/green]")

    # ── PHASE 3: Image Generation (Pollinations.AI) ────────────────────
    console.print("\n[bold green]=== PHASE 3: IMAGE GENERATION ===[/bold green]")
    img_gen     = ImageGenerator()
    image_paths = {}

    if img_gen.check_comfyui_running():
        console.print("[green]OK Pollinations.AI ready[/green]")
        image_paths = img_gen.generate_for_all_scenes(scene_list.scenes)
        for scene in scene_list.scenes:
            path = image_paths.get(scene.sequence_number)
            if path:
                scene.image_path = path
                console.print(f"  [green]OK[/green] Scene {scene.sequence_number}: {os.path.basename(path)}")
            else:
                console.print(f"  [yellow]WARN[/yellow] Scene {scene.sequence_number}: failed — using fallback")

    # ── PHASE 4: Audio Generation ──────────────────────────────────────
    # MUST happen BEFORE video clip generation so our audio is ready
    console.print("\n[bold yellow]=== PHASE 4: AUDIO GENERATION ===[/bold yellow]")

    console.print("\n[yellow]Step 4a: TTS Narration...[/yellow]")
    tts_gen     = TTSGenerator()
    tts_results = tts_gen.generate_for_all_scenes(scene_list.scenes)
    for r in tts_results:
        if r.get("narration_path"):
            console.print(f"  [green]OK[/green] {os.path.basename(r['narration_path'])}")

    console.print("\n[yellow]Step 4b: Background Music...[/yellow]")
    music_gen   = MusicGenerator(model_size="small")
    music_paths = music_gen.generate_for_all_scenes(scene_list.scenes)
    for scene_num, path in music_paths.items():
        if path:
            console.print(f"  [green]OK[/green] Scene {scene_num}: {os.path.basename(path)}")

    console.print("\n[yellow]Step 4c: Mixing Audio...[/yellow]")
    mixer       = AudioMixer()
    mixed_audio = mixer.mix_all_scenes(story_id, tts_results, music_paths)
    for scene_num, path in mixed_audio.items():
        if path:
            scene = next((s for s in scene_list.scenes if s.sequence_number == scene_num), None)
            if scene:
                scene.audio_path = path
            console.print(f"  [green]OK[/green] Scene {scene_num}: {os.path.basename(path)}")

    # ── PHASE 5: Video Clip Generation (Magic Hour) ────────────────────
    # Runs AFTER audio so assembler can replace Magic Hour's audio with ours
    console.print("\n[bold green]=== PHASE 5: VIDEO CLIP GENERATION (MAGIC HOUR) ===[/bold green]")

    clip_paths         = {}
    scenes_with_images = [
        s for s in scene_list.scenes
        if image_paths.get(s.sequence_number)
    ]
    settings = get_settings()

    if not scenes_with_images:
        console.print("[yellow]WARNING No images — skipping video clips[/yellow]")
        console.print("[dim]Ken Burns effect on static images will be used[/dim]")
    elif not settings.magic_hour_api_key:
        console.print("[yellow]WARNING MAGIC_HOUR_API_KEY not set — skipping video clips[/yellow]")
        console.print("[dim]Get free key at magichour.ai/developer[/dim]")
    else:
        console.print(f"[green]OK Magic Hour ready — animating {len(scenes_with_images)} scenes[/green]")
        video_gen  = VideoGenerator()
        clip_paths = video_gen.generate_clips_for_all_scenes(
            scenes_with_images, image_paths
        )
        success = sum(1 for v in clip_paths.values() if v)
        console.print(f"[green]OK {success}/{len(scenes_with_images)} clips generated[/green]")
        for scene_num, path in clip_paths.items():
            if path:
                size_mb = os.path.getsize(path) / (1024 * 1024)
                console.print(f"  [green]OK[/green] Scene {scene_num}: {os.path.basename(path)} ({size_mb:.1f}MB)")
            else:
                console.print(f"  [yellow]WARN[/yellow] Scene {scene_num}: clip failed — using static image")

    # ── PHASE 6: Final Video Assembly ─────────────────────────────────
    # video_assembler will:
    # - If clip exists: strip Magic Hour audio, replace with our mixed audio
    # - If no clip: use static image with Ken Burns + our audio
    console.print("\n[bold blue]=== PHASE 6: VIDEO ASSEMBLY ===[/bold blue]")
    assembler = VideoAssembler()

    console.print("\n[blue]Step 6a: Assembling scene videos...[/blue]")
    scene_paths = assembler.assemble_all_scenes(
        scene_list.scenes,
        mixed_audio,
        clip_paths=clip_paths,
    )
    for path in scene_paths:
        if path:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            console.print(f"  [green]OK[/green] {os.path.basename(path)} ({size_mb:.1f}MB)")

    console.print("\n[blue]Step 6b: Stitching final video...[/blue]")
    final_video = assembler.stitch_final_video(story_id, scene_paths)
    size_mb     = os.path.getsize(final_video) / (1024 * 1024)
    console.print(f"  [green]OK[/green] Final: [bold]{os.path.basename(final_video)}[/bold] ({size_mb:.1f}MB)")

    # ── Save Metadata ──────────────────────────────────────────────────
    with open(f"./storage/scenes/{story_id}_scenes.json", "w") as f:
        json.dump(scene_list.model_dump(), f, indent=2, default=str)

    # ── Summary ────────────────────────────────────────────────────────
    console.print(f"\n[bold green]Pipeline Complete![/bold green]")
    console.print(f"  Story  : ./storage/stories/{story_id}.json")
    console.print(f"  Scenes : ./storage/scenes/{story_id}_scenes.json")
    console.print(f"  Images : ./storage/images/")
    console.print(f"  Clips  : ./storage/videos/clips/")
    console.print(f"  Audio  : ./storage/audio/")
    console.print(f"  Video  : [bold green]./storage/videos/{story_id}_final.mp4[/bold green]")


if __name__ == "__main__":
    main()
