# ON1 reviewer guide (rev 3)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md`, `runbook.md` and this guide; put
questions in `handshake.md`), then at the review. Depth: discovery (W5): the real-data boundary (RC4), people and
roles (rev 3, D-ON1.15: an emulated file's roles are granted by `service:onboarding`; a real file is refused before
any write until `ON1b` builds the owner's option A, so OD-14 holds for real data), key erasure, and the tenant the
server serves.

## First checks

1. **Scope.** The diff holds only spec §8 question 10's list; **no migration**, one alembic head unchanged.
2. **No operator database anywhere.** Grep the tests and the packet's logs: no connection string names an
   `assetops_op` database except with host `rc4.invalid`; the no-connect fixture is autouse in each RC4 file and its
   self-test passes.
3. **Module paths** in the packet resolve to the worktree.
4. **3C0a unchanged.** Sign-in, `accounts_api.py`, `model.py` and the persistence guard are not in the diff; the
   3C0a service, API and Postgres files pass with the `build_parser` rename and no expected value moved.
5. **RC4-F1 and 3A3 merged first**; `database_name` appears nowhere.

## Done means

Spec §8's ten questions answered yes with real output: the four no-database files, the Postgres file through
`tools/heavy-slot.sh --db`, the regression set, check-all, and each plant below failing.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V1 | Let `check` accept `data: real` with `real_data=False` | service 8 |
| V2 | Drop the served-tenant check (step 2) | service 8 |
| V3 | Let `create_app` start with the switch on and `ASSETOPS_TENANT_SLUG` unset | settings 2 |
| V4 | Keep `DEVELOPMENT_TENANT_SLUG` in `create_app`'s `FoundationService` | settings 2, Postgres 1 |
| V5 | Remove the `ONBOARDING_CLOSED` check from `add_onboarding_grant` (memory and adapter) | service 7, Postgres 3 |
| V6 | Update an existing Site's name instead of refusing | service 6 |
| V7 | Print the people's emails in the plan | service 2 |
| V8 | Skip the tombstone in `FileKeyStore.key` | keys 2 and 3 |
| V9 | Let `create_key_file` replace an erased key | keys 1 |
| V10 | Unlink the key before writing the tombstone | keys 2 (crash case) |
| V11 | Add a command line to the runbook with a flag the parser lacks | settings 3 |
| V12 | Grant `OPERATOR_EXECUTIVE` through `onboard_grant` | service 10 |
| V13 | **Let a real file write** (drop step 3a, or move it after the tenant is created) | service 3 and 8 |
| V14 | Drop the store's `ROLES_SEPARATE` backstop (memory and adapter) | service 10, Postgres 3 |
| V15 | Record the onboarding grants `by_person_id` = the executive instead of `by_service` `service:onboarding` | service 2, Postgres 1 |
| V16 | `apply` without the `--confirmed-digest` comparison | service 6 |
| V17 | Drop the submitter/accepter separation rule | file tests (`ONBOARD_ROLES_SEPARATE`) |
| V18 | Remove the demo pin from `Demo.env()` | settings 4 |
| V19 | Detect the tombstone with `Path.exists` instead of `_tombstoned` | keys 2 and 4 (dangling symlink) |
| V20 | In `erase_key_file`, skip the unlink when the tombstone already exists | keys 1 (crash case) |
| V21 | Remove the no-connect fixture from the service file | its self-test |
| V22 | Add an `export` line outside a subshell, or delete a checked line, in the runbook | settings 3 |

## Probes

- **Convergence.** Read `apply`: every step is guarded by the fresh `check`; a failure between the Sites and the
  people leaves a state the next `check` marks `keep` and `create` correctly (service 4).
- **OD-14 and D-ON1.15.** On a real file nothing is written: walk `check` with `data: real` and confirm step 3a is
  reached only after the RC4 steps and before any store call. On an emulated file every grant says
  `service:onboarding`, the record of who decided. After one person-made grant no onboarding grant is possible, also
  under concurrency (Postgres 3). Ask: can an emulated file reach an `assetops_op_` database by any setting? (It must
  not: `ONBOARD_DATA_MISMATCH` and 3A2's settings.) The residual, a real file mislabelled `emulated` in another
  database, is an RC4 breach stated in the runbook, not a code path.
- **Runbook as a person.** Follow it from step 1 on paper: is every value it asks for named, does every command
  exist with those flags, and is every setting inside a subshell next to its command? Residual: the parser test
  cannot see a missing setting (R5's class); this read is the check. Does step 7 delete every copy, and does the
  runbook say plainly that real operators wait for `ON1b`?
- **Words.** Each refusal reads as one plain sentence with the place in the file, never a value.
