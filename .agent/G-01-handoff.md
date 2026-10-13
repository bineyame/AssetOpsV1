# G-01 handoff and design (Implementer coordinator, 2026-10-13)

Contract: `tasks/G-01-mock-gap-catalogue-and-guard.md`. Decisions: `D-2026-10-12-mock-gap-closure-mechanism`,
`D-2026-10-13-g-gap-packet-activation` (`.ai/DECISIONS.md` ~4081/4085); detail in
`.agent/architect-mock-gap-mechanism-answers.md` sections 1-2 and `.agent/architect-G-activation-answers.md` F2/F3.
Branch `task/G-01-mock-gap-catalogue-and-guard`. Never commit `.agent/coordinator-handoff.md`. No push, no merge.

## Design (binding for all phases)

### A. Registry catalogue (`frontend/docs/architecture/v69-dependency-registry-pilot.json`)
- `schema` -> `assetops.v69.dependency-registry.pilot.v3` (update `check_v69_dependency_registry.cjs:19` and
  `check_v69_ledger.py:46`).
- New top-level `mock_gaps`: `{version: 1, decision: "D-2026-10-12-mock-gap-closure-mechanism",
  scoring: "read and validated by next-work; ignored for candidate scoring until an owner-approved W1-exit policy",
  gap_enrolled_screens: [], gaps: [...]}`.
- Gap fields (all present on every gap): `id`, `screen_ids[]`, `panel_portion_ids[]`, `element_ids[]`, `claim`,
  `boundary {window, subject, source, cannot_mean}`, `missing_kind` (decision|data_source|contract|build|visual),
  `status` (open|resolved|owner_withheld), `target_wave` (a wave key in `delivery_plan.waves` or `unplanned`),
  `allocation` (`"pending owner review"` iff unplanned, else an owner allocation evidence path), `requires[]`,
  `source_status` (existing|absent|undecided), `ui_placements[]`, `unplaced_reason` (string|null), `owner_or_role`,
  `evidence {source, ui, visual, reviewed_by}` (each string|null), `review_trigger`. Conditional:
  `owner_decision {evidence, reason, revisit_trigger}` for owner_withheld; `evidence.ui_transition` for a resolved gap
  the UI still references.
- Portions in `w1_panel_mapping` may carry optional `gap_ids[]`; screen-ledger rows may carry optional `gap_ids[]`.
- First entry `G-readiness-gateway-firmware`: screen `readiness`, `element_ids: ["readiness:2.firmware"]`,
  no portion (G-02 decides portion joins), data_source / absent / open / unplanned, `requires: []` (no reviewed node
  proves the claim), placement `readiness.gateway.firmware`. Ledger row `readiness` gets
  `gap_ids: ["G-readiness-gateway-firmware"]`. Does NOT enroll readiness.

### B. Validation (`frontend/docs/architecture/mock_gaps.cjs`, pure, exported `validateMockGaps(registry, opts)`)
Returns typed errors `{type, id, reason}`. `opts`: `{contracts, screenIds?, screenLedger?, requirePresent}`.
Rules: catalogue present (if requirePresent) and version 1; id regex `^G-[a-z0-9]+(-[a-z0-9]+)+$`, unique, no
collision with registry node or visual-gate IDs, prefix `G-<one of screen_ids>-` or `G-shared-` (>=2 screens);
screen_ids known; portion IDs exist in `w1_panel_mapping` on a listed screen; element IDs
`<screen>:<panel>.<slug>` with known panel key on a listed screen; at least one portion or element; enums;
combinations: resolved needs source existing + wave not unplanned + source/ui/visual/reviewed_by evidence + all
requires resolved; owner_withheld needs complete owner_decision; open/withheld `data_source` cannot have source
`existing`; `allocation` consistent with target_wave; requires = known non-product nodes or gap IDs, no gap cycles;
open gap has exactly one of non-empty `ui_placements` / non-empty `unplaced_reason`; placement regex
`^[a-z0-9-]+(\.[a-z0-9-]+)+$` with first segment a listed screen or `shared`; `unplaced_reason` matching
/not built/i is rejected for any W1 screen; portion `gap_ids` known and joined both ways with the gap's
`panel_portion_ids`; ledger `gap_ids` (when present) equal exactly the gaps listing that screen; every
`gap_enrolled_screens` screen: every non-core portion whose state is not `delivered` has non-empty `gap_ids`, and its
ledger row has `gap_ids`.
- `check_v69_dependency_registry.cjs` calls it with `requirePresent: true` plus ledger; `delivery_next_work.cjs`
  `nextWork` calls it with `requirePresent: false` (absent catalogue = empty), refuses on errors (type `mock_gaps`),
  adds an informational `gap_catalogue` summary to the report and NEVER uses gaps in scoring/paths.

