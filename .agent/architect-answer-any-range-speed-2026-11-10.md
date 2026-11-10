# Architect answer: fast pages for any date range (2026-11-10)

- Architect: Claude (fresh `assetops-architect` instance). Binding checked: `.ai/ROLE_CONFIG.md`, Architect = Claude since 2026-10-27.
- Owner question, verbatim: `.agent/owner-any-range-speed-2026-11-10.md`. Owner instruction of 2026-11-03, verbatim (`.agent/owner-walkthrough-notes-2026-11-01.md`): "does it not make sense to have a per day snapshot that gets recaculated based on changes?"; "should be stored and recalcualted per event and that trigger should be declaratively designed, perhaps some event register"; "we should make sure the site and portolio data should load quickly, today it is actually really slow"; item 12 "make sure it is performant  and scale path is designed"; item 13 "usage of snapshot is encouraged".
- Owner away, verbatim (`.agent/owner-away-architect-decides-2026-11-08.md`): "let the architect make decisions if there are any input required from my side and make sure it makes decisions based on understanding of how real sites work and what assetops is trying to achieve, no cutting corners on fundamentals". Decisions below are logged in `build-sheet-OWN-GAPS-2026-11-08.md` as D-ANY.1 to D-ANY.4 for owner review.

## 1. In plain words, for the owner

- **Yes, you asked for daily snapshots, and you were right.** The app has them (one graded row per Site, day and measure, rebuilt per event through the event register). But today they answer only "how good was each day's data" plus a few daily values. They are **not** what the slow parts of the pages read.
- **The slow parts recompute from raw readings on every page load.** A Kobo or Kisiwa board re-reads and re-fingerprints the raw readings of 57 daylight hours to check that each stored hourly result is still current. The Portfolio re-derives every day's dispatch status, claim limit and evidence trail from raw readings for every Site in the range. That is why the time grows with the length of the range: a week takes about 12 s, a month about 36 s.
- **The demo speed comes from a page cache, not from the design you asked for.** Whole pages are stored after someone (or the pre-load list) asks for them once. A range nobody asked for before is a full recompute. That is why "the demo's pages" are fast and any other range is not.
- **The fix is the one you described.** Store the expensive daily results as daily rows, rebuild only the days an event touches, and build any page by adding up stored days. With that, any range reads a few hundred small rows instead of tens of thousands of readings: under 2 s for a board or a Portfolio month, with no pre-loading.
- **Size:** about 7 lane-units in two slices (Site boards first, then Portfolio).

## 2. Measured: where the time goes

Method. In-process compose with `TestClient` over `host/lab_app.py` on the plan2 checkout (`b234cea2a`), against `assetops_polish_client2_test` (alembic `0058`, story S = 2026-11-07), `ASSETOPS_RESPONSE_STORE=off` (nothing read or written in `chain_response`), serve keys from `var/polish_client2/keys.json`. SQL timed per statement by SQLAlchemy cursor events, attributed to the innermost product function; phases from the existing `perf` timers (`Server-Timing`) and cProfile. One process at a time; free RAM stayed 3.1-3.4 GB. "Cold" = first request in a fresh process; "repeat" = the same request again in that process (no response store, so it recomputes). Times without the profiler; the phase split is from the same runs' `perf` timers.

| Request | Cold | Repeat | SQL statements / SQL time | Body |
|---|---|---|---|---|
| Kobo board, day 2026-10-21 | **11.2 s** | 9.8 s | 809 / 7.4 s | 14 KB |
| Kisiwa board, day 2026-11-05 | **11.3 s** | 10.8 s | 830 / 7.4 s | 11 KB |
| Cold board, week 10-31..11-06 (local) | **1.6 s** | 0.8 s | 109 / 0.8 s | 12 KB |
| Portfolio, week 10-31..11-07 | **12.1 s** | 10.8 s | 693 / 6.2 s | 67 KB |
| Portfolio, 2026-10-12..10-19 (not pre-loaded) | **4.2 s** | 3.4 s | 162 / 2.1 s | 15 KB |
| Portfolio, month 10-07..11-07 (scaling check) | **36.1 s** | 37.5 s | 1,606 / 17.0 s | 111 KB |

The 10-12..10-19 range is cheaper only because little data existed then (Kobo from 10-10, Cold from 10-14, EV from 10-23). Cost grows with Site-days of data, not with the request.

### Phase breakdown (cold run)

