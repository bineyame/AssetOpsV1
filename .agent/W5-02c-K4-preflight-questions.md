# W5-02c K4a/K4b/K5 pre-flight refresh: questions for the Architect

Branch `task/W5-02c-K4-cold-action` at main `59c66b5e` (K2 and K3 merged). This is a read-only dry-read. It checks the K4/K5 cards (`.agent/W5-02-build-spec.md:103-105, :70-76, :367-373`), the merged K2 domain Action shell, mock `cold-action` (`frontend/mockups/v69/index.html:742-746`) and the expected W5-03b E4/E6 collisions. The E4/E6 branch `task/W5-03b-ev-health-ui` has no diff from main yet, so the collisions below are taken from `.agent/W5-03b-ui-preflight-rulings.md` and `.agent/W5-03-build-spec.md`. No product code was written.

## Earlier rulings that still hold (no question)

- P-K4a-1-6 (`build-spec:369`) still hold: the guard line form, both `active` and `aria-current`, the tests in `operatorRailInventory.test.tsx`, the secondary `button` class, `expectV69Panels('cold-action')` and no banner (K3 ruling 1). Current main still has the guard literal at `tools/checks/navigation-truthfulness.ps1:645`, the nine live rail links (`OperatorShellLayout.tsx:50-61`) and the nine-link focus-order test (`operatorRailInventory.test.tsx:112,174-182`). `NavRail` is still pure `NavLink` (`NavRail.tsx:92`).
- P-K4b-1-2 (the 422 comes from the capture tool and sits beside the client refusal) and P-K5-1-2 (lineage test and one full suite) still hold. The wire order is still `INITIAL_RESULTS = NOT_TESTED, NOT_TESTED, NOT_ESTABLISHED, PENDING` (`domain_action_index.py:52`), and the criteria are still the four fixed rows (`domain_action.py:34-39`).
- These K2 rulings still hold: 7 (refusal shape), 8 (`/verification` 404, no W1 fallback), 10 (notice on loaded only), 12 (`Finding version`) and 18 (`Open site` as `button`). The merged shell has all of them at `SiteAnalyticsFrames.tsx:1412-1483`.
- Spec `:32/:54` still holds the Related activity sentence template. K3 ruling 10 / P-G-4 still holds the WR Overview href, with only an explicit URL `known_at`. R65, R66 and R68 still cover the Finding label, the Finding control and the Inspect target (`.agent/mock-departure-register.md:111-114`).

## New or still-open points

**Q1. Should the rail override apply to W1 battery Action detail as well?** (new)
- Evidence: the ruled regex `^/sites/[^/]+/actions/[^/]+(?:/.*)?$` (`build-spec:369`) also matches MINIGRID/EV W1 Action detail (`SITE_ACTION_ROUTE_PATH`/`SITE_ACTION_VIEW_ROUTE_PATH`, `App.tsx:471`). R69 names only `cold-action`. The mock's W1 `action-*` screens also use root `Actions` (`index.html:729`; `rail()` marks `s.root===label` active, `:1114`), so the regex is mock-consistent.
- (a) Recommended: apply it to all Site types, as ruled. Add one W1 mini-grid Action active-state test and widen R69's resolution note.
- (b) Restrict it to domain Actions. The pathname helper cannot know the root type without a read, so this means new plumbing.

**Q2. What exact source text should the `railActiveLabel` guard match?** (still open in practice)
- Evidence: a PowerShell guard cannot execute TypeScript, so "returns `Actions` only for regex X" (`build-spec:369`) has to be a source-text match. The shell scan at `navigation-truthfulness.ps1:659` already rejects `to:`/`href`/`Link` outside the inventory. E6 edits the same guard and fixture files (`W5-03b-ui-preflight-rulings.md:31`).
- (a) Recommended: one exact module-level line in `OperatorShellLayout.tsx`, e.g. `const railActiveLabel = (pathname: string): "Actions" | null => (/^\/sites\/[^/]+\/actions\/[^/]+(?:\/.*)?$/.test(pathname) ? "Actions" : null);`, matched whitespace-flexibly. Add two negative fixtures: the unconditional `activeLabel="Actions"` (as ruled) and a widened regex such as `/^\/sites\//`. K4a rebases on E6's guard edits and keeps both sets.
- (b) Add a vitest unit test of the helper and have the guard only require the call form.

