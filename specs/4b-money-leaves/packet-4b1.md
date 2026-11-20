# 4b1 packet: the stated-node seam

Implementer (Claude Opus 5.5, fresh), 2026-11-20. Branch `task/4b1-money-leaves` (the dispatch's name; spec §0 says
`task/4b1-stated-nodes`), worktree `/opt/assetecon/AssetOpsV1-4b1`, off `main` `880ba4dbf`. Not merged.
Spec `spec.md` rev 2 §2 and §2.7; rulings D-4B.1, .2, .10, .11, .16, .17. Non-screen: layout evidence not applicable.

## Commits

- `70d40757e` 4b1: the seam, tests S1-S10, the P1 version edits, mid-build Q1.
- (this commit) packet, spec status, built-state entry.

## Module paths (PYTHONPATH = worktree backend, backend/tests, contracts, simulator, gateway, field, host, tools)

```
/opt/assetecon/AssetOpsV1-4b1/backend/assetops_backend/__init__.py /opt/assetecon/AssetOpsV1-4b1/contracts/assetops_contracts/__init__.py
```
`frontend/node_modules` is a symlink to the main checkout's (not used: no frontend change).

## What changed (done Q8 list, 4b1 part)

- `structure/registry.py`: `FactorRow.stated_by` (after `composes`); MINI_GRID `Registry(..., 3, ...)` in place.
- `structure/rows_mini_grid.py`: `_node(stated_by=None)`; `revenue` and `fuel_cost` with the §2.1 literals; docstring v3.
- `structure/check.py`: `STRUCTURE_STATED` right after `STRUCTURE_COMPOSES` (leaf, family, `composes != "SUM"`,
  `not unit.is_money`). No test pinned `CODES` literally; S8 asserts the position.
- `structure/evaluate.py`: `ORIGIN_ORDER`, `weakest_origin`, `LeafValue.origins`, the four `FactorValue` fields,
  `STRUCTURE_ORIGIN` (unknown, out of order, repeated), `evaluate(..., stated=)` with §2.3's four rows, origins and
  `detail_missing` folds (neutral identity drops the other operand), `_compose_factor` origins/`detail_missing`.
- `structure/sources.py`: `StatedSource`. `structure/read.py`: `StructureRead(sources, stated=None)`.
- `commercial/composition.py`: `CommercialReads`, `build_commercial_reads` (one store; `dispose` is the store's).
  `commercial/` imports nothing from `structure/` (check-all dependency direction passed).
- Tests: new `backend/tests/test_4b1_stated_nodes.py`; P1 edits `test_3b1_structure_registry.py:88`,
  `test_3b3_structure_evaluate.py:366` and `:652`, `test_3b3_structure_read_postgres.py:82`. Sweep after:
  `grep -rn '"MINI_GRID", 2\|version == 2' backend/tests` leaves only `test_s3_dispatch_assessment_postgres.py:455`
  (plus the unrelated `scenario_version`/`template_version`/`foundation_version` hits the pattern also matches).

## Done criteria (4b1's share)

1. Stated node takes its record, keeps `computed` and `detail_missing`; the read without a stated source equals
   3B3's: **yes**, S1, S2, S9. Probe: `evaluate` with `stated` empty on main and on the branch, the 10 old fields of
   all 47 factors x 3 Sites x 2 variants (pack; `delivered_kwh` and `om` absent), 282 values: identical repr hash.
4. A total never stronger than its weakest part, in origin: **yes**, S6 (union in `ORIGIN_ORDER`, `weakest_origin`).
8. Nothing outside the list: **yes** for 4b1 (the diff is the files above, the spec folder and `.ai/state/`).
- Leaves are built with 3B3 T1's `pack_leaves` (imported from `test_3b3_structure_evaluate`, with its `_absent`,
  `_plant`, `_raises`, `site_structure`, `KOBO`, `MG`; that file has only the P1 edits).
- Questions 2, 3, 5, 6, 7 are 4b2's (money leaves from records).

## Tests (real output)

