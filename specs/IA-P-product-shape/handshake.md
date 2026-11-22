# IA-P handshake (rev 2 spec; reviewer and implementer pre-flight)

Fresh Claude reviewer, 2026-11-22, on `main` at `908186bdc`. Read: `spec.md`, `spec-period.md`, `rulings.md` (D-IAP.1 to
D-IAP.23), `reviewer-guide.md`, `owner/owner-iap-q1-q2-kobo-datasheets-2026-11-22.md` (Q1, Q2, Q9, Q10 answered, not
re-raised), IA-2b's spec on `task/IA-2b1-lists` (§3, §4), vNEXT `ia-routes.js`, and the code below. No code was run;
nothing here needs a run to settle.

**Checked and found as the spec says.**
- Backend. `deep_dive/read.py` `DeepDiveRead.month` (the per-month reads P.3 copies: `snapshots.portfolio(tenant.id, m)`,
  `reconciliation.standing(tenant.id, None, m, known_at=served.as_of)`); `deep_dive_api.py` refusal order (503, 401
  `PERSON_REQUIRED`, 422, store 503, `NO_STORE`); `view.py` `_View(served, standing, names, month)`, `.R`, `.rows`,
  `.group_sums()`, `.tiles()[1]`, `.fresh()`, `_nav`, `_actions`, `month_view`; `words.py` `render_month`, `amount`,
  `word`, `weakest_of`, `named`, `factor_label`, `heading_label`, `as_of`, `no_snapshot`, `rebuild`, `text`;
  the `month` slot's `month` form (year dropped) in `i18n/schema.py:24`; `portfolio_bridge` lists operator lines and never
  adds them (`structure/attribution/portfolio.py:6`), so Site root effects can sum to `R.effect`. World A's literals
  (`test_5c_deep_dive_view.py:159-252`: $1,443.00, $2,295.00, −$852.00, −$97.00, −$755.00, "63% of target", the Kisiwa
  status sentence) double exactly to every World P literal in P.7 test 2. Kobo, Kisiwa and Mto's Site gaps in P.8 test 1
  (−$562.00, −$185.00, −$105.00) are actual minus target and sum to −$852.00. `estate/portfolio.py:895` `placement_counts`
  over `members` (E0's base). `estate/scope.py:22` `limit` 1 to 100 (P2's `limit: 50` is legal).
- Frontend. `operatorRailItems` and `railActiveLabel` (`OperatorShellLayout.tsx:60-82`); `RailIcon` has `book`, `clock`,
  no `decide`; `useDeclareRangeSpan` (`ui/rangeFocus.tsx:41`) and the bar's `data-shared-range-focus="inside"`
  (`SharedRangeBar.tsx:294`); `RANGE_PAGES`/`FILLED_PAGES` (`sharedRange.ts:228-238`); `presetRange("lastmonth")`; the P.1
  table's preset days at `now` 2026-11-22; `PORTFOLIO_TABS` (seven today); `DeepDiveMonth.tsx` reads `?month=`
  (`:591`); `CANONICAL_OPERATOR_SITE_TABS` (eight); `PLACEMENT_GROUP_LABEL`, `DOMAIN_WORD` ("Mini-grid", "Cold-chain",
  "EV charging"); `CategoryCards` (`PortfolioOutcomes.tsx:239`), `ObjectivesPanel`, `OpportunityPanel`, `ProgressPanel`,
  `TopThree`, `ScopeDisclosure`, `getOutcomeSummary`; `Disclosure`, `PageHeader`, `EstateRefusal`, `formatDayTime`;
  `estateClient` `total_count`, `next_cursor`, `limit`, `link_refs`, `lens_flags`, `action_id`, `placement`;
  `linkFor`/`routeFor` take a `view` on a `FINDING` Ref (`operatorSiteRoutes.ts:627-632`).
- Tools. `tools/deep_dive_gates.cjs` (base and fixture arguments, `/api/portfolio/month` only, the 6-block and fold
  checks); `tools/world.py:43` `CODE_PATHS`; `tools/select-tests.py`; `backend/conversions/walk-layer4-v1.json` pages;
  the DDR runbook's S7 line (`Docs/engineering/operator-deep-dive-runbook.md:195`); `.agent/mock-departure-register.md`.
- New files the spec names are absent today, as expected: `period.py`, `sites.py`, `portfolio_period.py`,
  `portfolio_sites.py`, `iaRoutes.ts`, `SectionTabs.tsx`, `HomeList.tsx`, `estateReadCache.tsx`, `fixtures/iap/`.

