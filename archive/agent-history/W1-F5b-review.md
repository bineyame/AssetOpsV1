# W1-F5b review: in-page tab rows, Site Findings chips, carries, all-26 audit

Reviewer: fresh independent Claude reviewer. Revision `13cf2477` (code at `6978d924`), base `e7a1f6a1`.

## Verdict: RETURN

The tab rows, the unavailable-entry component, the guards and carries 8-11 are sound and match the ruling. Three findings block:

- **High:** a mock column deferred to F5 was never delivered.
- **Medium:** one sibling heading still differs from the mock.
- **Medium:** an audited state shows raw IDs, enums and backend JSON in the panel body.

## Findings

1. **High: the Site Findings table still has no Lens column.**
   - Where: `frontend/src/sites/SiteFindingIndex.tsx:433-441`.
   - The mock's columns are Finding, Domain, Priority, Confidence, State, Main consequence and **Lens**. The app ends with Period and has no Lens column.
   - This was explicitly deferred to F5: see `W1-F3-findings-money-review-packet.md:219,241` and `W1-F3-review.md:48`.
   - The ruling says the lens values "remain gaps unless backed", which means they are shown as gaps, not dropped.
   - Neither the packet nor the sitefindings overage reason mentions the omission, so the audit's "matches" verdict for this screen hides it.
   - It is a missing mock column, which is a structure mismatch under the owner rule.
   - Fix:
     - Add `<th scope="col">Lens</th>` after Main consequence.
     - In each row, add a cell holding the same muted dashed "Not assessed" badge used for Priority and Confidence.
     - Keep Period.
     - Add an assertion to the s404 W1-F3 structure test that the header row equals the full mock list plus Period.
     - Recapture part09.

2. **Medium: the Recommendation h1 is still "Recommendation" (packet deviation 3).**
   - Where: `frontend/src/shell/SiteAnalyticsFrames.tsx:399-401` and `:459`.
   - The mock titles `recommendation` "Generator support merits review" (`screens.js:344`), the same as `finding`.
   - After this slice, Finding, Evidence and History all head with the Finding's name and only Recommendation differs. The owner will see the inconsistency inside one tab row, on a class of issue that was already raised once (carry 10).
   - Fix:
     - Pass `onTitle={onTitle}` to `SiteRecommendation`, using the same lifecycle-title derivation as Evidence and History, with fallback `FINDING_NAME`.
     - Drop `FINDING_VIEW_TITLES` and always use `title`.
     - Update the recommendation heading test.
     - Recapture part13 for the recommendation cases.

3. **Medium: Evidence Analysis with a reading opened shows raw IDs, enums and backend JSON as body content.**
   - Where: `frontend/src/sites/LedgerSiteEvidence.tsx:1544-1630`.
   - Seen in `part04-evidence/evidence-analysis-record-1440-app.png`. With "Open record" selected, the "Accepted records" panel shows these unfolded:
     - reading, message, configuration, input and equipment UUIDs;
     - delivery and SHA-256 fingerprints;
     - the enum values `GOOD` and `ACCEPTED`;
     - source codes such as `battery-pcs-controller / edge-kobo-001`;
     - the full raw message JSON.
   - This fails the recurring-defect checklist ("no raw IDs, enums or backend text") on a state included in the owner walkthrough. It is also what drives the 5.75x/7.86x panel height. No earlier W1 review inspected this state.
   - Fix:
     - Word the reading detail: Quality "Good", Decision "Accepted", source and device by their configured names.
     - Move every UUID, fingerprint and the exact message into one closed "Exact references" disclosure inside the reading detail.
     - Recapture part04 `record`.
   - On the question asked: the audit already captures the default state (part06 `no-selection`, 1.64x/1.70x). Keep the `record` case, but list it after `no-selection` and label it "a reading opened". The reason keyed `evidence-analysis|*|*|Accepted records…` begins "In the captured case a reading is opened" and is applied to the no-selection, supported and limited rows, where that is false. Split it per case, and give the real cause of the 1.64x default height.

4. **Low: two overage reasons are placeholders, not reasons.**
   - Where: `overages.json` keys `analysis|*|*|Coverage, confidence and alternatives` and `asset|*|*|Interpretation and next evidence`.
   - I checked both captures:
     - **analysis-supported-390 (1.38x):** the label/value list keeps a two-column split at 390, so values wrap into a narrow right column. For example, Confidence takes 4 lines and "Other explanations" takes 4. This is a mild instance of the "tall wrapped rows at 390" defect. The honest reason is that, or better, fix it by stacking label above value below about 480px.
     - **asset-kobo001-390 (1.31x):** the content is three numbered missing-input items plus the capacity-test line, all honest. The reason's "1.26x at 1440" is wrong: the audit records 1.20x.
   - Fix: replace both "Not yet verified at 390…" texts with these causes and regenerate the index. The owner should not read reviewer to-do text.