| Phase | Kobo day | Kisiwa day | Cold week | Portfolio week | Portfolio 10-12..19 | Portfolio month |
|---|---|---|---|---|---|---|
| Mini depth: hourly currentness re-check (`mini_depth/read.py:_hour` → `_cutoff_sha` → `load_hour_inputs` → `store.read_hour_rows`, 57 hours, 5 days) | **~7.0 s** (513 SQL, 5.3 s SQL) | **~7.3 s** (567 SQL, 4.7 s SQL) | - | - | - | - |
| Mini depth: provenance blocks (`provenance.mini_blocks` → `link_rows_on`, 8.5k link rows hashed) | ~1.9 s | ~1.9 s | - | (inside evidence) | | |
| Findings / coverage (Portfolio: `coverage._mini_grid_basis` → `dispatch_days` → `assessment_store._window_read` + `cohort.select_cohort` over ~34k readings) | threads 0.03-0.2 s | 0.1 s | cold findings 0.03 s | **5.6 s** | 1.7 s | **17.8 s** |
| Evidence (Portfolio: `claim_limit_on`, provenance `link_rows`, `selected_windows`) | - | - | - | **3.8 s** | 1.0 s | **13.6 s** |
| Money (financial/evidence money lines) | price/productive 0.1 s | 0.1 s | 0.01 s | **1.2 s** | 0.16 s | in the above |
| Performance comparison (`performance_gate` lineage, `read.dispatch`) | 0.6 s | 0.3 s | - | - | - | - |
| Work and action lists (`read.work_index`, action index) | 0.55 s | 0.6 s | **0.74 s** | 0.14 s | 0.10 s | 0.12 s |
| Mini/opportunity (`read.opportunity`, chain claims) | 0.16 s | 0.09 s | - | in findings | | |
| Day snapshots (`read.chain_day`, graded rows) | **0.03-0.16 s** | 0.14 s | 0.002 s | - | | |
| Roll-up (Portfolio summary, rows, cards, disclosure) | - | - | - | 0.9 s | 0.45 s | 1.9 s |
| Serialization (JSON encode + transport) | < 0.2 s | < 0.3 s | < 0.2 s | < 0.2 s | < 0.2 s | < 0.4 s |

Findings from the numbers:

1. **Boards (mini grid): 80-85% is one thing.** The renewable depth reads 5 local days of daylight hours, and for each hour it rebuilds the hour's input set from raw readings to recompute a SHA-256 and compare it with the stored result's digest (`mini_depth/read.py:182-191`, `:494-516`). This is a "has anything changed since?" question answered by recomputing, on every page view.
2. **Portfolio: the same pattern per Site-day.** Each day's dispatch status (CURRENT / STALE / PENDING) and claim limit are re-derived from the assessment window and its readings, and evidence provenance is re-hashed link by link. It is linear in Site-days: week 12 s, month 36 s. At 100 Sites a month would take many minutes.
3. **The day snapshots that exist are already fast** (`read.chain_day` 2-160 ms). The design works where it was applied.
4. **Serialization and roll-up are not the problem** (under 0.5 s, except the Portfolio disclosure at 0.4-1.3 s).
5. Cold/EV boards are near budget (1.6 s cold); their largest part is the work list read (0.5-0.7 s).
6. Versus earlier measurements: QW-1 (2026-11-03) measured the Kobo board at 9.5-10.1 s cold and the Portfolio week at 8.2 s; CH5c-R2 (2026-11-04) at 4.5 s and 5.2 s after CH-5a1. The numbers have since grown with the data (Kisiwa, more days), which is the linear cost showing.

## 3. Snapshot coverage today, and why it ended up covering grades

### What day snapshots cover today

`site_day_snapshot` (migration `0043`, `chain/snapshots.py`, `chain/adapters/postgres_snapshot_store.py`) holds, per Site, local day, subject and measure: coverage seconds, grade (COMPLETE / PARTIAL / LOW / NO_DATA / NOT_EXPECTED / PENDING), a small `value` and `money`, revisioned by input fingerprint, with `computed_at` for as-of reads. Seven measures (`chain/measures.py`): `productive_kwh`, `daylight_headroom_kw`, `critical_served`, `avoidable_gen_min`, `chamber_temp_c`, `backup_start_chain`, `charging_kwh`. They are rebuilt per event: outbox (`event_outbox`) → register (`config/chain/event-register-v1.yaml`, `chain/events.py`) → `snapshot_dirty` (Site, day, measure) → builder in the tick. This part is exactly the owner's 2026-11-03 design.

