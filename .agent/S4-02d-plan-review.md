# S4-02d planning packet: fresh Claude review

Reviewer: fresh Claude reviewer. I did not write the packet; the Codex Planner did. Date 2026-10-14.
Worktree `AssetOpsV1-gap-planning`, branch `plan/S4-02c-architect`, HEAD `3e1c40b4`.
Scope: `tasks/S4-02d-analytic-finding-worker-schedule.md` (47 lines), its `tasks/README.md` row, the registry node `I-analytic-finding-worker-schedule`, `.agent/planner-S4-02d-brief.md` and `.agent/planner-S4-02d-notes.md`.
Judged against: `.agent/architect-S4-02c-answers.md` R1, `D-2026-10-14-s402c-late-sequence-and-s5-money`, `D-2026-10-14-s5-selected-window-overview`, the S3 projection-status decisions (`.ai/DECISIONS.md` :4013, :4049, :4053), backlog carries W1-W5 ("S4-02c Architect closeout review carries") and I1/I2 ("S4-02c carries"), and the built code.

## Verdict: RETURN for a short Planner amendment

The scope, size and authority are right. It is a non-UI S4 follow-on that owns exactly the R1 node. F1 is kept out. I1 and I2 are carried. The "no queue-empty shortcut" and "stopped worker cannot certify CURRENT" principles are stated. Registry, README and next-work are consistent. `USER_REVIEW_REQUIRED: false` is justified.

It is not implementation-ready, for two reasons:

1. **The S4 gate in item 1 conflicts with the built S3 job model (H1).** A terminally FAILED S3 job stays live until a later selection covers its window, and nothing re-enqueues it. So "defer that Site's S4 while S3 is ... failed" freezes every Finding on the Site permanently. Every listed proof still passes.
2. **Phase 3 cannot pass as written (H2).** Once the late mean is released, a tick-only drive runs S3, then S4, then the consequence drain in one tick. r1's `EVIDENCE_ACCEPTED` work then no-ops as `FINDING_REVISION_SUPERSEDED`. The "retained" same-revision `POWER_NOT_IN_ASSESSMENT_INPUTS` consequence is never produced.

The Medium findings are omissions an implementer would otherwise decide under pressure: storage/migration and the rule 8 guard amendment, the active-Site predicate, the fate of the S4-02c timer, `NO_WORK_RECORDED` heads, and the F1 assertion in phase 3. Each fix is a Planner text edit. None needs the owner, and none needs a new Architect ruling.

## Checks run (by me)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0 ("Registry valid: 224 nodes, 11 linked pilot panels").
- `... --verify-report .agent/next-work-2026-10-14j.json`: exit 0. Decision `select` `I-analytic-finding-worker-schedule` 2.198 vs `I-action-store` 2.016, gap 8.28%, tie-break notice. The report is tracked in `3e1c40b4`.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed. `git diff --check HEAD~1 HEAD`: clean.
- Registry: the node's `task` is `S4-02d`, and `requires` is `I-S3-01`, `I-S4-01`, `I-evidence-acceptance-consequence-work`. It is in `queue_baseline_nodes`. `I-site-overview-read.requires` includes both this node and `I-late-reading-series-and-money-limit`. README row :31 matches.
- W5: the 8.28% notice is recorded in main's `.agent/coordinator-handoff.md` (UPDATE 26). It is not in this worktree's copy, which is expected.
- No backend or frontend suites were run (planning-only change).

## Anchor spot-checks (built code)

- `assess_dispatch.py`: `process-jobs` calls `worker.run_pending()` (default `limit=1000`, `reconcile_all()` first). `match-findings` is one explicit tenant/Site. The packet's description is accurate.
- `assessment_worker.py` / `postgres_assessment_store.py`:
  - `lease_job` is **global per domain**: `ORDER BY available_at, created_at ... FOR UPDATE SKIP LOCKED`, with no Site filter. The lease is 5 min. `max_attempts=3`, then the job is `FAILED`. An expired lease on its last attempt also becomes FAILED (:196-201).
  - `_LIVE_JOBS` (:88-91) keeps a FAILED job live until a later DEFAULT selection covers its window. `reconcile` re-enqueues only on a model-version or configuration change, so **nothing re-enqueues a FAILED job**. Only new accepted evidence in that window does.
  - `assessed_sites` = DISTINCT Sites in `analytic_run_selection`.
