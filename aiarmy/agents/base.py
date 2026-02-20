from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal, cast

import anthropic
from rich.console import Console

from ..core.config import config
from ..core.memory import SessionMemory
from ..core.budget import BudgetTracker
from ..core.audit import log_action
from ..core.security import (
    SecurityError,
    request_human_approval,
    requires_hitl,
    validate_input,
)
from ..core.claude_session import ClaudeSessionClient
from ..tools.registry import call as tool_call
from ..tools.registry import get_tools_for_agent

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

        if config.AUTH_MODE == "api_key":
            self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            self._session_client = None
        elif config.AUTH_MODE == "session_key":
            self._client = None
            self._session_client = ClaudeSessionClient(config.CLAUDE_SESSION_KEY)
        else:
            raise ValueError(f"Invalid AUTH_MODE: {config.AUTH_MODE}")

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
        prompt = self._build_prompt(safe_task, context)
        tools = get_tools_for_agent(self.allowed_tools)

        raw_messages = self.memory.to_api_format()
        messages: list[dict[str, Any]] = [
            {
                "role": cast(Literal["user", "assistant"], m["role"]),
                "content": m["content"],
            }
            for m in raw_messages
        ]
        messages.append({"role": "user", "content": prompt})

        total_tokens = 0
        output = "(no text response)"

        try:
            if self._client:
                request_params: dict[str, Any] = {
                    "model": self.model,
                    "max_tokens": config.MAX_TOKENS_PER_RUN,
                    "system": self.system_prompt,
                    "messages": messages,
                }
                if tools:
                    request_params["tools"] = tools

                response = self._client.messages.create(**request_params)
                total_tokens += (
                    response.usage.input_tokens + response.usage.output_tokens
                )

                iteration = 0
                while (
                    response.stop_reason == "tool_use"
                    and iteration < config.MAX_AGENT_TURNS
                ):
                    tool_results: list[dict[str, Any]] = []

                    for block in response.content:
                        if block.type != "tool_use":
                            continue

                        tool_name = block.name
                        tool_input = cast(dict[str, Any], block.input)

                        approved = True
                        if requires_hitl(tool_name):
                            approved = request_human_approval(
                                session_id=self.session_id,
                                agent=self.name,
                                action_type=tool_name,
                                action_description=f"Tool call: {tool_name}",
                                details=str(tool_input),
                            )

                        if not approved:
                            rejection = "Rejected by human approval gate."
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": rejection,
                                    "is_error": True,
                                }
                            )
                            log_action(
                                session_id=self.session_id,
                                agent=self.name,
                                action_type="tool_call",
                                action=tool_name,
                                approved=False,
                                result=rejection,
                            )
                            continue

                        try:
                            result = tool_call(
                                tool_name,
                                self.allowed_tools,
                                **tool_input,
                            )
                            result_text = str(result)
                            is_error = False
                        except Exception as e:
                            result_text = f"{type(e).__name__}: {e}"
                            is_error = True

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result_text,
                                "is_error": is_error,
                            }
                        )
                        log_action(
                            session_id=self.session_id,
                            agent=self.name,
                            action_type="tool_call",
                            action=tool_name,
                            approved=not is_error,
                            result=result_text[:500],
                        )

                    messages.append({"role": "assistant", "content": response.content})
                    messages.append({"role": "user", "content": tool_results})

                    self.budget.check_run_budget()

                    request_params = {
                        "model": self.model,
                        "max_tokens": config.MAX_TOKENS_PER_RUN,
                        "system": self.system_prompt,
                        "messages": messages,
                    }
                    if tools:
                        request_params["tools"] = tools

                    response = self._client.messages.create(**request_params)
                    total_tokens += (
                        response.usage.input_tokens + response.usage.output_tokens
                    )
                    iteration += 1

                text_blocks = [b for b in response.content if b.type == "text"]
                if text_blocks:
                    output = "\n".join(block.text for block in text_blocks)
                elif response.stop_reason == "tool_use":
                    output = "Stopped after reaching max tool-use turns."

            elif self._session_client:
                system_prompt = self.system_prompt
                if tools:
                    tool_lines = [
                        f"- {tool['name']}: {tool['description']}" for tool in tools
                    ]
                    system_prompt = (
                        f"{self.system_prompt}\n\n"
                        "Available tools (descriptions only; no native tool execution in "
                        "session mode):\n" + "\n".join(tool_lines)
                    )

                output, tokens = self._session_client.send_message(
                    prompt=prompt,
                    model=self.model,
                    max_tokens=config.MAX_TOKENS_PER_RUN,
                    system=system_prompt,
                )
                total_tokens += tokens
            else:
                raise RuntimeError("No client configured")

        except anthropic.APIError as e:
            return AgentResult(success=False, content=f"API error: {e}")
        except RuntimeError as e:
            return AgentResult(success=False, content=f"Session error: {e}")

        self.memory.add("user", prompt)
        self.memory.add("assistant", output)
        self.memory.trim_to_last_n(20)

        self.budget.record(total_tokens)

        log_action(
            session_id=self.session_id,
            agent=self.name,
            action_type="llm_call",
            action=safe_task[:200],
            approved=True,
            result=output[:500],
            tokens_used=total_tokens,
        )

        return AgentResult(success=True, content=output, tokens_used=total_tokens)

    def _build_prompt(self, task: str, context: str) -> str:
        if context:
            return f"Context:\n{context}\n\nTask:\n{task}"
        return task

    @abstractmethod
    def describe(self) -> str:
        pass
