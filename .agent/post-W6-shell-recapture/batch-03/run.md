# post-W6 shell recapture, batch 03 (capture-only)

- SHA 710b0de5, captured 2026-10-25. API 127.0.0.1:18101 (producer-internal TLS/HTTP 18102-18103; s408 prepare on 18104-18106), Vite http://localhost:5181 (this worktree's frontend/, ASSETOPS_API_PORT=18101), CDP 9521.
- Capture tool: frozen `.agent/post-W6-audit/batch-03/tools/capture-b3.mjs`, unchanged; filtered targets here; AUDIT_REVISION=710b0de5.
- part-s404-late: `tools/s404_finding_index_walkthrough.py --db assetops_s404_owner_audit --work var/s404_owner_audit --api-port 18101 --tls-port 18102 --http-port 18103 prepare (266 s, 0 failed) | serve | late | drop`.
- part-s408-owner: `tools/s408_assumption_history_walkthrough.py --suffix _audit prepare --api-port 18104 --tls-port 18105 --http-port 18106` (566 s, 0 failed; builds owner + mixed), `links`, `serve --case owner --api-port 18101 ...`, `drop` (both DBs).
- IDs: s408 Finding f1753882/rev 3a9738f5 -> adcc07d4/11336241, and the T3 second-page address (recorded_at + history_after cursor) replaced by this run's `links` "Second page at T3" address (frozen logs/s408-links.log vs s408-links.log here).
- Pairs: 12 captured / 12 selected (s404-late 2, s408-owner 10). All claims pass, no console errors, no gap. A first s408 attempt raced the API start (financials nofinding 1440 read "Site unavailable"); rerun once the API listened passed 60/60 (`capture-s408-owner.try1.log` kept).
- All DBs dropped by producer drop modes; all spawned PIDs stopped by PID.