**Q3. Who admits the `cold-action` currentness notice to the panel guard?** (new)
- Evidence: the merged shell renders `[data-domain-action-currentness]` between the strip and the first panel on non-CURRENT reads (`SiteAnalyticsFrames.tsx:1451-1456`). `SCREEN_LEADING` admits the leading notice only for the three `cold-work*` screens (`frontend/src/test/panelStructure.ts:63-70`), so `expectV69Panels('cold-action')` fails on any historical, pending, stale or unknown test. `panelStructure.ts` is not in K4a's file list (`build-spec:103`), and E4/E6 are barred from it (`W5-03b-ui-preflight-rulings.md:5,11`). R91 covers only `cold-work*`.
- (a) Recommended: grant K4a `panelStructure.ts`, solely to add `"cold-action": "[data-domain-action-currentness]"`, and extend R91 to `cold-action`.
- (b) Move the notice below the panels. That departs from the K2/K3 notice position.

**Q4. Which panels render for loading, not-found and refusal states?** (new)
- Evidence: the K2 shell renders these states inside one untitled `Panel` (`SiteAnalyticsFrames.tsx:1457-1477`). The mock has exactly two headed panels (`v69-rendered-panels.json:884-892`; `index.html:744-745`). The cards do not say whether the two headings render on non-loaded states.
- (a) Recommended: render both headed panels only when the read is loaded. Loading, 404 and 403/422/503 keep one untitled state panel. Assert `expectV69Panels` on loaded states only, and assert the refusal states explicitly.
- (b) Put the state inside `Declared outcome criteria` and omit `Related activity`.
- (c) Render both headings with the state in the first panel. This shows an empty Related activity heading.

**Q5. Ruling 22's "explicit cutoff before completion" cannot be reached by a browser capture.** (new; backlog K3 Low 3)
- Evidence: the producer completes the WR (ASSIGN/COMPLETE, `w502_cold_work_walkthrough.py:207-218`) before it POSTs the Action link and intent (`:246-253`). The Action's `recorded_at` therefore comes after completion. Any cutoff before completion reads `ACTION_NOT_FOUND` 404 (`domain_action_index.py:199-201`), not the not-linked sentence. The not-linked branch is reachable for a cutoff `K1 <= c < K2`: the Action exists and has no case link yet, and `_work` returns all-null (`:263-273`; manifest K values `:253`). A linked OPEN WR has no fixture.
- (a) Recommended: prove the completed sentence at a CURRENT cutoff, and prove `No completed inspection is linked to this Action.` with an explicit cutoff in `[K1,K2)`. Record that "before completion" is unreachable because the Action is recorded after completion. Cover a linked OPEN/IN_PROGRESS WR in a component test, and add the matching `links.work` assertions at both cutoffs to K5's backend lineage test. K4b extends `attest` to require these detail reads.
- (b) Add a producer mode that links before it completes. This contradicts ruling 22's ordering for that mode.
- (c) Prove the branch with component tests only.

**Q6. The Action strip cap 100/120 is likely to fail for the worst-case owner.** (new; see the cap audit)
- Evidence: the worst-case Actions carry a 160-code-point owner that contains an unbroken run of about 115 `y` characters (`w502_cold_work_walkthrough.py:281-283`). The status line renders `{owner} · {shortName} · Finding {id8}` plus the `Finding version` disclosure (`SiteAnalyticsFrames.tsx:1436-1447`). The strip is 11 px / 1.5 line-height, wraps, with 6 px row gaps and 10/14 px padding (`primitives.css:4945-4957`). Without `overflow-wrap:anywhere` the run (about 630 px) overflows a 330 px strip at 390. With wrapping, the estimate at 390 is about 135 px closed and about 160 px with the disclosure open; at 1440 it is about 88 px closed and about 105 px open. The mock strip is 44/44 (`W5-02-04-mock-measurements.md`, `cold-action`).
- (a) Recommended: wrap the status line with `overflow-wrap:anywhere` on the owner text only, never on the UUID. Keep 100/120 for the positive fixture Action (short owner). For the 160-character-owner Action, set the strip cap to 140/200 at 1440/390 and exempt the open `Finding version` state from the strip height cap, keeping containment and no-overflow.
- (b) Apply no strip height cap to the long-owner Action; only containment gates.
- (c) Clamp the owner to two lines in the strip with a full-text disclosure. This adds an element the mock does not have.

