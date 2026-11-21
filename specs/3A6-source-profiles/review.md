# 3A6 review, round 1 (discovery, W5)

Reviewer: fresh Claude reviewer (did not author 3A6). Branch `task/3A6-source-profiles`, head `f3ccbd0b1`, worktree
`/opt/assetecon/AssetOpsV1-3a6`; read only. Judged against `spec.md` rev 2, `rulings.md` (D-3A6.1 to D-3A6.17 and
handshake answers), `reviewer-guide.md` rev 2, `packet.md`, `mid-build-questions.md` Q1.

## Summary (round 1)

- **Verdict: accept with findings fixed on the branch.** One High (F1) and one Medium (F2) are code fixes that stay
  inside 3A6. F3 is a spec-level gap for the Architect: the packet's stated way around it is closed by 3A6's own rules.
- F1 High: a tiny XLSX file makes the reader allocate a huge padded cell list. A 1.6 KB file gives 32.7 M cells,
  about 270 MB and 2 s. Any analyst upload can exhaust the server's memory.
- F2 Medium: deviation 7 (coverage runs before the row refusals) crashes with `IndexError` when a CSV sample has a
  short row. That should be `ADMIT_SAMPLE_ROW NATIVE_ROW`.
- F3 Medium (Architect): a new version that changes `personal` leaves the unchanged rows refused on every later
  upload, and their old values stay stored raw. A new `profile_id` cannot get round it: it is refused with
  `PROFILE_SOURCE_SYSTEM_TAKEN`, or with `UPLOAD_SOURCE_SWITCHED` when it names a new system.
- Lows: F4 (a formula with no cached value reads as empty), F5 (`isdigit` on a row number lets a `ValueError` out),
  F6 (S1 misses aliases made by assignment and `from assetops_backend import commercial`), F7 (Q1's substitute value
  is not a canonical status), F8 (an unlisted literal), F9 (an undisposed store).
- Everything else hunted holds: honesty checks 4a/4b/4c, the serial window, `YYYYMM` read as text, cell marks, the
  invisible rule, the switch rule with Site narrowing and the re-check under the lock, coded probes derived from the
  canonical side, hashes only stored, migration chain and downgrade, and the S1 clauses with their plants.
- Checks rerun: focused 323 passed; Postgres 3A6 file 3 passed; both guards passed; 4 plants of my own, each failing
  its test.

## Checks I ran (revision f3ccbd0b1; it differs from the builder's 43b1040a8 only by the packet, spec status, state)

PYTHONPATH = worktree `backend:backend/tests:contracts:simulator:gateway:field:host:tools`. `assetops_backend`,
`assetops_contracts` and `assetops_simulator` resolve to `/opt/assetecon/AssetOpsV1-3a6/...` (printed).

| Check | Result |
|---|---|
| `heavy-slot.sh -- pytest` contracts `test_3a6_profiles.py`; backend `test_3a6_source_profiles.py`, `test_3a6_source_profile_command.py`, `test_3a3_source_contract.py` (contract suite, 5 cases), `test_3a3_single_writer.py`, `test_3a3_load_emulated.py`, `test_3a2_commercial_upload_service.py` | `323 passed, 1 warning in 32.32s` |
| `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- backend/tests/test_3a6_source_profiles_postgres.py` (pg_harness clone `*_pt<run>_*_test`) | `3 passed, 7 warnings in 5.26s` (run twice) |
| `pwsh tools/check-architecture.ps1` (ASSETOPS_GUARD_PYTHON = main venv) | `Architecture check passed.` |
| `pwsh tools/check-agent-workflow.ps1` | `Agent workflow check passed.` |
| Digests recomputed by hand (plain sha256) | PL-1001 `r7a74ac02930cf9bd`, budget Diesel `r4bc1868e230b8ed3`; files `de793415be17…`, `df247815c6c6…`: all match spec §4 |
| `main` since merge-base `26dd65e60` | 12 commits, no new migration; 0067 stays the only child of 0066 |

Cited, not rerun (same code revision `43b1040a8`, evidence `/opt/assetecon/evidence/3A6/2026-11-21/`): no-database
regression `792 passed in 78.16s`; Postgres set `80 passed in 56.60s`; fast check-all `All 41 guards passed`; plants
V1 to V32 in `plants.txt`.

**My plants** were run in the scratch copy `scratchpad/r3a6/plantcopy-r3a6rev1`, a `git archive` of HEAD. Each was
applied, run and reverted.

| Plant | Fails |
|---|---|
| V22 (4b skipped: `for key in ():`) | `test_a9_coverage` |
| V16 (Site narrowing dropped: `and bool(sites)`) | `test_u3_one_source_system_per_site` |
| Own: the `sys.modules["assetops_backend.commercial..."]` subscript clause removed | `test_s1_each_clause_has_its_plant[p10]` |
| Own: 4c dates judged only on `date` paths (`_DATED = ("date",)`; the kobo dates are `datetime`) | `test_a10_ambiguity` |

