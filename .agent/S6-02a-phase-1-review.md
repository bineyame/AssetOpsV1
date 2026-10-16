# S6-02a phase 1 review (verification core)

Reviewer: fresh independent Claude reviewer (did not author the slice). Branch reviewed `review/S6-02a-phase-1` at
`854f1ca4`, diff `07de54ac..854f1ca4`, worktree `AssetOpsV1-gap-planning`. Inputs: packet
`tasks/S6-02a-verification-core.md` (with the Architect rulings and coordinator R1/R2), both Architect answer files,
the four plan/architecture reviews, the phase-1 brief and handoff.

## Verdict

**Accept with one Medium fixed on the branch (F1).** Everything else is Low, or carried into phase 2. The migration,
the battery-scoped lock, the rules module, roles-3 and Lab profile v4, and VERIFY scoping match the rulings. F1 is a
small freeze-time check, but it guards an immutable plan field that phase 2 cannot repair.

## Checks run (what I saw)

Environment: main venv python, `PYTHONPATH` = this worktree's `backend;contracts;gateway;simulator`
(`assetops_backend.__file__` and `assetops_simulator.__file__` both resolve into `AssetOpsV1-gap-planning`).
`ASSETOPS_GUARD_PYTHON` = the same python. Private base DB `assetops_s602ap1rev_test`, dropped afterwards. All runs
were serial, with no `-n`.

- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed.
- `pytest test_s6_verification_rules.py test_s6_verification_plan_postgres.py test_s3_role_vocabulary.py -q`:
  **60 passed, 1 failed** in 903 s (the machine was memory-starved). The failure was
  `TestBatteryScopedLock::test_two_findings_on_one_battery_race_to_one_unresolved_trial`. My `tail` cut off the
  assertion text, so I did not capture the cause.
  - That class rerun alone: 1 passed (124 s). The whole `test_s6_verification_plan_postgres.py` rerun: 5 passed (74 s).
  - See F5. The likely cause is the store's 5 s `lock_timeout` while the first thread holds the trial lock plus a
    1 s sleep under memory pressure, which fails closed. That is a likely cause, not a proven one.
- `pytest test_s6_action_store_postgres.py -q`: **8 passed** (67 s). This covers the battery-hold change.
- **Not run (owed):**
  - The writer-guard probe corpus (`tools/writer_guard_probes.py`). The implementer's run was interrupted before it
    reached the new verification probes, and the dispatch forbade a corpus run here. The five new probes (plan
    update, outcome delete, binding upsert, reverse metric insert, plan insert control) are therefore unproven.
  - The full backend suite and `check-all` (not phase-1 scope).
  - The host test `test_interval_declarations_survive_central_acceptance` (Lab run plus gateway, too heavy for this
    machine today). I read it: it asserts accepted rows keep INTERVAL_MEAN 5-minute spans per power role and
    5-minute SOC samples.
  - No mutation checks of my own. The implementer's five kills are cited, not re-proven.

## Findings

### F1 - Medium (acceptance gap): the baseline's "old" FoundationRevision is not tied to the applied change

`backend/assetops_backend/actions/verification.py:145-154`. Freeze accepts any single FoundationRevision that
covers the whole baseline, provided it differs from the change's new revision. It never checks that this is the
revision the Action changed *from*: the change's `split_foundation_revision_id` or
`superseded_foundation_revision_id`, or at least a revision whose battery reserve equals `change.old_value`.

Take a baseline placed before an unrelated intervening publication: R0 covers the baseline, R1 is published later
(any content change), and the Action then moves R1 to R2. Freeze records R0 as `old_foundation_revision_id`. The
plan then compares an R0-era window with an R2-era window and labels it the old/new pair.

- The packet requires "old/new covering FoundationRevision", and the Architect requires a baseline "under the old
  covering FoundationRevision" with no policy change.
- The plan is immutable and the evaluator trusts its frozen basis, so phase 2 cannot repair this, and a later
  VERIFIED could rest on a confounded comparison.

Fix: in freeze, refuse with `VERIFICATION_FOUNDATION_NOT_COMPARABLE` unless the baseline's covering revision is the
change's split or superseded revision. Add a Postgres test with an intervening revision (refused) next to the
existing pass case.

