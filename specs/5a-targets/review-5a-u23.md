# Review: 5a units 2-3 (target rules, TargetRead, portfolio, composition), round 1

Reviewer (Claude, fresh; not the author), 2026-11-20. Branch `task/5a-targets-u23`, head `e6416e50a`, worktree
`/opt/assetecon/AssetOpsV1-5a2`, merge base `e88641e97`. Depth: discovery (W5). Read only.

## Summary (round 1)

- **Verdict: ACCEPT.** One Low finding (F1, a missing test for a ruled path), fixable on the branch, not blocking.
- No honesty breach found. Each hunt item checked in code and by test or plant (table below).
- Lakeside's 2,295.00, 3 of 3, is derived: `evaluate` per Site, then `compose`. No figure is literal under
  `structure/targets/`, and test 6 compares with the pack's `plan.sums` read from `derived-values.json`.
- P5 rules 6 and 7 are followed exactly (stated headings DECLARED, the weakest part sets the label elsewhere, "k of n"
  per factor, operator lines only in `portfolio_lines`).
- Q2: change the fixture to a `service:` literal. Q3: confirm the builder's default. Views below; neither blocks.
- Reruns: 5a and parity 37 passed; Postgres 4/4 (routed); architecture and workflow checks pass; 3 of my own plants:
  2 caught, 1 survived (F1).

## Honesty hunt

