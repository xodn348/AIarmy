from __future__ import annotations

import json

from rich.console import Console

from ..core.config import config
from ..core.memory import SessionMemory
from ..core.budget import BudgetTracker
from .base import BaseAgent, AgentResult

console = Console()

ROUTING_SYSTEM = """You are the Commander — the orchestrator of an AI team.

Your team:
- developer: writing code, reviewing PRs, debugging, git operations
- researcher: web research, document analysis, fact-finding, summarization
- writer: blog posts, documentation, emails, creative content
- analyst: data analysis, charts, metrics, business insights
- commander: coordination, planning, anything that needs multiple agents

Given a user request, respond ONLY with valid JSON:
{
  "agent": "<agent_name>",
  "task": "<clear task description for that agent>",
  "reason": "<one-line explanation>"
}

Rules:
- If the task needs multiple agents, pick the most important one first
- Be specific in the task description — the agent sees ONLY what you write here
- Never pick an agent for a task they aren't suited for
"""

COMMANDER_SYSTEM = """You are the Commander of an elite AI team working for your user.

Your responsibilities:
1. Plan and coordinate complex tasks across multiple agents
2. Synthesize results from multiple agents into coherent answers
3. Handle tasks that don't fit a single specialist
4. Always be direct, concise, and action-oriented

The AIarmy is built on two core principles:
- Safety first: risky actions require human approval
- Fail loudly: surface problems immediately, never silently fail
"""


class CommanderAgent(BaseAgent):
    name = "commander"
    role = "Orchestrator & CEO"
    model = config.COMMANDER_MODEL
    system_prompt = COMMANDER_SYSTEM

    def __init__(self, session_id: str, budget: BudgetTracker, memory: SessionMemory):
        super().__init__(session_id, budget, memory)
        self._roster: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._roster[agent.name] = agent

    def route(self, user_input: str) -> tuple[str, str, str]:
        if self._client:
            resp = self._client.messages.create(
                model=config.SPECIALIST_MODEL,
                max_tokens=300,
                system=ROUTING_SYSTEM,
                messages=[{"role": "user", "content": user_input}],
            )
            tokens = resp.usage.input_tokens + resp.usage.output_tokens
            self.budget.record(tokens)

            text_blocks = [b for b in resp.content if b.type == "text"]
            raw = text_blocks[0].text.strip() if text_blocks else "{}"

        elif self._session_client:
            raw, tokens = self._session_client.send_message(
                prompt=user_input,
                model=config.SPECIALIST_MODEL,
                max_tokens=300,
                system=ROUTING_SYSTEM,
            )
            self.budget.record(tokens)
            raw = raw.strip()

        else:
            return "commander", user_input, "fallback: no client configured"

        try:
            data = json.loads(raw)
            return data["agent"], data["task"], data["reason"]
        except (json.JSONDecodeError, KeyError):
            return "commander", user_input, "fallback: could not parse routing"

    def dispatch(self, user_input: str) -> AgentResult:
        if self.compactor and self.compactor.should_compact(self.memory):
            self.compactor.compact(self.memory)

        agent_name, task, reason = self.route(user_input)

        console.print(f"\n[dim]→ Routing to [bold]{agent_name}[/bold]: {reason}[/dim]")

        target = self._roster.get(agent_name, self)
        return target.run(task)

    def describe(self) -> str:
        return "Orchestrates the AI team, routes tasks to the right specialist."
