# 3A6 rulings

Architect (Claude), 2026-11-20. Each ruling: what, why, and (where a residual is closed) the class and the sweep (W6).
Applied by default; the open questions with defaults are in `spec.md` §10.

## D-3A6.1 A source profile is a JSON data file compiled to the one engine's `Layout` (amends D-3A3.2)

- **Ruling.** A profile (spec §2.1) compiles to a `Layout` through `native/profiles_v1.py`. The engine in
  `layouts_v1.py` gains optional file rules (CSV encoding and delimiter, header row, XLSX sheet), value rules (decimal
  and thousands marks, negatives, date, time and month forms, time zone), per-path types and scales, a joined record ID
  and a row digest version. Every new field defaults to today's behaviour, so the four illustrative layouts read and
  render byte for byte as before (done 1). `read_layout` splits into `split_file` and `read_rows`, both public.
- **Why.** §7.2: "only transport and profile change; the parser ... do[es] not". D-3A3.2 put the native shape in one
  engine so a new export is a new value, not a new parser; the transforms are what a real export needs (a decimal
  comma, a day-first date, a local time with no offset, a header under a title block, a workbook). Two engines would
  drift; one engine with defaults keeps 3A3's contract and its pins.

## D-3A6.2 Profiles live in the tenant's database, admitted by a command; the sample is never kept (RC4)

- **Ruling.** New append-only table `commercial_source_profile` (migration 0067) holds each admitted version: the
  profile text, its SHA-256, the SHA-256 of the sample and of the expected file, the row count, who admitted it and in
  which role. `python -m assetops_backend.source_profile {check,admit,list}`. Uploads name `profile.<id>.v<n>`; only the
  latest version of a profile reads (`UPLOAD_READER_SUPERSEDED` names it).
- **Why.** An operator's sample holds customer and staff references, so it may live only in that operator's database
  (RC4) and only as long as needed; its hash pins the profile to it without keeping it. Profiles in the repository would
  need a code review and a merge per operator, which is the "code change" the owner asked to remove (RC2), and would
  put a real operator's export shape beside other tenants'. §6.5's "each source system is registered per tenant with
  its profile" is this table. Only the latest version reads, so an analyst who fixed a profile cannot upload through
  the broken one by habit.

## D-3A6.3 Admission is the contract test as product code, pinned by hand-written records

- **Ruling.** `SourceProfiles.admit` runs, in order: the profile's validity, its status against the database's
  real-data switch, lineage, the sample read with no refusal, the reader's records equal to the analyst's hand-written
  expected records, and six probes (P1 header, P2 short row, P3 invisible characters, P4 every map, P5 every typed
  path, P6 every blanked column invents nothing). The pytest suite (C1 to C10) also runs over the committed
  illustrative profile through the intake.
- **Why.** 3A3 made `READERS` admission mechanical with a pytest case per reader (D-3A3.5), but a pytest case is code,
  and a real operator's sample cannot enter the repository. The probes are the store-free part of C3, C8 and the
  coded check, run on the operator's own sample; the store-dependent part (idempotency, pseudonymisation, acceptance)
  is 3A2's intake, unchanged, which every profile upload goes through. Independence (W2): the expected records are
  written by the analyst from the sample, not produced by the engine, so a profile cannot pass its own mistake.
  Status follows the database (as provenance does, D-3A3.10): `PINNED` on an operator database, `ILLUSTRATIVE`
  elsewhere, so a rehearsal profile cannot pose as a real one.

## D-3A6.4 Invisible characters beyond C0 are refused per row (3A3 residual; amends D-3A3.9)

- **Ruling.** A cell of a column that writes a path is refused (`NATIVE_CHARACTER`, its row alone) when it holds a
  character of Unicode category Cc (C1 controls U+0080 to U+009F included), Cf (U+200B to U+200F, U+FEFF, U+00AD, the
  bidirectional marks and the rest), Zl, Zp or Cs, besides 3A3's set; tab, LF and CR stay text. Dropped columns are not
  checked. The words now say "such as a NUL byte or an invisible mark".
- **Why.** D-3A3.9's reason applies unchanged: an invisible character inside a reference splits one customer into two
  pseudonyms. 2a already refuses C0 and C1 in refs (`_REF_BANNED`), but not zero-width or line-separator characters,
  which spreadsheet exports do carry (U+FEFF from a pasted cell, U+200B from web copies). Refusing in the engine,
  before 2a, gives the person one plain sentence for the whole class.
- **Class and sweep.** Class: an input check written as a code-point list where the risk is a Unicode category. Sweep:
  every character check on operator text: `layouts_v1._CONTROL` (now by category), 2a `_REF_BANNED` (C0 and C1; left:
  2a is a protected v1 seam, D-2A.2, and the engine now refuses the rest before 2a sees it), 3A2
  `has_control_character` (the two free-text inputs, file name and decline reason; C0 only; left: they are shown, not
  joined on, so an invisible mark there splits nothing), ON1's onboarding file (closed patterns, ASCII). No other
  site found.

## D-3A6.5 One source system per source type per Site, enforced at the intake (3A3 residual; amends D-3A3.7, D-3A3.14)

- **Ruling.** `CommercialUploads._check` refuses (409 `UPLOAD_SOURCE_SWITCHED`) a file whose kept records name a Site
  for which the tenant holds a waiting or accepted upload of the same source type from another source system. The
  emulated loader's own checks compare source types within a directory and source systems across runs (not reader IDs);
  the intake rule is the authority.
- **Why.** The double count D-3A3.7 guards against comes from the same money arriving under two record identities, and
  a record's identity is `(tenant, source_system, source_record_id)` (3A1). Reader IDs were the wrong key: two versions
  of one profile are two readers with one source system (their records revise each other, no double count), while the
  template and a profile for the same ledger are two systems (they would double count). D-3A3.14's reader-ID rule also
  lived only in the emulated loader, while real files arrive through the route. Narrowing by Site keeps a legitimate
  case: an operator whose Sites run on two vending platforms.
