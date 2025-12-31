class ConversationLog:
    def __init__(self, max_turns=6):
        self.max_turns = max_turns
        self.messages = []

    def add(self, agent_name: str, message: str):
        if message is None:
            message = ""
        message = message.strip()
        if not message:
            return

        self.messages.append(f"{agent_name}: {message}")

        if len(self.messages) > self.max_turns:
            self.messages.pop(0)

    def get(self) -> str:
        if not self.messages:
            return "No agent discussion yet."
        return "\n".join(self.messages)