5. **Low: carry 7 (legacy-Site captures) is not met.**
   - It is disclosed as deviation 1. The legacy paths are not owner-demo surfaces and remain covered by structure tests.
   - Fix: the coordinator records the acceptance or opens a backlog item for a LEGACY_FILE capture tool. No code change in this slice.

6. **Low: most 390 captures predate `useCurrentTabInView` (6978d924).**
   - This is disclosed. In the samples I checked (analysis, asset and finding-evidence at 390), the current Site tab is visible anyway. The panel structure is unaffected.
   - Fix: when part09 and part13 are recaptured for findings 1-2, the index picks up the current code for those screens. A full recapture is not required.

## Judgements requested

- **Deviation 2, "Finding" as the first entry of the Finding row:** accepted.
  - The Finding page keeps its Overview | Analysis view row, which falls under the contextual-Analysis-tab rule (`D-2026-10-16-w1-ux`, cited in the F5 contract).
  - Renaming the first entry to "Overview" would put two "Overview" entries on screen.
  - Alternatives sits after Evidence, as in the mock.
- **Deviation 4, "Scenarios":** accepted.
  - The two glosses are exact-text only and cannot be used anywhere else.
  - The label is the mock's.
- **Tab rows:**
  - Foundation: Site model | Single line diagram | Readiness | Change & effect. Change & effect is live and current on both Changes routes; a cold-room Site has three entries.
  - Work: Actions | Incidents · Not available yet | Maintenance · Not available yet.
  - Financials: Overview | Assumptions | Scenarios · Not available yet.
  - Finding: Finding | Evidence | Alternatives · Not available yet | Recommendation | History.
  - All of these match the ruling.
  - The unavailable entries are `li` text with no href, handler, tab stop, role or disabled state. Tests cover focus, Enter, Space and click.
- **Site Findings chips:** All is live (`aria-current`); Cost, Risks and Opportunities are not available yet. The chips sit in the panel, and the date window is kept and works.
- **Bare Change & effect page:** it now has the mock's two panels, with "No change selected" stated once (part17, 390 checked).

## Carries

- **8:** one closed money row, with the source record folded into it. Asserted.
- **9:** in `finding-open-1440-app.png` the "What happened" state line starts at "Source unverified." with no leading separator. Verified visually.
- **10:** Evidence and History head with the Finding's name. The tab rows scroll inside themselves and do not wrap (sitework, financials, finding-evidence and changes at 390). The scrollbar is visible, as in the mock.
- **11:** every sampled breadcrumb reads "Kobo mini-grid", never KOBO-001.

## Guards

- `navigation-truthfulness.ps1`:
  - The Foundation row now requires exactly 4 labels.
  - Only "Change & effect" was removed from the forbidden list; "Change and effect" and "Changes" stay forbidden.
  - The hard-coded `>Change & effect<` text scan elsewhere is unchanged.
  - The new `Get-InPageUnavailableEntryFailures` fails closed and pins the exact inventory.
- The 9 fixture cases run inside check-architecture.
- The missing-claim exemption is narrow and has mutation tests.
- I found no weakened assertion. Every changed assertion follows from the ruling, and most now assert more than before (for example, the Scenarios check went from "absent" to "in the row, unbuilt, nothing outside names it").

## Recurring-defect checklist, sampled screens

| Width | Screens |
| --- | --- |
| 1440 | sitefindings, finding-open, evidence-analysis record, health, foundation |
| 390 | sitefindings, sitework, financials, analysis, asset, changes, finding-evidence |

| Check | Result |
| --- | --- |
| State line said once | OK |
| One disclosure per panel | OK |
| No raw IDs, enums or backend text | Fails on evidence-analysis record (finding 3) |
| No contradictions | None found |
| Mock rows, columns and chips present | Lens column missing (finding 1) |
| No material limit hidden | None hidden |
| No tall wrapped rows at 390 | Mild case on analysis Coverage (finding 4) |

## Checks I ran

| Check | Result |
| --- | --- |
| `tools/check-architecture.ps1` | passed |
| `tools/check-agent-workflow.ps1` | passed |
| `node --test tools/checks/test_missing_claim_scan.mjs` | 24/24 |
| `npx.cmd tsc --noEmit` | exit 0 |
| Focused vitest (siteFinancials, siteFoundationRevision, foundationScreen, siteFoundationChange, s404SiteFindingIndex, siteFindingEvidence, siteFindingHistory, siteDetailScreen, w1f4ChangesWorkStructure, s5SiteWindowOverview) | 10 files, 451/451 passed. Vitest ran in this environment. |

- The full suite was not rerun. I am citing the implementer's 2140/0 at `6978d924`, which is the code revision under review.
- I did not rerun the captures, because they need Chrome, the backend and a dev server.
