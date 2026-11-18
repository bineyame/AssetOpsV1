# Review: DIESEL-K5 fuel screens (code round; captures owed)

Reviewer: Claude (Opus), fresh context, independent of the builder. Branch `task/DIESEL-K5-fuel-screens` at `31b9bd7f8`
(merge-base with main `9d7641f9a`). Judged against `.agent/build-sheet-DIESEL-1.md` §9l.2, with §9l.1, §9j.7, §9k and
§8.2 H1-H5 for context. Packet: `.agent/review-packet-K5.md`.

## Verdict: FIX

One Medium finding: the F8 "absent with no rows" test passes vacuously. The code is correct, but the card's
"must fail" proof does not hold. After the fix, this becomes ACCEPT-pending-captures. Nothing else blocks. The
layout evidence is still owed, as the packet says.

## Findings

### M1 (Medium): F8 "absent with no rows" never sees the loaded state, so a panel that renders with zero rows passes
- File: `frontend/src/sites/__tests__/siteFuelFinding.test.tsx:174-184`.
- The test waits until `getFuelFindings` has been called, then awaits a single `Promise.resolve()`, then asserts
  `container.innerHTML === ""`. The client's `.then(setRows)` and React's re-render have not yet happened at that
  point. The assertion therefore checks the pre-load state, which is empty for every implementation.
- Failure scenario, reproduced on a scratch copy of `frontend` (worktree untouched):
  - I changed `SiteFuelFinding.tsx:138` from `if (shown.length === 0) return null;` to `if (rows === null) return null;`.
  - With that change, a Kobo or Cold Site would show an empty "Fuel checks" heading once the read lands. That breaks
    the card's "renders only when `rows` is non-empty, so Kobo stays byte-equal" and MD-FUEL-K5-3's scope.
  - All 5 tests in `siteFuelFinding.test.tsx` still passed.
- Why it matters: deviation 2 (no Site-type test) depends on exactly this behaviour: rows decide visibility. The only
  test guarding it cannot fail.
