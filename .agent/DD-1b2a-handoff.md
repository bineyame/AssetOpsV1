# DD-1b2a handoff

Branch `task/DD-1b2-finish-rehearsal`, worktree `AssetOpsV1-dd1b2`. Ruling: `build-sheet-DD-1.md` DD1b2-R. Packet: `.agent/review-packet-DD-1b2a.md`. Evidence: `.agent/DD-1b2a-probe.json`.

## State: STOPPED at P1 for the Architect

Pinned study S-19 to S-15: UNKNOWN, 0 eligible, `RENEWABLE_DAY_MISSING`. S-20 to S-16 the same. Cause measured: on all 13 full days hours 05 and 23 local are missing, because the last row of each night and rest run reads `UNAVAILABLE`. P2 to P7 not run.

## Landed

- `16339efe8`: store seam (`mini_decisions/store.py`), `kobo.mill` in `demo-combined-story-v1.json`, `tools/demo_combined_mill.py`, `Demo.after_children` and `finish_build` plus dev subcommand `after-children` in `tools/demo_combined.py`, `tools/dd1b2a_probe.py`, L0 `test_demo_combined_mill.py`, L2 `test_mini_opportunity_story_clock_postgres.py`, `.agent/DD-1b2-probe-days.json`.
- The stop commit: packet, evidence, this handoff, BL-40 and BL-41, the tool's `day_rows` key fix.

## Resume after the ruling

Re-probe in full, about 40 min to the stop plus the rest: `prepare --sites kobo --no-finish --days .agent/DD-1b2-probe-days.json`, DB `assetops_demo3_dd1b2p_test`, work `var/demo3_dd1b2p`; `after-children`; then `tools/dd1b2a_probe.py ticks --db ... --work ... --out .agent/DD-1b2a-probe.json`. The prepare archives git HEAD, so commit first. `dd1b2a_probe.py` has never run. Its output path would overwrite the stop's evidence, so keep that copy.

## Own DBs

`assetops_demo3_dd1b2p_test` with `var/demo3_dd1b2p`, and `assetops_dd1b2a_test`: see the packet's Checks for whether they were dropped.
