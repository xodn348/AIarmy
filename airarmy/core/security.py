from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from .config import config
from .audit import log_action

console = Console()

PROMPT_INJECTION_PATTERNS = [
    "ignore previous",
    "ignore all previous",
    "disregard",
    "forget your instructions",
    "you are now",
    "act as",
    "pretend you are",
    "new instructions:",
    "system:",
    "jailbreak",
]


def validate_input(text: str) -> str:
    lowered = text.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern in lowered:
            raise SecurityError(
                f"Potential prompt injection detected: '{pattern}'. "
                "Request blocked for security."
            )
    return text


def requires_hitl(action_type: str) -> bool:
    return action_type in config.HITL_REQUIRED_ACTIONS


def request_human_approval(
    session_id: str,
    agent: str,
    action_type: str,
    action_description: str,
    details: str = "",
) -> bool:
    console.print()
    console.print(
        Panel(
            f"[bold yellow]⚠️  Human Approval Required[/bold yellow]\n\n"
            f"[bold]Agent:[/bold] {agent}\n"
            f"[bold]Action:[/bold] {action_type}\n"
            f"[bold]Description:[/bold] {action_description}\n"
            + (f"\n[dim]{details}[/dim]" if details else ""),
            border_style="yellow",
            title="[yellow]HITL Checkpoint[/yellow]",
        )
    )

    approved = Confirm.ask("[yellow]Approve this action?[/yellow]", default=False)

    log_action(
        session_id=session_id,
        agent=agent,
        action_type=action_type,
        action=action_description,
        approved=approved,
        result="approved" if approved else "rejected_by_user",
    )

    if not approved:
        console.print("[red]Action rejected.[/red]")

    return approved


class SecurityError(Exception):
    pass
