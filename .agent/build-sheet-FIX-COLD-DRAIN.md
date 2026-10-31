# Build sheet FIX-COLD-DRAIN: the scheduled tick drives the cold and EV producers

Architect: Claude (default binding, `.ai/ROLE_CONFIG.md` "Architect Is Claude By Default", 2026-10-27). Ruling on
the DEMO-A CO-6 finding (`-demo3/.agent/DEMO-A-packet.md:44-51`, head `5b4713b8c`). Code read at main `0796218fc`.
Branch `task/FIX-COLD-DRAIN-tick`. This is a separate slice that merges before DEMO-A.

## 1. Ruling: (a) product fix, widened to the whole cold/EV producer chain

The gap is wider than the cold money drain. The tick (`tick.py:302-370`) drives mini-grid only (`s3` = `dispatch_v3`,
`mini` = `mini_*`, `consequence` = mini `ConsequenceRecomputeWorker`, `stages.py:186-198`). No runtime path calls the cold/EV assessment builders
(`analytics/composition.py:113-125`; only `test_w203`/`test_w206` and the demo replay) or the cold/EV consequence
builders (`financials/composition.py:83-99`; only `test_w204`/`test_w207`).

Accepted cold/EV evidence enqueues `recompute_job` rows (domains `cold_chain`/`ev_charging`, migrations 0020 and 0025).
Cold/EV FindingRevisions trigger `cold_consequence_work`/`ev_consequence_work`. On a real deployment, and under
`demo_combined.py serve`, none of it is ever worked. Draining cold money alone would still leave every live cold or EV
day unassessed, so the fix wires all four producers.

**(b) rejected.** The live demo loop is `serve`/`tick` (packet: "start `serve` before showing"). A build-step drain shows
a state the running product cannot reach, any cold/EV day added live falls back to pending or stale, and the self-check
would certify a fixture rather than the product.

**Who reads the result** (pending, withheld or missing until the drain runs; no reader changes in this slice):
- Estate Financials `_pending_guard` (cold `withheld` `estate/financials.py:227`, EV `PENDING_RECOMPUTE` `:251`) feeds
  Portfolio `money_pending` (`estate/portfolio.py:72-77`, CO-6); estate coverage consequence rows (`coverage.py:280`).
- Cold Site overview needs-attention `COLD_RECOMPUTE_PENDING`, `consequence_summary` WITHHELD
  (`analytics/cold_site_reads.py:213-239, 398-399, 450`) and the cold Financials page.
- EV: with no drained head the read gives guard `STALE_BASIS` (`ev_site_reads.py:324-331`), so the EV line is silently
  absent, not pending, and the EV board GROW `headline_money` stays null (`site_outcomes/ev.py:184-208`). The cold
  board composer (`site_outcomes/cold.py`) reads no consequence field.

**Register.** No row records the runtime gap. R535 (plan2 `:539`) only says the combined dataset is missing; the demo3
copy of R535 cites the drain as the CO-6 cause. Add a new row (next free ID at merge; R620 if still free; class D3,
structural oversight) for "cold/EV producers not scheduled", resolved by this slice. Leave R535 to DEMO-A.

## 2. Stage order and fencing (no migration)

Per Site, under the existing Site claim, keeping today's markers (the 0030 `stage` CHECK is unchanged):
`S3: s3 → cold_assess → ev_assess` · `MINI` · `OPPORTUNITY` · `S4` · `CONSEQUENCE: consequence → cold_consequence → ev_consequence`

- Fencing: call `stage(<marker>)` again before each new child (`set_stage` re-checks the claim; a lost claim stops the
  Site there, as F3 does). Each child is its own killable process with `PGOPTIONS` timeouts.
- Assessment precedes the drains so the same tick's cold FindingRevisions and trigger-made work exist; the EV drain
  refuses with `PENDING_RECOMPUTE` while an overlapping `ev_charging` job is PENDING/LEASED/FAILED (`ev_recompute.py:3-6`).
- Failures: `failure = failure or (stage_name, code, detail)`, later children still run (MINI/OPPORTUNITY rule). Names
  `COLD_ASSESS`, `EV_ASSESS`, `COLD_CONSEQUENCE`, `EV_CONSEQUENCE`; `last_failure_stage` is free text (`health.py:291`).

## 3. Units (4). Effort 2.0 d

