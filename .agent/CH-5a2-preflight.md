# CH-5a2 pre-flight (Implementer, 2026-11-04)

Branch `task/CH-5a2-chain-endpoints` from main `01133225a`; worktree `C:\Users\assef\Bineyame\AssetOpsV1-ch5a2`.
B = `backend/assetops_backend`, F = `frontend/src`. MD-0 template `status`: `usable: true` (5e589e86). No code written yet.

## Answers to B11

**P1 (B3) — fields `place` and `workflow_label` read**
- `place` (`B/estate/placement.py:144-155`, `_rule` :98-123, `_confidence` :126-141, `_reason` :87-91) reads these row keys: `source_provenance.state`, `consequence.state`, `lifecycle`, `_recurs_after`, `_recurs_after_title`, `_transition`, `_episode_end`, `_mechanism`. It also reads `site_cov.state`.
- `workflow_label` (`B/estate/portfolio.py:206-220`) reads `resolution_state`, `verification_outcome`, `_raw._verification_window` and `application_state`.
- Today's sources:
  - Finding row: `B/estate/coverage.py:179-189` (index heads, `finding_provenance`) and `:246-268` (`consequence`, which is only PRICED, UNPRICED or UNKNOWN; the WITHHELD branches in placement are unreachable).
  - Action row: `coverage.py:_actions` :358-408. This is a lifecycle reduce over `snapshot.actions().events`, plus the `snapshot.verification` plan window.
- Board use: `B/site_outcomes/mini.py:399` reads `estate`, `_findings` :638-663 (confidence at :654) and `_actions` :666-702 (label at :682).
- **ChainReader sources (`B/chain/read.py`):**
  - Lifecycle, transition, episode end and mechanism come from `ChainRequest.findings` (`FindingHead` :170-181).
  - **Missing:** recurs_after id and title, the per-Finding consequence state (`money_head` covers only the lead Finding), and the Finding's source provenance.
  - **Missing:** the Action lifecycle reduce, verification window and selected event time. `action_facts` :250-263 carries only verification_state, cost_check, trial_hours and has_change.
  - See Q1.

**P2 (B7) — source provenance of the verification evidence**
- The value is `rules.source_pair(...)["source_class"]` (`B/actions/verification_rules.py:684-712`). It is stored in three places on evaluate:
  - `details.source.source_class` (`B/actions/verification.py:616,640`);
  - `basis.source_resolutions.*.state` (:631-632);
  - the metric `source_provenance` (`verification_rules.py:744`).
- `VerificationService.summary` (:1044-1050) does **not** carry it, so `ActionFact` (`board.py:155-173`) has no such field.
- None of the three render sites (`board.py:50`, `mini.py:89-94`, `placement.py:42`) has it in scope. `action["source_provenance"]` in coverage is the cited basis/origin provenance, not the verification windows. See Q2.

**P3 (B2) — href inventory**

Server:
- **Board** (`board.py:679-689`, filled :840-850):
  - `evidence_link.href` :686 (templates :95-107);
  - `issues[].href`: Finding :877-881, signal :709-710 and :895-897, warning :717 (`B/outcomes/warnings.py:58,199,234,248,258,271`);
  - `must_not_harm.href` :786, :792-793;
  - `contributors[].href` :906-908 (f-strings across mini.py and `cold.py:322`);
  - `options[].href` :846 (`mini.py:460-465`, `cold.py:158-163`, `ev.py:238-240`);
  - `in_hand` and `earlier` :743-775 (`mini.py:698-699,721,734`, `cold.py:205`, `B/work/domain_action_index.py:457,488`).
- **Cold/EV `/api` Finding hrefs are confirmed.** They originate in `B/analytics/adapters/postgres_assessment_store.py:2349` (cold) and `:3331` (EV), and pass through `cold.py:217` and `ev.py:264-266`.
- **Portfolio:** `portfolio.py:271-273` (`links`), plus the `destination` fields at :367-384, :427, :455-473, :520 and :625. Helpers are in `B/estate/evidence_money.py:108-161` and `B/estate/financials.py:141-156`.
- **Estate Findings:** `B/estate/index.py:94-107` (`_finding_links`), used at :160.
- **Estate Actions:** `index.py:193-196`.
- **CH-4 items:** `B/chain/opportunities.py:121-126`. These already carry `ref {kind, site, id}` and `thread_ref`.
- `B/chain/refs.py` does not exist.
- **Existing `ref` keys with other shapes** (see Q4):
  - board Finding issue `{finding_id, finding_revision_id, thread}` (`board.py:879`);
  - opportunity issue `{opportunity_id, code, thread}` (:895);
  - warning issue `ref` = a string key (:717).
  - COH-5 and COH-13 read `ref.finding_id` and `ref.thread.*`.

