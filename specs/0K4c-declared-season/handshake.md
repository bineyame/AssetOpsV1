# 0K4c handshake (rev 1 spec; reviewer and implementer pre-flight)

Fresh Claude reviewer, 2026-11-21, on `main` at `e39a5d2fa`. Read: `spec.md`, `reviewer-guide.md`, D-0K4.7, D-0K4.8,
D-0K4.19 to D-0K4.25 in `specs/0K4-dispatch-model-review/rulings.md`, `one-figure-change-list.md`, and the code below.
The 0K4b fixture was read on `task/0K4b-fuel-curve` (`d6f108613`), because it is not on `main` yet.

**Checked and found as the spec says (no question):** `host/tests/kobo_season.py` (`overcast_v1` :66, `season_site`
:70, `base_run` :84, `day_windows` :102, `season_inputs` :117; no caller passes `overcast` or calls `day_windows`
outside the module); D-0K4.8's literal list. The test's own loop gives 21 days, 13 below day 30 and 8 from it, and
spells `[2, 3, 1, 4, 2, 1, 1, 2, 1, 3, 1]`. The multiplier formula gives S2's 13 literals exactly. 1 Sep 2026 is a
Tuesday, `date(2026, 9, 6).weekday() == 6`, and `d % 7 == 5` gives the eight Sundays of S4. Day 9's mill rows are
non-zero on the overcast day file (15 and 18 kW), so P2 can fail S3. Day 9's night rows (00:00-06:00) carry res 3 and
clinic 2 kW, so P3 can fail S3. Every series covers each local day with 13 rows summing to 1,440 minutes, so P5
(deleting rows) can fail S5 on an 8-day season, which holds Sunday day 5. `assumed_site` on 0K4b writes the six rows
S7 expects (`host/tests/kobo_assumed.py`, P5 of 0K4b). No database and no served text: host fixtures are outside the
SC-1 scan, so D-0K4.19 has nothing to apply to.

## Reviewer questions (R)

**R1. Season v2 has no pin as a whole** (`spec.md:62-75`; guide check 1). S1 and S2 pin the calendar and the
multiplier. The mill rule is pinned only on days 4, 5, 6 and 12 (S4), and the multiplier only on day 9 (S3). S6 pins
v1 only. A later edit to `day_windows`' v2 branch (which windows are scaled, a Sunday rule that drifts after day 12)
would move every 0K4d figure under the same name "season v2". That breaks simulator-version reproducibility in its
season form (the D-0K4.20 class).
*Default:* add **S9**. It pins, as a literal, the same digest as the pre-flight for
`season_inputs(base_run(61), 61, season="v2")` (a v7 base: inputs only, no kernel run, so it does not need v8). Its
docstring says "a change here is a new season, never an edit". The packet prints it, and 0K4d's `study.json` header
records it.

**R2. The S6 digest is too weak for "byte-equal", and half of S6 has no expected value** (`spec.md:19-21, 74-75`;
guide check 3). The digest covers only `(address, offset, duration, value)` of the forcings, plus "the initial values"
in an unstated form. An edit to `event_id`, `shape`, `parameter_id`, `canonical_unit` or `requirement` passes it.
"`day_windows(d)` ... equals `main`'s" names no source for `main`'s value, and the test cannot import `main`.
*Default:* the digest is the sha256 of a canonical text with one line per forcing, sorted, holding every
`ForcingInput` field (`str(Fraction)` for numbers). Each initial value adds a line with its address, `str(value)` and
unit. A second literal digest covers `day_windows(d)` for d = 0 to 60. The pre-flight prints both, and S6 pins both as
literals. The packet calls this "v1 inputs unchanged", not "byte-equal".

**R3. Are the expected values in S3 and S4 independent, and is `load_scale` composed?** (`spec.md:61, 67-71`; guide
check 2). "The shipped file's value" can only come from `_series_events` or `day_windows`, and both are under test.
Day 9 is overcast in v2 and clear in v1, so even v1's `day_windows(9)` gives the wrong day type. No test composes
`load_scale` with the multiplier, which is exactly 0K4d's Mto path (`host/tests/mto.py:65-66`, `load_scale=1/2`).
*Default:* S3 and S4 read the four scenario YAML files with their own `yaml.safe_load` loop, or write the kW as
literals (night res 3 and clinic 2, scaled by 7/8 to 21/8 and 7/4). S3 adds one case, with `load_scale=Fraction(1, 2)`
on day 9: res and clinic equal the file times 1/2 times 7/8, and the mill equals the file times 1/2.

## Implementer questions (I)

**I1. S7 and S8 cannot run on "`main` with 0K4b"** (`spec.md:13, 76-79`; plant P7). `version=8` needs
`MINI_GRID_V8_MODEL` in `kobo_draft`'s profile tuple (`host/tests/kobo.py:130-140` stops at v7). D-0K4.22 R1 adds it
in 0K4a commit 3, and v8 reaches `main` only in 0K4a's merge (D-0K4.2). 0K4b only declares `GENERATOR_CURVE_NEEDS`
("0K4a puts them on MINI_GRID_V8_MODEL", `runs/profiles.py:977` on `task/0K4b-fuel-curve`). In the D-0K4.25 order,
0K4c (lane 2, after 0K4b's 2.0) finishes before 0K4a's commit 3 merges.
*Default:* 0K4c builds S1-S6 and the document half of S7 now. That half renders `kobo_site(season_site_v2)` and
checks the three basis rows and the 20,000 L tank, so P7 still fails it. S7's frozen-needs half and the S8 smoke move
to 0K4d commit 2, as **V0**, run after both merges. If 0K4a has merged when 0K4c starts, 0K4c keeps S7 and S8 whole.

**I2. Where does S7's "Foundation document" come from?** (`spec.md:76-78`). A run holds no Foundation document.
`FrozenSiteBinding` (`runs/models.py:339-355`) has an id and a version only. `FrozenModelNeed` (`:809-839`) freezes
needs, and basis rows are not needs, so they are never frozen.
*Default:* the basis rows and the tank are read from `kobo_site(season_site_v2)` (`host/tests/kobo.py:66`). The
three values are read from `frozen_world_inputs(run).initial_values` by `parameter_id == "model-need:<key>"`
(`host/execution_adapter.py:421-436`): `11/200`, `30` and `95`, each `answered_by` the Foundation.

**I3. `overcast=overcast_v1` cannot tell "the caller passed one"** (`spec.md:53-55`). With a non-`None` default,
`season="v2"` cannot see whether `overcast_v1` was passed on purpose.
*Default:* the default becomes `overcast=None`, meaning the season's own calendar. v1 behaviour is unchanged for every
current caller, and none passes `overcast` (grep). An unknown `season` raises `ValueError`. S6 still pins v1.

**I4. The packet strip has no letter for an overcast Sunday** (`spec.md:90`). Days 19 and 33 are both overcast and
Sunday.
*Default:* two rows of 61 characters. Row 1 is weather (`C` or `O`); row 2 marks Sundays (`S`, else `.`).

**Answered** (Architect, 2026-11-21): every question by a D-ID or its default, in the table "Handshake answers (rev 2 of 0K4c and 0K4d)" of `specs/0K4-dispatch-model-review/rulings.md` (D-0K4.26 to D-0K4.30); the spec is rev 2.
