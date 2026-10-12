# V-01a review packet: Site and Foundation visual fidelity

**Task:** `tasks/V-01a-foundation-visual-fidelity.md` (`USER_REVIEW_REQUIRED: true`, owner visual checkpoint).
**Branch:** `task/V-01a-foundation-visual`. Diff base: `575430f`.
**Scope:** `sites:1`, `foundation:1-3`, `readiness:1` and `sld:1-2`, as approved in the W1 mapping. Bounded registered portions of `readiness:2-3` are shown only where the UI already shows them.

## Outcome delivered

- Each panel was compared against the v6.9 mock at 1440 and 390 px, in populated, empty and no-version states.
- The supported-claim gaps found were fixed: a false "In effect now" period selection, a contradictory devices caption, missing panel sub-lines, the Sites panel label, and the bus rating on the topology bus.
- An isolated walkthrough tool, a measured evidence tool (50/50), and an owner guide are included.
- No new data claim was added, and no mock value is used as product data.

## Files materially changed

- `frontend/src/sites/FoundationRevisionPanel.tsx`: an address-instant option in the period selector.
- `frontend/src/ui/Panel.tsx` and `ui/primitives.css`: the optional `description` sub-line (`.panel__description`).
- `frontend/src/sites/SitesIndex.tsx`, `StoredFoundationViews.tsx` and `FoundationBindingsPanel.tsx`: labels and sub-lines, plus the bus rating.
- `frontend/src/sites/SiteConfiguration.tsx`: the devices caption.
- Tests: `shell/__tests__/siteFoundationRevision.test.tsx` (new address-instant test) and `sites/__tests__/siteConfiguration.test.tsx` (caption test rewritten).
- Tools: `tools/v01a_foundation_walkthrough.py` and `tools/v01a-foundation-evidence.mjs`.
- Records: `.agent/V-01a-owner-walkthrough.md`, `.agent/V-01a-questions-1.md`, `.ai/CODE_STATE.md` "V-01a" and `.ai/ACTIVE_CONTEXT.md`.

## Per-panel record

The routes are on web 5360 (API 8860, DB `assetops_v01awalk`), except the empty Sites state, which is on 5361 (API 8861, DB `assetops_v01aempty`). Both viewports are 1440x1000 and 390x900, and each pair has screenshots `mock-<id>-<vp>` and `app-<state>-<vp>`.

| Panel | App route | Supported claim | Deliberate gap | API / source | Accepted visual difference |
| --- | --- | --- | --- | --- | --- |
| `sites:1` Site inventory | `/sites`; empty: 5361 `/sites` | Stored Sites with type, location, mode (provenance), lifecycle, origin and template | Mock KPI tiles, type chips, Assessment, Top issue and Evidence columns (no source); `sites:2` In setup and setup tabs (W6) | `GET /api/sites` (`siteDirectoryClient.ts`) | Search and filter selects instead of chips; header button "Create a site in the Simulator Lab" |
| `foundation:1` Configured topology | `/sites/KOBO-001/foundation?at=…` | Declared components chained onto the bus, declared ratings, and the bus rating | Live flows | `GET /api/sites/{id}/foundation?at=` and the site detail | Text cards with no glyphs (Q5); the bus line uses the accent colour, not green |
| `foundation:2` Identity & obligations | same | Code, name, archetype, location, timezone, critical-load priority, lifecycle, mode and origin | Mock "Productive use" and "Critical service" phrasing; unregistered obligations | same | More rows than the mock (stored fields) |
| `foundation:3` Time-valid controls | same | Reserve, generator start/stop (or "declares none"), minimum runtime, and source and critical-load priority, with the authority version | Mock "Evidence / change" links (no policy or proposal source) | same | The reserve-change form sits under the table (S1-03 interaction) |
| Period strip (all views) | `?at=` | The selected stored version, its binding set, gaps, and whether the period is current | — | `…/foundation/versions` | The mock statusbar is one line; the app adds the selector and the scheduled/historical note |
| `readiness:1` | `/sites/KOBO-001/foundation/readiness?at=…` | Configuration verdict, role coverage, bindings and gaps, with "Configuration readiness is distinct from claim readiness and from operational status, which are not assessed here." | Commissioning columns (Declared, Confirmed, Owner); `readiness:2-4` gateway status, source health and effect (S2/S7 paths) | foundation read (`readiness`, `bindings`) | Neutral tones instead of green/amber tiles (Q3); binding IDs remain visible (S1-02 ruling D5) |
| `sld:1` diagram | `/sites/KOBO-001/foundation/sld?at=…` | Declared parts and connections for the period, and bound channels | Reporting dots, live flow, breakers and meters not declared | foundation read and site detail topology | Archetype grid drawing, not a bus-bar SLD (Q1); the drawing scrolls in its own region at 390 |
| `sld:2` parts | same | Each part's type, rating and bound channels; "No channel declared" for the AC bus | "What it reports" cadence (Evidence) | same | Column "Channels" in place of the mock's "What it reports" |

The page heading is the view name ("Foundation"), with the Site name and code beneath (Q2).

## Acceptance criteria

