# 6h handshake review (pre-code, W4)

Reviewer (Claude, not the author), 2026-11-22. Read on `main` at `c39006bf6`: `spec.md` rev 0, 6f `rulings.md`
D-P6.42 to D-P6.58, 6f `spec.md` rev 1 §2a/§4, `assessment-levers.md`, `owner/owner-6f-q1-levers-2026-11-22.md`,
and the code 6h extends (`structure/levers.py`, `check.py` `_lever_fault`/`check_levers`, `difference.py`,
`decisions/evaluate.py`, `models.py`, `run.py`, `records.py` `prepare`/`state_one_off`, migration 0072,
`rows_*.py`, `pins.py`, `tests/option_fixtures.py`, `test_6c_difference.py`, `test_3b6_cold_ev_structures.py`),
and the manifest by grep.

## Summary

**Buildable without design: not yet.** Five blocking points, each small and each with a proposed answer below.
None changes the direction (named options, records as document levels, protective levers unranked) or the size
much (about +0.25 u in 6h2, still under the 6-unit cap). Once the Architect rules B1 to B5, the spec is buildable.

**Literals recomputed by hand from the registry expressions and the 6c fold:** Mwea N1 **1670.00** holds (monthly
485.00 x 4 = 1940.00, less 270.00). Kasarani K2 **630.00** holds (missed 6 to 0, penalties -720.00, less 90.00).
Thika T1 **-100.00** holds **only if** `stopgap-and-claim` changes `uncovered_nights` alone (B1); as §5.1 is written
the option has no `backup_unproven_days` record and its value is null.

**H1 to H5:** agree with all five; H1 and H2 with one addition each (N6, N7).

## 1. Literal recompute

| Fixture | Step | Result |
|---|---|---|
| N1 Mwea | `contract_crate_days` +4500, `contract_rate` +0.18, `handling` +100.00 (option-only neutral 0) | |
| | `revenue` = d(ccd) x v1(cr) + v0(ccd) x d(cr) = 4500 x 0.18 + 0 | +810.00 |
| | `kwh_model` = k x d(ccd) x v1(model_factor) = 0.25 x 4500 x 1 | +1125 |
| | `kwh` +1125; `energy` = 1125 x 0.20 | +225.00 |
| | `cost_to_serve` = 225.00 + 100.00; `contribution` = 810.00 - 325.00 | +485.00 |
| | 485.00 x 4 - 270.00 | **1670.00** (manifest `net_contract` 1670.00) |
| T1 Thika | base `uncovered_nights` 26 (manifest: 6 to 31 Oct inclusive, stock every night, no rota); record 0 | -26 |
| | `nights_without_backup_cover` (via `also`) -26; `contribution` forced, rests on nothing | 0 |
| | 0 x 1 - 100.00 (currency from the one-off, D-P6.29) | **-100.00**, needs B1 |
| K2 Kasarani | deliverable min(4 x 50, 400) x 7 = 1400; scheduled 45000 / 30 = 1500; supplied 1400 | |
| | required 11 x 140 = 1540; short ceil(140 / 140) = 1; missed max(8 - 2 - 0, 0) + 0 | 6 |
| | record 6 → missed max(8 - 2 - 6, 0) = 0; `penalties` -6 x 120.00; `cost_to_serve` -720.00 | `contribution` +720.00 |
| | 720.00 x 1 - 90.00 | **630.00** |

K2 is a unit fixture. On the manifest's Kasarani (`KAS-OEM-STOPGAP` `nights: 2`, `KAS-OEM-WAIT` penalties 240.00,
`modelled_12m_change` 150.00) the DD world should read **150.00**; see N6.

## 2. Handshake H1 to H5

| # | Position | Why |
|---|---|---|
| H1 | **Agree**, plus N6 | K2 proves the mechanism at unit level; a page that names the missing November record is honest. But "gate G4" is cited in §8 and not defined in §2, and the DD-world figure (150.00) is not pinned anywhere. |
| H2 | **Agree**, plus N7 | The manifest's formula gives 26 (`backup_unproven_from` 2026-10-06, no stock-free or rota nights); a missing base names its record through `base.missing` (never 0). The no-action *level* is a separate question (N7). |
| H3 | **Agree** | 6f rev 1 §2a already reads `title`, `question`, `option_label` and `no_action` from `decision_lever.*`. One fix to the table: `KEEP` cannot carry two texts (N1). |
| H4 | **Agree; checked** | 0072 leaves column checks unnamed (its docstring: "column checks keep `<table>_<column>_check`"). On `assetops_pt23142e7e4e_main_test` (at 0072) the live names are `decision_option_generator_check` and `option_evaluation_run_outcome_check`, as §3.4 writes them. |
| H5 | **Agree** | Branch 14 passes (pin row `excursion_crates` and purpose `nights_without_backup_cover` are both Protect P1); P4's `FINDING_NOT_ON_LEVER` reads the pin row's `levers`, so a COLD_EXCURSION Finding can carry Thika's cover decision. It is a data row: another excursion cause adds its lever to the same row. |

