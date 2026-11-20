# 3A3 rulings

Architect (Claude), 2026-11-20. D-3A3.1 to D-3A3.8 are applied by `spec.md` rev 1; D-3A3.9 to D-3A3.12 and the
handshake answers below by rev 2. D-3A3.1, D-3A3.6 and D-3A3.8 settle three of
the four residuals that 3A2's review and packet left open (`specs/3A2-commercial-file-intake/review.md` "Residual
risk", handshake answer R4); the fourth (a recreated key) is `ON1`'s, D-ON1.7.

## D-3A3.1 Every commercial record enters through 3A2's intake; emulators write files, never the store

- **Ruling.** No emulator, seed, bootstrap or bulk loader calls `CommercialRecords.ingest`. Emulators write native
  files; a loader submits them through `CommercialUploads` (read, check, pseudonymise, submit, accept). The class test
  S1 holds the seam: `CommercialRecords(` is built only in `commercial/composition.py`, `.ingest(` is called only by
  `commercial/uploads.py`, and `build_commercial_uploads(` has two callers (`main.py`, `load_emulated_exports.py`).
  `build_commercial_records` is deleted (no caller on `main`). This binds `DS3` too: it loads the generated world's
  canonical files through the same loader (it accepts `<tenant>.<source_type>.json`).
- **Why.** The review found that a direct 3A1 writer keeps raw refs while 3A2 stores pseudonyms, so one customer
  would not link across the two paths and the same version sent both ways ends in `INTAKE_VERSION_CONFLICT`.
  Pseudonymising in a second place would copy the key rule and the field table; routing through the one service
  keeps one rule, one acceptance record and one refusal vocabulary. The integration design already says emulators
  "write native-shape files into the same authenticated intake" (§7.2, §7.3). Volumes are small (D-3A1 Q2), so the
  in-process path costs nothing.
- **Sweep (W6).** `grep -rn "\.ingest(\|CommercialRecords(\|build_commercial_records"` over product, tools, host and
  simulator on `main` 6db81330a: the only product caller is `commercial/uploads.py`; `build_commercial_records` has
  none; the rest are tests. Nothing else to change.

## D-3A3.2 Native layouts are data in the neutral contracts package, read and rendered by one engine

- **Ruling.** `assetops_contracts.native` holds `Column`, `Layout`, `read_layout`, `render_layout` and the four
  illustrative layouts. The simulator renders with it; the backend reads with it through `LayoutReader`. `3A6` adds
  loading `Layout` values from profile files and the transforms; it does not change the engine's contract.
- **Why.** The simulator may not import the backend (protected seam), and the emulator and the reader must share one
  definition of the native shape, so the definition sits where both may import it, as 2a's format does. A layout as a
  value (not a parser per source) is what makes `3A6` "only transport and profile change" (§7.2). Independence (W2):
  the contract test's goldens and expected records are hand-written, so a shared engine cannot pass its own mistake.

## D-3A3.3 A reader gets the upload's context and may refuse a row

- **Ruling.** `SourceReader.read(data, *, context)` with `ReadContext(tenant_code, received_at)`; `ReadResult.refused`
  maps record indexes to a native code and path. A reader refusal wins over 2a's verdict for that row.
