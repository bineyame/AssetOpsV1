# S4-02c planning packet: fresh Claude review

Reviewer: fresh Claude reviewer. The Codex Planner wrote the packet; I did not. Date 2026-10-14.
Branch `plan/A-S5-overview` in worktree `AssetOpsV1-gap-planning`. The packet commit is `3fe91819`. HEAD moved to `9037baac` (owner autonomy window closed, `.agent/` only) during the review, and nothing in this review depends on that commit.
Scope: `tasks/S4-02c-evidence-consequence-work.md` (38 lines), its `tasks/README.md` row, the registry edits in `3fe91819`, `.agent/planner-S4-02c-brief.md` and `.agent/planner-S4-02c-notes.md`. Judged against `.agent/architect-S4-02-batch-answers.md` Q2, `.agent/architect-contest-2026-10-14d-answers.md`, `D-2026-10-13-s4-bounded-financial-basis`, `D-2026-10-14-s402-post-review-follow-ons`, `D-2026-10-14-s5-selected-window-overview`, the backlog carries "S4-02b carries" (Q6) and "A-S5-overview review carries" P7, and the built code.

## Verdict: RETURN for a short Planner amendment

The scope and authority are right. It is a separate M-size, non-UI S4-02 follow-on. The FindingRevision-insert trigger is kept (P7). "Queued" requires a real work row (P7). It owns a run plan (Q6) and an independent review. The registry, README and next-work report are consistent, and `USER_REVIEW_REQUIRED: false` is justified (see below).

The packet is not implementation-ready, for three reasons:

1. **The phase 3 walkthrough cannot pass.** Under the reviewed `fuel-cost-1` contract, a late accepted reading on an *unchanged* FindingRevision can never produce a `CURRENT`/`PRICED` consequence (H1).
2. **The migration it describes breaks FindingRevision insertion** unless an existing unique constraint and the 0011 trigger's `ON CONFLICT` target are changed. The packet says neither (H2).
3. **Where it puts the enqueue conflicts with architecture guard rule 8** (H3). The claim, lease and backoff mechanism collides in the same way with the append-only work tables (M1).

Each fix is a text edit by the Planner. None needs the owner. H1 can be settled from the existing Architect Q2 text, which asks for a "new version" walkthrough, not a priced result on the same FindingRevision. One optional Architect question is named under residual risks.

## Checks run (by me)

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0.
- `... --verify-report .agent/next-work-2026-10-14f.json`: exit 0. Decision `stop_owner`, `I-evidence-acceptance-consequence-work` 2.020 vs `I-action-store` 2.016, gap 0.20%. The Architect already chose this item under the owner's delegation (`architect-contest-2026-10-14d-answers.md`). The report is tracked in `3fe91819`; the notes call it "generated/ignored", but the coordinator committed it, which is fine.
- `tools/check-agent-workflow.ps1`: passed. `tools/check-architecture.ps1`: passed. No product code changed.
- Registry: node `task` = `S4-02c`; it is in `queue_baseline_nodes`. `mini:1#a`..`mini:4#a` `technical_requires` now include `I-evidence-acceptance-consequence-work` (A-S5-overview review L3 fixed), and `mini:2#a`/`mini:3#a` include `D-site-finding-index-rows`.
- I did not run backend or frontend suites (planning-only change).

## Anchor spot-checks

