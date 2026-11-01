# POLISH-PC review packet: final gate of the client-demo polish round

Task: `tasks/POLISH-PC-final-gate.md`. Spec: `.agent/build-sheet-POLISH.md` §5 PC, §6, §7, Addenda 1-13 (Addendum 13
item 3: rebuild from merged main before the strict run). Branch `task/POLISH-PC-final-gate` from main `06543e540`.
USER_REVIEW_REQUIRED: true (the owner walkthrough uses `.agent/POLISH-runbook.md`). Not merged.

## Outcome

- Copy pass (review N1, N2, the EV fallback and the EV tabs check), pins updated, no guard touched.
- `assetops_polish_full_test` rebuilt from this branch (`cb1a92cfc` = main + copy pass): finish check 17/17.
- Strict capture 14 keys x 2 widths: 28/28 settled, no overflow, 0 counted hits. v70 panel structure unchanged from DEMO-B.
- Slow demo test 19/19, full vitest 3594/3594, backend `-Tier all` and check-all: see Checks.
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

- Slow demo build: `toolsun-host-tests.ps1 -- backend/tests/test_demo_combined_postgres.py -m slow` at `c5277805b`,
  17:07:18-17:24:40 (1042 s): **19 passed**; JUnit tests 19, failures 0, errors 0, skipped 0.
- Full `npx vitest run` at `c5277805b`, 17:24:50-17:29:17 (267 s): **150 files, 3594/3594 passed** (the evEnergy load
  flake did not fire).
- Backend `toolsun-backend-suite-in-container.ps1 -Tier all`, run `20261101-172931-803fd5` at `c5277805b`, started
  17:29:30: **incomplete at handback**. Claude Code reaped the PowerShell wrapper for low system memory; the runner
  container kept going (console at about 82%). Results land in `var/test-results/OPS-03/20261101-172931-803fd5/`
  (junit.xml if pytest finishes). The wrapper's wall-time and post-processing did not run. Not restarted.
- `tools\check-all.ps1` (12): **not run** (it was to follow `-Tier all`). Run on the copy pass alone: the vocabulary
  guard `mock-deviation-labels.mjs` OK (153 files) and its 12 self-tests passed.

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

- **Finding for a ruling (not fixed): server text "test data" is still on capture screens.** The Kobo board's
  Earlier interventions chip reads "Verified on test data" (`site_outcomes/board.py:49` ACTION_RESULT), and the mini
  Assure line "{code} verified on test data" (`site_outcomes/mini.py:77,81`); Portfolio has a sibling
  "Change verified on test data; watch for a return" (`estate/placement.py:42`). §3.1 rules "Verified on example data"
  for the Verification page only, and the vocabulary scan does not flag "test data". Fixing it is lane A server text
  and needs a rebuild + recapture.
- `-Tier all` and check-all are owed (above). The whole-diff review of the round by a fresh Claude reviewer (§5 PC) is
  the coordinator's next step.
- Owner confirms at the walkthrough: §6 D-1 banner "Demonstration · example sites and records…" and badge "Example
  data" (R651); D-2 an INEFFECTIVE trial never shows a modelled money line; D-3 no backdating of the Depot Action (R645,
  runbook P-08 line); D-4 one "Times in UTC" note per page (R650), and Addendum 13 L4 UTC clock times on Finding pages
  with site-local calendar dates (R661; site-local clock everywhere is a later choice); D-5 mock Lab Site names in the
  demo build (R646); Q1 Kobo fuel cost reads zero with "No fuel cost estimated…" (R626), idle-fuel rate later (~1.5 d +
  rebuild); the plain-language copy rows R655 and R662 (including this PC copy pass); R641 hours-of-use plans stay
  "Not assessed"; R08 closure.

## Addendum 14 round (commit `c6854cfab`; rebuild, recapture and check-all still owed)

- Server: `board.py:49` "Verified on example data"; `mini.py:77,81` "{code} verified on example data"; `placement.py:42`
  "Change verified on example data; watch for it coming back". Frontend: `globalWorkParts.tsx:53` "Generated example
  data"; sibling trial note `SiteActionVerification.tsx:556` "Policy trial on Lab or authored example data: …" (on the
  `kobo-verification` capture, so the new rule would count it). No other "test data" in those maps.
- Vocabulary: `["test data wording", /\btest data\b/gi]` added to `WORD_KINDS` in `tools/demo-combined-vocabulary.mjs`
  (the capture VOCAB moved there under Addendum 5; `demo-combined-evidence.mjs` imports it). It matches "test data" and
  "TEST DATA" and not "testdata"; the guard self-tests pass 12/12.
- Pins updated in 6 backend tests and 3 vitest files; R655 lists the strings.
- Scoped runs: pure pytest (cc_placement, out_b1_board, out_b2_mini, out_e4_readback, polish_pa2a_server_copy) 135
  passed; vitest work + outcomeBoard + siteActionVerification + estatePortfolio 12 files, 282 passed.
  `test_out_e4_readback_postgres.py` is waiting for a DB slot once the `-Tier all` container exits.
- Still out of scope: the AUTHORED "Authored test data (test-scoped example)" (`verificationWords.ts:215`) and the EV
  refusal "Authored test data versions conflict." (`EvAssessmentViews.tsx:451`) are not on the capture screens.
