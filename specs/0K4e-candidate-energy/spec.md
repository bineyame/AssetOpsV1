# 0K4e: `dispatch-3.3`, a battery-support Candidate needs the energy to reach solar cover (implementer spec)

Status: live, rev 1 (Architect, Claude, 2026-11-21); handshake next. **2.0 units.** Discovery review (W5): a change to
a served classification that bounds money (fuel-cost-1) and litres (4d). No migration (a model version is data).
`USER_REVIEW_REQUIRED: true` (served candidate litres and Findings move). Rulings: `specs/0K4-dispatch-model-review/
rulings.md` (D-0K4.10, D-0K4.11). Reviewer guide: `reviewer-guide.md`.

- **What it is.** One new rule in the dispatch analytic. Today a generator-ON point is Candidate when PV plus the
  battery's discharge *power* covers the load with 10 % headroom (`dispatch_v3.py:298-300`). `dispatch-3.3` keeps such
  a point Candidate only if the battery's *energy* above the reserve also covers the load PV does not cover, from that
  point until PV alone covers the load with the same headroom; otherwise the point is Indeterminate, naming why. The
  PV-alone branch (`:294-296`) and every other rule are unchanged.
- **Why next.** The 330 "avoidable" litres behind the pack's 210 L come from the power test (review §3); 0M's review
  found the same same-step reading. One class, fixed once (W6). Lane 3, independent (D-0K4.1).
- **Builds on (`main`, `fa13f254f`):** `backend/assetops_backend/analytics/dispatch_v3.py` (whole: `_Index`
  150-213, `_evaluate` 253-322, `_control_changes` 336-342), `analytics/assessment_inputs.py:183-184`,
  `analytics/adapters/postgres_assessment_store.py:309-340` (`_configuration`), `analytics/claim_limit_read.py:39`,
  `backend/tests/dispatch_3_decision_table.md`, `backend/tests/test_s3_dispatch_v3_analytic.py`.

## 0. Before you start

- Branch `task/0K4e-dispatch-3-3` off `main`; worktree `/opt/assetecon/AssetOpsV1-0k4e`.
- **Pre-flight (packet, first section):**
  1. the W6 sweep: `git grep -n "dispatch-3\.2"` over `backend/`, `frontend/src/` and `tools/`, each hit classed as
     *pins a version* (must accept 3.3), *names the current rule in prose* (docstring: update), or *history* (leave);
  2. how `finding_service.py`, `structure/litres/inputs.py` and `financials/fuel_cost.py` select dispatch runs (by
     `MODEL_VERSION`, by the default selection, or by a literal), quoted with `path:line`;
  3. on a scratch `*_test` database with the DS1 Kobo history loaded (the existing fixture producer), the count of
     Candidate segments and Candidate minutes on `main` (3.2) for 1-31 Oct, kept for E9.
  A pin the sweep finds that this spec does not name is a mid-build question.
- **Files.** Edited: `analytics/dispatch_v3.py`, `analytics/assessment_inputs.py` (two constants),
  `analytics/adapters/postgres_assessment_store.py` (`_configuration` only), `analytics/claim_limit_read.py`
  (`SUPPORTED_MODELS`), `backend/tests/dispatch_3_decision_table.md`, the docstrings the sweep classes as prose. New:
  `backend/tests/test_0k4e_energy_to_cover.py`, `backend/tests/test_0k4e_dispatch_33_postgres.py`. Tests that pin the
  string `dispatch-3.2` as the current version are updated to `dispatch-3.3`; tests of stored 3.2 history are not.
- **Databases:** `*_test` only, through `tools/heavy-slot.sh --db -- <command>`. Never the walkthrough database,
  ports 5490 or 8990, or Docker. The reassessment of any demo database is the coordinator's job (§5).

## 1. Outcome and gate questions

Is a battery-support point Candidate only when the battery's energy above the reserve covers, with 10 % headroom, the
energy PV does not cover from that point until PV alone covers the load with 10 % headroom? Is it Indeterminate,
naming the shortfall in kWh or the record that is missing, otherwise? Is the PV-alone branch unchanged? Is every
other rule, threshold and output of 3.2 unchanged, and the model version 3.3 in every hash, so stored 3.2 revisions
stay history and the reconcile pass reassesses default windows? Do the version pins downstream accept 3.3?

## 2. Design

### 2.1 Constants and inputs

