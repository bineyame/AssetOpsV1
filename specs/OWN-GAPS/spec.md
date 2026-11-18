# Build sheet OWN-GAPS (2026-11-08): Kisiwa add-day, automatic diesel-night check, saving operational records

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only on code, main `2cf460aa5` (includes R-1 merge
`733eaf75c`). No Postgres or heavy run was made for this sheet.

Owner, verbatim (`.agent/owner-decisions-ingest-gaps-2026-11-08.md`): "here is my response to the architect 1- update
the demo tool to address the gap mentioned 2- Diesel night should be checked automatically 3-operational records should
be saved , the entry form should be updated as well as the subsequent backend logic"

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
  - `lt::time <= '12:30'` → `lt::date - 1`;
  - otherwise no night.

  **Rev 1:** the two bounds are not typed as literals. They are computed from the rule's own constants:
  `rules.NIGHT_START − EDGE` (17:30) and `rules.NIGHT_END + EDGE` (12:30), passed to the SQL as bound parameters, so the
  fuel-balance-1 night window has one source. A unit test pins that changing `NIGHT_START` moves the bucket.

  This is a night's read range `[start − 30 min, end + 30 min]` (closed, D-R3.7) in local time. Two nights' ranges never overlap. The
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
- **P4.** (Rev 2: replaced by R2-G2 Q6; the delivery half below was backwards.) A dip posted after night N's revision 1, which conflicts with the sensor: the next tick appends revision 2
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
| 201 / 200 | (Rev 2, R2-G3b Q2) "Saved as {displayCode(public_code)}, status Submitted." For a fuel entry, a second line: "If this Site's tank level is measured, the night it falls in is checked again at the next background refresh." | the list re-reads (the page's existing refresh); the form clears Value, Ticket and Taken at |
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

## E2 fix-round scope (2026-11-09)

- Architect: Claude (assetops-architect), delegated by the owner. Binding checked: `.ai/ROLE_CONFIG.md`, Architect =
  Claude since 2026-10-27. Input: `.agent/E2-results.md` on `task/E2-endgame` (bda19fecf), main 9bbbb5626. This
  ruling is read-only. I read the code and the E2 junit (`AssetOpsV1-e2/var/test-results/OPS-03/20261109-115734-e74ec1`,
  `...-104402-6465c5`). I queried no DB and ran nothing.
- Scope rule (owner, 2026-11-05): demo-critical only. The owner's bar for this round: decide from how real Sites work
  and what AssetOps is for, with no corners cut on fundamentals. So every red test below ends in one of three ways.
  It is **fixed**, with a named cause. Or it is **bounded** by a check on the demo build that proves the same thing.
  Or it goes to the **backlog**, with the reason it is not on a presented beat.
- There are two rounds. **FR-A** runs now, and E3 waits for it. **FR-B** runs Wed 11 to Fri 13 Nov, before the
  Sat 14 Nov backend run (D.4). FR-A changes **no product code**: only tests, one frontend test fixture and the
  container copy list. So E3 builds the same code that E2 measured.

### E2.1 Rulings

**(1) The G2 clock read at `fuel_balance/adapters/postgres_fuel_balance_store.py:254` is legitimate. It goes on the
allow-list as a writer, with a call-site guard. (D-E2.1)**
- What it is: only `fuel_balance/scheduled.py:117` (`run_site`) calls `schedule_inputs`, and only the tick's
  `fuel_night` stage (`scheduling/stages.py:473-486`) calls `run_site`. No stored compose, board, summary or route
  calls it. Its `known_at` decides which nights are due. `transaction` (`:213-219`) then assesses each due night, and
  takes its own `known_at` from the same `SELECT clock_timestamp()`. That read is already allow-listed as a writer
  (`test_ch5c2_clock_guard.py`, DIESEL-K4b block).
- Fundamentals: on a real Site, "is last night closed, and have the tank readings been quiet for 5 minutes?" is a
  question about the moment the check runs. It must use the same clock as the assessment it gates. Otherwise a night
  can be picked as due and then refused as `WINDOW_OPEN`. Every other tick stage works the same way: `db_now`, the
  cold, EV and opportunity leases at DB time, and the Kisiwa prepare's night assessment (`fuel_balance/worker.py`,
  also DB time). The story clock and the request's `known_at` (the visibility cutoff) belong to **reads**. They limit
  what a page may show, and must never drive a writer. A tick that judged nights by a story date would assess nights
  that have not happened yet, or skip nights that have. `read_scope.read_instant` is for compose read captures, so it
  does not apply here. Tests keep their hook, `test_db_clock_override`. So diesel-night due-checks agree with the rest
  of the product. This is not a defect. The guard fired only because OWN-G2 u1 did not add its allow-list row.
