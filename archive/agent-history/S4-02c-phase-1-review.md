# S4-02c phase 1: fresh Claude review (transactional acceptance work)

Reviewer: fresh Claude (did not build this). Branch `task/S4-02c-evidence-consequence-work`. Diff reviewed: `5af9f214..a42f8e05`
(`9d1b8303`, `9a4a421b`, `89e7b709`, `a42f8e05`). Judged against:
- packet `tasks/S4-02c-evidence-consequence-work.md`, phase row 1 and contract items 1, 2, 5 and the item 3 unknown-cause guard; carries C1-C4 (phase 1 halves);
- `.agent/S4-02c-plan-review.md`, `.agent/S4-02c-plan-fix-rereview.md` (N1-N8);
- `D-2026-10-13-s4-bounded-financial-basis` and `D-2026-10-14-s402-post-review-follow-ons`;
- the handoff `.agent/S4-02c-phase-1-handoff.md` and `.ai/CODE_STATE.md` "S4-02c phase 1". I treated the handoff's claims as claims and reran them.

## Verdict: ACCEPT with carries

Migration 0012 is correct against the contract. The three-arm CHECK, scoped FK, both partial unique indexes, the
replaced 0011 trigger with `ON CONFLICT (finding_revision_id) WHERE cause = 'FINDING_REVISION_APPENDED'`, the
accepted-disposition trigger filtered on the stored `generator_power` role, latest-revision selection scoped by
tenant+Site, one identical lock expression in both triggers, and the lock taken after the role check but before
selection all hold. Trigger failure rolls back acceptance. The two-connection race test proves that the
acceptance selects the *new* revision, not only that it waits. Downgrade refuses while evidence work exists and
otherwise restores 0011. `chain()` matches evidence work by Finding, and `NO_WORK_RECORDED` is a typed code with
no new copy. The unknown-cause guard closes the assumption fallthrough.

I found no High or Medium defect. There are three Low findings and two Info notes. None needs a fix round before
phase 2. L2 is a merge gate: phase 1 must not merge or deploy without phase 2.

## Checks I ran (results as observed)

- **Full backend suite**, run once on my scratch DB `assetops_s402crev1_full_test` at `a42f8e05` (after the
  head-pin test fix): **2066 passed, 0 failed** in 23:38. It ran alongside my mutation sweep, which explains the
  slower time compared with the implementer's 12:15. This closes the handoff's "full suite not rerun" gap.
- **Focused suites** on `assetops_s402crev1_test`:
  - `test_s4_evidence_consequence_work_postgres.py` + `test_s4_consequence_cause_dispatch.py`: **14 passed**.
  - `test_s4_consequence_store_postgres.py`, `test_s4_consequence_recompute_postgres.py`,
    `test_s4_consequence_read.py`, `test_s4_finding_api.py`, `test_s4_assumption_read_api.py`: **65 passed**.
- **`tools/check-all.ps1`: All 9 guards passed.** This includes Architecture seams, so rule 8 still passes with
  the comment-only edit, and Agent workflow passed. The orphan scan reported 31 tagged and 12 baselined.
- **My own mutations, 10 of 10 killed.** I ran them in a `git archive HEAD` copy in my scratchpad, so the live
  tree stayed untouched while the full suite ran. Each mutation got a fresh schema from the module fixture.
  Most of these differ from the implementer's twelve.

| Mutation | Result |
| --- | --- |
| Evidence trigger takes the lock *after* its INSERT (select before lock) | killed: race test (selects superseded revision) |
| Evidence trigger swallows its own error (`EXCEPTION WHEN OTHERS THEN RETURN NULL`) | killed: rollback-atomicity test |
| Trigger `WHEN` also fires on `DUPLICATE` | killed: replay/duplicate test (+ Site B test) |
| Zero-width episode filter removed | killed: half-open/zero-width test |
| Strict overlap relaxed to `episode_start <= interval_end` | killed: half-open test |
| Evidence arm allows an empty `[affected_from, affected_to)` | killed: shape test |
| `no_op_reason` allowed with non-empty consequence IDs | killed: shape test |
| Downgrade restores the 0012 conflict target instead of the 0011 body | killed: empty-downgrade test |
| `NO_WORK_RECORDED` appended even when work is pending | killed: chain/read test |
| Evidence trigger drops the `site_id` predicate | killed: Site B test |

- **Not run:**
  - Frontend tests, `tsc` and the build. No frontend file changed. `pending_work` gains two fields, and
    `financialsClient.ts:219` neither types nor renders them.
  - Layout evidence: not applicable, because there is no UI.
