# POLISH-PC review packet: final gate of the client-demo polish round

Task: `tasks/POLISH-PC-final-gate.md`. Spec: `.agent/build-sheet-POLISH.md` §5 PC, §6, §7, Addenda 1-13 (Addendum 13
item 3: rebuild from merged main before the strict run). Branch `task/POLISH-PC-final-gate` from main `06543e540`.
USER_REVIEW_REQUIRED: true (the owner walkthrough uses `.agent/POLISH-runbook.md`). Not merged.

## Outcome

- Copy pass (review N1, N2, the EV fallback and the EV tabs check), pins updated, no guard touched.
- `assetops_polish_full_test` rebuilt from this branch (`cb1a92cfc` = main + copy pass): finish check 17/17.
- Strict capture 14 keys x 2 widths: 28/28 settled, no overflow, 0 counted hits. v70 panel structure unchanged from DEMO-B.
- Slow demo test 19/19, full vitest 3594/3594, backend `-Tier all` 4737/0, check-all 12/12 (section 4).
- Register: R625-R662 checked unique and statused; R08 (P-B3-3) closed; PC copy added to R655.
- Runbook: `.agent/POLISH-runbook.md`.

## Files materially changed

- `frontend/src/sites/coldAssessmentWords.ts`, `EvSiteViews.tsx`, `EvEnergy.tsx`; pins in `sites/__tests__/`
  `coldRoutes`, `coldScenarios`, `coldSiteViews`, `evAssessmentRoutes`, `evEnergy`, `evSiteMoneyRoutes`.
- `.agent/mock-departure-register.md` (R08, R655), `.agent/POLISH-runbook.md`, `.agent/POLISH-PC-captures/`, this packet,
  the task file.

## 1. Copy pass (old → new)

| Where | Old | New |
|---|---|---|
| `coldAssessmentWords.ts:108` `REGISTERED_SIMULATION` (cold Record details, EV Capability/Claim/Record/Basis "source …") | Generated test data | Example data |
| `EvSiteViews.tsx:321` EV provenance badge | Generated test data | Example data |
| `EvSiteViews.tsx:1474` EV Assumptions window line | Generated test data | Example data |
| `EvEnergy.tsx:166` Energy card note (N2) | Scenario tariff: 0.30 USD/kWh / Scenario tariff not established | Charging tariff: 0.30 USD/kWh / Charging tariff not set |
| `EvSiteViews.tsx:1235` `NO_SCENARIO` (Analysis money fallback, Financials card, bridge chip, Financials gap) | No gross tariff estimate yet | No charging income estimate yet (matches `ev_site_reads.NO_MONEY`) |
| `EvSiteViews.tsx:1293` Financials strip | … · gross scenario only · … | … · charging income estimate only · … |
| `EvSiteViews.tsx:1301` Financials "Gross tariff estimate" card note | Gross scenario · not cash collected | Estimate · not cash collected |
| `EvSiteViews.tsx:1344` bridge badge | Scenario | What-if |
| `EvSiteViews.tsx:1510` Assumptions currency row | Scenario display currency | Currency for charging estimates |

- The brief's EvSiteViews line numbers (726/731/1203/1349) and the text "No gross tariff scenario assessed" were not in
  the merged file; the single local copy is the `NO_SCENARIO` constant, used at every one of those places. The old server
  text survived only as a test fixture (`evSiteMoneyRoutes.test.tsx:145,448`), now the server's current text.
- Kept as accepted mock wording (plain, not jargon), recorded in R655: "How a claim limit is set" and "Claim details"
  (cold and EV Analysis); the mock tile labels "Gross tariff estimate" and "What-if details".
- Test change beyond string swaps: `evSiteMoneyRoutes` `selected_claim_rules_and_money_lines_ignore_pending_class`
  scoped two `main()` assertions to the window line `[data-ev-window]`, because the Site badge "Example data" (R651)
  is now the same words; the negative uses `!` so a missing element fails rather than passes.
- Not changed: `work/globalWorkParts.tsx:53` work provenance "Generated test data" (the Work source summary pairs it
  with "Prepared example data" for authored records; merging the two words needs a wording call). Out of named scope.

## 2. Rebuild

