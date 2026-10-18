"""W2-03 commit 4: selected cold reads (`.agent/W2-03-build-spec.md` "Commit 4 - selected reads" and the
"freshness reference for commit 4" amendment).

One REPEATABLE READ snapshot per request: the committed disposition watermark captured first, the latest DEFAULT
selection per analytic whose window covers the request and whose run cutoff is at or before `known_at`, its
assessment revision, the episode revisions of that revision and the cold Findings (`domain='cold_chain'`) whose
latest revision was known at the cutoff. Read-only; nothing here inserts. A missing selection is a valid
`UNKNOWN` read with null values and empty arrays; an unreachable store raises `ColdReadUnavailable` (503).
"""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError, OperationalError

from assetops_backend.analytics import cold
from assetops_backend.analytics.assessment_inputs import iso, sha256_json

#: The probe recency limit of a CURRENT read.
PROBE_RECENCY = timedelta(minutes=10)
STATES = ("CURRENT", "PENDING_RECOMPUTE", "STALE_SOURCE", "HISTORICAL", "UNKNOWN")
MAX_WINDOW = timedelta(days=31)
DEFAULT_LIMIT, MAX_LIMIT = 50, 200
NO_SPOILAGE = "No spoilage, product-loss or failed-part determination is made."
PENDING_NOTE = ("Newer accepted evidence is waiting to be assessed; this is the previous selected result, "
                "not a current claim.")
HISTORICAL_NOTE = "Read at an earlier evidence cutoff; newer committed evidence exists."
NO_SELECTION_NOTE = "No selected cold assessment covers this window yet."
STALE_NOTE = "The latest usable probe reading is more than 10 minutes before the end of the window."
FUTURE_NOTE = "The window has not ended yet."
NO_PROBE_NOTE = "No usable probe reading in the selected window."


class ColdReadUnavailable(Exception):
    """The cold read store cannot be reached; the route answers 503, never an empty success."""


class ColdCursorRefused(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status, self.code = status, code


def probe_fresh(latest_probe_at: datetime | None, reference_at: datetime) -> bool:
    """The single probe-recency rule. `reference_at` is the selected half-open window's `to` boundary
    (Architect amendment 2026-10-18: window-scoped freshness, not live gateway contact or the wall clock)."""
    return latest_probe_at is not None and reference_at - latest_probe_at <= PROBE_RECENCY


def currentness_state(*, pending: bool, historical: bool, selected: bool, latest_probe_at: datetime | None,
                      window_to: datetime | None, now: datetime) -> str:
    """Amendment precedence: pending -> PENDING_RECOMPUTE; older explicit cutoff -> HISTORICAL; no settled
    selection, no qualifying probe or a future `to` -> UNKNOWN; stale probe at `to` -> STALE_SOURCE; else CURRENT."""
    if pending:
        return "PENDING_RECOMPUTE"
    if historical:
        return "HISTORICAL"
    if not selected or latest_probe_at is None or window_to is None or window_to > now:
        return "UNKNOWN"
    return "CURRENT" if probe_fresh(latest_probe_at, window_to) else "STALE_SOURCE"


def encode_cursor(anchor: datetime, finding_id: UUID, basis: str) -> str:
    raw = json.dumps({"basis": basis, "id": str(finding_id), "t": iso(anchor)}, sort_keys=True,
                     separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def decode_cursor(cursor: str, basis: str) -> tuple[datetime, UUID]:
    try:
        doc = json.loads(base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)))
        anchor = datetime.fromisoformat(doc["t"].replace("Z", "+00:00"))
        finding_id = UUID(doc["id"])
        held = doc["basis"]
    except (ValueError, KeyError, TypeError, binascii.Error) as error:
        raise ColdCursorRefused(422, "COLD_CURSOR_INVALID", "The cursor is not a cold Finding cursor.") from error
    if held != basis:
        raise ColdCursorRefused(409, "COLD_CURSOR_BASIS_CHANGED",
                                "The selected basis changed since this cursor was issued; reload the first page.")
    return anchor, finding_id


