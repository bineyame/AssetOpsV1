# 3A6: source profiles as data (implementer spec)

Status: **in_review** (fix round r5 built: commit 1 the envelope `3134d35c6`, commit 2 the bounds `ba6eaee85`; packet "Fix round r5"), rev 4 amendments from review r5 (D-3A6.23 to D-3A6.28, §2.12: the parse envelope, +1.25 units, two commits), rev 3 from review r1 (D-3A6.18 to D-3A6.22; `rulings.md` "Review answers (r1)") (built on rev 2, 21 Nov; packet `packet.md`). Handshake round 1 answered (`rulings.md`).
Questions during the build: `mid-build-questions.md`. Reviewer: `reviewer-guide.md` rev 3 (round 6 stop rule). Decisions with reasons:
`rulings.md` (D-3A6.1 to D-3A6.28).

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

Non-screen. **2.75 units, three commits** (rev 2: +0.25 for the handshake's coverage checks, acceptance re-check and S1 plants). Discovery review (W5): a new shared contract (the profile format), a new
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
- **Migration (D-3A6.12)** `0067_source_profile` revises `0066_structure_snapshot` (`3B7a`, which merges first; no
  renumbering). Commit 1 (no migration) may start off `main` before 3B7a merges; commit 2 starts only on a base holding
  `backend/migrations/versions/0066_structure_snapshot.py` (merge `main` in; never branch off the unmerged 3B7a branch).
  Q1 asserts the chain link `("0067_source_profile", "0066_structure_snapshot")`, never "is head" (D-3B7A.14).
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
| `version` | `{"from": "constant", "value": <1..40 characters, no control>}` (refused, `PROFILE_INVALID version`, when any column writes `status`: D-3A6.16), `{"from": "column"}` (exactly one column writes `source_version`) or `{"from": "row_digest"}` |
| `record_id_join` | optional list of 2 to 4 distinct headers; when present no column writes `source_record_id`; when absent exactly one column does |
| `columns` | 2 to 60 objects `{"header": <1..100 characters, no control, unique>, "paths": [<path object>, ...]}`; `paths: []` is a **dropped** column (read for the header match, never written) |
| path object | `{"path": <canonical path>, "type": "text" \| "number" \| "date" \| "datetime" \| "month" \| "month_of", "map": {<native>: <canonical>}?, "scale": <decimal text>?}`; `map` only with type `text`; `scale` only with type `number`, fullmatching `(0\|[1-9][0-9]{0,11})(\.[0-9]{1,12})?` and not zero |
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
   `header_row` (XLSX; absent is an empty header). Rows before it are skipped whatever they hold. A missing header row
   (CSV: fewer rows) is `NATIVE_HEADER json` here; XLSX drops the header row's trailing empty cells. The comparison
   with the layout's headers is `read_rows`' first step (handshake R5), so the P1 probe reaches it.
4. Data rows: every later row; a row with no cells, or (XLSX) whose cells are all empty, is skipped. XLSX rows are
   padded with `""` to the header's length; an XLSX row with a non-empty cell beyond the header's length is refused
   `NATIVE_ROW row.<n>` (by `read_rows`, as a count mismatch).

**`read_rows`** first compares `header` with `[c.header for c in layout.columns]` (not equal: `NATIVE_HEADER json`,
the file refused), then applies 3A3 §2.2 steps 4 to 7, with these changes, in this order per row:
- Count mismatch: `NATIVE_ROW row.<n>` (unchanged).
- **XLSX bad cell (D-3A6.13 c):** an `XlsxBad` cell in a column with at least one path refuses the row
  `NATIVE_FORMAT record.<that column's first path>` (first such column); in a dropped column it is ignored.
- **Invisible characters (D-3A6.4, amends D-3A3.9):** a cell of a column with at least one path holding a character
  `ch` with `ord(ch) in _CONTROL` (3A3's set) or `unicodedata.category(ch) in {"Cc", "Cf", "Zl", "Zp", "Cs"}`, tab, LF
  and CR excepted, refuses the row `NATIVE_CHARACTER row.<n>`. Dropped columns are not checked.
- Each column path, cell not `""`: map (miss: `NATIVE_VALUE record.<path>`, first miss only, unchanged), else the
  type's transform (§2.4; failure: `NATIVE_FORMAT record.<path>`, first failure only, after maps), else the cell.
  A row with a map miss is refused `NATIVE_VALUE` even if a transform also fails.
- **Join (record ID):** with `record_id_join`, `source_record_id = ":".join(v)` where `v` is, for each named header in
  the given order, the value its column wrote to its **first path**; when any is absent, nothing is written (2a then
  refuses the record); when any part contains `":"`, the row is refused `NATIVE_FORMAT record.source_record_id`
  (handshake R16).
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
`XlsxNumber(str)` (a marker subclass for numeric cells), `XlsxBad(str)` (a marker for a cell that cannot be read;
its value is `""`). `zipfile` and `xml.etree.ElementTree` only. File refusals (`CanonicalRefused(<code>, "json")`):
- `NATIVE_WORKBOOK`: not a zip; a member
  `xl/workbook.xml`, `xl/_rels/workbook.xml.rels` or the sheet's target missing; a read member that does not decode
  strict UTF-8 (a leading UTF-8 BOM dropped; a UTF-16 member is refused); any decoded member containing `<!DOCTYPE`
  or `<!ENTITY`; XML that does not parse; `workbookPr` with `date1904` true (`"1"` or `"true"`). Every
  `zipfile.BadZipFile`, `zipfile.LargeZipFile`, `zlib.error`, `NotImplementedError` (unsupported compression),
  `RuntimeError` (encryption), `EOFError`, `KeyError`, `UnicodeDecodeError` and `ElementTree.ParseError` raised inside
  `xlsx_rows` is `NATIVE_WORKBOOK`; nothing else is caught (D-3A6.13 e).
- `NATIVE_SHEET`: the workbook does not hold exactly one `<sheet>` element, or its `name` is not `sheet`.
- `NATIVE_TOO_LARGE` (rev 4, D-3A6.25): every resource bound (the member and total sizes, declared or inflated, the
  element, character, padding, attribute and zip-directory bounds) and every envelope breach (§2.12).

Cells: `<c r="B7" t="...">`. Column index from the letters of `r` (`A` = 0; a cell without `r` takes the next index).
`t="s"`: shared string `int(v)` (`<si>` text: its `<t>`, or its `<r><t>` runs concatenated); `t="inlineStr"`: the `<is>`
text, same rule; `t="str"`: the `<v>` text; `t="b"`: `"TRUE"` or `"FALSE"`; `t` absent or `"n"`: an `XlsxNumber` of
`format(Context(prec=15, rounding=ROUND_HALF_EVEN).plus(Decimal(v)).normalize(...), "f")` (Excel's 15 significant
digits: `874.99999999999989` reads `875`, `3420` reads `3420`); `t="e"` or `t="d"`, or a `<v>` that is not a finite
decimal (`NaN`, `Infinity`, `sNaN`, text): an `XlsxBad("")` cell; `xlsx_rows` refuses no row, and `read_rows` judges
the marker only in a column with a path (§2.2; D-3A6.13 c). A `<row>` without `r` takes the previous row's number plus
one. The character rule of §2.2 applies to the text cells of columns with a path only, as for CSV.

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
  its integer part `k` must be 61 to 73050 (1900-03-01 to 2099-12-31), else the transform fails; out
  `date(1899, 12, 30) + timedelta(days=k)` (D-3A6.13 b; the window is checked before any date arithmetic).
- **datetime**: a cell that fullmatches 2a's instant pattern (with `Z` or an offset) is kept unchanged. Else it must
  fullmatch `date_format + " " + time_format`; the naive time is placed in `ZoneInfo(timezone)` (`fold=0`); a local
  time that does not exist there (the UTC round trip differs) fails. Out `isoformat()` (`2026-10-11T09:00:00+03:00`).
  An `XlsxNumber` is a serial: date as above plus `round(fraction × 86400)` seconds, then placed in the zone.
- **month**: the cell fullmatches `month_format`, out `YYYY-MM`. An `XlsxNumber` under `month_format` `YYYYMM` is read
  through the grammar as its text (`202610` → `2026-10`; D-3A6.13 a); under any other month format it is a serial
  date (window as above); out its month.
- **month_of**: the cell read as **datetime** (any branch above), else as **date**; out the month of the local date
  (an instant with an offset is first converted to `timezone`). An `XlsxNumber` under `month_format` `YYYYMM` is read
  as **month** (its text through the grammar).

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

1. **Profile.** The bytes (≤ 64 KiB) decoded strict UTF-8 (a BOM is not stripped, so it refuses: handshake R18), then
   `json.loads` of the text to an object, else `PROFILE_INVALID {where: "json"}`;
   `compile_profile` (its `ProfileInvalid(where)` is `PROFILE_INVALID {where}`); each `personal` path in
   `ALLOWED_EXTRA` and class in `CLASSES`, else `PROFILE_INVALID {where: "personal.<i>"}`.
2. **Status.** `PINNED` when the service runs with `real_data`, `ILLUSTRATIVE` otherwise, else `PROFILE_STATUS`.
3. **Lineage and version.** `rows = store.source_profiles_all(tenant_id, profile_id)` (every version). If one has
   `profile_sha256` equal to the file's: `already` is that row (`admit` returns it, writes nothing; the command says
   `ALREADY_ADMITTED`). Else a row whose `source_type` or `source_system` differs from the file's is
   `PROFILE_LINEAGE`; a file whose `personal` differs from the latest row's, while the tenant holds an ACCEPTED upload
   with this `source_system`, is `PROFILE_LINEAGE {where: "personal"}` (rev 3, D-3A6.18); `version = max(versions) + 1` or 1. Another `profile_id` of the tenant whose latest row has the
   same `source_system` is `PROFILE_SOURCE_SYSTEM_TAKEN {system}`.
4. **Sample.** At most 1 MiB. `reader = LayoutReader(compile_profile(obj, version))`; `read = reader.read(sample,
   context=ReadContext(slug, clock(), real_data))` (`slug = store.tenant_slug(tenant_id)`; None is
   `UPLOAD_TENANT_MISMATCH` as 3A3); a `CanonicalRefused` is `ADMIT_SAMPLE_FILE {code}`; data rows (records) must be 3
   to 200, else `ADMIT_SAMPLE_SIZE {rows}`; `parse_batch(read.obj)`; the first index (file order) refused by the reader
   or by 2a is `ADMIT_SAMPLE_ROW {row, code, path}` (`row` from `read.rows`, path cut by `cut_path`).

   **Coverage (D-3A6.11)**, on `split_file`'s rows, in this order, first failure only:
   - 4a. Each column with at least one path, in header order: no data row's cell there is non-empty:
     `ADMIT_COLUMN_EMPTY {header}`.
   - 4b. Each column with a map, in header order, each map key in the profile file's key order: no data row's cell
     there equals the key: `ADMIT_MAP_UNCOVERED {header, value}`.
   - 4c. Dates: when `date_format` is `DD/MM/YYYY`, `MM/DD/YYYY`, `DD-MM-YYYY` or `DD.MM.YYYY` and at least one
     non-empty, non-`XlsxNumber` cell of a `date`, `datetime` or `month_of` path is read through `date_format` (not
     an instant kept as is), at least one such cell must **fail** under the same format with DD and MM swapped, else
     `ADMIT_DATE_AMBIGUOUS`. Numbers: when `{decimal_mark, thousands_mark} == {".", ","}` and at least one non-empty,
     non-`XlsxNumber` cell of a `number` path exists, at least one such cell must **fail** the number grammar with the
     two marks swapped, else `ADMIT_NUMBER_AMBIGUOUS`. A cell that reads under both orders (even to another value)
     does not disambiguate.
5. **Expected.** The expected bytes decoded strict UTF-8 (BOM refused) and `json.loads` to a list of objects, else
   `ADMIT_EXPECTED_FILE`; its
   length must equal the records' (`ADMIT_EXPECTED_COUNT {expected, records}`); record `i` (the reader's object, before
   pseudonymisation) must equal item `i` exactly, else `ADMIT_EXPECTED {row, where}` with `where` the first differing
   dotted path in sorted-key walk order (`record` when the types differ).
