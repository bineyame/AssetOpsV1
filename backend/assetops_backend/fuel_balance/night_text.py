"""DIESEL-K5 (`.agent/build-sheet-DIESEL-1.md` §9l.2, ruling DIESEL-1-R3l): the Fuel page's night-mode wording.
Pure, no I/O.

Rules H1-H5 (§8.2); owner 2026-11-07: "'Unexplained fuel', never 'theft'". Every number a viewer reads is formatted
here, never in the browser: litres to one decimal, half-even on the exact `Fraction` (K4a's `finding_text.litres1`);
ticket and dip volumes in whole litres when integral; kWh to one decimal; the fuel and idle rates as stored; times as
Site-local 24 h `HH:MM`; dates as the board's short day ("4 Oct"). The margin and gap lines are K4a's, imported.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

from assetops_backend.actions.verification_rules import parse_exact
from assetops_backend.fuel_balance import finding_text
from assetops_backend.fuel_balance.finding_text import litres1, short_day

NIGHT_LABEL = "Night of {date} · 6 pm to noon"
STATUS = {
    "UNEXPLAINED": "Fuel balance: unexplained fuel",
    "WITHIN_MARGIN": "Fuel balance: accounted for within the margin",
    "BELOW_MATERIALITY": "Fuel balance: a small difference, below the 40 L the check flags",
    "EXCESS": "Fuel balance: more fuel than recorded",
    "NOT_ASSESSED": "Fuel balance: not checked",
}
STATUS_TONE = {"UNEXPLAINED": "amber", "WITHIN_MARGIN": "neutral", "BELOW_MATERIALITY": "neutral",
               "EXCESS": "amber", "NOT_ASSESSED": "neutral"}
FUEL_REASON_WORDS = {  # K4b imports these (amended, §9l.4); §9j.11's literals, with "no-load" made guard-V safe
    "NO_SENSOR_ACCURACY": "no tank sensor accuracy declared",
    "SFC_MISSING": "no generator fuel rate declared",
    "NO_LOAD_RATE_MISSING": "no generator idle fuel rate declared",
    "MISSING_OPENING": "no tank reading at 6 pm",
    "MISSING_CLOSING": "no tank reading at noon",
    "FUEL_LEVEL_CONFLICT": "two different tank readings at the same time",
    "GENERATOR_KWH_UNKNOWN": "generator power readings incomplete",
    "IDLE_SECONDS_UNKNOWN": "generator state readings incomplete",
}
NOT_CHECKED = "Not checked: {why}"
# cards (label, value, note); labels are the existing ones (MiniPerformance.tsx:1417-1444)
OPENING_NOTE = "Tank reading at {hh_mm}"
DELIVERIES_NONE = "None recorded"
DELIVERIES_NOTE_ONE = "1 delivery record"
DELIVERIES_NOTE_MANY = "{n} delivery records"
DELIVERIES_NOTE_NONE = "Absence of record does not prove none occurred"          # v69 :625, verbatim
USE_NOTE = "Modelled: {kwh} kWh × {sfc} L/kWh, 10 % either way"
USE_NOTE_IDLE = "Modelled: {kwh} kWh × {sfc} L/kWh plus {m} min idle at {r} L/h, 10 % either way"
RESIDUAL_NOTE = {"UNEXPLAINED": "Above the 40 L the check flags", "WITHIN_MARGIN": "Zero lies inside this range",
                 "BELOW_MATERIALITY": "Below the 40 L the check flags", "EXCESS": "More fuel than recorded"}
CANNOT_COMPUTE = "Cannot compute"                                                  # v69 :626
UNKNOWN_VALUE = "Unknown"
# bridge rows: (term, label, evidence basis, treatment); the row shows "{label} · {value}"
BRIDGE = (
    ("OPENING", "Opening inventory", "Tank reading at {hh_mm}", "Declared sensor accuracy ±{a} L"),
    ("DELIVERIES", "Plus deliveries", "{deliveries_basis}", "1 % allowance on each ticket"),
    ("USE", "Less generator consumption", "Generator output × declared fuel coefficient",
     "Modelled range, not a fuel-meter reading"),
    ("CLOSING", "Less closing inventory", "Tank reading at {hh_mm}", "Declared sensor accuracy ±{a} L"),
    ("RESIDUAL", "Unexplained residual", "Opening + deliveries − use − closing",
     "Compared with the combined margin; never says why fuel left"),
)
DELIVERIES_BASIS_NONE = "No delivery record"     # else DELIVERIES_NOTE_ONE / _MANY
# records table
RECORD_KIND = {"FUEL_DELIVERY": "Fuel delivery", "TANK_DIP": "Tank dip"}           # K2's labels
RECORD_WHEN = "{hh_mm}, {date}"
RECORDS_EMPTY = "No delivery or tank dip recorded this night"
DIP_CONFLICT = "A tank dip differs from the nearest tank reading by more than the declared accuracy plus 10 L."
DELIVERY_LATE = "A delivery was first recorded after the night could be checked."
# Finding panel on the night page
FINDING_NONE_WITHIN = "No finding: the fuel was accounted for within the margin."
FINDING_NONE = "No finding for this night."
FINDING_NOT_RAISED = "Not available yet · the finding for this night has not been raised"
FUEL_NIGHT_LINK = "Open this night on the Fuel page"
# fuel Finding page and the Site Findings panel
LIFECYCLE = {"SUPPORTED": "Supported by the latest check", "NO_LONGER_SUPPORTED": "No longer supported"}
VERSION_ROW = "Version {n} · {lifecycle} · {hh_mm}, {date}"
FUEL_CHECKS_ROW = "{title} · {date} · about {lo}–{hi} L"

#: Every K5 literal (the local wording guard and `test_out_b2_vocabulary.py` scan these).
LITERALS = (NIGHT_LABEL, *STATUS.values(), *FUEL_REASON_WORDS.values(), NOT_CHECKED, OPENING_NOTE, DELIVERIES_NONE,
            DELIVERIES_NOTE_ONE, DELIVERIES_NOTE_MANY, DELIVERIES_NOTE_NONE, USE_NOTE, USE_NOTE_IDLE,
            *RESIDUAL_NOTE.values(), CANNOT_COMPUTE, UNKNOWN_VALUE, *(text for row in BRIDGE for text in row[1:]),
            DELIVERIES_BASIS_NONE, *RECORD_KIND.values(), RECORD_WHEN, RECORDS_EMPTY, DIP_CONFLICT, DELIVERY_LATE,
            FINDING_NONE_WITHIN, FINDING_NONE, FINDING_NOT_RAISED, FUEL_NIGHT_LINK, *LIFECYCLE.values(), VERSION_ROW,
            FUEL_CHECKS_ROW)

#: The existing hour-mode card and bar labels (`MiniPerformance.tsx:1417-1446`, `:1460-1464`), reused verbatim.
CARD_LABELS = (("OPENING", "Opening evidence"), ("DELIVERIES", "Recorded deliveries"),
               ("USE", "Modelled expected use"), ("RESIDUAL", "Residual"))
BAR_LABELS = (("opening", "Opening tank"), ("deliveries", "+ Deliveries"), ("use", "− Modelled generator use"),
              ("closing", "− Closing tank"), ("residual", "= Unexplained"))


# --- formatting ------------------------------------------------------------------------------------------------


def _exact(value: Any) -> Fraction | None:
    return value if isinstance(value, Fraction) else parse_exact(value)


def litres(value: Any) -> str | None:
    """A computed litre amount: one decimal, half-even on the exact value (K4a's rule)."""
    f = _exact(value)
    return None if f is None else litres1(f)


def volume(value: Any) -> str | None:
    """A ticket or dip volume: whole litres when integral, else one decimal half-even."""
    f = _exact(value)
    if f is None:
        return None
    return str(f.numerator) if f.denominator == 1 else litres1(f)


def accuracy(value: Any) -> str | None:
    """`{a}`: the declared accuracy to 0.1 L, without a trailing ".0" for whole litres ("10")."""
    f = _exact(value)
    if f is None:
        return None
    text = litres1(f)
    return text[:-2] if text.endswith(".0") else text


def kwh1(value: Any) -> str | None:
    f = _exact(value)
    return None if f is None else f"{Decimal(round(f * 10)) / 10:.1f}"


def band(low: Any, high: Any) -> str | None:
    lo, hi = litres(low), litres(high)
    return None if lo is None or hi is None else f"{lo}–{hi} L"


def hh_mm(at: datetime | str | None, tz: str) -> str | None:
    if at is None:
        return None
    instant = datetime.fromisoformat(at.replace("Z", "+00:00")) if isinstance(at, str) else at
    return instant.astimezone(ZoneInfo(tz)).strftime("%H:%M")


def local_day(at: datetime, tz: str) -> date:
    return at.astimezone(ZoneInfo(tz)).date()


def night_label(night_date: date) -> str:
    return NIGHT_LABEL.format(date=short_day(night_date))


def not_checked(reason: str | None) -> str:
    return NOT_CHECKED.format(why=FUEL_REASON_WORDS.get(reason or "", UNKNOWN_VALUE))


def _float(value: Any) -> float | None:
    f = _exact(value)
    return None if f is None else float(f)


# --- the night view ----------------------------------------------------------------------------------------------


def counted_deliveries(window: Any, records: Sequence[Any]) -> list[Any]:
    """The delivery records the stored check counted (their roots are in the window's `record_ids`)."""
    roots = {root for root, _ in window.record_ids}
    return [r for r in records if r.kind == "FUEL_DELIVERY" and r.root_id in roots]


def record_rows(records: Iterable[Any], tz: str) -> list[dict[str, Any]]:
    return [{"code": r.code, "kind": RECORD_KIND.get(r.kind, r.kind),
             "when": RECORD_WHEN.format(hh_mm=hh_mm(r.occurred_at, tz), date=short_day(local_day(r.occurred_at, tz))),
             "volume": f"{volume(r.quantity_l)} L", "occurred_at": r.occurred_at.isoformat()}
            for r in sorted(records, key=lambda r: (r.occurred_at, r.root_id))]


def night_view(window: Any, records: Sequence[Any], tz: str) -> dict[str, Any]:
    """The night body's text (status, cards, bars, bridge, notes, records) from one stored window and the K2 fuel
    records occurring in it. Every visible number is a string; `value_l` only scales a bar."""
    t: Mapping[str, Any] = window.terms or {}
    state = window.state
    deliveries = counted_deliveries(window, records)
    n = len(deliveries)
    a = accuracy(t.get("accuracy_l"))
    opening, closing = litres(t.get("opening_l")), litres(t.get("closing_l"))
    open_at, close_at = hh_mm(t.get("opening_at"), tz), hh_mm(t.get("closing_at"), tz)
    d_value = volume(t.get("deliveries_l"))
    d_text = DELIVERIES_NONE if n == 0 else f"{d_value} L"
    use = band(t.get("use_low"), t.get("use_high"))
    residual = band(window.residual_low, window.residual_high)

    if use is None:
        use_note = None
    else:
        idle = int(t.get("idle_seconds") or 0)
        sfc, kwh = t.get("sfc_l_per_kwh"), kwh1(t.get("generator_kwh"))
        use_note = (USE_NOTE_IDLE.format(kwh=kwh, sfc=sfc, m=idle // 60, r=t.get("no_load_l_per_h")) if idle > 0
                    else USE_NOTE.format(kwh=kwh, sfc=sfc))
    residual_note = not_checked(window.reason) if state == "NOT_ASSESSED" else RESIDUAL_NOTE.get(state)
    deliveries_note = (DELIVERIES_NOTE_NONE if n == 0 else DELIVERIES_NOTE_ONE if n == 1
                       else DELIVERIES_NOTE_MANY.format(n=n))
    values = {
        "OPENING": (f"{opening} L" if opening else UNKNOWN_VALUE,
                    None if open_at is None else OPENING_NOTE.format(hh_mm=open_at)),
        "DELIVERIES": (d_text, deliveries_note),
        "USE": (use or UNKNOWN_VALUE, use_note),
        "RESIDUAL": (residual or CANNOT_COMPUTE, residual_note),
    }
    numeric = {"OPENING": opening is not None, "DELIVERIES": n > 0, "USE": use is not None,
               "RESIDUAL": residual is not None}
    cards = [{"key": key, "label": label, "value": values[key][0], "note": values[key][1], "word": not numeric[key]}
             for key, label in CARD_LABELS]

    closing_text = f"{closing} L" if closing else UNKNOWN_VALUE
    residual_high = _float(window.residual_high)
    bar_values = {
        "opening": (_float(t.get("opening_l")), values["OPENING"][0]),
        "deliveries": (_float(t.get("deliveries_l")) if n else None, d_text),
        "use": (_float(t.get("use_high")) if use else None, values["USE"][0]),
        "closing": (_float(t.get("closing_l")), closing_text),
        "residual": (None if residual is None else max(residual_high or 0.0, 0.0), values["RESIDUAL"][0]),
    }
    bars = [{"key": key, "label": label, "value_l": bar_values[key][0], "text": bar_values[key][1]}
            for key, label in BAR_LABELS]

    bridge_value = {"OPENING": values["OPENING"][0], "DELIVERIES": d_text, "USE": values["USE"][0],
                    "CLOSING": closing_text, "RESIDUAL": values["RESIDUAL"][0]}
    deliveries_basis = (DELIVERIES_BASIS_NONE if n == 0 else DELIVERIES_NOTE_ONE if n == 1
                        else DELIVERIES_NOTE_MANY.format(n=n))
    at = {"OPENING": open_at, "CLOSING": close_at}
    counts = {"OPENING": int(opening is not None), "DELIVERIES": n, "USE": len(window.evidence_ids),
              "CLOSING": int(closing is not None), "RESIDUAL": len(window.evidence_ids)}
    bridge = []
    for term, label, basis, treatment in BRIDGE:
        if term in at:
            basis_text = UNKNOWN_VALUE if at[term] is None else basis.format(hh_mm=at[term])
            treatment_text = UNKNOWN_VALUE if a is None else treatment.format(a=a)
        elif term == "DELIVERIES":
            basis_text, treatment_text = basis.format(deliveries_basis=deliveries_basis), treatment
        else:
            basis_text, treatment_text = basis, treatment
        bridge.append({"term": term, "label": label, "value": bridge_value[term], "basis": basis_text,
                       "treatment": treatment_text, "evidence_count": counts[term]})

    notes = []
    if window.gap_minutes > 0:
        notes.append(finding_text.gap_line(window.gap_spans, tz))
    if "DIP_SENSOR_CONFLICT" in window.limitations:
        notes.append(DIP_CONFLICT)
    if "DELIVERY_RECORDED_LATE" in window.limitations:
        notes.append(DELIVERY_LATE)
    if state == "NOT_ASSESSED":
        notes.append(not_checked(window.reason))

    return {"night_date": window.night_date.isoformat(), "label": night_label(window.night_date), "state": state,
            "status": STATUS.get(state, STATUS["NOT_ASSESSED"]), "tone": STATUS_TONE.get(state, "neutral"),
            "revision": window.revision, "window_start": window.window_start.isoformat(),
            "window_end": window.window_end.isoformat(), "cards": cards, "bars": bars, "bridge": bridge,
            "notes": notes, "margin": None if a is None else finding_text.margin_line(t.get("accuracy_l")),
            "records": record_rows(records, tz)}


def night_summary(window: Any) -> dict[str, Any]:
    """One row of the nights list."""
    return {"night_date": window.night_date.isoformat(), "label": night_label(window.night_date),
            "state": window.state, "status": STATUS.get(window.state, STATUS["NOT_ASSESSED"]),
            "tone": STATUS_TONE.get(window.state, "neutral"), "revision": window.revision}


def finding_note(state: str) -> str:
    """The night page's Finding panel when no fuel Finding cites this night."""
    if state == "WITHIN_MARGIN":
        return FINDING_NONE_WITHIN
    if state == "UNEXPLAINED":
        return FINDING_NOT_RAISED
    return FINDING_NONE


def fuel_checks_row(ff: Any) -> str:
    w = ff.window
    return FUEL_CHECKS_ROW.format(title=finding_text.TITLE, date=short_day(w.night_date),
                                  lo=litres(w.residual_low) or UNKNOWN_VALUE, hi=litres(w.residual_high) or UNKNOWN_VALUE)


def version_row(revision_no: int, lifecycle: str, created_at: datetime, tz: str) -> str:
    return VERSION_ROW.format(n=revision_no, lifecycle=LIFECYCLE.get(lifecycle, lifecycle),
                              hh_mm=hh_mm(created_at, tz), date=short_day(local_day(created_at, tz)))
