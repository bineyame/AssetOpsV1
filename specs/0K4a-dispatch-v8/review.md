# 0K4a review

## Round 1: discovery review (W5), fresh Claude reviewer, 2026-11-21, head `8ff3a90f2`

**Summary (verdict: ACCEPT; 0 High, 0 Medium, 4 Low, none blocking).**
- v8 is a cycle-charging controller. N1's night starts at 34.78 %, charges on every running step, never discharges
  beside the generator and stops at 90.83 % after 4 h 40 min. Support is exact, the minimum load is held by charging
  then curtailing, the tank falls by exactly the curve, and the start and stop decision is v5's.
- By hand: N4's 10/3, +5/2, 5/12 kWh; N13's 7/4; N13b's 1/4 and -1; N8's 21049/200 L. Each matches.
- `_resolve_cycle` against v7's `resolve`: the eight named changes only; the §2.1 extraction moves bodies unedited.
  N9 `8eb9c44c...` unchanged; N12 `d6add2a3...` pins v8.
- Dawn (model-change reconciliation, both SIMULATED): v7 30.53 % (`9281/304`), v8 74.29 % (`677533/9120`).
- N2 is honest and not vacuous: it guards the resolver, not the controller (plant R2). N13 and N13b together prove
  the intent. The 7 mid-build readings are sound; the Architect should ratify them.
