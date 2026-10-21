# W3-02 commit 1 - combined review (Evidence read/API, Lane A facade and mount)

Reviewer: fresh Claude reviewer (independent; authored none of the range).
Branch `task/W3-02-estate-evidence-money-basis`, head `1e50a8a4`. Range: Lane B `8d1e6325`, `c9e19695`, `1147519a`,
`9efa3914`, `1e50a8a4`; Lane A `71c00d59`, `cb39fdc9`. Authority: `main:.agent/W3-02-build-spec.md` closures 1-5,
0b/0c r1 rulings, "Commit-1 rulings (c1)", plus the handoff readings in `.agent/W3-02-phase-handoff.md` and
`.agent/W3-02-pending-rulings.md`.

## Verdict: REVISE

Two Medium findings (M1, M2). Both are small, local fixes in Lane B files with one focused test each. Everything
else checked holds. The Lows can ride along or go to commit 2.

## Checks run (by this reviewer, detached worktree at `1e50a8a4`, private DB `assetops_w302r_test`, now dropped)

- Focused pytest: `test_w302_evidence_api`, `test_w302_evidence_scope_snapshot_postgres`, `test_w302_evidence_ev_postgres`,
  `test_w302_w1_claim_limit_on_postgres`, `test_w302_pinned_facades_postgres`, `test_w302_w1_day_reduction`,
  `test_w302_pinned_facades`, `test_w302_estate_cursor`, `test_w301_estate_api`: **87 passed, 0 skipped, 0 failed,
  473 s** (JUnit 87/0/0/0). Note: the shared `.venv` has editable installs that point at the `AssetOpsV1` checkout
  (old main). A worktree run needs `PYTHONPATH=<wt>/backend;<wt>/contracts`, or Postgres modules fail collection
  with `ImportError` from the wrong `assetops_contracts`.
- `tools/check-all.ps1` in review2 at `1e50a8a4`: **11/11 passed** (architecture, estate guard self-tests,
  workflow, registry and so on). `check-architecture.ps1` passed. `check-agent-workflow.ps1` passed.
- Mount smoke test (my own script, worktree code): with `create_app()` and no `DATABASE_URL`,
  `GET /api/estate/evidence?from&to` gives 503 with
  `{"detail":{"code":"ESTATE_STORE_UNAVAILABLE",...,"rows":null,"total_count":null,"gaps":null}}`, and a missing
  `from` gives 422 `INVALID_WINDOW` with `gaps:null`. `build_estate_evidence_service(url)` gives an
  `EstateEvidenceService` over `PostgresEvidenceMoneyRead`, with `cold_site`, `ev_site` and `ev_money` wired and
  `claim_limits.store is assessments`. These are the same collaborators as `build_estate_read`.
- M1 probe (my own script, using the pure-test fakes): on a live basis, a pin whose W2 state is `HISTORICAL` gives
  cold/EV rows `raw_state/readiness UNKNOWN` while the response `status` and coverage stay `CURRENT`. Output is in
  M1.
- No full suite was run, and none is due before commit 4. No frontend change is in the range, so tsc and the
  frontend suite do not apply. No layout-sensitive surface.

## Findings

### M1 (Medium) - a live continuation turns cold/EV rows UNKNOWN after any new Site disposition (c1-q1, c1-q7)
`backend/assetops_backend/estate/evidence_money.py:221-228` (`_window_state`) maps any pin state other than
CURRENT, PENDING or STALE to `UNKNOWN`. On a live cursor page two, `k` is the cursor cutoff (earlier than the new
`read_at`). `evidence_cutoff` is `max(decided_at <= k)`, while the W2 `_snapshot` `watermark` is the Site's latest
`max(decided_at)` (`postgres_assessment_store.py` ~2406 EV, ~1822 cold). Any disposition committed between the two
requests therefore makes the pin `state == "HISTORICAL"`, even though the selected IDs, the token and the W3-01
coverage state (`coverage.py:_windowed`, which maps W2 HISTORICAL to CURRENT on a live basis) are unchanged. The
rows flip from FULL/LIMITED to `UNKNOWN`, the claim moves into `prior_selection`, and current gaps disappear. No
409 fires. Probe:
`CURRENT pin -> cold/ev FULL/LIMITED/CONTRADICTORY; HISTORICAL pin, live basis -> all UNKNOWN, status CURRENT`.
Ingest is continuous on live cold/EV Sites, so the flip happens on ordinary paging.
Why it matters: c1-q1 says the W2 `state=HISTORICAL` "means only that the row-local evidence cutoff is earlier
than the Site's committed disposition watermark; [it does] not decide estate currentness". c1-q7 says "every
displayed row state must remain stable across pages at the same selected IDs". This is the cold/EV counterpart of
the W1 relabel that c1-q7 fixed.
Fix: on a live basis, treat a pin `HISTORICAL` as the as-of selection. Take the row state from the Site coverage
state (PENDING/STALE/UNKNOWN as now, else CURRENT), not from the pin's row-local historical flag. Add a pure test
(a live basis with a pin state of `HISTORICAL` keeps the rows) and, preferably, a Postgres test: live page one,
append a disposition, page two at the cursor, and assert identical row states and token.

