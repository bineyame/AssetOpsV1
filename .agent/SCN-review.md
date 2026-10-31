# SCN-kobo-reserve-matters review

Reviewer: fresh Claude reviewer (did not author the slice), 2026-10-31.
Branch `task/SCN-kobo-reserve-matters`, head `956fc3fde`, base `ca6d7d61b`. The review ran on a `git archive`
snapshot of `956fc3fde` with the plan2 venv and PYTHONPATH set to the snapshot's
`backend;contracts;tools;simulator;gateway;host;field`. No Postgres was used.

## Verdict: ACCEPT, with M1 fixed on the branch before merge

The honest-result rule holds. The scenario values are exactly Addendum 1 D2. No price, SFC, profile, template,
verification, cost-check or existing scenario file is touched. The only deleted line is the 13 -> 14 count. The
D2 kernel properties hold on my independent rerun, and each of the five tests fails when its property is broken.
M1 is the only thing blocking the merge: the branch does not merge cleanly into main `89280952d`. The conflicts are
in bookkeeping files only.

## Findings

### M1 (Medium, merge gate). The branch conflicts with main `89280952d`
`git merge-tree --write-tree 89280952d 956fc3fde` reports content conflicts in three files:
- `.ai/ACTIVE_CONTEXT.md:7-11`
- `.ai/CODE_STATE.md:6140-6171`
- `.ai/DECISIONS.md:4346-4354`

(The line numbers are in the merge result.) In each file both sides appended an entry at the same place: IDX-GAPS on
main, SCN on the branch. No code, config or test file conflicts. The dispatch requires a clean merge.

**Fix:** merge main into the branch, keep both entries in all three files, then rerun the four focused test files
and the two guards.

### L1 (Low, accuracy of prose). `purpose` overstates what the generator does
`config/scenarios/kobo-mini-grid-reserve-matters.yaml:25` says: "With a 30 % reserve the battery stops at 30 % and the
generator carries the load until the sky clears."

The trajectory says otherwise. I reproduced it independently: the baseline loads the generator in a sawtooth, one
5-minute step about every 40 minutes. The loaded steps are 04:45, 04:50, 05:25, 05:30, 06:05, 06:10, 06:45 and 06:50.
- At the big step (offset 110), 2.85 kWh is produced. Of that, `generator_to_battery` is 2.5 kWh and
  `generator_to_load` is only 0.35 kWh.
- Of the 12.08 kWh produced before the clearing, roughly 10 kWh charges the battery.
- Between those steps, the battery carries the load.

The text is Lab vocabulary and makes no money claim. Still, it is the scenario's own stated design, and a demo
narrator may read it aloud.

**Fix (optional):** reword to something like "with a 30 % reserve the generator recharges the battery each time it
reaches 30 %, so it delivers energy before the clearing; with a 25 % reserve it stays unloaded." Any rewording
changes the fingerprint, so do it before merge, re-pin the fingerprint, and keep the text under the 800-character
limit. Leaving it as is is acceptable.

### L2 (Low, test strength). Property 5 does not inspect the transition into step 0
`host/tests/test_scn_reserve_matters.py:93`: `transitions` compares step i with step i-1. The baseline's
STOPPED -> STARTING happens at offset 0, because step 0 is already STARTING. That transition is never checked; only
STARTING -> RUNNING at offset 5 is. The interval is fixed at 03:00 UTC, which is 180 minutes from midnight, so the
property holds today, and my planted break (moving the run start to 23:50) is still caught. The gap would matter
only if the interval moved.

**Fix (optional):** prepend the initial state (`STOPPED`, from `starting-generator-state`) to `states`.

### L3 (Low, preference). H is not pinned
`host/tests/test_scn_reserve_matters.py:56-60` asserts that some loaded hour exists, but not that H = 4 (04:00 UTC).
U3 and the DEMO-SPARSE `trial.window_hour` depend on H. A later kernel change could move H silently while all five
tests stay green.

**Fix (optional):** `assert hour == 4`, labelled as the recorded U3 window rather than a design target.

### L4 (Low, packet wording)
`.agent/SCN-packet.md:47` says the generator "charges at -35.8 kW (2.85 kWh)". -35.8 kW is the *requested*
`battery-power`. The accepted charge is 2.5 kWh in 5 minutes, which is 30 kW, the PCS limit. This is a wording
correction only.

## Key judgement: the change to the property-1 test

The Addendum says: "the generator delivers > 0 kWh in at least one whole hour before offset 240. H = the first such
hour (expected 05:00-06:00 UTC)." The sheet uses "whole hour" in one other place, §2 U2 property 2: "the hour holding
that start (rounded down to the whole hour; expected 04:00-05:00 UTC)". There it plainly means a clock-aligned hour
bucket. The Addendum also gives H as a clock interval, and H is reused as the U3 trial window hour. So "whole hour"
means a complete clock hour, and "> 0 kWh in" it means the hour's energy total. "Loaded at every step" appears nowhere
in the text.

The corrected helper (`_first_loaded_hour`, `:45-52`) does what the text says. It takes clock hours in order, rejects
any hour that ends after offset 240, and returns the first hour whose total is > 0.

