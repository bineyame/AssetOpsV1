# 0K4d: the admission rule, the rerun on v8 and season v2, and the restated MG-T lines (implementer spec)

Status: in_review, rev 2 (Architect, Claude, 2026-11-21; handshake answered by D-0K4.26 to D-0K4.30). **2.25 units.** Discovery review (W5): the
figures that will reach the option card and its money. Non-screen. No migration. No database.
`USER_REVIEW_REQUIRED: true` (the figures go to the owner; nothing served). Rulings: `specs/0K4-dispatch-model-review/
rulings.md` (D-0K4.7, D-0K4.9, D-0K4.11, D-0K4.12, D-0K4.16, D-0K4.26 to D-0K4.29). Reviewer guide: `reviewer-guide.md`.

- **What it is.** Three things. (1) The owner's admission rule as code that `6c` imports, with the four replay measures
  it reads added to 0K2's `CaseOutcome`. (2) The Kobo study (0K2's grid) and the Mto study (0M's cases) rerun on
  `mini-grid` v8 and season v2, with each case's admission and the assumptions it rests on. (3) The pack's MG-T lines
  in `domain-and-decision-models.md` §4.2 restated to one figure per quantity.
- **Why next.** Review §6 step 4 and the owner's rule: the stop-70 figure may stand only from the corrected model.
  Lane 1 (D-0K4.30): commit 1 needs only `main` and can start now; commits 2-3 follow 0K4a's commit 3, once 0K4a
  and 0K4c are both on `main`.
- **Builds on:** `backend/assetops_backend/runs/replay_study.py` (§2.1 types, §2.4 outcomes; 0K2 spec), `runs/
  headroom_replay.py` (0M), `tools/kobo_replay_study.py`, `tools/mto_headroom_study.py`, `host/tests/kobo_season.py`
  (season v2, 0K4c), `host/tests/mto.py`, `host/tests/kobo_assumed.py` (0K4b), `mini-grid` v8 (0K4a).

## 0. Before you start

- Branch `task/0K4d-rerun` off `main`; worktree `/opt/assetecon/AssetOpsV1-0k4d`. Unit 1 on `main` as it is; merge
  `main` before unit 2 once 0K4a and 0K4c are on it.
- **Commit 1** has no pre-flight beyond B1-B13 of 0K2 green on `main` (D-0K4.28).
- **Pre-flight print (packet, first section; opens commit 2, after merging `main`):**
  1. before either tool is edited, `main`'s `tools/kobo_replay_study.py --days 8` with no model or season flag; each
     case's `avoided_l`, exact, recorded as V5's literals;
  2. `--time-one` of both tools on v8 and season v2 (site run and one replay, seconds each; the Mto tool gains
     `--time-one` in D-0K2.24's form in this commit);
  3. the caps: Kobo `max(25, ceil(2 x (site + 15 x replay) / 60))` minutes, Mto `max(25, ceil(2 x (site + 6 x replay) / 60))`.
- **Files.** New: `backend/assetops_backend/runs/admission.py`, `backend/tests/test_0k4d_admission.py`,
  `host/tests/test_0k4d_v8_study.py`. Edited: `runs/replay_study.py` (four `CaseOutcome` fields, `StudyFrame` and
  `StudyResult` `assumptions`, §2.2), `tools/kobo_replay_study.py` and `tools/mto_headroom_study.py` (the flags of §2.4),
  `host/tests/mto.py` (`mto_site_v2`, `MTO_ASSUMED_DERIVATION`, the `version`/`site`/`season` arguments),
  `host/tests/kobo_assumed.py` (`ASSUMED_DERIVATION` only, D-0K4.27), `backend/tests/test_0k1_replay_port_seam.py` (allow-list gains `runs/
  admission.py` and its test, if the seam test names them), `Docs/demo-sprint/product-direction-layer4/
  domain-and-decision-models.md` (§4.2's Kobo option text only, anchored by text, §2.5). Nothing under `simulator/`, `config/` or guards.
- **Heavy tools** through the slot pool; the 61-day runs with `--label 0K4d-kobo` and `--label 0K4d-mto`, one at a
  time, after `--time-one`. Evidence to `/opt/assetecon/evidence/0K4d/<run>/`. Never ports 5490 or 8990.

## 1. Outcome and gate questions

For each setting of the Kobo grid on v8 and season v2, are the litres avoided by month, starts, unserved energy,
reserve breaches, most starts in a day, days without a full charge and the dawn readings each equal to an independent
reader's, and is each case admitted or not by the four-part rule alone, with the dawn margin shown and never deciding?
Does every result name the assumptions it rests on? Do the Mto figures (huller, welder, reduced inverter) come from
the same model and season? Do the MG-T lines carry one figure per quantity, labelled SIMULATED, with no design value
beside them?

## 2. Design

### 2.1 `backend/assetops_backend/runs/admission.py` (pure; imports `__future__`, `dataclasses`, `fractions`, `runs.replay_study`)

```python
ADMISSION_PARTS = ("energy_not_served", "reserve_breaches", "starts", "full_charge")     # this order
JUDGED = frozenset({"RELATIVE", "ABSOLUTE", "RELATIVE_BASELINE_FAILS"})

@dataclass(frozen=True)
class AdmissionRule:
    max_starts_per_day: int = 6                 # the maker's limit; GENERIC_DEFAULT until Kobo's generator sheet
    full_charge_every_days: int = 7             # LFP; GENERIC_DEFAULT until Kobo's battery sheet
    basis: str = "GENERIC_DEFAULT"
@dataclass(frozen=True)
class AdmissionPart:
    name: str; case_value: Fraction; baseline_value: Fraction; limit: Fraction | None; judged: str; passed: bool
@dataclass(frozen=True)
class DawnInformation:                          # information, never a gate (D-0K4.9)
    worst_soc_pct: Fraction; margin_points: Fraction; days_below: int; dates_below: tuple[str, ...]
@dataclass(frozen=True)
class Admission:
    case_id: str; admitted: bool; parts: tuple[AdmissionPart, ...]; dawn: DawnInformation
    rule: AdmissionRule; input_class: str; evidence_class: str = "MODELLED"

def admit(baseline: CaseOutcome, case: CaseOutcome, rule: AdmissionRule = AdmissionRule(),
          dawn_limit_pct: Fraction = Fraction(35)) -> Admission
```

Parts, in `ADMISSION_PARTS` order:
1. `energy_not_served`: values `unserved_kwh`; `RELATIVE`, limit `None`; passes when case <= baseline.
2. `reserve_breaches`: values `reserve_breach_steps`; `RELATIVE`; passes when case <= baseline.
3. `starts`: values `max_starts_in_a_day`; limit `rule.max_starts_per_day`; `ABSOLUTE` and passes when case <= limit,
   unless baseline > limit: then `RELATIVE_BASELINE_FAILS`, passes when case <= baseline.
4. `full_charge`: values `longest_days_without_full_charge`; limit `rule.full_charge_every_days - 1`; the same
   absolute-then-relative rule.
`admitted` is the conjunction of the four. `dawn` from `case.dawn` (worst reading, `worst - dawn_limit_pct`, count and
dates below). `admit(baseline, baseline)` is always admitted: the relative parts are equal, and an absolute part the baseline fails
falls back to `RELATIVE_BASELINE_FAILS` against itself (no action is never rejected). `input_class` is copied from the case; mismatched `input_class` between the two is `ValueError`.

### 2.2 `runs/replay_study.py` additions (D-0K4.16)

`CaseOutcome` gains, after `clipped_steps`: `reserve_breach_steps: int`, `max_starts_in_a_day: int`,
`full_charge_dates: tuple[str, ...]`, `longest_days_without_full_charge: int`, computed from the projection's steps
exactly as D-0K4.16 defines (as corrected by D-0K4.28: a start is STOPPED to STARTING/RUNNING only, by
`start_steps(states, start.generator_state)` unchanged, grouped by each step's local start date) (local dates in the frame's zone; a step's start counts in the local
date of its start; the end SOC counts in the window's last local date). `StudyFrame` gains `assumptions: tuple[str, ...]
= ()`; `StudyResult` gains `assumptions: tuple[str, ...]`, copied from the frame. The `dawn_verdict` field stays, and
its docstring says it is information (D-0K4.9). The four are computed by one public pure helper, added to `__all__`:

```python
def admission_measures(p: ReplayProjection, local_times: tuple[datetime, ...], first_previous: str
                       ) -> tuple[int, int, tuple[str, ...], int]:
    # (reserve_breach_steps, max_starts_in_a_day, full_charge_dates, longest_days_without_full_charge);
    # reserve_breach_steps reads p.reserve_soc_pct (the case's own reserve)
```

`_outcome` calls it. Every exception raised by the additions and by `admission.py` is built-in (`ValueError`,
`TypeError`) and holds codes, never English (D-0K4.28, SC-1). No other change; B1-B13 of 0K2 still pass.

### 2.3 The Mto site on v8 (`host/tests/mto.py`)

`MTO_ASSUMED = (("generator-no-load-fuel-rate", 2.4, "L/h"), ...)`: Mto's 30 kW generator at the generic rule of
0.08 L/h per kW of rating (2.4 L/h; not scaled from Kobo's 3.3, which is the owner's value for one set, D-0K4.27),
minimum load 30 %, taper 95 %, each basis `GENERIC_DEFAULT`; `MTO_ASSUMED_DERIVATION` holds each key's derivation
line exactly as D-0K4.27 words it (SFC 0.33 `declared, MANIFEST`); `mto_site_v2(limit)` = `mto_site(limit)` then these rows appended (as `assumed_site` does, with Mto's
no-load value). `mto_base_run(days, *, inverter_limit_kw=MTO_INVERTER_KW, version=7, site=mto_site)` and
`mto_season(run, days, season="v1")`; v2 calls pass `version=8, site=mto_site_v2` and `season="v2"`, the reduced
(25 kW) run included.

### 2.4 The tools

Both tools gain `--model-version {7,8}` (default 7) and `--season {v1,v2}` (default v1), so the 0K2 and 0M runs stay
reproducible by their recorded commands. Only (7, v1) and (8, v2) run; a mixed pair exits 2 with
`STUDY_FLAGS_INVALID model=<v> season=<s>` on stderr. `dawn_class` takes the season's overcast function.

On `--model-version 8` each tool composes the four assumption strings of D-0K4.27, in its order, through one helper
per tool (which V4 calls): value and unit from the run's frozen `model_needs` (authored form), label, basis and
derivation from `ASSUMED_DERIVATION` (Kobo) or `MTO_ASSUMED_DERIVATION` (Mto); a missing entry is `KeyError`. They go
in as `StudyFrame(assumptions=...)` and in the Mto JSON header (`HeadroomResult` unchanged). The Kobo JSON header also
carries `admission_rule`, the two limit strings of D-0K4.27 (the words live in the tool).

Every JSON header holds (D-0K4.28) `commit` (`git rev-parse HEAD`), `model` (`mini-grid/<v>`), `season`,
`season_inputs_digest` (`kobo_season.inputs_digest`), and each site run's `trajectory_digest` (0K4a's
`host/tests/trajectory_digest.py`), plus `input_class=SIMULATED evidence_class=MODELLED`. Every printed line starts
with `input_class=SIMULATED evidence_class=MODELLED model=mini-grid/<v> season=<s>`; on (7, v1) that adds labels and
changes no figure. The Kobo tool calls `admit(result.baseline, case)` for each case and writes, per case,
the four parts, `admitted`, and the dawn information; it prints one line per case: case id, avoided litres by month,
`admitted yes|no`, and the first failing part. A study that is not CALIBRATED prints `admission not available (<status>)` and writes no
admission. The Mto tool writes 0M's outcomes unchanged in shape. No design value
is read, printed or written by either tool (D-0K4.11).

### 2.5 The MG-T lines (`domain-and-decision-models.md` §4.2, the Kobo option text from the `F(π)` block to the vectors line; anchored by text)

D-0K4.29 governs, place by place; this is its build form. After the edit, every numeral in that text is one of four
kinds: (1) a declared setting or record fact; (2) a v8 study figure, SIMULATED, by the definitions below;
(3) "Not available yet (<record or unit>)"; (4) a rule in `runs/admission.py`, or information beside it. The packet
lists every numeral with its kind.

Figure definitions (D-0K4.28): a month is `scaled_to_30_days` (window x 30 / 61); starts is `added_starts` scaled the
same way, with `max_starts_in_a_day` in the admission cell; stop 70 is `stop-70-reserve-30`, reserve 25 is
`stop-90-reserve-25`; dawn margin is `worst - 35`; lowest charge is the case's `min_soc_pct`; the huller is
`mto-huller` `extra_fuel_l` x 30 / 61; the reduced inverter is `extra_fuel_l_per_day`.

- `dawn_ok(π) ... → bound` becomes `admitted(π) = admit(baseline, π)  → runs/admission.py (four parts)` and
  `dawn(π) = min_d SOC_π(d, 05:00) − 35 → information, never a bound`.
- "Design values:" before the table becomes "Figures from the v8 study (SIMULATED, MODELLED; assumptions as listed
  in the study):". The two setting rows carry the study's litres a month, dawn information, added throughput a month
  and starts. "Bound result" holds "admitted" or "not admitted (<first failing part>)"; the dawn column is headed
  "Dawn (information)"; both Value cells read "Not available yet (`6c` values it)" ("REJECTED", "0 of 61", "dawn PASS"
  and "dawn adequacy FAIL (hard)" go).
- Stop 70's cell loses "of the 330 candidate L (120 L of candidate running remain needed)"; a line under the table
  reads "Kobo's candidate running litres: Not available yet (dispatch-3.3 on Kobo's October telemetry; 0K4e, 4d)".
  The Calibration paragraph's "The 120 L residual" becomes "The residual (candidate litres no setting avoids)".
- "lowest charge 30% ≥ warranty floor 10%" becomes the lowest charge, SIMULATED, with "warranty floor: Not available
  yet (Kobo's battery sheet)" as information; "wear costed 12.00" and `(262.50 − 12.00) × 12 − 90.00 = 2,916.00` go.
- The selection sentence becomes "`6c` chooses among the settings `runs/admission.py` admits; the dawn margin is shown
  and never gates"; the 10 % tie rule stays, as `6c`'s.
- "Design values as calibration-spike inputs" becomes four of the five inputs as the v8 studies' figures (stop 70, reserve 25,
  huller, reduced inverter; SIMULATED, with D-0K4.27's assumptions); KIS-BATT60's 150 L and 195.00 read "Not available
  yet (a Kisiwa battery replay; queue Q7)".
- "Minimum sample: 61 days for the dawn bound (…)" becomes "the dawn information is read over the study's 61 days;
  ≥ 14 days for the litres".
- "Sensitivity / break-even" (2,286.00, 2,166.00, 15.6 L/month, 1.70/kWh) reads "Not available yet (`6c`)".
- Vectors: MG-T1 and MG-T2 carry the study's litres, the admission result and the dawn information; MG-T2's value
  "Not available yet (`6c`)"; MG-T3 "Not available yet (`6c`)"; MG-T4 unchanged.
- The `<!--fig:...-->` anchors on removed figures are removed with them; the manifest and `derived-values.json` are
  0K4m's (D-0K4.15), so `check_manifest.py` may report the pack's derived figures as stale: record its output in the
  packet, do not edit the manifest here.
- If the Kobo study is not CALIBRATED, the MG-T cells read "Not available yet (replay not calibrated)" (D-0K4.28).

## 3. Tests (written first)

`backend/tests/test_0k4d_admission.py` (no kernel; stub `CaseOutcome`s built in the test):
- **AD1** each part passes and fails on its own, the others held passing; `admitted` is the conjunction.
- **AD2** starts: baseline 4, case 6 passes `ABSOLUTE`; case 7 fails; baseline 8, case 7 passes
  `RELATIVE_BASELINE_FAILS`, case 9 fails.
- **AD3** full charge: limit 6 days; case 6 passes, 7 fails; baseline 9 and case 8 passes `RELATIVE_BASELINE_FAILS`.
- **AD4** the dawn never decides: a case with 20 dawn days below and every part passing is admitted; a case with 0
  dawn days below and one failing part is not; `margin_points == worst - 35`.
- **AD5** `admit(b, b)` is admitted for a baseline that fails the starts limit.
- **AD6** mismatched `input_class` raises; `Admission.evidence_class == "MODELLED"`.
- **AD7** the four `CaseOutcome` measures on a stub projection (2 local days, Addis Ababa): a step below its case's
  reserve counted; two starts on day 1 and one on day 2 give 2; SOC 100 at one step of day 1 only and the end SOC 100
  give dates `(day 1, day 2)` and longest gap 0; no 100 anywhere gives 2.
- **AD8** imports of `admission.py` are exactly §2.1's set (an `ast` scan); no adopting word (D-0K2.20's scan).

`host/tests/test_0k4d_v8_study.py` (the kernel; an 8-day v2 season on v8; under 3 minutes; cached runs):
- **V0 frozen needs and smoke (only if 0K4c's S7 frozen half and S8 were not built there, D-0K4.26):** a 1-day
  `base_run(1, version=8, site_edit=season_site_v2)` has `frozen_world_inputs(run).initial_values` with
  `model-need:generator-no-load-fuel-rate` = `11/200`, `model-need:generator-minimum-load` = `30`,
  `model-need:battery-charge-taper-start` = `95`; a 2-day v2 season on v8 executes COMPLETED.
- **V1 calibrated:** `replay_study` on the v2 site run and its observed series is CALIBRATED with `min_litre_days=8`,
  and the baseline replay follows the site within 0K2's T11 bounds (its reader reused by copy in the test, not import).
- **V2 measures equal the reader's:** for grid `(S(90, 30), S(70, 30), S(90, 25))` every `CaseOutcome` field,
  including the four new ones, equals the test's own reader of the projections.
- **V3 the old fault is gone:** on every RUNNING step of the baseline projection whose demand is at most PV plus 40 kW,
  the SOC at the next step is not below this step's (the reader's), unless it is 100.
- **V4 assumptions:** through each tool's helper, Kobo's `result.assumptions` equals D-0K4.7/D-0K4.27's four Kobo
  strings, literal, in order, and Mto's equals the four Mto strings; a derivation entry removed gives `KeyError`.
- **V5 the tools are reproducible:** the Kobo tool's `main(["--days", "8", ...output args])`, in-process with no model
  or season flag, gives each case's `avoided_l` equal to the pre-flight literals from `main`'s tool, and its header
  reads `model=mini-grid/7 season=v1`.
- **V6 flags:** `main(["--model-version", "8", "--season", "v1", ...])` and `("7", "v2")` each return 2 with
  `STUDY_FLAGS_INVALID` on stderr, for both tools.

**The 61-day runs** (unit 2): Kobo, 1 site run and 15 replays; Mto, 0M's set on v8 and v2. Outputs:
`study.json` per tool, the per-case lines, the per-dawn table of D-0K2.17 (date, SOC, state, cause class), and the
admission table.

**Regression:** `backend/tests/test_0k2_replay_study.py`, `test_0k1_replay_port_seam.py`, `host/tests/
test_0k2_kobo_season.py`, `test_0m_mto_headroom.py`, check-all (fast) once, `python tools/select-tests.py --base main`.

## 4. Units

| Commit | Content |
|---|---|
| 1 (0.75) | §2.1, §2.2 (with `admission_measures`), AD1-AD8, the seam-test edit (on `main`; can start now) |
| 2 (1.0) | merge `main`, the pre-flight, §2.3, §2.4, V0 (if needed), V1-V6, the two 61-day runs (after 0K4a and 0K4c merge) |
| 3 (0.5) | §2.5 with the numeral list, regression, packet |

Packet `specs/0K4d-rerun-restate/packet.md` (D-0K4.11's form): the pre-flight (V5's literals, timings and caps);
each `study.json`'s identity header (commit, model, season, season digest, trajectory digests); per Kobo case, the
figures in one column headed "season v2 on mini-grid v8 (SIMULATED, MODELLED; assumptions: ...)" with the admission
result and the dawn information beside it; per Mto case, 0M's figures in the same form; a separate reconciliation
table "what moved from the v7 study and why" (v7 study, v8 study, cause), both columns model figures; a v7 cell with no
measure reads "not computed on v7", and the cause reads "model v7 to v8 and season v1 to v2 together (not separated)"
(D-0K4.28); the §2.5 numeral list with each numeral's kind; the statement-catalogue check's output (no
`HAND_BUILT_NEW`; both baseline files untouched); the `check_manifest.py` output; run count, wall time, mid-build count. No design value
appears except in that reconciliation table's cause text, if at all.

## 5. Done (questions; each can fail)

1. Is the admission rule exactly D-0K4.9 (four parts, the absolute-then-relative fallback, the dawn never deciding),
   proven on stubs?
2. Do the four new measures equal an independent reader's on the kernel, with B1-B13 of 0K2 still green?
3. Is the v8 baseline calibrated (adapter fidelity) and free of the battery-beside-generator fault?
4. Does every result, line and JSON carry SIMULATED, MODELLED, the model and season, the identity header, and the
   assumptions, each with its basis and derivation (D-0K4.27)?
5. Is every numeral of the restated §4.2 text one of D-0K4.29's four kinds, with "0 of 61", "dawn PASS" and every
   design value gone and money left to `6c`?
6. Are the 0K2 and 0M commands still reproducible on v7 and v1?
7. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 6. Out of scope

Money and the 12-month value (`6c`); the manifest, derived values and the vNEXT mock (0K4m); the product fuel law and
any world on v8 (0K4f); Kisiwa's battery replay; any screen or served text.
