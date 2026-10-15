# S6-01b — Action, recommendation and change surfaces

Status: implementation-ready
USER_REVIEW_REQUIRED: true; hold merge for owner's actual visual walkthrough
Size: M; phases: two. Branch: `task/S6-01b-action-ui` on freshly reviewed/merged S6-01a; if unmerged, label stack and hold merge.
Depends on: reviewed S6-01a store/read, closed `I-S4-01`, S1 Foundation. S5-01 is queue order only.
Planner: Codex, 2026-10-15

## Outcome and routes

One persisted Finding-linked Action is visible with its proposed trial, SYSTEM demonstration acceptance, applied or failed policy activity, and **pending** outcome after reload. Owns `I-action-ui`, `I-recommendation-ui`, `I-configuration-change-ui`, `I-action-overview-ui`, `I-action-execution-ui`, `I-action-history-ui`, and final `I-S6-01`. Close only `recommendation:1#a`, `action-overview:1#a`, `action-execution:1#a`, `action-history:1#a`, `changes:1#a` after fresh review and owner checkpoint. `sitework:1` stays S6-03; recommendation:2/3, changes:1#b/2, Action Plan/Evidence/Verification stay S6-02.

Canonical Action root `/sites/{site_code}/actions/{action_id}`; child `/execution`, `/history`, exact `?event_id=` or `?recorded_at=` preserves selection. Recommendation lives under `/sites/{site_code}/findings/{finding_id}/recommendation?revision_id=`; change panel at `/sites/{site_code}/foundation/changes/{change_id}` links the Action and exact application event. Parallel `/api/sites/{site_code}/...` reads come from S6-01a. Site/Finding back-links and origin revision query survive reload. No Site ActionIndex is needed: navigate from known Finding/Action. Cross-Site/unknown 404, unauthenticated 401, denied write 403. Hide Plan, Evidence and Verification tabs or show an explicit unavailable state; no empty delivered tab.

## Visible states and proof

Recommendation shows server rule/version, proposed reserve value, basis FindingRevision, purpose/limit and no mock savings. If rule cannot produce a valid value, show unavailable reason. Acceptance control is **labelled SYSTEM demonstration command**, never human approval. Action Overview shows stable Action code/ID, origin FindingRevision and latest revision/episode notice side by side, pinned assessment/evidence/Foundation basis and pending outcome. Execution shows ACCEPTED, APPLIED and FAILED events, actor kind, service/job provenance, effective revision and exact change artifact. History selects event ID or recorded cutoff, distinguishes backdated occurred time, and never invents ActionRevision. Changes shows old/new reserve, unit, asset, effective and recorded times, old/PUBLISH/SPLIT and binding revision IDs, application event, pending/failed state, and no measured effect verdict.

Use S6-01a's persisted fixture cases: proposed/unavailable, accepted pending, applied pending, stale expected revision with FAILED, invalid/no-change/backdate, same-key retry, concurrent command, wrong Site, later FindingRevision/episode, exact event/cutoff and reload. The UI must show typed errors and preserve prior successful event/artifact. A newer Finding cannot replace the Action origin. The `D-action-records` manifest supplies exact IDs. Do not use static mock values as product data.

| Phase | Reviewable result | Focused proof |
| --- | --- | --- |
| 1 | Action root Overview, Execution, History and Recommendation with real reads and labelled SYSTEM command | Focused frontend route/component tests; focused S6-01a API tests; reload and event selection |
| 2 and slice review | Site Foundation Changes panel, links, all empty/failed/pending states, walkthrough/evidence | Focused frontend tests; app versus v6.9 mock at 1440 and 390 for `action-overview`, `action-execution`, `action-history`, `recommendation:1`, `changes:1#a`; private-DB serve walkthrough |

Owner walkthrough tool **new**: prepare an isolated DB and fixture, `serve` API/web on private ports, print exact Site/Finding/Action/change URLs and event IDs, capture 1440/390 screenshots and a comparison table for each named panel/state, verify reload, then drop only its own DB/work directory. Reviewer follows the manifest to the persisted API, old/new Foundation and binding revisions and failed attempt; records distinct review from implementer. Owner views served pages at 1440/390 and records acceptance; coordinator holds merge until then. Phase 2 review is slice review. Focused tests per phase; one real-Postgres full backend suite on final slice revision per `backend/TESTING.md:7-31,91-130`, JUnit zero skips/failures, `tools/check-all.ps1` and registry checker.

## Checked code reality and reference

- Existing Finding route/frame and explicit later recommendation absence: `frontend/src/App.tsx:274-290`, `frontend/src/sites/FindingDetail.tsx:50-103`, `frontend/src/sites/SiteFinding.tsx:120`. Action routes/components, Changes panel and walkthrough tool are **new**.
- Existing Finding API route and selected revision links: `backend/assetops_backend/finding_api.py:112-160`. S6-01a Action/Recommendation/Change APIs are **new** and required before this slice.
- v6.9 screen identities and root ownership: `frontend/mockups/v69/screen-manifest.json:306-330,1367-1452`; specific panels/tiers in `frontend/docs/architecture/v69-panel-contracts.json` and registry claim portions. The mock is content/interaction reference, not evidence of live values.

## Architect questions (plan follows recommendations)

1. **Q4 UI command exposure:** recommend a clearly marked demo-only acceptance/apply control when server authorizes the SYSTEM fixture; otherwise show read-only unavailable. No proxy human approval.
2. **Q5 selected cutoff URL:** recommend `event_id` preferred when selected, `recorded_at` alternative; reject both together with typed 422 rather than silently choosing.

S6-02 later resolves `A-S6-verification` with `VERIFIED`, `INEFFECTIVE`, `INCONCLUSIVE`; S6-01b displays only pending outcome and policy activity. No positive Site Work list or later-window effect claim.
