"""IVF wellness guide tool — stage-specific lifestyle and diet guidance."""

from __future__ import annotations

from typing import Optional

_DISCLAIMER = (
    "This guidance is general and educational. Always follow your clinic's specific "
    "instructions, which take priority over general advice."
)

_STAGE_GUIDANCE: dict[str, dict] = {
    "stimulation": {
        "diet": (
            "High-protein foods (eggs, chicken, legumes, dairy) — aim for 80–100g protein/day. "
            "Leafy greens, colourful vegetables, whole grains. Stay well hydrated (2–3L water/day) "
            "to reduce OHSS risk."
        ),
        "avoid": (
            "Alcohol, smoking, excessive caffeine (max 200mg/day), raw/undercooked foods, "
            "high-mercury fish (swordfish, shark, tilefish), strenuous exercise, hot tubs/saunas."
        ),
        "sleep": "Aim for 7–9 hours. Sleep disruption can affect hormone levels.",
        "exercise": (
            "Light walking (20–30 min/day) is fine. Avoid high-impact exercise, heavy lifting, "
            "or anything that causes abdominal discomfort. Stop if you feel bloated or uncomfortable."
        ),
        "stress_management": (
            "Gentle yoga, meditation, acupuncture (evidence-based for stress reduction). "
            "Avoid anything that raises core body temperature."
        ),
        "supplements": (
            "Folic acid 400mcg (evidence-based, essential). Vitamin D if deficient. "
            "CoQ10 200–600mg (some evidence for egg quality). Always check with your doctor "
            "before starting supplements."
        ),
    },
    "egg_retrieval": {
        "diet": (
            "Light meal the evening before. Fast from midnight before the procedure. "
            "After retrieval, eat easily digestible foods. High-protein diet to support recovery."
        ),
        "avoid": (
            "Alcohol, NSAIDs (ibuprofen) unless prescribed, strenuous activity for 24–48 hours, "
            "driving on the day of procedure (sedation)."
        ),
        "sleep": (
            "Rest for the remainder of the day after retrieval. "
            "Most patients return to normal activities the next day."
        ),
        "exercise": (
            "Rest on the day of retrieval. Light walking from day 2. "
            "Avoid strenuous exercise until after embryo transfer."
        ),
        "stress_management": (
            "Rest and be gentle with yourself. Mild cramping and bloating are normal. "
            "Contact your clinic if pain is severe."
        ),
        "supplements": "Continue folic acid. Progesterone support as prescribed by your clinic.",
    },
    "two_week_wait": {
        "diet": (
            "Mediterranean-style diet — fruits, vegetables, whole grains, lean protein, healthy fats. "
            "Pineapple core (contains bromelain) is a popular folk remedy but evidence is limited."
        ),
        "avoid": (
            "Alcohol, smoking, excessive caffeine (max 200mg/day), hot baths/saunas/jacuzzis, "
            "raw/undercooked foods, high-mercury fish, NSAIDs."
        ),
        "sleep": (
            "Aim for 7–9 hours. Avoid sleep deprivation which can increase stress hormones."
        ),
        "exercise": (
            "Light walking is safe and beneficial. Avoid high-impact exercise, heavy lifting, "
            "or anything that causes abdominal discomfort."
        ),
        "stress_management": (
            "The two-week wait is emotionally challenging. Distraction activities, gentle yoga, "
            "and talking to a trusted person can help. Avoid obsessive symptom-checking."
        ),
        "supplements": (
            "Continue folic acid and any supplements prescribed by your clinic. "
            "Do not start new supplements without medical advice."
        ),
    },
    "embryo_transfer": {
        "diet": (
            "Light, easily digestible meal before transfer. Stay hydrated. "
            "No special dietary restrictions after transfer."
        ),
        "avoid": (
            "Strenuous exercise for 24–48 hours, heavy lifting, sexual intercourse for 48 hours "
            "(unless advised otherwise), hot baths/saunas."
        ),
        "sleep": (
            "Short rest (30–60 min) after transfer is common practice, though evidence for "
            "extended bed rest is not strong. Return to normal gentle activities the same day."
        ),
        "exercise": (
            "Light walking is fine from the next day. "
            "Avoid high-impact exercise until pregnancy test."
        ),
        "stress_management": (
            "Gentle activities, reading, light walking. "
            "Avoid anything that causes anxiety or physical strain."
        ),
        "supplements": (
            "Continue all prescribed medications (progesterone, oestrogen). "
            "Do not stop any medication without consulting your clinic."
        ),
    },
    "general": {
        "diet": (
            "Balanced Mediterranean-style diet rich in antioxidants, healthy fats, and lean protein. "
            "Maintain a healthy weight — both underweight and overweight can affect IVF outcomes."
        ),
        "avoid": (
            "Alcohol, smoking, recreational drugs, excessive caffeine, "
            "environmental toxins (pesticides, BPA)."
        ),
        "sleep": "7–9 hours per night. Good sleep hygiene supports hormonal balance.",
        "exercise": (
            "Regular moderate exercise (150 min/week) is beneficial. "
            "Avoid extreme endurance sports or very high-intensity training during treatment."
        ),
        "stress_management": (
            "Mindfulness, yoga, acupuncture, counselling. "
            "Chronic stress can affect reproductive hormones."
        ),
        "supplements": (
            "Folic acid 400mcg (essential). Vitamin D if deficient. "
            "Discuss CoQ10, omega-3, and other supplements with your doctor."
        ),
    },
}

