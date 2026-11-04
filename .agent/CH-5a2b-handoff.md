# CH-5a2b handoff (phase 1 of ~4; PARTIAL, context limit)

Branch `task/CH-5a2b-chain-counts`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch5a2b`, base main `27aa6a638`.
Authority: `AssetOpsV1-plan2\.agent\build-sheet-CH-5a.md` §B13 as amended by **§B14 (CH5a2b-R)**; pre-flight
`.agent/CH-5a2b-preflight.md` (facts F1–F9). `B` = `backend/assetops_backend`.

## Landed (`a8c748b7c`)
- `B/chain/vocabulary.py`: `Claim` (+`to_json`), `count_basis` (accepts GradeCounts or the §S.2 subset mapping),
  `count_claim(key, value, days)`, `sum_days`, `COUNT_TEXT`, `NOT_KNOWN_TEXT`, `provenance_suffix`.
- `B/chain/reader.py`: public `grade_counts_of(facts, measures)` (L2); `chain_api.py` uses it (no `_counts`, no `_Row`).
- `B/chain/threads.py`: `classify(states)` + `OPEN_CLASS/IN_HAND_CLASS/VERIFIED_CLASS`; `estate/portfolio.py`
  `thread_progress` uses it (legacy fields, own set); `VERIFIED_/ATTENTION_THREAD_STATES` alias the classes.
- L1: `portfolio.progress` `origin_selected` per Finding row at that row's cutoff via new `_same_segment` (shared with
  `_action_for`).
- R2: `VerificationService._cost_check_read` returns `source_class` (`actions/verification.py` ~1057/1077) →
  `ChainRequest.action_facts` → `ActionFacts.source_class` (`chain/read.py`) → `ActionFact.source_class`
  (`site_outcomes/board.py`, set in `mini._actions`). Wording: `board.action_result()` ("Verified{suffix}"),
  `mini.VERIFICATION_TEXT`/`VERIFIED_WITH_COST` `{suffix}`.
- Q6: `postgres_estate_read.verification` adds `source_classes` (from `details->'source'->>'source_class'`);
  `coverage._actions` row `_source_class` (private, so not on the wire); `placement.place` passes
  `provenance_suffix(action._raw._source_class)` into the `VERIFIED_WATCH_RETURN` text.
- Tests: new `backend/tests/test_ch5a2b_claims.py` (26); `test_cc_placement.py` gains the B7 text test plus the two
  Q1 guards (chip ignores consequence; `_mini_grid_money` never returns WITHHELD). Both guards were proven
  non-vacuous: a planted `cons in (WITHHELD, UNKNOWN)` failed 24, and a planted WITHHELD return failed 1; both
  were reverted. Fixtures in `test_out_b1_board`, `test_out_b2_mini`, `test_out_e4_readback`,
  `test_polish_pa2a_server_copy` now carry `source_class="REGISTERED_SIMULATION"`.
- Result: 351 passed on board, mini, placement, e4, pa2a, ch5a2 contract and refs, and w303 reduction. No Postgres
  file has been run yet.

## Next (in order)
1. **Q7/Q8 claims.** Add `B/chain/claims.py`:
   - `claim_days(req, sites, lo, hi)`: one `ChainRequest.day` per Site over `window_days`, then `grade_counts_of`; None on failure.
   - `estate_count_claims(req, sites, lo, hi, opportunity_count)`: the thread set is `site_chain.threads_of` restricted to threads with a Finding occurrence whose episode meets the window, read on `window_day`. Classify with `classify`. `open_threads` = open + in_hand.
   - Per-Site cutoff: add a ChainReadPort `evidence_cutoff` (`SELECT max(decided_at) FROM ingestion_disposition ... <= :k`, as `EstateSnapshot.evidence_cutoff`), then `site_cutoff(domain, known_at, ev, k)`.
   - Wire it into `/estate/chain` `counts` and `sites[].threads` (`chain_api.py` `_estate_chain`).
   - Wire it into the Portfolio `summary.claims` (all 3 keys) and `summary.count_basis = count_basis(days)` (`portfolio.py` ~803). Keep the old local value only for `finding_known`/`evidence_known`.
   - Wire it into the estate Findings `summary.claims` (`count.opportunities`, `estate/index.py` ~356).
   - Inject from `main.py` (~568, 577, 630) with a callable built over `outcome_board.s.chain_reader` + `registry` (`outcome_api.site_ref`), set on the index and Portfolio services.
2. **COH-17** in `tools/checks/chain_coherence.py` (rule list ~:1091). The collector adds `/api/estate/chain` per estate window (in `Collector.estate`, ~:166) and `/api/sites/{c}/chain` per built day. Add a non-vacuous self-test and fixture bundle.
3. **R1.** Add the ChainRequest ports `placement_facts(site, finding_ids)` (provenance via imported `PublicProvenance`, at most 3 statements, Q2) and `action_rows(site)` (Q5; `actions.lifecycle.reduce`; keys `resolution_state`, `verification_outcome`, `application_state`, `_raw._verification_window`, `_raw._source_class`).
   - In `mini.py` (`compose` ~399, `_findings` ~643, `_actions` ~671): drop the `estate` port and `estate_bounds`. The chip is computed only for `in_window` heads (Q3).
   - Failure names are `placement_facts`/`action_rows`; the diagnostic is renamed `ACTION_ROW_MISSING` (Q4).
   - Update `site_outcomes/read.py:253-283,461-485` (the estate port and the prefetch) and the `test_out_b2_mini` Fake.
4. **Q11/L3.** Factor the cold/EV cutoff resolution out of `read.py:347-366` into one service method used by both the board and `/threads/{id}` (optional `from`/`to` via `board_window`). The docstring says "last visible event".
5. **Tests.** L2 `test_ch5a2_chain_api_postgres.py` and the scoped postgres files (w301 index, w303 fixture, s6 action store, ch5a1 reader), 1–2 per call. Then vitest-related, only if the frontend is touched (it should not be).
6. **Rebuild the MD-0 template once at the slice head.** Run `status` right before it, because MD-0b may prune. Wait if MD-0b is building.
7. **L3 clone and L3m.**
   - A/B the chips and labels; only the Q3 classes are allowed.
   - Assert every VERIFIED summary has a non-null `source_class`.
   - List old → new `count_basis` values with the screen text each changes, and where the thread counts differ.
   - COH-17 = 0, and the "on the days checked" texts appear only in GAP-K7/C3/E2 windows.
   - Record payload sizes.
8. Guards, then the packet `.agent/review-packet-CH-5a2b.md`.

## Risks
- Golden or fixture diffs from the "Verified" wording where the unit fakes lacked `source_class` (handled for the files above). The CH-5a2a contract goldens passed unchanged.
- `/estate/chain` and the Portfolio use different cutoff sources (`evidence_cutoff` vs the estate `_WindowRecorder.cutoff`). Q7 routes all claims through the one function, so this matters only for the legacy fields.
