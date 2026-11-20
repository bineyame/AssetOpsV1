# Build sheet CH-5a: ChainReader, the chain endpoints and the single routeFor — split into CH-5a1 and CH-5a2

- Architect: Claude, 2026-11-04 (`.ai/ROLE_CONFIG.md` "Architect Is Claude By Default"). Rulings are logged in the plan as **CH5a-R**.
- Plan: `Docs/demo-sprint/client-demo-plan.html` §2.1 CH-5a row, §2.3 DS-R1, §2.4 OL-1, §4 ladder, EX-3, QW-R; CH0-R, CH2-R, CH3-R carried items.
- Design: `implementation-logic-design-proposal.html`:
  - §5.1 (ChainReader replaces the joins at `board.py` refresh/linked, `estate/portfolio.py` `_action_for` and `estate/index.py`);
  - §6 S3, §7 (endpoints, `outcome-chain-1`), §8 (routeFor);
  - §11b (measured QW-1 diagnosis; budgets), §13 (structural guard), §14 D5.
- Register: I-03, I-08, I-21, I-23, plus the carried COH-8/I-01 progress rule and I-25 (part).
- Paths: `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`. Lines are to main `da5b18391`. CH-1b (0044) is merged before CH-5a1 starts.

# Part A — CH-5a1: ChainReader and the board read path (lane 1, 6 units)

- **MD0-S2 (2026-11-04):** the branch may be cut now. Kobo-only MD-0 must merge before review, and its L2m/L3m cases then run on Kobo only. Cold and EV run on the polish clone, and the E1 MD-0 lines for GAP-C3, GAP-E2 and EV are void.
- Branch: `task/CH-5a1-chain-reader`, originally cut from main **after MD-0 merges** (MD-0 itself follows CH-4 and CH-1b; CH1b-R2 item 4, MD0-R). The pre-flight may run earlier, read-only.
- **Two datasets** (BASE-1): every A/B, coherence and perf check runs on the settled polish clone (L3, the gap paths) **and** on the mechanism dataset (`.agent/build-sheet-MD-0.md`: L2m `mechanism_db()`, L3m `assetops_mechanism_test`, the normal path). Update 2026-11-04 (Architect 3): this card folds in MD-0, DD0-R and CH1b-R2.

## A0. Result and boundary

**Observable result.**
- `/outcome-board` (all three Site types) and `/estate/outcome-summary` make **no call** to `mini_overview`, `finding_index` or `evidence_readiness` (`estate.site_readiness*`). The per-request read ledger shows each of those names 0 times.
- **No same-argument read runs twice in one request.** The ledger asserts a maximum of 1 per key for the board, the summary and the Portfolio.
- **Board text is unchanged** except the enumerated changes E1–E5 (§A6). An A/B diff proves it for every Site × story day in `days.json` on the L3 clone, and for every Site-day of MD-0 (`var/mechanism/days.json`) on L3m.
- **Measured timings** (5 cold, 5 warm, in process) are reported against the §11b budgets and the QW-1 baseline. The budgets are not expected to be met here; see §A7.

**Not in this slice.**
- New endpoints, refs, routeFor, lens, progress rows, structured lines and the estate read on the board (CH-5a2).
- The Portfolio evidence selection and money reads (CH-5c, sized by R3).
- No change to any detector, matcher, money model, verification rule, lifecycle rule or copy literal, except E1–E5. Any such change is High.

## A2. Module layout

- **`B/chain/read.py` (pure):**
  - `ChainReader(ports)`;
  - `ChainRequest`, one per route request, built by `reader.request(tenant_id, known_at)` inside the `ReadScope`; it holds `k` and the ports;
  - `site_cutoff`, `readiness_of`, `day_settled`;
  - frozen dataclasses `DayFacts`, `FindingHead`, `ActionFacts`, `MoneyHead`.
  - It imports no store, driver or other domain's adapter.
- **`B/chain/adapters/postgres_chain_read.py`** (registered `$pgReaders`, SELECT only): the SQL of §A3.
- **`B/read_scope.py`:** `ReadScope`, `ledger()`, `memo(name, fn, *args)`, `freeze(value)`. `perf.route` enters it, and `Reads.call`/`pages` (`B/site_outcomes/mini.py:214-250`) record into its ledger.
- **`B/chain/composition.py`:** `build_chain_reader(database_url, consequences=…)`. `B/site_outcomes/composition.py:60-73` passes it to `SiteOutcomePorts` as `chain_reader`, beside `threads`.

## A3. ChainReader ports (each one indexed query, memoised per request)

