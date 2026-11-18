# S6-01a / S6-01b plan re-review (after fix round 1)

Reviewer: fresh Claude reviewer. I did not write the packets, the fix brief, the first review or the Architect rulings.
Reviewed: `plan/S6-01-refine` at `29f3afed`, mainly the fix-round diff `1cb19eb1..29f3afed`. That covers `tasks/S6-01a-action-store-read.md`, `tasks/S6-01b-action-ui.md`, the `tasks/README.md` rows and the registry. I checked them against `.agent/S6-01-plan-review.md`, `.agent/planner-S6-01-fix-brief.md`, `.agent/architect-S6-01-answers.md` (Q1-Q5 and "Follow-up (plan review M1-M3)") and `D-2026-10-15-s601-action-store-and-ui`. The code-reality checks were against `main`.

## Verdict: ACCEPT

No High or Medium findings remain. M1-M3 are resolved as the Architect follow-up rules. Every Q1-Q5 packet change is present, L1-L5 are resolved, and both residual risks are addressed. There are two new Low findings, and neither blocks.

## M1-M3

- **M1: resolved.** S6-01a now names `backend/assetops_backend/actions/adapters/postgres_action_store.py` (**new**) as the sole writer of `action`, `action_event`, `action_policy_change` and the Action-owned children.
  - Acceptance writes without a publish.
  - On apply, the outer transaction is opened by the Action adapter. It locks the Action, then checks idempotency and authority, then calls a caller-owned-connection `publish_configuration`. That call does not open or commit a transaction. It takes the Site `FOR UPDATE`, does the expected-ID check under the lock, and runs the S1 writes, which return every written and superseded ID. A same-connection callback then writes the artifact and the APPLIED event, and the Action adapter makes the only commit.
  - The existing S1 entrypoint is unchanged when no connection is supplied.
  - FAILED is written in a separate transaction after rollback.
  - The rule-8 additions are listed (`$pgWriters`, `$pgWritesSeen`, `$pgDriverSeen`, INSERT-only, with UPDATE, DELETE, upsert, TRUNCATE and DDL rejected), plus a reverse-ownership rejection that explicitly covers the Foundation adapter. The guard cases are listed too. This matches follow-up item 1.
- **M2: resolved.** The recommendation key and the acceptance digest now include `foundation_revision_id`. An immutable accepted-recommendation snapshot is persisted with every field the ruling lists. `GET recommendation` returns the snapshot and the Action link beside a separately labelled live status. Before acceptance, the proposal is "served from persisted inputs" and is not described as a recommendation row. S6-01b displays the snapshot beside the live status.
- **M3: resolved.** There is a state-neutral `OBSERVED` event on `POST /actions/{action_id}/observations`, limited to the fixed `DEMO_REVIEW_NOTE` code and the scoped SYSTEM capability. Its bounds are `accepted_at <= occurred_at <= recorded_at` with at most 30 days of backdating. Refusals are 422 for time, 401/403 for authority, 404 for unknown or wrong-Site, and 409 for conflicting reuse. It is idempotent, and the fixture requires a valid backdated OBSERVED with server-order proofs. S6-01b displays both timestamps.

## Q1-Q5 packet changes: all present

- Q1: the `reserve-trial-1` eligibility rule, typed unavailable reasons, the exact numeric source, boundary tests (`r+10` versus just above, 15/90 and just outside, missing or conflicting inputs, asset or basis mismatch), and an eligible plus an ineligible fixture. S6-01b shows the limitation and the unavailable reason.
- Q2: lock order, a callback that returns every ID, and tests for rollback and concurrent apply (identical and distinct keys).
- Q3: the command table separates authorized FAILED from 401/403/404, which append nothing. The fixture now lists "wrong-Site 404 **without** FAILED".
- Q4: `system_demo_capability` (`allowed`, `command`, `fixture_id`, reason) is in the read contract and re-enforced on POST. S6-01b tests the absent and denied cases at 1440 and 390.
- Q5: `ACTION_SELECTOR_CONFLICT` 422 on Action and event reads, tie tests, and S6-01b URL, navigation and reload tests for each selector.

## L1-L5 and residual risks

- L1: resolved. The table has rows for a new key on an APPLIED Action (`ACTION_ALREADY_APPLIED` 409, no FAILED) and for the state after FAILED and its retry keying.
- L2: resolved. The migration re-chains if LR-01's 0014/0015 merge first, and the review and the full suite then run on the re-chained revision.
- L3: resolved. S6-01a and S6-01b have their own README rows. `parseQueue` now yields `S6-01a, S6-01b, S6-01, S6-02, S6-03`, and `packetMeta` parses `user_review_required` as false for a and true for b, so the per-candidate `user_review_required` is no longer null.
- L4: resolved. The packets cite `backend/tests/test_s1_bindings_postgres.py`, and S6-01b defines the Changes route as a non-subtab deep route with a bare-route unavailable state, citing `FoundationSubtabs.tsx:32,57-60` and `foundationScreen.test.tsx:306,344`.
- L5: resolved. `backend/tests/fixtures/s6_action_api_contract.json` (**new**) is keyed by manifest IDs, its fields are checked in the S6-01a tests, and the S6-01b tests load it.
- Residual risks: both are addressed. If needed, the packet authors the eligible evidence through the normal ingestion path with `demonstration_label.py`. S6-01b says the Site does not claim changed operation, a Lab effect or a benefit before S6-02.

