"""PostgreSQL Finding store (S4-01 phase 1, migration 0009).

The fifth product database writer (architecture guard rule 8): it only INSERTs
its own append-only tables. Writes for one Site run in one transaction under a
Site-scoped advisory lock and re-check the selection/job fence the matcher read
under, so a selection that lands between the read and the write is never
half-applied: the caller re-plans instead. Revisions are idempotent on
`(finding_id, basis_sha256, transition)`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import OperationalError, ProgrammingError

from assetops_backend.analytics.assessment_inputs import sha256_json
from assetops_backend.analytics.dispatch import CANDIDATE, INDETERMINATE, NECESSARY
from assetops_backend.analytics.finding_episode import (
    DOMAIN,
    MATCHER_VERSION,
    MECHANISM,
    TITLES,
    Episode,
    Write,
)


def _num(x) -> str:
    return format(float(x), ".4f")


class FindingStoreUnavailable(RuntimeError):
    pass


class FindingFenceMoved(RuntimeError):
    """A selection or recompute job changed between the matcher's read and its write."""


@dataclass(frozen=True)
class Fence:
    selection_seq: int
    job_count: int
    job_marker: str
    finding_revisions: int = 0


@dataclass(frozen=True)
class Applied:
    finding_ids: tuple[str, ...]
    revision_ids: tuple[str, ...]


