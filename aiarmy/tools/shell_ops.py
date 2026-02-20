import subprocess
from .registry import Tool, register


def _shell_exec(command: str, working_dir: str = ".", timeout: int = 30) -> str:
    """Execute a shell command and return combined stdout and stderr."""
    if not command or not command.strip():
        return "Error: command cannot be empty"

    if timeout > 300:
        return "Error: timeout cannot exceed 300 seconds"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=working_dir,
            check=False,
        )
        # Combine stdout and stderr
        output = result.stdout + result.stderr
        return output if output else ""
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s"
    except Exception as e:
        return f"Error: {type(e).__name__}: {str(e)}"


register(
    Tool(
        name="shell_exec",
        description="Execute a shell command. Returns stdout and stderr combined. Use for running scripts, installing packages, building projects, git commands, etc.",
        fn=_shell_exec,
        requires_hitl=True,
        input_schema={
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute",
                },
                "working_dir": {
                    "type": "string",
                    "description": "Working directory (default: current directory)",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30, max: 300)",
                },
            },
            "required": ["command"],
        },
    )
)