### M2 (Medium) - any W1 `ClaimLimitRefusal` becomes a whole-estate 409, not an UNKNOWN day (unclassified reading)
`backend/assetops_backend/estate/adapters/postgres_evidence_money_read.py:55-59` maps every `ClaimLimitRefusal`
from `claim_limit_on` to `EstateSelectionInconsistent`. After the W3-01 one-retry, the whole tenant's Evidence
root returns 409 `ESTATE_SELECTION_INCONSISTENT` ("Some records are being updated. Reload the list."). The
refusals include `UNSUPPORTED_RULE_VERSION` (422; `SUPPORTED_MODELS = ("dispatch-3.2",)`, while `dispatch-3` and
`dispatch-3.1` revisions were stored in earlier slices), `ASSESSMENT_REVISION_NOT_FOUND` (404) and
`REVISION_OUTSIDE_WINDOW` (422). One Site day with a selected revision from an older model then fails every estate
Evidence request whose window covers that day, for every Site, and does so persistently. A reload never clears
it.
Why it matters: closure 1 Q1/Q3 and closure 4 say an unreconstructable or unsupported W1 day is an `UNKNOWN` row
(`HISTORICAL_SELECTION_UNAVAILABLE`, null ceiling, no fabricated IDs). The 0b handoff reading 3 states "the estate
caller maps them to UNKNOWN". The commit departs from that reading without recording it as a pending ruling.
Fix: map the refusal to an `UNKNOWN` row for that day (raw reason in disclosure, no IDs, no current claim).
Reserve `EstateSelectionInconsistent` for a true lineage inconsistency (`ACCEPTED_LINEAGE_ABSENT`, 409) if the
Architect wants that one kept as a fence. Add a test with an unsupported-model or foreign revision that asserts a
200 with one UNKNOWN day and the other Sites intact. If the Architect prefers the 409, record that as a ruling.

### L1 (Low) - EV token `cited_accepted_evidence_ids` is not the full cited union (c1-q3(5))
`evidence_money.py:292-297` and `:370`: the token unions only the four display claims' `accepted_evidence_ids`.
The selected assessment's other citations (the supporting claims `SITE_POWER_CONTEXT`, `POWER_CONSTRAINT` and
`GROSS_TARIFF_SCENARIO`, and `read["evidence_ids"]` in general) are left out. c1-q3(5) asks for "the full exact
cited accepted-ID union". Fence impact is small: the citations are immutable per assessment revision, and that
revision ID is in the token. The token bytes still differ from the contract. Fix: add `read["evidence_ids"]` to
`_cited` for the token (row `source_provenance` can stay per claim, as closure 1 Q3 says). The
`if not parts` branch that cites all window evidence on a claimless row should cite nothing.

### L2 (Low) - W1 rows lose interval reasons in disclosure (state table, c1-q3(2))
`evidence_money.py:188-192`: `disclosure.reasons` is `reduced["reasons"]` (empty when the day is available) or the
projection's top-level `reasons` (also empty). `interval_ceilings` carries no `reasons`. As a result:
- a CURRENT `CONTRADICTORY` W1 day has no raw conflict reason on the row. The table asks for
  `Conflicting records; raw reason`. Historical days are covered by `historical_statements`.
- a PENDING or STALE W1 day has no labelled prior-selection disclosure. Cold/EV rows have `prior_selection`.

Fix: carry each interval's `reasons` in the disclosure constituents, and add `prior_selection` for non-current W1
days. Commit 2 needs both.

### L3 (Low) - historical W1 statements use a different time format from the label
The label is `wire_time(k)`, for example `2026-10-20T06:00:00Z`. `reduce_day` builds `historical_statements`
with `known_at.isoformat()` (`claim_limit_read.py` reduce_day, giving `...+00:00`), and those statements are passed
straight into `disclosure.historical.statements` (`evidence_money.py:202`). Cold/EV use the `wire_time` copy.
Fix: format in the estate projection (or rebuild the two literal lines) so that the copy is
`Historical as of {estate known_at}`.

### L4 (Low) - summary counts go null on a live page two
`evidence_money.py:380-390`: `complete` keys off `status`. On a continuation, `status` is the W3-01 presentation
label `HISTORICAL` (Run 8 ruling 2), so page two nulls the full/limited/none/unknown/limited-Site counts that page
one returned for the same selection. W3-01 q11 says totals come from page one's mode. Fix: key `complete` on the
basis mode (`not snap.basis_historical` plus the coverage states), not on the response label. Alternatively,
document that the UI reads cards from page one only.

### L5 (Low) - proof gaps (the tests pass, but these claims are not asserted)
- `test_w302_evidence_ev_meter_gap_from_unknown_meter_seconds` says in its docstring that the token carries the
  session revision IDs, but asserts nothing about the token. The pure test does prove that a change to the
  sessions alone gives a 409.
- c1-q7 is proved for `claim_limit_on` directly (Lane A Postgres test) and for page one's mode (pure). No estate
  test pages a live continuation whose cutoff is earlier than its read time. The `mini` fixture pins `read_at`, so
  this path is never exercised. M1's test would cover it.
