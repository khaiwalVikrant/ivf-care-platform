"""IVF emotional support tool — provides empathetic, distress-aware responses."""

from __future__ import annotations

import re

from ivf_advisor.models import EmotionalSupportOutput

# ---------------------------------------------------------------------------
# Distress keyword sets
# ---------------------------------------------------------------------------

_SEVERE_KEYWORDS = [
    "giving up",
    "can't cope",
    "cannot cope",
    "hopeless",
    "end it",
    "self-harm",
    "self harm",
    "suicidal",
    "don't want to live",
    "do not want to live",
    "no point",
]

_MODERATE_KEYWORDS = [
    "devastated",
    "heartbroken",
    "failed again",
    "another failure",
    "never going to work",
    "lost hope",
    "depressed",
    "can't do this anymore",
    "cannot do this anymore",
]

_MILD_KEYWORDS = [
    "anxious",
    "scared",
    "worried",
    "stressed",
    "nervous",
    "frustrated",
    "overwhelmed",
]

# ---------------------------------------------------------------------------
# Support resources
# ---------------------------------------------------------------------------

_SUPPORT_RESOURCES: dict[str, list[str]] = {
    "india": [
        "iCall: 9152987821",
        "NIMHANS Helpline: 080-46110007",
        "Vandrevala Foundation: 1860-2662-345",
    ],
    "uk": [
        "Samaritans: 116 123 (free, 24/7)",
        "Fertility Network UK: fertilitynetworkuk.org",
        "Mind: 0300 123 3393",
    ],
    "global": [
        "IFMH: ifmh.org",
        "Crisis Text Line: text HOME to 741741",
    ],
}

# ---------------------------------------------------------------------------
# Coping strategies (mild / moderate)
# ---------------------------------------------------------------------------

_COPING_STRATEGIES_MILD = [
    "Try a short grounding exercise: name 5 things you can see, 4 you can touch, 3 you can hear.",
    "Gentle movement — even a 10-minute walk — can help shift anxious energy.",
    "Write down one specific worry and one small action you could take about it.",
]

_COPING_STRATEGIES_MODERATE = [
    "Allow yourself to grieve — your feelings are valid and do not need to be fixed immediately.",
    "Reach out to one trusted person today, even just to say how you are feeling.",
    "Consider speaking with a fertility counsellor who understands the specific grief of IVF.",
]

# ---------------------------------------------------------------------------
# Forbidden phrases (never use these)
# ---------------------------------------------------------------------------

_FORBIDDEN_PHRASES = [
    "stay positive",
    "it will work out",
    "think positive",
    "everything happens for a reason",
    "just relax",
]

# ---------------------------------------------------------------------------
# Distress classification
# ---------------------------------------------------------------------------


def _classify_distress(message: str) -> str:
    """Return 'severe', 'moderate', or 'mild' based on keyword matching."""
    text = message.lower()
    for kw in _SEVERE_KEYWORDS:
        if kw in text:
            return "severe"
    for kw in _MODERATE_KEYWORDS:
        if kw in text:
            return "moderate"
    for kw in _MILD_KEYWORDS:
        if kw in text:
            return "mild"
    return "mild"


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------


def _build_severe_response(context: str | None) -> str:
    lines = [
        "What you're going through sounds incredibly painful, and I'm glad you reached out.",
        "Right now, the most important thing is that you speak with someone who can truly support you.",
        "",
        "Please contact one of these crisis support lines:",
        "• Samaritans (UK): 116 123 — free, available 24/7",
        "• iCall (India): 9152987821",
        "• Crisis Text Line: text HOME to 741741",
        "",
        "You do not have to face this alone.",
    ]
    return "\n".join(lines)


def _build_moderate_response(context: str | None) -> str:
    ctx_note = ""
    if context:
        ctx_note = f" I can hear how much this journey has taken from you — {context.strip().rstrip('.')}."
    lines = [
        f"I'm so sorry you're feeling this way.{ctx_note}",
        "The grief and exhaustion that come with IVF are real, and it makes complete sense "
        "that you're struggling right now.",
        "Your feelings deserve to be acknowledged, not minimised.",
    ]
    return " ".join(lines)


def _build_mild_response(context: str | None) -> str:
    ctx_note = ""
    if context:
        ctx_note = f" It sounds like {context.strip().rstrip('.')} is adding to the weight you're carrying."
    lines = [
        f"It's completely understandable to feel this way during IVF.{ctx_note}",
        "This process asks a lot of you — physically, emotionally, and practically.",
        "You're not alone in finding it hard.",
    ]
    return " ".join(lines)


# ---------------------------------------------------------------------------
# Public tool function
# ---------------------------------------------------------------------------


def emotional_support_tool(
    message: str,
    context: str | None = None,
) -> EmotionalSupportOutput:
    """Provide empathetic, distress-aware emotional support for IVF patients.

    Args:
        message: The patient's message expressing their emotional state.
        context: Optional additional context (e.g. recent cycle outcome).

    Returns:
        EmotionalSupportOutput with distress level, empathy response, coping
        strategies, support resources, and a crisis_mode flag.
    """
    distress_level = _classify_distress(message)

    if distress_level == "severe":
        return EmotionalSupportOutput(
            distress_level="severe",
            empathy_response=_build_severe_response(context),
            coping_strategies=[],
            support_resources=_SUPPORT_RESOURCES,
            crisis_mode=True,
        )

    if distress_level == "moderate":
        return EmotionalSupportOutput(
            distress_level="moderate",
            empathy_response=_build_moderate_response(context),
            coping_strategies=_COPING_STRATEGIES_MODERATE[:3],
            support_resources=_SUPPORT_RESOURCES,
            crisis_mode=False,
        )

    # mild (default)
    return EmotionalSupportOutput(
        distress_level="mild",
        empathy_response=_build_mild_response(context),
        coping_strategies=_COPING_STRATEGIES_MILD[:3],
        support_resources=_SUPPORT_RESOURCES,
        crisis_mode=False,
    )