6. **Probes**, `run_probes(layout, header, rows, *, tenant_code, produced_at, provenance, read=read_rows) ->
   tuple[str, str] | None` in `native/profiles_v1.py` (public; returns the first failing `(probe, where)`, None when
   all pass; the backend raises `ADMIT_PROBE {probe, where}`; each probe mutates a copy of `split_file`'s header or
   rows and calls `read`; `first` = the first data row; the check after
   each: the number of records equals the number of data rows, and only the named row is refused, with the named code;
   otherwise `ADMIT_PROBE {probe, where}`):
   - `P1 header`: the first two header cells swapped (profiles have at least two columns): `read` raises
     `CanonicalRefused` `NATIVE_HEADER` (`where` "file").
   - `P2 short`: `first` without its last cell: `NATIVE_ROW` on `first` alone.
   - `P3 invisible`: for each of `"\x00"`, `"\x85"`, `"\u200b"`, `"\ufeff"`, `"\u2028"` (Python escapes): appended to `first`'s cell of
     the first column with a path: `NATIVE_CHARACTER` on `first` alone.
   - `P4 coded`: for each column with a map, the first row whose cell there is non-empty, the cell set to
     `cell + " ?"`: `NATIVE_VALUE` on that row alone (`where` the header).
   - `P5 format`: for each column path of type other than `text`, the first row whose cell there is non-empty, the
     cell set to `"?"` (a plain `str`): `NATIVE_FORMAT` on that row alone (`where` the header).
   - `P6 blank`: for each column with a path, the first row whose cell there is non-empty, the cell set to `""`: that
     row is refused by the reader, or the reader's record holds none of the column's paths (no value is invented;
     2a is not consulted).
7. **Write** (`admit` only): `store.add_source_profile(ProfileRow(...))` with `profile_json` the profile bytes decoded,
   `admitted_role` the actor's role; a unique violation is `PROFILE_ALREADY_ADMITTED`. Nothing of the sample or the
   expected file is kept but their SHA-256 and the row count (RC4).

**Reading uploads** (`reader(tenant_id, reader_id, *, superseded_ok: bool = False)`): `reader_id` must fullmatch `profile\.([a-z][a-z0-9-]{0,47})\.v([1-9][0-9]{0,3})`,
else `UploadRefused(422, "UPLOAD_READER_UNKNOWN")`; the latest row of that profile (`store.source_profile_latest`)
None is `UPLOAD_READER_UNKNOWN`; a lower version than the latest is `UploadRefused(422, "UPLOAD_READER_SUPERSEDED",
{"latest": <reader>})` unless `superseded_ok` (then that version's row from `source_profiles_all`; absent is
`UPLOAD_READER_UNKNOWN`); `sha256(profile_json)` differing from `profile_sha256` is 500 `COMMERCIAL_STORE_FAULT`; then
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
- **Re-checked at acceptance under the lock (D-3A6.15).** `CommercialStore.write_intake` with an ACCEPTED `decision`
  and not a dry run, under the tenant's lock, after the already-decided check and before `decide`: when another upload
  of the tenant with an ACCEPTED decision has the deciding upload's `source_type`, a different `source_system`, and a
  `month_site_code` value in common with it (NULL equal to NULL; Postgres: `EXISTS (SELECT 1 FROM unnest(a.month_site_code)
  x JOIN unnest(b.month_site_code) y ON x IS NOT DISTINCT FROM y)`), it raises `UploadSourceSwitched(system)` (new, in
  `commercial/model.py`; `system` the smallest such `source_system`) and writes nothing. `decide` maps it to
  `UploadRefused(409, "UPLOAD_SOURCE_SWITCHED", {"source_type", "system"})`; the upload stays waiting. The memory
  store mirrors it.