class PostgresFindingStore:
    def __init__(self, database_url: str | None) -> None:
        self._database_url = database_url
        self._engine: Engine | None = None

    def _connect(self) -> Engine:
        if not self._database_url:
            raise FindingStoreUnavailable("DATABASE_URL is not set, so the Finding store cannot be reached.")
        if self._engine is None:
            self._engine = create_engine(self._database_url, pool_pre_ping=True)
        return self._engine

    def _read(self, work):
        try:
            with self._connect().connect().execution_options(isolation_level="REPEATABLE READ") as c:
                with c.begin():
                    return work(c)
        except (OperationalError, ProgrammingError) as error:
            raise FindingStoreUnavailable(f"The Finding store failed: {error.orig}") from error

    @staticmethod
    def _fence(c: Connection, tenant_id: UUID, site_id: UUID, analytic_id: str) -> Fence:
        seq = c.execute(text("SELECT coalesce(max(seq), 0) FROM analytic_run_selection WHERE tenant_id = :t "
                             "AND site_id = :s AND analytic_id = :a"),
                        {"t": tenant_id, "s": site_id, "a": analytic_id}).scalar_one()
        count, marker = c.execute(text(
            "SELECT count(*), coalesce(max(created_at)::text, '') || '/' || "
            "coalesce(string_agg(status, ',' ORDER BY id), '') FROM recompute_job WHERE tenant_id = :t "
            "AND site_id = :s"), {"t": tenant_id, "s": site_id}).one()
        # Finding state is part of the fence: a pass planned before another pass committed (whose episodes
        # are stale) must re-plan instead of opening a second Finding for the same episode. Revisions are
        # append-only, so their count only grows.
        revisions = c.execute(text("SELECT count(*) FROM finding_revision WHERE tenant_id = :t AND site_id = :s"),
                              {"t": tenant_id, "s": site_id}).scalar_one()
        return Fence(int(seq), int(count), marker, int(revisions))

    def fence(self, tenant_id: UUID, site_id: UUID, analytic_id: str) -> Fence:
        return self._read(lambda c: self._fence(c, tenant_id, site_id, analytic_id))

    def assessed_days(self, tenant_id: UUID, site_id: UUID, analytic_id: str) -> list[date]:
        rows = self._read(lambda c: c.execute(text(
            "SELECT DISTINCT window_start FROM analytic_run_selection WHERE tenant_id = :t AND site_id = :s "
            "AND analytic_id = :a ORDER BY window_start"), {"t": tenant_id, "s": site_id, "a": analytic_id}).all())
        return [r[0].date() for r in rows]

    def episodes(self, tenant_id: UUID, site_id: UUID) -> list[Episode]:
        rows = self._read(lambda c: c.execute(text(
            "SELECT DISTINCT ON (f.id) f.id, f.generator_asset_id, f.anchor_start, r.lifecycle, r.episode_start, "
            "r.episode_end, r.basis_sha256, r.model_version, r.support_sha256 FROM finding f "
            "JOIN finding_revision r "
            "ON r.finding_id = f.id WHERE f.tenant_id = :t AND f.site_id = :s ORDER BY f.id, r.revision_no DESC"),
            {"t": tenant_id, "s": site_id}).all())
        return [Episode(str(r[0]), r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]) for r in rows]

    def apply(self, tenant_id: UUID, site_id: UUID, analytic_id: str, writes: list[Write], fence: Fence,
              now: datetime) -> Applied:
        def work(c: Connection) -> Applied:
            c.execute(text("SELECT pg_advisory_xact_lock(hashtext('finding:' || :s))"), {"s": str(site_id)})
            if self._fence(c, tenant_id, site_id, analytic_id) != fence:
                raise FindingFenceMoved("a selection, recompute job or Finding changed since the matcher read; "
                                        "re-plan")
            findings, revisions = [], []
            for w in writes:
                if w.new_finding is not None:
                    self._insert_finding(c, tenant_id, site_id, analytic_id, w, now)
                    findings.append(w.finding_id)
                rid = self._insert_revision(c, tenant_id, site_id, analytic_id, w, now)
                if rid is not None:
                    revisions.append(rid)
            return Applied(tuple(findings), tuple(revisions))

        try:
            with self._connect().begin() as c:
                return work(c)
        except (OperationalError, ProgrammingError) as error:
            raise FindingStoreUnavailable(f"The Finding store failed: {error.orig}") from error

    @staticmethod
    def _insert_finding(c: Connection, tenant_id: UUID, site_id: UUID, analytic_id: str, w: Write,
                        now: datetime) -> None:
        n = w.new_finding or {}
        c.execute(text(
            "INSERT INTO finding (id, tenant_id, site_id, finding_key, domain, mechanism, analytic_id, "
            "generator_asset_id, anchor_start, anchor_assessment_revision_id, cohort_sha256, matcher_version, "
            "recurs_after_finding_id, split_from_finding_id, opened_at, created_at) VALUES (:id, :t, :s, :k, :d, "
            ":m, :a, :g, :anchor, :anchor_rev, :cohort, :mv, :recurs, :split, :now, :now)"),
            {"id": w.finding_id, "t": tenant_id, "s": site_id, "k": n["finding_key"], "d": DOMAIN, "m": MECHANISM,
             "a": analytic_id, "g": w.asset, "anchor": n["anchor_start"],
             "anchor_rev": n["anchor_assessment_revision_id"], "cohort": n["cohort_sha256"], "mv": MATCHER_VERSION,
             "recurs": n["recurs_after_finding_id"], "split": n["split_from_finding_id"], "now": now})

    @staticmethod
    def _insert_revision(c: Connection, tenant_id: UUID, site_id: UUID, analytic_id: str, w: Write,
                         now: datetime) -> str | None:
        exists = c.execute(text("SELECT 1 FROM finding_revision WHERE finding_id = :f AND basis_sha256 = :b "
                                "AND transition = :tr"),
                           {"f": w.finding_id, "b": w.basis_sha256, "tr": w.transition}).first()
        if exists:
            return None
        digests = c.execute(text(
            "SELECT id::text, envelope_sha256 FROM accepted_evidence WHERE tenant_id = :t AND site_id = :s "
            "AND id = ANY(CAST(:ids AS uuid[])) ORDER BY id"),
            {"t": tenant_id, "s": site_id, "ids": w.cited_evidence_ids}).all()
        if len(digests) != len(w.cited_evidence_ids):
            raise FindingFenceMoved("a cited evidence ID is not accepted in this Site")
        number = c.execute(text("SELECT coalesce(max(revision_no), 0) + 1 FROM finding_revision "
                                "WHERE finding_id = :f"), {"f": w.finding_id}).scalar_one()
        rid = str(uuid4())
        c.execute(text(
            "INSERT INTO finding_revision (id, tenant_id, site_id, finding_id, revision_no, transition, lifecycle, "
            "claim_level, title, mechanism, matcher_version, analytic_id, model_version, assessment_revision_id, "
            "analytic_run_id, window_assessment_revision_id, episode_start, episode_end, candidate_minutes, "
            "necessary_minutes, indeterminate_minutes, claim, limitations, basis_sha256, support_sha256, "
            "cited_evidence_sha256, input_evidence_sha256, created_at) VALUES (:id, :t, :s, :f, :n, :tr, :lc, "
            ":cl, :title, :m, :mv, :a, "
            ":model, :primary, :run, :wrev, :es, :ee, :cand, :nec, :ind, CAST(:claim AS jsonb), "
            "CAST(:limits AS jsonb), :basis, :support, :cited, :inputs, :now)"),
            {"id": rid, "t": tenant_id, "s": site_id, "f": w.finding_id, "n": number, "tr": w.transition,
             "lc": w.lifecycle, "cl": w.claim_level, "title": TITLES[w.lifecycle], "m": MECHANISM,
             "mv": MATCHER_VERSION, "a": analytic_id, "model": w.model_version, "primary": w.primary_revision_id,
             "run": w.primary_run_id, "wrev": w.window_revision_id, "es": w.episode_start, "ee": w.episode_end,
             "cand": _num(w.minutes[CANDIDATE]), "nec": _num(w.minutes[NECESSARY]),
             "ind": _num(w.minutes[INDETERMINATE]), "claim": json.dumps(w.claim, sort_keys=True),
             "limits": json.dumps(w.limitations), "basis": w.basis_sha256, "support": w.support_sha256,
             "cited": sha256_json([[r[0], r[1]] for r in digests]), "inputs": sha256_json(w.input_sha256s),
             "now": now})
        for revision_id, run_id, scope, primary in w.assessments:
            c.execute(text(
                "INSERT INTO finding_revision_assessment (finding_revision_id, assessment_revision_id, tenant_id, "
                "site_id, analytic_run_id, scope, is_primary) VALUES (:r, :a, :t, :s, :run, :scope, :p)"),
                {"r": rid, "a": revision_id, "t": tenant_id, "s": site_id, "run": run_id, "scope": scope,
                 "p": primary})
        for evidence_id in w.cited_evidence_ids:
            c.execute(text(
                "INSERT INTO finding_revision_evidence (finding_revision_id, evidence_id, tenant_id, site_id) "
                "VALUES (:r, :e, :t, :s)"), {"r": rid, "e": evidence_id, "t": tenant_id, "s": site_id})
        if w.merged_into is not None:
            c.execute(text(
                "INSERT INTO finding_merge (superseded_finding_id, canonical_finding_id, tenant_id, site_id, "
                "finding_revision_id, created_at) VALUES (:old, :new, :t, :s, :r, :now)"),
                {"old": w.finding_id, "new": w.merged_into, "t": tenant_id, "s": site_id, "r": rid, "now": now})
        return rid

    def rows(self, tenant_id: UUID, site_id: UUID) -> dict[str, Any]:
        """Every Finding and revision of a Site, for verification and the phase-2 read."""
        def work(c: Connection) -> dict[str, Any]:
            p = {"t": tenant_id, "s": site_id}
            findings = [dict(r._mapping) for r in c.execute(text(
                "SELECT * FROM finding WHERE tenant_id = :t AND site_id = :s ORDER BY anchor_start, id"), p)]
            revisions = [dict(r._mapping) for r in c.execute(text(
                "SELECT * FROM finding_revision WHERE tenant_id = :t AND site_id = :s "
                "ORDER BY finding_id, revision_no"), p)]
            cites = [dict(r._mapping) for r in c.execute(text(
                "SELECT * FROM finding_revision_assessment WHERE tenant_id = :t AND site_id = :s"), p)]
            evidence = [dict(r._mapping) for r in c.execute(text(
                "SELECT * FROM finding_revision_evidence WHERE tenant_id = :t AND site_id = :s"), p)]
            merges = [dict(r._mapping) for r in c.execute(text(
                "SELECT * FROM finding_merge WHERE tenant_id = :t AND site_id = :s"), p)]
            return {"findings": findings, "revisions": revisions, "assessments": cites, "evidence": evidence,
                    "merges": merges}
        return self._read(work)
