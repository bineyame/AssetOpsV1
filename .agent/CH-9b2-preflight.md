# CH-9b2 pre-flight (Implementer, 2026-11-05, branch `task/CH-9b2-mill-plan` from main `92f95effb`)

Scope read: build sheet CH-9b2 unit, §1 R1-R2, §2 P2-P3, CH9b1-R (CH-9b2 bullets), CH9b1-R2, SCOPE-1; owner P1.
`B/` = `backend/assetops_backend/`, `M/` = `backend/migrations/versions/`.

## Facts

- **Migration:** next head is `0052_verification_plan_domain`, `down_revision = "0051_action_opportunity_origin"` (`M/0051_action_opportunity_origin.py:24-25`). Lane 1 re-points if it merges second.
- **P2, family column:** none needed. `rule_id` is the family: `M/0019_verification_core.py:62` `rule_id text NOT NULL CHECK (rule_id = 'reserve-trial-1')`. 0052 widens it to `IN ('reserve-trial-1','midday-productive-shift-1')` (CH9b1-R). No `0047_verification_family`.
- **P2, reserve-shaped columns on `verification_plan`** (`M/0019:48-112`), all NOT NULL today:
  `action_id` :52 (FK `action_fk` :90-91, kept), `plan_version` :53 (CHECK reserve value), `origin_finding_revision_id` :55 (FK :92-93),
  `applied_event_id` :56 (FK `(action_id, applied_event_id)` -> `action_event` :94-95), `change_id` :57, `old/new_foundation_revision_id` :58-59,
  `battery_asset_id` :60, `field` :61, `baseline_candidate_seconds` :68; windows :63-67 with 60-minute CHECKs :83-84 (`WINDOW` :44),
  `window_order` :85-86, `same_clock` :87-88; uniques keyed on `action_id` :104, :106, :108-111.
  Child tables key on `(action_id, plan_id)`: `verification_evaluation_request` :142-150, `verification_outcome` :161, :178-179, `action_event_plan_fk` :237-238.
- **P2, code that assumes the reserve shape:** `B/actions/verification.py:138-308` (`freeze`: 60-min windows, policy change, foundation revisions, S3 days), `:216-266` (plan content);
  `B/actions/verification_rules.py:28-33` (`PLAN_VERSION`, 5-min slots, 60-min window); `B/actions/adapters/postgres_action_store.py:530, 649-665, 705, 717` (plans by `action_id`, `PLAN_COLUMNS`);
  site-wide plan reader `B/chain/adapters/postgres_chain_read.py:118-123` (`_ACTION_PLANS`, no `action_id` filter: a domain plan would surface as action `None`);
  `B/chain/adapters/postgres_thread_sources.py:66-69` and `B/chain/lifecycle_run.py:45-51` (outcomes keyed by `o.action_id`); `B/estate/adapters/postgres_estate_read.py:196-199` (inner join `action`, unaffected), `:418-420` (`action_id = ANY`, unaffected).
- **APPLIED anchor for the mill:** the COMPLETE `work_event` of the case linked through `domain_action_case_link` (`B/chain/adapters/postgres_thread_sources.py:71-74`, consumed `B/chain/lifecycle_run.py:66-68`). FK targets exist: `work_event_scope UNIQUE(tenant_id,site_id,id)` (`M/0027_w4_work_cases.py:113`), `domain_action_scope` (`M/0033_w5_cold_work.py:56`), `mini_opportunity_revision_scope_uk` (`M/0030_w4_mini_decisions.py:168`).
- **P3, trigger:** reserve freeze is an explicit synchronous command (`action_api.py:268` route -> `VerificationService.freeze` `verification.py:138`), evaluate likewise (`:751`). Q2 forbids a new route, so the mill freeze is a service method `freeze_domain_plan` called at story time (DD-1) and in tests, after the case link (CH9b1-R2 order: record, complete, link, then freeze).
- **Snapshot reader:** `productive_kwh` is per ASSET subject, period operating hours (`B/chain/measures.py:44-46`); there is no separate midday measure (`B/chain/policy.py:19-21`). `SnapshotReader.latest(..., known_at)` (`B/chain/reader.py:100-109`) built by `B/chain/composition.py:42`; reached through a new `VerificationPorts.snapshots` port (`B/actions/composition.py:86-131`).
- **Triggers (W6):** `verification_plan` already carries the `chain_input_change` row trigger (`M/0047_chain_response.py:48`); new columns on it are covered. No new table.
- **Writer rule:** `postgres_action_store.py` is the sole `verification_plan` writer (`tools/checks/configuration-persistence.ps1:805-808`); the mill INSERT goes there.
- **Byte-equality proof (R1):** golden reserve-trial plan/outcome/summary bodies captured from the unchanged code at `92f95effb` (ids/times masked), committed, and asserted after the registry.

