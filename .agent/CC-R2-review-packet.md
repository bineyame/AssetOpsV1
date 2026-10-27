# CC-R2 review packet: Portfolio placement (D5) and the estate producer case

Task `tasks/CC-R2-placement.md`. Branch `task/CC-R2-placement`, branched from CC-R1 head `71aa1fea`. The contract is
`.agent/build-spec-commercial-2026-10-27.md` "CC-R2", with CC-R1-Q1/Q2 and Appendix C D5 as amended. Owner Q11:
the MG-C stand-in is kept. Questions Q1-Q4 are **ruled** (Architect, 2026-10-28, `.agent/CC-R2-questions.md`
"Rulings") and applied in `4e986966`.

PYTHONPATH (PowerShell):
```
$env:PYTHONPATH = "C:\Users\assef\Bineyame\AssetOpsV1-cc2\backend;C:\Users\assef\Bineyame\AssetOpsV1-cc2\contracts;C:\Users\assef\Bineyame\AssetOpsV1-cc2\simulator;C:\Users\assef\Bineyame\AssetOpsV1-cc2\gateway;C:\Users\assef\Bineyame\AssetOpsV1-cc2\host;C:\Users\assef\Bineyame\AssetOpsV1-cc2"
```
`assetops_backend.__file__` resolved to `AssetOpsV1-cc2\backend\assetops_backend\__init__.py`.

## Commits

- `1407a4b0`: the CC-R1 review Lows.
  - L1: three `double_count_violations(portfolio, financials)` asserts in `test_w303_portfolio_comparison_postgres.py`.
  - L2: the packet text.
  - L3: the R500 cell names the verdict.
  - L4: the import space.
  - L5: negatives showing that the cold and EV Financials frames have no "Open the recommendation" link.
- `0bcb7f16`: the backend, the tests and the s602b `estate` case.
- `41f1507a`: the frontend and register R502.
- `39a669a4`: the task file, `.ai` and this packet.
- `4e986966`: the Q1-Q4 rulings.
  - Q1: the confidence words become "Supported Finding", "Unconfirmed Finding", "Generated test data source" and "Prepared example data source". Both new guarded-word tests were proven to fail on a planted word and then reverted.
  - Q2: `test_ev_interruption_placement` (expects ACT_NOW).
  - Q3: the subtitle and `PRIORITY_BOTTOM_LINE`, with MOCK DEVIATION comments.
  - Q4: `estate_assertions` returns `rows` keys, and `portfolioSuite` is added to `s602b-verification-evidence.mjs`.
- Packet update: this text.

## CC-00 facts (pinned from code)

These come from a tier-2 probe on `assetops_cc2_test`, `build_portfolio_fixture`, window 10-06.

- The W3-03 fixture has **two** cold members, `COLD_EXCURSION` and `COLD_START_FAILURE`.
  - Both have `episode_end` = null, and neither has an Action.
  - Both are therefore ACT_NOW / `EPISODE_OPEN` + `NO_ACTION_RECORDED`, pinned unconditionally.
- **The fixture has no EV member row.** EV `complete` selects no EV Finding, so the EV placement assertion is open (Q2).
- KOBO-001 W1 has a closed episode, a PRICED consequence and a `SINGLE_LINE` group, so it is COMPARE_VALUE / `PRICED_SINGLE`.
- The w403 minimum ELIGIBLE lower headroom is a CC-D1 fact, already in the CC-R1 packet. It is not part of R2.

## Outcome delivered

- **`estate/placement.py`** (pure):
  - It implements the six rules in the spec order: Monitor runs before Compare (Q-C6).
  - It carries the 20 reason texts. `VERIFIED_WATCH_RETURN` = "Change verified on test data; watch for a return".
  - It sets confidence and its reasons from row facts. Site coverage adds text only (R5.6).
  - `{other}` = "Finding " + the first 8 characters.
- **Row facts:**
  - `f.mechanism` is added to the `_index_snapshot` head SELECT.
  - One batched `finding.mechanism` SELECT runs per cold or EV window read.
  - Mini rows carry recurrence, revision and transition facts through `.get`.
  - The RISK lens flag is set for the cold and EV mechanisms, on both the Findings root and the Portfolio.
- **Portfolio:**
  - Each row carries `placement` (`policy_version`, `group`, `group_rank`, `reasons`), `confidence` and `confidence_reasons`. `priority` stays null.
  - `line_group` comes from the same call's `compare()` groups, with no query.
  - The six-part marker, `order_key` and `PORTFOLIO_ORDER` are verbatim.
  - `summary.placement_counts` counts over `members`. It is null unless F is COMPLETE or EMPTY; EMPTY gives zeros.
- **Cursor:**
  - A six-part marker is accepted.
  - A five-part marker, a bool, a string or float rank, and a rank of 0 or 6 are each refused as INVALID_CURSOR.
  - `v` and the MAC are unchanged.