- **Fix (test only), `backend/tests/test_ch5c2_clock_guard.py`:**
  (a) In `SQL_CLOCK_ALLOWLIST`, directly after the `PostgresFuelBalanceStore.transaction` entry, add:
  ```python
      (_B + "fuel_balance.adapters.postgres_fuel_balance_store", "PostgresFuelBalanceStore.schedule_inputs.work"):
          _WRITER + " (OWN-G2: the fuel_night tick stage's due-night read, scheduled.run_site; the same DB clock as "
          "`transaction`, which assesses each due night)",
  ```
  (b) Add `test_schedule_inputs_is_called_only_by_the_tick_stage`, which makes the `_WRITER` claim checkable. Use `ast`
  over every `.py` under `backend/assetops_backend`. Collect each `Call` whose `func` is an `Attribute` named
  `schedule_inputs`. Assert that the set of calling files is exactly
  `{"assetops_backend/fuel_balance/scheduled.py"}` (the store's definition and the Protocol in `model.py` are not
  calls). Then assert that `assetops_backend.fuel_balance.scheduled` is **not** in `listed_modules()`. If it is
  listed, stop and report: a stored compose would then reach a writer clock.

**(2) The container copy list is a fix-now. The diesel tests are demo-critical (ST-K). (D-E2.2)**
- `tools/run-backend-suite-in-container.sh:49-51` copies only the code folders. Tests read four tracked inputs outside
  them: `.agent/DIESEL-F0/` (`probe-result.json`, `kisiwa-001-bindings.draft.json`), `.agent/DIESEL-D0/`
  (`kisiwa-diesel-hybrid-60kw.draft.yaml`), `Docs/demo-sprint/chain-graph.dot` and `.gitattributes`. The readers are
  `test_k0_operational_actions.py:45,475`, `test_k1_kisiwa_fixtures.py:34,36`, `test_k3...:24`, `test_k4a...:29`,
  `test_k5...:22` and `test_ch5b_graph.py:17`. Copy exactly these, not all of `.agent/` (1.7 GB) or `Docs/`.
- **Fix:** line 50 becomes
  ```sh
    ./backend ./contracts ./simulator ./gateway ./host ./field ./config ./contract-fixtures ./tools ./var ./frontend/src ./frontend/docs \
    ./.agent/DIESEL-D0 ./.agent/DIESEL-F0 ./Docs/demo-sprint ./.gitattributes \
  ```
  The comment at line 48 gets: `..., the frontend source, and the tracked test inputs under .agent/DIESEL-*,
  Docs/demo-sprint and .gitattributes`. All four paths are tracked. If `tar` fails on a missing path, stop: the
  checkout is wrong.
- Required: K3, K4a and K5 (fuel-balance rules, unexplained-fuel Finding rules, night text), K0, K1 and K7 (Kisiwa
  fixtures and story) and ch5b_graph are **re-run in the container** (list in E2.2). This is the diesel rules' first
  container run since they merged.

**(3) ch6b, Optimize card against the board: a test-design error. It is not a product inconsistency and not a date
effect. (D-E2.3)**
- There is no date effect. The fixture fixes the window to D7..D14 (`mechanism_dataset.day`, D1 = Mon 19 Oct 2026), so
  `from` = 25 Oct and `to` = 1 Nov 00:00 UTC. It does not end today.
