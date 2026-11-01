# Review: POLISH-PB-3 (estate, cold/EV and work copy; P-07, P-09, P-10)

- Reviewer: fresh Claude reviewer, independent of the builder. Date 2026-11-01.
- Branch `task/POLISH-PB-3-estate-work-copy`, head `28f516edd`, worktree `AssetOpsV1-polB3`. Diff `0ad27df7f...28f516edd` (92 files).
- Spec: plan2 `.agent/build-sheet-POLISH.md` §1.2, §1.4, §1.5, §3/§3.1, §5 PB-3, §6, §7, Addenda 3, 5, 6, 7, 8, 12.
- PA-3 wire fields read from `AssetOpsV1-polA3` `84ab3ca3d`.

## Verdict: REVISE

Two Medium findings. The fixes are small.
- **M1** must be fixed on the branch. It is client-visible on `portfolio-week`.
- **M2** is fixed on the branch, or the Architect accepts D3 explicitly.

P-07, P-09 and P-10 are built correctly against the spec. The guards, tsc and the scoped vitest are green.

## Checks I ran (on `28f516edd`)

| Check | Result |
|---|---|
| `npx.cmd tsc --noEmit -p .` | exit 0 |
| `powershell -NoProfile -File tools\check-all.ps1 -Python <plan2 .venv>` | **All 12 guards passed**. Missing-claim scan: 43 tagged, 10 baselined legacy, baseline vs merge-base `0ad27df7f4`. |
| `npx.cmd vitest run` on `workRequestOverview`, `globalPreventive`, `coldSiteViews`, `outcomeBoard` and `estatePortfolio` tests | **5 files, 189/189 passed**, 24 s. Vitest ran under this sandbox, so the scoped numbers are verified here. |
| Full vitest | Not rerun. Cited from the packet: 150 files, 3590 tests, 344 s. That run was on `a5e514ecf`. The two later commits change only records, the task file and the packet, so the run is valid for this head. |
| Captures | Not rerun (serve and browsers are not allowed). I inspected `pb3cap/captures.json`: 20 captures, all `settled:true`, `overflow:false`, 0 counted hits, and 1 `exempt_hits` each (the time-zone note). I viewed the `wr-overview`, `maintenance-preventive`, `cold-board-failure` and `portfolio-week` PNGs at 1440. |
| Layout evidence | `not run`, as the packet records honestly. The capture overflow measure stands in. |

## Findings

### M1 (Medium, acceptance and honesty): the D1 rewording turns "not shown yet" into "no data exists", which is false on demo rows

These lines are affected:
- `frontend/src/estate/EstatePortfolio.tsx:121` `?? "No time recorded yet"`;
- `frontend/src/estate/EstatePortfolio.tsx:153` `<small>No cost basis recorded yet</small>`;
- `frontend/src/sites/EvSiteViews.tsx:1418`.

**The time line.**
- `moneyWindowText` (`estateFinancialsWords.ts:141-143`) returns null when *either* end is null.
- The three GreenHarvest rows in `portfolio-week` are open episodes. Their start is recorded, and the same row's Placement cell says "No end time yet".
- So the cell now says "No time recorded yet" for an episode whose start time is recorded and shown elsewhere (the cold board shows 16:15).
- The ruled §3.1 text "Time not available yet" said that the page cannot show the time, which was true. The new text says the record has no time, which is false.

**The cost basis line.**
- This line is hardcoded on every row, whatever the consequence state is.
- On a PRICED row, a basis exists: Kobo, for example, has the declared diesel price (§1.1).
- So "No cost basis recorded yet" makes a data claim that is false there. "Cost basis not available yet" did not.

**Why it matters.** The owner's standing rule is that missing data is stated plainly and honestly. Swapping a UI-gap statement for a data-absence claim to get past the missing-claim guard fails that rule on the demo's main screen.

**Fix.**
- Time: when only `episode_start` is present, show the start, for example `From 30 Oct 2026, 16:15 · no end time yet` (formatDayTime). Use "No time recorded yet" only when both ends are null.
- Basis: keep the ruled "Cost basis not available yet" through a registered `MissingClaim` gap, which is the route the guard intends. Or show the line only on rows where it is true.
- The other D1 strings are honest and plain, and I accept them:
  - "Repeat visits could not be checked (the site summary could not be read)";
  - "No what-if value worked out yet";
  - Preventive "Not shown" / "This list did not include the due counts" / "Due status not sent with this list".

  "Not sent with this list" is slightly technical, but it is accurate and appears only on an older build.

