from llm_client import call_llm
from agent_base import BaseAgent

class Agent:
    def __init__(self, name, role, priority):
        self.name = name
        self.role = role
        self.priority = priority

    def generate_proposal(self, story_state):
        raise NotImplementedError
    
class EmotionAgent(BaseAgent):
    name = "EmotionAgent"

    def communicate(self, story_context, conversation_log):
        system = "You control emotional tone, fear, tension, pacing."
        user = f"""
Story so far:
{story_context}

Other agents discussion:
{conversation_log}

Describe how emotions should evolve.
"""
        return call_llm(system, user)

    def propose(self, story_context, conversation_log):
        system = "Write a continuation emphasizing emotion and mood."
        user = f"""
Story so far:
{story_context}

Agent discussion:
{conversation_log}

Write the next scene focusing on emotion.
"""
        return call_llm(system, user)