The copy holds no `tools/` or `host/`, so `test_s1_allowlists_are_exact` fails there with or without a plant. That is
an artefact of the copy, not a finding.

## Findings

### F1 High: an XLSX file can force a huge padded cell list (memory and CPU exhaustion through the intake)

- **Where:** `contracts/assetops_contracts/native/xlsx.py:133` (`while len(cells) < index: cells.append("")`), with
  `_REF` taking up to three letters at :27.
- **What:** each `<c r="XFD1"/>` pads its row to 16,384 cells (`ZZZ` gives 18,278) before any header is known. I ran
  `<row><c r="XFD1"/></row>` × 2,000, deflated:
  - file: 1,647 bytes;
  - result: 32,768,000 cells, about 270 MB peak, 2.1 s.
  The cost grows linearly with the row count. The 16 MiB member cap allows about 700 k such rows, which is billions
  of cells, from an upload far under the 8 MiB limit.
- **Why it matters:** `LayoutReader.read`, then `split_file`, then `xlsx_rows`, runs on every upload's check through
  a profile, before the header comparison. Anyone with `commercial.upload` can stall or kill the shared server. The
  spec's member-size caps were meant to bound memory, and they do not bound this.
- **Fix:** keep each row sparse, as `{index: value}`, in `_read`. `split_file` then pads only to the header's length,
  and treats a non-empty index at or beyond the header's length as the count mismatch that refuses the row (what
  §2.2 point 4 already says). Alternatively, refuse `NATIVE_WORKBOOK` for a column index above 16,383 or a total
  padded-cell budget above a cap. Add an N3 case with one cell at `XFD` that asserts bounded work, plus a plant.
- **Kind:** an acceptance gap against the intent of D-3A6.9 and D-3A6.13 (caps bound the reader). The spec does not
  name it.

### F2 Medium: deviation 7 crashes admission on a short CSV row

- **Where:** `backend/assetops_backend/commercial/profiles.py:130` and `:135` (`cells[i]`), called at `:232` before
  the row verdicts.
- **What:** CSV rows from `split_file` are not padded. The kobo sample with PL-1002's last cell removed (or PL-1001's)
  gives `IndexError: list index out of range` out of `check` and `admit`, so the command exits with a traceback.
  Probe: `scratchpad/r3a6/probe2.py`. Under the spec's order, the row verdict would give `ADMIT_SAMPLE_ROW` with
  `NATIVE_ROW` (the P2 class).
- **Why it matters:** a trailing short line is common in real exports ("End of report", a totals line with fewer
  delimiters). The analyst gets a crash, not the plain refusal, and no test covers it.
- **Fix:** in `_coverage`, judge only rows whose length equals the header width; the row verdict that follows refuses
  the others. Add an A4 case: a short row gives `ADMIT_SAMPLE_ROW {row, code: NATIVE_ROW}` with the
  `admit_sample_row_whole` text.
- **Kind:** an acceptance gap (A4/P2 behaviour) brought in by the deviation. With this guard, deviation 7 itself is
  sound (see Judgements).

### F3 Medium (Architect): a `personal` change has no way forward, and the packet's stated way round it is closed

- **Where:** `packet.md:75-76` (residual), and the design of D-3A6.16 with §2.2's row digest. The digest is taken
  before pseudonymisation, so it ignores `personal`.
- **What I saw (memory world, `scratchpad/r3a6/probe2.py`, `probe3.py`):**
  - v1 is admitted, uploaded and accepted, then v2 (with `personal: [["body.counterparty_ref","P"]]`) is admitted.
  - The same export with PL-1001 corrected gives "0 new, 1 corrected, 1 already held, 2 refused". The refusals are
    rows 5 and 6, `INTAKE_VERSION_CONFLICT`, worded "send the correction as a new version", which the operator cannot
    do.
  - The packet's way round it: a new `profile_id` with the same `source_system` is `PROFILE_SOURCE_SYSTEM_TAKEN`. With
    a new `source_system` it is admitted, but its upload is 409 `UPLOAD_SOURCE_SWITCHED`.
- **Why it matters:**
  - Every later full-ledger upload carries permanent refusals.
  - The records the analyst has just declared personal stay stored with the raw value, and nothing can pseudonymise
    them. That goes against the purpose of PII-1 and RC4.
  - The packet understates this.
