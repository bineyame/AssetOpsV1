# post-W6 W1-b recapture, batch 05 (capture-only, agent B)

- SHA: AUDIT_REVISION=d960eeee; HEAD 2af5fef6 at end (only .agent files differ; product tree identical). Captured 2026-10-25.
- Ports: APIs 18142/18143 (s602b replay/case), 18144 (s603); Vite http://localhost:5186 (this worktree's frontend/); CDP 9526.
- Capture tool: frozen `.agent/post-W6-audit/batch-05/tools/capture-b5.mjs`, unchanged; filtered remapped targets here.
- part-s602b-replay: same s602b run as batch 04 (Vite->18142) 8/8, 48/48. IDs remapped from frozen batch-05 links log.
- part-s602b-cases: guardrail (with batch 04 guardrail), then `tools/B-cases.sh` restarting unmodified `serve --case target_miss|inconclusive|withdrawn --port 18142` (case API 18143, Vite->18143): 8/8, 12/12 claims each.
- part-s603: `tools/s603_site_work_walkthrough.py --db assetops_s603_owner_audit_w1brc --work var/s603_owner_w1brc prepare | attest (ATTEST OK) | serve --port 18144 --web-port 5186 | drop` (Vite->18144): 10/10, 60/60.
- Pairs: 26 captured / 26 selected. overflowX 0; titles equal frozen; no console errors. Verification pages have no "Evidence requirements" panel (cap n/a there).
- Checks `checks-*.json`: verification pages no Site tab row, no R383, rail Actions; sitework is a Site page (tab row present, rail Sites).
- Extra: withdrawn case `extra-withdrawn-history/` action-history both widths (RESOLUTION_WITHDRAWN row "Resolution withdrawn" with the ruled meaning, shown after "Show all 6 entries"); viewer click in `viewer-withdrawn/`.
- DBs: s602b DBs dropped (batch 04 run.md); assetops_s603_owner_audit_w1brc dropped by producer drop. PIDs stopped by PID.
- Gaps: none.
