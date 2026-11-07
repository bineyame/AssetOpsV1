# Review K1a: `mini-grid` v7, the tank-level signal

- Reviewer: fresh Claude reviewer (independent; did not author the slice). 2026-11-07.
- Branch `task/DIESEL-K1a-minigrid-v7`, worktree `AssetOpsV1-k1a`, reviewed at `864b2d9fd`. Diff `b5b3e7f03...HEAD`: 6 files (packet, `profiles.py`, `execution_adapter.py`, `host/tests/kobo.py`, new `host/tests/test_mini_grid_v7.py`, `mini_grid.py`).
- Judged against: `.agent/build-sheet-DIESEL-1.md` §9.2 (K1a card), with §9.1, §9.3 and §9.4 for context.

## Verdict: ACCEPT

There are no High or Medium findings. Every item on the K1a card is met. I re-derived the v1-v6 byte-equal claim myself on a clean export of the base commit rather than taking it from the packet.

## Checks run (by me, on this revision)

Python: `AssetOpsV1-plan2\.venv`, with an absolute PYTHONPATH under the k1a worktree. Imports were asserted to resolve into the worktree: `assetops_simulator`, `assetops_backend` and `execution_adapter` all live under `AssetOpsV1-k1a`.

- `host`: `pytest tests/test_mini_grid_v7.py tests/test_kernel_conformance.py tests/test_mini_grid.py tests/test_mini_grid_v6.py -q` gave **74 passed** (70 s). The packet's 116 also included v5 and v2. I did not rerun those two, because they are untouched v5/v2 tests and the v5 pin covers v5.
- `backend`: `pytest tests/test_component_properties.py tests/test_addressed_bindings.py -q` gave **184 passed**, which matches the packet.
- **Independent digest proof.** I exported `b5b3e7f03` with `git archive` into the scratchpad. The tree excludes `frontend`, `Docs`, `.agent` and `.ai`. I ran the builder's `k1a_digests.py` against that export, where its ROOT assertion forces imports into the export, and against the k1a worktree. The two 9-line outputs are **byte-identical** (`diff` is empty), and both equal the packet's table verbatim. That covers daytime/1, mini-grid/1-6 on the Lab v3 path, and mini-grid/5-6 on `registered-kobo-publication` v5.
- **F0 probe v7 against the real v7.** I loaded `main:tools/probe_kisiwa_fuel.py` (`probe_v7()`) and compared its output with the real `MINI_GRID_V7_MODEL` objects, with `PYTHONHASHSEED=0`:
  - simulator `==` True, product profile `==` True;
  - `repr` equal for both, with sha256 prefixes sim `2d6972b11025e17b` and profile `722b13c6b236dddb`.
  - The only object that is not identical is the restated `fuel-tank-volume-stock` handler. Both sides build it with their own `replace(...)`, it is equal in value, and that is expected. `fuel.SAMPLE_HANDLER` is the same object on both sides.
