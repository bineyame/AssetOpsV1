# 3C0a review, round 1 (discovery, W5)

Reviewer: fresh Claude (not the author), 2026-11-20. Branch `task/3C0a-operator-accounts` at `72d7383fb`
(commits `43fcbda84` tests first, `2b9f24759` merge of main, `c7f2016d6` implementation, `72d7383fb` packet).
Reviewed in a scratch worktree at that head (removed afterwards); the author's worktree was not touched.

## Summary

- **Verdict: ACCEPT with Lows.** No High or Medium. Four Lows, none an acceptance gap against spec §10.
- Migration 0062 is the spec §2 SQL exactly (a whitespace-normalised comparison found no difference), plus the
  four `ledger_append_only()` triggers. The downgrade drops only the three 0062 functions.
- Security mechanics check out: scrypt n=32768/r=8/p=1, one scrypt on every refused path, a 256-bit token stored
  only as SHA-256, the cookie flags, the per-email lock with reset on success, R8, LAST_EXECUTIVE on removal and on
  disable, tenant isolation, the refusal order, no-store, 4 KiB, and 503 when the store is down.
- Reran: the no-database files (69 passed), the pooled Postgres set (40 passed), the persistence guard, the full
  architecture guard, the agent-workflow guard, and an 11-file route and catalogue regression set (275 passed).
- **Plants: 14 of my own, all caught.** One more plant (a success no longer resets the count, in the adapter SQL)
  was caught only by my own probe test, not by the branch's tests: L1.
- Personal data: OK at runtime. The onboarding command prints the email and the name in a traceback when a
  database CHECK fails: L2.
- Full suite: not needed to judge this slice. The merge-time fast tier is `backend/TESTING.md` policy anyway.
  The sufficient regression set is given at the end.

## Findings

### L1 (missing test, not an acceptance gap): "a success resets the count" is untested against Postgres
`backend/assetops_backend/accounts/adapters/postgres_account_store.py:97-100` (`_RECENT_FAILURES`). The reset rule
(R5, reviewer guide P2) is tested only against the in-memory store, and that store is written in the test file
(`test_3c0a_accounts_service.py:358`). I planted `... AND succeeded AND false` in the adapter's subquery, which
breaks the reset, and all of `test_3c0a_accounts_postgres.py` and `test_3c0a_onboard_postgres.py` still passed
(17 passed). Only my probe failed. Today's SQL is correct: the probe passes on the clean tree. The implementer
followed spec §9, which puts this case in the service tests. **Fix:** add a Postgres test like this one:
4 failures, then a success, then 2 failures at minutes 0-6, then `not locked`.
```python
for m in range(4): accounts.guarded_attempt(key, T0 + timedelta(minutes=m), lambda: (False, None))
accounts.guarded_attempt(key, T0 + timedelta(minutes=4), lambda: (True, world["exec_id"]))
accounts.guarded_attempt(key, T0 + timedelta(minutes=5), lambda: (False, None))
assert not accounts.guarded_attempt(key, T0 + timedelta(minutes=6), lambda: (False, None)).locked
```
Sweep (W6): check the other store rules for in-memory-only coverage. I checked them: the lock, the purge,
LAST_EXECUTIVE on disable and on removal (plants PG1, PG3, PG4, PG5), ROLE_ALREADY_HELD and EXECUTIVE_EXISTS are
all covered against Postgres.

### L2 (personal data in an error): the onboarding command prints the email and name in a traceback
`backend/assetops_backend/accounts/onboard.py:56-67` and `postgres_account_store.py:116`. The command catches only
`AccountRefused`. A `--name` that is blank, padded or over 120 characters, or a `--reason` that is empty or over
500 characters, fails a database CHECK. SQLAlchemy's `IntegrityError` text carries `[parameters: ...]`. A probe
(`onboard_create(..., " Padded ", ...)`) confirmed that the error text contains the email. The password hash was
not in it, because the failing statement was the account INSERT. The packet names the traceback but not that it
carries personal data. The server routes do not hit this: 503 swallows the store error, and nothing in
`accounts/` logs. **Fix (either):** refuse a bad name or reason in the service with a code, which needs an
Architect word; or build the engine with `create_engine(url, pool_pre_ping=True, hide_parameters=True)`, which
also keeps parameters out of any server 500 traceback.

### L3 (robustness): a password with a lone surrogate answers 500, not 401
`passwords.py:35` (`password.encode("utf-8")`). A JSON body `"password":"\ud800..."` passes `_json` as a `str`,
and `UnicodeEncodeError` is then raised inside `verify()`. A probe got a server exception on both the known-email
path and the malformed-email path. This breaks no security property:
- no stored password can contain a lone surrogate, so it cannot succeed;
- the 500 is the same for known and unknown emails;
- the attempt transaction rolls back, so the try is not counted.