@dataclass(frozen=True)
class Selected:
    analytic_id: str
    revision_id: UUID
    revision_no: int
    basis: str
    result: dict[str, Any]
    evidence_ids: list[str]
    window_start: datetime
    window_end: datetime
    knowledge_cutoff: datetime


def _plain(value: Any) -> Any:
    return cold.plain(value)


def _decimal(raw: str | None) -> str | None:
    """A stored normalized value as a canonical decimal string, or null when it is not a number."""
    try:
        return None if raw is None else _plain(Decimal(raw))
    except InvalidOperation:
        return None


class ColdReadService:
    def __init__(self, database_url: str | None = None, *, engine=None,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self._url, self._engine, self.clock = database_url, engine, clock

    def _connect(self):
        if self._engine is None:
            self._engine = create_engine(self._url, pool_pre_ping=True)
        return self._engine.connect().execution_options(isolation_level="REPEATABLE READ")

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()

    def _read(self, work: Callable[[Connection], Any]) -> Any:
        try:
            with self._connect() as c, c.begin():
                return work(c)
        except (OperationalError, DBAPIError) as error:
            raise ColdReadUnavailable(f"The cold assessment store is unavailable: {error.__class__.__name__}") \
                from error

    # --- the shared snapshot ---------------------------------------------------------------------------------

    def _snapshot(self, c: Connection, t: UUID, s: UUID, code: str, lo: datetime | None, hi: datetime | None,
                  known_at: datetime | None) -> dict[str, Any]:
        p = {"t": t, "s": s}
        watermark = c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE tenant_id = :t "
                                   "AND site_id = :s"), p).scalar()
        known = known_at or watermark
        if lo is None and known is not None:  # no explicit window: the latest selected cold window at the cutoff
            row = c.execute(text(
                "SELECT sel.window_start, sel.window_end FROM analytic_run_selection sel JOIN analytic_run r "
                "ON r.id = sel.run_id WHERE sel.tenant_id = :t AND sel.site_id = :s AND sel.analytic_id IN (:a, :b) "
                "AND r.knowledge_cutoff <= :k ORDER BY sel.seq DESC LIMIT 1"),
                {**p, "a": cold.EXCURSION_ANALYTIC, "b": cold.START_RESPONSE_ANALYTIC, "k": known}).first()
            if row is not None:
                lo, hi = row[0], row[1]
        selected: dict[str, Selected] = {}
        if lo is not None and known is not None:
            for analytic in (cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC):
                r = c.execute(text(
                    "SELECT ar.id, ar.revision_no, ar.basis_sha256, ar.result, ar.evidence_ids, sel.window_start, "
                    "sel.window_end, r.knowledge_cutoff FROM analytic_run_selection sel JOIN analytic_run r "
                    "ON r.id = sel.run_id JOIN analytic_run_assessment x ON x.run_id = r.id JOIN assessment_revision "
                    "ar ON ar.id = x.assessment_revision_id WHERE sel.tenant_id = :t AND sel.site_id = :s "
                    "AND sel.analytic_id = :a AND sel.window_start <= :lo AND sel.window_end >= :hi "
                    "AND r.knowledge_cutoff <= :k ORDER BY sel.seq DESC LIMIT 1"),
                    {**p, "a": analytic, "lo": lo, "hi": hi, "k": known}).first()
                if r is not None:
                    result = r[3] if isinstance(r[3], dict) else json.loads(r[3])
                    ids = r[4] if isinstance(r[4], list) else json.loads(r[4])
                    selected[analytic] = Selected(analytic, r[0], r[1], r[2], result, list(ids), r[5], r[6], r[7])
        pending_since = None
        if lo is not None:
            pending_since = c.execute(text(
                "SELECT min(created_at) FROM recompute_job WHERE tenant_id = :t AND site_id = :s "
                "AND domain = :d AND status IN ('PENDING', 'LEASED', 'FAILED') AND window_start < :hi "
                "AND window_end > :lo"),
                {**p, "d": cold.DOMAIN, "lo": lo - cold.MAX_BRIDGE, "hi": hi + cold.MAX_BRIDGE}).scalar()
        exc = selected.get(cold.EXCURSION_ANALYTIC)
        support = [UUID(x["evidence_id"]) for x in (exc.result.get("links") or [])
                   if x["use"] == "SUPPORT"] if exc else []
        evidence = self._evidence(c, t, s, support + [UUID(x["evidence_id"]) for x in self._other_links(selected)])
        probes = sorted((evidence[e] for e in support if e in evidence), key=lambda e: (e["source_time"], e["id"]))
        latest_probe = probes[-1]["source_time"] if probes else None
        historical = known_at is not None and watermark is not None and known_at < watermark
        any_selected = exc or selected.get(cold.START_RESPONSE_ANALYTIC)
        window_to = any_selected.window_end if any_selected else None
        state = currentness_state(pending=pending_since is not None, historical=historical,
                                  selected=bool(selected), latest_probe_at=latest_probe, window_to=window_to,
                                  now=self.clock())
        limitations = []
        if not selected:
            limitations.append(NO_SELECTION_NOTE)
        elif state == "PENDING_RECOMPUTE":
            limitations.append(PENDING_NOTE)
        elif state == "HISTORICAL":
            limitations.append(HISTORICAL_NOTE)
        elif state == "STALE_SOURCE":
            limitations.append(STALE_NOTE)
        elif state == "UNKNOWN":
            limitations.append(FUTURE_NOTE if window_to is not None and window_to > self.clock() else NO_PROBE_NOTE)
        return {"code": code, "t": t, "s": s, "lo": lo, "hi": hi, "known": known, "watermark": watermark,
                "selected": selected, "pending_since": pending_since, "evidence": evidence, "probes": probes,
                "latest_probe": latest_probe, "state": state, "limitations": limitations}

    @staticmethod
    def _other_links(selected: dict[str, Selected]) -> list[dict[str, Any]]:
        out = []
        for sel in selected.values():
            out += [x for x in sel.result.get("links") or () if x["use"] != "SUPPORT"
                    or sel.analytic_id == cold.START_RESPONSE_ANALYTIC]
        return out

    @staticmethod
    def _evidence(c: Connection, t: UUID, s: UUID, ids: list[UUID]) -> dict[UUID, dict[str, Any]]:
        if not ids:
            return {}
        rows = c.execute(text(
            "SELECT id, source_time, normalized_value_text, quality, outcome, message_id, record_kind, role "
            "FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s AND id = ANY(:ids)"),
            {"t": t, "s": s, "ids": sorted(set(ids), key=str)}).all()
        return {r[0]: {"id": r[0], "source_time": r[1], "value": r[2], "quality": r[3], "outcome": r[4],
                       "message_id": r[5], "record_kind": r[6], "role": r[7]} for r in rows}

    def _envelope(self, snap: dict[str, Any], analytics: tuple[str, ...]) -> dict[str, Any]:
        chosen = [snap["selected"][a] for a in analytics if a in snap["selected"]]
        gate = chosen[0].result.get("source_gate") if chosen else None
        basis = (chosen[0].basis if len(chosen) == 1 else sha256_json([x.basis for x in chosen])) if chosen else None
        return {
            "site_id": str(snap["s"]),
            "window": {"from": _plain(snap["lo"]), "to": _plain(snap["hi"]), "known_at": _plain(snap["known"])},
            "currentness": {"state": snap["state"],
                            "watermark": {"decided_at": _plain(snap["watermark"]),
                                          "assessment_revision_ids": [str(x.revision_id) for x in chosen]},
                            "latest_relevant_evidence_at": _plain(snap["latest_probe"]),
                            "pending_since": _plain(snap["pending_since"])},
            "source_provenance": {
                "classification": None if gate is None else gate.get("classification"),
                "source_ids": [] if gate is None else list(gate.get("source_ids") or ()),
                "evidence_ids": sorted({e for x in chosen for e in x.evidence_ids}),
                "basis_sha256": basis},
            "limitations": list(snap["limitations"]),
        }

    def _as_of(self, snap: dict[str, Any], analytic: str) -> str | None:
        sel = snap["selected"].get(analytic)
        return None if sel is None else _plain(sel.knowledge_cutoff)

    def _episodes(self, c: Connection, snap: dict[str, Any], sel: Selected | None, kind: str,
                  subject: str | None) -> dict[str, tuple[str, str]]:
        """anchor evidence ID -> (episode_id, episode_revision_id) of the selected assessment revision."""
        if sel is None or subject is None:
            return {}
        rows = c.execute(text(
            "SELECT e.id, e.episode_key_sha256, r.id FROM cold_episode e JOIN cold_episode_revision r "
            "ON r.episode_id = e.id WHERE e.tenant_id = :t AND e.site_id = :s AND e.kind = :k "
            "AND r.assessment_revision_id = :a"),
            {"t": snap["t"], "s": snap["s"], "k": kind, "a": sel.revision_id}).all()
        by_key = {r[1]: (str(r[0]), str(r[2])) for r in rows}
        items = sel.result.get("excursions" if kind == "EXCURSION" else "chains") or []
        out = {}
        for item in items:
            key = cold.episode_key_sha256(snap["t"], snap["s"], kind, UUID(subject), UUID(item["anchor_evidence_id"]))
            if key in by_key:
                out[item["anchor_evidence_id"]] = by_key[key]
        return out

    # --- temperature -----------------------------------------------------------------------------------------

    def temperature(self, tenant_id: UUID, site_id: UUID, code: str, lo: datetime | None, hi: datetime | None,
                    known_at: datetime | None) -> dict[str, Any]:
        return self._read(lambda c: self._temperature(c, tenant_id, site_id, code, lo, hi, known_at))

    def _temperature(self, c, t, s, code, lo, hi, known_at) -> dict[str, Any]:
        snap = self._snapshot(c, t, s, code, lo, hi, known_at)
        body = self._envelope(snap, (cold.EXCURSION_ANALYTIC,))
        sel = snap["selected"].get(cold.EXCURSION_ANALYTIC)
        as_of = self._as_of(snap, cold.EXCURSION_ANALYTIC)
        if sel is None:
            return {**body, "policy": None, "points": [], "gaps": [], "excursions": [], "excluded": [],
                    "coverage": {"known_points": None, "expected_points": None, "ratio": None}}
        r, pol = sel.result, sel.result.get("policy") or {}
        in_window = [p for p in snap["probes"] if snap["lo"] <= p["source_time"] < snap["hi"]]
        episodes = self._episodes(c, snap, sel, "EXCURSION", pol.get("room_asset_id"))
        body["limitations"] += list(r.get("limitations") or ()) + [NO_SPOILAGE]
        return {
            **body,
            "state": r.get("state"), "claim_level": r.get("claim_level"),
            "policy": {"low_deg_c": pol.get("policy_low"), "high_deg_c": pol.get("policy_high"),
                       "return_hysteresis_deg_c": pol.get("return_hysteresis"),
                       "min_excursion_min": pol.get("min_excursion_minutes"),
                       "probe_asset_id": pol.get("probe_asset_id"), "room_asset_id": pol.get("room_asset_id"),
                       "as_of": as_of, "limitation": None},
            "points": [{"at": _plain(p["source_time"]), "value": _decimal(p["value"]), "quality": p["quality"], "evidence_id": str(p["id"]),
                "as_of": _plain(p["source_time"]), "limitation": None} for p in in_window],
            "coverage": {"known_points": r.get("known_points"), "expected_points": r.get("expected_points"),
                         "ratio": r.get("coverage")},
            "gaps": [{**{k: g.get(k) for k in ("start", "end", "reason", "expected_points", "received_points")},
                      "as_of": as_of, "limitation": None} for g in r.get("gaps") or ()],
            "excursions": [{
                "episode_id": episodes.get(x["anchor_evidence_id"], (None, None))[0],
                "revision_id": episodes.get(x["anchor_evidence_id"], (None, None))[1],
                "direction": x["direction"], "anchor_time": x["anchor_time"], "open": x["open"],
                "start_bounds": {"earliest": x["start_earliest"], "latest": x["start_latest"]},
                "end_bounds": {"earliest": x["end_earliest"], "latest": x["end_latest"]},
                "duration_bounds": {"low": x["duration_low"], "high": x["duration_high"]},
                "degree_minute_bounds": {"low": x["degree_minutes_low"], "high": x["degree_minutes_high"]},
                "peak_observed": x["peak_observed"], "claim_level": x["claim_level"],
                "exposure_finding": x["exposure_finding"], "as_of": as_of, "limitation": x.get("limitation"),
            } for x in r.get("excursions") or ()],
            "excluded": [{"evidence_id": x["evidence_id"], "use": x["use"], "reason": x["reason"],
                          "as_of": _plain(snap["evidence"].get(UUID(x["evidence_id"]), {}).get("source_time")),
                          "limitation": None}
                         for x in r.get("links") or () if x["use"] != "SUPPORT"],
        }

    # --- backup chain ----------------------------------------------------------------------------------------

    def backup_chain(self, tenant_id: UUID, site_id: UUID, code: str, lo: datetime | None, hi: datetime | None,
                     known_at: datetime | None) -> dict[str, Any]:
        return self._read(lambda c: self._backup(c, tenant_id, site_id, code, lo, hi, known_at))

    def _backup(self, c, t, s, code, lo, hi, known_at) -> dict[str, Any]:
        snap = self._snapshot(c, t, s, code, lo, hi, known_at)
        body = self._envelope(snap, (cold.START_RESPONSE_ANALYTIC,))
        sel = snap["selected"].get(cold.START_RESPONSE_ANALYTIC)
        if sel is None:
            return {**body, "state": None, "claim_level": None, "chains": [], "contradictions": []}
        r, as_of = sel.result, self._as_of(snap, cold.START_RESPONSE_ANALYTIC)
        episodes = self._episodes(c, snap, sel, "START_RESPONSE", (r.get("policy") or {}).get("generator_asset_id"))
        order = {name: n for n, name in enumerate(cold.STEPS)}
        chains, contradictions = [], []
        for ch in r.get("chains") or ():
            steps = []
            for st in sorted(ch["steps"], key=lambda x: order.get(x["step"], 99)):
                first = st["evidence_ids"][0] if st.get("evidence_ids") else None
                e = snap["evidence"].get(UUID(first)) if first else None
                outcome = None if e is None else (e["outcome"] or e["value"])
                steps.append({"kind": st["step"], "at": st["at"], "outcome": outcome, "evidence_id": first,
                              "evidence_ids": list(st.get("evidence_ids") or ()), "state": st["state"],
                              "as_of": st["at"], "limitation": None if st["state"] == "OBSERVED" else (
                                  "No accepted record shows this step." if st["state"] == "MISSING"
                                  else "Accepted records disagree for this step.")})
            episode = episodes.get(ch["anchor_evidence_id"], (None, None))
            chains.append({"correlation_id": ch["correlation_id"], "episode_id": episode[0],
                           "revision_id": episode[1], "result": ch["result"], "steps": steps,
                           "missing_steps": list(ch["missing_steps"]), "claim_level": ch["claim_level"],
                           "start_timeout_min": ch["start_timeout_min"], "as_of": as_of,
                           "limitation": ch.get("limitation")})
            conflicting = [x["evidence_id"] for x in ch["links"] if x.get("reason") == "CONTRADICTORY"]
            if conflicting:
                contradictions.append({"correlation_id": ch["correlation_id"], "evidence_ids": sorted(conflicting),
                                       "reason": "CONTRADICTORY", "as_of": as_of,
                                       "limitation": "Conflicting accepted outcomes; no failure is claimed."})
        body["limitations"] += list(r.get("limitations") or ())
        excluded = [{"evidence_id": x["evidence_id"], "use": x["use"], "reason": x["reason"],
                     "as_of": _plain(snap["evidence"].get(UUID(x["evidence_id"]), {}).get("source_time")),
                     "limitation": None} for x in r.get("links") or () if x["use"] != "SUPPORT"]
        return {**body, "state": r.get("state"), "claim_level": r.get("claim_level"), "chains": chains,
                "contradictions": contradictions, "excluded": excluded}

    # --- Findings --------------------------------------------------------------------------------------------

    _REVISION = (
        "SELECT r.id, r.revision_no, r.transition, r.lifecycle, r.claim_level, r.title, r.claim, r.limitations, "
        "r.assessment_revision_id, r.basis_sha256, r.created_at, er.lower_start, er.upper_start, er.lower_end, "
        "er.upper_end FROM finding_revision r JOIN analytic_run ar ON ar.id = r.analytic_run_id "
        "LEFT JOIN cold_episode_revision er ON er.id = CAST(r.claim->>'episode_revision_id' AS uuid) "
        "WHERE r.finding_id = :f AND r.domain = 'cold_chain' AND ar.knowledge_cutoff <= :k ")

    def _finding_ids(self, c, snap, after: tuple[datetime, UUID] | None, limit: int | None,
                     finding_id: UUID | None = None) -> list:
        sql = ("SELECT f.id, f.anchor_start, f.subject_asset_id, f.split_from_finding_id FROM finding f "
               "WHERE f.tenant_id = :t AND f.site_id = :s AND f.domain = 'cold_chain' AND f.anchor_start >= :lo "
               "AND f.anchor_start < :hi AND EXISTS (SELECT 1 FROM finding_revision r JOIN analytic_run ar "
               "ON ar.id = r.analytic_run_id WHERE r.finding_id = f.id AND ar.knowledge_cutoff <= :k) ")
        p = {"t": snap["t"], "s": snap["s"], "lo": snap["lo"], "hi": snap["hi"], "k": snap["known"]}
        if finding_id is not None:
            sql += "AND f.id = :f "
            p["f"] = finding_id
        if after is not None:
            sql += "AND (f.anchor_start, f.id) > (:at, :aid) "
            p.update(at=after[0], aid=after[1])
        sql += "ORDER BY f.anchor_start, f.id"
        if limit is not None:
            sql += " LIMIT :n"
            p["n"] = limit + 1
        return c.execute(text(sql), p).all()

    def _revisions(self, c, snap, finding_id: UUID, latest_only: bool) -> list:
        sql = self._REVISION + "ORDER BY r.revision_no DESC" + (" LIMIT 1" if latest_only else "")
        return c.execute(text(sql), {"f": finding_id, "k": snap["known"]}).all()

    @staticmethod
    def _revision_evidence(c, revision_id: UUID) -> list[str]:
        return [str(x) for x in c.execute(text(
            "SELECT evidence_id FROM finding_revision_evidence WHERE finding_revision_id = :r ORDER BY evidence_id"),
            {"r": revision_id}).scalars().all()]

    def _links(self, snap, finding_id, revision_id, assessment_revision_id, evidence_ids) -> dict[str, Any]:
        q = f"?from={_plain(snap['lo'])}&to={_plain(snap['hi'])}&known_at={_plain(snap['known'])}"
        messages = {str(k): v["message_id"] for k, v in snap.get("finding_evidence", {}).items()}
        return {
            "finding": f"/api/sites/{snap['code']}/cold/findings/{finding_id}{q}",
            "evidence": [{"evidence_id": e, "href": f"/api/sites/{snap['code']}/evidence/records/{messages[e]}{q}"
                          if e in messages else None} for e in evidence_ids],
            "analysis": {"assessment_revision_id": str(assessment_revision_id),
                         "href": f"/api/sites/{snap['code']}/assessments/{assessment_revision_id}{q}"},
        }

    def _item(self, c, snap, row, rev) -> dict[str, Any]:
        claim = rev[6] if isinstance(rev[6], dict) else json.loads(rev[6])
        limits = rev[7] if isinstance(rev[7], list) else json.loads(rev[7])
        evidence_ids = self._revision_evidence(c, rev[0])
        snap.setdefault("finding_evidence", {}).update(self._evidence(c, snap["t"], snap["s"],
                                                                      [UUID(e) for e in evidence_ids]))
        return {
            "finding_id": str(row[0]), "kind": claim.get("kind"), "subject_asset_id": _plain(row[2]),
            "revision_id": str(rev[0]), "lifecycle": rev[3], "claim_level": rev[4], "title": rev[5],
            "state": claim.get("state"), "claim": claim,
            "episode_bounds": {"start": {"earliest": _plain(rev[11]), "latest": _plain(rev[12])},
                               "end": {"earliest": _plain(rev[13]), "latest": _plain(rev[14])}},
            "limitations": list(limits), "assessment_revision_id": str(rev[8]), "evidence_ids": evidence_ids,
            "split_from_finding_id": _plain(row[3]),
            "links": self._links(snap, row[0], rev[0], rev[8], evidence_ids),
            "as_of": _plain(rev[10]), "limitation": limits[0] if limits else None,
        }

    def findings(self, tenant_id: UUID, site_id: UUID, code: str, lo: datetime | None, hi: datetime | None,
                 known_at: datetime | None, cursor: str | None, limit: int) -> dict[str, Any]:
        def work(c):
            snap = self._snapshot(c, tenant_id, site_id, code, lo, hi, known_at)
            body = self._envelope(snap, (cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC))
            basis = body["source_provenance"]["basis_sha256"] or "none"
            after = None if cursor is None else decode_cursor(cursor, basis)
            if not snap["selected"]:
                return {**body, "items": [], "next_cursor": None}
            rows = self._finding_ids(c, snap, after, limit)
            page, more = rows[:limit], len(rows) > limit
            items = [self._item(c, snap, row, self._revisions(c, snap, row[0], True)[0]) for row in page]
            nxt = encode_cursor(page[-1][1], page[-1][0], basis) if more else None
            return {**body, "items": items, "next_cursor": nxt}
        return self._read(work)

    def finding(self, tenant_id: UUID, site_id: UUID, code: str, finding_id: UUID, lo: datetime | None,
                hi: datetime | None, known_at: datetime | None) -> dict[str, Any] | None:
        def work(c):
            snap = self._snapshot(c, tenant_id, site_id, code, lo, hi, known_at)
            body = self._envelope(snap, (cold.EXCURSION_ANALYTIC, cold.START_RESPONSE_ANALYTIC))
            if snap["lo"] is None:
                return None
            rows = self._finding_ids(c, snap, None, None, finding_id)
            if not rows:
                return None
            revisions = self._revisions(c, snap, finding_id, False)
            item = self._item(c, snap, rows[0], revisions[0])
            claim = item["claim"]
            history = [{"revision_id": str(r[0]), "revision_no": r[1], "transition": r[2], "lifecycle": r[3],
                        "claim_level": r[4], "basis_sha256": r[9], "created_at": _plain(r[10]),
                        "evidence_ids": self._revision_evidence(c, r[0]), "as_of": _plain(r[10]),
                        "limitation": None} for r in revisions]
            body["source_provenance"]["basis_sha256"] = revisions[0][9]
            return {**body, **item, "basis_sha256": revisions[0][9], "episode_id": claim.get("episode_id"),
                    "episode_revision_id": claim.get("episode_revision_id"), "revisions": history}
        return self._read(work)


def build_cold_read_service(database_url: str) -> ColdReadService:
    return ColdReadService(database_url)
