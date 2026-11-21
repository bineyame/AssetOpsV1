# 3B6 review packet: cold-room and captive-EV structures

Branch `task/3B6-cold-ev` (base main `22dc0bbf3`, after 4a). Spec rev 2, rulings D-3B6.1-24, reviewer guide rev 2.
`USER_REVIEW_REQUIRED: false`. No migration, no guard or `tools/` edit, no route, no served text. Mid-build count 0.

## Outcome

`COLD_CHAIN` (36 rows) and `EV_DEPOT_CAPTIVE` (42 rows) are rows on the shared records, read through
`StructureRead.site`. Captive-depot revenue is declared not applicable: declared, checked at start-up and queryable
through `applicability()`. No read carries it (D-3B6.14). Every portfolio reader names a Site of another structure
`STRUCTURE_OTHER_KEY`. The three mini-grid-only Site readers refuse `STRUCTURE_KEY_NOT_READ` before any read.
`evaluate.py`/`expressions.py` diff is empty. `check.py`/`read.py` name no cold or EV key.

## Files

New: `structure/rows_cold_chain.py`, `structure/rows_ev_depot.py`, `tests/test_3b6_cold_ev_structures.py` (62 tests,
no DB). Edited: `structure/{registry,check,pins,read,sources,money,__init__}.py`, `structure/targets/read.py`,
`structure/attribution/read.py`, `structure_snapshot/{build,read,model}.py`; the test lines below.

## Done questions (spec §8)

1. Yes. Tests 1 and 2: manifest parity (expressions, leaves, sources, words, absences, homes, order, counts,
   `not_applicable` against `chain_model`), units and composes from the test's own tables, `check_all()` passes.
2. Yes. Test 4: 13 sides to the cent, plus the hand literals. The Ruiru plan skip is a literal. Test 4b: both
   portfolios' SUM factors, NONE not composed. Calendar leaves are checked over 4 month lengths in test 5b.
3. Yes, at the data level. Test 5a: no `revenue` row or value. `applicability` gives NOT_APPLICABLE, NOT_IN_STRUCTURE
   or APPLIES and is total. EV `contribution` = −`cost_to_serve` on all 7 EV sides.
4. Yes. Test 5b: the state table (COLD 2/4/1/16, EV 1/2/3/17). Every NOT_CONNECTED or HELD leaf is NOT_AVAILABLE
   with the manifest kind, family and words. Money nodes are None, never 0. Test 5c: the 5 cited tokens exist and the
   HELD set equals the literal. Test 6: the production chain (Energy→Commercial→Litre→Product) touches no fake. A
   COLD `staff` patched PROVIDED still reads NOT_CONNECTED (`COMMERCIAL_KEYS`).
5. Yes. Test 8 covers `sites_excluded`, the portfolio per key and `NOPE`. `TargetRead.site`, `BridgeRead.site` and
   `SnapshotRead.site` raise KEY_NOT_READ while the raising fakes stay uncalled. The Target, Bridge and Snapshot
   portfolios name THIKA `OTHER_STRUCTURE`, and `site_inputs` is called for KOBO only.
6. Yes. Test 7: five pins, `PENDING_PINS == {}`, `parity()` returns `[UNEXPLAINED_FUEL]`, and the three new pins'
   category is PROTECT_ASSET.
7. Yes. No migration. The guards are unchanged and check-all passes (below).
8. Every plant fails its named test, with one guide expectation that cannot hold (P1, below).

## W6 sweep (spec §6.3) and changed literals

| File | Old → new |
|---|---|
| `test_3b1:92` | `{"MINI_GRID"}` → the three keys |
| `test_3b2` `DESIGN_PINS`/`DESIGN_PENDING` | 2 pins, 3 pending → 5 pins, `{}` |
| `test_3b2` manifest-row test | the node-equals-leaf rule added; `NO_MANIFEST_ROW = {COLD_EXCURSION}` |
| `test_3b2` `OWN_SITE_STRUCTURE` | the six cold and EV Sites added |
| `test_3b2` unpinned-mechanism test | drops `EV_INTERRUPTION` from `PINS` (same text) |
| `test_3b3:684,708`, `test_5a:675,677`, `test_5b:813`, `test_3b7a:234,285` | `STRUCTURE_NOT_DECLARED` → `STRUCTURE_OTHER_KEY` |
| `test_5a:544` | code → `STRUCTURE_KEY_NOT_READ` |

**Known deviations: four lines the §6.3 table did not list, all needed by §3/§4.3.**
(a) `test_3b2` `test_t2_which_planted_nodes_are_totals` and `test_t3_a_new_difference_is_reported` planted a
MINI_GRID-only mapping, which now refuses `STRUCTURE_PIN COLD_CHAIN/uncovered_nights`. They now keep the real
registries beside it (`{**REGISTRIES, "MINI_GRID": ...}`) and their expected texts are unchanged.
(b) `test_3b2` `test_t5_pending_and_unknown_read_none` keeps only `NOT_A_MECHANISM`, because the other three are pinned.
(c) `test_3b7a` `test_10_grep`: the import list of `structure_snapshot/read.py` gains `KEY_NOT_READ`.

