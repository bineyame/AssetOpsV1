# S4-02d phase 2 review (health, install and currentness handoff)

Reviewer: fresh Claude reviewer (did not author the slice), 2026-10-14. Branch
`task/S4-02d-analytic-finding-worker-schedule`, diff `01cc6f50..HEAD` (8cf2d147..b204f786, 10 commits). Judged
against the packet phase-2 row and contract item 4, `D-2026-10-14-s402d-schedule-storage-and-install-gate`
(`.agent/architect-S4-02d-answers.md`), `D-2026-10-14-s402c-late-sequence-and-s5-money`,
`D-2026-10-14-s5-selected-window-overview`, the phase-1 review carries (F1-F3, Q1-Q5, carries 1-6) and the handoff.

## Verdict

**ACCEPT with findings fixed on the branch.** The seam, health report, install gate, F2/F3 and the engine release
are correct. My own I4 race (real stage children, continuous seam polling) found no false CURRENT and no
unresolved lock. One Medium finding needs a small fix round before phase 3. Moving the S3 knowledge cutoff to the
DB clock opens a skew case where a window stays STALE permanently and the health report does not show it (F-A).
F-B (guard misses multi-line and non-text SQL) and the Low items can be carried.

## Findings

### F-A - Medium - DB-clock knowledge cutoff vs app-clock `decided_at`: a window stuck STALE that health does not report (acceptance gap: "Operators can see per-Site backlog")

`backend/assetops_backend/scheduling/stages.py:111` gives the scheduled S3 worker `clock=db_clock(url)`, so the
lease instant, which is also the run's `knowledge_cutoff`
(`postgres_assessment_store.lease_job` returns `JobLease(..., now)`), is now DB time. The evidence query compares
that cutoff with `ingestion_disposition.decided_at` (`postgres_assessment_store.py:54`, `d.decided_at <= :k`). But
`decided_at` is still the ingestion service's application clock (`evidence/ledger_service.py:181`,
`decided_at=self.clock()`). The cutoff and the value it filters now come from two different clocks.

Before this change, the worker and the ingestion API on one host shared a clock. If the ingestion host now runs
ahead of the DB by d, a reading accepted less than d before the lease is excluded from the run. Acceptance widened
an existing PENDING job instead of creating one (`_coalesce_job` only widens a PENDING job, and its
`available_at` stays earlier). The job completes DONE, so nothing is left to recompute. The S3 read (open cutoff)
then reports `INPUT_BASIS_CHANGED`, and `reconcile()` only re-enqueues on model or configuration change. The window
stays STALE until unrelated new evidence arrives.

Reproduced (scratch DB, `kobo` fixture, in-process tick): deliver 10-12 h (job J, past `decided`), then deliver
11-13 h with `decided` = DB now + 75 s (widens J), then tick, wait 90 s for the DB clock to pass every `decided_at`,
then tick twice:

| Worker clock | First read | After the DB clock catches up |
| --- | --- | --- |
| DB (this branch) | `STALE_PROJECTION`, `S3_STALE_PROJECTION` (`INPUT_BASIS_CHANGED`) | still `STALE_PROJECTION`, **0 live jobs, health Site `IDLE`, no alarm** |
| ingestion clock (pre-switch single host, control) | `CURRENT` | `CURRENT` |

The seam fails closed (never CURRENT), so this is not a false-CURRENT defect. It is a permanent non-convergence
that the operator report shows as IDLE, against packet item 3 and the outcome "Operators can see per-Site
backlog". The implementer's skew proof cannot see it: it only moves the tick's clock ahead, and every test delivery
uses a backdated `decided` (2026-10-11/12), so `decided_at` is always far below DB now. Lease expiry, `available_at`
and retry timing on the DB clock are right. Only the cutoff's comparand is on another clock.

Fix on the branch (minimum): (1) make the case visible. In health, add a Site alarm for any assessed window whose
S3 read is `STALE`/`INPUT_BASIS_CHANGED` with no live job (for example `S3_STALE_NO_JOB`, with the window and
selection seq), state FAILED or BACKLOG. Add a test that drives the 75 s scenario above. (2) State the residual in
the runbook and CODE_STATE under I3. Carry to the evidence/ingestion owner in a separate scoped packet, as the
Architect ruling routes ingestion defects: stamp `decided_at` from the database (`clock_timestamp()`), or have
acceptance enqueue a new job when the PENDING job's lease could predate the decision. Until one of those lands, I3
is closed for heartbeat, claims, retry, STOPPED, the seam and the drain, but not for the S3 cutoff against
app-clock acceptance.

