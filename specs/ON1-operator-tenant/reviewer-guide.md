# ON1 reviewer guide (rev 1)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md`, `runbook.md` and this guide; put
questions in `handshake.md`), then at the review. Depth: discovery (W5): the real-data boundary (RC4), people and
roles (OD-14, D-3C0A.7 refined), key erasure, and the tenant the server serves.

## First checks

1. **Scope.** The diff holds only spec §8 question 9's list; no migration.
2. **No operator database anywhere.** Grep the tests and the packet's logs: no connection string names an
   `assetops_op` database; the RC4 tests use names only and in-memory ports.
3. **Module paths** in the packet resolve to the worktree.
4. **3C0a unchanged in behaviour.** Its service, API and Postgres files pass with only the `build_parser` rename.

## Done means

Spec §8's nine questions answered yes with real output: the four no-database files, the Postgres file through
`tools/heavy-slot.sh --db`, the regression set, check-all, and each plant below failing.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V1 | Let `check` accept `data: real` with `real_data=False` | service 7 |
| V2 | Drop the served-tenant check (step 2) | service 7 |
| V3 | Let `create_app` start with the switch on and `ASSETOPS_TENANT_SLUG` unset | settings 2 |
| V4 | Keep `DEVELOPMENT_TENANT_SLUG` in `create_app`'s `FoundationService` | settings 2, Postgres 1 |
| V5 | Remove the `ONBOARDING_CLOSED` check from `add_onboarding_grant` (memory and adapter) | service 6, Postgres 3 |
| V6 | Update an existing Site's name instead of refusing | service 5 |
| V7 | Print the people's emails in the plan | service 2 |
| V8 | Skip the tombstone in `FileKeyStore.key` | keys 2 and 3 |
| V9 | Let `create_key_file` replace an erased key | keys 1 |
| V10 | Unlink the key before writing the tombstone | keys 2 (crash case) |
| V11 | Add a command line to the runbook with a flag the parser lacks | settings 3 |
| V12 | Grant `OPERATOR_EXECUTIVE` through `onboard_grant` | service 9 |

## Probes

- **Convergence.** Read `apply`: every step is guarded by the fresh `check`; a failure between the Sites and the
  people leaves a state the next `check` marks `keep` and `create` correctly (service 4).
- **OD-14.** The onboarding grants carry `by_service = service:onboarding` and no person; after one person-made grant,
  no onboarding grant is possible, also under concurrency (Postgres 3).
- **Runbook as a person.** Follow it from step 1 on paper: is every value it asks for named, and does every command
  exist with those flags? Does step 10 say what is lost?
- **Words.** Each refusal reads as one plain sentence with the place in the file, never a value.
