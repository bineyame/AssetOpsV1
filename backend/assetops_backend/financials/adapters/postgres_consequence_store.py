"""PostgreSQL financial consequence store (S4-02b phase 1, migration 0011).

The seventh product database writer (architecture guard rule 8). It only INSERTs into
`financial_consequence_revision`, its three link tables and `financial_consequence_work_attempt`; dirty work
rows are written by the migration's triggers inside the assumption-publication or FindingRevision transaction,
never here.

`load_input` reads, in one REPEATABLE READ snapshot, the exact public inputs of one FindingRevision for
`fuel_cost.quantify`: the revision and its Finding, its INTERVAL assessments (primary and every supporting)
with stored segments and their analytic runs' accepted input sets and Foundation revisions, the accepted
generator-power readings of that generator inside the Finding window, and the as-accepted Foundation and
binding revisions those readings name. `append` stores a consequence idempotently: under a per-FindingRevision
advisory lock, an identical consequence basis digest returns the stored ID (`replayed=True`); otherwise it
appends revision `n+1` with its links, at one `clock_timestamp()` instant taken after the lock.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Iterator
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError, ProgrammingError

from assetops_backend.financials import cold_consequence as cc
from assetops_backend.financials import fuel_cost as fc

RECOMPUTE_ACTOR = "service:assetops-consequence-recompute"
RUNNER_LOCK_PREFIX = "financial_consequence_runner:"


class ConsequenceStoreUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class Appended:
    consequence_revision_id: UUID
    revision_no: int
    recorded_at: datetime
    replayed: bool


def _at(value: str | None) -> datetime | None:
    return None if value is None else datetime.fromisoformat(value.replace("Z", "+00:00"))


class PostgresConsequenceStore:
    def __init__(self, database_url: str | None, *, link_rows: Callable[..., list] | None = None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None
        # W2-04: the S4-05 link-row reader on the caller's connection (`evidence.composition.build_link_rows_reader`),
        # so the cold worker classifies its exact evidence inside its own snapshot.
        self._link_rows = link_rows

    def _connect(self) -> Engine:
        if not self._database_url:
            raise ConsequenceStoreUnavailable("DATABASE_URL is not set, so the consequence store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def _run(self, work, isolation: str = "READ COMMITTED"):
        try:
            with self._connect().connect().execution_options(isolation_level=isolation) as c:
                with c.begin():
                    return work(c)
        except (OperationalError, ProgrammingError) as error:
            raise ConsequenceStoreUnavailable(f"The consequence store failed: {error.orig}") from error

    # ---- exact inputs --------------------------------------------------------------------------------------

    def load_input(self, tenant_id: UUID, site_id: UUID, finding_id: UUID,
                   finding_revision_id: UUID) -> fc.FindingInput | None:
        """The exact persisted inputs of one FindingRevision of this Site; None if it is not this Site's."""
        scope = {"t": tenant_id, "s": site_id}

        def work(c: Connection) -> fc.FindingInput | None:
            head = c.execute(text(
                "SELECT r.id, r.finding_id, r.episode_start, r.episode_end, r.lifecycle, r.claim, "
                "f.generator_asset_id FROM finding_revision r JOIN finding f ON f.id = r.finding_id "
                "AND f.tenant_id = r.tenant_id AND f.site_id = r.site_id "
                "WHERE r.tenant_id = :t AND r.site_id = :s AND r.id = :r AND r.finding_id = :f"),
                {**scope, "r": finding_revision_id, "f": finding_id}).first()
            if head is None:
                return None
            asset = str(head.generator_asset_id)
            links = c.execute(text(
                "SELECT a.assessment_revision_id, a.analytic_run_id, a.scope, a.is_primary, v.result, "
                "run.foundation_revision_ids FROM finding_revision_assessment a "
                "JOIN assessment_revision v ON v.id = a.assessment_revision_id AND v.tenant_id = a.tenant_id "
                "AND v.site_id = a.site_id JOIN analytic_run run ON run.id = a.analytic_run_id "
                "AND run.tenant_id = a.tenant_id AND run.site_id = a.site_id "
                "WHERE a.tenant_id = :t AND a.site_id = :s AND a.finding_revision_id = :r "
                "ORDER BY a.scope, a.is_primary DESC, a.assessment_revision_id"),
                {**scope, "r": finding_revision_id}).all()
            runs = sorted({row.analytic_run_id for row in links if row.scope == "INTERVAL"}, key=str)
            run_evidence: dict[str, set[str]] = {str(r): set() for r in runs}
            for row in c.execute(text(
                    "SELECT run_id, evidence_id FROM analytic_run_evidence WHERE tenant_id = :t AND site_id = :s "
                    "AND run_id = ANY(:runs)"), {**scope, "runs": runs}):
                run_evidence[str(row.run_id)].add(str(row.evidence_id))
            assessments = []
            for row in links:
                result = row.result or {}
                segments = tuple(fc.Segment(_at(s["start"]), _at(s["end"]), bool(s.get("observed")),
                                            s["classification"]) for s in result.get("segments") or ())
                assessments.append(fc.AssessmentInput(
                    str(row.assessment_revision_id), str(row.analytic_run_id), row.scope, bool(row.is_primary),
                    None if result.get("generator_asset_id") is None else str(result["generator_asset_id"]),
                    segments, frozenset(run_evidence.get(str(row.analytic_run_id), ())),
                    frozenset(str(x) for x in (row.foundation_revision_ids or ()))))
            readings = [fc.PowerReading(str(r.id), str(r.asset_id), r.interval_start, r.interval_end,
                                        r.normalized_value_text, r.normalized_unit, r.quality, r.envelope_sha256,
                                        str(r.foundation_revision_id), str(r.binding_revision_id))
                        for r in c.execute(text(
                            "SELECT e.id, e.asset_id, e.interval_start, e.interval_end, e.normalized_value_text, "
                            "e.normalized_unit, e.quality, e.envelope_sha256, e.foundation_revision_id, "
                            "e.binding_revision_id FROM accepted_evidence e JOIN ingestion_disposition d "
                            "ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal "
                            "WHERE e.tenant_id = :t AND e.site_id = :s AND d.decision = 'ACCEPTED' "
                            "AND d.accepted_evidence_id = e.id AND e.role = :role "
                            "AND CAST(e.asset_id AS text) = :asset AND e.interval_start IS NOT NULL "
                            "AND e.interval_start < :hi AND e.interval_end > :lo ORDER BY e.interval_start, e.id"),
                            {**scope, "role": fc.POWER_ROLE, "asset": asset, "lo": head.episode_start,
                             "hi": head.episode_end})]
            asset_code = c.execute(text(
                "SELECT asset_code FROM asset WHERE tenant_id = :t AND site_id = :s AND CAST(id AS text) = :a"),
                {**scope, "a": asset}).scalar_one_or_none()
            foundation_ids = sorted({r.foundation_revision_id for r in readings}, key=str)
            foundations = tuple(fc.FoundationRevision(
                str(r.id), r.valid_from, r.valid_to,
                tuple((p[0], p[1]) for p in (r.sfc or ()))) for r in c.execute(text(
                    "SELECT f.id, f.valid_from, f.valid_to, (SELECT jsonb_agg(jsonb_build_array(p->>'value', "
                    "p->>'unit')) FROM jsonb_array_elements(COALESCE(f.content->'components', '[]'::jsonb)) comp, "
                    "jsonb_array_elements(COALESCE(comp->'properties', '[]'::jsonb)) p "
                    "WHERE comp->>'component_id' = :code AND p->>'property_key' = :key) AS sfc "
                    "FROM foundation_revision f WHERE f.tenant_id = :t AND f.site_id = :s "
                    "AND CAST(f.id AS text) = ANY(:ids)"),
                    {**scope, "code": asset_code, "key": fc.SFC_PROPERTY, "ids": foundation_ids}))
            binding_ids = sorted({r.binding_revision_id for r in readings}, key=str)
            bindings = tuple(fc.BindingRevision(str(r.id), r.valid_from, r.valid_to) for r in c.execute(text(
                "SELECT id, valid_from, valid_to FROM signal_binding_revision WHERE tenant_id = :t AND site_id = :s "
                "AND CAST(id AS text) = ANY(:ids)"), {**scope, "ids": binding_ids}))
            claim = head.claim or {}
            spans = tuple(fc.CandidateSpan(_at(s["start"]), _at(s["end"]), str(s.get("assessment_revision_id")))
                          for s in claim.get("candidate_spans") or ())
            return fc.FindingInput(str(tenant_id), str(site_id), str(head.finding_id), str(head.id), asset,
                                   head.episode_start, head.episode_end, head.lifecycle, spans, tuple(assessments),
                                   tuple(readings), foundations, bindings)

        return self._run(work, "REPEATABLE READ")

    # ---- idempotent append ---------------------------------------------------------------------------------

    def append(self, c_: fc.Consequence, actor_id: str = RECOMPUTE_ACTOR) -> Appended:
        f, q, p = c_.finding, c_.quantity, c_.price
        scope = {"t": UUID(f.tenant_id), "s": UUID(f.site_id)}
        frid = UUID(f.finding_revision_id)

        def work(c: Connection) -> Appended:
            c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended("
                           "'financial_consequence:' || :r || ':' || :k, 0))"),
                      {"r": str(frid), "k": fc.CONSEQUENCE_TYPE})
            same = c.execute(text(
                "SELECT id, revision_no, recorded_at FROM financial_consequence_revision WHERE finding_revision_id = :r "
                "AND consequence_type = :k AND consequence_basis_sha256 = :b"),
                {"r": frid, "k": fc.CONSEQUENCE_TYPE, "b": c_.basis_sha256}).first()
            if same is not None:
                return Appended(same[0], same[1], same[2], True)
            head = c.execute(text(
                "SELECT id, revision_no FROM financial_consequence_revision WHERE finding_revision_id = :r "
                "AND consequence_type = :k ORDER BY revision_no DESC LIMIT 1"),
                {"r": frid, "k": fc.CONSEQUENCE_TYPE}).first()
            at = c.execute(text("SELECT clock_timestamp()")).scalar_one()
            cid, no = uuid4(), 1 if head is None else head[1] + 1
            c.execute(text(
                "INSERT INTO financial_consequence_revision (id, tenant_id, site_id, finding_id, finding_revision_id, "
                "consequence_type, revision_no, prior_consequence_revision_id, window_start, window_end, "
                "overlap_group, basis_kind, model_id, formula_version, parameter_version, parameter_sha256, "
                "sfc_upper_multiplier, state, quantity_state, quantity_reason, quantity_detail, quantity_unit, "
                "quantity_low, quantity_high, quantity_high_exact, price_state, price_reason, price_revision_id, "
                "price_value, price_currency, price_considered, amount_low, amount_high, currency, limitations, "
                "technical_input_sha256, consequence_basis_sha256, actor_id, recorded_at) VALUES (:id, :t, :s, :f, "
                ":r, :k, :no, :prior, :ws, :we, :og, :bk, :model, :fv, :pv, :psha, :mult, :state, :qs, :qr, :qd, "
                ":qu, :ql, :qh, :qx, :ps, :pr, :prev, :pval, :pcur, CAST(:pcons AS jsonb), :al, :ah, :cur, "
                "CAST(:lim AS jsonb), :tech, "
                ":basis, :actor, :at)"),
                {**scope, "id": cid, "f": UUID(f.finding_id), "r": frid, "k": fc.CONSEQUENCE_TYPE, "no": no,
                 "prior": None if head is None else head[0], "ws": f.window_start, "we": f.window_end,
                 "og": f"{fc.CONSEQUENCE_TYPE}:finding:{f.finding_id}", "bk": fc.BASIS_KIND, "model": fc.MODEL_ID,
                 "fv": fc.FORMULA_VERSION, "pv": fc.PARAMETER_VERSION["parameter_version"],
                 "psha": fc.PARAMETER_SHA256, "mult": fc.MULTIPLIER, "state": c_.state, "qs": q.state,
                 "qr": q.reason, "qd": q.detail, "qu": fc.QUANTITY_UNIT, "ql": q.low, "qh": q.high,
                 "qx": None if q.high_exact is None else f"{q.high_exact.numerator}/{q.high_exact.denominator}",
                 "ps": p.state, "pr": p.reason, "prev": None if p.revision_id is None else UUID(p.revision_id),
                 "pval": p.value if p.state == "PRICED" else None,
                 "pcur": p.currency if p.state == "PRICED" else None,
                 "pcons": json.dumps([list(x) for x in p.considered]), "al": c_.amount_low, "ah": c_.amount_high,
                 "cur": c_.currency, "lim": json.dumps(list(c_.limitations)), "tech": c_.technical_input_sha256,
                 "basis": c_.basis_sha256, "actor": actor_id, "at": at})
            for a in f.assessments:
                if a.scope != "INTERVAL":
                    continue
                c.execute(text(
                    "INSERT INTO financial_consequence_assessment_revision (consequence_revision_id, tenant_id, "
                    "site_id, assessment_revision_id, analytic_run_id, is_primary) VALUES (:c, :t, :s, :a, :run, "
                    ":p)"), {**scope, "c": cid, "a": UUID(a.assessment_revision_id),
                             "run": UUID(a.analytic_run_id), "p": a.is_primary})
            if c_.state == "PRICED":
                c.execute(text(
                    "INSERT INTO financial_consequence_assumption_revision (consequence_revision_id, tenant_id, "
                    "site_id, assumption_revision_id, assignment_id, role) VALUES (:c, :t, :s, :a, :g, 'PRICE')"),
                    {**scope, "c": cid, "a": UUID(p.revision_id), "g": UUID(p.assignment_id)})
            for i in q.intervals:
                c.execute(text(
                    "INSERT INTO financial_consequence_power_interval (consequence_revision_id, tenant_id, site_id, "
                    "evidence_id, interval_start, interval_end, mean_kw, duration_seconds, sfc_l_per_kwh, "
                    "foundation_revision_id, binding_revision_id, envelope_sha256, covered_spans, containment) "
                    "VALUES (:c, :t, :s, :e, :a, :b, :kw, :sec, :sfc, :fr, :br, :sha, CAST(:spans AS jsonb), :cont)"),
                    {**scope, "c": cid, "e": UUID(i.evidence_id), "a": i.interval_start, "b": i.interval_end,
                     "kw": i.mean_kw, "sec": i.duration_seconds, "sfc": i.sfc_l_per_kwh,
                     "fr": UUID(i.foundation_revision_id), "br": UUID(i.binding_revision_id),
                     "sha": i.envelope_sha256, "cont": i.containment,
                     "spans": json.dumps([[fc.iso(s), fc.iso(e)] for s, e in i.covered_spans])})
            return Appended(cid, no, at, False)

        return self._run(work)

    # ---- durable dirty work --------------------------------------------------------------------------------

    def pending_work(self, tenant_id: UUID, site_id: UUID) -> list[dict[str, Any]]:
        """Dirty work of this Site with no SUCCEEDED attempt, oldest first, with its attempt count and its latest
        attempt (`last_attempt_no`, `last_outcome`, `last_finished_at`; null before any attempt). With no success,
        the latest attempt is the last FAILED one, which the runner's retry schedule reads (S4-02c item 4)."""
        def work(c: Connection):
            return [dict(r._mapping) for r in c.execute(text(
                "SELECT w.*, (SELECT count(*) FROM financial_consequence_work_attempt a WHERE a.work_id = w.id) "
                "AS attempts, last.attempt_no AS last_attempt_no, last.outcome AS last_outcome, "
                "last.finished_at AS last_finished_at FROM financial_consequence_work w "
                "LEFT JOIN LATERAL (SELECT a.attempt_no, a.outcome, a.finished_at FROM "
                "financial_consequence_work_attempt a WHERE a.work_id = w.id ORDER BY a.attempt_no DESC LIMIT 1) last "
                "ON true WHERE w.tenant_id = :t AND w.site_id = :s "
                "AND NOT EXISTS (SELECT 1 FROM financial_consequence_work_attempt a WHERE a.work_id = w.id "
                "AND a.outcome = 'SUCCEEDED') ORDER BY w.enqueued_at, w.id"), {"t": tenant_id, "s": site_id})]
        return self._run(work, "REPEATABLE READ")

    def db_now(self) -> datetime:
        """The database's `clock_timestamp()`: the one-off runner's default `now` (S4-02d phase 2, I3)."""
        return self._run(lambda c: c.execute(text("SELECT clock_timestamp()")).scalar_one())

    def pending_work_sites(self) -> list[dict[str, Any]]:
        """Every tenant/Site with dirty work and no SUCCEEDED attempt (the `pending_work` predicate), with its
        pending count, total attempts and oldest enqueue instant (S4-02d Site inventory: a Site with pending
        consequence work stays selected)."""
        def work(c: Connection):
            return [dict(r._mapping) for r in c.execute(text(
                "SELECT w.tenant_id, w.site_id, count(*) AS pending, min(w.enqueued_at) AS oldest_enqueued_at, "
                "coalesce(sum((SELECT count(*) FROM financial_consequence_work_attempt a WHERE a.work_id = w.id)), "
                "0) AS attempts FROM financial_consequence_work w WHERE NOT EXISTS (SELECT 1 FROM "
                "financial_consequence_work_attempt a WHERE a.work_id = w.id AND a.outcome = 'SUCCEEDED') "
                "GROUP BY w.tenant_id, w.site_id ORDER BY w.tenant_id, w.site_id"))]
        return self._run(work, "REPEATABLE READ")

    def evidence_target(self, tenant_id: UUID, site_id: UUID, accepted_evidence_id: UUID, finding_id: UUID,
                        finding_revision_id: UUID) -> dict[str, Any]:
        """One snapshot of what an `EVIDENCE_ACCEPTED` work row names, read only inside this tenant/Site: the
        accepted reading (stored role, asset, interval, and whether an ACCEPTED disposition binds it), the queued
        FindingRevision of that Finding (episode, Candidate spans, generator) and the Finding's highest
        `revision_no` in the same tenant/Site (the 0012 trigger's "latest"). A locator naming another Site's row
        reads as None here; nothing falls back to an unscoped lookup."""
        scope = {"t": tenant_id, "s": site_id}

        def work(c: Connection) -> dict[str, Any]:
            ev = c.execute(text(
                "SELECT e.role, CAST(e.asset_id AS text) AS asset_id, e.interval_start, e.interval_end, "
                "EXISTS (SELECT 1 FROM ingestion_disposition d WHERE d.batch_id = e.batch_id "
                "AND d.ordinal = e.ordinal AND d.decision = 'ACCEPTED' AND d.accepted_evidence_id = e.id) "
                "AS accepted FROM accepted_evidence e WHERE e.tenant_id = :t AND e.site_id = :s AND e.id = :e"),
                {**scope, "e": accepted_evidence_id}).first()
            rev = c.execute(text(
                "SELECT r.revision_no, r.episode_start, r.episode_end, r.claim, "
                "CAST(f.generator_asset_id AS text) AS generator_asset_id, (SELECT max(x.revision_no) FROM "
                "finding_revision x WHERE x.tenant_id = r.tenant_id AND x.site_id = r.site_id "
                "AND x.finding_id = r.finding_id) AS latest_revision_no FROM finding_revision r JOIN finding f "
                "ON f.id = r.finding_id AND f.tenant_id = r.tenant_id AND f.site_id = r.site_id "
                "WHERE r.tenant_id = :t AND r.site_id = :s AND r.id = :r AND r.finding_id = :f"),
                {**scope, "r": finding_revision_id, "f": finding_id}).first()
            return {"evidence": None if ev is None else dict(ev._mapping),
                    "revision": None if rev is None else dict(rev._mapping)}

        return self._run(work, "REPEATABLE READ")

    @contextmanager
    def claim_site(self, tenant_id: UUID, site_id: UUID) -> Iterator[bool]:
        """The runner's Site claim (S4-02c item 4, re-review N3): a session `pg_try_advisory_lock` keyed by
        `financial_consequence_runner:` plus the Site, on one dedicated connection held for the whole run. Yields
        whether this run holds the claim. The lock is released explicitly in `finally`; if the unlock cannot run,
        the connection is invalidated rather than returned to the pool still holding it. A killed runner's
        connection closes and Postgres releases its session lock with it."""
        try:
            conn = self._connect().connect().execution_options(isolation_level="AUTOCOMMIT")
        except (OperationalError, ProgrammingError) as error:
            raise ConsequenceStoreUnavailable(f"The consequence store failed: {error.orig}") from error
        key = {"k": RUNNER_LOCK_PREFIX + str(site_id)}
        held = False
        try:
            try:
                held = bool(conn.execute(text("SELECT pg_try_advisory_lock(hashtextextended(:k, 0))"),
                                         key).scalar_one())
            except (OperationalError, ProgrammingError) as error:
                raise ConsequenceStoreUnavailable(f"The consequence store failed: {error.orig}") from error
            yield held
        finally:
            try:
                if held:
                    conn.execute(text("SELECT pg_advisory_unlock(hashtextextended(:k, 0))"), key)
            except Exception:  # noqa: BLE001 - never pool a connection that may still hold the claim
                conn.invalidate()
            finally:
                conn.close()

    def record_attempt(self, tenant_id: UUID, site_id: UUID, work_id: UUID, *, succeeded: bool,
                       consequence_revision_ids: tuple[UUID, ...] = (), error_code: str | None = None,
                       error_detail: str | None = None, actor_id: str = RECOMPUTE_ACTOR,
                       skip_if_succeeded: bool = False, no_op_reason: str | None = None) -> int:
        """Append one attempt to a work item under its lock; returns the attempt number. With
        `skip_if_succeeded`, a work item another worker already finished records nothing and returns 0. A typed
        `no_op_reason` marks a SUCCEEDED attempt that appended nothing (migration 0012's CHECK enforces both)."""
        def work(c: Connection) -> int:
            c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('financial_consequence_work:' || :w, 0))"),
                      {"w": str(work_id)})
            if skip_if_succeeded and c.execute(text(
                    "SELECT 1 FROM financial_consequence_work_attempt WHERE work_id = :w AND outcome = 'SUCCEEDED'"),
                    {"w": work_id}).first() is not None:
                return 0
            n = c.execute(text("SELECT count(*) FROM financial_consequence_work_attempt WHERE work_id = :w"),
                          {"w": work_id}).scalar_one() + 1
            c.execute(text(
                "INSERT INTO financial_consequence_work_attempt (id, work_id, tenant_id, site_id, attempt_no, outcome, "
                "error_code, error_detail, consequence_revision_ids, actor_id, finished_at, no_op_reason) VALUES (:id, "
                ":w, :t, :s, :n, :o, :code, :detail, CAST(:ids AS jsonb), :actor, clock_timestamp(), :noop)"),
                {"id": uuid4(), "w": work_id, "t": tenant_id, "s": site_id, "n": n,
                 "o": "SUCCEEDED" if succeeded else "FAILED", "code": None if succeeded else (error_code or "FAILED"),
                 "detail": error_detail, "ids": json.dumps([str(x) for x in consequence_revision_ids]),
                 "actor": actor_id, "noop": no_op_reason if succeeded else None})
            return n
        return self._run(work)

    # ---- phase 2a: recompute targets and the consequence read ------------------------------------------------

    def latest_revisions_overlapping(self, tenant_id: UUID, site_id: UUID, lo: datetime,
                                     hi: datetime | None) -> list[tuple[UUID, UUID]]:
        """(finding_id, latest FindingRevision id) of every Finding of this Site whose latest revision's
        episode overlaps `[lo, hi)` (half-open; `hi` None is open-ended)."""
        def work(c: Connection):
            return [(r[0], r[1]) for r in c.execute(text(
                "SELECT r.finding_id, r.id FROM finding_revision r WHERE r.tenant_id = :t AND r.site_id = :s "
                "AND r.revision_no = (SELECT max(x.revision_no) FROM finding_revision x WHERE x.finding_id = "
                "r.finding_id) AND r.episode_end > :lo "
                "AND (CAST(:hi AS timestamptz) IS NULL OR r.episode_start < CAST(:hi AS timestamptz)) "
                "ORDER BY r.episode_start, r.id"), {"t": tenant_id, "s": site_id, "lo": lo, "hi": hi})]
        return self._run(work, "REPEATABLE READ")

    def site_history(self, tenant_id: UUID, site_id: UUID, cutoff: datetime | None,
                     after: tuple[datetime, UUID] | None, limit: int) -> dict[str, Any]:
        """S4-08: one REPEATABLE READ snapshot of a Site's consequence revisions recorded at or before `cutoff`.

        Read-only. A missing cutoff is fixed from the database clock (the clock `recorded_at` uses) as the
        snapshot's first statement. The fence (count and maximum `(recorded_at, id)`) covers every in-scope row
        at or before the cutoff, off-page rows included. The page is keyset `(recorded_at DESC, id DESC)` after
        `after`, `limit + 1` rows. For the page's Findings it returns every FindingRevision with its latest
        consequence `(recorded_at, id)` at or before the cutoff, so the caller can classify currentness at the
        cutoff without current heads; each row's stored price links with their assignment intervals; and each
        row's prior consequence digest and price, for a supported "only the price changed" sentence."""
        def work(c: Connection) -> dict[str, Any]:
            cut = cutoff if cutoff is not None else c.execute(text("SELECT clock_timestamp()")).scalar_one()
            scope = {"t": tenant_id, "s": site_id, "k": fc.CONSEQUENCE_TYPE, "cut": cut}
            where = ("FROM financial_consequence_revision WHERE tenant_id = :t AND site_id = :s "
                     "AND consequence_type = :k AND recorded_at <= :cut ")
            fence = c.execute(text("SELECT count(*) AS n, max(recorded_at) AS max_at " + where), scope).one()
            max_id = None if fence.max_at is None else c.execute(text(
                "SELECT max(id::text) " + where + "AND recorded_at = :m"), {**scope, "m": fence.max_at}).scalar_one()
            keyset = "" if after is None else "AND (recorded_at, id) < (:ra, :rid) "
            page = [dict(x._mapping) for x in c.execute(text(
                "SELECT * " + where + keyset + "ORDER BY recorded_at DESC, id DESC LIMIT :n"),
                {**scope, "n": limit + 1, **({} if after is None else {"ra": after[0], "rid": after[1]})})]
            findings = list({r["finding_id"] for r in page})
            revisions = [dict(x._mapping) for x in c.execute(text(
                "SELECT fr.id, fr.finding_id, fr.revision_no, fr.created_at, fr.title, fr.episode_start, "
                "fr.episode_end, (SELECT c2.id FROM financial_consequence_revision c2 WHERE c2.tenant_id = :t "
                "AND c2.site_id = :s AND c2.consequence_type = :k AND c2.finding_revision_id = fr.id "
                "AND c2.recorded_at <= :cut ORDER BY c2.recorded_at DESC, c2.id DESC LIMIT 1) "
                "AS latest_consequence_id FROM finding_revision fr WHERE fr.tenant_id = :t AND fr.site_id = :s "
                "AND fr.finding_id = ANY(:f) ORDER BY fr.finding_id, fr.revision_no"),
                {**scope, "f": findings})] if findings else []
            ids = [r["id"] for r in page]
            links: dict[Any, list[dict[str, Any]]] = {}
            for x in (c.execute(text(
                    "SELECT l.consequence_revision_id, l.assumption_revision_id, l.assignment_id, l.role, "
                    "a.tenant_id AS a_tenant_id, a.site_id AS a_site_id, a.revision_id AS a_revision_id, "
                    "a.valid_from, a.valid_to, a.recorded_from, a.recorded_to "
                    "FROM financial_consequence_assumption_revision l "
                    "LEFT JOIN financial_assumption_assignment a ON a.id = l.assignment_id "
                    "WHERE l.tenant_id = :t AND l.site_id = :s AND l.consequence_revision_id = ANY(:ids) "
                    "ORDER BY l.consequence_revision_id, l.assumption_revision_id"), {**scope, "ids": ids})
                      if ids else []):
                links.setdefault(x.consequence_revision_id, []).append(dict(x._mapping))
            prior_ids = [r["prior_consequence_revision_id"] for r in page
                         if r["prior_consequence_revision_id"] is not None]
            priors = {x.id: dict(x._mapping) for x in (c.execute(text(
                "SELECT id, technical_input_sha256, price_revision_id, state FROM financial_consequence_revision "
                "WHERE tenant_id = :t AND site_id = :s AND id = ANY(:p)"), {**scope, "p": prior_ids})
                if prior_ids else [])}
            return {"cutoff": cut, "fence": {"count": fence.n, "max_recorded_at": fence.max_at, "max_id": max_id},
                    "page": page, "finding_revisions": revisions, "links": links, "priors": priors}
        return self._run(work, "REPEATABLE READ")

    def locate(self, tenant_id: UUID, site_id: UUID, finding_id: UUID,
               consequence_revision_id: UUID) -> UUID | None:
        """The FindingRevision of one exact consequence revision of this Site's Finding, else None."""
        def work(c: Connection):
            return c.execute(text(
                "SELECT finding_revision_id FROM financial_consequence_revision WHERE tenant_id = :t "
                "AND site_id = :s AND finding_id = :f AND id = :c"),
                {"t": tenant_id, "s": site_id, "f": finding_id, "c": consequence_revision_id}).scalar_one_or_none()
        return self._run(work)

    def chain(self, tenant_id: UUID, site_id: UUID, finding_id: UUID, finding_revision_id: UUID, *,
              consequence_revision_id: UUID | None, after_revision_no: int, limit: int) -> dict[str, Any]:
        """One snapshot of a FindingRevision's consequence chain: its head, an optional exact revision, a
        keyset page, the lineage links of every returned revision and the pending work that touches it.

        Pending work touches the read when it names this Finding (a FindingRevision append, or S4-02c accepted
        evidence: matched by Finding, its queued revision is only a locator kept for diagnostics) or when an
        assumption publication's affected range overlaps the FindingRevision's window."""
        scope = {"t": tenant_id, "s": site_id, "f": finding_id, "r": finding_revision_id,
                 "k": fc.CONSEQUENCE_TYPE}

        def work(c: Connection):
            base = ("SELECT * FROM financial_consequence_revision WHERE tenant_id = :t AND site_id = :s "
                    "AND finding_id = :f AND finding_revision_id = :r AND consequence_type = :k ")
            head = c.execute(text(base + "ORDER BY revision_no DESC LIMIT 1"), scope).first()
            exact = None if consequence_revision_id is None else c.execute(
                text(base + "AND id = :c"), {**scope, "c": consequence_revision_id}).first()
            page = c.execute(text(base + "AND revision_no > :after ORDER BY revision_no LIMIT :n"),
                             {**scope, "after": after_revision_no, "n": limit + 1}).all()
            total = c.execute(text(base.replace("SELECT *", "SELECT count(*)")), scope).scalar_one()
            rows = [dict(x._mapping) for x in page]
            ids = list({x["id"] for x in rows} | {x.id for x in (head, exact) if x is not None})
            links: dict[str, dict[Any, list[dict[str, Any]]]] = {}
            for name, table, order in (
                    ("assessments", "financial_consequence_assessment_revision",
                     "is_primary DESC, assessment_revision_id"),
                    ("assumptions", "financial_consequence_assumption_revision", "assumption_revision_id"),
                    ("intervals", "financial_consequence_power_interval", "interval_start, evidence_id")):
                out: dict[Any, list[dict[str, Any]]] = {}
                for x in c.execute(text(f"SELECT * FROM {table} WHERE tenant_id = :t AND site_id = :s "
                                        f"AND consequence_revision_id = ANY(:ids) ORDER BY {order}"),
                                   {**scope, "ids": ids}):
                    out.setdefault(x.consequence_revision_id, []).append(dict(x._mapping))
                links[name] = out
            window = c.execute(text("SELECT episode_start, episode_end FROM finding_revision WHERE tenant_id = :t "
                                    "AND site_id = :s AND id = :r"), scope).first()
            pending = [] if window is None else [dict(x._mapping) for x in c.execute(text(
                "SELECT w.id, w.cause, w.assumption_revision_id, w.finding_revision_id, w.accepted_evidence_id, "
                "w.affected_from, "
                "w.affected_to, w.enqueued_at, (SELECT count(*) FROM financial_consequence_work_attempt a "
                "WHERE a.work_id = w.id) AS attempts, (SELECT a.error_code FROM financial_consequence_work_attempt a "
                "WHERE a.work_id = w.id ORDER BY a.attempt_no DESC LIMIT 1) AS last_error_code "
                "FROM financial_consequence_work w WHERE w.tenant_id = :t AND w.site_id = :s "
                "AND NOT EXISTS (SELECT 1 FROM financial_consequence_work_attempt a WHERE a.work_id = w.id "
                "AND a.outcome = 'SUCCEEDED') AND ((w.cause IN ('FINDING_REVISION_APPENDED', 'EVIDENCE_ACCEPTED') "
                "AND w.finding_id = :f) "
                "OR (w.cause = 'ASSUMPTION_PUBLISHED' AND (w.affected_to IS NULL OR w.affected_to > :lo) "
                "AND w.affected_from < :hi)) ORDER BY w.enqueued_at, w.id"),
                {**scope, "lo": window[0], "hi": window[1]})]
            return {"head": None if head is None else dict(head._mapping),
                    "exact": None if exact is None else dict(exact._mapping),
                    "page": rows[:limit], "has_more": len(rows) > limit, "total": total, "links": links,
                    "pending": pending}
        return self._run(work, "REPEATABLE READ")

    # ---- raw rows (tests and diagnostics) -------------------------------------------------------------------

    def rows(self, tenant_id: UUID, site_id: UUID) -> dict[str, list[dict[str, Any]]]:
        scope = {"t": tenant_id, "s": site_id}

        def work(c: Connection):
            out = {}
            for table, order in (("financial_consequence_revision", "finding_revision_id, revision_no"),
                                 ("financial_consequence_assessment_revision", "consequence_revision_id, "
                                                                               "assessment_revision_id"),
                                 ("financial_consequence_assumption_revision", "consequence_revision_id"),
                                 ("financial_consequence_power_interval", "consequence_revision_id, interval_start"),
                                 ("financial_consequence_work", "enqueued_at, id"),
                                 ("financial_consequence_work_attempt", "work_id, attempt_no")):
                out[table] = [dict(r._mapping) for r in c.execute(text(
                    f"SELECT * FROM {table} WHERE tenant_id = :t AND site_id = :s ORDER BY {order}"), scope)]
            return out
        return self._run(work, "REPEATABLE READ")

    # ---- W2-04: cold consequence (migration 0023) -------------------------------------------------------------
    # `.agent/W2-04-build-spec.md` "Money schema `0023` and rules", Q5/Q6. This store alone INSERTs
    # `cold_consequence_revision`, `cold_consequence_evidence` and `cold_consequence_work_attempt`; work rows come
    # only from the 0023 triggers. Server times (`created_at`, `finished_at`) are always the column defaults: no
    # method accepts a client timestamp. The mini-grid methods above are unchanged.
    #
    # `cold_unit` opens one REPEATABLE READ transaction whose first statement takes the work lock
    # `pg_advisory_xact_lock(hashtextextended('cold_consequence:' || work_id, 0))`. Its snapshot starts at that
    # statement, so a concurrent worker's success committed while this one waited is caught by the unique
    # constraints (attempt number, consequence basis) on write; the worker then records the failure through
    # `cold_record_failure`, which re-checks success under the lock at READ COMMITTED and records nothing when
    # the work already succeeded.

    @contextmanager
    def cold_unit(self, tenant_id: UUID, site_id: UUID, work_id: UUID) -> Iterator["ColdUnit"]:
        try:
            with self._connect().connect().execution_options(isolation_level="REPEATABLE READ") as c:
                with c.begin():
                    c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('cold_consequence:' || :w, 0))"),
                              {"w": str(work_id)})
                    yield ColdUnit(c, tenant_id, site_id, work_id, self._link_rows)
        except (OperationalError, ProgrammingError) as error:
            raise ConsequenceStoreUnavailable(f"The consequence store failed: {error.orig}") from error

    def cold_record_failure(self, tenant_id: UUID, site_id: UUID, work_id: UUID, error_code: str) -> int:
        """Append a typed FAILED attempt in a fresh transaction under the work lock; returns its number, or 0 when
        the work is not this Site's or already has a SUCCEEDED attempt (nothing is recorded)."""
        def work(c: Connection) -> int:
            c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('cold_consequence:' || :w, 0))"),
                      {"w": str(work_id)})
            p = {"t": tenant_id, "s": site_id, "w": work_id}
            if c.execute(text("SELECT 1 FROM cold_consequence_work WHERE tenant_id = :t AND site_id = :s "
                              "AND id = :w"), p).first() is None:
                return 0
            if c.execute(text("SELECT 1 FROM cold_consequence_work_attempt WHERE tenant_id = :t AND site_id = :s "
                              "AND work_id = :w AND outcome = 'SUCCEEDED'"), p).first() is not None:
                return 0
            return _cold_attempt(c, tenant_id, site_id, work_id, "FAILED", error_code, [])
        return self._run(work)

    def cold_pending_work(self, tenant_id: UUID, site_id: UUID) -> list[dict[str, Any]]:
        """Cold work of this Site with no SUCCEEDED attempt in `(enqueued_at, id)` order, with its latest attempt
        (`last_attempt_no`, `last_outcome`, `last_finished_at`; null before any attempt)."""
        def work(c: Connection):
            return [dict(r._mapping) for r in c.execute(text(
                "SELECT w.*, last.attempt_no AS last_attempt_no, last.outcome AS last_outcome, "
                "last.finished_at AS last_finished_at FROM cold_consequence_work w "
                "LEFT JOIN LATERAL (SELECT a.attempt_no, a.outcome, a.finished_at FROM cold_consequence_work_attempt a "
                "WHERE a.tenant_id = w.tenant_id AND a.site_id = w.site_id AND a.work_id = w.id "
                "ORDER BY a.attempt_no DESC LIMIT 1) last ON true WHERE w.tenant_id = :t AND w.site_id = :s "
                "AND NOT EXISTS (SELECT 1 FROM cold_consequence_work_attempt a WHERE a.tenant_id = w.tenant_id "
                "AND a.site_id = w.site_id AND a.work_id = w.id AND a.outcome = 'SUCCEEDED') "
                "ORDER BY w.enqueued_at, w.id"), {"t": tenant_id, "s": site_id})]
        return self._run(work, "REPEATABLE READ")

    @contextmanager
    def cold_claim_site(self, tenant_id: UUID, site_id: UUID) -> Iterator[bool]:
        """The cold runner's Site claim: a session `pg_try_advisory_lock` keyed by `cold_consequence_runner:` plus
        the Site on one dedicated connection, released in `finally` (invalidated if the unlock cannot run)."""
        try:
            conn = self._connect().connect().execution_options(isolation_level="AUTOCOMMIT")
        except (OperationalError, ProgrammingError) as error:
            raise ConsequenceStoreUnavailable(f"The consequence store failed: {error.orig}") from error
        key = {"k": COLD_RUNNER_LOCK_PREFIX + str(site_id)}
        held = False
        try:
            try:
                held = bool(conn.execute(text("SELECT pg_try_advisory_lock(hashtextextended(:k, 0))"),
                                         key).scalar_one())
            except (OperationalError, ProgrammingError) as error:
                raise ConsequenceStoreUnavailable(f"The consequence store failed: {error.orig}") from error
            yield held
        finally:
            try:
                if held:
                    conn.execute(text("SELECT pg_advisory_unlock(hashtextextended(:k, 0))"), key)
            except Exception:  # noqa: BLE001 - never pool a connection that may still hold the claim
                conn.invalidate()
            finally:
                conn.close()

    def cold_rows(self, tenant_id: UUID, site_id: UUID) -> dict[str, list[dict[str, Any]]]:
        """Raw cold consequence rows of one Site (tests and diagnostics)."""
        scope = {"t": tenant_id, "s": site_id}

        def work(c: Connection):
            out = {}
            for table, order in (("cold_consequence_revision", "created_at, id"),
                                 ("cold_consequence_evidence", "consequence_revision_id, evidence_id, use"),
                                 ("cold_consequence_work", "enqueued_at, id"),
                                 ("cold_consequence_work_attempt", "work_id, attempt_no")):
                out[table] = [dict(r._mapping) for r in c.execute(text(
                    f"SELECT * FROM {table} WHERE tenant_id = :t AND site_id = :s ORDER BY {order}"), scope)]
            return out
        return self._run(work, "REPEATABLE READ")


