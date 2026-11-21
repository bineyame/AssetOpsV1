# 3A6 reviewer guide (rev 3, after review round 5; rev 2 after handshake round 1)

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md` and this guide; put questions in
`handshake.md`), then at the review. Depth: discovery (W5): a new shared contract (the profile format and the engine's
growth), a new table, what the intake admits, and the RC4 boundary for an operator's sample.

## First checks

1. **Scope.** The diff holds only spec §7 question 11's list.
2. **Migration.** One new head, `0067_source_profile`, revising `0066_structure_snapshot` (D-3A6.12; its test asserts
   the chain link, not "is head");
   downgrade refused with a row; the append-only trigger present.
3. **Module paths** in the packet resolve to the worktree for all three packages.
4. **3A3 unchanged in behaviour.** Its contracts goldens, E7 SHA-256 pins, and the 3A2 and 3A3 service, loader and
   Postgres files pass; the only edits to them are the ones §6 names.
5. **No real data.** Every fixture is the spec's literal text; nothing under `fixtures/3a6/` came from an operator.

## Done means

Spec §7's eleven questions answered yes with real output: `contracts/tests/test_3a6_profiles.py`, the 3A6 service,
command and Postgres files (Postgres through `tools/heavy-slot.sh --db`), the extended 3A3 suite (C1 to C10 over five
cases, S1, the loader), the regression set, check-all, and each plant below failing its named test.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V1 | Default `FileRules.header_row` to 2 | N1 (illustrative goldens) |
| V2 | Trim cells before transforms | N4 (` 500,00` must fail) |
| V3 | Number grammar accepts `12.5` with decimal `,` and thousands `.` | N4 |
| V4 | Datetime without offset placed in UTC instead of the profile zone | N2, N4 |
| V5 | Drop the category rule (keep only 3A3's code-point set) | N5, A6 (b) |
| V6 | Check dropped columns for invisible characters | N5 (dropped `Phone`) |
| V7 | XLSX numbers kept at full float precision | N3, U2 |
| V8 | Accept a second sheet | N3 |
| V9 | Allow an unmapped coded path in `check_layout` | N7, N8 |
| V10 | Derive `coded_headers` from the layout's maps instead of `CODED_PATHS_EXPECTED` | `test_coded_check_fails_on_an_unchecked_layout` |
| V11 | Skip probe P6 | A6 (e) |
| V12 | Store the sample text in `profile_json` or any column | A8 |
| V13 | Let an older version read uploads | A2 |
| V14 | Skip the status check | A3 |
| V15 | Key the intake's switch rule on reader ID | U3 (v2 of one profile must still upload; a template file must be refused) |
| V16 | Drop the Site narrowing | U3 (KISIWA-001 file) |
| V17 | Count a declined upload as held | U3 |
| V18 | Remove the `S1-DYN` clause | S1 plants p01 to p06 |
| V19 | Allow `eval` in `commercial/` | S1 plant p22 |
| V20 | Let the loader accept a profile file not admitted | L8 |
| V21 | Write `source_record_id` from a join with an empty part as `"KOBO-001::Revenue"` | N6 |
| V22 | Skip step 4b (map coverage) | A9 (a) |
| V23 | Skip step 4a (empty column) | A9 (b) |
| V23b | Drop the serial window (61 to 73050) | N4 (`"60"`, `"73051"`, `"2958466"`, `202610` under `Mon-YYYY`) |
| V24 | Drop the acceptance re-check under the lock | U3 (race), Q3 |
| V25 | Remove `body.factor_id` from `CODED_PATHS` | N9 |
| V26 | Remove the `S1-SYSMOD` clause | S1 plants p09, p11 |
| V27 | Remove the `S1-RUNPY` clause | S1 plants p12, p13 |
| V28 | Compare the header in `split_file` only | A1, A6 (the true engine fails P1) |
| V29 | Skip step 4c (ambiguity) | A10 |
| V30 | Judge `XlsxBad` cells in dropped columns | N3 (`Note` variant) |
| V31 | Restrict `S1-DYN-COMMERCIAL` to non-allowlisted modules | S1 plants p07, p08 |
| V32 | Read the `YYYYMM` `XlsxNumber` as a serial | N4 (`2026-10`) |

| V33 | Read in the server process in `_check` (call `reader.read` directly) | E7 |
| V34 | Drop `RLIMIT_AS` in `_child` | E1 |
| V35 | Drop the parent's `poll` timeout (wait without limit) | E3 (run with a 10 s pytest timeout) |
| V36 | Drop `maxlength` and the child's result check | E4 |
| V37 | Raise `RuntimeError` for a breach instead of `NATIVE_TOO_LARGE` | E1, E3, E4 |
| V38 | Skip the `=` run scan in `_parse` | B1 (one element, 1.45 M names) |
| V39 | Reset the N9 counter per physical line instead of per row | B2 (quoted lines) |
| V40 | Remove `_directory_check` | B3 |

Rule for plants (rev 2): every gate in `rulings.md` "Handshake answers (round 1)" has a row here; a plant that no
listed test fails is a High finding against the spec, reported, not waived.

## Probes

- **Independence (W2).** The expected JSON, N4's literals and §4.1's and §4.2's digests are written by hand; none comes from
  `read_rows`, `compile_profile` or a helper they share. Recompute one digest yourself.
- **RC4.** Admission keeps three hashes and a count, never a cell; nothing in logs or answers carries a sample value;
  the Postgres file names only `*_test` databases.
- **The class fixes.** For D-3A6.4 to D-3A6.7, check the recorded sweep in `rulings.md` against the code, and that each
  residual queued to 3A6 by 3A3's review is either closed or stated in the packet.
- **Words.** Render a profile refusal as the analyst reads it ("Row 4 of the sample is refused: Litres: this value is
  not written the way this layout reads it (for example, a date in another order).") and an upload refusal as the
  person reads it.
- **No code per layout.** Admit a fresh profile of your own (any small CSV in a scratch directory) with the command on
  a scratch `*_test` database and upload through it: no file in the repository changes.

## Round 6: what the review checks (stop rule, D-3A6.27)

Depth: verification of fix round r5. The checks below are the only ones that can return REVISE:

1. **Exclusive.** E7 passes. Your own grep of `backend/assetops_backend/` finds no parse of upload bytes outside
   `commercial/envelope.py` and the reader classes. Every caller (the intake, admission, and through them the loader
   and the command) goes through `ParseEnvelope.read`.
2. **Bounded.** E1 to E6 pass. Run one breach of each kind yourself through the HTTP route: memory, CPU, wall, result
   size, and a child killed by hand with `kill -9`. Each answers 422 `NATIVE_TOO_LARGE` within the wall limit plus
   about 1 s, with no 500 and no hang. The server's RSS returns to its baseline, and the next upload reads.
3. **Faithful.** E8 passes, and the packet's 600-case differential has 0 mismatches. Rerun 100 of its cases yourself.
4. **Pinned and logged.** E0 and E9 pass. `DEFAULT_LIMITS` is the only production construction, with no setting or
   environment variable that changes it.
5. **Plants.** V33 to V37 each fail their named test.
6. **Words.** A breach renders "this file is too large or too complex to read in one upload; split it and upload
   the parts." on the upload route and in admission's `ADMIT_SAMPLE_FILE`.

Checked, not blocking: B1 to B3 and V38 to V40 (D-3A6.24), and the r4 bounds table. A defect in these is Low unless
it refuses a legitimate file, which is Medium.

New routes: do not hunt further XML, CSV or zip shapes. If you meet one anyway, record it as a Low residual when it
is refused with a coded reason inside the envelope's limits. It is a finding at its own severity only if it escapes
the envelope: parent-side work that grows with the input beyond D-3A6.23's parent figures (8 MiB upload, 32 MiB
result, `parse_batch` over the returned records), or a breach that harms the server process.