### M2 (Medium, spec deviation and gate coverage): D3 tags many disclosures that clients can open, under their own names, as `data-technical-details`

These disclosures are affected:
- `coldSiteViews.tsx:1073` Source details, `:1315` Record details, `:1354` Claim details, `:1509` Basis details;
- in `EvSiteViews.tsx`: Event details, Chart details, What-if details, Capability details, Source details, Record details, Claim details, Basis details and Assumption details (all `technical` added).

**What is wrong.**
- §3 rules that disclosures holding ids "are renamed 'Technical details' and tagged".
- Addendum 5 makes `[data-technical-details]` the *only* region removed before the id checks.
- The PB-0 strict scan and the `-open` stress capture skip the whole region for vocabulary as well.
- D3 keeps the plain names and tags the whole disclosure. Disclosures such as "Assumption details", "What-if details" and "Source details" hold client-relevant prose, not only ids, and all of that prose has now left the strict gate.
- Nothing in these regions is verified as plain language. A client who opens "Assumption details" in the demo sees text that no gate checked.
- The Architect has not ruled on D3. Addendum 5 says a new exempt region is a finding for the reviewer.

**Fix, either of these:**
- (a) Leave the named disclosures untagged and nest a `TechnicalReferences`/`TechnicalDetails` block around only the id lines inside them. `WorkedOut` already does this. The "one disclosure per panel" tests need to count top-level disclosures only.
- (b) The Architect explicitly accepts D3 and adds a register row, and PC opens these disclosures in a review pass.

### L1 (Low, ruling vs. rationale): the two-part note shows on pages with no local due dates

- `workRequestShared.tsx:277` (`<TimeZoneNote dueDates />`) and `GlobalMaintenance.tsx:359` (`dueDates`).
- The `wr-overview` capture shows "Times in UTC · due dates in each site's local date" next to "Due / SLA: Not set". The corrective Maintenance page lists no due dates either; its preventive card is "Not assessed".
- Addendum 12 Q2 does name "Preventive, Maintenance and the work request pages", so this follows the ruling. Addendum 7 Q6's own reason, though, is that no page should claim local due dates before it shows them.
- It is not misleading, only redundant.
- Suggest: plain note on the corrective and WR pages, two-part note only on Preventive. This is an Architect call; it does not block.

### L2 (Low, residual): "Open incident →" opens a list whose default window follows the wall clock

- `coldSiteViews.tsx:681` uses the board href as sent, `/sites/COLD-LAB-001/work/incidents`.
- That is a real, mounted route (`App.tsx:480`, `SITE_WORK_INCIDENTS_ROUTE_PATH`), so the D2 deviation lands on a working page.
- With no `from`/`to`, `workCasesScope` falls back to `defaultWorkWindow()` (`workClient.ts:187`): the last 7 UTC days from *now*.
- INC-005 occurred on 30 Oct, so from about 6 Nov the link opens a list without the incident.
- The board's own INC-005 link has the same behaviour (`site_outcomes/mini.py:569`), so PB-3 adds no new defect.
- Fix: PC adds a runbook line, or the link appends the cold window's `from`/`to` (a frontend-only change of a few lines).

### L3 (Low, packet accuracy): `a5e514ecf` changed more on capture screens than the packet says

The packet says the post-capture commit changes only "Cost basis not available yet". It also changes:
- "Time not available yet" and "What-if value not available yet" on `portfolio-week`;
- the Preventive missing-summary words;
- the P-07 unavailable text;
- cold/EV refusal references.

The `portfolio-week` PNG therefore shows the pre-D1 wording. No vocabulary effect is likely, but PC's recapture must be the evidence of record for these screens.

### L4 (Low, judgement asked in item 6): SiteFinding pages show Site-local times beside "Times in UTC"

