# Test-pipeline hygiene (2026-10-31)
- MEDIUM: several lanes share `assetops_test`. The FIX-COLD-DRAIN reviewer found it reset to migration 0009 mid-session by another lane, which could explain intermittent Postgres failures, e.g. the w301 cold KeyError. Proposal: give each lane or worktree its own `*_test` DB name.
- MEDIUM: `check-architecture.ps1` rule 8 reported cold/EV consequence INSERTs missing from `postgres_consequence_store.py` (lines 966/983/1076). The count varied 4/6/6 across runs under machine load, so the check is non-deterministic. It needs a look.
- LOW: FIX-COLD-DRAIN L3, the 60 s Site-lease slack now covers 9 children.
