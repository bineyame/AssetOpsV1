# Review: 5b units 2-3 (carrying, Site and portfolio bridges, the pinned read)

Reviewer: fresh Claude (`assetops-reviewer`), 2026-11-20. Discovery depth (W5). Branch `task/5b-attribution-u23`,
head `4b34f7a36` (code `a3df6e11d`), worktree `/opt/assetecon/AssetOpsV1-5b2`, base `main` `fb6d248d3`. Read only.

## Summary (round 1)

- **Verdict: ACCEPT with findings fixed on the branch** (two Medium test gaps; no code defect found).
- Every figure an executive could see is right and single: Lakeside October 1,443.00 / 2,295.00 / −852.00, 3 of 3,
  ESTIMATED, `carried == ("KISIWA-001",)`; without Mto's billing −747.00 (633.00 / 1,380.00), 2 of 3, Mto named in
  `out`. Both recomputed by hand below. The uncarried 883.00 (1 of 3) is not reachable from `SiteBridge` or
  `PortfolioBridge`.
- Carrying, SUM-only, Kisiwa's disagreement, unknown-never-zero, Q5 like-for-like: all correct in code.
- M1: test 9(b) cannot catch a clock read more than once (my plant survives). M2: the portfolio's "k = 0 → effect
  None" safeguard is untested (my plant writing 0.00 survives), and it is reachable: an open month gives k = 0 on
  every row.
- Builder's three extra safeguards are sound; none is tested (M2, L1). The single code commit is acceptable.
- Checks rerun: 255 passed; Postgres 2 passed; architecture and workflow guards pass; 4 plants of my own, 2 caught.

## Hand recomputation

Sites (contribution actual, target, gap): Kobo 3458.00 − (1475.00 + 600.00 + 500.00) = 883.00 against 1445.00, −562.00;
Kisiwa 4070.00 − (3120.00 + 700.00 carried + 500.00) = −250.00 against −65.00 (not the budget line −60.00), −185.00;
Mto 2160.00 − (400.00 + 500.00 + 450.00) = 810.00 against 915.00, −105.00.

