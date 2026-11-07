# Re-review: DD-1b2b fix round (M1, M2, L1, L2, L4, R14 asserts)

Reviewer: fresh Claude (Opus), re-review of named findings only. Branch `task/DD-1b2-finish-rehearsal` at `350b33dba`; diff `851c94f3d..HEAD` (fix commits `28bb723d0`, `2c2f49e8b`, packet `350b33dba`). Rulings: DD1b2-R13, R14. I edited no code, wrote to no DB, ran no prepare, tick, add-day or suite.

## Verdict: ACCEPT

No High or Medium finding. Two Low notes below, neither blocks.

## Per finding

- **M1 (COH-17): closed as R13 section 1 ruled.**
  - `tools/demo_combined_rows.py` `_coh17_mill_recurrence`/`coh_split` allow a COH-17 only when `recurs`, `site_code` is None, `subject == "L3"`, window is week or month, and the detail matches "n distinct Verified threads in the table, claim m" with n - m == 1. At most one per window (`taken`). The entry carries `reason` (with CH6b3-R4) and `owner` BL-07.
  - All eight must-fail L0s are in `test_demo_combined_finish_rows.py` (recurs False, window S, n-m==2, site-less summary, site-less window, KOBO-001 site code, second L3 on a window, plus a non-COH-17 rule). Each asserts the finding lands in `faults`, so each would fail against the old code (the old rule allowed site_code None or KOBO-001 with any detail).
- **M2 (owed items): closed.**
  - O8 clone half, `var/demo3_dd1b2d/after.json` (s2_mode true, failed []): study OPP-000005 ends 2026-11-07, UNKNOWN, 0 eligible; thread events unchanged with the single RECURRED effective 2026-10-31 and no WITHDRAWN or CLOSED; `o8_assure_unchanged` compares S-5, S-1, S+0, S+1 against the dd1b2 reference and S+2 reads WATCH "1 verified result"; Portfolio Grow `open_findings` 1 on week, month, week_s2, month_s2; S+2 renewable selections 6. All match the packet.
  - O12: S-8 potential "No potential found yet" with contributor "Spare solar on 4 of 4 well-observed days"; S-5 per R14. Present in both after.json files.
  - "Why?" price line S-11: "42 kWh × 0.25 USD/kWh", money 10.50 = 42 x 0.25. Pass, asserted against the stored selection price.
  - ACT-002/003 "Action agreed": Cold ["Action agreed","Open"], EV ["Action agreed"]. Asserts.
  - O16 moved into asserts: 11 rows, S-14 4, S-7 4, S+0 3; each on a story day, none on a steady day; pure function has five must-fail cases.
  - O19 statement is quoted in the packet. MG-2 and earnings are closed by citation.
  - Items moved to E3 each name a step: known_at links report E3.2 (also run now: 4 listed); Portfolio Cold/EV landing E3.2 (also reported now: 17 paths); post-add COH-17/CO-2 E3.3; O13 browser path E3.4; perf_budget `--record` with NOT MEASURED routes named E3.5. Nothing silently dropped.
- **L1 (EX-1): closed.** `exit_code` returns 1 on a failed compare, `after_not_available`, or a missing comparison. `counts` is read, and `in_hand_items` is a whole-item key in O9_KEYS. Three new L0s have must-fail arms (including an in_hand text change with no "trial"/"ACT-").
- **L2: closed in substance.** Both after.json runs used the committed tool; I confirmed `tools/demo_combined_after.py` is byte-identical to the copies in `var/demo3_dd1b2/tree/tools/` and `var/demo3_dd1b2d/tree/tools/`, and the same for `demo_combined_rows.py` on dd1b2d. O16 is now an assertion (the missing MONEY-B gate). The packet notes the lineage. Perf record moved to E3.5 as ruled.
- **L4: closed.** `l4_action_index_cold/ev` read the Site-local day and its week through `domain-work/action-index`, assert at least one row and the right Action code. Evidence: 1 and 1 on both Sites.
- **R14 S-5: implemented as ruled.** `o12_s5_grow` requires the potential to start "Not judged yet", no `kW` token, no money on node or chip, spare solar seen; thread label is report-only. Evidence: "Not judged yet: 4 of the 5 study days have no reading", label "Seen again". L0 has four must-fail arms (old text, kW figure, bad solar, money).
- **R14 Cold "Why?": implemented as ruled.** `protect_names_threads` fails if ACT-000002's thread (resolved from the chain's `actions` entry, not hard-coded) is not named; the other thread is recorded "BL-50 known gap: not named". Evidence: `aacec8fa` named, `b13f2110` recorded as the gap, text "ACT-002 · Open · linked finding outside this view". L0s cover both the recorded gap and the failing case.
- **BL-50** row is in `.agent/backlog-post-demo.md`. **R14's DS-1 lines** (S-8, S-5, Cold Room, and the "if a client opens it" sentence) are in the packet, with the DS-1 source index.

## Low notes (not blocking)

- L-a: `.agent/DD-1b2b-rehearsal.json` carries no O10 output (R13 section 3 L2(b) said O10's output goes there). The packet records the O10 result in prose and names the scratch script; the claim was verified in the first review. Optional.
- L-b: `action_agreed` checks that "Action agreed" is among each Site's thread labels, not that the label sits on the ACT-000002/003 thread. R14 section 3(b) said "tighten if cheap"; the Cold protect assert is properly keyed, so the residual gap is small.

## Checks run
- `backend/tests/test_demo_combined_finish_rows.py` + `test_demo_combined_ex1.py` (plan2 venv, absolute worktree PYTHONPATH): 36 passed in 0.35 s.
- Read both `after.json` files in full for the asserts above (exit state: `failed: []` on both).
- Byte compare of the tree-copied tools against HEAD.
- No SQL was needed; the evidence files carried what the claims rest on.

## Not verified
- The after tool itself was not rerun (not permitted); the pure functions are covered by L0s, the live reads rest on the two after.json files.
- Frontend/guards untouched by this round and not run.