`tools/demo_combined.py --db assetops_polish_full_test --work var/polish_full prepare` from this worktree at `cb1a92cfc`,
16:39:05-16:55:52, **1007 s** (cap 3120 s): Kobo 716.2 s (8 runs, VERIFIED ACT-000001, cost check MODELLED_NO_IMPROVEMENT),
cold 56.1 s (3 runs, 4 findings), EV 61.3 s (2 runs); objectives 6; both cutovers permitted;
**self-check 17 pass, 0 fail, 0 skipped**. S = 2026-10-30.
- Before it: prepare refuses a DB whose marker is in another worktree (`demo_combined.py:295`). The PA-3 build was owned by
  `AssetOpsV1-polA3/var/polish_full`, so it was removed with the tool's own `drop` from that worktree (DB + work folder),
  then rebuilt here. `assetops_demo3_full_test` was not touched.

## 3. Captures (`.agent/POLISH-PC-captures/`)

- Serve (API 8990) and Vite (5490) from this worktree on the polish DB, CDP 9493, `DEMOB_STRICT=1`, 16:57:23-17:03:24
  (361 s): **28/28 OK, settled, overflow false at both widths; 0 counted hits (strict), exit 0**.
- Exempt hits: every capture 1 per width, the "Times in UTC" note (`data-time-zone-note=utc`; preventive
  `=due-dates`). `kobo-board-S-open` 283 per width, same as PA-3's final run (no jump): Technical details 266 (uuid 255,
  snake_case 4, enum 2, raw timestamp 2, "UUID" 1, "claim" 1, "run" 1), source-reference "PCS" 3 / "PV" 2,
  user-owned "load" 1, lab region 11 (simulator 3, run 3, runs 1, scenario 1, scenarios 1, simulation 1), UTC note 1.
- Review mode (`DEMOB_REVIEW_LABELS=1 DEMOB_ONLY=wr-overview,kobo-board-S`, 64 s, `review-mode/`): labels visible;
  `kobo-board-S` 390 shows "MOCK DEVIATION D2 (R453)" (1440 none); `wr-overview` R396, R363, R365 at both widths.
- `-open`: the tool has one open key (`kobo-board-S-open`). Cold and EV open captures are not supported without
  adding keys to the tool, so their disclosure prose is covered by vitest and the guard scan only (PB-3 residual stands).
- v70 compare (mock 55 s, `compare-run.log`): panel counts equal DEMO-B's everywhere: portfolio 4/4, mini 5/8,
  verification 3/3, cold 5/5, ev 5/5, findings x4 1/1, preventive 1/1, wr-overview 2/2. The missing/extra title
  counts moved only by the R655 renames (mini "what happened on this day"/"possible cost"; cold and ev "possible cost").
  Cards 4/4 where measured. Page height ratios 0.54-1.23 (open captures 8-11).
- Stack stopped by PID (serve 18324 tree, npm 20100 tree); ports 8990, 5490, 9493 free.

## 4. Suites

- Slow demo build: `tools\run-host-tests.ps1 -- backend/tests/test_demo_combined_postgres.py -m slow` at `c5277805b`,
  17:07:18-17:24:40 (1042 s): **19 passed**; JUnit tests 19, failures 0, errors 0, skipped 0.
- Full `npx vitest run` at `c5277805b`, 17:24:50-17:29:17 (267 s): **150 files, 3594/3594 passed** (the evEnergy load
  flake did not fire).
- Backend `tools\run-backend-suite-in-container.ps1 -Tier all`, run **`20261101-172931-803fd5`** at `c5277805b`
  (everything except the Addendum 14 copy round): JUnit **4737 tests, 0 failures, 0 errors, 0 skipped**, 3380.9 s;
  console "4737 passed in 3382.36s (0:56:22)". Claude Code's memory guard killed the PowerShell wrapper; the runner
  container ran to completion and wrote `junit.xml`, `wall-time.txt` and `exit-code` itself. Not rerun.
- Addendum 14 round, scoped: pure pytest 135 passed; `test_out_e4_readback_postgres.py` 1 passed (76 s, host tests);
  vitest 12 files 282 passed.
- `tools\check-all.ps1 -Python …plan2\.venv\Scripts\python.exe` at `fffbded4b`: **All 12 guards passed** (407 s).

## 5. Register reconcile (`.agent/mock-departure-register.md`)

- R625-R662: 29 rows, no duplicate ids anywhere in the register; unused ids are the reserved slice ranges
  (R637-R639, R642-R644, R647-R649, R653-R654, R657-R659).
