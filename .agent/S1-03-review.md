# S1-03 review: Foundation organized as Site model, SLD and Readiness

- **Reviewer:** a fresh Claude Reviewer (Opus). I did not author any of this slice, and I did not edit, fix or commit any tracked file.
- **Reviewed:** `git diff f639990..3d944e1` on `task/S1-03-foundation-organization`.
- **Commit landed during the review:** `98a255b Record owner S1 UI acceptance`. It adds only `.agent/owner-S1-acceptance-2026-10-08.md` and changes no code, so this verdict still applies to the code at HEAD.
- **Authority:** `D-2026-10-08-s1-foundation-organization`, sections 2 and 3, and `tasks/S1-03-foundation-organization.md`.

## Verdict

**Accept with carries.**

There are no blockers. The build matches section 2 of the decision, the backend is untouched, and every check I ran passes.

The two most important carries:

- **M1:** an imported Site whose store read fails is told it has no stored Foundation.
- **M2:** the navigation guard is a declaration check, not a rendering check, and the order of panels inside a view has no test or guard at all.

## Checks I ran

| Check | Result |
|---|---|
| `tools/check-architecture.ps1` | Passed |
| `tools/check-agent-workflow.ps1` | Passed |
| `pytest backend/tests -q` with `ASSETOPS_TEST_DATABASE_URL=.../assetops_test` | 1572 passed |
| `npx.cmd tsc --noEmit` | Clean |
| `npm.cmd test` | **Ran this time and did not hit the known sandbox failure:** 49 files and 1170 tests passed. |
| `npm.cmd run build` | Built. The only warning is the existing chunk-size warning. |
| Backend diff `f639990..3d944e1 -- backend` | Empty: no backend or API change |
| `tools/layout-evidence.mjs` | Not rerun by me. The packet records it honestly: KOBO-001 had 200 PASS and 0 FAIL before it aborted at Lab run-setup, and the MG-001 Lab FAILs are explained, not counted as passes. |

How the probes were run:
- All mutation and guard probes ran in a detached scratch worktree, so the owner's :5183 server was never hot-reloaded. The worktree has since been removed.
- For the Q1 check I ran my own Vite server on :5241, sending read-only GETs to :8010; it is now stopped.
- :5183 and :8010 were not touched, and I did not write to `assetops`.
- Port 5199 was already held by another process; I left it alone.

## Against section 2 of the decision

- **Views and routing: met.** There are three direct-linkable views in mock order (`/foundation`, `/foundation/sld`, `/foundation/readiness`), and every view link carries `?at=` (`SiteFoundationFrame.tsx:95`, `operatorSiteRoutes.ts:72-75`).
- **Old navigation removed: met.** The contents row is gone. `Changes` (or `Change & effect`) is absent, and `/foundation/changes` renders `RouteNotAvailableFrame` (`SiteFoundationFrame.tsx:62`).
- **Panel order: met.** I checked `StoredFoundationViews.tsx:152-196`, `:320-354` and `:421-437`:
  - **Site model:** strip → topology beside identity → controls with the reserve form → audit disclosures.
  - **Readiness:** verdict and missing items → role coverage → bindings with the action → gateway and sources → acquisition (hash and download) → scope note.
  - **SLD:** strip → diagram → parts and channels → detail disclosures.
- **No repeated binding table: met.** The binding table renders on Readiness only; the SLD's D5 table is behind a disclosure.
- **Strip on every view: met.** The strip, with the selector and the historical label, renders on all three views.
- **Behaviour (task item 3): preserved.**
  - The reserve form is on the Site model and the binding removal is on Readiness.
  - The snapshot link still uses `foundation.snapshotUrl(siteId, loaded.resolved.at)`.
  - A legacy Site keeps its single page with no view row.
  - The Lab shell code is unchanged apart from the shared CSS in Q1.
- **Truthfulness: no problems found.**
  - The new source contains no online, reporting, connected or healthy claim, and no mock value (MG-DEMO-01, Nairobi, 35%/90%, GW-MG-01, "synced").
  - The gateway reads "registered, awaiting credentials, not sending data".
- **Binding-period fix: correct.** `FoundationRevisionPanel.tsx:138-152` checks for a current Foundation shown with a FUTURE or PAST binding set, and the mutation probe confirms its test catches a regression.
- **"Not configured: Battery reserve" fix: correct.** `FoundationBindingsPanel.tsx:68-81` splits FOUNDATION_CONTROL roles from channel roles, and the mutation probe confirms its test catches a regression.

## Findings

### Major

