# FIX-COLD-DRAIN handoff

Status: U1-U4 built and committed on `task/FIX-COLD-DRAIN-tick`. P1-P4 pass on the host (4 passed, 364 s).
Next: scoped selector run (fast tier, in container) result -> packet `.agent/FIX-COLD-DRAIN-packet.md` -> check-all.
`-Tier all` waits for the coordinator's go. Anchors: `scheduling/tick.py` `_site`, `scheduling/stages.py`
`_domain_assess`/`_domain_consequence`, tests `backend/tests/test_fix_cold_drain_*`.
