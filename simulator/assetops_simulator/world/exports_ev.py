"""DD2.4 (spec `specs/DD-demo-data/spec.md` §4.5, §5.3; D-DD.49, D-DD.51, D-DD.52): the EV depot decided books.

In the source profiles' own formats:

- the fleet roster (`ev-fleet-roster-illustrative`): one row per bus per night, July to October, by the one roster
  function `roster_rows` (DD4.3 widens its month span to 6 Nov; it never writes a second roster writer, D-DD.52). A
  night is dated by its start (the evening return); the bus leaves the next morning. Embakasi's returns spread over
  17:30-19:30 by bus index (17:30 + i x 120/(n-1) minutes, to the whole minute, half to even), departure 05:30;
  Kasarani returns 22:00, Ruiru 21:00, both depart 05:00. `required_kwh` is `kwh_per_bus_night` scaled by largest
  remainder, to 0.001 kWh, so the month's total equals the month's `kwh`.
- service tickets (`ev-service-tickets-illustrative`): the incident blocks' tickets, from `TICKETS` (a module table
  with a manifest parity test, D-DD.51), OPEN on `as_of`.
- expenses (`expenses-illustrative-1`, unchanged): DS1b's EXPENSE rows only (OM). There is no PENALTY row: penalties
  are the node `departures_missed * penalty_rate` (D-DD.49), and the energy cost is the utility invoice's (DD4.4).
- budget (`ev-budget-illustrative`, D-DD.49): DS1b's own-leaf lines plus the node lines `energy_cost` and
  `departures_required`.

A month without its `kwh` writes no roster rows and is listed `NOT_IN_HISTORY`; it is never written as zero.

Standard library, `assetops_contracts` and the world modules only.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from pathlib import Path

from assetops_contracts.native import LAYOUTS, render_layout

from .allocate import allocate
from .books import (NOT_IN_HISTORY, SOURCE_VERSION, STAGED_KINDS, BooksResult, SiteMonth, budget_rows, checked,
                    ds1b_by_tenant, expense_rows, remaining_unwritten, site_months, zone_currency)
from .exports import ExportFile
from .months import dates_of
from .profile_csv import PROFILES_DIR, load_profile, render_profile, row_digest
from .records import RecordsResult

KEY = "EV_DEPOT_CAPTIVE"
BUDGET_LINES = ("peak_kwh", "max_kw", "maintenance", "energy_cost", "departures_required")
PROFILES = {"roster": "ev-fleet-roster-illustrative", "tickets": "ev-service-tickets-illustrative",
            "budget": "ev-budget-illustrative"}
#: Spec §4.5: per depot, (first return, last return or None, departure). Returns between the two spread by bus index.
ROSTER_TIMES = {
    "EV-EMB": (time(17, 30), time(19, 30), time(5, 30)),
    "EV-KAS": (time(22, 0), None, time(5, 0)),
    "EV-RUI": (time(21, 0), None, time(5, 0)),
}
#: D-DD.51: the tickets of the incident blocks (`tenants.metro-bus.sites.*.incident`), with a manifest parity test.
#: (Site code, asset, opened at, state). The CH-K2 ACKNOWLEDGED event is the warranty claim's, not the ticket's.
TICKETS = (
    ("EV-KAS", "CH-K2", "2026-11-01T23:40:00+03:00", "OPEN"),
    ("EV-RUI", "CH-R7", "2026-10-06T00:00:00+03:00", "OPEN"),
)
CONTRACTOR = "oem-contractor"  # R5: source text, never a named counterparty
MILLI = 1000


def _return_times(code: str, buses: int) -> list[time]:
    first, last, _ = ROSTER_TIMES[code]
    if last is None or buses == 1:
        return [first] * buses
    span = (last.hour * 60 + last.minute) - (first.hour * 60 + first.minute)
    out = []
    for i in range(buses):
        offset = int((Decimal(i * span) / Decimal(buses - 1)).to_integral_value(rounding=ROUND_HALF_EVEN))
        minutes = first.hour * 60 + first.minute + offset
        out.append(time(minutes // 60, minutes % 60))
    return out


def _kwh_text(milli: int) -> str:
    return f"{milli // MILLI}.{milli % MILLI:03d}"


def roster_rows(m: SiteMonth, zone, nights: list[date]) -> list[dict] | None:
    """One FLEET_ROSTER row per bus per night of `nights` (D-DD.52: the one roster function). None when the month's
    `kwh` is absent."""
    physical = m.site.get("physical", {})
    buses, per_night = int(physical["buses"]), Decimal(str(physical["kwh_per_bus_night"]))
    total = m.whole("actual", "kwh")
    if total is None:
        return None
    weights = [Fraction(per_night)] * (buses * len(nights))
    shares = allocate(total * MILLI, weights)
    returns = _return_times(m.code, buses)
    departure = ROSTER_TIMES[m.code][2]
    out = []
    k = 0
    for night in nights:
        for i in range(buses):
            bus = f"{m.code}-B{i + 1:02d}"
            back = datetime.combine(night, returns[i], tzinfo=zone)
            leaves = datetime.combine(night + timedelta(days=1), departure, tzinfo=zone)
            out.append(checked(m.where(), {
                "format_version": 1, "kind": "FLEET_ROSTER",
                "source_record_id": f"gen:{m.code}:{night.isoformat()}:roster:{i + 1:02d}",
                "source_version": SOURCE_VERSION, "site_code": m.code, "subject": {"kind": "VEHICLE", "ref": bus},
                "clocks": {"effective_from": night.isoformat()},
                "body": {"vehicle_ref": bus, "block_ref": f"{m.code}-BLK-{i + 1:02d}", "return_at": back.isoformat(),
                         "departure_at": leaves.isoformat(), "required_kwh": _kwh_text(shares[k])}}))
            k += 1
    return out


def ticket_rows(codes: set[str], layout) -> list[dict]:
    out = []
    for code, asset, opened, state in TICKETS:
        if code not in codes:
            continue
        record = {
            "format_version": 1, "kind": "SERVICE_TICKET", "source_record_id": f"gen:{code}:ticket:{asset}",
            "source_version": "", "site_code": code, "subject": {"kind": "ASSET", "ref": asset},
            "clocks": {"occurred_at": opened}, "status": state,
            "body": {"asset_ref": asset, "counterparty_ref": CONTRACTOR}}
        record["source_version"] = row_digest(layout, record)  # the State column versions the row (3A6)
        out.append(checked(code, record))
    return out


def build_ev_exports(view: dict, history: dict, records: RecordsResult, tenant: dict, *,
                     profiles_dir: Path = PROFILES_DIR) -> BooksResult:
    zone, currency = zone_currency(view)
    name = tenant["tenant"]
    months = site_months(view, history, tenant)
    ds1b = ds1b_by_tenant(records, name)
    unwritten: list[tuple[str, ...]] = []
    written: set[tuple[str, str, str, str]] = set()
    roster: list[dict] = []
    for m in months:
        rows = roster_rows(m, zone, dates_of(m.month))
        if rows is None:
            unwritten.append((name, m.code, m.month, "actual", "kwh", NOT_IN_HISTORY))
            continue
        roster += rows
        written.add((m.code, m.month, "actual", "kwh"))
    layouts = {key: load_profile(pid, profiles_dir)[1] for key, pid in PROFILES.items()}
    tickets = ticket_rows({s["code"] for s in tenant.get("sites", [])}, layouts["tickets"])
    budget, node_fields = budget_rows(KEY, name, months, ds1b, BUDGET_LINES, currency, unwritten)
    written |= {(code, month, "plan", f) for code, month, f in node_fields}
    files: list[ExportFile] = []
    for key, rows in (("roster", roster), ("tickets", tickets), ("budget", budget)):
        if rows:
            profile_id = PROFILES[key]
            stem = profile_id.removesuffix("-illustrative")
            files.append(ExportFile(name, f"profile.{stem}", profile_id, tuple(rows),
                                    render_profile(layouts[key], rows)))
    expenses = expense_rows(ds1b)
    if expenses:
        files.append(ExportFile(name, "expenses", "expenses-illustrative-1", tuple(expenses),
                                render_layout(LAYOUTS["expenses-illustrative-1"], expenses)))
    staged = [r["source_record_id"] for r in ds1b if r["kind"] in STAGED_KINDS]
    unwritten += remaining_unwritten(records, name, written, {})
    return BooksResult(tuple(files), tuple(unwritten), tuple(staged))