### F-B - Low/Medium - rule 8 schedule-writer guard: robust on one line, blind to multi-line statements and non-text SQL (carry)

`tools/checks/configuration-persistence.ps1:680` (`$sqlWrite`) and the schedule block `:776-820` match line by
line. F1's lines are all caught now (phase-1 probes `guard` 20/20 rerun), and so are these fresh one-line variants:
f-string table, `AS` alias, schema-qualified, mixed case, tabs, lowercase CTE delete, `exec_driver_sql` insert into
another table, and a lowercase unlisted-column control. I injected each line below into the schedule writer in a
`git archive` scratch copy and ran `tools/check-architecture.ps1`. Every one **passed (missed)**:

- `("UPDATE site "` / `"SET lifecycle = :l WHERE ..."` split across implicit concatenation. The same miss happens
  for `UPDATE schedule_site_head` / `SET created_at = now()`, and for a lowercase `delete` / `from schedule_cursor`
  split.
- A triple-quoted multi-line `UPDATE site / SET ... / WHERE`. A literal `\n` inside the string also misses.
- SQL comments as whitespace: `UPDATE/**/site/**/SET ...`, `delete/**/from site`.
- `MERGE INTO site ... WHEN MATCHED THEN UPDATE SET ...` (PostgreSQL 16 here).
- SQLAlchemy Core `update(table("site")).values(...)` and `delete(table("schedule_cursor"))`, which contain no SQL
  text.
- Lowercase `copy site from stdin`.

The first class is ordinary formatting for a long statement, not a contrived evasion. Every other writer's rules
share the same line-based weakness, so this is a guard-architecture limit, not a phase-2 regression. Carry: a
statement-level guard (extract Python string literals per call with `ast`, join implicit concatenations, strip SQL
comments, then apply the rules). Also refuse `MERGE`, lowercase `copy`, and SQLAlchemy Core `insert/update/delete`
imports outside the allowed writers. Route it to the guard owner, or fold it into the phase-3 fix round if that is
cheap.

### F-C - Low - systemd `TimeoutStartSec=660` is below the tick lease, and its comment says the opposite

