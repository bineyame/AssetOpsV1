# post-W6 W1-b recapture, batch 04 (capture-only, agent B)

- SHA: AUDIT_REVISION=d960eeee recorded in evidence; HEAD moved to 2af5fef6 during the run (adds only .agent/post-W6-W1-b-recapture brief/selection; product tree identical). Captured 2026-10-25.
- Ports: APIs 127.0.0.1:18141 (s601b), 18142 (s602b replay), 18143 (s602b TEST-SCOPED case); Vite http://localhost:5186 from this worktree's frontend/ (restarted per API via ASSETOPS_API_PORT); CDP 9526.
- Capture tool: frozen `.agent/post-W6-audit/batch-04/tools/capture-b4.mjs`, unchanged; filtered, ID-remapped targets here (`tools/remap.py`: positional UUID map frozen links log -> this run's links log; structure identical).
- s601b: `tools/s601b_action_walkthrough.py --db assetops_s601b_audit_w1brc --work var/s601b_w1brc prepare | links --web-port 5186 | serve --port 18141 --web-port 5186 | drop` -> `s601b/` 28/28, 168/168 claims.
- s602b: `tools/s602b_verification_walkthrough.py --db assetops_s602b_audit_w1brc --work var/s602b_w1brc prepare | links --web-port 5186 | serve --case guardrail --port 18142 --web-port 5186 | drop` (+4 case DBs).
  - `s602b/` (replay, Vite->18142) 14/14, 84/84 (try1 82/84: cold Vite compile on the first target; log kept as capture-s602b.try1.log).
  - `s602b-guardrail/` (Vite->18143) 8/8, 48/48.
- Pairs: 50 captured / 50 selected. overflowX 0 everywhere; titles equal to frozen titles; no console errors.
- Post-capture checks (`tools/B-checks.mjs`, navigation only): `checks-*.json` - no Site tab row, no R383 on recommendation/Action pages; rail Findings / Actions active.
- Viewer click (`probe/tools/B-viewer.mjs`): `viewer-s601b/`, `viewer-s602b/`; see ../viewer-clicks-B.md.
- Extras (route only, s601b API): `extra-s601b/` unknown Action section `/actions/<id>/unknown` and `/overview` alias, both widths, 24/24 claims.
- Synthetic probes (Action history on s601b `all`; Evidence requirements on s602b guardrail/pass): ../probe/B-*. Both caps EXCEEDED (see probe results); work on those panels stopped.
- DBs: assetops_s601b_audit_w1brc, assetops_s602b_audit_w1brc(+_target_miss,_guardrail,_inconclusive,_withdrawn) dropped by producer drop modes; PIDs stopped by PID.
- Gaps: none.
