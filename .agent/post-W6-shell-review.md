# post-W6 shell-typography-copy: code review

Reviewer: independent Claude reviewer (not the author). 2026-10-25.
Branch `task/post-W6-shell` at `0c245601`, diffed against `git merge-base main HEAD` = `7554111e` (31 files, +774/-116).
Inputs: `post-W6-shell-rulings.md` Q1-Q26, the shell card in `post-W6-audit/fix-slices.md`, `post-W6-shell-preflight.md`, register rows R115-R319 and R375-R381, the v69 mock.
Scope: code only. Screenshots, layout and closed-height caps (Q13, Q23, Q24) belong to the capture batch and capture review that follow.

## Verdict: ACCEPT-WITH-LOWS

Each D3 in the card is fixed as ruled, with the exact ruled copy. Each D1/D2/D4 split-off has a register row and a `MOCK DEVIATION` source label, with one gap (L3). I ran a mutation check: every new or changed test fails with the product files reverted to the merge base. No High or Medium findings. The Lows below can be fixed on the branch or carried forward; none blocks the capture batch.

## Checks run (this reviewer, on 0c245601)

| Check | Result |
| --- | --- |
| `tools/check-all.ps1` | All 11 guards passed (architecture, estate guard, navigation, agent workflow, dependency registry, delivery and mock-gap fixtures, missing-claim scan with 42 tagged uses and a baseline of 10 against the seed ceiling of 16, evidence width, screen ledger). |
| `npx.cmd tsc --noEmit` | exit 0 |
| Focused vitest, 12 files (postW6ShellCss, measuredTime, siteFoundationChange, siteAction, siteWorkCases, coldWorkCases, evWorkCases, siteHealthBoundary, sitesIndexRoute, v01bEvidenceVisual, siteFoundationRevision, simulatorLabWorkspaceEntryPoint) | 12 files, 361 tests passed |
| Mutation check: the 17 changed product files reverted to `7554111e` and the same 12 files rerun | 48 of 361 tests failed, in all 12 files. Every new post-W6 test failed. The only new cases that pass are the zero and plural incident rows (`0 incidents`, `3 incidents`, `4 incidents`), whose copy did not change. They are invariance rows, as intended. Worktree restored to HEAD afterwards and confirmed clean. |

Not run, per the quiet-machine instruction: the full vitest run, the build, Postgres and backend tests, captures and `layout-evidence`. I found no implementer packet for this slice in `.agent/`, so there is no full-suite or capture evidence to cite yet (see Residual risk).

## Ruling-by-ruling verification (diff, not commit messages)

- **Q5/R115:** `primitives.css` sets `grid-template-rows: auto minmax(0, 1fr)` in the 640 px operator/lab rule. The CSS source test fails against the old rule.
- **Q6/Q7/R119/R120:** Readiness closing sentence and changes page-end sentence use `Notice tone="blue"`, with their copy unchanged. The SLD unknown-part note uses `Notice`. `.v69-prose` is applied to the Sites empty state, the reserve form intro and both battery refusal sentences. Sites and SLD gained no callouts (D4 R378).
- **Q8/R125:** Only the `--badge-provenance-*` tokens changed, to `#f0eafa`/`#725094`. Origin violet is kept. The wording stays "Demonstration data" (D4 R376).
- **Q9/R127:** Root `Sites` crumb added above the h1. The subtitle is kept, with a D4 R375 label.
- **Q10/R129:** `--plant-bus: #6ca99a`. The icon row is centred. Paired icons and part links stay (D2 R377).
- **Q11/R130:** Ten Identity rows are rendered through `KeyValues`. `dd code` is set to nowrap. `.panel-pair--top` sets `align-items:start`. The test asserts all ten terms and the exact `KOBO-001` code.
- **Q12/R133:** `knownSiteName ?? siteId` in the no-version heading and skeletons. The test covers both Foundation and Readiness.
- **Q13/R140:** SVG `width`/`height` attributes removed. The viewBox is kept, with an inline `maxWidth: lattice.width`, `.sld{width:100%;height:auto}`, and `.sld__scroll{overflow-x:auto}` intact. Legibility at 390 is unverified (Residual risk).
- **Q14/R141:** See "Builder deviations" below. Copy is exact: "Set in the plan" / "Plan details are not available yet." / "{n} required". With the backend plan (`ratio [3,4]`, three guardrails, `actions/verification.py:233-246`), the target renders "≥25% lower" and "3 required", matching mock L432.
- **Q15/R151:** The four failure-code strings match the ruling verbatim. Raw codes are in a `tech` ExactReferences disclosure. `PolicyChangeBody` has no battery label, so "Battery" is used and the UUID stays in the change-references "Battery" row, as ruled.
- **Q16/R152:** Both change routes end at `Foundation › Change & effect` with a linked Foundation.
- **Q17/R149:** 12 px refusal prose. The three-panel refusal and generic "Battery" h1 stay (D4 R380).
- **Q18/R170:** `site.timezone` is threaded from SiteEvidenceFrame through SiteEvidence to LedgerSiteEvidence. Header reads `Measured (EAT)` and cells `HH:MM:SS`. The local date appears only when the local day differs from the selected day. The UTC instant is on `title`. A missing or unknown zone falls back to `UTC` in both header and cell. No D1 gap row was created (D1 R381).
- **Q19/R203:** `Actions › {code} › {section} · site: {site}`. It matches the mock's `breadcrumbs()` (object crumb as plain text, L1121) and the existing domain crumb at `SiteAnalyticsFrames.tsx:1424`. The code is hidden while the read is pending. Tests cover six sections and the loading state.
- **Q20/R319:** `countWords` gives `1 incident` / `n incidents` / `1 maintenance case` / `n maintenance cases`. Tests cover zero, one and plural on mini, cold and EV.
- **Q21 boundary:** `siteWorkCases.tsx` changes only the noun strip. `SiteAnalyticsFrames.tsx` changes only the Action and change crumbs. Q2's excluded files (`App.tsx`, layouts, `domainActionClient.ts`, `EvHealthDepth.tsx`, `globalWorkParts.tsx`, `WorkRequestOverview.tsx`) are untouched. `SiteEvidence.tsx` changed only to pass the timezone through, as Q18 needs. `SiteHealthFrames.tsx` changed only by a label comment. The registry JSON and `gapCatalogue.ts` are outside the Q2 list (L1).
- **Q26:** `tools/checks/*` has no pins on provenance, bus or operator-grid. `shell-overflow.ps1` still pins `.sld__scroll`. No guard was loosened.
- **Test loosening:** `simulatorLabWorkspaceEntryPoint.test.tsx:136` now filters out the Breadcrumb navigation. It still fails on a workspace landmark and asserts exactly one breadcrumb, which is acceptable.