- The cause: for a mini-grid Site, the summary row's `nodes` are re-evaluated over the summary's **window days**,
  D7..D13 (`site_outcomes/read.py:529-555` `_window_parts`, CH6b1-R Q1). The test compares them with the board read
  over `kobo["window"]`. For a mini Site that is the one **board day**, D13: `summary_window` returns DAY, and the mini
  compose window is that day (`mini.py:622`). The KPI node's `days` therefore differ by design: a week on the
  Portfolio, one day on the board. The coherence check states the same rule. V4 compares summary nodes with board
  nodes **only on S for mini Sites**, "one day on both; other windows differ by design"
  (`tools/checks/chain_coherence.py:1442`). The CH5d1-R test spec says "the Kobo Optimize row's `nodes` equal the
  **S** board's" (`build-sheet-CH-5d.md` §3). The asserts that did pass show the product invariant: the card is the one
  builder over the rows, and the chain cards equal the summary cards. The demo client sees the same money on the card
  and on the board, because the cost claim is a stored consequence and has no days.
- **Fix (test only), `backend/tests/test_ch6b_estate_postgres.py::test_optimize_card_is_the_one_builder_over_the_summary_rows_and_equals_the_board`:**
  Keep the week asserts on the card, the order and the chain (`:236-239`). Replace `:242` with
  `assert set(row["nodes"]) == set(there["nodes"])` and
  `assert row["nodes"]["earnings"] == there["nodes"]["earnings"], (row["nodes"]["earnings"], there["nodes"]["earnings"])`.
  The cost claim has no days. Keep `:243-248`. Then add the S check (V4 at L2m). Read `/api/estate/outcome-summary`
  with `{"from": _utc(d13), "to": _utc(d13 + timedelta(days=1))}`. This is a one-day pair of UTC midnights, so
  `window_day` rule 2 selects D13 and `window_days` is `(D13,)`. Assert that Kobo's `OPTIMIZE_COST` row `nodes` equal
  the `OPTIMIZE_COST` `nodes` of `day` exactly. Docstring: "...equal the board's on S (one day on both). On the week
  only the cost claim is compared, because the KPI days differ by design (CH6b1-R Q1, V4)". **If the S equality fails,
  stop and report.** That would be a real contradiction between the board and the Portfolio.

**(4) Frontend s502: fix the test fixture, not the wording or the scan. Leave the evEnergy timeout. (D-E2.4)**
- Since K8 R-LOAD (`ffc23b202`), the Overview objective line names the Site's **own** LOAD components
  (`sites/SiteWindowOverview.tsx:492-500`). Clients see it on every mini-grid Overview. On the demo Sites it reads:
  Kobo (it has a clinic) gets v69's `MINIGRID_OBJECTIVE`, "residential, clinic and productive loads". Kisiwa gets
  "Households, Cold store (ice and fish) and Water pump". Neither line contains the bare word "load". The flagged
  sentence comes only from the shared test fixture `HYBRID_MINI_GRID_SITE`, whose one LOAD is named
  "Distribution load" (`sites/__tests__/sldFixtures.ts:88`). `s5SiteWindowOverview.test.tsx:44-55` was already adapted
  with `withLoadNames`; s502 was missed. So this is a fixture lag from K8, not a defect a client sees. The scan stays
  as it is: "load" in our own prose stays flagged (`productVocabulary.json:56`), which keeps the owner's
  no-system-vocabulary rule. The names an operator gives a Site's parts are their data, and the product must not
  rewrite them.
- **Fix:** move `withLoadNames` and `KOBO_LOAD_NAMES` from `s5SiteWindowOverview.test.tsx:44-53` into
  `frontend/src/sites/__tests__/sldFixtures.ts` as exports. Give `withLoadNames` a `site` parameter, because it is now
  shared. Use it in both test files. In `s502OverviewFindingList.test.tsx:30`, `DETAIL` serves
  `withLoadNames(HYBRID_MINI_GRID_SITE, KOBO_LOAD_NAMES)`, and `SITE_ID` stays as it is. Do not edit
  `productVocabulary.json` or the shared fixture's components.
