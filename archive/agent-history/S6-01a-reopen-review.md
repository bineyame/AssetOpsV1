# S6-01a reopen review - `D-2026-10-15-s601-reopen`

Reviewer: fresh Claude reviewer (did not author). Worktree `AssetOpsV1-review4`, branch `review/S6-01a-reopen` at `b82140d8`; diff `868a98b8..b82140d8` (code `586d5fe1`, closeout docs `b82140d8`). Scope limited to the reopen items listed in the dispatch.

## Verdict

**Accept.** No High or Medium findings. Three Low notes below; none block.

## Checks run (by me, on `b82140d8`)

- `assetops_backend.__file__` = `AssetOpsV1-review4\backend\assetops_backend\__init__.py`.
- Focused: `test_s6_action_rule.py`, `test_s6_action_store_postgres.py`, `test_s6_action_records_postgres.py`, `test_s6_action_apply_postgres.py` on private base `assetops_s601arr_test` -> **81 passed** (113 s). This includes the contract-fixture normalised-equality assertion. (A first attempt errored 21 at setup because the base DB did not exist yet; created it and reran. Not a code issue.) Base DB dropped afterwards; no `assetops_s601arr%` databases remain.
- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed. `tools/checks/configuration-persistence.ps1` (rule 8): exit 0.
- Full suite not rerun: cited implementer run on `586d5fe1` (the code revision under review; `b82140d8` adds docs only) - 2210 passed in 546 s, JUnit 2210 / 0 skipped / 0 failed.
- Mutations not repeated; the implementer's four (guard releases all, APPLIED treated as resolved, trial lock removed, store guard skipped) are cited and map onto the tests I read.

## Ruling items

| Item | Result |
| --- | --- |
| Prior Actions always visible | Met. `recommendation()` reads `actions_for_finding` right after currentness and before `rule_inputs`; no later branch drops `prior_actions.items`. Covered: stale basis (store test), later revision with live AVAILABLE (F04 + recorded-clock fixture), `FINDING_NOT_CURRENT` on a closed source, served-clock stale fixture. R5: a `None` from `rule_inputs` now yields `LIVE_RECOMPUTATION_FAILED` instead of 404 (see L1). Each item carries its own origin revision ID/number, `is_selected_revision` (true only for its own revision), application state, outcome state, `unresolved`, exact links. |
| R1 - every post-acceptance state blocks | Matches the ruling. `lifecycle.reduce` gives PENDING (FAILED leaves PENDING) or APPLIED; outcome is always PENDING in S6-01. The ruling forbids treating a completed verification as release until S6-02, so `UNRESOLVED_APPLICATION = (PENDING, APPLIED)` is the correct reading. S6-02 owns the release. |
| R2 - scope | Matches. Store guard and lock: same Site, Finding (any revision), asset, field, `reserve-trial-1`, excluding the identical key. Read/service: when the live rule offers no key the block is reported for any asset; since nothing is acceptable then, this only changes the reason (409 PRIOR_ACTION_UNRESOLVED with `live_status` vs 422), which is what the ruling asks for. A selected revision with its own Action and no new key shows ACCEPTED and no block. |
| 409 payload; refusals write nothing | Met. `code`, `blocking_action_id`, `blocking_action_code`, `origin_finding_revision_id`, `origin_revision_no`, `links`, `blocking_actions`, `live_status` (separately labelled). Store guard raises before `nextval`, inside the transaction, so rollback writes nothing and consumes no code; tests assert unchanged counts (store, F04, records `len(action) == 2`). |
| Identical retry returns its Action | Met. `action_for_recommendation` replay runs before evaluation and before the service guard; in the store the replay check runs under the locks before the guard. F04 test `again` -> 200, same ID. |
| Atomic recheck lock | Sound. Every accept takes `action-trial:<site:finding:asset:field:rule>` then `action-accept:<site:key>`; a key determines its trial, so the order is total and accept-vs-accept cannot deadlock. Apply takes the Action row `FOR UPDATE` then the S1 Site lock and never requests either advisory lock; accept takes no Action/Site row locks (only FK key-share on referenced rows, as before), so no cycle with apply. The write transaction is READ COMMITTED, so the guard's post-lock SELECT sees a rival's committed insert. `hashtext` collisions only over-serialise. |
| R3 - store-level race proof | Adequate. The real race is two accepts that both pass the unlocked service pre-check (e.g. revision 1 in flight when revision 2 lands); the protection lives entirely in `store.accept`, which the test drives with two real server proposals on two revisions, the service's own `_prior_guard`, a barrier and a 1 s hold after the check. The remove-lock and skip-store-guard mutations both fail it. Driving it through the service is not possible without a timing hook, and would not test more. |
| Contract fixture, three new cases | Faithful (inspected the JSON). `latest_revision_after_apply`: newer revision, PRIOR_ACTION_UNRESOLVED, proposal null, capability `allowed=false`, live AVAILABLE, prior item origin revision 1 / `is_selected_revision=false` / APPLIED / outcome PENDING / exact link. `..._served_clock_stale`: same, live `FOUNDATION_BASIS_STALE`. `accept_newer_revision_prior_action_unresolved`: 409 with the full typed detail and live AVAILABLE. NOTES `prior_actions` and `PRIOR_ACTION_UNRESOLVED` present. |
| Rule 8 | Unchanged and correct: the reopen adds only SELECTs and `pg_advisory_xact_lock`; no new writer or table. Guard passes. |

## Findings

- **L1 (Low, test gap) - `service.py:181-182`, R5 path untested.** `LIVE_RECOMPUTATION_FAILED` is never exercised; `rule_inputs` returns `None` only when the revision row is missing, which currentness has just confirmed, so it is reachable only by a race. The change also turns a former 404 into a 200 UNAVAILABLE body even with no prior Actions. Acceptable as defensive behaviour; a unit test with a stub store returning `None` would pin it. Not an acceptance gap.
- **L2 (Low, packet wording) - `.agent/S6-01a-review-packet.md` R2.** Says field `battery_reserve`; the code and fixture use `reserve-state-of-charge` (`reserve_trial.FIELD`). Correct the packet text.
- **L3 (Low, residual) - `service.py:168-185`.** The read is several separate read transactions (currentness, `actions_for_finding`, `rule_inputs`, `actions_for_revision`), as before. An accept landing between them can make one response's `accepted` and `prior_actions` disagree momentarily; next read is consistent. No action required for S6-01a.

## Residual risk not named in the packet

- `lock_timeout=5000 ms` now also bounds the trial lock; a pile-up of accepts on one Finding beyond 5 s surfaces as store-unavailable rather than a refusal. Not plausible in the demonstration fixture.
- `prior_action_block` can be non-null alongside `state=ACCEPTED` if a selected revision with its own Action ever has a different live key on offer; S6-01b should key its notice on `state` first, then `prior_action_block`.
