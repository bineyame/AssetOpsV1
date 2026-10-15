# LR-01 fix round: targeted check

Reviewer: a fresh Claude reviewer who did not author the fix. Worktree `AssetOpsV1-review`, branch `task/LR-01-late-reading-series-and-money-limit`, head `78a47be5`. Diff checked: `87019e52..78a47be5`. `assetops_backend.__file__` was confirmed under `AssetOpsV1-review`.

## Verdict

**Accept once M1 is fixed on the branch.** M1 is a one-line regression in copy the owner sees, and it contradicts the owner walkthrough, which is a merge checkpoint. Rulings 1, 2, 4 and 5 are done as required, and so are L2 and L3. L1 is done except for M1.

## Items

| Item | Result |
| --- | --- |
| Ruling 1 | Done. The store docstring now describes the latest-revision replay and the returning basis. `TestMigration0015Downgrade` covers both paths: the refusal case keeps both revisions, stays at 0015 and leaves the constraint absent, and the clean case restores `finding_revision_basis_unique` and then upgrades back. |
| Ruling 2 | Done. See the next section. |
| Ruling 4 | Done. The wording in the task file, the packet and the walkthrough now matches the ruling: the money is on the Financials bridge, and the Finding page shows the SERIES_LIMIT statement and its evidence link. |
| Ruling 5 | Done. The new PG test builds `build_consequence_read_service(URL)`, asserts that the wired gate is a `MoneyEligibility`, reads ELIGIBLE at 15.8125 from persisted lineage, and then shows that both a raising gate and a `None` gate give no current amount and no bridge amount. `main.py` and `scheduling/composition.py` both use this builder. |
| L1 | Done except for M1. The relation wording is correct for every case: tail cut, head cut, inside, former and neighbouring window (SELECTED_WINDOW, "within 6 hours", which also holds for a span inside the finding). The span list is skipped when there are no spans. Two tests were added. |
| L2 | Done (the two downgrade tests above). |
| L3 | Done. The residual is recorded in the packet's residual risk and in the walkthrough notes. |

## Ruling 2: `scheduling/upstream.py`

- `findings[].money_eligibility` is the body's gate, passed through untouched. When the gate is missing, the seam falls back to PENDING (`ELIGIBILITY_NOT_READ`), so it fails closed. Nothing writes to the raw gate after that.
- `current_amount_permitted = gate.state == "ELIGIBLE" and not reasons`. The reasons are the window's S3, S4 and SCHEDULE blockers plus the Finding's own non-CURRENT consequence state. An amount is therefore never permitted unless the gate is ELIGIBLE and `upstream_status` is CURRENT.
- `upstream_status` carries typed `{stage, code}` reasons. A stopped schedule is named `SCHEDULE_STOPPED`.
- Scope note (not a finding): `upstream_status` leaves out window-level `CONSEQUENCE` blockers that belong to other Findings or to range work. The behaviour before the fix had the same scope, and S5 still requires a same-basis exact-head CURRENT PRICED result for this Finding.

## Mutations (all reverted, tree clean)

| Mutation | Result |
| --- | --- |
| Re-add the ELIGIBLE to PENDING rewrite in the seam | The stopped-schedule test fails. |
| `current_amount_permitted` ignores upstream reasons | Both new unit tests fail. |
| `current_amount_permitted` ignores the gate state | The permission-matrix test fails. |
| Ruling 5: composition wires `eligibility=None` | The new PG test fails (an assertion failure, not a setup error). |
| Ruling 5: a failed gate read returns ELIGIBLE | The new PG test fails. |

## Findings

### M1 (Medium): the authored withheld state now shows two lines for one span

- **Where:** `frontend/src/sites/FindingConsequence.tsx:447` and `:458`. The walkthrough is affected at `.agent/LR-01-owner-walkthrough.md:30`.
- **What is wrong:** the de-duplication key now includes `source`. The gate returns `series_limits = revision_limits + selected-window limits`. I probed the authored PG run with a temporary print, since reverted, and the withheld gate carries the same 07:05-08:00 `SEQUENCE_ORDER_INVERTED` span twice: once as `FINDING_REVISION`/`CUTS_TAIL` and once as `SELECTED_WINDOW` (with no relation). Before this round the key merged the two. The bridge now renders two list items for that one span: "...The finding ends before them..." and "...These records are within 6 hours of this finding...".
- **Why it matters:** the walkthrough tells the owner to expect "One line", but the screen shows two near-identical sentences about the same records. The copy is not untrue, but the merge-checkpoint walkthrough no longer matches the screen. The new frontend tests miss this because the authored fixture carries only the `FINDING_REVISION` limit.
- **Fix:** de-duplicate by `start|end|kind` again. Revision limits come first, so the more specific relation wording wins. Add a test that feeds the authored shape (the same span from both sources) and asserts exactly one `<li>` with the tail sentence.

### L1 (Low): precision of "some arrived out of order"

- **Where:** `FindingConsequence.tsx:408`.
- **What is wrong:** the sentence "The order of generator records from 07:05 to 08:00 is not proven: some arrived out of order" still attributes the late arrival to the 07:05-08:00 span. Pairwise it is defensible, because those records arrived before an earlier-measured record. The walkthrough adds a parenthetical that explains this.
- **Status:** optional. Wording such as "they arrived before an earlier reading" would be more exact.

## Checks run

- **Focused backend:** `pytest test_s4_schedule_upstream_unit.py test_lr01_money_eligibility_postgres.py test_s4_consequence_store_postgres.py test_s4_schedule_tick_postgres.py test_s4_consequence_read.py test_lr01_money_eligibility.py -n 2 --dist loadfile` on the private base `assetops_lr01fx_test`: **41 passed**, 130 s.
- **Full suite:** not rerun. I cite the implementer's run on this branch: 2186 tests, 1 failure, 671.9 s.
- **Claimed environmental failure: confirmed.** The failing test is `test_runs_api.py::...the_shipped_scenario_blocks_only_on_the_values_this_site_lacks`, the test the handoff names. It reproduces alone with `FileNotFoundError ...AssetOpsV1-review\var\sites\mg-001.yaml`. `git check-ignore` shows `.gitignore:6:var/`, no `var` files are tracked, and the file exists only in the main checkout. The diff does not touch `test_runs_api.py` or `var`.
- **`npx.cmd tsc --noEmit`:** clean.
- **vitest:** `siteFinancials.test.tsx` and `siteFinding.test.tsx` gave **69 passed**. The full `npm.cmd test` and the build were not run by me.
- **`tools/check-all.ps1`:** **all 9 guards passed**, including the Screen ledger. That guard ran through a temporary `.venv` junction to the main venv, which I have since removed. The main venv is intact.
- **Browser evidence:** not rerun (it needs Chrome and a dev server). The withheld screenshots predate this round, so they do not show M1's second line.
- **Cleanup:** I dropped `assetops_lr01fx_test` and no `assetops_lr01fx*` databases remain. The worktree is clean apart from this file.
