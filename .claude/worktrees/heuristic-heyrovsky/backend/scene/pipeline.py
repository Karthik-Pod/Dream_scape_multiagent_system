"""
scene/pipeline.py
──────────────────
Main scene pipeline orchestrator.

Connects: SceneSegmenter → SceneStructurer → SceneValidator
Input:  story text (string) + story_id
Output: validated SceneList object saved to storage/scenes/

Usage:
    pipeline = ScenePipeline()
    scene_list = pipeline.run(story_text, story_id, character_profiles)
"""
import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from rich.console import Console
from rich.progress import track
from rich.panel import Panel
from rich.table import Table

from scene.segmenter import SceneSegmenter
from scene.structurer import SceneStructurer
from scene.validator import SceneValidator
from scene.schemas import Scene, SceneList
from config import get_settings

console = Console()


class ScenePipeline:
    def __init__(self):
        self.segmenter  = SceneSegmenter()
        self.structurer = SceneStructurer()
        self.validator  = SceneValidator()
        self.settings   = get_settings()

    def run(
        self,
        story_text: str,
        story_id: str,
        character_profiles: dict = None,
    ) -> SceneList:
        """
        Full pipeline: story text → validated SceneList.

        Args:
            story_text:         Complete story as a string.
            story_id:           Unique story identifier.
            character_profiles: Optional character data for consistency.

        Returns:
            SceneList — ready for multimodal generation.
        """
        console.print(Panel.fit(
            f"[bold cyan]🎬 SCENE PIPELINE[/bold cyan]\n"
            f"[dim]Story: {story_id}[/dim]",
            border_style="cyan",
        ))

        profiles = character_profiles or {}

        # ── STEP 1: Segmentation ──────────────────────────────────
        console.print("\n[bold yellow]Step 1: Segmenting story into scenes...[/bold yellow]")
        raw_scenes = self.segmenter.segment(story_text, story_id)
        console.print(f"  ✅ {len(raw_scenes)} scenes identified")

        # ── STEP 2: Structuring ───────────────────────────────────
        console.print("\n[bold yellow]Step 2: Structuring scenes...[/bold yellow]")
        scenes: list[Scene] = []

        for raw in track(raw_scenes, description="Structuring scenes..."):
            scene = self.structurer.structure(raw, profiles)
            scenes.append(scene)
            console.print(
                f"  [green]✅[/green] Scene {scene.sequence_number}: "
                f"[cyan]{scene.title}[/cyan] | "
                f"[yellow]{scene.emotional_tone.value}[/yellow] | "
                f"tension: {scene.tension_level}/10"
            )

        # ── STEP 3: Validation ────────────────────────────────────
        console.print("\n[bold yellow]Step 3: Validating scenes...[/bold yellow]")
        scene_list = SceneList(
            story_id=story_id,
            total_scenes=len(scenes),
            scenes=scenes,
        )
        validation = self.validator.validate(scene_list)

        if validation.issues:
            console.print(f"  [red]⚠️  {len(validation.issues)} issues found[/red]")
            for issue in validation.issues:
                console.print(f"    Scene {issue['scene']}: {issue['description']}")
        else:
            console.print("  [green]✅ All validation checks passed[/green]")

        if validation.warnings:
            for w in validation.warnings:
                console.print(f"  [yellow]⚠️  {w}[/yellow]")

        # ── STEP 4: Save to disk ──────────────────────────────────
        output_path = self._save(scene_list, story_id)
        console.print(f"\n[dim]Scenes saved to: {output_path}[/dim]")

        # ── STEP 5: Print summary table ───────────────────────────
        self._print_summary(scene_list)

        return scene_list

    def _save(self, scene_list: SceneList, story_id: str) -> str:
        """Save scene list as JSON to storage/scenes/."""
        scenes_dir = os.path.join(self.settings.storage_base, "scenes")
        os.makedirs(scenes_dir, exist_ok=True)

        output_path = os.path.join(scenes_dir, f"{story_id}_scenes.json")

        # Convert to dict for JSON serialization
        data = scene_list.model_dump()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path

    def _print_summary(self, scene_list: SceneList):
        """Print a formatted summary table of all scenes."""
        table = Table(title=f"Scene Summary — {scene_list.story_id}", show_lines=True)
        table.add_column("#",       style="cyan",   width=3)
        table.add_column("Title",   style="white",  width=25)
        table.add_column("Tone",    style="yellow", width=14)
        table.add_column("Tension", style="red",    width=8)
        table.add_column("Pacing",  style="green",  width=8)
        table.add_column("SFX",     style="dim",    width=20)

        for s in scene_list.scenes:
            table.add_row(
                str(s.sequence_number),
                s.title[:24],
                s.emotional_tone.value,
                f"{s.tension_level}/10",
                s.pacing.value,
                ", ".join(s.sfx_cues[:2]) if s.sfx_cues else "—",
            )

        console.print(table)
