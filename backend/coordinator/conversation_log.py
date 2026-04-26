"""
coordinator/conversation_log.py
─────────────────────────────────
Windowed conversation log for inter-agent communication.
Keeps only recent messages to prevent context window overflow.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConversationLog:
    window_size: int = 10           # Max messages kept in active window
    messages: list = field(default_factory=list)

    def add(self, agent: str, message_type: str, content: dict) -> None:
        """
        Add a message to the log.
        message_type: 'communicate' or 'propose'
        """
        self.messages.append({
            "agent": agent,
            "type": message_type,
            "intent": content.get("intent", ""),
            "content": content,
        })

    def get_recent(self, n: Optional[int] = None) -> list[dict]:
        """Return last n messages (defaults to window_size)."""
        limit = n or self.window_size
        return self.messages[-limit:]

    def get_all(self) -> list[dict]:
        return self.messages

    def clear(self) -> None:
        self.messages = []

    def summary(self) -> str:
        """Human-readable summary of the conversation."""
        lines = []
        for m in self.get_recent():
            lines.append(f"[{m['agent']}] ({m['type']}): {m['intent'][:100]}")
        return "\n".join(lines) if lines else "No messages yet."
