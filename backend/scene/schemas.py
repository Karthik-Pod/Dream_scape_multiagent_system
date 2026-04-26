"""
scene/schemas.py
─────────────────
Pydantic schemas for structured scene data.
This is the CENTRAL DATA CONTRACT of the entire multimodal pipeline.
Every downstream system (image gen, TTS, music, video) reads from these.

Flow:
  Story text → SceneSegmenter → [RawScene] → SceneStructurer → [Scene]
  Scene.visual_prompt    → image_gen.py
  Scene.narration_text   → tts_gen.py
  Scene.music_mood       → music_gen.py
  Scene.sfx_cues         → sfx_gen.py
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


# ── Enums ────────────────────────────────────────────────────────────

class EmotionalTone(str, Enum):
    TENSE       = "tense"
    HOPEFUL     = "hopeful"
    OMINOUS     = "ominous"
    MELANCHOLIC = "melancholic"
    TRIUMPHANT  = "triumphant"
    MYSTERIOUS  = "mysterious"
    PEACEFUL    = "peaceful"
    FEARFUL     = "fearful"
    JOYFUL      = "joyful"
    SUSPENSEFUL = "suspenseful"


class TimeOfDay(str, Enum):
    DAWN      = "dawn"
    MORNING   = "morning"
    AFTERNOON = "afternoon"
    DUSK      = "dusk"
    NIGHT     = "night"
    UNKNOWN   = "unknown"


class NarrationStyle(str, Enum):
    CALM       = "calm"
    URGENT     = "urgent"
    WHISPERED  = "whispered"
    DRAMATIC   = "dramatic"
    MELANCHOLIC= "melancholic"


class Pacing(str, Enum):
    SLOW   = "slow"
    MEDIUM = "medium"
    FAST   = "fast"


# ── Sub-models ───────────────────────────────────────────────────────

class Setting(BaseModel):
    """Where and when the scene takes place."""
    location: str = Field(..., description="Specific place name or description")
    time_of_day: TimeOfDay = Field(TimeOfDay.UNKNOWN)
    weather: str = Field("clear", description="Weather conditions")
    atmosphere: str = Field("neutral", description="Overall atmosphere/mood of place")
    lighting: str = Field("natural", description="Lighting style: dramatic, soft, candlelit, etc.")


class CharacterPresence(BaseModel):
    """A character's state within a scene."""
    name: str
    emotion: str = Field(..., description="Character's emotional state in this scene")
    action: str = Field(..., description="What the character is doing")
    location_in_scene: Optional[str] = None


class DialogueLine(BaseModel):
    """A single line of dialogue."""
    character: str
    text: str
    emotion: str = Field("neutral", description="Emotional delivery of the line")


# ── Main Scene Schema ─────────────────────────────────────────────────

class Scene(BaseModel):
    """
    A fully structured story scene.
    This single object drives ALL downstream generation.
    """
    # Identity
    scene_id: str                       = Field(..., description="Unique ID: story_id_scene_N")
    story_id: str                       = Field(..., description="Parent story ID")
    sequence_number: int                = Field(..., description="Scene order in the story")
    title: str                          = Field(..., description="Short scene title")

    # Content
    setting: Setting
    characters: list[CharacterPresence] = Field(default_factory=list)
    narration_text: str                 = Field(..., description="The prose narration for this scene")
    dialogue: list[DialogueLine]        = Field(default_factory=list)

    # Tone & Pacing
    emotional_tone: EmotionalTone       = Field(EmotionalTone.MYSTERIOUS)
    pacing: Pacing                      = Field(Pacing.MEDIUM)
    tension_level: int                  = Field(5, ge=1, le=10, description="1=calm, 10=maximum tension")

    # Visual Generation Inputs (→ image_gen.py)
    visual_prompt: str                  = Field(..., description="Engineered SDXL image prompt")
    negative_prompt: str                = Field(
        "blurry, low quality, bad anatomy, watermark, text, ugly, deformed, glitch, chromatic aberration, oversaturated, colored dots, colored orbs, floating circles, lens flare orbs, bokeh balls, light leaks, digital noise, jpeg artifacts, color bleed",
        description="SDXL negative prompt"
    )

    # Audio Generation Inputs (→ tts_gen.py, music_gen.py, sfx_gen.py)
    narration_style: NarrationStyle     = Field(NarrationStyle.CALM)
    music_mood: str                     = Field(..., description="Music generation descriptor")
    music_tempo: str                    = Field("moderate", description="slow/moderate/fast/building")
    sfx_cues: list[str]                 = Field(default_factory=list, description="Sound effects list")
    ambient_sounds: list[str]           = Field(default_factory=list, description="Background ambient sounds")

    # Metadata
    arc_stage: str                      = Field("unknown", description="Story arc position")
    source_agent: str                   = Field("unknown", description="Agent that generated this segment")
    tags: list[str]                     = Field(default_factory=list, description="Keywords for retrieval")
    duration_estimate: float            = Field(30.0, description="Estimated scene duration in seconds")

    # Generation Status (updated as pipeline runs)
    image_path: Optional[str]           = None
    audio_path: Optional[str]           = None
    video_path: Optional[str]           = None


class SceneList(BaseModel):
    """Container for a complete story's scenes."""
    story_id: str
    total_scenes: int
    scenes: list[Scene]

    def get_scene(self, sequence_number: int) -> Optional[Scene]:
        for s in self.scenes:
            if s.sequence_number == sequence_number:
                return s
        return None