- **Class and sweep.** Class: a cross-upload invariant enforced in a caller instead of the one writer. Sweep: every
  caller of `CommercialUploads.check` and `.submit`: the route (now covered by the intake), the emulated loader (keeps
  an earlier, stricter, whole-directory check), ON1's command (submits nothing). `held_uploads` is the one read; it
  gains `source_system` and `site_codes`.

## D-3A6.6 Coded paths must be mapped, and the suite derives its probes from the canonical side (3A3 residual)

- **Ruling.** `CODED_PATHS` (the twelve closed-vocabulary paths: kind, status, subject kind, quantity unit and the body
  enums including `factor_id`) is fixed in the engine. A column writing one must carry a map; a map is allowed only on
  one. `check_layout` enforces this for every layout. The contract suite replaces `mapped: (header, value) | None` with
  `coded`, one probe per coded column, and asserts that the probed headers equal those whose column writes a coded path,
  computed from its own hand-written copy of the twelve paths.
- **Why.** The residual: a case with `mapped=None` was accepted when the layout declared no map, so a layout that wrongly
  omitted a map would hide, and an unmapped `factor_id` lets an operator heading such as `marketing` through as a factor
  nobody declared (2a checks only its pattern). Deriving from the canonical side makes the probe depend on what the
  column writes, not on what the layout claims. The sweep found a second gap of the same class: the illustrative
  expenses layout maps `Status`, but its case probed only `Category`; it now probes both.

## D-3A6.7 The single-writer test sees dynamic imports and names built from strings (3A3 residual; amends D-3A3.12)

- **Ruling.** S1 also fails on: a dynamic import call outside a reviewed allowlist (exactly the set found on `main`);
  any dynamic import naming the commercial package, allowlisted or not; outside the writers, a string constant
  `"ingest"` or `"CommercialRecords"`; in a module importing the commercial package, a non-constant `getattr`-family
  name or `operator.attrgetter`/`methodcaller`; `eval`, `exec` or `compile` in the commercial package or the native
  engine. Five planted sources prove each (rev 2: one plant per clause, and `sys.modules`/`runpy` rules: D-3A6.14).
- **Why.** D-3A3.12 left these to review. A profile is data, and data must never become a way to reach code: the
  `eval` rule pins that; the others close the dynamic routes to `CommercialRecords.ingest`. No current file holds the
  `"ingest"` literal, so the rule costs nothing today. Still not seen, stated in the packet: a module importing nothing
  commercial that calls `.ingest` on a service handed to it (ten `.ingest` attributes of other services make a blanket
  rule noisy).

## D-3A6.8 Only the latest admitted version of a profile reads

- **Ruling.** Reader IDs are `profile.<profile_id>.v<version>`; an older version is refused with the latest's ID. The
  loader resolves `<SLUG>.profile.<profile_id>.<ext>` to the latest.
- **Why.** Versions of one profile share a source system, so their records revise each other; reading through an old
  version would re-introduce the fault the new version fixed. Naming the latest in the refusal tells the person what to
  do.

## D-3A6.9 Single-sheet XLSX through the standard library, with Excel's 15 digits

- **Ruling.** `native/xlsx.py` reads exactly one sheet with zipfile and ElementTree, refusing a DTD or entity, oversize
  members, the 1904 date system, error and ISO-date cells. Numbers are rounded to 15 significant digits and written in
  plain notation; a typed date, datetime or month column also reads an Excel serial.
- **Why.** The owner scoped "CSV and single-sheet XLSX" (§0.1 row 5); the contracts package is standard library only,
  and no XLSX library is installed. Excel stores money as binary floats and shows 15 significant digits, so
  `874.99999999999989` is the 875 the person typed; rounding to 15 digits recovers it exactly without inventing
  precision. Several sheets or merged cells go to the reshaping fallback (RC2), timed.

## D-3A6.10 The emulated loader takes admitted profiles; the command does not refuse operator databases

- **Ruling.** The loader admits `<SLUG>.profile.<profile_id>.csv|xlsx` once that profile is admitted for the tenant.
  `source_profile` composes through `commercial_upload_settings` and so runs on an operator database only with the
  real-data switch on, and elsewhere only with it off.
- **Why.** `DDR` must load an unseen shape "through a new profile with no code change" on the rehearsal tenant, and
  its runbook drives the loader. A pinned profile belongs where the operator's data lives (D-3A6.2), so the admission
  command must run there; the settings switch already refuses a mismatch both ways (RC4-F1).

## D-3A6.11 The sample must exercise the whole profile: every map value, every written column, and the format's order (handshake R1, R9)

- **Ruling.** Admission (spec §2.5 steps 4a to 4c) refuses: a column with a path that no sample row fills
  (`ADMIT_COLUMN_EMPTY {header}`); a map key that no sample row's cell equals (`ADMIT_MAP_UNCOVERED {header, value}`);
  a profile whose `date_format` is day-month ambiguous (`DD/MM/YYYY`, `MM/DD/YYYY`, `DD-MM-YYYY`, `DD.MM.YYYY`) when no
  grammar-read date, datetime or month_of cell of the sample fails under the swapped day-month order
  (`ADMIT_DATE_AMBIGUOUS`); and a profile whose marks are `{".", ","}` when no grammar-read number cell fails under the
  swapped marks (`ADMIT_NUMBER_AMBIGUOUS`). Each check applies only where the sample reads that kind of cell through
  the grammar (an `XlsxNumber` cell skips the grammar and is never ambiguous).
