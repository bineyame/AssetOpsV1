# 3C0a handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Fresh Reviewer (Claude), 2026-11-20, at `2a56ed99c`. Read: `spec.md`, `rulings.md`, `reviewer-guide.md`, the BW1
rulings; checked against `main.py` `create_app`, `reading_upload_api.py`, migrations 0001, 0005 and 0061,
`backend/tests/pg_harness.py`, `test_health.py` and `route_inventory.py`, `tools/heavy-slot.sh`, and the guard block
at `configuration-persistence.ps1:915-960`. Verified, no question: the head is `0061_reading_upload`; `site` has
`UNIQUE (tenant_id, id)` and `site_code_key`; `ledger_append_only()` exists (0005) and refuses every UPDATE and
DELETE; no CORS or cookie middleware is mounted (only `LocaleMiddleware`); no existing path starts with `/api/auth` or
`/api/organisation`, no frontend code calls them, and the route-inventory tests pin only the `{site_id}` and
`/api/findings` paths, so the seven new routes break no existing test or route.

**The decision queue (§13).** Q1 and Q2 are real owner questions with sound defaults. Q3 is real; R5 adds a gap in
it. Q4 is real and rightly `3C0b`'s; R12 adds two notes for it.

Severity: **High** blocks coding until answered; **Medium** changes what is built or tested; **Low** is a wording or
coverage fix. **(done)** marks a question whose answer changes what counts as done.

- **R1 (High, done) — §2 `sign_in_attempt`, §3 Sign-in: personal data kept forever, including what people mistype.**
  Every sign-in writes the typed email key in plain text into an append-only table (the 0005 trigger forbids DELETE),
  including keys of people who have no account and whatever was typed in the email box: a password typed into the
  email field is stored in clear, permanently. The 1-320 length CHECK also means a long typed value raises a 500
  instead of a 401. The lockout needs only "failures for this key in the last 15 minutes". *Proposed:* (a) store
  `email_key_sha256` (hex SHA-256 of the key) instead of the key: the lock still works and nothing typed stays
  readable; (b) a sign-in whose email fails `normalise_email` writes no attempt row (it can match no account, so it
  gives no guessing value) but still runs the dummy verify and returns the same 401; (c) `sign_in_attempt` is "insert
  and purge", not append-only: one guard-registered `DELETE FROM sign_in_attempt WHERE at < :before` shape with a
  stated retention (proposed 30 days), run by nothing yet; or, if the Architect keeps the table append-only now, a
  decision-queue line naming retention for the pilot. Accounts (email, name) are also undeletable by design
  (D-3C0A.2); say so as a known limit for the pilot.

- **R2 (High, done) — §9 Postgres file, §10 Q4: the last-executive concurrency test can pass without the lock.** "Two
  threads removing the two last executives at once" gives one refusal whenever the two transactions do not overlap,
  which is the usual case for two threads on a fast machine. Without the advisory lock it would still pass most runs,
  so it does not prove D-3C0A.5. *Proposed:* make the overlap certain: the test opens its own connection and takes
  `pg_advisory_xact_lock` on the tenant's key, starts both removals in threads, asserts after 0.5 s that neither has
  finished (both wait on the lock, which proves the adapter takes it), then commits to release; exactly one
  `LAST_EXECUTIVE` and one held executive must result. Use the same shape for two identical grants and two
  `create --executive` (R6). P5's "run it five times" is then unnecessary.

- **R3 (Medium, done) — §3 Email, §2 CHECK: the key computed in Python must equal Postgres `lower()`.** The CHECK
  `email_key = lower(email)` uses the database's `LC_CTYPE`; Python's `str.lower()` lowercases non-ASCII letters (and
  `İ` becomes two characters). Where they differ the insert fails with an IntegrityError: a 500 at the API, a
  traceback in the command. The pattern `[^@\s]` also admits NUL and other control characters; Postgres text refuses
  NUL, so a sign-in with `\x00` in the email raises instead of answering 401. *Proposed:* an email is printable ASCII
  only (U+0021-U+007E except `@`, either side), applied with `re.fullmatch`; internationalised addresses wait for single
  sign-on. Add `normalise_email` cases: a non-ASCII letter and a NUL, both `BAD_EMAIL`.

