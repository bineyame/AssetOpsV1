# post-W6 W2-cold review packet: cold Site screens D3 fixes

Task: the post-W6 W2-cold card, D3 portion of R241-R261 (`.agent/post-W6-W2-cold-rulings.md`, Q0-Q15 and cross-card ownership 1-8; `.agent/post-W6-W1-rulings.md` cross-card contract). Branch `task/post-W6-W2-cold`, main `09196de0` merged in at `38fdff6d`. Frontend only: no backend, contract or schema file changed (`git diff main --stat -- backend host contracts gateway simulator` is empty). Reviewer diff: `git diff main...HEAD -- ':!.agent'`.

## Outcome

- Refused cold Temperature/Backup screens: strip, four `Not assessed` tiles, sentence once in panel 1, technical disclosure, no page banner. Window refusal copy is classified by code (ruling 5).
- Cold KPI units, the "Inspect temperature claim" link and the R245-R249 copy.
- Cold Overview: five "View detail →" cards; causal-strip outcomes joined from the backup chain; Single line diagram link; each limitation shown once.
- Cold Evidence: "Portfolio evidence" and "Review cooling →" links; the normal next-evidence copy.
- Cold Evidence Analysis: Measured/Sent/Received in the Site zone, using the canonical `sites/siteTime.ts`.
- New cold Site Findings index (R253).
- Cold main tabs keep `from/to/known_at` (ruling 3).

## Commits

Build:
- `2c879eb1` unit 1
- `30003578` unit 2
- `6b5d952e` unit 3
- `36b1b70e` unit 4
- `af70636f` tabs
- `710aea85` W2-cold's local copy of the W2-EV interfaces. Superseded by main's canonical files at the merge.

Coordinator step:
- `38fdff6d` merge main. The cold Findings branch is layered before W2-EV's EV branch, then the mini branch. Main's `siteTime.ts` and its test were kept.
- `8d1c0d59` register R435-R437 and visible labels.
- `47d7929c` cap fallback.
- `7beb5f72` and `8bfd4730`: the refusal sentence once per page, and the missing-zone header.
- Evidence: `5648c773`, `e2d83bd5`, plus r3 (see Captures).

## Files materially changed

- `frontend/src/sites/ColdAssessmentViews.tsx`:
  - refusal classification;
  - `PerformanceRefusal`;
  - `ColdFindingIndex`;
  - R241-R249;
  - `REPEATED_GAP`;
  - R435/R436 labels.
- `frontend/src/sites/coldSiteViews.tsx`:
  - Overview cards (R437 label);
  - strip join;
  - SLD;
  - Evidence links;
  - Analysis Site time;
  - `RefusedGap repeat`.
- `frontend/src/sites/w2-cold-assessment.css`: Findings row treatment.
- `frontend/src/shell/coldSiteRoutes.tsx`: `sld`, `workMaintenance`, `portfolioEvidence`, `coldTabSearch`.
- `frontend/src/shell/SiteAnalyticsFrames.tsx`: the cold Findings branch and cold tab search only.
- `frontend/src/App.tsx`: the `coldAssessment` prop.
- `frontend/src/shell/{SiteDetailFrame,SiteEvidenceFrame,SiteHealthFrames}.tsx`: tab search.
- `frontend/src/ui/V69Layout.tsx` and `primitives.css`: small additions (CausalTimeline ok tone).
- Tests: `coldFindingIndex.test.tsx` (new), `coldRoutes.test.tsx`, `coldSiteViews.test.tsx`.
- `.agent/mock-departure-register.md`: R435-R437.

## Acceptance status