- `postgres_evidence_ledger.py`: **there is no `process_batch`.** The acceptance transaction is `decide_chunk` (:242). It runs one `engine.begin()` per chunk, calling `_persist` (:309, which returns `ACCEPTED` only when `ON CONFLICT ... DO NOTHING RETURNING id` inserts), the disposition insert, the batch counter update and `_coalesce_job` (:376). `accepted_evidence.role` is `decision.binding.role`, which is server-bound, so "server-bound role" is implementable. See L1.
- `0011_financial_consequences.py`: `financial_consequence_work` and `financial_consequence_work_attempt` are append-only (`ledger_append_only` triggers). Work has `UNIQUE (finding_revision_id)` and `UNIQUE (assumption_revision_id)`. Both 0011 triggers use `ON CONFLICT (<col>) DO NOTHING`. Attempt `outcome IN ('SUCCEEDED','FAILED')` has a one-success partial unique index.
- `recompute.py`: `targets()` handles `FINDING_REVISION_APPENDED`, and **every other cause** falls through to `latest_revisions_overlapping` (an `else`). `run_pending` processes each pending item once per run, so there is no hot loop today. Nothing is persisted for backoff.
- `postgres_consequence_store.py`: `append` uses a per-FindingRevision advisory lock plus a basis-digest replay, which is sound for concurrent and crash-retry appends. In `chain()`, the pending-work SQL matches only `FINDING_REVISION_APPENDED` (by `finding_id`) and `ASSUMPTION_PUBLISHED` (by overlap). `latest_revisions_overlapping` uses `max(revision_no)`, with no eligibility filter.
- `finding_api.py:327-363`: the reviewed owner-facing copy already has `STALE` ("has not been recalculated yet") and `STALE_QUEUED` ("a recalculation is queued"), chosen by `bool(currentness["pending_work"])`. `FindingConsequence.tsx:394` renders that `reason`. `POWER_NOT_IN_ASSESSMENT_INPUTS` and `POWER_OVERLAP_CONFLICT` have reviewed words (`FindingConsequence.tsx:45,48`).
- `fuel_cost.quantify` (:284-353): a GOOD reading in Candidate time that is not in a cited run's accepted input set returns `QUANTITY_UNAVAILABLE / POWER_NOT_IN_ASSESSMENT_INPUTS`. Overlapping good readings return `POWER_OVERLAP_CONFLICT`. `technical_input_sha256` includes `examined_evidence_ids`.
- `tools/checks/configuration-persistence.ps1` rule 8 (:580-640) has three constraints that matter here. The ledger writer writes only `ingestion_batch, accepted_evidence, evidence_rejection, ingestion_disposition, batch_refusal, recompute_job`. The consequence store is INSERT-only on its four tables plus `financial_consequence_work_attempt`. And: "Dirty work rows are inserted only by migration 0011 triggers, so **no module may write financial_consequence_work at all**".
- `s4-power-demo-cases-v1.json` P01-power: 23 back-to-back 20 kW means fully cover Candidate `[06:05, 08:00)`. The power and Finding tools are one-shot CLIs (`assess_dispatch process-jobs`, `match-findings`) with no scheduler.

## Findings

### H1 (High, acceptance gap): the late-power walkthrough and Outcome cannot reach S5 eligibility on an unchanged FindingRevision

Packet :13 (Outcome) and :34 (phase 3) say: accept a late good generator-power interval "that changes its technical digest without relying on a new FindingRevision", drain, then assert a "new consequence revision ... current priced eligibility for S5-01".

That cannot happen. A reading accepted after the FindingRevision's analytic run is not in `run_evidence_ids`, so re-deriving the *same* FindingRevision gives `QUANTITY_UNAVAILABLE / POWER_NOT_IN_ASSESSMENT_INPUTS` (`fuel_cost.py` ~:333). Packet item 3 correctly forbids any shortcut. The before-drain half is achievable: the reading enters `examined_evidence_ids`, so the head reads `STALE/TECHNICAL_INPUT_CHANGED`, exactly as Architect Q2 describes. The drained revision n+1 on that FindingRevision is honestly *not* S5-eligible, though.

A `PRICED` result needs a new analytic run that includes the reading (S3 `process-jobs`, which the same acceptance already queues through `_coalesce_job`). Then S4 `match-findings` must append a revised FindingRevision, and its 0011 insert trigger queues the work. The fixture also blocks this path. P01-power already covers every Candidate minute, so any additional good mean overlaps one and ends `POWER_OVERLAP_CONFLICT` even after reassessment.

**Why it matters:** an implementer either fails phase 3 or invents a shortcut the packet forbids. The registry node then cannot be honestly resolved, and the claimed S5-01 prerequisite is mis-described.

**Fix (Planner, no owner input):** rewrite the Outcome and phase 3 as two legs, both on an isolated copy.

- **Leg A, same FindingRevision.** Accept a late GOOD power mean in Candidate time. Before the scheduled drain, assert `STALE/TECHNICAL_INPUT_CHANGED` plus the `EVIDENCE_ACCEPTED` work ID (`STALE_QUEUED` in the bridge). After the drain, assert revision n+1 on the same FindingRevision with `QUANTITY_UNAVAILABLE / POWER_NOT_IN_ASSESSMENT_INPUTS`, the old revision retained, `CURRENT` currentness, and no S5 money.
- **Leg B, genuinely revised Finding.** Run `assess_dispatch process-jobs` and `match-findings` and assert a revised eligible FindingRevision. Then the old FindingRevision's `EVIDENCE_ACCEPTED` work either no-ops as superseded or derives the latest eligible revision exactly once (pick one and assert it). The new revision's consequence is `CURRENT/PRICED` and S5-eligible.
- **Fixture.** Name an authored variant whose late mean *fills a withheld gap*, for example P01-power with the 07:00-07:05 mean withheld until a later decided time. The pre-late state is then honestly `POWER_COVERAGE_GAP` (or whatever S3 yields; the implementer records it). Keep the variant in its own database so P01-power and S4-02b evidence stay valid. Treat it as demonstration-labelled content under the existing owner ruling, and do not change P01-power's own label.

