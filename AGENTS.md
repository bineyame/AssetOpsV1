# AssetOps Agent Guide

AssetOps turns evidence from energy and cold-chain Sites (mini-grid, cold chain,
EV charging) into bounded operational and economic conclusions, and verifies
the interventions taken on them.

## Read, in this order

1. `.ai/START_HERE.md`: router. Current direction, authority order, which mock
   governs which work.
2. `.ai/NOW.md`: the active lanes, each with its spec.
3. `.ai/ROLE_CONFIG.md`: who plays which role, and the live role rules.
4. `.ai/RULES.md`: project rules, workflow (W1-W9) and the keep-it-tidy rules.
5. The spec your dispatch names, by the sections it names.

Stop there. Everything else is found on demand.

## Find on demand

- Decisions: grep the ID in `.ai/decisions/index-*.md` (`.ai/decisions/INDEX.md`
  explains), then open the named file at that ID; never read a part whole.
- Built state: grep the slice ID in `.ai/state/index-*.md`, then read that one
  section of the area file.
- Specs: `specs/INDEX.md`. Owner words: `owner/INDEX.md` (files verbatim in
  `.agent/owner-*.md`), by the file a spec or NOW cites.
- Product glossary and old boundaries: `.ai/PRODUCT.md`, `.ai/ARCHITECTURE.md`,
  only where `.ai/START_HERE.md` says they still apply.

## Do not read by default

- `.ai/history/`, `tasks/archive/`, `tasks/completed/`, and any `archive/` folder.
- `.agent/` beyond the files your spec or `.ai/NOW.md` names (it is scratch,
  reviews, packets and evidence).
- Evidence and capture folders (`*-evidence/`, `*-captures/`, screenshots, logs).
- `frontend/mockups/v69/` and `frontend/mockups/v71/` (owner, 2026-11-18: not
  to be read).
- `.ai/FEATURE_MAP.md`, `.ai/ARCHITECT_DEMO_RECOMMENDATION.md`,
  `.ai/PLANNING_HANDOFF_*.md`, `.ai/PLANNING_GUIDANCE.md`,
  `.ai/MILESTONE_REVIEW_BACKLOG.md`, `.ai/ARTIFACT_INDEX.md` (history).

Never work on `main`: one branch per slice or task. Keep context small.
