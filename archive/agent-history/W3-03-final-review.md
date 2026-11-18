# W3-03 final whole-slice review (Portfolio composition)

Reviewer: independent Claude reviewer (author of no W3-03 unit). Branch `task/W3-03-portfolio-composition`, head
`85efbea7`; merge base with main `6cdb8c4b`; main `0352d9b7` is ahead only by `.agent`/`.ai` planning files and
`git merge-tree` against it is clean. Read-only on `AssetOpsV1-review2`; checks ran in a private detached worktree
(removed) on a private `w303fr_test` DB (created and dropped).

## Verdict: REVISE

Two Medium findings, both small: one spec-literal UI gap and one launch-documentation gap that blocks the owner
walkthrough. Otherwise the page, registry, Lane A shared edits and captures match the v69 `portfolio` mock and the spec
through r3b.

## Findings

### Medium

**M1. The business-context footer has no source/window disclosure.** `frontend/src/estate/EstatePortfolio.tsx`,
`ContextFooter`. Closure 1 (Q4-Q8) requires that "the source and exact window appear in a `Disclosure` attached to that
sentence". The wire carries `footer.source_provenance`, `window_start` and `window_end` for this purpose, and
`estateClient.ts` types them, but the page never renders them. On the positive capture the page shows `KES 8.33 gross
tariff scenario` with no way to see its window or source. No later ruling (r1b2 R12, r2, r3, r3b) removes this. It is
an acceptance gap, not a preference: it is the only money amount on the page without a provenance path.
**Fix:** attach a `Disclosure` (for example `Energy basis ↗`) to the sentence. It should show
`moneyWindowText(window_start, window_end)` and the six-key source block, or `No selected source basis`. Add an
assertion to `rendersEvFooterAndMissingEnergyBasis`. Recapture is needed only if the footer block exceeds its Q24 caps.

**M2. `/portfolio` returns 503 on any server started without a cursor key, and there are no instructions for setting
one.** `backend/assetops_backend/estate_portfolio_api.py` calls `portfolio_cursor_key()` on every request. Under r1b
Q-1b-1 it deliberately has no default: "a local server must be given a separately generated key". Yet
`ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX` appears only in `scope.py`, `main.py`, the tests and the capture harness. It
is not mentioned in `backend/README-db.md`, `docker-compose.yml`, any run script or the packet. A dev server started the
documented way therefore shows the page as `Estate records could not be read.` on the live rail item. The next gate is
the owner walkthrough, so the slice would look broken there. The packet's residual-risk section does not name this.
**Fix (docs only):** add a key-generation step, for example
`python -c "import secrets;print(secrets.token_hex(32))"`, plus the env var, to the backend run instructions. Name it in
the packet as a walkthrough precondition. The code does not change; the ruling stands.

### Low

**L1. An empty scope is labelled "coverage incomplete".** `EstatePortfolio.tsx` `PriorityPanel`:
`incomplete = finding_state !== "COMPLETE"`, so `EMPTY` counts as incomplete. The empty capture reads
`0 SELECTED FINDINGS · COVERAGE INCOMPLETE` beside `No accessible Sites`. The spec appends the suffix only "when
coverage is incomplete", and an empty scope is not incomplete. **Fix:** exclude `EMPTY`, or test for
`PARTIAL|UNKNOWN`.

**L2. The short Finding IDs do not tell rows apart in the captures.** All three positive rows read
`Finding 00000002 · Mechanism not recorded` (KOBO, and both COLD rows). This follows the spec's "first 8 UUID chars",
but deterministic fixture or replay IDs share that prefix, so the label identifies nothing. Route this to the
Architect or the W1 plain-copy pass; it does not block.

**L3. The drawers show system vocabulary.** The scope drawer prints raw `coverage.state` (`CURRENT`,
`PENDING_RECOMPUTE`), `reason_codes`, line keys and group keys. The progress drawer prints raw UUIDs and
`VERIFIED`. The scope drawer also omits the `Selected Sites` caption and the nested provenance and group disclosures
from closure 1. Most of this is spec-literal "exact IDs in disclosure", so it belongs in the batched client-facing copy
pass rather than here.

**L4. The matrix footnote points to linked cells that do not exist.** Every matrix cell shows `Site detail
unavailable`: 20 repetitions in positive, 25 in partial. This is because r1b2 R7 fixes all cell destinations to null.
The literal footnote still says `Select a linked cell for context.`. This is consistent with the rulings but
misleading; refer it to the Architect for the copy pass.

**L5. Mock icons are missing.** The v69 value-card label icon and arrow, and the pulse icons, are not reproduced.
Panel set, order, titles and prominence otherwise match. This is a presentation-pass item, not a layout mismatch.

## What was verified