Client:
- `F/sites/OutcomeBoard.tsx` `To` :93-95, used at :130, :177, :189, :208 and :230.
- `F/estate/EstatePortfolio.tsx` :148, :159, :189, :201, :371, :391, :435, :438-439 and :672.
- `F/estate/findingIndex.tsx` :297-304 (gate), :315, :336, :372, :381, :395 and :401.
- `F/estate/actionIndex.tsx` :107 and :118-119 (the estate Actions list, `EstateActionsPage` :168).
- **Also rendering server hrefs, but not named in B2:**
  - `F/sites/EarlyWarnings.tsx:25-26,65` (its own `To`);
  - `F/estate/PortfolioOutcomes.tsx:353,391,409`;
  - `F/estate/EstateEvidence.tsx:237`;
  - `F/estate/EstateFinancials.tsx:158-163,186`;
  - `F/sites/SiteWorkActions.tsx:954` and `F/sites/siteWorkCases.tsx:578`;
  - `F/work/GlobalIncidents.tsx:112` and `F/work/workRequestShared.tsx:164,332`.
- **Builders** in `F/shell/operatorSiteRoutes.ts`:
  - as cited: `siteDetailHref` :45, `siteEvidenceHref` :111, `sitePerformanceHref` :143, `siteFindingHref` :162, `siteOpportunityHref` :208, `siteWorkHref` :324, `siteActionHref` :392-408;
  - plus `siteFinancialsHref` :217, `siteFinancialScenariosHref` :183, `siteEvHref` :274, `siteHealthHref` :490, `siteFindingViewHref` :292, and the estate path constants :424-455.
  - There is no thread or case builder. `F/shell/__fixtures__/` does not exist.

**P4 — mini Finding index rows**
- Rows are built by `FindingIndexService._rows`, `B/analytics/finding_index.py:412-460` (links :453-455, categories :458). There is no `lens_flags` today.
- Tests: `test_s4_finding_index_postgres.py`, `test_s4_finding_index_reach.py`, `test_idx_gaps_index.py`, `test_idx_gaps_postgres.py`, `test_idx_gaps_board.py`.
- The frontend Lens cell is the hard-coded "Not assessed" badge at `F/sites/SiteFindingIndex.tsx:606-610`, not :597-600 (that is the State cell). The lens chips are `LensChips` :134-145.
- Estate lens today: `index.py:31` (LENS_FLAG), `:33` (RISK_MECHANISMS) and `:147-148`.
- The single helper exists: `outcome_map.lens_flags(signal_key, domain)` :117-123, with `finding_signal_key` :47.

**P5 — wiring**
- `B/main.py:624-626`: `build_outcome_router(outcome_board, registry, estate=estate_portfolio, tenant=registry_tenant(registry), access=development_access, work_access=site_read_access, unavailable=(SiteStoreUnavailable,))`.
- `B/outcome_api.py`:
  - signature :105-112; `admitted` :116-117; `disclosed` :119-121; `registry.tenant()` and `registry.imported(code)` :136-137; `perf.route` :125 and :168;
  - refusals: `_refuse` :50, `_instant` :54-60, `_mini_day_params` :63-78, `_pin` :81-89, plus the inline PARTIAL_WINDOW and 31-day refusals at :152 and :154;
  - estate scope: `parse_request` (`B/estate/scope.py:120`) with `estate_refusal`, as `B/estate_portfolio_api.py:40-62`.
- The chain router will take the same arguments and helpers. I will move the helpers to a shared module or import them, but not copy them.

