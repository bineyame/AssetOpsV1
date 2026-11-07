# Review: DD-1a2 (the B-22 day list)

Branch `task/DD-1a2-b22-day-list` at `2c033f6c8`, against `9b1c53ae3`. Reviewer: independent Claude, did not author the work.

## Verdict: REVISE

One High, routed to the Architect. Everything else in the slice stands: the data, the day list, the guards, G0, G1, MILL-3 and MONEY-A hold on the ruled tests. Nothing else needs rework.

## High

### H1. A live `steady` add-day on S+2 takes ACT-K1 off "Verified", and it does not come back
- **Where:** `tools/demo_story_days.py:483` (`plan_add_runs`), `ADD_DAY_KINDS` (`steady`); `backend/assetops_backend/actions/verification.py:1093-1095` (`current_state`: a later pin has no `facts_window`) and `:702` (the same in `_assess`). The packet's "R25 probe plus L0 cover it" (`review-packet-DD-1a2.md:18`) is wrong.
- **Scenario, measured.** I ran the Kobo child's own trial chain on S+0 and S+1 (own `*_test` DB), then `plan_add_runs` and the child's `add_day`, then the prepare's tick 3 times. ACT-K1 was read through the real `VerificationService.current_state`.

| Added day | After build and 2 ticks | After add, before tick | After tick 1, 2, 3 |
|---|---|---|---|
| `steady` on S+2 | VERIFIED | REASSESSMENT_PENDING (S3 stale) | **REASSESSMENT_PENDING all 3: "later_days: selection moved from run ... to ..."** |
| `normal` on S+2 (control) | VERIFIED | REASSESSMENT_PENDING (S3 stale) | VERIFIED all 3 |
| `steady` on S+3, S+2 empty | VERIFIED | VERIFIED | VERIFIED all 3 |

- **Cause.** `kobo-night-early` on S+2 starts at S+1 21:00Z, inside S+1's UTC-day window (R9's mechanism). A `normal` day starts at 03:00Z, in the bracket only, and the selected run did not change. The night's readings change S+1's selected run, and a later pin has no equal-facts rule (R9 gave that to baseline pins only: "the later pins keep their current rule"). The rule asks for a new later binding, and neither the tick nor add-day appends one.
- **Why it matters: what the client sees.** ST-7 is the live step, classed demo-critical (`DD1a2-R` Q8.3). The steady add is new in this slice, so this is a regression against `normal`. Read from code (`site_outcomes/board.py`, `mini.py`, `frontend/src/ui/productWords.ts:84`), not seen on screen:
  - the Action reads "New readings call for another assessment";
  - the Assure count loses the verified result and can read "No verified result yet";
  - the trial line falls to "Status changed; not attributed";
  - the Cost line does not get worse here: the probe's stored cost check is `MODELLED_NO_IMPROVEMENT`, so `board.py:505` reads as before. `COST_NOT_CREDITED` ("The trial did not fix the problem...", `board.py:65`) fires only on `MODELLED_IMPROVEMENT`, so it does not apply to this data.
