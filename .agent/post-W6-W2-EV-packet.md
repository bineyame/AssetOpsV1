# post-W6 W2-EV review packet: EV Site screens D3 fixes

Branch `task/post-W6-W2-EV`, worktree `AssetOpsV1-review5`. Reviewer diff: `git diff main...HEAD -- ':!.agent'`.
Binding inputs: `.agent/post-W6-W2-EV-rulings.md` (cross-card ownership 1-8, Q1-Q31), `.agent/post-W6-W1-rulings.md`
cross-card contract, `.agent/post-W6-W1-a-closeout-rulings.md` ruling 5, `.agent/owner-ui-ux-guidance-2026-10-25.md`.
Pre-flight anchors: `.agent/post-W6-W2-EV-preflight.md`; build history `.agent/post-W6-W2-EV-phase-1-handoff.md`.

## Outcome

EV main tabs go to EV pages and carry the selected window; bare `/sites/:id` opens the EV Overview for an EV Site;
readiness Financials/Assumptions are live; Sessions and Finding link to EV Analysis at their own window; refusals use
the common set; Overview/Evidence/Analysis/Financials D3 duplicates are fixed; the Site Findings page has an EV branch.
Main (shell, W3-estate, W1-a, W1-b) is merged in; the canonical `siteTime.ts` now names Asmara, Djibouti and Mogadishu
as EAT and `LedgerSiteEvidence.EXTRA_EAT_ZONES` is deleted (W1-a closeout ruling 5). Frontend only: no backend change.

## Commits

3c533f0f interfaces · fc95d2e3 U1 · 74c86e64 U2 · 620a5902 U3 · 39ac52c4 U4 · 3a3bb00b merge main + EAT zones ·
01d19b76 register R420/R421 · ce4a8dd1 Sessions/Finding refusals (ruling 5) · dab4d15e EV Findings title column and
strip separators (Q26 fallback) · 93e6d9bb, 67b5e5ec, 0134f893, c47d003f captures · (closeout commit: packet, CODE_STATE,
ACTIVE_CONTEXT).

## Files materially changed

- Shell: `operatorSiteTabs.tsx` (href override, `operatorSiteTabHref`), `evSiteRoutes.tsx` (`EV_SITE_TAB_HREFS`, routes
  `health`/`work`/`portfolioEvidence`, `timeZone`), `SiteAnalyticsFrames.tsx` (EV Sessions/Finding mounts, EV Findings
  branch, `FINDING_SECTION_UNAVAILABLE`), `SiteFoundationFrame.tsx` (two readiness hrefs, EV tab override),
  `SiteDetailFrame.tsx` (EV redirect), `App.tsx` (`evAssessment` to Site Findings).
- Sites: `EvSiteViews.tsx`, `EvAssessmentViews.tsx` (now holds the shared `RefusedHead`/`RefusedGap`/`NOT_ASSESSED`, used
  by the EV Site pages, Sessions, Finding and the EV Findings index), `EvFoundationViews.tsx`, `EvFindingIndex.tsx` (new),
  `evSelectedWindow.ts` (new), `siteTime.ts` (new on this card, identical on main; +3 EAT zones), `coldSiteViews.tsx`
  (`eatTime` delegates), `LedgerSiteEvidence.tsx` (local zone list removed), `SiteFindingIndex.tsx` (export
  `LensChips`), `w2-ev-assessment.css`.
- Guards: `tools/checks/missing-claim-scan.mjs` (readiness exemption reason).
- Register: `.agent/mock-departure-register.md` R420 (R270 split, Q4 D4) and R421 (R286 split, Q13 D4), inside the
  W2-EV block R420-R434 (W4 ruling 22).

## Acceptance status (rulings)

