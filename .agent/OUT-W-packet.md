# OUT-W review packet · estate event windows for cold and EV Sites

Task `tasks/OUT-W-estate-event-windows.md`; contract `AssetOpsV1-plan2/.agent/build-sheet-OUT-W.md`. Branch
`task/OUT-W-estate-event-windows` from main `833e7c95`. Review range `git diff 833e7c95..HEAD -- ':!.agent'`.
Commits: f99c3626 W1 · bb556587 W2 (+ W1 review L1) · ca73bd55 W3 code/tests (+ W2 review L1/L2) · 315ef5aa register ·
0e0ce581 closeout docs. USER_REVIEW_REQUIRED: false for merge (fresh independent review gates merge).

## Outcome delivered

The estate outcome summary now judges each cold or EV Site on its latest assessed event inside the requested period. This is
owner option A. If the Site has no event, or the window choice fails, it is judged on the period. A mini-grid Site is
unchanged. On real w502 data, GreenHarvest's Cost cell reads Needs attention on the day and on the week, with one repeat
warning, and its Portfolio cell opens the Site on that event window.

## Units

- **W1** `estate/evidence_money.py` `site_selected_windows`. The sheet's code as written. Per-unit review ACCEPT, and L1 is folded in
  (a STALE_SOURCE and a PENDING_RECOMPUTE window are still returned).
- **W2** `site_outcomes/read.py`:
  - adds `WINDOW_BASIS_*`, `latest_window` and `_event_window`;
  - `summary()` picks the window per Site and adds `window` and `window_basis` (both None on a failed board);
  - `_overview_href(site, window, known_at)` puts the window in the link only for LATEST_EVENT, and adds `known_at` only when the request had one.

  Per-unit review ACCEPT, with these items folded in:
  - L1: `LOG = logging.getLogger(__name__)` logs `"window choice for <code> fell back to the period (<ExceptionType>)"` and never
    the message. It is silent for `PortUnavailable` (no estate configured). A caplog test covers it.
  - L2: the tie test puts the earlier start first.
  - Residual risk: the parametrized fallback test now includes an `EstateRefusal("ESTATE_SELECTION_INCONSISTENT")` estate.
- **W3**
  - Real-data tests: P-C1 is now asserted rather than branched.
  - The EV test follows Architect ruling (a).
  - Frontend type and fixtures: no component change.
  - Captures, and the register.

## Acceptance (§5)

1. **Met.** `test_out_w1_selected_windows.py` (9 tests) proves:
   - the same `selected_windows` arguments as `coverage._windowed`, i.e. `(t, sid, domain, from, to, cutoff, k)`;
   - deduplicated and ascending results, with spans that are not forward or that exceed 31 days dropped;
   - [] for no cutoff or mini, None for an unknown Site;
   - INVALID_KNOWN_AT and INVALID_WINDOW refusals.
2. **Met.** `test_out_w2_summary_window.py` (14 tests) covers:
   - the latest event wins, and a tie on the end goes to the later start;
   - the event href is exact;
   - the period fallback for each of [], None, RuntimeError, EstateRefusal and an unconfigured estate;
   - mini untouched;
   - `known_at` passed through and never invented;
   - a failed board gives `window` and `window_basis` None with 4 UNKNOWN rows;
   - warnings and counts come from the event board.
3. **Met.** In `test_out_c3_repeat_visits_postgres.py` the P-C1 record reads:

   | Period | Basis | Window | Cost (lead) | REPEATED warnings | Summary GET | Windows read |
   |---|---|---|---|---|---|---|
   | Day `[2026-10-29, 10-30)` | LATEST_EVENT | 16:00-17:05Z (the W5-01 window, `is_w501` true) | NEEDS_ATTENTION (CC-3) | 1 | 1.113 s | 0.084 s |
   | Week `[10-23, 10-30)` | LATEST_EVENT | same | same | 1 | 1.047 s | 0.087 s |

   The href is `/sites/COLD-LAB-001?from=2026-10-29T16%3A00%3A00Z&to=2026-10-29T17%3A05%3A00Z`, with no `known_at`, and
   `money_hits == []`. The windows read adds under 0.1 s per Site, well inside the 2 s limit in §7.

   The captures show the cell opens the Site on that window, where the board reads the same Cost state.
4. **Partly met (ruling (a)).**
   - **8 Oct:** Depot is PERIOD on `[10-08, 10-09)` with href `/sites/EV-LAB-001/ev`.
   - **6 Oct:** the summary refuses **409 ESTATE_SELECTION_INCONSISTENT** before any Site is composed. The route's `estate.scope`
     fails because "Finding 0ccdbf27-... has two selected revisions at one cutoff". This is pre-existing: OUT-C's board on E
     already recorded `evidence_readiness: EstateRefusal: ESTATE_SELECTION_INCONSISTENT`.
   - The test asserts the 409 and carries a comment saying it flips to LATEST_EVENT on window E when FIX-01 lands.
   - R577 is open.
