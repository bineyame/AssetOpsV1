# Build sheet CH-5a: ChainReader, the chain endpoints and the single routeFor — split into CH-5a1 and CH-5a2

- Architect: Claude, 2026-11-04 (`.ai/ROLE_CONFIG.md` "Architect Is Claude By Default"). Rulings are logged in the plan as **CH5a-R**.
- Plan: `Docs/demo-sprint/client-demo-plan.html` §2.1 CH-5a row, §2.3 DS-R1, §2.4 OL-1, §4 ladder, EX-3, QW-R; CH0-R, CH2-R, CH3-R carried items.
- Design: `implementation-logic-design-proposal.html`:
  - §5.1 (ChainReader replaces the joins at `board.py` refresh/linked, `estate/portfolio.py` `_action_for` and `estate/index.py`);
  - §6 S3, §7 (endpoints, `outcome-chain-1`), §8 (routeFor);
  - §11b (measured QW-1 diagnosis; budgets), §13 (structural guard), §14 D5.
- Register: I-03, I-08, I-21, I-23, plus the carried COH-8/I-01 progress rule and I-25 (part).
- Paths: `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`. Lines are to main `da5b18391`. CH-1b (0044) is merged before CH-5a1 starts.

## Why it is split (sizing ruling, CH5a-R S1)

