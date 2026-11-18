## 7. Q7 audit (Rev 1): is any date, story or Site logic hard-coded in the product?

Owner, Q7: "how does this relate to how a real site operates where you can just show how site/portfolio is operating
and add missing data through proper mechainsm when needed, i sense a possible hardcoding of logic that should not be".

**First, the question itself.** Q7 (Part D.5 Q1) asked only *at what clock time* the 10-Nov meeting was, so the
coordinator could fit the owner's walkthrough before it. It was a calendar question, not a product rule. It is moot now
that the session moves (R1.3).

**Verdict: no product hard-coding to remove. No G4.** Searched read-only on main `9aae0d003`: `backend/assetops_backend`,
`host/` and `frontend/src`, for Site codes, fixed dates, "story"/"demo" logic and clock reads. Tests and fixtures were
excluded from "product".

### 7.1 What was found, classified

**A. Site-specific branches on the monitoring path (what a Site's screens show): none.**
- No Site code appears in any non-comment line of the backend monitoring path. The Site codes found in
  `backend/assetops_backend` are in docstrings and CLI usage examples only (e.g. `chain/snapshots.py:3`,
  `evidence_migration.py:3`, `recompute_consequences.py:3`).
- `frontend/src`: Site codes appear only in `frontend/src/test/outcomeBoardFixture.ts` (a test fixture).
- No fixed date is read by any screen. The fuel night window (18:00 to 12:00 local, `fuel_balance/rules.py:57`) is the
  versioned model parameter `fuel-balance-1` (`rules.py:30-45`), applied to every diesel Site in its own timezone. It is
  not tied to Kisiwa.

**B. Real-clock reads and retention windows: legitimate.** This is how a real Site behaves.
- Frontend default windows read the browser clock: `sites/PerformanceDispatch.tsx:86-87` (board opens on today),
  `sites/siteTime.ts:203-206` (the last 7 days), `estate/estateShared.tsx:30`, `work/globalWorkClient.ts:701`,
  `sites/workClient.ts:187`, `sites/miniDepthClient.ts:334,358`.
- Backend 30-day rules: "verified recently" `estate/coverage.py:40`; the Action observation window
  `actions/service.py:45`; the work backdate limit `work/model.py:37`; the EV read window `ev_assessment_api.py:107`.
- Month-to-date targets: "too early to judge" below the checked-day minimum (`outcomes/objectives.py:16-22`, `:141`;
  copy `chain/vocabulary.py:277`). A real Site on 2 December would show the same.
- Validation bounds `fuel_balance/night_read.py:24` (years 2000–2100), and `review_date` provenance stamps in
  `financials/fuel_cost.py:79` and `fuel_cost_v2.py:65`. These are metadata, not logic.
- One Low (after the demo): `PerformanceDispatch.tsx:86-87` takes "today" in UTC, not Site-local. Between local
  midnight and 03:00 in Dar es Salaam it opens on the previous day. This is not hard-coding.

**C. Clock overrides that only a prepare or a test may switch on: legitimate, guarded.**
- `prepare_clock.py:13-24` refuses any story clock unless the database is `assetops_polish_*` or `*_test`. Users:
  `mini_decisions/store.py:119-130` (`story_clock`) and `objectives/adapters/postgres_objective_store.py:48`. Production
  composition never sets them.
- "Story time" in `chain/` (`lifecycle.py:7`, `threads.py:157,206`, `lookup.py:3-10`) means the *effective* time of an
  event, as opposed to when it was recorded. That is a bitemporal rule, not demo logic. The name is unfortunate, and
  renaming it to "effective time" is an after-the-demo cosmetic item.

**D. Demo labels standing in for missing sign-in: legitimate, labelled, configuration-driven.**
- `actions/fuel_verification.py:55` and `actions/verification_families.py:60` (`BASIS_TEXT` "SYSTEM_DEMONSTRATION: …
  no verified human principal exists"), and `actions/lifecycle.py:49-54`. These are honest provenance, because no user
  sign-in exists. The freeze methods have no route (`actions/verification.py:367,376`) and are also called by the
  tick's `chain_snapshots` stage.
- `ASSETOPS_ACTION_DEMO_GRANTS` (`actions/composition.py:37`, `actions/adapters/demo_grants_file.py`: absent means
  nothing is granted) and `ASSETOPS_DEMO_FIXTURE_MANIFEST` (`analytics/adapters/demo_manifest_file.py`: it only
  annotates exact evidence IDs, never fills an input). Both are server configuration and are labelled on screen.
- G3's `ASSETOPS_OPERATIONAL_ENTRY` follows the same pattern.

**E. Lab and simulator fixture pins: product code, but not on the monitoring path. After the demo; not G4.**
- `scenarios/ev_parsing.py:26-32` pins the Lab's `ev-scenario/1` to EV-LAB-001, seed 20517 and the window
  2026-10-06 08:00–09:00Z. `simulator_lab_api.py:2750` lists EV scenarios only for `EV_SITE_CODE`.
- `sites/ev_lab.py:76-77` and `sites/cold_lab.py:30` are fixture installers with fixed effective dates.
- `host/ev_publication.py:331-336` is the simulated charger. It runs only in a weekly TUESDAY 08:00–16:00 window.
- These shape what the **simulator** can generate, standing in for a real device. They do not shape how the product
  reads a Site. Their only demo effect: EV data can be added on Tuesdays only (§4.4).
- After-demo item: generalise to `ev-scenario/2` (any registered EV Site, its declared schedule).

**F. Demo tooling only (`tools/`): the story lives here, as it should.**
- `tools/demo_combined.py:146-148` `story_day` (S = the prepare day − 2), the S-relative story calendar
  (`backend/conversions/demo-story-days-v3.json`, `tools/demo_story_days.py`), `SITE_WEEKDAY`, `FULL_DAY_AFTER_TRIAL`,
  `BOARD_WINDOW_DAYS`, and the Kisiwa story (`tools/demo_combined_kisiwa.py`).
- The date rule "do not prepare on the 3rd to 5th" is also tool-side (D-W1-15).

### 7.2 Why the date mattered, and why it mostly stops mattering with G1

- **The product reads the real clock** (B). It shows each Site's state as of now, as a real Site would.
- **The demo data is generated once, at build time.** The story is anchored at S = the build day − 2, and nothing adds
  data afterwards. So as the calendar moves on, the demo Sites look like real Sites whose gateways stopped: recent days
  show as missing, and "this week" empties. The earlier plans re-built the demo (about 2.5 h) close to each session
  for that reason. The product was right; the data simply stopped.
- **With G1, the owner adds the missing days up to yesterday whenever he wants** (one command, about 20 min per missing
  date). G2 and the normal tick check them, and every screen updates. The session date then stops mattering for
  freshness. That is the "proper mechanism" the owner describes: in production the gateway does it continuously, and
  in the demo `add-dates` stands in for the gateway.

### 7.3 What still remains, and whether it is real behaviour

| Remaining effect | Real product behaviour or demo artefact | What we do |
|---|---|---|
| Today has no data: G1 adds whole days only, up to yesterday, so a Site board opening on today is empty | Demo artefact. A real Site streams today's readings. The screen's "no readings" message is honest. | The presenter uses the dated links (`links`). After the demo: open on the latest data day (Part E.5). |
| On the 1st–3rd of a month, the monthly target reads "too early to judge" | **Real.** A real Site shows the same. | Nothing. The prepare date rule is tool-side only. |
| The story ages: about 30 days after S, "verified recently" drops, and story items fall outside the 30-day work and observation windows | **Real.** A trial six weeks old is not "recent". | Prepare a fresh build if the demo is more than about 25 days after S (R1.5). |
| A long gap costs catch-up time (about 20 min per date) | Demo artefact (the simulator) | If more than about 7 dates are missing, prepare fresh (about 2.5 h) instead |
| EV data only on Tuesdays | Simulator pin (E) | Printed by the tool. After the demo: `ev-scenario/2` |
| Host-vs-database clock skew (Part F) | Environment | The clock check before E2, E3 and each E4-lite |

---

## Revision 3 — G2 test rulings (2026-11-08)

Claude Architect (binding: Claude, `AssetOpsV1-plan2/.ai/ROLE_CONFIG.md:9`). Read-only; no Postgres run. Inputs: branch
`task/OWN-G2-diesel-night-check` at `a5a5ffaf0` (worktree `AssetOpsV1-g2`), its `.agent/review-packet-G2.md`
(Deviations 1-6) and `backend/tests/test_own_g2_fuel_night_tick_postgres.py`. **This revision wins over R2-G2 Q5 and
§2.6/§2.7 where they differ.** The builder makes no further decision on the items below.

### R3.1 Fixture: keep K1's real path and all four runs; no shortcut

- **Ruled: the fixture stays exactly as written at `a5a5ffaf0`** (K1's path: `kis.register`, `day_document` runs, a real
  gateway, `_publish_and_accept` into S2 `BatchIngestionService`; `OFFSETS = (0, 1, 2, 9)`), plus the `received_at`
  fix already made (Deviation 2).
- **Rejected: readings straight into `BatchIngestionService` without the gateway.** No Kisiwa batch builder exists
  (the w402 `cases.build_batches` precedent is mini-grid only), so the builder would have to design batch bytes, and the
  readings would stop being the story-shaped ones P6 and KIS-11 depend on. That lowers fidelity; the owner said not to.
- **Rejected: night-only runs.** `day_document` is a fixed 15:00-15:00 day; changing it is design work for about a 20 %
  saving.
- **Rejected: dropping a run.** Each run carries a distinct proof (N0: P1, P4a, P7, Q1; N1: P1, P4b/c on a
  WITHIN_MARGIN night; N2: P6's pre-assessed night; N9: P5 outside the base set). Merging them couples P4a and P4b on
  one night's records.
- Measured reference: `host/tests/test_k4a_kisiwa_night4.py` (one Kisiwa night on the same path) took 348 s
  (`review-packet-K4a.md:124`), so four runs plus ticks is about 20-25 min. That is the expected cost, not a defect.

### R3.2 The cap: this file is one background heavy job with a 45-minute budget

- The 10-minute figure is the per-command tool limit, not a limit on a test file (precedents: the estate guard
  self-tests, about 20 min, `review-CH-5b2.md:77`; T6 at 15-25 min in E2, combined pass F.3). It does not apply here.
- **Run the file whole, in one process, in file order**: no `-k` split and no `-n` (its tests share the module fixture
  and run in order: P1/P6/P7 tick, then P4a, P4b/c, P5). Under the container runner's `--dist loadfile` the module stays
  on one worker, so the full-suite tiers are safe.
- **How:** `run_in_background`, as the only heavy job on the machine (not while check-all or any other Postgres run is
  going), on its own `*_test` DB, with `-s` so the `G2 ...` print lines land in the log.
- **Budget: 45 minutes hard** (about 2x the estimate, per the long-run rule). **Stall rule:** check every 5 min with
  `SELECT count(*) FROM ingestion_disposition` on that DB (cheap, read-only) until the fixture ends; if the count does
  not move for 10 min during the fixture, or the budget is reached, kill the run and report. Do not retry blindly.
- **Marker:** add `pytest.mark.slow` to the module's `pytestmark` (a list beside the existing `skipif`), as R2-G2 Q5
  ruled for over 120 s. Add the measured runtime to the module docstring.
- The reviewer reruns it the same way, as its one heavy job. E2 runs it as its own named item (about 25 min, inside
  the 08:00-10:45 E2 window; R1.3 already counts it).

### R3.3 Fixture deviations (packet Deviations 3 and 4): all accepted

1. **15:00-15:00 local day runs ending at the latest local 15:00 at or before DB now - 15 min, and 1, 2 and 9 days
   before it.** Accepted. Each run holds exactly one whole night (17:30 to 12:30 sits inside 15:00 to 15:00), and the
   ticks' L can move by at most one night during a 25-min run, which keeps N0-N2 in the base set and N9 out of it.
2. **P5's old night at 9 nights, not 10.** Accepted. The requirement is "outside the base set `[L - 6, L]`, inside
   `RECORD_LOOKBACK`"; 9 nights meets it, and `_night(fuel, n[9]) is None` after tick 1 proves "outside".
3. **Only `fuel_night` as a real `StageRunner` child; the other stages in process.** Accepted. G2 changes only the
   `fuel_night` child path (its args, `deadline_at`, JSON result); the other stages' child paths are unchanged and
   covered by the s4 tick tests. "Real `StageRunner` children" in R2-G2 Q5 means the stage under test.
4. **Q1 edges at the real 5-minute readings 17:25 / 17:30 / 12:25 / 12:30.** Accepted. The SQL bounds are bound from
   `bucket_bounds()` (one source), and the inclusive/exclusive edges are exactly 17:30 (in) and 12:30 (out), both real
   readings in the set. The minute-exact 17:29 / 12:29 proof stays in no-DB case 1 on `night_of`. Keep the assert that
   all four edge times are present.
5. **Q12 with a Site id that has no FUEL_TANK or GENERATOR rows (an unknown id).** Accepted. `schedule_inputs` takes the
   same early return for any Site without exactly one tank and one generator. The real Cold and EV Sites are proven on
   the real build at E4 (`eligible: false` for Cold/EV, R1.3).

### R3.4 `test_fix_cold_drain_tick_postgres.py` p1/p2/p3: the pre-existing replay-fixture failure family

**Ruled: the same failure family as R-1 T6 / w203 (combined pass Part F), not caused by G2, not a G2 blocker. Tracked
into E2's reserved fix round.** Evidence:

- **Where they fail.** All three fail inside the replay fixtures, before the tick and before any line G2 changed: p1 at
  `assert jobs` (`test_fix_cold_drain_tick_postgres.py:101`, no PENDING `cold_chain` job after `opened("excursion",
  cold_chain)`); p2 at the EV replay's Lab run `FAILED`; p3 at an unpack of the cold fixture's rows. G2's only edits to
  this file are the two stage-list pins (`:106-108`, `:199-201`).
- **Same factories as T6.** p1-p3 build their data with `test_w203_cold_replay_postgres.opened` and
  `test_w301_estate_golden_postgres.cold_chain` / `ev_chain`. Those are exactly the factories of the w301 golden
  replays that failed on main at R-1 (`733eaf75c`, an ancestor of G2's base `1d666d410`) with "cold `run_pending` -> []"
  and "a Lab run FAILED" (Part F.1). Neither w203 nor w301 imports `scheduling` or `fuel_balance` (grep: no match), so
  no G2 module runs in these fixtures.
- **Clock skew is ruled out** (DB clock checked, not skewed; coordinator handoff line 30). With no skew, Part F.1's
  branch applies: a real fixture failure that goes to E2's fix round. p1 failing at `assert jobs` (no job at all, not a
  job that is merely not yet due) fits a replay that never reaches the job, the same as T6's empty `run_pending`.
- **G2's own pin is still proven on Postgres:** p4 (`test_p4_mini_only_site_...`, the full stage list including
  `fuel_night`) passed, and `test_w402_mini_stage_postgres.py` passed.

**What the builder and reviewer do:**
- Builder: no further change to this file. The packet lists p1-p3 as "pre-existing, replay-fixture family (R-1 T6 /
  w203, Part F), tracked to E2" with the three failure lines.
- **One confirming run, required before merge (about 2 min, in the reviewer's heavy-job slot, after the G2 file):**
  `test_fix_cold_drain_tick_postgres.py::test_p1_one_tick_assesses_and_drains_cold_work` alone on the **main**
  checkout (`AssetOpsV1-plan2`, main HEAD, own `*_test` DB, only when no other heavy job runs). If it fails at the same
  line on main, the ruling stands. **If it passes on main, G2 caused it: that is a High finding and G2 does not merge.**
- E2's reserved fix round gains the item "cold_drain p1-p3 replay fixtures" beside "w203/w202 cold replay fails with no
  skew" (Part F.3), under the same test-side-only rule; a product change there stops and goes to the Architect.

### R3.5 `test_ch1b_drain.py` (§2.6 pin file)

- It needs no edit by reading: its tick tests use `test_ch0_tick_timing.FakeRunner`, which G2 already updated and which
  returns an OK result for any stage, and its lease assert is relative (`site_lease_seconds + 30`,
  `test_ch1b_drain.py:400`), so the added `fuel_night_seconds` does not move it.
- **Builder runs it** (no DB, seconds) with the no-DB set. If it passes unchanged, the packet says "run, passed, no edit
  needed". If any test fails, edit only a stage-list or lease pin, exactly as in the other pin files; any other failure
  stops and goes to the Architect.

### R3.6 G2 merge condition (all must hold)

1. `test_own_g2_fuel_night_tick_postgres.py` completes under R3.2 with **every test passing** (Q1/Q12, P1/P2/P3/P6/P7,
   P4a, P4b/c, P5), by the builder and again by the reviewer; the packet records the runtime and the `G2 ...` lines.
2. The no-DB set is green: the three G2 files, the pin files (`test_ch0_tick_timing.py`, `test_ch1b_drain.py`,
   `test_fix_cold_drain_stage.py`, `test_w402_mini_stage.py`, `test_w403_opportunity_stage.py`), the k3 and k4a rules
   files and `test_demo_combined_finish_rows.py`.
3. `test_w402_mini_stage_postgres.py` and `test_fix_cold_drain_tick_postgres.py::test_p4_...` pass (already shown at
   `a5a5ffaf0`; rerun only if a stage, tick or limits file changes again).
4. The R3.4 confirming run on main fails at the same line (pre-existing). p1-p3 are then listed, not counted.
5. A fresh Opus review with no open High or Medium finding; then `--no-ff` merge and check-all on main, as R1.3 says.

### R3.7 — G2 Q1 edge ruling (2026-11-08)

Claude Architect, under the owner's delegation of 2026-11-08 (`.agent/owner-away-architect-decides-2026-11-08.md`:
decide from how real sites work, no corner cutting on fundamentals). Read-only; no Postgres run. Inputs: branch
`task/OWN-G2-diesel-night-check` at `11f284e80`, packet Phase 3, `test_own_g2_fuel_night_tick_postgres.py:215-244`.
**This wins over R3.3 item 4, R2-G2 Q1's Postgres case and §2.4's half-open read range where they differ.** Logged for
owner review (decision D-R3.7 below).

**1. The cadence is 15 minutes; R3.3 item 4 was wrong.** The fixture's runs use `registered-kobo-publication` v5
(`tools/demo_combined_kisiwa.py:73-75`). Its `fuel-level-sensor/fuel-level` declaration is inherited unchanged from
`LAB_PUBLICATION_PROFILE` (`backend/assetops_backend/runs/profiles.py:1496-1498`: `cadence_minutes=15`,
`dropout_per_thousand=40`) through v1 (`:1873-1890`); v4's five-minute set `_V4_FIVE_MINUTE` (`:1996-2005`) does not
contain it and v5 changes only PV output (`:2087`). 96 slots a day less 4 % dropout is about 92-94 a day, matching the
builder's 376 over 4 runs. The "five-minute publication profile" wording (`sites/binding_roles.py:275`) is about the
other signals; that is where R3.3's assumption came from. Readings sit on :00/:15/:30/:45, so 17:30 and 12:30 exist and
17:25 / 12:25 never will.

**2. Found while ruling: the bucket's end was open, but the assessment's read is closed. Fixed here (D-R3.7).** The
assessment reads `[start - 30 min, end + 30 min]` closed (`fuel_balance/service.py:108`, with `window_readings`'
`<= :hi`, `actions/adapters/postgres_action_store.py:606`) and picks the closing reading from `end <= t <= end + 30 min`
(`fuel_balance/rules.py:160`). So a reading at exactly local 12:30 can be the night's closing reading: on a 15-minute
sensor with 4 % dropout, a lost 12:00 and 12:15 makes the 12:30 reading the closing one, and `rules.py:160-168` also uses
it for the conflict check. The bucket put 12:30 in no night (`< 12:30`). On a real remote mini-grid, readings arrive
late routinely (gateway store-and-forward after a link outage); a late 12:30 reading would change night d-1's inputs but
never trigger its re-check. The bucket is the re-check trigger, so it must cover exactly what the assessment reads.
**Ruled: the bucket is `[17:30, 12:30]`, closed at both ends.** Two nights' ranges still never overlap (12:30 to 17:30
lies outside both). The start side is already right (opening search `start - 30 <= t <= start`, bucket `>= 17:30`).

