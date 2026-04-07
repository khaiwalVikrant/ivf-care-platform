"""SQLAlchemy ORM definitions and Database facade for the task_manager."""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    select,
    delete,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from task_manager import config
from task_manager.models import (
    Appointment,
    AppointmentType,
    CostRecord,
    CriticalityLevel,
    ErrorResponse,
    Event,
    IVFCycle,
    IVFStage,
    MedicationAdministration,
    MedicationSchedule,
    Note,
    NurseVisit,
    PathologyOrder,
    PathologyResult,
    PatientRecord,
    PriceBenchmark,
    Priority,
    Reminder,
    StepTransition,
    Task,
    TaskStatus,
    Workflow,
    WorkflowStatus,
    WorkflowStep,
)


# ---------------------------------------------------------------------------
# ORM base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# ORM table definitions
# ---------------------------------------------------------------------------


class TaskRow(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    status = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    workflow_id = Column(String, nullable=True, index=True)


class EventRow(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    recurrence_rule = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    workflow_id = Column(String, nullable=True, index=True)


class NoteRow(Base):
    __tablename__ = "notes"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    tags = Column(Text, default="[]")  # JSON list
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    workflow_id = Column(String, nullable=True, index=True)


class WorkflowRow(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True)
    request = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    failure_step = Column(String, nullable=True)
    failure_detail = Column(Text, nullable=True)


class WorkflowStepRow(Base):
    __tablename__ = "workflow_steps"

    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False, index=True)
    capability = Column(String, nullable=False)
    input_data = Column(Text, default="{}")   # JSON
    output_data = Column(Text, nullable=True)  # JSON
    status = Column(String, nullable=False)
    error = Column(Text, nullable=True)
    transitions = Column(Text, default="[]")  # JSON list of StepTransition dicts


class IVFCycleRow(Base):
    __tablename__ = "ivf_cycles"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False, index=True)
    current_stage = Column(String, nullable=False)
    stage_history = Column(Text, default="[]")  # JSON
    created_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class AppointmentRow(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)
    datetime = Column(DateTime, nullable=False)
    location = Column(String, nullable=False)
    checklist = Column(Text, default="[]")  # JSON
    post_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    workflow_id = Column(String, nullable=True, index=True)


class PathologyOrderRow(Base):
    __tablename__ = "pathology_orders"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False, index=True)
    cycle_id = Column(String, nullable=False, index=True)
    ivf_stage = Column(String, nullable=False)
    tests = Column(Text, default="[]")  # JSON
    collection_status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False)
    workflow_id = Column(String, nullable=True, index=True)


class PathologyResultRow(Base):
    __tablename__ = "pathology_results"

    id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey("pathology_orders.id"), nullable=False, index=True)
    test_name = Column(String, nullable=False)
    value = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    reference_range = Column(String, nullable=False)
    abnormal = Column(Boolean, nullable=False, default=False)
    recorded_at = Column(DateTime, nullable=False)


class MedicationScheduleRow(Base):
    __tablename__ = "medication_schedules"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False, index=True)
    cycle_id = Column(String, nullable=False, index=True)
    drug_name = Column(String, nullable=False)
    dose = Column(String, nullable=False)
    frequency = Column(String, nullable=False)
    route = Column(String, nullable=False)
    start_date = Column(String, nullable=False)  # ISO date string
    end_date = Column(String, nullable=False)    # ISO date string
    dose_history = Column(Text, default="[]")    # JSON
    workflow_id = Column(String, nullable=True, index=True)


class MedicationAdministrationRow(Base):
    __tablename__ = "medication_administrations"

    id = Column(String, primary_key=True)
    schedule_id = Column(String, ForeignKey("medication_schedules.id"), nullable=False, index=True)
    administered_by = Column(String, nullable=False)
    administered_at = Column(DateTime, nullable=False)
    actual_dose = Column(String, nullable=False)
    nurse_visit_id = Column(String, nullable=True)
    workflow_id = Column(String, nullable=True, index=True)


class NurseVisitRow(Base):
    __tablename__ = "nurse_visits"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False, index=True)
    nurse_id = Column(String, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    status = Column(String, nullable=False, default="scheduled")
    medication_administration_id = Column(String, nullable=False)
    escalated_at = Column(DateTime, nullable=True)
    workflow_id = Column(String, nullable=True, index=True)


class ReminderRow(Base):
    __tablename__ = "reminders"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False, index=True)
    linked_record_id = Column(String, nullable=False)
    linked_record_type = Column(String, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    criticality = Column(String, nullable=False)
    acknowledged = Column(Boolean, nullable=False, default=False)
    acknowledged_at = Column(DateTime, nullable=True)
    escalation_count = Column(String, nullable=False, default="0")
    workflow_id = Column(String, nullable=True, index=True)


class CostRecordRow(Base):
    __tablename__ = "cost_records"

    id = Column(String, primary_key=True)
    patient_id = Column(String, nullable=False, index=True)
    cycle_id = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="INR")
    linked_record_id = Column(String, nullable=False)
    flagged_unnecessary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False)
    workflow_id = Column(String, nullable=True, index=True)


