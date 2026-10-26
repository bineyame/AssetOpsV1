# Review packet: post-W6 W5-EV-Work (EV depth and Work screens), complete

2026-10-26. Branch `task/post-W6-W5-EV-work` from main `104e9c33`. Frontend plus one backend copy string and one producer line.
Binding: `.agent/post-W6-W5-rulings.md` 3-5, `.agent/post-W6-W5-EV-preflight.md`, `frontend/docs/architecture/ui-ux-decision-guide.md`; handoff `.agent/post-W6-W5-EV-handoff.md`.

**Status: complete, `in_review`.** Nothing merged. USER_REVIEW_REQUIRED: fresh independent review gates merge; the owner sees it in the post-W6 walkthrough.

## Commits
| SHA | Unit |
|---|---|
| 01de9656 | R345 units and plurals, R244 depth refusals, R346 bridge quantity, R06 visible label, stale-basis copy (backend string + test) |
| 60f25c41 | R347 EV tab window and hrefs (depth, health, scenarios, Work mounts) |
| 8966ac30 | R348 ev-action window refusal, R349 refusal copy, R350 not-served Action sections (EV and cold) |
| 2e54c4d1 | R373 producer: Site Work router gets the case-detail service (`tools/w504_ev_work_walkthrough.py`) |
| 8929f9b8 | Cap fix: ev-health Condition table first column 40% at phone width (R470) |
| 2a7b872d | Recapture evidence, cap measurements, capture tools |
| (final) | Test updates for R350/R244, register, state docs, this packet |

## Files materially changed
- `sites/EvAvailability.tsx` (connector-h hours; `EvDepthRefusal`), `EvEnergy.tsx` (bridge row 1, R06 line), `EvHealthDepth.tsx`, `EvScenarios.tsx` (one refusal block each), `EvAssessmentViews.tsx` (window text constants, tab search), `evSelectedWindow.ts` (`ReportSelected`), `evHealthDepth.css`, `w2-ev-assessment.css`.
- `shell/SiteAnalyticsFrames.tsx` (EV hunks: `DomainActionShell` window/refusal, `DomainActionUnknownSection`, W1-only section branch), `shell/SiteHealthFrames.tsx`, `shell/evSiteRoutes.tsx` (`evWorkTabHrefs`), `sites/evWorkPresentation.ts`, `DomainActionVerification.tsx`.
- `backend/assetops_backend/ev_site_reads.py`: one string, `MONEY_COPY["STALE_BASIS"]` (ruling 5). Wire and selection unchanged.
- `tools/w504_ev_work_walkthrough.py`: two changes in the Site Work router: the work service argument `M.build_work_service(url)` and `details=M.build_work_detail_service(url)` (ruling 3, the R373 fix itself).
- `.agent/mock-departure-register.md`: R345-R350 closed in place, R06 note, R470 added.

## Criteria status
| Item | Status | Evidence |
|---|---|---|
| R345 | done | availability tiles `N connector-h`, exact `X h Y min` in the title; 0/1/2 plural tests; `cap-positive` availability-current |
| R244 (EV instances) | done | refusal matrix by code/status on four depth pages; `Read without a selected window` link (window refusals, keeps known_at), Reload (503, 409, unreached); `availability-one-sided-*`, `span-32d`, `refused-reversed` captures |
| R346 | done | bridge row 1 shows metered kWh when the tariff is withheld; stored null stays Unknown; `MOCK DEVIATION D1 (R06)` line; tariff copy `No stored gross tariff estimate matches the current evidence.` verified live on Energy, EV Overview, EV Financials (`caps7/caps.json`, `has: true`, old wording absent) |
| R347 | done | tabs carry the reported or explicit valid window and known_at; Work tabs carry only an explicit valid URL window; `evDepth/evEnergy/evHealthDepth/evScenarios/evWorkActions/evWorkCases` tests |
| R348 | done | ev-action invalid, one-sided and over-31-day windows refuse before any read; no link carries them; `Open this Action without a window`; `ev-action-one-sided-from/to`, `refused-span-32d`, `refused-bad-known-at` (recaptured in the fix round; the earlier capture predated the INVALID_KNOWN_AT copy fix and is not R349 evidence) |
| R349 | done | refusal copy by code, Reload only 503/409/unreached, `Technical detail` disclosure; `cap-forbidden`, `cap-unavailable` |
| R350 | done (EV and cold) | `/plan /execution /history /evidence` land on `Page not available` / `This address is not served`, link `Open this Action's verification`, no read, no redirect; `/overview` stays the R222 alias; EV `cap-links` (4 landings), cold `cap-cold-links` (4 landings plus known_at) |
| R373 (EV case detail) | done | `/maintenance/requests/<WR>?site_id=EV-LAB-001`, `/record`, `/history` render (not 503) in `cap-positive` `case-detail-r373-landing-*`; backend `test_w504_ev_cases/intent_api/test_w207...` scoped runs pass (handoff) |
| Caps | done, see below | `caps*/caps.json` |

