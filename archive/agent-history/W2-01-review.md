# W2-01 review - cold Foundation, topology, readiness and SLD

Reviewer: fresh independent Claude reviewer (not the author). Revision `a4e4cb10`, diff `7ea8d042..a4e4cb10` (excluding `.agent`).

## Verdict: RETURN

The backend matches `D-2026-10-17-w2-01-answers` A-I. It is clean and well tested. One High UI finding (the cold SLD drawing) and one Medium (390 density and a gap repeated in every row) block. Fix both on the branch, then send it for a focused re-review of the SLD and readiness captures.

## Findings

1. **High - `cold-sld` panel 1 drawing does not match the mock's structure, prominence or style.** `frontend/src/sites/SiteSingleLineDiagram.tsx:1290` (`ColdTopologyDiagram`), truncation at `:1343`.
   - The mock draws a single line diagram: a vertical AC bus bar, with grid and generator feeding the transfer switch on the left, the compressor feeder on the right, and a "Monitoring & communication" strip of source boxes under the drawing. The mini-grid `sld` (W1-F1, `.agent/W1-F1-evidence/sld-now-1440-app.png`) already reproduces that bus-bar idiom with component icons.
   - The cold view draws a left-to-right chain of plain boxes. It has no bus bar, no icons and no monitoring strip.
   - Panel 1 is about 479 px tall at 1440 against the mock's about 700 px (about 1.46x shorter, outside the 1.3x budget). Packet deviation 7 and its residual risk acknowledge this.
   - Names are cut with an ellipsis ("Ambient temperature pro...", "Automatic transfer swit...", "Chamber temperature pro..."). The same file's own rule (`:198-204`) refuses truncation because it hides a fact.
   - At 390 the drawing scrolls sideways and the cold room and chamber probe start off-screen. The mock scales the whole drawing to fit.
   - **Fix:** render the cold topology in the mini-grid bus-bar idiom. Draw the AC bus as a vertical bar. Put the grid meter and generator on the left into the transfer switch, with the transfer switch feeding the bus. Put the compressor on the right of the bus, with a THERMAL link to the cold room. Reuse the existing component-icon set and add icons for the probe, compressor and switch.
   - Add a "Monitoring" strip below the drawing with one box per configured source (from `bindings`). Each box carries the honest "reporting not assessed here" marker, never a reporting dot.
   - Wrap names instead of truncating them (use the existing `NAME_LINE_BUDGET`/`NAME_LINES`). Keep the 390 view fitted the way the mock is, or the way the mini-grid SLD is.
   - Recapture the stocked, missing-probe and no-version states at 1440/390 so panel 1 is within about 1.3x of the mock.

2. **Medium - 390 density: tall wrapped rows and a gap repeated in every row.**
   - Capture heights at 390, app against mock: `cold-readiness` 3451/2476 (1.39x) stocked and 3613/2476 (1.46x) missing-probe; `cold-sld` about 1.43x. Even after allowing for the taller shared nav rail (about 275 px), readiness is still about 1.4x.
   - In the "What each part does" table (`frontend/src/sites/ColdFoundationViews.tsx:715`), every one of the 8 rows repeats "(configured) · Function description not recorded". At 390 each row wraps to 4-5 lines. The panel footnote already states the same limit once.
   - The readiness table rows (Declared chip plus inline text, and a three-line Area cell) are similarly tall at 390.
   - **Fix:** in the parts table, show only the plain role in "Role at this site". Drop the per-row "(configured)" and `FUNCTION_UNKNOWN` and keep the single footnote. In the readiness table at narrow widths, put the Declared detail text under the chip as one short line, or omit it there, so each row is about 2 lines. Recapture at 390 and confirm each route is within about 1.3x, net of the shell rail.

3. **Low - contradictory-looking readiness row.** `frontend/src/sites/ColdFoundationViews.tsx:481`. "Door and loading log" shows a `Configured` chip next to "No source: Manual temperature log (optional)". Grouping the manual temperature log under the door/loading area also reads oddly. **Fix (non-blocking):** word it as "Manual temperature log (optional) not configured", or give the optional manual log its own row.

4. **Low - contact null when no health store or no matching gateway.** `backend/assetops_backend/sites/cold_foundation.py:207-208` and `backend/assetops_backend/cold_foundation_api.py:80-91`. In those cases the API returns `state:null` with "Gateway contact is not available". The design names only RECENT, STALE and NEVER. This is reasonable and recorded as a deviation. **Fix (non-blocking):** have the Architect confirm it in the W2-02 question batch.

