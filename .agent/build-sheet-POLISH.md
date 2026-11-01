# Build sheet: POLISH (client-demo polish round)

Architect: Claude (assetops-architect; ROLE_CONFIG "Architect Is Claude By Default", 2026-10-27). Date 2026-11-01.
Main at writing: `884be1fbe`. Owner trigger (verbatim, `.agent/owner-client-demo-sequence-2026-10-31.md`):
"start the polish round first, walkthrough after". The owner walkthrough follows this round, so the result must be
client-presentable.

Inputs: `.agent/DEMO-B-packet.md` (P-01..P-12, client-copy list, runbook), `.agent/DEMO-B-captures/`,
`.agent/review-DEMO-B.md`, `.agent/demo-sprint-lows-2026-10-28.md`, `.agent/demo-sprint-lows-2026-10-31-pipeline.md`,
`.agent/owner-ui-ux-guidance-2026-10-25.md`. Diagnoses were made from the code at `884be1fbe` and read-only SELECTs
on `assetops_demo3_full_test` (kept build `AssetOpsV1-demo3`, S = 2026-10-29, built 2026-10-31).

Standing rules for every slice:
- Plain client copy. No codes, ids, enum names, developer words or register ids on screen.
- Missing data reads "not available yet". Never tune numbers or story data.
- The v70 mock is the layout spec. Every changed mock string or element gets a register row (§7).
- State-of-the-art UI within demo speed: cheap and local changes only (copy, CSS, states).

A **unit** is about 0.25 builder-day: one reviewable commit, including updating the tests that pin changed strings.

---

## 1. Diagnoses (six suspected contradictions)

| # | Symptom | Class | Root cause (evidence) | Fix (slice) |
|---|---|---|---|---|
| P-06 / R626 | Kobo day S: "0.00 USD exposure in this hour", "0.00 to 0.00 USD" over 200 avoidable minutes | **Correct but confusing copy**, plus wrong "hour" wording | The stored amount really is 0. `financial_consequence_revision` S row: window 04:35-07:55, PRICED, quantity 0 L, price 1.25 USD/L, amount 0/0.00. The 40 power intervals all have `mean_kw` 0. Accepted evidence: `generator_power` 0 kW ×40 while `generator_state` RUNNING ×40, because PV (45 kW) covers the load and charges the battery. Model `fuel-cost-1` prices delivered kWh only. The price is declared (`tools/demo_combined_kobo.py:85-96`). "in this hour" (`site_outcomes/mini.py:48-49`) is mock copy on a whole-day board. | §1.1 (PA-1, PB-2). No data change. The idle-fuel model is owner question Q1. |
| P-07 / R630 | WR-000006 has no repeat-visit notice; the cold board warns | **Product bug** (silent async notice). The cause is probable, not proven. | Both surfaces read the same board warning. `RepeatVisitNotice` (`frontend/src/work/WorkRequestOverview.tsx:157-191`) renders `null` while the board read loads and on a refused read (`.catch(() => undefined)`). The DB agrees with the matching rule: WR-000007, WR-000008 and WR-000006 are all completed on generator-1, and the latest is WR-000006 (`6d715387…`), which is the captured page. The capture settle check (3 stable reads 600 ms apart) can finish before the board read returns. | §1.2 (PB-3) |
| P-08 | Depot fault window: the Action raised for the fault Finding is not in Already in hand | **Story-data gap** (build-time clock). Board code is correct. | The Action ACT-000003 is in `domain_action`, `raised_at` 2026-10-31 18:41 (build time; `tools/w504_ev_work_walkthrough.py:218-221`, Ruling 35). The board reads `raised_at` in `[hi-31d, hi)` with `hi` = 2026-10-27 09:00 (`site_outcomes/ev.py:115`, `work/adapters/postgres_domain_action_index.py:70-75`). The Finding revisions themselves were recorded at build time (2026-10-31 18:41:09), so an Action dated inside the story window would predate its own Finding: backdating is refused. `ev.json` has `code: null` because of a producer slip: `tools/demo_combined_ev.py:156-157` reads `code`/`id` where the API returns `action_code`/`intent_id`. | §1.3 (PA-3): register; fix the slip; runbook line. No board change. |
| P-09 | Preventive "Overdue: Not assessed · No due evaluator"; boards warn plan overdue | **Product bug** (missing wiring; stale copy) | Boards: `outcomes/warnings.py:211-223` `_plans` with `site_outcomes/visits.py:68-71`: a CALENDAR plan with `next_due_at < to` is overdue, `< to + 14 d` is due soon. Preventive rows already carry `trigger_kind`/`next_due_at` (`frontend/src/work/globalWorkClient.ts:112-113`), but `GlobalPreventive.tsx:171-180` and `:46` hardcode "Not assessed". DB: PM-000009 due 10-25 and PM-000013 due 10-21 are overdue for `to` = 11-01; PM-000004 (11-02) and PM-000010 (11-07) are due soon; PM-000003 runs on run-hours. | §1.4 (PA-2 backend counts, PB-3 UI) |
| P-10 | Cold failure "What happened" says "No incident recorded"; INC-000005 is Open under Already in hand | **Product bug** (hardcoded placeholder) | `frontend/src/sites/coldSiteViews.tsx:622` passes the constant `"No incident recorded"` and never reads incidents (W2-04, before incidents existed). INC-000005 occurred 10-29 16:11, inside the window, with 2 Finding links. | §1.5 (PB-3) |
| P-11 | Depot Optimize: "a tariff estimate exists in Financials"; Grow, money and Next step: no EV tariff | **Product bug** (unchecked fixed sentence) | `outcomes/catalogue.py:72` `ROW_NOT_MEASURED[(EV,"OPTIMIZE_COST")]` (and EV-2 `missing_records` `:53-54`) is emitted by `site_outcomes/board.py:562` without any check. DB: EV-LAB-001 has 0 rows in `financial_assumption_revision`/`assignment`. Grow (`ev.py:192-202`), money (`ev_site_reads.py:40`) and Next step (`:74`) are correct. | §1.6 (PA-1) |
| P-12 | Kobo Assure "No objective declared" on S, "Unknown" on S+1 | **Product bug** (readiness rule) | The Mini Assure row holds MG-7 only (`outcomes/catalogue.py:50`). MG-7 settles only when readiness is not UNKNOWN (`mini.py:347`, `outcomes/status.py:55-91`). On S+1 the trial worked and the generator never started (generator_state STOPPED ×97). The dispatch day is COMPLETE with zero intervals, and `analytics/claim_limit_read.py:507-508` `reduce_day` maps "zero intervals" to UNKNOWN, so MG-7 reads Unknown on the day the result was verified. Kobo declares MG-1/2/5 only, so S's "No objective declared" is honest. | §1.7 (PA-1) |

None of the fixes changes a stored number or story fact. The only data changes are a producer bookkeeping slip (P-08),
request narratives that are currently a test default, and the Lab Sites' display names (§3, PA-3). These are text,
not quantities.

### 1.1 P-06: zero priced exposure

