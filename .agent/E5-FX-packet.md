# E5-FX packet

Branch `task/E5-FX-actor-label-links`. Spec: D-E5.3 (part A), D-E5.4 (part B) in build-sheet-OWN-GAPS-2026-11-08.md.

## Delivered
- A: `actorLabel` in `frontend/src/work/OperationalRecords.tsx` maps `service:operator-entry` to "Entered by site admin" (unchanged), `service:w401-fixture` to "Prepared example record", any other `service:` id to "Entered by a system service"; other values as stored. Comment MD-E5-1; register row R714 in `.agent/mock-departure-register.md`.
- `data-global-work-actor` now carries the raw actor id (it was an empty string; the card said it "keeps the raw ID", so it is set to `row.actor_id`).
- B: `tools/demo_combined.py` Finding link has no `?revision_id`; `backend/tests/test_demo_combined_links.py:56` updated.

## Tests
- `operationalRecords.test.tsx` + `operationalEntryForm.test.tsx`: 32 passed. Entry-form test now covers all four mappings (admin, example, fallback, as-stored `user:jane`) and the raw-id hook.
- `test_demo_combined_links.py`: 11 passed. Mock-deviation/vocabulary guard test (14) and `mock-deviation-labels.mjs` OK; v69 ledger valid.
- Non-vacuity: with the old `OperationalRecords.tsx` and `demo_combined.py` restored, 2 frontend tests and 1 backend test fail.

## Assertions changed (list requested by card)
1. `operationalRecords.test.tsx` ~:289: By text `service:w401-fixture` is now "Prepared example record".
2. `operationalEntryForm.test.tsx` ~:419: the By-label test, extended.
3. Deviation: `ACTOR128` fixture (long-id truncation test) was `service:` + 120 x; that is now the fallback label, so the fixture is `user:` + 123 x (128 chars, same assertion kept). The card says other changed assertions are a stop; I changed the fixture, not the assertion, to keep the long-text coverage. Review this.

No full suite run (card). node_modules junction removed before commit.
