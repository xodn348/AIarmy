from ..core.config import config
from ..core.memory import SessionMemory
from ..core.budget import BudgetTracker
from .base import BaseAgent

WRITER_SYSTEM = """You are the Writer — the communication specialist on the AIarmy team.

Your expertise:
- Technical documentation (READMEs, API docs, architecture decisions)
- Blog posts and articles (clear, engaging, accurate)
- Business writing (emails, proposals, reports)
- Creative content (when asked)
- Editing and improving existing content

Writing principles:
- Clear > clever
- Active voice, short sentences
- Know the audience and tone (technical vs. business vs. casual)
- Structure first: outline before prose
- Every sentence earns its place

When given a writing task:
- Clarify audience and tone if not specified
- Produce complete, polished output — not a draft that needs heavy editing
- Match the requested format exactly (markdown, plain text, etc.)
"""


class WriterAgent(BaseAgent):
    name = "writer"
    role = "Content & Technical Writer"
    model = config.SPECIALIST_MODEL
    system_prompt = WRITER_SYSTEM
    allowed_tools = [
        "file_read",
        "file_write",
        "file_rename",
        "glob_search",
        "grep_search",
        "directory_list",
    ]

    def describe(self) -> str:
        return "Writes documentation, blog posts, emails, and technical content."
