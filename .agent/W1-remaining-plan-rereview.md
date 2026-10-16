# W1 remaining packets - plan re-review (fix round 1)

Reviewer: fresh independent Claude Reviewer, 2026-10-16. Plan re-review only. Worktree `AssetOpsV1-review5` at `c4cb8662`. Scope: Planner fix `git diff e855cedb..cb4208f7 -- tasks` against `.agent/W1-remaining-plan-review.md` F1-F5, and agreement with `.agent/architect-W1-remaining-q-answers.md` / `D-2026-10-16-w1-remaining-questions` (`.ai/DECISIONS.md:4168`). Untouched packet text not re-reviewed. Owner direction: demo speed, no wording/visual findings, only High/Medium block. No suites run.

## Verdicts

| Packet | Verdict |
| --- | --- |
| S6-03 `tasks/S6-03-site-work-list.md` | **ACCEPT** (F1, F2, F8, F9 resolved) |
| S7-01a `tasks/S7-01a-health-read.md` | **ACCEPT** (Lows F6, F7 resolved) |
| S7-01b `tasks/S7-01b-health-ui.md` | **ACCEPT** (F3 resolved; Low R2) |
| S3-02a `tasks/S3-02a-capability-read.md` | **ACCEPT** (F4, F6 resolved) |
| S3-02b `tasks/S3-02b-claim-limit-ui.md` | **RETURN** (F5 parts 1-2 resolved; new Medium R1 introduced by the route fix) |

## Checks run

- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: "Registry valid: 234 nodes, 11 linked pilot panels", exit 0. Registry not changed since the prior review (`git diff --stat e855cedb..HEAD` touches only `.agent/`, `.ai/DECISIONS.md` and the five packets).
- No suites run (per dispatch).

## Prior findings

- **F1 (S6-03) - resolved.** `tasks/S6-03-site-work-list.md:11` now reduces lifecycle with the same `actions.lifecycle` reducer as Action detail (exists on main: `backend/assetops_backend/actions/lifecycle.py:64` `reduce`, imported by `actions/service.py:18`), requires same-fence list/detail equality, shows S6-02a `RESOLVED`/`RESOLUTION_WITHDRAWN` as recorded events with no list-derived verdict; `:19` adds those fixture rows conditionally and the second-to-merge parity rerun.
- **F2 (S6-03) - resolved.** `:24` reuses `backend/tests/s6_action_records.py::build` (`:103`), runs the Performance comparison as `tools/s601b_action_walkthrough.py:19,193-198` does, and `attest` fails unless it passed.
- **F3 (S7-01b) - resolved.** `tasks/S7-01b-health-ui.md:20` names a distinct gateway per case (latest-per-gateway selection is per gateway, `postgres_gateway_access.py:174-187`), splits disk stop and recovery, adds a `deliver` fresh-receipt command run immediately before viewing with `attest` checking current receipt, and a second Site for no-source and absent/unbound battery with printed URLs (`:22`).
- **F4 (S3-02a) - resolved.** `tasks/S3-02a-capability-read.md:9` applies the `performance_api.py:51-61` gate with typed `409 PERFORMANCE_CUTOVER_CLOSED`, never `UNASSESSED`/empty; `:18` adds the closed-gate test.
- **F5 (S3-02b) - parts 1 and 2 resolved, part 3 not.** `tasks/S3-02b-claim-limit-ui.md:18` runs the S2 Evidence and Performance comparisons with `attest` failing on either, and S3-02a now names `backend/tests/s3_claim_limit_records.py::build` with a manifest (`S3-02a:17`). Part 3 (route) was replaced by a concrete route that carries the wrong identity - see R1.
- Lows F6, F7, F8, F9 and the prior Architect-question notes are carried into the packets.

## Architect agreement

All five packets agree with `.agent/architect-W1-remaining-q-answers.md`: S6-03 cursor bound to tenant/Site/half-open window/last key with max creation and event-recorded times plus Action and event counts (`S6-03:11,30`); S7-01a versioned DTO, S2 route untouched, one repeatable-read snapshot (`S7-01a:24`); S7-01b configured effective asset ID, `NOT_CONFIGURED`, foreign/superseded asset refused (`S7-01b:9,26`); S3-02a exact spans/durations under one versioned rule (`S3-02a:22`); S3-02b separate S2 section and a visible `UNASSESSED`/"no assessment selected" S3 section (`S3-02b:7,24`). No disagreement found.

## New findings

### R1 - Medium - S3-02b walkthrough URL reuses a param that already carries a different identity, and drops the required day (`tasks/S3-02b-claim-limit-ui.md:18`)

The fix cites `/sites/{id}/evidence?view=analysis&assessment=<selected-id>` (`operatorSiteRoutes.ts:120-122`). That `assessment` param is already consumed by the Evidence Analysis view as a legacy analytics assessment ID: `frontend/src/sites/SiteEvidence.tsx:190-195` passes it to `SelectedAssessmentCoverage`, which resolves it against `analytics.getDispatch(siteId)` (`SiteEvidence.tsx:844-855`, i.e. `GET {site}/dispatch`, `siteAnalyticsClient.ts:436-437`), and Performance/Finding links populate it with that ID (`SiteAnalyticsFrames.tsx:159`, `FindingDetail.tsx:237`). The S3 dispatch view selects with `day` and `revision` instead (`PerformanceDispatch.tsx:81-82`), and S3-02a requires a UTC day plus exact `assessment_revision_id`. Following the packet, one URL param would mean two identities: an S3 revision ID put there is looked up as a legacy assessment (not found), and a legacy ID arriving from existing Performance/Finding links would be sent to the S3-02a read as a revision (refused). It also contradicts the packet's own contract to keep the UTC day/window in the URL (`:7`). Not fail-open (S3-02a refuses a wrong revision), but the walkthrough step cannot show the promised ceiling as written and the identity choice will otherwise be settled in a review round. Fix (one sentence): keep `view=analysis` but carry the S3 selection in distinct params, e.g. `day=<YYYY-MM-DD>&revision=<assessment_revision_id>` matching `PerformanceDispatch.tsx:81-82`, leave the legacy `assessment` param untouched, and have the wrapper print that URL.

### R2 - Low - S7-01b stale-cadence case depends on owner pace (`tasks/S7-01b-health-ui.md:20`)

`received_at` is server-set, so the stale-cadence gateway becomes `STALE` only after 2 x cadence (`gateway_access.py:293-297`, default 60 s). If the owner opens Health within two minutes of `prepare`, that case reads `CURRENT`. `attest` checks only the fresh cases. Have `attest` also assert the stale case is `STALE` (or register it with a short cadence). `deliver` must also advance the gateway's local sequence so it becomes the latest row (`postgres_gateway_access.py:185-186` orders by `received_at DESC, diagnostic_sequence DESC`). Non-blocking.

## Fail-open check

No fix introduced a fail-open path: the S3-02a gate and identity seam close a prior one; S6-03 adds a typed choose-window state (`S6-03:13`) instead of an unbounded read; S7-01a stale-projection scoping keeps the inconsistent-selection refusal. The only unreachable walkthrough step introduced is R1.
