# W3-03 pending rulings

## P-0b-1 — RESOLVED (r0b applied: `excursion` + drain, cold line assertions added) — B3 clean fixture: cold `normal` makes no POTENTIAL_PRODUCT_EXPOSURE line (run 0b, stopped variant)

Spec: closure 4 B3 names cold `normal` (via `mixed_replay` mechanics) and requires "cold `POTENTIAL_PRODUCT_EXPOSURE`
UNPRICED" in the clean four-Site fixture, plus F/E/M COMPLETE.

Producer step: `test_w303_portfolio_fixture_postgres.py::build_portfolio_fixture` — `opened("normal", cold_chain)`,
`run(cold)` (W2-03 assessment worker), then EV x2, tariffs, money, P01 PowerSite v1-v3, `rig.run()`; frozen read
`2026-10-30T09:03:00Z` (= PowerSite `runner.now + 1 min`); request `[2026-10-06,2026-10-07)`, no `known_at`.

Actual public read (cold `normal`):
- `/findings`, `/evidence`, `/financials`: `CURRENT`, `coverage.state=COMPLETE`, all four Sites `CURRENT`.
- `/findings` rows: only KOBO-001 (W1 PRICED). **No COLD-LAB-001 Finding.**
- `/financials` rows: KOBO-001 `CANDIDATE_OPERATING_COST_EXPOSURE ELIGIBLE`; EV-LAB-001/002 `GROSS_TARIFF_SCENARIO
  ELIGIBLE` (group `COMPARABLE`, 2 lines). **No cold line**; group `POTENTIAL_PRODUCT_EXPOSURE` state
  `UNKNOWN_COVERAGE`, 0 lines, while root `coverage.state` is `COMPLETE` (under closure 5 S4 this cold unit is `U`,
  so Portfolio M would be PARTIAL, not COMPLETE).
- `/evidence`: COLD-LAB-001 rows backup/cooling/temperature FULL, exposure NONE (window 19:00-20:05Z).
- Cold coverage item: selection `…017c`, watermark real DB time, job SETTLED, freshness RECENT.

Mismatched assertion: "cold POTENTIAL_PRODUCT_EXPOSURE UNPRICED" (and M COMPLETE once Portfolio reduces it).

Probes (not committed; evidence only, same DB, same composition):
- cold `excursion` without drain: two cold Findings (`UNPRICED` in `/findings`), still no cold line,
  `POTENTIAL_PRODUCT_EXPOSURE` still `UNKNOWN_COVERAGE`.
- cold `excursion` **plus the W2-04 cold consequence worker** (`test_w204_cold_consequence.drain(cold)`, the pattern of
  `test_w301_provenance_dto_postgres.py::_cold`): one cold line `POTENTIAL_PRODUCT_EXPOSURE UNPRICED`, amount null,
  `finding_revision_id` = a selected cold Finding revision; group `INELIGIBLE` (1 line); all three roots
  `CURRENT/COMPLETE`; every other assertion in the test still passes (1 passed, 83 s).

Question: should the clean fixture use cold `excursion` + W2-04 drain (builder already takes
`cold_case="excursion", cold_drain=True`), or another cold producer? Once ruled, the held assertions to add are:

```python
(cold_line,) = lines[fx.site_ids["COLD-LAB-001"]]
cold_revisions = {r["finding_revision_id"] for r in rows[fx.site_ids["COLD-LAB-001"]]}
assert (cold_line["category"], cold_line["eligibility"]) == ("POTENTIAL_PRODUCT_EXPOSURE", "UNPRICED")
assert cold_line["amount"] is None and cold_line["finding_revision_id"] in cold_revisions
assert len({line["category"] for line in financials["rows"]}) == 3
```

## Q-1a-1 — RESOLVED (r1a applied in 1b: Lane A `06acf1cf`, Lane B `f3f04ef6`) (run 1a): S9 Action tie key has no selected event time in the Action selector rows