## Reviewer questions (R)

**R1. A range of more than 31 days cannot reach the Overview, so mode `period` and four gates cannot be judged** (spec §3,
§6 P3b H4 and H6, P4 S1; `spec-period.md` P.1 rows 5 and 6; reviewer-guide Q2). High.
- `ui/sharedRange.ts:18` `RANGE_MAX_DAYS = 31`. `readSharedRange` (`:128`) returns `invalid` for a longer range, and the bar
  refuses it (`SharedRangeBar.tsx:52`, `:221`: "… 31 days at most.").
- Every estate read refuses a window over 31 days: `estate/scope.py:21` `MAX_DAYS = 31`, `INVALID_WINDOW`. That covers
  `/api/estate/portfolio`, `findings`, `actions` and `evidence`, which feed Overview L2, the three lists, the inbox and
  search.
- So `/portfolio?from=2026-09-01&to=2026-10-31` (61 days; H4, S1's second range, Q2's two-month probe) and
  `/portfolio?from=2026-10-01&to=2026-11-21` (52 days; H6, P.1 row 5) are invalid addresses today. The spec never raises
  the cap, and "Month by month" (owner Q10) would be unreachable in the served app. The E2 and E1 backend tests pass
  anyway, because they call the view directly.

*Default:* the Architect rules the cap.
- The shared range accepts up to 24 whole months (E2's cap) on every page.
- E2 and E1 read the whole range.
- A page whose read stays capped at 31 days (estate lists, Overview L2, inbox, search, Evidence) reads the last 31 days of
  the range and declares that span through SR-4c (`useDeclareRangeSpan`), so the bar says the page shows part of the range.
  The browser takes the span's days from `presetRange`-style day arithmetic in `sharedRange.ts` only.
- The reviewer-guide sweep "date arithmetic in the browser beyond `monthDays`" names this helper.
- Alternative: keep 31 days and drop mode `period` from IA-P. That reverses owner Q10, so it goes back to the owner.

**R2. The page × Site-type matrix fails on the Overview in mode `period`** (spec §3 matrix row 1; P.5). High.
- In mode `month`, 5c names a cold-chain or EV Site through the headline suffix "Compared for 3 of 4 Sites." and the tile
  line "3 of 4 Sites" (`test_5c_deep_dive_view.py:402-410`, World G).
- P.5's period body has neither. Its `headline` variants have no compared clause. `tiles[0].lines` is only
  `[tile1_target]`, which drops 5c's `W.sites(R.k, n)` line, the cost-received line and the rest line. There is no
  `by_site` and no out line.
- So on a two-month range, a cold-chain or EV Site vanishes from the Overview without a word. The matrix says it is "named
  as not compared".
- No P.7 or P.8 test uses World G (`served_world(thika=True)`), so nothing would catch it.

*Default:*
- The period body keeps 5c's line `W.sites(k, n)` on tile 1, with `k` and `n` from the latest served month, and a
  `portfolio_period.compared` suffix "Compared for {k} of {n} Sites." when `k < n` in any month.
- P.7 adds test 11, World G with a September copy (2026-09-01 to 2026-10-31): the suffix, the tile line, and a `months` row
  per month.
- P.8 adds a World G row (Thika last, "Not available yet" ×3, `without_target.count` 1). The vitest matrix test asserts
  that the Overview, Outcomes and Sites each name Thika on a one-month and a two-month fixture.

**R3. The matrix fails on Outcomes and the Sites list for cold-chain and EV, without a deviation row** (spec §3 matrix row
2; D-IAP.9; IA-2b §4 `sites`). High.
- E1 gives every cold-chain and EV Site "Not available yet" ×3, because only the contribution kind is live.
- The governing mock's Sites list gives cold-chain rows a figure of the cost kind ("Cost per required departure met", "Over
  target"). Rows with no figure are a departure from vNEXT, and §7 has no row for it.
- The owner's range rule is "data in range gives output for that range, for every Site type". A cold-chain Site with
  analysed events in the range has data. The row still says only "Not available yet", which does not say why.
- Reviewer-guide sweep "Any unlabelled departure from vNEXT" would fail on this.

*Default:*
- Add MD-IAP-12 (D1): cold-chain and EV rows carry no monthly target, so no gap. The resolving unit is a cold or EV target
  kind in E1, to be specified.
- The row's Contribution cell reads `portfolio_sites.no_target` "No monthly target for this Site type yet", in place of
  the bare "Not available yet". Gap and driver stay "Not available yet".
- The Architect confirms that no cold or EV monthly target source exists today. If one exists, E1 needs a second kind, and
  that is a spec change.

**R4. `iaRouteMap.test.ts` passes on wrong work as written** (spec §6 P1 "Tests first"; plant `routemap`). Medium.
- "Fails on any route path that is not a live route, a live alias, a Lab route or `*`" is circular: every `<Route>` in
  `App.tsx` is a live route by definition. So a planted `<Route path="/x">` passes unless "live" means a list held apart
  from `App.tsx`.
- The test also does not check the other direction: that every §2.4 address still has a route or alias, which is the "no
  screen lost" half.

*Default:*
- The test holds §2.4's "Current address" column as its own literals, never imported from `iaRoutes.ts`.
- It asserts both directions: (a) every `App.tsx` and `operatorSiteRoutes.ts` path matches an `IA_HOMES` pattern or a live
  `LEGACY_ROUTES.from`; (b) every §2.4 literal resolves to a route or a live alias.
- The `routemap` plant fails (a); the `alias` plant fails (b).

**R5. The month words in E2's notes: with or without the year?** (`spec-period.md` P.6 "month slots use 5c's month value";
P.7 tests 4 and 6). Medium.
- 5c's month value renders "September 2026" (`deep_dive.month_words`, `month_year` form). Test 4's literal is "No
  figures are served for September, …", which is the `month` form, but it adds "(the month words as the catalogue renders
  them)".
