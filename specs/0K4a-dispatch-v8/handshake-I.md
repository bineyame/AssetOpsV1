# 0K4a handshake, implementer side

Implementer (Claude), 2026-11-21, pre-flight against `main` `0ead104e9` (spec base `fa13f254f`). No product code
written. Shared round with 0K4b (D-0K4.17).

Checked and as the spec says:
- The `mini_grid.py` anchors `decide` 503, `resolve` 631, `resolve_v2` 964, `resolve_v3` 1041, `resolve_v4` 1100,
  `decide_v5` 1159, `resolve_v6` 1221 and `MINI_GRID_V7_MODEL` 1289.
- `Coupling.prepare` exists, and `CouplingRefused` raised in prepare becomes a run failure
  (`kernel/execute.py:671-673`). `PHYSICAL_RESOLUTION_FAILURE` is an execution failure kind.
- The kernel checks only declared balances and `delta x energy_per_unit` per stock account (`execute.py:1530-1561`),
  so the `fuel_energy` / `generator_conversion_loss` flows and the energy-per-litre account fit.
- `_Generator.tank` exists. `execution_path_for` gives `MODEL_SPEC` for any mini-grid pair (`execute.py:1983-1991`), so
  no `ProfilePairMismatch`.
- Run requests name their version explicitly (`runs/service.py:583`), so adding v8 moves no existing world.
- The S1-S7 table recomputed by hand from §2.2's formulas: every row matches.
- `fuel_litres` with SFC >= 1/10 L/kWh keeps `generator_conversion_loss` non-negative.

## Implementer questions (I)

**I1. `kobo_draft` cannot build a v8 run.** `host/tests/kobo.py:131-141` hard-codes the profile tuple, ending at
`MINI_GRID_V7_MODEL`, and passes it to `RunSetupService`. `base_run(days, version=8, ...)` (`kobo_season.py:84-88`)
therefore raises `StopIteration`. Every N test depends on it, and the file is not in §0's Files list.
**Default:** commit 3 appends `MINI_GRID_V8_MODEL` to that tuple. That is a test-helper edit, listed in the packet.

**I2. The `ValueError` rule in `cycle_charge_split` cannot be decided inside the function.** §2.2 (last paragraph)
says `minimum_kw <= generator_kw`, "unless `generator_kw` is fuel-capped below it ... else `ValueError`". S8 skips
"M > R with R not fuel-capped". The pure function has no input that says whether R is fuel-capped.
**Default:** no `ValueError` for `M > R`. `g = min(R, ...)` always caps by R, so the case is legal everywhere. S8
covers every combination in its grid. S9 checks only a float argument or a negative one.

**I3. N9 and the pre-flight cite a digest helper that does not exist.** No kernel trajectory digest helper exists in
`host/`, `host/tests/` or `simulator/`. The only Kobo digest is the publication `content_digest`
(`host/tests/test_registered_kobo_execution.py:38`). **Default:** the test computes its own sha256 over a canonical
text of every boundary (offset, sorted stocks, sorted interval measurements, discrete states) of the v7 8-day season
run. I compute it on `main` at pre-flight and pin it as a literal in N9.

**I4. N11's call does not match the port, and T1 cannot take v8.** `HostForwardReplay.forward_replay(run, request)`
takes a `ForwardReplayRequest` (`host/forward_replay.py:384`), not a series. "Stop-90 baseline" is `replay_study`'s
word. `REPLAY_MODELS` says "each is proven by T1 (D-0K1.12)" (`forward_replay.py:55`). T1 is parametrized `[5, 6, 7]`
(`host/tests/test_0k1_forward_replay.py:251`), and its hand anchors (`fuel == 3/10 x kWh`, 66 running steps, :268-270)
cannot hold on v8. **Default:**
- N11 builds `ForwardReplayRequest(BASELINE, observed.pv_available_kw, observed.loads, start_state(observed), ...)`
  the way `runs/replay_study.py:516` does, with `observed = kobo_season.observed_series(<N1 trajectory>, 576)`.
- N11 asserts the request is not refused, the result has 576 steps, and `generator_kwh` is within 1 % of the site's.
- v8 is not added to T1. N11 is v8's replay proof, and the `REPLAY_MODELS` comment cites it.

**I5. The backend v8 statement strings fail the SC-1 ratchet.** The `V8_SENTENCE` literal and the restated
fuel-tank-volume statement that §2.5 adds to `runs/profiles.py` are prose (rule g). Each would be a `HAND_BUILT_NEW`
(`tools/checks/statement_catalogue.py:404-405`, `:965-970`). D-SC1.34 admits them to the baseline only when the spec
names the text and a D-ID. **Default:** the same ruling as 0K4b I1, naming these two strings too. The simulator's
strings are outside the scan (`PKG = backend/assetops_backend`), so they need nothing.

**I6. §2.4 cites line numbers that have moved, and the fuel note is unclear.** On `main`, `resolve`'s
allocation-and-charging block is `mini_grid.py:705-731` (cited as "744-772"). The loads loop is :715-720 (cited as
"754-759"). Fuel is :733-735, balances :805-845, stock accounts :881-895, the "differed from the view" note :849-851
and the "RUNNING with nothing to absorb" note :852-853. **Default:** build by the content §2.4 describes. v8's notes
are `(CURVE_FUEL_NOTE,)` alone: it replaces `LINEAR_FUEL_NOTE` (:909) and is not appended beside it. v7's
nothing-to-absorb note is kept.
