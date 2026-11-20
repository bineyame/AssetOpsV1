# ON1 reviewer guide (rev 2)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md`, `runbook.md` and this guide; put
questions in `handshake.md`), then at the review. Depth: discovery (W5): the real-data boundary (RC4), people and
roles (OD-14 kept by the owner's answer to D-ON1.9: the file proposes, the executive approves at sign-in), key
erasure, and the tenant the server serves.

## First checks

1. **Scope.** The diff holds only spec §8 question 10's list; one migration (0066), one alembic head.
2. **No operator database anywhere.** Grep the tests and the packet's logs: no connection string names an
   `assetops_op` database except with host `rc4.invalid`; the no-connect fixture is autouse in each RC4 file and its
   self-test passes.
3. **Module paths** in the packet resolve to the worktree.
4. **3C0a unchanged except sign-in's approval.** Its service, API and Postgres files pass with the `build_parser`
   rename and the sign-in body's two `[]` lists; no other expected value moves.
5. **RC4-F1 and 3A3 merged first**; `database_name` appears nowhere.

## Done means

Spec §8's ten questions answered yes with real output: the four no-database files, the Postgres file through
`tools/heavy-slot.sh --db`, the regression set, check-all, and each plant below failing.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V1 | Let `check` accept `data: real` with `real_data=False` | service 7 |
| V2 | Drop the served-tenant check (step 2) | service 7 |
| V3 | Let `create_app` start with the switch on and `ASSETOPS_TENANT_SLUG` unset | settings 2 |
| V4 | Keep `DEVELOPMENT_TENANT_SLUG` in `create_app`'s `FoundationService` | settings 2, Postgres 1 |
| V5 | Remove the `ONBOARDING_CLOSED` check from `add_role_proposal` (memory and adapter) | service 7, Postgres 3 |
| V6 | Update an existing Site's name instead of refusing | service 6 |
| V7 | Print the people's emails in the plan | service 2 |
| V8 | Skip the tombstone in `FileKeyStore.key` | keys 2 and 3 |
| V9 | Let `create_key_file` replace an erased key | keys 1 |
| V10 | Unlink the key before writing the tombstone | keys 2 (crash case) |
| V11 | Add a command line to the runbook with a flag the parser lacks | settings 3 |
| V12 | Propose `OPERATOR_EXECUTIVE` through `onboard_propose` | service 10 |
| V13 | **Grant a proposed role before the executive approves it** (any of: `apply` inserts `role_grant` rows for the file's roles; sign-in applies proposals without `approve_roles`; a non-executive's sign-in applies them) | service 2 and 3, Postgres 1 |
| V14 | Accept an `approve_roles` digest that differs from the proposals' | service 3 |
| V15 | Record the approved grants `by_service` instead of `by_person_id` = the executive | service 3, Postgres 1 |
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
- **OD-14.** Only the executive's own grant carries `service:onboarding`; every other grant row names the executive
  as `by_person_id` and exists only after the sign-in that named the confirmed digest. After one person-made grant no
  proposal is possible, also under concurrency (Postgres 3). Walk the approval: without the digest, with a wrong one,
  by a non-executive.
- **Runbook as a person.** Follow it from step 1 on paper: is every value it asks for named, does every command
  exist with those flags, and is every setting inside a subshell next to its command? Residual: the parser test
  cannot see a missing setting (R5's class); this read is the check. Does step 11 delete every copy?
- **Words.** Each refusal reads as one plain sentence with the place in the file, never a value.
