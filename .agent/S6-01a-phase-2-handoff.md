# S6-01a phase 2 handoff

Branch `task/S6-01a-action-store-read`, code-final `375c8cf9` (commits `b8a5e931`, `d9f2aec5`, `375c8cf9`; closeout docs after). Not merged. Task status `in_review`; packet `.agent/S6-01a-review-packet.md` (slice review).

## What landed

- **Apply.** `PostgresActionStore.apply` (`actions/adapters/postgres_action_store.py`) does the following:
  - Takes the Action `FOR UPDATE` lock.
  - Returns `REPLAY` or `ALREADY_APPLIED`, or `FOUNDATION_UNKNOWN` when the expected revision is unknown.
  - Calls `attempt(c, action, events, then)`. The service's `attempt` (`actions/service.py` `apply`) validates the value and effective time, then calls the composed `foundation_publish` (`actions/composition.py`).
  - `foundation_publish` calls `FoundationService.publish_battery_reserve(..., caller=CallerTransaction(...))`, which reaches `PostgresFoundationStore.publish_configuration(..., connection=, then=)`.
  - `then(written_ids)` inserts the change, its binding rows and APPLIED via `_insert_applied`.
  - `ApplyFailed` causes a rollback, then `_append_failed` runs in a separate transaction.
- **S1 checks under the Site lock**, in `_publish_content_change`, run in this order:
  1. `expect`: `FOUNDATION_EXPECTED_REVISION_STALE`.
  2. No-change.
  3. `basis`: `FOUNDATION_EXPECTED_VALUE_STALE`.
  - `FoundationRefused` now carries `current_revision_id`.
- **Phase-1 review fold-in.** Grants v2 is scoped to fixture records (`capability.py`), with `authorize_accept` and `authorize_action` in `service.py`. L1, L3, L4 and L5 are covered as described in the packet.
- **`D-action-records`.** The loader is `backend/tests/s6_action_records.py`. The contract fixture is `backend/tests/fixtures/s6_action_api_contract.json`, checked by `backend/tests/test_s6_action_records_postgres.py`.

## Next

- Slice review (fresh Claude reviewer).
- Re-chain the migration if LR-01 merges first; the packet lists the head-pin locations.
- S6-01b builds the UI on the contract fixture.

## Open risks

- See the packet's Residual risk section.
- To serve a demo, the server needs an `ASSETOPS_ACTION_DEMO_GRANTS` v2 document for that database's tenant, Site and Finding IDs. No tool writes one for a served host yet; `fixture_grants` is test-side.
