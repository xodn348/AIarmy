import subprocess
from pathlib import Path
from .registry import Tool, register


def _glob_search(pattern: str, path: str = ".") -> str:
    try:
        p = Path(path).resolve()
        if not p.exists():
            return f"Error: path not found — {path}"

        results = list(p.glob(pattern))[:100]
        if not results:
            return f"No matches found for pattern: {pattern}"

        return "\n".join(str(r) for r in sorted(results))
    except Exception as e:
        return f"Error: {e}"


def _grep_search(pattern: str, path: str = ".", include: str = "") -> str:
    try:
        p = Path(path).resolve()
        if not p.exists():
            return f"Error: path not found — {path}"

        cmd = ["grep", "-r", "-n", pattern, str(p)]

        if include:
            cmd.extend(["--include", include])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 1:
            return f"No matches found for pattern: {pattern}"

        if result.returncode != 0:
            return f"Error: {result.stderr}"

        lines = result.stdout.strip().split("\n")[:50]
        return "\n".join(lines)
    except subprocess.TimeoutExpired:
        return "Error: grep search timed out"
    except Exception as e:
        return f"Error: {e}"


def _directory_list(path: str = ".") -> str:
    try:
        p = Path(path).resolve()
        if not p.exists():
            return f"Error: path not found — {path}"

        if not p.is_dir():
            return f"Error: not a directory — {path}"

        items = []
        for item in sorted(p.iterdir()):
            if item.is_dir():
                items.append(f"[DIR]  {item.name}/")
            else:
                size = item.stat().st_size
                items.append(f"[FILE] {item.name} ({size} bytes)")

        if not items:
            return f"Empty directory: {p}"

        return "\n".join(items)
    except Exception as e:
        return f"Error: {e}"


register(
    Tool(
        name="glob_search",
        description="Search for files matching a glob pattern",
        fn=_glob_search,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern (e.g., '*.py', 'src/**/*.ts')",
                },
                "path": {
                    "type": "string",
                    "description": "Root path to search from (default: current directory)",
                },
            },
            "required": ["pattern"],
        },
    )
)

register(
    Tool(
        name="grep_search",
        description="Search for text pattern in files using grep",
        fn=_grep_search,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Text pattern to search for (regex supported)",
                },
                "path": {
                    "type": "string",
                    "description": "Root path to search from (default: current directory)",
                },
                "include": {
                    "type": "string",
                    "description": "File pattern to include (e.g., '*.py')",
                },
            },
            "required": ["pattern"],
        },
    )
)

register(
    Tool(
        name="directory_list",
        description="List directory contents with file sizes and types",
        fn=_directory_list,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list (default: current directory)",
                },
            },
            "required": [],
        },
    )
)