Under the frozen policy no hour is loaded at every step, which is the sawtooth described above. The stricter reading
would therefore fail for any D2-like design, and the Addendum's own expectation ("carries load until the clearing")
does not depend on it. The design values were not changed between the two runs: the YAML is identical, and only the
instrument changed. I judge the correction to be a fix to the implementer's own instrument back to the written
property, not tuning. The packet disclosed it openly. If the Architect's separate answer says "loaded throughout",
D2 fails property 1 and that answer governs.

## Trajectory claims, verified independently

These are from my own dump of both runs on the snapshot, not from the evidence file. They match
`trajectory-d2-5min.txt`.

| Claim | Observed |
|---|---|
| Baseline 2.95 kWh in 04:00-05:00 UTC | 2.950 (0.100 at 04:45 + 2.850 at 04:50); 05:00 3.044; 06:00 6.088; 07:00-10:00 0 |
| Reserve 25: 0 kWh in H | 0 in every hour; requested STARTING 04:50 (SOC 29.95 %), RUNNING 04:55 |
| Minimum SOC 30.00 % / 25.16 % | 30.0 / 25.157894... (478/19); neither below its own reserve |
| Avoidable morning after the clearing | Baseline RUNNING at offset >= 240 with generator 0 and `pv_to_load == load_demand`; end SOC 86.8 % (below the 90 % stop) |
| Transitions >= 20 min from midnight | Baseline 03:00 / 03:05; reserve 25 04:50 / 04:55 |

H = 04:00, not the expected 05:00. The baseline first reaches 30 % at 04:45-04:50. The packet records this as a
deviation, and it is a design note, not an assertion target.

## Honest-result checks

- **Values against D2:** SOC 34; fuel 300 L; STOPPED; `irradiance-1` 30 W/m2 for 0/240; `irradiance-2` 800 W/m2 for
  240/240; residential 4 kW, clinic 2 kW, mill 0 kW, each 0/480; `scenario_version` 1; `version_valid_from`
  2026-10-01; no `supersedes`; `display_name` as the sheet gives it. These match exactly.
- **Diff against reserve-trial:** a field-level diff against `kobo-mini-grid-reserve-trial.yaml` shows only these
  value, offset and duration changes, plus the text. Structure, roles and `state_key`s are identical.
- **Untouched files:** `git diff --stat ca6d7d61b..956fc3fde` touches 13 files. In `config/` the only change is one
  added scenario. The backend test diffs add lines and change only the 13 -> 14 count, which is the single deletion.
  Nothing under prices, SFC, profiles, `config/site-templates`, verification or the cost check is touched.
- **Existing digests:** the pinned dict only gains an entry. `test_every_shipped_scenario_matches_its_pinned_fingerprint`
  passes, so every existing digest still matches.
- **Physical plausibility:** 30 W/m2 on a 60 kW array gives 1.8 kW (`pv_to_load` 0.15 kWh per 5 min). A steady 6 kW
  residential-plus-clinic load, a 34 % starting SOC after the night, clearing to 800 W/m2 at 10:00 local, and a
  300 L tank are all plausible for a rainy-season morning at Kobo.
- **Generated test data:** the file states "Demonstration values designed for a client demo story, not a
  recommendation for any real site", and it names no Site (`test_no_shipped_scenario_names_a_site` passes). The
  "Generated test data" label comes from the existing Lab-run provenance path, which the frontend sources show; this
  slice does not change it. The label was not observed on a live run, because U3 is out of scope.

## Do the checks really fail? Planted breaks, in memory

| Property | Planted break | Result |
|---|---|---|
| 1 | Baseline run with reserve 20 | FAILED: "no whole hour before the clearing with the baseline generator loaded" |
| 2 | The reserve-25 run replaced by the baseline | FAILED: (4, 2.95) |
| 3 | The baseline label given the reserve-25 trajectory | FAILED: (None, 478/19) |
| 4 | `CLEARING` = 10000 (and, separately, baseline reserve 20) | FAILED both |
| 5 | Run start moved to 23:50 UTC | FAILED: (None, 5) |

All five can fail.

## Checks run

- `pytest host/tests/test_scn_reserve_matters.py backend/tests/test_scenario_fingerprints.py
  backend/tests/test_run_binds_scenario_to_site.py host/tests/test_mini_grid_v5.py -q` on the snapshot:
  **63 passed in 15.62s**. This matches the packet's 63.
- `tools/check-architecture.ps1`: passed. On the git-less snapshot it printed "not a git repository" notes, so I
  reran it in the worktree at `956fc3fde` with a clean status, and it passed there too.
- `tools/check-agent-workflow.ps1`: passed, in the snapshot and in the worktree.
- `git merge-tree` against `89280952d`: conflicts (M1).

## Not verified

- The full backend suite and `tools/select-tests.py`. The packet says neither was run, at the coordinator's
  direction. `config/` changes may select the whole suite at the merge gate (§3).
- The frontend suite and build. They are not relevant: this slice has no frontend change.
- U3 (the real chain, the Finding, verification and the cost check). It is out of scope by design.

## Residual risk not already named in the packet

- The baseline's 12.08 kWh is mostly battery recharge in 5-minute bursts. Only about 2 kWh of it serves load. The
  "lever" in U3 is therefore small, and how the dispatch assessment classifies the sawtooth runtime (loaded or
  avoidable) on the real chain is untested.
- Moving the fixed `window_hour` to 04:00 means DEMO-SPARSE must use "04:00", not the sheet's expected "05:00". The
  sheet's consumption step already writes "04:00", so this is consistent. Check it again when U3 runs.
