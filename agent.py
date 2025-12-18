class Agent:
    def __init__(self, name, role, priority):
        self.name = name
        self.role = role
        self.priority = priority

    def generate_proposal(self, story_state):
        raise NotImplementedError


class PlotAgent(Agent):
    def generate_proposal(self, story_state):
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
        if story_state.get_round() == 0:
            text = "A quiet sense of unease settles into the atmosphere."
        else:
            text = "The emotional tension intensifies as uncertainty grows."

        return {
            "agent": self.name,
            "text": text,
            "priority": self.priority,
            "type": "emotion"
        }
