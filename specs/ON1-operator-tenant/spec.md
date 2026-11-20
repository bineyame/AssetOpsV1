# ON1: an operator's tenant from one onboarding file (implementer spec)

Status: **rev 1**, spec handshake step 1 (`.ai/RULES.md` §4). Questions: `handshake.md` before code,
`mid-build-questions.md` during it. Reviewer: `reviewer-guide.md`. Decisions with reasons: `rulings.md` (D-ON1.1 to
D-ON1.8). The runbook's text: `runbook.md` (this folder), copied verbatim by the build.

Architect (Claude), 2026-11-20. Lane A, the deep-dive path's unit 6 (`two-week-build-plan.md` §0.1 row 6; D-BW1.11;
owner RC1 to RC9 accepted, `owner/owner-recut-decisions-rc1-rc9-2026-11-20.md`: RC4 real data only in its own
database, created by the coordinator after a signed DPA, deleted at the agreed retention; RC5 mini-grid only; RC7 the
owner presents).
- **Builds on (merged, `main` 6db81330a, plus `3A3` which merges first):** `3C0a` (`accounts/service.py`
  `AccountService.onboard_create`, `grant`; `accounts/store.py` `AccountStore`; `accounts/onboard.py` `_parser`,
  `main`; `model.ROLES`, `ONBOARDING`, `GrantRow`); `3A3` (`AccountService.onboard_person`, `OnboardPerson`); the Site
  import (`sites/foundation_service.py` `import_site`, `ImportSource`, `ImportConflict`; `sites/site_parsing.py`
  `parse_site_document`; `sites/foundation_records.py` `FoundationStore`, `TenantNotFound`, `TenantRef`;
  `sites/adapters/postgres_foundation_store.py` `ensure_tenant`, `resolve_tenant`, `find_site`; `sites/composition.py`
  `build_foundation_store`); `3A2` (`commercial/composition.py` `commercial_upload_settings`, `create_key_file`,
  `FileKeyStore`, `KeyExists`, `KeyDirectoryMissing`; `commercial/adapters/file_key_store.py`;
  `commercial/pseudonym_key.py` `main`; `commercial/uploads.py` step 7); `config.DEVELOPMENT_TENANT_SLUG`;
  `main.create_app` (`FoundationService(foundation_store, DEVELOPMENT_TENANT_SLUG, ...)`).

Non-screen. **1.75 units, three commits** (the plan's 1.5 plus the served tenant and the erasure tombstone; rulings
D-ON1.5, D-ON1.7). Discovery review (W5): the real-data boundary (RC4), people and roles (OD-14), key erasure.

## 0. Before you start

- **Branch** `task/ON1-operator-tenant` off `main` after `3A3` merges (it edits `commercial/uploads.py`,
  `pseudonym.py`, `file_key_store.py` and `messages.py` after 3A3 does); worktree `/opt/assetecon/AssetOpsV1-on1`.
  Code starts when the handshake has no open question.
- **Python:** as 3A3 §0.
- **Read:** this spec, `rulings.md`, `runbook.md`; 3C0a `spec.md` §3 ("Grant", "Who did it"), §4.1, §7 and
  `rulings.md` D-3C0A.7; 3A2 `spec.md` §3.4 ("Key store", "Key command") and §4 "Settings"; `sites/foundation_service.py`
  `plan_import` and `import_site`; `sites/site_parsing.py` `SITE_KEYS` to `COMPONENT_KEYS`; `main.py` `create_app` to
  the `FoundationService(...)` call; `backend/tests/foundation_fakes.py` `InMemoryFoundationStore`;
  `backend/tests/test_3c0a_accounts_service.py` `MemoryStore`.
- **Databases.** Postgres tests run only on the harness's routed `*_test` databases (`tools/heavy-slot.sh --db`). **No
  test creates, names or connects to a database whose name starts with `assetops_op`**: the RC4 checks are tested on
  in-memory ports with names placed in `DATABASE_URL` (no connection is made before the refusal). The runbook's
  database steps are for the coordinator after a signed DPA; no agent runs them. Never ports 5490 or 8990, the
  walkthrough DB or Docker.
- **No migration.**

## 1. Outcome and why