## Revert proofs (product file restored from `104e9c33`, test run, `git checkout HEAD --`; `git status` clean after each)
| Product file | Result |
|---|---|
| EvAvailability.tsx (evDepth) | 11 failed |
| EvEnergy.tsx | 3 failed |
| EvHealthDepth.tsx | 2 failed |
| EvScenarios.tsx | 2 failed |
| evSelectedWindow.ts (4 depth files) | 31 failed (missing export) |
| EvAssessmentViews.tsx (+ domainActionVerification) | 6 failed |
| SiteHealthFrames.tsx | 1 failed |
| evSiteRoutes.tsx (evWorkActions, evWorkCases) | 55 failed (missing export) |
| SiteAnalyticsFrames.tsx (R348/R350, 3 files) | 21 failed |
| evWorkPresentation.ts | 31 failed |
| ev_site_reads.py (`test_five_routes_reuse_w206...`, real Postgres) | 1 failed; restored: 1 passed |

## Checks run
- Full vitest at `4bd2fd8f`+CSS: 136 files, 3393 tests: 3389 passed, 4 failed. All four were old expectations of behavior this card changes (R350 `/plan` and `/history` no longer redirect; R244 `data-ev-depth-error` replaced by the refusal block). Updated in `coldWorkActions`, `siteAction`, `siteHealthBoundary` (one new R350 EV `/plan` test); re-run of those three files: 156 passed. `logs/vitest-full.log` is the pre-fix run.
- `npx tsc --noEmit -p .`: clean. `npm run build`: ok (`logs/build.log`).
- `tools/check-all.ps1` via `powershell -ExecutionPolicy Bypass`, main venv: **All 11 guards passed** (`logs/check-all.log`).
- Backend: scoped only (handoff): `test_w504_ev_work_cases.py` 18 passed; `test_w504_ev_intent_api.py` + `test_w207_ev_site_reads_postgres.py` 25 passed (8m12s). Full backend suite not run (held by the coordinator).

## Captures (`.agent/post-W6-W5-EV/`, revision `4bd2fd8f`; ev-health recaptured after the CSS commit)
Producer `tools/w504_ev_work_walkthrough.py --work var/w504a_w5ev --tag w5ev` with `W504_API_PORT_BASE=18460` and a fresh `ASSETOPS_WORK_CURSOR_KEY_HEX`; cold `tools/w502_cold_work_walkthrough.py --tag w5ev --modes positive`; both unmodified (R373 line aside). Harness: batch-16/17 `mk_targets.py` and `capture-b17.mjs` unmodified (b16 targets port rewritten in the run script), one Vite (5197), one Chrome. Clock: real time (2026-10-26 UTC).
| Set | Claims | Notes |
|---|---|---|
| positive (72 targets: depth 4 pages x current/empty/known-at/refused/no-window/work-day/all-open, ev-work, ev-action, one-sided from/to, span-32d, R373 landings) | 848/864 | 16 failing = availability and energy refused-window pairs (reversed, one-sided from, one-sided to, span-32d): app 0 `section.panel` vs mock 3, the baseline refusal shape (batch-16 refused-reversed also 0). Refusal block verified in screenshots |
| zero / worstcase / forbidden | 84/84, 168/168, 60/60 | worstcase = five 160-char Actions, real |
| unavailable | 58/60 | availability 503: "Site unavailable" panel vs mock 3 panels, baseline |
| links (EV Overview, Findings, Sessions, Scenarios, Financials, ev-action tabs, work tabs, global lists) | 188/192 | 4 baseline mock-count misses (ev-sessions, global-incidents) |
| ev-health recapture after CSS | 120/120 | 20 targets |
| cold links (R350) | 86/96 | 10 failing = the four W1-only sections and the known_at variant, deliberate: app shows `This address is not served`, mock shows the verification panels |
Together these cover the 124 indexed pairs (depth 64, ev-work 24, ev-action 36) at 1440 and 390, plus the extras above.

