# DD-1b2a handoff

Branch `task/DD-1b2-finish-rehearsal`, worktree `AssetOpsV1-dd1b2`. Rulings: `build-sheet-DD-1.md` DD1b2-R and DD1b2-R2. Packet: `.agent/review-packet-DD-1b2a.md` (full results).

## State: STOPPED at P1 (LIMITED, SOURCE_CLASS_MIXED) for the Architect and owner

- R2 fix landed (`8589bc527`) and proved: M0 (`.agent/DD-1b2a-m0.json`) confirmed the cause; M1 (`DD-1b2a-m1.json`) passed all four conditions.
- Re-probe (`e513401e0`, DB `assetops_demo3_dd1b2p_test`, work `var/demo3_dd1b2p`): all 13 full days have no missing hour; the pinned study is **LIMITED with 5 eligible days**, limitations include `SOURCE_CLASS_MIXED`. Read: `source_provenance.py:23` makes any set from several runs MIXED, and a full day is three runs. P2 recorded the Action; P3 grades right; the mill tool then stopped on its own literal bug ("FULL" vs `COMPLETE`), fixed in the working tree/commit after, not rerun. P4 to P7 not run. Evidence `.agent/DD-1b2a-probe-2.json`, `-seam.json`.
- The R2 section 3 owner question names the wrong rule (hours are fixed; the rule is provenance). See the packet.

## R3 update (2026-11-07)

M2 and R3 section 4 ran on the clone `assetops_demo3_dd1b2q_test` (kept; it is now post-mill, no longer pre-mill). M2: MIXED with exactly `MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS`, 10 runs, snapshot/foundation v15/binding set v14 equal, `run_identity_sha256` differs per run; in-memory figure SUPPORTED, 0-2 kW over 3 daylight hours (low bound 0). Mill step: ACT-000002 VERIFIED, 42.00 -> 110.00; P2-P5, P7 pass; P6 matches "does not recur" (no "Seen again", 0 stuck events). Option (b) not built; owner question pending. Results: packet section "DD1b2-R3 results"; evidence `DD-1b2a-m2.json`, `DD-1b2a-probe-3.json`. The steps below are done.

## Resume after the ruling (done)

The clone `assetops_demo3_dd1b2q_test` (+ `var/demo3_dd1b2q`) is the state before the mill step. On it: `tools/demo_combined.py --db assetops_demo3_dd1b2q_test --work var/demo3_dd1b2q after-children`, then `tools/dd1b2a_probe.py ticks --db ... --work ... --out .agent/DD-1b2a-probe-2.json` (never run). The work folder's `tree` is the archive of `e513401e0`, so it does not contain the mill-tool literal fix: re-archive (new prepare) or copy `tools/demo_combined_mill.py` into the tree first.

## Own DBs

Kept: `assetops_demo3_dd1b2p_test`, `assetops_demo3_dd1b2q_test`. Dropped: `dd1b2m`, `dd1b2n`, `assetops_dd1b2t_test`.
