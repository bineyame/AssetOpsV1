# 6c handshake (rev 1 spec; reviewer and implementer pre-flight)

Fresh Claude reviewer, 2026-11-22, on `main` at `19c3e7cb8` (the 6a/6c rev 1 merge). Read: `spec.md`, `reviewer-guide.md`,
D-P6.1 to D-P6.19 (`specs/6-decision-valued/rulings.md`), 6a `spec.md` §2 to §4, 0K4d's study file, and the code below.
Not re-raised: Q1 (Kobo's fuel saved "Not available yet" until 0K4f), Q2, Q3 (6f1/6f2).

**Checked and found as the spec says.**
- `structure/evaluate.py`:
  - `evaluate(registry, leaves, stated={})` checks every leaf (`:396-415`), and `_check_leaf` has no sign check
    (`:183-209`), so pre-flight 1 holds.
  - `Context(prec=34, ROUND_HALF_EVEN)`, `EVIDENCE_ORDER`, `weakest`, `ORIGIN_ORDER` (with `unknown` last),
    `CARRIED_AS`, and `Missing`'s seven fields in the order F1's helper writes them.
- `expressions.py`: only `+ - * /`, `Neg`, and the calls `min`, `max`, `ceil`, `floor`. That is every case in §2's rule.
- Every registry has a `contribution` row (pre-flight 3).
- `StructureRead.site_inputs(site, month, known_at).leaves` (`read.py:118-131`) and `build_structure_read`
  (`composition.py:40`).
- `runs/admission.py`: `ADMISSION_PARTS` (energy_not_served, reserve_breaches, starts, full_charge) and
  `AdmissionRule` (6; 7, with a limit of 7 − 1). `admit` builds its parts inline (`:110-121`), so `judge` is a pure
  extraction.
- `INPUT_CLASSES` and `EVIDENCE_CLASS` are in `runs/replay_study.py`.
- Hand-checked figures:
  - F1b: every row of the table, the effects of `stop-70-reserve-30`, the 2710.80 threshold, ranks 1 to 4, and
    `AT_GRID_EDGE` only in F1g.
  - F1d's ≤ −898.00, F1f's 0.00 and F1i's −150.
  - C1's 800.00: it holds because `contract_crate_days` is OPTION_ONLY, so it is neutral 0.
  - E1's 2400.00: the numerator of `scheduled_kwh_night` has an exact zero change, so the missing `kwh_2200_2400` is
    never read.
- `/opt/assetecon/evidence/0K4d/kobo-61d/study.json`:
  - sha256 `c52e4755…eccc78b61`, with no `frame` key and 14 cases, all admitted.
  - `stop-90-reserve-30` is present, and the baseline is 90/30.
  - Each `*_by_month` holds `2026-09` (30 days) and `2026-10` (31 days). Stop 70 / reserve 30 is 242.444 L in
    October, with dawn worst `6611/190` and 4 days below.

## Reviewer questions (R)

**R1. The world-month rule rests on a header any file can claim** (spec §3.1, §3.3; D-P6.2; done question 8).
`frame.kind = SITE_RECORD` with the right tenant and Site code is all 6c checks. Nothing ties the study to the Site's own
record. 0K4d's season file is a case in point. It has full `2026-09` and `2026-10` entries, so stamping a `frame` on it
would value Kobo's October with the season's figures: D-0K4.38's forbidden case, passing every 6c test. 0K4d's
`replay_study` also has an unrelated `StudyFrame` (timezone, capacity, dawn limit). 0K4f could easily write that object
under the `frame` key.
*Default:* 6c ships as specified (today every study values nothing). The packet's residual risk names the gap. The
Architect adds to 0K4f's acceptance:
- the writer derives `frame` from the replay's input (the Site's stored readings, by tenant and Site), never from a flag;
- the study records a digest of those readings, which a later check compares.

Spec §8's "Writing the `frame` header (0K4f)" line cites this.

