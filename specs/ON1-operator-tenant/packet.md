# ON1 packet: an operator's tenant from one onboarding file

Implementer (Claude, fresh), 2026-11-20. Branch `task/ON1-operator-tenant` off main `8fddb2bba` (3A3 and RC4-F1
merged). Worktree `/opt/assetecon/AssetOpsV1-on1`. Spec rev 3, rulings D-ON1.1-16, reviewer guide rev 3.
`USER_REVIEW_REQUIRED: false` (non-screen; the owner's decisions it rests on are recorded; Q2 below goes to the
Architect).

## Outcome

One emulated onboarding file creates the tenant, its 3 Sites (through `import_site`), 7 accounts, 7 grants (all
`by_service service:onboarding`, `by_person_id` NULL) and the key; a rerun writes nothing. A real file passes the RC4
steps and is refused before any write (`ONBOARD_REAL_AWAITS_APPROVAL`, until `ON1b`). The server serves
`ASSETOPS_TENANT_SLUG`; the demo pins `demo`. Erasure leaves a tombstone no key can follow.

## Commits

1. `ec838ccbd` the file, digest, separation, fixture, file tests; mid-build Q1.
2. `0ca29b276` service, command, account/store methods, `tenant_slugs`, served tenant and accessors, the key
   tombstone/erase/state/directory check and 409; service 1-10, keys 1-4, settings 1-2, Postgres 1-4.
3. head: demo pin, runbook copy, `world_history.build_parser`, settings 3-4, packet and bookkeeping.

**Deviation (order only):** the key-store code moved from the spec's commit 3 into commit 2 because the command
composes `FileKeyFiles`. All files are those of spec §4, plus §6's tests and fixture. No migration (alembic heads:
`0065_commercial_upload (head)`, one head).

## Module paths

`PYTHONPATH` = worktree `backend:backend/tests:contracts:simulator:gateway:field:host:tools`; interpreter
`/opt/assetecon/AssetOpsV1/.venv/bin/python`. `assetops_backend.__file__` =
`/opt/assetecon/AssetOpsV1-on1/backend/assetops_backend/__init__.py`; `assetops_contracts` and
`assetops_simulator` resolve under `/opt/assetecon/AssetOpsV1-on1/contracts/` and `.../simulator/`.

## Done (spec §8)

1. Yes: service 1, 2, 4, 5; Postgres p1, p2.
2. Yes: service 3 and 8; step 3a sits after steps 1-3 and before any store read beyond `tenant_slugs`.
3. Yes: service 6 (Site, operator name, person, other tenant's email, executive, digest one character off).
4. Yes: service 7 and 10; Postgres p3 (person-made grant closes; two concurrent grants record one; adapter
   `ROLES_SEPARATE` with the file rule bypassed).
5. Yes: service 8 (matrix and the command's `CONFIGURATION` refusals for `?dbname=assetops_op_x` and no name),
   settings 2, the no-connect self-test in each of the three RC4 files. Every database URL in them uses
   `rc4.invalid:1`.
6. Yes: keys 1-4 (file, symlink, dangling symlink, mode-000 tombstones; crash cases), service 9.
7. Yes: settings 1, 2, 4; Postgres p1 (`create_app` serves `KOBO-001` through `registry.ledger_scope`).
8. Yes: settings 3: exactly the 7 listed lines parse with each program's `build_parser()`, no top-level `export`,
   declared variables only, runbook equals `runbook.md` from its first heading.
9. Yes: service 2 (no `@` or name in the plan or the command's output); file tests (submitters and accepters disjoint).
10. Yes: every plant below fails its named test; the diff is §4's files, §6's tests and fixture, and the bookkeeping.

## Checks run (code as at commit 3; `f2a7970b6` was commit 3 before the packet was added by amend)

- Focused + regression, `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1` (routed `*_test`): the four ON1
  no-database files, `test_on1_onboarding_postgres.py`, 3C0a service/API/Postgres/onboard-Postgres/passwords, 3A2
  service/API/Postgres, 3A3 loader/loader-Postgres/single-writer/source-contract, RC4-F1, `test_s1_foundation_postgres.py`,
  `test_demo_combined_links.py`, 3C1a and its Postgres file: **657 passed, 16 warnings in 163.97 s** (wall 2m46s).
- Plants V1-V22 (runner in the session scratchpad; each applied, run, reverted with `git checkout`; tree clean
  after): all 23 runs **fail** their named tests (V22 as V22a export and V22b deleted line). V5, V14 fail service 7
  / 10 and Postgres p3; V4, V15 fail settings 2 / service 2 and Postgres p1; V10 fails the added keys-2 crash case
  (a tombstone that cannot be written leaves the key `PRESENT`); V21 fails the self-test.
- §7 guard plants (`check-architecture.ps1 -Only configuration-persistence.ps1`, `ASSETOPS_GUARD_PYTHON` set): each
  adds its own failure: `UPDATE role_grant` in the account adapter ("runs only its declared statements"),
  `INSERT INTO role_grant` in `onboarding/service.py` ("a second product database writer"), `os.unlink` in
  `pseudonym_key.py` ("write-capable call outside a user store adapter").
- Fast check-all: **all 40 pass** (81.5 s wall).
- Layout evidence: not run (no screen).

## Known deviations and open questions

- **Fix round r1 (D-ON1.17 to .20, spec/runbook rev 3.1), done:** `onboarding_open` renamed `onboarding_may_grant` (5 references,
  guard untouched); parser reads `format` first, structural errors are `ONBOARD_STRUCTURE` with its own sentence;
  runbook recopied from its first heading; new test `test_2_a_tombstone_check_that_cannot_be_answered_fails_closed`
  (os.lstat raises PermissionError; reviewer's plant A, `except OSError: return False`, now fails it, reverted).
  Review copied to `review.md`. Runs: ON1 non-Postgres + 3C0a/3A2/3A3/RC4-F1 regression (non-Postgres) 416 passed
  (72 s); ON1 Postgres file 5 passed (`heavy-slot.sh --db`, run-host-tests.ps1); check-all 40/40.
- Q1 and Q2 are answered (D-ON1.18, D-ON1.17).
- `site_source` validation also runs `plan_import` on a placeholder tenant so a Site the importer would refuse is
  `ONBOARD_SITE_INVALID` at parse time; no message is kept (raised outside the handler).
- The command's exit-3 refusals for `AccountRefused` and key errors print the code alone (§5 gives no sentence).
- The time zone is not validated by `parse_site_document` (an unknown zone parses); not changed here.

## Residual risk

- A real operator's file mislabelled `emulated` in a non-operator database gets automatic grants (D-ON1.15 residual;
  stated in the runbook).
- `check`'s executive rule only binds when an executive exists; a tenant whose file executive exists without the role
  and no executive at all would apply without one (unreachable through `apply`, which creates the account and role
  together).

## Review focus

RC4 order in `onboarding/service.py` `check` (steps 0-3a), `add_onboarding_grant` under the lock (adapter and
`MemoryStore`), `_tombstoned`/`erase_key_file` order, the runbook test's exact list, and Q2.