- `finding_episode.py:12-14`: "A window that is STALE, FAILED, PENDING or unassessed never creates, extends or closes an episode." The matcher is already window-safe when S3 work is outstanding.
- `postgres_finding_store.py`:
  - `apply` takes `pg_advisory_xact_lock('finding:'||site)` and writes `finding_match_pass(selection_seq, matcher_version)` on every pass, including zero-write passes (Q18).
  - `match_state` (:400-415) already computes `matched_through_selection_seq` against a window's `max(seq)` for the current `MATCHER_VERSION`. That is an exact, durable S4 backlog watermark.
  - `_fence` includes `count(*)` and the `string_agg(status)` of the Site's `recompute_job` rows. Any S3 lease or ingestion enqueue on the Site during a match moves the fence. After 3 attempts the matcher raises.
- `recompute.py` / `recompute_consequences.py`:
  - The Site claim is a session `pg_try_advisory_lock` on a dedicated connection. It is released on crash, but held indefinitely by a hung process.
  - Retry is 1/2/4/8/16 min with no cap.
  - The CLI refuses any tenant other than `demo` (exit 2) and serves one named Site.
  - The README-db runbook (:88-112) installs **one external timer per Site** for this CLI.
- `site` table (0001): `lifecycle` is free text. Values are `PLANNED|COMMISSIONED|ACTIVE|DECOMMISSIONED|ARCHIVED` (`sites/models.py:543`). New Sites start `PLANNED`, and every fixture Site, including KOBO-001, is `PLANNED`. There is no lifecycle-mutation path.
- `tools/checks/configuration-persistence.ps1` rule 8 (:583-750) has a closed list of seven PG writer modules, each with its own tables. A database driver imported anywhere else fails the guard (:739-743).
- `tools/s402c_late_power_walkthrough.py`: step 1 and Leg B call `process-jobs`/`match-findings` as CLIs (:222, :292-296). The source-ordered variant (`SOURCE_ORDER` renumbering, :112-137) exists.

## Findings

### H1 (High, contract defect): the Site-wide "defer S4 while S3 is due/leased/failed" gate freezes a Site on any terminal S3 failure, and is unnecessary for correctness

Packet :19 says: "S4 matching runs only after S3 work relevant to that Site has reached a completed basis; if S3 remains due, leased, failed or deferred, record it as pending and defer that Site's S4/currentness promotion."

- **Failed.** A job that exhausts `max_attempts`, or whose lease expires on its last attempt, is FAILED. It stays live (`_LIVE_JOBS`) until a later DEFAULT selection covers its window, and `reconcile` never re-enqueues it. One deterministic failure on one UTC day therefore stops S4 for **every** window of that Site indefinitely. Late evidence on unrelated days never reaches a revised Finding. That defeats the slice's Outcome, and the packet names no recovery command (none exists: `assess` writes an EXPLICIT cohort-suffixed run, not the default selection).
- **Due.** The gate is checked after a bounded S3 drain. On a Site whose arrivals outpace its per-tick S3 share, or behind other Sites' older jobs in the global FIFO, S4 is deferred tick after tick.
- **Not needed.** The matcher already ignores non-CURRENT windows per window (`finding_episode.py:12-14`) and replans idempotently from the selection basis. Running S4 every tick after the S3 stage is safe.

**Why it matters:** the implementer would build exactly this. The phase-1 proof "no S4 promotion ahead of due/leased/failed S3 work" would pass, the phase-2 "failed S3 job" proof would show "deferred" as intended, and production would freeze silently except for an alarm.