- 3 of 3: actual 883.00 − 250.00 + 810.00 = 1443.00; target 1445.00 − 65.00 + 915.00 = 2295.00; gap −852.00 =
  −562.00 − 185.00 − 105.00. Revenue 9688.00 / 9785.00 (−97.00); cost to serve 8245.00 / 7490.00 (Kisiwa's target
  4125.00 + 65.00 = 4190.00; Mto's 2240.00 − 915.00 = 1325.00); fuel 4995.00 / 4240.00; om 1800.00 / 1800.00; staff
  1450.00 / 1450.00. `by_home` −97.00 + −755.00 = −852.00. All match the test literals and the code.
- 2 of 3 (no Mto step): actual 633.00, target 1380.00, gap −747.00; never 633.00 − 2295.00 (−1662.00). My probe of the
  real code on that world: revenue 7528.00 / 7545.00 (−17.00), cost to serve 6895.00 / 6165.00, fuel 4595.00 /
  3865.00, om 1300.00, staff 1000.00, each 2 of 3 with `MTO-001` in `out`; `by_home` −17.00 / −730.00 (Σ −747.00);
  contribution ESTIMATED, `carried` Kisiwa; disagreement kept. All consistent by hand.

## Honesty checks (dispatch list)

| Check | Result | Where |
|---|---|---|
| One contribution only | Yes. `SiteBridge.actual` is `evaluate_inputs(carried inputs)`; the original inputs are not kept; `SiteBridge.targets` holds only the target side and checks; `PortfolioBridge` holds no composed actual or `PortfolioTargets`. 3B7a's `PortfolioMonthSnapshot.actual()` stays reachable outside 5b; D-5B.12 makes that 5c's gate. | `site.py:38-50`, `read.py:38-45` |
| Carrying | Closed month only (note checked), `NOT_RECEIVED` only (CAUSES has three values, two refused), own `DECLARED` `budget:` line only, `ESTIMATED`, `carried_as` TARGET, `CARRIED_TEXT` byte for byte; headings untouched (only `inputs.leaves`). | `carry.py:37-63` |
| −747.00 case | Mto named in `out` with `actual:` + `MTO_MISSING`. | test 8a |
| Prices and rates never summed | `actual/target/gap` only when `composes == "SUM"`; effect always. | `portfolio.py:124-128`; test 8c, test 7 sweep |
| Unknown never zero | Real code: k = 0 row has effect None, evidence NOT_AVAILABLE; `_sum` only runs over a non-empty set; currency mismatch → None. Untested (M2). | `portfolio.py:121-131` |
| Kisiwa −60 vs −65 | Kept in `disagreements`; target −65.00. | test 6, test 7 |
| Read instant pinned | Correct in code: `_pin` once per call, passed to every read. Test cannot catch a second clock read (M1). | `read.py:26-45` |
| Q5 like-for-like | Only like-for-like rows are built; no 3-of-3 target anywhere in the bridge. | `portfolio.py` |

## Findings

### M1 (Medium, test gap): test 9(b) cannot see the clock read twice

- **Where.** `backend/tests/test_5b_attribution.py:802-815` (`clock=lambda: READ_AT` at 808).
- **What.** The clock always returns the same instant, so a `BridgeRead` that calls its clock again for each
  `site_inputs` records only `READ_AT` and passes. My plant R1 (`site_inputs(s, month, self._pin(None))` in
  `read.py:43`) passed all 53 tests. Test 9(b) catches only V19 (None passed through), not "pinned once".
- **Why it matters.** D-5B.13 is "one instant per read": a target set from one state and an actual from another is
  a false gap. The spec's gate as written is weak; this is the class the ruling exists for.
- **Fix.** A clock that returns a later instant on each call (e.g. `itertools.count` seconds after `READ_AT`) and a
  call counter; assert the clock is called once per `site` / `portfolio` call and every recorded `known_at` equals
  that call's first value. Acceptance gap against D-5B.13's intent, not a preference.

### M2 (Medium, test gap): "unknown is never zero" in the portfolio is not pinned by any test

- **Where.** `backend/assetops_backend/structure/attribution/portfolio.py:121-131` (k = 0) and `:159` (`by_home`
  empty on a currency mismatch); tests 8a/8b (`test_5b_attribution.py:720-748`).
- **What.** My plant R3 (a row with k = 0 gets `effect = Decimal(0)`) passed all 53 tests. The case is real, not
  edge: November (open month) on the same world gives the `contribution` row `effect None, NOT_AVAILABLE, 0 of 3`
  in the real code, so under the plant the portfolio would read "gap 0.00" for a month that has not happened. Test
  8b also does not assert `by_home == {}` under a currency mismatch.
- **Why it matters.** It is the dispatch's "unknown is never zero" and the reviewer guide's first W6 sweep; the
  packet lists it as a safeguard but nothing fails if it regresses.
- **Fix.** Test 8(d): `BridgeRead.portfolio` for `"2026-11"` on §5.2's world: the `contribution` row has `actual`,
  `target`, `gap`, `effect` None, evidence NOT_AVAILABLE, `k` 0, `n` 3, three Sites in `out`, `by_home == {}`. Add
  `assert dict(pb.by_home) == {}` to 8b.

### L1 (Low, test gap): two of the builder's refusals are untested

- `portfolio.py:141-143` (a `SiteBridge` of another month, key or version is refused) and `read.py:29` (naive
  `known_at` refused). Both are sound and cheap; one `pytest.raises` each. Not blocking.

### L2 (Low, preference): `site_bridge` does not check `site_code`

- `site.py:41-43` compares key, version and month only; Kobo's inputs with Kisiwa's targets would bridge silently.
  The spec does not ask for it and `BridgeRead` keys by code, so it is a preference for 5c's snapshot path; adding
  `site_code` to the tuple costs one line.

## The builder's three safeguards and the combined commit

1. **`portfolio_bridge` refuses mixed month/key/version:** right; prevents silent mixing on 5c's snapshot path.
   Untested (L1).
2. **k = 0 → effect None, NOT_AVAILABLE; `by_home` empty on a currency mismatch:** right and honesty-critical;
   untested (M2).
3. **Naive `known_at` refused, aware converted to UTC:** right; untested (L1).

**One code commit for units 2 and 3** (spec §9 says one each): acceptable. The code is 390 lines, the units are
separable by file (`carry.py`/`site.py` vs `portfolio.py`/`read.py`/`composition.py`), the deviation is recorded in
the packet, and unit order is not a figure risk (3B7a unit 0 is on `main`; `structure/read.py` diff is empty).
No fix.

## Checks run (reviewer)

- PYTHONPATH = worktree `backend`, `contracts`, `simulator`; `__file__` verified: `portfolio.py`, `read.py` (structure)
  and `assetops_contracts` all resolve under `/opt/assetecon/AssetOpsV1-5b2`.
- `heavy-slot.sh -- pytest test_5b_attribution.py test_3b3_structure_evaluate.py test_4b1_stated_nodes.py
  test_4b_money_leaves.py test_5a_targets.py test_3b7a_site_inputs_seam.py -q`: **255 passed in 3.35s** (matches
  the builder's 255).
- `heavy-slot.sh --db -- pwsh -NoProfile -File tools/run-host-tests.ps1 -- backend/tests/test_5b_attribution_postgres.py`
  (from the worktree): **2 passed in 5.58s**, rootdir the worktree's `backend`. Builder's 8 (with 5a and 4b
  Postgres files) cited, not rerun.
- `check-architecture.ps1`: passed (with `ASSETOPS_GUARD_PYTHON` set; without it the chain-structure guard refuses
  to run). The Rule 8 "vacuous" note is pre-existing, not 5b. `check-agent-workflow.ps1`: passed. Builder's fast
  check-all (40 guards, exit 0) cited.
- `git diff main...HEAD -- backend/assetops_backend/structure/read.py`: empty.
- Plants in a unique scratch copy (`scratchpad/rev5b-u23-plants-2303472`, no git, so test 10's branch check skips):

| Plant | Result |
|---|---|
| R1 clock read again per `site_inputs` | **Not caught** (M1) |
| R2 carry a `NOT_CONNECTED` leaf | Caught: test 5c |
| R3 k = 0 row effect `Decimal(0)` | **Not caught** (M2) |
| R4 carry from any valued target (assumption) | Caught: test 5d |

- Builder's 18 plants (V4 to V22, D-5B.15 pair, commercial import, `float(`) cited from the packet, not rerun.

## Not verified

- The full suite (`select-tests` says full, 548 files, because a fixture changed): coordinator's to schedule.
- 5c's screen side of D-5B.12 (no screen in this slice).

## Residual risk the packet does not name

- **`out` reasons on sub-rows in the 2-of-3 case.** Mto is out of `om` and `staff` with its root's missing records
  (billing, fuel invoice), though Mto's own O&M and staff records exist. Spec-conformant (§4.1), but 5c must word it
  as "Mto not compared: its month is incomplete (billing, fuel invoice not received)", never as "Mto's O&M missing".
  Test 8a asserts only the `contribution` row's `out`.
- **`carried` follows the rendered tree.** A Site row that is not split below a carried leaf would read ESTIMATED with
  `carried == ()`. Not reachable for MINI_GRID today (non-stated sums always split), but a future stated
  `cost_to_serve` would hit it.
- `test_pg_2` reads at the wall clock; it would change meaning if run before the fixture's intake instants (not today).
