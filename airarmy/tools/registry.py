from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., Any]
    requires_hitl: bool = False
    input_schema: dict[str, Any] = field(
        default_factory=lambda: {"type": "object", "properties": {}}
    )

    def to_anthropic_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


_registry: dict[str, Tool] = {}


def register(tool: Tool) -> None:
    _registry[tool.name] = tool


def get(name: str) -> Tool | None:
    return _registry.get(name)


def list_tools() -> list[str]:
    return list(_registry.keys())


def get_tools_for_agent(allowed_tools: list[str]) -> list[dict[str, Any]]:
    return [
        tool.to_anthropic_schema()
        for tool_name in allowed_tools
        if (tool := _registry.get(tool_name)) is not None
    ]


def call(name: str, agent_allowed_tools: list[str], **kwargs: Any) -> Any:
    if name not in agent_allowed_tools:
        raise PermissionError(
            f"Tool '{name}' is not in this agent's allowed tool list."
        )
    tool = _registry.get(name)
    if not tool:
        raise KeyError(f"Tool '{name}' is not registered.")
    return tool.fn(**kwargs)
