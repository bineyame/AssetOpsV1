"""SR-10a (rev 10b.1, D-SR.31-33): pure day reducers over the stored hours of `mini_depth.fuel_day` and
`mini_depth.backup_day` rows (`period_rows.hour_from_json` -> `read._Hour`; the head `result` is the `mini-depth-1`
shape of `projection._fuel` / `projection._backup`). Nothing here reads the database or recomputes an hour.

Hour classes (each stored hour is exactly one):
- pending: the hour has a live job (`PENDING`/`LEASED`) or reads `PENDING_RECOMPUTE` (a pending period at k);
- assessed: not pending, with a selected head (its `status` is counted);
- missing: not pending, with no selected head.

Fuel never sums residual, opening, closing or deliveries (W4-02 never has them). Backup counts backup start
sequences de-duplicated by `chain_id` (the latest hour wins) and never an outage count (`projection.py` q3 ruling 8).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, Mapping, Sequence

STATUSES = ("SUPPORTED", "LIMITED", "UNKNOWN")
SEQUENCE_RESULTS = ("PASS", "FAIL", "INCOMPLETE")
_LIVE_JOBS = frozenset({"PENDING", "LEASED"})

NOT_EXPECTED = "NOT_EXPECTED"
STILL_PROCESSING = "STILL_PROCESSING"
NO_ASSESSMENT = "NO_ASSESSMENT"
NO_DATA = "NO_DATA"
ASSESSED = "ASSESSED"
SEQUENCE_FAILED = "SEQUENCE_FAILED"
SEQUENCE_INCOMPLETE = "SEQUENCE_INCOMPLETE"
SEQUENCES_PASSED = "SEQUENCES_PASSED"
NO_SEQUENCE = "NO_SEQUENCE"


def _pending(h: Any) -> bool:
    return h.state == "PENDING_RECOMPUTE" or h.job_state in _LIVE_JOBS


def _num(value: Decimal) -> int | float:
    return int(value) if value == value.to_integral_value() else float(value)


def _dec(value: Any) -> Decimal:
    return Decimal(str(value))


def _base(local_day: date, hours: Sequence[Any]) -> tuple[dict[str, Any], list[Any]]:
    pending = [h for h in hours if _pending(h)]
    assessed = [h for h in hours if not _pending(h) and h.head is not None]
    counts = {s: 0 for s in STATUSES}
    codes: set[str] = set()
    for h in assessed:
        status = h.head.result.get("status")
        if status in counts:
            counts[status] += 1
        codes.update(str(l["code"]) for l in h.head.result.get("limitations") or ())
    return {"local_day": local_day.isoformat(), "stored": True, "hours_expected": len(hours), "hours_assessed": len(assessed),
            "hours_pending": len(pending), "hours_missing": len(hours) - len(assessed) - len(pending),
            "status_counts": counts, "limitations": sorted(codes)}, assessed


def fuel_day_summary(local_day: date, hours: Sequence[Any]) -> dict[str, Any]:
    """The modelled expected-use band of one local day: the sum of `cards.expected_use_l` bounds over the assessed
    hours that have one (null when none do)."""
    out, assessed = _base(local_day, hours)
    bands = [b for b in ((h.head.result.get("cards") or {}).get("expected_use_l") for h in assessed) if b is not None]
    out["expected_use_l"] = _band_sum(bands)
    out["hours_with_use"] = len(bands)
    return out


def backup_day_summary(local_day: date, hours: Sequence[Any]) -> dict[str, Any]:
    """The backup start sequences of one local day, de-duplicated by `chain_id` (the latest hour wins)."""
    out, assessed = _base(local_day, hours)
    chains: dict[str, dict[str, Any]] = {}
    successes = [n for n in ((h.head.result.get("cards") or {}).get("start_success_count") for h in assessed)
                 if n is not None]
    for h in sorted(assessed, key=lambda h: h.window.start):
        for r in h.head.result.get("rows") or ():
            chains[str(r["chain_id"])] = {"chain_id": r["chain_id"], "outage_start": r.get("outage_start"),
                                          "result": r.get("result"), "service_outcome": r.get("service_outcome"),
                                          "critical_recovery": r.get("critical_recovery")}
    sequences = sorted(chains.values(), key=lambda s: (str(s["outage_start"]), str(s["chain_id"])))
    out["sequences"] = sequences
    out["sequence_counts"] = {r: sum(1 for s in sequences if s["result"] == r) for r in SEQUENCE_RESULTS}
    out["start_success_count"] = sum(successes) if successes else None
    out["slowest_recovery"] = slowest_recovery(sequences)
    return out


def slowest_recovery(sequences: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """D-SR.51 (2): the largest `critical_recovery.seconds` over the de-duplicated sequences; a null recovery is
    skipped, the target comes from the same sequence, and a tie goes to the earliest `outage_start`."""
    timed = [s for s in sequences if (s.get("critical_recovery") or {}).get("seconds") is not None]
    if not timed:
        return None
    best = min(timed, key=lambda s: (-_dec(s["critical_recovery"]["seconds"]), str(s["outage_start"])))
    return {"seconds": best["critical_recovery"]["seconds"],
            "target_seconds": best["critical_recovery"].get("target_seconds")}


def absent_day(domain: str, local_day: date) -> dict[str, Any]:
    """D-SR.51 (3): an absent day row is unknown, not zero: `stored: false` and every count and figure null."""
    out: dict[str, Any] = {"local_day": local_day.isoformat(), "stored": False, "hours_expected": None,
                           "hours_assessed": None, "hours_pending": None, "hours_missing": None,
                           "status_counts": None, "limitations": None}
    if domain == "fuel":
        out.update(expected_use_l=None, hours_with_use=None)
    else:
        out.update(sequences=None, sequence_counts=None, start_success_count=None, slowest_recovery=None)
    return out


def day_state(domain: str, summary: Mapping[str, Any] | None, grade: str | None, *, no_readings: bool = False,
              pending: bool = False) -> tuple[str, bool]:
    """Rev 10b.1 "Day state" as amended by D-SR.70, first match wins: NOT_EXPECTED, pending (STILL_PROCESSING), NO_DATA
    (no readings that day, stored row or not), absent row (STILL_PROCESSING), then the rest; plus `partial` (missing
    hours or a LIMITED hour, D-E5.45). `summary` None is an absent row: "Still being prepared", never "nothing known"
    (D-SR.16)."""
    if grade == NOT_EXPECTED:
        state = NOT_EXPECTED
    elif pending or (summary is not None and summary["hours_pending"] > 0):
        state = STILL_PROCESSING
    elif no_readings:
        return NO_DATA, False
    elif summary is None:
        state = STILL_PROCESSING
    elif summary["hours_assessed"] == 0:
        state = NO_ASSESSMENT
    elif domain == "fuel":
        state = ASSESSED
    else:
        counts = summary["sequence_counts"]
        state = (SEQUENCE_FAILED if counts["FAIL"] else SEQUENCE_INCOMPLETE if counts["INCOMPLETE"]
                 else SEQUENCES_PASSED if summary["sequences"] else NO_SEQUENCE)
    partial = summary is not None and (summary["hours_missing"] > 0 or summary["status_counts"]["LIMITED"] > 0)
    return state, partial


def hours_of(body: Mapping[str, Any], *, historical: bool, pending: bool) -> list[Any]:
    """A stored day row's hours as `read._Hour` at the request (`period_rows.hour_from_json`)."""
    from assetops_backend.mini_depth.period_rows import hour_from_json

    return [hour_from_json(h, historical=historical, pending=pending) for h in body.get("hours") or ()]


