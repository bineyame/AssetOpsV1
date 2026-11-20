# 3A3: emulated native exports and the source contract test (implementer spec)

Status: **rev 1**, spec handshake step 1 (`.ai/RULES.md` §4). Questions: `handshake.md` before code,
`mid-build-questions.md` during it. Reviewer: `reviewer-guide.md`. Decisions with reasons: `rulings.md` (D-3A3.1 to
D-3A3.8).

Architect (Claude), 2026-11-20. Lane A (sources), the deep-dive path's unit 4 (`two-week-build-plan.md` §0.1 row 4;
D-BW1.8 to D-BW1.12; owner RC1 to RC9 accepted, `owner/owner-recut-decisions-rc1-rc9-2026-11-20.md`; RC4 real data
only in its own database after a signed DPA; RC5 mini-grid only).
- **Structure:** page P3A (`specs/3A1-commercial-record-store/structure-page-P3A.md`), rules 1, 3, 4 and 7;
  integration design `integration-source-to-canonical-design.md` §7.2 (transport, parser, profile), §7.3 (emulators
  are placeholders; the replacement rule; the contract test) and §8 (DUP-1, CONF-1, GAP-1, LATE-SETTLE-1, SRC-1).
- **Builds on (merged, `main` 6db81330a):** `2a` (`assetops_contracts.canonical`: `parse_batch`, `parse_record`,
  `CanonicalRefused`, `SOURCE_TYPES`, `to_canonical_json`); `3A1` (`CommercialRecords`); `3A2`
  (`commercial/readers.py`: `ReadResult`, `SourceReader`, `CanonicalJsonReader`, `READERS`, `DEFAULT_READER`;
  `commercial/uploads.py`: `CommercialUploads.check`, `.submit`, `.decide`, `UploadScope`, `Actor`, `UploadRefused`,
  `_check`; `commercial/pseudonym.py`: `PERSONAL_FIELDS`, `cut_path`; `commercial/composition.py`:
  `commercial_upload_settings`, `build_commercial_uploads`, `build_commercial_records`;
  `adapters/postgres_commercial_store.database_name`); `3C0a`/`3C1a` (`AccountService`, `roles_of`,
  `COMMAND_ROLES`); `DS1b` (`simulator/assetops_simulator/world/records.py`: `build_records`, `money_text`,
  `batch_file_name`); `DS1` (`world/history.generate_history`, `world/months.period_end`, `tools/world_history.py`
  `load_view`, `_out_dir`).

Non-screen. **3 units, four commits.** Discovery review (W5): a protected seam (who may write commercial records), the
real-data boundary (R4) and a new shared contract.

## 0. Before you start

- **Branch** `task/3A3-emulators-contract` off `main` after this spec branch merges; worktree
  `/opt/assetecon/AssetOpsV1-3a3`. Code starts when the handshake has no open question.
- **Python:** as 3A2 §0 (`PYTHONPATH` = worktree `backend:backend/tests:contracts:simulator:gateway:field:host:tools`,
  absolute; `/opt/assetecon/AssetOpsV1/.venv/bin/python`; the packet records `assetops_backend.__file__`,
  `assetops_contracts.__file__`, `assetops_simulator.__file__`).
- **Read:** this spec and `rulings.md`; 3A2 `spec.md` §3.2, §3.4, §4 and `rulings.md` D-3A2.6, D-3A2.7, D-3A2.14,
  D-3A2.17 and "Handshake answers" R4; DS1b `spec.md` §2 and §3; `commercial/readers.py`, `commercial/uploads.py`
  (`_check`), `commercial/composition.py`; `tools/world_history.py`; `backend/tests/test_3a2_commercial_upload_service.py`
  lines 1 to 260 (the in-memory world, `UploadMemoryStore`, `People` use).
- **Databases:** `*_test` only, through the harness; every Postgres run `tools/heavy-slot.sh --db -- <command>`. No
  test names or creates a database whose name starts with `assetops_op`; the operator-database refusals are tested
  with the name in `DATABASE_URL` and no connection (the refusal precedes every connection). Never ports 5490 or 8990,
  the walkthrough DB or Docker. No real operator data anywhere (RC4).
- **No migration.**
- **Collisions.** `ON1` (lane A, next) edits `commercial/uploads.py`, `commercial/pseudonym.py`,
  `commercial/adapters/file_key_store.py` and `i18n/messages.py`: it branches after this unit merges. `4b`, `3B7a`
  (lane B) read the commercial store only. `DS1m`, `IA-1` touch mock-up files only.

## 1. Outcome and why

The operator-shaped exports the deep-dive needs (billing, mobile-money collections, the expense ledger with fuel
purchases, and the monthly budget) exist as **native CSV files** emulated from the demonstration manifest for the
mini-grid tenant, and they reach the commercial store **only through 3A2's intake**: read by a layout reader,
checked, pseudonymised, submitted and accepted by named people. One **contract test** suite runs on every layout
reader: a reader is registered in `READERS` only with a passing contract case, which is the admission rule for
`3A6`'s operator profiles and every later real adapter (§7.3: "a real adapter is admitted only when it passes").

