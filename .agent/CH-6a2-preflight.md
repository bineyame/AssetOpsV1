# CH-6a2 pre-flight (evaluator and claims, pure)

Branch `task/CH-6a2-evaluator` from main `6b3bb9182`. Sheet: plan2 working copy of `build-sheet-CH-6.md` (CH6a1-R is
uncommitted there; it is not in `6b3bb9182`). Paths: `B` = `backend/assetops_backend`, `F` = `frontend/src`.

## Sheet against code

- **P3 Claim.** Merged `Claim` (`B/chain/vocabulary.py:90-101`) and `count_basis` (`:112-118`) equal §S.2 exactly:
  fields `key, value, basis, days, text`; `to_json` sends Decimal as string; days keys `CLAIM_DAY_KEYS` (`:70`)
  include `pending`. No adaptation needed. `NOT_KNOWN_TEXT = "Not known yet"` (`:71`) already equals A4
  `money.not_known`; it is reused, not duplicated.
- **P7 `boardMoneyText`** (`F/sites/OutcomeBoard.tsx:79-86`, `F/ui/money.ts:7-19`): null when either bound is null;
  each bound by `money2` (two places, half-even on the absolute value, exact, `-0.001` -> `0.00`, no float); equal
  bounds -> one amount, else `"{lo} to {hi}"`; `" {currency}"` only when currency is truthy. Fixture cases: the nine
  of `outcomeBoard.test.tsx:110-119` plus `0.00`, a negative, a negative rounding to zero, `0.005` (half-even down),
  `0.015` (up), a 10-place value. `money_text(low, high=None, currency=None)`: `high=None` means one amount.
- **Judges.** `judge` `B/outcomes/objectives.py:112-124`, `judge_month` `:127-143`, `MEASURES` `:57-73`,
  `CHAMBER_RANGE_MEASURE = "excursions"` `:76`. Called unchanged; not edited.
- **Day grade rule.** `_day_grade` / `_counts` (`B/chain/reader.py:42-86`) are the one day rule: NOT_EXPECTED only when
  no row of the day is expected; PENDING weakest; a requested measure with no row is NO_DATA. The evaluator's `days`
  come from `_counts` over the window (exposed under a public name; no rule change).
- **Records/strategies (CH-6a1).** `CONTRIBUTIONS` `B/outcomes/outcome_map.py:149-179`, `kpi_record` `:187`.
  `ContributionContext` `B/chain/strategies/base.py:26-37` (additive only, CH6a1-R Q5), `Effect` `:40-50`.
- **Stored values.** `productive_kwh` value `{"kwh": ...}` and money `{"amount", "currency": str(...)}`
  (`B/chain/measure_impls.py:149,160`); the `str()` there is the CH-6a1 L3 source of `"None"`.
- **Opportunity item** (`B/chain/opportunities.py:115-134`): `state`, `study.status`, `study.headroom_kw`
  `{low, high}`, `study.window_hours`, `limit_line` (already `vocabulary.limit_line`). NodeInputs.opportunity is
  this item.
- **MG-1 texts** `MG1_SO_FAR/PACE/TOO_EARLY/MISSED` at `B/site_outcomes/mini.py:151-154`; formatting `num` `:305-315`,
  `plural` `:342-347`. The Grow headline words are now at `mini.py:478` (sheet `:452` drifted).
- **Lows.** L1 `grade_counts` (`B/chain/strategies/graded_verdict.py:13-24`) ranks by `GRADES` order, so NOT_EXPECTED
  and PENDING outrank COMPLETE: fix by `_day_grade`. L2 `priced_energy._earnings` (`priced_energy.py:31`) filters per
  row: fix to the day grade (a day adds money only when its weakest grade is COMPLETE or PARTIAL; same as R5's MG-1
  value). L3 (`priced_energy.py:37`): a row with an amount and no currency makes the money NOT_PRICED.
- **Lane 2 overlap (CH-9b2, 0052, `actions/*`):** none in files. Possible text-only merge contact in
  `B/chain/vocabulary.py` if CH-9b2 appends verification copy there (append-only both sides). No migration here.
- **Stored bodies:** none change in CH-6a2 (no composer/route wiring). The polish clone is left to CH-6a3.

## Questions (batched, each with a default)

1. **Potential's money line in one Claim.** §S.2 has one `text`; A3.3/R11 want a value line and a money line.
   Default: `value = {"low", "high", "unit": "kW", "money_low", "money_high", "currency"}` (strings), `text` = the two
   lines joined by `"\n"`; CH-6a3's `OutcomeRow` splits on `"\n"` into two `ob-part` lines.
2. **Basis of a claim with no day rows** (MG-5 verdict, MG-2 `avoided_cost` earnings, both potentials). Default:
   MG-5 and MG-2 earnings take `days` = `_counts` of their nearest stored measure (`critical_served`,
   `avoidable_gen_min`) over the window, so `count_basis` applies as for every claim; a potential has `days=None`
   and basis COMPLETE when shown (SUPPORTED, or the warning present), else NOT_KNOWN.
3. **Moving the MG-1 texts "unchanged" touches `mini.py`**, but acceptance says no composer edit. Default: move the
   four constants to `vocabulary.py`; `mini.py` imports them under the same names (import-only diff, no logic line),
   so its tests and `COPY` stay unchanged.
4. **Potential vs thread state.** R13 defines only the status signal (open when OPEN or RECURRED). Default: the
   potential part shows the study for any thread state except WITHDRAWN (CHANGE_APPLIED still has unused headroom
   until verified); WITHDRAWN or no thread -> "No potential found yet". `headroom_signal_open(item)` implements R13.
5. **MG-1 with no counted day** (value None). Default: the verdict claim text is the composer's MG-1 actual text
   when given (`MG1_ACTUAL`, "sales not recorded"), else `target.none` / NOT_KNOWN; verdict NOT_JUDGED.
6. **No objective for a KPI.** Default: the `kpi` claim has value None, basis from its days, text `target.none`
   ("No target set yet"); `target.days_none` is used for the days line by CH-6a3.
