# Owner decision, 22 Nov 2026 (verbatim)

Context: the coordinator reported that only one Postgres test job can run at a time (tools/heavy-slot.sh db-job), so four build lanes queue behind one 60-minute run, and proposed a second DB lane (each worktree its own `_test` database, already authorised), about 0.5-1 u of tooling, asking "Do you want me to queue it now, or keep it on the backlog?"

Owner: "proceed"
