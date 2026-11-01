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

---

## Addendum 1 (2026-11-01): PB-0 pre-flight rulings

**Q1: option (a).** PB-0 lands the whole P-04 mechanism, so guard 12 passes in full in the slice that adds it:
- the hide rule in `frontend/src/ui/mock-deviation.css`;
- `frontend/src/ui/reviewLabels.ts` with `src/ui/__tests__/reviewLabels.test.ts` and `mockDeviationStyle.test.ts`;
- `main.tsx` calls `reviewLabels` first and imports `mock-deviation.css` app-wide. This is required: the `MockDeviation`
  component in `globalWorkParts` (`.global-work-deviation`) does not load the file today;
- the register rule sentence (§2 text, verbatim).

PB-0 becomes **3.5 units**. In PB-1, the P-04 unit becomes 0.25 unit of verification only:
- one review-mode capture (`DEMOB_REVIEW_LABELS=1 DEMOB_ONLY=kobo-board-S`) at 390 shows the R453 label, and at 1440 the label stays hidden by its width rule;
- the client-mode `portfolio-week` and `findings-all` captures have zero "MOCK DEVIATION" hits.

PB-1 becomes **5.25 units**. The freed 0.75 unit is held as slack for the time consolidation. Register ids are unchanged:
PB-0 and PB-1 share R650-R654.

**M1: confirmed.** The file is `tools/evidence-checks.mjs`. Export a pure ready predicate from it, test it in
`tools/checks/test_evidence_checks.mjs`, and call it from `settle()` in `demo-combined-evidence.mjs`. The §5 path was wrong.

**M2: confirmed.** Use the whole-line regex. Fixtures must cover:
- "Loading the site's overview." counts as not settled;
- "Loading and door records" counts as settled;
- "Loading…" counts as not settled.

Keep the `aria-busy` and `[data-repeat-check="loading"]` waits; the latter is inert until PB-3 adds the attribute, which is expected.

**M3: confirmed, with two conditions.**
- Excluding `w1.codes` is accepted. Upper-case codes are still caught by the existing enum-code regex and the
  zero-padded code regex.
- Gloss stripping must use only the allowed phrases and glosses already in `productVocabulary.json`, with no
  tool-local allow-list. Each stripped phrase is listed in the PB-0 packet.

The rest of M3 stands as planned: "MOCK DEVIATION" is always scanned on the full `<main>` text, and with
`DEMOB_REVIEW_LABELS=1` hits are recorded but not strict.

---

## Addendum 2 (2026-11-01): PA-1 pre-flight rulings (these apply to every lane)

**Q-A (OUT-E L3): accepted.** `history()` orders by `ORDER BY recorded_at, revision_no, id`. `revision_no` is unique
only within one verification outcome, so `recorded_at` leads and `id` makes the order total. The pinning test needs
two outcomes for one Action, with interleaved revisions.

**Q-B: one capture rule for all lanes (option 3, serialised).**
- Serving the kept DB is allowed. "Read-only" means no manual writes, no `prepare` and no `add-day` against it.
  The serve loop's ticks only refresh projections and comparisons, which is what the walkthrough itself does and what
  DEMO-B did. No migration lands in this round, so slice code can safely tick it.
- **Only one serve may run against a DB at a time** (two schedulers on one DB is the real risk). Lanes take a
  capture slot from the coordinator. Each run, in order:
  1. Start `demo_combined.py … serve` from the slice worktree with `--db assetops_demo3_full_test --work <AssetOpsV1-demo3>\var\demo3_full`.
  2. Start Vite from the same worktree.
  3. Wait for the first `performance:` line.
  4. Capture with `DEMOB_ONLY`.
  5. Stop both by PID and confirm ports 8990 and 5490 are free.
  6. Release the slot.