- No test exercises `build_estate_evidence_service` or the `main.py` mount. The Postgres suites still use the
  test-scoped `evidence_read` stand-in. W3-01 has the same precedent, and my smoke test confirms the mount and
  the no-DB 503. Switch `evidence_read` to the builder, or add one `create_app` no-DB 503 test.

## Readings classified

- **R1 `GENERATOR_UNOBSERVED` copy per role: needs Architect.** W1 `_reasons` maps NOT_EVALUATED spans of every
  role to `GENERATOR_UNOBSERVED` (0b reading 5). The closure-2 literal table gives every such group the text
  `Generator state not observed` / `Record generator state` (`evidence_money.py:53`). A `feeder_demand` group
  therefore tells the user to record generator state. The 0b ruling ("each distinct typed role states what was not
  observed") suggests role-specific copy. The code follows the literal table, which is acceptable until a ruling.
  Raise this before commit 2's copy.
- **R2 METER_GAP from `unknown_meter` unlocks the energy row: confirm.** `evidence_money.py:305-306` attaches
  METER_GAP to `energy@...` whenever `unknown_meter` is true, even if `DELIVERED_ENERGY` carries no
  `connector_meter_delta` missing role. This is a reasonable reading, since unknown meter seconds bear on delivered
  energy. It does go slightly past c1-q3(1)'s "only through a constituent's missing role". Acceptable; confirm
  with the Architect.
- **R3 W2 `ClaimLimitRefusal` mapping.** Classified as M2.
- **R4 pin KeyError re-raised as 500 (`pinned_windows`).** Accept. This is the deliberate "programming error is not
  409" rule (W3-01 Run 8 ruling 9).
- **R5 a `CONTRADICTORY` row is in no readiness count**, so full+limited+none+unknown can be less than
  `capability_count`, while only `limited_site_count` is nulled. Accept as one reading of "null affected count".
  Record it for the commit-2 cards.
- **R6 `_window_gaps` (supporting-only EV codes) only on CURRENT windows, with `unlocks: []`.** Accept (c1-q3(1)
  and (2)).

## Verified as conforming

- Rows/windows: one `GENERATOR_SUPPORT@YYYY-MM-DD` row per intersecting day. Cold/EV give four rows per selected
  stored window with `@<ws>/<we>` six-digit keys; a Site without a selected window gets four unsuffixed
  placeholders. Grouping precedence is `CONTRADICTORY > NONE > LIMITED > UNKNOWN`, with FULL only when all
  constituents are FULL. Cold cites only its owning analytic. Nothing is borrowed across windows (pure test and
  Postgres test).
- W1: day reduction comes from `claim_limit_on` with `basis_mode` taken from the frozen `page_one_mode`.
  Rows cite the interval IDs, and the window revision appears in disclosure and the token only. The estate-basis
  historical label (c1-q1) applies to W1 and cold/EV. Historical rows keep their IDs, clear every current claim and
  produce no current gap groups.
- Lane A: `claim_limit_on(..., basis_mode=)` keeps the default direct-call behaviour and rejects an unknown mode.
  `capabilities_on` returns `unknown_meter` from one pinned ctx. Lane B now consumes it, and the private
  `_sessions` call is gone. The METER_GAP Postgres test (`missing-meter`) shows the gap.
- Token/cursor: `/2` via the shared `selection_token`. Evidence arrays override coverage. Consequence, Finding,
  Action and assumption arrays are `[]`. The token includes the window revision and EV session revision IDs.
  The empty-scope vector `5944cb...` and `df70eb...` match exactly. The cursor marker is
  `[site_code_key, site_id, capability_key]`. The fence runs before `resume_after`, and the absent marker is a
  422. Changed grant, changed selection and a session-only change each give a 409. A wrong-kind cursor gives a
  422.
- Refusals: auth comes first (no store call on 401), with `WWW-Authenticate: Bearer`. All codes carry `gaps:null`
  inside `detail` and have no top-level `rows`. The no-DB 503 holds, and W3-01 bodies are unchanged.
- Links: closure-5 B5 is enforced (`known == evidence_cutoff <= k`, `<= watermark`) with `cold.plain` times. The
  fallback is the base route with `Opens current Site view`. The Site code is encoded once. Postgres tests check
  the exact window and cutoff.
- Mount/composition: the builder is exactly as Lane B requested, the router is mounted after the W3-01 estate
  router, and no shell, registry or guard change was made.
- Tests are non-vacuous: the Postgres W1 test traps `_snapshot`, `_run` and `_connect_engine`. The cold and EV
  tests assert real windows (`assert windows`) and compare against independently computed reductions. The
  handoff records reverted mutations.

## Residual risk not named in the packet

- The shared venv's editable installs point at the `AssetOpsV1` checkout, so any worktree test run imports stale
  code unless `PYTHONPATH` is set. That can make worktree runs silently test the wrong revision.
- On page one of a live read, an EV/cold disposition written with `clock_timestamp()` after `SELECT now()` but
  visible in the snapshot can also make `known < watermark` (the 0c L2 edge). M1's fix covers this as well.
