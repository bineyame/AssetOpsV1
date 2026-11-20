# 3A6: source profiles as data (implementer spec)

Status: **spec rev 1, handshake open** (`handshake.md`). Questions during the build: `mid-build-questions.md`.
Reviewer: `reviewer-guide.md`. Decisions with reasons: `rulings.md` (D-3A6.1 to D-3A6.10).

Architect (Claude), 2026-11-20. Lane A (sources), the deep-dive path's unit 5 (`two-week-build-plan.md` §0.1 row 5;
D-BW1.8, D-BW1.11; owner RC2 "build 3A6; hand reshaping stays the fallback", RC4 real data only in its own database
after a signed DPA, RC5 mini-grid only: `owner/owner-recut-decisions-rc1-rc9-2026-11-20.md`).
- **Structure:** integration design `integration-source-to-canonical-design.md` §6.5 (idempotency key, row digest for
  sources without a version, source registration per tenant), §7.2 ("only transport and profile change"; profile =
  columns, units, timezone, mutability, personal-data fields; pinned against the sample) and §8 PII-1, SRC-1.
- **Builds on (merged, `main` e2387b334):** `3A3` (`assetops_contracts.native`: `Column`, `Layout`, `read_layout`,
  `render_layout`, `check_layout`, `LAYOUTS`; `commercial/readers.py`: `ReadContext`, `ReadResult`, `LayoutReader`,
  `READERS`; `CommercialUploads._check`, `.held`; `HeldUpload`; `load_emulated_exports.py`; `backend/tests/
  source_contracts.py`, `test_3a3_source_contract.py`, `test_3a3_single_writer.py`, `test_3a3_load_emulated.py`;
  D-3A3.2, D-3A3.5, D-3A3.7, D-3A3.9, D-3A3.10, D-3A3.12, D-3A3.14); `3A2` (`commercial/pseudonym.py`
  `ALLOWED_EXTRA`, `CLASSES`; `commercial/composition.py` `commercial_upload_settings`); `3C0a`/`3C1a`
  (`accounts/permissions.py` `COMMAND_ROLES`, `roles_of`; `AccountService.onboard_person`); `2a`
  (`parse_batch`, `SOURCE_TYPES`, `CanonicalRefused`).

Non-screen. **2.5 units, three commits.** Discovery review (W5): a new shared contract (the profile format), a new
table, a protected seam (what the intake admits), and the RC4 boundary (a real operator's sample).

## 0. Before you start

- **Branch** `task/3A6-source-profiles` off `main` after this spec branch merges; worktree
  `/opt/assetecon/AssetOpsV1-3a6`. Code starts when the handshake has no open question.
- **Python, PYTHONPATH, module-path record:** as 3A3 §0.
- **Read:** this spec and `rulings.md`; 3A3 `spec.md` §2.2 to §2.4, §2.6, §4, §5 and `rulings.md` D-3A3.9,
  D-3A3.10, D-3A3.12, D-3A3.14; `contracts/assetops_contracts/native/layouts_v1.py`; `commercial/readers.py`;
  `commercial/uploads.py` (`reader`, `_check`, `held`); `commercial/store.py`;
  `commercial/adapters/postgres_commercial_store.py` (`_HELD`, `add_upload`); `load_emulated_exports.py`;
  `backend/tests/source_contracts.py`; `test_3a3_source_contract.py` (the mutation helpers);
  `test_3a3_single_writer.py`; `backend/migrations/versions/0065_commercial_upload.py`.
- **Databases:** `*_test` only, through the harness; every Postgres run `tools/heavy-slot.sh --db -- <command>`. No
  real operator data anywhere (RC4): every sample and expected file in this unit is written by hand from this spec.
- **Migration** `0067_source_profile` (revises `0066_structure_snapshot`, `3B7a`). If `3B7a` has not merged when this
  branch merges, renumber at merge preparation (D-3A2.11's rule); tests read head and `down_revision` from the modules.
- **Collisions.** `3A7` (lane A, next) edits the same store, adapter, model, composition, `i18n/messages.py`,
  `accounts/permissions.py` and the persistence guard: it branches after this unit merges. `3B7a`, `5b` (lane B) read
  the commercial store only. `DDR` uses what this unit builds and changes none of it.

## 1. Outcome and why

An operator's own export (CSV, or an Excel workbook with one sheet) is read through a **source profile**: a JSON data
file that names the export's columns, the canonical paths each fills, how dates, times, months and numbers are written,
the time zone, the currency, how the record's ID and version are found, which columns are dropped (personal data the
canonical record does not carry), and which refs are personal. The analyst writes the profile and a few expected
records by hand from the operator's sample, then **admits** it with one command: the command reads the sample through
the profile, compares every record with the hand-written ones, and runs the contract probes (a reordered header refuses
the file; a short row, an invisible character, a value outside a map and a badly written date each refuse their row
alone). Only an admitted profile reads uploads, through 3A2's intake unchanged: dry run, plain refusals, pseudonymised
customer refs, a named person accepting. Onboarding a new export layout is a new profile file and one command: **no
code change**.

Why next: `DDR` must take "one export of a shape never seen before ... through a new profile with no code change";
without `3A6` an operator's file must be reshaped by hand into the illustrative template (RC2 keeps that as the
fallback). The four residuals queued to 3A6 are settled here (§2.8 to §2.11).

## 2. Rules

### 2.1 The profile file (D-3A6.1)

One JSON object, UTF-8, at most 64 KiB, **closed keys at every level** (an unknown or missing key is
`PROFILE_INVALID <where>`, `<where>` the dotted key path, list items by index: `columns.3.paths.0.type`):

