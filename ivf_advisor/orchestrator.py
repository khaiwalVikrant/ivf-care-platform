"""Conversation orchestrator — manages session state and routes turns to the ADK agent."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Optional

from google.adk.agents import Agent  # type: ignore
from google.adk.runners import Runner  # type: ignore
from google.adk.sessions import InMemorySessionService  # type: ignore
from google.genai import types  # type: ignore

from ivf_advisor.config import ALLOYDB_CONNECTION_STRING, GOOGLE_CLOUD_PROJECT
from ivf_advisor.models import ConversationState, PatientProfile, Session
from ivf_advisor.session import (
    AlloyDBSessionStore,
    FirestoreSessionStore,
    InMemorySessionStore,
    SessionStore,
)

_ONBOARDING_STEP_0 = (
    "👋 Welcome to IVF Care Platform!\n\n"
    "To get started, please enter your **mobile number** so I can look up your profile.\n\n"
    "_(New patient? I'll set up your profile automatically.)_"
)

_ONBOARDING_NEW_NAME = "I couldn't find an existing profile for that number. **What is your full name?**"
_ONBOARDING_NEW_EMAIL = "Thanks {name}! **What is your email address?** (Used for appointment confirmations — type 'skip' to skip)"

_ONBOARDING_RETURNING = (
    "✅ Welcome back, **{name}**!\n\n"
    "- Patient ID: `{patient_id}`\n"
    "- Active Cycle ID: `{cycle_id}`\n\n"
    "Your profile is loaded. How can I help you today?"
)

_ONBOARDING_COMPLETE = (
    "✅ Profile created! Welcome, **{name}**.\n\n"
    "- Patient ID: `{patient_id}`\n"
    "- Cycle ID: `{cycle_id}`\n\n"
    "I'll use these automatically for all your appointments, reminders, and cost tracking. "
    "Use the quick action buttons on the left to get started!"
)

_PROFILE_PROMPT = (
    "Thank you. To give you more relevant guidance, I'd like to collect a brief profile. "
    "You can skip any question or type 'skip' to go straight to the main conversation.\n\n"
    "Could you share:\n"
    "- Your age (optional)\n"
    "- Any diagnosis you've received (e.g., PCOS, unexplained infertility) — optional\n"
    "- Any prior treatment history (e.g., previous IUI or IVF cycles) — optional\n"
    "- Any preferences or concerns you'd like me to keep in mind — optional\n\n"
    "Feel free to share as much or as little as you're comfortable with."
)

_ACKNOWLEDGEMENT_KEYWORDS = {"understand", "acknowledge", "agree", "yes", "ok", "okay", "accept"}


class ConversationOrchestrator:
    """Routes each patient turn through the correct conversation phase.

    State machine:
        DISCLAIMER_PENDING → PROFILE_COLLECTION → MAIN_LOOP
    """

    def __init__(
        self,
        agent: Agent,
        session_store: Optional[SessionStore] = None,
    ) -> None:
        self._agent = agent
        if session_store is not None:
            self._store = session_store
        elif os.getenv("ALLOYDB_SESSION_STORE", "").lower() == "true":
            self._store = AlloyDBSessionStore(connection_string=ALLOYDB_CONNECTION_STRING)
        elif os.getenv("FIRESTORE_SESSION_STORE", "").lower() == "true":
            self._store = FirestoreSessionStore(project=GOOGLE_CLOUD_PROJECT)
        else:
            self._store = InMemorySessionStore()
        # ADK session service and runner for MAIN_LOOP turns
        self._adk_sessions = InMemorySessionService()
        self._runner = Runner(
            agent=agent,
            app_name="ivf_advisor",
            session_service=self._adk_sessions,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_session(self) -> Session:
        """Create a new session and return it."""
        session = Session(session_id=str(uuid.uuid4()))
        self._store.create(session)
        return session

    def turn(self, session_id: str, user_message: str) -> str:
        """Process one patient turn and return the agent response string.

        Args:
            session_id: The active session ID.
            user_message: The raw text from the patient.

        Returns:
            The agent's response as a plain string.

        Raises:
            KeyError: If session_id does not exist.
        """
        session = self._store.get(session_id)
        if session is None:
            raise KeyError(f"Session '{session_id}' not found.")

        if session.state == ConversationState.ONBOARDING:
            response, session = self._handle_onboarding(session, user_message)
        elif session.state == ConversationState.PROFILE_COLLECTION:
            response, session = self._handle_profile_collection(session, user_message)
        else:  # MAIN_LOOP
            response, session = self._handle_main_loop(session, user_message)

        self._store.update(session)
        return response

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._store.get(session_id)

    def delete_session(self, session_id: str) -> None:
        self._store.delete(session_id)

    # ------------------------------------------------------------------
    # State handlers
    # ------------------------------------------------------------------

    def _handle_onboarding(
        self, session: Session, user_message: str
    ) -> tuple[str, Session]:
        """Mobile-first onboarding — lookup by mobile, register if new."""
        import re
        msg = user_message.strip()

        if session.onboarding_step == 0:
            # Step 0: received mobile number — look up patient
            mobile = re.sub(r'\D', '', msg)  # strip non-digits
            if len(mobile) < 10:
                return "Please enter a valid mobile number (10 digits).", session

            # Look up patient via task manager API
            patient = _lookup_patient_by_mobile(mobile)
            if patient:
                # Returning patient — load profile
                session.patient_id = patient.get("patient_id")
                session.patient_name = patient.get("name")
                session.patient_email = patient.get("email")
                session.cycle_id = patient.get("active_cycle_id")
                # Attempt to load persisted profile from Firestore
                loaded_profile = _load_patient_profile(session.patient_id)
                if loaded_profile:
                    session.profile = loaded_profile
                session.state = ConversationState.MAIN_LOOP
                return _ONBOARDING_RETURNING.format(
                    name=session.patient_name,
                    patient_id=session.patient_id,
                    cycle_id=session.cycle_id or "No active cycle",
                ), session
            else:
                # New patient — collect name
                session.patient_id = mobile  # temp store mobile
                session.onboarding_step = 1
                return _ONBOARDING_NEW_NAME, session

        elif session.onboarding_step == 1:
            # Step 1: received name
            session.patient_name = msg
            session.onboarding_step = 2
            return _ONBOARDING_NEW_EMAIL.format(name=msg), session

        elif session.onboarding_step == 2:
            # Step 2: received email — register patient
            mobile = session.patient_id  # we stored mobile here temporarily
            email = None if msg.lower() == "skip" else msg

            patient = _register_patient(
                name=session.patient_name,
                mobile_number=mobile,
                email=email,
            )
            if patient:
                session.patient_id = patient.get("patient_id")
                session.patient_email = email
                session.cycle_id = patient.get("active_cycle_id")
            else:
                # Fallback if API unavailable
                import uuid as _uuid
                session.patient_id = f"P-{_uuid.uuid4().hex[:8].upper()}"
                session.cycle_id = f"C-{_uuid.uuid4().hex[:8].upper()}"

            session.onboarding_step = 3
            return (
                "Would you like me to save your profile so I can personalise your experience "
                "on future visits? Your data is stored securely and only used to tailor guidance. "
                "(Reply **yes** to opt in, or **no** to continue without saving.)"
            ), session

        elif session.onboarding_step == 3:
            # Step 3: profile save opt-in
            if msg.lower() in {"yes", "y", "ok", "okay", "sure", "yep", "yeah"}:
                session.profile_opted_in = True
                if session.profile:
                    _persist_patient_profile(session.patient_id, session.profile)

            session.state = ConversationState.MAIN_LOOP
            return _ONBOARDING_COMPLETE.format(
                name=session.patient_name,
                patient_id=session.patient_id,
                cycle_id=session.cycle_id,
            ), session

        session.state = ConversationState.MAIN_LOOP
        return "Welcome! How can I help you today?", session

    def _handle_disclaimer(
        self, session: Session, user_message: str
    ) -> tuple[str, Session]:
        """Present disclaimer or advance state if patient acknowledges."""
        words = set(user_message.lower().split())
        if words & _ACKNOWLEDGEMENT_KEYWORDS:
            session.disclaimer_acknowledged = True
            session.state = ConversationState.PROFILE_COLLECTION
            return _PROFILE_PROMPT, session

        # Not acknowledged — repeat disclaimer
        return (
            _DISCLAIMER_TEXT + "\n\n(Please type 'I understand' to continue.)",
            session,
        )

    def _handle_profile_collection(
        self, session: Session, user_message: str
    ) -> tuple[str, Session]:
        """Collect profile data or skip, then transition to MAIN_LOOP."""
        msg_lower = user_message.lower().strip()

        if msg_lower in {"skip", "no", "no thanks", "none", "n/a"}:
            session.state = ConversationState.MAIN_LOOP
            return (
                "No problem — I'll provide general IVF guidance. "
                "What would you like to know?",
                session,
            )

        # Parse whatever the patient provided into a PatientProfile
        profile = _parse_profile_from_text(user_message)
        session.profile = profile
        session.state = ConversationState.MAIN_LOOP

        # Reflect details back to confirm (sets confirmed=False until this turn completes)
        confirmation = _build_profile_confirmation(profile)
        profile.confirmed = True
        session.profile = profile

        # Persist if patient has opted in
        if session.profile_opted_in and session.patient_id:
            _persist_patient_profile(session.patient_id, session.profile)

        return confirmation, session

    def _handle_main_loop(
        self, session: Session, user_message: str
    ) -> tuple[str, Session]:
        """Pass the turn to the ADK agent and update session metadata."""
        session.turn_count += 1

        # Use a fixed ADK session ID per conversation session.
        # create_session is async — run it synchronously via asyncio.run()
        adk_session_id = session.session_id

        async def _ensure_adk_session():
            try:
                await self._adk_sessions.create_session(
                    app_name="ivf_advisor",
                    user_id=adk_session_id,
                    session_id=adk_session_id,
                )
            except Exception:
                pass  # Already exists

        asyncio.run(_ensure_adk_session())

        # Inject patient context so agent uses correct IDs automatically
        context_prefix = ""
        if session.patient_id:
            context_prefix = (
                f"[Patient context — always use these IDs for all tool calls: "
                f"patient_id='{session.patient_id}', "
                f"cycle_id='{session.cycle_id or 'C-DEFAULT'}', "
                f"patient_name='{session.patient_name or 'Patient'}', "
                f"patient_email='{session.patient_email or ''}']\n\n"
            )

        content = types.Content(
            role="user",
            parts=[types.Part(text=context_prefix + user_message)],
        )

        response_text = ""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                for event in self._runner.run(
                    user_id=adk_session_id,
                    session_id=adk_session_id,
                    new_message=content,
                ):
                    if event.is_final_response() and event.content and event.content.parts:
                        # Collect all text parts — skip function_call parts
                        text_parts = [
                            p.text for p in event.content.parts
                            if hasattr(p, "text") and p.text
                        ]
                        if text_parts:
                            response_text = " ".join(text_parts)
                            break
                        # If only function_call parts, keep waiting for next event
                break  # success
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < max_retries - 1:
                        import time
                        wait = 10 * (attempt + 1)
                        logger.warning("Rate limited, retrying in %ds", wait)
                        time.sleep(wait)
                        continue
                    return "I'm sorry, I wasn't able to generate a response. Please try again.", session
                logger.exception("ADK runner error: %s", e)
                return "I'm sorry, I wasn't able to generate a response. Please try again.", session

        # Track topics discussed (simple keyword extraction)
        _update_topics(session, user_message)

        return response_text or "I'm sorry, I wasn't able to generate a response. Please try again.", session


# ------------------------------------------------------------------
# Patient profile persistence helpers
# ------------------------------------------------------------------


def _persist_patient_profile(patient_id: str, profile: PatientProfile) -> None:
    """Write PatientProfile to Firestore at patient_profiles/{patient_id}.

    Only runs when FIRESTORE_SESSION_STORE=true. Logs warning on failure, never raises.
    """
    if os.getenv("FIRESTORE_SESSION_STORE", "").lower() != "true":
        return
    try:
        from datetime import datetime as _dt
        import google.cloud.firestore as _firestore  # type: ignore

        client = _firestore.Client(project=GOOGLE_CLOUD_PROJECT)
        data = profile.model_dump(mode="json")
        data["last_updated"] = _dt.utcnow().isoformat()
        client.collection("patient_profiles").document(patient_id).set(data)
    except Exception as exc:
        logger.warning("Failed to persist patient profile for %s: %s", patient_id, exc)


def _load_patient_profile(patient_id: str) -> Optional[PatientProfile]:
    """Load PatientProfile from Firestore. Returns None on miss or error."""
    if os.getenv("FIRESTORE_SESSION_STORE", "").lower() != "true":
        return None
    try:
        import google.cloud.firestore as _firestore  # type: ignore

        client = _firestore.Client(project=GOOGLE_CLOUD_PROJECT)
        doc = client.collection("patient_profiles").document(patient_id).get()
        if not doc.exists:
            return None
        return PatientProfile.model_validate(doc.to_dict())
    except Exception as exc:
        logger.warning("Failed to load patient profile for %s: %s", patient_id, exc)
        return None


# ------------------------------------------------------------------
# Patient API helpers
# ------------------------------------------------------------------

import os as _os
import httpx as _httpx

_TM_URL = _os.getenv("TASK_MANAGER_URL", "https://task-manager-api-100876575377.us-central1.run.app")
_TM_KEY = _os.getenv("TASK_MANAGER_SECRET_KEY", "")


def _tm_headers() -> dict:
    return {"Authorization": f"Bearer {_TM_KEY}"}


def _lookup_patient_by_mobile(mobile: str) -> dict | None:
    """Look up a patient by mobile number via Task Manager API."""
    try:
        resp = _httpx.get(
            f"{_TM_URL}/patients",
            headers=_tm_headers(),
            params={"mobile": mobile},
            timeout=10.0,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def _register_patient(name: str, mobile_number: str, email: str | None) -> dict | None:
    """Register a new patient via Task Manager API."""
    try:
        resp = _httpx.post(
            f"{_TM_URL}/patients",
            headers={**_tm_headers(), "Content-Type": "application/json"},
            json={"name": name, "mobile_number": mobile_number, "email": email},
            timeout=10.0,
        )
        if resp.status_code == 201:
            return resp.json()
        return None
    except Exception:
        return None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_profile_from_text(text: str) -> PatientProfile:
    """Best-effort extraction of profile fields from free-form patient text."""
    profile = PatientProfile()

    lower = text.lower()

    # Age — look for patterns like "I'm 34", "age 34", "34 years"
    import re
    age_match = re.search(r"\b(?:i(?:'m| am)|age[d]?|aged)\s+(\d{2})\b|\b(\d{2})\s+years?\b", lower)
    if age_match:
        age_str = age_match.group(1) or age_match.group(2)
        try:
            profile.age = int(age_str)
        except ValueError:
            pass

    # Diagnosis keywords
    diagnoses = [
        "pcos", "polycystic", "endometriosis", "unexplained infertility",
        "diminished ovarian reserve", "low amh", "male factor", "azoospermia",
        "poor responder", "recurrent miscarriage", "premature ovarian insufficiency",
    ]
    for d in diagnoses:
        if d in lower:
            profile.diagnosis = d
            break

    # Prior history
    if any(w in lower for w in ["previous ivf", "prior ivf", "failed cycle", "iui", "prior treatment"]):
        profile.prior_treatment_history = text[:200]  # store raw snippet

    # Preferences
    if any(w in lower for w in ["prefer", "minimal", "natural", "concerned about", "worried about"]):
        profile.preferences = text[:200]

    return profile


def _build_profile_confirmation(profile: PatientProfile) -> str:
    """Build a human-readable confirmation of the collected profile."""
    lines = ["Here's what I've noted about your situation:"]
    if profile.age:
        lines.append(f"- Age: {profile.age}")
    if profile.diagnosis:
        lines.append(f"- Diagnosis: {profile.diagnosis}")
    if profile.prior_treatment_history:
        lines.append(f"- Prior treatment: noted")
    if profile.preferences:
        lines.append(f"- Preferences/concerns: noted")
    if len(lines) == 1:
        lines.append("- No specific details captured — I'll provide general guidance.")
    lines.append(
        "\nI'll use this to tailor my guidance where relevant. "
        "You can update any details at any time. What would you like to know?"
    )
    return "\n".join(lines)


logger = logging.getLogger(__name__)

_TOPIC_KEYWORDS: dict[str, list[str]] = {
    "costs": ["cost", "price", "fee", "expensive", "afford", "budget", "pay", "fund"],
    "journey": ["stage", "process", "step", "what happens", "timeline", "how long"],
    "stimulation": ["stimulation", "injection", "medication", "drug", "protocol"],
    "egg_retrieval": ["egg retrieval", "collection", "retrieve"],
    "embryo": ["embryo", "blastocyst", "fertilisation", "fertilization", "icsi"],
    "transfer": ["transfer", "implantation", "two week wait", "tww"],
    "evidence": ["evidence", "study", "research", "success rate", "statistics"],
    "emotional": ["anxious", "scared", "worried", "stressed", "emotional", "support"],
    "comparison": ["compare", "difference", "versus", "vs", "better", "which"],
}


def _update_topics(session: Session, message: str) -> None:
    """Append newly detected topics to session.topics_discussed."""
    lower = message.lower()
    for topic, keywords in _TOPIC_KEYWORDS.items():
        if topic not in session.topics_discussed:
            if any(kw in lower for kw in keywords):
                session.topics_discussed.append(topic)
