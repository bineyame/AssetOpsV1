# Architect request: rule on the W5-03a pre-flight batch (51 items)

You are the AssetOps Architect (Codex). Read:
- `.ai/ROLE_CONFIG.md`: both mock-fidelity rules, "Departure categories and register", "Builder pre-flight and quiet-machine suites", lessons 13–14 and "Token Efficiency";
- `.agent/W5-03-build-spec.md` (W5-03a units, closures, close2, your retrospective) and `tasks/W5-03-ev-depth.md`;
- `.agent/mock-departure-register.md`;
- the pre-flight list in branch `task/W5-03a-ev-selected-depth`: run `MSYS_NO_PATHCONV=1 git show task/W5-03a-ev-selected-depth:.agent/W5-03a-phase-handoff.md`.

The mock screens are `availability`, `energy` and related EV screens in `frontend/mockups/v69/index.html`.

1. **Gate (P-G-1/2).** W5-03a waits on W5-02 at `0033`. The W5-02a core (K1a–K1c, with `0033`) is near review on `task/W5-02a-cold-action-root`, and the screens part (K2a/K2b) follows. Rule whether W5-03a may start once the W5-02a **core** merges, or must wait for all of W5-02. Give the shared-file merge order (`main.py`, `SiteAnalyticsFrames.tsx`, `operatorSiteRoutes.ts`, nav guards), preferring the shortest critical path.
2. **Code reality.** Correct the cards against the real code:
   - `EvReplayBuilder` is really `class Chain`;
   - the `EvReadService` anchors are stale;
   - `accepted_on` returns every accepted row, not the selected set;
   - `foundation_on` has no revision ID or `valid_to`;
   - `ev_gate` opens no snapshot.
   Give literal reads, fields and file lists.
3. **States without a field.** Give literal fields for "trustworthy", "stale" and "unattested", and make `service_windows` per connector, including `weekly: []`.
4. **E3 chart.** Write the chart literals for the restored chart (graphics module registration, marks, axes, the limit line, tests), and remove the stale "no svg" text.
5. **File lists.** Add `evAssessmentRoutes.test.tsx`, `settled.ts`, `evSiteRoutes.tsx` and `DataTable` (sticky column), or rule them out.
6. **Departures.** For the roughly 20 unlabelled departures (headings, breadcrumbs, subtitles, card notes, dropped chart notes, the conclusions table form, the bridge text): restore each to the mock, or label it `MOCK DEVIATION (Dn)` and add a register row.
7. **Closure table.** Map every P-ID to where it is closed, and amend `D-2026-10-22-w5-01-w5-03-buildspec`.

Write only `.agent/W5-03-build-spec.md`, `tasks/W5-03-ev-depth.md` if needed, `.agent/mock-departure-register.md` and `.ai/DECISIONS.md`. Do not commit. End your output with: the gate ruling, every new departure with its code, and anything left open.
