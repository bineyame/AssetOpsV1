# S1-03 — Organize persisted Foundation, configuration Readiness and SLD

Status: done
USER_REVIEW_REQUIRED: true
Milestone: S1 Foundation
Depends on: S1-01 and S1-02 reviewed baseline at `d8dd3e9`
Branch: task/S1-03-foundation-organization
Trigger: owner UI feedback, `.agent/owner-S1-ui-feedback-2026-10-08.md` (verbatim)
Authority: Codex Architect decision `D-2026-10-08-s1-foundation-organization`; full text `.agent/architect-S1-ui-organization-2026-10-08.md` (committed with this packet)

## Visible result

Three direct-linkable, mock-organized Kobo Foundation views (Site model, Single line diagram, Readiness) at the same selected effective period, with truthful configuration gaps and no invented observations.

## Build boundary

Recompose existing S1 read models and actions into Site model, Readiness and SLD views; replace the old `Definition | Topology | Controls` contents-row navigation and revise its guard/tests for the new three-view contract (sections 2 of the Architect decision). Preserve server APIs, validation, version/recorded-time semantics, audit IDs, snapshot download, legacy Site behavior and Lab gates. Use shared status, panel and responsive styles to match the three v6.9 references (`frontend/mockups/v69/index.html#/foundation`, `#/readiness`, `#/sld`); keep long audit material available but subordinate. No new data model, gateway health, commissioning workflow, Evidence, broad visual token rewrite, other Site domains or full V-01 activation. Do not render the mock's `Changes` destination.

## Acceptance fixture

Converted KOBO-001 at a current and earlier period; one missing reserve or missing binding state. At 1440 × 900 and 390 × 844, compare each app view side by side with its mock route and document supported panels and honest omissions. Verify navigation, URL/reload, keyboard focus, reserve/binding action placement, linked API/revision basis, no overflow and no false status or mock values. Reviewer checks changed behavior and required guards; owner checks whether the page is now organized well enough to verify S1.

## Defer

S2 gateway contact, accepted evidence and commissioning confirmation; V-01's wider Site/Lab/evidence visual pass and owner tier review remain at their existing gate. S1-01/S1-02 technical carries stay recorded and separate from this UI acceptance gate.

## Merge rule

Hold the S1-01/S1-02 merge until S1-03 lands and the owner completes the UI check; then integrate in dependency order.
