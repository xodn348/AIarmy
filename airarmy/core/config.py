import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent


class Config:
    AUTH_MODE: str = os.getenv("AUTH_MODE", "api_key")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_SESSION_KEY: str = os.getenv("CLAUDE_SESSION_KEY", "")

    COMMANDER_MODEL: str = os.getenv("COMMANDER_MODEL", "claude-opus-4-5")
    SPECIALIST_MODEL: str = os.getenv("SPECIALIST_MODEL", "claude-sonnet-4-5")

    MAX_TOKENS_PER_RUN: int = int(os.getenv("MAX_TOKENS_PER_RUN", "8000"))
    MAX_TOKENS_PER_SESSION: int = int(os.getenv("MAX_TOKENS_PER_SESSION", "100000"))
    MAX_AGENT_TURNS: int = int(os.getenv("MAX_AGENT_TURNS", "10"))

    HITL_REQUIRED_ACTIONS: set[str] = set(
        os.getenv(
            "HITL_REQUIRED_ACTIONS",
            "file_delete,git_push,shell_exec,package_install,file_rename",
        ).split(",")
    )

    AUDIT_LOG_PATH: Path = BASE_DIR / os.getenv("AUDIT_LOG_PATH", "logs/audit.db")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        if cls.AUTH_MODE == "api_key":
            if not cls.ANTHROPIC_API_KEY:
                raise ValueError(
                    "AUTH_MODE=api_key but ANTHROPIC_API_KEY is not set.\n"
                    "Run: cp .env.example .env && edit .env"
                )
        elif cls.AUTH_MODE == "session_key":
            if not cls.CLAUDE_SESSION_KEY:
                raise ValueError(
                    "AUTH_MODE=session_key but CLAUDE_SESSION_KEY is not set.\n"
                    "Get your session key from claude.ai (browser cookies) and add to .env"
                )
        else:
            raise ValueError(
                f"Invalid AUTH_MODE: {cls.AUTH_MODE}. Must be 'api_key' or 'session_key'"
            )

        cls.AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


config = Config()
