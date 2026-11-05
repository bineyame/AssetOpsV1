# CH-5a2b pre-flight (Implementer, 2026-11-05)

- Branch `task/CH-5a2b-chain-counts`, worktree `AssetOpsV1-ch5a2b`, cut from main `27aa6a638`.
- Scope read: build sheet CH-5a Part B as amended by §B13 (CH5a2-R): B3 bullet 1 (R1), B7 (R2), PC-1 count claims
  and COH-17 (R3), plus CH-5a2a review Lows L1-L3 (`.agent/demo-sprint-lows-2026-10-31-pipeline.md:108-111`).
  Claim/`count_basis` exactly as CH-6 sheet §S.2.
- Result: **11 questions** (below), each with a proposed default. No code written. Stopping for the Architect.

## Code facts the questions rest on (`B` = `backend/assetops_backend`)

- **F1. Board chip inputs.** The board uses only `place(...).confidence` (`B/site_outcomes/mini.py:659`).
  `_confidence` (`B/estate/placement.py:126-141`) reads only `source_provenance.state`, `lifecycle` and
  `cons == "WITHHELD"`. `site_cov` adds reason text only; `action` only changes the group. The coverage consequence
  rule `_mini_grid_money` (`B/estate/coverage.py:241-269`) never returns WITHHELD (PRICED / UNPRICED / UNKNOWN).
  So on every input the board chip is a function of (source provenance state, lifecycle) alone.
- **F2. Consequence rule cost.** `_mini_grid_money` takes a snapshot object and calls `consequence`,
  `consequence_provenance` (PublicProvenance `cited_set`), `eligibility` and `source_gate` per head
  (`B/estate/adapters/postgres_estate_read.py:172-188`). Importing it needs a snapshot shim serving four reads.
- **F3. Finding source provenance cost.** `finding_provenance` = `PublicProvenance.cited_set` over the revision's cited
  evidence from the index lineage (`coverage.py:163-189`, `postgres_estate_read.py:141-175`): lineage read, link rows,
  resolver. Not one SQL statement.
- **F4. Today's chip is null without an estate row.** The estate Finding rows cover the board's UTC day only
  (`mini.estate_bounds`), and only when that day is fully selected; heads span the 31-day work window. Every head
  without a row has a null chip (`mini.py:656`).
- **F5. Placement text site.** `REASON_TEXT["VERIFIED_WATCH_RETURN"]` (`placement.py:42`) is rendered on Portfolio and
  estate Findings rows. Their Action rows come from `coverage._actions` (`coverage.py:358-414`, estate snapshot
  `verification`), not from the board's new `action_rows`.
- **F6. Thread sets differ.** `thread_progress` (`B/estate/portfolio.py:599-618`) counts the threads of the
  Portfolio's selected Finding rows (`attach_threads`; a PARTIAL Site drops heads next to unchecked days). The
  `/estate/chain` route has no estate Finding rows. Its natural set is `site_chain.threads_of`
  (`B/chain/site_chain.py:83-97`): occurrence episodes meeting the window, **plus** threads with an event in the
  window, and opportunity threads.
- **F7. No ChainReader in the estate services.** `EstatePortfolioService` and the estate Findings service read no
  `GradeCounts` today. The Portfolio `count_basis` is coverage-based (`portfolio.py:803-804`).
- **F8. The client reads `summary.count_basis`.** `PortfolioOutcomes.tsx:85,99,104` and `EstatePortfolio.tsx:711`
  switch the checked-days clause and badge texts on `count_basis === "CHECKED_DAYS"`.
- **F9. L3 cutoff.** For cold/EV the board's cutoff is the overview body's resolved `window.known_at`
  (`B/site_outcomes/read.py:347-366`, `board_cutoff` :569-573). The thread route has no window to read it with.
- **R2 source** confirmed: `VerificationService._cost_check_read` (`B/actions/verification.py:1053-1080`) already loads
  the selected outcome row; `details.source.source_class` is on it. There is no derivation to add.

## Questions (one batch; proposed default for each)

**Q1 (R1, placement_facts content).** By F1, the consequence head state and `recurs_after` cannot change the board
chip. Building the consequence state "by the coverage rule, imported" needs a four-read snapshot shim (F2).
- *Default:* `placement_facts` returns the source provenance state and `recurs_after` id and title (one finding
  revision read). The consequence head state is **not** built in this slice. `place` gets the row without
  `consequence`, which yields the same confidence by F1. CH-6/CH-7 adds the consequence when a chain consumer
  needs the placement group.
- *Alternative:* build the shim and import `_mini_grid_money` unchanged. That is about 0.75 unit more, and it is
  several statements, not one query.

**Q2 (R1, "one indexed query" for provenance).** Source provenance cannot be one SQL statement (F3).
- *Default:* `placement_facts` is one memoised port call (ledger 1). Inside it there is one SQL statement for the
  cited evidence ids of the selected revisions, plus the batched link-row provenance through `PublicProvenance`
  imported unchanged (as `cited_provenance_many` does). That is at most 3 statements on one read-only connection.
  `postgres_chain_read.py` gains the import of `evidence.public_provenance`, and the injected
  `provenance_reads`/`link_rows_many` come from `chain/composition.py`.

**Q3 (R1, chip on heads without an estate row today).** By F4, the chain port gives every head a chip, so heads
outside the board's UTC day (Kobo, UTC+3) or on a not-fully-selected day gain a chip where today it is null.
- *Default:* compute the chip only for heads with `in_window` true, so it is null outside the board day as today.
  The A/B reports any remaining difference and does not adapt it.
- Alternative: every head, with the differences reported.

