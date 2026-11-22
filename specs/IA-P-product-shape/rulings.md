# IA-P rulings (Architect, Claude, 2026-11-22)

Each ruling has its reason. The owner asked for this spec on 22 Nov (`owner/owner-merge-on-accept-ia-shape-k10-2026-11-22.md`)
and reviews once the product is close to the shape. The open owner questions are spec §9 (Q1 to Q8, with the defaults
applied).

- **D-IAP.1 Scope and boundary.**
  - IA-P brings the real app onto the agreed shape for these parts: the menu, the Portfolio's three tabs and its Overview,
    the four home lists, the Site's six-tab row, "Waiting for you", scope and search.
  - The content of IA-2c, IA-2d and IA-2e follows the mock's own units: the real app does not run ahead of the mock.
  - The Plan is an unavailable rail item, because the live product has no plan record. Showing the pack's modelled plan as
    live would present modelled figures as the operator's own (an owner product rule).
  - Reason: the owner named exactly these three things (Portfolio, live lists, a home for the month), and "no screen lost"
    needs every other route mapped, not rebuilt.

- **D-IAP.2 The month is the Portfolio Overview.**
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

- **D-IAP.9 E1, `GET /api/portfolio/sites`.**
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

- **D-IAP.12 The old Overview's content, re-housed.**
  - The range category cards (with 1a's line) go to Outcomes L3. The objectives matrix goes in a disclosure there from P4.
  - The top three becomes Overview L2: Decisions rows, for the month's bounds, at most 6, then "View all {n}" carrying those
    bounds.
  - The pulse is retired: each of its links has a menu item or tab now, and the mock's Overview has no pulse.
  - The coverage line and the scope disclosure go to Evidence & records › Coverage. What changed goes to Results.
  - Reason: proposal §6 and the owner's rule to move reviewed constructs, not drop them.

- **D-IAP.13 Units and gates.**
  - The units run in the order P1 to P7, in two parts:
    - IA-P1 is P1 to P3 (3.75 units); its review follows P3;
    - IA-P2 is P4 to P7 (4.75 units); its review follows P7.
  - Each unit is 1 to 3 commits and leaves the app working.
  - `tools/iap_gates.cjs` (fixtures through `page.route`) and the route-map test are written first and grow each unit.
  - Plants are one-line edits shown failing.
  - Discovery review per part: P4 adds a money figure and an endpoint.

- **D-IAP.14 Ladder, WK and DDR.**
  - Only P4 changes `backend/assetops_backend`, so only P4 stales the world key (`CODE_PATHS`). The coordinator rebuilds
    the current rung once after P4 merges, before the next WK run.
  - The walk pages all still land (the month path through its alias). P7 adds the new pages to
    `walk-layer4-v1.json`.
  - DDR's S7 browser path is aliased; its runbook text is updated in P3.
