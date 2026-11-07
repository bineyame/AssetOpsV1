# Review packet K1a: `mini-grid` v7, the tank-level signal

- Ruling: DIESEL-1-R3 §9.2 (`.agent/build-sheet-DIESEL-1.md`, commit `b5b3e7f03`). Branch `task/DIESEL-K1a-minigrid-v7`, worktree `AssetOpsV1-k1a`, from main `b5b3e7f03`.
- Commits: `2f054857c` (code), `1a4d3b5c5` (tests), plus this packet.
- Pre-flight: the K1a section was complete enough to build from. Every anchor it names was checked against the code: the STATE_SAMPLE rule in `S/kernel/model.py:396-400`, the inline stock handler `mini_grid.py:192-207`, `fuel.SAMPLE_HANDLER` (`fuel.py:207-221`), the `fuel-tank` relation, the product profile v6 `:1359-1367`, `MODEL_PROFILES`, `EXECUTABLE_MODELS`, the `kobo.py` tuple, and the host drop `execution_adapter.py:734-739`. One duplicate check also passes: the sample adds a new `(fuel-tank-volume, REPORTED_OBSERVATION)` pair and a new handler id, so `ModelSpec.__post_init__` accepts it. No questions were left open.

## Outcome delivered

- Simulator, `simulator/assetops_simulator/packs/mini_grid.py`:
  - `MINI_GRID_V7_MODEL = replace(V6, version 7, statement V6 + V7_SENTENCE, handlers=V6 handlers with the stock handler restated + (fuel.SAMPLE_HANDLER,))`.
  - `SAMPLE_HANDLER` is imported (as `FUEL_TANK_SAMPLE_HANDLER`), not copied.
  - `FUEL_TANK_STOCK_V7` is `replace(<v6 stock handler>, statement=<ruling's sentence>)`. The id, role, kind, floor, `consume` and `initialize` are the same objects.
  - v1-v6 objects are not edited.
- Product profile, `backend/assetops_backend/runs/profiles.py`:
  - `MINI_GRID_V7_MODEL = replace(V6, version 7, statement V6 + same sentence, supported_states=V6's with fuel-tank-volume roles {CAUSAL_INPUT, REPORTED_OBSERVATION} and the restated statement)`.
  - Appended to `MODEL_PROFILES` after v6.
- Executable: appended to `host/execution_adapter.py` `EXECUTABLE_MODELS` and to the profile tuple in `host/tests/kobo.py`. The `next(...)` there still resolves `None` to v1.
- No change to any publication profile, mapping, binding, Kobo file (`T/demo_combined_kobo.py`), frontend or migration.

## Files materially changed

`simulator/assetops_simulator/packs/mini_grid.py`, `backend/assetops_backend/runs/profiles.py`, `host/execution_adapter.py`, `host/tests/kobo.py`, new `host/tests/test_mini_grid_v7.py`.

## Acceptance (§9.2 K1a card)

