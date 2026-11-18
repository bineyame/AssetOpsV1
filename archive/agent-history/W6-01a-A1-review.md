# W6-01a unit A1 review (fresh independent Claude reviewer)

Branch `task/W6-01a-global-incidents`, commits `ad1cefc1`, `801e5ad8`, `c5e45a67`; diff `git diff 1ac44fd2 c5e45a67`.
Judged against `.agent/W6-01-build-spec.md` A1 card, §1 (wire, parser, refusal table), §3.1 (G1-G6, Q3-Q9), §4 fixture clocks.

## Verdict: ACCEPT

No High or Medium finding. Four Low notes below; none blocks.

## Scope

Changed files: `backend/README-db.md`, `backend/assetops_backend/{global_work_api.py,main.py}`,
`work/{global_index.py,composition.py,adapters/postgres_global_read.py}`, `backend/tests/test_w601a_global_incidents.py`,
`tools/checks/configuration-persistence.ps1`, `tools/w601_seed.py`. All of them are on the amended A1 card.
The only other change is `.agent/W6-01a-phase-handoff.md`, which is a process record.

## Ruling-by-ruling check (verified against the code, not the handoff)

- **G1**: the `$pgReaders` block matches the literal exactly, and no other line in the guard changes.
- **G2**: the adapter, service, router and composition signatures match. `build_global_work_read` and
  `build_global_work_index_service` are literal and are in `__all__`. The `main.py` import and the mount directly
  after the W4 `build_work_router` are literal. `GlobalReadTx.site()` returns the merged W4 `_ReadTx` on the same
  connection, and nothing from `estate/adapters` is imported.
- **G3**: the README block follows the estate key, with the POSIX line and the commented PowerShell line.
- **G6(a)/(b)**: guards pass. `global_index.py` has no driver import and no `open(`.
- **Endpoint and parser**: authentication runs first and returns 401 with `Bearer`. The `from`/`to` checks give
  `INVALID_WINDOW`, an unknown or repeated key gives `INVALID_CURSOR`, and `known_at` and `limit` follow the W3
  literals. Every refusal body is `{code,message,rows:null,total_count:null}` with the messages from the refusal
  table. Without a service the route returns a typed 503; I confirmed this on the real `main.app` with no
  database.
- **Signed cursor**: uses the W3-03 HMAC pattern with a dedicated `ASSETOPS_WORK_CURSOR_KEY_HEX` that has no
  default. A missing or malformed key gives 503. The MAC is checked with `compare_digest` before the shape. A bad
  MAC or shape gives 422. A changed route, tenant, Site set, basis, window or selection gives 409. The cursor
  binds the route, the filter (null), the window, the six-digit K, `page_one_mode`, the token and the last
  4-tuple. The W4 unsigned cursor is not reused.
- **Q4**: on page one, EMPTY_SCOPE takes precedence. Otherwise the status is HISTORICAL if and only if an explicit
  `known_at` is earlier than `read_at`, and CURRENT if not. Continuations take their status from
  `cursor.page_one_mode`. An explicit `known_at` on page two must equal K exactly or be its whole-second copy
  with `microsecond==0`, otherwise 409. A cursor K later than `read_at` gives 409. The response `known_at` is
  `wire_time(k)`.
- **Ordering**: rows sort by `(-micros(root occurred_at), site_code_key, site_id lower, case_id lower)`. The full
  set is sorted before paging, and continuation compares against the complete tuple.
- **Q5**: the candidate SQL matches the estate predicate and order verbatim, with no `known_at` predicate. A null
  tenant gives zero candidates, and only admitted IDs feed the counts, `access_basis`, the rows and the cursor.
- **Q6**: the read time is `SELECT clock_timestamp()` taken once per snapshot. The override is called once instead
  and asserted UTC, and only the constructor sets it. This is the same form as `postgres_work_read.py:287-300`.
- **Q7**: links use the merged `_finding_link` and `_action_link`, projected to `{label,href}` and sorted in W4
  order. The request-code SQL is character-for-character the ruling, ordered by `created_at, id`, with no window
  filter.
- **Q8**: `links.site_incidents.href` always carries `from`, `to` and the response `known_at`, URL-encoded.
- **Q9**: the seed uses `W401_FIXTURE_SERVICE_PRINCIPAL_ID` (`service:w401-fixture`), set server-side.
- **Q3 provenance parity**: `select_incidents` lines 506-518 do the same steps as `site_index.select`, in the
  same order: `revisions[-1]`, `events`, `records[-1]`, `revision_links`, `link_selections(rid, lo, hi, k)`,
  `case_basis`, `provenance_dto`, then `missing_lineage` if and only if a selection has no lineage. The row DTO
  is the same as the Site row's, `missing_lineage` included.
