# S6-02a fix round 2 re-review: verification core (R1 + merge of main S4-05b)

Reviewer: a fresh, independent Claude reviewer. I did not author this slice or its fixes. I reviewed worktree
`AssetOpsV1-review5`, detached at `e4f3469f` (the head of `task/S6-02a-verification-core`).

Inputs:
- `.agent/S6-02a-rereview.md` (RETURN on R1 Medium; R2 and R3 Low).
- The F2 section of `.agent/architect-S6-02a-holds-answers.md` (`D-2026-10-16-s602a-holds`).
- The "Fix round 2" section of `.agent/S6-02a-review-packet.md`, with its merge evidence.
- The fix diff `81f5c962..b1928b12` (excluding `.agent`).
- The merge resolution `b1928b12..e4f3469f` in `backend/assetops_backend/actions`.

## Verdict

**ACCEPT.** R1 is closed as the ruling requires. The merge keeps both the S4-05b stored provenance and the S6
`publish=` and verification wiring. I found one new Low (N1). It does not block.

## Checks run (what I saw)

Environment:
- Python: the main venv python.
- `PYTHONPATH`: this worktree's `backend;contracts;gateway;simulator`. `assetops_backend.__file__` resolves to
  `AssetOpsV1-review5`.
- Database: private base DB `assetops_s602arr2_test` on 127.0.0.1:55432. I created it first and dropped it
  afterwards; no `assetops_s602arr2%` database remains.

Results:
- Five files, run serially with no `-n`:
  - `test_s6_verification_holds_postgres.py`
  - `test_s6_verification_evaluator_postgres.py`
  - `test_s6_action_store_postgres.py`
  - `test_s6_action_apply_postgres.py`
  - `test_s6_action_records_postgres.py`

  They gave **40 passed** in 526 s. The JUnit file shows tests=40, failures=0, errors=0, skipped=0. That includes both
  parametrizations of `test_a_duplicate_reading_never_moves_the_overlap_boundary`, `[action-before-conflict]` and
  `[control]`. The records test compares the committed regenerated contract fixtures field by field after
  `normalise`, so the fixtures match a fresh run at this revision.
- `tools/check-agent-workflow.ps1`: passed.
- `tools/check-architecture.ps1`: passed.
  - The first run failed Rule 8 only because this worktree has no `.venv`, so the SQL extractor had no interpreter.
    Its two "vacuous" lines are a consequence of that.
  - I reran it with `ASSETOPS_GUARD_PYTHON` set to the main venv python, and it passed.
- **Not rerun:**
  - The full suite. I cite the implementer's run at `97d101d4`: 2491 passed, JUnit failures=0, errors=0, skipped=0,
    1249 s. `97d101d4..e4f3469f` touches only `.agent/`, so it is code-identical to the revision under review.
  - The mutation checks, `check-all`, and the frontend `tsc` and vitest runs. These are cited from the packet, not
    re-proven. Frontend `npm.cmd test` and `build` cannot run under this sandbox anyway.

## R1: closed

`_attribution` (`backend/assetops_backend/actions/verification.py`, `result` and `arrivals`) now works as follows:
- It groups the window's candidates by `decided_at`. `late_evidence` sorts by `(decided_at, id)`, so the groups are in
  acceptance order.
- It recomputes the window at each group's instant, starting from the closed result `was`. Reserves are held at the
  closure cutoff, as in `before`.
- It skips any group whose prefix result equals the previous one.
- It advances `prev` only on a change.

Both `before` and the replay use `closed_at`. `late_evidence` uses `decided_at > closed_at` and `window_readings` uses
`<= known_at`. There is therefore no gap between the closed basis and the first candidate prefix.

Consequences:
- A duplicate, or any reading that leaves the result unchanged, is never causal. It stays only in
  `candidate_evidence_ids`.
- The earliest causal `accepted_at` is the first prefix at which the result differs from the closed result. That is
  exactly the boundary the ruling asks for: Actions accepted after "at least one such invalidating reading".
- `hit` is still intersected with `entered`. A causal reading that is later superseded can drop out of the set. That
  only moves the boundary later, or yields INDETERMINATE, which is toward the ordinary hold.

