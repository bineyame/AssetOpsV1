# W1-F4 review packet: Recommendation, Changes, Action screens, Verification, Site Work to v69

- **Task:** W1-F4 (`.agent/W1-F4-actions-work-build-brief.md`), contract `D-2026-10-17-mockup-layout-spec` (`.agent/architect-W1-fidelity.md`).
- **Branch / worktree:** `task/W1-F4-actions-work` in `AssetOpsV1-review4`, base `af1aa23e` (main with W1-F1). Not merged.
- **Commits:** `cf2eec5b` page descriptions, `3560b3aa` recommendation, `410ff7d1` changes + sitework (group B), `5b663628` Action overview/execution/history (C1), `076064dc` Plan/Evidence/Verification (C2), `4016b4fc` planted-panel proofs, plus this packet/evidence commit.
- **USER_REVIEW_REQUIRED:** yes (owner walkthrough of W1 fidelity; hold merge for it).

## Outcome
Nine screens rebuilt to their v69 panel set, order and titles. Every W1-UX-04 answer card (`[data-headline-card]`) is gone on these routes: its state line now leads the one-line `.status-strip`, and its steps/bars/limits are merged into the owning panel (key values, table rows, one chart-note line, closed "How this was worked out" disclosure). Page refusals render as `[data-page-refusal]` lines before the panel slots, and every slot keeps its title with an in-panel `[data-panel-gap]`.

## Panel lists (v69 vs app, enforced by `expectV69Panels` exact-title equality)
| Screen | v69 panels | App panels | Leading patterns |
| --- | --- | --- | --- |
| recommendation | Proposed intervention, Declare success before evaluating, Evidence needed to verify | same | strip; acceptance-limit notice between pair and panel 3 |
| changes | Change and effect, Decision path | same | strip, four metric cards from the read |
| action-overview | Action scope | same | page refusal only when refused |
| action-plan | Success criteria | same | strip |
| action-execution | Activity log | same | - |
| action-evidence | Evidence requirements | same | strip |
| action-history | Action history | same | - |
| verification | Target and guardrails evaluated together, Activity evidence, Outcome evidence | same | strip, four metric cards |
| sitework | Actions at this site | same | strip, window chips |

Merged-away app panels: recommendation (battery trial, accepted proposal, live recomputation, prior-action hold, Actions list, accept control, money link -> panel 1); changes (What changed, Outcome, Later effect, Application, Foundation versions -> Change and effect / Decision path); Action (state/work/history cards -> their single panel; verification outcome history added to Action history with earlier/current labels and withdrawable RESOLVED); Plan (Windows panel -> Success criteria); Evidence (window panels -> Evidence requirements, readings in one closed disclosure); Verification (Outcome, guardrail, inconclusive, no-outcome panels -> panel 1 and Outcome evidence).

## Changed assertions (none weakened; each guarantee re-asserted where the content now lives)
- **siteFoundationChange:** h1 is now the site name (v69 heading); change title asserted as strip lead `Battery reserve change · Applied`. "Not found" h2 -> `[data-page-refusal] .page-refusal__title` (refusals are never panel headings). Answer-card test -> no card; state in strip; scope/as-of/outcome words asserted outside any closed `<details>`; Outcome metric never green and says "No verification plan yet"; 4-step `not done` check replaced by the outcome metric's non-positive tone + text; attempts-refused now asserts the in-panel gap text and absence of any "0 recorded"/"No failed attempts" claim (stronger: whole body).
- **siteWorkActions:** proved-zero and unknown headings -> text inside the one panel (`[data-site-work-proved-zero]`, `.w1f4-work-state__title`). Card tests -> strip `[data-site-work-status]`, scope and read time visible; disclosure vocabulary scan widened from card to `<main>` (violations still `[]`); `disclosures === 1` dropped because the scan now covers the whole main (several disclosures by design). Value-bar count dropped (bars removed with the card; the table is the content). No-instant case still asserts "Read time not recorded", never now, and no zero claim (now body-wide).
- **siteAction:** card -> `panelTitled("Action scope" | "Activity log" | "Action history")`. Step counts -> key values (`action` accepted time, `application`, `outcome` label; `attempts` "N recorded, N failed", `trial`); history step count -> `[data-action-event]` row count (same number). Done-step -> outcome badge in amber, never green. Actor column -> named `[data-action-event-actor]` cell, count equals events and every one is SYSTEM demonstration. Application words on execution -> `[data-action-work-headline]` (Overview keeps `data-action-application-words`). Selector-propagation checks exclude only the new unselected `/verification/history` read and add `gets.length > 0` so they cannot pass empty. Not-found/selection refusals -> page-refusal titles; the slot keeps its titled panel with `action-unread` gap.
- **siteActionVerification:** card lookups -> strip `.w1f4-verification-strip` + owning panel. Failed limits ("measured 10 min, limit 0 min", "60 min") and known-failure lists asserted in panel 1 **and** outside the closed disclosure (`visibleOutsideClosedDisclosure`). Tone checks keep `not positive`. Reassessment: card bars `null` -> all metric cards are `Pending` gap words. Historical: source/demonstration/historical label asserted visible; outcome marked `data-verification-historical-outcome="yes"`. Plan: 3 steps -> 2 windows in Success criteria; no plan -> in-panel gap. Evidence: "12 of 12 readings" -> requirement row "12/12 slots complete"; gap case adds `requirement-ok="no"` and the GAP problem visible outside the disclosure. Overlap hold: strip keeps text, `problem` tone, held link, one disclosure, plus a W1 vocabulary scan over main.
- **S6-02b fail-closed checks:** unchanged files / assertions; all pass in the full run.

