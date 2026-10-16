# S4-08 review packet: Site assumption and consequence history

Task: `tasks/S4-08-assumption-consequence-history.md` (`I-assumption-consequence-history-read`, `I-assumption-consequence-history-ui`, `I-S4-08`). Authority: `D-2026-10-16-s408`, plan re-review Lows L-R1/L-R2, `D-2026-10-16-w1-ux`. Branch `task/S4-08-assumption-history` from main `e46bbd7c`. USER_REVIEW_REQUIRED: true, satisfied by fresh independent slice review now and the combined W1 walkthrough later (owner-walkthrough policy 2026-10-16). Do not promote `assumptions:3#a` before the accepted review.

## Outcome

Site > Financials > Assumptions now ends with an "Interpretation history" panel (v69 `assumptions` history table). For one recorded moment it lists every fuel cost version the Site had recorded, newest first: earlier and latest versions, unpriced versions, the exact price version each one used, its own source label, a plain "the price changed; the measured result did not" where supported, and links to that exact fuel cost version's Financials view and its Finding. No amount on this panel is current. A recorded amount appears only where the server permits it, labelled "Recorded amount — historical, assumption-conditioned audit history" and "Not a current cost", beside the source label. Nothing is totalled. IDs sit only in each row's closed "How this was worked out" disclosure.

The default address `/sites/{site}/financials/assumptions` is not rewritten. The history read fixes the moment (database clock), and the price list is read at that exact string, so both lists describe one instant. An explicit `?recorded_at=` address reads both at that moment and keeps it through reload and paging (`history_after`, `history_limit`).

## Files materially changed

