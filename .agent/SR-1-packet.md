# SR-1 packet: shared date range bar and state (card B4)

Branch `task/SR-1-shared-range` (wt `AssetOpsV1-sr1`, from main `bfe609500`). Build commit `c984af785`.
Spec: `.agent/architect-sequence-client-scope-2026-11-11.md` C.7 B4; proposal 2026-11-10 "Item 12.5", SR.3, SR.4;
layout `frontend/mockups/v71/portfolio-tabs.html` Change 0b; D-UI.2 (range in the address only).

## What changed
- `shell/sharedRange.ts` (new): `useSharedRange()` -> `{status:"set", from, to, known_at, preset}` | `absent` | `invalid`;
  reads both address forms (day form `from=2026-09-30&to=2026-10-06`, `to` included; instant form, `to` excluded).
  Invalid = one bound, unparseable, from after to, >31 days, bad `known_at` (never echoes dates).
  `presetRange`/`presetOf` (Yesterday, Last 7 days, Last 30 days, This month, Last month, Custom; no Today; full UTC
  days ending yesterday). `rangeSearch`, `withRange(path, params)` (a path with its own range keeps it; page-only
  params such as `cursor`, `lens`, `day` never travel). `fillsRangeOnEntry`, `entryRange` (sessionStorage last range,
  else Last 7 days; storage errors fall back), `rememberRange` (days only).
- `shell/SharedRangeBar.tsx` + `sharedRangeBar.css` (new): button naming the whole state (`aria-expanded`,
  `aria-controls`), "All pages" tag, non-modal labelled dialog, `aria-pressed` presets, labelled custom date inputs,
  "View an earlier point in time", Apply/Cancel, Escape/Cancel return focus, polite live region, "As known at {time} ·
  every page" + "Return to latest". Apply keeps page params (e.g. `lens`) and drops `cursor`. Phones (<=760 px): dates
  only, 44 px button, bottom sheet (85vh, scrolls), as-of label on its own line.
- `shell/OperatorShellLayout.tsx`: new sticky `<header class="app-topbar">` row with the bar, above the demonstration
  banner (kept); rail gets `search={railSearch}`; the outlet is `SharedRangeOutlet`, which on an estate address with
  no range renders `<Navigate replace>` to the filled address before the page mounts (one read, for that range).
- `ui/NavRail.tsx`: optional `search` added to every live item's href; matching stays on the path.
- `estate/estateShared.tsx`: `queryFromParams` maps the day form to the same UTC instants (instant addresses
  unchanged); new `EstateCutoffLine` (cutoff, earlier-cutoff words, `Window not valid` on a refused window, UTC note).
- `estate/EstatePortfolio.tsx`: PF-T's `EstateDateBar` replaced by the cutoff line under the title; PF-T-1 closed.
  One mounted `/portfolio/:tab?` route, no refetch on tab switch, tab links carry `from`/`to`/`known_at`: unchanged.
- Guard: `navigation-truthfulness.ps1` requires `search={railSearch}` with `railSearch = rangeSearch(params)`;
  `navigation-rail-fixtures.ps1` gets two cases (search dropped; search = raw `location.search`).

## API request shapes (demo pre-built routes)
Unchanged for any instant-form address (all `story_links`/prebuilt links): estate pages still send the same
`from`/`to`/`known_at`. The bar writes the instant form, so a range chosen in the bar reaches every page in the form it
already reads. Filling applies only on estate roots, whose fallback is the same default (S17), so a bare `/portfolio`
makes the same request as before. Work and Site pages are not filled and read nothing new.

## Mock deviations (header comment of `SharedRangeBar.tsx`)
- SR-1-1: the bar writes the instant form, not the short day form of SR.3 (keeps every page's request identical
  until SR-2 moves pages onto the hook). The hook and estate reads accept the day form.
- SR-1-2: the v7.0 top bar's estate name, "Find a screen" and avatar are not drawn (no data or route behind them).
- SR-1-3: picker note says "Days and times are UTC"; Site-local days arrive with SR-2. A page whose address has no
  range (Work, Site pages) shows "This page's own dates" on the button.

## Scope split (recorded, not decided for SR-2)
- Fill-on-entry covers the estate roots only (Portfolio + tabs, Findings + lens roots, Actions, Evidence,
  Financials). Work pages (R338 includes today) and Site pages (Site-local days, Cold/EV selected event) change their
  default in SR-2, so filling them now would change their requests and the demo's Site tab links.
- `withRange` is used by the rail only; tabs/breadcrumbs/row links switch in SR-2 (estate tab links already carry it).

## Tests (vitest, one file at a time)
- `shell/__tests__/sharedRange.test.tsx` (new, 18): both address forms, Custom + known_at, absent/invalid, presets
  (no Today, values match the mock's 7 Oct example), withRange/rangeSearch, rail links carry the range, bare rail
  without a range, fill on entry (default, session range, one read), filled-pages list, top bar above the banner + aria
  label, focus (selected preset, Escape, Cancel), Apply (lens kept, cursor dropped, live text, focus), custom
  validation, as-known-at + Return to latest, Window not valid, Portfolio reads day form = instant request and re-reads
  on Apply. Failed before the code (module missing), 18/18 after.
- Touched: `estatePortfolio` 85/85, `estatePortfolioRoutes` 4/4, `operatorRailInventory` 31/31, `operatorRouteFrames`
  22/22. Adjacent, unchanged: `w301EstateShellRoutes` 3/3, `t028Screens` 25/25, `estateRoots` 23/23.
- `tsc --noEmit`: clean.
- `tools\check-architecture.ps1` (ASSETOPS_GUARD_PYTHON = plan2 .venv) on `cbc8e5435`: "Architecture check passed."
  The first run failed: navigation truthfulness flagged the fill `<Navigate>` in `OperatorShellLayout.tsx` as a
  destination outside the inventory, so the redirect moved to `SharedRangeOutlet` in `SharedRangeBar.tsx` (same path,
  replace only). The two new rail fixtures (search dropped / raw `location.search`) fail the guard as expected inside
  that pass, which shows the new rail-search check can fail.

## Not run / risks
- No full suite, layout evidence or captures (brief). Layout (sticky row, 760 px sheet, 1100 px short label) is
  CSS-only, unmeasured.
- Other App-level tests that open an estate root without a range, or assert bare rail hrefs on a ranged Site
  address, may need their expectations updated (grep found none beyond the files above; not run).
- Other estate pages (Findings, Actions, Evidence, Financials) still show their own `EstateDateBar` under the shared
  bar until SR-2 removes it.
