from llm_client import call_llm
from agent_base import BaseAgent

class Agent:
    def __init__(self, name, role, priority):
        self.name = name
        self.role = role
        self.priority = priority

    def generate_proposal(self, story_state):
        raise NotImplementedError
class PlotAgent(BaseAgent):
    name = "PlotAgent"

    def communicate(self, story_context, conversation_log):
        system = "You control plot escalation and events."
        user = f"""
Story so far:
{story_context}

Other agents discussion:
{conversation_log}

Suggest plot changes or twists.
"""
        return call_llm(system, user)

    def propose(self, story_context, conversation_log):
        system = "Write the next plot-driven story event."
        user = f"""
Story so far:
{story_context}

Agent discussion:
{conversation_log}

Write the next plot advancement.
"""
        return call_llm(system, user)