## Questions (batched; each has a default I build if not overridden)

1. **Reader-audit class of `postgres_action_store.py` and `verification.py`.** `test_ch9b1_origin_readers.py:24,27` pins both as `action` (Finding-only, must not name `origin_opportunity`). The plan's new `origin_opportunity_revision_id` column must be named by its sole writer. **Default:** keep the `action` class for the action-table code and add one narrow class `action_plan`: the file may name `origin_opportunity_revision_id` only (never `origin_opportunity_id`) and must carry the marker `CH-9b2 plan origin`; the mill freeze lives in a new `B/actions/verification_families.py` (class `both`). Non-vacuity proved.
2. **Effective day.** R2 puts the effective day (the change applied part-way through it) in the later window. **Default:** follow R2 literally; the packet notes the mixed day.
3. **Baseline look-back bound.** R2 bounds only the look-ahead (14 days). **Default:** the baseline looks back at most 14 days before the effective day.
4. **Fewer than 3 COMPLETE baseline days at freeze.** **Default:** the plan still freezes with the days found and `baseline.state = "SHORT"`; CH-9b3 then records "not judged yet". No refusal (the freeze is the apply-time record).
5. **Day grade subject.** **Default:** a day counts when every `productive_kwh` subject row of the Site that day is COMPLETE (the `SnapshotReader` weakest-row day rule, `reader.py:39-49`).
6. **Later window at freeze.** **Default:** the plan stores the candidate range only (effective day .. +13 days); the later days are chosen at evaluation (CH-9b3) by the same pure `choose_days` function L0-tested here.
7. **Target registration.** **Default:** CH-9b2 registers it, since `target jsonb NOT NULL` is frozen at freeze: `{"rule": "10*mean(later) >= 11*mean(baseline) productive_kwh[midday]", "over": "COMPLETE days of each window", "ratio": [11, 10], "declared_by": "owner 2026-11-05"}` exactly. `guardrails = {}` (BL-09, SCOPE-1).
8. **Outcome/metric widening.** `verification_outcome.action_id` is NOT NULL with `(action_id, plan_id)` FKs. **Default:** not in CH-9b2; CH-9b3 widens `verification_outcome` the same way. Flagged as a CH-9b3 size risk.
9. **Plan cardinality and coupling.** **Default:** one plan per domain Action (`UNIQUE (domain_action_id)`, no supersession for domain plans); beyond the three ruled exactly-one-of CHECKs, couple them: `action_id` <-> `applied_event_id` <-> `origin_finding_revision_id`; `rule_id = 'reserve-trial-1'` <-> `action_id` with every reserve column NOT NULL and the 60-minute window CHECKs; the mill rows use day-range windows (`baseline_end <= later_start`, `later_end - later_start = 14 days`). `plan_version` gains `midday-productive-shift-verification-1`. Actor columns: the existing SYSTEM demonstration actor, `triggering_fixture = 'productive-load-midday@1'`.
10. **`_ACTION_PLANS` reader** (`postgres_chain_read.py:118-123`). **Default:** pinned with `AND action_id IS NOT NULL`, so existing bodies stay byte-equal.
