# W3-01 pending rulings (q6, Lane B commit-2 run 2, 2026-10-20)

Branch `task/W3-01-estate-claim-action-roots` at `15dae742` (main merged: already up to date; Lane A
prerequisite `a75b0291` + fix r1 present). q1-q5 and the prerequisite r1 rulings are answered in
`.agent/W3-01-build-spec.md`. Lane B stopped before writing the estate read/API core on the two blocking items
below. Both come from the merged code, not from the spec text alone.

## Blocking questions

1. **Cold/EV selection grammar for an estate `[from,to)` window.** The estate window is whole UTC days
   (B5, up to 31 days). The W2 snapshots cannot select anything for such a window:
   - `ColdReadService._snapshot` (`analytics/adapters/postgres_assessment_store.py:1706`) selects a cold run only
     when `sel.window_start <= :lo AND sel.window_end >= :hi` (`:1728`). Cold selection windows are
     data-bracketed, five-minute-aligned series windows (`cold_windows`, `:934`; for example
     `contract-fixtures/w2/cold/normal.json` covers 19:00-20:05Z), so no selection covers a whole day.
   - `EvReadService._snapshot` (`:2288`) requires `sel.window_start = :lo AND sel.window_end = :hi` exactly
     (`:2311`). EV windows are exact bracket windows (`ev_windows`, `:1238`; `complete.json` covers 08:00-09:00Z).

   So `selection_on(c,t,s,code,from,to,known_at)` and `_snapshot(c,...,from,to,known_at)` called with the estate
   window always return "no selection", and every cold/EV Site would be `UNKNOWN` with no rows. B5/W5 and the
   token v2 text assume one `selection_id` per Site/domain. Options:
   (a) Enumerate every distinct cold (both analytics) or EV selected window that intersects `[from,to)` at the
       cutoff (latest `seq` per exact window, `r.knowledge_cutoff <= :k`). Call the existing
       `_snapshot(c,t,s,code,wlo,whi,known_at)` once per window on the estate connection. Union their selected
       Finding rows (`current_findings_on` / `findings_on`) and derive the Site state across windows by the
       estate precedence. `selected_assessment_revision_ids` becomes the union, which token v2's arrays already
       allow; `selection_id` would be null or the latest.
   (b) Use the W2 no-window grammar (`lo=None`, the latest selected window at the cutoff) once per Site. Include
       its rows whose episode intersects `[from,to)`, and mark the Site `UNKNOWN`/partial when that window does
       not cover `[from,to)`. Findings from earlier windows are then not shown.
   (c) Read cold/EV Finding heads directly (the latest `finding_revision` per Finding with
       `analytic_run.knowledge_cutoff <= :k`, as `ColdReadService._revisions` does) that intersect `[from,to)`,
       taking the Site state from (a) or (b).
   (d) Another rule.

   Please also say whether a window must be covered by `[from,to)` or only intersect it, and what state a Site
   gets when all its selections lie outside `[from,to)`: `CURRENT` with zero rows, or `UNKNOWN`.
2. **Mini-grid consequence and Cost on the estate connection.** B7/W7 require four things per selected mini-grid
   Finding revision: the selected `financial_consequence_revision` at the cutoff, the `consequence_read`
   `currentness.state`, `money_eligibility.state=ELIGIBLE` and `source_gate.permits_current_money`. None of these
   exists as a connection-taking read:
   - `ConsequenceReadService.read` (`financials/consequence_read.py:169`) uses the store's own transactions plus
     `derive(...)` and prices.
   - `MoneyEligibility.for_finding` (`financials/money_eligibility.py:176`) reads per-day windows through its own
     ports.
   - The source gate is the S3 Performance gate in `main.py`.

   W3-02 commits `0a` (`select_consequence_on`) and `0b` (`for_finding_on`) supply exactly these reads, but the
   Run 5 dependency amendment schedules them **after** W3-01 merges. Options:
   (a) Lane A pulls W3-02 `0a`/`0b` forward into a second W3-01 prerequisite, as in q5, and Lane B consumes them.
   (b) W3-01 commit 2 ships mini-grid rows with `consequence:{state:"UNKNOWN",amount:null,currency:null,
       source_revision_id:<selected revision id or null>}` (`Source unverified`) and an empty Cost lens with
       `No supported priced consequence in this selection.`. A follow-up wires them once W3-02 `0a`/`0b` land.
   (c) Lane B reads `financial_consequence_revision` directly in the estate adapter (the latest revision for the
       exact `finding_revision_id` with `created_at <= :k`). It shows `UNPRICED` or `No consequence recorded`
       from the stored row but never `PRICED`, because there is no eligibility or gate proof, so Cost stays
       empty.
   (d) Another rule.

   The source-gate question also applies: which read on the estate connection is the `permits_current_money`
   gate for a mini-grid Site?