Product changes (G2 branch only, nothing else moves):
- `fuel_balance/scheduled.py` `night_of`: `if local.time() <= end:` (was `<`). `bucket_bounds` docstring: "`[NIGHT_START
  - EDGE, NIGHT_END + EDGE]` (closed: the assessment reads both edges)".
- `fuel_balance/adapters/postgres_fuel_balance_store.py`: move the `CASE` into a module constant `NIGHT_BUCKET_SQL`
  (alias `e`, binds `:tz`, `:ns`, `:ne`), ending `... WHEN {local}::time <= :ne THEN {local}::date - 1 END`, and use it
  unchanged in `schedule_inputs` (`SELECT {NIGHT_BUCKET_SQL} AS night, d.decided_at FROM ...`). It is the one SQL source
  the Postgres test evaluates; no other behaviour changes.
- §2.4's "`[start − 30 min, end + 30 min)`" now reads "`[start − 30 min, end + 30 min]`".

**3. What Q1 must prove on Postgres.** That the store's own SQL bucket and `night_of` give the same night for every
instant, at second precision, at both edges, for the real Kisiwa readings and for any cadence another site may report on
(1, 5, 10, 15 or 60 min, or unaligned clocks such as 17:29:58). A set equality on `reading_nights` alone cannot prove an
edge: every night already has dozens of readings, so moving the 17:30 or 12:30 reading in or out leaves the set
unchanged. Hence a per-reading check through the store's own expression, plus synthetic instants for other cadences
evaluated by Postgres. No new evidence is written, so P1-P7 are untouched and R3.1's no-hand-built-batch rule holds.

**Exact asserts, replacing `test_q1_...` body lines 216-242 (the Q12 assert at the end stays as it is):**

```python
from assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store import NIGHT_BUCKET_SQL
from assetops_backend.fuel_balance.composition import build_fuel_balance_store
from assetops_backend.fuel_balance.scheduled import RECORD_LOOKBACK, bucket_bounds, night_of

