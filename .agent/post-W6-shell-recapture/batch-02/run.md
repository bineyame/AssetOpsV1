# post-W6 shell recapture, batch 02 (capture-only)

- SHA 710b0de5, captured 2026-10-25. API 127.0.0.1:18101, Vite http://localhost:5181 (this worktree's frontend/, ASSETOPS_API_PORT=18101), CDP 9521.
- Capture tool: frozen `.agent/post-W6-audit/batch-02/tools/capture-b2.mjs`, unchanged; filtered targets files `targets-*.json` here; AUDIT_REVISION=710b0de5.
- Producers (reviewed, unmodified). DB names follow the brief (producer prefix + `_audit`, or `assetops_shellrc_b02*_test`), so the producers ran directly where their guards accept those names:
  - dispatch: frozen `run_renamed_producer.py tools/s3_dispatch_walkthrough.py s3walk-renames.json -- prepare|serve --port 18101` (renames = frozen s3walk.json with DB `assetops_shellrc_b02_s3walk_test`; work folder stayed `%LOCALAPPDATA%/AssetOps/audit-b2-s3walk`). No drop mode: DB dropped and work folder removed by this agent.
  - evidence / evidence-record: `tools/s302_claim_limit_walkthrough.py --db assetops_s302_audit --work var/s302_shellrc --port 18101 prepare|serve|drop`.
  - health: s701 run of batch 01 (`assetops_s701_owner_audit`, serve 18101, deliver just before capture).
  - mini: `tools/s5_overview_walkthrough.py prepare|serve|tick|drop --db assetops_s501_owner_audit --work var/s501_owner_shellrc --api-port 18101 --tls-port 18102 --http-port 18103` (prepare 287 s, 0 failed checks).
- IDs: s302 revisions remapped positionally from the producer's serve output (5 IDs). Record-opened: the frozen record came from `GET /api/sites/KOBO-001/evidence/records`; the same read here gave first record 6eb191fe-e6a1-4dfa-bde4-55b7f05d4103 (frozen 1687c876 cannot be matched one to one; first record chosen).
- Pairs: 26 captured / 26 selected (dispatch 4, evidence 16, evidence-record 2, health 2, mini 2). All claims pass. No console errors. No gap.
- All DBs dropped; all spawned PIDs stopped by PID.