**The same-instant joint rule is sound.** Within one instant, each member is tested alone, with the other members
excluded. Members that change the result alone are causal. Only if none does is the group recorded jointly. Every
member of a group shares one `decided_at`, so joint recording can never move the overlap boundary earlier than that
instant. A no-op member of a jointly causal group cannot broaden the timing predicate. The packet says this path is
not mutation-covered because the roles-2 Lab cannot deliver it, and that is accepted.

**The new test reproduces the re-review sequence exactly**:
1. VERIFIED and RESOLVED at 12:00.
2. Duplicate SOC "50" accepted at 12:15.
3. Conflicting "79" accepted at 13:00.
4. Evaluation at 14:00.

It asserts the following:
- CAUSAL with the invalidating set equal to the conflicting reading only.
- Candidates equal to both readings.
- An Action at 12:30 gives `PRIOR_ACTION_UNRESOLVED`.
- The control Action at 13:30 still gives `PRIOR_TRIAL_REASSESSMENT_OVERLAP`.

Both cases passed on my run.

**No new fail-open path.**
- The fix adds no writer statement. `exclude` is a read-side filter only.
- The `release_engines` fixture is test-only.
- Every new branch either removes a reading from the causal set or keeps the existing INDETERMINATE or NONE fall-backs.
  Those leave the ordinary unresolved hold in force.

## Merge resolution: correct

- `actions/service.py`:
  - `ActionService.__init__` takes `publish=` and `source=` and keeps `self.verification_ports`.
  - `source_provenance` fails closed: when unwired it returns `PROVENANCE_NOT_WIRED`, and on an exception it returns
    `PROVENANCE_UNREADABLE`.
  - Both read bodies now carry `source_provenance` for the exact pinned revision, not `demonstration`.
- `actions/composition.py`:
  - `build_action_service` passes `publish=` and `source=getattr(finding_reads, "source_provenance", None)`.
  - It then sets `service.verification_ports = verification_ports(database_url)`.
  - Diffed against main (`95d5261a`), the only additions are the S6 ones.
- `demonstration_label` is no longer used. The only hit in `backend` is main's own docstring in
  `evidence/provenance_read.py:5`, which names the retired module.
- The regenerated fixtures are plausible:
  - No `"demonstration` key remains in either S6 contract fixture.
  - `s6_action_api_contract.json` has 11 `source_provenance` blocks, all `UNKNOWN` with a `NO_POSITIVE_BINDING` reason.
    That matches the shape on main.
  - `s6_verification_api_contract.json` has 2 such blocks, normalised.
  - The large UUID churn in the action fixture is per-run IDs, which `normalise` removes.

## Findings

### N1 - Low: the prefix replay credits a group with any change since the previous candidate prefix, including one made by a non-candidate reading the rules still use

In `_attribution.arrivals`, a single-member group is marked causal whenever `result(at) != prev`. The comparison
point `prev` is the previous *candidate* prefix, not "this instant minus this group". `result` goes through `_windows`
and then `rules.window_evidence`. That function filters only roles present in `role_assets`
(`verification_rules.py:390-394`). Readings of a single power role or `generator_state` that has no frozen binding are
therefore still used. `is_bound` never makes them candidates.

If such a reading changed the window between candidate instants, the next bound reading would be credited with that
change, even an exact duplicate. That would recreate R1's earlier boundary.

Why it is Low:
- It needs a plan frozen with a required single role unbound, yet complete enough to have been VERIFIED.
- The roles-2 Lab cannot produce that, and the packet's own unbound-role proof is TEST-SCOPED for the same reason.
- The role-filter behaviour itself predates this round (F6).

Fix (optional; S6-02b or a later hardening): compare each group against `result(name, at, exclude=group_ids)` rather
than against `prev`, so only the group's own arrival is credited. Alternatively, make `window_evidence` drop readings
of roles with no frozen binding. Otherwise, name the gap beside R2 and R3 in the handoff.

### R2 and R3 (Low, carried)

These are named in the phase-2 handoff as fail-toward-hold, as the re-review allowed. No change is needed.

## Residual risk

- The same-instant one-by-one split is reasoned correct but not mutation-covered, as the packet says.
- N1 above.
- The single-evaluator gap remains Low, as rated before.