| Criterion | Status |
|---|---|
| v7 `reports("fuel-tank-volume","STATE_SIGNAL","L")` is true; v6 (and v1-v5) false | PASS `test_v7_reports_the_tank_level_and_v6_does_not` |
| v7 advertised supported states equal the product profile's (parity pattern) | PASS `test_v7_advertises_what_the_product_profile_declares` (state, scope, role triples) |
| Sampler reused, not copied; stock sentence restated for v7 only; V7 sentence on both sides | PASS `test_v7_reuses_the_fuel_pack_sampler_and_adds_nothing_else` (`is fuel.SAMPLE_HANDLER`), `test_the_stock_sentence_is_restated_for_v7_only` |
| Kobo-template run on v7 with `registered-kobo-publication` v5's fuel-level signal: 15-minute tank observations = stock at the instant - 0.5 L before noise | PASS `test_v7_publishes_the_tank_level_every_15_minutes_as_the_stock_less_half_a_litre`. Registered KOBO-001 over `InMemoryFoundationStore`, prolonged scenario, 2026-10-13 03:00-11:00Z, 5-min step. The signal is a STATE_SIGNAL in L with bias -1/2. Due offsets are 0,15,...,480. Each REPORTED value = `quantize_half_even(stock - 1/2, resolution)`; the rest are DROPPED. The test asserts the reported set is non-empty and the tank level actually moves. |
| Same document on v6: identical generator, battery and tank trajectory except the sample | PASS `test_v7_and_v6_share_one_physics_and_differ_only_by_the_sample`. Per boundary, the v7 boundary with the tank sample removed equals the v6 boundary. Applied events, bounded transitions and outcome are equal. v6 has no fuel-level reporting path, and v7's signals are v6's plus fuel-level. |
| Byte-equal pins: one v6 Kobo run digest, one v5 run digest | PASS `test_a_v6_registered_kobo_run_keeps_its_digests`, `test_a_v5_lab_run_keeps_its_digests` (values computed on main `b5b3e7f03`) |
| Kobo stays on v6, publishes no tank level | No Kobo file edited; v6 drops fuel-level as before (asserted above) |
| No publication-profile / mapping / binding change | None changed (diff limited to the 5 files above) |

## v1-v6 digest byte-equal proof

Script: `k1a_digests.py` in the scratchpad (not committed). For each run it prints the trajectory `content_digest` (with `run_id` fixed to `k1a-fixed-run-id`, because a Draft mints a uuid run_id), the trajectory `inputs_identity` (run identity), and the `observation_series_digest`.

Method:
1. Commit the change.
2. In the worktree, `git checkout b5b3e7f03 -- <the 4 changed files>`. `git diff --stat b5b3e7f03` was empty. Run the script twice; the two runs were identical.
3. Restore with `git checkout HEAD --` and run the script on `2f054857c`.

All 9 lines are identical before and after:

Each line is `run | trajectory content_digest | inputs_identity | observation_series_digest | n_obs`. The script output is copied verbatim:

```
daytime-mini-grid/1 kobo-daytime lab-v3 | 784b98cb5e02d4c18636b9f6e86eface36d55357bcb8d0ea7e4a68a63d2067cc | 295bcb34edc52ad25721929f0a6be2b3eee0085e78e0f183f082158928a8551a | ff9520f4a0a38d5696a2e5d5b70f1c3cf0642ef87bd3ffb2443f4b5cecacd3ac | n_obs=294
mini-grid/1 reserve-trial lab-v3 | a113ac2310ca2e99e183f6f4f188fade3188f46d3572945641f647310d453b31 | 000f7043c5371f4b11135e60ff1c39172671827fe569cb5996034997ba459271 | 8f30673ac053643a221a32d811d2679188b62e4d6045e35d2586923a8ab903cc | n_obs=198
mini-grid/2 reserve-trial lab-v3 | 820edc97d5d3f4e33ab536e70689af43ec71bc9b524ef75f4a383ae2fc086867 | e95ddf6295558c83e8b72b43a4a4546a10c8dfbc9b3eb24cf104b06438214bbd | ee83becde77bc74539aef998d14b80268f2f37dd226bf5d57a4176173b43fb98 | n_obs=207
mini-grid/3 reserve-trial lab-v3 | a5710a0bd6d59e53650ae2fa0ec986070f66971a5a539768773495891e02a9c4 | ac8f414869cd78a5581c5e0fec0472e76cbcf3f16efcb67a335cacdaf1df4f46 | ee83becde77bc74539aef998d14b80268f2f37dd226bf5d57a4176173b43fb98 | n_obs=207
mini-grid/4 reserve-trial lab-v3 | 9ba18d983a062829f2fa20e863950315ca5b23bd5c1b809e0bc45fdd6cb0e96c | ff5a08dc1449c1689e65893ab2d7c4b0541200ba025d031cd7c9cc106b078801 | ee83becde77bc74539aef998d14b80268f2f37dd226bf5d57a4176173b43fb98 | n_obs=207
mini-grid/5 reserve-trial lab-v3 | 6c49e7c00e75d0ac465134a6d996133ea73df2b492858cd3bf30996ddddf84a5 | 5c79b256e104e2ec23da0c2e6da788f3e1dd47ccabd01e67f110ae6a7dc349da | ee83becde77bc74539aef998d14b80268f2f37dd226bf5d57a4176173b43fb98 | n_obs=207
mini-grid/6 reserve-trial lab-v3 | 6b7dc8b00883cedad64d511ac06f5504660a7222605c31f0628b7da82387b9f3 | 2d96f202f7d162f79725320d9ef108d6ae7fe9aa3c45c0c38e2dee6efed66ec7 | ee83becde77bc74539aef998d14b80268f2f37dd226bf5d57a4176173b43fb98 | n_obs=207
mini-grid/5 prolonged registered-v5 | 7e6db2d7d925c165a451dc578611cb0f40ac9912e9d1d3fea59a55fe063d10d1 | 71e2b5371dcdf2c91381a97d6fef46c0ad6e20a44a3077e1fc21d61b00cf1859 | bc9989c23afda6bf0ced1600ad0f4f6b5004c293cd62a0e19cc1fdf4374e7cc9 | n_obs=1100
mini-grid/6 prolonged registered-v5 | b0d800f360e035a9fa150c21f1fc6671b104b7df97a610dd742363cc8ebce24f | c703db7f803806f30e36183af9eb995f03fcbddae832bc55452520212a5ada92 | bc9989c23afda6bf0ced1600ad0f4f6b5004c293cd62a0e19cc1fdf4374e7cc9 | n_obs=1100
```