- **Options (Architect's call):**
  - Fold the profile's `personal` declaration into the row digest, so a change revises every record. This could apply
    only when `personal` is non-empty, which keeps the kobo literals.
  - Refuse a new version whose `personal` differs, under `PROFILE_LINEAGE`, until a retire act exists (queue Q1).
  - For column or constant versioning, state the limit in the words.
- **Kind:** a spec gap, not a build defect. A2 builds what the spec says. It does not block this round's fixes, but
  the packet residual must be corrected either way.

### F4 Low: a formula cell with no cached value reads as an empty cell

- **Where:** `xlsx.py:97`.
- **What:** `<c r="A2"><f>SUM(B1:B9)</f></c>` (no `<v>`, as a generator that does not compute values writes it)
  becomes `""`. In an optional path such as `quantity.value` the value disappears silently. 4a protects only the
  sample, not later uploads.
- **Fix:** a cell with `<f>` and no `<v>` becomes `XlsxBad("")`, so a written column refuses the row with
  `NATIVE_FORMAT`.

### F5 Low: a row number in Unicode digits lets a `ValueError` out

- **Where:** `xlsx.py:127`.
- **What:** `r.isdigit()` is true for `"²"`, and then `int("²")` raises `ValueError`, which `xlsx_rows` does not catch
  (seen). The upload answers 500.
- **Fix:** `re.fullmatch(r"[0-9]+", r, re.ASCII)`.

### F6 Low: two S1 blind spots are not named in the residual

- **Where:** `backend/tests/test_3a3_single_writer.py:156` and `:170` (clauses on `Call` only), and `:110`
  (`_imports_package`).
- **What:**
  - `im = importlib.import_module; im(name)`, `e = eval; e(s)` and `g = getattr; g(svc, name)` pass, because only
    calls are matched, not references.
  - `from assetops_backend import commercial` is not counted as importing the package, so `S1-INGEST`, `S1-ATTR` and
    `S1-OPERATOR` do not apply in such a module. This part is inherited from 3A3.
- **Fix:** flag any load reference whose qualified name is in `DYNAMIC_CALLS` or `EVAL_CALLS` (as `S1-SYSMOD`
  already does). Count `ImportFrom(module="assetops_backend", names∋"commercial")`. Add two plants. Otherwise, add
  both to the D-3A6.14 residual in the packet.

### F7 Low (preference): Q1's substitute maps to a status that does not exist

- **Where:** `test_3a6_source_profiles.py:310`.
- **What:** `"Quote": "DRAFT"`. The expense statuses are `QUOTE`, `INVOICED` and `PAID` (`records_v1.py:205`).
  `"Quote": "QUOTE"` is one to one, a valid status, and still uncovered.

### F8 Low: an unlisted literal change

- **Where:** `backend/tests/source_contracts.py:109`.
- **What:** the kobo case's `bad_clock` is `"2026-10-11T09:00:00"`, where §4.1 gives `2026-10-11 09:00`. Both refuse
  with `NATIVE_FORMAT`. Use the spec's literal, or list the change.

### F9 Low: an undisposed store

- **Where:** `load_emulated_exports.py:199`.
- **What:** `build_source_profiles(url)[0]` drops the `dispose` and leaves a second engine open for the command's
  life. Keep it and call it in a `finally`.

## Judgements asked

- **Q1 (substitution):**
  - Sound for what A9(a) tests: 4b fires on the uncovered key `Quote` before any value is judged, so the substitute
    exercises exactly the gate, and V22 fails it (rerun above).
  - It cannot show the spec's motivating error (`Quote`→`INVOICED`, a wrong meaning), but that error is caught by the
    expected-record compare once covered, not by 4b.
  - Prefer `QUOTE` (F7).
  - The question itself (may profile maps be many to one?) is real for operator exports ("Paid" and "Paid in full").
    It is the Architect's to rule. Many to one would be safe for profiles, because 4b and the expected records reach
    every key and profiles are never rendered.
- **Deviation 5 (`held_uploads` in 3A2's `UploadMemoryStore`):** accept.
  - It is needed: §2.6 makes every check call `held_uploads`.
  - It is test-only, and it is the 3A3 mirror moved, not new behaviour.
  - It matches `_HELD`: waiting or accepted, ordered by id (string order equals Postgres uuid order), with
    `source_system` and `site_codes` (None first).
  - Done 11's wording should be amended to list it.
- **Deviation 6 (`code_digest.py` allowlisted):** accept. `structure_snapshot/adapters/code_digest.py:26` calls
  `importlib.util.find_spec("assetops_contracts")`, which runs no code, and `test_s1_allowlists_are_exact` needs the
  entry.
- **Deviation 7 (coverage before row refusals):** sound in intent. A9(b)'s spec literal needs it, because 2a refuses
  FUEL rows without `Litres` first. As built it crashes on short rows (F2); with F2's guard, accept.
- **The residual (`personal` change):** understated (F3). The way round it in the packet does not exist.

## Hunt results with no finding

- **Honesty:**
  - 4a, 4b and 4c are implemented as specified. The swapped date formats (`MM.DD.YYYY`, `MM-DD-YYYY`) work, because
    `_date_pattern` builds from any form.
  - Instants are excluded, and `XlsxNumber` cells are excluded.
  - The serial window is checked before arithmetic. `YYYYMM` `XlsxNumber` is read through the grammar.
  - `XlsxBad` is judged only in written columns.
  - The invisible rule covers Cc, Cf, Zl, Zp and Cs on written columns only.
  - Residual beyond the spec, for the Architect's sweep: an interior U+00A0, U+3000 or U+034F inside a ref is not
    refused (Zs and Mn), and can still split a pseudonym.
- **Source system:**
  - `_refuse_switch` compares source system and Sites, not reader ID, with None as a Site key.
  - `decide` does not re-run `_check`, so two waiting uploads cannot block each other.
  - `_SWITCHED` runs under `_LOCK` after `_decided` and before `decide`, and only ACCEPTED uploads count.
  - The memory mirror wraps `decide`. Q3 shows nothing written and the upload still WAITING.
- **Coded probes:** `coded_headers` reads `CODED_PATHS_EXPECTED` and never `Column.maps`.
- **Data stored:** `ProfileRow` holds the profile text, three SHA-256s and a count. Refusal params are profile keys,
  headers and paths, never sample cells.
- **RC4:**
  - The command does not refuse operator databases, by design (§2.7; it composes through
    `commercial_upload_settings`).
  - The loader keeps `refuse_operator_database` first.
  - The Postgres test reads only `ASSETOPS_TEST_DATABASE_URL`, and the harness clones a `*_test` database. My runs
    touched only that.
- **Migration:**
  - `0067_source_profile` revises `0066_structure_snapshot`; Q1 asserts the link.
  - The append-only trigger is present.
  - The downgrade refuses while rows exist, then drops the trigger and the table.
  - The unique keys are named, as `_UNIQUE_KEYS` expects.

## Could not verify

- The full no-database and Postgres suites at this revision (cited, not rerun).
- Plants V1 to V32 beyond my four (cited from `plants.txt`).
- Windows host behaviour.

## Residual risk the packet does not name

- F1's class reaches CSV only through the 8 MiB limit, so CSV is bounded. XLSX is not.
- `fold=0` silently picks the first of a repeated local hour in zones with DST. Nairobi has none; a European
  operator's export would.
- The profile reader does not check `status` against the database at upload time. It relies on admission and upload
  happening on the same database, which holds today.


## Round 2 (verification re-review at 3fb8ed114; verdict REVISE)

### Summary (verdict: REVISE)

- F1 is fixed for far-right cells in data rows, but not for the same class one row up. A far-right
  cell in the header row sets `width` to 16,384, and `split_file` then pads every data row to that width before
  `read_rows` compares the header. The blow-up is still there (N1, High).
- F2, F3/D-3A6.18 (memory and Postgres), Q1/D-3A6.19 (QUOTE), F4, F5, F6, F8 and F9 are fixed as ruled. I found no
  regression in row-count verdicts, formula cells or row numbers.
- Two Lows: (N2) a sample-only change after acceptance has no test, and (N3) the packet's wording and plant labels
  differ from the ruling.
- Checks: 180 non-DB tests passed, 4 Postgres tests passed, and the F1 padding plant fails its test.

### Findings

### N1 High: the F1 class is still open through the header row (`contracts/assetops_contracts/native/layouts_v1.py:318-325`)

- **Wrong.** `header` is padded densely to its last non-empty cell (`range(max(sparse) + 1)`), so a header cell
  at XFD gives `width = 16384`. Every data row is then built as `[sparse.get(i, "") for i in range(width)]`. All of
  this happens inside `split_file`, before `read_rows:356` refuses the header as `NATIVE_HEADER json`. The cap
  `_MAX_COLUMN` and the sparse reader keep each row small, but this padding brings the cost back.
- **Seen.** I took the budget workbook and added one header cell `XFD1` plus N one-cell rows:
  - N=100: peak 14.4 MB, 2.35 s.
  - N=1,000: peak 137.6 MB, 22.9 s, ending in `NATIVE_HEADER`.
  - The cost grows linearly. A sheet member under `_MEMBER_MAX` holds about 341k such rows, which is 5.6e9 padded
    cells. Uploads are capped at 8 MB (`uploads.py:44`) and identical rows deflate to almost nothing, so one small
    upload or profile sample can exhaust the host. The F1 test only puts far cells in data rows, so it cannot see
    this.
- **Why it matters.** This is the same risk F1 was ruled High for, reachable through the upload and admission paths.
- **Fix.** Bound the padding by the layout, not the file:
  - In `split_file`, refuse `NATIVE_HEADER json` as soon as the trimmed header differs from
    `[c.header for c in layout.columns]`, before any row is built; or
  - pad to `len(layout.columns)`, keeping the one-extra-cell rule.

  Then add an N3 case with a header cell at XFD over a few thousand rows, bounded the same way as the F1 test, and
  a plant that restores header-width padding.

### N2 Low: no test for a sample-only change after acceptance (`backend/tests/test_3a6_source_profiles.py:211`)

- **Wrong.** D-3A6.18 and spec A2b say that once an upload is accepted, a v2 that changes only the sample is still
  admitted. A2b covers the reordered-set case but not the sample-only case.
- **Why it matters.** The code path is the same one the reordered case exercises, so the risk is small.
- **Fix.** Add one assertion.

### N3 Low: the packet wording differs from the ruling (`specs/3A6-source-profiles/packet.md`, "Fix round r1")

- **Wrong.** The residual is shortened from the text D-3A6.18 gives.
- **Wrong.** The plant labels are swapped. The ruling has V34 = waiting uploads counted and V35 = ordered compare;
  the packet has V34 = order-sensitive and V35 = waiting.
- **Why it matters.** It is documentation only.

### Finding by finding

- **F1.** Fixed for data rows:
  - Rows are kept sparse and the column index is capped (`XFE` gives `NATIVE_WORKBOOK`).
  - 5,000 rows at XFC, 1,000 rows apart, took 6.8 MB and 0.44 s.
  - 5,000 rows holding only an empty XFD cell are skipped: 6.8 MB and 0.32 s.
  - The plant restoring dense padding in `_read` fails `test_n3_far_right_cells...`, after a 182 s run.

  Still open through the header row: see N1.
- **F2.** Fixed. `_coverage` keeps only rows of header width, and A4's short row 5 gives `ADMIT_SAMPLE_ROW`
  `NATIVE_ROW`. One side effect: if a map key appears only in a short row, the refusal is `ADMIT_MAP_UNCOVERED`, not
  the row's own verdict. This follows from deviation 7, which was accepted, so it is not a finding.
- **F3 / D-3A6.18.** Fixed:
  - `personal` is compared as a set.
  - `held_uploads` returns uploads with no decision or an accepted one, so `not h.waiting` means accepted.
  - The system is filtered, nothing is written, and the words match.
  - Q2b, the Postgres twin, covers a waiting upload not counting and the refusal writing nothing.
- **Q1 / D-3A6.19.** Fixed: A9 (a) uses `QUOTE`, in both the spec and the test.
- **F4.** Fixed: a formula with no `<v>` becomes `XlsxBad`, which gives `NATIVE_FORMAT` on a written column (test
  present).
- **F5.** Fixed: the row number is checked with an ASCII `fullmatch`, and `²` gives `NATIVE_WORKBOOK`.
- **F6.** Fixed: references to `DYNAMIC_CALLS` and `EVAL_CALLS` are now flagged, `from assetops_backend import
  commercial` counts as importing the package, and plants p26 to p28 cover these.
- **F8.** Fixed: the literal is `2026-10-11 09:00`.
- **F9.** Fixed: the loader's disposers run in `main`'s `finally`.

**Regressions checked.**
- Row counts: rows with extra non-empty cells past the header are still `NATIVE_ROW`, and rows with only trailing
  empty cells are still equal to the header width.
- Cells without a ref take the next index, which is the same as before.
- `xlsx_rows` keeps its padded shape under a 2 M cell budget.

None found.

### Checks run (at `3fb8ed114`)

- Non-DB: 180 passed in 19.25 s, with the worktree's backend, contracts and simulator on `PYTHONPATH`. Command:
  `heavy-slot.sh -- pytest contracts/tests/test_3a6_profiles.py backend/tests/test_3a6_source_profiles.py
  backend/tests/test_3a3_single_writer.py contracts/tests`.
- Postgres: 4 passed in 5.67 s. Command: `heavy-slot.sh --db -- pytest backend/tests/test_3a6_source_profiles_postgres.py`,
  with `ASSETOPS_TEST_DATABASE_URL` set to `.../assetops_test`; the harness runs on its own clone.
- Probes: header-far, sparse-rows and wide-empty workbooks (in the scratchpad), with the results above.
- Plant: dense padding restored in a scratch copy of `contracts`. The F1 test failed.

### Not verified

- The full suite and the architecture and workflow guards: I relied on the implementer's run at `c727f97dd`.
  `3fb8ed114` adds only the packet commit on top.
- I did not re-run the S1 plants p26 to p28 one by one beyond the suite passing.

### Residual risk

- After N1 is fixed, the cost is bounded by the layout's column count times the rows, both of which the member cap
  limits.
- D-3A6.21's residuals stand as recorded.

### Fix round r2 outcome

N1, N2, N3 fixed in the commit after 3fb8ed114 (see packet.md "Fix round r2"). N1 probe after the fix: header cell XFD1 over 2,000 one-cell rows refuses NATIVE_HEADER in 0.15 s, under the 20 MB bound; the old order peaks at 274.6 MB.

## Round 3 (verification re-review at a141bab51; verdict REVISE)

### Summary (verdict: REVISE)

- N1 is fixed for the case it named: a header cell at XFD now refuses `NATIVE_HEADER` before any data row is
  built, and data rows pad only to the layout's width. The plant (old order) fails the new test.
- The same class is still reachable one step earlier: the header row itself is padded to the file's widest cell,
  and it is rebuilt once for every row numbered `header_row`. Duplicate `r="1"` rows make that a CPU bomb (N4, High).
- N2 and N3 are fixed as ruled. Legitimate files read as before.
- Checks: contracts suite plus 3A6 backend, 139 passed; 3A6 Postgres, 4 passed; the N1 plant fails.

### N4 High: the header row is padded to an unchecked width, once per duplicate row (`contracts/assetops_contracts/native/layouts_v1.py:316-318`)

- **Wrong.** `split_file` loops over every sheet row and, for each one numbered `header_row`, builds
  `[sparse.get(i, "") for i in range(max(sparse) + 1)]`. `_read` does not refuse repeated or decreasing row
  numbers, so a sheet of N rows `<row r="1"><c r="XFD1"><v>1</v></c></row>` builds N lists of 16,384 cells
  before the new check runs. Memory stays flat, because each list is discarded, but the time grows with N.
- **Seen** (no tracemalloc; deflated as an upload would be):
  - 1,000 rows: 0.95 s. 10,000 rows: 9.68 s. 40,000 rows: 37.8 s (the parse alone is 0.41 s). The file is 6.6 kB.
  - A member at the cap holds 409,200 such rows and deflates to 49 kB, which is under the 1 MB sample cap and the
    8 MB upload cap. That is about 6.5 minutes of CPU for each request.
  - The last duplicate wins: 10,000 rows of `r="1"` holding an empty XFD1 cell, then a valid header, read as `ok`
    after 9.2 s.
- **Why it matters.** This is the cost F1 and N1 were ruled High for, through the same upload and admission paths.
  The bound is now on memory but not on time.
- **Fix.** Do either or both of these:
  - Build the header without padding past the layout. Compare the non-empty sparse cells with the layout's headers,
    or pad to `len(layout.columns)` and refuse if any non-empty cell lies past that width.
  - Take the first row numbered `header_row` and stop there, or refuse repeated or non-increasing row numbers in
    `_read` as `NATIVE_WORKBOOK`.

  Add a test with a few thousand duplicate `r="1"` rows holding XFD1, bounded on time like the N1 test, and a plant
  that restores `range(max(sparse) + 1)` for the header.

### Probes (scratch, at a141bab51; peak memory from tracemalloc unless stated)

- **P0, golden budget workbook.** 3 records, rows (2, 3, 4), no refusals.
- **P1, header XFD1 plus one-cell rows.**
  - 2,000 rows: `NATIVE_HEADER`, 2.6 MB, 0.11 s.
  - 20,000 rows: 26.2 MB, 1.07 s.
  - 200,000 rows (14.2 MB sheet): 263 MB, 11.4 s.

  The cost is linear in the parse and the same as a parse with no far cell (see residual risk).
- **P2, a far cell in an otherwise valid header.**
  - An empty `<c r="XFD1"/>` or an empty inline string reads `ok`, 3 records, which is unchanged.
  - XFD1 = "x" gives `NATIVE_HEADER`.
- **P3, a valid header plus 20,000 data rows at XFD.** 20,003 records with `NATIVE_ROW` on the far rows, 26.9 MB,
  1.86 s. Data rows pad only to the layout's width.
- **P4, duplicate header-numbered rows.** See N4.
- **Plant: N1 check removed (old order).** `test_n3_far_right_header_cell_is_refused_in_bounded_memory_and_time`
  FAILED.

**Sweep for padding.** The remaining padding sites are these:
- `layouts_v1.py:318` (the header, N4).
- `:329` (rows, bounded by the layout).
- `xlsx.py:167` (`xlsx_rows`, under the 2 M cell budget; it has no caller outside contracts).

The only caller of `split_file` outside contracts is `commercial/profiles.py:233`, which comes after
`reader.read` and so after the same refusal.

### N2, N3

- **N2.** Fixed. A2b now admits a sample-only change as v4.
- **N3.** Fixed. The residual matches the text in D-3A6.18, and the V34 and V35 labels follow the ruling.

### Legitimate verdicts

- The suite passes the kobo and budget goldens, the formula-cell, row-number and row-count tests, and the
  illustrative goldens.
- In the probes, a trailing empty header cell still trims, and `NATIVE_HEADER json` is the same code and path as
  before. It is now raised in `split_file` rather than `read_rows`, and `read_rows` keeps its own check for CSV.

### Checks run

- Non-DB: `heavy-slot.sh -- pytest contracts/tests backend/tests/test_3a6_source_profiles.py` gave 139 passed in
  4.47 s, with the worktree's backend, contracts and simulator on `PYTHONPATH`.
- Postgres: `heavy-slot.sh --db -- pytest backend/tests/test_3a6_source_profiles_postgres.py` gave 4 passed in
  5.45 s, against `.../assetops_test`; the harness runs on its own clone.

### Not verified

- The full suite and the guards: I relied on the implementer's r2 run (495 non-DB, 59 Postgres, 41 guards).

### Residual risk

- The sparse parse itself costs about 19 times the sheet size in peak memory (P1 at 200k rows: 263 MB for a
  14 MB member). It is bounded by `_MEMBER_MAX` and was accepted in round 2.
- Under the 8 MB upload cap, repeated rows deflate well, so a member near the cap is reachable. Consider refusing
  on the header row before parsing the rest of the sheet if this matters at the host's memory size.
- Duplicate data-row numbers are kept as separate rows that share one number, so row-numbered messages can repeat.
  The N4 fix that refuses non-increasing numbers would close this too.

## Round 4 (fresh adversarial re-review at 84113ed14, code at c8a6d23c1; verdict REVISE)

### Summary (verdict: REVISE)

- N4 is fixed and the r3 work bound does what it says for what it counts: XML elements. Duplicate, falling,
  zero, overlong and missing row numbers, deep nesting, many attributes, many tags, DTDs and big numbers all stay
  bounded (table below). The 249k-row case reproduces (4.54 s, 151 MB) and is acceptable as bounded.
- The class is still open in two places the element count cannot see:
  - **N5 High.** A compressed member whose declared size lies is inflated in full before the size is checked. A
    1.0 MB upload took 2.0 GB of RSS and then read `ok`.
  - **N6 High.** One shared string is reused by reference in every cell that points at it, then scanned
    character by character in each row. A 4.6 kB upload took 17.4 s, and the cost grows linearly to hours.
- **N7 Medium.** The CSV path has no budget: an 8 MiB file of `x\n` took 11.8 s and 2.5 GB.
- The differential (2,000 random legitimate sheets, old reader against new) gave 0 mismatches. Contracts plus 3A6:
  160 passed. 3A6 Postgres: 4 passed.
- Open point: tell the operator the file is too large rather than "not readable" (recommended; Low, not blocking).

### N5 High: the member cap trusts the zip's declared sizes (`contracts/assetops_contracts/native/xlsx.py:295` and `_parse`, `z.read(name)`)

- **Wrong.** `_read` checks `ZipInfo.file_size`, which is the size the central directory claims. On Python 3.12,
  `z.read` inflates the whole compressed stream in one `decompress` call with no output limit, and only then cuts
  the result to the declared size. A sheet member that declares the small golden sheet's size and CRC, followed by
  a deflate stream of N MiB of spaces, passes the cap, allocates N MiB (twice, briefly), and then passes the CRC,
  because the cut bytes are the real sheet.
- **Seen** (a fresh process reading a saved file, baseline RSS 22 MB):
  - 200 MB lie in a 200.8 kB upload: 422 MB max RSS, `NATIVE_WORKBOOK`.
  - 1,000 MB lie in a 997 kB upload: **2,024 MB max RSS, 3.69 s, read `ok 3`**.
  - Deflate gives about 1,000:1, so the 8 MiB upload cap allows about 8 GB inflated (about 16 GB peak) per
    request, and the 1 MiB profile sample cap allows about 2 GB.
- **Why it matters.** This is the same small-file, host-sized-cost class as F1, N1 and N4, and it reaches past
  every later bound because it happens before parsing. The r3 audit row "member cap 16 MiB" relies on a header field
  the attacker writes.
- **Fix.** Read each member through `z.open(name)` with a bounded read, so the inflation itself is limited:
  `f.read(_MEMBER_MAX + 1)`, refused when longer. `ZipExtFile.read(n)` passes `n` as the decompressor's
  `max_length`. Also keep a running total against `_TOTAL_MAX` over the bytes actually read. Then add a test that
  splices a large deflate stream behind a small declared size, bounded on peak memory, and a plant that restores
  `z.read`.

### N6 High: shared-string amplification through `read_rows` (`layouts_v1.py:382` `_invisible`, and the joins after it; source `xlsx.py` `_Cell.value`, `shared[int(v)]`)

- **Wrong.** The work bound charges one unit per `<c>` and `<v>`, but a `t="s"` cell delivers the whole shared
  string. Every cell that references the same `<si>` gets the same Python string, so this is free in memory. Then
  `read_rows` runs `_invisible` on it, a Python-level loop over every character with `unicodedata.category`, once
  for each written cell. For the budget profile, `record_id_join` and `version_digest` also build a new string of
  that length for each record and hash it.
- **Seen** (shared string at index 0 is 1,000,000 `A`s; each row is the budget row with Site = `s0`; profiled time
  is 95% `_invisible`):

  | Rows | Upload | Time | Max RSS |
  |---|---|---|---|
  | 1 | 2.9 kB | 0.19 s | 27 MB |
  | 10 | 3.1 kB | 1.72 s | 35 MB |
  | 100 | 4.6 kB | 17.38 s | 122 MB |

  The cost is linear: about 0.17 s and 1 MB a row. A 10,000-row upload is about 170,000 elements, so it sits
  under the bound. It would come to roughly 30 minutes and 10 GB, still only tens of kB. With a 16 MiB shared
  string, each row costs about 16 times more.
- **Why it matters.** This is the class r3 was asked to close. The budget counts elements, but the work is
  proportional to the characters delivered.
- **Fix.** Charge characters too. Either:
  - when a `t="s"` cell resolves, charge `len(shared[i])` against a workbook-wide character budget (for example
    `_MEMBER_MAX` characters across all cells, which no legitimate export reaches); or
  - also refuse any cell longer than Excel's own limit of 32,767 characters, which is defence in depth but not
    enough alone (250k cells times 32k characters).

  Then add a test with one long shared string referenced by a few thousand rows, bounded on time, and a plant.

### N7 Medium: the CSV path is outside the budget (`layouts_v1.py` `split_file`, CSV branch `all_rows.append`)

- **Wrong.** The packet states that CSV rows are bounded by the 8 MiB upload cap. They are bounded, but not to a
  small cost:
  - `kobo` profile, 8 MiB of `;;;;;;;;\n` (932,051 rows): 11.36 s, 551 MB, `ok 932051`.
  - 8 MiB of `x\n` (4,194,230 rows, all `NATIVE_ROW`): **11.80 s, 2,536 MB**.

  `parse_batch` refuses anything above `MAX_RECORDS = 10,000` only after the full read. The reader before 3A6
  was also unbounded in row count, but it streamed rows into records. 3A6 lists every row first, and now serves
  tenant-written profiles.
- **Why it matters.** This is the same cost class. It is Medium rather than High because the shape predates the
  slice and needs the full 8 MiB upload rather than a few kB.
- **Fix.** Bound rows on both paths by the batch ceiling, not by the bytes. In `split_file`, refuse as soon as kept
  data rows pass `MAX_RECORDS`, and stop iterating at once, on CSV and XLSX alike. That also brings the 249k XLSX
  case down to about 10k rows (about 0.2 s). Add a CSV test at the cap and a plant.

### Probes that held (fresh process each; max RSS includes about 22 MB of baseline)

| Probe | Upload | Outcome | Time | RSS |
|---|---|---|---|---|
| 499k nested elements in one cell | 5.8 kB | ok | 0.90 s | 147 MB |
| one element, 600k attributes | 1.4 MB | ok | 1.19 s | 200 MB |
| 400k distinct tag names | 0.9 MB | ok | 1.26 s | 188 MB |
| 200k `xmlns:` declarations | 1.0 MB | ok | 0.37 s | 91 MB |
| one 15 MiB inline cell (written column) | 16.8 kB | ok | 2.76 s | 82 MB |
| 15 MiB-digit amount | 16.8 kB | ok | 0.25 s | 88 MB |
| 200k long-number rows | 1.0 MB | `NATIVE_WORKBOOK` (bound) | 0.00 s | 92 MB |
| 240k shared strings | 11.6 kB | ok | 0.67 s | 37 MB |
| 4 duplicate sheet member names, 15 MiB each | 63.5 kB | ok (last wins; total under 64 MiB) | 0.12 s | 67 MB |
| DTD/ENTITY | 1.7 kB | `NATIVE_WORKBOOK` | 0.00 s | 22 MB |
| 249k `<row><c t="b"/></row>` (builder's worst) | 14.2 kB | ok 249003 | 4.54 s | 151 MB |

The 15 MiB inline cell (2.76 s) is the single-copy form of N6. It is bounded by the member, and the N6 character
budget would cover it too. The 249k case is acceptable as bounded. N7's row ceiling would tighten it about 25
times at no cost to legitimate files.

### Open point: the budget refusal's words

- **Judgment.** Telling an operator "not an Excel workbook this layout can read" for a file that is merely too
  large is not honest. They will look for a format problem that is not there.
- **Recommendation.** A dedicated code, for example `NATIVE_TOO_LARGE`, saying "This file holds more than one
  upload can take (at most 10,000 rows); split it and upload the parts". It would be shared by the element budget,
  the N6 character budget and the N7 row ceiling. It needs an SC-1/messages entry and the Architect's ruling.
- **Severity.** Low: legitimate files are far under every bound, so no real operator should see it. It does not
  block. If the Architect declines, keep `NATIVE_WORKBOOK` and record the reason.

### Differential (my own)

- **Method.** The round-2 reader (`a141bab51:xlsx.py`) against the r3 reader, `xlsx_sparse_rows`, on 2,000 random
  legitimate sheets (seed 7).
- **Contents.** Shared strings (plain and rich), inline strings (plain, rich runs, phonetic, two `<t>`), numbers
  (including `-0`, `1E+20`, `4.2e300`, 17 digits), booleans, `str` with a formula, formulas without a value, errors,
  `t="d"`, styled empty cells, cells and rows without `r`, gaps, and out-of-range shared indexes.
- **Result.** 0 mismatches.

### Checks run (at 84113ed14, worktree on `PYTHONPATH`)

- `heavy-slot.sh -- pytest contracts/tests backend/tests/test_3a6_source_profiles.py -q`: 160 passed in 27.16 s.
- `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 backend/tests/test_3a6_source_profiles_postgres.py -q`:
  4 passed in 5.45 s, routed `*_test`.
- The probes are in my scratchpad, not the worktree. Each ran under `ulimit -v`.

### Not verified

- The full suite and the 41 guards: I relied on the implementer's r3 run at c8a6d23c1.
- The 16 MiB shared-string form of N6 and an end-to-end HTTP upload. Late in the session the temp volume's quota
  filled (other sessions' files), so the N6 figures are projected from the measured linear series above.
- The r3 plants were not re-run.

### Residual risk

- The profile admission path reads the sample twice, through `reader.read` and then `split_file`. Every cost above
  doubles there.
- Concurrency: every figure is per request, and nothing limits parallel uploads per tenant.
