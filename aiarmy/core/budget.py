from dataclasses import dataclass, field

from .config import config


@dataclass
class BudgetTracker:
    session_id: str
    tokens_used: int = 0
    runs: int = 0

    def record(self, tokens: int) -> None:
        self.tokens_used += tokens
        self.runs += 1

    def check_run_budget(self, estimated_tokens: int = 0) -> None:
        if self.tokens_used + estimated_tokens > config.MAX_TOKENS_PER_SESSION:
            raise BudgetExceededError(
                f"Session budget exceeded: {self.tokens_used}/{config.MAX_TOKENS_PER_SESSION} tokens used."
            )

    def remaining(self) -> int:
        return max(0, config.MAX_TOKENS_PER_SESSION - self.tokens_used)

    def summary(self) -> str:
        pct = (self.tokens_used / config.MAX_TOKENS_PER_SESSION) * 100
        return f"{self.tokens_used:,}/{config.MAX_TOKENS_PER_SESSION:,} tokens ({pct:.1f}%)"


class BudgetExceededError(Exception):
    pass
