# SR-5 server review (fresh Claude reviewer, 2026-11-12)

Scope: `GET /api/sites/{code}/range-overview` and `estate/range_days.py`, branch `task/SR-5-range-board` at 9219ab10b,
diff `git diff 6872ce10d HEAD` (merge-base with main). Pages not built, not reviewed. Judged against rev 9 §9.4,
rev 10a.4, 10c, 10d.10 and D-SR.9-12, 16, 22, 28-29, 50.

## Verdict: ACCEPT WITH NOTES (two Medium findings to fix on the branch before merge; no High)

## Findings

**M1 (Medium, acceptance gap, D-SR.50 2c / 10d.10 table row (c)). Day money composition is never exercised with a priced line.**
`backend/assetops_backend/estate/site_range.py:137-141` buckets `site_lines` to a day by `window_start[:10]` and sums
them with `_sum_lines`. The ruling requires that "the no-DB file pins the SUMMED and OVERLAPPING **day compositions**,
including the D-ANY.10 absent-run compose, with stub rows". `backend/tests/test_sr5_range_overview.py:277-286` only
calls `_sum_lines` directly. Every body in both test files has no ELIGIBLE line: the golden has `NO_ELIGIBLE_LINES`
on every analysed day, and the Postgres file asserts `NO_ELIGIBLE_LINES` (`test_sr5_range_overview_postgres.py:190`).
So a broken day filter (for example `day_lines = []`, a wrong date slice, or lines landing on the wrong UTC day) passes
every test. This matters because the per-day money is what SR-5d shows. Fix: one no-DB test that feeds
`site_range_body` stub money lines (monkeypatch `select_financial_scope`, or a priced `MoneySnapshot` line) on two
analysed days. Assert: a SUMMED amount on day A; OVERLAPPING on day B (two lines sharing an `overlap_group`);
`NO_ELIGIBLE_LINES` on a third day; WITHHELD on a gap day even when a line exists there. Run it with the dispatch rows
from the absent-run compose (`coverage.dispatch_rows_provider` returning absent runs, or the existing
`range_days.dispatch_days` patch), as the ruling names.

**M2 (Medium, acceptance gap per the most natural reading of 10a.4 / D-SR.28). `confirmed` and `not_confirmed` stay numeric when `count` is null.**
Rev 10a.4 says: "numeric when F coverage is COMPLETE/EMPTY, or the status is PARTIAL (checked days); else null, with
`confirmed` and `not_confirmed`." At `site_range.py:180-182`, only `count` is nulled. The test pins the opposite
(`test_sr5_range_overview.py:267`: `count is None and confirmed == 1`). The Portfolio nulls its per-member breakdowns
under the same `finding_known` rule (`category_counts(members, finding_known)` and `placement_counts`,
`portfolio.py:895-898`). On an UNKNOWN Site the page would then show "1 confirmed" next to an unknown total, which is
not an honest missing state. Fix: null `confirmed` and `not_confirmed` when `finding_known` is false, and flip the
test. If the builder reads 10a.4 differently, it is a one-line Architect question, not a design call.

**L1 (Low).** `outcome_api.py:244`: a malformed `known_at` is refused with `INVALID_WINDOW` (the local `_instant`).
The estate parser's code is `INVALID_KNOWN_AT` (`estate/scope.py:135`). This is harmless for the page, but it is a
different code from the estate's for the same input.

**L2 (Low, test strength).** `test_sr5_range_overview.py:154` guards its main assertion with
`if body["findings"]["count"]:`. The next test pins `count == 1`, so the guard is not vacuous today, but an assert
would be stricter. `test_every_day_carries_retired_count_and_totals` is 0 == 0 in the no-DB world. The real
`retired_finding_count` pin is the Postgres 10-21 agreement test, which is adequate.

**L3 (Low, residual).** The no-DB coverage-wins test (`:251`) covers only "rule ANALYSED, coverage names a gap". The
opposite direction ("rule gap, coverage none -> ANALYSED, logged") is pinned only on Postgres (F08 10-19). That is
acceptable, but it is worth a no-DB case when M1's test is added.

## Checked and found correct
- **Portfolio equality.** `_status` reproduces `_portfolio`'s rule for count 1: E and M use their own tuple domains and
  the per-site money lines; `partial and (all_g or partial)` reduces to `partial`, as `partial_sites and
  settled_or_partial` does for one Site. The coverage entry is `_coverage_site(site, cov)`. `money.partial` uses the
  same per-site lines (`portfolio.py:856-858`). The card is `operating_cost_card` over the one-Site lines. All of this
  is pinned against the live Portfolio route in the no-DB file and in three Postgres worlds (coverage, card, partial,
  status). Gaps == `coverage.days.gaps` is pinned on every fixture (STILL_PROCESSING excluded, per D-SR.28).
