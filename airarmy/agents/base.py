from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal, cast

import anthropic
from rich.console import Console

from ..core.config import config
from ..core.memory import SessionMemory
from ..core.budget import BudgetTracker
from ..core.audit import log_action
from ..core.security import validate_input, SecurityError

console = Console()


@dataclass
class AgentResult:
    success: bool
    content: str
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    name: str
    role: str
    model: str
    system_prompt: str
    allowed_tools: list[str] = []

    def __init__(self, session_id: str, budget: BudgetTracker, memory: SessionMemory):
        self.session_id = session_id
        self.budget = budget
        self.memory = memory
        self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def run(self, task: str, context: str = "") -> AgentResult:
        try:
            safe_task = validate_input(task)
        except SecurityError as e:
            log_action(
                session_id=self.session_id,
                agent=self.name,
                action_type="security_block",
                action=task[:200],
                approved=False,
                result=str(e),
            )
            return AgentResult(success=False, content=f"[Security] {e}")

        self.budget.check_run_budget()

        raw_messages = self.memory.to_api_format()
        messages: list[anthropic.types.MessageParam] = [
            {
                "role": cast(Literal["user", "assistant"], m["role"]),
                "content": m["content"],
            }
            for m in raw_messages
        ]
        messages.append(
            {"role": "user", "content": self._build_prompt(safe_task, context)}
        )

        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=config.MAX_TOKENS_PER_RUN,
                system=self.system_prompt,
                messages=messages,
            )
        except anthropic.APIError as e:
            return AgentResult(success=False, content=f"API error: {e}")

        tokens = response.usage.input_tokens + response.usage.output_tokens
        text_blocks = [b for b in response.content if b.type == "text"]
        output = text_blocks[0].text if text_blocks else "(no text response)"

        self.memory.add("user", self._build_prompt(safe_task, context))
        self.memory.add("assistant", output)
        self.memory.trim_to_last_n(20)

        log_action(
            session_id=self.session_id,
            agent=self.name,
            action_type="llm_call",
            action=safe_task[:200],
            approved=True,
            result=output[:500],
            tokens_used=tokens,
        )

        return AgentResult(success=True, content=output, tokens_used=tokens)

    def _build_prompt(self, task: str, context: str) -> str:
        if context:
            return f"Context:\n{context}\n\nTask:\n{task}"
        return task

    @abstractmethod
    def describe(self) -> str:
        pass
