"""IVF lab result interpretation tool — classifies AMH, FSH, and AFC values."""

from __future__ import annotations

from ivf_advisor.models import LabResultOutput

_DISCLAIMER = (
    "These classifications are for educational purposes only and do not constitute "
    "medical advice. Lab reference ranges vary between laboratories and assay methods. "
    "Always discuss your results with your treating fertility specialist, who can "
    "interpret them in the context of your full clinical picture."
)


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def _classify_amh(amh: float) -> tuple[str, str]:
    """Return (classification, explanation) for an AMH value in ng/mL."""
    if amh < 1.0:
        return (
            "low",
            f"AMH of {amh} ng/mL is below 1.0 ng/mL, indicating a low ovarian reserve. "
            "This may be associated with fewer eggs retrieved per cycle and a higher risk "
            "of poor response to stimulation.",
        )
    if amh <= 3.5:
        return (
            "normal",
            f"AMH of {amh} ng/mL falls within the normal range (1.0–3.5 ng/mL), "
            "suggesting an adequate ovarian reserve for IVF stimulation.",
        )
    return (
        "high",
        f"AMH of {amh} ng/mL is above 3.5 ng/mL, indicating a high ovarian reserve. "
        "While this often means a good response to stimulation, it also carries an "
        "increased risk of ovarian hyperstimulation syndrome (OHSS).",
    )


def _classify_fsh(fsh: float) -> tuple[str, str]:
    """Return (classification, explanation) for an FSH value in IU/L."""
    if fsh < 10.0:
        return (
            "normal",
            f"FSH of {fsh} IU/L is within the normal range (<10 IU/L), consistent with "
            "adequate ovarian reserve.",
        )
    if fsh <= 15.0:
        return (
            "borderline",
            f"FSH of {fsh} IU/L is borderline elevated (10–15 IU/L). This may indicate "
            "early diminished ovarian reserve and warrants further evaluation alongside "
            "other markers such as AMH and AFC.",
        )
    return (
        "elevated",
        f"FSH of {fsh} IU/L is elevated (>15 IU/L), which is associated with diminished "
        "ovarian reserve and may predict a poorer response to stimulation.",
    )


def _classify_afc(afc: int) -> tuple[str, str]:
    """Return (classification, explanation) for an antral follicle count."""
    if afc < 7:
        return (
            "low",
            f"AFC of {afc} follicles is below 7, indicating a low ovarian reserve. "
            "This is associated with fewer eggs retrieved and a higher cancellation rate.",
        )
    if afc <= 15:
        return (
            "normal",
            f"AFC of {afc} follicles falls within the normal range (7–15), suggesting "
            "a good ovarian reserve and a reasonable response to stimulation.",
        )
    return (
        "high",
        f"AFC of {afc} follicles is above 15, indicating a high ovarian reserve. "
        "This is associated with a strong response to stimulation but also an elevated "
        "risk of OHSS.",
    )


# ---------------------------------------------------------------------------
# Age context helper
# ---------------------------------------------------------------------------


def _age_context(age: int, amh_class: str | None, fsh_class: str | None, afc_class: str | None) -> str:
    """Return a brief age-contextualised note."""
    if age < 35:
        context = "Under 35, ovarian reserve markers are expected to be in the normal range."
    elif age <= 37:
        context = "At 35–37, a mild decline in ovarian reserve is normal and expected."
    elif age <= 40:
        context = "At 38–40, ovarian reserve naturally declines; borderline results are more common."
    elif age <= 42:
        context = "At 41–42, reduced ovarian reserve is typical; results should be interpreted with this in mind."
    else:
        context = "Over 42, significantly reduced ovarian reserve is expected; results should be discussed carefully with your specialist."

    # Add a note if markers are inconsistent with age expectations
    low_markers = [c for c in [amh_class, fsh_class, afc_class] if c in ("low", "elevated")]
    high_markers = [c for c in [amh_class, fsh_class, afc_class] if c in ("high",)]

    if age < 38 and low_markers:
        context += (
            " Your results suggest reduced reserve that is lower than typical for your age group — "
            "your specialist may recommend further investigation."
        )
    elif age >= 38 and high_markers:
        context += (
            " Your results suggest a higher-than-expected reserve for your age group, which is a positive finding."
        )

    return context


