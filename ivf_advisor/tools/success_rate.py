"""IVF success rate tool — returns age-adjusted live birth rate estimates."""

from __future__ import annotations

from ivf_advisor.models import SuccessRateOutput

# ---------------------------------------------------------------------------
# Age band definitions: (label, low%, high%)
# ---------------------------------------------------------------------------

_AGE_BANDS: list[tuple[str, float, float]] = [
    ("<35",   40.0, 50.0),
    ("35-37", 35.0, 42.0),
    ("38-40", 25.0, 35.0),
    ("41-42", 15.0, 22.0),
    (">42",    5.0, 12.0),
]

_DATA_SOURCE = "SART/HFEA 2022-2023 data"

_DISCLAIMER = (
    "These figures represent population-level statistics from published registry data "
    "and are not a prediction of your individual outcome. Success rates vary by clinic, "
    "laboratory quality, stimulation protocol, and many patient-specific factors not "
    "captured here. Always discuss your personal prognosis with your treating clinician."
)

# ---------------------------------------------------------------------------
# Diagnosis adjustment table: (low_delta%, high_delta%, explanation)
# ---------------------------------------------------------------------------

_DIAGNOSIS_ADJUSTMENTS: list[tuple[list[str], float, float, str]] = [
    (
        ["diminished ovarian reserve", "low amh", "poor responder"],
        -12.0, -8.0,
        "Diminished ovarian reserve / low AMH is associated with fewer eggs retrieved "
        "and a higher cycle cancellation rate, reducing per-cycle success rates.",
    ),
    (
        ["pcos", "polycystic"],
        2.0, 5.0,
        "PCOS is generally associated with a good ovarian response to stimulation, "
        "which can support slightly higher success rates per cycle.",
    ),
    (
        ["male factor", "azoospermia"],
        0.0, 0.0,
        "Male factor infertility is typically addressed with ICSI, which restores "
        "fertilisation rates to normal levels. Female age-based rates apply.",
    ),
    (
        ["endometriosis"],
        -8.0, -5.0,
        "Endometriosis can affect egg quality and implantation, leading to modestly "
        "reduced success rates compared to the general population.",
    ),
    (
        ["unexplained infertility"],
        0.0, 0.0,
        "Unexplained infertility does not carry a specific adjustment — age-based "
        "rates apply.",
    ),
    (
        ["recurrent miscarriage", "recurrent implantation failure"],
        -10.0, -5.0,
        "Recurrent miscarriage or implantation failure suggests underlying factors "
        "(immunological, anatomical, or embryonic) that reduce per-cycle live birth rates.",
    ),
]


def _get_age_band(age: int) -> tuple[str, float, float] | None:
    """Return (label, low, high) for the given age, or None if out of range."""
    if age < 35:
        return _AGE_BANDS[0]
    if age <= 37:
        return _AGE_BANDS[1]
    if age <= 40:
        return _AGE_BANDS[2]
    if age <= 42:
        return _AGE_BANDS[3]
    return _AGE_BANDS[4]


def _match_diagnosis(diagnosis: str | None) -> tuple[float, float, str] | None:
    """Return (low_delta, high_delta, explanation) for a matched diagnosis, or None."""
    if not diagnosis:
        return None
    diag_lower = diagnosis.lower().strip()
    for keywords, low_delta, high_delta, explanation in _DIAGNOSIS_ADJUSTMENTS:
        if any(kw in diag_lower for kw in keywords):
            return low_delta, high_delta, explanation
    return None


def success_rate_tool(
    age: int,
    diagnosis: str | None = None,
    num_embryos: int = 1,
) -> SuccessRateOutput:
    """Returns estimated IVF live birth rate ranges based on age, diagnosis, and embryo count.

    Args:
        age: Patient age in years.
        diagnosis: Optional primary diagnosis (free text). Matched against known
                   categories to apply evidence-based adjustments.
        num_embryos: Number of embryos available for transfer. When > 1, a cumulative
                     success note is added explaining the benefit of additional transfers.

    Returns:
        SuccessRateOutput with base and adjusted rate ranges, data source, and disclaimer.
    """
    # Validate age range
    if age < 18 or age > 55:
        return SuccessRateOutput(
            age_band="N/A",
            base_rate_low=0.0,
            base_rate_high=0.0,
            data_source=_DATA_SOURCE,
            disclaimer=(
                f"Age {age} is outside the supported range (18–55). "
                "Success rate estimates are not available for this age. "
                "Please consult a fertility specialist for personalised guidance. "
                + _DISCLAIMER
            ),
        )

    band_label, base_low, base_high = _get_age_band(age)

    # Diagnosis adjustment
    adjustment = _match_diagnosis(diagnosis)
    adjusted_low: float | None = None
    adjusted_high: float | None = None
    adjustment_explanation: str | None = None

    if adjustment is not None:
        low_delta, high_delta, explanation = adjustment
        # Only apply non-zero adjustments
        if low_delta != 0.0 or high_delta != 0.0:
            adjusted_low = max(0.0, base_low + low_delta)
            adjusted_high = max(0.0, base_high + high_delta)
            adjustment_explanation = explanation

    # Cumulative note for multiple embryos
    cumulative_note: str | None = None
    if num_embryos > 1:
        effective_low = adjusted_low if adjusted_low is not None else base_low
        effective_high = adjusted_high if adjusted_high is not None else base_high
        # Each additional transfer adds ~50-60% of the per-cycle rate
        extra_transfers = num_embryos - 1
        cumulative_low = round(
            effective_low + extra_transfers * effective_low * 0.50, 1
        )
        cumulative_high = round(
            effective_high + extra_transfers * effective_high * 0.60, 1
        )
        cumulative_note = (
            f"With {num_embryos} embryos available, the cumulative success rate across "
            f"all transfers is estimated at {cumulative_low}%–{cumulative_high}%. "
            f"Each additional frozen embryo transfer adds approximately 50–60% of the "
            f"per-cycle rate, because each transfer is an independent attempt."
        )

    return SuccessRateOutput(
        age_band=band_label,
        base_rate_low=base_low,
        base_rate_high=base_high,
        adjusted_rate_low=adjusted_low,
        adjusted_rate_high=adjusted_high,
        adjustment_explanation=adjustment_explanation,
        cumulative_note=cumulative_note,
        data_source=_DATA_SOURCE,
        disclaimer=_DISCLAIMER,
    )
