# Review packet: DIESEL-K5 fuel screens (Fuel page night mode, fuel Finding page, Fuel checks panel)

Card: `.agent/build-sheet-DIESEL-1.md` §9l.2 (ruling DIESEL-1-R3l), with §9j.7 (K4a wording), §9m/§9m2
(`fuel_finding_ref`), §8.2 H1-H5. Branch `task/DIESEL-K5-fuel-screens`, worktree `AssetOpsV1-k5`, from main
`97505484a` (K4a merged `3358553f8`), so phases A and B were built together. USER_REVIEW: none required by the card;
owner walkthrough is the standing post-W6 one. **K5 merges only after the owed captures (below).**

## Outcome

- **Night mode** on Site › Performance › Fuel iff the Site has a stored `fuel-balance-1` window as known: a night
  selector (`<nav aria-label="Nights">`, option = server `label · status`, Previous/Next night disabled at the ends,
  `?night=YYYY-MM-DD`, latest night by default), the status bar (badge, provenance chips, notes), the four cards, the
  glance bars and chart note (+ K4a margin line), the five-row bridge, **Deliveries and tank dips**, the reworded notice
  (K4a's `FUEL_NOTICE`, imported) and **Finding for this night**. Hour mode otherwise, unchanged (Kobo).
- **Fuel Finding page** at `/sites/{code}/fuel-findings/{id}[?revision_id=]` (`SITE_FUEL_FINDING_ROUTE_PATH`,
  `siteFuelFindingHref`, Ref kind `FUEL_FINDING`, `refs.fuel_finding_ref`): Site header + Findings tab, status bar
  (lifecycle, night label, provenance), `BigClaim` (claim or no-longer), fact lines (gap, money, margin, not-why),
  "How the night was checked" (shared bridge + "Open this night on the Fuel page"), shared records table, "Versions".
- **Fuel checks** panel on the MINIGRID Site Findings index, after the dispatch table, only when rows exist.
- Four read routes (`backend/assetops_backend/fuel_balance_api.py`), all text server-composed
  (`fuel_balance/night_text.py`, K4a's `finding_text`); the browser formats no number.

## Commits (oldest first)

1. `ad0616e46` v69 fuel mock measurements (pre-build budgets) — `.agent/K5-mock-measurements.md` (+ json, png).
2. `c9e77abe3` reads, routes, `has_windows`, `FUEL_FINDING` ref, route fixture rows, L0/L2 tests.
3. `418cd75ec` frontend: night mode, fuel Finding page, Fuel checks panel, F1-F8 tests.
4. `4dde70a37` guard fixes: no hard-wiring rise (links through `linkFor`/shell builders, no Site-type compare);
   (a `$pgReaders` join here was reverted in 6).
5. `32723b79a` merge main (K6a `bda3c666e`); conflict in `test_out_b2_vocabulary.py`, both additions kept.
6. `34e064f2a` the two snapshot reads move into `PostgresFuelBalanceStore` (architecture guard: no storage technology
   above the adapter layer); `night_read.py` holds no driver import; no guard file changes remain.
7. the packet commit.

## Files

- New backend: `fuel_balance/night_text.py`, `fuel_balance/night_read.py`, `fuel_balance_api.py`;
  tests `test_k5_fuel_night_text.py`, `test_k5_fuel_night_api_postgres.py`.
- Edited backend: `fuel_balance/adapters/postgres_fuel_balance_store.py` (`has_windows`, `night_context`,
  `night_records_and_provenance`, all read-only; deviation 0), `main.py` (router),
  `chain/refs.py` (kind, `href_for` branch, `fuel_finding_ref`), `tests/test_out_b2_vocabulary.py` (literals only).
- New frontend: `sites/fuelBalanceClient.ts`, `sites/MiniFuelNights.tsx`, `sites/SiteFuelFinding.tsx`; tests
  `sites/__tests__/miniFuelNights.test.tsx`, `sites/__tests__/siteFuelFinding.test.tsx`.
- Edited frontend: `sites/MiniPerformance.tsx` (MiniFuel prop + branch only), `shell/SiteAnalyticsFrames.tsx`,
  `shell/operatorSiteRoutes.ts`, `sites/chainRef.ts`, `App.tsx`, `sites/SiteFindingIndex.tsx` (`fuelChecks` slot),
  `test/linkRefs.ts`, `shell/__fixtures__/route-refs.json` (2 rows), `shell/__tests__/routeRefs.test.ts` (kind list + F7).
- Guard allowlists: none changed (a `$pgReaders` join was tried and reverted, deviation 0).

## Pre-flight answers (no question needed an Architect ruling; decisions taken inside the card are listed)

- (a) Provenance builder: `backend/assetops_backend/mini_depth/provenance.py:21` `mini_blocks(c, link_rows, t, s,
  selected_revision_ids, selected_evidence_ids, pending_evidence_ids)`, called by `MiniDepthRead._read`
  (`mini_depth/read.py:445`); body keys `source_provenance`, `selected_source_provenance`, `pending_source_provenance`.
  Reused unchanged on a read-only snapshot of the fuel-balance store (`night_records_and_provenance`), basis selection
  = the window revision id(s), cited set = the window's `evidence_ids`; served under `"provenance"`. S-d did not fire.
- (b) `build_finding_router` is included at `backend/assetops_backend/main.py:548`; K5's router is included just after
  it (before the Finding index). `host/lab_app.py:40` imports `create_app` from `assetops_backend.main`, so `serve`
  exposes the new routes.
- (c) A new Ref kind joins: `backend/assetops_backend/chain/refs.py:28` `KINDS` + one `href_for` branch + the
  constructor; `frontend/src/shell/__fixtures__/route-refs.json` (one row per kind; read by
  `backend/tests/test_ch5a2_refs.py` and `frontend/src/shell/__tests__/routeRefs.test.ts`, whose kind list gains the
  name); `frontend/src/sites/chainRef.ts` `Ref` union; `routeFor` (`operatorSiteRoutes.ts`, exhaustive `never` switch);
  `frontend/src/test/linkRefs.ts` parser. `tools/checks/chain_coherence.py` checks issue kinds (`FINDING`,
  `OPPORTUNITY`) on boards, not Ref kinds; no entry needed. S-e did not fire.
- (d) `.agent/K5-mock-measurements.md`: identical to W4-02's fuel numbers; the existing `mini-max--fuel-cards`,
  `mini-max--fuel-bridge`, `mini-max--fuel-interpretation` classes meet them. No new CSS.
- (e) Site Findings index: `frontend/src/sites/SiteFindingIndex.tsx` (`SiteFindingIndex`), its MINIGRID branch is the
  default branch of `SiteFindingsFrame` (`frontend/src/shell/SiteAnalyticsFrames.tsx`, `opportunityHelper` /
  `earlyWarnings` for MINIGRID). K5 adds an optional `fuelChecks` slot rendered after the dispatch panel.
- (f) K4a's `finding_text.finding_lines(ff, tz)` matches §9j.7 (SUPPORTED: claim, gap iff gap_minutes > 0, money,
  not_why, margin; NO_LONGER_SUPPORTED: title, no_longer, not_why). Imported, never retyped; `litres1`, `short_day`,
  `gap_line`, `margin_line` imported too.

## Rendered literals (server, verbatim; night 4 values from F0's committed band)

- Residual card "95.7–144.3 L", note "Above the 40 L the check flags"; status "Fuel balance: unexplained fuel" (amber).
- Use note "Modelled: 122.3 kWh × 0.355 L/kWh, 10 % either way" (idle form only when idle_seconds > 0).
- Night label "Night of 4 Oct · 6 pm to noon"; gap note "The tank sensor sent no readings from 00:45 to 02:30."
- Night 2: "300 L", "1 delivery record"; night 1: "None recorded", "Absence of record does not prove none occurred".
- Fuel checks row "Unexplained fuel overnight · 4 Oct · about 95.7–144.3 L".
- Records "07:00, 5 Oct" · "Tank dip" · "706 L" · REC code; empty "No delivery or tank dip recorded this night".
- Finding panel: link "Unexplained fuel overnight" + K4a claim line, or "No finding: the fuel was accounted for within
  the margin." / "Not available yet · the finding for this night has not been raised" / "No finding for this night."

## Kobo unchanged (hour mode)

- `git diff main -- frontend/src/sites/MiniPerformance.tsx`: two imports, the optional `fuelBalance` prop, one
  `useFuelNights` hook line and one early-return branch inside `MiniFuel`. No other line; K4a's `FUEL_NOTICE`
  (`:1310-1312`) and RESIDUAL row (`:1344-1345`) untouched.
- Hour mode renders while the nights read is pending and stays for `NONE`, a failed or refused read and no client,
  so Kobo never flashes another state. F4 asserts byte-equal `innerHTML` for no client / NONE / unavailable / refused,
  with a NIGHTS control that leaves hour mode. `miniFuelRoutes.test.tsx` passes unchanged.
- B1: Kobo with no window answers `mode: "NONE"`, `nights: []`; the mini-depth fuel hour read is equal before and after.
- Fuel checks renders nothing without rows (F8), so the Kobo Findings index is unchanged.

## MOCK DEVIATIONs (header comment at each render)

| ID | Where | What |
|---|---|---|
| MD-FUEL-K-1 | `MiniFuelNights.tsx` header | night window with a night selector instead of v69's hour bar (`:623-630`) |
| MD-FUEL-K5-1 | `FuelNightRecords` | "Deliveries and tank dips" table; v69's bridge only names "Delivery / operator records" (`:627`) |
| MD-FUEL-K5-2 | `NightFindingPanel` | "Finding for this night" replaces "Inspect existing generator fuel interpretation" (`:629`) in night mode |
| MD-FUEL-K5-3 | `SiteFuelChecks` | "Fuel checks" panel on the Site Findings index (v69 lists dispatch Findings only) |
| MD-FUEL-K4-1 | `SiteFuelFinding.tsx`, `SiteFuelFindingFrame` | the fuel Finding page itself (K4a's, cited; v69 `:630`) |

## Layout evidence owed (not run)

`layout evidence: not run` — blocking precondition: K7-D's kept scratch database `assetops_demo3_kisiwa_test` does
not exist yet (§9l.2 Captures; §9l.3). Owed, with `node tools/layout-evidence.mjs` against `serve` on that database,
at 1440 and 390 unless noted:
1. Kisiwa Fuel, night 4 (UNEXPLAINED, gap note, one dip) and night 6 (WITHIN_MARGIN, two dips);
2. Kisiwa Fuel, the night-2 delivery night (1440 only);
3. the fuel Finding page for night 4;
4. Kisiwa Site Findings with the Fuel checks panel (use a window covering night 4);
5. Kobo Fuel in hour mode, compared with main's capture of the same page: only K4a's two strings may differ.
Claims owed by those captures: panel budgets from `.agent/K5-mock-measurements.md`; no horizontal scroll at 390;
every table scrolls inside its own panel; the records table's cap. Until then every layout claim above is unverified.

## Checks

(filled in below)

## Known deviations / builder decisions (none changes product semantics; each is for the reviewer to accept or rule)

0. **The store gains two read-only methods beyond `has_windows`** (card: "`has_windows` only"). `night_read.py` first
   held its own engine; `configuration-persistence.ps1` refuses storage technology above `fuel_balance/adapters`
   ("Move it into .../adapters and speak domain records across the port"), and a `$pgReaders` join does not lift that
   domain rule. So `night_context` (Site zone, the one active tank, the read instant) and
   `night_records_and_provenance` (K2's `select_fuel_records` through the store's injected reader + `mini_blocks`, one
   snapshot) live in `PostgresFuelBalanceStore`. No write path, no K3/K4a method, no `B/work/` file changed (S-c not
   hit). `night_read._guard` maps an unexpected store exception to the typed 503 (it may name no driver class).
1. **`SiteAnalyticsFrames.tsx` is more than "one prop".** It gains `DEFAULT_FUEL_BALANCE`, a `fuelBalance` prop on
   `SitePerformanceFrame` (passed to `MiniFuel`) and on `SiteFindingsFrame` (the Fuel checks slot), and the new
   `SiteFuelFindingFrame`. The frame must live in the shell: `sites/` may not import shell code (site-substrate rule 8),
   and the card's layout needs `OperatorSiteTabs` and the route builders. `App.tsx` registers it.
2. **Fuel checks has no Site-type test.** It is passed on the index's default branch and renders only with rows, so a
   Site without fuel Findings (Kobo, any non-MINIGRID) renders nothing; a `site_type === "MINIGRID"` guard raised the
   hard-wiring ratchet (cmp/lit) and was removed.
3. **Links in the substrate**: the night page's Finding link is `useLinkFor()` of a `FUEL_FINDING` Ref; the fuel Finding
   page's night and version links come from shell builders (props). Server `href` fields stay in the bodies (unused by
   the client), so the hard-wiring `href` cell does not rise.
4. **Body keys beyond the card**: night body `margin` (K4a's `margin_line`, for the chart note in phase B) and
   `records_empty` (`RECORDS_EMPTY`, so the browser holds no copy); fuel Finding `links.fuel_night_label`
   (`FUEL_NIGHT_LINK`). Nights `[from, to)` is half-open (as `windows()`); default = 14 nights ending with the latest.
5. **Unspecified formats**, chosen inside the card's rules: ticket/dip volumes and the deliveries total in whole litres
   when integral (A2's "300 L"), every computed litre amount one decimal half-even; a card note is null when its value
   is unknown (no reading time, no modelled use); bridge basis/treatment read "Unknown" when the reading time or the
   declared accuracy is missing; the residual bar scales by `max(high, 0)`; a null bar shows the existing `Unknown`
   while the card says "Cannot compute".
6. **`evidence_count`**: OPENING/CLOSING 1 or 0, DELIVERIES = the delivery records the check counted (roots in
   `record_ids`), USE and RESIDUAL = every evidence id the window cites (no per-term split is stored).
7. **Refusal messages reuse existing sentences** (no new wording): `INVALID_KNOWN_AT` and the 503 reuse the mini-depth
   messages; the fuel-findings window refusal reuses `FUEL_BALANCE_RANGE_INVALID`.
8. **Revisions without a new store method**: the fuel Finding's versions are walked with K4a's `fuel_finding(...,
   known_at = previous created_at − 1 µs)`; `?revision_id=` must be one of them, else 404.
9. **Night page Finding** = the fuel Finding (latest revision as known) whose cited window is this night's on the same
   tank; a NO_LONGER_SUPPORTED Finding shows K4a's `no_longer` line as its text.
10. **Hour mode while the nights read is pending** (Kobo never flashes another state); on Kisiwa the hour bar shows for
    one round trip before night mode. The hour read still fires in night mode (hook order); its result is unused.
11. **Bounds reused** (no new CSS): records table on `mini-max--fuel-bridge` (Show all after 6), Finding panel on
    `mini-max--fuel-interpretation`. Night selector label "Night" (as the hour bar's "Day"/"Hour").

## Residual risk

- Every layout claim is unverified until the owed captures run (above); K5 merges after them.
- K6b must import `refs.fuel_finding_ref` and `siteFuelFindingHref` from main once K5 merges (§9m.4), not add copies.
- K4b imports `night_text.FUEL_REASON_WORDS` (§9l.4); the literals are final here.
- The default nights read loads every stored window of the tank to find the latest night (one indexed query; fine for
  the demo's tens of nights).
- The fuel Finding's estate list entry is K8's (§9l.2 "Moved out of K5").
