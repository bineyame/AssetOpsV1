# CC-R2 review (fresh Claude reviewer, 2026-10-28)

Branch `task/CC-R2-placement` at `78ddc60e`, diffed against `71aa1fea` (CC-R1 head, on main). Scope: CC-R2 and the
CC-R1 Low fixes in `1407a4b0`. Authority: build spec "CC-R2" with CC-R1-Q1/Q2 and CC-R2-Q1..Q4 rulings, Appendix C
D5 as amended, owner Q11, v69 `#/portfolio`. Tier 0-1 only (no DB, no browser, no full suite).

## Verdict: ACCEPT-WITH-FIXES

The pure placement, confidence, cursor, lens and frontend grouping match the spec and the rulings, and the checks
pass. The `estate` producer case cannot pass as designed: its window is refused, and its read time comes before
every row it asserts on (H1, H2). One customer-visible regression is a new raw enum in the Portfolio row (M1). Fix
H1, H2 and M1 on the branch. M2 is a spec-level honesty question for the Architect. It is not an Implementer gap.

## Checks run (by me, at 78ddc60e)

- Backend tier 1: the 30 non-Postgres `test_w30*`, `test_cc_*`, `test_s4_finding*` and `test_w40*` files, run with
  the Lane C PYTHONPATH (`-cc2`) and no test DB URL. Result: **441 passed, 15 skipped** (8.7 s).
  `assetops_backend.__file__` resolved to `AssetOpsV1-cc2\backend`.
- Frontend: `npx.cmd vitest run src/estate src/sites/__tests__/coldSiteViews.test.tsx
  src/sites/__tests__/evSiteMoneyRoutes.test.tsx`. Result: **7 files, 157 passed** (estate 64 + R1 L5 files 93).
  It ran here, despite the usual esbuild sandbox note.
- `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-architecture.ps1`, with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv: passed. `tools/check-agent-workflow.ps1`: passed. Both
  were run directly, with no policy override.
- `py_compile` passed on both s602b Python tools. `node --check tools/s602b-verification-evidence.mjs` passed.
- Pure probe: `scope.parse_request("portfolio", from=2026-10-01, to=2026-11-03)` gives **EstateRefusal
  INVALID_WINDOW**. `from=2026-10-03` with the same `to` is accepted.
- Not run (owed, see the last section): `test_cc_placement_postgres.py` (both tests), the s602b `estate` build,
  the Portfolio capture, `npm run build`, and the full suites.

## Findings

### High

**H1. The `estate` case window is refused (INVALID_WINDOW), so Producer 1 and the capture can never pass.**
- `tools/s602b_test_scoped_cases.py:51`: `ESTATE_PORTFOLIO = ...from=2026-10-01T00:00:00Z&to=2026-11-03T00:00:00Z`.
  The same window appears at `tools/s602b-verification-evidence.mjs:293`.
- That window is 33 days. `estate/scope.py:21,121` allows at most 31 (`MAX_DAYS`), and I confirmed the refusal with
  `parse_request`.
- `estate_assertions` will exit with "Portfolio read 422" before `case-estate.json` is written. The literal comes
  from the build spec "Producer" 1 and the Q4 ruling, so this is a spec defect that the build carried through.
- Fix: choose a window of 31 days or less that holds F01 (10-06), F02 (10-08), F03 (10-11) and F05 (10-21), for
  example `2026-10-03` to `2026-11-03`. Ask the Architect to amend the spec and Q4 literals, then change both
  files.

**H2. The Portfolio read time comes before every row the `estate` case asserts on.**
- The S4/S6 runners stamp `created_at` and the selection and Action times from fake clocks. These are
  `SETUP_AT = 2026-10-29T12:00Z` (`backend/tests/test_s4_finding_store_postgres.py:48`), the step `decided` values
  from 2026-10-30 onward, and the evaluation at `CLOSED + 1h = 2026-11-02T12:00Z`.
- The estate snapshot takes `read_at = SELECT now()` (`estate/adapters/postgres_estate_read.py:90`) and uses it as
  the cutoff `k` (`estate/index.py:193-197`). The mini head SELECT then filters `r.created_at <= :k`
  (`postgres_finding_store.py:_index_snapshot`), and `known_at` may not be later than the read time.
- `pinned_app` pins only the Action service clock (`s602b_test_scoped_cases.py:pinned_app`). The machine clock now
  reads 2026-10-27 UTC.
- So any run before about 2026-11-02T12:01Z will see no KOBO-001 Finding rows. F01, F03 and F05 would then each
  report "0 matching rows", and the served Portfolio page would be empty for the capture as well.
