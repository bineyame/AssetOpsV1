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
