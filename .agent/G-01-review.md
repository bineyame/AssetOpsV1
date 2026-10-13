# G-01 review - Mock-gap catalogue and orphan guard

Reviewer: fresh Claude Reviewer (did not author G-01). Date: 2026-10-13.
Branch `task/G-01-mock-gap-catalogue-and-guard`, HEAD `780500c`, diff `db98e54..780500c`.
Against: `tasks/G-01-mock-gap-catalogue-and-guard.md`, `D-2026-10-12-mock-gap-closure-mechanism` sections 1-2 and
`D-2026-10-13-g-gap-packet-activation`. Calibrated to `.ai/WORKFLOW.md` Review Packet: only expensive-to-reverse
defects, claims that would mislead an Implementer, and owner-only decisions are findings. Everything else is a carry.

## Verdict: RETURN (one small fix on the branch; the 1440/390 evidence is still owed)

The catalogue, validator, next-work invariance, typed component and baseline are sound, and I reproduced the
packet's results. One guard hole makes the packet's central claim, that new untagged missing-capability copy
fails the scan, untrue in practice. G-02 will lean on this guard across four screens, so it should be closed now
while it costs a few lines. Re-review can be narrow: Finding 1 plus its fixture.

## Findings

### 1. A catalogued placement can be rendered any number of times, anywhere, wrapping any copy (guard bypass)

- Where: `tools/checks/missing-claim-scan.mjs:127-141` (usage collection) and `:156-159` (`used` is a Set).
- Defect: the scan checks that each `<MissingClaim>` uses a catalogued (gapId, placement) pair, and that every
  catalogued placement is used at least once. It never checks that a placement is used at most once. Any number of
  `<MissingClaim gapId="G-readiness-gateway-firmware" placement="readiness.gateway.firmware">` elements can wrap
  unrelated copy in any product file. That copy then counts as tagged, never reaches the baseline, and the scan passes.
- Reproduced, then reverted with `git checkout`: I added this to `ReadinessOverview.tsx`:
  `const REVIEWER_PROBE = "Uptime not available yet: probe.";` and
  `<MissingClaim gapId="G-readiness-gateway-firmware" placement="readiness.gateway.firmware">{REVIEWER_PROBE}</MissingClaim>`.
  Result: `Missing-claim scan passed: 2 tagged placement use(s), 16 baselined legacy occurrence(s)`, exit 0.
  The uptime claim was silently catalogued as the firmware gap.
- Why it blocks:
  - The task requires "a stable placement ID" per static text, with each conditional branch carrying its own reference.
  - The packet and `gapCatalogue.ts` say the scan keeps every use equal to the mirror, and that new untagged copy fails.
  - Both claims would mislead the G-02..G-05 Implementers. Under deadline, the easiest way to silence the scan is to
    reuse an existing placement, and the guard would accept it.
  - Every mis-tag that lands is a wrong claim-to-gap join. It gets expensive to unwind once G-02 has tagged four screens.
  - The jsdom exact-membership test only catches a duplicate on the Readiness page. It does not catch one elsewhere.
- Fix (small):
  - In `analyze`, report an error such as `ui_duplicate_placement` with both file:line locations when a
    (gapId, placement) pair is used more than once. Reuse of a claim stays possible as the same gap ID at
    another registered placement, as the decision intends.
  - Add one mutation fixture to `tools/checks/test_missing_claim_scan.mjs`.
  - Optionally require each placement's first segment to match the screen that owns the file. This is a carry, not required.

### 2. Acceptance item still open: 1440/390 browser evidence (environment-blocked, not a code defect)

- Where: task "Review and checks", and packet "Layout evidence: not run".
- Defect: the task requires the real Readiness gateway panel at 1440 and 390 px, once with a populated contact read
  and once with unknown or unavailable contact, while firmware stays explicitly missing. It was not produced, because
  Postgres/Docker is down. The packet records this honestly as `not run` with its precondition, and does not claim a pass.
- I did not run it either (dispatch: Postgres down; no servers started).
  `tools/g01-firmware-evidence.mjs` passes `node --check`. Its claims include an exact text match, a single element,
  `right <= innerWidth`, `scrollWidth <= innerWidth`, no firmware value, and identical outerHTML after reload.
- Why it blocks merge, not the fix round: the claim stays unverified until the tool runs. The coordinator should run
  it, or get an owner waiver, before merge. It needs no code change.

## Owner-only decision

None new. Q1-Q4 are within Architect authority, and the shipped defaults are reasonable (see below).

## Verification of the dispatch points

1. **Next-work is unaffected by `mock_gaps`: confirmed.**
   - `delivery_next_work.cjs` uses the catalogue only at `:201` (validate, then refuse) and `:256` (an informational summary).
   - Nothing reaches candidates, paths, scores or the decision.
   - The fixture `test_delivery_next_work.cjs:429` compares status, decision, sorted eligible IDs, and for every
     candidate: score, reach, blocked, and path key/d/proof/portions. It does this with and without three open gaps,
     one linked to core `site:1#b`, and the comparison holds.
   - The diff removes no line from the existing fixtures. The registry diff touches only `schema` and `mock_gaps`,
     so K=10 and the W1 core paths are untouched.
   - Q4 (refuse on an invalid catalogue) is a safe default:
     - The registry checker already fails check-all on the same errors, so refusing adds no new blocking condition.
     - An absent catalogue is treated as empty.
     - The two callers differ in one input. Next-work derives known screens from panel contracts; the checker uses
       ledger IDs. I confirmed that every ledger screen has contracts today (0 differences), so they cannot disagree
       now (carry C3).
