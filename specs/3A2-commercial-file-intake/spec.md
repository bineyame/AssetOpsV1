# 3A2: file intake of an operator's exports (implementer spec)

Status: live, spec (handshake step 1; `.ai/RULES.md` §4).

Architect (Claude), 2026-11-20. Lane A (sources), the deep-dive path's unit 2 (`two-week-build-plan.md` §0.1, row 2;
D-BW1.8 to D-BW1.12; owner RC1 to RC9 accepted, `owner/owner-recut-decisions-rc1-rc9-2026-11-20.md`).
- **Structure:** page P3A (`specs/3A1-commercial-record-store/structure-page-P3A.md`, approved 20 Nov): rules 1, 3, 4
  and 7, and "Who sees and acts".
- **Builds on (merged):** `3A1` (`backend/assetops_backend/commercial/`: `CommercialRecords.ingest`,
  `CommercialStore.write_intake`, `latest_revisions`, `intake`, `ExistingRecord`, `StoreRefused`), `2a`
  (`assetops_contracts.canonical`: `loads_canonical`, `parse_batch`, `parse_record`, `CanonicalRefused`,
  `KIND_SPECS`, `PROVENANCES`), `3C0a` (`accounts.principal.person_from_request`, `PersonPrincipal.has_role`),
  `3C1a` (`accounts.permissions.person_step`, `COMMAND_ROLES`, `roles_of`, `PersonRefused`).
- **Decisions:** `rulings.md` (D-3A2.1 to D-3A2.12). D-3A2.1 to D-3A2.3 ratify 3A1's three unstated choices.
- **Reviewer guide:** `reviewer-guide.md`. Questions: `handshake.md` before code, `mid-build-questions.md` during it.

Non-screen (no mock element; the words below are served for the later screen). **3.5 units, four commits.**
Discovery review (W5): a new schema, personal data, an acceptance seam and the real-data boundary (RC4).

## 0. Before you start

- **Branch** `task/3A2-commercial-file-intake` off `main`, after this spec branch merges. Worktree
  `/opt/assetecon/AssetOpsV1-3a2`. Code starts when the handshake has no open question.
- **Python:** as 3A1 §0 (set `PYTHONPATH` to the worktree, record `assetops_backend.__file__`,
  `assetops_contracts.__file__` and `fixtures.__file__` in the packet).
- **Read:** `rulings.md`; P3A; 3A1 `spec.md` §2 to §4 and `rulings.md`; 2a `spec.md` §6.1 to §6.8a and §7;
  `backend/assetops_backend/commercial/` (all); `backend/assetops_backend/reading_upload_api.py` (route shape,
  `_body_within`, refusal envelope); `accounts/permissions.py`; `main.py:238-360` and `:665-675`;
  `integration-source-to-canonical-design.md` §6.9 (searched); `tools/checks/configuration-persistence.ps1:967-1050`
  (the commercial writer block); `backend/tests/test_3a1_commercial_service.py:46-230` (the in-memory store and
  helpers); `backend/tests/test_3c1a_person_work.py:60-117` (`People`).
- **Databases:** `*_test` only, through the harness, every Postgres run as `tools/heavy-slot.sh --db -- <command>`.
  Never ports 5490 or 8990, the walkthrough DB or Docker. No real operator data anywhere (RC4).
- **Migration** `0065_commercial_upload` on `0064_person_on_work`. If another migration merges first, renumber at
  merge preparation (D-3A1.12); tests read the head and `down_revision` from the modules.
- **Collisions.**
  - `3A4` (lane B, same days) adds read methods to `commercial/store.py`, the Postgres adapter and
    `commercial/composition.py`. You add write methods to the same files. Whichever merges second merges `main` first;
    the two sets of methods do not overlap.
  - `3B3` touches `structure/` only. `IA-1` and `DS1m` touch mock-up and generator files only.

## 1. Outcome and why

A person in the Analyst role (or the finance lead) sends an operator's export to the product, sees in plain words
what it would add, correct, already hold and refuse, row by row, and submits it. The finance lead (or the executive
as backup, OD-15) accepts or declines it. Only an accepted file reaches the commercial store, in one transaction with
its acceptance. Customer, meter and staff identifiers are pseudonymised before anything is kept. A late record lands
in its own month. Nothing real is accepted on a server that is not the operator's own database (RC4).

Why next: the deep-dive needs an operator's own exports in the store (`3A3`, `3A6`, `DDR` build on this); `3B7a`
rebuilds "after an accepted import", which needs acceptance to exist.

## 2. Records: migration `0065_commercial_upload`

`TABLES = ("commercial_upload", "commercial_upload_decision")`. Raw string `UPGRADE = r"""..."""`, exactly:

```sql
CREATE TABLE commercial_upload (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    site_id uuid NULL,                                   -- NULL: the organisation path
    file_name text NOT NULL CHECK (char_length(file_name) BETWEEN 1 AND 200
                                   AND strpos(file_name, '/') = 0 AND strpos(file_name, chr(92)) = 0),
    file_sha256 text NOT NULL CHECK (file_sha256 ~ '^[0-9a-f]{64}$'),   -- of the bytes as received; bytes never kept
    file_bytes int NOT NULL CHECK (file_bytes BETWEEN 0 AND 8388608),
    reader text NOT NULL CHECK (reader ~ '^[a-z][a-z0-9.:@_-]{0,99}$'),
    source_type text NOT NULL CHECK (source_type ~ '^[a-z][a-z_]{0,39}$'),
    source_system text NOT NULL CHECK (char_length(source_system) BETWEEN 1 AND 200),
    provenance text NOT NULL CHECK (provenance IN ('demo-simulated', 'source-emulated', 'bench-tested',
                                                   'field-integrated', 'observed-financial')),
    batch text NOT NULL,                                 -- the pseudonymised canonical batch (UTF-8 JSON)
    batch_sha256 text NOT NULL CHECK (batch_sha256 ~ '^[0-9a-f]{64}$'),
    row_map int[] NULL,                                  -- file row per record index; NULL: row = index + 1
    record_count int NOT NULL CHECK (record_count >= 0),
    new_count int NOT NULL CHECK (new_count >= 0),
    revised_count int NOT NULL CHECK (revised_count >= 0),
    unchanged_count int NOT NULL CHECK (unchanged_count >= 0),
    refused_count int NOT NULL CHECK (refused_count >= 0),
    refusal_index int[] NOT NULL,
    refusal_code text[] NOT NULL,
    refusal_path text[] NOT NULL,
    month_site_code text[] NOT NULL,                     -- NULL element: portfolio level
    month_period text[] NOT NULL,
    submitted_by uuid NOT NULL,
    submitted_role text NOT NULL CHECK (submitted_role IN ('ANALYST', 'FINANCE_AND_COMMERCIAL_LEAD')),
    submitted_at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, site_id) REFERENCES site (tenant_id, id),
    FOREIGN KEY (tenant_id, submitted_by) REFERENCES operator_account (tenant_id, id),
    CHECK (new_count + revised_count + unchanged_count + refused_count = record_count),
    CHECK (new_count + revised_count >= 1),
    CHECK (cardinality(refusal_index) = refused_count AND cardinality(refusal_code) = refused_count
           AND cardinality(refusal_path) = refused_count),
    CHECK (cardinality(month_site_code) = cardinality(month_period)),
    CHECK (row_map IS NULL OR cardinality(row_map) = record_count),
    UNIQUE (tenant_id, id)
);
CREATE INDEX commercial_upload_tenant_at ON commercial_upload (tenant_id, submitted_at DESC);
CREATE TABLE commercial_upload_decision (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    upload_id uuid NOT NULL UNIQUE,
    decision text NOT NULL CHECK (decision IN ('ACCEPTED', 'DECLINED')),
    reason text NULL CHECK (reason IS NULL OR (char_length(reason) BETWEEN 1 AND 500 AND reason = btrim(reason))),
    intake_id uuid NULL,
    decided_by uuid NOT NULL,
    decided_role text NOT NULL CHECK (decided_role IN ('FINANCE_AND_COMMERCIAL_LEAD', 'OPERATOR_EXECUTIVE')),
    decided_at timestamptz NOT NULL,
    FOREIGN KEY (tenant_id, upload_id) REFERENCES commercial_upload (tenant_id, id),
    FOREIGN KEY (tenant_id, intake_id) REFERENCES commercial_intake (tenant_id, id),
    FOREIGN KEY (tenant_id, decided_by) REFERENCES operator_account (tenant_id, id),
    CHECK ((decision = 'ACCEPTED') = (intake_id IS NOT NULL)),
    CHECK ((decision = 'DECLINED') = (reason IS NOT NULL))
);
```

Then the `ledger_append_only()` trigger on both tables, and the 0063-style downgrade: lock both, refuse with
`RAISE EXCEPTION 'Downgrade refused: commercial uploads exist'` if either has a row, drop in reverse order. No column
defaults; every time comes from the service clock. Not in the chain change log (D-3A1.6 stands).

## 3. Rules

### 3.1 Who, where (D-3A2.8, D-3A2.9)

Two paths, one service. **Site path** `/api/sites/{site_code}/commercial-uploads`: every record must be this Site's.
**Organisation path** `/api/organisation/commercial-uploads`: records of any Site of the person's tenant, and
portfolio-level records (`BUDGET_LINE`, `CONTRACT_DOCUMENT` without `site_code`). A signed-in person is always
required on both, whatever `ASSETOPS_REQUIRE_PERSON` says: these routes are new and have no unsigned path.

Add to `COMMAND_ROLES` (and to `SPEC_ROLES` in `backend/tests/test_3c1a_person_work.py`, which pins the table), with
constants `ANALYST = "ANALYST"` and `EXECUTIVE = "OPERATOR_EXECUTIVE"` beside the existing three:

| Command key | Roles, admitting order |
|---|---|
| `commercial.upload` (check and submit) | ANALYST, FINANCE_AND_COMMERCIAL_LEAD |
| `commercial.upload_decision` (accept, decline) | FINANCE_AND_COMMERCIAL_LEAD, OPERATOR_EXECUTIVE |
| `commercial.upload_read` (list, one upload) | ANALYST, FINANCE_AND_COMMERCIAL_LEAD, OPERATOR_EXECUTIVE, SITE_MANAGER |

`person_step`'s `site_id` annotation widens to `UUID | None` (no behaviour change: `has_role` already ignores it
for every role but SITE_MANAGER, and a SITE_MANAGER check with `None` is false). The submitter may also accept their
own upload; both people are recorded (D-3A2.9, queue Q1).

### 3.2 Check and submit (`dry_run=true` / `false`), in this order