**Other code facts**
- **B6:** `progress()` (`portfolio.py:540-568`) sees only `selected_pairs`. The `f_rows` already carry `_thread.id` and `_thread.segment_no`, and the `a_rows` carry `_thread_id` and `_segment_no` (`attach_threads` :131-168). Segments are computed, not stored (`B/chain/lookup.py:99-146`). So `origin_selected` = some selected `f_row` with the same thread and segment. **No question.**
- **B3 `_action_for` fallback:** `portfolio.py:192-194`. `same_segment` :186-190 treats a None segment as a match.
- **B3 cutoff:** there is no `ChainRequest.site_cutoff`. The module function `chain/read.py:29-35` `site_cutoff(domain, request_known_at, evidence_cutoff, k)` is applied per row at `index.py:170-171` and grouped per cutoff in `attach_threads` :149.
- `GradeCounts` (`B/chain/reader.py:20-33`) has `requested, expected, complete, partial, low, no_data, not_expected, pending, enough_data_days`. `Claim.days` takes the §S.2 subset.
- `count_basis` today is a Portfolio inline at `portfolio.py:779-780`, built from coverage status, not GradeCounts.
- `check-architecture.ps1` runs no Python; it dot-sources the `tools/checks/*.ps1` modules (:24-36).
- COH-17 does not exist yet. The collector fetches no `/chain` route.
- `expected-today.json` holds COH-1 ×12, COH-5 ×6 and COH-8 ×3 (plus COH-2 ×2 and COH-7a ×8). `expected-mechanism.json` is `[]`: M3's ×6 were not recorded there, as the CH-5a1 review notes.
- **CH-5a1 Lows:**
  - L4: `site_outcomes/read.py:587-596` `_last_local_day` equals `chain/read.py:110-112` `summary_day`. Its only caller is `read.py:391`.
  - L5: `BoardServices.finding_index` and `parse_finding_index` are still wired at `main.py:547,619` and `composition.py:19,52,75,80` but never read. `covering_days` has no references.

## Questions for the Architect (one batch; each has a proposed default)

**Q1 (B3): ChainReader has no source for 5 of the 12 fields `place`/`workflow_label` read.**
- Missing: recurs_after, per-Finding consequence state, Finding source provenance, the Action lifecycle reduce, and the verification window.
- *Default:*
  - Add two memoised ChainRequest ports in `B/chain/`:
    - `placement_facts(site, finding_ids, k)`: finding provenance state, consequence head state (PRICED/UNPRICED/UNKNOWN by the coverage rule) and recurs_after;
    - `action_rows(site, k)`: chain_action plus its events reduced at `k`.
  - Both reuse the existing reduce and consequence functions by import, moving them into `B/chain/` only if an import cycle forces it.
  - Prove the chip and label unchanged by the L3 A/B.
  - This is about 1.5 units, not counted in the sheet's 6 (see Q9).

**Q2 (B7): the verification `source_class` is not on `VerificationService.summary`/`ActionFact`.**
- *Default:*
  - Add `source_class` to the summary, read from the evaluated outcome's stored `details.source.source_class`, then to `ActionFact`. `board.py`/`mini.py` read it from there.
  - For `placement.py:42`, `coverage._actions` copies the same field onto the estate action row. Once Q1 is done, the row comes from `action_rows`.
  - No new derivation.

**Q3 (PC-1 count claims: scope is not defined in Part B).**
- Plan §2.5.3 says "CH-5a2 builds the claim type and the count claims, plus COH-17". Part B names neither the claims nor the screens.
- *Default:*
  - `Claim` and `count_basis` go exactly as §S.2.
  - Count claims are `count.open_threads`, `count.verified_results` and `count.opportunities` on `/estate/chain` `counts` (Claim wire), with `days` = the summed per-Site GradeCounts subset.
  - The same keys are added as additive `claims` on the Portfolio `summary` and the Findings summary (`opportunity_count`).
  - The Portfolio's existing `summary.count_basis` value then comes from `count_basis(days)`. Any old → new difference is listed in the packet.
  - COH-17 compares claims with equal (key, Sites, window) across those bodies.
  - The collector adds `/estate/chain` per estate window and `/sites/{c}/chain` per built day. This is in `tools/checks/chain_coherence.py`, which is not a FIX-MAIN-1 file.

**Q4 (B2): existing `ref` keys collide, and the Ref union has no kinds for several emitted links.**
- (a) Board Finding and opportunity issues already have `ref` objects of another shape, read by COH-5, COH-13 and the frontend.
  - *Default:* add the Ref keys (`kind`, `site`, `id`, `revision`, `window`) **into** the existing object, additively, keeping `finding_id`, `finding_revision_id` and `thread`.
  - A warning issue's `ref` is a string key. *Default:* keep it, and give warnings a sibling `link_ref` (Ref).