Also change the README row text "recomputes an exact Finding fuel consequence; current money becomes eligible for S5-01". It should say that current money becomes eligible *after the Finding is re-evaluated*.

### H2 (High): the migration shape omits the existing `UNIQUE (finding_revision_id)` and the 0011 trigger's `ON CONFLICT` target

Item 1 asks for `EVIDENCE_ACCEPTED` rows carrying `finding_revision_id` and a unique `(accepted_evidence_id, finding_revision_id, cause)`. However, 0011's `financial_consequence_work_finding_revision_once UNIQUE (finding_revision_id)` already holds a row for every FindingRevision (from the trigger or the L4 bootstrap). The first `EVIDENCE_ACCEPTED` insert for any existing Finding therefore violates it. Under item 2's atomicity rule, that rolls back the *acceptance*, so ingestion of late power fails. If the implementer instead writes `ON CONFLICT DO NOTHING`, the work is silently lost.

Narrowing the constraint to a partial unique index (`WHERE cause = 'FINDING_REVISION_APPENDED'`) is not enough on its own. `financial_consequence_dirty_on_finding_revision` uses `ON CONFLICT (finding_revision_id)`, which cannot infer a partial index. Every FindingRevision insert would then fail with "no unique or exclusion constraint matching the ON CONFLICT specification", which breaks S4 matching.

**Fix:** item 1 names the replacement explicitly:
- drop `financial_consequence_work_finding_revision_once`;
- add a partial unique index for `FINDING_REVISION_APPENDED`;
- `CREATE OR REPLACE` the 0011 trigger function with `ON CONFLICT (finding_revision_id) WHERE cause = 'FINDING_REVISION_APPENDED' DO NOTHING`;
- add a partial unique index `(accepted_evidence_id, finding_revision_id) WHERE cause = 'EVIDENCE_ACCEPTED'`;
- replace `financial_consequence_work_cause_shape` with a three-arm CHECK.

Phase 1 proof must include "a FindingRevision append still enqueues exactly once after 0012" and "an `EVIDENCE_ACCEPTED` row coexists with that FindingRevision's own row".

### H3 (High): the enqueue location conflicts with architecture guard rule 8, and the packet does not choose a mechanism

Item 2 says to "insert scoped work before commit" in the acceptance transaction. Rule 8 forbids that from the ledger adapter twice over. The ledger writes only its six tables, and no module may write `financial_consequence_work` at all (work rows are trigger-only). An implementer who adds an `INSERT` in `decide_chunk` fails `check-architecture`. They then either edit the guard, which is a boundary decision nobody made, or pick a design under pressure.

**Fix:** specify an `AFTER INSERT` trigger in the new migration, following the 0011 precedent. Either:
- **on `ingestion_disposition`** `WHEN (NEW.decision = 'ACCEPTED')`, joining `accepted_evidence` by `NEW.accepted_evidence_id`; or
- **on `accepted_evidence`** (fires only on a genuine insert, because duplicates take `ON CONFLICT DO NOTHING`).

It selects by `role = 'generator_power'` (the stored, binding-derived role) and half-open overlap with the latest eligible FindingRevision's episode, scoped by `tenant_id, site_id`. That makes atomicity and "duplicate/conflict/rejected never enqueue" structural, and it needs no guard change. The disposition trigger has one advantage: the "accepted disposition" recheck in item 3 holds by construction. If the Planner prefers adapter code, the packet must say that rule 8 is amended and how, and that is an Architect boundary call.

The packet should also correct the anchor `process_batch`/`_persist` to `decide_chunk`/`_persist` (L1).

### M1 (Medium): claim, lease, backoff and "due time" are unimplementable as written on append-only, INSERT-only tables

Item 1 says "Index pending selection by Site and due time". Item 4 says "database claim/lease ..., persisted retry eligibility/backoff". However, `financial_consequence_work` and `..._work_attempt` are append-only, and rule 8 makes the consequence store INSERT-only, so there is no column to update with a lease or due time. A mutable lease table would need a guard amendment like the one the S3 `recompute_job` got.

