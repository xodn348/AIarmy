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
    working_set: dict[str, Any] = field(
        default_factory=lambda: {
            "summary": "",
            "pinned_facts": [],
            "decisions": [],
            "open_tasks": [],
            "files_touched": [],
            "recent_messages": [],
        }
    )

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    def to_api_format(self) -> list[dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def trim_to_last_n(self, n: int = 20) -> None:
        if len(self.messages) > n:
            self.messages = self.messages[-n:]

    def estimate_tokens(self) -> int:
        total_chars = sum(len(m.content) for m in self.messages)
        return total_chars // 4

    def get_llm_context(self, max_messages: int = 20) -> list[Message]:
        return self.messages[-max_messages:]

    def add_pinned_fact(self, fact: str) -> None:
        if fact not in self.working_set["pinned_facts"]:
            self.working_set["pinned_facts"].append(fact)

    def add_decision(self, decision: str) -> None:
        if decision not in self.working_set["decisions"]:
            self.working_set["decisions"].append(decision)

    def update_summary(self, summary: str) -> None:
        self.working_set["summary"] = summary

    def set_context(self, key: str, value: Any) -> None:
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)

    def clear(self) -> None:
        self.messages.clear()
        self.context.clear()