- (b) Links to financials, scenarios, performance, health, evidence, foundation changes, work, maintenance and the Portfolio card destinations are not in the union.
  - *Default:* `SITE{site, view}` with an enumerated `view` (`performance:renewable`, `financials:scenarios`, …), and `ESTATE{path, query}` for `/maintenance/*` and the estate lens pages.
- (c) Other client renderers of server hrefs are not named in B2: EarlyWarnings, PortfolioOutcomes, EstateEvidence, EstateFinancials, Site work, GlobalIncidents and workRequestShared.
  - *Default:* convert only the four B2 components, plus EarlyWarnings (it shares the board's issue and warning hrefs). Leave the rest to CH-5b's hard-wiring guard and list them.

**Q5 (I-08): the cold/EV `/api` Finding hrefs are built in `analytics/adapters/postgres_assessment_store.py:2349,3331`.**
- Editing that file probably invalidates the MD-0 template fingerprint (import-traced, MD0-S5 M1). The same risk applies to `analytics/finding_index.py` (B5/P4) and `actions/verification.py` (Q2).
- *Default:*
  - Build the FINDING Ref with `window` in `cold.py`/`ev.py` from the row's own window and cutoff (via `evidence_money.finding_window_href`'s inputs), leaving the store's `links` untouched until CH-7. The rendered link then comes from `routeFor`, and `href` from `href_for`.
  - For `finding_index.py` and `verification.py`, which must be edited: rerun `status` after editing. If it reads stale, rebuild the template once, at the slice head, with `--budget 540` in parts, as the dispatch allows.

**Q6 (B8): the AST guard must run "from `check-architecture.ps1`", which runs no Python.**
- *Default:* a new `tools/checks/chain-structure.ps1` module registered in `$checkModules`. It calls `$guardPython tools/checks/check_chain_structure.py`, as `configuration-persistence.ps1:974` already does for `sql_statements.py`.

**Q7 (CH-5a1 L2, the UTC-midnight summary card day; B3 re-check).**
- B3 does not move the estate's day rule. `summary_day` (local day of `to − 1 µs`) stays as CH5a1-R2 ruled. So the S card for [31 Oct 00:00Z, 1 Nov 00:00Z) is still Kobo's 1 Nov board.
- *Default:* no change in CH-5a2. Record it for the owner walkthrough.
- *Alternative for the Architect:* the card day is the Site-local day containing the window's **start** for 1-day windows. That would change COH-7a's expectation.
- Related, also unchanged by default: the CH-5a1 residual that `db_today()` is a UTC date (21:00–24:00Z gives the local "yesterday").

**Q8 (CH-5a1 L4/L5 cleanup).**
- *Default:* replace `_last_local_day` with `summary_day`. Delete `BoardServices.finding_index`, `parse_finding_index` and `covering_days`, with their wiring in `main.py`/`composition.py`.

**Q9 (size).**
- With Q1 (+1.5), Q2 (+0.5), Q3 (claims, COH-17 and collector, +1) and Q4's wider ref vocabulary (+0.5), my estimate is about 9 units against 6. The owner rule splits slices over 6.
- *Default split:*
  - **CH-5a2a** (≈5): refs/`href_for`/`routeFor` plus the shared fixture, the three endpoints, lens (B5), progress (B6), `thread_lines` (B4), the exact-join deletion and per-Site cutoff (B3 second and third bullets), the AST guard (B8) and the L4/L5 cleanup.
    - Its L3/L3m target is COH-1/5/8 = 0.
  - **CH-5a2b** (≈4): the board off the estate snapshot (B3 first bullet, Q1), the provenance suffix (B7, Q2), and the PC-1 count claims with COH-17 (Q3).
    - Its L3m target adds COH-17 = 0 and the "on the days checked" window assertion.

## Overlap with FIX-MAIN-1
- The coherence collector imports `tools/demo_combined_finish.app_client`. I read it and do not edit it.
- No w301 goldens, `test_runs_api` or mechanism naming are touched. `mechanism_dataset.py` is used only via `status`/`derive`.

## Next
Stopped per B11. Code begins on the Architect's rulings.