- Served text: SC-1 only; no baseline, allow-file or `tools/checks/` change.
- Lows: L1 the reserve in support has no kernel test; L2 a fuel-limited RUNNING segment has no kernel test; L3 doc
  merge conflicts with `main` (state index #186); L4 a stale test name.

### Checks run (this reviewer, at `8ff3a90f2`, all through `tools/heavy-slot.sh`)

| Check | Result |
|---|---|
| `pytest simulator/tests` (whole) | 565 passed in 13.2 s |
| `run-host-tests.ps1`: `test_0k4a_dispatch_v8`, plus the six host files the builder did not rerun at head (`test_0k1_forward_replay`, `test_0k2_kobo_season`, `test_registered_kobo_execution`, `test_mini_grid_v7`, `test_s6_verification_replay`, `test_0k4b_kobo_assumed`) | 82 passed in 267 s |
| `run-host-tests.ps1`: `test_0k4a_profile_words`, `test_0k4b_properties`, `test_sc1_statements` (no database) | 408 passed in 2.9 s |
| `check-all.ps1` (fast) | `All 42 guards passed (blocking; 0 advisory, 0 warned).` 221.1 s wall |
| `git diff <merge-base> HEAD -- tools/ config/ contracts/ runs/replay_study.py *baseline* *allow*` | empty |
| `git merge-tree HEAD main` | conflicts in `.ai/state/data.md`, `.ai/state/index-3.md` and `specs/INDEX.md` only (L3) |

Not run (as dispatched): the 300-file container suite, which needs a database and Docker.

### Realism against the named controller behaviours

- **Carries the load and charges after a night start.** I diffed v7's `resolve` against `_resolve_cycle`. While
  RUNNING, the allocation is `cycle_charge_split`. The split was read against D-0K4.3, and S1-S7 and S10 were
  recomputed by hand. My probe of N1's run found no step between the start and the stop with battery AC > 0.
- **Discharge only as support above the rating.** Branch 1 alone gives `battery_to_load > 0`, and only when
  `D > A + R`. This is S8's invariant over 540 combinations.
- **Minimum load by charging, then curtailing.** In the split, `g = min(R, max(M, D + C - A), D + C)`. PV is used
  before the generator for charging, and the generator is curtailed to `D + C` only when nothing more can be
  absorbed. S4 and S5 cover this, and N5 has one exact step on this fixture.
- **The tank falls by exactly the curve.** `fuel_litres` gives `33/600 x 5 x 108 + 2175/10000 x 1042/3 = 29.7 +
  75.545 = 105.245 = 21049/200` L, and my probe matches. The new `generator-fuel` balance and the tank account at 10
  kWh/L are present, and no balance identity was removed.
- **Start and stop are v5's.** `decide_v8` calls `decide_v5` for the run decision. The decide tests assert
  `generator(v8) == generator(decide_v5(site))`, and N7 checks starts at or below 35 and stops after at least 30
  minutes at or above the stop.

### The two cases the spec's tests do not fully catch

- **P1 versus N2.** I reran P1 on the whole v8 host file. It fails N1, N3, N4, N12, N13 and N13b, but not N2. (The
  packet's P1 row lists only N3, because its plant run selected `-k test_n2 or test_n3`.)
  N2 holds under P1 because the split cannot discharge outside branch 1, whatever the controller requested. So N2
  tests the resolver layer, and that layer alone already guarantees N2.
  Reviewer plant R2 (P1 plus v7's allocation while RUNNING, which is v7's own fault inside v8) fails N2, N1, N3, N4,
  N5, N12, N13 and N13b. R1 (v7's allocation while RUNNING, controller intact) fails N5 and N13b.
  So N2 is not vacuous: it catches the fault the review names whenever the resolver regresses. The guide was simply
  wrong to expect a controller-only plant to fail it. The builder's account is honest.
- **P13 versus N13 and N13b.** P13 passes N13, because v7's end-of-step rule appends the same "differed from the
  view" note whenever `limited` is empty. That is what N13's fixture has: a 5 kW charge request that nothing else
  limits.
  N13b gives the step another limit (res 5 kW: a 35 kW request against the 30 kW PCS). Only v8's own note can then
  carry it, and P13 fails N13b (my rerun confirms).
  Hand check: [60, 62) charges 30 kW for 2 min (-1 kWh); [62, 65) has 45 > 40 with no discharge, so 5 kW is unserved
  for 3 min (1/4 kWh).
  Together the two tests prove what the spec intends: the unserved amount and the view-bound rule (N13), and the
  note's independence from v7's fallback (N13b).

### Mid-build questions (7)

1. **Generator-only reorder, and the extra file `test_decide_v8.py`.** Both match §2.3 and §4. Kobo's order is
   unaffected. Sound.
2. **N7 gains a 37 % stop run.** This is not tuning. N1's and N5's runs are unchanged. The extra run is a declared
   input under which the minimum runtime must bind: from 35 % to 37 % takes about 3 running steps against the 6 the
   runtime requires. Without it, P11 passed N7. Sound.
3. **N13's "all night" read as [60, 90).** Correct. My probe of the all-night fixture (res and clinic over [0, 360),
   mill [60, 90)) shows the reserve binding inside the window: at [75, 80) battery AC is `1667/960` and from 80 it is
   0, so N4's per-step figures cannot hold there. The spec's literal was not satisfiable. Sound.
4. **N13b added.** See above. Sound.
5. **The `test_0k4b_properties.py` P4 edit.** It excludes exactly `("mini-grid", 8)`, and W1 asserts v8's needs.
   Filtering the cases by key keeps 0K4b's assertion intact. Correct (name: L4).
6. **The `test_sc1_statements.py` T8 edit.** It is the same adopter edit 0K4b made: the two new keys. Correct.

Each reading should be ratified by the Architect in a spec revision. None of them changes product behaviour.

### 0K4b's review notes (G1, G2)

`_checked_curve` refuses `rated <= 0` at `generator-rated-power@generator` before the curve's division, and maps
`CurveRefused` to the no-load-rate address (N10 covers the SFC case). `_fuel_cap_kw` refuses a segment of zero or
negative length. G1 and G2 test both guards and the positive path (G2's literal checked by hand: `29/40 / (2175/10000
/ 12)`). Both guards are adequate. The fuel cap's use inside the kernel is untested (L2).

### Served text (D-0K4.19)

`ModelProfile.statement: str | Message`. `run_profile_summary` renders both statements through `served_text`, and
the two statements have hand-literal cases. W1 checks the text served on v8. W2 checks, by a pinned hash, that
every other profile's summary is byte-equal to `main`. No baseline or allow entry was added, and check-all's SC-1
guards are green.

`publication_profile_summary` still reads `profile.statement` directly. That is a different family (publication
profiles), not touched here, and correct to leave alone.

### Plants

The builder's plant log was spot-checked by rerunning P1 and P13. My own plants are below. Each was reverted, and
the tree was clean after.

| Plant | Result |
|---|---|
| P1 `decide_v8` never reorders | fails N1, N3, N4, N12, N13, N13b; passes N2 (see above) |
| P13 reverse-mismatch note removed | fails N13b only |
| R1 v7's allocation while RUNNING | fails N5, N13b |
| R2 P1 + R1 | fails N1, N2, N3, N4, N5, N12, N13, N13b |
| R3 fuel cap dropped (`generator_cap = gen.rated`) | **all 15 pass** (L2) |
| R4 support discharge ignores the reserve (`min(requested, discharge_limit)`) | **all 15 pass** (L1) |

### Findings

- **L1 (Low; evidence gap against spec §5 Q2, not a behaviour fault).** `host/tests/test_0k4a_dispatch_v8.py:239`
  (N4) and `:377` (N13).
  - What is wrong: §5 Q2 asks for support "within PCS and reserve limits". N4's precondition (SOC above 30 at
    01:30) keeps the reserve from binding, so no test sees the reserve term: plant R4 passes all 15 tests.
  - The behaviour is correct. My probe of the all-night fixture shows battery AC `1667/960` kWh at [75, 80), which
    equals the reader's `(soc - 30) x 2 x 95/100`, then 0 with 35/12 kWh unserved at [80, 90).
  - Fix: add N4b on that fixture (res 25 and clinic 10 over [0, 360), mill 40 over [60, 90), start SOC 34). Assert
    the reader's reserve-limited battery AC and the unserved remainder on [75, 90).
- **L2 (Low; missing test).** `simulator/assetops_simulator/packs/mini_grid.py:1548` and the step-5 branch below it
  (§2.4 (3) and (5)).
  - What is wrong: no kernel test exercises a fuel-limited RUNNING segment. Plant R3 (fuel cap dropped) passes all
    15 host tests. G2 tests `_fuel_cap_kw` only in isolation. The Kobo tank never binds, so the curve-based cap,
    "below the no-load burn" and the rerun with `generator_kw = 0` are unverified in a trajectory.
  - Why it matters: litres feed a money figure, and a later season or world may run a tank low.
  - Fix: a short v8 run with a tank of a few litres. It asserts the partial output equals the reader's
    `(fuel - 33/600 x 5) / (2175/10000 x 5/60)` kW, that the tank ends at 0, not below, and that the run is
    COMPLETED.
- **L3 (Low; merge hygiene).** `.ai/state/index-3.md:11` and `.ai/state/data.md` (the 0K4a section), plus
  `specs/INDEX.md`.
  - What is wrong: `main` now carries 0K4c as #186, and `git merge-tree` reports content conflicts in these three
    doc files.
  - Fix: renumber 0K4a to 187 at the merge.
  - After the merge, rerun `test_0k4a_dispatch_v8.py`. 0K4c edited `host/tests/kobo_season.py` additively, with v1
    defaults unchanged, so N9 and N12 are expected to hold.
- **L4 (Low; preference).** `backend/tests/test_0k4b_properties.py:117`. The test is named
  `..._on_no_profile_yet`, but v8 now carries the needs. Rename it to say "on no profile but v8".

### Residual risk the packet does not name

- `trajectory_digest` hashes stocks, measurements and states, but not `limited_by`, the dispatch reasons or the flow
  set. A change to v8's note texts moves neither N12 nor N9. N8 and N13b pin only two notes.
- In a Site order with PV behind the battery, the view's support request ignores PV. The resolver's split corrects
  the physics, but the step carries a "differed" note. This does not affect Kobo.
- N5's exact set is one step (packet residual). The minimum-load mechanism rests mainly on S4, S5 and S8.