- Both scratch DBs were dropped afterwards.

## Migration 0012 (focus)

- **Three-arm CHECK** (`0012:61-68`). Each arm nulls the other causes' locators. The evidence arm requires the
  accepted, Finding and revision locators, plus `affected_to IS NOT NULL AND affected_from < affected_to`. The
  0011 `financial_consequence_work_range` CHECK is kept.
- **The upgrade drops the 0011 column CHECK by its auto-generated name** (`financial_consequence_work_cause_check`).
  The 0011 to 0012 upgrade test proves that the name matches.
- **Scoped FK** `(tenant_id, site_id, accepted_evidence_id) -> accepted_evidence(tenant_id, site_id, id)`. The
  target is the 0005 `accepted_evidence_scope_unique`.
- **The revision locator is already scoped** by the 0011 `financial_consequence_work_finding_revision_fk`.
- **Partial unique indexes.**
  - `..._finding_revision_once` (FRA only) and `..._evidence_once (accepted_evidence_id, finding_revision_id)`.
  - Each index's predicate is identical to its trigger's `ON CONFLICT ... WHERE` inference clause.
  - The C1 test proves that both indexes hold and that an FRA row and an evidence row coexist for one revision.
- **Evidence trigger** (`0012:100-130`).
  - The trigger is `AFTER INSERT ON ingestion_disposition WHEN (NEW.decision = 'ACCEPTED')`.
  - It joins the disposition's own stored `accepted_evidence_id`, scoped by tenant and Site.
  - The role comes from the binding (`_persist` writes `decision.binding.role`).
  - Null and empty reading intervals return before the lock is taken (N6 option).
  - "Latest" is `max(revision_no)` within tenant, Site and Finding.
  - The overlap is strict half-open, and zero-width episodes are excluded.
- **The coarse selection is complete.** The overlap predicate is exactly the reader's own
  (`postgres_consequence_store.py:127-128`, `interval_start < episode_end AND interval_end > episode_start`).
  Every reading `load_input` could load for the latest revision is therefore enqueued for it, and
  `quantify`'s examined set is a subset of that.
- **One exception, which is safe.** For a zero-width episode, `load_input` can load a reading that straddles the
  instant, but `quantify` returns `NO_CANDIDATE_TIME` with an empty examined set (`fuel_cost.py:309-311`). The
  digest therefore cannot change, and excluding zero-width episodes (C3) loses nothing.
- **Lock.** Both stored bodies contain the identical `pg_advisory_xact_lock(hashtextextended('financial_consequence_enqueue:' || NEW.site_id::text, 0))`,
  generated from one Python constant and compared by test (N6).
  - **READ COMMITTED:** the `INSERT ... SELECT` runs as a new statement after `PERFORM` returns, so it sees a
    revision committed by the lock holder.
  - My lock-after-INSERT mutation shows that the test checks the revision it *selects*, not only that it waited.
- **Lock order and deadlock.**
  - `decide_chunk` takes the batch row lock, then the enqueue lock (per accepted power row), then `_coalesce_job`
    once at the end of the chunk (`postgres_evidence_ledger.py:302-304`).
  - `FindingStore.apply` takes `finding:` and then the enqueue lock.
  - No path takes these in the reverse order. See I1 for the residual risk with unique-key waits.
- **Downgrade.**
  - The refusal runs first, inside alembic's transaction. The test shows the error, a version that stays at 0012
    and rows that are intact.
  - The empty case restores the exact 0011 trigger body, the two-arm CHECK and `UNIQUE (finding_revision_id)`.
    The test asserts all three and an FRA enqueue under the restored trigger.
  - The restored UNIQUE is safe, because with no evidence rows only FRA rows carry a `finding_revision_id`.
- **Upgrade.** The 0011 bootstrap rows are identical across the 0011 to 0012 upgrade, and nothing is backfilled
  (L4).

## Reads, guard and USER_REVIEW_REQUIRED

- **`chain()`** (`postgres_consequence_store.py:341`) adds `EVIDENCE_ACCEPTED` to the Finding-ID match. It is
  served by the new `financial_consequence_work_finding` index.
- **Read.** `NO_WORK_RECORDED` is added only when the state is STALE and `work` is empty (`consequence_read.py:193`).
  The bridge keeps `REASONS["STALE"]`/`["STALE_QUEUED"]`.
- **The two conditions hold.**
  - Condition (a): `NO_WORK_RECORDED` is not in `REASONS`, and no component renders `currentness_reasons`,
    `pending_work.cause` or `last_error_code` for consequences (grep of `frontend/src`).
  - Condition (b) is untouched in phase 1.
  - **`USER_REVIEW_REQUIRED: false` stands.**