2. **Checker rejections: confirmed.**
   - On in-memory mutations of the real registry (no file edits), each of these produced its typed error:
     - unknown panel element, unknown portion, a one-way portion join;
     - duplicate ID (plus the placement collision);
     - resolved without evidence (4 errors), owner_withheld without a decision;
     - a product or unknown `requires`, a self-cycle;
     - an open gap without placement, "not built" on W1 Readiness;
     - a planned wave with pending allocation, an unresolved data_source claiming `existing`;
     - enrolling `readiness` (6 enrollment errors, as expected).
   - The joins hold. Registry `G-readiness-gateway-firmware`, element `readiness:2.firmware`, refers to panel 2,
     "Gateway status · GW-MG-01". From there:
     - ledger `readiness.gap_ids` lists the same gap;
     - the mirror `UI_GAP_CATALOGUE` has the same entry;
     - the one `<MissingClaim>` in `ReadinessOverview.tsx:491` uses it;
     - Vitest asserts the rendered `data-gap-id` set exactly.
   - The G-02 seam fits. Its seed list includes the excluded portions `sites:2#a` and `readiness:4#a`, and the
     enrollment rule covers every non-core, undelivered portion, including excluded ones, which matches.
3. **`<MissingClaim>`: confirmed.**
   - `gapId` appears only in `data-gap-*` attributes.
   - An unknown ID or placement is a TS error (the `@ts-expect-error` tests compile under `tsc`) and throws at runtime.
     The `toString` prototype key is rejected.
   - The firmware line is honest and invents no value.
   - Vitest covers the CURRENT, UNKNOWN, 503-unavailable, 404 and empty-gateway branches, reload, and exact membership.
     The loading branch is not asserted (carry C6).
4. **Orphan scan and baseline: confirmed shrink-only, apart from Finding 1.**
   - An untagged `"Uptime not available yet: probe."` in `ReadinessOverview.tsx` gave
     `untagged_copy ReadinessOverview.tsx:301`, exit 1.
   - Adding its baseline entry (total 17) gave `baseline_growth ... exceeds the frozen G-01 seed ceiling 16`, exit 1.
   - Removing a legacy entry while its copy remains gave `untagged_copy RunCommitPanel.tsx:315`, exit 1.
   - All three were reverted with `git checkout`. The working tree is clean apart from the coordinator's handoff file.
   - Scope (`isProductSource`) excludes `__tests__`, `*.test.*`, `src/test/` and `.d.ts`. Comments are not string
     nodes, and docs are outside `frontend/src`.
   - Q1 (not matching "not recorded") is reasonable. Most of those hits are runtime states of existing
     capabilities, and baselining them would create entries that can never honestly shrink.

## Checks run (my results)

- `npx.cmd tsc --noEmit` (frontend): exit 0.
- `npx.cmd vitest run` (frontend): ran under this session, 58 files, 1391 tests passed. This includes
  `MissingClaim.test.tsx` (3) and the G-01 describe block in `siteFoundationRevision.test.tsx`.
- `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1 -Python .venv/Scripts/python.exe`: `All 9 guards passed`.
- `node --test frontend/docs/architecture/test_delivery_next_work.cjs`: 35 pass, 0 fail. Run directly with `node`, it also passes.
- `node --test frontend/docs/architecture/test_mock_gaps.cjs`: 13 pass.
- `node --test tools/checks/test_missing_claim_scan.mjs`: 10 pass.
- `node tools/checks/missing-claim-scan.mjs`: passed, 1 tagged use, 16 baselined.
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: `Registry valid: 212 nodes, 11 linked pilot panels`.
- `check_v69_ledger.py`: `v6.9 ledger valid: 110 screens, 88 distinct models, 258 panels`.
- Not run:
  - `npm run build`.
  - Backend pytest (G-01 changes no backend code; Postgres is down).
  - The 1440/390 browser evidence (Finding 2).

## Carries (to `.ai/MILESTONE_REVIEW_BACKLOG.md`; none block)

- C1. `mergeBaseBaseline()` (`missing-claim-scan.mjs:219-227`) returns null silently on any git error, such as a
  shallow clone, a missing local `main` ref or a timeout. The main comparison is then skipped, and only the seed
  ceiling holds. On `main` itself, the merge-base is HEAD, so it compares the baseline with itself. Consider printing
  when the comparison is skipped. Until G-01 merges, a swap that removes legacy copy and adds new baselined copy at
  <= 16 is possible on this branch only.
- C2. A resolved gap's prerequisites must have node `status === 'resolved'` (`mock_gaps.cjs:550`). The registry also
  uses `recorded` and `pending owner`, so a resolved gap that requires a `recorded` decision node would be rejected.
  Settle this at the first resolution.
- C3. Next-work validates against screens derived from contracts, and the checker against ledger IDs. The sets are
  identical today. Pass `screenIds` from the same source if they ever diverge.
- C4. A ledger row without `gap_ids` is skipped. So a gap can list a screen whose ledger row has no `gap_ids`,
  meaning the join is one-way until that screen is enrolled. This meets "validate what exists", and enrollment closes it.
- C5. G-02 seam: `GATEWAY_NOT_AVAILABLE_YET` still bundles uptime, completeness and signal strength in one
  sentence. `MissingClaim` takes one `gapId`, so G-02 must split the copy per claim, which fits one ID per distinct
  claim. Otherwise the Architect must allow multi-gap elements. The G-02 planner should note this.
- C6. The firmware placement in the loading branch is claimed (Q2) but not asserted in Vitest.
- C7. The Q1 phrase set is narrow. Copy such as "not tracked yet" or "not recorded" for an absent capability passes
  untagged. Widening the set changes the guard and goes to review.
- C8. The `tasks/README.md` G-01 row still reads "open planning packet". That is for the coordinator's records step.

## Questions Q1-Q4

The shipped defaults (A, A, A, A) are reasonable. No owner decision is needed.