1. **Reader** (D-3A2.7). `READERS[reader_id]`; unknown is 422 `UPLOAD_READER_UNKNOWN`. Media type not in
   `reader.media_types` is 415 `UPLOAD_UNSUPPORTED_TYPE`. Over `MAX_UPLOAD_BYTES = 8 * 2**20` is 413
   `FILE_TOO_LARGE` (read with `_body_within`, never whole past the limit).
2. `file_sha256 = sha256(data)`. The bytes are never stored or logged (D-3A2.10).
3. `obj = reader.read(data)`; a `CanonicalRefused` is 422 `UPLOAD_FILE_REFUSED` with `params.code`,
   `params.field` (`reader.field_label(path)`).
4. `parse_batch(obj)` for the envelope only: a `CanonicalRefused` is 422 `UPLOAD_FILE_REFUSED` as above.
5. `batch.tenant_code` not the tenant's slug: 422 `UPLOAD_TENANT_MISMATCH`.
6. **Provenance cap** (D-3A2.6). With `real_data` off: only `source-emulated` and `demo-simulated` are admitted.
   With it on: only `observed-financial`. Anything else: 422 `UPLOAD_PROVENANCE_NOT_ALLOWED`, `params.provenance`.
7. **Key.** `keys.key(tenant_id)`: `PseudonymKeyMissing` is 409 `PSEUDONYM_KEY_MISSING`;
   `PseudonymKeyUnusable` is 503 `PSEUDONYM_KEY_UNUSABLE`.
8. **Pseudonymise** (§3.4): `obj2 = pseudonymise(obj, key, reader_paths)`, `data2 = encode(obj2)` with
   `json.dumps(obj2, ensure_ascii=False, separators=(",", ":")).encode("utf-8")`.
9. **Dry run in the store:** `records.ingest(tenant_id, data2, entered_by=f"person:{pid}", dry_run=True,
   site_scope=<the Site's id, or None on the organisation path>)`. A REFUSED intake here cannot happen after steps
   4 and 5; if it does, it is 500 `COMMERCIAL_STORE_FAULT`.
10. **Months** named by the file: from `parse_batch(obj2)`, every valid record whose outcome is NEW or REVISED and
    has `clocks.recognition_period`, as `(site_code or None, period)`, distinct, sorted with `None` first then by
    `(site_code, period)`. A record without a recognition period (a SETTLEMENT may omit it) names no month here;
    `3A4` places it.
11. `dry_run=true` answers 200 with the preview (§5). Nothing is written.
12. `dry_run=false`: `new + revised == 0` is 422 `UPLOAD_NOTHING_NEW`. Otherwise `store.add_upload(UploadRow)` and
    201 with the upload (state `WAITING`). The commercial store is **not** written (D-3A2.4).

### 3.3 Decide

