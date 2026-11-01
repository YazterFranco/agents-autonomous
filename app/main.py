"""FastAPI surface for submitting and inspecting autonomous agent tasks."""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.agent.graph import run_agent
from app.config import get_settings

logging.basicConfig(level=get_settings().log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Local LangGraph Agent",
    description="Autonomous LangChain/LangGraph agent running locally via Docker + Ollama",
    version="0.1.0",
)


class TaskStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class TaskCreate(BaseModel):
    goal: str = Field(..., min_length=1, description="What the agent should accomplish")
    thread_id: str | None = Field(
        default=None,
        description="Optional thread id to continue a prior conversation",
    )


class TaskView(BaseModel):
    id: str
    thread_id: str
    goal: str
    status: TaskStatus
    created_at: str
    updated_at: str
    result: str | None = None
    error: str | None = None
    messages: list[dict[str, str]] = Field(default_factory=list)


_tasks: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_task(task_id: str) -> None:
    with _lock:
        task = _tasks[task_id]
        task["status"] = TaskStatus.running
        task["updated_at"] = _now()
        goal = task["goal"]
        thread_id = task["thread_id"]

    try:
        outcome = run_agent(goal, thread_id=thread_id)
        with _lock:
            task = _tasks[task_id]
            task["status"] = TaskStatus.completed
            task["result"] = outcome["result"]
            task["messages"] = outcome["messages"]
            task["updated_at"] = _now()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Task %s failed", task_id)
        with _lock:
            task = _tasks[task_id]
            task["status"] = TaskStatus.failed
            task["error"] = str(exc)
            task["updated_at"] = _now()


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "model": settings.ollama_model,
        "ollama": settings.ollama_base_url,
    }


@app.post("/tasks", response_model=TaskView, status_code=202)
def create_task(body: TaskCreate) -> TaskView:
    task_id = str(uuid.uuid4())
    thread_id = body.thread_id or task_id
    now = _now()
    record = {
        "id": task_id,
        "thread_id": thread_id,
        "goal": body.goal,
        "status": TaskStatus.queued,
        "created_at": now,
        "updated_at": now,
        "result": None,
        "error": None,
        "messages": [],
    }
    with _lock:
        _tasks[task_id] = record

    worker = threading.Thread(target=_run_task, args=(task_id,), daemon=True)
    worker.start()
    return TaskView(**record)


@app.get("/tasks", response_model=list[TaskView])
def list_tasks() -> list[TaskView]:
    with _lock:
        items = sorted(_tasks.values(), key=lambda t: t["created_at"], reverse=True)
        return [TaskView(**item) for item in items]


@app.get("/tasks/{task_id}", response_model=TaskView)
def get_task(task_id: str) -> TaskView:
    with _lock:
        task = _tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return TaskView(**task)
