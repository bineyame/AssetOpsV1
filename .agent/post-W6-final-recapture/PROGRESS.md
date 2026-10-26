# Final recapture progress (agent A: batches 01-04), main SHA 89a11477
- batch 01 DONE: 40 pairs, FIXED 28, PASS 12, REGRESSION-OPEN 0, GAP 0. DBs dropped, servers stopped.
- batch 02 DONE: 62 pairs, FIXED 30, PASS 10, REGRESSION-OPEN 0, GAP 22 (dispatch + analysis: s3_dispatch_walkthrough has no --db/--work option and would DROP owner DB assetops_s3walk; not run). DBs dropped, servers stopped.
- batch 03 DONE: 72 pairs, FIXED 59, PASS 13, REGRESSION-OPEN 0, GAP 0. Producers s404/s408/s405 unmodified (_audit), DBs dropped, servers stopped.
- batch 04 DONE: 50 pairs, FIXED 50, PASS 0, REGRESSION-OPEN 0, GAP 0 (observation: raw ACTION_* codes + ellipsized ids still on action-history under open D2 R217). DBs dropped, servers stopped, var/ clean.
# Agent B (batches 05-08), main SHA 89a11477 (HEAD cfd0c989, no product-file diff)
- batch 05 BLOCKED at start: s603 prepare+attest ran fine (unmodified, DB assetops_s603_owner_audit), then the Bash call that started `serve` in the background plus start-vite.ps1 (PowerShell -ExecutionPolicy Bypass) was DENIED by the auto-mode permission classifier. Per brief: stopped, no workaround. DB dropped via producer's own `drop`, var/s603_owner_audit removed, no processes left. Only batch-05/{tools,logs,sha.txt,head.txt} written. No pairs captured in batches 05-08.
- UPDATE after owner authorized local servers (owner-local-servers-authorization-2026-10-26.md): resumed.
- batch 05 DONE: 26 pairs, FIXED 22, PASS 4, REGRESSION-OPEN 0, GAP 0. s603 + s602b (replay + 4 cases) unmodified; DBs dropped, servers stopped.
- batch 06 DONE: 46 pairs, FIXED 24, PASS 22, REGRESSION-OPEN 0, GAP 0. seed.py unmodified against assetops_audit_b06_test (dropped). Observation: refusal panels gained a collapsed details disclosure (96->113/129 px), flagged only.
- helper tools added: tools/seed-phase.sh, start-api.sh, stop-serve.ps1, stop-port.ps1.
- batch 07 DONE: 60 pairs, FIXED 36, PASS 24, REGRESSION-OPEN 0, GAP 0. seed.py cold excursion/normal unmodified vs assetops_audit_b07_test (dropped).
- batch 08 DONE: 56 pairs, FIXED 27, PASS 23, REGRESSION-OPEN 6, GAP 0. seed.py ev x5 unmodified vs assetops_audit_b08_test (dropped). OPEN: ev-finding Overview (cases interrupted, no-window, recommendation-address; 1440 and 390): Session id in Operational context became a one-line horizontal scroller and is cut (frozen: wrapped, R277). Evidence batch-08/interrupted/ev-finding-*-app.png.
- NEXT (if context allows): batch-02 dispatch/analysis 22 pairs with s3_dispatch_walkthrough.py (owner authorized rebuilding assetops_s3walk).
- batch 02 UPDATED (dispatch/analysis 22 pairs now captured with s3_dispatch_walkthrough.py unmodified, owner-authorized): batch-02 now FIXED 42, PASS 20, REGRESSION-OPEN 0, GAP 0. assetops_s3walk left rebuilt (owner DB; producer has no drop). Servers stopped.
- All agent-B work complete; all audit DBs dropped, no listeners, var/ clean.
# Agent C (batches 09-12), main SHA 89a11477 (HEAD 1b9ae037, no product-file diff)
- batch 09 DONE: 50 pairs, FIXED 32, PASS 18, REGRESSION-OPEN 0, GAP 0. seed.py ev interrupted/complete unmodified vs assetops_audit_b09_test (dropped).
- batch 10 DONE: 62 pairs, FIXED 0, PASS 62, REGRESSION-OPEN 0, GAP 0. W3-01 serve.py unmodified vs w301cap_test (dropped). Observation (uncounted link check): EV finding page still has the ev-id one-line scroller (same as batch 08 OPEN).
- batch 11 DONE: 66 pairs, FIXED 6, PASS 60, REGRESSION-OPEN 0, GAP 0. W3-03 (assetops_audit_b11_test) and W3-02 (w302j_test) producers unmodified; DBs dropped. globalfinancials Consequence register 1.37-1.46x mock: inner scroller removed, inside ruled 800 cap, classed FIXED.
- batch 12 DONE: 42 pairs, FIXED 25, PASS 17, REGRESSION-OPEN 0, GAP 0. W4-02 seed (w402r_test) and W4-03 walkthrough (assetops_audit_b12_test) unmodified; DBs dropped; replay.json restored. 
- Note: Vite serves on localhost (IPv6) only; targets rewritten from 127.0.0.1 to localhost. Tracked pyc .agent/W3-03-evidence/__pycache__ modified by pytest was restored with git checkout. Empty untracked var/evidence/migration-performance appeared at 12:42 (not removed).
- All servers stopped, DBs dropped, no listeners on 9741/9751/9761/9781/188xx/518x/952x.
