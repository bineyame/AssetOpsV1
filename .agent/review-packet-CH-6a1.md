# Review packet CH-6a1: records, strategies, CHARGERS_MOSTLY_IDLE

- **Branch:** `task/CH-6a1-records`, from main `628f77b36`.
- **Commits:** pre-flight `4cb9dbd94`, build `29dfb24a3`, then this packet.
- **Scope:** `build-sheet-CH-6.md` SCOPE-1, CH-6a1 (1.25 units).
- **Rulings applied:** CH6a1-R, at the end of `build-sheet-CH-6.md`.
- **Review:** own review. Not batched.

## Outcome delivered

- **Node records.** `outcomes/outcome_map.py` gains `OutcomeContribution` (the §S.1 fields in order, frozen) and `CONTRIBUTIONS`.
  - `CONTRIBUTIONS` holds exactly the ten §A2.2 records, with `records_for(source, node)` and `kpi_record(outcome_key)`.
  - The `ENTRIES` literal is byte-identical. Its diff is empty; the only other change in the file is the import line.
- **Strategy registry.** `chain/strategies/` holds `base.py` plus six classes, and `REGISTRY` resolves `"<key>@<version>"`.
  - `base.py` defines the `ContributionStrategy` Protocol, a frozen `ContributionContext`, `Effect` (with `reason`), `Registry` and `UnknownStrategy`.
  - The six classes: `finding_presence`, `direction_only`, `graded_verdict`, `priced_energy`, `avoided_cost`, `recorded_amount`.
  - The strategies are pure and compute no new money:
    - `priced_energy` sums the stored day `money.amount` over COMPLETE and PARTIAL days. It does not scale a PARTIAL day. With mixed currencies it returns no money and `CURRENCY_MIXED`.
    - For a potential, `priced_energy` gives headroom kW × 1 h × the declared price, only when the evidence is SUPPORTED.
    - `avoided_cost` reads the `MoneyHead` range.
    - `recorded_amount` returns `NO_RECORDS`.
- **CHARGERS_MOSTLY_IDLE.** The key and the R12 record stay (SCOPE-1, CH6a1-R Q4). The `chain/graph.py:47` owner changes from `CH-6a1` to `BL-06`, and the test pins at `test_ch5b_graph.py:32,100-103` change to match. No detector is built.
- **No wiring.** Nothing calls the records or the registry yet (CH6a1-R Q1). No composer, route, "Why?" body or frontend changes, so no polish clone was run.

## Files

- `backend/assetops_backend/outcomes/outcome_map.py`
- `backend/assetops_backend/chain/strategies/{__init__,base,finding_presence,direction_only,graded_verdict,priced_energy,avoided_cost,recorded_amount}.py` (new)
- `backend/assetops_backend/chain/graph.py` (owner text and comment only)
- `backend/tests/test_ch6_contributions.py` (new, 22 tests)
- `backend/tests/test_ch5b_graph.py` (the pins)

## Acceptance criteria (SCOPE-1 CH-6a1)

| Criterion | Status |
|---|---|
| R2 node records as a data tuple beside the unchanged `ENTRIES`, with `records_for` / `kpi_record` | Met. `test_records_are_exactly_a22`, `test_records_for_and_kpi_record`, `test_records_are_data_only` |
| `ENTRIES` diff empty | Met. The git diff touches only the import and the appended block; `test_entries_literal_unchanged` compares against the verbatim copy |
| Every `kpi` driver is a `MEASURES` key (CH6a1-R Q2: or `CHAMBER_RANGE_MEASURE`) | Met. It also checks the measure's outcome |
| Every strategy resolves, as a test | Met. `test_registry_has_the_six_keys_and_every_record_resolves` |
| No duplicate record | Met. Keyed on `(source, outcome, node, role)` |
| R4 registry has six keys and no new money | Met. Strategy tests cover PARTIAL unscaled, LOW not totalled, zero → 0.00, CURRENCY_MIXED, potential SUPPORTED / LIMITED / unpriced, and the MoneyHead range |
| R12 record kept and graph known-gap owner BL-06 | Met. `test_chargers_mostly_idle_kept_as_known_gap_owned_by_bl06`; the graph check prints `(owner BL-06)` |
| Guards A, W, N, V, M, L, D | All PASS; see Checks |
| Backlogged (not built): BL-03, BL-04, BL-05, BL-06 | Not built, as ruled |

## Checks run (worktree, foreground, localised; no full suite, no demo prepare, no DB)

- **New and adjacent tests.** `pytest tests/test_ch6_contributions.py tests/test_ch5b_graph.py tests/test_out_a1_outcome_map.py`: 50 passed.
- **`outcome_map` importers.** The tests of the other `outcome_map` importers (`test_ch4_opportunities`, `test_ch5b_why`, `test_out_c1_never_money`, `test_out_c2_board`, `test_out_c_rules`, `test_out_d4_board`, `test_s4_finding_api`, `test_w301_estate_api`, `test_w303_portfolio_api`): 143 passed, 1 skipped.
  - The skip is `test_w303_portfolio_api.py:353`, because `ASSETOPS_TEST_DATABASE_URL` is not set. It needs a DB and was not run here.
  - `test_out_d2_objectives` was not run: it is untracked in the main checkout and not present on this branch.
- **Non-vacuity proofs.** Each check below was run on the committed head, failed, and was reverted with `git checkout --`; the tree was clean afterwards.

  | Mutation | Result |
  |---|---|
  | Duplicate record | 3 failed |
  | Unknown kpi driver | 2 failed |
  | `direction_only@2` (an unresolved strategy) | 3 failed |
  | An `ENTRIES` edit | 1 failed |
  | LOW counted in earnings | 2 failed |

- **Graph check.** `python -m assetops_backend.chain.graph check` exits 0 and prints "known gap: no producer: WARNING:CHARGERS_MOSTLY_IDLE (owner BL-06)".
- **Guards, run one at a time.** All PASS:

  | Guard | Command | Result |
  |---|---|---|
  | A | `check-architecture.ps1` | PASS |
  | W | `check-agent-workflow.ps1` | PASS |
  | N | `check-navigation-truthfulness.ps1` | PASS |
  | V | `test_out_b2_vocabulary.py` | 4 passed |
  | M | `test_mock_deviation_labels.mjs` | exit 0 |
  | L | `check_v69_ledger.py` | 110 screens, valid |
  | D | `check_v69_dependency_registry.cjs` | exit 0 |

- **Frontend hard-wiring ratchet.** Passed and did not rise: totals api 12, href 24, lit 70, cmp 51, code 3. No frontend edit.
- **Polish clone.** Not run. No stored route body changes (CH6a1-R).

## Known deviations

- **KD-1.** The `ContributionContext` fields are the builder's (CH6a1-R Q5 accepted). CH-6a2 may only add fields.
- **KD-2.** The CH5b2-R Q5 interim "Why?" rule is still live. The wiring goes to CH-6a3 at +0 (CH6a1-R Q1). The `why.py:9-11` docstring still names CH-6a1 as the replacement; CH-6a3 rewrites that function.
- **KD-3.** `graded_verdict@1` reports day-grade counts. A day takes its weakest subject row's grade, in `GRADES` order. CH-6a2's evaluator AND-ing (R6) decides completeness and may count differently. If it does, CH-6a2 owns the change.

## Residual risk

- The strategies have no consumer yet. Their real inputs (MoneyHead from `money_head`, the thread headroom items) are tested only on synthetic values until CH-6a2/6a3.
- No file overlaps lane 2 (CH-9b2: 0052, `actions/*`, `verification_*`).

## User review

Not required. This is backend data and pure code with no screen change. Own review only.
