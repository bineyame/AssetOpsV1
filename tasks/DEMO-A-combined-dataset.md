# DEMO-A Combined three-Site demo dataset on the sparse story calendar (DEMO-SPARSE)

Status: in_review

One `tools/demo_combined.py prepare` builds a private test database holding KOBO-001 (mini-grid), GreenHarvest
(cold room) and Depot (EV charging) on one story clock, from the owner-approved sparse day list
`backend/conversions/demo-story-days-v1.json` (8 Kobo, 3 cold, 2 EV story days; every day a registered Lab run),
then finishes objectives, comparisons and ticks and runs the acceptance self-check (`tools/demo_combined_finish.py`).
Branch `task/DEMO-A-combined-dataset`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-demo3`. Packet
`.agent/DEMO-A-packet.md`; phase handoff `.agent/DEMO-A-phase-handoff.md`.

Contract: `AssetOpsV1-plan2/.agent/build-sheet-DEMO-SPARSE.md` (rev 1 + Addenda 1-3, wins where it differs) over
`build-sheet-DEMO-COMBINED.md` (rev 1 + Addendum 1). Depends on IDX-GAPS, SCN and FIX-S4-DOMAIN (all on main).

## Gates (from the sheet)

- Units U1-U6 of DEMO-SPARSE §3; acceptance rows CO-1..CO-12 and SP-1..SP-7 (§5) as the self-check and as one test
  each in the slow build test `backend/tests/test_demo_combined_postgres.py`, none skipped at merge.
- Addendum 3: CO-1 re-premised until the owner rules on the Finding-revision lineage (R552 stays open); trial on (a)
  unless the single (d) re-probe verifies (it did not: R617).
- Register R615-R619 and the R535 / R552 / R569 / R595 resolutions.
- Tier: `test_demo_story_days.py`, check-all, the full prepare, the slow build test; the `-Tier all` on the combined
  tree before merge on the coordinator's go.

Built state: self-check 16/17 on the kept build `assetops_demo3_full_test` (`20f83276b`); CO-6 fails on a product gap (no cold
consequence drain at runtime; packet "CO-6 measured value and cause"), so merge waits on that ruling.

USER_REVIEW_REQUIRED: false (a demo dataset; merges on a fresh independent review ACCEPT; the owner sees it in the
walkthrough after DEMO-B captures)
