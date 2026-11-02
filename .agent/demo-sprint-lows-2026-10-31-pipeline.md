# Test-pipeline hygiene (2026-10-31)
- MEDIUM: several lanes share `assetops_test`. The FIX-COLD-DRAIN reviewer found it reset to migration 0009 mid-session by another lane, which could explain intermittent Postgres failures, e.g. the w301 cold KeyError. Proposal: give each lane or worktree its own `*_test` DB name.
- MEDIUM: `check-architecture.ps1` rule 8 reported cold/EV consequence INSERTs missing from `postgres_consequence_store.py` (lines 966/983/1076). The count varied 4/6/6 across runs under machine load, so the check is non-deterministic. It needs a look.
- LOW: FIX-COLD-DRAIN L3, the 60 s Site-lease slack now covers 9 children.

## DEMO-A final review Lows (merged `4f57261d3`, review `.agent/review-DEMO-A-final.md`)
- L1: CO-1 lacks the original U6 assertion `"Reliable service and battery and generator life" in mnh["text"]` (`tools/demo_combined_finish.py:142-149`); text is present in the kept build, add the line back.
- L2: CO-1 "Action on the Cost row" reads `items(cost)` incl. `earlier`, so it cannot tell a linked Action from CO-3's line (`tools/demo_combined_finish.py:145-147`); restrict to `issues` + `in_hand`. The href assertion is the real guard.
- L3: register R535/R552 description text and `.ai/CODE_STATE.md:6251-6252` ("main `15eed62c8`", "Addenda 1-3") are stale; statuses closed by coordinator at merge, descriptions still historical.

## POLISH PB-0 re-review Lows (`.agent/review-POLISH-PB-0.md` re-review section)
- N1: gloss test (`tools/checks/test_mock_deviation_labels.mjs:110-114`) cannot fail if gloss stripping is removed; add an assertion that "generator running" alone counts 0.
- N2: `CAPTURE_TEXTS` in-page selectors (`tools/demo-combined-vocabulary.mjs:104-119`) are untested; a selector change could reintroduce the M1 bug unnoticed. Add a string or jsdom test.

## Clock time bomb found in PA-2a review (2026-11-01)
- RESOLVED by FIX-W401b merge. `test_w401_work_service_postgres::test_foreign_asset_and_evidence_refuse` failed on main since ~02:05Z 2026-11-01: the `clocked` fixture freezes the store clock at `POSITIVE_NOW` (2026-11-01T01:00Z) but request bodies use real-clock `at()` (lines 43-48), so `check_occurrence` (`work/model.py:236-238`) returns `WORK_OCCURRED_AT_FUTURE`. Other `clocked` tests with default times are exposed. Fix: derive those times from `POSITIVE_NOW`. Blocks a clean `-Tier all` until fixed.

## POLISH PA-2b review Lows (`.agent/review-POLISH-PA-2b.md`)
- L2 (pre-existing harness): `test_out_b4_board_postgres.py:71-80` `_case_db` uses fixed DB name `assetops_out_b_guardrail_test` with a module-scoped fixture; under `-n` without `--dist loadfile` two workers collide (SITE_NOT_FOUND or killed connection). Always pass `--dist loadfile` with `-n`; later tag `_case_db` names per run/worker.
- L3: `WarningFacts.soon_until` (`warnings.py:96`) no longer read; drop or assert.
- Residual: historical asset labels use today's same-type count (no cutoff, per q7-1); PB-3 `assetWords` must not reintroduce "EV connector".

## POLISH whole-diff re-review Lows, for the post-walkthrough copy round (`.agent/review-POLISH-whole-diff.md`)
- L-A: `SiteFindingHistory.tsx:461-467` visible "Related Findings: … Finding <8-char id>"; `:576-641` "Times and references" shows model_version and 8-char assessment ids outside Technical details.
- L-B: `tools/demo_combined.py:197-199` prewarm prints "ready:" for any HTTP status; print only on 2xx.
- Capital labels: "Review Finding" / "Open Finding →" (`EstatePortfolio.tsx:182`, `coldSiteViews.tsx:662,703`, `EvAssessmentViews.tsx:347`, `EvSiteViews.tsx:237`); "Service disruptions recorded in Findings" on Portfolio.
- Off-capture "test data": none on demo path now; "Demonstration data" Mode value inside Technical details on Kobo all-open.
- Test pipeline: evEnergy `energy_states_table_loading` load flake; test_out_b4 `_case_db` fixed-name collision under -n without --dist loadfile.

## WALK1 round (2026-11-02)
- MAIN TEST FAILURE (pre-existing, from POLISH-PC a08bf548b): `test_idx_gaps_board::test_board_finding_titles_are_the_frontend_plain_titles` fails on main — `findingWords.ts:35` says "earlier finding" but the backend MERGED title still says "Finding". Needs a small fix on main (fold into WALK1-4/5 or a standalone fix).
- WALK1-1 N1 (pre-existing): board shows unqualified "None open" when the only unchecked days are just outside the board window (`finding_gap_line` returns None, withheld lost). Check on G1 captures.
- WALK1-1 N2: `SiteAnalyticsFrames.tsx:833` "Open Finding overview" capital F.
- WALK1-1 L4: Portfolio "Fixes confirmed" (30-day verified resolutions) may differ from the Assure card's verified Actions count; record both on the portfolio-week capture at G1.
- WALK1-2 L2: identical related-finding link texts when a finding relates to two others. L3: finding-history capture added to G1 list (via WALK1-3).
- WALK1-2: E2 demo prepare unverified — confirm the EV fault-Tuesday window reads ESTIMATED with an amount at G1 (ev-board-fault capture).
- MAIN TEST FAILURE (from WALK1-1, missed by its review): `test_out_b2_mini::test_pending_finding_index_unsettles_finding_outcomes` expects no `withheld` key in `finding_gaps`; WALK1-1 added it. Update the test expectation (fold into WALK1-3b with the MERGED-title fix).
- WALK1-3b L5: WK-4 in `tools/demo_combined_finish.py` hard-codes "(needs 3 checked days)"; use regex `\(needs \d+ checked days\)$` (fails safe today).
