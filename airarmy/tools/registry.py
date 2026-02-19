from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class Tool:
    name: str
    description: str
    fn: Callable[..., Any]
    requires_hitl: bool = False


_registry: dict[str, Tool] = {}


def register(tool: Tool) -> None:
    _registry[tool.name] = tool


def get(name: str) -> Tool | None:
    return _registry.get(name)


def list_tools() -> list[str]:
    return list(_registry.keys())


def call(name: str, agent_allowed_tools: list[str], **kwargs: Any) -> Any:
    if name not in agent_allowed_tools:
        raise PermissionError(
            f"Tool '{name}' is not in this agent's allowed tool list."
        )
    tool = _registry.get(name)
    if not tool:
        raise KeyError(f"Tool '{name}' is not registered.")
    return tool.fn(**kwargs)