engine = site["engine"]
ns, ne = bucket_bounds()
b = {"tz": site["tz"], "ns": ns, "ne": ne}
# (a) every real tank reading, through the store's join, acceptance filter and its own CASE
rows = _q(engine, "SELECT COALESCE(e.interval_start, e.source_time) AS at, d.decided_at, "
          f"{NIGHT_BUCKET_SQL} AS night FROM accepted_evidence e JOIN ingestion_disposition d "
          "ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal WHERE e.site_id = :s AND d.decision = 'ACCEPTED' "
          "AND d.accepted_evidence_id = e.id AND e.role = 'fuel_level' AND e.asset_id = CAST(:a AS uuid)",
          s=site["site_id"], a=site["tank"], **b)
local = [(r["at"].astimezone(site["zone"]), r) for r in rows]
hhmm = {t.strftime("%H:%M") for t, _ in local}
print("G2 Q1 readings", len(rows), "minutes", sorted({t.minute for t, _ in local}), "edges",
      sorted(hhmm & {"17:30", "12:30"}))
assert len(rows) > 0 and {"17:30", "12:30"} <= hhmm, sorted(hhmm)   # the real edge readings exist
for t, r in local:
    assert r["night"] == night_of(t), (t, r["night"])              # SQL == Python, every reading
    if t.strftime("%H:%M") == "17:30":
        assert r["night"] == t.date(), t                           # start edge in
    if t.strftime("%H:%M") == "12:30":
        assert r["night"] == t.date() - timedelta(days=1), t       # end edge in (closed, = closing search)
