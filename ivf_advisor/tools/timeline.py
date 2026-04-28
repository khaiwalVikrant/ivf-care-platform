"""IVF treatment timeline tool — generates a personalised cycle schedule."""

from __future__ import annotations

from datetime import date, timedelta

from ivf_advisor.models import TimelineEvent, TimelineOutput

_CLINIC_ADJUSTMENT_NOTE = (
    "All dates are estimates based on a standard protocol. Your clinic may adjust "
    "the schedule based on your scan results, hormone levels, and individual response "
    "to stimulation. Always follow your clinic's specific instructions."
)

# ---------------------------------------------------------------------------
# Protocol event definitions
# Each entry: (day_offset_from_day1, event_name, description)
# day_offset 0 = Day 1 (baseline scan day)
# ---------------------------------------------------------------------------

_ANTAGONIST_FRESH_EVENTS: list[tuple[int, str, str]] = [
    (0,  "Baseline scan",
     "Transvaginal ultrasound to assess antral follicle count and confirm readiness to start stimulation."),
    (1,  "Stimulation injections start",
     "Daily FSH/LH injections begin to stimulate follicle growth. Your nurse will demonstrate the injection technique."),
    (4,  "Monitoring scan 1",
     "Ultrasound to assess follicle development and adjust medication dose if needed."),
    (7,  "Monitoring scan 2",
     "Further ultrasound monitoring; blood oestradiol levels may also be checked."),
    (9,  "Monitoring scan 3 + trigger decision",
     "Final monitoring scan. If lead follicles are ≥18 mm, the trigger injection will be scheduled."),
    (10, "Trigger injection (evening)",
     "hCG or GnRH agonist trigger injection given at a precise time — typically 36 hours before egg retrieval."),
    (12, "Egg retrieval",
     "Transvaginal ultrasound-guided egg collection under sedation or light anaesthesia."),
    (13, "Fertilisation result call",
     "The embryology team will call to confirm how many eggs fertilised normally."),
    (17, "Embryo transfer (day 5 blastocyst)",
     "The best-quality blastocyst(s) are transferred into the uterus. A short rest period follows."),
    (31, "Pregnancy test (beta hCG)",
     "Blood test to measure hCG levels and confirm whether implantation has occurred."),
]

_LONG_PROTOCOL_DOWNREGULATION: list[tuple[int, str, str]] = [
    (-14, "Downregulation starts",
      "GnRH agonist (e.g. Buserelin nasal spray or Lupron injection) begins to suppress natural hormone production."),
    (-7,  "Downregulation check scan",
      "Ultrasound and blood test to confirm successful pituitary suppression before stimulation begins."),
]

_FET_EVENTS: list[tuple[int, str, str]] = [
    (0,  "FET preparation starts",
     "Endometrial preparation begins — typically with oestrogen tablets or patches to thicken the uterine lining."),
    (7,  "Lining check scan",
     "Ultrasound to measure endometrial thickness. A lining of ≥7 mm is generally required before progesterone is added."),
    (10, "Progesterone support starts",
     "Progesterone pessaries or injections begin to prepare the endometrium for embryo transfer."),
    (14, "Frozen embryo transfer (FET)",
     "The thawed blastocyst is transferred into the uterus. The procedure is usually quick and painless."),
    (28, "Pregnancy test (beta hCG)",
     "Blood test to measure hCG levels and confirm whether implantation has occurred."),
]


# ---------------------------------------------------------------------------
# Date formatting
# ---------------------------------------------------------------------------


def _format_date(d: date) -> str:
    """Return a human-readable date string, e.g. 'Monday, 5 May 2025'."""
    return d.strftime("%A, %-d %B %Y")


# ---------------------------------------------------------------------------
# Public tool function
# ---------------------------------------------------------------------------


def timeline_tool(
    start_date: str,
    protocol: str = "antagonist",
    transfer_type: str = "fresh",
) -> TimelineOutput:
    """Generate an IVF treatment timeline from a given start date.

    Args:
        start_date: ISO 8601 date string (YYYY-MM-DD) for Day 1 (baseline scan).
        protocol: "antagonist" (default) or "long" (long GnRH agonist protocol).
        transfer_type: "fresh" (default) or "frozen" (FET cycle).

    Returns:
        TimelineOutput with a list of dated events, protocol metadata, and a
        clinic adjustment note.

    Raises:
        ValueError: If start_date is not a valid ISO 8601 date string.
    """
    try:
        day1 = date.fromisoformat(start_date)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid start_date '{start_date}'. Expected ISO 8601 format: YYYY-MM-DD."
        ) from exc

    protocol_lower = protocol.lower().strip()
    transfer_lower = transfer_type.lower().strip()

    events: list[TimelineEvent] = []

    if transfer_lower == "frozen":
        # FET cycle: endometrial prep + frozen transfer
        for offset, name, description in _FET_EVENTS:
            event_date = day1 + timedelta(days=offset)
            events.append(TimelineEvent(
                date=_format_date(event_date),
                day_number=offset + 1,
                event_name=name,
                description=description,
            ))
        protocol_label = "FET (frozen embryo transfer)"
    else:
        # Fresh transfer cycle
        base_events = list(_ANTAGONIST_FRESH_EVENTS)

        if protocol_lower == "long":
            # Prepend downregulation phase (negative offsets relative to day1)
            downreg_events = list(_LONG_PROTOCOL_DOWNREGULATION)
            all_raw = downreg_events + base_events
            protocol_label = "Long GnRH agonist protocol (fresh transfer)"
        else:
            all_raw = base_events
            protocol_label = "Antagonist protocol (fresh transfer)"

        for offset, name, description in all_raw:
            event_date = day1 + timedelta(days=offset)
            # day_number: offset relative to day1 + 1 (so day1 = Day 1)
            events.append(TimelineEvent(
                date=_format_date(event_date),
                day_number=offset + 1,
                event_name=name,
                description=description,
            ))

    return TimelineOutput(
        events=events,
        protocol=protocol_label,
        transfer_type=transfer_lower,
        clinic_adjustment_note=_CLINIC_ADJUSTMENT_NOTE,
    )
