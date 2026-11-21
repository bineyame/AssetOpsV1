# 3B6 review

## Round 1: discovery review (W5), 2026-11-21

Reviewer: fresh Claude reviewer (not the author). Branch `task/3B6-cold-ev` at `b9bd03757`, diff `main...b9bd03757`
(merge base `22dc0bbf3`, 4a merged). Judged against spec rev 2, rulings D-3B6.1 to D-3B6.24 and reviewer guide rev 2.

**Summary.**
- **Verdict: ACCEPT.** No High or Medium finding. Three Low findings (L1 to L3). None blocks. Fix them on the branch if it is cheap.
- Honesty holds. Each of the 5 HELD citations is a real stored record on `main`. The 33 other record-fed leaves are
  NOT_CONNECTED. No missing value becomes 0. `applicability()` is claimed only as declared, checked and queryable.
- `COMMERCIAL_KEYS` works. My own plant set `staff` and then `outstanding` PROVIDED: both read NOT_CONNECTED. With the guard removed, both reach the
  commercial store.
- Ordering, portfolio exclusion and the changed existing tests are correct. None is weakened.
- The plant deviations are the guide's errors, not the build's (P1; P2 to P6 also failing test 3).
- It merges cleanly onto current `main` (`04da33fac`). It does not collide with 3B4's pending `check.py` commit beyond a small rebase of
  `check_all` (residual risk RR1).

### What I checked, against the brief

1. **HELD records are real (D-3B6.13).** I opened each citation on `main` (`04da33fac`):
   - `compressor_state` is a `Role` in `COLD_ROLES_1`, at `sites/binding_roles.py:162`. `analytics/cold.py:54` reads it.
   - `ev_connector_fault` and `ev_connector_state` are `Role`s in `EV_ROLES_1`, at `binding_roles.py:204` and `:208`.
   - `ev-site-import-limit` is a `PropertyDefinition` at `sites/models.py:224`. `ev_foundation.py:431` checks it.
   - `EV_CHARGER` is in `COMPONENT_TYPES` (`sites/models.py:49`). `ev_foundation.py:518` iterates over it.

   None of them is a work case. `uncovered_nights`, `backup_unproven_days` and `charger_out_days` are NOT_CONNECTED, with the reason as a comment.
   Test 5c checks that the HELD set equals its literal, so a leaf cannot become HELD without a citation. It checks a
   token string in a file, not the record (L1).
2. **Unknown is never 0.** Test 5b checks every non-calendar, non-option leaf as `NOT_AVAILABLE` with the manifest's kind,
   family and words, over 4 month lengths. Every money node is `None` with `missing_leaves`. The zero set is limited to the
   neutral-0 option leaves.
3. **`applicability()`.** It is pure and total. It has no caller outside tests (grep). The module docstring, the `Registry` field comment
   and the packet claim no read. The cross-registry pass covers only the checked set (`check.py` `check_all`).
4. **Shared IDs (R-SHARED-ID).** COLD shares `staff` and `outstanding` with `COMMERCIAL_LEAVES`. It shares those two and `revenue` with `money._ROWS`.
   It shares nothing with `ENERGY_LEAVES`, `LITRE_LEAVES` or `PRICE_KEYS`. EV shares none of these. I checked this by script.
   - `CommercialLeafSource.stated` is keyed by `STATED_STATE[key]`, which has no cold or EV entry, so `revenue` cannot route.
   - `LitreLeafSource` routes by ID alone, but no cold or EV ID is a litre ID.
   - My plant ran on a scratch copy of HEAD, with `SOURCE_STATE` patched in `sources` and `money`. `staff` gave `None/NOT_AVAILABLE/NOT_CONNECTED` and
     so did `outstanding`. With `and key in COMMERCIAL_KEYS` removed, both called `commercial months.site_month`.
5. **Ordering.**
   - `TargetRead.site` raises `KEY_NOT_READ` before `_month` and before the lines read (`targets/read.py:109`).
   - `SnapshotRead.site` raises before `_check_month` and before the store (`structure_snapshot/read.py:60`).
   - `BridgeRead.site` binds the targets first (`attribution/read.py:35`).
   - Test 8 proves all three with raising fakes, for both a cold and an EV Site.
   - The reorder keeps the same calls with a pinned `known_at`, so no result changes. `test_5b_attribution.py` passes.
