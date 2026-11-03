# Review packet CH-0: chain coherence check, L3 clone helper, tick stage timings

- Build sheet: `AssetOpsV1-plan2/.agent/build-sheet-CH-0.md` (Architect, 2026-11-03).
- Branch: `task/CH-0-coherence`, cut from main `7fffc8358` (QW-1/QW-2 merged). The sheet names the branch `task/CH-0-coherence-timings`; the dispatch named this one.
- Commits: `83401621b` (U3), `0e8fddde9` (U1/U2), `ad1acb67d` (route test via `?raw`), plus this packet's commit.
- User review: the sheet sets no `USER_REVIEW_REQUIRED`. This slice needs a fresh Reviewer only. Do not merge.

## Outcome

- `python tools/checks/chain_coherence.py collect|check` produces today's contradiction report. Each finding carries a rule id, Site, window, subject and bodies; `expected-today.json` maps each finding to a register issue and an owner slice.
- Every tick that selects Sites logs one `assetops.perf` line with per-stage `elapsed_ms`, `limit_ms` (from `TickLimits`), `share` and the stage child's `peak_rss_kb`.
- QW review L1 is closed for the tick. `scheduling.run tick` installs a stderr handler (`tick.enable_perf_log`), so the INFO line is actually emitted. Stdout still carries only the report.

## Pre-flight answers (no blocking questions; decisions below are for the Architect to confirm)

- **P1.** App registers 60 patterns, excluding `*` and `/`. That is 49 constants from `operatorSiteRoutes.ts`, the literal `/maintenance/requests/:caseId/*`, and 11 Lab routes from `simulatorLabRoutes()` (flag-gated, included).
  - The dynamic `path={path}` sources are inline arrays in `App.tsx:396-405,420,469,488,527`.
  - `FINDINGS_OPPORTUNITIES_PATH` is registered (`App.tsx:500-503`).
  - Because the inline arrays are not exported, the vitest test reads `App.tsx` as text through Vite `?raw`. Every `path=` form must be recognised, so a new form fails the test.
- **P2.** Estate actions rows have `action_id`, `source_finding_id`, `created_at` and `verification_outcome`. Domain index rows have `action_id` and `origin.finding_id`, but **no `created_at` and no verification outcome**. COH-3 therefore uses `raised_at`, falling back to `recorded_at`.
- **P3.** No backend constant maps outcome category to lens.
  - `lens_flags` comes from `estate/index.py:128-129`: COST when the consequence is PRICED, RISK when the mechanism is in `RISK_MECHANISMS`. OPPORTUNITY is never set.
  - The frontend cards link GROW_REVENUE→`/findings/opportunities`, PROTECT_ASSET→`/findings/risks` and OPTIMIZE_COST→`/financials` (`PortfolioOutcomes.tsx:201-241`).
  - I kept the sheet's `CATEGORY_LENS` as the screen reading the plan intends, which is exactly the I-21 contradiction. Its GROW_REVENUE entry overlaps COH-6 (I-06).
- **P4.** The names are as in the sheet. `state=all` and `lens=opportunities` are valid.
  - Outcome-summary accepts only `from`/`to`/`known_at`.
  - Findings, actions, portfolio and the domain index page by `cursor`/`next_cursor`.
  - Estate `from`/`to` must be UTC midnights, at most 31 days apart.
- **P5.** No file store is needed: the board, estate and domain reads come from Postgres. All 56 requests returned 200 in process from this worktree, with no `var/sites` copy.
- **P6.** `consequence`→`consequence_seconds`; `cold_consequence` and `ev_consequence`→`domain_consequence_seconds`. There are no other Site stages; `discover` is tick-level and not in `sites[]`.

## Acceptance (sheet §5)

