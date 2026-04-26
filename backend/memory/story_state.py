"""
memory/story_state.py
──────────────────────
Tracks the growing story with full metadata per segment.
Upgraded from your original: now tracks arc stage, agent,
emotional tone, and round number per segment.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StorySegment:
    """A single story segment with full metadata."""
    round_number: int
    text: str
    agent: str
    arc_stage: str
    emotional_tone: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class StoryState:
    def __init__(self, initial_prompt: str):
        self.initial_prompt = initial_prompt
        self.segments: list[StorySegment] = []
        self._round = 0

    def add_segment(
        self,
        text: str,
        agent: str = "unknown",
        arc_stage: str = "unknown",
        emotional_tone: str = "neutral",
    ) -> None:
        self._round += 1
        self.segments.append(StorySegment(
            round_number=self._round,
            text=text,
            agent=agent,
            arc_stage=arc_stage,
            emotional_tone=emotional_tone,
        ))

    def get_full_story(self) -> str:
        """Full story as continuous prose."""
        parts = [self.initial_prompt] + [s.text for s in self.segments]
        return "\n\n".join(parts)

    def get_last_segment(self) -> str:
        if self.segments:
            return self.segments[-1].text
        return self.initial_prompt

    def get_round(self) -> int:
        return self._round

    def get_arc_history(self) -> list[dict]:
        """Return arc progression across rounds — useful for evaluation."""
        return [
            {"round": s.round_number, "arc": s.arc_stage, "tone": s.emotional_tone, "agent": s.agent}
            for s in self.segments
        ]

    def to_dict(self) -> dict:
        return {
            "initial_prompt": self.initial_prompt,
            "total_rounds": self._round,
            "segments": [
                {
                    "round": s.round_number,
                    "agent": s.agent,
                    "arc_stage": s.arc_stage,
                    "emotional_tone": s.emotional_tone,
                    "text": s.text,
                }
                for s in self.segments
            ],
        }