| Item | Where | Result |
|---|---|---|
| Assumed target unlabelled or with stronger origins (Q3) | `read.py:158-162, 214-259` | Every assumption is `ESTIMATED`, carried as `ASSUMPTION` and uses the spec's words byte for byte (test 3(a), 31 leaves × 3 Sites, `Missing` field by field). The origins are no stronger than the basis: `LEAK_ZERO` carries `unknown`, `AT_ACTUAL` carries the actual's, and `MAIN` carries the union of its heading line and every leaf under that heading. Kobo `necessary_l` = `(source-emulated, unknown)`, so `weakest_origin` reads `unknown`. My plant R2 (MAIN carries only the heading's origin) fails `test_3a_origins_of_assumptions`. |
| Heading above a cost at actual not Estimated (D-5A.15) | evaluator weakest-part rule | Test 3(b): Mto `staff` at actual, so `cost_to_serve` and `contribution` are `ESTIMATED`, with `assumed_leaves == ("staff",)`. The check still agrees. V10 fails it. |
| Unknown read as zero | `read.py:214-229, 246-255` | The only `Decimal("0")` built is `LEAK_ZERO`, plus the neutral `OPTION` values. A missing actual, a missing heading, or a main factor that is unsolved, nonlinear or has zero slope each gives an absent target. My plant R3 (unsolved MAIN set to 0) fails tests 7 and 9. One sub-path is untested: F1. |
| k of n | `read.py:283-291` | Mirrors `StructureRead.portfolio`. Test 7: 1380.00, 2 of 3, Mto `out` named with its 8 leaves. Another Site type shows as `sites_excluded`, not dropped (test 6 refusals). |
| Head-office lines added in | `read.py:287-291` | `compose` runs over the Sites only, and `portfolio_lines` is listed apart. Test 6: `staff` 1450.00. V7 fails it. |
| Blocked target computed instead (D-5A.13) | `read.py:205-206, 239-240` | A blocked factor's target is absent with cause `NOT_CALCULATED_YET`, which triggers 4b1's blocking row. In test 8(c), a control shows the expression has a value; with a second line, `revenue` is absent and `computed` is None. V15 fails it. |
| Mismatch hidden (Kisiwa −60 vs −65) | `read.py:262-269` | The computed −65.00 is served, and the line value appears only as `TargetCheck(-60.00, -65.00, USD, False)`. The line is never used in place of the computed value (V6 fails tests 3 and 6). |

## Findings

**F1 (Low; a missing test, not a spec acceptance gap).** `backend/assetops_backend/structure/targets/read.py:215-216`.
D-5A.10 names `LEAK_ZERO` on a money leaf with no Site currency (giving an absent target, note
`TARGET_CURRENCY_UNKNOWN`) as an "unknown is never zero" path. No test reaches it: the Site currency is always USD
in the fixture. My plant R1 removed the guard and gave money leaks a hard-coded USD zero, and all 32 tests in
`test_5a_targets.py` still passed. **Why it matters:** this is the class sweep the guide names ("an unknown read as
zero"); a later edit could assume a currency silently. **Fix:** add one case where Kobo's money lines carry two
currencies, so `currency` is None. Assert that `SiteTargets.currency is None`, and that `in_transit`, `outstanding`
and `liability` are absent (`NOT_RECEIVED`, `TARGET_CURRENCY_UNKNOWN`). Assert also that the non-money leaks
(e.g. `technical_loss_kwh`) are still 0 `ESTIMATED`.

No other findings. As an aside, not a finding: `read.py:170` `_origin_union` copies `evaluate._origin_union` (private).
It is harmless, and sharing it would edit an existing module, which 5a may not do.

## Mid-build questions (my view; the Architect rules)

- **Q2.** I recommend changing the fixture's step-1 `entered_by` and §5's `declared_by` literal to a `service:` name
  (e.g. `service:ds3-loader`). Today the spec's own literal is a declarer that production refuses, so the in-memory
  test proves a path Postgres cannot hold. The "no person declared it" meaning is unchanged (`person_id` None). The
  workaround is honest and labelled (`test_5a_targets_postgres.py:30-33`), and both stores now pass.
- **Q3.** Confirm the builder's default. A solved main factor is arithmetic over its heading line and the parts under
  that heading, so their union is exactly its basis. Because `unknown` ranks weakest, any `LEAK_ZERO` under the
  heading already makes it read `unknown`. The `("unknown",)`-only alternative is more conservative but drops a true
  `source-emulated`. Either is honest, since `ESTIMATED` and the label `ASSUMPTION` carry the evidence.
  `solve_main`'s keyword-only `currency=` is needed to follow the spec's words and does not change its positional
  signature.

## Checks run (this review, head `e6416e50a`)

- Module paths: PYTHONPATH = worktree `backend`, `backend/tests`, `contracts`, `simulator`. `targets/read.py`,
  `assetops_contracts` and `assetops_simulator` resolve inside `/opt/assetecon/AssetOpsV1-5a2`.
- `heavy-slot.sh -- pytest backend/tests/test_5a_targets.py simulator/tests/world/test_5a_fixture_parity.py`:
  **37 passed** in 1.03s.
- `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- backend/tests/test_5a_targets_postgres.py`: **4 passed**,
  run twice. The conftest's `pg_harness.route()` routes each run to a per-run `*_test` clone; the routed name is not
  printed in quiet mode.
- `check-architecture.ps1`: passed, with `ASSETOPS_GUARD_PYTHON` set to the main venv. Without it, the chain guard
  refuses, because the worktree has no `.venv`; that is the environment, not the diff. `check-agent-workflow.ps1`:
  passed.
- Plants, in scratch copy `.../scratchpad/rev5a23-plants-1976746` (from `git archive HEAD`; never in the worktree):
  - R1 (money leak takes USD with no currency): **survived**, 32 passed (F1).
  - R2 (MAIN origins = heading only): failed `test_3a_origins_of_assumptions`.
  - R3 (unsolved MAIN read as 0): failed tests 7 and 9.
- Cited, not rerun (same revision, evidence `/opt/assetecon/evidence/5a-u23/`): 289 passed regression set;
  fast check-all, 40 guards; `plants.log` shows V1-V8, V10-V13 and V15 each failing their named tests.

## Could not verify

- The routed database name for my Postgres runs: it is not printed, and the harness routing is relied on.
- The two origin plants: `plants.log` lists only V-plants. My R2 independently covers one of them, the MAIN origin.
- The 289-test regression run and check-all: cited, not rerun (`.ai/RULES.md` §7).

## Residual risk the packet does not name

- **The check is the only place a disagreement lives.** Kisiwa's −60.00 vs −65.00 is visible only in
  `SiteTargets.checks`. `5c` must render it beside contribution, or the mismatch is hidden on screen. Pin this in 5c's
  spec.
- **Mixed currencies.** `AT_ACTUAL` takes the actual's currency, while `LEAK_ZERO` and `MAIN` take the budget's. A
  Site whose actuals are in KES and whose budget is in USD gives a heading the evaluator refuses or leaves absent. That
  is honest, but no test shows which.
- **The in-memory store accepts `entered_by` values Postgres refuses.** This is a parity gap in 3A1's fake, outside
  5a, and it is the root of Q2.
- **The merge with 4b2** will conflict on `.ai/state/data.md` and `index-2.md`; renumber line 157.