**Q4 (R1, failure and missing-row markers).** Today an estate read failure adds `"estate"` to `reads.failed`
(PARTIAL notice). An Action present in `action_index` but missing from the estate rows adds the diagnostic
`ESTATE_ROW_MISSING` (`mini.py:121,686-691`).
- *Default:* the failure names become `"placement_facts"` / `"action_rows"`, with the same notice behaviour. The
  diagnostic code `ESTATE_ROW_MISSING` is kept byte-identical (wire-stable) and now means "missing from
  `action_rows`". The `estate` port and `estate_bounds` are deleted from `MiniPorts`.

**Q5 (R1, action_rows set).** The estate Action rows are `select_action_scope` over the 31-day work window, wrapped
in `_raw`.
- *Default:* `action_rows(site, k)` gives the Site's MINI_TRIAL `chain_action` rows created by `k`, with events by `k`,
  reduced by `actions.lifecycle.reduce` (imported; the reduce `coverage._actions` uses). It adds the
  verification-plan window open at `k`, `_selected_recorded_at` and `source_class` (R2). Rows are shaped with the
  exact keys `workflow_label` reads (`resolution_state`, `verification_outcome`, `application_state`,
  `_raw._verification_window`). The board joins by id to its windowed `action_index` rows, so there is no window
  bound in the port.

**Q6 (R2, the Portfolio / Findings placement text).** By F5, the `placement.py:42` text is rendered from
`coverage._actions` rows, which `action_rows` does not feed.
- *Default:* the estate `snapshot.verification` read also returns each selected outcome's stored
  `details.source.source_class`. `coverage._actions` copies the resolution outcome's value onto the row as
  `source_class`. `place` passes `action.get("source_class")` to the VERIFIED_WATCH_RETURN text through
  `provenance_suffix`. There is no new derivation.
- This edits `postgres_estate_read.py` and `coverage.py`, probably import-traced, so the MD-0 template is rebuilt
  once at the slice head (R5).

**Q7 (R3, thread set for COH-17).** The two sets differ (F6), so the Portfolio and `/estate/chain` `count.*_threads`
can disagree.
- *Default:* one pure classifier `chain.threads.classify(states) -> {open, in_hand, verified}` (plus the existing
  `priority_site_count`), called by `thread_progress` over its unchanged Finding-row set. `/estate/chain` feeds it
  `threads_of` restricted to threads with a **Finding** occurrence whose episode meets the window: no event-only and
  no opportunity-only threads, at the per-Site cutoff, read on `window_day`. COH-17 is the check. If L3 or L3m shows a
  difference, I report it and stop, never adapt.
- *Alternatives:* (b) `/estate/chain` runs the estate Finding scope (`select_finding_scope` + `attach_threads`), the
  snapshot read the chain is meant to retire; (c) the Portfolio switches to the chain set, so its
  `verified_resolution_count` and `priority_site_count` may change.

**Q8 (R3, `days` in the Portfolio and Findings summaries).** F7.
- *Default:* `main.py` injects into both estate services a callable from `chain/composition.py`:
  `claim_days(tenant, sites, lo, hi, known_at) -> {site_code: GradeCounts | None}`. It does one
  `ChainRequest.day` per Site over `window_days(lo, hi, tz)` and uses the public GradeCounts-from-DayFacts function
  (L2).
- The request's own `known_at` is used, as `/estate/chain` uses it, so COH-17 compares equal inputs.
- `days` is the §S.2 subset summed over the Sites. If any Site's counts are None, `days` is None (NOT_KNOWN).
- The scope is the body's whole Site scope, with no lens.

**Q9 (R3, `summary.count_basis` is read by the client).** By F8, switching the value to `count_basis(days)` changes
rendered text wherever the grade basis and the coverage basis differ. For example, a PARTIAL-graded day with COMPLETE
Finding coverage flips `onCheckedDays` texts. Also `null` becomes `"NOT_KNOWN"`, which is harmless.
- *Default:* as ruled, with no frontend edit. The packet lists every old → new value on the clone and on L3m windows,
  with the screen text each one changes.
- *Alternative:* keep the coverage value in `count_basis` until CH-6b, and carry the new basis only in
  `summary.claims[*].basis`.

**Q10 (R3, lens on the Findings summary claims).** The estate Findings route takes `lens`.
- *Default:* `summary.claims` (`count.opportunities`) is lens-independent: it is the whole scope on every lens. COH-17
  reads it from the `findings_all` (lens=all) bodies the collector already fetches.

**Q11 (L3, thread route cutoff).** F9.
- *Default:* the thread route takes optional `from`/`to` (the board's `board_window` parsing). For cold/EV it
  resolves the cutoff with one service method factored out of the board's cold/EV path: the same
  `ports.overview(lo|None, hi|None)` read, then `board_cutoff`. With no window it equals `/chain`'s default-window
  `window.known_at`. Mini is unchanged.
- The state rule stays "last visible event", and the contract docstring says so. It costs one extra overview read on
  a cold/EV thread request.

## Not questions (will build as written)

- `Claim`, `count_basis`, the texts table and NOT_KNOWN, exactly per CH-6 §S.2 and §B13 R3. The texts go through
  guard V. If V flags one, I report and stop.
- `provenance_suffix` in `chain/vocabulary.py`. `VerificationService.summary` gains `source_class`, which flows into
  `ActionFacts`/`ActionFact`. The L3/L3m assertion is a non-null `source_class` on every VERIFIED summary.
- L1: per-row `origin_selected` at the row's cutoff (`action_segment_for(a, r)`). L2: a public
  `grade_counts_of(facts, measures)` in `chain/reader.py` replaces the private import and the route `_Row`.
- COH-17 plus a non-vacuous self-test. The collector adds `/estate/chain` per estate window and `/sites/{c}/chain`
  per built day.
- MD-0b `MD0b-R:A1` entries: left alone if present on main.