## Builder deviations requested for scrutiny

1. **`G-changes-plan-figures` registry gap plus the `<MissingClaim>` wrap.** This is mechanically forced. Q14 mandates the copy "Plan details are not available yet.", and `tools/checks/missing-claim-scan.mjs` PATTERNS (`/not available yet/i`) fails any such copy that is not in `<MissingClaim>` with a catalogued registry pair. The baseline may only shrink. So under the guard, Q14's "registered" cannot be met without a registry gap. The entry itself mis-describes the source (L1).
2. **W1 Action code parsed from the `SiteAction` title.** This works and is test-pinned: `siteAction.test.tsx` asserts the code crumb equals `action.action_code` for all six sections, so a change to the title template fails CI rather than silently drifting. The coupling is still implicit (L2).
3. **R141 fallbacks.**
   - Pending: before the effect resolves, `planRead` is null, so the state is `"pending"` and the cards keep "Set in the plan" plus the not-available line.
   - Error: a non-`loaded` result, or a thrown promise, gives `"failed"`.
   - Empty: `plan: null`, or an unusable target or guardrails, gives `"absent"`.
   - Stale responses are dropped by the `active` flag and the `planRead.planId === planId` guard. The hook sits before the early returns, so hook order is safe.
   - All three states are tested.
   - One edge is over-strict (L4).
4. **R170 timezone fallback.** This is correct for missing, empty and unresolvable zones (`usableZone` try/catch, then `UTC` header and UTC clock). The abbreviation for zones not in the map is weak (L5).
5. **R140 SVG scaling.** This is correct in code, and the `.sld__scroll` contract is kept. Geometry and legibility need the capture (Residual risk).
6. **Register-ID collision risk.** No collision today. On `main` and on the parallel branches `task/post-W6-W2-cold`, `task/post-W6-W2-EV` and `task/post-W6-W3-estate` (all committed 2026-10-25), the register ends at R374. Any of those cards that registers its own D1/D2/D4 split-offs will naturally also start at R375 (L6).

## Findings

### High
None.

### Medium
None.

### Low

**L1. The registry entry `G-changes-plan-figures` mis-states its source, and it is an Architect-owned artefact added by the builder.** `frontend/docs/architecture/v69-dependency-registry-pilot.json:422`, `frontend/src/ui/gapCatalogue.ts:15`.
- **What is wrong:** The entry says `"missing_kind":"contract"` and `"source_status":"absent"`, but its own `evidence.source` names the existing `verificationClient.getPlan` read. The backend always stores `target.ratio` and three `guardrails` on a frozen plan (`backend/assetops_backend/actions/verification.py:233-246`). In practice the gap covers only transient pending or failed reads. The registry already uses `"source_status":"existing"` for that kind of case (3 entries).
- **Failure scenario:** A registry-driven allocation pass reads this as an open, unplanned contract gap "pending owner review", and schedules contract work that is not needed.
- **Fix:** The Architect ratifies the entry, with `source_status:"existing"` and a `missing_kind` and `review_trigger` that describe a runtime read state. Alternatively the Architect records that Q14's "registered" includes the dependency registry. Q2 does not list the registry or `gapCatalogue.ts` among the files this card may edit.
- This is a process and truthfulness point, not a UI defect. The rendered copy is the ruled copy.

