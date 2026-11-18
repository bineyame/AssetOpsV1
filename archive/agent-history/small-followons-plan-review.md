# Plan review - small follow-ons S4-06, S4-07, OPS-02

Reviewer: fresh independent Claude reviewer (did not author the packets). Branch `plan/small-followons`, HEAD
`7c01f46b`, base main `5a37c8ce`. Plan review only: no code, no test suites run. Brief
`.agent/planner-small-followons-brief.md`; work order `.agent/architect-autonomy-2026-10-15-answers.md` items 5-7.

## Verdicts

| Packet | Verdict | Blocking |
| --- | --- | --- |
| `tasks/S4-06-price-succession.md` | **ACCEPT** (Lows carried) | none |
| `tasks/S4-07-evidence-decided-at.md` | **RETURN** | M1 |
| `tasks/OPS-02-writer-guard-ast.md` | **ACCEPT** (Lows carried) | none |

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0, "Registry valid: 228 nodes".
- `... check_v69_dependency_registry.cjs --next-work`: exit 0, status `ranked`, no refusals or `queue_mismatch`; the
  three new README rows parse (gate queue by link filename; first-column labels match the S4-02c/d precedent, and
  `I-price-equal-start-succession` is a persistence node, so the S-task row count is unaffected). Decision line is
  the existing LR-01 / Action store contest, unchanged by these packets.
- Code reality read on main for every cited path (below).

## S4-06 - equal-start future price succession: ACCEPT

Code reality (all hold on main):
- `financials/assumptions.py:189-217` `plan_assignments`; line 211 `not only.valid_from < valid_from` is exactly what
  refuses equality today, and line 216 always inserts the left remainder. Packet's `193-217` is the body; correct.
- `financials/adapters/postgres_assumption_store.py:99-174` `publish`: SYSTEM check, Site/key advisory xact lock,
  idempotency before expected prior, DB `clock_timestamp()` after the lock, `recorded_to` close with rowcount check,
  inserts. `snapshot` at `:195-222`. Correct.
- Rule 8 `tools/checks/configuration-persistence.ps1:641-645` (assumption writer/tables/update regex) and the per-writer
  test in the 680-757 loop. Correct; no new write form is needed (close + insert are both already allowed).
- Migration 0010 CHECK `valid_from < valid_to` on assignments (why a zero-length left row would be refused, not just
  undesirable) and the close trigger (`recorded_to` later than the series' latest `recorded_from`) are compatible with
  the existing close-then-insert at one `at`.
- Migration 0011 `financial_consequence_dirty_on_assumption` dirties `[valid_from, NULL)` for any SUCCESSION, so the
  replacement enqueues consequence work with no change. No test on main asserts equality is refused.

Coverage: registry acceptance (close tenure, insert only replacement, no empty interval, prior cutoff history,
idempotent retry, stale/concurrent prior refusal) and Q1 (`valid_from >= recorded_at`, one open-ended overlap,
409 on >1/bounded/stale) are all in Build 1-3. Concurrency is the existing advisory lock + head check; the race test
is specified. USER_REVIEW_REQUIRED false is justified (no copy or visual change; existing history read shows it).
Size S is honest.

Lows (carry, non-blocking):
- L1: Build 3 "unchanged earlier-price consequence selection when its window does not cross the new start" needs a
  series with an earlier price (e.g. INITIAL open-ended P0, SUCCESSION A at T, then equal-start B at T), but Build 2's
  scenario is a lone INITIAL future price. Name the second scenario so the implementer does not drop that check.
- L2: also cover equal-start on an open-ended *remainder* row (one whose `revision_id` differs from the series head,
  e.g. the tail left by a bounded CORRECTION): the expected prior is the head, the replaced assignment cites an older
  revision. The planner change handles it; one assertion proves it.

## S4-07 - evidence decision time at the scheduled cutoff: RETURN

Code reality (holds on main): `evidence/ledger_service.py:181` `decided_at=self.clock()` (and `:99`
`received_at = self.clock()`); `postgres_evidence_ledger.py:249-306` `decide_chunk`, `_coalesce_job` at `:376-404`
(widens only a PENDING overlapping job `FOR UPDATE`, else inserts one with `available_at = created_at = decided_at`);
`postgres_assessment_store.py:54` `d.decided_at <= :k`; `lease_job` `:192-222` uses `FOR UPDATE SKIP LOCKED` and DB
`now`; `README-db.md:128-135` I3 residual and `:204` `S3_STALE_NO_JOB`; F-A test
`tests/test_s4_schedule_health_postgres.py:385-424`. Rule 8: `recompute_job` is already in `$ledgerTables`
(`configuration-persistence.ps1:624-625`), so evidence-owned re-enqueue needs no ownership change; the packet correctly
forbids schedule-table writes.

### M1 - Medium - the mechanism, and with it the size and the proof path, is not decided

The packet leaves the mechanism open ("stamp ... at DB time ... or durably enqueue an additional job") and its
Architect question is conditional on a case it does not resolve. What it does not address is that `decided_at` is the
**injected test clock** across the deterministic real-Postgres fixtures:
- `BatchIngestionService(PostgresEvidenceLedger(URL), Clock(decided_at))` in `test_s3_dispatch_assessment_postgres.py:62`,
  `test_s4_finding_store_postgres.py:118` (the stepped `runner.tick(step["decided"])` used by the S4 Finding read,
  consequence store and evidence-history suites, with `decided` values such as `2026-10-30/31`, i.e. after today's DB
  time), `test_s4_schedule_health_postgres.py` (`decided="2026-10-12..."`), `test_s2_site_evidence_postgres.py:276`
  (asserts the exact `decided_at`), and workers paired with `Clock(...)` cutoffs.
- If the ledger stamps `clock_timestamp()` unconditionally, every scenario whose worker cutoff is an injected past
  instant excludes all evidence, and future-dated `decided` steps lose their ordering. That is a cross-suite rewrite,
  not an S slice.
- If instead the injected clock is kept as an override and only the production composition (`main.py:267`, no clock)
  stamps DB time, then the existing fixtures exercise a path production does not use, Build 2's "deliberately fast
  and slow app clock" has no effect on the fixed path, and the existing F-A alarm test (which injects
  `decided = db_now + 20 s`) keeps passing only through the override. The packet must say which path the race and
  restart proofs use and how the alarm stays tested.
