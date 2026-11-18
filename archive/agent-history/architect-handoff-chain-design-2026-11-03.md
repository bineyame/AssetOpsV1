# Architect handoff: outcome-chain design, 2026-11-03

Architect: Claude (`.ai/ROLE_CONFIG.md` "Architect Is Claude By Default"). Nothing is committed. Both documents are in `AssetOpsV1-plan2\Docs\demo-sprint\` and are untracked.

## Files
- `Docs/demo-sprint/implementation-logic-portfolio-sites-findings-actions.html` (main document, about 162 KB). What the build does today:
  - §1–7: data flow, the outcome mechanism, Portfolio, Sites, Findings, Actions, demo data per Site.
  - §8: links.
  - §9: gaps.
  - Part A: issues register I-01…I-25.
  - Part B: root causes RC1…RC5.
  - Part C: a short summary that links to the companion.
- `Docs/demo-sprint/implementation-logic-design-proposal.html` (companion, about 259 KB). The full design review and proposal.

## Where the agreed state lives (companion)
- **Agreed decisions:** section "Decisions agreed with the owner" (`#agreed`), AG-1 … AG-32, with the owner's words. All original OD-1 … OD-10 are agreed (§17). No owner decision is open.
- **Data:**
  - ERDs: §4.0 whole application (106 tables, 13 groups) and §4.1–4.2 the chain area.
  - DDL and evidence classes: §4.3 and §4.3b.
  - State machines: §4.4.
- **Service:**
  - Components: §5.1.
  - Algorithms: §5.2, A0 (event register) to A6.
  - Chain catalogue, demonstrated: §5b (YAML excerpt, consumers, strategies, graph validation, "Why?" trace, end-to-end on Kobo).
- **Sequences:** §6. **API:** §7. **UI:** §8. **Hard-wiring removed:** §8b. **Walkthrough:** §9.
- **Prior decisions:** §9b. **Alternatives:** §10. **Trade-offs:** §11.
- **Performance and scale path:** §11b (diagnosis P-1…P-6, budgets, ETag, guard).
- **Migration:** §12. **Tests and guards:** §13. **Issue-to-design map:** §14.
- **Next build:** QW-1/QW-2 (§14b), agreed and before the CH slices.
- **Slices:** §15.
  - QW-1/2 (about 3 units).
  - CH-0, CH-1a, CH-1b, CH-2, CH-3, CH-4, CH-5a, CH-5b, CH-6, CH-7, CH-8, CH-9, CH-10a, CH-10b: about 72 units in total.
  - Demo-critical subset: CH-0, CH-2, CH-3, CH-5a, about 21 units.
- **Integrations:** §16a, future integrations (design context only). **Out of scope:** §16.

## Conventions
- `B/` = `backend/assetops_backend/`; `F/` = `frontend/src/`; `M/` = `backend/migrations/versions/`. References are `path:line` at polC main `73a558a1b`.
- Sourcing tags:
  - `live` = read-only GETs on 2026-11-02 at about 21:30 UTC (serve on 8990, now stopped);
  - `work-dir` = `AssetOpsV1-polC\var\polish_full\*.json`;
  - `code`;
  - `doc`.
- Read-only SELECTs were made only on `assetops_polish_full_test`.
- Table count is 106: 104 literal `CREATE TABLE` names plus 2 created through a `{TABLE}` variable (`M/0037:27`, `M/0038:24`).
- Owner wording is always quoted verbatim in the AG log. Coordinator wording is never presented as the owner's.

## Loose ends
- **QW-1/QW-2:** not yet built. Measure on a demo build, never by restarting the owner's serve (§14b).
- **Thread ids in the §7 JSON are placeholders** (`T-…`). Every other id and value is from current data.
- **Performance diagnosis is from code reading, not a profile.** QW-1 produces the real numbers; update §11b once they exist.
- **§4.0 FK extraction** came from parsing the migrations. Only the chain tables were hand-checked.
- **Unverified UI claims:**
  - Whether any screen uses Portfolio `scope_disclosure` was not checked.
  - The Cold/EV board API-URL links are a defect found by code reading; they were not clicked.
- **Build specs not written yet:** the CH slices still need per-unit build specs (Planner = Codex) and an implementer dry-read per `.ai/ROLE_CONFIG.md`.
- **Scratch tools** (not part of the deliverable) are in the session scratchpad: `gen_erd.py` (ERD generator) and `schema.json`. Rerun the generator if the migrations change.