- `evEnergy.test.tsx::energy_states_table_loading` passes alone (12/12). It timed out at 10 s only under the load of
  the full run. Leave it: a bigger timeout would hide real slowness, and the demo does not show this screen state.
  → BL-61.

**(5) The 25 pre-existing failures. All are "P": they fail identically at 733eaf75c. (D-E2.5)**
"Stale" needs two things. The builder names the merged commit whose sheet **intends** the new value, and the change
in the assert is exactly that commit's change. Anything else: **stop, edit no product code, report to the
Architect.**

| Group | Tests | Demo beat? | Ruling | Round |
|---|---|---|---|---|
| G-a Catalogue/head pins | `test_ch1a_snapshot_postgres::test_0043...`, `test_cc_schema_postgres::test_chain_sole_head_and_trial_catalog`, `test_out_d1_schema_postgres::test_sole_head_chain_and_catalog`, `test_w204_cold_migration::TestMigration0023::...`, `test_w207_ev_money_postgres::TestMigration0026::...`, `test_w403_migration_postgres::TestMigration0030` x3 | They guard append-only and the schema under every screen | **Fix (stale).** Add the CH-5c `0047` `*_cic_*` triggers in catalogue order. For w207, add the `0053_fuel_cost_2` `model_id` check widening. For w403, add the `mini_alternative_revision` unique-key change from the migration that made it. For w204, add the trigger delta. **Each delta must name its migration file on main. A delta with no migration is a stop.** The append-only triggers must still be in every list. | FR-A |
| G-b Trial formula vocabulary | `test_cc_schema_postgres::test_trial_rows_chain_scope_and_append_only` (`:227`, "DID NOT RAISE") | As G-a | **Fix (stale).** `0053_fuel_cost_2` made `trial-fuel-comparison/2` valid (FUEL-1 A1, `972dc747f`). Change the invalid example to `"trial-fuel-comparison/9"`. The UPDATE/DELETE append-only asserts (`:242-244`) stay and must pass. | FR-A |
| G-c Scenario pins | `test_scenario_fingerprints.py` x3: 24 scenarios shipped against 14 listed; `kobo-mill-midday` v1 and `kobo-night-early-after-before-mill` v1 are unpinned; the "v2 supersedes v1" rule fails | **Yes.** The E3 prepare runs them (ST-3 mill, DD-1a2 before-mill) | **Fix.** For each new file, confirm it is unchanged since the merge that introduced it (`git log --oneline -- <file>` shows a DD-1a1, DD-1a2 or DIESEL commit). Then pin the fingerprint the test prints. List all 24 files. Add an explicit `FIRST_SHIPPED_AS_V1 = {...}` exemption, with the introducing commit in a comment for each entry. The rule stays strict for the original 14. | FR-A |
| G-d Renamed or added fields | `test_w302_financials_links_postgres::...fall_back...` (`window_links` is now `windowed_lines`); `test_ch4_opportunity_postgres::test_backfill...` (extra `headroom_unit`, CH-6b2 `6b4e682f2`); `test_walk1_productive_producer_postgres::...` (extra `generator-no-load-fuel-rate` 3.3, `GENERIC_DEFAULT`, FUEL-1 A1 `972dc747f`) | ch4 and walk1 are on the ST-3 path | **Fix (stale).** Rename the call. Add the keys to the expected values, with the commit in a comment. | FR-A |
| G-e Kobo board states | `test_out_b4_board_postgres::test_kobo_guardrail_two_board_days`, `::test_kobo_estate_finding_rows_and_states`. They expect only UNKNOWN/NOT_MEASURED; the board now shows NO_OBJECTIVE, NEEDS_ATTENTION and WATCH | **Yes** (ST-1, ST-2) | **Diagnose, then fix the test or stop.** The likely cause is the assert's premise, "the s602b overview is STALE_PROJECTION, so the outcomes stay UNKNOWN" (`:429-431`). It predates CH-6, after which states come from stored `site_day_snapshot` day rows, not from the overview projection. It is stale **only if** each measured state comes from stored, settled day rows of that board day, and the same board's readiness or days line does not say that day is unknown. Then assert the recorded states, and keep `MG-8 == NOT_APPLICABLE`. **Stop** if a NEEDS_ATTENTION or WATCH appears on a day that the same board calls not checked: a client would see a judgement on an unchecked day. | FR-A |
| G-f Gap naming | `test_idx_gaps_postgres::TestMovingAndBoard::test_p5_board_settles...` (10-06 now settles; `none_declared` = productive_kwh) | ST-1 coverage line | **Diagnose, then fix or stop.** K10 v2 (`56256bbc9`) stopped counting a declared-absent measure as a gap. It is stale **only if** productive_kwh was the one missing measure on 10-06. Then assert that the day settles and that the gaps line does not name productive_kwh. **Stop** if another measure is missing and the day still settles. | FR-A |
| G-g Grow text | `test_ch6_nodes_postgres::test_kobo_estate_grow_nodes` ("Not known yet" is now "No productive-use sales — no productive-use equipment declared") | **Yes** (ST-3) | **Diagnose, then fix or stop.** It is stale **only if** the mechanism Kobo (`backend/conversions/mechanism-v1.json` and the Site it imports) declares no productive-use equipment. The demo Kobo declares its mill: `test_walk1_productive_producer_postgres` "kobo declares supply uses" (green after G-d) and E3's MILL rows show it. **Stop** if the mechanism Kobo declares the mill, because "none declared" would then be a false statement about Kobo. | FR-A |
| G-h Mill-path pins | `test_k6b_fuel_verification_postgres::test_5_mill_path_outputs_equal_the_first_commit_pins`. The grade for 2026-10-25 is `None` where the pin says `NO_DATA`; `declared_by` is `owner <d-4>` where the pin says `<d-3>` | **Yes** (ST-3 mill verification) | **Diagnose, then re-pin or stop.** `declared_by` is a declaration ordinal, so one more earlier declaration in the fixture (DD-1b1 or K10 v2) shifts it. That part is stale once the extra declaration is named. The grade is stale **only if** 10-25 is now a day the baseline selection does not read at all (no row, rather than a graded row) because of a named change, and the verdict, the counted days and the before and after values all equal the pins byte for byte. **Stop** if any verdict, count or value moves. | FR-A |
| G-i Kisiwa fuel row on the Portfolio | `test_k8_estate_fuel_postgres::test_k8_fuel_row_in_estate_findings_never_in_money` (`:145`: the fuel Finding appears in estate Findings, but not in the Portfolio `rows`) | **Yes** (ST-K step 6, "Portfolio fuel row") | **Diagnose. A product cause stops the round.** A Portfolio member must have `lifecycle in ("SUPPORTED","UNCONFIRMED")` (`estate/portfolio.py:47`, `:840-846`), and then passes the lens and a page of `req.limit`. Find which of these drops the row. If the cause is in the test setup (the forced coverage row's lifecycle, or its page position under the test's limit), fix the setup so it builds the row the real Kisiwa data builds, and say so. **Stop** if the same gate would drop the real Kisiwa row. E4 adds a check either way (E2.4). | FR-A |
| G-j Opportunity routine scan | `test_w403_opportunity_scan_postgres::test_routine_scan_retention_edge_and_missing_day` (`:101`), `::test_uf6_failed_job_is_retained...` (`:112`, queues nothing) | **Yes**, indirectly: the routine scan is how a day added live reaches the opportunity (ST-7) | **Diagnose, then fix or stop.** Suspected cause: CH-9 u2 (`badd2fbb9`, "study day_heads per measured daylight hour") changed what a head needs, and the w402 fixture ingests too few daylight hours. It is stale **only if** the fixture lacks hours the new rule needs. Then add the measured hours to the fixture, and keep the retention-edge asserts exact. **Stop** if a day with full daylight hours is not queued. | FR-A |
| G-k Decision replay 422 | `test_w403_replay_postgres` x2 (`DECISION_INPUT_INVALID` on the positive replay) | **No.** The W4-03 Alternatives and decision replay are not in DS-1 (ST-0 to ST-7, ST-K) | **Backlog BL-60.** No presented beat uses it. The scenarios the demo does use run through E3's prepare and self-check. | — |
| G-l w301 golden (T6) | `test_w301_estate_golden_postgres.py` x6 (only `$.summary.claims` gains `count.opportunities`) | It guards the estate Findings body (ST-6) | **Deferred to FR-B (D-E2.6).** E2 showed the only cause is the `claims` addition from CH-5a2b: there was no `run_pending -> []`, and the skew was about 20 ms. FR-A changes no product code, so before E3 the golden has nothing new to guard. It must be green before the next product change. | FR-B |
| G-m Needs a prepared `var/` | `test_ch5c_env_parity::...one_code_version`, `test_demo_combined_mill.py` x2 (`SystemExit: Run prepare first.`, `tools/demo_combined.py:620`) | `demo_combined_mill` is the order of the mill steps in the prepare (ST-3) | **Bounded at E4.** Run these 3 tests in the E3 checkout right after E3's prepare; they take seconds (E2.4). They claim to be L0 "no work folder" tests but read `story.json`. Making them hermetic → BL-62. | E4 |