A person in the Analyst role fills one onboarding file with the operator: the operator, its mini-grid Sites (code,
name, time zone, location, lifecycle, installed components) and its people with their roles. One command checks it
against the database and the switches and prints what it would create; the same command applies it: the tenant, its
Sites through the existing Site import, the people's accounts and roles, and the tenant's pseudonym key. Re-running
creates nothing more. On an operator database (`assetops_op_<name>`) only a `real` file is admitted, and only with the
real-data switch on and the server set to serve that tenant (RC4). The server serves the tenant named by
`ASSETOPS_TENANT_SLUG`, so 3A2's Site path works for the operator's Sites. A key erased at the end of retention can
never be recreated, so a re-sent file is refused in plain words instead of conflicting (3A2 residual). A runbook takes
a person from the signed DPA to the first accepted export and to erasure.

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

Rules, each refusal `OnboardRefused(code, where)` (`where` a JSON path such as `sites[2].code`, never a value):
- `format` exactly as above (`ONBOARD_FORMAT`); JSON that does not parse, is not an object, or is over size
  (`ONBOARD_FILE`).
- `data` is `emulated` or `real` (`ONBOARD_DATA`).
- `operator.slug` fullmatches `[a-z0-9][a-z0-9-]{0,62}` and is not `demo` (`ONBOARD_SLUG`); `name` 1 to 120 characters
  after `strip()`, equal to its stripped form (`ONBOARD_NAME`); `vertical` exactly `MINI_GRID` (`ONBOARD_VERTICAL`,
  RC5).
