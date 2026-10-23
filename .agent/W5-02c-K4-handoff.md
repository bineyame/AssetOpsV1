# W5-02c K4a + K4b + K5 handoff (cold Action detail and W5-02 closeout)

Branch `task/W5-02c-K4-cold-action`, from main `acf3f078` (K2, K3 and the K4 rulings), merged at `2b287613`. It is built
against the 13 pre-flight rulings in `.agent/W5-02c-K4-preflight-rulings.md`. **Not yet rebased on W5-03b E4/E6**: per
ruling 13, review happens only after that merge and a rerun of the batch.

## Commits

| Commit | Unit | What |
|---|---|---|
| `199e788e` | K4a | New `DomainActionVerification.tsx` holds the loaded `Declared outcome criteria` and `Related activity` panels (rulings 4, 5, 8).<br>The shell in `SiteAnalyticsFrames.tsx` (domain Action region only) renders those two panels when loaded, and one untitled state panel for loading, 404 and refusals. It adds an owner span and the `shortName()\|\|display_name` fallback (ruling 9).<br>`domainActionClient.ts` now requires one known initial result per criterion, in order.<br>`NavRail` takes `activeLabel`. `OperatorShellLayout` declares the ruled `railActiveLabel` line and passes it (rulings 1, 2).<br>The guard pins the helper and the call form, with 2 negative rail fixtures.<br>`SCREEN_LEADING["cold-action"]` is added (ruling 3).<br>Tests: new `domainActionVerification.test.tsx` (22); rail inventory (+7); R69 inverted in `operatorRouteFrames`; `coldWorkActions`, `siteActionVerification` and `w1f4ActionStructure` updated from the placeholder. |
| `ace6f269` | K4b | Producer: `detail_reads` (positive CURRENT, positive `known_at`=K1, worstcase Action 1), required by `attest` and served-checked.<br>Capture: `W502B_EVIDENCE=action` mode and the final `ACTION_CAPS`.<br>CSS: H1 and owner use `overflow-wrap:anywhere`; Related controls row; direct-code containment, including the strip's `Finding version` (ruling 12).<br>Ledger: `cold-action` row and its 2 panel contracts (spec literals). The pilot registry is untouched. |
| `7c2fb351` | K4b | The case-capture containment relaxation is narrowed to direct-code bodies (ruling 12). |
| `5db28f19` | K5 | Postgres lineage test `test_k5_cold_action_lineage_through_product_get`. `coldWorkCases`: `[data-cold-cases]` is absent on MINIGRID and present on both cold tabs. |
| `b9db3711` | K5 | Lineage test reads the WR title from its revision row (first focused run: KeyError on `wr["revision"]["title"]`). |
| `d809186f` | K4b | Capture-tool fixes (warm-up; closed `<details>` skipped). Evidence and README. Question Q1. Stale K2 attest Low removed after the negative proof. |

## Checks

All runs were on the code above, before the E4/E6 rebase.

- **Types and build:** `npx tsc --noEmit` is clean and `npm run build` is green.
- **Targeted vitest (`src/sites src/shell src/test src/ui`):** 107 files, 2672 passed. This ran at the K4a tree and was
  rerun for the changed files.
- **Full vitest (`--minWorkers=1 --maxWorkers=2`):** see "Final counts" below.
- **`tools/check-all.ps1`:** 11/11 at the K5 tree.
  - The navigation guard and rail fixtures pass on the real tree.
  - Non-vacuity, committed then reverted with `git checkout`: I removed `SCREEN_LEADING["cold-action"]` and dropped
    `activeLabel={railActiveLabel(pathname)}`. That failed 8 tests (4 currentness tests and the 3 detail-path rail
    tests, plus 1 more). The guard fixtures prove the unconditional and widened forms fail.
- **Producer:** `prepare` (187 s) blocked no mode. `serve` started 7 APIs, all healthy, and `attest` returned ATTEST OK.
  The negative attest (positive `detail_reads` and worstcase `reads` removed) returned ATTEST FAILED with both
  reasons.
- **Captures:** `.agent/W5-02c-K4-evidence/` gives 292 PASS, 0 FAIL over 24 PNGs. All closed states are under the final
  caps (README table). The K3 case recheck gives 930/4, with every failure being Q1.
- **Focused w502 Postgres:** see "Final counts".
- **Full backend suite:** not run. P-K5-2 requires one same-revision real-Postgres full suite for W5-02c, because K4a
  edits `tools/checks/*`. It belongs on the final, post-rebase revision.