5. **Met.** `test_out_b4_read.py` is unchanged and green. The B/C focused set and `test_out_b4_board_postgres.py` are green. The fast tier is below.
6. **Met.** R575 is resolved, R576 is standing (it names the approved meaning), R577 is open, and the captures are recorded.

## Checks run

- **Focused backend, real Postgres:**
  - Unit set (w1, w2, b4_read, b4_route, b4_window, b4_imports, c2_board): 60 passed.
  - Adjacent estate unit tests: 94 passed.
  - c3 + b4_board_postgres: 6 passed. c4: 1 passed.
- **Frontend:**
  - `tsc --noEmit` clean.
  - estatePortfolio: 34 passed.
  - estatePortfolioRoutes + estateRoots + globalMaintenance: 48 passed.
  - Full `npx vitest run`: **3526 passed, 3 failed** (only the known `w1f4VerificationStructure` tests), 144 files, 342 s. The log is
    `.agent/OUT-W-vitest-full.log`.
- **Backend `tools\run-backend-suite-in-container.ps1 -Tier fast`** (coordinator's choice in place of the 175-file selection): started 2026-10-31 00:37:32 +03:00 at head 0e0ce581, 4 workers, postgres-test, cache on; wall 3516 s (58m40s); **4362 passed, 0 failed**; JUnit `errors=0 failures=0 skipped=0 tests=4362` (no `<skipped`); exit 0; run dir `var/test-results/OPS-03/20261031-003732-df5e04`; log `.agent/OUT-W-backend-fast.log`.
- **check-all** (override-free, `ASSETOPS_GUARD_PYTHON` = plan2 venv): 11/11 at W1 and at W2. Closeout run: 11/11 (after the fast tier, head 0e0ce581).

## Captures (`.agent/OUT-W-captures/`)

The tool is `capture-outw.mjs`: OUT-C's CDP tool plus `click`, which follows a Portfolio cell and records the Site board's
request URLs. Targets are in `targets.json` and `targets-maint.json`, evidence in `shots/raw-evidence.json`, and logs in `logs/`.

- **Producer:** w502 positive, DB `w502b_positive_outw_test`, API 8971 / Vite 5471. The DB is dropped afterwards, and the servers
  were stopped by PID.
- **Results:** 62/62 claims passed, plus 10/10 on the maintenance rerun. Every app shot has its v70 pair at 1440 and 390, and no
  page overflows.

| Target | v70 mock | Observed |
|---|---|---|
| `portfolio-day` / `portfolio-week` | portfolio | The "Outcomes across the estate" Cold replay lab Cost cell reads Needs attention. The early-warning list under the ranked table lists "Risk · Repeated maintenance without a result" (3 items). The pulse reads "3 warnings not yet priced". |
| `*-click` | cold | The Cost cell click opens `/sites/COLD-LAB-001?from=2026-10-29T16%3A00%3A00Z&to=2026-10-29T17%3A05%3A00Z`. The Site board requested exactly that `from`/`to`, which confirms the pre-flight item. The Cost row reads "Needs attention · 3 repair visits in 60 days without a result". |
| `findings-cost-day` | findings | The Cost lens lists "Risk · Repeated maintenance without a result" (screenshot; the measure's selector does not match this list). |
| `maintenance` | maintenance | Card 4 "Repeat visits without a result" reads 1, "generator-1 · 3 visits, automatic start failure still open". |

**Capture notes:**
- The w502 `serve` command does not set `ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` or `ASSETOPS_WORK_CURSOR_KEY_HEX`. Without them,
  Portfolio and Maintenance return 503, so I set both in the environment and re-served.
- Card 4 renders "Not assessed" while its summary is loading, which is pre-existing OUT-C behaviour. The maintenance target
  waits for the loaded state.

## Known deviations

- Acceptance 4 is partly met; see above (ruling (a), R577, FIX-01).
- W2 L1 adds the backend's first module logger, approved by the coordinator. It logs the Site code and exception type only.
- `test_out_c4_ev_warnings_postgres.py` now restores `ev.compose` after the board-on-E read. Otherwise the summary's own EV boards
  (8 Oct) overwrite the spied availability, and the existing connector assertion compares against the wrong read.

## Residual risk

- One extra estate snapshot per cold or EV Site per summary. It measured 0.08 s on w502; larger estates scale linearly (serially, per B-Q8).
- While the R577 inconsistency lasts on a day, the whole estate summary refuses 409 for that day. This is pre-existing and not caused by OUT-W.
- Card 4's loading state reads "Not assessed", which is pre-existing.

## Review focus

- `read.py` `summary()`: the window choice never fails or empties a Site, and the href is built only on LATEST_EVENT.
- No edits outside the sheet's file list. The schema version is unchanged.
