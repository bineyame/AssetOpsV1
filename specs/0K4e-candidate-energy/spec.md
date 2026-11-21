# 0K4e: `dispatch-3.3`, a battery-support Candidate needs the energy to reach solar cover (implementer spec)

Status: live, rev 2 (Architect, Claude, 2026-11-21): handshake answered (D-0K4.19, D-0K4.23, D-0K4.24, D-0K4.25),
build-ready. **2.75 units.** Discovery review (W5): a change to
a served classification that bounds money (fuel-cost-1) and litres (4d). No migration (a model version is data).
`USER_REVIEW_REQUIRED: true` (served candidate litres and Findings move). Rulings: `specs/0K4-dispatch-model-review/
rulings.md` (D-0K4.10, D-0K4.11; handshake answers D-0K4.19, D-0K4.23, D-0K4.24). Reviewer guide: `reviewer-guide.md`.
Questions: `handshake.md`, `handshake-I.md`.

**Rev 2 (handshake).** The new outcome adds no English to `reasons` or `missing`: each point that reaches the test
stores an `energy_cover` entry of codes and figures, and the two readers that explain a segment render SC-1
statements from it (§2.5, D-0K4.24). The walk is one argument and a memoised per-slot recurrence (§2.2). E5b is
redesigned so the fallback's convention can fail it. E9-E11 run on the `CaseRunner` world. Role coverage stays per
instant (E10).

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
  3. on a run-owned `*_test` database (`..._pt<run>_<tag>_test`, `backend/TESTING.md`, through `tools/heavy-slot.sh
     --db`) holding the `CaseRunner` world (`backend/tests/test_4d_litre_split_postgres.py:17`) plus E9's planted
     night, the count of Candidate segments and Candidate minutes on `main` (3.2) over that fixture's days, labelled
     as such, kept for E9 (D-0K4.23).
  A pin the sweep finds that this spec does not name is a mid-build question.
- **Files.** Edited: `analytics/dispatch_v3.py`, `analytics/assessment_inputs.py` (two constants),
  `analytics/adapters/postgres_assessment_store.py` (`_configuration` only), `analytics/claim_limit_read.py`
  (`SUPPORTED_MODELS`), `analytics/plain.py` (`_segment`), `analytics/finding_read.py` (`portion_cause` and its
  caller), `structure/rows_mini_grid.py` (three version tokens, §2.4), `i18n/statements/en/vocabulary.py` (two
  vocabularies), `backend/tests/dispatch_3_decision_table.md`, the docstrings the sweep classes as prose. New:
  `i18n/statements/en/dispatch.py`, `backend/tests/statement_cases/dispatch.py`,
  `backend/tests/test_0k4e_energy_to_cover.py`, `backend/tests/test_0k4e_readers.py`,
  `backend/tests/test_0k4e_dispatch_33_postgres.py`. Tests that pin the
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

### 2.2 `_Index.energy_to_cover(t) -> Cover` (one argument; D-0K4.23)

`Cover` is a frozen dataclass `(state, need, input, problem, at)`: `state` one of `REACHED`, `GAP`, `END`; `need` a
`Fraction` for `REACHED`, else `None`; `input` and `problem` the failing role and its lookup code for `GAP`; `at` the
failing slot for `GAP` or the read range's end for `END`. Slots are `s = t, t + 5 min, ...` (`COVER_WALK_STEP`).
Per slot, the feeders are re-read (`self.assets(LOAD, s)`), so a feeder bound later counts from its binding on:
- load at `s`: the sum over `self.assets(LOAD, s)` of `lookup_asset(LOAD, asset, s)`; PV at `s`: `lookup(PV_AVAILABLE,
  s)`. A lookup that is `MISSING` at `s` takes, instead, the value of a GOOD interval reading of that channel with
  `interval_start < s <= interval_end` (a 15-minute mean holds over its own interval only, never beyond it). No
  feeder bound is `UNBOUND`.
