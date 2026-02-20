import os
import subprocess
from pathlib import Path
from .registry import Tool, register


def _file_rename(old_path: str, new_path: str) -> str:
    try:
        old = Path(old_path).resolve()
        new = Path(new_path).resolve()

        if not old.exists():
            return f"Error: file not found — {old_path}"

        old.rename(new)
        return f"Renamed: {old_path} → {new_path}"
    except Exception as e:
        return f"Error: {e}"


def _package_install(package: str, manager: str = "pip") -> str:
    try:
        if manager == "pip":
            cmd = ["pip", "install", package]
        elif manager == "npm":
            cmd = ["npm", "install", package]
        else:
            return f"Error: unsupported package manager — {manager}"

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            return f"Error: {result.stderr}"

        return f"Installed: {package} via {manager}\n{result.stdout}"
    except subprocess.TimeoutExpired:
        return f"Error: package installation timed out (120s)"
    except Exception as e:
        return f"Error: {e}"


def _env_read(name: str) -> str:
    sensitive_keywords = ["SECRET", "PASSWORD", "KEY", "TOKEN"]

    if any(keyword in name.upper() for keyword in sensitive_keywords):
        return f"Error: cannot read sensitive environment variable — {name}"

    value = os.environ.get(name)
    if value is None:
        return f"Not set: {name}"

    return f"{name}={value}"


register(
    Tool(
        name="file_rename",
        description="Rename or move a file",
        fn=_file_rename,
        requires_hitl=True,
        input_schema={
            "type": "object",
            "properties": {
                "old_path": {"type": "string", "description": "Current file path"},
                "new_path": {"type": "string", "description": "New file path"},
            },
            "required": ["old_path", "new_path"],
        },
    )
)

register(
    Tool(
        name="package_install",
        description="Install a package using pip or npm",
        fn=_package_install,
        requires_hitl=True,
        input_schema={
            "type": "object",
            "properties": {
                "package": {"type": "string", "description": "Package name to install"},
                "manager": {
                    "type": "string",
                    "description": "Package manager: 'pip' or 'npm' (default: pip)",
                },
            },
            "required": ["package"],
        },
    )
)

register(
    Tool(
        name="env_read",
        description="Read an environment variable",
        fn=_env_read,
        requires_hitl=False,
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Environment variable name"},
            },
            "required": ["name"],
        },
    )
)