# (b) any cadence: synthetic instants around N0, evaluated by Postgres through the same expression
d, z = site["nights"][0], site["zone"]
d1 = d + timedelta(days=1)
probe = {datetime.combine(d, time(17, 25), z): None, datetime.combine(d, time(17, 29, 59), z): None,
         datetime.combine(d, time(17, 30), z): d, datetime.combine(d, time(17, 30, 1), z): d,
         datetime.combine(d, time(23, 55), z): d, datetime.combine(d1, time(0, 5), z): d,
         datetime.combine(d1, time(12, 25), z): d, datetime.combine(d1, time(12, 29, 59), z): d,
         datetime.combine(d1, time(12, 30), z): d, datetime.combine(d1, time(12, 30, 1), z): None,
         datetime.combine(d1, time(15), z): None}
for at, want in probe.items():
    [got] = _q(engine, f"SELECT {NIGHT_BUCKET_SQL} AS night FROM (SELECT CAST(:x AS timestamptz) AS interval_start, "
               "CAST(NULL AS timestamptz) AS source_time) e", x=at.astimezone(UTC), **b)
    assert got["night"] == night_of(at) == want, (at, got["night"], night_of(at), want)
# (c) the store itself: same nights, and each night's trigger instant is its readings' latest decided_at
store = build_fuel_balance_store(URL)
try:
    inputs = store.schedule_inputs(site["tenant_id"], site["site_id"], RECORD_LOOKBACK)
    empty = store.schedule_inputs(site["tenant_id"], uuid4(), RECORD_LOOKBACK)
finally:
    store.dispose()
want = {}
for t, r in local:
    n = night_of(t)
    if n is not None:
        want[n] = max(want.get(n, r["decided_at"]), r["decided_at"])
print("G2 Q1 reading nights", sorted(inputs.reading_nights), "want", sorted(want))
assert set(inputs.reading_nights) == set(want) == {site["nights"][k] for k in OFFSETS}
assert all(inputs.reading_nights[n].astimezone(UTC) == want[n].astimezone(UTC) for n in want), (inputs.reading_nights,
                                                                                                want)
assert inputs.tank_asset_id == site["tank"] and inputs.generator_asset_id is not None
```

Builder rules: `UTC`, `time`, `datetime`, `timedelta`, `uuid4`, `OFFSETS`, `URL` and `_q` (keyword binds) are already in
the file. If `_q` cannot take the `time` binds, use `engine.connect()` + `text(...)` with the same binds; nothing else.
No `-k` split (R3.2 stands).

**No-DB case 1 (`test_own_g2_fuel_night_due.py:97-112`):**
- `:102` becomes `assert night_of(datetime(2026, 11, 6, 12, 30)) == d  # fails if the end is open (the closing search
  includes end + 30 min)`; add `assert night_of(datetime(2026, 11, 6, 12, 30, 1)) is None  # fails past end + 30 min`
  and `assert night_of(datetime(2026, 11, 5, 17, 29, 59)) is None`.
- `:112` becomes `assert night_of(datetime(2026, 11, 6, 11, 30)) == date(2026, 11, 5)`; add
  `assert night_of(datetime(2026, 11, 6, 11, 30, 1)) is None`.

**4. The two Phase 3 test-code fixes (`0dd9e5af6`) are accepted; neither changes what is proved.**
- (a) Delivery ticket digest: the product refuses a `FUEL_DELIVERY` without a ticket SHA-256 (`work/service.py:550-551`,
  `WORK_RECORD_TICKET_REQUIRED`), which is right for a real site (no ticket, no delivery credit). Before the fix
  P4b/P4c/P5 stopped at `_post`'s 201 assert, before their proof; volumes, times and tank are unchanged, so the fix only
  lets the tests reach what they were written to prove.
- (b) `_ids()`: `record_ids` is stored as `[[root, head], ...]` (`fuel_balance/service.py:124`, `model.py:63`), so the
  old `str(x)` compare could never match. Each dip has one revision (root == head), so "the dip's id is among the
  flattened ids" is the same claim as "the dip is a counted record".

**5. Merge condition update (R3.6).** Item 1 now includes these Q1 asserts passing in the same whole-file run. The no-DB
set (item 2) is rerun after the `night_of` change. The reviewer confirms `NIGHT_BUCKET_SQL` is the only bucket `CASE`
in `schedule_inputs`. The packet lists D-R3.7 as a product change with this reason.

**D-R3.7 (for owner review).** The night re-check trigger now includes a reading at exactly the closing edge (local
12:30), because the assessment uses that reading and real gateways deliver late readings; leaving it out would let a
late closing reading go unnoticed. Cost: one comparison in two places, one extracted SQL constant, and the Postgres
rerun Q1 needed anyway.

### R3.8 — G2 review rulings (2026-11-09)

Claude Architect (binding: Claude, `AssetOpsV1-plan2/.ai/ROLE_CONFIG.md:9`), under the owner's delegation of 2026-11-08
(`.agent/owner-away-architect-decides-2026-11-08.md`). Read-only; no Postgres run. Inputs: `AssetOpsV1-g2/.agent/review-G2.md`
(commit `e2400a0d1`, REJECT on M1) on `task/OWN-G2-diesel-night-check` at `e33d8f113`. **This wins over §2.4 step 4,
§2.4 "What this means", `run_site` step 2.1, §2.7 and R3.6 items 1-2 where they differ.** The builder (Sonnet) makes no
further decision. Branch: the same G2 branch; one fix round.

**Ruled: M1 fixed now (D-R3.8); L2 accepted for now, no change (D-R3.9); L3 fixed now, narrowly (D-R3.10); L1 fixed in
this sheet (§2.4 lines 504 and 511 now read `<= '12:30'` and `[start − 30 min, end + 30 min]`).**

#### R3.8.1 M1 — a record that LEAVES an old night re-checks that night (D-R3.8)

Real-site case: a delivery keyed with the wrong date (or to the wrong tank, or as the wrong kind) is corrected days
later. The night it left must be re-checked, or an "unexplained fuel" Finding the data no longer supports stays open in
front of the client. The base set covers this only for the last 7 nights; the record set (§2.4 step 4) sees only where a
record *is now*, never where it *was*. The stored window already says where it was: `fuel_balance_window.record_ids`
holds the `[root_id, head_id]` pairs the assessment used (`service.py:124`).

