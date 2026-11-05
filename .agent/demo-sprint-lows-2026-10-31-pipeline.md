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
- WALK1-5 re-review 2 Lows: L1 WK-6 derive noon from pinned[-1] in Site zone instead of hi-12h; L2 one-frame stale price on known_at change (reset price when read disabled / key by validAt|recordedAt); L3 last-resort validAt fallback is Date.now() (only with no pinned day, no URL to, no renewable link) — Architect to confirm or show "not read".
- WALK1-5 merge: close R682 (superseded by R685/R687).
- WALK1-6 Lows: L1 board rounds mini cost range half-even while Estate Financials rounds outward (Architect); L2 strip suffix "on its board" should be "on their boards" for k>1 (PortfolioOutcomes.tsx:176; not visible in demo, k=1); L3 money2 crashes on exponent-form numbers; L4 captures.json `code` records base revision. Vitest timing flakes: evEnergy/evDepth R347 and generatorLifecycle under full load.

## QW-1/QW-2 Lows (review-QW-1-2.md, 2026-11-03)
- L1 perf.py:100: no logging handler configured, so `assetops.perf` INFO lines likely not emitted under serve; CH-0 must configure/document it before relying on it.
- L2 estate/index.py:184-188: lineage-retry read not timed (under-reports).
- L3 test_w502_domain_intent_api.py:50: `COLD` default arg imported only with DB URL -> collection NameError without one (pre-existing on main).
- L4 libyaml loader test fails with relative PYTHONPATH (subprocess cwd backend/, editable install resolves stale AssetOPsV1 checkout); passes with absolute PYTHONPATH.
- Residual: with no known_at, estate values come from one snapshot before first board (up to ~10 s older); one lineage 409 sends all Sites to per-Site reads.

## CH-0 Lows (review-CH-0-r2.md, 2026-11-03)
- L1 scheduling/tick.py:291-297 dead handler code after `return perf.enable_log(stream)`; delete.
- L2 chain_coherence.py:398-402 self-link exemption compares path+query only; also require no scheme/host/fragment (+test).
- L3 COH-0 cannot see a request missing from the manifest; optionally check expected requests per window.
- L4 tick CLI test leaves perf.LOG.propagate False; restore in test.
- Residual: importing host/lab_app.py prints perf lines to stderr; --known-at mode makes Kobo date-equivalence not apply (extra COH-1 findings, not false passes).

## CH-1a Lows (review-CH-1a.md / -r2.md, 2026-11-03)
- L2 (latent): not-expected day with asset-subject measure writes no row -> reader counts NO_DATA not NOT_EXPECTED (CH-1b).
- L3 (latent): chamber peak and backup chains Site-wide, not per subject (CH-1b).
- L5 packet: D3 "reading-based count would not change grades" untrue for 24 Oct (13 chamber readings, no assessment -> NO_DATA); name 24 Oct in SWEEP-DS.
- L6 builder.py prints latest+1 revision for unwritten rows (cosmetic; CH-1b).
- Residual: re-assessment detected only via new run id; _WINDOWS ignores selected_at and pending_jobs ignores known_at; 0043 L2 downgrade test must be rerun after CH-2 lands.

## CH-2 Lows (review-CH-2-r2.md, 2026-11-03)
- R2-L1 no unit test for action_thread_id on Portfolio row (portfolio.py:213).
- R2-L2 test_a_non_protected_database_writes_through_the_store accepts 3 exception types; tighten to RuntimeError match="write attempted".
- R2-L3 backfill step (a) builds snapshots up to today (rows for 1-3 Nov past story end); rerun on a later day writes rows -> CH-1b / SWEEP-DS.
- R2-L4 chain/__init__.py docstring names only CH-2.
- CH-1a has no estate-guard self-test of its own (reviewer wrote a scratch probe; 3 passed) -> add one.

## CH-3 Lows (review-CH-3-r2.md, 2026-11-04)
- N1 skip reason differs between runs after a planned CLOSED event (no write differs).
- N2 credit.py parses "-" as 0, rejects "1e3" (cannot credit wrongly).
- COH-14 thread-line match is a text prefix; add structured `thread_lines` field (CH-5a / copy pass).
- DD-1 inventory: ACT-000002 history OPEN 28 Oct -> ACTION_IN_HAND 2 Nov (build time) -> CHANGE_APPLIED 31 Oct; with no cutoff Cold start reads "applied" 31 Oct/1 Nov, ACTION_IN_HAND never current.

## CH-1b residuals (review-CH-1b-r2.md, 2026-11-04)
- Writer guard checks templates only; optional L0 test comparing `_values` expansion with guard shapes.
- Per-page select time grows with consumed history (~10x over 14 days); 90-day ~15 s/Kobo day is an estimate -> DD-1 note (commit-safe cursor or pruning if real).
- L3 tick output lacks consume/drain split (evidenced at L2 only).

## MD-0 residuals (review-MD-0-r2.md, 2026-11-04)
- Three studies, not two: product also queues a 10-27..10-31 study (UNKNOWN, 2 eligible) straddling undelivered D9; CH-5a1 must not assume one study per declared window.
- Module hashes taken at end of each build step, not at import (mid-step edit window) - residual.
- L1 parity exemption covers 3 of 4 renewable channels (ac-power is in dispatch mapping) - packet wording.
- Receipt: plain reasons missing for OUTSIDE_FOUNDATION_PERIOD / OUTSIDE_BINDING_PERIOD (SWEEP-DS).
- Product: V3 path accepts point samples on power channels, dispatch uses them as fallback, chain coverage ignores them (SWEEP-DS / post-demo).
- `full` 14-day build still unmeasured.

