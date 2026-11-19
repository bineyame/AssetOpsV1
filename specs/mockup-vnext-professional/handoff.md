# Handoff: mock-up vNEXT professional pass (build complete; browser checks not run)

Branch `task/mockup-vnext-professional` (worktree `/opt/assetecon/AssetOpsV1-mockup`).
Plan: `Docs/demo-sprint/product-direction-layer4/interactive-mockup-vNEXT/REVISION-PLAN-professional.md`.
Packet: `specs/mockup-vnext-professional/packet.md`.

## Done
- First pass (6922e5559, b6bb46813): plain words, "target" not "plan" (OD-6), theme and layout layer, vocab and render checks.
- Second pass (a8fd856b6, 9e55785cb, bb3c2f6f7, aa7ff2562):
  - `fixtures.js` regenerated so `MANIFEST.demo_workflow` reaches the bundle.
  - Act first (`actFirstScreen`, `loop-portfolio.js`): Finding triage in the main column, each row with who decides; plan summary in the side panel.
  - The plan, `#/portfolio/act-first/plan` (`planScreen`, registered in `loop-init.js`): items as cards, the Actions under each, approval panel, switches, items left out, Actions that return to their creator when a case drops their item.
  - Decision pages: `whoDecides(id)` strip at the top of `decisionScreen` (`loop-site.js`).
  - What changed: KPI row, "Actions and their owners", "The plan's review", then the existing verdicts and rights.
  - Workflow helpers (`WF`, `PSTATE`, `releaseOf`, `deciderOf`, `actionRows`, `approvalPanel`) sit just above `planScreen` in `loop-portfolio.js`. `releaseOf` computes release from the rule and logs `console.error` when the data's stated release differs.
  - Audit routes moved to the plan page (`tools/audit.mjs`, `tools/rendered_strings.cjs`).
  - New check `tools/plan_switch_check.cjs` (jsdom).

## Next
1. Run the Playwright audit and screenshots (`tools/run-audit.sh --shots`) on a host with Chromium. Then regenerate `CHANGE-REGISTER.md` and `browser-audit.md` (`tools/gen_docs.cjs`), which will list the new plan screen.
2. Get the Architect to confirm the gaps listed in the packet.
3. Earlier v7.0 views still show record codes in their body: 256 hits on 60 routes. The check reports them but does not fail on them.

## Risks / not run
- No browser here, and installing one was refused, so no Playwright audit, no screenshots and no visual check at 1280/1366/1440/390 px. Layout evidence: not run, no browser.
