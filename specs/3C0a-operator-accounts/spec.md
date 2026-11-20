# 3C0a: operator accounts and roles behind the API (implementer spec)

Architect (Claude), 2026-11-20. **Rev 2** (handshake round 1 folded in: `rulings.md` "Handshake answers (round 1)", D-3C0A.11). Rev 1 was spec handshake step 1 (`.ai/RULES.md` §4). Lane A, first unit of the
non-screen build (`specs/BW1-build-wave1/rulings.md` D-BW1.1, D-BW1.3). Decisions with reasons: `rulings.md`
(D-3C0A.1 to D-3C0A.10). Reviewer: `reviewer-guide.md`. Questions: `handshake.md`, then `mid-build-questions.md`.

Structure approved with the pack (OD-20, page P1): `decision-loop-specification.md` §8, OD-13, OD-14. Non-screen: it
adds routes and tables and changes no existing route, screen or command. The sign-in page and Organisation settings
are `3C0b` (screen, held). Discovery review (W5: new schema, a security mechanism, a new seam).

## 0. Before you start

- **Branch** `task/3C0a-operator-accounts` off `main` after the coordinator has merged `task/build-wave1-specs` (P1); worktree
  `/opt/assetecon/AssetOpsV1-3c0a`. Never work in `/opt/assetecon/AssetOpsV1`.
- **Gate.** Code starts when the handshake has no open question. No owner sitting is needed (OD-20).
- **Read:** this spec; `rulings.md`; `decision-loop-specification.md` §8 (in the pack); for style,
  `backend/migrations/versions/0061_reading_upload.py`, `backend/assetops_backend/reading_upload/` (service, adapter,
  API), `backend/assetops_backend/i18n/messages.py`, `host/lab_app.py:72-137`, `backend/assetops_backend/main.py:234-263`
  and its `include_router` calls, `tools/checks/configuration-persistence.ps1:915-960`, `backend/TESTING.md` §"The
  heavy-tool slot pool" and §"The test database", `.agent/lane-rules-vps-2026-11-12.md`.
- **Python.** `export PYTHONPATH=$PWD/backend:$PWD/backend/tests:$PWD/contracts:$PWD/simulator:$PWD/gateway:$PWD/field:$PWD/host:$PWD/tools`
  (absolute, from the worktree root) and `PY=/opt/assetecon/AssetOpsV1/.venv/bin/python`.
- **Databases.** Only `*_test` databases on `assetopsv1-postgres-1` (127.0.0.1:55432, `assetops`/`assetops-local-dev`):
  set `ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test`;
  the harness routes each run to its own `assetops_pt<run>_<tag>_test` and drops it at the end. Every Postgres test
  file runs through the slot pool: `tools/heavy-slot.sh -- <command>`. No heavy database job is needed, so `--db` is
  not used. The onboarding command (§7) is run only by tests against those routed databases. Never touch ports 5490
  or 8990, the walkthrough DB (`assetops_polish_walk1113_test`) or Docker.
- **Migration number.** Write it as `0062_operator_accounts` (`down_revision = "0061_reading_upload"`). If another
  migration reaches `main` first, the coordinator renumbers at merge preparation (`delivery-plan.md` §2).
- **Collisions.** The UI lanes and DS1m edit only `Docs/.../interactive-mockup-vNEXT/` and `Docs/design-system/`; no
  overlap. `2a` (lane B) edits only `contracts/`; no overlap. You edit `backend/` (not `host/lab_app.py`, P11),
  `tools/checks/configuration-persistence.ps1`, this folder's packet and the finish bookkeeping (P15: the
  `.ai/state/` entry and its index line, the `specs/INDEX.md` row).

## 1. Outcome and why

People of an operator have accounts: they sign in with email and password, and the operator executive grants and
removes their roles, each change on record. The API can say who is signed in. This is the first unit of step 3C,
because `3C1` (every command recorded under the person) and through it the targets, decisions and plan of steps 5 to
7 need an authenticated person. Gate questions it answers (`delivery-plan.md` §3, step 3C, the first two): does each
person sign in with an email-and-password account of their own operator; are roles granted and removed only by the
operator executive, each change on record?

**What does not change.** No existing route, command or screen. Commands are not yet refused without a person: that
switch arrives with the sign-in page (D-BW1.3, `3C1` and `3C0b`), so today's screens keep working.

## 2. Records (migration `0062_operator_accounts`)

`TABLES = ("operator_account", "account_credential", "account_status", "role_grant", "operator_session",
"sign_in_attempt")`. The upgrade is exactly this SQL (the 0061 style: one `UPGRADE` string, `op.execute`; a raw string
`r"""..."""` as in 0001, because of the `\$` in the hash CHECK, P12):

