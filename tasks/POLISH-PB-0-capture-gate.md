# POLISH-PB-0 Capture gate and label guard

Status: in_progress
USER_REVIEW_REQUIRED: false
Lane: B (frontend and tools). Units: 3. Branch `task/POLISH-PB-0-capture-gate`.

The spec is `.agent/build-sheet-POLISH.md`: §2 (P-04 ruling), §5 Lane B "PB-0", and §7 (PB-0/PB-1 own register ids R650-R654). This file
states scope only; the sheet is the contract.

## Scope

- `tools/demo-combined-evidence.mjs`:
  - strict gate `DEMOB_STRICT=1` (exit 1 on any counted vocabulary hit; exclusions `[data-technical-details]`,
    `[data-time-zone-note]`, `[data-vocabulary-exempt]`; the `-open` capture counts only `MOCK DEVIATION`);
  - widened VOCAB plus the T028 and w1 terms from `frontend/src/test/productVocabulary.json`;
  - `DEMOB_REVIEW_LABELS=1` opens `/?review=labels` once before capturing;
  - settle also waits for no `[data-repeat-check="loading"]` and no `[aria-busy="true"]` in `<main>`.
- OUT-D L1: whole-line loading predicate in `tools/evidence-checks.mjs`, so "Loading and door records" no longer blocks settling.
- Guard 12, "Mock deviation labels and client vocabulary": `tools/checks/mock-deviation-labels.mjs` plus
  `tools/checks/test_mock_deviation_labels.mjs` and four fixtures, registered in `tools/check-all.ps1`.
- The P-04 mechanism, if the coordinator rules option (a) on pre-flight Q1. See the packet.

## Not in scope

The label sweep, copy changes, time notes, banner and every PB-1+ item.

## Checks

- `node --test tools/checks/test_mock_deviation_labels.mjs tools/checks/test_evidence_checks.mjs`
- `node --check tools/demo-combined-evidence.mjs`
- Scoped vitest; `tsc --noEmit`.
- `tools/check-all.ps1`: 12 guards pass.
- A strict capture against the kept build is expected to fail. Its hit count is recorded as the baseline.
