# Test-pipeline hygiene (2026-10-31)
- MEDIUM: several lanes share `assetops_test`. The FIX-COLD-DRAIN reviewer found it reset to migration 0009 mid-session by another lane, which could explain intermittent Postgres failures, e.g. the w301 cold KeyError. Proposal: give each lane or worktree its own `*_test` DB name.
- MEDIUM: `check-architecture.ps1` rule 8 reported cold/EV consequence INSERTs missing from `postgres_consequence_store.py` (lines 966/983/1076). The count varied 4/6/6 across runs under machine load, so the check is non-deterministic. It needs a look.
- LOW: FIX-COLD-DRAIN L3, the 60 s Site-lease slack now covers 9 children.

## DEMO-A final review Lows (merged `4f57261d3`, review `.agent/review-DEMO-A-final.md`)
- L1: CO-1 lacks the original U6 assertion `"Reliable service and battery and generator life" in mnh["text"]` (`tools/demo_combined_finish.py:142-149`); text is present in the kept build, add the line back.
- L2: CO-1 "Action on the Cost row" reads `items(cost)` incl. `earlier`, so it cannot tell a linked Action from CO-3's line (`tools/demo_combined_finish.py:145-147`); restrict to `issues` + `in_hand`. The href assertion is the real guard.
- L3: register R535/R552 description text and `.ai/CODE_STATE.md:6251-6252` ("main `15eed62c8`", "Addenda 1-3") are stale; statuses closed by coordinator at merge, descriptions still historical.