- **R4 (Medium) — §3 Sign-in, D-3C0A.6: timing parity for the disabled and no-credential paths.** Only the unknown-email
  path is said to verify against `DUMMY_HASH`. A disabled account or one with no credential that returns before scrypt
  answers in milliseconds, against 0.13 s for a wrong password, so timing tells that the email has an account.
  *Proposed:* every refused path runs exactly one scrypt verification (the stored hash, else `DUMMY_HASH`) before
  answering, and the status check comes after it. The service test spies on `verify_password` on all four paths.

- **R5 (Medium, done) — §3 Lockout: concurrent guesses, and whether a success resets the count.** The count is read,
  the password is checked (0.13 s), then the attempt is written; N parallel requests all read "fewer than 5" and all
  get a guess, so the bound is 5 plus the concurrency. Also unstated: 4 failures, a success, 1 failure: locked?
  *Proposed:* take a per-email advisory lock (`hashtextextended('sign_in:' || :key_hash, 0)`) around count, verify and
  insert in one transaction, or accept the looser bound and say so; count failures "since the later of 15 minutes ago
  and the last success". Add service tests for the reset case and for an unknown email locking exactly like a known
  one (else the lock itself enumerates accounts).

- **R6 (Medium, done) — §3 Concurrency, D-3C0A.5: which writes take the tenant lock.** §3 names "each grant and
  removal". Three more writes need it: `create_account` with `executive_grant` (two simultaneous `create --executive`
  both see no executive and both grant: `EXECUTIVE_EXISTS` is read-then-write); a plain grant (two identical grants both
  pass "already held": no unique index covers held grants); and `set_status` to DISABLED (R7). *Proposed:* all four take
  the same tenant lock, and the store re-checks inside it.

- **R7 (Medium, done) — D-3C0A.5: disabling the last executive is not refused.** The rule refuses a removal that would
  leave no ACTIVE account holding `OPERATOR_EXECUTIVE`, but `disable --email` on that executive has the same result;
  `create --executive` then refuses `EXECUTIVE_EXISTS` (a held grant remains on the disabled account), so the only way
  back is `enable`. *Proposed:* `disable` refuses `LAST_EXECUTIVE` too (exit 2, same words), keeping the invariant in
  one place; or `EXECUTIVE_EXISTS` counts only executives on ACTIVE accounts. Add the case to the onboarding test.

- **R8 (Medium, done) — §3 Session, §7 `set-password`: a new password leaves old sessions alive.** After `set-password`
  (the answer to a leaked password) every session signed in with the old password stays valid for up to 12 hours.
  *Proposed:* derived, no UPDATE: a session is valid only if its `created_at` is not before the latest credential's
  `set_at` (one more condition in `resolve`). Add it to the service test's `resolve` cases.

- **R9 (Medium) — §5: scrypt off the event loop, and a body size limit.** The reading-upload routes are `async` and run
  their work through `run_in_threadpool` after a size-bounded body read (`reading_upload_api.py:59`, `:98`). An `async`
  sign-in route calling the service directly would block the server's event loop for each 0.13 s, 32 MiB scrypt.
  *Proposed:* state the precedent: bodies are read with a small limit (4 KiB; over it 422 `ACCOUNTS_BAD_REQUEST`), and
  every service call goes through `run_in_threadpool`. A password over 128 characters at sign-in is `SIGN_IN_REFUSED`
  (still one dummy verify, R4).

