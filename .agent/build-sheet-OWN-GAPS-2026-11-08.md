# Build sheet OWN-GAPS (2026-11-08): Kisiwa add-day, automatic diesel-night check, saving operational records

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only on code, main `2cf460aa5` (includes R-1 merge
`733eaf75c`). No Postgres or heavy run was made for this sheet.

Owner, verbatim (`.agent/owner-decisions-ingest-gaps-2026-11-08.md`): "here is my response to the architect 1- update
the demo tool to address the gap mentioned 2- Diesel night should be checked automatically 3-operational records should
be saved , the entry form should be updated as well as the subsequent backend logic"

---

## Revision 1 — owner answers 2026-11-08

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only on code, main `9aae0d003`. No Postgres or heavy
run. Owner, verbatim (`.agent/owner-answers-own-gaps-2026-11-08.md`): "i want all the fixes i asked for done now, with
the option for me to add dates so it can automatically udpate, see if this is clear to the architect. My reponse to the
open points 1. I'll add the data as i need it via the tool, nothing has to be done now, just ensuring the capcity for me
to do it 2.yes 3. "entered by site admin" 4.we are relaxing thte time, both are needed for the demo 5.illustrative is
fine 6.yes 7.Again , i don't know why this question is relevant, how does this relate to how a real site operates where
you can just show how site/portfolio is operating and add missing data through proper mechainsm when needed, i sense a
possible hardcoding of logic that should not be"

**This revision overrides the rest of this sheet where they differ.** §4 (G1) is replaced; §2.4, §3.1–§3.3 carry edits
marked "Rev 1"; §5 and §6 are superseded and kept only as history; §7 is the Q7 audit.

### R1.1 What the owner wants, in plain words (the Architect's understanding)

- **Build everything now.** G2 (diesel nights checked automatically), G3a and G3b (saving operational records from the
  screen, backend and form) and G1 (adding data days) are all built, reviewed and merged **before** the demo build. No
  item is cut and there is no cut order. The demo date gives way to this; 10 Nov is no longer fixed.
- **G1 is the owner's tool, not our daily chore.** The owner runs one command whenever he wants the demo Sites to be
  current: it adds the missing days, for any of the four Sites (Kobo, Cold, EV, Kisiwa), for any date or range of dates
  up to yesterday. The product then updates itself the way it would for a real Site: the background refresh checks the
  new days (G2 makes that include diesel nights) and every screen reads the new results. We schedule no roll-forward
  work; "nothing has to be done now" means the tool must exist and work, not that we pre-fill dates.
- **Q1 → one build, kept current by the owner with the tool.** The two-build plan (Part D.3) and the nightly add-day rows
  of old §5.2 are dropped.
- **Q2 yes:** the presenter may save a tank dip on screen during a client demo. It is a real, append-only write into the
  demo build, followed by the automatic re-check.
- **Q3:** records saved through the entry route are labelled **"Entered by site admin"** (replaces "Entered on screen").
  No person's name is recorded or claimed.
