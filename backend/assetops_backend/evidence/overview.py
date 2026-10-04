"""The mini-grid Site Overview read model: accepted evidence only (T027 phase 2).

AC11, AC22 and the Overview parts of AC10/12/13/14/15/19. Every value here is
computed from accepted records in the selected window, beside the Site >
Evidence read model and under the same dependency guard: no stage, world,
LabProjection, observation, private trace or scenario expectation.

What it serves, and what it never does:

- One card per domain the backend measures (`OVERVIEW_DOMAIN_SIGNALS`). Which
  of them render, and in which order, is the frontend presentation profile's;
  card **state** is this module's. With no analytic (none exists before the
  dispatch Finding), every card's assessment is `NO_ASSESSMENT` - never
  `UNKNOWN`, which is reserved for an assessment that exists but cannot
  conclude.
- Metrics are measured values with units. Energy and running time are summed
  over measured intervals only (interval mean x interval length); time between
  measured intervals is not counted, and the measured hours are stated beside
  the value. A state-at-instant value is shown at its own source time. No sample
  is carried forward.
- A needed signal with no record a metric can use in the window is a coverage
  gap: no record, no GOOD record, no interval span (interval signals), or only
  overlapping records. A metric that reads it has no value, and the card names
  the gap with its reason.
- Fuel is tank level only: no consumption or loss is inferred.
- The timeline (demand, PV, generator, SOC) is context, not a status source.
"""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from typing import Any, Callable

from assetops_backend.evidence.models import AcceptedRecord
from assetops_backend.evidence.ports import EvidenceStore
from assetops_backend.evidence.read_model import (
    OVERVIEW_DOMAIN_SIGNALS,
    default_window,
    in_window,
)
from assetops_backend.sites.models import SiteRecord

SignalKey = tuple[str, str]

NO_ASSESSMENT = {
    "status": "NO_ASSESSMENT",
    "label": "No assessment yet",
    "reason": (
        "Nothing assesses this area of the site yet. The metrics are measured "
        "values, not a judgement of how the site is operating."
    ),
}
FINDINGS_STATEMENT = (
    "Nothing has assessed this site yet, so no Finding exists. This is not "
    "a statement that the site is or is not operating well."
)
INTERVAL_STATEMENT = (
    "Energy and operating time are summed over measured intervals only (interval "
    "mean multiplied by interval length). Time between measured intervals is not "
    "counted and no sample is carried forward. Overlapping records (distinct "
    "records at one interval or instant) are listed in Evidence and used by no "
    "metric."
)
TIMELINE_STATEMENT = (
    "The timeline places accepted measurements on the window's time axis. It is "
    "context, not a status: a gap is a time with no accepted measurement."
)

SERVICE_FEEDERS: tuple[tuple[str, str], ...] = (
    ("residential-meter", "Residential feeder"),
    ("clinic-meter", "Clinic feeder"),
    ("mill-meter", "Mill feeder"),
)
METER = "active-power"
GENERATOR_STATUS: SignalKey = ("generator-controller", "status")
GENERATOR_POWER: SignalKey = ("generator-controller", "ac-power")
SOC: SignalKey = ("battery-pcs-controller", "state-of-charge")
FUEL: SignalKey = ("fuel-level-sensor", "fuel-level")
PV: SignalKey = ("pv-inverter-controller", "ac-power")

_FMT = "%Y-%m-%dT%H:%M:%SZ"


def _seconds(start: str, end: str) -> int:
    return int((datetime.strptime(end, _FMT) - datetime.strptime(start, _FMT)).total_seconds())