- Not run, by instruction: the full suites, any DB, guards (the packet's `check-all` 15/17 with 2 env-only `typescript` failures is cited, not re-verified), and the frontend. There is no frontend change.

## Card items

1. **The v7 shape.**
   - Simulator, `mini_grid.py:1265-1298`: `replace(V6, version 7, statement + V7_SENTENCE, handlers = V6's with the stock handler restated + (fuel.SAMPLE_HANDLER,))`. The sampler is imported as an alias rather than copied, and the test asserts it with `is`, at `test_mini_grid_v7.py:81`.
   - The stock handler is restated through `replace` of the v6 object. The test proves `replace(v7_stock, statement=old) == v6_stock`.
   - Product profile, `profiles.py:1375-1397`: the roles are `{CAUSAL_INPUT, REPORTED_OBSERVATION}` with the restated statement, and the other states are equal to v6's.
   - v7 is appended after v6 in `MODEL_PROFILES` (`:2203`) and in `EXECUTABLE_MODELS`.
   - There is no publication-profile, mapping, binding, Kobo (`tools/demo_combined_kobo.py`), frontend or migration change.
   - Two duplicate rules hold: the new `(fuel-tank-volume, REPORTED_OBSERVATION)` pair and the new handler id `fuel-tank-volume-state-signal` are both unique.
2. **v1-v6 byte equality.** Proven above, independently. The proof is sound for three reasons:
   - v1-v6 objects are not rebound or mutated. They are frozen dataclasses, and v7 is built only with `replace`.
   - Every consumer that could observe the new entry resolves the model by exact `(id, version)`: `model_for` at `execution_adapter.py:178-183`, `find_model_profile` in `provenance.py:665` and in Kobo's replay, and the run-setup refusal of "latest" at `parsing.py:372` and `service.py:852`. No caller takes `max(version)` or "the last mini-grid".
   - `host/tests/kobo.py` takes the first match by version, so `None` still gives v1.
   - The Lab catalogue grows by one row. `test_runs_api.py:97` reads index 0, which is unchanged. The frontend auto-selects only when there is exactly one profile (`RunSetupFrame.tsx:347`).
3. **Kobo stays on v6.** The replay resolves its model from the manifest: `backend/conversions/d-verification-window-v3.json:20-22` pins `mini-grid` 6, through `host/tests/test_s6_verification_replay.py:140-146`. v6 does not report the tank level (`reports` is False), so `fuel-level` is still dropped at `reporting_inputs`. The registered v6 run's `n_obs=1100` and its observation digest are byte-equal, and `test_v7_and_v6_share_one_physics...` asserts that v6 carries no level signal. Kobo still stores 0 `fuel_level` rows.
4. **The tests bite.** I mutated nothing, by instruction. By construction, each defect below would fail a named test:
   - sampler dropped or copied: `:73`, `:81`;
   - product role missing: `:100`, `:109`;
   - v7 missing from either catalogue: `:68-69` raise `ValueError`, and `model_for` refuses;
   - sample leaked into v6: `:76`, plus the v6 content digest, because `state_samples` would change;
   - a v7 physics change: the boundary-by-boundary parity at `:197-205`;
   - a bias or cadence error: `:167-170`, `:183`.
   
   The level test guards against vacuity: `reported > 0` and "the tank moved". The packet's own mutation shows the v6 pin is non-vacuous (doubling v6's charge request failed it), and it honestly records one mutation that did not move any digest, explaining why.
5. **F0 probe equivalence.** Re-checked above: equal in content, `==` and `repr` both under `PYTHONHASHSEED=0`.
6. **Regression risk** to Kobo, the Lab and existing runs is none observed. `git diff --stat b5b3e7f03 main` over the five touched code paths is empty, so main's 29 later commits do not overlap the changed files.

## Findings

High: none. Medium: none.

**Low 1 (preference, not an acceptance gap): `host/tests/test_mini_grid_v7.py:92` checks the old stock sentence on v1, v5 and v6 only.**
- v2-v4 are not checked.
- Failure scenario: someone rebinds v3's handler table to v7's restated handler. That would not change any digest, because handler statements do not enter the trajectory, and this test would not notice.
- Today v2-v6 share the v1 handler through `replace`, so the risk is theoretical.
- Fix, if wanted: iterate all six versions, as `:74-76` already does.

**Low 2 (residual, not K1a's defect): the F0 evidence line goes stale.**
- After merge, the line in `tools/probe_kisiwa_fuel.py:281` reads "product code has no v7 until K1a merges". It stays true as history but reads stale.
- The probe keeps using its local copy, which is content-equal, so its `--check` output is unaffected.
- Nothing to fix in K1a. K1 already plans to use the real v7 (main's K1 notes).

## Process deviations (disclosed by the builder; non-blocking)

- **`Tee-Object` scratch write.** The worktree is clean (`git status` is empty), and no scratch artefact is committed. The digest script and its outputs live only in the session scratchpad. This does not matter for the slice.
- **Task-status docs unchanged.** No DIESEL/FUEL unit is tracked in `tasks/README.md` or `.ai/ACTIVE_CONTEXT.md` on this base. The build sheet and the coordinator handoff are the sprint's tracking surface, so leaving them unchanged is consistent with practice. The coordinator should record K1a's merge in the handoff.

## Residual risk (beyond the packet's)

- The first consumer that stores `fuel_level` through the gateway is K1, and this unit does not exercise it, as the packet says. One further point: v7 appends the sample handler last. Any future code that looks up "the" `fuel-tank-volume` handler by `state_key` alone will still find the STOCK handler first. Nothing does that today, so this is only a note for K1/K3 builders.
- Cold and EV byte stability is not pinned in this slice. It is unaffected by construction, because they execute through their own packs and the only shared edit appends to two tuples.
