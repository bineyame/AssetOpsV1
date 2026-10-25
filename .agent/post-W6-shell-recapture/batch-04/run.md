# post-W6 shell recapture, batch 04 (capture-only)

- SHA 710b0de5, captured 2026-10-25. API 127.0.0.1:18101 (replay) / 18102 (TEST-SCOPED guardrail case), Vite http://localhost:5181 (this worktree's frontend/), CDP 9521.
- Capture tool: frozen `.agent/post-W6-audit/batch-04/tools/capture-b4.mjs`, unchanged; filtered targets `targets-*.json` here; AUDIT_REVISION=710b0de5.
- s601b: the batch 01 run (`tools/s601b_action_walkthrough.py --db assetops_s601b_audit --work var/s601b_shellrc prepare|links|serve --port 18101 --web-port 5181|drop`). IDs remapped positionally from the frozen `logs/s601b-links.log` to this run's `../batch-01/s601b-links.log` (16 IDs; recorded_at fixture times unchanged).
- s602b / s602b-guardrail: the batch 01 run (`tools/s602b_verification_walkthrough.py --db assetops_s602b_audit --work var/s602b_shellrc prepare|links|serve --case guardrail --port 18101|drop`); replay on Vite->18101, guardrail on Vite restarted with ASSETOPS_API_PORT=18102. IDs remapped positionally from frozen `logs/s602b-links.log` to `../batch-01/s602b-links.log` (14 IDs).
- Pairs: 42 captured / 42 selected (s601b 24, s602b 12, s602b-guardrail 6). Claims all pass. The guardrail first attempt failed action-plan 1440 'app rendered' (cold Vite compile after the restart); rerun passed 36/36 (`capture-s602b-guardrail.try1.log` kept).
- Console: action-history verified-replay (1440, 390) logs React "two children with the same key" warning, also present in the frozen run.
- All DBs dropped by producer drop modes; all spawned PIDs stopped by PID.