`backend/deploy/schedule/assetops-schedule-tick@.service:15-16`. The comment says "Above the tick's own lease".
`tick_lease_seconds` is 120 + 240 + 360 + 60 = **780 s** (`tick.py:75-76`). 660 s also equals the natural worst-case
wall time (discover 120 + tick 240 + one Site's stage bounds 300) with no room for the store calls between stages,
each of which can take up to a 30 s statement timeout. systemd can therefore SIGTERM a tick that is still inside its
own bounds, and the next starts see `SKIPPED_CLAIMED` until the lease expires. Fix: set `TimeoutStartSec` at or
above `tick_lease_seconds` (for example 840) or correct the comment and the reasoning. Templates are not installed,
so there is no runtime impact today.

### F-D - Low - `tools/schedule-install-gate.py:32` lists F1 twice for `pilot`

`real_pilot_requires` already contains `I-late-reading-series-and-money-limit`, so the CLOSED reason prints it
twice. Cosmetic; deduplicate `needed`.

### Observations (no change requested)

- The seam hard-codes `source_open=True` (`upstream.py:136`). It reports upstream truth only. S5 must apply the S3
  source gate and the F1 money rule itself, as the docstring says.
- `stages.db_clock` builds and disposes one engine per clock call. That is correct and leak-free, but costs a
  connection per call (several per S3 job, one per matcher apply). It is fine at current bounds and is part of the
  measured ~1.3 s S3 stage.
- `release()` is sound: it walks `store`/`_store`/`_prices` and disposes each engine once. An S5 API should hold one
  seam instance rather than build one per request.

## Rulings

### Clock change (focus 2): within the ruling, scoped to scheduled stages; one comparand is wrong (F-A)

The Architect ruling ("S4-02d owns DB-clock resolution of I3 for scheduled work") and phase-1 Q4 ("phase 2's skew
proof must cover the S3 lease/cutoff and matcher `now`, or state the residual") allow the switch.

- **Scope:** `build_dispatch_assessment_worker(url, clock=...)` and `FindingMatcher.now` were already injection
  points, and the change sets them only inside the scheduled stage functions (`stages.py:91, 111, 137`). Defaults
  for every other caller are unchanged: manual `process-jobs`/`match-findings`/`assess`, the API, and the tests that
  inject `Clock(...)`. Reviewed S3/S4 behaviour for other callers does not change.
- **Existing tests:** focused S3/S4 suites pass (below). Determinism is unaffected: the cutoff and revision instants
  were already wall-clock values, and S3 identity (input SHA) does not hash the cutoff.
- **Decisions:** the switch does not contradict the S3 phase-2/3 decision in `.ai/DECISIONS.md`, which says the
  clock-based `knowledge_cutoff` is not a commit-ordered fence and forbids describing arbitrary `knowledge_at` replay
  as reproducible. That decision's assurance, "later acceptance still creates a dirty job and cannot leave a stale
  run marked CURRENT", still holds for "never CURRENT". Under cross-clock skew it no longer holds for "creates a
  dirty job" (F-A).
- **Mixed operation:** the matcher instants and the lease on DB time are coherent with the schedule. A manual
  app-clock `process-jobs` running alongside the tick mixes clocks on `lease_until` and the FAILED-supersession
  comparison (`selected_at > available_at`). The runbook's stop-the-tick rule (Q5) covers that.

### Deviations 1-5: honest and fail-closed (accepted)

1. Schedule-only blockers with a usable result report `STALE_PROJECTION`, stage `SCHEDULE`, with typed reasons.
   Accepted; S5 owns presentation.
2. A never-visited scheduled Site reports STOPPED (`SITE_NOT_OBSERVED`). Accepted. It is noisy for one tick after a
   Site's first delivery, but correct.
3. A consequence read of `PENDING` blocks CURRENT. Accepted: every latest revision gets a head from the drain, so it
   is not a permanent block.
4. Work with null `affected_from/to` blocks every window. Accepted (fails closed).
5. A multi-day window containing a day with no evidence stays `PENDING`. Accepted as fail-closed, with an S5 carry:
   such a window can never become CURRENT, and "PENDING" implies coming work. S5-01 must read `S3_UNASSESSED` in
   `reasons` and present it as a gap, not a wait.

### Q1 / commit-safe comparison / `SELECTION_MOVED_DURING_READ`

CURRENT requires the environment not to be STOPPED **and** an empty `site_observation`: visit freshness, no stale
claim, skips/failures/fence streak below their thresholds, no `MATCH_EVIDENCE_NOT_ACCEPTED`. The comparison uses
`analytic_run_selection.seq` and `finding_match_pass.selection_seq`, read before and after the S3 reads. `seq` is
commit-ordered per Site because `_persist` takes the per-Site `_ASSESS_LOCK` advisory lock before inserting the
selection, so a `max(seq)` comparison cannot be overtaken by an earlier-numbered late commit. No timestamp acts as a
fence. Live S3 jobs come from each day's snapshot over its read range, so the six-hour bracket is included.
`SELECTION_MOVED_DURING_READ` fired live in my race (below). There is no S5 UI, no owner copy, and no frontend
change.

### `SKIPPED_UNCHANGED_FENCE` clearing `fence_moved_streak`: sound, cannot hide a moving fence

S4 skips only when the current fence equals the fence stored at the last `MATCHED` (and the version matches). The
fence's seq, job count and revision count are monotonic; only the job-status marker can revert. A skip therefore
means the Site is back in exactly the fully matched state, so there is nothing left to match, and clearing the alarm
is correct. A fence that keeps moving never equals the stored fence, so S4 keeps running and the streak grows.
Mutation "streak not cleared" is caught.

### `STALE_NO_WORK` scan cost

The health report calls `consequence_read.read` (including `derive`) for every Finding's latest revision of every
inventoried Site on each run, which grows linearly with Findings. That is acceptable for an operator CLI. Carry: a
bounded or cached scan before health runs on a timer or an API. In the seam it is per window (bracketed Findings
only), which is fine.

### Install gate and runbook (focus 5)

`tools/schedule-install-gate.py` reports CLOSED (exit 2) for `demo` (F1 node `open`), CLOSED for `walkthrough` and
`pilot`, and OPEN only for `private`, all observed. The templates are headed DO NOT INSTALL, nothing under `/etc`
or any host was touched, and the repository contains only the templates. The runbook retires the per-Site
consequence timer in the same change and names `CONSEQUENCE_CLAIMED` (Q3). It requires stopping the tick before any
manual Leg B command (Q5) and states `last_started_at` semantics, bounds, identities and stop/restart. The bounds
text matches `TickLimits`. The only error is F-C.

### F2 / F3 non-vacuous

Phase-2 probes rerun: F2 "Site back-off ignored" and F3 "lost claim ignored" are both CAUGHT. The tests assert no
stage ran for the backed-off Site with the cursor advanced, and `CLAIM_LOST` with no S4 or drain after the loss.

### Engine release fix (focus 7)

Sound. See the observation above. The focused run of 85 tests on one DB showed no `too many clients`.

## I4: independent two-chunk race (packet requirement)

Built independently in scratch, not committed. Real `StageRunner` children (killable subprocesses, real
`db_clock`) ran while a poller thread read the seam continuously over a two-day window `[DAY_A, DAY_A+2d)`.
Four rounds each committed two overlapping chunks from concurrent threads, at random 0-4 s delays (seeded) after
the tick started, so they landed in S3, S4 or the drain:

- (9-12 h, 10-13 h) and (14-18 h, 15-17 h): overlapping windows.
- (20 h to 01 h next day, 22 h to 03 h next day): crosses midnight, so jobs span two day windows and both brackets.
- (11-12 h, 11-12 h): identical windows.

Up to six convergence ticks followed. Before each poll I recorded which chunks had committed. For every CURRENT
poll, I checked from the database that each committed chunk's evidence (restricted to what the converged runs
assess) was in the selected runs at that poll's watermark seqs.

Result: 48 polls, 7 CURRENT, 41 non-CURRENT, 0 poll errors, **0 false CURRENT**. Every chunk thread finished, so no
lock was left unresolved, and none raised. The window reached CURRENT with every chunk's evidence in the final runs,
so the moved basis was reprocessed. Reasons observed during the race: `LIVE_JOB`, `S3_PENDING`,
`S3_STALE_PROJECTION`, `S3_UNASSESSED`, `MATCH_PENDING`, `SELECTION_MOVED_DURING_READ`, `CONSEQUENCE_PENDING`,
`WORK_OUTSTANDING`. No ingestion transaction or lock-order defect was observed. **I4 can be closed for the race
proof as specified.** F-A is a clock defect, not an I4 ordering defect.

## Checks as observed

- Focused suites, DB `assetops_s402drev2_test`: `test_s4_schedule_health_postgres`, `test_s4_schedule_tick_postgres`,
  `test_s4_schedule_upstream_unit`, `test_s4_schedule_install_gate`, `test_s3_dispatch_assessment_postgres`,
  `test_s3_dispatch_read_postgres`, `test_s4_evidence_consequence_work_postgres`,
  `test_s4_consequence_recompute_postgres`, `test_s4_evidence_drain_postgres`, `test_s4_finding_store_postgres`:
  **85 passed** in 9 min 46 s.
- `.agent/S4-02d-phase-2-probes.py`: **21/21 CAUGHT**, tree restored. `.agent/S4-02d-phase-1-probes.py guard`:
  **20/20 CAUGHT**, tree restored. Running that script with no argument raises `IndexError`; it needs a probe-set
  argument.
- My guard probes (scratch copy): 8 one-line variants caught, 11 multi-line or non-text forms missed (F-B).
  Baseline architecture check passed.
- My probes (DB `assetops_s402drev2_probe_test`): I4 race passed (above). The clock scenario reproduced F-A, and the
  control did not.
- `tools/check-all.ps1`: **All 9 guards passed.**
- Full backend suite: not rerun. My findings change no code, and the implementer's 2115-passed run after the engine
  fix is unverified by me.
- Frontend: no frontend change in the diff, so the suite, `tsc`, build and layout evidence were not applicable and
  not run.
- Scratch DBs `assetops_s402drev2_test` and `assetops_s402drev2_probe_test` dropped.

## Not verified / residual risk

- Tick cost and `--max-sites` were measured only on the Windows dev host. A demo-host measurement is still needed.
- One-off S3/S4 CLIs stay on the app clock and bypass the Site claim. The runbook covers this.
- F-A's root cause (app-clock `decided_at`) also affects configuration `recorded_at` against the DB-clock
  `reconcile` (`_KNOWN recorded_at <= :k`). That case only delays a backdated-publication re-enqueue by the skew,
  and it self-heals once the DB clock passes.

## Carries for phase 3

1. Fix F-A (health alarm and test, runbook/I3 residual) on the branch. Open a scoped evidence-owner packet for DB-time
   `decided_at` or a re-enqueue on late decisions. I3 stays open for that comparand.
2. F-C service timeout; F-D dedupe (small).
3. F-B statement-level guard (guard owner, or the phase-3 fix round).
4. S5-01: deviation 5 presentation (`S3_UNASSESSED` days), the `source_open` gate and the F1 money rule applied on
   top of the seam, and one seam instance per process.
5. Health `STALE_NO_WORK` scan bound before any automated or API use.
6. I4: race proof passed at this review. Record it in the registry and CODE_STATE when the slice closes.