**L2. The Action code crumb is derived by string-splitting the page title.** `frontend/src/shell/SiteAnalyticsFrames.tsx:1747-1750`, used at `:1668`.
- **What is wrong:** `w1ActionCode` takes everything before the first `" · "` in the title that `SiteAction.tsx:170` builds.
- **Failure scenario:** `SiteAction` later reports a title such as `"Action not found · …"`, or reorders it to `"Battery reserve trial · A-104"`. The crumb then shows the wrong text as the Action code. Today's tests would catch a template change only for the loaded case they cover.
- **Fix:** Optional. Add an `onActionCode(code | null)` callback (or report `{code, title}`) from `SiteAction`. Q2 permits Site-component edits "as each ruling requires". This is a preference given the existing test pin.

**L3. R376 covers `sites, foundation`, but only Foundation has the label.** `frontend/src/sites/SitesIndex.tsx:557` (`<Badge tone="provenance">{view.sourceMode}</Badge>`) has no `MOCK DEVIATION D4 (R376)` comment. The register row itself says the label is only at the Foundation Identity row.
- **Failure scenario:** The capture review or a later audit finds the Sites inventory "Demonstration data" chip without a label, and re-raises it as an unregistered departure (Q3: "visible label on the affected view").
- **Fix:** Add the one-line label comment at `SitesIndex.tsx:557`, and name both sites in the R376 row.

**L4. `planFigures` hides a stored target whenever guardrails are empty, and the reverse.** `frontend/src/sites/SiteFoundationChange.tsx:207`.
- **What is wrong:**
  - One combined null-check gates both cards.
  - A ratio of `num >= den` (for example a "no increase" `[1,1]` target) is treated as absent.
  - `Math.round` can overstate the bar: `[1,3]` renders "≥67% lower" for a 66.7% requirement.
- **Failure scenario:** A future plan version with a valid target and no guardrails shows "Plan details are not available yet." on the Target card, which hides a stored value. Q14 says to show the stored target and guardrails, each as stored. This cannot happen with today's backend.
- **Fix:** Compute target and guardrails independently, so each card falls back on its own. Use `Math.floor` for the percentage.

**L5. Abbreviations for zones not in the map are taken from 1 Jan 1970.** `frontend/src/sites/LedgerSiteEvidence.tsx:114-122`.
- **What is wrong:** `formatToParts(new Date(0))` gives the winter name or offset for DST zones, for example `GMT` for Europe/London in summer.
- **Failure scenario:** A summer-dated record on a London Site is headed `Measured (GMT)`, while its cells are in BST.
- **Fix:** Derive the name from the selected window's start instant, not the epoch. Demo Sites are Addis and UTC (both in the map), so there is no impact today.

**L6. Register-ID collision risk with the parallel post-W6 cards.** `.agent/mock-departure-register.md:476-482` (R375-R381).
- **What is wrong:** Three sibling branches are open from the same R374 tail.
- **Failure scenario:** W2-cold, W2-EV or W3-estate appends its own R375+ rows. Whichever merges second gets a textual or semantic ID clash, and source-comment labels then point to the wrong row.
- **Fix:** Before merge, the coordinator or Architect reserves R375-R381 for this card and tells the sibling cards to start at R382 or later. Alternatively, renumber on rebase and update the label comments with it.

**L7. Orphaned doc comment.** `frontend/src/sites/SiteFoundationChange.tsx:660`. `/** Application attempts of the Action… */` now sits directly above the new `FAILURE_WORDS` JSDoc instead of `Attempts`. **Fix:** Move it back above `function Attempts`. This is cosmetic.

## Residual risk not named elsewhere

- **SLD legibility at 390 (Q13).** Full scale-to-fit can shrink a wide lattice to roughly a third, making node labels unreadable. Q13 then requires a readable selected-part key. Only the 390 capture of default, battery and unknown-part can show this. The capture review should judge legibility explicitly.
- **Q23 caps.** The ten-row Identity panel at 390 (cap 1050 px), and evidence-analysis with the longer chart note and new column header (cap 1800 px at 390), are unmeasured until the capture batch runs.
- **Implementer evidence.** No packet for this slice was found in `.agent/`. The full vitest result, build result, and the 174 + 230 recapture inventory (Q24) are therefore unverified at this SHA. The capture batch packet must cite them against `0c245601`, or whichever SHA it is taken from.
- **Provenance token reach.** The new purple applies to every `tone="provenance"` badge, including EV "Generated test data" and the EV assessment classification badges. This is intended under Q21, and the all-screen regression capture should look at it.
