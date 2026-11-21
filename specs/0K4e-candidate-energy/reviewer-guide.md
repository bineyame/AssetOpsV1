# 0K4e reviewer guide

Architect (Claude), 2026-11-21, rev 1. Discovery review (W5): a served classification that bounds money and litres.
Read `spec.md`, D-0K4.10 in `specs/0K4-dispatch-model-review/rulings.md`, `backend/tests/dispatch_3_decision_table.md`,
then the diff. Done means every question of spec §6 answers yes with evidence and every plant fails its named test.

## What to check, and how

1. **The rule, by hand.** Recompute E1-E3 yourself (need = load less PV over the walk at 5/60 h a slot; held = (SOC -
   reserve) / 100 x capacity x efficiency / 100; Candidate iff held >= 1.1 x need). A test whose expected value comes
   from calling `energy_to_cover` is High (W2).
2. **Only the branch moved.** Diff `_evaluate`: the battery-support branch and nothing else; E8 green with only version
   literals changed; the PV-alone branch, the Necessary rules, the 10-point SOC rule and the minimum-runtime
   withholding unchanged.
3. **No extrapolation.** `energy_to_cover` holds a mean over its own interval only; a gap or the read range's end is
   Indeterminate, never zero need (owner rule: unknown is never zero).
4. **Version discipline.** 3.3 in `MODEL_VERSION`, so every `input_sha256` and `basis_sha256` changes; E9 shows 3.2
   history intact; the decision table row matches the code.
5. **The sweep (W6).** Every `dispatch-3.2` hit is in the packet's table with its class; spot-check three. A pin left at
   3.2 that a consumer uses to select current runs is High.
6. **Downstream honesty.** E10: 4d's total litres unchanged, candidate not larger. Read `finding_service.py`'s
   selection quote: the Findings follow the default selection, not a literal.
7. **Served text.** The new reasons sit on the same lists as the existing ones; the SC-1 scan passes on the file without
   a new allow entry, or the packet shows the mid-build ruling.
8. **Databases.** Only `*_test` databases in the logs; no reconcile pass run on a demo database.

## Plants (each must fail the named test; revert after)

| # | Plant | Must fail |
|---|---|---|
| P1 | the energy test skipped (3.2's branch) | E1 |
| P2 | headroom dropped (`held >= need`) | E3 |
| P3 | efficiency ignored | E3 (its edge cases are built at 95 %) |
| P4 | a missing reading treated as 0 load | E4 |
| P5 | a 15-minute mean held for 5 minutes only | E5 |
| P6 | the walk stops at the window end, not the read range end | E6 |
| P7 | the energy test also applied to the PV-alone branch | E7 (PV-alone still Candidate with no capacity) |
| P8 | `MODEL_VERSION` left at 3.2 | E9 |
| P9 | `SUPPORTED_MODELS` without 3.3 | E10 |

## What counts as done

All of spec §6 yes; P1-P9 each fail; the sweep table complete; mid-build count 0.
