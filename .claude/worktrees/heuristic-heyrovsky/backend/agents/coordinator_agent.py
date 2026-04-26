"""
agents/coordinator_agent.py
─────────────────────────────
The Coordinator Agent — the most important agent in DreamScape.

Responsibilities (from thesis):
  1. Evaluate all agent proposals using LLM scoring
  2. Detect narrative contradictions
  3. Select the best proposal or synthesize a merged output
  4. Update shared memory after each round
  5. Track narrative arc position (exposition → climax → resolution)
"""
import sys, os, json
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from llm.client import call_llm
from loguru import logger


# Narrative arc stages — coordinator uses these to guide agent selection
ARC_STAGES = [
    "exposition",       # Round 1: setup world, introduce characters
    "rising_action",    # Rounds 2-4: escalate conflict
    "climax",           # Round 5: peak tension
    "falling_action",   # Round 6: consequences
    "resolution",       # Round 7+: wrap up
]


class CoordinatorAgent:
    name = "CoordinatorAgent"

    def __init__(self, total_rounds: int = 7):
        self.total_rounds = total_rounds
        self.current_round = 0

    def get_arc_stage(self) -> str:
        """Map current round to narrative arc position."""
        idx = min(
            int((self.current_round / self.total_rounds) * len(ARC_STAGES)),
            len(ARC_STAGES) - 1
        )
        return ARC_STAGES[idx]

    def evaluate_proposals(
        self,
        proposals: dict[str, dict],
        story_context: str,
        character_profiles: dict,
    ) -> dict:
        """
        LLM-scored proposal evaluation.
        Scores each proposal on 3 dimensions, selects winner or synthesizes.

        Returns:
            {
                "chosen_agent": "...",
                "chosen_segment": "...",
                "score_breakdown": {...},
                "arc_stage": "...",
                "reasoning": "..."
            }
        """
        arc_stage = self.get_arc_stage()

        # Build the proposals summary for the LLM
        proposals_text = ""
        for agent_name, proposal in proposals.items():
            segment = proposal.get("segment", proposal.get("content", ""))
            tone = proposal.get("emotional_tone", "unknown")
            proposals_text += f"\n\n[{agent_name}]:\nTone: {tone}\nSegment: {segment[:300]}..."

        system = """You are the Coordinator Agent. Evaluate story proposals and select the best one.
Score each proposal 1-10 on these dimensions:
  - narrative_coherence: Does it logically follow from the story?
  - character_consistency: Are characters behaving as established?
  - arc_appropriateness: Does it fit the current story arc stage?

Respond ONLY with valid JSON:
{
  "chosen_agent": "<agent name>",
  "reasoning": "<why this proposal best serves the story>",
  "scores": {
    "<agent_name>": {
      "narrative_coherence": <1-10>,
      "character_consistency": <1-10>,
      "arc_appropriateness": <1-10>,
      "total": <sum>
    }
  },
  "contradiction_detected": <true/false>,
  "contradiction_note": "<if any contradictions found>"
}"""

        user = f"""Current arc stage: {arc_stage}

Story so far (last 500 chars):
{story_context[-500:]}

Character profiles:
{json.dumps(character_profiles, indent=2)[:500]}

Proposals to evaluate:
{proposals_text}

Select the best proposal. Respond in JSON."""

        raw = call_llm(system, user, temperature=0.3, json_mode=True, model="smart")  # Low temp = consistent judging

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Coordinator JSON parse failed. Falling back to longest proposal.")
            result = {
                "chosen_agent": max(proposals, key=lambda a: len(proposals[a].get("segment", ""))),
                "reasoning": "Fallback: parse error",
                "scores": {},
                "contradiction_detected": False,
            }

        # Attach the actual chosen segment
        chosen = result.get("chosen_agent", list(proposals.keys())[0])
        if chosen in proposals:
            result["chosen_segment"] = proposals[chosen].get("segment", "")
            result["chosen_proposal"] = proposals[chosen]
        else:
            # Safety fallback if coordinator hallucinated an agent name
            chosen = list(proposals.keys())[0]
            result["chosen_agent"] = chosen
            result["chosen_segment"] = proposals[chosen].get("segment", "")
            result["chosen_proposal"] = proposals[chosen]

        result["arc_stage"] = arc_stage
        self.current_round += 1

        logger.info(f"Coordinator selected: {result['chosen_agent']} | Arc: {arc_stage}")
        return result

    def check_consistency(self, new_segment: str, story_context: str, character_profiles: dict) -> dict:
        """
        Post-selection consistency check.
        Run after a segment is chosen to catch any remaining contradictions.
        """
        system = """You are a narrative consistency checker.
Respond ONLY with valid JSON:
{
  "is_consistent": <true/false>,
  "issues": ["<issue 1>", "<issue 2>"],
  "suggested_fix": "<brief fix if inconsistent, else null>"
}"""

        user = f"""Check if this new story segment is consistent with the established story.

Story so far:
{story_context[-800:]}

Character profiles:
{json.dumps(character_profiles)[:400]}

New segment to check:
{new_segment}

Is it consistent? Respond in JSON."""

        raw = call_llm(system, user, temperature=0.2, json_mode=True, model="smart")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"is_consistent": True, "issues": [], "suggested_fix": None}
