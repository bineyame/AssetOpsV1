# 3C0a rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines: `.ai/decisions/index-rulings-7.md`. Handshake
answers go below under "Handshake answers (round 1)" and are folded into `spec.md`.

## D-3C0A.1 Accounts behind the API now; the screens and the refusal later

- **Ruling.** This unit adds accounts, sessions, role grants and their routes. It changes no existing route and
  refuses no existing command.
- **Why.** The owner started non-screen work and held screens (20 Nov). If commands were refused without a person
  before a sign-in page exists, today's screens would stop working. `3C1` records the person; the refusal switches on
  with `3C0b`'s sign-in page (D-BW1.3).

## D-3C0A.2 Every record is a row; current state is derived

- **Ruling.** Accounts, credentials, statuses, grants and attempts are append-only (the 0005 trigger). Only a session's
  `revoked_at` may be set, once. Current password, status and held grants are the latest rows.
- **Why.** OD-14 asks that every grant and removal be on record with its person and time; `decision-loop-specification.md`
  §8 makes `role_grant` append-only with "a removal is a new row". Applying the same rule to credentials and
  statuses gives one rule for the whole unit, and an auditor can see every change. A session is not a record of a
  decision; making it revoke-only keeps sign-out simple without allowing any other edit.

## D-3C0A.3 Email is unique across all tenants

- **Ruling.** `email_key` is globally unique; sign-in takes email and password, no tenant.
- **Why.** "One set of accounts per operator" (OD-13) is kept: each account belongs to one tenant. A global key
  removes a tenant field from sign-in, which the operator's people should not have to know. A person who works for
  two operators uses two emails; that is rare before SaaS scale and can be revisited with single sign-on.

## D-3C0A.4 Role codes are the manifest's; only the Site manager carries a Site

- **Ruling.** `OPERATOR_EXECUTIVE`, `FINANCE_AND_COMMERCIAL_LEAD`, `SITE_MANAGER`, `FIELD_TECHNICIAN`, `ANALYST`.
  `SITE_MANAGER` requires a Site; the others must not have one.
- **Why.** The manifest's `demo_workflow.tenants[].people` already uses these codes, and only Site managers carry a
  Site there. `decision-loop-specification.md` §8 says "Site where the role is Site-bound", and its permission table
  binds only the Site manager's choices to a Site. No other role exists: no Admin, no Viewer.

## D-3C0A.5 The tenant keeps one executive

- **Ruling.** A removal that would leave no ACTIVE account holding `OPERATOR_EXECUTIVE` is refused, under a per-tenant
  advisory lock with the check inside the transaction.
- **Why.** Only the executive grants roles (OD-14). With none left, nobody could grant again except by the onboarding
  command, so the rule prevents a locked-out operator. The lock makes two simultaneous removals safe.

## D-3C0A.6 One refusal for every failed sign-in, with a dummy hash and a lockout

- **Ruling.** Unknown email, wrong password, disabled account and missing credential give the same 401 body; the
  unknown-email path still runs scrypt; five failures in fifteen minutes lock the email key.
- **Why.** Telling them apart, by words or by timing, would tell an outsider which emails have accounts. The lockout
  bounds password guessing. The parameters are conventional and are revisited at the pilot (decision queue Q3).

## D-3C0A.7 The onboarding command creates people; only the first executive gets a role from it

- **Ruling.** `create --executive` grants `OPERATOR_EXECUTIVE` by `service:onboarding`, and only when the tenant has
  none. Every other grant comes from the executive through the API.
- **Why.** "The first executive of a tenant is created when the operator is onboarded" (`decision-loop-specification.md`
  §8); OD-14 says roles are granted and removed by the executive. Creating an account is not granting a role, so
  the command may create the others' accounts without breaking OD-14.

## D-3C0A.8 The demo people's accounts are not this unit's

- **Ruling.** Seeding Amina, Joseph, Peter and the others into the walkthrough database is done when that database is
  built (`WK`), after `3C0b`.
- **Why.** Their accounts need emails and passwords the manifest does not hold, and a walkthrough sign-in needs the
  sign-in page. Seeding them now would be data no screen can use.

## D-3C0A.9 The seam `3C1` uses is `accounts.principal.person_from_request`

- **Ruling.** One function turns a request into a `PersonPrincipal` or `None`, reading the `assetops_session` cookie.
- **Why.** Every command module today takes an injected principal (`mini_decision_principal`, `domain_work_principal`,
  `operational_entry_principal` in `create_app`). `3C1` replaces those injections with this one function; naming it
  now keeps `3C1` from reaching into the store.

## D-3C0A.10 Standard-library scrypt, no new dependency

- **Ruling.** `hashlib.scrypt` with n = 32768, r = 8, p = 1, a 16-byte salt and a 32-byte key, in a self-describing
  string.