- Load the upload in scope (`site_id` equal to the path's Site, or `NULL` on the organisation path); otherwise 404
  `UPLOAD_NOT_FOUND` (another tenant's, another Site's, or a malformed ID, the same body).
- A decision already recorded: 409 `UPLOAD_ALREADY_DECIDED` (checked first outside, then definitively under the
  tenant's commercial lock).
- **Accept** (D-3A2.4): `records.ingest(tenant_id, upload.batch.encode("utf-8"), entered_by=f"person:{pid}",
  dry_run=False, site_scope=upload.site_id, acceptance=Acceptance(decision_id, upload_id, pid, role))`. One
  transaction: the lock, the "no decision yet" check, the plan's rows, then the `ACCEPTED` decision row whose
  `intake_id` is the plan's intake. The intake's `entered_by` is the accepting person. Outcomes may differ from the
  preview (another upload may have landed); the answer shows the real ones.
- **Decline:** `store.write_decline(UploadDecisionRow(..., "DECLINED", reason, None, ...))` under the same lock with
  the same check. Nothing reaches the commercial store.
- `reason`: required for DECLINE, 1 to 500 characters after trimming; must be absent or `null` for ACCEPT; else 422
  `UPLOAD_DECISION_INVALID`.

### 3.4 Pseudonymisation (D-3A2.5)

- `pseudonym(key, cls, value) = f"{cls}-" + hmac.new(key, f"{cls}\x1f{value}".encode("utf-8"),
  hashlib.sha256).hexdigest()[:32]`. Classes: `C` customer, `M` meter, `P` person. Deterministic per tenant key, so
  a repeated file is still UNCHANGED, and the same customer links across billing, payments and the meter register.
- `PERSONAL_FIELDS` (literal, in `commercial/pseudonym.py`), applied only to a record object that `parse_record`
  accepts; a refused record is left exactly as sent, so 2a refuses it with its own code (a bad ref is never hidden
  behind a valid pseudonym):

| Kind | Path, class |
|---|---|
| `CHARGE` | `subject.ref` when `subject.kind` is CUSTOMER (C) or METER (M); `body.account_ref` (C) |
| `RECEIPT` | `subject.ref` (C); `body.payer_ref` (C) |
| `ADJUSTMENT` | `subject.ref` when CUSTOMER (C) or METER (M); `body.authorised_by_ref` (P) |
| `EXPENSE` | `body.counterparty_ref` (P) only when `body.category` is `STAFF` |
| `STORAGE_MOVEMENT` | `body.customer_ref` (C) |
| `CUSTOMER_METER_READ` | `subject.ref` (M); `body.meter_ref` (M) |
| `METER_ASSIGNMENT` | `subject.ref` (M); `body.meter_ref` (M); `body.customer_ref` (C) |
| `FLEET_ROSTER` | `body.tag_ref` (P) |
| all others | none |

- A reader may add paths (`ReadResult.personal_paths: frozenset[tuple[str, str]]`, path and class), only from
  `ALLOWED_EXTRA = {"source_record_id"} | {"subject.ref"} | {f"body.{name}"}` for a body field that 2a types as a
  ref; any other path is `ValueError` (a reader bug). This is 3A6's room: a profile names its personal columns.
- **Key store.** `PseudonymKeys` port: `key(tenant_id) -> bytes`. `FileKeyStore(directory)` reads
  `<directory>/<tenant_id>.key`: absent is `PseudonymKeyMissing`; not exactly 32 bytes, or `st_mode & 0o077 != 0`, is
  `PseudonymKeyUnusable`. The key never sits in the database (D-3A2.5).
- **Key command** `python -m assetops_backend.commercial.pseudonym_key create --dir <dir> --tenant-id <uuid>`: 32
  bytes from `secrets.token_bytes`, written with `os.open(path, O_WRONLY | O_CREAT | O_EXCL, 0o600)`; an existing
  file is refused (exit 2, "A key already exists for this tenant; it is never replaced."). No other subcommand.
  Erasure is deleting the file (a named pilot residual, D-3A1.10).
- Not pseudonymised: set-of-refs fields (`applied_to`, `receipts`, `parties`), `vehicle_ref`, supplier
  `counterparty_ref`. Queue Q3.

### 3.5 Store changes (3A1 code)

- `CommercialRecords.ingest(..., site_scope: UUID | None = None, acceptance: Acceptance | None = None)`. Defaults
  keep 3A1's behaviour byte for byte.
- **Site scope.** In `_Decision.__call__`, after the `INTAKE_SITE_UNKNOWN` check and before identity: when
  `site_scope` is not None and the record's `site_id != site_scope` (a portfolio-level record included), refuse with
  `INTAKE_SITE_NOT_THIS_SITE record.site_code`.
- **Acceptance.** `write_intake(..., decision: UploadDecisionRow | None = None)`. When given and not a dry run: under
  the lock and before `decide`, `SELECT 1 FROM commercial_upload_decision WHERE tenant_id = :t AND upload_id = :u`
  raises `UploadAlreadyDecided` (new, `commercial/model.py`); after the plan's rows, insert the decision. The service
  builds the row with `intake_id = plan.intake.id` and `decided_at` the intake's clock. The envelope-refusal path
  (`_refuse`) passes it through the same way.
- New port methods: `add_upload(row: UploadRow) -> None`; `write_decline(row: UploadDecisionRow) -> None` (lock,
  check, insert); `upload(tenant_id, upload_id) -> UploadRecord | None`; `uploads_in_scope(tenant_id, site_id:
  UUID | None, limit: int) -> tuple[UploadRecord, ...]` (exactly that Site, or `site_id IS NULL`; newest first by
  `(submitted_at, id)`). `UploadRecord(upload: UploadRow, submitted_by_name: str, decision: UploadDecisionRow |
  None, decided_by_name: str | None, intake: IntakeSummary | None)`; names joined from `operator_account`.
- **Errors (D-3A2.2).** The adapter catches every `DBAPIError` that is not `OperationalError` or `InterfaceError`
  and raises `StoreRefused(constraint_or_None)` outside the handler (no cause, no context), as it does today for
  `IntegrityError`. `OperationalError` and `InterfaceError` pass through for the route's 503.

## 4. Code

| File | Holds |
|---|---|
| `commercial/model.py` (add) | frozen `UploadRow` (every column of `commercial_upload`, arrays as tuples), `UploadDecisionRow`, `UploadRecord`, `Acceptance(decision_id, upload_id, person_id, role)`, `UploadAlreadyDecided(Exception)` |
| `commercial/readers.py` | `ReadResult(obj, rows: tuple[int, ...] \| None, personal_paths: frozenset[tuple[str, str]])`; `SourceReader` Protocol (`id`, `media_types`, `read(data) -> ReadResult`, `field_label(path) -> str`); `CanonicalJsonReader` (`id = "canonical-json-v1"`, `media_types = frozenset({"application/json"})`, `read` is `loads_canonical`, `rows = None`, no extra paths); `READERS: Mapping[str, SourceReader]` (a `MappingProxyType`); `DEFAULT_READER = "canonical-json-v1"` |
| `commercial/pseudonym.py` | `PERSONAL_FIELDS`, `ALLOWED_EXTRA`, `pseudonym`, `pseudonymise(obj, key, extra=frozenset()) -> object` (a new object; the input is not mutated), `PseudonymKeys`, `FileKeyStore`, `PseudonymKeyMissing`, `PseudonymKeyUnusable` |
| `commercial/pseudonym_key.py` | the key command (`main(argv) -> int`) |
| `commercial/uploads.py` | `CommercialUploads(records, store, keys, *, clock, real_data: bool)` with `check`, `submit`, `decide`, `get`, `list`; `UploadScope(site_id, site_code)`; `Actor(person_id, role)`; `UploadRefused(Exception)` with `status`, `code`, `params` |
| `commercial/composition.py` (add) | `UploadSettings(key_dir: Path \| None, real_data: bool)`; `commercial_upload_settings(database_url: str \| None) -> UploadSettings`; `build_commercial_uploads(database_url, settings) -> CommercialUploads`; `COMMERCIAL_UNAVAILABLE = (OperationalError, InterfaceError)` |
| `commercial_upload_api.py` | `build_commercial_upload_router(uploads, scope, *, accounts, unavailable, access) -> APIRouter` |
| `main.py` | `create_app(..., commercial_uploads: CommercialUploads \| None = None)` (last keyword); when None, `database_url()` is set and `settings.key_dir` is not None, build it; always mount the router with `registry.ledger_scope`, `accounts`, `unavailable=(*ACCOUNTS_UNAVAILABLE, *COMMERCIAL_UNAVAILABLE)` and `access=site_read_access` |

**Settings** (D-3A2.6). `ASSETOPS_PSEUDONYM_KEY_DIR`: unset means the uploads are off (403
`COMMERCIAL_UPLOAD_OFF`). `ASSETOPS_REAL_OPERATOR_DATA`: unset or `off` is off, `on` is on, else
`ConfigurationError`. The database name (`sqlalchemy.engine.make_url(url).database`) must match
`^assetops_op_[a-z0-9_]{1,40}$` **if and only if** the switch is on; otherwise `ConfigurationError("Real operator
data needs its own database (assetops_op_<name>) and ASSETOPS_REAL_OPERATOR_DATA=on, together.")` at `create_app`.
Only the coordinator creates such a database, after a signed data-processing agreement (RC4).

## 5. HTTP routes (`commercial_upload_api.py`)

Every route is `async`, calls the service through `run_in_threadpool`, and answers refusals as
`{"code", "message", "words", "params"}` (the reading-upload envelope; `message` rendered for the request locale).
Every response carries `Cache-Control: no-store`. `COMMERCIAL_UNAVAILABLE` and the account store's unavailable types
answer 503 `COMMERCIAL_UPLOAD_UNAVAILABLE`; `StoreRefused` answers 500 `COMMERCIAL_STORE_FAULT` with no detail.

| Route | Command | Success |
|---|---|---|
| `POST {base}?dry_run=true\|false&file_name=<name>[&reader=<id>]`, body the file | `commercial.upload` | 200 `{"state": "CHECKED", ...Preview}` / 201 `Upload` |
| `GET {base}` | `commercial.upload_read` | 200 `{"uploads": [UploadSummary, ...]}` (50 newest) |
| `GET {base}/{upload_id}` | `commercial.upload_read` | 200 `Upload` |
| `POST {base}/{upload_id}/decision`, JSON `{"decision": "ACCEPT"\|"DECLINE", "reason"}` (4 KiB) | `commercial.upload_decision` | 201 `Upload` |

`{base}` is `/api/sites/{site_code}/commercial-uploads` or `/api/organisation/commercial-uploads`.

**Refusal order, Site path:** `access` (401 `UNAUTHENTICATED`, 403 `SITE_SCOPE_FORBIDDEN`, as reading upload);
`scope` (404 `SITE_NOT_FOUND`); `uploads is None` (403 `COMMERCIAL_UPLOAD_OFF`); `person_step(request, accounts,
required=True, unavailable=..., tenant_id, site_id, command, enabled=True)`: `UNAVAILABLE` 503, `PERSON_REQUIRED` 401,
`TENANT` the byte-equal Site 404, `PERSON_ROLE_REQUIRED` 403 with `params.roles`; then the request: `dry_run` not
`true`/`false`, or `file_name` not 1 to 200 characters after `strip()` or holding `/` or `\`: 422
`UPLOAD_BAD_REQUEST` with `params.field`; then §3.2 steps 1 to 12. Decision route: JSON content type (415
`JSON_REQUIRED`), body over 4 KiB, not an object, an unknown key, `decision` not one of the two: 422
`UPLOAD_DECISION_INVALID` with `params.field`; then §3.3.
**Organisation path:** the same, with no `access`/`scope` step: the person comes from `person_from_request` (an
account-store error 503, none 401 `PERSON_REQUIRED`); the tenant is `person.tenant_id`; the admitting role is the
first of `roles_of(command)` for which `person.has_role(role, None)`; none is 403 `PERSON_ROLE_REQUIRED`.

**Shapes.**
- `Preview` = `{"source_type", "source_system", "provenance", "counts": Counts, "months": [{"site_code", "period"}],
  "refusals": [Refusal, ...] (first 200 by row), "refusals_total", "words", "text"}`.
- `Counts` = `{"records", "new", "revised", "unchanged", "refused"}`.
- `Refusal` = `{"row", "field", "code", "words", "text"}`: `row` is `rows[index]` or `index + 1`; `field` is
  `reader.field_label(path)`; `words` is `message(f"commercial_upload.reason.{code.lower()}")`; `text` is
  `render(message("commercial_upload.row_refused", row=row, field=field, reason=render(words)))`.
- `Upload` = `UploadSummary` plus `"preview": Counts`, `"months"`, `"refusals"`, `"refusals_total"`, `"result"`:
  `null` or `{"intake_id", "state", "counts": Counts}` (from `IntakeSummary`), with `refusals` from the stored
  rejections once accepted and from the upload's preview arrays before.
- `UploadSummary` = `{"upload_id", "scope": "SITE"|"ORGANISATION", "site_code", "file_name", "file_sha256",
  "reader", "source_type", "source_system", "provenance", "submitted_by": {"person_id", "display_name"},
  "submitted_role", "submitted_at", "state": "WAITING"|"ACCEPTED"|"DECLINED", "decision": null | {"by":
  {"person_id", "display_name"}, "role", "at", "reason"}, "words", "text"}`.
- No response holds a record value, a ref or the batch (D-3A1.10).

**Field labels** (`CanonicalJsonReader.field_label`): `json` and `batch` give "the file"; `batch.<k>` gives `<k>`;
`record` gives "the record"; `record.<rest>` gives `<rest>` (so `record.body.payer_ref` is `body.payer_ref`).

**Words** (`i18n/messages.py`, a `# 3A2` block; English):

| Key | English |
|---|---|
| `commercial_upload.row_refused` | Row {row}, {field}: {reason} |
| `commercial_upload.summary` | {new} new, {revised} corrected, {unchanged} already held, {refused} refused. |
| `commercial_upload.state.checked` | Checked. Nothing is kept until you submit. |
| `commercial_upload.state.waiting` | Waiting for the finance lead to accept it. |
| `commercial_upload.state.accepted` | Accepted by {name}. |
| `commercial_upload.state.declined` | Declined by {name}: {reason} |
| `commercial_upload.off` | Sending exports is switched off on this server. |
| `commercial_upload.unavailable` | Exports cannot be reached right now. Try again shortly. |
| `commercial_upload.store_fault` | The export could not be kept. Nothing was changed. |
| `commercial_upload.bad_request` | The request is not complete: {field}. |
| `commercial_upload.unsupported_type` | This kind of file is not read here. |
| `commercial_upload.too_large` | The file is larger than {limit_mb} MB. |
| `commercial_upload.reader_unknown` | That file layout is not known. |
| `commercial_upload.file_refused` | This file cannot be read: {field}. {reason} |
| `commercial_upload.tenant_mismatch` | This file is for another organisation. |
| `commercial_upload.provenance_not_allowed` | This server does not take {provenance} data. |
| `commercial_upload.nothing_new` | Nothing in this file is new: every row is already held or refused. |
| `commercial_upload.key_missing` | This organisation is not set up to receive exports yet. |
| `commercial_upload.key_unusable` | This organisation's export set-up is damaged. Ask the administrator. |
| `commercial_upload.not_found` | No such export here. |
| `commercial_upload.already_decided` | This export was already accepted or declined. |
| `commercial_upload.decision_invalid` | The decision is not complete: {field}. |
| `commercial_upload.json_required` | Send the decision as JSON. |
| `commercial_upload.person_required` | Sign in to continue. |
| `commercial_upload.role_required` | Your role cannot do this here. |

Reasons (`commercial_upload.reason.<code lower>`, no parameters):

| Code | English |
|---|---|
| `CANONICAL_VERSION` | the format version must be 1. |
| `CANONICAL_KIND` | this kind of record is not known. |
| `CANONICAL_FIELD` | a required value is missing. |
| `CANONICAL_FORBIDDEN` | this value is not allowed for this kind of record. |
| `CANONICAL_TYPE` | this value has the wrong form. |
| `CANONICAL_NUMBER` | write the number as digits with a point, like 1800.00. |
| `CANONICAL_SIGN` | this number cannot be negative or zero here. |
| `CANONICAL_ENUM` | this value is not one of the allowed choices. |
| `CANONICAL_UNIT` | this unit is not allowed here. |
| `CANONICAL_CURRENCY` | the currency must be a three-letter code, like USD. |
| `CANONICAL_CLOCK` | this date or time cannot be read; times need their UTC offset. |
| `CANONICAL_RANGE` | this value is out of range or out of order. |
| `CANONICAL_REF` | this reference is empty, too long or holds a character that is not allowed. |
| `CANONICAL_DUPLICATE` | this appears twice. |
| `CANONICAL_FACTOR` | this budget line does not name a known heading, or its currency does not fit it. |
| `CANONICAL_SOURCE_TYPE` | this kind of record does not belong in this export. |
| `CANONICAL_PROVENANCE` | the data's origin is not one of the known words. |
| `INTAKE_NOT_COMMERCIAL` | this record belongs with operations records, not money records. |
| `INTAKE_SITE_UNKNOWN` | no Site of this organisation has this code. |
| `INTAKE_SITE_NOT_THIS_SITE` | this row is for another Site; send it from that Site or from the organisation. |
| `INTAKE_KIND_CHANGED` | this record was sent before as another kind of record. |
| `INTAKE_SITE_CHANGED` | this record was sent before for another Site. |
| `INTAKE_VERSION_CONFLICT` | this version was sent before with other content; send the correction as a new version. |
| `INTAKE_PROVENANCE_CHANGED` | this version was sent before with another origin. |
| `INTAKE_TENANT_MISMATCH` | this file is for another organisation. |

A test asserts every code in 2a's `§6.7` list and every `INTAKE_*` code the service emits has a reason key.

## 6. Tests

Shared helpers: subclass, never edit, 3A1's `MemoryCommercialStore` (`from test_3a1_commercial_service import
MemoryCommercialStore, Clock`) as `UploadMemoryStore`, adding the §3.5 methods with the same lock and check. People
from `test_3c1a_person_work.People` (tenant `acme`, Sites `KOBO-001`, `KISIWA-001`; Fiona finance, Ana analyst,
Amina executive (call `people.sign("amina")`), Peter Kobo Site manager, Fatma field technician, Hugo of `beta`);
the commercial world registers tenant `acme` (People's tenant ID) with People's Site IDs. Key: `bytes(range(32))`
through an in-memory `PseudonymKeys`. Batches are built in the test with tenant code `acme`.

**Data** (`T_SUBMIT = 2026-11-06T09:00:00+00:00`, one clock per test):
- `B_BILL` (`billing_export`, `kobo-vending`, `source-emulated`): `KOBO-CH-0001` v1 CHARGE KOBO-001, period
  `2026-10`, effective `2026-10-01` to `2026-11-01`, 120.00 USD, 400 kWh, USAGE, `tariff_code` `T-RES`, subject
  CUSTOMER `C-0412`, `account_ref` `C-0412`; `KOBO-RC-0001` v1 RECEIPT KOBO-001, `2026-10-30T19:00:00+03:00`, period
  `2026-10`, 100.00 USD, COLLECTED, MOBILE_MONEY, `payer_ref` `C-0412`, subject CUSTOMER `C-0412`.
- `B_LATE` (`expense_ledger`, `lakeside-accounts`, `source-emulated`): `KOBO-EX-OM-1029` v1 EXPENSE KOBO-001,
  occurred `2026-10-29T10:00:00+03:00`, period `2026-10`, 95.00 USD, INVOICED, OM, `counterparty_ref` `SUP-OM`,
  `document_ref` `INV-OM-1029`.
- `B_MIXED`: `B_BILL` plus a CHARGE `KISIWA-CH-0001` for `KISIWA-001` and a record with `amount.value` `"12,5"`.
- `B_BUDGET` (`budget_workbook`, `lakeside-budget-2026`, `source-emulated`): a KOBO-001 BUDGET_LINE `diesel_price`
  1.25 USD and a portfolio-level `staff` 1200.00 USD, period `2026-10`, version `budget-2026-v1`.

**Service, no database** (`backend/tests/test_3a2_commercial_upload_service.py`):
1. Check `B_BILL` on the Kobo path: 2 new, nothing written anywhere; months `[("KOBO-001", "2026-10")]`.
2. Submit then accept: one upload row, one decision (ACCEPTED, the intake's ID), one STORED intake with
   `entered_by` the accepter's `person:<uuid>`; `latest_revisions` holds the two records.
3. Pseudonyms: the stored `canonical` of the charge has `subject.ref` and `account_ref` equal to
   `C-448c423147e7b551e039ebc4c61f2029`, the receipt's `payer_ref` the same; no stored text, upload `batch`,
   rejection, refusal path or exception contains `C-0412` (grep over every stored string).
4. Pseudonym goldens with key `bytes(range(32))`: `M`, `MT-2201` is `M-c04f202e85dd8387ebaf47111ad43111`; `P`,
   `P-JOSEPH` is `P-8612fd0721ba1f89ecbd14eff25bcf42`. A STAFF expense's counterparty is pseudonymised; a FUEL
   expense's is not.
5. A refused record keeps its own code: a RECEIPT whose `payer_ref` has a leading space is `CANONICAL_REF
   record.body.payer_ref`, not admitted under a pseudonym.
6. The same file submitted and accepted twice: the second submit is 422 `UPLOAD_NOTHING_NEW`.
7. Late record: `B_LATE` checked and accepted at `T_SUBMIT`: months `[("KOBO-001", "2026-10")]`; the stored
   revision's `recognition_period` is `2026-10`; a v2 at 98.00 is REVISED and supersedes it.
8. `B_MIXED` on the Kobo path: `INTAKE_SITE_NOT_THIS_SITE record.site_code` at row 3, `CANONICAL_NUMBER
   record.amount.value` at row 4, the two Kobo records new (a refused row never sinks its file).
9. `B_BUDGET` on the Kobo path: the portfolio line is `INTAKE_SITE_NOT_THIS_SITE`; on the organisation path both
   are new.
10. Provenance cap: with `real_data=False`, `observed-financial` is 422 `UPLOAD_PROVENANCE_NOT_ALLOWED`; with
    `True`, `source-emulated` is refused and `observed-financial` admitted.
11. Decline: needs a reason; writes the decision only; a later accept is 409 `UPLOAD_ALREADY_DECIDED`.
12. `UploadAlreadyDecided` under the lock: a decision row inserted between the outside check and the lock makes the
    accept raise it and write nothing (the in-memory store's hook).
13. Key missing (409) and key unusable (wrong length; mode `0o644` with `FileKeyStore` on `tmp_path`) (503).
14. Another tenant's file: 422 `UPLOAD_TENANT_MISMATCH`.
15. Every reason key exists for 2a's 17 codes and the 8 `INTAKE_*` codes; `INTAKE_SITE_NOT_THIS_SITE` words render.
16. `ALLOWED_EXTRA`: a reader declaring `body.amount` raises `ValueError`; one declaring `source_record_id` (C)
    pseudonymises it and the record is still UNCHANGED on a repeat.
17. The key command: creates a 32-byte file with mode `0o600`; a second `create` exits 2 and leaves it unchanged.
18. 3A1's behaviour is unchanged: `ingest` without the new keywords gives byte-identical plans on 3A1's fixture
    run (run `backend/tests/test_3a1_commercial_service.py` unchanged).

**API, no database** (`backend/tests/test_3a2_commercial_upload_api.py`), a `FastAPI` with only this router and the
in-memory services:
1. The refusal order of §5, one test per step, on both paths.
2. Roles: Ana and Fiona may check and submit; Peter (Site manager), Fatma and Amina may not (403 with `roles`);
   Fiona and Amina may decide; Ana may not; Peter may read Kobo's uploads and not the organisation's; Hugo gets the
   byte-equal Site 404.
3. No session: 401 `PERSON_REQUIRED` with `ASSETOPS_REQUIRE_PERSON` unset.
4. A body naming `actor` or `person_id` on the decision route: 422 `UPLOAD_DECISION_INVALID`, field the key.
5. 413 at `MAX_UPLOAD_BYTES + 1` without reading the whole body; 415 for `text/csv` with the canonical reader.
6. Responses: `Cache-Control: no-store`; no response body contains `C-0412` or the batch.
7. `StoreRefused` from the store is 500 `COMMERCIAL_STORE_FAULT` with no constraint name in the body.

**Postgres** (pooled, `--db`; `backend/tests/test_3a2_commercial_upload_postgres.py`):
1. Tables, triggers, index; UPDATE and DELETE refused on both; each CHECK fails on a planted row (one per CHECK).
2. Accept is atomic: with a decision row planted to fail its CHECK through the adapter, no intake, record,
   revision, rejection or decision row is left.
3. Lock proof (3A1's shape): the test holds the tenant's commercial lock, starts two accepts of one upload in
   threads, sees both alive after 0.5 s and two advisory waiters in `pg_locks`, releases: one ACCEPTED, one
   `UploadAlreadyDecided`, exactly one intake for the upload. Recorded negative run with the under-lock check
   removed.
4. A `DataError` (an `UploadRow` with `file_bytes = 2**31`, out of `int` range) and an `IntegrityError` both leave as
   `StoreRefused`; `str()`, `__cause__` and `__context__` hold
   no row value.
5. `uploads_in_scope` and `upload` round-trip, with display names; the organisation scope lists only `site_id IS
   NULL`.
6. Downgrade refused with one upload row; down then up on an empty clone.

**Regression beside them:** `test_3a1_commercial_service.py`, `test_3a1_commercial_postgres.py`,
`test_3c1a_person_work.py` (its `SPEC_ROLES` gains §3.1's three rows), `test_3c0a_accounts_postgres.py`,
`test_pg_harness.py`, `tools/checks/test_estate_guard.py`.

Commands (as 3A1 §6, with these files); `pwsh -NoProfile -File tools/check-all.ps1` once at the end;
`python3 tools/select-tests.py --base main` is "full" because of the migration (not run while building).

## 7. Guard

Extend the commercial writer block in `tools/checks/configuration-persistence.ps1`: `$commercialTables` gains
`commercial_upload` and `commercial_upload_decision`, with the same plain-INSERT shape and anti-vacuity, and
`commercial_upload_decision` also admits the one read `SELECT 1 FROM commercial_upload_decision WHERE ...` (a read is
not a write; check the guard does not count it). Show it failing on a planted `INSERT INTO commercial_upload` in
`commercial/uploads.py` and on a planted `UPDATE commercial_upload_decision` in the adapter.

## 8. Done (questions; each can fail)

1. Does a file go check, submit, accept, with nothing in the commercial store before acceptance, and the store's rows
   and the acceptance in one transaction?
2. Is every customer, meter and staff identifier of the table in §3.4 pseudonymised before anything is kept, and is
   a malformed identifier still refused with 2a's own code?
3. Does a refused row never sink its file, and does each refusal name its row and field in plain words?
4. Does a late record land in its own recognition month, and a corrected version become a revision of it?
5. Are only the roles of §3.1 admitted, a person always required, and another tenant answered "not found"?
6. Is real data refused on a server that is not the operator's own database, and emulated data refused on one that
   is (RC4)?
7. Are the 2a and `INTAKE_*` codes all worded, and do no response, log or error carry a record value or ref?
8. Do the guard and the lock proof each fail on their planted violation?
9. Is nothing changed beyond: the migration; `commercial/**`; `commercial_upload_api.py`; `main.py` (the keyword and
   mount); `accounts/permissions.py` (§3.1); `i18n/messages.py` (the `# 3A2` block); the four test files and the
   `SPEC_ROLES` rows; the guard block; the packet?

Packet: `specs/3A2-commercial-file-intake/packet.md`, with the module paths, the negative lock run and the
mid-build question count.

## 9. Units

| Unit | Content | Commit |
|---|---|---|
| 1 | Migration 0065; model rows; adapter methods, decision under the lock, `DBAPIError` scrub; Postgres tests | 1 |
| 1 | Pseudonymiser, key store and command; readers; site scope in `_Decision`; service; service tests | 2 |
| 1 | Routes, words, `COMMAND_ROLES`, `create_app`, settings; API tests | 3 |
| 0.5 | Guard block and its planted failures; check-all; packet | 4 |

## 10. Out of scope

Native CSV and XLSX layouts and source profiles (`3A6`); emulators and the contract test (`3A3`); amounts by month
and "out of date" (`3A4`); labels on screens (`3A5`); the screen itself; a store for raw files (queue Q2);
retention and deletion at the agreed term (pilot runbook); creating any database (coordinator, after the DPA).

## 11. Decision queue (W3)

| # | Question | Default applied |
|---|---|---|
| Q1 | May the person who submitted an upload also accept it? | Yes, both recorded; small operators have one finance person. **Owner to weigh in** |
| Q2 | The design (§6.9) keeps the raw file 24 months in a restricted store; this unit keeps only its SHA-256 | Keep none; the operator keeps the original under the DPA. **Owner to weigh in** |
| Q3 | Set-of-refs fields and contract `parties` are not pseudonymised | Not on the mini-grid path (RC5); revisit with `9a0` and the cold-chain and EV kinds |
| Q4 | The real-data database is named `assetops_op_<name>` | Yes; the coordinator names it at creation |
| Q5 | The pseudonym key lives in a file per tenant outside the database | Yes; the coordinator creates keys for the demo and walkthrough tenants when it switches uploads on |
