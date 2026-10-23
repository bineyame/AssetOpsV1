"""W4-01 commit 3: the work read adapter (Run 3 ruling 7; rule-8 named PostgreSQL reader, never a writer).

Owns the scoped work-case/revision/event/record/junction/accepted-evidence SQL, the exact pinned Finding/Action
and selected-window reads, and the caller-owned **read-only REPEATABLE READ** connection for detail (`snapshot`).
The read time is the unrounded DB `clock_timestamp()` taken once, as the snapshot's first statement (q4-1: a private
test may inject `test_read_clock_override`, called once instead; no request, env or `main.py` path supplies it).

Pinned link selection (Run 3 ruling 6, W3-01 Run 7 q7-1): on the same connection, cold/EV links resolve the
pinned Finding revision's exact stored run window and its greatest eligible selection seq at the requested cutoff
(the shared `selected_windows_on`), then call the shared `ColdReadService._snapshot` / `EvReadService._snapshot`
with `known_at=:evidence_cutoff` (the Site's latest `ingestion_disposition.decided_at` at or before the request
cutoff), `selection_cutoff=:requested_known_at` and `selection_seqs`; the selected assessment revision must be the
pinned Finding revision's, or the pin is missing. Mini-grid links read the at-cutoff S3 dispatch days
(`select_dispatch_days_on`) and the S4 matcher pass (`index_snapshot_on`) on this connection. No SQL here
writes: the work store (`postgres_work_store.py`) remains the sole writer of the eleven work tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError

from assetops_backend.work.link_coverage import DOMAIN_ACTION
from assetops_backend.work.model import WorkStoreUnavailable

_CASE = ("SELECT c.id, c.kind, c.public_code, c.asset_id, c.occurred_at, c.created_at, r.incident_id "
         "FROM work_case c LEFT JOIN maintenance_work_request r ON r.tenant_id = c.tenant_id "
         "AND r.site_id = c.site_id AND r.id = c.id "
         "WHERE c.tenant_id = :t AND c.site_id = :s AND c.id = :i AND c.created_at <= :k")
_REVISIONS = ("SELECT id, revision_no, supersedes_revision_id, title, narrative, reason, recorded_at, actor_kind, "
              "actor_id, occurred_at FROM work_case_revision WHERE tenant_id = :t AND site_id = :s AND case_id = :i "
              "AND recorded_at <= :k ORDER BY recorded_at, id")
_EVENTS = ("SELECT id, kind, payload, occurred_at, recorded_at, actor_kind, actor_id FROM work_event "
           "WHERE tenant_id = :t AND site_id = :s AND case_id = :i AND recorded_at <= :k ORDER BY recorded_at, id")
_RECORDS = ("SELECT id, activity, outcome_note, occurred_at, recorded_at, supersedes_record_id FROM maintenance_record "
            "WHERE tenant_id = :t AND site_id = :s AND case_id = :i AND recorded_at <= :k ORDER BY recorded_at, id")
_FINDING_PIN = ("fr.domain, fr.analytic_id, fr.analytic_run_id, fr.assessment_revision_id, fr.episode_start, "
                "fr.episode_end, fr.created_at")
_MICROSECOND = timedelta(microseconds=1)
_DOMAIN_LINKS = (
    "SELECT DISTINCT ON (l.action_id) CAST(l.action_id AS text) AS action_id, "
    "CAST(a.origin_finding_id AS text) AS origin_finding_id, "
    "CAST(a.origin_finding_revision_id AS text) AS origin_finding_revision_id "
    "FROM domain_action_case_link l "
    "JOIN work_case_revision cur ON cur.tenant_id = l.tenant_id AND cur.site_id = l.site_id AND cur.id = :r "
    "AND cur.case_id = l.case_id "
    "JOIN work_case_revision lr ON lr.tenant_id = l.tenant_id AND lr.site_id = l.site_id "
    "AND lr.id = l.case_revision_id AND lr.case_id = l.case_id AND lr.revision_no <= cur.revision_no "
    "JOIN work_event ev ON ev.tenant_id = l.tenant_id AND ev.site_id = l.site_id AND ev.id = l.case_event_id "
    "AND ev.case_id = l.case_id "
    "JOIN domain_action a ON a.tenant_id = l.tenant_id AND a.site_id = l.site_id AND a.id = l.action_id "
    "AND a.recorded_at <= :k "
    "WHERE l.tenant_id = :t AND l.site_id = :s AND l.recorded_at <= :k "
    "ORDER BY l.action_id, l.recorded_at DESC, l.id")
# W4-01 commit 4 (spec "Commit 4 implementer dry-read"): eligible cases of one kind before paging. Incidents by root
# `occurred_at`, requests by root `created_at`, both in `[from, to)` and created by the cutoff; a case needs its
# revision at the cutoff. q7-1: the scoped Asset label inputs are `asset_code`, `asset_type` (no cutoff, no name).
_ELIGIBLE = ("SELECT CAST(c.id AS text) AS id, c.kind, c.public_code, CAST(c.asset_id AS text) AS asset_id, "
             "c.occurred_at, c.created_at, CAST(r.incident_id AS text) AS incident_id, a.asset_code, a.asset_type "
             "FROM work_case c LEFT JOIN maintenance_work_request r ON r.tenant_id = c.tenant_id "
             "AND r.site_id = c.site_id AND r.id = c.id "
             "LEFT JOIN asset a ON a.tenant_id = c.tenant_id AND a.site_id = c.site_id AND a.id = c.asset_id "
             "WHERE c.tenant_id = :t AND c.site_id = :s AND c.kind = :kind AND c.created_at <= :k "
             "AND c.{member} >= :lo AND c.{member} < :hi AND EXISTS (SELECT 1 FROM work_case_revision v "
             "WHERE v.tenant_id = c.tenant_id AND v.site_id = c.site_id AND v.case_id = c.id AND v.recorded_at <= :k)")
_MEMBER = {"INCIDENT": "occurred_at", "MAINTENANCE_REQUEST": "created_at"}


def _rows(result) -> list[dict[str, Any]]:
    return [dict(r._mapping) for r in result]


@dataclass(frozen=True)
class LinkReadPorts:
    """Shared reads injected by the composition root; each takes the caller's connection and opens nothing."""

    cold_snapshot: Callable[..., dict[str, Any]]       # ColdReadService._snapshot
    ev_snapshot: Callable[..., dict[str, Any]]         # EvReadService._snapshot
    selected_windows: Callable[..., list[dict[str, Any]]]  # selected_windows_on
    pin_refused: tuple[type, ...]                      # SelectionPinRefused
    dispatch_days: Callable[..., list[dict[str, Any]]]  # PostgresAssessmentStore.select_dispatch_days_on
    finding_index: Callable[..., dict[str, Any]]       # PostgresFindingStore.index_snapshot_on
    cold_analytics: tuple[str, ...]
    ev_analytics: tuple[str, ...]
    # q7-2: `PostgresActionStore.site_window_on` for the exact W1 `sai1-` Action window fence on this connection.
    action_window: Callable[..., dict[str, Any]] | None = None
    # W5-02a ruling B1: `ColdReadService.envelope_on` of the same cold read owner, for the K1b domain Action detail.
    cold_envelope: Callable[..., dict[str, Any]] | None = None


