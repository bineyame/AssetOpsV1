# 3C1 mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **1** (3C1a); 3C1b: **3** (below).

## Q1 (3C1a, §4 "Regression (must pass unchanged)"): two older migration tests assume their migration is the head

- **What fails.** On `task/3C1a-person-on-work` (b1c90c80a), pooled run:
  - `test_3c0a_accounts_postgres.py::test_downgrade_refused_with_an_account_then_down_and_up`: it runs
    `TRUNCATE operator_account, ...` at head. Postgres refuses: "cannot truncate a table referenced in a foreign key
    constraint. Table "work_case" references "operator_account"". The reference is §4 step 3's
    `<t>_person_fk`, which the spec requires. No migration that references `operator_account` can leave this test
    passing unchanged.
  - `test_k2_fuel_records_postgres.py::test_migration_up_down_up_on_empty_table`: it downgrades from **head** to
    0053 and asserts `operational_record` lost exactly `{asset_id}`; at head it also loses `person_id`.
- **Class.** A migration test that measures "head" as if its own migration were the head. Swept: every test that
  downgrades and touches the nine tables or `operator_account` (14 files); the others pass (see the packet).
- **Stopped.** Only these two files: they are not edited. Everything else is built.
- **Question.** May 3C1a edit the two tests? Proposed default (smallest edit, no assertion weakened):
  - 3C0a test: `TRUNCATE ... CASCADE` (or downgrade to `0062_operator_accounts` first, read from `MIG`);
  - k2 test: compare against the schema at its own revision (`command.upgrade(config, "0054_...")` before
    `shape`, or subtract the later migrations' declared columns), not at head.

## 3C1b pre-flight (2026-11-21, against `main` 28263c47b: 3C1a, 3C0a, 3A2, 3B1, 0K1 merged)

§5 otherwise fits `main`: the action routes still run open scope, then `authorize_*` (404/403 grant), then the body;
`AUTHORITY_WORDS` already refuses `actor` with 422 `CLIENT_AUTHORITY_FORBIDDEN`; the person words exist
(`person.person_required`, `person.person_role_required`, from 3C1a), so the refusals reuse existing codes and keys.
`action_event` has one writer (`postgres_action_store.py`), and the three named checks exist with the 0016/0019 texts.

### Q-3C1b-1 (§5 step 5, labels) vs D-SC1.28: "Recorded by a signed-in person" is new served text

- **Conflict.** §5.5 asks USER rows to read "Recorded by a signed-in person". D-SC1.28 (SC-1a not merged) forbids any
  new served text, constant or catalogue key, before SC-1a.
- **Stopped.** Only the wording. **Built (proposed default):** USER rows carry `label: null` in `event_wire`, and the
  observe `statement` and the change artifact's `label` and `statement` are `null` for a USER act. SYSTEM rows keep
  today's text byte for byte. Tests assert `null` and `actor.kind == "USER"`, never words. The sentence is recorded in
  the packet as a pending SC-1 statement for the text commit after SC-1a.

### Q-3C1b-2 (§5 step 5, scope gap): three SYSTEM wordings §5.5 does not name

- **What.** On a person's act these still say "SYSTEM demonstration": the Action read's `action.label`
  (`actions/service.py:674`, from the Action row, which has no actor), the Foundation publish note stored on the new
  Foundation revision by apply (`:534`), and the `CLIENT_AUTHORITY_FORBIDDEN` message ("the server records the SYSTEM
  demonstration actor").
- **Proposed default.** Unchanged in 3C1b: §5.5 names only the event label, the observe note and the apply statement,
  and any replacement is new text (D-SC1.28). Listed in the packet as pending statements and a Known Deviation; the
  stored publish note is the one that persists, so it is flagged for the SC-1 text commit or 3C2.

### Q-3C1b-3 (§5 tests, "through `create_app`, an accept and an apply"): no harness composes Actions in `create_app`

- **What.** No existing test runs an accept through `create_app`: it needs the grants file
  (`ASSETOPS_ACTION_DEMO_GRANTS`), the S4 Finding pipeline (`CaseRunner`) and the fixed rule clock the action tests
  inject (`T_ACCEPT`); `create_app` uses the wall clock.
- **Proposed default.** The accept and the apply are stored under the person through the real router, the real
  `PostgresActionStore` and the real Postgres account store (the S6 `Harness` pattern), with `triggering_fixture`
  asserted. `create_app` wiring is proven separately on Postgres: with the switch on and no cookie an accept answers
  401 `PERSON_REQUIRED`, and a signed-in person of another tenant gets the unknown-Site 404 (so `accounts` and the
  switch reach the action router). Recorded as a Known Deviation.