- Fix: settle the read before asserting, for example
  `await act(() => new Promise<void>((r) => setTimeout(r, 0)));` (or the repo's `settledScreen()`), in place of
  `await Promise.resolve()`.
  - I applied this on the scratch copy. The mutant above then FAILED, and the real code passed 5/5.

### L1 (Low): night mode ignores the page's `known_at`
- Files: `frontend/src/sites/fuelBalanceClient.ts:130-131`, `MiniFuelNights.tsx:278-291`.
- The backend nights and night reads are as-known: `known_at` is honoured, `recorded_at <= :k`, and B2 covers it. The
  browser, however, never sends `known_at`. A Fuel URL carrying `?known_at=` (which the hour read honours via
  `MiniWindowQuery.known_at`) shows windows and Findings as known now.
- This matches the card literally (`getNights(siteCode)`), and the demo's DB clock is after every story cutoff, so
  the demo is not affected. It is noted for whoever wires story-cutoff links to the Fuel page (K4b's Protect line).
- No fix required in K5 unless the Architect wants pass-through.

### L2 (Low): `has_windows` is Site-wide but the default range reads one tank, which can raise IndexError and give a 500
- File: `backend/assetops_backend/fuel_balance/night_read.py:89-95`.
- `has_windows` checks any window on the Site. `windows(...)` then reads only the one active tank. Failure scenario:
  1. A tank with stored windows is retired.
  2. A new active tank has none yet.
  3. Result: `has` is True, `every` is `()`, and `every[-1]` raises IndexError. That is outside `_guard`, so the
     read returns a 500.
- Kisiwa has one tank, so the demo is not affected.
- Fix: treat an empty `every` as `mode: "NONE"` (or pass the tank to `has_windows`).

### L3 (Low): the delivery count comes from the current records, but the delivery litres come from the stored window
- File: `night_text.py:164-167`, `:182-188`.
- `n` counts delivery records whose roots are in `window.record_ids` and that are *currently* found occurring in the
  window. If a counted delivery record is later corrected so that its occurrence moves out of the window:
  - the card and bridge say "None recorded" / "No delivery record";
  - the stored residual still includes those litres.
- This is rare. It is an honesty edge (H-rules) rather than a demo risk. Counting kinds from `record_ids` (or
  reading the records as known at `window.recorded_at`) would remove it.

### L4 (Low): the default Findings index window is today only, so "Fuel checks" shows on Kisiwa only with a window covering the night
- File: `SiteAnalyticsFrames.tsx:451-455`, `:571-579`.
- This is consistent with the dispatch list on the same page, and the packet's capture plan already uses an
  explicit window. It is noted for the demo script: the Findings link must carry `from`/`to` covering the story nights.

## The brief's questions

1. **Night read and night mode.**
   - Kobo keeps hour mode. F4 (`miniFuelNights.test.tsx:245-271`) asserts byte-equal `innerHTML` for no client,
     `NONE`, unavailable and refused, and has a NIGHTS control. I verified that the 4 cases and the control exist.
   - I re-ran the F4 mutation myself on the scratch copy (drop `mode === "NIGHTS"` in `useFuelNights`): F4 FAILS.
     So F4 is a real guard.
   - `MiniPerformance.tsx` diff: two imports, one optional prop, one hook line and one early return, placed after
     all hooks (no hook-order hazard). K4a's `FUEL_NOTICE` and RESIDUAL lines (`:1312`, `:1346`) are untouched.
   - `miniFuelRoutes.test.tsx` passes unchanged (11/11).
   - The backend is as-known throughout:
     - `windows` and `has_windows` use `recorded_at <= :k`;
     - `fuel_finding(s)` uses `created_at <= :k`;
     - a future `known_at` gives 422.
   - There is no write path. Every new store method runs through `_read` (REPEATABLE READ, `SET TRANSACTION READ
     ONLY`). There are no inserts, and no K3/K4a write method or `work/` file is touched.
2. **Deviation 0 (store methods).**
   - `night_context` and `night_records_and_provenance` sit in `fuel_balance/adapters`, the only layer allowed to
     hold SQL.
   - `night_read.py` imports no driver.
   - `check-architecture.ps1` PASSES.
   - Both methods are read-only and reuse K2's injected `select_fuel_records` and the existing `mini_blocks`
     unchanged.
   - The adapter's lazy import of `mini_depth.provenance` is a cross-module read, but it is the provenance reuse
     the card asks for.
   - I accept the deviation. The card text ("`has_windows` only") was written before the guard's domain rule
     surfaced.
3. **Deviation 1 (`SiteAnalyticsFrames.tsx` scope).** I accept it.
   - `sites/` may not import shell code.
   - The frame needs `OperatorSiteTabs` and the route builders.
   - The additions are props with defaults plus one new frame. Existing frames' behaviour is unchanged.
4. **Wording.**
   - Every `night_text.py` literal matches the card block verbatim. I compared all of them, including
     `FUEL_REASON_WORDS`, `BRIDGE`, `RESIDUAL_NOTE` and the Finding-panel strings.
   - `litres1`, `short_day`, `gap_line`, `margin_line`, `finding_lines` and `TITLE` are imported from K4a's
     `finding_text`, not retyped. A6 asserts `nt.litres1 is ft.litres1`.
   - The new frontend copy has no run, ran, running, load or theft words. Matches appear only in comments and
     identifiers.
   - Guard V's fixture suite passes (14/14). The rendered-page vocabulary scan runs over captures, which are owed.
5. **Fuel Finding page wiring.**
   - The page lives at `/sites/{code}/fuel-findings/{id}[?revision_id=]`.
   - The `FUEL_FINDING` kind appears in `refs.py` KINDS, `href_for` and `fuel_finding_ref`; in `route-refs.json`
     (2 rows); in `routeRefs.test.ts` (kind list plus F7); in the `chainRef.ts` union; in `routeFor`; and in
     `linkRefs.ts`.
   - `test_ch5a2_refs.py` passes.
   - B4: K4a's `_fuel_findings` filters on `f.domain = 'fuel_balance'`, so a dispatch Finding id gives 404.
     `test_b4_...dispatch_id_refused` covers it (Postgres, not run here; see below).
6. **Deviation 2 (Fuel checks with no Site-type test).** Safe in production. Rows come only from `fuel_balance`
   Findings of that Site, so Kobo, Cold, EV and other non-fuel Sites receive `[]` and render nothing.
   - The one cost is an extra GET on non-fuel Findings pages that use the default branch. It changes no DOM.
   - The safety rests on F8, which is M1.
7. **MOCK DEVIATION labels.** All present at their renders:
   - MD-FUEL-K-1 at `MiniFuelNights.tsx:7`;
   - MD-FUEL-K5-1 at `:137`;
   - MD-FUEL-K5-2 at `:215`;
   - MD-FUEL-K5-3 at `SiteFuelFinding.tsx:111` and `SiteFindingIndex.tsx:198`;
   - MD-FUEL-K4-1 at `SiteFuelFinding.tsx:6` and `SiteAnalyticsFrames.tsx:2575`.
8. **Overlap with K6b.** The K6b worktree (`9f647dd95`) already adds **byte-identical** `FUEL_FINDING` code:
   - in `refs.py` (KINDS, docstring line, `href_for` branch, `fuel_finding_ref`);
   - `chainRef.ts`, `operatorSiteRoutes.ts` (`SITE_FUEL_FINDING_ROUTE_PATH`, `siteFuelFindingHref`, the `routeFor`
     case);
   - both `route-refs.json` rows, `linkRefs.ts` and the `routeRefs.test.ts` kind list.

   K6b also adds `FUEL_VERDICT` lines beside them in the same hunks, so whichever unit merges second will get textual
   conflicts in about 6 files. Resolution is mechanical: take the union, keeping one copy of each `FUEL_FINDING` line.
   - Watch `KINDS`, the `routeRefs.test.ts` kind list, and the `linkRefs.ts` regex order.
   - After the merge, run `test_ch5a2_refs.py` and `routeRefs.test.ts`.
   - `App.tsx` and `SiteAnalyticsFrames.tsx` additions are at different spots and should merge cleanly.
   - K6b does not register K5's route or frame, so there is no duplicate `<Route>`.

## Checks I ran (actual output)

**Backend, no database.** Python = plan2 venv, PYTHONPATH under the k5 worktree, `DATABASE_URL` unset.
- Command: `pytest test_k5_fuel_night_text.py test_out_b2_vocabulary.py test_ch5a2_refs.py test_k4a_fuel_finding_rules.py -q`
- Result: **120 passed**, 0 skipped, 2.55 s.

**Mutation A1** (in process, no file edited): `night_text.litres1` swapped for a half-up rounding.
`test_a1_litres_round_half_even_not_half_up` FAILS (AssertionError). The baseline passed.

**Frontend tests.**
- Command: `npx.cmd vitest run` on `miniFuelNights`, `siteFuelFinding`, `routeRefs`, `miniFuelRoutes`.
- Result: **4 files, 87 passed**. Vitest did run in this sandbox.
- `siteFuelFinding` prints act() warnings, which are noise.

**Mutations on a scratch copy of `frontend`** (node_modules linked; the worktree is unchanged):
- F4 (night mode on any loaded read): F4 FAILS.
- F8 (panel rendered with zero loaded rows): **survives**. This is M1. With the settled-read test it FAILS.

**Other checks.**
- `npx.cmd tsc --noEmit`: exit 0.
- `tools\check-architecture.ps1` (`ASSETOPS_GUARD_PYTHON` set): "Architecture check passed."
- `tools\check-agent-workflow.ps1`: "Agent workflow check passed."
- `node --test tools/checks/test_mock_deviation_labels.mjs`: 14/14 pass.
- `node tools/checks/frontend-hardwiring.mjs`: passed, totals unchanged
  `{"api":12,"href":24,"lit":70,"cmp":51,"code":3}`.

## Not verified by me

- **Postgres tests**, not run by instruction (machine busy). I cite the packet: 133 passed (68.7 s) on
  `assetops_k5_test` for `test_k5_fuel_night_api_postgres.py` plus the adjacent K3/K4a/K6a files at `34e064f2a`, and
  the B4 mutation proof.
  - The commits after `34e064f2a` are packet-only, so that revision matches the code under review.
  - I read B1-B5, which exist and assert the 404s for a dispatch Finding id, another Site's id and a foreign
    revision. I did not execute them.
- **`npm run build` and the full frontend suite**: not run (not a full suite).
- **Layout evidence**: `not run`, with its blocking precondition correctly recorded (K7-D's
  `assetops_demo3_kisiwa_test` does not exist yet). Every layout claim stays unverified until those captures exist:
  the panel budgets, no horizontal scroll at 390, the records table cap, and Kobo hour mode byte-equal in the browser.
  The rendered-page guard V scan comes with them.

## Residual risk not in the packet

- The K6b merge conflicts (above).
- L2's 500 on a retired-tank Site.
- Night mode ignores `known_at` (L1).
- The demo's Findings link must carry a window covering the story nights (L4).