- **Unknown-cause guard.** `targets()` raises `CauseNotSupported` for anything except the two 0011 causes.
  `process()` records a typed FAILED attempt, and no other backend code branches on cause.

## Deviations (as asked)

- **Closed four-code `no_op_reason` enum.** I accept it. The codes match N1's safe set plus item 3's
  Candidate-window no-op. Extending a CHECK by migration is the normal cost of a typed field, and it is better
  than a format-only CHECK. Phase 2 must use `EVIDENCE_OUTSIDE_CANDIDATE_TIME` only when the reading misses the
  *merged Candidate components* that `quantify` uses, never on quality (N1).
- **Downgrade also refuses on `no_op_reason`.** I accept it, because it follows the same never-delete rule.
  The path is untested; see L3.
- **`CAUSE_NOT_SUPPORTED` failure on every run until phase 2.** This is acceptable on an unmerged branch only.
  See L2.

## Findings

### L1 (Low, test robustness): the race test's "waited" probe is cluster-wide

`test_s4_evidence_consequence_work_postgres.py:388-389` counts `pg_locks WHERE locktype = 'advisory' AND NOT granted`
across the whole cluster. On this machine, where several `*_test` databases and suites share one Postgres, an
unrelated waiter can satisfy `waited` and skip the wait before the holder commits. The decisive assertion,
`w["finding_revision_id"] == nid`, still guards the result, so this is not vacuous today, but the "waited" half of
the M4 proof can pass spuriously. **Fix:** add `AND database = (SELECT oid FROM pg_database WHERE datname =
current_database())`, and ideally match `objid` to the Site's key. Fold this into phase 2.

### L2 (Low, merge gate): phase 1 alone leaves evidence work failing, accumulating and able to block the queue

Until phase 2 lands:
- every `run` appends one `CAUSE_NOT_SUPPORTED` FAILED attempt per evidence row and exits 1;
- `run_pending` takes `pending[:limit]` oldest first (`recompute.py:146`), so with `--limit N`, N or more older
  evidence rows block newer FRA and assumption work forever;
- the bridge says `STALE_QUEUED` ("a recalculation is queued") for work that cannot drain.

This is acceptable on the unmerged branch as the handoff states. **Carry:** do not merge or deploy phase 1
without phase 2. Phase 2's due/deferred selection must not let undrainable rows starve others.

### L3 (Low, test gap): the `no_op_reason` downgrade refusal is untested

`0012:177-179` is the implementer's own extension and has no test. It is cheap to add in phase 2, once
`record_attempt` writes `no_op_reason`: write a no-op attempt on an FRA row, then assert the downgrade refuses.

### I1 (Info, residual risk): the Site enqueue lock widens a concurrent-ingestion deadlock window

`_persist` uses `INSERT ... ON CONFLICT ON CONSTRAINT accepted_evidence_message_unique DO NOTHING`, which waits
on another chunk's uncommitted identical message. Take two concurrent chunks for the same Site and source whose
batches overlap:
1. Chunk A accepts a power mean, which takes the enqueue lock.
2. Chunk B inserts message X.
3. Chunk A reaches X and waits on B.
4. Chunk B's accepted power disposition waits on A's lock.

Postgres aborts one chunk, the transaction rolls back cleanly, and the batch stays IN_PROGRESS for retry. Two
overlapping keys in reverse order could already deadlock before 0012, so this widens an existing window rather
than creating one. R2's bounded-batch test could include two concurrent overlapping batches and log the result.

### I2 (Info): the unindexed scan runs under the lock

The evidence trigger scans the Site's `finding_revision` rows for overlap, with a correlated `max(revision_no)`
per row, after taking the Site lock. At current scale this is fine. It joins the handoff's named chunk-latency
risk for R2.

## Carries for phase 2

- L1, L2 (merge gate and starvation), L3.
- N1: never no-op on quality. `EVIDENCE_OUTSIDE_CANDIDATE_TIME` applies only against merged Candidate components.
  Test a non-GOOD same-asset mean that yields revision n+1.
- C4, worker half: a forged cross-Site locator is refused without fallback.
- N3/N4: a dedicated runner connection with unlock in `finally`, and an injected `now` for retry, deferred and
  backlog counts.
- "Latest" in the worker uses the trigger's tenant/Site/Finding `max(revision_no)`. The handoff correctly notes
  that `latest_revisions_overlapping` scopes differently.
- R2 bounded batch with chunk-latency logging (I1, I2).
