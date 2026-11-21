# 0K4c review

## Round 1: discovery review (Claude reviewer, 2026-11-21, head `f8e6a0b26`)

**Verdict: ACCEPT** (2 Low, none blocking).

Summary:
- The season matches D-0K4.8 exactly. I recomputed it independently and it matches.
- All three digests reproduce from **main's** `kobo_season.py` (no branch code) plus my own transform and digest
  written from the D-0K4.26 text: v1 inputs `59d6456b…`, v1 windows `f2f0088e…`, v2 inputs `465ab6e0…`. v1 is unchanged.
- Labels: declared and SIMULATED in the module docstring, the test docstring, the packet and the state entry. There are no
  figures, and no new assumed value (the assumed rows are 0K4b's, carried with their basis rows).
- `overcast=None` resolves to the season's own calendar, and `season="v3"` is `ValueError`. Overriding it with a passed
  function is untested (L1).
- Plants: P8 fails S9 only, and so does my R2. R1 (a passed `overcast` ignored) fails nothing (L1).
- Deviations: all three are accepted. The frozen order of the initial lines is a defensible reading (L2).
- Checks: the new test plus the 0K2 and 0M regressions, `32 passed`; check-all (fast) `All 42 guards passed (blocking; 0 advisory, 0 warned)`, 140.1 s wall.

### 1. The season, recomputed

- **Calendar.** I built `OVERCAST_V2` independently of the code. It gives 21 days: 13 on days below 30 (September has 30
  days) and 8 from day 30. The run lengths are 2,3 / 7-9 / 13 / 17-20 / 24,25 / 28 / 33 / 38,39 / 45 / 50-52 / 57,
  which is `[2,3,1,4,2,1,1,2,1,3,1]`. My `C`/`O` row and my Sunday row (`datetime`, with 1 Sep 2026 asserted
  `weekday()==1`, a Tuesday) both equal the packet's two rows character for character. The Sundays are days 5, 12, …, 54;
  days 19 and 33 are both overcast and Sundays.
- **Multiplier, by hand.** With k = (7d+3) mod 13:
  - d=0: k=3, so 1 − 0.15·3/6 = 37/40.
  - d=3: k=11, so 9/8.
  - d=7: k=0, so 17/20 (the minimum).
  - d=9: k=1, so 7/8.
  - d=12: k=9, so 43/40.

  The maximum is 23/20, at k=12 (d=5). All 13 of S2's literals agree.
- **Night values.** On day 9: res 3 × 7/8 = 21/8 and clinic 2 × 7/8 = 7/4. With `load_scale=1/2` they are 21/16 and 7/8,
  and the mill is the file value × 1/2. S3's parametrised case asserts exactly this.
- **Scope (guide check 4).** In `kobo_season.py:146-158`, only `RES` and `CLINIC` are multiplied. `MILL` is zeroed only
  when `mill_on` is false, and irradiance falls through untouched. All four windows of the day go through the same loop
  (night, day, dusk and late). My v2 transform applied the multiplier to every res and clinic forcing by
  `offset // 1440` and reproduced `465ab6e0…`. That is a whole-61-day independent check of scope, calendar and Sundays
  together.

### 2. Digest form, and the frozen-order choice

`inputs_digest` (`kobo_season.py:219-229`) follows D-0K4.26: forcing lines sorted, every `ForcingInput` field in
declaration order, `str(Fraction)`, then the `initial|…` lines, joined by `\n`, UTF-8. `duration_minutes` is never
`None` in these inputs (I counted 0), so the `str(None)` edge does not arise.

The ruling attaches "sorted" to the forcing lines only. The frozen order of `initial_values` is deterministic: it is the
document's order, then the two stocks. I computed both variants:

| Season | Frozen order | Sorted order |
|---|---|---|
| v1 | `59d6456b…` | `edc62bfe…` |
| v2 | `465ab6e0…` | `c5800a24…` |

The builder's frozen order is the literal reading, and I accept it (L2 asks only that it be written down).

### 3. v1 unchanged

`day_windows` with both new keywords `None` returns `_day_rows` unchanged (`kobo_season.py:146-148`). In
`season_inputs`, v1 resolves `overcast=None` to `overcast_v1` and passes no shape keywords. No caller passes `overcast`:
I checked `mto.py:66`, `test_0k2_kobo_season.py:88` and `tools/kobo_replay_study.py:64`. Both v1 digests reproduce from
main's module, and the 0K2 and 0M regressions are green. The diff in `kobo_season.py` is additions plus the
`day_windows`/`_day_rows` split and the two new keywords with v1-reproducing defaults.

### 4. Independence (guide check 2)

- S1 and S2 are literals and the test's own run-length loop.
- S3 and S4 read the YAML with the test's own `yaml.safe_load` (`test_0k4c_season_v2.py:51-71`), with the late windows
  as the test's own literal. The window-placement offsets (0, +360, +1080 for `o == 360`) mirror the fixture's layout,
  but no value passes through `_series_events` or `day_windows`. That is what D-0K4.26 R3 asks.
- S6 and S9's `_own_digest` follows the same reading as the code. My recompute from the ruling text is the independent
  one, and it agrees.

### 5. Plants (spot-checks; applied to scratch copies of `kobo_season.py`, the worktree untouched)

| Plant | Result |
|---|---|
| P8 (guide) `mill_on_v2` true from day 41 | S9 fails only, 9 passed. As the guide says. |
| R2 (mine) Sunday zeroing also hits irradiance | S9 fails only. |
| R1 (mine) a passed `overcast` ignored when `season` resolves | **10 passed**. See L1. |

Is P8 enough? Yes, for what S9 is for. S9 is a whole-season pin, so any change to v2's 61 days fails it, which R2 also
shows. The cost is diagnosis: a red S9 does not say what moved. S1 to S5 give the per-property signal for the declared
features. That trade is the one the ruling made, so it is not a finding.

### Findings

- **L1 (Low; missing test; not an acceptance-criterion gap).** `host/tests/kobo_season.py:180-181` and
  `test_0k4c_season_v2.py`.
  - What is wrong: spec §2 and D-0K4.26 I3 say "a passed function overrides it", but no test exercises a passed
    `overcast`. Plant R1, which ignores it, leaves all 10 tests green, and 0K2 and 0M stay green too because no caller
    passes one.
  - Why it matters: 0K4d's handshake gives `dawn_class` the season's overcast function, so the override may get a
    caller later.
  - Fix: one assertion, for example that `season_inputs(base_run(1), 1, season="v2", overcast=lambda d: False)` day 0's
    irradiance equals the steady-day file's. Fix it on the branch, or carry it into 0K4d's V0. Not blocking.
- **L2 (Low; ambiguity).** `kobo_season.py:228` and D-0K4.26.
  - What is wrong: the `initial|…` lines keep the frozen order. That is a reading of the ruling, not its stated text.
  - Why it matters: the digest is what 0K4d's `study.json` records. Any outside recompute, or a future refactor that
    reorders `frozen_world_inputs`' initial values without changing them, gets a different digest. That would read as a
    "new season" when nothing changed.
  - Fix: one line in D-0K4.26 (Architect) saying the initial lines are in frozen order, unsorted, or else sort them now,
    before anything records the digest. Either is fine; I prefer the one line, so the pinned values stand.

### Deviations (all accepted)

- **Branch name** `task/0K4c-declared-season` follows the dispatch. Harmless.
- **Code written alongside the tests.** W2 wants checks first. Evidence that each test can fail is the first run (S6 and
  S9 red against `PENDING`), the packet's eight plants and my three. Acceptable for a 1-unit fixture; not a finding.
- **Digest order.** See §2 and L2.

### Checks run (this review, head `f8e6a0b26`)

- `tools/heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/run-host-tests.ps1 -- host/tests/test_0k4c_season_v2.py host/tests/test_0k2_kobo_season.py host/tests/test_0m_mto_headroom.py -q`:
  `32 passed in 115.74s`.
- My independent recompute (main's module plus my transform), run with `/opt/assetecon/AssetOpsV1/.venv/bin/python`:
  all three digests equal the literals.
- Plants P8, R1 and R2 were run through `heavy-slot.sh`, with results as in §5.
- `heavy-slot.sh --wait-seconds 3000 -- pwsh -NoProfile -File tools/check-all.ps1`: `All 42 guards passed (blocking; 0 advisory, 0 warned)`, 140.1 s wall.
- Not run: `test_0k4b_kobo_assumed.py`. It is unchanged by this diff, and the implementer ran it at `12851e0b8`
  (`24 passed` with 0K2 and 0M). S7's frozen half and S8 were not judged here: they are 0K4d's V0 (D-0K4.26).

### Residual risk the packet does not name

- `inputs_digest` covers forcings and initial values only, not the other fields of `FrozenWorldInputs` (the
  unmodelled-input pairs and so on). "Pinned as a whole" means pinned as to forcings and initial values. That is the
  ruling's scope, but 0K4d's identity header should not claim more.
- Nothing maps a season name to its overcast function (for example a `SEASON_OVERCAST` table). 0K4d's `dawn_class`
  will need one; today a caller must know to use `overcast_v2`.
- S9 is a v7 base on v1's site (`base_run(61)`). 0K4d's v8 runs on `season_site_v2` use the same forcings, but its
  initial values (the three assumed needs) differ. So 0K4d's `study.json` digest equals S9's only if 0K4d hashes the
  v7-base inputs, as D-0K4.26 says, and not the v8 run's own inputs. 0K4d's reviewer should check which one it hashes.