## Caps (guide section 1; measured by `tools/measure-caps.mjs` on the real mounted page, 1440 / 390; all-open exempt)
Stress probe: capture-only DOM edit (labelled), no persistence; true row counts kept; every variable text field set to 160 characters, `fieldsChanged` and `allSet160` asserted. Document overflow 0 in every case.
| Panel | Ruled | Closed peak | Stress | Result / provisional cap `50*ceil(peak*1.15/50)` |
|---|---|---|---|---|
| ev-health Condition and evidence | 400 / 800 | 324 / 453 | 3 true rows, 160-char labels: 394 / 754 | within; first column 40% at <=640 px (was 27%: 1071 at 390, over 800), R470. 5-row clone (not producible, EV-LAB has 2 connectors + meter): 558 / 1175, reported only |
| ev-work Actions at this site | 550 / 800 | 480 / 480 (worstcase, five real 160-char Actions) | real | within |
| availability Connector states | none | 275 / 316 | 2 connectors, 160-char labels: 547 / 794 | 650 / 950 |
| availability Full-schedule bound; Most useful next evidence | none | 182 / 205 | fixed copy | 250 / 250 |
| availability and energy refusal block (strip, 4 tiles, note, link) | none | 195 / 300 | closed | 250 / 350 |
| energy Import power; What can be concluded | none | 442 / 332; 442 / 339 | fixed copy, no variable text | 550 / 400 |
| energy Technical-to-financial bridge | none | 197 / 211 | 3 true rows, all cells 160: 307 / 431 | 400 / 500 |
| ev-scenarios Financial scenarios (and refusal 103 / 120) | none | 305 / 345 | no variable text | 400 / 400 (150 / 150) |
| ev-action Declared verification plan | none | 248 / 406 | 3 true criteria, 160-char cells: 353 / 934 | 450 / 1100 (5-row clone 513 / 1480, reported only) |
No ruled cap is exceeded after the column-width fix. The provisional caps are measurements only; no CSS enforces them.

## Choices made (guide-covered)
C1 connector-h decimals with exact title (4); C2 refusal by code/status, one alert, raw code only in the disclosure, Reload also on 409 (3); C3 link `Read without a selected window` keeping known_at (3); C4 state-specific ev-action h1s (3/4); C5 R06 visible D1 label, no new row (5); C6 no Site tab row on ev-action (2); C7 Work tabs carry only a valid explicit window (2). Health and Scenarios keep their single panel; Health refusal has no tile labels.
Added here: C8 ev-health Asset column 40/30/30 at 640 px (guide 1, R470). C9 caps probe uses the largest real row count when five cannot be produced (guide 1).

## Capture gaps (selected-DTO tests, no fabricated screenshots)
`unknown` mode (replay selects 0 SUPPORTED), pending, stale (no unmodified producer: "needs a modified replay"), missing-meter, historical depth, authored scenario (B16-09), non-Open Action states (B17-12), the tariff copy shown only through its live STALE_BASIS state (it is live in the positive data, so it is captured). Five-row clones of EV health/ev-action panels are not producible.

