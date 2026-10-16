# S6-01b phase 2 handoff (slice closeout)

- **Branch:** `task/S6-01b-action-ui`, stacked on unmerged S6-01a `c341599b`.
- **State:** not merged. The task Status is `in_review`.
- **Backend:** no change.
- **Packet:** `.agent/S6-01b-review-packet.md`.
- **Owner steps:** `.agent/S6-01b-owner-walkthrough.md`.

## What landed

- **Foundation change deep route** `/sites/{site}/foundation/changes/{change_id}`.
  - Component: `frontend/src/sites/SiteFoundationChange.tsx`.
  - Frame: `SiteFoundationChangeFrame` at the end of `shell/SiteAnalyticsFrames.tsx`.
  - Routes: `SITE_FOUNDATION_CHANGE(S)_ROUTE_PATH` and `siteFoundationChangeHref` in `shell/operatorSiteRoutes.ts`, registered in `App.tsx` before the Evidence route.
  - Client: `getChange` in `sites/actionClient.ts`.
- **Bare `/foundation/changes`:** `SiteFoundationChangesFrame` shows an explicit unavailable state with a link back. `FOUNDATION_SUBTABS` and `foundationViewFor` are untouched.
- **Action links:**
  - `SiteActionLinks.change` is new.
  - `ChangeSummary` gains `data-action-change-link`.
  - `EventDetails` links the change record (`data-action-event-change-link`).
- **Phase-1 review fold-in:**
  - M1: `SelectionNotFound` handles a 404 `ACTION_EVENT_NOT_FOUND`.
  - L1: the default `effective_from` is re-derived at click when untouched, and the exact default is asserted.
  - L2: an exact-command `granted()` test.
  - L3: a no-basis Apply reason.
  - L4: derived bodies are declared in the test header. The recorded `capability_denied` is served as recorded.
  - L5: tests for `unknown_event_404`, `apply_wrong_site_404`, the three 422 variants, `accept_replayed`, `latest_revision_after_apply`, and SiteFinding with no link.
- **Styles:** at the end of `ui/primitives.css`, scoped under `.app-frame--operator`.
- **Tools:**
  - `tools/s601b_action_walkthrough.py`: DB `assetops_s601b*`, work folder `var/s601b*`, API 8961, web 5461.
  - `tools/s601b-action-evidence.mjs`: CDP 9461.

## Proof

The review packet carries the numbers:

- 56/56 browser claims at 1440/390, plus `comparison.md`;
- layout-evidence;
- the full frontend and backend suites;
- `check-all`;
- the mutations.

## Open risks

- The Recommendation for a newer FindingRevision does not mention the Action accepted on the earlier one. This is S6-01a behaviour, set out in the owner doc as a decision candidate.
- The served walkthrough runs on the real clock, but the records carry the fixture clock. For example, the served latest-revision recommendation reads `FOUNDATION_BASIS_STALE`, while the contract reads AVAILABLE.
- There is no OBSERVED command control.

## Next

1. Fresh Claude slice review.
2. Owner walkthrough at 1440/390.
3. The coordinator holds the merge until the owner accepts and S6-01a merges.