## Structure tests (new)
`frontend/src/sites/__tests__/w1f4RecommendationStructure.test.tsx` (stocked, accepted, held, empty, refused 404/503), `w1f4ChangesWorkStructure.test.tsx` (changes stocked/empty/attempts-refused/404; sitework stocked/proved-zero/no-window), `w1f4ActionStructure.test.tsx` (3 views x stocked, empty, historical, events-refused, not-found, selection-not-found; verification-history refused), `w1f4VerificationStructure.test.tsx` (plan/evidence/verification stocked, empty, refused, selector conflict, historical). Non-vacuity: `expectPlantedPanelRejected` (`frontend/src/test/panelStructure.ts`, additive) plants a titled `section.panel` before panel 1 on the rendered route, asserts the guard throws, removes it and re-passes: one test per route (9 routes, 12 tests). F1's generic plant tests (h3 card, untitled card, strip bulk, stray block) still pass.

## Checks (revision `4016b4fc`, frontend code unchanged after)
- `npx.cmd tsc --noEmit`: clean.
- F4 structure + guard tests: 5 files, 70 passed.
- Full `npm.cmd test`: 80 files, **2017 passed, 1 failed** in 214 s. Failure: `siteFinancials.test.tsx > Interpretation history (S4-08) > reloads page one at the same moment when the basis changed (typed 409)` (URL still had `&history_after=stale` at assertion time). File untouched by F4; reran alone twice: 75/75 both times. Recorded as a load-timing flake, not fixed (out of scope).
- `tools/check-all.ps1`: All 10 guards passed (232 s).
- `npm.cmd run build`: built (chunk-size warning only).
- Backend: not run (frontend-only slice).

## Captures (`node tools/w1-fidelity-evidence.mjs`, 1440 and 390, app vs mock)
Fixtures: `s601b_action_walkthrough` (API 8981 / web 5481), `s602b_verification_walkthrough` (9082+9083 / 5582+5583, `--case guardrail`), `s603_site_work_walkthrough` (9090 / 5590). All three fixtures dropped afterwards (databases and `var/` folders removed).
- `.agent/W1-F4-evidence/s601b/` - recommendation accepted/held/unavailable, changes applied, action-overview, action-execution applied/failed, action-history all/event: **108/108**. (A first run had 2 fails on the very first page: blank app before Vite's cold compile; rerun warm, all pass.)
- `.agent/W1-F4-evidence/s602b/` - action-plan, action-evidence, verification (pass, historical, guardrail) and the guardrail recommendation hold: **96/96**.
- `.agent/W1-F4-evidence/s603/` - sitework active/zero/no-window: **36/36** (same cold-start note).
Each folder has `index.html` (side-by-side pairs) and `evidence.json`. App and mock panel counts match on every pair; no horizontal overflow at 390.

## Heights against the mock (1440, panel top y / height in px, app vs mock)
| Screen:case | App | Mock |
| --- | --- | --- |
| recommendation accepted | 346/785, 1245/348 | 366/370, 814/234 |
| recommendation held / unavailable | 346/871 or 811, panel 3 123 | same mock |
| changes applied | 386/679 | 547/319 |
| action-overview | 247/611 | 304/268 |
| action-execution applied / failed | 247/929 / 759 | 304/211 |
| action-history all / event | 247/657 / 370 | 304/243 |
| action-plan pass / guardrail | 374/672 / 734 | 304/287 |
| action-evidence pass / guardrail | 352/616 / 678 | 304/262 |
| verification pass / guardrail | 523/456 + 1013/678 ; 500/578 + 1112/695 | 586/336 + 940/252 |
| sitework active / zero / none | 303/439 / 284 / 223 | 409/234 |
Panel tops sit at or above the mock's (no layer above panel 1). Panels are 2-4x the mock's height: the reads carry more rows than the mock (e.g. execution has 6 real events with full identifiers vs the mock's 3 short rows) plus the merged key values and one-line notes. See deviations.

## Known deviations
1. **Panel height (Medium risk for review).** Merged content (key-value rows, recorded identifiers, real event counts) makes panels 2-4x the mock's height, worst on action-execution (929 vs 211) and recommendation panel 1 (785-912 vs 370). No body-size explanatory panel prose was found in the capture checked (execution notes are chart-note size), but the reviewer should judge prominence per the F1 rereview "bulk" standard; candidates to trim are the Activity log key-value block and the recommendation panel-1 merged hold/live-recomputation block.
2. Recommendation held/unavailable states draw no small visual (unchanged since W1-UX-06; no read supports it).
3. Rail visible at 390 (shell scope, W1-UX-07/F5), as noted in F1.

## Residual risk / user-review focus
- Owner: compare `index.html` pairs for recommendation and action-execution first (largest height gaps).
- The `siteFinancials` S4-08 timing flake can recur under full-suite load.
