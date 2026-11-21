# 3A6 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Fresh Claude reviewer, 2026-11-20, on `main` fb6d248d3 (spec rev 1, `rulings.md`, `reviewer-guide.md`, owner RC2/RC4).
Severity: **High** blocks coding; Medium needs a ruling; Low is the Architect's call. **(done)** = the answer changes
what counts as done.

### High

- **R1 (done) §2.5 step 6, §4.1: a map entry the sample never uses is admitted unchecked.** The probes only test the
  engine (a value outside the map is refused); nothing tests that each map entry maps to the right canonical value.
  The kobo fixture shows the hole: `"Quote": "QUOTE"` occurs in no sample row. A profile written `"Quote": "INVOICED"`
  (or `"Draft": "PAID"`) passes steps 1 to 6 and the expected-record compare, then turns every quote into fuel cost
  (4b `COST_STATUSES`, and 3A7 reconciles against it). Same class: a column with a path whose cells are all empty in
  the sample makes P4, P5 and P6 skip silently, so its type, format and map were never read once. Expected: admission
  refuses a map key that no sample row uses (`ADMIT_MAP_UNCOVERED {header, value}`) and a column with a path that no
  sample row fills (`ADMIT_PROBE {probe, where}` "no value in the sample"); the kobo sample gains a `Quote` row (or the
  map loses `Quote`); a test for each.
- **R2 (done) §2.10, V10, done 7: nothing can tell the canonical-side derivation from the maps-side one.** Every layout
  the suite runs has passed `check_layout`, which (D-3A6.6) refuses an unmapped coded column; on such layouts "headers
  whose column writes a coded path" and "headers whose column has a map" are the same set, so V10's plant passes every
  listed test, and "the §2.10 assertion" names no test that can fail. Likewise, deleting `body.factor_id` (or any one
  path) from the engine's `CODED_PATHS` fails no listed test (N7 probes `body.category`, N8 `body.method` only).
  Expected: a named test that builds a `Layout` directly (bypassing `check_layout`) with a coded column and no map,
  pairs it with `coded=()`, and asserts the suite's coded-headers check fails; and a test
  `CODED_PATHS == <the twelve, written out>`.
- **R3 (done) §2.9, done 8: five plants for about ten rule clauses; the rest can be no-ops and still pass.** Unproven:
  (a) a commercial-named dynamic import inside an *allowlisted* module (the "anywhere" clause: the planted
  `import_module` sits in a non-allowlisted path, so the plain dynamic-import rule catches it first); (b)
  `from importlib import import_module as im` / `import importlib as il`; (c) the `"ingest"` / `"CommercialRecords"`
  string-constant rule (the `"in" + "gest"` plant is caught by the non-constant `getattr` rule instead); (d)
  `setattr`/`hasattr`/`delattr`; (e) `operator.attrgetter`; (f) `exec` and `compile`; (g) `builtins.eval`. Not covered
  at all: `sys.modules["assetops_backend.commercial.service"]` (`tools/mechanism_dataset.py` and
  `tools/probe_kisiwa_fuel.py` already use `sys.modules`), `runpy.run_module`, `importlib.__import__`. Expected: one
  plant per clause, each with a `rel` chosen so only that clause fires (assert the violation text names the clause),
  and a ruling on the three uncovered routes (rule or stated residual).
- **R4 (done) §2.3, §2.4: an XLSX number in a month or date column is always a serial.** A `YYYYMM` month stored as a
  number (`202610`, common in ERP workbooks) reads as serial 202610, i.e. a date in 2454, and `2454-xx` passes 2a's
  period pattern: wrong-month records are accepted silently, also after admission when the sample happened to hold
  text months. A serial above 2958465 overflows `date` (an uncaught `OverflowError`, a 500, not a row refusal), and
  `Decimal` accepts `<v>NaN</v>` / `Infinity`. Expected: for `month_format` `YYYYMM` an `XlsxNumber` is read through
  the grammar as its text; a serial must be 1 to 2958465 (or a narrower stated window), else `NATIVE_FORMAT`; a
  non-finite `<v>` is `NATIVE_FORMAT`; an N3/N4 literal for each.

### Medium

