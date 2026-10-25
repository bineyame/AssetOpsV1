# post-W6 W1-a recapture, batch 03 (capture-only)

- SHA 56d36bf2 (task/post-W6-W1-a), captured 2026-10-25. API 127.0.0.1:18121 (producer-internal TLS/HTTP 18122-18123; s408 prepare on 18124-18126), Vite http://localhost:5183 from this worktree's frontend/ (ASSETOPS_API_PORT=18121), CDP 9523.
- Capture tool: frozen `.agent/post-W6-audit/batch-03/tools/capture-b3.mjs`, unchanged; filtered `targets-*.json` here; AUDIT_REVISION=56d36bf2.
- part-s404 / part-s404-late: `tools/s404_finding_index_walkthrough.py --db assetops_s404_owner_audit --work var/s404_owner_audit --api-port 18121 --tls-port 18122 --http-port 18123 prepare (159 s, 0 failed) | serve | late | drop`.
- part-s405: `tools/s405_provenance_walkthrough.py --suffix _audit prepare --only owner (141 s, 0 failed) | links | serve --case owner --api-port 18121 | drop`.
- part-s408-owner / part-s408-mixed: `tools/s408_assumption_history_walkthrough.py --suffix _audit prepare --api-port 18124 --tls-port 18125 --http-port 18126 (331 s, 0 failed) | links | serve --case owner|mixed --api-port 18121 | drop`.
- IDs (all re-derived from this run; Finding IDs are not stable across runs):
  - s404: Finding 2ce656e8 -> da87d497-4796-47a7-a806-57ce369028a8 (first row of the positive window in `s404-prepare.log`, same position as frozen), version 1 921f15e4 -> 6b141888-b73d-4d6c-9912-25c3c2a7756b (the revision with no previous revision in `GET .../history`; 4 revisions as frozen).
  - s405: P01 Finding/rev b6b17a85/ffc6bc5c -> 057de30c/385ca44a (line 5 of frozen vs this `s405-links.log`).
  - s408 owner: f1753882/3a9738f5 -> 40c9c8e5/a8e856de (positional from `s408-links.log`). Mixed: 4f566b9c/e46abda4 -> 33aaa84d-cf0f-417c-ba0b-259f073adba2 / 6d9b798b-170c-46e1-9012-dfda00523688, the only Finding and only revision in `assetops_s408_mixed_audit` (read-only SELECT).
- Pairs: 46 captured / 46 selected (s404 30, s404-late 6, s405 2, s408-owner 6, s408-mixed 2). Claims 180/180, 36/36, 12/12, 36/36, 12/12. No console errors, no gap.
- Retries (kept logs): `capture-s404.try1-unmapped.log` ran with frozen Finding IDs (not found here); its images were discarded and part-s404 recaptured with remapped IDs. `s405-prepare.try1.log`: run in parallel with s408 prepare, the s405 gateway failed to open its named pipe (WinError 5); that partial state was dropped by `s405 drop` and prepare rerun alone (0 failed).
- All DBs dropped by producer drop modes; all spawned PIDs stopped by PID.
