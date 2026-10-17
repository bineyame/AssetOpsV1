# W1-UX-07 review: full v6.9 left menu with unavailable entries

Reviewer: fresh independent Claude reviewer (not the author). Revision reviewed: `3526a0f2` (worktree `AssetOpsV1-review5`, detached). Diff: `git diff 3bb1b8b2..3526a0f2 -- ':!.agent'`.
Contract: `D-2026-10-17-w1-rail` (`.agent/architect-W1-UX-07-answers.md`); owner decision `.agent/owner-rail-decision-2026-10-17.md`; task `tasks/W1-UX-07-full-rail.md`.

## Verdict: ACCEPT

No High or Medium findings. The four Low findings below do not block the merge. They can be fixed on the branch or carried forward.

## Contract check (against the ruling)

- **Groups, labels and order.** `operatorRailItems` (`frontend/src/shell/OperatorShellLayout.tsx:49-61`) matches `ROOTS` and `rail()` in `frontend/mockups/v69/screens.js:940,966` exactly. The groups are OPERATIONS, INTELLIGENCE, WORK, ASSURANCE, BUSINESS and ADMIN. OPERATE is gone, and a test asserts that.
- **Live roots.** Only Sites (`/sites`) and Findings (`/findings`) are live, and both are registered inside the `OperatorShellLayout` route block in `App.tsx`. The tests click each one and assert the h1, and also assert that the h1 is not "Page not available".
- **Unavailable rows.** Each is an `li` showing the visible text "Not available yet". The `aria-label` reads "`<label>`, Not available yet". The row has no href, `to`, handler, tabindex, role or title, and its icon is `aria-hidden`. The union type `NavRailUnavailableItem { kind: "unavailable"; to?: never }` is proven by a `@ts-expect-error` test that `tsc` checks. Contrast of `#93a3bd` on `#16233f` works out to about 6.1:1, which I recomputed by hand and which matches the packet.
- **Workspace footer.** The footer and its Lab link render only through `simulatorLabWorkspaceEntryPoints(flags)`, and the link renders once. With the gate off, no footer, label or Lab text appears; tests cover both gate states. The "Demo workspace / 3 sites" line is absent in both states.
- **390 px.** The existing `@media (max-width: 640px)` operator rule wraps the rail above the content. The browser claims in `tools/w1-ux-07-rail-evidence.mjs` cover six groups, eleven roots, each status kept inside its row, rows inside the viewport, no horizontal overflow, Tab order, and both footer states. I could not rerun that script (it needs Chrome, the backend and a dev server). The packet records it as run (118/118 with the gate on, 62/62 with it off), not as skipped.

## Guard verification (planted by me on the real file, then reverted; `git status` clean after)

Each plant was run through `tools/check-architecture.ps1`:
- Dead link: `to: "/assets"` on the unavailable Assets row gave exit 1, with "Dead link: the unavailable operator rail root 'Assets' carries 'to'" plus the inventory mismatch.
- Missing route: live Findings pointed at `/insights` gave exit 1, with "'/insights' ... not a route registered in the operator route table" plus the inventory mismatch.
- Multi-line object: gave exit 1 ("Unparseable operator rail line"). A trailing `// c` comment on an item line also gave exit 1. Both fail closed.
- Restored tree: "Architecture check passed", exit 0.

The one-item-per-line parsing is fail-closed for reformatting, spreads, unknown keys, a missing `kind`, a renamed inventory, an unclosed array, and the inventory not being what is passed to `NavRail`. It has two narrow holes (Findings 1 and 2), and neither can be reached by an ordinary edit.

## Findings

1. **Low. Comment-skip regex can hide a live item in the inventory.** `tools/checks/navigation-truthfulness.ps1:565` (and `:635`)
   - **What is wrong.** Lines matching `^\s*(//|/?\*)` are skipped, so a code line that starts with the close of a block comment is ignored even though it is live code. I fed `Get-OperatorRailFailures` an inventory with an extra `  /* x` line followed by `  */ { kind: "live", to: "/portfolio", label: "Portfolio", group: "ADMIN" },` after Settings, and it returned 0 failures.
   - **Why it matters.** It is a dead link the guard does not see. Only a contrived edit reaches it, and the component tests (eleven labels, exactly two links) would still fail.
   - **Fix.** Skip only `//`-prefixed lines and lines inside a tracked `/* ... */` span, or treat any `*/` followed by code as unparseable.

2. **Low. The route-registration window extends past the operator block.** `tools/checks/navigation-truthfulness.ps1:671`
   - **What is wrong.** The scan runs from `<Route element={<OperatorShellLayout />}>` to the last `path="*"`. That window includes the `simulatorLabRoutes(...)` block after the operator `</Route>`. A literal `path="/sites"` placed outside the operator layout but before the catch-all would count as an "operator route".
   - **Why it matters.** Today nothing there uses a literal path, and the pinned expected targets limit the exposure. It is still looser than the ruling's "registered in the operator route table".
   - **Fix.** Stop the window at the `</Route>` that closes the operator block.