Pages read them for: day grades and settledness (board `read.chain_day`, CH-5a1 R4), the window's "how many days, of which grade" counts, MG-5 from `critical_served`, and some daily values. They do **not** feed the mini-depth hourly currentness, the Portfolio dispatch-day coverage, claim limits, evidence provenance or money lines. Those are the measured 85-95%.

### What could be served from stored daily rows (keeping "as known at k")

| Page part | Today | Stored row (per event) | "As known at k" |
|---|---|---|---|
| Board mini depth (renewable, fuel, service, backup) | per-hour re-fingerprint of raw readings | one row per (Site, domain, hour window): selected head, its state, cards/rows envelope, provenance class summary | rows revisioned with `computed_at`; read latest revision with `computed_at <= k`. An input event recorded `<= k` and not consumed by `k` (`event_outbox.recorded_at`, `event_consumption.processed_at`) makes that hour PENDING, as today's `PENDING_RECOMPUTE` |
| Portfolio coverage (`_mini_grid_basis`) | per-day `dispatch_days` from the assessment window | one row per (Site, S3 day window): available, selection seq, job states, S3 status | same; the Finding-index match pass stays one read per Site |
| Portfolio evidence | `claim_limit_on`, provenance `link_rows` per window | per (Site, day): claim-limit components and provenance class counts; provenance per assessment revision is immutable and stored once | same; immutable per revision |
| Portfolio money | windowed financial and evidence-money lines | per (Site, day) money lines with `assumption_revision_id` (as `site_day_snapshot.money` already does) | same; a price change is a register event (`by_assumption_key`, `from_valid_local_to_today`) |
| Findings / threads | already stored threads | unchanged; lifecycle read at `lifecycle_cutoff(k)` (D-E4.2, D-E3b.2) | unchanged |
| Work and action lists | live lists | unchanged (not range-bound); batch the 4 reads | unchanged |
| Roll-up, cards, disclosure | computed per request | computed per request from the rows above | n/a |

R-1 visibility (occurrence visibility compared with request `known_at`, both recording times) and `lifecycle_cutoff` are unaffected: threads stay where they are, and every new row carries a recording-time `computed_at`, the same rule `site_day_snapshot` already uses.

### Why the 2026-11-03 instruction ended up covering only grades

The trail, from the record:

1. **AG-1 / AG-20 (design proposal, 2026-11-03)** recorded the owner's words correctly: "Snapshots are the primary read source" (§11b). The QW-1 measurement written into §11b said the budgets "are reachable only if ... outcome rows, coverage and readiness are read from day snapshots; Findings from threads; **Portfolio evidence and money are read from snapshots**".
2. **CH-1a (`build-sheet-CH-1a.md`, Architect, 2026-11-03)** scoped the snapshot as graded **measure** rows, and stated: "No screen reads the snapshots yet. CH-5a and CH-6 switch screens over", and "No QW files are edited: `B/site_outcomes/*`, `B/estate/*` ... read only. Adapters call existing pure functions." The slow reads live in exactly those files. They were not outcome measures, so no measure was declared for them.
3. **CH-5a1 (`build-sheet-CH-5a.md` R4)** switched the board's readiness and grades to snapshots ("snapshot settledness"). No card was written to move mini-depth currentness, dispatch-day coverage, claim limit, provenance or money onto stored rows.
4. **CH-5c pre-flight (`.agent/CH-5c-preflight.md` P1, R3 sizing rule in `build-sheet-CH-5a.md`)** measured that per-Site selection compute dominated; the sizing rule said that case means "4 units (from snapshots)". The conclusion written was instead: "Batching alone cannot bring the Portfolio uncached time to 1.5-2.5 s; **the stored responses are the lever**".
5. **CH5c-R2 (`Docs/demo-sprint/client-demo-plan.html`, owner decision 2026-11-04)** offered three options: (A) batching plus a stored copy of each page with the demo-script pages pre-built; (B) accept 2-4 s; (C) nothing. **The from-snapshots read model was not among the options.** Option A said openly "an uncached request stays at about 2-4 s". The owner chose A ("go with option A").

So the honest answer to "why was the product built this way": the Architect carried your snapshot design into the data (grades and daily measures), but, under demo time pressure, offered a page cache instead of moving the expensive reads onto daily rows, and did not put the proper option in front of you. A page cache is fast only for pages already asked for. Then the uncached estimate (2-4 s) turned out to be 4-36 s as data grew, and the pre-load list (D-E4.1, D-E4.10) grew to cover the script. That was a corner cut on a fundamental. It is the decision to reverse.

