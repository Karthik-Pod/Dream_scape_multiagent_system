"""
scripts/test_agents.py
───────────────────────
Quick smoke test for the agent system.
Run this before starting main.py to verify:
  1. Groq API key is working
  2. All agents can call the LLM
  3. Structured JSON output is valid
  4. ChromaDB initializes correctly

Usage:
    cd dreamscape
    source .venv/bin/activate
    python scripts/test_agents.py
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from rich.console import Console
from rich.table import Table
import json

console = Console()


def test_llm_connection():
    console.print("\n[bold]Test 1: LLM Connection[/bold]")
    try:
        from llm.client import call_llm
        result = call_llm(
            system_prompt="You are a test agent. Respond only with valid JSON: {\"status\": \"ok\"}",
            user_prompt="Say ok",
            json_mode=True,
        )
        data = json.loads(result)
        assert data.get("status") == "ok"
        console.print("  ✅ Groq API connection working")
        return True
    except Exception as e:
        console.print(f"  ❌ LLM connection failed: {e}")
        console.print("  → Check your GROQ_API_KEY in .env")
        return False


def test_agents():
    console.print("\n[bold]Test 2: Agent Structured Output[/bold]")
    from agents.plot_agent import PlotAgent
    from agents.character_agent import CharacterAgent
    from agents.emotion_agent import EmotionAgent
    from agents.visual_agent import VisualAgent
    from agents.audio_agent import AudioAgent

    agents = [PlotAgent(), CharacterAgent(), EmotionAgent(), VisualAgent(), AudioAgent()]
    story = "A lone traveler arrives at an abandoned village at dusk."
    results = []

    table = Table(title="Agent Communication Test")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Intent (preview)", style="white")

    for agent in agents:
        try:
            output = agent.communicate(
                story_context=story,
                conversation_log=[],
                character_profiles={},
                world_bible={},
            )
            assert isinstance(output, dict), "Output must be a dict"
            assert "intent" in output, "Must have 'intent' key"
            table.add_row(agent.name, "✅ OK", output["intent"][:60] + "...")
            results.append(True)
        except Exception as e:
            table.add_row(agent.name, "❌ FAIL", str(e)[:60])
            results.append(False)

    console.print(table)
    return all(results)


def test_memory():
    console.print("\n[bold]Test 3: ChromaDB Memory[/bold]")
    try:
        from memory.chroma_store import ChromaStore
        store = ChromaStore()
        store.add_segment(
            segment_id="test_001",
            text="The traveler found an old map in the village.",
            metadata={"round": 1, "agent": "PlotAgent", "arc_stage": "exposition", "emotional_tone": "mysterious"},
        )
        results = store.search_segments("map discovery", n_results=1)
        assert len(results) > 0
        stats = store.get_collection_stats()
        console.print(f"  ✅ ChromaDB working | Stats: {stats}")
        return True
    except Exception as e:
        console.print(f"  ❌ ChromaDB failed: {e}")
        return False


def test_story_state():
    console.print("\n[bold]Test 4: Story State[/bold]")
    try:
        from memory.story_state import StoryState
        state = StoryState("A traveler arrives at dusk.")
        state.add_segment("The village was silent.", "PlotAgent", "exposition", "ominous")
        state.add_segment("A child appeared from shadows.", "CharacterAgent", "rising_action", "tense")
        assert state.get_round() == 2
        arc = state.get_arc_history()
        assert len(arc) == 2
        console.print(f"  ✅ StoryState working | Rounds: {state.get_round()}")
        return True
    except Exception as e:
        console.print(f"  ❌ StoryState failed: {e}")
        return False


if __name__ == "__main__":
    console.print("[bold magenta]🌙 Dreamscape - Agent System Test[/bold magenta]")
    console.print("=" * 50)

    results = {
        "LLM Connection": test_llm_connection(),
        "Agent Output":   test_agents(),
        "ChromaDB":       test_memory(),
        "Story State":    test_story_state(),
    }

    console.print("\n[bold]═══ SUMMARY ═══[/bold]")
    all_passed = True
    for test, passed in results.items():
        status = "[green]✅ PASS[/green]" if passed else "[red]❌ FAIL[/red]"
        console.print(f"  {status}  {test}")
        if not passed:
            all_passed = False

    if all_passed:
        console.print("\n[bold green]All tests passed! Run: cd backend && python main.py[/bold green]")
    else:
        console.print("\n[bold red]Some tests failed. Fix errors above before running main.py[/bold red]")