Why next: `3A6` adds profiles that this contract admits; `DDR` rehearses the path on these files; `ON1` gives them a
tenant. The four 3A2 residuals are settled here (rulings D-3A3.1, D-3A3.6, D-3A3.8; the key residual goes to `ON1`,
D-ON1.7).

## 2. Rules

### 2.1 One writer of commercial records (D-3A3.1)

- `CommercialRecords.ingest` is called only by `commercial/uploads.py`. `CommercialRecords(...)` is constructed only
  in `commercial/composition.py` (`build_commercial_uploads`). Delete `build_commercial_records` (no caller on `main`).
- Every loader outside the HTTP app calls `build_commercial_uploads` and nothing below it. The callers of
  `build_commercial_uploads` are exactly `main.py` and `load_emulated_exports.py` (§3.6); a new caller is a reviewed
  change to the allowlist in test S1 and must call `refuse_operator_database` first unless it is the app.
- Consequence: every stored commercial record is pseudonymised with the tenant key and accepted by a recorded person,
  whatever produced it. Customers link across billing and collections; a record sent twice is UNCHANGED.

### 2.2 Native layouts (D-3A3.2)

New neutral module `contracts/assetops_contracts/native/layouts_v1.py` (and `native/__init__.py` re-exporting the
public names). Standard library plus `assetops_contracts.canonical` only.

```python
@dataclass(frozen=True)
class Column:
    header: str                                    # exact header cell
    paths: tuple[str, ...]                         # canonical record paths the cell fills, e.g. ("subject.ref", "body.account_ref")
    maps: Mapping[str, Mapping[str, str]] = {}     # path -> {native value: canonical value}; paths not in maps take the cell as is

@dataclass(frozen=True)
class Layout:
    id: str                                        # reader id, also commercial_upload.reader
    source_type: str                               # a key of SOURCE_TYPES
    source_system: str
    provenance: str                                # "source-emulated" for every layout in this unit
    columns: tuple[Column, ...]
    constants: Mapping[str, str]                   # path -> value, written on every record (rule C below)
    personal: frozenset[tuple[str, str]] = frozenset()   # extra (path, class) for 3A2's pseudonymise; empty here
```

`Mapping` fields are `MappingProxyType` literals. A path is dot-separated from the record root: `source_record_id`,
`source_version`, `site_code`, `kind`, `status`, `subject.kind`, `subject.ref`, `clocks.<clock>`, `amount.value`,
`amount.currency`, `quantity.value`, `quantity.unit`, `body.<field>`.

**Reading** `read_layout(layout, data: bytes, *, tenant_code: str, produced_at: str) -> NativeRead(obj, rows,
refused)`, in this order:
1. `data` without a leading UTF-8 BOM decodes as strict UTF-8, else `CanonicalRefused("NATIVE_ENCODING", "json")`.
2. `csv.reader(io.StringIO(text, newline=""), dialect="excel", strict=True)`. A `csv.Error` at any point is
   `CanonicalRefused("NATIVE_ROW", f"row.{reader.line_num}")` (the file is refused).
3. The first row must equal `[c.header for c in layout.columns]` exactly (order, case, spaces), else
   `CanonicalRefused("NATIVE_HEADER", "json")`. A file with no header row is the same.
4. Every later row with zero cells is skipped. Each other row gives one record, in file order; its row number is
   `reader.line_num` after reading it (the header is row 1).
5. A row whose cell count differs from the header's: the record is `{"format_version": 1}` and its index is refused
   `("NATIVE_ROW", f"row.{n}")`.
6. Otherwise the record starts `{"format_version": 1}`; for each column, a cell equal to `""` writes nothing; any
   other cell writes each of its paths: `maps[path][cell]` when `path in maps` (a miss refuses the index
   `("NATIVE_VALUE", f"record.{path}")`, first miss only), else the cell unchanged (no trimming, no conversion: 2a
   judges numbers, clocks and refs). Then **rule C**: each constant whose top-level object (`subject`, `amount`,
   `quantity`, `body`, `clocks`) also has a column path is written only when a column wrote into that object; every
   other constant is always written.
7. `obj = {"format_version": 1, "tenant_code": tenant_code, "source_type": layout.source_type, "source_system":
   layout.source_system, "provenance": layout.provenance, "produced_at": produced_at, "records": [...]}`.
   `rows` is the tuple of row numbers; `refused` is a `MappingProxyType` `{index: (code, path)}`.