```sql
CREATE TABLE operator_account (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    email text NOT NULL CHECK (char_length(email) BETWEEN 3 AND 320 AND email = btrim(email)),
    email_key text NOT NULL UNIQUE CHECK (email_key = lower(email)),
    display_name text NOT NULL CHECK (char_length(display_name) BETWEEN 1 AND 120 AND display_name = btrim(display_name)),
    created_at timestamptz NOT NULL,
    created_by text NOT NULL CHECK (created_by ~ '^(service:[a-z][a-z0-9-]{0,62}|person:[0-9a-f-]{36})$'),
    UNIQUE (tenant_id, id)
);
CREATE TABLE account_credential (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    person_id uuid NOT NULL,
    password_hash text NOT NULL CHECK (password_hash ~ '^scrypt\$32768\$8\$1\$[A-Za-z0-9_-]{22}\$[A-Za-z0-9_-]{43}$'),
    set_at timestamptz NOT NULL,
    set_by text NOT NULL CHECK (set_by ~ '^(service:[a-z][a-z0-9-]{0,62}|person:[0-9a-f-]{36})$'),
    FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE INDEX account_credential_person ON account_credential (person_id, set_at DESC, id);
CREATE TABLE account_status (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    person_id uuid NOT NULL,
    status text NOT NULL CHECK (status IN ('ACTIVE', 'DISABLED')),
    reason text NULL CHECK (reason IS NULL OR char_length(reason) BETWEEN 1 AND 500),
    set_at timestamptz NOT NULL,
    set_by text NOT NULL CHECK (set_by ~ '^(service:[a-z][a-z0-9-]{0,62}|person:[0-9a-f-]{36})$'),
    FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account (tenant_id, id)
);
CREATE INDEX account_status_person ON account_status (person_id, set_at DESC, id);
CREATE TABLE role_grant (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    person_id uuid NOT NULL,
    role text NOT NULL CHECK (role IN ('OPERATOR_EXECUTIVE', 'FINANCE_AND_COMMERCIAL_LEAD', 'SITE_MANAGER',
                                       'FIELD_TECHNICIAN', 'ANALYST')),
    site_id uuid NULL,
    action text NOT NULL CHECK (action IN ('GRANTED', 'REMOVED')),
    grant_id uuid NULL REFERENCES role_grant (id),
    by_person_id uuid NULL,
    by_service text NULL CHECK (by_service IS NULL OR by_service ~ '^service:[a-z][a-z0-9-]{0,62}$'),
    at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account (tenant_id, id),
    FOREIGN KEY (tenant_id, by_person_id) REFERENCES operator_account (tenant_id, id),
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    CHECK ((role = 'SITE_MANAGER') = (site_id IS NOT NULL)),
    CHECK ((action = 'REMOVED') = (grant_id IS NOT NULL)),
    CHECK ((by_person_id IS NULL) <> (by_service IS NULL))
);
CREATE UNIQUE INDEX role_grant_one_removal ON role_grant (grant_id) WHERE action = 'REMOVED';
CREATE INDEX role_grant_tenant_at ON role_grant (tenant_id, at DESC, id);
CREATE INDEX role_grant_person ON role_grant (tenant_id, person_id);
CREATE FUNCTION role_grant_removal_matches() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.action = 'REMOVED' AND NOT EXISTS (
        SELECT 1 FROM role_grant g
        WHERE g.id = NEW.grant_id AND g.action = 'GRANTED' AND g.tenant_id = NEW.tenant_id
          AND g.person_id = NEW.person_id AND g.role = NEW.role AND g.site_id IS NOT DISTINCT FROM NEW.site_id) THEN
        RAISE EXCEPTION 'role_grant removal % does not match a granted row', NEW.id;
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER role_grant_removal_check BEFORE INSERT ON role_grant
    FOR EACH ROW EXECUTE FUNCTION role_grant_removal_matches();
CREATE TABLE operator_session (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    person_id uuid NOT NULL,
    token_sha256 text NOT NULL UNIQUE CHECK (token_sha256 ~ '^[0-9a-f]{64}$'),
    created_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz NULL,
    FOREIGN KEY (tenant_id, person_id) REFERENCES operator_account (tenant_id, id),
    CHECK (expires_at > created_at),
    CHECK (revoked_at IS NULL OR revoked_at >= created_at)
);
CREATE INDEX operator_session_person ON operator_session (person_id, created_at DESC);
CREATE FUNCTION operator_session_revoke_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'operator_session rows are never deleted';
    END IF;
    IF OLD.revoked_at IS NOT NULL OR NEW.revoked_at IS NULL
       OR (NEW.id, NEW.tenant_id, NEW.person_id, NEW.token_sha256, NEW.created_at, NEW.expires_at)
          IS DISTINCT FROM (OLD.id, OLD.tenant_id, OLD.person_id, OLD.token_sha256, OLD.created_at, OLD.expires_at) THEN
        RAISE EXCEPTION 'operator_session allows only setting revoked_at once';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER operator_session_revoke BEFORE UPDATE OR DELETE ON operator_session
    FOR EACH ROW EXECUTE FUNCTION operator_session_revoke_only();
CREATE TABLE sign_in_attempt (
    id uuid PRIMARY KEY,
    email_key_sha256 text NOT NULL CHECK (email_key_sha256 ~ '^[0-9a-f]{64}$'),
    at timestamptz NOT NULL,
    succeeded boolean NOT NULL,
    person_id uuid NULL REFERENCES operator_account (id),
    CHECK (succeeded = (person_id IS NOT NULL))
);
CREATE INDEX sign_in_attempt_email ON sign_in_attempt (email_key_sha256, at DESC);
CREATE INDEX sign_in_attempt_at ON sign_in_attempt (at);
CREATE FUNCTION sign_in_attempt_no_update() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'sign_in_attempt rows are inserted and purged, never updated';
END;
$$;
CREATE TRIGGER sign_in_attempt_no_update BEFORE UPDATE ON sign_in_attempt
    FOR EACH ROW EXECUTE FUNCTION sign_in_attempt_no_update();
```

