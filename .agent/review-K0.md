# Review: K0, the operational-action bridge (DIESEL-1-R3 §9.3, §9c.3 items 1 and 4, §9f R3f, §9i R3i)

- Reviewer: Claude (Opus), independent first review, fresh context. Not the author.
- Branch `task/DIESEL-K0-action-bridge`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k0`, reviewed at `72998296d`. Diff `git diff main...HEAD` (20 files).
- **Verdict: ACCEPT.** There are no High or Medium findings. Two Lows follow. Each is a spec'd rule with correct code but no test that bites, so they are optional hardening on the branch and do not block the merge.

## Findings

### L1 (Low): the `site_code` arm of `OPERATIONAL_ACTION_LOG_MISMATCH` has no test
- **Where:**
  - `backend/assetops_backend/runs/operational_actions.py:232-233` holds the check (`or document["site_code"] != request.site_id`).
  - The only MISMATCH producers are `backend/tests/test_k0_operational_actions.py:369` (inner `log_version` 2) and `:495-498` (file name v2). Neither one changes `site_code`.
- **Evidence:** mutation M5 deletes the `site_code` clause on a scratch copy. All 65 non-DB K0 tests still pass.
- **Failure scenario:** a later edit drops or breaks the clause. A log whose inner `site_code` is `KOBO-001` but whose file is named for Kisiwa then freezes its fuel effects into a Kisiwa run with no refusal, and no test fails. §9f.1 ("builder-resolved items") rules that MISMATCH also covers this case.
- **Fix:** one more `refused(MemoryLog({**log_document(), "site_code": "KOBO-001"}), k=2).kind == "OPERATIONAL_ACTION_LOG_MISMATCH"` assertion.

### L2 (Low): the Q5 order (`at`, then `action_id`) is not exercised by any run with two effect-bearing actions
- **Where:** `backend/assetops_backend/runs/operational_actions.py:263-264` sorts the effect-bearing actions. That order drives:
  - the OVER_CAPACITY and OVER_STOCK running sums (`:265-282`);
  - cause order;
  - the `intervention_history` order;
  - `operational_action_log.actions`.
- **Evidence:** mutation M1 adds `reverse=True` to the sort. All 65 non-DB K0 tests still pass.
  - The shipped log selects at most one effect-bearing action per run, so no test can observe the order.
  - The parser's cross-check (`parsing.py:556-558`) compares the history with `log.actions` in their shared order, so it would accept a consistently wrong order.
- **Failure scenario:** a future log, or a K7 day, puts a delivery and a removal in the same run. A wrong or unstable order then:
  - changes `intervention_history`, and with it the trajectory identity;
  - can make OVER_STOCK miss or spuriously refuse a removal that follows a same-run delivery ("earlier deliveries" depends on the order).

  No test fails.
- **Fix:** one L0 test over a modified log with two effect-bearing actions in one run. Order them out of `at` order in the file, and add a same-`at` pair to exercise the `action_id` tie-break. Assert:
  - the history order;
  - that a removal larger than the initial stock is accepted only after an earlier delivery.

No other findings. I looked for more and found none.

## What I verified, item by item

**1. Byte-equality.**
- `d782fc09f` is the branch's first commit and touches only `backend/tests/k0_byte_equal_pins.py`. The production edits begin at `dd4a3874f`.
- `git diff d782fc09f HEAD -- backend/tests/k0_byte_equal_pins.py` changes only the deviation-1 docstring sentence. No pin value has moved.
- All 27 parametrised `test_a_run_with_no_actions_is_byte_equal_to_its_pin` cases pass on my run. They pin the render, `run_identity_sha256`, the causes and the trajectory digest. The Cold and EV `run_identity_sha256` are among them.
- The same test asserts that `"origin"`, `"action_ref"` and `"operational_action_log"` are absent from every scenario-only render.
- `git diff --name-only main...HEAD` holds nothing under any of these: `contracts/`, `simulator/`, `host/execution_adapter.py`, any `trajectory` file, `frontend/`, `.agent/DIESEL-F0/`, `tools/probe_kisiwa_fuel.py`.

**2. Frozen fields.**
- `origin` and `action_ref`, with `check_cause_origin`, exist only on `FrozenCause` and `FrozenReportingPathCondition` in `B/runs/models.py`.
- `FrozenOperationalAction`, `FrozenOperationalActionLog` and `DeterministicIdentity.operational_action_log` (last, default None) follow §9f.2 (1).
- `FROZEN_INPUT_ANSWERERS` includes `OPERATIONAL_ACTION`.
- Provenance reads only `identity.operational_action_log` (`provenance.py` `_answered`, plus the log row).
- `intervention_history` holds only the effect-bearing actions:
  - run 6, which has only the seal, the sensor fix and the dips, freezes an empty log and an empty history;
  - runs 2 and 4 each equal `probe-result.json` `runs[k-1].intervention_history`.

**3. Refusals.**
- All 11 kinds are in `refusals.py`, each with a comment.
- UNIT and EVENT_ID_CONFLICT carry the R3i deviation-5 comment, verbatim.
- `operational_action_refusals()` produces each kind with `store.written == []`.
- `test_run_setup`'s `produced == RUN_SETUP_REFUSAL_KINDS` passes.
- Covered:
  - spans outside the run (window too long, sensor span before the start, sensor span past the end, off-minute `at`);
  - the unsupported path (legacy, Cold, EV);
  - LOG_MISMATCH through version and through file name (see L1 for `site_code`);
  - `CAUSE_ORIGIN_INVALID` through the 4 model cases × 2 records and the 9 parse mutations.

**4. Wiring.**
- `runs/composition.build_operational_action_log()` returns `YamlOperationalActionLog()`.
- `main.py` imports only the composition function and passes it at the `build_simulator_lab_router` call.
- Test 10 builds the real `create_app(...)` with no injected port. On my run the POST returns 201 with three `OPERATIONAL_ACTION` rows, on memory and on `assetops_k0_test`.
- `load_yaml_text` is the only `yaml.load(` call in `B/runs/adapters`. The operational-action adapter calls it and maps `yaml.YAMLError` to `OperationalActionLogUnavailable`.
- Guard rule 7 (`tools/checks/configuration-persistence.ps1`) is unchanged on the branch. It counts lines that match `=\s*yaml\.load\(...Loader=CSafeLoader\)`.
- So `document = yaml.load(...)` followed by `return document` is a real fix, not a dodge: it is still one load call with one loader, at the one load point. A bare `return yaml.load(...)` would hold the same policy but would make the guard count 0 and fail. Keeping the counted form keeps the guard meaningful.

**5. The action log.**
- `git rev-parse HEAD:config/operational-actions/kisiwa-001-operational-actions-v1.yaml` and `main:.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml` are the same blob, `d7ac1cc58f33…`.
- `git check-attr eol` reports `lf`.
- sha256 of both the working file and the blob is `77777c82…b634`, which equals `probe-result.json:8` `actions_sha256`.
- `test_no_product_module_names_the_operational_action_directory` passes. M10 (no newline normalisation in the adapter) makes the CRLF test fail.

**6. F0r per-step parity.**
- `test_the_kernel_moves_the_tank_exactly_as_f0r_did` passes on memory and on `assetops_k0_test`.
- It chains runs 1–4 and checks:
  - `found == expected` against F2 `non_generator_steps`;
  - run 4 at steps 120–128, each `40/3`;
  - run 2 per the evidence, step 227, −300;
  - each run's start state and history against `probe-result.json`.

**7. Deviations 1–5, all as ruled.**
1. The EV pin is seeded under `seeded_uuid4()` and was already in the first commit. The docstring carries the R3i sentence.
2. Test 1 is in `host/tests`.
3. The loader takes the `component_ids` keyword.
4. `test_a_run_naming_a_log_covers_every_identity_field_with_no_exclusion` asserts `covered == declared` for a run that names a log.
5. The UNIT and EVENT_ID_CONFLICT comments are in place, and both kinds are produced by direct loader calls.

**8. Test strength.** I ran these mutations on a scratch `git archive` copy, never on the worktree:

| # | Mutation | Result |
|---|---|---|
| M2 | OVER_CAPACITY `>` → `>=` | killed |
| M9 | drop the legacy (`selection is None`) arm of UNSUPPORTED_PATH | killed |
| M10 | adapter reads bytes, no newline normalisation | killed |
| M11 | drop the EVENT_ID_CONFLICT check | killed |
| M12 | parser accepts a stored `origin: SCENARIO` | killed |
| M13 | always write an `operational_action_log` key | killed |
| M1 | reverse the effect-bearing order | **survived** (L2) |
| M5 | drop the `site_code` mismatch clause | **survived** (L1) |

The packet's own non-vacuity proof (rendering origin for SCENARIO breaks the fuel-loss-event pin) is consistent with the pin set: that scenario carries 2 causes and 1 condition.

**9. Process deviations (noted, not blocking).** The builder disclosed three:
- a Bash heredoc append to the packet;
- a polling loop, later stopped;
- a tail-piped check-all output.

## Checks I ran

All used the plan2 venv python, with PYTHONPATH set to the K0 worktree. I confirmed the imports resolve to `AssetOpsV1-k0`:
- `assetops_backend`
- `assetops_contracts`
- `assetops_simulator`
- `execution_adapter`
- `probe_kisiwa_fuel`
- `kisiwa`

| Check | Result |
|---|---|
| `test_k0_operational_actions.py` + `host/tests/test_k0_kisiwa_actions.py` + `test_run_setup.py`, no DB | **153 passed, 2 skipped** (the postgres params), 15.5 s |
| `host/tests/test_k0_kisiwa_actions.py -k "kernel or lab_api"` on `assetops_k0_test` | **4 passed**, 21.4 s |
| Adjacent, no DB: `test_runs_api`, `test_run_store`, `test_run_store_loader`, `test_w202_cold_run_identity`, `test_w205b_ev_scenarios`, `test_simulator_lab_gate`, `test_k1_kisiwa_fixtures` | **271 passed**, 54.9 s |
| `tools/check-architecture.ps1` with `ASSETOPS_GUARD_PYTHON` set to the plan2 venv | **"Architecture check passed."**, exit 0 |

- The Postgres run used `ASSETOPS_TEST_TEMPLATE=0`, so the harness reset that one database in place and created no template or clone databases. Free RAM was 3.66 GB before and 3.59 GB at the DB step.
- Mutations: 8 runs on the scratch copy, as listed above.

## Not verified by me
- The estate-guard self-tests (about 23 min) and a whole `check-all.ps1`. The packet records the self-tests passing (15) after the fix. It says check-all was not re-run whole after the load-line fix.
- `mypy`, which §9f.4 asks for. It is installed in neither venv (packet), and I did not run it.
- `ruff`: I did not re-run it.
- `test_run_binds_scenario_to_site.py` (DRIFT-RB1, main drift): not re-run, out of K0's scope by R3i.
- The full suite: not run, by instruction.

## Residual risk (beyond the packet's)
- Actions are selected by `at` alone. A removal whose `at` falls just before a run's start, but whose window reaches into the run, is not selected, so its tail is silently absent from that run. The spec rules this ([start, end) on `at`), and the shipped log does not hit it. K7 should keep actions inside a single run's day.
- `provenance._answered` uses `next(...)` with no default. It relies on the parse cross-check and the setup self-assert to guarantee that the action exists. That is sound today, but a future path that builds a `DeterministicIdentity` without either check would raise `StopIteration` rather than give a typed error.
