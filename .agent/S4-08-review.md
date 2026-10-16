# S4-08 slice review: Site assumption and consequence history

Reviewer: fresh independent Claude reviewer (not the author). Revision `48ace99f` (`task/S4-08-assumption-history`), diff `e46bbd7c..48ace99f -- ':!.agent'`. Judged against `tasks/S4-08-assumption-consequence-history.md` (with plan fix round 1), `D-2026-10-16-s408`, the plan reviews and the review packet.

## Verdict: ACCEPT

There are no High or Medium findings. The two Lows below do not block the merge.

## Findings

1. **Low: the "price version used" link drops the selected cutoff, and the packet says it keeps it.** See `frontend/src/sites/ConsequenceHistory.tsx:96`, which calls `links.assumptions({ revisionId: row.price.price_revision_id })` with no `recordedAt`. Packet deviation 2 (`.agent/S4-08-review-packet.md:46`) says "Paging and price links keep it." Only the paging links (`:191`, `:198`) do. From an explicit `?recorded_at=` view, this link opens the exact price version, but the price list and the history are then re-read at a fresh server-default moment. That is not dishonest: the price ID is exact and the page states its moment. It does break the packet's "same cutoff through contextual links" intent and makes the packet's claim inaccurate. Fix: pass `recordedAt: body.cutoff.recorded_at` through to `Row` and into the link (the price route already accepts both `revision_id` and `recorded_at`), or correct the deviation text. This is an acceptance-wording gap, not a correctness failure.
2. **Low (residual, not a defect): currentness classification is not covered by the fence.** `financials/adapters/postgres_consequence_store.py` (`site_history`) builds the fence from consequence rows only. `finding_revision` rows feed `classify` from each page's own snapshot. A FindingRevision that commits between pages, with an application-clock `created_at` at or before the cutoff and no consequence yet, can change one Finding's at-cutoff label between page one and page two without a 409. No row is double-labelled current, and no amount changes, because amounts are never current here. Record this in the packet's residual risk. No code change is required.

## Focus points verified

- **No current amount at any cutoff.** `current_amount_shown` is the constant `False` (`consequence_history.py:217`), and every row has `is_current_amount: False`. The UI type guard `isHistory` rejects a body where it is not `false`. `SHOWN` requires all four of these: the source gate is open, the lineage is consistent, the version is `PRICED` with `ROUNDED_OUTWARD`, and the exact-version S4-05b `permits_current_money` check passes (`:256-267`). Closed source gives `SOURCE_CLOSED` first and hides the amount. A displayed amount carries the historical audit label, the "Not a current cost." text and the version's source label. Test: `test_no_current_amount_at_any_cutoff_even_when_every_gate_passes`.
- **Deviation 1 (LR-01 not applied to recorded audit amounts): accepted as honest.** LR-01 is documented as a gate on *current* money (`consequence_read.py:17-21`: an ineligible head "stays recorded history"). The existing Finding Financials view already shows pinned earlier versions' recorded amounts as "Recorded for this version; not the current cost" without LR-01 (`FindingConsequence.tsx:190-197`, `:574-608`). S4-08 is stricter than that precedent, because it also applies the exact-version source gate. This meets Q3: "existing source and historical money-display gates".
- **CURRENT_AT_CUTOFF.** `classify` (`:156-167`) treats a FindingRevision as qualifying if its `created_at` is at or before the cutoff, or if it has a consequence recorded by the cutoff. It takes the latest qualifying revision by `revision_no` and the latest consequence within it by `(recorded_at DESC, id DESC)` (SQL subquery). When the latest FindingRevision has no consequence, no row of that Finding is current. This matches Q2 and the app-clock rule. The real skew and the same-instant boundary are both tested.
- **Unpriced versions** are listed with `NO_PRICE_LINK` or `NOT_EVALUATED`, a null amount and a typed disposition. A broken or foreign link is `LINEAGE_INCONSISTENT` and never substituted.
- **Fence and 409.** The fence is a count plus the maximum `(recorded_at, id)` over all in-scope rows. It is recomputed in each page's own REPEATABLE READ snapshot, and the default cutoff `clock_timestamp()` is the snapshot's first statement. The cursor binds tenant, Site, cutoff, limit, the fence token and the last pair, the same as the S6-03 `site_index.py` pattern. An undecodable cursor gets 400. The late-commit Postgres test is real. A second connection holds an uncommitted row stamped before the cutoff during a default-cutoff page one, then commits. Page two returns 409 with `rows: None`, page one reloads with a different fence, the late row is then listed, and a row stamped after the cutoff stays excluded.
- **Shared exact cutoff string.** On the default view, `SiteAssumptions` passes `historyRead.value.cutoff.recorded_at` unchanged to `getAssumptions`, with no `Date` round trip. `Date` is used only to validate the URL value and to format display. Paging links carry the server string.
- **A failed history read is refused, never silently CURRENT.** On the default view, `cutoff === null` renders "Prices unavailable" (`data-financials-read="no-cutoff"`) and makes no price read. A 409 navigates (replace) to page one at the same `recorded_at` and `history_limit`.
- **The two deliberately changed expectations are justified.** The default-view price read now uses `recordedAt: CUT` instead of `null`, and `data-price-cutoff` is now `RECORDED_CUTOFF`. Both follow directly from contract item 1, which says the default view reads history first and passes its cutoff to the price read.
- **Foreign Site and scope.** Access returns 401 or 403, then 404 for an unknown Site, before any validation or read. A foreign tenant or Site cursor gets 409 `SCOPE_CHANGED` with no rows. All queries filter on tenant and Site. No estate or Site total is returned. Only reads were added: no migration, no INSERT or UPDATE, and no writer.
- **Presentation.** IDs appear only inside the closed "How this was worked out" disclosure and in non-visible `data-*` attributes. No leaks were found.
- **The walkthrough is reachable.** `tools/s408_assumption_history_walkthrough.py` is guarded (`assetops_s408*`, not `_test`), has prepare, serve, links, close-gate, open-gate and drop, and is linked from the `assumptions` row of `tasks/W1-UX-mockup-fidelity.md`. I did not run it.

## Checks run (this review, revision `48ace99f`)

- `pytest backend/tests/test_s4_consequence_history.py backend/tests/test_s4_consequence_history_postgres.py -q`: **32 passed** in 74.7 s, using a private `assetops_s408rev_test` database. That database was created and then dropped, and I confirmed it is gone.
- `npx.cmd tsc --noEmit` (PowerShell): exit 0.
- `npx.cmd vitest run src/sites/__tests__/siteFinancials.test.tsx`: **48 passed**. It ran in this environment despite the known esbuild sandbox issue.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.

## Not verified

- **Full backend suite.** The implementer's run on `46dc42cb` was stopped at about 63% when it hit the 30-minute cap, and it produced no JUnit file. No complete full-suite evidence exists for this slice. Per the dispatch, the coordinator runs it at merge, and the merge should wait for that pass.
- **Full frontend suite and production build.** I did not rerun them. The packet reports 1704 passing and a successful build on `46dc42cb`.
- **Walkthrough `prepare` (23/23) and browser and layout evidence at 1440/390 (owner 44/44, closed 16/16, mixed 16/16, overflow 0).** I did not rerun these; they are the packet's claims only.
