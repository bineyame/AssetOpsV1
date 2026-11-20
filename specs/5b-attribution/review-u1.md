# Review: 5b unit 1, the split rules (discovery, W5)

Reviewer: fresh Claude (`assetops-reviewer`), 2026-11-20. Branch `task/5b-attribution`, head `f431e3af8` (code at
`b81c09eff`; `f431e3af8` changes docs only: packet, state entry, spec status line). Worktree
`/opt/assetecon/AssetOpsV1-5b`, read only. Base `main` `8a2900bc4`.

## Summary (round 1)

- **Verdict: ACCEPT.** No High or Medium finding. Two Low items, neither blocking; Q1 is for the Architect.
- The engine follows spec §2.3's six steps in order, and nothing in it hides a figure. Volume is valued at the
  target price before price at the actual volume, and the price is chosen by its unit. Money reaches each part
  through `scale`. A RESIDUAL is built in exactly one branch, a node with a non-computable term and at least one
  computable term. A missing side gives no gap and no effect, never 0. `-0` is normalised.
- I recomputed by hand Kobo −562.00 = +38.00 − 600.00, AT-1, AT-2, AT-3 and 3(i). All match to the cent (below).
- `structure/read.py`: no diff. There is no `float`, and no `commercial` or `snapshot` import under `structure/attribution/`.
- 5b tests rerun: 28 passed. Three plants of my own, in a scratch copy: each fails its named tests.
- Q1 view: `NOT_SPLIT` / `DETAIL_NOT_AVAILABLE`, as built (reason below).

## What I checked against the hunt list

| Hunt | Result | Where |
|---|---|---|
| Parts add exactly to the gap | Yes. Step 6 sums the children and compares with `agree`. Test 4 asserts `==` on 12 of 13 trees and the tolerance only on 3(i). | `bridge.py:221-225`; test 4 |
| Volume at target price, then price at actual volume | Yes. VOLUME `m × tp.value`, then PRICE `m × aq.value`. The price is chosen by `("MONEY",1)` and not `is_money`. | `bridge.py:191-196, 213-216` |
| Money pushed down | Yes. Each child's scale is the parent scale × sign (× price or volume), and `effect = scale × gap` at every level. | `bridge.py:179, 211-219` |
| Residual only beside unobserved leaves | Yes. It is built only when `whole` is False and `children` is non-empty. `unobserved_*` is the stated side's `detail_missing`, or `()` for a side that is not stated. | `bridge.py:226-236` |
| 1E-12 hiding a real difference | No. It is used only in steps 4 and 6. A cent is 1E10 times the tolerance. 3(j) and my P3 plant confirm. | `rules.py:22, 30-33` |
| −0 | `gap`, `effect`, `scale`, the residual and `by_home` go through `_norm`. Test 4 checks every row. | `bridge.py:96-98, 162, 168, 234, 270` |
| Unknown read as zero | No. Every `Decimal(0)` is the start of a sum. A missing side returns before any arithmetic. In a SPLIT tree every child has an effect (steps 6 and 229), so `by_home` drops nothing. | `bridge.py:116-120, 173-174, 263-268` |
| SUM split on non-SUM rows (D-5B.11) | Not reachable in unit 1. D-5B.11 governs portfolio addition (`portfolio.py`, unit 3). Within one Site the split follows the parsed expression, never `composes`. Nothing here adds across Sites. | n/a |
| `structure/read.py` untouched | `git diff main...HEAD -- .../structure/read.py` gives 0 lines | |

## Hand recomputation

- **Kobo contribution.**
  - Actual: billed = 9100 − 410 − 0 − 45 − 0 = 8645, so revenue = 8645 × 0.40 = 3458.00. Diesel is 730 + 330 + 120 = 1180 L, so fuel = 1180 × 1.25 = 1475.00. Cost to serve = 2575.00, and contribution = 883.00.
  - Target: revenue 8550 × 0.40 = 3420.00, fuel 700 × 1.25 = 875.00, cost to serve 1975.00, contribution 1445.00.
  - Gap: −562.00 = +38.00 − 600.00.
- **AT-1 (revenue split).**
  - billed_kwh VOLUME: 95 × 0.40 = 38.00.
  - metered_kwh: 140 × 0.40 = 56.00, which is delivered 550 × 0.40 = 220.00 plus technical loss 410 × −0.40 = −164.00.
  - adjustments: 45 × −0.40 = −18.00.
  - The parts give 56 − 18 = 38.00. tariff PRICE: 0 × 8645 = 0.
- **AT-2 (litres).** diesel_l VOLUME 480 × −1.25 = −600.00. Its parts are necessary 30 → −37.50, candidate 330 → −412.50 and unexplained 120 → −150.00, which sum to −600.00.
- **by_home.** GROW_REVENUE is 220.00. OPTIMIZE_COST is −164 − 18 − 37.50 − 412.50 − 150 = −782.00. Together they give −562.00.
- **AT-3 (actual price 1.30).**
  - Fuel is 1534.00, so its effect is −659.00.
  - Volume (1180 − 700) × 1.25 = 600, effect −600.00. Price (1.30 − 1.25) × 1180 = 59, effect −59.00.
  - The reversed order would give 35.00 and 624.00. The test excludes both.
