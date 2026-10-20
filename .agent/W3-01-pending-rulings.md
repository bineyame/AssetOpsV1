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

## q8 (Lane B commit-2 core, 2026-10-20): readings built, none blocking; confirm at review

1. An unsupported `state` value is 422 `INVALID_LENS` (the refusal table has no state code).
2. The cursor carries its page-one cutoff, which is the token `known_at`. An explicit `known_at` must repeat it to
   the wire second; a default-cutoff page two reads live at its own read time, so any selection change since page
   one changes the token (409). `HISTORICAL` only when the request supplies `known_at < read_at`.
3. `PRICED` consequence adds `amount_low`/`amount_high` decimal strings (W7 interval); `amount` = `amount_low`.
4. No consequence revision is `UNPRICED` with a null `source_revision_id` (`No consequence recorded`); cold rows are
   `UNPRICED` with the stored cold consequence ID or null; EV rows `UNPRICED`/null (window money has no Finding pin).
5. Finding rows add `episode_start` and `status` (the row Site's state) for the B3 row tones.
6. Cold/EV pending: an estate-level overlapping open-job query with `created_at <= requested known_at` (live reads
   only); the W2 snapshot's own job query is bounded by the evidence cutoff and misses later-created work.
7. Episode bounds: cold `cold_episode.anchor_time` to `cold_episode_revision.upper_end`; EV `ev_session.anchor_time`
   to the pinned session revision `end_at`; a null end is open through `known_at`.
8. Mini-grid: any requested day without an available selection makes the Site `UNKNOWN`; freshness from day
   statuses; `selection_id` is the latest selected day's window assessment; `committed_watermark` is the Run 7
   evidence cutoff for every domain.
9. Refused pins (`LookupError` from `index_lineage_on` / `estate_snapshots_on`) and `ColdReadUnavailable` /
   `EvReadUnavailable` are 409 `ESTATE_SELECTION_INCONSISTENT` after one retry; DB failures are 503.
10. Summary basis is the lens set ignoring the state filter; `total_count` follows the state filter. Awaiting
    verification counts Actions matched by exact origin (Finding, revision) over the lens basis.
11. `covered_site_count` counts CURRENT/HISTORICAL; the Action root also counts NOT_APPLICABLE Sites as covered.

## q9 (Lane B commit-2 mini-grid tests, 2026-10-20): golden manifest blocked; one reading to confirm

1. **Golden manifest `w301-estate-golden/1` (blocking).** Every replay mints fresh UUIDs (KOBO-001's `site_id`
   differed on each run here), so a checked-in file that "pins exact IDs from public reads at creation" cannot
   match any later run, and the cold, EV and mini-grid replays each build their own DB, so no single estate body
   holds all three Sites. Options: (a) the golden pins bodies with symbolic refs (for example
   `{"$ref": "KOBO-001/F05/revision/3"}`), resolved at test time from public reads, with one branch file per
   domain; (b) a once-recorded reference artifact that no test compares; (c) deterministic fixture UUIDs (changes
   the W1/W2 harnesses, outside Lane B). Not built until ruled.
2. **Awaiting verification (reading, built as-is).** The estate counts an Action only while its frozen plan's
   later window is open at `k` (`later_start <= k < later_end`), not RESOLVED, and its origin
   (Finding, revision) is the selected head (q8 reading 10). In the only real S6 chain, the apply's settle
   re-revises F01, so the origin is never the selected head once a plan exists, and the card is always 0
   (`test_action_event_and_verification_counts_full_basis` pins 0 and is marked q9). The spec text reads "a frozen
   verification window and no terminal outcome". Options: (a) keep as built; (b) match by origin Finding with any
   selected revision; (c) also drop the open-window requirement (any frozen, unresolved plan).

## q10 (Lane B golden manifest, 2026-10-20)

Built: `backend/tests/fixtures/w3/w301-estate-golden.json` (`w301-estate-golden/2`) and
`backend/tests/test_w301_estate_golden_postgres.py::test_w301_golden_manifest_public_replay` (parametrized
`mini_grid`, `cold`, `ev`; each its own private DB). `mixed` ships `cases: []`, asserted by the validator.

1. **Mixed branch: one private DB is not reachable with the existing fixtures (blocking for `mixed`).**
   `test_w202_cold_replay_postgres.py:174-177` and `test_w205b_ev_replay_postgres.py:236-239` call
   `pg_harness.fresh_database()` inside `Chain.open()` (drops/recreates the DB), and the mini-grid `store` fixture
   (`test_s1_bindings_postgres.py:81-82`) empties `site`/`site_import`/`tenant`. Any second chain wipes the first,
   so the three Sites cannot coexist without changing fixture behaviour. All three use tenant slug `demo`, so one
   tenant is possible. Options: (a) a test-scoped `Chain` subclass / `fresh_database` no-op after the first open
   (cold, then EV, then the S4 runner on the same engine, no `store` truncation), owned by Lane B in the golden
   file; (b) a shared harness change to the W2 chains (`open(fresh=False)`), outside Lane B; (c) keep `mixed`
   empty and rely on the per-branch partial cases. Not built until ruled.
2. **Replay paths are not replay inputs (reading).** `contract-fixtures/w2/cold/normal.json` and
   `contract-fixtures/w2/ev/complete.json` are pinned expected manifests; the chains generate evidence from
   their scenario. The test maps each path's stem to the chain case (`normal`, `complete`). The mini-grid has no
   contract-fixture replay; its `replay_paths` is `backend/conversions/s4-finding-cases-v1.json` (the S4 case
   source `run_case` replays). Both `normal` and `complete` select windows with **zero** Findings at
   2026-10-06, so cold/EV cover the complete-empty, unknown, partial, historical, scope and NOT_APPLICABLE cases;
   rows, cursor/page two, changed-cursor, recurrence/withdrawal and pending live in `mini_grid`.
3. **Cases with no natural replay (reading).** No branch's replay produces `STALE_SOURCE`, `LEASED` or `FAILED`
   without fabricating rows; `pending` is covered (`kobo-late-accepted-delivery`, `PENDING_RECOMPUTE`,
   `job_state: PENDING`). Confirm, or name a replay (for example cold `missing-probe`, outside the q9 path
   literal) to add as a further branch case.
4. **Public basis for `$public` and the token rebuild (reading).** Site IDs resolve from `/api/estate/scope`;
   Finding/Action IDs, links and provenance from a separate unpaged, unfiltered estate read of the same
   root/window/cutoff (no Site-level finding-index/cold/EV routers are mounted). The `estate-selection/2` rebuild
   is an independent canonicalizer; scalars and Finding/event IDs come from the public rows/coverage, while the
   six-digit watermark and the four basis arrays come from the estate snapshot's `evidence_cutoff`,
   `selected_windows`, `dispatch_days`, `finding_lineage`, `consequence` and `action_basis` reads at the same
   cutoff (the wire carries neither). Cold/EV reads pin the snapshot `read_at` to a frozen DB-clock instant so a
   default cutoff is a known six-digit value. A changed-cursor case's expected is the literal
   `{"refusal": {"code": "ESTATE_BASIS_CHANGED", "status": 409}}`, outside the q9 200-body shape. Coverage Sites keep
   the wire `match_state` beside the projected keys (whole-response comparison). Confirm or rule otherwise.

## q11 (Lane A commit-2 integration, 2026-10-20): readings built, none blocking; confirm at review

1. **Typed UI DTO and q8/q9 copy: no Lane A-owned file exists yet (reading, nothing built).** `frontend/src` has no
   estate client, type or page (`grep` for `/api/estate`, `estate-finding-index`, `Awaiting verification`, `No consequence
   recorded`: no match). The spec puts `frontend/src/estate/{findingIndex,actionIndex,estateClient}` in commit 3, so the
   `estate-finding-index-2` DTO (`amount_low`, `amount_high`, `amount` alias, `episode_start`, `status`) and the q8
   ruling 4 / q9 ruling 2 copy land there. Commit 2 adds no frontend file, and none was created ahead of commit 3.
2. **Guard self-test home (reading).** `tools/checks/test_estate_guard.py` (pytest, run explicitly; not in the backend
   suite, whose Linux container has no PowerShell and whose JUnit check forbids skips). Each test writes one untracked
   probe module and deletes it: the reader probe uses the second `$pgReaders` path
   (`estate/adapters/postgres_evidence_money_read.py`, W3-02's, absent here), and the domain probe is
   `estate/_guard_probe_driver.py`. No tracked `estate/` file is modified. The test refuses to run if the probe path
   exists.
3. **`main.py` mount (reading).** `build_estate_router(build_estate_index_service(database_url()),
   registry_tenant(registry), access=development_access, unavailable=(SiteStoreUnavailable,))`, placed after the
   Site Action index router. `authenticate` keeps the router default (`development_authenticate`), and `access` is the
   same `development_access` the Finding router defaults to. Without a database the route answers 503
   `ESTATE_STORE_UNAVAILABLE` (checked ad hoc through `create_app()`; no committed app-level test).
4. **Dependency direction (reading).** `tools/checks/dependency-direction.ps1` needed no allowance: check-all passes
   with the new composition.
