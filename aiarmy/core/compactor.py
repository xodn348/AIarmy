from __future__ import annotations

import re
from typing import TYPE_CHECKING

import anthropic
from rich.console import Console

if TYPE_CHECKING:
    from .memory import Message, SessionMemory

console = Console()


class ContextCompactor:
    def __init__(
        self,
        client: anthropic.Anthropic | None,
        threshold_tokens: int = 15000,
    ):
        self.client = client
        self.threshold_tokens = threshold_tokens

    def should_compact(self, memory: SessionMemory) -> bool:
        return memory.estimate_tokens() > self.threshold_tokens

    def compact(self, memory: SessionMemory) -> None:
        if len(memory.messages) <= 20:
            console.print("[dim]⚠️  Not enough messages to compact (need > 20)[/dim]")
            return

        if not self.client:
            console.print("[dim]⚠️  Compaction unavailable (session key mode)[/dim]")
            return

        old_messages = memory.messages[:-20]
        console.print(f"[dim]🗜️  Compacting {len(old_messages)} old messages...[/dim]")

        try:
            summary = self._summarize_messages(old_messages)
            facts = self._extract_facts(old_messages)
            decisions = self._extract_decisions(old_messages)

            if not isinstance(memory.working_set, dict):
                memory.working_set = {}
            memory.working_set.setdefault("summary", "")
            memory.working_set.setdefault("pinned_facts", [])
            memory.working_set.setdefault("decisions", [])

            memory.working_set["summary"] = summary
            memory.working_set["pinned_facts"].extend(facts)
            memory.working_set["decisions"].extend(decisions)

            memory.working_set["pinned_facts"] = list(
                set(memory.working_set["pinned_facts"])
            )
            memory.working_set["decisions"] = list(set(memory.working_set["decisions"]))

            console.print(
                "[dim]✅ Compacted: "
                f"{len(facts)} facts, {len(decisions)} decisions extracted[/dim]"
            )
        except Exception as e:
            console.print(f"[dim]⚠️  Compaction failed: {e}[/dim]")

    def _summarize_messages(self, messages: list[Message]) -> str:
        if not self.client:
            return ""

        messages_to_summarize = messages[-50:] if len(messages) > 50 else messages
        conversation_text = "\n\n".join(
            f"{m.role}: {m.content[:500]}" for m in messages_to_summarize
        )

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Summarize this conversation in 3-5 sentences. Focus on:\n"
                            "- What the user is trying to accomplish (main goal/project)\n"
                            "- Key decisions made\n"
                            "- Important context for future work\n"
                            "- Current state/progress\n\n"
                            "Conversation:\n"
                            f"{conversation_text}\n\n"
                            "Concise summary (3-5 sentences):"
                        ),
                    }
                ],
            )
            text_parts: list[str] = []
            for block in response.content:
                if block.type == "text":
                    text_parts.append(block.text)
            return "\n".join(text_parts).strip()
        except Exception as e:
            console.print(f"[dim red]Summarization failed: {e}[/dim red]")
            return "Summary unavailable due to API error."

    def _extract_facts(self, messages: list[Message]) -> list[str]:
        facts: list[str] = []

        for msg in messages:
            content_lower = msg.content.lower()

            if (
                "/users/" in content_lower
                or "/home/" in content_lower
                or "/tmp/" in content_lower
            ):
                paths = re.findall(r"(/[^\s'\"`]+)", msg.content)
                for path in paths[:3]:
                    if len(path) > 10:
                        facts.append(f"File: {path}")

            if "project:" in content_lower or "repo:" in content_lower:
                lines = [
                    line.strip()
                    for line in msg.content.split("\n")
                    if "project" in line.lower() or "repo" in line.lower()
                ]
                facts.extend(lines[:2])

            if any(
                keyword in content_lower
                for keyword in ["package:", "library:", "dependency:"]
            ):
                lines = [
                    line.strip()
                    for line in msg.content.split("\n")
                    if any(
                        keyword in line.lower()
                        for keyword in ["package", "library", "dependency"]
                    )
                ]
                facts.extend(lines[:2])

        return list(set(facts))[:15]

    def _extract_decisions(self, messages: list[Message]) -> list[str]:
        decisions: list[str] = []

        decision_keywords = [
            "decided",
            "chose",
            "using",
            "will use",
            "implemented",
            "created",
            "added",
            "renamed",
            "changed to",
            "switched to",
        ]

        for msg in messages:
            content_lower = msg.content.lower()
            if not any(keyword in content_lower for keyword in decision_keywords):
                continue

            sentences = [
                sentence.strip()
                for sentence in msg.content.split(".")
                if sentence.strip()
            ]
            decision_sentences = [
                sentence
                for sentence in sentences
                if any(keyword in sentence.lower() for keyword in decision_keywords)
                and len(sentence) < 150
            ]
            decisions.extend(decision_sentences[:2])

        return list(set(decisions))[:15]