| # | Item | Status |
|---|---|---|
| 1 | `pytest tools/checks/test_chain_coherence.py` passes in under 5 s with the §3.2 cases | PASS: 39 passed in 0.39 s. Covers `clean`, one bundle per rule (exactly one finding each), `--expect` new/expected/resolved, the matcher cases, the page merge, a non-200 page, COH-12 info, day windows, and clone refusals with the fixed source |
| 2 | vitest `chainScreenRoutes.test.ts` passes; a fake `<Route path="/x">` fails it | PASS: 2 passed. Mutation: adding `<Route path="/x" element={null} />` to `App.tsx` gave 1 failed (`"/x"` in the diff), reverted with `git checkout`. Re-proved on the final `?raw` version |
| 3 | Today's report and `expected-today.json` exist; `check --expect` exits 0; COH-1/2/5/6/7a present | PASS, see the table below. Every listed rule has findings |
| 4 | `test_ch0_tick_timing.py` passes | PASS: 8 passed (L0 via `run-host-tests.ps1`). Mutation: removing `enable_perf_log()` from `run.py` failed the CLI emission test, reverted |
| 5 | Existing tick tests pass | PASS: `test_s4_schedule_tick_postgres.py -m "not slow"` 6 passed, 1 deselected, 0 skipped. The non-Postgres importers `test_w402_mini_stage`, `test_w403_opportunity_stage`, `test_fix_cold_drain_stage` and `test_s4_schedule_install_gate` gave 42 passed |
| 6 | No response body change | PASS. No read path is in the diff; the backend change is limited to `scheduling/{tick,stages,run}.py`. The only change to the tick report is the extra stage key `peak_rss_kb` |
| 7 | Guards pass, including the new line | PASS: Architecture seams, Agent workflow and Navigation truthfulness each exit 0. The new check-all line is the L1 command and passes |

## Today's contradictions (`.agent/CH-0-today-report.json`, 61 findings; `expected-today.json`)

Source: clone `assetops_chainclone_ch0_test` of `assetops_polish_full_test`, migrated to head and **not ticked** (header `freshness: not ticked`). Story S = 2026-10-31. 56 requests, about 133 s in process. The clone was dropped after use.

| Rule | Count | Register | Owner | What |
|---|---|---|---|---|
| COH-1 | 12 | I-08 | CH-5a | Cold and EV board issue and `must_not_harm` hrefs, and summary `warnings[].evidence_refs` hrefs, are `/api/sites/<code>/{cold,ev}/findings/...` URLs |
| COH-1 | 22 | **new** | none (Architect) | Board `links.self` is the board's own API URL (`/api/sites/<code>/outcome-board?...`) on all 13 day boards and 9 summary-window boards. No register issue names it. It is probably a deliberate resource self-link, so the Architect should rule whether `self` is exempt. The rule was not weakened |
| COH-2 | 3 | I-03 | CH-2 | Kobo ACT-001 answers Finding 706d2f14, but its Portfolio row has `action_id: null` (week, S, month) |
| COH-2 | 2 | I-09 | DD-1 | Cold ACT-000002 (Finding 2505d188) and EV ACT-000003 (274196f4) have Portfolio rows with no `action_id` (month) |
| COH-5 | 3 | I-21 | CH-2 | Cold f9ed0fec and 2505d188 sit under OPTIMIZE_COST but have `lens_flags` `[RISK]`. EV 274196f4 sits under GROW_REVENUE but has `[RISK]` |
| COH-6 | 6 | I-06 | CH-4 | The Kobo boards (overuse 10-17, late 10-28, trial-before 10-31) show an OPPORTUNITY. For week, S and month, the Opportunities lens has no Kobo row and Portfolio `opportunity.state` is UNSUPPORTED |
| COH-7a | 10 | I-04 | CH-6 | Each summary mixes bases (week and month use DAY and LATEST_EVENT; S uses DAY, LATEST_EVENT and PERIOD). Seven Site windows differ from the requested window. In month, the Kobo Site window is 11-02, a day with no run |
| COH-8 | 3 | I-03 (+I-01 part) | CH-2 (+CH-3) | Kobo ACT-001 is VERIFIED, but its Portfolio row reads `verification_outcome: null` and its progress row has `origin_revision_selected: false` |
| COH-3 | 0 | (I-09) | DD-1 | **Not seen.** Domain ACT-002/003 have `raised_at` 2026-11-01 and 11-02 (build time), which is after every Cold/EV board window ends. So the "Action existed by the window end" condition never holds, and that is itself the I-09 symptom. Kobo ACT-001 is linked on its boards. Not forced |
| COH-4, COH-7b, COH-9a | 0 | none | | As the sheet expected |