- the recurrence, memoised on the `_Index` by slot instant (built once per `assess()`):
  `s > read_range.end` gives `Cover(END, at=read_range.end)`; a load or PV problem at `s` gives `Cover(GAP, input=role,
  problem=code, at=s)`; `pv >= load x (1 + CAPABILITY_HEADROOM)` gives `Cover(REACHED, need=0)` (this slot excluded);
  otherwise `Cover(REACHED, need=(load - pv) x Fraction(5, 60) + next.need)` where `next = cover(s + 5 min)`, and a
  `GAP` or `END` `next` is returned unchanged.
- computed iteratively: walk forward until a memo hit or a terminal, then fill the memo backward. Each slot's lookups
  run once per assessment however many points reach the branch. Exact `Fraction` throughout.

The read range is the window plus `assessment_inputs.BRACKET` (6 hours) each side, so the walk sees at most 6 hours
past the window; an evening point whose cover lies later is Indeterminate (`NOT_REACHED`). That is conservative (no
Candidate is claimed) and the decision table's 3.3 row says so.

### 2.3 `_evaluate`, the battery-support branch only (lines 298-300 today)

```python
elif pv + dis >= load * (1 + CAPABILITY_HEADROOM):
    capacity, _, cap_problem = index.control(CONTROL_BATTERY_CAPACITY, t_ctrl)
    efficiency, _, eff_problem = index.control(CONTROL_PCS_EFFICIENCY, t_ctrl)
    if cap_problem or eff_problem:
        result = point(INDETERMINATE, None)
        result.cover = cover_entry(t_meas, "NOT_CONFIGURED", controls=[k for k, p in (
            (CONTROL_BATTERY_CAPACITY, cap_problem), (CONTROL_PCS_EFFICIENCY, eff_problem)) if p])
    else:
        walk = index.energy_to_cover(t_meas)
        held = (soc - reserve) / 100 * capacity * efficiency / 100
        if walk.state == "GAP":
            result = point(INDETERMINATE, None)
            result.cover = cover_entry(t_meas, "GAP", held=held, input=walk.input, problem=walk.problem,
                                       gap_at=walk.at)
        elif walk.state == "END":
            result = point(INDETERMINATE, None)
            result.cover = cover_entry(t_meas, "NOT_REACHED", held=held, range_end=walk.at)
        elif held >= walk.need * (1 + CAPABILITY_HEADROOM):
            result = point(CANDIDATE, None, pv + dis - load)
            reasons.append("PV available plus PCS discharge capability covers load with 10 % headroom")  # 3.2's text
            result.cover = cover_entry(t_meas, "COVERED", held=held, need=walk.need)
        else:
            result = point(INDETERMINATE, None)
            result.cover = cover_entry(t_meas, "SHORT", held=held, need=walk.need)
```

`Point` and `Segment` gain `cover: dict | None = None` and `covers: list[dict]` respectively. `cover_entry(at, state,
*, held=None, need=None, input=None, problem=None, gap_at=None, range_end=None, controls=())` returns `{"at": iso(at),
"state": state, "held_kwh": _num(held), "need_kwh": _num(need), "input": input, "problem": problem, "gap_at":
iso(gap_at) or None, "range_end": iso(range_end) or None, "controls": sorted(controls)}`, codes and `_num` strings only
(I2: `_num` normalizes, so `"95"`, `"120"`, `"133"`). The Candidate keeps 3.2's reason string byte for byte, so
`claim_limit_read._CANDIDATE_ROLES` still maps it and no new string is added. The minimum-runtime withholding after
the branch is unchanged and still applies; a withheld point keeps its `cover`. `_combine` sets `covers` to its two
points' entries (deduplicated, sorted by `at`), and `Segment.payload()` adds `"energy_cover": covers` only when
`covers` is non-empty, so a segment that never reaches the branch is byte-equal to 3.2's form (E8).

### 2.4 The decision table and the pins

