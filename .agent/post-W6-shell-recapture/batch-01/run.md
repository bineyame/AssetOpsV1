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

## r2 recapture at 321cfe56 (populated foundation + sld; Q13 re-measure)
- `tools/v01a_foundation_walkthrough.py --db assetops_shellrc_b01r2_walk_test --empty-db assetops_shellrc_b01r2_empty_test --work-name shellrc-b01r2-v01a prepare` (tree from 321cfe56); API via frozen `serve-one.py --which populated --port 18101`; Vite 5181 (ASSETOPS_API_PORT=18101); `drop` (both DBs, work tree removed).
- `capture-b1.mjs` unchanged, args foundation:{imported-period,no-version,now}, sld:{battery,now,unknown-part}. `populated-r2/`: 12 captured / 12 selected, 72/72 claims, no console errors.
- Q13 r2: `sld-legibility-r2.mjs` (earlier measure + `ul[data-sld-key]` reads) -> `sld-legibility-r2.json`, `sld-*-legibility-r2.png`. 390: SVG scale 0.3147, min label 3.46 px (unchanged); key visible (flex 318x148), 12px, 10 items/10 buttons vs 10 drawn `.sld-node` (incl. 1 bus; panel text says "9 parts are drawn"), 10/10 buttons focusable; battery case marks "Battery energy storage · 200 kWh" pressed. 1440: scale 1, min 11 px; key display:none (not visible, not focusable).

## r3 recapture at ac2e9b4f (closeout ruling 3: the R382 label on the phone SLD key)
- `tools/v01a_foundation_walkthrough.py --db assetops_shellrc_b01r3_walk_test --empty-db assetops_shellrc_b01r3_empty_test --work-name shellrc-b01r3-v01a prepare` (unmodified; tree from ac2e9b4f); API via frozen `serve-one.py --which populated --port 18101` (PID 16464); Vite 5181 (PID 23560, ASSETOPS_API_PORT=18101); CDP 9521; `drop` (both DBs dropped, work tree removed; PIDs stopped by PID).
- `capture-b1.mjs` unchanged, sld:{battery,now,unknown-part}, AUDIT_REVISION=ac2e9b4f. `populated-r3/`: 6 captured / 6 selected, 36/36 claims, overflowX 0. These supersede the populated-r2 sld pairs in the index.
- `sld-legibility-r3.mjs` (r2 measure + `[data-mock-deviation='R382']` read) -> `sld-legibility-r3.json`, `sld-*-legibility-r3.png`: at 390 the label is present, visible (block, 12px, 318x19.8, directly before `ul[data-sld-key]`) in 3/3 cases with the key visible; at 1440 present but `display:none` (0x0) in 3/3 with the key hidden.
- No Lab history inspector or Lab Site model screen is in the Q24 selection, so the label there is covered by the unit test only (`siteConfiguration.test.tsx`), not by an app capture.

