"""Core Pydantic data models for the IVF Treatment Advisor Agent."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ConversationState(str, Enum):
    """Tracks which phase of the conversation flow the session is in."""

    PROFILE_COLLECTION = "profile_collection"
    MAIN_LOOP = "main_loop"


class CostVariability(str, Enum):
    """Classifies how a cost component varies across patients and clinics."""

    FIXED = "fixed"
    CLINIC_VARIABLE = "clinic_variable"
    PATIENT_VARIABLE = "patient_variable"


# ---------------------------------------------------------------------------
# Patient & Session models
# ---------------------------------------------------------------------------


class PatientProfile(BaseModel):
    """Self-reported patient context collected at the start of a session.

    All data is session-scoped and never persisted beyond the active session.
    """

    age: Optional[int] = None
    diagnosis: Optional[str] = None
    prior_treatment_history: Optional[str] = None
    preferences: Optional[str] = None
    region: Optional[str] = None  # e.g. "UK", "US", "Australia" — used in Phase 2
    confirmed: bool = False  # True once the agent has reflected details back to the patient


class Session(BaseModel):
    """Represents a single continuous conversation between a patient and the agent."""

    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    state: ConversationState = ConversationState.MAIN_LOOP
    profile: Optional[PatientProfile] = None
    disclaimer_acknowledged: bool = True
    topics_discussed: list[str] = Field(default_factory=list)
    tool_invocations: list[str] = Field(default_factory=list)  # for Phase 3 logging
    turn_count: int = 0


# ---------------------------------------------------------------------------
# Journey models
# ---------------------------------------------------------------------------


class TreatmentStage(BaseModel):
    """A named phase of the IVF process."""

    name: str                          # e.g. "Ovarian Stimulation"
    slug: str                          # e.g. "ovarian_stimulation"
    sequence_number: int               # 1–8 in the standard IVF journey
    typical_duration: str              # e.g. "8–14 days"
    description: str                   # What happens during this stage
    physical_experience: str           # What the patient will feel / experience
    emotional_notes: str               # Common emotional experiences at this stage
    decisions_required: list[str]      # Actions / decisions the patient may need to make
    protocol_variations: Optional[str] = None  # How a diagnosis/protocol may alter this stage


# ---------------------------------------------------------------------------
# Cost models
# ---------------------------------------------------------------------------


class CostComponent(BaseModel):
    """A distinct category of IVF expenditure."""

    name: str                                    # e.g. "Monitoring Scans"
    description: str
    variability: CostVariability
    typical_range_low: Optional[float] = None    # In local currency
    typical_range_high: Optional[float] = None
    currency: Optional[str] = None               # e.g. "GBP", "USD"
    region: Optional[str] = None                 # Phase 2: region-specific
    notes: str                                   # e.g. "Multiple scans required per cycle"
    is_addon: bool = False                       # True for optional add-on treatments


# ---------------------------------------------------------------------------
# Tool output models
# ---------------------------------------------------------------------------


class JourneyGuideOutput(BaseModel):
    """Structured output from journey_guide_tool."""

    stages: list[TreatmentStage]
    total_timeline_estimate: str       # e.g. "4–8 weeks per cycle"
    tailored_notes: Optional[str] = None


class CostBreakdownOutput(BaseModel):
    """Structured output from cost_breakdown_tool."""

    components: list[CostComponent]
    multi_cycle_note: str
    clinic_questions: list[str]
    region: Optional[str] = None


class EvidenceSearchOutput(BaseModel):
    """Structured output from evidence_search_tool."""

    answer: str
    citations: list[str]               # Source names / guideline bodies
    confidence: str                    # "high", "moderate", "low", or "not_found"
    disclaimer: str


class ScopeGuardOutput(BaseModel):
    """Structured output from scope_guard_tool."""

    in_scope: bool
    is_emergency: bool = False
    reason: str
    referral_suggestion: Optional[str] = None


# ---------------------------------------------------------------------------
# Phase 3 logging model
# ---------------------------------------------------------------------------


class SessionLogEntry(BaseModel):
    """Structured log entry emitted per session turn — contains NO PII fields."""

    session_id: str
    turn_count: int
    topics_covered: list[str]
    tool_invocations: list[str]
