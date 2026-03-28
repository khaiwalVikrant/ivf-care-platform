"""IVF cost breakdown tool — returns a structured breakdown of all cost components."""

from __future__ import annotations

from ivf_advisor.models import CostBreakdownOutput, CostComponent, CostVariability

_INDIAN_CITIES = {
    "mumbai", "delhi", "bangalore", "bengaluru", "chennai", "hyderabad",
    "pune", "kolkata", "ahmedabad", "jaipur", "lucknow", "india", "indian",
    "chandigarh", "noida", "gurgaon", "gurugram", "surat", "kochi", "nagpur",
}

# ---------------------------------------------------------------------------
# India-specific cost components (INR)
# ---------------------------------------------------------------------------

_INDIA_CORE_COMPONENTS: list[CostComponent] = [
    CostComponent(
        name="Initial Consultation",
        description="First appointment with a fertility specialist including medical history review, baseline blood tests (AMH, FSH, LH), and ultrasound.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=500.0,
        typical_range_high=2000.0,
        notes="Costs vary between government hospitals (subsidised) and private fertility clinics. Many top private clinics in metro cities charge ₹1,000–₹2,000.",
        is_addon=False,
    ),
    CostComponent(
        name="Monitoring Scans",
        description="Serial ultrasound scans during ovarian stimulation to track follicle growth, typically 3–6 visits.",
        variability=CostVariability.PATIENT_VARIABLE,
        typical_range_low=3000.0,
        typical_range_high=10000.0,
        notes="Per scan costs range from ₹500–₹2,000. Some clinics bundle monitoring into the package price — always confirm.",
        is_addon=False,
    ),
    CostComponent(
        name="Medications",
        description="Fertility injections (FSH/LH gonadotrophins), GnRH antagonist, trigger injection, and progesterone support.",
        variability=CostVariability.PATIENT_VARIABLE,
        typical_range_low=30000.0,
        typical_range_high=80000.0,
        notes="Medication is the most variable cost. Indian-manufactured generics (e.g. Recagon, Folisurge) are significantly cheaper than imported brands. Ask your clinic for a medication budget based on your AMH.",
        is_addon=False,
    ),
    CostComponent(
        name="Laboratory Fees",
        description="Embryology lab charges covering egg/sperm preparation, fertilisation, embryo culture to blastocyst, and grading.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=20000.0,
        typical_range_high=50000.0,
        notes="Usually included in the clinic's IVF package. ICSI is often charged separately. Confirm what is included.",
        is_addon=False,
    ),
    CostComponent(
        name="Egg Retrieval Procedure",
        description="Surgical egg collection under sedation, approximately 36 hours after trigger injection.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=15000.0,
        typical_range_high=40000.0,
        notes="Usually included in all-inclusive packages. Anaesthesia fees may be charged separately at some clinics.",
        is_addon=False,
    ),
    CostComponent(
        name="Embryo Transfer",
        description="Procedure to place embryo(s) into the uterus under ultrasound guidance.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=5000.0,
        typical_range_high=15000.0,
        notes="Usually included in the base package. Frozen embryo transfer (FET) in a subsequent cycle is charged separately.",
        is_addon=False,
    ),
]

_INDIA_ADDON_COMPONENTS: list[CostComponent] = [
    CostComponent(
        name="ICSI (Intracytoplasmic Sperm Injection)",
        description="Single sperm injected directly into each egg. Recommended for male factor infertility or previous fertilisation failure.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=20000.0,
        typical_range_high=50000.0,
        notes="Very commonly recommended in India. Often charged on top of the base IVF package.",
        is_addon=True,
    ),
    CostComponent(
        name="Preimplantation Genetic Testing (PGT-A)",
        description="Genetic screening of embryos before transfer to identify chromosomally normal embryos.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=50000.0,
        typical_range_high=150000.0,
        notes="Available at larger fertility centres in metro cities. Adds significant cost — discuss clinical indication with your doctor.",
        is_addon=True,
    ),
    CostComponent(
        name="Embryo Freezing and Storage",
        description="Vitrification of surplus embryos plus annual storage fees.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=10000.0,
        typical_range_high=25000.0,
        notes="Annual storage fees typically ₹5,000–₹10,000/year. Confirm the clinic's storage policy.",
        is_addon=True,
    ),
]

