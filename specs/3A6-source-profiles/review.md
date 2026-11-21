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