### F2 - Low (deviation, phase-2 obligation): freeze and later binding do not gate on S3 currentness

`verification.py:155-168` and `:284-291`. Freeze pins each day's latest DEFAULT selection, and later-selection
binding does the same, even when S3's own `dispatch_read.derive_status` would report it PENDING, STALE_PROJECTION or
FAILED. The test binds at 11:00 on the later window's own day, so it binds a selection of a day that has not
closed.

This is **not fail-open in phase 1**: no verdict exists yet, and the plan pins selection seq, run, input and
configuration digests, so staleness can be detected later. It becomes fail-open only if phase 2 forgets to check.

- Required in phase 2: the evaluator recomputes S3 status for both pinned windows and returns REASSESSMENT_PENDING
  unless they are CURRENT.
- Cheap now: refuse freeze unless every baseline day is CURRENT, and refuse binding before `later_end` has passed
  and the day is CURRENT.

### F3 - Low (deviation, needs Architect acknowledgement): the "later run has begun" cutoff is approximated

`postgres_action_store.py:509` (`_accepted_count`). Only accepted later-window evidence counts. The central database
has no Lab run table, so the run-start half of `D-2026-10-16-s602-questions` Q3 cannot be observed centrally. This
is a reasonable approximation. It fails closed in one direction: it counts any role and any asset, and an interval
ending exactly at `later_start` counts too.

The gap is a later run that has started but whose reports are not yet accepted. Ask the Architect to accept
"first accepted later-window report" as the observable cutoff, or name a public run-start signal. A possible proxy
is any received batch with an envelope inside the window, accepted or not.

### F4 - Low: the later-selection command takes an idempotency key it ignores, and does not check the plan head

`action_api.py:42` and `verification.py:279-298`. `BIND_FIELDS` requires `idempotency_key`, but replay is decided
only by the selection digest, so the key is never stored or compared. A binding can also be appended to a
superseded plan.

Either drop the field or persist and compare it, as freeze does. Refuse binding to a plan that is not the head.

### F5 - Low: race test flaked once under memory pressure

`backend/tests/test_s6_verification_plan_postgres.py` (`TestBatteryScopedLock`). It failed once in the long
combined run and passed twice in isolation. The probable cause is the 5 s `lock_timeout` in
`PostgresActionStore.__init__` while the first thread sleeps inside the lock. If so, it fails closed (503), not as
a double accept, but I did not capture the actual `out` value.

The phase-2 evaluator will share this lock. Consider printing `out` on failure, or shortening the sleep.

### F6 - Low: window evidence picks SOC, generator and PV assets from whichever asset reported, not from the plan

`verification_rules.py:394-401,417`. `battery_soc` is not filtered to the plan's `battery_asset_id`, and
`generator_*` and `pv_available_power` are not filtered to bound assets. Roles-2 and roles-3 bind SOC with ONE
cardinality and `validate_bindings` ties SOC to the reserve battery, so this is safe today. A multi-generator or
multi-PV Site is always AMBIGUOUS, which is INCONCLUSIVE and fails closed. Pass the plan's battery and bound assets
in phase 2.

### F7 - Low: timestamp format is mixed

Rules payloads use `...000000Z`, while plan and other fields use `+00:00` (handoff deviation). Both parse as the
same instant. Pick one format before the S6-02b fixture is handed off.

### F8 - Low (note): the API contract fixture shows a state the API can no longer reach

`backend/tests/s6_action_records.py:282-301` writes the second same-battery Action through the store with a
pass-through guard, so `s6_action_api_contract.json` now shows two unresolved Actions on one battery. That is
acceptable as S6-01 history. Label it as a pre-S6-02a state so S6-02b's UI does not treat it as a live path.

## Confirmed as built (no finding)

- **Migration 0019.**
  - All five tables have the `ledger_append_only` trigger.
  - Window CHECKs: exactly 60 minutes, starting on a 300 s epoch boundary. Same-clock CHECK, and order CHECK
    `baseline_end <= effective_from <= later_start`.
  - Every reference is a same-Site composite FK. The supersede chain uses `(action_id, id)` FKs, with `UNIQUE
    (supersedes_plan_id)`, one root per Action (partial unique index), and no self-reference.
  - Idempotency is `UNIQUE (action_id, idempotency_key)`.
  - The outcome enum has exactly three values, and `GUARDRAIL_FAIL` is allowed only on INEFFECTIVE.
  - Downgrade refuses once plans or resolution events exist. The passing Postgres test confirms the database
    itself rejects plan UPDATE, DELETE and a misaligned-window insert.