- Test 6's November `partial` sentence is not written out. The two readings give different strings, and only one can pass.

*Default:*
- `{months}` follows `span`'s year rule over the months that sentence names: names alone when they all fall in one year,
  with the year otherwise. So test 4 reads "September" and test 6 reads "November is only partly in this range, …".
- `suggest` keeps `month_words` with the year ("Show October 2026", H5).
- P.7 writes test 6's sentence out in full.

**R6. The Sites "Gap to target" tile under a scope, a facet or a search** (spec §5.2 sites row; IA-2b §4 "Sites remainder"
and §3.4). Medium.
- The tile is E1's `total.gap`, the whole portfolio's figure. With `scope=group:COLDCHAIN`, `scope=site:MTO-001` or
  `target=below`, the tile would still show −$852.00 beside rows that do not add up to it.
- IA-2b equates the tile with the Overview only "at scope all and unfiltered". Its other cases sum parts in the browser,
  which IA-P forbids (D-5C.2).
- IA-2b's More line ("Not shown: {h} Sites, gap to target {sum}") and §3.4's whole-dollar rule are also browser sums or
  re-formatting.

*Default:*
- The tile shows `total.gap` only at scope `all` with no facet and no `q`. Otherwise it reads "Not available yet" with the
  line "For every Site only" (a new string, in the spec).
- The More line has no figure: "Not shown: {h} Sites.".
- §3.4 is not transcribed: E1's strings are shown as served.
- Add MD-IAP-13 (D2) for both.

**R7. Is a `MONITOR` placement a decision "waiting for a choice"?** (D-IAP.3, D-IAP.8, D-IAP.10; `estateClient.ts:278`).
Medium.
- `waiting` is "placed and `action_id` null", and every Portfolio member is placed, `MONITOR` and `NEEDS_INVESTIGATION`
  included.
- So the badge, the Decisions tile and each Site's "Waiting for a choice" count Findings whose placement says "watch" or
  "investigate first". Those are not choices waiting for an executive. The badge would overstate, against the
  honest-numbers rule.

*Default:*
- `waiting` excludes `MONITOR`. `NEEDS_INVESTIGATION` stays, because investigating is a choice.
- E0's `waiting_count` and `waiting_by_site` use the same rule, so `homeLists.test`'s equality still holds.
- If the Architect keeps every group, the State column reads the placement word beside "Waiting for a choice", so the
  inflation is visible.

**R8. E1's frontend fixtures are hand-written, so S1 and `sitesList.test` can pass on stale bodies** (spec §6 P4; P.8 tests).
Medium.
- P.7 test 10 keeps the `period-*.json` bodies equal to the view's output. P.8 has no such test.
- S1 compares two browser renderings of fixtures. If `sites-*.json` drifts from `sites_view`, S1 still passes, and the
  one-figure link between a real E1 and a real E2 is proven only in the backend.

*Default:* P.8 adds test 9, "Fixtures current". The committed `fixtures/iap/sites-2026-10.json`, `sites-2026-09-10.json`
and `sites-none-2026-11.json` equal `sites_view`'s output for tests 1, 7 and 3, and the E0 fixture's `waiting_by_site`
keys are E1's `site_code`s.

