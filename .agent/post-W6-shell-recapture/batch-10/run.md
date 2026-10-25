# post-W6 shell recapture, batch 10 (capture-only) — NON-QUALIFYING DIAGNOSTIC EVIDENCE (closeout ruling 4)

- SHA 321cfe56 (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=321cfe56.
- Capture tool: frozen `.agent/post-W6-audit/batch-10/tools/capture-b10.mjs`, unchanged; filtered `targets-historical.json`, `targets-positive.json` here.
- Producer (reviewed): `.agent/W3-01-evidence/serve.py` run through the frozen `.agent/post-W6-audit/batch-02/tools/run_renamed_producer.py` with `w301-renames.json` (one rename: hard-coded DB `w301cap_test` -> `assetops_shellrc_b10_test`, created first; nothing else changed). PYTHONPATH backend;backend/tests;gateway;simulator;contracts;host.
- Ports: the producer hard-codes API 127.0.0.1:9741 (checked free first; another agent's W3-01 run had just ended). Vite 5181 with ASSETOPS_API_PORT=9741. No capture-control POSTs needed (historical and positive precede late-kobo/empty-site).
- historical: first attempt (`capture-historical.try1.log`, 40/48) showed "Choose a valid evidence cutoff": the producer's pinned clock (11:04, flowing with wall time) had not yet passed the frozen known_at 2026-11-02T11:08:27Z. Waited (polling `/__capture/clock`) until it did; rerun 48/48.
- Pairs: 10 captured / 10 selected (historical 8: findings, -cost, -risks, -opportunities; positive 2: actions empty-day, 12/12). No console errors, no gap.
- DB dropped WITH (FORCE); producer (PID 12092) and Vite (PID 10620) stopped by PID.

## Replacement run ledger (closeout ruling 4, 2026-10-25, SHA ac2e9b4f)

- **Status of the run above: NON-QUALIFYING DIAGNOSTIC EVIDENCE.** It used the forbidden name-rewriting `run_renamed_producer.py`. Its images are kept here only as diagnostic material; every pair below is a capture gap for the Q24/current-SHA audit verdict.
- Producer: `.agent/W3-01-evidence/serve.py`, unmodified. It has no `<prefix>_audit` mode; it hard-codes its own `w301cap_test` (a `*_test` name) and expects the DB to exist.
- Attempt: `docker exec assetopsv1-postgres-1 psql -U assetops -d postgres -c "CREATE DATABASE w301cap_test"`. **Refused** by the Claude Code auto-mode permission classifier: "Permission for this action was denied by the Claude Code auto mode classifier. Reason: The server-side auto mode classifier judged this action dangerous (it gave no explanation)."
- Fallback (pure selected-DTO render proof): the next step, listing `.agent/post-W6-shell-recapture/dto-proof/` to reuse its harness, was **refused** too: "Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Auto-Mode Bypass]." Work on this ruling stopped there; no DTO proof was produced.
- Pairs: 0 qualifying / 10 selected (historical 8: findings, findings-cost, findings-risks, findings-opportunities x 1440/390; positive 2: actions empty-day x 1440/390). **10 capture gaps.**
- No wrapper, renamed producer, edited producer or alternate DB name was used or tried. No DB was created; nothing to drop. No server was started for this batch.
