"""W3-01 estate read adapter: one read-only REPEATABLE READ Postgres snapshot for every estate root.

`PostgresEstateRead.read(work)` opens exactly one connection and transaction, runs `SET TRANSACTION READ ONLY`,
takes `read_at = now()` once, and hands `work` an `EstateSnapshot` whose every read runs on that connection: the
Lane A connection-taking W1 helpers (`index_snapshot_on`, `index_lineage_on`, `select_dispatch_days_on`,
`site_window_on`, `select_consequence_on`, `for_finding_on`), the pinned cold/EV `estate_snapshots_on` and their
selected-row helpers, and the shared `PublicProvenance` over `ProvenanceReadsOn(c)`. It never calls a method that
opens its own transaction and never writes (`tools/checks/configuration-persistence.ps1` `$pgReaders`).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import DBAPIError, OperationalError

from assetops_backend.analytics import dispatch as dispatch_contract
from assetops_backend.analytics.cold_reads import probe_fresh
from assetops_backend.analytics.finding_episode import DOMAIN as FINDING_DOMAIN
from assetops_backend.estate.coverage import COLD, EV
from assetops_backend.estate.scope import EstateSelectionInconsistent, EstateStoreUnavailable
from assetops_backend.evidence.public_provenance import (
    PublicProvenance, consequence_row_selection, estate_projection, finding_row_selection)


class _Prefetched:
    """`ProvenanceReads` serving one Site's link rows from a batched read; an ID the batch did not return (never
    expected: the read is a LEFT JOIN from the requested IDs) falls back to the per-Site read."""

    def __init__(self, rows: dict, site: str, fallback: Any) -> None:
        self._rows, self._site, self._fallback = rows, site, fallback

    def link_rows(self, tenant_id: UUID, site_id: UUID, evidence_ids: list[str]) -> list[Any]:
        keys = [(self._site, str(i).lower()) for i in evidence_ids]
        if str(site_id).lower() != self._site or any(k not in self._rows for k in keys):
            return list(self._fallback.link_rows(tenant_id, site_id, evidence_ids))
        return [row for k in keys for row in self._rows[k]]

    def finding_revision_evidence(self, tenant_id: UUID, site_id: UUID, finding_revision_id: UUID) -> Any:
        return self._fallback.finding_revision_evidence(tenant_id, site_id, finding_revision_id)

    def consequence_inputs(self, tenant_id: UUID, site_id: UUID, consequence_revision_id: UUID) -> Any:
        return self._fallback.consequence_inputs(tenant_id, site_id, consequence_revision_id)


def _uuids(values: Any) -> list[str]:
    return sorted({str(v).lower() for v in values or () if v is not None})


class PostgresEstateRead:
    """`read(work)` runs `work(EstateSnapshot)` inside one read-only REPEATABLE READ transaction."""

    def __init__(self, database_url: str | None, *, findings: Any, assessments: Any, actions: Any,
                 consequences: Any, eligibility: Any, cold: Any, ev: Any,
                 provenance_reads: Callable[[Connection], Any],
                 inconsistent: tuple[type[BaseException], ...] = (),
                 unavailable: tuple[type[BaseException], ...] = (), engine: Any = None,
                 cold_site: Any = None, ev_site: Any = None, ev_money: Any = None,
                 link_rows_many: Callable[..., dict] | None = None) -> None:
        self._url, self._engine = database_url, engine
        self.findings, self.assessments, self.actions = findings, assessments, actions
        self.consequences, self.eligibility, self.cold, self.ev = consequences, eligibility, cold, ev
        self.provenance_reads, self.inconsistent, self.unavailable = provenance_reads, inconsistent, unavailable
        # W3-02 0c: the pinned cold/EV Site facades (`capabilities_on`/`money_on`) and the SELECT-only EV money
        # reads, all used on the one estate connection; None leaves the W3-01 reads unchanged.
        self.cold_site, self.ev_site, self.ev_money = cold_site, ev_site, ev_money
        # W3-03 r1b2 R11: the batched link-row read `(c, tenant, [(site, ids)]) -> {(site, id): [rows]}`; None
        # keeps the per-Site `cited_provenance` path (same DTOs, one query per Site).
        self.link_rows_many = link_rows_many

    def _connect(self):
        if self._engine is None:
            if not self._url:
                raise EstateStoreUnavailable("No product database is configured.")
            self._engine = create_engine(self._url, pool_pre_ping=True)
        return self._engine.connect().execution_options(isolation_level="REPEATABLE READ")

    def dispose(self) -> None:
        if self._engine is not None:
            self._engine.dispose()

    def read(self, work: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
        try:
            with self._connect() as c, c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                return work(EstateSnapshot(self, c, c.execute(text("SELECT now()")).scalar_one()))
        except (OperationalError, DBAPIError) as error:
            raise EstateStoreUnavailable(f"The estate store is unavailable: {error.__class__.__name__}") from error
        except self.inconsistent as error:  # an exact pin refused inside the one transaction
            raise EstateSelectionInconsistent(str(error)) from error
        except self.unavailable as error:  # a broad W2 read failure is a store outage, never a selection conflict
            raise EstateStoreUnavailable(f"The estate store is unavailable: {error.__class__.__name__}") from error


class EstateSnapshot:
    """Every read on the one estate connection `c`; `historical` and `continuation` (a cursor page) are set by the
    index once the cutoff is known."""

    def __init__(self, owner: PostgresEstateRead, c: Connection, read_at: datetime) -> None:
        self._o, self._c, self.read_at, self.historical, self.continuation = owner, c, read_at, False, False
        self.basis_historical = False  # page one's mode: the selection basis, apart from the response label

    def _public(self) -> PublicProvenance:
        return PublicProvenance(self._o.provenance_reads(self._c))

    # --- scope and shared -------------------------------------------------------------------------------------

    def imported_sites(self, t: UUID, to: datetime) -> list[dict[str, Any]]:
        """All Sites of the tenant with a committed `site_import` before `to`, inactive ones included, ordered by
        `(site_code_key, id)`; each item also carries that stored `site_code_key` (W3-02 0c)."""
        rows = self._c.execute(text(
            "SELECT s.id, s.site_code, s.name, s.site_type, s.site_code_key FROM site s WHERE s.tenant_id = :t AND EXISTS ("
            "SELECT 1 FROM site_import i WHERE i.tenant_id = s.tenant_id AND i.site_id = s.id AND i.imported_at < :to) "
            "ORDER BY s.site_code_key, s.id"), {"t": t, "to": to}).all()
        return [{"site_id": r[0], "site_code": r[1], "site_name": r[2], "site_type": r[3], "site_code_key": r[4]}
                for r in rows]

    def evidence_cutoff(self, t: UUID, s: UUID, k: datetime) -> datetime | None:
        """Run 7 q7-1: the Site's latest disposition decided by the requested cutoff (its evidence watermark)."""
        return self._c.execute(text(
            "SELECT max(decided_at) FROM ingestion_disposition WHERE tenant_id = :t AND site_id = :s "
            "AND decided_at <= :k"), {"t": t, "s": s, "k": k}).scalar_one()

    def open_jobs(self, t: UUID, s: UUID, domain: str, from_: datetime, to: datetime, k: datetime) -> list[str]:
        """Overlapping unsettled recompute work created by the requested cutoff: the work fence of a live basis, on
        page one and every continuation; never a historical basis (c2 r1 M1)."""
        return list(self._c.execute(text(
            "SELECT status FROM recompute_job WHERE tenant_id = :t AND site_id = :s AND domain = :d "
            "AND status IN ('PENDING', 'LEASED', 'FAILED') AND window_start < :to AND window_end > :from "
            "AND created_at <= :k"), {"t": t, "s": s, "d": domain, "from": from_, "to": to, "k": k}).scalars())

    def cited_provenance(self, t: UUID, s: UUID, cited: list[str], selected: list[str]) -> dict[str, Any]:
        return estate_projection(self._public().cited_set(t, s, cited, selected, detail=False))

    def cited_provenance_many(self, t: UUID, items: list[tuple[Any, list[str], list[str]]]) -> list[dict[str, Any]]:
        """W3-03 r1b2 R11: `cited_provenance` for several Sites `(site_id, cited, selected)` with one batched
        link-row query on this connection; each DTO equals that Site's `cited_provenance` (same resolver,
        classification and digest). Without a batched reader it is the per-Site call."""
        if self._o.link_rows_many is None:
            return [self.cited_provenance(t, s, cited, selected) for s, cited, selected in items]
        prefetched = self._o.link_rows_many(self._c, t, [(s, sorted({str(i) for i in cited}))
                                                         for s, cited, _ in items])
        out = []
        for s, cited, selected in items:
            reads = _Prefetched(prefetched, str(s).lower(), self._o.provenance_reads(self._c))
            out.append(estate_projection(PublicProvenance(reads).cited_set(t, s, cited, selected, detail=False)))
        return out

    # --- mini-grid Findings and money -------------------------------------------------------------------------

    def dispatch_days(self, t: UUID, s: UUID, from_: datetime, to: datetime, k: datetime) -> list[dict[str, Any]]:
        return self._o.assessments.select_dispatch_days_on(self._c, t, s, from_, to, k)

    def finding_index(self, t: UUID, s: UUID, k: datetime) -> dict[str, Any]:
        return self._o.findings.index_snapshot_on(self._c, t, s, FINDING_DOMAIN, dispatch_contract.ANALYTIC_ID, k)

    def finding_lineage(self, t: UUID, s: UUID, revision_ids: list[Any], k: datetime) -> dict[str, Any]:
        """Exact pinned lineage; a refused pin (`FindingPinRefused`, a LookupError) is an inconsistent selection."""
        try:
            return self._o.findings.index_lineage_on(self._c, t, s, [UUID(str(x)) for x in revision_ids], k)
        except KeyError:
            raise
        except LookupError as error:
            raise EstateSelectionInconsistent(str(error)) from error

    def finding_provenance(self, t: UUID, s: UUID, finding_revision_id: Any, cited: list[str]) -> dict[str, Any]:
        """Run 1 ruling 2: the W1 Finding row set `{finding_revision.id}` over its exact pinned citations (read by
        `index_lineage_on` on this connection)."""
        return self.cited_provenance(t, s, cited, finding_row_selection(finding_revision_id))

    def consequence(self, t: UUID, s: UUID, finding_revision_id: Any, k: datetime) -> dict[str, Any]:
        return self._o.consequences.select_consequence_on(self._c, t, s, UUID(str(finding_revision_id)), k)

    def consequence_provenance(self, t: UUID, s: UUID, consequence_revision_id: Any, finding_revision_id: Any,
                               cited: list[str]) -> dict[str, Any]:
        """Run 6 Blocker 2: the consequence row's six-key block over its pinned Finding citations plus its own
        power citations, selected `{consequence_revision.id, finding_revision.id}`."""
        return self.cited_provenance(t, s, cited, consequence_row_selection(consequence_revision_id,
                                                                            finding_revision_id))

    def eligibility(self, t: UUID, s: UUID, finding_id: Any, k: datetime) -> dict[str, Any]:
        return self._o.eligibility.for_finding_on(self._c, t, s, UUID(str(finding_id)), k)

    def awaiting_verification(self, t: UUID, s: UUID, pairs: list[tuple[str, str]], k: datetime) -> int:
        """Actions of these exact (Finding, selected revision) pairs with a frozen verification window open at `k`
        and no surviving RESOLVED event by `k`."""
        return int(self._c.execute(text(
            "SELECT count(DISTINCT a.id) FROM action a JOIN verification_plan p ON p.tenant_id = a.tenant_id "
            "AND p.site_id = a.site_id AND p.action_id = a.id WHERE a.tenant_id = :t AND a.site_id = :s "
            "AND (CAST(a.origin_finding_id AS text) || '/' || CAST(a.origin_finding_revision_id AS text)) = ANY(:pairs) "
            "AND a.created_at <= :k AND p.recorded_at <= :k AND p.later_start <= :k AND :k < p.later_end "
            "AND (SELECT e.kind FROM action_event e WHERE e.tenant_id = a.tenant_id AND e.site_id = a.site_id "
            "AND e.action_id = a.id AND e.kind IN ('RESOLVED', 'RESOLUTION_WITHDRAWN') AND e.recorded_at <= :k "
            "ORDER BY e.recorded_at DESC, e.id DESC LIMIT 1) IS DISTINCT FROM 'RESOLVED'"),
            {"t": t, "s": s, "k": k, "pairs": [f"{f.lower()}/{r.lower()}" for f, r in pairs]}).scalar_one())

    # --- cold and EV selected windows -------------------------------------------------------------------------

    def _selected_at(self, t: UUID, s: UUID, analytic: str, lo: datetime, hi: datetime, seq: int) -> datetime:
        return self._c.execute(text(
            "SELECT selected_at FROM analytic_run_selection WHERE tenant_id = :t AND site_id = :s "
            "AND analytic_id = :a AND window_start = :lo AND window_end = :hi AND seq = :q"),
            {"t": t, "s": s, "a": analytic, "lo": lo, "hi": hi, "q": seq}).scalar_one()

    def _created(self, t: UUID, s: UUID, revision_ids: list[Any]) -> dict[str, datetime]:
        if not revision_ids:
            return {}
        return {str(r[0]).lower(): r[1] for r in self._c.execute(text(
            "SELECT id, created_at FROM finding_revision WHERE tenant_id = :t AND site_id = :s "
            "AND id = ANY(CAST(:ids AS uuid[]))"), {"t": t, "s": s, "ids": [str(x) for x in revision_ids]})}

    def _with_mechanism(self, t: UUID, s: UUID, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """CC-R2 (build spec Q-C8): one batched `finding.mechanism` read per window, added to each findings dict."""
        if not findings:
            return findings
        mechanism = {str(r[0]).lower(): r[1] for r in self._c.execute(text(
            "SELECT id, mechanism FROM finding WHERE tenant_id = :t AND site_id = :s "
            "AND id = ANY(CAST(:ids AS uuid[]))"), {"t": t, "s": s, "ids": [f["finding_id"] for f in findings]})}
        for f in findings:
            f["mechanism"] = mechanism.get(str(f["finding_id"]).lower())
        return findings

    def selected_windows(self, t: UUID, s: UUID, domain: str, from_: datetime, to: datetime,
                         evidence_cutoff: datetime, k: datetime) -> list[dict[str, Any]]:
        code = self._c.execute(text("SELECT site_code FROM site WHERE tenant_id = :t AND id = :s"),
                               {"t": t, "s": s}).scalar_one()
        reads = {COLD: (self._o.cold, self._cold_window), EV: (self._o.ev, self._ev_window)}.get(domain)
        if reads is None:
            raise ValueError(f"No selected-window read for {domain!r}.")
        try:
            snaps = reads[0].estate_snapshots_on(self._c, t, s, code, from_, to, evidence_cutoff, k)
        except KeyError:
            raise
        except LookupError as error:  # `SelectionPinRefused`: an inconsistent pinned selection, never another head
            raise EstateSelectionInconsistent(str(error)) from error
        return [reads[1](t, s, snap, k) for snap in snaps]

    def _cold_window(self, t: UUID, s: UUID, snap: dict[str, Any], k: datetime) -> dict[str, Any]:
        cold = self._o.cold
        selected = snap["selected"]
        seqs = snap["selection_seqs"]
        top = max(selected, key=lambda a: (seqs[a], a))
        chosen = {str(x.revision_id).lower() for x in selected.values()}
        findings = []
        for row in cold._finding_ids(self._c, snap, None, None):
            revisions = cold._revisions(self._c, snap, row[0], False)
            created = self._created(t, s, [r[0] for r in revisions])
            # c2 r1 L2: the latest revision created by the cutoff whose assessment this window selected; a newer
            # revision of an unselected assessment waits for its selection.
            eligible = [r for r in revisions if created[str(r[0]).lower()] <= k and str(r[8]).lower() in chosen]
            if not eligible:
                continue
            rev = eligible[0]  # latest by revision_no
            item = cold._item(self._c, snap, row, rev)
            claim = item["claim"] or {}
            anchor = self._c.execute(text(
                "SELECT anchor_time FROM cold_episode WHERE tenant_id = :t AND site_id = :s AND id = :e"),
                {"t": t, "s": s, "e": claim.get("episode_id")}).scalar_one_or_none()
            if anchor is None:
                raise EstateSelectionInconsistent(f"Cold Finding {row[0]} names no stored episode.")
            consequence = self._c.execute(text(
                "SELECT id FROM cold_consequence_revision WHERE tenant_id = :t AND site_id = :s "
                "AND finding_revision_id = :r AND created_at <= :k ORDER BY revision_no DESC, id DESC LIMIT 1"),
                {"t": t, "s": s, "r": rev[0], "k": k}).scalar_one_or_none()
            findings.append({"finding_id": str(row[0]), "finding_revision_id": str(rev[0]), "lifecycle": rev[3],
                             "title": rev[5], "episode_start": anchor, "episode_end": rev[14],
                             "evidence_ids": _uuids(item["evidence_ids"]),
                             "source_provenance": estate_projection(item["source_provenance"]),
                             "consequence_revision_id": None if consequence is None else str(consequence)})
        latest = snap.get("latest_probe")
        return {"window_start": snap["lo"], "window_end": snap["hi"], "state": snap["state"],
                "seq": seqs[top], "selection_id": str(selected[top].revision_id),
                "selected_at": self._selected_at(t, s, top, snap["lo"], snap["hi"], seqs[top]),
                "assessment_revision_ids": _uuids(x.revision_id for x in selected.values()),
                "evidence_ids": _uuids(e for x in selected.values() for e in x.evidence_ids),
                "probe_fresh": None if latest is None else probe_fresh(latest, snap["hi"]),
                "findings": self._with_mechanism(t, s, findings)}

    def _ev_window(self, t: UUID, s: UUID, snap: dict[str, Any], k: datetime) -> dict[str, Any]:
        ev = self._o.ev
        sel = snap["selected"]
        if sel is None:
            raise EstateSelectionInconsistent("A pinned EV window has no selected assessment.")
        rows = list(ev._findings(self._c, snap))
        withdrawn = self._c.execute(text(
            "SELECT fr.finding_id FROM finding_revision fr WHERE fr.tenant_id = :t AND fr.site_id = :s "
            "AND fr.assessment_revision_id = :ar AND fr.lifecycle = 'NO_LONGER_SUPPORTED' ORDER BY fr.finding_id"),
            {"t": t, "s": s, "ar": sel["revision_id"]}).scalars().all()
        for finding_id in withdrawn:
            rows += [r for r in ev._findings(self._c, snap, finding_id) if r["lifecycle"] == "NO_LONGER_SUPPORTED"]
        created = self._created(t, s, [r["revision_id"] for r in rows])
        sessions = [str(x) for x in sel["result"].get("session_revision_ids") or ()]
        findings = []
        for r in rows:
            if created[str(r["revision_id"]).lower()] > k:
                raise EstateSelectionInconsistent(f"EV Finding revision {r['revision_id']} postdates its cutoff.")
            bounds = self._c.execute(text(
                "SELECT s.anchor_time, (SELECT v.end_at FROM ev_session_revision v WHERE v.tenant_id = s.tenant_id "
                "AND v.site_id = s.site_id AND v.session_id = s.id AND CAST(v.id AS text) = ANY(:revs) LIMIT 1) "
                "FROM ev_session s WHERE s.tenant_id = :t AND s.site_id = :s AND CAST(s.id AS text) = :session"),
                {"t": t, "s": s, "revs": sessions, "session": str(r["session_id"]).lower()}).first()
            if bounds is None:
                raise EstateSelectionInconsistent(f"EV Finding {r['finding_id']} names no stored session.")
            findings.append({"finding_id": str(r["finding_id"]), "finding_revision_id": str(r["revision_id"]),
                             "lifecycle": r["lifecycle"], "title": r["title"], "episode_start": bounds[0],
                             "episode_end": bounds[1], "evidence_ids": _uuids(r["source_provenance"]["evidence_ids"]),
                             "source_provenance": estate_projection(r["source_provenance"]),
                             "consequence_revision_id": None})
        seq = int(snap["selection_seqs"][next(iter(snap["selection_seqs"]))])
        analytic = next(iter(snap["selection_seqs"]))
        return {"window_start": snap["lo"], "window_end": snap["hi"], "state": snap["state"], "seq": seq,
                "selection_id": str(sel["revision_id"]),
                "selected_at": self._selected_at(t, s, analytic, snap["lo"], snap["hi"], seq),
                "assessment_revision_ids": _uuids([sel["revision_id"]]), "evidence_ids": _uuids(sel["evidence_ids"]),
                "probe_fresh": None, "findings": self._with_mechanism(t, s, findings)}

    # --- Actions ----------------------------------------------------------------------------------------------

    def actions(self, t: UUID, s: UUID, from_: datetime, to: datetime, k: datetime) -> dict[str, Any]:
        return self._o.actions.site_window_on(self._c, t, s, from_, to, k)

    def action_basis(self, t: UUID, s: UUID, action_ids: list[Any]) -> dict[str, dict[str, Any]]:
        """D3: each Action's stored primary assessment, Foundation revision, basis assessments, basis evidence and
        its pinned origin Finding revision's exact citations."""
        p = {"t": t, "s": s, "ids": [str(x) for x in action_ids]}
        out: dict[str, dict[str, Any]] = {}
        origins: dict[str, str] = {}
        for r in self._c.execute(text(
                "SELECT id, primary_assessment_revision_id, foundation_revision_id, origin_finding_revision_id "
                "FROM action WHERE tenant_id = :t AND site_id = :s AND id = ANY(CAST(:ids AS uuid[]))"), p):
            out[str(r[0])] = {"primary": str(r[1]), "foundation": str(r[2]), "assessments": [], "evidence": [],
                              "origin_evidence": []}
            origins[str(r[0])] = str(r[3])
        for aid, assessment in self._c.execute(text(
                "SELECT action_id, assessment_revision_id FROM action_basis_assessment WHERE tenant_id = :t "
                "AND site_id = :s AND action_id = ANY(CAST(:ids AS uuid[]))"), p):
            out[str(aid)]["assessments"].append(str(assessment))
        for aid, evidence in self._c.execute(text(
                "SELECT action_id, evidence_id FROM action_basis_evidence WHERE tenant_id = :t AND site_id = :s "
                "AND action_id = ANY(CAST(:ids AS uuid[]))"), p):
            out[str(aid)]["evidence"].append(str(evidence))
        cited: dict[str, list[str]] = {}
        for frid, evidence in self._c.execute(text(
                "SELECT finding_revision_id, evidence_id FROM finding_revision_evidence WHERE tenant_id = :t "
                "AND site_id = :s AND finding_revision_id = ANY(CAST(:ids AS uuid[]))"),
                {"t": t, "s": s, "ids": sorted(set(origins.values()))}):
            cited.setdefault(str(frid), []).append(str(evidence))
        for aid, frid in origins.items():
            out[aid]["origin_evidence"] = cited.get(frid, [])
        return out

    def verification(self, t: UUID, s: UUID, action_ids: list[Any], k: datetime) -> dict[str, dict[str, Any]]:
        """Frozen verification plans and outcome decision times recorded by `k`, per Action."""
        p = {"t": t, "s": s, "k": k, "ids": [str(x) for x in action_ids]}
        out: dict[str, dict[str, Any]] = {}
        # W3-03 closure 4 S8: each plan also carries its `id` and `recorded_at` (outcomes map id -> recorded_at);
        # the existing `later_start`/`later_end` and outcome-map consumers are unchanged. Ordered for determinism.
        for aid, pid, recorded, start, end in self._c.execute(text(
                "SELECT action_id, id, recorded_at, later_start, later_end FROM verification_plan WHERE tenant_id = :t "
                "AND site_id = :s AND action_id = ANY(CAST(:ids AS uuid[])) AND recorded_at <= :k "
                "ORDER BY recorded_at, id"), p):
            out.setdefault(str(aid), {"plans": [], "outcomes": {}})["plans"].append(
                {"id": str(pid), "recorded_at": recorded, "later_start": start, "later_end": end})
        for aid, oid, at in self._c.execute(text(
                "SELECT action_id, id, recorded_at FROM verification_outcome WHERE tenant_id = :t AND site_id = :s "
                "AND action_id = ANY(CAST(:ids AS uuid[])) AND recorded_at <= :k ORDER BY recorded_at, id"), p):
            out.setdefault(str(aid), {"plans": [], "outcomes": {}})["outcomes"][str(oid)] = at
        return out