**Data read: no new query, no migration, no index.** `schedule_inputs` already reads, on its one snapshot, (a) the tank's
fuel records as known in `[known_at − RECORD_LOOKBACK, known_at)` through K2's `select_fuel_records`, which returns
each record's `root_id` and current `head_id` (head = latest version as known; membership by the head's kind, tank and
occurrence), and (b) each night's latest window through `_windows_on`, which returns `record_ids`. Both are already
bounded to about 32 days. The fix only keeps two more fields from those two reads.

**Model (`fuel_balance/model.py`).** Add `field` to the `dataclasses` import. Append two fields at the END of
`ScheduleInputs` (defaults keep every existing positional constructor call valid, including the early return
`ScheduleInputs(known_at, tz, None, None, {}, (), {})`):

```python
    window_records: Mapping[date, tuple[tuple[str, str], ...]] = field(default_factory=dict)  # night -> its latest window's stored (root_id, head_id) pairs
    record_heads: Mapping[str, str] = field(default_factory=dict)  # root_id -> current head_id, same read as `records`
```

`records` keeps its 2-tuple shape (P5 unpacks it).

**Store (`fuel_balance/adapters/postgres_fuel_balance_store.py`, `schedule_inputs.work`).** Replace the `records = ...`
statement through the final `return ScheduleInputs(...)` of `work` with:

```python
            fuel = self._fuel_records(c, tenant_id, site_id, UUID(tank), known_at - record_lookback, known_at, known_at)
            records = tuple((r.occurred_at, r.recorded_at) for r in fuel)
            record_heads = {str(r.root_id): str(r.head_id) for r in fuel}
            zone = ZoneInfo(str(tz))
            lo = (known_at - record_lookback - timedelta(days=1)).astimezone(zone).date()
            hi = known_at.astimezone(zone).date() + timedelta(days=1)
            stored = _windows_on(c, tenant_id, site_id, UUID(tank), lo, hi, known_at)
            latest = {w.night_date: w.recorded_at for w in stored}
            window_records = {w.night_date: tuple((str(a), str(b)) for a, b in w.record_ids) for w in stored}
            return ScheduleInputs(known_at, tz, tank, generators[0], reading_nights, records, latest,
                                  window_records, record_heads)
```

Docstring of `schedule_inputs`: append "; per night, its latest window's stored record pairs, and per fuel record its
current head (D-R3.8)".

**Due rule (`fuel_balance/scheduled.py` `due_nights`).** New step 4b, inserted after the record loop and before
`return`:

```python
    # 4b (D-R3.8): an older ready night whose stored records changed since its latest window: a stored root whose
    # current head differs, or that is no longer a fuel record of this tank occurring inside the record read
    # (corrected to another time, tank or kind). Only nights whose whole window lies inside the record read are
    # compared; for an earlier night a stored record could be missing only because the read starts after it, which
    # would make the night due on every tick without changing its result.
    read_from = known_at - RECORD_LOOKBACK
    for night, held_ids in inputs.window_records.items():
        if night >= first_base or not ready(night) or rules.night_window(night, tz)[0] < read_from:
            continue
        if any(inputs.record_heads.get(root) != head for root, head in held_ids):
            due.add(night)
```

Why it converges (no spin): the re-assessment reads the night's records as they are now, and its digest covers the
record pairs (`rules.input_sha256(..., records=...)`), so a changed or removed pair always appends a revision whose
stored pairs equal the current heads; the night stops being due on the next tick. A night that is not ready (no
readings, or not quiet) is not touched, as in step 4.

Module docstring of `scheduled.py`, after the "Record set" bullet, add: "- **Left-record set (D-R3.8):** an older
ready night whose latest window cites a fuel record that has since been corrected or no longer counts for this tank."
§2.4 "What this means" gains, in effect: a correction that moves a record out of a night up to 31 days back re-checks
that night (its window must start at or after `known_at − 31 d`).

**No-DB test (`backend/tests/test_own_g2_fuel_night_due.py`).** Extend the helper, keeping the existing keyword order:

```python
def inputs(reading_nights=None, records=(), latest=None, known_at=KNOWN, tank=TANK, window_records=None,
           record_heads=None) -> ScheduleInputs:
    return ScheduleInputs(known_at, TZ, tank, None if tank is None else GEN, dict(reading_nights or {}),
                          tuple(records), dict(latest or {}), dict(window_records or {}), dict(record_heads or {}))
```

Add after `test_5_records_older_than_the_lookback_are_not_read`:

```python
def test_5b_a_record_that_left_an_old_night_rechecks_it() -> None:
    """D-R3.8. Fails on a record set that only looks at where a record is now."""
    old = L - timedelta(days=10)
    held = KNOWN - timedelta(days=9)
    stored = {old: (("r1", "h1"),)}
    # the stored record was corrected (new head; it now occurs elsewhere, so `records` has nothing on `old`)
    assert due_nights(inputs(seen(old), [], {old: held}, window_records=stored,
                             record_heads={"r1": "h2"})).nights == (old,)
    # the stored record is no longer a fuel record of this tank in the read (moved out of range, tank or kind)
    assert due_nights(inputs(seen(old), [], {old: held}, window_records=stored)).nights == (old,)
    # unchanged: same head, recorded before the window -> not due (fails on "any stored record makes it due")
    assert due_nights(inputs(seen(old), [(inside(old), held)], {old: held}, window_records=stored,
                             record_heads={"r1": "h1"})).nights == ()
    # not ready (no readings) -> not due, even with a changed record
    assert due_nights(inputs({}, [], {old: held}, window_records=stored, record_heads={"r1": "h2"})).nights == ()
    # the read-range edge: KNOWN - 31 d is 6 Oct 14:00 local. Night 6 Oct starts 18:00 local (inside) -> compared;
    # night 5 Oct starts before the read (a stored record may simply be unread) -> never compared (fails on spin)
    inside_read, outside_read = L - timedelta(days=30), L - timedelta(days=31)
    both = {inside_read: (("r1", "h1"),), outside_read: (("r2", "h2"),)}
    assert due_nights(inputs(seen(inside_read, outside_read), [], {inside_read: held, outside_read: held},
                             window_records=both)).nights == (inside_read,)
```

**Postgres test (`backend/tests/test_own_g2_fuel_night_tick_postgres.py`).** At the end of `test_p5_...` add one line:
`site["p5_dip"] = str(dip["id"])`. Then add, as the LAST test in the file (file order: Q1, P1/P2/P3/P6/P7, P4a, P4b/c,
P5, P5b):

