"""
coordinator/round_manager.py
──────────────────────────────
Orchestrates the round-robin multi-agent storytelling loop.

DATA FLOW PER ROUND:
  1. Assemble context (story + memory + profiles)
  2. Communication phase: all agents broadcast intent (parallel-ready)
  3. Proposal phase: all agents write story segments
  4. Coordinator evaluates and selects winner
  5. Consistency check on chosen segment
  6. Update story state + memory
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from agents.coordinator_agent import CoordinatorAgent
from coordinator.conversation_log import ConversationLog
from memory.story_state import StoryState
from memory.character_profiles import CharacterProfileStore
from memory.world_bible import WorldBible

console = Console()


class RoundManager:
    def __init__(
        self,
        agents: list,
        story_state: StoryState,
        character_profiles: CharacterProfileStore,
        world_bible: WorldBible,
        total_rounds: int = 7,
    ):
        self.agents = agents
        self.story_state = story_state
        self.character_profiles = character_profiles
        self.world_bible = world_bible
        self.conversation_log = ConversationLog(window_size=10)
        self.coordinator = CoordinatorAgent(total_rounds=total_rounds)
        self.total_rounds = total_rounds

    def run_round(self) -> dict:
        """
        Execute one complete story generation round.
        Returns the result dict from the coordinator.
        """
        round_num = self.story_state.get_round() + 1
        console.print(f"\n[bold cyan]═══ ROUND {round_num} / {self.total_rounds} ═══[/bold cyan]")

        # ── Assemble shared context ───────────────────────────────
        story_context = self.story_state.get_full_story()
        profiles = self.character_profiles.get_all()
        world = self.world_bible.get_all()

        # ── PHASE 1: Communication ────────────────────────────────
        console.print("\n[bold yellow]📢 COMMUNICATION PHASE[/bold yellow]")
        for agent in self.agents:
            message = agent.communicate(
                story_context=story_context,
                conversation_log=self.conversation_log.get_recent(),
                character_profiles=profiles,
                world_bible=world,
            )
            self.conversation_log.add(agent.name, "communicate", message)

            intent = str(message.get("intent") or message.get("content") or message.get("proposal") or "")[:120]
            console.print(Panel(
                f"[white]{intent}[/white]",
                title=f"[green]{agent.name}[/green]",
                border_style="dim green",
            ))

        # ── PHASE 2: Proposals ────────────────────────────────────
        console.print("\n[bold yellow]✍️  PROPOSAL PHASE[/bold yellow]")
        proposals = {}
        for agent in self.agents:
            proposal = agent.propose(
                story_context=story_context,
                conversation_log=self.conversation_log.get_recent(),
                character_profiles=profiles,
                world_bible=world,
            )
            proposals[agent.name] = proposal
            self.conversation_log.add(agent.name, "propose", proposal)

            segment_preview = proposal.get("segment", "")[:100]
            console.print(f"[dim]  [{agent.name}]: {segment_preview}...[/dim]")

        # ── PHASE 3: Coordinator Evaluation ──────────────────────
        console.print("\n[bold yellow]⚖️  COORDINATOR EVALUATION[/bold yellow]")
        result = self.coordinator.evaluate_proposals(
            proposals=proposals,
            story_context=story_context,
            character_profiles=profiles,
        )

        chosen_agent = result["chosen_agent"]
        chosen_segment = result["chosen_segment"]
        arc_stage = result["arc_stage"]

        console.print(f"[bold green]✅ Selected: {chosen_agent}[/bold green] | Arc: [cyan]{arc_stage}[/cyan]")
        console.print(f"[dim]Reason: {result.get('reasoning', '')[:150]}[/dim]")

        # ── PHASE 4: Consistency Check ────────────────────────────
        consistency = self.coordinator.check_consistency(
            new_segment=chosen_segment,
            story_context=story_context,
            character_profiles=profiles,
        )

        if not consistency.get("is_consistent", True):
            issues = consistency.get("issues", [])
            console.print(f"[bold red]⚠️  Consistency issues: {issues}[/bold red]")
            logger.warning(f"Consistency issues in round {round_num}: {issues}")

        # ── PHASE 5: Update State ─────────────────────────────────
        self.story_state.add_segment(
            text=chosen_segment,
            agent=chosen_agent,
            arc_stage=arc_stage,
            emotional_tone=result["chosen_proposal"].get("emotional_tone", "neutral"),
        )

        # Update character profiles if the CharacterAgent made changes
        if chosen_agent == "CharacterAgent":
            updates = result["chosen_proposal"].get("character_updates", {})
            for char_name, update_note in updates.items():
                self.character_profiles.update(char_name, {"last_action": update_note})

        return result

    def run_all_rounds(self) -> str:
        """Run all rounds and return the complete story."""
        for i in range(self.total_rounds):
            self.run_round()

        full_story = self.story_state.get_full_story()
        console.print("\n[bold magenta]📖 STORY GENERATION COMPLETE[/bold magenta]")
        return full_story
