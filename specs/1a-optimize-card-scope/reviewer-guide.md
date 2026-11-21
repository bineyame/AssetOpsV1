# 1a reviewer guide

For a fresh Claude reviewer. Read the spec §1 to §5 and `rulings.md`. Cite the builder's gate run at the same commit,
and rerun only what a finding needs. Standard review (W5). Screen unit: say ACCEPT or not; do not merge (the merge is
held for the owner's walkthrough).

## What to check

1. **Pin before change.** Commit 1 has only tests, P1 to P4, and they pass on its parent. P4 is the only pin commit 2
   edits, and commit 2's message says so.
2. **One figure.** The card's `value` and `claim` equal what `test_ch5d1_optimize_card.py` expects, byte for byte. The
   scope sentence holds no amount (S7). No total exists anywhere in the card (`test_two_priced_sites_list_each_and_never_sum`
   still passes).
3. **Words.** Every new served word is in `portfolio_card.cost_scope`. Each of the six variants has a case with exact
   English. `chain/vocabulary.py` and both statement baselines are unchanged (`git diff main -- tools/checks
   backend/assetops_backend/chain/vocabulary.py` is empty).
4. **Facts.** `CostScope` is filled in `_summary` from `summary_window`'s basis and `window_days`, per Site. No date is
   computed in the browser.
5. **Screen.** The scope line sits after the figure and before the sentence, on the Optimize card only. Check the
   captures at 1440 × 900 and 390 × 844, and the register row for MD-1A-1.
6. **Guards.** Fast check-all is green, including the statement catalogue guard. COH-17 O1 returns `[]` on the new
   cards (S9).

## Plants (each alone, reverted; each must fail the named test)

| # | Plant | Must fail |
|---|---|---|
| PL1 | In `_summary`, set every Site's scope day to `lo`'s date instead of `b_day` | S8 |
| PL2 | In `cost_scope_text`, treat `n == {30}` as ONE_DAY | S1 |
| PL3 | Put the claim's `text` into the statement as a `name` slot | S7 (and the catalogue guard, if the slot is undeclared) |
| PL4 | Delete the `each_differ` case | the statement catalogue guard (`CASE_MISSING`) |
| PL5 | Render the scope line on every card | F3 |
| PL6 | In commit 1's tree, change `window_day` rule 3 to return `lo`'s date | P1 |

## Not in scope

The period figure (`7g`), `1b`'s hidden fields, the Grow card, how the lead Finding is chosen.
