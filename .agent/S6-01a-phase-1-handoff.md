# S6-01a phase 1 handoff

Branch `task/S6-01a-action-store-read`. The build commit is `9a115431`, on top of `5e0b705d`. It has not been merged. This phase covers only phase 1 of `tasks/S6-01a-action-store-read.md`; the task Status line is unchanged.

## What landed

- **Migration** `backend/migrations/versions/0014_action_store.py` (down_revision `0013_schedule_state`).
  - Tables: `action` (with the accepted-recommendation snapshot as columns plus `snapshot` jsonb), `action_basis_assessment`, `action_basis_evidence`, `action_event`, `action_policy_change`, `action_policy_change_binding`.
  - All of them are append-only through `ledger_append_only` and use same-Site composite FKs. `action_code` comes from `action_code_seq`, with `UNIQUE(tenant_id, action_code)`.
  - The acceptance key and recommendation key are each unique within tenant/Site.
  - Events: `UNIQUE(action_id, idempotency_key)`, one ACCEPTED and at most one APPLIED per Action. CHECKs make every non-OBSERVED event have occurred = recorded. OBSERVED may be backdated by at most 30 days and must carry `DEMO_REVIEW_NOTE`.
  - The migration adds `finding_revision_finding_scope_unique (tenant_id, site_id, finding_id, id)` so the Action's origin revision FK proves the revision belongs to the origin Finding.
  - The phase-2 change tables already exist here. Phase 2 writes them and may adjust columns before merge.
  - Tests that pinned the head now say `0014_action_store`: `test_s1_bindings_postgres.py:118`, `test_s2_evidence_ledger_postgres.py:445` and `test_s4_evidence_consequence_work_postgres.py:516,539`.
- **Package** `backend/assetops_backend/actions/`:
  - `reserve_trial.py` holds the pure `reserve-trial-1` rule (`evaluate`, `REASONS`, key and acceptance-key digests).
  - `lifecycle.py` holds `TRANSITIONS`, `reduce`, `selector`/`select` and the `SYSTEM_DEMO` actor.
  - `capability.py` holds the scoped grant check (`from_grants`, `no_capability`).
  - `ports.py`, `service.py` (`ActionService`) and `composition.py` (`build_action_service`, `finding_currentness`, `GRANTS_ENV=ASSETOPS_ACTION_DEMO_GRANTS`).
  - `adapters/postgres_action_store.py` is the ninth writer and only INSERTs. Accept is at :180 (advisory lock per recommendation key, then INSERT of the Action, basis rows and ACCEPTED). Observe is at :237 (Action row `FOR UPDATE`). `rule_inputs` is at :105.
  - `adapters/demo_grants_file.py` reads the grants document.
- **Routes** `backend/assetops_backend/action_api.py`, wired at `main.py:360`:
  - GET recommendation
  - POST accept
  - POST observations
  - GET action and GET events, each with `event_id` or `recorded_at` (both together gives 422 `ACTION_SELECTOR_CONFLICT`)
- **Rule 8** in `tools/checks/configuration-persistence.ps1`:
  - New `actions` domain entry.
  - `$actionWriter`/`$actionTables` at :692, registered in `$pgWriters`, `$pgWritesSeen` and `$pgDriverSeen`.
  - An INSERT-only check and a cross-module ban on Action-table writes.
  - A per-line ban on UPDATE, DELETE, TRUNCATE, upsert (`ON CONFLICT`/`DO UPDATE`), MERGE, DDL, GRANT and COPY in the Action adapter (:803).

## Choices to review (interpretations, not decided elsewhere)

1. **"Reviewed" FindingRevision.** No reviewed flag exists in the schema. I read "reviewed" as a persisted S4-01 matcher revision. "Current" means all three of: it is the latest revision; the S4 read's `claim_is_current` is true; and the Performance gate is open. This goes through `FindingReadService.finding`.
2. **Segment SOC.** The rule uses the `battery_soc` evidence that the segment's interval assessment cites. A usable reading is GOOD, numeric and in `%`. Conflicting means two readings at the same instant with different values. The selected reading is the lowest usable value, which is the conservative reading of "a reading strictly above r+10". The basis is the latest eligible segment's covering FoundationRevision, and every eligible segment on that same Foundation is cited. When nothing is eligible, the reason reported is the latest Candidate segment's reason.
3. **Reserve 90 cannot be reached physically.** It needs SOC above 100. The band is still proven at rule level.
4. **`action_code` sequence.** It comes from a single database sequence (`ACT-000001`), and uniqueness is enforced per tenant. Per-tenant numbering would need a mutable counter, which the INSERT-only writer cannot keep.
5. **Command authentication.** It uses the same development access seam as the Finding read (`command_access`, injectable). The actual authority is the server grant document; a client field naming an actor, capability or authority is refused with 422 `CLIENT_AUTHORITY_FORBIDDEN`.
   - Refusal order: 401/403 access → 404 Site → scoped capability 403 `SYSTEM_DEMO_CAPABILITY_DENIED` → body 422 → Finding, revision or Action 404 → domain 409/422.
