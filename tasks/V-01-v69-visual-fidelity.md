# V-01 - v6.9 visual and interaction fidelity

Status: executable W1 visual slice; adopted by owner 2026-10-09 (`.agent/owner-S2-closeout-2026-10-09.md`); activate after W1 core input/startup guards
USER_REVIEW_REQUIRED: true
Depends on: merged S2-02 and S1 surfaces; W1 owner core-panel/demo-value input before full tier acceptance
Branch when activated: task/V-01-v69-visual-fidelity
Planner: Codex, 2026-10-07

## Visible result and bounded screen set

The supported Kobo Site and Lab path uses a coherent v6.9 visual vocabulary at desktop and narrow widths. First comparison IDs from `frontend/mockups/v69/screen-manifest.json` are `sites`, `foundation`, `readiness`, `sld`, `evidence`, `evidence-analysis` and `lab`. Record actual route and supported panel/claim portions for each before capture. Add `dispatch` only with S3-01's accepted Postgres Performance read. This slice covers only claims made real by S1/S2 and honest missing states; no whole-screen Real claim follows from visual work alone.

## Contract and approach

- Compare `frontend/mockups/v69/index.html#/ID`, reference images and `mockups.css`/`portfolio.css` with the actual app at matching viewport sizes. Inventory colors, typography, spacing, density, status/coverage treatments, rail, Site header, tab/subtab row, date/window selector, panels, tables, evidence drawer and responsive states. Map recurring values to `frontend/src/ui/tokens.css` and shared UI components; document deliberate differences for accessibility or real data. Keep the mock files as reference, not product state.
- Publish one capability-based route inventory: show supported Site/Lab destinations and direct links with stable Site, window and selected revision IDs. Hide unsupported root/tab/subtab routes or clearly mark a meaningful unavailable destination; no empty mock tab. Site lists remain scoped projections and Finding/Action detail uses durable root identity when those slices arrive. Keyboard focus, navigation and reload preserve selection.
- Exercise a populated state, a missing configuration/evidence state, and a contradictory or late-evidence state where the owning slice supports one. `Unknown`, `Pending`, unpriced and unavailable have distinct visible meanings. Do not fill cards from mock values, Lab truth or a default healthy status. Every displayed number or claim resolves through its read API to its persisted source and evidence/assumption IDs.
- Compare app and mock screenshots for panel order, alignment, token use, table density and narrow behavior at 1440px desktop and 390px narrow viewport (or document device/browser equivalent); exercise actual hover/focus, selector and drill-down behavior. `frontend/mockups/v69/review-browser.mjs` checks the mock, not the app; app browser evidence is required. Record one report keyed by manifest ID, route, viewport, state, supported panels/claim portions, deliberate omissions and API/lineage reference. Review discrepancies by panel and record accepted differences.
- Record which `promotion_dependencies.to_real` items the reviewed screen closes and which remain. A Deferred screen enters a later task only after its `to_candidate` design, projection, fixture and owner-tier gates are met; an honest-gap screen cannot be marked fully Real while a named panel or remaining-work dependency is open.

## Acceptance and reviewer path

Open each supported app route and corresponding mock `#/ID` at desktop and narrow widths; capture side-by-side comparisons, navigate by keyboard, change Site/window, reload, follow one visible Evidence value to its accepted SourceEnvelope, and verify missing configuration and missing/contradictory Evidence states. App navigation must not expose an empty mock tab; unbuilt destinations are hidden or typed unavailable. Accept only supported panel portions whose layout, hierarchy, labels, state and interaction are reviewed; keep the remaining 58-panel mapping gaps explicit in the report. Add dispatch comparison with S3-01, as a separate review increment. Run frontend test/typecheck/build, layout/browser checks and `python frontend/docs/architecture/check_v69_ledger.py`; record exact commands and results. A screenshot proves presentation, not claim support. A whole screen becomes Real only when all its panels are real or owner-approved withheld and navigation/interaction/lineage are accepted.

The first S3/S4 claim fixture needs one complete, one missing/contradictory and one late Kobo interval; later S6 requires a distinct post-action window. Multi-site and cross-domain visual acceptance needs the separate [demo-data dependency](../frontend/docs/architecture/v69-demo-data-plan-proposal.md), with source-to-claim lineage and compatible window/currency basis. Do not copy illustrative mock events. S3-S7 packets add their new manifest IDs to this comparison method as each screen becomes real.

## Deferred

No global root, cold-chain/EV, Site creation, broad Performance, Incidents, Maintenance, warranty or Settings fidelity claim in V-01. Their proposed tiers and data/model gaps remain owner/Architect decisions and follow-on dependencies in `tasks/README.md`.
