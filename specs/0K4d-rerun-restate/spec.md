# 0K4d: the admission rule, the rerun on v8 and season v2, and the restated MG-T lines (implementer spec)

Status: live, rev 1 (Architect, Claude, 2026-11-21); handshake next. **1.5 units.** Discovery review (W5): the
figures that will reach the option card and its money. Non-screen. No migration. No database.
`USER_REVIEW_REQUIRED: true` (the figures go to the owner; nothing served). Rulings: `specs/0K4-dispatch-model-review/
rulings.md` (D-0K4.7, D-0K4.9, D-0K4.11, D-0K4.12, D-0K4.16). Reviewer guide: `reviewer-guide.md`.

- **What it is.** Three things. (1) The owner's admission rule as code that `6c` imports, with the four replay measures
  it reads added to 0K2's `CaseOutcome`. (2) The Kobo study (0K2's grid) and the Mto study (0M's cases) rerun on
  `mini-grid` v8 and season v2, with each case's admission and the assumptions it rests on. (3) The pack's MG-T lines
  in `domain-and-decision-models.md` §4.2 restated to one figure per quantity.
- **Why next.** Review §6 step 4 and the owner's rule: the stop-70 figure may stand only from the corrected model.
  Lane 1, after 0K4a; unit 1 needs only `main` and starts while 0K4c builds (D-0K4.1).
- **Builds on:** `backend/assetops_backend/runs/replay_study.py` (§2.1 types, §2.4 outcomes; 0K2 spec), `runs/
  headroom_replay.py` (0M), `tools/kobo_replay_study.py`, `tools/mto_headroom_study.py`, `host/tests/kobo_season.py`
  (season v2, 0K4c), `host/tests/mto.py`, `host/tests/kobo_assumed.py` (0K4b), `mini-grid` v8 (0K4a).

## 0. Before you start

- Branch `task/0K4d-rerun` off `main`; worktree `/opt/assetecon/AssetOpsV1-0k4d`. Unit 1 on `main` as it is; merge
  `main` before unit 2 once 0K4a and 0K4c are on it.
- **Pre-flight print (packet, first section):** `--time-one` of both tools on v8 and season v2 (site run and one
  replay, seconds each), and the caps they give by 0K2's rule (`max(25, ceil(2 x (site + 15 x replay) / 60))` minutes;
  for Mto `site + 6 x replay`).