Then, for each of `operator_account`, `account_credential`, `account_status`, `role_grant` (not `sign_in_attempt`,
which is insert-and-purge, D-3C0A.11):
`CREATE TRIGGER <table>_immutable BEFORE UPDATE OR DELETE ON <table> FOR EACH ROW EXECUTE FUNCTION
ledger_append_only();` (the 0005 function). The downgrade follows 0061: `LOCK` every table, refuse with
`RAISE EXCEPTION 'Downgrade of 0062_operator_accounts refused: accounts exist'` if `operator_account` has a row, then
drop triggers, indexes and tables in reverse order and exactly the functions `role_grant_removal_matches()`,
`operator_session_revoke_only()` and `sign_in_attempt_no_update()`; never 0005's `ledger_append_only()` (R11). The adapter writes every timestamp itself (from the
service clock); there are no column defaults.

**Current state is derived, never stored** (D-3C0A.2): a person's password is the latest `account_credential` row by
`(set_at, id)`; the status is the latest `account_status` row; a grant is held while its GRANTED row has no REMOVED
row naming it.

## 3. Rules

- **Roles** (codes as the manifest's `demo_workflow.tenants[].people`), in this order everywhere a list is sorted:
  `OPERATOR_EXECUTIVE`, `FINANCE_AND_COMMERCIAL_LEAD`, `SITE_MANAGER`, `FIELD_TECHNICIAN`, `ANALYST`. Only
  `SITE_MANAGER` carries a Site, and it must (D-3C0A.4). A person may hold several grants.
- **Email.** Trimmed of surrounding whitespace, then it must `re.fullmatch` `[!-?A-~]{1,64}@[!-?A-~]{1,255}`
  (printable ASCII, no `@`, space or control character on either side; R3) and be at most 320 characters.
  `email_key = email.lower()`, which then equals Postgres `lower()`. Unique across all tenants (D-3C0A.3). The
  attempt record stores `email_key_sha256 = sha256(email_key.encode("ascii")).hexdigest()`, never the key.
- **Password** (set only by the onboarding command in this unit): 12 to 128 characters, not all whitespace, kept
  exactly as typed (no trimming or normalisation). Hash: `hashlib.scrypt(password.encode("utf-8"),
  salt=os.urandom(16), n=32768, r=8, p=1, maxmem=67108864, dklen=32)`, stored as
  `scrypt$32768$8$1$<salt>$<hash>` with unpadded URL-safe base64 (22 and 43 characters). Verify with
  `hmac.compare_digest`. A stored hash in any other form fails verification (it never raises). About 0.13 s per hash
  on this machine (measured 20 Nov).
- **Sign-in.** Email and password. Every refused path runs exactly one scrypt verification before answering: the
  stored hash when one exists, else `DUMMY_HASH` (a module constant made once at import with a fixed salt); the
  status check comes after it (R4). Refused with one code and one body for an unknown email, a malformed email, a
  wrong password, a password over 128 characters (only its first 128 reach scrypt), a disabled account or an account
  with no credential (D-3C0A.6).
- **Attempt records** (D-3C0A.11). A malformed email writes no row. Every other outcome writes one row, except a
  locked refusal (so a lock cannot extend itself): `person_id` only on a success, `NULL` on every failure. Each insert
  runs, in its transaction, `DELETE FROM sign_in_attempt WHERE at < :before` with `:before = now - 30 days`.
- **Lockout** (R5). Under a per-email advisory lock
  (`pg_advisory_xact_lock(hashtextextended('sign_in:' || :key_sha256, 0))`), held across count, verification and
  insert: when the key has 5 or more failures with `at` after the later of `now - 15 min` and the key's latest
  success, sign-in is refused as locked before the password is checked. `retry_minutes = ceil((t5 + 15 min - now) /
  1 min)`, at least 1, `t5` the earliest of the 5 most recent counted failures. An unknown email locks exactly as a
  known one. A success resets the count.
- **Session.** A token `secrets.token_urlsafe(32)`; only its SHA-256 hex is stored. It lasts 12 hours from sign-in,
  absolute, not sliding. A session is valid while not expired, not revoked, the account is ACTIVE, and its
  `created_at` is not before the latest credential's `set_at` (a new password ends older sessions; R8). Sign-out
  revokes it (idempotent).
- **Grant.** Only a person holding `OPERATOR_EXECUTIVE` grants or removes. The target person and Site must be the
  executive's own tenant's. A grant that is already held (same person, role, Site) is refused. A removal of a grant
  already removed is refused. Removing a held `OPERATOR_EXECUTIVE` grant is refused when it would leave the tenant
  with no person holding that role on an ACTIVE account (D-3C0A.5); so is disabling the last ACTIVE executive (R7). The
  executive may remove their own roles subject to that rule. A grant to a DISABLED account is allowed (P13).
  `EXECUTIVE_EXISTS` counts held executive grants on ACTIVE accounts only.
- **Concurrency** (R6). Four writes each run in one transaction that first takes
  `SELECT pg_advisory_xact_lock(hashtextextended('role_grant:' || CAST(:tenant_id AS text), 0))` and then re-checks its refusal
  rules inside the transaction: a grant, a removal, `create_account` with an executive grant, and `set_status` to
  DISABLED.
- **Who did it.** A grant or removal by a person stores `by_person_id`; the onboarding command stores
  `by_service = 'service:onboarding'`. `created_by` and `set_by` are `person:<uuid>` or `service:onboarding`.

## 4. Code: package `backend/assetops_backend/accounts/`

| File | Holds |
|---|---|
| `model.py` | `ROLES` (tuple, the order above), `SITE_ROLE = "SITE_MANAGER"`, `SESSION_HOURS = 12`, `LOCK_FAILURES = 5`, `LOCK_MINUTES = 15`, `COOKIE = "assetops_session"`, `ONBOARDING = "service:onboarding"`; frozen dataclasses `Account(id, tenant_id, email, display_name)`, `PersonPrincipal(person_id, tenant_id, display_name, roles: frozenset[tuple[str, UUID | None]], session_id, at)` with `has_role(role, site_id=None) -> bool` (a SITE_MANAGER check needs the Site; any other role ignores `site_id`), `GrantRow(row_id, grant_id, tenant_id, person_id, display_name, role, site_id, site_code, action, by_person_id, by_display_name, by_service, at)`, `PersonView(person_id, display_name, email, status, grants: tuple[GrantRow, ...])`, `SignedIn(principal, token, expires_at)`; `AccountRefused(Exception)` with `code`, `status` and `params` |
| `passwords.py` | `hash_password(pw) -> str`, `verify_password(pw, stored) -> bool`, `check_policy(pw) -> None` (raises `AccountRefused("PASSWORD_POLICY", 422)`), `normalise_email(text) -> tuple[str, str]` (email, key; raises `AccountRefused("BAD_EMAIL", 422)`), `DUMMY_HASH` |
| `store.py` | `AccountStore` (a `typing.Protocol`) with the methods of §4.1; `StoreConflict(Exception)` with `code` |
| `service.py` | `AccountService` (§4.2) |
| `principal.py` | `person_from_request(request, accounts) -> PersonPrincipal | None`: reads the `assetops_session` cookie and calls `accounts.resolve`; the seam `3C1` uses (D-3C0A.9) |
| `composition.py` | `build_account_service(database_url: str) -> AccountService` (the only importer of the adapter), `session_cookie_secure() -> bool` (§6) |
| `adapters/postgres_account_store.py` | `PostgresAccountStore(url)`: SQLAlchemy `text()` statements, as the reading-upload adapter |
| `onboard.py` | the command of §7 (`python -m assetops_backend.accounts.onboard`) |
| `../accounts_api.py` | `build_accounts_router(accounts: AccountService | None, *, cookie_secure: bool) -> APIRouter` (§5) |

### 4.1 Store port

`tenant_by_slug(slug) -> tuple[UUID, str] | None` (id, name); `site_id(tenant_id, site_code) -> UUID | None` (by
`site_code_key`, as the existing Site lookups); `account_by_email_key(key) -> Account | None`;
`account(tenant_id, person_id) -> Account | None`; `current_credential(person_id) -> str | None`;
`current_status(person_id) -> str | None`; `held_grants(tenant_id, person_id) -> tuple[GrantRow, ...]`;
`guarded_attempt(key_sha256, now, verify: Callable[[], tuple[bool, UUID | None]]) -> Attempt` (R5: one transaction
under the per-email lock: count, return `Attempt(locked=True, retry_at)` if locked, else call `verify`, insert the row
(person only on success), purge rows older than 30 days, return `Attempt(locked=False, succeeded, person_id)`);
`grant_row(tenant_id, grant_id) -> GrantRow | None` (P3);
`add_session(id, tenant_id, person_id, token_sha256, created_at, expires_at)`;
`session(token_sha256) -> tuple[UUID, UUID, UUID, datetime, datetime | None] | None` (id, tenant, person, expires,
revoked); `revoke(token_sha256, at) -> None` (the one UPDATE; a no-op when already revoked);
`people(tenant_id) -> tuple[PersonView, ...]` (sorted in Python by `(display_name.casefold(), email_key)`, P13); `grant_rows(tenant_id) -> tuple[GrantRow, ...]`
(newest first by `(at, id)`); `add_grant(row: GrantRow) -> GrantRow` (refuses `ROLE_ALREADY_HELD` by `StoreConflict`);
`add_removal(row: GrantRow) -> GrantRow` (refuses `GRANT_ALREADY_REMOVED`, `LAST_EXECUTIVE`);
`create_account(account, password_hash, created_at, by, executive_grant: GrantRow | None) -> None` (one
transaction: the account, its credential, an ACTIVE status, and the optional first grant; refuses `EMAIL_TAKEN`,
and `EXECUTIVE_EXISTS` when `executive_grant` is given and the tenant already has a held `OPERATOR_EXECUTIVE` on an
ACTIVE account; under the tenant lock);
`set_credential(tenant_id, person_id, password_hash, at, by)`; `set_status(tenant_id, person_id, status, reason, at, by)`
(DISABLED under the tenant lock; refuses `LAST_EXECUTIVE`, R7). The in-memory test store re-implements every refusal
and uses a `threading.Lock` per key for `guarded_attempt`.

### 4.2 Service

`AccountService(store, *, clock: Callable[[], datetime], token: Callable[[], str] = secrets-based default)`:
- `sign_in(email, password) -> SignedIn`; raises `AccountRefused` `SIGN_IN_REFUSED` (401) or `SIGN_IN_LOCKED` (429,
  `params={"minutes": n}`). `BAD_EMAIL` at sign-in is reported as `SIGN_IN_REFUSED` too.
- `sign_out(token: str | None) -> None`.
- `onboard_create(tenant_slug, email, display_name, password, *, executive: bool) -> UUID`,
  `onboard_set_password(email, password) -> None`, `onboard_set_status(email, status, reason) -> None`: the
  onboarding command's writes, each by `ONBOARDING` (P2); refusals as §7.
- `resolve(token: str | None) -> PersonPrincipal | None`: `None` for no token, an unknown, expired or revoked
  session, a session older than the latest credential, or an account that is not ACTIVE. Roles are read from the held grants at each call (OD-14: current grants
  at each command).
- `people(principal) -> tuple[PersonView, ...]`, `grant_record(principal) -> tuple[GrantRow, ...]`: any signed-in
  person of the tenant (Organisation settings is read by every role).
- `grant(principal, person_id, role, site_code) -> GrantRow`; `remove(principal, grant_id) -> GrantRow`. Refusals in
  this order: `ROLE_REQUIRED` 403 (principal lacks `OPERATOR_EXECUTIVE`); `ROLE_UNKNOWN` 422; `ROLE_SITE_RULE` 422;
  `PERSON_NOT_FOUND` 404 (another tenant's person is also not found); `SITE_NOT_FOUND` 404; then the store's
  `ROLE_ALREADY_HELD` 409. For removal: `ROLE_REQUIRED` 403; `GRANT_NOT_FOUND` 404 (unknown, another tenant's, or a
  REMOVED row's id); `GRANT_ALREADY_REMOVED` 409; `LAST_EXECUTIVE` 409.

## 5. HTTP routes (`accounts_api.py`, mounted in `create_app`)

Every route is `async`, reads the body with a 4 KiB limit, and calls the service through `run_in_threadpool` (R9;
`reading_upload_api.py` precedent). Every POST, sign-out included, requires `Content-Type: application/json` (else 415
`JSON_REQUIRED`) and a JSON object body (else 422 `ACCOUNTS_BAD_REQUEST`). `params.field` is `"body"` when the body is
over 4 KiB, not JSON or not an object; otherwise the first unknown key in sorted order, then the first missing or
wrongly typed key in the route's listed order (`site_code` may be absent or `null`; P6). **Order of refusals** (R13):
503 `ACCOUNTS_UNAVAILABLE`, 415, 422, 401 `NOT_SIGNED_IN` (routes needing a session; sign-out never answers 401), then
the service's order. Every response under `/api/auth/` and `/api/organisation/` carries `Cache-Control: no-store`.
`sqlalchemy.exc.OperationalError` and `InterfaceError` from the store answer 503 `ACCOUNTS_UNAVAILABLE` (R14). The
table's refusal column lists only the domain refusals.
Every refusal body is `{"code", "message", "words"}` as the reading-upload routes (`message` rendered for the
request's locale, `words` the `Message`). With `accounts` None every route answers 503 `ACCOUNTS_UNAVAILABLE`.

| Route | Body | Success | Refusals |
|---|---|---|---|
| `POST /api/auth/sign-in` | `{"email", "password"}` (strings) | 200 `{"person": Person, "tenant": {"slug", "name"}, "session_expires_at"}` and the cookie | 401 `SIGN_IN_REFUSED`, 429 `SIGN_IN_LOCKED` |
| `POST /api/auth/sign-out` | `{}` | 204 and the cookie cleared with `set_cookie(value="", max_age=0)` and the same `HttpOnly`, `SameSite`, `Path` and `Secure` as sign-in (P9), with or without a session | none |
| `GET /api/auth/me` | none | 200 as sign-in's body | 401 `NOT_SIGNED_IN` |
| `GET /api/organisation/people` | none | 200 `{"people": [Person, ...]}` | 401 `NOT_SIGNED_IN` |
| `GET /api/organisation/role-grants` | none | 200 `{"rows": [GrantRecord, ...]}` newest first | 401 `NOT_SIGNED_IN` |
| `POST /api/organisation/role-grants` | `{"person_id", "role", "site_code"}` (`site_code` may be omitted or null) | 201 GrantRecord | 401, 403 `ROLE_REQUIRED`, 422 `ROLE_UNKNOWN`, 422 `ROLE_SITE_RULE`, 404 `PERSON_NOT_FOUND`, 404 `SITE_NOT_FOUND`, 409 `ROLE_ALREADY_HELD` |
| `POST /api/organisation/role-grants/{grant_id}/removal` | `{}` | 201 GrantRecord (the REMOVED row) | 401, 403 `ROLE_REQUIRED`, 404 `GRANT_NOT_FOUND`, 409 `GRANT_ALREADY_REMOVED`, 409 `LAST_EXECUTIVE` |

- `Person` = `{"person_id", "display_name", "email", "status", "roles": [{"grant_id", "role", "site_code"}]}`, roles
  sorted by the role order, then `site_code`; `site_code` is `null` for a role without a Site.
- `GrantRecord` = `{"row_id", "grant_id", "person_id", "display_name", "role", "site_code", "action", "by", "at"}`;
  `by` is `{"person_id", "display_name"}` or `{"service": "service:onboarding"}`; `at` ISO 8601 with offset.
- A malformed `person_id` or `grant_id` (not a UUID) is 404, as not found.
- **The cookie:** `assetops_session=<token>; HttpOnly; SameSite=Strict; Path=/api; Max-Age=43200`, plus `Secure` when
  `session_cookie_secure()` is true. Because unknown body keys are refused, a body that tries to name an actor is
  refused too (the browser never names an actor; `financial_api.py` precedent). Starlette writes `SameSite=strict`;
  tests compare attribute names and values case-insensitively (P9).
- **Cross-site requests** (R12c): the defence is SameSite=Strict, the required JSON content type and the absence of
  any CORS middleware. A later slice that adds CORS with credentials removes part of it and must say so.

**Words** (add to `i18n/messages.py`, English, under one `# 3C0a` comment; keys `accounts.<code lower case>`):

| Code | English |
|---|---|
| `SIGN_IN_REFUSED` | The email or password is not right. |
| `SIGN_IN_LOCKED` | Too many attempts. Try again in a few minutes. (`minutes` stays in `params`, R15) |
| `NOT_SIGNED_IN` | Sign in to continue. |
| `ROLE_REQUIRED` | Only the operator executive can change roles. |
| `ROLE_UNKNOWN` | That role does not exist. |
| `ROLE_SITE_RULE` | A Site manager is granted for one Site; other roles are granted without a Site. |
| `PERSON_NOT_FOUND` | No such person in this organisation. |
| `SITE_NOT_FOUND` | No such Site in this organisation. |
| `ROLE_ALREADY_HELD` | {name} already holds this role. |
| `GRANT_NOT_FOUND` | No such role grant in this organisation. |
| `GRANT_ALREADY_REMOVED` | This role was already removed. |
| `LAST_EXECUTIVE` | The organisation must keep one operator executive. |
| `JSON_REQUIRED` | Send the request as JSON. |
| `ACCOUNTS_BAD_REQUEST` | The request is not complete: {field}. |
| `ACCOUNTS_UNAVAILABLE` | Sign-in is not available on this server. |
| `TENANT_NOT_FOUND` | No organisation has that code. |
| `BAD_EMAIL` | That is not an email address. |
| `EMAIL_TAKEN` | An account already uses that email. |
| `PASSWORD_POLICY` | A password has 12 to 128 characters and is not only spaces. |
| `EXECUTIVE_EXISTS` | This organisation already has an operator executive. |
| `DATABASE_URL_REQUIRED` | Set DATABASE_URL to the product database. |

21 codes in all (P4); the last six are the onboarding command's, rendered in English by it.

## 6. Composition

- `create_app(..., accounts: AccountService | None = None)` (new keyword, last). Inside: when `accounts is None and
  database_url()`, `accounts = build_account_service(database_url())`; then
  `app.include_router(build_accounts_router(accounts, cookie_secure=session_cookie_secure()))`. With no URL the
  routes answer 503.
- `session_cookie_secure()` reads `ASSETOPS_SESSION_COOKIE_SECURE`: unset or `on` is true, `off` is false, anything
  else raises `ConfigurationError("ASSETOPS_SESSION_COOKIE_SECURE must be 'on', 'off' or unset")` at `create_app`.
  `host/lab_app.py` needs no change: `build_app` passes overrides through.
- No existing route, dependency or middleware changes.

## 7. Onboarding command (`python -m assetops_backend.accounts.onboard`)

Reads `DATABASE_URL` (`config.database_url()`; unset is exit 2 `DATABASE_URL_REQUIRED`). Passwords come from the first
line of stdin (the trailing newline removed, nothing else). It imports only `composition.build_account_service` and
calls the service's `onboard_*` methods (P2). Success prints the person ID and exits 0; a refusal prints
`<CODE>` and one plain sentence to stderr and exits 2.

| Sub-command | Does | Refusals |
|---|---|---|
| `create --tenant SLUG --email E --name N [--executive]` | creates the account, its credential and an ACTIVE status; with `--executive`, also the tenant's first `OPERATOR_EXECUTIVE` grant by `service:onboarding` | `TENANT_NOT_FOUND`, `BAD_EMAIL`, `EMAIL_TAKEN`, `PASSWORD_POLICY`, `EXECUTIVE_EXISTS` |
| `set-password --email E` | a new credential row by `service:onboarding` | `PERSON_NOT_FOUND`, `PASSWORD_POLICY` |
| `disable --email E --reason R` / `enable --email E` | a new status row | `PERSON_NOT_FOUND`; `disable` of the last ACTIVE executive `LAST_EXECUTIVE` (R7) |

No other role is granted by the command: after onboarding, only the executive grants (OD-14; D-3C0A.7).

## 8. Guard

Register the account store in `tools/checks/configuration-persistence.ps1`, after the `$uploadWriter` block, in the
statement-shape style of the `$eventWriter` block: `$accountWriter =
"$backendRoot/accounts/adapters/postgres_account_store.py"` is the sole runtime writer of the six tables, and runs
only these shapes, each with an owner statement (anti-vacuity): one plain `INSERT INTO <table> (...) VALUES (...)`
per table (no `ON CONFLICT`, no `SELECT` source), `UPDATE operator_session SET revoked_at = :at WHERE
token_sha256 = :h AND revoked_at IS NULL`, and `DELETE FROM sign_in_attempt WHERE at < :before` (D-3C0A.11). The
advisory-lock `SELECT`s are reads, not write shapes. The registration touches the declaration, `$pgWriters`,
`$pgWritesSeen`, `$pgDriverSeen`, the rule block and the anti-vacuity loop, as the existing writers do (P14). Show the guard failing on a planted `UPDATE role_grant` and on a planted
`INSERT INTO role_grant` in a second module (RULES §7); record both in the packet.

## 9. Tests

No-database files (not pooled; run while building):
- `backend/tests/test_3c0a_passwords.py`: hash form (the CHECK regex); verify true, false; a tampered salt, hash or
  parameter fails; policy at 11, 12, 128, 129 characters and all-whitespace; `normalise_email` cases (trim, case key,
  no `@`, two `@`, 321 characters, a non-ASCII letter, a NUL, an inner space).
- `backend/tests/test_3c0a_accounts_service.py`: an in-memory `AccountStore` written in the test file; a settable
  clock. Sign-in success writes one succeeded attempt (with the person) and a session; wrong password, unknown email,
  disabled account and no credential each give `SIGN_IN_REFUSED` and one failed attempt with no person; a malformed
  email and a 129-character password give `SIGN_IN_REFUSED` (the malformed email writes no row); `verify_password`
  is called exactly once on every one of these paths (patched spy; `DUMMY_HASH` where no stored hash); the 6th
  attempt after 5 failures is `SIGN_IN_LOCKED` with the minutes of §3, writes no attempt, and sign-in works again once
  the window passes; 4 failures, a success, 1 failure: not locked; an unknown email locks after 5 like a known one;
  stored keys are hashes. `resolve` is `None` at 12 h after sign-in, after sign-out, for a disabled account, and after
  a later `onboard_set_password`; roles come from held grants at each call (grant then remove: the next `resolve`
  lacks the role). Each grant and removal refusal of §4.2 in its order; the executive removing their own role when
  another executive exists succeeds; a grant to a DISABLED account succeeds; `onboard_set_status` DISABLED on the
  last ACTIVE executive is `LAST_EXECUTIVE`; record newest first.
- `backend/tests/test_3c0a_accounts_api.py`: `TestClient(create_app(accounts=AccountService(<memory store>, ...)),
  base_url="https://testserver")` (http only for the `off` case; R12a) with `DATABASE_URL` unset (monkeypatch). The cookie attributes, with `ASSETOPS_SESSION_COOKIE_SECURE` unset, `on`
  and `off`; a bad value refuses `create_app`; identical 401 bodies for an unknown email and a wrong password; 415
  for a form body (sign-out included); 422 for an unknown key (including `actor`) and for a 5 KiB body; the refusal
  order of §5 (a form body with no session is 415); `Cache-Control: no-store` on all seven routes; a store raising
  `OperationalError` gives 503; each route's success shape; `create_app()`
  with neither accounts nor URL answers 503 on all seven routes.

Postgres files (pooled):
- `backend/tests/test_3c0a_accounts_postgres.py` (`store` and `engine` fixtures as `test_up1_reading_upload_postgres.py`):
  the six tables, their triggers and indexes exist; UPDATE and DELETE refused on the four append-only tables;
  UPDATE refused and the purge DELETE accepted on `sign_in_attempt`; `guarded_attempt` purges a 31-day-old row; on
  `operator_session` only setting `revoked_at` once is accepted; each CHECK fails on a planted row (role and Site,
  removal and `grant_id`, exactly one of `by_person_id` and `by_service`, `email_key`, `email_key_sha256`, success and
  person); the removal trigger refuses a
  mismatched removal; the partial unique index refuses a second removal; `email_key` unique across two tenants; the
  adapter's round trips for every port method. **Lock proofs** (R2): the test takes the tenant lock on its own
  connection, starts two threads, asserts after 0.5 s that both are still alive, commits, joins, and checks the
  result, for two removals of the last two executives (one `LAST_EXECUTIVE`, one executive held), two identical grants
  (one `ROLE_ALREADY_HELD`) and two `create_account` with an executive grant (one `EXECUTIVE_EXISTS`); the same shape
  with the per-email lock for two `guarded_attempt` calls (both blocked, then serialised). Downgrade refused with an
  account present; down then up again on an empty clone, and after the downgrade an 0005 trigger on an older table
  still refuses an UPDATE (R11).
- `backend/tests/test_3c0a_onboard_postgres.py`: the subprocess environment is built from scratch with
  `DATABASE_URL` set to the `engine` fixture's routed URL, after asserting its database name ends `_test` and is not
  `assetops_test` (R10); `create --executive` with the password on stdin, then `EXECUTIVE_EXISTS` for a second
  `--executive`; `disable` of the only executive is `LAST_EXECUTIVE`; `create` without it holds no role; `set-password` makes the next
  sign-in use the new password; `disable` refuses sign-in; `EMAIL_TAKEN` across tenants; `TENANT_NOT_FOUND`.
- Regression beside them: `backend/tests/test_pg_harness.py` and `backend/tests/test_up1_reading_upload_postgres.py`
  (the migration head and the 0061 downgrade still hold).

Commands:
```bash
cd /opt/assetecon/AssetOpsV1-3c0a
export PYTHONPATH=$PWD/backend:$PWD/backend/tests:$PWD/contracts:$PWD/simulator:$PWD/gateway:$PWD/field:$PWD/host:$PWD/tools
PY=/opt/assetecon/AssetOpsV1/.venv/bin/python
$PY -m pytest backend/tests/test_3c0a_passwords.py backend/tests/test_3c0a_accounts_service.py backend/tests/test_3c0a_accounts_api.py -q
ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_test \
  tools/heavy-slot.sh -- $PY -m pytest backend/tests/test_3c0a_accounts_postgres.py backend/tests/test_3c0a_onboard_postgres.py backend/tests/test_pg_harness.py backend/tests/test_up1_reading_upload_postgres.py -q
pwsh -NoProfile -File tools/check-all.ps1      # fast mode, once, at the end; it takes its own slot
python3 tools/select-tests.py --base main      # cite its output
```
`select-tests` selects the whole suite because a migration changes. Do not run it: the full backend tier runs at the
merge (`backend/TESTING.md`, "At every merge to main"; owner, 19 Nov: no expensive full run while building). Say so
in the packet.

## 10. Done (acceptance as questions)

1. Does a person sign in with email and password, receive an HttpOnly, SameSite=Strict session cookie, and does
   `GET /api/auth/me` name them, their tenant and their current roles?
2. Are an unknown email and a wrong password refused identically, and does the sixth attempt in 15 minutes lock?
3. Is a role granted or removed only by a person holding `OPERATOR_EXECUTIVE`, inside their own tenant, and is every
   grant and removal a row with its person and time, newest first in the record?
4. Can the tenant never be left without an executive, by removal or by disabling, even with two writes at once, and
   do the lock proofs show the writes waiting on the lock?
5. Are the four record tables append-only, the session table revoke-only and the attempt table insert-and-purge
   (hashed keys, no person on a failure, 30 days), enforced by the database?
6. Is no existing route, command or screen changed (`git diff --stat main...HEAD` shows only §0's files)?
7. Do the focused files, the regression pair and check-all pass, with the planted guard violations shown failing?

Packet: `specs/3C0a-operator-accounts/packet.md` (at most 3k tokens), with the mid-build question count.

## 11. Out of scope

The sign-in page and Organisation settings (`3C0b`); recording the person on commands and refusing commands without
one (`3C1`); Actions' creator and owner (`3C2`); thresholds in Organisation settings (`7b`); single sign-on (OD-13,
later); password reset by email; the demo people's accounts (`WK`, D-3C0A.8).

## 12. Sizing and commits

2.5 units (P14; `plan_model.py` re-run): up to six commits. Suggested: (1) migration and Postgres tests; (2) passwords, model, store port, adapter;
(3) service and its tests; (4) routes, words, composition and API tests; (5) onboarding command and its tests;
(6) guard registration and planted proofs.

## 13. Decision queue (W3)

| # | Question | Default applied |
|---|---|---|
| Q1 | Is 3C0a inside "non-screen work now"? | Yes (D-BW1.3); if the owner meant only data, engine and integrations, lane A takes `0K1` instead |
| Q2 | Email unique across tenants, so sign-in needs no tenant field (D-3C0A.3) | Yes |
| Q3 | 12-hour absolute sessions; lockout after 5 failures in 15 minutes | Yes; revisit at the pilot |
| Q4 | `Secure` cookie by default; `off` only for local http | Yes; `3C0b` checks the walkthrough's address and that cookies are shared across ports on one host (R12b) |
| Q5 | Accounts, credentials, statuses and grants are undeletable by design (D-3C0A.2); attempts are purged after 30 days | Accepted for the demo; erasure of a person's data is a pilot data-protection question |