- **Stored uploads keep their profile reader (handshake P6).** `CommercialUploads.get` resolves `u.reader`: `READERS`
  first; else, when it starts `profile.` and `profiles` is set, `self._profiles.reader(tenant_id, u.reader,
  superseded_ok=True)`; else `READERS[DEFAULT_READER]` as today.
- `HeldUpload` gains `source_system: str` and `site_codes: tuple[str | None, ...]` (distinct `month_site_code`
  values, `None` first then sorted); `_HELD` and the memory mirror select them.
- `build_commercial_uploads` builds `SourceProfiles(store, clock=..., real_data=settings.real_data)` and passes it.
  New `build_source_profiles(database_url) -> (SourceProfiles, dispose)` for the command (same settings path).

### 2.7 The command (D-3A6.10)

`python -m assetops_backend.source_profile {check,admit,list} --tenant SLUG ...`; `build_parser()` public. The tenant
is `AccountService.tenant_by_slug(slug)` (new, `accounts/service.py`, delegating to `AccountStore.tenant_by_slug`
and returning its ID; D-3A6.17); None is `TENANT_NOT_FOUND`, exit 2.
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
  For profile files the source type is known only after step 5c, so this check runs after 5c over every file
  (`PROFILE_NOT_ADMITTED` first, then `EXPORT_PATHS_MIXED`; handshake P7); files of the illustrative readers and JSONs
  keep their pre-connection steps 1, 2 and 4.