## Open question (blocks review of K4b's case CSS only)

**Q1** in `.agent/W5-02c-K4-questions.md`: ruling 12 (only direct-code disclosure bodies scroll; others wrap)
contradicts merged K3 ruling 20 (one-line UUIDs in `UTC and IDs`). The tree implements ruling 12 as written, and the 4
ruling-20 capture claims fail. Options a, b and c are listed there; no choice was made.

## Judgment calls (each follows a ruling's letter; please confirm)

1. **Vocabulary scan.** The criteria row text `Accepted command followed by successful running status` (stored
   `domain_action.py` CRITERIA, mock-exact) trips `running`. The test sets aside exactly that text node, following the
   K2 ruling-14 precedent. There is no product exemption attribute.
2. **Strict detail client.** A detail whose `results` are not one per criterion, in criterion order, with values in
   {NOT_TESTED, NOT_ESTABLISHED, PENDING}, is refused as the ledger's malformed-200 "unexpected shape". It is never
   rendered with an invented label.
3. **Strip `Finding version` when open.** The disclosure item takes the strip's full row (`flex-basis:100%`). With the
   ruled `contain:inline-size`, the body would otherwise be only as wide as its summary. This is an expanded state
   only; the closed layout is unchanged.
4. **K1 cutoff read.** At `known_at` = K1 the intent does not exist yet (K3 > K1), so this state also shows
   `No outcome criteria have been declared for this Action.` beside the not-linked sentence. This is the selected
   data, not a fixture choice. Its status is HISTORICAL.
5. **Related activity with a linked OPEN or IN_PROGRESS WR.** The sentence is the not-linked one (no completed
   inspection), and Inspect stays live to that WR's Overview, because a case ID is selected (ruling 8).
6. **`COLD_ACTION_PREPARING`** in `coldWorkPresentation.ts` is now unused. It is left in place because that file is
   not in K4's lists.
7. **K3 Lows** (backlog "W5-02b K3 Lows"): items 1-3 are addressed by K4b CSS/capture, K5 tests and K4b attest/K5
   lineage. Only the K2 attest line was removed, which is the one ruling 12 names. The coordinator may close the
   K3 lines.
8. **Registry.** `A-cold-work-projections` is left open. Its predecessors `A-maintenance-index` (open) and
   `A-work-cases` (open, task W4-01) remain unresolved (ruling 11).

## Shared plumbing touched

- `frontend/src/ui/NavRail.tsx`: optional `activeLabel`. When it is absent or null, the `NavLink` behaviour is
  unchanged.
- `frontend/src/shell/OperatorShellLayout.tsx`: the helper line and the call form.
- `tools/checks/navigation-truthfulness.ps1` and `navigation-rail-fixtures.ps1`: Action-specific additions only.
- `frontend/src/test/panelStructure.ts`: one `SCREEN_LEADING` entry.
- `SiteAnalyticsFrames.tsx`: the domain Action region only.
- Not touched: `App.tsx`, `missing-claim-scan.mjs`, the EV files, the backend product code and the migrations. The
  only backend change is a test.

## Rebase plan (after E4/E6 merge)

1. Merge main, keeping E6's Scenarios rail entry and its fixtures alongside the K4a `activeLabel` guard and fixtures.
   The nine-link and focus-order assertions in `operatorRailInventory.test.tsx` must follow E6's live count.
2. Keep E4's missing-claim scan.
3. Rerun tsc, full vitest, build, check-all, the producer and the captures.
4. Run the P-K5-2 full backend suite.

## Final counts
All counts are at `b9db3711`.

- **Focused w502 Postgres:** `backend/tests/test_w502_*.py`, `-n 4`, on the private base `assetops_w502ck4_test`, with
  PYTHONPATH set to the worktree. JUnit: tests=35, failures=0, errors=0, skipped=0. Wall time 210 s.
  - The first attempt errored because the base database did not exist. I created it.
  - The second attempt failed the new K5 test with the KeyError noted in the `b9db3711` row. It is fixed and rerun.
- **Full vitest (`--minWorkers=1 --maxWorkers=2`):** 121 files, 2865 passed, 409 s.
- **Cleanup:** stopped only my own PIDs.
  - 7 Vite processes, stopped with `taskkill /PID /T`.
  - 7 APIs and 5 `w502b_*_k4_test` databases, removed with the tool's `drop`.
  - The keep-awake process, stopped by PID.
  - `assetops_w502ck4_test`, dropped.
  - Ports 5471-5477, 8971-8977 and CDP 9481 are free.