Widened, no literal changed (D-3B6.21): `test_3b2:234` (L2 now refuses first, same `CODES` code; comment retitled);
`test_4b1` `_valued_cases` (cold and EV cases join; all pass).

## W6 greps (§4.4), at HEAD

- G1 (26 hits, 9 files):
  - Changed: `read.py` (map, portfolio, `sites_excluded`), `targets/read.py`, `structure_snapshot/{build,read}.py`,
    `attribution/read.py` (reorder), `money.py:167-169` (guard).
  - Safe: `read.py` `site_inputs` (per-Site key); `sources.py:207` (per-Site key); `money.py:179` (`stated`: no cold or
    EV STATED_STATE); `energy/source.py:69` (`_state` by key; no ENERGY_LEAVES ID in cold or EV);
    `attribution/read.py:44` (portfolio follows targets); `structure_snapshot/model.py:82` (snapshots are MINI_GRID
    only).
- G2: no hit outside `structure/` and `structure_snapshot/`.
- G3 `REGISTRIES["MINI_GRID"]` (`money.py:44`, `energy/source.py:30`, `litres/source.py:26`): mini-grid row lookups
  only, so safe.
- G3 `NOT_DECLARED`:
  - Changed: `read.py`, `targets/read.py`, `structure_snapshot/*`.
  - Safe: `read.py:76` (`site_count` fallback); `attribution/portfolio.py:21,103`.
  - Other constants that only contain the substring (`energy/*` band state, `litres/rules`, `attribution/bridge|rules`
    `PRICE_/RULE_NOT_DECLARED`): not the reason tuple.
- No change needed: `litres/source.py`, `attribution/{site,carry,rules,portfolio}.py`, `targets/{lines,rules}.py` and
  `structure_snapshot/{codec,untracked}.py`. Each is reached only under a mini-grid key, or looks the key up as stored.

## Plants (reviewer guide P1-P30; scratch copy of HEAD `13d1f98d0`, each applied, run, reverted)

Runner: the 3B6 file plus `test_3b1::test_t4_create_app_starts_with_the_real_registry` ("startup"). Baseline: 63 pass.

- **P1 deviation.** P1 (`* 1`) fails test 1 only. It keeps every value the same, so test 4 cannot fail on it. The
  guide's "and test 4" is wrong for this plant.
- Data plants that fail their named tests, sometimes with more:
  - P2: 1, 5a, startup, plus 2, 3, 4, 4b, 5b and 7.
  - P3: 1, 5a, plus 3 (test 3's "EV alone" case uses the real EV rows).
  - P4: 1, 2 and startup, plus more.
  - P5 and P6: 1, 2 and startup.
  - P7: 1.
  - P8: 5b.
  - P10: 6b and 5b, not 6c.
  - P13: startup and 2.
  - P14: 7.
  - P15: 2 and 5b.
  - P16: 2 only.
  - P17: 5b.
  - P27: 5c.
  - P28: 5b and 5c.
- Code plants:
  - P9 and P19: 5b.
  - P11, P12, P18, P29 and P30: 8.
  - P20 to P24: 3 only.
  - P26: 6c only.
- Guide note: D-3B6.16 says data plants cannot fail test 3. P2 to P6 do fail it, because spec test 3's "EV alone" and
  L2 cases need the real EV registry. Nothing the guide requires is missed.

## Checks (HEAD `13d1f98d0` unless noted)

- Focused (no DB): `pytest` on the 3B6 file, 3b1, 3b2, 3b3, 4b1, 4d, 5a, 5b, 3b7a seam and snapshot, and 4a:
  **679 passed, 1 skipped, 24.6 s**.
- Postgres: `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1` on `test_3b3_structure_read_postgres`,
  `test_4a_energy_to_cash_postgres` and `test_3b7a_structure_snapshot_postgres` (default `assetops_test`): **16 passed, 61.8 s** (15 min wall, slot wait).
- `pwsh -NoProfile -File tools/check-all.ps1 -SlotWaitMinutes 90` (includes check-architecture and check-agent-workflow): **all 40 guards passed**, 79 s of work (1,088 s wall, 1,009 s slot wait). An earlier run timed out on the slot (20 min) and its log is not used. `check-decision-index.py` passes when run alone.

## Stored snapshots

`rules_digest` covers every imported module, so after merge every stored snapshot reads "rebuild needed" until it is
rebuilt (not a finding). 3B6 touches no stored row.

## Residual risks

- `R-EV-PUBLIC` (D-3B6.7): every `EV_CHARGING` Site reads as a captive depot.
- `R-DST-MINUTES` (D-3B6.11): `minutes_per_day` is a fixed 1440.
- `R-CROSS-KEY` (D-3B6.8): there is no cross-structure total, and the portfolio ratio `cost_per_departure_met` is
  not built.
- `R-SHARED-ID` (D-3B6.18): closed by `COMMERCIAL_KEYS` and test 6. It stays listed until 9d.

## Review focus

The four unlisted sweep lines (a)-(c), the P1 expectation, and `TargetRead.site` guard placement (before `_month`).
