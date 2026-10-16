# S6-02a fix round 1 re-review: verification core

Reviewer: a fresh, independent Claude reviewer. I did not author this slice or its fixes. I reviewed worktree
`AssetOpsV1-review5`, detached at `b9b6e93c` (the head of `task/S6-02a-verification-core`).

Inputs:
- The fix diff `c07fc2b4..b9b6e93c` (excluding `.agent`).
- The slice review `.agent/S6-02a-review.md`.
- The ruling `D-2026-10-16-s602a-holds` (`.agent/architect-S6-02a-holds-answers.md`).
- The brief `.agent/S6-02a-fix-1-brief.md`.
- The packet's "Fix round 1" section.

## Verdict

**RETURN on one Medium (R1, F2 attribution timing).**

- F1 is closed.
- F4 matches the ruling.
- F2 is mostly right. One reproduced case breaks the ruling's "only readings whose arrival materially changed"
  rule and moves the permanent-overlap boundary earlier:
  - A non-material bound reading joins the causal set because a later, material reading changed the same window.
  - An Action accepted between the two readings is then permanently blocked, although it was accepted before any
    invalidating evidence arrived.
- The fix is local to `_attribution`.

## Checks run (what I saw)

Environment:
- Python: main venv python.
- `PYTHONPATH`: this worktree's `backend;contracts;gateway;simulator`. `assetops_backend.__file__` resolves to
  `AssetOpsV1-review5`.
- Database: private base DB `assetops_s602arr_test` on 127.0.0.1:55432, dropped afterwards.

Results:
- `tools/check-architecture.ps1`: passed.
- `tools/check-agent-workflow.ps1`: passed.
- Focused Postgres and pure tests, `-n 2 --dist loadfile`: **97 passed** in 266 s; the JUnit file shows tests=97,
  failures=0, errors=0, skipped=0. The files were:
  - `test_s6_verification_holds_postgres.py`, `test_s6_verification_evaluator_postgres.py`,
    `test_s6_verification_plan_postgres.py`;
  - `test_s6_verification_verdict.py`, `test_s6_verification_rules.py`;
  - `test_s6_action_store_postgres.py`, `test_s6_action_apply_postgres.py`, `test_s6_action_records_postgres.py`.
- A scratch reproduction of R1 (2 passed, output quoted below). It was a temporary file under `backend/tests`,
  deleted afterwards and not committed.
- I checked that the fix diff adds no `INSERT`, `UPDATE` or `DELETE` (`git diff ... | grep`: no match).
  `late_evidence` gained only a read predicate.
- **Not rerun:**
  - The full suite. I cite the implementer's run at `3924ee03`: 2469 passed, failures=0, errors=0, skipped=0,
    1116 s. `3924ee03..b9b6e93c` touches only `.agent/`, so that revision is code-identical to the one under
    review.
  - `check-all`, the registry checker, and the mutation checks. These are cited, not re-proven.
  - The frontend. There is no frontend change.

## F1: closed

`compose` now does all of the following under the battery trial lock taken in `record_evaluation`
(`verification.py`, `evaluate`):
- re-reads the head;
- takes `now`, bumped past every stored outcome and event stamp;
- runs `_assess`.

The store reads in `_assess` use separate connections. They are made after the lock is granted, so they see every
earlier holder's commit.

The reuse branch withdraws an outstanding RESOLVED with `RESOLUTION_NOT_CURRENT` in two cases: when the RESOLVED
belongs to another outcome, or when the reused outcome is not final. A stale decision therefore cannot append
RESOLVED, and a stale RESOLVED cannot persist through reuse.

`TestF1DecisionUnderTheLock` replays the review's interleaving and passes. A reused INCONCLUSIVE outcome leaves no
RESOLVED and the hold kept.

## F4: matches the ruling

`_continuation_check` runs inside `freeze_plan`'s locked `check`.

Eligibility:
- A plan with no outcome is eligible.
- Otherwise, every one of these must hold:
  - the latest outcome is this plan's INCONCLUSIVE;
  - the read state is INCONCLUSIVE, not REASSESSMENT_PENDING;
  - no RESOLVED is outstanding;
  - any RESOLUTION_WITHDRAWN was settled by an outcome in the same job or a later one;
  - no reassessment overlap names the Action.

