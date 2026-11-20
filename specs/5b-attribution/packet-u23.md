# 5b units 2-3 packet: carrying, the Site and portfolio bridges, the read

Implementer: Claude (fresh `assetops-implementer`), 2026-11-20. Branch `task/5b-attribution-u23`, worktree
`/opt/assetecon/AssetOpsV1-5b2`, base `main` `fb6d248d3`. Spec rev 2 §3, §4, §5.2, §6 tests 5 to 11 and Postgres;
rulings D-5B.1 to D-5B.15. Not merged. `USER_REVIEW_REQUIRED`: false for these units (no screen; the money figures are
spec literals); true for the slice at `5c`.

## Files changed

- New: `backend/assetops_backend/structure/attribution/carry.py`, `backend/assetops_backend/structure/attribution/site.py`,
  `backend/assetops_backend/structure/attribution/portfolio.py`, `backend/assetops_backend/structure/attribution/read.py`,
  `backend/assetops_backend/structure/attribution/composition.py`, `backend/tests/fixtures/attribution_lakeside_mto.json`
  (spec §5.2, verbatim), `backend/tests/test_5b_attribution_postgres.py`.
- Edited (5b's own): `backend/assetops_backend/structure/attribution/__init__.py` (docstring),
  `backend/assetops_backend/structure/attribution/bridge.py` (comment only: D-5B.15), `backend/tests/test_5b_attribution.py`
  (tests 5 to 11; 3(a) and test 4 assert the RESIDUAL pair, review u1 Low 1).
- Docs: `specs/5b-attribution/packet-u23.md`, `specs/5b-attribution/spec.md` (status), `specs/5b-attribution/mid-build-questions.md`
  (count), `specs/INDEX.md` (5b row), `.ai/state/data.md` (u1 "Open" line, review u1 Low 2; new u2-3 entry), `.ai/state/index-2.md` (163).
- `git diff main...HEAD -- backend/assetops_backend/structure/read.py`: empty. No migration, no other module edited.
- **Overlap with 3B7a (parallel in `/opt/assetecon/AssetOpsV1-3b7a`):** no shared code file. Shared docs only:
  `specs/INDEX.md` (5b's row only), `.ai/state/data.md` and `.ai/state/index-2.md` (appended lines; a merge may need the
  next free number). Test 10's branch check (`git diff main...HEAD -- structure/read.py`) runs only on a `task/5b-*`
  branch, so 3B7a's branch, which owns the seam, never fails it.

## Acceptance (spec §7)

1. Yes. Portfolio `contribution` 1443.00 / 2295.00 / −852.00 / −852.00, 3 of 3, ESTIMATED; each Site as §5.2's table
   (test 6, 7; Postgres pg_1, pg_2).
2. Yes. Kobo −562.00 = revenue +38.00 + cost to serve −600.00 (fuel −600.00, om 0, staff 0); revenue and fuel cost
   `NOT_SPLIT` `DETAIL_NOT_AVAILABLE` with §5.2's `unobserved_*` tuples, the same on Kisiwa and Mto (R9: no difference).
3. Yes (unit 1, tests 1, 2; unchanged).
4. Yes. Kisiwa `om` carried at 700.00, ESTIMATED, `carried_as` TARGET, "Service contractor invoice", `CARRIED_TEXT`,
   `target:budget:<revision>`, blocks `("cost_to_serve", "contribution")`; not carried for `MONTH_OPEN` (root then
   `GAP_NOT_AVAILABLE`), `NOT_CONNECTED`, an assumed target (`NO_TARGET_LINE`) or a stated heading (test 5).
5. Yes. Row evidence weakest, origins union; Kobo root DECLARED with `("observed-financial", "source-emulated")`;
   every cash root ESTIMATED with weakest origin `unknown`.
6. Yes (unit 1; D-5B.15 pair now asserted in 3(a) and as a test 4 invariant; test 4 also runs over test 6's six trees).
7. Yes. One set per row (`k`, `n`, `out`); without Mto's billing −747.00, 2 of 3, Mto out with `actual:` + 4b's
   `MTO_MISSING`; `NONE` factors add no values (`diesel_price` None/None/None, effect −59.00; `diesel_l` 2360/1400/960);
   `carried == ("KISIWA-001",)` on `om`, `cost_to_serve`, `contribution`, `()` elsewhere.
8. Yes. `disagreements == (("KISIWA-001", TargetCheck("contribution", −60.00, −65.00, "USD", False)),)`; target −65.00.
9. Yes (Files changed above).
- Q5 (owner default, like-for-like only): `portfolio_bridge` returns only like-for-like rows; no 3-of-3 target is built.

## Checks (code at `a3df6e11d`; docs commit follows)

- No database: `pytest tests/test_5b_attribution.py tests/test_3b3_structure_evaluate.py tests/test_4b1_stated_nodes.py
  tests/test_4b_money_leaves.py tests/test_5a_targets.py tests/test_3b7a_site_inputs_seam.py`: **255 passed in 3.16s** (5b alone: 54; 26 new, test 4 over the six Site trees included).
  PYTHONPATH = the worktree's `backend`, `contracts`, `simulator` (verified by `__file__`).
- Postgres: `/opt/assetecon/AssetOpsV1/tools/heavy-slot.sh --db -- pwsh -NoProfile -File tools/run-host-tests.ps1 --
  backend/tests/test_5b_attribution_postgres.py backend/tests/test_5a_targets_postgres.py
  backend/tests/test_4b_money_leaves_postgres.py`: **8 passed in 8.34s** (exit 0; routed `*_test`). Log:
  `/opt/assetecon/evidence/5b-attribution/u23-plants/pg.log`.
- `pwsh -NoProfile -File tools/check-all.ps1` (fast): **exit 0, all 40 guards passed**, 76 s wall. Log: `/opt/assetecon/evidence/5b-attribution/u23-plants/check-all.log`.
- `python tools/select-tests.py --base main`: `mode: full (548 of 548)`, because a file under `backend/tests/fixtures/` changed; the full suite is the coordinator's to schedule (not run here).
- Plants (applied, run, reverted by `git checkout`; V22 by a temporary commit and `git reset --hard HEAD~1`): V4, V5,
  V6, V7, V7b (no `carried_as`), V8, V9, V10p (a Site with no effect counted), V15, V17, V19, V20, V20b (`carried` from
  the row only, not descendants), V21, V22, the D-5B.15 pair (LEAF/None), a `commercial` import in `bridge.py`, a
  `float(` in `portfolio.py`: **each fails its named test; 0 not caught**. Script and output:
  `/opt/assetecon/evidence/5b-attribution/u23-plants/{plants.py,plants.txt}`.
- Layout evidence: not run (no screen).

## Known deviations and local choices

- Mid-build count: **1** (unit 1's Q1, ruled D-5B.15); none in units 2-3.
- One code commit for units 2 and 3 (spec §9 says one each): the tests share one file; splitting it needed partial staging.
- `site_bridge` checks key, version and month as the spec says; it does not compare `site_code` (not in the spec).
- `portfolio_bridge` also refuses (`STRUCTURE_COMPOSE`) a `SiteBridge` whose month, key or version differ from its
  arguments (silent mixing otherwise). A row with `k == 0` has effect None and evidence NOT_AVAILABLE (never 0).
  `by_home` is empty when the `contribution` row has a currency mismatch (no currencies added).
- `BridgeRead` refuses a naive `known_at` (`ValueError`) and converts an aware one to UTC.
- `carry_at_target` relies on 3B3's rule that a leaf with no value names its `missing`.
- Test 10's packet check covers 5b's paths only (attribution package, `test_5b_*`, the fixture, `specs/5b-attribution/`),
  so another lane's files never fail it.
- Postgres step 1's `entered_by` needs no workaround: `targets_lakeside.json` already uses `service:ds3-loader`.

## Residual risk and review focus

- `portfolio._row`'s `out` reasons (sites_excluded, root unobserved, `NOT_SPLIT`) and the `carried` walk.
- The recorder in test 9(b) takes `known_at` from the keyword or the first `datetime` argument.
- `test_pg_2` runs the real wiring at the wall clock (20 Nov, after the fixture's intakes).

## Fix round 1 (review-u23.md: M1, M2, L1, L2)

Files: `specs/5b-attribution/review-u23.md` (the review, copied in).

- M1: test 9(b) uses a clock that moves per call plus a call count (one call per read). Reviewer plant R1 (clock re-read per Site) now fails it.
- M2: test 8(d) (November, open month: every row k 0 of 3, effect None, NOT_AVAILABLE, no 0.00, `by_home == {}`); 8(b) asserts `by_home == {}`. Plant writing `Decimal(0)` at k = 0 fails 8(d).
- L1: tests 8(e) (mismatched month, key, version refused) and 9(c) (naive `known_at` refused). L2: `site_bridge` also checks `site_code`; test 8(f).
- Runs (PYTHONPATH worktree backend, contracts, simulator; paths verified): 5b file 58 passed; 5b plus regression set 259 passed; 5b Postgres file via `heavy-slot.sh --db` and run-host-tests.ps1: 2 passed; fast check-all: 40 guards passed (84.4 s).