**Q7. What is K4b's "worst-case" Action?** (new)
- Evidence: the K4b card says "worst-case captures at both widths" (`build-spec:104`). The caps were derived assuming "36-character IDs, 160-character source/error, four criteria" (`:38`). The only long Actions are the five `worstcase` Actions: 160-character title and owner, `intent:null`, no WR link (`w502_cold_work_walkthrough.py:276-292`). No long Action has an intent and a completed WR. The criteria text is fixed (`domain_action.py:34-39`).
- (a) Recommended: worst-case = worstcase Action 1 (long title/owner, missing intent, not linked, disabled Inspect copy); populated = the positive fixture Action. Both are captured at 1440/390.
- (b) K4b extends the producer to add an intent and a WR link to one long Action, re-asserting K2/K3 counts and ordering.

**Q8. Which control forms do `Inspect maintenance evidence` and `Open source Finding →` take?** (still open)
- Evidence: the spec rules a disabled Inspect button with the adjacent `Maintenance detail is unavailable for this record.` (`build-spec:62,297`). P-K2a-37 calls `Open source Finding →` "an unavailable control" with `The selected Finding revision cannot be opened here yet.` (`:307`) but gives no element. Nothing on main renders either control yet (no hit outside tests for either literal). The repo's no-disabled-affordance pattern is `UnavailableEntry` (`ui/UnavailableEntry.tsx:5`), but its guard covers only the tab row (`navigation-truthfulness.ps1:158-166`). The mock shows a `button` and a link (`index.html:745`). With C2 mounted, Inspect is disabled only when no WR is linked.
- (a) Recommended: Inspect is `<button type="button" className="button" disabled aria-describedby=…>` plus a visible adjacent sentence, as ruled. `Open source Finding →` is plain muted text (no `href`, button or `tabIndex`) followed by its sentence, matching the `UnavailableEntry` pattern.
- (b) Both are disabled buttons.
- (c) Both are `UnavailableEntry` text. This changes the ruled Inspect element.

**Q9. A stored `shortName` does not exist.** (still open, Low)
- Evidence: P-K4a says "stored W4 `shortName` ... fallback to stored display name" (`build-spec:369`). There is no stored field. K2/K3 use the derived first-token `shortName()` (`siteWorkCases.tsx:269`), which the K2 shell already uses in the status line (`SiteAnalyticsFrames.tsx:1438`). For the fixture it gives `GreenHarvest`, matching the mock.
- (a) Recommended: confirm the derived `shortName(display_name)`. The breadcrumb keeps the full display name, as in the mock (`breadcrumbs: … site: GreenHarvest Cold Room`).

**Q10. The spec's `Due` sentence has no slot on `cold-action`.** (still open, Low)
- Evidence: `build-spec:70` says "Due cells use `YYYY-MM-DD` in UTC", but the `cold-action` mock has no due slot in the status line, the criteria or Related activity (`index.html:742-746`).
- (a) Recommended: render no due date on `cold-action`. The sentence applies to the `cold-work` Due column only.