- I traced this in code and did not run it. The tool fails closed, so it cannot produce false evidence, but the
  owed run cannot pass on this design.
- Fix: in a test-scoped way, pin the estate snapshot `read_at` to `spec["pinned_at"]` in `pinned_app`, so that it
  covers both `build` and `serve` (for example, wrap `PostgresEstateRead.read` so that the `EstateSnapshot` gets
  the pinned instant). Alternatively, the Architect can rule that the case runs only after `pinned_at`. In either
  case, record it in the packet.

### Medium

**M1. The Portfolio Finding cell now shows raw mechanism codes.**
- The row is rendered at `frontend/src/estate/EstatePortfolio.tsx:199` as ``Finding {site_code} · {finding_id} ·
  {row.mechanism ?? "Mechanism not recorded"}``.
- Before CC-R2, `mechanism` was always null on the wire. `estate/coverage.py:154,266` now carry the stored value,
  so every live row will show `GENERATOR_SUPPORT_CANDIDATE`, `COLD_EXCURSION`, `COLD_START_FAILURE` or
  `EV_INTERRUPTION`.
- These are system codes in a client-facing view, which breaks the standing plain-language rule. v69
  `#/portfolio` shows plain mechanism text, for example "Automatic start failed; cooling interrupted".
- No test catches it, for two reasons:
  - The KOBO fixture still has `mechanism: null` (`portfolioFixtures.ts:45`), which no longer matches the wire.
  - The capture's claim 4 only scans for claim, simulat and scenario.
- Fix: map the four stored codes to customer words, falling back to "Mechanism not recorded" for any other value.
  The Architect should rule the words, since Implementers do not design copy. Then:
  - set the fixture to `GENERATOR_SUPPORT_CANDIDATE`;
  - assert the rendered words in `estatePortfolio.test.tsx`;
  - assert in the test that no `[A-Z]+_[A-Z_]+` token appears in the priority panel text.

**M2 (spec-level, for the Architect). "The episode is still open" is not a supported statement for some cold and EV rows.**
- Q-C21 defines open as `episode_end` null, and the code follows it. But null does not always mean open:
  - `COLD_START_FAILURE` revisions never store an end (`postgres_finding_store.py:672-673` sets only `start`), so
    every backup start failure will read "still open" and land in ACT_NOW permanently.
  - The W2-05b `interrupted` session has an observed `abort_at` with `end_at` null
    (`test_w205b_ev_replay_postgres.py:132`). The interruption was observed to happen, yet the row says the
    episode is still open.
