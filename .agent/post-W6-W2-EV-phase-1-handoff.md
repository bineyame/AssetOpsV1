# post-W6 W2-EV phase 1 handoff (PARTIAL: interfaces only)

Branch `task/post-W6-W2-EV`, worktree `AssetOpsV1-review5`. Inputs: `.agent/post-W6-W2-EV-rulings.md` (binding),
`.agent/post-W6-W2-EV-preflight.md` (anchors and Q numbers), `.agent/post-W6-W2-cold-rulings.md` (cold behaviour for
the duplicates). The builder stopped at the context budget after landing the shared interfaces.

## Landed

Commit 3c533f0f contains the exact signatures, also listed in the commit message.
- `shell/operatorSiteTabs.tsx`: `OperatorSiteTabLabel`, `OperatorSiteTabHrefs`, the props `hrefs?` and `search?`, and
  `operatorSiteTabHref()`.
- `shell/evSiteRoutes.tsx`: `EV_SITE_TAB_HREFS` (Overview → `/ev`, Evidence → `/ev/evidence`, Financials → `/ev/financials`).
- `sites/siteTime.ts`: `siteTime(value, timeZone, reference?)` returns `{text, utc, zone, siteZone}`, plus `siteZoneLabel()`.
- `sites/coldSiteViews.tsx`: `eatTime(value, timeZone = "Africa/Addis_Ababa", reference?)` delegates to it. Cold callers
  are unchanged; W2-cold migrates them.
- Tests: `shell/__tests__/operatorSiteTabsOverride.test.tsx` and `sites/__tests__/siteTime.test.ts` both pass, and
  `operatorSiteTabs.test.tsx` still passes (62 tests in total).

Shell is not merged into main yet. Its shared hunks are in `SiteAnalyticsFrames.tsx` (Action crumbs) and
`SiteFoundationFrame.tsx`. Rebase before editing those, per cross-card ownership 1.

## Remaining units (build in this order; commit each)

Line anchors are from main 7554111e.

**U1 Tabs, EV home and readiness**
- Wire `hrefs={EV_SITE_TAB_HREFS}` and `search=` (the selected read's `from`, `to` and `known_at`, never the raw URL;
  none on a refused or no-window read) on these mounts:
  - `SiteEvFrame` (`evSiteRoutes.tsx`; `tabs` is a ReactNode today).
  - The EV Sessions/Performance mount (`SiteAnalyticsFrames.tsx` ~:265).
  - The EV Finding mount (~:667).
  - The EV Foundation mount (`SiteFoundationFrame.tsx` ~:160).
- To carry the *selected* window, make the frame tabs prop `ReactNode | ((search: string) => ReactNode)`. Let the screens
  report their loaded envelope window upward, for example with an `onSelected` callback or frame state. The EV Subtabs
  (`EvSiteViews.tsx:377`) use `sel(route, window)` as the query helper.
- Bare `/sites/:id`: in `SiteDetailFrame.tsx`, an `EV_CHARGING` site gets `<Navigate replace>` to `siteEvHref(id)`,
  keeping the query. Mini and cold stay unchanged. Do not change App routes.
- R265: `EvFoundationViews.tsx:624` and `:635` become `<Link to={props.financialsHref}>Financials →</Link>` and the
  same for Assumptions. In `SiteFoundationFrame.tsx:174-175`, use `siteEvHref(siteId,"financials")` and
  `siteEvHref(siteId,"assumptions")`. Update the reason text in `tools/checks/missing-claim-scan.mjs:68` and lower the
  baseline (`missing-claim-baseline.json`). Prove an untagged phrase still fails the scan.
- R267: in `EvFoundationViews.tsx:724`, append the connector/asset name or `device_id` to the label, so each label is
  unique.
- Tests: `evFoundation.test.tsx:563-565`, home redirect on EV, mini and cold, and the tab hrefs per EV mount.

**U2 Sessions, Finding and the shared constant**
- R268: on `EvAssessmentViews.tsx:524`, replace `UnavailableInline` with `<Link>Inspect session lineage ↗</Link>` to the
  new `analysisHref` prop. Wire it at `SiteAnalyticsFrames.tsx:250-272` as `evRoutes.analysis` plus the read window.
  Hide it on a null or refused read.
- R270: under `SessionCards` (:493), when `started − (confirmed_delivery + fault_aborted + incomplete) > 0`, add one
  line: "{r} of {n} attempts are outside these three outcomes; see How to read the denominator." Place a visible D4
  label next to it.
- R271: in `w2-ev-assessment.css:21-33`, wrap the Outcome chips, bound their width, and widen the Outcome column. Keep
  the 390 scroll. Add a CSS source assertion.
- R281 / Q9: write one local `plural(n, one, many)` in `EvAssessmentViews.tsx`, export it, and use it at :446,
  `EvSiteViews.tsx:475` and `EvSiteViews.tsx:798`.
