> Moved verbatim from the former `.ai/CODE_STATE.md` on 2026-11-18 (declutter step 2), part 10 of 11; sections keep their original relative order; the original order of all sections is the numbering in `index-*.md`. Index: `INDEX.md` in this folder.

## post-W6 final-fix - whole-diff review Mediums and Lows (built, awaiting owner walkthrough)

Branch `task/post-W6-final-fix` from main `739c0d7a`. Rulings `archive/agent-history/post-W6-final-review-rulings.md` (binding); packet `archive/agent-history/post-W6-final-fix-packet.md`.

- M1: mini Site Work Incidents/Maintenance default is seven Site-local calendar days including today (`siteSevenDayWindow` in `sites/siteTime.ts`; `workCasesScope(params, site)` in `SiteAnalyticsFrames.tsx` picks it for non-cold/EV Sites, R338 UTC days stay for cold/EV and global Work). Invalid or missing zone uses UTC.
- M2: cold Action refusal map mirrors EV (`coldActionRefusal`, 409 and 503/unreached offer Reload, 403/INVALID_KNOWN_AT/other have none), `COLD_WORK_RELOAD`, cold gets the "Technical detail" disclosure; the cold Actions list keeps its own Retry (app-wide label convergence is backlog (j)).
- M3: the 640 px 152 px first-column rules apply only to the Findings table (`:has(col.estate-findings-col)`).
- L3: one sentence `STALE_BASIS_COPY` for the withheld tariff state on Site and estate pinned reads (`ev_site_reads.py`; `STALE_AS_OF_COPY` aliases it). L4/L5: `coldTabSearch` applies the EV valid-window gate (complete, ordered, at most 31 days, UTC; cutoff kept alone) and the cold Financials > Scenarios tab row uses it. L6: `siteZoneDisplayLabel`/`SITE_ZONE_UNAVAILABLE_LABEL` ("UTC (Site time zone unavailable)") on mini Scenarios and Work fields, Finding history header, mini Evidence Measured/Sent/Received headers. L8: dead mini Performance 422 branch removed. L9: `EV_WINDOW_NOT_UTC_TEXT` for an ordered non-UTC Action window. L11: `KeyValueValue` (V69Layout) makes an overflowing `dd code` focusable (tabindex 0, role group, "Full value: ..." name) with a CSS focus ring.
- Register housekeeping done per `archive/agent-history/post-W6-register-reconciliation.md`: 117 stale D3 rows closed with merge shas (19 are split parents pointing at their child), 60 planned rows now `standing (owner)`, R224 duplicate of R207, counts refreshed; R328 and R374 stay open. Backlog (j) added to `.ai/MILESTONE_REVIEW_BACKLOG.md`.
- Open: backlog (j) items (L1, L2, L7, L10 probes, L11 duplicate 760 px rule, Reload/Retry convergence).

## SCN - Kobo scenario where the reserve change matters (built, in_review)
Branch `task/SCN-kobo-reserve-matters` (from main ca6d7d61b). Contract `AssetOpsV1-plan2/specs/SCN/spec.md`
(§2 U1, Addendum 1 design D2); packet `archive/agent-history/SCN-packet.md`; decision `D-2026-10-31-scn-kobo-reserve-matters`.
- `config/scenarios/kobo-mini-grid-reserve-matters.yaml` v1 (D2): start SOC 34 %, 300 L, STOPPED; 30 W/m2 0/240, 800 W/m2 240/240;
  loads 4 / 2 / 0 kW over 0/480. Fingerprint `50f8be3e...c956`; registered in `PINNED_SCENARIO_FINGERPRINTS`, `NEW_SINCE_T025G`,
  `NEVER_SHIPPED_AS_V1`; `test_the_shipped_scenarios_were_found` 13 -> 14 (the only non-additive test line).
- `host/tests/test_scn_reserve_matters.py`: in-process mini-grid v5 kernel check, reserve 30 vs 25, five design properties, no money.
- Measured (kernel, 5-min steps): baseline generator requested from 03:00 UTC and RUNNING to the run end; it carries load in a
  sawtooth at the 30 % reserve (2.95 / 3.04 / 6.09 kWh in the 04, 05, 06 UTC hours, 0 after the clearing). Reserve 25: requested
  from 04:50, unloaded throughout, minimum SOC 25.16 %. H = 04:00-05:00 UTC.
