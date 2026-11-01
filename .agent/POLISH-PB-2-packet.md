# POLISH-PB-2 review packet: Kobo board, verification page and display codes

Task `tasks/POLISH-PB-2-kobo-board.md`. Branch `task/POLISH-PB-2-kobo-board` from main `1c0ef34c3`, worktree
`AssetOpsV1-polB2`. Spec: `.agent/build-sheet-POLISH.md` §1.1, §3, §3.1 (Kobo and Verification rows), §5 PB-2, §7,
Addenda 3-5, 7, and Addendum 8 (PB-2 pre-flight rulings Q1-Q6, which answered this slice's questions).
USER_REVIEW_REQUIRED: false.

## Outcome delivered

- **Ids (R656).**
  - Every id on the Kobo board sits in a closed "Technical details" disclosure that carries `data-technical-details`,
    as do the ids on the verification page, the Action History cells and every `SourceProvenanceRecord`.
  - On `kobo-board-S-open`, 256 id hits per width became 0: 251 UUID, 2 enum and 3 raw timestamps. 255 UUIDs, 2 enums
    and 2 raw timestamps are now `exempt_hits` inside Technical details; the third raw timestamp is now formatted.
- **Kobo copy (R655).** Every §3.1 Kobo row not done in PB-1, with the Addendum 4 run/ran/running swaps.
- **P-06 money panel (§1.1).** A priced zero reads "No fuel cost estimated" plus the idle-fuel sub-line. The
  "Latest estimate" chip and the "How this estimate was made" disclosure stay. This closes R626.
- **Verification rows.** All §3.1 Verification rows. The claim label moved inline into the status strip, which fixes
  the 3 known `w1f4VerificationStructure` failures.
- **Display codes.** `displayCode()` is applied at the ~25 visible record-code render sites (Addendum 8 Q6).
- **PA-2a hand-offs.**
  - `mini.FINDING_TITLE` and `findingWords.LIFECYCLE_WORDS` now use the Addendum 4 titles (MERGED and the fallback
    unchanged).
  - `GAPS_NO_READINGS` changed (Q1).
  - Frontend fixtures match the new wire strings.
  - The essential-service role words are in place (Q2).

## Files materially changed

- **New.** `ui/TechnicalDetails.tsx` (`TechnicalDetails`, `TechnicalReferenceList`, `WorkedOut`), `ui/displayCode.ts`,
  and tests `ui/__tests__/{displayCode,technicalDetails}.test.ts(x)` and `sites/__tests__/pb2KoboWords.test.ts`.
- **PB-2 files.**
  - `sites/SiteWindowOverview.tsx` (freshness, day reading, reads sentence, context counts, money zero, choice
    lines, panel descriptions, next step).
  - `sites/OverviewFindingList.tsx` (row line, count line, `WorkedOut`, `episodeRange`, `choiceLines`).
  - `sites/overviewSlots.tsx`, `sites/dispatchWords.ts`, `sites/sourceProvenance.tsx`.
  - `sites/SiteActionVerification.tsx`, `sites/actionPresentation.tsx`, `sites/ClaimLabel.tsx` (`inline`).
  - `sites/SiteAction.tsx` (History Technical details, title code), `sites/findingWords.ts`.
- **Shared, additive.** `ui/Disclosure.tsx` (`technical` prop), `ui/index.ts`, and `test/v69PanelTitles.ts`
  (`mini:1` "What happened on this day", `mini:4` "Possible cost", per Addendum 8 Q3 and R655).
- **Time-only.** `sites/SiteDetails.tsx` and `sites/SiteConfiguration.tsx`: "Valid from" uses `formatDayTime`. This
  was a raw timestamp on `-open`.
- **Backend, string constants only (Addendum 8 Q1).** `site_outcomes/mini.py` `FINDING_TITLE` and `GAPS_NO_READINGS`.
  - Tests: `test_idx_gaps_board.py`, `test_idx_gaps_postgres.py`, `test_out_b2_mini.py`, `test_out_b2_vocabulary.py`.
  - `tools/demo_combined_finish.py` `GAPS_TEXT` matches the new gap text.
- **PB-3-owned files touched, `displayCode()` calls only (Addendum 8 Q6).** PB-3 rebases on main first.
  - `sites/SiteRecommendation.tsx`, `sites/recommendationVerification.tsx`, `sites/DomainActionVerification.tsx`.
  - `sites/SiteWorkActions.tsx`, `sites/siteWorkCases.tsx`, `shell/SiteAnalyticsFrames.tsx`.
  - `work/{workRequestShared,GlobalIncidents,GlobalMaintenance,GlobalPreventive,OperationalRecords,WorkRequestRecord}.tsx`.
  - `estate/{actionIndex,EstatePortfolio}.tsx`.
  - aria-labels, `data-*` attributes and the "Action code" reference row keep the stored code.
- **Records.** `.agent/mock-departure-register.md` (R655, R656 added; R626 closed) and `.ai/CODE_STATE.md`
  ("POLISH PB-2").

## §3.1 rows (old → new as built)

| Row | Built |
|---|---|
| Reads on this Overview: Service, Dispatch, Fuel, Renewable… | "This page uses service, generator, fuel and solar readings for the selected day." (the list follows the readable reads) |
| 0.00 USD exposure in this hour | BE (PA-1), awaiting the rebuild |
| Not available yet · 24 of 31 days have no assessed readings | BE `GAPS_NO_READINGS` "24 of the last 31 days have no checked readings yet" (Q1), awaiting the rebuild |
| What happened in the selected hour | "What happened on this day" |
| Selected day 2026-10-29 · plain sequence… | "29 Oct 2026 · the periods we checked; Dispatch has the detail" |
| Hour not selected: … | deleted from the Kobo board (the legacy `SiteOverview` keeps its own) |
| Day reading: Assessed. 1 operating period assessed; 13 measured roles covered | "Checked: 1 period of generator use, from 13 measured inputs"; zero gives "Checked: generator not used on this day, from 13 measured inputs" (Addendum 4) |
| The source of these readings is open for current use. | inside "How this was worked out": "The reading source is active." (a closed source stays visible) |
| Operating context · Selected day · when readings arrived… | "When the generator was on and when readings arrived" (Addendum 4) |
| critical load delivered/requested power | "Essential services: power supplied" / "Essential services: power requested" (Q2); the fallback capitalises |
| 1036 accepted readings…; the first 500 are listed. | "1,036 readings on this day (first 500 shown)" |
| No rule yet says which gaps… | "Gaps in the readings are not judged yet; reading counts are shown instead." |
| Needs attention · The Finding chosen… | "The main finding for this day" |
| 2026-10-29 04:35 UTC to … · Open · version 2 · the Finding chosen for this day | "29 Oct, 04:35–07:55 · Open · main finding for this day" |
| 1 Finding overlap this day. Showing all 1. Open the full Findings list… | "1 finding on this day · Open all findings for this day" (partial pages keep "Showing the first n of N.") |
| Generator support merits review (board/list title) | "Generator may have been on longer than needed" (`LIFECYCLE_WORDS` + `mini.FINDING_TITLE`) |
| Bounded money consequence | "Possible cost" (Kobo/mini slot only, Q3) |
| 0.00 to 0.00 USD | "No fuel cost estimated" + "The generator was on longer than needed but delivered no measured power. Fuel used while idling is not estimated yet." |
| Current amount / This range uses… | "Latest estimate" / "Based on the latest finding and the recorded diesel price." |
| Generated test data. These records were generated for a test… | "Example data: these readings were prepared for this demonstration, not measured on physical equipment." |
| A modelled range of possible extra fuel cost for one Finding… | "An estimate of possible extra fuel cost, not money lost or saved." |
| Cost range, money gate, source record and links | "How this estimate was made" |
| The Finding records what the assessment concluded… | "Start from the finding to decide what to do next." |
| Modelled change after the trial · not realized savings (FE claim) | "Estimated effect of the trial (not money saved)"; the board sentence is BE (PA-2a) |
| Kobo (open) access/choice/list-built/listed refs | "Access: operator account", "Showing the latest version of each finding", "List built 1 Nov 2026, 06:49"; values in Technical details |
| Verification: Dig deeper… / Source Finding version / new-episode sentence / claim | "Technical details" / "Finding it came from" / "A later finding about the same issue does not change this trial's result." / "Verified on example data · benefits the mini-grid operator" |

Builder copy outside §3.1, for review:
- "measured inputs not recorded for this day" is the coverage-missing case of the day line. "not available yet"
  tripped the missing-claim scan.
- "from 29 Oct, 04:35, no end time yet" is used for an open episode.
- "Checked (possibly avoidable): …" is used when the day's claim level has an outcome word.
- "Access: not recorded" and "Access: recorded in the technical details" are the non-operator bases.
- "Change record" is now the visible History link text. The change id sits in Technical details.

## Acceptance criteria

- **Kobo §3.1 rows (§5 PB-2): met.** See the table. The BE rows await the PA-3 rebuild (Addendum 3).
- **P-06 money panel (§1.1): met.** Pinned by `s5SiteWindowOverview` "POLISH §1.1 (P-06)".
- **Technical details tagging and renames on Kobo and verification: met.** `technicalDetails.test.tsx` includes a
  non-vacuity check: once the region is removed, no UUID is left.
- **Verification rows: met.**
- **displayCode at the capture-screen sites and the rest of the ~25: met.** `kobo-verification` h1 reads
  "ACT-001 · Battery reserve trial". The `maintenance-preventive` and `wr-overview` frontend codes read `PM-010`/`WR-006`.
- **OUT-A L1 "Candidate" in the Optimize card detail: not visible.** It has 0 hits on the Kobo captures, so there was
  no change.
- **3 known `w1f4VerificationStructure` failures: fixed** (they touched `ClaimLabel`/verification).
- **Checklist (owner table, 258 per width):**
  - 256 per width are PB-2 frontend hits on `-open`; they are now **0**.
  - The 2 Portfolio "scenario" hits moved to PB-3 (Addendum 8 Q4), so they were not done.

## Checks run (final code `abbe8cf03`)

- `npx tsc --noEmit`: clean. `npm run build`: built in 14.3 s.
- Full `npx vitest run`: **150 files, 3580 tests passed, 0 failed**, wall 321 s.
  - An earlier full run, before the cold/EV/work test expectations were aligned, had 24 failures in 9 test files.
    All were padded-code expectations, fixed in `abbe8cf03`.
  - There were no `w1f4` failures and no `evEnergy`/`evScenarios` flakes.
- Backend (plan2 venv, PYTHONPATH = this worktree): `test_idx_gaps_board`, `test_out_b2_mini`, `test_out_b2_vocabulary`,
  `test_out_b1_board`, `test_link_lineage`: 97 passed. `test_idx_gaps_postgres.py` on `assetops_test` (README-db URL): 7 passed, 68.8 s.
- `tools\check-all.ps1 -Python <plan2 venv>` on `abbe8cf03`: **All 12 guards passed.**
  - The first run failed 2 of 12: the missing-claim orphan scan and its fixtures, both on the words "not available
    yet" in the day line. These were fixed in `3d2251e16`.
  - After the fix: `node tools/checks/missing-claim-scan.mjs` passed, and `test_missing_claim_scan.mjs` gave 26 pass, 0 fail.

## Live captures (Addendum 3)

- **Setup.**
  - Serve ran from `AssetOpsV1-demo3` with the runbook PYTHONPATH and the plan2 venv:
    `--db assetops_demo3_full_test --work var/demo3_full serve`, PID 25732.
  - Vite ran from `polB2/frontend` with `ASSETOPS_API_PORT=8990` on 5490, PID 30808.
  - The log showed `performance: Performance cutover: permitted`. There were no prepare, add-day or manual writes.
  - Both were stopped by PID (`taskkill /T`), and ports 8990 and 5490 were free afterwards. The slot was released.
- **Strict run** (`DEMOB_STRICT=1`), keys `kobo-board-S, kobo-board-S1, kobo-board-S-open, kobo-verification,
  maintenance-preventive, wr-overview` × 2 widths:
  - exit 1, with **17 counted hits per width (34 total)**;
  - both widths are identical; all 12 captures settled, with no overflow.

| Owner | Hits per width | What |
|---|---|---|
| **PB-2 (this slice)** | **0** | baseline 256 on `-open` (251 UUID, 2 enum, 3 raw timestamps) |
| Awaiting PA-2a (server text, DEMO-A build) | 9 | Kobo board: "when ACT-000001 is verified" (S, and `-open`), `-open` items PM-000003, PM-000004, WR-000001, WR-000002 (`board._item_text`); wr-overview: "Incident INC-000005 · Finding a8cea97b" (code + `Finding <8hex>`), "Linked action ACT-000002" (server link label) |
| PB-3 | 3 | maintenance-preventive "running" (calendar or running hours), "draft" 2 |
| Awaiting PA-3 | 5 | Lab names 3 ("charging lab", "replay lab" ×2 incl. wr-overview), "replay" 2 |

- **`exempt_hits` per capture.**
  - Every capture has 1, the TimeZoneNote.
  - `kobo-board-S-open` has 283:
    - in `data-technical-details`: 255 uuid, 2 enum, 2 raw timestamp, 4 snake_case, 3 product term;
    - `data-vocabulary-exempt=source-reference`: 5;
    - `=user-owned`: 1;
    - `=lab`: 10;
    - time-zone note: 1.
  - The `=lab` value predates PB-2 (PB-0 baseline). It is flagged for the reviewer under Addendum 5.
- Output is in the scratchpad: `pb2/cap/` (PNGs, `captures.json`) and `pb2/cap.log`.

## Known deviations

1. **The Portfolio "scenario" (2 per width) is not done.** It moved to PB-3 with "What-if" wording (Addendum 8 Q4).
2. **Banned word in a ruled string.** "Critical load supplied/demand" contained the banned word "load". It was
   replaced with Architect wording (Addendum 8 Q2), not with a builder synonym.
3. **The day-line coverage fallback reads "not recorded", not "not available yet".** The missing-claim guard reserves
   that phrase for registered gaps. The guard was not loosened.
4. **History "Change record".** The visible History link is plain "Change record". The change id moved into Technical
   details.
5. **Overview slot titles.** The mini slot titles depart from v69 (`v69PanelTitles` `mini:1`/`mini:4`). This is
   approved by §3.1 and Addendum 8 Q3, and is recorded in R655.

## Residual risk

- **Kobo server sentences on the demo.** They still show stored codes and the old gap or title text on the DEMO-A
  build. Proof waits for the PA-3 rebuild captures.
- **`SourceProvenanceRecord` id lists sit behind one more click on every page that uses them.** This includes cold,
  EV and work. Tests querying those ids found them, and the full suite is green.
- **The money panel nests two disclosures.** "How this estimate was made" now contains "How this was worked out",
  which contains "Technical details". This is deep but honest; the reviewer may prefer a flatter form.

## User-review focus

None required. The reviewer should check:
- the copy table and the builder copy list (R655);
- the Technical details mechanism (R656) and its use of `exempt_hits`;
- the claim-label move into the status strip;
- the list of PB-3 files touched.

## Review fold-in (`.agent/review-POLISH-PB-2.md`, ACCEPT with M1)

- **M1.** `WorkedOut` with no plain lines and no `extra` now renders a single "Technical details" disclosure. It keeps
  `data-exact-references`, `data-disclosure` and `data-technical-details`, so there is no empty "How this was worked
  out" level. This affects the verification strip, the Kobo money references, and the finding choice when
  `choiceLines()` is null. Pinned in `ui/__tests__/technicalDetails.test.tsx` ("PB-2 review M1").
- **L1.** The day line now reads "Checked: 1 period of generator use; the measured inputs for this day were not
  recorded". Pinned in `s5SiteWindowOverview`. The missing-claim scan passes unchanged.
- **L2.** `ui/productWords.ts` `REGISTERED_SIMULATION` now reads "Example data, not field readings". The 5 tests that
  pinned the old words were updated.
- **L3.**
  - The stray import line and the triple blank lines are gone.
  - The freshness `<p>` renders only when it has content.
  - Its `data-freshness-*` attributes moved to an inner wrapper, which is empty when nothing is said.
- **L4.** "One finding overlapping …", "Review the finding for this day" and "Open the finding" are now lower case.
- **Main merged.** `c4a39b1dc` is merged in. The CODE_STATE conflict was resolved by keeping both sections (PA-2b,
  then PB-2).