| Key | Value |
|---|---|
| `schema` | exactly `"assetops.source-profile"` |
| `schema_version` | exactly `1` (JSON integer) |
| `profile_id` | `[a-z][a-z0-9-]{0,47}` |
| `status` | `"ILLUSTRATIVE"` (emulated data) or `"PINNED"` (an operator's real export) |
| `source_type` | a key of `SOURCE_TYPES` |
| `source_system` | `[a-z0-9][a-z0-9.-]{0,79}`, not starting `illustrative-` (those are the template's, D-3A3.10) |
| `file` | CSV: `{"format": "csv", "encoding": "utf-8" \| "cp1252", "delimiter": "," \| ";" \| "\t" \| "\|", "header_row": 1..20}`. XLSX: `{"format": "xlsx", "sheet": <1..31 characters>, "header_row": 1..20}` |
| `values` | `{"decimal_mark": "." \| ",", "thousands_mark": "" \| "," \| "." \| " " \| "'", "negative": "minus" \| "parentheses", "date_format": <DATE_FORMATS>, "time_format": "HH:MM" \| "HH:MM:SS", "month_format": <MONTH_FORMATS>, "timezone": <IANA name ZoneInfo loads>}`; `thousands_mark != decimal_mark` |
| `version` | `{"from": "constant", "value": <1..40 characters, no control>}`, `{"from": "column"}` (exactly one column writes `source_version`) or `{"from": "row_digest"}` |
| `record_id_join` | optional list of 2 to 4 distinct headers; when present no column writes `source_record_id`; when absent exactly one column does |
| `columns` | 1 to 60 objects `{"header": <1..100 characters, no control, unique>, "paths": [<path object>, ...]}`; `paths: []` is a **dropped** column (read for the header match, never written) |
| path object | `{"path": <canonical path>, "type": "text" \| "number" \| "date" \| "datetime" \| "month" \| "month_of", "map": {<native>: <canonical>}?, "scale": <decimal text>?}`; `map` only with type `text`; `scale` only with type `number` |
| `constants` | `{<canonical path>: <string>}` (rule C of 3A3 §2.2 applies) |
| `personal` | list of `[<path>, "C" \| "M" \| "P"]`, each path in 3A2's `ALLOWED_EXTRA` (checked in the backend, §2.5) |

A canonical path is one of 3A3 §2.2's forms. A path may be written by one column or constant only
(`PROFILE_INVALID <where>` naming the second writer). `DATE_FORMATS = ("YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY",
"DD-MM-YYYY", "DD.MM.YYYY", "YYYY/MM/DD")` (DD and MM one or two digits, YYYY four). `MONTH_FORMATS = ("YYYY-MM",
"MM/YYYY", "YYYYMM", "Mon-YYYY", "Month YYYY")` (`Mon` `Jan` to `Dec`, `Month` `January` to `December`, English,
first letter capital, the rest lower case).

**Coded paths (D-3A6.6).** `CODED_PATHS = frozenset({"kind", "status", "subject.kind", "quantity.unit",
"body.line_type", "body.tariff_class", "body.method", "body.category", "body.direction", "body.read_type",
"body.contract_type", "body.factor_id"})`, in `native/layouts_v1.py`. A column path in `CODED_PATHS` must carry a
`map`; a `map` is allowed only on a coded path. `check_layout` enforces both for **every** layout, the four
illustrative ones included (they pass: their maps are on `status`, `body.category` and `body.factor_id` only, and no
column of theirs writes another coded path), raising `NATIVE_LAYOUT <id> <path>`.

`compile_profile(obj, version: int) -> Layout` in new `contracts/assetops_contracts/native/profiles_v1.py` (standard
library, `assetops_contracts.canonical`, `native.layouts_v1` only; re-exported from `native/__init__.py` with
`ProfileInvalid`, `reader_id_for`). `ProfileInvalid(where)` is a `ValueError` subclass whose `str` is
`PROFILE_INVALID <where>`. The Layout's `id` is `reader_id_for(profile_id, version) = f"profile.{profile_id}.v{version}"`.
`version` is 1 to 9999. `constants` of the version rule: `{"from": "constant"}` adds `source_version` to `constants`.

### 2.2 The engine grows, its contract does not change (D-3A6.1, amends D-3A3.2)

`layouts_v1.py` gains, all with defaults that reproduce today's behaviour exactly:

```python
@dataclass(frozen=True)
class FileRules:
    format: str = "csv"            # "csv" | "xlsx"
    encoding: str = "utf-8"        # csv only
    delimiter: str = ","           # csv only
    header_row: int = 1
    sheet: str | None = None       # xlsx only

@dataclass(frozen=True)
class ValueRules:
    decimal_mark: str = "."
    thousands_mark: str = ""
    negative: str = "minus"
    date_format: str = "YYYY-MM-DD"
    time_format: str = "HH:MM:SS"
    month_format: str = "YYYY-MM"
    timezone: str = "UTC"

Column   gains  types: Mapping[str, str] = _EMPTY    # path -> type; absent = "text"
                scales: Mapping[str, str] = _EMPTY   # path -> exact decimal multiplier
Layout   gains  file: FileRules = FileRules()
                values: ValueRules = ValueRules()
                record_id_join: tuple[str, ...] = ()
                version_digest: bool = False
```

`read_layout(layout, data, *, tenant_code, produced_at, provenance)` keeps its signature and result. It becomes
`split_file(layout, data) -> (header: list[str], rows: list[tuple[int, list[str]]])` then `read_rows(layout, header,
rows, *, tenant_code, produced_at, provenance) -> NativeRead`; both public (the admission probes call `read_rows`).

**`split_file`:**
1. CSV: a leading UTF-8 BOM is dropped only when `encoding` is `utf-8`; decode strict with `encoding`, else
   `CanonicalRefused("NATIVE_ENCODING", "json")`; `csv.reader(io.StringIO(text, newline=""), dialect="excel",
   delimiter=file.delimiter, strict=True)`; a `csv.Error` is `NATIVE_ROW row.<line_num>` (file refused). Row numbers as
   3A3 (physical line on which the row ends).
2. XLSX: `xlsx_rows(data, sheet)` (§2.3); row numbers are the sheet's `r`.
3. The header is the `header_row`-th row the reader returns, counting empty rows (CSV) or the row whose number is
   `header_row` (XLSX; absent is an empty header). Rows before it are skipped whatever they hold. A missing header or
   one not equal to `[c.header for c in layout.columns]` is `NATIVE_HEADER json` (XLSX: trailing empty cells of the
   header row are dropped before comparing).
4. Data rows: every later row; a row with no cells, or (XLSX) whose cells are all empty, is skipped. XLSX rows are
   padded with `""` to the header's length; an XLSX row with a non-empty cell beyond the header's length is refused
   `NATIVE_ROW row.<n>` (by `read_rows`, as a count mismatch).

**`read_rows`** applies 3A3 §2.2 steps 4 to 7, with these changes, in this order per row:
- Count mismatch: `NATIVE_ROW row.<n>` (unchanged).
- **Invisible characters (D-3A6.4, amends D-3A3.9):** a cell of a column with at least one path holding a character
  `ch` with `ord(ch) in _CONTROL` (3A3's set) or `unicodedata.category(ch) in {"Cc", "Cf", "Zl", "Zp", "Cs"}`, tab, LF
  and CR excepted, refuses the row `NATIVE_CHARACTER row.<n>`. Dropped columns are not checked.
- Each column path, cell not `""`: map (miss: `NATIVE_VALUE record.<path>`, first miss only, unchanged), else the
  type's transform (§2.4; failure: `NATIVE_FORMAT record.<path>`, first failure only, after maps), else the cell.
  A row with a map miss is refused `NATIVE_VALUE` even if a transform also fails.
- **Join (record ID):** with `record_id_join`, `source_record_id = ":".join(v)` where `v` is, for each named header in
  the given order, the value its column wrote to its **first path**; when any is absent, nothing is written (2a then
  refuses the record).
- **Row digest:** with `version_digest`, `source_version = "r" + sha256("\x1f".join(w).encode("utf-8")).hexdigest()[:16]`,
  where `w` is, for each column with at least one path in header order, the value written to its first path, or `""`
  when none (§6.5's "digest of the normalised row").
- Rule C constants, then the record, as 3A3.

`render_layout` raises `ValueError("NATIVE_RENDER <id> profile")` for a layout whose `file`, `values`,
`record_id_join`, `version_digest`, `types` or `scales` differ from the defaults (emulators render the illustrative
layouts only). `LayoutReader.media_types` is `{"text/csv"}` for CSV and
`{"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}` for XLSX.

The four illustrative layouts, their goldens and 3A3's E7 SHA-256 pins must not move (done criterion 1).

### 2.3 Single-sheet XLSX, standard library only (D-3A6.9)

`contracts/assetops_contracts/native/xlsx.py`: `xlsx_rows(data: bytes, sheet: str) -> list[tuple[int, list[str]]]`,
`XlsxNumber(str)` (a marker subclass for numeric cells). `zipfile` and `xml.etree.ElementTree` only. File refusals
(`CanonicalRefused(<code>, "json")`):
- `NATIVE_WORKBOOK`: not a zip; a member's declared uncompressed size over 16 MiB or a total over 64 MiB; a member
  `xl/workbook.xml`, `xl/_rels/workbook.xml.rels` or the sheet's target missing; any read member containing `<!DOCTYPE`
  or `<!ENTITY`; XML that does not parse; `workbookPr` with `date1904` true (`"1"` or `"true"`).
- `NATIVE_SHEET`: the workbook does not hold exactly one `<sheet>` element, or its `name` is not `sheet`.

Cells: `<c r="B7" t="...">`. Column index from the letters of `r` (`A` = 0; a cell without `r` takes the next index).
`t="s"`: shared string `int(v)` (`<si>` text: its `<t>`, or its `<r><t>` runs concatenated); `t="inlineStr"`: the `<is>`
text, same rule; `t="str"`: the `<v>` text; `t="b"`: `"TRUE"` or `"FALSE"`; `t` absent or `"n"`: an `XlsxNumber` of
`format(Context(prec=15, rounding=ROUND_HALF_EVEN).plus(Decimal(v)).normalize(...), "f")` (Excel's 15 significant
digits: `874.99999999999989` reads `875`, `3420` reads `3420`); `t="e"` or `t="d"`, or a `<v>` that is not a decimal:
the row is refused `NATIVE_FORMAT row.<n>` (the reader marks it; `read_rows` carries the refusal). A `<row>` without
`r` takes the previous row's number plus one. The character rule of §2.2 applies to every text cell.

### 2.4 Transforms (exact)

All produce the canonical text 2a judges; none rounds.
- **number**: the cell, stripped of nothing, must fullmatch `S? I F?` where `I` is `[0-9]+` when `thousands_mark` is
  `""`, else `[0-9]+` or `[0-9]{1,3}(T[0-9]{3})+` (`T` the mark, escaped), `F` is `D[0-9]+` (`D` the decimal mark),
  and the sign `S` is `-` for `negative: "minus"`; for `"parentheses"` the whole is `(` `I F?` `)` for a negative. Output:
  `-` when negative, the integer digits with the marks removed and leading zeros dropped (`0` kept alone), then `.`
  and the fraction digits when present. An `XlsxNumber` cell skips the grammar (it is already plain). With `scale`,
  the output is `format(Decimal(out) * Decimal(scale), "f")` under `Context(prec=60, traps=[Inexact, Rounded,
  InvalidOperation])`.
- **date**: the cell fullmatches `date_format` and is a calendar date, out `YYYY-MM-DD`. An `XlsxNumber` is a serial:
  its integer part `k` ≥ 1, `date(1899, 12, 30) + timedelta(days=k)`.
- **datetime**: a cell that fullmatches 2a's instant pattern (with `Z` or an offset) is kept unchanged. Else it must
  fullmatch `date_format + " " + time_format`; the naive time is placed in `ZoneInfo(timezone)` (`fold=0`); a local
  time that does not exist there (the UTC round trip differs) fails. Out `isoformat()` (`2026-10-11T09:00:00+03:00`).
  An `XlsxNumber` is a serial: date as above plus `round(fraction × 86400)` seconds, then placed in the zone.
- **month**: the cell fullmatches `month_format`, out `YYYY-MM`. An `XlsxNumber` is a serial date; out its month.
- **month_of**: the cell read as **datetime** (any branch above), else as **date**; out the month of the local date
  (an instant with an offset is first converted to `timezone`).

### 2.5 Admission: the contract test as product code (D-3A6.2, D-3A6.3)

New `backend/assetops_backend/commercial/profiles.py`:

```python
@dataclass(frozen=True)
class ProfileRow:            # in commercial/model.py; every column of commercial_source_profile
    profile_row_id: UUID; tenant_id: UUID; profile_id: str; version: int; reader: str; status: str
    source_type: str; source_system: str; file_format: str; profile_json: str; profile_sha256: str
    sample_sha256: str; expected_sha256: str; sample_rows: int; admitted_at: datetime
    admitted_by: UUID; admitted_role: str

class ProfileRefused(Exception):  # code, params: dict[str, str]; words via message(f"source_profile.{code.lower()}")

class SourceProfiles:
    def __init__(self, store: CommercialStore, *, clock, real_data: bool) -> None
    def check(self, tenant_id, profile: bytes, sample: bytes, expected: bytes) -> AdmissionReport   # no write
    def admit(self, tenant_id, actor: Actor, profile: bytes, sample: bytes, expected: bytes) -> ProfileRow
    def reader(self, tenant_id, reader_id: str) -> LayoutReader          # raises UploadRefused (below)
    def latest(self, tenant_id) -> tuple[ProfileRow, ...]
```

`AdmissionReport(profile_id, version, reader, source_type, source_system, sample_rows, profile_sha256, sample_sha256,
expected_sha256, already: ProfileRow | None)`. `check` and `admit` run the same steps; the first failure raises
`ProfileRefused(code, params)`:

1. **Profile.** `json.loads` of the UTF-8 bytes (≤ 64 KiB) to an object, else `PROFILE_INVALID {where: "json"}`;
   `compile_profile` (its `ProfileInvalid(where)` is `PROFILE_INVALID {where}`); each `personal` path in
   `ALLOWED_EXTRA` and class in `CLASSES`, else `PROFILE_INVALID {where: "personal.<i>"}`.
2. **Status.** `PINNED` when the service runs with `real_data`, `ILLUSTRATIVE` otherwise, else `PROFILE_STATUS`.
3. **Lineage and version.** `rows = store.source_profiles_all(tenant_id, profile_id)` (every version). If one has
   `profile_sha256` equal to the file's: `already` is that row (`admit` returns it, writes nothing; the command says
   `ALREADY_ADMITTED`). Else a row whose `source_type` or `source_system` differs from the file's is
   `PROFILE_LINEAGE`; `version = max(versions) + 1` or 1. Another `profile_id` of the tenant whose latest row has the
   same `source_system` is `PROFILE_SOURCE_SYSTEM_TAKEN {system}`.
4. **Sample.** At most 1 MiB. `reader = LayoutReader(compile_profile(obj, version))`; `read = reader.read(sample,
   context=ReadContext(slug, clock(), real_data))` (`slug = store.tenant_slug(tenant_id)`; None is
   `UPLOAD_TENANT_MISMATCH` as 3A3); a `CanonicalRefused` is `ADMIT_SAMPLE_FILE {code}`; data rows (records) must be 3
   to 200, else `ADMIT_SAMPLE_SIZE {rows}`; `parse_batch(read.obj)`; the first index (file order) refused by the reader
   or by 2a is `ADMIT_SAMPLE_ROW {row, code, path}` (`row` from `read.rows`, path cut by `cut_path`).
5. **Expected.** `json.loads` of the UTF-8 expected bytes to a list of objects, else `ADMIT_EXPECTED_FILE`; its
   length must equal the records' (`ADMIT_EXPECTED_COUNT {expected, records}`); record `i` (the reader's object, before
   pseudonymisation) must equal item `i` exactly, else `ADMIT_EXPECTED {row, where}` with `where` the first differing
   dotted path in sorted-key walk order (`record` when the types differ).
6. **Probes**, `run_probes(layout, header, rows, *, read=read_rows)` (public; each probe mutates a copy of
   `split_file`'s rows and calls `read`; `first` = the first data row; the check after
   each: the number of records equals the number of data rows, and only the named row is refused, with the named code;
   otherwise `ADMIT_PROBE {probe, where}`):
   - `P1 header`: the first two header cells swapped: `read_rows` raises `NATIVE_HEADER` (`where` "file").
   - `P2 short`: `first` without its last cell: `NATIVE_ROW` on `first` alone.
   - `P3 invisible`: for each of `"\x00"`, `"\x85"`, `"​"`, `"﻿"`, `" "`: appended to `first`'s cell of
     the first column with a path: `NATIVE_CHARACTER` on `first` alone.
   - `P4 coded`: for each column with a map, the first row whose cell there is non-empty, the cell set to
     `cell + " ?"`: `NATIVE_VALUE` on that row alone (`where` the header).
   - `P5 format`: for each column path of type other than `text`, the first row whose cell there is non-empty, the
     cell set to `"?"` (a plain `str`): `NATIVE_FORMAT` on that row alone (`where` the header).
   - `P6 blank`: for each column with a path, the first row whose cell there is non-empty, the cell set to `""`: that
     row is refused by the reader or by 2a, or its record holds none of the column's paths (no value is invented).
7. **Write** (`admit` only): `store.add_source_profile(ProfileRow(...))` with `profile_json` the profile bytes decoded,
   `admitted_role` the actor's role; a unique violation is `PROFILE_ALREADY_ADMITTED`. Nothing of the sample or the
   expected file is kept but their SHA-256 and the row count (RC4).

**Reading uploads** (`reader`): `reader_id` must fullmatch `profile\.([a-z][a-z0-9-]{0,47})\.v([1-9][0-9]{0,3})`,
else `UploadRefused(422, "UPLOAD_READER_UNKNOWN")`; the latest row of that profile (`store.source_profile_latest`)
None is `UPLOAD_READER_UNKNOWN`; a lower version than the latest is `UploadRefused(422, "UPLOAD_READER_SUPERSEDED",
{"latest": <reader>})`; `sha256(profile_json)` differing from `profile_sha256` is 500 `COMMERCIAL_STORE_FAULT`; then
`LayoutReader(compile_profile(json.loads(profile_json), version))` with `layout.personal` from the profile.

### 2.6 The intake (3A2 code; D-3A6.5, D-3A6.8)

- `CommercialUploads.__init__` gains `profiles: SourceProfiles | None = None` (keyword). `reader` becomes an
  instance method `reader(self, tenant_id, reader_id, media_type)`: `READERS` first; else `self._profiles.reader(...)`
  when `profiles` is set and the ID starts `profile.`; else `UPLOAD_READER_UNKNOWN`; then the media type (415) as
  today. `_check` calls `self.reader(tenant_id, ...)`. The route (`commercial_upload_api.py:168`) calls
  `await run_in_threadpool(uploads.reader, tenant_id, reader_id, media_type)` inside its existing `try`.
- **One source system per source type per Site (D-3A6.5).** In `_check`, after the kept indexes are known and before
  the dry-run ingest: `sites = {raw_records[i].get("site_code") for i in kept}`; for each `h` in
  `self._store.held_uploads(tenant_id)` with `h.source_type == batch.source_type`, `h.source_system !=
  batch.source_system` and `set(h.site_codes) & sites`: `UploadRefused(409, "UPLOAD_SOURCE_SWITCHED",
  {"source_type": ..., "system": <the first such h.source_system, sorted>})`. `None` (portfolio level) is a Site key
  like any other.
- `HeldUpload` gains `source_system: str` and `site_codes: tuple[str | None, ...]` (distinct `month_site_code`
  values, `None` first then sorted); `_HELD` and the memory mirror select them.
- `build_commercial_uploads` builds `SourceProfiles(store, clock=..., real_data=settings.real_data)` and passes it.
  New `build_source_profiles(database_url) -> (SourceProfiles, dispose)` for the command (same settings path).

### 2.7 The command (D-3A6.10)

`python -m assetops_backend.source_profile {check,admit,list} --tenant SLUG ...`; `build_parser()` public.
- `check --profile P --sample S --expected E`: steps 1 to 6. Out one JSON line `{"state": "ADMISSIBLE", "reader",
  "version", "sample_rows", "profile_sha256", "sample_sha256", "expected_sha256"}` (or `"ALREADY_ADMITTED"`) exit 0;
  a `ProfileRefused` prints `{"state": "REFUSED", "code", "params", "text"}`, exit 3.
- `admit ... --as EMAIL`: the person as 3A3 §2.6 step 5 (`PERSON_NOT_FOUND`, `PERSON_ROLE_REQUIRED` against
  `roles_of("commercial.profile_admit")`, new command key `(ANALYST, FINANCE)` in `COMMAND_ROLES`), exit 2; then
  `admit`: `{"state": "ADMITTED" | "ALREADY_ADMITTED", "reader", "version", ...}` exit 0, or REFUSED exit 3.
- `list`: one line per latest profile `{"profile_id", "reader", "status", "source_type", "source_system",
  "admitted_at", "admitted_by"}`, by `profile_id`.
- Before any connection: `DATABASE_URL` unset `DATABASE_URL_REQUIRED`; `commercial_upload_settings(url)` (a
  `ConfigurationError` is `CONFIGURATION <message>`), exit 2. Files unreadable (not a regular file) `FILE_UNREADABLE
  <arg>`, exit 2. Operator databases are **not** refused here: a pinned profile is admitted where its real data lives
  (RC4); the settings switch already refuses a real-data run on a non-operator database and the reverse.

### 2.8 The loader takes admitted profiles (D-3A6.10, amends D-3A3.7 and D-3A3.14)

`load_emulated_exports.py`:
- Step 4 also admits `<SLUG>.profile.<profile_id>.csv` and `.xlsx`. Step 5c (after the people): each such file
  resolves to the tenant's latest admitted reader for `profile_id` (`profiles.latest`), else `PROFILE_NOT_ADMITTED
  <name>`, exit 2; its media type follows the profile's format. Order: CSVs in `KEYS` order, then profile files by
  name, then JSONs by name.
- In-directory: two files of one **source type** (whatever their readers) are `EXPORT_PATHS_MIXED <source_type>`.
- Across runs (step 5b): a file of source type `t` and source system `s` (a layout reader's `layout.source_system`;
  a JSON batch's top-level `source_system`, read with `json.loads`; unreadable JSON is left to the submission) when
  `held` has an upload of type `t` with another source system is `EXPORT_PATH_SWITCHED <t>`, exit 2. (The loader takes
  whole-tenant directories, so it does not narrow by Site; the intake's rule of §2.6 is the authority.)
- `main(argv, *, uploads=None, accounts=None, profiles=None)`.

### 2.9 S1 reaches dynamic imports and names built from strings (D-3A6.7, amends D-3A3.12)

`test_3a3_single_writer.py` (renamed nothing; extended), roots gain `contracts/assetops_contracts`:
- **Dynamic import:** a call to `importlib.import_module`, `importlib.reload`, `importlib.util.find_spec`,
  `importlib.util.spec_from_file_location`, `importlib.util.module_from_spec` or `__import__` (however `importlib` is
  imported or aliased) in a module outside `DYNAMIC_IMPORT_ALLOWED` fails. `DYNAMIC_IMPORT_ALLOWED` is exactly the
  set the scan finds on `main` at branch time; at `e2387b334` it is `backend/assetops_backend/chain/adapters/
  file_chain_config.py`, `backend/assetops_backend/chain/adapters/file_inputs.py`, `tools/mechanism_dataset.py`,
  `tools/checks/import_root_probe.py`, `tools/checks/neutral_tests.py`, `tools/validate-test-selection.py`,
  `tools/checks/test_event_register.py`, `host/conftest.py` (if the scan excludes it as a test file, drop it), each
  with a one-line reason in the test.
- **Anywhere** (allowlisted modules too): such a call whose first argument is a string constant beginning
  `assetops_backend.commercial` or containing `/commercial/` fails.
- **Names from strings:** outside `INGEST_ALLOWED | IMPORT_ALLOWED`, any string constant equal to `"ingest"` or
  `"CommercialRecords"` fails. In a module that imports from the commercial package (except `INGEST_ALLOWED`): a
  `getattr`, `setattr`, `hasattr` or `delattr` whose name argument is not a string constant, and any use of
  `operator.attrgetter` or `operator.methodcaller` (also when imported by name), fail.
- **No code in data:** a call to `eval`, `exec` or `compile` in `backend/assetops_backend/commercial/` or
  `contracts/assetops_contracts/native/` fails.
- `PLANTED` gains five sources, each must fail: `importlib.import_module("assetops_backend.commercial.service")`;
  `m = __import__(name)` (module not allowlisted); `getattr(svc, "in" + "gest")(b)` in a module importing
  `assetops_backend.commercial.uploads`; `operator.methodcaller("ingest")(svc)`; `eval("svc")` under
  `backend/assetops_backend/commercial/`.
- Still not seen (residual, packet): a module that imports nothing commercial and calls `.ingest` on a service it is
  handed (ten `.ingest` attributes of other services exist; review covers it).

### 2.10 The contract suite derives what it probes (D-3A6.6)

`backend/tests/source_contracts.py`:
- `ContractCase.mapped` is replaced by `coded: tuple[tuple[str, str], ...]` (header, a value outside its map). The
  suite computes, from a hand-written `CODED_PATHS_EXPECTED` (the same twelve paths, written in the test file, not
  imported) and the reader's layout, the set of headers whose column writes a coded path, and asserts it equals
  `{h for h, _ in case.coded}`. So a layout that writes a coded path without declaring a map fails the suite (and
  `check_layout`), and billing's `coded=()` is now derived, not declared.
- Cases change exactly: billing `coded=()`; collections `(("Status", "Lost"),)`; expenses `(("Category", "Fuel"),
  ("Status", "Draft"))`; budget `(("Line", "marketing"),)`. C8's map-miss check runs for every pair.
- New fields with defaults: `encoding="utf-8"`, `delimiter=","`, `header_row=1`, `line_end="\n"`,
  `bad_number=("12,5", "CANONICAL_NUMBER")`, `bad_clock_code="CANONICAL_CLOCK"`, `versioning="column"` (`"column"`,
  `"constant"` or `"digest"`; billing, expenses and budget `"column"`, collections `"constant"`), `profile: Path |
  None = None`. The suite's mutation helpers read and write the golden with the case's encoding, delimiter, header row
  and line end (`csv` module, `lineterminator=line_end`). "Row 2" and "row 3" in C3 to C8 mean the first and second
  **data** rows (lines `header_row + 1` and `+ 2`); expected fields and texts name their physical row numbers (the
  profile case: `Row 4, ...`). C4 uses `bad_number`; C5 expects `bad_clock_code`. C6 for
  `"digest"`: the changed amount is `REVISED` (a new digest), not a conflict.
- `PROFILE_CASES` (one case, §4.1) is appended to the parametrisation; a profile case is admitted into the test's
  in-memory store by `SourceProfiles.admit` before C1 (C10's real-data half admits a copy whose `status` is `PINNED`).
  S2 is unchanged (static `READERS` against the static cases).

### 2.11 Words (`i18n/messages.py`, a `# 3A6` block)

| Key | English |
|---|---|
| `commercial_upload.reason.native_format` | this value is not written the way this layout reads it (for example, a date in another order). |
| `commercial_upload.reason.native_workbook` | this is not an Excel workbook this layout can read. |
| `commercial_upload.reason.native_sheet` | the workbook must hold exactly one sheet, with the sheet name this layout reads. |
| `commercial_upload.reason.native_character` (changed) | this row holds a character that is not text (such as a NUL byte or an invisible mark). |
| `commercial_upload.reader_superseded` | That file layout has a newer version: use {latest}. |
| `commercial_upload.source_switched` | These Sites already send this kind of export from another system ({system}). Use that system's export, or ask for the switch to be set up. |
| `source_profile.profile_invalid` | The profile is not valid at {where}. |
| `source_profile.profile_status` | A profile for an operator's real export must be PINNED; one for emulated data, ILLUSTRATIVE. |
| `source_profile.profile_lineage` | A new version cannot change the source type or the source system. Give it a new profile name. |
| `source_profile.profile_source_system_taken` | Another profile already reads the source system {system}. |
| `source_profile.profile_already_admitted` | This profile is already admitted. |
| `source_profile.upload_tenant_mismatch` | This organisation is not known here. |
| `source_profile.admit_sample_file` | The sample cannot be read: {reason} |
| `source_profile.admit_sample_size` | The sample must hold 3 to 200 rows; it holds {rows}. |
| `source_profile.admit_sample_row` | Row {row} of the sample is refused: {reason} |
| `source_profile.admit_expected_file` | The expected records must be a JSON list of records. |
| `source_profile.admit_expected_count` | The expected file holds {expected} records; the sample gives {records}. |
| `source_profile.admit_expected` | Row {row} does not read as its expected record: {where} differs. |
| `source_profile.admit_probe` | The profile does not refuse what it must ({probe}, {where}). |

`{reason}` is `render(reason_words(code))`. `_WORDS` in `uploads.py` gains `UPLOAD_READER_SUPERSEDED`,
`UPLOAD_SOURCE_SWITCHED`.

## 3. Code

| File | Holds |
|---|---|
| `contracts/assetops_contracts/native/layouts_v1.py` | `FileRules`, `ValueRules`, new fields, `CODED_PATHS`, `split_file`, `read_rows`, transforms, join, digest, the invisible rule, `render_layout`'s refusal, `check_layout`'s coded rule |
| `contracts/assetops_contracts/native/xlsx.py`, `profiles_v1.py`, `__init__.py` | §2.3, §2.1 |
| `backend/migrations/versions/0067_source_profile.py` | §5 |
| `backend/assetops_backend/commercial/model.py`, `store.py`, `adapters/postgres_commercial_store.py` | `ProfileRow`; `source_profiles_all`, `source_profile_latest`, `source_profiles_latest`, `add_source_profile`; `HeldUpload` fields |
| `backend/assetops_backend/commercial/profiles.py` | §2.5 |
| `backend/assetops_backend/commercial/readers.py` | media types by format |
| `backend/assetops_backend/commercial/uploads.py`, `commercial_upload_api.py` | §2.6 |
| `backend/assetops_backend/commercial/composition.py` | `build_commercial_uploads` passes profiles; `build_source_profiles` |
| `backend/assetops_backend/source_profile.py` | §2.7 |
| `backend/assetops_backend/load_emulated_exports.py` | §2.8 |
| `backend/assetops_backend/accounts/permissions.py` | `"commercial.profile_admit": (ANALYST, FINANCE)` |
| `backend/assetops_backend/i18n/messages.py` | §2.11 |
| `tools/checks/configuration-persistence.ps1` | `commercial_source_profile` joins `$commercialTables` (same writer, same plain-INSERT shape) |
| `.gitattributes` | `backend/tests/fixtures/3a6/* -text` (byte-pinned: CRLF and cp1252 kept) |

## 4. Fixtures (hand-written; never produced by the code under test, W2)

### 4.1 `backend/tests/fixtures/3a6/kobo-ledger-expenses.*` (CSV, cp1252, `;`, CRLF, header on row 3)

`kobo-ledger-expenses.csv`, exactly these lines, each ended by CR LF, encoded cp1252 (the `–` on line 1 is byte
`0x96`):
```
Lakeside Power Ltd – Purchases ledger;;;;;;;;
Exported 06/11/2026 09:12;;;;;;;;
Ref;Txn Date;Site;Account;Supplier;Phone;Litres;Net (USD);State
PL-1001;11/10/2026 09:00;KOBO-001;Diesel;fuel-co;0712000001;400;500,00;Invoiced
PL-1002;21/10/2026 09:00;KOBO-001;Diesel;fuel-co;0712000001;380;475,00;Paid
PL-1003;31/10/2026 17:00;KOBO-001;Repairs & maintenance;om-contractor;;;1.200,00;Paid
PL-1004;31/10/2026 17:30;KOBO-001;Wages;STAFF-07;0712000777;;450,00;Paid
```
`kobo-ledger-expenses.profile.json`: `profile_id` `kobo-ledger-expenses`, `status` ILLUSTRATIVE, `source_type`
`expense_ledger`, `source_system` `lakeside-purchases-ledger`, `file` csv cp1252 `;` header_row 3, `values` decimal
`,` thousands `.` negative minus, `DD/MM/YYYY`, `HH:MM`, `YYYY-MM`, `Africa/Nairobi`; `version` constant `"1"`; no
join; columns: `Ref` → `source_record_id`, `body.document_ref` · `Txn Date` → `clocks.occurred_at` (datetime),
`clocks.recognition_period` (month_of) · `Site` → `site_code`, `subject.ref` · `Account` → `body.category` map
`{"Diesel": "FUEL", "Repairs & maintenance": "OM", "Wages": "STAFF"}` · `Supplier` → `body.counterparty_ref` ·
`Phone` → dropped · `Litres` → `quantity.value` (number) · `Net (USD)` → `amount.value` (number) · `State` → `status`
map `{"Invoiced": "INVOICED", "Paid": "PAID", "Quote": "QUOTE"}`; constants `kind` EXPENSE, `subject.kind` SITE,
`quantity.unit` L, `amount.currency` USD; `personal` `[]`.

`kobo-ledger-expenses.expected.json`, in order (every record `format_version` 1, `source_version` "1", `site_code`
KOBO-001, `kind` EXPENSE, `subject` `{"kind": "SITE", "ref": "KOBO-001"}`, `amount.currency` USD):

| ID (= `document_ref`) | `occurred_at` | period | status | category | counterparty | amount | quantity |
|---|---|---|---|---|---|---|---|
| PL-1001 | 2026-10-11T09:00:00+03:00 | 2026-10 | INVOICED | FUEL | fuel-co | 500.00 | 400 L |
| PL-1002 | 2026-10-21T09:00:00+03:00 | 2026-10 | PAID | FUEL | fuel-co | 475.00 | 380 L |
| PL-1003 | 2026-10-31T17:00:00+03:00 | 2026-10 | PAID | OM | om-contractor | 1200.00 | (none) |
| PL-1004 | 2026-10-31T17:30:00+03:00 | 2026-10 | PAID | STAFF | STAFF-07 | 450.00 | (none) |

Rows `(4, 5, 6, 7)`. Its `PROFILE_CASES` entry: `required_headers` all but `Phone`; amount `Net (USD)`; clock `Txn
Date`, bad clock `2026-10-11 09:00`, `bad_clock_code` `NATIVE_FORMAT`; `bad_number=("12.5", "NATIVE_FORMAT")`;
`versioning="constant"`; `coded=(("Account", "Fuel"), ("State", "Draft"))`; `personal_raw=("STAFF-07", "0712000001",
"0712000777")`; `encoding="cp1252"`, `delimiter=";"`, `header_row=3`, `line_end="\r\n"`.

### 4.2 `backend/tests/fixtures/3a6/lakeside-budget.*` (XLSX, one sheet `Budget 2026`)

`make_budget_xlsx.py` (in the fixtures folder; standard library; `build_workbook(rows) -> bytes` and `main()` that
writes `lakeside-budget.xlsx`): a zip with every entry dated 1980-01-01 00:00:00, `ZIP_DEFLATED`, entries in this
order: `[Content_Types].xml`, `_rels/.rels`, `xl/workbook.xml` (one `<sheet name="Budget 2026" sheetId="1"
r:id="rId1"/>`), `xl/_rels/workbook.xml.rels` (`rId1` → `worksheets/sheet1.xml`), `xl/worksheets/sheet1.xml`. Text
cells are `t="inlineStr"`; numbers have no `t`. Rows (`r` 1 to 4):

| r | A | B | C | D | E |
|---|---|---|---|---|---|
| 1 | Site | Month | Line | Amount | Currency |
| 2 | KOBO-001 | Oct-2026 | Revenue | `3420` | USD |
| 3 | KOBO-001 | Oct-2026 | Diesel | `874.99999999999989` | USD |
| 4 | KOBO-001 | `46296` (number: 1 Oct 2026) | kWh sold | `8550` | (no cell) |

Test X0 asserts the committed `.xlsx` bytes equal `build_workbook(GOLDEN_ROWS)`.

`lakeside-budget.profile.json`: `profile_id` `lakeside-budget`, ILLUSTRATIVE, `budget_workbook`, `source_system`
`lakeside-budget-workbook`, `file` xlsx sheet `Budget 2026` header_row 1, `values` as §4.1 but `month_format`
`Mon-YYYY`; `version` `{"from": "row_digest"}`; `record_id_join` `["Site", "Month", "Line"]`; columns `Site` →
`site_code` · `Month` → `clocks.recognition_period` (month) · `Line` → `body.line_ref` (text), `body.factor_id` map
`{"Revenue": "revenue", "Diesel": "fuel_cost", "kWh sold": "billed_kwh"}` · `Amount` → `body.value` (number) ·
`Currency` → `body.currency`; constants `kind` BUDGET_LINE, `body.version_ref` `lakeside-budget-2026`.

`lakeside-budget.expected.json` (every record `format_version` 1, `kind` BUDGET_LINE, `site_code` KOBO-001,
`clocks.recognition_period` 2026-10, `body.version_ref` lakeside-budget-2026):

| `source_record_id` | `source_version` | `line_ref` | `factor_id` | `value` | `currency` |
|---|---|---|---|---|---|
| KOBO-001:2026-10:Revenue | r8b6cdd540fa7c49a | Revenue | revenue | 3420 | USD |
| KOBO-001:2026-10:Diesel | r4bc1868e230b8ed3 | Diesel | fuel_cost | 875 | USD |
| KOBO-001:2026-10:kWh sold | rff4a97f304aa3280 | kWh sold | billed_kwh | 8550 | (absent) |

(Digests by hand: `sha256` of `KOBO-001␟2026-10␟Revenue␟3420␟USD`, `...␟Diesel␟875␟USD`, `...␟kWh sold␟8550␟`, `␟` =
U+001F, first 16 hex.) Rows `(2, 3, 4)`.

## 5. Migration `0067_source_profile`

```sql
CREATE TABLE commercial_source_profile (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES tenant (id),
    profile_id text NOT NULL CHECK (profile_id ~ '^[a-z][a-z0-9-]{0,47}$'),
    version int NOT NULL CHECK (version BETWEEN 1 AND 9999),
    reader text NOT NULL CHECK (reader = 'profile.' || profile_id || '.v' || version::text),
    status text NOT NULL CHECK (status IN ('ILLUSTRATIVE', 'PINNED')),
    source_type text NOT NULL CHECK (source_type ~ '^[a-z][a-z_]{0,39}$'),
    source_system text NOT NULL CHECK (source_system ~ '^[a-z0-9][a-z0-9.-]{0,79}$'
                                       AND source_system NOT LIKE 'illustrative-%'),
    file_format text NOT NULL CHECK (file_format IN ('csv', 'xlsx')),
    profile_json text NOT NULL CHECK (octet_length(profile_json) BETWEEN 2 AND 65536),
    profile_sha256 text NOT NULL CHECK (profile_sha256 ~ '^[0-9a-f]{64}$'),
    sample_sha256 text NOT NULL CHECK (sample_sha256 ~ '^[0-9a-f]{64}$'),
    expected_sha256 text NOT NULL CHECK (expected_sha256 ~ '^[0-9a-f]{64}$'),
    sample_rows int NOT NULL CHECK (sample_rows BETWEEN 3 AND 200),
    admitted_at timestamptz NOT NULL,
    admitted_by uuid NOT NULL,
    admitted_role text NOT NULL CHECK (admitted_role IN ('ANALYST', 'FINANCE_AND_COMMERCIAL_LEAD')),
    UNIQUE (tenant_id, profile_id, version),
    UNIQUE (tenant_id, reader),
    UNIQUE (tenant_id, profile_id, profile_sha256)
);
CREATE TRIGGER commercial_source_profile_immutable BEFORE UPDATE OR DELETE ON commercial_source_profile
    FOR EACH ROW EXECUTE FUNCTION ledger_append_only();
```
No defaults; downgrade refuses if a row exists (0065's pattern). Reads: `source_profiles_all(tenant, profile_id)`
(`ORDER BY version`), `source_profile_latest(tenant, profile_id)` (`ORDER BY version DESC LIMIT 1`),
`source_profiles_latest(tenant)` (`DISTINCT ON (profile_id) ... ORDER BY profile_id, version DESC`). The memory store
mirrors them.

## 6. Tests

**Contracts, no database** (`contracts/tests/test_3a6_profiles.py`, T2's neutral guard):
- N1 The four illustrative goldens still read to their expected records and render to their bytes (3A3 contracts 1
  rerun unchanged); `check_layout` passes on `LAYOUTS`.
- N2 `kobo-ledger-expenses`: compiles; reads to its expected records, rows `(4, 5, 6, 7)`, no refusal; the same
  bytes declared `utf-8` are `NATIVE_ENCODING`; `Phone` values appear nowhere in the batch object.
- N3 `lakeside-budget`: X0; reads to its expected records, rows `(2, 3, 4)`; a second sheet added is `NATIVE_SHEET`;
  sheet renamed `Budget` is `NATIVE_SHEET`; `date1904="1"` is `NATIVE_WORKBOOK`; a `<!DOCTYPE` in `sheet1.xml` is
  `NATIVE_WORKBOOK`; a cell `t="e"` in row 3 refuses row 3 alone `NATIVE_FORMAT`; bytes `b"not a zip"` are
  `NATIVE_WORKBOOK`.
- N4 Transforms, literals: number `1.200,00` → `1200.00`, `-5,5` → `-5.5`, `(12,50)` with parentheses → `-12.50`,
  `0012` → `12`, `1.20,00` fails, ` 500,00` (leading space) fails, `12.5` (decimal `,`, thousands `.`) fails; scale `0.001` on `12500` → `12.500`;
  date `5/1/2026` `DD/MM/YYYY` → `2026-01-05`, `31/02/2026` fails; datetime `11/10/2026 09:00` Nairobi →
  `2026-10-11T09:00:00+03:00`, `2026-10-11T06:00:00Z` kept as is; month `Oct-2026` → `2026-10`, `oct-2026` fails,
  `October 2026` (`Month YYYY`) → `2026-10`; month_of `2026-10-31T22:30:00+00:00` Nairobi → `2026-11`; serial 46296
  date → `2026-10-01`; serial `46296.5` datetime UTC → `2026-10-01T12:00:00+00:00`.
- N5 Invisible: U+0085, U+200B, U+FEFF, U+2028 and U+00AD each in row 2 of the billing golden refuse that row alone
  `NATIVE_CHARACTER`; a tab inside a quoted cell is still admitted; a U+200B in `kobo-ledger-expenses`' dropped
  `Phone` column is admitted.
- N6 Join and digest: blanking `Line` in the budget's row 2 writes no `source_record_id`; the digests are the
  literals of §4.2; changing row 2's amount to `3421` changes only row 2's digest.
- N7 Profile validation: each of these is `ProfileInvalid` naming the key: unknown top-level key; `schema_version` 2;
  a map on `body.counterparty_ref`; `body.category` without a map; two columns writing `site_code`; `record_id_join`
  with a column also writing `source_record_id`; `source_system` `illustrative-x`; `thousands_mark` equal to
  `decimal_mark`; `timezone` `Mars/Base`; `scale` on a text path; version `column` with no column writing
  `source_version`.
- N8 `render_layout` on a compiled profile raises `NATIVE_RENDER <id> profile`; a planted illustrative layout whose
  column writes `body.method` with no map fails `check_layout`.

**Service, no database** (`backend/tests/test_3a6_source_profiles.py`; 3A2's in-memory world plus a
`ProfileMemoryStore` mirroring §5; Ana ANALYST, Fiona FINANCE):
- A1 Admit `kobo-ledger-expenses` (Ana): row v1, reader `profile.kobo-ledger-expenses.v1`, `sample_rows` 4,
  SHA-256s of the three files; admitting the same bytes again is `ALREADY_ADMITTED`, nothing written.
- A2 Changed profile (a fourth map value `"Repairs": "REPAIR"`) admits as v2; uploads naming v1 are 422
  `UPLOAD_READER_SUPERSEDED` with `latest` v2; a v2 with `source_system` changed is `PROFILE_LINEAGE`; a new
  `profile_id` with the same `source_system` is `PROFILE_SOURCE_SYSTEM_TAKEN`.
- A3 Status: ILLUSTRATIVE with `real_data=True` is `PROFILE_STATUS`; PINNED with `real_data=False` is
  `PROFILE_STATUS`.
- A4 Sample: 2 data rows is `ADMIT_SAMPLE_SIZE` (2); a row with `Litres` `4OO` is `ADMIT_SAMPLE_ROW` row 4
  `NATIVE_FORMAT`; a header renamed is `ADMIT_SAMPLE_FILE NATIVE_HEADER`.
- A5 Expected: PL-1002's amount written `475.0` in the expected file is `ADMIT_EXPECTED` row 5, where
  `amount.value`; one record missing is `ADMIT_EXPECTED_COUNT` 3 vs 4.
- A6 Probes refuse a lax engine: `run_probes` on the `kobo-ledger-expenses` rows with five stub `read` functions,
  each `read_rows` with one fault: (a) drops short rows, (b) admits U+200B, (c) writes the raw cell on a map miss,
  (d) writes the raw cell on a bad date, (e) writes `"0"` for a blank amount. Each gives `ADMIT_PROBE` P2, P3, P4, P5,
  P6 respectively; the true `read_rows` passes all six.
- A7 Personal: a profile declaring `personal` `[["body.counterparty_ref", "P"]]` is admitted; `[["amount.value",
  "P"]]` is `PROFILE_INVALID personal.0`.
- A8 Nothing of the sample is stored: the memory row holds no cell value of the sample (search every string field
  for `fuel-co`, `STAFF-07`, `0712000001`).
- U1 Upload through the intake (organisation path, Ana submits, Fiona accepts) with the v1 reader: 4 NEW; stored
  `STAFF-07` pseudonymised (3A2's formula, written out in the test); no phone number in any stored string or response.
- U2 Budget workbook admitted and uploaded (media type XLSX): 3 NEW; resubmitting nothing new; row 2's amount `3421`
  is REVISED (digest).
- U3 Source switch: after U1, the illustrative `expenses-illustrative-1` golden (KOBO-001 rows) is 409
  `UPLOAD_SOURCE_SWITCHED` with `system` `lakeside-purchases-ledger` on check and on submit; the same golden with
  only KISIWA-001 rows is admitted (another Site); a declined upload of the other system does not block (it is not
  held).
- U4 Unknown `profile.nope.v1` is 422 `UPLOAD_READER_UNKNOWN`; a tampered `profile_json` in the memory store is 500
  `COMMERCIAL_STORE_FAULT`; a CSV profile with media type XLSX is 415.
- U5 `field_label` for the profile: `record.amount.value` → `Net (USD)`; `row.6` → `row 6`.
- **Contract suite:** `test_3a3_source_contract.py` runs C1 to C10 over `CONTRACT_CASES + PROFILE_CASES` with the
  fields of §2.10; its coded-headers assertion passes for all five cases.
- S1 extended (§2.9): the five new planted sources fail; the allowlist equals the scan's findings.

**Loader, no database** (`test_3a3_load_emulated.py`, extended): L7 a directory with `acme.billing.csv` and
`acme.profile.kobo-ledger-expenses.csv` (profile admitted for `acme`) loads both; L8 `acme.profile.nope.csv` is
`PROFILE_NOT_ADMITTED`, exit 2; L9 `acme.expenses.csv` beside `acme.profile.kobo-ledger-expenses.csv` is
`EXPORT_PATHS_MIXED expense_ledger`; L5's held row gains `source_system` `profile-x-system` and still gives
`EXPORT_PATH_SWITCHED`.

**Command, no database** (`backend/tests/test_3a6_source_profile_command.py`, injected services): K1 `check` prints
ADMISSIBLE exit 0; K2 `admit --as peter` (no role) `PERSON_ROLE_REQUIRED` exit 2; K3 a refused sample prints REFUSED
with `text` "Row 4 of the sample is refused: Litres: ..." exit 3; K4 `list` prints one line per latest profile.

**Postgres** (`backend/tests/test_3a6_source_profiles_postgres.py`, pooled `--db`, `*_test` only): Q1 migration
upgrade, downgrade refused with a row, append-only trigger refuses UPDATE; Q2 admit v1 and v2, `source_profiles_latest`
returns v2, the three reads round-trip every column; Q3 U1 end to end on Postgres (upload accepted, `held_uploads`
carries `source_system` and `site_codes`).

**Regression:** 3A3's contracts, service, single-writer, emulator, loader and Postgres files; 3A2's service, API and
Postgres files; `test_3a4_commercial_months.py`; `test_on1_*`; check-all.

## 7. Done (questions; each can fail)

1. Do the four illustrative layouts read and render exactly as before (N1, 3A3 contracts 1 and E7's SHA-256 pins)?
2. Does each fixture profile read its sample to its hand-written records (N2, N3), and does every transform give the
   literal of N4?
3. Is a profile admitted only after its sample reads to the expected records and every probe refuses what it must
   (A1, A4 to A6), with nothing of the sample stored (A8)?
4. Does an admitted profile read uploads through 3A2's intake unchanged, pseudonymising refs and dropping dropped
   columns (U1, U2, C1 to C10 on the profile case)?
5. Is a second source system for the same source type and Site refused at the intake, on check and submit, while
   another Site or a declined upload is not (U3)?
6. Are invisible characters beyond C0 refused per row (N5, P3)?
7. Does the suite require a probe for every column writing a coded path, derived from the canonical side and not from
   the layout's maps, and does `check_layout` refuse an unmapped coded path (§2.10 assertion, N7, N8)?
8. Does S1 fail on each of the five new planted sources, with the allowlist equal to the scan (§2.9)?
9. Does a new layout need no code: a profile file plus `source_profile admit`, then the loader or the route (L7, U1,
   K1)?
10. Does each planted violation in the reviewer guide fail its named test?
11. Is nothing changed beyond §3's files, the fixtures and tests of §4 and §6, `source_contracts.py`, the
    `test_3a3_*` files named in §6 (extensions only), `test_3a2_commercial_upload_service.py` and the 3A2 API test
    (the `reader` signature only), and the packet?

Packet: `specs/3A6-source-profiles/packet.md` (module paths, fixture SHA-256s, plants, mid-build count, S1 residual).

## 8. Units

| Unit | Content | Commit |
|---|---|---|
| 1 | Engine growth (§2.2), `xlsx.py`, transforms, `profiles_v1.py`, the coded rule, fixtures and `make_budget_xlsx.py`, N1 to N8 | 1 |
| 0.75 | Migration 0067, store and adapter, `profiles.py`, the intake changes (§2.6), words, guard, A1 to A8, U1 to U5, Q1 to Q3 | 2 |
| 0.75 | The command, the loader (§2.8), S1 (§2.9), the suite changes (§2.10), L5 to L9, K1 to K4; check-all; packet | 3 |

## 9. Out of scope

Workbooks with several sheets, merged cells or formulas needing evaluation (the analyst reshapes them into the
template, timed, RC2); skipping totals rows (they are refused as rows and counted); a switch of source system for a
Site (queue Q1); a profile editor or upload screen; real operator data (RC4, ON1b); cold-chain and EV profiles (RC5);
reconciliation (`3A7`).

## 10. Decision queue (W3)

| # | Question | Default applied |
|---|---|---|
| Q1 | How does a tenant move a source type at a Site from one system to another (e.g. from the hand-reshaped template to a profile)? | Not this fortnight: refused (`UPLOAD_SOURCE_SWITCHED`); while the old system's uploads are only waiting, declining them frees the switch. A retire act that supersedes the old system's records comes with the upload screen. The runbook puts the profile first and the template second (D-3A3.10), so the case should not arise in the deep-dive. **Owner to weigh in** only if a pilot needs it sooner |
| Q2 | Who may admit a profile? | The analyst or the finance lead (`commercial.profile_admit`); every upload it reads is still accepted by a finance lead or executive |
| Q3 | Totals rows at the foot of an export | Refused as rows, shown in the counts; no "skip when" rule (it could hide data) |
| Q4 | Encodings | UTF-8 and cp1252 only; another is reshaped or converted by the analyst, timed |
| Q5 | Where real profiles live | In the operator's own database, with only the sample's and expected file's SHA-256 (RC4); the illustrative fixtures alone are in the repository |