`dispatch_3_decision_table.md`: the version table gains a `dispatch-3.3` row ("the battery-support Candidate branch
also needs the battery's energy above the reserve, at the PCS efficiency, to cover the load PV does not cover until PV
alone covers it with the 10 % headroom; otherwise Indeterminate naming the shortfall or the missing record. Inputs gain
the Foundation's battery energy capacity and PCS efficiency", status current) and 3.2's status becomes historical in
3.1's words. `claim_limit_read.SUPPORTED_MODELS = ("dispatch-3.2", "dispatch-3.3")`. The 3.3 row also says: the walk re-reads the
feeders at each slot; an energy-cover Indeterminate is a limit of the rule, not an input-role gap, so per-instant role
coverage reads COVERED when the instant's inputs are whole (D-0K4.23, R3). `structure/rows_mini_grid.py:62-67`: the
`necessary_l` and `candidate_l` sources (code-form, not fingerprinted) read `dispatch-3.3`; the `unexplained_l`
source reads "fuel balance (FUEL_DELIVERY, TANK_DIP) minus dispatch-3.3", a fingerprint swap (D-0K4.19 item 5: the
packet lists the old and new fingerprint; the diff is the version token only). Every other pin the sweep finds is
handled by its class (§0).

### 2.5 The words: statements from the stored facts (D-0K4.24)

`i18n/statements/en/vocabulary.py`, two vocabularies appended:

```python
"dispatch_input": {
    "forms": ["label", "in_sentence"],
    "order": ["feeder_demand", "pv_available_power", "battery_energy_capacity", "pcs_conversion_efficiency"],
    "entries": {
        "feeder_demand": {"label": "Load", "in_sentence": "the load"},
        "pv_available_power": {"label": "Solar available power", "in_sentence": "solar available power"},
        "battery_energy_capacity": {"label": "Battery energy capacity", "in_sentence": "the battery energy capacity"},
        "pcs_conversion_efficiency": {"label": "PCS conversion efficiency",
                                      "in_sentence": "the PCS conversion efficiency"},
    },
},
"reading_problem": {
    "forms": ["in_sentence"],
    "order": ["MISSING", "NOT_GOOD", "CONFLICTING", "AMBIGUOUS_SERIES", "UNBOUND", "MULTIPLE_BINDINGS"],
    "entries": {
        "MISSING": {"in_sentence": "no accepted reading"},
        "NOT_GOOD": {"in_sentence": "a reading not of good quality"},
        "CONFLICTING": {"in_sentence": "contradictory readings"},
        "AMBIGUOUS_SERIES": {"in_sentence": "readings out of sequence order or overlapping"},
        "UNBOUND": {"in_sentence": "no bound asset"},
        "MULTIPLE_BINDINGS": {"in_sentence": "several bound assets"},
    },
},
```

`i18n/statements/en/dispatch.py` (data only, D-SC1.3):

```python
STATEMENTS = {
    "dispatch.energy_cover": {
        "slots": {
            "state": {"type": "state", "values": ["COVERED", "SHORT", "GAP", "NOT_REACHED", "NOT_CONFIGURED"]},
            "held": {"type": "quantity", "places": "normal", "optional": True, "evidence": {"with": "basis"}},
            "need": {"type": "quantity", "places": "normal", "optional": True, "evidence": {"with": "basis"}},
            "headroom": {"type": "percent", "places": "normal", "optional": True, "evidence": {"with": "basis"}},
            "basis": {"type": "evidence", "of": ["held", "need", "headroom"]},
            "input": {"type": "word", "vocabulary": "dispatch_input", "form": "in_sentence", "optional": True},
            "problem": {"type": "word", "vocabulary": "reading_problem", "form": "in_sentence", "optional": True},
            "at": {"type": "instant", "optional": True},
            "controls": {"type": "items", "of": {"type": "word", "vocabulary": "dispatch_input", "form": "in_sentence"},
                         "order": "vocabulary", "optional": True},
        },
        "variants": [
            {"id": "covered", "when": {"is": ["state", "COVERED"]},
             "requires": {"all": [{"present": "held"}, {"present": "need"}, {"present": "headroom"}]},
             "text": "The available solar power and battery output were more than the site demand, with battery "
                     "charge above its minimum reserve, and the battery's {held} above that reserve covers the {need} "
                     "needed until solar power covers site demand with {headroom} headroom ({basis}); no reason the "
                     "generator was needed was recorded."},
            {"id": "short", "when": {"is": ["state", "SHORT"]},
             "requires": {"all": [{"present": "held"}, {"present": "need"}, {"present": "headroom"}]},
             "text": "Battery support was not counted: the battery's {held} above its minimum reserve does not cover "
                     "the {need} needed until solar power covers site demand with {headroom} headroom ({basis})."},
            {"id": "gap", "when": {"is": ["state", "GAP"]},
             "requires": {"all": [{"present": "input"}, {"present": "problem"}, {"present": "at"}]},
             "text": "Battery support was not counted: {input} has {problem} at {at}, before solar power covers site "
                     "demand."},
            {"id": "not_reached", "when": {"is": ["state", "NOT_REACHED"]}, "requires": {"present": "at"},
             "text": "Battery support was not counted: solar power does not cover site demand before the assessed "
                     "records end at {at}."},
            {"id": "not_configured", "when": {"is": ["state", "NOT_CONFIGURED"]}, "requires": {"present": "controls"},
             "text": "Battery support was not counted: the Site's Foundation does not give {controls}."},
        ],
        "exhaustive": "state",
        "rephrase": "never",
    },
    "dispatch.energy_cover_cause": {
        "slots": {"state": {"type": "state", "values": ["SHORT", "NOT_REACHED"]}},
        "variants": [
            {"id": "short", "when": {"is": ["state", "SHORT"]},
             "text": "the battery's stored energy above its minimum reserve would not have lasted until solar power "
                     "covered site demand"},
            {"id": "not_reached", "when": {"is": ["state", "NOT_REACHED"]},
             "text": "solar power did not cover site demand before the assessed records end"},
        ],
        "exhaustive": "state",
        "rephrase": "never",
    },
}
```

Facts from an entry (one function, `dispatch_v3.cover_message(entry) -> Message`): `state=State(entry["state"])`;
`held` and `need` as `Quantity(Decimal(v), "kWh", Evidence("DERIVED"))` when not null; `headroom =
Percent(Decimal(_num(CAPABILITY_HEADROOM)), Evidence("DECLARED"))` (a fraction: `0.1` reads 10%) for `COVERED` and `SHORT`; `input=Word("dispatch_input", ...)`,
`problem=Word("reading_problem", ...)` and `at=Instant(gap_at)` for `GAP`; `at=Instant(range_end)` for
`NOT_REACHED`; `controls=Items(tuple(Word("dispatch_input", k) for k in entry["controls"]))` for `NOT_CONFIGURED`.
Rendered for E1's figures, `short` reads "Battery support was not counted: the battery's 95 kWh above its minimum
reserve does not cover the 120 kWh needed until solar power covers site demand with 10% headroom (Estimated)." (the
evidence word is the format's, D-SC1.10).

Readers:
- `plain._segment(s)`: `lead` = the segment's `energy_cover` entry first by `NOT_CONFIGURED`, `GAP`, `NOT_REACHED`,
  `SHORT`, `COVERED`, then earliest `at`. When the segment is CANDIDATE and `lead` is `COVERED`, or INDETERMINATE with
  no legacy `missing` text and `lead` is not `COVERED`, `reason = render(cover_message(lead))`. Otherwise today's
  branches, unchanged (a legacy record gap wins).
- `finding_read.portion_cause(missing, cover=())`: today's rule over `missing`, then a `GAP` or `NOT_CONFIGURED`
  entry in `cover` gives `RECORD_GAP`; each `SHORT` or `NOT_REACHED` entry adds `render(message(
  "dispatch.energy_cover_cause", state=State(...)))` to the `MODELLING` words. `_indeterminate_reasons` passes
  `seg.get("energy_cover") or []` and adds `"energy_cover"` (the stored entries, codes only) to each portion.
- `claim_limit_read` and `stored_declaration`: unchanged apart from `SUPPORTED_MODELS` (D-0K4.23, R3).

`statement_cases/dispatch.py`: one hand-literal case per variant (seven), the E1-E7 facts. Every literal above was loaded
and rendered in a scratch copy of `i18n` (D-0K4.19, "Checked").

## 3. Tests (written first)

`backend/tests/test_0k4e_energy_to_cover.py` (pure; `AnalyticInputSet` built in the test as
`test_s3_dispatch_v3_analytic.py` builds it; 5-minute GOOD readings; expected values are literals):
- **E1 covered:** at 18:00 load 10 kW, PV 0, discharge capability 30, SOC 80, reserve 30, capacity 200, efficiency
  95; load 10 and PV 0 to 05:55 next day, PV 12 at 06:00: need `10 x 12 = 120` kWh (144 slots of 5/6 kWh), held
  `0.5 x 200 x 0.95 = 95` kWh: Indeterminate; `missing` is 3.2's for that point (nothing added); the entry is
  `state "SHORT"`, `held_kwh "95"`, `need_kwh "120"`.
- **E2 enough:** the same with SOC 100: held `133` kWh, `133 >= 132`: Candidate; the reason is 3.2's string exactly;
  the entry is `state "COVERED"`, `held_kwh "133"`, `need_kwh "120"`.
- **E3 headroom edge:** held exactly `1.1 x need` is Candidate; one kWh less is Indeterminate.
- **E4 a gap:** one PV reading missing at 23:00: Indeterminate; entry `state "GAP"`, `input "pv_available_power"`,
  `problem "MISSING"`, `gap_at` 23:00.
- **E5 15-minute means:** the same night at 15-minute load and PV interval means gives E1's need exactly (each mean
  held over its own interval).