_INDIA_CITY_RANGES = {
    "mumbai":    {"low": 120000, "high": 350000},
    "delhi":     {"low": 100000, "high": 300000},
    "bangalore": {"low": 100000, "high": 280000},
    "bengaluru": {"low": 100000, "high": 280000},
    "chennai":   {"low": 90000,  "high": 250000},
    "hyderabad": {"low": 90000,  "high": 250000},
    "pune":      {"low": 90000,  "high": 250000},
    "kolkata":   {"low": 80000,  "high": 220000},
    "default":   {"low": 80000,  "high": 300000},
}

_INDIA_MULTI_CYCLE_NOTE = (
    "IVF costs in India are significantly lower than in Western countries, making India "
    "a destination for medical tourism. However, costs are cumulative — most patients "
    "require 2–3 cycles. Budget for multiple cycles rather than assuming one will suffice. "
    "Government hospitals (e.g. AIIMS, NIMHANS) offer subsidised IVF for eligible patients. "
    "Some states have government schemes — check with your state health department."
)

_INDIA_CLINIC_QUESTIONS: list[str] = [
    "What is included in your IVF package price — does it cover medications?",
    "Are monitoring scans and blood tests included or billed separately?",
    "Is ICSI included in the base price or charged additionally?",
    "Do you use Indian-manufactured or imported medications — what is the cost difference?",
    "Do you offer EMI or payment plan options?",
    "Are there any government scheme benefits I may be eligible for?",
    "What are the costs for a frozen embryo transfer (FET) if needed?",
    "What are your annual embryo storage fees?",
    "What is your cancellation/refund policy if the cycle is cancelled?",
]

# ---------------------------------------------------------------------------
# Core cost components (default — UK/international)
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
            "ovarian stimulation phase to track follicle growth and number."
        ),
        variability=CostVariability.PATIENT_VARIABLE,
        typical_range_low=150.0,
        typical_range_high=600.0,
        notes="Multiple scans required per cycle — typically 3–6 visits.",
        is_addon=False,
    ),
    CostComponent(
        name="Medications",
        description=(
            "Prescription fertility medications including gonadotrophins, GnRH antagonist, "
            "trigger injection, and progesterone supplementation."
        ),
        variability=CostVariability.PATIENT_VARIABLE,
        typical_range_low=800.0,
        typical_range_high=3000.0,
        notes="Highly variable — depends on individual response and brand.",
        is_addon=False,
    ),
    CostComponent(
        name="Laboratory Fees",
        description="Embryology lab charges covering fertilisation, embryo culture, and grading.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=1000.0,
        typical_range_high=2500.0,
        notes="Usually included in the clinic package. ICSI often charged separately.",
        is_addon=False,
    ),
    CostComponent(
        name="Egg Retrieval Procedure",
        description="Surgical egg collection under sedation.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=1500.0,
        typical_range_high=3500.0,
        notes="Usually included in all-inclusive packages.",
        is_addon=False,
    ),
    CostComponent(
        name="Embryo Transfer",
        description="Procedure to place embryo(s) into the uterus under ultrasound guidance.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=500.0,
        typical_range_high=1500.0,
        notes="Usually included in the base package.",
        is_addon=False,
    ),
]

