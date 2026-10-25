W2-cold U5 recapture (capture-only). Product SHA captured: 47d7929c (r1-8d1c0d59/ holds the pre-fallback run at 8d1c0d59).
Producers (unmodified): .agent/W2-F-evidence/seed.py "cold excursion" -> assetops_w2coldrc_x_test, "cold normal" -> _n_test,
"cold backup-failed" -> _b_test, "ev interrupted" -> _e_test (tools/seed_all.sh); lab API host/lab_app.py on 18535 (tools/api.sh),
Vite 5195 (ASSETOPS_API_PORT=18535), Chrome CDP 9595. Mini Site Findings: tools/s404_finding_index_walkthrough.py prepare|serve|drop
--db assetops_s404_owner_w2coldrc_audit --work var/s404_owner_w2coldrc --api-port 18536 (Vite 5196, CDP 9596).
All DBs dropped and every server stopped after capture.
Parts: part-x (excursion: 33 indexed pairs + 8 URL-only one-sided/32-day + excursion Finding rep + tab known_at), part-n (8),
part-b (5), part-e (EV Findings rep), part-mini (mini Site Findings rep); each target at 1440x1000 and 390x900, app + v69 mock.
probe/part-x: inspect + cold Findings cap probe (SYNTHETIC LAYOUT EVIDENCE, NOT PRODUCT DATA; browser-only DOM clone).
fallback-steps/: the cap fallback measurements step by step. summary.json: per-capture URL, overflow, clipping, console,
panel titles vs mock, closed heights, MOCK DEVIATION label counts, refusal sentence counts.
Tools: capture-cold.mjs (from W2-EV r2 capture-b8.mjs + EXTRA DOM checks), inspect-cold.mjs (from W2-EV r2 inspect.mjs + coldrows
probe), celldump.mjs (per-cell sizes), mk_targets.py (targets from post-W6-audit/audit-index.json), summarize.py, caps.py, run.sh.