- **Files.** New: `backend/assetops_backend/runs/admission.py`, `backend/tests/test_0k4d_admission.py`,
  `host/tests/test_0k4d_v8_study.py`. Edited: `runs/replay_study.py` (four `CaseOutcome` fields, `StudyFrame` and
  `StudyResult` `assumptions`, §2.2), `tools/kobo_replay_study.py` and `tools/mto_headroom_study.py` (the flags of §2.4),
  `host/tests/mto.py` (`mto_site_v2`), `backend/tests/test_0k1_replay_port_seam.py` (allow-list gains `runs/
  admission.py` and its test, if the seam test names them), `Docs/demo-sprint/product-direction-layer4/
  domain-and-decision-models.md` (§4.2 lines 400-415 only, §2.5). Nothing under `simulator/`, `config/` or guards.
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
`full_charge_dates: tuple[str, ...]`, `longest_days_without_full_charge: int`, computed in §2.4 of 0K2's spec from the
projection's steps exactly as D-0K4.16 defines (local dates in the frame's zone; a step's start counts in the local
date of its start; the end SOC counts in the window's last local date). `StudyFrame` gains `assumptions: tuple[str, ...]
= ()`; `StudyResult` gains `assumptions: tuple[str, ...]`, copied from the frame. The `dawn_verdict` field stays, and
its docstring says it is information (D-0K4.9). No other change; B1-B13 of 0K2 still pass.

### 2.3 The Mto site on v8 (`host/tests/mto.py`)

`MTO_ASSUMED = (("generator-no-load-fuel-rate", 2.4, "L/h"), ...)`: Mto's 30 kW generator at the same generic rule as
Kobo's (0.08 L/h per kW of rating, to one decimal: 2.4 L/h), minimum load 30 %, taper 95 %, each basis
`GENERIC_DEFAULT`; `mto_site_v2(limit)` = `mto_site(limit)` then these rows appended (as `assumed_site` does, with Mto's
no-load value). `mto_base_run(days, *, inverter_limit_kw=..., version=7, site=mto_site)`; v2 calls pass `version=8,
site=mto_site_v2` and `mto_season(run, days, season="v2")`.

### 2.4 The tools

Both tools gain `--model-version {7,8}` (default 7) and `--season {v1,v2}` (default v1), so the 0K2 and 0M runs stay
reproducible by their recorded commands. On `--model-version 8` the tool reads the five assumed rows from the run's
Foundation document and passes them as `StudyFrame(assumptions=...)` in the form `"<key> <value> <unit>
(<basis>)"`; the JSON header and every printed line carry `input_class=SIMULATED evidence_class=MODELLED
model=mini-grid/8 season=v2`. The Kobo tool calls `admit(result.baseline, case)` for each case and writes, per case,
the four parts, `admitted`, and the dawn information; it prints one line per case: case id, avoided litres by month,
`admitted yes|no`, and the first failing part. The Mto tool writes 0M's outcomes unchanged in shape. No design value
is read, printed or written by either tool (D-0K4.11).

### 2.5 The MG-T lines (`domain-and-decision-models.md` §4.2, lines 400-415)

- The table at lines 403-404: the stop-70 and reserve-25 rows carry the v8 study's figures (avoided litres a month as
  the mean of September and October scaled to 30 days, added battery throughput a month, starts, dawn margin) each
  marked SIMULATED, with "admitted" or "not admitted (<first failing part>)" from §2.1 in place of "dawn PASS" and
  "dawn adequacy FAIL (hard)". The value column for stop 70 reads "Not available yet (`6c` values it)" because money is
  `6c`'s (D-0K2.12). "0 of 61" and "dawn PASS" are removed.
- Line 410 ("Design values as calibration-spike inputs"): rewritten to say the five inputs are the v8 studies'
  figures, SIMULATED, with the assumptions of D-0K4.7, except KIS-BATT60's 150 L, which reads "Not available yet" until
  a Kisiwa battery replay exists (D-0K4.12).
- Line 415, the vectors: MG-T1 and MG-T2 restated with the study's figures and the admission result; MG-T3's
  sensitivities "Not available yet (`6c`)"; MG-T4 unchanged.
- The `<!--fig:...-->` anchors on removed figures are removed with them; the manifest and `derived-values.json` are
  0K4m's (D-0K4.15), so `check_manifest.py` may report the pack's derived figures as stale: record its output in the
  packet, do not edit the manifest here.

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
- **V1 calibrated:** `replay_study` on the v2 site run and its observed series is CALIBRATED with `min_litre_days=8`,
  and the baseline replay follows the site within 0K2's T11 bounds (its reader reused by copy in the test, not import).
- **V2 measures equal the reader's:** for grid `(S(90, 30), S(70, 30), S(90, 25))` every `CaseOutcome` field,
  including the four new ones, equals the test's own reader of the projections.
- **V3 the old fault is gone:** on every RUNNING step of the baseline projection whose demand is at most PV plus 40 kW,
  the SOC at the next step is not below this step's (the reader's), unless it is 100.
- **V4 assumptions:** `result.assumptions` equals the five strings of D-0K4.7 for the v2 Foundation.
- **V5 the tools are reproducible:** `--model-version 7 --season v1 --days 8` of the Kobo tool gives the same per-case
  litres as `main`'s tool on 8 days (the 0K2 path is unchanged).

**The 61-day runs** (unit 2): Kobo, 1 site run and 15 replays; Mto, 0M's set on v8 and v2. Outputs:
`study.json` per tool, the per-case lines, the per-dawn table of D-0K2.17 (date, SOC, state, cause class), and the
admission table.

**Regression:** `backend/tests/test_0k2_replay_study.py`, `test_0k1_replay_port_seam.py`, `host/tests/
test_0k2_kobo_season.py`, `test_0m_mto_headroom.py`, check-all (fast) once, `python tools/select-tests.py --base main`.

## 4. Units

| Commit | Content |
|---|---|
| 1 (0.75) | §2.1, §2.2, AD1-AD8, the seam-test edit (on `main`) |
| 2 (0.5) | §2.3, §2.4, V1-V5, the two 61-day runs (after 0K4a and 0K4c merge) |
| 3 (0.25) | §2.5, regression, packet |

Packet `specs/0K4d-rerun-restate/packet.md` (D-0K4.11's form): the pre-flight timings and caps; per Kobo case, the
figures in one column headed "season v2 on mini-grid v8 (SIMULATED, MODELLED; assumptions: ...)" with the admission
result and the dawn information beside it; per Mto case, 0M's figures in the same form; a separate reconciliation
table "what moved from the v7 study and why" (v7 study, v8 study, the cause: dispatch, fuel curve, taper or season),
both columns model figures; the `check_manifest.py` output; run count, wall time, mid-build count. No design value
appears except in that reconciliation table's cause text, if at all.

## 5. Done (questions; each can fail)

1. Is the admission rule exactly D-0K4.9 (four parts, the absolute-then-relative fallback, the dawn never deciding),
   proven on stubs?
2. Do the four new measures equal an independent reader's on the kernel, with B1-B13 of 0K2 still green?
3. Is the v8 baseline calibrated (adapter fidelity) and free of the battery-beside-generator fault?
4. Does every result, line and JSON carry SIMULATED, MODELLED, the model and season, and the assumptions?
5. Do the MG-T lines carry one figure per quantity, with "0 of 61" and "dawn PASS" gone and money left to `6c`?
6. Are the 0K2 and 0M commands still reproducible on v7 and v1?
7. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 6. Out of scope

Money and the 12-month value (`6c`); the manifest, derived values and the vNEXT mock (0K4m); the product fuel law and
any world on v8 (0K4f); Kisiwa's battery replay; any screen or served text.