- **E5b the fallback's convention** (D-0K4.23, R2): the point at 18:00 with E2's SOC, reserve, capacity and
  efficiency; load as 5-minute means ending 18:00, 18:05 and 18:10 (10 kW), no load reading ending 18:15, one
  15-minute load mean over `(18:15, 18:30]` of 20 kW; PV 0 at every slot to 18:30 and 30 kW from 18:35: entry `state
  "GAP"`, `input "feeder_demand"`, `problem "MISSING"`, `gap_at` 18:15. (Under the swapped convention the walk reads 20
  kW at 18:15 and returns need `55/6` kWh: plant P10.)
- **E6 read range:** cover after the read range's end: Indeterminate; entry `state "NOT_REACHED"`, `range_end` the
  read range's end; with E2's figures and the
  window ending at 04:00, the cover at 06:00 (inside the read range) is reached and the point is Candidate.
- **E7 not configured:** no capacity control: Indeterminate; entry `state "NOT_CONFIGURED"`, `controls
  ["battery_energy_capacity"]`; the PV-alone branch is still
  Candidate on a point where PV alone covers load (no capacity needed).
- **E8 nothing else moved:** every case of `test_s3_dispatch_v3_analytic.py` that does not reach the battery-support
  branch gives the same classification, binding, margin and texts as on `main` (the file runs green with only its
  version literals updated; no segment that does not reach the branch carries `energy_cover`; the packet lists which
  cases reach the branch and how each changed).