- R275: in the strip at `EvAssessmentViews.tsx:696-701`, join the claim phrase, `siteName` and
  `windowText(finding.window.from, finding.window.to)` (from `coldFormat.ts`) with " · ".
- R276: in the Bounded conclusion (:739-748), add the paragraph link "Inspect claim evidence ↗" to the analysis at the
  Finding's own window. Add an `analysisHref` (function of the window) prop on `EvFindingFrame`, wired at
  `SiteAnalyticsFrames.tsx:660`. Keep `REC … · No analysis link`.
- R280: set `FINDING_SECTION_UNAVAILABLE` (`SiteAnalyticsFrames.tsx:616`) to "This Finding section is not available
  for this kind of Finding."
- Tests: `miniDecisions.test.tsx:834/1072/1100` and `evAssessmentRoutes.test.tsx`. Cover cold and EV child addresses
  and an unknown child.

**U3 EvSiteViews**
- R283: in `chronology` (:499-526), drop the padding. Above 7 events, show the first 7 plus "{n} more accepted events in
  Event details". Event details is the in-page Disclosure at :609; there is no mounted target, so per ruling Q10 render
  all events instead. Test none, one and eight events.
- R284 / ruling 5 refusal set: in `evRefusalText` (`EvAssessmentViews.tsx:79-95`), classify `read.code`:
  - `EV_WINDOW_INVALID` → "The selected window needs both a start and an end, with the start before the end."
  - `EV_WINDOW_TOO_LONG` → "The selected window is longer than 31 days."
  - any other 422 → "The selected window is invalid."

  The title is "Window cannot be read". On Overview, Evidence, Analysis, Financials and Assumptions, keep a strip and the
  normal tile labels with "Not assessed": Overview has the 5 `OverviewCards` labels (:482), Financials the 4 at :1239.
  Add one in-panel sentence and a technical disclosure, with no page banner. A non-window refusal keeps its own title and
  the requested-window line. The cold pattern to mirror locally is `coldSiteViews.tsx:394-428`; do not import it.
  Sessions and Finding inherit the new copy; test them.
- R285: at :1287, show "Energy ↗" linked to `sel(routes.energy, f.window)` when the row is estimated, else no link.
- R286: at :1191 and :1418, render billing as a `Chip`: "No record", or "Not connected" for `NOT_CONNECTED`. Add a D4
  label.
- R254 (B9-02), `OverviewCards` :470-495: plain labels, and `MetricCard link` "View detail →" on each card. Availability
  links to Performance/availability at the window and Health to EV Health, using live values where the DTO has them or
  "Not summarised here"-style honest copy. Follow cold Q8 wording.
- R258 (B9-06), Evidence screen:
  - Strip action :850 → "Portfolio evidence", linking `EVIDENCE_PATH`.
  - Delivered energy next step → "Review energy →".
  - Work link → EV Work at the window.
  - Remove the padded next-evidence rows (:975).
  - Complete-case Cause copy: no "Limited" when nothing was interrupted.
- R259 (B9-07), Analysis table :1093-1106: header `Measured ({siteZoneLabel(tz)})`. Format Measured, Sent and Received
  with `siteTime(v, tz, i.source_time)` and put the exact UTC in `title`. This needs the Site timezone in
  `EvSiteFrameProps`, passed from `SiteEvFrame` as `site.timezone`. Test Addis, UTC, midnight crossing and a missing
  zone.

**U4 EV Findings branch**
- In `SiteFindingsFrame` (`SiteAnalyticsFrames.tsx` ~:451), add an `EV_CHARGING` branch that uses
  `evAssessment.listFindings`.
- `App.tsx` ~:435 passes `evAssessment`.
- Mirror the cold index content in W2-cold pre-flight Q3 and ruling Q3: `LensChips` from `SiteFindingIndex.tsx`, 7
  columns, and "Not assessed" priority and lens.
  - Strip: "Scoped to {site} · {n} open".
  - Empty: "No Findings at this site in the selected window."
  - Cursor: "Showing the first {n} Findings; paging is not available on this page."
  - Global-list note: "EV charging Findings are not in the global Findings list". Verify this against
    `estate/findingIndex.tsx` first.
- Do not import cold clients. Leave the mini branch unchanged.

**U5 Verify, holding the quiet-machine rule**
- Run the focused EV, Foundation, mini and tab suites, plus `tsc`.
- Run `tools/check-architecture.ps1`, `tools/check-agent-workflow.ps1`, the navigation rail fixtures (keep the pinned
  strings in preflight Q22 byte-identical) and the missing-claim scan.
- Captures (Q27-Q29; caps in ruling 8 and Q26) and the full vitest run wait until the coordinator clears the R373 suite.

## Risks

- The shell merge will conflict in `SiteAnalyticsFrames.tsx` and `SiteFoundationFrame.tsx`, so rebase first.
- W2-cold consumes `eatTime`/`siteTime` and the override, so keep the signatures stable.
