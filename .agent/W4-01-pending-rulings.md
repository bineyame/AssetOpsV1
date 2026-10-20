# W4-01 pending rulings (batched, 2026-10-20, after commit 1 `4cb89c68`)

None blocks commit 1. Each needs an answer before commit 2 or 3 is built. No builder default is assumed.

1. **Client `authorization_basis` on a SERVICE command (commit 2/3).** Review closure B6 says "no
   `authorization_basis` accepted from the client"; S28 says the server "derives/overwrites" it; the request wire
   example still carries `actor.authorization_basis`. When a body includes `actor.authorization_basis`: refuse 422
   `WORK_INPUT_INVALID`, or accept, ignore and exclude it from the canonical hash? Which exact value does the server
   store for the development SERVICE principal (for example the `command_access` grant name)?
2. **Shared provenance patch owner (commit 2, Q11).** Has W3-01 commit 1 (`evidence/public_provenance.py`) merged to
   main, or reached a reviewed state the W4 branch should consume? If not, W4 commit 2 carries "that same reviewed
   patch": name the exact reviewed revision/diff to carry so the two lanes do not produce two variants.
3. **Rule-8 per-table anti-vacuity at commit 2.** S25 requires per-table INSERT counts for all 11 tables in commit 2.
   `maintenance_plan` and `operational_record` writers are in commit 2's service, but the routes arrive in commit 3.
   Confirm all 11 table INSERTs (including plan and operational record) land in `postgres_work_store.py` in commit 2.

## Run 2 (q2) - commit 2 stopped before commit (2026-10-20, branch head `f6fd3c4f`)

Questions 1-3 above are answered by "Run 1 rulings (q1)". Run 2 stopped on these; commit 2 is saved uncommitted in
`.agent/W4-01-commit2-partial.patch`. No builder default is assumed for either.

4. **Positive fixture evidence is received after the command's DB time (blocking).** The mandated closure-3 setup
   (`run_case(runner, CASES["F01"])` via `CaseRunner`) ingests through `PostgresEvidenceLedger(...,
   test_decision_clock_override=Clock(decided_at))` (`test_s4_finding_store_postgres.py:117-120`), so F01's accepted
   evidence has `received_at` = authored `decided` instants (2026-10-30/31). Real DB time is 2026-10-20. B7 makes
   `accepted_evidence.received_at <= command DB time` the acceptance cutoff, so the positive incident citing the
   public F01 row's `cited.accepted_evidence_ids` is refused 422 `WORK_LINK_SCOPE_INVALID` (observed on
   `w401b_test`). The same holds for any occurrence-bounds reading tied to those dates. Which is the contract: (a) a
   test-only DB-time override for the work store analogous to the ledger's `test_decision_clock_override` (name and
   seam?), (b) a different positive setup whose evidence is received before real time, (c) cite the pinned Finding/
   Action lineage without posting `cited_accepted_evidence_ids` (Q11 already unions them), or (d) another rule?
5. **Second in-scope Action for the wrong-Action-event vector.** The dry-read requires
   `test_foreign_asset_and_evidence_refuse` to refuse an event "belonging to another in-scope Action". After F01's
   Action is accepted, F02's `GET .../recommendation` returns `proposal: null` (the S6 prior-action trial rule), so
   the closure-3 accept route cannot make a second Action on F02 in this setup. Name the setup that yields a second
   Action (another authored case/asset, the S6 `authored_case` helper, or an SQL fixture row), or confirm the vector
   may use another existing Action-producing path.

## Run 4 (q3) - commit 3 partial (2026-10-20, branch head `5973ca09`)

Questions 4-5 are answered by "Run 2 rulings (q2)". Run 4 committed the six POST routes, the main.py mount and seven
API nodes (`5973ca09`), then stopped on these. No builder default is assumed.

6. **Link coverage vs. the frozen assessment-store file (blocking for detail GET).** Q9 has commit 3 create
   `work/link_coverage.py` and "extract the existing Cold/Ev `_snapshot(c,...)` query and pure status rules" from
   `analytics/adapters/postgres_assessment_store.py` (`ColdReadService._snapshot` :1607, `EvReadService._snapshot`
   :2189). This dispatch forbids editing that file (the W3-01 agent is changing it). Choose: (a) wait for W3-01's
   change to land, then extract; (b) call the existing instance methods `ColdReadService(...)._snapshot(c, ...)` /
   `EvReadService(...)._snapshot(c, ...)` on the caller's connection without editing the file; (c) move detail GET
   plus link coverage to commit 4 with the read adapter; or (d) another rule.
7. **Where link-coverage and detail SQL live.** Rule 1 lets only an adapter import the SQL driver, so
   `linked_coverage(snapshot, ...)` reads through a port. Does its SQL (and the detail read's REPEATABLE READ
   transaction) go in commit 4's `work/adapters/postgres_work_read.py` created now, or in `postgres_work_store.py`
   (the registered rule-8 writer)?
8. **Detail GET query rules.** For `GET .../work/cases/{id}?known_at=`: is an invalid/future `known_at` 422
   `INVALID_KNOWN_AT` (B8 names it for the list), is the default the snapshot DB time, and is its refusal body the
   mutation shape `{code,message}` or the list shape with `rows:null,total_count:null`?