- `SiteFinding.tsx:571-572`: `LocalPeriod` (for example "… 07:35–10:55 EAT") sits next to `<TimeZoneNote/>` ("Times in UTC"). The same holds for `periodText`/`endText`, and for the History page.
- The local times carry an explicit zone abbreviation, so a reader can tell which zone they are in. It is inconsistent rather than misleading, so I rate it **Low, not Medium**.
- The real confusion risk is elsewhere: the same Kobo episode reads 04:35–07:55 on the board and 07:35–10:55 EAT on the Finding.
- Suggest: a third note variant ("Times in UTC · the period in site time") or the two-part wording on these pages. Fold it into PC or a later polish.

## Item-by-item results

1. **P-07: correct.**
   - `WorkRequestOverview.tsx:180-225` covers all four states. Loading has `role="status"`.
   - A rejected promise is now caught as unavailable; previously it was swallowed.
   - `none` renders an empty wrapper, so the attribute settles.
   - `tools/evidence-checks.mjs:45-48` refuses to settle while `[data-repeat-check="loading"]` remains.
   - The 4-state test is at `workRequestOverview.test.tsx:731`.
   - The capture shows the notice, so R630 is closed.
2. **P-09: correct.**
   - Cards and badge read `summary` through a validating `summaryOf`. A missing or invalid summary is stated, never shown as zero.
   - Chips read `due_state`: Overdue amber, Due soon blue, No date neutral, nothing for NOT_DUE.
   - `nextDue` uses `formatDay(…, {timeZone: site_time_zone ?? null})`, which falls back to UTC.
   - DRAFT reads "Not yet approved" in neutral tone.
   - Addendum 4's "based on hours of use" line is present.
   - The capture matches: 2 overdue, 2 due soon, 1 hours-of-use plan, 21 Oct / 26 Oct Overdue.
   - Minor edge: the counts use the UTC instant against `to`, while the row day is Site-local, so a plan due late on the evening before `to`'s day in a +zone can read as due "on" `to`'s day yet count as overdue. It is not seen in the demo (all zones are UTC or EAT and due dates fall at 00:00Z).
   - The note placement is covered under L1.
3. **P-10: correct.**
   - `onRead` is called inside the existing effect, whose deps stay `[client, key]`, so it adds no fetch.
   - The test asserts one distinct query. A strict call-count assertion would be stronger; this is not a finding.
   - `windowIncident` takes the first `kind === "INCIDENT"` item with `occurred_at` in `[from, to)` across `in_hand` and `earlier`.
   - The three texts match Addendum 12. `displayCode` is idempotent on "INC-005".
   - The href is covered under L2.
4. **Asset labels: correct.**
   - `assetLabelWords` and `coldAssetLabel` are removed. Rows render the wire `asset_label`, and `WorkRequestOverview` uses `asset_label ?? assetWords(...)`.
   - `ASSET_WORDS` no longer emits "EV connector". `EV_CONNECTOR` and `CONNECTOR` give "Connector c1".
   - Fallback nuance: GENERATOR always gives "Backup generator" (on mini the server says "Generator"). It applies only when the wire field is absent, so it is acceptable.
5. **Technical details.**
   - I checked these ids and found them inside `[data-technical-details]` or only in `title`/`aria-label`:
     - cold/EV `REC`, `SES`, `F` and Assessment;
     - estate Finding, revision, progress, exclusion and footer source ids;
     - WR stored action id;
     - Preventive earlier version;
     - `siteWorkCases` fence and UTC bounds.
   - The disclosure tagging is covered under M2.
   - Nothing a client needs is newly hidden, with one judgement call: `siteWorkCases` "Linked evidence" (a raw coverage enum) moved into Technical details. It was not plain before either, so this is acceptable.
6. **UTC tail:** spot-checked SiteFinding, SiteFindingHistory, coldDepthGraphics, EvAvailability and ColdScenarios. Suffixes are dropped and each status bar gains a note. The mixed-zone note is covered under L4.
7. **D1 wording:** see M1. Two of the strings are not honest; the rest are fine.
8. **Copy:**
   - The builder copy list is plain and passes the vocabulary guard.
   - "What-if", "Compressor on", "Cooling on" and "Charger report" are clear.
   - "Gross tariff estimate" and "No gross tariff estimate yet" are acceptable. "Gross" is mildly jargon, but it is §3.1-adjacent.
   - EV source reasons use "Registered test sources", which sits inside Technical details.
