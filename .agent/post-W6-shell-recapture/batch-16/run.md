# post-W6 shell recapture, batch 16 (capture-only)

- SHA 7e7b3dd5 (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, fresh per part (`--strictPort`), CDP 9521, AUDIT_REVISION=7e7b3dd597a5597bbbac5354fe98d0a6af86c18a. One warm-up read per Vite start went to %TEMP% (not counted).
- Producer (reviewed, unmodified, shared with batch 1617): `W504_API_PORT_BASE=18100 tools/w504_ev_work_walkthrough.py --work var/w504a_shellrc1617 --tag shellrc1617` prepare / serve / attest / drop. DBs `w504a_{positive,zero,worstcase,unknown}_shellrc1617_test` (none existed first). APIs positive 18101, zero 18102, worstcase 18103, forbidden 18106 (real 403), unavailable 18107 (stopped by attest). unknown/pending/stale unavailable (producer verdict). Logs in batch-16/logs/.
- Capture tool: frozen `.agent/post-W6-audit/batch-16/tools/capture-b16.mjs`, unchanged. `targets-positive.json` here = frozen `mk_targets.py positive <this run's manifest>`, filtered to the selected cases, origin 127.0.0.1:5186 -> localhost:5181.
- Pairs: 10 captured / 10 selected (5 all-open screens x 2 widths). 60/60 claims, no console errors, Vite alive after capture, no gap.
- drop stopped the API PIDs and dropped all four DBs and the work folder; my Vite PIDs stopped by PID; no port of mine still listens.