- Left open: U3 (real-chain probe at H in `-demo3`) and the DEMO-SPARSE day-list consumption; the money figure and verification
  outcome are unknown until U3. The first design's stop is recorded in the packet and `.agent/SCN-evidence/`.
## DEMO-A - combined three-Site demo dataset on the DEMO-SPARSE calendar (merged `4f57261d3`)
Branch `task/DEMO-A-combined-dataset` (worktree `AssetOpsV1-demo3`, merged to main as `4f57261d3`). Contract `AssetOpsV1-plan2/specs/DEMO-SPARSE/spec.md`
+ Addenda 1-4 over `build-sheet-DEMO-COMBINED.md`; packet `archive/agent-history/DEMO-A-packet.md`; history `archive/agent-history/DEMO-A-phase-handoff.md`.
- `tools/demo_combined.py` `prepare | links | serve | tick | add-day | drop` on a private `assetops_demo3_<name>_test` DB; children
  `demo_combined_kobo.py` (day runs + the S/S+1 trial chain), `_cold.py` (ShiftedChain per night, attest at setup instant), `_ev.py`
  (Tuesday days, w504 work rows), `_finish.py` (`check`: CO-1..CO-12 + SP-1..SP-7 via `host/lab_app.py`, `<work>/check.json`).
- `tools/demo_story_days.py` resolves `backend/conversions/demo-story-days-v1.json` (8 Kobo runs incl. S-1d normal, 3 cold, 2 EV);
  `validate` refuses DUPLICATE_DAY, TRIAL_PAIR_INVALID, OUTSIDE_BOARD_WINDOW, DAY_BEFORE_INSTALL, DAY_NOT_IN_PAST and
  DUPLICATE_RECEIVED_AT (acceptance is counted by `received_at`); late Kobo delivery D+2d 12:30.
- Final build `20f83276b` kept as `assetops_demo3_full_test` / `var/demo3_full`: 1105 s, self-check 16/17; trial (a) 06:00, 0 USD (R617).
- Slow build test `backend/tests/test_demo_combined_postgres.py` (19): fixture prepare aborts on any self-check fail (rows error at setup).
- Final round (main `c8702bb2b` merged, head `e3b2caf2d`): CO-1 original assertions (LINK-LINEAGE) and CO-6 on
  estate-coverage/2 (week PARTIAL, cold/EV money settled) pass; self-check 17/17; build test 19/19 (reads through a
  `finish check`/`get` child in the private tree; SP-7 weekday-bound comparison per DEMO-SPARSE Addendum 4);
  `-Tier all` 4688/0/0/0. R535 and R552 now pass on this build (left for the coordinator to close).
- Left open: reads go stale 300 s after the last tick (heartbeat): run `serve` or `tick` before a demo.

## DEMO-B - combined-dataset captures, v70 comparison and walkthrough runbook (built, in_review)

- Tool `tools/demo-combined-evidence.mjs`: `capture <work> <out> [web]` (14 screens x 1440/390 from `story.json`,
  `kobo.json`, `days.json`; settle on no "Loading" + stable text; full-page PNG; measure-mock-panels blocks + overflow;
  visible-vocabulary scan), `mock-ids`, `compare <out> <mock-measure.json>`. `DEMOB_ONLY=<keys>` filters. No product
  code, Python or data changed.
- Route facts it settles: the outcome board renders on the Site Overview (`/sites/KOBO-001?date=`,
  `/sites/COLD-LAB-001?from&to`, `/sites/EV-LAB-001/ev?from&to`); `/sites/{code}/outcomes` and `/overview` (printed by
  `demo_combined.py links`) are not routes (P-01). Cold/EV boards read on `days.json` start/end windows.
- Global work lists window by recorded time (build day), not story time (R629).
- Open: R626, R630 (open rows), polish P-01..P-10 and the client-copy list in `archive/agent-history/DEMO-B-packet.md`.

## POLISH PA-2a - server copy, codes and titles (built, in_review)