### U1 · Four stage children · 0.5 d · file `scheduling/stages.py`, plus `analytics/composition.py` (two kwargs)
- `cold_assess(url, args)` and `ev_assess(url, args)`:
  - Call `build_cold_assessment_worker(url, clock=db_clock(url), lease=timedelta(seconds=DOMAIN_JOB_LEASE_SECONDS))
    .run_pending(limit, t, s)` (EV the same; constant 300, the workers' own 5 min). Add a `**kw` passthrough
    (`clock`, `lease`) to both builders in `analytics/composition.py`; defaults unchanged.
  - Return `{"code":"OK","processed":n,"failed":#FAILED,"deferred":#PENDING|LEASED,"outcomes":[...],"live_jobs":[...]}`.
    Serialize outcomes as the `s3` stage does (`job_id`, `status`, `runs`, `error`).
  - `deferred` comes from `build_postgres_assessment_store(url).live_jobs(<analytic>, <domain>, t, s)`, with
    `(cold.EXCURSION_ANALYTIC, COLD_DOMAIN)` and `(ev.SESSION_ANALYTIC, EV_DOMAIN)`. Pre-flight: confirm the
    `analytic_run_selection.analytic_id` literal that cold writes. It affects only FAILED-row reporting, not `deferred`.
- `cold_consequence(url, args)` and `ev_consequence(url, args)`:
  - `build_cold_consequence_worker(url).run(t, s, limit, now=datetime.fromisoformat(args["now"]))` (EV the same),
    returning the `consequence` shape: `code` `"OK" if report.claimed else "CONSEQUENCE_CLAIMED"`, `claimed`, `now`,
    `selected`/`appended`/`replayed`/`failed`/`deferred`/`backlog` (computed here; workers unedited, no `counts()`),
    `outcomes` (`work_id`, `succeeded`, `attempt_no`, `error_code`). Register all four in `STAGES` and the docstring.
- Idempotency and retry keep the workers' semantics, nothing added; the tick passes DB `now` as for mini. Assessment:
  job lease, `max_attempts=3`, 30 s backoff, `LeaseLost` reported. Consequence: session advisory Site claim
  (`cold_/ev_consequence_runner:`), per-item xact lock, repeatable read; succeeded work is skipped, a replayed basis
  returns the stored ID, and a failed item appends a typed FAILED attempt and is due again under `retry_due_at`
  (1, 2, 4, 8, 16 min).

### U2 · Tick wiring and limits · 0.5 d · file `scheduling/tick.py`
- `TickLimits`: add `domain_jobs_per_site: int = 10`, `domain_assess_seconds: float = 120`,
  `domain_consequence_seconds: float = 60` (drains reuse `consequence_items_per_site`). Validate
  `0 < domain_assess_seconds < DOMAIN_JOB_LEASE_SECONDS`; add the new fields to the `< 1` and `statement_timeout`
  checks. `site_lease_seconds` adds `2*domain_assess_seconds + 2*domain_consequence_seconds`.
- `_site`: insert the children per §2; module docstring states the new order. Counts are summed into existing head
  columns (no schema change): `record_s3(s3 + cold + ev processed, summed deferred)` once after the three S3 children,
  `record_consequence(summed selected, summed deferred)` after the three drains. A non-OK child adds 0 and sets
  `failure`. Per-domain detail goes in `site.stages["cold_assess"|"ev_assess"|"cold_consequence"|"ev_consequence"]`.
- Out of scope (open register row in U4): selecting an excluded-lifecycle Site whose only work is cold/EV (every
  cold/EV job comes from accepted evidence, so an active Site is already selected by `has_evidence`), and cold/EV
  counts in `health.py`.

### U3 · Tests · 0.75 d
- New `backend/tests/test_fix_cold_drain_stage.py`, fake runner as in `test_w402_mini_stage.py`. T1 exact order
  `s3, cold_assess, ev_assess, mini, opportunity, s4, consequence, cold_consequence, ev_consequence`; T2 limits, lease
  sum, `domain_assess_seconds >= 300` raises; T3 a new child's FAILED/TIMEOUT/`CONSEQUENCE_CLAIMED` is kept as first
  failure with its stage name and later children run; T4 a claim lost before any new child gives `CLAIM_LOST` there;
  T5 summed `record_s3`/`record_consequence` counts.
- New `backend/tests/test_fix_cold_drain_tick_postgres.py`, real runner, `*_test` DB:
  - P1 (cold, required): the `test_w204_cold_consequence` `chain` fixture gives accepted cold evidence, a PENDING
    `cold_chain` job and no run. Tick 1: the job is DONE, every `cold_consequence_work` row of the Site has a SUCCEEDED
    attempt, and the excursion case has at least one `cold_consequence_revision`. The Portfolio read for that window
    then has `money_pending` false and a status other than PENDING. Tick 2: zero new attempts and revisions.
  - P2 (EV): the `test_w207_ev_money_postgres` tariff-window fixture. One tick assesses the `ev_charging` job and then
    drains `ev_consequence_work`; the EV money guard is not `PENDING_RECOMPUTE`/`STALE_BASIS` and a stored head exists.
  - P3 (retry; pre-flight ruling (b), 2026-10-31: item failures stay worker-level, as in the mini drain; the Site
    failure is proven only by T3's fake non-OK code): basis read raises once → tick 1 stage OK, `failed == 1`, one
    FAILED attempt; a tick before `retry_due_at` adds none (`deferred == 1`); once due (move `finished_at` back, test DB only) it succeeds.
  - P4: a mini-only Site's tick result is byte-identical apart from the four new `stages` keys, each a 0-count OK.
- Pre-flight grep: every test/tool running `ScheduleTick` or `tools/*tick*` over cold/EV fixtures that asserts a
  pending/stale cold/EV state or exact head counts goes in the packet first; only literals that follow from the drain
  may change, anything else stop.

### U4 · Records · 0.25 d
Register: new D3 row (§1) resolved, one open row for the U2 out-of-scope pair. `CODE_STATE`: tick order. Packet: tests.

## 4. Tests to run
Per unit: the focused files. Slice end: `python tools/select-tests.py --base main` (picks the full suite: runner and
composition changed). Merge: full backend **`-Tier all`** (fast and slow; scheduling is shared plumbing, ROLE_CONFIG
:465-467), full frontend, check-all. No migration.

## 5. File overlap and merge order
- FIX-COLD-DRAIN touches `scheduling/stages.py`, `scheduling/tick.py`, `analytics/composition.py` and new tests.
  LINK-LINEAGE (`site_outcomes/board.py`, its composition, `main.py` wiring) and COV-PARTIAL (`estate/coverage.py`,
  `index.py`, `portfolio.py`) share **no files** with it.
- The three merge independently, in any order, each re-running its scoped tests on the updated main.
- DEMO-A merges **last**: it rebases on all three, rebuilds and re-derives CO-6's expected tuple (the drain settles
  the cold window, so not PENDING; COV-PARTIAL makes the Kobo week PARTIAL, not UNKNOWN, its sheet line 34), then
  closes R535 against the measured value. Do not weaken the row before the rebuild.
