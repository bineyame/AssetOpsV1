# 6c review packet: options valued against doing nothing

Branch `task/6c-option-evaluator` (worktree `/opt/assetecon/AssetOpsV1-6c`), on `main` at 57cecf954. Commits:
bced7b260 (1: difference), 4bb16168a (2: study, admission, models, evaluator), c380b1faf (3: command, run, Postgres),
plus the bookkeeping commit. Implementer: Claude (assetops-implementer). `USER_REVIEW_REQUIRED: true` (spec header).

## Outcome

`python -m assetops_backend.evaluate_options --tenant SLUG --as EMAIL --decision UUID [--study PATH]` values every
option of a 6a decision against no action through the structure's `contribution` and writes one 6a run. With a
Site-record study it ranks (F1b: `stop-70-reserve-30` RECOMMENDED, the nearest within 10 % of the best); with a
declared season (every study today, Kobo's `kobo-61d` included) every value names `SITE_MONTH_SIMULATION` and the run
is `RANKING_INCOMPLETE`, admission and dawn stored (D-P6.2; owner Q1: Kobo "Not available yet" until 0K4f).

## Pre-flight (spec §0), confirmed from `main`

1. `evaluate._check_leaf` has no sign check; `difference` passes deltas only to its own fold, `evaluate` gets the base.
2. The 0K4d study's case keys hold every §3.1 key, `*_by_month` entries with `days` (read in K1).
3. All three registries have `contribution`. Gates: 6a's `site_by_id` and `add_run` present (Protocol, memory,
   adapter); gate K met.

## Files

New: `backend/assetops_backend/structure/difference.py`, `decisions/study_input.py`, `decisions/models.py`,
`decisions/evaluate.py`, `decisions/run.py`, `evaluate_options.py`; tests `test_6c_difference.py`,
`test_6c_evaluate.py`, `test_6c_run.py`, `test_6c_run_postgres.py`, `option_fixtures.py`; fixtures
`tests/fixtures/decisions/study-f1.json`, `study-f1h.json`, `study-f1g.json`, `kobo-61d-study.json` (+ `.md`
provenance: source path and sha256 `c52e4755...`).
Changed: `runs/admission.py` (`AdmissionMeasures`, `judge`, `DAWN_LIMIT_PCT`; `admit` delegates, behaviour unchanged);
6a's `decisions/records.py` (`COMMANDS["evaluate"]`, the 10 codes in `REFUSAL_EXIT`, C1-C3 lifted into
`admit_person` which `DecisionService._admit` calls), `decisions/cli.py` (`run(..., build=)`),
`decisions/composition.py` + `decisions_composition.py` (`build_evaluation`), `accounts/permissions.py`
(`decision.evaluate`: ANALYST), statement `decision.refused` (+10 variants, spec §4 sentences); tests amended:
6a's test 9 (D-P6.28 allowlist) and statements test (6c codes in 6c's test 7), `test_3c1a_person_work.py` role table,
`statement_cases/decision.py`.

## Done (spec §7)

1. Value = difference of `contribution`, option minus no action on the same leaves, × horizon − one-off: test 4
   F1b/C1/E1 literals; no stated map reaches `evaluate` (D-P6.4). Yes.
2. Missing named, never zero; unchanged factor exactly 0: F1a (`wear_rate` named, `stop-90-reserve-25` valued because
   its throughput change is exactly 0 by the product rule, not a special case), C1b, F1h. Yes.
3. Not admitted: REJECTED `NOT_ADMITTED_<PART>`, value stored, never ranked (F1b, F1e). Yes.
4. Near set + distance (F1b), `RANKING_INCOMPLETE` withholds ranks (F1a, F1c), `NO_ACTION_BEST` (F1d), tie (F1f),
   `AT_GRID_EDGE` (F1g only). Yes.
5. Source class from origins used (F1 SIMULATED, C1/E1 RECORDED, C1e EMULATED); `assumed` lists `diesel_price`. Yes.
6. Cold room and EV through the same code; test 8 scans `evaluate.py`/`difference.py` for every structure key and
   factor id. Yes.
7. sha256 and identity stored (test 5 literal, incl. `ignored_cases`, `months_averaged`); admission recomputed on
   every case and refused on mismatch. Yes.
