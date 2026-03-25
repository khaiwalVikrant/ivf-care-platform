"""IVF journey guide tool — returns structured stage-by-stage guidance."""

from __future__ import annotations

import json

from ivf_advisor.models import JourneyGuideOutput, TreatmentStage

# ---------------------------------------------------------------------------
# Static stage definitions (sequence_number 1–8)
# ---------------------------------------------------------------------------

_STAGES: list[TreatmentStage] = [
    TreatmentStage(
        name="Initial Consultation",
        slug="initial_consultation",
        sequence_number=1,
        typical_duration="1–2 appointments over 1–2 weeks",
        description=(
            "Your first meeting with a fertility specialist. The clinic reviews your "
            "medical history, may order baseline blood tests and an antral follicle "
            "count (AFC) ultrasound, and discusses your diagnosis and treatment options. "
            "A personalised protocol is proposed and consent forms are signed."
        ),
        physical_experience=(
            "You may have blood drawn and a transvaginal ultrasound. Both are brief and "
            "minimally uncomfortable. No medications are started yet."
        ),
        emotional_notes=(
            "Many patients feel a mix of hope and anxiety at this stage. It is common to "
            "feel overwhelmed by the volume of information. Writing down questions in "
            "advance and bringing a support person can help."
        ),
        decisions_required=[
            "Choose a fertility clinic and specialist",
            "Decide whether to proceed with IVF or explore other options first",
            "Review and sign informed consent documents",
            "Discuss and agree on the stimulation protocol",
            "Clarify costs and payment arrangements",
        ],
    ),
    TreatmentStage(
        name="Ovarian Stimulation",
        slug="ovarian_stimulation",
        sequence_number=2,
        typical_duration="8–14 days",
        description=(
            "You self-administer daily hormone injections (gonadotrophins) to stimulate "
            "your ovaries to produce multiple follicles. A GnRH agonist or antagonist "
            "is added to prevent premature ovulation. The clinic adjusts medication doses "
            "based on your response."
        ),
        physical_experience=(
            "Injection sites (usually the abdomen) may be tender or bruised. As follicles "
            "grow, the ovaries enlarge and you may feel bloating, pelvic pressure, or "
            "mild cramping. Headaches and mood fluctuations are also common."
        ),
        emotional_notes=(
            "The daily injection routine can feel relentless. Hormonal changes often "
            "intensify emotions. Many patients report feeling anxious about how their "
            "body is responding. Connecting with a support network or counsellor during "
            "this phase is strongly encouraged."
        ),
        decisions_required=[
            "Learn and practise self-injection technique",
            "Adhere strictly to the medication schedule",
            "Attend all monitoring appointments as scheduled",
            "Contact the clinic promptly if you experience severe pain or bloating",
        ],
    ),
    TreatmentStage(
        name="Monitoring Scans",
        slug="monitoring_scans",
        sequence_number=3,
        typical_duration="Multiple visits across the 8–14 day stimulation window",
        description=(
            "Regular transvaginal ultrasound scans (typically every 1–3 days) track "
            "follicle growth and number. Blood tests measure oestradiol and LH levels. "
            "The clinic uses this data to fine-tune medication doses and determine the "
            "optimal time for the trigger injection."
        ),
        physical_experience=(
            "Each scan involves a transvaginal ultrasound probe, which is mildly "
            "uncomfortable but not painful for most patients. Blood draws are routine. "
            "Expect 3–6 clinic visits during stimulation."
        ),
        emotional_notes=(
            "Waiting for scan results can be stressful. Patients often compare their "
            "follicle counts with others online, which can increase anxiety. Try to focus "
            "on your own response rather than averages."
        ),
        decisions_required=[
            "Attend all scheduled monitoring appointments — missing one can affect timing",
            "Be available to adjust your schedule at short notice as trigger timing is precise",
            "Discuss with your clinic what follicle count and size they are aiming for",
        ],
    ),
    TreatmentStage(
        name="Egg Retrieval",
        slug="egg_retrieval",
        sequence_number=4,
        typical_duration="Day procedure (30–60 minutes); recovery 1–2 days",
        description=(
            "Approximately 36 hours after the trigger injection, eggs are collected under "
            "sedation or light general anaesthesia via transvaginal ultrasound-guided "
            "needle aspiration. The embryologist immediately assesses the retrieved eggs "
            "for maturity."
        ),
        physical_experience=(
            "You will be sedated and should not feel pain during the procedure. Afterwards, "
            "cramping, bloating, and light spotting are common for 1–2 days. Most patients "
            "rest at home the day of retrieval and return to normal activities within 1–2 days. "
            "Ovarian hyperstimulation syndrome (OHSS) is a risk — report severe pain, rapid "
            "weight gain, or difficulty breathing to your clinic immediately."
        ),
        emotional_notes=(
            "The number of eggs retrieved is a significant emotional moment. Fewer eggs than "
            "expected can be devastating; more than expected can bring relief but also worry "
            "about OHSS. Try to remember that egg number is only one factor in the outcome."
        ),
        decisions_required=[
            "Arrange for someone to drive you home after the procedure",
            "Plan to rest for the remainder of the day",
            "Discuss with your clinic what happens if fewer eggs than expected are retrieved",
            "Confirm sperm sample arrangements (partner or donor) in advance",
        ],
    ),
    TreatmentStage(
        name="Fertilization and Embryo Development",
        slug="fertilization",
        sequence_number=5,
        typical_duration="5–6 days in the laboratory",
        description=(
            "Retrieved eggs are fertilised with sperm in the laboratory using conventional "
            "IVF (insemination) or intracytoplasmic sperm injection (ICSI). Fertilisation "
            "is confirmed the following morning. Embryos are cultured for 3–6 days, typically "
            "to the blastocyst stage (day 5–6). Optional preimplantation genetic testing "
            "(PGT) may be performed at this stage."
        ),
        physical_experience=(
            "You are at home during this stage. Mild residual discomfort from egg retrieval "
            "may continue for a day or two. You will begin progesterone supplementation "
            "(pessaries, injections, or gel) to prepare the uterine lining."
        ),
        emotional_notes=(
            "Waiting for fertilisation and embryo development updates is one of the most "
            "anxious periods of the IVF journey. Each daily update — fertilisation rate, "
            "cleavage, blastocyst formation — can feel like a rollercoaster. It is normal "
            "to feel grief if embryos do not develop as hoped."
        ),
        decisions_required=[
            "Decide between conventional IVF and ICSI if not already determined",
            "Decide whether to pursue PGT-A or PGT-M if applicable",
            "Discuss with your clinic how many embryos to transfer",
            "Understand the clinic's embryo freezing and storage policy",
        ],
    ),
    TreatmentStage(
        name="Embryo Transfer",
        slug="embryo_transfer",
        sequence_number=6,
        typical_duration="Day procedure (15–30 minutes); no general anaesthesia required",
        description=(
            "One (or occasionally two) embryo(s) are transferred into the uterus via a "
            "thin catheter passed through the cervix under ultrasound guidance. The "
            "procedure is usually painless and does not require sedation. Remaining "
            "good-quality embryos are frozen for future use."
        ),
        physical_experience=(
            "You may feel mild cramping during or after the transfer, similar to a smear "
            "test. A full bladder is often required for ultrasound guidance, which can be "
            "uncomfortable. You can resume normal, gentle activities the same day; "
            "strenuous exercise is typically advised against for a few days."
        ),
        emotional_notes=(
            "Transfer day is often described as both exciting and terrifying. Many patients "
            "feel a strong emotional attachment to the embryo from this moment. The "
            "pressure to 'do everything right' to support implantation is common, though "
            "there is limited evidence that rest beyond normal activity improves outcomes."
        ),
        decisions_required=[
            "Confirm the number of embryos to transfer (single embryo transfer is recommended in most cases)",
            "Discuss fresh versus frozen embryo transfer with your clinic",
            "Understand the plan for any remaining embryos (freeze, donate, discard)",
            "Clarify post-transfer medication instructions (progesterone support)",
        ],
    ),
    TreatmentStage(
        name="Two-Week Wait",
        slug="two_week_wait",
        sequence_number=7,
        typical_duration="Approximately 10–14 days",
        description=(
            "The period between embryo transfer and the pregnancy test. The embryo either "
            "implants in the uterine lining or does not. There is no clinical intervention "
            "during this time; you continue progesterone supplementation and wait."
        ),
        physical_experience=(
            "Progesterone supplementation can cause symptoms that mimic early pregnancy — "
            "breast tenderness, bloating, fatigue, and light spotting — making it very "
            "difficult to interpret physical signs. Avoid home pregnancy tests before the "
            "clinic-scheduled date, as early tests can give misleading results."
        ),
        emotional_notes=(
            "The two-week wait is widely regarded as the most psychologically challenging "
            "part of IVF. Uncertainty, symptom-spotting, and the fear of a negative result "
            "are nearly universal. Strategies that help include staying gently active, "
            "limiting internet searches, and leaning on trusted support. Professional "
            "counselling is available through most fertility clinics."
        ),
        decisions_required=[
            "Continue all prescribed medications without interruption",
            "Avoid home pregnancy tests until the clinic-advised date",
            "Plan how you will receive and process the test result — who will be with you",
            "Discuss with your partner or support person how you will handle either outcome",
        ],
    ),
    TreatmentStage(
        name="Pregnancy Test",
        slug="pregnancy_test",
        sequence_number=8,
        typical_duration="Single blood test; results same day",
        description=(
            "A blood test (serum beta-hCG) is performed at the clinic to determine whether "
            "implantation has occurred. A positive result is followed by a repeat test a "
            "few days later to confirm rising hCG levels, and then an early ultrasound "
            "scan at around 6–7 weeks. A negative result means the cycle has not resulted "
            "in pregnancy; the clinic will discuss next steps."
        ),
        physical_experience=(
            "The test itself is a routine blood draw. If the result is positive, you may "
            "continue progesterone supplementation until the clinic advises otherwise. "
            "If negative, progesterone is stopped and a natural period usually follows "
            "within a few days."
        ),
        emotional_notes=(
            "This is the most emotionally charged moment of the entire cycle. A positive "
            "result brings joy but also cautious anxiety until a heartbeat is confirmed. "
            "A negative result can bring profound grief, and it is important to allow "
            "yourself time to process this before making decisions about future cycles. "
            "Counselling support is strongly recommended regardless of the outcome."
        ),
        decisions_required=[
            "Attend the blood test at the clinic-scheduled time — do not test early at home",
            "Have a support person with you or available when you receive the result",
            "If positive: schedule the confirmatory hCG test and early scan",
            "If negative: allow yourself time to grieve before discussing next steps with your clinic",
            "Review what, if anything, you would do differently in a subsequent cycle",
        ],
    ),
]