class _ReadTx:
    """One detail read: every method reads on the snapshot connection, scoped by tenant and Site."""

    def __init__(self, c: Connection, tenant_id: UUID, site_id: UUID, site_code: str, read_at: datetime,
                 link_rows: Callable[[Connection, UUID, UUID, list[str]], list[Any]] | None,
                 ports: LinkReadPorts | None) -> None:
        self._c, self._t, self._s, self._code = c, tenant_id, site_id, site_code
        self.read_at = read_at
        self._link_rows, self._ports = link_rows, ports

    def _p(self, **extra: Any) -> dict[str, Any]:
        return {"t": self._t, "s": self._s, **extra}

    # ---- the case at the cutoff ------------------------------------------------------------------------------

    def case(self, case_id: str, known_at: datetime) -> dict[str, Any] | None:
        row = self._c.execute(text(_CASE), self._p(i=case_id, k=known_at)).first()
        return None if row is None else dict(row._mapping)

    def revisions(self, case_id: str, known_at: datetime) -> list[dict[str, Any]]:
        return _rows(self._c.execute(text(_REVISIONS), self._p(i=case_id, k=known_at)))

    def events(self, case_id: str, known_at: datetime) -> list[dict[str, Any]]:
        return _rows(self._c.execute(text(_EVENTS), self._p(i=case_id, k=known_at)))

    def records(self, case_id: str, known_at: datetime) -> list[dict[str, Any]]:
        return _rows(self._c.execute(text(_RECORDS), self._p(i=case_id, k=known_at)))

    def revision_links(self, revision_id: str, known_at: datetime) -> dict[str, Any]:
        """W1 `action_links` and, separately (W5-02a ruling C1), the explicit cold `domain_action_links` bound to
        this case at or before `known_at` (never the battery FK table, which W4 command replay re-inserts)."""
        p = self._p(r=revision_id)
        finding = self._c.execute(text(
            "SELECT CAST(finding_id AS text) AS finding_id, CAST(finding_revision_id AS text) AS finding_revision_id "
            "FROM work_case_finding_link WHERE tenant_id = :t AND site_id = :s AND case_revision_id = :r "
            "ORDER BY finding_id, finding_revision_id"), p)
        action = self._c.execute(text(
            "SELECT CAST(action_id AS text) AS action_id, CAST(action_event_id AS text) AS action_event_id "
            "FROM work_case_action_link WHERE tenant_id = :t AND site_id = :s AND case_revision_id = :r "
            "ORDER BY action_id, action_event_id"), p)
        evidence = self._c.execute(text(
            "SELECT CAST(evidence_id AS text) FROM work_case_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND case_revision_id = :r ORDER BY evidence_id"), p)
        domain = [{"kind": DOMAIN_ACTION, "action_id": r["action_id"], "action_event_id": None,
                   "finding_revision_id": r["origin_finding_revision_id"]}
                  for r in self._domain_links(revision_id, known_at)]
        return {"finding_links": _rows(finding), "action_links": _rows(action), "evidence_ids": list(evidence.scalars()),
                "domain_action_links": domain}

    def _domain_links(self, revision_id: str, known_at: datetime) -> list[dict[str, Any]]:
        """Ruling C1: one row per domain Action explicitly linked to this revision's case at an exact selected
        revision/event no later than this revision (a link carries forward to later revisions of the same case),
        recorded at or before `known_at`, scoped to this tenant/Site; the newest link of an Action wins."""
        return _rows(self._c.execute(text(_DOMAIN_LINKS), self._p(r=revision_id, k=known_at)))

    def lineage_evidence(self, finding_revision_ids: list[str], action_ids: list[str]) -> list[str]:
        """Q11: pinned Finding revisions' cited evidence, each pinned Action's basis evidence and its origin
        Finding revision's cited evidence, scoped to this tenant/Site."""
        p = self._p(r=list(finding_revision_ids), a=list(action_ids))
        return list(self._c.execute(text(
            "SELECT CAST(evidence_id AS text) FROM finding_revision_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND finding_revision_id = ANY(CAST(:r AS uuid[])) "
            "UNION SELECT CAST(evidence_id AS text) FROM action_basis_evidence WHERE tenant_id = :t "
            "AND site_id = :s AND action_id = ANY(CAST(:a AS uuid[])) "
            "UNION SELECT CAST(e.evidence_id AS text) FROM action a JOIN finding_revision_evidence e "
            "ON e.tenant_id = a.tenant_id AND e.site_id = a.site_id AND e.finding_revision_id = a.origin_finding_revision_id "
            "WHERE a.tenant_id = :t AND a.site_id = :s AND a.id = ANY(CAST(:a AS uuid[]))"), p).scalars())

    def link_rows(self, evidence_ids: list[str]) -> list[Any]:
        if self._link_rows is None:
            raise WorkStoreUnavailable("The work read has no provenance link-row reader.")
        return list(self._link_rows(self._c, self._t, self._s, evidence_ids))

    # ---- the list selection (commit 4) ---------------------------------------------------------------------

    def site_name(self) -> str | None:
        return self._c.execute(text("SELECT name FROM site WHERE tenant_id = :t AND id = :s"), self._p()).scalar()

    def eligible_cases(self, kind: str, from_: datetime, to: datetime, known_at: datetime) -> list[dict[str, Any]]:
        return _rows(self._c.execute(text(_ELIGIBLE.format(member=_MEMBER[kind])),
                                     self._p(kind=kind, lo=from_, hi=to, k=known_at)))

    def action_window(self, from_: datetime, to: datetime, known_at: datetime) -> dict[str, Any] | None:
        """q7-2: the W1 Action index window (Actions created in `[from, to)`) at the cutoff on this connection;
        None when no port is wired (the `sai1-` fence then cannot be reproduced)."""
        if self._ports is None or self._ports.action_window is None:
            return None
        return self._ports.action_window(self._c, self._t, self._s, from_, to, known_at)

    # ---- pinned link selections (Q9 coverage port) -----------------------------------------------------------

    def link_selections(self, revision_id: str, from_: datetime | None, to: datetime | None,
                        known_at: datetime) -> list[dict[str, Any]]:
        p = self._p(r=revision_id, k=known_at)
        finding = _rows(self._c.execute(text(
            f"SELECT CAST(l.finding_id AS text) AS root_id, CAST(l.finding_revision_id AS text) AS selected_id, "
            f"fr.id AS pinned, {_FINDING_PIN} FROM work_case_finding_link l LEFT JOIN finding_revision fr "
            "ON fr.tenant_id = l.tenant_id AND fr.site_id = l.site_id AND fr.id = l.finding_revision_id "
            "AND fr.finding_id = l.finding_id AND fr.created_at <= :k "
            "WHERE l.tenant_id = :t AND l.site_id = :s AND l.case_revision_id = :r"), p))
        action = _rows(self._c.execute(text(
            f"SELECT CAST(l.action_id AS text) AS root_id, CAST(l.action_event_id AS text) AS selected_id, "
            "CAST(a.origin_finding_id AS text) AS origin_finding_id, "
            "CAST(a.origin_finding_revision_id AS text) AS origin_finding_revision_id, "
            f"fr.id AS pinned, {_FINDING_PIN} FROM work_case_action_link l "
            "LEFT JOIN action_event ae ON ae.tenant_id = l.tenant_id AND ae.site_id = l.site_id "
            "AND ae.action_id = l.action_id AND ae.id = l.action_event_id AND ae.recorded_at <= :k "
            "LEFT JOIN action a ON a.tenant_id = l.tenant_id AND a.site_id = l.site_id AND a.id = ae.action_id "
            "LEFT JOIN finding_revision fr ON fr.tenant_id = a.tenant_id AND fr.site_id = a.site_id "
            "AND fr.id = a.origin_finding_revision_id AND fr.finding_id = a.origin_finding_id AND fr.created_at <= :k "
            "WHERE l.tenant_id = :t AND l.site_id = :s AND l.case_revision_id = :r"), p))
        # Ruling C1: an explicit domain link's selected ID is its root's pinned cold Finding revision; lineage
        # needs that exact stored `cold_chain` revision of the origin Finding by the cutoff.
        domain_rows = []
        for link in self._domain_links(revision_id, known_at):
            fr = _rows(self._c.execute(text(
                f"SELECT fr.id AS pinned, {_FINDING_PIN} FROM finding_revision fr WHERE fr.tenant_id = :t "
                "AND fr.site_id = :s AND fr.id = :f AND fr.finding_id = :fid AND fr.domain = 'cold_chain' "
                "AND fr.created_at <= :k"),
                self._p(f=link["origin_finding_revision_id"], fid=link["origin_finding_id"], k=known_at)))
            domain_rows.append({"root_id": link["action_id"], "selected_id": link["origin_finding_revision_id"],
                                "origin_finding_id": link["origin_finding_id"],
                                "origin_finding_revision_id": link["origin_finding_revision_id"],
                                **(fr[0] if fr else {"pinned": None, "domain": "cold_chain"})})
        out = []
        for kind, rows in (("FINDING", finding), ("ACTION", action), (DOMAIN_ACTION, domain_rows)):
            for row in rows:
                domain = row["domain"]
                pin = None if row["pinned"] is None else self._pin(row, from_, to, known_at)
                # Commit 4: `lineage` is whether the exact pinned revision (or Action event, root and origin
                # revision) exists in scope by the cutoff, apart from whether its analytic selection resolves.
                out.append({"kind": kind, "id": row["root_id"], "selected_id": row["selected_id"],
                            "domain": domain, "pin": pin, "lineage": row["pinned"] is not None,
                            "origin_finding_id": row.get("origin_finding_id"),
                            "origin_finding_revision_id": row.get("origin_finding_revision_id")})
        return out

    def _pin(self, fr: dict[str, Any], from_: datetime | None, to: datetime | None,
             known_at: datetime) -> dict[str, Any] | None:
        if self._ports is None:
            raise WorkStoreUnavailable("The work read has no linked selection reader.")
        if fr["domain"] == "mini_grid":
            return self._minigrid(fr, from_, to, known_at)
        if fr["domain"] == "cold_chain" and fr["analytic_id"] in self._ports.cold_analytics:
            return self._cold_ev(fr, known_at, self._ports.cold_snapshot, self._ports.cold_analytics, cold=True)
        if fr["domain"] == "ev_charging" and fr["analytic_id"] in self._ports.ev_analytics:
            return self._cold_ev(fr, known_at, self._ports.ev_snapshot, self._ports.ev_analytics, cold=False)
        return None  # an unrecognized domain is UNKNOWN

    def _minigrid(self, fr: dict[str, Any], from_: datetime | None, to: datetime | None,
                  known_at: datetime) -> dict[str, Any] | None:
        if from_ is not None and to is not None:
            lo, hi = from_, to
        elif fr["episode_start"] is not None and fr["episode_end"] is not None:
            lo, hi = fr["episode_start"], max(fr["episode_end"], fr["episode_start"] + _MICROSECOND)
        else:
            return None
        days = self._ports.dispatch_days(self._c, self._t, self._s, lo, hi, known_at)
        index = self._ports.finding_index(self._c, self._t, self._s, "mini_grid", fr["analytic_id"], known_at)
        match_pass = index.get("match_pass")
        deferred = {d.astimezone(timezone.utc) for d in (index.get("deferred_windows") or ())}
        return {"matched_through_selection_seq": None if match_pass is None
                else int(match_pass["matched_through_selection_seq"]),
                "match_pass_id": None if match_pass is None else match_pass["match_pass_id"],
                "days": [{"window_start": d["window_start"], "available": bool(d["available"]),
                          "status": d["status"],
                          "seq": None if d["selection"] is None else int(d["selection"]["seq"]),
                          "deferred": d["window_start"].astimezone(timezone.utc) in deferred} for d in days]}

    def _cold_ev(self, fr: dict[str, Any], known_at: datetime, snapshot: Callable[..., dict[str, Any]],
                 analytics: tuple[str, ...], cold: bool) -> dict[str, Any] | None:
        p = self._p(k=known_at, r=fr["analytic_run_id"])
        evidence_cutoff = self._c.execute(text(
            "SELECT max(decided_at) FROM ingestion_disposition WHERE tenant_id = :t AND site_id = :s "
            "AND decided_at <= :k"), p).scalar()
        if evidence_cutoff is None:  # q7-1: no provable evidence basis
            return None
        window = self._c.execute(text(
            "SELECT window_start, window_end FROM analytic_run WHERE tenant_id = :t AND site_id = :s AND id = :r"),
            p).first()
        if window is None:
            return None
        lo, hi = window[0], window[1]
        # The exact window's selected seq of every analytic of the domain at the cutoff (one snapshot per exact
        # window, as `estate_snapshots_on` pins it); the pinned Finding's analytic must be among them.
        seqs = {k["analytic_id"]: k["seq"] for k in self._ports.selected_windows(
            self._c, self._t, self._s, analytics, lo, hi, known_at, evidence_cutoff=evidence_cutoff)
            if k["window_start"] == lo and k["window_end"] == hi}
        if fr["analytic_id"] not in seqs:
            return None
        seq = seqs[fr["analytic_id"]]
        try:
            snap = snapshot(self._c, self._t, self._s, self._code, lo, hi, evidence_cutoff,
                            selection_cutoff=known_at, selection_seqs=seqs)
        except self._ports.pin_refused:
            return None
        if cold:
            selected = snap["selected"].get(fr["analytic_id"])
            selected_revision = None if selected is None else selected.revision_id
        else:
            selected_revision = None if snap["selected"] is None else snap["selected"]["revision_id"]
        if selected_revision is None or str(selected_revision) != str(fr["assessment_revision_id"]):
            return None  # the pinned Finding revision is not the exact selected result at this cutoff
        return {"state": snap["state"], "analytic_id": fr["analytic_id"], "window_start": lo, "window_end": hi,
                "seq": int(seq), "selection_seqs": {a: int(v) for a, v in sorted(seqs.items())},
                "assessment_revision_id": str(selected_revision),
                "evidence_cutoff": evidence_cutoff}