| Ruling | Status | Evidence |
| --- | --- | --- |
| Ownership 3 / Q14 / Q23 tabs + EV home | done | operatorSiteTabsOverride, evSiteMoneyRoutes, evAssessmentRoutes, siteDetailRoute; captures |
| Ownership 5 / Q11 refusal set | done (Sessions/Finding fixed at ce4a8dd1) | evSiteMoneyRoutes; evAssessmentRoutes `expectOneRefusal` (strip title, sentence exactly once in-panel, technical disclosure, no banner, Sessions tiles `Not assessed`); probe sentence count 1 on every refused/one-sided/long case |
| Ownership 6 / Q8 / Q18 | done | `FINDING_SECTION_UNAVAILABLE` one copy; miniDecisions; siteTime |
| Ownership 8 / Q26 caps | pass on the variable-cell reading; see Caps | |
| Q1 / Q21 readiness links | done | evFoundation; missing-claim guard proven non-vacuous (untagged phrase in `EvFoundationViews` failed) |
| Q2 unique labels | done | evFoundation duplicate-role test |
| Q3 lineage link | done | evAssessmentRoutes |
| Q4 denominator line | done, D4 R420 | evAssessmentRoutes zero/positive |
| Q5 Outcome column | done | CSS assertion; missing-meter captures |
| Q6 / Q7 Finding strip + claim link | done | evAssessmentRoutes |
| Q9 plural | done | evAssessmentRoutes, evSiteMoneyRoutes |
| Q10 chronology | done (render all; no mounted Event details target) | none/one/eight events |
| Q12 Energy source | done | evSiteMoneyRoutes |
| Q13 billing chip | done, D4 R421 | evSiteMoneyRoutes both DTO values |
| Q15 B9-02/06/07 | done | evSiteMoneyRoutes (cards, evidence, timezone Addis/UTC/midnight/missing) |
| Q16 / Q19 EV Findings branch | done | evFindingIndex; mini s404 index unchanged; captures |
| Q17 Foundation frame | done | foundationScreen, siteFoundation* |
| Q22 navigation fixture | done | check-all 11/11 (navigation-truthfulness) |
| Q27-Q29 captures | done; see Captures | |
| Q30 named gaps | DTO tests only | |
| Q31 register | R420/R421 added open; statuses update after review | |
| W1-a closeout 5 | done | siteTime, v01bEvidenceVisual, siteFinding: all three zones EAT with exact UTC; proven non-vacuous (removing the table rows fails all 6 screen tests) |

## Checks

- At dab4d15e (product code final): `tsc --noEmit` clean; focused suites (27 files, 784 tests: EV, cold, mini Finding,
  siteTime, tabs, site detail, v01b evidence) pass; full vitest 133 files / 3179 tests pass (355 s, log
  `r2/logs/vitest-full.log`); `npm run build` passes (77 s, chunk-size warning only); `tools/check-all.ps1` 11/11 at
  dab4d15e (`r2/logs/check-all.log`).
- Earlier, at 01d19b76: `tsc --noEmit` clean; focused suites (36 files, 1164 tests) pass; full vitest 133 files / 3179 tests
  pass (wall 483 s); `npm run build` passes (chunk-size warning only); `tools/check-all.ps1` 11/11 (run at 3a3bb00b; the
  later commit changed comments, test names and the register only).
- Backend: no backend code changed on this card, so no backend suite is required.

## Known deviations

- Assumptions route is `/ev/financial-assumptions` (ruling text "/ev/assumptions" was shorthand).
- No missing-claim baseline entry existed for EV readiness to lower; only the exemption reason changed.
- R270's line is the first line of Sessions panel 1, because the v69 panel guard rejects an element between cards and
  panel 1.
- Bare `/sites/:id` shows the mini loading state until the Site type is read; tab query arrives one effect tick after
  the read settles.
- UI decisions taken locally (owner UI bar; NN/g consistency and GOV.UK error-summary practice: one message, one place):
  Sessions/Finding refusals reuse the EV Overview refused pattern; EV Findings strip parts get ` · ` separators (they ran
  together: "1 open6 Oct ... UTCEV charging Findings ..."); EV Findings rows reuse the mini index column treatment.
- Merge: `SiteFindingIndex.tsx` took W1-b's `LensChips` (hrefs, D5 R394) and kept W2-EV's export.

## Captures

All at product code dab4d15e (later commits touch `.agent/` only; evidence revisions read dab4d15e/93e6d9bb/67b5e5ec/c47d003f).
Folder `.agent/post-W6-W2-EV-recapture/r2/` (run scripts, logs, `tools/summary.py`, `tools/caps.py`). The first run's
folders beside it (at 01d19b76) are superseded. Producers unmodified: `.agent/W2-F-evidence/seed.py` (ev interrupted,
complete, missing-meter, fault, contradictory; cold excursion) into `assetops_w2evrc_{i,c,m,f,x,k}_test`;
`tools/s404_finding_index_walkthrough.py` prepare/serve/drop into `assetops_s404_owner_w2evrc_audit`;
`tools/w504_ev_work_walkthrough.py` prepare/serve/drop (`W504_API_PORT_BASE=18440`). Every DB dropped, every server
stopped by PID, `var/` work dirs removed by the producers.