It does break "one code and one body" for refused sign-ins (spec §3). **Fix:** encode with
`"surrogatepass"` in `_derive`, or refuse non-encodable strings in `_json` as 422.

### L4 (spec literal): framework 404 and 405 answers under `/api/auth/` carry no `Cache-Control`
Spec §5 says "every response under `/api/auth/` and `/api/organisation/`". `GET /api/auth/sign-in` (405),
`PUT /api/auth/me` (405) and `GET /api/auth/nothing` (404) have no `no-store`. None of these answers carries
personal data. Preference-level. Close it with a small path-scoped middleware, or record it as accepted.

## Checklist (reviewer guide)

- **Scope:** `git diff --stat main...HEAD` shows 26 files. All are in spec §0/§8 plus `mid-build-questions.md` and
  the P15 bookkeeping. `host/lab_app.py` is untouched.
- **`main.py`:** imports, the `accounts` keyword (last), and one router block after `health_router`. No existing
  route, dependency or middleware changed. No CORS middleware exists anywhere (grep).
- **Tests first:** `43fcbda84` holds the five files before any code. The later test edits in `c7f2016d6` are two
  clock advances (same-instant status rows) and the memory store recording `site_code`. Neither weakens a test.
- **P1 enumeration:** the six refused paths give identical bodies and headers. A spy shows exactly one
  `verify_password` call. Status is checked after it; plant P6, which moves the status check first, is caught.
- **Timing parity:** one scrypt on each path. The query count differs by one or two cheap reads between unknown and
  known emails (milliseconds against about 130 ms of scrypt). The malformed-email path does no database work, but
  it reveals nothing. Residual only.
- **Session:** the token is `token_urlsafe(32)` (256 bits). Only `sha256(token)` is stored and looked up. Validity
  checks revoked, expiry, `created_at >= set_at` (MB1), ACTIVE, and that the account exists.
- **Cookie:** `HttpOnly; SameSite=strict; Path=/api; Max-Age=43200`, and `Secure` unless `off`. Sign-out clears it
  with the same attributes. A bad env value refuses `create_app`.
- **P2 lockout:** a per-email `pg_advisory_xact_lock` is held across count, verify and insert (the verify reads
  use the same connection). It counts failures after `greatest(now-15m, latest success)`, and
  `retry_at = 5th-latest + 15m`. A locked try writes no row.
- **P2b personal data:** `sign_in_attempt` holds only `email_key_sha256`, a person only on success (CHECK), no row
  for a malformed email, and a purge on every insert.
- **P4 tenant isolation:** person, Site and grant are all looked up by the principal's tenant. Covered by tests.
- **P5 lock proofs:** all four hold the lock on their own connection, wait for two `NOT granted` advisory locks,
  then sleep 0.5 s and assert that both threads are alive. They are not plain races.
- **P6/P7:** checked in the Postgres tests. Database triggers and CHECKs are in place.
- **P8 guard:** passes clean. My three extra plants fail it: `ON CONFLICT` on the session insert, a
  `DELETE FROM operator_session`, and an `UPDATE account_status` from `service.py`.
- **P9 words:** all 21 codes match the spec table character for character (scripted compare). There are 21
  `accounts.*` keys.
- **Refusal order:** 503 (no service), then 415, then 422 (body or keys), then 401, then the service's order.
  Covered by `test_refusal_order_503_415_422_401`. `application/json; charset=utf-8` and `Application/JSON` are
  accepted; `text/plain` and `application/json-patch+json` get 415. A 5 KB chunked body without Content-Length
  gets 422 `field=body`.
- **CSRF basis:** SameSite=Strict, the required JSON content type, and no CORS. The GET routes are reads.
- **Migration:** see the summary. The downgrade is refused while an account exists (tested). Down then up works,
  and an 0005 trigger still refuses afterwards (tested).
- **Nothing breaks before 3C0b:** the routes are additive. With `DATABASE_URL` set, `create_app` builds a lazy
  engine (it does not connect). `DUMMY_HASH` adds about 0.13 s at import.

## Deviations, judged on merit

- **`unavailable=()` on `build_accounts_router`:** sound. The guard forbids `sqlalchemy` in `accounts_api.py`,
  and this is the reading-upload pattern. `create_app` always passes `ACCOUNTS_UNAVAILABLE`.
- **`accounts` domain entry in the guard:** needed and correct (only the composition imports the adapter).
- **`grant_id` on a GRANTED row equals its `row_id`:** sound. It is what `Person.roles[].grant_id` and the removal
  route need. It is derived with `COALESCE` in reads, and the database still stores NULL, so the CHECK holds.