Info (never failing):
- **COH-9b, 26 phrases (I-15), all Kobo:** "of the last 5 days" ×11, "of N well-observed days" ×7, and "of 31/30/28/24/17/10 days".
- **COH-12, 10 strings (DS-R1 item 4):** all Kobo ACT-001, "verified on example data" in `contributors[].text` and `earlier[].result_label`. `source_mode` is null because the board bodies state no `source_provenance` at those paths. Owner: CH-5a.

## Demo-shaped items (DS-R1, sheet §4b)

- **Hard-coded "example data" wording:** recorded by COH-12, not fixed. Owner CH-5a.
- **Cold/EV Actions recorded at build time:** recorded as COH-2 under `I-09` with owner `DD-1`. COH-3 cannot see them for the reason in the table.
- **Fixed opportunity claim:** recorded as COH-6 under `I-06` with owner `CH-4`.
- **U3 timing code:** holds no demo values. Limits are read from `TickLimits` via `STAGE_LIMIT_FIELDS`, which maps names only.
- **No rule was weakened to fit the data.** The single carve-out, `links.*_label`, is listed under deviations.

## Known deviations

1. **Branch name** follows the dispatch, not the sheet.
2. **COH-1 skips `links` keys ending `_label`.** `links.current_view_label: "Current view"` is display text, not a link (`LABEL_SUFFIX`).
3. **Rule sub-ids.** COH-7 reports `COH-7a`/`COH-7b`, COH-9 reports `COH-9a`, and the COH-5 subject is `<finding_id>:<lens>`.
4. **Day-window estate Findings** use the enclosing UTC-midnight window (`day_windows()["estate"]`), because the estate routes refuse non-midnight bounds such as Cold's `[16:00, 17:05)`. COH-4(b) and COH-5 read that body, restricted to the board's Site.
5. **COH-3** uses the domain index `raised_at` (P2).
6. **Files outside the sheet's list:**
   - `scheduling/run.py`: one call to `enable_perf_log()` for QW review L1.
   - `frontend/src/test/rawSource.d.ts`: a `*.tsx?raw` declaration so the route test typechecks.
7. **QW review L1, serve side, documented and not configured.** Under uvicorn, the QW-1 request lines (`perf.finish`) still have no handler, so they are not emitted. The fix is to call `assetops_backend.scheduling.tick.enable_perf_log()` at app start (for example in `host/lab_app.py`), or to pass a uvicorn `--log-config` that sets `assetops.perf` to INFO. Left to the coordinator, because it is a QW/serve file.
8. **"12 guards" search:** hits only in historical `.agent/` files (`build-sheet-POLISH.md:405,464,482,526`, `POLISH-PA-2a-packet.md:159`, `COV-PARTIAL-*`, `OUT-D-*`). There are none in `.ai/` or `backend/TESTING.md`. Nothing was edited.

## Checks run

- **L1:** `.venv python -m pytest tools/checks/test_chain_coherence.py -q -p no:cacheprovider`: 39 passed, 0.39 s.
- **L0:** `run-host-tests.ps1 -- backend/tests/test_ch0_tick_timing.py`: 8 passed.
- **Tick Postgres:** `run-host-tests.ps1 -- backend/tests/test_s4_schedule_tick_postgres.py -m "not slow"` on `assetops_test`: 6 passed, 1 deselected, 0 skipped, 107 s wall.
- **Pure tick and stage importers:** 42 passed (4 files).
- **Frontend:**
  - `npx vitest run src/__tests__/chainScreenRoutes.test.ts`: 2 passed.
  - `npx tsc --noEmit`: exit 0. The first version used `node:fs`, which failed typecheck; it was switched to `?raw`.
- **L3:** clone, migrate, collect, check and drop, as above.
- **Guards:** `powershell -NoProfile -File` for check-architecture, check-agent-workflow and check-navigation-truthfulness: all passed, with no policy override.
- **Not run (by the sheet):** full suites, full vitest, demo prepare, the deferred guards (estate self-tests, delivery, mock-gap, missing-claim, evidence width) and layout evidence. Layout evidence does not apply; this slice has no UI.

## Residual risk

