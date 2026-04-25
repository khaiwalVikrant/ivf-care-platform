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

    ONBOARDING = "onboarding"
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
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_email: Optional[str] = None
    cycle_id: Optional[str] = None
    last_updated: Optional[datetime] = None


class Session(BaseModel):
    """Represents a single continuous conversation between a patient and the agent."""

    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    state: ConversationState = ConversationState.ONBOARDING
    profile: Optional[PatientProfile] = None
    disclaimer_acknowledged: bool = True
    topics_discussed: list[str] = Field(default_factory=list)
    tool_invocations: list[str] = Field(default_factory=list)
    turn_count: int = 0
    # Patient identity — set during onboarding
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    patient_email: Optional[str] = None
    cycle_id: Optional[str] = None
    onboarding_step: int = 0  # tracks which onboarding question we're on
    profile_opted_in: bool = False  # True once patient explicitly opts in to profile saving


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


# ---------------------------------------------------------------------------
# New tool output models (Phase 2)
# ---------------------------------------------------------------------------


class SuccessRateOutput(BaseModel):
    """Structured output from success_rate_tool."""

    age_band: str
    base_rate_low: float
    base_rate_high: float
    adjusted_rate_low: Optional[float] = None
    adjusted_rate_high: Optional[float] = None
    adjustment_explanation: Optional[str] = None
    cumulative_note: Optional[str] = None
    data_source: str
    disclaimer: str


class LabResultOutput(BaseModel):
    """Structured output from lab_result_tool."""

    amh_classification: Optional[str] = None
    amh_explanation: Optional[str] = None
    fsh_classification: Optional[str] = None
    fsh_explanation: Optional[str] = None
    afc_classification: Optional[str] = None
    afc_explanation: Optional[str] = None
    combined_interpretation: Optional[str] = None
    age_context: Optional[str] = None
    disclaimer: str


class TimelineEvent(BaseModel):
    """A single event in an IVF treatment timeline."""

    date: str
    day_number: int
    event_name: str
    description: str


class TimelineOutput(BaseModel):
    """Structured output from timeline_tool."""

    events: list[TimelineEvent]
    protocol: str
    transfer_type: str
    clinic_adjustment_note: str


class RedFlagOutput(BaseModel):
    """Structured output from red_flag_tool."""

    flags_found: list[str]
    risk_level: str
    explanation: str
    legitimate_clinic_note: str


class EmotionalSupportOutput(BaseModel):
    """Structured output from emotional_support_tool."""

    distress_level: str
    empathy_response: str
    coping_strategies: list[str]
    support_resources: dict
    crisis_mode: bool
