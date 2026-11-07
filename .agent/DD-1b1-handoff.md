# DD-1b1 handoff (keep current)

Branch `task/DD-1b1-story-time-actions`, worktree `AssetOpsV1-dd1b1`. Rulings: `build-sheet-DD-1.md` "DD1b1-R" (:1033).

## STOP-level item for the Architect (found while building)

DD1b1-R Q7's assert fails on v3: the objectives instant is S-26d 07:00 (2026-10-10 07:00 for prepare 11-07), and Kobo's first built day is S-28d (2026-10-08, start 03:00). Implemented literally as ruled (`demo_combined.objectives_instant` raises `OBJECTIVES_INSTANT_CONFLICT`), so **any full prepare stops at finish until ruled**. Not tuned.

## Disclosure

Two ad-hoc SQL checks called `pg_harness.fresh_database()` unrouted, which resets the shared base `assetops_test` in place. No pytest process was listed afterwards. The probe now refuses unrouted runs.

## Done (committed)
- `prepare_clock.py`, objective seam, `demo_declare_objectives.py`, `objectives_instant`, `coh3_pairs`, L0 and L2 tests (Q4, Q6, Q7): 8a478a6dd.
- Cold and EV story clocks, `demo_story_clock.py`, BUILD hook, R645 comment (Q1, Q2): 9f069966a.
- Probe `tools/dd1b1_coh3_probe.py`: 055c954cc and the next commit. R645 register closed: 2d6998e5b, conditional on the probe.
- Publication build check: `evidence_publication.recorded_at` reaches no route (ledger `_PUBLICATION_COLUMNS` used only for `content()`, `ORDER BY` :1100).

## Running
Probe in the background: output `var/dd1b1-probe/probe.json`, cap 20 min. Copy it to `.agent/DD-1b1-coh3-probe.json`.

## Next
1. Read the probe. Fail means stop and report, and revert the R645 closure if it does not hold.
2. Mutation proofs (invert the coh3 window test; drop the refusal in the objective store). Committed first, revert by `git checkout --`.
3. Scoped: `test_demo_story_days.py`, `test_ch1b_*`, `test_s6_verification_replay*`, `tools/checks/test_chain_coherence.py`, the two dd1b1 test files.
4. Guards A, W, N, V, M. Packet `.agent/review-packet-DD-1b1.md`.

## DBs / processes alive
Probe's run-owned DB (the probe cleans it up). Two keep-awake helpers of mine (PIDs 12084, 20492), which self-exit; never stop them.
