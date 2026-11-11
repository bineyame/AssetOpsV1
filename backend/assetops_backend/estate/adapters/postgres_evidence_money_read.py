"""W3-02 estate Evidence/Financials read adapter: the W3-01 one-transaction estate snapshot plus the pinned Site
facades, all on that one read-only REPEATABLE READ connection.

`PostgresEvidenceMoneyRead.read(work)` keeps W3-01 `PostgresEstateRead.read` exactly (one connection, one
transaction, `SET TRANSACTION READ ONLY`, one `now()` read time) and hands `work` an `EvidenceMoneySnapshot`,
an `EstateSnapshot` extended with connection-taking W1 day, pinned cold/EV window and capability reads. It calls
only Lane A's connection-taking helpers (`ClaimLimitReadService.claim_limit_on`, `estate_snapshots_on`,
`ColdSiteReadService.capabilities_on`, `EvSiteReads.capabilities_on`); never `read()`, `_ctx`, `open_on` or any
method that opens its own transaction, and never writes (`tools/checks/configuration-persistence.ps1` `$pgReaders`).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Callable
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError

from assetops_backend import read_scope
from assetops_backend.estate.adapters.postgres_estate_read import EstateSnapshot, PostgresEstateRead
from assetops_backend.estate.coverage import COLD, EV
from assetops_backend.estate.scope import EstateSelectionInconsistent, EstateStoreUnavailable


class PostgresEvidenceMoneyRead(PostgresEstateRead):
    """The W3-01 estate read plus the W1 claim-limit service; `read(work)` runs one transaction."""

    def __init__(self, database_url: str | None, *, claim_limits: Any, claim_limit_refused: tuple[
                 type[BaseException], ...] = (), period_rows: Any = None, **kwargs: Any) -> None:
        super().__init__(database_url, **kwargs)
        self.claim_limits, self.claim_limit_refused = claim_limits, claim_limit_refused
        # ANY-2 AR-4: `estate.period_rows.EvidenceRows` (stored `evidence.claim` days), or None = today's compose.
        self.period_rows = period_rows

    def dispose(self) -> None:
        super().dispose()
        store = getattr(self.period_rows, "store", None)
        if store is not None and hasattr(store, "dispose"):
            store.dispose()

    def read(self, work: Callable[[Any], dict[str, Any]]) -> dict[str, Any]:
        try:
            with self._connect() as c, c.begin():
                c.execute(text("SET TRANSACTION READ ONLY"))
                read_at = read_scope.read_instant(c.execute(text("SELECT clock_timestamp()")).scalar_one())  # CH5c-R7 L2: at or after the snapshot
                with read_scope.snapshot(c, read_at):  # CH5c-R3 R3
                    return work(EvidenceMoneySnapshot(self, c, read_at))
        except (OperationalError, DBAPIError) as error:
            raise EstateStoreUnavailable(f"The estate store is unavailable: {error.__class__.__name__}") from error
        except self.inconsistent as error:  # an exact pin refused inside the one transaction
            raise EstateSelectionInconsistent(str(error)) from error
        except self.unavailable as error:  # a broad W2 read failure is a store outage, never a selection conflict
            raise EstateStoreUnavailable(f"The estate store is unavailable: {error.__class__.__name__}") from error


#: c1 r1 M2: the finite W1 reconstruction refusals, each one UNKNOWN day (never a tenant-wide 409).
W1_RECONSTRUCTION_REFUSALS = frozenset({"UNSUPPORTED_RULE_VERSION", "ASSESSMENT_REVISION_NOT_FOUND",
                                        "REVISION_OUTSIDE_WINDOW", "REVISION_NOT_WINDOW", "ACCEPTED_LINEAGE_ABSENT"})


_UNSET = object()


def _rows_of(snap: Any) -> Any:
    """AR-4: the snapshot's stored claim days (`estate.period_rows.RequestRows`, made once per snapshot), or None
    when its owner has no `period_rows` or the kind is not served (`ASSETOPS_PERIOD_READ_KINDS`)."""
    cached = getattr(snap, "_ar4_rows", _UNSET)
    if cached is _UNSET:
        source = getattr(getattr(snap, "_o", None), "period_rows", None)
        cached = None if source is None else source.request(snap)
        snap._ar4_rows = cached
    return cached


class EvidenceMoneySnapshot(EstateSnapshot):
    """W3-01 `EstateSnapshot` reads plus the W3-02 connection-taking projections, every one on `self._c`."""

    def _period_rows(self) -> Any:
        return _rows_of(self)

    def dispatch_days(self, t: UUID, s: UUID, from_: datetime, to: datetime, k: datetime) -> list[dict[str, Any]]:
        days = super().dispatch_days(t, s, from_, to, k)
        rows = self._period_rows()
        if rows is not None:  # AR-4: the page's own dispatch days are the claim days' selection
            rows.note_days(t, s, from_, to, k, days)
        return days

    def cited_provenance(self, t: UUID, s: UUID, cited: list[str], selected: list[str]) -> dict[str, Any]:
        """AR-4: today's projection over the stored link rows when every cited ID's rows are stored."""
        rows = self._period_rows()
        stored = None if rows is None else rows.link_rows(s, cited)
        if stored is None:
            return super().cited_provenance(t, s, cited, selected)
        from assetops_backend.estate.adapters.postgres_estate_read import _Prefetched
        from assetops_backend.evidence.public_provenance import PublicProvenance, estate_projection

        reads = _Prefetched(stored, str(s).lower(), self._o.provenance_reads(self._c))
        return estate_projection(PublicProvenance(reads).cited_set(t, s, cited, selected, detail=False))

    def claim_limit_on(self, t: UUID, s: UUID, day: date, window_revision_id: Any,
                       k: datetime, basis_mode: str) -> dict[str, Any]:
        """0b: one UTC day's selected interval claim limits at `k`; a refused stored lineage is an inconsistent
        selection (409 after the W3-01 retry), never a guessed row. `basis_mode` is the estate request's frozen
        `page_one_mode` (c1-q7), so a live cursor's page two never relabels an identical live day HISTORICAL.
        AR-4: a stored `evidence.claim` day is projected by the same pure rule; any other day is read as today."""
        try:
            rows = _rows_of(self)
            served = None if rows is None else rows.claim(self._o.claim_limits, t, s, day, window_revision_id, k,
                                                          basis_mode)
            if served is not None:
                return served
            return self._o.claim_limits.claim_limit_on(self._c, t, s, day, window_revision_id, k,
                                                       basis_mode=basis_mode)
        except self._o.claim_limit_refused as error:
            code = getattr(error, "detail", {}).get("code")
            if code not in W1_RECONSTRUCTION_REFUSALS:  # c1 r1 M2: only these are one unprovable day
                raise EstateSelectionInconsistent(str(error)) from error
            return {"day": day.isoformat(), "site_id": str(s), "available": False, "currentness": None,
                    "intervals": [], "window_reasons": [], "window_assessment_revision_id": None, "known_at": k,
                    "reasons": [{"code": "HISTORICAL_SELECTION_UNAVAILABLE",
                                 "text": "The day's selection at the cutoff cannot be reconstructed from stored "
                                         "records."},
                                {"code": code, "text": str(error)}]}

    def pinned_windows(self, t: UUID, s: UUID, domain: str, from_: datetime, to: datetime,
                       evidence_cutoff: datetime, k: datetime) -> list[dict[str, Any]]:
        """Closure 5 B5: the pinned `_snapshot` per exact stored selected window intersecting `[from_, to)`, with
        the Site's row-local evidence cutoff as `known_at` and the estate cutoff `k` as the selection cutoff."""
        code = self._c.execute(text("SELECT site_code FROM site WHERE tenant_id = :t AND id = :s"),
                               {"t": t, "s": s}).scalar_one()
        reads = {COLD: self._o.cold, EV: self._o.ev}.get(domain)
        if reads is None:
            raise ValueError(f"No pinned window read for {domain!r}.")
        try:
            return reads.estate_snapshots_on(self._c, t, s, code, from_, to, evidence_cutoff, k)
        except KeyError:
            raise
        except LookupError as error:  # `SelectionPinRefused`: an inconsistent pin, never another head
            raise EstateSelectionInconsistent(str(error)) from error

    def cold_capabilities(self, pin: dict[str, Any]) -> dict[str, Any]:
        """0c `ColdSiteReadService.capabilities_on`, plus each selected analytic's own cited accepted IDs (a cold
        row cites only its owning analytic, closure 1 Q3)."""
        read = self._o.cold_site.capabilities_on(self._c, pin)
        by = {a: sorted({str(e).lower() for e in x.evidence_ids}) for a, x in pin["selected"].items()}
        return {**read, "evidence_by_analytic": by}

    def ev_capabilities(self, pin: dict[str, Any]) -> dict[str, Any]:
        """0c `EvSiteReads.capabilities_on`, whose public `unknown_meter` is the W2 `METER_GAP` input of
        `_next_candidates` (c1-q2), plus the pinned selected assessment's exact session revision IDs (selected
        basis for the selection token, c1-q3(5))."""
        read = self._o.ev_site.capabilities_on(self._c, pin)
        sessions = sorted({str(x).lower() for x in (pin["selected"]["result"].get("session_revision_ids") or ())})
        return {**read, "session_revision_ids": sessions}

    def cold_money(self, t: UUID, s: UUID, pin: dict[str, Any], k: datetime) -> dict[str, Any]:
        """W3-02 commit 3: 0c `ColdSiteReadService.money_on` over this pinned window's exact selected cold Finding
        revisions at `k` (W3-01 `_cold_window` on this connection), plus their Finding IDs."""
        findings = self._cold_window(t, s, pin, k)["findings"]
        read = self._o.cold_site.money_on(self._c, pin, findings)
        return {**read, "finding_ids": {str(f["finding_revision_id"]).lower(): f["finding_id"] for f in findings}}

    def ev_money(self, pin: dict[str, Any]) -> dict[str, Any]:
        """W3-02 commit 3: 0c `EvSiteReads.money_on` of this pinned window (its as-of head or transient guard and
        stored history recorded by the cutoff). Its `historical_label` is not the estate's (c1-q1). Plus the pinned
        selected assessment's exact session revision IDs, with or without a stored head (c3-q2(6))."""
        read = self._o.ev_site.money_on(self._c, pin)
        sessions = sorted({str(x).lower() for x in (pin["selected"]["result"].get("session_revision_ids") or ())})
        return {**read, "session_revision_ids": sessions}