- Across runs (step 5b): a file of source type `t` and source system `s` (a layout reader's `layout.source_system`;
  a JSON batch's top-level `source_system`, read with `json.loads`; unreadable JSON is left to the submission) when
  `held` has an upload of type `t` with another source system is `EXPORT_PATH_SWITCHED <t>`, exit 2. (The loader takes
  whole-tenant directories, so it does not narrow by Site; the intake's rule of §2.6 is the authority.)
- `main(argv, *, uploads=None, accounts=None, profiles=None)`.

### 2.9 S1 reaches dynamic imports and names built from strings (D-3A6.7, D-3A6.14; amends D-3A3.12)

`test_3a3_single_writer.py` (renamed nothing; extended). `ROOTS` gain `contracts/assetops_contracts`; the scan's
test-file filter is unchanged. Every violation string, old and new, is `f"{tag} {rel}:{lineno}: {detail}"`. Import
aliases are resolved per module: `import importlib as il`, `import importlib.util as u`, `from importlib import
import_module as im`, `import sys as s`, `from sys import modules as m`, `from operator import attrgetter as ag`,
`import builtins as b` all name the same thing as the plain form.

| Tag | Fails | Where |
|---|---|---|
| `S1-CTOR`, `S1-BUILD`, `S1-INGEST`, `S1-IMPORT` | 3A3's four rules (unchanged, now tagged) | as 3A3 |
| `S1-DYN` | a call to `importlib.import_module`, `importlib.reload`, `importlib.__import__`, `importlib.util.find_spec`, `importlib.util.spec_from_file_location`, `importlib.util.module_from_spec`, `__import__` or `builtins.__import__` | a module outside `DYNAMIC_IMPORT_ALLOWED` |
| `S1-DYN-COMMERCIAL` | such a call with **any** string-constant argument beginning `assetops_backend.commercial` or containing `/commercial/` | every module, allowlisted too |
| `S1-SYSMOD` | any reference to `sys.modules` | a module outside `SYS_MODULES_ALLOWED` |
| `S1-SYSMOD-COMMERCIAL` | a `sys.modules` subscript, or a call of its `get`, `pop`, `setdefault` or `__getitem__`, with a string-constant key beginning `assetops_backend.commercial` | every module |
| `S1-RUNPY` | an import of `runpy` (any form) | a module outside `RUNPY_ALLOWED` |
| `S1-NAME` | a string constant equal to `"ingest"` or `"CommercialRecords"` | outside `INGEST_ALLOWED \| IMPORT_ALLOWED` |
| `S1-ATTR` | a `getattr`, `setattr`, `hasattr` or `delattr` (bare or `builtins.`) whose name argument is not a string constant | a module importing from the commercial package, outside `INGEST_ALLOWED` |
| `S1-OPERATOR` | any use of `operator.attrgetter` or `operator.methodcaller` | same as `S1-ATTR` |
| `S1-EVAL` | a call of the bare builtins `eval`, `exec`, `compile` or of `builtins.eval`/`.exec`/`.compile` (an attribute call on anything else, such as `re.compile`, is not) | `backend/assetops_backend/commercial/`, `contracts/assetops_contracts/native/` |

Allowlists, each exactly the scan's findings at branch time, each entry with a one-line reason in the test:
`DYNAMIC_IMPORT_ALLOWED` = `backend/assetops_backend/chain/adapters/file_chain_config.py`,
`backend/assetops_backend/chain/adapters/file_inputs.py`, `tools/checks/import_root_probe.py`,
`tools/checks/neutral_tests.py`, `tools/mechanism_dataset.py`, `tools/validate-test-selection.py`, `host/conftest.py`
(handshake P4); `SYS_MODULES_ALLOWED` = `tools/mechanism_dataset.py`, `tools/probe_kisiwa_fuel.py`; `RUNPY_ALLOWED` =
`set()` (if the scan finds any, they are listed). `test_s1_allowlists_are_exact`: every allowlisted module holds at
least one finding of its clause (no stale entry), and the scan with empty allowlists finds exactly the allowlisted
modules.

`PLANTED_TAGGED` (each: `rel`, source, the exact set of tags `violations` must return); `x`, `s`, `name`, `svc`
are free names:

| # | `rel` | Source | Tags |
|---|---|---|---|
| p01 | `tools/planted.py` | `import importlib\nm = importlib.import_module(name)\n` | `{S1-DYN}` |
| p02 | `tools/planted.py` | `from importlib import import_module as im\nm = im(name)\n` | `{S1-DYN}` |
| p03 | `tools/planted.py` | `import importlib as il\nm = il.import_module(name)\n` | `{S1-DYN}` |
| p04 | `tools/planted.py` | `m = __import__(name)\n` | `{S1-DYN}` |
| p05 | `tools/planted.py` | `import importlib\nm = importlib.__import__(name)\n` | `{S1-DYN}` |
| p06 | `tools/planted.py` | `import importlib.util\nx = importlib.util.find_spec(name)\n` | `{S1-DYN}` |
| p07 | `tools/mechanism_dataset.py` | `import importlib\nm = importlib.import_module("assetops_backend.commercial.service")\n` | `{S1-DYN-COMMERCIAL}` |
| p08 | `tools/mechanism_dataset.py` | `import importlib.util as u\nx = u.spec_from_file_location("x", "backend/assetops_backend/commercial/service.py")\n` | `{S1-DYN-COMMERCIAL}` |
| p09 | `tools/planted.py` | `import sys\nm = sys.modules[name]\n` | `{S1-SYSMOD}` |
| p10 | `tools/mechanism_dataset.py` | `import sys\nm = sys.modules["assetops_backend.commercial.service"]\n` | `{S1-SYSMOD-COMMERCIAL}` |
| p11 | `tools/planted.py` | `from sys import modules as mods\nm = mods.get(name)\n` | `{S1-SYSMOD}` |
| p12 | `tools/planted.py` | `import runpy\nrunpy.run_module(name)\n` | `{S1-RUNPY}` |
| p13 | `tools/planted.py` | `from runpy import run_path\nrun_path(name)\n` | `{S1-RUNPY}` |
| p14 | `tools/planted.py` | `name = "ingest"\n` | `{S1-NAME}` |
| p15 | `tools/planted.py` | `name = "CommercialRecords"\n` | `{S1-NAME}` |
| p16 | `tools/planted.py` | `from assetops_backend.commercial import composition\nf = getattr(svc, name)\n` | `{S1-ATTR}` |
| p17 | `tools/planted.py` | `from assetops_backend.commercial import composition\nsetattr(svc, name, f)\n` | `{S1-ATTR}` |
| p18 | `tools/planted.py` | `from assetops_backend.commercial import composition\nx = hasattr(svc, name)\n` | `{S1-ATTR}` |
| p19 | `tools/planted.py` | `from assetops_backend.commercial import composition\ndelattr(svc, name)\n` | `{S1-ATTR}` |
| p20 | `tools/planted.py` | `import operator\nfrom assetops_backend.commercial import composition\nf = operator.attrgetter(name)\n` | `{S1-OPERATOR}` |
| p21 | `tools/planted.py` | `from operator import methodcaller as mc\nfrom assetops_backend.commercial import composition\nf = mc(name)\n` | `{S1-OPERATOR}` |
| p22 | `backend/assetops_backend/commercial/planted.py` | `x = eval(s)\n` | `{S1-EVAL}` |
| p23 | `backend/assetops_backend/commercial/planted.py` | `exec(s)\n` | `{S1-EVAL}` |
| p24 | `backend/assetops_backend/commercial/planted.py` | `x = compile(s, "f", "exec")\n` | `{S1-EVAL}` |
| p25 | `contracts/assetops_contracts/native/planted.py` | `import builtins\nx = builtins.exec(s)\n` | `{S1-EVAL}` |
| n1 | `backend/assetops_backend/commercial/planted.py` | `import re\nx = re.compile(s)\n` | `set()` |
| n2 | `tools/planted.py` | `x = getattr(obj, name)\n` | `set()` (no commercial import: the stated residual) |
| n3 | `tools/mechanism_dataset.py` | `import importlib\nm = importlib.import_module(name)\n` | `set()` (allowlisted) |

`test_s1_each_clause_has_its_plant` parametrises over `PLANTED_TAGGED` and asserts
`{v.split(" ", 1)[0] for v in violations(rel, src)} == tags`. 3A3's `PLANTED` stays (each must still give a non-empty
list).

Still not seen (residual, packet; D-3A6.14): a module that imports nothing commercial and calls `.ingest` on a
service it is handed, or uses a non-constant attribute name (n2); `__getattribute__`; `vars(obj)[name]` with a
non-constant name; a non-test tool named `test_*.py` (the filter hides `tools/checks/test_event_register.py`).

### 2.10 The contract suite derives what it probes (D-3A6.6)

`backend/tests/source_contracts.py`:
- `ContractCase.mapped` is replaced by `coded: tuple[tuple[str, str], ...]` (header, a value outside its map). The
  suite computes, from a hand-written `CODED_PATHS_EXPECTED` (the same twelve paths, written in the test file, not
  imported) and the reader's layout, the set of headers whose column writes a coded path, and asserts it equals
  `{h for h, _ in case.coded}`. So a layout that writes a coded path without declaring a map fails the suite (and
  `check_layout`), and billing's `coded=()` is now derived, not declared. The derivation is two named helpers in
  `source_contracts.py`: `coded_headers(layout) -> set[str]` (headers of columns with any path in
  `CODED_PATHS_EXPECTED`; it never reads `Column.maps`) and `assert_coded_probes(case, layout)` (raises
  `AssertionError` when `coded_headers(layout) != {h for h, _ in case.coded}`); the suite calls the latter for every
  case. `test_coded_check_fails_on_an_unchecked_layout` builds `Layout(id="planted.v1", ..., columns=(Column("Ref",
  ("source_record_id",)), Column("Method", ("body.method",))))` directly (no `check_layout`), a case with
  `coded=()`, and asserts `assert_coded_probes` raises (handshake R2).
- Cases change exactly: billing `coded=()`; collections `(("Status", "Lost"),)`; expenses `(("Category", "Fuel"),
  ("Status", "Draft"))`; budget `(("Line", "marketing"),)`. C8's map-miss check runs for every pair.
- New fields with defaults: `encoding="utf-8"`, `delimiter=","`, `header_row=1`, `line_end="\n"`,
  `bad_number=("12,5", "CANONICAL_NUMBER")`, `bad_clock_code="CANONICAL_CLOCK"`, `versioning="column"` (`"column"`,
  `"constant"` or `"digest"`; billing, expenses and budget `"column"`, collections `"constant"`, kobo `"digest"`),
  `changed_amount="999.00"` (C6's new amount; kobo `"999,00"`), `profile: Path | None = None`. Every count literal
  in C1 to C10 (`test_3a3_source_contract.py:166, 205, 211` and the like) is computed from the case's number of data
  rows `n`, not written for three (handshake P5). The word pins at lines 32 and 36 change to §2.11's
  `native_encoding` and `native_character` texts (a change, listed). The suite's mutation helpers read and write the golden with the case's encoding, delimiter, header row
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
| `commercial_upload.reason.native_too_large` (rev 4) | this file is too large or too complex to read in one upload; split it and upload the parts. |
| `commercial_upload.reason.native_sheet` | the workbook must hold exactly one sheet, with the sheet name this layout reads. |
| `commercial_upload.reason.native_encoding` (changed) | the file is not text in the character encoding this layout reads. |
| `commercial_upload.reason.native_character` (changed) | this row holds a character that is not text (such as a NUL byte or an invisible mark). |
| `commercial_upload.reader_superseded` | That file layout has a newer version: use {latest}. |
| `commercial_upload.source_switched` | These Sites already send this kind of export from another system. Use that system's export, or ask for the switch to be set up. |
| `source_profile.profile_invalid` | The profile is not valid at {where}. |
| `source_profile.profile_status` | A profile for an operator's real export must be PINNED; one for emulated data, ILLUSTRATIVE. |
| `source_profile.profile_lineage` | A new version cannot change the source type or the source system. Give it a new profile name. |
| `source_profile.profile_source_system_taken` | Another profile already reads the source system {system}. |
| `source_profile.profile_already_admitted` | This profile is already admitted. |
| `source_profile.upload_tenant_mismatch` | This organisation is not known here. |
| `source_profile.admit_sample_file` | The sample cannot be read: {reason} |
| `source_profile.admit_sample_size` | The sample must hold 3 to 200 rows; it holds {rows}. |
| `source_profile.admit_sample_row` | Row {row} of the sample is refused: {field}: {reason} |
| `source_profile.admit_sample_row_whole` | Row {row} of the sample is refused: {reason} |
| `source_profile.admit_column_empty` | No row of the sample has a value in {header}, so the profile's reading of it cannot be checked. Add a row that fills it. |
| `source_profile.admit_map_uncovered` | No row of the sample has {value} in {header}, so its meaning cannot be checked. Add such a row, or remove {value} from the profile. |
| `source_profile.admit_date_ambiguous` | The sample cannot show which way round dates are written: add a row whose day is after the 12th. |
| `source_profile.admit_number_ambiguous` | The sample cannot show which mark is the decimal mark: add a row with an amount written with its decimals. |
| `source_profile.admit_expected_file` | The expected records must be a JSON list of records. |
| `source_profile.admit_expected_count` | The expected file holds {expected} records; the sample gives {records}. |
| `source_profile.admit_expected` | Row {row} does not read as its expected record: {where} differs. |
| `source_profile.admit_probe` | The profile does not refuse what it must ({probe}, {where}). |

`{reason}` is `render(reason_words(code))`. In `admit_sample_row`, `{field}` is `reader.field_label(cut_path)` when the
cut path starts `record.`; a row-level path (`row.<n>`) uses `admit_sample_row_whole` (handshake R12). `_WORDS` in
`uploads.py` gains `UPLOAD_READER_SUPERSEDED`, `UPLOAD_SOURCE_SWITCHED`.

### 2.12 The parse envelope and the last bounds (fix round r5; D-3A6.23 to D-3A6.28)

**Module** `backend/assetops_backend/commercial/envelope.py` (new). It holds:

```python
@dataclass(frozen=True)
class EnvelopeLimits:
    memory_bytes: int = 512 * 2**20   # RLIMIT_AS, soft = hard
    cpu_seconds: int = 6              # RLIMIT_CPU soft; hard = soft + 1
    wall_seconds: float = 12.0        # parent's wait, then SIGKILL
    result_bytes: int = 32 * 2**20    # the pickled answer, checked in the child and by recv_bytes(maxlength)
    concurrent: int = 2               # children at once per ParseEnvelope (one per server process)
    # __post_init__: every field > 0, else ValueError

DEFAULT_LIMITS = EnvelopeLimits()

@dataclass(frozen=True)
class BoundedRead:
    result: ReadResult                                     # `refused` back as MappingProxyType
    split: tuple[list[str], list[tuple[int, list[str]]]] | None   # admission only

class ParseEnvelope:
    def __init__(self, limits: EnvelopeLimits = DEFAULT_LIMITS) -> None   # RuntimeError off Linux
    def read(self, reader: SourceReader, data: bytes, context: ReadContext, *, split: bool = False) -> BoundedRead
    peak_active: int    # the most children alive at once so far (for E5)

def reader_spec(reader: SourceReader) -> tuple: ...
```

- **Reader spec (what the child rebuilds).**
  - `("builtin", reader.id)` when `READERS.get(reader.id) is reader`.
  - `("profile", profile_json, version)` for a `LayoutReader` built with `profile=`.
  - Any other reader is a `TypeError`.
  - `LayoutReader.__init__(self, layout, *, profile: tuple[str, int] | None = None)` keeps `profile`.
    `ProfileService.reader` passes `(row.profile_json, row.version)`. Admission passes the uploaded profile's UTF-8
    text and its version.
  - The child rebuilds `LayoutReader(compile_profile(json.loads(text), version))` and refuses to run (an `error`
    answer) if the rebuilt `id` differs from `reader.id`.
- **The child** is `_child(conn, spec, data, context, split, limits)`, a module-level function.
  1. Before anything else: `setrlimit(RLIMIT_AS, (m, m))`, `RLIMIT_CPU (c, c + 1)`, `RLIMIT_FSIZE (0, 0)`,
     `RLIMIT_CORE (0, 0)`.
  2. Rebuild the reader. Call `reader.read(data, context=context)`. With `split`, also call
     `split_file(reader.layout, data)`.
  3. Count the records. For the JSON reader, a `records` list longer than `MAX_RECORDS + 1` answers
     `("refused", "CANONICAL_RANGE", "batch.records")`. This applies only if 2a's `parse_batch` does not already
     refuse the count before walking the records; the builder states which one holds in pre-flight, with a test of
     1,000,000 `{}` records.
  4. Answer with one `conn.send_bytes(pickle.dumps(answer, protocol=5))`:
     - `("ok", obj, rows, dict(refused), sorted(personal_paths), split_or_None)` on success;
     - `("refused", code, path)` for a `CanonicalRefused`;
     - `("breach", "memory")` for a `MemoryError`;
     - `("breach", "result")` when the pickle is longer than `result_bytes`;
     - `("error", type(e).__name__)` for any other exception.
  The child holds no database handle, no key and no store.
  No reader catches `MemoryError` (D-3A6.13 e already lists what is caught), so a breach in the C parsers reaches
  the child's handler.
- **The parent** (`ParseEnvelope.read`, in the request's worker thread). Inside `with self._slots:` (a
  `threading.BoundedSemaphore(concurrent)`; an upload waits for a slot and is never refused for waiting):
  1. Start the child: `ctx = multiprocessing.get_context("forkserver")`, created once under a lock with
     `ctx.set_forkserver_preload(["assetops_contracts.native"])`. Then `ctx.Pipe(duplex=False)` and
     `ctx.Process(target=_child, args=..., daemon=True).start()`, and close the child's end.
  2. Wait: `if not conn.poll(limits.wall_seconds)` → `kill()`, cause `wall`. Otherwise
     `conn.recv_bytes(maxlength=limits.result_bytes + 4096)`:
     - `OSError` (too long) → cause `result`;
     - `EOFError` → cause from the exit code: `-SIGXCPU` or `-SIGKILL` after the CPU hard limit → `cpu`, otherwise
       `crash`.
  3. Clean up, always: `join(1)`, `kill()` and `join()` if still alive, `close()` both.
  4. Map the answer:
     - `ok` → `BoundedRead`;
     - `refused` → raise `CanonicalRefused(code, path)`, as the in-process read did;
     - `breach` or any cause above → raise `CanonicalRefused("NATIVE_TOO_LARGE", "json")`, after logging
       `assetops.commercial.envelope` WARNING `"upload parse refused by the envelope"`, with `extra` `cause`,
       `reader` (id), `bytes` (length) and `tenant` (`context.tenant_code`) and nothing else from the file;
     - `error` → raise `RuntimeError(f"parse failed in the envelope: {name}")`, a 500 as an unexpected reader
       exception is today.
- **Wiring.**
  - `CommercialUploads._check`: `read = self._envelope.read(reader, data, context).result` replaces `reader.read`.
  - `ProfileService` step 4: one `self._envelope.read(reader, sample, context, split=True)` replaces `reader.read`
    and `split_file`. The rest of step 4 (`parse_batch`, `_coverage`, the row verdicts, `run_probes`) runs on the
    returned rows in the parent. Those rows are at most 200 after `ADMIT_SAMPLE_SIZE`.
  - `build_commercial_uploads` and `build_source_profiles` take an optional `envelope`. The default is one shared
    `ParseEnvelope(DEFAULT_LIMITS)` per process. Tests may pass a lower-limit envelope.
- **S1.** `S1-DYN` adds any attribute call named `set_forkserver_preload`. `DYNAMIC_IMPORT_ALLOWED` gains
  `backend/assetops_backend/commercial/envelope.py` ("the forkserver preloads the pure contracts package"), plus a
  plant `p-env` (`import multiprocessing as mp\nmp.get_context("forkserver").set_forkserver_preload([name])\n` →
  `{S1-DYN}`).
- **The bounds** (D-3A6.24), each `NATIVE_TOO_LARGE`:
  - `xlsx.py` `_ATTR_RUN_MAX = 4096`: in `_parse` after the DTD check, only when `text.count("=") > 4096`, any
    `[^<]+` match holding more than 4,096 `=`.
  - `xlsx.py` `_ATTR_NAMES_MAX = 512`: distinct attribute names per workbook. One set is shared by the four parses
    through the targets' constructor, and `_Target.start` checks it after adding `attrib`'s keys.
  - `xlsx.py` `_Workbook.date1904`: a string or None, which replaces `pr`.
  - `xlsx.py` `_directory_check(data)`, before `zipfile.ZipFile`: at most 256 entries and a 256 KiB directory, from
    the end record, or the zip64 end record when a field holds its sentinel. No end record → `NATIVE_WORKBOOK`.
  - `layouts_v1.py` `_ROW_CHARS_MAX = 1_048_576`: the CSV line generator (D-3A6.24, N9), path
    `row.{reader.line_num + 1}`.
- **Code switch** (D-3A6.25): `_too_large()` (`CanonicalRefused("NATIVE_TOO_LARGE", "json")`) replaces
  `_workbook_error()` at the declared-size pre-check, the inflated member and total caps, `_WORK_MAX`, `_CHAR_MAX` and
  `_PAD_BUDGET`. Every format refusal keeps `_workbook_error()`.
- **Words** (§2.11 row): `commercial_upload.reason.native_too_large`. The 3A3 contract word pin gains the code.

**Tests** (new file `backend/tests/test_3a6_parse_envelope.py`, no database; each upload goes through
`CommercialUploads.check` with the kobo profile admitted in memory unless stated):
- E0 `DEFAULT_LIMITS == EnvelopeLimits(512 * 2**20, 6, 12.0, 32 * 2**20, 2)`. A zero or negative field is a
  `ValueError`.
- E1 Memory: `memory_bytes=80 * 2**20` and the kobo fixture padded to 10,000 rows in about 8 MiB (VmPeak 104 MB) →
  `NATIVE_TOO_LARGE`, logged cause `memory` or `crash`. The same file under `DEFAULT_LIMITS` reads all 10,000
  records.
- E2 CPU: `cpu_seconds=1`, `wall_seconds=30`, the 499,000 `<row/>` workbook through the lakeside profile → refused,
  cause `cpu`. Precondition first: the same read in process takes at least 1.3 s of `process_time`. If the machine is
  faster, the builder scales the rows; the test is never skipped.
- E3 Wall: `wall_seconds=0.2` and E1's file → refused, cause `wall`, and the request returns within 2 s.
- E4 Result: `result_bytes=1 * 2**20` and the 10,000-row 788 kB file (3.2 MB result) → refused, cause `result`.
- E5 Concurrency: `concurrent=1`, two threads each checking E1's file → both read, and `peak_active == 1`.
- E6 Survival: after each of E1 to E4 on the same envelope, the kobo fixture reads to its expected records.
- E7 Exclusive: an AST scan of `backend/assetops_backend/` finds `read_layout`, `split_file`, `xlsx_rows`,
  `xlsx_sparse_rows`, `loads_canonical` calls and `.read(...)` calls with a `context=` keyword only in
  `commercial/envelope.py` and `commercial/readers.py`.
- E8 Faithful: for the four illustrative goldens, both fixtures and `canonical-json-v1` on 3A2's fixture,
  `envelope.read(...)` equals `reader.read(...)` in process (obj, rows, refused, personal paths). Admission's `split`
  equals `split_file`.
- E9 Logged without content: E1's file carries a sentinel string in a text column. No log record's message, args or
  extra contains it. The record holds `cause`, `reader`, `bytes` and `tenant`.

Contracts (`contracts/tests/test_3a6_profiles.py`, section "N3 r5", in process; time bounded in a plain run, peak
memory in a traced run):
- B1 N8: review r5's four attribute probes each give `NATIVE_TOO_LARGE` under 1.0 s and 60 MB: one element with
  1.45 M names; 14,500 names an element over 100 elements; 1 M `p:aN`; `workbookPr` plus a sheet element. A text run
  of 4,097 `=` is refused, and one of 4,096 reads. 513 distinct names over elements of 10 are refused; 512 read. The
  lakeside fixture and a 10,000-row, 20-column budget workbook (about 600,000 `=`, so the scan runs) read as before.
- B2 N9: one line of 4.2 M `\x80;` (cp1252), and 2.7 M fields over 90 quoted lines, each give `NATIVE_TOO_LARGE`
  under 0.5 s and 60 MB. A row of exactly 1,048,576 characters is not refused by the cap. The kobo fixture is
  unchanged.
- B3 N10: 125 entries, each with a 65,535-byte extra field of empty records (review r5), give `NATIVE_TOO_LARGE`
  under 0.2 s. 257 empty entries are refused; a 10-entry workbook reads. The zip64 path is exercised by a workbook
  written with zip64 end records (`zipfile` with `force_zip64=True` on a member).
- The r3 and r4 tests that expect `NATIVE_WORKBOOK` for a budget breach now expect `NATIVE_TOO_LARGE` (listed literal
  change).

**Plants** (reviewer guide V33 to V40). **Packet:**
- the bounds table rewritten with the envelope as its first row and the N8 to N10 rows;
- E1 to E4's measured costs;
- a 600-case differential of in-process against envelope reads (seed 2026, review r5's generator), with 0
  mismatches required;
- the 3A7 and 3C2 note of D-3A6.26.

## 3. Code

| File | Holds |
|---|---|
| `contracts/assetops_contracts/native/layouts_v1.py` | `FileRules`, `ValueRules`, new fields, `CODED_PATHS`, `split_file`, `read_rows`, transforms, join, digest, the invisible rule, `render_layout`'s refusal, `check_layout`'s coded rule |
| `contracts/assetops_contracts/native/xlsx.py`, `profiles_v1.py`, `__init__.py` | §2.3, §2.1 |
| `backend/migrations/versions/0067_source_profile.py` | §5 |
| `backend/assetops_backend/commercial/model.py`, `store.py`, `adapters/postgres_commercial_store.py` | `ProfileRow`, `UploadSourceSwitched`; `source_profiles_all`, `source_profile_latest`, `source_profiles_latest`, `add_source_profile`; `HeldUpload` fields; `write_intake`'s acceptance re-check (§2.6) |
| `backend/assetops_backend/commercial/profiles.py` | §2.5 |
| `backend/assetops_backend/commercial/readers.py` | media types by format; `LayoutReader(..., profile=)` (§2.12) |
| `backend/assetops_backend/commercial/envelope.py` (rev 4, new) | §2.12: `EnvelopeLimits`, `DEFAULT_LIMITS`, `BoundedRead`, `ParseEnvelope`, `reader_spec`, `_child` |
| `backend/assetops_backend/commercial/uploads.py`, `commercial_upload_api.py` | §2.6 |
| `backend/assetops_backend/commercial/composition.py` | `build_commercial_uploads` passes profiles; `build_source_profiles` |
| `backend/assetops_backend/source_profile.py` | §2.7 |
| `backend/assetops_backend/load_emulated_exports.py` | §2.8 |
| `backend/assetops_backend/accounts/permissions.py` | `"commercial.profile_admit": (ANALYST, FINANCE)` |
| `backend/assetops_backend/accounts/service.py` | `tenant_by_slug` (D-3A6.17) |
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
map `{"Invoiced": "INVOICED", "Paid": "PAID"}` (rev 2: no `Quote`, which no sample row holds; D-3A6.11); constants
`kind` EXPENSE, `subject.kind` SITE, `quantity.unit` L, `amount.currency` USD; `personal` `[]`. `version`
`{"from": "row_digest"}` (rev 2, D-3A6.16; replaces the constant `"1"`).

`kobo-ledger-expenses.expected.json`, in order (every record `format_version` 1, `site_code` KOBO-001, `kind`
EXPENSE, `subject` `{"kind": "SITE", "ref": "KOBO-001"}`, `amount.currency` USD):

| ID (= `document_ref`) | `source_version` | `occurred_at` | period | status | category | counterparty | amount | quantity |
|---|---|---|---|---|---|---|---|---|
| PL-1001 | r7a74ac02930cf9bd | 2026-10-11T09:00:00+03:00 | 2026-10 | INVOICED | FUEL | fuel-co | 500.00 | 400 L |
| PL-1002 | rb02e46e3dd180e63 | 2026-10-21T09:00:00+03:00 | 2026-10 | PAID | FUEL | fuel-co | 475.00 | 380 L |
| PL-1003 | r45ba3a14daa3c051 | 2026-10-31T17:00:00+03:00 | 2026-10 | PAID | OM | om-contractor | 1200.00 | (none) |
| PL-1004 | rf609c71589ac443d | 2026-10-31T17:30:00+03:00 | 2026-10 | PAID | STAFF | STAFF-07 | 450.00 | (none) |

(Digests by hand, §2.2's rule: `sha256` of the first-path values of `Ref`, `Txn Date`, `Site`, `Account`, `Supplier`,
`Litres`, `Net (USD)`, `State` joined by U+001F, e.g. `PL-1001␟2026-10-11T09:00:00+03:00␟KOBO-001␟FUEL␟fuel-co␟400␟
500.00␟INVOICED`; PL-1003 and PL-1004 carry `""` for `Litres`; first 16 hex. PL-1001 with `State` `Paid` gives
`r16fd22096444d702`; with `Net (USD)` `999,00` gives `r6e38c75df75107a7`.)

Rows `(4, 5, 6, 7)`. Its `PROFILE_CASES` entry: `required_headers` all but `Phone`; amount `Net (USD)`; clock `Txn
Date`, bad clock `2026-10-11 09:00`, `bad_clock_code` `NATIVE_FORMAT`; `bad_number=("12.5", "NATIVE_FORMAT")`;
`versioning="digest"`; `changed_amount="999,00"`; `coded=(("Account", "Fuel"), ("State", "Draft"))`; `personal_raw=("STAFF-07", "0712000001",
"0712000777")`; `encoding="cp1252"`, `delimiter=";"`, `header_row=3`, `line_end="\r\n"`.

### 4.2 `backend/tests/fixtures/3a6/lakeside-budget.*` (XLSX, one sheet `Budget 2026`)

`make_budget_xlsx.py` (in the fixtures folder; standard library; `build_workbook(rows, *, sheet="Budget 2026") -> bytes`, where `rows` is a list of `(r, cells)` and each cell is
`(ref, t, v)`: `t` None writes `<c r=ref><v>v</v></c>`, `"inlineStr"` writes `<c r=ref t="inlineStr"><is><t>v</t></is></c>`,
any other `t` writes `<c r=ref t=t><v>v</v></c>`; `GOLDEN_ROWS` is the table below in that form; and
`main()` that writes `lakeside-budget.xlsx`): a zip with every entry dated 1980-01-01 00:00:00, `ZIP_STORED` (rev 2,
handshake R14: byte-stable across zlib builds), entries in this
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
  `NATIVE_WORKBOOK`; a cell `t="e"` in row 3's `Amount` refuses row 3 alone `NATIVE_FORMAT`; bytes `b"not a zip"` are
  `NATIVE_WORKBOOK`. Rev 2 adds: `<v>NaN</v>` and, separately, `<v>Infinity</v>` as row 3's `Amount` refuse row 3
  alone `NATIVE_FORMAT` (D-3A6.13 c); a variant with a sixth header `Note` (dropped in a copy of the profile) whose
  row 2 cell is `t="e"` `#N/A` and row 3 cell an inline string holding U+200B reads all three records (no refusal);
  each `NATIVE_WORKBOOK` (D-3A6.13 d, e): one byte inside `sheet1.xml`'s stored data flipped (CRC), `sheet1.xml`'s
  compression method set to 99 in its local and central headers, the encryption flag (bit 0) set in both, and a
  workbook whose `sheet1.xml` is written UTF-16 with a BOM.
- N4 Transforms, literals: number `1.200,00` → `1200.00`, `-5,5` → `-5.5`, `(12,50)` with parentheses → `-12.50`,
  `0012` → `12`, `1.20,00` fails, ` 500,00` (leading space) fails, `12.5` (decimal `,`, thousands `.`) fails; scale `0.001` on `12500` → `12.500`;
  date `5/1/2026` `DD/MM/YYYY` → `2026-01-05`, `31/02/2026` fails; serial (date) `XlsxNumber("61")` → `1900-03-01`,
  `"73050"` → `2099-12-31`, `"60"`, `"73051"` and `"2958466"` fail (no exception escapes); month `YYYYMM`
  `XlsxNumber("202610")` → `2026-10`, `"202610"` (text) → `2026-10`, `XlsxNumber("202610")` under `Mon-YYYY` fails; datetime `11/10/2026 09:00` Nairobi →
  `2026-10-11T09:00:00+03:00`, `2026-10-11T06:00:00Z` kept as is; month `Oct-2026` → `2026-10`, `oct-2026` fails,
  `October 2026` (`Month YYYY`) → `2026-10`; month_of `2026-10-31T22:30:00+00:00` Nairobi → `2026-11`; serial 46296
  date → `2026-10-01`; serial `46296.5` datetime UTC → `2026-10-01T12:00:00+00:00`.
- N5 Invisible: U+0085, U+200B, U+FEFF, U+2028 and U+00AD each in row 2 of the billing golden refuse that row alone
  `NATIVE_CHARACTER`; a tab inside a quoted cell is still admitted; a U+200B in `kobo-ledger-expenses`' dropped
  `Phone` column is admitted.
- N6 Join and digest: blanking `Line` in the budget's row 2 writes no `source_record_id`; row 2's `Site` set to
  `KOBO:001` refuses row 2 alone `NATIVE_FORMAT record.source_record_id`; the digests are the literals of §4.2 and
  §4.1; changing row 2's amount to `3421` changes only row 2's digest.
- N7 Profile validation: each of these is `ProfileInvalid` naming the key: unknown top-level key; `schema_version` 2;
  a map on `body.counterparty_ref`; `body.category` without a map; two columns writing `site_code`; `record_id_join`
  with a column also writing `source_record_id`; `source_system` `illustrative-x`; `thousands_mark` equal to
  `decimal_mark`; `timezone` `Mars/Base`; `scale` on a text path; version `column` with no column writing
  `source_version`; rev 2: version `constant` with a column writing `status` (`version`); one column (`columns`);
  `scale` `"0"`, `"-1"` and `"1e3"` (each `columns.<i>.paths.<j>.scale`).
- N8 `render_layout` on a compiled profile raises `NATIVE_RENDER <id> profile`; a planted illustrative layout whose
  column writes `body.method` with no map fails `check_layout`.
- N9 `CODED_PATHS == frozenset({"kind", "status", "subject.kind", "quantity.unit", "body.line_type",
  "body.tariff_class", "body.method", "body.category", "body.direction", "body.read_type", "body.contract_type",
  "body.factor_id"})`, written out in the test (handshake R2).

**Service, no database** (`backend/tests/test_3a6_source_profiles.py`; 3A2's in-memory world plus a
`ProfileMemoryStore` mirroring §5; Ana ANALYST, Fiona FINANCE):
- A1 Admit `kobo-ledger-expenses` (Ana): row v1, reader `profile.kobo-ledger-expenses.v1`, `sample_rows` 4,
  SHA-256s of the three files; admitting the same bytes again is `ALREADY_ADMITTED`, nothing written.
- A2 Changed profile (rev 2: v1 plus `personal` `[["body.counterparty_ref", "P"]]`; same sample and expected file)
  admits as v2; uploads naming v1 are 422
  `UPLOAD_READER_SUPERSEDED` with `latest` v2; a v2 with `source_system` changed is `PROFILE_LINEAGE`; a new
  `profile_id` with the same `source_system` is `PROFILE_SOURCE_SYSTEM_TAKEN`. (Rev 3: this v2 is admitted only while no
  upload with the system is accepted; A2b below.)
- A2b Personal change after data (D-3A6.18): after U1's accepted upload, the v2 of A2 is `PROFILE_LINEAGE {where:
  "personal"}` with the words in D-3A6.18, nothing written; a v2 that changes only the sample, or `personal` listed in
  another order, is admitted; the same v2 before any accepted upload is admitted (A2).
- A3 Status: ILLUSTRATIVE with `real_data=True` is `PROFILE_STATUS`; PINNED with `real_data=False` is
  `PROFILE_STATUS`.
- A4 Sample: 2 data rows is `ADMIT_SAMPLE_SIZE` (2); a row with `Litres` `4OO` is `ADMIT_SAMPLE_ROW` row 4
  `NATIVE_FORMAT`, text "Row 4 of the sample is refused: Litres: this value is not written the way this layout reads
  it (for example, a date in another order)."; a header renamed is `ADMIT_SAMPLE_FILE NATIVE_HEADER`; the profile
  bytes with a leading UTF-8 BOM are `PROFILE_INVALID json`.
- A5 Expected: PL-1002's amount written `475.0` in the expected file is `ADMIT_EXPECTED` row 5, where
  `amount.value`; one record missing is `ADMIT_EXPECTED_COUNT` 3 vs 4; the expected bytes with a leading UTF-8 BOM are
  `ADMIT_EXPECTED_FILE`.
- A6 Probes refuse a lax engine: `run_probes` on the `kobo-ledger-expenses` rows with five stub `read` functions,
  each `read_rows` with one fault: (a) drops short rows, (b) admits U+200B, (c) writes the raw cell on a map miss,
  (d) writes the raw cell on a bad date, (e) writes `"0"` for a blank amount, (f) ignores the header's order. Each
  gives `ADMIT_PROBE` P2, P3, P4, P5, P6, P1 respectively; the true `read_rows` passes all six.
- A9 Coverage (D-3A6.11): (a) the kobo profile with `State` map `{"Invoiced": "INVOICED", "Paid": "PAID", "Quote":
  "QUOTE"}` (rev 3, D-3A6.19: one to one; `QUOTE` is an expense status) is `ADMIT_MAP_UNCOVERED {header: "State", value: "Quote"}`; (b) the kobo sample with every `Litres` cell
  emptied is `ADMIT_COLUMN_EMPTY {header: "Litres"}`.
- A10 Ambiguity (D-3A6.11): (a) the kobo sample with `Txn Date` `11/10/2026 09:00`, `12/10/2026 09:00`,
  `10/10/2026 17:00`, `09/10/2026 17:30` is `ADMIT_DATE_AMBIGUOUS`; (b) the kobo sample with `Net (USD)` `500`, `475`,
  `1.200`, `450` is `ADMIT_NUMBER_AMBIGUOUS`; the unchanged kobo sample passes both checks. (Steps 4a to 4c run
  before step 5, so A9 and A10 use the unchanged expected file.)
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
  held). Race (D-3A6.15): on a fresh world, the template golden's KOBO-001 file is submitted (waiting); the kobo
  profile file is submitted with `held_uploads` patched to return `()` for that one call (the concurrent submit that
  passed its check first); Fiona accepts the profile upload (ACCEPTED); accepting the template upload is 409
  `UPLOAD_SOURCE_SWITCHED` with `system` `lakeside-purchases-ledger`, and it stays waiting.
- U4 Unknown `profile.nope.v1` is 422 `UPLOAD_READER_UNKNOWN`; a tampered `profile_json` in the memory store is 500
  `COMMERCIAL_STORE_FAULT`; a CSV profile with media type XLSX is 415.
- U5 `field_label` for the profile: `record.amount.value` → `Net (USD)`; `row.6` → `row 6`; an upload submitted
  through v1 and read through `get` after v2 is admitted still names `Net (USD)` (handshake P6).
- U6 Corrections flow (D-3A6.16): after U1, the same export with PL-1001's `State` `Paid` is 1 REVISED, 3 UNCHANGED.
- **Contract suite:** `test_3a3_source_contract.py` runs C1 to C10 over `CONTRACT_CASES + PROFILE_CASES` with the
  fields of §2.10; `assert_coded_probes` passes for all five cases; `test_coded_check_fails_on_an_unchecked_layout`
  (§2.10) passes.
- S1 extended (§2.9): every `PLANTED_TAGGED` row gives exactly its tags; `test_s1_allowlists_are_exact` passes.

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
carries `source_system` and `site_codes`), then U3's race on Postgres (the second acceptance 409, no row written).

**Regression:** 3A3's contracts, service, single-writer, emulator, loader and Postgres files; 3A2's service, API and
Postgres files; `test_3a4_commercial_months.py`; `test_on1_*`; check-all.

## 7. Done (questions; each can fail)

1. Do the four illustrative layouts read and render exactly as before (N1, 3A3 contracts 1 and E7's SHA-256 pins)?
2. Does each fixture profile read its sample to its hand-written records (N2, N3), and does every transform give the
   literal of N4?
3. Is a profile admitted only after its sample reads to the expected records, exercises every written column, every
   map value and the format's order, and every probe refuses what it must (A1, A4 to A6, A9, A10), with nothing of
   the sample stored (A8)?
4. Does an admitted profile read uploads through 3A2's intake unchanged, pseudonymising refs and dropping dropped
   columns (U1, U2, C1 to C10 on the profile case)?
5. Is a second source system for the same source type and Site refused at the intake, on check, submit and (under
   the lock) acceptance, while another Site or a declined upload is not (U3, Q3)? Do corrections flow (U6)?
6. Are invisible characters beyond C0 refused per row (N5, P3)?
7. Does the suite require a probe for every column writing a coded path, derived from the canonical side and not from
   the layout's maps, and does `check_layout` refuse an unmapped coded path (`test_coded_check_fails_on_an_unchecked_layout`,
   N7 to N9)?
8. Does each S1 plant give exactly its clause's tags, and do the allowlists equal the scan (§2.9)?
9. Does a new layout need no code: a profile file plus `source_profile admit`, then the loader or the route (L7, U1,
   K1)?
10. Does each planted violation in the reviewer guide fail its named test?
11. Is nothing changed beyond §3's files, the fixtures and tests of §4 and §6, `source_contracts.py`, the
    `test_3a3_*` files named in §6 (extensions only, plus §2.10's listed literal and word-pin changes),
    `test_3a2_commercial_upload_service.py` and the 3A2 API test (the `reader` signature only, and only if they fail),
    `test_3c1a_person_work.py` (`SPEC_ROLES` gains `"commercial.profile_admit": (ANALYST, FINANCE)`, one line), and the
    packet?

12. (rev 4) Is every upload's parse inside the envelope (E7), is each breach a `NATIVE_TOO_LARGE` refusal after which
    the next upload reads (E1 to E6), are legitimate verdicts unchanged (E8 and the packet's differential), and are
    the limits pinned and the log free of content (E0, E9)? D-3A6.24's bounds (B1 to B3) are checked but do not block
    the merge (D-3A6.26). Question 11's list gains `commercial/envelope.py`, `test_3a6_parse_envelope.py`, and the
    S1 test's `S1-DYN` addition and plant.

Packet: `specs/3A6-source-profiles/packet.md` (module paths, fixture SHA-256s, plants, mid-build count, S1 residual).

## 8. Units

| Unit | Content | Commit |
|---|---|---|
| 1 | Engine growth (§2.2), `xlsx.py`, transforms, `profiles_v1.py` with `run_probes`, the coded rule, fixtures and `make_budget_xlsx.py`, N1 to N9 (no migration; may start before 3B7a merges, D-3A6.12) | 1 |
| 1 | Migration 0067 (base holds 0066), store and adapter with the acceptance re-check, `profiles.py` with coverage (4a to 4c), the intake changes (§2.6), `tenant_by_slug`, words, guard, A1 to A10, U1 to U6, Q1 to Q3 | 2 |
| 0.75 | The command, the loader (§2.8), S1 (§2.9), the suite changes (§2.10), L5 to L9, K1 to K4; check-all; packet | 3 |
| 0.75 | Fix round r5 (rev 4): the envelope (§2.12), wiring, `LayoutReader` profile source, `NATIVE_TOO_LARGE` and words, S1-DYN addition, E0 to E9, V33 to V37 | r5-1 |
| 0.5 | Fix round r5: N8 to N10 bounds, B1 to B3, V38 to V40, the code switch in the r3/r4 tests, packet (table, differential) | r5-2 |

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
| Q6 | An export naming Sites by name (`Kobo`) rather than code (handshake R15) | Not this unit: no map on `site_code`; such an export goes to the reshaping fallback (RC2), timed; the DDR runbook picks an unseen shape that carries Site codes. **Owner to weigh in** only if the first operator's export names Sites by name |
| Q7 | (rev 4) Merge with the N8 to N10 bounds still under review? | The envelope blocks the merge; the three bounds are built in the same round but a defect in one is a Low follow-up unless it refuses a legitimate file (D-3A6.26, owner-away row 29). **Owner to weigh in** on return if the merge should have waited for every bound |
