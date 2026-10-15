# S6-01a — Action store, controlled application and exact read

Status: implementation-ready
USER_REVIEW_REQUIRED: false; reopen for any owner-facing copy or UI
Size: M; phases: two. Branch: `task/S6-01a-action-store-read` from merged main, independent of LR-01/S5-01.
Depends on: merged S1 Foundation; closed `I-S4-01` reviewed FindingRevision; recorded Action lifecycle, actor and route decisions.
Planner: Codex, 2026-10-15

## Result and exact consumer

Persist one Finding-linked Action, immutable events and all rows of a reserve-SOC application. Same-Site API reloads Action detail, exact event history, recommendation and change provenance. This non-UI slice is mergeable only when a real stored demo executes accept → apply → reload and returns payloads consumed by S6-01b. A bare schema fails. Owns `I-action-store`, `I-action-read`, `I-recommendation-read`, `I-configuration-change-read`, `D-action-records`; closes no W1 panel.

## Creation, authority and state (L1, P1, P2, P7)

Use L1 model (a): a versioned server recommendation is PROPOSED for a reviewed FindingRevision; an Action is created **on acceptance**, so Action has no PROPOSED state. Recommendation key is `(tenant_id,site_id,finding_revision_id,rule_id,rule_version,asset_id)`; server acceptance key is a canonical digest of that tuple plus `ACCEPT`, unique within tenant/Site. Identical accept returns the same Action/event; same key with altered payload is 409. Allocate `action_code` with a tenant-scoped DB sequence and preserve `UNIQUE(tenant_id,action_code)`. Distinct revision/rule/asset keys permit several Actions per Finding. Each event has `UNIQUE(action_id,idempotency_key)` and payload digest; identical retry returns the original event, conflicting reuse is 409.

Recommendation value comes only from a **new**, versioned server reserve-trial rule over the pinned FindingRevision and current Foundation reserve; eligibility, delta and range are Q1. No client or mock value is authoritative. Unchanged/out-of-range output is unavailable before acceptance. Show purpose and limitation. Mock money is never a saving; an S4 consequence may appear only for its exact basis, labelled as consequence.

| Command | Precondition | Event / reduced state | Refusal |
| --- | --- | --- | --- |
| accept | reviewed persisted revision; valid recommendation; server-authorized SYSTEM demo | ACCEPTED / application pending | 401/403/404 or typed 422; no Action |
| apply | ACCEPTED; expected current Foundation ID; same Site/asset/value; prospective effective time | APPLIED only with committed new Foundation; outcome pending | FAILED same-Site attempt; stale 409, invalid/no-change/backdate 422 |
| repeat | identical command key and payload | return original Action/event/artifact | same key, different payload 409 |

FAILED is an attempt event; a new authorized apply may succeed. Reduce by `(recorded_at,id)`. `occurred_at` may be backdated for non-application activity, displayed separately, never used to reorder state. Accept/apply use server time. Do not infer Verified or human approval. With no verified operator principal, only labelled server-authorized SYSTEM demo commands run, carrying stable service principal and triggering job/command/fixture. No client, gateway or OS name becomes a human author.

## New storage and publish (P3-P5, P10)

New migration under `backend/migrations/versions/`: `action` has tenant/Site, immutable origin finding/revision, primary assessment, evidence/configuration basis IDs/digest, recommendation rule/key, action_code, created time and acceptance key. `action_event` has ID, tenant/Site/Action, kind, occurred/recorded time, actor_kind/id, source_channel, authorization_basis, triggering service/job/command/fixture, payload digest, idempotency key and typed failure code. New append-only `action_policy_change` has Action, authorized command and APPLIED event, asset/field/unit, old/new value, expected/superseded/new PUBLISH Foundation IDs, optional SPLIT ID, **every** superseded/inserted binding-set revision ID, effective/recorded time and validity. Use child rows for written IDs if arrays cannot prove same-Site FKs. Same-Site composite FKs and uniqueness; no simulator private truth. These tables/columns are **new**.

Extend S1's Site-locked `publish_configuration` callback: compare expected Foundation ID and Site against the current covering row **under the lock**. Apply under one transaction with Foundation/binding writes, artifact and APPLIED event (Q2). Stale revision returns typed `ACTION_FOUNDATION_STALE` 409; after publish rollback durably append FAILED with expected/current IDs and no effective new ID. Lock Action then Site consistently; prove concurrent commands publish once. Action effective time must be >= server recorded time and > ACCEPTED time; ordinary S1 historical publication is unaffected. Successful identical retry returns the old artifact before S1 `FOUNDATION_NO_CHANGE`. New no-change command returns typed 422 and FAILED.

