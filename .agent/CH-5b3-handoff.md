# CH-5b3 handoff (partial: build committed, DB step and packet pending)

Branch `task/CH-5b3-why-ui`; build commit `d783b643a` on top of `21503aa6f`.

## Landed (d783b643a)
- `frontend/src/sites/chainClient.ts`: `createChainClient`, `defaultChainClient`, `siteWhyUrl`/`estateWhyUrl`; the memory is keyed by full URL; `If-None-Match`; a 304 reuses the body; any other status gets refused/unavailable and drops the memory; `cache: "no-store"`.
  - **Known deviation:** the sheet names `F/shell/`, but the site-substrate guard (rule 8, `tools/checks/site-substrate.ps1:113-120`) bars `F/sites/OutcomeBoard.tsx` from importing shell. So the client sits in `F/sites/`.
- `frontend/src/blocks/Dialog.tsx`: `ModalDialog` (the focus trap), `ExplainerDialog` (moved out of OutcomeBoard; EarlyWarnings imports it), `isSheetWidth` (600 px or less).
- `frontend/src/blocks/EvidenceTrace.tsx`:
  - `WhyButton` (aria-label "Why? {label}"; uses preventDefault inside the summary).
  - `EvidenceTrace` dialog: placed under the button above 600 px; `.sheet` at 600 px or less; Close at every width and focused first.
  - Copy constants `WHY_LOADING` and `WHY_UNAVAILABLE`.
  - MOCK DEVIATION labels are in comments.
- `frontend/src/blocks/OutcomeRow.tsx`: `OutcomeRowHead` (3 CH-6 slots, MD-CH5b-2; no days line, MD-CH5b-4) and `OutcomeCardValue`. `blocks/blocks.css` holds the mock CSS on app tokens.
- Board: every row except NOT_MEASURED gets Why; prop `why?: ChainClient`.
- Portfolio `CategoryCards`: a div card with a stretched `Link.value-label.oc-cardlink[data-portfolio-card-link]`, Why on all 4 cards, prop `why?`.
- Tests:
  - New: `blocks/__tests__/evidenceTrace.test.tsx` (15) and `sites/__tests__/chainClient.test.ts` (6).
  - Selector-only edits in `estatePortfolio.test.tsx` and `outcomeBoard.test.tsx`.
  - `test/settled.ts` now has "the reasons".

## Checks done (on d783b643a)
- `vitest related` over the 7 changed sources, with `--exclude **/findingLinkWordsParity.test.ts`: 110 files, 2880 passed, exit 0.
  - The exclude works around a pre-existing failure: `related` cannot parse the `?raw` `.py` import.
- `tsc --noEmit`: exit 0.
- Ratchet: totals api 12, href 24, lit 70, cmp 51, code 3. These equal the baseline, so nothing rose.
- Guards V (14/0), N, A (architecture), dependency registry, delivery, mock-gap, missing-claim scan and fixtures, evidence width, ratchet tests, screen ledger, chain coherence (103) and event register (12): all exit 0.
- Still running in the background: the estate guard self-tests, the graph check, the perf fixture and the agent workflow. Rerun any of them if their result was lost.

## Next
1. Wait until no `mechanism_dataset.py` / `chain_clone.py` process is running (lane 2 was building).
2. Polish clone, using PYTHONPATH (absolute, the worktree's `backend;contracts;tools;simulator;gateway;host;field`) and the plan2 venv python:
   - `tools/chain_clone.py create ch5b3 --migrate`, then `settle ch5b3`;
   - `tools/checks/perf_budget.py --database-url postgresql://assetops:assetops-local-dev@127.0.0.1:55432/assetops_chainclone_ch5b3_test --store on --report`;
   - then `drop ch5b3`.
3. Write `.agent/review-packet-CH-5b3.md`:
   - criteria;
   - the mock→new table (aria-label, loading and failure lines, Close at all widths/first focus, no days line, slots show the headline, the client location);
   - layout evidence: not run (captures at E5 per coordinator Q7).
4. Run `git add -f`, then commit.
