# Final recapture progress (agent A: batches 01-04), main SHA 89a11477
- batch 01 DONE: 40 pairs, FIXED 28, PASS 12, REGRESSION-OPEN 0, GAP 0. DBs dropped, servers stopped.
- batch 02 DONE: 62 pairs, FIXED 30, PASS 10, REGRESSION-OPEN 0, GAP 22 (dispatch + analysis: s3_dispatch_walkthrough has no --db/--work option and would DROP owner DB assetops_s3walk; not run). DBs dropped, servers stopped.
- batch 03 DONE: 72 pairs, FIXED 59, PASS 13, REGRESSION-OPEN 0, GAP 0. Producers s404/s408/s405 unmodified (_audit), DBs dropped, servers stopped.
- batch 04 DONE: 50 pairs, FIXED 50, PASS 0, REGRESSION-OPEN 0, GAP 0 (observation: raw ACTION_* codes + ellipsized ids still on action-history under open D2 R217). DBs dropped, servers stopped, var/ clean.
# Agent B (batches 05-08), main SHA 89a11477 (HEAD cfd0c989, no product-file diff)
- batch 05 BLOCKED at start: s603 prepare+attest ran fine (unmodified, DB assetops_s603_owner_audit), then the Bash call that started `serve` in the background plus start-vite.ps1 (PowerShell -ExecutionPolicy Bypass) was DENIED by the auto-mode permission classifier. Per brief: stopped, no workaround. DB dropped via producer's own `drop`, var/s603_owner_audit removed, no processes left. Only batch-05/{tools,logs,sha.txt,head.txt} written. No pairs captured in batches 05-08.