- **Why.** The expected records are independent of the engine (W2) but prove only what the sample exercises: a map
  entry never used, a column never filled, or a date order no value disambiguates is a line of the profile nobody has
  checked against a hand-written record. A wrong entry (`"Quote": "INVOICED"`) would then turn quotes into fuel cost
  on the first real upload, and 3A7 would reconcile against it. Requiring the sample to cover each line makes the
  expected-record compare reach every line, so coverage is the whole fix: a covered entry is checked by the analyst's
  own record for that row.
- **Class and sweep.** Class: a profile line admitted without a sample value reaching it. Sweep over every profile
  key that changes a value: `columns[].paths` (4a), `map` (4b), `date_format` (4c), `decimal_mark`/`thousands_mark`
  (4c), `time_format` (covered: any datetime cell read through the grammar exercises it, and 4a guarantees one),
  `month_format` (unambiguous by construction: every form fixes the order), `timezone` (covered by the expected
  `occurred_at` offset), `scale` (covered by 4a and the expected value), `negative` (residual, stated in the packet:
  a sample with no negative value leaves the parentheses rule unexercised; a wrong choice refuses negatives
  `NATIVE_FORMAT`, it cannot misread them), `record_id_join` and `version` (covered by the expected IDs and versions).
  Residual: an XLSX sample whose numbers are all native leaves the marks unexercised; a later text cell is read with
  them (stated in the packet).

## D-3A6.12 Migration order: 3B7a's 0066, then 3A6's 0067, then 3A7's 0068 (handshake P1, 3A7 P1)

- **Ruling.** `3B7a` merges before `3A6` reaches its migration (the coordinator, 2026-11-20: 3B7a is in its last fix
  round). `0067_source_profile` revises `0066_structure_snapshot`; `0068_commercial_reconciliation` revises
  `0067_source_profile`. No renumbering. 3A6 may branch off `main` before 3B7a merges and build commit 1 (contracts
  only, no migration, no Postgres test); commit 2 starts only on a base that holds
  `backend/migrations/versions/0066_structure_snapshot.py` (merge `main` into the branch once 3B7a has merged; never
  branch off the unmerged 3B7a branch, which may still change). Each migration test asserts its own chain link
  (`(revision, down_revision)`), never "is head" (D-3B7A.14).
- **Why.** Two migrations revising 0065 would give `main` two heads; a branch revising a revision it does not hold
  breaks every Postgres test at `upgrade head`. Commit 1 needs no database, so ordering costs no wait.

## D-3A6.13 XLSX cells: a number in a compact month column is text, serials have a window, bad cells are cell marks (handshake R4, R7, R8)

- **Ruling.** (a) Under `month_format` `YYYYMM`, an `XlsxNumber` cell of a `month` or `month_of` column is read through
  the grammar as its text (`202610` → `2026-10`). (b) Every serial read as a date must have an integer part from 61
  (1900-03-01) to 73050 (2099-12-31), else `NATIVE_FORMAT` (no `OverflowError` can arise; Excel's fictitious
  1900-02-29 is excluded). (c) `xlsx_rows` never refuses a row: a `t="e"` or `t="d"` cell, or a `<v>` that is not a
  finite decimal (`NaN`, `Infinity`, `sNaN`, text) becomes an `XlsxBad("")` cell (a `str` subclass marker); `read_rows`
  refuses the row `NATIVE_FORMAT record.<first path>` only when the marker sits in a column with a path, so dropped
  columns stay unchecked (as D-3A6.4 for characters). (d) Every member read is decoded strict UTF-8 (a leading BOM
  dropped) before the `<!DOCTYPE`/`<!ENTITY` test and the parse; a member that does not decode is `NATIVE_WORKBOOK`.
  (e) Every `zipfile.BadZipFile`, `zipfile.LargeZipFile`, `zlib.error`, `NotImplementedError`, `RuntimeError`,
  `EOFError`, `KeyError` (missing member), `UnicodeDecodeError` and `xml.etree.ElementTree.ParseError` raised inside
  `xlsx_rows` is `NATIVE_WORKBOOK`; nothing else is caught.
- **Why.** An ERP's month column stored as a number is common, and read as a serial it lands in the year 2454, which
  2a's period pattern admits: wrong-month money accepted silently. A window turns that and every other absurd serial
  into a plain row refusal instead of a 500. Cell marks keep the "dropped columns are never read" rule true for
  workbooks as for CSV. The zip and XML error classes are the reader's input faults and must read as one plain
  sentence.

## D-3A6.14 S1 has one plant per clause, each firing only its own clause; sys.modules and runpy are rules (handshake R3, P4)

- **Ruling.** Every S1 violation string begins with its clause tag. The clauses and their plants are spec §2.9's
  table; the plant test asserts, per plant, the exact set of tags. `sys.modules` outside an allowlist (the scan's
  two tools), any `sys.modules` key naming the commercial package anywhere, and any `runpy` import outside an
  allowlist (empty at `main`) are rules; `importlib.__import__` and `builtins.__import__` join the dynamic-import
  set. `eval`/`exec`/`compile` mean the bare builtins and `builtins.<name>` (so `re.compile` is not flagged, with a
  negative plant). The allowlists are the scan's findings at branch time, and a test fails on a stale entry.
- **Why.** A plant caught by an earlier clause proves nothing about the clause it was written for; with tags, a
  no-op clause fails its own plant. `sys.modules[...]` and `runpy` reach a module without an import statement, the
  same route the dynamic-import rule closes.
- **Residual (packet).** S1 is a tripwire for accidental routes, not a sandbox: a module that imports nothing
  commercial and is handed a service, attribute access by non-constant name in such a module, `__getattribute__`,
  `vars(obj)[name]` with a non-constant name, and a non-test tool named `test_*.py` (hidden by the scan's test-file
  filter, e.g. `tools/checks/test_event_register.py`) are left to review.

## D-3A6.15 The source-switch rule is re-checked under the tenant's lock at acceptance (handshake R11; amends D-3A6.5)