## 3. Blocking questions (each with a proposed answer)

**B1. `backup_cover`: `stopgap-and-claim` changes both leaves, but T1 and the manifest record only one.**
§5.1 gives `stopgap-and-claim → both` (`uncovered_nights`, `backup_unproven_days`); T1 and the DD row state only
`uncovered_nights` = 0. By §4.2 the missing `backup_unproven_days` record gives `LeafChange(None, ...)`, so T1's
stopgap value is null, not -100.00. The manifest's three Thika options all change `uncovered_nights` only
(`THIKA-EPC-WAIT/STOPGAP/SELF changes: {uncovered_nights: ...}`).
*Proposed:* `backup_cover.changes = ("uncovered_nights",)`, both options → `uncovered_nights`; drop the
`BACKUP_COVER__BACKUP_UNPROVEN_DAYS` record words; T1 `self-repair` missing = `[OPTION_RECORD, DECISION,
uncovered_nights]`, `[ONE_OFF, DECISION, null]`. (If the Architect wants a proven backup on `self-repair`, give
`self-repair` both leaves and keep `stopgap-and-claim` on `uncovered_nights`; T1's literals then stand as written.)

**B2. An option's own missing records are not named when its changed leaves do not reach `contribution`.**
`_value_option` takes `missing` only from the outcome's `missing_leaves` plus the one-off. For `backup_cover` and
`generator_redundancy` the changed leaves (`uncovered_nights`, `reduced_days`) are outside `contribution`'s closure,
so the forced `contribution` is 0 with no missing. T1's `self-repair` would list only `[ONE_OFF]`, not the records
§10.1 expects; worse, with a one-off held and no record it would read value = -one-off, a missing record read as 0.
*Proposed:* in `_value_option`, after the outcome's misses and before `ONE_OFF`, add a `MissingInput` for every
changed leaf whose `LeafChange.delta` is None (catalogue `changes` order, de-duplicated), and value is null when
any is present. Plant: remove it → T1 `self-repair` with a one-off held reads a value (test 3).

**B3. A no-money-path option gets evidence `NEUTRAL` and a false source class.**
For T1 `contribution` uses no factor, so `out.evidence = weakest(()) = "NEUTRAL"` and `out.origins = ()`. The 0072
check `option_evaluation.evidence_class IN (RECORDED, MEASURED, DECLARED, DERIVED, ESTIMATED, MODELLED)` refuses
`NEUTRAL`, so test 6 (T1 on Postgres) fails at insert while the memory store passes. `_source_class(())` gives
`RECORDED` even when Thika's record is `--emulated` (DD world): an emulated figure labelled as recorded.
*Proposed:* the row's evidence is `weakest` over the outcome delta's evidence and each changed leaf's
`LeafChange.evidence`; its source class reads the union of `out.origins` and the changed leaves' origins. The
generator path is unchanged (its changed leaves are already in `contribution.used`). Add T1e (emulated record →
`EMULATED`, evidence `DECLARED`).

**B4. An option record's currency never enters the difference.**
`LeafChange` has no currency and `_Difference.delta` skips `LeafChange` parts when collecting currencies; an
option-only leaf's no-action value is `NEUTRAL` with no currency. So on N1 the `revenue` (+810.00) and `handling`
(+100.00) effects carry currency None (6f would print money without a currency), and a KES record against a USD
base is not caught when no one-off is held. §4.2's one-off-currency rule does not cover either case.
*Proposed:* `LeafChange` gains `currency: str | None = None` (keyword, default; every existing caller unchanged);
`stated_changes` sets it from the record; `delta` adds it to `currencies`. The existing `CURRENCY_MISMATCH` and
`ONE_OFF_CURRENCY` then cover §4.2's case, and `OPTION_RECORD_CURRENCY` can be dropped (or kept as the word, if the
Architect prefers a distinct sentence). N1 asserts `revenue` and `handling` effects in USD; plant: record currency
dropped → N1 `revenue` currency None.

**B5. The existing lever checks refuse every `STATED_OPTIONS` lever.**
`grid()` of a lever with no axes yields one empty point, so `option_key` gives `""`, which fails `_OPTION_KEY`
(branch 13). §3.2 says branches 2 to 14 apply unchanged, so the real `LEVERS` fail start-up.
*Proposed:* the axis, template and grid branches (6 to 13) run for `SETTING_GRID` only; branch 17 already covers
`STATED_OPTIONS` (axes empty, options non-empty); add "key_template non-empty" to 17. Branches 2 to 5 and 14 run for
both.

## 4. Non-blocking questions (proposed answer applied unless the Architect says otherwise)

- **N1** `no_action` `KEEP` has two texts (generator vs others). *Proposed:* `NO_ACTION_WORDS = ("KEEP_SETTINGS",
  "KEEP", "WAIT_FOR_REMEDY")`; `generator_stop_reserve` takes `KEEP_SETTINGS`.
