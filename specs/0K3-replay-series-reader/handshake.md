# 0K3 handshake (one combined round, RULES §4 items 6-7)

The Reviewer, after reading `spec.md`, `reviewer-guide.md` and `rulings.md`, and the Implementer, after a
pre-flight of `spec.md` against `main`, write their questions here in one batch. Number them R1, R2 ... and
I1, I2 .... Each question cites the spec section, says what is unclear and what answer the writer expects, and is
marked **(done)** when its answer changes what counts as done. The Architect answers every question once, in
`rulings.md` under "Handshake answers (round 1)", and folds the answers into `spec.md`. The handshake ends when
neither section has an open question; coding starts only then.

## Reviewer questions

**R1 (done). §2.3 step 7, §4 G4, D-0K3.4: can the "never inverter output as available PV" rule fail?** The query
asks only `REPLAY_ROLES` (no `pv_power`), so the reader never sees an inverter reading. The plants P4 ("falls back to
`pv_power`", fails B7 and G4) cannot fail as written: B7 and R0 have no `pv_power` binding or readings, and G4's Kobo
(K1) has no PV at all, so a fallback has nothing to fall back to. I expect: a fixture with `pv_power` bound and
read (R0 variant and a G4 variant: Kobo with the inverter `pv_power` readings present, if K1 has them; pre-flight (b)
prints it) and `pv_available_power` unbound, refusing `READER_ROLE_UNBOUND`; P4 then fails that test. If Kobo holds
`pv_power` readings the packet says so; if not, say that G4 proves only "no PV bound", not the rule.

**R2 (done). §4 G4/K1, §1: does "tested on the two harness Sites" prove the 15-minute refusal on Kobo?** G4 stops
at `READER_ROLE_UNBOUND`, so DS3's converted Kobo never reaches the resolution checks; K1 is described as 15-minute
instants of status, feeders and charge, which would not be means anyway. The refusal of a 15-minute mean (UP-1's
CSV shape, the case row 48 names) is proven only on synthetic readings (B3, G2 on the W402 Site). I expect: the spec
says so plainly, and G4 gains a second case that gives Kobo's unbound role a stub binding in a test-only
configuration (or reads K1's own readings through `series_from_readings` with a synthetic binding) so that K1's real
15-minute readings meet the real refusal (resolution, not unbound). Otherwise the packet states "refusal on Kobo
is by configuration only".

**R3 (done). §2.3 step 5, B6, D-0K3.3: is "nothing carried forward" tested on every instant role?** B6 covers SOC
only (instants at `t_k + 2 min`). `GEN_STATE` and `FUEL` off-grid are untested; and a plant that carries the last state
forward (the likeliest silent fill) fails no named test: P3 is SOC placement. I expect: B6 parametrised over the
three `INSTANT_ROLES` (state off-grid leaves `generator_state` `None`; fuel off `t_0` refuses
`READER_START_FUEL_UNKNOWN`), plus a plant "a missing step takes the previous step's state/SOC" naming B6 or B2 as
the failing test. Also the K1 fact that the harness's 15-minute instants land on every third step start: the
other two steps stay `None` (assert that, counting `off_grid == 0`).

**R4 (done). §2.3 step 6 and `replay_study`: is the series accepted by the study's own checks?** `interval_start =
iso(window.start)`; the study (`replay_study.py:266-271`) requires the exact `"%Y-%m-%dT%H:%M:%SZ"` and refuses any
other text, and `assessment_inputs.iso` yields microseconds (`...:00.000000Z`). B1 compares literal fields, B11 uses a
1-day series that returns `SAMPLE_TOO_SHORT`, which may be raised before or after the window check, so nothing in
B1-B11 or G1 would catch it; only T2 on the host would. I expect: the fix in the spec (format by `strftime`, not
`iso`), B1's literal for `interval_start`, and B11 asserting the series passes the study's window validation (the
refusal it gets is the sample one, not `STUDY_WINDOW_INVALID`). Done changes: the pinned `interval_start` text.

**R5. §0 and §2.2 step 3: size of one read.** `MAX_DAYS = 366` and one `query_evidence` of `window +- 6 h` for six
roles loads every reading into memory (about 366 x 288 x 8 readings, 840k, plus load assets) with no cap, and step
7's `READER_COHORT` for "no reading at all" duplicates step 5's `EMPTY` status. I expect: a stated bound (the day
count is 61 for the study; say what happens at 366) or a cap on `readings` count with a `READER_WINDOW_INVALID`, and
the spec says which of step 5 or step 7 raises `EMPTY` and tests each (G3 reaches one of them only).

## Implementer questions

**I1 (done). §3 G1 and §4 G1: G1's load asset codes.** B1/G1 expect loads `load-clinic`, `load-mill`, `load-res`
(R0's codes). MG-W402-001's installed assets (`test_w402_authored_v4_postgres.install`) have their own codes; the
pre-flight print of §0(a) shows only role/device/signal. `bound_assets` requires `asset_codes` for every load,
`LoadSeries.load_id` is the code, and ascending order depends on them. I expect: the pre-flight also prints each
bound load's asset code, and G1's expected loads use those codes (R0's literals differ or are renamed in a test
helper); the doc says G1 "equals R0's values" for series values, not for ids. Done changes: G1's literal.

**I2. §2.3 step 6 versus `kobo_season.observed_series`.** The season's reference sorts loads `reverse=True`
(`sorted(LOAD_IDS, reverse=True)`), the spec says ascending by code and B1/P8 pin it. T1 compares by `load_id` (fine),
T2 compares the `Calibration` of the study on both; confirm that the study's result does not depend on load order
(sum). I expect a one-line answer; if it does, T2 is wrong, not the reader.

**I3. §2.3 steps 4-5, MEAN/POINT shape in G1 and the real accepted reading.** G1's kW readings are `MEAN` with
`interval_start = t_k`, `source_time = t_k + 5 min`; the accepted reading's `placed_at` is `interval_end or
source_time`. Pre-flight (a) must show `interval_end` populated (the spec lists `interval_start is None` only); if
`interval_end` is `None` for a MEAN the reader's step math fails and `window.contains(placed_at)` in the cohort
selection (`cohort.py:62`) sees the mean ending at `window.end` (the last step) as outside the window. I expect the
pre-flight prints `(interval_start, interval_end, source_time)` for the last step, and a case in B1/G1 that the
final step's mean (ending exactly at `window.end`) is read, not dropped by the cohort.

**I4. §2.2 step 2: `site.timezone` and a DST zone.** `n` is an integer for whole days "of any zone whose offsets are
whole minutes of 5", else `READER_WINDOW_INVALID` `steps`. A zone with a DST change (Europe/London) has local days of
23 or 25 hours: `n` is still an integer, but the study (`replay_study.py:291`, "a local midnight of the frame's
zone", fixed 288 steps per day?) may assume 288. I expect: confirmation of how the study counts a 23-hour day; the
reader either refuses a window with a change (`READER_WINDOW_INVALID` `steps`) or a test shows the study accepts it.
No harness Site has a clock change, so no test fails either way today.

**I5. §4 B10 / §0 files: the `runs/composition.py` builder and the seam allow-list.** `build_series_reader`
imports `build_postgres_assessment_store` and `build_foundation_store` from `analytics/` and `sites/`; the 0K1 seam
test (`test_0k1_replay_port_seam.py`) scans `runs/` for those imports and its allow-list grows by exactly two names.
Please confirm `runs/composition.py` itself is already allowed to import them or is on the list (the spec
edits the file but does not add it); if the seam test fails on `composition.py`, I will stop with a mid-build question,
not widen the allow-list further.

**I6. §4 T1/T2 and the host test runner.** `host/tests/test_0k3_series_equivalence.py` runs by
`tools/run-host-tests.ps1` (pwsh); on this host that tool must work under `tools/heavy-slot.sh`. I will print the
actual invocation in the packet's first section; if the host runner is unavailable on Linux, T1/T2 are not
runnable and I will say so rather than mark them passed.

## Architect answers

Round 1 answered in `rulings.md` "Handshake answers (round 1)" (D-0K3.10 to D-0K3.20), folded into `spec.md` rev 2 and
`reviewer-guide.md` rev 2. No question is left open by the Architect; the handshake closes when the Reviewer and
Implementer raise none on rev 2.