- No DB: `env -u DATABASE_URL -u ASSETOPS_TEST_DATABASE_URL tools/heavy-slot.sh -- python -m pytest
  test_4b1_stated_nodes.py test_3b3_structure_evaluate.py test_3b1_structure_registry.py -q`: **181 passed** in 2.96 s
  (30 are 4b1's). Before the code: collection error on `ORIGIN_ORDER` (tests first); before the P1 edits: exactly the
  3 version assertions failed.
- PG regression: `tools/heavy-slot.sh --db -- python -m pytest test_3b3_structure_read_postgres.py -q -rs`
  (base `assetops_test` at 127.0.0.1:55432, routed by the harness to a run-owned `*_test` clone): **5 passed**, 7 s.
- Selected subset with DB (structure + every commercial test `select-tests` picked: 3a2 api/postgres/service, 3a4
  both, 3b1, 3b3 both, 4b1): **336 passed**, 0 skipped, 26 s.
- `python tools/select-tests.py --base main`: selected 273 of 531 backend files (the container fast tier).
  **Not run as a whole**: its runner is `run-backend-suite-in-container.ps1` (Docker, outside this dispatch) and the
  full-size runs are the coordinator's to schedule. The 9 files above are its structure and commercial members.
- Fast check-all (`pwsh -NoProfile -File tools/check-all.ps1`, at `70d40757e`): **All 40 guards passed** (0 advisory,
  0 warned), 83 s; includes the architecture seams (module roots, dependency direction, simulator gate).

## Plants (each applied alone, the 4b1 file run, reverted with `git checkout --`; tree clean after)

| # | Plant | Failed |
|---|---|---|
| V1 | ignore `stated` | S1, S2, S4, S7, S9 (asks once), S10 |
| V2 | accept a stated node without `stated_by` | S5 `contribution` |
| V3 | node left out of `missing_leaves` (stated and expression absent) | S4, S10 |
| V4 | neutral identity inherits the other operand's origins and `detail_missing` | S6 neutral identity |
| V5a | alphabetical origin union | S6 both reordered pairs |
| V5b | alphabetical input check | S5 `("demo-simulated", "source-emulated")` |
| V5c | `weakest_origin` = alphabetical max | S6 both reordered pairs (`weakest_origin` assertions) |
| V6 | MINI_GRID left at v2 | S8, S9 |
| V16 | expression served for a `NOT_CALCULATED_YET` stated record | S10 |
| V18 | `stated_by` allowed on any MONEY exponent | none at first (Q1); after the fix round see the table below |

Script and log: `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/36691a1d-3a44-455a-947e-9acaa1af47c0/scratchpad/probe4b1/`.

## Fix round (mid-build Q1 answer, review r1; D-4B.18)

Built: F1 (S8 `s8_money_sq`, `s8_money_kwh` added stated SUM rows plus controls without `stated_by`); F2 (a TARGET
stated value `test_s1_stated_carried_as_target...`, S4's provenance, row 3's provenance); D-4B.18 (`ORIGIN_UNKNOWN`
last in `ORIGIN_ORDER`; `_check_leaf` refuses valued, non-NEUTRAL, non-CALENDAR-row leaves and stated values with
`origins == ()` as `STRUCTURE_ORIGIN`; `ProductLeafSource` snapshot and declared price return `("unknown",)`;
`pack_leaves(origins=("source-emulated",))`; 3B3 test edits: `pack_leaves`, `:459`'s leaf, `test_t6_prices` and
`test_t6_unserved_critical...` expect `("unknown",)`; S6 amended, S11 added). Review copied to `review-4b1.md`.

Plants (each alone, 4b1 + 3B3 evaluate + 3B1 files, reverted; tree clean after):

| # | Plant | Failed |
|---|---|---|
| V18 | any MONEY exponent | `test_s8_a_stated_node_must_be_exactly_money` both rows |
| V18b | MONEY exponent 1, any unit | `...exactly_money[s8_money_kwh]` only |
| F2a | row 1 `assumed_leaves` always `()` | TARGET test |
| F2b | row 1 drops `missing` | TARGET test |
| F2c | rows 3/4 provenance from the stated value | `test_s4_both_absent` (row 4 and row 3 asserts) |
| V21 | `()` accepted | S11(a) all three |
| V22 | `unknown` not last | S6 order, S11(b) |
| V23 | exemption keyed on evidence (`DERIVED`) | S11(a) `outstanding` (S11(c) holds under it; not separately planted) |
| V24a / V24b | snapshot / price leaf returns `()` | `test_t6_unserved...`, `test_t6_prices` and read tests |

Runs at this revision (PYTHONPATH = this worktree's backend, contracts, simulator; modules verified to import from it):
4b1 + 3B3 evaluate + 3B1, no DB: 191 passed (3 s); `test_3b3_structure_read_postgres.py` through
`heavy-slot.sh --db` + `run-host-tests.ps1`: 5 passed (a bare pytest under the slot skipped all 5, since it sets no
URL); fast check-all: all 40 guards passed (81 s).

## Mid-build count: 1 (answered)

Q1 (`mid-build-questions.md`): S8's plant "a copy of `revenue` with `MONEY / KWH`" cannot reach the unit rule.
`check` is code-major; `MONEY / KWH` with `SUM` is refused by `STRUCTURE_COMPOSES` first, and with `NONE` it is
refused by `STRUCTURE_STATED` for `composes`, so V18 passes. That S8 assertion is stopped (not written); the rule is
built and the `diesel_l` plant (unit L) shows the unit condition refusing. Proposed: a `MONEY^2` SUM node plant.

## Known deviations and readings

- **P2 (T6 table and body edits) not done.** The dispatch lists "the P1 and P2 test edits"; the rulings (P2) and spec
  §3.2 assign them to 4b2, with the `SOURCE_STATE` change they test. In 4b1 the states are unchanged, so T6 stays
  green as it is; editing it now would fail it.
- **Dispatch "S5-S10"**: built S1 to S10 as spec §2.7 and §8 assign to 4b1.
- **Row 4 of §2.3, unlisted fields**: `assumed_leaves` and `currency` are the expression's (the row is the
  expression's `FactorValue` with the listed fields replaced), as 3B3 keeps them on any node without a value.
- **Row 1 `computed`** is the expression's folded value after 3B3's currency check (None on mixed currencies).
- Extra assertions beyond the spec (none relaxes one): a repeated origin and a leaf's origin refused
  (`STRUCTURE_ORIGIN`); `check(MG)` passes; a no-DB test of `build_commercial_reads` (one store, disposed once).

## Not verified

- The full select-tests set (273 files) and any full suite: not run (see above).
- `5a`'s use of the new fields: not exercised here.

## Review focus

§2.3's table in `evaluate.py` `_stated_node`; origin ordering in `_check_leaf` and `_origin_union`; Q1.
USER_REVIEW_REQUIRED: not stated in the spec; non-screen. Q1 is for the Architect, not the owner.