Backend, `backend/assetops_backend/site_outcomes/mini.py`:
- `COST_MONEY` becomes `"possible extra fuel cost on this day"` (rendered after the amount, as now).
- `COST_NO_MONEY` becomes `"No fuel cost estimated for this day"`.
- In `compose`, where the Cost headline and `headline_money[COST]` are set (around `:381-389`), handle the case where
  money is PRICED and `Decimal(str(amount_high)) == 0`:
  - set the headline text to `"No fuel cost estimated: the generator was on but delivered no measured power"`;
  - set `headline_money[COST] = None`.
  - Do not test `amount_low`: the schema pins it to 0.

Frontend, money panel in `frontend/src/sites/SiteWindowOverview.tsx` `Money` (around `:786-801`), when the state is
PRICED and `amount_high` is 0:
- the big value is `"No fuel cost estimated"` (same style as "Not priced");
- the sub-line is `"The generator was on longer than needed but delivered no measured power. Fuel used while idling is not estimated yet."`;
- the "Latest estimate" chip and the "How this estimate was made" disclosure stay.
- Non-zero amounts keep `boardMoneyText` (`OutcomeBoard.tsx:68-73`) unchanged.

Register: R626 is closed by this fix ("honest zero; idle fuel not modelled; owner Q1").

### 1.2 P-07: repeat-visit notice

`frontend/src/work/WorkRequestOverview.tsx` `RepeatVisitNotice` sets `data-repeat-check` on its wrapper in every state:
- loading: `data-repeat-check="loading"` and a muted line "Checking for repeat visits…".
- refused or failed: `data-repeat-check="unavailable"` and "Repeat visits: not available yet (the site summary could not be read)".
- loaded, no matching warning: `data-repeat-check="none"` and no text.
- loaded and matched: `data-repeat-check="found"` and the existing notice.

Slice step 0 (before any code): with the kept build served, GET `/api/sites/COLD-LAB-001/outcome-board` and confirm
`warnings[]` holds `REPEATED_MAINTENANCE_NO_RESULT` with href `/maintenance/requests/6d715387-39a8-436f-a52c-282e8350e558`.
If it does not, stop and return to the Architect.

The capture tool settles a page only when no `[data-repeat-check="loading"]` remains (PB-0).

R630 is closed when `wr-overview` shows the notice.

### 1.3 P-08: Depot Action outside the fault window

- Ruling: no board change. As-of semantics are right: an Action raised after a window is not "already in hand" for that window.
- Backdating is refused for two reasons:
  - The Finding revision itself is recorded at build time, so a backdated Action would predate its own Finding.
  - Dating the Finding chain to story time would need the cold-style recorded clock across the EV assessment chain,
    which is about 2 d of producer work plus a rebuild. That is not demo speed.
- `tools/demo_combined_ev.py:156-157`: record `declared["action"]["action_code"]`, `declared["intent"]["intent_id"]` and
  the Action's own `raised_at`, not `declared["R"]`.
- New register row R645 (D4): "Depot fault-window board: the fault Action exists (raised at build time, after every
  story window), so Already in hand lists only the plan; the Action shows on the Actions list."
- Runbook line (PC): "Depot: the follow-up Action is on Work › Actions; the fault-window board shows the warning and the plan."
- Same slice, copy bug: `site_outcomes/ev.py:220` `f"Investigate connector {label}"` doubles the word. Use
  `connector_name(label)` so it reads "Investigate Connector c1".

### 1.4 P-09: Preventive due state

- Backend (PA-2): extract the board predicate into one pure helper, `outcomes/plan_due.py`
  `plan_due_state(trigger_kind, next_due_at, to) -> "OVERDUE" | "DUE_SOON" | "NOT_DUE" | "NOT_ASSESSED"`, with `SOON` = 14 d.
  - Only CALENDAR plans with a due date are assessed; everything else is NOT_ASSESSED.
  - `warnings._plans` and `visits.py` call the helper, with unchanged behaviour (existing warning tests must pass unchanged).
- The global preventive read (the backend route behind `GlobalPreventive`, `backend/assetops_backend/work/`) adds:
  - `summary.overdue_count`, `summary.due_soon_count` and `summary.not_assessed_count`, over **all** plans matching
    the filters, not just the page;
  - a per-row `due_state`.
  - `to` is the request's `to`.
- Frontend (PB-3), `GlobalPreventive.tsx`:
  - Cards: "Overdue" `{overdue_count}` with note `Calendar plans due before {day(to)}`. "Due in the next 14 days"
    `{due_soon_count}` with note `Calendar plans due by {day(to+14d)}`. When `not_assessed_count > 0`, add the line
    `{n} plan(s) run on running hours; not checked here yet`.
  - Strip badge (`:46`): `{overdue_count} overdue`, or `None overdue` when 0.
  - Row chip from `due_state`: Overdue (amber), Due soon (blue), No date (neutral), or nothing for NOT_DUE.
- The register's P-B3-3 departure (Preventive due state not assessed) is closed.

### 1.5 P-10: cold "What happened" incident line

- `frontend/src/sites/coldSiteViews.tsx:622`. Choose the description from the outcome-board read the page already holds:
  - the first INCIDENT case fact with `occurred_at` in `[from, to)` gives `Incident {displayCode(code)} · steps from the recorded readings`, with an "Open incident →" link to the case href, matching mock `v69/index.html:540`;
  - board loaded and no incident gives `No incident recorded in this period`;
  - board not loaded gives `Steps from the recorded readings`.
- If the cold page does not already hold the board read at this component, pass it down from `coldSiteRoutes.tsx`,
  which renders the board. No new fetch.

### 1.6 P-11: EV Optimize tariff sentence

In `site_outcomes/board.py` `_row` (near `:562`), for `(EV, "OPTIMIZE_COST")`:
- use the existing sentence only when `facts.headline_money.get("GROW_REVENUE") is not None` (a priced EV tariff);
- otherwise use a new `catalogue.py` constant `ROW_NOT_MEASURED_EV_COST_UNPRICED = "Energy cost per km needs odometer readings and a published charging tariff"`.

Apply the same condition where EV-2 `missing_records` (`catalogue.py:53-54`) is shown. Update the tests that pin the
old string. Register row R635 (D4) cites R628/R263.

### 1.7 P-12: Kobo Assure on a day with no generator run

Narrow rule in `site_outcomes/mini.py` `compose` only. The shared `claim_limit_read.reduce_day` is not changed: it
feeds Portfolio evidence cells, and a shared-rule change needs its own slice.

When readiness is UNKNOWN **and** the day's dispatch window revision is COMPLETE with zero assessed intervals, treat
MG-7 as settled. Use the same fields the Overview's "Day reading" line reads (`frontend/src/sites/SiteWindowOverview.tsx:496-498`
shows "Assessed · 0 operating periods"; take them from the overview body the board already composes). Then:
- the Assure chip follows `outcome_state` as on S, so it reads "No objective declared";
- the Readings contributor text is `No generator run to check on this day · readings complete`.

