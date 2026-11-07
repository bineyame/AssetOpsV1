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