COLD_RUNNER_LOCK_PREFIX = "cold_consequence_runner:"


def _cold_attempt(c: Connection, tenant_id: UUID, site_id: UUID, work_id: UUID, outcome: str,
                  error_code: str | None, revision_ids: list[UUID]) -> int:
    n = c.execute(text("SELECT count(*) FROM cold_consequence_work_attempt WHERE tenant_id = :t AND site_id = :s "
                       "AND work_id = :w"), {"t": tenant_id, "s": site_id, "w": work_id}).scalar_one() + 1
    c.execute(text(
        "INSERT INTO cold_consequence_work_attempt (id, tenant_id, site_id, work_id, attempt_no, outcome, error_code, "
        "consequence_revision_ids) VALUES (:id, :t, :s, :w, :n, :o, :code, CAST(:ids AS jsonb))"),
        {"id": uuid4(), "t": tenant_id, "s": site_id, "w": work_id, "n": n, "o": outcome, "code": error_code,
         "ids": json.dumps([str(x) for x in revision_ids])})
    return n


def _low(value: Any) -> str | None:
    return None if value is None else str(value).lower()


class ColdUnit:
    """One locked, repeatable-read cold work transaction (see `PostgresConsequenceStore.cold_unit`)."""

    def __init__(self, c: Connection, tenant_id: UUID, site_id: UUID, work_id: UUID,
                 link_rows: Callable[..., list] | None) -> None:
        self._c = c
        self._p = {"t": tenant_id, "s": site_id, "w": work_id}
        self._link_rows = link_rows
        self.tenant_id, self.site_id, self.work_id = tenant_id, site_id, work_id

    def work(self) -> dict[str, Any] | None:
        """This Site's work row with `succeeded` (a SUCCEEDED attempt is visible), or None when foreign/missing."""
        row = self._c.execute(text(
            "SELECT w.*, EXISTS (SELECT 1 FROM cold_consequence_work_attempt a WHERE a.tenant_id = w.tenant_id "
            "AND a.site_id = w.site_id AND a.work_id = w.id AND a.outcome = 'SUCCEEDED') AS succeeded "
            "FROM cold_consequence_work w WHERE w.tenant_id = :t AND w.site_id = :s AND w.id = :w"), self._p).first()
        return None if row is None else dict(row._mapping)

    def targets(self, work: dict[str, Any]) -> list[UUID]:
        """The exact cold FindingRevisions a work item derives for. FINDING: its revision. EPISODE: the cold
        revisions whose claim names its episode revision (none for an episode without a warranted Finding).
        SOURCE_GATE: the latest cold FindingRevision per Finding of the work's window and room whose cited
        evidence, or its claimed episode revision's evidence, came from the linked batch."""
        c, p = self._c, self._p
        if work["cause"] == "FINDING_REVISION_APPENDED":
            return [work["finding_revision_id"]]
        if work["cause"] == "EPISODE_REVISION_APPENDED":
            return list(c.execute(text(
                "SELECT r.id FROM finding_revision r WHERE r.tenant_id = :t AND r.site_id = :s "
                "AND r.domain = 'cold_chain' AND r.claim->>'episode_revision_id' = :e ORDER BY r.created_at, r.id"),
                {**p, "e": str(work["episode_revision_id"])}).scalars())
        return list(c.execute(text(
            "SELECT r.id FROM finding_revision r JOIN assessment_revision a ON a.tenant_id = r.tenant_id "
            "AND a.site_id = r.site_id AND a.id = r.assessment_revision_id "
            "WHERE r.tenant_id = :t AND r.site_id = :s AND r.domain = 'cold_chain' "
            "AND r.revision_no = (SELECT max(x.revision_no) FROM finding_revision x WHERE x.tenant_id = r.tenant_id "
            "AND x.site_id = r.site_id AND x.finding_id = r.finding_id) "
            "AND a.window_start = :ws AND a.window_end = :we "
            "AND cold_consequence_room(a.tenant_id, a.site_id, a.id) = :room "
            "AND (EXISTS (SELECT 1 FROM finding_revision_evidence l JOIN accepted_evidence ev "
            "ON ev.tenant_id = l.tenant_id AND ev.site_id = l.site_id AND ev.id = l.evidence_id "
            "WHERE l.tenant_id = r.tenant_id AND l.site_id = r.site_id AND l.finding_revision_id = r.id "
            "AND ev.batch_id = :b) OR EXISTS (SELECT 1 FROM cold_episode_evidence l JOIN accepted_evidence ev "
            "ON ev.tenant_id = l.tenant_id AND ev.site_id = l.site_id AND ev.id = l.evidence_id "
            "WHERE l.tenant_id = r.tenant_id AND l.site_id = r.site_id "
            "AND CAST(l.episode_revision_id AS text) = r.claim->>'episode_revision_id' AND ev.batch_id = :b)) "
            "ORDER BY r.created_at, r.id"),
            {**p, "ws": work["window_start"], "we": work["window_end"], "room": work["room_asset_id"],
             "b": work["publication_batch_id"]}).scalars())

    def basis(self, finding_revision_id: UUID) -> cc.ColdBasis | None:
        """The exact basis of one cold FindingRevision in this snapshot, or None when the revision is not this
        Site's cold revision. Missing episode/assessment parts are None for `check_basis` to refuse."""
        c, p = self._c, {**self._p, "r": finding_revision_id}
        fr = c.execute(text(
            "SELECT r.id, r.finding_id, r.lifecycle, r.basis_sha256, r.assessment_revision_id, r.claim "
            "FROM finding_revision r WHERE r.tenant_id = :t AND r.site_id = :s AND r.id = :r "
            "AND r.domain = 'cold_chain'"), p).first()
        if fr is None:
            return None
        claim = fr.claim if isinstance(fr.claim, dict) else {}
        try:
            episode_revision = UUID(str(claim.get("episode_revision_id")))
        except ValueError:
            episode_revision = None
        er = None if episode_revision is None else c.execute(text(
            "SELECT er.id, er.episode_id, er.assessment_revision_id, er.basis_sha256, er.claim_level, "
            "er.degree_minutes_low, er.degree_minutes_high, er.coverage, e.kind FROM cold_episode_revision er "
            "JOIN cold_episode e ON e.tenant_id = er.tenant_id AND e.site_id = er.site_id AND e.id = er.episode_id "
            "WHERE er.tenant_id = :t AND er.site_id = :s AND er.id = :e"), {**p, "e": episode_revision}).first()
        a = c.execute(text(
            "SELECT a.id, a.basis_sha256, a.window_start, a.window_end, run.knowledge_cutoff, "
            "cold_consequence_room(a.tenant_id, a.site_id, a.id) AS room FROM assessment_revision a "
            "JOIN analytic_run run ON run.tenant_id = a.tenant_id AND run.site_id = a.site_id "
            "AND run.id = a.analytic_run_id WHERE a.tenant_id = :t AND a.site_id = :s AND a.id = :a"),
            {**p, "a": fr.assessment_revision_id}).first()
        episode_links = [] if er is None else [cc.EvidenceUse(str(x[0]), x[1], x[2]) for x in c.execute(text(
            "SELECT evidence_id, use, reason FROM cold_episode_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND episode_revision_id = :e ORDER BY evidence_id, use"), {**p, "e": er.id}).all()]
        cited = [str(x) for x in c.execute(text(
            "SELECT evidence_id FROM finding_revision_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND finding_revision_id = :r ORDER BY evidence_id"), p).scalars()]
        evidence = cc.merged_evidence(episode_links, cited)
        ids = sorted({e.evidence_id for e in evidence})
        if ids and self._link_rows is None:
            raise RuntimeError("no S4-05 link reader is configured for the cold consequence source gate")
        rows = tuple(self._link_rows(c, self.tenant_id, self.site_id, ids)) if ids else ()
        return cc.ColdBasis(
            tenant_id=str(self.tenant_id).lower(), site_id=str(self.site_id).lower(),
            finding_revision_id=str(fr.id), finding_id=str(fr.finding_id), finding_lifecycle=fr.lifecycle,
            finding_basis_sha256=fr.basis_sha256, finding_assessment_revision_id=str(fr.assessment_revision_id),
            claim=claim,
            episode_revision_id=None if er is None else str(er.id),
            episode_id=None if er is None else str(er.episode_id),
            episode_kind=None if er is None else er.kind,
            episode_assessment_revision_id=None if er is None else str(er.assessment_revision_id),
            episode_basis_sha256=None if er is None else er.basis_sha256,
            claim_level=None if er is None else er.claim_level,
            degree_minutes_low=None if er is None else er.degree_minutes_low,
            degree_minutes_high=None if er is None else er.degree_minutes_high,
            coverage=None if er is None else er.coverage,
            assessment_revision_id=None if a is None else str(a.id),
            assessment_basis_sha256=None if a is None else a.basis_sha256,
            window_start=None if a is None else a.window_start, window_end=None if a is None else a.window_end,
            known_at=None if a is None else a.knowledge_cutoff, room_asset_id=None if a is None else _low(a.room),
            evidence=evidence, link_rows=rows)

    def append(self, consequence: cc.ColdConsequence) -> tuple[UUID, bool]:
        """Store one derived consequence idempotently: an identical `(finding_revision_id, kind, basis)` returns its
        ID (`True` = replayed); otherwise revision `max+1` of the Finding/kind chain with `prior_revision_id`,
        after checking the predecessor is the same Finding and kind (Q5), under a Finding/kind lock."""
        c, k = self._c, consequence
        p = {"t": self.tenant_id, "s": self.site_id, "fr": k.finding_revision_id, "f": k.finding_id, "k": k.kind}
        c.execute(text("SELECT pg_advisory_xact_lock(hashtextextended('cold_consequence_finding:' || :f || ':' "
                       "|| :k, 0))"), p)
        found = c.execute(text(
            "SELECT id FROM cold_consequence_revision WHERE tenant_id = :t AND site_id = :s "
            "AND finding_revision_id = :fr AND kind = :k AND consequence_basis_sha256 = :b"),
            {**p, "b": k.consequence_basis_sha256}).scalar_one_or_none()
        if found is not None:
            return found, True
        prior = c.execute(text(
            "SELECT cr.id, cr.revision_no, cr.kind, r.finding_id FROM cold_consequence_revision cr "
            "JOIN finding_revision r ON r.tenant_id = cr.tenant_id AND r.site_id = cr.site_id "
            "AND r.id = cr.finding_revision_id WHERE cr.tenant_id = :t AND cr.site_id = :s AND cr.kind = :k "
            "AND r.finding_id = :f ORDER BY cr.revision_no DESC LIMIT 1"), p).first()
        if prior is not None and (str(prior.finding_id) != str(k.finding_id) or prior.kind != k.kind):
            raise RuntimeError(f"cold consequence predecessor {prior.id} is not Finding {k.finding_id}/{k.kind}")
        rid = uuid4()
        c.execute(text(
            "INSERT INTO cold_consequence_revision (id, tenant_id, site_id, finding_revision_id, episode_revision_id, "
            "assessment_revision_id, revision_no, prior_revision_id, kind, state, reason, window_start, window_end, "
            "room_asset_id, overlap_group, quantity_unit, quantity_low, quantity_high, amount_low, amount_high, "
            "currency, finding_basis_sha256, consequence_basis_sha256, model_id, source_classification, "
            "source_gate_sha256, assumption_revision_ids, limitation) VALUES (:id, :t, :s, :fr, :er, :ar, :n, "
            ":prior, :k, :state, :reason, :ws, :we, :room, :group, :unit, CAST(:ql AS numeric), "
            "CAST(:qh AS numeric), NULL, NULL, NULL, :fb, :cb, :model, :cls, :gate, CAST(:assumptions AS jsonb), "
            ":limitation)"),
            {**p, "id": rid, "er": k.episode_revision_id, "ar": k.assessment_revision_id,
             "n": 1 if prior is None else prior.revision_no + 1, "prior": None if prior is None else prior.id,
             "state": k.state, "reason": k.reason, "ws": k.window_start, "we": k.window_end,
             "room": k.room_asset_id, "group": k.overlap_group, "unit": k.quantity_unit, "ql": k.quantity_low,
             "qh": k.quantity_high, "fb": k.finding_basis_sha256, "cb": k.consequence_basis_sha256,
             "model": k.model_id, "cls": k.source_classification, "gate": k.source_gate_sha256,
             "assumptions": json.dumps(list(k.assumption_revision_ids)), "limitation": k.limitation})
        if k.evidence:
            c.execute(text(
                "INSERT INTO cold_consequence_evidence (consequence_revision_id, tenant_id, site_id, evidence_id, "
                "use, reason) VALUES (:r, :t, :s, :e, :u, :why)"),
                [{"r": rid, "t": self.tenant_id, "s": self.site_id, "e": e.evidence_id, "u": e.use,
                  "why": e.reason} for e in k.evidence])
        return rid, False

    def succeed(self, revision_ids: list[UUID]) -> int:
        """Append the SUCCEEDED attempt with the exact returned IDs (`[]` for a no-op) in this transaction."""
        return _cold_attempt(self._c, self.tenant_id, self.site_id, self.work_id, "SUCCEEDED", None, revision_ids)