- **Extra service methods:**
  - `AccountService.tenant(principal)` is MB2's read.
  - `onboard_set_*` returning the person ID serves the command's output.
  - `EXECUTIVE` and `ATTEMPT_DAYS` are constants.

  All are harmless.
- **`add_grant` answers the row as recorded:** better than echoing the request (it gives the Site's own code).

## Residual risk the packet does not name

- **Password-change race:** a sign-in that reads the old credential in the milliseconds between the onboarding
  command's `set_at` clock read and its commit gets a session with `created_at > set_at`. That session survives
  the new password. The window is milliseconds, and onboarding is an operator action.
- **ROLE_REQUIRED is not re-checked under the tenant lock:** an executive whose role is removed concurrently can
  complete one in-flight grant. The spec's port does not carry the actor into `add_grant`, so this is spec-level
  (R6 lists "its refusal rules"). LAST_EXECUTIVE still holds, because removal re-checks under the lock.
- **Lockout by design:** anyone can lock any email for 15 minutes. There is no per-IP limit, so spraying one
  password across many emails is not limited. These are Q3 defaults; revisit at the pilot.
- **The `Secure` cookie over the walkthrough's http address:** this is 3C0b's question (Q4), as the guide says.

## What I ran (my own runs, at 72d7383fb)

- `pytest test_3c0a_passwords.py test_3c0a_accounts_service.py test_3c0a_accounts_api.py -q`: **69 passed**, 28 s.
- `tools/heavy-slot.sh -- pytest test_3c0a_accounts_postgres.py test_3c0a_onboard_postgres.py test_pg_harness.py
  test_up1_reading_upload_postgres.py -q` (routed `*_test` databases only): **40 passed**, 189 s.
- **No-database plants (each reverted):** each failed its test.

  | Plant | Failing test |
  |---|---|
  | P2: no dummy hash on a malformed email | `[malformed email]` |
  | P3: plain email key passed to `guarded_attempt` | `test_sign_in_writes_one_succeeded_attempt...` |
  | P4: a session older than the credential allowed | `test_resolve_none_after_a_later_password` |
  | P6: status checked before the verification | `[disabled]` |
  | P8: a 129-character password accepted | `test_the_129_character_password...` |
  | P9: sign-out without no-store | `test_cache_control_no_store_on_all_seven_routes` |

- **Postgres plants (pooled, each reverted):**

  | Plant | Result |
  |---|---|
  | PG1: per-email lock dropped | `test_lock_two_sign_ins_wait_on_the_per_email_lock` failed |
  | PG2: a success no longer resets the count | only my probe failed (L1) |
  | PG3: disabling the last executive allowed | `test_the_onboarding_command` failed |
  | PG4: no purge | `test_sign_in_attempt_is_insert_and_purge` failed |
  | PG5: no tenant lock on removal | `test_lock_two_removals_of_the_last_two_executives` failed |

- **Guard plants** (`check-architecture.ps1 -Only configuration-persistence.ps1`, with
  `ASSETOPS_GUARD_PYTHON` set): all three failed (P8 above). Clean: passed.
- `check-architecture.ps1` (all): passed. `check-agent-workflow.ps1`: passed.
- Regression, no database: `test_health`, `test_w205a_ev_roles`, `test_t027_overview`, `test_t027_ingestion`,
  `test_simulator_lab_gate`, `test_uq6a_message_seam`, `test_up1_reading_upload`, `test_sites_api`,
  `test_site_templates_api`, `test_site_template_fingerprints`, `test_scenario_fingerprints`: **275 passed**.
- Not rerun: check-all (I cite the packet: 38/38 at the finish commit); the full suite; wall-time timing parity.

## Full suite

`select-tests` picks the full suite only because `main.py` and a migration changed. The change is additive: new
tables, no change to existing tables, and new route paths only. Where it touches the rest:

- **Alembic head and downgrade.** 41 Postgres test files call `command.downgrade`, and each now passes through
  0062's downgrade. That downgrade is safe on empty account tables, and the harness's FK-closure cleanup includes
  the six tables through `tenant`.
- **Route inventory.** `test_health` and similar tests check that the inventory is not vacuous.
- **The message catalogue.**
- **`create_app` with `DATABASE_URL` set.**

My judgment: the full suite is not needed to accept the slice. A sufficient regression set is the focused files,
the regression pair, the 11 no-database files above, and the 41 `*downgrade*`-calling Postgres files (grep
`downgrade(` in `backend/tests`), run pooled. The merge-time full fast tier is standing `backend/TESTING.md`
policy ("at every merge to main"), so the coordinator runs it regardless. The slow tier that policy adds for
schema merges adds little here, since no existing table changes. Skipping it is the coordinator's or owner's call
under that policy.