- **Producer case `estate`** (`tools/s602b_test_scoped_cases.py`, walkthrough `CASES`):
  - Steps: F01, F02, F03, F05 up to its UNCONFIRMED match (each match is checked with `check`), diesel price v1, then the `withdrawn` steps up to the first VERIFIED.
  - It then asserts on `GET /api/estate/portfolio?...` through `TestClient(lab_app.app)`, with the Action clock pinned. `serve` and the build share one `pinned_app`.
  - The three placements, the invariant, "no numeric priority" and the source-not-UNKNOWN/MIXED Stop are all asserted. Any failure exits non-zero before `case-estate.json` is written.
- **Frontend (`EstatePortfolio.tsx`):**
  - The "Priority" head becomes "Placement".
  - Each Placement cell shows the bold group label and the reason texts joined by " · ".
  - Each Confidence cell shows the words with the reasons joined by " · ".
  - A group heading row (`tr.placement-group`, `th colSpan=6 scope=colgroup`, " · n" from `placement_counts`) appears once per group, including across loaded pages.
  - `<details>` "How placement works" holds the five lines and the footer, verbatim.

## Files materially changed

- Backend:
  - `estate/placement.py` (new), `estate/portfolio.py`, `estate/scope.py`, `estate/index.py`, `estate/coverage.py`.
  - `estate/adapters/postgres_estate_read.py`, `analytics/adapters/postgres_finding_store.py`.
- Tools: `tools/s602b_test_scoped_cases.py`, `tools/s602b_verification_walkthrough.py`.
- Frontend:
  - `estate/EstatePortfolio.tsx`, `estate/portfolioWords.ts`, `estate/estateClient.ts`, `estate/estatePortfolio.css`.
  - The tests `estatePortfolio.test.tsx` and `portfolioFixtures.ts`.
- Tests:
  - New: `test_cc_placement.py` (40 cases) and `test_cc_placement_postgres.py`.
  - Updated:
    - `test_w303_estate_cursor.py`: the five-part fixtures were rewritten to six-part by design.
    - `test_w303_portfolio_api.py`: the order prefix, `placement_counts`, and a marker length of 6.
    - `test_w301_estate_index_postgres.py:199,204`: cold `lens_flags == ["RISK"]`, and the risks lens now returns the cold rows. This is the specified R5.5 change. `:548-563` needed no change, because those rows are mini-grid `GENERATOR_SUPPORT_CANDIDATE` and pass as before.
- Register: `.agent/mock-departure-register.md` R502, with the Appendix C deviation text verbatim.

## Acceptance criteria

| Gate | Status |
|---|---|
| One pure case per rule and per reason code | Met. `test_cc_placement.py` has the parametrised rules, plus `test_every_reason_code_is_reachable`, which hits all 20 codes. |
| MIXED + PRICED goes to NEEDS_INVESTIGATION; Verified + PRICED goes to MONITOR | Met (pure). |
| A six-part marker passes and a five-part marker fails | Met (pure `_marker_ok` and the signed-cursor mutations). |
| Producer 1, the s602b `estate` assertions | **Built, not run.** The brief allows DB runs only on `*_test`; s602b refuses `*_test`, and the coordinator has since paused DB runs. This is owed. |
| Producer 2: cold pinned, `lens=risks`, `limit=2` paging, invariant | Met on tier 2. |
| Producer 2: EV row (ruled Q2: the `interrupted` chain gives ACT_NOW) | **Written, not run** (DB hold): `test_cc_placement_postgres.py::test_ev_interruption_placement`. |
| Browser: group headings and reason lines (`settledScreen`) | Met. There are 3 new tests in `estatePortfolio.test.tsx`. |
| Stop conditions | None hit on tier 2. The producer-1 Stops are asserted in the tool but not yet run. |
| Register row for the new panel | R502 added. |

## Checks run

- After the rulings: tier 1 backend **441 passed, 15 skipped**; frontend `src/estate` **5 files, 64 passed**; `tsc` clean; both guards passed.
- Tier 1, backend (before the rulings): every non-Postgres `test_w30*`, `test_cc_*`, `test_s4_finding*` and `test_w40*` file. Result: **440 passed, 15 skipped**.
  - A Postgres module collected without a URL raises a `NameError`. That is pre-existing (e.g. `test_w301_w1_money_snapshot_helpers_postgres.py`) and untouched.
- Tier 2, one run on my own DB:
  - Command: `ASSETOPS_TEST_DATABASE_URL=.../assetops_cc2_test pytest tests/test_cc_placement_postgres.py tests/test_w301_estate_index_postgres.py tests/test_w303_portfolio_fixture_postgres.py tests/test_w303_portfolio_comparison_postgres.py`.
  - Revision `0bcb7f16`. Result: **27 passed, 0 skipped, 0 failed**, wall time 14:28.
  - Before it, there was one short probe run (97 s) to read the CC-00 facts. The probe file was deleted.
  - I created DB `assetops_cc2_test`; it is still present.
  - There were no DB runs after the coordinator's pause.