Pre-flight check by the builder: the S+1 capture also shows Grow as "Unknown".
- If `outcome_state` for the MG-1/MG-6 contributors is UNKNOWN for the same readiness reason, apply the same settled rule.
- Otherwise do not change it. Add register row R636 (D4) with the observed reason, and return the reason in the packet.

---

## 2. P-04 ruling: MOCK DEVIATION labels on client screens

**Ruling.** Client screens never show `MOCK DEVIATION` text. The register stays the record. Each live label stays in
the DOM, tagged, and renders only in **review mode**.

- **Mechanism.** One rule in `frontend/src/ui/mock-deviation.css`, which every label already loads or which gets
  imported once from `frontend/src/main.tsx`:
  `:root:not([data-review-labels="on"]) [data-mock-deviation] { display: none !important; }`
  - This hides all 17 inline labels and the shared `MockDeviation` component (`frontend/src/work/globalWorkParts.tsx:102`),
    which all carry `data-mock-deviation`.
  - `display:none` also removes them from the accessibility tree, so screen-reader users get the client view too.
  - The existing R453 width rule still applies inside review mode.
- **Review mode switch.** New file `frontend/src/ui/reviewLabels.ts`, called first in `main.tsx`:
  - `?review=labels` sets `sessionStorage["assetops.reviewLabels"] = "on"`; `?review=off` removes it.
  - Then set or remove `document.documentElement.dataset.reviewLabels = "on"`.
  - Wrap every storage call in try/catch. With no storage, the URL parameter alone decides for that page load.
  - Default is off. Nothing in the UI links to review mode.
- **Tests.** Vitest (jsdom) does not apply CSS, so existing label assertions stay valid. Add
  `frontend/src/ui/__tests__/reviewLabels.test.ts` for: param on/off, storage failure, and the dataset attribute.
  Also assert that the CSS file contains the hide selector (import with `?raw`).
- **Register rule change.** Replace the first sentence under "Post-W6 audit Architect rulings" in
  `.agent/mock-departure-register.md`, which is `Each open D1/D2/D4/D5/D6 row must show MOCK DEVIATION Dn beside the affected element…`, with:
  > Each open D1/D2/D4/D5/D6 row whose departure is visible on a screen has a label element beside the affected element
  > carrying `data-mock-deviation="Rnnn"` and the text `MOCK DEVIATION Dn (Rnnn)`. The label renders only in review
  > mode (`?review=labels`); client mode, the default, hides it (POLISH §2, 2026-11-01). The register remains the record.
  > Reviewers check labels in review-mode captures. A departure without a tagged label, or a label visible in client
  > mode, is a High finding.
  - Rows that today are labelled only in code comments (for example the `// MOCK DEVIATION` comments) are unchanged.
- **Guards.**
  - New guard 12 in `tools/check-all.ps1`, "Mock deviation labels and client vocabulary", runs
    `node --test tools/checks/test_mock_deviation_labels.mjs`. Its scanner `tools/checks/mock-deviation-labels.mjs` checks three things:
    - (a) every non-comment JSX text containing `MOCK DEVIATION D` in `frontend/src/**/*.tsx` (tests excluded) sits in
      an element whose opening tag has `data-mock-deviation=`, or is rendered by the `MockDeviation` component;
    - (b) every `data-mock-deviation` id exists as a row in the register;
    - (c) the hide selector is present in `mock-deviation.css`.
    - Fixtures: one passing file, one untagged label, one unknown id, and the missing CSS rule.
  - `tools/demo-combined-evidence.mjs` in client mode must record zero `MOCK DEVIATION` hits (strict gate, PB-0).
    `DEMOB_REVIEW_LABELS=1` captures in review mode, for reviewers.
- **ROLE_CONFIG.** No change. Its MOCK DEVIATION rule is about rulings, not screens.

---

## 3. Copy pass (old → new)

General rules, applied by the builders:
- **Record codes.** Storage keeps the `ACT-[0-9]{6,}` CHECK (`backend/migrations/versions/0016_action_store.py:51`), so codes are formatted only for display.
  - One rule: prefix plus the number zero-padded to 3 (`ACT-000001` → `ACT-001`, `WR-000006` → `WR-006`, `INC-000005` → `INC-005`, `PM-000013` → `PM-013`), matching the mock's `ACT-048`/`INC-203`.
  - Backend: `backend/assetops_backend/outcomes/display_code.py` `display_code(code: str | None) -> str | None`, used in every server-composed sentence that embeds a code (`site_outcomes/*`, `outcomes/warnings.py`).
  - Frontend: `frontend/src/ui/displayCode.ts` `displayCode()`, used at every render of a `code`/`action_code`/case code.
  - API code fields stay as stored.
- **Ids.** No UUID or 8-character id is visible outside a "Technical details" disclosure. The disclosure element carries
  `data-technical-details`; the capture scan skips it. The existing "Dig deeper…"/"Advanced details" disclosures that hold
  ids are renamed "Technical details" and tagged. Server labels `Finding {fid[:8]}` (`estate/index.py:131`, `estate/placement.py:86`,
  `work/domain_action_index.py:268,347,445,474`, `work/site_index.py:191,208`) become the Finding's title, or `Finding` when no title is held.
- **Times.** New `frontend/src/ui/time.ts` with `formatDay`, `formatDayTime`, `formatTime` and `formatRange`.
  - Format: `29 Oct 2026`, `29 Oct 2026, 16:00`, `16:00`, `29 Oct 2026, 16:00–17:05` (same day), otherwise both ends
    in full. Always computed in UTC (`timeZone: "UTC"`), with **no** per-time "UTC" suffix and no ISO strings.
  - Each page shows one `<TimeZoneNote/>` (`<span data-time-zone-note>All times UTC</span>`) in its date or window bar:
    `EstateDateBar`, the mini day control, the cold/EV window bar, the global work "Updated" bar, and the verification header.
  - The ~10 existing formatters (`estateShared.tsx:64`, `globalWorkClient.ts:744,762`, `coldFormat.ts:26`, `EvEnergy.tsx:46`,
    `EvScenarios.tsx:57`, `SiteFindingIndex.tsx:267`, `SiteWorkActions.tsx:122`, `FoundationRevisionPanel.tsx:26`, `SiteHealth.tsx:85`)
    keep their names and delegate to `time.ts`.
  - Backend sentences that append " UTC" and are visible on the 14 capture screens drop the suffix and use `29 Oct, 04:35–07:55` form (PA-2).
- **Lab Site names (data).**
  - `install_cold_lab`/`install_ev_lab` (`backend/assetops_backend/sites/cold_lab.py:52`, `ev_lab.py:52`) gain `display_name: str | None = None`, which overrides the fixture name.
  - The demo producers pass "GreenHarvest Cold Room" and "Depot Charging Hub", the mock names. This closes R111 for the demo build. The fixture YAMLs and tests are unchanged.
