from llm_client import call_llm
from agent_base import BaseAgent

class Agent:
    def __init__(self, name, role, priority):
        self.name = name
        self.role = role
        self.priority = priority

    def generate_proposal(self, story_state):
        raise NotImplementedError
class CharacterAgent(BaseAgent):
    name = "CharacterAgent"

    def communicate(self, story_context, conversation_log):
        system = "You control character actions and survival decisions."
        user = f"""
Story so far:
{story_context}

Other agents discussion:
{conversation_log}

State what the character wants to do next and why.
"""
        return call_llm(system, user)

    def propose(self, story_context, conversation_log):
        system = "Write the next character-driven story action."
        user = f"""
Story so far:
{story_context}

Agent discussion:
{conversation_log}

Write the next scene focused on character action only.
"""
        return call_llm(system, user)