- **The R25 gate does not catch this.** Its pass line (STOPPED, 0 starts) was met, and I reproduced it. It is a physics probe on a Foundation, with no Action or outcome on the Site. The S-10 fill path has no Action near it either. So the "not run" gap in the packet matters, and it should not wait for DD-1b2: the choice changes this slice's kind.
- **Fix: the Architect rules (a stop in the sense of this sheet, not the builder's call).** Options:
  1. **Product, narrow:** give later pins R9's equal-facts rule over `[later_start, later_end)` in `current_state` and `_assess`, with R9's unit checks. It keeps a full `steady` on S+2, and it touches a defended path. Any continuous real Site would hit this too.
  2. **Script and guard:** refuse `steady` on S+2 by name and add it on S+3 or later. Measured stable above, but S+2 then reads no data. S+3 ends at its 24:00, so with S at prepare day -2 the demo must be at least 2 days after the prepare.
  3. **Q8.3's own fallback:** after S+1 the kind runs 06:00-18:00 only and reads partly checked. Not tested here. It starts at 03:00Z like `normal`, so it is likely to recover, but that needs the same probe.
- **Whichever is chosen:** one L2 check holds the state: ACT-K1 VERIFIED before and after the live add plus the ticks. The reviewer's scratch probe (not committed) shows the shape; each run took about 5 min.
- **Limits of the probe:** two story days plus the add, not the whole build; the state is read at the service, not on the board.

## Medium
None.

## Low, not blocking
- **L1. Owner's Q1 said "a line on screen says so" about the 06:00 battery step.** The disclosure reaches only `purpose`, shown on the Lab scenario pages (`ScenarioFrame.tsx:240`, `ScenariosFrame.tsx:132`). `# label:` and `# source:` are YAML comments and are not served. I found no such line on Site routes by search. `kobo-mill-midday`'s purpose carries only "can jump at a segment edge", as ruled (comment-only). The file requirement is met, so this is not a code gap. Fix: add the correction to the coordinator's R2 owner line, and a demo-script line.
- **L2. MONEY-A: the comparison is honest but narrow, and the packet explains the zero wrongly.** `review-packet-DD-1a2.md:46` ties 0 USD to the price seed. The rows carry price 1.25 USD and quantity 0 L: the generator delivers no power in the Candidate span, so 0 is computed. See "Decisions asked for". Fix: correct that line.
- **L3. Lab purpose text carries system words:** `kobo-night-handover-v1.json`, `(DD1a1-R16)`, "segment edge", scenario ids. `kobo-night-early`'s "after a steady sunny day: the start state is what that day leaves" is untrue on S-20, S-13, S-9 and S-6, where it is the fresh declared start. Lab pages only, same pattern as existing files. Backlog.
- **L4. Evidence claims I could not check from the files:**
  - `DD-1a2-addday-l2.json` is the rerun: 1 `received_at` value and no plan text, so "3 distinct `received_at`" is not in it (L0 does prove the plan's three stamps);
  - "cited evidence equal" for S-14 and S-7: the report drops that field;
  - "on 10-23 and 10-30": revision times are not stored in the report.
- **L5. R25 test:** the night's "no generator" is printed, not asserted (`test_dd1a2_r25_probe.py:47`). I saw it print `generator []`, ends 31.16 %. The gate's "no Finding" is not measured by a probe.
- **L6. Guard gap:** `check_mill_side` does not tie `mill_change_day` to the `mill-midday` entry, so moving only the entry passes. The ruling did not ask for it. Backlog.

## Decisions asked for

**Scenario files: correct.** Value by value against the parents, by script:
- `kobo-steady-before-mill` differs from `kobo-daytime@2` only in mill windows 2-6 (0, 0, 0, 18, 3 against 15, 18, 10, 12, 0; window 1 is 0 in both). The packet's "six windows" is the ruling's wording.
- 0 kW comes from the reserve-trial's one 06:00-14:00 window (`:176`); 18 and 3 from the evening's 14-16 and 16-18 (`:398`, `:422`). Source lines resolve. Start 55 %, 300 L, STOPPED.
- The composition is the frozen one, unchanged after G1. No value moved to pass a gate.
- `kobo-rest-before-mill` and the night equal their siblings' timelines; their starts are the measured 86.316 and 45.263.
- `kobo-steady-day` equals `kobo-mill-midday`. The `kobo-mill-midday` diff is comment-only. v1 and v2 are unchanged.

**`demo-story-days-v3.json`: matches the DD1a2-R table.** 13 / 6 / 3; S-4 and S-2 absent; Cold 3 story days; EV adds S-14; `mill_change_day` S-9.

**`DEFAULT_FILE`:** consumers checked by search. The real exposure is `test_demo_combined_postgres.py`, whose fixture now prepares all of v3 (already owed to DD-1b2). Its SP-7 `late` add on S+2 is not refused by the new guards (by reading). Finish rows are unrun.

**Guards: each can fail on a realistic wrong list, and no bound weakened (0.5 pp / 0.5 L).** The L0 mutations cover: 48 % after 45.26 % (`FULL_DAY_JOIN_BOUND`), `steady-before` after a story-only day (`FULL_DAY_JOIN_UNMEASURED`), a wrong rest or night (`FULL_DAY_CHAIN_UNMEASURED`), each wrong side, `LATE_IN_STREAM` on S-4 and S-2, degraded without a complement. `FULL_DAY_JOIN_NOT_STOPPED` is unchanged.

**0.973 L: a real measurement, of the model, not of evidence.** It is the fuel stock change in the registered-Site probe, which I reproduced (299.026875 L end, generator 04:00-06:00). No fuel signal reaches evidence, as the G1 signal list shows. 3.167 kWh in evidence is an independent reading of the same interval. "About 6.8 L" is 7 x one probe, and the packet says so.

**MILL-3: no shortcut found.** Real gateway acceptance on the registered Site, the real snapshot builder and reader, the real `assess`. 42.000 and 110.000 are what the windows give (2 x (18+3); 2 x (15+18+10+12)). Baseline 10-23..25, later 10-28, 30, 31 by grade. The plan is in memory, as ruled. Two differences from the stored-outcome path, both owed to F-THREADS: `reader.latest` has no `known_at`, and the stored evaluator was not run.

**MONEY-A: passes the ruled test, but does not prove "the same money" in the owner's sense.**
- It shows no new fuel-cost row on a steady, `steady-before` or mill day, and equal rows on S-14 and S-7. That is real: a row or a non-zero quantity would have shown.
- It compares 0 with 0, and every non-zero figure is outside it (Grow sales on the new days, WK-2a's 42.08 USD).
- So tell the owner: "no new fuel cost anywhere on the test build; the two problem days still show no fuel cost estimated". MONEY-B stays required before E3, and the R2 line's "isn't proven yet" stays true.

**3 revisions vs 1: a client can see it; it does not threaten the demo.**
- **Cause (from code and R9):** the next full day's night falls in the Finding's UTC window and its 03:00-06:00Z falls in the 6 h bracket, so 2 re-runs each. Bounded by the neighbour, and consistent with R9's "honest data". This is inference: the report does not store revision times.
- **Visible:**
  - Finding history lists Version 1 Opened and Versions 2-3 "Assessment updated; amount unchanged";
  - the Site Findings index shows that small label under the state (`SiteFindingIndex.tsx:604`);
  - the consequence history lists 6 rows instead of 2, stated as "none is added up".
- **Not affected:**
  - thread occurrences and recurrence counts (`_PLACED` keys on `finding_id`, so a revision is a NOOP);
  - Finding counts, claim and minutes;
  - money (nothing sums revisions; `estate_total` is null).
- The wording is true. A demo-script line is enough. Not on screen in this review.

**Disclosure:** text matches the measurement (04:00, 30 %, about 1 L). Nothing says the mill change saves fuel. See L1 and L3.

**Scope:** `missing` day (BL-10) not built, BL-23 to BL-25 only recorded. The five HELD files are gone, `--check` fails if one returns, no test or conversion other than the handover history names them.

## Checks I ran
| Check | Result |
|---|---|
| `test_demo_story_days.py` | 76 passed |
| `test_demo_combined_finish_co1.py`, `test_demo_combined_links.py`, `test_dd1a1_r9_baseline_facts.py` | 24 passed |
| `host/tests/test_dd1a2_registered_kobo.py`, `test_dd1a2_r25_probe.py` (own DB) | 2 passed, 35 s; states equal the packet |
| `derive_steady_scenarios.py --check`, `probe_kobo_nights.py --check` | current |
| `tools/check-architecture.ps1` | first run failed: no guard Python in this worktree (environment, not the slice); with `ASSETOPS_GUARD_PYTHON` set, passed |
| `tools/check-agent-workflow.ps1` | passed |
| Add-day probe, 3 runs (reviewer script) | table in H1 |

DB `assetops_dd1a2rv_test` created and dropped. No code edited.

## Not verified
- The G1, G2 and MONEY-A JSONs were read and checked for consistency, not regenerated (per the brief).
- Anything on screen: board, history and index text are read from code. Layout evidence does not apply (no frontend file changed), and `npm test`, build and `tsc` were not run for the same reason.
- Guards N, V, M were not run. The full suite, a prepare and `test_demo_combined_postgres` were not run (barred by the brief).
- Whole-build behaviour: the finish rows on v3, and how much Grow and spare-solar figures move on the new days. Both owed to DD-1b2.

## Re-review (DD1a2-R3)
**Verdict: ACCEPT.** H1 only, `git diff 66115ca05...432a07d87`. No High or Medium.

1. Guard: `plan_add_day` (`tools/demo_story_days.py:464-468`) fires for kobo, a kind with `complement`, offset = `trial-after` offset + 1, after `check_mill_side` and before any expansion, `DAY_NOT_IN_PAST` or provisioning. It is relative to the stored `trial-after` entry, so it holds for any S. `plan_add_runs` calls it first, and `demo_combined.add_day` (only caller, reads stored `days.json`) goes through `plan_add_runs`; I found no other add path or argument that bypasses it. `normal` S+2, `steady` S+3+ and the `steady-before-first` S-10 fill are untouched (L0 asserts each). Low: other complement-less kinds (`overuse`, `overcast`, `late`) on S+2 are not guarded and not measured; outside the ruling.
2. Moved test (S+2 to S+3, `now` shifted, all assertions shifted equally, the `normal` S+2 and DAY_NOT_IN_PAST assertions kept) is legitimate; nothing weakened.
3. L2 proves the chain it names (VERIFIED, then REASSESSMENT_PENDING, then VERIFIED x3, guard leaves reading count unchanged). Real timing differs: the live add happens right after S+2 ends, so received_at is much closer to the S+2 window than here (a day later). Not measured; the cause (S+1's selected run changing) is independent of delay, so this is residual risk, correctly owed to DD-1b2/EX-1. Low: REASSESSMENT_PENDING between add and tick 1 is a designed read state (Architect A-S6 answers: "late accepted readings immediately mark REASSESSMENT_PENDING and withdraw Verified presentation"); a client viewing the board in that gap would see it. Neither the DD1a2-R3 script lines nor a rule covers it: EX-1 should add "tick right after the add (or `--assess-now`) before showing the board".
4. Packet `:18` and `:46` now state the truth and match the ruling.

Checks: `test_demo_story_days.py` 77 passed (1.7 s). Not run: the 224 s L2, mutation check, guards, any DB.