```python
def test_p5b_a_correction_that_moves_the_dip_out_of_an_old_night_rechecks_it(site) -> None:
    """D-R3.8: N9 (outside the base set) is re-checked when its stored dip is corrected to the afternoon, returns to
    exactly its pre-dip result, and is not due again on the next tick."""
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store
    from assetops_backend.fuel_balance.scheduled import RECORD_LOOKBACK, due_nights

    engine, s, n9 = site["engine"], site["site_id"], site["nights"][9]
    dip_id = site["p5_dip"]
    revs = [w for w in _windows(engine, s) if w["night_date"] == n9]
    rev1, rev2 = revs[0], revs[-1]
    assert (rev1["revision"], rev2["revision"]) == (1, 2) and dip_id in _ids(rev2), revs
    moved = datetime.combine(n9, time(15), site["zone"]).astimezone(UTC)  # before N9 starts, after N8 ends
    correction = _post(_record(site, "TANK_DIP", "g2-p5b-correction", moved, "1", supersedes_record_id=dip_id,
                               canonical_record_id=dip_id, correction_reason="Dip was taken in the afternoon"))
    store = build_fuel_balance_store(URL)
    try:
        inputs = store.schedule_inputs(site["tenant_id"], s, RECORD_LOOKBACK)
    finally:
        store.dispose()
    print("G2 P5b heads", inputs.record_heads.get(dip_id), "held", inputs.window_records.get(n9))
    assert (dip_id, dip_id) in inputs.window_records[n9]
    assert inputs.record_heads[dip_id] == str(correction["id"])
    assert n9 in due_nights(inputs).nights
    fuel = _fuel(_tick(engine)[0], s)
    entry, rev3 = _night(fuel, n9), _latest(engine, s, n9)
    print("G2 P5b", entry, rev3["state"], rev3["limitations"], rev3["record_ids"])
    assert entry and (entry["assess"], entry["revision"]) == ("APPENDED", 3) and entry["raise"] is not None, entry
    assert dip_id not in _ids(rev3) and str(correction["id"]) not in _ids(rev3), rev3["record_ids"]
    assert (rev3["state"], sorted(_ids(rev3)), list(rev3["limitations"])) == (
        rev1["state"], sorted(_ids(rev1)), list(rev1["limitations"])), (rev1, rev3)
    again = _fuel(_tick(engine)[0], s)
    print("G2 P5b again", _night(again, n9))
    assert _night(again, n9) is None and _latest(engine, s, n9)["revision"] == 3
```

Rev 3 equals rev 1 because N9's readings and Foundation are unchanged since the CLI's rev 1, and its records are again
the ones rev 1 had. The dip's first version is its own root and head, hence `(dip_id, dip_id)`. If `_post` rejects the
correction body, copy P4c's exact call shape (it passed on Postgres); any other failure stops and goes to the Architect.

**How it fits the whole-file run (R3.2 unchanged).** P5b adds one correction post, one store read and two ticks after
P5, on the same module fixture; expect +2-4 min on the reviewer's measured 17.7 min, inside the 45-minute budget and the
stall rule. Run the file whole, one process, file order, `-s`, no `-k`/`-n`, as the only heavy job. Update the module
docstring's "Measured:" line to the new result ("6 passed in N s") and add "P5b (D-R3.8)" to its first line's case list.

#### R3.8.2 L2 — quiet looks only at tank readings: accepted for now, no change (D-R3.9)