| Method | Returns | Source |
|---|---|---|
| `day(site, d)` | `DayFacts(local_day, grades: {measure: {subject_ref: grade}}, settled: bool, readiness: str, gaps: tuple[date,…])` | `SnapshotReader.latest(tenant, site, d0, d1, measures_for(site_type), known_at=k)` (`B/chain/reader.py:90`); one call per (Site, day range), and the board asks for its requested days at once |
| `findings(site, lo, hi)` | `tuple[FindingHead(finding_id, revision_id, revision_no, lifecycle, transition, episode_start, episode_end, mechanism, subject_ref, title)]` | Thread occurrences joined to the Finding head at `k` (SQL below). Head rule = the finding index's (P3, CH5a1-R Q6): merged-away Findings excluded, the Site type's domain and analytic only, ordered `episode_start DESC, finding_id`. Visibility `coalesce(source_known_at, joined_at) <= k`. Episode intersects `[lo, hi)`. **`links.selected_revision` is not a column** (CH5a1-R C4): the index builds it as `f"{base}?revision_id={rid}"` (`B/analytics/finding_index.py:443`). The board builds it from `(site code, finding_id, revision_id)` through that same `base` construction, moved to one shared helper and imported by both, never a second f-string. |
| `findings_settled(site)` | bool | R8 |
| `action_facts(site, action_ids)` | `tuple[ActionFacts(action_id, verification_state, cost_check, trial_hours, has_change)]` | **Corrected (CH5a1-R C6, Q7).** `verification_state`, `cost_check` and `trial_hours` come from **one** `VerificationService.summary(t, s, code, aid)` per Action (`B/actions/verification.py:1043-1080`), the call the board makes today (`mini.py:687`), memoised in the read scope. They are never re-derived in SQL: `current_state` (`:948-`) also produces PENDING from the clock and REASSESSMENT_PENDING from late evidence and moved S3/S4 bases, which a "latest outcome" SQL would lose. `trial_hours` keeps today's shape `{before_seconds, after_seconds, later_start, later_end}` (stored `candidate_avoidable_seconds` metrics plus the plan's later window), and `mini._trial_hours` still adds `later_local`. `has_change` is one SQL over all ids (`EXISTS action_policy_change`), replacing the `action` detail call (`mini.py:688`); an L2 parity test proves it equals `bool(detail.change)` for each seeded Action. The ledger shows one `action_read` per Action, not two. |
| `money_head(site, finding_id, revision_id)` | `MoneyHead(priced: bool, amount_low, amount_high, currency, source_provenance)` or None | One `consequences.read(t, s, fid, rid, finding_revision_is_latest=…, source_open=…, limit=1)`, the service the overview called (`B/site_overview/read.py:296-297`), on the instance `site_overview.upstream.consequence_read` (P6; ChainReader never disposes it). The lead Finding is chosen as `_money` chooses it (discovered head, else pinned, `site_overview/read.py:287-295`) over the `findings()` rows, and `finding_revision_is_latest` is computed from those rows (CH5a1-R Q5). `priced` = `money_eligibility.state == "ELIGIBLE"` and `currentness.current_amount_shown` and the display amounts are present and the day is settled (R4). The board uses only priced, zero and amounts (`mini.py:453-465`), and the source state at `:949`. Measured at about 0.66 s warm (pre-flight §3); its dispatch reads share the R1 `_window` memo key. |
| `threads(...)` | the existing `thread_lookup` result | `LOOKUP` (`B/chain/lookup.py:18-40`), fixed for **L5**: the occurrence count `cnt` and the 'F' rows count only occurrences with `coalesce(source_known_at, joined_at) <= :k` (today `:28-29` counts all occurrences). This is CH2-R L5: occurrence counts never include later occurrences. The view also returns `applied: bool`, `verified: bool` and `later: bool` per Finding, so `board.py` needs no state tuples (§A5). |

