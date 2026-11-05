# Review packet CH-9b2: the mill verification plan and freeze (lane 2, 3.0 units)

- Branch `task/CH-9b2-mill-plan`, from `1bc73ce7e` (pre-flight). Commits: `2938ed1ff` (golden captured at unchanged 0051 code),
  `cbbf3325d` (0052, registry, freeze, tests), `17bd70996` (Q10 L2), `22d73f9b1` (0019 CHECK names kept), plus this packet.
- Authority: build sheet CH-9b §1 R1-R2, CH9b1-R (Q1 = B, P1), **CH9b2-R** (binding), SCOPE-1. `B/` = `backend/assetops_backend/`.
- Migration `0052_verification_plan_domain` on `0051_action_opportunity_origin`. `main` is now `628f77b36` (CH-5b3 merged):
  it adds no migration and touches none of this slice's files, so no re-point is needed today.
- USER_REVIEW_REQUIRED: no task file exists for this unit. The slice adds no UI, so no owner walkthrough is needed. It merges after a
  Claude review ACCEPT (own review, SCOPE-1).

## Outcome delivered

- **0052** (`backend/migrations/versions/0052_verification_plan_domain.py`):
  - `verification_plan` gains `domain_action_id`, `origin_opportunity_revision_id` and `applied_work_event_id`, each with a
    scoped FK (`domain_action`, `mini_opportunity_revision`, `work_event`). The nine reserve-shaped columns lose NOT NULL only.
  - Three named exactly-one-of CHECKs: `verification_plan_one_action`, `_one_anchor` and `_one_origin`.
  - `verification_plan_family` couples the rule to its shape:
    - reserve: every reserve column NOT NULL and no domain column;
    - midday: the domain columns only, no supersession, `triggering_fixture = 'productive-load-midday@1'`, 14-day candidate
      ranges, and `baseline_end <= later_start`.
  - The 0019 window CHECKs keep their names (`verification_plan_baseline_window`, `_later_window`, `_same_clock`) and are now
    conditional on `rule_id = 'reserve-trial-1'`. `rule_id` and `plan_version` admit the new family. The table also gets
    `UNIQUE (domain_action_id)` (Q9: one plan per domain Action).
  - **Q8:** `verification_evaluation_request` and `verification_outcome` each get `domain_action_id`, `action_id` loses NOT
    NULL, and an exactly-one-of CHECK plus the domain twin FK `(domain_action_id, plan_id)` are added. The outcome also gets
    the domain supersession twin and an order index.
  - The 0044 `verification.outcome` producer now emits `COALESCE(action_id, domain_action_id)` in `action_ids`. A reserve
    outcome's subject is unchanged.
  - Downgrade refuses while any domain plan, request or outcome exists. Otherwise it restores the 0019 constraints, the NOT
    NULLs and the 0044 producer.
- **Registry** (`B/actions/verification_families.py`, class `both`):
  - `FAMILIES = {reserve-trial-1: ReserveTrial, midday-productive-shift-1: MiddayShift}`, with `family_of(plan)` failing
    closed.
  - Pure day functions: `day_grades` (weakest-row rule, `chain.reader._day_grade`), `baseline_candidates` /
    `later_candidates` (the effective day is excluded, 14 days each way), and `choose_days` (grade only, nearest first,
    returned ascending).
  - Plan pieces: `baseline_selection` (`state` COMPLETE/SHORT, found, days, grades, candidates) and `short_text`.
  - `TARGET` is the P1 rule verbatim with `ratio [11, 10]`; `guardrails = {}`.
- **Freeze:** `VerificationService.freeze_domain_plan(tenant, site, domain_action_id)` (`B/actions/verification.py`) calls
  `MiddayShift.freeze`. It has no route.
  - The effective day is the Site-local day of the first COMPLETE `work_event` of a linked case.
  - The baseline is read through the new `VerificationPorts.snapshots` port, which is the chain `SnapshotReader` wired in
    `B/actions/composition.py` (`known_at` = now).
  - The plan pins the chosen days' snapshot `(day, subject_ref, revision, input_fp)` and reads no values.
  - The later range is stored as candidates only (Q6).
  - Replays return 200 with the same plan. Refusals: 404 for an unknown Action, 409 `VERIFICATION_FAMILY_UNSUPPORTED`,
    409 `VERIFICATION_ACTION_NOT_APPLIED` and 503 `VERIFICATION_SNAPSHOTS_UNAVAILABLE`.