**Q11. `A-cold-work-projections` cannot close in K4b as specified.** (new)
- Evidence: `build-spec:365` lets K4b close it after its ancestors are verified resolved. In the pilot registry `A-maintenance-index` is still `open` and requires `A-work-cases`, also `open` with task `W4-01`. `A-cold-excursion-rules` and `A-action-index` are resolved. W5-04 ruling 41 settled the parallel EV case: leave the node open and name the predecessor (`W5-04-preflight-rulings.md:45`).
- (a) Recommended: mirror ruling 41. K4b leaves the node open, names `A-maintenance-index` in the packet and still promotes the `cold-action` ledger row.
- (b) Authorize K4b to resolve `A-work-cases` and `A-maintenance-index` with merged W4-01/W6-01 evidence. This is out-of-slice registry work.

**Q12. Assign the backlog Lows.** (still open)
- Containment: the K3 ruling-20 rule `contain:inline-size; overflow-x:auto` applies to every cold case disclosure body (`w1f4-action.css:227-230`), and the capture's `inside`/`openBodyFits` pass any `overflow-x:auto` body (`w502-cold-work-evidence.mjs:380,385`). K4b owns both files. Recommended: scope the CSS and the relaxation to bodies whose direct content is the code (`.disclosure__body:has(> code)`). Give the K4 strip `Finding version` body the same one-line-UUID treatment outside `[data-cold-cases]`.
- MINIGRID `[data-cold-cases]` absent / cold present (`coldWorkCases.test.tsx:448-460`): that file is in K5's list, not K4b's (`build-spec:105`). Recommended: K5 owns it.
- Attest gap: the K2 Low (`MILESTONE_REVIEW_BACKLOG.md:2414`) looks closed. A mode without reads now appends a failure (`w502_cold_work_walkthrough.py:723-727`), and any `blocked` mode fails at `:747`. Recommended: K4b re-verifies this, deletes the stale line and adds the K4 detail reads (Q5) to `attest`.

**Q13. Remove `App.tsx` and `missing-claim-scan.mjs` from K4a's file list.** (new)
- Evidence: E4/E6 edit `App.tsx` (client injection plus the Scenarios route, `W5-03-build-spec.md:787,806`), and E4 edits `missing-claim-scan.mjs` (`W5-03b-ui-preflight-rulings.md:23`). K4a needs neither. The domain client is already injected through `SiteAnalyticsFrames.tsx:1552-1558`, `App.tsx`'s route set must not change (`build-spec:103`), and the disabled-Inspect literal does not match the scan (`:62`). Also note that `operatorRouteFrames.test.tsx:369-371` currently asserts the interim R69 Sites-active state, and K4a must invert it.
- (a) Recommended: treat both as read-only proof in K4a, edit `SiteAnalyticsFrames.tsx` only inside the domain Action region (`:1352-1600`), and rebase onto merged E4/E6 before review.

## Cap audit (K4 caps, `build-spec:38`; capture constants `w502-cold-work-evidence.mjs:52`)

| Cap (1440/390) | Worst-case content | Estimate | Verdict |
|---|---|---|---|
| Page main 1350/1750 | 160-char unbroken-run H1 (about 3 lines at 1440, 6-7 at 390), long-owner strip, two panels, notice | about 750 / about 1150 | fits; the H1 needs `overflow-wrap:anywhere` for containment |
| Strip 100/120 | 160-char owner plus `Finding version` (open) | about 88-105 / about 135-160 | **likely fail**: Q6 |
| Criteria 410/660 | four fixed rows; mock 287/428 | about 290 / about 430 | fits; `intent:null` is much smaller |
| Related 260/340 | sentence, Inspect, Finding unavailable text and copy; or not-linked plus disabled copy | about 160-180 / about 235-270 (about 300 with a hypothetical 160-char WR title) | fits |
| Notice 100/140 | the blue Action notice and a currentness notice, each capped | about 42 / about 60-95 | fits |

- `ACTION_CAPS` in the capture tool has no criteria or related caps (`w502-cold-work-evidence.mjs:52`). K4b must add 410/660 and 260/340.
- No K4 state has an open long-text disclosure in a panel; the only expandable element is the strip's `Finding version`. Q6 asks for its exemption once, so that K4 does not repeat the cap-only rounds K2 and K3 needed.
