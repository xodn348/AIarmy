import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent.parent


class Config:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    COMMANDER_MODEL: str = os.getenv("COMMANDER_MODEL", "claude-opus-4-5")
    SPECIALIST_MODEL: str = os.getenv("SPECIALIST_MODEL", "claude-sonnet-4-5")

    MAX_TOKENS_PER_RUN: int = int(os.getenv("MAX_TOKENS_PER_RUN", "8000"))
    MAX_TOKENS_PER_SESSION: int = int(os.getenv("MAX_TOKENS_PER_SESSION", "100000"))
    MAX_AGENT_TURNS: int = int(os.getenv("MAX_AGENT_TURNS", "10"))

    HITL_REQUIRED_ACTIONS: set[str] = set(
        os.getenv("HITL_REQUIRED_ACTIONS", "file_delete,git_push,shell_exec").split(",")
    )

    AUDIT_LOG_PATH: Path = BASE_DIR / os.getenv("AUDIT_LOG_PATH", "logs/audit.db")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set.\nRun: cp .env.example .env && edit .env"
            )
        cls.AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


config = Config()
