"""IVF cost breakdown tool — returns a structured breakdown of all cost components."""

from __future__ import annotations

from ivf_advisor.models import CostBreakdownOutput, CostComponent, CostVariability

# ---------------------------------------------------------------------------
# Core cost components (Phase 1 — region-agnostic)
# ---------------------------------------------------------------------------

_CORE_COMPONENTS: list[CostComponent] = [
    CostComponent(
        name="Initial Consultation",
        description=(
            "Your first appointment with a fertility specialist, including a review of "
            "medical history, baseline blood tests (AMH, FSH, LH, oestradiol), and an "
            "antral follicle count (AFC) ultrasound. A personalised treatment plan is "
            "discussed and consent forms are signed."
        ),
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=200.0,
        typical_range_high=500.0,
        notes=(
            "Fees vary significantly between private clinics. Some clinics offer a free "
            "or reduced-cost initial consultation. NHS-funded patients may not incur this "
            "cost if referred via their GP."
        ),
        is_addon=False,
    ),
    CostComponent(
        name="Monitoring Scans",
        description=(
            "Serial transvaginal ultrasound scans performed every 1–3 days during the "
            "ovarian stimulation phase to track follicle growth and number. Blood tests "
            "measuring oestradiol and LH levels are typically included."
        ),
        variability=CostVariability.PATIENT_VARIABLE,
        typical_range_low=150.0,
        typical_range_high=600.0,
        notes=(
            "Multiple scans are required per cycle — typically 3–6 visits. The total "
            "cost depends on how many scans your response requires. Some clinics include "
            "monitoring in an all-inclusive package price; others charge per scan. "
            "Always confirm whether monitoring is bundled or billed separately."
        ),
        is_addon=False,
    ),
    CostComponent(
        name="Medications",
        description=(
            "Prescription fertility medications used during ovarian stimulation, including "
            "gonadotrophins (FSH/LH injections), GnRH agonists or antagonists to prevent "
            "premature ovulation, a trigger injection (hCG or GnRH agonist), and "
            "progesterone supplementation after egg retrieval."
        ),
        variability=CostVariability.PATIENT_VARIABLE,
        typical_range_low=800.0,
        typical_range_high=3000.0,
        notes=(
            "Medication costs are highly variable and depend on your individual response "
            "to stimulation — patients with lower ovarian reserve typically require higher "
            "doses and therefore higher costs. Costs also vary by brand and pharmacy. "
            "Ask your clinic for a realistic medication budget estimate based on your "
            "AMH and AFC results."
        ),
        is_addon=False,
    ),
    CostComponent(
        name="Laboratory Fees",
        description=(
            "Embryology laboratory charges covering egg and sperm preparation, "
            "fertilisation (conventional IVF or ICSI), embryo culture to blastocyst "
            "stage (day 5–6), and embryo assessment and grading by the embryologist."
        ),
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=1000.0,
        typical_range_high=2500.0,
        notes=(
            "Laboratory fees are usually included in the clinic's quoted IVF package "
            "price, but ICSI is often charged as an add-on. Confirm whether the quoted "
            "price covers conventional IVF only or includes ICSI if that is your "
            "recommended approach."
        ),
        is_addon=False,
    ),
    CostComponent(
        name="Egg Retrieval Procedure",
        description=(
            "The surgical procedure to collect mature eggs from the ovaries under "
            "sedation or light general anaesthesia, performed approximately 36 hours "
            "after the trigger injection. Includes the procedure room, anaesthesia, "
            "and immediate post-procedure recovery."
        ),
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=1500.0,
        typical_range_high=3500.0,
        notes=(
            "This is typically one of the largest single cost items in an IVF cycle. "
            "It is usually included in all-inclusive package prices. If billed separately, "
            "confirm whether anaesthesia fees are included or charged additionally."
        ),
        is_addon=False,
    ),
    CostComponent(
        name="Embryo Transfer",
        description=(
            "The procedure to place one or more embryos into the uterus via a thin "
            "catheter under ultrasound guidance. No sedation is usually required. "
            "Includes the transfer procedure and ultrasound guidance."
        ),
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=500.0,
        typical_range_high=1500.0,
        notes=(
            "Embryo transfer is usually included in the base IVF package price. "
            "Frozen embryo transfer (FET) in a subsequent cycle is typically charged "
            "separately and may include additional costs for endometrial preparation "
            "medications and monitoring scans."
        ),
        is_addon=False,
    ),
]

# ---------------------------------------------------------------------------
# Add-on components (appended when include_addons=True)
# ---------------------------------------------------------------------------

