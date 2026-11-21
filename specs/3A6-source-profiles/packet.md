# 3A6 packet: source profiles as data

`USER_REVIEW_REQUIRED: false` (no screen; the intake's new refusals are the owner-reviewed spec rev 2). Architect ruling
needed on mid-build Q1. Branch `task/3A6-source-profiles`, worktree `/opt/assetecon/AssetOpsV1-3a6`; commits `7bcacba98`
(1), `26729b9ce` (2), `43b1040a8` (3), plus this packet; `main` `26dd65e60` (3B7a, 0066) merged in at `9d0d74067`.

## Outcome

An operator export (CSV or one-sheet XLSX) is read through a JSON profile admitted by
`python -m assetops_backend.source_profile check|admit|list`: no code per layout. Admission (`commercial/profiles.py`)
runs steps 1 to 7 (coverage 4a to 4c, expected records, six probes) and keeps three SHA-256s and a row count, never a
cell. Only the latest version reads new uploads; stored uploads keep their reader. One source system per source type
per Site at check/submit, re-checked under the tenant's lock at acceptance (D-3A6.15). The loader takes
`<SLUG>.profile.<id>.csv|xlsx`. S1 has eleven new tags with one plant each; the suite derives coded probes from
`CODED_PATHS_EXPECTED` and runs the kobo profile case.

## Module paths and fixtures

PYTHONPATH = worktree `backend:backend/tests:contracts:simulator:gateway:field:host:tools`; `assetops_backend`,
`assetops_contracts`, `assetops_simulator` resolve to `/opt/assetecon/AssetOpsV1-3a6/...`. SHA-256: kobo csv
`de793415…bead`, budget xlsx `df247815…0e78` (hand-written; digests recomputed by hand in commit 1).

## Done (spec §7)

1. Illustrative layouts unchanged: N1, 3A3 contracts, E7 pins pass. 2. N2 to N4 pass. 3. A1, A4 to A6, A8 to A10
pass. 4. U1, U2, C1 to C10 on the profile case pass. 5. U3 (check, submit, KISIWA, declined, race), Q3, U6 pass.
6. N5, P3 pass. 7. `test_coded_check_fails_on_an_unchecked_layout`, N7 to N9 pass. 8. 28 `PLANTED_TAGGED` rows give
exactly their tags; `test_s1_allowlists_are_exact` passes. 9. L7, U1, K1 pass. 10. Every plant fails (below).
11. Scope: §3 files, fixtures, tests, `source_contracts.py`, the listed `test_3a3_*` edits, `test_3c1a` (one line),
plus two deviations (below).

## Checks (revision `43b1040a8`)

- Focused + regression, no DB (`heavy-slot.sh -- pytest`: contracts/tests, 3A6 service and command, 3A3 contract,
  single writer, loader, 3A2 service and API, 3A1, 3A4, 3C1a, 3B7a, ON1, RC4-F1, simulator E7): `792 passed in
  78.16s`.
- Postgres (`heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1`, routed `*_test`): 3A1, 3A2, 3A3 loader, 3A4,
  3A6 Q1-Q3, 3B7a, ON1: `80 passed in 56.60s`, none skipped.
- Fast check-all (`heavy-slot.sh -- pwsh tools/check-all.ps1`): `All 41 guards passed` in 4m26s (architecture, agent
  workflow, persistence and its self-tests among them).
- Evidence: `/opt/assetecon/evidence/3A6/2026-11-21/` (run logs, plant log).

## Plants (applied, run, reverted; tree clean after each)

Commit 1 (previous builder): V1-V9, V21, V23b, V25, V30, V32. Commits 2 and 3, each failing its named test: V11
(A6 e), V12 (A8), V13 (A2), V14 (A3), V15, V16, V17 (U3), V22, V23 (A9), V24 (memory: U3 race; adapter: Q3 on
Postgres, `1 failed, 2 passed`), V28 (A1, A6), V29 (A10), V10 (`test_coded_check_fails...`), V18 (p01), V19 (p22),
V20 (L8), V26 (p09, p11), V27 (p12, p13), V31 (p07, p08). V17 is planted in the memory mirror (`_HELD`'s mirror),
since U3 runs in memory.

## Mid-build questions: 1

Q1 (`mid-build-questions.md`): A9 (a)'s map `"Quote": "INVOICED"` is not one to one, which `check_layout` refuses at
compile. A9 (a) runs with `"Quote": "DRAFT"` (same uncovered key and expected refusal). A count above zero is a
spec-template defect.

## Known deviations

- `test_3a2_commercial_upload_service.py`: `UploadMemoryStore` gains `held_uploads` (3A3's mirror moved there, plus
  `source_system`, `site_codes`). §2.6 makes every check call `held_uploads`, and without it every 3A2, 3A3, 3A4 and
  ON1 world fails. Done 11 allows only the `reader` signature (amended, D-3A6.20: it also lists `held_uploads` on `UploadMemoryStore` and the `code_digest.py` allowlist entry). `HeldMemoryStore` now only subclasses it.
- `DYNAMIC_IMPORT_ALLOWED` adds `structure_snapshot/adapters/code_digest.py` (3B7a, merged after rev 2 listed seven;
  `find_spec("assetops_contracts")`). The exactness test needs it.
- Coverage (4a to 4c) runs before the per-row verdict of step 4. A9 (b) (every `Litres` emptied) expects
  `ADMIT_COLUMN_EMPTY`, but 2a refuses those FUEL rows first.
- U3's "newer version still uploads" uses v1 reformatted, not A2's `personal` v2. That v2 pseudonymises
  `fuel-co`, so its rows are `INTAKE_VERSION_CONFLICT` against v1's records (risk below).
- Choices the spec left open: profile over 64 KiB is `PROFILE_INVALID json`; sample over 1 MiB is
  `ADMIT_SAMPLE_FILE {code: FILE_TOO_LARGE}`; an already-admitted profile still runs steps 4 to 6; the unique keys are
  named (`commercial_source_profile_{version,reader,sha256}_key`) so `PROFILE_ALREADY_ADMITTED` maps from the key.
  The route also maps `StoreRefused` and unavailability on the reader lookup.

## Residual risk

- A change to `personal` after accepted data is refused (D-3A6.18); the migration is unit 3A6b. Until then raw values from before the declaration cannot arise, because the declaration is fixed before the first accepted upload. Review r1 residuals: D-3A6.21.
- S1 still misses (D-3A6.14): unimported services handed in, `__getattribute__`, `vars(obj)[name]`, tools named
  `test_*.py`.
- Commit 1's risk stands: a CSV with a bad header and a later syntax error reports `NATIVE_ROW`.
- 3A7 edits the same store, adapter, model, composition, words, permissions and guard. P9: 3B7a's code digest changes,
  so snapshots must be rebuilt after 3A7.

## Review focus

`profiles.py` step order and `_coverage`; the `_SWITCHED` SQL and its memory mirror; `uploads._refuse_switch` and
`_stored_reader`; loader steps 5c/mixed/5b; S1 `_aliases`/`_qual`; `source_contracts.coded_headers`.

## Fix round r1 (review `review.md`; D-3A6.18 to D-3A6.22), revision `c727f97dd` plus this packet commit

- F1 `xlsx.py`: rows kept sparse (`xlsx_sparse_rows`); `split_file` pads only to the header's width and turns any
  non-empty cell past it into one extra cell (a count mismatch, `NATIVE_ROW` for that row); column index above 16,383
  is `NATIVE_WORKBOOK`; `xlsx_rows` (kept) pads under a 2 M cell budget. Test `test_n3_far_right_cells_...`: 2,000
  rows with a cell at XFD, peak under 20 MB and under 3 s; plus XFE and a `²` row number.
- F2 `_coverage` judges only rows of header width; a short CSV row is `ADMIT_SAMPLE_ROW` row 5 `NATIVE_ROW` (A4).
- F3 / D-3A6.18: `PROFILE_LINEAGE {where: "personal"}` when `personal` (as a set) differs from the latest version's
  and an accepted upload of the system exists (`held_uploads`, `not waiting`); words `profile_lineage_personal`.
  A2b (memory) and Q2b (Postgres) cover it, including a waiting upload not counting and reordering admitted.
- F4 formula without cached value is `XlsxBad`; F5 ASCII-digit row numbers only (`²` is `NATIVE_WORKBOOK`); F6 S1
  flags references to `DYNAMIC_CALLS`/`EVAL_CALLS` and `from assetops_backend import commercial` (plants p26 to p28);
  F7/D-3A6.19 `QUOTE`; F8 `bad_clock` literal `2026-10-11 09:00`; F9 loader disposes the profile store in `finally`.
- Plants (applied, run, reverted): V33 personal comparison dropped fails A2b and Q2b; V34 waiting uploads counted fails
  A2b; V35 order-sensitive compare fails A2b; V36 old dense padding fails the F1 test; F2 guard removed fails A4;
  S1 reference clause removed fails p26 and p27; commercial-import clause removed fails p28.
- Checks: focused + regression, no DB: `562 passed in 70.93s` (revision `f8118b65f`); Postgres set (3A1, 3A2, 3A3
  loader, 3A3b7a, ON1, 3A6): `71 passed in 55.58s`; fast check-all: `All 41 guards passed` (236.7 s). Re-run after resume at `c727f97dd`: 562 passed in 68.31s; Postgres 71 passed in 52.69s; plants V33, V35, V36 re-seen failing.
- Residuals: D-3A6.21; the 3A6b migration is queued.

## Fix round r2

- N1: `split_file` refuses `NATIVE_HEADER json` before any data row is built (`layouts_v1.py`); rows pad only to the layout's width. Test `test_n3_far_right_header_cell_is_refused_in_bounded_memory_and_time` (header cell XFD1, 2,000 rows): passes; plant V37 (old order restored) fails it at 274.6 MB peak.
- N2: A2b asserts a sample-only change (same content, new profile bytes, new sample) is admitted as v4.
- N3: residual text restored in full; V34/V35 labels follow D-3A6.18 (V34 = waiting uploads counted, V35 = ordered compare).
- Checks at r2: 3A6 + contracts + 3A2/3A3/ON1/RC4-F1/3B7a non-DB: 495 passed in 51.66s; Postgres (3A6, 3A3, 3A2, ON1, 3B7a) 59 passed in 50.05s; fast check-all: All 41 guards passed (245.2 s).

## Fix round r3 (review N4; the class, not the instance)

The class: a small, well-compressed XLSX making the reader do work out of proportion to what it carries. Rounds 1
and 2 closed padding instances; r3 bounds the reader as a whole.

**What changed** (`contracts/assetops_contracts/native/xlsx.py`, `layouts_v1.py` `split_file`):
- **One work bound.** Every member the reader reads (`workbook.xml`, its rels, `sharedStrings.xml`, the sheet) is
  parsed by event through an `XMLParser` target; no tree is built. Every element start costs one unit of a single
  workbook-wide budget, `_WORK_MAX = 500,000`; past it the file is `NATIVE_WORKBOOK json`, raised inside the parse.
  Rows and cells are elements, so rows plus cells visited never pass it, and every later loop runs over what the
  parse kept.
- **Row numbers rise strictly.** A row whose `r` is not above the previous row's number (duplicate, decreasing, `0`)
  or is past 1,048,576 is `NATIVE_WORKBOOK`; a `<row>` without `r` takes the previous number plus one (§2.3), so it
  always rises; an `r` longer than seven significant digits is refused before `int` (which raises `ValueError` past
  4,300 digits; a leak of the same kind as F5).
- **No padding past a checked width.** The header is the one row numbered `header_row`; a non-empty cell at or past
  the layout's column count refuses it (`NATIVE_HEADER json`) before the header list is built, and the list is the
  layout's width only. Same verdicts as before (an empty far cell still trims, a far value still refuses).
- **A cell without `r`** takes one past the widest index so far, kept as a running value (was `max(cells)` per
  cell: quadratic in a row of 16,000 cells without `r`). Same index as before.
- **Found in the sweep, same class:** a numeric cell `<v>1E+999999</v>` (11 bytes) became a 1,000,000-character
  plain-notation string, and `1E+9999999` let `decimal.Overflow` out. A non-zero number whose adjusted exponent is
  outside -324..308 (a double's range; Excel holds doubles) is now `XlsxBad("")`, judged by the row verdict as any
  unreadable cell; zero reads `0` whatever its exponent.

**The cap and why it covers legitimate exports.** 500,000 elements. A batch holds at most 10,000 records
(`MAX_RECORDS`), so 500,000 covers that ceiling at up to 24 numeric or shared-string columns (2 elements a cell)
or 16 inline-string columns (3 a cell), and a 60-column profile to about 4,000 rows. The plan's real files are a
few dozen rows of 5 to 12 columns (the budget golden: 4 rows, 5 columns, 63 elements in its sheet). A file past the
bound gets the workbook words ("not an Excel workbook this layout can read"); a dedicated "too large" reason would
be a new code (open point for the coordinator, not built).

**Audit of every pad, rebuild and loop** (why each is bounded):

| Site | Work | Bound |
|---|---|---|
| `xlsx._read` infolist `any`/`sum` | one pass over the zip's central directory | the directory is part of the upload bytes (8 MiB cap; 20,000 empty members read in under 1.5 s, tested) |
| `xlsx._parse` decode + `<!DOCTYPE` scan | linear in one member | member cap 16 MiB, total 64 MiB (unchanged) |
| `XMLParser` feed, target `start`/`data`/`end` | O(1) per event; `data` appends only to the open `<v>`/`<t>` being read | every start is one unit of `_WORK_MAX`; text length is within the member |
| `_Workbook` sheets, `_Rels` relationships | count; keep the first | elements, under the budget |
| `_Shared` strings list | one string per `<si>` | `<si>` elements, under the budget |
| `_Text.value` join of runs | linear in runs | runs are elements, under the budget |
| `_Sheet` row: `r` regex, length check, `int` | linear in the attribute, `int` on at most 7 significant digits | member size |
| `_Sheet` cell: `_REF` match, `_column_index`, running next index | O(1) (letters 1 to 3) | was quadratic; now one step a cell |
| `_number` | `Decimal` parse linear in digits (5 M digits: 0.05 s), result at most 309 + 324 characters | exponent range check |
| `xlsx_rows` padding (no caller outside contracts) | pads each row to its last cell | `_PAD_BUDGET` 2,000,000 cells total (unchanged) |
| `split_file` header | one row found (row numbers are unique), cells past width scanned, list of the layout's width | rows and cells parsed, under the budget; width at most 60 |
| `split_file` data rows | per row: all-empty test, list of the layout's width, `min` over cells past width (was `sorted`) | rows and cells under the budget; width at most 60 |
| `read_rows` (and `commercial/profiles.py` `_coverage`, after `split_file`) | per row: the layout's columns | rows under the budget (XLSX); for CSV, rows within the 8 MiB upload, as before |

**Adversarial tests** (`contracts/tests/test_3a6_profiles.py`, section "N3 r3"; each bounded on time in a plain
run and on peak memory in a traced run; builders after the reviewer's r3 probes): duplicate header rows with XFD1
(5,000), duplicate data rows, decreasing rows, row 0 and row past Excel, rows without `r`, a 5,000-digit row number,
far header cells compared without padding, far data cells (F1, kept), far header (N1, kept), 100,000 empty rows
under the bound read as before, empty rows past the bound, a near-member-cap sheet (just under 16 MiB, at the real
bound), 2 rows of 16,000 cells without `r`, repeated cell references, shared strings and sheets counted against the
bound, 20,000 members, and numbers past a double (4 cases) plus numbers inside it read as before. Past-the-bound
cases other than the near-member-cap one run with the bound lowered to 100,000 by `monkeypatch`, so the traced run
stays short; `test_n3_r3_the_bound_is_the_stated_one` pins the real value.

**Plants** (applied, run with `-k "r3 or far_right"`, reverted; tree clean after each):
- Pa, row-number check removed: 5 fail (duplicate header, duplicate data, decreasing, row 0/past Excel, rows without `r`).
- Pb, Pa plus the header padded to the file's widest cell, last match (round-2 shape): the same 5 fail; the run took
  131 s against 26 s, the duplicate-header case carrying the time. With row numbers unique, header padding alone is
  not observable (one row padded once), so the row check is the guard for N4 and the width rule is defence in depth.
- Pc, work bound disabled: 5 fail (empty rows past the bound, near member cap, repeated references, shared strings,
  sheets).
- Pd, next index found by rescanning the row: the cells-without-`r` case fails on time.
- Pe, the whole round-2 reader restored (tree parse, no bound): 12 fail.
- Pf, data rows padded to the widest cell (F1): the F1 test fails.
- Pg, exponent range check removed: the numbers-past-a-double run did not finish inside a 900 s timeout (bound
  1.5 s; 2,000 cells of a million characters each, every one scanned by the row verdict).
- Ph, row-number length check removed: the 5,000-digit case fails with `ValueError: Exceeds the limit (4300 digits)`.

**Legitimate verdicts.** A differential fuzz of the round-2 reader against the new one (3,000 random sheets: shared
and inline strings, rich-text runs, phonetic runs, `<t>` with a child, `<v>` with a child, nested `<c>`, formulas,
errors, booleans, cells and rows without `r`, out-of-order cells) gave 0 mismatches; inputs with repeated or falling
row numbers were counted only when the new reader refused them `NATIVE_WORKBOOK`. The existing row-count, formula,
row-number, `NATIVE_HEADER`, kobo and budget golden tests pass unchanged.

**Measurements** (scratch probes, host shared with other lanes, so timings are upper-ish):
- N4 itself: 40,000 duplicate `r="1"` rows with XFD1, 37.8 s at round 3, now `NATIVE_WORKBOOK` in 0.04 s; a
  member-cap sheet of them (409,000 rows, 50.6 kB deflated) in 0.38 s.
- Worst found, at the bound: 249,000 rows `<row><c t="b"/></row>` (each a non-empty `FALSE` row, two elements),
  14.5 kB, read `ok 249003` in 4.55 s, max RSS 171 MB; 251,000 rows refuse in 1.27 s. Almost all of the 4.55 s is
  `read_rows` building one record a row, the same per-row cost as CSV: a 2.75 MB kobo CSV of 250,000 minimal rows
  took 3.99 s (max RSS 261 MB), and CSV rows are bounded by the 8 MiB upload cap, not by this slice.
- Parse residual (item 5): the event parse keeps no tree. P1 (200,000 one-cell rows, 14 MB sheet) parse peak
  94 MB under tracemalloc, was 263 MB; what remains is the output rows themselves (one tuple and dict a row), so
  peak parse memory follows the work bound, not the member size: 990,000 empty rows peaked at 173 MB when the bound
  was 1,000,000; at 500,000 the bound halves that. Lowering the 16 MiB member cap is no longer needed for memory and
  would refuse a legitimate 10,000-row wide export, so it stays.

**Checks at r3** (code at `c8a6d23c1`; this packet commit adds docs only):
- Non-DB, `heavy-slot.sh -- pytest contracts/tests` plus 3A6 service and command, 3A3 contract, single writer,
  loader, 3A2 service and API, 3B7a seam and snapshot, ON1 (4 files), RC4-F1: `584 passed in 91.15s` (wall 150 s).
- Postgres, `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1` (routed `*_test`): 3A6, 3A3 loader, 3A2, ON1,
  3B7a snapshot: `59 passed in 49.85s`, none skipped.
- Fast check-all: `All 41 guards passed` (244.1 s).
- Evidence: `/opt/assetecon/evidence/3A6/2026-11-21/r3/` (run logs, plant log, probes, the differential fuzz).

**Open point for the coordinator:** the budget refusal reuses `NATIVE_WORKBOOK` and its words; a dedicated reason
(for example "this file holds more than this layout reads at once") would need a new code and catalogue entry.

## Fix round r4 (review N5, N6, N7; bounds by resource)

The r3 element budget held for what it counts. r4 bounds every other resource an upload can consume, each before
the work it limits (`xlsx.py`, `layouts_v1.py` `split_file` and `_invisible`).

**What changed:**
- **N5, inflated bytes.** Every member is read through `_member`: `z.open(info)` and `read(64 KiB)` in a loop
  (`ZipExtFile.read(n)` gives the decompressor `n` as its output limit), with a running count refused past
  `min(_MEMBER_MAX, what is left of _TOTAL_MAX)`. The declared size is no longer trusted (the infolist pre-check
  stays as a cheap first filter). A lying header now inflates only to its declared size: the trailing stream is
  never inflated. Members compressed with bzip2 or lzma are `NATIVE_WORKBOOK` (their decompressors in `zipfile`
  take no output limit; Excel writes deflate only).
- **N6, characters.** Every cell value the sheet parse delivers charges its length to one workbook-wide budget,
  `_CHAR_MAX = 16 Mi` characters (shared strings on every reference, inline strings, numbers, booleans); past it
  `NATIVE_WORKBOOK`, raised inside the parse. `_invisible` is now one precompiled regex character class built once
  from the per-character rule (`_flagged`) over every code point; a test proves the class flags exactly the rule's
  code points, so verdicts are unchanged and the per-character cost is the regex engine's.
- **N7, rows and cells.** `split_file` stops one kept row past `MAX_RECORDS` (10,001 rows; the batch then refuses
  `CANONICAL_RANGE batch.records`, as it did for any longer file), on CSV by breaking the reader loop and on XLSX
  inside the parse (`xlsx_sparse_rows(..., after=header_row, keep=MAX_RECORDS)`). CSV rows are kept as they come,
  each cut to the layout's width plus one cell (a longer row is a count mismatch either way), and the header row to
  the same width plus one (a longer header mismatches either way).

**Every resource and its bound** (both paths):

| Resource | XLSX bound | CSV bound |
|---|---|---|
| Upload bytes | 8 MiB (`MAX_UPLOAD_BYTES`), profile sample 1 MiB; checked before any read | same |
| Zip members listed | central directory inside the upload (a 17.9 MB directory of empty members, twice the cap, lists in 1.49 s, 166 MB) | n/a |
| Members read | four named ones only | n/a |
| Inflated bytes | counted as inflated: 16 MiB a member, 64 MiB in total (N5) | n/a |
| Compression method | stored or deflate only | n/a |
| XML elements (rows, cells, `<si>`, sheets, nesting) | `_WORK_MAX` 500,000 starts across members (r3) | n/a |
| DTD/entities | refused (r3) | n/a |
| Characters delivered by cells | `_CHAR_MAX` 16 Mi a workbook, charged per reference (N6) | at most the decoded upload (8 Mi characters) |
| Characters in one field | member size | `csv.field_size_limit` 131,072 (stdlib default; a longer field is `NATIVE_ROW`) |
| Kept data rows | `MAX_RECORDS` + 1, stops the parse (N7) | `MAX_RECORDS` + 1, stops the reader (N7) |
| Cells kept a row | the layout's width plus one (r3) | the layout's width plus one (N7) |
| Cells in one physical row (transient) | elements, under `_WORK_MAX` | the upload bytes: one 8 MiB row of 2.7 M fields peaks at 253 MB RSS, then is cut |
| Blank or skipped rows | elements, under `_WORK_MAX` | the upload bytes: 8 Mi blank lines read in 1.56 s, 91 MB (none kept) |
| Row numbers, column letters, numbers | rise strictly, at most 1,048,576; XFD; a double's exponent range (r3) | n/a |
| Padding | `_PAD_BUDGET` 2,000,000 (`xlsx_rows` only) | n/a |
| Per-row work after the read (`read_rows`, `_coverage`, `run_probes`, digests) | kept rows times layout width, characters under `_CHAR_MAX` | kept rows times layout width, characters under the upload |

**Adversarial tests** (`contracts/tests/test_3a6_profiles.py`, section "N3 r4", 12 tests, each bounded on time in a
plain run and on peak memory in a traced run where it matters): a 200 MiB size lie (about 200 kB upload) reads
`ok 3` under 1.0 s and 30 MB; inflated bytes counted against the member and total caps; bzip2 and lzma refused; a
1,000,000-character shared string referenced from 1,000 rows refused under 1.0 s and 60 MB; 10 references under
the budget read as before; inline characters charged to the same budget; the stated bounds pinned; the regex class
equal to the per-character rule over every code point; 1,048,576 CSV rows stop at 10,001 under 1.0 s and 40 MB;
a CSV at exactly 10,000 rows reads every row; CSV rows of 100,000 fields kept at width plus one under 50 MB; 100,000
non-empty XLSX rows stop at 10,001. The 21 r3 adversarial tests are kept; one changes its expected outcome:
`test_n3_r3_near_member_cap_sheet_...` now ends at the row ceiling (`ok 10001`, refused by the batch) before the
work bound (was `NATIVE_WORKBOOK`), still under its 3.0 s and 120 MB bounds.

**Plants** (applied, run with `-k r4` under `ulimit -v 6 GB`, reverted with `git checkout`; tree clean after each;
log `plants.log`):
- P1 `z.read` restored: 3 fail (size lie, caps, bzip2/lzma).
- P2 character charge removed: 2 fail (shared-string references; inline characters); the run took 61 s.
- P3 CSV row ceiling removed: the CSV ceiling test fails (44 s run).
- P4 CSV width-plus-one cut removed: the wide-row test fails.
- P5 XLSX row ceiling removed: the XLSX ceiling test fails.
- P6 compression-method check removed: the bzip2/lzma test fails.
- P7 total-bytes count removed: the caps test fails.

**Measurements** (fresh process per probe, max RSS includes about 25 MB baseline; files built into the evidence
folder and deleted after measuring; `probes.log`):

| Probe | Upload | Outcome | Time | Max RSS |
|---|---|---|---|---|
| N5: 1,000 MiB size lie (2,024 MB, 3.69 s at review) | 1,021 kB | `ok 3` | 0.33 s | 37 MB |
| N6: 1 M-character shared string, 100 rows (17.4 s at review) | 4.4 kB | `NATIVE_WORKBOOK` | 0.03 s | 43 MB |
| N6: same, 10,000 rows | 55.2 kB | `NATIVE_WORKBOOK` | 0.04 s | 43 MB |
| N6: 16 MiB shared string, 10,000 rows | 69.6 kB | `NATIVE_WORKBOOK` | 0.19 s | 83 MB |
| N7: 8 MiB of `x\n` (11.8 s, 2,536 MB at review) | 8,388 kB | 10,001 read, batch `CANONICAL_RANGE` | 0.09 s | 93 MB |
| N7: 8 MiB of `;;;;;;;;\n` (11.36 s, 551 MB at review) | 8,388 kB | 10,001 read, batch `CANONICAL_RANGE` | 0.50 s | 93 MB |
| CSV: 8 Mi blank lines | 8,389 kB | `ok 0` | 1.56 s | 91 MB |
| CSV: one row of 2.7 M fields | 8,100 kB | `ok 1` (row refused) | 0.39 s | 253 MB |
| XLSX: 249k `<row><c t="b"/></row>` (4.54 s at review) | 14.5 kB | 10,001 read, batch `CANONICAL_RANGE` | 0.63 s | 50 MB |
| XLSX: 17.9 MB directory of empty members (over the cap) | 17,899 kB | `ok 3` | 1.49 s | 166 MB |

Worst found: time 1.56 s (8 Mi blank CSV lines), memory 253 MB (one CSV row of 2.7 M fields); both bounded by the
8 MiB upload cap and only transient. The profile admission path reads the sample twice, at 1 MiB.

**Legitimate verdicts.** The r3 differential (round-2 reader `a141bab51` against `xlsx_sparse_rows`, 3,000 random
sheets, seed 7): 0 mismatches. A new read-level differential (`diff_read.py`: 1,500 random kobo CSVs and budget
XLSXs under the ceiling, with blank lines, short, long and 30-field rows, multi-line quoted fields, invisible
characters, missing headers, an unterminated quote; read by `read_layout` from the pre-r4 tree `ed9bd5f0c` and
from r4): 0 mismatches (1,301 read with refused rows, 96 clean, 64 `NATIVE_HEADER`, 39 `NATIVE_ROW`).

**Known deviations:**
- A file past 10,000 data rows now gets `CANONICAL_RANGE` even when a malformed CSV row (formerly `NATIVE_ROW`)
  sits past row 10,001; both refuse the file.
- A profile sample past 10,000 rows is refused `ADMIT_SAMPLE_SIZE` with `rows: 10001` (meaning more than 10,000),
  not its full count.

**Follow-up (not built, no new served text):** the bounds refuse with `NATIVE_WORKBOOK` and its words. A dedicated
`NATIVE_TOO_LARGE` ("this file holds more than one upload can take") would cover the element, character and row
bounds; it needs SC-1 text and an Architect ruling after SC-1a merges.

**Checks at r4** (code and tests at `72bc785cd`):
- Non-DB, `heavy-slot.sh -- pytest contracts/tests` plus 3A6 service and command, 3A3 contract, single writer and
  loader, run-store loader, 3A2 service and API, 3B7a seam and snapshot, ON1 (4 files), RC4-F1: `656 passed in
  104.91s` (wall 214 s).
- Postgres, `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1` (routed `*_test`): 3A6, 3A3 loader, 3A2, ON1,
  3B7a snapshot: `59 passed in 50.25s`, none skipped.
- Fast check-all: `All 41 guards passed` (239.7 s; the first attempt timed out waiting for a heavy slot held by other lanes, exit 75, and was rerun).
- Evidence: `/opt/assetecon/evidence/3A6/2026-11-21/r4/` (run logs, plant script and log, probe script and log,
  both differentials).