- **R10 (Medium) — §9 onboarding test, §0 Databases: the command's `DATABASE_URL` in a subprocess.** The harness
  rewrites `ASSETOPS_TEST_DATABASE_URL` to a run-owned `assetops_pt<run>_<tag>_test` database; the command reads
  `DATABASE_URL`. If the subprocess environment is built from anything but the routed value (or inherits a shell
  `DATABASE_URL`), the command writes to the shared `assetops_test` or another database. *Proposed:* the test sets
  `DATABASE_URL` from the routed `ASSETOPS_TEST_DATABASE_URL` (the `engine` fixture's URL), asserts the database name
  ends `_test` and is not `assetops_test` itself before running the command, and drops any inherited `DATABASE_URL`.

- **R11 (Medium) — §2 downgrade: which functions it drops.** "Drop triggers, functions, indexes and tables in reverse
  order" must drop only `role_grant_removal_matches()` and `operator_session_revoke_only()`, never 0005's
  `ledger_append_only()`, which older tables' triggers still use. *Proposed:* name the two functions in §2; the
  down-then-up test also asserts an existing 0005 trigger still refuses an UPDATE after the downgrade.

- **R12 (Low) — §5 cookie, queue Q4: the API tests, and notes for `3C0b`.** (a) With `Secure` on, `TestClient`'s
  `http://testserver` base does not send the cookie back, so tests that sign in then call `/api/auth/me` must use
  `base_url="https://testserver"` or the `off` setting; say which. (b) Cookies are not isolated by port: the
  walkthrough server and any other AssetOps server on the same host share `assetops_session` for `Path=/api`, so
  signing in on one replaces the other's session. A note for `3C0b`, no change here. (c) The CSRF defence is
  SameSite=Strict plus the required JSON content type plus no CORS middleware; state it in §5, so a later slice adding
  CORS with credentials knows it removes a defence.

- **R13 (Low) — §5: refusal precedence and caching.** For `POST /api/organisation/role-grants` with no session and a
  form body, is it 401 or 415? *Proposed:* 415, then 422, then 401, then the service's order; one sentence in §5.
  Also `Cache-Control: no-store` on every `/api/auth/*` and `/api/organisation/*` response (personal data and
  `Set-Cookie`).

- **R14 (Low) — §5: a database outage.** With `accounts` built but Postgres unreachable, does sign-in answer 503
  `ACCOUNTS_UNAVAILABLE` or 500? *Proposed:* 503 with the same words, catching SQLAlchemy's `OperationalError` in the
  router, as reading-upload's `unavailable` tuple does.

- **R15 (Low) — §5 Words: "Try again in 1 minutes".** `retry_minutes` is at least 1. *Proposed:* "Try again in a few
  minutes." (the number stays in `params`), or two keys; no plural machinery.

## Implementer pre-flight questions

(none yet)

## Implementer pre-flight

Implementer (Claude), 2026-11-20. Pre-flight of `spec.md` rev 1 against `main` at `e3052032d`, read-only; no code.
**(done)** marks an answer that changes what counts as done. Each item has its evidence and a proposed answer.

**Checked and true as the spec says:**
- Migrations: `0061_reading_upload` is the head (`0061:21-22`; nothing else pins it); `ledger_append_only()` is at
  `0005:310`; `site` has `UNIQUE (tenant_id, id)` (`0001:78`), so the composite FK holds.
- `create_app` (`main.py:234-263`) is keyword-only. `config.database_url()` is at `config.py:108` and
  `ConfigurationError` at `config.py:27`. `create_app()` runs with no `DATABASE_URL` (existing tests delete it).
- The words: `render(msg, locale=None)` is at `i18n/render.py:8`, and `CATALOGUE["en"]` at `i18n/messages.py:26`.
  The refusal body `{code, message, words}` follows `reading_upload_api.py:40-42`.
- The test harness:
  - `pg_harness` names databases `<stem>_pt<run>_<tag>_test` (`pg_harness.py:72-80`).
  - `empty_tables` empties the FK closure from `tenant` (`pg_harness.py:338-367`), so the six new tables are
    emptied between tests even with the append-only triggers.
  - The `store` and `engine` fixtures come from `test_s1_bindings_postgres.py:67-86`, imported as
    `test_up1_reading_upload_postgres.py:28` does. The downgrade pattern is at `test_up1:90-110`.
  - `tools/heavy-slot.sh [--db] ... -- <command>` (line 4). The conftest asks for a slot only when
    `ASSETOPS_TEST_DATABASE_URL` is set (`conftest.py:141`).
- `select-tests` gives `full` for the migration and `main.py`, as §9 says.
- Routes: no route test pins `/api/auth` or `/api/organisation` (`test_health.py` pins only `/api/findings*` and
  `{site_id}` paths), and no such path exists today.
- Measured here: scrypt takes 0.12 s, and the encodings are 22 and 43 characters.
- The manifest's role codes match, and only `SITE_MANAGER` carries a Site.
- Versions: FastAPI 0.162.5, Starlette 1.10.0.

- **P1 (done) The spec folder is not on `main`.** `specs/3C0a-operator-accounts/` exists only on
  `task/build-wave1-specs` (`git merge-base main 2a56ed99c` is `56300a810`), so a branch cut from `main` has no home
  for the packet. *Proposed:* the coordinator merges the spec branch into `main` when the handshake closes, and the
  build branch is cut after that merge.
- **P2 (done) The onboarding command has no service to call.** §4.2's `AccountService` has no create, set-password or
  status method. §4 makes `composition.py` "the only importer of the adapter", and §7's command needs exactly those
  writes. *Proposed:* add `AccountService.onboard_create(tenant_slug, email, display_name, password, *, executive:
  bool) -> UUID`, `onboard_set_password(email, password)` and `onboard_set_status(email, status, reason)`, each
  recorded as `ONBOARDING`. `onboard.py` then imports only `composition.build_account_service`.
- **P3 Removal needs a grant lookup the port lacks.** `remove(principal, grant_id)` must find the GRANTED row to
  answer `GRANT_NOT_FOUND` and to copy its person, role and Site into the REMOVED row. §4.1 offers only
  `grant_rows(tenant_id)`, which returns the whole record. *Proposed:* add the port method
  `grant_row(tenant_id, grant_id) -> GrantRow | None`. It returns the row with that id; a REMOVED row's id is
  answered `GRANT_NOT_FOUND` by the service.
- **P4 (done) The onboarding refusals have no sentences.** §7 says "`<CODE>` and one plain sentence", but §5's words
  table lacks `TENANT_NOT_FOUND`, `BAD_EMAIL`, `EMAIL_TAKEN`, `PASSWORD_POLICY`, `EXECUTIVE_EXISTS` and
  `DATABASE_URL_REQUIRED`. *Proposed:* six more `accounts.*` keys in the same `# 3C0a` block, rendered in English
  by the command:
  - `TENANT_NOT_FOUND`: "No organisation has that code."
  - `BAD_EMAIL`: "That is not an email address."
  - `EMAIL_TAKEN`: "An account already uses that email."
  - `PASSWORD_POLICY`: "A password has 12 to 128 characters and is not only spaces."
  - `EXECUTIVE_EXISTS`: "This organisation already has an operator executive."
  - `DATABASE_URL_REQUIRED`: "Set DATABASE_URL to the product database."
  The reviewer's W6 sweep of codes then counts 21, not 15.
- **P5 (done) The order of the generic refusals, and sign-out.** §5 says every POST requires JSON, yet sign-out's row
  says "Refusals: none". The order of 503, 401, 415 and 422 is not given. *Proposed:* the order is 503
  `ACCOUNTS_UNAVAILABLE`, then 401 `NOT_SIGNED_IN` (routes that need a session), then 415, then 422, then the service.
  415 and 422 apply to all four POST routes, sign-out included (the reviewer's sweep covers all four). Sign-out never
  answers 401. The table's refusal column lists only the domain refusals.
- **P6 `ACCOUNTS_BAD_REQUEST`'s `field`.** It is not defined for a body that is not JSON-decodable or not an object.
  *Proposed:* `field = "body"` in that case. Otherwise the field is the first unknown key in sorted order, then the
  first missing or wrong-typed key in the route's listed order. `site_code` may be absent or `null`; any other
  non-string is wrong-typed.
- **P7 (done) Sign-in with a malformed email.** §3 says "every outcome writes one `sign_in_attempt` row". But
  `email_key`'s CHECK is 1 to 320 characters, so an empty or over-long input cannot be stored. *Proposed:* `BAD_EMAIL`
  at sign-in writes no attempt row, still runs the dummy verification, and answers `SIGN_IN_REFUSED`. Lockout counts
  only valid keys.
- **P8 `sign_in_attempt.person_id` on a failure for a known email.** Not specified. *Proposed:* `NULL` on every
  failure and set only on success (the CHECK allows this), so the failed rows of known and unknown emails look alike.
- **P9 The cookie as Starlette writes it.** Starlette 1.10 writes `SameSite=strict` in lower case, and its
  `delete_cookie` writes `SameSite=lax` with no `HttpOnly` or `Secure`. Measured:
  `assetops_session=abc; HttpOnly; Max-Age=43200; Path=/api; SameSite=strict; Secure` and `assetops_session="";
  expires=...; Max-Age=0; Path=/api; SameSite=lax`. §5 and reviewer probe P3 say `SameSite=Strict`. *Proposed:* tests
  compare attribute names and values case-insensitively (RFC 6265bis). Sign-out clears the cookie with
  `set_cookie(value="", max_age=0)` carrying the same `HttpOnly`, `SameSite`, `Path` and `Secure` as sign-in.
- **P10 The default `Secure` cookie and `TestClient`.** With the variable unset the cookie is `Secure`, and httpx's
  cookie jar does not send a `Secure` cookie to `http://testserver`, so a sign-in then `/me` flow fails under the
  default (measured: over http `/api/me` saw no cookie; over https it did). *Proposed:* the API tests use `TestClient(app, base_url="https://testserver")`, and the `off` case uses
  http. Confirm only; no spec change.
- **P11 (done) `host/lab_app.py`.** §0 lists it among the files edited, §6 says it "needs no change", and the reviewer
  guide's scope list omits it. *Proposed:* no change to `host/lab_app.py`, and §0 is corrected.
- **P12 The migration string.** The §2 CHECK `'^scrypt\$32768\$8\$1\$...'` inside a non-raw `"""` (the 0061 style,
  `0061:28`) is an invalid `\$` escape. That is a SyntaxWarning on Python 3.12, and an error under `-W error`.
  *Proposed:* `UPGRADE = r"""..."""` (as `0001:50` does). The SQL text stays character for character.
- **P13 A disabled person, and the last executive.** Neither case is specified. *Proposed:*
  - A grant to a DISABLED account is allowed (status and roles are independent; `LAST_EXECUTIVE` counts ACTIVE
    accounts only).
  - The onboarding `disable` of the last ACTIVE executive is allowed: it is the operator-level recovery path and
    `enable` restores it. The packet notes it against D-3C0A.5.
  - `create --executive` checks `EXECUTIVE_EXISTS` under the same per-tenant advisory lock as grants.
  - `people(tenant_id)` sorts in Python by `(display_name.casefold(), email_key)`, not by a collation-dependent
    `ORDER BY`.
- **P14 (done) The estimate looks low at 2 units.** The scope is:
  - a six-table migration with two functions and seven triggers;
  - about 20 port methods in the adapter, plus an in-memory store in the tests that must re-implement
    `ROLE_ALREADY_HELD`, `LAST_EXECUTIVE` and `EXECUTIVE_EXISTS`;
  - the service, 7 routes and 21 words (P4);
  - a CLI with four sub-commands;
  - five test files, with a concurrency test and a downgrade test;
  - guard registration, which touches six places in `configuration-persistence.ps1`, not one block: the declaration
    (~925), `$pgWriters` (985-988), `$pgWritesSeen` (1053-1058), `$pgDriverSeen` (1059-1065), the rule block
    (~1461-1475) and the anti-vacuity loop (~1789-1793). Two planted proofs come on top.

  *Proposed:* 2.5 units. Alternatively, keep 2 and move the onboarding command (§7 and
  `test_3c0a_onboard_postgres.py`) to a 0.5-unit follow-up before `WK`. `3C1` needs only the seam and the store.
- **P15 (done) Finish bookkeeping falls outside §10 Q6's scope.** The standing brief requires a `.ai/state/` entry and
  its index line, and the spec's status. The specs have no `Status:` line; the status lives in the `specs/INDEX.md` row
  (line 73). *Proposed:* those files are allowed and are excluded from the scope check, and the status means that row.