## Readings (none built; to confirm with the answers)

3. **Authentication before enumeration.** `finding_api.Access` is `(request, site_code) -> None|401|403`. The
   router takes an `authenticate(request) -> None|401` seam (default development: admit) and checks it first:
   401, with no DB read. It then applies the per-Site `access(request, code)` filter to the snapshot's candidate
   imported Sites; per B6, estate roots never answer 403 or 404. The tenant comes from
   `ImportedSiteRegistry.tenant()`, never from the client. A missing tenant is an empty authorized scope
   (`COMPLETE`, zero counts).
4. **Explicit historical.** Estate `status=HISTORICAL` iff `known_at` is supplied and `known_at < read_at`
   (snapshot `now()`). At such a cutoff a mini-grid Site is `HISTORICAL` only when every requested day from
   `select_dispatch_days_on` is `available`, has a selection, and has its seq matched by the as-of matcher pass
   (and is not in that pass's deferred windows). Otherwise the Site is `UNKNOWN` and shows no mini-grid rows.
   L1's outstanding PENDING day marker is kept in `job_state` but does not demote a provable `HISTORICAL` Site.
5. **Mini-grid current state.** Per Site, over the requested days only:
   - any day unavailable or with no selection gives `UNKNOWN` (`match_state` is `MISSING` when there is no pass);
   - any day `PENDING`/`FAILED`, or a selected seq above the matched-through seq (or deferred), gives
     `PENDING_RECOMPUTE`;
   - any day `STALE` gives `STALE_SOURCE`;
   - all days `CURRENT` and matched gives `CURRENT`.

   The W1 index's continuity discovery beyond `[from,to)` (`finding_index.discover`) is not applied, because
   `select_dispatch_days_on` returns no segment intervals. Rows use the spec's plain `start<to AND end>from`
   intersection over the as-of canonical heads.
6. **Rows from unsettled Sites.** Mini-grid rows are shown only for a `CURRENT` (or provable `HISTORICAL`) Site,
   as the W1 index does. Cold/EV rows follow their W2 selected read, so selected rows are shown while pending.
   `total_count` and the summary counts stay null unless coverage is `COMPLETE`.
7. **`read_at` and the default `known_at`** are `SELECT now()` on the estate REPEATABLE READ connection (the
   transaction timestamp). The token uses six-digit UTC; the wire uses `Z` seconds.
8. **Action coverage.** A mini-grid Site is `CURRENT` with `match/job/freshness=NOT_APPLICABLE`,
   `selection_id=null` and `committed_watermark=null` (as on the W20 literal page). Cold/EV Sites are
   `NOT_APPLICABLE`.
9. **Action reduce input.** `site_window_on(c,t,s,from,to,known_at)` supplies the actions and events. The
   selected event is the latest `(recorded_at,id)` event, and the reduced state comes from
   `actions/lifecycle.reduce` as `actions/site_index.py` uses it. Verification counts read `verification_plan` /
   `verification_outcome` directly on the estate connection (`recorded_at <= known_at`).

## q7 (Lane A q6-prerequisite run, 2026-10-20): one question, non-blocking for the prerequisites

**Q7-1. Which cutoff bounds `selected_at` in the pinned cold/EV mode?** Run 6 Blocker 1 sets the selection
filters (`sel.selected_at`, `r.completed_at`, `ar.created_at <= :k`) on `:k` = the estate cutoff *clamped to the
Site's latest evidence watermark*. Measured on the W2 fixtures, every cold/EV selection is written after the last
decided evidence: cold `late-reading` watermark 10:46:40.131, selections 10:46:40.383/.518; EV watermark is the
replay's decided time (2026-10-06 09:00) while selections carry the DB clock (2026-10-20). With the clamped `:k`,
a live estate read therefore selects **nothing** (proved: `test_cold_day_intersection_selects_exact_windows`
asserts `selected_windows_on(..., watermark) == []`). The prerequisite keeps the two inputs separate:
`_snapshot(..., known_at, *, selection_cutoff, selection_seqs)` and `estate_snapshots_on(c,t,s,code,from_,to,
known_at, selection_cutoff)`; the tests pass `known_at` = clamped watermark (W2 grammar, no `EV_TIME_INVALID`) and
`selection_cutoff` = the unclamped requested cutoff. Options: (a) confirm that split (the clamp applies only to
`known_at`/`knowledge_cutoff`; selection filters use the requested estate cutoff); (b) another rule. Lane B's
estate core needs the answer; the prerequisite API serves either.
