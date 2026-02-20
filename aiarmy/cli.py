from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime

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
from .core.session_manager import SessionManager
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
@click.option("--new-session", is_flag=True, help="Start a new interactive session")
@click.pass_context
def main(ctx: click.Context, new_session: bool) -> None:
    if ctx.invoked_subcommand is None:
        _run_interactive(force_new=new_session)


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


@main.command()
def sessions() -> None:
    session_manager = SessionManager()
    all_sessions = session_manager.list_sessions()

    if not all_sessions:
        console.print("[dim]No saved sessions found.[/dim]")
        return

    table = Table(title="💾 Saved Sessions", border_style="cyan")
    table.add_column("Session ID", style="bold cyan")
    table.add_column("Messages", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("Last Updated", style="dim")

    for session in all_sessions[:10]:
        table.add_row(
            session["session_id"],
            str(session["message_count"]),
            f"{session['token_count']:,}",
            session["last_updated"][:19],
        )

    console.print(table)


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
    memory.set_context("created_at", datetime.now(UTC).isoformat())
    session_manager = SessionManager()
    army = build_army(session_id, budget, memory)

    with console.status("[bold cyan]Working...[/bold cyan]"):
        result = army.dispatch(task)

    if result.success:
        console.print(Markdown(result.content))
    else:
        console.print(f"[red]Failed: {result.content}[/red]")

    session_manager.save_session(
        session_id=session_id,
        memory=memory,
        state={
            "created_at": memory.context.get(
                "created_at", datetime.now(UTC).isoformat()
            ),
            "tokens_used": budget.tokens_used,
            "runs": budget.runs,
        },
    )

    console.print(f"\n[dim]Tokens used: {budget.summary()}[/dim]")


def _run_interactive(force_new: bool = False) -> None:
    try:
        config.validate()
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    console.print(BANNER)

    session_manager = SessionManager()

    if not force_new:
        last_session_id = session_manager.get_last_session()
        if last_session_id:
            try:
                loaded = session_manager.load_session(last_session_id)
                if loaded is None:
                    raise FileNotFoundError("Session not found")

                memory, state = loaded
                budget = BudgetTracker(
                    session_id=last_session_id,
                    tokens_used=state.get("tokens_used", 0),
                )
                budget.runs = state.get("runs", 0)
                session_id = last_session_id
                console.print(
                    f"[dim]📂 Resumed session: {session_id} "
                    f"({len(memory.messages)} messages, {budget.tokens_used:,} tokens)[/dim]\n"
                )
            except Exception as e:
                console.print(f"[yellow]⚠️  Could not resume session: {e}[/yellow]")
                session_id = f"session-{uuid.uuid4().hex[:8]}"
                memory = SessionMemory(session_id=session_id)
                memory.set_context("created_at", datetime.now(UTC).isoformat())
                budget = BudgetTracker(session_id=session_id)
                console.print(f"[dim]✨ Started new session: {session_id}[/dim]\n")
        else:
            session_id = f"session-{uuid.uuid4().hex[:8]}"
            memory = SessionMemory(session_id=session_id)
            memory.set_context("created_at", datetime.now(UTC).isoformat())
            budget = BudgetTracker(session_id=session_id)
            console.print(f"[dim]✨ Started new session: {session_id}[/dim]\n")
    else:
        session_id = f"session-{uuid.uuid4().hex[:8]}"
        memory = SessionMemory(session_id=session_id)
        memory.set_context("created_at", datetime.now(UTC).isoformat())
        budget = BudgetTracker(session_id=session_id)
        console.print(f"[dim]✨ Started new session: {session_id}[/dim]\n")

    army = build_army(session_id, budget, memory)

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
            session_manager.save_session(
                session_id=session_id,
                memory=memory,
                state={
                    "created_at": memory.context.get(
                        "created_at", datetime.now(UTC).isoformat()
                    ),
                    "tokens_used": budget.tokens_used,
                    "runs": budget.runs,
                },
            )
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

        session_manager.save_session(
            session_id=session_id,
            memory=memory,
            state={
                "created_at": memory.context.get(
                    "created_at", datetime.now(UTC).isoformat()
                ),
                "tokens_used": budget.tokens_used,
                "runs": budget.runs,
            },
        )