## Known deviations and residual risk
- (Superseded by the fix round below: R350 now probes the domain Action first; W1 IDs keep their W1 section.)
- R348 `window_invalid` also applies at the bare route (no redirect when the window is refused).
- `evWorkPresentation.ts` imports constants from `EvAssessmentViews.tsx` (heavier module); build and tsc are clean.
- Vite died twice when started with a bare `nohup` from the tool shell, so captures were rerun; the evidence kept is from clean single-instance runs. The harness uses `startvite.ps1` for later runs.
- Backend full suite not run.

## Cleanup
Vite and APIs stopped by PID; `w504a_*_w5ev_test` and `w502b_positive_w5ev_test` dropped; `var/w504a_w5ev` and `var/w502b_w5ev` removed. No `.venv`, node_modules, var or caches committed.

## Fix round (R350 ruling 1 and review Mediums), 2026-10-26
Commit "W5-EV fix round" on top of e6931203. Binding: `.agent/post-W6-W5-EV-r350-rulings.md` 1.
1. **R350 (merge blocker).** `/plan /execution /evidence /history` on cold and EV Sites now render through `DomainActionRoute` with an `unserved` element: the domain Action is probed by Site and Action ID; a loaded Action shows the shelled `Page not available` / `This address is not served` at the original address (no redirect, no W1 read); a non-loaded probe falls back to `w1()` with the original section and W1 selectors. `/verification`, bare and `/overview` unchanged. Tests (`siteAction.test.tsx`): 4 suffixes x domain/W1 x cold/EV (16 cases) asserting URL kept, domain request made, no `/api/sites/.../actions/` read for domain IDs, and W1 content plus `aria-current` section for W1 IDs; `domainActionVerification.test.tsx` EV/cold R350 cases now expect the one probe read.
2. **Medium 1.** `evActionRefusal` checks `INVALID_KNOWN_AT` before the `http === null` branch: "Choose a valid evidence cutoff.", no Reload (`evActionFixRound.test.ts`, http null and 422).
3. **Medium 2.** `evWorkTabSearch` carries a valid UTC `known_at` when `from` and `to` are both null; one-sided stays refused (test).
4. **Lows.** Packet R373 line, register R244 EV note and bad-known-at evidence wording corrected above.
Revert proofs (each product file reset to its pre-fix version, tests rerun, restored): SiteAnalyticsFrames 22 failed; evSiteRoutes 1 failed; evWorkPresentation 1 failed; all pass restored.
Captures (`.agent/post-W6-W5-EV-fix/`, unmodified producers, tag `w5evfix`, work folders removed afterwards; Vite 5197 via `startvite.ps1`, one at a time), 1440 and 390: EV `cap-ev` 144/144 claims (bare, verification, overview, plan, execution, evidence, history for the domain ID; plan, execution, evidence, history for a W1-shaped ID; `refused-bad-known-at`); cold `cap-cold` 116/132: bare, verification and overview pass; the 16 failing pairs are the deliberate ones (domain ID at the four W1-only suffixes shows `This address is not served`; the W1-shaped ID shows each W1 section, against the verification mock's panel set). A first cold run (`logs/cap-cold-run1.log`, 117/132) had load-dependent mis-renders at some bare/verification/overview pairs (`No such site`, mock content in the app shot) and was rerun once on the same Vite; the rerun is the evidence kept. The producers create no W1 Action, so the W1-ID landing is a W1-shaped unknown ID: probe 404, W1 fallback, the W1 section with its own "Action not found" state (screenshot `ev-action-r350-w1shaped-plan-1440-app.png`); a loaded W1 section is proved in jsdom only.
Final checks at the fix-round head: full vitest 137 files, 3411 tests passed (run alone, 199 s); `tsc --noEmit` clean; `npm run build` ok; `check-all.ps1` 11/11 guards. Servers, Chrome, Vite stopped by PID; `w504a_*_w5evfix_test` and `w502b_positive_w5evfix_test` dropped (verified none remain); `var/` work folders removed.
