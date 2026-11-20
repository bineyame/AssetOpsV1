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

## B7. "Verified on example data" from provenance (DS-R1; COH-12)

- One helper `provenance_suffix(source_state) -> str` in `B/chain/vocabulary.py`: `REGISTERED_SIMULATION` and `AUTHORED_DEMONSTRATION` → `" on example data"`, anything else → `""`.
- Applied at `B/site_outcomes/board.py:50` (`ACTION_RESULT["VERIFIED"]` becomes `"Verified{suffix}"`), `B/site_outcomes/mini.py:88,92` (`"{code} verified{suffix}"`), and `B/estate/placement.py:42` (`"Change verified{suffix}; watch for it coming back"`).
- The source state is the verification evidence's source provenance (P2 names the field). On the demo data the words are unchanged.
- **L3 assertion:** every COH-12 info line has `source_mode` in {REGISTERED_SIMULATION, AUTHORED_DEMONSTRATION}.

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

## B11. Pre-flight items (answer from code, batch them, then stop)

- **P1.** The fields `placement.place` and `workflow_label` read from an estate row, and the ChainReader source of each (B3).
- **P2.** The verification evidence's source provenance field for B7, for mini trials.
- **P3.** Every server `href` field on the board, Portfolio, estate Findings and Actions bodies, and every client component that renders one (the B2 inventory, with `path:line`).
- **P4.** The mini finding-index row builder (where `lens_flags` is added) and its tests.
- **P5.** The router wiring in `B/main.py` and the registry and access dependencies the board route uses (`B/outcome_api.py:84-101`), so the chain router reuses them unchanged.

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