With every carried item, CH-5a is about 12 units, not 6. The measured perf work (QW R1–R3 and the board's three recompute reads) alone is a full slice. It splits along one seam:

| Slice | Lane | Units | Depends on | Delivers |
|---|---|---|---|---|
| **CH-5a1** ChainReader and the board read path | 1 | 6 | CH-1b, CH-3 | The board stops calling `mini_overview`, `finding_index` and `evidence_readiness`. R1 (one read per argument), R2 (light Site list, the 409 ruling), R3 (the profile that sizes CH-5c). One cutoff helper. Site-local board day. `known_at` everywhere (L5). The board's old joins and duplicated state tuples are deleted. Measured timings. |
| **CH-5a2** chain endpoints, refs and routeFor | 1 | 6 | CH-5a1, CH-4 | `/api/sites/{code}/chain`, `/api/estate/chain` and `/api/sites/{code}/threads/{id}`. Typed refs, and one `routeFor` on the client (I-08). Lens from the chain (I-21, COH-5). Progress rows from threads (COH-8). Structured `thread_lines`. "Verified on example data" from provenance. The board stops reading the estate snapshot. `_action_for`'s exact join is deleted. The structural AST guard. |

- **Lanes (CH5a-R S2):** lane 1 runs CH-1b → CH-5a1 → CH-5a2 → CH-5b → CH-6. Lane 2 runs CH-4 → CH-9 → DD-1 → **CH-5c** (contingent, 0–4 units; moved from lane 1). That keeps the reader on one lane and one builder context, and gives lane 2 the Portfolio evidence and money work after DD-1.
- The mid-point check (plan §4.5) runs after **CH-5a2**.
- Lane units go from about 51 to about 57. The plan's §2.1, §3 and gate rows are updated.

---

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

## A1. Rulings (CH5a-R)

| # | Question | Ruling |
|---|---|---|
| R1 | QW R1 changes REPEATABLE READ boundaries (`review-packet-QW-1-2.md:83`). | **One request, one read scope.** `perf.route` (`B/perf.py:128`), which already wraps every board, summary and Portfolio route, opens a `ReadScope` (contextvar). It holds the **ledger** (every port call: name and argument key → count) and the **memo**. Memoised: (a) **`PostgresAssessmentStore._window`** (`B/analytics/adapters/postgres_assessment_store.py:865`; CH5a1-R Q10: at `_window`, not only `window_snapshot`, because the Portfolio reaches it through `_dispatch_day_on` with a `cutoff`), keyed on every `EvidenceQuery` field (`read_range` and `cohort` included) plus `analytic_id`, `basis.__qualname__`, `cutoff` and `all_jobs`. `knowledge_at` is **excluded** only when `cutoff` is None: inside one request every live read is the request's "now", and the first read wins. A request is therefore never less consistent than one snapshot; a memo hit crossing REPEATABLE READ connection boundaries is accepted on that basis (CH5a1-R Q12, recorded in the packet). (a2) **`claim_limit_snapshot_on`** (`B/analytics/claim_limit_read.py:1050`), keyed on its full argument tuple (CH5a1-R Q10). (b) every ChainReader port (§A3). The memo returns only frozen values: `WindowSnapshot` is `frozen=True` (`B/analytics/assessment_ports.py:78-79`) but only shallowly (`head`, `run`, `jobs`, `key_heads` are dicts and lists), so `freeze()` deep-freezes it before memoising; ChainReader returns frozen dataclasses and tuples. A port that returns a `dict` is frozen at the adapter boundary (`types.MappingProxyType` over tuples), never handed out mutable (QW-R: the shared-object risk). Outside a route there is no scope, no memo and no change. |
| R2 | QW R2 and the 409. | The summary lists its Sites with `EstateIndexService._scope` only (`B/estate/index.py:214-251`, a static method `(snap, tenant_id, req, admit)` that needs an open estate snapshot and sets `snap.historical/continuation/basis_historical`), through a new light `EstateIndexService.site_list(tenant, req, admit)`. **CH5a1-R Q3:** `site_list` uses the estate snapshot the summary already opens (no extra open; the ledger's `estate.snapshot` count does not grow), calls `_scope` only, and never calls `_finding_coverage`. The mutation is the one `scope()` makes today, so it is not a change. It replaces `estate.scope(...)` at `B/outcome_api.py:158-159`. **The summary never answers 409 for a selection inconsistency.** After CH-5a1 its boards do not read the estate selection for coverage, so the case cannot arise from the Site list. A board that still fails (any reason) makes that Site `UNAVAILABLE` with four UNKNOWN rows, as today (`B/site_outcomes/read.py:549-552`). The `/estate/findings`, `/estate/portfolio` and `/estate/scope` routes keep their 409. |
| R3 | QW R3: profile the Portfolio evidence selection. | **Pre-flight P1, measurement only.** cProfile one warm `GET /api/estate/portfolio` (story week) on the settled L3 clone, and report the top 20 by cumulative time under `select_evidence_scope` and `select_financial_scope`. Sizing rule for CH-5c, ruled by the Architect on the numbers: per-row `cited_provenance` or repeated window reads dominate → CH-5c is 1–2 units (batching); per-Site selection compute dominates → 4 units (from snapshots). CH-5a1 changes neither selection. |
| R4 | What replaces the overview's freshness. | **Snapshot settledness** (design A1). A board day is *settled* for a measure when its latest snapshot at the cutoff exists and is not `PENDING`. The overview's wall-clock freshness (S3 schedule state; I-25's "Unknown about 5 minutes after the serve stops") is no longer an input. The source gate stays: `ports.overview_source` (`B/site_outcomes/mini.py:183-213`), the same cheap route gate the overview used. |
| R5 | Evidence readiness. | `readiness_of(days)` in `B/chain/read.py` over the grades of the given Site-local days (one day for the mini board; every local day the window intersects for cold/EV, rows pooled, CH5a1-R Q8) for the Site type's measures: every expected row COMPLETE → `FULL`; else any COMPLETE or PARTIAL → `LIMITED`; else any LOW or NO_DATA → `NONE`; any PENDING, or no expected row → `UNKNOWN`. A measure with no stored row on a day counts as `NO_DATA`, unless that day carries a NOT_EXPECTED row, exactly as `_counts` (`B/chain/reader.py:50-81`) does; "no expected row" therefore means every measure of every day is NOT_EXPECTED (CH5a1-R Q9). The chip words are `READINESS_CONFIDENCE` (`B/site_outcomes/board.py:115-116`), unchanged. CH-5c reuses this function for the Portfolio evidence cell. Until then the Portfolio cell keeps `evidence_cell_state`: **labelled keep → CH-5c**. |
| R6 | Board day (CH0-R "Day windows", AG-27). | The board day `D` is the **Site-local** day `[local 00:00 D, local 00:00 D+1)` as UTC instants. The route's `?date=D`, `selected_day` and `db_today()` are read as the Site-local date. The summary's mini day is the Site-local day of `to − 1 µs` (the CH3-R `day_at` rule), replacing `mini_summary_day` (`B/site_outcomes/read.py:158`). The dispatch read keeps its own analytic day key (`DispatchReadService.window(t, s, day)`, `B/analytics/dispatch_read.py:136`): **labelled keep → SWEEP-DS**. For Kobo the run hours lie inside both days, so values are unchanged; P2 confirms. |
| R7 | One cutoff helper (CH3-R condition; carried "replace the Portfolio per-row `_cutoff`"). | `site_cutoff(domain, request_known_at, evidence_cutoff, k) -> datetime \| None` in `B/chain/read.py`, pure: mini → `request_known_at` (None = as known now); cold/EV → `min(evidence_cutoff, k)` when the evidence cutoff is known, else `request_known_at`. `board_cutoff` (`read.py:605-608`) calls it. **Corrected (CH5a1-R C5):** `_cutoff` is not a function. It is a row key set at `B/estate/index.py:168-169` as `min(rec.cutoff, scope["k"])` and read at `B/estate/portfolio.py:148-149,170`; that assignment computes its value through `site_cutoff`, and the consumers are unchanged. There is no second derivation. CH-5a2 moves the per-row call into ChainReader's per-Site read. |
| R8 | Findings settled (the index status, `mini.py:391-396`). | Findings are settled for a Site at cutoff `k` when no outbox event of that Site with `type IN ('finding.revised','opportunity.revised')` (the **bare** type strings, `M/0044:66,68`; `@1` is only the register key, CH5a1-R C1) and `occurred_at <= k` (story time; no bound when `k` is None) lacks an `event_consumption` row for consumer `threads` (CH-1b, `M/0044`). `recorded_at` is wall clock and is never compared with a story-time cutoff. The board's `finding_gaps` note (`mini.py:279-294`) names the requested days whose day grade is `PENDING` or `NO_DATA` for the Site type's measures (a missing row counts as NO_DATA, CH5a1-R Q9), with the same template and count of days. **Query shape (CH1b-R2 item 2):** one `EXISTS (… LIMIT 1)` per Site over the `event_outbox_site_type_order (site_id, type, recorded_at, event_id)` index, as an anti-join on `event_consumption` primary key `(consumer, event_id)` (the pre-flight P8 statement). It is memoised in the read scope (R1), and its ms appears in the ledger. P8 measures it on MD-0's full outbox. |

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

## A8. DS-R1 and OL-1

| Item | Touched how | Resolution |
|---|---|---|
| Wall-clock freshness on the board (I-25 part, `mini.py:412-415`) | Replaced | **Fixed:** snapshot settledness (R4) |
| Board day = UTC day (CH0-R "Day windows") | Replaced | **Fixed:** Site-local day (R6) |
| Dispatch analytic UTC day key | Not edited | **Labelled keep → SWEEP-DS** |
| Exact-revision lineage join (`_lineage`, `refresh_chain`, `linked_actions`) | Deleted | **Fixed:** thread join |
| Duplicated state tuples (`board.py:72-74,655`) | Deleted | **Fixed** |
| Occurrence counts include later occurrences (L5, `lookup.py:28-29`) | Edited | **Fixed** |
| Portfolio evidence cell via `evidence_cell_state` | Not edited | **Labelled keep → CH-5c** (R5) |
| "Verified on example data" (`board.py:50`, `mini.py:88,92`, `placement.py:42`) | Not edited | **Labelled keep → CH-5a2** |

**OL-1:** ChainReader names measures and mechanisms only. Which outcomes a Finding moves stays `outcome_map.finding_signal_key`, read by the board composition as today. No outcome id is added.

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

## A10. Pre-flight items (answer from code and the clone, batch them, then stop)

- **P1 (R3).** The Portfolio cProfile (top 20 cumulative under the evidence and money selections), plus the QW-1 call ledger of one summary on the clone, before any code.
- **P2.** The `dispatch` read body (`DispatchReadService.window`, `B/analytics/dispatch_read.py:136`):
  - does it carry the selected window assessment's `state`, `limitations`, `claim_level` and intervals as the overview's `_assessment` shows them?
  - Name each field, or the revision-id read that supplies it.
  - Confirm for Kobo that the dispatch day key equals the Site-local day for every story day (R6).
- **P3.** The finding index's head rule (`B/analytics/finding_index.py`): which revision is a row's head, and how MERGED and NO_LONGER_SUPPORTED heads are listed. The §A3 SQL must reproduce it. The A/B proves equal sets of `(finding_id, revision_id)` per board.
- **P4.** Guard registration: `$pgReaders` gains `chain/adapters/postgres_chain_read.py`, with its tables.
- **P5.** Every caller of `estate.scope` in the summary path, `board_cutoff`, `_cutoff` and `mini_summary_day`.
- **P6.** The consequence read service's constructor in `site_overview/composition` (the `consequences` the overview holds), so ChainReader is handed the same instance (no new connection pool).
- **P7.** The CH-1b names: the outbox `type` strings and the `event_consumption.consumer` values (R8).
- **P8.** On L3m (MD-0 built at main), the ms of the R8 settled query and of each §A3 port on the Kobo D13 board, with the outbox row count. This is report only; it tells whether the per-request R8 check needs the commit-safe cursor that CH1b-R2 item 2 left to DD-1.
- **P9.** Any §A3 port or E-change that assumes sparse days, for example a port that reads only `days.json` story days rather than every Site-local day in the window. List each one; on MD-0 every day is present.

## A11. Review focus

- Zero calls of the three reads. The ledger maximum is 1. The memo returns only frozen values.
- Every board difference is in E1–E5.
- No re-derived join, window, day count or card rule outside `B/chain/`. Re-derivation is High (design §13 checklist).
- Budgets are reported, not claimed.

## A12. Pre-flight rulings (CH5a1-R, Architect: Claude, 2026-11-04)

The pre-flight is `.agent/CH-5a1-preflight.md`. Its answers P1–P9 and its §6 anchors are accepted as build facts. The rulings below are binding. The sections above are corrected in place where they were wrong; each correction names its ruling.

**Questions.**

| Q | Ruling |
|---|---|
| Q1 R8 time bound | **Default accepted.** `occurred_at <= k` (story time, the revision's `created_at`), no bound when `k` is None, bare type strings. `recorded_at` is never compared with a story cutoff. |
| Q2 `base` | **Default accepted.** `base = source_open and day.settled and dispatch is not None`; UNASSESSED → UNKNOWN in `chain/read.py`. CLOSED was always the source gate. |
| Q3 light Site list | **Default accepted.** Reuse the summary's open estate snapshot; `_scope` only; no `_finding_coverage`; no new snapshot type. |
| Q4 index withholding | **Default accepted, with a stop.** The board shows the Finding and the gap line still names the days (E3b). If E3b is non-empty on either dataset, list it and stop before merge. *Architect call while owner away; owner to review (D-AW-10).* |
| Q5 lead Finding | **Default accepted.** `_money`'s choice over `findings()` rows. |
| Q6 Finding SQL | **Default accepted, one change.** Merge exclusion (bounded by `k`), domain/analytic filter, `episode_start DESC, finding_id`. `links_selected_revision` is dropped from the SQL and built from ids by the index's own `base` construction (C4). A Finding missing from the thread read is caught by the A/B set equality, which is a regression gate; no new COH rule. |
| Q7 `trial_hours` | **Replaced by C6.** `trial_hours`, `cost_check` and the state all come from the existing `VerificationService.summary` call, memoised, not from new SQL. |
| Q8 Cold local days | **Default accepted.** `readiness_of` pools the rows of every Site-local day the window intersects (no new rule; R5 over a day set). **Amended by MD0-PF Q4:** MD-0 itself writes Cold `days.json` entries as Addis local days in UTC. CH-5a1 changes only the collector's board-query canonicalisation and `day_windows`, plus Kobo's R10 `build_work` change (§A9 item 5). Both A/B sides use the B-side windows. |
| Q9 missing row | **Default accepted.** A missing row is NO_DATA unless the day carries NOT_EXPECTED (the `_counts` rule), in `day.gaps` and in `readiness_of`. UNKNOWN for "no expected row" only when every row is NOT_EXPECTED or the Site type has no measures. Kobo days before first evidence (1–2 Oct) are therefore named as gap days; listed under E3. |
| Q10 memo surface | **Default accepted.** `_window` with the full key, plus `claim_limit_snapshot_on`; `freeze()` deep-freezes. This is the CH-5c precondition (CH5c sheet §1). |
| Q11 EV LIMITED → NONE | **Default accepted as E1.** EV 20 and 27 Oct read "Low" because their day grades are LOW; R5 is unchanged and nothing is tuned. *Architect call while owner away; owner to review (D-AW-9).* |
| Q12 memo across snapshots | **Default accepted** under R1. Recorded in the packet. |

**Sheet corrections (applied above).**

- **C1 (R8).** Bare type strings; `occurred_at`, not `recorded_at`.
- **C2 (A4 `base`).** The dispatch body has no CLOSED; the gate is the source.
- **C3 (§A3 SQL).** Merge exclusion, domain filter, DESC order.
- **C4 (§A3 `findings`).** `links.selected_revision` is a built link, not a column.
- **C5 (R7).** `_cutoff` is a row key at `index.py:168-169`; its value goes through `site_cutoff`.
- **C6 (§A3 `action_facts`).** Found by the Architect on reading `B/actions/verification.py:948-1080`, not by the pre-flight. A single "latest `verification_outcome`" SQL would drop the clock PENDING and REASSESSMENT_PENDING states that `current_state` derives. The state, cost check and trial hours therefore stay on the one `summary` call. Only the `action` detail call is replaced. This reduces the planned `action_read` saving from about 0.68 s to about half; the residual is reported in §A7.
- **C7 (R2).** `_scope` needs an open snapshot and mutates it (Q3).
- **C8 (E1).** EV 20/27 Oct listed; Kobo old/new values from the pre-flight §4.
- **C9 (R5, R8).** The missing-row rule (Q9) and the day-set form (Q8).
- **C10 (anchors).** `board_cutoff` `read.py:605-608`; `THREAD_WIRE_KEYS` `board.py:74`; `THREAD_LATER_STATES` `:656`; `cost_checks` `postgres_estate_read.py:359`; mini `compose` `mini.py:372-511`; `finding_gaps` use `:496`; `SnapshotReader.latest` `chain/reader.py:90`.

**Performance note for §A7.** `money_head` is about 0.66 s warm on its own (about 0.42 s of it `money_eligibility`'s dispatch and Finding reads). With the Q10 memo it shares the board's dispatch key. The packet reports `money_head` as its own ledger line, so CH-5c can tell whether the share happened.

---

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

## B7. "Verified on example data" from provenance (DS-R1; COH-12)

- One helper `provenance_suffix(source_state) -> str` in `B/chain/vocabulary.py`: `REGISTERED_SIMULATION` and `AUTHORED_DEMONSTRATION` → `" on example data"`, anything else → `""`.
- Applied at `B/site_outcomes/board.py:50` (`ACTION_RESULT["VERIFIED"]` becomes `"Verified{suffix}"`), `B/site_outcomes/mini.py:88,92` (`"{code} verified{suffix}"`), and `B/estate/placement.py:42` (`"Change verified{suffix}; watch for it coming back"`).
- The source state is the verification evidence's source provenance (P2 names the field). On the demo data the words are unchanged.
- **L3 assertion:** every COH-12 info line has `source_mode` in {REGISTERED_SIMULATION, AUTHORED_DEMONSTRATION}.

## B8. Structural AST guard (design §13)

- **`tools/checks/check_chain_structure.py`**, run from `tools/check-architecture.ps1`. Outside `backend/assetops_backend/chain/`:
  - (a) no module imports both a Finding store or index (`analytics.adapters.postgres_finding_store`, `analytics.finding_index`) and an Action store or index (`actions.*store*`, `actions.site_index`);
  - (b) no call to the replaced day and window functions `{_days_block, _productive_month, mini_summary_day}`, nor a new definition of a function named in the design §5.1 "Replaces" column.
- **Baseline** `tools/checks/fixtures/chain_structure_baseline.json` lists today's violations, each with its owner (CH-6, CH-7). The baseline may only shrink.
- **Self-test:** `tools/checks/test_chain_structure.py`.

## B9. DS-R1 and OL-1

| Item | Touched how | Resolution |
|---|---|---|
| "Verified on example data" (`board.py:50`, `mini.py:88,92`, `placement.py:42`) | Edited | **Fixed** (B7) |
| Cold/EV API links on screens (`cold.py:217`, `ev.py:264-266`) | Replaced | **Fixed** (B1, I-08) |
| Lens from price or mechanism lists (`index.py:27-28,125-128`) | Replaced | **Fixed** (B5) |
| Exact-revision Action join (`portfolio.py:173-200`) | Deleted | **Fixed** (B3) |
| Per-row cutoff (`index.py:182-183`) | Replaced | **Fixed** (B3, R7) |
| The 17 outcome-id literal sites (design §8b item 7) | Not edited | **Labelled keep → CH-6** (ratchet) |

**OL-1:** threads and rows get categories and lens only through `outcome_map` (`categories_for`, `lens_flags`, `thread_signal_key`). `B/chain/refs.py` and `chain_api.py` hold no outcome id.

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

## B11. Pre-flight items (answer from code, batch them, then stop)

- **P1.** The fields `placement.place` and `workflow_label` read from an estate row, and the ChainReader source of each (B3).
- **P2.** The verification evidence's source provenance field for B7, for mini trials.
- **P3.** Every server `href` field on the board, Portfolio, estate Findings and Actions bodies, and every client component that renders one (the B2 inventory, with `path:line`).
- **P4.** The mini finding-index row builder (where `lens_flags` is added) and its tests.
- **P5.** The router wiring in `B/main.py` and the registry and access dependencies the board route uses (`B/outcome_api.py:84-101`), so the chain router reuses them unchanged.

## B12. Review focus

- One `routeFor` and one `href_for`, agreeing on the shared fixture. No component renders a server `href`. No `/api` in any rendered link.
- Lens, progress and lines are read from the chain. COH-1, COH-5 and COH-8 pass with no expected entries.
- The new endpoints are views over ChainReader. They contain no join, window or day-count logic of their own.
- No outcome id outside `outcome_map.py` (OL-1).

## A13. Build rulings CH5a1-R2 (Architect 6, Claude, 2026-11-04; packet `AssetOpsV1-ch5a1\.agent\review-packet-CH-5a1.md` at `110d0057a`)

- **R-1: default accepted. Keep the two time axes apart.**
  - `source_known_at` is transaction time: the revision's `created_at`, 0045 / CH3-R D-b. Compare it only with the request's transaction-time bound (`known_at`; None means live, all visible). That applies in `B/chain/lookup.py:28,34,55`, `postgres_chain_read.py:37` and `postgres_thread_sources.py:273`.
  - The Site evidence cutoff is story or valid time. It bounds thread *state* (event `effective_day`, snapshots) and is never compared with `source_known_at`. The alternative, a story-time instant, is refused: an occurrence has no story-time "known" instant.
  - This is consistent with D-b, because 0045 records exactly the transaction-time column, and with R8, which is about settledness, not visibility.
  - Tests:
    - L0: a revision created after the story cutoff but before the request `known_at` is visible;
    - L0: an explicit `known_at` earlier than `created_at` hides it;
    - the clone: COH-10 ×7 and COH-11 ×2 go to 0, and Cold/EV threads return on the Portfolio, the summary and the EV 27 Oct board.
- **COH-7a: keep `summary_day` (local day of `to − 1 µs`, the CH3-R `day_at` rule); adapt COH-7a.**
  - The summary's mini card is one Site-local day by design. So COH-7a's expected window for a mini Site's summary card is `[local midnight, next local midnight)` of `chain.read.summary_day(to, tz)`, imported and not re-derived. Every other Site window must still equal the requested window.
  - This covers CH-5a1's ×1 and MD-0 L3m's ×2 (week and month: same cause, card day against requested window). Ownership moves from CH-6 to **CH-5a1**, superseding MD0-S4 R3. MD-0's L3m rerun after the CH-5a1 merge must show 0; nothing is added to `expected-mechanism.json`.
- **Extra E1 entry (summary month Kobo, local 3 Nov, Unknown → Low): accepted.** It is the honest R5 `readiness_of` grade of a part day. Add it to the E1 list and to DS-1's honest-state table.
- **Ledger max 3 on the summary: default accepted.**
  - Key `objectives` by Site.
  - Kobo `productive_readings`: if the two calls have the same arguments, memoise them (R1). If they differ (card day against period), the window is part of the key.
  - A0 "max 1 per key" then holds as written. Report the key list.
- **Performance: no ruling relaxes a budget.** The plan change is in plan row CH5a1-R2 and CH5c-R2, an owner decision.
  - CH-5a1 must also report the cause of the Kobo warm-over-cold inversion (7.8 s against 4.5 s) and the query plan of the 2.1 s `_window` read (max_per_key 1, so it is a plan or index problem, not repetition), as findings in its re-packet.

## A14. Review-time rulings CH5a1-R3 (Architect 6, Claude, 2026-11-04)

- **M1 (GAP-K7 reads UNKNOWN): this is a harness artefact.**
  - The live `mini_renewable` jobs for D7–D9 stay queued only because the harness never drains the mini queue for undelivered days. The real worker would run them; the demo prepare runs `drain_mini`.
  - **The fix goes in MD-0b:** after seeding, run the product mini worker's `run_pending` over the whole story, as the worker would. Do not add a special reconcile for undelivered days.
  - Expected after the fix: D7 headroom NO_DATA and readiness NONE before the fill, so the E1 "GAP-K7 NONE" line stands. MD0-S4 R1.5's "NO_DATA/PENDING" is amended to NO_DATA on all three measures once MD-0b drains.
  - Until MD-0b, CH-5a1 records D7 as UNKNOWN, with the cause and owner MD-0b. It does not block CH-5a1.
- **M3 (COH-5 ×6, `lens_flags []`): accepted as the builder suggests.** The defect is already on main (Findings index). Record the 6 entries in `expected-mechanism.json` with owner **CH-5a2**, whose L3m target is COH-5 = 0.
- **M4 (shared template staleness): give each fingerprint its own template.**
  - The template is named `assetops_mechanism_tpl_<fp8>_test`, and the tool keeps the two newest, so main and a branch never overwrite each other.
  - The rebuild-on-merge job builds main's template when a merge changes a fingerprinted file.
  - This is a small `mechanism_dataset.py` change in FIX-MAIN-1.

## B13. Pre-flight rulings CH5a2-R (Architect 7, Claude, 2026-11-04; pre-flight `AssetOpsV1-ch5a2\.agent\CH-5a2-preflight.md` at `6d2d37881`)

The answers to P1–P5 are accepted. These rulings amend Part B. Where a ruling conflicts with B0–B12, the ruling wins.

**S1, split (Q9): accepted.** About 9 units against 6, so Part B splits into two slices.
- **CH-5a2a (5 units)**, branch `task/CH-5a2-chain-endpoints` (the current one):
  - B1: refs, `href_for`/`routeFor` and the shared `route-refs.json`, plus the three endpoints, with counts as in R3 left `null` until CH-5a2b;
  - B2 as amended by R4, and R5;
  - B3 second and third bullets (the exact-join deletion and the per-Site cutoff map);
  - B4, B5, B6, B8 (R6), and R8;
  - R7 only if the owner says yes.
  - L3 target: COH-1, COH-5 and COH-8 entries all removed, with COH-1 finding 0 `/api` links. L3m target: 0 unexpected.
- **CH-5a2b (4 units)**, cut from main after CH-5a2a merges:
  - B3 first bullet (R1);
  - B7 (R2);
  - the PC-1 count claims and COH-17 (R3).
  - L3/L3m targets add COH-17 = 0 and the "on the days checked" texts appearing only in GAP-K7/C3/E2 windows.
- **Lane 1** becomes CH-5a2a → CH-5a2b → CH-5c → CH-5b → CH-6a → CH-6b. CH-6a's pre-flight P3 (the Claim shape) reads CH-5a2b.

**R1 (Q1), board off the estate snapshot: default accepted (CH-5a2b).** Add two ChainRequest ports in `B/chain/`. Each is one indexed query per Site, memoised in the request ledger (ledger maximum 1 per port per request):
- `placement_facts(site, finding_ids, k)` gives, per Finding:
  - its source provenance state;
  - its consequence head state, by the coverage rule (PRICED, UNPRICED or UNKNOWN), with the coverage function imported, never copied;
  - `recurs_after` id and title.
- `action_rows(site, k)` gives `chain_action` with its events reduced at `k` by the existing coverage reduce (imported), plus the verification plan window and the selected event time.
- Move a function into `B/chain/` only if an import cycle forces it. The move is then a pure move, with no edits.
- `place` and `workflow_label` stay the same functions.
- Acceptance is the L3 A/B: every chip and label unchanged. Any difference is reported, never adapted.

**R2 (Q2), provenance: default accepted (CH-5a2b).**
- `VerificationService.summary` gains `source_class`, read from the stored `details.source.source_class` of the outcome the summary already selects. There is no new derivation.
- The field then goes to `ActionFact.source_class`, then to the estate action row (from `action_rows` under R1).
- `provenance_suffix` as in B7. A null `source_class` gives `""`.
- **L3/L3m assertion:** every VERIFIED summary has a non-null `source_class` (VERIFIED needs a positive source class, `verification_rules.py:664`). A null is reported as a finding.
- The MD-0 template is rebuilt as R5 says.

**R3 (Q3), PC-1 count claims and COH-17 (CH-5a2b).** `Claim` and `count_basis` are exactly as in CH-6 §S.2.
- **Thread classes.** One function in `B/chain/` classifies a Site's mechanism threads in the window, at the cutoff, using the same thread set as `thread_progress` (CH-3 I-24):
  - `open`: OPEN, RECURRED or REOPENED;
  - `in_hand`: ACTION_IN_HAND or CHANGE_APPLIED;
  - `verified`: RESOLVED_MONITORING or CLOSED.

  `/estate/chain` `sites[].threads` and the Portfolio's `thread_progress` both call it.
- **Claims.**
  - `count.open_threads` = open + in_hand;
  - `count.verified_results` = verified (it equals `verified_resolution_count`);
  - `count.opportunities` = the CH-4 item count.
- **`days`** is the per-Site GradeCounts §S.2 subset, summed over the Sites in scope.
- **A null value** (the read failed) gives basis NOT_KNOWN, whatever the days.
- **Texts** (literals in `B/chain/vocabulary.py`; they are MOCK DEVIATION candidates and go through guard V; if V flags one, report and stop):

| key | COMPLETE | CHECKED_DAYS, n ≥ 1 | CHECKED_DAYS, n = 0 |
|---|---|---|---|
| `count.open_threads` | `"{n} open finding"` / `"{n} open findings"` | `"{n} open on the days checked"` | `"None open on the days checked"` |
| `count.verified_results` | `"{n} fix confirmed"` / `"{n} fixes confirmed"` | `"{n} confirmed on the days checked"` | `"None confirmed on the days checked"` |
| `count.opportunities` | `"{n} opportunity"` / `"{n} opportunities"` | `"{n} found on the days checked"` | `"None found on the days checked"` |

  NOT_KNOWN is always `"Not known yet"`.
- **Where.** The claims appear in three places:
  - `/estate/chain` `counts` (now Claim wire objects);
  - Portfolio `summary.claims`, with all three keys;
  - estate Findings `summary.claims`, with `count.opportunities`.

  They are wire-only in this slice. CH-5b (Findings) and CH-6b (Portfolio cards) render them.
- **`summary.count_basis`** takes its value from `count_basis(days)`. The nullability of `finding_count` and `evidence_gap_site_count` stays on the coverage states until CH-6b. The packet lists every old → new `count_basis` value.
- **COH-17** compares claims with equal (key, Site set, window), and no lens or other filter, across `/estate/chain`, the Portfolio summary and the Findings summary. Value, basis and text must be equal.
- **Collector** (`tools/checks/chain_coherence.py`): fetch `/estate/chain` for each estate window it already reads, and `/sites/{c}/chain` for each built day.

**R4 (Q4), refs: amended.**
- **(a) One rendered-link field.** Every linked item on the legacy bodies (board, Portfolio, estate Findings, estate Actions and CH-4 items) gains a sibling `link_ref` (a Ref).
  - The existing `ref` objects are identity refs and stay byte-identical: the Finding issue, the opportunity issue, the warning's string key, and the CH-4 `ref`/`thread_ref`.
  - Their readers (COH-5, COH-13, the frontend) are untouched.
  - `href` is built by `href_for(link_ref)`.
  - The client renders only `routeFor(link_ref)`. An item without `link_ref` renders no link (this replaces "without `ref`" in B2).
  - The new `/chain` bodies keep `ref` as B1 defines it, since there is no collision there.
- **(b) Ref kinds.**
  - `SITE{site, view?}` and `ESTATE{view, query?}` take enumerated views: exactly one value per existing builder not already covered by another kind (`operatorSiteRoutes.ts` site builders, and the estate path constants at :424-455). There is no free `path`.
  - `query` keys are only those the mapped builder already takes.
  - Every enum value has a `route-refs.json` row.
  - `CASE` maps to the work-case path the server emits today, with one builder added in `routeFor`.
  - `THREAD` renders no link until CH-5b gives it a screen.
- **(c) Client conversion.**
  - Convert the four B2 components and `EarlyWarnings.tsx`.
  - The server adds `link_ref` to the Portfolio card `destination` fields too. `PortfolioOutcomes`, `EstateEvidence` and `EstateFinancials` convert in CH-6b, which rebuilds those cards.
  - The work screens (`SiteWorkActions`, `siteWorkCases`, `GlobalIncidents`, `workRequestShared`) are listed in the packet for CH-5b's hard-wiring baseline, owner CH-7.
  - None of these renders an `/api` link today. COH-1 = 0 checks the server.

**R5 (Q5): default accepted.**
- Build the cold/EV FINDING `link_ref` with `window` in `cold.py`/`ev.py` from the row's own proven window and cutoff, as `evidence_money.finding_window_href` takes them. Leave the assessment store's `links` untouched until CH-7.
- After editing an import-traced file (`finding_index.py`, `verification.py`), run `status`. If it is stale, rebuild the template once at the slice head with `--budget 540`, in parts as dispatched. This is a time bound, not a data value.

**R6 (Q6): default accepted.** `tools/checks/chain-structure.ps1` is registered in `$checkModules` and calls `$guardPython tools/checks/check_chain_structure.py`, as `configuration-persistence.ps1:974` does. It never adds `-ExecutionPolicy`.

**R7 (Q7), summary card day: recommendation to the owner, not built until the owner answers.**
- **The defect.** CH-5a1's `summary_day` (Site-local day of `to − 1 µs`) gives a UTC-midnight one-day window the next local day east of UTC. The board route reads the same pair as the calendar date the user picked (`outcome_api.py:63-78`, then `selected_day`, then `board_day(date, tz)`).
- **What the client sees.** The 31 Oct summary and Portfolio cell is Kobo's 1 Nov board ("On track"). The Site page they click into for 31 Oct says "Needs attention · Before the change on 1 Nov". This is a visible contradiction on the story's key day.
- **It also breaks CO-6.** CO-6 asserts that Kobo's summary cells equal its day-S board and that the window starts at S. It is expected to fail on main `01133225a`. The FIX-MAIN-1 evidence ran on `c036f8a49`, before CH-5a1. This is not a FIX-MAIN-1 expectation to move.
- **Recommendation: one day rule for the board and the summary.**
  - A pair that is exactly one Site-local day selects that local date.
  - A UTC-midnight pair selects its UTC calendar date, read as that Site's local day of the same date.
  - Any other window uses the calendar date of `to − 1 µs` in the frame where `to` is a midnight: UTC if `to` is a UTC midnight, otherwise Site-local.
  - One function in `B/chain/read.py` is used by `_mini_day_params` and `site_outcomes/read.py:391`.
  - COH-7a's expectation (CH5a1-R2) follows it.
  - About 0.25 unit, in CH-5a2a.
- **Alternative:** keep the current rule and accept the mismatch until the walkthrough. Not recommended.
- **`db_today()` as a UTC date** stays recorded (SWEEP-DS).

**R8 (Q8): accepted.** Replace `_last_local_day` with `summary_day`, or with the R7 function if the owner agrees. Delete `BoardServices.finding_index`, `parse_finding_index`, `covering_days` and their wiring.

## B14. Pre-flight rulings CH5a2b-R (Architect 8, Claude, 2026-11-05; pre-flight `AssetOpsV1-ch5a2b\.agent\CH-5a2b-preflight.md` at `73a3fcc74`)

Code facts F1–F9 are accepted. These rulings amend §B13 R1–R3 for CH-5a2b. Where they conflict, B14 wins. **Size stays 4 units** (Q1's +0.75 alternative is not taken; Q7's override replaces code rather than adding it).

- **Q1, placement_facts content: default accepted.** By F1 the chip is a function of (source provenance state, lifecycle) alone, so building the consequence state changes nothing a client sees. `placement_facts` returns source provenance state and `recurs_after` id and title; no consequence state, no snapshot shim. **Guard (bulletproof, not data):** one L0 test pins F1. It asserts `place(row, …).confidence` is equal for `consequence` in {PRICED, UNPRICED, UNKNOWN, absent} on every (provenance state, lifecycle) pair, and that `_mini_grid_money` cannot return WITHHELD. If `_confidence` ever starts reading the consequence, the test fails and the consequence must be built (owner then: CH-6/CH-7). R1's "consequence head state" bullet is withdrawn.
- **Q2, provenance read: default accepted.** "One indexed query" in R1 means one memoised port call (ledger 1), at most 3 statements on one read-only connection, with `PublicProvenance` imported unchanged and its injected reads wired from `chain/composition.py`.
- **Q3, chip scope: default accepted.** The chip is computed for heads with `in_window` true (the Site-local board day, AG-27 / CH5a-R R6). Pre-declared allowed A/B change class: heads whose membership differs only between the old UTC day (`estate_bounds`) and the Site-local day, plus heads on a day that was not fully selected. List each in the packet. Any other chip difference is a finding: report and stop.
- **Q4, failure names: default accepted, one change.** `reads.failed` gains `"placement_facts"` / `"action_rows"` with the same notice behaviour; the `estate` port and `estate_bounds` leave `MiniPorts`. **Override:** rename the diagnostic to `ACTION_ROW_MISSING`. It is never on the wire (`mini.py:213`), so byte-stability buys nothing and the old name would describe a read that no longer exists. Tests follow the rename.
- **Q5, action_rows set: default accepted.** Site MINI_TRIAL `chain_action` rows created by `k`, events by `k`, reduced by the imported `actions.lifecycle.reduce`, plus the plan window open at `k`, `_selected_recorded_at` and `source_class`, with exactly the keys `workflow_label` reads. No window bound in the port; the board joins by id.
- **Q6, Portfolio / Findings placement text: default accepted.** The estate `snapshot.verification` read returns the selected outcome's stored `details.source.source_class`; `coverage._actions` copies it onto the row; `place` passes it to `provenance_suffix`. No new derivation. MD-0 template rebuilt once at the slice head (R5, `--budget 540`).
- **Q7, thread set for the claims: overridden.** The claims must come from one computation, not two sets compared after the fact (a stop there would cost a round and invite tuning).
  - One function in `B/chain/` (for example `chain/claims.py: estate_count_claims(request, sites, lo, hi, opportunity_items) -> {key: Claim}`) builds all three count claims. Its thread set is the default's: `site_chain.threads_of` restricted to threads with a **Finding** occurrence whose episode meets the window, at the per-Site cutoff, read on `window_day`. No event-only and no opportunity-only threads. It classifies with the one `chain.threads.classify(states)`.
  - `/estate/chain` `counts`, Portfolio `summary.claims` and estate Findings `summary.claims` all call it, injected from `chain/composition.py` with Q8's callable (same ChainRequest, same per-Site cutoff).
  - `thread_progress` keeps its existing fields (`verified_resolution_count`, `priority_site_count`) over its unchanged Finding-row set, calling the same `classify`. R3's "`count.verified_results` equals `verified_resolution_count`" is withdrawn. The packet lists, per window on the clone and on L3m, every place where the two differ, as an info item for CH-6b (which retires the legacy fields when it renders the claims). No screen text changes from this.
  - COH-17 still compares the three bodies (equal key, Site set, window, no lens): it now proves the routes pass equal scope, window and cutoff into the one function.
- **Q8, `days`: default accepted.** One injected `claim_days` from `chain/composition.py`, one `ChainRequest.day` per Site over `window_days(lo, hi, tz)`, the public `grade_counts_of` (L2), the request's own `known_at` through ChainRequest (so the per-Site cutoff applies as on `/estate/chain`). Any Site None → `days` None. Whole Site scope, no lens. Q7's function reuses this read.
- **Q9, `summary.count_basis`: default accepted, no owner question.** This is a mechanism consequence the owner already agreed: BASE-1 (owner-agreed direction) and plan §2.5.3 PC-1, "One basis function (the Portfolio's `count_basis` rule) is used by the Portfolio, Findings, the outcome summary and the board", with AG-28 (screens render the unified backend logic) and AG-29 (copy from the server). The changed checked-days wording follows from the day grades, not from a screen task. No frontend edit. `null` → `"NOT_KNOWN"` is inert (the client tests `=== "CHECKED_DAYS"`). The packet lists every old → new value on the clone and the L3m windows, with the screen text each one changes. The Q9 alternative is rejected: it would keep two basis rules alive.
- **Q10, lens: default accepted.** `summary.claims` is lens-independent (whole scope on every lens); COH-17 reads it from the `findings_all` bodies.
- **Q11, thread route cutoff: default accepted.** Optional `from`/`to` with the board's `board_window` parsing; cold/EV resolve the cutoff through **one** service method factored out of the board's cold/EV path (`ports.overview` then `board_cutoff`) and used by both routes, never copied. With no window it equals `/chain`'s default-window `window.known_at`. Mini unchanged. The docstring states "last visible event".
- **Lows L1–L3** (`.agent/demo-sprint-lows-2026-10-31-pipeline.md`, CH-5a2a): built as the pre-flight's "Not questions" list says; L3 is Q11.
- **Tests stay localised** (L0, L2/L2m for the touched modules, one L3 + L3m run at the slice head after the template rebuild). No full suite (OD-P4).

## B15. Review-time ruling CH5a2b-R2 (Architect 9, Claude, 2026-11-05; packet `AssetOpsV1-ch5a2b\.agent\review-packet-CH-5a2b.md` at `3122c2d1d`)

**D2, "on the days checked" outside the GAP windows: (a) the target is restated. No code change in CH-5a2b. Size stays 4 units.**

- **MD-0 estate day windows (10-19 and 10-28 on states, 10-19 on close): not a defect.**
  - The collector's estate day window is `day_windows()[].estate` (`tools/checks/chain_coherence.py:71-91`). It is the *enclosing* UTC-midnight window of a Site-local day. East of UTC, that is two UTC dates (48 h), for example `10-18..10-20`.
  - CH-5a2a D14 says a window with both ends at UTC midnight names its UTC dates (`chain/read.py:140-147`). So this window names two days, and one of them is outside the dataset's day set (`no_data`). CHECKED_DAYS is the honest grade of the window that was asked for.
  - Mapping a 48 h window to one Site-local day would break D14 and R7. It would also make a two-day request report one day.
  - A client never issues this window. The estate routes take UTC-midnight bounds, and a picked date is a one-day UTC-midnight pair. By R7 rule 2 and D14, that pair names exactly that date, read as the Site's local day.
  - The GAP-K7 day window reads NOT_KNOWN because both of its named days are `no_data`. That is consistent with this.
  - The original target assumed each estate day window names one day. That assumption was wrong.
- **Polish clone, every window: an honest consequence of the data, not a defect.**
  - No polish day grades `complete`. Until DD-1, Kobo is PARTIAL and Cold/EV are LOW (handoff §5). CH9-R2 Q2 makes the 8 h Kobo story days missing study days.
  - Week and month already read CHECKED_DAYS before this slice. No value is tuned.
  - DD-1, which extends story days to their declared hours using existing scenarios only, is the slice that can move polish days to `complete`. If DD-1 does not fit its cap, the owner is told before E3 (already agreed).
- **Restated target (replaces "only in GAP-K7/C3/E2 windows"):**
  - In every window, a count claim's text is CHECKED_DAYS-form exactly when `count_basis(days)` is CHECKED_DAYS. NOT_KNOWN reads "Not known yet".
  - On MD-0, every day the window names (by `window_days`) that is not `complete` is either a declared gap day (GAP-K7/C3/E2) or outside the variant's built day set.
  - Every built, non-gap MD-0 day grades `complete`.
- **Evidence in this slice (packet edit only, about 0.1 unit, no re-run):**
  - Add one table to the packet from the collected bundles already on disk. Per MD-0 window (states and close; estate S/week/month plus the day windows that show the text), give:
    - the named days;
    - the `days` counts;
    - each non-`complete` day with its reason (declared gap / outside the day set).
  - For polish, one line giving the per-grade totals.
  - Any non-`complete` day that is built and not a declared gap is a finding: report it, do not adapt.
  - If the bundles are gone, state that. The reviewer then accepts on the packet's existing D2 account, and the guard below carries the proof.
- **Guard: owner CH-6b, before these texts reach a screen.** CH-6b renders the claims to clients, so the mechanism proof lands there as COH-18 in `tools/checks/chain_coherence.py`. It needs no new data.
  - For each window and Site, the claim's `days` must equal the sum, over `window_days(lo, hi, tz)`, of that Site's per-day grades from the collected `/sites/{c}/chain` day bodies. An unbuilt day counts as `no_data`.
  - With an expectation file, every built day not listed as a declared gap must grade `complete`. The list goes in `expected-mechanism.json` as `gap_days`. The polish build has no `gap_days` list, so only the sum rule applies there.
  - Size about 0.25 unit inside CH-6b.
  - L0 test: a planted wrong-day mapping fails COH-18.

**For CH-6b (info, no ruling): the legacy fields against the claims on the clone at S and week.** `verified_resolution_count` 1 against `count.verified_results` 0, and `priority_site_count` 0 against `count.open_threads` 1.
- The claims are the authority (B14 Q7). They read the thread state at the per-Site cutoff on `window_day`, which is CH-3's rule. The board on the same day reads "Needs attention · before the change", so the claims agree with it.
- When CH-6b retires the legacy fields, the Portfolio text at S and week moves from one confirmed fix to one open finding. CH-6b's packet must:
  - list that screen-text change;
  - confirm its cause from the thread events: the verification is known only after the S/week cutoff.
- If the events show otherwise, report and stop.