**R9. One figure between E1's Site gap and 5c's own by-Site table** (D-IAP.9; P.8 "One figure"; `view.py:506-535`). Low.
5c's bridge shows each Site's Gap as `W.amount(root.gap, …)`. E1 shows the Site root's `effect`. They are equal for the
contribution root today, but no test pins it, and the reviewer-guide's Q3 compares exactly these.
*Default:* P.8 test 1 also asserts that each compared row's `gap` equals that Site's `by_site` Gap cell in `month_view`
for October, string for string.

## Implementer questions (I)

**I1. Typed months and the disabled "next" in `DeepDiveMonth.tsx`** (spec §6 P3b; §5.3 "Never type a month"). Medium.
- The month screen builds month words in the browser: `MONTHS`, `monthWords` (`:64-67`) and `monthAfter` (`:70`).
- When `nav.next` is null it draws a disabled button labelled with the typed month after (`:577-579`). E2's `nav` gives
  `month_words` for both sides, but a null `next` carries no words.

*Default:*
- `MonthNav` reads E2's `nav` only. With `next` null it draws no next control.
- `monthWords`, `monthAfter` and `MONTHS` are deleted.
- The `DeepDiveMonth.test.tsx` nav assertion is updated and named in the packet.

**I2. How `iaRouteMap.test.ts` reads `App.tsx`** (spec §6 P1). Medium.
- Almost every path is a constant (`path={SITE_FINDINGS_ROUTE_PATH}`; 41 `*_ROUTE_PATH` in `operatorSiteRoutes.ts`).
- Six are `.map((path) => …)` loops over arrays (`App.tsx:426-447`, `:496-522`, `:568`), and the Lab routes come from
  `simulatorLabRoutes(...)`. A raw text scan cannot resolve these.

*Default:*
- The test imports `operatorSiteRoutes.ts` and resolves each `{IDENT}` from its exports.
- It reads the array literals before each `.map` and takes the Lab paths from `simulatorLabRoutes`' returned `path`s
  (called with stub arguments).
- An unresolvable `path={…}` fails the test, so a new form cannot hide.

**I3. `entryRange` takes `now`, not a pathname** (spec §3 "Fresh entry", P3b; `sharedRange.ts:325`). Low.
- Its call sites are `SharedRangeBar.tsx:128` and `:137`, and seven tests call `entryRange()`.
- `/` is not in `FILLED_PAGES`, so the order between the alias and the fill decides what `/` opens on.

*Default:*
- The signature becomes `entryRange(pathname?: string, now = Date.now())`. `SharedRangeOutlet` passes
  `location.pathname`, and existing callers stay valid.
- The `/` alias runs before the fill, so `/` lands on `/portfolio` and then fills "Last month". `portfolioHub.test`
  asserts it.

**I4. The bar's words for a declared span** (`spec-period.md` P.1 "Top bar" column; reviewer-guide Q2). Low.
- The spec quotes "This page shows part of it". The bar renders `Showing {span} of the range` (`SharedRangeBar.tsx:63`,
  `:297`).

*Default:* keep the bar's existing words. The P.1 column is a paraphrase, and H6 checks `data-shared-range-focus="inside"`,
not the text.