- Backend: `backend/assetops_backend/financials/consequence_history.py` (new service, cursor, fence, classification, dispositions); `financials/adapters/postgres_consequence_store.py` (`site_history`, read-only snapshot); `consequence_history_api.py` (new route); `financials/composition.py`; `main.py` (route included before the price-revision route).
- Frontend: `frontend/src/sites/ConsequenceHistory.tsx` (new panel); `SiteFinancials.tsx` (`SiteAssumptions` shared cutoff, L-R2 refusal, `data-price-recorded-cutoff`); `financialsClient.ts` (`getConsequenceHistory`, types, `basis_changed`); `shell/operatorSiteRoutes.ts` (`history_after`, `history_limit`); `ui/primitives.css`.
- Tests: `backend/tests/test_s4_consequence_history.py`, `backend/tests/test_s4_consequence_history_postgres.py`, `frontend/src/sites/__tests__/siteFinancials.test.tsx`.
- Tools: `tools/s408_assumption_history_walkthrough.py`, `tools/s408-assumption-history-evidence.mjs`, `tools/s402a-assumptions-evidence.mjs` (two new claims).
- Docs: task status, `tasks/W1-UX-mockup-fidelity.md` assumptions row, `.ai/ACTIVE_CONTEXT.md`, `.ai/CODE_STATE.md`.

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| 1. Route; server default cutoff returned; zoned explicit cutoff; repeatable-read snapshot; `(recorded_at DESC, id DESC)`; fence over all in-scope rows incl. off-page; cursor binds tenant/Site/cutoff/limit/last pair/fence; 409 restart; 400 tampered; limit+1; equal timestamps; late commit; post-cutoff exclusion | Met | `site_history`, `ConsequenceHistoryService.read`; unit `TestPaging`, Postgres `test_equal_timestamps_across_pages`, `test_interleaved_late_commit_refuses_page_two_and_page_one_reloads` (second connection holds an uncommitted row stamped before the cutoff during page one, commits, page two gets 409, page one reloads and includes it; a row stamped an hour after the cutoff stays excluded). Non-vacuity: disabling the fence comparison made both the unit and the Postgres late-commit tests fail; reverted with `git checkout`. |
| 1. Default view requests history first and passes its cutoff to the price read; explicit URL notice only for URL cutoffs; default URL unchanged; price no-cutoff `CURRENT` contract kept for other callers | Met | `SiteAssumptions`; frontend tests "reads prices at the history's exact cutoff string..." and "keeps an explicit cutoff..."; Postgres `test_price_read_reports_the_identical_cutoff_string` (identical strings incl. microseconds; default reload gives a new instant); browser evidence both widths. |
| 2. Row lineage: exact IDs, price link via stored link (never today's), assignment valid/recorded intervals, typed absence, unpriced rows kept, broken/foreign lineage typed | Met | `_row`; recorded close after the cutoff is not shown; unit `test_broken_or_foreign_price_link_is_typed_never_substituted`, `test_unpriced_version_is_listed...`; Postgres `test_versions_lineage_currentness_and_recorded_amounts`. |
| 3. `CURRENT_AT_CUTOFF` rule with FindingRevision `created_at` and skew; no current amount at any cutoff; label; closed source hides; no per-Finding `derive()` | Met | `classify`; unit `TestClassification` (incl. same-instant boundary and skewed `created_at`); Postgres `test_cutoff_boundaries_and_the_real_clock_skew` (real FindingRevision `created_at` is later than its consequence's `recorded_at`); `current_amount_shown: false` constant; `TestMoney`. |
| 4. Scope before lookup; foreign Site; closed source typed not empty; store failure unavailable; empty/loading/error/withheld states at 1440/390; plain default copy; exact links with contextual destination | Met | Route tests `TestRoute`; Postgres foreign Site/cursor; frontend states tests; browser evidence owner 44/44, closed 16/16, mixed 16/16 at 1440 and 390. |
| Walkthrough tool and captures; S4-02a walkthrough claims | Met | `prepare` 23/23 API checks PASS (270 s); captures listed below; S4-02a evidence adds "default address is not rewritten" and "identical cutoff" claims (not run in this slice; its walkthrough needs its own DBs). |

## Review Lows folded in

- L-R1: the cutoff is a string end to end. Server `instant()` emits the same `+00:00` microsecond form the price read echoes; the UI never parses it into `Date` for transport (only for display). Tests compare exact strings with sub-millisecond digits (`CUT = ...09:30:00.123456+00:00`; Postgres asserts `"."` survives and strings match).
- L-R2 (deliberate expectation changes): if the history read fails on the default view, the price list shows a plain refusal ("The moment to show this site's prices at could not be fixed..."), `data-financials-read="no-cutoff"`, and no price read is made; never a silent CURRENT list. Changed on purpose: `siteFinancials.test.tsx` default-view expectation `recordedAt: null` is now `recordedAt: CUT` after a history read with `{ recordedAt: null, after: null }` (comment in the test); the default view's `data-price-cutoff` is now `RECORDED_CUTOFF`, asserted in the new test.

## Checks run (final code revision `46dc42cb`)

- Backend focused: `pytest backend/tests/test_s4_consequence_history.py` 25 passed; `test_s4_consequence_history_postgres.py` 7 passed (private `assetops_s408_test`).
- Full backend suite: **not completed within the cap.** `pytest backend/tests -n 2 --dist loadfile --no-loadscope-reorder -q --junitxml=<scratchpad>/s408-junit.xml` on `46dc42cb`, private `assetops_s408_test`, keep-awake running, no other pytest process, 4.3 GB free at start. Capped at 1800 s (`timeout 1800`, the brief's 30-minute cap); it reached 63% (about 1,700 passing tests, no failure printed) and was stopped there, so `gw1` reported "node down: Not properly terminated" at the kill. No JUnit file was written; no zero-skip count is available. The Reviewer (or coordinator) needs one complete run; the shared Postgres was contended by other agents during this window. Leftover `assetops_s408_pt*` databases were dropped.
- Frontend: `npx.cmd tsc --noEmit` clean; full `npm.cmd test -- --run`: 72 files, 1704 tests passed, 144 s, no timeouts; `npm.cmd run build` succeeded.
- Guards: `tools/check-all.ps1` all 9 passed (architecture, navigation, agent workflow, registry, delivery, mock-gap, missing-claim, screen ledger); `node frontend/docs/architecture/check_v69_dependency_registry.cjs` "Registry valid: 240 nodes", exit 0. No writer added, so no rule-8 change.
- Walkthrough: `tools/s408_assumption_history_walkthrough.py prepare` 0 failed checks; evidence script owner 44/44, closed 16/16, mixed 16/16. Captures (1440 `desktop`, 390 `narrow`): `s408-default-*`, `s408-T1-*`, `s408-finding-financials-*`, `s408-closed-*`, `s408-mixed-*`, `s408-mock-assumptions-*` (v69). Layout: page and shell overflow 0 at both widths (measured on a non-empty list of 6+ rows). Databases dropped afterwards.

## Known deviations

1. Recorded-amount gates: shown only when the S3 source gate is open, the row is PRICED with an outward-rounded display, and that exact version's S4-05b block is a positive stored class. LR-01 money eligibility is not applied to these audit rows (as for pinned earlier versions on Finding Financials); it gates current money only. A reviewer may prefer it applied.
2. "Maintain the same cutoff through contextual Finding links": the Finding and fuel-cost links pin exact IDs, which are cutoff-independent; Finding Financials has no cutoff parameter, so it is not carried there. Paging and price links keep it.
3. Page size: a cursor is bound to its page size (packet), so the UI keeps `history_limit` in the address when one was given; the default size (25) adds nothing to the URL.
4. The Finding is named by its time window, not the stored title (the vocabulary guard rejects the raw title's wording; the Finding index uses a fixed label too).
5. S4-06 equal-start succession is exercised in the walkthrough (v5 at 2030-01-01) and by S4-06's own tests; this slice's Postgres tests do not repeat it.

## Residual risk

- The full backend suite has not completed on this revision (see Checks run); only focused/adjacent files and 63% of the suite ran.
- Per-row provenance resolution runs outside the history snapshot (one resolver call per row, up to 100), as the existing consequence read does.
- The default cutoff is the database clock; the FindingRevision `created_at` comparison uses the application clock as the packet specifies, so skew is classified by rule, not corrected.

## Owner steps (for the combined W1 walkthrough; non-developer)

Open PowerShell and run, one line at a time:

1. `cd C:\Users\assef\Bineyame\AssetOpsV1-review`
2. `$env:PYTHONPATH="backend;contracts;gateway;simulator"`
3. `.\.venv\Scripts\python.exe tools\s408_assumption_history_walkthrough.py prepare` (about 5 minutes; it ends with "0 failed checks")
4. `.\.venv\Scripts\python.exe tools\s408_assumption_history_walkthrough.py serve --case owner` (leave this window open)
5. In a second PowerShell window: `cd C:\Users\assef\Bineyame\AssetOpsV1-review\frontend`, then `$env:ASSETOPS_API_PORT="8968"; npm.cmd run dev -- --port 5468 --strictPort`
6. In a third window (same `cd` and `PYTHONPATH` as steps 1-2): `.\.venv\Scripts\python.exe tools\s408_assumption_history_walkthrough.py links` prints the exact addresses.

What to look for at `http://localhost:5468/sites/KOBO-001/financials/assumptions` (try a narrow window too):
- At the bottom, "Interpretation history": the site and the moment it was read at; the address bar does not change.
- Rows marked "Latest at this moment" and "Earlier version"; one says "The price changed; the measured result did not."
- Amounts only as "Recorded amount — historical, assumption-conditioned audit history. Not a current cost.", next to "Prepared example data" (or "Generated test data").
- An unpriced version says "No amount" and why.
- "Open this fuel cost version" opens that exact version on the Financials page; "Open the finding" opens its finding.
- Open the "Recorded at T1" address from `links`: fewer rows; reload keeps the moment. The T3 second-page address shows "Back to the newest versions".
- Closed source: stop step 4 (Ctrl+C), run `...walkthrough.py close-gate`, repeat step 4, reload: every version is listed with "Not shown: this site's source is closed". Then Ctrl+C and `...walkthrough.py open-gate`.
- Mixed source: stop step 4, run `...walkthrough.py serve --case mixed`, reload: amounts say "Not shown: the source of the readings behind this version is not confirmed" beside "Sources do not agree".
- When finished: Ctrl+C both servers, then `...walkthrough.py drop`.
