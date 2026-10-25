# post-W6 shell recapture, batch 19 (capture-only)

- SHA 7e7b3dd5 (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, fresh per part (`--strictPort`), CDP 9521, AUDIT_REVISION=7e7b3dd597a5597bbbac5354fe98d0a6af86c18a. One warm-up read per Vite start went to %TEMP% (not counted).
- Producer (reviewed, unmodified): `tools/w601_seed.py --db assetops_w601_shellrc19detail_test --fixture detail --clock 2026-10-20T12:00:00Z` (the tool only accepts `assetops_w601_*_test`; none existed first). Output in `seed/seed-detail.json`.
- API: plain product API (frozen batch-19 run_phase.ps1 form) on 127.0.0.1:18101; Vite ASSETOPS_API_PORT=18101.
- IDs: WR-000001 from this seed = 8d4f17c7-6cd8-491a-8cc9-a83fb80d7fdc, swapped for the frozen 9b43962f-... in the frozen `targets-detail.json`, filtered, origin 5189 -> localhost:5181. Capture: frozen capture-b19.mjs unchanged.
- Pairs: 6 captured / 6 selected (wr-overview, wr-record, wr-history all-open-wr1). 36/36 claims, no gap.
- Console: wr-record (both widths) logs the React validateDOMNesting warning (<div> inside <p>, Clamp in TechnicianNotes); the frozen batch-19 evidence has the same warning. /api/sites returns 503 on this DB (stale ignored var/sites/kobo-001.yaml, batch-18 note); the detail screens do not depend on it and it was left as is, as in the frozen batch 19.
- API PID stopped by PID; DB dropped WITH (FORCE).
