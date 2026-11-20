# ON1: an operator's tenant from one onboarding file (implementer spec)

Status: **rev 3** (re-scope, D-ON1.15, D-ON1.16), on rev 2's handshake answers (D-ON1.9 to D-ON1.14). The owner
chose option A (`owner/owner-on1-roles-executive-approves-2026-11-20.md`: "A, executive approves roles at first
sign-in"), then allowed it to wait (`owner/owner-on1-approval-can-wait-2026-11-20.md`: "the approval step can wait if
autoamtic approval for the demo saves us time"). Rev 3: **an emulated file's roles are granted automatically** at
onboarding (`service:onboarding`); **a real file is refused** before any write until the queued unit `ON1b` builds
option A (D-ON1.9, unchanged as the rule for real data). OD-14 is unchanged for real operators; rev 3 departs from it
on emulated tenants only (D-ON1.15). Saving: 0.5 unit now (2.5 to 2.0), no migration, no change to sign-in, and the
executive never signs in this fortnight (RC7 holds whole). Questions: `handshake.md` before code,
`mid-build-questions.md` during it. Reviewer: `reviewer-guide.md` (rev 3). Decisions with reasons: `rulings.md`
(D-ON1.1 to D-ON1.16). The runbook's text: `runbook.md` (rev 3, this folder), copied verbatim by the build.

Architect (Claude), 2026-11-20. Lane A, the deep-dive path's unit 6 (`two-week-build-plan.md` §0.1 row 6; D-BW1.11;
owner RC1 to RC9 accepted, `owner/owner-recut-decisions-rc1-rc9-2026-11-20.md`: RC4 real data only in its own
database, created by the coordinator after a signed DPA, deleted at the agreed retention; RC5 mini-grid only; RC7 the
owner presents).
- **Builds on (merged, `main` 6db81330a, plus `RC4-F1` and `3A3`, which merge first):** `RC4-F1`
  (`database_target`, `PG_TARGET_ENV`); `3C0a` (`accounts/service.py`
  `AccountService.onboard_create`, `grant`; `accounts/store.py` `AccountStore`; `accounts/onboard.py` `_parser`,
  `main`; `model.ROLES`, `ONBOARDING`, `GrantRow`); `3A3` (`AccountService.onboard_person`, `OnboardPerson`); the Site
  import (`sites/foundation_service.py` `import_site`, `ImportSource`, `ImportConflict`; `sites/site_parsing.py`
  `parse_site_document`; `sites/foundation_records.py` `FoundationStore`, `TenantNotFound`, `TenantRef`;
  `sites/adapters/postgres_foundation_store.py` `ensure_tenant`, `resolve_tenant`, `find_site`; `sites/composition.py`
  `build_foundation_store`); `3A2` (`commercial/composition.py` `commercial_upload_settings`, `create_key_file`,
  `FileKeyStore`, `KeyExists`, `KeyDirectoryMissing`; `commercial/adapters/file_key_store.py`;
  `commercial/pseudonym_key.py` `main`; `commercial/uploads.py` step 7); `config.DEVELOPMENT_TENANT_SLUG`;
  `main.create_app` (`FoundationService(foundation_store, DEVELOPMENT_TENANT_SLUG, ...)`).

Non-screen. **2.0 units, three commits**: the plan's 1.5, the served
tenant and the erasure tombstone (D-ON1.5, D-ON1.7), the automatic grants for emulated files and the refusal of real
ones (D-ON1.15), the digest and separation (D-ON1.10), the demo pin (D-ON1.11). Owner decisions: OD-14 (the executive
grants roles; kept for real data by refusing it until `ON1b`), RC2, RC4, RC5, RC7, D-ON1.9's answer and its deferral.
Discovery review (W5): the real-data boundary (RC4), people and roles (OD-14 on real data, D-ON1.15 on emulated),
key erasure.

## 0. Before you start

- **Branch** `task/ON1-operator-tenant` off `main` after `RC4-F1` and `3A3` merge (it edits `commercial/uploads.py`,
  `pseudonym.py`, `file_key_store.py` and `messages.py` after 3A3 does); worktree `/opt/assetecon/AssetOpsV1-on1`.
  Code starts when the handshake has no open question.
- **Python:** as 3A3 §0.
- **Read:** this spec, `rulings.md`, `runbook.md`; 3C0a `spec.md` §3 ("Grant", "Who did it"), §4.1, §7 and
  `rulings.md` D-3C0A.7; 3A2 `spec.md` §3.4 ("Key store", "Key command") and §4 "Settings"; `sites/foundation_service.py`
  `plan_import` and `import_site`; `sites/site_parsing.py` `SITE_KEYS` to `COMPONENT_KEYS`; `main.py` `create_app` to
  the `FoundationService(...)` call; `backend/tests/foundation_fakes.py` `InMemoryFoundationStore`;
  `backend/tests/test_3c0a_accounts_service.py` `MemoryStore`.
- **Databases.** Postgres tests run only on the harness's routed `*_test` databases (`tools/heavy-slot.sh --db`). **No
  test creates, names in a connection, or touches a database whose name starts with `assetops_op`** (D-ON1.6,
  D-ON1.12): the RC4 checks run on in-memory ports with names placed in `DATABASE_URL`, host `rc4.invalid` port 1,
  and the no-connect fixture of §6, so even a planted violation cannot reach a database. The runbook's
  database steps are for the coordinator; no agent runs them. Never ports 5490 or 8990, the
  walkthrough DB or Docker.
- **No migration** (rev 3; `ON1b` brings the proposal tables).

## 1. Outcome and why

