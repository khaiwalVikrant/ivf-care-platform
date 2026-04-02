"""Application entry point — wires Database, sub-agents, orchestrator, and FastAPI."""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from task_manager.db.database import Database
from task_manager.db.seed_data import seed_price_benchmarks
from task_manager.agents import (
    TaskManagerSubAgent,
    CalendarSubAgent,
    NotesSubAgent,
    AppointmentSubAgent,
    PathologySubAgent,
    MedicationSubAgent,
    NurseSubAgent,
    ReminderSubAgent,
    CostGuardSubAgent,
)
from task_manager.orchestrator import TaskOrchestrator
from task_manager.api.app import create_app

# ---------------------------------------------------------------------------
# Singleton instances
# ---------------------------------------------------------------------------

_db: Database | None = None
_orchestrator: TaskOrchestrator | None = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db


def get_orchestrator() -> TaskOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        db = get_db()
        agents = [
            TaskManagerSubAgent(db),
            CalendarSubAgent(db),
            NotesSubAgent(db),
            AppointmentSubAgent(db),
            PathologySubAgent(db),
            MedicationSubAgent(db),
            NurseSubAgent(db),
            ReminderSubAgent(db),
            CostGuardSubAgent(db),
        ]
        _orchestrator = TaskOrchestrator(sub_agents=agents, db=db)
    return _orchestrator


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_db()
    await db.init_db()
    await seed_price_benchmarks(db)
    yield


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = create_app(get_db, get_orchestrator, lifespan)

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("task_manager.main:app", host="0.0.0.0", port=port, reload=False)