- **Why.** No password library is in `backend/pyproject.toml`, and adding one needs the coordinator's dependency
  change in every worktree (`frontend/node_modules` precedent, lane rules). scrypt is memory-hard and in the standard
  library. Measured 0.13 s per hash on this machine (20 Nov), acceptable for sign-in. The parameters are in the
  stored string, so a later change verifies old hashes.

## Handshake answers (round 1)

Answered once, 2026-11-20, and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. "Adopted" means the
proposed answer is the ruling. Where the Reviewer and the Implementer disagreed, the choice is named.

### Highs

- **R1 / P7 / P8 (High): sign-in attempts hold no typed text, no person on a failure, and 30 days at most. New
  ruling D-3C0A.11.**
  - **What is stored.** `sign_in_attempt` stores `email_key_sha256`, the hex SHA-256 of the normalised key, never the
    key.
  - **A malformed email.** It writes no row: it can match no account. It still runs one dummy verification, and
    answers `SIGN_IN_REFUSED`.
  - **The person.** `person_id` is set only on a success. Every failure has `NULL`, so failures for known and unknown
    emails look alike.
  - **Retention: insert and purge.** Every attempt insert runs, in the same transaction, `DELETE FROM sign_in_attempt
    WHERE at < :before`, with `:before` = now − 30 days. The table has no append-only trigger. It has a trigger that
    refuses UPDATE only, and the guard registers that one DELETE shape. There is an index on `at`.
  - **A known limit, stated for the pilot.** Accounts, credentials, statuses and grants are undeletable by design
    (D-3C0A.2). Erasing a person's personal data is a pilot data-protection question; it is in the decision queue
    (Q5).
- **R2 (High): the concurrency tests prove the lock.**
  1. The test opens its own connection and takes `pg_advisory_xact_lock(hashtextextended('role_grant:' || <tenant>,
     0))`.
  2. It starts the two operations in threads.
  3. After 0.5 s it asserts that neither thread has finished (`Thread.is_alive()`).
  4. It commits to release the lock and joins the threads.
  5. It asserts exactly one refusal and the surviving state.

  The same shape covers three pairs: two removals of the last two executives (one `LAST_EXECUTIVE`), two identical
  grants (one `ROLE_ALREADY_HELD`), and two `create --executive` (one `EXECUTIVE_EXISTS`). A per-email shape covers two
  sign-ins under the sign-in lock (R5). The reviewer's "run five times" probe is withdrawn.

### Security Mediums

- **R3: adopted.** An email is printable ASCII only: `[!-?A-~]{1,64}@[!-?A-~]{1,255}`, applied with `fullmatch` (no
  `@`, space or control character on either side), at most 320 characters. Python's `lower()` then equals Postgres
  `lower()`. Internationalised addresses wait for single sign-on. New `normalise_email` cases: a non-ASCII letter, a
  NUL and a space give `BAD_EMAIL`.
- **R4: adopted.** Every refused sign-in path runs exactly one scrypt verification before answering: the stored hash
  when one exists, else `DUMMY_HASH`. The status check comes after the verification. The service test spies on
  `verify_password` on all five paths (unknown email, malformed email, wrong password, disabled, no credential).
- **R5: adopted, with the lock.**
  - **The lock.** Count, verify and insert run under a per-email advisory lock, through one store method,
    `guarded_attempt(key_sha256, now, verify)`. Inside one transaction it:
    1. takes `pg_advisory_xact_lock(hashtextextended('sign_in:' || :key_sha256, 0))`;
    2. counts the failures since the later of now − 15 min and the latest success;
    3. returns `Locked(retry_at)` at 5 or more failures;
    4. otherwise calls `verify()`, which does the account read and the scrypt and returns `(succeeded, person_id)`;
    5. inserts the attempt, purges, and returns the result.
  - **The in-memory store** uses a `threading.Lock` per key.
  - **A success resets the count.** Four failures, a success, then one failure: not locked.
  - **An unknown email locks** exactly as a known one, because the key is hashed whether or not an account exists.
  - **Why the lock rather than a looser bound.** The route runs in a thread pool of about 40, so without it the bound
    would be 5 plus 40 guesses per window.
- **R6: adopted.** Four writes take the per-tenant lock and re-check inside it: a grant, a removal, `create_account`
  with an executive grant, and `set_status` to DISABLED.
- **R7 over P13 (second point): disabling the last ACTIVE executive is refused, `LAST_EXECUTIVE`.** The command exits
  2 with the same words. `EXECUTIVE_EXISTS` counts held executive grants on ACTIVE accounts only. To replace a
  departing sole executive, the existing executive grants the role to the successor through the API, then the old
  account is disabled. So the invariant lives in one place and a tenant is never left with no executive. P13's other
  points are adopted:
  - a grant to a DISABLED account is allowed;
  - `LAST_EXECUTIVE` counts ACTIVE accounts only;
  - `create --executive` takes the tenant lock;
  - `people()` sorts in Python by `(display_name.casefold(), email_key)`.
