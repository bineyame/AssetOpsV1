# G-01 — Mock-gap catalogue and orphan guard

Status: open planning packet (M); not activated
USER_REVIEW_REQUIRED: true
Depends on: owner-confirmed `D-2026-10-12-mock-gap-closure-mechanism` sections 1–2
Branch when activated: task/G-01-mock-gap-catalogue-and-guard
Planner: Codex, 2026-10-12

## Visible outcome

An honest missing-capability message in a supported Site view has a stable, inspectable gap ID. The catalogue and normal checks catch orphaned IDs and new untagged missing-capability copy. This enables G-02's visible V-01a pilot; it does not delay the current V-01a review or merge.

## Acceptance

- Migrate `v69-dependency-registry-pilot.json` to a versioned schema with `mock_gaps`. Each distinct missing claim or interaction has a stable `G-<screen-or-shared>-<claim>` ID, the fields and allowed values in the confirmed decision, reviewed existing-node AND prerequisites, and one or more stable UI placements or an explicit `unplaced_reason`. Reused claims share an ID; normal zero/loading/error states do not become gaps. `owner_withheld` has recorded owner decision and revisit trigger. `unplanned` remains pending allocation.
- Extend the dependency checker to reject duplicate/unknown IDs, invalid screen/panel portion/element references, invalid wave/status/source combinations, cycles or unknown technical prerequisites, open gaps without placement or reason, and resolved gaps lacking reviewed source, UI and visual evidence. Validate `gap_ids` on every non-core/open `w1_panel_mapping` portion and linked screen-ledger references as batches populate them; G-01 can seed explicit unplaced inventory for screens not yet built.
- Provide a typed missing-state UI component/API carrying `gapId` as metadata, never product copy. It resolves only known open gaps or a reviewed resolved transition. Static/translated text uses a stable placement ID; conditional branches carry their own reference.
- Hook a scoped product-source/AST orphan scan into `tools/check-all.ps1`. It reports file/line for new untagged “not available yet” and equivalent missing-capability copy, excluding docs, tests and unrelated runtime zero/error messages. Start with a dated, enumerated legacy baseline, including scope and reason. The baseline may shrink but cannot gain entries; newly touched V-01a placements are checked immediately. Keep the guard compatible with V-01a's independent merge.
- Add focused frontend Vitest checks for registered placement rendering, conditional missing branches, reload and `data-gap-id` membership. Mutation tests must fail on an unknown UI ID, an unused open catalogue ID without `unplaced_reason`, and new untagged missing-capability copy; a legacy-baseline expansion must fail.
- `delivery_next_work.cjs` reads/validates the catalogue but ignores it for candidate scoring. Preserve the approved W1 core paths, K=10 and current ranking/refusal fixtures; a conditional visual pass cannot promote a partial panel or screen to Real.

## Review and checks

Independent review samples catalogue↔panel↔UI joins and the mutation failures. Run focused Vitest, `node frontend/docs/architecture/check_v69_dependency_registry.cjs`, `python frontend/docs/architecture/check_v69_ledger.py`, delivery checker fixtures, and `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1`. Show one populated and one missing state at desktop and narrow widths where the first typed placement is introduced. Owner checks the visible missing-state treatment. No non-core scoring or completion policy is authorized before W1 exit.
