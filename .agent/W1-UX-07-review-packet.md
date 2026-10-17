# W1-UX-07 review packet: full v6.9 left menu with unavailable entries

Task: `tasks/W1-UX-07-full-rail.md`. Contract: `D-2026-10-17-w1-rail` (`.agent/architect-W1-UX-07-answers.md`); owner decision `.agent/owner-rail-decision-2026-10-17.md`.
Branch `task/W1-UX-07`, base `3bb1b8b2`. Reviewer diff: `git diff 3bb1b8b2..HEAD -- ':!.agent'`.
USER_REVIEW_REQUIRED: a fresh independent review gates the merge, and the owner sees the menu in the combined W1 walkthrough (new Part 17). Not merged.

## Outcome delivered

- The operator rail shows the six v6.9 groups and eleven roots, in the order of `screens.js` `ROOTS`/`rail()`. Sites (`/sites`) and Findings (`/findings`) are links. The other nine are `<li>` text rows: the same icon slot, muted (`--rail-eyebrow`, measured contrast 6.1:1), and the visible status "Not available yet" under the label. Each row's accessible name is `"<label>, Not available yet"` (an `aria-label` on the li). A row has no href, `to`, handler, tabindex, role, title or pointer.
- Item model: a discriminated union. `NavRailUnavailableItem` has `kind: "unavailable"; to?: never`, so `tsc` rejects a route on an unavailable root. A `@ts-expect-error` test proves this. Lab rail items are unchanged, because `kind` is optional on live items.
- Workspace footer: `WorkspaceShellLayout` still decides whether it exists, using the gate through `simulatorLabWorkspaceEntryPoints`. It now renders the `Workspace utilities` landmark (visible "WORKSPACE" plus "Open Simulator Lab") and hands it to `OperatorShellLayout` through the outlet context. `OperatorShellLayout` places that footer under the rail and stays flag-free. The old bar above the shell and its CSS are removed, so the link appears once. With the gate off there is no footer, label or link. The "Demo workspace / 3 sites" line is omitted.
- At 390 px the existing narrow shell wraps the rail above the content. All rows, statuses and the footer stay in DOM order and inside the viewport, with no page overflow.

## Files materially changed

- `frontend/src/ui/NavRail.tsx`, `RailIcon.tsx` (8 v6.9 root icons), `index.ts`, `primitives.css` (unavailable row and footer styles; dead `.workspace-bar` rules removed)
- `frontend/src/shell/OperatorShellLayout.tsx` (the `operatorRailItems` inventory, one item per line; footer placement), `WorkspaceShellLayout.tsx` (footer via outlet context)
- Tests: new `shell/__tests__/operatorRailInventory.test.tsx` (19 tests); `operatorRouteFrames.test.tsx` group expectation changed from `OPERATE` to the ruled inventory
- Guards: `tools/checks/navigation-truthfulness.ps1` (new `Get-OperatorRailFailures` replaces the old two-item rail block; the Site tab/subtab, parameterless and Foundation checks are untouched); new `tools/checks/navigation-rail-fixtures.ps1` (14 mutation fixtures, registered in `check-architecture.ps1`); `tools/checks/missing-claim-scan.mjs` (one reviewed exemption) and `test_missing_claim_scan.mjs` (2 tests)
- Evidence: new `tools/w1-ux-07-rail-evidence.mjs`; walkthrough Part 17 in `.agent/W1-UX-combined-owner-walkthrough.md`

## Acceptance criteria