def _fmt(value: Fraction, places: int) -> str:
    exact = Decimal(value.numerator) / Decimal(value.denominator)
    return str(exact.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def _plain(value: str | None) -> str | None:
    """Exact decimal or fraction text as decimal text to two places, trimmed."""
    if value is None:
        return None
    try:
        exact = Fraction(value)
    except ValueError:
        return value
    text = _fmt(exact, 2)
    return text.rstrip("0").rstrip(".") if "." in text else text


def _good(records: list[AcceptedRecord]) -> list[AcceptedRecord]:
    return [r for r in records if r.quality == "GOOD" and r.normalized_value is not None]


def _unique(records: list[AcceptedRecord], key) -> list[AcceptedRecord]:
    """Records whose key no other record shares (AC9).

    Distinct records at one span or instant are overlapping evidence. They are
    kept and shown in Site > Evidence, but a computed metric uses neither, so
    nothing is summed twice and none silently replaces another.
    """
    counts: dict[Any, int] = {}
    for record in records:
        counts[key(record)] = counts.get(key(record), 0) + 1
    return [r for r in records if counts[key(r)] == 1]


def _spanned(records: list[AcceptedRecord]) -> list[AcceptedRecord]:
    """GOOD records with a positive interval span (start before end)."""
    return [
        r for r in _good(records)
        if r.interval_start is not None
        and r.interval_end is not None
        and _seconds(r.interval_start, r.interval_end) > 0
    ]


def _intervals(records: list[AcceptedRecord]) -> list[AcceptedRecord]:
    return _unique(_spanned(records), lambda r: (r.interval_start, r.interval_end))


def _instants(records: list[AcceptedRecord]) -> list[AcceptedRecord]:
    return _unique(_good(records), lambda r: r.source_time)


def _link(record: AcceptedRecord) -> dict[str, str]:
    return {
        "device_id": record.device_id,
        "signal_id": record.signal_id,
        "message_id": record.message_id,
    }


def _latest(records: list[AcceptedRecord]) -> AcceptedRecord:
    return max(records, key=lambda r: (r.source_time, r.message_id))


def _hours(seconds: int) -> Fraction:
    return Fraction(seconds, 3600)


def _gap_text(key: SignalKey) -> str:
    return f"{key[0]}/{key[1]}"


#: Signals whose metrics read interval means (energy, running time, peak). Every
#: other Overview signal is read as a state at an instant.
INTERVAL_SIGNALS: frozenset[SignalKey] = frozenset(
    {(device, METER) for device, _ in SERVICE_FEEDERS} | {GENERATOR_POWER, PV}
)

#: Why a needed signal is a gap, by coverage status. Review F1: coverage is
#: decided from the records a metric can actually use, not from "any GOOD".
GAP_REASONS = {
    "NOT_REPORTED": "reported no accepted record in this window",
    "NO_GOOD_RECORD": "has no GOOD accepted record in this window",
    "NO_INTERVAL_SPAN": "has GOOD records in this window, none with an interval span",
    "OVERLAPPING_ONLY": (
        "has GOOD records in this window that all overlap; overlapping records "
        "are used by no metric"
    ),
    # Review R2: an interval signal whose spanned records all overlap and whose
    # other GOOD records have no span. Neither half alone is literally true.
    "OVERLAPPING_OR_NO_SPAN": (
        "has GOOD records in this window, none usable: those with an interval "
        "span overlap, and the rest have no interval span"
    ),
}


def _metric(
    metric_id: str,
    label: str,
    unit: str,
    *,
    value: str | None = None,
    at: str | None = None,
    basis: str,
    evidence: list[dict[str, str]] | None = None,
    missing: list[str] | None = None,
    window_note: str | None = None,
) -> dict[str, Any]:
    gaps = missing or []
    return {
        "metric_id": metric_id,
        "label": label,
        "unit": unit,
        "value": None if gaps else value,
        "at": None if gaps else at,
        "basis": basis,
        "window_note": None if gaps else window_note,
        "evidence": [] if gaps else (evidence or []),
        "unavailable_because": None if not gaps else "; ".join(gaps) + ".",
    }


class _Window:
    """Accepted records in the window, grouped by signal."""

    def __init__(self, records: list[AcceptedRecord], seconds: int | None = None) -> None:
        self.records = records
        #: The window's length, or None when there is no window.
        self.seconds = seconds
        self.by_signal: dict[SignalKey, list[AcceptedRecord]] = {}
        for record in records:
            self.by_signal.setdefault((record.device_id, record.signal_id), []).append(record)

    def of(self, key: SignalKey) -> list[AcceptedRecord]:
        return sorted(self.by_signal.get(key, []), key=lambda r: (r.source_time, r.message_id))

    def usable(self, key: SignalKey) -> list[AcceptedRecord]:
        """The records a metric of this signal actually reads."""
        records = self.of(key)
        return _intervals(records) if key in INTERVAL_SIGNALS else _instants(records)

    def status(self, key: SignalKey) -> str:
        records = self.of(key)
        if not records:
            return "NOT_REPORTED"
        if not _good(records):
            return "NO_GOOD_RECORD"
        if self.usable(key):
            return "REPORTED"
        if key in INTERVAL_SIGNALS:
            spanned = _spanned(records)
            if not spanned:
                return "NO_INTERVAL_SPAN"
            if len(spanned) < len(_good(records)):
                return "OVERLAPPING_OR_NO_SPAN"
        return "OVERLAPPING_ONLY"

    def reason(self, key: SignalKey) -> str:
        return f"{_gap_text(key)} {GAP_REASONS[self.status(key)]}"

    def uncovered(self, *keys: SignalKey) -> list[str]:
        """A named reason for each key no metric can read; empty when covered."""
        return [self.reason(key) for key in keys if not self.usable(key)]

    def window_note(self, measured_seconds: list[int]) -> str | None:
        if self.seconds is None or not measured_seconds:
            return None
        low, high = min(measured_seconds), max(measured_seconds)
        span = (
            f"{_fmt(_hours(low), 2)} h"
            if low == high
            else f"{_fmt(_hours(low), 2)} to {_fmt(_hours(high), 2)} h"
        )
        return f"{span} of the {_fmt(_hours(self.seconds), 2)} h window measured"


def _interval_energy(records: list[AcceptedRecord]) -> tuple[Fraction, int]:
    energy = Fraction(0)
    seconds = 0
    for record in _intervals(records):
        span = _seconds(record.interval_start or "", record.interval_end or "")
        energy += Fraction(record.normalized_value or "0") * _hours(span)
        seconds += span
    return energy, seconds


def _interval_link(records: list[AcceptedRecord]) -> list[dict[str, str]]:
    measured = _intervals(records)
    return [_link(_latest(measured))] if measured else []


def _service(window: _Window) -> list[dict[str, Any]]:
    keys = [(device, METER) for device, _ in SERVICE_FEEDERS]
    missing = window.uncovered(*keys)
    total = Fraction(0)
    links: list[dict[str, str]] = []
    feeder_metrics = []
    hours_text = []
    measured: list[int] = []
    for (device, label), key in zip(SERVICE_FEEDERS, keys):
        energy, seconds = _interval_energy(window.of(key))
        measured.append(seconds)
        total += energy
        links += _interval_link(window.of(key))
        hours_text.append(f"{label.lower()} {_fmt(_hours(seconds), 2)} h")
        feeder_metrics.append(
            _metric(
                f"{device}-energy",
                f"{label} energy",
                "kWh",
                value=_fmt(energy, 1),
                basis=f"Measured intervals cover {_fmt(_hours(seconds), 2)} h.",
                evidence=_interval_link(window.of(key)),
                missing=window.uncovered(key),
                window_note=window.window_note([seconds]),
            )
        )
    served = _metric(
        "served-energy",
        "Served energy, measured intervals",
        "kWh",
        value=_fmt(total, 1),
        basis=(
            "Sum of the three feeder meters over their measured intervals ("
            + ", ".join(hours_text) + ")."
        ),
        evidence=links,
        missing=missing,
        window_note=window.window_note(measured),
    )
    return [served, *feeder_metrics]


def _dispatch(window: _Window) -> list[dict[str, Any]]:
    power = window.of(GENERATOR_POWER)
    measured = _intervals(power)
    running = [r for r in measured if Fraction(r.normalized_value or "0") > 0]
    running_seconds = sum(
        _seconds(r.interval_start or "", r.interval_end or "") for r in running
    )
    measured_seconds = sum(
        _seconds(r.interval_start or "", r.interval_end or "") for r in measured
    )
    energy, _ = _interval_energy(power)
    statuses = _instants(window.of(GENERATOR_STATUS))
    running_status = [r for r in statuses if r.normalized_value == "RUNNING"]
    status_links = [_link(_latest(running_status or statuses))] if statuses else []
    return [
        _metric(
            "generator-runtime",
            "Generator operating time, measured intervals",
            "h",
            value=_fmt(_hours(running_seconds), 2),
            basis=(
                "Measured intervals with generator output above zero, out of "
                f"{_fmt(_hours(measured_seconds), 2)} h of measured intervals."
            ),
            evidence=[_link(_latest(running))] if running else _interval_link(power),
            missing=window.uncovered(GENERATOR_POWER),
            window_note=window.window_note([measured_seconds]),
        ),
        _metric(
            "generator-energy",
            "Generator energy, measured intervals",
            "kWh",
            value=_fmt(energy, 1),
            basis=f"Over {_fmt(_hours(measured_seconds), 2)} h of measured intervals.",
            evidence=_interval_link(power),
            missing=window.uncovered(GENERATOR_POWER),
            window_note=window.window_note([measured_seconds]),
        ),
        _metric(
            "generator-status-running",
            "Status records showing the generator operating",
            "samples",
            value=f"{len(running_status)} of {len(statuses)}",
            basis="Instantaneous status samples; nothing between samples is inferred.",
            evidence=status_links,
            missing=window.uncovered(GENERATOR_STATUS),
        ),
    ]


def _instant_metrics(
    window: _Window,
    key: SignalKey,
    prefix: str,
    label: str,
    unit: str,
    with_range: bool,
) -> list[dict[str, Any]]:
    good = _instants(window.of(key))
    missing = window.uncovered(key)
    latest = _latest(good) if good else None
    metrics = [
        _metric(
            f"{prefix}-latest",
            f"Latest {label}",
            unit,
            value=None if latest is None else _plain(latest.normalized_value),
            at=None if latest is None else latest.source_time,
            basis="The last GOOD sample in the window, at its own source time.",
            evidence=[] if latest is None else [_link(latest)],
            missing=missing,
        )
    ]
    if with_range:
        for metric_id, name, pick in (
            ("min", "Lowest", min),
            ("max", "Highest", max),
        ):
            chosen = (
                pick(good, key=lambda r: (Fraction(r.normalized_value or "0"), r.source_time))
                if good
                else None
            )
            metrics.append(
                _metric(
                    f"{prefix}-{metric_id}",
                    f"{name} {label}",
                    unit,
                    value=None if chosen is None else _plain(chosen.normalized_value),
                    at=None if chosen is None else chosen.source_time,
                    basis=f"Over {len(good)} GOOD samples in the window.",
                    evidence=[] if chosen is None else [_link(chosen)],
                    missing=missing,
                )
            )
    return metrics


def _battery(window: _Window) -> list[dict[str, Any]]:
    return _instant_metrics(window, SOC, "soc", "battery charge", "%", True)


def _fuel(window: _Window) -> list[dict[str, Any]]:
    # Tank level only: no consumption or loss is inferred from two levels.
    return _instant_metrics(window, FUEL, "fuel-level", "tank level", "L", False)


def _renewable(window: _Window) -> list[dict[str, Any]]:
    records = window.of(PV)
    energy, seconds = _interval_energy(records)
    measured = _intervals(records)
    peak = (
        max(measured, key=lambda r: (Fraction(r.normalized_value or "0"), r.source_time))
        if measured
        else None
    )
    return [
        _metric(
            "pv-energy",
            "Solar energy, measured intervals",
            "kWh",
            value=_fmt(energy, 1),
            basis=f"Solar inverter output over {_fmt(_hours(seconds), 2)} h of measured intervals.",
            evidence=_interval_link(records),
            missing=window.uncovered(PV),
            window_note=window.window_note([seconds]),
        ),
        _metric(
            "pv-peak",
            "Highest interval mean solar output",
            "kW",
            value=None if peak is None else _plain(peak.normalized_value),
            at=None if peak is None else peak.source_time,
            basis="The largest interval mean among measured intervals.",
            evidence=[] if peak is None else [_link(peak)],
            missing=window.uncovered(PV),
        ),
    ]


#: Each backend domain's metric computation. The domains themselves, and the
#: signals each reads, are `OVERVIEW_DOMAIN_SIGNALS`; a test pins these keys
#: equal to it.
DOMAIN_METRICS: dict[str, Callable[[_Window], list[dict[str, Any]]]] = {
    "Service": _service,
    "Dispatch": _dispatch,
    "Battery": _battery,
    "Fuel": _fuel,
    "Renewable": _renewable,
}


def _coverage_row(window: _Window, key: SignalKey) -> dict[str, Any]:
    records = window.of(key)
    good = _good(records)
    return {
        "device_id": key[0],
        "signal_id": key[1],
        "status": window.status(key),
        "records": len(records),
        "good": len(good),
        "usable": len(window.usable(key)),
        "unavailable": sum(1 for r in records if r.quality == "UNAVAILABLE"),
        "last_source_time": records[-1].source_time if records else None,
    }


def _timeline(window: _Window) -> list[dict[str, Any]]:
    def interval_points(records: list[AcceptedRecord]) -> list[dict[str, Any]]:
        return [
            {
                "start": r.interval_start,
                "end": r.interval_end,
                "value": _plain(r.normalized_value),
                "message_id": r.message_id,
            }
            for r in _intervals(records)
        ]

    feeders = [
        {(r.interval_start, r.interval_end): r for r in _intervals(window.of((device, METER)))}
        for device, _ in SERVICE_FEEDERS
    ]
    spans = sorted(set.intersection(*(set(f) for f in feeders))) if feeders else []
    demand = [
        {
            "start": start,
            "end": end,
            "value": _plain(str(sum(Fraction(f[(start, end)].normalized_value or "0") for f in feeders))),
            "message_id": None,
        }
        for start, end in spans
    ]
    soc = [
        {"at": r.source_time, "value": _plain(r.normalized_value), "message_id": r.message_id}
        for r in _instants(window.of(SOC))
    ]
    return [
        {
            "series_id": "demand",
            "label": "Demand (three feeders)",
            "unit": "kW",
            "kind": "INTERVAL_MEAN",
            "basis": "Summed only where all three feeders measured the same interval.",
            "points": demand,
        },
        {
            "series_id": "pv",
            "label": "Solar output",
            "unit": "kW",
            "kind": "INTERVAL_MEAN",
            "basis": "Solar inverter interval means.",
            "points": interval_points(window.of(PV)),
        },
        {
            "series_id": "generator",
            "label": "Generator output",
            "unit": "kW",
            "kind": "INTERVAL_MEAN",
            "basis": "Generator controller interval means.",
            "points": interval_points(window.of(GENERATOR_POWER)),
        },
        {
            "series_id": "soc",
            "label": "Battery charge",
            "unit": "%",
            "kind": "STATE_AT_INSTANT",
            "basis": "Instantaneous samples at their own source times.",
            "points": soc,
        },
    ]


#: Supplies analytic assessments for the Overview (T028): `(site, window_start,
#: window_end) -> {"cards": {domain_id: assessment}, "findings": [...]}`. The
#: composition root passes the analytics service's reader in; this package
#: never imports an analytic. A domain it does not name keeps `NO_ASSESSMENT`.
CardAssessments = Callable[[SiteRecord, "str | None", "str | None"], dict[str, Any]]

FINDINGS_PRESENT_STATEMENT = (
    "Findings raised for this window. Each links to its assessed period; the "
    "Overview does not recompute it."
)


NO_FINDINGS_STATEMENT = (
    "The site was assessed for this window and no Finding was raised. This is not "
    "a statement that the site is operating well."
)


class OverviewReadModel:
    def __init__(self, store: EvidenceStore, card_assessments: CardAssessments | None = None) -> None:
        self._store = store
        self._card_assessments = card_assessments

    def site_overview(
        self,
        site: SiteRecord,
        window_start: str | None = None,
        window_end: str | None = None,
    ) -> dict[str, Any]:
        evidence = self._store.load_site(site.site_id)
        if window_start is None and window_end is None:
            window_start, window_end = default_window(evidence)
            basis = "LATEST_RELEASE"
        else:
            basis = "REQUESTED"
        window = _Window(
            [r for r in evidence.records if in_window(r, window_start, window_end)],
            None
            if window_start is None or window_end is None
            else _seconds(window_start, window_end),
        )
        domains = OVERVIEW_DOMAIN_SIGNALS.get(site.site_type, ())
        analytic = (
            {"cards": {}, "findings": []}
            if self._card_assessments is None
            else self._card_assessments(site, window_start, window_end)
        )
        cards = []
        for domain, signals in domains:
            coverage = [_coverage_row(window, key) for key in signals]
            gaps = [
                {
                    "device_id": row["device_id"],
                    "signal_id": row["signal_id"],
                    "status": row["status"],
                    "reason": GAP_REASONS[row["status"]],
                }
                for row in coverage
                if row["status"] != "REPORTED"
            ]
            cards.append(
                {
                    "domain_id": domain,
                    "label": domain,
                    "assessment": dict(analytic["cards"].get(domain, NO_ASSESSMENT)),
                    "metrics": DOMAIN_METRICS[domain](window),
                    "coverage": coverage,
                    "gaps": gaps,
                }
            )
        service = next((c for c in cards if c["domain_id"] == "Service"), None)
        return {
            "site_id": site.site_id,
            "site_type": site.site_type,
            "window": {
                "start": window_start,
                "end": window_end,
                "basis": basis,
                "hours": (
                    None
                    if window_start is None or window_end is None
                    else _fmt(_hours(_seconds(window_start, window_end)), 2)
                ),
            },
            "accepted_in_window": len(window.records),
            # Review F5: these are (source, gateway) pairs, and are named so.
            "source_gateway_pairs_in_window": len(
                {(r.source_id, r.gateway_id) for r in window.records}
            ),
            "objective": {
                "assessment": dict(NO_ASSESSMENT),
                "service_delivered": None if service is None else service["metrics"][0],
            },
            "cards": cards,
            "interval_statement": INTERVAL_STATEMENT,
            "timeline": _timeline(window),
            "timeline_statement": TIMELINE_STATEMENT,
            "findings": analytic["findings"],
            "findings_statement": (
                FINDINGS_PRESENT_STATEMENT if analytic["findings"]
                else NO_FINDINGS_STATEMENT if analytic["cards"]
                else FINDINGS_STATEMENT
            ),
        }