- **Row keys**: exactly the 23 keys in the §1 incident row. The owner is the latest ASSIGN `payload.assignee`.
- **§4 clocks**: writes are at `11:59:00Z` and then one second apart. The historical successor and late writes
  are at `12:00:01Z` and `12:00:02Z`, and the cursor_change append is at `12:00:02Z`. Occurrence offsets are
  -2d3h for an incident, -2d2h for a request and -1d for a correction.

## Tests named by the card

All of the named tests exist: missing/malformed key; authorized/denied Site and two tenants; complete zero and
empty scope; the same-time UUID tie; the selected revision and ASSIGN; historical; cursor MAC and changed
selection (including denied-Site 409); and 401/409/422/503. The seven §3.1 tests are also present:
`test_missing_lineage_matches_site_row`, `test_continuation_status_follows_page_one`,
`test_page_two_known_at_wire_second`, `test_candidates_imported_before_to`, `test_linked_request_codes_order`,
`test_site_incidents_link_carries_response_known_at` and `test_read_clock_override_pins_read_at`. Each asserts
what its ruling requires. The parity test compares against a real W4 `WorkIndexService` row, not a copy.

## Findings (Low, non-blocking)

- **L1 (test gap, preference)** `backend/tests/test_w601a_global_incidents.py`: no global row with a lineage-true
  Finding href or any Action link is ever asserted. The helpers are reused rather than copied, so the risk is
  low. If wanted, add a lineage-true Finding row to the parity test.
- **L2 (weak assertion)** `test_w601a_global_incidents.py`, in `test_cursor_mac_and_changed_selection`: the
  check `[...] not in [[r["case_id"]] for r in one["rows"]]` is correct but indirect. Asserting that the page-two
  `case_id` is not among the page-one `case_id`s would read more clearly.
- **L3 (ordering nuance)** `global_index.py:385-386` and `:570`: the parser checks the cursor envelope before the
  key. A malformed cursor therefore gets 422 even when the key is missing, and the key is only read after the
  snapshot connection opens. Both still fail closed, and the order mirrors the estate parser. Recorded only.
- **L4 (artifact)**: §4 makes A1 the owner of `.agent/W6-01a-review-packet.md`, which does not exist yet. That is
  acceptable if it is meant to be assembled with A2's captures before slice review.

## Readings R1-R4 (no ruling; is it a real defect?)

- **R1**: not a behaviour defect. The seed imports `PostgresWorkStore(test_db_clock_override=...)` directly,
  because `build_work_service` cannot take the §4 ordered clock. `tools/` is outside every scan root, and the
  W4 tests use the same pattern. It is, however, a literal gap: G6(c) names only `build_work_service`, so the
  Architect should either widen G6(c) or add a clock kwarg in composition.
- **R2**: a minor literal gap. The §4 CLI list includes `linked` and A1 owns that CLI, but no A1 or A2 capture
  consumes `linked`, and the Finding and Action producers exist. Defer it or assign an owner.
- **R3**: not a defect. Row content and the provenance DTO depend only on the bound IDs and the lineage booleans
  (`case_basis`/`provenance_dto` read immutable link rows at K). The W4 cold/EV fence states never reach a
  global row or status.
- **R4**: not a defect. It matches §4 ("`empty_scope` injects a principal access callback denying all Sites").

## Checks run (by this reviewer, on `c5e45a67`)

- `tools/check-architecture.ps1`: passed. `tools/check-agent-workflow.ps1`: passed. `tools/check-all.ps1`: all 11
  guards passed.
- `pytest backend/tests/test_w601a_global_incidents.py -q` on the private base `assetops_w601rev_test` through the
  harness: **15 passed** in 173 s. The database was dropped afterwards and no process was left running.
- `main.app` with no database: `GET /api/work/incidents?...` returns 503 `WORK_STORE_UNAVAILABLE` with
  `rows:null,total_count:null`.

## Not verified

- I did not rerun the adjacent `test_w401_work_api.py` or `test_w301_estate_api.py`; the implementer reports 34
  passed with them.
- The full backend suite has not run on this revision, by dispatch.
- The frontend is out of scope for A1.

## Residual risk

The read issues per-case and per-Site queries across the whole tenant before paging (as W4 does per Site), so
cost grows with the number of cases in a 31-day window.