**M1. An imported Site whose store is unavailable is told it has no stored Foundation on its SLD and Readiness addresses.**
- **Where:** `frontend/src/shell/SiteFoundationFrame.tsx:139-156`.
- **What is wrong:** the "This view needs an imported Site" branch is taken for every non-loaded status that falls through: `unavailable`, and `not_found` or `invalid` when there is no `at`, not only `migration_required`.
- **Failure scenario:** Postgres is briefly down, or the Foundation API returns 5xx. Someone opens a shared `/sites/KOBO-001/foundation/readiness` link. They see the heading "This view needs an imported Site" and the statement "This site has no stored Foundation version, signal binding set or snapshot". For an imported Site, that is a false statement of fact.
- **Contrast:** the Site model address handles the same failure honestly. Its notice reads "Stored versions could not be read…" (`:168-175`).
- **Why it matters:** the decision requires named, truthful empty states. This one asserts that records do not exist when they could not be read.
- **Fix:** take this branch only for `migration_required`. For `unavailable`, `not_found` and `invalid`, render the same "Stored versions unavailable" notice, or the message, that the model view uses. Add one test that renders `/readiness` with `{status: "unavailable"}`.
- **Classification:** acceptance gap (truthfulness). It is not a blocker, because it appears only on an infrastructure failure.

**M2. Two gaps in what the guard and the tests protect.**
- **Where:** `tools/checks/navigation-truthfulness.ps1:409-420`.

**(a) The guard checks the inventory declaration, not what renders.** I tried three bypasses against `check-architecture.ps1` (each reverted). All three passed the guard:

| Bypass | Guard | Vitest |
|---|---|---|
| A `label: \`Changes\`` entry (backtick quotes) in `FOUNDATION_SUBTABS` | Passed: the label regex accepts only `'` and `"` | Caught |
| `label: CHANGE_LABEL`, where `CHANGE_LABEL` is a constant | Passed | Caught |
| A hard-coded `<Link aria-disabled="true">Change &amp; effect</Link>` placed next to `<FoundationSubtabs>` in `StoredFoundationViews.tsx` | Passed: the guard scans only the module that declares the inventory | **Not caught** (80/80 still pass) |

- Why the third gap matters: the old Site-model test checked the whole screen for "changes" text (`spacedText(container)`). The rewrite narrowed it to the view row (`foundationScreen.test.tsx`, "never offers Change & effect"). So nothing now stops a disabled `Change & effect` destination from being rendered beside the row, which is exactly what the decision forbids.
- The control probe worked as intended: relabelling a view made the guard fail with a clear message.
- **Fix:**
  - Make the label regex accept backtick quotes, and fail when any `label:` value is not a string literal.
  - Restore a whole-page check for `/\bchange(s| & effect| and effect)\b/i` on each of the three views in `siteFoundationRevision.test.tsx`.
  - Alternatively, extend the guard to forbid that vocabulary as link text in `StoredFoundationViews.tsx`.

**(b) The order of panels inside a view has no protection.** Probes that moved a panel, rather than duplicating it, all left 80/80 passing:
- the acquisition details moved above the verdict on Readiness;
- the signal bindings swapped with the verdict on Readiness;
- the controls moved above the topology/identity pair on the Site model.

`layout-evidence.mjs` does not check order either. Panel order is the substance of the owner's complaint and of section 2, so it should carry at least one assertion per view.
- **Fix:** in a test, read the `h2` order inside `main` for each view and compare it with a written-out list.

What the tests do catch: view-row order, dropping `at` from view links, removing the strip from a view, reverting either truthfulness fix, "connected" wording, record IDs leaving their disclosure, and a binding table repeated on the SLD.

### Minor

**m1. The ≤640 px shell rule hides the rail group labels.**
- **Where:** `frontend/src/ui/primitives.css`, in the new `@media (max-width: 640px)` block: `.nav-rail__group-label { display: none }`.
- **Effect:** at phone width the OPERATE and INTELLIGENCE headers from T028 disappear, and Sites and Findings sit side by side with no grouping.
- **Impact:** low today, with two items. It is a silent drop of a decided rail grammar, so it should be named in Q1 rather than left implicit.
- See Q1 below for the rest of the shell-rule assessment.

**m2. The SLD view puts two paragraphs of explanation before the diagram.**
- **Where:** `SiteSldPrimary` (`SiteSingleLineDiagram.tsx`); see `app-sld-1440-full.png`, around y 440-530.
- **Effect:** at 390 px the diagram starts below the first viewport.
- **Why it matters:** the decision makes the diagram the primary visual. This is a preference-level hierarchy issue, not a gap; the paragraphs could follow the diagram or sit behind a disclosure.

