# Owner instruction, 2026-10-23 ~01:10

The owner said "solve the 90 minutes build issue and memory problem". The coordinator proposed:
1. 4 pytest workers instead of 2.
2. synchronous_commit=off on test DBs only.
3. Postgres max_connections 100 -> 200, which restarts the shared postgres container (no data loss).
4. .wslconfig with memory=6GB and autoMemoryReclaim, plus one wsl --shutdown / Docker restart.
5. Only one light job alongside a suite.

Owner verbatim: "do what needs to be done"
