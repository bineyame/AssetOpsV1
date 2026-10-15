"""S5-01 phase 1: the selected-window imported-Site Overview read (`SiteWindowSummary`, schema below).

Packet `tasks/S5-01-site-overview.md` "Read contract"; decisions `D-2026-10-14-s5-selected-window-overview`,
`D-2026-10-15-s501-finding-choice`; Architect LR-01 deviations item 2 (the shared money gate is reported raw and is
never rewritten by upstream or schedule state; S5's own upstream status blocks the amount separately).

An equivalent scoped read over committed public records (no `site_window_projection` table). For one UTC day
`[00:00Z, next 00:00Z)` it composes, in one request:

1. the accepted-source fence (`accepted_fingerprint` over the day plus S3's six-hour bracket), read before and
   after everything else;
2. the S4-02d upstream currentness seam (`UpstreamCurrentness.window`): S3 day, S4 match, Findings, consequence
   work and schedule observation;
3. the selected S3 day detail (`DispatchReadService.window`), fenced to the seam's run, window revision and input;
4. one Finding chosen by the ruled rule, and its exact-head consequence read with the real Performance source gate;
5. accepted-reading context for the day from the evidence ledger.

A moved fence never yields mixed CURRENT: freshness is stale and money is `UPSTREAM_PENDING`. Nothing is written.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from assetops_backend.demonstration_label import demonstration_case
from assetops_backend.site_overview import money_state as ms

SCHEMA_VERSION = "site-window-summary-1"
BRACKET = timedelta(hours=6)
SELECTION_RULE = ("LATEST_RECORDED_REVISION_OF_EACH_CANONICAL_FINDING; half-open day intersection "
                  "(episode_start < day_end and episode_end > day_start); merge-superseded excluded; greatest "
                  "episode_start, then smallest Finding UUID")
SINGLE_FINDING_NOTE = "This card covers this Finding only; it is not a Site total."
FINDING_LIST = {"state": "UNAVAILABLE", "reason": "Unavailable until the Site Finding index is delivered."}
CONTEXT_LIMIT = 500
MONEY_LABEL = ("fuel-cost-1 model-conditioned potential fuel-cost exposure: zero lower bound, bounded upper "
               "value, with assumption and evidence lineage. Not savings and not a physical maximum.")

#: (site_code, episode_start, episode_end) -> label dict or None. The single replaceable provenance input
#: (S4-05 replaces it with a stored provenance resolver). The unverified label always gives no amount.
Provenance = Callable[[str, Any, Any], "dict[str, Any] | None"]


class InvalidSelection(ValueError):
    pass


def day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def _utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _iso(value: Any) -> str | None:
    v = _utc(value)
    return None if v is None else v.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def intersects(episode_start: Any, episode_end: Any, day_start: datetime, day_end: datetime) -> bool:
    """Half-open: a boundary touch alone (an episode ending exactly at the day's 00:00Z) does not qualify."""
    lo, hi = _utc(episode_start), _utc(episode_end)
    return lo is not None and lo < day_end and (hi is None or hi > day_start)


def choose(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Greatest episode_start, then the lexicographically smallest stable Finding UUID."""
    if not candidates:
        return None
    latest = max(_utc(c["episode_start"]) for c in candidates)
    return min((c for c in candidates if _utc(c["episode_start"]) == latest), key=lambda c: str(c["finding_id"]))


class SiteOverviewRead:
    def __init__(self, upstream: Any, ledger: Any, consequences: Any, findings: Any, *,
                 provenance: Provenance = demonstration_case, environment: str = "default",
                 context_limit: int = CONTEXT_LIMIT) -> None:
        self.upstream, self.ledger, self.consequences, self.findings = upstream, ledger, consequences, findings
        self.provenance, self.environment, self.context_limit = provenance, environment, context_limit

    def dispose(self) -> None:
        self.upstream.dispose()

    def db_today(self) -> date:
        return _utc(self.upstream.schedule.db_now()).astimezone(timezone.utc).date()

    def _fingerprint(self, t: UUID, s: UUID, lo: datetime, hi: datetime) -> tuple[dict[str, Any] | None, str | None]:
        try:
            fp = self.ledger.accepted_fingerprint(t, s, lo, hi)
        except Exception as exc:  # noqa: BLE001 - fail closed: no ledger fence, never CURRENT
            return None, f"ACCEPTED_SOURCE_UNREADABLE: {type(exc).__name__}"
        return {**fp, "bracket": {"start": _iso(lo), "end": _iso(hi)}, "order": "accepted evidence ID"}, None

    def read(self, site_code: str, tenant_id: UUID, site_id: UUID, day: date, *, access_basis: str,
             source_open: bool, source_reason: str, pinned: tuple[UUID, UUID | None] | None = None
             ) -> dict[str, Any]:
        t, s, code = tenant_id, site_id, site_code
        start, end = day_bounds(day)
        lo, hi = start - BRACKET, end + BRACKET
        reasons: list[str] = []

        fp_before, fp_error = self._fingerprint(t, s, lo, hi)
        up = self.upstream.window(t, s, start, end, self.environment)
        [up_day] = up["days"]
        detail = self.upstream.dispatch_read.window(t, s, day)
        context = self._context(t, s, start, end, code)
        fp_after, fp_error_after = self._fingerprint(t, s, lo, hi)

        moved: list[str] = []
        if fp_error or fp_error_after:
            reasons.append(fp_error or fp_error_after)
        elif fp_before["sha256"] != fp_after["sha256"] or fp_before["count"] != fp_after["count"]:
            moved.append("ACCEPTED_SOURCE_MOVED_DURING_READ")
        sel = detail.get("selection") or {}
        wa = detail.get("window_assessment") or {}
        if (str(sel.get("run_id")) if sel.get("run_id") else None) != (
                str(up_day["run_id"]) if up_day["run_id"] else None) or (
                str(wa.get("id")) if wa.get("id") else None) != (
                str(up_day["window_assessment_revision_id"]) if up_day["window_assessment_revision_id"] else None):
            moved.append("SELECTION_MOVED_DURING_READ")
        upstream_elig = up["eligibility"]
        up_reasons = tuple(upstream_elig["reasons"])
        discovery_blockers = [c for c in up_reasons if not ms.is_consequence_code(c)]
        discovery_complete = not moved and not fp_error and not fp_error_after and not discovery_blockers

        # ---- one Finding (D-2026-10-15-s501-finding-choice) ----
        seam = {f["finding_id"]: f for f in up["findings"]}
        candidates, excluded = [], []
        for f in up["findings"]:
            if not intersects(f["episode_start"], f["episode_end"], start, end):
                continue
            root = self.findings.finding_detail(t, s, UUID(f["finding_id"]))
            if root is None or (root.get("relations") or {}).get("merged_into"):
                excluded.append({"finding_id": f["finding_id"], "reason": "SUPERSEDED_BY_MERGE"})
                continue
            candidates.append({**f, "_root": root})
        fresh = choose(candidates)
        pin_view = self._pin(t, s, pinned)
        if pin_view is not None and not (discovery_complete and source_open):
            chosen, rule = pin_view, "PINNED_RETAINED_WHILE_BASIS_INCOMPLETE"
        elif source_open and fresh is not None:
            chosen, rule = {"finding_id": fresh["finding_id"], "finding_revision_id": fresh["finding_revision_id"],
                            "episode_start": fresh["episode_start"], "episode_end": fresh["episode_end"],
                            "root": fresh["_root"]}, "DISCOVERED"
        else:
            chosen, rule = None, None
        if not source_open and chosen is None:
            reasons.append("SOURCE_CLOSED_NO_UNPINNED_FINDING")

        money = self._money(code, t, s, chosen, seam, source_open=source_open, upstream=upstream_elig,
                            moved=moved or ([fp_error or fp_error_after] if fp_error or fp_error_after else []),
                            discovery_complete=discovery_complete)

        # ---- freshness ----
        state = upstream_elig["status"]
        f_reasons = list(up_reasons) + moved + reasons
        if not source_open:
            f_reasons.append("SOURCE_CLOSED")
        if state == "CURRENT" and (not source_open or moved or fp_error or fp_error_after):
            state = "STALE_PROJECTION"
        match = next((m for m in up["match"] if m["day"] == day.isoformat()), {})
        built = {
            "schema_version": SCHEMA_VERSION, "site_id": str(s), "site_code": code, "access_basis": access_basis,
            "window": {"start": _iso(start), "end": _iso(end), "utc_date": day.isoformat(), "bounds": "[start, end)"},
            "built_at": up["db_now"], "db_now": up["db_now"],
            "freshness": {"state": state, "stage": upstream_elig["stage"], "reasons": list(dict.fromkeys(f_reasons)),
                          "errors": upstream_elig["errors"], "source_open": source_open,
                          "source_reason": source_reason,
                          "schedule": up["schedule"], "s3_jobs": up["s3_jobs"],
                          "consequence_work": up["consequence_work"]},
            "watermarks": {
                "accepted_source": fp_after if not (fp_error or fp_error_after) else None,
                "accepted_source_reason": fp_error or fp_error_after,
                "analytic_selection_seq": up_day["watermark"]["selection_seq"],
                "input_sha256": up_day["watermark"]["input_sha256"],
                "configuration_sha256": up_day["watermark"]["configuration_sha256"],
                "match_pass_id": match.get("match_pass_id"),
                "matched_through_selection_seq": match.get("matched_through_selection_seq")},
            "model_version": detail.get("model_version"),
            "assessment": self._assessment(code, day, up_day, detail, source_open, source_reason),
            "context": context,
            "money": money,
            "known_finding": None if chosen is None else {
                "id": chosen["finding_id"], "revision_id": chosen["finding_revision_id"],
                "selection_rule": SELECTION_RULE, "selected_by": rule,
                "episode": {"start": _iso(chosen["episode_start"]), "end": _iso(chosen["episode_end"])},
                "audit_only": not source_open,
                "several_intersect": len(candidates) > 1, "note": SINGLE_FINDING_NOTE,
                "excluded": excluded,
                "previous_pin": None if pinned is None or (str(pinned[0]) == chosen["finding_id"]) else {
                    "finding_id": str(pinned[0]), "reason": "BASIS_CHANGED_CHOICE"},
                "link": self._finding_link(code, chosen["finding_id"], chosen["finding_revision_id"])},
            "finding_list": dict(FINDING_LIST),
        }
        return built

    # ---- pinned Finding (review N3: optional scope-checked query parameters) ----

    def _pin(self, t: UUID, s: UUID, pinned: tuple[UUID, UUID | None] | None) -> dict[str, Any] | None:
        if pinned is None:
            return None
        fid, rid = pinned
        root = self.findings.finding_detail(t, s, fid)
        if root is None:
            raise LookupError("No such Finding for this Site.")
        revisions = root["revisions"]
        rev = revisions[-1] if rid is None else next((r for r in revisions if str(r["id"]) == str(rid)), None)
        if rev is None:
            raise LookupError("No such revision for this Finding.")
        return {"finding_id": str(fid), "finding_revision_id": str(rev["id"]), "episode_start": rev["episode_start"],
                "episode_end": rev["episode_end"], "root": root}

    # ---- money ----

    def _money(self, code: str, t: UUID, s: UUID, chosen: dict[str, Any] | None, seam: dict[str, Any], *,
               source_open: bool, upstream: dict[str, Any], moved: list[str], discovery_complete: bool
               ) -> dict[str, Any]:
        out: dict[str, Any] = {"amount_low": None, "amount_high": None, "currency": None, "model_version": None,
                               "finding_id": None, "finding_revision_id": None, "consequence_revision_id": None,
                               "eligibility": None, "quantity_state": None, "price_state": None,
                               "limitation": None, "demonstration": None, "links": {}, "label": MONEY_LABEL,
                               "upstream": {"status": upstream["status"], "stage": upstream["stage"],
                                            "reasons": upstream["reasons"]}}
        inputs = dict(source_open=source_open, upstream_status=upstream["status"],
                      upstream_reasons=tuple(upstream["reasons"]), basis_moved=bool(moved),
                      discovery_complete=discovery_complete, finding_selected=chosen is not None)
        if chosen is None:
            out["state"] = ms.money_state(ms.MoneyInputs(**inputs))
            out["limitation"] = moved or list(upstream["reasons"]) or None
            return out
        fid, rid, root = chosen["finding_id"], chosen["finding_revision_id"], chosen["root"]
        latest = root["revisions"][-1]
        is_latest = str(latest["id"]) == rid
        body = self.consequences.read(t, s, UUID(fid), UUID(rid), finding_revision_is_latest=is_latest,
                                      source_open=source_open, limit=1) or {}
        selection = body.get("consequence_selection") or {}
        cur = body.get("currentness") or {}
        row = body.get("consequence") or {}
        gate = body.get("money_eligibility") or {}
        seam_row = seam.get(fid) or {}
        head = selection.get("head_consequence_revision_id")
        demo = self.provenance(code, chosen["episode_start"], chosen["episode_end"])
        inputs.update(
            eligibility=gate.get("state"), revision_is_latest=is_latest,
            merged=bool((root.get("relations") or {}).get("merged_into")),
            consequence_state=cur.get("state"),
            head_matches_seam=head is not None and head == seam_row.get("head_consequence_revision_id")
            and seam_row.get("finding_revision_id") == rid,
            consequence_row_state=row.get("state"), quantity_state=(row.get("quantity") or {}).get("state"),
            price_state=(row.get("price") or {}).get("state"),
            display_state=(row.get("display") or {}).get("state"),
            provenance_resolved=not (demo is not None and demo.get("case_id") == "unverified"),
            presented_as_current=bool(row.get("presented_as_current")) and bool(cur.get("current_amount_shown")))
        state = ms.money_state(ms.MoneyInputs(**inputs))
        out.update({
            "state": state, "finding_id": fid, "finding_revision_id": rid, "consequence_revision_id": head,
            "model_version": (row.get("model") or {}).get("model_id"),
            "eligibility": {k: gate.get(k) for k in ("version", "state", "note", "pending_reasons", "series_limits",
                                                    "latest_finding_revision_id", "end_reason")},
            "quantity_state": (row.get("quantity") or {}).get("state"),
            "price_state": (row.get("price") or {}).get("state"),
            "consequence_currentness": {"state": cur.get("state"), "reasons": cur.get("reasons"),
                                        "pending_work": cur.get("pending_work")},
            "seam_head_consequence_revision_id": seam_row.get("head_consequence_revision_id"),
            "demonstration": demo,
            "limitation": None if state == ms.PRICED else (moved or [state]),
            "links": self._money_links(code, fid, rid, head, row)})
        if state == ms.PRICED:
            display = row["display"]
            out.update({"amount_low": display["amount_low"], "amount_high": display["amount_high"],
                        "currency": display["currency"],
                        "amount_unrounded": row.get("amount")})
        return out

    # ---- sections ----

    def _assessment(self, code: str, day: date, up_day: dict[str, Any], detail: dict[str, Any], source_open: bool,
                    source_reason: str) -> dict[str, Any]:
        if not source_open:
            return {"state": "CLOSED", "reason": source_reason, "run_id": None, "window_assessment_revision_id": None,
                    "status": None, "claim_level": None, "limitations": [], "coverage": None,
                    "dispatch_intervals": [], "links": {}}
        status = up_day["s3_status"]
        run_id, wa_id = up_day["run_id"], up_day["window_assessment_revision_id"]
        base = f"/api/sites/{code}/performance/dispatch"
        links = {"dispatch_day": f"{base}/windows/{day.isoformat()}"}
        if run_id:
            links["run"] = f"{base}/runs/{run_id}"
        if wa_id:
            links["window_assessment_revision"] = f"{base}/revisions/{wa_id}"
        return {
            "state": "UNKNOWN" if status == "UNASSESSED" else status, "status": status,
            "status_reasons": up_day["s3_status_reasons"],
            "run_id": None if run_id is None else str(run_id),
            "window_assessment_revision_id": None if wa_id is None else str(wa_id),
            "claim_level": up_day["claim_level"], "limitations": up_day["limitations"] or [],
            "objective": None if not detail.get("window_assessment") else (detail["window_assessment"].get("result")
                                                                           or {}).get("objective"),
            "coverage": detail.get("coverage"),
            "dispatch_intervals": [{
                "revision_id": str(r.get("id")), "start": _iso(r.get("window_start")),
                "end": _iso(r.get("window_end")), "claim_level": r.get("claim_level"),
                "assessment_key": r.get("assessment_key"),
                "link": f"{base}/revisions/{r.get('id')}"} for r in detail.get("intervals") or []],
            "links": links}

    def _context(self, t: UUID, s: UUID, start: datetime, end: datetime, code: str) -> dict[str, Any]:
        try:
            window = self.ledger.site_window(t, s, start, end)
            page = self.ledger.records_page(t, s, start=start, end=end, device=None, signal=None, source=None,
                                            after=None, limit=self.context_limit)
        except Exception as exc:  # noqa: BLE001 - a missing input is a null with a reason, never an empty claim
            return {"series": None, "coverage": None, "gaps": None, "evidence_links": {},
                    "reason": f"EVIDENCE_LEDGER_UNAVAILABLE: {type(exc).__name__}"}
        series = [{"evidence_id": str(r["id"]), "time": _iso(r["source_time"]),
                   "interval": None if r.get("interval_start") is None else {
                       "start": _iso(r["interval_start"]), "end": _iso(r["interval_end"])},
                   "device_id": r["device_id"], "signal_id": r["signal_id"], "role": r.get("role"),
                   "value": r.get("normalized_value_text"), "unit": r.get("normalized_unit"),
                   "quality": r["quality"], "unavailable_reason": r.get("unavailable_reason")}
                  for r in page["rows"][:self.context_limit]]
        coverage = [{"device_id": c["device_id"], "signal_id": c["signal_id"], "role": c.get("role"),
                     "unit": c.get("normalized_unit"), "records": int(c["records"]), "good": int(c["good"]),
                     "first_source_time": _iso(c.get("first_source_time")),
                     "last_source_time": _iso(c.get("last_source_time"))} for c in window.get("coverage") or []]
        return {"series": series, "total": page["total"], "truncated": page["total"] > len(series),
                "limit": self.context_limit, "coverage": coverage,
                "gaps": None, "gaps_reason": "No reviewed gap rule exists for the Site context; coverage counts "
                                             "and the selected S3 coverage are shown instead.",
                "evidence_links": {r["evidence_id"]: f"/api/sites/{code}/evidence/records/{r['evidence_id']}"
                                   for r in series}}

    @staticmethod
    def _finding_link(code: str, fid: str, rid: str) -> dict[str, str]:
        return {"page": f"/sites/{code}/findings/{fid}?revision_id={rid}",
                "api": f"/api/sites/{code}/findings/{fid}?revision_id={rid}"}

    @staticmethod
    def _money_links(code: str, fid: str, rid: str, head: str | None, row: dict[str, Any]) -> dict[str, Any]:
        base = f"/api/sites/{code}/findings/{fid}"
        links: dict[str, Any] = {"finding": f"{base}?revision_id={rid}",
                                 "financials": f"{base}/financials?revision_id={rid}"}
        if head:
            links["consequence"] = f"{base}/financial-consequences?revision_id={rid}&consequence_revision_id={head}"
        price = (row.get("price") or {}).get("revision_id")
        if price:
            links["price_revision"] = f"/api/sites/{code}/financial-assumptions/{price}"
        lineage = row.get("lineage") or {}
        links["assumption_revisions"] = {a["assumption_revision_id"]:
                                         f"/api/sites/{code}/financial-assumptions/{a['assumption_revision_id']}"
                                         for a in lineage.get("assumptions") or []}
        links["evidence_records"] = {e: f"/api/sites/{code}/evidence/records/{e}"
                                     for e in lineage.get("evidence_ids") or []}
        links["assessment_revisions"] = {a["assessment_revision_id"]:
                                         f"/api/sites/{code}/performance/dispatch/revisions/{a['assessment_revision_id']}"
                                         for a in lineage.get("assessments") or []}
        return links