## CH-5a1 Lows (review-CH-5a1.md, 2026-11-04)
- L1 L2m counts occurrences via raw SQL; R8 late_fill/consume step on MD-0 missing.
- L2 UTC-midnight estate window: Kobo summary card = local day of to-1us, so "S=31 Oct" summary shows the 1 Nov board (cost card NA -> On track). As ruled (E4); owner should see it; re-check in CH-5a2 B3.
- L3 Portfolio "max 1 per key" holds by construction; repeated reads (cited_provenance x20 etc.) not ledgered -> CH-5c.
- L4 _last_local_day in site_outcomes/read.py duplicates summary_day.
- L5 dead wiring: BoardServices.finding_index, parse_finding_index, covering_days.
- L6 L1 goldens generated from branch, not A side.
- Residual: memo frozen only inside route scope; db_today() UTC read as Site-local (21:00-24:00Z default Kobo board shows local previous day).
- MD-0 (M1): GAP-K7 UNKNOWN before fill until MD-0b runs mini queue; M3 COH-5 x6 -> CH-5a2; M4 template status recheck on main.

## FIX-MAIN-1 Lows (review-FIX-MAIN-1.md, 2026-11-04)
- L1 two xfails (test_md0_mechanism_postgres.py:185,:271) still say "owner CH-5a1 R5" -> should be MD-0b (fix in MD-0b).
- L2 tools/summarize-test-run.py:39 counts JUnit xfail as skipped; --compare proof fails on them (test-tooling follow-up; read E2 summary accordingly).
- L3 runner time cap counts the ensure build; slow build shows as HANG and leaves an untagged staging DB.
- L4 publish test creates real-pattern template with built_at=now; could evict main's template under keep-two-newest.
- Evidence DB assetops_demo3_fixmainone_test + var/demo3_fixmain1 kept; drop after.
- First container run on merged main rebuilds MD-0 template (~11 min) per M4.

## CH-5a2a (merged ab890f695, review ACCEPT, .agent/review-CH-5a2a.md)
- L1 `estate/portfolio.py:571` origin_selected reads the Action segment at the default cutoff, Finding segments at the per-Site cutoff; compare per Finding row as `_action_for` did. Owner: CH-5a2b.
- L2 `chain_api.py` imports private `chain.reader._counts` and builds day-count rows in the route. Owner: CH-5a2b.
- L3 `/threads/{id}` (chain_api.py:153,156) uses raw known_at, not the board cutoff, for cold/EV; can show events `/chain` threads[] hides. Owner: CH-5a2b.
- L4 Unconverted renderers (work screens, PortfolioOutcomes overview_href, EstateEvidence, EstateFinancials) and backend path builders outside href_for (read.py:543 _overview_href, work/global_index.py:235, work/operational_index.py:39); dead `_site_href` evidence_money.py:109. Owner: CH-6a/CH-6b sweep.
- L5 D12 frontend /chain golden rendering moves to CH-5b — Architect to record.
- L6 backend vs client encoders disagree on `!*'()~`; no live ids use them.
- Residual: `EarlyWarnings.tsx:116` miniBoardDay is a second client-side day rule outside window_day (predates slice). Owner: CH-6a.
- Merge trap: MD-0b merges second — delete both MD0b-R:A1 COH-8 entries; L3m COH-8 = 0 on states AND close.

## MD-0b (merged 7b8a22b78, reviews ACCEPT, .agent/review-MD-0b.md)
- L2 `run-backend-suite-in-container.ps1:85-86` PS 5.1 mangles `§` in the base fixture → spurious close rebuild (~20 min) for slices editing mechanism-v1.json; never skips.
- L3 derived `generator_power` reads 15 kW one interval before status RUNNING; +1.25 kWh to baseline generator_kwh (cost check only, not verdict).
- L4 "`-Close yes` at E1/E4 and post-merge" only in comments; add to TESTING.md / end-game runbook (E1/E4).
- N2 guard A false-fails in a worktree without `.venv` unless ASSETOPS_GUARD_PYTHON is set.
- Seed timings: drain_mini ≈30–34% of each seed — candidate for an inputs/producers split if rebuild cost matters.

## CH-5a2b (merged 414c43a81, review ACCEPT, .agent/review-CH-5a2b.md)
- L1 portfolio.py:578-581 per-row origin_selected fix has no revert-failing test. Owner: CH-6b.
- L2 /estate/chain `counts` keys are `count.*` vs §B1 bare names — Architect to record the wire form before a client reads it (CH-5b/CH-6a).
- L3 count_basis list has no "before" for MD-0 close.
- L4 frontend EstateCountBasis lacks NOT_KNOWN (harmless per Q9). Owner: CH-6b.
- L5 COH-17 doesn't report compared/skipped counts (a vacuous pass looks identical). Owner: CH-6b with COH-18.
- Residual: Portfolio + Findings now run the full claims read per Site with no timings recorded → CH-5c perf baseline must time both; non-site-store chain-read errors now fail these routes.
- CH5a2b-R2 packet table (per-window named days + reason) folded into CH-9's merge: CH-9 merges second and must re-collect L3/L3m anyway (measure rename + critical_served change Kobo day grades and count_basis).