- **`action_event` widening.**
  - RESOLVED and RESOLUTION_WITHDRAWN require `EVALUATE`, `SYSTEM_JOB`, `service:verification-evaluator`,
    `SYSTEM_VERIFICATION_EVALUATOR`, a non-null `triggering_job`, and non-null plan and outcome FKs.
  - Every other event must have null plan and outcome IDs. The existing `_append_event` columns cannot satisfy
    `SYSTEM_JOB`.
  - Nothing writes these kinds yet. `lifecycle.reduce` and `is_unresolved` are unchanged, as phase 1 scopes.
- **Battery-scoped lock.** One key, `action-trial:tenant:site:asset:field:rule`, is used by accept, freeze and
  binding. The guard reads every Action at that scope on any Finding.
  - The Recommendation read and the accept pre-check use the same scope. With no live offer, the scope is every
    battery of the Site, which fails closed.
  - The changed behaviour (a second Finding on the same battery gets a typed 409 and no Accept capability) is
    asserted in `test_s6_action_store_postgres.py`.
  - Accept's lock order (trial lock, then accept lock) is preserved, and apply takes neither lock.
- **Rules.** All arithmetic uses exact Fractions.
  - Each window is twelve half-open slots. Power is INTERVAL_MEAN only; whole-slot or exact-partition coverage is
    accepted, and gaps, overlaps, boundary-crossing readings (no clipping), POINT_ONLY readings, non-GOOD quality,
    wrong units, negative or non-finite values all give UNKNOWN.
  - SOC must be sampled exactly at each slot start and at the window end. A reserve change mid-slot makes the slot
    UNASSESSABLE. Each below-reserve slot counts 300 s.
  - The 10% and 2-point bands are inclusive, a zero baseline requires a zero later value, and a missing load never
    shrinks the total.
  - Comparability treats UNKNOWN as overriding FAIL.
  - Targets clip to the window. OPEN_BOUND or INDETERMINATE time inside the window makes the result INCONCLUSIVE.
    Cross-midnight time from the previous day is counted (`required_days` uses the 6 h bracket). The comparison is
    `4*later <= 3*baseline`.
  - Accepted evidence `source_time` equals `interval_end` (contract `source_envelope.py:65`), so the
    `source_time >= lo` reads catch boundary-crossing intervals.
- **Roles-3 and Lab v4.**
  - Critical-load roles are LOAD/kW/ONE. `BINDING_CRITICAL_LOAD_MISMATCH` ties them to the first
    `critical-load-priority` member.
  - `verification-readiness-1` provides Lab and real-Site messages for roles-3 only, and the default publication
    set stays roles-2.
  - Mini-grid v4 only adds a measurement (requested power taken from `demand:<load>`). Profile v4 publishes
    5-minute interval power, 5-minute SOC and status with no dropout, plus `clinic-meter/requested-power` and
    `delivered-power`.
  - Residual risk: v4 power channels keep v3's dropout rates, so a replay window can lose a slot and come out
    INCONCLUSIVE. Phase 2's manifest must pick seeds and windows that prove completeness.
- **VERIFY.** The grant must list `VERIFY` explicitly, scoped to tenant, Site and the fixture record of the Action's
  origin Finding. Routes check it before reading the body (403 or 404). The command freezes a plan or binds a
  selection, and never supplies a metric, verdict or event.
- **Rule 8.** The five tables are added to `$actionTables`, so the ninth writer is the only writer and no tenth
  writer appears. The probes exist but are unproven (see "Not run").

## Residual risk not in the packet

- Phase-1 Postgres tests never reach a *complete* window: the S4 case Site binds roles-2. The positive evidence path
  (roles-3 Site, accepted v4 data, `complete=True`, comparability PASS) is proven only by unit tests, and by the
  host acceptance test that I did not run. Phase 2's replay manifest must close this.
- The battery-scoped lock is now shared by accept, freeze, binding and (soon) the evaluator, under a 5 s
  `lock_timeout`. Contention fails closed as 503, which the demo scripts should expect.
