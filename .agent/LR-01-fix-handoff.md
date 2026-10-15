# LR-01 fix round handoff

Branch `task/LR-01-late-reading-series-and-money-limit`. Items:

1. Ruling 1: `analytics/adapters/postgres_finding_store.py` docstring corrected (latest-revision replay, returning basis). 0015 downgrade already refuses duplicate history. New tests `TestMigration0015Downgrade` in `backend/tests/test_s4_consequence_store_postgres.py` (refusal keeps both revisions and stays at 0015; clean path restores `finding_revision_basis_unique`).
2. Ruling 2: `backend/assetops_backend/scheduling/upstream.py` (S5-01 must absorb): `findings[].money_eligibility` is now the raw gate result, never rewritten. New per-finding `upstream_status` `{status: CURRENT|BLOCKED, reasons: [{stage, code}]}` (window S3/S4/SCHEDULE blockers plus the Finding's own consequence state, e.g. `SCHEDULE_STOPPED`) and `current_amount_permitted` (gate ELIGIBLE and upstream CURRENT; S5 still adds same-basis CURRENT PRICED). Window `eligibility` unchanged. Tests in `backend/tests/test_s4_schedule_upstream_unit.py` (stopped schedule keeps ELIGIBLE, blocks amount, names schedule; permission matrix).
3. Ruling 4: wording fixed in the task file, `.agent/LR-01-review-packet.md`, `.agent/LR-01-owner-walkthrough.md`.
4. Ruling 5: `test_production_composition_wires_the_persisted_gate_and_a_failed_gate_shows_no_amount` in `backend/tests/test_lr01_money_eligibility_postgres.py` (proven non-vacuous by setting composition eligibility=None: fails).
5. L1: `frontend/src/sites/FindingConsequence.tsx` `MoneyLimit` worded by relation/source, no list when no spans; two tests in `siteFinancials.test.tsx` (non-tail limit, empty).
6. L3: residual added to packet and walkthrough.

Results: tsc clean; `npm test` 1484 passed (62 files); focused backend new tests pass. Full backend: see packet/final report. Browser evidence at 390: not run.