9. **Tests:**
   - Removed assertions are matched by replacements with the new strings. Negative assertions are kept with the new wording (`some days not checked`, `The version of the finding it came from`, `Not priced yet`).
   - One intent shift: the Portfolio twin-row test no longer asserts that the two rows' texts differ (`new Set(labels).size === 2`). It now asserts that no id is visible. This follows from the §3.1 ruling, so it is not a loosening, but twin rows now read identically apart from their links.
10. **Lane A server text, checked in polA3 `84ab3ca3d`:**
    - **`placement.py:56,60` (`_SOURCE_TEXT`/`_LIFECYCLE_TEXT`): "Supported Finding · Generated test data source".**
      - It is visible in the Confidence column of every Portfolio row in `portfolio-week`.
      - It contradicts the §3.1 row "Supported finding · example data" and the D-1 banner ("example … records prepared").
      - **This should block PC.**
    - **`placement.py:31` "No accepted Action; open the recommendation"** is not in the packet's list. It is also visible on the three GreenHarvest rows (Placement cell) and uses the capitalised "Action", which §3.1 rules against. **It should block PC** together with the item above.
    - `portfolio.py:146` already reads "No action agreed yet" (done). `evidence_money.py:43` already reads "Current view" (done). The packet list is stale on these two.
    - `portfolio.py:297-299` "Not established" (UNSUPPORTED/NOT_ESTABLISHED `display_value`) is overridden on the Assure card. No other card shows it in the capture, so it should not block. It is a latent risk if another card reaches that state.
    - The placement "No price basis for this Finding" (Kobo row) and "Site coverage incomplete; other Findings may be missing" also carry capitalised "Finding". These are low.

## Residual risk not named in the packet

- The M2 regions are outside every automated plain-language check.
- PC's recapture is the only capture of the post-`a5e514ecf` copy (L3).
- The incident link and the incidents list depend on the demo date (L2).

---

## Re-review (fix round, `28f516edd...ef43cd219`)

- Reviewer: fresh Claude reviewer, independent of the builder. Date 2026-11-01.
- Worktree `AssetOpsV1-polB3`, head `ef43cd219` (5 commits; the last one changes only the packet and the register).

### Verdict: ACCEPT

M1 and M2 are closed. L1 and L4 follow Addendum 13. L2 is fixed. Two new Lows (N1, N2) are copy consistency. Neither is false or blocking, and both can be folded into PC's copy pass.

### Checks I ran (on `ef43cd219`)

| Check | Result |
|---|---|
| `npx.cmd tsc --noEmit -p .` | exit 0 |
| `powershell -NoProfile -File tools\check-all.ps1 -Python <plan2 .venv>` | **All 12 guards passed**. Missing-claim scan: 43 tagged, 10 baselined, merge-base `0ad27df7f4`. |
| Scoped vitest: the 10 changed test files (estatePortfolio, coldSiteViews, evSiteMoneyRoutes, evEnergy, siteFinding, siteFindingHistory, globalMaintenance, workRequestOverview/History/Record) | **10 files, 382/382 passed**, 39 s. `energy_states_table_loading` passed in 985 ms. |
| Adjacent vitest: coldDepth, coldHealthDepth, evAssessmentRoutes, outcomeBoard, `src/estate` | **9 files, 204/204 passed**, 23 s. |
| Full vitest | Not rerun. The packet cites a run on `8f3de6e52`: 150 files, 3593/3594 passed, 356 s, with 1 failure (the evEnergy flake). `8f3de6e52..ef43cd219` changes only `.agent/` files, so that run applies to this head. |
| Recapture `pb3cap2/captures.json` | I read it: 20 captures, all `settled:true`, `overflow:false`, `vocabulary_counted:0`, `stale_words` empty, and 1 exempt hit each (`data-time-zone-note=utc`). It was taken at `f1547458e`. The only later frontend commit, `8f3de6e52`, touches EvEnergy, which is not a capture key. I viewed `portfolio-week-1440.png`: the GreenHarvest rows read "From 30 Oct 2026, 16:15 · no end time yet" (and 16:00, 27 Oct), Kobo reads "30 Oct 2026, 04:35–07:55", and no row has a cost-basis line. |
| Layout evidence | `not run`. It is recorded honestly in the packet, and the capture overflow measure stands in. |
| Serve, browsers and `-Tier all` | Not run, as instructed. |

