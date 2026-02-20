from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from .memory import SessionMemory


class SessionManager:
    def __init__(self, base_dir: Path | None = None):
        if base_dir is None:
            base_dir = Path.home() / ".aiarmy"
        self.base_dir = Path(base_dir)
        self.sessions_dir = self.base_dir / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, session_id: str, memory: SessionMemory, state: dict) -> None:
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(exist_ok=True)

        with (session_dir / "full.json").open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "messages": [
                        {"role": m.role, "content": m.content} for m in memory.messages
                    ],
                    "context": memory.context,
                },
                f,
                indent=2,
            )

        with (session_dir / "working.json").open("w", encoding="utf-8") as f:
            json.dump(memory.working_set, f, indent=2)

        with (session_dir / "state.json").open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

        with (session_dir / "metadata.json").open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "session_id": session_id,
                    "created_at": state.get(
                        "created_at", datetime.now(UTC).isoformat()
                    ),
                    "last_updated": datetime.now(UTC).isoformat(),
                    "message_count": len(memory.messages),
                    "token_count": state.get("tokens_used", 0),
                },
                f,
                indent=2,
            )

        with (self.base_dir / "current_session").open("w", encoding="utf-8") as f:
            f.write(session_id)

    def load_session(self, session_id: str) -> tuple[SessionMemory, dict] | None:
        session_dir = self.sessions_dir / session_id
        if not session_dir.exists():
            return None

        with (session_dir / "full.json").open(encoding="utf-8") as f:
            data = json.load(f)

        memory = SessionMemory(session_id=session_id)
        for msg in data["messages"]:
            memory.add(msg["role"], msg["content"])
        memory.context = data.get("context", {})

        working_file = session_dir / "working.json"
        if working_file.exists():
            with working_file.open(encoding="utf-8") as f:
                memory.working_set = json.load(f)

        with (session_dir / "state.json").open(encoding="utf-8") as f:
            state = json.load(f)

        return memory, state

    def get_last_session(self) -> str | None:
        current_file = self.base_dir / "current_session"
        if current_file.exists():
            session_id = current_file.read_text(encoding="utf-8").strip()
            if (self.sessions_dir / session_id).exists():
                return session_id
        return None

    def list_sessions(self) -> list[dict]:
        sessions = []
        for session_dir in self.sessions_dir.iterdir():
            if session_dir.is_dir():
                metadata_file = session_dir / "metadata.json"
                if metadata_file.exists():
                    with metadata_file.open(encoding="utf-8") as f:
                        sessions.append(json.load(f))
        return sorted(sessions, key=lambda x: x["last_updated"], reverse=True)