5. **Low - the readiness availability timeline is omitted.** The mock's 4-segment availability band and legend under the gateway cards are absent. The Availability card says "Not available" in their place. **Fix (non-blocking):** keep the band slot as an empty or unknown track labelled "No availability history".

## Backend check against the answers (all match)

- **A, topology:** the four component types, node roles `COLD_ROOM/SENSOR/COOLING/SWITCH`, and `SIGNAL/THERMAL` media are in place. `COLD_EDGE_TYPES` holds exactly the design's directed pairs. Duplicate `(from,to,medium)`, self-loops (via the pair table), the DAG check (`_find_cycle`), at most one SIGNAL edge out of a room and at most one into a probe are all enforced. Readiness requires exactly one primary probe that is bound.
- **B, events:** the `event` unit and `EVENT` value kind are added. The IDENTITY `event` triple is valid only for EVENT roles. Manual temperature is the one degC EVENT role. ENUM members are role-specific (compressor, grid, generator, bus). Policy roles are `FOUNDATION_CONTROL`. The v4 table carries roles, and both `validate_bindings` and the S2 ledger check them (W2-00 Low 2 folded).
- **C, properties:** all 13 properties have the exact units, kinds and carriers. `UNIT_RANGES` matches. degC is signed only through `SIGNED_PROPERTY_UNITS`. Cold-specific strict/nonnegative rules, band order and hysteresis are enforced after parsing in `validate_cold_foundation`, wired in `site_parsing.py` for COLDCHAIN only.
- **D-I:** commissioning is always UNCONFIRMED with an empty ID list. Contact maps per the rule, including UNKNOWN with a diagnostic going to STALE plus the limitation. Cadence is the fixed 300 for periodic channels and null with `transition` for event channels. It is never read from stored rows or from the gateway's declared cadence. A wrong-type read returns 404. The frontend route switches on the Site record type. Title-map entries `cold-readiness:2` and `cold-sld:1` are present.
- **W2-02 channel closure:** `grid_power_event` and one `backup_start_event` are in `cold-roles-1`, and no channel is bound twice.
- **Migration `0021`:** a no-op upgrade and downgrade. The Postgres test covers 0020->0021->0020 with no row touched.
- **Mini-grid is unchanged:** cold validation is gated on COLDCHAIN, and an empty `states` field falls back to `GENERATOR_STATES`. Adjacent S1 tests pass (below).

## Checks I ran (worktree at `a4e4cb10`; main venv python; private DB `assetops_w201rev_test`, dropped afterwards)

- Focused, serially: `test_w201_cold_vocabulary.py`, `test_w201_cold_foundation_postgres.py`, `test_w200_binding_metadata.py`, `test_w200_source_events_postgres.py` returned **60 passed**, 0 skipped, in 5:09.
- Adjacent mini-grid/S1: `test_foundation_content_parsing.py`, `test_s1_bindings.py`, `test_addressed_bindings.py`, `test_s1_cutover.py`, `test_s1_foundation_postgres.py`, `test_s1_bindings_postgres.py` returned **315 passed** in 2:09.
- `tools/check-all.ps1 -Python <main venv>`: **10/10 guards passed.** Without `-Python`, the worktree has no `.venv`, so rule 8 and the screen ledger fail on the missing interpreter. That is environmental.
- **Rule-8 probe:** I planted a sqlalchemy `text` import plus an `INSERT INTO foundation_revision` in `cold_foundation.py`. `check-architecture.ps1` failed with storage-above-adapter, driver-import and "second product database writer". I reverted it, and the tree was clean.
- **Behaviour probes:**
  - Removing `seen.add(key)` made `test_duplicate_edge_is_refused` fail.
  - Disabling the GREY cycle branch made both cycle tests fail.
  - Both were reverted.
- Frontend: `npx.cmd tsc --noEmit` was clean. `npx.cmd vitest run src/sites/__tests__/coldFoundation.test.tsx` returned **19 passed**. `expectV69Panels` covers stocked, missing-probe/no-contact, no-version (refused) and unreadable, for each of the three routes.
- **Not rerun:** the full frontend suite (implementer: 1976 passed at `e5162465`) and the full backend suite (the coordinator is running it; the packet records it as not complete). The capture tool was not rerun. I judged the committed 1440/390 pairs in `.agent/W2-01-evidence/`.

## Residual risk

- Contact and the gateway title are current facts shown on historical `?at=` periods. The panel says so.
- The gateway acquisition snapshot still refuses COLDCHAIN (`SITE_TYPE_UNSUPPORTED`). W2-02 owns that.
- Cold binding rows persist no v4 metadata. W2-02 must derive or persist it before admission.
