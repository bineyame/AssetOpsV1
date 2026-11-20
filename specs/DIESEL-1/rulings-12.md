## 9p. Ruling DIESEL-1-R3p — K8 consolidated card (four Sites on the estate screens, the fuel Finding in the estate lists, re-expectations, captures)

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). READ on main at `3bfbff43e` (K4b with R3j3 0058 and K7-F merged). Read: `estate/index.py`, `estate/coverage.py`, `estate/portfolio.py`, `estate/placement.py`, `estate/financials.py:407-435`, `estate/money_invariants.py`, `estate/composition.py`, `estate/adapters/postgres_estate_read.py`, `fuel_balance/adapters/postgres_fuel_balance_store.py:200-335`, `chain/claims.py`, `chain/threads.py:31,111-126`, `site_outcomes/read.py:640-870`, `site_outcomes/mini.py:811-846`, `evidence/overview.py`, `evidence_api.py:393-409`, `config/chain/stored-composer-modules-v1.json`, `tools/checks/chain_coherence.py` (COH-0..13 and helpers), `tools/demo_combined_finish.py` (CO-6, CH5D1-O1, F-COH, `run`), `tools/demo_combined_rows.py` (`optimize_card`, `kis8_protect`), both Kobo and Kisiwa templates, `frontend/src/sites/SiteWindowOverview.tsx`, `MiniPerformance.tsx`, `shell/SiteDetailFrame.tsx`, `estate/findingIndex.tsx`, `EstatePortfolio.tsx`. Nothing was run.
- **This card supersedes every scattered K8 line** (§8.4 K8 row, §3.4 D4, §9j.14, §9l.4, §9m.5, §9j2.5 item 3, §9o.1's last bullet, §9c.4). Where they disagree, this card wins. D4's Assure value line stays removed (H2).

### 9p.1 Code reality that decides the card (READ)

1. **The fuel Finding is in no estate list on main.** `EstateSnapshot.finding_index` (`postgres_estate_read.py:163-164`) reads only the dispatch domain, and `coverage._mini_grid_basis` builds rows only from it. `select_finding_scope` therefore never emits a fuel row, so the estate Findings index, the Portfolio rows, `summary.category_counts`, `placement_counts`, `finding_count`, the Findings lens chips and the thread columns all omit it.
2. **R3j2 item 3 is unmet on main.** Its "Kisiwa Protect `open_findings` +1 via `portfolio.py:297 category_counts`" does not happen, because `category_counts` runs over `select_finding_scope` members. Two clarifications:
   - `summary.category_counts` is a wire field. No client screen renders it today (the only frontend reference is the type at `estateClient.ts:465`), and `demo_combined_after.py:286` reads only GROW.
   - The Portfolio **Protect card's value** is `count.sites_disrupted` (`read.py:859`), which correctly excludes fuel (R3j2 item 4). It is not meant to rise, and it does not.
   - **This round fixes item 3** by putting the fuel row into `select_finding_scope` (§9p.2).
3. **Money is separate by construction.** Estate money comes only from `select_financial_scope` (`financials.py:407`). That calls `site_coverage` → `_mini_grid` → `finding_index` itself, independently of `select_finding_scope`. `double_count_violations` reads only `selected_lines` and money `groups`. **So a join placed in `select_finding_scope`, after coverage, can never reach a money line, a group, `estate_total`, `combined_value` or Financials.** A join placed in `site_coverage`, `_mini_grid` or `finding_index` would reach them all. That is the whole design constraint.
4. **The W6 module list already has the fuel store** (`fuel_balance.adapters.postgres_fuel_balance_store`, listed). It does **not** have `actions.verification_rules` (`parse_exact`, called by `to_window`) or `fuel_balance.finding_text` (`litres1`, `money`, `short_day`). K4b's stored board already runs both whenever a fuel Finding is present, so K9's guard CLI would report them in `unlisted_modules`. That is a K4b gap the Kobo-only evidence could not show. K8 closes it (§9p.2 item 7).
5. **`SERVICE_FEEDERS` is not served for Kisiwa.** `GET /api/sites/{id}/overview` returns `site_overview.serve(...)` (the selected-day window summary) for an imported Site (`evidence_api.py:394-397`). The legacy `OverviewReadModel` and its `SERVICE_FEEDERS` cards are reached only for a non-imported Site. Kisiwa is imported (K1), so no Kisiwa screen shows "Clinic feeder" from that source.
6. **The two UI strings are on Kisiwa's screens.** `MINIGRID_OBJECTIVE` renders on every mini Site's Overview (`SiteWindowOverview.tsx:487-492`). `CLINIC_FEEDER_LABEL` renders for the CRITICAL row of the Service page (`MiniPerformance.tsx:974`). Kisiwa's cold store is declared `ESSENTIAL_SERVICE` (`demo_combined_kisiwa.py:62`), so it is Kisiwa's CRITICAL row. Kisiwa's Foundation loads are "Households", "Cold store (ice and fish)" and "Water pump" (`kisiwa-diesel-hybrid-60kw.yaml:156-172`). Its devices are still named `clinic-meter` and `mill-meter`.
7. **Estate rows match only W1 Actions.** `_action_for` matches `select_action_scope` rows: the W1 `action` table, mini only. The fuel Action is a `FUEL_BALANCE` domain Action, so a fuel row would read "No action agreed yet" next to a verified fix. Cold and EV rows have the same pre-existing gap, and it stays out of scope. For the fuel row it would contradict the Kisiwa board on the demo's main beat, so K8 corrects it for fuel rows only (§9p.2 item 5).
8. **COH rows and Kisiwa.** `chain_coherence.day_windows` collects boards only for `SITE_CODE` (three Sites), so COH-3/4(board)/5/10(board)/13 never see a Kisiwa board. The estate-level rules do see Kisiwa: COH-1 (links in Portfolio and Findings bodies), COH-4 (Portfolio ⊂ Findings) and COH-7a (summary Site windows). COH-7a's zone lookup (`chain_coherence.py:646`) has no Kisiwa zone, so Kisiwa's local-day window would be compared with a zone-less day.

### 9p.2 Q1: the estate fuel Finding entry (exact design)

1. **Store (`B/fuel_balance/adapters/postgres_fuel_balance_store.py`).** Add a connection-taking public method with the same contract as `fuel_findings`:
   ```python
   def fuel_findings_on(self, c: Connection, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                        known_at: datetime | None) -> tuple[FuelFinding, ...]:
       """DIESEL-1-R3p: `fuel_findings` on the caller's read-only connection (the estate snapshot); same refusal,
       same filter and order. Opens no transaction."""
   ```
   - It holds the existing validation and filter body.
   - `fuel_findings` becomes `return self._read(lambda c: self.fuel_findings_on(c, tenant_id, site_id, lo, hi, known_at))`.
   - Behaviour is byte-identical. The K4b and K5 tests stay green unchanged.
2. **Estate reader (`B/estate/adapters/postgres_estate_read.py`).**
   - `PostgresEstateRead.__init__` gains `fuel: Any = None` as the **last** keyword, stored as `self.fuel`, with the comment `# DIESEL-1-R3p: PostgresFuelBalanceStore (fuel_findings_on on this connection); None = no fuel rows`.
   - `dispose()` also calls `self.fuel.dispose()` when it is not None.
   - `EstateSnapshot` gains `fuel_findings(t, s, from_, to, k) -> list[dict]`:
     - `[]` when `self._o.fuel is None`;
     - else `self._o.fuel.fuel_findings_on(self._c, t, s, from_, to, k)`, plus **one** batched `SELECT finding_revision_id, evidence_id FROM finding_revision_evidence WHERE tenant_id = :t AND site_id = :s AND finding_revision_id = ANY(CAST(:ids AS uuid[]))` on `self._c`;
     - each item is `{"finding": <FuelFinding>, "evidence_ids": sorted ids}`.
   - No new transaction and no write. `configuration-persistence.ps1` `$pgReaders` is unchanged, because no new driver import is added.
3. **Composition (`B/estate/composition.py`).**
   - `build_estate_read` builds `fuel = build_fuel_balance_store(database_url)` with a **function-local** import from `assetops_backend.fuel_balance.composition` (the site_outcomes pattern, which avoids the `work.composition` cycle), and passes `fuel=fuel`.
   - `build_estate_evidence_service`'s `keys` tuple gains `"fuel"` (last), so the Portfolio and Evidence reader carries it.
4. **The join (`B/estate/index.py`, `select_finding_scope`; no new module).** After the per-Site `for r in cov["rows"]` loop, for each Site with `domain == MINI_GRID` and `cov["state"] in (CURRENT, HISTORICAL, PARTIAL)` (the same gate as mini rows, "reading 6"):
   - `rows += _fuel_rows(snap, site, cov, req, scope["k"])`.
   - Read via `getattr(snap, "fuel_findings", None)`. A snapshot without it (test fakes) gives no fuel rows and no error.
   - Header comment at `_fuel_rows`: `# DIESEL-1-R3p, MOCK DEVIATION MD-FUEL-K4-1: the unexplained-fuel Finding joins the estate Finding rows here, after coverage and outside site_coverage/_mini_grid, so it never reaches select_financial_scope, selected_lines, money groups, estate_total or double_count_violations. Its money is its own fuel-residual-1 row, shown on its own and never added.`
   - Candidates: `snap.fuel_findings(tenant_id, site["site_id"], req.from_, req.to, scope["k"])`. These are the latest revision as known at `k` whose cited night window intersects `[from, to)`, every lifecycle. That is the same window rule as K4b's board `fuel_findings(work_lo, end)`, so COH-4's board half agrees once K9 collects Kisiwa boards.
   - **Row fields.** Every key a mini row has, in the same order, so the Findings and Portfolio wires are unchanged in shape. With `f = item["finding"]`, `fid = str(f.finding_id)`, `frid = str(f.revision_id)`:
     - `"finding_id": fid`, `"finding_revision_id": frid`, `"site_id"`, `"site_code"` and `"site_name"` as mini;
     - `"finding_label": finding_label(fuel_text.TITLE)`, `"title": fuel_text.TITLE` ("Unexplained fuel overnight"; import `assetops_backend.fuel_balance.finding_text as fuel_text`);
     - `"priority": None`, `"confidence": None`, `"confidence_reasons": []`;
     - `"lifecycle": str(f.lifecycle)`;
     - `"lens_flags": lens_flags(finding_signal_key("UNEXPLAINED_FUEL"), MINI_GRID)`, which gives `["RISK"]`;
     - `"categories": categories_for(finding_signal_key("UNEXPLAINED_FUEL"), MINI_GRID)`, which gives MAPPED, Protect, MOVES `MG-8`. These are the `outcome_roles` entries R3j2 added, so `category_counts` counts it under `PROTECT_ASSET`;
     - `"consequence"`: §9p.2 item 6;
     - `"source_provenance": snap.finding_provenance(tenant_id, site["site_id"], frid, item["evidence_ids"])`;
     - `"episode_start": wire_time(f.window.window_start)`, `"status": cov["state"]`;
     - `**_links({"finding": refs.fuel_finding_ref(code, fid), "site": site_home_ref(code, MINI_GRID)})`, the K5 page with no revision, as the board links it;
     - private keys: `"_at": f.window.window_start`, `"_site": site`, `"_domain": site["site_type"]`, `"_episode_end": f.window.window_end`, `"_mechanism": "UNEXPLAINED_FUEL"`, `"_recurs_after": None`, `"_recurs_after_title": None`, `"_transition": None`, `"_revision_no": f.revision_no`.
   - **Not touched:** `cov` (no array, token or selection id gains fuel ids), `cutoffs`, and the Site coverage state. The selection token does not cover fuel rows; that goes on the after-the-demo list (§9p.10).
5. **Portfolio Action column for fuel rows only (`B/estate/portfolio.py`, `B/estate/placement.py`).**
   - `placement.place` gains a last keyword `label: str | None = None`. When it is given, it replaces `workflow_label(action)`. The default keeps every existing caller byte-equal.
   - `portfolio.py` gains:
     ```python
     #: DIESEL-1-R3p: a fuel row's Action is a FUEL_BALANCE domain Action, which `_action_for` cannot see; its column
     #: reads its thread state with the existing workflow words. Cold and EV rows are unchanged.
     FUEL_THREAD_LABEL = {"RESOLVED_MONITORING": "Verified", "CLOSED": "Verified", "CHANGE_APPLIED": "Applied",
                          "ACTION_IN_HAND": "Pending"}
     ```
   - In `portfolio_row`, when `r["_mechanism"] == "UNEXPLAINED_FUEL"`, compute `label = FUEL_THREAD_LABEL.get(((r.get("_thread") or {}).get("state")), "No action agreed yet")`. Pass it to `place(..., label=label)` and use it as `"workflow_label"`. `action_*` stay None.
   - For every other row, `label` is None and nothing changes.
6. **Consequence block (fuel `fuel-residual-1`, own basis).** Let `q = f.consequence` (the stored row, or None), and let `live` mean `cov["state"] == CURRENT` (not HISTORICAL and not PARTIAL: the mini rule "a prior or partly checked amount is never current money").
   - `q is None`: `{"state": "UNPRICED", "amount": None, "amount_low": None, "amount_high": None, "currency": None, "source_revision_id": None, "basis": "UNEXPLAINED_FUEL_AT_DECLARED_PRICE"}`. The client words are "No consequence recorded".
   - `q["state"] == "UNPRICED"`: the same, with `source_revision_id = q["id"]`. The client words are "Unpriced".
   - `q["state"] == "PRICED"` and **not** `live`: `state "UNKNOWN"`, no amounts, `source_revision_id = q["id"]`. The client words are "Historical as of …" or "Partly checked · …".
   - `q["state"] == "PRICED"` and `live`: `state "PRICED"`, with `amount_low = amount = fuel_text.money(q["amount_low"])`, `amount_high = fuel_text.money(q["amount_high"])` (the same two-place text as K4b's Protect line), `currency = q["currency"]` and `source_revision_id = q["id"]`.
   - `basis` is the literal `"UNEXPLAINED_FUEL_AT_DECLARED_PRICE"` with the comment `# equals the stored fuel_residual_consequence_revision.basis and site_outcomes/mini.py FUEL_BASIS`. A test asserts the equality. It is additive, and only fuel rows carry it.
   - **Placement** follows from the existing rules, and `placement.py` gets no `_UNPRICED_REASON` entry:
     - priced and no thread work: rule 4, `COMPARE_VALUE` `PRICED_SINGLE` ("Priced cost exposure; no like line to compare with"). That is true, because the fuel row has no money line, so `line_group` is None;
     - unpriced: rule 5, `UNPRICED_OTHER` ("No price basis for this finding");
     - thread verified: rule 3, `MONITOR` `VERIFIED_WATCH_RETURN` with `provenance_suffix(None)`.
   - **Fuel money joins no estate money total.** It is never in `select_financial_scope`, `selected_lines`, `money.groups`, `money.estate_total`, `summary.combined_value`, `value_cards`, `footer`, Financials or any sum. It appears only as the row's own interval, beside K4b's own Protect line.
7. **W6 stored-route coverage.**
   - The estate Findings index (`estate_api.py:64`) and the Portfolio (`estate_portfolio_api.py:75`) are stored routes. They now read `finding`, `finding_revision`, `finding_revision_evidence`, `fuel_balance_window` and `fuel_residual_consequence_revision`. All of these are triggered: 0047, plus 0058 for the two fuel tables. **No migration.**
   - **No new reader module is created:** the join lives in `estate/index.py` and the snapshot method in the listed estate adapter.
   - `config/chain/stored-composer-modules-v1.json` gains **two** modules, in alphabetical position: `"assetops_backend.actions.verification_rules"` (after `"assetops_backend.actions.verification"`) and `"assetops_backend.fuel_balance.finding_text"` (after `"assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store"`; builder: keep the file's existing sort rule, whichever `test_module_list_is_recorded_and_resolves` enforces). Both are clock-free (READ). `test_ch5c2_clock_guard.py` must stay green unchanged.
   - K9's guard CLI acceptance (R3j3) then covers the estate routes too.

### 9p.3 Q2: the Assure count. Confirmed, with the window condition stated

- `count.verified_results` counts a thread in `VERIFIED_CLASS` (`RESOLVED_MONITORING`, `CLOSED`; `threads.py:113`) whose **Finding occurrence episode meets `[lo, hi)`** (`claims._finding_threads`), read at `LATEST_KNOWN` under the request cutoff. The fuel thread after K6b's VERIFIED is `RESOLVED_MONITORING`, so it counts **on windows that contain night 4's window** (the story week). **It does not count on the S-only window.** That is correct, not a defect. No product code changes.
- **K8 adds one L0 test** in `backend/tests/test_k8_estate_fuel.py`, through `estate_count_claims` with a fake `req`. Cases:
  - a `UNEXPLAINED_FUEL` thread at `RESOLVED_MONITORING` with a Finding occurrence inside `[lo, hi)` gives verified +1 and is absent from `disrupted`;
  - the same thread with the occurrence outside the window adds 0;
  - the test must fail if `VERIFIED_CLASS` loses `RESOLVED_MONITORING`.
- **The finish expectation is K9's** (it needs the four-Site run). K9's KIS-6 gains: on the week window, `/api/estate/chain` `sites` entry for `KISIWA-001` has `threads.verified == 1`, and the Portfolio Assure card `claim.value` equals the chain `count.verified_results`. Both are read from data. **No Assure value line (H2).**

### 9p.4 Q3: Kisiwa objectives. None for the demo (confirmed)

- Kisiwa shows the honest "no target" state. `objective_site_count` stays **3**, CO-6's `== 3` stays, and the Assure card detail reads the targets at 3 Sites, which is true.
- Declaring one would add stored objective data, a board and estate re-expectation, and captures for no demo beat. Not demo-critical (owner 2026-11-05). After-the-demo list: "Kisiwa operating objectives (for example, cold store supply kept)".

### 9p.5 Q4: device-id copy

**Shared rule R-LOAD:** a Site whose declared load names include a clinic or health load (`/clinic|health/i`) keeps v69's Kobo words. Any other Site's words are built from its own load names. **Kobo bytes do not change.** Kobo's Foundation names "Health clinic" (`kobo-mini-grid-60kw.yaml:195`), and the existing CRITICAL test fixture "Health post" matches as well, so its expectations stay byte-equal. **MOCK DEVIATION MD-KIS-K1-1** (already logged) covers the Kisiwa words, with a header comment at each helper.

1. **`evidence/overview.py` `SERVICE_FEEDERS`: no change.** It is not served for an imported Site (§9p.1 item 5).
   - **Pre-flight (a):** confirm `site_overview.serve` returns a body for `KISIWA-001`.
   - If it returns None, that is **stop S-5**. Do not add a feeder rule unasked.
   - After-the-demo list: "feeder labels from the Foundation on the legacy overview".
2. **`SiteWindowOverview.tsx` `MINIGRID_OBJECTIVE`: data rule.**
   - `OverviewMiniReads` gains `loadNames?: readonly string[]`: the Site's Foundation `components` with `component_type === "LOAD"`, `display_name` in document order. `SiteDetailFrame.tsx` sets it from the loaded `site` record when it builds `mini`.
   - New exported pure function in `SiteWindowOverview.tsx`:
     ```ts
     /** DIESEL-1-R3p R-LOAD, MOCK DEVIATION MD-KIS-K1-1: the objective names the Site's own loads; a Site with a clinic
      *  or health load keeps v69's words (Kobo byte-equal). */
     export const OBJECTIVE_NO_LOADS = "Objective: serve this site's loads while protecting the battery reserve.";
     export function minigridObjective(loadNames: readonly string[] | undefined): string
     ```
     - `undefined` gives `MINIGRID_OBJECTIVE`, so every existing caller and test is byte-equal.
     - Any name matching `/clinic|health/i` gives `MINIGRID_OBJECTIVE`.
     - `[]` gives `OBJECTIVE_NO_LOADS`.
     - Otherwise it gives `` `Objective: serve ${list} while protecting the battery reserve.` ``, where `list` is the names verbatim joined as "A", "A and B" or "A, B and C" (no serial comma).
   - **Kisiwa literal:** `Objective: serve Households, Cold store (ice and fish) and Water pump while protecting the battery reserve.`
   - `ObjectiveLine` renders `minigridObjective(mini?.loadNames)`.
3. **`MiniPerformance.tsx` `CLINIC_FEEDER_LABEL`: data rule.**
   ```ts
   const feederName = (row: ServiceRow): string =>
     row.role !== "CRITICAL" ? row.load_label
       : /clinic|health/i.test(row.load_label) ? CLINIC_FEEDER_LABEL : `${row.load_label} feeder delivered power`;
   ```
   - It carries an R-LOAD and MD-KIS-K1-1 comment.
   - **Kisiwa literal:** `Cold store (ice and fish) feeder delivered power`.
   - **Pre-flight (b):** confirm Kobo's served CRITICAL `load_label` matches `/clinic|health/i` (from the Kobo mini-depth golden or fixture). If it does not, that is **stop S-6**; never guess.

### 9p.6 Q5: template signal names. Deferred (confirmed)

- "Active power to the clinic" and "Active power to the mill" (`kisiwa-diesel-hybrid-60kw.yaml:312,320`) appear only in signal and evidence tables.
- A v2 template plus a re-import puts the K7 digests and the 3568 s build at risk for no demo beat.
- **Deferred after the demo as part of MD-KIS-K1-1.** After-the-demo list: "Kisiwa template v2: meter signal names to the cold store and water pump, then re-import".
- DS-1 note (for K9's beat): do not open Kisiwa's signal tables in the demo.

### 9p.7 Q6: re-expectations (exact values). K8 edits these rows directly; they are named here

The rule for every row: the core three Sites, plus Kisiwa **iff** the dataset holds Kisiwa. That is read from data, never typed from a run, so a three-Site partial prepare stays green.

1. **CO-6** (`T/demo_combined_finish.py:451`). A new helper is cached on `ctx`, with one `SELECT 1 FROM site WHERE site_code_key = lower(%s)` through the `_kisiwa_read` connection pattern:
   ```python
   def _kisiwa_present(ctx: Ctx) -> bool:
       """DIESEL-1-R3p: whether the dataset holds the Kisiwa Site (cached)."""
   def expected_site_codes(kisiwa: bool) -> list[str]:
       return sorted([KOBO, COLD, EV] + ([KISIWA] if kisiwa else []))
   ```
   - `assert codes == expected_site_codes(_kisiwa_present(ctx)), codes`.
   - `objective_site_count == 3` **stays** (§9p.4).
   - `double_count_violations(body) == []` stays and must still pass with fuel rows present (§9p.2 item 6).
   - The return gains `"kisiwa_present"`.
2. **CH5D1-O1** (`T/demo_combined_finish.py:1165`; A3 L3).
   - `demo_rows.optimize_card(summary, site="KOBO-001", allowed=("KOBO-001",))` gains the `allowed` parameter, and the call passes `allowed=(KOBO, KISIWA)`. The priced codes come from the summary in Site order.
   - Assert `site in codes` and `set(codes) <= set(allowed)`.
   - **Exactly one** (`[KOBO]`): the existing assertions, byte for byte.
   - **Two or more:**
     - `card.value.text == card_text("cost.sites", sites=sites_text(len(codes)))`;
     - `card.claim is None`;
     - `card.detail == " · ".join(card_text("cost.site", site=<site_name or code>, text=claim["text"], small=COST_SMALL[claim["key"].removeprefix("money.")]) for each priced Site in order)`, with imports from `assetops_backend.chain.vocabulary` and wherever `sites_text` lives.
   - It returns `{"text": card.value.text, "priced": codes}`.
   - Whether Kisiwa is priced is read from its board claim, never typed. The no-sum check stays in K9's KIS-6.
   - The docstring cites R3p.
3. **F-COH / COH-1** (`T/checks/fixtures/chain_coherence/screen_routes.json`). Add three App routes, keeping the file `sorted(set(...))`:
   - `"/sites/:siteId/domain-actions/:actionId/fuel-verification"`;
   - `"/sites/:siteId/domain-actions/:actionId/verification"` (the CH-9b3 mill verdict route, which is in `App.tsx` but missing from the file);
   - `"/sites/:siteId/fuel-findings/:findingId"`.

   The two `domain-actions` entries sort after `/sites/:siteId/configuration`, and `fuel-findings` sorts after `/sites/:siteId/foundation/changes/:changeId`.
4. **COH-7a** (`T/checks/chain_coherence.py:646`). Add, below `LOCAL_DAY_TZ`:
   `SUMMARY_SITE_TZ = {"KISIWA-001": "Africa/Dar_es_Salaam"}  # DIESEL-1-R3p: config/operational-actions/kisiwa-001-operational-actions-v1.yaml timezone; Kisiwa boards stay K9's (SITE_CODE)`
   - The lookup becomes `{**{SITE_CODE[k]: z for k, z in LOCAL_DAY_TZ.items()}, **SUMMARY_SITE_TZ}.get(...)`.
   - **Pre-flight (c):** confirm Kisiwa's stored Site timezone is `Africa/Dar_es_Salaam` (K1's Site document). If it is not, that is stop S-10.
5. **COH-10: no change.** It iterates the expected threads only, so an unlisted Kisiwa thread cannot fail it. **K9** adds the Kisiwa fuel thread `{"name": "kisiwa-fuel", "site_code": "KISIWA-001", "mechanism": "UNEXPLAINED_FUEL", "findings": [<night-4 finding id from kisiwa.json>]}` to `build_expected_threads`, together with the board collection.
6. **COH-13 / COH-4 board half (`SITE_CODE`): K9's job.**
   - Extending `SITE_CODE` (and `LOCAL_DAY_TZ` with `"kisiwa": "Africa/Dar_es_Salaam"`) collects Kisiwa boards. That switches on COH-3/4/5/10/13 for Kisiwa. It can only be proven on a four-Site bundle, and it is the same family as COH-17/V4, which K9 owns.
   - COH-4's estate half (Portfolio ⊂ Findings) already includes Kisiwa, and it holds by construction: both come from `select_finding_scope`.
   - K9's card gains: "`SITE_CODE`/`LOCAL_DAY_TZ` + Kisiwa; COH-10 Kisiwa thread; COH-13/COH-4 board half on Kisiwa (R3p)".
7. **Not changed:** `kis8_protect`'s `tally["compared"] == 3` (UF1's check count, not a Site count), CO-6b, CO-8, CO-11 and `_boards` (three-Site by design).

### 9p.8 Q7: the K7-F L3 docs. Yes, inside K8 (doc only, about 0.02)

- `backend/tests/test_demo_combined_postgres.py:3`: "(all three Sites, the shipped day list)" becomes "(all four Sites, the shipped day list)".
- `:9`: "one prepare is about 20-25 min" becomes "one prepare is about 2.0-2.35 h (DIESEL-1-R3n)".
- `backend/TESTING.md:327-328`: "one three-Site `tools/demo_combined.py prepare`, about 20-25 min" becomes "one four-Site `tools/demo_combined.py prepare`, about 2.0-2.35 h (DIESEL-1-R3n)".
- No code or runtime changes.

### 9p.9 Q8: capture data. Ruled (a) + (b); no dedicated four-Site prepare

- **(a) Kisiwa-only captures, inside K8 code.** Clone `assetops_demo3_kisiwa_test` to producer scratch `assetops_k8_audit_kisiwa` (`CREATE DATABASE … TEMPLATE …`, with no open connection to the template). Upgrade the clone to head (0058) at the K8 commit, `serve` it read-only, capture, then drop the clone. **The kept source DB is never written.** Captures at 1440 and 390:
  - the Kisiwa Overview objective line;
  - the Kisiwa Service page with the CRITICAL feeder name;
  - the estate Findings page (all and Risks) showing the Kisiwa fuel row;
  - the Portfolio row group showing the fuel row with "Verified".

  The same clone is the Postgres-backed evidence. In process, against the clone, read `/api/estate/findings` and `/api/estate/portfolio` for the story week and print:
  - the fuel row (consequence and link);
  - `category_counts.PROTECT_ASSET`;
  - `money.groups`/`selected_lines` lengths;
  - `double_count_violations == []`.
- **(b) The four-Site captures are a "K8 capture phase" (0.25) on K9's rehearsal DB.** This avoids a second 2.0–2.35 h heavy job (machine time and the one-heavy-job gate). **§3.5's "then drop the DB" is amended to: keep the rehearsal DB and work folder until the K8 capture phase and K9's guard CLI are done, then drop.** Scope:
  - the four-Site Portfolio, estate Findings (all, Risks), the Sites list and navigation, at 1440 and 390;
  - the all-26 recapture by W1-F5b's procedure (168 pairs as of W1-F5b), plus the Kisiwa pages built since (K5's Fuel night mode and fuel Finding page, K6b's verdict page, Kisiwa board): the regenerated audit index;
  - K4b's Protect line (§9p.11).

  The capture phase is its own small branch, `task/DIESEL-K8c-captures`, from main after the rehearsal. Coordinator capture check, then merge.
- **How K8 code merges before K9 without the four-Site self-check:** on review ACCEPT (W1 rule), with this evidence:
  - (i) the L0 tests of §9p.12, including pass and fail self-tests for every re-expected row, on synthetic bodies;
  - (ii) the Postgres test on `assetops_k8_test`;
  - (iii) the clone evidence of (a).

  The re-expected rows are data rules, so a three-Site dataset must still pass them. The builder proves that with the self-tests' three-Site cases.
- **If a re-expectation is wrong at K9's rehearsal:**
  1. K9 does **not** edit the row. It reports a stop (the §9o.1 pattern) with the row's printed `check.json` entry.
  2. K9 copies `check.json` to `check-rehearsal.json` first.
  3. The Architect rules, and a Sonnet fix round on `task/DIESEL-K8-fix-reexpect` edits only the named row or fixture.
  4. After it merges, `python tools/demo_combined_finish.py check <url> <work>` re-runs on the **kept** rehearsal DB. `run` skips `mutates` rows, so the re-check is read-only. No re-prepare is needed, because read-path code changes rebuild stored bodies through `code_version`.
  5. Only a fix that changes prepared **data** needs a re-prepare. That goes to the Architect, and the owner is told the machine time.
  6. K9's measured rehearsal wall time stands either way.

### 9p.10 After-the-demo list (coordinator)

- estate selection token covers fuel rows;
- estate rows match domain Actions (Cold, EV, fuel), replacing the fuel-only thread label;
- Kisiwa operating objectives;
- feeder labels from the Foundation on the legacy overview;
- Kisiwa template v2 signal names and re-import (MD-KIS-K1-1).

### 9p.11 Q9: the K4b Protect line. Confirmed: capture only

`portfolio_cards` emits `fuel_lines` and `fuel_note` (`read.py:850-865`), and `PortfolioOutcomes.tsx` renders them (K4b, merged). K8 changes neither and captures them in §9p.9 (b). KIS-8a (K4b) and UF1 already guard them.

### 9p.12 Tests (localised; no full suite)

Every "must fail" names the mutation the reviewer applies to a scratch copy.

**Backend L0, new `backend/tests/test_k8_estate_fuel.py`** (fake snapshot with `fuel_findings`, built on the existing estate fake patterns):
1. **Row.** A CURRENT mini Site with one SUPPORTED priced fuel Finding gives exactly one fuel row in `EstateIndexService._findings`, with every §9p.2 item 4 field:
   - `lens_flags == ["RISK"]`;
   - categories MAPPED with `PROTECT_ASSET`/MOVES/`MG-8`;
   - `links.finding == "/sites/KISIWA-001/fuel-findings/<id>"`;
   - `link_refs.finding.kind == "FUEL_FINDING"`;
   - consequence PRICED with the two-place amounts and `basis`.
2. **Money untouched.** `_portfolio` with and without the fuel Finding gives equal `selected_lines`, `money`, `value_cards`, `footer`, `summary.combined_value`, `summary.combined_value_state`, and `double_count_violations(body) == []`. Must fail if the join moves into `site_coverage`/`_mini_grid`.
3. **Counts.** `category_counts.PROTECT_ASSET.open_findings` is +1 and `sites_with_primary_finding` includes the Site. `finding_count` is +1. The Risks lens shows the row, and the Cost lens does not.
4. **Consequence cases.**
   - no row: UNPRICED with null source;
   - UNPRICED row: UNPRICED with its id;
   - PRICED with PARTIAL coverage: UNKNOWN with no amounts;
   - PRICED with HISTORICAL: UNKNOWN with no amounts;
   - `basis` equals `site_outcomes.mini.FUEL_BASIS`.
5. **Gates.**
   - Coverage UNKNOWN/PENDING/STALE gives no fuel row. Must fail if the gate is dropped.
   - A window outside `[from, to)` gives no row.
   - A snapshot without `fuel_findings` gives no row and no error.
   - A Site whose `fuel_findings` returns `[]` gives `_findings` and `_portfolio` bodies equal to the bodies from a snapshot lacking the method (Kobo byte-equality).
6. **Action column.**
   - A fuel row with thread `RESOLVED_MONITORING` gives `workflow_label == "Verified"`, placement `MONITOR`/`VERIFIED_WATCH_RETURN`.
   - Thread `OPEN` and priced gives "No action agreed yet", `COMPARE_VALUE`/`PRICED_SINGLE`.
   - Unpriced and OPEN gives `UNPRICED_RISK`/`UNPRICED_OTHER`.
   - A **cold** row with a `RESOLVED_MONITORING` thread keeps "No action agreed yet". Must fail if the override is not mechanism-gated.
   - `place(row, None, cov, None)` without `label` is unchanged.
7. **Assure.** §9p.3.
8. **Store parity.** With a fake connection, `fuel_findings_on` and `fuel_findings` return equal tuples, and both refuse bad bounds with `FINDINGS_REFUSED`.

**Backend Postgres, new `backend/tests/test_k8_estate_fuel_postgres.py`** (`assetops_k8_test` only; reuse `test_k4a_fuel_finding_postgres.py`'s fixture helpers by import, never copy):
- Raise one priced fuel Finding.
- `build_estate_index_service(url).findings(...)` shows the row, with consequence from the stored row and evidence-backed `source_provenance` state not `UNKNOWN`.
- `build_estate_portfolio_service(url).portfolio(...)` `money.groups`/`selected_lines` contain no fuel id.
- One estate read opens exactly one connection: assert through the existing engine-connect counting pattern if one exists, else skip this assertion and say so in the packet.

**Unchanged and green:** `test_ch5c2_clock_guard.py` (module list +2), `test_w303_portfolio_api.py`, `test_cc_placement.py`, `test_cov_partial_portfolio.py`, `test_ch6b2_portfolio_cards.py`, `test_pv1_value_lines.py`, `test_k4b_protect_fuel.py`, `test_out_b4_imports.py`, and estate goldens (fakes hold no fuel; **any golden diff is stop S-1**).

**Rows and coherence self-tests:**
- `backend/tests/test_demo_combined_finish_rows.py`:
  - `expected_site_codes(False/True)`;
  - `optimize_card`: one priced passes (unchanged); Kobo and Kisiwa priced passes with exact `detail`; Kisiwa priced with `allowed=(KOBO,)` fails; Kobo unpriced fails.
- `tools/checks/test_chain_coherence.py`:
  - COH-7a Kisiwa summary Site passes with the Dar local-day window and fails with the UTC-midnight window (must fail if `SUMMARY_SITE_TZ` is removed);
  - COH-1 accepts the fuel Finding and fuel verdict hrefs (must fail if either route is removed);
  - the route file stays sorted and unique.

**Frontend:**
- the `SiteWindowOverview` test file:
  - `minigridObjective(undefined)` and Kobo's names give `MINIGRID_OBJECTIVE`;
  - Kisiwa's names give the exact Kisiwa literal;
  - `[]` gives `OBJECTIVE_NO_LOADS`;
  - the rendered line uses `mini.loadNames`;
- the `MiniPerformance`/`miniServiceRoutes` test files:
  - "Health post" and "Health clinic" give `CLINIC_FEEDER_LABEL`;
  - "Cold store (ice and fish)" gives the Kisiwa literal;
- `estatePortfolio.test.tsx`/`findingIndex` tests: a fixture fuel row renders its interval, "Verified" and the `/fuel-findings/` link with no client words added;
- `tsc`.

**Guards:**
- `tools\check-all.ps1`, `check-architecture.ps1`, `check-agent-workflow.ps1`, `check-navigation-truthfulness.ps1`, run directly with no `-ExecutionPolicy`;
- chain coherence self-tests;
- `node tools/checks/frontend-hardwiring.mjs` (no rise);
- the fast tier for the edited backend files.

**Not run:** full suite, prepare.

### 9p.13 Files (approved list)

- **Backend:**
  - `B/fuel_balance/adapters/postgres_fuel_balance_store.py` (`fuel_findings_on`);
  - `B/estate/adapters/postgres_estate_read.py` (`fuel` kwarg, `dispose`, `EstateSnapshot.fuel_findings`);
  - `B/estate/composition.py`;
  - `B/estate/index.py` (`_fuel_rows`, the join);
  - `B/estate/portfolio.py` (`FUEL_THREAD_LABEL`, `portfolio_row`);
  - `B/estate/placement.py` (`label` kwarg only);
  - `config/chain/stored-composer-modules-v1.json` (+2).
- **Tools:**
  - `T/demo_combined_finish.py` (CO-6, `_kisiwa_present`, `expected_site_codes`, the CH5D1-O1 call);
  - `T/demo_combined_rows.py` (`optimize_card`);
  - `T/checks/chain_coherence.py` (`SUMMARY_SITE_TZ`);
  - `T/checks/fixtures/chain_coherence/screen_routes.json` (+3);
  - `T/checks/test_chain_coherence.py`.
- **Frontend:**
  - `F/sites/SiteWindowOverview.tsx`;
  - `F/shell/SiteDetailFrame.tsx` (`loadNames` only);
  - `F/sites/MiniPerformance.tsx` (`feederName` only);
  - their test files;
  - `F/estate/__tests__/` fixtures as needed.
- **Docs:** `backend/tests/test_demo_combined_postgres.py` (docstring lines 3 and 9 only), `backend/TESTING.md` (327-328).
- **Tests:** the two new backend files, `backend/tests/test_demo_combined_finish_rows.py`.
- **Packet:** `.agent/review-packet-K8.md`, plus the capture-phase section on `task/DIESEL-K8c-captures`.
- **Not touched:**
  - every K5 file (`refs.py`, `linkRefs`, the fuel pages) except by import;
  - `evidence/overview.py`;
  - the Kisiwa template;
  - `.agent/owner-walkthrough-notes-2026-11-01.md`;
  - `Docs/demo-sprint/implementation-logic-design-proposal.html`.

### 9p.14 Pre-flight (no code first; batch every question in one message)

- (a) `site_overview.serve` serves `KISIWA-001` (§9p.5 item 1).
- (b) Kobo's served CRITICAL `load_label` and Kobo's Foundation LOAD names match `/clinic|health/i`.
- (c) Kisiwa's stored timezone.
- (d) The frontend estate Findings and Portfolio link rendering accepts a `FUEL_FINDING` ref without a K5 file change (READ `linkRefs`/the row link code).
- (e) The sort rule of `stored-composer-modules-v1.json` as its test enforces it.
- (f) Whether the K4a Postgres fixture can be imported as is.
- (g) Name every other non-KIS finish or COH row that hard-codes three Sites or a three-Site count (the Architect's grep found only CO-6:451/453 and `SITE_CODE`). A new one is a stop for a ruling, not a silent edit.

### 9p.15 Stops

- **S-1:** any Kobo, Cold or EV served byte, golden or estate-fake body changes.
- **S-2:** fuel money reaches `select_financial_scope`, `selected_lines`, money groups, `estate_total`, `combined_value`, Financials, or any sum.
- **S-3:** the join needs a second transaction or connection, or a stored-route module beyond the two named.
- **S-4:** the frontend needs a K5 file change for the `FUEL_FINDING` link (pre-flight (d)).
- **S-5:** the legacy overview serves Kisiwa.
- **S-6:** a Kobo load name or label misses R-LOAD.
- **S-7:** a guard rejects a literal (report it; never reword silently).
- **S-8:** K8 code above **1.1**, or K8 total above **1.4**.
- **S-9 (capture phase):** a four-Site re-expectation or COH row fails on the rehearsal DB (§9p.9 procedure).
- **S-10:** Kisiwa's stored timezone is not `Africa/Dar_es_Salaam`.

### 9p.16 Branch, DB, model, size

- **K8 code:** branch `task/DIESEL-K8-estate-four-sites` in `C:\Users\assef\Bineyame\AssetOpsV1-k8` (exists, from main). DBs: `assetops_k8_test` and the producer scratch clone `assetops_k8_audit_kisiwa` only. Never `assetops_demo3_kisiwa_test` for writes, and never `assetops_demo3_full_test`. Opus first build and review. Merge on review ACCEPT.
- **K8 capture phase:** `task/DIESEL-K8c-captures`, after K9's rehearsal prepare, read-only `serve` on K9's rehearsal DB.
- **Size: K8 = 1.2** (range 1.1–1.35), against the card's 1.0. That is +0.2: the estate join is larger than §9l.4's +0.15 (consequence gates, Portfolio Action column, module list), plus the re-expectation self-tests and the device-copy rules. The increase is reported, not absorbed.
  - **K8 code 0.95:** estate join, store and composition 0.3; Portfolio label and placement 0.05; tests (L0 and Postgres) 0.25; re-expectations and self-tests 0.14; device copy 0.1; docs 0.02; clone captures (a) 0.09.
  - **K8 capture phase 0.25.**
  - **Template v2 is ruled out, so +0.**
  - **Kisiwa total +0.2.**

### 9p.17 Critical path, tripwire, date

- **Spent through K7-F:** 3.65 → K4a 1.6 → K6a 0.6 → K6b 1.4 → K7-F 0.65 = **7.9**.
- **K8 code is now on the path.** It waited for K4b's fix round (R3j3), and K9's rehearsal needs it on main. Remaining:
  - K8 code 0.95, **in parallel with K9's pre-rehearsal work** (wording guard, KIS-1/2/6/7 rows, COH-17/V4 and §9p.7 items 5–6, about 0.6 of K9's 1.0);
  - then K9's rehearsal (machine time, 2.0–2.35 h, outside lane-units);
  - then K9's remaining ~0.4 beside the K8 capture phase 0.25.
- **Path ≈ 7.9 + 0.95 + 0.4 = 9.25** if the captures overlap K9's reading, **≈ 9.5** if they run after it. **Headroom 0.25–0.5 to the 9.75 tripwire. Not crossed. No cut.**
- **Condition (coordinator):** K9's card and build must start **now** on another lane, beside K8 code. If K9 waits for K8 to merge, the path is 7.9 + 0.95 + 1.0 + 0.25 ≈ **10.1**, which crosses the tripwire. That then becomes an owner question with these cut options, in order:
  1. the all-26 recapture narrowed to the changed and new pages only (about −0.1);
  2. the device-copy rules of §9p.5 deferred, with Kisiwa's Overview showing Kobo's objective words under a logged MOCK DEVIATION (about −0.1);
  3. the K8 capture phase limited to the four-Site Portfolio and Findings (about −0.1).
- **Demo date:** about +0.05–0.1 working day on R3n's +3.5, so about **+3.6** (range 3.1–5.6).
- **Plan HTML rows (coordinator):**
  - K8 becomes 1.2 ("K8 code 0.95, K8 capture phase 0.25 on K9's rehearsal DB");
  - the lanes figure shows K8 code beside K9's pre-rehearsal work, then the rehearsal, then the K8 capture phase;
  - the rulings table gains "DIESEL-1-R3p: K8 card; fuel Finding joins the estate Finding rows after coverage (never money; R3j2 item 3 met); fuel rows' Action column from thread state; W6 list +2 (`verification_rules`, `finding_text`); Kisiwa no objectives; R-LOAD device copy (Kobo byte-equal); template v2 deferred; CO-6/CH5D1-O1/COH-1 routes/COH-7a re-expected by data; `SITE_CODE` to K9; captures (a) clone + (b) on K9's rehearsal DB (§3.5 keep until captures); K8 1.2; path about 9.25–9.5".

### 9p.18 Lines for K9's card (the coordinator passes these verbatim)

- Keep the rehearsal DB and work folder until the K8 capture phase and the W6 guard CLI are done (amends §3.5). Copy `check.json` to `check-rehearsal.json` before any re-check.
- `SITE_CODE` and `LOCAL_DAY_TZ` gain Kisiwa (`"kisiwa": "KISIWA-001"`, `"Africa/Dar_es_Salaam"`). COH-3/4/5/10/13 then run on Kisiwa boards. COH-10 gains the Kisiwa fuel thread (§9p.7 item 5).
- KIS-6 gains the Assure count line of §9p.3.
- The W6 guard CLI acceptance (R3j3) also expects `unlisted_modules []` with K8's two added modules. A further unlisted, clock-free fuel module is a one-line add, pre-authorised after `test_ch5c2_clock_guard.py` passes.
- A failing re-expected row is reported, never edited (§9p.9).

### 9p.19 Owner questions

None (conditional on §9p.17's parallel start). For the owner's information, in plain words:
- The unexplained-fuel finding now appears in the estate-wide finding lists and the portfolio table. Its money is shown only on its own row and is never added to any other figure.
- Kisiwa's overview now names its own loads: households, the cold store and the water pump, not a clinic and a mill. Kobo's pages are unchanged.
- Kisiwa declares no targets for the demo, and the screens say so.
- The work grows by about 0.2 unit. The demo date moves by about a tenth of a working day, provided the final check-and-rehearsal step starts now, alongside this work.

## 9q. Ruling DIESEL-1-R3q — K9 pre-rehearsal answers (Q1–Q5)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md` 2026-10-27). Read-only code reading in `AssetOpsV1-k9` (`task/DIESEL-K9-checks-rehearsal`, after 319236613) and main 6913b3454. No DB, no suites. This ruling amends §9p.7 items 2 and 6 and §9p.18 where they differ.

### 9q.1 Q1: Kisiwa board collection. The builder's proposal is confirmed, with the exact form below

**What the code does (READ).** `SITE_CODE` alone collects nothing for Kisiwa. `day_windows(days)` (`T/checks/chain_coherence.py:72`) iterates `days.json`, and `resolve_story` builds that file from `CORE_SITES` only (`T/demo_combined.py:166`). Kisiwa's calendar lives in `story["kisiwa"]`, and `date=` is sent only for Kobo (`:92`). §9p.7 item 6's sentence "extending `SITE_CODE` collects Kisiwa boards" was wrong. This section replaces it.

**Days.** Use exactly the two boards `story_links` opens (`T/demo_combined.py:306-309`), and no others:
- `S−5d`, the morning after the unexplained-fuel night: `(at(story["S"]) − 5 d).date()`;
- `S`: `at(story["S"]).date()`.

The S−6d board (the evening night 4 opens) is **not** collected. Neither story_links nor DS-1 opens it.

**Form.**
```python
SITE_CODE = {"kobo": "KOBO-001", "cold": "COLD-LAB-001", "ev": "EV-LAB-001", "kisiwa": "KISIWA-001"}
LOCAL_DAY_TZ = {"kobo": "Africa/Addis_Ababa", "cold": "Africa/Addis_Ababa", "kisiwa": "Africa/Dar_es_Salaam"}
#: DIESEL-1-R3q: the Kisiwa boards `demo_combined.story_links` opens (offset from S in days, id kind).
KISIWA_BOARD_DAYS = ((-5, "fuel-morning"), (0, "S"))

def kisiwa_day_windows(story: dict) -> list[dict[str, Any]]:
    """DIESEL-1-R3q: Kisiwa's board days, from `story["kisiwa"]` (not `days.json`), only when Kisiwa is in
    `story["sites"]`. Each is its Site-local day read by `?date=` (mini board), in `day_windows`' row shape."""
```
- **Gate.** Return `[]` unless `"kisiwa" in (story.get("sites") or [])` and `story.get("kisiwa")`. A three-Site or Kisiwa-less work folder therefore collects exactly what it collects today.
- **Row.** For each `(n, kind)`:
  - `day = (at(story["S"]) + timedelta(days=n)).date()`;
  - `local = datetime.combine(day, time(0), tzinfo=ZoneInfo(LOCAL_DAY_TZ["kisiwa"]))`;
  - `lo, hi` = `local` and `local + 1 d`, both in UTC (Dar es Salaam is UTC+3 with no DST, so `[D−1 21:00Z, D 21:00Z)`);
  - `estate` = `day_windows`' existing enclosing-midnight formula, which gives `[D−1 00:00Z, D+1 00:00Z)`;
  - `id = f"day:kisiwa:{kind}:{day.isoformat()}"`, `site_code = "KISIWA-001"`, `date = day.isoformat()`.
- **`day_windows`** skips `site == "kisiwa"` explicitly (its days come only from the function above). It is otherwise byte-equal for the three core Sites.
- **`collect`:** `days_out = day_windows(days) + kisiwa_day_windows(story)`. The board, `chain_site` and `day_` estate fetches then run unchanged (`date=` for both Kisiwa fetches).
- **`_coh7a_window`:** after the change, the K8 lookup `{**{SITE_CODE[k]: z for k, z in LOCAL_DAY_TZ.items()}, **SUMMARY_SITE_TZ}` maps `KISIWA-001` to the same zone twice. That is harmless.
- **Merge note.** Whichever of K8 and K9 merges second keeps the union:
  - K9's `"kisiwa"` entries in `SITE_CODE` and `LOCAL_DAY_TZ`;
  - K8's `SUMMARY_SITE_TZ` line and lookup, both unchanged (not removed: removal is churn with no effect).

**L0 tests (in `T/checks/test_chain_coherence.py`).**
1. With a story whose `sites` includes `kisiwa`, the two rows equal the `date=` values `story_links` prints for `KISIWA-001` boards on the same story. Call `demo_combined.story_links` with a stub `kisiwa` doc and parse its links. This proves "the boards the presenter opens".
2. The S−5d row's date equals `story["kisiwa"]["runs"][INCIDENT_K − 1]["night_date"] + 1 day`.
3. Without `kisiwa` in `sites`, `kisiwa_day_windows` returns `[]` and `day_windows` output is unchanged.
4. `LOCAL_DAY_TZ["kisiwa"] == demo_combined_kisiwa.ZONE`.

**Which rules then run on Kisiwa boards, and what must hold (READ against `board.py`, `mini.py:492-503`, `:811-827`).** The fuel Finding reaches the board as an ordinary `kind: "FINDING"` issue (`board.py:1105`) only where it is open and its night window meets the board day (`board.py:707`, `mini.py:825`):
- on **S−5d**, night 4's window `[S−6d 15:00Z, S−5d 09:00Z)` meets the local day, so it is a Protect MOVES issue;
- on **S** it does not, so it is not an issue there.

Kisiwa's dispatch Findings appear as issues on both days in the ordinary way.

| Rule | On Kisiwa boards | Expectation |
|---|---|---|
| COH-0 | 2 boards, 2 `chain_site`, 2 × `day_` estate reads | every one 200 |
| COH-3 | **0 Kisiwa pairs, by design** | see exception E1 |
| COH-4 (board half) | the fuel Finding (S−5d) and dispatch Findings are in `day_findings_all` for KISIWA-001 | pass. K8's estate fuel rows use the same intersect rule; the S−5d estate window `[S−6d, S−4d)` contains night 4's window |
| COH-5 | fuel: Protect → RISK, and K8 gives `lens_flags == ["RISK"]`; dispatch: Cost → COST | pass |
| COH-6 | Kisiwa shows no opportunity | vacuous, pass |
| COH-10 | Portfolio leg: the `kisiwa-fuel` thread (853fc207d), occurrence 1 of 1 in week and month (not in S, which does not contain night 4; "observed" needs one window). Board leg: the S−5d ref thread equals the Portfolio thread in week and month (both contain the S−5d window) | pass |
| COH-13 | S−5d board state (before the verdict) against the Portfolio state (`RESOLVED_MONITORING` if VERIFIED, effective on the evaluate day) | pass through the "hi took effect later" branch. Time-zone free |
| COH-14 | S: the Protect row may carry the fuel thread's MONITORING thread line with no MOVES Finding | pass: no Protect outcome is NEEDS_ATTENTION / PRIMARY_FINDING_OPEN on S |
| COH-17 (day leg) | `day_chain_estate` against `day_findings_all` on both Kisiwa day windows | pass (one computation) |

- **No countdown, multi-night window: no exception needed.**
  - No rule reads the countdown. R3j2 §9j2.4 `close_measured: False` changes only the line copy, and COH-14 keys on `thread_lines[].kind`, not on a countdown.
  - The multi-night window is judged per board, and only S−5d shows it.
- **Exception E1 (COH-3, named).** The fuel Action is a `FUEL_BALANCE` **domain** Action. It is absent from `/api/estate/actions` (mini `actions.site_window_on`, `postgres_estate_read.py:330`), and Kisiwa is not in `DOMAIN_SITES`, so `_actions` never yields it. Kisiwa's dispatch Findings have no Action. COH-3 therefore evaluates 0 Kisiwa pairs.
  - **Not extended.** Adding Kisiwa to `DOMAIN_SITES` also switches COH-2/8/11 onto a domain-Action row shape never proven on a mini Site. That is new scope with no demo beat (owner 2026-11-05).
  - The Finding → Action link is proven by KIS-10 (thread link) and KIS-9 (e).
  - The packet states "COH-3 Kisiwa pairs: 0 (R3q E1)". After-the-demo list: "COH-3 for mini-Site domain Actions (Kisiwa fuel)".
- **At the rehearsal:** a Kisiwa COH finding fails F-COH. It is a stop reported with its `check.json` entry (§9p.9), never edited.

### 9q.2 Q2: KIS-6 confirmed as CO-6's pattern. The Optimize no-sum is KIS-7

**Pick.** §8.7 is the row list: KIS-6 holds the counts, KIS-7 holds the Optimize card. §9p.7 item 2's "the no-sum check stays in K9's KIS-6" used the withdrawn §4.3 numbering, so it reads **KIS-7**. §9p.3's Assure line is a count and goes in **KIS-6** (as §9p.18 says).

**KIS-6** (`demo_rows.kis6`, pure; wired after KIS-8a; on a dataset without Kisiwa it raises `KisiwaMissing`, the KIS-4 pattern). It reads the week window `[S−6d, S+1d)`:
1. **Four Sites from data.**
   - Outcome-summary `sites[].site_code`, `/api/estate/chain` `sites[].code` and the Portfolio `objectives` site codes (the list CO-6 reads after K8) each equal `sorted([KOBO, COLD, EV, KISIWA])`.
   - `objective_site_count == 3` is CO-6's and is not repeated here.
2. **Kisiwa's summary cells equal its S board.**
   - `{category: state}` of the summary's KISIWA-001 `rows` equals `{category: state}` of `/api/sites/KISIWA-001/outcome-board?date=<S date>`.
   - The summary entry has `window_basis == "DAY"` and `window.from == iso(demo_rows.site_day_start(S.date(), "Africa/Dar_es_Salaam"))`.
3. **Assure line (§9p.3), with the verdict read from data.**
   - `want = 1 if kisiwa.json["verdict"] == "VERIFIED" else 0`. The verdict is recorded as computed (H, §9m.5) and never forced.
   - The chain `sites` entry for KISIWA-001 has `threads.verified == want`.
   - The Portfolio Assure card `claim.value` equals the chain `counts["count.verified_results"].value`.
   - No Assure value line exists for Kisiwa (H2).
4. **Return** the four code lists, Kisiwa's cells, `want` and the two Assure values.
5. **L0 self-test:** one pass body, plus one fail body for each of items 1–3.

**KIS-7** (`demo_rows.kis7`, pure; wired after KIS-6; `KisiwaMissing` if absent). It reads the S window (CH5D1-O1's).
1. The priced codes, read from each summary Site's cost claim (never typed), are exactly `[KOBO, KISIWA]` in Site order.
2. `card.claim is None`, and `card.value.text == card_text("cost.sites", sites=sites_text(2))`.
3. `demo_rows.never_summed([each priced Site's claim amount_high], bodies) > 0` and finds no sum. The bodies are the S and week outcome-summary bodies and the Portfolio week body.
4. If Kisiwa is not priced on S, the row fails and the failure is reported as a stop. It is never re-expected to the one-Site path.
5. **L0 self-test:** a pass body, plus fail bodies for one priced Site, a present claim and a summed string.

### 9q.3 Q3: KIS-1 sources and expected values

**"As known" means as known now.** Read the Site's Foundation revisions through `PostgresFoundationStore(ctx.url).revisions(tenant_id, site_id)` (`sites/foundation_records.py:269`). Keep only the current-knowledge rows (`superseded_at is None`). The components are in `RevisionRow.content`. Pure logic goes in `demo_rows.kis1(revisions, register, prices)`, and a dataset without Kisiwa raises `KisiwaMissing`.

| Item | Source | Expected |
|---|---|---|
| Site | `site` row `site_code_key = lower('KISIWA-001')` | exists |
| Stop setting, "90 throughout" | the `generator` component's `stop-soc-threshold` in **every** current revision (template `config/site-templates/kisiwa-diesel-hybrid-60kw.yaml:123`, fixture `backend/tests/fixtures/s1/kisiwa-001.yaml:86`) | one value across all revisions: `90`, unit `%`. "Throughout" means no revision changes it: Kisiwa's lever is the Action, not a stop setting (R2). K0's RUN_GUARD_HISTORY already proves every run froze this stored history |
| No-load rate | the `generator` component's `generator-no-load-fuel-rate` and `-basis` in every current revision with `valid_from ≥ kisiwa-register.json["no_load_effective_from"]` | equals `demo_combined_kisiwa.NO_LOAD` (read, never retyped) **and** the §8.7 literal `4.9` `L/h`, `GENERIC_DEFAULT`. No revision in that range lacks it |
| Sensor accuracy | the `fuel-tank` component's `fuel-level-sensor-accuracy` and `-basis` in every current revision with `valid_from ≥ register["roles4_effective_from"]` | equals `ROLES4["component_properties"]["properties"]` (`backend/conversions/kisiwa-001-minigrid-roles-demo-config.json`) **and** the literal `10` `L`, `GENERIC_DEFAULT` |
| Diesel price v1 | `build_trial_comparison_ports(ctx.url).price_selection(t, s, w.window_start, w.window_end, w.window_end)` for each of the 10 stored night windows (KIS-4's call) | every selection is priced with **one** `revision_id`, and its value and currency equal step `v1` of `backend/conversions/demo-diesel-price-publications.json` (`1.25` `USD`, read from the file). No later step was published for Kisiwa |

- **Component lookup.** Look up components by `component_id` (`generator`, `fuel-tank`) in `content`.
- **Content keys.** The builder confirms the content key path on the in-memory store from `register_in`, in the L0 test. If the path is not `components[].properties[]`, that is a one-line adaptation, not a stop.
- **L0 self-test:** a pass body, plus fail bodies for stop 60 in one revision, no-load 3.3, a missing accuracy basis and two price revisions.

### 9q.4 Q4: KIS-2 is the fuel-cost-2 formula over the stored power intervals, with exact equality

**Stored columns (READ).**
- `financial_consequence_revision` (0011 + 0053): `finding_id`, `finding_revision_id`, `revision_no`, `recorded_at`, `model_id`, `state`, `sfc_upper_multiplier`, `quantity_high_exact` (`n/d` text), `quantity_high` (ceiling Decimal), `no_load_fuel_rate_l_per_h`, `no_load_fuel_rate_basis`, `idle_seconds`.
- The "segments" are its `financial_consequence_power_interval` rows (`consequence_revision_id`, `mean_kw`, `duration_seconds`, `sfc_l_per_kwh`; written at `postgres_consequence_store.py:249-259`).

Kobo's `idle_morning` covers only the idle term, so KIS-2 needs its own function.

**Selection.**
- Kisiwa's dispatch Findings are `finding_revision` rows on KISIWA-001 in the dispatch domain. Bind the same backend constant the R3k filter binds, never a retyped literal.
- For each Finding, take the latest revision (`revision_no` DESC) and its head consequence: the Kobo `_consequence_heads` ordering, with the Site as a parameter.
- **At least one** Finding is required.

**Per Finding** (`demo_rows.kis2(heads, intervals_by_head, latest_revisions)`, pure, exact `Fraction`):
1. The latest Finding revision is `SUPPORTED`, and the head consequence cites it (`finding_revision_id`).
2. `model_id == "fuel-cost-2"`, `state == "PRICED"`, and `Decimal(sfc_upper_multiplier) == fuel_cost_v2.MULTIPLIER`.
3. `no_load_fuel_rate_l_per_h == 4.9` and its basis is `GENERIC_DEFAULT`. These equal KIS-1's Foundation value.
4. The computation:
   ```
   loaded = Σ_{mean_kw > 0}  F(mean_kw) × F(duration_seconds, 3600) × F(sfc_l_per_kwh)
   idle   = Σ_{mean_kw == 0} F(duration_seconds, 3600) × F(no_load_fuel_rate_l_per_h)
   exact  = F(sfc_upper_multiplier) × (loaded + idle)
   ```
   Here `F(x) = Fraction(str(x))`, which is exact for stored numerics.
5. **Tolerance zero:**
   - `exact == Fraction(quantity_high_exact)`;
   - `Decimal(quantity_high) == fuel_cost.to_decimal_ceiling(exact)` (import it, never re-implement it);
   - `idle_seconds == Σ duration_seconds over mean_kw == 0`.
6. Kisiwa has 0 idle minutes (§9d.6), so `idle` is 0 on the real data. That is **reported** (`idle_seconds` printed per Finding) and not asserted. The idle term is exercised by the self-test.
7. A non-SUPPORTED latest revision, or a non-PRICED head, fails the row and is reported as a stop. It is never forced.

**L0 self-test:**
- one pass body with one loaded and one idle interval;
- fail bodies for: a ×1.00 multiplier, a dropped idle interval, `quantity_high` rounded half-up instead of ceiling, `fuel-cost-1`, and `UNPRICED`.

### 9q.5 Q5: COH-17 and V4 confirmed

- The collector fetches `board_summary.{w}.{code}` for every summary Site (`chain_coherence.py:186-191`).
- `_coh17_full` iterates `chain["sites"]` (`:1395-1420`). V1–V3 run for every Site and window. V4 runs on the S window for every mini Site, so Kisiwa is included with no code change.
- K9's part is **self-tests only**, in `test_chain_coherence.py`, on a four-Site fixture bundle:
  - Kisiwa V4 passes when the nodes are equal and fails (`site_code == "KISIWA-001"`) when one node differs;
  - one C2/V2 pass and fail case on the Kisiwa entry.
- **Rehearsal evidence:** the packet quotes the `board_summary.S.KISIWA-001` request at status 200. That shows V4 actually compared Kisiwa: the Site-set guard at `:1368` did not skip the window.

### 9q.6 Files (added to K9's list)

- `T/checks/chain_coherence.py`: §9q.1.
- `T/checks/test_chain_coherence.py`: the §9q.1 tests and the §9q.5 self-tests, with fixture bundle(s) under `T/checks/fixtures/chain_coherence/bundles/`.
- `T/demo_combined_rows.py`: `kis1`, `kis2`, `kis6`, `kis7`.
- `T/demo_combined_finish.py`: the four rows, wired after KIS-8a in the order KIS-1, KIS-2, KIS-6, KIS-7.
- The existing row self-test file for the L0 bodies.

### 9q.7 Size, path, tripwire

- **K9 stays 1.0.** The answers match the builder's proposals, apart from these additions:
  - the E1 note;
  - the conditional `want` in KIS-6;
  - KIS-1's per-window price read;
  - KIS-2's interval read.

  Each is within its estimate. The pre-rehearsal work is about 0.25 spent plus 0.3–0.35, so **0.55–0.6, inside the 0.6 budget**.
- **Watch item.** If pre-rehearsal work passes 0.7, the builder reports before the rehearsal. The first lever is moving the KIS-7 Portfolio body out of `never_summed` (−0.02). No row is dropped.
- **Critical path unchanged: about 9.25 (captures overlapping K9's reading) to 9.5,** against the 9.75 tripwire. Not crossed, no cut.
- **Plan HTML (coordinator):** the rulings table gains "DIESEL-1-R3q: K9 pre-rehearsal answers; Kisiwa boards S−5d and S collected from `story.kisiwa` (`date=`, Site-local), COH-0/4/5/6/10/13/14/17 on them, COH-3 0 Kisiwa pairs by design (E1, domain Action); KIS-6 counts + Assure (verdict-conditional), KIS-7 Optimize no-sum; KIS-1 Foundation as known now (stop 90 every revision, 4.9 L/h, 10 L, price v1 1.25 USD); KIS-2 fuel-cost-2 over stored power intervals, exact; COH-17/V4 self-tests only; K9 1.0; path 9.25–9.5".

### 9q.8 Owner questions

None.

