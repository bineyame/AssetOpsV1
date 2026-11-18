# Architect request: W5-02a K1a/K1b builder deviations

You are the AssetOps Architect (Codex). The W5-02a core build is on `task/W5-02a-cold-action-root`: K1a is done, and K1b is committed (`828e284c`, `3279887c`) but not yet verified. Read the handoff Run entries with `MSYS_NO_PATHCONV=1 git show task/W5-02a-cold-action-root:.agent/W5-02a-phase-handoff.md`, plus the K1a–K1c cards and the pre-flight rulings in `.agent/W5-02-build-spec.md`.

The builder made three choices. Confirm each one or give a literal correction, with a test:
1. `work_record_id` references W4 `maintenance_record`, because no `work_record` table exists.
2. A missing Action returns 404 before the 422 link checks; the spec orders 422 first. Give the exact check order.
3. A case link must name the case's head revision and latest event, or it gets 409 `DOMAIN_INTENT_BASIS_CHANGED`. Confirm whether that is intended and what the request carries.

Append "W5-02a build rulings (K1 deviations)" to `.agent/W5-02-build-spec.md`. Write nothing else. Do not commit. End your output with one line per item, saying whether code must change.
