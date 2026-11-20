# 5a units 2-3 packet: target rules, `TargetRead.site` and `portfolio`, composition

Implementer (Claude), 2026-11-20. Branch `task/5a-targets-u23`, worktree `/opt/assetecon/AssetOpsV1-5a2`, base main
`e88641e97` (unit 1 and 4b1 merged). Commits `3a455f85c` (code, tests), `7c84cf426` (state, status, Q2/Q3), this
packet. Spec `spec.md` rev 2 §3-§6; rulings D-5A.4-D-5A.15, D-4B.16, D-4B.18. P5 approved:
`owner/owner-p5-approved-and-defaults-2026-11-20.md`. Not merged. `USER_REVIEW_REQUIRED`: false for this unit
(non-screen; owner Q7 default D-5A.15 is applied and pinned by test 3(b)).

## Files (all new, except the two test files)

- `backend/assetops_backend/structure/targets/rules.py`: literals, `TARGET_RULE`, `MAIN_OF`, `solve_main`.
- `backend/assetops_backend/structure/targets/read.py`: `TargetCheck`, `SiteTargets`, `PortfolioTargets`, `TargetRead`.
- `backend/assetops_backend/structure/targets/composition.py`: `TargetReadService`, `build_target_read`.
- `backend/tests/test_5a_targets.py` (tests 3-9, 11, composition; unit 1's `lakeside` split into `load` and
  `check_1a` for reuse, no assertion changed), `backend/tests/test_5a_targets_postgres.py` (new).
- Docs: `.ai/state/data.md`, `.ai/state/index-2.md` (line 157), `specs/INDEX.md`, `spec.md` status,
  `mid-build-questions.md`. No existing module edited, no migration, no route.

## Done (spec §7)

1. Yes: portfolio `contribution` 2295.00, 3 of 3, DECLARED; Kobo 1445.00, Kisiwa −65.00, Mto 915.00; equal to the
   pack's `plan.sums` to the cent (test 6 reads `derived-values.json`).
2. Yes: line targets carry `budget:<revision id>` and the line provenance; declarers are unit 1's (test 1 also on Postgres).
3. Yes: `LEAK_ZERO`/`AT_ACTUAL`/`MAIN` give ESTIMATED, `carried_as` ASSUMPTION, spec words byte for byte (test 3(a),
   all 31 leaves per Site, `Missing` field by field, `blocks` from `blocks_of`).
4. Yes: absent targets name `BUDGET_LINE`; blocked cause `NOT_CALCULATED_YET`; two versions or two lines block (tests 7, 8).
5. Yes: stated headings DECLARED whatever is assumed below; Kisiwa check `(-60.00, -65.00, USD, False)`.
6. Yes: `site_count` out names MTO-001 with its 8 leaves (test 7); `staff` 1450.00, operator line only in
   `portfolio_lines` (test 6).
7. Yes: tests 5(a)-(c) plus a linear control.
8. Yes: `git diff --stat main` lists only the files above.

## Checks (real output; evidence `/opt/assetecon/evidence/5a-u23/`)

- PYTHONPATH = worktree `backend`, `backend/tests`, `contracts`, `simulator`; module paths printed and verified in the worktree.
- Focused + regression + parity (`test_5a_targets`, `test_4b1_stated_nodes`, `test_3b3_structure_evaluate`,
  `test_3b3_window_price_selection`, `test_3a4_commercial_months`, `test_3b1_structure_registry`,
  `simulator/tests/world/test_5a_fixture_parity.py`) through `heavy-slot.sh`: **289 passed in 5.66s**.
- Postgres: `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- backend/tests/test_5a_targets_postgres.py`
  (routed `assetops_pt1de323efce_main_test`): **4 passed** (first run failed, see Q2; `pg-1.log`, `pg-2.log`).
- Fast check-all: **All 40 guards passed**, 87.6 s (`check-all.log`). `select-tests --base main`: the two 5a files.
- Plants (`plants.log`, script in scratch; each reverted, tree clean): V1 (2b, 8a), V2 (2a, 7), V3 (3a), V4 (3a),
  V5 (3a, 6), V6 (3a, 6), V7 (6), V8 (5b, 5c), V10 (3a, 3b), V11 (3a, 8b), V12 (8a), V13 (7), V15 (8c) each fail
  every named test. V9, V14 are unit 1's (shown in `packet-5a-u1.md`). Origin plants: LEAK_ZERO tagged
  `source-emulated`, and MAIN without the parts under its heading, each fail `test_3a_origins_of_assumptions`.

## Mid-build questions: count 3 (Q1 answered earlier; Q2, Q3 new)

- **Q2 (open):** Postgres' `commercial_intake_entered_by_check` refuses the fixture's `loader:ds3`. Workaround, labelled
  as one: the Postgres file enters step 1 as `service:ds3-loader`; the in-memory file keeps the spec literal.
- **Q3 (default applied):** origins of assumptions (D-4B.18, not in spec §3.2): `LEAK_ZERO` `unknown`; `AT_ACTUAL` the
  actual's; `MAIN` its heading line's plus the other parts under the heading; `solve_main`'s probe `unknown` and a
  keyword-only `currency=`.

## Known deviations

- Q2 workaround and Q3 default above. Units 2 and 3 are one code commit (read.py holds both `site` and `portfolio`).
- Tests were written in the same pass as the code, not run red first; every plant above was then shown to fail.
- Plant V8 fails test 5(c) by a division error rather than a wrong note; it still fails.

## Overlap with 4b2 (`/opt/assetecon/AssetOpsV1-4b2`)

No shared file in code. `build_target_read` calls 4b2-edited `structure.composition.build_structure_read` (signature
unchanged on 4b2: it adds `stated=source`); tests import `structure.sources.ASSUMPTION_WORDS` (kept on 4b2). Likely
text conflicts at merge: `.ai/state/data.md` and `.ai/state/index-2.md` (both lanes append; renumber line 157).

## Review focus

Q3's origin rule; that `AT_ACTUAL` costs (D-5A.15) read ESTIMATED up to `contribution` while stated headings stay
DECLARED; that `TargetCheck` never replaces a computed value.

## Fix round 1 (review `review-5a-u23.md`, ACCEPT with F1)

- Merged `task/5a-u23-midbuild-answers` (spec rev 3, D-5A.16). Q2 as ruled: step-1 declarer is `service:ds3-loader` in
  `backend/tests/fixtures/targets_lakeside.json` and `test_5a_targets.py`; `PG_LOADER` removed from the Postgres file
  (spec §5 already carries the literal from rev 3). Parity test passes.
- F1: `test_8d_two_currencies_leave_the_money_leaks_unknown` (Kobo `fuel_cost` re-declared in EUR): `currency` None,
  `in_transit`/`outstanding`/`liability` absent `TARGET_CURRENCY_UNKNOWN`, `technical_loss_kwh` still 0 ESTIMATED.
  Plant (guard removed, money leak hard-codes USD) fails it: `assert Decimal('0') is None` for `in_transit`.
- Origin plants re-shown, failing output in `/opt/assetecon/evidence/5a-u23/plants-fixround.log`: MAIN without the
  parts under its heading and LEAK_ZERO tagged `source-emulated` each fail `test_3a_origins_of_assumptions`. Tree clean.
- Regression set (7 files) **290 passed**; Postgres 4 passed (`pg-3.log`); fast check-all: all guards passed, 81 s (`check-all-r2.log`).