**Rendering** `render_layout(layout, records: Sequence[Mapping]) -> bytes`: the header row, then one row per record
in the given order, `csv.writer(..., dialect="excel", lineterminator="\n")`, UTF-8, no BOM. A cell is the record's
value at the column's first path that is not in `maps`, else the inverse map of the first mapped path; every path of
the column must agree with that cell (through its map), and every constant present in the record must equal the
layout's; an absent path is `""`. Any disagreement, or a value that is not a `str`, raises
`ValueError("NATIVE_RENDER <layout id> <path>")` (an emulator bug, never an operator's). Each map must be one to one
(checked at import: `NATIVE_LAYOUT <id> <path>`).

`LAYOUTS: Mapping[str, Layout]` holds exactly the four layouts of §2.3.

### 2.3 The four illustrative layouts (exact)

Every layout: `provenance="source-emulated"`, `personal=frozenset()` (3A2's `PERSONAL_FIELDS` already covers their
customer and staff refs).

| Layout id | Source type, system | Constants |
|---|---|---|
| `billing-illustrative-1` | `billing_export`, `illustrative-vending` | `kind` CHARGE; `subject.kind` CUSTOMER; `quantity.unit` kWh; `body.line_type` USAGE |
| `collections-illustrative-1` | `mobile_money_statement`, `illustrative-mobile-money` | `kind` RECEIPT; `source_version` "1"; `subject.kind` CUSTOMER; `body.method` MOBILE_MONEY |
| `expenses-illustrative-1` | `expense_ledger`, `illustrative-accounts` | `kind` EXPENSE; `subject.kind` SITE; `quantity.unit` L |
| `budget-illustrative-1` | `budget_workbook`, `illustrative-budget` | `kind` BUDGET_LINE |

Columns, in header order (header → paths; maps):
- **billing:** `Invoice no` → source_record_id · `Revision` → source_version · `Site` → site_code · `Account` →
  subject.ref, body.account_ref · `Period start` → clocks.effective_from · `Period end` → clocks.effective_to ·
  `Billing month` → clocks.recognition_period · `kWh` → quantity.value · `Amount` → amount.value · `Currency` →
  amount.currency · `Tariff` → body.tariff_code.
- **collections:** `Transaction ID` → source_record_id · `Site` → site_code · `Paid at` → clocks.occurred_at ·
  `Month` → clocks.recognition_period · `Payer` → subject.ref, body.payer_ref · `Amount` → amount.value ·
  `Currency` → amount.currency · `Status` → status, map `{"Settled": "COLLECTED", "Pending": "PAID_IN_TRANSIT"}`.
- **expenses:** `Entry no` → source_record_id · `Revision` → source_version · `Site` → site_code, subject.ref ·
  `Date` → clocks.occurred_at · `Month` → clocks.recognition_period · `Category` → body.category, map `{"Diesel":
  "FUEL", "O&M": "OM", "Salaries": "STAFF"}` · `Supplier` → body.counterparty_ref · `Document` → body.document_ref ·
  `Litres` → quantity.value · `Amount` → amount.value · `Currency` → amount.currency · `Status` → status, map
  `{"Invoiced": "INVOICED", "Paid": "PAID", "Quote": "QUOTE"}`.
- **budget:** `Line ID` → source_record_id · `Revision` → source_version · `Site` → site_code · `Month` →
  clocks.recognition_period · `Line` → body.line_ref, body.factor_id, map for `body.factor_id` only `{"revenue":
  "revenue", "diesel_cost": "fuel_cost", "om": "om", "staff": "staff", "billed_kwh": "billed_kwh", "diesel_l":
  "diesel_l", "tariff_usd_per_kwh": "tariff", "diesel_usd_per_l": "diesel_price"}` · `Value` → body.value ·
  `Currency` → body.currency · `Budget version` → body.version_ref.

The factor IDs are the structure's own leaf and node IDs (`structure/rows_mini_grid.py`); how `5a` reads node-level
lines is `5a`'s ruling. The native file carries line labels, never factor IDs (§7.3 replacement rule): the layout maps
them.

### 2.4 The reader seam in 3A2 (D-3A3.3)

- `commercial/readers.py`: new frozen `ReadContext(tenant_code: str, received_at: datetime)`. `SourceReader.read`
  becomes `read(self, data: bytes, *, context: ReadContext) -> ReadResult`. `ReadResult` gains a last field
  `refused: Mapping[int, tuple[str, str]] = MappingProxyType({})`. `CanonicalJsonReader.read` accepts and ignores
  `context`.
- New `LayoutReader(layout)`: `id = layout.id`, `media_types = frozenset({"text/csv"})`; `read` calls
  `read_layout(layout, data, tenant_code=context.tenant_code, produced_at=context.received_at.astimezone(timezone.utc)
  .replace(microsecond=0).isoformat())` and returns `ReadResult(obj, rows, layout.personal, refused)`; `field_label`:
  `json`, `batch` or a `json.` path is "the file"; `row.<n>` is "row <n>"; `record.<path>` is the header of the first
  column whose paths hold `<path>`, else (a constant or an unmapped path) "the record"; anything else as
  `CanonicalJsonReader`.
- `READERS` = `canonical-json-v1` plus one `LayoutReader` per `LAYOUTS` value, in that order.
- `CommercialUploads._check`: call `reader.read(data, context=ReadContext(self._store.tenant_slug(tenant_id),
  self._clock()))`. After `parse_batch`, an index in `read.refused` is a refusal with the reader's `(code,
  cut_path(code, path))` whatever 2a decided for it, and is not kept. An index in `read.refused` outside
  `range(len(records))` is 500 `COMMERCIAL_STORE_FAULT` (a reader bug). Nothing else in `_check` changes.

### 2.5 The emulated exports (D-3A3.4)

New `simulator/assetops_simulator/world/exports.py`: `build_exports(view, history) -> ExportsResult(files:
tuple[ExportFile, ...], unwritten: tuple[tuple[str, ...], ...])`; `ExportFile(tenant, key, layout_id, records:
tuple[dict, ...], data: bytes)`; `file_name(f) = f"{f.tenant}.{f.key}.csv"`; `KEYS = ("billing", "collections",
"expenses", "budget")`, layout id `f"{key}-illustrative-1"`. Imports: standard library, `assetops_contracts`
(`canonical`, `native`), the world modules.

- **Scope.** Tenants with `vertical == "MINI_GRID"` only (RC5); every other tenant is listed unwritten `(tenant,
  "*", "*", "*", "*", "NOT_ON_PATH_VERTICAL")`. Month: the view's `accounting_period` only (`2026-10`). Sites in
  site-code order. Zone: `ZoneInfo(view["timezone_default"])`; currency `view["currency"]`; `as_of` as DS1b.
- **Reused from DS1b.** `build_records(view, history)`; take its batches whose tenant is in scope; of their records
  (`json.loads(to_canonical_json(batch))["records"]`) keep those with `clocks.recognition_period == month`:
  `EXPENSE` records go to `expenses`, `BUDGET_LINE` records to `budget`; any other kind is listed `(tenant, site_code,
  month, kind, source_record_id, "NOT_IN_LAYOUT")`. DS1b's `unwritten` rows for the month and in-scope tenants are
  carried as they are.
- **New records** (all `format_version` 1, `source_version` "1", IDs `gen:<site>:<month>:<side>:<name>` as DS1b),
  per Site with `a = period.actual`, `p = period.plan`, `cov = period.coverage`, prices `tenant.prices[...][site]`:
  - **Charges** (`billing`), when `cov.get("revenue") != "ESTIMATED"` and `a` has `billed_kwh` and `revenue`:
    `N = 40` customers `<site>-C-0001` … `-0040`; customer `i` gets `billed_kwh // N` kWh, plus 1 for `i <= billed_kwh
    % N`; amount cents = kWh × tariff cents (`tariff_usd_per_kwh` × 100, must be whole: `EMU_PRICE`); the sum must
    equal `revenue` in cents (`EMU_REVENUE <tenant>/<site>`). Name `charge-<i:04d>`, side `actual`, subject CUSTOMER
    `<site>-C-<i>`, `account_ref` the same, effective `<month>-01` to the next month's `-01`, recognition the month,
    quantity `str(kWh)` kWh, amount `money_text(cents)` currency, `line_type` USAGE, `tariff_code` `T-RES`.
  - **Receipts** (`collections`), same condition: `collected + in_transit + outstanding` must equal `revenue`
    (`EMU_COLLECTIONS`). Walk customers in order, each owing its charge: pay `collected` cents first, `pay =
    min(owed, left)`, one RECEIPT per payment, status COLLECTED, at day `1 + (i - 1) % 28` of the month 10:00 local;
    then pay `in_transit` from where it stopped (the part-paid customer first), status PAID_IN_TRANSIT, at the
    month's last day 19:00 local. Names `receipt-<seq:04d>` in emission order; subject CUSTOMER and `payer_ref` the
    customer; recognition the month.
  - **Fuel** (`expenses`), when `cov.get("diesel") != "ESTIMATED"` and `a` has `diesel_l` and `diesel_cost`:
    deliveries of 400 L while more than 400 remain, then the rest; `m` deliveries, delivery `k` on day `1 + (k - 1) *
    (31 // m)` 09:00 local; amount cents = litres × price cents (`diesel_usd_per_l`; `EMU_PRICE`); the sum must equal
    `diesel_cost` (`EMU_FUEL`). Name `fuel-<k>`; subject SITE `<site>`; status INVOICED; `counterparty_ref`
    `fuel-supplier`; `category` FUEL; `document_ref` the record ID; quantity `str(litres)` L.
  - **Budget lines** (`budget`), side `plan`, name the factor ID, recognition the month, `version_ref`
    `budget-2026-v1`, `line_ref` as the map key: `revenue` (p.revenue, money), `fuel_cost` (`diesel_cost`, money),
    `billed_kwh` (int text, no currency), `diesel_l` (int text, no currency), `tariff` (`tariff_usd_per_kwh`,
    `f"{Decimal(str(v)):.2f}"`, currency), `diesel_price` (`diesel_usd_per_l`, same). A plan field absent writes
    nothing, listed `PLAN_FIELD_ABSENT`. DS1b's `om` and `staff` lines complete the set.
  - Every record must pass `parse_record` (`EMU_FORMAT <tenant>/<site> <name>`).
- **Order in each file:** by site code, then: billing by name; collections by name; expenses fuel by `k`, then DS1b's
  OM, then STAFF; budget `revenue, fuel_cost, om, staff, billed_kwh, diesel_l, tariff, diesel_price`.
- `data = render_layout(LAYOUTS[layout_id], records)`. No empty file is written.
- **Tool.** `tools/world_history.py exports --manifest M --out DIR`: `_out_dir` rules (outside the repository, new
  or empty), writes each file and `unwritten.json` (`file_bytes`). An `EMU_`/`DS1B_` `ValueError` prints and exits 3.

### 2.6 Loading emulated exports (D-3A3.6, D-3A3.7)

New top-level command `backend/assetops_backend/load_emulated_exports.py`, `python -m
assetops_backend.load_emulated_exports --dir DIR --tenant SLUG --submit-as EMAIL [--accept-as EMAIL]`. Messages through
`sys.stdout.write` / `sys.stderr.write`; one JSON line per file on stdout: `{"file", "upload_id", "state", "counts"}`
(`counts` the upload's `Counts` without `words`/`text`). Exit codes: 0 done; 2 refused before any submission; 3 a
submission or decision refused (files before it stay as they are).

Order, each refusal printing `<CODE> <one sentence>` to stderr:
1. `DATABASE_URL` unset: `DATABASE_URL_REQUIRED`, exit 2.
2. `refuse_operator_database(url)` (new in `commercial/composition.py`): `database_name(url)` is `None` or
   `name.lower().startswith("assetops_op")` raises `OperatorDatabaseRefused`: `EMULATED_ON_OPERATOR_DATABASE
   Emulated exports are never loaded into an operator's database.`, exit 2. No connection has been made.
3. `commercial_upload_settings(url)`; a `ConfigurationError` is `CONFIGURATION <its message>`, exit 2; `key_dir` None
   is `COMMERCIAL_UPLOAD_OFF`, exit 2.
4. Files: `DIR` holds only regular files named `<SLUG>.<key>.csv` (`key` in `KEYS`) or `<SLUG>.<source_type>.json`
   (`batch_file_name`, reader `canonical-json-v1`), plus an optional `unwritten.json`; anything else is
   `EXPORT_FILE_UNKNOWN <name>`, exit 2. A directory holding a CSV and a JSON for the same source type is
   `EXPORT_PATHS_MIXED <source_type>`, exit 2 (D-3A3.7). Order: CSVs in `KEYS` order, then JSONs by name.
5. `accounts.onboard_person(email)` (new `AccountService` method, §2.7) for each email: not found, another tenant's,
   or not ACTIVE is `PERSON_NOT_FOUND`, exit 2. Role: the first of `roles_of("commercial.upload")` (resp.
   `"commercial.upload_decision"`) the person holds; none is `PERSON_ROLE_REQUIRED`, exit 2.
6. Per file: `uploads.submit(tenant_id, UploadScope(None, None), Actor(pid, role), data, file_name=<name>,
   reader_id=<id>, media_type="text/csv" or "application/json")`. `UPLOAD_NOTHING_NEW` prints the line with `state`
   `NOTHING_NEW` and continues (a rerun is idempotent); any other `UploadRefused` is `<its code>`, exit 3. With
   `--accept-as`, then `uploads.decide(..., "ACCEPT")`. Organisation scope always: the files hold every Site.

`build_parser() -> argparse.ArgumentParser` is public (ON1's runbook test parses the runbook's lines with it).
`main(argv, *, uploads=None, accounts=None)`: injected services skip step 3 and the composition (tests); steps 1, 2
and 4 always run. The tenant is the submitter's `OnboardPerson.tenant_id`; a person whose `tenant_slug` is not
`--tenant` is `PERSON_NOT_FOUND` (step 5).

### 2.7 One account read (3C0a code)

`AccountService.onboard_person(email) -> OnboardPerson | None`, frozen `OnboardPerson(person_id, tenant_id,
tenant_slug, display_name, active: bool, roles: frozenset[tuple[str, UUID | None]])`, from the store's
`account_by_email_key`, `current_status` and `held_grants`, and a new store read `tenant_slug(tenant_id) -> str |
None` (adapter: `SELECT slug FROM tenant WHERE id = :t`; the in-memory store from its tenants). A malformed email is
`None`. No write. (`ON1` uses the same method.)

## 3. Code

| File | Holds |
|---|---|
| `contracts/assetops_contracts/native/__init__.py`, `layouts_v1.py` | §2.2, §2.3 |
| `backend/assetops_backend/commercial/readers.py` | `ReadContext`, `ReadResult.refused`, `LayoutReader`, `READERS` (§2.4) |
| `backend/assetops_backend/commercial/uploads.py` | `_check`: context and reader refusals (§2.4) |
| `backend/assetops_backend/commercial/composition.py` | `refuse_operator_database`, `OperatorDatabaseRefused`; `build_commercial_records` deleted |
| `backend/assetops_backend/load_emulated_exports.py` | §2.6 |
| `backend/assetops_backend/accounts/service.py`, `store.py`, `model.py`, `adapters/postgres_account_store.py` | §2.7 (`OnboardPerson` in `model.py`) |
| `backend/assetops_backend/i18n/messages.py` | a `# 3A3` block: the four reasons below |
| `simulator/assetops_simulator/world/exports.py`; `tools/world_history.py` | §2.5 |

Reasons (`commercial_upload.reason.<code lower>`):

| Code | English |
|---|---|
| `NATIVE_ENCODING` | the file is not UTF-8 text. |
| `NATIVE_HEADER` | the column headings are not the ones this layout reads, in this order. |
| `NATIVE_ROW` | this row cannot be read: its cells do not line up with the headings. |
| `NATIVE_VALUE` | this value is not one this layout knows. |

## 4. Fixtures

`backend/tests/fixtures/3a3/<layout id>.csv` (golden native file, LF line ends, exactly these rows after the header of
§2.3) and `<layout id>.expected.json` (the list of canonical record objects, written by hand from the rows; never
produced by `read_layout`):
- **billing:** `INV-K-0001,1,KOBO-001,C-0412,2026-10-01,2026-11-01,2026-10,400,160.00,USD,T-RES` ·
  `INV-K-0002,1,KOBO-001,C-0413,2026-10-01,2026-11-01,2026-10,250,100.00,USD,T-RES` ·
  `INV-S-0001,1,KISIWA-001,C-0901,2026-10-01,2026-11-01,2026-10,100,55.00,USD,T-RES`
- **collections:** `MM-0001,KOBO-001,2026-10-30T19:00:00+03:00,2026-10,C-0412,100.00,USD,Settled` ·
  `MM-0002,KOBO-001,2026-10-31T19:30:00+03:00,2026-10,C-0413,60.00,USD,Pending` ·
  `MM-0003,KISIWA-001,2026-10-12T10:00:00+03:00,2026-10,C-0901,55.00,USD,Settled`
- **expenses:** `FUEL-K-01,1,KOBO-001,2026-10-11T09:00:00+03:00,2026-10,Diesel,fuel-supplier,DN-311,400,500.00,USD,Invoiced` ·
  `OM-K-10,1,KOBO-001,2026-10-31T17:00:00+03:00,2026-10,O&M,om-contractor,INV-OM-10,,600.00,USD,Paid` ·
  `STAFF-K-10,1,KOBO-001,2026-10-31T17:00:00+03:00,2026-10,Salaries,payroll,PAY-10,,500.00,USD,Paid`
- **budget:** `KOBO-001-2026-10-revenue,1,KOBO-001,2026-10,revenue,3420.00,USD,budget-2026-v1` ·
  `KOBO-001-2026-10-billed_kwh,1,KOBO-001,2026-10,billed_kwh,8550,,budget-2026-v1` ·
  `ORG-2026-10-staff,1,,2026-10,staff,1200.00,USD,budget-2026-v1`

`backend/tests/source_contracts.py` (not collected): `ContractCase(reader_id, golden, expected, required_headers:
tuple[str, ...], amount_header: str, clock_header: str, bad_clock: str, revision_header: str | None, mapped: tuple[str,
str] | None, personal_raw: tuple[str, ...], scope: "SITE" | "ORGANISATION")` and `CONTRACT_CASES`, one per layout
(billing: required `Invoice no, Site, Billing month, Amount, Currency, Account`; amount `Amount`; clock `Period start`,
bad clock `01/10/2026`;
revision `Revision`; mapped none; raw `C-0412, C-0413, C-0901`; scope ORGANISATION — the same for the others with
their headers: collections clock `Paid at`, bad `2026-10-30T19:00:00`, mapped `("Status", "Lost")`, no revision, raw
the payers; expenses clock `Date`, bad `2026-10-11T09:00:00`, mapped `("Category", "Fuel")`, raw `payroll`; budget
amount `Value`, clock `Month`, bad `Oct-2026`, mapped `("Line", "marketing")`, raw none). `3A6` appends its profile cases here.

## 5. Tests

**Contracts, no database** (`contracts/tests/test_3a3_native_layouts.py`, run by T2's neutral guard):
1. Each golden reads to its expected records (dict equality) with rows `(2, 3, 4)` and no refusals; each expected list
   renders to the golden bytes.
2. Header refusals: reordered, renamed (`kwh`), extra column, missing column, empty file: `NATIVE_HEADER json`. A BOM
   is accepted; byte `0xFF` is `NATIVE_ENCODING`; a NUL byte is `NATIVE_ROW row.<n>`.
3. A row with one cell fewer is refused `NATIVE_ROW row.3` and the other rows stand; a blank row is skipped and row
   numbers stay physical.
4. Map miss: `Category` `Fuel` is `NATIVE_VALUE record.body.category`; budget `Line` `marketing` is `NATIVE_VALUE
   record.body.factor_id`.
5. Rule C: an expenses row with `Litres` blank has no `quantity`; with `Litres` set it has `{"value", "unit": "L"}`.
6. `render_layout` raises `NATIVE_RENDER` for a record whose constant differs, whose two `Account` paths differ, or
   whose value is not a string; each map is one to one (import check planted fails).

**Service, no database** (`backend/tests/test_3a3_source_contract.py`; 3A2's in-memory world: `UploadMemoryStore`,
`People`, key `bytes(range(32))`, `T_SUBMIT`), parametrised over `CONTRACT_CASES` (C) plus single tests:
- C1 Check, submit, accept (Fiona) on the case's scope: all rows NEW; `months == [(site, "2026-10") ...]`; the stored
  canonical records equal the expected records after 3A2's pseudonymisation (expected values pseudonymised in the
  test with the formula written out, as 3A2 svc 3b).
- C2 Kinds: every stored kind is in `SOURCE_TYPES[case source type].kinds`.
- C3 Required: blanking each required header's cell in row 2 refuses row 2 only, with 2a's code; the refusal `field`
  is that header and `text` reads `Row 2, <header>: <words>`.
- C4 Number: row 2's amount `12,5` is `CANONICAL_NUMBER`, field the amount header (budget: `Value`).
- C5 Clock: row 2's clock cell set to the case's `bad_clock` is `CANONICAL_CLOCK`, field the clock header.
- C6 Idempotency (DUP-1, CONF-1): resubmitting the golden is 422 `UPLOAD_NOTHING_NEW`; rows reversed: nothing new;
  row 2's amount changed with the same revision: that row `INTAKE_VERSION_CONFLICT`, nothing else new (so 422);
  with a revision header, the same change at revision 2 is REVISED.
- C7 Late record: the golden checked at `2026-11-06T09:00:00+00:00` names October only.
- C8 Native refusals on the service: a reordered header is 422 `UPLOAD_FILE_REFUSED` with `field` "the file"; the
  case's map miss is a row refusal with the header as `field`.
- C9 Personal data: no `personal_raw` string appears in any stored string (upload batch, refusal arrays, canonical,
  rejection) or any response.
- C10 Provenance: with `real_data=True` the case is 422 `UPLOAD_PROVENANCE_NOT_ALLOWED`.
- S1 Single writer (`backend/tests/test_3a3_single_writer.py`, AST scan of `backend/assetops_backend`, `tools`,
  `host`, `simulator`, `gateway`, `field`, tests excluded): `CommercialRecords(` only in `commercial/composition.py`;
  any `.ingest(` call in a module that imports from `assetops_backend.commercial` fails unless the module is
  `commercial/uploads.py`;
  `build_commercial_uploads(` only in `main.py` and `load_emulated_exports.py`; `build_commercial_records` exists
  nowhere.
- S2 `READERS` keys equal `{"canonical-json-v1"} | {c.reader_id for c in CONTRACT_CASES}`.
- S3 Every native code has its reason words; `LayoutReader.field_label` gives "row 7", "Amount", "the record", "the
  file" for `row.7`, `record.amount.value`, `record.kind`, `json`.
- S4 Cross-source link: billing and collections goldens accepted; the charge's `subject.ref` for `C-0412` equals the
  receipt's `payer_ref` (same pseudonym).
- S5 A reader refusal outside the record range is 500 `COMMERCIAL_STORE_FAULT` (a stub reader).

**Emulator, no database** (`simulator/tests/world/test_3a3_exports.py`; the manifest fixture of
`simulator/tests/world/conftest.py`). Expected figures are literals here, read by hand from the manifest (W2):
- E1 Files: `lakeside-power.billing.csv`, `.collections.csv`, `.expenses.csv`, `.budget.csv`; no cold or EV file;
  `NOT_ON_PATH_VERTICAL` for `harvest-cold` and `metro-bus`.
- E2 Charges: 40 per Site; amount sums KISIWA-001 4070.00, KOBO-001 3458.00, MTO-001 2160.00; kWh sums 7400, 8645,
  5400; KOBO-001 customers 1 to 5 have 217 kWh, 86.80.
- E3 Receipts: COLLECTED sums 3800.00, 3180.00, 1890.00; PAID_IN_TRANSIT 0, 0, 150.00; counts 38, 37, 38; KOBO-001's
  last receipt is customer 37's 67.60.
- E4 Fuel: litres 2400, 1180, 320; amounts 3120.00, 1475.00, 400.00; deliveries 6, 3, 1; KOBO-001 on days 1, 11, 21.
- E5 GAP-1: no KISIWA-001 `OM` expense, and `ESTIMATED_NOT_RECEIVED` for it in `unwritten`; KOBO-001 OM 600.00, MTO-001
  500.00; STAFF 500.00, 500.00, 450.00.
- E6 Budget: KOBO-001 `revenue` 3420.00, `fuel_cost` 875.00, `billed_kwh` 8550, `diesel_l` 700, `tariff` 0.40,
  `diesel_price` 1.25; KISIWA-001 `tariff` 0.55, `diesel_price` 1.30.
- E7 Round trip: each file reads (`read_layout`) back to its records with no refusal; two runs give identical bytes;
  the packet records each file's SHA-256 and the test pins them.
- E8 Planted manifest: revenue 3459.0 for Kobo raises `EMU_REVENUE`; `diesel_cost` 1476.0 raises `EMU_FUEL`.

**Loader, no database** (`backend/tests/test_3a3_load_emulated.py`, injected in-memory services):
- L1 `DATABASE_URL` names `assetops_op_pilot1`, `ASSETOPS_OP_X`, `assetops_opx`, and a URL with no database: each
  `EMULATED_ON_OPERATOR_DATABASE`, exit 2, and the injected services are never called (spies).
- L2 The emulator's records (`build_exports` on the fixture manifest) for KOBO-001 and KISIWA-001 only, rendered by
  the test with `render_layout` into `tmp_path/acme.<key>.csv`, load with `--tenant acme`, Ana submitting and Fiona
  accepting: four ACCEPTED uploads; a rerun prints `NOTHING_NEW` four times.
- L3 `EXPORT_FILE_UNKNOWN` (a `notes.txt`), `EXPORT_PATHS_MIXED` (`acme.budget.csv` with `acme.budget_workbook.json`),
  `PERSON_NOT_FOUND` (Hugo of beta), `PERSON_ROLE_REQUIRED` (Peter submitting).
- L4 A refused submission (a file with a reordered header) exits 3 after the earlier files were accepted.

**Postgres** (`backend/tests/test_3a3_load_emulated_postgres.py`, pooled `--db`, harness-routed `*_test` only):
- P1 Tenant `acme`, Sites KOBO-001 and KISIWA-001, Ana and Fiona created through the 3C0a service on the routed DB;
  the loader (composition path, `DATABASE_URL` the routed URL, key in `tmp_path`) loads L2's files: four uploads,
  four decisions, the store's `latest_revisions` count equals the files' Kobo and Kisiwa rows; a rerun writes nothing.
- P2 `onboard_person` round-trips roles and tenant slug.

**Regression beside them:** the 3A2 service, API and Postgres files (they must pass with `read(data, context=...)`),
`test_3a1_commercial_service.py`, `test_3c0a_accounts_service.py`, `simulator/tests/world/` (DS1b's), check-all.

## 6. Guard

No new guard. S1 is the class test for D-3A3.1. `tools/checks/configuration-persistence.ps1` is unchanged: the loader
and `world/exports.py` write no configuration (the tool writes only into its out directory, as DS1b's).

## 7. Done (questions; each can fail)

1. Do the four goldens read to their hand-written records and render back to the same bytes (contracts 1)?
2. Is every native problem refused in plain words at the right level: a bad file whole, a bad row alone (contracts
   2 to 4, C3 to C5, C8)?
3. Does every `READERS` entry other than the canonical one have a passing contract case, and does every case pass
   C1 to C10 (S2)?
4. Do the emulated files total exactly the manifest's October figures per Site, write nothing ESTIMATED, and read
   back with no refusal (E2 to E7)?
5. Is `CommercialRecords.ingest` reachable only through `CommercialUploads`, with `build_commercial_records` gone (S1)?
6. Does the loader refuse every `assetops_op*` name, any case, and an unnamed database, before any connection or
   service call (L1)?
7. Is the same customer one pseudonym across billing and collections, and is no raw customer or staff ref stored or
   answered (S4, C9)?
8. Does each planted violation in the reviewer guide fail its named test?
9. Is nothing changed beyond §3's files, the fixtures and tests of §4 and §5, `source_contracts.py`, and the packet?

Packet: `specs/3A3-emulators-contract-test/packet.md` (module paths, file SHA-256s, plants, mid-build count).

## 8. Units

| Unit | Content | Commit |
|---|---|---|
| 1 | `native/layouts_v1.py`, the four layouts, goldens, contracts tests | 1 |
| 0.75 | Reader seam (`ReadContext`, `refused`), `LayoutReader`, `READERS`, words, `build_commercial_records` deleted; `source_contracts.py`, C1 to C10, S1 to S5 | 2 |
| 0.75 | `world/exports.py`, the `exports` tool command, E1 to E8 | 3 |
| 0.5 | `onboard_person`, `refuse_operator_database`, the loader, L1 to L4, P1, P2; check-all; packet | 4 |

## 9. Out of scope

Source profiles as data, transforms (units, date formats, time zones, currency), composite keys, XLSX and operator
samples (`3A6`); history months and SETTLEMENT, meter-register and meter-read emulators (no path unit reads them;
`3A6` or `4a`); the reconciliation gate (`3A7`); a waiting list across Sites (D-3A3.8); any screen; creating any
database.

## 10. Decision queue (W3)

| # | Question | Default applied |
|---|---|---|
| Q1 | May the loader accept as the finance lead (`--accept-as`) on emulated data? | Yes, for emulated rehearsal and walkthrough tenants only (refused on operator databases, §2.6 step 2); the decision row names that person. **Owner to weigh in** if a person must click accept even in rehearsal |
| Q2 | The finance lead's one list of everything waiting across Sites | Later: with the upload list screen (next fortnight, with `3C0b`); a read `uploads_waiting(tenant_id, limit)` then. The rehearsal uses the loader's output and the organisation path (D-3A3.8) |
| Q3 | Budget lines at node level (`revenue`, `fuel_cost`, `billed_kwh`, `diesel_l`) are carried as the budget states them | Yes; `5a` rules how targets read them |