# Index by slug for fast single-stage lookup
_STAGE_BY_SLUG: dict[str, TreatmentStage] = {s.slug: s for s in _STAGES}

_TOTAL_TIMELINE_ESTIMATE = (
    "A single IVF cycle typically takes 4–8 weeks from the start of stimulation to the "
    "pregnancy test result. When you include the initial consultation and any waiting "
    "periods between cycles, the full journey from first appointment to completed cycle "
    "is commonly 2–4 months. Patients who require multiple cycles should plan for "
    "6–18 months or more in total."
)


# ---------------------------------------------------------------------------
# Tool function
# ---------------------------------------------------------------------------


def journey_guide_tool(
    stage: str | None = None,
    profile_context: str | None = None,
) -> JourneyGuideOutput:
    """Returns structured information about IVF treatment stages.

    Args:
        stage: Optional specific stage slug. If None, returns the full journey overview.
               Valid values: "initial_consultation", "ovarian_stimulation",
               "monitoring_scans", "egg_retrieval", "fertilization",
               "embryo_transfer", "two_week_wait", "pregnancy_test"
        profile_context: Optional JSON string of patient profile for tailoring.
                         Expected keys: "diagnosis", "protocol", "age",
                         "prior_treatment_history", "preferences".

    Returns:
        JourneyGuideOutput with stage details, duration, physical experience,
        emotional notes, decisions required, and optional tailored notes.
    """
    # Resolve which stages to return
    if stage is None:
        selected_stages = list(_STAGES)  # all 8, already in order
        timeline = _TOTAL_TIMELINE_ESTIMATE
    else:
        matched = _STAGE_BY_SLUG.get(stage)
        if matched is None:
            # Return all stages if the slug is unrecognised (graceful fallback)
            selected_stages = list(_STAGES)
            timeline = _TOTAL_TIMELINE_ESTIMATE
        else:
            selected_stages = [matched]
            timeline = matched.typical_duration

    # Build tailored notes when profile context is supplied
    tailored_notes: str | None = None
    if profile_context:
        tailored_notes = _build_tailored_notes(profile_context, selected_stages)

    return JourneyGuideOutput(
        stages=selected_stages,
        total_timeline_estimate=timeline,
        tailored_notes=tailored_notes,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_tailored_notes(profile_context: str, stages: list[TreatmentStage]) -> str:
    """Generate profile-specific guidance based on the patient's context.

    Parses the profile JSON and produces a plain-language note that reflects
    how the patient's diagnosis or protocol may affect the stages being shown.
    """
    try:
        profile = json.loads(profile_context)
    except (json.JSONDecodeError, TypeError):
        return (
            "Your profile could not be parsed. Please ensure it is valid JSON. "
            "General IVF journey information is shown above."
        )

    notes: list[str] = []

    diagnosis = (profile.get("diagnosis") or "").strip()
    protocol = (profile.get("protocol") or "").strip()
    age = profile.get("age")
    prior_history = (profile.get("prior_treatment_history") or "").strip()
    preferences = (profile.get("preferences") or "").strip()

    # --- Diagnosis-specific guidance ---
    diagnosis_lower = diagnosis.lower() if diagnosis else ""

    if "pcos" in diagnosis_lower or "polycystic" in diagnosis_lower:
        notes.append(
            "PCOS and your journey: Because PCOS is associated with a higher antral "
            "follicle count, your clinic will likely use a lower starting dose of "
            "gonadotrophins during ovarian stimulation to reduce the risk of ovarian "
            "hyperstimulation syndrome (OHSS). Monitoring scans will be particularly "
            "important to catch any early signs of over-response. A freeze-all strategy "
            "(freezing all embryos and transferring in a subsequent cycle) is often "
            "recommended for patients with PCOS to further reduce OHSS risk."
        )
    elif "diminished ovarian reserve" in diagnosis_lower or "low amh" in diagnosis_lower or "poor responder" in diagnosis_lower:
        notes.append(
            "Diminished ovarian reserve and your journey: With a lower ovarian reserve, "
            "your clinic may use a higher stimulation dose (antagonist or flare protocol) "
            "to maximise the number of eggs retrieved. Fewer eggs are typically expected "
            "compared to the average, so it is important to discuss realistic expectations "
            "with your specialist. Some clinics recommend a 'mini IVF' or natural cycle "
            "IVF approach for poor responders."
        )
    elif "endometriosis" in diagnosis_lower:
        notes.append(
            "Endometriosis and your journey: Endometriosis can affect ovarian reserve and "
            "egg quality. Your clinic may recommend a longer down-regulation phase before "
            "stimulation (long agonist protocol) to suppress endometriosis activity. "
            "Egg retrieval may be more complex if endometriomas are present. Discuss "
            "whether surgical treatment of endometriosis before IVF is appropriate in "
            "your case."
        )
    elif "unexplained" in diagnosis_lower:
        notes.append(
            "Unexplained infertility and your journey: With no identified cause, the "
            "standard IVF protocol is typically used. Your clinic may recommend ICSI "
            "alongside conventional IVF to rule out fertilisation failure as a factor. "
            "Success rates for unexplained infertility are generally comparable to the "
            "average for your age group."
        )
    elif "male factor" in diagnosis_lower or "sperm" in diagnosis_lower:
        notes.append(
            "Male factor infertility and your journey: ICSI (intracytoplasmic sperm "
            "injection) is typically recommended during the fertilisation stage to "
            "maximise fertilisation rates. If sperm count or motility is severely "
            "affected, surgical sperm retrieval (TESA/PESA) may be required on egg "
            "retrieval day — discuss this with your clinic in advance."
        )
    elif diagnosis:
        notes.append(
            f"Your diagnosis ({diagnosis}) may affect specific stages of your journey. "
            "Your fertility specialist will tailor the protocol to your individual "
            "circumstances — please discuss how each stage may differ for you at your "
            "next consultation."
        )

    # --- Protocol-specific guidance ---
    protocol_lower = protocol.lower() if protocol else ""

    if "antagonist" in protocol_lower:
        notes.append(
            "Antagonist protocol: This is the most commonly used protocol today. "
            "Stimulation starts on day 2–3 of your cycle, and a GnRH antagonist "
            "injection is added from around day 5–6 to prevent premature ovulation. "
            "The cycle is shorter than a long agonist protocol (typically 10–12 days "
            "of stimulation) and allows a GnRH agonist trigger, which significantly "
            "reduces OHSS risk."
        )
    elif "long agonist" in protocol_lower or "long protocol" in protocol_lower:
        notes.append(
            "Long agonist (down-regulation) protocol: This protocol begins with a "
            "GnRH agonist nasal spray or injection in the cycle before stimulation, "
            "suppressing your natural hormones before gonadotrophins are started. "
            "The overall cycle is longer (4–6 weeks) but gives the clinic precise "
            "control over timing. It is often preferred for endometriosis or where "
            "previous cycles have had premature LH surges."
        )
    elif "natural" in protocol_lower or "mini ivf" in protocol_lower or "minimal" in protocol_lower:
        notes.append(
            "Natural / minimal stimulation IVF: This approach uses little or no "
            "stimulation medication, aiming to retrieve 1–3 eggs in a natural cycle. "
            "It is gentler on the body and lower cost per cycle, but typically yields "
            "fewer embryos. Multiple cycles may be needed to accumulate embryos for "
            "transfer. It is often considered for poor responders or patients who "
            "prefer to minimise medication."
        )
    elif protocol:
        notes.append(
            f"Your protocol ({protocol}) will shape the timing and medication schedule "
            "across the stimulation and monitoring stages. Your clinic will provide a "
            "detailed calendar — keep this with you throughout the cycle."
        )

    # --- Age-specific guidance ---
    if isinstance(age, int):
        if age >= 40:
            notes.append(
                f"Age consideration (age {age}): Egg quality and quantity naturally "
                "decline with age, which can affect fertilisation rates and embryo "
                "development. Your clinic may recommend preimplantation genetic testing "
                "(PGT-A) to identify chromosomally normal embryos, improving the chance "
                "of a successful transfer. Realistic expectations and open conversations "
                "with your specialist about success rates for your age group are important."
            )
        elif age >= 35:
            notes.append(
                f"Age consideration (age {age}): Fertility begins to decline more "
                "noticeably from the mid-30s. Your clinic will factor your age into "
                "stimulation dosing and may discuss PGT-A as an option. Success rates "
                "remain good in this age group, particularly with good ovarian reserve."
            )

    # --- Prior treatment history ---
    if prior_history:
        notes.append(
            f"Prior treatment history: You have noted '{prior_history}'. Your clinic "
            "will review what worked and what did not in previous cycles to refine your "
            "protocol. If a previous cycle was cancelled due to poor response or OHSS, "
            "discuss how the protocol will be adjusted this time."
        )

    # --- Preferences ---
    if "minimal" in preferences.lower() or "natural" in preferences.lower():
        notes.append(
            "Preference for minimal stimulation: Your preference for a gentler approach "
            "is noted. Discuss natural cycle IVF or minimal stimulation IVF with your "
            "specialist to understand whether this is appropriate given your diagnosis "
            "and ovarian reserve."
        )
    elif preferences:
        notes.append(
            f"Your stated preferences ({preferences}) have been noted. Raise these "
            "directly with your fertility specialist so they can be incorporated into "
            "your treatment plan where clinically appropriate."
        )

    # --- Stage-specific tailoring for single-stage queries ---
    if len(stages) == 1:
        stage_slug = stages[0].slug
        stage_note = _stage_specific_note(stage_slug, diagnosis_lower, protocol_lower)
        if stage_note:
            notes.append(stage_note)

    if not notes:
        notes.append(
            "Your profile has been noted. The journey overview above reflects the "
            "standard IVF process. Your fertility specialist will tailor each stage "
            "to your individual circumstances."
        )

    return "\n\n".join(notes)


def _stage_specific_note(slug: str, diagnosis_lower: str, protocol_lower: str) -> str:
    """Return a brief stage-specific tailored note based on diagnosis/protocol."""
    if slug == "ovarian_stimulation":
        if "pcos" in diagnosis_lower or "polycystic" in diagnosis_lower:
            return (
                "For this stage specifically: your PCOS means the clinic will monitor "
                "you very closely for signs of over-response. Do not adjust your "
                "medication dose without clinic guidance."
            )
        if "diminished ovarian reserve" in diagnosis_lower or "poor responder" in diagnosis_lower:
            return (
                "For this stage specifically: with diminished ovarian reserve, a higher "
                "stimulation dose is typically used. The goal is to recruit as many "
                "follicles as possible while avoiding over-suppression."
            )
    elif slug == "egg_retrieval":
        if "endometriosis" in diagnosis_lower:
            return (
                "For this stage specifically: if you have endometriomas (ovarian cysts "
                "caused by endometriosis), retrieval may be more technically challenging. "
                "Discuss the risks and approach with your surgeon beforehand."
            )
    elif slug == "fertilization":
        if "male factor" in diagnosis_lower or "sperm" in diagnosis_lower:
            return (
                "For this stage specifically: ICSI will be used to inject a single sperm "
                "directly into each mature egg, bypassing the need for sperm to penetrate "
                "the egg naturally. This is standard practice for male factor infertility."
            )
    elif slug == "embryo_transfer":
        if "pcos" in diagnosis_lower or "polycystic" in diagnosis_lower:
            return (
                "For this stage specifically: if a freeze-all strategy was used due to "
                "OHSS risk, your transfer will take place in a subsequent frozen embryo "
                "transfer (FET) cycle rather than immediately after egg retrieval."
            )
    return ""