- No template copies (option 1). The I/O cost and the risk to the file store are not worth it for re-capture.
- No deferral (option 2). Each slice proves its own screens.
- After PA-3 merges, the same rule applies with `assetops_polish_full_test` and `var/polish_full`. From then on,
  `assetops_demo3_full_test` is only the walkthrough fallback.

**Q-C: accepted.** Leave EV-2 `missing_records` (`catalogue.py:53-54`) unchanged and note in the packet that nothing
renders it while the row sentence takes precedence. Drop the §1.6 clause "the same condition where EV-2
`missing_records` is shown".

**Pre-flight results: accepted.**
- **Grow (§1.7 pre-flight).** Kobo Grow is Unknown on both S and S+1 because MG-1 cannot be judged without sales
  records (`mini.py:457`, OBJECTIVE_NOT_JUDGED). This is a different cause from the readiness rule. Add R636 (D4)
  with that reason; Grow is not changed.
- **MG-7 settled rule.** Accepted as the builder planned it: `assessment.claim_level == "COMPLETE"`, zero dispatch
  intervals, and readiness exactly `UNKNOWN`. The chip then reads "No objective declared", and the Readings line reads
  "No generator run to check on this day · readings complete".

---

## Addendum 3 (2026-11-01): capture rule re-ruled (supersedes Addendum 2 Q-B)

The PA-1 implementer verified that Addendum 2 Q-B cannot work:
- `Demo.__init__` only accepts its own `var/demo3*` work dir;
- serve runs uvicorn and ticks from the private tree `<work>\tree`, which is frozen at DEMO-A `e2df244c2`;
- slice backend code served directly against the kept DB gets 409 AWAITING_EVIDENCE_MIGRATION, because of the file-store root binding.

**Frontend slices (PB-0, PB-1, PB-2, and the frontend part of PB-3): confirmed as the coordinator set it.**
- Run serve from `AssetOpsV1-demo3`, unchanged, against its own DB and work dir. Run Vite from the slice worktree with `ASSETOPS_API_PORT=8990`.
- One serve at a time, as in Addendum 2: the coordinator holds the slot, and processes are stopped by PID when done.
- Captures therefore show the slice's frontend over the DEMO-A backend. In the strict gate (PB-0 tool), a hit whose
  source is server text owned by PA-1 or PA-2 (§3.1 "BE" rows, display codes inside server sentences, Finding titles,
  asset labels) is recorded as `awaiting PA-x` in the packet, not as a slice failure. Any frontend-sourced hit fails the slice.

**Backend slices (PA-1, PA-2): option (a).**
- Captures are deferred to the PA-3 rebuild (`assetops_polish_full_test`, whose private tree contains PA-1 and PA-2).
  Each packet records "captures: deferred to PA-3 (Addendum 3)".
- Options (b) and (c) are refused:
  - (b) the overlay edits the kept walkthrough build's private tree; one missed restore corrupts the fallback;
  - (c) is expected to hit the same store-root refusal.
- Screen proof in place of captures: each changed board or read sentence and value is pinned by a compose- or
  read-level test that asserts the exact output (for example the PA-1 zero-amount headline, the EV unpriced sentence,
  the MG-7 chip and Readings line, and COST_NOT_CREDITED). These tests are the review evidence until PA-3.

**PA-3** captures all 14 keys from the rebuild, as before. Its packet adds a "PA-1/PA-2 screen check" list: each
capture-visible change from §1.1, §1.6, §1.7, §1.3 (connector wording), §1.4 (backend counts present in the read) and
§3.1 "BE" rows, each with the capture file where it shows. A miss there goes back to the owning slice as a fix round.

