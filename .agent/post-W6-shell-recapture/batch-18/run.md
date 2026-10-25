# post-W6 shell recapture, batch 18 (capture-only)

- SHA 7e7b3dd5 (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, fresh per part (`--strictPort`), CDP 9521, AUDIT_REVISION=7e7b3dd597a5597bbbac5354fe98d0a6af86c18a. One warm-up read per Vite start went to %TEMP% (not counted).
- Producer (reviewed, unmodified): `tools/w502_cold_work_walkthrough.py --work var/w502b_shellrc18 --tag shellrc18 prepare --modes positive`, then `drop`. DB `w502b_positive_shellrc18_test` (none existed first). No serve (8971-8977 untouched).
- API: plain product API (frozen batch-18 start_apis.ps1 form: `uvicorn assetops_backend.main:app`, random cursor key) on 127.0.0.1:18101 over that DB. Vite ASSETOPS_API_PORT=18101.
- Targets: frozen `mk_targets.py cold 18101 <window>`, window 2026-10-19T00Z..2026-10-26T00Z (the frozen 7-day window ending the day after the run, shifted one day because the producer's cases are recorded 2026-10-25), filtered, origin 5188 -> localhost:5181. Capture: frozen capture-b18.mjs unchanged.
- Pairs: 8 captured / 8 selected (incidents, maintenance, maintenance-preventive, oprecords cold). 48/48 claims, no console errors, no gap.
- API PID stopped by PID; drop removed the DB and work folder.
