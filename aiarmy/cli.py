from __future__ import annotations

import uuid
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt

from .core.config import config
from .core.memory import SessionMemory
from .core.budget import BudgetTracker
from .core.audit import get_session_logs
from .agents.commander import CommanderAgent
from .agents.developer import DeveloperAgent
from .agents.researcher import ResearcherAgent
from .agents.writer import WriterAgent
from .agents.analyst import AnalystAgent

console = Console()

BANNER = """
[bold cyan]
  █████╗ ██╗ █████╗ ██████╗ ███╗   ███╗██╗   ██╗
 ██╔══██╗██║██╔══██╗██╔══██╗████╗ ████║╚██╗ ██╔╝
 ███████║██║███████║██████╔╝██╔████╔██║ ╚████╔╝
 ██╔══██║██║██╔══██║██╔══██╗██║╚██╔╝██║  ╚██╔╝
 ██║  ██║██║██║  ██║██║  ██║██║ ╚═╝ ██║   ██║
 ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝   ╚═╝
[/bold cyan]
[dim]Your personal AI company. Type [bold]help[/bold] for commands.[/dim]
"""

HELP_TEXT = """
[bold]Commands:[/bold]
  [cyan]help[/cyan]        Show this message
  [cyan]team[/cyan]        Show your AI team
  [cyan]budget[/cyan]      Show token usage this session
  [cyan]log[/cyan]         Show audit log for this session
  [cyan]clear[/cyan]       Clear conversation history
  [cyan]exit[/cyan]        Quit

[bold]Just type anything else to give a task to your team.[/bold]
"""


def build_army(
    session_id: str, budget: BudgetTracker, memory: SessionMemory
) -> CommanderAgent:
    commander = CommanderAgent(session_id=session_id, budget=budget, memory=memory)
    for AgentClass in [DeveloperAgent, ResearcherAgent, WriterAgent, AnalystAgent]:
        agent = AgentClass(session_id=session_id, budget=budget, memory=memory)
        commander.register(agent)
    return commander


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        _run_interactive()


@main.command()
@click.argument("task", nargs=-1, required=True)
def ask(task: tuple[str, ...]) -> None:
    task_str = " ".join(task)
    _run_single(task_str)


@main.command()
def team() -> None:
    _show_team()


@main.command()
def logs() -> None:
    session_id = "cli-single"
    _show_logs(session_id)


def _show_team() -> None:
    table = Table(title="🪖 AIarmy — Your Team", border_style="cyan")
    table.add_column("Role", style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("What they do")
    table.add_column("Model", style="dim")

    table.add_row(
        "👑 Commander",
        "Commander",
        "Routes tasks, orchestrates complex work",
        config.COMMANDER_MODEL,
    )
    table.add_row(
        "💻 Developer", "Dev", "Code, review, debug, git", config.SPECIALIST_MODEL
    )
    table.add_row(
        "🔍 Researcher",
        "Researcher",
        "Research, documents, fact-finding",
        config.SPECIALIST_MODEL,
    )
    table.add_row(
        "✍️  Writer",
        "Writer",
        "Docs, blog posts, emails, content",
        config.SPECIALIST_MODEL,
    )
    table.add_row(
        "📊 Analyst",
        "Analyst",
        "Data analysis, metrics, business insights",
        config.SPECIALIST_MODEL,
    )

    console.print(table)


def _show_logs(session_id: str) -> None:
    rows = get_session_logs(session_id)
    if not rows:
        console.print("[dim]No audit log entries for this session.[/dim]")
        return

    table = Table(title=f"Audit Log — {session_id}", border_style="dim")
    table.add_column("Time", style="dim", no_wrap=True)
    table.add_column("Agent", style="cyan")
    table.add_column("Type")
    table.add_column("Action", max_width=60)
    table.add_column("Tokens", justify="right")

    for row in rows:
        ts = row["ts"][11:19]
        table.add_row(
            ts,
            row["agent"],
            row["action_type"],
            row["action"][:60],
            str(row["tokens_used"]),
        )

    console.print(table)


def _run_single(task: str) -> None:
    try:
        config.validate()
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    session_id = f"single-{uuid.uuid4().hex[:8]}"
    budget = BudgetTracker(session_id=session_id)
    memory = SessionMemory(session_id=session_id)
    army = build_army(session_id, budget, memory)

    with console.status("[bold cyan]Working...[/bold cyan]"):
        result = army.dispatch(task)

    if result.success:
        console.print(Markdown(result.content))
    else:
        console.print(f"[red]Failed: {result.content}[/red]")

    console.print(f"\n[dim]Tokens used: {budget.summary()}[/dim]")


def _run_interactive() -> None:
    try:
        config.validate()
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    console.print(BANNER)

    session_id = f"session-{uuid.uuid4().hex[:8]}"
    budget = BudgetTracker(session_id=session_id)
    memory = SessionMemory(session_id=session_id)
    army = build_army(session_id, budget, memory)

    console.print(f"[dim]Session: {session_id}[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]You[/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not user_input:
            continue

        cmd = user_input.lower()

        if cmd in ("exit", "quit", "bye"):
            console.print(f"\n[dim]Session ended. {budget.summary()}[/dim]")
            break
        elif cmd == "help":
            console.print(HELP_TEXT)
        elif cmd == "team":
            _show_team()
        elif cmd == "budget":
            console.print(f"[cyan]Budget:[/cyan] {budget.summary()}")
        elif cmd == "log":
            _show_logs(session_id)
        elif cmd == "clear":
            memory.clear()
            console.print("[dim]Conversation history cleared.[/dim]")
        else:
            with console.status("[bold cyan]Working...[/bold cyan]"):
                result = army.dispatch(user_input)

            if result.success:
                console.print(
                    Panel(
                        Markdown(result.content),
                        border_style="cyan",
                        padding=(1, 2),
                    )
                )
            else:
                console.print(f"[red]{result.content}[/red]")

            console.print(f"[dim]Budget: {budget.summary()}[/dim]")
