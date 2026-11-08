# Build sheet OWN-GAPS (2026-11-08): Kisiwa add-day, automatic diesel-night check, saving operational records

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only on code, main `2cf460aa5` (includes R-1 merge
`733eaf75c`). No Postgres or heavy run was made for this sheet.

Owner, verbatim (`.agent/owner-decisions-ingest-gaps-2026-11-08.md`): "here is my response to the architect 1- update
the demo tool to address the gap mentioned 2- Diesel night should be checked automatically 3-operational records should
be saved , the entry form should be updated as well as the subsequent backend logic"

Background: `.agent/architect-answers-owner-ingest-captures-2026-11-08.md` (T1, T3) and
`.agent/architect-combined-pass-2026-11-08.md` Parts C–F. Fuel rulings carried from `.agent/build-sheet-DIESEL-1.md`:
the wording is "unexplained fuel", never theft; fuel money is never summed with any other amount.

| Item | What | Size (units, review included) | Lane |
|---|---|---|---|
| **G2** | Automatic diesel-night check: a `fuel_night` stage in the schedule tick | **2.25** (two build units) | A |
| **G3a** | Saving operational records: backend entry route and server identity | **1.0** | B |
| **G3b** | Saving operational records: the live entry form | **1.25** | B |
| **G1** | Kisiwa `add-day` in the demo tool, fed through the product's real paths | **1.25** | A, after G2 and G3a |
| | **Total** | **5.75** (about 2 lane-days) | |