**(6) Wrapper defects. (D-E2.7)**
- **Close template `HARNESS_URL_MISMATCH`: a real tooling defect, fixed in FR-B.** `tools/mechanism_dataset.py ensure`
  builds `states` and then `close` **in one Python process** (`:421-432`). `build` sets `ASSETOPS_TEST_DATABASE_URL`
  for each build (`:155`). But `test_s4_finding_store_postgres.URL` is a module global, bound at first import to the
  states build DB. So `_harness_checked` refuses the close build (`backend/tests/mechanism_dataset.py:696-702`). The
  guard is right; the process model is wrong.
  **Fix:** `ensure` runs each variant build in a child process:
  `subprocess.run([sys.executable, str(Path(__file__).resolve()), "build", "--variant", day_set, "--budget", "inf"], env=os.environ.copy())`.
  It checks the return code where it calls `build(...)` today, and `build` itself does not change. Add one L0 test
  that monkeypatches `subprocess.run` and asserts one child per wanted variant and no in-process `build` call. The L2m
  proof is the FR-B run: it builds `close` and runs
  `test_md0_mechanism_postgres.py::test_close_variant_resolves_closes_after_seven_clean_days_and_recurs`. That test is
  the only Postgres proof of ST-2's "resolved, then recurs" path, so it runs before W-1.