`assessment_inputs.py`: `CONTROL_BATTERY_CAPACITY = "battery_energy_capacity"` (kWh),
`CONTROL_PCS_EFFICIENCY = "pcs_conversion_efficiency"` (%). `postgres_assessment_store._configuration`, inside the
per-revision loop after the minimum runtime: `_property(content, "BATTERY", "battery-energy-capacity")` and
`_property(content, "POWER_CONVERSION_SYSTEM", "pcs-conversion-efficiency")`, each appended as a `ControlValue` (value
as `format(Decimal(str(v)), "f")`, unit `kWh` or `%`, the revision's validity and id, `f"{source} v{source_version}"`)
when present with a value; when absent, nothing is appended and no limit is added (the analytic names it, §2.3).
`foundation_controls_on` is not changed (its readiness read lists the two policy controls only). `_control_changes`
adds both keys to its edge set.

`dispatch_v3.py`: `MODEL_VERSION = "dispatch-3.3"`; the module docstring's version paragraph gains: "`dispatch-3.3`
(0K4e, D-0K4.10) = `dispatch-3.2` plus the energy-to-cover test on the battery-support Candidate branch". New
constant `COVER_WALK_STEP = timedelta(minutes=5)`.

### 2.2 `_Index.energy_to_cover(t, feeders_at_t) -> tuple[Fraction | None, str | None]`

Walk `s = t, t + 5 min, t + 10 min, ...` while `s <= self.inputs.read_range.end`:
- load at `s`: the sum over `self.assets(LOAD, s)` of `lookup_asset(LOAD, asset, s)`; PV at `s`: `lookup(PV_AVAILABLE,
  s)`. A lookup that is `MISSING` at `s` takes, instead, the value of a GOOD interval reading of that channel with
  `interval_start < s <= interval_end` (a 15-minute mean holds over its own interval only, never beyond it). Any other
  problem, or still missing: return `(None, "<role>: <problem text> at <iso s>")`.
- if `pv >= load x (1 + CAPABILITY_HEADROOM)`: return `(need, None)` (cover reached; `need` excludes this slot);
- else `need += (load - pv) x Fraction(5, 60)`.
Reaching the read range's end without cover: `(None, f"solar cover not reached before the read range ends at {iso}")`.
Exact `Fraction` arithmetic throughout. The read range is the window plus `assessment_inputs.BRACKET` (6 hours) each
side, so the walk sees at most 6 hours past the window; an evening point whose cover lies later is Indeterminate. That
is conservative (no Candidate is claimed) and the decision table's 3.3 row says so.

### 2.3 `_evaluate`, the battery-support branch only (lines 298-300 today)

```python
elif pv + dis >= load * (1 + CAPABILITY_HEADROOM):
    capacity, _, cap_problem = index.control(CONTROL_BATTERY_CAPACITY, t_ctrl)
    efficiency, _, eff_problem = index.control(CONTROL_PCS_EFFICIENCY, t_ctrl)
    if cap_problem or eff_problem:
        result = point(INDETERMINATE, None)
        result.missing.append("battery energy capacity or PCS efficiency not configured; battery support not counted")
    else:
        need, why = index.energy_to_cover(t_meas)
        held = (soc - reserve) / 100 * capacity * efficiency / 100
        if need is None:
            result = point(INDETERMINATE, None)
            result.missing.append(f"energy to solar cover not evidenced ({why}); battery support not counted")
        elif held >= need * (1 + CAPABILITY_HEADROOM):
            result = point(CANDIDATE, None, pv + dis - load)
            reasons.append("PV available plus PCS discharge capability covers load with 10 % headroom, and the "
                           f"battery's {fmt(held)} kWh above reserve covers the {fmt(need)} kWh until solar covers load")
        else:
            result = point(INDETERMINATE, None)
            result.missing.append(f"battery energy above reserve ({fmt(held)} kWh) does not cover the {fmt(need)} kWh "
                                  "until solar covers load with 10 % headroom; battery support not counted")
```

`fmt` is the module's existing decimal formatter if one exists, else `format(Decimal(n.numerator) /
Decimal(n.denominator), ".3f")` defined once beside the constants. These strings are segment reasons and missing
texts, the same class as the existing ones on the same lists: the SC-1 scan's classification of `dispatch_v3.py`
strings applies unchanged (D-SC1.34); if the scan flags the new strings, that is a mid-build question, not a
workaround. The minimum-runtime withholding after the branch is unchanged and still applies.

### 2.4 The decision table and the pins

`dispatch_3_decision_table.md`: the version table gains a `dispatch-3.3` row ("the battery-support Candidate branch
also needs the battery's energy above the reserve, at the PCS efficiency, to cover the load PV does not cover until PV
alone covers it with the 10 % headroom; otherwise Indeterminate naming the shortfall or the missing record. Inputs gain
the Foundation's battery energy capacity and PCS efficiency", status current) and 3.2's status becomes historical in
3.1's words. `claim_limit_read.SUPPORTED_MODELS = ("dispatch-3.2", "dispatch-3.3")`. Every other pin the sweep finds
is handled by its class (§0).

## 3. Tests (written first)

`backend/tests/test_0k4e_energy_to_cover.py` (pure; `AnalyticInputSet` built in the test as
`test_s3_dispatch_v3_analytic.py` builds it; 5-minute GOOD readings; expected values are literals):
- **E1 covered:** at 18:00 load 10 kW, PV 0, discharge capability 30, SOC 80, reserve 30, capacity 200, efficiency
  95; load 10 and PV 0 to 05:55 next day, PV 12 at 06:00: need `10 x 12 = 120` kWh (144 slots of 5/6 kWh), held
  `0.5 x 200 x 0.95 = 95` kWh: Indeterminate, missing names 95.000 and 120.000.
- **E2 enough:** the same with SOC 100: held `133` kWh, `133 >= 132`: Candidate, the reason names both figures.
- **E3 headroom edge:** held exactly `1.1 x need` is Candidate; one kWh less is Indeterminate.
- **E4 a gap:** one PV reading missing at 23:00: Indeterminate, missing names `PV available power` and the time.
- **E5 15-minute means:** the same night at 15-minute load and PV interval means gives E1's need exactly (each mean
  held over its own interval).
- **E6 read range:** cover after the read range's end: Indeterminate naming the end; with E2's figures and the
  window ending at 04:00, the cover at 06:00 (inside the read range) is reached and the point is Candidate.
- **E7 not configured:** no capacity control: Indeterminate with the configuration text; the PV-alone branch is still
  Candidate on a point where PV alone covers load (no capacity needed).
- **E8 nothing else moved:** every case of `test_s3_dispatch_v3_analytic.py` that does not reach the battery-support
  branch gives the same classification, binding, margin and texts as on `main` (the file runs green with only its
  version literals updated; the packet lists which cases reach the branch and how each changed).

`backend/tests/test_0k4e_dispatch_33_postgres.py` (a `*_test` database, the DS1 Kobo history producer):
- **E9 stored history:** after assessing October on 3.3, the 3.2 runs and revisions are unchanged; the default
  selection is 3.3; Candidate minutes on 3.3 are at most the pre-flight's 3.2 count, and the packet shows both (a
  model-change reconciliation, D-0K4.11).
- **E10 consumers:** 4d's `candidate_l` and `necessary_l` for October on the same database sum to the same total as
  on 3.2, with `candidate_l` not larger (the litre split moves only between those two leaves); the claim-limit read
  answers for a 3.3 window.
- **E11 the reconcile pass:** the worker's reconcile pass enqueues every October window whose last default selection
  is 3.2, and only those.

**Regression:** the S3 dispatch tests, the 4d tests, `test_s4_fuel_cost.py`, `test_fuel_cost_v2.py`, the finding
service tests, `frontend/src/sites/__tests__/evidenceClaimLimit.test.tsx` (its `dispatch-3.2` literal is a stored
fixture: leave it, unless the sweep classes it a pin), check-all (fast) once, `python tools/select-tests.py --base main`.

## 4. Units

| Commit | Content |
|---|---|
| 1 (1.0) | §2.1, §2.2, §2.3; E1-E8 |
| 2 (0.75) | §2.4, the sweep's edits; E9-E11 on `*_test` |
| 3 (0.25) | regression, packet |

Packet `specs/0K4e-candidate-energy/packet.md`: the sweep table (hit, class, action), the selection quotes, E1-E3 in
words, E9's 3.2 against 3.3 Candidate minutes and 4d litres (labelled as the model-change reconciliation), the
regression output, the mid-build count.

## 5. What changes downstream (for the coordinator and the owner)

- **4d:** `candidate_l` falls and `necessary_l` rises by the same litres; `diesel_l`, `unexplained_l` unchanged.
- **fuel-cost-1:** new runs bound POTENTIAL_FUEL_COST over less Candidate time; pinned consequences stay as history.
- **Findings:** candidate-running Findings re-derive from 3.3 selections on the next pass; some shrink or close.
- **Databases:** the 5c walkthrough world has no telemetry (D-DS4.1) and does not move. The 13 Nov demo database and
  any database with telemetry change only when the coordinator runs the worker's reconcile pass on it (a heavy job,
  one at a time, on a clean database per the owner's rule). The 4d monthly figure served on the deep-dive for a
  telemetry Site moves at that point.

## 6. Done (questions; each can fail)

1. Is a battery-support point Candidate only with energy to solar cover, with the headroom, and Indeterminate naming
   the reason otherwise?
2. Are 15-minute means held over their own interval only, and a gap or an unreached cover never counted?
3. Is everything outside the branch byte-for-byte 3.2's, with 3.3 in every hash and 3.2 history intact?
4. Does every pin the sweep found accept 3.3, and does 4d move litres only between candidate and necessary?
5. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 7. Out of scope

The PV-alone branch's own counterfactual (whether PV would refill the battery later); load forecasting; any change to
4d, fuel-cost-1 or Findings code beyond version pins; running the reconcile pass on any demo database.