**m3. Critical-load priority appears twice on the Site model, in two vocabularies.**
- **Where:** `StoredFoundationViews.tsx:299-303` (names: "Health clinic → Residential feeder → Grain mill") and `FoundationRevisionPanel.tsx:284` (codes: "load-clinic → load-res → load-mill").
- Source priority likewise shows raw codes.
- **Why it matters:** someone verifying S1 has to map codes to names by eye.
- **Fix:** use names in the controls table too, or drop it from the identity panel.

**m4. Readiness is still the densest page (3,068 px at 1440).**
- Role coverage and the binding table both state role → channel for every role, so the same mapping is read twice.
- This is acceptable under the decision, which allows coverage and binding details to be grouped. A later pass could put the channel table behind a disclosure, since the Binding IDs are audit material.

**m5. The topology cards follow one upstream chain per bus feeder and one hop for loads.**
- **Where:** `StoredFoundationViews.tsx:204-243`.
- **Effect:** a branching supply chain or a two-level distribution would lose parts on the cards. They remain in the SLD.
- The packet already names this risk, and KOBO-001 is drawn correctly.

### Notes

- **n1.** `SiteFoundationFrame` calls `useSiteFoundation` before refusing a bad segment (`:48` vs `:62`), so `/foundation/changes` still fetches the Foundation. This is harmless.
- **n2.** In the Q1 captures, the header's bottom rule spans only the brand block at ≤640 px (`app-foundation-390-viewport.png`). Cosmetic.
- **n3.** The packet's frontend numbers (1170 tests and a clean build) matched what I saw.

## Screenshots, app against mock

At 1440 px the hierarchy now follows the mock closely.

- **Site model:**
  - It shows the view row, the strip with version, period, bindings, gaps, the Readiness link and the selector, then topology cards beside identity, then the controls with the reserve form inline, then four closed audit disclosures.
  - The page is 1,762 px.
  - Version, reserve and SLD are each found in under one scroll.
- **Readiness:**
  - It leads with the verdict and four counts, the way the mock's area cards do.
  - The SOC and generator-status bindings can be found in role coverage, and the hash and download sit in the labelled acquisition area.
  - The gap variant leads with "Unknown" and names the missing roles in the first viewport at 390 px.
- **SLD:**
  - It shows the diagram and then a clear parts and channels table, with audit tables closed.
  - Apart from m2, this is the cleanest of the three.

At 390 px all three views stack sensibly: the strip, then the row of views, then the panels. They are not dump-like any more; what remains is m2, m3 and m4.

The omissions listed in `INDEX.md` are honest and correctly reasoned: gateway status, connected sources, commissioning evidence, `Change & effect`, and evidence links.

## The four questions in `S1-03-questions.md`

**Q1. Shell-wide rail stacking at ≤640 px: keep it (option a).**
- Method: I captured Lab and operator pages at 390 × 844 on my own server, with the rule on and again with it disabled.
- Without the rule, the Lab is unusable at 390 px. The 216 px rail leaves about 140 px of content, for example "Draft run" wraps word by word.
- With the rule:
  - Lab home, Site Templates, Scenarios, a draft run, Create a site and Sites all render with no horizontal page scroll.
  - The four Lab rail items fit on one wrapping row.
- I found no regression it causes. The draft-run "Why this draft cannot be executed" table is still tall and cramped at 390 px, but it is worse without the rule, so the rule did not cause it.
- Residual risks:
  - The rule hides rail group labels (m1).
  - The existing `640x700` layout-evidence width now measures the stacked layout, so the earlier "rail beside narrow content" case is no longer measured at any width.
  - The Lab layout claims remain unmeasured, as in S1-02.
- I'd record this as a shell decision rather than an S1-03 side effect.

**Q2. Legacy view addresses show a named panel rather than redirecting: agree with a named panel.** A named panel explains a shared link better than a silent redirect does. Restrict that panel to `migration_required`, though (M1).

**Q3. Three legacy-only panels left off the imported Site model: agree.** "Configuration is fixed at creation" would be false once the reserve can be published. The other two are duplicated or superseded by the Readiness view.

**Q4. Unbound channels listed under the device's component: agree for S1.**
- Inferring the asset from the role would invent an association that S1 does not hold.
- The row reads "Not bound: battery-pcs-controller / state-of-charge" under the battery PCS. That is truthful, but it could confuse someone who sees the bound SOC under Battery.
- A short caption line, "unbound channels are listed under the device's own component", would remove the ambiguity.

## Residual risk the packet does not name

- M1: the unavailable-store wording on the SLD and Readiness addresses.
- M2: the guard can be bypassed by rendering outside the inventory, and panel order is unprotected.
- With the ≤640 rule, nothing measures the narrow rail-beside-content layout any more.
