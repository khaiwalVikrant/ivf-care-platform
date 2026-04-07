"""Pydantic v2 data models for the multi-agent task manager."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Core enums
# ---------------------------------------------------------------------------


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class WorkflowStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------


class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    status: TaskStatus
    priority: Priority
    due_date: datetime | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("title")
    @classmethod
    def title_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title must not be empty or whitespace-only")
        return v


class Event(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    recurrence_rule: str | None = None
    created_at: datetime


class Note(BaseModel):
    id: str
    title: str
    body: str
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

    @field_validator("body")
    @classmethod
    def body_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("body must not be empty or whitespace-only")
        return v


class StepTransition(BaseModel):
    from_status: WorkflowStatus
    to_status: WorkflowStatus
    timestamp: datetime
    detail: str | None = None


class WorkflowStep(BaseModel):
    step_id: str
    capability: str
    input: dict[str, Any] = {}
    output: dict[str, Any] | None = None
    status: WorkflowStatus
    error: str | None = None
    transitions: list[StepTransition] = []


class Workflow(BaseModel):
    workflow_id: str
    request: str
    status: WorkflowStatus
    steps: list[WorkflowStep]
    created_at: datetime
    completed_at: datetime | None = None
    failure_step: str | None = None
    failure_detail: str | None = None


class StepResult(BaseModel):
    step_id: str
    capability: str
    output: dict[str, Any] | None = None
    error: str | None = None


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    detail: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# IVF domain enums
# ---------------------------------------------------------------------------


class IVFStage(str, Enum):
    baseline = "baseline"
    stimulation = "stimulation"
    trigger = "trigger"
    retrieval = "retrieval"
    fertilisation = "fertilisation"
    transfer = "transfer"
    luteal_support = "luteal_support"
    pregnancy_test = "pregnancy_test"


class AppointmentType(str, Enum):
    consultation = "consultation"
    ultrasound = "ultrasound"
    egg_retrieval = "egg_retrieval"
    embryo_transfer = "embryo_transfer"


class CriticalityLevel(str, Enum):
    normal = "normal"
    critical = "critical"


# ---------------------------------------------------------------------------
# IVF domain models
# ---------------------------------------------------------------------------


class IVFCycle(BaseModel):
    id: str
    patient_id: str
    current_stage: IVFStage
    stage_history: list[dict[str, Any]] = []
    created_at: datetime
    completed_at: datetime | None = None


class Appointment(BaseModel):
    id: str
    patient_id: str
    type: AppointmentType
    datetime: datetime
    location: str
    checklist: list[str] = []
    post_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class PathologyOrder(BaseModel):
    id: str
    patient_id: str
    cycle_id: str
    ivf_stage: IVFStage
    tests: list[str]
    collection_status: str = "pending"
    created_at: datetime


class PathologyResult(BaseModel):
    id: str
    order_id: str
    test_name: str
    value: str
    unit: str
    reference_range: str
    abnormal: bool
    recorded_at: datetime


class MedicationSchedule(BaseModel):
    id: str
    patient_id: str
    cycle_id: str
    drug_name: str
    dose: str
    frequency: str
    route: str
    start_date: date
    end_date: date
    dose_history: list[dict[str, Any]] = []


class MedicationAdministration(BaseModel):
    id: str
    schedule_id: str
    administered_by: str
    administered_at: datetime
    actual_dose: str
    nurse_visit_id: str | None = None


class NurseVisit(BaseModel):
    id: str
    patient_id: str
    nurse_id: str
    scheduled_at: datetime
    status: str = "scheduled"
    medication_administration_id: str
    escalated_at: datetime | None = None


class Reminder(BaseModel):
    id: str
    patient_id: str
    linked_record_id: str
    linked_record_type: str
    scheduled_at: datetime
    criticality: CriticalityLevel
    acknowledged: bool = False
    acknowledged_at: datetime | None = None
    escalation_count: int = 0


class CostRecord(BaseModel):
    id: str
    patient_id: str
    cycle_id: str
    category: str
    amount: float
    currency: str = "INR"
    linked_record_id: str
    flagged_unnecessary: bool = False
    created_at: datetime


class PatientRecord(BaseModel):
    id: str
    name: str
    mobile_number: str
    email: str | None = None
    patient_id: str
    active_cycle_id: str | None = None
    created_at: datetime


class PriceBenchmark(BaseModel):
    id: str
    item_name: str
    item_type: str
    benchmark_price: float
    currency: str = "INR"
    updated_at: datetime
    # Enums
    "TaskStatus",
    "Priority",
    "WorkflowStatus",
    "IVFStage",
    "AppointmentType",
    "CriticalityLevel",
    # Core models
    "Task",
    "Event",
    "Note",
    "StepTransition",
    "WorkflowStep",
    "Workflow",
    "StepResult",
    "ErrorResponse",
    # IVF models
    "IVFCycle",
    "Appointment",
    "PathologyOrder",
    "PathologyResult",
    "MedicationSchedule",
    "MedicationAdministration",
    "NurseVisit",
    "Reminder",
    "CostRecord",
    "PriceBenchmark",
]
