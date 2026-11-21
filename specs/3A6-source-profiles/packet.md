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
  ON1 world fails. Done 11 allows only the `reader` signature. `HeldMemoryStore` now only subclasses it.
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

- A change to `personal` after accepted data is refused (D-3A6.18); the migration is queued unit 3A6b. Review r1 residuals: D-3A6.21.
- S1 still misses (D-3A6.14): unimported services handed in, `__getattribute__`, `vars(obj)[name]`, tools named
  `test_*.py`.
- Commit 1's risk stands: a CSV with a bad header and a later syntax error reports `NATIVE_ROW`.
- 3A7 edits the same store, adapter, model, composition, words, permissions and guard. P9: 3B7a's code digest changes,
  so snapshots must be rebuilt after 3A7.

## Review focus

`profiles.py` step order and `_coverage`; the `_SWITCHED` SQL and its memory mirror; `uploads._refuse_switch` and
`_stored_reader`; loader steps 5c/mixed/5b; S1 `_aliases`/`_qual`; `source_contracts.coded_headers`.