- **Empty `slice-paths.txt`: fixed in FR-B.** `tools/run-backend-suite-in-container.ps1:85` pipes `git diff` into
  `Set-Content`. When the diff is empty, PowerShell 5.1 writes no file. `ensure --close auto` then reads "diff
  unreadable" and builds the close template. Fix: `$paths = @(& git -C $worktree diff --name-only $baseSha 2>$null)`,
  then `[System.IO.File]::WriteAllLines((Join-Path $runDir 'slice-paths.txt'), [string[]]$paths)`, which writes an
  empty file. `slice_inputs` then returns `[]`, and the close test is deselected loudly, as designed. It does not
  matter for FR-A, which runs `-Close no`.
- **60-minute cap on `-Targets`: fixed in FR-B (one line).** `:142` caps every custom `-Targets` run at 60 minutes,
  even one that names a directory. Apply the 60-minute cap only when every target is a `.py` file or a node id.
  Otherwise keep the cap derived from the tier. Not needed before E3/E4, which do not run this wrapper.

### E2.2 FR-A (now; E3 waits for it): builder card

- **Branch** `task/E2-fix-A` from main 9bbbb5626. **Model: Sonnet.** No item needs design. Each diagnose item (G-e to
  G-j) has a written stale test and a stop rule. The builder sends its stops to the Architect as one batched message
  and carries on with the other items.