- **Ruling.** `write_intake` with an ACCEPTED `decision`, under the tenant's lock after the already-decided check and
  before `decide`, refuses (`UploadSourceSwitched(system)`, 409 `UPLOAD_SOURCE_SWITCHED`, the upload left waiting)
  when another **accepted** upload of the tenant has the deciding upload's `source_type`, a different
  `source_system`, and shares a `month_site_code` value (NULL equal to NULL). Check and submit keep comparing against
  waiting and accepted uploads (§2.6).
- **Why.** The check at submit runs outside the lock, so two submits racing each other both pass; only the one writer
  can decide atomically. At acceptance only accepted uploads count, or two racing waiting uploads would block each
  other forever.

## D-3A6.16 A profile for a mutable ledger versions by row digest (handshake R10)

- **Ruling.** `compile_profile` refuses `{"from": "constant"}` when any column writes `status`
  (`PROFILE_INVALID version`). The kobo fixture versions by `row_digest`.
- **Why.** A constant version on records whose status or amount changes turns every correction into
  `INTAKE_VERSION_CONFLICT`, so corrections never flow, and 3A7 reconciles on corrections. A written `status` is the
  plain sign of a mutable record; the digest of the normalised row is §6.5's answer for sources without a version.
  The illustrative collections layout (constant, with `Status`) is a 3A3 layout, not a profile, and is unchanged.

## D-3A6.17 The commands find a tenant by slug through the accounts service (handshake P3; 3A7 P3)

- **Ruling.** `AccountService.tenant_by_slug(slug: str) -> UUID | None` (delegating to `AccountStore.tenant_by_slug`,
  returning its ID) in `accounts/service.py`; `source_profile` and `reconcile_month` use it for `--tenant`; None is
  `TENANT_NOT_FOUND`, exit 2.
- **Why.** The accounts service is the one reader of tenants; a second slug lookup in the commercial store would
  duplicate it.

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, on `task/3A6-3A7-handshake` c01baa35a. Every answer is folded into `spec.md` rev 2;
section numbers below are rev 2's. A gate named here has a plant in `reviewer-guide.md` rev 2 that fails it.

### Reviewer

- **R1 (High).** Accepted: D-3A6.11. Steps 4a (`ADMIT_COLUMN_EMPTY`) and 4b (`ADMIT_MAP_UNCOVERED`) in §2.5. The kobo
  map loses `"Quote"` (§4.1); no sample row is added. Tests A9 (a), (b). Gates: V22 (drop 4b) and V23 (drop 4a) fail A9.
- **R2 (High).** Accepted. `source_contracts.py` gains `coded_headers(layout) -> set[str]` (from
  `CODED_PATHS_EXPECTED`) and `assert_coded_probes(case, layout)`; the suite calls the latter. New tests:
  `test_3a3_source_contract.py::test_coded_check_fails_on_an_unchecked_layout` builds a `Layout` directly (no
  `check_layout`) with a column `Method` → `body.method` and no map, and asserts `assert_coded_probes` raises with
  `coded=()`; N9 asserts `CODED_PATHS` equals the twelve written out. Gates: V10 (derive from maps) fails the first;
  V25 (drop `body.factor_id` from `CODED_PATHS`) fails N9.
- **R3 (High).** Accepted: D-3A6.14. §2.9 rewritten as a clause table (eleven clauses) with 25 positive plants and
  3 negative plants, each with its `rel` and its exact tag set. `sys.modules`, `runpy` and `importlib.__import__` are
  rules, not residuals. Gate: removing any one clause fails its own plant(s) (V18, V19, V26, V27, V31 named).
- **R4 (High).** Accepted: D-3A6.13 (a), (b), (c). N4 gains literals: `YYYYMM` `XlsxNumber("202610")` → `2026-10`;
  `Mon-YYYY` `XlsxNumber("202610")` fails; serials 60 and 73051 fail, 61 → `1900-03-01`, 73050 → `2099-12-31`,
  `2958466` fails (no exception). N3 gains `<v>NaN</v>` and `<v>Infinity</v>` in row 3 (row 3 alone `NATIVE_FORMAT`).
  Gates: V23b (serial window removed) and V32 (`YYYYMM` number read as a serial)
  fail N4.
- **R5 (Medium).** The header comparison moves to `read_rows` (its first step); `split_file` refuses only a missing
  header row. Profiles need 2 to 60 columns (P1 always swaps two different headers). A6 gains (f) "ignores header
  order" → `ADMIT_PROBE P1`. Gate: V28 (compare in `split_file` only) fails A1 and A6 (the true engine then fails P1).
- **R6 (Medium).** P6 judges the reader's result only: the row is refused by the reader, or its record holds none of
  the column's paths. `run_probes` lives in `native/profiles_v1.py` with the signature in §2.5 and returns the first
  failing `(probe, where)` or None; the backend wraps it.
- **R7 (Medium).** Accepted: D-3A6.13 (c). N3 gains: a budget variant with a sixth column `Note` (dropped) holding an
  error cell and a U+200B text cell is admitted. Gate: V30 (judge marks in dropped columns) fails it.