class PostgresWorkRead:
    def __init__(self, database_url: str | None, *,
                 link_rows: Callable[[Connection, UUID, UUID, list[str]], list[Any]] | None = None,
                 ports: LinkReadPorts | None = None, statement_timeout_ms: int = 30_000,
                 test_read_clock_override: Callable[[], datetime] | None = None) -> None:
        self._database_url = database_url
        self.test_read_clock_override = test_read_clock_override
        self._link_rows, self._ports = link_rows, ports
        self._options = f"-c statement_timeout={int(statement_timeout_ms)}"
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise WorkStoreUnavailable("DATABASE_URL is not set, so the work store cannot be read.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True,
                                         connect_args={"options": self._options})
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def snapshot(self, tenant_id: UUID, site_id: UUID, site_code: str, work: Callable[[_ReadTx], Any]) -> Any:
        """One read-only REPEATABLE READ transaction; `work` receives the read handle with the DB read time."""
        try:
            with self._connect().connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                # q4-1: one read instant per snapshot; a private test clock replaces only this upper bound.
                if self.test_read_clock_override is not None:
                    read_at = self.test_read_clock_override()
                    assert read_at.tzinfo is not None and read_at.utcoffset() == timedelta(0)
                else:
                    read_at = c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc)
                return work(_ReadTx(c, tenant_id, site_id, site_code, read_at, self._link_rows, self._ports))
        except (OperationalError, DBAPIError) as error:
            raise WorkStoreUnavailable(f"The work store could not be read: {error.__class__.__name__}") from error