- Closed as §5 PC asks: R626 closed (PA-1/PB-2; capture: Kobo S "No fuel cost estimated: the generator was on but
  delivered no measured power"); R630 closed (PB-3; capture: WR-006 "This is the third visit to Backup generator in 60
  days…"); R111 closed for the demo build by R646 (captures: h1 "GreenHarvest Cold Room", "Depot Charging Hub");
  P-B3-3 = R08 "Due status not assessed" **closed here** by R641/R661 (capture: "2 overdue", Overdue 2, Due in the next 14
  days 2, "1 plan based on hours of use; not checked here yet").
- §7 rows present: R635, R636, R640, R641, R645, R646, R650, R651, R652, R655, R656, R660 (+ R661, R662).
- Cross-checked on captures: R640 (ACT-001, WR-006, INC-005, PM-013), R645 (Depot board: PM-013 under Already in hand,
  no backdated Action), R651 (banner on every page, Site badge "Example data"), R650 (one "Times in UTC" per page),
  R655 (Possible cost, Publish a charging tariff, Needed before charging income can be estimated), R635 (Optimize:
  "…needs odometer readings and a published charging tariff").
- R661 carries both its PB-3 Preventive content and Addendum 13 L4 (UTC on Finding pages); the PB-3 re-review accepted
  the fold. Left as is.

## Known deviations

- Runbook is a new `.agent/POLISH-runbook.md` (§5 PC) rather than an edit of the DEMO-B packet.
- The polish build sits in this worktree's `var/polish_full` (untracked); the PA-3 copy in `AssetOpsV1-polA3` is gone.

## Residual risk and user-review focus

- "test data" on capture screens: ruled by Addendum 14 and fixed (section below).
- The whole-diff review of the round by a fresh Claude reviewer (§5 PC) is the coordinator's next step.
- Cold and EV disclosures have no `-open` capture (tool limit); their prose is covered by vitest and the guard scan.
- Owner confirms at the walkthrough: §6 D-1 banner "Demonstration · example sites and records…" and badge "Example
  data" (R651); D-2 an INEFFECTIVE trial never shows a modelled money line; D-3 no backdating of the Depot Action (R645,
  runbook P-08 line); D-4 one "Times in UTC" note per page (R650), and Addendum 13 L4 UTC clock times on Finding pages
  with site-local calendar dates (R661; site-local clock everywhere is a later choice); D-5 mock Lab Site names in the
  demo build (R646); Q1 Kobo fuel cost reads zero with "No fuel cost estimated…" (R626), idle-fuel rate later (~1.5 d +
  rebuild); the plain-language copy rows R655 and R662 (including this PC copy pass); R641 hours-of-use plans stay
  "Not assessed"; R08 closure.

## Addendum 14 round (commits `c6854cfab`, recapture `fffbded4b`)

- Server: `board.py:49` "Verified on example data"; `mini.py:77,81` "{code} verified on example data"; `placement.py:42`
  "Change verified on example data; watch for it coming back". Frontend: `globalWorkParts.tsx:53` "Generated example
  data"; sibling trial note `SiteActionVerification.tsx:556` "Policy trial on Lab or authored example data: …"
  (coordinator accepted). No other "test data" in those maps. Pins updated in 6 backend tests and 3 vitest files; R655.
- Vocabulary: `["test data wording", /\btest data\b/gi]` in `WORD_KINDS`, `tools/demo-combined-vocabulary.mjs` (the
  capture VOCAB lives there since Addendum 5; `demo-combined-evidence.mjs` imports it). Non-vacuous: it matches
  "test data" and "TEST DATA", not "testdata"; guard self-tests 12/12.
- Rebuild at `e413fc8c8`, 18:29:15-18:50:09, **1254 s** (cap 3120 s): Kobo 854.1 s, cold 49.0 s, EV 85.5 s; **self-check 17
  pass, 0 fail, 0 skipped**. S unchanged (2026-10-30); new Action and Finding ids (runbook updated).
