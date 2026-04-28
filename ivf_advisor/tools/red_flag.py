"""IVF clinic red flag detection tool — identifies potentially misleading claims."""

from __future__ import annotations

import re

from ivf_advisor.models import RedFlagOutput

_LEGITIMATE_CLINIC_NOTE = (
    "Reputable fertility clinics are transparent about success rates, publish data with "
    "national registries (e.g. HFEA in the UK, ICMR in India, SART in the US), provide "
    "clear itemised cost breakdowns, and never pressure patients into specific treatments. "
    "If you are unsure about a clinic's claims, ask for their published registry data and "
    "seek a second opinion from an independent specialist."
)

# ---------------------------------------------------------------------------
# Red flag pattern definitions
# Each entry: (flag_label, check_function)
# ---------------------------------------------------------------------------


def _flag_unrealistic_success_rate(text: str) -> bool:
    """Detect claims of >60% success rate for patients over 40."""
    high_rate = re.search(r"\b(6[0-9]|[7-9]\d|100)\s*%", text)
    over_40 = re.search(r"\b(over\s*40|above\s*40|aged?\s*40\+|\b4[0-9]\s*year)", text)
    return bool(high_rate and over_40)


def _flag_guaranteed_pregnancy(text: str) -> bool:
    """Detect guaranteed pregnancy claims."""
    patterns = [
        r"\bguarantee[ds]?\b",
        r"\b100\s*%\s*(success|pregnancy|guarantee)",
        r"\bcertain(ly)?\s+(pregnant|pregnancy|conceive)",
        r"\bdefinitely\s+(pregnant|pregnancy|conceive|get\s+pregnant)",
    ]
    return any(re.search(p, text) for p in patterns)


def _flag_donor_egg_pressure(text: str) -> bool:
    """Detect pressure to use donor eggs without justification."""
    patterns = [
        r"\bmust\s+use\s+donor",
        r"\bonly\s+option\s+is\s+donor",
        r"\bhave\s+to\s+use\s+donor\s+eggs?",
        r"\bno\s+choice\s+but\s+donor",
        r"\bonly\s+way\s+is\s+donor",
    ]
    return any(re.search(p, text) for p in patterns)


def _flag_unusually_low_price(text: str) -> bool:
    """Detect suspiciously low all-inclusive prices that likely exclude medications."""
    # Look for "all inclusive" or "all-inclusive" combined with a low price
    all_inclusive = re.search(r"\ball[\s-]inclusive\b", text)
    # Extract numeric prices (handles commas in numbers like 40,000)
    prices = re.findall(r"[\$£₹]?\s*([\d,]+)\s*(?:inr|gbp|usd|\$|£|₹)?", text)

    def _parse_price(p: str) -> int:
        return int(p.replace(",", ""))

    if all_inclusive and prices:
        for raw in prices:
            try:
                amount = _parse_price(raw)
                # Flag if price < 50,000 INR or < 2,000 GBP/USD
                if amount < 50_000 or amount < 2_000:
                    return True
            except ValueError:
                continue

    # Also flag "medications not included" with a very low headline price
    meds_excluded = re.search(r"\bmedications?\s+not\s+included\b", text)
    if meds_excluded and prices:
        for raw in prices:
            try:
                amount = _parse_price(raw)
                if amount < 50_000 or amount < 2_000:
                    return True
            except ValueError:
                continue

    return False


def _flag_proprietary_protocol(text: str) -> bool:
    """Detect claims of secret or proprietary protocols not supported by evidence."""
    patterns = [
        r"\bsecret\s+protocol\b",
        r"\bproprietary\s+treatment\b",
        r"\bspecial\s+technique\b",
        r"\bexclusive\s+method\b",
        r"\bunique\s+protocol\b",
    ]
    return any(re.search(p, text) for p in patterns)


_FLAG_CHECKS: list[tuple[str, object]] = [
    (
        "Unrealistic success rate for patients over 40 (>60%)",
        _flag_unrealistic_success_rate,
    ),
    (
        "Guaranteed pregnancy claim",
        _flag_guaranteed_pregnancy,
    ),
    (
        "Pressure to use donor eggs without clinical justification",
        _flag_donor_egg_pressure,
    ),
    (
        "Unusually low all-inclusive price likely excluding medications",
        _flag_unusually_low_price,
    ),
    (
        "Proprietary or secret protocol not supported by published evidence",
        _flag_proprietary_protocol,
    ),
]


# ---------------------------------------------------------------------------
# Risk level helpers
# ---------------------------------------------------------------------------


def _risk_level(flag_count: int) -> str:
    if flag_count == 0:
        return "low"
    if flag_count <= 2:
        return "medium"
    return "high"


def _explanation(flags: list[str], risk: str) -> str:
    if not flags:
        return (
            "No red flag patterns were detected in this claim. "
            "This does not guarantee the claim is accurate — always verify with published registry data."
        )
    flag_list = "; ".join(f'"{f}"' for f in flags)
    base = (
        f"{len(flags)} red flag pattern(s) detected: {flag_list}. "
        "These patterns are associated with misleading or unsubstantiated marketing claims "
        "in fertility medicine."
    )
    if risk == "high":
        base += (
            " Given the number of red flags, we strongly recommend seeking a second opinion "
            "from an independent specialist and verifying the clinic's data on the HFEA register "
            "(UK) or ICMR registry (India) before proceeding."
        )
    return base


# ---------------------------------------------------------------------------
# Public tool function
# ---------------------------------------------------------------------------


def red_flag_tool(clinic_claim: str) -> RedFlagOutput:
    """Analyse a clinic claim for red flag patterns.

    Args:
        clinic_claim: Free-text claim made by a clinic (e.g. from a website or consultation).

    Returns:
        RedFlagOutput with detected flags, risk level, explanation, and a note on
        what legitimate clinics look like.
    """
    if not clinic_claim or not clinic_claim.strip():
        return RedFlagOutput(
            flags_found=[],
            risk_level="low",
            explanation="No claim provided. No red flags detected.",
            legitimate_clinic_note=_LEGITIMATE_CLINIC_NOTE,
        )

    text = clinic_claim.lower()
    flags_found: list[str] = []

    for label, check_fn in _FLAG_CHECKS:
        if check_fn(text):
            flags_found.append(label)

    risk = _risk_level(len(flags_found))
    explanation = _explanation(flags_found, risk)

    return RedFlagOutput(
        flags_found=flags_found,
        risk_level=risk,
        explanation=explanation,
        legitimate_clinic_note=_LEGITIMATE_CLINIC_NOTE,
    )
