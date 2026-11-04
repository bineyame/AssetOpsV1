# CH-5a2a phase 1 handoff: PARTIAL (stopped at the context limit)

Branch `task/CH-5a2-chain-endpoints`. B = `backend/assetops_backend`, F = `frontend/src`.

## Landed
- `4e7547e63`: the Ref union, `href_for`, the TS `Ref`/`routeFor`/`linkFor`, and the shared fixture.
  - `B/chain/refs.py`: kinds, `SITE_VIEWS`/`ESTATE_VIEWS`/`FINDING_VIEWS`/`ACTION_VIEWS`, `href_for`, constructors (`finding_ref`, `action_ref`, `site_ref`, `estate_ref`, `evidence_ref`, `case_ref`, `opportunity_ref`, `thread_ref`, `window`), `query_window`, `links_of`, `split_links`. Imports stdlib only.
  - The TS side is at the end of `F/shell/operatorSiteRoutes.ts`: `Ref`, `REF_SITE_VIEWS`, `REF_ESTATE_VIEWS`, `routeFor`, `linkFor`, and the CASE builder `workRequestHref`.
  - `F/shell/__fixtures__/route-refs.json` has 56 rows: every kind, every enumerated view, and one encoded Site code.
- `1c3e3a075` (partial): server R4(a). Every legacy link is built by `href_for`.
  - **Board** (`B/site_outcomes/board.py` `_link`): every item with `href` gains a sibling `link_ref`. This covers issues, contributors, options, in_hand, earlier, evidence_link and must_not_harm.
    - The fact dataclasses hold Refs: `href` becomes `link_ref`, and `verification_href` becomes `verification_ref`.
    - The `EVIDENCE_LINK` values are Ref factories.
  - **Warnings** (`B/outcomes/warnings.py`): `Warning`/`Visit`/`PlanCue` `.link_ref`. The wire gains `link_ref`, and each `evidence_refs[]` item gains `link_ref` (`_eref`). `PLAN_LINK` is the Ref form of `PLAN_HREF`.
  - **mini/cold/ev/visits** build Refs. `mini.renewable_ref` is new; `renewable_href` is kept as a wrapper.
    - Cold/EV Findings: `cold.finding_window_link` reads the store row link's query (its own proven window and cutoff) and builds the Ref through `evidence_money.finding_window_ref` (R5). The store is untouched, and no `/api` link remains.
    - A domain-intent Action is `ACTION view=verification` and a W1 row is bare, by `W1_DOMAIN`, which matches `domain_action_index.py:457,488`.
  - **Estate** (`B/estate/index.py` `_links`, `_finding_link_refs`; `_finding_links` is kept as an href wrapper): Findings and Actions rows gain `link_refs` keyed like `links`.
    - `evidence_money.window_link_refs`/`site_home_ref`/`finding_window_ref` are new, and the old href functions wrap them.
    - `financials.money_link_refs` is new (`_money_links` wraps it).
    - `_row`/`_line` take Refs and emit `**split_links`, giving both `links` and `link_refs`.
  - **Portfolio** (`B/estate/portfolio.py`):
    - row `links`/`link_refs`;
    - `_destination` gives `destination` plus `link_ref` on the cards, the opportunity block, the cells, `evidence_prompt` and the footer;
    - `objective_destination_refs` is new (`objective_destinations` wraps it).
  - **CH-4** (`B/chain/opportunities.py`): `link_refs` sits beside `links`. `ref`/`thread_ref` are unchanged.
  - **Tests:**
    - `backend/tests/link_parity.py` `checked(body)` asserts `href == href_for(link_ref)`, `destination == href_for(link_ref)` and `links[k] == href_for(link_refs[k])`, then strips the Refs. The b1/b2/b3/d4 board helpers and the w303 prompt use it, so parity runs on every unit-built board.
    - `test_ch5a2_refs.py`: fixture rows, coverage of every kind and view, no `/api`, unknown view or kind raises, OL-1, and stdlib-only imports.

## link_ref shape (apply consistently)
- An item with `href` gains a sibling `link_ref` (Ref or null).
- An object with `destination` gains a sibling `link_ref`.
- A `links` dict gains a sibling `link_refs` with the same keys. `*_label` keys are text and stay only in `links`.
- The existing `ref` objects are byte-identical.

## Resume here (in order)
1. **Eight unit test files fail on fixtures only** (25 tests). Run the command from the "Tests" section.
   - `test_out_c_rules.py` ×14, `test_polish_pa2a_server_copy.py`, `test_polish_pa2b_plan_due_assets.py`: `Visit(href=…)`/`PlanCue(href=…)` and `w.href`. Change to `link_ref=R.case_ref(...)` and similar, and read `R.href_for(w.link_ref)`. `test_out_c_rules.py:237` also needs `link_ref` added to the wire key list.
   - `test_out_c4_mini_ev.py:143`: `w.href`.
   - `test_out_c1_never_money.py`, `test_ch2_threads.py`, `test_walk1_productive_sales.py`: a string passed where a Ref is expected (`refs.py:98` TypeError), `portfolio.py:270 KeyError 'link_refs'` (a hand-built index row needs `**index._links(index._finding_link_refs(...))`), and dict equality with the new `link_ref` key (wrap with `link_parity.checked`).
   - `test_out_c3_cold_cost.py:35`: the domain Action option now ends `/verification`; update the expectation, as in `test_out_b3_cold_ev.py`.
