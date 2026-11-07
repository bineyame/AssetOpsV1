# DD-1b1 packet: NOT READY FOR REVIEW. Stopped on the Q6 probe, for the Architect

Branch `task/DD-1b1-story-time-actions`. Rulings: `build-sheet-DD-1.md` "DD1b1-R". Probe output: `.agent/DD-1b1-coh3-probe.json` (first run, 231 s; cap 20 min). Per Q6 "Fail: stop and report": no product code, clock or threshold was changed to pass it.

## Stops needing a ruling

**S1. EV: no COH-3 pair is possible with the ruled instants.** The EV day board window is `[08:00, 09:00)` (`chain_coherence.day_windows`, an EV day is its `[start, end)`). Action `raised_at` is 09:40 per Q2. COH-3 needs `created <= to`, so the pair never qualifies, and the board reads `known_at` 09:00, so `in_hand` lists only PM-009. The Finding itself is created at 09:35, and evidence is decided at 09:00 and 09:05, so no instant after the evidence can be at or before 09:00. Q6's "`coh3_pairs` >= 1 for EV-LAB-001", "S+0 board's `in_hand` lists the Action" and the R645 closure cannot hold on this window. The collector's other EV reads were not examined for a wider window.

**S2. Cold: the day board shows no Finding, so no pair.** Board window is the local day, `known_at` 17:05 (the evidence cutoff). Findings and selection are at 17:10 (Q1, Q2).
- Protect is `UNKNOWN`, not `NEEDS_ATTENTION`; contributors read "Not available yet · no backup start in this window".
- `in_hand` does list ACT-001 and INC-001, but as "Open · linked finding outside this view".
- **Cause not proved.** A `known_at` earlier than the Finding is the leading reading. The other candidate is the local-day window itself: finish reads Cold on `[start, end)` (`demo_combined_finish.py:343`), the collector on the local day. The log also says "contained windows for COLD-LAB-001 fell back to the requested window (EstateRefusal)".
- A control run with the story clock off would attribute it (about 4 min). Not run: it needs a probe flag, and this unit is stopped.

**S3. Q7's assert fails on v3.** The objectives instant S-26d 07:00 (2026-10-10 07:00 for prepare 11-07) is later than Kobo's first built day, S-28d (2026-10-08, start 03:00). `objectives_instant` raises `OBJECTIVES_INSTANT_CONFLICT` as ruled, so **any full prepare now stops at finish until this is ruled**. Found by resolving v3; prepare not run. L0 covers both branches on synthetic stories.

## What the probe did prove (real child `build` paths, own routed DB)

Cold 14 s, EV about 15 s, backfill 3 s, three ticks about 158 s. Passing checks:
- Cold Action `raised_at` 17:15:00, `recorded_at` 17:15:01. EV 09:40:00, 09:40:01.
- Cold COMPLETE `occurred_at` 16:42, `recorded_at` 17:11:04. Findings at 17:10 and 09:35.
- Both linked threads `ACTION_IN_HAND`, no `CHANGE_APPLIED`. `ACTION_APPLIED` skipped `ILLEGAL_TRANSITION` from OPEN. Further ticks wrote 0 thread events.
- `doc["blocked"]` null, WR COMPLETE stored, 0 COH-3 findings (vacuous here: 0 pairs).

Five checks failed: `pairs.cold>=1`, `pairs.ev>=1`, `board.cold.in_hand_lists_action`, `board.ev.in_hand_lists_action`, `cold.protect.NEEDS_ATTENTION`.

**Probe defect:** the two `in_hand` checks read a top-level `in_hand`; it is per row. Fixed after the run and **not re-run**. On the bundle, Cold's would pass and EV's would still fail. `probe.json` keeps the first run's `false` values.

## Acceptance (DD1b1-R :1178)

| Item | Status |
|---|---|
| ACT-002, ACT-003 at story time per Q2, threads ACTION_IN_HAND | Proved by the probe |
| ACT-002 case linked, COMPLETE recorded, no change applied | Proved by the probe |
| COH-3 evaluates >= 1 pair per Cold and EV board | **FAILS: 0 pairs (S1, S2)** |
| Objective override refused outside `assetops_polish_*` / `*_test`; children behind the same check | L0 for the store; children call the helper (`worker_instant`, `story_commands`), no direct refusal test |
| Unset byte-unchanged | L0 statement text; L2 set and unset. **Instant conflicts on v3 (S3)** |
| Add-day unchanged | By construction (`story_clock` defaults off; EV `story` is None on add-day). No run |
| Q4 pin | L2, EV and mini, set and unset (5 passed in that file). The trigger pin writes dispositions through the existing fixtures, with `decided` taken from the ledger's `_decision_instant`, not a full ledger submit |
| R645 closed | **Withdrawn:** closure reverted, since the EV board does not list the Action (S1) |
| Publication not built (BL-30); no route carries its date | Grep of ledger and evidence modules: `_PUBLICATION_COLUMNS` used for idempotency only, `ORDER BY` :1100 |

## Disclosures

- **Shared DB reset.** Two ad-hoc SQL checks called `pg_harness.fresh_database()` unrouted, which resets the shared base `assetops_test` in place. No pytest process was listed afterwards, but I cannot rule out an effect on another lane using that DB. The probe now refuses unrouted runs.
- **Earlier guessed password.** In the pre-flight, one guessed password failed against Postgres. Everything since uses the configured `demo_combined.PW`.

## Known deviations

- `_coh3_evaluate` holds COH-3's one loop, and `coh3_pairs` plus `coh3_action_on_board` both read it. The ruling named one generator; the rule needs each Action's `file`, which the five-tuple does not carry.
- `.ai/CODE_STATE.md` and `.ai/ACTIVE_CONTEXT.md` not updated: no DD unit has entries there, and the unit is stopped.
- `demo_declare_objectives.py` and the `finish` change were never run end to end (prepare barred, and S3 stops it).

## Not run

Guards A, W, N, V, M. `test_ch1b_*`, `test_s6_verification_replay*`. Mutation proofs (coh3 window, refusal). Re-run of the probe after the `in_hand` fix. Control run for S2. Any demo prepare or full suite.
Run: `test_demo_story_days.py`, `test_dd1b1_prepare_clock.py`, `tools/checks/test_chain_coherence.py`: 201 passed. `test_dd1b1_story_clock_postgres.py`: 5 passed.

## User review

Not applicable yet. The next step is an Architect ruling on S1, S2 and S3.
