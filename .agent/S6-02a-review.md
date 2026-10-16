# S6-02a slice review (phase 2 + slice review): verification core

Reviewer: fresh, independent Claude reviewer. I did not author this slice. I reviewed worktree `AssetOpsV1-review5`,
detached at `8b6e0c10` (the head of `task/S6-02a-verification-core`).

- The S6-02a code diff is `e39a3c20..8b6e0c10`. `f6476c38..8b6e0c10` also carries the S4-04 main merge, which is
  already reviewed and was not re-reviewed here.
- `f88f3c8c..8b6e0c10` touches only `.agent/`, so the implementer's full suite at `f88f3c8c` is the same code
  revision as the one under review.

## Verdict

**RETURN on one Medium (F1).** Everything else is Low.

The phase-1 fixes F1-F8 are in place. The verdict rules, holds, per-window source resolution, currentness gates,
idempotency and rule 8 are correct.

F1 is a fail-open on the trial hold. The evaluator decides what to write from an assessment it read before taking the
battery trial lock, and it stamps the write with the earlier `now`. I reproduced the interleaving on Postgres: it
leaves a lasting RESOLVED VERIFIED, with the hold released, while the current outcome is INCONCLUSIVE. Re-evaluating
does not repair it. The fix is small.

## Checks run (what I saw)

Environment:
- Python: the main venv.
- `PYTHONPATH`: this worktree's `backend;contracts;gateway;simulator`. `assetops_backend.__file__` resolves to
  `AssetOpsV1-review5`.
- `ASSETOPS_GUARD_PYTHON`: the same python.
- Database: private base DB `assetops_s602arev5_test`, dropped afterwards. All runs were serial.

Results:
- `tools/check-architecture.ps1`: passed.
- `tools/check-agent-workflow.ps1`: passed. Rule 8 is part of the architecture check and passed:
  - `$actionTables` lists the five verification tables (`configuration-persistence.ps1:707-709`).
  - The only `INSERT INTO verification_*` and `INSERT INTO action_event` statements are in
    `postgres_action_store.py`, and they name the table literally. There are still nine writers, with no tenth.
- `pytest test_s6_verification_verdict.py test_s6_verification_rules.py test_s6_verification_evaluator_postgres.py
  test_s6_verification_plan_postgres.py -q`: **71 passed**, 0 failed and 0 skipped in the JUnit file, 362 s.
- `pytest test_s6_action_store_postgres.py test_s6_action_apply_postgres.py test_s6_action_records_postgres.py -q`:
  **21 passed**, 219 s.