- **Files:** `backend/tests/test_ch5c2_clock_guard.py`; `tools/run-backend-suite-in-container.sh`;
  `backend/tests/test_ch6b_estate_postgres.py`; `frontend/src/sites/__tests__/sldFixtures.ts`,
  `frontend/src/shell/__tests__/s502OverviewFindingList.test.tsx` and
  `frontend/src/shell/__tests__/s5SiteWindowOverview.test.tsx`; and the test files of G-a to G-j and their fixtures
  under `backend/tests/` (G-j may touch the w402 test fixture). **Do not edit any file under
  `backend/assetops_backend/` or `config/`, any file in `frontend/src/` outside `__tests__`, or any file in `tools/`
  other than the `.sh`.** If a product edit is needed, stop.
- **Order:** (2) copy list, (1) guard, (3) ch6b, (4) s502, then G-a to G-d (mechanical), then G-e to G-j (diagnose),
  then one scoped run, then the packet.
- **Scoped re-run (one heavy job, after all edits):**
  `tools\run-backend-suite-in-container.ps1 -Close no -Workers 2 -CapMinutes 60 -Targets "<list>"`, where the list is
  `backend/tests/test_ch5c2_clock_guard.py backend/tests/test_k0_operational_actions.py backend/tests/test_k1_kisiwa_fixtures.py
  backend/tests/test_k3_fuel_balance_rules.py backend/tests/test_k4a_fuel_finding_rules.py backend/tests/test_k5_fuel_night_text.py
  backend/tests/test_k7_kisiwa_story.py backend/tests/test_ch5b_graph.py backend/tests/test_ch6b_estate_postgres.py
  backend/tests/test_ch6_nodes_postgres.py backend/tests/test_ch1a_snapshot_postgres.py backend/tests/test_cc_schema_postgres.py
  backend/tests/test_out_d1_schema_postgres.py backend/tests/test_w204_cold_migration.py backend/tests/test_w207_ev_money_postgres.py
  backend/tests/test_w403_migration_postgres.py backend/tests/test_scenario_fingerprints.py backend/tests/test_w302_financials_links_postgres.py
  backend/tests/test_ch4_opportunity_postgres.py backend/tests/test_walk1_productive_producer_postgres.py
  backend/tests/test_out_b4_board_postgres.py backend/tests/test_idx_gaps_postgres.py backend/tests/test_k6b_fuel_verification_postgres.py
  backend/tests/test_k8_estate_fuel_postgres.py backend/tests/test_w403_opportunity_scan_postgres.py`.
  The states template built in E2a is reused. FR-A loads no changed module into the build, so nothing is rebuilt. If
  `ensure` reports a rebuild anyway, let it run (about 11 minutes) and note it. Frontend:
  `npx vitest run src/shell/__tests__/s502OverviewFindingList.test.tsx src/shell/__tests__/s5SiteWindowOverview.test.tsx`.
  At merge prep, run `tools\check-all.ps1` once (18 guards).
- **Pass bar:** every listed file is green, except items stopped under their stop rule. Each stop is listed with its
  cause in the packet. K3, K4a and K5 must collect and pass. Any failure in a K file is a stop, and E3 waits for the
  Architect.
- **Review:** one fresh Claude reviewer (Opus; the diff is small and test-only). It checks every "stale" claim against
  its named commit. Merge on ACCEPT, then E3.

### E2.3 FR-B (Wed 11 to Fri 13 Nov, before the Sat 14 backend run and W-1): builder card

- **Branch** `task/E2-fix-B`. **Model: Sonnet.** Files: `tools/mechanism_dataset.py` (`ensure` builds in child
  processes), `tools/run-backend-suite-in-container.ps1` (`:85` empty file, `:142` cap), one L0 test for `ensure`, and
  `backend/tests/fixtures/w3/w301-estate-golden.json` (T6).
- **T6**, as in Parts A.2 and F.2: write once with `ASSETOPS_WRITE_W301_GOLDEN=1` on a `*_test` DB, then check the
  diff. Only `claims` entries under the Findings `summary` may be added; anything else is a stop. Then verify without
  the flag: 6 of 6 pass.
