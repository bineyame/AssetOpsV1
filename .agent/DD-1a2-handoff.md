# DD-1a2 handoff

## State: stopped at pre-flight, waiting on the lane-2 Architect
- Done: `.agent/DD-1a2-preflight.md` (Q1-Q8). No repo code changed.
- Next: apply rulings, then gates G0, G1, G2 as listed there, then the v3 list, guards, FILL-1 kinds, packet.
- Anchors: `tools/demo_story_days.py:130` (guard), `:296-301` (stream rules), `:354` (`plan_add_day`); `tools/derive_steady_scenarios.py:58` (HELD), `:373` (`rest_document`); `tools/probe_kobo_nights.py:233` (`full_days`); `backend/assetops_backend/actions/verification_families.py:277` (`assess`).
- PYTHONPATH must be absolute Windows paths, or imports resolve to the stale editable install under `AssetOPsV1`.
- DBs and processes alive: none. The scratch chain probe is in-memory and outside the repo.