class PriceBenchmarkRow(Base):
    __tablename__ = "price_benchmarks"

    id = Column(String, primary_key=True)
    item_name = Column(String, nullable=False, unique=True)
    item_type = Column(String, nullable=False)
    benchmark_price = Column(Float, nullable=False)
    currency = Column(String, nullable=False, default="INR")
    updated_at = Column(DateTime, nullable=False)


class PatientRow(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    mobile_number = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=True)
    patient_id = Column(String, nullable=False, unique=True, index=True)
    active_cycle_id = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.utcnow()


def _row_to_task(row: TaskRow) -> Task:
    return Task(
        id=row.id,
        title=row.title,
        description=row.description or "",
        status=TaskStatus(row.status),
        priority=Priority(row.priority),
        due_date=row.due_date,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _row_to_event(row: EventRow) -> Event:
    return Event(
        id=row.id,
        title=row.title,
        start_time=row.start_time,
        end_time=row.end_time,
        recurrence_rule=row.recurrence_rule,
        created_at=row.created_at,
    )


def _row_to_note(row: NoteRow) -> Note:
    return Note(
        id=row.id,
        title=row.title,
        body=row.body,
        tags=json.loads(row.tags or "[]"),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _row_to_workflow(row: WorkflowRow, steps: list[WorkflowStepRow]) -> Workflow:
    return Workflow(
        workflow_id=row.id,
        request=row.request,
        status=WorkflowStatus(row.status),
        steps=[_row_to_step(s) for s in steps],
        created_at=row.created_at,
        completed_at=row.completed_at,
        failure_step=row.failure_step,
        failure_detail=row.failure_detail,
    )


def _row_to_step(row: WorkflowStepRow) -> WorkflowStep:
    raw_transitions = json.loads(row.transitions or "[]")
    transitions = [
        StepTransition(
            from_status=WorkflowStatus(t["from_status"]),
            to_status=WorkflowStatus(t["to_status"]),
            timestamp=datetime.fromisoformat(t["timestamp"]),
            detail=t.get("detail"),
        )
        for t in raw_transitions
    ]
    return WorkflowStep(
        step_id=row.id,
        capability=row.capability,
        input=json.loads(row.input_data or "{}"),
        output=json.loads(row.output_data) if row.output_data else None,
        status=WorkflowStatus(row.status),
        error=row.error,
        transitions=transitions,
    )


def _row_to_appointment(row: AppointmentRow) -> Appointment:
    return Appointment(
        id=row.id,
        patient_id=row.patient_id,
        type=AppointmentType(row.type),
        datetime=row.datetime,
        location=row.location,
        checklist=json.loads(row.checklist or "[]"),
        post_notes=row.post_notes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _row_to_pathology_order(row: PathologyOrderRow) -> PathologyOrder:
    return PathologyOrder(
        id=row.id,
        patient_id=row.patient_id,
        cycle_id=row.cycle_id,
        ivf_stage=IVFStage(row.ivf_stage),
        tests=json.loads(row.tests or "[]"),
        collection_status=row.collection_status,
        created_at=row.created_at,
    )


def _row_to_pathology_result(row: PathologyResultRow) -> PathologyResult:
    return PathologyResult(
        id=row.id,
        order_id=row.order_id,
        test_name=row.test_name,
        value=row.value,
        unit=row.unit,
        reference_range=row.reference_range,
        abnormal=row.abnormal,
        recorded_at=row.recorded_at,
    )


def _row_to_medication_schedule(row: MedicationScheduleRow) -> MedicationSchedule:
    return MedicationSchedule(
        id=row.id,
        patient_id=row.patient_id,
        cycle_id=row.cycle_id,
        drug_name=row.drug_name,
        dose=row.dose,
        frequency=row.frequency,
        route=row.route,
        start_date=date.fromisoformat(row.start_date),
        end_date=date.fromisoformat(row.end_date),
        dose_history=json.loads(row.dose_history or "[]"),
    )


def _row_to_medication_administration(row: MedicationAdministrationRow) -> MedicationAdministration:
    return MedicationAdministration(
        id=row.id,
        schedule_id=row.schedule_id,
        administered_by=row.administered_by,
        administered_at=row.administered_at,
        actual_dose=row.actual_dose,
        nurse_visit_id=row.nurse_visit_id,
    )


def _row_to_nurse_visit(row: NurseVisitRow) -> NurseVisit:
    return NurseVisit(
        id=row.id,
        patient_id=row.patient_id,
        nurse_id=row.nurse_id,
        scheduled_at=row.scheduled_at,
        status=row.status,
        medication_administration_id=row.medication_administration_id,
        escalated_at=row.escalated_at,
    )


def _row_to_reminder(row: ReminderRow) -> Reminder:
    return Reminder(
        id=row.id,
        patient_id=row.patient_id,
        linked_record_id=row.linked_record_id,
        linked_record_type=row.linked_record_type,
        scheduled_at=row.scheduled_at,
        criticality=CriticalityLevel(row.criticality),
        acknowledged=row.acknowledged,
        acknowledged_at=row.acknowledged_at,
        escalation_count=int(row.escalation_count or 0),
    )


def _row_to_cost_record(row: CostRecordRow) -> CostRecord:
    return CostRecord(
        id=row.id,
        patient_id=row.patient_id,
        cycle_id=row.cycle_id,
        category=row.category,
        amount=row.amount,
        currency=row.currency,
        linked_record_id=row.linked_record_id,
        flagged_unnecessary=row.flagged_unnecessary,
        created_at=row.created_at,
    )


def _row_to_price_benchmark(row: PriceBenchmarkRow) -> PriceBenchmark:
    return PriceBenchmark(
        id=row.id,
        item_name=row.item_name,
        item_type=row.item_type,
        benchmark_price=row.benchmark_price,
        currency=row.currency,
        updated_at=row.updated_at,
    )


def _row_to_patient(row: PatientRow) -> PatientRecord:
    return PatientRecord(
        id=row.id,
        name=row.name,
        mobile_number=row.mobile_number,
        email=row.email,
        patient_id=row.patient_id,
        active_cycle_id=row.active_cycle_id,
        created_at=row.created_at,
    )


def _row_to_ivf_cycle(row: IVFCycleRow) -> IVFCycle:
    return IVFCycle(
        id=row.id,
        patient_id=row.patient_id,
        current_stage=IVFStage(row.current_stage),
        stage_history=json.loads(row.stage_history or "[]"),
        created_at=row.created_at,
        completed_at=row.completed_at,
    )


# ---------------------------------------------------------------------------
# Database facade
# ---------------------------------------------------------------------------


class Database:
    """Async SQLAlchemy-backed persistence facade.

    All writes are confirmed (flushed + committed) before returning.
    No partial commits — any exception causes a full rollback.

    In production (when ALLOYDB_PASSWORD is set), connects via the
    Cloud SQL Python Connector using the AlloyDB instance URI.
    Falls back to DATABASE_URL (SQLite) for local dev.
    """

    def __init__(self, url: str | None = None) -> None:
        if url:
            # Explicit URL passed (e.g. in tests)
            self._engine = create_async_engine(url, echo=False)
        elif config.ALLOYDB_PASSWORD:
            # Production: use Cloud SQL Python Connector for AlloyDB
            from google.cloud.alloydb.connector import AsyncConnector  # type: ignore
            import asyncpg  # type: ignore

            connector = AsyncConnector()

            async def _getconn() -> asyncpg.Connection:
                return await connector.connect(
                    config.ALLOYDB_INSTANCE_URI,
                    "asyncpg",
                    user=config.ALLOYDB_USER,
                    password=config.ALLOYDB_PASSWORD,
                    db=config.ALLOYDB_DB,
                )

            self._engine = create_async_engine(
                "postgresql+asyncpg://",
                async_creator=_getconn,
                echo=False,
            )
        else:
            # Local dev: SQLite
            self._engine = create_async_engine(config.DATABASE_URL, echo=False)

        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_db(self) -> None:
        """Create all tables and initialize vector extensions (idempotent)."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        # Initialize pgvector extension and embedding columns on AlloyDB
        from task_manager.db.vector_search import init_vector_extensions
        await init_vector_extensions(self._engine)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    async def create_task(
        self,
        title: str,
        description: str = "",
        status: TaskStatus = TaskStatus.pending,
        priority: Priority = Priority.medium,
        due_date: datetime | None = None,
        workflow_id: str | None = None,
    ) -> Task:
        if not title or not title.strip():
            raise ValueError("title must not be empty or whitespace-only")
        if not isinstance(status, TaskStatus):
            raise ValueError(f"invalid status: {status!r}")
        now = _now()
        row = TaskRow(
            id=_new_id(),
            title=title,
            description=description,
            status=status.value,
            priority=priority.value,
            due_date=due_date,
            created_at=now,
            updated_at=now,
            workflow_id=workflow_id,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_task(row)

    async def get_task(self, task_id: str) -> Task | None:
        async with self._session_factory() as session:
            result = await session.execute(select(TaskRow).where(TaskRow.id == task_id))
            row = result.scalar_one_or_none()
            return _row_to_task(row) if row else None

    async def update_task(self, task_id: str, **fields: Any) -> Task | None:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(select(TaskRow).where(TaskRow.id == task_id))
                row = result.scalar_one_or_none()
                if row is None:
                    return None
                for key, value in fields.items():
                    if hasattr(row, key) and value is not None:
                        if isinstance(value, (TaskStatus, Priority)):
                            setattr(row, key, value.value)
                        else:
                            setattr(row, key, value)
                row.updated_at = _now()
                session.add(row)
        return _row_to_task(row)

    async def query_tasks(
        self,
        status: TaskStatus | None = None,
        priority: Priority | None = None,
        due_date_from: datetime | None = None,
        due_date_to: datetime | None = None,
    ) -> list[Task]:
        stmt = select(TaskRow)
        if status is not None:
            stmt = stmt.where(TaskRow.status == status.value)
        if priority is not None:
            stmt = stmt.where(TaskRow.priority == priority.value)
        if due_date_from is not None:
            stmt = stmt.where(TaskRow.due_date >= due_date_from)
        if due_date_to is not None:
            stmt = stmt.where(TaskRow.due_date <= due_date_to)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return [_row_to_task(r) for r in result.scalars().all()]

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    async def create_event(
        self,
        title: str,
        start_time: datetime,
        end_time: datetime,
        recurrence_rule: str | None = None,
        workflow_id: str | None = None,
    ) -> Event:
        now = _now()
        row = EventRow(
            id=_new_id(),
            title=title,
            start_time=start_time,
            end_time=end_time,
            recurrence_rule=recurrence_rule,
            created_at=now,
            workflow_id=workflow_id,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_event(row)

    async def get_event(self, event_id: str) -> Event | None:
        async with self._session_factory() as session:
            result = await session.execute(select(EventRow).where(EventRow.id == event_id))
            row = result.scalar_one_or_none()
            return _row_to_event(row) if row else None

    async def query_events(
        self,
        start_from: datetime | None = None,
        start_to: datetime | None = None,
    ) -> list[Event]:
        stmt = select(EventRow)
        if start_from is not None:
            stmt = stmt.where(EventRow.start_time >= start_from)
        if start_to is not None:
            stmt = stmt.where(EventRow.start_time <= start_to)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return [_row_to_event(r) for r in result.scalars().all()]

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------

    async def create_note(
        self,
        title: str,
        body: str,
        tags: list[str] | None = None,
        workflow_id: str | None = None,
    ) -> Note:
        if not body or not body.strip():
            raise ValueError("body must not be empty or whitespace-only")
        now = _now()
        row = NoteRow(
            id=_new_id(),
            title=title,
            body=body,
            tags=json.dumps(tags or []),
            created_at=now,
            updated_at=now,
            workflow_id=workflow_id,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_note(row)

    async def get_note(self, note_id: str) -> Note | None:
        async with self._session_factory() as session:
            result = await session.execute(select(NoteRow).where(NoteRow.id == note_id))
            row = result.scalar_one_or_none()
            return _row_to_note(row) if row else None

    async def search_notes(
        self,
        keyword: Optional[str] = None,
        tag: Optional[str] = None
    ) -> list[Note]:
        async with self._session_factory() as session:
            result = await session.execute(select(NoteRow))
            rows = result.scalars().all()
        notes = [_row_to_note(r) for r in rows]
        if keyword:
            kw = keyword.lower()
            notes = [n for n in notes if kw in n.title.lower() or kw in n.body.lower()]
        if tag:
            notes = [n for n in notes if tag in n.tags]
        return notes

    async def semantic_search_notes(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """Search notes using AlloyDB vector similarity search.

        Falls back to keyword search if embeddings are unavailable.
        """
        from task_manager.db.vector_search import semantic_search_notes
        return await semantic_search_notes(self._session_factory, query, limit)

    async def semantic_search_pathology(
        self,
        query: str,
        patient_id: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Search pathology results using AlloyDB vector similarity search."""
        from task_manager.db.vector_search import semantic_search_pathology
        return await semantic_search_pathology(self._session_factory, query, patient_id, limit)

    # ------------------------------------------------------------------
    # Patients
    # ------------------------------------------------------------------

    async def get_patient_by_mobile(self, mobile_number: str) -> PatientRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PatientRow).where(PatientRow.mobile_number == mobile_number)
            )
            row = result.scalar_one_or_none()
            return _row_to_patient(row) if row else None

    async def get_patient_by_id(self, patient_id: str) -> PatientRecord | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PatientRow).where(PatientRow.patient_id == patient_id)
            )
            row = result.scalar_one_or_none()
            return _row_to_patient(row) if row else None

    async def create_patient(
        self,
        name: str,
        mobile_number: str,
        email: str | None = None,
        active_cycle_id: str | None = None,
    ) -> PatientRecord:
        patient_id = f"P-{_new_id()[:8].upper()}"
        now = _now()
        row = PatientRow(
            id=_new_id(),
            name=name,
            mobile_number=mobile_number,
            email=email,
            patient_id=patient_id,
            active_cycle_id=active_cycle_id,
            created_at=now,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_patient(row)

    async def update_patient(self, patient_id: str, **fields: Any) -> PatientRecord | None:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(PatientRow).where(PatientRow.patient_id == patient_id)
                )
                row = result.scalar_one_or_none()
                if row is None:
                    return None
                for key, value in fields.items():
                    if hasattr(row, key) and value is not None:
                        setattr(row, key, value)
                session.add(row)
        return _row_to_patient(row)

    # ------------------------------------------------------------------
    # Workflows
    # ------------------------------------------------------------------

    async def create_workflow(
        self,
        request: str,
        steps: list[dict[str, Any]],
    ) -> Workflow:
        now = _now()
        wf_id = _new_id()
        wf_row = WorkflowRow(
            id=wf_id,
            request=request,
            status=WorkflowStatus.pending.value,
            created_at=now,
        )
        step_rows = [
            WorkflowStepRow(
                id=s.get("step_id", _new_id()),
                workflow_id=wf_id,
                capability=s["capability"],
                input_data=json.dumps(s.get("input", {})),
                status=WorkflowStatus.pending.value,
            )
            for s in steps
        ]
        async with self._session_factory() as session:
            async with session.begin():
                session.add(wf_row)
                for sr in step_rows:
                    session.add(sr)
        async with self._session_factory() as session:
            result = await session.execute(
                select(WorkflowStepRow).where(WorkflowStepRow.workflow_id == wf_id)
            )
            loaded_steps = result.scalars().all()
        return _row_to_workflow(wf_row, list(loaded_steps))

    async def get_workflow(self, workflow_id: str) -> Workflow | None:
        async with self._session_factory() as session:
            wf_result = await session.execute(
                select(WorkflowRow).where(WorkflowRow.id == workflow_id)
            )
            wf_row = wf_result.scalar_one_or_none()
            if wf_row is None:
                return None
            steps_result = await session.execute(
                select(WorkflowStepRow).where(WorkflowStepRow.workflow_id == workflow_id)
            )
            step_rows = steps_result.scalars().all()
        return _row_to_workflow(wf_row, list(step_rows))

    async def update_workflow_step(
        self,
        workflow_id: str,
        step_id: str,
        status: WorkflowStatus,
        output: dict[str, Any] | None = None,
        error: str | None = None,
        transition: StepTransition | None = None,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(WorkflowStepRow).where(WorkflowStepRow.id == step_id)
                )
                row = result.scalar_one_or_none()
                if row is None:
                    return
                row.status = status.value
                if output is not None:
                    row.output_data = json.dumps(output)
                if error is not None:
                    row.error = error
                if transition is not None:
                    existing = json.loads(row.transitions or "[]")
                    existing.append({
                        "from_status": transition.from_status.value,
                        "to_status": transition.to_status.value,
                        "timestamp": transition.timestamp.isoformat(),
                        "detail": transition.detail,
                    })
                    row.transitions = json.dumps(existing)
                session.add(row)

    async def update_workflow_status(
        self,
        workflow_id: str,
        status: WorkflowStatus,
        failure_step: str | None = None,
        failure_detail: str | None = None,
        completed_at: datetime | None = None,
    ) -> None:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(WorkflowRow).where(WorkflowRow.id == workflow_id)
                )
                row = result.scalar_one_or_none()
                if row is None:
                    return
                row.status = status.value
                if failure_step is not None:
                    row.failure_step = failure_step
                if failure_detail is not None:
                    row.failure_detail = failure_detail
                if completed_at is not None:
                    row.completed_at = completed_at
                session.add(row)

    async def rollback_workflow(self, workflow_id: str) -> None:
        """Delete all records tagged with this workflow_id in a single transaction."""
        async with self._session_factory() as session:
            async with session.begin():
                for table in [
                    TaskRow, EventRow, NoteRow, AppointmentRow,
                    PathologyOrderRow, MedicationScheduleRow,
                    MedicationAdministrationRow, NurseVisitRow,
                    ReminderRow, CostRecordRow,
                ]:
                    await session.execute(
                        delete(table).where(table.workflow_id == workflow_id)
                    )

    # ------------------------------------------------------------------
    # Appointments
    # ------------------------------------------------------------------

    async def create_appointment(
        self,
        patient_id: str,
        type: AppointmentType,
        datetime_: datetime,
        location: str,
        checklist: list[str] | None = None,
        workflow_id: str | None = None,
    ) -> Appointment:
        now = _now()
        row = AppointmentRow(
            id=_new_id(),
            patient_id=patient_id,
            type=type.value,
            datetime=datetime_,
            location=location,
            checklist=json.dumps(checklist or []),
            created_at=now,
            updated_at=now,
            workflow_id=workflow_id,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_appointment(row)

    async def get_appointment(self, appointment_id: str) -> Appointment | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(AppointmentRow).where(AppointmentRow.id == appointment_id)
            )
            row = result.scalar_one_or_none()
            return _row_to_appointment(row) if row else None

    async def update_appointment(self, appointment_id: str, **fields: Any) -> Appointment | None:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(AppointmentRow).where(AppointmentRow.id == appointment_id)
                )
                row = result.scalar_one_or_none()
                if row is None:
                    return None
                for key, value in fields.items():
                    if hasattr(row, key) and value is not None:
                        if key == "checklist" and isinstance(value, list):
                            setattr(row, key, json.dumps(value))
                        elif isinstance(value, AppointmentType):
                            setattr(row, key, value.value)
                        else:
                            setattr(row, key, value)
                row.updated_at = _now()
                session.add(row)
        return _row_to_appointment(row)

    async def query_appointments(
        self,
        patient_id: str | None = None,
    ) -> list[Appointment]:
        stmt = select(AppointmentRow)
        if patient_id:
            stmt = stmt.where(AppointmentRow.patient_id == patient_id)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return [_row_to_appointment(r) for r in result.scalars().all()]

    # ------------------------------------------------------------------
    # Pathology orders
    # ------------------------------------------------------------------

    async def create_pathology_order(
        self,
        patient_id: str,
        cycle_id: str,
        ivf_stage: IVFStage,
        tests: list[str],
        workflow_id: str | None = None,
    ) -> PathologyOrder:
        now = _now()
        row = PathologyOrderRow(
            id=_new_id(),
            patient_id=patient_id,
            cycle_id=cycle_id,
            ivf_stage=ivf_stage.value,
            tests=json.dumps(tests),
            collection_status="pending",
            created_at=now,
            workflow_id=workflow_id,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_pathology_order(row)

    async def get_pathology_order(self, order_id: str) -> PathologyOrder | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PathologyOrderRow).where(PathologyOrderRow.id == order_id)
            )
            row = result.scalar_one_or_none()
            return _row_to_pathology_order(row) if row else None

    async def update_pathology_order(self, order_id: str, **fields: Any) -> PathologyOrder | None:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(PathologyOrderRow).where(PathologyOrderRow.id == order_id)
                )
                row = result.scalar_one_or_none()
                if row is None:
                    return None
                for key, value in fields.items():
                    if hasattr(row, key) and value is not None:
                        setattr(row, key, value)
                session.add(row)
        return _row_to_pathology_order(row)

    # ------------------------------------------------------------------
    # Pathology results
    # ------------------------------------------------------------------

    async def create_pathology_result(
        self,
        order_id: str,
        test_name: str,
        value: str,
        unit: str,
        reference_range: str,
        abnormal: bool,
    ) -> PathologyResult:
        row = PathologyResultRow(
            id=_new_id(),
            order_id=order_id,
            test_name=test_name,
            value=value,
            unit=unit,
            reference_range=reference_range,
            abnormal=abnormal,
            recorded_at=_now(),
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_pathology_result(row)

    async def query_pathology_results(
        self,
        order_id: str | None = None,
        patient_id: str | None = None,
        cycle_id: str | None = None,
    ) -> list[PathologyResult]:
        if patient_id is not None or cycle_id is not None:
            # Join with orders to filter by patient/cycle
            stmt = (
                select(PathologyResultRow)
                .join(PathologyOrderRow, PathologyResultRow.order_id == PathologyOrderRow.id)
            )
            if patient_id:
                stmt = stmt.where(PathologyOrderRow.patient_id == patient_id)
            if cycle_id:
                stmt = stmt.where(PathologyOrderRow.cycle_id == cycle_id)
        else:
            stmt = select(PathologyResultRow)
            if order_id:
                stmt = stmt.where(PathologyResultRow.order_id == order_id)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return [_row_to_pathology_result(r) for r in result.scalars().all()]

    async def query_medication_history(
        self,
        patient_id: str,
        cycle_id: str,
    ) -> dict:
        """Return schedules and administrations for a patient/cycle."""
        schedules_stmt = (
            select(MedicationScheduleRow)
            .where(MedicationScheduleRow.patient_id == patient_id)
            .where(MedicationScheduleRow.cycle_id == cycle_id)
        )
        async with self._session_factory() as session:
            sched_result = await session.execute(schedules_stmt)
            schedule_rows = sched_result.scalars().all()
            schedules = [_row_to_medication_schedule(r) for r in schedule_rows]

            schedule_ids = [s.id for s in schedules]
            administrations: list[MedicationAdministration] = []
            if schedule_ids:
                admin_stmt = select(MedicationAdministrationRow).where(
                    MedicationAdministrationRow.schedule_id.in_(schedule_ids)
                )
                admin_result = await session.execute(admin_stmt)
                administrations = [
                    _row_to_medication_administration(r)
                    for r in admin_result.scalars().all()
                ]

        return {
            "schedules": [s.model_dump(mode="json") for s in schedules],
            "administrations": [a.model_dump(mode="json") for a in administrations],
        }

    # ------------------------------------------------------------------
    # Medication schedules
    # ------------------------------------------------------------------

    async def create_medication_schedule(
        self,
        patient_id: str,
        cycle_id: str,
        drug_name: str,
        dose: str,
        frequency: str,
        route: str,
        start_date: date,
        end_date: date,
        workflow_id: str | None = None,
    ) -> MedicationSchedule:
        row = MedicationScheduleRow(
            id=_new_id(),
            patient_id=patient_id,
            cycle_id=cycle_id,
            drug_name=drug_name,
            dose=dose,
            frequency=frequency,
            route=route,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            dose_history=json.dumps([]),
            workflow_id=workflow_id,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_medication_schedule(row)

    async def get_medication_schedule(self, schedule_id: str) -> MedicationSchedule | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(MedicationScheduleRow).where(MedicationScheduleRow.id == schedule_id)
            )
            row = result.scalar_one_or_none()
            return _row_to_medication_schedule(row) if row else None

    async def update_medication_schedule(
        self, schedule_id: str, **fields: Any
    ) -> MedicationSchedule | None:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(MedicationScheduleRow).where(MedicationScheduleRow.id == schedule_id)
                )
                row = result.scalar_one_or_none()
                if row is None:
                    return None
                for key, value in fields.items():
                    if hasattr(row, key) and value is not None:
                        if key == "dose_history" and isinstance(value, list):
                            setattr(row, key, json.dumps(value))
                        elif key in ("start_date", "end_date") and isinstance(value, date):
                            setattr(row, key, value.isoformat())
                        else:
                            setattr(row, key, value)
                session.add(row)
        return _row_to_medication_schedule(row)

    # ------------------------------------------------------------------
    # Medication administrations
    # ------------------------------------------------------------------

    async def create_medication_administration(
        self,
        schedule_id: str,
        administered_by: str,
        administered_at: datetime,
        actual_dose: str,
        nurse_visit_id: str | None = None,
        workflow_id: str | None = None,
    ) -> MedicationAdministration:
        row = MedicationAdministrationRow(
            id=_new_id(),
            schedule_id=schedule_id,
            administered_by=administered_by,
            administered_at=administered_at,
            actual_dose=actual_dose,
            nurse_visit_id=nurse_visit_id,
            workflow_id=workflow_id,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_medication_administration(row)

    # ------------------------------------------------------------------
    # Nurse visits
    # ------------------------------------------------------------------

    async def create_nurse_visit(
        self,
        patient_id: str,
        nurse_id: str,
        scheduled_at: datetime,
        medication_administration_id: str,
        workflow_id: str | None = None,
    ) -> NurseVisit:
        row = NurseVisitRow(
            id=_new_id(),
            patient_id=patient_id,
            nurse_id=nurse_id,
            scheduled_at=scheduled_at,
            status="scheduled",
            medication_administration_id=medication_administration_id,
            workflow_id=workflow_id,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_nurse_visit(row)

    async def get_nurse_visit(self, visit_id: str) -> NurseVisit | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(NurseVisitRow).where(NurseVisitRow.id == visit_id)
            )
            row = result.scalar_one_or_none()
            return _row_to_nurse_visit(row) if row else None

    async def update_nurse_visit(self, visit_id: str, **fields: Any) -> NurseVisit | None:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(NurseVisitRow).where(NurseVisitRow.id == visit_id)
                )
                row = result.scalar_one_or_none()
                if row is None:
                    return None
                for key, value in fields.items():
                    if hasattr(row, key) and value is not None:
                        setattr(row, key, value)
                session.add(row)
        return _row_to_nurse_visit(row)

    async def query_nurse_visits(
        self,
        patient_id: str | None = None,
        status: str | None = None,
    ) -> list[NurseVisit]:
        stmt = select(NurseVisitRow)
        if patient_id:
            stmt = stmt.where(NurseVisitRow.patient_id == patient_id)
        if status:
            stmt = stmt.where(NurseVisitRow.status == status)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return [_row_to_nurse_visit(r) for r in result.scalars().all()]

    # ------------------------------------------------------------------
    # Reminders
    # ------------------------------------------------------------------

    async def create_reminder(
        self,
        patient_id: str,
        linked_record_id: str,
        linked_record_type: str,
        scheduled_at: datetime,
        criticality: CriticalityLevel,
        workflow_id: str | None = None,
    ) -> Reminder:
        row = ReminderRow(
            id=_new_id(),
            patient_id=patient_id,
            linked_record_id=linked_record_id,
            linked_record_type=linked_record_type,
            scheduled_at=scheduled_at,
            criticality=criticality.value,
            acknowledged=False,
            escalation_count="0",
            workflow_id=workflow_id,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_reminder(row)

    async def get_reminder(self, reminder_id: str) -> Reminder | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(ReminderRow).where(ReminderRow.id == reminder_id)
            )
            row = result.scalar_one_or_none()
            return _row_to_reminder(row) if row else None

    async def update_reminder(self, reminder_id: str, **fields: Any) -> Reminder | None:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(ReminderRow).where(ReminderRow.id == reminder_id)
                )
                row = result.scalar_one_or_none()
                if row is None:
                    return None
                for key, value in fields.items():
                    if hasattr(row, key):
                        if key == "escalation_count":
                            setattr(row, key, str(value))
                        else:
                            setattr(row, key, value)
                session.add(row)
        return _row_to_reminder(row)

    async def query_reminders(
        self,
        patient_id: str | None = None,
    ) -> list[Reminder]:
        stmt = select(ReminderRow)
        if patient_id:
            stmt = stmt.where(ReminderRow.patient_id == patient_id)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return [_row_to_reminder(r) for r in result.scalars().all()]

    # ------------------------------------------------------------------
    # Cost records
    # ------------------------------------------------------------------

    async def create_cost_record(
        self,
        patient_id: str,
        cycle_id: str,
        category: str,
        amount: float,
        linked_record_id: str,
        currency: str = "INR",
        flagged_unnecessary: bool = False,
        workflow_id: str | None = None,
    ) -> CostRecord:
        row = CostRecordRow(
            id=_new_id(),
            patient_id=patient_id,
            cycle_id=cycle_id,
            category=category,
            amount=amount,
            currency=currency,
            linked_record_id=linked_record_id,
            flagged_unnecessary=flagged_unnecessary,
            created_at=_now(),
            workflow_id=workflow_id,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_cost_record(row)

    async def query_cost_records(
        self,
        patient_id: str | None = None,
        cycle_id: str | None = None,
    ) -> list[CostRecord]:
        stmt = select(CostRecordRow)
        if patient_id:
            stmt = stmt.where(CostRecordRow.patient_id == patient_id)
        if cycle_id:
            stmt = stmt.where(CostRecordRow.cycle_id == cycle_id)
        async with self._session_factory() as session:
            result = await session.execute(stmt)
            return [_row_to_cost_record(r) for r in result.scalars().all()]

    # ------------------------------------------------------------------
    # Price benchmarks
    # ------------------------------------------------------------------

    async def create_price_benchmark(
        self,
        item_name: str,
        item_type: str,
        benchmark_price: float,
        currency: str = "INR",
    ) -> PriceBenchmark:
        row = PriceBenchmarkRow(
            id=_new_id(),
            item_name=item_name,
            item_type=item_type,
            benchmark_price=benchmark_price,
            currency=currency,
            updated_at=_now(),
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_price_benchmark(row)

    async def get_price_benchmark(self, item_name: str) -> PriceBenchmark | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(PriceBenchmarkRow).where(PriceBenchmarkRow.item_name == item_name)
            )
            row = result.scalar_one_or_none()
            return _row_to_price_benchmark(row) if row else None

    # ------------------------------------------------------------------
    # IVF cycles
    # ------------------------------------------------------------------

    async def create_ivf_cycle(
        self,
        patient_id: str,
        current_stage: IVFStage = IVFStage.baseline,
    ) -> IVFCycle:
        now = _now()
        row = IVFCycleRow(
            id=_new_id(),
            patient_id=patient_id,
            current_stage=current_stage.value,
            stage_history=json.dumps([]),
            created_at=now,
        )
        async with self._session_factory() as session:
            async with session.begin():
                session.add(row)
        return _row_to_ivf_cycle(row)

    async def get_ivf_cycle(self, cycle_id: str) -> IVFCycle | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(IVFCycleRow).where(IVFCycleRow.id == cycle_id)
            )
            row = result.scalar_one_or_none()
            return _row_to_ivf_cycle(row) if row else None

    async def update_ivf_cycle(self, cycle_id: str, **fields: Any) -> IVFCycle | None:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(IVFCycleRow).where(IVFCycleRow.id == cycle_id)
                )
                row = result.scalar_one_or_none()
                if row is None:
                    return None
                for key, value in fields.items():
                    if hasattr(row, key) and value is not None:
                        if key == "stage_history" and isinstance(value, list):
                            setattr(row, key, json.dumps(value))
                        elif isinstance(value, IVFStage):
                            setattr(row, key, value.value)
                        else:
                            setattr(row, key, value)
                session.add(row)
        return _row_to_ivf_cycle(row)