| Criterion (ruling) | Status | Evidence |
| --- | --- | --- |
| Exact groups, labels and order (OPERATIONS, not OPERATE); group headers visible | Met | `operatorRailInventory` order test; `operatorRouteFrames` group test; browser claims at 1440 and 390; mock rail equality claim |
| Only Sites and Findings live, each a registered route rendering a truthful frame | Met | Test asserting two links; navigation test checks h1 and that it is not "Page not available"; guard route check |
| Unavailable: visible status, accessible name with label and status, muted but readable, no href/route/handler/tab stop/pointer, Enter/Space inert, decorative icon, no title | Met | 9 parametrised tests plus a click/keydown test; browser claims for cursor, contrast >= 4.5 (6.1), and Tab never landing on a row |
| Not a disabled button; no title-only explanation | Met | Rows are `li` with no `aria-disabled` and no `title`. See Known Deviations on `aria-disabled` |
| Footer: Lab link only when gated on, in WORKSPACE placement, not an operator group, no duplicate; gate off shows nothing | Met | Footer tests for gate on and off; existing `simulatorLabWorkspaceEntryPoint` tests (landmark name kept) pass; browser gate on 118/118, gate off 62/62 |
| Demo workspace line omitted | Met | Tests in both gate states |
| Guard amended, fail-closed: six groups and eleven labels, two live, live targets registered (not the catch-all), unavailable carries no destination, typed model, unparseable or missing inventory fails | Met | `Get-OperatorRailFailures`; 14 fixtures, including a dead link, a handler, a missing route, a removed route, an unknown root, a typo, OPERATE, an unreviewed promotion, a missing kind, an unparseable line, a renamed inventory, a link outside the inventory, and the type losing `to?: never` |
| Guard proven on real files | Met | A planted `to: "/assets"` on Assets gave 2 failures ("Dead link: ... 'Assets' carries 'to'" plus the inventory mismatch). Live Findings pointed at `/insights` gave 2 failures (`'/insights' ... not a route registered`). Both reverted, after which the check returns 0. Weakening the guard's dead-link test made `check-architecture` fail through the fixture module; reverted |
| Old Site tab rules not weakened | Met | Those functions are unchanged |
| 390 px: all groups, roots, statuses and footer readable in DOM order, no horizontal overflow, label kept with status, focus order | Met | Browser claims at 390 (scrollWidth 390/390; every row inside the viewport; label and status inside the row; Tab gives Sites, Findings, Open Simulator Lab) |
| Orphan scan: exempt only the identified rail status element | Met | `REVIEWED_EXEMPTIONS`: one file, one const, exact text, and only if every reference is in that file. Fixtures show the same phrase in another file, another const, inline copy, an import leak, or no exemption list all still fail |
| W1 vocabulary scan over the rail | Met | `t028Vocabulary` passes. The `data-vocabulary-exempt="lab"` now wraps only the Lab label span |
| Lab rail unchanged | Met | `SimulatorLabShell` untouched; Lab tests pass |

## Checks run (final revision `6b1e60dc`, plus docs)

- Focused: `operatorRailInventory`, `operatorRouteFrames`, `simulatorLabWorkspaceEntryPoint`, and `t028Vocabulary` all pass.
- `npx.cmd tsc --noEmit`: exit 0. `npm.cmd run build`: built. The only warning is the existing chunk-size one.
- Full `npm.cmd test` on `50a90e11` (the code is the same as HEAD; the later commit only adds a tools script): **75 files, 1931 tests passed**. An earlier run caught the vocabulary-exemption regression (1 failed), which was fixed in `1e31df2d`.
- `tools/check-all.ps1 -ExecutionPolicy Bypass`: **All 10 guards passed** (Architecture seams includes the new "Operator rail guard fixtures" seam).
- Browser: v01a walkthrough (`--db assetops_v01awalk_w1ux07 ... prepare/serve`, APIs 8970/8971, web 5470/5471). `node tools/w1-ux-07-rail-evidence.mjs <dir> on /sites /sites/KOBO-001/foundation 5471/sites /findings`: 118/118. Gate off was run with `config/app-config.json` flipped temporarily and then reverted (`git status` clean): `/sites`, `/findings` 62/62. Screenshots in the session scratchpad (`w1ux07-on`, `w1ux07-off`), not in git. Fixtures dropped (`drop`: both DBs and the work folder removed), and ports were confirmed free.
- No backend change, so no backend suite was run.

## Known deviations

- **No `aria-disabled` on unavailable rows.** The ruling allows it but does not require it. ARIA 1.2 deprecates `aria-disabled` on a `listitem`, and the status is already in the visible text and in the accessible name. So it is omitted, and the row cannot read as a switched-off control.
- **Footer link label stays "Open Simulator Lab"**, the existing `SIMULATOR_LAB_ENTRY_POINT_LABEL` that the gate tests use. The mock says "Simulator Lab".
- **Workspace landmark moved.** The `Workspace utilities` landmark moved from a bar above the shell into the rail column. It keeps its accessible name, and it is a sibling of the `Operator routes` nav, not nested in it.

## Residual risk

- The guard parses `operatorRailItems` line by line, one object per line. A reformat to multi-line objects fails closed, as intended, but the fixtures have to move with it.
- At 390 the rail is about 575 px tall above the content, which pushes the page down. This is within the ruling ("may move above"), but it is a visual cost the owner should judge.
- The orphan-scan exemption mechanism is new guard surface. It is limited by file, const and text and is guarded against an import leak.

## User-review focus

1. The greyed rows at 1440 beside the mock, and whether the muted tone reads as "not built" without hurting readability.
2. The menu height at 390 px.
3. The WORKSPACE footer, and that the bar above the page is gone.
