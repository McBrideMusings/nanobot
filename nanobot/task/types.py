"""Task types."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Task:
    """A tracked unit of autonomous agent work."""
    id: str
    type: Literal["heartbeat", "cron"]
    status: Literal["running", "completed", "failed"]
    label: str
    session_key: str
    created_at_ms: int
    completed_at_ms: int | None = None
    summary: str = ""
    metadata: dict = field(default_factory=dict)
    error: str | None = None