A person in the Analyst role fills one onboarding file with the operator: the operator, its mini-grid Sites (code,
name, time zone, location, lifecycle, installed components) and its people with their roles. One command checks it
against the database and the switches and prints what it would create; the same command applies it: the tenant, its
Sites through the existing Site import, the people's accounts, the executive's role, the other roles, and the
tenant's pseudonym key. Re-running creates nothing more. For an **emulated** file (rehearsal and demo tenants, never
an operator database) the other roles are granted automatically by `service:onboarding` (D-ON1.15). A **real** file
passes the real-data checks and is then refused before any write, until `ON1b` lets the operator's executive approve
the roles at sign-in (OD-14; D-ON1.9). On an operator database (`assetops_op_<name>`) only a `real` file is admitted,
and only with the real-data switch on and the server set to serve that tenant (RC4). The server serves the tenant named by
`ASSETOPS_TENANT_SLUG`, so 3A2's Site path works for the operator's Sites. A key erased at the end of retention can
never be recreated, so a re-sent file is refused in plain words instead of conflicting (3A2 residual). A runbook takes
a person through the rehearsal to the first accepted export and to erasure, and names the real-operator steps that
wait for `ON1b`.

Why now: `DDR` rehearses on an onboarded tenant; the first real deep-dive needs one.

## 2. The onboarding file (`assetops.operator-onboarding/1`)

UTF-8 JSON, at most 262144 bytes, an object with exactly these keys (strict at every level: an unknown or missing key
is refused; duplicate keys are refused):

```json
{
  "format": "assetops.operator-onboarding/1",
  "data": "emulated",
  "operator": {"slug": "lakeside-power", "name": "Lakeside Power", "vertical": "MINI_GRID"},
  "sites": [
    {"code": "KOBO-001", "name": "Kobo mini-grid", "timezone": "Africa/Nairobi", "country": "Kenya",
     "locality": "Kobo", "lifecycle": "ACTIVE", "valid_from": "2026-07-01T00:00:00Z",
     "components": [{"id": "pv-array", "type": "PV_ARRAY", "name": "PV array", "rating": {"value": 60.0, "unit": "kW"}}]}
  ],
  "people": [
    {"email": "amina@lakeside.example", "name": "Amina", "roles": [{"role": "OPERATOR_EXECUTIVE"}]},
    {"email": "peter@lakeside.example", "name": "Peter", "roles": [{"role": "SITE_MANAGER", "site": "KOBO-001"}]}
  ]
}
```

Rules, each refusal `OnboardRefused(code, where)` (`where` a JSON path such as `sites[2].code`, never a value; no
other field):
- `format` exactly as above (`ONBOARD_FORMAT`); JSON that does not parse, is not an object, or is over size
  (`ONBOARD_FILE`).
- `data` is `emulated` or `real` (`ONBOARD_DATA`).
- `operator.slug` fullmatches `[a-z0-9][a-z0-9-]{0,62}` and is not `demo` (`ONBOARD_SLUG`); `name` 1 to 120 characters
  after `strip()`, equal to its stripped form (`ONBOARD_NAME`); `vertical` exactly `MINI_GRID` (`ONBOARD_VERTICAL`,
  RC5).
