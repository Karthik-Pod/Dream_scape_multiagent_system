from llm_client import call_llm
class Agent:
    def __init__(self, name, role, priority):
        self.name = name
        self.role = role
        self.priority = priority

    def generate_proposal(self, story_state):
        raise NotImplementedError


class PlotAgent(Agent):
    def generate_proposal(self, story_state):
        system_prompt = (
            "You are a plot-focused storytelling agent. "
            "Your job is to advance the story with events. "
            "Do NOT describe emotions. Do NOT change character decisions."
        )

        user_prompt = (
            f"Story so far:\n{story_state.get_full_story()}\n\n"
            "Add one vivid plot development sentence."
        )

        # ✅ initialize text first (IMPORTANT)
        text = None

        try:
            text = call_llm(system_prompt, user_prompt)
        except Exception:
            if story_state.get_round() == 0:
                text = "An unexpected disturbance breaks the calm of the setting."
            else:
                text = "The situation escalates as consequences of earlier actions unfold."

        return {
            "agent": self.name,
            "text": text,
            "priority": self.priority,
            "type": "plot"
        }
class CharacterAgent(Agent):
    def generate_proposal(self, story_state):
        last = story_state.get_last_segment()

        if "hesitates" in last or story_state.get_round() == 0:
            text = "The protagonist gathers courage and makes a deliberate choice."
        else:
            text = "The protagonist stands by their decision, accepting its consequences."

        return {
            "agent": self.name,
            "text": text,
            "priority": self.priority,
            "type": "character"
        }
class EmotionAgent(Agent):
    def generate_proposal(self, story_state):
        system_prompt = (
            "You are an emotion-focused storytelling agent. "
            "You only describe mood and atmosphere. "
            "Do NOT change character decisions or plot events."
        )

        user_prompt = (
            f"Story so far:\n{story_state.get_full_story()}\n\n"
            "Add one sentence describing the emotional tone."
        )

        try:
            text = call_llm(system_prompt, user_prompt)
        except Exception:
            # fallback (VERY IMPORTANT)
            text = "An undercurrent of emotion subtly shapes the scene."

        return {
            "agent": self.name,
            "text": text,
            "priority": self.priority,
            "type": "emotion"
        }