- **R8 (Medium).** Accepted: D-3A6.13 (d), (e). N3 gains four cases, each `NATIVE_WORKBOOK`: CRC broken (one byte of
  `sheet1.xml`'s stored data flipped), compression method 99, encryption flag set, `sheet1.xml` written UTF-16 with a
  BOM.
- **R9 (Medium).** Accepted, not a residual: D-3A6.11, step 4c. Test A10 (literals in §6); gate V29. The kobo fixture already
  disambiguates both (`21/10/2026`, `500,00`).
- **R10 (Medium).** Accepted: D-3A6.16. Kobo versions by `row_digest` (expected `source_version` literals in §4.1,
  computed by hand); `PROFILE_CASES` `versioning="digest"`; N7 gains "constant version with a `status` column"; U6: the
  same export with PL-1001 `Paid` reads 1 REVISED, 3 UNCHANGED.
- **R11 (Medium).** Accepted: D-3A6.15. U3 gains the race (literal in §6); Q3 runs it on Postgres. Gate: V24.
- **R12 (Medium).** The field stays: `admit_sample_row` is "Row {row} of the sample is refused: {field}: {reason}"
  with `field = reader.field_label(cut_path)` when the cut path starts `record.`; a row-level path (`row.<n>`) uses
  `admit_sample_row_whole`, "Row {row} of the sample is refused: {reason}". K3's literal holds.
- **R13 (Medium).** `native_encoding` becomes "the file is not text in the character encoding this layout reads."
  (pin in `test_3a3_source_contract.py:32` updated; listed in §2.10).
- **R14 (Medium).** `ZIP_STORED` for the fixture; X0 compares bytes.
- **R15 (Medium).** Not this unit: the reshaping fallback (RC2) covers an export naming Sites by name; queue Q6
  (default: no map on `site_code` now; the DDR runbook picks an unseen shape that carries codes). Owner to weigh in only
  if the first operator's export names Sites by name.
- **R16 (Low).** A join part containing `":"` refuses the row `NATIVE_FORMAT record.source_record_id`. N6 literal.
- **R17 (Low).** The digest branch is now live in the suite through kobo (R10). The budget workbook is not a suite
  case (the suite's mutation helpers are CSV); XLSX is covered by N3 and U2.
- **R18 (Low).** Profile and expected bytes are decoded strict UTF-8; a leading BOM is `PROFILE_INVALID json` /
  `ADMIT_EXPECTED_FILE`. A4 and A5 gain one case each.
- **R19 (Low).** `scale` fullmatches `(0|[1-9][0-9]{0,11})(\.[0-9]{1,12})?` and is not zero (no sign). U+00A0 and
  U+202F as thousands marks stay refused (`NATIVE_FORMAT`), intended: the analyst converts, timed.
- **R20 (Low).** Written as escapes in §2.5 P3: `"\x00"`, `"\x85"`, `"​"`, `"﻿"`, `" "`.
- **R21 (Low).** The words drop the ID: "These Sites already send this kind of export from another system. Use that
  system's export, or ask for the switch to be set up." `params.system` stays (the analyst's JSON).

### Implementer pre-flight

- **P1 (High).** D-3A6.12: `0067_source_profile` revises `0066_structure_snapshot`; no renumbering; commit 1 may start
  off `main` now, commit 2 only on a base holding 0066. 3A7's `0068` revises `0067`.
- **P2 (Medium).** Yes: `test_3c1a_person_work.py`'s `SPEC_ROLES` gains `"commercial.profile_admit": (ANALYST,
  FINANCE)` (one line, extension); added to done 11.
- **P3 (Medium).** D-3A6.17: `AccountService.tenant_by_slug`; `accounts/service.py` joins §3.
- **P4 (Medium).** Accepted as written: `DYNAMIC_IMPORT_ALLOWED` is the seven modules P4 lists (no
  `test_event_register.py`; `host/conftest.py` kept); eval/exec/compile per D-3A6.14; the filter's blind spot is
  stated (D-3A6.14 residual).
- **P5 (Medium).** Accepted: counts from `n`; `ContractCase.changed_amount` (default `"999.00"`, kobo `"999,00"`); the
  `NATIVE_ENCODING` and `NATIVE_CHARACTER` word pins updated; all in §2.10.
- **P6 (Medium).** Accepted: `get` resolves a `profile.*` reader by the stored ID through
  `SourceProfiles.reader(tenant_id, reader_id, superseded_ok=True)` (no `UPLOAD_READER_SUPERSEDED`); U5 reads through
  `get` after v2 is admitted.
- **P7 (Medium).** Accepted: the in-directory `EXPORT_PATHS_MIXED` check runs after step 5c, over every file with its
  source type resolved; `PROFILE_NOT_ADMITTED` comes first.
- **P8 (Low).** Edit the 3A2 tests only if they fail; done 11 permits the `reader` signature edit, it does not require it.
- **P9 (Low).** Residual for the packet: 3A6's and 3A7's `commercial.composition` edits change 3B7a's code digest,
  so snapshots built before these merges read stale; that is the digest working. The coordinator rebuilds any demo
  snapshots after 3A7 merges.
- **P10.** Noted; the digests and literals stand (kobo's new digests are in §4.1).

## Review answers (r1) (review `.agent/review-3A6-r1.md`, head f3ccbd0b1; Architect, 2026-11-21)

F1 (XLSX padding, High) and F2 (short CSV row, Medium) are straight fixes, no ruling; the reviewer's fixes stand
(sparse rows `{index: value}` with an N3 case at `XFD` and a plant; `_coverage` judges only rows of header width, A4 gains
the short-row case, `ADMIT_SAMPLE_ROW NATIVE_ROW`).

### D-3A6.18 A change to `personal` is refused once data is accepted; a migration step is a queued unit (F3; amends D-3A6.16, spec §2.5 step 3)

- **Ruling.** Step 3 refuses a new version whose `personal` set (compared as a set of `[path, class]`, order ignored)
  differs from the latest version's, when the tenant holds an ACCEPTED upload whose `source_system` is the profile's
  (`PROFILE_LINEAGE {where: "personal"}`, exit and HTTP as the other lineage refusals, nothing written). Before any
  accepted upload the change is admitted, as in A2. Words: "This profile already read accepted files, so who counts as a
  person cannot change under the same source. Records already stored would keep the old values. Ask for the migration, or
  keep the declaration as it is." The residual in `packet.md` is replaced (see below). The store answers the question through
  the existing `held_uploads(tenant, source_system)` (accepted only; no new port), in both the memory and Postgres mirrors.
- **Why.** The three ways out are all unsound today: the row digest ignores `personal`, so unchanged rows would conflict
  (INTAKE_VERSION_CONFLICT) on every upload; a new `profile_id` is closed by D-3A6.5's one-system rule, rightly; and
  folding `personal` into the digest revises every record, which stores a second copy while the raw first copy stays
  (the leak PII-1 forbids), and cannot cover `column` or `constant` versioning. A refusal that says so is honest and
  loses nothing: before data, the analyst fixes `personal` freely, and that is the moment the mistake is cheapest.
- **Queued, not built (owner RC4 gate: real data needs it first).** Unit `3A6b` "personal migration": a profile version
  on the same system where pseudonymisation applies forward; every already-stored raw value of the newly personal
  paths is listed for erasure (path, record ID, count; never the value); unchanged rows are matched by row digest
  of the normalised row (taken before pseudonymisation) and reported UNCHANGED, not conflicted. Default: Architect specs
  it when the owner names real data for a tenant; not demo-critical (illustrative data only).
- **Tests and plants.** A2b above (accepted upload refuses; unaccepted, set-equal, sample-only change admit); the
  Postgres file gains the same case (refusal reads the accepted row, nothing written). Plants: V33 (the check removed:
  A2b fails); V34 (counts waiting uploads too: A2's v2 before any acceptance fails, because U1 is only waiting there);
  V35 (compares `personal` as an ordered list: A2b's reordered case fails).
- **Packet residual, replaced.** "A change to `personal` after accepted data is refused (D-3A6.18); the migration is unit
  3A6b. Until then raw values from before the declaration cannot arise, because the declaration is fixed before the first
  accepted upload."

### D-3A6.19 Q1: profile maps stay one to one; A9 (a) uses `QUOTE` (mid-build Q1; F7)

- **Ruling.** Confirmed: the substitution stands, with `"Quote": "QUOTE"` in place of `DRAFT` (`QUOTE`, `INVOICED`, `PAID`
  are the expense statuses, `records_v1.py:205`). Spec A9 (a) amended to that literal; the test follows. Maps stay one to
  one for every layout (`check_layout` unchanged).
- **Why.** 4b fires on the uncovered key before any value is judged, so the value cannot change the test; one to one
  keeps 3A3's rule single. Many to one ("Paid", "Paid in full") is a real operator need, but it is a change to the
  shared `check_layout` and its rendering; queued with 3A6b, ruled when an operator export needs it.

### D-3A6.20 The Lows (F4 to F9) and the deviations

- **F4 confirmed.** A cell with `<f>` and no `<v>` becomes `XlsxBad("")`, so a written column refuses `NATIVE_FORMAT`; N3 case plus plant.
- **F5 confirmed.** Row number read with `re.fullmatch(r"[0-9]+", r, re.ASCII)`; `²` is `NATIVE_WORKBOOK`; N3 case plus plant.
- **F6 confirmed.** Flag any load reference (not only calls) to a name in `DYNAMIC_CALLS` or `EVAL_CALLS`, and count
  `ImportFrom("assetops_backend", names ∋ "commercial")` as importing the package; two plants, each failing only its clause.
- **F8 confirmed.** Use the spec's literal `2026-10-11 09:00` for `bad_clock`.
- **F9 confirmed.** The loader keeps `dispose` from `build_source_profiles` and calls it in `finally`.
- **Deviations.** 5 (`held_uploads` on `UploadMemoryStore`; done 11 lists it), 6 (`code_digest.py` allowlisted) and 7
  (coverage before row refusals, with F2's guard) accepted.

### D-3A6.21 Residuals recorded (reviewer's sweep)

Not fixed here, named in the packet: an interior U+00A0, U+3000 or U+034F inside a ref is not refused (Zs, Mn) and can
split a pseudonym (class: ref normalisation, queue with 3A6b); `fold=0` picks the first of a repeated DST hour (profiles
state a fixed-offset zone today; a DST zone needs its own ruling); the profile reader trusts admission and upload to
share one database.

### D-3A6.22 Fix round for the builder

F1, F2, F4, F5, F6, F8, F9, A2b with Postgres twin, A9 (a) `QUOTE`, the packet residual and done 11 wording; a Sonnet
fix round (ROLE_CONFIG), then a fresh Claude re-review.

## Review answers (round 5) (review `review.md` "Round 5", head 166942e7d, code at bc0c57ecf; Architect, 2026-11-21, owner away)

Decided under `owner/owner-away-architect-decides-2026-11-21.md`; the merge call (D-3A6.26) is logged as row 29 of
`specs/OWNER-AWAY/decisions-2026-11-21.md`. Probes behind the figures below ran in a scratch folder, since deleted:
the kobo fixture scaled to 10,000 rows (788 kB) and padded to 8,210 kB, each read in a forkserver child of Python
3.12.

### D-3A6.23 Every upload's parse runs in a worker process under hard OS limits (the class)

- **Ruling.** The step that turns upload bytes into rows or a batch object (`SourceReader.read` for every reader,
  `canonical-json-v1` included, plus admission's `split_file`) runs only in a short-lived child process. The new
  module `backend/assetops_backend/commercial/envelope.py` (spec §2.12) creates it. The child sets `RLIMIT_AS`
  512 MiB, `RLIMIT_CPU` 6 s (hard 7 s), `RLIMIT_FSIZE` 0 and `RLIMIT_CORE` 0 before it reads a byte. The parent
  waits at most 12 s of wall time, takes at most 32 MiB of result back, and runs at most 2 parses at once per server
  process. Any breach (memory, CPU, wall, result size, or a child that dies without answering) refuses the file with
  `NATIVE_TOO_LARGE` (D-3A6.25). The server logs the cause with no file content. There is no in-process mode and no
  setting that turns the envelope off. Tests may build a `ParseEnvelope` with lower limits; production builds it from
  `DEFAULT_LIMITS` only, and a test pins those values.
- **Why a process, and not a sixth list of bounds.** Five rounds each found a route the table did not list: padding,
  the header, inflated bytes, shared-string reuse, CSV rows, attributes and zip extras. Several of these costs sit
  inside the standard library's C parsers (expat's name cache, `csv` splitting, `zipfile`'s directory decode), where
  no Python-level counter can stop them in time. Listing resources cannot prove the list is complete. A kernel limit
  on the process bounds every route by construction, including the ones not found yet. Four other mechanisms were
  rejected:
  - A watchdog thread or `tracemalloc` in the server process cannot stop C code that is running, and a breach would
    take the server down with it.
  - cgroups or container limits are set when the app is deployed. The suite cannot test them, and they kill the
    whole server.
  - A hardened third-party parser breaks D-3A6.9 (standard library only) and does not cover CSV.
  - A process pool that keeps its workers would carry one tenant's memory into the next parse, and one breach
    breaks the pool (`BrokenProcessPool`).
  A fresh child for every parse costs about 11 ms with a forkserver that has preloaded `assetops_contracts.native`.
- **Why these limits (legitimate files are far inside them).** The plan's real exports are a few dozen rows. The
  largest legitimate file the intake accepts is 10,000 rows within 8 MiB. Measured in a forkserver child:
  - 10,000 kobo rows in 788 kB: 1.0 s CPU, VmPeak 64 MB, 3.2 MB pickled result.
  - The same rows padded to 8,210 kB: 1.4 s CPU, VmPeak 104 MB, 10.9 MB result.
  - The child's own baseline (forkserver plus preload) is about 64 MB of address space.
  That leaves about 5x headroom on memory, 4x on CPU, 8x on wall time and 3x on result size. The worst attack
  measured after the D-3A6.24 bounds is about 170 MB and 3 s (review round 5, residual), also inside the limits.
- **What the server pays per upload, worst case.**
  - The child: at most 512 MiB of address space, 6 to 7 s of one core, 12 s of wall time, then freed whole.
  - The parent: the upload (8 MiB cap, one copy to the pipe), its SHA-256, at most 32 MiB of result bytes and their
    unpickled objects (roughly 3 to 4 times that, transient), and 2a's `parse_batch` over the returned records.
  - Two at once per server process: about 1.4 GB and 2 cores for at most 12 s. The host has 22 GB and 8 cores.
  - Further uploads wait for a slot. They are not refused, and each slot frees within 12 s.
- **The boundary is exclusive (W6, the sweep).**
  - A test scans `backend/assetops_backend/` for calls of `read_layout`, `split_file`, `xlsx_rows`,
    `xlsx_sparse_rows` and `loads_canonical`, and for any `.read(` call with a `context=` keyword. Each may appear
    only in `commercial/envelope.py` and `commercial/readers.py`.
  - S1-DYN gains `set_forkserver_preload` (the envelope joins `DYNAMIC_IMPORT_ALLOWED`). Its preload names
    `assetops_contracts.native` only, so `S1-DYN-COMMERCIAL` does not fire.
  - Sweep result: the commercial intake (`uploads._check`), profile admission (`profiles` step 4) and, through them,
    the loader and the command are every caller.
  - Outside 3A6: the reading-upload intake (`reading_upload_api.py`, meter-reading CSVs) parses in the server
    process. It is queued as `ENV-1` (0.25 unit, not on the critical chain): route it through the same envelope
    after 3A6 merges.
- **Platform.** The envelope needs Linux (`resource`, forkserver). On any other platform the constructor raises; there
  is no fallback. The host and the deployment are Linux.

### D-3A6.24 The N8 to N10 bounds, kept as precision bounds under the envelope

Each one is cheap and keeps a common attack's cost well under the envelope. Each refuses `NATIVE_TOO_LARGE`.
- **N8, attributes (`xlsx.py`).**
  - A run check: XML forbids a raw `<` inside an attribute value, so the number of `=` between two `<` bounds one
    element's attributes. After decoding, if a member's `text.count("=")` exceeds `_ATTR_RUN_MAX = 4096`, `_parse`
    scans `re.compile(r"[^<]+")` matches and refuses one holding more than 4,096 `=`. The scan is linear.
  - A names check: at most `_ATTR_NAMES_MAX = 512` distinct attribute names per workbook, counted in
    `_Target.start`. This catches names spread over many elements, which builds expat's name cache.
  - `_Workbook` keeps only `date1904` (a string or None), not `dict(attrib)`.
  - Legitimate: SpreadsheetML uses well under 200 distinct attribute names, and Excel writes at most a few dozen
    attributes per element. A text run holding 4,096 `=` is not an operator's export.
- **N9, a logical CSV row (`layouts_v1.py` `split_file`).** `csv.reader` reads from a generator over
  `io.StringIO(text, newline="")`. The generator adds each line's length to a counter that the loop body sets back
  to zero after each row it receives. Past `_ROW_CHARS_MAX = 1,048,576` characters it raises
  `CanonicalRefused("NATIVE_TOO_LARGE", f"row.{reader.line_num + 1}")` before yielding the line. Quoted newlines no
  longer get past the cap. Legitimate kobo rows are a few hundred characters.
- **N10, the zip directory (`xlsx.py`, before `zipfile.ZipFile`).** Read the end-of-central-directory record from
  the last 65,557 bytes, using the last `PK\x05\x06`, as `zipfile` does. If an entry count, size or offset holds its
  zip64 sentinel, read the zip64 end record through its locator. Refuse more than `_ZIP_ENTRIES_MAX = 256` entries,
  or a directory over `_ZIP_DIRECTORY_MAX = 256 KiB`. A file with no end record is `NATIVE_WORKBOOK`, as today. A
  one-sheet workbook has about 10 entries and a directory of about 1 KiB. With 256 KiB, the quadratic extra-field
  decode costs at most about 0.1 s.
- **Why kept although the envelope holds.** Without them, a 6 kB file costs up to the envelope on every request:
  512 MiB and 6 s, twice at once. With them, the same files are refused in milliseconds, and the bounds table's worst
  case stays true and small.

### D-3A6.25 One honest reason for "too much": `NATIVE_TOO_LARGE` (closes the r4 open point)

- **Ruling.** New code `NATIVE_TOO_LARGE`, a whole-file refusal (422, path `json`, or `row.N` for the N9 cap). Its
  words, key `commercial_upload.reason.native_too_large`: "this file is too large or too complex to read in one
  upload; split it and upload the parts."
- **What it covers.** Every envelope breach and every resource bound:
  - the declared and inflated member caps (16 MiB and 64 MiB);
  - the element budget (`_WORK_MAX`), the character budget (`_CHAR_MAX`) and `_PAD_BUDGET`;
  - D-3A6.24's three bounds.
- **What keeps its code.**
  - Format problems stay `NATIVE_WORKBOOK`: not a zip, bzip2 or lzma, DTD, bad XML, a bad rels target, falling row
    numbers, `date1904`.
  - The row ceiling stays `CANONICAL_RANGE batch.records`, which already says how many records.
  - The CSV field limit stays `NATIVE_ROW`. `csv.Error` cannot tell it apart from a quoting error without matching
    its message, and the N9 cap sits above it. This is recorded, not fixed.
- **Why.** "Not an Excel workbook this layout can read" sends an operator looking for a format problem that is not
  there (review r4). Honest words are the owner's standing rule.
- **Served text.** 3A6 keeps D-SC1.27 (D-SC1.28 scope), so the key joins 3A6's `# 3A6` block and the legacy baseline
  at 3A6's merge.
- **Test changes.** The r3 and r4 adversarial tests that expect `NATIVE_WORKBOOK` for a budget breach change to
  `NATIVE_TOO_LARGE`. This is a listed literal change; their bounds on time and memory stay.

### D-3A6.26 What blocks the merge (owner-level; logged, row 29)

- **Blocks the merge:**
  - D-3A6.23's envelope, wired at both call sites, with spec §2.12's tests E0 to E9 and plants V33 to V37 passing;
  - D-3A6.25's code and words.
- **Built in the same round but not merge-blocking:** D-3A6.24's three bounds (B1 to B3, plants V38 to V40). Once
  the envelope holds, N8, N9 and N10 are each bounded with a coded refusal, inside the envelope's stated cost. Their
  severity falls to Low. A defect in one of these bounds is a Low follow-up, not a REVISE, unless it refuses a
  legitimate file.
- **Weighing.**
  - The exposure today is small. Only the analyst uploads, only emulated exports, behind authentication, and no real
    operator data before a signed agreement (RC4). On exposure alone, merging now would be defensible.
  - It does not merge as-is, for three reasons:
    1. This seam is where real operator exports will enter. The envelope is what makes it safe to open, and
       building it later means reviewing the same seam twice.
    2. Without a class bound, the review cannot converge: every round can find another route.
    3. The cost is about one unit and one verification review.
- **Taking it off the critical chain.** 3A7 commit 1 and 3C2 commit 1 wait only for migration 0067 as their base.
  They may start now from `task/3A6-source-profiles` at `166942e7d`, and merge `main` once 3A6 merges. Their own
  merges still wait for 3A6's. This amends the start condition in rows 6 and 7 of the owner-away dispatch list. The
  envelope round adds only an optional keyword argument to `LayoutReader` and leaves migration 0067 alone, so their
  base does not move.

### D-3A6.27 The review stop rule (the next review checks a closed list)

The next review (a fresh Claude reviewer; the reviewer guide's "Round 6") checks, and only these can REVISE:
1. **Exclusive.** Upload bytes are parsed only inside the envelope: test E7, plus the reviewer's own grep of the call
   sites.
2. **Bounded.** Each breach (memory, CPU, wall, result size, a child killed) refuses `NATIVE_TOO_LARGE`, never with a
   500, a hung request, or the server process dying or growing past the parent figures in D-3A6.23. After every
   breach the next upload reads normally: E1 to E6.
3. **Faithful.** Legitimate verdicts are unchanged: E8, and the packet's 600-case differential of in-process
   against envelope reads.
4. **Pinned and logged.** `DEFAULT_LIMITS` is pinned (E0). The log carries no file content (E9).
5. **Plants.** V33 to V37 each fail their named test.

D-3A6.24's bounds and the r4 table are checked for legitimate-file refusals only. A new route the reviewer finds is a
Low residual, not a REVISE, if it is refused with a coded reason inside the envelope's limits. It is a finding at its
own severity only if it escapes the envelope: work in the parent that grows with the input beyond D-3A6.23's parent
figures. Hunting further XML, CSV or zip shapes is out of scope for round 6.

### D-3A6.28 The fix round

- **Size.** About 1.25 units, in two commits:
  1. The envelope, wiring, `LayoutReader`'s profile source, the code and words, the S1 addition, E0 to E9 and V33 to
     V37 (about 0.75 unit).
  2. The N8 to N10 bounds, B1 to B3, V38 to V40, the code switch in the r3 and r4 tests, and the packet with the
     differential and the updated bounds table (about 0.5 unit).
- **Who.** A fresh Opus implementer, since this is new process code and not a fix against a written list
  (ROLE_CONFIG). The verification review uses D-3A6.27's list.
- **Spec.** `spec.md` §2.12 holds the exact design. The spec's status line records the round, at +1.25 units.
