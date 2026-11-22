# IA-P rulings (Architect, Claude, 2026-11-22)

Each ruling has its reason. The owner asked for this spec on 22 Nov (`owner/owner-merge-on-accept-ia-shape-k10-2026-11-22.md`)
and reviews once the product is close to the shape. The open owner questions are spec §9 (Q3 to Q10, with the defaults
applied). Q1 and Q2 were answered on 22 Nov (D-IAP.15). Rev 2 rulings are D-IAP.15 to D-IAP.23, and rev 3 rulings (the handshake) D-IAP.24 to D-IAP.33, at the end.

- **D-IAP.1 Scope and boundary.**
  - IA-P brings the real app onto the agreed shape for these parts: the menu, the Portfolio's three tabs and its Overview,
    the four home lists, the Site's six-tab row, "Waiting for you", scope and search.
  - The content of IA-2c, IA-2d and IA-2e follows the mock's own units: the real app does not run ahead of the mock.
  - The Plan is an unavailable rail item, because the live product has no plan record. Showing the pack's modelled plan as
    live would present modelled figures as the operator's own (an owner product rule).
  - Reason: the owner named exactly these three things (Portfolio, live lists, a home for the month), and "no screen lost"
    needs every other route mapped, not rebuilt.

- **D-IAP.2 The month is the Portfolio Overview.** *(Amended by D-IAP.15 and D-IAP.18: the month exception and the
  month span are withdrawn; the Overview follows the range.)*
  - `/portfolio` renders 5c's month screen, and `/portfolio/month` aliases to it, keeping `?month=`.
  - The page declares the month's span through SR-4c (`useDeclareRangeSpan`). The month links stay in the hub header.
  - Reason: the mock's Overview is this screen (5c MD7 names this rebuild as its resolving unit), and two front pages would
    show the portfolio's contribution twice (the owner's one-figure rule).
  - Alternative (spec §3): a fourth tab.
  - The range-rule exception is Q2, for the owner.