**Fix (Planner):** separate S4 *execution* from *currentness*.
- (a) Run `match` for every selected Site every tick after its S3 stage. The matcher's CURRENT-window rule is the correctness gate.
- (b) Make the currentness gate window-scoped. A selected window is not CURRENT while a live S3 job intersects it (with its continuity bracket), its `match_state.matched` is false, or relevant consequence work is outstanding. This is what item 4 already needs.
- (c) A terminal FAILED S3 job is a `FAILED` stage state with job ID and `last_error`, and an alarm. Specify an operator recovery that re-enqueues the window through the existing `AssessmentStore.enqueue` (for example an `assess_dispatch requeue --tenant-id --site-id --start --end` command, an INSERT/UPDATE already allowed to the assessment writer) and document it in README-db.
- (d) Replace the phase-1 proof with "S4 runs but does not change episodes over a due/leased/failed window; that window's currentness is not CURRENT; other windows' Findings still advance."

### H2 (High, acceptance gap): phase 3's retained Leg A cannot be produced by a tick-only drive

Packet :38: "Retain Leg A exact accepted ID, stale queued work, same-revision `POWER_NOT_IN_ASSESSMENT_INPUTS` and history. Release the withheld GOOD mean, then drive only the configured schedule/ticks."

After the release, the first tick runs S3, which assesses the late mean into a new run. S4 then appends r2. The consequence drain then takes r1's `EVIDENCE_ACCEPTED` work (enqueued first, so first by `eligible_since`), finds r1 no longer the highest revision, and records the typed no-op `FINDING_REVISION_SUPERSEDED` (`recompute.py` header). The same-revision consequence 2 with `POWER_NOT_IN_ASSESSMENT_INPUTS` never exists.

The only ways to "retain" it are a manual consequence drain before the first tick, which the sentence appears to forbid, or a stage-limited tick, which the packet does not define. The pre-tick `STALE/TECHNICAL_INPUT_CHANGED` + work-ID read *is* achievable.

**Fix (Planner), pick one and state it:**
- (i) Leg A is replayed exactly as in S4-02c, using the consequence stage only. This is either the S4-02c runner or a documented `--stages consequence` tick, and it is not a Leg B command. Then Leg B is driven only by full ticks.
- (ii) Under the automatic schedule Leg A is transient. Assert the pre-tick STALE/queued read, then after one tick the `FINDING_REVISION_SUPERSEDED` no-op on r1's work plus r2's `CURRENT/PRICED` chain. Cite the S4-02c evidence for the same-revision state.

Either way, also say whether step 1 (the first delivery before Leg A) is tick-driven. A tick-driven step 1 is recommended, so the artifact contains no `process-jobs`/`match-findings` invocation at all and W4 is shown by a grep of the recorded commands.

### M1 (Medium): new durable state needs a migration and a rule 8 guard amendment, and the packet does not say so

Items 1-3 require a durable tick/Site claim, a durable cursor for fairness, and a schedule record with last tick start, last success/failure, retry due, claim age and heartbeat. A heartbeat, a last failure and a STOPPED threshold cannot be derived from existing tables, so this is a new migration (0013).

Rule 8 permits exactly seven PG writer modules with fixed tables, and fails any database driver import outside them. A new orchestrator/schedule store therefore either becomes an eighth writer or extends an existing writer's table list.

The S4-02c plan review (H3) already showed the cost of leaving a guard collision unstated: the implementer either edits a boundary rule nobody chose or contorts the design.

**Fix:** name the migration, its tables and their append-only or mutable discipline. A mutable schedule head is reasonable. If an attempt history is kept, state its retention, given I1 volume. Name the new writer module and the rule 8 amendment as in-scope, reviewer-checked guard edits, mirroring the S4-02a/b comments in the guard. Put the storage in phase 1 so phase 2 does not add a second migration for the same record.

### M2 (Medium): the "active tenant/Site" predicate is left open, and the obvious reading excludes every built Site

Packet :19 says "Define and test the exact active predicate" and "newly activated Site". `site.lifecycle` exists, but every fixture Site, including KOBO-001 (the walkthrough Site), is `PLANNED`, and new Sites start `PLANNED`. No activation transition exists. A natural `lifecycle = 'ACTIVE'` would make the schedule process nothing and fail phase 3.