_ADDON_COMPONENTS: list[CostComponent] = [
    CostComponent(
        name="ICSI (Intracytoplasmic Sperm Injection)",
        description=(
            "A laboratory technique where a single sperm is injected directly into each "
            "mature egg to assist fertilisation. Recommended for male factor infertility, "
            "previous fertilisation failure, or low egg numbers."
        ),
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=800.0,
        typical_range_high=1500.0,
        notes=(
            "ICSI is one of the most commonly recommended add-ons. It is often charged "
            "on top of the base IVF package. Discuss with your clinic whether ICSI is "
            "clinically indicated for your situation — it is not routinely necessary for "
            "all patients."
        ),
        is_addon=True,
    ),
    CostComponent(
        name="Preimplantation Genetic Testing (PGT-A)",
        description=(
            "Genetic screening of embryos before transfer to identify chromosomally "
            "normal (euploid) embryos. Aims to improve implantation rates and reduce "
            "miscarriage risk, particularly for patients over 35 or with recurrent "
            "implantation failure."
        ),
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=2000.0,
        typical_range_high=5000.0,
        notes=(
            "PGT-A adds significant cost and requires embryo biopsy, which carries a "
            "small risk of embryo damage. The evidence for routine use in all patients "
            "is mixed — ESHRE and ASRM guidelines recommend it selectively. Discuss "
            "whether it is appropriate for your circumstances."
        ),
        is_addon=True,
    ),
    CostComponent(
        name="Embryo Freezing and Storage",
        description=(
            "Vitrification (rapid freezing) of surplus good-quality embryos not "
            "transferred in the fresh cycle, plus annual storage fees. Frozen embryos "
            "can be used in future frozen embryo transfer (FET) cycles."
        ),
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=300.0,
        typical_range_high=800.0,
        notes=(
            "Freezing fees are typically a one-off charge; annual storage fees are "
            "charged separately (commonly £200–£400/year in the UK). Confirm the "
            "clinic's storage policy, including what happens to embryos if you do not "
            "return for a FET cycle."
        ),
        is_addon=True,
    ),
    CostComponent(
        name="Endometrial Receptivity Testing (ERA)",
        description=(
            "A biopsy-based test to identify the personalised window of implantation — "
            "the optimal time for embryo transfer in a given patient. Sometimes "
            "recommended after recurrent implantation failure."
        ),
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=600.0,
        typical_range_high=1200.0,
        notes=(
            "ERA is an add-on with limited evidence for routine use. Current NICE and "
            "ESHRE guidance does not recommend it outside of research settings for most "
            "patients. Discuss the evidence base with your clinic before proceeding."
        ),
        is_addon=True,
    ),
]

# ---------------------------------------------------------------------------
# Multi-cycle note
# ---------------------------------------------------------------------------

_MULTI_CYCLE_NOTE = (
    "IVF costs are cumulative. Many patients require more than one cycle to achieve a "
    "successful pregnancy — national data suggests that, on average, patients undergo "
    "2–3 cycles. This means the total financial commitment can be two to three times "
    "the cost of a single cycle. When budgeting, plan for the possibility of multiple "
    "cycles rather than assuming one will be sufficient. Some clinics offer multi-cycle "
    "packages or refund programmes — ask about these options when comparing clinics."
)

# ---------------------------------------------------------------------------
# Clinic questions
# ---------------------------------------------------------------------------

_CLINIC_QUESTIONS: list[str] = [
    "What is included in your quoted IVF package price, and what is charged separately?",
    "Are monitoring scans and blood tests included in the package, or billed per visit?",
    "Is ICSI included in the base price, or is it an additional charge?",
    "What is your cancellation policy if the cycle is abandoned before egg retrieval — will I receive a partial refund?",
    "Do you offer multi-cycle packages or refund programmes, and what are the eligibility criteria?",
    "What financing or payment plan options do you offer?",
    "Are there any funding or grant schemes I may be eligible for (e.g., NHS funding, employer fertility benefits)?",
    "What are the costs for a frozen embryo transfer (FET) cycle if I have embryos remaining?",
    "What are your annual embryo storage fees, and how long can embryos be stored?",
    "Are there any additional costs I should anticipate that are not covered in the quoted price?",
]

# ---------------------------------------------------------------------------
# Tool function
# ---------------------------------------------------------------------------


def cost_breakdown_tool(
    region: str | None = None,
    include_addons: bool = False,
    profile_context: str | None = None,
) -> CostBreakdownOutput:
    """Returns a structured IVF cost breakdown covering all cost components.

    Args:
        region: Optional country/region code for localised cost ranges.
                Region-aware logic is a Phase 2 feature; in Phase 1 this parameter
                is accepted but does not alter the output (region=None / currency=None
                on all components).
        include_addons: Whether to include optional add-on treatment costs.
                        When True, add-on components (ICSI, PGT-A, embryo freezing,
                        ERA) are appended to the core components list.
        profile_context: Optional JSON string of patient profile. Accepted for
                         forward-compatibility; not used in Phase 1.

    Returns:
        CostBreakdownOutput with per-component cost ranges, fixed vs variable
        classification, multi-cycle note, and clinic questions list.
    """
    components: list[CostComponent] = list(_CORE_COMPONENTS)

    if include_addons:
        components = components + list(_ADDON_COMPONENTS)

    # Phase 1: region-aware logic is a stub — region and currency remain None
    # Full region-aware implementation is delivered in Phase 2 (task 16).
    return CostBreakdownOutput(
        components=components,
        multi_cycle_note=_MULTI_CYCLE_NOTE,
        clinic_questions=list(_CLINIC_QUESTIONS),
        region=None,
    )
