"""W3-02 commit 3: the estate Financials root, `GET /api/estate/financials`, over the one estate snapshot (pure).

Every selected persisted consequence head of the authorized estate is one register line (closure 4 "Money and proof
corrections"): W1 `financial_consequence_revision` through `select_consequence_on`, cold `cold_consequence_revision`
(both kinds) through the pinned `ColdSiteReadService.money_on`, EV `ev_consequence_revision` through the pinned
`EvSiteReads.money_on`. No line is synthesized from a Finding without a head, and a transient EV `STALE_BASIS`
guard (`revision_id: null`) is never a line, token revision or numeric candidate.

Eligibility follows closure 2 Q6-Q7's ordered table; partitions, states, exclusions and diagnostics follow closure 1
"Money row and comparison contract", closure 2 Q19 and closure 3 Q19/C1, over the full unpaged line set. The estate
basis mode (c1-q1) alone decides HISTORICAL: an explicit earlier estate `known_at`, or the cursor's frozen
`page_one_mode=historical`. The EV facade's `historical_label` is ignored. `summary.estate_total` is always null.
Nothing here opens a connection or writes; the snapshot is `postgres_evidence_money_read.py`'s bound read.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from assetops_backend.estate.coverage import (
    COLD, COVERED, CURRENT, DOMAIN_OF_SITE_TYPE, EV, HISTORICAL, MINI_GRID, NOT_APPLICABLE, PENDING, STALE,
    not_applicable, site_coverage)
from assetops_backend.estate.evidence_money import (
    CURRENT_VIEW, EMPTY, EMPTY_SCOPE, _ids, _site_href, _window_state, group_key_for_partition, site_home_href,
    window_links)
from assetops_backend.estate.index import _coverage_site, _coverage_state, _status, _token_site
from assetops_backend.estate.scope import EstateRequest, resume_after, selection_token, wire_time
from assetops_backend.evidence.provenance_read import source_gate
from assetops_backend.financials.ev_money import ERROR_PENDING, TARIFF_UNIT
from assetops_backend.financials.fuel_cost import PRICE_UNIT

FINANCIALS_SCHEMA = "estate-financials-1"
FINANCIALS_ORDER = "window_start desc nulls last, site_code_key asc, site_id asc, category asc, line_key asc"

OPERATING = "CANDIDATE_OPERATING_COST_EXPOSURE"
PRODUCT = "POTENTIAL_PRODUCT_EXPOSURE"
TARIFF = "GROSS_TARIFF_SCENARIO"
REPAIR = "RECORDED_REPAIR"
OBSERVED, SCENARIO = "OBSERVED_WINDOW", "SCENARIO_WINDOW"
#: The three mock categories, per domain, that get a closure 2/3 `NO_LINES` sentinel. `RECORDED_REPAIR` lines are
#: listed and partitioned when a stored head exists, but the category is outside the mock enum and gets no sentinel.
APPLICABLE = {MINI_GRID: (OPERATING,), COLD: (PRODUCT,), EV: (TARIFF,)}
COLD_CATEGORY = {"PRODUCT_EXPOSURE": PRODUCT, "RECORDED_REPAIR": REPAIR}
CONTRIBUTION = "PRODUCTIVE_USE_CONTRIBUTION_SCENARIO"
#: Owner Q9 (a constant per category): who a money line benefits. Commercial build spec 0.4.
BENEFICIARY_OF_CATEGORY = {OPERATING: "MINI_OPERATOR", CONTRIBUTION: "MINI_OPERATOR", PRODUCT: "GOODS_OWNER",
                           REPAIR: "COOLING_PROVIDER", TARIFF: "CHARGING_SERVICE"}

ELIGIBLE, UNPRICED, UNKNOWN_E, PENDING_E, HISTORICAL_E, WITHHELD, CONFLICT = (
    "ELIGIBLE", "UNPRICED", "UNKNOWN", "PENDING", "HISTORICAL", "WITHHELD", "CONFLICT")
COMPARABLE, SINGLE_LINE, INELIGIBLE, OVERLAPPING, UNKNOWN_COVERAGE, NO_LINES = (
    "COMPARABLE", "SINGLE_LINE", "INELIGIBLE", "OVERLAPPING_BASIS", "UNKNOWN_COVERAGE", "NO_LINES")
EV_LIMIT = "Gross scenario only; not cash collected."
PARTITION_INELIGIBLE = "PARTITION_INELIGIBLE"


def assumption_fingerprint(category: str, currency: str | None, unit: str | None, rate: Any,
                           price_kind: str | None) -> str | None:
    """Closure 1: `sha256:` of sorted-key compact JSON over the normalized economic assumption values; an
    unreadable value is null (no COMPARABLE)."""
    if not (currency and unit and price_kind) or rate is None:
        return None
    try:
        value = Decimal(str(rate))
    except InvalidOperation:
        return None
    if not value.is_finite():
        return None
    payload = {"version": "estate-money-assumption/1", "category": category, "currency": currency, "unit": unit,
               "rate": format(value.normalize(), "f"), "price_kind": price_kind}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _at(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _dec(value: Any) -> Decimal | None:
    try:
        return None if value is None else Decimal(str(value))
    except InvalidOperation:
        return None


def decide(*, historical: bool, pending: bool, provenance: dict[str, Any], withheld: bool, unknown: bool,
           unpriced: bool, eligible: bool) -> tuple[str, list[str]]:
    """Closure 2 Q6-Q7: the ordered table, top to bottom; one eligibility per line."""
    if historical:
        return HISTORICAL_E, ["HISTORICAL"]
    if pending:
        return PENDING_E, ["PENDING"]
    cls = provenance.get("classification")
    if cls == "UNKNOWN":
        return WITHHELD, ["UNKNOWN_SOURCE"]
    if cls == "MIXED":
        return WITHHELD, ["MIXED_SOURCE"]
    if withheld or not source_gate(provenance)["permits_current_money"]:
        return WITHHELD, ["WITHHELD"]
    if unknown:
        return UNKNOWN_E, ["BASIS_NOT_PROVEN"]
    if unpriced:
        return UNPRICED, ["UNPRICED"]
    if eligible:
        return ELIGIBLE, []
    return UNKNOWN_E, ["BASIS_NOT_PROVEN"]


def _line(site: dict[str, Any], domain: str, category: str, revision_id: str, *, finding_id: Any,
          finding_revision_id: Any, window_start: Any, window_end: Any, quantity: dict[str, Any],
          amount: dict[str, Any] | None, period_kind: str, assumptions: list[str], fingerprint: str | None,
          cited: list[str], technical: list[str], overlap_group: Any, limit: str | None,
          provenance: dict[str, Any], links: dict[str, Any], decision: tuple[str, list[str]],
          disclosure: dict[str, Any] | None = None) -> dict[str, Any]:
    eligibility, reasons = decision
    line_key = f"{domain}:{str(revision_id).lower()}"
    ws, we = _at(window_start), _at(window_end)
    return {
        "line_key": line_key, "domain": domain, "site_id": str(site["site_id"]), "site_code": site["site_code"],
        "site_name": site["site_name"], "category": category, "beneficiary": BENEFICIARY_OF_CATEGORY[category],
        "finding_id": None if finding_id is None else str(finding_id),
        "finding_revision_id": None if finding_revision_id is None else str(finding_revision_id),
        "consequence_revision_id": str(revision_id).lower(), "window_start": wire_time(ws), "window_end": wire_time(we),
        "quantity": quantity, "amount": amount if eligibility == ELIGIBLE else None, "period_kind": period_kind,
        "assumption_revision_ids": _ids(assumptions), "assumption_fingerprint": fingerprint,
        "basis_evidence_ids": _ids(cited), "technical_interval_ids": _ids(technical),
        "overlap_group": overlap_group, "eligibility": eligibility, "reason_codes": sorted(set(reasons)),
        "limit": limit, "source_provenance": provenance, "links": links,
        "disclosure": {"pinned_amount": amount, **(disclosure or {})},
        "group_key": None,
        "_ws": ws, "_we": we, "_currency": None if amount is None else amount.get("currency"),
        "_key": (ws, str(site["site_code_key"]), str(site["site_id"]).lower(), category, line_key)}


def _money_links(code: str, domain: str, pin: dict[str, Any] | None, cutoff: datetime | None,
                 k: datetime) -> dict[str, Any]:
    """Closure 4 / closure 5 B5: the server owns links. Mini-grid opens the current Site view without an estate
    cutoff; cold/EV carry only the row's own pinned window and proven row-local cutoff, else the Site home (EV:
    `/sites/{code}/ev`, post-W6 W3-estate Q2/Q9)."""
    base, home = _site_href(code), site_home_href(code, domain)
    if domain == MINI_GRID:
        return {"site": home, "bridge": f"{base}/financials", "evidence": f"{base}/evidence",
                "current_view_label": CURRENT_VIEW}
    shown = window_links(code, domain, pin, cutoff, k)
    if shown["site_readiness_label"] is not None:
        return {"site": home, "bridge": home, "evidence": home, "current_view_label": CURRENT_VIEW}
    query = shown["site_readiness"].split("?", 1)[1]
    bridge = f"{base}/financials" if domain == COLD else f"{base}/ev/financials"
    return {"site": home, "bridge": f"{bridge}?{query}", "evidence": shown["site_readiness"],
            "current_view_label": None}


# --- per-domain selected heads -------------------------------------------------------------------------------

def mini_grid_lines(snap: Any, t: Any, site: dict[str, Any], cov: dict[str, Any], k: datetime) -> list[dict]:
    lines = []
    links = _money_links(site["site_code"], MINI_GRID, None, None, k)
    for row in cov.get("rows") or ():
        sel = snap.consequence(t, site["site_id"], row["finding_revision_id"], k)
        cid = sel.get("consequence_revision_id")
        if cid is None:  # no head, no line (closure 1 Q18)
            continue
        cited = sel.get("cited") or {}
        power = [str(x) for x in cited.get("power_evidence_ids") or ()]
        basis = _ids([*row["source_provenance"].get("evidence_ids", ()), *power])
        prov = snap.consequence_provenance(t, site["site_id"], cid, row["finding_revision_id"], basis)
        state = sel.get("consequence_state")
        current = (sel.get("currentness") or {}).get("state")
        money = snap.eligibility(t, site["site_id"], row["finding_id"], k).get("state")
        low, high, currency = _dec(sel.get("amount_low")), _dec(sel.get("amount_high")), sel.get("currency")
        shaped = (low is not None and high is not None and isinstance(currency, str) and len(currency) == 3
                  and currency.isupper() and low <= high)
        price = sel.get("price") or {}
        amount = {"low": sel["amount_low"], "high": sel["amount_high"], "currency": currency} if shaped else None
        decision = decide(
            historical=snap.basis_historical, pending=money == "PENDING_REASSESSMENT" or current == "PENDING",
            provenance=prov,
            withheld=(state in ("AUDIT_ONLY", "STALE") or current in ("STALE", "HISTORICAL")
                      or money == "WITHHELD_GENERATOR_SERIES"
                      or (state == "PRICED" and current == "CURRENT" and money != "ELIGIBLE")),
            unknown=state == "QUANTITY_UNAVAILABLE" or (state == "PRICED" and not shaped),
            unpriced=state == "UNPRICED",
            eligible=state == "PRICED" and current == "CURRENT" and money == "ELIGIBLE" and shaped
            and sel.get("quantity_high") is not None)
        lines.append(_line(
            site, MINI_GRID, OPERATING, cid, finding_id=row["finding_id"],
            finding_revision_id=row["finding_revision_id"], window_start=sel.get("window_start"),
            window_end=sel.get("window_end"),
            quantity={"low": sel.get("quantity_low"), "high": sel.get("quantity_high"),
                      "unit": sel.get("quantity_unit")},
            amount=amount, period_kind=OBSERVED,
            assumptions=[x for x in [cited.get("price_revision_id")] if x],
            # c3-q2(5): the economic price unit `currency/L`, not the consequence quantity unit `L`.
            fingerprint=assumption_fingerprint(OPERATING, currency, PRICE_UNIT, price.get("value"),
                                               price.get("state")),
            cited=basis, technical=power, overlap_group=sel.get("overlap_group"),
            limit=" ".join(sel.get("limitations") or ()) or None, provenance=prov, links=links, decision=decision,
            disclosure={"currentness": sel.get("currentness"), "money_eligibility": money}))
    return lines


def windowed_lines(snap: Any, t: Any, site: dict[str, Any], domain: str, req: EstateRequest, k: datetime,
                   site_state: str) -> tuple[list[dict], bool, list[str], bool]:
    """Cold/EV heads per selected pinned window; returns the lines, whether every window is covered (a stale
    or pending window, or an EV `STALE_BASIS` guard, leaves the category's coverage unknown), the selected EV
    session revision IDs of every pinned window, with or without a stored head (c3-q2(6)), and `pending_guard`
    (W3-03 r1b Q-1b-3): true if any selected cold pinned window is `withheld` or any selected EV pinned window
    has guard `ERROR_PENDING`, whether or not that window emits a line. A `STALE_BASIS` guard, a missing pin, an
    uncovered window or an ordinary UNPRICED head never sets it."""
    s = site["site_id"]
    cutoff = snap.evidence_cutoff(t, s, k)
    pins = [] if cutoff is None else snap.pinned_windows(t, s, domain, req.from_, req.to, cutoff, k)
    lines, covered, sessions, pending_guard = [], True, [], False
    for pin in pins:
        state = _window_state(snap, site_state, pin.get("state"))
        covered = covered and state in COVERED
        links = _money_links(site["site_code"], domain, pin, cutoff, k)
        common = {"historical": state == HISTORICAL, "pending": state == PENDING}
        if domain == COLD:
            read = snap.cold_money(t, s, pin, k)
            if read["withheld"]:  # overlapping cold work pending at K: full-scope coverage is unknown (c3-q2(2))
                covered = False
                pending_guard = True
            for row in read["consequences"]:
                basis = row["exact_basis"]
                prov = snap.cited_provenance(t, s, basis["evidence_ids"], [row["id"]])
                stored = row["state"]
                decision = decide(**{**common, "pending": common["pending"] or read["withheld"]}, provenance=prov,
                                  withheld=stored == "WITHHELD" or state == STALE, unknown=state not in COVERED
                                  and state not in (PENDING, STALE), unpriced=stored == "UNPRICED", eligible=False)
                lines.append(_line(
                    site, COLD, COLD_CATEGORY.get(row["kind"], row["kind"]), row["id"],
                    finding_id=read["finding_ids"].get(str(row["finding_revision_id"]).lower()),
                    finding_revision_id=row["finding_revision_id"], window_start=row["window_start"],
                    window_end=row["window_end"],
                    quantity={**row["quantity_bounds"], "unit": row["quantity_unit"]}, amount=None,
                    period_kind=OBSERVED, assumptions=basis["assumption_revision_ids"], fingerprint=None,
                    cited=basis["evidence_ids"], technical=[], overlap_group=row["overlap_group"],
                    limit=row["limitation"], provenance=prov, links=links, decision=decision,
                    disclosure={"reason": row["reason"], "counted": row["counted"], "hold": read["hold"]}))
            continue
        read = snap.ev_money(pin)
        sessions += [str(x) for x in read.get("session_revision_ids") or ()]
        head, guard = read["consequence"], read["guard"]
        pending_guard = pending_guard or guard == ERROR_PENDING
        history = sorted(read["history"], key=lambda h: (h["revision_no"] or 0))
        if head is not None and head.get("revision_id") is None:  # the transient guard: never a line
            covered = False
            if not history:
                continue
            head = history[-1]  # only the exact older stored head, current amount withheld
            # Only a pending recompute is pending work; a stale or historical-current-claim guard withholds.
            forced = {"withheld": guard != ERROR_PENDING, "pending": guard == ERROR_PENDING}
        elif head is None:
            continue
        else:
            forced = {"withheld": False, "pending": False}
        prov = snap.cited_provenance(t, s, head["evidence_ids"], [head["revision_id"]])
        amount = (None if head["amount"] is None or not head["currency"] else
                  {"low": head["amount"], "high": head["amount"], "currency": head["currency"]})
        decision = decide(
            historical=common["historical"], pending=common["pending"] or forced["pending"], provenance=prov,
            withheld=forced["withheld"] or head["state"] in ("WITHHELD", "STALE_BASIS") or state == STALE,
            unknown=state not in COVERED and state not in (PENDING, STALE)
            or (head["state"] == "ESTIMATED" and (amount is None or head["quantity_kwh"] is None)),
            unpriced=head["state"] == "UNPRICED",
            eligible=(head["state"] == "ESTIMATED" and head["reason"] == "ELIGIBLE_COMPLETE_INTERVALS"
                      and head["tariff_revision_id"] is not None and amount is not None
                      and head["quantity_kwh"] is not None))
        lines.append(_line(
            site, EV, TARIFF, head["revision_id"], finding_id=None, finding_revision_id=None,
            window_start=read["window_start"], window_end=read["window_end"],
            quantity={"low": head["quantity_kwh"], "high": head["quantity_kwh"],
                      "unit": None if head["quantity_kwh"] is None else "kWh"},
            amount=amount, period_kind=SCENARIO,
            assumptions=[x for x in [head["tariff_revision_id"]] if x],
            fingerprint=assumption_fingerprint(TARIFF, head["currency"], TARIFF_UNIT, head["tariff_value"],
                                               "GROSS_TARIFF_PER_KWH"),
            cited=head["evidence_ids"], technical=head["session_revision_ids"], overlap_group=head["overlap_group"],
            limit=" ".join(x for x in [head.get("limitation"), EV_LIMIT] if x), provenance=prov, links=links,
            decision=decision,
            disclosure={"guard": guard, "history": [h["revision_id"] for h in read["history"]]}))
    return lines, covered and bool(pins), _ids(sessions), pending_guard


# --- comparison ---------------------------------------------------------------------------------------------

def _beneficiary(line: dict[str, Any]) -> str | None:
    return line.get("beneficiary", BENEFICIARY_OF_CATEGORY.get(line["category"]))


def _partition(line: dict[str, Any]) -> tuple:
    return (line["category"], line["_currency"], line["window_start"], line["window_end"], line["period_kind"],
            line["assumption_fingerprint"], _beneficiary(line))


def _overlaps(eligible: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    """Closure 1 / closure 2 Q19 rule 3: pairwise duplicate key, equal nonnull overlap group, or intersecting
    technical or cited IDs is OVERLAPPING_BASIS; missing technical/citation proof is BASIS_NOT_PROVEN."""
    involved, reasons = set(), set()
    for i, a in enumerate(eligible):
        for b in eligible[i + 1:]:
            proven = a["technical_interval_ids"] and b["technical_interval_ids"] and a["basis_evidence_ids"] \
                and b["basis_evidence_ids"]
            collide = (a["line_key"] == b["line_key"]
                       or (a["overlap_group"] is not None and a["overlap_group"] == b["overlap_group"])
                       or set(a["technical_interval_ids"]) & set(b["technical_interval_ids"])
                       or set(a["basis_evidence_ids"]) & set(b["basis_evidence_ids"]))
            if collide or not proven:
                involved |= {a["line_key"], b["line_key"]}
                reasons.add("OVERLAPPING_BASIS" if collide else "BASIS_NOT_PROVEN")
    return involved, reasons


def compare(lines: list[dict[str, Any]], applicable: dict[str, bool]) -> tuple[list, list, list]:
    """Groups, exclusions and diagnostics over the full line set. `applicable` maps each category applicable to an
    authorized Site to whether its coverage is complete. Mutates CONFLICT lines and their `group_key`."""
    parts: dict[tuple, list[dict[str, Any]]] = {}
    for line in lines:
        parts.setdefault(_partition(line), []).append(line)
    groups, exclusions = [], []
    for key in sorted(parts, key=lambda p: json.dumps(p, default=str)):
        members = sorted(parts[key], key=lambda x: x["line_key"])
        category, currency, ws, we, period, fingerprint, beneficiary = key
        gkey = group_key_for_partition(category, currency, ws, we, period, fingerprint, beneficiary=beneficiary)
        reasons = {r for m in members for r in m["reason_codes"]}
        eligible = [m for m in members if m["eligibility"] == ELIGIBLE]
        involved, overlap = _overlaps(eligible) if len(eligible) >= 2 else (set(), set())
        reasons |= overlap
        for m in members:
            m["group_key"] = gkey
            if m["line_key"] in involved:
                m.update(eligibility=CONFLICT, amount=None,
                         reason_codes=sorted(set(m["reason_codes"]) | {"OVERLAPPING_BASIS"}))
        uncovered = applicable.get(category) is False
        if uncovered:
            reasons.add(UNKNOWN_COVERAGE)
        if len(eligible) >= 2 and fingerprint is None:
            reasons.add("ASSUMPTION_UNKNOWN")
        if uncovered:
            state = UNKNOWN_COVERAGE
        elif len(eligible) < len(members) or "ASSUMPTION_UNKNOWN" in reasons:
            state = INELIGIBLE
        elif involved:
            state = OVERLAPPING
        else:
            state = SINGLE_LINE if len(eligible) == 1 else COMPARABLE
        amount = None
        if state == COMPARABLE:
            low = sum((Decimal(m["amount"]["low"]) for m in eligible), Decimal(0))
            high = sum((Decimal(m["amount"]["high"]) for m in eligible), Decimal(0))
            amount = {"low": str(low), "high": str(high), "currency": currency}
        groups.append({"group_key": gkey, "category": category, "currency": currency, "window_start": ws,
                       "window_end": we, "period_kind": period, "assumption_fingerprint": fingerprint,
                       "state": state, "line_keys": [m["line_key"] for m in members], "amount": amount,
                       "reason_codes": sorted(reasons)})
        if state not in (COMPARABLE, SINGLE_LINE):
            for m in members:
                own = set(m["reason_codes"]) | ({UNKNOWN_COVERAGE} if uncovered else set())
                if not own and state == INELIGIBLE and m["eligibility"] == ELIGIBLE and len(eligible) < len(members):
                    own = {PARTITION_INELIGIBLE}  # group membership only; never a mate's line reason (L4)
                exclusions.append({"line_key": m["line_key"], "group_key": gkey,
                                   "reason_codes": sorted(own or reasons)})
        else:
            exclusions += [{"line_key": m["line_key"], "group_key": gkey, "reason_codes": m["reason_codes"]}
                           for m in members if m["eligibility"] != ELIGIBLE]
    present = {line["category"] for line in lines}
    for category in sorted(c for c in applicable if c not in present):  # closure 2/3: the zero-head sentinel
        uncovered = applicable[category] is False
        groups.append({"group_key": None, "category": category, "currency": None, "window_start": None,
                       "window_end": None, "period_kind": None, "assumption_fingerprint": None,
                       "state": UNKNOWN_COVERAGE if uncovered else NO_LINES, "line_keys": [], "amount": None,
                       "reason_codes": sorted({NO_LINES, *([UNKNOWN_COVERAGE] if uncovered else [])})})
    diagnostics = []
    for category in sorted(present):
        mine = [line for line in lines if line["category"] == category]
        for code, field in (("MIXED_CURRENCY", lambda x: x["_currency"]), ("DIFFERENT_PERIOD", lambda x: x["period_kind"]),
                            ("DIFFERENT_WINDOW", lambda x: (x["window_start"], x["window_end"])),
                            ("DIFFERENT_ASSUMPTION", lambda x: x["assumption_fingerprint"])):
            values = {field(x) for x in mine if field(x) not in (None, (None, None))}
            if len(values) > 1:
                diagnostics.append({"category": category, "code": code,
                                    "line_keys": sorted(x["line_key"] for x in mine
                                                        if field(x) not in (None, (None, None)))})
    exclusions.sort(key=lambda e: e["line_key"])
    return groups, exclusions, diagnostics


def _order(line: dict[str, Any]) -> tuple:
    ws = line["_ws"]
    return (ws is None, -(ws.timestamp()) if ws is not None else 0.0, *line["_key"][1:])


# --- the read --------------------------------------------------------------------------------------------------

def select_financial_scope(snap: Any, tenant_id: Any, req: EstateRequest, scope: dict[str, Any]) -> tuple:
    """W3-03 closure 4 B1/B2: `(per_site, lines, applicable, groups, exclusions, diagnostics)` over every selected
    line before paging, on the caller's one snapshot and `scope` (moved verbatim from `financials_body`)."""
    k = scope["k"]
    per_site, lines, applicable = [], [], {}
    for site in scope["sites"]:
        domain = DOMAIN_OF_SITE_TYPE.get(site["site_type"])
        if domain is None:
            per_site.append((site, NOT_APPLICABLE, {**not_applicable(), "_pending_guard": False}, []))
            continue
        cov = site_coverage(snap, tenant_id, site["site_id"], domain, req.from_, req.to, k)
        if domain == MINI_GRID:
            site_lines = mini_grid_lines(snap, tenant_id, site, cov, k) if cov["state"] in COVERED else []
            covered, sessions, pending_guard = cov["state"] in COVERED, [], False
        else:
            site_lines, windows_covered, sessions, pending_guard = windowed_lines(
                snap, tenant_id, site, domain, req, k, cov["state"])
            covered = cov["state"] in COVERED and windows_covered
        for category in APPLICABLE[domain]:
            applicable[category] = applicable.get(category, True) and covered
        per_site.append((site, domain, {**cov, "_sessions": sessions, "_windows_covered": covered if domain == MINI_GRID
                                                                                else windows_covered,
                                       "_pending_guard": pending_guard}, site_lines))
        lines += site_lines
    seen: set[str] = set()
    lines = [x for x in lines if not (x["line_key"] in seen or seen.add(x["line_key"]))]  # dedupe selected heads
    groups, exclusions, diagnostics = compare(lines, applicable)
    lines.sort(key=_order)
    return per_site, lines, applicable, groups, exclusions, diagnostics


def financials_body(service: Any, snap: Any, tenant_id: Any, req: EstateRequest, admit: Any) -> dict[str, Any]:
    scope = service._scope(snap, tenant_id, req, admit)
    k = scope["k"]
    per_site, lines, applicable, groups, exclusions, diagnostics = select_financial_scope(snap, tenant_id, req, scope)
    token_sites = []
    for site, domain, cov, site_lines in per_site:
        arrays = {"selected_finding_revision_ids": _ids(x["finding_revision_id"] for x in site_lines),
                  "selected_action_event_ids": [],
                  "selected_consequence_revision_ids": _ids(x["consequence_revision_id"] for x in site_lines),
                  "selected_assumption_revision_ids": _ids(a for x in site_lines for a in x["assumption_revision_ids"]),
                  # c3-q2(6): plus every pinned selected EV window's session revision IDs (c1-q3(5)).
                  "selected_assessment_revision_ids": _ids([*(cov.get("selected_assessment_revision_ids") or ()),
                                                            *cov.get("_sessions", ())]),
                  "cited_accepted_evidence_ids": _ids(e for x in site_lines for e in x["basis_evidence_ids"])}
        token_sites.append(_token_site(site, domain, {**cov, **arrays}))
    token = selection_token(tenant_id, scope["ids"], req.from_, req.to, scope["token_k"], None, None, token_sites)
    after = service._fence(tenant_id, req, scope, token)
    start = 0 if after is None else resume_after([x["_key"] for x in lines], after)
    page = lines[start:start + req.limit]
    last = page[-1] if start + req.limit < len(lines) else None
    states = [cov["state"] for _, domain, cov, _ in per_site if domain != NOT_APPLICABLE]
    empty = not scope["sites"]
    status = EMPTY_SCOPE if empty else _status(scope["historical"], states)
    counts = {e: sum(1 for x in lines if x["eligibility"] == e) for e in (ELIGIBLE, UNPRICED)}
    summary: dict[str, Any] = {"eligible_line_count": counts[ELIGIBLE], "unpriced_line_count": counts[UNPRICED],
                               "withheld_line_count": len(lines) - counts[ELIGIBLE] - counts[UNPRICED],
                               "estate_total": None, "estate_total_state": "NO_ESTATE_TOTAL"}
    if scope["historical"]:
        summary["as_of"] = wire_time(k)
    covered_count = sum(1 for s in states if s in COVERED)
    body = service._envelope(FINANCIALS_SCHEMA, tenant_id, req, scope, covered_count, status,
                             {"state": EMPTY if empty else _coverage_state([c["state"] for _, _, c, _ in per_site]),
                              "sites": [_coverage_site(site, cov) for site, _, cov, _ in per_site]})
    body.update({"summary": summary, "order": FINANCIALS_ORDER, "total_count": len(lines),
                 "rows": [{k2: v for k2, v in x.items() if not k2.startswith("_")} for x in page],
                 "groups": [] if empty else groups, "exclusions": [] if empty else exclusions,
                 "diagnostics": [] if empty else diagnostics,
                 "next_cursor": None if last is None else service._cursor(tenant_id, req, scope, token, *last["_key"]),
                 "selection_token": token})
    return body
