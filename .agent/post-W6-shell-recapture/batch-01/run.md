# post-W6 shell recapture, batch 01 (capture-only)

- SHA 710b0de5 (task/post-W6-shell), captured 2026-10-25. API 127.0.0.1:18101 (s602b case API 18102), Vite http://localhost:5181 from this worktree's frontend/ (ASSETOPS_API_PORT=18101), CDP 9521.
- Capture tool: frozen `.agent/post-W6-audit/batch-01/capture-b1.mjs`, unchanged, run with only the selected targets; AUDIT_REVISION=710b0de5.
- Producers (reviewed, unmodified):
  - populated/empty: `tools/v01a_foundation_walkthrough.py --db assetops_shellrc_b01_walk_test --empty-db assetops_shellrc_b01_empty_test --work-name shellrc-b01-v01a prepare`; APIs one at a time via frozen `serve-one.py --which populated|empty --port 18101`; `drop`.
  - s601b: `tools/s601b_action_walkthrough.py --db assetops_s601b_audit --work var/s601b_shellrc prepare|links|serve --port 18101 --web-port 5181|drop` (same API also served batch 04 s601b).
  - s602b: `tools/s602b_verification_walkthrough.py --db assetops_s602b_audit --work var/s602b_shellrc prepare|links|serve --case guardrail --port 18101 --web-port 5181|drop` (+4 case DBs; also served batch 04/05).
  - s701: `tools/s701_health_walkthrough.py --db assetops_s701_owner_audit --work var/s701_owner_shellrc prepare|serve --port 18101 --web-port 5181|deliver|drop` (also served batch 02 health).
- Generated IDs remapped from the producers' own links/serve output: s601b applied change f272ee05 -> 4902825c; s602b effect change e8873a43 -> c89de4c0; s701 battery 2661fe42 -> c3c120a2. Fixed IDs (v01a copy of assetops_s4cases, zero UUIDs) unchanged.
- Pairs: 40 captured / 40 selected (empty 2, populated 28, s601b 4, s602b 2, s701 4). No gap.
- Claims: populated 166/168 (asset unknown-site panel-count FAIL at 1440 and 390, identical to the frozen run: refusal vs mock panels); others all pass.
- Extra (coordinator request, Q13): `sld-legibility.json` + `sld-*-legibility.png` (capture-only CDP measurement of the SLD at 390/1440, default, battery, unknown part).
- All DBs dropped by producer drop modes; all spawned PIDs stopped by PID.