**PB-3 (touches the frontend only; it consumes PA-2's preventive counts):**
- Its non-P-09 captures follow the frontend rule above.
- P-09 is proven by vitest with the PA-2 read shape. Its `maintenance-preventive` capture comes from the PA-3 rebuild
  when PA-3 has merged before PB-3 is reviewed; otherwise it is deferred to PC.
- P-07 step 0 (§1.2): the GET runs against the demo3 serve. The DEMO-A backend has the same warning logic, so the check is valid there.

**PC** is unchanged: the strict 28-capture run on merged main, served from the PA-3 rebuild.

---

## Addendum 4 (2026-11-01): PA-1 sign-off items

The product vocabulary guard bans "run"/"running". The guard stays as it is: copy must avoid run, ran and running.

1. **MG-7 Readings line: accepted.** The text is "Generator not used on this day, so nothing to check · readings complete".
2. **Finding titles (§3, PA-2) are replaced:**
   - SUPPORTED: "Generator may have been on longer than needed"
   - UNCONFIRMED: "Extra generator time not confirmed by the latest check"
   - NO_LONGER_SUPPORTED: "Extra generator time no longer supported by the latest check"

   These other §3/§1 strings use "run" and change with them, in their owning slice:
   - §3.1 Kobo "Checked: 1 generator run, from 13 measured inputs" becomes "Checked: 1 period of generator use, from 13
     measured inputs". The zero case becomes "Checked: generator not used on this day, from 13 measured inputs". (PB-2)
   - §3.1 "When the generator ran and when readings arrived" becomes "When the generator was on and when readings arrived". (PB-2)
   - §1.4 "{n} plan(s) run on running hours; not checked here yet" becomes "{n} plan(s) based on hours of use; not checked here yet". (PB-3)

   For any other guard-banned word in a ruled string, the builder may swap in the nearest plain synonym without
   asking, and must list the swap in the packet.
3. **S+1 readiness chip changes in a PA-1 fix round before merge.** It does not wait for a later slice, because the same
   line would otherwise say "Unknown" and "complete" at once.
   - In the MG-7 settled case only (the three Addendum 2 conditions), the Readings contributor's chip is the chip
     `mini.py` gives FULL readiness. Any readiness word the line or chip shows is the FULL word, never "Unknown".
   - The shared readiness value and `reduce_day` are unchanged.
   - Pin it in the existing settled-case compose test: assert the chip is not UNKNOWN_CHIP and the text has no "Unknown".

---

## Addendum 5 (2026-11-01): PB-0 review M1 (exempt regions and the id checks)

**Accepted as the reviewer proposes. This corrects §5 PB-0 and Addendum 1.**

- **Identifier checks run everywhere.** These checks run on all visible `<main>` text, including inside
  `[data-vocabulary-exempt]` and `[data-time-zone-note]`:
  - UUID;
  - `Finding [0-9a-f]{8}`;
  - zero-padded record code;
  - UPPER_SNAKE enum code;
  - raw ISO timestamp.
- **Only `[data-technical-details]` hides ids.** It is the only region whose text is removed before the id checks,
  for the strict gate and for the `-open` stress capture alike.
- **Exemptions apply to product terms only.**
  - `data-vocabulary-exempt` exempts only the product-term checks (T028/w1 terms, Lab names, developer words).
  - `data-time-zone-note` exempts only `\bUTC\b`.
  - "MOCK DEVIATION" is never exempt.
- **Exempt regions are recorded, not dropped.** Every hit found inside an exempt or Technical-details region goes into
  `captures.json` under `exempt_hits[]`, with `{kind, match, region: "<attribute>=<value>", context}`. These hits never fail the
  strict gate (except the id kinds above, outside Technical details).
  - The packet and the PC review list the `exempt_hits` counts per capture. A reviewer seeing a new exempt value, or a
    jump in exempt hits, treats it as a finding.
  - New `data-vocabulary-exempt` values are allowed only for genuine source quotations, never for Site names, asset
    names or record codes. `data-vocabulary-exempt="lab"` or similar on Site names is refused; Lab names are fixed
    by PA-3's data change.
- **Baseline.**
  - Recount after the change.
  - The 3 EV `REC <uuid>` hits per width (`EvAssessmentViews.tsx:806,871`) are frontend hits owned by PB-3 (§3.1 EV row).
  - `SiteAction.tsx:1393,1410,1422` (codes and revision UUIDs) and `ColdAssessmentViews.tsx:237` are added to the
    owning slices:
    - `SiteAction.tsx` goes to PB-2 (Technical details tagging, display code);
    - `ColdAssessmentViews.tsx` goes to PB-3.
    - If either is not on a capture screen, the vitest product-vocabulary check for that view covers it.
- **Addendum 1 / L1-L3 folds: noted.** The baseline split is 21 frontend / 61 awaiting per width, and the Lab-name
  hits are marked as awaiting PA-3.
- **Unit size.** PB-0 stays at 3.5 units; this is a fix round.

---

## Addendum 6 (2026-11-01): PA-2 pre-flight rulings

**Split.** With the files added below, PA-2 exceeds 6 units, so it becomes two slices in the same lane. Both use
register ids R640-R644.
- **PA-2a, server copy, codes and titles (about 4.5 units).** Q1, Q3, Q5, Q6, Q8, Q9, the "Recommendation not
  accepted" maps, and the §3.1 BE strings.
- **PA-2b, asset labels and plan due (about 3.5 units).** Q2, Q4, and the §1.4 backend.
- Order: PA-2a, then PA-2b, then PA-3. PB-3 waits for PA-2b, not PA-2a.

**Q1: accepted.** Edit the 12 title strings in `backend/tests/fixtures/w3/w301-estate-golden.json` directly. They are
text, not numbers, and the stop rule existed to catch exactly this. Run `test_w301_estate_golden_postgres.py` once,
when the machine is idle (quiet-suites rule). Update `test_idx_gaps_board.py:97-99` mechanically. MERGED stays unchanged.
`frontend/src/.../findingWords.ts:14-36` goes to PB-2: align its title words with the Addendum 4 titles there.

**Q2: accepted.**
- Add a top-level `summary: {overdue_count, due_soon_count, not_assessed_count}` and a per-row `due_state` to
  `GET /api/work/preventive` only. `state_counts` stays null.
- `plan_due_state` takes the timestamptz `next_due_at`, with the boundary as the implementer settled it.
- PB-3's validator must accept the new keys. Until PB-3, the existing frontend validator must not reject them. If it
  rejects unknown keys, PA-2b relaxes it for exactly these keys. That is the only frontend change allowed in lane A,
  and it is listed in the packet.

**Q3: accepted, with a wording correction.**
- The extra reads are accepted: `fr.title` in `_IndexTx.finding_revisions`, the `finding_revision` join in
  `_ReadTx.revision_links`, and a private `recurs_after_title` through `coverage.py` and `index.py`.
- RECURRED text: "Happened again after an earlier occurrence ({earlier title})". Without a title, it is "Happened
  again after an earlier occurrence".

**Q4: accepted.**
- Rewrite `asset_label` in place to the plain form, and add a wire `asset_type`. `cold.py` and `visits.py` read
  `asset_type` and no longer parse the label.
- `asset_code` is appended only when the Site has more than one non-retired asset of that type (the scalar subqueries).
- Unmapped types use the capitalised type word.
- Generators: GENERATOR shows as "Backup generator" on COLDCHAIN Sites and "Generator" on mini and EV Sites.
- In lane B, PB-3 replaces the two frontend parsers (`globalWorkParts.tsx:123`, `siteWorkCases.tsx:256`) with
  `asset_type` and `assetWords`. Add `siteWorkCases.tsx` to PB-3's files. Until then, their raw-label fallback shows
  the new plain label, which is acceptable.

**Q5: accepted.** At read time in `cold_site_reads`, rewrite the TRANSFER observation to "No record of switching to
backup power." and align estate's `COLD_OBSERVATION_WORDS` TRANSFER entry to the same words. The stored analytics are unchanged.

**Q6: accepted.**
- Change only the read-side constants in `board.py`, as the implementer proposed. `trial_fuel_comparison.LABEL` stays as stored.
- **Yes for `mini.py:79` `VERIFIED_WITH_COST`:** keep its verdict and code prefix, and use the same cost clause:
  `…: estimated effect of the trial (not money saved): {amount} {currency} less supply cost per kWh`.

**Q7: D-4 is revised for the whole round.**
- **Clock times stay in UTC.** Instants come from the DTOs without a Site offset (R86), so they are shown in UTC
  with no per-time suffix.
- **Calendar dates stay on the Site's own date.** That covers plan due dates, visit days and warning days: the
  server already computes them in the Site's zone (`warnings.day_text`, `visits._local_date`), and that is unchanged.
  Where the frontend formats a due date itself (Preventive `next_due_at`), it uses the Site zone from `siteTime.ts`
  when it is declared, and UTC otherwise.
- **The page note becomes "Times in UTC".** Pages that also list due dates (Preventive, Maintenance, the work request
  pages) say "Times in UTC · due dates in each site's local date". PB-1 builds `TimeZoneNote` with these two variants.
- `mini.py:39` `UTC_SUFFIX` stays as it is: it applies only to Sites with no zone, and none appears in the demo.

**Q8: accepted.** Apply `display_code` to every visible server label listed (`warnings.py:195,204`, `board.py`
`_item_text`/`_action_name`, `mini.py:75-79,725`, `cold.py:313,354`). The stored and wire `code` fields stay as stored.

**Q9: in scope for PA-2a.** `Action {aid[:8]}` (`work/site_index.py:208,215`) becomes the Action's display code when it
has a code (for example "ACT-003"), and "Action" otherwise.

**Q10: confirmed.** The extra files are in scope for PA-2a/PA-2b as split above:
`work/adapters/postgres_{domain_action_index,work_read,global_read}.py`, `estate/coverage.py`,
`site_outcomes/{board,mini,ev}.py`, and `global_work_api.py` if the summary needs it. PA-1 has merged
`site_outcomes/{board,mini,ev}.py`, so PA-2a rebases on main first.

**Settled items: noted.**
- The "critical load" wording is PB-2's.
- `display_code` uses minimum 3-digit padding.
- The `plan_due` boundary is as the implementer settled it.
- Both "Recommendation not accepted" maps change to "No action agreed yet".

---

## Addendum 7 (2026-11-01): PB-1 pre-flight rulings

**Q1: accepted.** PB-1 removes every visible " UTC" and "(UTC)" in the frontend, in all files, including:
- the PB-2 and PB-3 files;
- `EstateEvidence.tsx:96`, `estateFinancialsWords.ts:148` and `portfolioWords.ts:93`.

The edits are time-only: `time.ts` calls, dropped "(UTC)" labels, and `TimeZoneNote` in each bar. The lanes run in
order, so there is no conflict. PB-1 grows to **6 units**, including the 0.75 slack from Addendum 1. If it would
exceed 6, PB-1 stops at the 14 capture screens and lists the rest for PB-3.

**Q1a: accepted.** Where the time text sits inside a §3.1 row, PB-1 applies the whole row as ruled. These are the
five rows named (Kobo day control and window sentence, Kobo "Latest checked readings…", Cold window line, EV "as of…",
Work "Updated… · Reload"). The PB-1 packet lists them as "done in PB-1", and PB-2/PB-3 skip them.

**Q2: accepted.** `{seconds: true}` is optional. Seconds appear only where an existing ruling shows them: R372
historical "as of" lines, SiteHealth, EvEnergy and the cold hm. Live and latest lines have no seconds.

**Q3: accepted.** Each formatter keeps its own null word. Unparseable input shows "Time not available yet" and never echoes the raw string.

**Q4: accepted.** PB-1 makes the one copy change "Supported, coherent source" → "Well supported"
(`portfolioWords.ts:40`) with the P-03 CSS. PB-3 skips it.

**Q5: accepted.**
- `formatDayRange(from, toExclusive)` gives "23–29 Oct 2026" within a month and "28 Sep – 4 Oct 2026" across months.
  Across years, both ends are written in full.
- The cutoff picker moves into a `<details>` titled "View an earlier point in time". It is closed by default and open
  when `known_at` is set. The Show button stays in the bar.
- "This is an earlier evidence cutoff." becomes "Showing an earlier point in time."
- The historical line reads "Information as of {dayTime}".

**Q6: corrected.**
- PB-1 adds `formatDay(value, {timeZone})` to `time.ts`, and uses the plain "Times in UTC" note on **every** page,
  including Preventive, Maintenance and the work request pages.
- The two-part note "Times in UTC · due dates in each site's local date" is switched on by PB-3, in the same commit
  that wires the Site-zone due dates under P-09 with PA-2b's read.
- This way no page claims local due dates before it shows them.

---

## Addendum 8 (2026-11-01): PB-2 pre-flight rulings

**Q1: accepted, with a lane constraint.**
- PB-2 changes `mini.py:102` `GAPS_NO_READINGS` to "{g} of the last {n} days {verb} no checked readings yet" and updates
  `test_idx_gaps_board.py:72`. `GAPS_NOT_ASSESSED` and `GAPS_WITHHELD` are unchanged.
- PB-2's edits to `mini.py` are limited to string constants (`GAPS_NO_READINGS`, `FINDING_TITLE`); no logic.
- PA-2a also edits `mini.py` (display codes, `VERIFIED_WITH_COST`), so the coordinator merges whichever lands second
  after a rebase. A conflict there is constant-level and is resolved by keeping both changes.

**Q2: corrected.** The ROLE_WORDS entries are "Essential services: power supplied" and "Essential services: power
requested". The fallback capitalises the first letter. Builders must check the result against the vocabulary guard.

**Q3: accepted.** PB-2 changes only the shared Overview slot title (Kobo/mini) to "Possible cost". The cold and EV
headings go to PB-3.

**Q4: corrected, and moved to PB-3** (`EstatePortfolio.tsx` is a PB-3 file).
- "Estimate" clashes with the money panel's "Latest estimate" and "How this estimate was made".
- Use badge "What-if" and "No reviewed what-if yet". This is mock wording, so it goes in the R655 plain-language row.

**Q5: accepted as proposed.**
- Add the optional `technical` prop on `ui/Disclosure.tsx`, which renders `data-technical-details`.
- Add `ui/TechnicalDetails.tsx` with two pieces:
  - "Technical details";
  - "How this was worked out", with plain lines and the raw references nested in Technical details.
- `ExactReferences` stays unchanged.
- Switch the Kobo board, the verification page, SiteAction History and the `SourceProvenanceRecord` id lists.
- Rename the verification DigDeeper to "Technical details", and tag the two id-holding DigDeepers.
- Cold/EV/foundation `ExactReferences` sites that leak ids on capture screens are PB-3 (the Addendum 5 baseline decides which).

**Q6: accepted. PB-2 applies `displayCode()` at all ~25 visible render sites, including files owned by PB-3.**
- Lane B runs in order and PB-3 starts from main after PB-2 merges, so there is no parallel conflict.
- aria-labels and the "Action code" reference row keep the stored code.
- PB-2's packet lists every file it touched that PB-3 owns, and PB-3 rebases on main first.
- PB-2 grows by about 0.5 unit. If it would exceed 6 units, PB-2 stops after the capture-screen sites and leaves the rest to PB-3.

---

## Addendum 9 (2026-11-01): PA-3 pre-flight rulings

**Q1: accepted.**
- `DB_RE` becomes `^assetops_(demo3|polish)_[a-z0-9]{1,20}_test$`.
- `Demo.__init__` accepts `var/demo3*` or `var/polish*` directly under the checkout's `var/`.
- The marker and drop guard are unchanged, and the help text is updated.
- Add one pure test case each, for an accepted polish name and for a refused other name (for example `assetops_other_x_test`).

**Q2: accepted.**
- `demo_combined_cold.py` sets `ns["DEMO_NARRATIVES"] = True`. Only then do the calls at `:202` and `:461` pass `narrative=f"{title}."`.
- The standalone w502 walkthrough keeps its default, so historical audit evidence stays reproducible.
- `:315` (worst case only) is unchanged.
- Kobo `:115` and EV `:116` pass `narrative=f"{v['title']}."` directly.

**Q3: accepted.**
- A cold or EV story day with null `start`/`end` links to the whole calendar day, `{day}T00:00:00Z` to the next day.
- Its label says so: `… day S{offset}d ({day}), no event: whole day`. This way the presenter knows the board will read
  "nothing to show" rather than an event.
- Do not skip the row. The calendar should list every story day.

**Q4: confirmed. This is the ruled form, not a loosened check.**
- The CO-1 check reads `issues` + `in_hand` only, which folds in DEMO-A L2.
- It passes when `k["action"]` is in an item's href, which is the real guard, **or** `display_code(k["action_code"])`
  is in its text. That is the §3 / Addendum 6 Q8 display form.
- Import `display_code` from `outcomes/display_code.py`; do not copy it.

DEMO-A L1 stands: add back the assertion that "Reliable service and battery and generator life" is in the safeguards
text (`board.py:658` still composes it).

---

## Addendum 10 (2026-11-01): CO-1 "Action on the Cost row" (corrects Addendum 9 Q4)

**Ruling: the check's premise was wrong. This is not a board gap.**
- On day S the trial is VERIFIED, a final outcome. A finished intervention belongs under Earlier interventions, so the
  board places it correctly.
- LINK-LINEAGE guarantees that the Action is **linked** on the row (problem → trial → Must-not-harm). It does not
  guarantee which column the Action appears in.

**CO-1 asserts the linkage by href, with the column chosen by the verification state:**
1. When `kobo.json`'s verification outcome is final (VERIFIED, INEFFECTIVE or INCONCLUSIVE), the OPTIMIZE_COST row's
   `earlier` holds an entry whose href path is `/sites/KOBO-001/actions/{k["action"]}`. Otherwise, `issues` + `in_hand`
   hold such an entry. A text match alone never passes.
2. The Must-not-harm href contains `k["action"]`, and its text contains `display_code(k["action_code"])` (unchanged).
3. The safeguards text contains "Reliable service and battery and generator life" (DEMO-A L1, unchanged).

**Why this still fails on behaviour from before LINK-LINEAGE.** The trial Action's origin is an earlier revision of the
Finding, and that version of the board only linked Actions whose origin revision was the current revision. So it shows
no Action href on the row and no Must-not-harm, and (1) and (2) both fail. Pin this with a pure test of the CO-1
function on two row fixtures:
- a linked `earlier` href passes;
- the same row with no Action href (text "ACT-001" only) fails.

DEMO-A L2 is resolved by the href requirement: text that only names the code, like CO-3's line, cannot satisfy (1).
No rebuild is needed. Re-run only the finish check on `assetops_polish_full_test`, and expect 17/17.

The Kobo Finding title still reads "Generator support merits review" until PB-2 merges. That is expected; PC verifies it.

---

## Addendum 11 (2026-11-01): EV TARIFF_GAP wording

`backend/assetops_backend/ev_site_reads.py:74` TARIFF_GAP detail: "Needed before a gross tariff scenario can be
estimated." becomes **"Needed before charging income can be estimated."** The action title ("Publish an EV gross
tariff") becomes **"Publish a charging tariff"**. PA-3 owns this change (lane A, still open): update the tests that pin
the old text, and re-capture `ev-board-fault` after the change. Register: add both strings to the R655 plain-language row.
