# DD-1a2 handoff

## State: rulings in (`DD1a2-R`, sheet `:717`), owner-independent items committed; waiting on two owner answers
Size 2.25. Do NOT start the scenario files, v3 or G0/G1/G2 until the coordinator relays the answers.

**Done**
- `6a75592d2` Q7: 5 files removed (`kobo-night-{late,late-after-overcast,early-after-overcast}`, `kobo-steady-{afternoon,dusk}`). `derive.WITHDRAWN`/`REMOVED`: `--check` fails if one reappears. Their `NIGHTS`/`STEADY`/`HELD_UNUSED` entries stay: `probe_kobo_nights` renders them in memory, so the handover JSON is unchanged (`--check` current). Stream probe Day A now uses `kobo-mill-midday` + `kobo-rest-mill`.
- `4f41af404` Q8.4 (`_entry`, Kobo `degraded` always held), Q4 (`plan_add_day` `LATE_IN_STREAM`), Q6 (`sd.apply_baseline`, `prepare --baseline b16`), `sd.uncovered_weekdays` (reported in prepare).
- Mutation proofs: each of the four guards failed its test or `--check`, reverted.

**EV entry: not in a shipped list yet.** It belongs to v3 (barred for now), and the ruling keeps v1 and v2. `S-14d normal` is proved on a test list (`_baseline_doc`, 3 Tuesdays on every weekday of S, 4th reported). Add it as the EV line of v3.

**Next, once answered**
- Un-hold `kobo-steady-day` under Q1 (b): remove it from `HELD_UNUSED`, regenerate. Check first that no handover probe hashes it.
- Add `kobo-steady-before-mill`, `kobo-rest-before-mill`, `kobo-night-early-after-before-mill`; v3 per the sheet's table (`:788`), `mill_change_day`, `MILL_PROFILE_WRONG_SIDE`; `ADD_DAY_KINDS` gains; add-day expands via `_expand` (+0.25); list-level join guard (sheet `:867`).
- G0, files, v3, G1, R25 probe, G2 (`tools/dd1a2_mill3_dry_run.py`), scoped tests, guards, packet.
- When v3 exists: Q6 L0 asserts the real MILL-3 days under b16 (today a test list), `test_r10_...` covers v3 through `DEFAULT_FILE`.

**Anchors**: `tools/demo_story_days.py` `_entry`, `_expand`, `plan_add_day`, `apply_baseline`; `tools/derive_steady_scenarios.py` `WITHDRAWN`, `HELD_UNUSED`, `rest_document`; `tools/probe_kobo_nights.py` `full_days`, `dusk`; `backend/assetops_backend/actions/verification_families.py` `assess`.

**How to run**
- PYTHONPATH absolute Windows paths, or imports hit the stale editable install. `run-host-tests.ps1` prepends only the packages, so set `tools;backend\tests;host\tests` in `PYTHONPATH` first.
- Own DB: `assetops_dd1a2_test`, created and dropped around each run.

**Checks at `4f41af404`**
- L0 `test_demo_story_days` + `test_demo_combined_finish_co1` + `_links`: 71 passed. `derive --check` and `probe --check` current.
- Host: stream probe + registered Kobo, 4 passed, 179 s, own DB (dropped).
- Guards: architecture, agent-workflow, navigation-truthfulness pass. `check_v69_ledger.py` and `test_mock_deviation_labels.mjs` pass. I could not find the definition of "V" and "M" and ran those as my best reading; confirm them.
- `missing-claim-scan.mjs`: not run, precondition missing: `MODULE_NOT_FOUND`, this worktree has no `frontend/node_modules`. No frontend file changed here.

DBs and processes alive: none.