Refusals:
- Guardrail failure, current VERIFIED or target-miss, pending reassessment, overlap, and not INCONCLUSIVE are
  refused, each with a `reason`.
- Each is asserted on Postgres, including GUARDRAIL_FAILED, RESOLVED, REASSESSMENT_PENDING (twice) and
  PRIOR_TRIAL_REASSESSMENT_OVERLAP.

The post-cutoff rule:
- Once the replaced plan's later window has an accepted report, `l0 < prior.later_end` is refused.
- `l0 == later_end` does not intersect the half-open prior window. In practice the general later-window check also
  refuses it whenever the prior window's end SOC sample is accepted.

History and idempotency:
- The baseline is revalidated by the normal freeze preconditions.
- History, the old outcome and idempotency are retained:
  - an original retry returns the original ID;
  - a replacement retry returns its own ID;
  - stray new keys are refused with NOT_HEAD.

The hold:
- After continuation the hold reads `PRIOR_ACTION_UNRESOLVED`.
- No RESOLVED is appended, and the new head reads PENDING.

## F2: largely matches, with one Medium

What is correct:
- **Candidates** are filtered to tenant and Site, with:
  - `decided_at` after the RESOLVED stamp and at or before the withdrawal instant;
  - a pinned-window intersection;
  - the frozen per-window bound role or asset, which is the plan battery for SOC.
  Unbound assets and unbound roles are excluded, as proven by the TEST-SCOPED rewrite.
- **Material change** compares the closed window result with the reassessed one, with:
  - frozen bindings;
  - Foundation reserves held at the closure cutoff;
  - source excluded from the compared keys.
- **Source-only and Foundation-only withdrawals** record `NONE` and an empty set, as proven.
- **Indeterminate** cases are a bound reading whose effect on a pending or moved S3 selection cannot be shown.
  They give `INDETERMINATE`, an ordinary hold and never an overlap, as proven.
- **Overlap timing.** `reassessment_overlaps` uses only CAUSAL payloads with
  `resolved < min(causal accepted_at) < other.created_at < withdrawal`, and keeps exact links. Both sides of the
  boundary are tested.

### R1 - Medium (ruling acceptance gap; wrong permanent block, no override): a non-material reading joins the causal set and moves the overlap boundary earlier

`backend/assetops_backend/actions/verification.py`, `_attribution`: the per-window loop, with
`entered = ...`, `hit = [...]` and `if was != now_ and hit:`.

The implementation attributes **every** bound candidate that entered a window's used evidence, whenever that
window's result changed at all.

`rules._instant` and `_power_slot` add a reading's ID to `evidence_ids` even when it exactly duplicates an existing
value: the same SOC value at the same instant, or the same interval and value. Such a reading enters the used
evidence without changing anything. On its own it is correctly not causal. With the scratch variant
`conflict=False`, the result is `INDETERMINATE`, an empty set and `PRIOR_ACTION_UNRESOLVED`.

When a later conflicting reading then changes the same window, the duplicate is swept into the CAUSAL set.
`reassessment_overlaps` takes `min(accepted_at)` over that set, so the overlap boundary moves back to the
duplicate's acceptance.

Reproduction on Postgres (real roles-2 path, the packet's TEST-SCOPED complete windows, real accepted readings
injected the way the existing overlap tests do):
1. VERIFIED and RESOLVED at 12:00.
2. Bound SOC "50" at 08:30, identical to the pinned sample, accepted at 12:15.
3. A second Finding's Action accepted at 12:30.
4. Conflicting bound SOC "79" at 08:30, accepted at 13:00.
5. Evaluation at 14:00.

```
conflict True True REASSESSMENT_PENDING
withdrawn True attribution CAUSAL
invalidating [('aa71860a-...', '2026-11-02T12:15:00+00:00'), ('d976c5fe-...', '2026-11-02T13:00:00+00:00')]
guard PRIOR_TRIAL_REASSESSMENT_OVERLAP        <- permanent block
conflict False True REASSESSMENT_PENDING
withdrawn True attribution INDETERMINATE      <- the duplicate alone changes nothing
guard PRIOR_ACTION_UNRESOLVED
```

