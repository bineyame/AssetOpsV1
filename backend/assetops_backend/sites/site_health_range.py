"""SR-6a (rev 10 §10.2, rev 10a §10a.1, D-SR.19-23): mini-grid Site Health over a date range, `site-health-range-1`.

`health_range_body(service, tenant_id, site_code, req)` composes the body on ONE estate snapshot
(`EstatePortfolioService.read_snapshot`, one REPEATABLE READ, READ ONLY transaction), reading in order:
1. registration: `PostgresGatewayAccess._health_registration(snap._c, t, s)` (called, not copied; D-SR.23), injected
   as `registration` (`evidence.composition.health_registration`);
2-3. the grouped diagnostics and accepted readings per UTC day (`sites/adapters/postgres_health_range.py`), injected as
   `counts` (`sites.composition.health_range_counts`).
4. day states: `select_finding_scope` once, for the coverage only, then `estate.range_days.range_day_states` (D-SR.22,
   the SR-5a rule with step 6 = ANALYSED; Health shows no finding counts).

Rules (D-SR.20/D-SR.21):
- gateway-day contact: diagnostics > 0 -> IN_CONTACT when `diagnostics x cadence_seconds >= 0.9 x` the seconds of
  the day inside `[from, min(to, k))`, else PARTIAL_CONTACT; else readings through the gateway > 0 -> READINGS_ONLY;
  else a day before the gateway's `registered_at` UTC day -> NOT_EXPECTED; else NO_CONTACT;
- source-day: the day's `days[].state == NOT_EXPECTED` -> NOT_EXPECTED; readings > 0 -> READINGS; else NO_READINGS.
D-SR.49: AFTER_CUTOFF for days wholly after the cutoff; the body has no `battery` (the page reads `/battery`).
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Callable

from assetops_backend.estate.coverage import DOMAIN_OF_SITE_TYPE, MINI_GRID
from assetops_backend.estate.index import select_finding_scope
from assetops_backend.estate.range_days import GAP_STATES, NO_READINGS, NOT_EXPECTED, range_day_states
from assetops_backend.estate.scope import EstateRequest, wire_time

SCHEMA = "site-health-range-1"
IN_CONTACT, PARTIAL_CONTACT, READINGS_ONLY, NO_CONTACT = (
    "IN_CONTACT", "PARTIAL_CONTACT", "READINGS_ONLY", "NO_CONTACT")
#: D-SR.49 Q4: a day wholly at or after `min(to, k)` ("Not reached yet"), never NO_CONTACT / NO_READINGS.
AFTER_CUTOFF = "AFTER_CUTOFF"
READINGS = "READINGS"
#: IN_CONTACT when the received diagnostics cover at least this share of the day's seconds in the window.
CONTACT_SHARE = 0.9

Registration = Callable[[Any, Any, Any], tuple[tuple[Any, ...], tuple[Any, ...]]]
Counts = Callable[[Any, Any, Any, datetime, datetime, datetime], tuple[dict, dict]]


class HealthRangeNotApplicable(Exception):
    """The Site is not a mini-grid Site: its Health already reads the range (route 404)."""


def _day_seconds(d: date, lo: datetime, hi: datetime) -> float:
    """Seconds of UTC day `d` inside `[lo, hi)` (0 when the day lies outside)."""
    start = datetime.combine(d, time(0), tzinfo=timezone.utc)
    return max(0.0, (min(start + timedelta(days=1), hi) - max(start, lo)).total_seconds())


def gateway_contact(d: date, diagnostics: int, readings: int, cadence_seconds: int, registered_at: datetime,
                    lo: datetime, hi: datetime) -> str:
    """D-SR.20 precedence; `hi` is `min(to, k)`."""
    if diagnostics > 0:
        covered = diagnostics * cadence_seconds
        return IN_CONTACT if covered >= CONTACT_SHARE * _day_seconds(d, lo, hi) else PARTIAL_CONTACT
    if readings > 0:
        return READINGS_ONLY
    if d < registered_at.astimezone(timezone.utc).date():
        return NOT_EXPECTED
    if datetime.combine(d, time(0), tzinfo=timezone.utc) >= hi:
        return AFTER_CUTOFF
    return NO_CONTACT


def source_state(day_state: str, readings: int, after_cutoff: bool = False) -> str:
    if readings > 0:  # accepted readings always win (D-SR.20 principle)
        return READINGS
    if day_state == NOT_EXPECTED:
        return NOT_EXPECTED
    if after_cutoff:
        return AFTER_CUTOFF
    return NO_READINGS


def health_range_body(service: Any, tenant_id: Any, site_code: str, req: EstateRequest,
                      registration: Registration, counts: Counts) -> dict[str, Any] | None:
    """The `site-health-range-1` body without `battery`, or None when the Site is not in the authorized imported set
    (route 404). Raises `HealthRangeNotApplicable` for a Site that is not a mini-grid Site."""
    admit = lambda code: code == site_code  # noqa: E731 - one-Site admit, the Portfolio's own scope rule

    def work(snap: Any) -> dict[str, Any] | None:
        scope = service._scope(snap, tenant_id, req, admit)
        if not scope["sites"]:
            return None
        site = scope["sites"][0]
        if DOMAIN_OF_SITE_TYPE.get(site["site_type"]) != MINI_GRID:
            raise HealthRangeNotApplicable(site_code)
        k, sid = scope["k"], site["site_id"]
        gateways, sources = registration(snap._c, tenant_id, sid)
        diag, reads = counts(snap._c, tenant_id, sid, req.from_, req.to, k)
        f_sites, _ = select_finding_scope(snap, tenant_id, req, scope, {})
        day_rule = range_day_states(snap, tenant_id, site, req, scope, f_sites[0][2])  # D-SR.22
        days = list(day_rule)
        contact_hi = min(req.to, k)
        after = {d: datetime.combine(d, time(0), tzinfo=timezone.utc) >= contact_hi for d in days}

        sources_out, per_gateway = [], {}
        for src in sources:
            row_days = []
            for d in days:
                got = reads.get((str(src.source_id), d)) or {"n": 0, "last_at": None}
                per_gateway[(str(src.gateway_id), d)] = per_gateway.get((str(src.gateway_id), d), 0) + got["n"]
                row_days.append({"day": d.isoformat(), "accepted_readings": got["n"],
                                 "last_received_at": wire_time(got["last_at"]),
                                 "state": source_state(day_rule[d]["state"], got["n"], after[d])})
            sources_out.append({"source_external_id": src.source_external_id, "disabled": src.disabled,
                                "days": row_days})

        gateways_out = []
        for gw in gateways:
            row_days = []
            for d in days:
                got = diag.get((str(gw.gateway_id), d)) or {"n": 0, "first_at": None, "last_at": None}
                row_days.append({"day": d.isoformat(), "diagnostics": got["n"],
                                 "first_received_at": wire_time(got["first_at"]),
                                 "last_received_at": wire_time(got["last_at"]),
                                 "contact": gateway_contact(d, got["n"], per_gateway.get((str(gw.gateway_id), d), 0),
                                                            gw.cadence_seconds, gw.registered_at, req.from_,
                                                            contact_hi)})
            gateways_out.append({"gateway_external_id": gw.gateway_external_id, "mode": gw.mode,
                                 "disabled": gw.disabled, "cadence_seconds": gw.cadence_seconds, "days": row_days})

        days_out = []
        for d, rule in day_rule.items():
            row, state = rule["row"], rule["state"]
            readings = None if row is None else row.get("accepted_reading_count")
            days_out.append({"day": d.isoformat(), "state": state,
                             "accepted_readings": None if state in GAP_STATES else readings})
        totals = {d: sum(got["n"] for (_, day), got in reads.items() if day == d) for d in days}
        # D-SR.49 Q1: one class per day; with + without + not expected + after cutoff = requested.
        klass = {d: ("with" if totals[d] > 0 else "not_expected" if day_rule[d]["state"] == NOT_EXPECTED else
                     "after_cutoff" if after[d] else "without") for d in days}
        expected = {d for d in days if klass[d] in ("with", "without")}
        n = lambda c: sum(1 for d in days if klass[d] == c)  # noqa: E731
        skipped = (NOT_EXPECTED, AFTER_CUTOFF)  # D-SR.49 Q2: a gateway's own pre-registration / post-cutoff days

        def own_days(g):
            return [x for x in g["days"] if x["contact"] not in skipped and date.fromisoformat(x["day"]) in expected]

        in_contact_all = sum(1 for g in gateways_out
                             if own_days(g) and all(x["contact"] == IN_CONTACT for x in own_days(g)))
        return {
            "schema_version": SCHEMA,
            "site": {"site_code": site["site_code"], "site_name": site["site_name"], "timezone": site.get("timezone")},
            "window": {"from": wire_time(req.from_), "to": wire_time(req.to), "known_at": wire_time(k),
                       "basis": "HISTORICAL" if snap.basis_historical else "CURRENT"},
            "gateways": gateways_out,
            "sources": sources_out,
            "days": days_out,
            "summary": {"days_requested": len(days),
                        "days_with_readings": n("with"),
                        "days_without_readings": n("without"),
                        "days_not_expected": n("not_expected"),
                        "days_after_cutoff": n("after_cutoff"),
                        "gateways_in_contact_all_days": in_contact_all},
            "links": {"day": f"/sites/{site['site_code']}/health?day={{day}}"},
        }

    return service.read_snapshot(work)
