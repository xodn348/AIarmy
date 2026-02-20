from ..core.config import config
from ..core.memory import SessionMemory
from ..core.budget import BudgetTracker
from .base import BaseAgent

DEVELOPER_SYSTEM = """You are the Developer — a senior software engineer on the AIarmy team.

Your expertise:
- Writing clean, idiomatic code in Python, TypeScript, Go, and more
- Code review: finding bugs, security issues, performance problems
- Debugging: systematic root-cause analysis
- Architecture: designing scalable, maintainable systems
- Git: commit messages, PR descriptions, branch strategy

When writing code:
- Write complete, runnable code (no placeholders or "TODO: implement this")
- Include error handling
- Follow the language's conventions and style
- Explain non-obvious decisions briefly in the code itself (only when truly necessary)

When reviewing code:
- Identify actual bugs first, then improvements
- Be specific: line numbers, concrete suggestions
- Distinguish blocking issues from style preferences

Security mindset: always flag potential injection, auth bypass, or data exposure issues.
"""


class DeveloperAgent(BaseAgent):
    name = "developer"
    role = "Senior Software Engineer"
    model = config.SPECIALIST_MODEL
    system_prompt = DEVELOPER_SYSTEM
    allowed_tools = [
        "file_read",
        "file_write",
        "file_delete",
        "file_rename",
        "shell_exec",
        "git_init",
        "git_status",
        "git_diff",
        "git_add",
        "git_commit",
        "git_push",
        "git_clone",
        "git_log",
        "glob_search",
        "grep_search",
        "directory_list",
        "package_install",
        "env_read",
    ]

    def describe(self) -> str:
        return "Writes code, reviews PRs, debugs issues, handles git operations."