- `sites`: 1 to 50 entries; `code` fullmatches `[A-Z0-9][A-Z0-9-]{0,63}` (2a's site code) and is unique
  case-insensitively (`ONBOARD_SITE_CODE`); the other site fields are passed to the Site document (§3.2) and judged by
  `parse_site_document` (`ONBOARD_SITE_INVALID`, `where` = `sites[i]`; the parser's message is neither printed nor
  kept, since it may quote a value).
- `people` (granted automatically when `emulated`; a `real` file is refused at `check` step 3a, D-ON1.15): 1 to 50 entries; `email` normalised by 3C0a's `passwords.normalise_email` (`ONBOARD_EMAIL`), unique by
  key (`ONBOARD_EMAIL_DUPLICATE`); `name` 1 to 120 after strip (`ONBOARD_NAME`); `roles` 1 to 5 entries, each
  `{"role"}` or `{"role", "site"}`: role in `model.ROLES` (`ONBOARD_ROLE`); `site` present exactly for
  `SITE_MANAGER` and naming a file Site (`ONBOARD_ROLE_SITE`); no duplicate (role, site) for a person
  (`ONBOARD_ROLE_DUPLICATE`).
- Exactly one person holds `OPERATOR_EXECUTIVE` (`ONBOARD_EXECUTIVE_COUNT`); at least one holds
  `FINANCE_AND_COMMERCIAL_LEAD` and at least one `ANALYST` (`ONBOARD_ROLES_MISSING`): without them no export can be
  submitted or accepted. No person holds `ANALYST` together with `FINANCE_AND_COMMERCIAL_LEAD` or
  `OPERATOR_EXECUTIVE` (`ONBOARD_ROLES_SEPARATE people[i]`; D-ON1.10: the submitter never accepts).
- **Roles digest** (D-ON1.10): `roles_digest(f) = sha256(json.dumps({"operator": slug, "people": [[email_key, name,
  sorted([role, site or ""] ...)] ... sorted by email_key]}, sort_keys=True, separators=(",", ":"),
  ensure_ascii=False).encode("utf-8")).hexdigest()`. `apply` takes it as `--confirmed-digest` (runbook step 4); under `ON1b` the executive confirms it in writing.
- Not collected (D-ON1.8): passwords, currency, tariff, loss band.

## 3. Rules

### 3.1 Check, then apply (D-ON1.1)

`OperatorOnboarding(foundation: FoundationStore, accounts: AccountService, keys: KeyFiles, *, clock, real_data: bool,
served_slug: str)` in `backend/assetops_backend/onboarding/service.py`, with `check(f: OperatorFile) -> Plan` and
`apply(f, *, confirmed_digest: str) -> Plan` (the plan as executed). `KeyFiles` is a port: `directory_ok() -> bool`,
`state(tenant_id) -> "MISSING" | "PRESENT" | "ERASED"`, `create(tenant_id) -> None`. (No `database_name`: the
command's `commercial_upload_settings`, through RC4-F1, is the one decider; R14.)

`check`, in this order (first refusal wins; codes in §5):
0. `keys.directory_ok()`: the key directory exists, is a directory and has `mode & 0o077 == 0`
   (`ONBOARD_KEY_DIR`).
1. **RC4** (D-ON1.6): `f.data == "real"` needs `real_data`; `"emulated"` needs not `real_data`
   (`ONBOARD_DATA_MISMATCH`). (`commercial_upload_settings` has already refused an unclear URL and a switch that
   disagrees with the database; the command calls it first.)
2. `served_slug == f.slug` (`ONBOARD_TENANT_NOT_SERVED`).
3. When real: `foundation.tenant_slugs()` is empty or exactly `(f.slug,)` (`ONBOARD_DATABASE_NOT_EMPTY`: one
   operator per operator database).
3a. When real: `ONBOARD_REAL_AWAITS_APPROVAL` (D-ON1.15). Placed after steps 1 to 3 so the RC4 refusals are still
   reached and tested; `ON1b` replaces this step with proposals.
4. Tenant: `resolve_tenant(f.slug)`; absent is `create`; present with another name is `ONBOARD_TENANT_DIFFERS`; else
   `keep`. Key: absent tenant is `create`; else `keys.state(id)`: `ERASED` is `ONBOARD_KEY_ERASED`; `PRESENT` is
   `keep`; `MISSING` is `create`.
5. Sites, each: the Site document and its `ImportSource` (§3.2). Tenant present and `find_site(id, code)` found: its
   `import_record.source_path` must equal the source's path and `source_sha256` its sha256
   (`ONBOARD_SITE_CHANGED sites[i]`), then `keep`; otherwise `create`.
6. People, each, `accounts.onboard_person(email)`: `None` is `create`; another tenant's is `ONBOARD_EMAIL_TAKEN
   people[i]`; this tenant's with another display name, or not active, is `ONBOARD_PERSON_DIFFERS people[i]`; else
   `keep`. Executive (R10): `current = accounts.executive_of(f.slug)` (the person holding `OPERATOR_EXECUTIVE` now,
   or `None`; `None` too when the tenant is absent). When `current` is not `None`, the file's executive must be that
   person (`keep` with that `person_id`), else `ONBOARD_EXECUTIVE_DIFFERS people[i]`.
7. Roles, each non-executive (person, role, site): held now (`onboard_person.roles`, the Site ID resolved through
   `find_site`) is `keep`, else `grant`. Any `grant` while `accounts.onboarding_open(f.slug)` is false is
   `ONBOARDING_CLOSED people[i]` (D-ON1.15: once a person has granted a role, only people grant).

`apply` checks `confirmed_digest == roles_digest(f)` first (`ONBOARD_DIGEST_DIFFERS`, exit 2), runs `check`, then in
this order, each step only for `create`/`grant` entries: `ensure_tenant(f.slug, f.operator.name, now=clock())`;
`import_site(foundation, tenant_slug=f.slug, configured_tenant_slug=f.slug, source=..., legacy_documents=(),
clock=clock)` per Site (an `ImportConflict` is `ONBOARD_SITE_CHANGED`); `accounts.onboard_create(f.slug, email,
name, secrets.token_urlsafe(32), executive=<holds OPERATOR_EXECUTIVE>)` per person (the password is never stored or
shown, D-ON1.4); `accounts.onboard_grant(f.slug, email, role, site)` per `grant` entry; `keys.create(tenant_id)`. A refusal mid-way stops; the steps done stay, and a rerun's `check` marks them `keep`.

`Plan` (printed as one JSON object): `{"tenant": {"slug", "id" (null until it exists), "action"}, "sites":
[{"code", "action"}], "people": [{"index", "action", "roles": [...]}], "roles": [{"index", "role", "site",
"action"}], "key": "create" | "keep", "roles_digest": "<hex>"}`; a role's `action` is `grant` or `keep`. No email,
name or password is printed.

### 3.2 The Site document (D-ON1.2)

`site_document(site) -> dict`: `{"site_id": code, "display_name": name, "site_type": "MINIGRID", "location":
{"country", "locality"}, "timezone", "lifecycle_status": lifecycle, "origin": "USER", "source": {"mode": "LIVE" if
real else "SIMULATED"}, "foundation": {"version": 1, "valid_from", "summary": "Onboarded from the operator's onboarding
file.", "components": [{"component_id": id, "component_type": type, "display_name": name, "rating": rating}]}}`.
`ImportSource(path=f"onboarding:{slug}/{code}", sha256=sha256(json.dumps(document, sort_keys=True,
separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest(), record=parse_site_document(document,
source=path), document_format="ASSETOPS_ONBOARDING_JSON")`. A Site's sha256 depends on its own entry only, so adding a
Site later does not change the others.

### 3.3 People and their roles (D-ON1.15, D-ON1.4; 3C0a code)

- **No migration.** The grants are ordinary `role_grant` rows (0062): `by_service = 'service:onboarding'`,
  `by_person_id` NULL, as the executive's own onboarding grant already is.
- `AccountService.onboard_grant(tenant_slug, email, role, site_code) -> GrantRow`, by `ONBOARDING`. Refusals in order:
  `TENANT_NOT_FOUND` 404; `PERSON_NOT_FOUND` 404 (another tenant's too, through `_onboard_account`); `ROLE_UNKNOWN`
  422; `ONBOARD_EXECUTIVE_GRANT` 422 (the executive is granted only by `onboard_create(..., executive=True)`);
  `ROLE_SITE_RULE` 422; `SITE_NOT_FOUND` 404; then the store's `ONBOARDING_CLOSED` 409, `ROLES_SEPARATE` 409 and
  `ROLE_ALREADY_HELD` 409. The row: `GrantRow(row_id, row_id, tenant_id, person_id, display_name, role, site_id,
  site_code, "GRANTED", None, None, ONBOARDING, clock())`.
- Store `add_onboarding_grant(row) -> GrantRow`: one transaction under the tenant's role lock (`_lock_tenant`), in
  this order: `ONBOARDING_CLOSED` when `SELECT 1 FROM role_grant WHERE tenant_id = :t AND by_person_id IS NOT NULL
  LIMIT 1` finds a row; `ROLES_SEPARATE` when the role is `ANALYST` and the person holds `FINANCE_AND_COMMERCIAL_LEAD`
  or `OPERATOR_EXECUTIVE`, or the role is `FINANCE_AND_COMMERCIAL_LEAD` and the person holds `ANALYST` (held by
  `held_grants`' rule; the file rule `ONBOARD_ROLES_SEPARATE` already refuses this, the store is the backstop for the
  class); `ROLE_ALREADY_HELD` by the existing `_HELD_SAME` read; then the existing `_INSERT_GRANT`. Returns
  `grant_row(...)` as `add_grant` does. The in-memory store (`MemoryStore` in the 3C0a tests) mirrors it in the same
  order.
- `AccountService.onboarding_open(tenant_slug) -> bool` (store `person_grant_exists(tenant_id) -> bool`, the same
  read outside a lock; an absent tenant is open); `AccountService.executive_of(tenant_slug) -> UUID | None` (store
  `executive_of(tenant_id)`: the person of a held `OPERATOR_EXECUTIVE` grant, by the rule `held_grants` uses; an
  absent tenant is `None`).
- **Sign-in is not changed** (rev 2's `approve_roles` moves to `ON1b`). The executive's grant API (3C0a) is not
  changed: a grant by a person closes onboarding, as before.
- The command never sets a password. Each person's password is set afterwards with `python -m
  assetops_backend.accounts.onboard set-password --email ...` (3C0a §7), typed on stdin.

### 3.4 The served tenant (D-ON1.5)

- `config.served_tenant_slug() -> str`: `ASSETOPS_TENANT_SLUG` unset is `DEVELOPMENT_TENANT_SLUG`; set, it must
  fullmatch `[a-z0-9][a-z0-9-]{0,62}` (empty included in the refusal), else `ConfigurationError("ASSETOPS_TENANT_SLUG
  must be a tenant slug.")`.
- `create_app`: right after `commercial_upload_settings`, `served = served_tenant_slug()`; when
  `upload_settings.real_data` and `served == DEVELOPMENT_TENANT_SLUG`, `ConfigurationError("An operator database
  serves its operator's tenant: set ASSETOPS_TENANT_SLUG to it.")`. The `FoundationService(...)` call takes `served`
  instead of `DEVELOPMENT_TENANT_SLUG`. Nothing else in `create_app` changes.
- Public accessors (R11): `FoundationService.tenant_slug` (property) and `ImportedSiteRegistry.served_tenant_slug`
  (property; `None` with no service); `create_app` sets `app.state.site_registry = registry`.
- **The demo serves `demo`** (D-ON1.11): `tools/demo_combined.py` `Demo.env()` sets `out["ASSETOPS_TENANT_SLUG"] =
  "demo"` and pops `ASSETOPS_REAL_OPERATOR_DATA` and `ASSETOPS_PSEUDONYM_KEY_DIR`, after RC4-F1's `PG*` removal.
- The other uses of `DEVELOPMENT_TENANT_SLUG` (command-line tools and backfills that refuse any other tenant) are not
  changed: none is on the deep-dive path. `3B7a`'s rebuild command takes `served_tenant_slug()` (carried to its spec).

### 3.5 Erasure is terminal (D-ON1.7, D-ON1.14; 3A2 code)

- `commercial/adapters/file_key_store.py`: a tombstone `<dir>/<tenant_id>.erased`. One `_tombstoned(directory,
  tenant_id) -> bool`: `os.lstat(path)`; `FileNotFoundError` is `False`; any other outcome (a file, a symlink, a
  dangling symlink, `PermissionError` or any `OSError`) is `True`. Used by all four below.
- `FileKeyStore.key`: `_tombstoned` first; `True` raises `PseudonymKeyErased` (new, `pseudonym.py`).
- `create_key_file`: after the directory check, `_tombstoned` refuses with `KeyErased` (new).
- New `key_state(directory, tenant_id) -> str`: `ERASED` if `_tombstoned`, else `PRESENT` if the key exists
  (`os.path.lexists`), else `MISSING`; no key bytes read.
- New `erase_key_file(directory, tenant_id) -> str`: a missing directory is `KeyDirectoryMissing`. `had_tomb =
  _tombstoned(...)`; if not, write it (`O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW`, 0600, `b"erased\n"`, `os.fsync`);
  then, whatever the tombstone's state, unlink the key if `os.path.lexists`; `os.fsync` the directory. Returns
  `ALREADY_ERASED` when `had_tomb` and no key was unlinked, else `ERASED` (also when neither file existed: the
  tombstone now forbids a new key). No `KeyMissing`.
- New `directory_ok(directory) -> bool`: `os.stat` succeeds, `S_ISDIR`, and `mode & 0o077 == 0`.
- `commercial/composition.py` re-exports `key_state`, `erase_key_file`, `KeyErased`, and builds
  `FileKeyFiles(directory)` (the `KeyFiles` port: `directory_ok`, `state`, `create`).
- `pseudonym_key.py`: a public `build_parser()`; new sub-command `erase --dir --tenant-id`: stdout `Erased.` or
  `Already erased.`, exit 0; `KeyDirectoryMissing` as `create`. `create` on a tombstone: exit 2 "This tenant's key
  was erased. A new key would not match the records already held; onboard the operator as a new tenant."
- `CommercialUploads._check` step 7: `PseudonymKeyErased` is 409 `PSEUDONYM_KEY_ERASED`, words
  `commercial_upload.key_erased`: "This organisation's customer identities were erased, so its exports are no longer
  received."

## 4. Code

| File | Holds |
|---|---|
| `backend/assetops_backend/onboarding/__init__.py`, `operator_file.py` | `FORMAT`, `OperatorFile`, `SiteEntry`, `PersonEntry`, `parse_operator_file(data: bytes) -> OperatorFile`, `OnboardRefused(code, where)`, `roles_digest`, `site_document`, `site_source` (§2, §3.2). No I/O |
| `backend/assetops_backend/onboarding/service.py` | `KeyFiles` (Protocol), `Plan`, `OperatorOnboarding` (§3.1) |
| `backend/assetops_backend/onboard_operator.py` | the command (§5), `build_parser()`, `main(argv, *, onboarding=None)` |
| `backend/assetops_backend/sites/foundation_records.py`, `adapters/postgres_foundation_store.py` | `FoundationStore.tenant_slugs() -> tuple[str, ...]` (`SELECT slug FROM tenant ORDER BY slug`) |
| `backend/assetops_backend/sites/foundation_service.py`, `sites/cutover.py` | `tenant_slug` and `served_tenant_slug` properties (§3.4) |
| `backend/assetops_backend/accounts/service.py`, `store.py`, `adapters/postgres_account_store.py` | `onboard_grant`, `onboarding_open`, `executive_of`; store `add_onboarding_grant`, `person_grant_exists`, `executive_of` (§3.3). `model.py` and `accounts_api.py` unchanged |
| `backend/assetops_backend/accounts/onboard.py` | `_parser` renamed `build_parser` (public); behaviour unchanged |
| `backend/assetops_backend/config.py`, `main.py` | §3.4 |
| `backend/assetops_backend/commercial/pseudonym.py`, `adapters/file_key_store.py`, `composition.py`, `pseudonym_key.py`, `uploads.py` | §3.5 |
| `backend/assetops_backend/i18n/messages.py` | `commercial_upload.key_erased` (a `# ON1` block) |
| `tools/demo_combined.py` | `Demo.env()` pins the demo tenant (§3.4) |
| `tools/world_history.py` | a public `build_parser()` (the runbook test parses its line); behaviour unchanged |
| `Docs/engineering/operator-deep-dive-runbook.md` | `runbook.md` of this folder, verbatim from its first `#` heading |
| `backend/tests/fixtures/on1/lakeside-power.onboarding.json` | the Lakeside rehearsal tenant (§6) |
| `backend/tests/test_3c0a_accounts_service.py` | `MemoryStore` gains the §3.3 store methods; no expected value moves |

## 5. The command (`python -m assetops_backend.onboard_operator`)

`digest --file FILE` reads and parses the file only (no database, no settings) and prints `roles_digest(f)`, exit 0
(a parse refusal exits 2). `check --file FILE` and `apply --file FILE --confirmed-digest HEX`, both with `--key-dir
DIR` (default `ASSETOPS_PSEUDONYM_KEY_DIR`; neither is `ONBOARD_KEY_DIR_REQUIRED`). Steps: `DATABASE_URL` unset is `DATABASE_URL_REQUIRED`; `commercial_upload_settings(url)`
(`ConfigurationError` is `CONFIGURATION <message>`); `served_tenant_slug()` (same); the file read with
`Path(file).read_bytes()` (a top-level command, as `publish_assumption.py`); `parse_operator_file`; build the service
from `build_foundation_store(url)`, `build_account_service(url)`, `FileKeyFiles(key_dir)`, the UTC clock,
`settings.real_data`, `served`; `check` or `apply`. Success prints the plan on stdout and exits
0. A refusal prints `<CODE> <where> <sentence>` on stderr and exits 2 (`check`, or `apply` before its first write) or
3 (`apply` after a write). Every message through `sys.stdout.write` / `sys.stderr.write`.

| Code | Sentence |
|---|---|
| `ONBOARD_FILE` | The onboarding file cannot be read as JSON. |
| `ONBOARD_FORMAT` | This is not an onboarding file of version 1. |
| `ONBOARD_DATA` | "data" must be "emulated" or "real". |
| `ONBOARD_SLUG` | The operator code must be lower-case letters, digits and hyphens, and not "demo". |
| `ONBOARD_NAME` | A name must be 1 to 120 characters with no surrounding spaces. |
| `ONBOARD_VERTICAL` | Only mini-grid operators are onboarded for now. |
| `ONBOARD_SITE_CODE` | A Site code must be upper-case letters, digits and hyphens, and unique. |
| `ONBOARD_SITE_INVALID` | This Site cannot be created as written. |
| `ONBOARD_EMAIL` / `ONBOARD_EMAIL_DUPLICATE` | This email cannot be used. / This email appears twice. |
| `ONBOARD_ROLE` / `ONBOARD_ROLE_SITE` / `ONBOARD_ROLE_DUPLICATE` | This role is not known. / Only a Site manager names a Site, and it must be one of the file's Sites. / This role appears twice for this person. |
| `ONBOARD_EXECUTIVE_COUNT` | Exactly one person must be the operator executive. |
| `ONBOARD_ROLES_MISSING` | At least one finance lead and one analyst are needed to receive exports. |
| `ONBOARD_DATA_MISMATCH` | Real data is onboarded only into an operator database with real data switched on, and emulated data never. |
| `ONBOARD_TENANT_NOT_SERVED` | Set ASSETOPS_TENANT_SLUG to this operator before onboarding it. |
| `ONBOARD_DATABASE_NOT_EMPTY` | An operator database holds one operator only. |
| `ONBOARD_TENANT_DIFFERS` | This operator already exists with another name. |
| `ONBOARD_KEY_ERASED` | This operator's identities were erased; onboard it again as a new operator. |
| `ONBOARD_SITE_CHANGED` | This Site already exists with other details; it is not changed here. |
| `ONBOARD_EMAIL_TAKEN` | This email belongs to another organisation. |
| `ONBOARD_PERSON_DIFFERS` | This person already exists with another name, or is disabled. |
| `ONBOARD_EXECUTIVE_DIFFERS` | This person is in the file as the executive but does not hold that role. |
| `ONBOARD_REAL_AWAITS_APPROVAL` | A real operator is onboarded once its executive can approve the roles; that step is not built yet. |
| `ONBOARDING_CLOSED` | The executive now grants roles; ask them to grant this one. |
| `ONBOARD_KEY_DIR_REQUIRED` | Name the key directory (--key-dir or ASSETOPS_PSEUDONYM_KEY_DIR). |
| `ONBOARD_KEY_DIR` | The key directory must exist and be readable by its owner only. |
| `ONBOARD_ROLES_SEPARATE` | The person who submits exports cannot also be the finance lead or the executive. |
| `ONBOARD_DIGEST_DIFFERS` | This file is not the one the executive confirmed: its roles digest differs. |
| `DATABASE_URL_REQUIRED`, `CONFIGURATION` | as 3C0a's command and the settings message |

An `AccountRefused` (`ROLES_SEPARATE`, `ROLE_ALREADY_HELD` and the others of §3.3 are backstops) or
`KeyDirectoryMissing` in `apply` prints its code and exits 3.

## 6. Tests

**Fixture** `lakeside-power.onboarding.json`: `data` `emulated`; operator `lakeside-power`, "Lakeside Power",
`MINI_GRID`; Sites `KISIWA-001` (Kisiwa mini-grid), `KOBO-001` (Kobo mini-grid), `MTO-001` (Mto mini-grid), each
`Africa/Nairobi`, Kenya, its locality, `ACTIVE`, `2026-07-01T00:00:00Z`, components from the manifest's `physical`
(Kobo: PV_ARRAY 60 kW, INVERTER 50 kW, BATTERY 200 kWh, GENERATOR 40 kW; Kisiwa: PV_ARRAY 30 kW, BATTERY 80 kWh,
GENERATOR 60 kW `gen-ks-01`, GENERATOR 60 kW `gen-ks-02`; Mto: PV_ARRAY 50 kW, INVERTER 25 kW `inv-mt-01`, INVERTER
25 kW `inv-mt-02`, BATTERY 150 kWh, GENERATOR 30 kW); people Amina (executive), Joseph (finance lead), Wanjiru
(analyst), Peter (Site manager KOBO-001), Halima (KISIWA-001), David (MTO-001), Musa (field technician), emails
`<name lower>@lakeside-power.example`. (The manifest's `demo_workflow` people; `DDR` uses this file.) The test
computes its digest once and pins it as a literal.

**No-connect rule (D-ON1.12).** In the service, keys and settings files an autouse fixture makes `psycopg.connect`,
`psycopg.Connection.connect` and `sqlalchemy.engine.Engine.connect` raise `AssertionError("connection attempted")`;
each file has one test proving it (`create_engine("postgresql+psycopg://u:p@rc4.invalid:1/x").connect()` raises
that). Every URL naming a database in them uses host `rc4.invalid` port 1.

**File, no database** (`backend/tests/test_on1_operator_file.py`): the fixture parses; one planted refusal per row
of §2 (each code once, `where` asserted, including `ONBOARD_ROLES_SEPARATE` for Wanjiru given
`FINANCE_AND_COMMERCIAL_LEAD`, and `ONBOARD_SITE_INVALID` printing no value); an unknown key at each level; a
duplicate JSON key; 262145 bytes; `roles_digest` equals the pinned literal, changes when a role, a Site of a role,
a name or an email changes, and does not change when a Site's components change.

**Service, no database** (`backend/tests/test_on1_onboarding_service.py`), world: `InMemoryFoundationStore` (it
gains `tenant_slugs`, the one edit to `foundation_fakes.py`) and a `MemoryStore` subclass whose `tenant_by_slug`,
`tenant_slug` and `site_id` read the foundation fake; an in-memory `KeyFiles`; clock `2026-11-20T09:00:00+00:00`:
1. `check` on an empty world: tenant, 3 Sites, 7 people, the key `create`, 6 roles `grant`; the plan's
   `roles_digest` is the pinned literal.
2. `apply`: tenant `lakeside-power` named "Lakeside Power"; 3 imported Sites whose `site_import.source_path` is
   `onboarding:lakeside-power/<code>`; 7 accounts; **7 grants**, every one `by_service` `service:onboarding` and
   `by_person_id` NULL (Amina's executive grant and 6 others); the key created; the plan printed holds no `@`.
3. **Real data waits for `ON1b`** (D-ON1.15): the fixture with `data` `real`, `real_data=True`, `served_slug`
   `lakeside-power`, an empty world: `check` and `apply` are `ONBOARD_REAL_AWAITS_APPROVAL` and the fakes count no
   write (no tenant, Site, account, grant or key). After test 2, `roles_of` gives Wanjiru `ANALYST` and Joseph
   `FINANCE_AND_COMMERCIAL_LEAD`, and no person holds both a submitting and an accepting role.
4. A second `apply` after test 2: every entry `keep`; no write (the fakes count writes).
5. Partial run: the account store raises on the fourth `onboard_create`; the rerun completes and the end state equals
   test 2's.
6. Changes refused: a Site's `name` changed (`ONBOARD_SITE_CHANGED sites[1]`); the operator name changed
   (`ONBOARD_TENANT_DIFFERS`); Joseph's name changed (`ONBOARD_PERSON_DIFFERS people[1]`); an email of tenant `acme`
   (`ONBOARD_EMAIL_TAKEN`); a file naming another person as executive on the applied tenant
   (`ONBOARD_EXECUTIVE_DIFFERS` at `check`, no write); `apply` with a digest one character off
   (`ONBOARD_DIGEST_DIFFERS`, no write).
7. Onboarding closes (D-ON1.15): after test 2, Amina grants Musa `ANALYST` through `AccountService.grant` (a
   person-made grant); a file adding a role for Peter is `ONBOARDING_CLOSED people[3]` at `check`, no write; the
   unchanged file still applies (`keep`).
8. RC4 matrix (no connection; names only): `data` `real` with `real_data=False` and `emulated` with `real_data=True`
   are `ONBOARD_DATA_MISMATCH`; `served_slug` `demo` is `ONBOARD_TENANT_NOT_SERVED`; real with another tenant present
   is `ONBOARD_DATABASE_NOT_EMPTY`; real with all three right is `ONBOARD_REAL_AWAITS_APPROVAL` (test 3); through the
   command's `main` with injected nothing: `DATABASE_URL`
   `.../assetops_test?dbname=assetops_op_x` and `.../` (no name) each exit 2 `CONFIGURATION` (RC4-F1), with the
   no-connect fixture never tripped.
9. Key: `KeyFiles.state` `ERASED` is `ONBOARD_KEY_ERASED`, and `directory_ok()` false is `ONBOARD_KEY_DIR`, each
   before any write.
10. `onboard_grant` refusals, called directly after test 2: `ONBOARD_EXECUTIVE_GRANT` (Joseph as executive),
    `ROLE_SITE_RULE`, `SITE_NOT_FOUND`, `PERSON_NOT_FOUND` for another tenant's email, `ROLE_ALREADY_HELD` (Joseph's
    finance role again), `ROLES_SEPARATE` (Wanjiru given `FINANCE_AND_COMMERCIAL_LEAD`; Joseph given `ANALYST`).

**Keys, no database** (`backend/tests/test_on1_key_erasure.py`, `tmp_path`):
1. `erase` writes the tombstone (mode 0600) and removes the key: `Erased.`; a second `erase` prints `Already
   erased.`; `create` then exits 2 with the sentence and writes nothing. Crash case: tombstone present and key present,
   `erase` unlinks the key, `Erased.`. Lost key: neither file, `erase` writes the tombstone, `Erased.`, and `create`
   then refuses.
2. `FileKeyStore.key` raises `PseudonymKeyErased` with a tombstone, also when a key file is still present, when the
   tombstone is a symlink, a dangling symlink, or a file of mode 000 (the test skips the mode case when run as root).
3. 3A2 path: an upload `check` with an erased key is 409 `PSEUDONYM_KEY_ERASED` with its words; with the key missing
   it is still 409 `PSEUDONYM_KEY_MISSING`.
4. `key_state` gives MISSING, PRESENT, ERASED, and ERASED for the dangling-symlink and mode-000 tombstones;
   `directory_ok` is false for a missing path, a file, and a directory of mode 0750.

**Settings, demo and runbook, no database** (`backend/tests/test_on1_served_tenant.py`):
1. `served_tenant_slug()`: unset `demo`; `lakeside-power`; `""`, `Lakeside`, `a b` refused.
2. `create_app()` with `ASSETOPS_REAL_OPERATOR_DATA=on`, `DATABASE_URL`
   `postgresql+psycopg://u:p@rc4.invalid:1/assetops_op_pilot1` and `ASSETOPS_TENANT_SLUG` unset raises
   `ConfigurationError`. Second half: switch off, **no** `DATABASE_URL`, `ASSETOPS_TENANT_SLUG=lakeside-power`,
   `foundation_store=InMemoryFoundationStore()`: `app.state.site_registry.served_tenant_slug == "lakeside-power"`.
3. Runbook (D-ON1.13): fenced `sh` blocks of `Docs/engineering/operator-deep-dive-runbook.md`. Depth rises on a line
   that is exactly `(` and falls on `)`; a line starting `export ` at depth 0 fails. **Checked lines** are those
   starting `python -m assetops_backend.`, `python -m uvicorn ` or `python tools/world_history.py`; each is split
   with `shlex`, its `$VARS` and `"$VARS"` replaced from a fixed table (one value per variable the runbook declares in
   its "Shell variables" line; an undeclared variable fails), and parsed by that program's `build_parser()`; the
   uvicorn line instead checks that its target is `assetops_backend.main:app` and that `main.py`'s AST assigns `app`
   at module level (no import). The ordered list of (program, sub-command) pairs must equal exactly:
   `onboard_operator digest`, `onboard_operator check`, `onboard_operator apply`, `accounts.onboard set-password`,
   `world_history exports`, `load_emulated_exports`, `commercial.pseudonym_key erase` (7 lines; a missing or extra
   line fails). Rev 3's runbook holds the rehearsal and erasure only; `ON1b` adds the real-operator lines back. The runbook equals `runbook.md` from
   its first heading.
4. Demo pin: `Demo.env()` (built as `backend/tests/test_demo_combined_links.py` builds its `Demo`) with
   `ASSETOPS_TENANT_SLUG=lakeside-power`, `ASSETOPS_REAL_OPERATOR_DATA=on` and `ASSETOPS_PSEUDONYM_KEY_DIR=/k` in the
   environment holds `ASSETOPS_TENANT_SLUG == "demo"` and neither other variable; `serve_env()` likewise.

**Postgres** (`backend/tests/test_on1_onboarding_postgres.py`, pooled `--db`, routed `*_test` only):
1. `apply` of the fixture on an empty routed database with `ASSETOPS_TENANT_SLUG=lakeside-power` and keys in
   `tmp_path`: the tenant, 3 Sites (and their `site_import` rows), 7 accounts, **7 grant rows**, each `by_service`
   `service:onboarding`, and a key file. Then `create_app` serves `KOBO-001` through `registry.ledger_scope`.
2. A second `apply` writes no row (row counts of `tenant`, `site`, `operator_account`, `role_grant` unchanged).
3. Under the lock: a person-made grant inserted first makes `add_onboarding_grant` `ONBOARDING_CLOSED`; two
   concurrent `add_onboarding_grant` calls for the same (person, role) record one grant (the other is
   `ROLE_ALREADY_HELD`); `ROLES_SEPARATE` is refused by the adapter when the file rule is bypassed.
4. Then (3A3 seam, end to end): `load_emulated_exports` with the 3A3 emulator files for `lakeside-power`, Wanjiru
   submitting and Joseph accepting: four ACCEPTED uploads on the onboarded Sites.

**Regression beside them:** the 3C0a service, API and Postgres files (`build_parser` rename; nothing else moves); the 3A2 service, API and Postgres files; 3A3's loader tests; RC4-F1's file; the
Site import tests (`test_s1_foundation_postgres.py`); `test_demo_combined_links.py`; `alembic heads` one head;
check-all.

## 7. Guard

`tools/checks/configuration-persistence.ps1` is **not changed** (rev 3): `add_onboarding_grant` reuses the
registered `_INSERT_GRANT` shape of `role_grant`, owned by `accounts/adapters/postgres_account_store.py`; the
under-lock `SELECT`s are reads. Show the guard failing on a planted `UPDATE role_grant` in the account adapter, on a
planted `INSERT INTO role_grant` in `onboarding/service.py`, and on a planted `os.unlink` in
`commercial/pseudonym_key.py`.

## 8. Done (questions; each can fail)

1. Does one emulated file create the tenant, its Sites (through the Site import), its people, every role in it
   (by `service:onboarding`) and the key, and does a rerun create nothing (service 1, 2, 4, 5; Postgres 1, 2)?
2. Is **a real file refused before any write** after the RC4 checks, so no role is granted on a real operator's
   data until `ON1b` (service 3, 8)?
3. Is a change to an existing tenant, Site, person or executive refused rather than applied, and is a file other
   than the confirmed one refused (service 6)?
4. Do onboarding grants stop once a person has granted a role, also under concurrency, and does no person hold both
   a submitting and an accepting role (service 7, 10; Postgres 3)?
5. Is real data onboarded only into an `assetops_op_<name>` database with the switch on and the server serving that
   tenant, emulated data refused there, and can no test connect to any database while checking it (service 8,
   settings 2, the no-connect self-tests)?
6. Does an erased key stay erased in every tombstone form, with no new key, a plain 409 on upload and a refusal on
   onboarding (keys 1 to 4, service 9)?
7. Does the server serve the tenant `ASSETOPS_TENANT_SLUG` names, refuse to start on an operator database without it,
   and does the demo serve `demo` whatever the shell holds (settings 1, 2, 4; Postgres 1)?
8. Does exactly the listed set of runbook commands parse, with no top-level `export`, and is the runbook the spec's
   text (settings 3)?
9. Is no password, email or name printed or stored beyond the account rows (service 2), and does each submitter
   differ from every accepter (file tests)?
10. Does each planted violation of the reviewer guide fail its named test, and is nothing changed beyond §4's files,
    the tests and fixture of §6, and the packet?

Packet: `specs/ON1-operator-tenant/packet.md`.

## 9. Units

| Unit | Content | Commit |
|---|---|---|
| 0.5 | `operator_file.py` (with `roles_digest`, separation), the fixture, file tests | 1 |
| 1.0 | `service.py` (with step 3a), `onboard_operator.py` (`digest`, `check`, `apply`), `tenant_slugs`, `onboard_grant`, `add_onboarding_grant`, `onboarding_open`, `executive_of`, `served_tenant_slug`, accessors and `create_app`; service 1 to 10, settings 1, 2; Postgres 1 to 4; 3C0a regression | 2 |
| 0.5 | Tombstone, `erase`, `key_state`, `directory_ok`, `PSEUDONYM_KEY_ERASED`; the demo pin; `world_history.build_parser`; key tests; the runbook copy and settings 3, 4; plants; check-all; packet | 3 |

Rev 2 was 2.5 units in four commits; the 0.5 saved is rev 2's commit 3 (migration 0066, proposals, approval at
sign-in, the API fields, the guard edit) less the 0.25 the automatic grant and the real refusal cost (D-ON1.15).

## 10. Out of scope

Onboarding a real operator: the executive's approval at sign-in, the proposal tables and the real-operator runbook
steps are the queued unit **`ON1b`** (0.75 unit, D-ON1.16). Creating, migrating or dropping any database (the
coordinator, by the runbook); a screen for any of
this (`3C0b` and later); changing a Site, person or role after onboarding (the executive's grant API; Site changes
through the Foundation); currency, tariff, diesel price and loss band (D-ON1.8); cold-room and EV operators (RC5);
raw-file retention (3A2 queue Q2).

## 11. Decision queue (W3)

| # | Question | Default applied |
|---|---|---|
| Q1 | Who grants the roles in the onboarding file? | **Answered by the owner** ("A, executive approves roles at first sign-in", `owner/owner-on1-roles-executive-approves-2026-11-20.md`), then allowed to wait ("the approval step can wait if autoamtic approval for the demo saves us time", `owner/owner-on1-approval-can-wait-2026-11-20.md`). Rev 3: emulated roles automatic; real files refused until `ON1b` builds A (D-ON1.15, D-ON1.16) |
| Q2 | Erasure: delete the key and keep the database until retention ends, or both at once? | Both at the agreed term; deleting the key alone is allowed and is terminal for intake (D-ON1.7). **Owner to weigh in** on the retention term per operator |
| Q3 | The tariff, declared diesel price and expected loss band in the onboarding file | Not collected: the tariff and prices arrive as the operator's own records (tariff sheet, budget lines, fuel invoices) through intake; the loss band waits for `4a`, which connects `technical_loss_kwh` |
| Q4 | One operator per operator database | Yes (RC4: "its own database") |
| Q5 | Later grants through the executive's API can still give one person both submit and accept roles | Not limited this fortnight (no grant screen; onboarding's own grants refuse it, §3.3); carried to `3C0b` with D-ON1.10 |
| Q6 | Defer option A to `ON1b` and refuse real operators until then? | **Yes** (D-ON1.15): 0.5 unit saved on lane A's path to `DDR`; no real export is planned this fortnight (`two-week-build-plan.md` "No real export yet"). **Owner to weigh in** only if a signed DPA could arrive before `ON1b` is built; default: `ON1b` is built as soon as a DPA is in sight, before any real file |