- **N2** Two record words state a difference, against D-P6.58: `FLEET_CAPACITY_USE__BUSES` "the route offer: buses
  added" and `CHAMBER_EFFICIENCY__EXCESS_KWH` "...the electricity it is expected to recover". *Proposed:* "the route
  offer: buses in the fleet" and "the repair quote and the electricity above the model after the repair".
- **N3** Two existing tests must change, named, not loosened: `test_6c_difference.py::test_1_stated_records_are_never_read`
  asserts the signature is exactly `[registry, base, changes]` (becomes `[..., "also"]`, still no stated map);
  `test_3b6_cold_ev_structures.py:171` asserts cold and EV rows have `levers == ()` (becomes: equal to the rows of
  §5.2). §10.2 item 3 "unchanged" should say so.
- **N4** `obligation_hours_without_redundancy` is a mini-grid **node**; `rows_mini_grid._node` has no `levers`
  keyword. *Proposed:* it gains `levers=()` too (§5.2 names only the cold and EV helpers).
- **N5** `option_inputs` has no `base` or records today and requires a study. *Proposed:* `option_inputs(options,
  lever, study | None, by_key, admissions, one_offs, *, base, records, grid_changes)`; for `STATED_OPTIONS`, E3's
  study block is skipped and `RunRow` gets `study_sha256 = None`, `study_identity = None` (0072's pair check).
- **N6** Define gate G4 in §2 (Kasarani valued on the DD world only when November inputs read, Q11) and pin the
  DD-world literal: with the manifest's November (`nights: 2`, penalty 120.00) Kasarani reads 150.00, as the
  manifest's `modelled_12m_change`.
- **N7** Thika's no-action level. The manifest's reference option `THIKA-EPC-WAIT` sets `uncovered_nights =
  days_to_restore` (nights to the supplier's restore), while 6h uses October's 26 as the level a month under doing
  nothing, so the page will show "uncovered nights -26". *Proposed:* keep for 6h (the decision month's own leaf,
  D-P6.58), state it in the packet, and let 9c's remedy records (restore date) set the forward level; the
  coordinator names this figure to the owner before the walkthrough.
- **N8** R7's "money unit" is `unit.has_money_dimension` (so `contract_rate`, MONEY/DAY, needs a currency);
  `declared_by_script` is true from the CLI (as the one-off); `_covering_role` is parameterised by command
  (`decision.option_record`), not hard-wired to `one_off`.
- **N9** `BOUNDS_NOT_CHECKED` is the outcome for a `bounds_required` lever even when no option is valued (Kisiwa,
  Ruiru `charger_restore`). *Proposed:* yes, unconditional; 6f's outcome note reads the same.
- **N10** The plant "option-only level read from base instead of `neutral`" cannot fail: an option-only base leaf
  is always its neutral (sources state `OPTION_ONLY`; `evaluate` refuses a NEUTRAL leaf whose value differs).
  *Proposed:* one rule, delta = record - base value (missing base named), and drop that plant; it also avoids a
  double count if an option-only leaf ever holds a real base value.
- **N11** E2 refuses a study for any `STATED_OPTIONS` lever, so the queued EV replay slice must amend E2 (and
  `charging_schedule` is valued by it). Record that in §13.
- **N12** `check_lever_paths`: a `PENDING_LEVERS` key that is not a `PINS` key has no structure; refuse with
  structure key `""`.

## 5. Owner rules checked

- Levers are data; `stated_changes`, `prepare` and the evaluator name no structure or factor (as §11 Q2). The only
  structure literals are catalogue rows and words. Holds, given B2/B3 are written generically.
- One figure per quantity: records are document levels; the model computes every change (D-P6.58). Holds, with N2.
- Missing named: holds only after B2 (an unrecorded leaf outside `contribution` must still be named).
- No workaround called a fix: the union is withdrawn; 6h fixes the model. Nothing in the spec is a relabelled
  workaround.
- Range rule (§8): same columns per Site type; values where records exist. Holds.

## 6. Residual risk not named in the spec

- Ruiru `fleet_capacity_use` is a Grow lever on a structure with no `revenue` row (`contribution = 0 -
  cost_to_serve`), so once valued its options can only read worse than doing nothing. Out of 6h (no records), but
  the slice that values it needs a revenue or contract term.
- 6f rev 1 fixture F6-T is 6h's T1; B1 or B2 changes T1's missing list, so F6-T follows.
- Unit card: 4.0 u stays plausible; B2 to B4 add roughly 0.25 u to 6h2 (still one slice, under 6 u).

## 7. Checks run

- Read-only on `main`; no code exists. Live constraint names read from `assetops_pt23142e7e4e_main_test`
  (`pg_constraint`): `decision_option_generator_check`, `option_evaluation_run_outcome_check`.
- Literals recomputed by hand against `rows_cold_chain.py`, `rows_ev_depot.py` and `difference.py`'s product rule.
- Not run: architecture and workflow scripts (no diff to check).
