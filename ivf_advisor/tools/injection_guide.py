"""IVF injection training guide tool — step-by-step self-injection guidance."""

from __future__ import annotations

from typing import Optional

_DISCLAIMER = (
    "Always follow your clinic's specific medication instructions. Never adjust your dose "
    "without medical guidance. If you are unsure about any aspect of your injection technique, "
    "ask your clinic nurse to demonstrate."
)

_SC_STEPS = [
    "Wash hands thoroughly with soap and water for at least 20 seconds.",
    "Gather supplies: medication pen/syringe, alcohol swab, sharps bin.",
    "Check medication: correct drug, correct dose, expiry date, no particles or discolouration.",
    "Choose injection site: lower abdomen (5cm from navel) or outer thigh. Rotate sites each day.",
    "Clean the site with an alcohol swab and allow to dry for 10 seconds.",
    "Pinch a fold of skin between thumb and forefinger (about 2–3cm).",
    "Insert needle at 45–90 degrees. For most patients, 45 degrees is recommended.",
    "Inject slowly and steadily. Do not aspirate (pull back plunger) for SC injections.",
    "Withdraw needle at the same angle. Release skin fold.",
    "Apply gentle pressure with a clean swab. Do not rub.",
    "Dispose of needle immediately in a sharps bin.",
]

_IM_STEPS = [
    "Wash hands thoroughly with soap and water.",
    "Identify the injection site: upper outer quadrant of the buttock.",
    "Clean the site with an alcohol swab and allow to dry.",
    "Stretch the skin taut (do not pinch for IM injections).",
    "Insert needle at 90 degrees with a quick, confident motion.",
    "Aspirate (pull back plunger slightly) — if blood appears, withdraw and choose a new site.",
    "If no blood, inject slowly and steadily over 10 seconds.",
    "Withdraw needle at 90 degrees. Apply gentle pressure and massage the site.",
    "Dispose of needle immediately in a sharps bin.",
]

_SITE_ROTATION = (
    "Rotate injection sites systematically to prevent bruising and lipodystrophy (hardening of tissue). "
    "Keep a simple log or use a body diagram to track sites. "
    "Allow at least 2cm between injection sites."
)

_MEDICATION_PREPARATION = (
    "Pre-filled pens: Remove cap, attach needle if required, dial correct dose, prime pen "
    "(small test dose to remove air).\n\n"
    "Powder vials: Inject diluent into powder vial, swirl gently (do not shake), draw up "
    "reconstituted solution, remove air bubbles by tapping syringe and pushing plunger until "
    "a small drop appears.\n\n"
    "Air bubbles: Tap syringe gently with finger, then push plunger slowly until bubbles are "
    "expelled. A tiny air bubble (<0.2ml) is not dangerous for SC injections."
)

_MISSED_DOSE = (
    "Missed by <4 hours: Administer as soon as you remember.\n\n"
    "Missed by >4 hours: Contact your clinic immediately for guidance. Do not double dose "
    "without medical advice.\n\n"
    "Trigger injection: This is time-critical. If you miss the trigger injection time, "
    "contact your clinic immediately — egg retrieval timing depends on it."
)

_INJECTION_SITE_REACTIONS = (
    "Normal: Mild redness, bruising, or a small lump at the injection site. "
    "These resolve within a few days.\n\n"
    "Monitor: Increasing redness, warmth, or swelling over 24–48 hours — contact your clinic.\n\n"
    "Seek immediate care: Signs of allergic reaction (hives, difficulty breathing, "
    "swelling of face/throat)."
)

_INDIA_NOTE = (
    "Pre-filled injection pens (e.g. Gonal-F pen, Puregon pen) are available in India and "
    "significantly reduce technique errors compared to vial-and-syringe. Ask your clinic if "
    "pen devices are available for your medication. If a nurse is administering your injections, "
    "ask them to demonstrate the technique and confirm the injection site before each administration."
)

_CONCERN_ADVICE: dict[str, str] = {
    "bruising": (
        "Bruising is common and usually harmless. Rotate sites, apply ice before injection, "
        "inject slowly. Avoid rubbing after injection."
    ),
    "missed dose": (
        "Contact your clinic immediately. Do not double dose without advice. "
        "For trigger injections, this is urgent — call your clinic right away."
    ),
    "air bubble": (
        "Small air bubbles in SC injections are not dangerous. Tap the syringe gently and "
        "push the plunger slowly until the bubble is expelled before injecting."
    ),
    "pain": (
        "Some discomfort is normal. Allow alcohol to dry fully before injecting, inject slowly, "
        "and use room-temperature medication (cold medication stings more)."
    ),
    "lump": (
        "A small lump (lipodystrophy) can form if you inject the same site repeatedly. "
        "Rotate sites systematically to prevent this. Existing lumps usually resolve over weeks."
    ),
}


def injection_guide_tool(
    injection_type: str,
    medication: Optional[str] = None,
    concern: Optional[str] = None,
) -> dict:
    """Returns step-by-step IVF injection guidance for patients.

    Args:
        injection_type: "subcutaneous" or "intramuscular".
        medication: Optional medication name (e.g. "Gonal-F", "Menopur", "Progesterone").
        concern: Optional specific concern (e.g. "bruising", "missed dose", "air bubble",
                 "pain", "lump").

    Returns:
        Dict with step-by-step instructions, site rotation, medication preparation,
        missed dose protocol, injection site reactions, India-specific note,
        optional concern advice, and disclaimer.
    """
    inj_lower = injection_type.lower().strip()

    if inj_lower == "intramuscular":
        steps = _IM_STEPS
        inj_label = "Intramuscular (IM)"
    else:
        steps = _SC_STEPS
        inj_label = "Subcutaneous (SC)"

    result: dict = {
        "injection_type": inj_label,
        "step_by_step": steps,
        "site_rotation": _SITE_ROTATION,
        "medication_preparation": _MEDICATION_PREPARATION,
        "missed_dose_protocol": _MISSED_DOSE,
        "injection_site_reactions": _INJECTION_SITE_REACTIONS,
        "india_note": _INDIA_NOTE,
        "disclaimer": _DISCLAIMER,
    }

    if medication:
        result["medication"] = medication

    if concern:
        concern_key = concern.lower().strip()
        advice = _CONCERN_ADVICE.get(concern_key)
        if not advice:
            for key, val in _CONCERN_ADVICE.items():
                if key in concern_key or concern_key in key:
                    advice = val
                    break
        if advice:
            result["concern_advice"] = advice

    return result