6. **Accept payload digest.** It includes `idempotency_key`. Re-accepting the same recommendation with a new key is therefore a 409, not a replay.
7. **OBSERVED moved forward.** The OBSERVED route and store were built in phase 1, so that the selector-tie proof has real events.
8. **Not built in phase 1:** the S4 money consequence on the recommendation, and the demonstration label on Action reads.

## Proof (all on `9a115431`)

- New tests:
  - `backend/tests/test_s6_action_rule.py`: 60 passed. Covers boundaries, reasons, transition table, selectors and capability.
  - `backend/tests/test_s6_action_store_postgres.py`: 7 passed (about 70 s). Covers eligible F01/F02 accept, replay, 409, snapshot after a reserve change plus reassessment (`FOUNDATION_BASIS_STALE`), and concurrent identical accepts (4 threads produce 1 Action). It covers authored SOC 30 vs 30.5 on persisted evidence. It covers F04 revision 2 alongside the pinned origin. It covers that 401/403/capability/404/422 refusals write nothing. It covers the backdated OBSERVED, its bounds, retry and 409. It covers ties, exact-event and cutoff reads, selector conflict and schema constraints.
  - DB used: `assetops_s601a_test`.
- Adjacent tests: `test_s4_finding_read_postgres`, `test_s1_foundation_postgres`, `test_s1_bindings_postgres`, `test_pg_harness` and `test_s4_finding_api`: 58 passed. The migration up/downgrade subset of `test_s2_evidence_ledger_postgres` and `test_s4_evidence_consequence_work_postgres`: 4 passed.
- `tools/check-all.ps1`: 9/9 PASS. I used a temporary `.venv` junction and ran `npm ci` in `frontend`.
- Mutation checks. Each was reverted, and the worktree is clean afterwards:
  - Rule 8: each of the following fails the guard: an Action-adapter UPDATE, DELETE, upsert, TRUNCATE, DDL or other-table INSERT; a Foundation adapter Action-table write; a Finding store Action-table write; a non-writer module Action-table write; all driver imports removed; all INSERTs removed.
  - Transitions: adding `(APPLIED, FAILED) -> PENDING` and removing `(PENDING, APPLIED)` each fail tests, and so does a cutoff that excludes ties.
  - Idempotency: removing the acceptance digest check or the observation key-reuse check fails the Postgres tests.
- No full suite was run, per the brief. Another full suite was running on the machine at the time.

## Next (phase 2)

- Add a caller-owned-connection form of `FoundationService.publish_battery_reserve` → `_publish_content_change` → `PostgresFoundationStore.publish_configuration` (`postgres_foundation_store.py:607-656`). The Action adapter opens the transaction and locks the Action with `SELECT ... FOR UPDATE`. S1 then locks the Site and checks the expected covering ID under that lock. It returns every written and superseded Foundation, SPLIT and binding-set ID. A callback then inserts `action_policy_change`, its binding rows and APPLIED, before the Action adapter commits.
  - The adapter must not import the S1 service. Pass the S1 publish in from composition as a callable.
- Add FAILED in a separate transaction after rollback. Its insert must treat a `UNIQUE(action_id, idempotency_key)` hit as "return the existing event" (plan re-review residual).
- Add `ACTION_ALREADY_APPLIED`, `ACTION_FOUNDATION_STALE` and the effective-time rules.
- Add `GET /foundation/changes/{change_id}` and fill `change` in the Action read (currently `None`).
- Add the `D-action-records` fixture/loader and `backend/tests/fixtures/s6_action_api_contract.json`.
- Add `test_s1_bindings_postgres.py`, the walkthrough, and the full suite.

## Risks

- LR-01 adds its own `0014`/`0015`. Whichever lands second must re-chain its migration (the packet already says this).
- `rule_inputs` makes one evidence query per Candidate segment. That is fine for demonstration volumes.
