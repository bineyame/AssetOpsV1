# 3C1 mid-build questions (RULES §4 item 7)

A question about something the spec did not fix stops only the affected part. Write it here (Q1, Q2 ...): the
section, what is stopped, what is built, and what you ask. The Architect rules in `rulings.md`. Record the count in
the packet; a count above zero is a spec-template defect to fix.

Count: **1**.

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