- Strict capture, first run 18:52:26-18:59:16: 26 OK, **portfolio-week unsettled at both widths** (still "Loading the
  Portfolio" two minutes after serve start, cold first read; `capture-run-first-unsettled.log`), 0 counted hits,
  exit 1. Rerun on the warm serve, 18:59:33-19:04:41 (308 s): **28/28 OK, settled, no overflow, 0 counted hits with
  "test data" now counted, exit 0**. Exempt: 1 per capture (UTC note), `kobo-board-S-open` 283 per width (no jump).
- Review mode (67 s): same labels as before (R453 at 390 on `kobo-board-S`; R396, R363, R365 on `wr-overview`).
- Stack stopped by PID; ports 8990, 5490, 9493 free.
- Still out of scope: "Authored test data (test-scoped example)" (`verificationWords.ts:215`) and the EV refusal
  "Authored test data versions conflict." (`EvAssessmentViews.tsx:451`); neither is on a capture screen.

## Whole-diff fix round (review `review-POLISH-whole-diff.md`; commits `a08bf548b`, `e547140a7`, `9d96ffc04`, `945002e04`)

Every change follows rulings already made (§3.1 pattern "no Finding/Action capitals in running text", Addenda 5, 13, 14).

| Item | Where | Old → new |
|---|---|---|
| M1 | `ui/ProductStatus.tsx` `ExactReferences` | a "How this was worked out" `<details>` with no tag → renders through `WorkedOut`: with no `extra`, one closed "Technical details" (`data-technical-details`; hooks `data-exact-references`/`data-disclosure` kept); with `extra`, "How this was worked out" keeps the plain detail and nests the ids in Technical details |
| M1 | `sites/FindingConsequence.tsx` `MethodDetail` | counted-readings table (Record reference column) in the plain `extra` → inside `TechnicalDetails name="financials-consequence-readings"`; method paragraphs stay plain |
| M3 | `sites/verificationWords.ts` `sourceWords` | "Registered Lab trial data" → "Example data"; "Authored test data (test-scoped example)" → "Prepared example data" |
| M3 | `SiteActionVerification.tsx:1290` | "Policy trial on demonstration data: …" → "Policy trial on example data: …" |
| M3 | `ui/productWords.ts` `DEMONSTRATION_OUTCOME_NOTE` | "This is a policy trial on demonstration data: …" → "… on example data: …" (same Verification page) |
| M3 | `tools/demo-combined-vocabulary.mjs` lab name | `(?:replay|charging) lab` → also `lab trial data` |
| L1 | `OverviewFindingList.tsx:405` (Kobo board), `ColdAssessmentViews.tsx:466` | "Open the Finding →" → "Open the finding →" |
| L1 | `estate/portfolioWords.ts:29` | "Selected Findings across accessible Sites, …" → "Selected findings across accessible Sites, …" |
| L1 | `findingWords.ts` (16 strings), `SiteFinding.tsx` (36), `actionPresentation.tsx:128-129` | "Finding(s)" after a lower-case word in prose → "finding(s)" (e.g. "Joined into an earlier finding", "Related findings", "not a no-finding result", "Open the finding to see what it found."); sentence-initial "Finding …" headings stay |
| L1 | `estate/placement.py:26,40,64` | "…no longer confirms this Finding…", "No price basis for this Finding", "…other Findings may be missing" → "finding"/"findings" |
| L2 | `site_outcomes/ev.py:45` NO_TARIFF | "Gross tariff estimate not available yet" → "Charging income estimate not available yet" |
| L2 | `ev_site_reads.py:31,37,42` | "No stored gross tariff estimate matches …" → "No stored charging income estimate matches …"; "…; no current gross tariff estimate." → "…; no current charging income estimate."; "Gross tariff scenario; not cash collected." → "Charging income estimate; not cash collected." |
| L3 | `estateEvidenceWords.ts:16`, `estateFinancialsWords.ts:19` | "Potential product exposure" → "Stock may be at risk" |
| L3 | `EstatePortfolio.tsx:370,417,462,473`, `portfolioWords.ts:129` | "… not established" / "Completed activity · Not established" → "… not known yet" / "Completed activity · Not known yet"; "Cross-Site energy and tariff totals are not established." → "… are not known yet." |
| L4 | `demo-combined-vocabulary.mjs` | new id kind "stored record code": `(?:ACT|INC|WR|F|PLAN|CHG|PM|REC)-(?!000)\d{6,}` (three-zero codes stay on the existing rule, so a code counts once) |
| L5 | `estatePortfolio.test.tsx`, `portfolioFixtures.ts` | "Supported/Unconfirmed Finding", "Generated test data source", "No accepted Action; open the recommendation" → the server copy ("Supported finding", "example data", "No action agreed yet · review the recommendation") |
| L5 | `tools/s405-provenance-evidence.mjs:36`, `s602b-verification-evidence.mjs:194,311` | "Generated test data" → "Example data"; `/Registered Lab trial data/` → `/Example data/`; "…confirms this Finding…" → "finding" |
| Item 8 | `tools/demo_combined.py` `serve`, `prewarm`, `story_week_query` | after the first tick, one `GET /api/estate/outcome-summary?<story week>` (timeout 900 s); prints `ready: Portfolio outcome summary for the story week answered HTTP <s> in <n> s. Do not restart serve once the client has joined.` only when it returns; a transport failure prints `pre-warm did not finish …` and no `ready:` line. Runbook step 2: wait for `ready:`; never restart serve once the client has joined |
| M2 support | `tools/demo-combined-evidence.mjs` | each capture also writes `<key>-<width>.txt` (visible `<main>` text) beside its PNG |

Pins updated: `productStatus.test.tsx` (+1 test for the `extra` nesting), `s404SiteFindingIndex.test.tsx`,
`siteActionVerification.test.tsx`, `siteFinding.test.tsx`, `siteFindingEvidence.test.tsx`, `performanceDispatch.test.tsx`,
`evEnergy.test.tsx`, `estate{Portfolio,Evidence,Financials}.test.tsx`; backend `test_cc_placement`, `test_cov_partial_portfolio`,
`test_out_b3_cold_ev`, `test_w207_ev_site_reads_postgres`; `test_demo_combined_links` +2 pre-warm tests.

M1 callers spot-checked: `SiteFinding.tsx:513`, `SiteFindingHistory.tsx:477`, `SiteAction.tsx:648,896,1093` and
`SiteRecommendation.tsx:890` pass `references` only (now Technical details); `FindingConsequence.tsx:931` is the one
`extra` user (fixed above). The `extra` props in `ColdAssessmentViews`/`EvAssessmentViews` are on `TechnicalReferences`,
already a Technical details region.

Guard proofs (non-vacuous): with `lab trial data` removed from the lab-name regex the M3 self-test fails (13/14); with
the stored-code regex replaced by `/(?!)/g` the L4 self-test fails (13/14); restored by `git checkout`, 14/14.

Register (`mock-departure-register.md`), checked against the new capture texts: R08 status leads with "closed by
POLISH"; R625 headlines "Can't be compared across these sites yet" / "Not known yet"; R628 "Charging income estimate
not available yet", "Publish a charging tariff"; R631 stays standing (the Portfolio tells the two rows apart by date;
the Findings list rows still read alike, with the id in closed Technical details); R632 "60 min → 0 min", "0 kWh" with
"Critical demand not served · pass"; R634 "ACT-001 Verified on example data" with no modelled improvement; R655 and
R662 append this round's words; R656 narrowed to the shared exact-reference components and the 28 captured screens.
Other R625-R662 product strings were found in the captures as written (R626, R627, R630, R635, R646, R650, R652, R655
Kobo/Verification words, R660, R661, R662). Not on a capture: R651's banner (outside `<main>`), R655's EV Energy and
Financials tab words.