- **Q4:** the timing is relaxed; G1 and G3b are both required.
- **Q5:** the client script uses **illustrative pictures, taken once**, labelled as such. They are not retaken per build.
- **Q6:** the client script **opens on the Portfolio**.
- **Q7:** answered in §7. Short version: the question was only about the clock time of the 10-Nov meeting (to place
  the owner's walkthrough before it); it was not a product rule. The audit finds **no hard-coded story, date or Site
  logic in the product's monitoring path**. The dates mattered only because the demo data is generated once, at build
  time; with G1 the owner can bring the data up to yesterday at any time, which is how a real Site behaves.

### R1.2 What changed in this sheet

| Item | Change | Size (units, review included) |
|---|---|---|
| G1 | Rewritten (§4): owner-run `add-dates`, any Site, a date or a range up to yesterday, one command, prints what it added | **1.75** (was 1.25) |
| G2 | §2.4: the night buckets are derived from `rules.NIGHT_START/NIGHT_END` and `EDGE`, not typed as 17:30/12:30 (no second copy of the rule) | 2.25 (unchanged) |
| G3a | §3.2: attestation `job=site-admin-entry` (it serves both the screen and the G1 tool) | 1.0 (unchanged) |
| G3b | §3.3: By column reads "Entered by site admin" | 1.25 (unchanged) |
| DS-1a refresh | illustrative pictures, Portfolio opening, "checked automatically" wording, live dip beat, "Entered by site admin" | **0.5** (new step) |
| DS-1b | add short G1/G2/G3 sections and the owner's `add-dates` runbook | +0.25 on DS-1b |
| **Total build (G1–G3)** | | **6.25** (about 2 lane-days) |

### R1.3 New dated plan, starting now (Sun 8 Nov, evening)

Two lanes; **one heavy job at a time** (any Postgres test run, clone, capture, check-all, suite, prepare). Each slice
starts with an Opus pre-flight that sends **one batched question list**; the Architect folds the rulings into the
card. A fresh Opus reviewer per slice; High or Medium findings block; Sonnet fix rounds; merge `--no-ff`, then
check-all on main.

| When | Lane A | Lane B | Heavy job (in this order) |
|---|---|---|---|
| **Sun 8, evening** | G2 pre-flight (read-only) | G3a pre-flight (read-only) | K8c merge check-all, only if K8c is not merged yet |
| Sun 8, late | One batched question list (G2 + G3a) to the Architect; rulings folded into §2 / §3 | | — |
| **Mon 9** | G2-u1 (am), G2-u2 (pm) | G3a build (am), review (early pm), fix, merge; G3b build starts (pm) | ~12:30 G3a Postgres; ~15:00 G3a merge check-all; ~17:00 G2 Postgres (builder) |
| **Tue 10** | G2 review (am, reruns its Postgres file), fix, merge; then G1 pre-flight (batched questions) and G1 build, no-DB tests first | G3b build finish, fixture captures, review (pm), fix, merge | ~09:30 G2 review Postgres; ~11:30 G3b captures; ~13:30 G2 merge check-all; ~17:30 G3b merge check-all |
| **Wed 11** | G1 build finish (am); G1 rehearsal (§4.3); G1 review (pm), fix, merge | **DS-1a refresh** (Sonnet, 0.5 unit with its review); DS-1b drafting incl. G sections (trails; not on the demo path) | ~12:00–13:30 G1 rehearsal; ~17:30 G1 merge check-all |
| **Thu 12** | **E1** 08:00 code freeze, tag main. **E2** (Part F.3: clock check, template rebuild, T6, `-Tier fast`, slow pair plus the G2 Postgres file if slow-marked, vitest, check-all), about 08:00–10:45; reserved fix round to ~12:00. **E3** into `assetops_polish_client_test`, about 12:00–14:30 (cap 15:00); prepare day 12 Nov, so S = 10 Nov (date rule passes). **E4** with live ticks, plus: KIS-11, `fuel_night` OK for KISIWA-001 and `eligible: false` for Cold/EV, entry switched on. **First owner-tool run**: `add-dates --to yesterday`, then `finish check`. **E5** (adds `oprecords` 1440/390). **DS-1f** (figures checked against `check.json`; dated links from `links`). DS-1a merge, check-all ~17:30 | | E2, E3, E4, add-dates, E5, check-all — in sequence |
| **Fri 13, 09:00–10:30** | **Owner walkthrough** with DS-1a on the build, including one `add-dates` run and one on-screen tank dip | | the walkthrough's own catch-up |
| Fri 13, rest | High notes only: one fix round, then E3–E5 again (Fri prepare, S = 11 Nov, legal); other notes go to one batched round before 16 Nov or to after the demo | | E3–E5 if needed |
| Each demo day | **Owner**, at least 3 h before: `add-dates` (catch-up to yesterday), which ends with `finish check`; then E4-lite (serve with ticks, one completed tick, prewarm, the three K8c-r probes) | | one at a time |

- **The 10-Nov session moves.** All four items cannot be built, proven and walked through by 10 Nov.
- **Earliest demo-ready: Fri 13 Nov, about midday** (walkthrough with no High note). **With one High fix round: Sat 14
  Nov.** The 16–20 Nov week is safe either way. Recommendation: hold the first client session on **Mon 16 Nov**, or on
  Fri 13 afternoon if the owner wants it sooner and accepts no slack.
- **Capacity.** Lane A: G2 2.25 + G1 1.75 = 4.0 units over Mon–Wed (about 9 available). Lane B: G3a 1.0 + G3b 1.25 +
  DS-1a refresh 0.5 = 2.75. The binding constraint is the heavy-job queue; the times above do not overlap.
- **Dependencies.** G3b needs G3a; G1 needs G2 and G3a merged; E1 needs all four merged plus DS-1a refresh drafted.
  G2 and G3a share only `tools/demo_combined.py` (different functions) and merge one after the other.
- **If a slice needs a second fix round,** the slip goes into Thu morning before E1; past Thu noon, E1–E5 move one day
  and demo-ready becomes Sat 14 (no High) or Sun 15 (with one).

### R1.4 DS-1a client script refresh (branch `task/DS-1a-client-script`) — size 0.5 unit

Sonnet build, 0.3; fresh Opus light review (forbidden words, no cross-Site sums, claims the screen supports), 0.2.
Wed 11, before E1; finalised in DS-1f on Thu.
- **Pictures:** keep the existing crops as **illustrative** pictures, with one caption under the first: "Pictures are
  from a rehearsal build. Dates and some figures on your screen will differ." Add two: the Operational records form
  (from G3b's fixture captures) and a Kisiwa week with checked nights (from E5). The script quotes dates as story days
  ("the night five days before"); the presenter takes real dates from `links`.
- **Opening:** step 1 is the Portfolio. With G1 run up to yesterday, Kisiwa's week shows checked nights; any still
  unchecked days are named, and the presenter line says so plainly.
- **Wording now allowed:** "Each night's fuel is checked automatically once that night's tank readings have come in.
  In this demo the background refresh runs every two minutes." "Records typed here are entered by the site admin."
- **New beat (Q2):** on Operational records, save a tank dip for the newest added Kisiwa night at 06:00 with the
  value `links` prints; show it listed as Submitted, "Entered by site admin"; after the next refresh, open that night
  and show it re-checked. Presenter note: use only the night and value `links` prints; a dip on a story night would
  honestly re-check that night and can change the story.
- **Still forbidden:** theft words; any combined money total; "real time"; a production cadence claim; naming a person
  as the one who typed a record.

### R1.5 The owner's runbook (goes into DS-1b and the presenter checklist)

```
python tools/demo_combined.py --db assetops_polish_client_test --work var/polish_client serve      (if not running)
python tools/demo_combined.py --db assetops_polish_client_test --work var/polish_client add-dates   (catch up to yesterday)
python tools/demo_combined.py --db assetops_polish_client_test --work var/polish_client links       (today's dated links)
```

`add-dates` ends with `finish check` and prints one line per Site and date. About 20 min per missing date for all four
Sites (Kobo ~7, Cold ~4.5, Kisiwa ~3–8 incl. its 5-min quiet wait, EV ~3.5 on Tuesdays only, one tick ~2), plus ~5 min
for the check. If more than about 7 dates are missing, a fresh prepare (~2.5 h) costs the same; if the demo is more than
about 25 days after S, prepare fresh (§7.3).

### R1.6 Remaining owner question

1. **When is the first client session now?** Earliest Fri 13 Nov afternoon (no slack); recommended Mon 16 Nov.

---

Background: `.agent/architect-answers-owner-ingest-captures-2026-11-08.md` (T1, T3) and
`.agent/architect-combined-pass-2026-11-08.md` Parts C–F. Fuel rulings carried from `.agent/build-sheet-DIESEL-1.md`:
the wording is "unexplained fuel", never theft; fuel money is never summed with any other amount.

| Item | What | Size (units, review included) | Lane |
|---|---|---|---|
| **G2** | Automatic diesel-night check: a `fuel_night` stage in the schedule tick | **2.25** (two build units) | A |
| **G3a** | Saving operational records: backend entry route and server identity | **1.0** | B |
| **G3b** | Saving operational records: the live entry form | **1.25** | B |
| **G1** | (Rev 1) Owner-run `add-dates` in the demo tool: any of the four Sites, a date or a range up to yesterday, fed through the product's real paths | **1.75** | A, after G2 and G3a |
| | **Total** | **6.25** (about 2 lane-days) | |

~~Ruling on timing (§5): none of G1–G3 goes into the 10-Nov build.~~ **Superseded by Revision 1 (R1.3):** all four are
built Mon 9 to Wed 11 Nov and go into one demo build on Thu 12 Nov. No migration is needed: the head stays
`0058_fuel_watermark_inputs`, and `0059` stays unused.

---

## 1. Shared rules (all three items)

- **Wording.** Client copy says "unexplained fuel" and "fuel check". It never says theft, stolen, siphon or pilfer
  (`tools/checks/fuel_wording.py` runs in check-all). It never shows a total that adds fuel money to any other money.
- **DB time.** Every scheduled write takes the database's `clock_timestamp()`, never the host clock (S4-02d I3,
  FIX-COLD-DRAIN). This follows Part F's clock-skew finding.
- **Append-only.** Nothing is updated or deleted. A re-check appends a new window revision only when its inputs digest
  changes (`fuel_balance/service.py`, `input_sha256`).
- **One heavy job at a time.** Heavy means any Postgres test run, prepare, clone, capture, check-all, or the full suites.
- **Mock fidelity.** The mock is the layout spec (`frontend/mockups/v69/index.html:983-987`, screen `oprecords`,
  manifest `screen-manifest.json:2205-2220`). Every departure carries a label `MOCK DEVIATION MD-OWN-G3-n` in the code
  comment and in `.agent/mock-departure-register.md`.
- **Builders make no design decisions.** If a card here does not fit the code, the builder stops and asks the
  Architect. Questions are batched once per slice, at pre-flight.

---

## 2. G2 — the automatic diesel-night check (product, scheduler)

### 2.1 What changes, in plain words

Today a diesel night is checked, and its unexplained-fuel Finding raised, only when someone runs
`python -m assetops_backend.fuel_balance.worker assess|raise` by hand (`fuel_balance/worker.py:1-14`). After G2, the
regular background refresh, the schedule tick, does it for every diesel Site. It checks a night once that night's tank
readings have arrived and gone quiet. It checks again whenever a new fuel delivery or tank dip touches a recent night.

This closes two after-the-demo items from DIESEL-1: "fuel-balance tick stage" (`build-sheet-DIESEL-1.md:1595`) and
"fuel-finding tick stage" (`:2834`). **"Fuel verdict tick stage" (`:3965`, `:4291`) stays open.** The Action's fuel
verdict is still judged explicitly.

### 2.2 Where in the tick (`backend/assetops_backend/scheduling/tick.py` `_site`)

- A new child **`fuel_night`** runs **after `mini` and before `opportunity`**, under the **`MINI` head stage**. The claim
  is re-checked with `stage("MINI")`, the same way `chain_threads` runs under `S4`.
  - The new order: `s3, cold_assess, ev_assess, mini, fuel_night, opportunity, s4, chain_threads, consequence,
    cold_consequence, ev_consequence, chain_snapshots`.
  - Why before `chain_threads`: a raised fuel Finding revision emits `finding.revised` (the `finding_revision` producer,
    `migrations/versions/0044_chain_events.py:66`). The same tick's `chain_threads` then places it on its thread. The
    0058 triggers on `fuel_balance_window` and `fuel_residual_consequence_revision` let the same tick's
    `chain_snapshots` rebuild the stored bodies.
- **No migration.** `schedule_site_head.stage` keeps its CHECK set (`0030_w4_mini_decisions.py:233`).
  `last_failure_stage` is free text (`0013_schedule_state.py:80`). The stage writes **no head counts**: its counts
  appear only in the tick report and the perf line.
- Code (exact shape):

```python
if not stage("MINI"):
    return
rf = self.runner.run("fuel_night", {**ids, "limit": self.limits.fuel_nights_per_site,
                                    "deadline_at": _deadline_at(self.limits.fuel_night_seconds)},
                     self.limits.fuel_night_seconds)
site.stages["fuel_night"] = rf
if rf["code"] != "OK":
    failure = failure or ("FUEL_NIGHT", rf["code"], str(rf.get("error")))
```

- **`TickLimits`** gains `fuel_nights_per_site: int = 10` and `fuel_night_seconds: float = 90`.
  - `__post_init__`: `fuel_nights_per_site >= 1` joins the "at least 1" `min(...)`. `fuel_night_seconds > 0` gets its
    own check, message "The fuel_night stage bound must be positive.". `fuel_night_seconds` joins the
    statement-timeout `min(...)`.
  - `site_lease_seconds` adds `+ self.fuel_night_seconds`.
  - `STAGE_LIMIT_FIELDS["fuel_night"] = "fuel_night_seconds"`.
  - `TickReport.as_json` already copies `processed`, `deferred` and `elapsed_ms`. Add `"eligible"` to that key tuple.
- The tick module docstring (`tick.py:1-35`) gains the stage in point 5 and one sentence: "OWN-G2 adds `fuel_night`
  after `mini`: the due diesel nights of the Site are assessed and their unexplained-fuel Finding raised, at DB time."

### 2.3 The stage child (`backend/assetops_backend/scheduling/stages.py`)

`fuel_night(url, args)` is registered in `STAGES` and named in the module docstring's stage list and the `OK` list.

```python
def fuel_night(url, args):
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store, build_fuel_finding_service
    from assetops_backend.fuel_balance.scheduled import run_site
    t, s = _uuid(args["tenant_id"]), _uuid(args["site_id"])
    store = build_fuel_balance_store(url)            # DB clock: no override
    findings = build_fuel_finding_service(url)       # DB clock: no override
    try:
        return run_site(store, findings, t, s, int(args["limit"]), _deadline(args))
    finally:
        _dispose(store, findings)
```

Errors propagate to `main`'s existing handler, which turns them into `classify(...)` → `TIMEOUT`/`UNAVAILABLE`/`FAILED`.

### 2.4 The due-night rule (new `backend/assetops_backend/fuel_balance/scheduled.py`)

Constants: `BASE_NIGHTS = 7`, `RECORD_LOOKBACK = timedelta(days=31)` (the work backdate limit, `work/model.py:37`, plus
one day), `QUIET = timedelta(minutes=5)`, and `EDGE = timedelta(minutes=rules.EDGE_SEARCH_MIN)`, which is 30 min.

**One read, `PostgresFuelBalanceStore.schedule_inputs(tenant_id, site_id, base_nights, record_lookback)`.** It runs in
one read-only transaction, with `known_at` = `clock_timestamp()` taken first. It returns `ScheduleInputs`:

- `known_at`.
- `timezone`, from the `site` row.
- `tank_asset_id` and `generator_asset_id`. Each is set only when the Site has exactly one active `FUEL_TANK` and
  exactly one active `GENERATOR`; otherwise both are `None` and the read stops there.
- `reading_nights: dict[date, datetime]`: night date → the latest `decided_at` of its tank `fuel_level` readings, as
  known at `known_at`. One aggregate SQL, over the same join and acceptance filter as
  `PostgresActionStore.window_readings` (`actions/adapters/postgres_action_store.py:600-608`), restricted to
  `e.role = 'fuel_level' AND e.asset_id = :tank`. It buckets the Site-local instant `lt = COALESCE(e.interval_start,
  e.source_time) AT TIME ZONE :tz` like this:
  - `lt::time >= '17:30'` → `lt::date`;
  - `lt::time < '12:30'` → `lt::date - 1`;
  - otherwise no night.

  **Rev 1:** the two bounds are not typed as literals. They are computed from the rule's own constants:
  `rules.NIGHT_START − EDGE` (17:30) and `rules.NIGHT_END + EDGE` (12:30), passed to the SQL as bound parameters, so the
  fuel-balance-1 night window has one source. A unit test pins that changing `NIGHT_START` moves the bucket.

  This is a night's read range `[start − 30 min, end + 30 min)` in local time. Two nights' ranges never overlap. The
  bucket is only a trigger: the assessment itself uses the exact `rules.night_window`. Time range read:
  `[known_at − record_lookback − 1 day, known_at]`.
- `records: list[(occurred_at, recorded_at)]`: the tank's fuel records as known, from the existing injected
  `fuel_records` reader (`FuelRecord.occurred_at`, `.recorded_at`, which is the head's). Range:
  `[known_at − record_lookback, known_at]`.
- `latest: dict[date, datetime]`: each night's latest window `recorded_at`, from the existing `windows(...)` read over
  the same nights.

**`due_nights(inputs) -> DuePlan(eligible, nights: list[date])`.** This is a pure function.

1. If `tank_asset_id is None`, return `eligible=False` with no nights. Cold and EV Sites take this path.
2. `L` = the latest night date `d` whose `rules.night_window(d, tz)` end satisfies `end + EDGE <= known_at`, which is
   the service's own closed rule (`service.py`, `WINDOW_OPEN`). Night `d` is **ready** when `d in reading_nights` and
   `reading_nights[d] <= known_at − QUIET`.
3. **Base set:** every ready `d` in `[L − 6, L]`.
4. **Record set:** for each record, take the night `d` whose `[start, end)` holds `occurred_at`. Add `d` when `d < L − 6`,
   `d` is ready, and either `d not in latest` or `recorded_at > latest[d]`.
5. Due = base ∪ record set, sorted ascending.

**What this means:**
- **A night with no tank readings is never assessed and gets no row.** That covers Kobo, which has a tank but publishes no
  `fuel_level` (`build-sheet-DIESEL-1.md:737`). So Kobo's MG-8 stays NOT_APPLICABLE (`:2750`). It also covers any night
  after the last published Kisiwa run.
- A night is first checked after its window is closed **and** its tank readings have been quiet for 5 minutes. That
  avoids checking a night in the middle of a batch.
- A later delivery or dip on a night up to 31 days back, or a late reading in the last 7 nights, triggers a re-check.
  Out of scope, listed for after the demo: a later Foundation correction (accuracy, SFC, no-load rate) on a night older
  than 7 days, and late readings older than 7 nights.

**`run_site(store, findings, tenant, site, limit, deadline) -> dict`:**

1. Read `schedule_inputs`, then compute `due_nights`. If `eligible` is false, return
   `{"code": "OK", "eligible": False, "processed": 0, "deferred": 0}`.
2. For each due night, in order, while fewer than `limit` have been processed and `time.time() < deadline`:
   1. Call `FuelBalanceService(store).assess_night(...)`.
      - `WINDOW_OPEN`: skip the night.
      - `ASSETS_UNSUPPORTED`: stop, and return `eligible: False` with what has been done so far.
      - Any other `FuelBalanceRefused`: raise it, so the stage fails with `FAILED` and an error that holds the code.
   2. Then call `findings.raise_night(...)`.
   3. Record the night as
      `{"night_date", "assess": "APPENDED"|"REUSED"|"OPEN", "revision", "state", "raise": <RaiseResult.status>}`.
3. Return `{"code": "OK", "eligible": True, "processed": n, "deferred": len(due) − n, "appended": a, "reused": r,
   "raised": {status: count}, "nights": [...]}`.

**Each night's assess and raise run in their own transactions** (already true in `service.py` and
`findings_service.py`). A failure on one night keeps the earlier nights. The next tick recomputes the due set, so no
state is needed.

**Idempotent:** with unchanged inputs, assess returns `REUSED` (the digest is equal) and raise returns `UNCHANGED` or
`NO_FINDING`. Neither writes a row.

**Failure handling:** a non-OK stage sets the Site failure `("FUEL_NIGHT", code, error)` and the Site's normal back-off.
Every other stage of that Site still runs ("every stage runs even after an earlier stage failed",
`tick.py:31-33`). The health read already shows `last_failure_stage` (`scheduling/health.py:142`, `:291`).

`fuel_balance/worker.py` docstring: replace "There is no tick stage, job domain or HTTP route in v1." with "OWN-G2: the
schedule tick's `fuel_night` stage assesses and raises the due nights automatically; this CLI remains for explicit runs."
Nothing else in the CLI changes.

### 2.5 Effect on the existing Kisiwa story, the KIS rows and COH

- **Story nights do not move.** The prepare already proves this at DB time: `cli_assess_check` (ten `REUSED`, revision 1)
  and `cli_raise_check` (night 4 `UNCHANGED`, the others `NO_FINDING`) (`tools/demo_combined_kisiwa.py:793-830`). The
  stage makes the same calls, so on the story nights it writes **zero rows**.
  - The story's records were all recorded before each night's assess instant (deliveries +30 min, dips +15 min;
    assess at run end + 30 min), so the record set is empty.
  - Ticks run only after every child, Kisiwa included (`tools/demo_combined.py:541-595`; "No tick may run before the
    mill step"). The stage therefore cannot pre-empt K7's story-instant assessments. That would refuse
    `FUEL_BALANCE_CLOCK_BACKWARDS`.
- **Night S+1 has no readings** (the runs end at S+1d 12:00Z), so it gets no row. The Portfolio's "Kisiwa 0 of 7 days
  checked" line is unchanged.
- **New finish row KIS-11** (G2 owns it, in `tools/demo_combined_finish.py`, not mutating). On the build:
  - the latest tick report has a `fuel_night` entry for KISIWA-001 with code `OK` and `eligible: true`;
  - every story night's latest window has `revision = 1`;
  - Kisiwa has exactly one fuel Finding;
  - KOBO-001 has zero `fuel_balance_window` rows.

  Source of the tick report: the tick child's stdout JSON, which `Demo.tick` already prints. G2 adds writing
  `<work>/last-tick.json` in `Demo.tick`, and KIS-11 reads that file.
- **KIS-3, KIS-4, KIS-9 and COH:** no change. KIS-3 and KIS-9 filter to the story nights (`demo_combined_finish.py:1385`);
  KIS-4 reads all windows and Findings, and G2 adds none to a story build.
- **Prepare time** grows by the child start per Site per tick, about 1–2 s, and about 1–3 s of Kisiwa's REUSED nights.
  That is about +2–5 min on E3. No cap changes.

### 2.6 Files

- `backend/assetops_backend/scheduling/tick.py`, `scheduling/stages.py`
- `backend/assetops_backend/fuel_balance/scheduled.py` (new), `fuel_balance/adapters/postgres_fuel_balance_store.py`
  (`schedule_inputs`, `ScheduleInputs`), `fuel_balance/worker.py` (docstring only)
- `tools/demo_combined_finish.py` (KIS-11), `tools/demo_combined.py` (`Demo.tick` writes `last-tick.json`)
- Tests listed in §2.7. Existing tests change **only** where they pin the stage list or the lease sum:
  `test_ch0_tick_timing.py`, `test_ch1b_drain.py`, `test_fix_cold_drain_stage.py`,
  `test_fix_cold_drain_tick_postgres.py`, `test_w402_mini_stage.py`, `test_w402_mini_stage_postgres.py`,
  `test_w403_opportunity_stage.py`. Their fake runners must also return an OK `fuel_night` result.

### 2.7 Tests

**Units (no DB): `backend/tests/test_own_g2_fuel_night_due.py`.** Each case must fail on the named wrong
implementation.

1. Bucket edges (Africa/Dar_es_Salaam): local 17:29 → no night; 17:30 → night d; next day 12:29 → night d; 12:30 → no
   night.
2. Closed edge: `known_at = end(L) + 30 min` → L is closed; 1 s earlier → L − 1.
3. A closed night with no reading is not due. This is the S+1 case; it must fail if `range(L−6, L+1)` is used directly.
4. Quiet: last `decided_at = known_at − 4 min 59 s` → not due; `− 5 min` → due.
5. Record set:
   - a record on night L − 10 with `recorded_at > latest` → due;
   - `recorded_at == latest` → not due;
   - a night with no window and a record → due;
   - a record 32 days back → not read.
6. Order is ascending; with `limit` 3 of 5 due, the result shows processed 3 and deferred 2.
7. Ineligible: 0 tanks; 2 generators. Each gives `eligible: False` and no further reads (the fake store counts calls).

**Units (no DB): `backend/tests/test_own_g2_fuel_night_stage.py`**, fake stores:
- REUSED, then raise `UNCHANGED`;
- a night refused `WINDOW_OPEN` is skipped;
- `CLOCK_BACKWARDS` raises, and the error holds the code;
- a passed deadline starts no night and counts them deferred;
- the stage args carry `deadline_at`.

**Units (no DB): additions to `backend/tests/test_s4_schedule_*` style (`InProcessRunner`):**
- the exact stage order of §2.2;
- a failing `fuel_night` → Site `FAILED`, failure `("FUEL_NIGHT", ...)`, and every later stage still ran;
- `TickLimits(fuel_night_seconds=0)` and `TickLimits(fuel_nights_per_site=0)` raise;
- `site_lease_seconds` grew by exactly `fuel_night_seconds`;
- `STAGE_LIMIT_FIELDS["fuel_night"]`.

**Postgres: `backend/tests/test_own_g2_fuel_night_tick_postgres.py`** (`*_test` DB via `pg_harness`; reuse the Site,
readings and record fixtures of `test_k4a_fuel_finding_postgres.py`; real `StageRunner` children):

- **P1.** After the night closes and goes quiet, tick 1 appends revision 1 and raises. Tick 2 adds no row to
  `fuel_balance_window`, `finding_revision` or `fuel_residual_consequence_revision` (counts equal).
- **P2.** A night with no `fuel_level` readings gets no row.
- **P3.** A Kobo-like Site (tank and generator, no `fuel_level`): zero `fuel_balance_window` rows after two ticks.
- **P4.** A dip posted after night N's revision 1, which conflicts with the sensor: the next tick appends revision 2
  with the record in `record_ids` and the `DIP_SENSOR_CONFLICT` limitation.
  - A delivery that turns an UNEXPLAINED night into WITHIN_MARGIN: the next tick's raise is `WITHDRAWN`.
  - The fixture has one UNEXPLAINED night, so `OPENED` is proven too.
- **P5.** A record on a night 10 days back, already assessed, is re-checked. A record 40 days back is not read.
- **P6. Story invariance.** Nights assessed and raised earlier at story instants through the CLI (as K7 does) give
  REUSED/UNCHANGED from the stage and add zero rows.
- **P7.** Every stamp is DB time: the new window's `recorded_at` lies between two `clock_timestamp()` reads taken around
  the tick.

### 2.8 Size, risk, review

- **Size 2.25 units.**
  - G2-u1 (0.75): `scheduled.py`, `schedule_inputs`, the stage child and the no-DB tests.
  - G2-u2 (0.75): the tick wiring, the limits, the existing-test updates, the Postgres test, KIS-11 and `last-tick.json`.
  - Review plus fix: 0.75.
- **Risk: medium.** The scheduler is a protected seam, and every tick runs the stage.
  - Mitigations: no migration; the stage is isolated (its failure never stops other stages); P6 and KIS-11 prove story
    invariance; on story data the stage is idempotent and writes nothing.
- **Review:** one fresh Opus reviewer, which reruns the targeted Postgres file as one heavy job. Findings of High or
  Medium block. Codex reviews retrospectively in the milestone batch.

---

## 3. G3 — saving operational records from the screen (product)

### 3.1 The identity ruling (Architect decision; owner informed)

- **Why the form saves nothing today.** It is more than inert UI. The app injects no work principal: a work write is 403
  (`main.py:603-609`). A client-sent actor never authenticates (closure 3 Q28, `work_api.py:20-23`). A USER actor is
  refused because there is no signed-in user (`work/model.py:277-280`).
- **Ruling.** Records typed on screen are written by a **server-configured entry service**, `service:operator-entry`.
  The browser never sends an actor. The server composes the attestation and calls the existing
  `WorkService.post_operational_record`. That means the same validation, idempotency, hashing, REC code, correction
  lineage and audit columns as every other record.
- **Switched on only by server configuration.** The environment variable `ASSETOPS_OPERATIONAL_ENTRY=on` is read in
  `host/lab_app.py` `build_app`, the way the gateway variables are. The demo `serve` environment sets it. Without it
  the route answers 403 `WORK_WRITE_FORBIDDEN`, and the form says so.
- **What it does not prove.** It does not say which person typed the record. **Rev 1 (owner Q3):** the list shows
  **"Entered by site admin"** in the By column (was "Entered on screen"). That names the role of the entry point, not a
  person. A signed-in user identity is still an after-the-demo item.
- **Rev 1: one entry point for the screen and the G1 tool.** G1 posts its Kisiwa dips and deliveries through this same
  route, so they carry the same service identity and the same label. That is honest: in the demo the owner, running the
  tool, is the site admin entering records.

### 3.2 API contract (G3a)

**`POST /api/sites/{site_code}/work/operational-entries`** is added to `work_api.py` `build_work_router`, with a new
keyword `entry_principal: Principal = no_service_principal` and a new keyword `site_context`.

Request, a closed object (any other key → 422 `OPREC_ENTRY_INVALID`):

```json
{"entry": "TANK_DIP" | "FUEL_DELIVERY" | "STOCK_IN_CHAMBER" | "METER_READING",
 "value": "198",
 "taken_at_local": "2026-11-14T06:00",
 "ticket_reference": null,
 "idempotency_key": "oprec-entry-<32 lowercase hex>"}
```

Validation, in order:

1. `entry` is one of the four.
2. `value` is a decimal string matching `^\d{1,6}(\.\d{1,3})?$`. For `FUEL_DELIVERY` it must be > 0.
3. `taken_at_local` matches `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$` and is a valid date and time.
4. `ticket_reference` is required (non-null) exactly for `FUEL_DELIVERY` (`OPREC_ENTRY_TICKET_REQUIRED`), and null
   otherwise. It matches `^[A-Za-z0-9][A-Za-z0-9 /._-]{0,39}$`.
5. `idempotency_key` matches `^oprec-entry-[0-9a-f]{32}$`.

Each failure is 422 `OPREC_ENTRY_INVALID`, except the ticket case.

Server mapping. The body literals are the K7 literals (`tools/demo_combined_kisiwa.py:201-203`), so screen and demo
records read alike:

| entry | kind | unit | asset_id | body | source_document_sha256 |
|---|---|---|---|---|---|
| TANK_DIP | TANK_DIP | L | the Site's one active FUEL_TANK | `Tank dip at the {HH:MM} round: {value} L.` | null |
| FUEL_DELIVERY | FUEL_DELIVERY | L | the tank | `Fuel delivery of {value} L received, ticket {ticket_reference}.` | sha256 of ASCII `Fuel delivery ticket {ticket_reference}, {value} L` |
| STOCK_IN_CHAMBER | MANUAL_READING | kg | absent | `Stock in chamber: {value} kg.` | null |
| METER_READING | MANUAL_READING | kWh | absent | `Meter reading: {value} kWh.` | null |

Other fields:
- `occurred_at` = `taken_at_local` in the Site's `timezone` (zoneinfo, fold 0) as UTC ISO. `{HH:MM}` is the local
  time as typed.
- `period_end` and `case_id` are null.
- The actor is `{"kind": "SERVICE", "id": "service:operator-entry", "attestation":
  "service=operator-entry;job=site-admin-entry;rule=oprec-entry/1"}` (Rev 1: was `job=screen-entry`).
- The principal passed to the service is `"service:operator-entry"`.
- The tank and timezone come from `site_context(tenant_id, site_id) -> (timezone, tank_id | None)`. It is composed in
  `main.py` from `build_fuel_balance_store(database_url()).night_context` (returns the timezone, the one active tank or
  None, and the read instant; `postgres_fuel_balance_store.py:236-246`).
- A fuel entry with no single tank → 422 `OPREC_ENTRY_NO_TANK`, message "This Site has no single fuel tank to record
  against.".

**Refusal order:**
1. Site read access 401/403 and unknown Site 404 (`open_scope`, as today).
2. Entry principal absent → 403 `WORK_WRITE_FORBIDDEN`.
3. No store → 503 `WORK_STORE_UNAVAILABLE`.
4. Shape 422.
5. Tank and timezone.
6. The service: its own codes, unchanged — `WORK_OCCURRED_AT_FUTURE` (more than 5 min ahead),
   `WORK_OCCURRED_AT_TOO_OLD` (more than 30 days back), `WORK_RECORD_QUANTITY_INVALID`, `WORK_EVENT_DUPLICATE_KEY`
   (same key with a different body), and their statuses from `work/model.py` `STATUS`.

**A refusal writes nothing. Success** is the service's own result: 201 with the lineage body, or 200 with the stored
body for an identical retry (`work_api.py:15`).

The new codes go into `work/model.py` `MESSAGES` and `STATUS`: `OPREC_ENTRY_INVALID` 422, `OPREC_ENTRY_TICKET_REQUIRED`
422, `OPREC_ENTRY_NO_TANK` 422. The mapping lives in the new module `backend/assetops_backend/work/operational_entry.py`,
as `compose_entry(body, timezone, tank_id) -> dict` (pure) plus constants. The route calls `compose_entry` and then
`service.post_operational_record`.

**Wiring:**
- `main.create_app(..., operational_entry_principal: Principal = no_service_principal)` passes it to
  `build_work_router(entry_principal=...)`.
- `host/lab_app.py` `build_app`: when `os.environ.get("ASSETOPS_OPERATIONAL_ENTRY") == "on"`, pass
  `operational_entry_principal=lambda request, site_code: "service:operator-entry"`.
  - Any other non-empty value refuses startup with `ConfigurationError("ASSETOPS_OPERATIONAL_ENTRY must be 'on' or
    unset")`.
- `tools/demo_combined.py` serve env (the CH5c-R6 one environment of the serve and tick children) sets
  `ASSETOPS_OPERATIONAL_ENTRY=on`.

**Audit trail.** This needs no new table. Each saved row carries:
- the REC public code;
- the actor kind and id, and the server-derived `authorization_basis` (`SERVICE_GRANT_PREFIX + principal`);
- the attestation;
- `payload_sha256` over the canonical body;
- the idempotency key;
- `recorded_at`, the DB command time;
- the correction lineage.

It is the existing `operational_record` row, written append-only through the existing service.

**The "subsequent backend logic".**
1. A saved `TANK_DIP` or `FUEL_DELIVERY` is a tank record. The fuel balance already reads it through
   `work.composition.build_fuel_records_reader` (K2).
2. With G2, the next tick finds its night in the base or record set (§2.4) and re-assesses it. The night appends a
   revision only if the digest changes.
3. The raise then opens, revises or withdraws the unexplained-fuel Finding (§9j.4 table, `findings_service.py:31-47`).
4. The same tick's `chain_threads` and `chain_snapshots` update the thread and the stored pages.

A delivery first written more than 30 min after its night closed carries `DELIVERY_RECORDED_LATE` (K3 §9d.3). That is
already honest product behaviour. `MANUAL_READING` entries are stored and listed, but no check reads them yet; the copy
in §3.3 says so.

### 3.3 The entry form (G3b, `frontend/src/work/OperationalRecords.tsx`)

**Layout.** The mock's order and panel stay (`index.html:987`). Inside "Record a manual reading", in order:
1. row 1: Site, Reading;
2. row 2: Value, Taken at;
3. the Ticket reference row, only for Fuel delivery;
4. the footer with the button.

The panel pair and "How records are used" are unchanged.

**Fields and literals:**

| Field | Control | Literal / rule |
|---|---|---|
| Site | `<select>`, enabled | options from `manualReadingSites(body)` (existing, R362). The first Site is pre-selected. With none: "No Site selected" and the button disabled. |
| Reading | `<select>` | "Fuel tank dip" (TANK_DIP), **"Fuel delivery" (FUEL_DELIVERY)**, "Stock in chamber" (STOCK_IN_CHAMBER), "Meter reading" (METER_READING) |
| Value | `<input inputMode="decimal">` plus a unit suffix L / L / kg / kWh | placeholders: "e.g. 192 L", "e.g. 300 L", "e.g. 40 kg", "e.g. 1520 kWh" |
| Taken at | `<input type="datetime-local" step="60">` | label "Taken at (Site local time)" |
| Ticket reference | `<input>`, Fuel delivery only | label "Ticket reference", placeholder "e.g. KIS-DT-0002" |
| Button | "Submit for review" (mock label) | disabled while a save is in flight; the label stays |

**Client validation** (shown under the field; nothing is sent):
- "Choose a Site."
- "Enter a number of 0 or more, with at most 3 decimals."
- "Enter the delivered litres (more than 0)."
- "Enter the time the reading was taken."
- "Enter the delivery ticket reference."

**Submit:**
- `POST` through a new `GlobalWorkClient.submitOperationalEntry(siteCode, body)` (`globalWorkClient.ts`, the same base
  path and fetch helper as the reads).
- The idempotency key is `"oprec-entry-" + crypto.randomUUID().replace(/-/g, "")`. It is made when the form first
  becomes valid. It is **kept** for a retry after a network error or a 5xx. It is **replaced** after a success, or after
  any field edit.

**Outcomes:**

| Outcome | Text (live region `role="status"`) | Then |
|---|---|---|
| 201 / 200 | "Saved as {displayCode(code)}. It is listed above as Submitted." For a fuel entry, a second line: "If this Site's tank level is measured, the night it falls in is checked again at the next background refresh." | the list re-reads (the page's existing refresh); the form clears Value, Ticket and Taken at |
| 403 `WORK_WRITE_FORBIDDEN` | "Saving records is not switched on for this installation." | form kept |
| 422 `OPREC_ENTRY_NO_TANK` | "This Site has no single fuel tank to record against." | form kept |
| 422 `WORK_OCCURRED_AT_FUTURE` | "The time taken is in the future." | form kept |
| 422 `WORK_OCCURRED_AT_TOO_OLD` | "The time taken is more than 30 days ago." | form kept |
| `WORK_EVENT_DUPLICATE_KEY` | "This entry was already saved with different values. Reload the page and enter it again." | form kept |
| other 4xx | "Check the values and try again." | form kept |
| 5xx, network | "The record could not be confirmed. Try again; it will not be saved twice." | key kept |

**Other UI changes:**
- **Panel description** (replaces `MANUAL_READING_DESCRIPTION`): "Saved records are listed above as Submitted.".
- **`MANUAL_READING_REASON` and the `UnavailableInline` button wrapper are removed.**
- **"How records are used" second paragraph**, an addition: "Fuel tank dips and fuel deliveries are read by the nightly
  fuel check. Stock and meter readings are stored and listed; no check reads them yet."
- **By column (Rev 1):** when `actor_id === "service:operator-entry"`, show **"Entered by site admin"**. Other ids are
  unchanged.

**MOCK DEVIATIONS** (labelled in code and in the register):
- **MD-OWN-G3-1:** the "Fuel delivery" option and its Ticket reference row are additions. The owner asked that fuel
  deliveries be entered.
- **MD-OWN-G3-2:** "Taken at" is a native date-time input with a "(Site local time)" label. The mock has a text field
  showing "6 Oct 2026 · 16:00 EAT".
- **MD-OWN-G3-3:** the result line under the footer, and the replaced description line. The mock's "Fills REC-307 when
  submitted" is still not rendered (D1/R12 stands).
- **MD-OWN-G3-4:** the "Entered by site admin" By label (Rev 1), and the added "How records are used" sentence.
- The existing D1 "inert form" deviation (R12) is **closed**.

### 3.4 Files

- **G3a:**
  - `backend/assetops_backend/work_api.py`
  - `backend/assetops_backend/work/operational_entry.py` (new)
  - `backend/assetops_backend/work/model.py` (codes)
  - `backend/assetops_backend/main.py`
  - `host/lab_app.py`
  - `tools/demo_combined.py` (serve env only)
  - tests
- **G3b:**
  - `frontend/src/work/OperationalRecords.tsx`
  - `frontend/src/work/globalWorkClient.ts`
  - `frontend/src/work/globalWork.css` (form states only)
  - tests
  - `.agent/mock-departure-register.md`

### 3.5 Tests

**G3a units: `backend/tests/test_own_g3_operational_entry.py`** (`compose_entry`, and the route with a fake service and
`TestClient`):
- each entry type's exact kind, unit, body, asset and digest. The digest is checked against `hashlib.sha256` of the
  literal.
- Dar es Salaam 06:00 local → 03:00Z.
- Each invalid shape → `OPREC_ENTRY_INVALID`.
- A delivery without a ticket → `OPREC_ENTRY_TICKET_REQUIRED`.
- No tank → `OPREC_ENTRY_NO_TANK`.
- Refusal order:
  - no principal → 403 `WORK_WRITE_FORBIDDEN`, even with an invalid body;
  - a principal with no store → 503 before shape.
- The browser cannot send an actor: an `actor` key → 422.
- `ASSETOPS_OPERATIONAL_ENTRY=yes` refuses startup.

**G3a Postgres: `backend/tests/test_own_g3_operational_entry_postgres.py`** (`create_app` with the entry principal,
fixture Site with one tank):
- 201, then an identical retry → 200 with the same body;
- the same key with another value → `WORK_EVENT_DUPLICATE_KEY` and its status;
- the stored row: actor id, attestation, `authorization_basis`, REC code, `payload_sha256`, `recorded_at` = DB time;
- a 31-days-back and a 10-minutes-ahead entry are refused, with zero rows;
- an app with no principal → 403, with zero rows;
- a saved dip is returned by `build_fuel_records_reader` for its night: this proves it feeds the fuel balance;
- `MANUAL_READING` rows are stored with their unit and have no `asset_id`.

**G3b vitest: additions to the Operational records tests:**
- field order and labels;
- the four options;
- the ticket row appears only for Fuel delivery;
- each client validation message;
- the exact request body;
- the button is disabled in flight;
- every outcome row's text;
- the list re-reads after success;
- the key is kept after a network error and replaced after an edit or a success;
- "Entered by site admin" (Rev 1);
- no `UnavailableInline` remains on the form;
- the form uses no forbidden fuel words.

**G3b captures** (one heavy job, fixture serve): `oprecords` at 1440 and 390, idle form and the Fuel delivery state.
They are compared with the mock; each difference must be one of MD-OWN-G3-1..4.

### 3.6 Size, risk, review

- **G3a 1.0 unit** (build 0.7, review 0.3). **Risk: medium.** It is a new write path, gated by server configuration.
  The identity is a labelled service, not a user.
- **G3b 1.25 units** (build 0.85, review and captures 0.4). **Risk: low to medium** (UI states).
- **Review:** a fresh Opus reviewer per slice. G3b's review includes the capture pair against the mock. High or Medium
  findings block.

---

## 4. G1 — the owner's `add-dates` tool (demo tool) — Rev 1, replaces the earlier Kisiwa `add-day` card

### 4.1 What it is, in plain words

A real Site gets its data from its gateway, all day, without anyone doing anything. The demo Sites have a simulated
gateway that runs only when the demo tool tells it to. `add-dates` is that instruction: the owner names the Sites and
the dates (or just runs it with no options to catch everything up to yesterday). The tool generates each missing day's
readings, sends them through the real gateway path, posts Kisiwa's tank dips and deliveries through the real entry
route (G3a), and then lets the product's normal background refresh check them (G2 for diesel nights). Nothing in the
product knows the tool exists.

### 4.2 Command

```
python tools/demo_combined.py --db <db> --work <work> add-dates
    [--site all | KOBO-001,COLD-LAB-001,EV-LAB-001,KISIWA-001]     default: all
    [--from YYYY-MM-DD]     default per Site: the day after that Site's last day (story or added)
    [--to YYYY-MM-DD | yesterday]     default: yesterday
    [--kind <kind>]     only with one Site and one date; default per Site below
    [--dry-run]     print the plan and the refusals, write nothing
    [--no-check]     skip the closing finish check (not for demo days)
```

- Dates are **calendar dates in the Site's own timezone**. The tool converts each to the story offset (`date − S`)
  internally; the owner never types S-offsets. `yesterday` is the day before DB now (`clock_timestamp()`) in each
  Site's timezone.
- The existing single-day `add-day` stays (variety kinds, `--as`, `--assess-now`); `add-dates` calls the same planning
  and children per date. `add-day`'s `--site` choices gain `KISIWA-001`, and its "no Kisiwa day kinds" comment goes.

### 4.3 Whole-command refusals (checked first; nothing is written; `StoryDaysError` codes)

| Code | When | Message |
|---|---|---|
| `DATE_NOT_PAST` | `--to` is today or later in any selected Site's timezone | "Data can be added only up to yesterday ({date})." |
| `STORY_DAY` | `--from` or `--to` falls on or before a selected Site's last **story** day | "{site} {date} is part of the prepared story and cannot be changed." |
| `GAP_NOT_ALLOWED` | Kisiwa only: `--from` is later than the day after its last night (each night's tank level starts from the night before) | "Kisiwa nights must follow on from {last}; start at {last+1}." |
| `FUEL_STAGE_MISSING` | Kisiwa selected and `"fuel_night" not in STAGE_LIMIT_FIELDS` | "This build's code has no automatic diesel-night check (G2)." |
| `ENTRY_DISABLED` | Kisiwa selected and a probe `POST` with an invalid body answers 403 `WORK_WRITE_FORBIDDEN` | "Saving records is not switched on for this build (ASSETOPS_OPERATIONAL_ENTRY)." |
| `BUSY` | `<work>/.busy` held | the existing "another prepare/add-day holds …" line |
| `FROM_AFTER_TO` | `--from` > `--to` | "--from is after --to." |
| `KIND_NEEDS_ONE_DATE` | `--kind` with several Sites or dates | "--kind needs exactly one Site and one date." |

For Kobo, Cold and EV a later `--from` than the default is allowed: the skipped days stay empty and the screens show
them as missing, which is what a real Site with a gateway outage shows. The tool prints "left empty: {dates}".

### 4.4 Per-date behaviour (date-major: every selected Site advances one date, then one tick, then the next date)

| Site | Default kind | Per-date rule |
|---|---|---|
| KOBO-001 | `normal` | `sd.plan_add_runs` as today (including `FULL_DAY_AFTER_TRIAL`, which `normal` passes) |
| COLD-LAB-001 | `normal` | `sd.plan_add_runs` as today |
| EV-LAB-001 | `normal` | **Tuesdays only.** The simulated charger model admits one weekly TUESDAY 08:00–16:00 window (`host/ev_publication.py:331-336`, `tools/demo_story_days.py` `SITE_WEEKDAY`). Other dates print "EV-LAB-001 {date}: no charging session (the simulated charger runs on Tuesdays)" and are not refusals. |
| KISIWA-001 | `normal`, or `delivery` when the start tank level is below 250 L | the Kisiwa child in §4.5 |

- A date that already holds that Site's data from an earlier `add-dates` (`DUPLICATE_DAY` or `DAY_HAS_EVIDENCE`) is
  **skipped** with "already present". So running the command twice is safe.
- After each date: one `Demo.tick()` (the product's own scheduled tick; with G2 it runs `fuel_night`), then the next
  date.
- After the last date: `finish check` (unless `--no-check`), then a summary:

```
{"added": [{"site", "date", "kind", "records": [REC codes], "checked": "<tick result / Kisiwa window state>"}],
 "skipped": [{"site", "date", "reason"}], "left_empty": [...], "finish_check": "PASS" | "FAIL <rows>"}
```

  and one plain line per Site, e.g. "KISIWA-001: added 13 Nov (normal), 14 Nov (delivery, ticket KIS-DT-20261114);
  both nights checked: within margin." A failed `finish check` prints "This build no longer passes its checks; prepare a
  fresh one before a demo." (R1.5: a failed check retires the build).

### 4.5 The Kisiwa child (`tools/demo_combined_kisiwa.py add-day <url> <work> <json>`)

**Day kinds** (unchanged from the first card):

| Kind | Night d carries | Records |
|---|---|---|
| `normal` | one v7 run `[d 12:00Z, d+1 12:00Z)` from the previous run's end state, with the story's no-removal behaviour | two tank dips, at d 18:00 local and d+1 06:00 local |
| `delivery` | as `normal`, plus a 300 L delivery at d+1 10:00 local (effect-bearing, in the run's log) | the two dips plus one FUEL_DELIVERY, 300 L, ticket `KIS-DT-{yyyymmdd of d}` |

No kind creates unexplained fuel, an Action or a Finding (those are prepare-only, as for Kobo, Cold and EV).

**Per-night refusals** (stop the command at that date; earlier dates stay; codes as before): `UNKNOWN_KIND`,
`NOT_NEXT_NIGHT`, `DUPLICATE_DAY` (story nights), `DAY_NOT_IN_PAST` (run end > DB now − 5 min), `FUEL_LOW_USE_DELIVERY`
(explicit `--kind normal` below 250 L), `DELIVERY_TANK_FULL` (start + 300 > 950 L), `RUN_NOT_READY`,
`ADD_NIGHT_UNEXPECTED`.

**Steps** (the product's real paths; unchanged from the first card except where marked):
1. **Start state.** The last `DONE` or `PUBLISHED` entry of `<work>/kisiwa-days.json` `end_state`, else `kisiwa.json`
   `runs[-1].physics` (`soc`, `fuel` as exact fractions).
2. **Log.** Write `<work>/operational-actions/kisiwa-001-story-{S yyyymmdd}-add-{d yyyymmdd}-v1.yaml` (header shape of
   the shipped log, this day's actions only; ids `kis-add-{yyyymmdd}-dip-1800`, `kis-add-{yyyymmdd}-dip-0600`,
   `kis-add-{yyyymmdd}-delivery`). Read back through `YamlOperationalActionLog`; keep its sha.
3. **Run.** `story_registered(...)`, `reg.draft(nights.day_document(soc, fuel), start, end, "v7", {"log_id": ...,
   "log_version": 1})`; must be `READY` with a registered basis, else `RUN_NOT_READY`. `run_to_end` gives the trajectory,
   the end state and each dip's litres (offsets 180 and 900 min, `probe._round_litre`; delivery at 1140 min).
4. **Readings.** `rp._publish_and_accept(work / "kisiwa-replay" / f"add-{yyyymmdd}", run, f"epoch-add-{yyyymmdd}",
   db_now)`: the gateway path, Batch V2, received at DB now. **Rev 1:** then append the night to `kisiwa-days.json` with
   `status: "PUBLISHED"` and its `end_state`, so a crash after this point can resume.
5. **Records.** Post through the G3a entry route, `POST /api/sites/KISIWA-001/work/operational-entries`, via
   `finish.app_client(url, work)` with `ASSETOPS_OPERATIONAL_ENTRY=on`. Idempotency key `oprec-entry-` + the first 32 hex
   of `sha256("kisiwa-add|{S}|{d}|{action_id}")`; a re-post answers 200. They list as "Entered by site admin".
6. **Wait for the check.** Poll DB now every 30 s until `now >= night end + 30 min` and `now >= last reading decided_at
   + 5 min` (cap 8 min); the date-major tick (§4.4) then checks it. A running `serve` may check it first; idempotent.
7. **Verify.** The night's latest window: revision ≥ 1, state `WITHIN_MARGIN`, no fuel Finding for that night, the
   tick's `fuel_night` code `OK`. Otherwise stop with `ADD_NIGHT_UNEXPECTED` and the window line (append-only: nothing
   rolled back).
8. **Save.** Set the entry to `status: "DONE"` with `{night_date, kind, run_id, start, end, received_at, end_state, log:
   {id, sha256}, records: [{code, kind, quantity, taken_at_local}], window: {revision, state}}`.
9. **Resume (Rev 1).** On a re-run, a `PUBLISHED` entry for the next night resumes at step 5 (keys are deterministic;
   readings are not re-sent). Any other partial state stops with `PARTIAL_NIGHT` and goes to the Architect.

**`links`** prints each added night's dated Kisiwa link and the **live-dip line**: the newest added night, 06:00 local,
with the dip litres from step 3, for the on-screen beat (owner Q2 yes).

**Guards for the story verdicts:** story nights cannot be touched (`STORY_DAY`, `DUPLICATE_DAY`); no kind can raise a
Finding; every command ends with `finish check` (KIS rows read story nights only; KIS-11 pins revision 1 on them). If
the rehearsal shows KIS-2 or KIS-6 failing **only** because of added-night dispatch content, the fix is pre-authorised:
bound that row's query to the story calendar's run range `[run1_start, runs[-1].end)` from `story.json`. Any other
failure stops and goes to the Architect.

### 4.6 Files

- `tools/demo_combined.py` (`add-dates` parser, range planner, date-major loop, summary; `add-day` choices and Kisiwa
  routing; `links`)
- `tools/demo_story_days.py` (only a pure `date → offset` helper and the per-Site `yesterday`, if not already there)
- `tools/demo_combined_kisiwa.py` (`add-day` child, plan, refusals, resume)
- `tools/demo_combined_finish.py` (only the pre-authorised bound, if needed)
- `backend/tests/test_own_g1_add_dates.py` (no DB)

### 4.7 Tests

**No DB:**
- range planning: defaults per Site; calendar date ↔ offset both ways; `yesterday` per Site timezone across a UTC
  midnight (Dar es Salaam at 22:00Z is the next local day); date-major order;
- every whole-command refusal at its edge (`--to` = yesterday passes, today refuses; `--from` = last story day refuses,
  +1 passes; Kisiwa gap of one day refuses);
- EV: a Tuesday is planned, a Wednesday prints the no-session line and is not a refusal;
- already-present dates are skipped, so a second identical run plans nothing;
- Kisiwa kind auto-choice at 249.999 L vs 250 L; `DELIVERY_TANK_FULL` at 650 L vs 651 L; run end = now − 5 min vs
  − 4 min 59 s;
- start state chains `DONE`/`PUBLISHED` entries over `kisiwa.json`; resume from `PUBLISHED` posts records only;
- action ids, instants, log text and sha stability, idempotency keys;
- `FUEL_STAGE_MISSING`; `--dry-run` writes nothing (no file, no call).

**Rehearsal** (one heavy job, about 1.5 h, Wed 11): clone the K9/K10 four-Site build,
`CREATE DATABASE assetops_k9_audit_g1 TEMPLATE assetops_k9_audit_r3u` (its serve stopped), copy
`AssetOpsV1-k10\var\demo3_r3u` to `var/g1_audit`, and run the product's own `evidence_migration run` and
`performance_migration run` on the clone (coordinator lesson 3). Then:
1. `add-dates --site KOBO-001,KISIWA-001,EV-LAB-001 --to <the clone's last Kisiwa night + 2>` (covers a normal night, the
   auto-delivery choice if the tank is low, and EV's Tuesday rule);
2. run the same command again: everything "already present";
3. `--to` today: `DATE_NOT_PAST`, nothing written;
4. `finish check` all green (KIS-11 included) and `chain_coherence.py` (EX-2 = 0);
5. drop the clone.

### 4.8 Size, risk, review

- **Size 1.75 units:** build 1.1 (Kisiwa child 0.6, the range command over four Sites 0.5), rehearsal 0.25 (machine),
  review and fix 0.4.
- **Risk: medium.** Physics continuity, a low tank, a crash mid-night, and a race with the serve loop. The tool guards
  each (start-state chain, auto-delivery, `PUBLISHED` resume, G2 idempotency).
- **Review:** a fresh Opus reviewer reads the code and the rehearsal output. High or Medium findings block.

---

## 5. Sequencing ruling — SUPERSEDED by Revision 1 (R1.3); kept as history

> Rev 1: the timing, the nightly add-day rows, the two-build option and the cut order below no longer apply. The
> plan is R1.3; one build is kept current by the owner with `add-dates` (§4).

### 5.1 Before 10 Nov: none

- **Monday is full.** The 10-Nov plan has no slack (Part D.2: "Yes, with no slack"). The code freeze E1 is Mon 08:00.
- **G2 is the main reason.** It changes the scheduler, so E2 and E3 would have to be re-run.
- **G3 and G1 do not fit either.** Even the smallest item (G3a, 1.0 unit, about 2.5 h, plus check-all) would have to be
  built and reviewed before 08:00 Monday. It would also change the served app inside the freeze.
- **Nothing changes in E2–E6 for 10 Nov.** DS-1a for 10 Nov must still **not** say or imply that diesel nights are
  checked automatically, and must not show anyone typing a record on screen.

### 5.2 After 10 Nov, before the 16–20 Nov demos (two lanes, one heavy job at a time)

| When | Lane A | Lane B | Heavy job (one at a time) |
|---|---|---|---|
| Tue 10, after the session | G2 pre-flight (Opus, read-only) | G3a pre-flight (Opus, read-only) | — |
| Tue 10, evening | One batched question list to the Architect; rulings folded into this sheet's cards | | — |
| Wed 11 | G2-u1 (am), G2-u2 (pm) | G3a build (am); review (early pm); fix; merge | 08:00 `finish check` on the 10-Nov build; ~12:30 G3a Postgres; ~15:30 G3a merge check-all; ~17:00 G2 Postgres |
| Thu 12 | G2 review (am, reruns Postgres); Sonnet fix; merge; then G1 pre-flight and build (unit tests only) | E6 non-High fix round (am, from the 10-Nov walkthrough, ≤ 1.5 units); G3b build (pm) | 08:00 finish check; ~10:00 G2 review Postgres; ~13:30 G2 merge check-all; ~17:30 G3b captures |
| Fri 13 | G1 build finish (am); G1 rehearsal (§4.3, ~13:30–14:30); review; merge | G3b review (am); fix; merge; DS-1a/b text revisions drafted (no serve) | 08:00 finish check; ~12:00 G3b merge check-all; ~13:30 G1 rehearsal; ~18:00 G1 merge check-all |
| Sat 14 | **E2-lite**: clock check (Part F.3 step 0); `-Tier fast`, then `-Tier slow` on the two schedule files plus `test_own_g2_fuel_night_tick_postgres.py` if slow-marked; vitest; check-all (about 1.5–2 h); reserved 0.5-unit fix round | | the suites, in sequence |
| Sun 15 | **E3** into `assetops_polish_client2_test` (S = 13 Nov; the date rule passes), about 2.0–2.4 h; then **E4** (live ticks; KIS-11; `fuel_night` OK in the tick report), then **E5** (adds `oprecords` 1440/390); DS-1a refresh (Sonnet) | | E3, E4, E5 in sequence |
| Sun 15, evening | add-day: Kobo S+1 (14 Nov) and **Kisiwa night 14 Nov**; tick; `finish check` | | yes |
| Mon 16–Fri 20 | Each evening: Kobo add-day; Kisiwa add-day (`normal`, or `delivery` when the tool says the tank is low); Cold/EV on their weekly day; tick; `finish check`. Each demo morning, ≥ 3 h before: E4-lite. | | one at a time |

- **Capacity.**
  - Lane A carries 3.5 units over Wed–Fri, against about 9 available.
  - Lane B carries about 3.75 units (G3a, E6 fixes, G3b).
  - The slack covers one extra fix round per item.
  - The real constraint is the heavy-job queue, so the times above are placed so that no two heavy jobs overlap.
- **Dependencies:**
  - G1 needs G2 merged (for `FUEL_STAGE_MISSING`) and G3a merged (records go through the entry route).
  - G3b needs G3a.
  - G2 and G3a are independent. Their only shared file is `tools/demo_combined.py`, in different functions, and they
    merge one after the other.
- **If the 10-Nov session moves to Wed 11, or the E6 fix round passes 1.5 units:** everything shifts one day. **G1 is
  then cut first** (it is built last, and Kisiwa stays judged on its story week, which is honest). G2 and G3 still land
  by Fri.

### 5.3 What changes in E2–E5 and in the scripts, for the 15-Nov build

- **E2-lite (Sat 14):**
  - the new no-DB tests run in the fast tier;
  - the G2 Postgres file runs in the fast tier, unless it is slow-marked;
  - the G3a Postgres file runs in the fast tier.
- **E3:** the command does not change. The prepare's ticks now run `fuel_night` (about +2–5 min). The in-prepare
  self-check now includes KIS-11.
- **E4:** check that each tick report has `fuel_night` `OK` for KISIWA-001 and `eligible: false` for COLD and EV. KIS-11
  passes. The serve env has `ASSETOPS_OPERATIONAL_ENTRY=on`. No live write is made in E4.
- **E5:** add `oprecords` at 1440 and 390 (the idle form). The after-submit state is captured only in G3b's fixture
  captures, never on the demo DB.
- **DS-1a (client) refresh on Sun 15.** It **may now say**: "Each night's fuel is checked automatically once that
  night's tank readings have come in; the background refresh in this demo runs every two minutes." It **may show**
  saving a tank dip from Operational records, only if the owner says yes (Q2), and then only on the newest added night,
  with the `links` live-dip value. Still forbidden:
  - theft words;
  - a combined money total;
  - "real time";
  - a production cadence claim;
  - saying who typed a record, because the record shows "Entered on screen".
- **DS-1b (technical):** a short section on `fuel_night` (the due rule, idempotency, DB time, the failure marker), the
  entry route and its server identity, and Kisiwa `add-day`.
- **The daily morning check** stays E4-lite: serve with ticks, one completed tick, `finish check`, prewarm. Plus the
  three K8c-r probes (Part E.3 step 4).

### 5.4 Rolling forward (from the colleague's recommendation, now with Kisiwa)

- One build, prepared Sun 15 (S = 13 Nov), rolled forward each evening.
- **G1 means Kisiwa rolls forward with the others.** "This week" views show checked diesel nights after S, instead of
  "0 of 7".
- A failed `finish check` retires the build. The fallback is a fresh E3, about 2.5 h, so the check runs at least 3 h
  before a demo.
- The 10-Nov build is kept as the fallback until the 15-Nov build passes E4.

---

## 6. Owner questions — ANSWERED 2026-11-08 (Revision 1, R1.1); kept as history

> Rev 1 answers: 1 → one build, owner adds dates with the tool; 2 → yes; 3 → "Entered by site admin"; 4 → no cuts,
> time relaxed; 5 → illustrative pictures taken once; 6 → Portfolio first; 7 → §7.

1. **16–20 Nov: one build rolled forward (recommended, and what G1 is for), or two builds (Part D.3)?** This was not
   answered yet. With two builds, G1 is still useful but not needed.
2. **May the presenter save a tank dip on screen during client demos?** It writes into the demo build. Recommended:
   yes, on the newest added Kisiwa night only, with the value `links` prints. That shows "record → automatic re-check"
   without changing any story result. If no, the entry form is shown but not used.
3. **For information (the Architect has decided; say if you disagree):** records saved from the screen are signed by a
   server-configured entry service, shown as "Entered on screen". Who typed them is not recorded until sign-in exists.
   - Option, +0.25 unit: add an unverified "Entered by" name field. That is a mock deviation, and it would be labelled
     "not verified".
4. **Cut order if time runs short:** G1 first (recommended), then G3b. G2 is never cut once DS-1a says "checked
   automatically": if G2 is not in the 15-Nov build, the script keeps today's wording.
5. **Still open from the earlier answer:** script pictures — exact pictures from each demo build, or labelled
   illustrative pictures taken once.

---

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