### C. UI (phase b)
- Typed mirror `UI_GAP_CATALOGUE` (`{ [gapId]: {status: "open" | "resolved_transition", placements: readonly [...]}}`
  `as const`) and component `<MissingClaim gapId placement [as] [className]>children</MissingClaim>` rendering
  `data-gap-id` + `data-gap-placement`; gapId is never product copy. Unknown id/placement is a TS error and a runtime
  throw. Location chosen so `tools/checks/*` accept it.
- Readiness: split firmware out of `GATEWAY_NOT_AVAILABLE_YET` (`ReadinessOverview.tsx:296`), render firmware through
  `MissingClaim` in every gateway branch; no firmware value invented.

### D. Orphan scan (phase c)
- `tools/checks/missing-claim-scan.mjs` (TypeScript AST from `frontend/node_modules/typescript`), baseline
  `tools/checks/missing-claim-baseline.json` (dated, enumerated, scope, reason, exact counts). Shrink-only: exact count
  equality, subset of the merge-base-with-main baseline when present, total <= frozen seed ceiling.
- Checks mirror <-> registry and every MissingClaim usage <-> mirror; every mirror placement used.
- Mutation tests (node --test) + check-all guards.

## Phase log
(phases append below: what landed, commit, anchors, open risks)

### Phase a (schema + checker + next-work invariance) - landed
- Registry schema v3 + `mock_gaps` with `G-readiness-gateway-firmware`; ledger `readiness.gap_ids`.
- `frontend/docs/architecture/mock_gaps.cjs` `validateMockGaps`/`summarizeMockGaps`; wired in
  `check_v69_dependency_registry.cjs` (requirePresent, ledger joins) and `delivery_next_work.cjs` nextWork
  (refuse type `mock_gaps`, report `gap_catalogue`, no scoring use).
- Fixtures: `test_mock_gaps.cjs` (13, in check-all as "Mock-gap catalogue fixtures"); `test_delivery_next_work.cjs`
  F3 invariance + invalid-catalogue refusal (35 pass).
- Next: phase b (UI mirror + MissingClaim + readiness firmware placement + Vitest).

### Phase b (typed MissingClaim + firmware placement) - landed
- `frontend/src/ui/gapCatalogue.ts` (`UI_GAP_CATALOGUE` mirror, `GapId`, `GapPlacement`, `isKnownGapPlacement`) and
  `frontend/src/ui/MissingClaim.tsx` (`data-gap-id`/`data-gap-placement`/`data-gap-status`; unknown pair = TS error +
  runtime throw), exported from `frontend/src/ui/index.ts`.
- `ReadinessOverview.tsx`: `GATEWAY_FIRMWARE_NOT_AVAILABLE_YET` split from `GATEWAY_NOT_AVAILABLE_YET` (latter now
  uptime/completeness/signal only, still untagged -> phase c baseline); firmware `<MissingClaim as="p">` rendered
  unconditionally after the branch body in `GatewayStatusPanel` (so present in loaded/unknown/unavailable/not_found/none).
- Tests: `src/ui/__tests__/MissingClaim.test.tsx` (3, incl. @ts-expect-error unknown id/placement);
  `siteFoundationRevision.test.tsx` describe "G-01: the catalogued gateway firmware missing state" (3).
- Next: phase c orphan scan `tools/checks/missing-claim-scan.mjs` + baseline + check-all + mutation tests.