- **Run (one heavy job):** `-Close yes -Workers 2 -CapMinutes 90 -Targets "backend/tests/test_md0_mechanism_postgres.py backend/tests/test_w301_estate_golden_postgres.py <the ensure L0 test>"`.
  `tools/mechanism_dataset.py` is in the template fingerprint, so this rebuilds states and builds close (about
  25 minutes), which proves the child-process fix end to end. Then run `check-all`. Also confirm that a run from main
  with nothing changed logs `close not selected` (the empty-file fix). Read the Sat 14 run's log, or do a `-Close auto`
  dry start.
- **Review:** a fresh Claude reviewer (Sonnet). Merge before Sat 14.

### E2.4 Additions to E4 (no code)
- **E4-K8:** on the E3 build, `GET /api/estate/portfolio` over the ST-K week shows the Kisiwa fuel Finding in `rows`
  with the "Verified" label (R-1), and not in `money` or `selected_lines`. Record the result in the E4 notes. If the
  row is missing, that is a High, and E6 waits.
- **E4-env:** in the E3 checkout, after its prepare, run
  `pytest backend/tests/test_ch5c_env_parity.py backend/tests/test_demo_combined_mill.py` (L0, seconds). A failure is
  an E4 stop.
- The E2-0 clock check runs again before E3 (as F.3 already says).

### E2.5 Size
- FR-A: about **0.45 unit** of building (0.15 mechanical, 0.3 for the six diagnoses). Machine time: one scoped run of
  about **25 to 35 minutes** (mostly the L2m files ch6b and ch6), about 1 minute of vitest and about 17 minutes of
  check-all. Review: about 0.15 unit. With no stops, E3 can start in about **2.5 to 3 hours** of wall time. A stop on
  G-e, G-g, G-h, G-i or G-j (all presented beats) adds an Architect ruling, and E3 waits for it.
- FR-B: about **0.25 unit**, plus about 45 minutes of machine time (template builds about 25 minutes, T6 about
  20 minutes) and check-all.

### E2.6 Decisions
- **D-E2.1** The `schedule_inputs` DB-clock read is a tick writer's read, on the same clock as the assessment it
  gates. It goes on the allow-list as `_WRITER`, with a call-site test that keeps it out of stored composes. The story
  clock and the visibility cutoff limit reads and never drive writers.
- **D-E2.2** The container copies the four tracked test inputs (`.agent/DIESEL-D0`, `.agent/DIESEL-F0`,
  `Docs/demo-sprint`, `.gitattributes`). The diesel rule tests (K0, K1, K3, K4a, K5, K7) re-run in FR-A, and any
  failure there holds E3.
- **D-E2.3** ch6b: comparing the full `nodes` over the week is a test-design error. The product rule (CH6b1-R Q1, V4)
  is that nodes are equal on S for mini Sites, and that on other windows only the cost claim is equal. Fix the test
  and add the S equality at L2m. This is not a date effect.
- **D-E2.4** s502 lags the K8 R-LOAD fixture change. Share `withLoadNames`. The wording and the vocabulary scan stay
  as they are. Leave the evEnergy timeout (BL-61).
- **D-E2.5** Of the 25 P failures: G-a to G-d are fixed as stale, each with a named commit. G-e to G-j are presented
  beats and are diagnosed in FR-A, each against a written stale test with a stop rule. G-k goes to BL-60. G-l (T6)
  goes to FR-B. G-m is bounded at E4, and making those tests hermetic is BL-62.
- **D-E2.6** T6 moves from E2 to FR-B. FR-A changes no product code, so before E3 the golden has nothing new to guard.
  It is green before the next product change (Sat 14).
- **D-E2.7** Close-template build: `ensure` builds each variant in a child process, `slice-paths.txt` is always
  written, and the 60-minute `-Targets` cap applies only to file targets. All three are in FR-B, before the Sat 14
  run. They are not needed before E3, because E3 and E4 do not run the wrapper.
- **D-E2.8** E3 starts after FR-A merges, when every red in the scoped run is either fixed or stopped and ruled. A stop
  on a presented beat holds E3 until it is ruled.