_CONCERN_ADVICE: dict[str, str] = {
    "bloating": (
        "Bloating during stimulation is common and usually normal. Stay hydrated, eat small "
        "frequent meals, avoid gas-producing foods (beans, carbonated drinks). Contact your "
        "clinic if you experience severe pain, rapid weight gain (>1kg/day), or difficulty breathing."
    ),
    "headache": (
        "Headaches can be a side effect of hormonal medications. Stay hydrated, rest, and use "
        "paracetamol if needed (avoid ibuprofen). Contact your clinic if headaches are severe or persistent."
    ),
    "mood swings": (
        "Hormonal fluctuations during IVF commonly cause mood changes. This is normal and temporary. "
        "Talk to someone you trust and practice self-compassion."
    ),
    "nausea": (
        "Nausea is common with progesterone support. Take medications with food, stay hydrated, "
        "and eat small frequent meals."
    ),
    "fatigue": (
        "Fatigue is very common during IVF. Prioritise rest, gentle movement, and good nutrition. "
        "Iron-rich foods (spinach, lentils, red meat) can help if you are anaemic."
    ),
}


def wellness_guide_tool(
    stage: str,
    concern: Optional[str] = None,
) -> dict:
    """Returns stage-specific IVF lifestyle and wellness guidance.

    Args:
        stage: IVF treatment stage. One of: "stimulation", "egg_retrieval",
               "two_week_wait", "embryo_transfer", "general".
        concern: Optional specific concern (e.g. "bloating", "headache",
                 "mood swings", "nausea", "fatigue").

    Returns:
        Dict with diet, avoid, sleep, exercise, stress_management, supplements,
        optional concern_advice, and disclaimer.
    """
    stage_key = stage.lower().strip().replace(" ", "_").replace("-", "_")
    guidance = _STAGE_GUIDANCE.get(stage_key, _STAGE_GUIDANCE["general"])

    result = {
        "stage": stage,
        **guidance,
        "disclaimer": _DISCLAIMER,
    }

    if concern:
        concern_key = concern.lower().strip()
        # Try exact match first, then partial match
        advice = _CONCERN_ADVICE.get(concern_key)
        if not advice:
            for key, val in _CONCERN_ADVICE.items():
                if key in concern_key or concern_key in key:
                    advice = val
                    break
        if advice:
            result["concern_advice"] = advice

    return result
