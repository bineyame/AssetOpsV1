# 3C0a packet: operator accounts, sessions and role grants behind the API

Implementer (Claude), 2026-11-20. Branch `task/3C0a-operator-accounts` (worktree `/opt/assetecon/AssetOpsV1-3c0a`),
off `main` 559e264a3, `main` 2b9f24759 merged in (MB1/MB2). Spec rev 2 + `rulings.md` (incl. MB1, MB2).
Not merged. Estimate 2.5 units.

## Commits

| Commit | What |
|---|---|
| `43fcbda84` | Tests first (W2): the five `test_3c0a_*` files; shown failing at collection (`ModuleNotFoundError: No module named 'assetops_backend.accounts'`); mid-build Q1, Q2 |
| `2b9f24759` | Merge of `main` (MB1, MB2 rulings) |
| `c7f2016d6` | Migration 0062, `accounts/` package, `accounts_api.py`, `create_app` keyword, 21 words, guard registration |
| (this) | Packet and finish bookkeeping (`.ai/state/work.md` entry, `index-2.md` line 143, `.ai/state/INDEX.md` row, `specs/INDEX.md` row) |

## Done (spec §10)

| # | Question | Answer and evidence |
|---|---|---|
| 1 | Sign-in, HttpOnly SameSite=Strict cookie, `/me` names person, tenant, roles | Yes. `test_the_cookie_attributes[None/on/off]` (attrs compared lower-case: `httponly`, `samesite=strict`, `path=/api`, `max-age=43200`, `secure` unless `off`), `test_success_shapes` (person, `tenant {slug,name}` from MB2 `tenant()`, `session_expires_at`); `/me` 503 when the tenant row is missing (`test_me_without_a_tenant_row_is_503`) |
| 2 | Unknown email = wrong password; 6th attempt locks | Yes. `test_refused_sign_ins_are_identical` (six paths, identical body and headers); `test_every_refused_path_is_one_refusal_after_exactly_one_verification[x6]` (spy: one `verify_password`, stored hash or `DUMMY_HASH`; status after it); lockout tests (minutes 11 then 1, no row on the locked try, unlocks at 15 min, success resets, unknown email locks); Postgres `test_guarded_attempt_counts_failures_and_locks` |
| 3 | Only an executive grants/removes, own tenant, every change a row, newest first | Yes. `test_grant_refusals_in_order`, `test_removal_refusals_in_order` (other tenant's person, Site and grant: 404, no row), `test_the_record_is_newest_first_and_state_is_derived`, Postgres `test_every_port_method_round_trips` |
| 4 | Never without an executive, even concurrently; locks shown waiting | Yes. LAST_EXECUTIVE on removal and on disabling (service + `onboard` subprocess). Four lock proofs (below) |
| 5 | Append-only records, revoke-only sessions, insert-and-purge attempts, by the database | Yes. Postgres: UPDATE/DELETE refused on the four tables; session: only `revoked_at` once; attempt: UPDATE refused, purge DELETE accepted, 31-day row purged on insert, 29-day row kept; every CHECK refuses a planted row; removal trigger and one-removal index |
| 6 | No existing route/command/screen changed | Yes. `git diff --stat main...HEAD`: only §0 files plus `mid-build-questions.md` and bookkeeping. `main.py`: imports, the `accounts` keyword (last) and one router block after `health_router`. `host/lab_app.py` untouched |
| 7 | Focused files, regression pair, check-all pass; planted guard violations fail | Yes, below |

## Tests (rev `c7f2016d6`)

- No-DB: `pytest test_3c0a_passwords.py test_3c0a_accounts_service.py test_3c0a_accounts_api.py -q`: **69 passed**,
  ~28 s; repeated 6 times, 69 passed each (after fixing two same-instant status rows in the tests, see Deviations).
- Postgres (`ASSETOPS_TEST_DATABASE_URL=.../assetops_test tools/heavy-slot.sh -- pytest test_3c0a_accounts_postgres.py
  test_3c0a_onboard_postgres.py test_pg_harness.py test_up1_reading_upload_postgres.py -q`): **40 passed**, 189 s
  wall, routed `assetops_pt<run>_*_test` databases only (warnings: alembic `path_separator` deprecation, harness).
- Guard alone: `check-architecture.ps1 -Only configuration-persistence.ps1`: passed.
- check-all (fast, `pwsh -NoProfile -File tools/check-all.ps1`, at the finish commit's tree): **All 38 guards
  passed**, 220 s wall. A first run at `c7f2016d6` failed 2 of 38: the estate guard self-test anchors on the
  `$pgWriters` line text (fixed: `$pgWriters += $accountWriter` on its own line), and `specs/INDEX.md` 51 bytes over
  its 8000-byte cap plus a packet path not yet written (fixed: shorter row).
- `python3 tools/select-tests.py --base main`: `mode: full (515 of 515 backend test files)` (because `main.py` and
  migration 0062). **Not run**: spec §9 and `backend/TESTING.md` put the full backend tier at the merge (owner,
  19 Nov: no expensive full run while building). The dispatch asked for "its selected set"; with a full selection
  that is the merge-time run, left to the coordinator.

## Concurrency proof (R2, R5, R6)

Each test holds the advisory lock on its own connection, starts two threads, polls `pg_locks` until **two advisory
locks are waiting** (`NOT granted`), sleeps 0.5 s, asserts both threads alive, commits, joins, then checks:
two removals of the last two executives (one `LAST_EXECUTIVE`, one executive held), two identical grants (one
`ROLE_ALREADY_HELD`, one held grant), two `create --executive` (one `EXECUTIVE_EXISTS`), two sign-ins under
`sign_in:<sha>` (both waited, both succeeded, two attempt rows). All four pass.

## Personal data

- `sign_in_attempt` stores `email_key_sha256` only (CHECK `^[0-9a-f]{64}$`; service test asserts the typed email is
  absent); `person_id` only on success (CHECK `succeeded = (person_id IS NOT NULL)`).
- A malformed email writes **no row** (still one dummy verification): service test `[malformed email]`.
- Every attempt insert runs `DELETE FROM sign_in_attempt WHERE at < :before` (now − 30 days) in its transaction;
  Postgres test shows the 31-day row gone, the 29-day row kept.
- Sessions store the token's SHA-256 only. Accounts, credentials, statuses and grants stay undeletable (Q5, pilot).

## Guard (spec §8)

`configuration-persistence.ps1`: `$accountWriter` declaration with eight shapes (six plain INSERTs, the revoke, the
purge), `$pgWriters` (a separate `+=` line, see above), `$pgWritesSeen`, `$pgDriverSeen`, the rule block, the anti-vacuity loop, and an `accounts`
domain entry (needed: the composition imports the adapter). Planted, then reverted (`git checkout`):
1. `UPDATE role_grant SET role = :role WHERE id = :id` in the adapter: exit 1, "The account store runs only its
   declared statements ...: postgres_account_store.py:57: UPDATE role_grant SET role = :role".
2. `INSERT INTO role_grant ...` in a new `accounts/rogue.py`: exit 1, "A second product database writer in
   backend/assetops_backend/accounts/rogue.py:3" (plus driver-import failures).
3. The same INSERT in the reading-upload adapter (a registered writer): exit 1, "Only
   .../postgres_account_store.py writes account table 'role_grant'".

## Mid-build questions

Count **2** (`mid-build-questions.md`): Q1 (R8 needs session `created_at` and credential `set_at`), Q2 (tenant
slug/name by id; `/me` expiry). Ruled MB1, MB2 and built as ruled; the R8 test is a normal test.

## Known deviations

- `build_accounts_router` gains `unavailable=()` (the reading-upload tuple pattern R14 names): the guard refuses a
  `sqlalchemy` import in `accounts_api.py`, so the adapter exports `UNAVAILABLE = (OperationalError, InterfaceError)`,
  `composition.ACCOUNTS_UNAVAILABLE` re-exports it, and `create_app` passes it.
- Guard: one more place than §8 lists (the `accounts` domain entry).
- `AccountService.tenant(principal)` added (MB2's read for the routes); `onboard_set_password/status` return the
  person ID (the command prints it). Model constants `EXECUTIVE`, `ATTEMPT_DAYS` added.
- `GrantRow.grant_id` on a GRANTED row is its own `row_id` (the database stores NULL); this is what `Person.roles`
  and the removal path call `grant_id`.
- The store answers `add_grant` with the row as recorded, so `site_code` is the Site's own code.
- Tests: two tests wrote an ACTIVE and a DISABLED status at the same clock instant (latest-row order then
  depends on random ids; flaky); the clock now advances between them.

## Not verified

- `--name` is passed as typed; a blank or padded name fails the database CHECK with a traceback (no refusal code
  in the spec).
- Sign-in timing parity measured only by call count (one scrypt per path), not wall time.
- The `Secure` cookie over the walkthrough's http address (Q4, `3C0b`).
- Full backend suite (see above).

## Review focus

The adapter's lock/re-check order, `resolve`'s validity conditions, the refusal order in `accounts_api.py`,
migration text against spec §2. User review: not needed for the build (non-screen; OD-20); the decision queue
Q1-Q5 defaults stand for the owner.