**Fix:** pin the mechanism. One option needs no guard change:
- **Claim:** the runner takes `pg_try_advisory_lock` on `('financial_consequence_runner:' || site_id)` (single consumer per Site) and holds it for the run. Per-item `record_attempt` locks already exist.
- **Retry eligibility:** derive it from the last FAILED attempt's `finished_at` plus a fixed backoff schedule by `attempt_no`, with a stated cap and stated behaviour after the cap (stays visible and pending, never terminal-silent).
- **Index:** drop the "due time" index wording, or index `financial_consequence_work_attempt (work_id, attempt_no DESC)`.

Otherwise, name the new mutable table and the guard amendment. In either case, state how "a later scheduled run retries it" is tested without sleeping, for example with an injectable clock.

### M2 (Medium): the read changes in item 5 have no phase, and the discrepancy must not add new copy

`chain()`'s pending SQL does not match an `EVIDENCE_ACCEPTED` cause. Until it does, the item 5 queued state and the phase 3 "queued work ID" assertion cannot pass. The `STALE`-with-no-work discrepancy also needs a typed field. No phase owns either change.

**Fix:** put both in phase 1 or phase 2 and state the matching rule: `EVIDENCE_ACCEPTED` rows whose `finding_id` is the selected Finding's (or whose locator is the selected revision). Express the discrepancy as a typed `currentness.reasons` code (for example `NO_WORK_RECORDED`) or a diagnostic field. Keep the existing reviewed `REASONS["STALE"]` text, and add **no** new `REASONS` sentence. That is what keeps `USER_REVIEW_REQUIRED: false` true.

### M3 (Medium, ambiguity): "latest eligible FindingRevision" is undefined

The term is used in items 1 and 3 and in the reviewer checks and phase 3, but no file defines it (`grep` of `tasks/`, DECISIONS, the backlog and architecture docs). The built worker uses `max(revision_no)`, with no lifecycle or source-gate filter. `quantify` already makes non-`SUPPORTED` revisions unavailable, and the read applies `source_open`.

**Fix:** define it in one sentence. Either "the Finding's highest `revision_no` FindingRevision in the same tenant/Site (lifecycle and source gate are decided by `quantify`/the read, not by the selector)", or name the extra filters. Say also whether the enqueue selector uses the same definition.

### M4 (Medium, residual correctness): acceptance selection can race a concurrent FindingRevision append and its drain

The race runs like this:
1. Acceptance (T1) selects overlapping Findings at READ COMMITTED.
2. `match-findings` (T2) commits a new FindingRevision for that window after T1's select.
3. A drain of T2's work runs before T1 commits, so it cannot see the reading.
4. T1 commits with no row for the new revision.

The read then shows `STALE` with no work, and stays that way until another trigger. Item 2's "must not omit a possibly affected Finding" is not met.

**Fix:** require both the new acceptance trigger and the 0011 FindingRevision-insert trigger to take the same Site-scoped transaction advisory lock (for example `'financial_consequence_enqueue:' || site_id`) before selecting or inserting. Under READ COMMITTED, the plpgsql select after the lock sees the other transaction's committed revision. Add a two-connection Postgres test.

### M5 (Medium): the downgrade policy is unstated

Item 1 requires a proved downgrade. After upgrade, `EVIDENCE_ACCEPTED` rows can exist. `ledger_append_only` blocks deleting them, and restoring the two-arm CHECK and `UNIQUE (finding_revision_id)` then fails.

**Fix:** state the policy. Either the downgrade refuses with a clear error when any `EVIDENCE_ACCEPTED` row exists (and is tested), or it is an explicitly destructive dev-only downgrade that disables the append-only trigger. Also state what downgrade does to the replaced 0011 trigger function (restore its original body).

### L1 (Low): wrong anchor name

`process_batch` does not exist. The acceptance transaction is `PostgresEvidenceLedger.decide_chunk` (`postgres_evidence_ledger.py:242`), called from `evidence/ledger_service.py:176`. The in-memory `evidence/ledger.py:403 decide_chunk` is unaffected if H3's trigger route is taken.

### L2 (Low): the typed no-op has no storage

Item 3's "records a successful typed no-op" and item 4's no-op count need a home. Attempts allow only `SUCCEEDED`/`FAILED` and carry no no-op reason. Name it: either a `SUCCEEDED` attempt with empty `consequence_revision_ids` plus a new nullable `outcome_detail`/`no_op_reason` column (with a CHECK), or a new outcome value, which also changes the one-success index and `pending_work`.

