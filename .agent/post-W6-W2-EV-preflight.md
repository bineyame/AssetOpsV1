# post-W6 W2-EV pre-flight

Builder pre-flight per `.ai/ROLE_CONFIG.md` "Builder pre-flight" and lesson 15. Base `main` 7554111e, branch
`task/post-W6-W2-EV`. No product code written. Sources: W2-EV card, "Sequencing", "Explicit Architect rulings" and the
cap docket in `post-W6-audit/fix-slices.md`; register R265-R286; `classification.md`; ledgers B8/B9 (`batch-08.md`,
`batch-09/differences.json`), B16-16/B11-01/B18-04; v69 `index.html`; `post-W6-shell-rulings.md` (precedent).

Every question has a recommended default (**Default**). If the Architect accepts all the defaults, the build can start
without a further stop. There are 31 questions: Q1-Q13 are per ID, Q14-Q24 cover seams and ownership, Q25-Q31 cover
tests, caps and recapture.

## A. Per-ID target behaviour

Line anchors are at 7554111e.

**Q1 - R265 (B8-06) ev-readiness Next step.** `EvFoundationViews.tsx:624` and `:635` render `UnavailableLinkEntry`
"Financials" and "Assumptions". The mock's `readinessScreen('ev')` (index.html:314) has `link('ev-financials','Financials →')`
and `link('ev-assumptions','Assumptions →')`. `EvFoundationFrameProps.financialsHref` and `assumptionsHref` (:122-123)
already exist but are unused. `shell/SiteFoundationFrame.tsx:174-175` wires them to the **mini** `siteFinancialsHref`
and `siteFinancialAssumptionsHref`, which is the wrong destination for EV (B16-16 class).
**Default:** render `<Link to={props.financialsHref}>Financials →</Link>` and `<Link to={props.assumptionsHref}>Assumptions →</Link>`.
Change the two wiring lines to `siteEvHref(siteId, "financials")` and `siteEvHref(siteId, "assumptions")`. The links
carry no window, because Readiness has only `at`. The EV money pages apply the ruled default window, matching the
existing `Evidence →` link. The D3 covers only these two cells. Rows and Confirmed values stay D4, as the ledger says.

**Q2 - R267 (B8-08) duplicate React keys.** `EvFoundationViews.tsx:724` builds ExactReferences labels
`${evRoleLabel(b.role)} source`, and two connectors share each role. `ui/ProductStatus.tsx:190` `ExactReferences` keys
rows by label.
**Default:** make the label unique locally, as `${evRoleLabel(b.role)} source · ${connector/asset display name ?? b.device_id}`.
Do not edit the shared `ui/ProductStatus.tsx`. The test asserts unique labels and no "same key" console error.
Alternative: add an optional `key` to the ExactReferences row type in shared ui. Is that preferred?

**Q3 - R268 (B8-12) Sessions "Inspect session lineage".** `EvAssessmentViews.tsx:524` renders `UnavailableInline`. In
the mock, `claim('Inspect session lineage','ev')` opens an **evidence drawer** (index.html:179/1216), not a page. The
app has no drawer.
**Default:** link "Inspect session lineage ↗" to the built EV Evidence analysis, `siteEvHref(siteId,"analysis")` plus
the selected read's `from,to,known_at`. Hide the link on a refused or null read, keeping today's refused strip. This
needs a new `analysisHref` prop on `EvSessionsFrame`, wired at `shell/SiteAnalyticsFrames.tsx:250-272` (see Q16).
Confirm the destination: analysis or EV Evidence overview.

**Q4 - R270 (B8-14) tiles don't account for every attempt.** DTO `EvDenominator` (`evAssessmentClient.ts:43`) carries
started, completed, confirmed_delivery, fault_aborted, observed_abort, incomplete, contradictory and orphan. The mock
tiles sum, and the denominator line is "10 confirmed completions + 1 observed failure + 1 unknown = 12 attempts."
**Default:** keep the four tiles. When `started − (confirmed_delivery + fault_aborted + incomplete) > 0`, add one muted
line under the tiles: "{r} of {n} attempts are outside these three outcomes; see How to read the denominator." It
derives no new categories, such as partial = completed − confirmed. Alternatives: an explicit equation in the
denominator panel (R272 is D4 content), or a ruling that the denominator line is enough. Which one?

