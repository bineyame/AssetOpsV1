# S6-01b — Action, recommendation and change surfaces

Status: active (activated 2026-10-15, stacked on reviewed S6-01a `c341599b`, under the owner-absence work order; merge held for owner walkthrough and S6-01a merge); was implementation-ready
USER_REVIEW_REQUIRED: true; hold merge for owner's actual visual walkthrough
Size: M; phases: two. Branch: `task/S6-01b-action-ui` on freshly reviewed/merged S6-01a; if unmerged, label stack and hold merge.
Depends on: reviewed S6-01a store/read, closed `I-S4-01`, S1 Foundation. S5-01 is queue order only.
Planner: Codex, 2026-10-15

## Outcome and routes

One persisted Finding-linked Action is visible with its proposed trial, SYSTEM demonstration acceptance, applied or failed policy activity, and **pending** outcome after reload. Owns `I-action-ui`, `I-recommendation-ui`, `I-configuration-change-ui`, `I-action-overview-ui`, `I-action-execution-ui`, `I-action-history-ui`, and final `I-S6-01`. Close only `recommendation:1#a`, `action-overview:1#a`, `action-execution:1#a`, `action-history:1#a`, `changes:1#a` after fresh review and owner checkpoint. `sitework:1` stays S6-03; recommendation:2/3, changes:1#b/2, Action Plan/Evidence/Verification stay S6-02.

Canonical Action root `/sites/{site_code}/actions/{action_id}`; child `/execution`, `/history`, exact `?event_id=` or `?recorded_at=` preserves selection. Recommendation lives under `/sites/{site_code}/findings/{finding_id}/recommendation?revision_id=`; change panel at `/sites/{site_code}/foundation/changes/{change_id}` links the Action and exact application event. The change URL is a **non-subtab deep route** under Foundation. Bare `/sites/{site_code}/foundation/changes` returns an explicit unavailable state with a link back to Foundation, since S6-01 has no Site change index; it must not add Changes to `FoundationView`/Foundation subtabs. Parallel `/api/sites/{site_code}/...` reads come from S6-01a. Site/Finding back-links and origin revision query survive reload. No Site ActionIndex is needed: navigate from known Finding/Action. Cross-Site/unknown 404, unauthenticated 401, denied write 403. Hide Plan, Evidence and Verification tabs or show an explicit unavailable state; no empty delivered tab.

## Visible states and proof

Recommendation shows `reserve-trial-1`, the proposed reserve in percent, pinned FindingRevision/FoundationRevision and accepted analytic input IDs, and the trial limitation: a policy-sensitivity experiment with no diagnosis or prediction of runtime, saving or safety. Show the typed unavailable reason when no value is eligible. Once accepted, show the immutable accepted-recommendation snapshot and Action link **beside** separately labelled live recomputation status; a stale current basis cannot erase the accepted proposal. No mock money becomes a saving.

Accept/apply controls appear only when S6-01a returns `system_demo_capability.allowed` for the exact tenant/Site/fixture/command; label each control and resulting actor/provenance **SYSTEM demonstration**. An absent or denied capability gives a read-only unavailable reason. No client flag enables a command and no operator approval wording appears. Action Overview shows stable Action code/ID, origin FindingRevision and latest revision/episode notice side by side, pinned assessment/evidence/Foundation basis and pending outcome. Execution shows ACCEPTED, APPLIED, FAILED and state-neutral OBSERVED events, actor kind, service/job provenance, effective revision and exact change artifact. After FAILED, application remains ACCEPTED/pending; an old retry key returns FAILED, a fresh key can attempt again, and a new key on APPLIED returns typed 409 without a FAILED event. History selects exact event ID or server `recorded_at` cutoff, orders by `(recorded_at,id)`, displays both timestamps on backdated OBSERVED and never invents ActionRevision. Changes shows old/new reserve, unit, asset, effective and recorded times, old/PUBLISH/SPLIT and binding revision IDs, application event, pending/failed state, and no measured effect verdict. The Site does not claim changed operation, Lab effect or measured benefit before S6-02.

