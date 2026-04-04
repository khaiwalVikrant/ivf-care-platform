"""Conversation orchestrator — manages session state and routes turns to the ADK agent."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Optional

from google.adk.agents import Agent  # type: ignore
from google.adk.runners import Runner  # type: ignore
from google.adk.sessions import InMemorySessionService  # type: ignore
from google.genai import types  # type: ignore

from ivf_advisor.models import ConversationState, PatientProfile, Session
from ivf_advisor.session import InMemorySessionStore, SessionStore

_DISCLAIMER_TEXT = (
    "🌸 Welcome to IVF Care Platform!\n\n"
    "I'm your AI companion for the IVF journey. I can help you book appointments, "
    "set medication reminders, arrange nurse home visits, track costs, and answer "
    "clinical questions.\n\n"
    "Use the quick action buttons on the left to get started, or just tell me what you need.\n\n"
    "_(Note: I provide educational information only — always consult your fertility specialist.)_"
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
        self._store = session_store or InMemorySessionStore()
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

        if session.state == ConversationState.PROFILE_COLLECTION:
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

        content = types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
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
