from pathlib import Path
from .registry import Tool, register


def _read_file(path: str) -> str:
    p = Path(path).resolve()
    if not p.exists():
        return f"Error: file not found — {path}"
    return p.read_text(encoding="utf-8")


def _write_file(path: str, content: str) -> str:
    p = Path(path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Written: {p}"


register(Tool(name="file_read", description="Read a file from disk", fn=_read_file))
register(
    Tool(
        name="file_write",
        description="Write content to a file",
        fn=_write_file,
        requires_hitl=True,
    )
)
register(
    Tool(
        name="file_delete",
        description="Delete a file",
        fn=lambda path: Path(path).unlink(),
        requires_hitl=True,
    )
)