## New API, stored proof and phases (P6, P8, P9)

Under `/api/sites/{site_code}` add `GET /findings/{finding_id}/recommendation?revision_id=`, `POST /findings/{finding_id}/recommendation/accept`, `POST /actions/{action_id}/apply`, `GET /actions/{action_id}?event_id=|recorded_at=`, `GET /actions/{action_id}/events?event_id=|recorded_at=` and `GET /foundation/changes/{change_id}`. Commands require server-issued recommendation key, idempotency key and expected Foundation ID; apply value/effective time are revalidated. Reads return canonical/selected IDs, origin FindingRevision **beside** latest revision/episode notice, assessment/evidence/configuration pins, exact actor/event/cutoff, Site/Finding/Action/change links and pending outcome. Event ID includes an exact recorded-order prefix; cutoff uses server recorded time and ID tie-break. Unknown/cross-Site 404, missing auth 401, denied command 403 per pre-S3 ruling. No Site ActionIndex dependency.

New versioned `D-action-records` fixture/loader runs through real accepted Finding/Foundation records with manifest IDs. Persist proposed/unavailable, accepted pending, applied pending, stale 409+FAILED, wrong Site, invalid/no-change/backdate, retry, concurrent apply, newer FindingRevision/episode, reload and backdated non-application `occurred_at`. No hand-inserted effective claim.

| Phase | Reviewable result | Focused proof |
| --- | --- | --- |
| 1 | migration, recommendation/accept, Action/event store and exact read | New Postgres store/API tests for origin, scope, uniqueness, cutoff, actor; existing `backend/tests/test_s4_finding_read_postgres.py` and `test_s1_foundation_postgres.py` |
| 2 and slice review | atomic publish, artifact, failure/race/retry and fixture/consumer API proof | New Postgres apply/fixture tests, S1 binding tests, private-DB accept/apply/reload walkthrough inspecting all written rows |

Fresh independent review per phase; phase 2 review is slice review. Focused tests each phase. On final revision run `tools/check-all.ps1`, registry checker and one real-Postgres full suite per `backend/TESTING.md:7-31,91-130` (`-n 2 --dist loadfile --no-loadscope-reorder`, JUnit zero skipped/failed, keep-awake, 20-minute cap). Merge only after review, with no unmerged UI parent.

## Checked code reality and gaps

- Existing `publish_battery_reserve`, `_publish_content_change`, SPLIT and `FOUNDATION_NO_CHANGE`: `backend/assetops_backend/sites/foundation_service.py:362-381,415-538`. Existing Site `FOR UPDATE`: `backend/assetops_backend/sites/adapters/postgres_foundation_store.py:607-620`. Expected check and atomic Action hook are **new**.
- Existing Finding API/read/lineage: `backend/assetops_backend/finding_api.py:112-160`; `backend/assetops_backend/analytics/finding_read.py:306`; `backend/assetops_backend/analytics/adapters/postgres_finding_store.py:274-291`; FindingRevision schema `backend/migrations/versions/0009_finding_store.py:64-105`. Action store/routes/tests/fixture tool are **new**. The proposed action tables at `frontend/docs/architecture/production-shaped-mvp-technical-design.md:55-56` are not shipped schema.
- Existing testing harness and full command: `backend/TESTING.md:7-31,91-130`. New tests/tools must have exact paths and lines in implementer handoff.

## Architect questions (plan follows recommendations)

1. **Q1 reserve rule:** ratify a server-only versioned bounded delta and eligibility derived from the pinned FindingRevision; refuse revisions without a justified numeric value. No implementation-chosen mock delta.
2. **Q2 publish hook:** use a narrow callback inside existing Site transaction; Action → Site lock order, no generic transaction framework.
3. **Q3 failed scope:** wrong-Site/unknown Action yields 404 without event to avoid an existence leak; FAILED only for authorized same-Site application attempts.

L2: S6-02's `A-S6-verification` must cite the lifecycle decision and define `VERIFIED`, `INEFFECTIVE`, `INCONCLUSIVE`; this slice produces no outcome. Defer Site ActionIndex (S6-03), plan/evidence/verification (S6-02), general work and human write path.