- **E8b the walk is memoised:** with a counting wrapper on `lookup_asset`, assessing a window of 36 battery-support
  points over one night calls it at most once per (channel, asset, slot), and E1-E6's figures are unchanged.

`backend/tests/test_0k4e_readers.py` (pure):
- **E12 plain:** `plain._segment` on E1's, E4's, E6's and E7's segments gives the `short`, `gap`, `not_reached` and
  `not_configured` case texts; on E2's, the `covered` text; on a segment with both a legacy `missing` text and a
  `SHORT` entry, today's "Records needed to decide are missing or conflicting: ..." reason.
- **E13 findings:** `portion_cause` with a `SHORT` entry and no legacy text gives `MODELLING` with the
  `dispatch.energy_cover_cause` `short` text; with a `GAP` or `NOT_CONFIGURED` entry, `RECORD_GAP`.
- **E14 roles:** `claim_limit_read.segment_roles` on a stored 3.3 segment Indeterminate for `SHORT`, `GAP` or
  `NOT_CONFIGURED`, whose own instant inputs are whole, reads every role COVERED (R3, I6 (d)).

`backend/tests/test_0k4e_dispatch_33_postgres.py` (a run-owned `*_test` database, the `CaseRunner` world plus one
planted night of battery-support points; precondition, on 3.2, at least one Candidate segment reaches the
battery-support branch):
- **E9 stored history:** after assessing the fixture's days on 3.3, the 3.2 runs and revisions are unchanged; the default
  selection is 3.3; Candidate minutes on 3.3 are at most the pre-flight's 3.2 count, and the packet shows both (a
  model-change reconciliation, D-0K4.11).