| Ruling / ID | Status | Evidence |
| --- | --- | --- |
| Ownership 1-2 / Q1-Q2 cold Findings branch, `coldAssessment` prop; no EV client import | done | coldFindingIndex `r253_mini_site_keeps_the_mini_index`; s404SiteFindingIndex; captures of the EV and mini Findings representatives |
| Ownership 3 tabs (B14-10) | done for Overview, Evidence, Performance, Findings, Finding, Financials and Health. Work and Scenarios are W5-cold-Work's | coldFindingIndex tab hrefs; capture `tab known_at` (8/8 tabs) |
| Ownership 5 / Q4 / Q5 / R244 / R261 refusal set | done | coldRoutes `r261_refusal_copy` x4 (sentence exactly once, proven non-vacuous: 4 fail on the old code), `r244_backup_503...`; coldSiteViews `expectSentenceOnce` (403/503 on every cold Site route); r3 captures |
| Ownership 6 shared files | done | `SiteFoundationFrame.tsx`/`operatorSiteTabs.tsx` not edited; uses main's `siteTime`/override |
| Ownership 8 cap: cold Findings 550/850 | pass, worst case 539/786 after fallback | see Caps |
| Q3 / R253 index | done | coldFindingIndex: selected, empty, no-assessment, refusal, 403/503, cursor, windowed links |
| Q6 / R242 units | done | `r241_r242_claim_link_and_units`; 390 captures, no clipping |
| Q7 / R241 | done | `r241_r242...`, `r241_no_link_without_a_loaded_read` |
| Q8 / R254 Maintenance | done, D1 R437 | `r254_five_view_detail_links_at_the_window`; label test |
| Q9 / R255 | done | `r255_steps_join...`, `r255_running_outcome...` |
| Q10 normal gap | done | coldSiteViews evidence tests |
| Q11 / R259 | done | `r259_addis...`, `r259_utc_site_and_midnight_crossing`, `r259_missing_timezone...` |
| Q12 / Q13 | respected; no other UTC conversions; depth/Work left to W5-cold-Work | |
| Q14 routes | done | fixtures updated |
| Q15 recapture | done | Captures |
| R245 / R246 / R247 / R249 / R256 / R258 | done | `r245_no_selection_policy_copy`, coldRoutes strip/start-result cases, `r256...`, `r258...` |

## Checks

| Check | Result |
| --- | --- |
| Focused tests at `8bfd4730` | `coldRoutes` 62, `coldSiteViews` 67 and `coldFindingIndex` all pass (137 tests across the three files) |
| `tsc --noEmit` | clean |
| `tools/check-all.ps1` at `8d1c0d59` | 11/11 |
| Full vitest at `8d1c0d59` | 134 files, 3211 passed, 266.6 s |
| `npm run build` at `8d1c0d59` | ok |

Final rerun at product head `8bfd4730`: full vitest 134 files / 3211 passed (321 s incl. build); `npm run build` ok; `tools/check-all.ps1` 11/11 (incl. architecture, agent workflow, navigation truthfulness, missing-claim scan, screen ledger). No backend change, so no backend suite (coordinator instruction).

## Choices made (UI guide)

- **Guide §5: register and labels.** R435 (Priority/Lens `Not assessed`), R436 (not-in-global-list strip, Manage unavailable) and R437 (Maintenance card) are registered as D1 in the W2-cold block. Each carries a visible `MOCK DEVIATION D1 (Rnnn)` label next to the change: under the table, inside the strip, and inside the card. The labels sit inside the card and strip, not as page-level lines, because a line before panel 1 trips the panel-structure guard. That guard was not changed.
- **Guide §1: cold Findings cap fallback.** Rows take the mini/EV `finding-index-row` class, with 8 px cell padding, a 34rem desktop title column and a 14 px block episode line. The 390 table keeps its focusable horizontal scroller.
- **Guide §3 and ruling 5: refusal sentence once per page.** The sentence appears once, in panel 1; later panels refused by the same read say `Not assessed`, matching W2-EV's `expectOneRefusal`. The older W2-04 tests pinned the sentence in every panel; they now assert it once. Ruling 5 is the newer, specific ruling.
- **Requested-window line.** A window refusal (422 `invalid-window`) shows no requested-window line, because the bounds are what is invalid. Non-window refusals keep the line. This is the same as EV `RefusedHead` and ruling 5 ("never echoes the invalid window" in EV).
- **Guide §4: missing Site zone.** The Analysis headers read `Measured (UTC; Site time zone unavailable)`, the same suffix as EV.
- Cold Evidence Analysis and Assumptions refusals show the sentence without a strip. The mock has no strip on these screens (existing `cold-assumptions gets no status strip` test), so no strip was added.

