# Review packet: K0, the operational-action bridge (DIESEL-1-R3 §9.3 + §9c.3 items 1 and 4 + §9f)

Branch `task/DIESEL-K0-action-bridge`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k0`, from main `8fa9540b4`.
USER_REVIEW_REQUIRED: no (Lab-only; the owner sees nothing new). **Both S5 stops resolved by ruling DIESEL-1-R3i (build sheet §9i); see "R3i fix round" at the end. Sections below describe the pre-fix state where they say S5.**

## Commits
- `d782fc09f`: byte-equal pins (`backend/tests/k0_byte_equal_pins.py`), the first commit, before any production edit.
- `dd4a3874f`: the bridge.

## Outcome
A Lab run on a registered Site can name an operational-action log, `{"log_id": "kisiwa-001-operational-actions", "log_version": 1}`. Run setup then reads the log through `OperationalActionLogPort` and freezes the effects onto the frozen records:
- a fuel delivery becomes an INCREASE POINT cause;
- an unrecorded removal becomes a DECREASE WINDOW cause;
- an unplugged sensor becomes a `fuel-level-reporting-availability` WINDOW condition.

Each frozen record carries `origin="OPERATIONAL_ACTION"` and `action_ref="{id}:{sha}"`. Each action is added to `intervention_history`, and the identity gains a frozen `operational_action_log`. Provenance labels these rows `OPERATIONAL_ACTION`.

A scenario-only run renders neither key, so it is byte-equal to its pre-K0 pins. The contracts, the host adapter, the trajectory module and the simulator are untouched (Q2).

## Files
- **Edited:**
  - `B/runs/{models,parsing,service,ports,refusals,provenance}.py`
  - `B/simulator_lab_api.py` (router keyword and pass-through only)
  - `host/tests/kisiwa.py`
  - `.gitattributes`
  - `backend/tests/test_run_setup.py`
- **New:**
  - `B/runs/operational_actions.py`
  - `B/runs/adapters/yaml_operational_action_log.py`
  - `config/operational-actions/kisiwa-001-operational-actions-v1.yaml`
  - `backend/tests/k0_byte_equal_pins.py`
  - `backend/tests/test_k0_operational_actions.py`
  - `host/tests/test_k0_kisiwa_actions.py`
- **Not edited:** `B/main.py` (see S5-a).
- The promoted log is F0's pre-registered draft, byte-for-byte: same git blob `d7ac1cc5`, sha256 `77777c82…b634`. Its header comment predates §9c.3 L1's file name and is kept verbatim (Q9).

## Criteria (§9f.4 tests; §9f.5 stops)
| # | Status | Evidence |
|---|---|---|
| 1 byte-equal | PASS | 27 pinned Drafts: Kobo, Cold, EV and 24 shipped timeline scenarios. Each pins three digests: render, `run_identity_sha256`, and trajectory where READY. No `origin`, `action_ref` or `operational_action_log` appears in any of them. Non-vacuous (proof below). |
| 2 model/parse refusals | PASS | Four model cases × two records. Nine parse mutations, including a stored `SCENARIO` origin, a history mismatch, a dangling ref and an orphan log action, all `CAUSE_ORIGIN_INVALID: `. Six malformed request keys give `REQUEST_INVALID`. |
| 3 round trip | PASS | Through `YamlRunStore`, the backend `FakeRuns` and the host `FakeRuns`. An action run keeps the fields and the log; a scenario run's stored YAML has neither key. |
| 4 setup runs 2 and 4 | PASS | The origin is a field. `event_id` is `"{id}/{effect}"` with no carrier prefix. History equals `probe-result.json` `runs[k-1].intervention_history`. The frozen log sha equals `actions_sha256`. |
| 5 eleven refusal kinds | PASS | Each one is produced with nothing written (`operational_action_refusals()`), and they are added to `test_run_setup`'s `produced` set. |
| 6 provenance | PASS | Rows exist for the cause, the condition and the log. Every other row is equal to the same run without a log. |
| 7 no-reader | PASS | Only the adapter names `operational-actions` under `B/`. Nothing under `F/src` names it. |
| 8 adapter | PASS | A CRLF copy and an LF copy give the same sha, `77777c82…`. A wrong file name gives `LOG_MISMATCH`; a missing file gives `LOG_UNAVAILABLE`. |
| 9 kernel parity (L2) | PASS (memory and Postgres) | Runs 1–4 are chained as F0r chains them. The non-generator steps equal the evidence exactly: run 2 at step 227 is −300; run 4 at steps 120–128 is 40/3 each; every other step is 0. Each run starts from F0r's exact Fraction state. |
| 10 Lab API readback | PASS (memory and Postgres) | A run is POSTed with the key, then read back with GET. It shows three `OPERATIONAL_ACTION` rows. The router is built with the adapter injected; `main.py` is not wired (S5-a). |
| S1, S2, S3, S4, S6 | not hit | S6: one EV fixture needed seeding (deviation 1). |
| S5 | **HIT ×2** | Below. |

**Non-vacuity proof.** Rendering the origin pair also for `SCENARIO` causes made `byte_equal[scenario:fuel-loss-event]` fail. The change was reverted with `git checkout`, and `git status` was clean afterwards. Only the fuel-loss-event pin carries scenario causes (2 causes, 1 condition), so that pin is what makes the guard bite.

## Stops (S5: a file outside §9f.3 is needed)
- **S5-a: wiring `main.py`.** `tools/checks/configuration-persistence.ps1` rule 1 allows only `B/runs/composition.py` to import `B/runs/adapters/*`. So `main.py:677-697` cannot construct `YamlOperationalActionLog()` itself.
  - The fix is about three lines: `build_operational_action_log()` in `runs/composition.py`, and `main.py` passing `operational_actions=build_operational_action_log()`.
  - `composition.py` is outside §9f.3, so I made neither edit. Today the composed app refuses a request that names a log with `OPERATIONAL_ACTION_LOG_UNAVAILABLE`.
- **S5-b: a second YAML load point in the run adapters.** Rule 7 of the same check requires exactly one `= yaml.load(..., Loader=CSafeLoader)` in `B/runs/adapters`, in `yaml_run_documents.py`. §9f.2 (5) asks for `yaml.safe_load`, which rule 7 bans by name.
  - The adapter uses `yaml.load(text, Loader=CSafeLoader)`, the run domain's libyaml policy. The count is now 2, so check-architecture fails.
  - Fix options for the Architect:
    - (i) a shared text-load function in `yaml_run_documents.py`, which the adapter calls. This is a file outside §9f.3.
    - (ii) the guard counts one load point per named reader module. This is a guard change.
  - I did not change the guard or work around the count.

## Checks
- **K0 tests**, Postgres on `assetops_k0_test` (created empty; harness clones): `host/tests/test_k0_kisiwa_actions.py` + `backend/tests/test_k0_operational_actions.py`. **66 passed, 0 skipped, 47.5 s.**
- **Adjacent backend tests (no DB):** `test_run_setup`, `test_runs_api`, `test_run_binds_scenario_to_site`, `test_run_execution_api`, `test_run_history_api`, `test_run_stage_api`, `test_run_store`, `test_run_store_loader`, `test_simulator_lab_gate`, `test_w202_cold_run_identity`, `test_w205b_ev_scenarios`, `test_s2_registered_basis`, `test_k1_kisiwa_fixtures`, and the K0 file. **527 passed, 12 failed.**
  - All 12 failures are in `test_run_binds_scenario_to_site.py`: `test_the_shipped_documents_were_found`, ten `test_an_owner_shaped_copy_still_parses[kobo-*]`, and `test_the_catalog_lists_every_owner_shaped_copy`.
  - The failures are `FROZEN_V1_SAMPLE` lacking about ten newer shipped kobo scenarios (`KeyError: 'kobo-rest-mill'`). This is pre-existing data drift: K0 touches no scenario or sample. It was not re-run on a main checkout.
- **Adjacent host tests (Postgres K0 DB):** `test_k1_registered_kisiwa`, `test_probe_kisiwa_fuel_band`, `test_mini_grid_v7`. **17 passed.**
- **`tools/check-all.ps1 -Python <plan2 venv>`:** 13 of 17 guards pass. The 4 failures:
  - **Architecture seams:** S5-b.
  - **Estate guard self-tests:** 3 failures. Each re-runs the architecture check on an isolated copy and reports the same S5-b message.
  - **Missing-claim scan, and its fixtures:** `MODULE_NOT_FOUND`, because the K0 worktree has no `frontend/node_modules`. This is environmental and unrelated.
  - Agent workflow passed.
- **ruff (system `ruff.exe`):** no new findings in edited production files compared with the same files on main. New production modules are clean except the repo-wide I001 convention. Test files keep the repo's `# noqa: E402` convention, as K1's tests do. `git diff --check` is clean.
- **mypy:** not run. It is installed in neither the plan2 venv nor the system Python.
- **Machine:** at least 2.5 GB free before each DB step (3.17 and 3.06 GB). One heavy step at a time.

## Known deviations
1. **EV pin.** The EV fixture's registered selection gets fresh `uuid4` mapping ids in every process, so the render differs across processes even after removing `run_id` and `created_at`. That is S6 as worded.
   - It is pinned by building that selection under F0's existing `seeded_uuid4()`, from `tools/probe_kisiwa_fuel.py`.
   - `run_id` and `created_at` are replaced by fixed literals, because `run_identity_sha256` hashes them.
   - **The Architect may rule this an S6 stop.**
2. **Test placement.** Test 1 lives in `host/tests/test_k0_kisiwa_actions.py`, not the backend file, because digest (c) needs the host's `frozen_world_inputs`.
3. **Extra loader argument.** `freeze_operational_actions` takes an extra keyword, `component_ids`, from the Site record, so the loader stays free of `sites.models`. Capacity is read from `model_needs` or from `initialization_inputs`.
4. **Extra `test_run_setup.py` edit.** One line beyond §9f.3's list: the top-level coverage test excludes `operational_action_log`, because its row exists only when a log is named (§9f.2 (4)). No existing test pinned the full `REQUEST_KEYS` message, so that pin needed no edit.
5. **Refusals that no shipped model or scenario can reach.** `OPERATIONAL_ACTION_UNIT` and `OPERATIONAL_ACTION_EVENT_ID_CONFLICT` are produced by calling the loader directly, not through a request:
   - every shipped tank is in litres;
   - scenario event ids cannot contain `/`.

## Residual risk
- Until S5-a lands, a request that names a log through the composed `main.py` app is refused (`OPERATIONAL_ACTION_LOG_UNAVAILABLE`). K7's harness path works, because `kisiwa.py` injects the adapter.
- In the delivery parity, the POINT cause at offset 1140 shows at step 227 (offset 1135), which matches F0r. This is the kernel's existing POINT convention and was not re-examined.

## Review focus
- The two S5 rulings.
- The EV pin seeding (deviation 1).
- The omit rule at `parsing.py` (cause and condition renders, and the log block).

## R3i fix round (ruling DIESEL-1-R3i, build sheet §9i)
Commits: `62960e440` (fix round), plus a follow-up for the guard-shaped load line (below). Main merged in first (`0fcfae227`).
- **S5-a:** `runs/composition.py` gains `build_operational_action_log()`. `main.py` passes `operational_actions=build_operational_action_log()` and never imports the adapter. Test 10 now drives the real `create_app(...)` (no injected router): POST of a Kisiwa run 4 naming the log returns 201, no `OPERATIONAL_ACTION_LOG_UNAVAILABLE`, readback shows the `OPERATIONAL_ACTION` rows. PASS on memory and on `assetops_k0_test`.
- **S5-b:** `load_yaml_text(text)` in `yaml_run_documents.py` is the one load point; `read_run_record` and the action-log adapter both call it. The guard is untouched. The guard regex needs `= yaml.load(`, so the body is `document = yaml.load(...)` then `return document` (a bare `return yaml.load(...)` made the check count 0 load calls).
- **Deviation 1:** EV pin docstring states the seeding fixes only ids K0 does not produce; pin values unchanged (S6 note cites R3i).
- **Deviation 4:** new `test_a_run_naming_a_log_covers_every_identity_field_with_no_exclusion`.
- **Deviation 5:** comments on UNIT and EVENT_ID_CONFLICT in `refusals.py`.
- **Not touched:** `test_run_binds_scenario_to_site.py` (DRIFT-RB1).
- **Results:** K0 tests (host + backend) 67 passed, 0 skipped on `assetops_k0_test`; with `test_run_setup.py` 155 passed, 0 skipped; 27 byte-equal pins pass no-DB and on DB; host `-k "kisiwa or kobo_run or k0"` 44 passed. `check-architecture.ps1` passed. Estate guard self-tests 15 passed (1390 s).
- **check-all** (first run, before the load-line fix): 15 of 17 guards PASS; the two failures were Architecture seams and Estate self-tests, both from the load-line shape. Both re-run individually after the fix and pass; check-all was not re-run whole (about 25 min).