- **Mock parity (run 2 and run 3).** I viewed positive 1440, positive 390, empty 390 and refusal-409 1440.
  - Leading rows (context, five cards, pulse), the main row (priority panel, then the aside with the Objectives panel
    and Evidence note), the bottom row (opportunity, progress) and the footer all follow `portfolioScreen()` order.
  - The four titles are verbatim. The eyebrows `GROW USEFUL DEMAND` and `CLOSE THE LOOP`, the `Scenario` chip and the
    `Inspect basis ↗` and `Assessment scope & periods ↗` triggers are kept.
  - The five card labels are in mock order. The lens chips are `All findings/Cost/Risks/Opportunities` per the r1b2
    literal.
  - No mock value leaks: no `Needs attention`, `simulated`, 18–20 kW, $2.50, ACT- or F- IDs.
  - The 390 layout is a 2-column card grid with the fifth card in column 1. The table and matrix scroll internally, and
    the document width stays fixed.
- **Five-status UI.** `contextWords` maps EMPTY_SCOPE, HISTORICAL, PENDING, UNKNOWN and CURRENT to the closure-1
  Q19 badge, tone and sentence. All five real-API captures show the expected status, and the frontend test
  `rendersEmptyPendingHistoricalAndSourceConflict` covers them.
- **MissingClaim / mock_gaps.**
  - `G-portfolio-opportunity` matches the r2 literal byte-for-byte in the registry.
  - The `gapCatalogue.ts` mirror is exact.
  - Both inert spans are wrapped exactly as r2 prescribes, with no href or button.
  - The missing-claim scan passes.
- **Registry and ledger (r3).**
  - The two nodes, the four `gap` panel rows and the ledger `registry_dependencies` match the r3 literals in order and
    content.
  - No node is closed.
- **Lane A shared files.**
  - `estateClient.ts` is additive only: Portfolio types, `portfolio()`, and no widened root unions.
  - `App.tsx` route, `EstateRootFrames.tsx` frame, `PORTFOLIO_ROOT_PATH`, and a rail item changed only for Portfolio.
  - The navigation guard and fixture move the dead-link subject to Assets, per S17.
  - The `panelStructure`/`settled` additions are scoped.
  - The `main.py` mount reuses the existing tenant and access seams.
  - The backend shared estate files are unchanged since the reviewed 1b/r1b3 commits apart from the
    `main.py` mount and the r3b literal.
- **Net diff hygiene.**
  - No debug leftovers in product code: the only `console.log` is in the committed capture script.
  - No build output and no migration.
  - No edits to W3-01/02 pages, and the W4-01/02 files are untouched.
  - The rail and route tests across `src/shell`, `src/ui` and `src/estate` pass, which covers the W3-01/02 roots.
- **Captures.**
  - All eight `app-portfolio-<state>.json` files have `failed=[]` and `over=[]`, with the expected status or refusal
    code.
  - In refusal-409 the 409 follows a CURRENT page one.
  - Empty 390 has card0 = card1 = 194 px, within the 207 px cap (r3b).
- **Packet.**
  - It is complete against the r2 "Registry rows and closeout packet" list.
  - Every pending ruling (P-0b-1 … P-3-2, Q-1a-1, Q-1b-1..3) is marked RESOLVED, and the r1a/r1b2/r2 readings are
    ruled.
  - The full backend suite is honestly recorded as not run, pending the coordinator.

## Checks I ran (head `85efbea7`, private worktree)

| Check | Result |
| --- | --- |
| `npx.cmd tsc --noEmit` | exit 0 |
| `vitest run estatePortfolio.test.tsx estatePortfolioRoutes.test.tsx` | 2 files, 16/16 passed (it ran here despite the documented sandbox issue) |
| `vitest run src/shell src/ui src/estate` | 66 files, 1337/1337 passed |
| `tools/check-all.ps1` | 11/11 PASS. A first run failed 3 guards only because my worktree had no `.venv`; the rerun with the venv linked passed all 11. |
| pytest W3-03 pure/API files (`portfolio_api`, `estate_cursor`, `reduction`, `workflow_labels`, plus pure parts) | 90 passed |
| pytest persisted W3-03 Postgres files | **not verified**: 4 failed and 7 errored in fixture setup (`test_w203_cold_replay_postgres.py:80`, empty worker outcomes). The pre-existing base `test_w203_cold_replay_postgres.py` also fails 14/14 in the same environment, so the cause is my worktree's linked venv and editable packages, not the slice. |
| `npm.cmd run build`, full frontend suite, full backend suite | not run. I rely on the packet's frontend figures (2450/2450 ×2, build ok); the full backend suite is pending with the coordinator. |

## Residual risk not named in the packet

- The M2 key precondition for any live demo or walkthrough.
- The persisted Postgres proofs (B3 fixture, Q9 variants, the November Action chain) were not independently rerun by
  this reviewer. The same-revision full suite is the remaining evidence gate before merge.
- `s404SiteFindingIndex` "changing the dates writes a new window" failed once under full-suite load (packet), and it
  is unrelated to this diff. It should be watched in the coordinator's run.
