# Architect request: W4-02 closure round 4 (post-W4-01 seam re-check)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide";
- `.agent/W4-02-build-spec.md`, closures 1–3;
- `.agent/W4-02-seam-recheck.md`: 20 open items (3 Blocker, 9 Should, 8 Nit) with file:line evidence against main, where W4-01 is now merged;
- `.agent/W4-02-mock-measurements.md`.

Close all 20 with exact artifacts verified against main.
- Blocker 1: the literal domain-to-role map in the `0029` trigger, listing all 14 roles.
- Blocker 2: the v4 mini-grid event mapping table. Give the exact rows. Resolve the shared role names `backup_start_event` and `backup_bus_state`, which collide with cold-chain enqueueing (`postgres_evidence_ledger.py:67,466`), and the conflicting bus-state values. Use distinct mini-grid role names, or a site-type-scoped enqueue, and give the DDL or code.
- Blocker 3: Q24's Backup Overview card. The v69 mock and the shipped page have five cards and no Backup card, so follow the mock. Revoke Q24's extra card and record the supersession.
- The Should item on the Q12/Q10 conflict: give one consistent performance-gate rule.

Include a supersession index for any replaced text. Append the result as "Review closure 4 (2026-10-20)" to `.agent/W4-02-build-spec.md`. Write nothing else. Do not commit.