#: Rev 10b.2/10b.3: the stored kind and the one-hour page of each range domain.
DAY_KIND = {"fuel": "mini_depth.fuel_day", "backup": "mini_depth.backup_day"}
SCHEMA_VERSION = {"fuel": "site-fuel-range-1", "backup": "site-backup-range-1"}
COUNTED_STATES = {"fuel": (ASSESSED,), "backup": (SEQUENCE_FAILED, SEQUENCE_INCOMPLETE, SEQUENCES_PASSED, NO_SEQUENCE)}


def hour_link(domain: str, site_code: str, local_day: date, tz: str) -> str:
    """The existing one-hour page of the day's local 12:00 hour (`[local noon, +1 h)` as UTC instants)."""
    from urllib.parse import quote

    from assetops_backend.mini_depth.inputs import local_hour

    w = local_hour(local_day, 12, tz)
    fmt = "%Y-%m-%dT%H:%M:%SZ"
    return (f"/sites/{quote(site_code, safe='')}/performance/{domain}"
            f"?from={quote(w.start.strftime(fmt), safe='')}&to={quote(w.end.strftime(fmt), safe='')}")


def range_days(domain: str, site_code: str, tz: str, site_id: Any, days: Sequence[date], result: Any,
               grades: Mapping[date, str], *, historical: bool,
               no_readings: frozenset[date] = frozenset()) -> list[dict[str, Any]]:
    """One entry per requested day from one `PeriodReader.read` result of `DAY_KIND[domain]`: the day summary, its
    state and `partial`, and the hour link. An absent row is STILL_PROCESSING (no compose fallback, D-SR.31)."""
    kind = DAY_KIND[domain]
    reduce = fuel_day_summary if domain == "fuel" else backup_day_summary
    by_day = {r.row.local_day: r for r in result.rows if r.row.kind == kind and r.row.site_id == site_id}
    out = []
    for d in days:
        read = by_day.get(d)
        summary = None
        pending = False
        if read is not None:
            pending = bool(read.pending) or result.is_pending(site_id, d, kind)
            summary = reduce(d, hours_of(read.row.body, historical=historical, pending=pending))
        state, partial = day_state(domain, summary, grades.get(d), no_readings=d in no_readings, pending=pending)
        if state == NO_DATA:   # D-SR.70: no counts, no figures, whether or not a row is stored
            entry = {**absent_day(domain, d), "stored": read is not None}
        else:
            entry = summary if summary is not None else absent_day(domain, d)
        out.append({**entry, "state": state, "partial": partial, "hour_link": hour_link(domain, site_code, d, tz)})
    return out


