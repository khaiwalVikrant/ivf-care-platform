"""Scope guard tool — classifies patient queries as in/out of IVF domain."""

from __future__ import annotations

import re

from ivf_advisor.models import ScopeGuardOutput

# ---------------------------------------------------------------------------
# Keyword sets
# ---------------------------------------------------------------------------

_IVF_KEYWORDS = re.compile(
    r"\b("
    r"ivf|iui|icsi|fertility|infertility|embryo|egg retrieval|egg donation|"
    r"sperm|ovulation|ovarian|stimulation|follicle|blastocyst|implantation|"
    r"endometrium|uterus|uterine|fallopian|amh|fsh|lh|oestradiol|estradiol|"
    r"progesterone|gonadotrophin|gonadotropin|gnrh|antagonist|agonist|"
    r"trigger injection|egg freezing|embryo transfer|frozen embryo|fet|"
    r"two.week wait|tww|pregnancy test|beta hcg|hcg|pgt|pgt-a|pgt-m|"
    r"preimplantation|genetic testing|surrogacy|donor egg|donor sperm|"
    r"reproductive|assisted reproduction|art|clinic|protocol|cycle|"
    r"miscarriage|recurrent|implantation failure|ohss|hyperstimulation|"
    r"polycystic|pcos|endometriosis|diminished ovarian reserve|low amh|"
    r"male factor|azoospermia|oligospermia|unexplained infertility|"
    r"natural killer|nk cells|era|endometrial receptivity|scratch|"
    r"intralipid|prednisone|steroids fertility|acupuncture fertility|"
    r"sperm dna|fragmentation|morphology|motility|count|semen analysis"
    r")\b",
    re.IGNORECASE,
)

_EMERGENCY_KEYWORDS = re.compile(
    r"\b("
    r"severe pain|unbearable pain|chest pain|difficulty breathing|"
    r"can't breathe|cannot breathe|shortness of breath|"
    r"heavy bleeding|bleeding heavily|soaking|blood clot|"
    r"faint|fainting|passed out|unconscious|"
    r"rapid weight gain|sudden swelling|abdomen swollen|"
    r"high fever|fever over|temperature over|"
    r"ectopic|rupture|ruptured|"
    r"emergency|call 999|call 911|call 112|ambulance"
    r")\b",
    re.IGNORECASE,
)

_OUT_OF_SCOPE_KEYWORDS = re.compile(
    r"\b("
    r"legal advice|lawsuit|sue|solicitor|lawyer|attorney|court|"
    r"tax|financial advice|investment|stock|crypto|"
    r"immigration|visa|passport|"
    r"car insurance|home insurance|mortgage|"
    r"recipe|cooking|food|restaurant|"
    r"weather|sport|football|cricket|tennis|"
    r"politics|election|government policy|"
    r"general gp|unrelated diagnosis|cancer treatment|chemotherapy|"
    r"diabetes management|blood pressure medication|"
    r"mental health therapy|psychotherapy|cbt|counselling(?! fertility)"
    r")\b",
    re.IGNORECASE,
)

_REFERRAL_MAP: dict[str, str] = {
    "legal": "Please consult a qualified solicitor or legal professional for legal advice.",
    "financial": "Please consult a qualified financial adviser for financial or investment advice.",
    "emergency": "Please call emergency services (999 / 911 / 112) or go to your nearest A&E immediately.",
    "general_medical": (
        "This appears to be outside the scope of IVF and fertility guidance. "
        "Please consult your GP or a relevant medical specialist."
    ),
    "other": (
        "This topic is outside my area of expertise (IVF and fertility treatment). "
        "Please consult an appropriate professional."
    ),
}


def scope_guard_tool(query: str) -> ScopeGuardOutput:
    """Checks whether a patient query is within the IVF/fertility domain.

    Args:
        query: The patient's raw query text.

    Returns:
        ScopeGuardOutput with in_scope boolean, is_emergency flag, reason,
        and referral_suggestion when out of scope or an emergency.
    """
    # Emergency check takes priority — always flag regardless of scope
    if _EMERGENCY_KEYWORDS.search(query):
        return ScopeGuardOutput(
            in_scope=False,
            is_emergency=True,
            reason="The query describes symptoms that may indicate a medical emergency.",
            referral_suggestion=_REFERRAL_MAP["emergency"],
        )

    # Check for clearly out-of-scope topics
    if _OUT_OF_SCOPE_KEYWORDS.search(query):
        referral = _classify_referral(query)
        return ScopeGuardOutput(
            in_scope=False,
            is_emergency=False,
            reason="The query is outside the IVF and fertility domain.",
            referral_suggestion=referral,
        )

    # Check for IVF/fertility relevance
    if _IVF_KEYWORDS.search(query):
        return ScopeGuardOutput(
            in_scope=True,
            is_emergency=False,
            reason="The query is within the IVF and fertility domain.",
            referral_suggestion=None,
        )

    # Ambiguous — treat as in-scope with a note (agent can handle nuance)
    return ScopeGuardOutput(
        in_scope=True,
        is_emergency=False,
        reason=(
            "The query does not clearly match known out-of-scope topics and may relate "
            "to IVF or fertility. Treating as in-scope; the agent will clarify if needed."
        ),
        referral_suggestion=None,
    )


def _classify_referral(query: str) -> str:
    """Return the most appropriate referral suggestion for an out-of-scope query."""
    q = query.lower()
    if any(w in q for w in ("legal", "lawyer", "solicitor", "sue", "court", "lawsuit")):
        return _REFERRAL_MAP["legal"]
    if any(w in q for w in ("tax", "investment", "financial", "stock", "crypto", "mortgage")):
        return _REFERRAL_MAP["financial"]
    return _REFERRAL_MAP["other"]
