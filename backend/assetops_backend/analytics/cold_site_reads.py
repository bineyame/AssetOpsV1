"""W2-04 commit 3: the five cold Site reads (`.agent/W2-04-build-spec.md` "Five API reads", "Selection,
projection and capability", the commit-3 Architect ruling on source contact and the dry-read table).

`ColdSiteReadService` is pure composition: it never imports a SQL driver. Every part of one response is read on
the single REPEATABLE READ connection that `ColdReadService.within` opens (W2-03 snapshot, envelope, temperature,
backup chain, current Findings, basis revisions, accepted records, source facts, gateway diagnostics) and the cold
consequence store's caller-connection heads and pending work. A display-meant field never carries a raw machine
code: money reasons and limits go through `financials.cold_consequence.SCREEN_WORDING`/`screen_sentences`.
A field whose content or shape the spec does not give is left out (see `.agent/W2-04-phase-handoff.md` Run 5).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from urllib.parse import quote, urlencode
from uuid import UUID

from assetops_backend.analytics import cold
from assetops_backend.analytics.cold_reads import (
    DEFAULT_LIMIT,
    NO_SELECTION_NOTE,
    ColdCursorRefused,
    decode_cursor,
    encode_cursor,
)
from assetops_backend.evidence.gateway_access import FRESHNESS_CADENCES
from assetops_backend.evidence.source_health import clock_trust
from assetops_backend.financials.cold_consequence import SCREEN_WORDING, screen_sentences
from assetops_backend.sites.binding_roles import COLD_ROLES_1

EXC, START = cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC
CAPABILITIES = ("TEMPERATURE_POINT", "EXCURSION_BOUNDS", "BACKUP_START_RESULT", "TRANSFER_POSITION",
                "COOLING_RESPONSE", "PRODUCT_EXPOSURE")
POLICY_ROLES = ("cold_policy_low", "cold_policy_high")
#: Required roles per capability claim, from the spec's capability predicates and `cold-roles-1`.
REQUIRED_ROLES: dict[str, tuple[str, ...]] = {
    "TEMPERATURE_POINT": (cold.PROBE_ROLE,),
    "EXCURSION_BOUNDS": (cold.PROBE_ROLE, *POLICY_ROLES),
    "BACKUP_START_RESULT": (cold.START_ROLE,),
    "TRANSFER_POSITION": (cold.TRANSFER_ROLE,),
    "COOLING_RESPONSE": (cold.COMPRESSOR_ROLE, cold.PROBE_ROLE),
    "PRODUCT_EXPOSURE": (cold.PROBE_ROLE, *POLICY_ROLES),
}
#: W2-03 causal step -> the `cold-roles-1` role whose accepted record observes it.
STEP_ROLES = {"GRID": cold.GRID_EVENT_ROLE, "START_REQUEST": cold.START_ROLE, "START_RESULT": cold.START_ROLE,
              "GENERATOR": cold.GENERATOR_STATE_ROLE, "TRANSFER": cold.TRANSFER_ROLE, "BUS": cold.BUS_ROLE,
              "COMPRESSOR": cold.COMPRESSOR_ROLE, "PROBE": cold.PROBE_ROLE}
ROLE_ORDER = {role.role: n for n, role in enumerate(COLD_ROLES_1)}
MISSING_KEYS = ("cold_stock_quantity", "cold_stock_unit_value", "cold_exposure_rule")
NOT_INCLUDED = ("STOCK_VALUE_UNDECLARED", "EXPOSURE_RULE_UNAPPROVED", "SPOILAGE_UNPROVED", "REPAIR_COST_ABSENT")
PROVED_LEVELS = ("OBSERVED", "BOUNDED")
STARTED = ("OBSERVED_SUCCESS", "OBSERVED_FAILURE")

# Spec "Exact in-panel copy": the pending statement; a failed attempt uses the ruled `COLD_RECOMPUTE_FAILED` copy.
PENDING_COPY = "New evidence is waiting to be assessed"
RECORD_TARGET_UNAVAILABLE = "Analysis view not available for this cold record"
POLICY_REVISION_UNRESOLVED = "No single effective Foundation revision covers this window's policy."

# Commit-3 Architect ruling, source contact: each UNKNOWN cause carries its own limitation.
CONTACT_NO_DIAGNOSTIC = "No gateway diagnostic was received by the window end and the evidence cutoff."
CONTACT_NOT_REPORTED = "The selected gateway diagnostic does not report this source."
CONTACT_NO_CADENCE = "The gateway has no usable declared diagnostic cadence."
CONTACT_CLOCK = "The gateway clock is not verified, so the reported contact time cannot be trusted."
CONTACT_AFTER_WINDOW = "The reported contact time is after the window end."


def _plain(value: Any) -> Any:
    return cold.plain(value)


def _at(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value.replace("Z", "+00:00"))


def _joined(sentences) -> str | None:
    out = [x for x in sentences if x]
    return " ".join(out) if out else None


def source_contact(diagnostic: dict[str, Any] | None, source_id: UUID, to: datetime) -> tuple[str, str | None]:
    """Commit-3 Architect ruling: `RECENT|STALE|NEVER|UNKNOWN` and its limitation, from only the selected
    diagnostic's explicit `last_device_contact_by_source[source_id]`, judged at the selected window end `to`."""
    if diagnostic is None:
        return "UNKNOWN", CONTACT_NO_DIAGNOSTIC
    contacts: dict[str, Any] = {}
    for key, value in (diagnostic.get("contacts") or {}).items():
        try:
            contacts[str(UUID(str(key)))] = value
        except ValueError:
            continue
    key = str(source_id)
    if key not in contacts:
        return "UNKNOWN", CONTACT_NOT_REPORTED
    raw = contacts[key]
    if raw is None:
        return "NEVER", None
    cadence = diagnostic.get("cadence_seconds")
    if not isinstance(cadence, int) or isinstance(cadence, bool) or cadence <= 0:
        return "UNKNOWN", CONTACT_NO_CADENCE
    if clock_trust(diagnostic.get("clock_offset_ms"))[0] != "WITHIN_TOLERANCE":
        return "UNKNOWN", CONTACT_CLOCK
    try:
        at = _at(str(raw))
    except ValueError:
        at = None
    if at is None or at.tzinfo is None:
        return "UNKNOWN", CONTACT_CLOCK
    if at > to:
        return "UNKNOWN", CONTACT_AFTER_WINDOW
    return ("RECENT" if to - at <= timedelta(seconds=FRESHNESS_CADENCES * cadence) else "STALE"), None


