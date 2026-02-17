"""Task store: JSON persistence for task records."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Literal

from loguru import logger

from nanobot.task.types import Task

_MAX_TASKS = 200


def _now_ms() -> int:
    return int(time.time() * 1000)


class TaskStore:
    """JSON file persistence for tasks."""

    def __init__(self, store_path: Path) -> None:
        self._path = store_path
        self._tasks: list[Task] = []
        self._load()

    # -- public API --

    def add(
        self,
        type: Literal["heartbeat", "cron"],
        label: str,
        session_key: str,
        metadata: dict | None = None,
    ) -> Task:
        """Create and persist a new running task. Returns the task."""
        task = Task(
            id=f"{type[:2]}-{uuid.uuid4().hex[:6]}",
            type=type,
            status="running",
            label=label,
            session_key=session_key,
            created_at_ms=_now_ms(),
            metadata=metadata or {},
        )
        self._tasks.append(task)
        self._prune()
        self._save()
        return task

    def get(self, task_id: str) -> Task | None:
        for t in self._tasks:
            if t.id == task_id:
                return t
        return None

    def update(
        self,
        task_id: str,
        status: Literal["running", "completed", "failed"] | None = None,
        summary: str | None = None,
        error: str | None = None,
    ) -> Task | None:
        task = self.get(task_id)
        if not task:
            return None
        if status:
            task.status = status
        if summary is not None:
            task.summary = summary
        if error is not None:
            task.error = error
        if status in ("completed", "failed"):
            task.completed_at_ms = _now_ms()
        self._save()
        return task

    def list_recent(self, limit: int = 50) -> list[Task]:
        """Return most recent tasks, newest first."""
        return list(reversed(self._tasks))[:limit]

    # -- serialization --

    def _load(self) -> None:
        if not self._path.exists():
            self._tasks = []
            return
        try:
            raw = json.loads(self._path.read_text())
            self._tasks = [
                Task(
                    id=t["id"],
                    type=t["type"],
                    status=t["status"],
                    label=t["label"],
                    session_key=t["sessionKey"],
                    created_at_ms=t["createdAtMs"],
                    completed_at_ms=t.get("completedAtMs"),
                    summary=t.get("summary", ""),
                    metadata=t.get("metadata", {}),
                    error=t.get("error"),
                )
                for t in raw.get("tasks", [])
            ]
        except Exception as e:
            logger.warning(f"Failed to load task store: {e}")
            self._tasks = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "tasks": [
                {
                    "id": t.id,
                    "type": t.type,
                    "status": t.status,
                    "label": t.label,
                    "sessionKey": t.session_key,
                    "createdAtMs": t.created_at_ms,
                    "completedAtMs": t.completed_at_ms,
                    "summary": t.summary,
                    "metadata": t.metadata,
                    "error": t.error,
                }
                for t in self._tasks
            ],
        }
        self._path.write_text(json.dumps(data, indent=2))

    def _prune(self) -> None:
        """Keep only the most recent _MAX_TASKS entries."""
        if len(self._tasks) > _MAX_TASKS:
            self._tasks = self._tasks[-_MAX_TASKS:]
