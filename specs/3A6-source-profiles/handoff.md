# 3A6 handoff after commit 1 (PARTIAL: stopped at commit 2, waiting on 0066)

Branch `task/3A6-source-profiles`, worktree `/opt/assetecon/AssetOpsV1-3a6`, commit 1 `7bcacba98` (off `main` d93815f0d).
Stopped because `backend/migrations/versions/0066_structure_snapshot.py` (3B7a) is not on `main` yet (D-3A6.12). Next
step: merge `main` into the branch once 3B7a has merged, then build commit 2. Mid-build questions: 0.

## Done (commit 1, spec §8 row 1)

- `contracts/assetops_contracts/native/layouts_v1.py`: `FileRules`, `ValueRules`, `Column.types/scales`, the `Layout`
  fields, `CODED_PATHS`, `DATE_FORMATS`/`TIME_FORMATS`/`MONTH_FORMATS`/`TYPES`, `transform` + `TransformFailed`
  (§2.4), `split_file`, `read_rows` (header compared first, R5), the invisible rule by category, XLSX cell marks, join,
  row digest, `check_layout`'s coded rule, `render_layout`'s `NATIVE_RENDER <id> profile` (`is_profile_shaped`).
- `native/xlsx.py` (§2.3), `native/profiles_v1.py` (`compile_profile`, `ProfileInvalid`, `reader_id_for`,
  `run_probes`), `native/__init__.py` re-exports.
- Fixtures `backend/tests/fixtures/3a6/` (hand-written; digests recomputed independently with plain sha256, all match
  the spec), `.gitattributes` `-text` line. SHA-256: kobo csv `de793415…bead`, budget xlsx `df247815…0e78`.
- `contracts/tests/test_3a6_profiles.py` N1 to N9 + X0: 111 passed in `contracts/tests` (neutral runner: simulator
  507, contracts 111). Regression, no DB: 3A3 source contract, single writer, loader, 3A2 service: 166 passed;
  simulator `test_3a3_exports.py` + `test_observation_transform.py`: 17 passed (E7 pins hold).
- Guards: `check-architecture.ps1` passed (needs `ASSETOPS_GUARD_PYTHON=/opt/assetecon/AssetOpsV1/.venv/bin/python`
  in a worktree); `check-agent-workflow.ps1` passed. Fast check-all not yet run (end of build).
- Plants (applied, run, `git checkout` reverted; tree clean): V1, V2, V3, V4, V5, V6, V7, V8, V9, V21, V23b, V25,
  V30, V32 each fail their named test. V25 fails as an import error (the budget layout's `factor_id` map becomes a
  map on a non-coded path); V9 fails N8 (N7's "category unmapped" is refused earlier, by `compile_profile`).
  Script: scratchpad `3a6/plants1.py`.

## Choices the spec left open (for the packet; conservative, local)

- `run_probes` `where`: P1 `file`, P2 `row.<n>`, P3 `U+XXXX` (the probe character), P4 to P6 the header.
- `compile_profile` treats every §2.1 key as required except `record_id_join`; map one-to-one is checked in
  compile (`.map`); a map on a non-coded path and an unmapped coded path both name `columns.i.paths.j.map`.
- A join part containing `:` refuses the row even when another part is absent.
- N5's dropped-`Phone` U+200B case declares the kobo copy UTF-8 (cp1252 cannot encode U+200B). Known deviation.
- Month grammars accept a one- or two-digit month for `YYYY-MM` and `MM/YYYY` (as DD/MM in dates); `HH`, `MM`, `SS`
  in times are two digits.

## Next (commit 2, then 3)

Commit 2: migration `0067_source_profile` (down_revision `0066_structure_snapshot`, Q1 asserts the chain link),
`ProfileRow`/`UploadSourceSwitched` in `commercial/model.py`, store + Postgres adapter reads and `add_source_profile`,
`HeldUpload.source_system/site_codes`, `write_intake` acceptance re-check under the lock, `commercial/profiles.py`
(steps 1 to 7 incl. 4a to 4c; 4c can reuse `transform` with swapped `ValueRules`), `readers.py` media types,
`uploads.py` (instance `reader`, switch rule, `get`), route call, composition, `tenant_by_slug`, `COMMAND_ROLES`,
words, persistence guard, A1 to A10, U1 to U6, Q1 to Q3; plants V11 to V17, V22 to V24, V28, V29.
Commit 3: command, loader, S1 (§2.9), suite (§2.10), L5 to L9, K1 to K4, plants V10, V18 to V20, V26, V27, V31;
check-all; `packet.md`; spec `Status: in_review`; `.ai/state` entry.

## Risks

- `split_file` now reads the whole CSV before comparing the header, so a file with a bad header *and* a CSV syntax
  error later reports `NATIVE_ROW` rather than `NATIVE_HEADER` (3A3 tests still pass).
- No live DBs or processes left by this run.