Results (one heavy job at a time):

| Check | Result | Wall |
|---|---|---|
| Scoped pytest (links, placement, cold/EV outcomes, partial portfolio, PA-2a/PA-3 copy, finish CO-1) | 99 passed | 2 s |
| `test_w207_ev_site_reads_postgres.py` (run-host-tests) | 19 passed | 347 s |
| Scoped vitest (26 files; then the 2 Finding files after pin updates) | 717/731, 14 pin failures fixed; then 127/127 | 45 s + 8 s |
| `npx tsc --noEmit` | exit 0 | 28 s |
| Guard node tests (mock-deviation, evidence, missing-claim) | 52/52; labels OK, 153 files | under 5 s |
| Rebuild at `e547140a7` | exit 0, self-check **17 pass, 0 fail, 0 skipped** | 828 s |
| Serve pre-warm | `ready:` HTTP 200 in 11 s, 58 s after serve start | |
| Strict 28-capture | **28/28 OK on the first run**, `portfolio-week` settled at both widths, 0 counted, no overflow; exempt 1 per capture, 283 per width on `kobo-board-S-open` (unchanged) | 312 s |
| Review-mode set | R453 (390, `kobo-board-S`); R363, R365, R396 (`wr-overview`), as before | 66 s |
| Full `npx vitest run` | 3593/3595: 2 pin failures in `performanceDispatch.test.tsx` ("no finding"); pins fixed (`945002e04`), file rerun 44/44. The `evEnergy` flake did not occur | 253 s + 7 s |
| check-all | **All 12 guards passed** | 396 s |

Stack stopped by PID (serve 28388 tree, npm 18316 tree); ports 8990, 5490 and 9493 free.

Residual: capitalised "Finding" remains in link and button labels outside this list ("Review Finding" on Portfolio
rows, "Open Finding →" on the EV board, the `SiteOverview`/`SitePerformance`/`SiteRecommendation` "Open the Finding"
links, `OverviewFindingList.tsx:94,165,201`); "Demonstration data" as a foundation Mode value on the `-open` stress
capture (inside Technical details); the "Gross tariff estimate" tile label stays mock wording (R628/R655).