## Registry (now 226 nodes)

The fix round added two task-layer nodes:

- `I-S6-01a` requires `A-action-lifecycle`, `I-action-store`, `I-action-read`, `I-recommendation-read`, `I-configuration-change-read`, `D-action-records` and `I-S4-01`.
- `I-S6-01b` requires `I-S6-01a` and the six UI nodes.

The umbrella `I-S6-01` now requires `I-S6-01b`. Both new nodes are in `queue_baseline_nodes`, and their layered capabilities share their `task` and `open` status. The requirements are sound: `b` cannot be reached technically without `a`, and the umbrella closes only after `b`.

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0, "Registry valid: 226 nodes, 11 linked pilot panels".
- `--next-work --json`: exit 0. `status: ranked`, no global stops. The decision is `stop_owner`: LR-01 at 2.02 against `I-action-store` at 2.004, a gap of 0.79%, which is at or under 5% and so goes to the owner.
- `node frontend/docs/architecture/test_delivery_next_work.cjs`: 35/35 passed.

## New Low findings (non-blocking)

- **N1 (Low, registry semantics).** `v69-dependency-registry-pilot.json`, node `I-S6-01a`, has `"sequenced_after":["I-S5-02"]`. The checker forces this: `check_v69_dependency_registry.cjs:127-128` requires each queue task to follow the previous README row and exempts only `S6-01` and `S7-01`. Splitting the rows moved the exemption onto the umbrella, so S6-01a is now recorded as queue-ordered after the S5-02 outline, which depends on S4-04. That contradicts the S6-01a row ("independent of LR-01/S5-01") and `D-2026-10-15-owner-absence-work-order`, which places the S6-01 Action store ahead of the S4-04/S5-02 lane. It has no practical effect, because `delivery_next_work.cjs` never reads `sequenced_after` and `I-action-store` stays eligible. Fix it at the next registry or checker touch: extend the exemption to `S6-01a` (the first S6 row), or record that this queue edge is nominal.
- **N2 (Low, citation).** S6-01a cites `foundation_service.py:362-381,415-538`, but the file is 528 lines long on main. The anchors exist: `FOUNDATION_CLOCK_BEHIND` at :435, `FOUNDATION_NO_CHANGE` at :459, `SPLIT` at :475 and `joint` at :510. The correct range is `415-528`.

## Correctness spot-check: no new hole

- **Lock order.** It is always Action first, then Site. S1 never locks Action, so it cannot deadlock against S1.
- **Idempotency.** Identical retries are checked under the Action lock, before the no-change check. A distinct key on an APPLIED Action returns 409 with no FAILED.
- **APPLIED.** It is written only inside the committed publish transaction, so a rollback removes it together with Foundation, the bindings and the artifact.
- **Effective time.** It must be at or after server `recorded_at` and after ACCEPTED, so it cannot be backdated. Only the state-neutral OBSERVED can carry an earlier `occurred_at`.
- **No savings claim.** The trial limitation is stated in both packets, and "No mock money becomes a saving".

## Residual risk for the implementer (not findings)

- **Where the planner is built.** The planner closure (SPLIT, `FOUNDATION_NO_CHANGE`, `FOUNDATION_CLOCK_BEHIND`) is built in `foundation_service._publish_content_change`, not in the adapter (`postgres_foundation_store.py:607-620`). The caller-owned connection must therefore be threaded through the service entrypoint (`publish_battery_reserve`) as well as the adapter, without the Action adapter importing the S1 service in a way that breaks the `check-architecture` import rules. The implementer handoff should state the actual call path.
- **FAILED after rollback.** Because FAILED is appended after rollback in a separate transaction, a concurrent identical-key retry can arrive between the rollback and the FAILED insert. The FAILED insert must treat a `UNIQUE(action_id,idempotency_key)` hit as "return the existing event". The reducer must also never let a late FAILED revert APPLIED. Both are implied by "attempt event" but are not tested by name.
- **Candidate without SOC.** `dispatch_v3.py:291` classifies a point as CANDIDATE from PV alone, without reading SOC. Many existing Candidate segments may therefore have no usable numeric SOC above reserve + 10, which makes the authored-evidence path likely rather than contingent.

## Checks run

- Registry checker, `--next-work --json`, and the `test_delivery_next_work.cjs` run: results above.
- Citations checked with `git show main:` against the rule-8 lines, `dispatch_v3.py`, `foundation_service.py`, `postgres_foundation_store.py`, the Finding API/read/store, `FoundationSubtabs.tsx`, `foundationScreen.test.tsx`, `App.tsx`, `FindingDetail.tsx`, `SiteFinding.tsx`, `screen-manifest.json` and `backend/TESTING.md`. `demonstration_label.py` and `test_s1_bindings_postgres.py` exist, and the migration head on main is `0013_schedule_state`.
- Per the dispatch, I ran no test suites, no `tools/check-all.ps1` and no tsc. This is a plan with no code.
