"""W3-02 commit 1: the estate Evidence root, `GET /api/estate/evidence`, over the one W3-01 estate snapshot (pure).

Every row, card, gap group and selection-token array is computed from the full authorized selected set before
paging (`.agent/W3-02-build-spec.md` closures 1-5). The snapshot is
`estate/adapters/postgres_evidence_money_read.py`'s bound read: every call it makes runs on the one read-only
REPEATABLE READ estate connection; nothing here opens a connection, reads a page or writes.

Rows, per display capability (closure 1 Q3, closure 4 "W1 day source, cold/EV windows"):
- mini-grid: one `GENERATOR_SUPPORT@YYYY-MM-DD` row per UTC day intersecting `[from, to)`, reduced by Lane A's
  `reduce_day` from every selected interval revision of `ClaimLimitReadService.claim_limit_on`;
- cold-chain / EV charging: four rows per selected stored window (`temperature@<ws>/<we>` ...), from the pinned
  `capabilities_on` facades; a Site with no selected window has four unsuffixed `UNASSESSED` placeholders.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from typing import Any, Callable
from urllib.parse import quote, urlencode

from assetops_backend.analytics import cold, dispatch_v3
from assetops_backend.analytics import claim_limit_read as w1
from assetops_backend.analytics.cold_site_reads import EXC, START
from assetops_backend.ev_site_reads import CLAIMS as EV_CLAIMS, NEXT_EVIDENCE as EV_NEXT, TARIFF_ROLE, EvSiteReads
from assetops_backend.estate.coverage import (
    COLD, COVERED, CURRENT, DOMAIN_OF_SITE_TYPE, EV, HISTORICAL, MINI_GRID, NOT_APPLICABLE, PENDING, STALE, UNKNOWN,
    not_applicable, site_coverage)
from assetops_backend.estate.index import (
    EstateIndexService, _coverage_site, _coverage_state, _status, _token_site)
from assetops_backend.estate.scope import (
    EstateRequest, estate_request, resume_after, selection_token, token_time, wire_time)
from assetops_backend.sites.binding_roles import COLD_ROLES_1, MINIGRID_ROLES

EVIDENCE_SCHEMA = "estate-evidence-1"
EVIDENCE_ORDER = "site_code_key asc, site_id asc, capability_key asc"
EMPTY_SCOPE, EMPTY = "EMPTY_SCOPE", "EMPTY"
FULL, LIMITED, NONE, CONTRADICTORY = "FULL", "LIMITED", "NONE", "CONTRADICTORY"
UNASSESSED = "UNASSESSED"
DOMAIN_LABEL = {MINI_GRID: "mini-grid", COLD: "cold-chain", EV: "EV charging"}
CURRENT_VIEW = "Opens current Site view"
HISTORICAL_AS_OF = "Historical as of {known_at}"
NO_CURRENT_CEILING = "No current ceiling"
Admit = Callable[[str], bool]

#: W2 capability state -> estate readiness (closure 1 "Snapshot, sources and identity").
READINESS = {"SUPPORTED": FULL, "LIMITED": LIMITED, "UNAVAILABLE": NONE, "CONTRADICTORY": CONTRADICTORY}

#: W1 (closure 1 Q3): one display capability per selected UTC day.
W1_KEY, W1_LABEL = w1.CAPABILITY_KEY, "Generator support"
#: Closure 2 Q4: the literal W1 role labels and their source constants.
W1_ROLE_LABEL = {w1.GEN: next(r.label for r in MINIGRID_ROLES if r.role == w1.GEN),
                 **{role: dispatch_v3.LABELS[role] for role in (w1.LOAD, w1.PV, w1.DIS, w1.SOC)}}
W1_GAP_TEXT = {"MISSING_ROLE": ("Missing {label}", "Record {label}"),
               "GENERATOR_UNOBSERVED": ("Generator state not observed", "Record generator state"),
               "POOR_QUALITY": ("Poor quality {label}", "Repair {label} readings"),
               "CONFLICTING": ("Conflicting {label}", "Resolve conflicting {label} records")}

#: Closure 1 Q3: cold display rows as `coldSiteViews.tsx:CAP_ROWS`; each cites its owning analytic only.
COLD_ROWS = (("temperature", "Temperature compliance", ("TEMPERATURE_POINT", "EXCURSION_BOUNDS"), EXC),
             ("backup", "Backup response", ("BACKUP_START_RESULT", "TRANSFER_POSITION"), START),
             ("cooling", "Cooling recovery", ("COOLING_RESPONSE",), START),
             ("exposure", "Product exposure", ("PRODUCT_EXPOSURE",), EXC))
COLD_ROLE_LABEL = {r.role: r.label for r in COLD_ROLES_1}

# c2c (c2-q7): the complete reachable `ColdStep.step` codes of `analytics/cold.py` and their literal plain
# sentences. A stored `Not observed: CODE[, CODE...].` fragment is replaced before it reaches any client field.
COLD_OBSERVATION_WORDS = {
    "GRID": "No record of a grid power loss.",
    "START_REQUEST": "No record of a generator start request.",
    "START_RESULT": "No record of a generator start result.",
    "GENERATOR": "No record of the generator running or failing.",
    "TRANSFER": "No record of power transferring to the generator.",
    "BUS": "No record of the electrical bus state.",
    "COMPRESSOR": "No record of the compressor state.",
    "PROBE": "No record of a room temperature reading.",
}
UNREADABLE_OBSERVATIONS = "Some required observations have no readable description."
_NOT_OBSERVED = re.compile(r"Not observed:([^.]*)\.?")


def plain_limitation(text: str | None, words: dict[str, str] = COLD_OBSERVATION_WORDS) -> str | None:
    """The stored limitation with each `Not observed:` fragment as one plain sentence per code in stored order;
    any other sentence is kept in place. An unexpected or malformed fragment fails closed to one fixed sentence.
    EV passes an empty mapping, so any future EV fragment fails closed until a mapping is approved."""
    if not text:
        return text

    def sentence(m: re.Match[str]) -> str:
        codes = [c.strip() for c in m.group(1).split(",")]
        if m.group(0).endswith(".") and codes and all(c in words for c in codes):
            return " ".join(words[c] for c in codes)
        return UNREADABLE_OBSERVATIONS

    return _NOT_OBSERVED.sub(sentence, text)

#: Closure 1 Q3: EV display rows as `EvSiteViews.tsx:CAP_ROWS`; the other three `CLAIMS` stay in disclosure.
EV_ROWS = (("sessions", "Session outcomes", ("SESSION_OUTCOME",)),
           ("availability", "Connector availability", ("SERVICE_STATE",)),
           ("energy", "Delivered energy", ("DELIVERED_ENERGY",)),
           ("cause", "Cause of interruption", ("FAULT_ASSOCIATION",)))
EV_SUPPORTING = tuple(c[0] for c in EV_CLAIMS if c[0] not in {x for row in EV_ROWS for x in row[2]})
#: Closure 1 Q4: EV typed gaps in `NEXT_EVIDENCE` order (BILLING_GAP excluded), their gap label and the missing
#: roles that make a claim affected by the code.
EV_GAP_LABEL = {"TERMINAL_GAP": "Missing session end report", "METER_GAP": "Missing connector meter intervals",
                "STATUS_GAP": "Missing connector status history",
                "INDEPENDENT_POWER_GAP": "Missing independent power readings",
                "SITE_IMPORT_GAP": "Missing Site import power", "TARIFF_GAP": "Missing EV tariff"}
EV_GAP_ROLES = {"TERMINAL_GAP": {"session_terminal"}, "METER_GAP": {"connector_meter_delta"},
                "STATUS_GAP": {"connector_status"}, "INDEPENDENT_POWER_GAP": {"requested_power", "allocated_limit"},
                "SITE_IMPORT_GAP": {"site_import"}, "TARIFF_GAP": {TARIFF_ROLE}}
EV_GAP_ORDER = tuple(code for code in EV_NEXT if code in EV_GAP_LABEL)

NO_PROVENANCE = {"classification": "UNKNOWN", "state": "UNKNOWN", "source_ids": [], "evidence_ids": [],
                 "basis_sha256": None, "reasons": []}


def _ids(values: Any) -> list[str]:
    return sorted({str(v).lower() for v in values or () if v is not None})


def group_readiness(states: list[str]) -> str:
    """Closure 4: a grouped row is FULL only when every constituent is FULL; otherwise CONTRADICTORY > NONE >
    LIMITED > UNKNOWN. A W2 state outside the reviewed enum is UNKNOWN."""
    mapped = [READINESS.get(s, UNKNOWN) for s in states]
    if mapped and all(m == FULL for m in mapped):
        return FULL
    for state in (CONTRADICTORY, NONE, LIMITED):
        if state in mapped:
            return state
    return UNKNOWN


def _site_href(code: str) -> str:
    return f"/sites/{quote(code, safe='')}"


def site_home_href(code: str, domain: str) -> str:
    """Post-W6 W3-estate Q2/Q9: the Site home every estate row links to. An EV Site opens its EV overview
    (`/sites/{code}/ev`); mini-grid and cold-chain keep the base Site route. `domain` is the estate domain constant
    (`EV`) or the stored Site type (`EV_CHARGING`)."""
    base = _site_href(code)
    return f"{base}/ev" if DOMAIN_OF_SITE_TYPE.get(domain, domain) == EV else base


#: Post-W6 W3-estate Q10: the longest selected window a Site route accepts.
MAX_WINDOW = timedelta(days=31)


def proven_window_query(lo: datetime | None, hi: datetime | None, known: datetime | None,
                        evidence_cutoff: datetime | None, k: datetime, watermark: datetime | None = None,
                        ) -> str | None:
    """Closure 5 B5: the `from`/`to`/`known_at` query of one pinned Site window, only when `known` equals the
    passed Site evidence cutoff and is at or before both the estate cutoff and the committed watermark. None when
    anything is unproved."""
    if (lo is None or hi is None or known is None or evidence_cutoff is None or known != evidence_cutoff
            or known > k or (watermark is not None and known > watermark)):
        return None
    return urlencode([("from", cold.plain(lo)), ("to", cold.plain(hi)), ("known_at", cold.plain(known))])


def finding_window_href(code: str, finding_id: str, lo: datetime | None, hi: datetime | None,
                        known: datetime | None, evidence_cutoff: datetime | None, k: datetime,
                        watermark: datetime | None = None) -> str | None:
    """Post-W6 W3-estate Q4/Q10: a cold/EV Finding's exact Site route over the selected Site window that holds
    it and the proven row-local cutoff; null when unproved, not a forward span, or longer than 31 days. Never
    episode bounds."""
    if lo is None or hi is None or not lo < hi or hi - lo > MAX_WINDOW:
        return None
    query = proven_window_query(lo, hi, known, evidence_cutoff, k, watermark)
    return None if query is None else f"{_site_href(code)}/findings/{quote(str(finding_id), safe='')}?{query}"


def window_links(code: str, domain: str, snap: dict[str, Any] | None, evidence_cutoff: datetime | None,
                 k: datetime) -> dict[str, Any]:
    """Closure 5 B5: a cold/EV row link carries only its own pinned `lo`/`hi` and row-local `known`, and only when
    `known` equals the passed Site evidence cutoff and is at or before both the estate cutoff and the committed
    watermark. Anything unprovable (and every placeholder) is the Site home (EV: `/sites/{code}/ev`), `Opens
    current Site view`."""
    base, home = _site_href(code), site_home_href(code, domain)
    if snap is not None:
        query = proven_window_query(snap.get("lo"), snap.get("hi"), snap.get("known"), evidence_cutoff, k,
                                    snap.get("watermark"))
        if query is not None:
            path = f"{base}/evidence" if domain == COLD else f"{base}/ev/evidence"
            return {"site": home, "site_readiness": f"{path}?{query}", "site_readiness_label": None}
    return {"site": home, "site_readiness": home, "site_readiness_label": CURRENT_VIEW}


def _gap(domain: str, code: str, role: str | None, label: str, step: str) -> dict[str, Any]:
    return {"key": (domain, code, role or ""), "domain": domain, "gap_code": code, "missing_role": role,
            "label": label, "next_step": step}


def w1_gap(code: str, role: str) -> dict[str, Any]:
    label = W1_ROLE_LABEL.get(role, role)  # closure 2 Q4: an unknown typed role uses its exact ID
    text, step = W1_GAP_TEXT[code]
    if code == "GENERATOR_UNOBSERVED" and role != w1.GEN:  # c1 r1 R1: role-specific copy, same typed identity
        text, step = "{label} not observed", "Record {label}"
    return _gap(MINI_GRID, code, role, text.format(label=label), step.format(label=label))


def cold_gap(role: str) -> dict[str, Any]:
    label = COLD_ROLE_LABEL.get(role, role)
    return _gap(COLD, "MISSING_ROLE", role, f"Missing {label}", f"Connect or record {label}")


def ev_gap(code: str) -> dict[str, Any]:
    return _gap(EV, code, None, EV_GAP_LABEL[code], EV_NEXT[code][0])


def _row(site: dict[str, Any], domain: str, key: str, label: str, **values: Any) -> dict[str, Any]:
    row = {"site_id": str(site["site_id"]), "site_code": site["site_code"], "site_name": site["site_name"],
           "domain": domain, "domain_label": DOMAIN_LABEL[domain], "capability_key": key, "capability_label": label,
           "window_start": None, "window_end": None, "raw_state": UNASSESSED, "readiness": UNKNOWN,
           "current_ceiling": None, "ceiling": None, "ceiling_source": "NONE", "next_evidence": None,
           "gap_codes": [], "selected_revision_ids": [], "source_provenance": dict(NO_PROVENANCE),
           "links": {"site": site_home_href(site["site_code"], domain),
                     "site_readiness": site_home_href(site["site_code"], domain),
                     "site_readiness_label": CURRENT_VIEW},
           "disclosure": {"capability_key": key, "constituents": [], "reasons": [], "historical": None},
           "_key": (str(site["site_code_key"]), str(site["site_id"]).lower(), key), "_gaps": [],
           "_cited": [], "_token_cited": [], "_assessments": []}
    row.update(values)
    return row


def _with_gaps(row: dict[str, Any], gaps: list[dict[str, Any]]) -> None:
    """A row's typed gaps; `next_evidence` is the first sorted typed step affecting it (closure 1 Q4)."""
    ordered = sorted({g["key"]: g for g in gaps}.values(), key=lambda g: g["key"])
    row["_gaps"] = ordered
    row["gap_codes"] = sorted({g["gap_code"] for g in ordered})
    row["next_evidence"] = ordered[0]["next_step"] if ordered else None