- **Fail-safe by construction.** The assessment's slot rule is strict: any 5-minute slot of the night without a generator
  power or state reading makes `GENERATOR_KWH_UNKNOWN` / `IDLE_SECONDS_UNKNOWN` true (`fuel_balance/rules.py:170-203`;
  `actions/verification_rules.py:222` and `:295` match a slot's own readings only), and any such reason gives
  `NOT_ASSESSED` (`rules.py:304-315`), never `UNEXPLAINED`. So a night checked before its generator readings land can
  show "not assessed" for a while, but cannot open an unexplained-fuel Finding on missing generator data. The
  reviewer's "open then withdraw" path needs generator data that is complete and then changes, which is a correction,
  not lateness.
- **How real sites send data.** One site gateway publishes tank and generator signals in the same store-and-forward
  batches (Kisiwa's path), so 5 minutes of quiet on the tank readings is quiet on the generator readings too. A site
  with a separate generator logger on another link is the case that differs; there the night is re-checked on every
  tick for 7 nights (base set), so it settles as soon as the readings land.
- **After the demo** (added to §2.4's out-of-scope list in effect): quiet over every role the assessment reads, if a
  site with a separate generator data path is onboarded.

#### R3.8.3 L3 — one refused night blocks later nights: fixed now, narrowly (D-R3.10)

Real-site reasoning: nights are independent (each has its own lock and its own revision chain). A refusal about one
night's stored history must not stop the checks of later nights, which are the most recent and the ones the operator
acts on. The failure must still be visible (Site failure, `last_failure_stage`, back-off capped at 16 min,
`tick.py:91-92`, `:132-133`). `CLOCK_BACKWARDS` is the only per-night refusal the scheduler can meet (a window recorded
at an instant later than DB now: a DB clock step back or failover, or a tool that assessed at a future virtual instant).
`WINDOW_INVALID` cannot come from scheduler-computed nights and stays a defect that fails at once.

**`run_site` (`fuel_balance/scheduled.py`).** Import `CLOCK_BACKWARDS` from `model`. Before the loop add
`refused_nights: list[tuple[date, FuelBalanceRefused]] = []`. In the `except FuelBalanceRefused as refused:` block,
after the `ASSETS_UNSUPPORTED` branch and before the bare `raise`:

```python
            if refused.code == CLOCK_BACKWARDS:  # D-R3.10: this night only; later nights still run
                nights.append({"night_date": night.isoformat(), "assess": "REFUSED", "revision": None,
                               "state": None, "raise": None})
                refused_nights.append((night, refused))
                continue
```

After the loop, before building the return dict (so it also applies after an `ASSETS_UNSUPPORTED` break):

```python
    if refused_nights:
        raise FuelBalanceRefused(CLOCK_BACKWARDS, f"{len(refused_nights)} night(s) refused "
                                 f"({', '.join(d.isoformat() for d, _ in refused_nights)}); first: "
                                 f"{refused_nights[0][1].detail}")
```

A refused night counts toward `limit` (it used an assess call). The raise keeps the stage contract unchanged
(`stages.classify` gives `FAILED`; the error holds the code), while every later night's assess and raise are already
committed in their own transactions. Any other refusal (`WINDOW_INVALID`) still raises at once, unchanged.

**No-DB test (`backend/tests/test_own_g2_fuel_night_stage.py`).** Import `WINDOW_INVALID` beside `CLOCK_BACKWARDS`.
Replace `test_clock_backwards_raises_and_the_stage_fails_with_the_code` with:

```python
def test_clock_backwards_on_one_night_still_checks_later_nights_then_fails_the_stage() -> None:
    """D-R3.10. Fails on the old re-raise (L is never assessed) and on swallowing the refusal (no raise)."""
    store = FakeStore(inputs(seen(PREV, L)), {PREV: FuelBalanceRefused(CLOCK_BACKWARDS, "before revision 1")})
    findings = FakeFindings()
    with pytest.raises(FuelBalanceRefused) as refused:
        run_site(store, findings, "t", "s", 10, None)
    assert [c[1] for c in store.calls if c[0] == "assess"] == [PREV, L] and findings.calls == [L]
    assert refused.value.code == CLOCK_BACKWARDS and PREV.isoformat() in str(refused.value)
    assert stages.classify(refused.value) == "FAILED" and CLOCK_BACKWARDS in str(refused.value)


def test_any_other_refusal_still_fails_at_once() -> None:
    store = FakeStore(inputs(seen(PREV, L)), {PREV: FuelBalanceRefused(WINDOW_INVALID, "bad window")})
    with pytest.raises(FuelBalanceRefused) as refused:
        run_site(store, FakeFindings(), "t", "s", 10, None)
    assert refused.value.code == WINDOW_INVALID and [c[1] for c in store.calls if c[0] == "assess"] == [PREV]
```

§2.4 `run_site` step 2.1 now reads, in effect: `WINDOW_OPEN` skip; `ASSETS_UNSUPPORTED` stop as ineligible;
`CLOCK_BACKWARDS` record the night as `REFUSED`, continue, and fail the stage after the loop; any other refusal raise.

#### R3.8.4 Merge condition (replaces R3.6 items 1-2; items 3-5 stand)

1. `test_own_g2_fuel_night_tick_postgres.py` whole file under R3.2: **6 passed** (Q1/Q12, P1/P2/P3/P6/P7, P4a, P4b/c,
   P5, P5b), by the builder and again by the reviewer; the packet records the runtime and the `G2 ...` lines incl. P5b's.
2. The R3.6 item 2 no-DB set is green, including `test_5b_...` and the two stage tests above.
3. R3.6 item 3 needs no rerun (no stage, tick or limits file changes). The R3.4 confirming run on main is done
   (`review-G2.md` run 3) and stands.
4. A fresh Claude re-review of this fix round (M1, L3, the tests), then `--no-ff` merge and check-all on main, as R1.3
   says.

**D-R3.8 (for owner review).** A correction that moves a fuel record out of a night (wrong date, tank or kind) now
re-checks that night up to 31 days back, so an unexplained-fuel Finding never stays open on data that was corrected.
It reuses two reads the check already makes: no new query, table or migration. Cost: about 15 lines, one no-DB case
and one Postgres case (+2-4 min on the G2 run).

**D-R3.9 (for owner review).** Not changed now: a night may be checked before late generator readings arrive. It is
safe because missing generator data makes the night "not assessed", never "unexplained", and the night is re-checked
for 7 nights. Revisit only if a site sends generator data on a separate link.

**D-R3.10 (for owner review).** A problem with one night's stored history (a clock that moved backwards) no longer stops
the checks of later nights; the Site still shows the failure in health. Cost: about 10 lines and two no-DB tests.

---

## R4 — DS-1a residual rulings (2026-11-09)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`, main `b73c65eb6`). Owner away; decisions delegated
(`.agent/owner-away-architect-decides-2026-11-08.md`). Read-only; no Postgres run. Input: the two residual risks in
`AssetOpsV1-ds1a/.agent/review-DS-1a.md` ("Residual risk"). **READ** = code or file, cited.

### R4.1 Cold room "No action yet" on the Portfolio against ACT-002 in step 4: a product inconsistency; fix before E1

**Cause (READ).**
- `select_action_scope` reads Actions only for mini-grid Sites (`estate/index.py:256-259`, `applicable = ... == MINI_GRID`).
  Cold and EV domain Actions never reach `_action_for`, so every Cold/EV row gets `workflow_label(None)` = "No action
  agreed yet" (`estate/portfolio.py:226-229`), the bold cell "No action yet" (`EstatePortfolio.tsx:207`) and the
  placement reason "No action agreed yet · review the recommendation" (`estate/placement.py:33, 51`).
- The chain already knows the truth: thread sources include `domain_action` (`chain/adapters/postgres_thread_sources.py:73, 185`),
  `attach_threads` puts each row's thread (with `state`) on the row, and the K9 rehearsal build's F-THREADS read shows
  Cold threads `["Action agreed", "Open"]` and EV `["Action agreed"]` (`AssetOpsV1-k9/var/demo3_k9rehearsal/check.json`).
- So the Portfolio says "no action agreed" while the board, the Work page and the chain say one is. This is the same
  class as K8 L1, which R-1 fixed for the fuel row only (`FUEL_THREAD_LABEL`, `estate/portfolio.py:257-267`;
  `EstatePortfolio.tsx:153-154, 202-204`). DD1b2-R9's "nothing shown is false" was wrong: the row states "No action
  agreed yet", and that is false for the start-failure thread.
- **Why it matters on a real Site:** the Portfolio exists to tell a manager where nobody is acting yet. A row that says
  "no action agreed" when the site team already owns a witnessed start test sends the manager to chase work that is
  in hand, and teaches him not to trust the list. That is a fundamental, not polish.

**Ruling: fix it now with the R-1 mechanism, generalised. BL-47 (joining the Action itself, code and link) stays in
the backlog.** One source for "is someone acting": the thread state the chain already computed, read at the row's own
cutoff, exactly as the fuel row does. No new query, port, table or migration.

**Product change (branch `task/R4-1-domain-row-thread-state`, from main):**
1. `backend/assetops_backend/estate/portfolio.py`
   - Rename `FUEL_THREAD_LABEL` to `THREAD_LABEL` (same four entries; update its comment: "a row whose Action the
     Portfolio does not join: the fuel row (FUEL_BALANCE domain) and every Cold/EV row (`select_action_scope` reads
     mini-grid Actions only)").
   - In `portfolio_row`, replace the `label = ...` statement with:
     ```python
     unjoined = r.get("_mechanism") == "UNEXPLAINED_FUEL" or (
         action is None and DOMAIN_OF_SITE_TYPE.get(r["_domain"], NOT_APPLICABLE) in (COLD, EV))
     label = (THREAD_LABEL.get((r.get("_thread") or {}).get("state"), "No action agreed yet") if unjoined else None)
     ```
     (`COLD`, `EV`, `DOMAIN_OF_SITE_TYPE`, `NOT_APPLICABLE` are already imported at `:25-26`.) Mini-grid rows are
     unchanged: their join is authoritative, so a mini row with no joined Action keeps "No action agreed yet".
   - Effect: ACTION_IN_HAND → "Pending" (placement reason ACTION_PENDING, "Action accepted, not yet applied"; Cold
     start-failure rows stay in Act now because their episode is open); CHANGE_APPLIED → "Applied";
     RESOLVED_MONITORING/CLOSED → "Verified"; OPEN, RECURRED, no thread → "No action agreed yet" (unchanged). The Cold
     temperature row stays "No action yet": its own thread is Open, which is true.
2. `frontend/src/estate/EstatePortfolio.tsx`: rename `fuelThread` to `threadState` and drop the mechanism test:
   `const threadState = row.action_id === null && row.workflow_label !== "No action agreed yet";` (for a mini row with
   no Action the label is always "No action agreed yet", so mini rows are unchanged). Extend the MOCK DEVIATION
   comment: "MD-FUEL-K4-1, extended by R4.1 to Cold/EV rows: the Action column shows the row's thread state in bold
   when the Portfolio does not join the Site's Actions."
3. No change to `actionIndex.tsx`, the estate Actions list, `select_action_scope`, the cursor, COH-2's named
   expectation (`action_id` stays null, so it still applies) or any tool.

**Tests (no DB; no Postgres file is touched):**
- Backend, new `backend/tests/test_r4_domain_row_thread_state.py` (pure `portfolio_row` with a Cold and an EV row
  fixture; copy the row shape from `test_w303_portfolio_workflow_labels.py`):
  (a) Cold, no Action, thread `ACTION_IN_HAND` → `workflow_label` "Pending", placement ACT_NOW with reasons
  `[EPISODE_OPEN, ACTION_PENDING]`; (b) Cold, thread `OPEN` → "No action agreed yet"; (c) EV, `CHANGE_APPLIED` →
  "Applied"; (d) Cold, `_thread` None → "No action agreed yet"; (e) **must-fail guard**: a mini-grid row with no
  Action and thread `ACTION_IN_HAND` → "No action agreed yet"; (f) the fuel row is unchanged (one case).
- Frontend, `frontend/src/estate/__tests__/estatePortfolio.test.tsx`: a Cold row with `action_id: null`,
  `workflow_label: "Pending"` renders bold "Pending" with `data-portfolio-workflow`, has no "No action yet" text in
  its Action cell, and keeps the "Review finding" link; a Cold row with "No action agreed yet" still renders "No action
  yet" plus the workflow text.
- Run: the two files above, `test_w303_portfolio_workflow_labels.py`, `test_cc_placement.py`, and vitest for
  `estatePortfolio.test.tsx` and `estateRoots.test.tsx`. An existing test that pinned "No action agreed yet" on a
  Cold/EV row **with an in-hand thread** is updated and listed in the packet; any other change to an existing
  assertion stops the work and comes to the Architect.

**Proof on the demo build (E4 checklist item, no code):** on the "Portfolio, week to story day S" link, the two Cold
"Backup generator did not start" rows and the EV row read **Pending**, and the Cold temperature row reads **No action
yet**. If a start-failure row reads "No action yet", the Portfolio's thread state disagrees with the board (COH-13
would also fire): stop and bring it to the Architect; do not change the script to match.

**Size and slot:** 0.25 unit (Sonnet build; fresh Opus light review, High/Medium block). Lane B (free since G3b merged),
merged before E1 (Thu 12, 08:00), then check-all on main per R1.3. It touches no G1 file.

**DS-1a / DS-1f changes:**
- Replace `demo-script-img/03-portfolio-act-first.png` with the same crop from E5's Portfolio capture (1440), so the
  illustrative picture does not show the old text. ST-1 quotes the row words from that crop.
- ST-4, presenter note (add after the Say): "On the Portfolio, the start-failure rows read Pending: an action is
  agreed and not yet done, and the action is ACT-002 on this page. The temperature row reads No action yet, which is
  correct: no action has been agreed on the temperature itself."
- ST-4 "If asked" (add): "Why does the Portfolio not name ACT-002?" → "The Portfolio shows whether someone is acting;
  the action itself, its owner and its test are on the Site's Work page, one click away."
- Callout 3 stays: the Work page does show the owner.

**D-R4.1 (for owner review).** The Portfolio now reads "Pending" (not "No action yet") on Cold and EV findings that
already have an agreed action, from the same chain state the board shows. Naming the action itself on the Portfolio
row (BL-47, about 0.5 unit) stays after the demo.

### R4.2 Step 7, "a new day arrives": hold yesterday back for Kobo, release it during the session

**What exists (READ).**
- A real Site's readings arrive all day from its gateway; nobody adds a day. A whole day arriving at once does
  happen on remote sites: a gateway that loses its uplink stores its readings and sends them when the link returns.
  That is the only honest real-site picture of "a day arrives during the meeting".
- `add-dates` is the demo's gateway (§4.1). Per date it runs the Site's child and then one `Demo.tick()`, the product's
  own scheduled tick (`AssetOpsV1-g1/tools/demo_combined.py:1069-1090`); readings keep their story time and are
  recorded at real time (client-demo-plan §2.5.1a "Honesty rules"). R1.5's estimate: Kobo about 7 min plus one tick
  about 2 min, so **about 9 min** from start to the day being checked. Nothing arrives in 3 minutes.
- The morning catch-up (`add-dates`, to yesterday) leaves no ended day free, so the old plan's "the live step adds
  S+2" (client-demo-plan §2.5.1a) has no day to add unless one is held back.
- The frontend does not poll (no `refetchInterval`/`setInterval` in `frontend/src`): the presenter reloads the page.
- The serve's scheduler also ticks every two minutes (CO-2); the tool's tick only runs the same check sooner.

**Ruling.**
1. **The held day is Kobo's yesterday** (Site-local date). It is exactly the day the morning catch-up would have
   added, with the same `normal` kind, so no story content changes. Kobo is chosen because it is the Site the client
   has just seen and its board grades the day against its objectives.
2. **Morning runbook (replaces R1.5's single `add-dates` line on a demo day):**
   ```
   ... add-dates --site COLD-LAB-001,EV-LAB-001,KISIWA-001 --no-check      (catch up to yesterday)
   ... add-dates --site KOBO-001 --to <day before yesterday>               (Kobo stops one day short; ends with the finish check)
   ... links
   ```
   If `<day before yesterday>` is a Kobo story day, the second command refuses with `STORY_DAY`: nothing is missing,
   so run `... add-dates --site KOBO-001 --to <day before yesterday> --dry-run` to confirm, and run the first command
   without `--no-check` instead. If **yesterday** is itself a Kobo story day (a session on S+2 or earlier), there is
   no day to hold: run the R1.5 catch-up unchanged, and step 7 uses the backup pictures and says so.
3. **Live command (during the session, off-screen, in a second window):**
   `... add-dates --site KOBO-001 --to yesterday --no-check`. After the client leaves: `... add-dates` with no options
   (it adds nothing or today's catch-up and always ends with the finish check, `:1091-1092`). A FAIL retires the
   build (R1.5).
4. **When to start it:** at the end of the last Kobo step (ST-3, or ST-3b when present). That leaves ST-4 to ST-6
   (3 + 2 + 6 + 2 = 13 min) for about 9 min of work. The Fri 13 owner walkthrough times it; if start-to-checked
   exceeds 11 min, start it at the end of step 0 instead (the before view then moves to step 0).
5. **The before view is shown live**, so the change is seen, not asserted: at the end of the last Kobo step the
   presenter opens `http://localhost:<web>/sites/KOBO-001?date=<yesterday>` (the `links` Kobo board form with
   yesterday's date) and shows the day with no readings, quoting the board's own words (DS-1f placeholder from the
   walkthrough). In step 7 the presenter reloads that page.
6. **Only the Kobo board is promised.** The Portfolio's story-week link ends before yesterday, so step 7 does not
   claim a Portfolio change. The checklist row 7 "Expected" becomes: "Kobo board for yesterday: before, no readings
   (board's words); after reload, the day is checked (board's words)."
7. **Not done in time** (the tool's plain line "KOBO-001: added …" has not printed when step 7 opens, or it refused):
   show the walkthrough's before/after pictures, say "Yesterday's readings are still arriving; we will open the day
   again at questions", and do so. Never say the day has arrived before the line has printed.

**Exact script wording (DS-1a, ST-7; replaces the current Say, "If asked" and "What it means"):**
- *End of the last Kobo step, Say:* "One more thing at Kobo. This is yesterday: no readings yet. In this demo we held
  yesterday's readings back, the way a site's gateway keeps them when its connection drops. I am letting them
  through now; we will come back to this day at the end."
- *Step 7, Say:* "Kobo's readings for yesterday have now arrived, as a gateway sends its stored readings when its
  connection returns. I reload the page: the day has been checked by the same rules as every other day. Nobody
  rebuilt a report or touched a spreadsheet."
- *What it means:* "Data arrives from the site and the checks follow on their own. A late day is checked like any
  other, and the screens state which days were checked."
- *If asked, "How often does it update?":* "In this demo, at the next background refresh, every two minutes. How
  often a real Site's readings arrive is agreed for a pilot." (the M2 fix).
- *If asked, "Who added that day?":* "In this demo, I released readings that were held back. On a real Site they come
  from your meters through the gateway; nobody adds them."
- Step 7's time stays 3 min. The step-map label changes from "New day" to "Yesterday arrives".
- Still forbidden: "live", "real time", "within minutes" without "in this demo", and any claim that the day arrived
  by itself without the held-back sentence.

**No code change.** G1 is not reopened: everything above uses `add-dates` options in §4.2. DS-1a's Sonnet refresh
takes R4.1's script lines and R4.2's wording and runbook; DS-1f fills the before/after words from the Fri 13
walkthrough.

**D-R4.2 (for owner review).** Step 7 shows one real held-back day (Kobo's yesterday) being released during the
session and checked by the product's normal background check, said plainly as held back in this demo. It takes about
9 minutes, so it starts after the Kobo steps and is revealed at step 7; the morning catch-up stops Kobo one day short.

