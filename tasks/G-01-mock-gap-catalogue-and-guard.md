# G-01 — Mock-gap catalogue and orphan guard

Status: done (owner accepted conditionally 2026-10-13; reviews ACCEPT; merged to main by coordinator)
USER_REVIEW_REQUIRED: true
Depends on: owner-confirmed `D-2026-10-12-mock-gap-closure-mechanism` sections 1–2
Branch when activated: task/G-01-mock-gap-catalogue-and-guard
Planner: Codex, 2026-10-12

## Visible outcome

An honest missing-capability message in a supported Site view has a stable, inspectable gap ID. The catalogue and normal checks catch orphaned IDs and new untagged missing-capability copy. This enables G-02's visible V-01a pilot; it does not delay the current V-01a review or merge.

## Acceptance

- Migrate `v69-dependency-registry-pilot.json` to a versioned schema with `mock_gaps`. Each distinct missing claim or interaction has a stable `G-<screen-or-shared>-<claim>` ID, the fields and allowed values in the confirmed decision, reviewed existing-node AND prerequisites, and one or more stable UI placements or an explicit `unplaced_reason`. Reused claims share an ID; normal zero/loading/error states do not become gaps. `owner_withheld` has recorded owner decision and revisit trigger. `unplanned` remains pending allocation.
- Extend the dependency checker to reject duplicate/unknown IDs, invalid screen/panel portion/element references, invalid wave/status/source combinations, cycles or unknown technical prerequisites, open gaps without placement or reason, and resolved gaps lacking reviewed source, UI and visual evidence. At G-01 close, validate every `gap_id` and ledger/UI reference that exists, but require complete `gap_ids` coverage only for an explicit `gap_enrolled_screens` list (initially empty). G-02 enrolls `sites`, `foundation`, `readiness` and `sld` and must then cover every non-core/open portion in those four screens. An open W1 screen that is already built cannot use “screen not built” as `unplaced_reason`; name the real absence or pending UI placement. The first G-01 element tag below does not enroll all of Readiness.
- Provide a typed missing-state UI component/API carrying `gapId` as metadata, never product copy. It resolves only known open gaps or a reviewed resolved transition. Static/translated text uses a stable placement ID; conditional branches carry their own reference.
- Hook a scoped product-source/AST orphan scan into `tools/check-all.ps1`. It reports file/line for new untagged “not available yet” and equivalent missing-capability copy, excluding docs, tests and unrelated runtime zero/error messages. Start with a dated, enumerated legacy baseline, including scope and reason. The baseline may shrink but cannot gain entries; newly touched V-01a placements are checked immediately. Keep the guard compatible with V-01a's independent merge.
- First real tagged placement: the visible gateway **firmware not available yet** state on `/sites/KOBO-001/foundation/readiness`, ID `G-readiness-gateway-firmware`, placement `readiness.gateway.firmware`. Register its absent-source boundary and source owner; tag the existing product copy through the typed component without inventing firmware data. Add focused Vitest checks for this real placement, conditional gateway-contact missing branches, reload and exact `data-gap-id` membership. Mutation tests must fail on an unknown UI ID, an unused open catalogue ID without `unplaced_reason`, and new untagged missing-capability copy; a legacy-baseline expansion must fail.
- `delivery_next_work.cjs` reads/validates the catalogue but ignores it for candidate scoring. Add a fixture that runs next-work with no `mock_gaps`, then with open absent-source gaps including one linked to a W1 core portion, and asserts identical decision, eligible candidate IDs, scores and path distances. Preserve the approved W1 core paths, K=10 and current ranking/refusal fixtures; a conditional visual pass cannot promote a partial panel or screen to Real.

## Review and checks

Independent review samples catalogue↔panel↔UI joins and the mutation failures. Run focused Vitest, `node frontend/docs/architecture/check_v69_dependency_registry.cjs`, `python frontend/docs/architecture/check_v69_ledger.py`, delivery checker fixtures, and `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1 -Python python`. Show the real Readiness gateway panel with a populated central-contact read and with unknown/unavailable contact while firmware stays explicitly missing, at 1440 and 390 pixels. Owner checks the visible missing-state treatment. No non-core scoring or completion policy is authorized before W1 exit.

## Review Outcome (recorded by coordinator, 2026-10-13)

- Reviews read (both): `.agent/G-01-review.md` RETURN (Finding 1 duplicate placement; Finding 2 browser evidence owed); `.agent/G-01-fix-rereview.md` ACCEPT (`e79ce8b`). Browser evidence 113/113 at 1440/390 recorded in the packet; screenshots kept at %LOCALAPPDATA%/AssetOps/evidence/g01.
- Architect: `.agent/architect-G-01-answers.md`, decision `D-2026-10-13-g01-placement-and-orphan-scan-boundary` (Q1-Q4 ratified; C5/C7 are G-02 carries).
- Owner checkpoint: `.agent/owner-G-01-acceptance-2026-10-13.md` — accepted conditionally; nothing becomes Real.
- Carries: `.ai/MILESTONE_REVIEW_BACKLOG.md` "G-01 carries (2026-10-13)".
