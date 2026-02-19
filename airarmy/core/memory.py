from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str
    content: str


@dataclass
class SessionMemory:
    session_id: str
    messages: list[Message] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    def to_api_format(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def trim_to_last_n(self, n: int = 20) -> None:
        if len(self.messages) > n:
            self.messages = self.messages[-n:]

    def set_context(self, key: str, value: Any) -> None:
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)

    def clear(self) -> None:
        self.messages.clear()
        self.context.clear()
