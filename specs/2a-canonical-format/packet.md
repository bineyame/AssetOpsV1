# 2a review packet: canonical format v1 and the leaf factor IDs

Implementer (Claude), 2026-11-20. Branch `task/2a-canonical-format`, base main `184dc509e`, worktree
`/opt/assetecon/AssetOpsV1-2a`. Spec rev 2, rulings D-2A.1 to D-2A.10. Discovery review (W5). No database, no server.

## Commits

1. `071096546` tests and fixture first (W2). Run at that commit: `ModuleNotFoundError: No module named
   'assetops_contracts.canonical'`, 2 collection errors.
2. `ce7a7221f` the package `contracts/assetops_contracts/canonical/` (`__init__`, `units`, `factors`, `records_v1`,
   `sources_v1`).
3. The branch head (`git log -1`): packet and finish bookkeeping (P10), amended with the guard results.

## Done (spec §10)

| # | Question | Answer and evidence |
|---|---|---|
| 1 | 17 source types map to v1 kinds with fields, units, clocks | Yes. `KIND_SPECS` holds §6.4 as data (one generic parser; no per-kind branch). T5: all 17 batches parse with no refusal, 14 kinds and 17 source types occur (23 records). T10: every kind emitted, the 17 IDs in order |
| 2 | Every leaf has one ID and unit equal to the manifest | Yes. T1, T2 pass (see leaf-ID match) |
| 3 | Exact decimals with currency; floats, naive instants, unknown fields refused with code and path | Yes. T6: 102 planted record failures, 9 batch failures, 6 `loads_canonical` cases, 8 accepted edges, each asserting full `str(refused)`. T7: 500 seeded mutations, only `CanonicalRefused` |
| 4 | Byte-stable, round-trips | Yes. T5 (below) |
| 5 | Stdlib only; check-all | T9 passes (no module outside stdlib and `assetops_contracts`). check-all: see Tests |
| 6 | Nothing outside §0's list | `git diff --stat main...HEAD`: `contracts/assetops_contracts/canonical/*` (5), `backend/tests/test_2a_canonical_*.py` (2), the fixture, this packet, `.ai/state/data.md`, `.ai/state/index-2.md`, `.ai/state/INDEX.md` (data.md row), `specs/INDEX.md` (2a row) |
| 7 | Tests in `backend/tests` | Yes (D-2A.10) |

## Tests

- Focused: `PYTHONPATH=<worktree>/backend:…/backend/tests:…/contracts:… .venv/bin/python -m pytest
  backend/tests/test_2a_canonical_v1.py backend/tests/test_2a_canonical_manifest_parity.py -q`: **162 passed** (0.9 to 2.3 s).
  `assetops_contracts.__file__` resolved to the worktree's `contracts/`.
- `pytest contracts/tests -q`: 6 passed.
- `python3 tools/select-tests.py --base main`: `mode: full (517 of 517 backend test files)`, `full because:
  backend/tests/fixtures/canonical_v1_examples.json`. Full suite **not run**, as spec §9 and P2 direct: no backend
  module reads the fixture, and the merge's full fast tier runs these files.
- `tools/heavy-slot.sh -- pwsh -NoProfile -File tools/check-all.ps1` (fast, at `ce7a7221f` plus the uncommitted bookkeeping): "All 37 guards passed (blocking; 0 advisory, 0 warned)", 48.8 s run after about 7 min waiting for a slot; estate-guard and pool self-tests skipped as unchanged. After the bookkeeping commit: `check-agent-workflow.ps1` "Agent workflow check passed."; `check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` set to the shared venv) "Architecture check passed."
- Guards shown to fail on a real violation, then reverted (`git checkout --`): writer `str(d)` in place of
  `format(d, "f")` → 2 T5 edge failures (`0.0000001`, `0.000000000001`); a renamed leaf ID → T1, T2 fail; `window_h`
  unit `HOUR` → T4 fails; `fullmatch` replaced by `match …$` → the `"diesel\n"` case fails.
- Extra probe (reviewer P6): T7's mutator on seeds 1, 7, 99, 12345 at 3,000 records each: nothing but
  `CanonicalRefused` escaped; every parsed record round-tripped to the same bytes.

## Round-trip byte proofs (T5)

- Every fixture record: `to_canonical_json(r)` re-parses (through `loads_canonical`) to an equal record and the same
  bytes; every batch likewise, with equal `batch_digest`.
- Edge list inside an ADJUSTMENT amount, bytes identical after re-parse: `"1.50"`, `"0.0000001"`,
  `"0.000000000001"`, `"1000000000000"`, `"-108.00"` (written e.g. `"amount":{"currency":"USD","value":"1.50"}`).
  `"0.0000000000001"` and `"10000000000000"`: `CANONICAL_NUMBER record.amount.value`.
- `Z` becomes `+00:00`; `"1.50"` stays `1.50` (asserted).
- `record_digest` of the first fixture record, in-process and under `PYTHONHASHSEED` 1 and 2:
  `89f7544f41c7f8c823a4a9747988aa0ae4dd9f7ff99857b326e9f60d2806569d`.

## Leaf-ID match (T1, T2)

`leaves_of`: MINI_GRID 31, COLD_CHAIN 23, EV_DEPOT_CAPTIVE 23; equal as sets to the manifest's `factor_map` keys;
73 IDs, 4 shared (`staff`, `outstanding`, `liability`, `period_days`), 9 money leaves. T3 passes on every
COMMERCIAL_RECORD, OPERATIONAL_RECORD and DOCUMENT row of `empty_states.leaf_sources`.

## Mid-build questions

Count: **0**.

## Readings made where the spec was terse (not open choices; flag if wrong)

- A quantity unit outside the five (`"MWh"`) is `CANONICAL_UNIT`, by analogy with §6.8's band-unit row.
- Paths of element faults point at the element: duplicate refs `record.body.receipts[1]`, overlap
  `record.body.bands[<input index of the later band>].from`.
- When a controlling body value (`line_type`, `read_type`, `category`) is absent or invalid, the quantity step checks
  only the quantity's own shape; the body step then refuses the controlling value.
- `FORMAT_VERSION` is defined in `records_v1.py` and re-exported by `__init__.py`.
- The batch key-set check runs before `format_version`; the record order is §6.6's.

## Not verified

- The spec file carries no `Status:` line; the status `in_review` is recorded in the `specs/INDEX.md` row (spec §0
  keeps `spec.md` outside the edit list).
- Full backend suite not run (above). No layout evidence: non-screen.

User review: the spec sets no `USER_REVIEW_REQUIRED`. The unit defines record semantics (a RULES §5 trigger), but its structure page P2 is owner-approved and nothing is on screen; no walkthrough needed, merge on review ACCEPT unless the coordinator rules otherwise.
