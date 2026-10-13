# G-02 handoff (V-01a mock-gap pilot)

Task `tasks/G-02-v01a-gap-pilot.md`; branch `task/G-02-v01a-gap-pilot` from `42bd74d` (main `5625447`). Never stage `.agent/coordinator-handoff.md`; stage by explicit path only.

## Phase a/b - catalogue, enrollment, UI tags (commit `402e047`)

- Registry `mock_gaps`: 20 new gaps (+ firmware, + 2 finding-evidence). `gap_enrolled_screens = [sites, foundation, readiness, sld]`. Portion `gap_ids` on all eight non-core open portions: `sites:2#a`, `foundation:2#b` (productive-use, obligation-policy), `readiness:2#a/#b`, `3#a/#b`, `4#a/#b`. Ledger `gap_ids` on the four rows.
- Placed gaps (mirror `frontend/src/ui/gapCatalogue.ts`): sites operating-view (cell + analysis note), attention-counts, setup-progress; foundation productive-use, financial-assumptions, change-record, constraint-evidence; readiness commissioning (5 placements), gateway uptime / completeness / signal-strength (C5 split) + firmware, source-contact (gateway line, registration-only line, sources caption); sld protection-metering, reporting-status (note clause + "Readings are not assessed in this view.").
- Unplaced (reason in registry): foundation obligation-policy, readiness gateway-registration, gateway-contact, source-registration, confidence-effect, evidence-capability.
- UI anchors: `SitesIndex.tsx` SiteTable/SiteRow; `StoredFoundationViews.tsx` IdentityPanel and SLD note (`data-sld-missing`); `FoundationRevisionPanel.tsx` evidenceOrChange + RegisteredSourcesPanel caption; `ReadinessOverview.tsx` ReadinessEvidenceTable, GatewayStatusPanel, RegistrationOnly; `SiteSingleLineDiagram.tsx` configured status line.
- Rendered text is unchanged except the gateway C5 split (three new sentences, firmware pattern). Baseline 15 -> 12.
- Tests: `siteFoundationRevision.test.tsx` "G-02: V-01a pilot missing-state placements" (4) + G-01 block updated (C6 loading); `sitesIndex.test.tsx` G-02 test; `test_mock_gaps.cjs` real-registry asserts.

## Phase c - scan (commit `2f2be4d`)

- `missing-claim-scan.mjs`: PATTERNS + `not tracked yet`, `commissioning confirmation not recorded` (C7). `mergeBaseBaseline(run)` returns `{baseline, ref, skipped, atHead}`; `baselineComparisonNote` is appended to the result line (C1).
- Fixtures: `test_missing_claim_scan.mjs` 17 pass (6 new).
- Real-tree proofs (reverted by `git checkout`): portion gap_ids emptied -> `gap_enrollment` + `gap_join`; setup-progress const rendered outside MissingClaim -> `untagged_copy SitesIndex.tsx:333`; extra claim inside the uptime element -> scan passes (C9 hole) but 2 G-02 Vitest tests fail; git off PATH -> result line says `merge-base baseline comparison SKIPPED (... spawnSync git ENOENT); only the seed ceiling 16 limits growth`.
- Full vitest after phase b: 61 files, 1445 passed.

## Phase d - next

1440/390 app-vs-mock evidence per manifest ID (sites, foundation, readiness, sld), packet, owner walkthrough, records. Questions: `.agent/G-02-questions-1.md` (Q1-Q6, defaults shipped).

## Open risks

- SLD per-node slot text and captions restate the reporting-status fact untagged (Q1).
- `tools/v01a-foundation-evidence.mjs` and `tools/g01-firmware-evidence.mjs` assert the pre-G-02 combined gateway copy; they are historical and would fail on rerun.