**Ruling on timing (§5): none of G1–G3 goes into the 10-Nov build.** All three are built Wed 11 to Fri 13 Nov in two
lanes. They are proven on Sat 14 (E2-lite) and go into the Sun 15 Nov build for the 16–20 Nov demos. No migration is
needed: the head stays `0058_fuel_watermark_inputs`, and `0059` stays unused.

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
- **What it does not prove.** It does not say which person typed the record. The list shows "Entered on screen" in the
  By column. A signed-in user identity is still an after-the-demo item.

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
  "service=operator-entry;job=screen-entry;rule=oprec-entry/1"}`.
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
- **By column:** when `actor_id === "service:operator-entry"`, show "Entered on screen". Other ids are unchanged.

**MOCK DEVIATIONS** (labelled in code and in the register):
- **MD-OWN-G3-1:** the "Fuel delivery" option and its Ticket reference row are additions. The owner asked that fuel
  deliveries be entered.
- **MD-OWN-G3-2:** "Taken at" is a native date-time input with a "(Site local time)" label. The mock has a text field
  showing "6 Oct 2026 · 16:00 EAT".
- **MD-OWN-G3-3:** the result line under the footer, and the replaced description line. The mock's "Fills REC-307 when
  submitted" is still not rendered (D1/R12 stands).
- **MD-OWN-G3-4:** the "Entered on screen" By label, and the added "How records are used" sentence.
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
- "Entered on screen";
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

## 4. G1 — Kisiwa `add-day` in the demo tool

### 4.1 Behaviour

```
python tools/demo_combined.py --db <db> --work <work> add-day --site KISIWA-001 --kind normal|delivery [--day S+Nd]
```

**CLI.** `tools/demo_combined.py:919` `choices` gains `KISIWA-001`, and its "no Kisiwa day kinds" comment goes.
`Demo.add_day` routes KISIWA-001 to a new child command, `tools/demo_combined_kisiwa.py add-day <url> <work> <json>`.
That child reuses the existing busy lock and `say` lines. `days.json` is not used for Kisiwa: Kisiwa keeps
`<work>/kisiwa-days.json`.

**Day kinds:**

| Kind | Night d carries | Records |
|---|---|---|
| `normal` | one v7 run `[d 12:00Z, d+1 12:00Z)` from the previous run's end state, with the story's no-removal behaviour | two tank dips, at d 18:00 local and d+1 06:00 local (the after-Action dip log, as in runs 6–10) |
| `delivery` | as `normal`, plus a 300 L delivery at d+1 10:00 local (effect-bearing, in the run's log) | the two dips plus one FUEL_DELIVERY, 300 L, ticket `KIS-DT-{yyyymmdd of d}` |

No add-day kind creates unexplained fuel, an Action or a Finding (those are prepare-only, as for Kobo, Cold and EV).

**Default day:** the night after the last Kisiwa night: the story's night S, or the last added night. Kisiwa nights must
be consecutive, because each start state chains from the one before.

**Refusals** (nothing written; `StoryDaysError` codes):
- `UNKNOWN_KIND`;
- `NOT_NEXT_NIGHT` (`--day` is not last + 1);
- `DUPLICATE_DAY` (any night ≤ the last one, story nights included);
- `DAY_NOT_IN_PAST` (run end > DB now − 5 min);
- `FUEL_LOW_USE_DELIVERY` (`normal` with a start tank level < 250 L);
- `DELIVERY_TANK_FULL` (start + 300 > 950 L; the tank is 1000 L, `kisiwa-001.yaml:108-112`);
- `FUEL_STAGE_MISSING` (`"fuel_night" not in STAGE_LIMIT_FIELDS` in the tree: G2 is not in this build's code);
- `ENTRY_DISABLED` (the entry route answered 403).

**Steps, in order (the product's real paths):**
1. **Start state.** The last entry of `kisiwa-days.json` `end_state`, else `kisiwa.json` `runs[-1].physics` (`soc`,
   `fuel` as exact fractions).
2. **Log.** Write `<work>/operational-actions/kisiwa-001-story-{S yyyymmdd}-add-{d yyyymmdd}-v1.yaml`.
   - It has the header shape of the shipped log, with only this day's actions.
   - Action ids: `kis-add-{yyyymmdd}-dip-1800`, `kis-add-{yyyymmdd}-dip-0600`, and `kis-add-{yyyymmdd}-delivery`
     (`volume_l: 300`, `ticket.reference`).
   - Read it back through `YamlOperationalActionLog`. Its sha is kept.
3. **Run.** Use `story_registered(...)`, then `reg.draft(nights.day_document(soc, fuel), start, end, "v7", {"log_id":
   ..., "log_version": 1})`.
   - It must be `READY` with a registered basis, else `RUN_NOT_READY`.
   - Then `run_to_end` gives the trajectory, the end state, and each dip's litres at its offset. The offsets are
     180 min (d 18:00 local = 15:00Z) and 900 min (d+1 06:00 local = 03:00Z), multiples of 5, and use
     `probe._round_litre`. The delivery sits at offset 1140 min (d+1 10:00 local), as in the story's run 2.
4. **Readings.** Use `rp._publish_and_accept(work / "kisiwa-replay" / f"add-{yyyymmdd}", run,
   f"epoch-add-{yyyymmdd}", db_now)`. This is the gateway path, Batch V2, received at DB now.
5. **Records.** Post through the **G3 entry route**, `POST /api/sites/KISIWA-001/work/operational-entries`. Use
   `finish.app_client(url, work)` with `ASSETOPS_OPERATIONAL_ENTRY=on` in its environment.
   - The idempotency key is `oprec-entry-` + the first 32 hex of `sha256("kisiwa-add|{S}|{d}|{action_id}")`. It is
     deterministic, so a re-run after a crash answers 200 and does not duplicate.
6. **Wait for the check.** Poll DB now every 30 s until `now >= night end + 30 min` and `now >= last reading decided_at
   + 5 min`, with a cap of 8 min. Then run one `Demo.tick()`. If `serve` is running, its loop may check the night first;
   that is idempotent.
7. **Verify.** Read the night's latest window and its fuel Finding status.
   - Expected: revision ≥ 1, state `WITHIN_MARGIN`, no fuel Finding for that night, and the tick's `fuel_night` code
     `OK`.
   - Otherwise stop with `ADD_NIGHT_UNEXPECTED` and the window line. Nothing is rolled back, because data is
     append-only. Under the rolling rule (§5.4) the build is then retired.
8. **Save.** Append to `kisiwa-days.json`: `{night_date, kind, run_id, start, end, received_at, end_state, log: {id,
   sha256}, records: [{code, kind, quantity, taken_at_local}], window: {revision, state}}`. Print `{"added": ...}`.
9. **Links.** `links` prints each added night's dated Kisiwa night link and a **live-dip line**: the newest added night,
   06:00 local, with the dip litres from step 3. That is a value equal to the sensor's, which the presenter can type if
   the owner allows the on-screen beat (§6, Q2).

**Guards for the story verdicts:**
- story nights cannot be touched (`DUPLICATE_DAY`);
- no kind can raise a Finding;
- every add is followed by the operator's `finish check` (KIS rows read story nights only; KIS-11 pins revision 1 on
  them).

If the G1 rehearsal (§4.3) shows KIS-2 or KIS-6 failing **only** because of added-night dispatch content, the fix is
pre-authorised: bound that row's query to the story calendar's run range `[run1_start, runs[-1].end)` from
`story.json`. Any other failure stops and goes to the Architect.

### 4.2 Files

- `tools/demo_combined.py` (`add-day` choices and routing; `links`)
- `tools/demo_combined_kisiwa.py` (`add-day` child, plan and refusals)
- `tools/demo_combined_finish.py` (only the pre-authorised bound, if needed)
- `backend/tests/test_own_g1_kisiwa_add_day.py` (no DB)

### 4.3 Tests

**No DB:**
- planning, for both kinds: run interval, action ids and instants, log text and sha stability, the idempotency keys;
- every refusal code, at its edge: 249.999 L vs 250 L; 650 L + 300 vs 651 L + 300; run end = now − 5 min vs − 4 min
  59 s;
- the start state chains from `kisiwa-days.json` over `kisiwa.json`;
- `FUEL_STAGE_MISSING` when the tick lacks `fuel_night`.

**Rehearsal (one heavy job, about 1 h, Fri 13 Nov):**
1. Clone the 10-Nov build: `CREATE DATABASE assetops_polish_g1rehearsal_test TEMPLATE assetops_polish_client_test`,
   with its serve stopped. Copy the work folder to `var/polish_g1rehearsal`.
2. Add Kisiwa nights 8, 9, 10 and 11 Nov (S = 7 Nov). The tool decides whether a delivery is needed.
3. Run `finish check` (all rows green, KIS-11 included) and `chain_coherence.py` (EX-2 = 0).
4. Drop the clone afterwards.

### 4.4 Size, risk, review

- **Size 1.25 units:** build 0.75, rehearsal about 0.2 (machine), review 0.3.
- **Risk: medium.** Physics continuity, a low tank, and a race with the serve loop. The tool guards all three, and G2's
  idempotency covers the race.
- **Review:** a fresh Opus reviewer reads the rehearsal output. High or Medium findings block.

---

## 5. Sequencing ruling

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

## 6. Owner questions (decisions still needed)

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