def _historical(row: dict[str, Any], k: datetime, readiness: str, statements: list[str] | None = None) -> None:
    """0b ruling M3, applied to every domain: IDs kept, every current claim cleared; CONTRADICTORY only from a
    selected as-of conflict, else UNKNOWN. Historical reasons stay in labelled disclosure, never current gaps."""
    row.update(raw_state=HISTORICAL, readiness=CONTRADICTORY if readiness == CONTRADICTORY else UNKNOWN,
               current_ceiling=None, ceiling=None, ceiling_source="NONE", next_evidence=None, gap_codes=[], _gaps=[])
    row["disclosure"]["historical"] = {
        "label": HISTORICAL_AS_OF.format(known_at=wire_time(k)),
        "statements": statements or [HISTORICAL_AS_OF.format(known_at=wire_time(k)), NO_CURRENT_CEILING]}


def _unique_reasons(reasons: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in reasons:
        if r not in out:
            out.append(r)
    return out


# --- mini-grid -------------------------------------------------------------------------------------------------

def mini_grid_rows(snap: Any, t: Any, site: dict[str, Any], req: EstateRequest, k: datetime) -> list[dict[str, Any]]:
    s = site["site_id"]
    rows = []
    for day in snap.dispatch_days(t, s, req.from_, req.to, k):
        revision = (day.get("window_assessment_revision_id")
                    if day.get("available") and day.get("selection") is not None else None)
        projection = snap.claim_limit_on(t, s, day["day"], revision, k,
                                         "historical" if snap.basis_historical else "live")
        reduced = w1.reduce_day(projection)
        raw = {str(i["assessment_revision_id"]): [dict(r) for r in i["reasons"]]
               for i in (projection["intervals"] if projection["available"] else [])}
        constituents = [{**c, "reasons": raw.get(str(c["assessment_revision_id"]), [])}
                        for c in reduced["interval_ceilings"]]
        refusal = [dict(r) for r in projection.get("reasons") or () if r["code"] != w1.HISTORICAL_SELECTION_UNAVAILABLE
                   and not projection["available"]]
        key = f"{W1_KEY}@{day['day'].isoformat()}"
        row = _row(site, MINI_GRID, key, W1_LABEL, window_start=wire_time(day["window_start"]),
                   window_end=wire_time(day["window_end"]))
        row["disclosure"].update(
            constituents=constituents,
            window_assessment_revision_id=None if reduced["window_assessment_revision_id"] is None
            else str(reduced["window_assessment_revision_id"]),
            reasons=[*reduced["reasons"], *refusal] or list(projection.get("reasons") or ()))
        if not projection["available"]:  # closure 1 Q1: unreconstructable -> UNKNOWN, no IDs fabricated
            row.update(raw_state=UNKNOWN)
        elif revision is None:
            row.update(raw_state=UNASSESSED)
        else:
            assessments = _ids(reduced["assessment_revision_ids"])
            row.update(selected_revision_ids=assessments, _cited=_ids(reduced["accepted_evidence_ids"]),
                       _assessments=assessments + _ids([reduced["window_assessment_revision_id"]]))
            if snap.basis_historical or reduced["currentness"] == w1.HISTORICAL:  # c1-q1: the estate basis
                stated = reduced["historical_statements"]  # c1 r1 L3: the estate's canonical `known_at` copy
                _historical(row, k, reduced["state"], None if not stated else [
                    HISTORICAL_AS_OF.format(known_at=wire_time(k)), NO_CURRENT_CEILING, *stated[2:]])
                row["disclosure"]["historical"]["gaps"] = [
                    {k2: v for k2, v in w1_gap(g["gap_code"], g["missing_role"]).items() if k2 != "key"}
                    for g in reduced["historical_gaps"]]
            else:
                current = projection.get("currentness") == CURRENT
                row.update(raw_state=reduced["state"] if current else projection.get("currentness") or UNKNOWN,
                           readiness=reduced["state"])
                if reduced["ceiling_source"] == "W1_CLAIM_LIMIT":
                    row.update(current_ceiling=reduced["ceiling_statement"], ceiling=reduced["current_ceiling"],
                               ceiling_source="W1_CLAIM_LIMIT")
                if current:
                    _with_gaps(row, [w1_gap(g["gap_code"], g["missing_role"]) for g in reduced["gaps"]])
                    row["disclosure"]["reasons"] = _unique_reasons(
                        [*row["disclosure"]["reasons"], *(r for c in constituents for r in c["reasons"])])
                else:  # c1 r1 L2: a non-current day's selected facts and reasons are labelled prior selection
                    row["disclosure"]["prior_selection"] = {
                        "state": reduced["state"], "interval_ceilings": constituents,
                        "reasons": _unique_reasons(r for c in constituents for r in c["reasons"])}
        rows.append(row)
    return rows


# --- cold-chain and EV -----------------------------------------------------------------------------------------

def _window_state(snap: Any, site_state: str, window_state: str | None) -> str:
    if snap.basis_historical:
        return HISTORICAL
    if site_state == PENDING or window_state == PENDING:
        return PENDING
    if site_state == STALE or window_state == STALE:
        return STALE
    # c1 r1 M1: on a live basis a W2 pin `HISTORICAL` is the valid as-of selection at the frozen `known_at`
    # (row-local cutoff earlier than the Site watermark), not an unknown pin.
    return CURRENT if window_state in (CURRENT, HISTORICAL) else UNKNOWN


def _shape_window_row(row: dict[str, Any], state: str, readiness: str, limitations: list[str],
                      source: str, gaps: list[dict[str, Any]], k: datetime) -> None:
    if state == HISTORICAL:
        _historical(row, k, readiness)
        return
    if state != CURRENT:  # pending/stale/unknown: the prior selected row is disclosure history, no current claim
        row.update(raw_state=state, readiness=UNKNOWN)
        row["disclosure"]["prior_selection"] = {"readiness": readiness, "limitation": " ".join(limitations) or None}
        return
    row.update(raw_state=readiness, readiness=readiness)
    if limitations:
        row.update(current_ceiling=" ".join(limitations), ceiling_source=source)
    _with_gaps(row, gaps)


def windowed_rows(snap: Any, t: Any, site: dict[str, Any], domain: str, req: EstateRequest, k: datetime,
                  site_state: str) -> list[dict[str, Any]]:
    s, code = site["site_id"], site["site_code"]
    layout = COLD_ROWS if domain == COLD else EV_ROWS
    evidence_cutoff = snap.evidence_cutoff(t, s, k)
    pinned = [] if evidence_cutoff is None else snap.pinned_windows(t, s, domain, req.from_, req.to,
                                                                    evidence_cutoff, k)
    if not pinned:  # closure 4: four unsuffixed UNKNOWN placeholders, never a zero
        return [_row(site, domain, spec[0], spec[1]) for spec in layout]
    rows = []
    for pin in pinned:
        suffix = f"@{token_time(pin['lo'])}/{token_time(pin['hi'])}"
        links = window_links(code, domain, pin, evidence_cutoff, k)
        state = _window_state(snap, site_state, pin.get("state"))
        if domain == COLD:
            read = snap.cold_capabilities(pin)
            caps = {c["claim"]: c for c in read["capabilities"]}
            for key, label, claims, analytic in COLD_ROWS:
                parts = [caps[c] for c in claims if c in caps]
                revision = read["assessment_revision_ids"].get(analytic)
                row = _row(site, domain, key + suffix, label, window_start=wire_time(pin["lo"]),
                           window_end=wire_time(pin["hi"]), links=links,
                           selected_revision_ids=_ids([revision]), _assessments=_ids([revision]),
                           _cited=_ids(read["evidence_by_analytic"].get(analytic)))
                row["disclosure"]["constituents"] = [
                    {"claim": p["claim"], "state": p["state"], "missing_roles": list(p["missing_roles"]),
                     "limitation": plain_limitation(p["limitation"]), "assessment_revision_id": revision}
                    for p in parts]
                readiness = group_readiness([p["state"] for p in parts])
                limitations = list(dict.fromkeys(plain_limitation(p["limitation"]) for p in parts
                                                 if p["limitation"]))
                gaps = [cold_gap(role) for p in parts for role in p["missing_roles"]]
                _shape_window_row(row, state, readiness, limitations, "COLD_LIMITATION", gaps, k)
                rows.append(row)
        else:
            read = snap.ev_capabilities(pin)
            caps = {c["claim"]: c for c in read["capabilities"]}
            missing = {role for c in read["capabilities"] for role in c["missing_roles"]}
            power = set(caps["POWER_CONSTRAINT"]["missing_roles"]) if "POWER_CONSTRAINT" in caps else set()
            codes = [c for c in EvSiteReads._next_candidates(missing, power, read["unknown_meter"])
                     if c in EV_GAP_LABEL]
            supporting = [{"claim": caps[c]["claim"], "state": caps[c]["state"],
                           "missing_roles": list(caps[c]["missing_roles"]), "limitation": plain_limitation(caps[c]["limitation"], {}),
                           "accepted_evidence_ids": list(caps[c]["accepted_evidence_ids"])}
                          for c in EV_SUPPORTING if c in caps]
            revision = read["assessment_revision_id"]
            for key, label, claims in EV_ROWS:
                parts = [caps[c] for c in claims if c in caps]
                cited = _ids([e for p in parts for e in p["accepted_evidence_ids"]])
                row = _row(site, domain, key + suffix, label, window_start=wire_time(pin["lo"]),
                           window_end=wire_time(pin["hi"]), links=links,
                           selected_revision_ids=_ids([revision]),
                           _assessments=_ids([revision, *read["session_revision_ids"]]),  # c1-q3(5)
                           _cited=cited, _token_cited=_ids([*cited, *read["evidence_ids"]]))  # c1 r1 L1
                row["disclosure"].update(constituents=[
                    {"claim": p["claim"], "state": p["state"], "missing_roles": list(p["missing_roles"]),
                     "limitation": plain_limitation(p["limitation"], {}),
                     "accepted_evidence_ids": list(p["accepted_evidence_ids"]),
                     "assessment_revision_id": revision} for p in parts], supporting_claims=supporting)
                readiness = group_readiness([p["state"] for p in parts])
                limitations = list(dict.fromkeys(plain_limitation(p["limitation"], {}) for p in parts
                                                 if p["limitation"]))
                affected = {r for p in parts for r in p["missing_roles"]}
                gaps = [ev_gap(c) for c in codes if EV_GAP_ROLES[c] & affected
                        or (c == "METER_GAP" and read["unknown_meter"] and "DELIVERED_ENERGY" in claims)]
                _shape_window_row(row, state, readiness, limitations, "EV_LIMITATION", gaps, k)
                rows.append(row)
            window = rows[-len(EV_ROWS):]
            placed = {g["gap_code"] for r in window for g in r["_gaps"]}
            if state == CURRENT:  # a code affecting only supporting claims still groups, unlocking no display row
                window[0]["_window_gaps"] = [ev_gap(c) for c in codes if c not in placed]
    return rows


def group_key_for_partition(category: Any, currency: Any, window_start: Any, window_end: Any, period_kind: Any,
                            assumption_fingerprint: Any, *, beneficiary: str | None = None) -> str:
    """Versioned amendment (shared financial group key): `sha256:` plus lowercase SHA-256 hex of UTF-8 sorted-key
    compact JSON over exactly these six wire values (JSON nulls kept). W3-03 imports this; never hash elsewhere.
    Commercial spec 0.4: a beneficiary other than the category default is added to the hashed payload, so a
    default-beneficiary key stays byte-identical."""
    from assetops_backend.estate.financials import BENEFICIARY_OF_CATEGORY  # lazy: financials imports this module
    payload = {"category": category, "currency": currency, "window_start": window_start, "window_end": window_end,
               "period_kind": period_kind, "assumption_fingerprint": assumption_fingerprint}
    if beneficiary is not None and beneficiary != BENEFICIARY_OF_CATEGORY.get(category):
        payload["beneficiary"] = beneficiary
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


# --- the service -----------------------------------------------------------------------------------------------

def _groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Closure 1 Q4 / 0b ruling: one group per `(domain, gap_code, missing_role)` over the full unpaged rows,
    unioning Site IDs/codes/names and the affected capability keys; sorted by key, Sites by code. No priority."""
    held: dict[tuple, dict[str, Any]] = {}
    for row in rows:
        for gap, unlocks in [*((g, True) for g in row["_gaps"]), *((g, False) for g in row.get("_window_gaps", ()))]:
            group = held.setdefault(gap["key"], {**{k: v for k, v in gap.items() if k != "key"},
                                                 "_sites": {}, "unlocks": set(), "link": None})
            group["_sites"][row["site_id"]] = (row["_key"][0], row["site_code"], row.get("site_name"))
            if unlocks:
                group["unlocks"].add(row["capability_key"])
    out = []
    for key in sorted(held):
        group = held[key]
        sites = sorted(group.pop("_sites").items(), key=lambda item: (item[1][0], item[0]))
        out.append({"domain": group["domain"], "gap_code": group["gap_code"], "missing_role": group["missing_role"],
                    "label": group["label"], "site_ids": [sid for sid, _ in sites],
                    "site_codes": [c for _, (_, c, _) in sites],
                    # c2-q1: the authorized stored Site name, parallel to `site_ids`/`site_codes`, full group.
                    "site_names": [n for _, (_, _, n) in sites], "unlocks": sorted(group["unlocks"]),
                    "next_step": group["next_step"], "link": None})
    return out


def select_evidence_scope(snap: Any, tenant_id: Any, req: EstateRequest,
                          scope: dict[str, Any]) -> tuple[list[tuple], list[dict[str, Any]]]:
    """W3-03 closure 4 B1/B2: every authorized Site's `(site, domain, cov, site_rows)` and the full canonical ordered
    Evidence rows before paging, on the caller's one snapshot and `scope` (moved verbatim from `_evidence`)."""
    k = scope["k"]
    per_site, rows = [], []
    for site in scope["sites"]:
        domain = DOMAIN_OF_SITE_TYPE.get(site["site_type"])
        if domain is None:
            per_site.append((site, NOT_APPLICABLE, not_applicable(), []))
            continue
        cov = site_coverage(snap, tenant_id, site["site_id"], domain, req.from_, req.to, k)
        site_rows = (mini_grid_rows(snap, tenant_id, site, req, k) if domain == MINI_GRID
                     else windowed_rows(snap, tenant_id, site, domain, req, k, cov["state"]))
        for row in site_rows:
            if row["_assessments"]:
                row["source_provenance"] = snap.cited_provenance(tenant_id, site["site_id"], row["_cited"],
                                                                 row["selected_revision_ids"])
        per_site.append((site, domain, cov, site_rows))
        rows += site_rows
    rows.sort(key=lambda r: r["_key"])
    return per_site, rows


class EstateEvidenceService(EstateIndexService):
    """The Evidence root over the shared W3-01 authorization, cutoff, fence, cursor and envelope (no fork)."""

    def evidence(self, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        return self._read(lambda snap: self._evidence(snap, tenant_id, req, admit))

    def financials(self, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        """W3-02 commit 3: the Financials root on the same snapshot/service seam (`estate/financials.py`)."""
        from assetops_backend.estate.financials import financials_body

        return self._read(lambda snap: financials_body(self, snap, tenant_id, req, admit))

    def site_readiness(self, tenant_id: Any, site_code: str, from_: datetime, to: datetime,
                       known_at: datetime | None = None) -> str | None:
        """OUT-B4 (§B.3): the Portfolio's per-Site evidence reduction (`portfolio.evidence_cell_state`) for one
        Site, over `select_evidence_scope` on the same snapshot, scope and cutoff. Nothing is reduced here. None when
        the Site is not in the authorized imported set."""
        from assetops_backend.estate.portfolio import evidence_cell_state

        req = estate_request("evidence", from_, to, known_at)  # addendum 7: the estate window rule, never widened

        def work(snap: Any) -> Any:
            scope = self._scope(snap, tenant_id, req, lambda code: code == site_code)
            per_site, _ = select_evidence_scope(snap, tenant_id, req, scope)
            for _, domain, cov, site_rows in per_site:
                return evidence_cell_state(domain, cov, site_rows, bool(snap.basis_historical))
            return None

        return self._read(work)

    def _evidence(self, snap: Any, tenant_id: Any, req: EstateRequest, admit: Admit) -> dict[str, Any]:
        scope = self._scope(snap, tenant_id, req, admit)
        k = scope["k"]
        per_site, rows = select_evidence_scope(snap, tenant_id, req, scope)
        token_sites = []
        for site, domain, cov, site_rows in per_site:
            arrays = {"selected_finding_revision_ids": [], "selected_action_event_ids": [],
                      "selected_consequence_revision_ids": [], "selected_assumption_revision_ids": [],
                      "selected_assessment_revision_ids": _ids(x for r in site_rows for x in r["_assessments"]),
                      "cited_accepted_evidence_ids": _ids(x for r in site_rows for x in (*r["_cited"], *r["_token_cited"]))}
            token_sites.append(_token_site(site, domain, {**cov, **arrays}))
        token = selection_token(tenant_id, scope["ids"], req.from_, req.to, scope["token_k"], None, None,
                                token_sites)
        after = self._fence(tenant_id, req, scope, token)
        start = 0 if after is None else resume_after([r["_key"] for r in rows], after)
        page = rows[start:start + req.limit]
        last = page[-1] if start + req.limit < len(rows) else None
        states = [cov["state"] for _, domain, cov, _ in per_site if domain != NOT_APPLICABLE]
        empty = not scope["sites"]
        status = EMPTY_SCOPE if empty else _status(scope["historical"], states)
        coverage_state = EMPTY if empty else _coverage_state([cov["state"] for _, _, cov, _ in per_site])
        basis_status = EMPTY_SCOPE if empty else _status(snap.basis_historical, states)  # c1 r1 L4: page one's mode
        complete = empty or (basis_status == CURRENT and coverage_state == "COMPLETE")
        counts = {r: sum(1 for x in rows if x["readiness"] == r) for r in (FULL, LIMITED, NONE, UNKNOWN)}
        contradictory = any(r["readiness"] == CONTRADICTORY for r in rows)
        summary: dict[str, Any] = {
            "limited_site_count": (len({r["site_id"] for r in rows if r["readiness"] == LIMITED})
                                   if complete and not contradictory else None),
            "priority_gap_count": None, "unsupported_claim_count": None, "capability_count": len(rows),
            "full_count": counts[FULL] if complete else None, "limited_count": counts[LIMITED] if complete else None,
            "none_count": counts[NONE] if complete else None, "unknown_count": counts[UNKNOWN] if complete else None}
        if scope["historical"]:  # W3-01 q12 ruling 1: a HISTORICAL response carries `as_of`
            summary["as_of"] = wire_time(k)
        covered = sum(1 for s in states if s in COVERED)
        body = self._envelope(EVIDENCE_SCHEMA, tenant_id, req, scope, covered, status,
                              {"state": coverage_state,
                               "sites": [_coverage_site(site, cov) for site, _, cov, _ in per_site]})
        body.update({"summary": summary, "order": EVIDENCE_ORDER, "total_count": len(rows),
                     "rows": [{k2: v for k2, v in r.items() if not k2.startswith("_")} for r in page],
                     "gaps": _groups(rows),
                     "next_cursor": None if last is None else self._cursor(tenant_id, req, scope, token,
                                                                          *last["_key"]),
                     "selection_token": token})
        return body
