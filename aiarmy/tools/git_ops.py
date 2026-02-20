import subprocess
from pathlib import Path
from .registry import Tool, register


def _run_git(args: list[str], cwd: str = ".") -> str:
    """Run a git command via subprocess with timeout."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return f"Error: {result.stderr}"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: git command timed out (60s)"
    except Exception as e:
        return f"Error: {str(e)}"


def _git_init(path: str = ".") -> str:
    """Initialize a new git repository."""
    return _run_git(["init"], cwd=path)


def _git_status(path: str = ".") -> str:
    """Get the status of a git repository."""
    return _run_git(["status"], cwd=path)


def _git_diff(path: str = ".", staged: bool = False) -> str:
    """Show git diff. If staged=True, show staged changes."""
    args = ["diff"]
    if staged:
        args.append("--staged")
    return _run_git(args, cwd=path)


def _git_add(path: str = ".", files: str = ".") -> str:
    """Add files to the staging area."""
    return _run_git(["add", files], cwd=path)


def _git_commit(path: str = ".", message: str = "") -> str:
    """Commit staged changes with a message."""
    if not message:
        return "Error: commit message is required"
    return _run_git(["commit", "-m", message], cwd=path)


def _git_push(path: str = ".", remote: str = "origin", branch: str = "") -> str:
    """Push commits to a remote repository."""
    args = ["push", remote]
    if branch:
        args.append(branch)
    return _run_git(args, cwd=path)


def _git_clone(url: str, dest: str = "") -> str:
    """Clone a git repository."""
    args = ["clone", url]
    if dest:
        args.append(dest)
    # Clone doesn't use cwd, runs in current directory
    return _run_git(args, cwd=".")


def _git_log(path: str = ".", count: int = 10) -> str:
    """Show git log with limited entries."""
    return _run_git(["log", "--oneline", f"-n", str(count)], cwd=path)


# Register all git tools
register(
    Tool(
        name="git_init",
        description="Initialize a new git repository",
        fn=_git_init,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to initialize git repository (default: current directory)",
                }
            },
            "required": [],
        },
    )
)

register(
    Tool(
        name="git_status",
        description="Get the status of a git repository",
        fn=_git_status,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to git repository (default: current directory)",
                }
            },
            "required": [],
        },
    )
)

register(
    Tool(
        name="git_diff",
        description="Show git diff. Use staged=True to show staged changes only",
        fn=_git_diff,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to git repository (default: current directory)",
                },
                "staged": {
                    "type": "boolean",
                    "description": "Show staged changes only (default: False)",
                },
            },
            "required": [],
        },
    )
)

register(
    Tool(
        name="git_add",
        description="Add files to the staging area",
        fn=_git_add,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to git repository (default: current directory)",
                },
                "files": {
                    "type": "string",
                    "description": "Files to add (default: '.' for all changes)",
                },
            },
            "required": [],
        },
    )
)

register(
    Tool(
        name="git_commit",
        description="Commit staged changes with a message",
        fn=_git_commit,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to git repository (default: current directory)",
                },
                "message": {
                    "type": "string",
                    "description": "Commit message (required)",
                },
            },
            "required": ["message"],
        },
    )
)

register(
    Tool(
        name="git_push",
        description="Push commits to a remote repository",
        fn=_git_push,
        requires_hitl=True,
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to git repository (default: current directory)",
                },
                "remote": {
                    "type": "string",
                    "description": "Remote name (default: 'origin')",
                },
                "branch": {
                    "type": "string",
                    "description": "Branch name (optional, pushes current branch if not specified)",
                },
            },
            "required": [],
        },
    )
)

register(
    Tool(
        name="git_clone",
        description="Clone a git repository",
        fn=_git_clone,
        requires_hitl=True,
        input_schema={
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Repository URL to clone",
                },
                "dest": {
                    "type": "string",
                    "description": "Destination directory (optional)",
                },
            },
            "required": ["url"],
        },
    )
)

register(
    Tool(
        name="git_log",
        description="Show git log with limited entries",
        fn=_git_log,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to git repository (default: current directory)",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of commits to show (default: 10)",
                },
            },
            "required": [],
        },
    )
)