8. Declared season values nothing (F1h, K1); Site record = mean of full months, no scaling (F1i: −150); another
   Site or a partial month refused (test 5). Yes.

## Checks (actual output)

- Focused + adjacent: `tools/heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- <13 files>` at c380b1faf:
  `1 failed, 852 passed in 148.38s`. The failure is `test_3b3_structure_evaluate.py::test_t6_each_state...`
  (`candidate_l` kind `dispatch-3.3` vs the pack manifest's `dispatch-3.2`), pre-existing on `main` (6a's state entry
  lists "Pre-existing: 3B3 t6"); 6c touches neither file. Files: test_6c_* (4), test_6a_decisions, test_6a_commands,
  test_6a_decisions_postgres, test_6a_migration_postgres, test_0k4d_admission, host/tests/test_0k4d_v8_study,
  test_3c1a_person_work, test_sc1_statements, test_3b3_structure_evaluate. 0K4d's two files pass unchanged.
- 6c alone: difference 15, evaluate 42, run 20, run_postgres 2: all pass.
- Plants (§6), each in the tree then `git checkout`, script `scratchpad/6c/plants.py`; all 14 caught:
  missing wear as 0 (F1a), rank a REJECTED (F1b), drop near set (F1b), zero as candidate (F1f), read declared
  season months (F1h), stated into the difference (signature test), dawn as gate (F1b), d(a)×val0(b) (product test),
  skip admission recomputation (test 5 E3), `unknown` weakest (C1), ignore `source-emulated` (C1e), `"MINI_GRID"` in
  `evaluate.py` (test 8), window × 30 / days (F1i), K1's `2026-10` entry (K1).
- Guards: see "Guards" below.

## Guards

GUARDS_PLACEHOLDER

Layout evidence: not run (no screen; non-UI slice).

## Known deviations and mid-build questions (defaults applied)

1. **Effect currency on an exactly-zero money effect.** §2 defines a Delta's currency as that of the money values
   used. `battery_wear` with a zero throughput change (F1b `stop-90-reserve-25`) and with a missing wear rate (F1a)
   reads no money value, so its effect currency is null, while §5 F1b says "money effects carry USD". Default: §2's
   rule (null). The option's currency is unaffected (it reads `diesel_price`).
2. **`assumed` on F1j's zero row is `[]`.** Nothing changed, so no price is read; §5 says "every other row as F1b".
3. **`assumed` lists used leaves only** (§3.4 step 3, literal). A used node's own assumed leaves are not added; no
   fixture reads a node's no-action value. Question: should they be (a node resting on an ASSUMPTION)?
4. **Names for missing values outside §3.4's cases:** a zero denominator met by the fold names the node,
   `MissingInput("ZERO_DENOMINATOR", "STRUCTURE", node)`; `ONE_OFF_CURRENCY` is not added when the option has no
   currency (its change is missing). No fixture reaches either.
5. **E2** refuses `STUDY_REQUIRED` whenever no study is given (SETTING_GRID is the only generator); a lever unknown
   at evaluation refuses `LEVER_UNKNOWN` (6a's code).
6. **Months check placement:** "every case has the baseline's full months" (STUDY_UNREADABLE) runs inside E3 after
   the frame check, before `STUDY_MONTH_NOT_COVERED`.
7. **6a files touched** (named above): `admit_person` lifted from `DecisionService._admit` (same behaviour);
   `cli.run` gains `build`. `read_study` raises its own `StudyRefused(code)` (0K4d's has a closed code set).

## Residual risk

- D-P6.26: 6c trusts a study's `frame` header. A stamped header on a season file would value Kobo's October; 0K4f's
  acceptance must derive `frame` from the Site's stored readings and record `site_readings_digest`.
- `build_evaluation` (the real composition, structure read over Postgres) is not exercised end to end by a test; the
  command is tested with injected services, the store through the adapter (test 6).

## Review focus

`structure/difference.py` against §2 operator by operator (used/evidence for changed leaves: LeafChange plus the base
value when read); `decisions/evaluate.py` R0-R4 and the run outcome; deviations 1-4.