def _band_sum(bands: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    if not bands:
        return None
    return {"low": _num(sum((_dec(b["low"]) for b in bands), Decimal(0))),
            "high": _num(sum((_dec(b["high"]) for b in bands), Decimal(0)))}


def totals(domain: str, days: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Sums over the counted days only; `partial` when a requested day is not counted or a counted day is partial."""
    counted = [d for d in days if d["state"] in COUNTED_STATES[domain]]
    out: dict[str, Any] = {"days_counted": len(counted), "days_requested": len(days),
                           "partial": len(counted) < len(days) or any(d["partial"] for d in counted)}
    if domain == "fuel":
        out["expected_use_l"] = _band_sum([d["expected_use_l"] for d in counted if d["expected_use_l"] is not None])
    else:
        # D-SR.51 (4): a sequence that crosses local midnight is on two days' rows; count it once by chain_id
        # (the latest day wins).
        chains: dict[str, Mapping[str, Any]] = {}
        for d in sorted(counted, key=lambda d: d["local_day"]):
            for seq in d["sequences"] or ():
                chains[str(seq["chain_id"])] = seq
        out["sequence_counts"] = {r: sum(1 for s in chains.values() if s["result"] == r) for r in SEQUENCE_RESULTS}
        successes = [d["start_success_count"] for d in counted if d["start_success_count"] is not None]
        out["start_success_count"] = sum(successes) if successes else None
    return out


def day_grades(facts: Any) -> dict[date, str]:
    """The chain day grade of each day of one `ChainRequest.day` read (`chain/site_chain.days_of`, `day_grade` over
    the mini-grid measures with the day's declared-absent measures)."""
    from assetops_backend.chain.measures import measures_for
    from assetops_backend.chain.site_chain import days_of

    return {date.fromisoformat(e["day"]): e["grade"]
            for e in days_of(facts, tuple(m.key for m in measures_for("MINIGRID")))}


def no_reading_days(facts: Any) -> frozenset[date]:
    """D-SR.70: the days on which every applicable mini measure grade is NO_DATA (`days_of` `measures`, minus
    `none_declared` and NOT_EXPECTED, at least one left). A missing snapshot is NO_DATA (CH5a1-R Q9)."""
    from assetops_backend.chain.measures import measures_for
    from assetops_backend.chain.site_chain import days_of

    out = set()
    for e in days_of(facts, tuple(m.key for m in measures_for("MINIGRID"))):
        left = [g for m, g in e["measures"].items() if m not in e.get("none_declared", ()) and g != NOT_EXPECTED]
        if left and all(g == "NO_DATA" for g in left):
            out.add(date.fromisoformat(e["day"]))
    return frozenset(out)


def compose(domain: str, site: Mapping[str, Any], window: Mapping[str, Any], days: Sequence[date], result: Any,
            grades: Mapping[date, str], *, historical: bool,
            no_readings: frozenset[date] = frozenset()) -> dict[str, Any]:
    """The `site-fuel-range-1` / `site-backup-range-1` body. `site` = {id, site_code, site_name, timezone};
    `window` = {from, to, known_at} as UTC text; `grades` = the chain day grade of each day (`ChainRequest.day`)."""
    rows = range_days(domain, site["site_code"], site["timezone"], site["id"], days, result, grades,
                      historical=historical, no_readings=no_readings)
    shown = {k: v for k, v in site.items() if k != "id"}
    return {"schema_version": SCHEMA_VERSION[domain], "site": shown, "window": dict(window), "days": rows,
            "totals": totals(domain, rows)}


__all__ = ["ASSESSED", "COUNTED_STATES", "DAY_KIND", "SCHEMA_VERSION", "compose", "day_grades", "no_reading_days", "NO_DATA", "hour_link", "range_days",
           "totals", "NOT_EXPECTED", "NO_ASSESSMENT", "NO_SEQUENCE", "SEQUENCES_PASSED", "SEQUENCE_FAILED",
           "SEQUENCE_INCOMPLETE", "STILL_PROCESSING", "absent_day", "backup_day_summary", "slowest_recovery", "day_state", "fuel_day_summary",
           "hours_of"]
