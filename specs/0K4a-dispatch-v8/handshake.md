# 0K4a handshake

Shared round with 0K4b (D-0K4.17); 0K4b's reviewer questions are in `specs/0K4b-fuel-curve-taper/handshake.md`.

## Reviewer questions (R)

Fresh Claude reviewer, 2026-11-21, on `main` `0ead104e9`. Read: `spec.md`, `reviewer-guide.md`, D-0K4.1 to D-0K4.18,
`one-figure-change-list.md`, the owner's one-figure file, `packs/mini_grid.py` (`decide` 503-611, `resolve` 631-910,
`decide_v5` 1150-1196, v6/v7 1218-1298), `host/tests/kobo.py`, `host/tests/kobo_season.py`, `host/forward_replay.py:56`.
I recomputed S1 to S7 by hand from D-0K4.3, and all seven rows match the table.

**R1. `base_run(version=8)` cannot build a run: `host/tests/kobo.py` is not in the Files list.** `kobo_draft` picks
its profile from a fixed tuple (`host/tests/kobo.py:130-140`), which ends at `MINI_GRID_V7_MODEL`. So `run8`, and every
N test with it, raises `StopIteration` before the kernel runs. N10's first case ("refused at run creation naming the
missing Foundation need") also needs that `RunSetupService` to hold the v8 backend profile.
*Default:* `host/tests/kobo.py` gains the backend `MINI_GRID_V8_MODEL`, imported and appended to that tuple, and is
added to §0 Files as a fixture edit. A v7 caller does not change.

**R2. A rule the function cannot apply, plus a misleading note.** §2.2 says `cycle_charge_split` raises `ValueError`
when `minimum_kw > generator_kw` "unless `generator_kw` is fuel-capped below it". The function has no argument that
says the cap came from fuel, so the rule cannot be implemented, and S8's "skipping M > R with R not fuel-capped"
cannot be enumerated. §2.4 step 5 also calls the split with `generator_kw = 0` on purpose. In that call `below_minimum`
(`D + C < M`) can be true, and the step would then note "below minimum load: nothing more to absorb" when the real
cause is an empty tank.
*Default:* drop that `ValueError`, because `M > R` is always legal (`g` is capped by `R`). Set `below_minimum =
D + C < M and D + C < R`: it is true only when the `D + C` cap binds, which keeps S5 `yes` and S6 `no`. S8 enumerates
every combination, including `M > R`. A new case S10 (`D 5, A 15, R 0, C 2, M 12, dis 0`) expects PV `5, 2, 8`,
generator `0, 0`, battery `0, 0`, and `below_minimum` false.

**R3. N3 asserts something the rule does not guarantee (fixture luck, guide check 6).** v8 starts the generator at an
SOC at or below 35 (`effective_start_threshold`). The STARTING step then draws the battery further. A correct
controller that starts between 04:50 and 04:55 therefore shows SOC just under 35 at 05:00, and N3 ("05:00 SOC at least
35") fails. If it passes, that is because of where the season's start happens to fall.
*Default:* N3 asserts three things:
- (a) precondition: v7's 05:00 SOC is below 35;
- (b) v8's lowest SOC from the night-1 start to 05:00 is at least the SOC at the STARTING step, less that step's draw
  by the reader's own arithmetic;
- (c) v8's 05:00 SOC is above v7's.

The packet shows both 05:00 readings as the model-change reconciliation.

**R4. N5's reader leaves out terms the model's `C` has, so "exactly 1 kWh" is fixture-dependent.** In the model,
`C = min(-requested, charge_acceptance_kw(...), (capacity - stored) / (eta x h))`, and under `decide_v8` the request
is `-(A + 40 - D)` (`decide` 597-602). The reader's `C` is the taper term alone. With `site_stop_pct = 100` the run
reaches full charge, where the headroom term binds. The reader's set of "minimum-load" steps then differs from the
model's, and N5 fails or passes on steps it should not judge.
*Default:* the reader computes `C = min(A + 40 - D, 30 x taper factor, (200 - stored) / (95/100 x 5/60))` from its own
SOC. It applies the exact `1` kWh assertion only to steps where that `C` is below `30` because of the taper, or to steps
at or below 95 %. The precondition "at least one such step" stays.

**R5. Nothing pins v8 itself (simulator-version reproducibility).** N9 proves that v1-v7 are unchanged. No test fixes
v8's own trajectory, yet 0K4d's SIMULATED litres and admission results come from it. A later edit to `_resolve_cycle`
or to 0K4b's module would move those figures under the same `mini-grid` v8 identity.
*Default:* add **N12**. The 8-day v8 season digest (`base_run(8, version=8, site_edit=site)`, `season_inputs`) is
printed in the packet and asserted as a literal. The test's docstring says "a change here is a new model version".
This pairs with 0K4b R2, which pins the module's constants.

**R6. The reverse view/segment mismatch can create unserved energy beside a charged battery (an admission input).**
§2.4 step 4 handles a RUNNING step whose view asked for discharge while the segment does not need it. It does not
handle the reverse: the view asked for charge (`requested < 0`) while the segment has `D > A + R` (a load window that
starts inside the step). Then `dis = 0`, and the split leaves `D - A - R` unserved although the battery is above
reserve. v7 also gates discharge on `requested > 0`, so this is not new. But `energy_not_served` is admission part 1
(D-0K4.9), and v8 changes when the case occurs.
*Default:* keep the view-bound rule, which is v7's and needs no physics change. In that case, add v7's "differed from
the view at T" note (`mini_grid.py:851`) to `limited`. A case in the decide/resolve tests pins the note and the
unserved amount. N4's load windows sit on step boundaries, as the spec already makes them, so the case never arises
there.

## Architect answers (2026-11-21)

Answered in the spec's rev 2 and the rulings (`specs/0K4-dispatch-model-review/rulings.md` for 0K4, `rulings.md` for
1a). R1 default (D-0K4.22). R2 D-0K4.22 (no `ValueError`; `below_minimum = D + C < M and D + C < R`; S10). R3 D-0K4.22 (N3 in three parts). R4 D-0K4.22 (the reader's whole `C`). R5 D-0K4.20 (N12). R6 D-0K4.22 (note kept, N13).