- **Store** (`B/actions/adapters/postgres_action_store.py`, which is still the sole writer): `DOMAIN_PLAN_COLUMNS`,
  `domain_plan_context` and `freeze_domain_plan` (advisory lock per Action). `PLAN_COLUMNS` is **unchanged**, so every reserve
  read and body keeps its shape.
- **Q10:** `B/chain/adapters/postgres_chain_read.py` `_ACTION_PLANS` reads `AND action_id IS NOT NULL`. `_ACTION_OUTCOMES`
  gets the same pin; see Known deviations.
- **Reader audit Q1** (`tests/test_ch9b1_origin_readers.py`):
  - New class `action_plan` for the action store (limit 15). The file may name `origin_opportunity_revision_id`, must never
    name `origin_opportunity_id`, and must carry the marker `CH-9b2 plan origin`.
  - `actions/verification_families.py` is added as `both` (5).

## Acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| L0 R2 day choice: gaps, LOW days, fewer than 3, 14-day look-ahead, grade only | Met | `test_ch9b2_midday_plan.py` 9 passed (adds weakest subject row, other measures, target verbatim, registry) |
| Q2: effective day in neither window | Met | L0 `baseline_candidates`/`later_candidates` exclude it. L2 has a COMPLETE effective day that is not chosen, and `baseline_end <= effective_from < later_start`, with `later_start` on the next local day |
| Q3: 14-day look-back | Met | L0 SHORT case: the day at -15 is not counted |
| Q4: SHORT freezes with "Not judged yet: only {n} of 3 fully checked days before the change" | Met (backend text) | L0 + L2 `test_short_baseline_freezes_with_the_not_judged_text`. CH-9b3 renders it (see the mock note below) |
| Q5: day counts only when every `productive_kwh` row is COMPLETE | Met | L0 `test_one_weak_subject_row_makes_the_day_not_count`. L2 day -1 has a LOW pump row and is skipped |
| Q7: P1 rule verbatim, ratio [11, 10], guardrails {} | Met | L0 `test_target_is_the_owner_rule_verbatim_and_no_guardrails`. L2 asserts the stored plan |
| Q9: one plan per Action, coupling, plan_version, SYSTEM actor, fixture | Met | L2 replay (count 1). 6 CHECK violations each named `verification_plan_family`/`_one_action` (`diag.constraint_name`) |
| Q8: request/outcome exactly-one-of + domain FK | Met | L2: neither/both refused by `<table>_one_action` on both tables. The mill plan's own domain Action is admitted, and another domain Action is refused by `verification_outcome_domain_plan_fk` |
| R1: reserve-trial bodies and rows byte-equal (plan, request, outcome, metric) | Met | `test_ch9b2_reserve_byte_equal_postgres.py` against the golden captured at unchanged 0051 code (`2938ed1ff`). The new columns are NULL on every reserve row |
| L2 freeze at apply | Met | `test_freeze_at_apply_baseline_effective_day_target_and_replay` (record, complete, link, then freeze, on real snapshot rows) |
| 0052 upgrade and downgrade | Met | `test_0052_round_trip_and_refusal`: refused with a domain plan; after removing it, 0051 has `action_id`/`field` NOT NULL and no domain column; then upgrade back |
| Q10 `_ACTION_PLANS` pin | Met | `test_q10_site_action_rows_read_no_domain_plan` |
| Freeze trigger: service method, no route | Met | `freeze_domain_plan`; no router change |
| Scoped `test_s6_*verification*`, `test_out_e*` | Met except 1 pre-existing failure | See Checks |
| Guards A, W (N, V, M) | Met | See Checks |

**Non-vacuity, each run on the committed tree and reverted with `git checkout`, with `git status` clean after:**

| Proof | Mutation | Result |
|---|---|---|
| P1 | effective day in the baseline candidates (`range(0, …)`) | L0: 2 failed |
| P2 | `choose_days` ignores the grade | L0: 4 failed |
| P3 | Q10 pin removed | the q10 L2 test failed |
| P4 | reserve target rule text changed in `verification.py` | the byte-equality test failed |
| P5 | `domain_action_id` added to `PLAN_COLUMNS` | the byte-equality test failed |
| Reader audit | `plan_names_opportunity_id`, `plan_marker` | 2 new parametrized cases, each exactly 1 violation (9 passed) |
| CHECK tests | — | assert the constraint name, so an unrelated unique or FK error cannot pass them |

## Checks run

