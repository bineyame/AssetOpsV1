# W1-UX-07 — full v69 left menu with unavailable entries

Status: active (2026-10-17, from main). Size S, one phase plus fresh review. Frontend (and guard) only. USER_REVIEW_REQUIRED: owner sees it in the combined W1 walkthrough; fresh independent review is the merge gate.

Authority: owner decision `.agent/owner-rail-decision-2026-10-17.md` (verbatim); Architect `D-2026-10-17-w1-rail` (`.agent/architect-W1-UX-07-answers.md`) is the contract: exact groups/labels/order from `frontend/mockups/v69/screens.js` ROOTS and `rail()` (OPERATIONS, INTELLIGENCE, WORK, ASSURANCE, BUSINESS, ADMIN); only Sites (`/sites`) and Findings (`/findings`) live; every other root rendered as an unavailable list item with visible "Not available yet", muted but readable, accessible name including label and status, no href/route/handler, not focusable as a link; the workspace footer and 390 px behaviour as ruled.

Scope: `frontend/src/shell/OperatorShellLayout.tsx` and `NavRail` (unavailable item support), CSS, `tools/checks/navigation-truthfulness.ps1` and its tests so an unavailable item can never become a dead link and a live item can never point at a missing route, the existing rail tests (`operatorRouteFrames.test.tsx:234` "OPERATE" group expectation updated to the ruled inventory), the W1 vocabulary scan on the rail, 1440/390 captures beside the mock rail with `tools/evidence-checks.mjs`, and a short new part in `.agent/W1-UX-combined-owner-walkthrough.md` telling the owner what to look for in the menu. Lab rail unchanged.

Proof: focused tests, `npx.cmd tsc --noEmit`, full `npm.cmd test`, `tools/check-all.ps1`, captures. No backend change.
