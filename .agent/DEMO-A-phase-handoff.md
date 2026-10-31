# DEMO-A phase handoff

Source: `AssetOpsV1-plan2\.agent\build-sheet-DEMO-COMBINED.md` (rev 1 + Addendum 1). Branch
`task/DEMO-A-combined-dataset`; main (DEMO-A0 seam) merged at `0cc70b2d7`.

## State (2026-10-31)

- U1 probe: done (`.agent/DEMO-A-probe.md`).
- **U2: built** (`tools/demo_combined.py`: tree, DB guard, story clock + `INSTALL_CLOCK_CONFLICT` /
  `STORY_CLOCK_OUT_OF_RANGE`, cursor keys, wall cap, `prepare|links|serve|tick|drop`; dev flags `--sites`,
  `--no-finish`). Story offsets: `backend/conversions/demo-combined-story-v1.json`. Self-check child
  (`tools/demo_combined_finish.py check`) is referenced by `finish()` but **not written yet** (U6).
- **U3: built, R2 STOP RULE FIRED.** `tools/demo_combined_kobo.py` builds VERIFIED with price via the A0 seam; cost
  check `MODELLED_NO_IMPROVEMENT` (0 USD). R2 diagnosis in the probe file, section "U3 build + R2 diagnosis": the
  board's 31-day Finding index read is UNASSESSED (index rule: all inspected days CURRENT), so F-104 is never on a
  Kobo board day. Waiting on the owner's story-stage call.
- U4, U5, U6: not started.

## Resume

- After the ruling: U4 (cold), U5 (EV), U6. Explore findings for U4/U5:
  - Cold: `test_w502_cold_scenario_producer.ShiftedChain.open` (:73-108) reads DB now (:79) and calls
    `producer.shifted_case` (:80); install = start - 4 h, setup = start - 1 h (:82) - R3 needs install S-26d 06:00,
    so `story_day`/`install_at`/`scenario_path` must thread through `target_delta` (:69), `shifted_case` (:118/:123)
    and `ShiftedChain.open`. `attest()` records at real now (:131). BUILD argv `[mode, out]` (walkthrough :707).
  - EV: `Chain.open`'s `now=lambda: "2026-10-06T07:00:00Z"` (test_w205b :258-263) is passed to
    `RunSetupService`, a module global read at call time - swappable as `registered.RunSetupService = wrapper`
    (w601 swap pattern) without editing the test module. Scenario: pass a shifted repository via
    `open(scenarios=..., scenario_id=...)`; INTERVAL_INVALID check is `runs/service.py:639-649` (EV branch).
    `native_replay` (:105-146) guard :122-124 needs the `window=` keyword; `P.E_START/E_END` fixed (w504 cases :39-40).
- Dev DB `assetops_demo3_dev_test` + `var/demo3_dev` dropped after diagnosis (rebuild: Kobo-only prepare, ~190 s).