**I5. Names in P.5 and P.6 that do not exist** (`spec-period.md` P.5, P.6). Low.
- `tile1_target` and `tile2_split` are `W.tile_target` and `W.tile_split`.
- The status line's "`standing_short` then `status_disagreement`" is one statement already: `W.status_line(as_of,
  reconciled, disagreeing, names)`, whose parts are those keys.
- `deep_dive.refused` has only `BAD_MONTH` and `DEEP_DIVE_UNAVAILABLE`.

*Default:*
- Call the existing helpers. `status_line` is `W.status_line(latest as_of, S.reconciled, union of disagreeing in the
  latest month's asked order first, names)`.
- E2 and E1 refuse 422 with `portfolio_period.refused` (the two P.6 error texts) through their own small helper.
  `_refused` keeps 503.

**I6. Test fixtures and names** (`spec-period.md` P.7, P.8 test 5). Low.
- "`test_deep_dive_api.py`'s fakes" are in `backend/tests/test_5c_deep_dive_api.py` (`client(...)`, the snapshot and
  reconciliation fakes, `imported_sites`).
- `Served` has no `month` field (`structure_snapshot/model.py:108-112`). World P's September copy is
  `replace(served, snapshot=replace(served.snapshot, month="2026-09"))`.
- `SiteRef.domain` comes from `StoredSite.site_type` (`sites/foundation_records.py:72`).
- P.8 test 8 ("Mto's September target removed") is not described.

*Default:*
- Those fakes are used, and `_world_p()` is written as above.
- Test 8 replaces Mto's `SiteMonthSnapshot.targets` in the September copy with an empty target set, so Mto falls out of
  September's `R` with 5c's reason. The packet shows the resulting `R.k` (2 of 3).

**I7. E1's `SITES_SUM` assertion in production** (P.8 "One figure", test 4). Medium.
- The view raises `AssertionError("SITES_SUM")` when the compared rows do not sum to `R.effect`.
- `R.effect` is None in the currency-mismatch world (`deep_dive_worlds.py` World X), and a raise in the route is a 500 on
  a page that should degrade.

*Default:*
- The check runs only when `R.effect` and every compared effect are not None.
- In the route an `AssertionError` is a 503 `DEEP_DIVE_UNAVAILABLE`, logged with the month. In tests it raises.
- Test 4 keeps the raise, and test 4b checks World X: no raise, and every row's gap reads "Not available yet".

**I8. Decision targets by Ref kind and vertical** (spec §5.2 decisions row; D-IAP.3; `findingIndex.tsx:366-375`). Medium.
- The decisions row links `link_refs.finding` with view `recommendation`.
- A `FUEL_FINDING` Ref has its own page and no `recommendation` view (`operatorSiteRoutes.ts:637`).
- A cold-chain or EV `FINDING` is live only with a windowed Ref (`findingLinkLive`), and that check needs the mini-grid
  Site ids from `/api/sites`. The spec's rule, "absent ref, text only", is looser than today's rule.

*Default:*
- Decisions and Findings rows use `findingLinkLive` (exported, with the Site directory from the shared cache).
- `recommendation` is added only to a `FINDING` Ref of a mini-grid Site. A `FUEL_FINDING` row links its own page, and a
  cold-chain or EV row links its windowed Finding page.
- A row that fails the check is text with "Detail not available yet".

**I9. `loadAllPages` when a later page is refused** (spec §4.1; `estateClient.ts:600`, `FIRST_PAGE_CODES`). Medium.
- A cursor carries `page_one_mode` and a `selection_token`. Page k > 1 can return `ESTATE_BASIS_CHANGED` or
  `INVALID_CURSOR`.
- The Portfolio body's `summary`, `progress` and `scope_disclosure` come with page 1. The spec does not say which page
  they come from.

*Default:*
- On a `FIRST_PAGE_CODES` refusal, restart once from page 1. A second refusal shows `EstateRefusal` for the list, with
  its retry.
- The body-level fields are page 1's. Only `rows` are concatenated.

**I10. Site tab lighting for the eight `current="Findings"` call sites** (spec §2.3, §6 P5; `SiteAnalyticsFrames.tsx:550,
573, 582, 808, 827, 868, 1075, 2726`). Medium.
- Three are the Site Findings index (mini-grid, EV, cold-chain). Five are Finding pages (`SiteFindingFrame`,
  `CanonicalMiniFinding`, `SiteFuelFindingPage`), which become object pages.
- `SITE_TAB_OF` has no `Findings` entry. If the parity test fails for a vertical, that vertical's index stays (no alias),
  and no tab lights on it.

*Default:*
- Finding pages draw no tab row (object pages).
- A Site Findings index kept for a failed vertical lights Evidence, and its section line reads "In Evidence: Records ·
  Uploads · Findings" until the alias ships. This is MD-IAP-8b, flagged in the packet.
- The domain-action verification pages (`SITE_MILL_VERIFICATION_ROUTE_PATH`, `SITE_FUEL_VERIFICATION_ROUTE_PATH`) are
  object pages with home "Actions".

**I11. Fixtures for `iap_gates.cjs`** (spec §6 gates R3, L1 to L3, H1 to H6, S1, T1, T2, W1, K1). Medium.
- The gates answer `/api/*` from `fixtures/iap/`. Only the three period fixtures are named.
- T1 and T2 open a Site page per vertical, and those frames read the Site detail plus vertical reads (cold site, cold
  assessment, EV site, findings, actions). The estate, directory and E1 bodies are not named either.

*Default:* the fixtures are:
- `estate-portfolio-2026-10.json`, `estate-findings-2026-10.json` and `estate-actions-2026-10.json`, copied from
  `fixtures/w3-02` and trimmed;
- `sites-directory.json` (Kobo, Kisiwa, Mto, Thika, Ruiru);
- the R8 E1 fixtures;
- `site-{mini,cold,ev}/*.json`, taken from the existing vitest fixtures of the Site frames.

Any other `/api/*` answers 404, and T1 and T2 assert the tab row and the crumb, which draw before the vertical reads
resolve. The packet lists each fixture with its source.

**I12. IA-2b1 is not on `main`** (spec "Read first"; `git log main..task/IA-2b1-lists` is 53 commits). Medium.
- `HomeList` "is IA-2b §3 transcribed", but the binding text is on an unmerged branch that can still change.

*Default:*
- P2 transcribes IA-2b rev 2 as at `task/IA-2b1-lists` `b3102080c` and names that sha in the packet.
- A later IA-2b change is a mid-build question, not a silent re-sync.
- §3.4 and the Sites remainder follow R6.

**I13. Walk definition pin** (spec §6 P7, §8 WK; `backend/tests/test_wk_walk_world.py:1363`). Low.
`test_t11_smoke_pages` pins the `pages` list exactly, so P7's added pages fail it. The reviewer-guide's diff scope omits
this test.
*Default:* P7 updates `test_t11_smoke_pages`' literal list in the same commit as `walk-layer4-v1.json`, and the diff scope
gains it.

**I14. `Results.tsx` and its test are new** (spec §6 P3b "as in rev 1"). Low.
`estate/Results.tsx` does not exist on `main`.
*Default:* a new frame, `PageHeader` "Results" and "What changed in this review", then `ProgressPanel` moved verbatim,
reading the estate portfolio for the range, page 1 only. `Results.test.tsx` is new.

**I15. Rail icons differ from vNEXT `IA_RAIL`** (spec §2.1; `ia-routes.js:53-67`). Low.
- The mock uses Decisions `finding`, Plan `action`, Results `evidence`, and Evidence & records `log`.
- §2.1 uses `decide` (new), `clock`, `book` and `evidence`, with no deviation row.

*Default:* follow §2.1 and add MD-IAP-14 (D4, the live icon set; `decide` is new because two items cannot share
`finding`). This avoids an unlabelled departure.

**I16. `railHomeOf` and the navigation-truthfulness pin** (spec §5.1; `navigation-truthfulness.ps1:649-669`). Low.
- The guard pins the full `railActiveLabel` source line inside `OperatorShellLayout.tsx`.
- `railHomeOf` lives in `iaRoutes.ts`, so the pin must move files, not only change its pattern.

*Default:*
- The guard pins the call form in `OperatorShellLayout.tsx` and the `export function railHomeOf` signature in
  `iaRoutes.ts`.
- The planted extra live item is shown failing first (spec), and also a planted `activeLabel={null}`.

## Severity count

High 3 (R1, R2, R3). Medium 13 (R4 to R8, I1, I2, I7 to I12). Low 9 (R9, I3 to I6, I13 to I16). 25 in all (9 R, 16 I).
R1 is a stop: until the cap is ruled, P3b's H4 and H6 and P4's S1 cannot pass in a browser.

## Answers (Architect)

Architect (Claude), 2026-11-22. All 25 questions are answered, and the spec is now rev 3. The rulings are D-IAP.24 to D-IAP.33. Owner
answers on `main` (`owner/owner-iap-q1-q2-kobo-datasheets-2026-11-22.md`): Q9 "Last month" and Q10 "Month by month". Both
stand (D-IAP.33), and nothing below reverses them. Two new owner questions, Q11 and Q12, carry defaults and do not block
the build.

**R1 (High): accepted, with a central design (D-IAP.24; `spec-period.md` P.9; new unit P0).** Q10 is kept.
- **The cap.** The shared range accepts up to 731 days (`RANGE_MAX_DAYS`). A 731-day range holds at most 24 whole months,
  so E2's 24-month cap is never the first limit a range hits.
- **Whole-range pages.** `/portfolio`, `/portfolio/outcomes` and `/sites` (`WHOLE_RANGE_PAGES`) send the whole range to E2
  and E1.
- **Every other read** keeps its server's 31-day cap. It reads `readWindow(params)`, the last 31 days ending at `to`
  (equal to the range at 31 days or fewer). It is one helper in `sharedRange.ts`: `to` is kept, and `from` becomes
  `max(from, to − 30 days)`. This is a sweep of every raw `get("from")`/`get("to")`: 35 call sites, plus the 10 helper
  users. A static vitest guard fails on any `get("from")` or `get("to")` outside `sharedRange.ts`.
- **The bar** declares that window itself on every non-whole page where the range is over 31 days and the page declared
  no span of its own. It uses its existing words, "Showing {span} of the range". No page needs its own declaration.
- **Mixed pages.** On a whole-range page, a block fed by a capped read (Overview L2, Outcomes L3, the Sites "Waiting for
  a choice" column, the inbox and search) carries `RangePartNote` with the same words beside the block or in the column
  header.
- **Why this is honest.** Every page still says exactly which days it shows. Showing the whole range on every page needs
  every 31-day read raised: estate, Site, cold, EV, actions and source health. That is a cross-system change with unknown
  query cost, so it goes to the owner as **Q12**. Default: IA-P ships the labelled window, and a measured cap-raise task
  is queued after IA-P.

**R2 (High): accepted (D-IAP.25).**
- The period body's tile 1 keeps 5c's `W.sites(k, n)` line, with `k` and `n` from the latest served month.
- The headline gains the suffix `portfolio_period.compared` "Compared for {k} of {n} Sites." when `k < n` in any served
  month, using the latest month's `k` and `n`.
- Each month row gains `sites` (5c's `W.sites` for that month).
- P.7 adds test 11, World G with a September copy: the suffix, the tile line, and each row's "3 of 4 Sites".
- P.8 test 2 is World G. A vitest matrix test asserts that the Overview, Outcomes and the Sites list each name Thika on a
  one-month and a two-month fixture.

**R3 (High): accepted in part (D-IAP.26, MD-IAP-12, owner Q11).**
- **Confirmed: there is no cold-chain or EV monthly figure source.** Snapshots are built for MINI_GRID only
  (`structure_snapshot/read.py:60`, D-3B6.6). The EV and cold structures exist, but no snapshot or target is served for
  them. So the mock's cost-kind cell ("Cost per required departure met") has no live source, and E1 does not get a second
  kind in IA-P.
- **The row now says why, by Site type.** A cold-chain or EV row's Contribution cell reads `portfolio_sites.no_figures`
  "No monthly figures for {domain word} Sites yet". Gap and driver read "Not available yet", and the row has no gap
  word. A mini-grid Site that is not compared keeps "Not available yet", with 5c's reason in the Overview.
- **The range rule.** The page is not empty for these Sites:
  - the row's "Waiting for a choice" is range output;
  - the row's link opens the Site Overview, which follows the range for every type;
  - Outcomes L3 shows the range category cards and objectives for every type.
  What is missing is one quantity: monthly money against target.
- **MD-IAP-12 (D1).** Its resolving unit is "monthly figures for cold-chain and EV" (a cost-kind snapshot and targets),
  which is not specified yet. Whether to build it is **Q11** for the owner. Default: state the gap now, and specify the
  unit after IA-P when the owner schedules it.

**R4: accepted (D-IAP.27).**
- `iaRouteMap.test.ts` holds §2.4's "Current address" column as its own literals and asserts both directions: (a) every
  route path matches an `IA_HOMES` pattern or a live `LEGACY_ROUTES.from`; (b) every §2.4 literal resolves to a route or a
  live alias.
- The `routemap` plant fails (a), and the `alias` plant fails (b).

**R5: accepted (D-IAP.28).**
- `{months}` follows `span`'s year rule over the months the sentence names, so test 4 reads "September".
- `suggest` keeps `month_words` with the year ("Show October 2026").
- Test 6 is written out in P.7: "November is only partly in this range, so it is not counted: the figures are kept by
  whole month."

**R6: accepted (D-IAP.28, MD-IAP-13).**
- The Sites "Gap to target" tile shows `total.gap` only at scope `all` with no facet and no `q`. Otherwise it reads "Not
  available yet", with the line "For every Site only".
- The More line is "Not shown: {h} Sites." with no figure. IA-2b §3.4's re-formatting is not transcribed: E1's strings are
  shown as served.

**R7: ruled (D-IAP.29).**
- A placed Finding in `MONITOR` with no Action is not a choice waiting. Its State is `watching`, "Being watched", a third
  facet option.
- `waiting` is `action_id` null and placement not `MONITOR`. `NEEDS_INVESTIGATION` stays waiting, because choosing to
  investigate is a choice.
- E0's `waiting_count` and `waiting_by_site` use the same rule, with an added test: a `MONITOR` member is not counted.
- The badge, tiles and inbox follow, and MD-IAP-2's note gains the third word.

**R8: accepted.** P.8 test 9, "Fixtures current": `fixtures/iap/sites-2026-10.json`, `sites-2026-09-10.json` and
`sites-none-2026-11.json` equal `sites_view` for tests 1, 7 and 3, and the E0 fixture's `waiting_by_site` keys are E1's
codes.

**R9: accepted.** P.8 test 1 also asserts that each compared row's `gap` equals its Site's `by_site` Gap cell in October's
`month_view`, string for string.

**I1: accepted.** `MonthNav` reads only E2's `nav`, and with `next` null it draws no next control. `MONTHS`, `monthWords`
and `monthAfter` are deleted. The nav assertion update is named in the packet.

**I2: accepted.** The test imports `operatorSiteRoutes.ts` to resolve each `{IDENT}`, reads the array literals before each
`.map`, and takes the Lab paths from `simulatorLabRoutes(stub)`. An unresolvable `path={…}` fails the test.

**I3: accepted.** The signature is `entryRange(pathname?: string, now = Date.now())`, called with `location.pathname`. The
`/` alias runs before the fill, and `portfolioHub.test` asserts that `/` lands on last month.

**I4: accepted.** The bar keeps its words ("Showing {span} of the range"), and P.1's column is corrected to them. H6 checks
`data-shared-range-focus="inside"`.

**I5: accepted.**
- Use `W.tile_target`, `W.tile_split` and `W.status_line(latest as_of, S.reconciled, union of disagreeing (latest month's
  asked order first), names)`.
- E2 and E1 refuse 422 with `portfolio_period.refused` through their own helper, and `_refused` keeps 503.

**I6: accepted.**
- The fakes are `backend/tests/test_5c_deep_dive_api.py`'s.
- `_world_p()` uses `replace(served, snapshot=replace(served.snapshot, month="2026-09"))`.
- P.8 test 8 empties Mto's September `SiteMonthSnapshot.targets`. The packet shows September `R.k` = 2 of 3.

**I7: accepted.**
- The sum check runs only when `R.effect` and every compared effect are present.
- In the route, an `AssertionError` is a logged 503 `DEEP_DIVE_UNAVAILABLE`. In tests it raises.
- Test 4b uses World X: no raise, and every gap reads "Not available yet". The same applies to E2's period sums.

**I8: accepted.**
- Decisions and Findings rows link through `findingLinkLive`, exported and using the Site directory from the shared cache.
- `recommendation` is added only to a mini-grid `FINDING` Ref. `FUEL_FINDING` links its own page, and cold-chain and EV
  rows link their windowed Finding page.
- A row that fails the check is text, with "Detail not available yet".

**I9: accepted.** On a `FIRST_PAGE_CODES` refusal, `loadAllPages` restarts once from page 1. A second refusal shows the
list's `EstateRefusal` with its retry. The body-level fields are page 1's, and only `rows` are concatenated.

**I10: accepted (D-IAP.31, MD-IAP-15; the reviewer's "MD-IAP-8b").**
- Finding pages are object pages.
- A Site Findings index kept for a vertical whose parity test failed lights Evidence, and its section line reads "In
  Evidence: Records · Uploads · Findings" until its alias ships.
- The mill and fuel verification pages are object pages with home "Actions".

**I11: accepted.** The fixtures are the five sets the reviewer listed, each with its source in the packet. Any other
`/api/*` answers 404. The fixture base is built in P1 and grows with each unit.

**I12: accepted.** P2 transcribes IA-2b rev 2 at `task/IA-2b1-lists` `b3102080c`, named in the packet. A later IA-2b change
is a mid-build question.

**I13: accepted.** P7 updates `test_t11_smoke_pages`' list in the same commit, and the diff scope gains it.

**I14: accepted.** `Results.tsx` and `Results.test.tsx` are new: `PageHeader` "Results" and "What changed in this review",
then `ProgressPanel` moved verbatim, reading the estate portfolio's page 1 for the window.

**I15: accepted (MD-IAP-14, D4).** The icons stay as §2.1, the live icon set. `decide` is new because two items cannot
share `finding`.

**I16: accepted.** The guard pins the call form in `OperatorShellLayout.tsx` and `export function railHomeOf` in
`iaRoutes.ts`. Both plants are shown failing: the extra live item and `activeLabel={null}`.

**Size (D-IAP.32).** 14.0 units, in three parts, each under 6:
- **IA-P1** (P0, P1, P2): 4.5;
- **IA-P2** (P3a, P3b, P4a): 5.0;
- **IA-P3** (P4b, P5, P6, P7): 4.5.

Only IA-P2 touches `backend/assetops_backend`, so there is one rung rebuild after it merges.