- `sites`: 1 to 50 entries; `code` fullmatches `[A-Z0-9][A-Z0-9-]{0,63}` (2a's site code) and is unique
  case-insensitively (`ONBOARD_SITE_CODE`); the other site fields are passed to the Site document (§3.2) and judged by
  `parse_site_document` (`ONBOARD_SITE_INVALID`, `where` = `sites[i]`, plus the parser's message).
- `people`: 1 to 50 entries; `email` normalised by 3C0a's `passwords.normalise_email` (`ONBOARD_EMAIL`), unique by
  key (`ONBOARD_EMAIL_DUPLICATE`); `name` 1 to 120 after strip (`ONBOARD_NAME`); `roles` 1 to 5 entries, each
  `{"role"}` or `{"role", "site"}`: role in `model.ROLES` (`ONBOARD_ROLE`); `site` present exactly for
  `SITE_MANAGER` and naming a file Site (`ONBOARD_ROLE_SITE`); no duplicate (role, site) for a person
  (`ONBOARD_ROLE_DUPLICATE`).
- Exactly one person holds `OPERATOR_EXECUTIVE` (`ONBOARD_EXECUTIVE_COUNT`); at least one holds
  `FINANCE_AND_COMMERCIAL_LEAD` and at least one `ANALYST` (`ONBOARD_ROLES_MISSING`): without them no export can be
  submitted or accepted.
- Not collected (D-ON1.8): passwords, currency, tariff, loss band.

## 3. Rules

### 3.1 Check, then apply (D-ON1.1)

`OperatorOnboarding(foundation: FoundationStore, accounts: AccountService, keys: KeyFiles, *, clock, database_name:
str | None, real_data: bool, served_slug: str)` in `backend/assetops_backend/onboarding/service.py`, with `check(f:
OperatorFile) -> Plan` and `apply(f) -> Plan` (the plan as executed). `KeyFiles` is a port: `state(tenant_id) ->
"MISSING" | "PRESENT" | "ERASED"`, `create(tenant_id) -> None`.

`check`, in this order (first refusal wins; codes in §5):
1. **RC4** (D-ON1.6): `f.data == "real"` needs `real_data`; `"emulated"` needs not `real_data`
   (`ONBOARD_DATA_MISMATCH`). (`commercial_upload_settings` has already refused a switch that disagrees with the
   database name; the command calls it first.)
2. `served_slug == f.slug` (`ONBOARD_TENANT_NOT_SERVED`).
3. When real: `foundation.tenant_slugs()` is empty or exactly `(f.slug,)` (`ONBOARD_DATABASE_NOT_EMPTY`: one
   operator per operator database).
4. Tenant: `resolve_tenant(f.slug)`; absent is `create`; present with another name is `ONBOARD_TENANT_DIFFERS`; else
   `keep`. Key: absent tenant is `create`; else `keys.state(id)`: `ERASED` is `ONBOARD_KEY_ERASED`; `PRESENT` is
   `keep`; `MISSING` is `create`.
5. Sites, each: the Site document and its `ImportSource` (§3.2). Tenant present and `find_site(id, code)` found: its
   `import_record.source_path` must equal the source's path and `source_sha256` its sha256
   (`ONBOARD_SITE_CHANGED sites[i]`), then `keep`; otherwise `create`.
6. People, each, `accounts.onboard_person(email)`: `None` is `create`; another tenant's is `ONBOARD_EMAIL_TAKEN
   people[i]`; this tenant's with another display name, or not active, is `ONBOARD_PERSON_DIFFERS people[i]`; else
   `keep`. The file's executive, when `keep`, must hold `OPERATOR_EXECUTIVE` (`ONBOARD_EXECUTIVE_DIFFERS`); when
   `create` on a tenant that already has an executive, `apply`'s `onboard_create` refuses `EXECUTIVE_EXISTS` (exit 3).
7. Grants, each non-executive (person, role, site): held (from `onboard_person.roles`, the Site ID resolved through
   `find_site`) is `keep`, else `grant`. Any `grant` while `accounts.onboarding_open(f.slug)` is false is
   `ONBOARDING_CLOSED` (D-ON1.3).

`apply` runs `check`, then in this order, each step only for `create`/`grant` entries: `ensure_tenant(f.slug,
f.operator.name, now=clock())`; `import_site(foundation, tenant_slug=f.slug, configured_tenant_slug=f.slug,
source=..., legacy_documents=(), clock=clock)` per Site (an `ImportConflict` is `ONBOARD_SITE_CHANGED`);
`accounts.onboard_create(f.slug, email, name, secrets.token_urlsafe(32), executive=<holds OPERATOR_EXECUTIVE>)` per
person (the password is never stored or shown, D-ON1.4); `accounts.onboard_grant(f.slug, email, role, site)` per
grant; `keys.create(tenant_id)`. A refusal mid-way stops; the steps done stay, and a rerun's `check` marks them `keep`.

`Plan` (printed as one JSON object): `{"tenant": {"slug", "id" (null until it exists), "action"}, "sites": [{"code", "action"}], "people":
[{"index", "action", "roles": [...]}], "grants": [{"index", "role", "site", "action"}], "key": "create" | "keep"}`.
No email, name or password is printed.

### 3.2 The Site document (D-ON1.2)

`site_document(site) -> dict`: `{"site_id": code, "display_name": name, "site_type": "MINIGRID", "location":
{"country", "locality"}, "timezone", "lifecycle_status": lifecycle, "origin": "USER", "source": {"mode": "LIVE" if
real else "SIMULATED"}, "foundation": {"version": 1, "valid_from", "summary": "Onboarded from the operator's onboarding
file.", "components": [{"component_id": id, "component_type": type, "display_name": name, "rating": rating}]}}`.
`ImportSource(path=f"onboarding:{slug}/{code}", sha256=sha256(json.dumps(document, sort_keys=True,
separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest(), record=parse_site_document(document,
source=path), document_format="ASSETOPS_ONBOARDING_JSON")`. A Site's sha256 depends on its own entry only, so adding a
Site later does not change the others.

### 3.3 People and roles (D-ON1.3, D-ON1.4; 3C0a code)

- `AccountService.onboard_grant(tenant_slug, email, role, site_code) -> GrantRow`, by `ONBOARDING`. Refusals in order:
  `TENANT_NOT_FOUND` 404; `PERSON_NOT_FOUND` 404 (another tenant's too); `ROLE_UNKNOWN` 422; `ONBOARD_EXECUTIVE_GRANT`
  422 (the executive is granted only by `onboard_create(..., executive=True)`); `ROLE_SITE_RULE` 422;
  `SITE_NOT_FOUND` 404; then the store's `ONBOARDING_CLOSED` 409 and `ROLE_ALREADY_HELD` 409.
- Store `add_onboarding_grant(row: GrantRow) -> GrantRow`: one transaction under the tenant's role lock (3C0a R6's
  `role_grant:` advisory lock); refuses `ONBOARDING_CLOSED` when `SELECT 1 FROM role_grant WHERE tenant_id = :t AND
  by_person_id IS NOT NULL LIMIT 1` finds a row, then `ROLE_ALREADY_HELD` as `add_grant`; then the plain `INSERT INTO
  role_grant` 3C0a already registers. The in-memory store mirrors both checks.
- `AccountService.onboarding_open(tenant_slug) -> bool`: the same read, outside a lock (the store method
  `person_grant_exists(tenant_id) -> bool`).
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
- The other uses of `DEVELOPMENT_TENANT_SLUG` (command-line tools and backfills that refuse any other tenant) are not
  changed: none is on the deep-dive path. `3B7a`'s rebuild command takes `served_tenant_slug()` (carried to its spec).

### 3.5 Erasure is terminal (D-ON1.7; 3A2 code)

- `commercial/adapters/file_key_store.py`: a tombstone `<dir>/<tenant_id>.erased`. `FileKeyStore.key` first opens the
  tombstone (`O_RDONLY | O_NOFOLLOW`); present (or a symlink) raises `PseudonymKeyErased` (new, `pseudonym.py`).
  `create_key_file` refuses with `KeyErased` (new) when the tombstone exists, before anything else after the directory
  check. New `key_state(directory, tenant_id) -> str` (`ERASED` if the tombstone exists, else `PRESENT` if the key
  exists, else `MISSING`; no key bytes read). New `erase_key_file(directory, tenant_id) -> str`: a missing directory is
  `KeyDirectoryMissing`; neither file is `KeyMissing` (new); otherwise, if no tombstone, write it (`O_WRONLY | O_CREAT
  | O_EXCL`, 0600, content `b"erased\n"`, `os.fsync`), then unlink the key if present, then `os.fsync` the directory;
  returns `ERASED`, or `ALREADY_ERASED` when the tombstone existed and no key remained.
- `commercial/composition.py` re-exports `key_state`, `erase_key_file`, `KeyErased`, `KeyMissing`, and builds
  `FileKeyFiles(directory)` (the `KeyFiles` port: `state`, `create`).
- `pseudonym_key.py`: a public `build_parser()`; new sub-command `erase --dir --tenant-id`: stdout `Erased.` or
  `Already erased.` exit 0; `KeyMissing` exit 2 "No key exists for this tenant."; `KeyDirectoryMissing` as `create`.
  `create` on a tombstone: exit 2 "This tenant's key was erased. A new key would not match the records already held;
  onboard the operator as a new tenant."
- `CommercialUploads._check` step 7: `PseudonymKeyErased` is 409 `PSEUDONYM_KEY_ERASED`, words
  `commercial_upload.key_erased`: "This organisation's customer identities were erased, so its exports are no longer
  received."

## 4. Code

| File | Holds |
|---|---|
| `backend/assetops_backend/onboarding/__init__.py`, `operator_file.py` | `FORMAT`, `OperatorFile`, `SiteEntry`, `PersonEntry`, `parse_operator_file(data: bytes) -> OperatorFile`, `OnboardRefused(code, where, detail=None)`, `site_document`, `site_source` (§2, §3.2). No I/O |
| `backend/assetops_backend/onboarding/service.py` | `KeyFiles` (Protocol), `Plan`, `OperatorOnboarding` (§3.1) |
| `backend/assetops_backend/onboard_operator.py` | the command (§5), `build_parser()`, `main(argv, *, onboarding=None)` |
| `backend/assetops_backend/sites/foundation_records.py`, `adapters/postgres_foundation_store.py` | `FoundationStore.tenant_slugs() -> tuple[str, ...]` (`SELECT slug FROM tenant ORDER BY slug`) |
| `backend/assetops_backend/accounts/service.py`, `store.py`, `adapters/postgres_account_store.py` | `onboard_grant`, `onboarding_open`, `add_onboarding_grant`, `person_grant_exists` (§3.3) |
| `backend/assetops_backend/accounts/onboard.py` | `_parser` renamed `build_parser` (public); behaviour unchanged |
| `backend/assetops_backend/config.py`, `main.py` | §3.4 |
| `backend/assetops_backend/commercial/pseudonym.py`, `adapters/file_key_store.py`, `composition.py`, `pseudonym_key.py`, `uploads.py` | §3.5 |
| `backend/assetops_backend/i18n/messages.py` | `commercial_upload.key_erased` (a `# ON1` block) |
| `Docs/engineering/operator-deep-dive-runbook.md` | `runbook.md` of this folder, verbatim from its first `#` heading |
| `backend/tests/fixtures/on1/lakeside-power.onboarding.json` | the Lakeside rehearsal tenant (§6) |

## 5. The command (`python -m assetops_backend.onboard_operator`)

`check --file FILE` and `apply --file FILE`, both with `--key-dir DIR` (default `ASSETOPS_PSEUDONYM_KEY_DIR`; neither is
`ONBOARD_KEY_DIR_REQUIRED`). Steps: `DATABASE_URL` unset is `DATABASE_URL_REQUIRED`; `commercial_upload_settings(url)`
(`ConfigurationError` is `CONFIGURATION <message>`); `served_tenant_slug()` (same); the file read with
`Path(file).read_bytes()` (a top-level command, as `publish_assumption.py`); `parse_operator_file`; build the service
from `build_foundation_store(url)`, `build_account_service(url)`, `FileKeyFiles(key_dir)`, the UTC clock,
`database_name(url)`, `settings.real_data`, `served`; `check` or `apply`. Success prints the plan on stdout and exits
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
| `ONBOARDING_CLOSED` | The executive now grants roles; ask them to grant this one. |
| `ONBOARD_KEY_DIR_REQUIRED` | Name the key directory (--key-dir or ASSETOPS_PSEUDONYM_KEY_DIR). |
| `DATABASE_URL_REQUIRED`, `CONFIGURATION` | as 3C0a's command and the settings message |

An `AccountRefused` or `KeyDirectoryMissing` in `apply` prints its code and exits 3.

## 6. Tests

**Fixture** `lakeside-power.onboarding.json`: `data` `emulated`; operator `lakeside-power`, "Lakeside Power",
`MINI_GRID`; Sites `KISIWA-001` (Kisiwa mini-grid), `KOBO-001` (Kobo mini-grid), `MTO-001` (Mto mini-grid), each
`Africa/Nairobi`, Kenya, its locality, `ACTIVE`, `2026-07-01T00:00:00Z`, components from the manifest's `physical`
(Kobo: PV_ARRAY 60 kW, INVERTER 50 kW, BATTERY 200 kWh, GENERATOR 40 kW; Kisiwa: PV_ARRAY 30 kW, BATTERY 80 kWh,
GENERATOR 60 kW `gen-ks-01`, GENERATOR 60 kW `gen-ks-02`; Mto: PV_ARRAY 50 kW, INVERTER 25 kW `inv-mt-01`, INVERTER
25 kW `inv-mt-02`, BATTERY 150 kWh, GENERATOR 30 kW); people Amina (executive), Joseph (finance lead), Wanjiru
(analyst), Peter (Site manager KOBO-001), Halima (KISIWA-001), David (MTO-001), Musa (field technician), emails
`<name lower>@lakeside-power.example`. (The manifest's `demo_workflow` people; `DDR` uses this file.)

**File, no database** (`backend/tests/test_on1_operator_file.py`): the fixture parses; one planted refusal per row of
§2 (each code once, `where` asserted); an unknown key at each level; a duplicate JSON key; 262145 bytes.

**Service, no database** (`backend/tests/test_on1_onboarding_service.py`), world: `InMemoryFoundationStore` (it
gains `tenant_slugs`, the one edit to `foundation_fakes.py`) and a
`MemoryStore` subclass whose `tenant_by_slug`, `tenant_slug` and `site_id` read the foundation fake; an in-memory
`KeyFiles`; clock `2026-11-20T09:00:00+00:00`:
1. `check` on an empty world: tenant, 3 Sites, 7 people, 6 grants and the key all `create`.
2. `apply`: tenant `lakeside-power` named "Lakeside Power"; 3 imported Sites whose `site_import.source_path` is
   `onboarding:lakeside-power/<code>`; 7 accounts; Amina's executive grant by `service:onboarding`; the other six
   grants by `service:onboarding`; the key created; the plan printed holds no `@`.
3. A second `apply`: every entry `keep`; no write (the fakes count writes).
4. Partial run: the account store raises on the fourth `onboard_create`; the rerun completes and the end state equals
   test 2's.
5. Changes refused: a Site's `name` changed (`ONBOARD_SITE_CHANGED sites[1]`); the operator name changed
   (`ONBOARD_TENANT_DIFFERS`); Joseph's name changed (`ONBOARD_PERSON_DIFFERS people[1]`); an email of tenant `acme`
   (`ONBOARD_EMAIL_TAKEN`).
6. OD-14 kept: after Amina grants a role through `AccountService.grant`, a file adding a role is `ONBOARDING_CLOSED`;
   a file with no new grant still applies (`keep`).
7. RC4 matrix (no connection; names only): `data` `real` with `real_data=False` and `emulated` with `real_data=True`
   are `ONBOARD_DATA_MISMATCH`; `served_slug` `demo` is `ONBOARD_TENANT_NOT_SERVED`; real with another tenant present
   is `ONBOARD_DATABASE_NOT_EMPTY`.
8. Key erased: `KeyFiles.state` `ERASED` is `ONBOARD_KEY_ERASED` before any write.
9. `onboard_grant` refusals: `ONBOARD_EXECUTIVE_GRANT`, `ROLE_SITE_RULE`, `SITE_NOT_FOUND`, `ROLE_ALREADY_HELD`,
   `PERSON_NOT_FOUND` for another tenant's email.

**Keys, no database** (`backend/tests/test_on1_key_erasure.py`, `tmp_path`):
1. `erase` writes the tombstone (mode 0600) and removes the key; a second `erase` prints `Already erased.`; `create`
   then exits 2 with the sentence and writes nothing.
2. `FileKeyStore.key` raises `PseudonymKeyErased` with a tombstone, also when a key file is still present (crash
   between the two steps), and when the tombstone is a symlink.
3. 3A2 path: an upload `check` with an erased key is 409 `PSEUDONYM_KEY_ERASED` with its words; with the key missing
   it is still 409 `PSEUDONYM_KEY_MISSING`.
4. `key_state` gives MISSING, PRESENT, ERASED.

**Settings and runbook, no database** (`backend/tests/test_on1_served_tenant.py`):
1. `served_tenant_slug()`: unset `demo`; `lakeside-power`; `""`, `Lakeside`, `a b` refused.
2. `create_app()` with `ASSETOPS_REAL_OPERATOR_DATA=on`, `DATABASE_URL` naming `assetops_op_pilot1` (never
   connected: the refusal precedes every store) and `ASSETOPS_TENANT_SLUG` unset raises `ConfigurationError`; with
   the switch off, `assetops_test` and the slug `lakeside-power`, the app's `FoundationService` is built for
   `lakeside-power` (inspect the registry's service tenant slug; no request is made).
3. Runbook: every line of `Docs/engineering/operator-deep-dive-runbook.md` inside a fenced block that starts with
   `python -m assetops_backend.` is split with `shlex`, its `$VARS` replaced from a fixed table (`SLUG`
   lakeside-power, `KEY_DIR` /k, `FILE` /f.json, `TENANT_ID` a UUID, `EMAIL` a@b.example, `DIR` /d, `REASON` x), and
   parsed by that module's `build_parser()` without error; the runbook equals `runbook.md` from its first heading.

**Postgres** (`backend/tests/test_on1_onboarding_postgres.py`, pooled `--db`, routed `*_test` only):
1. `apply` of the fixture on an empty routed database with `ASSETOPS_TENANT_SLUG=lakeside-power` and keys in
   `tmp_path`: the tenant, 3 Sites (and their `site_import` rows), 7 accounts, 7 grant rows (all `by_service`
   `service:onboarding`), and a key file; then `create_app` serves `KOBO-001` through `registry.ledger_scope`.
2. A second `apply` writes no row (row counts of `tenant`, `site`, `operator_account`, `role_grant` unchanged).
3. `add_onboarding_grant` under the lock: a person-made grant inserted first makes it `ONBOARDING_CLOSED`.
4. Then (3A3 seam, end to end): `load_emulated_exports` with the 3A3 emulator files for `lakeside-power`, Wanjiru
   submitting and Joseph accepting: four ACCEPTED uploads on the onboarded Sites.

**Regression beside them:** the 3C0a service, API and Postgres files (`build_parser` rename; grants unchanged); the
3A2 service, API and Postgres files; 3A3's loader tests; the Site import tests (`test_s1_foundation_postgres.py`);
check-all.

## 7. Guard

Extend `tools/checks/configuration-persistence.ps1`'s account-writer block only if the new under-lock read is counted
as a write shape (it must not be: a `SELECT` is a read); show the guard still failing on a planted `UPDATE role_grant`
in the account adapter and on a planted `os.unlink` in `commercial/pseudonym_key.py` (outside the registered file
writer).

## 8. Done (questions; each can fail)

1. Does one file create the tenant, its Sites (through the Site import), its people with their roles, and its key,
   and does a rerun create nothing (service 1 to 4, Postgres 1 and 2)?
2. Is a change to an existing tenant, Site or person refused rather than applied (service 5)?
3. Are roles granted from the file only until the executive grants one (OD-14; service 6, Postgres 3)?
4. Is real data onboarded only into an `assetops_op_<name>` database with the switch on and the server serving that
   tenant, and is emulated data refused there, all without any test touching such a database (service 7, settings 2)?
5. Does an erased key stay erased: no new key, a plain 409 on upload, a refusal on onboarding (keys 1 to 4, service 8)?
6. Does the server serve the tenant `ASSETOPS_TENANT_SLUG` names, and refuse to start on an operator database without
   it (settings 1 and 2, Postgres 1)?
7. Does every command in the runbook parse, and is the runbook the spec's text (settings 3)?
8. Is no password, email or name printed or stored beyond the account rows (service 2)?
9. Does each planted violation of the reviewer guide fail its named test, and is nothing changed beyond §4's files,
   the tests and fixture of §6, and the packet?

Packet: `specs/ON1-operator-tenant/packet.md`.

## 9. Units

| Unit | Content | Commit |
|---|---|---|
| 0.5 | `operator_file.py`, the fixture, file tests | 1 |
| 0.75 | `service.py`, `onboard_operator.py`, `tenant_slugs`, `onboard_grant` and its store method, `served_tenant_slug` and `create_app`; service, settings and Postgres tests | 2 |
| 0.5 | Tombstone, `erase`, `key_state`, `PSEUDONYM_KEY_ERASED`; key tests; the runbook copy and its test; guard plants; check-all; packet | 3 |

## 10. Out of scope

Creating, migrating or dropping any database (the coordinator, by the runbook, after the DPA); a screen for any of
this (`3C0b` and later); changing a Site, person or role after onboarding (the executive's grant API; Site changes
through the Foundation); currency, tariff, diesel price and loss band (D-ON1.8); cold-room and EV operators (RC5);
raw-file retention (3A2 queue Q2).

## 11. Decision queue (W3)

| # | Question | Default applied |
|---|---|---|
| Q1 | May the onboarding file grant roles other than the executive's (OD-14 says the executive grants)? | Yes, at onboarding only, by `service:onboarding`, from the file the operator's executive confirms (runbook step 1); closed once the executive grants any role. **Owner to weigh in** (a "no" removes `onboard_grant`; the executive then grants each role through the API) |
| Q2 | Erasure: delete the key and keep the database until retention ends, or both at once? | Both at the agreed term; deleting the key alone is allowed and is terminal for intake (D-ON1.7). **Owner to weigh in** on the retention term per operator |
| Q3 | The tariff, declared diesel price and expected loss band in the onboarding file | Not collected: the tariff and prices arrive as the operator's own records (tariff sheet, budget lines, fuel invoices) through intake; the loss band waits for `4a`, which connects `technical_loss_kwh` |
| Q4 | One operator per operator database | Yes (RC4: "its own database") |