Separately, `lease_job` is global, so S3 jobs of an "inactive" Site would still be leased unless the S3 drain is made Site-scoped.

**Fix:** state the predicate. For example: an imported Site (`site_import` row) whose lifecycle is not `DECOMMISSIONED`/`ARCHIVED`, plus any Site that holds live `recompute_job` or pending consequence work, so outstanding work is never orphaned. Say "newly activated" means "newly imported" in the proof. State whether the S3 stage uses a Site-filtered lease (allowed: an `UPDATE recompute_job SET status` already matches rule 8's `$assessUpdates`) or stays global-bounded with fairness argued by `available_at`. Say what happens to work of an excluded Site: it is reported, not silently dropped.

### M3 (Medium, carry W1): the existing S4-02c per-Site consequence timer and per-environment ownership are not settled

W1 asks for per-environment ownership and cadence, and whether to fold the consequence runner in or keep it separate. The packet folds the drain into the tick (:13) but does not say what happens to the per-Site timer that README-db :88-101 tells operators to install.

If both run, the tick's consequence stage regularly finds the Site claim held and reports skipped. That trips the "repeated Site-claim skips" alarm (I2) falsely, or trains operators to ignore it. "Deployment-owned" also does not name the environments: local development host, demo host, isolated walkthrough database, and the real-Site pilot (gated).

**Fix:** state that installing the schedule retires the per-Site consequence timer, and update README-db accordingly, keeping the CLI for one-off operator use. Alternatively, define how the tick treats a claim held by the legacy runner. Add a short per-environment table: owner, timer identity and credential, cadence, or "not installed" with its reason. The real-Site pilot row says gated by `real_pilot_requires`.

### M4 (Medium, carry W2): pre-0012 `NO_WORK_RECORDED` consequence heads are not covered

W2 lists "I1 retry volume / hung-runner alarm / `NO_WORK_RECORDED` heads". The packet carries the first two only. A stale head with no work row is invisible to any work-based backlog count. The Site report would then read "healthy idle" while a Finding's consequence is stale, which is exactly the queue-empty shortcut the packet forbids for S5.

**Fix:** count such heads in the consequence backlog as a distinct `STALE_NO_WORK` category with Finding/revision IDs. They must keep a window from CURRENT. Either name an operator backfill (if any is in scope) or state that they are reported, not repaired, in this slice.

### M5 (Medium): phase 3 asks it to "assert no S5 amount" under F1, but the F1 money gate is not built by this or any earlier slice

Packet :38: "If run-1 admission numbering triggers F1 ambiguity, assert no S5 amount and use the existing source-ordered variant for the positive amount path." The only S5 gate this slice exposes is upstream currentness (item 4). The generator-series withholding rule belongs to `I-late-reading-series-and-money-limit` and S5-01.

An implementer must either build part of F1, which is out of scope, or assert something the seam cannot express. Run 1 would actually pass this slice's currentness gate once upstream work completes.

**Fix:** under F1 ambiguity, phase 3 *records* the S3 status/limits (`SEQUENCE_ORDER_INVERTED`/`GENERATOR_SERIES_AMBIGUOUS`) and states that money eligibility belongs to the F1 node. It asserts only that the currentness seam reports the true upstream state. The positive CURRENT path uses the source-ordered variant, which exists (`s402c_late_power_walkthrough.py:112-137`).

### L1 (Low): the S5 seam should name its authority and reuse the built derivations

- Item 4's "healthy observed pass after the accepted-source watermark" is a time comparison. `.ai/DECISIONS.md` :4049 rules that the clock-based cutoff is not a commit-ordered acceptance fence. Acceptance transactionally creates or widens an S3 job, so the commit-safe signal is the live-job / selection-seq / `match_state` / pending-work comparison. The heartbeat is an additional requirement, never the proof. Say so.
- Name the watermark column, and compare against DB time (`clock_timestamp()`), not app time (I3 clock skew).
- Anchor the existing pieces so they are not rebuilt:
  - the S3 window read status (`UNASSESSED|PENDING|CURRENT|STALE_PROJECTION|FAILED` per :4013/:4053);
  - `PostgresFindingStore.match_state` / `finding_match_pass` for the S4 backlog (item 3's "durable dirty basis/watermark" already exists);
  - `ConsequenceStore.pending_work` with attempt counts.
- Define the seam's shape: a Python port/read in the backend, its input `(tenant_id, site_id, half-open window)` and its output fields. S5-01 can then consume it without re-planning.

### L2 (Low): the timeout mechanism is unstated

"Bound wall time per tick and per Site, including a hung `match-findings`/database call" (:20). The stores run in-process, and Python cannot interrupt a blocked driver call except through server-side `statement_timeout`/`lock_timeout`. A Python-side hang needs a child process with a hard kill.

Leave the choice to the implementer, but require the proof to inject both a DB-side stall (for example `pg_sleep` or a held lock) and a stage that does not return. Each is reported as a typed `TIMEOUT` with its work left retryable. Also state the relationship to the 5-minute S3 lease: a per-Site S3 bound shorter than the lease, or an explicit argument why a killed job's lease expiry is acceptable.

### L3 (Low): the S4 fence can be moved by the scheduler's own S3 stage or by ingestion

`_fence` includes the Site's `recompute_job` statuses. If the orchestrator overlaps S3 leasing for a Site with that Site's match (parallel Site workers, or another host's tick), the matcher can exhaust its 3 attempts and raise. Require that a Site's S3 and S4 stages do not overlap under the per-Site claim. Report `FindingFenceMoved` as a typed retryable S4 failure (`FENCE_MOVED`), not as a generic matcher error. The `string_agg` over all of a Site's jobs also grows without bound; note it with the reconcile cost risk.

### L4 (Low): phase sizing

Phase 1 carries the orchestrator, the Site predicate, Site-scoped S3 drain, cross-host claim, cursor, timeouts, timer configuration and eight proofs. With M1's migration and guard edit it is the heaviest phase, but plausibly under ~120k. Suggest moving "installable timer configuration" and the README-db runbook to phase 2, next to the health report, so phase 1 is orchestration plus storage. Each proof as listed is non-vacuous provided H1(d) replaces the S4-deferral proof.

## USER_REVIEW_REQUIRED

False is justified. The output is an operator CLI/report, a backend read seam and runbook text. No owner-facing copy, panel or visual state changes. The packet correctly reopens the flag if any of those change, and keeps S5-01's owner checkpoint.

One behavioural note for the coordinator, not a gate: once installed, existing Finding and consequence screens update automatically after late evidence, using already-reviewed copy (`STALE_QUEUED` and so on).

## Residual risks the packet does not name

- The run-1 7.5625 USD consequence on the S4-02b Finding money panel becomes reachable *automatically* once the schedule runs (the backlog residual). This slice makes that path hands-free before F1 lands. The coordinator should not install the schedule on a demo host that is shown to the owner before the F1 node, or should accept the residual knowingly.
- `reconcile_all()` is unbounded and global per tick (named), and `assessed_sites` omits never-assessed Sites. The Site predicate (M2) should state that reconcile covers every Site the predicate selects.
- I3/I4 from S4-02c (clock skew, concurrent ingestion chunks) are still unowned. I3 now also affects heartbeat/STOPPED thresholds (see L1).

## Implementer carries (if accepted after amendment)

1. Record actual job/run/selection-seq/match-pass/work/attempt IDs and watermarks in every proof. Never use illustrative values.
2. The report must distinguish skipped-because-claimed from processed-zero-work. Only the latter advances the heartbeat.
3. Keep the S4-02c CLI working for one-off use. Its dev-tenant refusal stays. The orchestrator calls the worker by IDs, not the CLI.
4. Run `check-architecture` after the rule 8 amendment and quote the new guard comment in the packet.
