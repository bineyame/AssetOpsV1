# 3B6 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main` (spec §0 (a) to (c)), write their questions here in one batch. Number them R1,
R2 ... and I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects,
and is marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

Checked at `main` f75321b92. Every figure quoted below was run read-only against the pack and the registry code; no
database was touched.

**R1 (done). Spec §5.3, §6.1 test 5b, guide P9.** The product read is fixed at month `2026-10`, 31 days. A provider
that hard-codes 31 days, or `nights_in_period` that returns 31 for every month, passes test 5b and the `chamber_minutes`
44640 check. The calendar leaves are the only values this slice serves, so they must be able to fail. Expected: test
5b also reads `2026-02` for both Sites (`period_days` 28, `nights_in_period` 28, `chamber_minutes` 40320, all
DERIVED), and the guide gains plant P19 ("`nights_in_period` returns 31") failing it.

**R2 (done). Reviewer guide P4, P5, P6, P13, P16; spec §6.1 test 3.** Several plants name test 3 but are written as
data mutations of the real `REGISTRIES`. Test 3 passes its own mapping to `check_all`, so a mutation of the real
registry fails tests 1, 2 and start-up (`create_app`), not test 3; and plants of the *code* (drop the L2 key check,
drop the cross-registry pass, drop the own-row refusal) are not in the guide at all. Expected: the guide separates
"data plants" (P4, P5, P6: failing test 2's `check_all()` and `create_app`) from "code plants" and adds three:
P20 L2 line removed (fails test 3 `STRUCTURE_CATALOGUE COLD_CHAIN/-`), P21 cross-registry pass removed (fails test 3
"EV alone"), P22 own-row refusal removed (fails test 3 `cost_to_serve`). P16 stays "test 2 only" (it is not forced by
`STRUCTURE_COMPOSES`: `buses_short_per_night` is unit ONE; run on a scratch copy).

**R3 (done). Spec §4.3 last row, §6.1 test 8.** `BridgeRead.site` is listed "no change", but it evaluates
`self._actual.site_inputs(site, ...)` (reading every cold or EV leaf through the providers) as an argument before
`self._targets.site(...)` raises `STRUCTURE_KEY_NOT_READ`; `BridgeRead.portfolio` and `TargetRead.portfolio` with a cold
Site have no test either (test 8 names `TargetRead.site` and `SnapshotRead.site` only). A "no change" claim with no
test cannot fail. Expected: test 8 adds `BridgeRead.site(cold)` raising `STRUCTURE_KEY_NOT_READ` with the leaf-source
fake failing if called (so either the guard moves ahead of `site_inputs` in `BridgeRead.site`, one line, or the spec
says the providers are called and the test allows it), and `TargetRead.portfolio([KOBO, cold])` and
`BridgeRead.portfolio` excluding the cold Site as `OTHER_STRUCTURE`.

**R4 (done). Spec §1, §8 question 3, §10 Q3; D-3B6.3.** `applicability()` has no caller outside tests, and
`SiteStructure`, `PortfolioStructure` and `site_count` carry nothing about it: a reader asking an EV Site for `revenue`
finds no key. §8.3 and §1 say a depot's revenue "reads *not applicable*"; what is built is a declared, checked,
queryable fact that the next screen (3B5) must call. Expected: §8.3 and §1 reworded to "is declared not applicable and
`applicability()` says so; no read shows it until 3B5", and a one-line interface note naming `applicability()` as the
only supported way to tell "revenue does not apply" from "revenue is not in this structure" (so 3B5 does not infer it
from a missing key).

**R5 (done). Spec §4.2 table, `HELD_NOT_CALCULATED` rows.** The state tells a reader a record is held and not yet
calculated, so each HELD leaf must name a stored record, and the table is inconsistent: COLD `backup_unproven_days` is
HELD (work cases) while COLD `uncovered_nights`, from the same work-case record (manifest `leaf_sources`), is
`NOT_CONNECTED`; EV `chargers_installed`, `charger_kw` and `import_limit_kw` are HELD "declared in the EV Foundation",
but `ev_foundation.py` declares per-charger `ev-charger-max-power` and a site import limit, not a charger count or a
`charger_kw` leaf; EV `charger_out_days` is HELD (work cases) with no cited reader. Expected: each HELD leaf cites the
file where its record is stored today, or is moved to `NOT_CONNECTED` (the safe default: "Not available yet, record not
connected"); §4.2 and test 5b's literal table change accordingly.

**R6 (done). Spec §4.2 last paragraph, test 6, guide P10.** `COMMERCIAL_LEAVES` and `money._ROWS` are keyed by factor ID
and `money.py` holds `_MG = REGISTRIES["MINI_GRID"]`. COLD shares `staff` and `outstanding` with the mini-grid. Today
they are `NOT_CONNECTED` for COLD so nothing reaches `_judge`, but the day `9d` flips COLD `staff` to `PROVIDED` the
commercial source would judge it with mini-grid rows. Expected: the packet names it `R-SHARED-ID`, and test 6 asserts
that no COLD or EV leaf whose ID is in `COMMERCIAL_LEAVES | LITRE_LEAVES | money._ROWS` (and, after 4a, `ENERGY_LEAVES`)
has state `PROVIDED` or `PROVIDED_ELSE_ASSUMED`; P10 then fails on that assertion as well as on the raising fake.

## Implementer questions (pre-flight results first)

**Pre-flight (a), spec §0.** Built both registries in a scratch script from the manifest and spec tables §2.2.1 and
§2.2.2 (not the literal row files): 36 and 42 rows; `check()` passes for both, no refusal. With the three new pins,
`check_pins` passes. Flipping each `NONE` leaf or node to `SUM`: refused by `STRUCTURE_COMPOSES` in every case except
`model_factor`, `period_days`, `nights_in_period` and `buses_short_per_night` (so P13 holds at start-up, because
`charger_kw` is KWH/HOUR; P16 does not).

**Pre-flight (b).** With `PINS` extended by the three and `PENDING_PINS` empty, `parity()` returns exactly one entry,
`UNEXPLAINED_FUEL` (PROTECT_ASSET vs OPTIMIZE_COST). The outcome-map literals' first moved outcomes are CC-6
(COLD_START_FAILURE), CC-1 (COLD_EXCURSION) and EV-1 (EV_INTERRUPTION), all Protect.

**Pre-flight (c).** The §4.4 grep over `backend/assetops_backend` returns about 60 hits, roughly 40 outside `structure/`
and `structure_snapshot/` (`chain/`, `sites/`, `scheduling/`, `site_outcomes/` and so on, all unrelated uses of the
literal `"MINIGRID"` or an unrelated `NOT_DECLARED`). Inside, hits not named in §4.1 to §4.3 or the "no change" list:
`structure/read.py:61` (`site_count` fallback), `structure/sources.py:144` and `structure/money.py:165,174` (key lookups
a cold key reaches; safe, test 6), `structure/attribution/portfolio.py:21,103` (fallback reason; unreachable once every
non-composed Site is in `sites_excluded`), `structure/attribution/read.py:43` (filters by the key the target
composition returned). None needs a change.

**Pack figures.** Every SUM factor of both registries equals `derived-values.json` `portfolio.<tenant>.actual.sums` over
the three Sites (all within 0.005); the pack's other sums are exactly the `NONE` factors named in §5.2. Every hand
figure of §5.1 and §5.2 matches the pack. `metro-bus/Ruiru` `plan` has no nodes, as the spec says. `Kasarani`
`november_to_date` `nights_in_period` is 5 in the pack (the test takes leaf values from the pack, so no conflict with
the provider's month-length rule).

**I1 (done). Spec §0, §2.1 (the `REGISTRIES` literal), §6.3 first row; collision with `task/4a-energy-to-cash`.** 4a
edits, in the same hunks 3B6 edits: `registry.py` (the `MINI_GRID` entry becomes version 4, plus a comment line, inside
the `REGISTRIES` literal 3B6 rewrites), `sources.py` (the `MINI_GRID` `SOURCE_STATE` and `STATED_STATE` entries, the new
`ENERGY_LEAVES`/`ENERGY_STATED`, `__all__`, and the `NOT_CONNECTED or (PROVIDED and ... in COMMERCIAL_LEAVES |
LITRE_LEAVES | ENERGY_LEAVES)` line of `ProductLeafSource.leaf`), `check.py` (imports and `_stated`; no overlap with the
appended `_CHECKS` entry or `check_all`), `targets/read.py` (`MAIN_OF` headings; 3B6 edits `site` and `portfolio`, no
overlap), `composition.py`, and the tests `test_3b1_structure_registry.py:91` (version 3 to 4, next to 3B6's line 92)
and `test_3b3_structure_evaluate.py:377,664`. The spec says the `MINI_GRID` entry is "its version on main, unchanged":
on main it is 3, after 4a it is 4. Expected answer: unit 1 may start before 4a only for new files, the `Registry` field,
`applicability`, `check.py` and `pins.py`; the `REGISTRIES` literal, `sources.py` and the §6.3 rows for
`test_3b1:91-92` wait for the merge of 4a into the branch; the spec says "`MINI_GRID` keeps the version it has when
3B6 merges (3 on main, 4 after 4a)", and test 1 asserts no mini-grid version (only the new two, version 1).

**I2 (done). Spec §4.2 last paragraph, §5.3, test 6.** After 4a, the product chain is `EnergyLeafSource(energy_inputs,
CommercialLeafSource(..., LitreLeafSource(..., ProductLeafSource)), now)` (`structure/composition.py` on that branch);
test 6 builds Commercial over Litre over Product only, so it is not the production chain. Expected: after 4a merges,
test 6's chain gains `EnergyLeafSource(<inputs fake raising>, <the chain>, now)`, and "no fake is called" covers it;
4a's `_state` helper keys by `SITE_TYPE_TO_STRUCTURE`, so a cold or EV Site reaches the fallback unchanged (none of the
energy IDs is a cold or EV leaf; the test asserts the intersection is empty, R6).

**I3. Spec §6.3 (the sweep), `test_3b2_findings_pinned.py:234` and `test_4b1_stated_nodes.py:212-224`.** Two existing
tests change meaning without a literal change, and neither is in §6.3: `test_3b2:234` plants
`{"X": Registry("NOT_MINI_GRID_KEY", ...)}` and asserts only `code in CODES`; with the L2 key check it now refuses at
L2 (`STRUCTURE_CATALOGUE X/-`), the same code, so it still passes but no longer tests what its comment says.
`test_4b1` `_valued_cases` iterates every registry, so about 60 cold and EV cases join it automatically (the
STRUCTURE_ORIGIN refusal on an empty-origin valued leaf). Expected: the packet lists both under "no literal changed,
behaviour widened" and runs `test_4b1_stated_nodes.py` in the build (it is already in §6.2); if a new case fails, that is
a finding on the row, not a test edit.

**I4. Spec §6.3 line numbers.** Every `file:line` of §6.3 matches `main` (checked: `3b1:92`, `3b2:258-259`, `3b3:681`,
`:705`, `:783` stays, `5a:544`, `:674`, `:676`, `5b:813`, `3b7a:234`, `:285`). No other `STRUCTURE_NOT_DECLARED`,
`PENDING_PINS` or `set(REGISTRIES)` literal exists in `backend/tests`. No question; recorded so the packet need not redo
it.

## Answers (Architect, 2026-11-21; `rulings.md` "Handshake answers (round 1)"; spec rev 2)

R1 D-3B6.15 · R2 D-3B6.16 · R3 D-3B6.17 · R4 D-3B6.14 · R5 D-3B6.13 · R6 D-3B6.18 · I1 D-3B6.19 · I2 D-3B6.20 ·
I3 D-3B6.21 · I4 and §4.4 D-3B6.22, D-3B6.23 · size D-3B6.24. The reviewer and implementer confirm below, or raise a
new numbered question (round 2); the handshake ends when neither section has an open question.