- **R8: adopted, derived.** A session is valid only if its `created_at` is not before the latest credential's
  `set_at`. A `resolve` test covers it.
- **R9: adopted.**
  - Every route is `async`. It reads the body with a limit of 4 KiB; a larger body is 422 `ACCOUNTS_BAD_REQUEST` with
    `field = "body"`.
  - Every service call goes through `run_in_threadpool`, as `reading_upload_api.py` does.
  - A password over 128 characters at sign-in is `SIGN_IN_REFUSED`, after one dummy verification. Only the first 128
    characters reach scrypt, so a long string costs no more.

### Mediums and Lows

- **R10: adopted.** The onboarding test builds the subprocess environment from scratch:
  - `DATABASE_URL` is the routed URL from the `engine` fixture;
  - it asserts the database name ends in `_test` and is not `assetops_test`;
  - an inherited `DATABASE_URL` is never used.
- **R11: adopted.** The downgrade drops exactly `role_grant_removal_matches()`, `operator_session_revoke_only()` and
  `sign_in_attempt_no_update()`, never `ledger_append_only()`. The down-then-up test asserts that an 0005 trigger on
  an older table still refuses an UPDATE after the downgrade.
- **R12: (a) adopted.** API tests use `TestClient(app, base_url="https://testserver")`, and the `off` case uses http
  (P10 confirmed). **(b)** is a note for `3C0b`: cookies are shared across ports on one host. **(c)** is stated in
  spec §5: the defence against cross-site requests is SameSite=Strict, plus the required JSON content type, plus no
  CORS middleware. A later slice that adds CORS with credentials removes part of it and must say so.
- **R13 with P5: the order of refusals** is 503 `ACCOUNTS_UNAVAILABLE`, then 415 `JSON_REQUIRED`, then 422
  `ACCOUNTS_BAD_REQUEST`, then 401 `NOT_SIGNED_IN`, then the service's order. The body's shape is checked without
  touching the session; this is R13's order rather than P5's. 415 and 422 apply to all four POST routes, sign-out
  included. Sign-out never answers 401. Every `/api/auth/*` and `/api/organisation/*` response carries
  `Cache-Control: no-store`.
- **R14: adopted.** `sqlalchemy.exc.OperationalError` and `InterfaceError` from the store are answered 503
  `ACCOUNTS_UNAVAILABLE`, through an `unavailable` tuple as in reading-upload.
- **R15: adopted.** The words are "Too many attempts. Try again in a few minutes." The `minutes` value stays in
  `params`.
- **P1: adopted.** The coordinator merges the spec branch; the build branch is cut after that.
- **P2: adopted.** `AccountService` gains `onboard_create(tenant_slug, email, display_name, password, *, executive)
  -> UUID`, `onboard_set_password(email, password)` and `onboard_set_status(email, status, reason)`, each by
  `ONBOARDING`. `onboard.py` imports only `composition.build_account_service`.
- **P3: adopted.** The port gains `grant_row(tenant_id, grant_id) -> GrantRow | None`.
- **P4: adopted.** There are six more words, which makes 21 codes in all.
- **P6: adopted.** `field` is `"body"` when the body is not JSON or not an object. Otherwise it is the first unknown
  key in sorted order, then the first missing or wrongly typed key in the route's listed order. `site_code` may be
  absent or `null`.
- **P9: adopted.** Tests compare cookie attribute names and values case-insensitively. Sign-out clears the cookie
  with `set_cookie(value="", max_age=0)` and the same `HttpOnly`, `SameSite`, `Path` and `Secure` as at sign-in.
- **P11: adopted.** `host/lab_app.py` does not change; §0 is corrected.
- **P12: adopted.** `UPGRADE = r"""..."""`.
- **P14: 2.5 units, as one slice.** `3C0a` changes from 2 to 2.5 units in `plan_model.py`, and the plan documents are
  re-filled. The onboarding command stays in the slice, because a slice without it cannot create the first executive,
  and `3C1`'s tests need a signed-in person built by the real path.
- **P15: adopted.** The finish bookkeeping is allowed and excluded from the scope check. "Status" means the
  `specs/INDEX.md` row.

**Open after round 1:** none for the handshake. One owner item remains, Q1 (is `3C0a` inside the non-screen start),
with its default applied.

## D-3C0A.11 Sign-in attempts are hashed, person-free on failure, and purged after 30 days

- **Ruling.** As R1 above.
- **Why.** The lockout needs only "failures for this key lately". Storing what people typed, or naming them on a
  failed attempt, keeps personal data for no purpose. Conservative by default (coordinator, 20 Nov).