- **`expected-today.json` is tied to this DB build.** Its subjects are Finding and Action UUIDs, and hrefs carrying `known_at`. A rebuilt polish DB, or DD-1's re-recorded Actions, produces new ids. The file must then be regenerated from a fresh report, not edited by hand. Its `basis` field says so.
- **HTTP `collect`** (`--base-url`) is written but untested against a live serve; no serve was available or allowed. The in-process path is proven.
- **COH-6 deduplication.** The rule dedupes per estate window and Site, so the board day that triggers each finding is only the first one seen.
- **Windows `peak_rss_kb`.** It uses `K32GetProcessMemoryInfo` and returns an int here. The POSIX path (`ru_maxrss`) is not exercised on this machine.

## Fix round 1 (review REVISE + Architect ruling CH0-R)

Commit `067299b6c` (on `9e444c6f8`).

| Item | Change | Proof (mutate, fail, revert) |
|---|---|---|
| M1 | New rule `COH-0` (first in `RULES`): one failing finding per request name whose status is not 200, and per paged run cut off at `MAX_PAGES` with a cursor set (`Collector` writes `truncated: true` on the last request; `Bundle` reads it). Test at the old `:123` now expects `COH-0`; cut-off test and a `Collector` cut-off test added | `if b.status != 200` -> `if False`: the non-200 test fails. `if b.truncated` -> `if False`: the cut-off test fails |
| L1 | Failing bundles `coh7b_state`, `coh4b_board_finding`, `coh6_opportunity_missing_row` (each exactly one finding) | COH-7b comparison disabled: `coh7b_state` fails |
| L2 | `chain_clone.create` prints `masked(url)` (`user:***@`); test on `masked` | The print path itself is not unit-tested (needs a DB); the clone run below shows `assetops:***@` |
| L3 | Route-sync regex accepts `path='...'`; unrecognised forms still throw | Vitest 2 passed. No new test: no single-quoted route exists in `App.tsx` to exercise it |
| L4 | `--known-at` is added to every collected request, boards included | Restricting it to `/api/estate` again fails `test_known_at_reaches_the_board_requests_too` |
| R1 | Only a body's root `links.self`, equal to the body's own request path and query (parsed, order-insensitive), is exempt (`is_own_self_link`). 22 self-link entries removed from `expected-today.json` (61 -> 39). Tests: equal root exempt; non-equal root, other-site root, nested equal self all stay COH-1 | Exempting any `*.self` fails the nested test; exempting nothing fails the root test (and nested) |
| R3 | `perf.enable_log()` (idempotent, named handler, `propagate=False`); `tick.enable_perf_log` delegates to it; `host/lab_app.build_app` calls it once. Tests: idempotent, one emission, nothing through a root handler; `lab_app` source calls it once | `propagate=False` removed: the idempotency test fails (double emission). Handler reuse removed: it and the tick CLI test fail |

### Checks
- L1+L0: `pytest tools/checks/test_chain_coherence.py backend/tests/test_ch0_tick_timing.py`: 59 passed, 1.7 s. `npx tsc --noEmit`: exit 0. `chainScreenRoutes.test.ts`: 2 passed.
- Fresh clone `fix1` (`chain_clone create`, no migrate needed: head matched), in-process `collect` (56 requests, all 200), `check --expect`, `drop`: COH-0 0, COH-1 20 (12 expected), COH-2 5, COH-5 3, COH-6 6, COH-7 10, COH-8 3, others 0. The report shows **0 resolved and 8 unexpected**, not 0 (see below).

### Open for the Architect (ruling needed)
The 8 unexpected findings are all Kobo day boards (`day:kobo:*`), the Kobo members of the 22 removed self-links. The collector reads Kobo boards with `?date=D`, while the body's `links.self` is `...?from=D&to=D+1`. Under the strict CH0-R rule (equal to the body's own request path and query) these are not exempt, so they stay COH-1. Two ways to close it, neither taken here:
1. Read Kobo day boards by `from`/`to` (one UTC day, which the mini board accepts), so the request equals the self link. This changes the collected request.
2. Widen the exemption so `date=D` equals `from=D&to=D+1`. This widens the ruling.
Cold and EV boards already use `from`/`to` and are exempt.