## 4. The proper fix: any range under 2 s, no pre-loading

### Principle

Compute when data changes, not when someone looks (§11b's own sentence). Every range-bound page part reads stored rows at its **native grain** (hour window for mini depth, S3 day window for dispatch, Site-local day for claim, provenance and money). A page for any range adds up the stored rows inside that range. The work per page is O(Sites × days × kinds) small indexed rows, never raw readings.

### What gets stored

One generic, revisioned read-row table, a sibling of `site_day_snapshot` that follows its rules (append-only revisions, `computed_at`, builder version, input fingerprint):

```
site_period_read (
  tenant_id, site_id, kind,               -- e.g. 'mini_depth.renewable', 'mini_depth.fuel', 'dispatch.day',
                                          --      'evidence.claim', 'evidence.provenance', 'money.lines'
  period_start timestamptz, period_end timestamptz, local_day date,   -- native grain; local_day for the register
  revision int, builder_version text, input_fp text,
  state text,                             -- the kind's own state (CURRENT / STALE_SOURCE / UNKNOWN / ...)
  body jsonb,                             -- the exact fragment today's compose builds for that period
  computed_at timestamptz,
  PRIMARY KEY (tenant_id, site_id, kind, period_start, revision))
```

Plus `revision_provenance (assessment_revision_id PRIMARY KEY, block jsonb)`: the provenance of a selected revision never changes, so it is computed once.

The body is produced by the **existing** pure functions (the CH-1a adapter pattern), so the numbers and labels are today's, byte for byte.

### What triggers recalculation

The existing event register, nothing new. Each new kind is declared in `event-register-v1.yaml` like a measure: which event types dirty it (`reading.accepted` by role, `mini_depth` selection, `recompute_job` state, `by_assumption_key`, `foundation`) and how the event's span maps to days (`span_local`, `windows_local`, `from_valid_local_to_today`). The `snapshots` consumer marks `(site, day, kind)` dirty and the builder rebuilds only those periods in the tick, bounded by the stage limit. The read path never computes a period.

### Late and corrected data

- A late reading: its outbox event's valid-time span resolves to the Site-local days it touches; only those days are rebuilt, as a new revision. The old revision stays, so a request "as known at k" before the correction still reads what was known then.
- A configuration or price correction: `from_valid_local_to_today` dirties every day from its valid date; rebuilt in bounded pages per tick.
- Between the event and the rebuild, the read shows that period **PENDING** (an input event recorded `<= k` without a consumption by `k`), never a silently stale number. This is today's `PENDING_RECOMPUTE` semantics, now from the ledger instead of a re-hash.
- A code change to a builder bumps `builder_version`; rows of an older version read as PENDING until a backfill command rebuilds them.

### Scale path

| Stage | Size | What changes |
|---|---|---|
| Demo | 4 Sites | Indexes on `(tenant_id, site_id, kind, period_start)`; the response store stays only as an ETag/304 layer whose key is the max row revision in the range (no pre-load list, no Site-wide rebuild). |
| Pilot | ~100 Sites | A latest-revision head table per (site, kind, period); parallel chain-stage workers by Site (existing per-Site claim); monthly partitions above ~10M rows; dirty-queue age and stage-time alarms (§11b). |
| Estate | 1,000+ Sites | Estate-day roll-up rows per tenant/scope, maintained by the same consumer when a Site's day row changes, so a Portfolio month reads ~31 rows per scope, not Sites × days; broker relay from the outbox (§11b S2); read replicas. |

### Cards and size

Sizes in lane-units. Two slices, each under the 6-unit split rule. AR-2 and AR-3/AR-4 can run in two lanes after AR-1.

| Card | Scope | Size |
|---|---|---|
| **AR-0** Parity and speed guard | A parity harness: for every story request plus seeded random ranges (boards any day, Portfolio any from/to up to 31 days, historical `known_at`), the row-based compose equals today's compose byte for byte. `perf_budget.py` gains arbitrary-range cases with the store off and no pre-build: board ≤ 2 s, Portfolio month ≤ 2 s. | 0.5 |
| **AR-1** Read-row foundation | Migration (`site_period_read`, `revision_provenance`), port and Postgres adapter, generic builder and reader (one query per Sites × range × kinds), PENDING-at-k from outbox/consumption, register schema accepts the new kinds, backfill CLI. | 1.0 |
| **AR-2** Board mini depth on rows | Kinds `mini_depth.{renewable,fuel,service,backup}` at hour grain plus revision provenance; `mini_depth/read.py` reads rows; the on-read `_cutoff_sha` leaves the serve path (kept as the test oracle). | 1.5 |
| **AR-3** Portfolio coverage on rows | Kind `dispatch.day`; `coverage._mini_grid_basis` reads rows; match pass unchanged. | 1.0 |
| **AR-4** Portfolio evidence and money on rows | Kinds `evidence.claim`, `evidence.provenance`, `money.lines`; roll-up functions; each proven equal by AR-0. | 1.5 |
| **AR-5** Retire pre-loading | Remove the pre-load route list from serve and prepare (D-E4.1, D-E4.10, BL-64 become moot); response store keyed on row revisions as an ETag layer only; BL-65 folded in. | 0.75 |
| **AR-6** Work lists | Batch the board's 4 work-index reads into one (Cold/EV boards to under 1 s cold). | 0.5 |
| **Total** | Slice **ANY-1** (boards): AR-0, AR-1, AR-2 = 3.0. Slice **ANY-2** (Portfolio): AR-3, AR-4, AR-5, AR-6 = 3.75. | **6.75** |

Expected after: board any day ≈ 1.0-1.5 s cold (snapshots 0.1 s, rows 0.1 s, work lists 0.3 s, the rest unchanged); Portfolio any range up to a month ≈ 0.8-1.5 s; repeat requests 304.

### Risks

| Risk | Level | Handling |
|---|---|---|
| Not every window value is a sum of days (claim limit and cohort clashes, Site-local days against UTC Portfolio windows, partial edge days) | High | Store at the native grain; for any non-decomposable value store the components the window rule needs; AR-0 proves equality on seeded ranges including unaligned ones before any switch. A kind that cannot be proven equal stays on the old path and is reported, not approximated. |
| Honesty gap between event and rebuild | Medium | PENDING from the append-only outbox/consumption ledgers at `k`; a test injects a late reading and reads before and after the drain, live and historical. |
| Two code paths drift | Medium | Old compose kept only as the AR-0 oracle; serve path has one reader; AST guard that `site_outcomes/*` and `estate/*` do not call raw-reading reads on the serve path. |
| Rebuild cost after large corrections | Medium | Bounded pages per tick, dirty-queue age alarm; measured on a 70-day backfill (estimate: ~2 s per mini Site-day today → about 5 min for current data, once). |
| Builder version changes leave stale rows | Low | `builder_version` in the row; old versions read as PENDING; backfill command. |
| Machine RAM and test time | Low | L2 tests on `*_test` DBs only; one full suite at the end per the test-suite policy. |

## 5. Demo-criticality ruling

- **Will a CFO, COO or CEO use the date selector off-script? Plausibly, yes.** "Show me last month", "what about the week before" and "open yesterday on that Site" are the natural executive questions, and the selector sits at the top of every screen. Measured off-list: a board day 10-11 s, a Portfolio week 12 s, a Portfolio month 36 s. In front of a CFO a 10 s page reads as broken, and 36 s reads as a crash. It also contradicts the presented beat "a fast first page" and the owner's "site and portolio data should load quickly".
- **No range-agnostic warm-up.** Pre-building every day and every week on data arrival is more of the page-cache approach: it cannot cover arbitrary from/to, it multiplies the 5-6 min Site-wide rebuild after each `add-dates`, and it would be thrown away. Refused (D-ANY.3).
- **Pre-demo partial step: slice ANY-1 (boards, 3.0 units).** It is the first slice of the real fix, not a workaround, and it removes the largest single cost (80-85% of every mini-grid board, any day, any Site). It starts after FR-B (Wed 11 to Fri 13) and does not displace it (D-ANY.2).
- **ANY-2 (Portfolio, 3.75 units)** is BL-66's remainder. It is demo-critical if the client session is set after it can land; the owner sets the date (D-ANY.1). If the session comes first, the presenter rule applies.
- **Presenter rule until the fix lands (walkthrough today/tomorrow, FR-B, and any client session before ANY-2):** stay on the script's ranges. The Portfolio selector is used only for the pre-built week, S and month. Off-script, say "this range is being computed" and do not wait on it. The owner is told the measured numbers above before the walkthrough (D-ANY.4).
