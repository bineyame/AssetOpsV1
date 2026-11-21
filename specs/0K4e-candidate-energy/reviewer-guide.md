# 0K4e reviewer guide

Architect (Claude), 2026-11-21, rev 2 (handshake answered: D-0K4.19, D-0K4.23, D-0K4.24). Discovery review (W5): a served classification that bounds money and litres.
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
   Indeterminate, never zero need (owner rule: unknown is never zero). E5b decides the fallback's convention at the
   one slot where it matters (a slot that starts a mean's interval with no reading ending at it).
3b. **Cost.** The recurrence is memoised per slot (E8b); E9's wall times on 3.2 and 3.3 are in the packet; above 2x is a
   mid-build question that should have been asked.
4. **Version discipline.** 3.3 in `MODEL_VERSION`, so every `input_sha256` and `basis_sha256` changes; E9 shows 3.2
   history intact; the decision table row matches the code.
5. **The sweep (W6).** Every `dispatch-3.2` hit is in the packet's table with its class; spot-check three. A pin left at
   3.2 that a consumer uses to select current runs is High.
6. **Downstream honesty.** E10: 4d's total litres unchanged, candidate not larger. Read `finding_service.py`'s
   selection quote: the Findings follow the default selection, not a literal.
7. **Served text (D-0K4.19, D-0K4.24).** The branch adds nothing to `reasons` or `missing`; the outcome is the
   `energy_cover` entry, codes and `_num` strings only. Both readers render `dispatch.energy_cover` or
   `dispatch.energy_cover_cause`; each variant has a hand-literal case. `git diff main -- tools/checks/` shows only
   the one version-token swap the packet lists (old and new fingerprint for `rows_mini_grid.py`'s `unexplained_l`
   source), and the diff of that string is the token only. Any other baseline or allow change is High.
7b. **Readers.** A 3.3 Indeterminate segment never reads "too close to decide" (plain) or "does not say why"
   (findings) when its cause is the energy test (E12, E13). Role coverage stays per instant (E14).
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
| P10 | the fallback swapped to `interval_start <= s < interval_end` | E5b |
| P11 | the walk's memo dropped (each point walks its own lookups) | E8b |
| P12 | an energy-cover outcome appended to `missing` as text | E1 (nothing added to `missing`) and the statement guard |
| P13 | `plain._segment` ignores `energy_cover` | E12 |
| P14 | `portion_cause` ignores `cover` | E13 |

## What counts as done

All of spec §6 yes; P1-P14 each fail; the sweep table complete; mid-build count 0.