- **Why.** A native export names no tenant and no production time; the uploader's tenant and the receipt time are the
  honest values. A map miss or a short row must be refused with its own words ("this value is not one this layout
  knows") rather than whatever 2a says about a placeholder; letting an unmapped budget line through as a lower-case
  factor would store a heading nobody declared.

## D-3A3.4 What the emulators write

- **Ruling.** October only (the accounting period), mini-grid tenants only (RC5), from the manifest's October `actual`,
  `plan`, `coverage` and tenant `prices`; DS1b's records reused for O&M, staff and its budget lines. Forty customers
  per Site, kWh split evenly with the remainder to the first customers; receipts pay customers in order; fuel in
  400-litre deliveries. Totals must equal the manifest per Site or the emulator stops (`EMU_REVENUE`,
  `EMU_COLLECTIONS`, `EMU_FUEL`). ESTIMATED coverage writes nothing (GAP-1, D-DS1B.7).
- **Why.** The deep-dive month is October and the gate is Kobo's −562.00; history months would need derived figures
  the manifest does not state, so emulating them would invent. Even splits are plain and checkable by hand (W2); the
  replacement rule allows values "derived from the manifest" and nothing a real export lacks.

## D-3A3.5 The contract test admits readers

- **Ruling.** One parametrised suite (C1 to C10) over `CONTRACT_CASES`; `READERS` may hold a reader only when it has a
  case (S2). It checks kinds, required fields, numbers, clocks, the idempotency key (DUP-1, CONF-1), the late month,
  plain-word refusals at file and row level, pseudonymisation and the provenance cap.
- **Why.** §7.3: "a real adapter is admitted only when it passes". Tying registration to a case makes the admission
  mechanical for `3A6` and every later profile, instead of a reviewer's memory.

## D-3A3.6 Emulated loading refuses operator databases (handshake R4 of 3A2)

- **Ruling.** `refuse_operator_database(url)` refuses a database whose name, lower-cased, starts with `assetops_op`, or
  that has no name, before any connection. The loader calls it first; any future non-app caller of
  `build_commercial_uploads` must too (S1's allowlist makes adding one a reviewed change).
- **Why.** RC4: an operator database holds only that operator's real data. 3A2's provenance cap already refuses
  `source-emulated` there, but a loader that fails late has already connected and read the people; refusing by name
  first matches 3A2's broad detection (D-3A2.6) and keeps the rehearsal tooling off real data entirely.

## D-3A3.7 One path per source type per tenant

- **Ruling.** A tenant takes a source type either as DS1b canonical files or as emulated native files, never both; the
  loader refuses a directory holding both for one source type (`EXPORT_PATHS_MIXED`). Across runs, the runbooks keep
  the walkthrough tenants (`DS3`) and the rehearsal tenant (`DDR`) apart.
- **Why.** A record's identity includes its source system (D-3A1.2), and the two paths name different systems, so the
  same O&M line loaded both ways would be two records and the month would count it twice.

## D-3A3.8 The finance lead's list across Sites comes with the upload screen, not now

- **Ruling.** No cross-Site "waiting" read in this fortnight. When the upload list screen is built (next fortnight,
  beside `3C0b`), it adds `uploads_waiting(tenant_id, limit)` over every Site and the organisation for the finance lead
  and the executive.
- **Why.** The deep-dive path has no upload screen (RC7: the owner presents; `3C0b` moved out), and the rehearsal
  submits on the organisation path, which already lists everything it sent. A read with no screen would be reviewed
  twice. Recorded so the screen unit cannot miss it (owner queue Q2).

## D-3A3.9 A row holding a control character is refused on its own

- **Ruling.** After decoding and reading, a row any of whose cells holds U+0000 to U+0008, U+000B, U+000C, U+000E to
  U+001F or U+007F is refused `NATIVE_CHARACTER row.<n>` (record `{"format_version": 1}`); the other rows stand. Tab,
  CR and LF are text. A header holding one fails the exact header match (`NATIVE_HEADER`).
- **Why.** Python 3.12's `csv.reader(strict=True)` reads `1,\x002` without error (R2), so "a NUL byte is
  `NATIVE_ROW`" could not pass. An invisible character in a reference would split one customer into two pseudonyms;
  refusing the row in its own words ("holds a character that is not text") keeps the rest of the file and tells the
  person what to fix. `NATIVE_ROW`'s words ("its cells do not line up") would be untrue for it.

## D-3A3.10 The layouts are also the owner's reshaping template: provenance follows the database (joint with ON1 R3)

- **Ruling.** `Layout` no longer fixes a provenance. `LayoutReader` writes `observed-financial` when the upload runs
  with real data on (an operator database, RC4) and `source-emulated` otherwise; `ReadContext` carries `real_data`.
  On an operator database a layout file is therefore admitted, and its upload row's `reader` (`*-illustrative-1`)
  marks it as a file the analyst reshaped by hand. `3A6`'s profiles are the first route for real exports; the
  layouts are the fallback the owner kept (RC2: "hand reshaping stays the fallback"; build plan risk 1: "reshaped by
  the analyst into our template ... a workaround, timed in the runbook"). C10 asserts both sides.
- **Why.** Rev 1 fixed `source-emulated` on every layout, so on an operator database the owner's fallback was refused
  every time (R3; ON1 R3). The database already decides whether data is real (RC4, D-3A2.6, RC4-F1), so letting it
  decide the provenance adds no second switch. A transcription of the operator's own records is still their observed
  financial record; the reader id and the runbook's per-file time record that a person reshaped it. A separate "real"
  layout id was rejected: the same columns under two names, and a choice the analyst could get wrong. Residual,
  stated in the runbook: an emulated file sent by hand to an operator's server would be stamped `observed-financial`;
  its Sites (the Lakeside codes) do not exist in the operator's tenant, so its rows are refused there.

## D-3A3.11 The loader reads what the tenant already holds, once, before submitting

- **Ruling.** After the people (step 5) the loader reads the tenant's held uploads once
  (`CommercialUploads.held(tenant_id)`: every upload not declined, with its source type, reader, file SHA-256 and
  whether it waits). A file whose source type the tenant holds through the other path (canonical JSON against a
  native layout) is `EXPORT_PATH_SWITCHED`, exit 2, before any submission. A file whose SHA-256 equals a waiting
  upload is not submitted again: its line says `ALREADY_WAITING`, and with `--accept-as` that upload is decided. The
  same person may not submit and accept (`PERSON_SAME_FOR_BOTH`, exit 2), and a line decided by the loader carries
  `"decided_by_script": true`.
- **Why.** D-3A3.7 held only inside one directory (R9): across runs one tenant could take O&M both ways and count it
  twice. Every commercial record now enters through uploads (D-3A3.1), so the upload rows are a complete record of
  the paths used, and one read closes the class with no new table. The same read makes a rerun without
  `--accept-as` idempotent (R12). Separating submitter and acceptor is the least a script owes OD-15's "acceptance
  as the person's" (R8); the owner may still ask that a person click accept even in rehearsal (queue Q1).

## D-3A3.12 What the single-writer test sees

- **Ruling.** S1 fails, in any scanned module that imports from `assetops_backend.commercial` other than
  `commercial/uploads.py` and `commercial/service.py`: any `.ingest` attribute (called or not, so `r = svc.ingest`
  is caught), any `getattr(<x>, "ingest")` with that constant; and anywhere except `commercial/composition.py` and
  `commercial/uploads.py`: any import of the name `CommercialRecords` (aliased or not). `CommercialRecords(` calls
  only in the composition. Not seen: `importlib` or names built from strings, and a module that receives a records
  service without importing the package; stated as residuals in the packet.
- **Why.** R10. Catching the attribute, not only the call, closes the bound-method alias at no cost; catching the
  import closes the class alias. Dynamic access is beyond an AST test and is left to review.

## Handshake answers (round 1)

Architect (Claude), 2026-11-20, on `handshake.md` at `60710d425`. Folded into `spec.md` rev 2 and `reviewer-guide.md`
rev 2. Order changes: **RC4-F1** (`specs/RC4-F1-database-name/`) merges first; 3A3 builds on it. Size 3 to 3.25 units
(the held-uploads read, the control-character rule, S1's reach), still four commits.

- **R1 (High).** Accepted as a class fix in its own unit, **RC4-F1** (D-RC4F1.1, D-RC4F1.2): `database_target(url,
  environ)` names the database libpq reaches and refuses an unclear URL or environment; 3A2's settings and the
  backfill use it, `database_name` is deleted. In 3A3, `refuse_operator_database(url)` is `database_target(url)`
  (`DatabaseTargetUnclear` is `DATABASE_URL_UNCLEAR <reason>`, exit 2) then `is_operator_name(target.name)`
  (`EMULATED_ON_OPERATOR_DATABASE`, exit 2). L1 gains `?dbname=assetops_op_x`, `/?dbname=assetops_op_x`, `/` (empty
  name), `?service=x` and `PGDATABASE` set; all URLs use host `rc4.invalid` port 1 and the no-connect fixture of ON1
  R4 (spec §5). Plant V1b (call `make_url(url).database` in the loader) fails L1.
- **R2 (High).** Accepted, D-3A3.9: a new row-level code `NATIVE_CHARACTER` with its words; contracts 2 pins
  `1,\x002`-style rows (NUL, U+001F, U+007F each refused alone, the other rows standing) and tab inside a quoted cell
  admitted.
- **R3 (Medium).** D-3A3.10, joint with ON1 R3: the owner kept hand reshaping as the fallback (RC2), so the
  layouts must work on real data. Provenance follows the database (`ReadContext.real_data`); C10 now asserts
  `observed-financial` stored with `real_data=True` and `source-emulated` without; the canonical JSON reader keeps
  3A2's cap. ON1's runbook step 8 puts `3A6` first and the template second, timed.
- **R4 (Medium).** Accepted; spec §4 lists all four `required_headers` tuples exactly. Budget `Site` and `Currency`
  (row 2 is the `revenue` node, which needs no currency) are not required. Where 2a's first refusal for a blanked
  cell names another column, the case carries a `field_for` override (header to expected field header), written by
  the builder with a one-line reason in `source_contracts.py`: a 2a ordering fact, not a mid-build question.
- **R5 (Medium).** Accepted as written, with one change: a non-whole `billed_kwh` or `diesel_l` is `EMU_QUANTITY`
  (a quantity is not a price). All arithmetic in `Decimal(str(v))`; cents by `* 100` with a whole check (`EMU_PRICE`
  for prices, `EMU_REVENUE`/`EMU_FUEL`/`EMU_COLLECTIONS` for totals); prices looked up by `site["site"]` (the name).
- **R6 (Medium).** Accepted. The emulator keeps the set `written` of `(tenant, site, month, side, field)` it emitted
  records for; a DS1b unwritten row with that key is dropped. `outstanding` (never a record; it is the charges not
  yet paid) is re-reasoned `AS_UNPAID_CHARGES` when the charges and receipts were written. New E9.
- **R7 (Medium).** Accepted: a DS1b record of a kept kind whose value the layout cannot render (a category or factor
  outside the map) is listed `NOT_IN_LAYOUT`, never a stop. A record the emulator built itself that fails to render
  stays `NATIVE_RENDER` (an emulator bug).
- **R8 (Medium; queue Q1).** D-3A3.11: `PERSON_SAME_FOR_BOTH` and `"decided_by_script": true`. Not blocking: the
  loader runs only on emulated data outside operator databases (step 2), and the decision row names a real person
  with a role that may accept. Q1 stays "owner to weigh in"; a "no" removes `--accept-as` and nothing else.
- **R9 (Medium).** D-3A3.11: `EXPORT_PATH_SWITCHED` from one read of held uploads. New L5 and plant V14.
- **R10 (Low).** D-3A3.12 states S1's reach; S1 gains the alias, bound-method and `getattr` cases as planted fixtures
  in the test itself.
- **R11 (Low).** Accepted: `ContractCase.scope` is dropped (every layout spans Sites; the Site path is 3A2's, tested
  there). E8 gains `EMU_COLLECTIONS` (Kobo `collected` 3181.0), `EMU_PRICE` (Kobo `tariff_usd_per_kwh` 0.405) and
  `EMU_QUANTITY` (Kobo `billed_kwh` 8645.5).
- **R12 (Low).** D-3A3.11: a file equal to a waiting upload is `ALREADY_WAITING`, not resubmitted; with
  `--accept-as` it is then decided. A rerun is idempotent with or without `--accept-as`.
- **R13 (Low).** Accepted: a row's number is the physical line on which it ends (a quoted cell spanning lines gives
  its last line). Stated in §2.2 step 4.
- **R14 (Low).** Accepted into D-3A3.1's binding: `DS3` loads one directory per tenant (its own files only), since
  the loader refuses another tenant's file.
- **P1 to P3, P9, P10 (verified).** Noted; no change.
- **P4.** Accepted: `test_3a2_commercial_upload_service.py` joins the allowed files, signature change only.
- **P5.** Accepted: `test_3c0a_accounts_service.py`'s `MemoryStore` gains `tenant_slug`; listed.
- **P6.** `MappingProxyType({})` as the default is accepted (immutable, shared safely).
- **P7.** Accepted: `tenant_slug(tenant_id)` `None` is `UPLOAD_TENANT_MISMATCH` before reading, as the JSON reader.
- **P8.** Accepted: C8 adds an unclosed quote in row 3 of a four-line collections file: 422 `UPLOAD_FILE_REFUSED`,
  field "row 4" (the line where the reader stopped, R13).
- **P11.** Accepted: E7 pins the SHA-256s of the files built from `view_v1.json`; the packet records, beside them,
  those of the runbook's YAML command if they differ, with the reason.