- **Day precedence** (`range_days.py:45-60`). It follows the corrected 9.4 order (NOT_EXPECTED, NO_READINGS,
  STILL_PROCESSING, the `data_gap_days` reason, NOT_ANALYSED, unmatched -> STILL_PROCESSING, ANALYSED). The 12-row
  table pins each step against a lower-precedence input. Coverage-wins in both directions is logged
  `site_range_day_mismatch` (`:88-97`). `site_range.py` maps ANALYSED to FINDINGS/CLEAR only.
- **retired_finding_count** (D-SR.50). It comes from the same `f_rows` read and the same `intersects` rule, with no
  second query. It is null exactly where `finding_count` is null (GAP_STATES), and the state stays CLEAR.
  `days_with_retired_findings` is added. The Postgres agreement pin (board = members + retired, 10-21 CLEAR with
  retired 1, F05 NO_LONGER_SUPPORTED) holds.
- **actions.open** imports `CLOSED_LABELS` from `site_outcomes/mini.py`. `complete_actions` (`pending_trial_count is not
  None`) is equivalent to `progress()`'s `complete` flag. `findings.count` follows `finding_known` (`portfolio.py:870-872`).
- **Route.** Admission is `board_site`. A non-MINI Site gets 404 `RANGE_OVERVIEW_NOT_APPLICABLE` before the window is
  read. The window goes through `estate_request` (422 `INVALID_WINDOW`; empty, non-midnight, >31 days and missing `to`
  are tested). No estate or a store failure gives 503 `SITE_RANGE_OVERVIEW_UNAVAILABLE`, and other EstateRefusals keep
  their own code. The stored route has key `{site, from, to, known_at}`, `sites` and `watermark_sites` set to the Site,
  and a `perf.route` line, all pinned.
- **D-SR.9.** The domain comes from `site_type` only (`DOMAIN_OF_SITE_TYPE`), with no Site-code branch, so Kobo and
  Kisiwa (both MINIGRID) take one path. Cold and EV get 404, which is tested.
- **D-SR.16.** Rows on, with every day an absent run and the provider proven called, give a body equal to rows off
  (Postgres).
- **Golden regeneration** (b19e917d2 -> 9219ab10b). Only `retired_finding_count` per day and
  `dispatch.days_with_retired_findings` are added. No existing value changed.
- **Diff hygiene.** There are 7 files: 3 source, 2 tests, 1 fixture and `.agent/SR-5-packet.md`. Nothing ignored or
  stray is in the diff, and the worktree is clean. No AR-4 file is edited (only imports).

## Checks run (this reviewer, worktree PYTHONPATH, main venv)
- `pytest tests/test_sr5_range_overview.py`: 33 passed (2.3 s).
- The same plus `test_cov_partial_portfolio.py` and `test_ch5a1_board_contract.py`: 59 passed.
- `ASSETOPS_TEST_DATABASE_URL=.../assetops_sr5_test pytest tests/test_sr5_range_overview_postgres.py`: 5 passed (85.6 s).
- Not run, by instruction: check-all/guards (the coordinator is running them), the full backend suite, and the frontend
  (no page in this round).

## Not verified / residual risk (not findings)
- Real-data parity (KOBO-001/KISIWA-001, 7/14/31 days), the mismatch-log count, the NOT_EXPECTED and OVERLAPPING
  counts, and stored <= 2.0 s are later gates (packet resume step 7).
- The WARM-1 `range-overview` entry is pending: `tools/warm_ranges.py` is not on main.
- Kisiwa has no dedicated test. Its path is identical by construction, and the parity run will exercise it.

## Re-review (fix round 95f5f0f52..083e4db26, fresh Claude reviewer, 2026-11-12)

**Verdict: ACCEPT.** No findings.

- M1 closed: `test_day_money_composes_per_day_through_the_body` feeds priced lines through `site_range_body`. In a scratch copy (git archive, not the worktree) with `day_lines = []` at site_range.py:138 it fails; on the branch it passes.
- M2 closed: `findings.confirmed` / `not_confirmed` are null when `count` is null; the test pins it.
- L1 closed (malformed `known_at` -> 422 `INVALID_KNOWN_AT`, tested). L2 closed (retired-day test now non-zero, guard removed). L3 closed (no-gap -> ANALYSED, logged, pinned).
- D-SR.56: state stays NOT_EXPECTED (Portfolio parity); `note` key only when readings > 0, carried server-side. Acceptable: the page is not built and the key is absent otherwise, so the golden is unchanged; SR-5b/d must render `note` in place of "Before readings began". Packet parity spec (`not_expected_with_readings` fields, one day per Site, last-local-day rule, 12 x offset readings cap) matches D-SR.56. The test checks note presence/absence only; the parity gate itself is a later real-data run.
- Regressions: none seen. No-DB run of test_sr5_range_overview, test_cov_partial_portfolio and the non-Postgres test_ch5a1_* files (incl. board_contract): 100 passed. test_ch5a1_reader_postgres.py fails collection (NameError `measures_for`), but it is a Postgres file and was not run; not in the diff. Not run: check-all, Postgres, frontend.
