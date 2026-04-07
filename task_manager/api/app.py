"""FastAPI application factory — core and IVF endpoints."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Callable, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from task_manager.db.database import Database
from task_manager.models import (
    AppointmentType,
    CriticalityLevel,
    IVFStage,
    Priority,
    TaskStatus,
)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)


def _require_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    return credentials.credentials


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class SubmitRequest(BaseModel):
    request: str


class CreateTaskRequest(BaseModel):
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.pending
    priority: Priority = Priority.medium
    due_date: datetime | None = None


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    priority: Priority | None = None
    due_date: datetime | None = None


class CreateEventRequest(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    recurrence_rule: str | None = None


class CreateNoteRequest(BaseModel):
    title: str
    body: str
    tags: list[str] = []


class BookAppointmentRequest(BaseModel):
    patient_id: str
    type: AppointmentType
    scheduled_at: datetime
    location: str


class RescheduleAppointmentRequest(BaseModel):
    datetime: Optional[datetime] = None
    status: Optional[str] = None


class OrderPathologyRequest(BaseModel):
    patient_id: str
    cycle_id: str
    ivf_stage: IVFStage
    tests: list[str]


class CreateMedicationScheduleRequest(BaseModel):
    patient_id: str
    cycle_id: str
    drug_name: str
    dose: str
    frequency: str
    route: str
    start_date: str  # ISO date
    end_date: str    # ISO date


class AdjustDoseRequest(BaseModel):
    dose: str


class BookNurseVisitRequest(BaseModel):
    patient_id: str
    nurse_id: str
    scheduled_at: datetime
    medication_administration_id: str


class ScheduleReminderRequest(BaseModel):
    patient_id: str
    linked_record_id: str
    linked_record_type: str
    scheduled_at: datetime
    criticality: CriticalityLevel = CriticalityLevel.normal


class AuditBillRequest(BaseModel):
    patient_id: str
    cycle_id: str
    line_items: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app(
    get_db: Callable[[], Database],
    get_orchestrator: Callable[[], Any],
    lifespan: Any = None,
) -> FastAPI:
    app = FastAPI(title="Multi-Agent Task Manager", lifespan=lifespan)

    # ------------------------------------------------------------------
    # POST /requests
    # ------------------------------------------------------------------

    @app.post("/requests", status_code=status.HTTP_202_ACCEPTED)
    async def submit_request(
        body: SubmitRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, str]:
        orch = get_orchestrator()
        result = await orch.submit(body.request)
        # result is either a Workflow or an ErrorResponse
        if hasattr(result, "error_code"):
            raise HTTPException(status_code=400, detail=result.model_dump())
        workflow = result
        # Fire-and-forget execution in background
        asyncio.create_task(orch.execute(workflow))
        return {"workflow_id": workflow.workflow_id}

    # ------------------------------------------------------------------
    # GET /workflows/{workflow_id}
    # ------------------------------------------------------------------

    @app.get("/workflows/{workflow_id}")
    async def get_workflow(
        workflow_id: str,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        workflow = await db.get_workflow(workflow_id)
        if workflow is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        return workflow.model_dump(mode="json")

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    @app.get("/")
    async def health_check() -> dict:
        return {"status": "ok", "service": "ivf-care-platform task-manager-api"}

    # ------------------------------------------------------------------
    # Patients
    # ------------------------------------------------------------------

    @app.get("/patients")
    async def get_patient(
        mobile: str | None = None,
        patient_id: str | None = None,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        if mobile:
            patient = await db.get_patient_by_mobile(mobile)
        elif patient_id:
            patient = await db.get_patient_by_id(patient_id)
        else:
            raise HTTPException(status_code=400, detail="Provide mobile or patient_id")
        if patient is None:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient.model_dump(mode="json")

    @app.post("/patients", status_code=status.HTTP_201_CREATED)
    async def create_patient(
        body: dict[str, Any],
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        patient = await db.create_patient(
            name=body.get("name", ""),
            mobile_number=body.get("mobile_number", ""),
            email=body.get("email"),
        )
        # Auto-create first IVF cycle
        cycle = await db.create_ivf_cycle(
            patient_id=patient.patient_id,
        )
        await db.update_patient(patient.patient_id, active_cycle_id=cycle.id)
        patient = await db.get_patient_by_id(patient.patient_id)
        return patient.model_dump(mode="json")

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    @app.get("/tasks")
    async def list_tasks(
        status: TaskStatus | None = None,
        priority: Priority | None = None,
        _token: str = Depends(_require_token),
    ) -> list[dict[str, Any]]:
        db = get_db()
        tasks = await db.query_tasks(status=status, priority=priority)
        return [t.model_dump(mode="json") for t in tasks]

    @app.post("/tasks", status_code=status.HTTP_201_CREATED)
    async def create_task(
        body: CreateTaskRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        task = await db.create_task(
            title=body.title,
            description=body.description,
            status=body.status,
            priority=body.priority,
            due_date=body.due_date,
        )
        return task.model_dump(mode="json")

    @app.patch("/tasks/{task_id}")
    async def update_task(
        task_id: str,
        body: UpdateTaskRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        updates = body.model_dump(exclude_none=True)
        task = await db.update_task(task_id, **updates)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task.model_dump(mode="json")

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    @app.get("/events")
    async def list_events(
        start_from: datetime | None = None,
        start_to: datetime | None = None,
        _token: str = Depends(_require_token),
    ) -> list[dict[str, Any]]:
        db = get_db()
        events = await db.query_events(start_from=start_from, start_to=start_to)
        return [e.model_dump(mode="json") for e in events]

    @app.post("/events", status_code=status.HTTP_201_CREATED)
    async def create_event(
        body: CreateEventRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        if body.start_time > body.end_time:
            raise HTTPException(status_code=400, detail="start_time must not be after end_time")
        event = await db.create_event(
            title=body.title,
            start_time=body.start_time,
            end_time=body.end_time,
            recurrence_rule=body.recurrence_rule,
        )
        return event.model_dump(mode="json")

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    @app.get("/notes")
    async def search_notes(
        keyword: str | None = None,
        tag: str | None = None,
        _token: str = Depends(_require_token),
    ) -> list[dict[str, Any]]:
        db = get_db()
        notes = await db.search_notes(keyword=keyword, tag=tag)
        return [n.model_dump(mode="json") for n in notes]

    @app.get("/notes/semantic-search")
    async def semantic_search_notes(
        query: str,
        limit: int = 5,
        _token: str = Depends(_require_token),
    ) -> list[dict[str, Any]]:
        db = get_db()
        return await db.semantic_search_notes(query=query, limit=limit)

    @app.get("/pathology/semantic-search")
    async def semantic_search_pathology(
        query: str,
        patient_id: str | None = None,
        limit: int = 5,
        _token: str = Depends(_require_token),
    ) -> list[dict[str, Any]]:
        db = get_db()
        return await db.semantic_search_pathology(query=query, patient_id=patient_id, limit=limit)

    @app.post("/notes", status_code=status.HTTP_201_CREATED)
    async def create_note(
        body: CreateNoteRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        note = await db.create_note(title=body.title, body=body.body, tags=body.tags)
        return note.model_dump(mode="json")

    # ------------------------------------------------------------------
    # Appointments
    # ------------------------------------------------------------------

    @app.post("/appointments", status_code=status.HTTP_201_CREATED)
    async def book_appointment(
        body: BookAppointmentRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        appt = await db.create_appointment(
            patient_id=body.patient_id,
            type=body.type,
            datetime_=body.scheduled_at,
            location=body.location,
        )
        return appt.model_dump(mode="json")

    @app.get("/appointments")
    async def list_appointments(
        patient_id: str | None = None,
        _token: str = Depends(_require_token),
    ) -> list[dict[str, Any]]:
        db = get_db()
        appointments = await db.query_appointments(patient_id=patient_id)
        return [a.model_dump(mode="json") for a in appointments]

    @app.get("/appointments/{appointment_id}")
    async def get_appointment(
        appointment_id: str,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        appt = await db.get_appointment(appointment_id)
        if appt is None:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return appt.model_dump(mode="json")

    @app.patch("/appointments/{appointment_id}")
    async def update_appointment(
        appointment_id: str,
        body: RescheduleAppointmentRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        updates = body.model_dump(exclude_none=True)
        appt = await db.update_appointment(appointment_id, **updates)
        if appt is None:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return appt.model_dump(mode="json")

    # ------------------------------------------------------------------
    # Pathology
    # ------------------------------------------------------------------

    @app.post("/pathology/orders", status_code=status.HTTP_201_CREATED)
    async def order_pathology(
        body: OrderPathologyRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        order = await db.create_pathology_order(
            patient_id=body.patient_id,
            cycle_id=body.cycle_id,
            ivf_stage=body.ivf_stage,
            tests=body.tests,
        )
        return order.model_dump(mode="json")

    @app.get("/pathology/results")
    async def get_pathology_results(
        order_id: str | None = None,
        patient_id: str | None = None,
        cycle_id: str | None = None,
        _token: str = Depends(_require_token),
    ) -> list[dict[str, Any]]:
        db = get_db()
        results = await db.query_pathology_results(
            order_id=order_id, patient_id=patient_id, cycle_id=cycle_id
        )
        return [r.model_dump(mode="json") for r in results]

    # ------------------------------------------------------------------
    # Medications
    # ------------------------------------------------------------------

    @app.post("/medications/schedules", status_code=status.HTTP_201_CREATED)
    async def create_medication_schedule(
        body: CreateMedicationScheduleRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        from datetime import date as date_type
        db = get_db()
        schedule = await db.create_medication_schedule(
            patient_id=body.patient_id,
            cycle_id=body.cycle_id,
            drug_name=body.drug_name,
            dose=body.dose,
            frequency=body.frequency,
            route=body.route,
            start_date=date_type.fromisoformat(body.start_date),
            end_date=date_type.fromisoformat(body.end_date),
        )
        return schedule.model_dump(mode="json")

    @app.patch("/medications/schedules/{schedule_id}")
    async def adjust_dose(
        schedule_id: str,
        body: AdjustDoseRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        schedule = await db.get_medication_schedule(schedule_id)
        if schedule is None:
            raise HTTPException(status_code=404, detail="Medication schedule not found")
        # Preserve dose history
        history = list(schedule.dose_history)
        history.append({"dose": schedule.dose, "changed_at": datetime.utcnow().isoformat()})
        updated = await db.update_medication_schedule(
            schedule_id, dose=body.dose, dose_history=history
        )
        return updated.model_dump(mode="json")

    # ------------------------------------------------------------------
    # Nurse visits
    # ------------------------------------------------------------------

    @app.post("/nurse-visits", status_code=status.HTTP_201_CREATED)
    async def book_nurse_visit(
        body: BookNurseVisitRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        visit = await db.create_nurse_visit(
            patient_id=body.patient_id,
            nurse_id=body.nurse_id,
            scheduled_at=body.scheduled_at,
            medication_administration_id=body.medication_administration_id,
        )
        return visit.model_dump(mode="json")

    @app.patch("/nurse-visits/{visit_id}/confirm")
    async def confirm_nurse_visit(
        visit_id: str,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        visit = await db.update_nurse_visit(visit_id, status="confirmed")
        if visit is None:
            raise HTTPException(status_code=404, detail="Nurse visit not found")
        return visit.model_dump(mode="json")

    # ------------------------------------------------------------------
    # Reminders
    # ------------------------------------------------------------------

    @app.post("/reminders", status_code=status.HTTP_201_CREATED)
    async def schedule_reminder(
        body: ScheduleReminderRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        reminder = await db.create_reminder(
            patient_id=body.patient_id,
            linked_record_id=body.linked_record_id,
            linked_record_type=body.linked_record_type,
            scheduled_at=body.scheduled_at,
            criticality=body.criticality,
        )
        return reminder.model_dump(mode="json")

    @app.get("/reminders")
    async def list_reminders(
        patient_id: str | None = None,
        _token: str = Depends(_require_token),
    ) -> list[dict[str, Any]]:
        db = get_db()
        reminders = await db.query_reminders(patient_id=patient_id)
        return [r.model_dump(mode="json") for r in reminders]

    @app.patch("/reminders/{reminder_id}/acknowledge")
    async def acknowledge_reminder(
        reminder_id: str,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        reminder = await db.update_reminder(
            reminder_id,
            acknowledged=True,
            acknowledged_at=datetime.utcnow(),
        )
        if reminder is None:
            raise HTTPException(status_code=404, detail="Reminder not found")
        return reminder.model_dump(mode="json")

    # ------------------------------------------------------------------
    # IVF cycles
    # ------------------------------------------------------------------

    @app.get("/cycles/{cycle_id}/summary")
    async def get_cycle_summary(
        cycle_id: str,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        orch = get_orchestrator()
        summary = await orch.get_cycle_summary(cycle_id)
        if summary.get("error_code"):
            raise HTTPException(status_code=404, detail=summary)
        return summary

    # ------------------------------------------------------------------
    # Costs
    # ------------------------------------------------------------------

    class CreateCostRecordRequest(BaseModel):
        patient_id: str
        cycle_id: str
        category: str
        amount: float
        linked_record_id: str = ""
        currency: str = "INR"
        flagged_unnecessary: bool = False

    @app.post("/costs/records", status_code=status.HTTP_201_CREATED)
    async def create_cost_record(
        body: CreateCostRecordRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        if not body.patient_id or not body.cycle_id:
            raise HTTPException(status_code=400, detail="patient_id and cycle_id are required")
        record = await db.create_cost_record(
            patient_id=body.patient_id,
            cycle_id=body.cycle_id,
            category=body.category,
            amount=body.amount,
            linked_record_id=body.linked_record_id,
            currency=body.currency,
            flagged_unnecessary=body.flagged_unnecessary,
        )
        return record.model_dump(mode="json")

    @app.get("/costs/summary")
    async def cost_summary(
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        records = await db.query_cost_records(patient_id=patient_id, cycle_id=cycle_id)
        by_category: dict[str, float] = {}
        for r in records:
            by_category[r.category] = by_category.get(r.category, 0.0) + r.amount
        grand_total = sum(by_category.values())
        return {
            "patient_id": patient_id,
            "cycle_id": cycle_id,
            "breakdown": by_category,
            "grand_total": grand_total,
            "currency": "INR",
        }

    @app.post("/costs/audit")
    async def audit_bill(
        body: AuditBillRequest,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        records = await db.query_cost_records(
            patient_id=body.patient_id, cycle_id=body.cycle_id
        )
        record_map = {r.linked_record_id: r for r in records}
        discrepancies = []
        for item in body.line_items:
            rec_id = item.get("linked_record_id", "")
            billed = float(item.get("amount", 0))
            record = record_map.get(rec_id)
            if record is None:
                discrepancies.append({"linked_record_id": rec_id, "issue": "not found in cost records"})
            elif abs(billed - record.amount) > 0:
                discrepancies.append({
                    "linked_record_id": rec_id,
                    "billed": billed,
                    "recorded": record.amount,
                    "discrepancy": billed - record.amount,
                })
        return {"discrepancies": discrepancies, "total_items": len(body.line_items)}

    @app.get("/costs/insurance-summary")
    async def insurance_summary(
        patient_id: str,
        cycle_id: str,
        _token: str = Depends(_require_token),
    ) -> dict[str, Any]:
        db = get_db()
        records = await db.query_cost_records(patient_id=patient_id, cycle_id=cycle_id)
        total = sum(r.amount for r in records)
        return {
            "patient_id": patient_id,
            "cycle_id": cycle_id,
            "total_claimable": total,
            "currency": "INR",
            "records": [r.model_dump(mode="json") for r in records],
        }

    return app
