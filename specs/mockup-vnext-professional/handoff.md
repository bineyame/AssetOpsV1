# Handoff (PARTIAL): mock-up vNEXT professional pass

Branch `task/mockup-vnext-professional` (worktree `/opt/assetecon/AssetOpsV1-mockup`). Stopped at the context budget.
Plan: `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/REVISION-PLAN-professional.md`.

## Done (commits 6922e5559, b6bb46813)
- OD-6: "plan" used for a declared target is now "target" on every loop screen (`tools/plain_target_sweep.py`, exact substrings; regex patterns over data-file text kept intact). Factor tables, waterfall, Financials, operations tables, attention labels ("Off target"), banners.
- One display vocabulary `PLAIN_WORDS` / `plainWords()` in `loop-core.js` (after `tagReplay` in `afterRender` and drawer open): breakdown, period, simulation, allowed, evidence type, moves, base factor, status, sum.
- Design-value label is now "Design estimate: not yet tested on your recorded data" (source, `tools/audit.mjs`, `tools/gen_docs.cjs`).
- Footer plain; "Tenant configuration" renamed "Organisation settings"; theme toggle in the top bar (`themeToggle`, system/light/dark, localStorage guarded); `theme.css` (tokens, dark theme, spacing, tables, laptop breakpoints, quiet review bar, utilities `.layout-main-side`, `.side-panel`, `.status-pill`, `.who`, `.action-list`, `.kpi-row`).
- Checks: `tools/render_text.cjs` (jsdom, 202 renders, 0 script errors), `tools/vocab_check.cjs` (0 hits; planted product-source violation gave 3 hits, exit 1, reverted). `hand_typed_scan.py` 0; `check_manifest.py` 3762 passed.

## Next
1. Act first: Finding triage first (`attentionList`/`ATTN_OF` in `loop-portfolio.js:79-85`) in `.layout-main-side`; plan summary in `.side-panel` (status "Proposed by the system · awaiting the operator executive's approval", meters, value, spend threshold "not set", Open the plan).
2. New drill-down `portfolio/act-first/plan` (register like `portfolio/scope/pilot`, `loop-init.js`): move current `actFirstScreen` body (`loop-portfolio.js:148-172`); Actions per item from `DERIVED.options[id].cost_lines` with creator/owner role (design §2.6) and due = `restore_date` or "not set"; approval panel. Update `tools/audit.mjs:91,103,107,156` and `tools/rendered_strings.cjs:30` routes to the plan page.
3. Decision page "Who decides" strip (`decisionScreen` in `loop-site.js`): system recommends, accountable role chooses, Actions created with origin/membership/release rule (§2.4 step 4, OD-8).
4. What changed: Actions with owners, plan review (§2.8).
5. Earlier v7.0 views keep record codes (F-104, ACT-048, ...) in headings/body: 274 hits on 61 routes, reported by the check, not failing.

## Risks / not run
- No Chromium or playwright-core here; installing playwright-core + Chromium into the scratchpad was refused by the permission classifier. So `tools/run-audit.sh`, all screenshots and any visual check of `theme.css` are NOT RUN. The audit's switch checks and "preserved identical" check are unverified after these edits.
- Design gaps: person names for roles; per-Action due dates; demo spend-threshold value; plan approval state and version for the demo.