### Items

1. **M1: closed.**
   - `EstatePortfolio.tsx:121-124`:
     - with both ends present, `moneyWindowText` is used;
     - with only the start present, the cell reads "From {formatDayTime(start)} · no end time yet";
     - otherwise it reads "No time recorded yet".
   - The always-on basis line is removed. The new test (`estatePortfolio.test.tsx:320-329`) can fail on every branch: on the open-episode text, on the no-time text, and on `not.toContain("cost basis")`.
   - The EV Assumption line `EvSiteViews.tsx:1456` reads "No cost basis recorded yet" only when `t.basis` is null, which is a true statement.
   - I found nothing false left. One nit, not a finding: a row with an end but no start would still read "No time recorded yet". That state does not occur.
2. **M2: closed.**
   - The `technical` flag is removed from all 4 cold and all 9 EV named disclosures. Each now nests a `TechnicalDetails` that holds only `TechnicalReferenceList` ids:
     - cold `coldSiteViews.tsx:907-910, 1353-1362, 1403-1406, 1550-1580`;
     - EV `Ids` at `EvSiteViews.tsx:177-183` and its uses.
   - The plain-word changes match the packet list:
     - Record/Rule/Source/Excluded record numbering;
     - `plainCode` for Kind, use, reason, quality and state;
     - `dayHm`/`windowText` instead of raw ISO;
     - "Tariff declared/not declared";
     - "Earlier what-if · version N";
     - the unverified-source sentence;
     - "Show more accepted records".
   - The only id left outside the nested blocks is the `KeyValues` label `{rule_id} details` (`coldSiteViews.tsx:1391`), which is an aria-label. That placement was accepted in round 1.
   - **The test relaxation is narrow.**
     - `topLevelDetails` (`coldSiteViews.test.tsx:371`) skips only a `details` whose ancestor is itself a `details`. A second top-level disclosure in a panel still fails.
     - A nested non-technical disclosure would pass, but none exists, and the M2 assertions pin the shape.
     - `evAssessmentRoutes.test.tsx:315` still counts all `details`, and it passes because those screens are unaffected.
   - **The new tests can fail.** They assert all of these:
     - `hasAttribute("data-technical-details") === false` on Basis and Assumption details;
     - the id appears inside the nested block;
     - `plainOf(...)` does not contain the id;
     - the plain prose is present;
     - no raw ISO time (`evSiteMoneyRoutes.test.tsx:478-500`, `coldSiteViews.test.tsx:737-742, 758-761, 851-855`).
     Restoring a raw id, a tag or an ISO time would fail them.
3. **L1 and L4 follow Addendum 13.**
   - `workRequestShared.tsx:276-277` and `GlobalMaintenance.tsx:359` use the plain note. Only `GlobalPreventive.tsx:296` passes `dueDates`. All 6 pinned status-line tests were updated to the plain note.
   - SiteFinding:
     - `EpisodePeriod` (`SiteFinding.tsx:583-591`), `periodText` and `endText` render in UTC with no zone tag;
     - the exact stored instants are in `title`;
     - the old "UTC time" disclosure and the "(site time zone unavailable; UTC shown)" suffix are removed;
     - there is one `TimeZoneNote` per bar, asserted.
   - History: the header is "Time" (`SiteFindingHistory.tsx:346-347`), cells read `formatDayTime(…, {year:false})` ("6 Oct, 14:10"), and the exact UTC is in `title`.
   - **`periodWords` → `formatRange`: accepted.**
     - The page already used `formatRange` for the portion line (`SiteFinding.tsx:727`), so it now has one period form.
     - It replaces the raw `2026-10-06 08:00–09:00` form.
     - An unparseable instant now gives the standard "not available" text instead of a broken string.
     - It is within the spirit of Addendum 6 Q7 and §3 Times.
   - `findingTime.ts` is still used by `LedgerSiteEvidence.tsx`, so nothing is dead.
   - **R661 is updated.** Addendum 13 asked for a D2 row. Folding the text into R661 is acceptable.