3. **Low. An aliased import leaks the orphan-scan exemption.** `tools/checks/missing-claim-scan.mjs:181,207`
   - **What is wrong.** The exemption is lifted when the const is referenced from another file. Identifiers under an `ImportSpecifier` are not counted, though, so `import { NAV_RAIL_UNAVAILABLE_STATUS as S } from "../ui"; <p>{S}</p>` on a product panel keeps the rail const exempt. I confirmed this with an in-memory `analyze` probe: the direct import and namespace (`ui.X`) leaks are caught, and the aliased leak is not.
   - **Why it matters.** The exemption's own stated defence against an import leak has a gap. The same alias blind spot already exists for MissingClaim-only consts, so this is a narrow, deliberate-edit path, not a general suppression. The rest of the exemption is narrow: one file, one const, exact text, and the reviewed fixtures pass.
   - **Fix.** Count `ImportSpecifier` nodes that have a `propertyName` (the imported name) as a reference in the importing file, and add an alias fixture.

4. **Low (owner judgment, not a contract gap). The status text is 9 px.** `frontend/src/ui/primitives.css:2188-2190`
   - **What is wrong.** `.nav-rail__status` uses `--text-rail-eyebrow` (0.5625rem, 9 px).
   - **Why it matters.** Contrast passes. Even so, the status is the one carrier of meaning, and 9 px is at the edge of "muted but readable", particularly at 390 px on a phone.
   - **Fix.** Consider `--text-rail` or about 10-11 px. Add it to the owner's walkthrough focus alongside the 575 px height.

## Deviations and other changes

- **No `aria-disabled`: accepted.** The ruling permits it but does not require it. ARIA 1.2 does not support `aria-disabled` on `listitem`, and the status is in both the visible text and the accessible name.
- **"Open Simulator Lab" label: accepted.** The ruling sets the footer placement, not the link text. Keeping `SIMULATOR_LAB_ENTRY_POINT_LABEL` preserves the existing gate tests. The mock text "Simulator Lab" is a fidelity preference for the owner.
- **Moved landmark: accepted.** "Workspace utilities" keeps its name and sits as a sibling of the "Operator routes" nav inside the side column (asserted), not nested in it. It appears once, and the old bar's CSS is removed.
- **575 px rail at 390: within the ruling** ("may move above"). The packet names it as a visual cost for the owner. I agree it is an owner judgment and not a blocker.
- **Tests: no assertion weakened.** Only three test files changed. In `operatorRouteFrames.test.tsx`, the OPERATE/one-item expectation was replaced by a stricter six-group expectation, with label and status for each row. `operatorRailInventory.test.tsx` is new (19 tests) and `test_missing_claim_scan.mjs` adds 2 tests. `simulatorLabWorkspaceEntryPoint` and `t028Vocabulary` are unchanged and pass.
- **Walkthrough Part 17: clear.** It gives no commands to run: it reuses the Part 1 servers, which use `$wt` paths. The mock address follows the established `#/sites` convention. It correctly explains that "Not available yet" is about a missing cross-site page, not missing site data. The Lab-off state can only be checked from the captures, because the walkthrough build has the Lab on.

## Checks run (by me, at `3526a0f2`)

- `npx.cmd tsc --noEmit` (frontend): exit 0.
- `npx.cmd vitest run` on `operatorRailInventory` and `operatorRouteFrames`: 2 files, 34/34 passed.
- `npx.cmd vitest run` on `simulatorLabWorkspaceEntryPoint`, `t028Vocabulary`, `w1Vocabulary` and `sharedVisualVocabulary`: 4 files, 47/47 passed.
- `tools/check-architecture.ps1` with `ASSETOPS_GUARD_PYTHON` set to the main venv python: "Architecture check passed", exit 0. That run includes the new "Operator rail guard fixtures" seam, whose 14 fixtures all pass.
- `node tools/checks/test_evidence_checks.mjs`: 10/10 passed.
- `node --test tools/checks/test_missing_claim_scan.mjs`: 22/22 passed, including both W1-UX-07 tests. `node tools/checks/missing-claim-scan.mjs` on the real tree: passed (31 tagged uses, 11 baselined).
- Guard plants: see "Guard verification" above.

## Not verified by me

- The full `npm.cmd test` and `npm.cmd run build`. I cite the implementer's run on `50a90e11`: 75 files, 1931 passed, and a successful build. `git diff --stat 50a90e11..3526a0f2` shows no `frontend/` change after that revision, so the run applies to the code under review.
- The browser evidence (`tools/w1-ux-07-rail-evidence.mjs`, 1440 and 390 px, gate on and off) and the screenshots. These need Chrome, the backend and a dev server, and the screenshots are not in git.
- `tools/check-all.ps1`. I ran only `check-architecture` and the missing-claim scan, which are the guards this slice changes.

## Residual risk

- Findings 1 and 2: the guard can be bypassed, but only by contrived edits. The component tests are the backstop for both.
- The line-per-item inventory format couples the guard to formatting: a Prettier reflow would fail `check-architecture`, which fails closed and is the intent.