- **E10 consumers:** 4d's `candidate_l` and `necessary_l` for October on the same database sum to the same total as
  on 3.2, with `candidate_l` not larger (the litre split moves only between those two leaves); the claim-limit read
  answers for a 3.3 window. The packet reports E9's `assess()` wall time on 3.2 and 3.3; above 2x is a mid-build
  question (R5).
- **E11 the reconcile pass:** the worker's reconcile pass enqueues every fixture window whose last default selection
  is 3.2, and only those.

**Regression:** the S3 dispatch tests, the 4d tests, `test_s4_fuel_cost.py`, `test_fuel_cost_v2.py`, the finding
service tests, the plain and finding read tests, `test_sc1_statements.py`, `python tools/checks/statement_catalogue.py`
(no `HAND_BUILT_NEW` beyond the one listed swap, no allow entry), `frontend/src/sites/__tests__/evidenceClaimLimit.test.tsx` (its `dispatch-3.2` literal is a stored
fixture: leave it, unless the sweep classes it a pin), check-all (fast) once, `python tools/select-tests.py --base main`.

## 4. Units

| Commit | Content |
|---|---|
| 1 (1.25) | §2.1, §2.2, §2.3; E1-E8b |
| 2 (0.75) | §2.5: vocabularies, statements, cases, `cover_message`, the two readers; E12-E14 |
| 3 (0.75) | §2.4, the sweep's edits and the one swap; E9-E11 on `*_test`; regression, packet |

Packet `specs/0K4e-candidate-energy/packet.md`: the sweep table (hit, class, action), the selection quotes, E1-E3 in
words, E9's 3.2 against 3.3 Candidate minutes and 4d litres (labelled as the model-change reconciliation), E9's wall
times, the database name, the fingerprint swap (old, new), the regression output, the mid-build count.

## 5. What changes downstream (for the coordinator and the owner)

- **4d:** `candidate_l` falls and `necessary_l` rises by the same litres; `diesel_l`, `unexplained_l` unchanged.
- **fuel-cost-1:** new runs bound POTENTIAL_FUEL_COST over less Candidate time; pinned consequences stay as history.
- **Findings:** candidate-running Findings re-derive from 3.3 selections on the next pass; some shrink or close. An
  undecided portion caused by the energy test reads its cause in plain words (§2.5).
- **Verifications (I6 (a)):** a verification whose baseline days mix model versions refuses
  (`VERIFICATION_MODEL_NOT_COMPARABLE`) from deploy until the reconcile pass ends; the coordinator runs the pass
  straight after deploy. The S3 lineage and performance reads follow `MODEL_VERSION` (I6 (b); no code change).
- **Readiness (I6 (d)):** per-instant role coverage reads COVERED on an energy-cover Indeterminate (E14); naming it
  in readiness is queued (Q10).
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
5. Is the new outcome stored as codes and figures only, explained by SC-1 statements in both readers, with no
   baseline or allow entry beyond the one listed version swap?
6. Does each plant of `reviewer-guide.md` fail its named test, and is the mid-build count 0?

## 7. Out of scope

The PV-alone branch's own counterfactual (whether PV would refill the battery later); load forecasting; any change to
4d or fuel-cost-1 code beyond version pins; Findings code beyond §2.5's `portion_cause`; migrating the existing
dispatch texts to SC-1 (queue Q9); readiness naming the energy test (Q10); running the reconcile pass on any demo
database.
