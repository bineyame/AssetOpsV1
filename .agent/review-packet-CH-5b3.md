# Review packet: CH-5b3 (Why? button, trace dialog, chain client)

Branch `task/CH-5b3-why-ui`. Build `d783b643a` on `21503aa6f`; handoff `fbac8b3bb`. Builder 2 finished the clone run and this packet.

## Outcome
Every board row except NOT_MEASURED, and all 4 Portfolio category cards, carry a "Why?" button. It opens a dialog fed by the chain client (`/chain/why`, site and estate URLs, ETag memory). Loading, failure, and a 422 `CATEGORY_UNKNOWN` show fixed copy. The row head has 3 CH-6 slots that stay empty until CH-6. The slice is frontend only: no backend or contract change.

## Files materially changed
- `frontend/src/sites/chainClient.ts` (new) and `sites/__tests__/chainClient.test.ts` (6 tests)
- `frontend/src/blocks/Dialog.tsx` (`ModalDialog` focus trap, `ExplainerDialog` moved out of OutcomeBoard, `isSheetWidth` at 600 px or less)
- `frontend/src/blocks/EvidenceTrace.tsx` (`WhyButton`, `EvidenceTrace`, `WHY_LOADING`, `WHY_UNAVAILABLE`) and `blocks/__tests__/evidenceTrace.test.tsx` (15 tests)
- `frontend/src/blocks/OutcomeRow.tsx` (`OutcomeRowHead`, `OutcomeCardValue`) and `blocks/blocks.css`
- Board and Portfolio `CategoryCards` (stretched `Link.oc-cardlink`, prop `why?`)
- Selector-only edits in `estatePortfolio.test.tsx` and `outcomeBoard.test.tsx`; `test/settled.ts` gains "the reasons"

## Mock to new (mock `frontend/mockups/v70/index.html:411-438`)
| Mock | New | Label |
|---|---|---|
| `aria-label` "Why? {site} · {category}" | "Why? {row label}" (the server title is not loaded until open) | MOCK DEVIATION CH5b3-R Q6 |
| Static text, no loading or failure line | Loading reads `WHY_LOADING`. Any failure, 422 `CATEGORY_UNKNOWN` included, reads `WHY_UNAVAILABLE` | MOCK DEVIATION CH5b3-R Q6 |
| Close hidden above 600 px (popover, outside-click close) | Modal dialog. Close shows at every width and takes first focus. Under the button above 600 px; `.sheet` at 600 px or less | MOCK DEVIATION MD-CH5b-5 (Q5) |
| Slots show earnings, KPI, potential | 3 slots exist but no caller fills them. The row shows the CH-5a2 headline until CH-6 | MOCK DEVIATION MD-CH5b-2 |
| `ob-days` / `oc-pfdays` line under the value | Not rendered. The days line shows only as "Days used" in the dialog (BL-13) | MOCK DEVIATION MD-CH5b-4 (Q3) |
| `chainClient` where the sheet says `F/shell/` | In `frontend/src/sites/chainClient.ts` | KNOWN DEVIATION (below) |

Other mock-faithful pieces: `.why-btn` (min-height 24 px), `.ob-head > .ob-val + .why-btn`, Portfolio card with Why on all 4 cards. Colours use app tokens, so dark mode follows.

## Known deviation: client location (rule 8)
The sheet places the client in `F/shell/`. The site-substrate guard (`tools/checks/site-substrate.ps1:113-120`, rule 8) bars `F/sites/OutcomeBoard.tsx` from importing shell. The client sits in `F/sites/` so the board can import it. `blocks/` and Portfolio import it from there. The guard was not loosened.

## Checks
- `vitest related` over the 7 changed sources, excluding `**/findingLinkWordsParity.test.ts`: 110 files, 2880 passed, exit 0. The exclude works around a pre-existing failure: `related` cannot parse the `?raw` `.py` import.
- New tests: 15 + 6 = 21.
- `tsc --noEmit`: exit 0.
- Ratchet totals api 12, href 24, lit 70, cmp 51, code 3. These equal the baseline.
- Guards V (14/0), N, A, dependency registry, delivery, mock-gap, missing-claim scan and fixtures, evidence width, ratchet tests, screen ledger, chain coherence (103) and event register (12): all exit 0.
- Not re-confirmed by builder 2 (the handoff said they were still running): estate guard self-tests, graph check, perf fixture, agent workflow. Rerun them.
- No full frontend suite and no full backend suite were run (demo sprint: none until E2).

## Perf budget (clone `assetops_chainclone_ch5b3_test`, store on, 3 runs, `--report`)
Made from `assetops_polish_full_test`: create, migrate, settle, perf, drop. Dropped and its var files deleted afterwards. Keys were fresh `secrets.token_hex(32)` in `var/ch5b3_perf/keys.json`; output is in `var/ch5b3_perf/perf.txt`.
Verdict: `FAIL (1 breach, 3 not measured)`, report mode, exit 0.
- BREACH `cold_chain_failure_night` cold_ms 1038.7 vs limit 1000. It is a cold-process figure on a backend `/chain` route. This slice changes no backend code, so the reading looks like cold-start noise on a busy machine, but I did not isolate it. The Reviewer should decide whether to rerun.
- All other measured routes PASS. Examples: portfolio_week cold 679.5 ms, warm p95 38.3 ms, 48714 B; kobo_board_31oct cold 697.4 ms.
- NOT MEASURED, as expected: `snapshot_rebuild_ms_per_measure_day` and `tick_chain_stage_fraction` (owner DD-1b2/E4), `why_trace_ms` (owner CH-5b2).
- A first attempt without `--work` failed on usage. That is a CLI error, not a result. The clone was recreated for the real run.

## Layout evidence
Not run. Captures are taken at E5 (coordinator Q7). Layout claims (placement under the button above 600 px, sheet at 600 px or less, Close at every width) are covered only by jsdom tests and are unverified for rendered layout.

## Residual risk
- The `cold_chain_failure_night` breach above.
- The dialog placement at the 600 px boundary is unmeasured until E5.
- Slots are empty until CH-6.

## User review
Not required by this packet; the E5 capture pass covers visuals.

## Review closure (coordinator, after review REVISE H1/L1)
- H1 fixed: `.conf-pop.why-pop.sheet .why-close { display:inline-flex; align-items:center; min-height:32px }` per mock `v70/index.html:239`. `.why-pop .conf-head` now matches the mock (`flex-wrap: wrap`, inherits 11 px).
- L1 fixed: `OUTCOME_KEY` doc comment restored.
- tsc clean; vitest (why/Dialog/estatePortfolio/outcomeBoard files) 82 passed.
- Perf: `cold_chain_failure_night` 1038.7 ms is a backend residual (route read 1846–2065 ms cold at CH-5b1; this slice has no backend change) — recorded for E4 perf check.
