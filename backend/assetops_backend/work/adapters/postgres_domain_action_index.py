"""W5-02a K1b: the domain Action read adapter (rule-8 named PostgreSQL reader, never a writer; ruling A5/B3).

Owns the public read SQL of the cold domain Action detail (`domain-action-intent-read-1`) and the Site Action union
index (`site-domain-action-index-1`): the scoped `domain_action` roots, their declared intents and explicit W4 case
links at a cutoff, the pinned Finding revisions and the linked W4 maintenance request's selected revision, events
and performed record. Every read runs on ONE caller-owned **read-only REPEATABLE READ** connection whose read time
is the DB `clock_timestamp()` taken once as the snapshot's first statement (a private test may inject
`test_read_clock_override`; no request, env or `main.py` path supplies it).

The selected cold Finding pin (`pin_of`, the W4 linked-selection pin), the selected cold envelope (`envelope_of`,
`ColdReadService._snapshot` + `envelope_on` on this connection; ruling B1), the W3 link-row reader and the W1 Action
window (`PostgresActionStore.site_window_on`; ruling B2, no second W1 SQL) and the selected EV basis (`ev_basis_of`,
W5-04a V1b) are injected by `work/composition.py`;
no analytics adapter is imported here. No SQL here writes: `postgres_domain_intent.py` remains the sole writer of
the three domain Action tables.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import DBAPIError, OperationalError

from assetops_backend.work.model import WorkStoreUnavailable

_ACTION_COLS = ("CAST(id AS text) AS id, action_code, domain, CAST(origin_finding_id AS text) AS origin_finding_id, "
                "CAST(origin_finding_revision_id AS text) AS origin_finding_revision_id, title, owner_label, due_at, "
                "raised_at, recorded_at")
_LINK_COLS = ("CAST(l.id AS text) AS id, CAST(l.action_id AS text) AS action_id, CAST(l.case_id AS text) AS case_id, "
              "CAST(l.case_revision_id AS text) AS case_revision_id, CAST(l.case_event_id AS text) AS case_event_id, "
              "l.recorded_at")

PinOf = Callable[[Connection, UUID, UUID, str, dict[str, Any], datetime], "dict[str, Any] | None"]
EnvelopeOf = Callable[[Connection, UUID, UUID, str, dict[str, Any], datetime], dict[str, Any]]
EvBasisOf = Callable[[Connection, UUID, UUID, str, dict[str, Any], datetime, str], "dict[str, Any] | None"]


def _rows(result) -> list[dict[str, Any]]:
    return [dict(r._mapping) for r in result]


def _one(result) -> dict[str, Any] | None:
    row = result.first()
    return None if row is None else dict(row._mapping)


class _IndexTx:
    """One domain Action read: every method reads on the snapshot connection, scoped by tenant and Site."""

    def __init__(self, c: Connection, tenant_id: UUID, site_id: UUID, site_code: str, read_at: datetime,
                 reader: "PostgresDomainActionRead") -> None:
        self._c, self._t, self._s, self._code = c, tenant_id, site_id, site_code
        self.read_at = read_at
        self._r = reader

    def _p(self, **extra: Any) -> dict[str, Any]:
        return {"t": self._t, "s": self._s, **extra}

    # ---- domain roots, intents and explicit case links -------------------------------------------------------

    def action(self, action_id: str, known_at: datetime) -> dict[str, Any] | None:
        return _one(self._c.execute(text(
            f"SELECT {_ACTION_COLS} FROM domain_action WHERE tenant_id = :t AND site_id = :s AND id = :i "
            "AND recorded_at <= :k"), self._p(i=action_id, k=known_at)))

    def actions_in_window(self, lo: datetime, hi: datetime, known_at: datetime) -> list[dict[str, Any]]:
        """Membership is the attested `raised_at` in `[lo, hi)`; a root recorded after the cutoff is not known."""
        return _rows(self._c.execute(text(
            f"SELECT {_ACTION_COLS} FROM domain_action WHERE tenant_id = :t AND site_id = :s AND raised_at >= :lo "
            "AND raised_at < :hi AND recorded_at <= :k ORDER BY raised_at DESC, id"),
            self._p(lo=lo, hi=hi, k=known_at)))

    def intents(self, action_ids: list[str], known_at: datetime) -> list[dict[str, Any]]:
        """Every declared intent of these roots recorded by the cutoff, in `(recorded_at, id)` order."""
        return _rows(self._c.execute(text(
            "SELECT CAST(id AS text) AS id, CAST(action_id AS text) AS action_id, recorded_at, criteria, basis "
            "FROM domain_action_intent WHERE tenant_id = :t AND site_id = :s "
            "AND action_id = ANY(CAST(:a AS uuid[])) AND recorded_at <= :k ORDER BY recorded_at, id"),
            self._p(a=list(action_ids), k=known_at)))

    def case_links(self, action_id: str, known_at: datetime) -> list[dict[str, Any]]:
        """The Action's explicit W4 case links recorded by the cutoff, with the linked case's kind and code."""
        return _rows(self._c.execute(text(
            f"SELECT {_LINK_COLS}, c.kind, c.public_code FROM domain_action_case_link l JOIN work_case c "
            "ON c.tenant_id = l.tenant_id AND c.site_id = l.site_id AND c.id = l.case_id "
            "WHERE l.tenant_id = :t AND l.site_id = :s AND l.action_id = :a AND l.recorded_at <= :k "
            "ORDER BY l.recorded_at DESC, l.case_id"), self._p(a=action_id, k=known_at)))

    def selected_case_link(self, action_id: str, case_id: str, upto: datetime) -> dict[str, Any] | None:
        """The newest explicit link of this case to this Action recorded by `upto` (the K1a token's selection)."""
        return _one(self._c.execute(text(
            f"SELECT {_LINK_COLS} FROM domain_action_case_link l WHERE l.tenant_id = :t AND l.site_id = :s "
            "AND l.action_id = :a AND l.case_id = :c AND l.recorded_at <= :u ORDER BY l.recorded_at DESC, l.id DESC "
            "LIMIT 1"), self._p(a=action_id, c=case_id, u=upto)))

    # ---- the linked W4 maintenance request at the cutoff ----------------------------------------------------

    def request_view(self, case_id: str, known_at: datetime) -> dict[str, Any] | None:
        """The request's selected revision title, its events and its latest performed record at the cutoff."""
        p = self._p(i=case_id, k=known_at)
        revision = _one(self._c.execute(text(
            "SELECT CAST(id AS text) AS id, title FROM work_case_revision WHERE tenant_id = :t AND site_id = :s "
            "AND case_id = :i AND recorded_at <= :k ORDER BY recorded_at DESC, id DESC LIMIT 1"), p))
        if revision is None:
            return None
        events = _rows(self._c.execute(text(
            "SELECT CAST(id AS text) AS id, kind, payload, occurred_at, recorded_at FROM work_event "
            "WHERE tenant_id = :t AND site_id = :s AND case_id = :i AND recorded_at <= :k ORDER BY recorded_at, id"), p))
        record = self._c.execute(text(
            "SELECT CAST(id AS text) FROM maintenance_record WHERE tenant_id = :t AND site_id = :s AND case_id = :i "
            "AND recorded_at <= :k ORDER BY recorded_at DESC, id DESC LIMIT 1"), p).scalar()
        return {"revision": revision, "events": events, "record_id": record}

    # ---- the pinned Finding revision and its selected cold read ----------------------------------------------

    def finding_revisions(self, revision_ids: list[str], known_at: datetime) -> dict[str, dict[str, Any]]:
        rows = _rows(self._c.execute(text(
            "SELECT CAST(id AS text) AS id, CAST(finding_id AS text) AS finding_id, domain, analytic_id, "
            "analytic_run_id, assessment_revision_id, episode_start, episode_end, created_at FROM finding_revision "
            "WHERE tenant_id = :t AND site_id = :s AND id = ANY(CAST(:r AS uuid[])) AND created_at <= :k"),
            self._p(r=list(revision_ids), k=known_at)))
        return {r["id"]: r for r in rows}

    def pin(self, revision: dict[str, Any], known_at: datetime) -> dict[str, Any] | None:
        if self._r.pin_of is None:
            raise WorkStoreUnavailable("The domain Action read has no selected Finding reader.")
        return self._r.pin_of(self._c, self._t, self._s, self._code, revision, known_at)

    def envelope(self, pin: dict[str, Any], known_at: datetime) -> dict[str, Any]:
        if self._r.envelope_of is None:
            raise WorkStoreUnavailable("The domain Action read has no selected cold envelope reader.")
        return self._r.envelope_of(self._c, self._t, self._s, self._code, pin, known_at)

    def ev_basis(self, pin: dict[str, Any], known_at: datetime, revision_id: str) -> dict[str, Any] | None:
        """W5-04a V1b: the selected EV basis of one pin at the selection cutoff (readiness 27/30)."""
        if self._r.ev_basis_of is None:
            raise WorkStoreUnavailable("The domain Action read has no selected EV basis reader.")
        return self._r.ev_basis_of(self._c, self._t, self._s, self._code, pin, known_at, revision_id)

    # ---- W1 battery Actions and provenance link rows ---------------------------------------------------------

    def w1_window(self, lo: datetime, hi: datetime, known_at: datetime) -> dict[str, Any]:
        if self._r.action_window is None:
            raise WorkStoreUnavailable("The domain Action index has no W1 Action window reader.")
        return self._r.action_window(self._c, self._t, self._s, lo, hi, known_at)

    def link_rows(self, evidence_ids: list[str]) -> list[Any]:
        if self._r.link_rows is None:
            raise WorkStoreUnavailable("The domain Action read has no provenance link-row reader.")
        return list(self._r.link_rows(self._c, self._t, self._s, evidence_ids))


class PostgresDomainActionRead:
    def __init__(self, database_url: str | None, *,
                 link_rows: Callable[[Connection, UUID, UUID, list[str]], list[Any]] | None = None,
                 pin_of: PinOf | None = None, envelope_of: EnvelopeOf | None = None,
                 ev_basis_of: EvBasisOf | None = None,
                 action_window: Callable[..., dict[str, Any]] | None = None, statement_timeout_ms: int = 30_000,
                 test_read_clock_override: Callable[[], datetime] | None = None) -> None:
        self._database_url = database_url
        self.link_rows, self.pin_of, self.envelope_of, self.action_window = link_rows, pin_of, envelope_of, action_window
        self.ev_basis_of = ev_basis_of
        self.test_read_clock_override = test_read_clock_override
        self._options = f"-c statement_timeout={int(statement_timeout_ms)}"
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise WorkStoreUnavailable("DATABASE_URL is not set, so the domain Action store cannot be read.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True,
                                         connect_args={"options": self._options})
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def snapshot(self, tenant_id: UUID, site_id: UUID, site_code: str, work: Callable[[_IndexTx], Any]) -> Any:
        """One read-only REPEATABLE READ transaction; `work` receives the read handle with the DB read time."""
        try:
            with self._connect().connect().execution_options(isolation_level="REPEATABLE READ") as c, c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                if self.test_read_clock_override is not None:
                    read_at = self.test_read_clock_override()
                    assert read_at.tzinfo is not None and read_at.utcoffset() == timedelta(0)
                else:
                    read_at = c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc)
                return work(_IndexTx(c, tenant_id, site_id, site_code, read_at, self))
        except (OperationalError, DBAPIError) as error:
            raise WorkStoreUnavailable(f"The domain Action store could not be read: {error.__class__.__name__}") \
                from error