_ADDON_COMPONENTS: list[CostComponent] = [
    CostComponent(
        name="ICSI (Intracytoplasmic Sperm Injection)",
        description="Single sperm injected directly into each egg.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=800.0,
        typical_range_high=1500.0,
        notes="Often charged on top of the base IVF package.",
        is_addon=True,
    ),
    CostComponent(
        name="Preimplantation Genetic Testing (PGT-A)",
        description="Genetic screening of embryos before transfer.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=2000.0,
        typical_range_high=5000.0,
        notes="Discuss clinical indication with your doctor before proceeding.",
        is_addon=True,
    ),
    CostComponent(
        name="Embryo Freezing and Storage",
        description="Vitrification of surplus embryos plus annual storage fees.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=300.0,
        typical_range_high=800.0,
        notes="Annual storage fees commonly £200–£400/year in the UK.",
        is_addon=True,
    ),
    CostComponent(
        name="Endometrial Receptivity Testing (ERA)",
        description="Biopsy-based test to identify optimal embryo transfer timing.",
        variability=CostVariability.CLINIC_VARIABLE,
        typical_range_low=600.0,
        typical_range_high=1200.0,
        notes="Limited evidence for routine use — discuss with your clinic.",
        is_addon=True,
    ),
]

_MULTI_CYCLE_NOTE = (
    "IVF costs are cumulative. Many patients require more than one cycle to achieve a "
    "successful pregnancy — national data suggests that, on average, patients undergo "
    "2–3 cycles. When budgeting, plan for the possibility of multiple cycles. "
    "Some clinics offer multi-cycle packages or refund programmes."
)

_CLINIC_QUESTIONS: list[str] = [
    "What is included in your quoted IVF package price, and what is charged separately?",
    "Are monitoring scans and blood tests included in the package, or billed per visit?",
    "Is ICSI included in the base price, or is it an additional charge?",
    "What is your cancellation policy if the cycle is abandoned before egg retrieval?",
    "Do you offer multi-cycle packages or refund programmes?",
    "What financing or payment plan options do you offer?",
    "What are the costs for a frozen embryo transfer (FET) cycle?",
    "What are your annual embryo storage fees?",
    "Are there any additional costs I should anticipate?",
]


def _is_india_region(region: str | None) -> bool:
    if not region:
        return False
    return region.lower().strip() in _INDIAN_CITIES


def cost_breakdown_tool(
    region: str | None = None,
    include_addons: bool = False,
    profile_context: str | None = None,
) -> CostBreakdownOutput:
    """Returns a structured IVF cost breakdown covering all cost components.

    Args:
        region: Optional country/region/city. Pass 'india' or an Indian city name
                (e.g. 'Mumbai', 'Delhi') to get INR cost ranges.
        include_addons: Whether to include optional add-on treatment costs.
        profile_context: Optional JSON string of patient profile (reserved for future use).

    Returns:
        CostBreakdownOutput with per-component cost ranges in the appropriate currency.
    """
    if _is_india_region(region):
        components: list[CostComponent] = list(_INDIA_CORE_COMPONENTS)
        if include_addons:
            components += list(_INDIA_ADDON_COMPONENTS)

        city_key = region.lower().strip() if region else "default"
        city_range = _INDIA_CITY_RANGES.get(city_key, _INDIA_CITY_RANGES["default"])
        city_note = (
            f"In {region.title()}, a complete IVF cycle (excluding medications) typically "
            f"costs between ₹{city_range['low']:,} and ₹{city_range['high']:,}. "
            f"Medications add approximately ₹30,000–₹80,000 on top."
        )

        return CostBreakdownOutput(
            components=components,
            multi_cycle_note=_INDIA_MULTI_CYCLE_NOTE + "\n\n" + city_note,
            clinic_questions=list(_INDIA_CLINIC_QUESTIONS),
            region=region,
        )

    # Default: international/UK ranges
    components = list(_CORE_COMPONENTS)
    if include_addons:
        components += list(_ADDON_COMPONENTS)

    return CostBreakdownOutput(
        components=components,
        multi_cycle_note=_MULTI_CYCLE_NOTE,
        clinic_questions=list(_CLINIC_QUESTIONS),
        region=region,
    )


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
