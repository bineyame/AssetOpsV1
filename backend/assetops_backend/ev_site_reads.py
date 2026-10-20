"""W2-07 commit 3: the five selected EV Site reads (`.agent/W2-07-build-spec.md` "Five selected reads", "Commits 2-3",
concrete-artifact closure section 2, the post-W2-06 reconciliation and q1-q4).

A pure composition over injected collaborators: `reads` is W2-06's `EvReadService` (its own snapshot, currentness,
envelope, denominator, provenance, completeness and Finding IDs, called on one caller connection) and `money` is the
SELECT-only `EvMoneyReads` of the consequence adapter. Every route opens exactly one read-only repeatable-read
transaction; the public envelope is W2-06's, unchanged, with W2-07 fields alongside it.

q4: one current-revision selector for all five routes. UNKNOWN (no exact selection) -> no consequence; HISTORICAL
(explicit earlier cutoff) and PENDING_RECOMPUTE (overlapping job) -> no current amount, stored rows only as labelled
`Historical scenario` history; CURRENT -> derive the exact basis on this connection (commit-2 rules + pure
`ev_money.derive`) and select only the stored revision with that basis; a derived basis with no stored row is the
read guard `WITHHELD/STALE_BASIS` (never inserted).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

from assetops_backend.analytics.ev import plain
from assetops_backend.financials import ev_money as em

NO_MONEY = "No gross tariff scenario assessed."
HISTORY_LABEL = "Historical scenario"
NOT_INCLUDED = ["lost_sales", "collections", "margin", "repair", "warranty"]
#: q1 R5/R6 visible copy per (guard or stored) reason.
MONEY_COPY = {
    "HISTORICAL_CURRENT_CLAIM": HISTORY_LABEL,
    em.ERROR_PENDING: "New evidence is being assessed. The previous result may change.",
    em.SOURCE_GATE: "EV source or binding is unverified; session outcomes cannot be assessed.",
    em.CONTRADICTORY: "Accepted EV records conflict; no current gross tariff estimate.",
    "STALE_BASIS": "The gross tariff scenario is being refreshed.",
    em.INCOMPLETE: "Delivered energy is incomplete for pricing; partial metered energy is shown separately.",
    em.TARIFF_MISSING: "No published EV tariff covers the eligible delivery.",
    em.PRICE_GAP: "One tariff revision does not cover all eligible delivery intervals.",
    em.ELIGIBLE: "Gross tariff scenario; not cash collected.",
}
#: Public claim vocabulary role -> accepted binding role (`sites/binding_roles.EV_ROLES_1`).
ROLE_OF = {"session_event": "ev_session_event", "connector_meter_delta": "ev_connector_energy",
           "connector_status": "ev_connector_state", "fault_event": "ev_connector_fault",
           "site_import": "ev_site_import", "requested_power": "ev_requested_power",
           "allocated_limit": "ev_allocated_limit"}
PUBLIC_ROLE = {v: k for k, v in ROLE_OF.items()}
TARIFF_ROLE = em.TARIFF_KEY
#: (claim, required public roles, roles whose accepted IDs the row cites, limitation, highest state allowed).
CLAIMS = (
    ("SESSION_OUTCOME", ("session_event",), ("session_event",), None, "SUPPORTED"),
    ("SERVICE_STATE", ("connector_status",), ("connector_status",), "Availability is not assessed.", "LIMITED"),
    ("DELIVERED_ENERGY", ("session_event", "connector_meter_delta"), ("connector_meter_delta",), None, "SUPPORTED"),
    ("FAULT_ASSOCIATION", ("session_event", "fault_event"), ("fault_event",), "Cause is not established.",
     "LIMITED"),
    ("SITE_POWER_CONTEXT", ("site_import",), ("site_import",), None, "SUPPORTED"),
    ("POWER_CONSTRAINT", ("site_import", "requested_power", "allocated_limit"),
     ("site_import", "requested_power", "allocated_limit"), None, "LIMITED"),
    ("GROSS_TARIFF_SCENARIO", ("connector_meter_delta", TARIFF_ROLE), ("connector_meter_delta",),
     "Gross scenario only.", "SUPPORTED"),
)
NEXT_EVIDENCE = {
    "TERMINAL_GAP": ("Recover the missing session end report", "Needed before a session outcome is complete.",
                     "analysis"),
    "METER_GAP": ("Recover connector meter intervals", "Needed before delivered energy is complete.", "analysis"),
    "STATUS_GAP": ("Recover connector status history", "Needed before connector availability can be assessed.",
                   "analysis"),
    "SITE_IMPORT_GAP": ("Record Site import power", "Needed for Site power context.", "analysis"),
    "TARIFF_GAP": ("Publish an EV gross tariff", "Needed before a gross tariff scenario can be estimated.",
                   "financials"),
    "BILLING_GAP": ("Connect billing records", "Needed before any amount can be stated as collected.",
                    "financials"),
}
KIND_TEXT = {"EV_SESSION_START": "Session started", "EV_SESSION_END": "Session ended",
             "EV_SESSION_ABORT": "Session aborted", "EV_CONNECTOR_FAULT": "Connector fault",
             "EV_CONNECTOR_CLEAR": "Connector fault cleared"}
SOURCE_UNVERIFIED_NOTE = "Source or binding unverified for this record."


def _dec(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _ratio(known: int, expected: int) -> str:
    return "0" if expected <= 0 or known <= 0 else format((Decimal(known) / Decimal(expected)).normalize(), "f")


def _utc_words(at: datetime) -> str:
    return at.strftime("%Y-%m-%d %H:%M")


class EvSiteReads:
    def __init__(self, reads: Any, money: Any,
                 derive: Callable[[em.EvMoneyBasis], em.EvConsequence | None] = em.derive) -> None:
        self._reads, self._money, self._derive = reads, money, derive

    def dispose(self) -> None:
        self._reads.dispose()

    # --- the shared snapshot and money selector ----------------------------------------------------------------

    def _ctx(self, c, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        snap, body = self._reads.open_on(c, t, s, code, lo, hi, known_at)
        ctx = {"c": c, "t": t, "s": s, "code": code, "snap": snap, "body": body}
        ctx["money"] = self._select(ctx)
        return ctx

    def _select(self, ctx: dict[str, Any]) -> dict[str, Any]:
        """q4: the one shared current-revision selector."""
        c, t, s, snap = ctx["c"], ctx["t"], ctx["s"], ctx["snap"]
        lo, hi, state = snap["lo"], snap["hi"], snap["state"]
        history = [] if lo is None else self._money.history_on(c, t, s, lo, hi)
        current, guard, derived = None, None, None
        if state == "CURRENT":
            basis = self._money.basis_on(c, t, s, lo, hi, snap["selected"])
            derived = None if basis is None else self._derive(basis)
            if derived is not None:
                current = self._money.select_on(c, t, s, lo, hi, derived.basis_sha256)
                if current is None:
                    guard = "STALE_BASIS"
        elif state in ("HISTORICAL", "PENDING_RECOMPUTE") and history:
            guard = "HISTORICAL_CURRENT_CLAIM" if state == "HISTORICAL" else em.ERROR_PENDING
        return {"current": current, "guard": guard, "derived": derived,
                "history": [h for h in history if current is None or h["id"] != current["id"]]}

    def _consequence(self, ctx: dict[str, Any]) -> dict[str, Any] | None:
        m = ctx["money"]
        row = m["current"]
        if row is None and m["guard"] is None:
            return None
        if row is None:  # a read guard: null current amount, never a stored row
            return {"revision_id": None, "revision_no": None, "state": "WITHHELD", "reason": m["guard"], "quantity_kwh": None,
                    "tariff_revision_id": None, "tariff_value": None, "currency": None, "amount": None,
                    "overlap_group": None, "recorded_at": None, "tariff_recorded_at": None, "source_gate": None,
                    "session_revision_ids": [], "evidence_ids": [], "limitation": MONEY_COPY[m["guard"]]}
        return self._revision(row, MONEY_COPY.get(row["reason"]))

    @staticmethod
    def _revision(row: dict[str, Any], limitation: str | None) -> dict[str, Any]:
        return {"revision_id": plain(row["id"]), "revision_no": row["revision_no"], "state": row["state"], "reason": row["reason"],
                "quantity_kwh": plain(row["quantity_kwh"]), "tariff_revision_id": plain(row["tariff_revision_id"]),
                "tariff_value": plain(row["tariff_value"]), "currency": row["currency"],
                "amount": plain(row["amount"]), "overlap_group": row["overlap_group"],
                "recorded_at": plain(row["recorded_at"]), "tariff_recorded_at": plain(row["tariff_recorded_at"]),
                "source_gate": row["source_gate"], "session_revision_ids": list(row["session_revision_ids"]),
                "evidence_ids": list(row["evidence_ids"]), "limitation": limitation}

    # --- shared pieces -------------------------------------------------------------------------------------------

    def _links(self, ctx: dict[str, Any], own: str) -> dict[str, Any]:
        snap, base = ctx["snap"], f"/sites/{ctx['code']}/ev"
        q = "" if snap["lo"] is None or snap["known"] is None else (
            f"?from={plain(snap['lo'])}&to={plain(snap['hi'])}&known_at={plain(snap['known'])}")
        paths = {"self": base + own, "evidence": base + "/evidence", "analysis": base + "/evidence/analysis",
                 "financials": base + "/financials"}
        return {"self": paths["self"] + q, "evidence": paths["evidence"] + q, "analysis": paths["analysis"] + q,
                "finding": None, "financials": paths["financials"] + q}

    def _accepted(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        if "accepted" not in ctx:
            ctx["accepted"] = self._reads.accepted_on(ctx["c"], ctx["snap"])
        return ctx["accepted"]

    def _sessions(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        if "sessions" not in ctx:
            ctx["sessions"] = self._reads.sessions_on(ctx["c"], ctx["snap"])
        return ctx["sessions"]

    def _tariffs(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        if "tariffs" not in ctx:
            snap = ctx["snap"]
            ctx["tariffs"] = [] if snap["lo"] is None else self._money.tariff_on(
                ctx["c"], ctx["t"], ctx["s"], snap["lo"], snap["hi"])
        return ctx["tariffs"]

    def _as_of(self, ctx: dict[str, Any]) -> str | None:
        sel = ctx["snap"]["selected"]
        return None if sel is None else plain(sel["created_at"])

    def _window_seconds(self, ctx: dict[str, Any]) -> int:
        snap = ctx["snap"]
        return 0 if snap["lo"] is None else int((snap["hi"] - snap["lo"]).total_seconds())

    def _session_seconds(self, ctx: dict[str, Any]) -> tuple[int, int, int]:
        """(expected, terminal-known, metered-known) seconds over the selected sessions with both ends."""
        expected = terminal = metered = 0
        for x in self._sessions(ctx):
            if x["start_at"] is None or x["end_at"] is None:
                continue
            span = int((datetime.fromisoformat(x["end_at"].replace("Z", "+00:00"))
                        - datetime.fromisoformat(x["start_at"].replace("Z", "+00:00"))).total_seconds())
            expected += span
            if x["state"] != "INCOMPLETE":
                terminal += span
            metered += max(0, span - (x["unknown_meter_seconds"] or 0)) if x["supported_kwh"] is not None else 0
        return expected, terminal, metered

    def _site_import(self, ctx: dict[str, Any]) -> tuple[int, Decimal | None]:
        known, peak = 0, None
        lo, hi = ctx["snap"]["lo"], ctx["snap"]["hi"]
        for r in self._accepted(ctx):
            if r["role"] != ROLE_OF["site_import"] or r["interval_start"] is None or r["interval_end"] is None:
                continue
            a, b = max(r["interval_start"], lo), min(r["interval_end"], hi)
            if b > a:
                known += int((b - a).total_seconds())
                value = _dec(r["value"])
                peak = value if peak is None or (value is not None and value > peak) else peak
        return known, peak

    def _capabilities(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        if "capabilities" in ctx:
            return ctx["capabilities"]
        snap, accepted, sessions = ctx["snap"], self._accepted(ctx), self._sessions(ctx)
        rows: list[dict[str, Any]] = []
        if snap["selected"] is not None or accepted:
            by_role: dict[str, list[str]] = {}
            for r in accepted:
                if r["role"] in PUBLIC_ROLE:
                    by_role.setdefault(PUBLIC_ROLE[r["role"]], []).append(r["evidence_id"])
            if self._tariffs(ctx):
                by_role[TARIFF_ROLE] = []
            incomplete = any(x["state"] == "INCOMPLETE" for x in sessions)
            contradictory = any(x["state"] == "CONTRADICTORY" for x in sessions)
            expected_s, terminal_s, metered_s = self._session_seconds(ctx)
            window_s = self._window_seconds(ctx)
            import_s, _peak = self._site_import(ctx)
            known_at = plain(snap["known"])
            for claim, required, cited, limitation, ceiling in CLAIMS:
                missing = [x for x in required if x not in by_role]
                if claim in ("SESSION_OUTCOME", "DELIVERED_ENERGY") and incomplete:
                    missing.append("session_terminal")
                state = ("UNAVAILABLE" if len(missing) >= len(required) and "session_terminal" not in missing
                         else "LIMITED" if missing else "SUPPORTED")
                if state == "SUPPORTED" and ceiling == "LIMITED":
                    state = "LIMITED"
                if contradictory and claim in ("SESSION_OUTCOME", "DELIVERED_ENERGY"):
                    state = "CONTRADICTORY"
                if claim == "SESSION_OUTCOME":
                    coverage = (terminal_s, expected_s)
                elif claim in ("DELIVERED_ENERGY", "GROSS_TARIFF_SCENARIO"):
                    coverage = (metered_s if "connector_meter_delta" in by_role else 0, expected_s)
                elif claim == "FAULT_ASSOCIATION":
                    coverage = (expected_s if "fault_event" in by_role else 0, expected_s)
                elif claim in ("SITE_POWER_CONTEXT", "POWER_CONSTRAINT"):
                    coverage = (import_s if not missing else 0, window_s)
                else:
                    coverage = (0, window_s)
                ids = sorted({e for role in cited for e in by_role.get(role, ())})
                rows.append({"claim": claim, "state": state, "required_roles": list(required),
                             "observed_roles": [x for x in required if x in by_role], "missing_roles": missing,
                             "coverage": {"known_seconds": coverage[0], "expected_seconds": coverage[1],
                                          "ratio": _ratio(*coverage)},
                             "accepted_evidence_ids": ids, "as_of": known_at, "limitation": limitation})
        ctx["capabilities"] = rows
        return rows

    # --- the five routes ---------------------------------------------------------------------------------------

    def overview(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            ctx = self._ctx(c, t, s, code, lo, hi, known_at)
            snap, body = ctx["snap"], ctx["body"]
            status, denominator = self._reads.status_on(snap)
            sessions = self._sessions(ctx)
            as_of = self._as_of(ctx)
            no_assessment = status["limitation"] if snap["selected"] is None else None
            foundation = self._reads.foundation_on(c, snap)
            limit_kw, feed_as_of = self._import_limit(foundation)
            # energy (W2-06 selected session heads; contradictory support is null, no report is null)
            if not sessions:
                energy = {"supported_kwh": None, "complete_kwh": None, "partial_kwh": None, "unknown_seconds": None,
                          "as_of": as_of, "limitation": no_assessment or "No supported session energy."}
            else:
                contradictory = any(x["state"] == "CONTRADICTORY" for x in sessions)
                complete = [_dec(x["supported_kwh"]) for x in sessions if x["energy_complete"] is True]
                partial = [_dec(x["supported_kwh"]) or Decimal("0.000") for x in sessions
                           if x["energy_complete"] is False]
                supported = [_dec(x["supported_kwh"]) for x in sessions if x["supported_kwh"] is not None]
                energy = {
                    "supported_kwh": None if contradictory or not supported else plain(sum(supported, Decimal(0))),
                    "complete_kwh": plain(sum(complete, Decimal(0))) if complete else None,
                    "partial_kwh": plain(sum(partial, Decimal("0.000"))),
                    "unknown_seconds": sum(x["unknown_meter_seconds"] or 0 for x in sessions),
                    "as_of": as_of, "limitation": "Accepted EV records conflict." if contradictory else None}
            window_s = self._window_seconds(ctx)
            import_s, peak = self._site_import(ctx)
            site_power = {
                "observed_peak_kw": plain(peak), "configured_limit_kw": limit_kw,
                "coverage": {"known_seconds": import_s, "expected_seconds": window_s,
                             "ratio": _ratio(import_s, window_s)},
                "claim_limit": "CONTEXT_ONLY" if import_s else "UNKNOWN",
                "as_of": plain(snap["known"]) if import_s else as_of,
                "limitation": None if import_s else (no_assessment
                                                     or "No accepted Site import intervals cover this window.")}
            findings = self._reads.findings_on(c, snap)
            money = self._consequence(ctx)
            summary = ({"state": None, "reason": None, "quantity_kwh": None, "amount": None, "currency": None,
                        "overlap_group": None, "as_of": None, "limitation": NO_MONEY} if money is None else
                       {"state": money["state"], "reason": money["reason"], "quantity_kwh": money["quantity_kwh"],
                        "amount": money["amount"], "currency": money["currency"],
                        "overlap_group": money["overlap_group"], "as_of": money["recorded_at"],
                        "limitation": money["limitation"]})
            links = self._links(ctx, "")
            return {**body,
                    "status": status,
                    "objective": {"text": "Let depot vehicles charge when scheduled, within the configured Site "
                                          "import limit.",
                                  "configured_service_window": None, "site_import_limit_kw": limit_kw,
                                  "as_of": feed_as_of,
                                  "limitation": "Configuration is not a measured service result."
                                  if limit_kw is not None else "Site limit not declared"},
                    "denominator": denominator, "energy": energy, "site_power": site_power,
                    "findings": {"count": len(findings),
                                 "items": [{**{k: x[k] for k in ("finding_id", "revision_id", "session_id", "title",
                                                                 "claim_level", "as_of", "links")},
                                            **{k: x["claim"].get(k) for k in ("start_evidence_id",
                                                                              "fault_evidence_id",
                                                                              "abort_evidence_id")}}
                                           for x in findings],
                                 "as_of": as_of, "limitation": no_assessment},
                    "needs_attention": self._attention(ctx, sessions, findings, money, links),
                    "consequence_summary": summary, "links": links}
        return self._reads.within(work)

    @staticmethod
    def _import_limit(foundation: dict[str, Any] | None) -> tuple[str | None, str | None]:
        if foundation is None:
            return None, None
        for component in foundation["content"].get("components") or ():
            for prop in component.get("properties") or ():
                if prop.get("property_key") == "ev-site-import-limit" and prop.get("value") is not None:
                    return format(Decimal(str(prop["value"])).normalize(), "f"), plain(foundation["valid_from"])
        return None, plain(foundation["valid_from"])

    def _attention(self, ctx, sessions, findings, money, links) -> list[dict[str, Any]]:
        out = []
        if ctx["snap"]["state"] == "PENDING_RECOMPUTE":
            out.append({"code": "PENDING", "text": MONEY_COPY[em.ERROR_PENDING], "link": None})
        faults = [x for x in findings if x.get("claim_level")]
        if any(x["state"] == "OBSERVED_ABORT" and x["fault_evidence_id"] for x in sessions):
            out.append({"code": "FAULT_ABORT", "text": "A session ended with a connector fault.",
                        "link": faults[0]["links"]["self"] if len(faults) == 1 else None})
        if any(x["state"] == "INCOMPLETE" for x in sessions):
            out.append({"code": "INCOMPLETE_SESSION", "text": "A session has no accepted end report.",
                        "link": links["analysis"]})
        if ctx["snap"].get("unassessable") is not None or any((x["unknown_meter_seconds"] or 0) > 0 for x in sessions):
            out.append({"code": "METER_OR_SOURCE_GAP", "text": "Meter or source evidence is missing or unverified.",
                        "link": links["analysis"]})
        if money is not None and money["reason"] == em.TARIFF_MISSING:
            out.append({"code": "TARIFF_MISSING", "text": MONEY_COPY[em.TARIFF_MISSING], "link": links["financials"]})
        return out

    def evidence(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            ctx = self._ctx(c, t, s, code, lo, hi, known_at)
            snap = ctx["snap"]
            capabilities = self._capabilities(ctx)
            accepted = self._accepted(ctx)
            foundation = self._reads.foundation_on(c, snap)
            assets = self._assets(c, ctx)
            components = [] if foundation is None else list(foundation["content"].get("components") or ())
            connectors = sorted((x for x in components if x.get("component_type") == "EV_CONNECTOR"),
                                key=lambda x: x.get("component_id") or "")
            meters = [x for x in components if x.get("component_type") == "METER"]
            slots = [(f"CONNECTOR_{i + 1}", x, f"Connector {i + 1}") for i, x in enumerate(connectors[:2])]
            while len(slots) < 2:
                slots.append((f"CONNECTOR_{len(slots) + 1}", None, f"Connector {len(slots) + 1}"))
            slots.append(("SITE_METER", meters[0] if len(meters) == 1 else None, "Site meter"))
            sources = []
            checked = plain(snap["known"])
            for slot, component, fallback in slots:
                asset = None if component is None else assets.get(component.get("component_id"))
                facts = [r for r in accepted if asset is not None and r["asset_id"] == asset]
                if slot == "SITE_METER":
                    facts = [r for r in facts if r["role"] == ROLE_OF["site_import"]]
                good = all(r["quality"] == "GOOD" for r in facts)
                sources.append({
                    "slot": slot, "asset_id": asset,
                    "display_name": (component or {}).get("display_name") or fallback,
                    "contact": {"state": "UNKNOWN", "checked_at": checked, "last_seen_at": None},
                    "quality": {"state": "NO_FACT" if not facts else "GOOD" if good else "DEGRADED",
                                "accepted_count": len(facts)},
                    "roles": sorted({PUBLIC_ROLE[r["role"]] for r in facts if r["role"] in PUBLIC_ROLE}),
                    "as_of": checked,
                    "limitation": "No source-specific contact diagnostic." if facts
                    else "No accepted report for this role."})
            sources.append({"slot": "BILLING", "asset_id": None, "display_name": "Billing system",
                            "contact": {"state": "UNKNOWN", "checked_at": checked, "last_seen_at": None},
                            "quality": {"state": "NO_FACT", "accepted_count": 0}, "roles": [], "as_of": checked,
                            "limitation": "No accepted payment feed."})
            return {**ctx["body"],
                    "capabilities": [{k: v for k, v in x.items() if k != "observed_roles"} for x in capabilities],
                    "sources": sources, "next_evidence": self._next(ctx, capabilities), "links": self._links(ctx, "/evidence")}
        return self._reads.within(work)

    def _assets(self, c, ctx) -> dict[str, str]:
        return self._reads.assets_on(c, ctx["snap"])

    def _next(self, ctx, capabilities) -> list[dict[str, Any]]:
        if not capabilities:
            return []
        missing = {role for x in capabilities for role in x["missing_roles"]}
        sessions = self._sessions(ctx)
        codes = []
        if "session_terminal" in missing:
            codes.append("TERMINAL_GAP")
        if "connector_meter_delta" in missing or any((x["unknown_meter_seconds"] or 0) > 0 for x in sessions):
            codes.append("METER_GAP")
        if "connector_status" in missing:
            codes.append("STATUS_GAP")
        if "site_import" in missing:
            codes.append("SITE_IMPORT_GAP")
        if TARIFF_ROLE in missing:
            codes.append("TARIFF_GAP")
        codes.append("BILLING_GAP")
        links = self._links(ctx, "/evidence")
        return [{"code": code, "text": NEXT_EVIDENCE[code][0], "why": NEXT_EVIDENCE[code][1],
                 "link": links[NEXT_EVIDENCE[code][2]]} for code in codes[:3]]

    def analysis(self, t: UUID, s: UUID, code: str, lo, hi, known_at, cursor: str | None, limit: int) -> dict:
        def work(c):
            ctx = self._ctx(c, t, s, code, lo, hi, known_at)
            snap, body = ctx["snap"], ctx["body"]
            accepted = self._accepted(ctx)
            names = self._names(c, ctx)
            items = []
            for r in accepted:
                kind = r["record_kind"]
                label = names.get(r["asset_id"]) or "EV source"
                items.append({
                    "evidence_id": r["evidence_id"],
                    "source_label": f"{label} · {PUBLIC_ROLE.get(r['role'], r['role'] or 'record')}",
                    "role": PUBLIC_ROLE.get(r["role"], r["role"]), "record_kind": kind,
                    "value_display": KIND_TEXT.get(kind) if r["family"] == "EVENT" else r["value"],
                    "unit": None if r["family"] == "EVENT" else r["unit"],
                    "source_time": plain(r["source_time"]), "sent_at": plain(r["sent_at"]),
                    "received_at": plain(r["received_at"]), "quality": r["quality"], "use": r["use"],
                    "reason": r["reason"], "session_id": r["session_id"],
                    "note": SOURCE_UNVERIFIED_NOTE if r["reason"] == "SOURCE_UNVERIFIED" else None,
                    "record_target_state": "UNAVAILABLE",
                    "links": {"self": None, "evidence": None, "analysis": None, "finding": None, "financials": None},
                    "_sort": r["_sort"]})
            page, nxt = self._reads.page_on(items, snap, body, "analysis", cursor, limit)
            source_class = body["source_provenance"]["classification"]
            rules = [{"claim": x["claim"], "required_roles": x["required_roles"],
                      "observed_roles": x["observed_roles"], "missing_roles": x["missing_roles"],
                      "coverage": x["coverage"], "result": x["state"],
                      "accepted_evidence_ids": x["accepted_evidence_ids"], "source_class": source_class,
                      "known_at": plain(snap["known"]), "limitation": x["limitation"]}
                     for x in self._capabilities(ctx)]
            excluded = [] if snap["selected"] is None else list(
                snap["selected"]["result"].get("excluded_records") or ())
            return {**body, "items": page, "total_count": len(items), "excluded_records": excluded,
                    "claim_rules": rules, "next_cursor": nxt, "links": self._links(ctx, "/evidence/analysis")}
        return self._reads.within(work)

    def _names(self, c, ctx) -> dict[str, str]:
        foundation = self._reads.foundation_on(c, ctx["snap"])
        assets = self._assets(c, ctx)
        out = {}
        for x in [] if foundation is None else foundation["content"].get("components") or ():
            asset = assets.get(x.get("component_id"))
            if asset is not None and isinstance(x.get("display_name"), str):
                out[asset] = x["display_name"]
        return out

    def financials(self, t: UUID, s: UUID, code: str, lo, hi, known_at, cursor: str | None, limit: int) -> dict:
        def work(c):
            ctx = self._ctx(c, t, s, code, lo, hi, known_at)
            history = [{**self._revision(h, HISTORY_LABEL), "label": HISTORY_LABEL,
                        "_sort": (h["recorded_at"], h["id"])} for h in ctx["money"]["history"]]
            page, nxt = self._reads.page_on(history, ctx["snap"], ctx["body"], "financials", cursor, limit)
            return {**ctx["body"], "consequence": self._consequence(ctx), "history": page,
                    "not_included": list(NOT_INCLUDED), "next_cursor": nxt, "links": self._links(ctx, "/financials")}
        return self._reads.within(work)

    def assumptions(self, t: UUID, s: UUID, code: str, lo, hi, known_at) -> dict[str, Any]:
        def work(c):
            ctx = self._ctx(c, t, s, code, lo, hi, known_at)
            snap = ctx["snap"]
            tariffs = self._tariffs(ctx)
            tariff = None
            if tariffs:
                x = tariffs[0]
                tariff = {"revision_id": plain(x["revision_id"]), "value": plain(x["value"]),
                          "currency": x["currency"], "unit": x["unit"], "basis": x["basis"],
                          "valid_from": plain(x["valid_from"]), "valid_to": plain(x["valid_to"]),
                          "recorded_at": plain(x["recorded_at"])}
            note = None
            if tariffs and snap["known"] is not None and tariffs[0]["recorded_at"] > snap["known"]:
                note = (f"Tariff published {_utc_words(tariffs[0]['recorded_at'])} UTC; applied as a scenario to the "
                        f"selected delivery window. Evidence through {_utc_words(snap['known'])} UTC.")
            money = self._consequence(ctx)
            return {**ctx["body"], "tariff": tariff, "tariff_revision_count": len(tariffs),
                    "publication_note": note,
                    "consequence_tariff": None if money is None or money["tariff_revision_id"] is None else
                    {"revision_id": money["tariff_revision_id"], "value": money["tariff_value"],
                     "currency": money["currency"], "recorded_at": money["tariff_recorded_at"]},
                    "billing_state": "NO_RECORD", "missing_keys": [] if tariffs else [em.TARIFF_KEY],
                    "links": self._links(ctx, "/financial-assumptions")}
        return self._reads.within(work)
