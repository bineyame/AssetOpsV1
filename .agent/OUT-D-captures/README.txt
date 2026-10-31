OUT-D U6 captures at b4e834f9 (capture-only; no product code changed). Tool: capture-outd.mjs (OUT-W's capture-outw.mjs plus
`open: "all"` and the `contributors` / `matrixCells` measures; CDP, 1440x1000 and 390x900, app + v70 mock).
Objectives declared after prepare, before serve: python -m assetops_backend.declare_objective fixture --file
backend/conversions/demo-objectives.json with DATABASE_URL = the producer DB (logs/*-declare.log).
Producers: w502 positive (GreenHarvest, DB w502b_positive_outd_test, API 8971 / Vite 5471); w504 (Depot, DBs
w504a_{positive,zero,worstcase,unknown}_outd_test, API 8981 / Vite 5481); s5_overview_walkthrough (Kobo, DB
assetops_s501_owner_outd_audit, API 8925 / Vite 5425); s602b estate case (Portfolio, DBs assetops_s602b_outd_audit and
_{target_miss,guardrail,inconclusive,withdrawn,estate}, API 8968 / Vite 5468). Cursor-key env vars set for every serve.
Targets: targets-1 (cold, ev), targets-2 (Kobo from/to day 2026-10-21), targets-2b (Kobo ?date=2026-10-21 cross-check),
targets-3 (Portfolio 2026-10-21). Evidence: shots/raw-evidence.json (runs; app.contributors, cards, matrixCells).
Claims: 18/20 (the two failures are the cold "app rendered" READY wait, also failing in OUT-B; board status loaded),
10/10, 10/10, 10/10. No page overflow anywhere. All DBs dropped, var/ work folders removed, servers and Vite stopped by PID.
