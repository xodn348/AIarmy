from __future__ import annotations

import json
import uuid
from typing import Any
from datetime import datetime

import httpx
from curl_cffi import requests

from .config import config


class ClaudeSessionClient:
    BASE_URL = "https://claude.ai/api"

    def __init__(self, session_key: str):
        self.cookie = (
            session_key
            if session_key.startswith("sessionKey=")
            else f"sessionKey={session_key}"
        )
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.organization_id: str | None = None
        self.conversation_id: str | None = None

    def _get_headers(self, referer: str = "https://claude.ai/chats") -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": referer,
            "Origin": "https://claude.ai",
            "Content-Type": "application/json",
            "Cookie": self.cookie,
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    def get_organization_id(self) -> str:
        if self.organization_id:
            return self.organization_id

        url = f"{self.BASE_URL}/organizations"
        headers = self._get_headers()

        try:
            response = requests.get(
                url, headers=headers, impersonate="chrome110", timeout=30
            )
            response.raise_for_status()
            orgs = response.json()

            if not orgs:
                raise RuntimeError("No organizations found. Check your session key.")

            self.organization_id = orgs[0]["uuid"]
            return self.organization_id
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                raise RuntimeError(
                    "Session key expired or invalid. Re-login to claude.ai and update CLAUDE_SESSION_KEY."
                )
            raise RuntimeError(f"Failed to get organization: {e}")

    def create_conversation(self) -> str:
        org_id = self.get_organization_id()
        url = f"{self.BASE_URL}/organizations/{org_id}/chat_conversations"

        new_uuid = str(uuid.uuid4())
        payload = {"name": "", "uuid": new_uuid}
        headers = self._get_headers()

        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                impersonate="chrome110",
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            self.conversation_id = result["uuid"]
            return self.conversation_id
        except requests.HTTPError as e:
            raise RuntimeError(f"Failed to create conversation: {e}")

    def send_message(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-5",
        max_tokens: int = 8000,
        system: str = "",
        conversation_id: str | None = None,
    ) -> tuple[str, int]:
        if not conversation_id:
            if not self.conversation_id:
                self.create_conversation()
            conversation_id = self.conversation_id

        org_id = self.get_organization_id()
        url = f"{self.BASE_URL}/organizations/{org_id}/chat_conversations/{conversation_id}/completion"

        payload = {
            "prompt": f"{system}\n\n{prompt}" if system else prompt,
            "timezone": "America/Chicago",
            "attachments": [],
            "files": [],
        }

        headers = self._get_headers(referer=f"https://claude.ai/chat/{conversation_id}")
        headers["Accept"] = "text/event-stream"

        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                impersonate="chrome110",
                timeout=240,
            )
            response.raise_for_status()

            return self._parse_sse_response(response.content.decode("utf-8"))

        except requests.HTTPError as e:
            if e.response.status_code == 429:
                error_data = e.response.json()
                if "error" in error_data and "resets_at" in error_data["error"]:
                    reset_time = datetime.fromtimestamp(
                        error_data["error"]["resets_at"]
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    raise RuntimeError(f"Rate limit exceeded. Resets at {reset_time}")
            raise RuntimeError(f"Failed to send message: {e}")

    def _parse_sse_response(self, data: str) -> tuple[str, int]:
        completions = []
        input_tokens = 0
        output_tokens = 0

        for line in data.split("\n"):
            if not line.startswith("data: "):
                continue

            json_str = line[6:]
            if not json_str.strip():
                continue

            try:
                event = json.loads(json_str)

                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        completions.append(delta.get("text", ""))

                if "completion" in event:
                    completions.append(event["completion"])

                if "error" in event:
                    error = event["error"]
                    if "resets_at" in error:
                        reset_time = datetime.fromtimestamp(
                            error["resets_at"]
                        ).strftime("%Y-%m-%d %H:%M:%S")
                        raise RuntimeError(f"Rate limit. Resets at {reset_time}")
                    raise RuntimeError(
                        f"API error: {error.get('message', 'Unknown error')}"
                    )

                if "usage" in event:
                    input_tokens = event["usage"].get("input_tokens", 0)
                    output_tokens = event["usage"].get("output_tokens", 0)

            except json.JSONDecodeError:
                continue

        content = "".join(completions)
        if not content:
            raise RuntimeError("No response from Claude. Possible rate limit or error.")

        total_tokens = input_tokens + output_tokens
        if total_tokens == 0:
            total_tokens = len(content.split()) * 2

        return content, total_tokens

    def delete_conversation(self, conversation_id: str | None = None) -> None:
        if not conversation_id:
            conversation_id = self.conversation_id

        if not conversation_id:
            return

        org_id = self.get_organization_id()
        url = f"{self.BASE_URL}/organizations/{org_id}/chat_conversations/{conversation_id}"
        headers = self._get_headers()

        try:
            requests.delete(url, headers=headers, impersonate="chrome110", timeout=30)
        except Exception:
            pass