Spec: closure 4 S6-S9 "choose for a Finding cell by latest selected Action event `recorded_at`, then `action_id`
ascending". `coverage.py::_actions` (Lane A file) selects each Action's latest event but its row carries only
`selected_event_id`, not that event's `recorded_at`; Lane B may not edit it. Built in 1a:
`estate/portfolio.py::_action_for` joins on the exact `(source_finding_id, source_finding_revision_id)` pair and, when
several match, takes the max of a private `_raw["_selected_recorded_at"]` if present, else `action_id` ascending (the
spec's second key). No fixture exercises two Actions on one origin pair (10-06 has none; the S6 chain has one per
Finding). Question: should Lane A add private `_selected_recorded_at` (the selected event's `recorded_at`) to
`coverage.py::_actions` rows, with root bytes unchanged, before 1b's workflow-label tests?

## Q-1b-1 — RESOLVED by r1b (build spec "Run-1b rulings"); was blocking r1a2 item 4: Portfolio cursor signing key has no configuration seam

r1a2 item 4: "Use a server-held cursor signing key; refuse issuance if it is unavailable. ... Lane A owns the shared
`scope.py` encode/decode seam and configuration in a pre-1b handoff; Lane B uses it for Portfolio in 1b."
That Lane A seam was not built (the 1b dispatch names only `coverage.py::_selected_recorded_at` for Lane A), and no
signing-key configuration exists in the backend (`grep hmac|signing_key|secret_key` finds only
`evidence/gateway_access.py`'s verifier compare). Unruled: the key's source (environment variable name? settings
object?), its encoding/minimum length, how the development/test server gets one, and whether the router or the
service refuses issuance when it is absent (which status/code: 503 `ESTATE_STORE_UNAVAILABLE`, or another).
Question: give the literal configuration (name, encoding, dev/test default or none), the refusal status/code when
absent, and confirm which run/lane builds the `scope.py` seam (a Lane A pre-run before 1b continues, or 1b itself).
Not built: the HMAC, the 422 tamper tests, and the signed page-one-mode assertions in
`test_w303_portfolio_api.py::test_cursor_lens_window_cutoff_and_v1_token`.

## Q-1b-2 — RESOLVED by r1b (`Applied` by first match): `workflow_label` for an APPLIED Action with a non-VERIFIED terminal outcome

Closure 5 S7: "The table order is precedence", and the last row "Joined Action with none of the above, including
`NONE_AT_CUTOFF` or a non-VERIFIED terminal outcome" -> `No action yet`. A RESOLVED Action with outcome other than
VERIFIED normally reduces to `application_state=APPLIED` (lifecycle: APPLIED is never reverted), so strict first
match gives `Applied`; the "non-VERIFIED terminal outcome" clause then only reaches `NONE_AT_CUTOFF` (PENDING
matches its own earlier row). Built: strict table order (`portfolio.py::workflow_label`),
so APPLIED + RESOLVED/NOT_VERIFIED reads `Applied`; the test asserts only the unambiguous `NONE_AT_CUTOFF` case.
Question: is APPLIED + RESOLVED non-VERIFIED `Applied` (strict order) or `No action yet` (terminal clause wins over
the application rows)? Same question for PENDING + non-VERIFIED terminal, if reachable.

## Q-1b-3 — RESOLVED by r1b (private `_pending_guard`): r1a2 item 2 pending guard without a selected line is invisible to Lane B

r1a2 item 2: "Lane B uses the full selected Financials inputs, including the guard/withheld reason". The selector
(`financials.py::select_financial_scope` / `windowed_lines`, Lane A files) exposes per Site only
`_windows_covered: bool`; the guard/withheld reason survives only on a selected line (`eligibility="PENDING"`).
A cold `withheld` read with zero consequences, or an EV transient guard with no stored history (`continue` at
`windowed_lines` EV branch), yields no line, so Portfolio sees only `_windows_covered=False` and reports UNKNOWN,
not PENDING. Built: `portfolio.py::money_pending` = window uncovered and any selected line `PENDING`.
Question: should Lane A add a private per-Site `_pending_guard: bool` (cold `withheld` or EV `ERROR_PENDING`) to the
financial selector's Site coverage, root bytes unchanged, or is the line-based rule sufficient for the named
persisted variant (a)?

## P-1b-1 — RESOLVED by r1b3 (pure `test_money_table`; persisted `a_lineless_cold` is the line-less path only) (run 1b 3b, variant stopped): Q9 (a) "later cold accepted record and unsettled cold job" not produced

Producer step: clean `build_portfolio_fixture` (cold `excursion` + drain), then `fx.cold.advance_late()` (the W2-02
chain's late publication upload, no worker run), re-pinned read clock `max(db_now, latest cold recorded + 1us)`.
Actual Portfolio read (one-day 10-06, no `known_at`): `status=UNKNOWN`, F/E/M `PARTIAL/PARTIAL/PARTIAL`, cold
`coverage.sites` item `state=CURRENT`, `job_state=SETTLED`, `match_state=NOT_APPLICABLE`, selection unchanged
(`...0173`). Mismatched assertions: `status=PENDING`, cold `PENDING_RECOMPUTE`. No overlapping PENDING cold job
appears for the excursion case, and the PARTIAL comes from a Site not identified in this run. Not built: variant
(a) as specified. Built instead and passing: `a_lineless_cold` (fixture with `cold_drain=False`: the r1b Q-1b-3
line-less guard) -> `status=PENDING`, F/E/M `COMPLETE/COMPLETE/PARTIAL`, cold Site `CURRENT`, no cold line or
exclusion, W1 card `SITE_OWNED`. Question: which reviewed producer step gives (a) (a `late-reading` cold case in
the four-Site fixture? a worker-created overlapping job?), or is the line-less variant sufficient for (a)?

## P-1b-2 — RESOLVED by r1b3 (pure `test_settled_current_and_historical_bases`; `mg_historical_marker` stays a STALE control) (run 1b 3b): r1a2 item 1 persisted positive proof - the reviewed mini-grid marker producer is STALE

Producer: S4 `F01` (`CaseRunner`) then W3-01 `LATE` (`runner.step`, decided 2026-10-31), `k = runner.now`, at
least one PENDING `recompute_job` created by `k`. Portfolio `[2026-10-06,2026-10-07)` at `known_at=k`: status
`HISTORICAL`, Site `state=HISTORICAL`, `job_state=PENDING`, `match_state=COMPLETE`, **`source_freshness=STALE`**,
F/E/M `UNKNOWN`. The stale-source rule (not the marker) makes the Site U, so "a selected-as-of head remains
covered despite its outstanding job marker" is not shown persisted; the test asserts the observed stale control
and the before-head cutoff (`known_at=2026-10-01`: Site UNKNOWN, F/E/M UNKNOWN). Question: name a non-stale
historical mini-grid producer, or accept the pure `test_settled_current_and_historical_bases` as the proof.

## P-1b-3 — RESOLVED by r1b3 (pure W3-02 `test_w302_money_overlap_by_group_ids_and_citations`; no persisted overlap claimed) (run 1b 3b, variant stopped): Q9 (d) OVERLAPPING_BASIS has no persisted producer

The two EV Sites' heads cite their own Site's accepted evidence and technical intervals (W3-02 `two_ev_sites`);
no reviewed producer makes two otherwise eligible EV heads share a persisted technical/cited ID, and W3-02 proves
OVERLAPPING_BASIS only in the pure `test_w302_money_api.py`. Not built. Question: name the producer, or accept the
pure W3-02 proof plus the persisted INELIGIBLE/COMPARABLE/UNKNOWN_COVERAGE declines in
`test_ineligible_overlap_and_unknown_coverage_decline_total`.

## P-1b-4 — RESOLVED by r1b3 (fake-snapshot `test_financial_scope_pending_guard_without_line` + pure `test_money_table`) (run 1b 3b): persisted limits of the operating-cost and EV-pending proofs

(1) The fixture has the one and only W1 Site (`KOBO-001`), so COMPARABLE_GROUP, multiple operating-cost partitions
and UNPRICED operating cost are not producible persisted; `test_operating_cost_first_match_wins_across_partitions`
proves rule 3 (SITE_OWNED) against a COMPARABLE EV and an INELIGIBLE cold partition, and c1/c2 prove WITHHELD.
(2) No reviewed producer gives a persisted EV `ERROR_PENDING` (EV `PENDING_RECOMPUTE` pin with stored money
history) in the four-Site fixture; only the cold line-less guard is persisted (R3/Q-1b-3 EV half is the pure
`_GuardSnap` test). Question: accept, or name producers.

## P-1b-5 — RESOLVED by r1b3 (pure `test_money_table` line branch, guard absent/false; persisted demand removed) (r1b2 R4): the persisted false-guard plus selected PENDING-line case has no producer

r1b2 R4 asks the persisted late-revision test to add `_pending_guard=false` with an uncovered selected
`eligibility=PENDING` line. In `financials.windowed_lines` a cold/EV line becomes PENDING only from the same
`withheld` / `ERROR_PENDING` read that sets `_pending_guard` (r1b Q-1b-3), and mini-grid PENDING lines sit on a
covered window, so no reviewed producer yields that combination. The rule stays covered by the pure
`test_w303_portfolio_reduction.py::test_money_table` (`money_pending(uncovered, guarded)`). Question: accept the
pure proof, or name a producer.

## P-1b-6 — RESOLVED by r1b3 (pure `test_two_actions_one_exact_origin_latest_event_then_id_tie`; persisted stays false) (r1b2 R10): the persisted `origin_revision_selected=true` case has no window in the B4 chain

The B4 S6 chain's Action is created 2026-11-01; F01's origin revision is selected only in the one-day 10-06
window (which selects no Action: Actions are those created in `[from,to)`), and `[2026-10-06,2026-11-03)` at the
acceptance cutoff reads mini-grid Finding coverage UNKNOWN (no selected revisions). So the persisted test asserts
`false` (November window and the wide window); `true` is proved by the pure
`test_two_actions_one_exact_origin_latest_event_then_id_tie`. Question: accept, or name a chain whose Action and
origin revision share an assessed window.

## P-2-1 — RESOLVED by r2 (`G-portfolio-opportunity` registry gap + `gapCatalogue.ts` mirror + two `<MissingClaim as="span">` wrappers; check-all 11/11): inert opportunity CTAs versus the missing-claim scan
Closure 1 Q20 / mock ledger require two inert plain-text CTAs, `Review opportunity Finding · Not available yet` and
`Inspect physical headroom · Not available yet`, with accessible names ending `, Not available yet`, and say
"No `UnavailableEntry` is added; inert mock-only CTAs are ordinary labelled text." `tools/check-all.ps1`'s
missing-claim orphan scan (and its fixtures run) rejects exactly that copy at `frontend/src/estate/EstatePortfolio.tsx`
(`OpportunityPanel`, 4 hits: "untagged missing-capability copy ... register a mock_gaps gap and render it through
<MissingClaim gapId placement>"). Satisfying the scan needs a new registry `mock_gaps` entry (claim, boundary,
owner/allocation, `ui_placements`) mirrored in `frontend/src/ui/gapCatalogue.ts` - a registry decision, not a run-2
build choice. The page keeps the ruled literal text; check-all therefore fails 2 of 11 guards on this one cause.
Question: (a) register a `G-portfolio-opportunity` gap (two placements) and render both through `<MissingClaim>`
keeping the literal copy, or (b) another ruled treatment.

## P-3-1 — RESOLVED by r3 (two new open nodes `I-estate-portfolio-read`/`-ui`, four r3 panel rows, portfolio ledger `registry_dependencies`; registry checker exit 0, check-all 11/11, no checker change) (run 3): the four r2 Portfolio panel rows fail the dependency-registry checker
Inserting r2's four `panels` rows verbatim (before `actions:1`) makes
`node frontend/docs/architecture/check_v69_dependency_registry.cjs` fail in two places:
1. `portfolio: ledger and registry node IDs diverge` - `v69-screen-ledger.json` `portfolio` has no
   `registry_dependencies`. The checker forces its value (governed product for area `estate-aggregation` =
   `P-estate-area`; `node_ids` = de-duplicated `requires` in panel order). Adding that object clears this error, but the
   ledger edit was not named in r2.
2. `portfolio:1: missing UI or projection gate` (checker line 343: each panel's `requires` must include one
   `layer:"ui"` and one `layer:"projection"` node). Layers of the r2 `requires`:
   - panel 1 `A-estate-index-scope`(none), `I-estate-finding-root`(ui), `A-estate-action-summary`(none): no projection;
   - panel 2 `A-evidence-shared-projections`(none), `I-estate-evidence-root`(ui), `D-estate-comparable-sites`(none): no projection;
   - panel 3 `A-estate-comparability`(none), `I-mini-depth-read`(projection): no ui;
   - panel 4 `A-estate-projections`(none), `I-estate-action-root`(ui): no projection.
   Existing estate projection/ui nodes: projection `I-mini-depth-read`; ui `I-estate-{finding,action,evidence,money}-root`,
   `I-mini-depth-ui`. Peer rows use `I-action-read` / `I-capability-read` / `I-finding-index` as projection gates.
The rows and ledger edit were reverted (not committed); check-all stays 11/11 at the P-2-1 commit. Run 3 stopped here
per the dispatch rule; no captures were taken.
Question: (a) amend each row's `requires` (which projection/ui node per panel), or a new registry node; and
(b) confirm the forced `portfolio` ledger `registry_dependencies` (`P-estate-area` + panel-order union).

## P-3-2 (run 3, OPEN): `empty` (EMPTY_SCOPE) capture at 390 exceeds two card caps; matrix cannot scroll with zero Sites
Captured on the real API (`W303_ROUTER=capture`, `tenant=foreign`, fresh UUID; API 200 `EMPTY_SCOPE`, F/E/M
`EMPTY/EMPTY/EMPTY`, 0 rows, 0 Sites). `app-portfolio-empty.json` / `portfolio-empty-390-app.png`:
1. `card0 218>207; card1 218>207`. Card 0 is `OPERATING_COST:NO_LINE` with the large value line
   `No supported value for this window` (wraps to three lines at 175 px); card 1 shares the grid row so it stretches to
   the same 218. 1440 is within caps (`over=[]`); positive/partial/historical/pending 390 cards are 189/178.
2. The r2 success check "table/matrix internal scrolling at 390" fails for the matrix only: with zero matrix Sites the
   matrix is 328 = 328 (nothing to scroll). The Findings table scrolls (720>336); no document overflow (390/390).
All other empty checks pass: exact status, four named panels, five cards, matrix count 0, zero rows, no fixture Site
name/code in page text. Options (builder decides nothing):
- (a) accept item 1 as a recorded limitation (the cap derives from a money-valued mock card; NO_LINE copy is longer);
- (b) a CSS-only fix, as in run-2 reading 10: the NO_LINE value line at a smaller size at 390 (e.g. 16 px), then
  recapture all eight states;
- (c) a shorter literal NO_LINE value (copy change, owner/Architect wording).
For item 2: confirm the matrix-scroll requirement does not apply when the matrix has zero Site columns.