- **D-IAP.3 The interim decision source.**
  - Until 6a's decision records exist, a decision is a placed Finding from the estate Portfolio read. It is "waiting" when
    no Action is agreed (`action_id` null), and "under way" otherwise.
  - Its page is the Finding's `recommendation` view (with `alternatives`), lit under Decisions.
  - Reason: the proposal maps Act first to Decisions, and the reviewed placement queue is an existing construct aligned with
    it (owner: extend, don't drop). Accepting a recommendation is the live choice that creates an Action.
  - 6f replaces the source (MD-IAP-2, D1).

- **D-IAP.4 The registry, the landed rule, aliases and paths.**
  - `shell/iaRoutes.ts` holds `IA_LANDED`, `IA_HOMES` (rail lighting and tab group per address family) and
    `LEGACY_ROUTES`.
  - An alias is live only when its unit has landed.
  - A redirect keeps the query (the range first) and, where marked, the sub-path.
  - Menu and Portfolio routes take the IA names. Site sub-paths keep today's segments, with the labels changed (Q5).
  - Every tab link carries the address range.
  - Reason: this is IA-1 §2.2's mechanism, in the live router's terms. Renaming 30+ Site paths buys nothing the owner sees.
  - The route-map test is the "no screen lost" control.

- **D-IAP.5 The menu.** It takes D-IA.1's groups, order and labels. "Operational records" merges into Evidence & records ›
  Records. Decisions goes live in P2 and Results in P3. `railHomeOf` replaces `railActiveLabel`. The navigation-truthfulness
  guard is re-pinned and shown failing on a plant.

- **D-IAP.6 One list component.**
  - `ui/HomeList.tsx` is IA-2b §3 transcribed (tiers, chips, the address as the view, cap 10 and "Show all", one target per
    row, text-only cells). It serves Decisions, Findings, Actions and Sites, and the hub rows (`cap`).
  - Lists read every page through a shared cache (at most 1,000 rows, stated beyond that), so the tiles equal the list.
  - A row without a server ref is shown as text, never dropped.
  - Reason: one interaction grammar, and exposure that scales from 3 to 300 Sites (standing brief).

- **D-IAP.7 The Site's six tabs.** Today's eight tabs fold into six:
  - Foundation, Changes and Assets go to Setup;
  - Health goes to Performance;
  - Work goes to Operations;
  - Uploads go to Evidence;
  - Findings leaves the row (`/findings?scope=site:`), behind a parity test.

  Finding and Action detail pages are object pages: no tab row, and a crumb of home list › Site › title (D-IA.9). Reason:
  D-IA.3. The parity test guards the one fold that changes a read.

- **D-IAP.8 E0, additive.** `summary.waiting_count` and `waiting_by_site` are added on `/api/estate/portfolio`, over the
  same members as `placement_counts`, counting members with no matched Action. Reason: the Sites list's "Waiting for a
  choice" needs a per-Site count across pages. The server already holds the rows; the browser must not count a partial page.

- **D-IAP.9 E1, `GET /api/portfolio/sites`.** *(Amended by D-IAP.20: it takes `from` and `to`, not `month`.)*
  - It is the Sites list and the Outcomes rows: every registry Site, ordered on the server by gap (most adverse first),
    then the not-compared Sites last.
  - Its strings come from SC-1 `portfolio_sites.*`. The largest driver is the most negative STEPS row.
  - The compared Sites' gaps sum exactly to the Overview's gap, and `total.gap` is tile 2's string. A break is a bridge
    fault, fixed there.
  - It covers contribution kind only, the only kind live.
  - Reason: sorting and choosing the largest driver are comparisons of figures, which the browser never makes (D-5C.2). One
    figure per quantity across the Overview, Outcomes and Sites.

- **D-IAP.10 "Waiting for you."**
  - The badge and "In your portfolio" show the waiting decisions. "For you" is not available yet: who decides is not
    recorded until 6a, and nothing is attributed to a person falsely.
  - "Since you last looked" shows the 3 newest `progress.rows`, linking to Results.
  - It uses one read (shared cache), refreshed when the range changes.

- **D-IAP.11 Scope and search.**
  - Scope follows IA-1 §2.3 and IA-2b §3.3: lists filter, and on a list a Site entry scopes it. Elsewhere a Site entry
    opens the Site. The Overview states that it shows every Site (MD-IAP-5, D5).
  - Search covers Sites, decisions, Findings, Actions and live rail items. It is lazy, through the shared cache, with words
    ANDed and 20 results shown.

- **D-IAP.12 The old Overview's content, re-housed.** *(Amended by D-IAP.18: the L2 rows are for the range.)*
  - The range category cards (with 1a's line) go to Outcomes L3. The objectives matrix goes in a disclosure there from P4.
  - The top three becomes Overview L2: Decisions rows, for the month's bounds, at most 6, then "View all {n}" carrying those
    bounds.
  - The pulse is retired: each of its links has a menu item or tab now, and the mock's Overview has no pulse.
  - The coverage line and the scope disclosure go to Evidence & records › Coverage. What changed goes to Results.
  - Reason: proposal §6 and the owner's rule to move reviewed constructs, not drop them.

- **D-IAP.13 Units and gates.** *(Sizes amended by D-IAP.22.)*
  - The units run in the order P1 to P7, in two parts:
    - IA-P1 is P1 to P3 (3.75 units); its review follows P3;
    - IA-P2 is P4 to P7 (4.75 units); its review follows P7.
  - Each unit is 1 to 3 commits and leaves the app working.
  - `tools/iap_gates.cjs` (fixtures through `page.route`) and the route-map test are written first and grow each unit.
  - Plants are one-line edits shown failing.
  - Discovery review per part: P4 adds a money figure and an endpoint.

- **D-IAP.14 Ladder, WK and DDR.** *(Amended by D-IAP.22: P3a also stales the key.)*
  - Only P4 changes `backend/assetops_backend`, so only P4 stales the world key (`CODE_PATHS`). The coordinator rebuilds
    the current rung once after P4 merges, before the next WK run.
  - The walk pages all still land (the month path through its alias). P7 adds the new pages to
    `walk-layer4-v1.json`.
  - DDR's S7 browser path is aliased; its runbook text is updated in P3.

## Rev 2 (Architect, Claude, 2026-11-22; owner answers `owner/owner-iap-q1-q2-kobo-datasheets-2026-11-22.md`)

- **D-IAP.15 The owner's answers to Q1 and Q2.**
  - Q1, "Month is the Overview": D-IAP.2 stands. `/portfolio` renders 5c's screen, with no fourth tab.
  - Q2, "Follow the date range": the Overview follows the top-bar range like every other page. Rev 1's exception (a
    calendar month whatever the range, with its SR-4c month span and the server's default month) is withdrawn.
  - Both leave the spec §9 queue as answered.

- **D-IAP.16 The period rule.**
  - The Overview counts the whole, closed calendar months inside the range.
  - A month the range only touches (PARTIAL), or holds but which has not closed (OPEN), is named and not counted. A whole
    month with no served snapshot is named as missing.
  - The modes are `none` (no served month), `month` (one) and `period` (two or more). The cap is 24 months, and
    `known_at` does not re-cut the snapshots.
  - Reason: targets and management accounts exist per month and there is no daily snapshot. Cutting by day would invent a
    target split, which breaks the honest-numbers rule. Counting every whole month and naming the rest gives output for
    the range wherever the data can carry it (the owner's range rule).
  - Spec: `spec-period.md` P.1, P.2.

- **D-IAP.17 E2, `GET /api/portfolio/period?from=&to=`, and the period body.**
  - The server resolves the range and returns the mode, the months, the notes, `shown`, `nav` and `suggest`. In mode
    `period` it also returns a body.
  - The body sums the months' root rows and heading sums exactly, reusing 5c's `_View` per month. It is None on any
    missing term or mixed currency. Its word is the weakest, under the period standing (reconciled only when every month
    is).
  - A month row's gap is that month's tile 2 string.
  - Reason: effects add across months as 5b's rule makes them add across Sites. Resolving months and days, and summing,
    are server work: the browser never compares or adds a figure (D-5C.2), and it never types a month.
  - 5c's month read is unchanged.

- **D-IAP.18 The hub on the range.**
  - Mode `month` renders 5c's screen for E2's month, with ‹ › from E2's `nav` setting the range. Mode `period` renders the
    period hub ("Month by month" in L3, MD-IAP-10). Mode `none` renders the notes, "Show {month}" and L2 (MD-IAP-11).
  - The page declares an SR-4c span only when E2's `shown` is not null, so the bar says "This page shows part of it"
    exactly when the counted months differ from the range.
  - Overview L2's Decisions rows are for the range.
  - `/portfolio/month?month=` aliases to that month's range, and `month` wins over a range in the address.
  - Reason: one page, one period, the same as the bar. The DDR, WK and bookmarked month addresses still land on their
    month.

- **D-IAP.19 Range pages: the class fix.**
  - Every IA-P page whose content follows the range joins `RANGE_PAGES` and `FILLED_PAGES` in the unit that lands it:
    `/evidence/records` (P1), `/decisions` (P2), `/results` (P3b) and `/sites` (P4).
  - Reason: rev 1 added these pages without the bar's registry, so the bar would have said the range is not used on pages
    that use it. The sweep covers every new route in spec §2.4.

- **D-IAP.20 E1 follows the same period.**
  - E1 takes `from` and `to` and uses E2's resolver and header.
  - In mode `period` a row sums the months in which its Site is compared, with "Compared in k of m months" when fewer than
    all. The compared rows sum to the period's effect, and `total.gap` is the Overview's tile 2 for the same range.
  - Reason: the one-figure rule across the Overview, Outcomes and Sites for any range. The Outcomes tab no longer mixes a
    month (L1, L2) with the range (L3).

- **D-IAP.21 A fresh Portfolio entry opens on last month.**
  - With no range in the address and none stored for the session, `/portfolio` (and `/` through its alias) fills "Last
    month" instead of "Last 7 days". Other pages keep "Last 7 days".
  - Reason: a 7-day range holds no whole month, so the front page would open on notes. "Last month" is a WARM-1 preset,
    so it stays warm.
  - The owner may veto: spec §9 Q9.

- **D-IAP.22 Units, sizes and the ladder (rev 2).** *(Superseded by D-IAP.32.)*
  - P3 splits into P3a (E2, 1.5) and P3b (the hub on the range, 1.75), and P4 grows to 2.0.
  - IA-P1 is 5.75 units and IA-P2 is 5.0, 10.75 in all, each under the 6-unit cap.
  - P3a and P4 both change `backend/assetops_backend`. The coordinator rebuilds the rung after each part merges before
    the next WK run, or once if both merge first.
  - IA-P1's review is now discovery-depth for a money endpoint too.

- **D-IAP.23 Kobo stays Simulated (owner, 22 Nov).**
  - IA-P renders Kobo's figures on the Overview, the month rows and the Sites rows. Each takes its word through 5c's
    `figure_word`/`W.word` from the served evidence. So a Kobo figure carries the same word on every surface, the word its
    evidence gives on 5c's screen today. IA-P adds no label of its own.
  - No IA-P change follows. The data sheet replacement is the owner's prospect ask (0K4f), outside IA-P.

## Rev 3 (Architect, Claude, 2026-11-22; the handshake, `handshake.md` "Answers (Architect)")

- **D-IAP.24 The long range (R1).**
  - The shared range accepts up to 731 days, so a 731-day range holds at most 24 whole months (E2's cap).
  - The Overview, Outcomes and Sites read the whole range (E2, E1). Every other read takes `readWindow`: the last 31
    days ending at `to`. The bar declares that window automatically ("Showing {span} of the range"). A capped block on a
    whole-range page carries `RangePartNote`, and links carry the whole range.
  - A static guard forbids raw `from`/`to` reads outside `sharedRange.ts`.
  - Reason: the owner's Q10 needs ranges over 31 days. The 31-day cap sits in about 15 server routes, so one central
    window plus a stated span is honest without a cross-system change. Raising the caps is owner Q12 (default: a
    measured task after IA-P).
  - Spec: `spec-period.md` P.9, unit P0.

- **D-IAP.25 The period body names the Sites it does not compare (R2).**
  - Tile 1 keeps `W.sites(k, n)`, and the headline gains "Compared for {k} of {n} Sites." when `k < n` in any month.
  - Each month row carries its `sites`.
  - World G tests cover the period view, E1 and the frontend matrix.
  - Reason: the page × Site-type rule. A cold-chain or EV Site never vanishes from a page without a word.

- **D-IAP.26 Cold-chain and EV rows state why they have no figure (R3).**
  - Monthly snapshots are MINI_GRID only (D-3B6.6). So E1's row for a cold-chain or EV Site reads "No monthly figures
    for {type} Sites yet", not the bare "Not available yet".
  - The row's range output is its "Waiting for a choice" and its link to the Site Overview. Outcomes L3 gives every type's
    range objectives.
  - MD-IAP-12 (D1) is registered. Building the figures is owner Q11; the default is to specify them after IA-P.
  - Reason: honest numbers. The mock's cost-kind cell has no live source, and inventing one would break the one-figure
    rule.

- **D-IAP.27 The route-map test runs both ways (R4, I2).**
  - It holds §2.4's addresses as its own literals and resolves route constants, `.map` arrays and the Lab routes.
  - It fails when a route has no home, when a §2.4 address has no route or alias, and when a `path` cannot be resolved.

- **D-IAP.28 Words and one-figure pins (R5, R6, R8, R9, I7).**
  - Month names in the notes follow `span`'s year rule.
  - The Sites gap tile shows the server's total only at scope `all`, unfiltered (MD-IAP-13), and the More line carries no
    figure.
  - The E1 fixtures are kept current by a test.
  - E1's Site gap equals 5c's `by_site` cell.
  - The sum checks degrade to a logged 503, never a 500, and are skipped when a term is absent.

- **D-IAP.29 `MONITOR` is not waiting for a choice (R7).**
  - A placed Finding in `MONITOR` with no Action is `watching`, "Being watched". `waiting` excludes it, while
    `NEEDS_INVESTIGATION` stays waiting.
  - E0, the tiles, the badge and the inbox use the same rule.
  - Reason: the badge must count only choices waiting for an executive (honest numbers).

- **D-IAP.30 Implementer clarifications adopted (I1, I3, I4, I5, I6, I8, I9, I11, I12, I13, I14, I16).** Each is as
  answered in `handshake.md`:
  - the month nav comes from E2 only, and the typed months are deleted;
  - `entryRange(pathname?, now)`;
  - the bar keeps its words;
  - the existing `W` helpers are used, with a `portfolio_period.refused` 422;
  - World P comes from `replace(snapshot)`;
  - links go through `findingLinkLive`;
  - `loadAllPages` restarts once;
  - the fixture sets are named;
  - IA-2b is pinned at `b3102080c`;
  - the walk test list is updated;
  - `Results.tsx` is new;
  - the navigation guard pins both files.

- **D-IAP.31 Site lighting and icons (I10, I15).**
  - Finding pages and the mill and fuel verification pages are object pages.
  - A Findings index kept for a failed parity vertical lights Evidence (MD-IAP-15).
  - The rail keeps the live icon set (MD-IAP-14).

- **D-IAP.32 Rev 3 units and parts.**
  - P0 (the long range, 1.0) is added, and P4 splits into P4a (E0 and E1, 1.5) and P4b (the Sites list and Outcomes,
    1.25).
  - Three parts: IA-P1 is P1, P0 and P2 (4.5); IA-P2 is P3a, P3b and P4a (5.0); IA-P3 is P4b, P5, P6 and P7 (4.5).
    That is 14.0 units in all, each part under 6.
  - Only IA-P2 touches `backend/assetops_backend`, so there is one rung rebuild after it.
  - Supersedes D-IAP.22's sizes and ladder.

- **D-IAP.33 The owner's answers to Q9 and Q10 (22 Nov).**
  - Q9 "Last month": D-IAP.21 stands.
  - Q10 "Month by month": MD-IAP-10 stands.
  - Both leave the queue. R1's answer keeps Q10 reachable.