- Focused: `test_ch9b2_midday_plan.py`, `test_ch9b2_midday_plan_postgres.py` (6), `test_ch9b2_reserve_byte_equal_postgres.py` (2),
  `test_ch9b1_origin_readers.py` (9), and `test_s6_verification_plan_postgres.py`. After the last code change at `22d73f9b1`:
  13 passed with the plan test, and the L0 and audit files passed.
- Scoped (ch9b1, out_e, s6 verification; 12 files) at `17bd70996`: 140 passed, 2 failed in 635 s.
  - `test_freeze_pins_basis_replays_and_refuses_changed_retry` failed because 0052 had renamed the window CHECK. Fixed in
    `22d73f9b1`; re-run passed.
  - `test_verified_resolves_then_late_evidence_withdraws_and_overlap_blocks` fails the S6 contract-shape fixture. It is
    **pre-existing**: CH-9b1's packet reproduced it on a detached `main`. Reserve bodies are byte-equal by the golden proof,
    so it is not caused here. Not re-run on main in this unit.
- Guards, one at a time at `22d73f9b1`:
  - `check-architecture.ps1`: passed (252 s).
  - `check-agent-workflow.ps1`: passed.
  - `tools/checks/test_chain_coherence.py`, `test_event_register.py` and `test_chain_structure.py`: 126 passed.
  - No frontend file changed, so the N, V and M guards see no change. They ran inside check-architecture.
- Polish clone `assetops_chainclone_ch9b2_test` at `22d73f9b1`:
  - create and migrate to 0052 (the polish DB has 1 reserve plan, 0 domain);
  - settle (tick COMPLETED 101 s);
  - W6 `chain_watermark_guard`: requests 46, non-200 0, unresolved [], untracked [], clock_predicates 0, file_violations 0,
    modules 127, unlisted [];
  - `chain_response_probe fresh` with `ASSETOPS_RESPONSE_STORE=on`: 43/43 stored bodies equal a fresh compose;
  - backfill b,c,d (LINKED 3);
  - collect: 85 requests, all 200;
  - COH check: every rule `0 new` (COH-2 2/2, COH-7 8/8 expected), self-check 10 pass 0 fail;
  - clone dropped (2 var files removed).
- No full suite and no demo prepare, per the testing rule.

## Mock to new: SHORT copy (MOCK DEVIATION, CH9b2-R Q4)

- **Mock:** v69 has generic pending wording, such as "Verification pending" and "outcome not yet verified". A grep of
  `frontend/mockups/v69/index.html` finds no state for "too few fully checked days before the change".
- **New:** "Not judged yet: only {n} of 3 fully checked days before the change". It is stored as `verification_families.SHORT_TEXT`
  and returned as the plan wire's `not_judged_text` when `baseline_selection.state == "SHORT"`.
- **Reason:** no verdict is claimed without 3 fully checked baseline days.
- **Owner of the UI label:** CH-9b3 R7, which must render it with the MOCK DEVIATION label and pass guard V. The demo never shows
  it: DD-1b2's F-THREADS asserts the mill plan is not SHORT.

## Known deviations

1. `_ACTION_OUTCOMES` also gets `action_id IS NOT NULL`, beyond Q10, which names plans only. This keeps estate bodies equal once
   CH-9b3 writes domain outcomes, and CH-9b3 can relax it if the estate read should show them.
2. The plan's day windows are `[local midnight(eff) - 14 d, local midnight(eff))` and `[+1 d, +15 d)`, in exact 24 h days. For a
   DST Site zone the UTC bounds are off by the DST hour; the chosen days are still by local date. Kobo has no DST.
3. Reserve dispatch stays in `VerificationService` unchanged (the registry's `ReserveTrial` entry names that path). A domain
   Action id on the reserve routes is a 404 there. No reserve read was moved, which keeps the byte-equality risk at zero.
4. `chain/lifecycle_run.py` and `postgres_thread_sources._OUTCOMES` still key outcomes by `o.action_id`. No domain outcome
   exists until CH-9b3, which must map `domain_action_id` there to reach RESOLVED_MONITORING.

## Residual risk / review focus

- 0052's `verification_plan_family` CHECK text, and whether the conditional window CHECKs match 0019 exactly. The downgrade
  restores the originals.
- The producer `CREATE OR REPLACE` is hand-written from the 0044 `_INSERT` template. Compare the two.
- `freeze_domain_plan` reads `domain_action` and `work_event` from the action store, which only reads them; the writer rule is
  unaffected (guard A passed).
- ACTIVE_CONTEXT and CODE_STATE are not edited: the coordinator owns them, as in prior lane-2 units, and no task file exists.