- **3(i).** Target necessary_l = 875 / 1.27. Price (1.25 − 1.27) × 1180 = −23.60 exactly. Volume (1180 − 875/1.27) × 1.27 = 623.60, within the 34-digit error. Together they give 600.00 within 1E-12, not with `==`.
- **Collected.** 3458.00 − 0 − 278.00 = 3180.00 against 3420.00, a gap of −240.00. This is revenue +38.00, in_transit 0 and outstanding −278.00.

## Findings

1. **Low, acceptance (pending Q1).** `backend/tests/test_5b_attribution.py:223-224`: test 3(a) does not assert the
   RESIDUAL's `split` or `reason`. The engine's choice therefore has no gate, and 5c will word it. Fix: once the Architect rules on Q1,
   assert the pair in 3(a). Also add a test 4 invariant: every RESIDUAL row has the ruled pair. This follows Q1 and does not block unit 1.
2. **Low, housekeeping.** `.ai/state/data.md` (5b entry, "Open" line) says units 2 and 3 wait for 3B7a unit 0 on
   `main`. That seam has since merged (`264d7d6a7`). Fix: update the line when unit 2 merges `main` into the branch.

No other findings. The packet's local choices are within the spec and named in the packet:
- the root currency is None on a mismatch;
- `scale` is normalised for −0;
- a SPLIT whose child has no effect becomes `SPLIT_INEXACT`.

## Q1: what a RESIDUAL row should carry (view for the Architect)

**Recommend `split` = `NOT_SPLIT`, `reason` = `DETAIL_NOT_AVAILABLE`, as built.**
- A RESIDUAL is the part of a heading that is not split because its detail is not observed. That is
  `DETAIL_NOT_AVAILABLE`'s meaning, and the row already carries that reason's payload (`unobserved_*` = the stated side's
  `detail_missing`). 5c can then word every stop, the residual included, from one rule: reason plus the records that would
  fill it (D-5B.10).
- `LEAF` with reason None would describe the row as an irreducible factor. It is not a factor (`factor_id` None), and its
  missing records would have no reason to hang on.
- `kind` RESIDUAL already distinguishes it from a heading that is not split. Two consequences follow:
  - 5c should key on `kind` first, so it reads as "the rest of revenue, not split until …" rather than as a heading.
  - `SPLITS` needs no fourth value.
- The contract "reason None unless NOT_SPLIT" stays true.
- Gate: finding 1.

## Checks run (reviewer, this revision)

- Module paths, with `PYTHONPATH` set to the worktree's `backend:contracts:simulator`:
  - `bridge.py` is `/opt/assetecon/AssetOpsV1-5b/backend/assetops_backend/structure/attribution/bridge.py`.
  - `assetops_contracts` and `evaluate.py` also resolve under `/opt/assetecon/AssetOpsV1-5b/`.
  - The interpreter is `/opt/assetecon/AssetOpsV1/.venv/bin/python`, because the worktree has no `.venv`.
- `tools/heavy-slot.sh -- python -m pytest tests/test_5b_attribution.py -q` gave **28 passed in 0.91s**.
- Plants of my own, run in the scratch copy
  `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/rev5b-u1-plants-2258764`.
  Each was reverted, and `diff` against the originals came back clean.
  - P1 (V1): price row at target volume (`m * tq.value`). 5 failed: test_1 ×2, test_2, 3d, 3i.
  - P2 (V10): a missing side read as 0 (guard removed, None → 0). 1 failed: 3g. My first attempt at this plant had an
    operator-precedence bug, so the guard still fired and the plant had no effect. I corrected it and reran.
  - P3 (V18b): `SOLVE_TOLERANCE = 0.01`. 3 failed: 3j, tolerance literal, test_4[3j].
- `pwsh tools/check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` set to the venv): **Architecture check passed**,
  exit 0. Without that variable, the chain-structure guard cannot find Python in the worktree. This is an environment
  matter, not a slice defect.
- `pwsh tools/check-agent-workflow.ps1`: **Agent workflow check passed**, exit 0.
- Builder's runs cited at code revision `b81c09eff`. The code is identical at head: `git diff b81c09eff f431e3af8` touches
  docs only.
  - 223 passed (focused and regression).
  - Fast check-all: all 40 guards passed (log `/opt/assetecon/evidence/5b-attribution/u1-plants/check-all.log`).
  - 12 plants each failing named tests, V1 to V18b and N1 −0 (`.../u1-plants/plants.txt`).
- Not rerun: the full regression set and check-all (no finding needs them, RULES §7). No database, server or Docker was touched.

## Could not verify / residual risk not named in the packet

- `actual` and `target` on a row are passed through unnormalised. An input that arrives as `-0` would show as `-0` there.
  The spec names only gap and effect. This is a 5c display risk, not a unit 1 defect.
- `SOLVE_TOLERANCE` is absolute. At these magnitudes (≤ 1E6) the 34-digit context's error is far below 1E-12. Above roughly
  1E22 it would not be, which is not plausible for monthly Site money.
- The "a child has no effect" `SPLIT_INEXACT` path (`bridge.py:223, 229`) is unreachable on today's data and untested.
  Only a child-level currency mismatch could reach it, and then the reason would name inexactness rather than currency.
- Stated-heading paths are tested on hand-built stated values only. Real 4b reads arrive in unit 2: tests 5 and 6, the Kobo,
  Kisiwa and Mto literals.
- Layout evidence: not applicable (no screen).