class ColdSiteReadService:
    def __init__(self, reads: Any, consequences: Any) -> None:
        self._reads, self._consequences = reads, consequences

    # --- shared ----------------------------------------------------------------------------------------------

    def _selected(self, c, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        snap = self._reads.selection_on(c, t, s, code, lo, hi, known_at)
        if known_at is not None and snap["watermark"] is not None and known_at > snap["watermark"]:
            raise ColdCursorRefused(422, "COLD_TIME_INVALID",
                                    "'known_at' is later than the latest committed evidence.")
        return snap

    @staticmethod
    def _query(snap: dict[str, Any]) -> str:
        pairs = [(k, _plain(snap[v])) for k, v in (("from", "lo"), ("to", "hi"), ("known_at", "known"))
                 if snap[v] is not None]
        return "?" + urlencode(pairs) if pairs else ""

    def _link(self, snap: dict[str, Any], suffix: str) -> str:
        return f"/api/sites/{quote(snap['code'], safe='')}/cold/{suffix}{self._query(snap)}"

    def _created(self, c, snap: dict[str, Any], analytic: str) -> dict[str, Any] | None:
        sel = snap["selected"].get(analytic)
        if sel is None:
            return None
        cache = snap.setdefault("basis_revisions", {})
        if analytic not in cache:
            cache[analytic] = self._reads.basis_revisions_on(c, snap["t"], snap["s"], sel.revision_id)
        return cache[analytic]

    def _as_of(self, c, snap, analytic: str) -> str | None:
        basis = self._created(c, snap, analytic)
        return _plain(snap["known"]) if basis is None else _plain(basis["created_at"])

    @staticmethod
    def _limits(snap, analytic: str) -> str | None:
        sel = snap["selected"].get(analytic)
        return NO_SELECTION_NOTE if sel is None else _joined(sel.result.get("limitations") or ())

    # --- money -----------------------------------------------------------------------------------------------

    def _money(self, c, snap: dict[str, Any], findings: list[dict[str, Any]]) -> dict[str, Any]:
        t, s = snap["t"], snap["s"]
        heads = self._consequences.cold_heads_on(c, t, s, [i["revision_id"] for i in findings]) \
            if findings else []
        pending = self._consequences.cold_pending_on(c, t, s, snap["lo"], snap["hi"]) \
            if snap["lo"] is not None else []
        failed = any(p.get("last_outcome") == "FAILED" for p in pending)
        withheld = snap["state"] == "PENDING_RECOMPUTE" or bool(pending)
        hold = SCREEN_WORDING["COLD_RECOMPUTE_FAILED"] if failed else PENDING_COPY
        groups: dict[str, dict[str, Any]] = {}
        for head in heads:
            if head["kind"] != "PRODUCT_EXPOSURE":
                continue
            held = groups.get(head["overlap_group"])
            if held is None or (head["created_at"], str(head["id"])) > (held["created_at"], str(held["id"])):
                groups[head["overlap_group"]] = head
        counted = [groups[g] for g in sorted(groups)]
        return {"heads": heads, "counted": counted, "withheld": withheld, "hold": hold}

    def _consequence_row(self, head: dict[str, Any], money: dict[str, Any]) -> dict[str, Any]:
        state = "WITHHELD" if money["withheld"] else head["state"]
        reason = money["hold"] if money["withheld"] else SCREEN_WORDING.get(head["reason"])
        return {
            "id": str(head["id"]), "kind": head["kind"], "state": state,
            "quantity_bounds": {"low": _plain(head["quantity_low"]), "high": _plain(head["quantity_high"])},
            "quantity_unit": head["quantity_unit"],
            "amount_bounds": {"low": None, "high": None}, "currency": None,
            "reason": reason, "overlap_group": head["overlap_group"],
            "as_of": _plain(head["created_at"]), "limitation": _joined(screen_sentences(head["limitation"])),
        }

    # --- /overview -------------------------------------------------------------------------------------------

    def overview(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            snap = self._selected(c, t, s, code, lo, hi, known_at)
            body = self._reads.envelope_on(snap, (EXC, START))
            temp = self._reads.temperature_on(c, t, s, code, lo, hi, known_at)
            back = self._reads.backup_on(c, t, s, code, lo, hi, known_at)
            exc, st = snap["selected"].get(EXC), snap["selected"].get(START)
            known = _plain(snap["known"])
            exc_as_of, st_as_of = self._as_of(c, snap, EXC), self._as_of(c, snap, START)
            findings = self._reads.current_findings_on(c, snap)
            money = self._money(c, snap, findings)
            return {
                **body,
                "status": {"state": exc.result.get("state") if exc else "UNKNOWN",
                           "claim_level": exc.result.get("claim_level") if exc else None,
                           "as_of": exc_as_of, "limitation": self._limits(snap, EXC)},
                "objective": self._objective(c, snap, exc),
                "temperature_summary": self._temperature_summary(snap, temp, exc, exc_as_of),
                "backup_summary": self._backup_summary(snap, back, st, st_as_of),
                "causal_strip": self._causal_strip(back, st, known),
                "findings": {"count": len({i["finding_id"] for i in findings}),
                             "items": [{"finding_id": i["finding_id"], "revision_id": i["revision_id"],
                                        "title": i["title"], "claim_level": i["claim_level"],
                                        "link": i["links"]["finding"]} for i in findings],
                             "as_of": max((i["as_of"] for i in findings), default=known),
                             "limitation": None if snap["selected"] else NO_SELECTION_NOTE},
                "consequence_summary": self._consequence_summary(snap, money),
                "links": {"temperature": self._link(snap, "temperature"),
                          "backup": self._link(snap, "backup-chain"),
                          "findings": self._link(snap, "findings"),
                          "evidence": self._link(snap, "evidence"),
                          "analysis": self._link(snap, "evidence/analysis"),
                          "financials": self._link(snap, "financials")},
            }
        return self._reads.within(work)

    def _objective(self, c, snap, exc) -> dict[str, Any]:
        pol = (exc.result.get("policy") or {}) if exc else {}
        as_of, limitation = _plain(snap["known"]), NO_SELECTION_NOTE if exc is None else None
        if exc is not None:
            lo = snap["lo"]
            covering = [f for f in self._created(c, snap, EXC)["foundations"]
                        if f[1] <= lo and (f[2] is None or f[2] > lo)]
            if len(covering) == 1:
                as_of = _plain(covering[0][1])
            else:
                limitation = POLICY_REVISION_UNRESOLVED
        return {"policy_low_deg_c": pol.get("policy_low"), "policy_high_deg_c": pol.get("policy_high"),
                "room_asset_id": pol.get("room_asset_id"), "as_of": as_of, "limitation": limitation}

    @staticmethod
    def _temperature_summary(snap, temp, exc, as_of) -> dict[str, Any]:
        points = temp.get("points") or []
        latest = points[-1] if points else None
        return {"latest_deg_c": latest["value"] if latest else None, "latest_at": latest["at"] if latest else None,
                "coverage": temp.get("coverage") or {"known_points": None, "expected_points": None, "ratio": None},
                "episode_count": len(temp.get("excursions") or ()),
                "claim_level": exc.result.get("claim_level") if exc else None,
                "as_of": as_of, "limitation": ColdSiteReadService._limits(snap, EXC)}

    @staticmethod
    def _latest_chain(st) -> str | None:
        chains = (st.result.get("chains") or []) if st else []
        if not chains:
            return None
        return max(chains, key=lambda ch: (ch["anchor_time"], ch["correlation_id"]))["correlation_id"]

    def _backup_summary(self, snap, back, st, as_of) -> dict[str, Any]:
        chains = back.get("chains") or []
        results = [ch["result"] for ch in chains]
        return {"attempts": len(chains), "observed_success": results.count("OBSERVED_SUCCESS"),
                "observed_failure": results.count("OBSERVED_FAILURE"),
                "unknown": len(results) - results.count("OBSERVED_SUCCESS") - results.count("OBSERVED_FAILURE"),
                "latest_chain_id": self._latest_chain(st), "as_of": as_of,
                "limitation": self._limits(snap, START)}

    def _causal_strip(self, back, st, known) -> list[dict[str, Any]]:
        latest = self._latest_chain(st)
        chain = next((ch for ch in back.get("chains") or () if ch["correlation_id"] == latest), None)
        if chain is None:
            return []
        return [{"step": x["kind"], "state": x["state"], "at": x["at"], "evidence_id": x["evidence_id"],
                 "as_of": x["as_of"] or known, "limitation": x["limitation"]} for x in chain["steps"]]

    def _consequence_summary(self, snap, money) -> dict[str, Any]:
        state = "WITHHELD" if money["withheld"] else "UNKNOWN"
        head = money["counted"][0] if money["counted"] else None
        if head is None:
            return {"state": state, "quantity": {"low": None, "high": None, "unit": None},
                    "amount": {"low": None, "high": None, "currency": None}, "overlap_group": None,
                    "as_of": _plain(snap["known"]),
                    "limitation": money["hold"] if money["withheld"] else (
                        None if snap["selected"] else NO_SELECTION_NOTE)}
        row = self._consequence_row(head, money)
        return {"state": row["state"],
                "quantity": {**row["quantity_bounds"],
                             "unit": head["quantity_unit"] if head["quantity_unit"] == "degC_min" else None},
                "amount": {"low": None, "high": None, "currency": None}, "overlap_group": head["overlap_group"],
                "as_of": row["as_of"], "limitation": _joined([row["reason"], row["limitation"]])}

    # --- /evidence -------------------------------------------------------------------------------------------

    def evidence(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            snap = self._selected(c, t, s, code, lo, hi, known_at)
            body = self._reads.envelope_on(snap, (EXC, START))
            links = {"analysis": self._link(snap, "evidence/analysis"),
                     "temperature": self._link(snap, "temperature"), "backup": self._link(snap, "backup-chain")}
            if not snap["selected"]:
                return {**body, "capabilities": [], "sources": [], "links": links}
            return {**body, "capabilities": self._capabilities(c, snap), "sources": self._sources(c, snap),
                    "links": links}
        return self._reads.within(work)

    def _observed_roles(self, c, snap) -> set[str]:
        ids = sorted({e for sel in snap["selected"].values() for e in sel.evidence_ids})
        roles = {r["role"] for r in self._reads.accepted_on(c, snap["t"], snap["s"], ids)}
        exc = snap["selected"].get(EXC)
        pol = (exc.result.get("policy") or {}) if exc else {}
        if pol.get("policy_low") is not None:
            roles.add("cold_policy_low")
        if pol.get("policy_high") is not None:
            roles.add("cold_policy_high")
        return roles

    def _capabilities(self, c, snap) -> list[dict[str, Any]]:
        exc, st = snap["selected"].get(EXC), snap["selected"].get(START)
        er = exc.result if exc else {}
        chains = (st.result.get("chains") or []) if st else []
        observed = self._observed_roles(c, snap)
        known_points = er.get("known_points") or 0
        ratio = er.get("coverage")
        long_gap = any(_at(g["end"]) - _at(g["start"]) > cold.MAX_BRIDGE for g in er.get("gaps") or ())
        policy = all(r in observed for r in POLICY_ROLES)
        contradictory = er.get("state") == "CONTRADICTORY"

        def steps(name: str) -> list[str]:
            return [x["state"] for ch in chains for x in ch["steps"] if x["step"] == name]

        bounds_ok = (policy and known_points >= 2 and ratio is not None
                     and Decimal(str(ratio)) >= cold.COVERAGE_NEEDED and not long_gap)
        states: dict[str, str] = {}
        states["TEMPERATURE_POINT"] = ("CONTRADICTORY" if contradictory else
                                       "SUPPORTED" if known_points >= 1 else "UNAVAILABLE")
        states["EXCURSION_BOUNDS"] = ("CONTRADICTORY" if contradictory else "SUPPORTED" if bounds_ok else
                                      "UNAVAILABLE" if known_points == 0 or not policy else "LIMITED")
        results = [ch["result"] for ch in chains]
        states["BACKUP_START_RESULT"] = (
            "CONTRADICTORY" if "CONTRADICTORY" in results or "CONTRADICTORY" in steps("START_RESULT") else
            "SUPPORTED" if any(r in STARTED for r in results) else "LIMITED" if chains else "UNAVAILABLE")
        transfer = steps("TRANSFER")
        states["TRANSFER_POSITION"] = ("CONTRADICTORY" if "CONTRADICTORY" in transfer else
                                       "SUPPORTED" if "OBSERVED" in transfer else "UNAVAILABLE")
        compressor = cold.COMPRESSOR_ROLE in observed
        states["COOLING_RESPONSE"] = (
            "CONTRADICTORY" if "CONTRADICTORY" in steps("COMPRESSOR") else
            "SUPPORTED" if compressor and known_points >= 2 else
            "LIMITED" if compressor or known_points >= 1 else "UNAVAILABLE")
        excursions = er.get("excursions") or []
        eligible = any(x.get("exposure_finding") and x.get("claim_level") in PROVED_LEVELS for x in excursions)
        states["PRODUCT_EXPOSURE"] = ("CONTRADICTORY" if contradictory else
                                      "SUPPORTED" if eligible and bounds_ok else
                                      "LIMITED" if excursions else "UNAVAILABLE")
        probe_coverage = {"known_points": er.get("known_points"), "expected_points": er.get("expected_points"),
                          "ratio": ratio}
        event_coverage = {"known_points": None, "expected_points": None, "ratio": None}
        out = []
        for claim in CAPABILITIES:
            analytic = START if claim in ("BACKUP_START_RESULT", "TRANSFER_POSITION", "COOLING_RESPONSE") else EXC
            required = list(REQUIRED_ROLES[claim])
            state = states[claim]
            out.append({"claim": claim, "state": state, "required_roles": required,
                        "missing_roles": [r for r in required if r not in observed],
                        "coverage": event_coverage if claim in ("BACKUP_START_RESULT", "TRANSFER_POSITION")
                        else probe_coverage,
                        "as_of": self._as_of(c, snap, analytic),
                        "limitation": None if state == "SUPPORTED" else self._limits(snap, analytic)})
        return out

    def _sources(self, c, snap) -> list[dict[str, Any]]:
        t, s, lo, hi, known = snap["t"], snap["s"], snap["lo"], snap["hi"], snap["known"]
        bindings = sorted({b for a in (EXC, START) if a in snap["selected"]
                           for b in self._created(c, snap, a)["bindings"]},
                          key=lambda b: (ROLE_ORDER.get(b[1], len(ROLE_ORDER)), b[1], str(b[0])))
        facts = self._reads.source_facts_on(c, t, s, lo, hi, known)
        diagnostics = self._reads.source_contacts_on(c, t, s, [b[2] for b in bindings], min(known, hi))
        out = []
        for source_id, role, gateway_id in bindings:
            count, last = facts.get((source_id, role), (0, None))
            diagnostic = diagnostics.get(gateway_id)
            contact, limitation = source_contact(diagnostic, source_id, hi)
            out.append({"id": str(source_id), "role": role, "contact": contact,
                        "fact_age": None if last is None else max(0, int((hi - last).total_seconds())),
                        "accepted_count": count, "last_accepted_at": _plain(last),
                        "as_of": _plain(diagnostic["received_at"]) if diagnostic else _plain(known),
                        "limitation": limitation})
        return out

    # --- /evidence/analysis ----------------------------------------------------------------------------------

    def analysis(self, t: UUID, s: UUID, code: str, lo, hi, known_at, cursor: str | None,
                 limit: int = DEFAULT_LIMIT) -> dict[str, Any]:
        def work(c):
            snap = self._selected(c, t, s, code, lo, hi, known_at)
            body = self._reads.envelope_on(snap, (EXC, START))
            basis = body["source_provenance"]["basis_sha256"] or "none"
            after = None if cursor is None else decode_cursor(cursor, basis)
            links = {"evidence": self._link(snap, "evidence"), "findings": self._link(snap, "findings")}
            if not snap["selected"]:
                return {**body, "accepted_records": {"items": [], "next_cursor": None}, "claim_rules": [],
                        "links": links}
            cited: dict[str, tuple[str, str | None]] = {}  # evidence ID -> (assessment revision ID, reason)
            for analytic in (EXC, START):
                sel = snap["selected"].get(analytic)
                if sel is None:
                    continue
                reasons = {x["evidence_id"]: x.get("reason") for x in sel.result.get("links") or ()}
                for e in sel.evidence_ids:
                    cited.setdefault(str(e), (str(sel.revision_id), reasons.get(str(e))))
            rows = self._reads.accepted_on(c, t, s, sorted(cited), after, limit)
            page, more = rows[:limit], len(rows) > limit
            items = [{
                "evidence_id": str(r["id"]), "kind": r["record_kind"], "source_time": _plain(r["source_time"]),
                "received_at": _plain(r["received_at"]), "quality": r["quality"], "role": r["role"],
                "exclusion": cited[str(r["id"])][1], "source_id": _plain(r["source_id"]),
                "envelope_sha256": r["envelope_sha256"], "assessment_revision_id": cited[str(r["id"])][0],
                "value_display": r["normalized_value_text"] if r["normalized_value_text"] is not None
                else r["outcome"],
                "unit": r["normalized_unit"], "sent_at": _plain(r["published_at"]),
                "record_target_state": "UNAVAILABLE", "link": None,
                "as_of": _plain(r["received_at"]), "limitation": RECORD_TARGET_UNAVAILABLE,
            } for r in page]
            nxt = encode_cursor(page[-1]["source_time"], page[-1]["id"], basis) if more else None
            return {**body, "accepted_records": {"items": items, "next_cursor": nxt},
                    "claim_rules": self._claim_rules(c, snap), "links": links}
        return self._reads.within(work)

    def _claim_rules(self, c, snap) -> list[dict[str, Any]]:
        out = []
        for analytic in (EXC, START):
            sel = snap["selected"].get(analytic)
            if sel is None:
                continue
            ids = sorted(str(e) for e in sel.evidence_ids)
            roles = {r["role"] for r in self._reads.accepted_on(c, snap["t"], snap["s"], ids)}
            r = sel.result
            pol = r.get("policy") or {}
            if analytic == EXC:
                required = [cold.PROBE_ROLE, *POLICY_ROLES]
                roles |= {k for k, v in (("cold_policy_low", pol.get("policy_low")),
                                         ("cold_policy_high", pol.get("policy_high"))) if v is not None}
            else:
                required = []
                for step in cold.STEPS:
                    role = STEP_ROLES[step]
                    if step == "TRANSFER" and not pol.get("transfer_bound"):
                        continue
                    if role not in required:
                        required.append(role)
            out.append({"rule_id": f"{analytic}/{cold.MODEL_VERSION}",
                        "observed_roles": [x for x in required if x in roles],
                        "missing_roles": [x for x in required if x not in roles],
                        "coverage": {"known_points": r.get("known_points"),
                                     "expected_points": r.get("expected_points"), "ratio": r.get("coverage")},
                        "result": r.get("state"), "as_of": self._as_of(c, snap, analytic),
                        "limitation": _joined(r.get("limitations") or ())})
        return out

    # --- /financials -----------------------------------------------------------------------------------------

    def financials(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            snap = self._selected(c, t, s, code, lo, hi, known_at)
            body = self._reads.envelope_on(snap, (EXC, START))
            links = {"assumptions": self._link(snap, "financial-assumptions"),
                     "findings": self._link(snap, "findings"), "evidence": self._link(snap, "evidence")}
            if not snap["selected"]:
                return {**body, "consequences": [], "not_included": [], "links": links}
            money = self._money(c, snap, self._reads.current_findings_on(c, snap))
            codes = list(NOT_INCLUDED)
            if any(h["reason"] == "SOURCE_GATE_WITHHELD" for h in money["heads"]):
                codes.append("SOURCE_GATE_WITHHELD")
            known = _plain(snap["known"])
            return {**body, "consequences": [self._consequence_row(h, money) for h in money["counted"]],
                    "not_included": [{"code": code_, "text": SCREEN_WORDING.get(code_), "as_of": known,
                                      "limitation": None} for code_ in codes],
                    "links": links}
        return self._reads.within(work)

    # --- /financial-assumptions ------------------------------------------------------------------------------

    def assumptions(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            snap = self._selected(c, t, s, code, lo, hi, known_at)
            body = self._reads.envelope_on(snap, (EXC, START))
            return {**body, "items": [], "missing_keys": list(MISSING_KEYS),
                    "publication_state": "NOT_SUPPORTED_IN_W2", "currency_state": "UNDECLARED",
                    "links": {"financials": self._link(snap, "financials")}}
        return self._reads.within(work)