- These rows are exactly the ones the dispatch asked me to check for honesty.
- Possible rulings (the choice is the Architect's):
  - a cold or EV specific signal and text, for example "No recorded end", or one based on the claim's `open` flag
    or fault-clear state;
  - or keep ACT_NOW but change the reason text so it does not claim the episode is open.
- This needs a ruling before the owner walkthrough sees the text. It is not an Implementer acceptance gap.

### Low

**L1. Group heading counts include rows that the current lens hides.**
- `EstatePortfolio.tsx:249-271` takes counts from `summary.placement_counts`. These are counted over all members
  (spec Q-C24), while the table shows only the lens rows.
- Under `lens=risks`, a heading such as "Act now · 3" can therefore sit above two rows.
- This conforms to the spec. Suggest that the Architect consider omitting the count, or labelling it "of all
  Findings", when the lens is not `all`.

**L2. The packet's Producer 2 evidence is from before the rulings.**
- The tier-2 run at `0bcb7f16` predates the Q1 texts and the Q2 EV test. The packet states this. Listed here only
  so that the coordinator does not count that run as the merge evidence.

No other findings:
- The placement rules match the build spec rules 1-6, including Q-C6 (Monitor before Compare), Q-C7 (`line_group`
  from the same call) and Q-C20 confidence.
- The vocabulary matches the Q1 and CC-R1-Q1 texts, and both guard tests are present.
- Cursor: six parts, with bool, float, string, 0 and 6 refused, and `v` unchanged.
- Lens: RISK is set for exactly the three mechanisms, on both roots.
- `placement_counts` is null unless F is COMPLETE or EMPTY, and EMPTY gives zeros.
- Q3 copy carries MOCK DEVIATION comments. R502 is registered.
- The CC-R1 Lows in `1407a4b0` are correct.
- No money is aggregated across beneficiaries:
  - placement reads only the money group `state`;
  - `placement_counts` are row counts;
  - `double_count_violations == []` is asserted in both Postgres tests and in the producer.

## Evidence owed before merge

1. **Tier-2 rerun on the reviewed revision.** Run `test_cc_placement_postgres.py` (both tests) on
   `assetops_cc2_test`, after the H1/H2/M1 fixes. Check:
   - `test_cold_ev_placement_risks_lens_and_paging`:
     - both cold rows are ACT_NOW with `EPISODE_OPEN` and `NO_ACTION_RECORDED`, with the Q1 confidence texts;
     - KOBO is COMPARE_VALUE / `PRICED_SINGLE`;
     - the counts are `{0, 2, 1, 0, 0}`;
     - `lens=risks` returns the two cold rows;
     - `limit=2` paging gives every row exactly once, in group order.
   - `test_ev_interruption_placement`:
     - exactly one EV row, with source `REGISTERED_SIMULATION` and `episode_end` null;
     - ACT_NOW_OPEN and SUPPORTED_SOURCE_COHERENT, with `["Supported Finding", "Generated test data source"]`;
     - `lens=risks` returns that row.
     - Any Stop condition must be reported, not worked around.
   - Also run the adjacent `test_w301_estate_index_postgres.py` and `test_w303_portfolio_*_postgres.py`. Record
     the revision, the pass/skip/fail counts and the wall time.
2. **The s602b `estate` build** on `assetops_s602b_audit_cc_estate`, using walkthrough `prepare --db
   assetops_s602b_audit_cc`, after the H1 window and H2 clock fixes. Check:
   - `case-estate.json` exists and has a `placement` block, and the stdout line reads "estate: F01 (MONITOR,
     [VERIFIED_WATCH_RETURN]), F03 (ACT_NOW, [RECURRED, ..., NO_ACTION_RECORDED]), F05 (NEEDS_INVESTIGATION,
     [LIFECYCLE_UNCONFIRMED, ...])".
   - F01's outcome is still VERIFIED after the F03, F05 and price steps (a spec Stop).
   - F03's 09:30 row has not moved to NEEDS_INVESTIGATION because of `CONSEQUENCE_WITHHELD` after the price
     publication. If it has, report it: do not reorder the steps.
   - No KOBO-001 row has source UNKNOWN or MIXED, `double_count_violations` is empty, no row has a numeric
     priority, and everything fits on one page (`next_cursor` null).
   - The other four cases still build unchanged: adding `estate` to `CASES` makes every `prepare` build five DBs.
3. **The Portfolio capture** (`capture`, part `estate`, at 1440x1000 and 390x900). Check:
   - `results-estate.json` has every `portfolioSuite` claim `ok`:
     - group headings once each, in GROUPS order, with the "label · count" text;
     - F01 MONITOR, F03 ACT_NOW and F05 NEEDS_INVESTIGATION, each under its own heading, with its reason line;
     - every row has a confidence code and text, and no guarded word appears;
     - the bottom line equals "Placement and confidence answer different questions.";
     - the disclosure is closed on load, and when opened shows the five lines and the footer;
     - `noOverflow` holds at both widths (the 6-column table with heading rows scrolls inside its own scroller at
       390, and the page never scrolls sideways).
   - The six PNGs: `app-case-estate-portfolio-*`, `app-case-estate-portfolio-policy-*` and `mock-portfolio-*`.
   - The `comparison.md` "portfolio (priority panel)" row.
   - A visual check that the Finding cell shows customer mechanism words, not raw codes (M1). The scripted claims
     do not check this.
   - A visual check that the Placement column (9%) does not wrap the group label awkwardly.
   - If Chrome is unavailable, record `layout evidence: not run` with that precondition. Never record it as a pass.
4. **Rulings.** An Architect ruling on the M2 text, the new window literal (H1), and the H2 approach (pin the read
   time, or run after `pinned_at`).

## Architect rulings (Claude, 2026-10-28)

Produced by the Architect (Claude) under the 2026-10-27 default binding. Each finding was checked in code at
`27d7c525`. All four are confirmed. The rulings are also recorded as CC-R2-F1..F4 in the build spec "Implementer
questions and resolutions".

**F1 (H1, window): confirmed.** `scope.py:21,121` refuses a span over `MAX_DAYS = 31`, and 10-01..11-03 is 33
days. The new literal is `from=2026-10-03T00:00:00Z&to=2026-11-03T00:00:00Z`, which is exactly 31 days and is
accepted. It holds F01 (10-06), F02 (10-08), F03 (10-11) and F05 (10-21), and every `site_import` is earlier than
`to`. Change it in `tools/s602b_test_scoped_cases.py:51` (`ESTATE_PORTFOLIO`) and
`tools/s602b-verification-evidence.mjs:293`. The spec Producer 1 literal is amended to match.

