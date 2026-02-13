"""Lightweight pub/sub event bus for agent observability."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable

from loguru import logger


@dataclass
class AgentEvent:
    """A single observable event from the agent system."""

    category: str   # "agent", "heartbeat", "subagent", "cron"
    event: str      # "thinking_started", "tool_call", "tool_result", "thinking_finished", etc.
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class EventBus:
    """
    Fire-and-forget pub/sub for AgentEvents.

    No persistence, no queuing.  Subscribers receive events as they happen;
    missed events on reconnect are acceptable.
    """

    def __init__(self) -> None:
        self._subscribers: list[Callable[[AgentEvent], Awaitable[None]]] = []

    async def publish(self, event: AgentEvent) -> None:
        """Publish an event to all subscribers (fire-and-forget)."""
        for cb in self._subscribers:
            try:
                await cb(event)
            except Exception as e:
                logger.warning(f"EventBus subscriber error: {e}")

    def subscribe(self, callback: Callable[[AgentEvent], Awaitable[None]]) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[AgentEvent], Awaitable[None]]) -> None:
        self._subscribers = [cb for cb in self._subscribers if cb is not callback]