- 122 app captures, 0 document horizontal overflow, 0 clipped text, 0 console errors (`tools/summary.py`).
- Indexed W2-EV set (Q27): 96 pairs (frozen audit target lists): batch-08 ev-readiness 6, sessions 24, ev-finding 12,
  ev-findings 4; batch-09 ev/evidence/analysis/financials/assumptions 10 each (interrupted, no-selection, refused,
  no-window, complete). Claims: 166/168, 240/240, 36/36, 60/60, 24/24 x3. The 2 failures are ev-finding
  `evidence-child` panel count (1 gap panel "Finding section" vs mock 3), expected for an unsupported child.
- Q29 extras: one-sided and 32-day on EV Overview and Sessions, 8 pairs, 48/48; probe: exact sentence once, `Not
  assessed` tiles, no banner.
- Q28 shared reach: ev-foundation, ev-sld (24/24); cold Finding root, `/recommendation`, `/evidence`, unknown child
  (44/48: the two child cases show the one gap panel with "This Finding section is not available for this kind of
  Finding. Open Finding overview"); mini Finding open and finding-evidence latest/not found (36/36); availability,
  energy, ev-scenarios current and refused-reversed (66/72). The 6 failures are the depth pages' refused state ("EV depth
  unavailable", raw `EV_WINDOW_INVALID` text, no panels): pre-existing audit B16-01, owned by W5-EV-Work (ownership 3,
  Q14/Q28), not touched here.

## Caps

Probe: `r2/tools/inspect.mjs` (W3 closeout ruling 1 method; every synthetic screenshot carries the red "SYNTHETIC LAYOUT
EVIDENCE, NOT PRODUCT DATA" label and `synthetic: true`). Results `r2/probe/part-interrupted/inspect.json` and
`part-varcells/inspect.json`. Closed panel px at 1440 / 390; every variant verified (5 rows, every intended field 160
chars), 0 clipped closed and all-open, 0 document overflow; 390 tables keep their own horizontal scroller.

| Panel (cap) | Real | Variable cells x5 | + 320-char gap | All cells x5 (informational) |
| --- | --- | --- | --- | --- |
| EV Accepted records (700/1000) | 399/357 | 562/577 (Source) | n/a | 1344/1032 |
| same, Source + Value | | 1344/655 | 1377/737 | |
| Sessions table (900/1400) | 206/240 | all cells 765/1258 | 798/1340 | 765/1258 |
| Finding Bounded conclusion (600/850) | 279/401 | 279/625 (5 lines) | 331/793 | |
| EV Findings index (550/850) | 159/159 | 429/699 (Finding title) | 462/781 | 1059/699 |
| Gateway list (1900 at 390) | 1669 at 390 | 1500 | 1533 | 16 rows 2239 |

- Reading used: W3 closeout ruling 2's definition, five rows with 160 characters in each variable visible text cell,
  typed values exempt. EV Findings has one free-text cell (title); the other six are fixed words (`Sessions`,
  `Not assessed`, claim and lifecycle words, `Not in this list`). Accepted records has Source label free text; Value is
  the record's formatted value + unit, times are formatted instants, Record is the UUID.
- Fallback applied (dab4d15e): EV Findings rows take the mini index row class (15rem title column at 390, 12rem at
  desktop, other cells one line). Before: title-only 425/2272 at 390 (a one-word title column); after 429/699.
- Open for the Architect: if Value counts as free text, Accepted records Source+Value is 1344 at 1440 (cap 700), because
  the mock-derived fixed column widths give Value 9% (`w2-ev-site.css` :144-149). Not changed: rebalancing mock column
  widths is a layout change; the measured fix would be Value about 20% taken from the three time columns.

## Residual risk and user-review focus

- Cap reading (above): confirm the variable-cell reading for EV Findings and Accepted records, or rule on Value.
- Refused Sessions/Finding now mirror the EV Overview pattern (strip title "Window cannot be read", tiles `Not
  assessed`, one in-panel sentence + "How this was worked out" disclosure). Review the Finding refused page: no tiles exist,
  so the strip carries only the title chip.
- EV depth refused pages (B16-01) still show raw codes until W5-EV-Work.
- Frontend only; no backend change, so no backend suite is required for this card.
- USER_REVIEW: owner sees it in the post-W6 walkthrough; merge on independent review ACCEPT.