- **R5 (done) §2.5 step 6 P1, A6.** P1 swaps two header cells and expects `read_rows` to raise `NATIVE_HEADER`, but
  §2.2 puts the header comparison in `split_file` (step 3); `read_rows` "applies steps 4 to 7". As written the true
  engine fails P1 and nothing can be admitted. Rule which function checks the header (or that P1 re-runs
  `split_file`). A6 has no stub for P1: add (f) "ignores header order" giving `ADMIT_PROBE P1`. A one-column profile
  cannot swap: require 2 columns or define P1 for it.
- **R6 §2.5 P6.** "Refused by the reader **or by 2a**, or holds none of the column's paths": an engine that invents a
  value 2a happens to refuse passes, and `run_probes(layout, header, rows, *, read=read_rows)` has no 2a argument.
  Expected: P6 judges the reader's record only (a refused row's placeholder holds none). Also say where `run_probes`
  lives (`native/` or `commercial/profiles.py`).
- **R7 (done) §2.3 vs §2.2: XLSX row refusals and dropped columns.** `xlsx_rows` returns `(n, cells)` with no place
  for a row mark (`t="e"`, `t="d"`, a bad `<v>`), and §2.3 applies the character rule to "every text cell" while §2.2
  exempts dropped columns (N5 tests the exemption for CSV only). An `#N/A` or a U+200B in a dropped XLSX column would
  refuse the row. Expected: a cell-level marker (e.g. an `XlsxError` cell) that `read_rows` judges only in columns
  with a path; an N3 case with an error cell in a dropped column admitted.
- **R8 §2.3: the DTD check and zip errors.** "A member containing `<!DOCTYPE`" on bytes misses a UTF-16 member
  (ElementTree parses UTF-16 with a BOM). Require UTF-8 members (or test the decoded text). A declared size that lies
  surfaces as `BadZipFile` (CRC) mid-read; unsupported compression is `NotImplementedError`, encryption
  `RuntimeError`: say every zip or zlib error is `NATIVE_WORKBOOK`; add an N3 case for each class.
- **R9 (done) §2.5: ambiguous formats pass with one consistent mistake.** If every sample date has day ≤ 12, a
  `MM/DD/YYYY` profile and an analyst who reads the dates the same wrong way agree; likewise `1,200` with decimal and
  thousands marks swapped. The expected file is independent of the engine (W2) but not of the analyst's reading.
  Expected: admission requires, per `date`/`datetime`/`month_of` column under `DD/MM` or `MM/DD`, one sample value
  with day > 12, and per `number` column with a thousands mark, one value that only one reading admits
  (`ADMIT_SAMPLE_AMBIGUOUS`); or a ruling that this is a stated residual.
- **R10 (done) §4.1: constant version on a mutable ledger.** `kobo-ledger-expenses` uses `version` constant `"1"`
  but has a `State` column (`Invoiced` then `Paid`). Its next export carries a changed status or a corrected amount
  under the same `(id, version)`: `INTAKE_VERSION_CONFLICT` (C6, `test_3a3_source_contract.py:204`), so corrections
  never flow through the profile, while 3A7 depends on corrections. Should the fixture use `row_digest`, and should
  `compile_profile` refuse `constant` when a column writes `status`?
- **R11 §2.6, D-3A6.5: the source-switch rule is check-then-act.** `_check` runs outside the tenant lock and
  `decide`/accept does not re-check, so two concurrent submits of different systems for one Site are both held, then
  both accepted: the double count the rule exists for. Expected: re-check inside `write_intake`'s locked `decide` at
  acceptance (refuse `UPLOAD_SOURCE_SWITCHED` there too), with a test.
- **R12 (done) §2.11 vs K3 and the guide.** `source_profile.admit_sample_row` is "Row {row} of the sample is refused:
  {reason}" with `{reason}` = `render(reason_words(code))`; K3 and the reviewer guide expect "Row 4 of the sample is
  refused: Litres: ...". One of them changes; if the field stays, say it is `reader.field_label(cut_path)`.
- **R13 §2.11: `commercial_upload.reason.native_encoding`** still says "the file is not UTF-8 text.", which is false
  for a cp1252 profile. Expected: words naming the profile's encoding, or encoding-neutral words.