- **Asset labels.** `f"{asset_code} · {asset_type}"` (`work/global_index.py:332,403`, `work/site_index.py:260`) becomes the
  plain type word from one backend map: COMPRESSOR → "Compressor", BATTERY → "Battery", GENERATOR → "Backup generator"
  on cold or "Generator" on mini, CONNECTOR → "Connector". The asset display name is appended only when the Site has
  more than one asset of that type. Server sentences that print `generator-1` (the portfolio warning "generator-1
  visited 3 times") use the same label.
- **Request narratives (data).** The demo producers pass `narrative=` the request's own title as a sentence
  (`"{title}."`), replacing the test default "Witnessed failure requires inspection." (`tools/demo_combined_kobo.py:100,115`,
  `demo_combined_ev.py:106,116`, `tools/w502_cold_work_walkthrough.py:202,315,461`).
- **Finding titles.** `analytics/finding_episode.py:97-100` `TITLES`. Titles are stored per revision, so the change applies from the rebuild on:
  - SUPPORTED: "Generator may have run longer than needed"
  - UNCONFIRMED: "Possible extra generator running not confirmed by the latest check"
  - NO_LONGER_SUPPORTED: "Extra generator running no longer supported by the latest check"
  - Stop rule: if a `contract-fixtures/` digest or golden file pins a title, stop and return to the Architect.

### 3.1 String table

The "Src" column says where the text comes from: FE is frontend, BE is backend, data is producer or fixture data.

| Screen | Old | New | Src (file:line) |
|---|---|---|---|
| Shell | Open Simulator Lab | Simulator Lab | FE `shell/simulatorLabRoutes.tsx:146` |
| Shell | (none) | App-wide banner: "Demonstration · example sites and records prepared for this walkthrough" (§6 D-1) | FE new, in `OperatorShellLayout` |
| Site header | Demonstration data · COLD-LAB-001 | Example data | FE `ui/V69Layout.tsx:392` |
| Cold/EV header | Cold replay lab / EV charging lab | GreenHarvest Cold Room / Depot Charging Hub | data (PA-3) |
| Kobo | UTC day (label) | Day | FE mini day control |
| Kobo | 2026-10-29 00:00 to 2026-10-30 00:00 UTC, start included, end excluded. | (delete; TimeZoneNote) | FE SiteWindowOverview |
| Kobo | Using the latest checked readings · This answer uses the latest readings that have been checked. 2026-10-29, one UTC day at this site · As of 1 Nov 2026, 02:09 UTC | Latest checked readings · 29 Oct 2026 · updated 1 Nov 2026, 02:09 | FE SiteWindowOverview |
| Kobo | Reads on this Overview: Service, Dispatch, Fuel, Renewable. Each outcome row shows only what these reads support for the selected period. | This page uses service, generator, fuel and solar readings for the selected day. | FE SiteWindowOverview |
| Kobo | 0.00 USD exposure in this hour | No fuel cost estimated for this day (zero); `{amount} possible extra fuel cost on this day` (non-zero) | BE `mini.py:48-49` (§1.1) |
| Kobo | Not available yet · 24 of 31 days have no assessed readings | 24 of the last 31 days have no checked readings yet | FE board footer |
| Kobo | What happened in the selected hour | What happened on this day | FE `overviewSlots.tsx:14` |
| Kobo | Selected day 2026-10-29 · plain sequence of the assessed periods · the dispatch view has the detail | 29 Oct 2026 · the periods we checked; Dispatch has the detail | FE |
| Kobo | Hour not selected: this Overview reads one whole UTC day… | (delete the line) | FE `overviewSlots.tsx:89` |
| Kobo | Day reading: Assessed. 1 operating period assessed; 13 measured roles covered | Checked: 1 generator run, from 13 measured inputs (0 → "Checked: no generator run on this day, from 13 measured inputs") | FE `SiteWindowOverview.tsx:496-498` |
| Kobo | The source of these readings is open for current use. | (move into "How this was worked out": "The reading source is active.") | FE `SiteWindowOverview.tsx:293` |
| Kobo | Operating context · Selected day · when readings arrived; context for the cards, not a status source | Operating context · When the generator ran and when readings arrived | FE |
| Kobo | critical load delivered power / critical load requested power | Critical load supplied / Critical load demand | FE `dispatchWords.ts:102` ROLE_WORDS (fallback capitalises the first letter) |
| Kobo | 1036 accepted readings on this day; the first 500 are listed. | 1,036 readings on this day (first 500 shown) | FE `SiteWindowOverview.tsx:668` |
| Kobo | No rule yet says which gaps in the readings matter here: the reading counts are shown instead. | Gaps in the readings are not judged yet; reading counts are shown instead. | FE `:675` |
| Kobo | Needs attention · The Finding chosen for this day and the day's Finding list | Needs attention · The main finding for this day | FE |
| Kobo | 2026-10-29 04:35 UTC to 2026-10-29 07:55 UTC · Open · version 2 · the Finding chosen for this day | 29 Oct, 04:35–07:55 · Open · main finding for this day | FE `OverviewFindingList.tsx:379` |
| Kobo | 1 Finding overlap this day. Showing all 1. Open the full Findings list for this day | 1 finding on this day · Open all findings for this day (plural "{n} findings") | FE `:396` |
| Kobo | Generator support merits review: bounded candidate avoidable running | Generator may have run longer than needed | BE `finding_episode.py:98` (rebuild) |
| Kobo | Bounded money consequence | Possible cost | FE `coldSiteViews.tsx:693` and mini/EV equivalents |
| Kobo | 0.00 to 0.00 USD | No fuel cost estimated (§1.1) | FE `SiteWindowOverview.tsx` Money |
| Kobo | Current amount | Latest estimate | FE `:122` |
| Kobo | This range uses the current version of this Finding and a recorded diesel price. | Based on the latest finding and the recorded diesel price. | FE |
| Kobo | Generated test data. These records were generated for a test. They are not readings from physical equipment. | Example data: these readings were prepared for this demonstration, not measured on physical equipment. | FE `sites/sourceProvenance.tsx:95-98` |
| Kobo | A modelled range of possible extra fuel cost for one Finding, not money lost or saved. | An estimate of possible extra fuel cost, not money lost or saved. | FE |
| Kobo | Cost range, money gate, source record and links | How this estimate was made | FE `:822` |
| Kobo | The Finding records what the assessment concluded about generator operation. No recommendation is recorded on this Overview: any next action starts from the Finding. | Start from the finding to decide what to do next. | FE Next step |
| Kobo | Modelled change after the trial · not realised savings: no lower cost per kWh of feeder demand · Supply cost per kWh before the trial: missed · after: met | Estimated effect of the trial (not money saved): no lower supply cost per kWh. Goal before the trial: missed; after: met. | BE `board.py:52` COST_PREFIX + `trial_fuel_comparison.py:26` LABEL; FE `actionPresentation.tsx:300` |
| Kobo (open) | Access reference DEVELOPMENT_TENANT_OPERATOR_CONTEXT; LATEST_RECORDED_REVISION_OF_EACH_CANONICAL_FINDING; raw ISO "List built at"; "Listed Finding N reference <uuid>" | Inside "Technical details" (`data-technical-details`); the visible label words become "Access: operator account", "Showing the latest version of each finding", "List built {formatDayTime}" | FE `SiteWindowOverview.tsx:320,911`, `OverviewFindingList.tsx:246-250` |
| Verification | Dig deeper: identifiers and typed values | Technical details | FE `SiteActionVerification.tsx:685` |
| Verification | Source Finding version | Finding it came from | FE `:393` |
| Verification | Finding version 2 is a new episode; it does not rewrite this trial | A later finding about the same issue does not change this trial's result. | FE `:1131` |
| Verification | Technical result verified on test data · benefits: mini-grid operator | Verified on example data · benefits the mini-grid operator | FE `actionPresentation.tsx:299`, `ClaimLabel.tsx:14` |
| Portfolio/Findings | Window 2026-10-23 to 2026-10-29 (UTC days) | 23–29 Oct 2026 | FE `estateShared.tsx` |
| Portfolio/Findings | Evidence cutoff 2026-11-01 02:09:11 UTC (latest at read time) | Latest information, as of 1 Nov 2026, 02:09 | FE `estateShared.tsx:82-85` |
| Portfolio/Findings | Evidence cutoff (UTC) mm/dd/yyyy picker + Show | Moved into a closed `<details>` "View an earlier point in time" | FE `estateShared.tsx:137-144` |
| Portfolio | Finding COLD-LAB-001 · d374e29a-… · Chamber temperature above policy | Chamber temperature above policy (mechanism words only) | FE `EstatePortfolio.tsx:141` |
| Portfolio | Opens current Site view | Current view | FE `portfolioWords.ts:133`, BE `estate/evidence_money.py:43` |
| Portfolio | Basis not recorded | Cost basis not available yet | FE `EstatePortfolio.tsx:150`, `EvSiteViews.tsx:1411` |
| Portfolio | Episode window not recorded | Time not available yet | FE `:118` |
| Portfolio | No end is recorded for this episode | No end time yet | BE `estate/placement.py:26` |
| Portfolio | Supported, coherent source | Well supported | FE `portfolioWords.ts:40` |
| Portfolio | Supported Finding · Generated test data source | Supported finding · example data | FE |
| Portfolio | Recommendation not accepted | No action agreed yet | BE `estate/portfolio.py:146` |
| Portfolio | No accepted Action · Next move not recorded | No action yet (delete "Next move not recorded") | FE `EstatePortfolio.tsx:169-171` |
| Portfolio | Partly checked · Value withheld | Partly checked · value shown once every day is checked | FE `:97,112-113`, `findingIndex.tsx:120` |
| Portfolio | Not comparable for this selection | Can't be compared across these sites yet | BE `portfolio.py:297`, FE `portfolioWords.ts:82` |
| Portfolio | Not established (Assure card) | Not known yet | FE |
| Portfolio | 5 SELECTED FINDINGS · COVERAGE INCOMPLETE | 5 findings · some days not checked | FE |
| Portfolio | Policy trial awaiting outcome · 0 / Verified resolutions · 1 | Trials waiting for a result · 0 / Fixes confirmed · 1 | FE `:454,459` |
| Portfolio | generator-1 visited 3 times in 60 days | Backup generator visited 3 times in 60 days | BE warning text (asset label rule) |
| Findings | one global object model | (delete the phrase) | FE `findingIndex.tsx:84` |
| Findings | Supported / Unconfirmed / No longer supported / Merged | Confirmed / Not yet confirmed / No longer applies / Combined with another | FE `findingIndex.tsx:93` |
| Findings | No supported lens | Not in any category | FE `:347` |
| Findings | Finding <uuid> · revision <uuid> | (Technical details only) | FE `findingIndex.tsx:327` |
| Findings/Financials | Coverage incomplete | Some data missing | FE `actionIndex.tsx:49,67`, `estateFinancialsWords.ts:42` |
| Cold | Selected window 29 Oct 2026 16:00–17:05 UTC · Selected evidence through 29 Oct 17:05 UTC | 29 Oct 2026, 16:00–17:05 · information up to 17:05 | FE |
| Cold | Degraded / Confidence: Bounded / Potential product exposure (chips) | Service affected / Confidence: partial / Stock may be at risk | FE `coldSiteViews.tsx:607`, `coldAssessmentWords.ts:36` |
| EV | Confidence: Bounded (OBSERVED) / Limited (BOUNDED) | Confidence: measured / Confidence: partial | FE `EvSiteViews.tsx:530-532` |
| Cold | No incident recorded | §1.5 | FE `coldSiteViews.tsx:622` |
| Cold | No accepted transfer to backup report for this chain | No record of switching to backup power | FE `coldSiteViews.tsx:556` |
| Cold | Not observed: transfer to backup. | No record of switching to backup power. | BE `analytics/cold_site_reads.py` |
| Cold | The steps above are based on the selected accepted records. Missing steps remain unobserved. | These steps come from the recorded readings. A step with no reading is marked Missing. | FE |
| Cold | Automatic generator start failed in the accepted record (Next step, Needs attention) | Backup generator did not start on its own | BE `cold_site_reads.py:73` |
| Cold | Not priced | Not priced yet | FE |
| Cold | Consequence basis: at least 19.5 °C·min; upper bound not established | Above the limit by at least 19.5 °C·min (degrees × minutes); the full extent is not known yet | FE `coldSiteViews.tsx:774`, `coldFormat.ts:73` |
| Cold | Potential product exposure. Stock value and product response are not declared, so no loss figure is stated. | Stock may be at risk. No stock value has been entered, so no loss figure is shown. | FE |
| Cold/EV | compressor-1 · COMPRESSOR / battery · BATTERY | Compressor / Battery | BE asset label rule |
| EV | Registered test reports; not physical charger observations | Example charger reports, not from physical chargers | FE `EvSiteViews.tsx:308` |
| EV | known at 27 Oct 09:00 UTC | as of 27 Oct, 09:00 | FE `EvAssessmentViews.tsx:130`, `EvSiteViews.tsx:335` |
| EV | Opens configuration at window end; evidence cutoff is not carried | Opens the site layout as it was at the end of this period | FE `EvSiteViews.tsx:536` |
| EV | REC <uuid> / F <id> on the timeline | Charger report / Finding (ids in a `title` attribute and Technical details) | FE `EvAssessmentViews.tsx:806,871`, `EvSiteViews.tsx:505` |
| EV | Investigate connector Connector c1 | Investigate Connector c1 | BE `ev.py:220` (§1.3) |
| EV | Energy cost per km needs odometer readings; a tariff estimate exists in Financials | §1.6 | BE `catalogue.py:72` |
| Maintenance | Overdue: Not assessed · No due evaluator; Due status not assessed | §1.4 | FE `GlobalPreventive.tsx:46,171-180` |
| Maintenance | No accepted-evidence link | No linked evidence yet | FE `GlobalPreventive.tsx:185` |
| Maintenance | Nothing verified by this plan | No completed work confirmed yet | FE `:127` |
| Maintenance | Listed by the time each plan was first recorded | Listed in the order plans were added | FE `:53` |
| Maintenance | Completing a draft plan here is unavailable | Plans can't be completed from this page yet | FE `:49` |
| Maintenance/Portfolio | Source unverified | Source not checked | FE `EstatePortfolio.tsx:110`, `findingIndex.tsx:125` and 4 more |
| WR | No work-case outcome evaluator is available | Whether this work fixed the problem is not checked yet | FE `WorkRequestOverview.tsx:24` |
| WR/work lists | As known at 1 Nov 2026 02:09:11 UTC · Reload | Updated 1 Nov 2026, 02:09 · Reload | FE `globalWorkParts.tsx:224`, `workRequestShared.tsx:272` |
| WR | Witnessed failure requires inspection. | `{title}.` | data (PA-3) |
| All | ACT-000001, WR-000006, INC-000005, PM-000013 | ACT-001, WR-006, INC-005, PM-013 | display code rule |

Strings that stay as they are: "Not available yet" entries (owner rule); "Assets/Settings · Not available yet" in the rail;
the objective sentences; and "Review recommendation · Not available yet".

Any visible string found by the strict capture gate (PB-0) that is not in this table is rewritten by the builder
using these patterns:
- plain verb-first wording;
- "not available yet" for missing data;
- no "Finding/Action" capitals in running text.

The builder lists every such string in its packet as `old → new` for review. Reviewers accept or return them; this is the
only builder copy latitude.

---

## 4. P-01/P-02 links and P-03 overlap

**P-01/P-02** (`tools/demo_combined.py:433-460`):
- Move URL building into a pure function `story_links(story: dict, days: list[dict], kobo: dict | None, web: int) -> list[tuple[str, str]]`.
  `links()` and `serve` print its output. The rows are:
  - Portfolio week: `/portfolio?from={S-6d}&to={S+1d}`.
  - Findings week: `/findings?from={S-6d}&to={S+1d}`.
  - Maintenance month: `/maintenance/preventive?from={S-28d}&to={S+3d}` and `/maintenance?from={S-28d}&to={S+3d}`.
  - Per story day:
    - kobo: `/sites/KOBO-001?date={day}`;
    - cold: `/sites/COLD-LAB-001?from={start}&to={end}`;
    - ev: `/sites/EV-LAB-001/ev?from={start}&to={end}`.
    - `start`/`end` come from `days.json`, which are the event windows.
  - Kobo Overview day S: `/sites/KOBO-001?date={S_date}`.
  - Verification: `/sites/KOBO-001/actions/{action}/verification`. The Finding link is unchanged.
  - Remove every `/outcomes` and `/overview` form.
- Test: `backend/tests/test_demo_combined_links.py`, pure with no DB, using a 3-day synthetic story. It asserts every URL
  starts with one of the forms above and that none contains `/outcomes` or `/overview`.

**P-03** (`frontend/src/estate/estatePortfolio.css`):
- add `.estate-portfolio .portfolio-findings td[data-portfolio-confidence] .badge{white-space:normal;max-width:100%;display:inline-block;overflow-wrap:anywhere}`;
- the copy change "Supported, coherent source" → "Well supported" shortens the chip.

Acceptance: in `portfolio-week-1440.png` no Confidence chip box intersects the Action cell. The PB-1 capture measures it:
the chip `getBoundingClientRect().right` ≤ its `td` right on every row.

---

## 5. Slices, lanes and order

Two lanes with no shared source files. Both lanes append to `.agent/mock-departure-register.md` and `.ai/CODE_STATE.md`
in their own section ("POLISH <slice>"). Register ids are reserved per slice:

| Slice | Register ids |
|---|---|
| PA-1 | R635-R639 |
| PA-2 | R640-R644 |
| PA-3 | R645-R649 |
| PB-0/PB-1 | R650-R654 |
| PB-2 | R655-R659 |
| PB-3 | R660-R664 |
| PC | R665+ |

There is one branch and worktree per slice (`task/POLISH-<id>`). Each slice merges on review ACCEPT, following the
walkthroughs-deferred rule.

**Captures before PA-3.** Serve the slice's code against `assetops_demo3_full_test`. No migration is in this round.
Use `DEMOB_ONLY` for the slice's keys.

**Captures after PA-3.** Use the rebuilt `assetops_polish_full_test`.

### Lane A: backend and producers

**PA-1 · Board truth (5 units).**
- Files: `backend/assetops_backend/site_outcomes/{mini,board,ev}.py`, `outcomes/catalogue.py`, the history ordering module from OUT-E L3, and their tests.
- Work:
  - P-06 backend (§1.1): 1 unit.
  - P-11 (§1.6): 1 unit.
  - P-12 with the Grow pre-flight (§1.7): 1.5 units.
  - `ev.py:220` connector wording: 0.25 unit.
  - OUT-E L4 ruling (§6, R-L4): `board.py` `cost_line` shows a modelled change only when `verification_state == "VERIFIED"`. A final INEFFECTIVE or other non-VERIFIED state with MODELLED_IMPROVEMENT returns the new `COST_NOT_CREDITED = "The trial did not fix the problem, so no cost change is credited to it"`. Add a pinning test. 0.75 unit.
  - OUT-E L3: `history()` orders by `revision_no`. 0.25 unit.
  - Total 4.75, rounded to 5.
- Tests:
  - pytest on the touched modules' unit tests;
  - the board/outcome Postgres tests that pin changed strings (`-k "board or outcome or mini or ev_site"`);
  - new tests:
    - zero-amount headline;
    - EV unpriced Optimize sentence;
    - S+1 MG-7 settled with zero intervals (a pure compose test with a COMPLETE zero-interval overview body);
    - INEFFECTIVE + MODELLED_IMPROVEMENT gives COST_NOT_CREDITED.
- Captures: `kobo-board-S`, `kobo-board-S1` and `ev-board-fault` at 1440/390.
- Guards: check-all 12/12 (11/11 before PB-0 lands).

**PA-2 · Server copy, codes and plan due (6 units).**
- Files: `outcomes/display_code.py` (new), `outcomes/plan_due.py` (new), `outcomes/warnings.py`, `site_outcomes/visits.py`,
  `site_outcomes/cold.py`, `analytics/cold_site_reads.py`, `estate/{index,placement,portfolio,evidence_money}.py`,
  `work/{global_index,site_index,domain_action_index}.py`, the global preventive read, `analytics/finding_episode.py` (TITLES), and tests.
- Work:
  - `display_code` in server sentences: 1 unit.
  - `Finding {id[:8]}` labels replaced by titles: 1 unit.
  - Asset label rule: 1 unit.
  - Server strings from §3.1 marked BE, plus UTC-suffix removal in server sentences on capture screens: 1 unit.
  - `plan_due` helper and preventive counts (§1.4 backend): 1.5 units.
  - Finding titles: 0.5 unit.
- Tests:
  - new pure tests for `display_code` and `plan_due_state`, the latter including the boundary `due_at == to` (not overdue) and run-hours;
  - preventive read Postgres test for the counts across pages;
  - the existing warning tests pass unchanged;
  - mechanical updates to tests pinning the old strings.
- Scoped regression: `backend/tests -k "estate or portfolio or work or warning or outcome or finding_episode"`.
- Captures: `portfolio-week`, `findings-*`, `maintenance-preventive` and `wr-overview` (wording only; UI counts come in PB-3).
- Guards: check-all.

**PA-3 · Producers, links and rebuild (5 units).** Starts after PA-1 and PA-2 merge.
- Files: `tools/demo_combined*.py`, `tools/w502_cold_work_walkthrough.py` (narrative kwarg passthrough only), `sites/cold_lab.py`, `sites/ev_lab.py`, `backend/tests/test_demo_combined_links.py` (new).
- Work:
  - P-01/P-02 `story_links` and test: 1 unit.
  - `demo_combined_ev` slip (§1.3): 0.25 unit.
  - Narratives: 0.75 unit.
  - Lab names (install kwarg and producer): 1 unit.
  - DEMO-A L1/L2 (`tools/demo_combined_finish.py:142-149`): add back the "Reliable service and battery and generator life" assertion, and restrict "Action on the Cost row" to `issues` + `in_hand`. Also L3 (stale R535/R552 and CODE_STATE text). 0.5 unit.
  - Full `prepare` into the new DB `assetops_polish_full_test`, work `var/polish_full`, and its acceptance (`check.json` CO rows all pass): 1.5 units.
- Stop rule: if `prepare` exceeds 2× 800 s, or any CO row fails, stop and report.
- Tests:
  - `test_demo_combined_links.py`;
  - `test_demo_combined_postgres.py`;
  - cold/EV lab install tests with and without `display_name`.
- Captures: all 14 keys from the rebuilt DB (non-strict; PC runs the strict gate).
- Guards: check-all.

### Lane B: frontend and tools

**PB-0 · Capture gate and label guard (3 units).** Runs first, alongside PA-1.
- Files: `tools/demo-combined-evidence.mjs`, `tools/checks/mock-deviation-labels.mjs` and `test_mock_deviation_labels.mjs` (new), `tools/check-all.ps1`, `tools/checks/evidence-checks.mjs` (OUT-D L1).
- Work:
  - Strict gate: `DEMOB_STRICT=1` exits 1 on any vocabulary hit. The scan excludes text inside `[data-technical-details]`,
    `[data-time-zone-note]` and `[data-vocabulary-exempt]`, and skips the `-open` stress capture except for "MOCK DEVIATION". 1 unit.
  - VOCAB:
    - add `PM|REC` to the code regex and require `-0{3,}` (so `ACT-001` passes and `ACT-000001` fails);
    - add `\bUTC\b`, `\bFinding [0-9a-f]{8}\b`, `\b(?:replay|charging) lab\b`i and `\b[a-z]+(?:_[a-z]+)+\b`;
    - load the T028 and w1 terms from `frontend/src/test/productVocabulary.json` (word-bounded, case-insensitive).
  - `DEMOB_REVIEW_LABELS=1` opens `/?review=labels` once per tab before capturing.
  - Settle waits for no `[data-repeat-check="loading"]` and no `[aria-busy="true"]` in `<main>`.
  - Label guard (§2 a-c) with its 4 fixtures, registered as guard 12 in `check-all.ps1`: 1 unit.
  - OUT-D L1: the ready regex `/^Loading\b/` stops matching "Loading and door records". Use `/^Loading(?:…|\.\.\.)?$/m` on whole lines, plus `aria-busy`. 0.5 unit.
  - Packet: 0.5 unit.
- Tests:
  - `node --test tools/checks/test_mock_deviation_labels.mjs` and `tools/checks/test_evidence_checks.mjs`;
  - `node --check` on the tool;
  - a strict run against the current kept build is **expected to fail**. Record its hit count as the baseline.
- Guards: check-all 12/12.

**PB-1 · Shell, labels, time, Portfolio overlap (6 units).** Starts after PB-0.
- Files: `frontend/src/main.tsx`, `ui/reviewLabels.ts` (new), `ui/mock-deviation.css`, `ui/time.ts` (new), `ui/TimeZoneNote.tsx` (new),
  `ui/V69Layout.tsx`, `shell/OperatorShellLayout.tsx`, `shell/simulatorLabRoutes.tsx`, `estate/estateShared.tsx`,
  `estate/estatePortfolio.css`, the 10 formatter bodies listed in §3, and `.agent/mock-departure-register.md` (the §2 rule text).
- Work:
  - P-04 (§2): 1 unit.
  - P-03: 0.5 unit.
  - Banner and header badge (§6 D-1): 0.75 unit.
  - Rail label: 0.25 unit.
  - `time.ts`, `TimeZoneNote`, formatter delegation and `EstateDateBar` (window, cutoff text, cutoff disclosure): 2.5 units.
  - Tests: 1 unit.
- Tests:
  - new `reviewLabels.test.ts` and `time.test.ts` (same-day range, cross-day range, midnight, invalid input gives "Time not available yet");
  - vitest scoped to `estate`, `shell`, `ui`, `work/globalWork*` and `sites/cold*`/`Ev*` formatter users;
  - `tools/w1-ux-07-rail-evidence.mjs` updated for "Simulator Lab".
- Captures (strict on these keys): `portfolio-week` (P-03 rectangle check) and `findings-all`.
- Guards: check-all 12/12; navigation truthfulness must stay green (rail rename).

**PB-2 · Kobo board, verification, display codes (6 units).** Starts after PB-1.
- Files: `sites/SiteWindowOverview.tsx`, `sites/overviewSlots.tsx`, `sites/OverviewFindingList.tsx`, `sites/dispatchWords.ts`,
  `sites/sourceProvenance.tsx`, `sites/SiteActionVerification.tsx`, `sites/actionPresentation.tsx`, `sites/ClaimLabel.tsx`,
  `sites/OutcomeBoard.tsx`, `ui/displayCode.ts` (new), and their tests.
- Work:
  - Kobo rows of §3.1: 2 units.
  - P-06 money panel (§1.1): 0.5 unit.
  - Technical details tagging and renames on Kobo and verification: 1 unit.
  - Verification rows: 0.5 unit.
  - `displayCode` and its use across all render sites found by the strict scan, including cold/EV/work files. The code
    call is the only change made in files owned by PB-3, so merge PB-2 before PB-3 starts: 1.5 units.
  - OUT-A L1 "Candidate" in the Optimize card detail, if still visible: 0.5 unit.
- Tests:
  - vitest `sites/` mini, overview and verification suites;
  - the 3 known `w1f4VerificationStructure.test.tsx` failures on main (lows log 2026-10-29): fix them if they touch these files, otherwise list them.
- Captures (strict): `kobo-board-S`, `kobo-board-S1` and `kobo-verification`; `kobo-board-S-open` (strict except inside Technical details).
- Guards: check-all.

**PB-3 · Estate, cold/EV, work: copy and P-07/P-09/P-10 (6 units).** Starts after PB-2, and after PA-2 for P-09.
- Files: `estate/EstatePortfolio.tsx`, `estate/portfolioWords.ts`, `estate/findingIndex.tsx`, `estate/actionIndex.tsx`,
  `estate/estateFinancialsWords.ts`, `sites/coldSiteViews.tsx`, `sites/coldAssessmentWords.ts`, `sites/coldFormat.ts` (copy only),
  `sites/EvSiteViews.tsx`, `sites/EvAssessmentViews.tsx`, `sites/SiteFindingIndex.tsx` (IDX-GAPS L2: "those days" → "the unchecked days"),
  `work/GlobalPreventive.tsx`, `work/WorkRequestOverview.tsx`, `work/workRequestShared.tsx`, `work/globalWorkParts.tsx`, and their tests.
- Work:
  - Estate rows of §3.1: 1.5 units.
  - Cold/EV rows: 1.5 units.
  - P-10 (§1.5): 0.5 unit.
  - P-07 (§1.2), including step 0: 0.75 unit.
  - P-09 UI (§1.4): 1 unit.
  - Work rows: 0.75 unit.
- Tests:
  - vitest `estate/`, `work/`, `sites/cold*` and `sites/Ev*`;
  - new tests: Preventive cards from summary counts, including 0 overdue; P-10 with incident, without incident, and with the board absent; `RepeatVisitNotice` in its 4 states.
- Captures (strict): `portfolio-week`, `findings-*`, `cold-board-*`, `ev-board-fault`, `maintenance-preventive` and `wr-overview` (the notice is visible).
- Guards: check-all.

### PC · Final gate (3 units). Runs after both lanes merge.
- Serve main against `assetops_polish_full_test`.
- Run the full 28-capture recapture with `DEMOB_STRICT=1` (`tools/demo-combined-evidence.mjs capture`, then mock-ids
  and compare per the DEMO-B runbook step 5): 0 hits and 28/28 settled.
- Run one review-mode set (`DEMOB_REVIEW_LABELS=1 DEMOB_ONLY=wr-overview,kobo-board-S`): labels visible.
- Run the v70 compare. Panel structure must still match: the same panel counts as DEMO-B's `compare-run.log`.
- Run full frontend and backend suites, with the machine idle (preflight-and-quiet-suites rule), plus check-all 12/12.
- Reconcile the register: close R626, R630, R111 (demo) and P-B3-3; add the §7 rows.
- Update the runbook in a new `.agent/POLISH-runbook.md`: new DB and work dir, `story_links` output, the P-08 line, and review mode.
- Reviewer: one whole-diff review of the round, by a fresh Claude reviewer.

**Order and size.**

| Order | Lane A | Lane B |
|---|---|---|
| 1 | PA-1 (5) | PB-0 (3) |
| 2 | PA-2 (6) | PB-1 (6) |
| 3 | PA-3 (5, rebuild) | PB-2 (6) |
| 4 | – | PB-3 (6; needs PA-2 merged) |
| 5 | PC (3), after all merge | |

Total is 40 units, about 10 builder-days, about 5-6 elapsed days with two lanes.

The demo-critical path, in case the owner wants a shorter cut: PB-0, PB-1, PB-2, PB-3 and PA-1, PA-2, PA-3, with
nothing dropped. If time must be cut, defer only the time-format consolidation beyond the 14 capture screens. The
strict gate covers just those screens.

---

## 6. Rulings made here and owner questions

The Architect decided these under the delegated-decision rule. Each is logged for the owner and confirmed at the walkthrough:
- **D-1, "Demonstration data" banner (DEMO-COMBINED §9 Q3): yes.**
  - A one-line, quiet, app-wide banner under the topbar: "Demonstration · example sites and records prepared for this walkthrough".
    It is neutral tone, 12 px, not dismissible, with `role="note"`.
  - The per-Site badge "Demonstration data · {code}" becomes "Example data".
  - This is a D2 row, R651. It is cheap (0.75 unit), and it lets the work records stay unmarked honestly.
- **D-2, OUT-E L4: an INEFFECTIVE trial never shows a modelled money line.** The Cost row then reads "The trial did not fix
  the problem, so no cost change is credited to it" (PA-1). This matches Assure (`mini.py:697`, VERIFIED only) and the
  "no change credited to the trial" rule.
- **D-3, P-08: no backdating.** The Depot Action stays dated at build time. It shows on Work › Actions, and the board register row and runbook line explain it.
- **D-4, times:** one "All times UTC" note per page, with no per-time suffix. (GOV.UK date and time guidance; NN/g redundancy heuristic.)
- **D-5, Lab Site names:** use the mock names, "GreenHarvest Cold Room" and "Depot Charging Hub", in the demo build only.

**Owner question (one):**
- **Q1. Kobo's fuel cost reads zero.**
  - On the overuse days the generator was switched on but delivered no power, because solar and the battery carried the
    load. The cost model counts only fuel for power delivered, so the honest figure is zero.
  - For this demo the screen will say "No fuel cost estimated: the generator was on but delivered no measured power".
  - **Recommendation:** keep that for the walkthrough. Afterwards, decide whether to add an idle-fuel rate to the cost
    model, entered by the customer like the diesel price, so a running-but-idle generator has a cost. This is about 1.5 d plus a rebuild.
  - Changing the simulated generator so it carries load would be tuning the story, so it is not offered.

---

## 7. Register rows to add (by slice)

| Row | Slice | Content |
|---|---|---|
| R635 | PA-1 | EV Optimize sentence conditional on a priced tariff (D4; cites R628, R263) |
| R636 | PA-1 | Only if the P-12 pre-flight finds Grow S+1 has a different cause |
| R640 | PA-2 | Display codes (3-digit) and asset type words, not stored codes (D2) |
| R641 | PA-2 | Preventive due counts (closes P-B3-3; D1 if the mock's counts differ in form) |
| R645 | PA-3 | §1.3 |
| R646 | PA-3 | Demo Lab Site names override (closes R111 for the demo build) |
| R650 | PB-1 | Times: "All times UTC" page note (D2) |
| R651 | PB-1 | Demonstration banner (D2) |
| R652 | PB-1 | Evidence cutoff picker in a closed disclosure (D2) |
| R655 | PB-2 | **Plain-language client copy (POLISH):** one row listing every §3.1 string that replaces mock wording (for example "Bounded money consequence" → "Possible cost"); D2, owner approves at the walkthrough |
| R656 | PB-2 | Technical details disclosures holding ids (D2) |
| R660 | PB-3 | Cold incident line (closes the P-10 part of the "What happened" departure) |
| R660+ | PB-3 | Further rows as needed |

Close rows R626 (PA-1 + PB-2) and R630 (PB-3).

## 8. Not in this round (from the Lows logs)

These stay in the Lows log:
- TEL-* Lows;
- the test-pipeline DB-sharing proposal;
- the w301 order-dependent Postgres failures;
- the check-architecture rule 8 non-determinism;
- FIX-01 L2;
- DEMO-A0 L1;
- IDX-GAPS L1/L3;
- FIX-S4 Lows.

None is client-visible.