- Contract: `specs/POLISH/` §3/§3.1 BE rows, Addenda 4 and 6; packet `archive/agent-history/POLISH-PA-2a-packet.md`.
- `outcomes/display_code.py`: `display_code` (prefix + number padded to at least 3; no `re`, the package stays pure)
  and `finding_label` (title, else "Finding"). Applied to warnings refs, board `_item_text`/`_action_name`, mini
  verification lines, cold contributors and the work link labels (request, incident, detail, linked requests).
  Stored/wire code fields are unchanged.
- Finding labels read the stored revision title: `_ReadTx.finding_titles`, `_ReadTx.action_codes` (work read; the
  `_ACTION_CODES` SQL moved there and global imports it), `title` in `_IndexTx.finding_revisions`, and a private
  `recurs_after_title` from `estate/coverage.py` heads into `estate/index.py` for placement RECURRED.
- Action link labels are the display code, else "Action" (`work/site_index.action_label`).
- `finding_episode.TITLES` per Addendum 4 (MERGED unchanged); stored per revision, so they show from the PA-3 rebuild.
- The cold observation words and `plain_limitation` moved to `analytics/cold_site_reads.py` (estate re-exports them);
  the cold read's `_limits` applies them, so TRANSFER reads "No record of switching to backup power.".
- Open: `mini.FINDING_TITLE` (board name by lifecycle) still mirrors frontend `findingWords.ts` and is pinned
  equal to it by `test_idx_gaps_board`; it changes together with PB-2's `LIFECYCLE_WORDS` alignment.
  `board.COST_NOT_CALCULATED` ("Modelled change not calculated") was not ruled and is unchanged. Asset labels and
  preventive due counts are PA-2b. Captures deferred to PA-3.
## POLISH PA-2b - plan due state and asset labels (built, in_review)

- Contract: `specs/POLISH/` §1.4 backend, §3 asset labels, Addendum 6 Q2/Q4; packet `archive/agent-history/POLISH-PA-2b-packet.md`.
- `outcomes/plan_due.py` `plan_due_state` (OVERDUE / DUE_SOON / NOT_DUE / NOT_ASSESSED; `due == to` not overdue;
  the 14-day horizon is built without importing `datetime`, because `outcomes/` stays pure). `warnings._plans`/
  `_overdue` and `visits.warning_facts` use it.
- `GET /api/work/preventive`: top-level `summary` over the full selection before paging and per-row `due_state` at
  the request `to`; `state_counts` stays null. Not in the selection token: both derive from `next_due_at` and `to`.
- `outcomes/asset_words.py`: the plain word map (EV_CONNECTOR → "Connector", EV_CHARGER → "Charger" as well).
  `work/site_index.asset_fields` builds `asset_label` + `asset_type` for site and global work rows and plans; the
  type count and Site type come from scalar subqueries in `_ELIGIBLE` and `_PLANS`. `asset_type` joins the plan basis.
- `cold.py` matches Protect plans by `asset_type`; `visits.asset_name` uses the plain label as it is.
- Open: the frontend parsers (`globalWorkParts.assetLabelWords`, `siteWorkCases.coldAssetLabel`) still parse
  " · " and fall back to showing the plain label (PB-3 replaces them). `global_detail` `work_asset` still returns
  raw `{asset_code, asset_type}`. The preventive cards and chips are PB-3.

## POLISH PB-2 - Kobo board, verification, display codes (built, in_review)