- Frontend:
  - `vitest src/estate`: 5 files, 63 passed.
  - Adjacent tests (`s404SiteFindingIndex`, `coldFindingIndex`, `operatorRouteFrames`): 69 passed.
  - The R1 L5 files (`coldSiteViews`, `evSiteMoneyRoutes`): 93 passed.
  - `tsc --noEmit` is clean, and `npm run build` built in 17 s.
- Guards:
  - `tools/check-architecture.ps1` passed. Its Rule 8 needs `ASSETOPS_GUARD_PYTHON` pointed at the plan2 venv; without it, it fails with "no Python interpreter".
  - `tools/check-agent-workflow.ps1` passed.
  - Neither was run with any policy override.
- Not run: full suites, browser capture, the s602b `estate` producer.

## Known deviations

- The `estate` case sets a random Portfolio cursor key in its own process when none is set (`_cursor_key`). This follows the post-W6 `start_apis.ps1` pattern, because the route returns 503 without a key. It is never a committed value.
- `line_groups` takes the first group per Finding revision. A mini revision has exactly one line today, so the choice never matters.

## Residual risk

- Producer 1 has not been run. The F05 runtime control (120 from 10-21) and the price publication could change F01's verdict or a row's source class. The tool asserts this and exits non-zero, but nobody has seen it pass.
- The ruled texts change `confidence_reasons` in the earlier tier-2 run. `test_cc_placement_postgres.py` has not been re-run with them (DB hold).

## Owed evidence

- A tier-2 re-run of `test_cc_placement_postgres.py` (both tests, including the new EV test) on `assetops_cc2_test`.

- s602b `estate` build plus assertions on `assetops_s602b_audit_cc_estate` (walkthrough `prepare`), once the DB pause lifts.
- Tier-3 capture of the estate Portfolio page (group headings, reason lines, `noOverflow` on the 6-column table with heading rows). The `portfolioSuite` claims are now in `s602b-verification-evidence.mjs` (Q4). Run the ruling's prepare, capture and drop steps; the coordinator runs the capture. **layout evidence: not run** (no browser runs allowed). The group-heading row layout and the Placement column width (9%) are unverified.

## User-review focus

`USER_REVIEW_REQUIRED`: the merge needs a fresh Claude review ACCEPT. The owner sees R502 and the placement groups in
the walkthrough. All four questions are ruled.

## Fix round: Architect rulings CC-R2-F1..F4 (applied)
- F1: estate window `from=2026-10-03..to=2026-11-03` (31 days) in `tools/s602b_test_scoped_cases.py` and `s602b-verification-evidence.mjs`.
- F2: `pinned_app` wraps `read` on `PostgresEstateRead` and `PostgresEvidenceMoneyRead` so `read_at == pinned_at` (`_pin_read_clock`); no product change. `serve` banner: "Action clock and estate read time pinned at <pinned_at>". Not run against a DB (hold).
- F3: `MECHANISM_WORDS`/`mechanismWords` in `frontend/src/estate/portfolioWords.ts` (MOCK DEVIATION comment); GENERATOR_SUPPORT_CANDIDATE reads "Possible extended generator support" (Architect re-ruling: "candidate" is a guarded word). New test `showsCustomerMechanismWordsNotRawCodes` (fails on raw codes); `.mjs` claim 4 adds the raw-code token check.
- F4: reason text "No end is recorded for this episode" in `placement.py` and the test literals.
- Checks: backend tier 1 (30 non-Postgres files) 441 passed, 15 skipped; `src/estate` 5 files, 65 passed; `tsc` clean; both guards passed. Tier 2, producer, capture: not run (hold).

## Heavy evidence run (2026-10-28, after the DB hold lifted, at `b9f88ed4`)

1. **Tier 2:** `test_cc_placement_postgres.py` on `assetops_cc2_test` took 93.5 s. Result: **1 passed, 1 failed**.
   - The W3-03 fixture test passed. That includes the F2 read-time pin path, which goes through `Portfolio`.
   - `test_ev_interruption_placement` stopped at the ruling's Stop: `episode_end` is `2026-10-06T08:16:00Z`, not
     null. The source is REGISTERED_SIMULATION. The test is unchanged. See `.agent/CC-R2-questions.md` CC-R2-Q5.
2. **Producer:** `s602b_verification_walkthrough.py --db assetops_s602b_audit_cc --work var/s602b_cc prepare`, run
   unmodified, with code from `b9f88ed4`.
   - The replay was VERIFIED, and the four existing cases built.
   - Case `estate` failed: freeze 409 `VERIFICATION_FOUNDATION_NOT_COMPARABLE`. A diagnostic copy with the F05
     steps skipped gave 201, so the cause is F05's backdated runtime control. This is the spec Stop. See CC-R2-Q6.
   - The DBs and the work folder were removed with the tool's `drop`.
3. **Capture: not run.** `prepare` did not finish, so no `cases.json` exists. **layout evidence: not run** (blocked
   by Q6). No Vite or API process was started.