6. **Portfolio.**
   - `StructureRead.portfolio` composes one key and refuses an unknown key.
   - `TargetRead.portfolio` and `SnapshotBuilder.build` use the single `sites_excluded` rule, and `BridgeRead.portfolio` follows the target composition.
   - There is no cross-vertical total.
   - `site_count` and `attribution/portfolio.py` keep `NOT_DECLARED` only as a fallback for a code missing from `sites_excluded`, which cannot happen for an asked Site.
   - Nothing outside `structure/` and `structure_snapshot/` reads the map, `REGISTRIES` or the reason codes. I grepped backend, contracts, simulator,
     tools and the frontend.
7. **Changed existing tests.** None is weakened.
   - (a) The two 3b2 tests keep their planted MINI_GRID registry and their exact expected texts. Adding the real cold and EV registries is
     required, because the real `PINS` now name them; without them `check_pins` refuses `STRUCTURE_PIN` before the asserted text.
   - (b) `test_t5` drops the three mechanisms because they are now pinned. Their pins are asserted positively by `test_t1` (`PINS ==
     DESIGN_PINS`) and by 3B6 test 7 (`pinned_category == PROTECT_ASSET`).
   - (c) `test_10_grep` gains exactly the one import the spec adds.
   - The widened `test_t2_check_all_with_planted_registries_runs_no_pin_check` still catches its regression: its last line
     `check_all(registries={"MINI_GRID": MG})` would now refuse on the real cold and EV pins if pins ran.
   - The manifest-row widening in `test_t1` matches only a bare-rename node (`nights_without_backup_cover: uncovered_nights`). I checked
     `COLD_EXCURSION`'s `NO_MANIFEST_ROW` against the manifest: no excursion findings row exists, and the test fails if one appears.
8. **The plant deviations.**
   - P1 (`* 1`) changes no value, so test 4 cannot fail on it. The guide is wrong for this plant. A value-changing variant such as `* 2` is what the
     guide needed.
   - P2 to P6 also fail test 3, because the spec's own "EV alone" and L2 cases use the real EV rows. D-3B6.16's "cannot
     fail test 3" is over-stated in the guide. Extra failures are harmless. Neither deviation needs a code change.
   - An Architect note for the next guide: write data plants as "must fail at least".
9. **Tests first not followed (units 1 and 2).** I judged the tests on strength.
   - Tests 1, 2, 4 and 4b read only the pack or their own literals (W2). I checked the imports: nothing expected comes from the row files, `HOMES` or `SOURCE_STATE`.
   - Test 3 asserts full texts.
   - Test 5b uses four month lengths, so a constant month length fails.
   - Test 8 uses raising fakes.
   - The tests are strong, apart from L1.
10. **Collision with 4a and 3B4.**
    - `git merge-tree main b9bd03757` is clean. `main` moved after the base only in `test_4a_energy_to_cash.py`, with new energy cases that do not touch the structure registry.
    - `registry.py` keeps MINI_GRID at v4, as on `main`.
    - 3B4's branch does not yet touch `check.py`. Its planned edit (spec §2.3) adds a separate `OBSERVE_CODES`, not `CODES`, so 3B6's
      `CODES[:-1] == CODES_BEFORE` survives. `check_observed` iterates only over `OBSERVED` keys (MINI_GRID), so cold and EV do not refuse
      `COVER`. See RR1.
11. **No vertical code.**
    - The diff of `evaluate.py` and `expressions.py` is empty.
    - `check.py` names no cold or EV key.
    - `read.py` names them only in the spec-mandated `SITE_TYPE_TO_STRUCTURE` literal (L2).
    - No migration, no `tools/` edit, no served text.

### Findings