- Scratch reproduction of F1, kept outside the repo and not committed: 1 passed, with the output quoted under F1.
- **Not rerun:**
  - The full suite. I cite the implementer's run at `f88f3c8c`: `pytest backend/tests -n 2 --dist loadfile
    --no-loadscope-reorder`, 2464 passed, 0 failed, 0 skipped, 0 errors, 1233 s. That revision is code-identical
    to the one under review.
  - `tools/writer_guard_probes.py`. I had no rule-8 doubt, so I cite the packet: 72 caught, controls allowed.
  - `check-all`.
  - The host replay `host/tests/test_s6_verification_replay.py`, which needs the Lab and gateway. I read it.
  - The frontend checks. This slice has no frontend change; the frontend files in `f6476c38..` come from S4-04.
  - The implementer's mutation kills, which are cited, not re-proven.

## Findings

### F1 - Medium (fail-open on the hold): the evaluator decides outside the trial lock and stamps the write with a stale `now`

`backend/assetops_backend/actions/verification.py:606` and `:614`, used by `compose` at `:647-672`, and
`postgres_action_store.py:736` (`record_evaluation`).

`evaluate` captures `now` and runs `_assess` before `record_evaluation` takes the battery `trial_lock`. Under the lock,
`compose` reads the latest outcome and events but trusts the earlier assessment. It then writes the outcome at
`recorded_at = now` and the events at `now + ε`.

The failure needs two evaluation requests. Request A reads basis X at t0 and resolves to VERIFIED. Between A's read
and A getting the lock, the basis changes: here, the per-window source resolution stops being coherent. Request B
reads basis Y at t1 > t0 and commits INCONCLUSIVE first. Then A takes the lock:
1. `latest` is B's outcome, and its basis differs from A's, so A inserts a VERIFIED outcome that supersedes B.
2. Nothing was resolved yet, so nothing is withdrawn.
3. A appends RESOLVED, stamped t0+ε.
4. Ordering is by `(recorded_at, id)`, so B's INCONCLUSIVE stays the *latest* outcome. A's RESOLVED is still the
   latest resolution event.

Reproduced on Postgres by rewinding the clock to A's `now` and replaying A's pre-lock assessment after B committed.
Both are code paths `evaluate` actually takes. The output:

```
A: VERIFIED True
events: ['ACCEPTED', 'APPLIED', 'RESOLVED']
lifecycle outcome: VERIFIED
verification state: INCONCLUSIVE
guard for another Finding: None          <- hold released
re-evaluate: SETTLED INCONCLUSIVE withdrawn False
events after: ['ACCEPTED', 'APPLIED', 'RESOLVED']
```

Why it matters:
- The packet requires the evaluator to write outcome, metrics and RESOLVED or RESOLUTION_WITHDRAWN in one serialized
  transaction under the trial lock, and requires INCONCLUSIVE to retain the hold. Here a new trial on the battery
  becomes acceptable while the current outcome is INCONCLUSIVE.
- It never self-heals. `compose`'s reuse branch (`:649-650`) does not check that the outstanding RESOLVED belongs
  to the outcome being reused, so later evaluations leave it in place.
- The window is narrow: two concurrent SYSTEM requests, plus a basis change within roughly the time `_assess` takes
  plus the 5 s lock timeout. But the result is lasting, not transient.

Fix (small):
1. Run `_assess` inside `compose`, and take `now` there or under the lock. As a cheaper alternative, refuse in
   `compose` with a retryable 409 or 503 when `latest.recorded_at` or any event `recorded_at` is at or after `now`.
2. In the reuse branch, also withdraw when `resolved` and `resolution["outcome_id"] != str(latest["id"])`, or when
   the latest outcome is not final.
3. Add one Postgres test of the interleaving. The scratch test above is a template.

### F2 - Low: the overlap's "invalidating evidence" is any late reading in a window, not the evidence that invalidated the closure

`verification.py:633-638` and `service.py` `reassessment_overlaps`.

The withdrawal records every evidence row, of any verification role and any asset, that was decided after the
RESOLVED and touches either window. That includes readings that F6 then filters out, such as an unbound asset. It
also includes withdrawals whose actual cause was a Foundation, source or S3 change. R1 says only the late evidence that
invalidated the closure counts.

This over-blocks and fails closed. The consequence, though, is a permanent battery block with no override. Narrow
the list to evidence whose ID enters the new window evidence, or record it only when the cause is late evidence. If
that is not done, name the over-approximation in the handoff.

### F3 - Low (deviation, fail-closed): a moved baseline selection settles INCONCLUSIVE instead of REASSESSMENT_PENDING

`verification.py:541`.

`D-2026-10-16-s602a-cutoff` says evaluation returns REASSESSMENT_PENDING unless both pinned windows stay CURRENT on
their pinned basis. A baseline day that is CURRENT on a different run becomes the blocker
`BASELINE_SELECTION_CHANGED` and settles INCONCLUSIVE. The read state shows REASSESSMENT_PENDING before that.

This is defensible, because an immutable plan cannot re-pin its baseline. It is not documented as a deviation, so add
it to the handoff.

### F4 - Low (acceptance ambiguity, fail-closed): once a plan has an outcome, no replacement plan can be frozen

`verification.py:278-280` (`VERIFICATION_PLAN_EVALUATED`). After any outcome, INCONCLUSIVE included, the Action can
never be re-planned. Two consequences follow:
- INCONCLUSIVE holds the battery forever.
- That includes the shipped Lab replay, whose settled outcome is INCONCLUSIVE (deviation 1).

`D-2026-10-16-s6-verification` says a changed covering FoundationRevision gives "INCONCLUSIVE without a new comparable
plan", which implies such a plan can be frozen. Raise this with the Architect together with deviation 1. It does not
block this slice.

### F5 - Low: the Action read shows two different "outcome" states

`lifecycle.py` `reduce` and `action_api.py:217-221`.

`state.outcome` comes from resolution events and keeps showing VERIFIED after late evidence. The sibling
`verification.state` shows REASSESSMENT_PENDING. The Change read likewise keeps an apply-time `outcome: PENDING`, which
the handoff names.

The packet says late evidence immediately withdraws the Verified/Resolved presentation. S6-02b must take its
presentation from `verification`, not from `state.outcome`. Say so in the fixture notes or the handoff to the UI
implementer.

### F6 - Low: verification `_wire` does not normalize timestamps to UTC

`verification.py:58-60`. `value.isoformat()` is applied to `timestamptz` values as the session returns them. The
action store does not pin the session `TimeZone` (`postgres_action_store.py:80`), so `+00:00` holds only because the
Docker server runs in UTC. The rules module's `_iso` does use `astimezone(timezone.utc)`. Do the same in `_wire`, so
the F7 ruling does not depend on server configuration.

### F7 - Low (test gap): 401 and 403 are proven only on the new POST route

The new GET routes `.../verification/outcome` and `.../verification/history` share `open_scope(access)` with the
other Action reads, so they behave correctly by construction. Only 404 is asserted for them; 401 and 403 are not.

## Phase-1 findings F1-F8: verified fixed

| Finding | Status |
| --- | --- |
| F1 | Freeze requires the baseline revision to be the change's split or superseded revision (`verification.py:173-181`); there is a Postgres refusal test. |
| F2 | Freeze needs CURRENT baseline days (`:187-193`). Binding needs `later_end` passed, the head plan, and CURRENT later days (`:326-343`). The evaluator returns REASSESSMENT_PENDING on S3 or S4 pending, or on a moved later day (`:532-540`). Tests cover stale and FAILED days, an open window, and a day turning stale. |
| F3 | Freeze takes `acceptance_fence`. I checked that it uses the same key as S2 `_coalesce_job` (`postgres_evidence_ledger.py:534`, domain `dispatch`), which every accepting chunk takes. Tests cover another role at exactly `later_start`, a report just before it, an unaccepted report, and an in-flight acceptance. |
| F4 | Binding `idempotency_key` and `payload_sha256` are persisted (migration 0019 is unmerged, so editing it is fine). The head is re-checked under the lock. |
| F5 | Done. |
| F6 | Battery and bound-asset filters are in place, with a unit test. |
| F7 | Rules `_iso` uses `+00:00`, and the fixture asserts every timestamp. F6 above is the remaining gap. |
| F8 | Labelled with the note `pre_s6_02a_second_action`. |

## Confirmed correct (no finding)

- **Verdict.**
  - Any unknown, including comparability FAIL, gives INCONCLUSIVE. The known failures stay as `KNOWN_FAILURE:*`.
  - `GUARDRAIL_FAIL` appears only on INEFFECTIVE with no unknowns, that is, only for a measured failure.
  - A target miss alone gives `TARGET_MISS`.
  - Source is resolved per window (`provenance` is called once per window's IDs). MIXED, UNKNOWN, crossed classes, a
    shared run or a missing resolution all give `SOURCE_NOT_COHERENT`, then INCONCLUSIVE.
- **Holds.**
  - `is_unresolved` reads the latest ordered RESOLVED or withdrawal.
  - INCONCLUSIVE and PENDING keep the hold.
  - `PRIOR_TRIAL_GUARDRAIL_FAILED` blocks a different Finding on the battery and links the outcome.
  - `PRIOR_TRIAL_REASSESSMENT_OVERLAP` is tested on both sides of R1.
  - The accept guard evaluates under the trial lock.
- **Idempotency.**
  - The same key replays the same outcome ID.
  - A new key on the same basis reuses the outcome.
  - A changed basis appends a superseding outcome. The basis is deterministic: evidence and publication IDs are
    sorted.
  - A pending request retried with the same key re-assesses.
  - Withdrawal plus a new outcome commit in one transaction.
- **Test-scoped windows.** They are honest and do not leak into product reads:
  - The fake `window_evidence` is applied with `monkeypatch`, which restores it per test.
  - The fake provenance is set only on the harness service object.
  - Production composition always wires the real S3/S4 ports and the S4-05a resolver.
  - The fixture and the manifest label these cases TEST-SCOPED and "not a Lab replay".

## Residual risks in the handoff, re-rated

| Risk | Rating |
| --- | --- |
| Evaluator reads before the lock | Raised to Medium as F1, but for the concurrent-evaluation path. The single-evaluator gap (an acceptance with an earlier `decided_at` that commits after the read) is Low: any in-window acceptance queues an S3 recompute, which makes the pinned day non-CURRENT and the read REASSESSMENT_PENDING. |
| Freeze fence `decided_at` ordering | Low. |
| Registered lineage not centrally observable | Low, documented. |
| Change read `outcome: PENDING` | Low, see F5. |
| 503 on 5 s lock contention | Fails closed. |

None of these is High.