# ---------------------------------------------------------------------------
# Combined interpretation helper
# ---------------------------------------------------------------------------


def _combined_interpretation(
    amh_class: str | None,
    fsh_class: str | None,
    afc_class: str | None,
) -> str:
    """Synthesise a combined interpretation from two or more available markers."""
    classes = {
        "amh": amh_class,
        "fsh": fsh_class,
        "afc": afc_class,
    }
    available = {k: v for k, v in classes.items() if v is not None}

    low_signals = sum(
        1 for v in available.values() if v in ("low", "elevated")
    )
    high_signals = sum(1 for v in available.values() if v == "high")
    normal_signals = sum(1 for v in available.values() if v == "normal")
    total = len(available)

    if low_signals == total:
        return (
            "All available markers consistently indicate a reduced ovarian reserve. "
            "Your specialist will discuss stimulation protocol options and realistic expectations with you."
        )
    if high_signals == total:
        return (
            "All available markers indicate a high ovarian reserve. "
            "Your protocol will likely be tailored to minimise the risk of OHSS."
        )
    if normal_signals == total:
        return (
            "All available markers are within the normal range, suggesting a good ovarian reserve "
            "and a reasonable prognosis for IVF stimulation."
        )
    if low_signals > 0 and normal_signals > 0:
        return (
            "Your markers show a mixed picture, with some values suggesting reduced reserve "
            "and others within the normal range. Your specialist will weigh all results together "
            "to guide your protocol."
        )
    if high_signals > 0 and normal_signals > 0:
        return (
            "Your markers are broadly reassuring, with some values in the high range. "
            "Your specialist will tailor your stimulation dose to optimise response while "
            "managing OHSS risk."
        )
    return (
        "Your markers present a mixed picture. Your specialist will interpret these results "
        "alongside your full clinical history."
    )


# ---------------------------------------------------------------------------
# Public tool function
# ---------------------------------------------------------------------------


def lab_result_tool(
    amh: float | None = None,
    fsh: float | None = None,
    afc: int | None = None,
    age: int | None = None,
) -> LabResultOutput:
    """Interpret IVF ovarian reserve lab results.

    Args:
        amh: Anti-Müllerian hormone in ng/mL (optional).
        fsh: Follicle-stimulating hormone in IU/L (optional).
        afc: Antral follicle count — number of follicles (optional).
        age: Patient age in years (optional, used for contextualisation).

    Returns:
        LabResultOutput with per-marker classifications, optional combined
        interpretation, optional age context, and a specialist disclaimer.
    """
    # All-None input: return disclaimer only
    if amh is None and fsh is None and afc is None:
        return LabResultOutput(disclaimer=_DISCLAIMER)

    amh_classification: str | None = None
    amh_explanation: str | None = None
    fsh_classification: str | None = None
    fsh_explanation: str | None = None
    afc_classification: str | None = None
    afc_explanation: str | None = None

    if amh is not None:
        amh_classification, amh_explanation = _classify_amh(amh)
    if fsh is not None:
        fsh_classification, fsh_explanation = _classify_fsh(fsh)
    if afc is not None:
        afc_classification, afc_explanation = _classify_afc(afc)

    # Combined interpretation when ≥2 values provided
    provided_count = sum(x is not None for x in [amh, fsh, afc])
    combined: str | None = None
    if provided_count >= 2:
        combined = _combined_interpretation(amh_classification, fsh_classification, afc_classification)

    # Age context
    age_ctx: str | None = None
    if age is not None:
        age_ctx = _age_context(age, amh_classification, fsh_classification, afc_classification)

    return LabResultOutput(
        amh_classification=amh_classification,
        amh_explanation=amh_explanation,
        fsh_classification=fsh_classification,
        fsh_explanation=fsh_explanation,
        afc_classification=afc_classification,
        afc_explanation=afc_explanation,
        combined_interpretation=combined,
        age_context=age_ctx,
        disclaimer=_DISCLAIMER,
    )