- **R14 §4.2 X0: byte equality of a `ZIP_DEFLATED` workbook depends on the zlib build** (zlib-ng builds emit
  different streams). X0 may pass for the implementer and fail for the reviewer. Expected: `ZIP_STORED` for the
  fixture, or X0 compares member names, order, dates and decompressed bytes.
- **R15 §2.1, D-3A6.6: maps only on coded paths.** An export naming Sites (`Kobo`) rather than codes (`KOBO-001`)
  cannot be read by any profile; that is a common shape and DDR's "unseen shape" may carry it. Confirm the reshaping
  fallback covers it, or allow a map on `site_code`.

### Low

- **R16 §2.2 join:** `":"` joins parts that may themselves contain `":"` (`A:B`+`C` = `A`+`B:C`); refuse a part
  containing the separator, or use U+001F.
- **R17 §2.10:** no case uses `versioning="digest"` and no XLSX case runs C1 to C10, so that branch is dead; add the
  budget profile as a case or drop the branch.
- **R18 §2.5 step 1 vs `reader`:** profile bytes with a UTF-8 BOM parse (`json.loads(bytes)` accepts it) but
  `json.loads(profile_json)` on the stored text refuses it, so an admitted profile cannot read; say strict UTF-8, no
  BOM.
- **R19 §2.1, §2.4:** the `scale` grammar (sign, zero) is unstated; thousands marks exclude U+00A0 and U+202F,
  which French-locale exports use (refused, so safe; confirm intended).
- **R20 §2.5 P3:** the characters are written literally (invisible in review); write `"​"`, `"﻿"`,
  `" "`.
- **R21 §2.11:** `UPLOAD_SOURCE_SWITCHED` shows the raw `source_system` ID to the person (system vocabulary).

## Implementer questions

See "Implementer pre-flight" (P1 to P10).

## Implementer pre-flight

Pre-flight of `spec.md` against `main` fb6d248d3 (the spec cites e2387b334; nothing it reads changed since, only 5b's
`structure/attribution/` and `structure/read.py`). Read-only; no database run.

- **P1 High (done) §0, §5: the migration chain cannot be built off `main`.** `0066_structure_snapshot` exists only
  on `task/3B7a-snapshot` (1f7e3b743; it revises `0065_commercial_upload` and touches no commercial file). A branch
  off `main` whose `0067` revises a missing revision breaks Alembic's graph, so every Postgres test on the branch
  fails at `upgrade head`, not only Q1 to Q3. If 3A6 instead revises 0065 and 3B7a merges with 0066 also revising
  0065, `main` gets two heads. Ruling needed: build as `0066_source_profile` revising 0065 and renumber to 0067 at
  merge preparation if 3B7a lands first (D-3A2.11), or branch off 3B7a's merge. 3A7's `0068` inherits the answer.
- **P2 Medium (done) §3, done 11:** `test_3c1a_person_work.py:479` asserts `COMMAND_ROLES == SPEC_ROLES` (a
  hand-written table). Adding `commercial.profile_admit` fails it unless `SPEC_ROLES` gains the key; that file is not
  in done 11's list. Add it (extension only).
- **P3 Medium (done) §2.7:** `--tenant SLUG` needs slug to tenant ID for `check` and `list` (no `--as`).
  `AccountService` has no such method; `AccountStore.tenant_by_slug` (`accounts/store.py:37`) does, and
  `CommercialStore` has only ID to slug. Name the method and its file (a new `CommercialStore.tenant_id(slug)`, or an
  `AccountService` method, which puts `accounts/service.py` in scope).
