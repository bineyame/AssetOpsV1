# CH-5a2a phase 2 handoff: PARTIAL (stopped at the context limit)

Branch `task/CH-5a2-chain-endpoints`, worktree `AssetOpsV1-ch5a2`. B = `backend/assetops_backend`.
Main `ff499d54d` (FIX-MAIN-1) is merged in (`bf73f236b`, clean).

## Step 1 (verify phase 1/1b): done
- `1f8f56ecd` then the next commit: the W301 golden manifest is **byte-identical to main**. Instead,
  `tests/test_w301_estate_golden_postgres.py:697` runs `link_parity.checked(body)` before `normalize`, which asserts
  every `href`/`destination`/`links[k]` == `href_for(Ref)` and strips the Ref siblings. A regenerated manifest had
  differed by 168 added Ref lines and 0 removed lines, but the Ref ids are replay-local (mini_grid), so they would
  have needed new marker leaves.
- **D1 is kept** (`%3A`). One builder means one encoding. Estate hrefs already used `urlencode`, and TS
  `URLSearchParams` also encodes `:`, so a raw colon would change the estate hrefs. The Kobo goldens show
  encoding-only diffs. Record this in the packet.
- Test counts (scoped, at about `cbf53f92b` plus the golden fix):
  - unit `test_ch5a2_refs`, `test_out_b3_cold_ev`, `test_w303_portfolio_api`, `test_w301_estate_api`: 103 passed;
  - Postgres `test_w301_estate_golden_postgres`: 6 passed;
  - `test_w301_estate_index_postgres`, `test_w403_opportunity_links_postgres`, `test_w303_portfolio_api`,
    `test_ch4_opportunity_postgres`: 30 passed;
  - `tsc`: clean;
  - vitest, 24 component files (OutcomeBoard, EarlyWarnings, EstatePortfolio, findingIndex, actionIndex, routeFor
    and their fixtures' users): 696 passed.
- `tools/mechanism_dataset.py status`: `usable: false`. Only an older template `bcfd2edf` is tagged, and the checkout
  changed (`finding_index.py` and `estate/*` were edited), so phase 3 must rebuild it.
- Private DB `assetops_ch5a2_test` was created (`ASSETOPS_TEST_DATABASE_URL`
  `postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_ch5a2_test`).
- No leftover processes from the phase-1b helper were alive.

## Phase 2 landed
- **`3cea423fd`**
  - **B5.**
    - `estate/index.py`: `lens_flags = outcome_map.lens_flags(finding_signal_key(mech), domain)`. `RISK_MECHANISMS`
      and the PRICED→COST rule are deleted.
    - Mini `analytics/finding_index.py` rows gain `lens_flags`. **This is an import-traced edit, so the template must
      be rebuilt.**
    - `F/sites/SiteFindingIndex.tsx` Lens cell: when `lens_flags` is absent it renders "Not assessed", otherwise the
      words ("Not in any category" when empty). Vitest is in `s404SiteFindingIndex.test.tsx`.
    - Board FINDING issues gain `primary` (`board.py` `_primary`, `_finding_issue`). CHECKED issues are always
      false.
    - COH-5 uses `_board_findings(primary_only=True)`.
  - **B3.**
    - The `_action_for` exact fallback is deleted.
    - `select_finding_scope(..., cutoffs=None)` fills a Site code → `site_cutoff(...)` map once per Site.
    - `attach_threads(..., cutoffs)` reads `cutoffs[r.site_code]`. The per-row `_cutoff` is gone.
  - **B6.** `progress(..., f_rows)` adds `origin_selected` (thread plus segment, any revision; a None segment
    matches, as in `same_segment`), and COH-8 reads it. The FE type has an optional `origin_selected`.
    `EstatePortfolio.tsx:504` still renders from `origin_revision_selected`; record this in the packet.
  - **`expected-today.json`:** the 12 COH-1, 6 COH-5 and 3 COH-8 entries are deleted. 10 remain (COH-7a ×8,
    COH-2 ×2).
- **`e2d0d277a`**
  - **B4.** `board.thread_line_item` builds a ThreadLine dict, and `thread_line` returns its `text`. Rows carry
    `thread_lines`, and the subline joins the texts exactly as before. In compose, `state_on` gives
    (state, label), and `after.state` is the rolled-up row state code.
  - **COH-14.** `_verified_line` reads `thread_lines` kinds.
  - The CH-5a1 board goldens were regenerated: additive only (`primary` ×9, `thread_lines` ×16). The golden test also
    asserts the subline ends with the joined texts.
  - **Fixture bundles.** FINDING issues gain `primary` (true unless CHECKED), and progress rows gain
    `origin_selected`. Two new self-tests, both non-vacuous.
- Tests at `e2d0d277a`:
  - the 67-file unit set (`grep -lE "site_outcomes|outcomes\.warnings|estate\.|chain\.|chain import|finding_index|chain_coherence" tests/*.py | grep -v postgres`):
    1056 minus the 4 goldens since regenerated, so all pass;
  - `tools/checks/test_chain_coherence.py`: 97 passed.
  - **Not rerun after phase 2:** the Postgres scoped set, and vitest beyond `s404`.

## Resume here (in order)
1. **R7, now OWNER-APPROVED.** Owner's words, verbatim: "fix the summary now as recommended". Build it per §B13 Q7,
   about 0.25 unit.
   - Write ONE function in `B/chain/read.py` covering three cases:
     - an exact one Site-local day pair gives that local date;
     - a UTC-midnight one-day pair gives the picked calendar date, read as each Site's local day;
     - any other window gives the date of `to − 1 µs`, in the frame where `to` is a midnight.
   - Use it from `outcome_api.py` `_mini_day_params` (:63-78), `site_outcomes/read.py:391`, and in place of
     `summary_day` (`chain/read.py:~110`) and `_last_local_day` (`site_outcomes/read.py:~587`). Delete both.
   - `_coh7a_window` (COH-7a, `tools/checks/chain_coherence.py`) must IMPORT it, not copy it.
   - Tests: one per rule case. Show that the 31 Oct summary card equals the 31 Oct Kobo board. Recheck the 8 COH-7a
     `expected-today` entries.
   - Note that the CO-6 finish check should now pass. Verify it with the finish self-check only if a demo DB already
     exists; never prepare.
   - Record the owner decision in the packet.
2. **R8 / L5.** Delete `BoardServices.finding_index`, `parse_finding_index` and `covering_days`, and their wiring:
   `main.py:547,619` and `composition.py:19,52,75,80`.
3. **B8/R6.** Write `tools/checks/check_chain_structure.py`, rules (a) and (b) per sheet §B8. Add a baseline
   `tools/checks/fixtures/chain_structure_baseline.json` that may only shrink, each entry with its owner, and the
   self-test `tools/checks/test_chain_structure.py`. `tools/checks/chain-structure.ps1` is registered in
   `$checkModules` as `configuration-persistence.ps1:974` does. Prove it non-vacuous.
4. **Phase 3 per the dispatch:**
   - `B/chain_api.py` with the 3 endpoints (counts null), wired in `main.py:~625`, plus the L1 goldens and L2 route
     tests;
   - one polish clone (COH-1/5/8 = 0; `--work` from the scratchpad `polish_work`);
   - MD-0: rebuild the template (`--budget 540`, in parts), then derive → collect → `check --threads`;
   - guards A, W, N, V, M, L and D;
   - the packet `.agent/review-packet-CH-5a2.md`, covering D1–D6 plus:
     - D7: the W301 golden parity strip;
     - D8: `origin_selected` not yet rendered;
     - D9: the fixture bundles were edited;
     - the frozen-dict-Refs risk.

## Environment notes
- Run pytest **from `backend/`**. The env file
  `C:\Users\assef\AppData\Local\Temp\claude\C--Users-assef-Bineyame-AssetOpsV1\809ecc09-3853-48b6-b795-60539b50a963\scratchpad\env.sh`
  sets `PY`, `PYTHONPATH`, `ASSETOPS_GUARD_PYTHON` and the DB URL, and cds to the worktree root.
- The machine is shared with lane 2 (MD-0b). Run Postgres test files one or two at a time; the golden file takes about
  3.5 minutes.
- Add `2>/dev/null` to git commands that touch the fixture JSON, because the CRLF warnings flood the output.
