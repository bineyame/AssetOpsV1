# Architect/Planner request: W5-02 (cold Work tabs) and W5-04 (EV Work) build specs

You are the AssetOps Architect and Planner (Codex). Read:
- `.ai/ROLE_CONFIG.md`, especially:
  - "Mockup drives the design";
  - the new "Both Architects ... check every screen-affecting spec, ruling and design against the v69 mock" rule;
  - "Build-Spec Readiness Gate For W5 And W6";
  - "W3/W4 lessons applied to W5 and W6";
  - "Token Efficiency";
- `.ai/DECISIONS.md`: `D-2026-10-22-w5-01-w5-03-buildspec` and its amendments, which reserve `0033_w5_cold_work` for W5-02 and `0035` for W5-04;
- `tasks/W5-01-cold-depth.md`, `tasks/W5-03-ev-depth.md` and `tasks/README.md`;
- as patterns, `.agent/W5-01-build-spec.md` and `.agent/W5-03-build-spec.md` (shared sections, unit cards, file lists, literal ledgers, closure tables, captures/loading sections, guard notes), and `.agent/W6-01-build-spec.md` for the merged W4 work model, global work reads and the rail/route ownership rules;
- the merged W4 work-case code (`backend/assetops_backend/work/`) and the W4 task files;
- `frontend/docs/architecture/production-shaped-mvp-technical-design.md` for the work sections;
- the v69 mock screens `cold-work`, `cold-work-incidents`, `cold-work-maintenance`, `cold-action`, `ev-work`, `ev-work-incidents`, `ev-work-maintenance` and `ev-action` in `frontend/mockups/v69/index.html` and `screen-manifest.json`.

Measurements at 1440/390 are in `.agent/W5-02-04-mock-measurements.md`, with screenshots in `.agent/W5-02-04-mock-shots/`. Use these for the panel caps.

Produce, in one pass:
1. `tasks/W5-02-cold-work.md` and `tasks/W5-04-ev-work.md`.
   - Scope: decide exactly which of those mock screens each owns versus what W4 or W6-01 already built. Cite the code.
   - Order: W5-02 after W5-01b (`0033`); W5-04 after W5-03b (`0035`).
   - Rows go in `tasks/README.md`.
2. `.agent/W5-02-build-spec.md` and `.agent/W5-04-build-spec.md`, at the same standard as the W5-01/W5-03 specs:
   - schema/migration (or state "no migration, reservation unused"), DTOs with key tables, refusal codes, producers/fixtures with clocks, unit cards of at most 6 units, split into sub-slices if larger;
   - per-unit file lists, including routes, nav, registry, ledger, guards, composition, `main.py`, seed tools and test files the change will break;
   - every copy literal, including loading, error, empty and refusal text;
   - table columns and cells;
   - status and notice text per currentness state;
   - capture states with named producers and the clock;
   - guard notes checked against the real `tools/checks/*`.
   - Every screen element maps to its mock element. Any departure is labelled `MOCK DEVIATION` with its reason and alternatives; graphics stay graphics, through registered graphics modules.
3. A readiness self-check at the end of each spec. Dry-read every unit card as an implementer against main and list any decision still left to the builder. The list must be empty.
4. Decisions: add `D-2026-10-22-w5-02-w5-04-buildspec` to `.ai/DECISIONS.md`.

Write only these files. Do not commit. End your output with:
- each slice's units, in order;
- the migrations used;
- every `MOCK DEVIATION`;
- any question that genuinely needs the owner (normally none).