4. **L2: fixed correctly.**
   - `incidentHref` (`coldSiteViews.tsx:619-629`):
     - splits the href on the first `?`;
     - keeps the existing params;
     - overwrites `from`/`to` with the page window, falling back to the board's resolved window;
     - returns the href unchanged only when neither window is known.
   - The test (`coldSiteViews.test.tsx:1425-1436`) covers merging into `?status=open&from=old` and the fallback.
   - ISO `from`/`to` is the form `workCasesScope` (`SiteAnalyticsFrames.tsx:2369-2376`) consumes, so the list opens on the window that holds INC-005.
   - Residual (not verified, needs a browser): when the cold page window is narrow (minutes, not days), the incidents list's date fields show a sub-day window.
5. **EvEnergy wording is in the spirit of Addendum 11.**
   - "No eligible charging income estimate." and "{v}/kWh charging tariff (charging income estimate)" (`EvEnergy.tsx:74,77`).
   - The second is a little redundant but plain and honest. See N2 for the sibling card note it missed.
6. **Still-open items: none should block PC.**
   - "Claim details" and "How a claim limit is set" (`coldSiteViews.tsx:1371`, `EvSiteViews.tsx:1201`) are v69 mock text (`v69/index.html` carries the heading).
   - "Scenario display currency" (`EvSiteViews.tsx:1510`, EV Assumptions) and the bridge badge "Scenario" (`EvSiteViews.tsx:1344`, EV Financials) are visible to a client who opens the EV Assumptions or Financials tab. They are reachable on a demo path, but they are mock vocabulary, not false and not a banned term (the guards pass).
   - They are inconsistent with the "What-if" wording §3.1 uses elsewhere.
   - Recommendation: PC's review pass opens EV Analysis, Financials, Assumptions and Energy, and either renames them in one copy commit ("What-if" badge, "Display currency", "Basis details"/"How a limit is set") or records them as accepted mock wording. Low, not a gate blocker.
7. **The evEnergy flake: PB-3 did not make it worse, and PC does not need a fix.**
   - `energy_states_table_loading` has failed the same way under full-suite or parallel load since W5-02b. It is recorded in the W5-02b handoff, the W5-03b re-review, post-W6 W1-a/W1-b, shell, W3-estate, OUT-A and PB-1.
   - The message comes from `settledScreen`'s `waitFor` (`test/settled.ts:66-72`) timing out while the loading text is still present, which is a load symptom.
   - PB-3's change to `EvEnergy.tsx` is two strings and adds no render or read cost. The test passes alone here in under 1 s.
   - PC should record a full-run failure of this test as the known flake after a passing solo rerun. The real fix belongs to the test-pipeline task, not PC; for example, a longer `waitFor` timeout for this test, or awaiting the loaded heading after `resolve`.

### New findings

**N1 (Low, copy consistency): "Generated test data" now shows in the plain prose of cold and EV disclosures.**
- `coldAssessmentWords.ts:108` maps `REGISTERED_SIMULATION` to "Generated test data".
- M2 moved this word out of the old tagged regions into the plain lines:
  - cold Record details "Source: Generated test data" (`coldSiteViews.tsx:1349`);
  - EV Capability, Claim, Record and Basis details "source Generated test data".
- It is not false.
- §3.1 rules "Example data" for the same idea (Kobo row, and the Portfolio row that Addendum 13 is fixing in PA-3). The demo would say "example data" on Portfolio and "Generated test data" one click deeper.
- The EV Assumptions main text already showed it before this round.
- Fix: change the map value to "Example data" (one line plus the pinned test strings). This is an Architect wording call; fold it into PC.

**N2 (Low, Addendum 11 completeness): the EV Energy card note still says "Scenario tariff".**
- `EvEnergy.tsx:166` reads "Scenario tariff: 0.30 USD/kWh" / "Scenario tariff not established". It sits beside the bridge cell that now reads "charging tariff (charging income estimate)".
- The mock has the same note (`v69/index.html:596`).
- Fix: "Charging tariff: …" / "Charging tariff not set". Fold it into PC with item 6.

### Residual risk

- No `-open` capture covers the newly untagged disclosures, so their prose is checked by vitest and the guards' vocabulary scan only. The packet says so.
- The narrow-window incident link (item 4) has not been seen in a browser.
- Lane A text ("Supported Finding · Generated test data source", "No accepted Action; …") is still on `portfolio-week` until PA-3's Addendum 13 fix merges. It is already ruled to block PC.