- `_coalesce_job` sets `available_at`/`created_at` from the same `decided_at`; with an app clock ahead, a newly
  inserted job is not leasable until DB time passes it (`available_at <= :now`). The packet does not say whether those
  move to DB time too.

Why it matters: the brief asked whether the conditional mechanism is decided enough to build. It is not: the
implementer would have to choose a test-clock contract with cross-suite consequences, and the choice changes the
size and what the acceptance proof actually proves.

Fix (Planner fix round; an Architect ruling only if the Planner keeps an injectable `decided_at` in production):
1. Decide the mechanism. Reviewer note for that decision (to be proved in build, not adopted): with `decided_at`
   from `clock_timestamp()` inside the chunk transaction, the existing coalesce appears sufficient. If the coalesce
   `SELECT ... FOR UPDATE` widens a PENDING job, `lease_job`'s `SKIP LOCKED` cannot take that job until the
   ingestion commit, so its DB cutoff is later than the decision and the row is visible. If the worker leased first,
   the coalesce sees LEASED (after EvalPlanQual if it was blocked) and inserts a new PENDING job. If that holds, the
   packet's Architect question is moot, and "DB-time stamp, existing coalesce, no new job path" can be stated as the
   design with the race test as its proof.
2. State the clock contract: for example, the ledger takes `decided_at` (and job `available_at`/`created_at`) from
   the DB inside the transaction, with an explicit, named test-only override for deterministic fixtures. Say that the
   race/restart proofs run on the production (DB) path, list the suites that keep the override, and replace the
   F-A alarm test's driver with the override (the alarm stays as defense in depth).
3. Re-size against that: either confirm S with the override, or split if fixtures must migrate.

Lows (carry):
- L1: state whether `ingestion_batch.received_at`/`completed_at` stay on the app clock ("preserve receipt times" reads
  as yes); the receipt API exposes both.
- L2: the I3 residual also mentions configuration `recorded_at` vs `reconcile` (phase-2 review residual risk).
  Packet should state it stays out of scope (it self-heals) so the closeout does not over-claim.

## OPS-02 - statement-level product writer guard: ACCEPT

Code reality (holds on main): rule 8 at `configuration-persistence.ps1:615-825` with eight `$pgWriters` (`:678`),
line-based `$sqlWrite`/`$sqlTarget` (`:680-681`), schedule block `:776-820` with the "one line" UPDATE requirement;
`backend/tests/conftest.py:103-116`; `backend/tests/pg_harness.py:88-108` returns None for `TEMPLATE_SWITCH == "0"`;
backlog L1 at `.ai/MILESTONE_REVIEW_BACKLOG.md:2239`. The 11 forms in the packet match F-B
(`.agent/S4-02d-phase-2-review.md:59-82`): 3 split-literal + triple-quoted + `\n` escape + 2 comment-separated + MERGE +
Core update + Core delete + lowercase COPY = 11. They live only in the review prose (the phase-2 probes file holds
the implementer's 21 caught probes), and the packet requires them to be recorded as automated probes. No dynamic
write target exists on main (only `f"SELECT ..."` reads at `postgres_assumption_store.py:209`,
`postgres_consequence_store.py:410`), so fail-closed on unresolved writes should not false-positive on main.
Fail-closed, every boundary preserved, non-vacuity, reverse cross-writer checks and L1 are all specified;
USER_REVIEW_REQUIRED false is justified; size S plausible.

Lows (carry):
- L1: `tools/check-architecture.ps1` and `checks/*.ps1` do not invoke Python today (only `check-all.ps1` resolves
  `.venv`). The packet should require interpreter resolution consistent with `check-all.ps1 -Python` and a hard
  failure, not a skip, when the extractor cannot run. Otherwise a missing interpreter silently passes rule 8.
- L2: name where the 11-form mutation corpus lives (for example a committed probe script beside
  `.agent/S4-02d-phase-2-probes.py`, or a test under `tools/`) so the reviewer can rerun it.
- L3: LR-01 (unmerged) adds `source_clock_attestation` to `$assessTables` in rule 8. Whichever lands second must
  carry that policy line into the new guard's tables; state it with the migration re-chaining note.
- L4: the full real-Postgres suite is warranted only by the L1 conftest change. If L1 is deferred, a guard-only
  change could cite `check-all.ps1` plus the corpus instead. That is a preference, not a gap.

## Residual risk not named in the packets

- S4-07: after the fix, a manual app-clock `process-jobs` running alongside the tick still mixes clocks (the runbook's
  stop-the-tick rule covers it). The packet should not claim I3 closed for manual CLIs.