Use S6-01a's persisted fixture cases: eligible/ineligible proposal, accepted snapshot with stale live status, accepted pending, applied pending, stale expected revision with FAILED, invalid/no-change/backdate, same-key retry, concurrent command, wrong-Site 404 without event, later FindingRevision/episode, valid OBSERVED and selector conflict. Test URL selection, child navigation and reload separately for `event_id` and `recorded_at`; both selectors together show typed `ACTION_SELECTOR_CONFLICT` 422 with no silent preference. The UI must show typed errors and preserve prior successful event/artifact. A newer Finding cannot replace the Action origin. Frontend tests load S6-01a's committed `backend/tests/fixtures/s6_action_api_contract.json` (**new in S6-01a**), keyed to `D-action-records` manifest IDs; no static mock values become product data. Test absent and denied `system_demo_capability` at both 1440 and 390, plus server refusal if a command is attempted without it.

| Phase | Reviewable result | Focused proof |
| --- | --- | --- |
| 1 | Action root Overview, Execution, History and Recommendation with real reads and labelled SYSTEM command | Focused frontend route/component tests loading shared contract fixture; focused S6-01a API tests; both selector URLs, navigation, conflict and reload; capability absent/denied at 1440/390 |
| 2 and slice review | Site Foundation Changes panel, links, all empty/failed/pending states, walkthrough/evidence | Focused frontend tests; app versus v6.9 mock at 1440 and 390 for `action-overview`, `action-execution`, `action-history`, `recommendation:1`, `changes:1#a`; private-DB serve walkthrough |

Owner walkthrough tool **new**: prepare an isolated DB and fixture, `serve` API/web on private ports, print exact Site/Finding/Action/change URLs and event IDs, capture 1440/390 screenshots and a comparison table for each named panel/state, verify reload, then drop only its own DB/work directory. Reviewer follows the manifest to the persisted API, old/new Foundation and binding revisions and failed attempt; records distinct review from implementer. Owner views served pages at 1440/390 and records acceptance; coordinator holds merge until then. Phase 2 review is slice review. Focused tests per phase; one real-Postgres full backend suite on final slice revision per `backend/TESTING.md:7-31,91-130`, JUnit zero skips/failures, `tools/check-all.ps1` and registry checker.

## Checked code reality and reference

- Existing Finding route/frame and explicit later recommendation absence: `frontend/src/App.tsx:274-290`, `frontend/src/sites/FindingDetail.tsx:50-103`, `frontend/src/sites/SiteFinding.tsx:120`. Action routes/components, Changes panel and walkthrough tool are **new**.
- Existing Foundation navigation excludes Changes: `frontend/src/sites/FoundationSubtabs.tsx:32,57-60` defines only model/SLD/readiness; `frontend/src/sites/__tests__/foundationScreen.test.tsx:306,344` asserts no Changes subtab and `foundationViewFor("changes")` is null. The new change-ID deep route and bare-route unavailable state preserve this contract.
- Existing Finding API route and selected revision links: `backend/assetops_backend/finding_api.py:112-160`. S6-01a Action/Recommendation/Change APIs are **new** and required before this slice.
- v6.9 screen identities and root ownership: `frontend/mockups/v69/screen-manifest.json:306-330,1367-1452`; specific panels/tiers in `frontend/docs/architecture/v69-panel-contracts.json` and registry claim portions. The mock is content/interaction reference, not evidence of live values.

## Architect rulings

`.agent/architect-S6-01-answers.md` Q1-Q5 and M1-M3, ratified by `D-2026-10-15-s601-action-store-and-ui` in `.ai/DECISIONS.md`, govern the trial limitation, scoped demonstration controls, exact cutoff URLs, accepted snapshot and backdated OBSERVED display.

## Plan fix round 1

Folded in the Architect packet changes and plan-review M1-M3/L1-L5: accepted snapshot/live status, capability-guarded controls at both widths, selector navigation and conflict, state-neutral observation, shared API fixture, Foundation deep-route behavior and the explicit S6-02 effect boundary.

S6-02 later resolves `A-S6-verification` with `VERIFIED`, `INEFFECTIVE`, `INCONCLUSIVE`; S6-01b displays only pending outcome and policy activity. No positive Site Work list or later-window effect claim.