- **Compare by manifest ID and supported portion: met.** See the table above. `tools/v01a-foundation-evidence.mjs` asserts the mock panels and the app's supported panels per ID.
- **1440 and 390 pairs for populated and missing states: met.** States covered: Sites populated and empty, Foundation, SLD and Readiness in effect now (no `?at=`, v10) and at the scheduled v13 period (`?at=2026-10-22`, not in effect until 21 Oct 2026), Foundation no-stored-version, the SLD imported period (captured in fix round 1), and Readiness. Screenshots are written to the tool's output directory.
- **Hierarchy, density, labels, focus, keyboard, selection, route and reload: met.** Labels and sub-lines are fixed. Tab reaches the subtab with a visible focus style. Enter keeps `?at=`. Tab moves to the next subtab.
- **Foundation revision and bound component stable: met.** The selected period survives reload and the subtab switch, and the selector now shows it truthfully. Each part's bound channels are identical after reload. They differ when the period changes (`pv-inverter` and `battery-pcs`, a non-empty set), which proves the check can tell periods apart. This uses the Q4 reading.
- **Readiness distinguishes configuration from operational status, with PRE-S3-04 incorporated: met.** The wording is asserted. A health word may appear only inside a disclaiming sentence.
- **Record route, viewport, claim, gap, API and accepted differences: met** (the table above).
- **Frontend tests, typecheck/build, layout evidence, ledger and registry checks: met.** See Checks.
- **Independent Reviewer and owner inspection: pending.** The owner guide is in place.

## Checks run

- `npx vitest run`: 55 files, 1326 tests passed.
- `tsc -b`: exit 0. `npm run build` (tsc --noEmit plus vite build): exit 0.
- `tools/check-all.ps1`: all 6 guards passed (architecture, navigation, workflow, dependency registry, delivery fixtures, ledger with 110 screens and 258 panels).
- `node tools/v01a-foundation-evidence.mjs http://localhost:5360 <dir> http://localhost:5361`: **50/50**, exit 0.
- Non-vacuous proofs, each reverted with `git checkout`:
  - With the address-instant option removed, the new vitest test fails (1 failed of 43).
  - With that option removed and the old caption restored, the evidence tool fails 8 claims (42/50): address instant, caption, reload and Enter, at each viewport.
- `node tools/layout-evidence.mjs http://localhost:5360 KOBO-001`: 200 PASS and 0 FAIL, including the Sites index, the three Foundation views at 1280 and 1000, the SLD scroll region and the table regions. It then **stopped at the known Lab precondition**: "/simulator-lab/scenarios/fuel-loss-event/run-setup found its submit still disabled after ten seconds". The walkthrough tree has no Lab backend state. The Lab and Scenario sections after that point are unverified by this run, and this slice does not touch them.

## Known deviations

- Q1-Q5 (`.agent/V-01a-questions-1.md`) are defaulted to the current app, and the owner decides them.
- 390 px `sld:2`: the parts-list table is 433 px wide in a 309 px scroll region, so the Channels column and the caption scroll off-screen. Accepted narrow-width difference, no CSS change; the column is reachable by horizontal scroll and the claim (bound channels per part) is unchanged.
- `SiteOverview.tsx:241` (backlog C2) is not a V-01a screen and stays with S5-01.

## Residual risk

- `Panel.description` is a shared primitive, though it is additive: panels without it render as before.
- The address-instant option label uses the resolved instant. A malformed `?at=` is handled upstream by the existing error and empty states.
- The evidence tool depends on `assetops_s4cases` (the S4 producer). If the producer output changes, the period instants named in the tool may need updating.

## User-review focus

- The four mock/app pairs at both widths.
- Decide Q1 (bus-bar SLD redraw) and Q3 (neutral readiness tones). These are the two visible differences most likely to matter.
- Confirm the period selector and devices caption fixes in steps 2 and 4 of the walkthrough.

## Fix round 1 (against `.agent/V-01a-review.md`)

- **B1:** walkthrough `PERIODS` relabelled (v13 is "Scheduled ... not in effect yet"; the comment now says the instants lie inside periods, not at `valid_from`). `links` prints the no-`?at=` in-effect-now routes first. The evidence tool adds in-effect-now app screenshots for Foundation, SLD and Readiness at both widths (`app-*-now-*`), with a claim that the selector reads "In effect now" and no "Scheduled/Historical period:" strip appears; the previous populated shots are renamed `app-*-scheduled-*`. Owner walkthrough and "States covered" corrected. The mock pair for in effect now is the same mock panel (the mock has one configuration).
- **C1:** `SITE_SLD_INTRODUCTION` now says whether any reading has arrived is not assessed in this view. New vitest asserts it and the absence of "no reading has arrived"; it fails on the old copy (1 failed of 78) and passes now.
- **C2:** recorded above as an accepted difference (no CSS change).
- **C3:** imported-period SLD now captured (`app-sld-imported-*`).
- Checks: vitest 55 files / 1327 passed; `tsc --noEmit` 0; `npm run build` exit 0; `tools/check-all.ps1` all 6 guards passed; `prepare` and `links` rerun on 8860/8861/5360/5361; evidence tool **62/62**, exit 0 (two claims initially failed on my own over-broad text match of unrelated form copy and were corrected). Servers stopped; those four ports are free.
- Not re-run: `layout-evidence.mjs` (no layout CSS changed).