**The Finding head SQL** (corrected by CH5a1-R Q6 to the index's head rule, pre-flight P3):

```sql
SELECT o.thread_id, o.occurrence_no, f.id AS finding_id, r.id AS revision_id, r.revision_no, r.lifecycle, r.transition,
       r.episode_start, r.episode_end, f.mechanism, t.subject_ref
  FROM finding_thread_occurrence o
  JOIN finding_thread t ON t.id = o.thread_id
  JOIN finding f ON f.tenant_id = o.tenant_id AND f.site_id = o.site_id AND f.id = o.finding_id
  JOIN LATERAL (SELECT * FROM finding_revision x WHERE x.tenant_id = f.tenant_id AND x.site_id = f.site_id
                AND x.finding_id = f.id AND (CAST(:k AS timestamptz) IS NULL OR x.created_at <= CAST(:k AS timestamptz))
                ORDER BY x.revision_no DESC LIMIT 1) r ON true
 WHERE o.tenant_id = :t AND o.site_id = :s AND o.finding_id IS NOT NULL
   AND f.domain = :domain AND f.analytic_id = :analytic          -- the index's scope (Kobo: mini_grid / dispatch)
   AND NOT EXISTS (SELECT 1 FROM finding_merge m                  -- finding_index.py:300, merged_into IS NULL
                    WHERE m.superseded_finding_id = f.id
                      AND (CAST(:k AS timestamptz) IS NULL OR m.created_at <= CAST(:k AS timestamptz)))
   AND (CAST(:k AS timestamptz) IS NULL OR coalesce(o.source_known_at, o.joined_at) <= CAST(:k AS timestamptz))
   AND r.episode_start < :hi AND (r.episode_end IS NULL OR r.episode_end > :lo)
 ORDER BY r.episode_start DESC, f.id                              -- finding_index.py:233-235 sort_key
```

- Column names (`f.domain`, `f.analytic_id`, `finding_merge` keys) are confirmed against `postgres_finding_store.py:478-550` in the build; a different name is a build fact, not a change of rule.
- A NO_LONGER_SUPPORTED or other lifecycle head is listed as its own row, as the index does. A merge target is listed as its own head.
- **No occurrence, no row.** A Finding the index lists but no thread occurrence holds would silently drop off the board. The A/B assertion of equal `(finding_id, revision_id)` sets per board, on both datasets, is the gate; a difference is a regression, never an allowed change.

- Run `EXPLAIN (ANALYZE, BUFFERS)` on the clone for the Kobo work window and report it in the packet.
- If any statement here exceeds 50 ms on the clone, report the plan. The Architect rules on an index migration (`0046`); nothing is added unasked.

## A4. The board inputs, field by field (mini `compose`, `B/site_outcomes/mini.py:371-500`)

| Board input | Today | CH-5a1 |
|---|---|---|
| `base` (`:412-415`) | overview present, freshness CURRENT, assessment not CLOSED | **Corrected (CH5a1-R Q2):** `base = source_open and day.settled and dispatch is not None`. The dispatch body has no `state` and no CLOSED: CLOSED came only from the overview's source gate (`site_overview/read.py:349-352`), which is `source_open` itself (`ports.overview_source`, `read.py:93`). The overview's UNASSESSED → UNKNOWN (`site_overview/read.py:362`) moves to `chain/read.py` as a pure map over `dispatch.status`. |
| `assessment.limitations`, `claim_level`, `dispatch_intervals` (`:423`, `no_run_day` `:908-913`) | overview `_assessment` (`B/site_overview/read.py:347-379`) | The `dispatch` read already made (`mini.py:388`): top-level `limitations` (`dispatch_read.py:173`), `window_assessment.claim_level`, `intervals`. Same sources as the overview (P2). No by-id read is needed. |
| `money` (`:453-465`), source state (`:949`) | overview `_money` | `money_head(lead Finding)` (§A3, CH5a1-R Q5) |
| `readiness` (`:389`; MG-7 settled `:419`; `rc` `:434-442`) | `estate.site_readiness` (the Portfolio evidence selection) | `readiness_of((D,))` (R5) |
| `finding_rows`, `findings_ok` (`:391-396`), `finding_gaps` (`:496`) | `finding_index` pages | `findings(site, work_lo, end)`, `findings_settled`, `day.gaps` (R8). `day(site, …)` for the gap line covers **every** Site-local day of the 31-day work window, missing rows as NO_DATA (CH5a1-R Q9). The index's PARTIAL-mode withholding (`finding_index.py:323-334`) is not reproduced (CH5a1-R Q4). |
| `_lineage` (`:640-667`), `finding_history` reads | refresh-chain lineage | **Deleted.** An Action belongs to a Finding through its thread and segment (CH-2/CH-3). `refresh_chain` (`board.py:534`) and `linked_actions` (`:567`) are deleted with their tests rewritten to the thread join. |
| `action_read` × 2 per Action (`:687-688`) | verification summary and action detail | `action_facts(site, ids)` (§A3) |
| `estate` `site_work_rows` (`:390`) | estate snapshot (labels, confidence) | **Kept in CH-5a1** (one call, ledger max 1); CH-5a2 B3 replaces it |
| `dispatch`, `mini_depth` × 4, `assumptions`, `plans`, `work_index`, `objectives`, `productive_*` | as today | Kept; ledger and memo apply. **Labelled keep → CH-6/CH-7** (nodes and adapters) |

- **Cold and EV** (`B/site_outcomes/cold.py:108-117`, `ev.py:124-133`): `evidence_readiness` → `readiness_of` over every Site-local day the window intersects, rows pooled (CH5a1-R Q8). Everything else is kept: their Finding bodies carry the claims the contributors use (`cold.py:224-227`). **Labelled keep → CH-7** (adapters).
- The `Reads` failure semantics are unchanged: a ChainReader port that raises is a failed read. It leaves the board PARTIAL (`mini.py:7`), never the route's error.

## A5. Deletions and moves in this slice

- `B/site_outcomes/board.py:72-74, 656` (anchors per the pre-flight §6: `THREAD_WIRE_KEYS` is `:74`, `THREAD_LATER_STATES` is `:656`): `THREAD_APPLIED_STATES`, `THREAD_VERIFIED_STATES` and `THREAD_LATER_STATES` are deleted, with the CH3-R equality test (`backend/tests/test_ch3_rows.py:22-23,184-186`). The board reads `applied`, `verified` and `later` from the thread view (§A3). `THREAD_WIRE_KEYS` is replaced by `lookup.PUBLIC_KEYS`, passed in through the view (the board imports only `outcomes/`, so the keys come with the data).
- `refresh_chain`, `linked_actions` and `_lineage`, as §A4.
- `mini_summary_day` (`read.py:158`) is replaced by the R6 rule. `latest_window` (`:168`) stays (cold/EV event window): **labelled keep → CH-6** (A6 composition).

## A6. Acceptance: the A/B diff and its allowed changes

- On one settled L3 clone **and on L3m** (`assetops_mechanism_test`, then `--variant close`), collect every board in that dataset's `days.json` (all Sites, all days, via `?date=` / window as the screen calls them), the summary and the Portfolio (week, S, month), twice:
  - **A** with main at the MD-0 merge, in a separate read-only worktree, as CH3-R's A/B;
  - **B** with this branch.
- Normalise `window.known_at`, `selection_token` and `links.self` (QW packet `:45`), then diff.
- **Same windows on both sides.** Both A and B are collected with the B side's `days.json` windows (after the CH5a1-R Q8 local-day change), so a window change is never mistaken for a board change.
- **Allowed differences, each listed in the packet as old → new with its Site and day:**
  - **E1.** The readiness chip and MG-7 text follow `readiness_of`. Expected on the polish clone (pre-flight §4): Kobo 17, 24, 31 Oct "High" → "Limited" and Kobo 1 Nov UNKNOWN → "Limited", because 8 of 24 h are covered (CH-1a §5c); Kobo 3, 10, 28, 30 Oct and Cold 24, 28, 31 Oct unchanged; **EV 20 and 27 Oct "Limited" → "Low"** (LOW day grades; the ASSURE headline is unchanged because `ev.py:224` treats LIMITED and NONE alike; CH5a1-R Q11). Grades on a fresh 0044 clone may differ after CH1b-R Q1 attribution; L3 re-reads them and the packet lists what it finds. Expected on MD-0:
    - every normal day reads FULL;
    - GAP-K7 (Kobo D7) reads NONE (NO_DATA);
    - GAP-C3 (Cold D3) reads LIMITED (PARTIAL);
    - GAP-E2 (EV D2) reads UNKNOWN (PENDING);
    - EV non-Tuesdays have no expected row, so UNKNOWN. That is the R5 rule as written; the packet lists the EV non-Tuesday boards, and the Architect rules whether a non-operating day should read differently. Not changed here.
  - **E2.** A row or Finding that read Unknown only because of overview freshness now reads from settled snapshots.
  - **E3.** `finding_gaps` names the days by day grade (R8). **E3b (CH5a1-R Q4):** a Finding the index withheld in PARTIAL mode now appears, with the gap days still named. Expected empty on both datasets; if it is not empty, list each case and stop for an Architect ruling before merge.
  - **E4.** Window bounds in `window`, the self link and in-window tests follow the Site-local day (R6).
  - **E5.** Occurrence counts and thread lines honour `known_at` (L5). Expected: no change at the latest cutoff.
- **Any other difference is a regression** (High). Fix it, or bring it to the Architect with the evidence.

## A7. Performance (EX-3: report, never relax)

- **`tools/chain_perf_probe.py`** (new; report only, no pass/fail; CH-5b turns it into `perf_budget.py`):
  - in process on a settled clone, 5 cold and 5 warm runs per URL;
  - URLs: Kobo board `?date=2026-10-31`; the Cold failure-night board; the EV 27 Oct board; the summary and the Portfolio for the story week;
  - run once on the clone and once on L3m. MD-0 dates fall on the same calendar days (S = 31 Oct, Cold failure D13 = 31 Oct, EV D9 = 27 Oct), so the URLs are the same. The MD-0 run gives normal-data payload sizes and full-outbox query costs;
  - it prints the median, min and max per URL, the body size in bytes, and the top 10 ledger names by ms.
- **Report** beside the QW-1 baseline (design §11b table) and the budgets: ≤ 1 s cold and ≤ 300 ms p95 warm; payloads ≤ 60 KB (board) and ≤ 100 KB (Portfolio).
- **Expected honestly:** the board loses about 6 s (overview 2.8, index 2.0, readiness 1.25) and the repeated window reads. It stays above 300 ms warm while `mini_depth`, `estate` and `dispatch` remain.
- **No budget is relaxed.** The residual goes into the CH-5a2/CH-5c/CH-5b sequence, and the Architect brings a measured proposal to the owner before E1 if the budget still misses after CH-5c (EX-3).

## A9. Localised test ladder

1. **L0:** `tools\run-host-tests.ps1 -- backend/tests/test_ch5a1_reader.py backend/tests/test_ch5a1_scope.py`
   - `site_cutoff` truth table (mini, cold, EV; with and without a request cutoff).
   - `readiness_of` truth table (each grade mix, including PENDING and NOT_EXPECTED only).
   - `day_settled`; R8 gap days.
   - `ReadScope`:
     - memo hit on equal keys, and `knowledge_at` excluded only when the cutoff is None;
     - a raising call is not memoised;
     - a mutable dict result is frozen;
     - outside a scope: no memo;
     - the ledger counts.
   - The R6 local day in Addis and in UTC; `to − 1 µs` across midnight.
   - The `thread_lookup` L5 count at `k` before the third occurrence.
2. **L1:** `backend/tests/test_ch5a1_board_contract.py`
   - The board composed from a fixture ChainReader equals the stored golden board JSON for Kobo 31 Oct and 1 Nov, Cold 31 Oct and EV 27 Oct. The goldens are taken once from the A side, with E1–E5 applied and listed.
   - A fixture ledger proves 0 calls of the three names.
3. **L2 and L2m:** `tools\run-host-tests.ps1 -- backend/tests/test_ch5a1_reader_postgres.py`, on `pg_harness.fresh_database()` plus `setup_cache` (head via `pg_harness.alembic_head()`), seeded as CH-2/CH-3 L2. **Plus L2m cases on `mechanism_db()`:**
   - every §A3 port over the full 14-day Kobo, Cold and EV Sites;
   - `readiness_of` per MD-0 day equals the E1 MD-0 list;
   - R8: Findings settled after the seed. After `late_fill(KOBO-001, D7)` and before its consume, they are not settled for KOBO-001. After the consume they are settled again;
   - the board route ledger maximum is 1 on Kobo D13, Cold D13 and EV D9.
   - Every §A3 SQL returns the expected rows.
   - `known_at` hides a later revision, occurrence and selection.
   - The board route under TestClient has a ledger maximum of 1, and none of the three names.
4. **Existing, scoped** (list every importer of `site_outcomes.*`, `chain.lookup`, `perf` and `estate.index` in the packet):
   - `test_out_b1_board.py`, `test_out_b2_mini.py`, `test_out_b3_cold_ev.py`;
   - `test_out_b4_board_postgres.py`, `test_out_b4_read.py`, `test_out_b4_route.py`, `test_out_b4_window.py`;
   - `test_qw1_perf.py`, `test_qw2_reuse.py`, `test_qw2_many_postgres.py`;
   - `test_ch2_*.py`, `test_ch3_*.py`;
   - `test_w301_estate_api.py`, `test_w303_portfolio_api.py`;
   - `test_polish_pa1_board_truth.py`, `test_out_d4_board.py`;
   - `tools/checks/test_chain_coherence.py`.
5. **L3:**
   - `python tools/chain_clone.py create ch5a1 --migrate`;
   - `python -m assetops_backend.chain.backfill --steps a,b,c,d`;
   - `python tools/chain_clone.py settle ch5a1`;
   - the §A6 A/B collect and diff;
   - `chain_coherence.py collect` and `check` with `expected-today.json`: every rule as on main except entries this slice resolves (expected: none; COH-1/5/8 resolve in CH-5a2);
   - `python tools/chain_perf_probe.py --database-url <clone url> --work <scratch copy>`;
   - pre-flight P1's cProfile;
   - `python tools/chain_clone.py drop ch5a1`.
   - **L3m:** `python tools/mechanism_dataset.py build`, then the §A6 A/B on it, then `collect` and `check --threads var/mechanism/expected-threads.json --expect tools/checks/fixtures/chain_coherence/expected-mechanism.json`. Pass: 0 unexpected. Run the perf probe on it, then `drop`. Repeat with `--variant close` for the A/B only.
   - **Collector update:** `_board_query` (`tools/checks/chain_coherence.py:384-394`) canonicalises `date=D` to the body's own `window.from`/`window.to` (R6), not to UTC midnights. `is_own_self_link` (`:397`) is unchanged otherwise. With it, close MD0-R R10: `day_windows` (`chain_coherence.py:67-85`) takes a Kobo **and a Cold** day as its Site-local day, and `backend/tests/mechanism_dataset.py` `build_work` writes Kobo entries as Site-local day bounds (Cold entries are already local days from MD-0, MD0-PF Q4; CH5a1-R Q8). EV (`Etc/UTC`, `[d 08:00Z, d 16:00Z)`) is unchanged. All change together in this slice, and `test_chain_coherence.py` gains the Addis case for both.
6. **Frontend:** `npx vitest related --run src/sites/outcomeBoardClient.ts` (window type unchanged; only the bounds move).
7. **Guards:** A, W, the chain-coherence fixtures line. Run the estate guard self-tests because P4 registers a new reader in `configuration-persistence.ps1` (plan §4.3 rule).

## A11. Review focus

- Zero calls of the three reads. The ledger maximum is 1. The memo returns only frozen values.
- Every board difference is in E1–E5.
- No re-derived join, window, day count or card rule outside `B/chain/`. Re-derivation is High (design §13 checklist).
- Budgets are reported, not claimed.

# Part B — CH-5a2: chain endpoints, refs, routeFor and the carried chain items (lane 1, 6 units)

- Branch: `task/CH-5a2-chain-endpoints`, cut from main after CH-5a1 and CH-4 merge.
- CH-4 provides `outcome_map.lens_flags`/`thread_signal_key`, `B/chain/vocabulary.py`, the opportunity items and their `ref` objects.
- **PC-1 claim type (Architect 5, 2026-11-04).** BASE-1 gives CH-5a2 the PC-1 count claims (the L3m "on the days checked" texts in §B10). This sheet never defined the type. It is defined **once**, in `.agent/build-sheet-CH-6.md` §S.2: `Claim {key, value, basis, days, text}` with `to_json()`, and the single `count_basis(days: GradeCounts | None)` rule, in `B/chain/vocabulary.py`. **Build it exactly as written there**: same names, fields, basis codes, wire shape, and Decimals as strings. No second basis function. CH-6a's pre-flight P3 checks the merged shape against §S.2, and any difference is a finding.
- **Carried from CH5a1-R:** the links CH-5a1 builds from ids through the index's `base` helper (C4) move to `href_for(ref)` here.

## B0. Result and boundary

**Observable result.**
- Three new read endpoints return the chain contract `outcome-chain-1`.
- Every board, Portfolio, estate Findings and estate Actions link the client renders comes from **one** `routeFor(ref)`. **No link contains `/api`**: the 12 COH-1 / I-08 entries resolve.
- Each Finding sits under its one lens (I-21; COH-5 passes with no expected entries).
- Progress rows read from threads (COH-8 passes).
- Board rows carry a structured `thread_lines` field.
- "Verified on example data" appears only where the evidence is example data.
- The board no longer reads the estate snapshot.
- The structural AST guard joins `check-architecture.ps1`.

**Not in this slice.**
- Outcome nodes (earnings, KPI, potential) and the Portfolio from EstateChain (CH-6).
- "Why?", ETag and shared blocks (CH-5b).
- The Portfolio evidence and money reads (CH-5c).
- The one ThreadList on the Site Findings page (CH-5b blocks).

## B1. The contract (`outcome-chain-1`, additive; frontend parsers accept absent fields)

**`GET /api/sites/{code}/chain?from&to&known_at`** (`from`/`to` are Site-local days or UTC instants, at most 31 days; the board's own parsing and refusals, `B/outcome_api.py:102-143`):

```json
{"schema_version": "outcome-chain-1", "site": {"code": "KOBO-001", "tz": "Africa/Addis_Ababa", "domain": "MINIGRID"},
 "window": {"from": "…Z", "to": "…Z", "known_at": "…Z"},
 "days": [{"day": "2026-10-31", "grade": "PARTIAL", "measures": {"productive_kwh": "PARTIAL", "…": "…"}}],
 "outcomes": [{"category": "OPTIMIZE_COST", "state": "NEEDS_ATTENTION", "state_label": "…", "headline": "…",
               "thread_lines": [ … §B4 … ], "refs": [Ref, …]}],
 "threads": [{"id": "…", "mechanism": "GENERATOR_SUPPORT_CANDIDATE", "lens": ["COST"],
              "categories": "<categories_for(thread_signal_key(mechanism), domain)>",
              "state": "RESOLVED_MONITORING", "state_label": "Checked and working, monitoring", "since": "2026-11-01",
              "occurrences": [{"finding_id": "…", "opportunity_id": null, "code": "F-…|OPP-…", "day": "2026-10-17"}],
              "ref": Ref}],
 "actions": [{"id": "…", "code": "ACT-000001", "kind": "MINI_TRIAL", "thread": "…", "segment_no": 1,
              "verification": "VERIFIED", "ref": Ref}],
 "policy_versions": {"coverage": "coverage-policy/1", "register": "event-register/1",
                     "lifecycle": "thread-lifecycle/1", "status": "outcome-status/3"}}
```

- `outcomes` is the board composition's rows: the same `assemble(facts)` output, with `refs` and `thread_lines`. CH-6 adds the node slots.
- The status policy version is the one the board route already names (`POLICY_VERSIONS`); it is not renamed here.

**`GET /api/estate/chain?from&to&known_at`** (estate scope parsing as `/estate/portfolio`):
- `{"schema_version", "window", "sites": [{"code", "domain", "days": GradeCounts.to_json(), "rows": {category: {"state", "state_label"}}, "threads": {"open": n, "in_hand": n, "verified": n}, "opportunities": [CH-4 item]}], "counts": {"verified_results", "open_threads", "opportunities"}, "money_total": null}`.
- Rows come from each Site's board composition on its Site-local day of `to − 1 µs` (CH3-R), read through one ChainRequest. Counts may be summed. Money is never summed across Sites (design A6; CH-6 adds earnings).

**`GET /api/sites/{code}/threads/{thread_id}?known_at`:** the thread, with `occurrences`, `events` (`seq`, `state`, `state_label`, `effective_day`, `cause_kind`) visible at the cutoff, and `actions`. A thread of another Site returns 404 `THREAD_NOT_FOUND`.

**Router.** `B/chain_api.py`, `build_chain_router(reader, registry, …)`, wired in `B/main.py` beside `build_outcome_router` (`:625`), each route inside `perf.route`.

**`Ref`** (`B/chain/refs.py`, mirrored by the TS type in design §8):

```
THREAD {site, id} | FINDING {site, id, revision?, window?: {from, to, known_at}} |
ACTION {site, id, event_id?, view?: "verification"|"plan"|"history"} | OPPORTUNITY {site, id, known_at?} |
CASE {site, id} | EVIDENCE {site, capability?, window?} | SITE {site, view?} | ESTATE {path, query?}
```

- `href_for(ref)` (backend) and `routeFor(ref)` (frontend) produce the same screen path. Each is the only builder on its side.
- **Contract test:** one JSON fixture `frontend/src/shell/__fixtures__/route-refs.json` (ref → expected path) is read by both a vitest and a pytest.
- **I-08:** a cold/EV FINDING ref carries `window` (the proven row-local window and cutoff, `B/estate/evidence_money.py:136-145`). Its path is `/sites/{code}/findings/{id}?from=…&to=…&known_at=…`, the screen route, replacing `/api/sites/{code}/cold|ev/findings/…` at `B/site_outcomes/cold.py:217` and `ev.py:264-266`.

## B2. Refs on the legacy bodies and routeFor on the client

- **Server:** every `href` on the board (issues, contributors, options, in-hand, earlier), on Portfolio rows (`links`), estate Findings rows, estate Actions rows and CH-4 items gains a sibling `ref`. The `href` stays until CH-7 (design §7), and is built by `href_for(ref)`, so it cannot disagree.
- **Client:**
  - `routeFor(r: Ref): string` lives in `F/shell/operatorSiteRoutes.ts`, as an exhaustive `switch` over the existing builders (`siteFindingHref` `:162`, `siteActionHref` `:392`, `siteOpportunityHref` `:208`, `siteEvidenceHref` `:111`, `sitePerformanceHref` `:143`, `siteWorkHref` `:324`, `siteDetailHref` `:45`).
  - The components render `routeFor(ref)` and never a server `href`:
    - `F/sites/OutcomeBoard.tsx` `To` (`:93-95`) takes a `Ref | null`;
    - `F/estate/EstatePortfolio.tsx` row links;
    - `F/estate/findingIndex.tsx` row and item links;
    - the estate Actions list.
  - A body without `ref` falls back to "no link", never to the `href`.
- **Root `links.self`** stays unrendered (CH0-R). CH-5b's hard-wiring guard enforces "no server href rendered".

## B3. The board off the estate snapshot; old joins removed

- The board's `estate` read (`mini.py:390`) feeds `workflow_label` and the confidence chip (`_findings` `:619-638`, `_actions` `:670-700`). It is replaced by ChainReader:
  - `workflow_label` is computed by the **same** function (`B/estate/portfolio.py:201`) over a row ChainReader builds from `chain_action` and its events at `k`;
  - confidence is `placement.place(row, action, site_cov, None).confidence` (`B/estate/placement.py:144-155`) over the light Finding head plus its consequence head state and source provenance state.
  - P1 states the row fields `place` and `workflow_label` read, and their sources.
  - The A/B on the clone must show the chip and label unchanged.
- **`_action_for` exact join** (`B/estate/portfolio.py:173-200`): the `(finding_id, finding_revision_id)` fallback is deleted. An Action without a thread link matches no row (honest "No action agreed yet"), and COH-11 flags it.
- **Portfolio `_cutoff`** (`B/estate/index.py:182-183`): the per-row derivation is replaced by one `ChainRequest.site_cutoff(site)` per Site (R7), passed to `attach_threads` (`portfolio.py:129-163`) as a Site → cutoff map. CH-6 keeps this rule (A6).

## B4. Structured `thread_lines` (replacing copy-only lines)

- Each board row gains `thread_lines: [ThreadLine]`, where `ThreadLine` is:
  ```json
  {"kind": "BEFORE_CHANGE"|"MONITORING"|"CLOSED"|"RECURRED", "thread_id", "action_code",
   "effective_day", "after": {"state", "day"}|null, "remaining_days": int|null, "clean_days": int|null,
   "ref": Ref, "text": "<the CH-3 literal, rendered>"}
  ```
- The CH-3 literals (`B/site_outcomes/board.py:64-70`) are unchanged.
- The row `subline` is built by joining `subline` and the `text` fields with `" · "`, exactly as now, so the screen text is identical.
- COH-13 and COH-14 read the structured field where present (`tools/checks/chain_coherence.py:833-922`).

## B5. Lens from the chain (I-21, COH-5)

- **Estate Findings rows** (`B/estate/index.py:125-128`): `lens_flags = outcome_map.lens_flags(finding_signal_key(mechanism), domain)`, one lens, from the primary moved category (CH4-R R5).
  - The PRICED → COST and `RISK_MECHANISMS` rules (`:27-28`) are deleted. The price stays in the consequence column. This matches the mock: one lens per Finding (`screens.js:175`: F-104 Cost, F-118 Risks, F-130 Risks).
- **Mini Site Finding index rows** (`/api/sites/{code}/finding-index`): add `lens_flags` from the same helper. `F/sites/SiteFindingIndex.tsx:597-600` renders it in the Lens column instead of "Not assessed". The lens chips stay disabled (MOCK DEVIATION D5, until the CH-5b ThreadList).
- **Board FINDING issues** gain `primary: bool` (the row's category is the category of the Finding's `moves[0]`).
- **COH-5** (`tools/checks/chain_coherence.py:503-519`) compares only primary issues. A checked-row or secondary appearance is not a lens.
- **Delete all six COH-5 entries** from `expected-today.json`:
  - the three owned by CH-2 (Cold `:COST`, EV `:OPPORTUNITY`);
  - the three owned by CH-5a (Kobo `:RISK`). Kobo's generator Finding is then under COST.

## B6. Progress rows from threads (COH-8 / I-01)

- `progress()` (`B/estate/portfolio.py:513-540`) adds `origin_selected: bool`: the Action's thread holds, in the Action's segment, a Finding in the selected set (any revision).
- `origin_revision_selected` stays as the exact-revision audit fact (design §3: "the revision is kept for audit").
- COH-8 (`chain_coherence.py:591-616`) reads `origin_selected`. Delete the three COH-8 entries.

## B8. Structural AST guard (design §13)

- **`tools/checks/check_chain_structure.py`**, run from `tools/check-architecture.ps1`. Outside `backend/assetops_backend/chain/`:
  - (a) no module imports both a Finding store or index (`analytics.adapters.postgres_finding_store`, `analytics.finding_index`) and an Action store or index (`actions.*store*`, `actions.site_index`);
  - (b) no call to the replaced day and window functions `{_days_block, _productive_month, mini_summary_day}`, nor a new definition of a function named in the design §5.1 "Replaces" column.
- **Baseline** `tools/checks/fixtures/chain_structure_baseline.json` lists today's violations, each with its owner (CH-6, CH-7). The baseline may only shrink.
- **Self-test:** `tools/checks/test_chain_structure.py`.

## B10. Localised test ladder

1. **L0:** `tools\run-host-tests.ps1 -- backend/tests/test_ch5a2_refs.py backend/tests/test_ch5a2_rows.py`
   - `href_for` on the shared `route-refs.json`.
   - `provenance_suffix`.
   - `lens_flags` on every stored mechanism (the mock's lenses).
   - `origin_selected` truth table (same segment, earlier segment, refreshed revision).
   - `thread_lines` rendering equals today's `subline` for the CH-3 cases.
   - The AST guard's self-test cases.
2. **L1:** `backend/tests/test_ch5a2_contract.py`
   - SiteChain goldens for Kobo 31 Oct and 1 Nov, Cold 31 Oct and EV 27 Oct, and the EstateChain week, taken from the fixture ChainReader. These are the CH-6 and CH-5b starting goldens.
   - The frontend renders them in vitest with no server.
3. **L2:** `tools\run-host-tests.ps1 -- backend/tests/test_ch5a2_chain_api_postgres.py`
   - The three routes under TestClient.
   - Refusals: more than 31 days, a bad `known_at`, a thread of another Site → 404.
   - Ledger maximum 1 for each route.
4. **Existing, scoped:** as Part A item 4, plus:
   - `test_w301_estate_index_postgres.py`, `test_w303_portfolio_reduction.py`, `test_w303_portfolio_fixture_postgres.py`;
   - the mini finding-index tests;
   - `test_s6_action_store_postgres.py`;
   - every importer of `estate.portfolio`, `estate.index`, `estate.placement` and `chain.vocabulary`.
5. **L3:** clone, migrate, backfill a–d, settle; collect and check with `expected-today.json`.
   - Pass: COH-1, COH-5 and COH-8 entries all resolved and removed; COH-1 finds 0 `/api` links; every other rule as before.
   - The B3 A/B: chips and labels unchanged.
   - The B7 assertion.
   - `chain_perf_probe.py` (report vs CH-5a1).
   - Payload sizes of the three new endpoints.
   - Drop.
   - **L3m (MD-0, BASE-1):** build, then collect and `check --threads var/mechanism/expected-threads.json --expect expected-mechanism.json`.
     - Pass: 0 unexpected, including COH-1, COH-5, COH-8 and the new COH-17.
     - The PC-1 "on the days checked" texts appear only in windows containing GAP-K7, GAP-C3 or GAP-E2.
     - Report the payload sizes of the three endpoints on full data. Then drop.
6. **Frontend:**
   - `npx vitest related --run src/shell/operatorSiteRoutes.ts src/sites/OutcomeBoard.tsx src/estate/EstatePortfolio.tsx src/estate/findingIndex.tsx src/sites/SiteFindingIndex.tsx`, which includes `outcomeBoard.test.tsx`, `estatePortfolio.test.tsx` and `s404SiteFindingIndex.test.tsx`;
   - routeFor tests over `route-refs.json`;
   - a body without `ref` renders no link.
7. **Guards:** A (with the new AST guard), W, N, V, M, L, D (plan §4.2), and the chain-coherence fixtures line. The estate guard self-tests run only if a reader registration changes.

## B12. Review focus

- One `routeFor` and one `href_for`, agreeing on the shared fixture. No component renders a server `href`. No `/api` in any rendered link.
- Lens, progress and lines are read from the chain. COH-1, COH-5 and COH-8 pass with no expected entries.
- The new endpoints are views over ChainReader. They contain no join, window or day-count logic of their own.
- No outcome id outside `outcome_map.py` (OL-1).