**F2 (H2, read clock): confirmed.** `PostgresEstateRead.read` takes `SELECT now()` as `read_at`, and that value is
the cutoff `k` (`index.py:193-197`). The rows carry fake times from 2026-10-29 to 11-02. Ruling: pin the read time
the same way as the Action clock. The pin lives in `pinned_app` in `tools/s602b_test_scoped_cases.py`, so it
covers both `estate_assertions` (build) and `serve`. No product module changes, and no environment flag or
production switch is added. In `pinned_app`, for both `PostgresEstateRead` and `PostgresEvidenceMoneyRead` (the
subclass overrides `read`, so each class is wrapped), replace `read` with a wrapper. The wrapper calls the original
`read` with `work'`, where `work'(snap)` sets `snap.read_at = pinned` and then returns `work(snap)`. Everything
else stays unchanged: the transaction, READ ONLY, the refusals and the cursor (`k = read_at` when `known_at` is
absent). The served page is then not historical, because `k == read_at`. Rows written at real `now()` (the price
publication) come earlier than `pinned` and stay visible. Record the pin in the packet and in the `serve` banner
line: "Action clock and estate read time pinned at <pinned_at>". Not chosen: "run only after `pinned_at`". It
would leave the case unreproducible later, because further rows are not ruled out.

**F3 (M1, mechanism words): confirmed.** `EstatePortfolio.tsx:199` renders `row.mechanism` raw. No frontend label
map exists for these codes. Add one map, `MECHANISM_WORDS`, in `frontend/src/estate/` (beside
`estateEvidenceWords.ts`, or inside it). The fallback is "Mechanism not recorded" for null or any other value. The
words:

| Code | Customer words |
|---|---|
| `GENERATOR_SUPPORT_CANDIDATE` | Possible extended generator support |
| `COLD_EXCURSION` | Chamber temperature above policy |
| `COLD_START_FAILURE` | Automatic start failed |
| `EV_INTERRUPTION` | Charging session interrupted |

These reuse the existing product phrases where they exist: "Automatic start failed" is from `cold_depth.py:144`,
and the others come from the v69 `#/portfolio` row titles and mechanisms. Mark it MOCK DEVIATION in a comment:
v69 shows instance text such as "Automatic start failed; cooling interrupted" and "30 min candidate; charging
trade-off remains". The wire carries only the code, so the generic words drop the figures and the effects that the
row does not carry. Tests:
- Set the KOBO fixture `mechanism` to `GENERATOR_SUPPORT_CANDIDATE` (`portfolioFixtures.ts:45`).
- Assert the four words and the fallback in `estatePortfolio.test.tsx`.
- Assert that no `/[A-Z]+_[A-Z_]+/` token appears in the priority panel text.
- Add the same token check to the `portfolioSuite` claim 4 in the `.mjs` file.

**F4 (M2, "still open"): confirmed.** `postgres_finding_store.py:672-673` stores only `start` for a start failure.
The W2-05b `interrupted` session has `abort_at` with `end_at` null. A null `episode_end` therefore means "no
recorded end", not "open". Ruling: this is a text change only. The code `EPISODE_OPEN`, rule 2 and every placement
stay unchanged, so the CC-00 ranks and the Q2 assertions keep their groups. `REASON_TEXT["EPISODE_OPEN"]` becomes
**"No end is recorded for this episode"**. The new text is true for all three cases: an open excursion, a point
start failure and an aborted session. No data change. Update the literal in the spec reason table and in:
- `placement.py:26`
- `test_cc_placement.py:101,188`
- `test_cc_placement_postgres.py:31`
- `portfolioFixtures.ts:105`
- `estatePortfolio.test.tsx:654,715`

The permanent ACT_NOW for a start failure with no Action is intended: the work is open until an Action is
accepted. L1 stays as the spec has it for now and goes to the post-W6 UI/UX pass.

**F3 amendment (2026-10-28).** The first label for `GENERATOR_SUPPORT_CANDIDATE` failed the vocabulary guard,
because "candidate" is a forbidden phrase. The label is now "Possible extended generator support": "Possible"
keeps the unconfirmed sense. All five strings below were checked with `forbiddenPhrases` under both the `t028` and
`w1` sets, and each returned `[]`:
- "Possible extended generator support"
- "Chamber temperature above policy"
- "Automatic start failed"
- "Charging session interrupted"
- "Mechanism not recorded"

F4's "No end is recorded for this episode" also returned `[]`. The guard is unchanged.