- Ids (§3, Addenda 5 and 8 Q5): `frontend/src/ui/TechnicalDetails.tsx` holds `TechnicalDetails` (a closed "Technical
  details" disclosure carrying `data-technical-details`), `TechnicalReferenceList`, and `WorkedOut` ("How this was
  worked out", with plain lines and the values nested in Technical details). `ui/Disclosure.tsx` has an optional
  `technical` prop. `ExactReferences` is unchanged; its cold/EV/foundation call sites stay PB-3's.
  Switched: `SiteWindowOverview` (freshness, money and choice references), `OverviewFindingList` `ListReferences`,
  `SourceProvenanceRecord` id lists (shared by every source record), the verification `DigDeeper` and strip
  references, and SiteAction History failure/applied/observed codes.
- Codes (§3): `ui/displayCode.ts` `displayCode()` mirrors `outcomes/display_code.py`. It is applied at the visible
  record-code renders: SiteAction, SiteRecommendation, recommendationVerification, DomainActionVerification,
  SiteWorkActions, siteWorkCases, SiteAnalyticsFrames, work/{workRequestShared, GlobalIncidents, GlobalMaintenance,
  GlobalPreventive, OperationalRecords, WorkRequestRecord}, estate/{actionIndex, EstatePortfolio}.
  aria-labels, `data-*` attributes and the "Action code" reference row keep the stored code.
- Kobo copy: §3.1 rows with the Addendum 4 swaps (`dayReadingLine`, `overviewReadsStrip`, `MONEY_ZERO` for P-06).
  The mini slot titles are "What happened on this day" and "Possible cost" (`v69PanelTitles` `mini:1`/`mini:4`).
  `dispatchWords` ROLE_WORDS has the essential-service power words, and its fallback capitalises.
- Titles: `findingWords` `LIFECYCLE_WORDS` and `mini.FINDING_TITLE` use the Addendum 4 titles (MERGED unchanged).
  `mini.GAPS_NO_READINGS` is "{g} of the last {n} days {verb} no checked readings yet".
- The verification claim label is an inline item of the status strip (`ClaimLabel inline`), which clears the
  3 w1f4VerificationStructure failures.
- Open: the Kobo board server sentences still show stored codes on the DEMO-A build (awaiting the PA-3 rebuild). The
  Portfolio "scenario" words and the cold/EV headings are PB-3's (Addendum 8 Q3/Q4). `data-vocabulary-exempt="lab"`
  (10 hits on `kobo-board-S-open`) predates PB-2.

## POLISH PA-3 - producers, links and rebuild (built, in_review)
Branch `task/POLISH-PA-3-producers-rebuild` (worktree `AssetOpsV1-polA3`, from main `c4a39b1dc`, main `0ad27df7f` merged).
- Contract: `specs/POLISH/` §1.3, §3, §4, §5 PA-3, Addenda 3, 9-12; packet `archive/agent-history/POLISH-PA-3-packet.md`.
- `tools/demo_combined.py`: pure `story_links` + `LINK_FORMS` (no `/outcomes`/`/overview`; cold/EV on the `days.json`
  event window, whole day "no event" otherwise); guards accept `assetops_polish_<name>_test` and `var/polish*`.
- `demo_combined_ev`: `ev.json` records `action_code`, `intent_id`, posted `raised_at` (P-08; R645). Narratives
  `"{title}."` in Kobo/EV and, via `ns["DEMO_NARRATIVES"]`, in w502's fixture WR and visits (standalone unchanged).
- `install_cold_lab`/`install_ev_lab(display_name=)` override the fixture name (same sha256); the demo passes
  "GreenHarvest Cold Room"/"Depot Charging Hub" (R646; R111 closed for the demo build).
- `demo_combined_finish.cost_row_action_links` (Addendum 10): Action href in `earlier` when the trial is final, else
  issues/in_hand; Must-not-harm href + display code; L1 sentence. `ev_site_reads` TARIFF_GAP plain words (R655).
- Addendum 12 wire: board case items `kind`/`occurred_at` (plan items `kind: "PLAN"`); preventive rows
  `site_time_zone`; `global_detail.work_asset.asset_label`.
- Build: `assetops_polish_full_test` / `var/polish_full` at `84ab3ca3d`, S = 2026-10-30, self-check 17/17; slow build
  test 19/19. `assetops_demo3_full_test` untouched (walkthrough fallback).
- Fix round (Addendum 13 item 3): Portfolio confidence/action text "Supported finding · example data", "No action agreed
  yet · review the recommendation"; Kobo Assure readings "Example data · readiness …" (not in the polish build; PC rebuilds).
- Left open: strict capture 15 hits per width, all PB-3 frontend (portfolio Finding ids and "Scenario", cold
  "Running", EV `REC <uuid>` and "Scenario details", preventive "running hours"/"draft").
## POLISH PB-3 - Estate, cold/EV and work copy; P-07, P-09, P-10 (built, in_review)

- P-07: `work/WorkRequestOverview.tsx` `RepeatVisitNotice` wrapper always carries `data-repeat-check`
  (`loading` | `unavailable` | `none` | `found`). The capture settle waits on `loading`. R630 closed.
- P-09: `work/GlobalPreventive.tsx` reads the optional `summary` (all three counts, or treated as not sent) and the
  per-row `due_state` and `site_time_zone`. It renders the cards, the strip badge ("{n} overdue" / "None overdue")
  and the row chips; due dates use `formatDay(value, {timeZone})`. `GlobalWorkBar`/`StatusLine` take `dueDates`
  (Preventive, Maintenance) and `WorkRequestBar` always shows the two-part note. DRAFT reads "Not yet approved".
- P-10: `sites/OutcomeBoard.tsx` has an optional `onRead(read)` with no extra fetch. `outcomeBoardClient`
  `OutcomeLinkItem` has optional `kind`/`occurred_at`. `coldSiteViews` `windowIncident()` picks the first INCIDENT
  item in `[from, to)` for the "What happened" description and "Open incident →".
- Asset words: the frontend label parsers are gone; rows render the wire `asset_label`. `WorkRequestOverview` uses
  `work_asset.asset_label`, falling back to `assetWords` (backend word map, no "EV connector").
- Ids: `ui/TechnicalDetails.tsx` gains `TechnicalReferences` (one closed Technical details region). It is used by
  the cold/EV views in place of `ExactReferences`; it sits in `ui/` because the substrate rule bars a `variant`
  prop in `sites/`. EV `REC`/`F` ids now show as "Charger report"/"Finding", with the id in `title`,
  `data-vocabulary-reference` and Technical details. Estate progress rows, findings ids and financials references
  sit in Technical details.
- Time: the PB-1 out-of-capture UTC list is done through `ui/time.ts`, with one `TimeZoneNote` per page.
  `findingPresentation` `readableTime`/`readablePeriod` now delegate to `time.ts`.
- Open: `MiniScenarios.tsx:216` "Scenarios created through" (banned "scenario", not a capture screen).
  The MiniPerformance Site-local `YYYY-MM-DD` day. `coldDueText` `YYYY-MM-DD`. `SiteEvidence`/`FindingDetail`/
  assessment pages use `readableTime` but may have no `TimeZoneNote`. SiteFinding pages mix Site-local times with
  the "Times in UTC" note. Lane A strings noted in the packet (placement/portfolio display values).
- WALK1 (post-polish walkthrough fixes): WALK1-1 Portfolio counts over checked days (`count_basis`, `checked_days[].withheld`,
  "None shown yet"), Assure `verified_result_count`; WALK1-2 Depot declared tariff 0.30/kWh, EV board prices on ESTIMATED;
  WALK1-3 migration `0040_walk1_productive_price` is the head (`productive_use_price_per_kwh`, Kobo 0.25/kWh), `supply-use`
  Foundation property, estimated productive-use sales (overlap per asset = no estimate), Assumptions price row.
- WALK1-4: Kobo `mini-grid` v6 (charge request at `@{plant.battery}`, mean kW) and publication v5 (v4 + charge request, PV
  output every 5 min), roles-4 at install +27 min, manifest `d-verification-window-v3.json` for every Kobo day (v2 unchanged).
  The mini-depth hour read judges each row under its own as-accepted binding revision, provided the pinned roles-4 set binds
  the same role and asset at that time (D-W1-10). Revision lineage lists every set used. Finish WK-2a (S-1, 42.08 USD) and WK-2b (S).
  Under outcome-status/3 (WALK1-3b) WK-2b expects S Grow state ON_TRACK/WATCH/UNKNOWN with `potential` set, not OPPORTUNITY.
  Open: boards go UNKNOWN (PRODUCER_NOT_SETTLED) about 5 min after the last scheduler tick (schedule heartbeat stale after 300 s,
  Site visit after 900 s, `scheduling/health.py:47-49`); `serve` (tick every 120 s) keeps them fresh. Captures/finish reruns must run
  under `serve` or right after a tick. Not caused by this slice.
- WALK1-3b migration `0041_walk1_objective_min_days` is the head (nullable `outcome_objective_revision.min_checked_days`,
  1-28, `productive_use_kwh` only, NULL = `DEFAULT_MIN_CHECKED_DAYS` 3). Grow row: KPI state from `judge_month` (MG-1 month
  to date over the Site-local month, `site_outcomes/mini.py` `_productive_month`/`mg1_reading`); a declared objective's
  verdict outranks an open opportunity (`outcomes/status.py`), carried as row `potential` and a second chip; contributor
  slot `SiteFacts.objective_after`. Fixed the two main failures (merged Finding title, gap-line `withheld`). Open: the mini Assure "not checked yet" count
  treats ON_PACE/BEHIND_PACE/TOO_EARLY as not checked; `outcome-status/2` was not bumped.
- WALK1-3b merged: migration `0041_walk1_objective_min_days` is the head (`min_checked_days`, default 3, 1-28, productive-use only);
  `judge_month` (MET/ON_PACE/BEHIND_PACE/TOO_EARLY over the Site-local month, no projection); objective-led rows take state from the
  verdict, opportunity rides as `potential` (second chip); POLICY now `outcome-status/3` and `outcome-objectives/2` (supersedes the /2 and /1
  mentions above); Assure line lists met / on pace / behind pace / too early / not checked. The two main test failures are fixed.
  Demo-date rule: S = prepare day - 2; do not prepare on days 3-5 of a month (MG-1 reads "too early to judge").

## OWN-G1 - add-dates (built, in_review)

- `tools/demo_combined.py add-dates` (build sheet OWN-GAPS §4, R2-G1, R5, R6): plan (`plan_add_dates`), then per date the
  Kobo/Cold/EV day (`_add_core_day`) and Kisiwa night (tree child `add-day`), date-major, then `finish check`.
- R5.2 settle: before a date is called checked, `drain_mini` (worker CLI, no per-tick bound) then `drain("settle-<date>")`
  (scheduled ticks until every count is 0); Kisiwa dates run `drain_mini`, `tick_and_verify`, then `drain`. Items carry
  `tick_failures`; a `DRAIN FAILED` stops the command with earlier dates in place. A closing `settle-close` runs if counts are
  above 0 after the last date (also under `--no-check`).
- R6.1: when the check runs, one `tick()` plus `retry_until_visited` precedes `finish_check` (the schedule must have just run;
  the product reports "not current" after 300 s without a tick, and that stays). R6.2: WK-6 uses
  `demo_combined_rows.study_ending(found, S+1)` (exactly one study ending that day) instead of `max()`.
- Recipe, not code: replacing a build's `tree` deletes its file-backed legacy comparison report; re-run `evidence_migration` and
  `performance_migration` after (R6.3). Never replace `tree` on the demo path.
- Tests: `backend/tests/test_own_g1_add_dates.py` (38, no DB); K7 skip-branch count is 13 (KIS-11).
- Rehearsal (fresh clone): run A 51/51 PASS (2545 s; settles 87.2 s and 109.6 s, 1 tick each), run B (10.5 min later, nothing
  to add, one closing tick) 51/51 PASS (1364 s). Packet `archive/agent-history/review-packet-G1.md`.
- Review fix round: a PUBLISHED Kisiwa night is resumed (planner starts after the last DONE night) and the child refuses any later
  night (`NIGHT_NOT_FINISHED`); `--dry-run` runs the read-only preflight; a stopped command prints what it added.
- Open: Kisiwa added-night board row in `finish check` is BL-52 (backlog). EX-2 = F-COH PASS in runs A and B (F-COH3 proves it is
  not vacuous); the standalone 8 findings are the old fixture's COH-10 x3 and the known BL-47 COH-2 x5, 0 from G1.


## IA-1a - the frame and gates of the shape rebuild (built, in_review)

- Mock-up only (`interactive-mockup-vNEXT/`). New: `ia-routes.js` (IA_ROUTES, IA_ALIASES, IA_RAIL, IA_LANDED, iaParse,
  iaLive, iaStart, iaDev), `ia-shapes.js` (iaFrame, iaUnlink, iaFinish, iaRender, iaBind, the plan interim), `ia.css`.
- Live in IA-1a: `plan` (shape plan, interim of D-IA.20; `planParts` byte-identical) and the typed `not-found`. Every
  other rail item is an unavailable root; links to unlanded targets are unlinked before insertion.
- Gates: `tools/ia_gates.cjs` runs `shape_check`, `click_depth_check` (self-test only until IA-1b), `after_render_check`
  and their 10 plants. r5 G1 and L-a carried in `ux_interaction_check.cjs` (`UXI_PLANT=container`).
- Open: G1 live surfaces from IA-1b; the empty hash still opens the legacy Portfolio; IA-1b adds hub tabs and
  `IA_G1_SURFACES`.
