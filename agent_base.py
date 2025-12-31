class BaseAgent:
    name = "BaseAgent"

    def communicate(self, story_context: str, conversation_log: str) -> str:
        raise NotImplementedError("communicate() not implemented")

    def propose(self, story_context: str, conversation_log: str) -> str:
        raise NotImplementedError("propose() not implemented")