- **P4 Medium (done) §2.9: the allowlist as the scan finds it.** An AST scan with S1's roots plus
  `contracts/assetops_contracts` and S1's test-file filter finds seven modules: `chain/adapters/file_chain_config.py`
  (`find_spec`), `chain/adapters/file_inputs.py` (`import_module`), `tools/checks/import_root_probe.py`,
  `tools/checks/neutral_tests.py` (`__import__`, `import_module`), `tools/mechanism_dataset.py`,
  `tools/validate-test-selection.py`, `host/conftest.py`. `tools/checks/test_event_register.py` is excluded by the
  `test_` filter (drop it; note the filter hides a non-test tool so named); `host/conftest.py` is scanned (keep it):
  the spec's conditional sits on the wrong file. `eval`/`exec`/`compile` must mean the bare builtin names (and
  `builtins.<name>`): S1's `_called` returns attribute names, so a rule built on it flags `re.compile` at
  `commercial/service.py:53` and `commercial/months.py:34`. No module outside the writers holds an `"ingest"` or
  `"CommercialRecords"` constant today (confirmed).
- **P5 Medium (done) §2.10: the suite's literals assume three records and a dot decimal.**
  `test_3a3_source_contract.py:166, 205, 211` hard-code counts such as `(3, 2, 0, 0, 1)`; the kobo case has four.
  C6 sets the amount to `"999.00"` (lines 202, 209), which the kobo grammar (decimal `,`, thousands `.`) refuses
  `NATIVE_FORMAT` instead of reaching `INTAKE_VERSION_CONFLICT`. Line 36 pins the old `NATIVE_CHARACTER` words
  (a change, not an extension). Expected: counts from `n`, a per-case `changed_amount` (kobo `"999,00"`), the words
  pin updated, all listed in §2.10.
- **P6 Medium (done) §2.6: stored uploads lose the profile reader.** `CommercialUploads.get` resolves
  `READERS.get(u.reader, READERS[DEFAULT_READER])` (`uploads.py:309`), and `submit` answers through `get`. A profile
  upload's refusals then read `amount.value` for `Net (USD)` and `row.6` for `row 6` (the JSON reader's labels).
  Expected: `get` resolves `profile.*` readers by the stored ID, superseded versions included, without raising
  `UPLOAD_READER_SUPERSEDED`; U5 checks it through `get`.
- **P7 Medium §2.8:** step 4 runs before any connection ("steps 1, 2 and 4 always run", `main`'s docstring), but a
  profile file's source type is known only once its profile is resolved (step 5c). L9's `EXPORT_PATHS_MIXED` must
  then be decided after 5c; say so, and its order against `PROFILE_NOT_ADMITTED`.
- **P8 Low done 11:** `CommercialUploads.reader` is called only at `commercial_upload_api.py:168` and
  `uploads.py:163`; no 3A2 test calls it, so the 3A2 test edits may be unnecessary.
- **P9 Low (residual, 3B7a):** 3B7a's code digest covers the import closure, which includes `commercial.composition`
  (its test 11b). 3A6's composition edit (and 3A7's) changes the digest, so snapshots built before the merge read
  stale (`RULES`). State it in the packet; 3B7a's owner should expect it.
- **P10 Recomputed by hand (no question):** the three budget digests `r8b6cdd540fa7c49a`, `r4bc1868e230b8ed3`,
  `rff4a97f304aa3280` are right (row 2 at `3421` gives `r941458d61291e87c`, only that row changes); serial 46296 is
  2026-10-01; `874.99999999999989` at 15 digits is `875`; every N4 literal holds; byte `0x96` is `–` in cp1252 and
  invalid UTF-8 (so N2's `NATIVE_ENCODING` bites); cp1252 strict refuses 0x81, 0x8D, 0x8F, 0x90, 0x9D. Cited code
  exists as named: `Column`, `Layout`, `read_layout`, `render_layout`, `check_layout`, `LAYOUTS`, `LayoutReader`,
  `READERS`, `CommercialUploads._check`/`.held`, `HeldUpload`, `_HELD`, `ALLOWED_EXTRA`, `CLASSES`,
  `commercial_upload_settings`, `COMMAND_ROLES`, `$commercialTables` (`configuration-persistence.ps1:977`). The four
  illustrative layouts already satisfy the coded rule. `site_code` is upper-case only in 2a, so the Site intersection
  of D-3A6.5 cannot be dodged by case.

## Round 1 closed

Architect (Claude), 2026-11-20: every question above is answered once in `rulings.md` "Handshake answers (round 1)"
and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. No question is open; coding may start (3A6 commit 2
and all of 3A7 wait on their migration base, D-3A6.12).