**R2. Several fixture rows leave fields to the evaluator, against W2** (spec §5; test 4 "every field of every row as a
literal"; guide 1).
- F1b's "Every option: `source_class` SIMULATED, `evidence_class` MODELLED, `assumed` ["diesel_price"]" contradicts R0
  for `no-action` (`DERIVED`, no effects).
- No `evidence_class`, `assumed` or effect `unit`/`currency` is given for C1, C1b or E1.
- For F1h, `source_class`, `evidence_class` and `assumed` are not given. For K1, only one row's dawn is given.

A builder who fills these by running the code writes expected values computed by the evaluator. The guide rates that
High.
*Default:* the Architect writes the missing literals into §5:
- F1b's line reads "every SETTING_GRID option". `no-action` is `SIMULATED`, `DERIVED`, `assumed` [], `missing` [], and
  has no effects.
- C1: `evidence_class` `MODELLED` (the change), `assumed` [].
- E1: `MODELLED`, [].
- F1h: SIMULATED, MODELLED, ["diesel_price"]. `diesel_price` is read because the delta of `candidate_l` is missing, so
  `d(diesel_l)` is MISSING and `val1(diesel_price)` is still folded: confirm.
- Effect currency: set on money rows only (`USD`).
- K1: every row's disposition, `missing` and admission pass, with dawn only for the rows the spec names.

**R3. Any input of unknown origin is labelled RECORDED** (spec §3.4 step 3; §5 "a priced or declared leaf has origins
(`"unknown"`,)"; done question 5). The rule gives SIMULATED, then EMULATED, otherwise RECORDED. C1 reads `base_kwh` and
`k_kwh_per_crate_day`, both of origin `unknown`, and is labelled RECORDED. That passes, but the label claims recorded
readings for a declared value whose origin is unknown. Nothing would catch an `unknown` that came from a simulated
source.
*Default:* keep the three classes (the database check fixes them), and write the rule out in §3.4: "`unknown` and
`observed-financial`/`field-integrated`/`bench-tested` read as RECORDED; the label speaks for the record origins only".
Test 4 adds a plant: a base leaf in C1 of origin `source-emulated` turns C1 `EMULATED`. Whether `unknown` should read
as the weakest class instead is for the Architect.

**R4. The import rules of the two slices collide** (6a §6 test 9; 6c §6 test 9).
- 6a's test 9 asserts "nothing under `decisions/` imports `runs/`". 6c's `study_input.py` needs `runs.replay_study`
  (`INPUT_CLASSES`), and `models.py`/`run.py` need `runs.admission`.
- `runs.admission` itself imports `runs.replay_study`, the replay study module, together with `runs.replay_port` and
  `assetops_contracts.forward_replay`. So "nothing under `runs/` that replays" holds only for direct imports.

*Default:* 6c amends 6a's test 9 to an allowlist: under `decisions/`, only `study_input.py`, `models.py`, `evaluate.py`
and `run.py` may import `runs.admission` and `runs.replay_study`, and only names from `__all__`/constants. 6c's test 9
checks direct imports, and also asserts that importing `decisions.run` loads no `simulator*` or `host*` module
(`sys.modules` after import).

**R5. Gate 6a's grep gives two lines, not one** (spec §0). `def add_run` is in 6a's `DecisionStore` Protocol and in
`MemoryDecisionStore`, both in `records.py`, so the gate as written fails on correct work.
*Default:* `git grep -n "def add_run" main -- backend/assetops_backend/decisions/` shows at least the Protocol line and
the adapter's.

**R6. The JSON line's top-level keys are ambiguous** (spec §4). The sentence lists `run_id, decision_id, outcome,
source_class, options`, then "plus the run's `frame` and `months_averaged`". It is not clear whether those two are
top-level or per option, or what form `frame` takes.
*Default:* top-level keys in this order: `run_id, decision_id, outcome, source_class, frame, months_averaged, options`.
`frame` is `{"kind", "tenant", "site_code"}`, with the last two null for a declared season. `admitted` is null for
`no-action`.

## Implementer questions (I)

**I1. The F1 lever has no entry in `SETTING_GRID_CHANGES`** (spec §3.3, §5 F1, tests 5 to 7). `SETTING_GRID_CHANGES`
is keyed by `lever_id` and holds only `generator_stop_reserve`. F1 injects the lever `test_stop_reserve`. Through the
study path (`EvaluationService`, Postgres, the command), `setting_changes(lever, …)` therefore finds no entry. The spec
gives no injection point. **High** (F1 end to end cannot run without a design the spec does not give).
*Default:* `setting_changes(lever, case, study, *, grid_changes=SETTING_GRID_CHANGES)`, with `EvaluationService(...,
grid_changes=SETTING_GRID_CHANGES)`. Tests inject `{"test_stop_reserve": SETTING_GRID_CHANGES["generator_stop_reserve"]}`.
The start-up assertion runs over every injected entry: its leaves equal `lever.changes`.

**I2. `run.py` cannot find the decision's Site** (spec §4 E3, E4). See 6a handshake I1: 6a's store has no Site-by-id
read, yet E4 needs a `SiteRef` and the frame check needs the Site code.
*Default:* 6a adds `DecisionStore.site_by_id`. If 6a merges without it, 6c adds it in commit 3, and the packet names
6a's files touched. **High** (cross-slice).

**I3. Test 8's literal scan fails on 6a's own code, and §3.5 needs a 35** (spec §6 test 8; §3.5 dawn).
- "`decisions/` holds no numeric literal outside `TIE`, the ±1 signs, and 0 and 1". But 6a's `decisions/records.py`
  holds `HORIZON_DEFAULT = 12`, the horizon bounds 1-60, the basis limit 200, the amount's 2 places and 12 digits, and
  the exits 2 and 3.
- §3.5 writes `margin_points` as "worst − 35". The dawn limit is not in the study file (it lives only in 0K4d's
  `StudyFrame.dawn_min_soc_pct = Fraction(35)` and as `admit`'s default parameter).

So either the scan fails, or the builder writes the 35 in and scopes the scan ad hoc. **High.**
*Default:*
- The scan covers 6c's modules only: `decisions/study_input.py`, `models.py`, `evaluate.py`, `run.py` and
  `structure/difference.py`.
- 6a's `records.py` is out of scope by name, since its numbers are rules, not figures.
- `runs/admission.py` gains `DAWN_LIMIT_PCT = Fraction(35)`, used as `admit`'s default. That is one more added name
  beside `AdmissionMeasures` and `judge` (guide check 9 is amended). 6c imports it.

**I4. The dawn and admission storage form, and K1's "34.795"** (spec §3.4 step 4 "decimal strings", §3.5 "fractions as
`"n/d"`", §5 K1 "worst 34.795").
- The worst dawn reading is `6611/190`, which has no finite decimal. "34.795" is the file's `reading`, which §3.1 says
  is never read.
- §3.4 and §3.5 disagree on the form.

*Default:*
- Every fraction in `admission` and `dawn` is stored as `"n/d"`, in lowest terms; integers are stored as JSON numbers.
- K1 asserts `worst_soc_pct` `"6611/190"`, `margin_points` `"-39/190"`, `days_below` 4, `days` 61.
- §3.4 step 4 is reworded to "as §3.5".

**I5. Missing currency when the outcome's change reads no money leaf** (spec §2 `currency`, §3.4 step 1; 6a §2 check
`value IS NULL OR currency IS NOT NULL OR disposition = 'COMPARISON'`). Take an option whose every delta is exactly 0,
such as a SITE_RECORD case equal to the baseline. Its `d(contribution)` is 0 with no value read, so `Delta.currency` is
`None`. Then `value = 0 − one_off` is set with a null currency, which the database refuses. Alternatively the one-off's
`USD` "differs from" `None`, which adds `ONE_OFF_CURRENCY`, and a valued option reads as missing.
*Default:*
- When `d[OUTCOME_FACTOR].currency` is `None` and the change is exactly 0, the option's currency is the one-off's, and
  no `ONE_OFF_CURRENCY` is added.
- With no one-off, the option's `missing` holds `ONE_OFF` as usual.
- Test 4 adds a case: an F1 option with 0 L and 0 kWh gives value −90.00 USD, `DEFERRED`,
  `NOT_WORTH_MORE_THAN_NO_ACTION`.

**I6. E3's refusal order, and the place of the admission recomputation** (spec §3.3, §3.5, §4 E3).
- §3.5's `STUDY_ADMISSION_MISMATCH` sits in no E step.
- The order of the frame, month, grid, baseline and admission refusals is unstated.
- It is also unclear whether the ignored case (K1's `stop-90-reserve-30`) is recomputed: the spec says "recomputed
  equal on all 14 cases".

*Default:*
- E3 runs, in order: `read_study` (`UNREADABLE`, `NOT_CALIBRATED`, `LABELS_INVALID`); then, for SITE_RECORD,
  `FRAME_MISMATCH` and `MONTH_NOT_COVERED`; then `BASELINE_MISMATCH`, then `GRID_MISMATCH`, then the admission
  recomputation over every case, ignored cases included (`ADMISSION_MISMATCH`).
- All of this runs before E4, so a bad file never reads the structure.
- Test 5 asserts that the structure read is not called on each E3 refusal.

**I7. `identity` cannot be complete inside `read_study`** (spec §3.1). `identity` includes `ignored_cases` and
`months_averaged`, but `read_study(path)` has no decision. `ignored_cases` depends on the decision's options and current
settings.
*Default:* `read_study` returns the header identity plus `frame`. `run.py` adds `ignored_cases` and `months_averaged`
before `add_run`. Test 2 asserts the header identity, and test 5 the stored one.

**I8. The study keys' types, and F1's digest fields** (spec §3.1, §5 F1 header).
- In the real file, some figures are `{"exact"}` objects: `unserved_kwh`, `stop_soc_pct`, `reserve_soc_pct`,
  `worst_dawn_soc_pct`, `value`, and the admission part limits.
- Others are plain JSON integers: `reserve_breach_steps`, `max_starts_in_a_day`, `longest_days_without_full_charge`,
  `dawn_days_below`, `days`, and the top-level `days`.
- `new_dawn_days_below` is a list of date strings.
- `trajectory_digests` is an object (`{"site": <64 hex>}`), but F1 says "digests 'a' × 64 and 'b' × 64".

*Default:*
- `read_study` holds one table of key to type, using exactly those types, and a wrong type is `STUDY_UNREADABLE`.
- F1's `season_inputs_digest` is `"a" * 64` and its `trajectory_digests` is `{"site": "b" * 64}`.

**I9. F1's helper and fixture details** (spec §5).
- CALENDAR leaves need a value: `_check_leaf` refuses a valueless leaf whose evidence is not NOT_AVAILABLE. Default:
  `period_days` and `nights_in_period` are the month's days (31 for 2026-10), and `minutes_per_day` is 1440, all
  DERIVED with no origins.
- `diesel_price` "ESTIMATED, carried ASSUMPTION" needs a `Missing` with `carried_as="ASSUMPTION"`, `cause`
  `NOT_RECEIVED` and `blocks` `()`, plus currency `USD` (`_check_leaf`). Default: as stated.
- F1i gives only `avoided_l_by_month`, but `full_months` looks at every field. Default: F1i's
  `added_throughput_kwh_by_month` holds the same months and days.
- F1e: `stop-60-reserve-25` (longest 8) also fails `full_charge`. Its file parts must say so, or recomputation refuses.
  Default: the fixture writes both failing parts, with first failing `starts`.

**I10. Two small mappings the spec leaves open** (spec §2, §3.4 step 1, step 3).
- The currency plant's missing leaf `("currency",)` is not a leaf, so the base-leaf lookup in step 1 fails. Default:
  `MissingInput("CURRENCY_MISMATCH", "STRUCTURE", None)`.
- `assumed` lists `carried_as == "ASSUMPTION"` only, whereas `evaluate` treats `TARGET` and `ASSUMPTION` alike as
  assumed (`_ASSUMED`). Default: both, as `evaluate` does.

**I11. An exception inside E6** (spec §4). E4 maps any exception to `STRUCTURE_UNAVAILABLE`. But `evaluate` inside
`difference` (E6) raises `StructureError` on a malformed leaf map, and the spec does not cover that.
*Default:* a `StructureError` in E6 also refuses `STRUCTURE_UNAVAILABLE` (exit 3), and nothing is written. Test 5 has one
case.

## Pre-flight as run here

Code and study file read only. No 6c code exists yet, so no test was run. `study.json` sha256 matched the spec, and the
file's types and months are those listed in I8 and the header above.

## Answers (Architect)

Architect (Claude), 2026-11-22. Spec moves to rev 2 with every answer below. New rulings D-P6.20 to D-P6.29
(`specs/6-decision-valued/rulings.md`).

- **R1. Accepted (D-P6.26).** 6c ships as specified; the packet's residual risk names the gap. 0K4f's acceptance
  gains: the writer derives `frame` from the replay's input (the Site's stored readings, by tenant and Site), never
  from a flag, and never writes 0K4d's `StudyFrame` under that key; the study records `site_readings_digest`, which a
  later check compares. §8 cites this. Recorded for 0K4f's spec (not yet written).
- **R2. Accepted.** The literals are in §5 as written. F1h: confirmed, `diesel_price` is read, because `val1(b)` is
  folded even when `d(a)` is MISSING (§2 now says so), so `assumed` is ["diesel_price"] and `evidence_class` MODELLED.
  K1 lists every row.
- **R3. Accepted, rule written out (D-P6.25).** RECORDED means "no simulated or emulated input": `unknown` and the
  record origins read RECORDED, and the label speaks for simulation and emulation only; the evidence class (DECLARED,
  ESTIMATED, MODELLED ...) carries the rest. Making `unknown` the weakest class would label every priced Site
  SIMULATED, which is false the other way. Plant added (C1 with a `source-emulated` base leaf gives EMULATED).
- **R4. Accepted (D-P6.28).** 6c amends 6a's test 9 to the allowlist as written; 6c's test 9 adds the `sys.modules`
  check.
- **R5. Accepted.** The gate reads `git grep -n "def add_run" main -- backend/assetops_backend/decisions/` showing the
  Protocol's and the adapter's lines.
- **R6. Accepted.** Top-level keys in that order; `frame` `{"kind", "tenant", "site_code"}`; `admitted` null for
  `no-action`.
- **I1. Accepted, High (D-P6.21).** `setting_changes(..., *, grid_changes=SETTING_GRID_CHANGES)` and
  `EvaluationService(..., grid_changes=SETTING_GRID_CHANGES)`; the start-up assertion runs over every entry passed in.
- **I2. Accepted, High (D-P6.20).** 6a adds `site_by_id` (6a I1). If 6a merges without it, 6c adds it in commit 3 and
  names 6a's files.
- **I3. Accepted, High (D-P6.22).** The scan covers `decisions/study_input.py`, `models.py`, `evaluate.py`, `run.py` and
  `structure/difference.py`. `runs/admission.py` gains `DAWN_LIMIT_PCT = Fraction(35)` as `admit`'s default; 6c imports
  it for `margin_points`. Guide check 9 amended.
- **I4. Accepted (D-P6.27).** Fractions `"n/d"` in lowest terms, integers as numbers; K1's literals as written.
- **I5. Accepted (D-P6.29).** A zero change with no currency takes the one-off's; no `ONE_OFF_CURRENCY`. Fixture F1j.
- **I6. Accepted.** E3's order as written, all before E4; test 5 asserts no structure read on each E3 refusal.
- **I7. Accepted.** `read_study` returns the header identity plus `frame`; `run.py` adds `ignored_cases` and
  `months_averaged`.
- **I8. Accepted.** One key-to-type table in §3.1; F1's digests as written.
- **I9. Accepted,** each default as written.
- **I10. Accepted.** `MissingInput("CURRENCY_MISMATCH", "STRUCTURE", None)`; `assumed` lists TARGET and ASSUMPTION.
- **I11. Accepted.** A `StructureError` in E6 refuses `STRUCTURE_UNAVAILABLE` (exit 3), nothing written; test 5 has it.

Size: 6c stays 3.0 u. The answers are clarifications and literals; `DAWN_LIMIT_PCT` and the injection are a few lines.