Why it matters:
- The ruling allows only "readings whose arrival materially changed" the pinned basis. It says "a newly listed but
  unused row is insufficient".
- It requires overlap only for an Action accepted **after** at least one such reading. It also says "Re-evaluation
  must not broaden the set".
- The Action accepted at 12:30 was accepted before any material evidence arrived, yet it is permanently blocked
  with no override. The ruling made this predicate a before-merge requirement precisely because the block is
  permanent.
- The packet names "a finer leave-one-out test is not done" as a deviation. It does not name this consequence. The
  ruling's "several jointly causal readings may be recorded together" covers readings that jointly cause the change,
  not a reading that is redundant on its own.

Fix (local to `_attribution`): replay the window by acceptance prefix.
1. Order the window's hit candidates by `decided_at`.
2. Recompute the window at each candidate's `decided_at`, with reserves held at the closure cutoff, as `after`
   already does.
3. A candidate is causal only when its arrival changes the result relative to the previous prefix. At minimum, the
   earliest causal `accepted_at` must be the first prefix at which the result differs from the closed result.
4. Readings that change nothing, such as exact duplicates, stay in `candidate_evidence_ids` only.
5. Add a Postgres test mirroring the reproduction above: duplicate, Action, conflict, then expect
   `PRIOR_ACTION_UNRESOLVED`, a CAUSAL set equal to the conflict reading only, and an overlap for an Action accepted
   after the conflict.

### R2 - Low: a bound reading that only changes the per-window source resolution is not attributed

The compared keys exclude source, which is correct for holding source *classification* fixed. However, a bound
late reading from another run or class can enter a window with values identical to the existing ones. That makes
the window's source resolution non-coherent, which the ruling lists as a dependency. With S3 settled it records
`NONE`. This under-attributes: no permanent block, and the ordinary hold remains.

It is narrow and fails toward the ordinary hold, as the ruling allows for unestablished causality. Either compare
the per-window source resolution of the closed and reassessed evidence ID sets under the closure-time provenance,
or name the gap in the handoff.

### R3 - Low: an S3-selection-only causal effect is recorded as INDETERMINATE, not CAUSAL

A reading whose only effect is to move a pinned S3 selection (the target) is reported `INDETERMINATE` when the
window result is unchanged. This fails toward the ordinary hold, as the ruling allows when attribution cannot be
established from persisted IDs. It is acceptable for S6-02a. Name it in the handoff next to the per-window
deviation.

## Implementer deviations, judged

| Deviation | Judgement |
| --- | --- |
| Per-window joint attribution, no leave-one-out | Not acceptable as is. See R1: it broadens the set and moves a permanent block's boundary. A prefix replay is enough; a full leave-one-out is not required. |
| Unbound and unrelated-role proof via a TEST-SCOPED row rewrite | Acceptable, and labelled. The roles-2 Lab cannot emit such readings, and the filter under test is the real `_attribution` filter. |
| INDETERMINATE when S3 is pending or moved and the result is unchanged | Matches the ruling. See R3. |
| Overlap regression re-settles INCONCLUSIVE; fixture regenerated | Acceptable. The test now also proves the overlap refuses continuation. |
| `writer_guard_probes.py` cut short (4/4 caught, 600 s cap) | Acceptable. I confirmed the fix diff adds no writer statement. Rule 8 passed in `check-architecture`. |
| `RESOLUTION_NOT_CURRENT` withdrawal not mutation-covered | Acceptable as defensive. If it ever fires, its withdrawal is settled only by a *new* outcome, so the reused outcome blocks continuation (REASSESSMENT_PENDING) until the basis changes. That fails closed. Low, and not raised. |

## Lows F3, F5, F6, F7

- F6: `_wire` converts aware datetimes to UTC, and plan, history and evidence stamps use it.
- F7: 401 and 403 are asserted on the `outcome` and `history` GETs.
- F3: documented in the packet.
- F5: noted for S6-02b.

All four are closed.

## Residual risk

- The R1 fix should re-run the F2 mutation checks. The packet's "every bound candidate causal" mutation is killed
  only by the INDETERMINATE test, which has a single candidate.
- The single-evaluator gap remains Low as previously rated. That is an acceptance whose earlier `decided_at`
  commits after the locked read; the S3 recompute makes the read REASSESSMENT_PENDING.
