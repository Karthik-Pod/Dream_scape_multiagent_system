"""
backend/main.py
────────────────
DreamScape — Multi-Agent AI Storytelling Platform
Full story production loop with user feedback and continuation.
"""
import sys, os, json, uuid
sys.path.append(os.path.dirname(__file__))

from rich.console import Console
from rich.prompt import Prompt, Confirm
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

console = Console()


def run_story_generation(prompt: str, rounds: int, story_id: str,
                          story_state: StoryState, character_profiles: CharacterProfileStore,
                          world_bible: WorldBible) -> str:
    """Run multi-agent story generation rounds. Returns full story text."""
    agents = [
        PlotAgent(), CharacterAgent(), EmotionAgent(), VisualAgent(), AudioAgent(),
    ]
    manager = RoundManager(
        agents=agents,
        story_state=story_state,
        character_profiles=character_profiles,
        world_bible=world_bible,
        total_rounds=rounds,
    )
    manager.run_all_rounds()
    return story_state.get_full_story()


def story_review_loop(story_id: str, story_state: StoryState,
                       character_profiles: CharacterProfileStore,
                       world_bible: WorldBible) -> str:
    """
    Interactive story review loop.
    User can: approve story, add content, or continue story with more rounds.
    Returns final approved story text.
    """
    while True:
        full_story = story_state.get_full_story()

        console.print("\n" + "="*60)
        console.print("[bold magenta]GENERATED STORY[/bold magenta]")
        console.print("="*60)
        console.print(full_story)
        console.print("\n" + "="*60)

        # Show story stats
        table = Table(show_header=False, box=None, padding=(0,2))
        table.add_row("[dim]Rounds completed[/dim]", f"[cyan]{story_state.get_round()}[/cyan]")
        table.add_row("[dim]Total length[/dim]",     f"[cyan]{len(full_story.split())} words[/cyan]")
        arc_history = story_state.get_arc_history()
        if arc_history:
            last_arc = arc_history[-1]['arc']
            table.add_row("[dim]Current arc stage[/dim]", f"[yellow]{last_arc}[/yellow]")
        console.print(table)

        console.print("\n[bold cyan]What would you like to do?[/bold cyan]")
        console.print("  [green]1[/green] → Approve story and continue to video production")
        console.print("  [yellow]2[/yellow] → Continue story (add more rounds)")
        console.print("  [blue]3[/blue] → Add specific content to the story")
        console.print("  [red]4[/red] → Start over with a new prompt")

        choice = Prompt.ask("\n[bold]Your choice[/bold]", choices=["1","2","3","4"], default="1")

        if choice == "1":
            console.print("\n[bold green]Story approved! Moving to video production...[/bold green]")
            return full_story

        elif choice == "2":
            extra_rounds = int(Prompt.ask("How many more rounds?", default="2"))
            console.print(f"\n[cyan]Continuing story for {extra_rounds} more rounds...[/cyan]")
            agents = [PlotAgent(), CharacterAgent(), EmotionAgent(), VisualAgent(), AudioAgent()]
            manager = RoundManager(
                agents=agents,
                story_state=story_state,
                character_profiles=character_profiles,
                world_bible=world_bible,
                total_rounds=extra_rounds,
            )
            manager.run_all_rounds()

        elif choice == "3":
            console.print("\n[blue]Add specific content:[/blue]")
            console.print("  [dim]Examples:[/dim]")
            console.print("  [dim]- 'Add a plot twist where the hero discovers a secret'[/dim]")
            console.print("  [dim]- 'Make the ending more emotional'[/dim]")
            console.print("  [dim]- 'Add a new character called Marcus'[/dim]")

            user_addition = Prompt.ask("\n[bold]What would you like to add?[/bold]")

            # Add user content as a directed round
            console.print(f"\n[cyan]Incorporating your addition...[/cyan]")
            from llm.client import call_llm

            system = """You are a story continuation expert.
Given the current story and the user's requested addition, write a new story segment
that naturally incorporates the requested content.
Respond ONLY with valid JSON:
{
  "segment": "<200-400 word story continuation incorporating the user's request>",
  "emotional_tone": "<tense|hopeful|ominous|melancholic|triumphant|mysterious|peaceful>",
  "arc_stage": "<exposition|rising_action|climax|falling_action|resolution>"
}"""
            user_prompt = f"""Current story:
{full_story[-1000:]}

User wants to add: {user_addition}

Write a new segment that incorporates this naturally. Respond in JSON."""

            raw = call_llm(system, user_prompt, temperature=0.8, json_mode=True, model="smart")
            import json as json_mod
            try:
                data = json_mod.loads(raw)
                segment = data.get("segment", "")
                tone    = data.get("emotional_tone", "mysterious")
                arc     = data.get("arc_stage", "rising_action")
                if segment:
                    story_state.add_segment(
                        text=segment,
                        agent="UserDirected",
                        arc_stage=arc,
                        emotional_tone=tone,
                    )
                    console.print("[green]Content added successfully![/green]")
            except Exception as e:
                console.print(f"[red]Failed to add content: {e}[/red]")

        elif choice == "4":
            new_prompt = Prompt.ask("\n[bold]Enter new story prompt[/bold]")
            new_rounds = int(Prompt.ask("Story rounds?", default="3"))
            # Reset state
            story_state.__init__(initial_prompt=new_prompt)
            character_profiles.__init__()
            world_bible.__init__()
            console.print("\n[cyan]Starting fresh story...[/cyan]")
            run_story_generation(new_prompt, new_rounds, story_id,
                                  story_state, character_profiles, world_bible)


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

    # ── PHASE 1: Story Generation ─────────────────────────────────────
    console.print("[bold magenta]=== PHASE 1: STORY GENERATION ===[/bold magenta]")

    story_state        = StoryState(initial_prompt=prompt)
    character_profiles = CharacterProfileStore()
    world_bible        = WorldBible()

    run_story_generation(prompt, rounds, story_id, story_state, character_profiles, world_bible)

    os.makedirs("./storage/stories", exist_ok=True)

    # ── PHASE 1B: Story Review Loop ───────────────────────────────────
    console.print("\n[bold magenta]=== PHASE 1B: STORY REVIEW ===[/bold magenta]")
    full_story = story_review_loop(story_id, story_state, character_profiles, world_bible)

    # Save approved story
    with open(f"./storage/stories/{story_id}.json", "w") as f:
        json.dump(story_state.to_dict(), f, indent=2)
    console.print(f"[dim]Story saved: ./storage/stories/{story_id}.json[/dim]")

    # ── PHASE 2: Scene Pipeline ───────────────────────────────────────
    console.print("\n[bold cyan]=== PHASE 2: SCENE PIPELINE ===[/bold cyan]")
    pipeline   = ScenePipeline()
    scene_list = pipeline.run(
        story_text=full_story,
        story_id=story_id,
        character_profiles=character_profiles.get_all(),
    )
    console.print(f"[green]OK {scene_list.total_scenes} scenes structured[/green]")

    # ── PHASE 3: Image Generation ─────────────────────────────────────
    console.print("\n[bold green]=== PHASE 3: IMAGE GENERATION ===[/bold green]")
    img_gen     = ImageGenerator()
    image_paths = {}

    if img_gen.check_comfyui_running():
        console.print("[green]OK Image generator ready[/green]")
        image_paths = img_gen.generate_for_all_scenes(scene_list.scenes)
        for scene in scene_list.scenes:
            path = image_paths.get(scene.sequence_number)
            if path:
                scene.image_path = path
                console.print(f"  [green]OK[/green] Scene {scene.sequence_number}: {os.path.basename(path)}")
            else:
                console.print(f"  [yellow]WARN[/yellow] Scene {scene.sequence_number}: failed — using fallback")
    else:
        console.print("[yellow]WARNING HF_API_TOKEN not set — skipping image generation[/yellow]")

    # ── PHASE 3B: Video Clip Generation ──────────────────────────────
    console.print("\n[bold green]=== PHASE 3B: VIDEO CLIP GENERATION (MAGIC HOUR) ===[/bold green]")
    clip_paths         = {}
    scenes_with_images = [s for s in scene_list.scenes if image_paths.get(s.sequence_number)]

    if not scenes_with_images:
        console.print("[yellow]WARNING No images — skipping video clips[/yellow]")
    else:
        from config import get_settings
        if not get_settings().magic_hour_api_key:
            console.print("[yellow]WARNING MAGIC_HOUR_API_KEY not set — skipping video clips[/yellow]")
        else:
            video_gen  = VideoGenerator()
            clip_paths = video_gen.generate_clips_for_all_scenes(scenes_with_images, image_paths)
            success    = sum(1 for v in clip_paths.values() if v)
            console.print(f"[green]OK {success}/{len(scenes_with_images)} clips generated[/green]")

    # ── PHASE 4: Audio Generation ─────────────────────────────────────
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

    # ── PHASE 5: Video Assembly ───────────────────────────────────────
    console.print("\n[bold blue]=== PHASE 5: VIDEO ASSEMBLY ===[/bold blue]")
    assembler   = VideoAssembler()

    console.print("\n[blue]Step 5a: Assembling scene videos...[/blue]")
    scene_paths = assembler.assemble_all_scenes(
        scene_list.scenes, mixed_audio, clip_paths=clip_paths,
    )
    for path in scene_paths:
        if path:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            console.print(f"  [green]OK[/green] {os.path.basename(path)} ({size_mb:.1f}MB)")

    console.print("\n[blue]Step 5b: Stitching final video...[/blue]")
    final_video = assembler.stitch_final_video(story_id, scene_paths)
    size_mb     = os.path.getsize(final_video) / (1024 * 1024)
    console.print(f"  [green]OK[/green] Final: [bold]{os.path.basename(final_video)}[/bold] ({size_mb:.1f}MB)")

    # ── Save & Summary ────────────────────────────────────────────────
    os.makedirs("./storage/scenes", exist_ok=True)
    with open(f"./storage/scenes/{story_id}_scenes.json", "w") as f:
        json.dump(scene_list.model_dump(), f, indent=2, default=str)

    console.print(f"\n[bold green]Pipeline Complete![/bold green]")
    console.print(f"  Story  : ./storage/stories/{story_id}.json")
    console.print(f"  Scenes : ./storage/scenes/{story_id}_scenes.json")
    console.print(f"  Images : ./storage/images/")
    console.print(f"  Clips  : ./storage/videos/clips/")
    console.print(f"  Audio  : ./storage/audio/")
    console.print(f"  Video  : [bold green]./storage/videos/{story_id}_final.mp4[/bold green]")


if __name__ == "__main__":
    main()