9. **`test_list_refusal_has_null_rows_and_total`.** S25 lists it among the commit-3 API nodes, but the list route
   mounts in commit 4. Confirm it lands with the list route in commit 4.
10. **Development SERVICE principal (confirm).** `main.py` injects no server SERVICE principal, so every development
   write is 403 `WORK_WRITE_FORBIDDEN`; only tests inject `W401_FIXTURE_SERVICE_PRINCIPAL_ID`. Commit 5's stocked
   capture must then be generated by a test harness, not the dev server. Confirm, or name the dev injection seam.

Readings made in `5973ca09` (confirm at review): `command_access` 401 -> `UNAUTHENTICATED` "Sign in to read work.",
403 -> `WORK_WRITE_FORBIDDEN`; unknown Site is coded `SITE_NOT_FOUND` with the table's literal message; a non-JSON
body reaches the service as a non-object, so it is 422 only after the principal gate; `case_id` is a string path
param, so a malformed ID is 404 `WORK_CASE_NOT_FOUND`, not FastAPI's 422; a Site-store outage inside `scope()`
stays 500, as on the Action routes, because `main.py` passes only `WORK_UNAVAILABLE`; routes are `async` with
synchronous service calls, as in `action_api.py`.

## Run 5 stop: cherry-pick conflict (q3 ruling 6)

`main` merged cleanly (`ec91ed70`). Cherry-pick of the first prerequisite `a75b0291` conflicts in
`tools/checks/configuration-persistence.ps1` at the `$pgWriters` list: HEAD (W4-01 commit 2) appends `$workWriter`;
`a75b0291` leaves the list without it and adds the `$pgReaders` line below it. Apparent union (not applied):
keep `$workWriter` in `$pgWriters` and add the `$pgReaders` line. Cherry-pick aborted; no prerequisite applied;
commit 3 not resumed. Question: may the implementer resolve this as the union, then continue the remaining eight
picks under the same rule for any identical writer-list/reader-list conflicts?

## Run 5 resolution and readings (commit 3 `3353e858` + `99e5fea3`)

Coordinator ruling applied: the `a75b0291` guard conflict resolved to the union; the other picks hit only
`.agent/W3-01-phase-handoff.md` (HEAD kept). All nine prerequisites applied; SHAs in the handoff.

Readings taken (each implements a ruled item; please confirm or replace):
1. Cold/EV pin seq: the Finding revision's run window `(analytic_run.window_start, window_end)` is the exact stored
   window; the shared `selected_windows_on` (cutoff K, evidence cutoff E) gives each domain analytic's greatest
   eligible seq for that exact window; **all** domain analytics selected for that window are pinned in one
   `_snapshot` (as `estate_snapshots_on` does), because pinning only the Finding's analytic left cold probe
   freshness unknowable. The Finding's analytic must be among them and its selected assessment revision must equal
   `finding_revision.assessment_revision_id`; otherwise the pin is missing (UNKNOWN/LINK_SELECTION_MISSING).
2. Cold/EV link state is the shared snapshot `state`; mini-grid day mapping: unavailable or UNASSESSED -> UNKNOWN;
   PENDING, FAILED, STALE_PROJECTION, or CURRENT not covered by the matcher pass (or deferred) -> PENDING_RECOMPUTE;
   else CURRENT. A link's CURRENT becomes HISTORICAL when `known_at < read_at` (explicit earlier cutoff).
3. Mini-grid detail window is the pinned Finding's `[episode_start, episode_end)` (end widened by 1 us when equal).
4. Action link: `action_event` must match `(action_id, id)` and be recorded by K; its root's
   `origin_finding_revision_id`/`origin_finding_id` is read as the pinned Finding (created by K).
5. Per-link `selection_token` = `sha256:` of canonical JSON `{version:"work-link-selection/1",kind,id,selected_id,
   domain,pin,state}`; null when the pin is missing. Commit 4's Q8 fence may replace it with the W1 index fence.
6. `INVALID_KNOWN_AT` message (no literal in the refusal table): `'known_at' must be one UTC instant no later than
   the read time.`
7. Detail `finding_links`/`action_links` items use the request shape (`{finding_id,finding_revision_id}`,
   `{action_id,action_event_id}`); timestamps use the existing six-digit `m.iso`; `selected_revision.actor_id` is
   the stored `service:w401-fixture` (the B3 literal's `w401-fixture` predates Q28).
8. `analytics/composition.py` gains `build_cold_ev_selection_pins()` (composition only; the assessment store file
   is untouched) because rule 8 bans the adapter import from `work/composition.py`.

Questions (non-blocking for commit-3 review):
- q4-1. The F01 runner writes on a virtual clock from 2026-10-29, so a real-time detail read sees its pinned
  revisions as not yet created (coverage UNKNOWN). May the private test harness inject a test-only read instant
  into `PostgresWorkRead` (like the store's `test_db_clock_override`), or should F01 positive detail wait?
- q4-2. Commit 2 `finding_pairs_in_scope`/`action_pairs_in_scope` do not require the pinned revision/event to
  exist by `command_now` (only evidence is bounded). Should the command refuse a pin recorded after its DB instant?