## Captures

- **r2** (`.agent/post-W6-W2-cold-recapture/`, product `47d7929c`): 116 captures, each with its v69 mock at 1440x1000 and 390x900.
  - Sets: 92 indexed cold pairs; 16 URL-only one-sided and 32-day cases; the `cold-finding-excursion` representative; the main-tab row with `known_at`; EV Findings and mini Site Findings representatives.
  - Results: 696/696 checks, 0 document overflow, 0 clipping, 0 console errors, panel titles equal to the mock's.
  - R435, R436 and R437 are visible in every loaded capture with rows or cards.
  - Producers (unmodified): `.agent/W2-F-evidence/seed.py` `cold excursion|normal|backup-failed` and `ev interrupted` into `assetops_w2coldrc_{x,n,b,e}_test`; `tools/s404_finding_index_walkthrough.py` into `assetops_s404_owner_w2coldrc_audit`. All dropped, all servers stopped by PID.
- **r1** (`r1-8d1c0d59/`): the pre-fallback evidence.
- **r3**: (`r3-8bfd4730/`, evidence commit `ab0d7db9`, product `8bfd4730`): 34 refused captures (8 indexed refused cases, 16 URL-only one-sided/32-day, cold-finding start-refused-window) at 1440/390; 204/204 capture checks; 32/34 meet "sentence exactly once in panel 1, later panels `Not assessed`", 0 overflow/clipping/console errors, titles equal mock. The 2 others are the cold Finding start-refused-window case (both widths): the sentence shows in the page refusal block and in the Bounded conclusion and Operational context panels. This is the Finding's established section form, kept by Q4 ("the Finding keeps its established section form"); not changed here (see Known deviations). Producers: `seed.py cold excursion` -> `assetops_w2coldrc_x_test`, `cold backup-failed` -> `assetops_w2coldrc_b_test` (the Finding id exists only there); both dropped, servers stopped by PID. The r3 refused captures supersede the same-named r2 refused captures.
- **Not producible** (covered by selected-DTO tests per Q15): cursor, pending/stale, 403/503, an unmatched step. "Not determined" never appears in seeded data, so its 390 wrap was not shown on screen.

## Caps

Cold Findings "Findings at this site", closed heights at 1440 / 390 (cap 550 / 850). The probe is a browser-only DOM clone with a synthetic label: five rows, Finding title at 160 characters, plus a 320-character gap.

| Case | Before (`8d1c0d59`) | After (`47d7929c`) |
| --- | --- | --- |
| Real rows | 285 / 462 | 296 / 313 |
| Titles at 160 + gap (ruled case) | 603 / 2606 | **539 / 786** |
| Episode line also at 160 (informational; timestamp-built, not free text) | 691 / 4101 | 554 / 606 |

The fallback steps are in `fallback-steps/`. All disclosures open: unclipped.

Informational:
- Evidence Analysis accepted records: 391 / 485.
- Overview cards at 390: no clipping.

## Known deviations

- Work and Scenarios tab-window preservation, and cold depth/Action copies, are W5-cold-Work's (ownership 3, Q13).
- R244/R261 close only after all merged instances are reviewed.
- Register statuses for R241-R261 and R435-R437 update after review.
- Cold Finding refused window keeps its banner plus per-section sentence (3 occurrences) per Q4; ruling 5's "no duplicate page banner" vs Q4's Finding exemption is for the Reviewer/Architect to confirm. Not escalated as a blocker: Q4 is explicit.

## Residual risk and user-review focus

- The refusal change applies to every cold Site page, including the 403/503 states. Please review the wording of the later panels: `Not assessed`.
- The stricter probe, with the episode line also at 160, is 4 px over at 1440. It is informational only.
- USER_REVIEW_REQUIRED: per the post-W6 plan, the owner sees it in the combined post-W6 walkthrough. Merge is on independent review ACCEPT.