2. **Client, item 5: not started.**
   - `OutcomeBoard.tsx` `To` (:93-95) takes `Ref | null` and renders `linkFor(item.link_ref)`.
   - Also convert `EstatePortfolio.tsx`, `findingIndex.tsx` (the `findingLinkLive` gate :297 must read `link_refs.finding`: a cold/EV ref is live only with a `window`), `actionIndex.tsx` :107/:118 and `EarlyWarnings.tsx` :25/:65.
   - Add optional `link_ref?: Ref | null` / `link_refs?` to the wire types: `F/sites/outcomeBoardClient.ts`; `F/estate/estateClient.ts` :101, :140, :182, :292; the warnings type.
   - Write the vitest "a body without `link_ref` renders no link", then run `tsc` and the component test file list from the dispatch.
   - Leave `PortfolioOutcomes`, `EstateEvidence`, `EstateFinancials`, `SiteWorkActions`, `siteWorkCases`, `GlobalIncidents` and `workRequestShared` for CH-5b/CH-6b.
3. Run the scoped Postgres tests: `test_out_b3_cold_ev` is unit; `test_w301_estate_golden_postgres`, `test_w301_estate_index*_postgres`, `test_ch4_opportunity_postgres` and `test_w403_opportunity_links_postgres` assert links.
   - **Do not edit the w301 goldens.** Record whether they differ only by added `link_refs`/`link_ref` keys. Estate hrefs should be text-identical (they already used `urlencode`).
4. Run `status` on the MD-0 template (`finding_index.py` was **not** edited; `estate/*` and `site_outcomes/*` were).

## Tests (last run, at `1c3e3a075`)
- `test_ch5a2_refs.py`: 64 + 1 passed.
- vitest `src/shell/__tests__/routeRefs.test.ts`: 59 passed.
- Every non-Postgres backend test importing a touched module: 715 passed, 25 failed (the eight files above), 1 skipped.
  - The file list was built with `grep -lE "site_outcomes|outcomes\.warnings|estate\.(evidence_money|financials|index|portfolio)|chain\.opportunities|chain import opportunities" tests/*.py | grep -v postgres`.
- `tsc`, the component vitests and Postgres: not run.

## Deviations (for the packet)
- **D1. Query encoding.** One builder means one encoding: URLSearchParams/`urlencode`, with `:` written `%3A`.
  - The mini renewable link (`renewable_href`) and the CH-4 `links.evidence` change from raw `:` to `%3A`. The instants are the same.
  - Estate hrefs were already `%3A` and are unchanged.
  - Tests updated: `test_ch4_opportunities.py`, `test_walk1_5_solar_window.py`. The Kobo CH-5a1 goldens show the same 4 encoding-only diffs.
  - `tools/checks/fixtures/chain_coherence/bundles/clean/board.day_kobo_trial-before_2026-10-31.json` holds the raw-colon form. Phase 3 owns coherence fixtures.
- **D2. Ref fields added beyond B1** to cover emitted links:
  - `FINDING.view` (the `/recommendation` options);
  - `ACTION.recorded_at` (Selector);
  - `SITE.window` (windowed `/financials`, `/ev/financials`, `/ev/evidence`);
  - `EVIDENCE.window` may carry only `from`/`to` (renewable).
  - `ESTATE` takes no `query`: no estate builder takes one.
  - Performance capabilities are `EVIDENCE{capability}`.
- **D3. The `test_out_b1_board` purity guard** now admits exactly `from assetops_backend.chain import refs`. `test_ch5a2_refs.py::test_refs_module_imports_only_stdlib` pins refs.py to stdlib.
- **D4. Behaviour changes in the CH-5a1 cold/EV goldens:**
  - Fake-fixture Finding links without a window now render no link: they are unproven, as on the estate.
  - Domain-intent Actions now point at `/verification`, as the real index emits. Before, the fixture's bare link was echoed.
  - The goldens were regenerated with `ASSETOPS_REGEN_CH5A1_GOLDENS=1`. Classified diff: kobo = encoding-only ×4 per file; cold/ev = these link changes only, plus the added Ref keys.
- **D5.** The estate Actions `source` is now null when `source_finding_id` is null. It was `/findings/None?revision_id=None`.
- **D6.** An empty mini `selected_event` id drops `?event_id=`.

## Open risks
- Facts are frozen dataclasses that now hold dict Refs. Nothing hashes them today, but a `set()` of facts would raise.