| # | Sev | File:line | What | Why it matters | Fix |
|---|---|---|---|---|---|
| L1 | Low (test strength; not an acceptance gap: the spec defines 5c as a token check) | `backend/tests/test_3b6_cold_ev_structures.py:522-536` | Test 5c checks that a quoted token occurs somewhere in the file, not that the record exists. Deleting the `ev_connector_fault` or `ev_connector_state` `Role` from `EV_ROLES_1` still passes, because the same token stays in `EV_CADENCE_PROPERTY_BY_ROLE` (`binding_roles.py:221-222`). `"EV_CHARGER"` occurs 6 times in `ev_foundation.py`, including a layout map. | A HELD leaf could outlive its record, which is the honesty failure D-3B6.13 guards against. | Assert against the live records: role names in `{r.role for r in COLD_ROLES_1}` and `EV_ROLES_1`, `"ev-site-import-limit" in COMPONENT_PROPERTY_DEFINITIONS`, `"EV_CHARGER" in COMPONENT_TYPES`. Keep the literal-set equality. |
| L2 | Low (packet accuracy) | `specs/3B6-cold-ev/packet.md:12` | The packet says "`check.py`/`read.py` name no cold or EV key". `read.py:29-30` names `COLD_CHAIN` and `EV_DEPOT_CAPTIVE` in `SITE_TYPE_TO_STRUCTURE`. Spec §4.1 requires that, and guide item 2 overlooked it. | Claim only what is true. | Say "`check.py` names none; `read.py` only in the Site-type map". |
| L3 | Low (coverage) | `backend/tests/test_3b6_cold_ev_structures.py:558` | Test 6c forces only `staff`. The other shared commercial ID, `outstanding`, is covered by the same guard (my plant), but no test reads it. | It is a cheap parametrisation and closes R-SHARED-ID for both shared IDs. | Parametrise 6c over `("staff", "outstanding")`. |

No acceptance gap. No finding on correctness, contract or architecture.

### Checks I ran (at `b9bd03757`)

- `tools/heavy-slot.sh -- python -m pytest` on the 3B6 file, 3b1, 3b2, 3b3, 4b1, 4d, 5a, 5b, the 3b7a seam and snapshot files, and 4a (no database,
  `PYTHONPATH` set to the worktree): **679 passed, 1 skipped, 22.4 s**. This matches the packet's run at `13d1f98d0`. HEAD changes only
  documents after that commit (`git diff 13d1f98d0 b9bd03757 --stat`: packet, spec status, `.ai/state`).
- `pwsh tools/check-architecture.ps1` with `ASSETOPS_GUARD_PYTHON` set: **passed**. Without it, the chain-structure guard refuses to run for want of a `.venv`. That is environmental.
- `pwsh tools/check-agent-workflow.ps1`: **passed**.
- The shared-ID plant (item 4) and `git merge-tree` against current `main`: as above. Scratch copy deleted.

### Not verified by me (cited)

- The Postgres files (`test_3b3_structure_read_postgres`, `test_4a_energy_to_cash_postgres`,
  `test_3b7a_structure_snapshot_postgres`): the packet reports 16 passed at `13d1f98d0`. Code is identical at HEAD. Not rerun,
  because no finding needs it.
- check-all (40 guards): cited from the packet. Plants P1 to P30: cited, except my own shared-ID plant.

### Residual risk the packet does not name

- **RR1 (3B4 rebase).** 3B4 is based on `17775a4d5` (before 4a). Its `check.py` commit must be written onto 3B6's reshaped
  `check_all`, which runs L2 per entry, then the cross-registry not-applicable pass, then `check_pins`, then 3B4's `check_observed`. Its
  Postgres fixture plants `("NOT_DECLARED",)` for a COLDCHAIN Site (`test_3b4_observer_postgres.py:177,306,490`). That is only a
  pass-through literal, but after 3B6 a real build writes `("STRUCTURE_OTHER_KEY",)`. 3B4's reviewer should check both.
- **RR2.** `ProductLeafSource` raises `STRUCTURE_LEAF_INPUT` for any cold or EV leaf flipped to `PROVIDED` that has no calendar branch, for example `rate`. That
  is correct today: `9d` and `9e` must add the provider together with the state change. It is already implied by R-SHARED-ID, so this note is informational.