"registered-v5" means `registered-kobo-publication` v5, Kobo's own route. The mini-grid/5 lab line and the mini-grid/6 registered line are also pinned in `host/tests/test_mini_grid_v7.py`.

Non-vacuity of the pins, run on committed work and reverted with `git checkout --`: doubling the v6 charge-request measurement in `resolve_v6` made `test_a_v6_registered_kobo_run_keeps_its_digests` FAIL (1 failed, 8 passed), and the v5 pin stayed green as expected. An earlier mutation, dropping the charge state from v6's `measured_interval_states`, did not change any digest. That is correct: that set gates only `reports()`, and the registered binding has no charge-request reading on that day. It is recorded so the reviewer does not take it as evidence.

## Checks run

- Imports resolve into the worktree. Asserted in the script, and printed under pytest for `assetops_simulator`, `assetops_backend`, `assetops_contracts` and `execution_adapter`.
- `host`: `pytest tests/test_mini_grid_v7.py test_mini_grid_v6.py test_mini_grid_v5.py test_mini_grid_v2.py test_mini_grid.py test_kernel_conformance.py`: **116 passed** (83 s).
- `backend`: `pytest tests/test_component_properties.py tests/test_addressed_bindings.py`: **184 passed**.
- Guards: `tools/check-all.ps1 -Python <plan2 .venv>`: see "Guards" below.
- Not run, by instruction: the full suites, prepare, `test_demo_combined_postgres`, and any DB (no K1a test needs one).

## Guards

GUARDS_RESULT

## Known deviations

- None from the ruling.
- The ruling's test text says "Kobo-template run". It uses the registered KOBO-001 basis (the Kobo template, imported and converted over `InMemoryFoundationStore`, `test_s2_registered_basis.converted()` plus the S3/S6 demo configuration), because `registered-kobo-publication` v5 is only selectable on a registered basis.

## Residual risk

- The Lab model-profile catalogue gains one row ("mini-grid 7"). The served copy is otherwise unchanged; no frontend test enumerates profiles.
- K1 (Kisiwa on v7) will be the first consumer to store `fuel_level` rows. That path through the gateway is not exercised here; this unit runs in process only.

## User review

Not required: a model version with no UI change. The Reviewer gates the merge.