### L3 (Low): unknown causes fall through in the existing worker

`ConsequenceRecomputeWorker.targets()` treats any non-`FINDING_REVISION_APPENDED` cause as an assumption range. If phase 1 is merged or run before phase 2, an `EVIDENCE_ACCEPTED` row is drained as a Site-wide overlap recompute and marked SUCCEEDED, which loses its typed recheck. Phase 1 should make an unknown cause a typed FAILED attempt (or skip it), or the packet should state that phases 1-3 merge together.

### L4 (Low): no backfill decision for heads that are already stale

0011 bootstrapped pre-existing FindingRevisions (review L4). Here, late power accepted before 0012 leaves `STALE` heads with no work forever. The new discrepancy code will show them, so this is honest, but the packet should say whether 0012 enqueues for them (for example, accepted generator-power evidence overlapping a latest revision and recorded after its head consequence) or deliberately leaves them as reported discrepancies.

### L5 (Low): the runner shape is open

Item 4 asks for a "documented one-minute recurring service/timer". Say whether the deliverable is a long-running `run --every 60 [--all-sites]` loop or a one-shot CLI under an external timer (Windows Task Scheduler or systemd timer), and how the CLI's development-tenant restriction (`recompute_consequences.py`: only `DEVELOPMENT_TENANT_SLUG`) applies to the "scoped active-Site iterator".

### I1 (Info): Depends text differs from the registry

The packet and README list S4-01, S4-03 and `A-S5-overview`. The registry `requires` is `A-S4-financial, I-S2-02, I-financial-store`. This is harmless (all are resolved), but align them at the next edit or note why the registry is narrower.

## USER_REVIEW_REQUIRED: false is justified, on two conditions

The current UI already renders reviewed copy for every state this slice produces: `STALE`, `STALE_QUEUED`, `PENDING`, and `POWER_NOT_IN_ASSESSMENT_INPUTS`. No new panel or route is needed. It stays justified only if:
- (a) M2's discrepancy stays a code or field and adds no new sentence;
- (b) H1's leg A outcome (the "not among this finding's checked inputs" wording appearing after a late reading) is accepted as existing reviewed copy.

The packet already says that any new owner-facing text reopens the flag, which is correct.

## Phase sizing

Phase 1 (migration, trigger and tests) and phase 3 (walkthrough) each fit one context. Phase 2 is the heaviest: worker recheck, no-op, claim and backoff, the CLI loop, runner documentation, and M2's read change if placed there. It probably still fits under ~120k, provided the claim mechanism is pinned (M1). Otherwise, move the read change (M2) to phase 1. Each phase's proofs are non-vacuous once H1, H2 and M4 are added.

## Carries for the Implementer (after the Planner amendment)

- C1: Prove H2 explicitly. Insert a FindingRevision after 0012 and assert one `FINDING_REVISION_APPENDED` row. Insert an `EVIDENCE_ACCEPTED` row for the same revision and assert both coexist. Run the 0011 bootstrap rows through upgrade, then downgrade per M5.
- C2: Rule 8 must still pass unchanged (or with the named amendment). Assert in a test that no Python module inserts into `financial_consequence_work`.
- C3: Half-open edge tests at both ends: a reading ending exactly at `episode_start` and one starting exactly at `episode_end` do not enqueue. A zero-width episode never enqueues.
- C4: Foreign-Site proof: an accepted reading at Site B with identical times enqueues nothing for Site A, and the worker refuses a forged cross-Site locator with no fallback.
- C5: Record exact work, attempt and consequence IDs, and the `examined_evidence_ids` before and after, in the walkthrough artifact. Record no mock money.

## Residual risks the packet does not name

- **R1:** After late evidence, S5 current money depends on S3 `process-jobs` and S4 `match-findings`, which are still one-shot and unscheduled. S4-02c schedules only the consequence drain. `D-2026-10-14-s5-selected-window-overview` already makes S5 show `PENDING`/`STALE` while analytic work is dirty, so this is honest. In practice, though, a late reading leaves Overview money unavailable until someone runs those CLIs. This is optional for the Architect: does S3/S4 runner scheduling become its own follow-on before W1 exit, or does S4-02c's runner also drive them? It is not a blocker for this packet.
- **R2:** Row volume. There is one work row per (accepted generator-power evidence x overlapping Finding). A gateway backfill of a day of 5-minute means across many Findings creates hundreds of rows per Site. This is acceptable at the current scale, but bounded batch size (item 4) should be tested against such a backfill.
