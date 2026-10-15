# S6-01b phase 1 handoff

Branch `task/S6-01b-action-ui` (stacked on unmerged S6-01a `c341599b`). Commits: `f538dc56` (build) and the tests commit after it. Not merged. Task Status is unchanged (`active`). No backend change.

## What landed

- **Client** `frontend/src/sites/actionClient.ts`. It covers the recommendation GET, the Action GET, the events GET (`event_id`/`recorded_at` passed as given), and the accept/apply POSTs.
  - Every refusal is a typed `Refusal {http, code, message, detail}`. A plain-string `detail` (the 404 on a wrong Site) is handled too.
  - `system_demo_capability` is optional in the types. Absent or `allowed:false` means read-only.
- **Shared words** `frontend/src/sites/actionPresentation.tsx`:
  - `granted()` requires `allowed === true` and the exact command.
  - `TrialLimitation` gives plain copy keyed by `POLICY_SENSITIVITY_TRIAL_ONLY`. The server text says "running", which is a banned product word, so it is used only as the fallback for an unknown code.
  - `Ref` renders exact IDs and codes with `data-vocabulary-exempt="source-reference"`.
  - `RefusalPanel` and `CommandRefusal`.
- **Recommendation** `frontend/src/sites/SiteRecommendation.tsx`. It is a new Finding child view: `FINDING_CHILD_VIEWS` now includes `"recommendation"` (`shell/operatorSiteRoutes.ts:195`), and it is wired in `SiteFindingFrame` (`shell/SiteAnalyticsFrames.tsx`).
  - Proposal state: shows the proposal, the pinned Finding, Foundation and primary-assessment IDs, and the input IDs and digest.
  - Unavailable state: shows the typed reason.
  - Accepted state: shows the snapshot and Action link beside the labelled "Live recomputation".
  - Accept control: `Accept trial (SYSTEM demonstration)`, with a fresh `ui-` key each time.
  - A 409 `ACTION_ACCEPTANCE_CONFLICT` is shown as "already accepted" with a link to `action_id`.
  - Money is a labelled link to `siteFinancialsHref(finding, revision)`, with no amount.
- **Finding "What to do next"** (`sites/SiteFinding.tsx`) now links to the Recommendation at the exact version. The old "Not yet available..." copy is gone, so `tools/checks/missing-claim-baseline.json` dropped that entry and the total went from 12 to 11.
- **Action root** `frontend/src/sites/SiteAction.tsx` and `SiteActionFrame` (end of `shell/SiteAnalyticsFrames.tsx`).
  - Routes: `SITE_ACTION_ROUTE_PATH`, `SITE_ACTION_VIEW_ROUTE_PATH` and `siteActionHref` in `operatorSiteRoutes.ts`, registered in `App.tsx`.
  - Sections: Overview, Application (`/execution`) and History. "Execution" is a banned product word, so only the URL keeps it.
  - The selector query is carried in every section link. An unknown section gets a refusal panel. There are no Plan, Evidence or Verification tabs; one sentence says they belong to the verification step.
  - Two reads, Action and events, each with its own loading sentence. Both sentences were added to `test/settled.ts`.
  - The last successful read is kept when a re-read or a command fails.
  - Apply sends the accepted value, `application_basis.current_foundation_revision_id` and `effective_from`. `effective_from` defaults to the next UTC midnight after `read_at` and is editable (UTC datetime-local). Each click sends a fresh key.
  - The apply control appears only on the LATEST selection, only while PENDING, and only with an `APPLY` grant.
- **Tests** `frontend/src/sites/__tests__/siteAction.test.tsx` (22). They import `backend/tests/fixtures/s6_action_api_contract.json` and stub `fetch` with the recorded responses, so they exercise the real client.
  - Two bodies are derived from the fixture, and the test file documents both:
    - The capability-absent read is a recorded body with the field deleted.
    - The events read at the ACCEPTED `event_id` is the recorded latest events cut through that event, with the recorded selection. The fixture has an Action read for that `event_id` but no events read.

## Proof

- `npx tsc --noEmit` clean.
- Focused and adjacent vitest: 8 files, 213 passed. Files: siteAction, siteFinding, siteFindingHistory, siteFindingEvidence, foundationScreen, t028Screens, t028Vocabulary, siteFinancials.
- `tools/check-architecture.ps1` passed; `tools/check-agent-workflow.ps1` passed. A temporary `.venv` junction was used and then removed.
- `missing-claim-scan` passed.
- Mutations (reverted; tree clean):
  - Making `granted()` ignore `allowed` fails 4 tests: capability denied or absent, at 1440 and at 390, for both Recommendation and Application.
  - Dropping the selector from the section links fails both selector navigation/reload tests.
- The 1440/390 tests set `innerWidth`. jsdom has no layout, so they prove the same structure at both widths, not rendered layout.
- Not run: the full frontend suite, the backend, layout evidence (phase 2) and `npm run build`.

## Next (phase 2)

- Foundation change deep route `/sites/{site}/foundation/changes/{change_id}`. Its API is `GET /api/sites/{site}/foundation/changes/{id}`; the fixture cases are `changes:1#a` change and `wrong_site_404`.
  - Bare `/foundation/changes` shows an unavailable state with a link back. Do not add a Foundation subtab; `foundationScreen.test.tsx:306,344` still holds.
  - Link it from `ChangeSummary` and `EventDetails` (`data-action-event-change`) in `SiteAction.tsx`.
- The walkthrough tool, mock comparison at 1440/390, layout evidence, the full suites with the real-Postgres JUnit run, and closeout docs.

## Open risks

- The CSS classes (`action-*`, `site-recommendation__pair`, `site-action__pair`) have no stylesheet rules yet. The pairs stack as plain blocks. Phase 2 layout work should add scoped styles under `.app-frame--operator`.
- The default `effective_from` assumes the server clock is close to `read_at`. If the clock passes the next midnight, the server returns `ACTION_EFFECTIVE_TIME_INVALID`, which the UI shows typed.
- There is no observation (OBSERVED) command control. The packet names accept/apply only; OBSERVED is shown from reads.
- A served demo needs an `ASSETOPS_ACTION_DEMO_GRANTS` document (S6-01a residual). Without one, every control correctly renders read-only.