**Q5 - R271 (B8-15) Outcome chip overpainted (missing-meter, 1440).** The CSS is `sites/w2-ev-assessment.css:21-33`
(EV-local, not the shell's primitives), with Outcome col 13%, Evidence col 22% and `.ev-chip`.
**Default:** let `.ev-chips` and the Outcome chip wrap (`white-space: normal; max-width: 100%`), and give the Outcome
col a `min-width` that fits "Completed · energy partial". Keep the 390 inner table scroll. Prove it with a CSS source
assertion (jsdom has no geometry) and the missing-meter 1440 recapture.

**Q6 - R275 (B8-19) EV Finding strip separator and window.** `EvAssessmentViews.tsx:696-701` places "Observed
interruption" and `{siteName}` with only a space between them. The strip has no window. The cold strip (`ColdAssessmentViews.tsx:845-856`)
joins with " · " and includes `windowText(from,to)`.
**Default:** join the claim phrase, site name and window with " · ", and add `windowText(finding.window.from, finding.window.to)`
from `coldFormat.ts` (read-only reuse). This gives "24 Oct 2026 08:00–16:00 UTC", or "No window selected". The stored
EV Site zone is `Etc/UTC`, so UTC is site-local under the time-basis ruling. The UUID chip and the "Observed"
confidence word stay as they are (B1-53 / D2).

**Q7 - R276 (B8-20) missing "Inspect claim evidence ↗".** The mock places `claim('Inspect claim evidence','ev')` in the
Bounded conclusion. In the app, the conclusion panel (`EvAssessmentViews.tsx:739-748`) ends with `REC … · No analysis link`.
**Default:** add a paragraph link "Inspect claim evidence ↗" to the EV Evidence analysis with the **Finding's own**
window, the same destination as Q3. Keep `REC {id} · No analysis link`: R38 says the record itself has no proved
anchor. This needs an `analysisHref` (or `routes`) prop on `EvFindingFrame`, wired at `SiteAnalyticsFrames.tsx:660`.

**Q8 - R280 (B8-24) "Finding section unavailable for this site."** `FINDING_SECTION_UNAVAILABLE`
(`SiteAnalyticsFrames.tsx:616`, used :747) is **shared by cold and EV** child addresses, so it overlaps W2-cold.
**Default:** use the kind-scoped copy "This Finding section is not available for this kind of Finding." for both domains,
with the `Open Finding overview` link unchanged. W2-EV makes the edit; W2-cold only rebases. Alternative: per-domain
copy ("…for EV charging Findings" / "…for cold-chain Findings"). The `/recommendation` address, where the selected tab
disagrees with the address, was an "Architect note" in the ledger and is not part of the D3. **Default:** leave it
unchanged; R278 D1 covers Recommendation. Is that in or out?

**Q9 - R281 (B8-27) plural.** `EvAssessmentViews.tsx:446` reads "1 accepted starts" and "1 observed aborts". The same
class appears on screens I own: `EvSiteViews.tsx:475` ("observed aborts … attempts") and `:798`.
**Default:** add a local `plural(n, one, many)` helper in `EvAssessmentViews.tsx`, exported to `EvSiteViews.tsx`. It
covers starts, aborts and attempts on all three lines, with no shared module (shell Q20 precedent). Including :475 and
:798 widens beyond the literal R281 screen. Accept?

**Q10 - R283 (B9-03) padded 7 timeline slots.** `EvSiteViews.tsx:499-526` pads to `CHRONOLOGY_SLOTS = 7` with "No
accepted event". The same constant also **truncates** after 7 accepted events.
**Default:** render only the accepted events, plus the existing "End record missing" row when the session is incomplete.
With none, render one gap line, "No accepted event in this window" (the existing literal at :612). Keep a 7-row visible
cap. Above 7, add "{n} more accepted events in Event details" (new copy). This cannot be produced, because each case
has one session, so it gets a pure fixture test. Accept the cap and the copy?

**Q11 - R284 (B9-05, Medium) refused EV states.** The refused Overview, Evidence, Analysis and Financials drop the strip
and tiles. Every panel shows `evRefusalText` 422 "Choose a valid UTC start and end, up to 31 days."
(`EvAssessmentViews.tsx:89`). The cold M3 pattern (`coldSiteViews.tsx:394-428`, `ColdAssessmentViews.tsx:128-160`) is
`RequestedWindowBar` (dropped for invalid-window), a `RefusedStrip` "Window cannot be read", `RefusedTiles` "Not
assessed" and a `page-refusal` banner.
**Default:** add local EV equivalents in `EvSiteViews.tsx` (no import from W2-cold's files): a refused strip on all
four screens, plus "Not assessed" tiles (Overview 5 with the `OverviewCards` labels; Financials 4) and one page-refusal
banner. The panels keep one short gap line. A non-window refusal (401/403/404/5xx) keeps the requested window line;
422 drops it (cold N7). Specific copy comes from `refused.code`, because the backend distinguishes them
(`ev_assessment_api.py:103-107`):
- `EV_WINDOW_INVALID` with from ≥ to: "The window end must be after its start."
- `EV_WINDOW_INVALID` one-sided: "Give both a start and an end, or neither."
- `EV_WINDOW_TOO_LONG`: "Choose a window of 31 days or less."

The title is "Window cannot be read". This copy must equal W2-cold's R261 (B7-11) ruling, so please rule **one** set
for both cards (see Q17). `evRefusalText` also feeds Sessions and the Finding (R273 D1), so they inherit the new
sentence. Accept?

**Q12 - R285 (B9-08) Financials source "Sessions ↗".** `EvSiteViews.tsx:1287`; the mock source is "Energy".
**Default:** use "Energy ↗" with `sel(routes.energy, f.window)` (`evSiteRoutes.energy` = Performance/energy, built in
W5-03a) when estimated, and keep no link otherwise. The interruption row's "Finding" stays (R65 D1). The chip colour
stays D2.

**Q13 - R286 (B9-09) Assumptions "Not connected" chip.** `EvSiteViews.tsx:1191` maps `billing_state` to plain text. The
backend **always** emits `"NO_RECORD"` (`ev_site_reads.py:968`), so "Not connected" would be a mock literal. Readiness
hard-codes "Not connected" for billing (`EvFoundationViews.tsx:618-620`), so the two screens disagree.
**Default:** render the billing value as a `Chip`, with the wire word "No record" (`NOT_CONNECTED` → "Not connected"),
and label the wording departure D4. The window line and the site-scoped refusal stay D2 (B7-10/R260 parity), and the
refused panel gets the Q11 banner only. Alternative: rule that billing absence is "Not connected" on both screens, which
needs a wire change. Which one?

## B. Seams, ownership and overlap

**Q14 - EV main-tab destinations (B16-16 / R347, owned by W5-EV-Work).** The card's States list "EV main-tab
destinations" and its tests list "tab-window". `shell/operatorSiteTabs.tsx:70-83` is site-type-blind: on EV, Overview
goes to `/sites/:id` (the "awaiting evidence migration" placeholder), Evidence to the mini `/evidence` and Financials to
the mini `/financials`, and no tab carries `from,to,known_at`.
**Default:** W2-EV owns the mechanism. Add an optional `hrefs` override (or a `siteType` prop) to `OperatorSiteTabs`:
on EV, Overview goes to `/ev`, Evidence to `/ev/evidence` and Financials to `/ev/financials`, and every tab carries the
read window when the frame has one. Apply it at the EV mounts W2-EV touches: `SiteEvFrame` (`evSiteRoutes.tsx`), the
EV Sessions/Performance mount and the EV Finding mount (`SiteAnalyticsFrames.tsx:265`, :667), and the EV Foundation
mount (`SiteFoundationFrame.tsx`). W5-EV-Work closes R347 on Health, Work and Action by reusing it. Confirm the owner
split. App routing is unchanged, so `/sites/:id` stays non-EV-aware.

**Q15 - Merged EV duplicates sit in my files but belong to W2-cold IDs.** These four are canonically W2-cold, but their
EV instances live in `EvSiteViews.tsx`, a W2-EV file:
- B9-02 → B7-03/R254: Overview cards. Availability is hard-coded "Not assessed" while linked; Health is unlinked.
- B9-06 → B7-07/R258: Evidence. Portfolio link, "Review energy", "Work · Not available yet", padded next-evidence rows
  (:975), and the complete-case Cause row.
- B9-07 → B7-08/R259: Analysis UUID cells and height.
- B9-10 → B7-01/R253: the EV Site Findings list.

**Default:** W2-EV fixes the EV instances in `EvSiteViews.tsx` using W2-cold's ruled copy. W2-cold keeps
`SiteFindingIndex.tsx`, so the B9-10 EV list stays with W2-cold. `ev-findings` is in my recapture only as a
destination regression. This adds about 4 ID instances to W2-EV. Otherwise, W2-cold must edit `EvSiteViews.tsx` and
serialize with me. Please rule.

**Q16 - Shell overlap: `shell/SiteAnalyticsFrames.tsx`.** The shell card edits it (Q19 Action crumbs), and W1-b and W4
share it. W2-EV needs it for an `analysisHref` on Sessions (Q3), an `analysisHref` and window tabs on the EV Finding
mount (Q7, Q14), and the `FINDING_SECTION_UNAVAILABLE` copy (Q8). `sites/*` never import `shell/*`; hrefs arrive as
props.
**Default:** limit the edits to the EV mount blocks (about :245-272 and :656-670) and the one constant. Rebase after
the shell merges, then after W1-b if W1-b lands first. Accept serialization with W1-b?

**Q17 - Shell overlap: `shell/SiteFoundationFrame.tsx:174-175`.** The shell card edits this file (Q11/Q12).
**Default:** two-line wiring change after the shell merges (Q1), plus the EV tab override (Q14).

**Q18 - W2-cold overlap list.** The two cards may both touch:
- `SiteAnalyticsFrames.tsx` (`FINDING_SECTION_UNAVAILABLE`, and the cold Finding mount sits next to the EV one);
- `shell/operatorSiteTabs.tsx`, if W2-cold also needs cold tab windows;
- `coldFormat.ts` (I read `windowText` only);
- the window refusal copy (Q11 ↔ R261);
- `EvSiteViews.tsx`, if Q15 goes to W2-cold.

**Default:** whichever card merges second rebases. The literals are identical by ruling, and no new shared module is
created.

**Q19 - `ev-findings` destination.** EV Findings currently lands on the mini closed state (B9-10, High, W2-cold). My
changed EV links never target `/findings` except the tab. **Default:** record `ev-findings` as a regression pair only.
It shows whatever W2-cold has landed by then.

**Q20 - Estate and global Site-name links to EV (B11-01 W3 / B18-04 W6).** **Default:** out of W2-EV. Those cards link
to `siteEvHref` directly. W2-EV exports nothing new for them beyond the existing `siteEvHref`.

**Q21 - missing-claim guard.** `tools/checks/missing-claim-scan.mjs:68` documents the W2-05a readiness "Financials and
Assumptions" unavailable entries. **Default:** update that reason text and lower the baseline count. Lowering is
allowed. Prove the scan fails if an untagged "Not available yet" is reintroduced.

**Q22 - Navigation fixtures.** `tools/checks/navigation-rail-fixtures.ps1:165-235` mutates exact strings in
`EvAssessmentViews.tsx` and `EvSiteViews.tsx` (`<UnavailableTab label="Recommendation" />`, `data-performance-subtab`,
`data-ev-subtab="scenarios"`, `{financial ? (`). **Default:** keep those strings byte-identical, and rerun the guard.

**Q23 - Window propagation on new links.** **Default:**
- Session lineage, claim evidence, Energy and tabs carry `from,to,known_at` from the selected read's envelope.
- A refused or no-window read carries nothing.
- Readiness links carry nothing (Q1).
- Explicit historical windows are preserved, and the default-window ruling is untouched.

**Q24 - Breadcrumb and Action chrome.** **Default:** no change to crumbs, which belong to the shell, nor to the `ev`
Overview card links, which belong to Q15.

## C. Tests, caps and recapture

**Q25 - Tests that will break.**
- `sites/__tests__/evFoundation.test.tsx:563-565`: the readiness entries become links.
- `evAssessmentRoutes.test.tsx`: "accepted starts", "observed aborts", "Choose a valid UTC start…", and the
  "Observed interruption" strip text.
- `evSiteMoneyRoutes.test.tsx`: the "No accepted event" slot count, "Sessions ↗", the window copy, "observed aborts",
  and billing "No record" if it becomes a chip.
- `miniDecisions.test.tsx:834,1072,1100` (Q8 copy).
- `shell/__tests__/operatorSiteTabs.test.tsx` (Q14).
- Possibly `evDepth.test.tsx` and `evEnergy.test.tsx`, because the Sessions mount tabs also render on availability and
  energy.

**Default:** update them, and add these assertions: the session denominator plural and the outside-outcomes line; the
lineage, claim-evidence and Energy hrefs with window; the readiness hrefs; tab-window; missing-meter chip CSS; unique
reference keys; the refused strip, tiles and banner per code; accepted-events-only.

**Q26 - Caps (lesson 15).** The docket rows that touch my screens are only `ev-readiness` Gateway 390 (cap 1900, peak
1669, regression), `ev-evidence-analysis` Accepted records 1440 (cap 450, peak 399) and `ev-findings` 390 (cap 500). No
sessions, ev-finding, ev, ev-financials or ev-assumptions panel has a cap.

Likely misses:
1. `ev-evidence-analysis` 1440 with the five-row 160-character fixture will very likely exceed 450 px. The 3-line UUID
   cells are B7-08/R259, which is W2-cold's or mine by Q15.
2. The Sessions table with 5 × 160 rows, plus the wrapped Outcome chip (Q5).
3. The EV Finding Bounded conclusion, already at 1.30x, gains a link (Q7).

**Default:** panels absent from the docket get no cap. I record their closed heights and keep them unclipped. For
analysis, I measure the worst case, and if it is over 450 I fix it only if Q15 gives me B7-08; otherwise I return the
measurement to the Architect. Please give a revised analysis cap now if it is known to be too small.

**Q27 - Recapture set (audit-index, both widths): 92 pairs plus 4 regression pairs.**

| Screen | Pairs | Indexed cases |
| --- | ---: | --- |
| ev-readiness | 6 | stocked, complete-replay, no-version |
| sessions | 24 | interrupted, default-window, complete(+dw), missing-meter(+dw), fault(+dw), contradictory(+dw), no-selection, refused |
| ev-finding | 12 | interrupted, no-window, refused, unknown-id, recommendation-address, evidence-child |
| ev | 10 | complete, interrupted, no-selection, no-window, refused |
| ev-evidence | 10 | complete, interrupted, no-selection, no-window, refused |
| ev-evidence-analysis | 10 | complete, interrupted, no-selection, no-window, refused |
| ev-financials | 10 | complete, interrupted, no-selection, no-window, refused |
| ev-assumptions | 10 | complete, interrupted, no-selection, no-window, refused |
| ev-findings | 4 | inventory-check (regression) |

Producer: `.agent/W2-F-evidence/seed.py ev {interrupted|complete|missing-meter|fault|contradictory}` on a `*_test`
database. The tools are `batch-08/tools/capture-b8.mjs` and `batch-09/tools/capture-b9.mjs`, with their
`targets-*.json`.

**Q28 - Reach from shared changes.** If Q14 changes the Sessions mount tabs, `availability` (18) and `energy` (14) are
also reached. If it changes `SiteEvFrame`, `ev-scenarios` (16) is reached. If it changes the Foundation mount,
`ev-foundation` (6) and `ev-sld` (4) are reached. The Q8 copy reaches the `cold-finding` child cases.
**Default:** recapture all of those too, 58 extra pairs plus the cold-finding child pairs, or the cold child pairs are
left to W2-cold's recapture. Confirm.

**Q29 - New cases not in the index.** **Default:** add these URL-only pairs to prove the Q11 copy split:
`EV_WINDOW_TOO_LONG` (span over 31 days) and a one-sided window on `ev` and `sessions` at both widths, 8 pairs. Accept
them as extra pairs?

**Q30 - Capture gaps (pure selected-DTO tests instead).**
- EV Finding NO_LONGER_SUPPORTED: produced only inside a backend test.
- EV pending, stale or unknown currentness: later bootstrap.
- 401/403 refusals: no audit producer.
- More than 7 accepted events on one day (Q10).
- `billing_state = NOT_CONNECTED` (Q13).
- The worst-case five 160-character rows.

**Default:** record these as gaps, each with a DTO test.

**Q31 - Mock-departure labels.** **Default:** add or keep visible `MOCK DEVIATION` labels only for the D4/D2 items these
fixes touch: the Q4 copy, the Q13 wording and Q11 if its copy differs from the mock. Update the R265-R286 register rows
to `fixed (pending review)` in the packet, not here.

## Top 5 for the Architect

1. Q15: whether the merged EV duplicates B9-02/06/07 in `EvSiteViews.tsx` go to W2-EV or W2-cold.
2. Q14: who owns the EV main-tab mechanism (R347), and through which `OperatorSiteTabs` API.
3. Q11 with Q18: one window-refusal copy set and refused layout shared with W2-cold's R261.
4. Q13: the billing wording, "No record" chip or "Not connected", given a wire that always emits NO_RECORD.
5. Q26: the `ev-evidence-analysis` worst-case cap, and no caps for the uncapped Sessions and Finding panels.
