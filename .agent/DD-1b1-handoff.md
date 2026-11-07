# DD-1b1 handoff

Branch `task/DD-1b1-story-time-actions`, worktree `AssetOpsV1-dd1b1`. **State: stopped on the Q6 probe; awaiting Architect rulings on S1, S2, S3 in `.agent/review-packet-DD-1b1.md`.** Rulings so far: `build-sheet-DD-1.md` "DD1b1-R" (:1033).

## Done (committed)
- `prepare_clock.py`, objective seam, `demo_declare_objectives.py`, `objectives_instant`, `coh3_pairs`, L0 and L2 tests.
- Cold and EV story clocks (`tools/demo_story_clock.py`, `run_day(story_clock=)`), BUILD hook, R645 comment in `demo_combined_ev.py`.
- Probe `tools/dd1b1_coh3_probe.py` (`in_hand` check fixed after the first run, not re-run). Report: `.agent/DD-1b1-coh3-probe.json`.
- R645 register closure reverted: the EV board does not list the Action. The comment at `demo_combined_ev.py` `declare_and_work` still says "closes R645"; correct it when S1 is ruled.

## Resume after the rulings
1. Apply the rulings; re-run the probe. Set `PYTHONPATH` with `tools\checks` added: `python tools/dd1b1_coh3_probe.py <repo>\var\dd1b1-probe` (about 4 min).
2. Mutation proofs (invert the coh3 window test; drop the refusal in the objective store), on committed work.
3. Scoped: `test_ch1b_*`, `test_s6_verification_replay*`. Guards A, W, N, V, M.
4. Close R645 if it holds; turn the packet into the review packet.

## DBs / processes alive
No probe DB expected (the probe cleans up its own run; not separately verified). Keep-awake helpers of mine (PIDs 12084, 20492) self-exit; never stop them. Scratch `var/dd1b1-probe` is git-ignored.

## R2 update
Committed: actions_to read fix (read.py/cold.py/ev.py), whole-UTC-day story_links + chain_coherence.day_windows, `objectives_instants` + per-Site `demo_declare_objectives.py <url> <file> <site> <iso>`, L0s, probe adapted (1 tick, extra reads, judge_r2), BL-33 -> BL-38, R645 comment. Re-probe started: `var/dd1b1-probe/probe.json`. Then: guards A,W,N,V,M; test_ch1b_*, test_s6_verification_replay*, test_ch6b1*, test_ch6b2*; mutation proofs; packet.

## R2 re-probe: FAILED, stopped for the Architect (report `.agent/DD-1b1-coh3-probe-r2.json`, DB assetops_pt3ef499e7_dd1b1_test, dropped)
Passed: objectives_instants (Kobo S-29d 12:00, Cold 06:30, EV 07:00) on v3; Cold/EV objectives declared per Site; chain_site "Action agreed" both; Protect Needs attention; Finding in issues on UTC day and event window; 0 thread events; all earlier instant checks.
Failed: coh3_pairs = 1 per Site but both unlinked (2 COH-3 findings); Action NOT in "in hand" on the UTC day (Cold lists INC-001 "Open", PM rows; EV lists only PM-009) or the event window (expected absent there). Cold local day lists ACT-001 as "Open · linked finding outside this view" (window known_at 17:05 also).
Unverified hypothesis: when an event is found, the cutoff `known_at` = event end (09:00 / 17:05) and `actions_in_window` has `recorded_at <= :k` (postgres_domain_action_index.py:~78), so an Action recorded after the event is excluded regardless of `actions_to`. DD1b1-R2 S1 said known_at is not the cause; the UTC-day result contradicts that.
Not run after the failure: guards W,N pass, V,M pass, A passes (after prepare_clock lost its sqlalchemy import); test_ch1b_*, test_s6_verification_replay*, test_ch6b1*, test_ch6b2*, mutation proofs, review packet (stays NOT READY), R645 stays open.

## Review fix round (H1, R645, Lows): DONE. See "Review H1 closure" in the review packet; owed list there now includes DD1b1-R, Q5 and R4. L2, L3 left open.

## R3: DONE. Re-probe passed 49/49 (`.agent/DD-1b1-coh3-probe-r3.json`), main merged, R645 closed, packet written (`review-packet-DD-1b1.md`). Nothing left for this unit except review; DD-1b2 owes list is in the packet.
