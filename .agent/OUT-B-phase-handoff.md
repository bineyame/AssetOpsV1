# OUT-B handoff (partial, 2026-10-30): B1-B3 landed; B4 addendum 4 landed (f8012282); B4 Postgres test WIP (aaebaa7f). Resume at "B4 addendum 4 landed"

Branch `task/OUT-B-site-outcome-board`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-outB`. It is cut from OUT-A head `7b826e97` and has no main merge yet. Merge main in only when the coordinator says A has merged.

The contract is spec rev 3, `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\build-spec-outcome-sprint-2026-10-29.md`. The precedence is:
1. "Pre-flight rulings B" (:672) and its addendum 1;
2. the Slice B text (:741).

## Landed
- `8b2aaf1c`: `outcomes/status.py` and `tests/test_out_b1_status.py`.
- `6e5ff830` and `1efe4f8f` (B1 per-unit review REVISE, then accepted):
  - `site_outcomes/__init__.py`, `site_outcomes/board.py` and `tests/test_out_b1_board.py`.
  - Focused run (b1_board, b1_status, a1_outcome_map): 72 passed.
- The review is at `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\OUT-B1-review.md`.

## Packet notes so far (B1 deviations and readings)
1. `roll_up` takes `(outcome_key, state)` pairs.
2. `ActionFact` gains `workflow_label`, `verification_href` and `is_domain`.
3. `signals_extra` holds `SignalFact(signal_key, open, text, href)`.
   - `kind` is derived from `SIGNAL_ISSUE_KIND` (review L1).
   - board.py turns each one into status Signals through `outcome_roles`.
4. `SiteFacts.headline_money` is a B-Q14 passthrough.
5. A `settled` key that is absent means not settled, so the outcome is UNKNOWN.
6. `PlanFact.next_due_at` is a Site-local date, resolved by the composer.
7. Must not harm drops the NOT_MEASURED exclusion (addendum 1). The constant `MUST_NOT_HARM_EXCLUDES_UNMEASURED=False` also governs the Earlier CHECKED entry.
8. Readings:
   - Earlier text is "{code} · {title}".
   - Earlier order is Actions by code, then requests by occurred_at.
   - The headline fallback is the first open Finding by title that moves the lead outcome in the role the reason names.
   - A plan with no due information falls back to its state as the label, e.g. "Draft" (review L2).
   - The B-Q18 columns are exclusive (addendum 1a). Issues list open heads only (1b).
9. Review M1: a linked Finding that is missing from `facts.findings` raises AssertionError. "Not linked" applies only when `finding_ids` is empty.

## B2 still to do (after the rulings)
- Build `site_outcomes/mini.py` (SiteFacts from mini port results) and tests with fake bodies.
- M1b: every Finding referenced by a case or an Action goes into `findings`, closed ones included, with a test.
- Add a vocabulary-scan test over all board and status copy (review). Model it on test_out_a1_outcome_map test 5, which loads `frontend/src/test/productVocabulary.json`.
- Then B2 gets its per-unit review. After that come B3, B4 (per-unit review), B5 and B6.

## Port shapes (surveyed; anchors relative to backend/assetops_backend)
- **Mini overview** (`site_overview/read.py:114`):
  - `read(site_code, tenant_id, site_id, day, *, access_basis, source_open, source_reason, pinned)`.
  - Keys: `window{start, end, utc_date}`, `freshness.state` ("CURRENT"…), `money{state, eligibility{state}, amount_low, amount_high, currency, source_provenance}`, `assessment{state, limitations["CODE: text"], coverage, dispatch_intervals}` and `known_finding{id, revision_id}`.
  - It has no Site name or timezone.
- **Mini depth** (`mini_depth/read.py:338`):
  - `read(*, tenant_id, site_id, site_code, domain, lo, hi, known_at)`.
  - renewable takes 1 to 5 local days; the other domains take exactly one local hour.
  - It refuses with `MiniReadRefused(code)` or `MiniReadUnavailable`.
  - The body has `cards` (flat) and `site.timezone`.
  - Card keys:
    - renewable: `headroom_kw{low, high}`, `eligible_days`, `assessed_days`;
    - fuel: `opening_l`;
    - service: `delivered_load_kw`;
    - backup: `outage_count`, `start_success_count`.
  - Zone helpers are at `mini_depth/inputs.py:57/:83`.
- **Dispatch** (`analytics/composition.py:38`): `window(tenant, site, day)` gives `intervals[].result.portions_minutes{candidate, indeterminate}`.
- **Assumptions** (`financials/assumption_read.py:63`):
  - `series(t, s, "diesel_price_per_litre", valid_at=...)`.
  - Read `selection.state == "PRICED"`, then `selection.price{value, currency}`.
- **Finding index** (`analytics/finding_index.py:262`):
  - Build the request with `parse_request("mini-grid-dispatch", start, end, ...)`, which allows at most 31 days.
  - Row keys: `finding_id`, `finding_revision_id`, `title`, `lifecycle` and `links.selected_revision`.
  - Rows carry no confidence and no asset. The mechanism is the constant `FINDING_MECHANISM` (:37).
- **Action index** (`actions/site_index.py:160`):
  - Row keys: `action_id`, `action_code`, `origin{finding_id, finding_revision_id}`, `selected_event.id`, `state{application, resolution{state, outcome}}` and `links`.
  - Rows have no title and no workflow_label inputs.
- **Verification** (`actions/verification.py:966`): `summary(t, s, code, action_id)["state"]`.
- **Foundation change**: `ActionService.action(...)["change"]["links"]["self"]`.
- **Work** (`work/site_index.py:309`):
  - `read(t, s, code, kind, ListRequest(start, end, limit, known_at, cursor))`.
  - Row keys: `case_id`, `code`, `title`, `state`, `asset_id`, `asset_label`, `finding_links[{finding_id}]` and `occurred_at`.
- **Preventive plans** (`work/global_index.py:388`):
  - `select_preventive(gx, t, sites, lo, hi, known_at)` returns `[{wire}]`.
  - wire keys: `canonical_plan_id`, `code`, `title`, `trigger_kind`, `next_due_at` (ISO), `next_due_hours` (decimal text), `state` and `asset_id`.
- **Limitation plain text**: `analytics/plain.py:80` `ALTERNATIVE_LABELS[code]`.
- **Source words**: `estate/placement.py:54` `_SOURCE_TEXT`.
- **Portfolio action rows** (`estate/coverage.py:~280-330`):
  - The estate-shaped Action has `action_title = f"Action {code}"`, `application_state`, `resolution_state` and `verification_outcome`.
  - `workflow_label` is at `estate/portfolio.py:137`.

## Open questions sent to the coordinator (B2 blocked)
These are Q-B2-1 to Q-B2-6 in the message of 2026-10-30.
1. Action title.
2. workflow_label inputs.
3. Finding confidence.
4. Finding window and the M1b linking set.
5. The settled proxies.
6. The Site timezone source.

## Rules carried
- Heavy jobs need the coordinator's go first: measure-mock-panels, full vitest, `-Tier all` and captures.
- Use test DBs only, named `assetops_out_b_…_test`.
- Kill processes by PID only.
- No execution-policy override.
- Focused pytest: in PowerShell, set PYTHONPATH from the task file, then run `..\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider <file>` from `backend/`.

## Since B1 (2026-10-30)
- Main (slice A, 32adae2f) merged in at 6dbf723f.
- Packet must mark register row R529 (Portfolio card site dots, D5) resolved once B6 fills the dots.

## B2 landed (commits 7ad1a040 board addendum 2, then the mini composer commit)
- board.py: Action items read the code only; Must-not-harm "... when {code} is verified ..."; `FindingFact.in_window`
  gates signals/issues/headline/earlier-empty; unresolved links kept under PROTECT_ASSET with
  " · linked finding outside this view" (in-hand state label, earlier result label); `unresolved_links(facts)`
  feeds the composer's diagnostics (M1 AssertionError removed). `SiteFacts.date_suffix` for UTC-fallback dates.
- mini.py: `MiniPorts` (12 callables bound by B4), `compose(ports, site_code, day, site_timezone)` ->
  `MiniComposition(facts, read_state, failed, diagnostics, window, timezone)`. Tests: test_out_b2_mini.py,
  test_out_b2_vocabulary.py (proved non-vacuous by injecting a raw code into mini copy).
- B4 must bind: estate port returning `{site_cov, findings (select_finding_scope rows), actions
  (select_action_scope rows)}` for one Site over the work window; paging ports take a cursor; `plans` returns
  DRAFT preventive wires for this Site; `readiness(lo, hi)` -> FULL/LIMITED/NONE/UNKNOWN.

## Packet notes added in B2 (readings)
10. Depth windows are built from the route's Site record zone (`site.timezone`, as mini_depth_api does); local
    dates use the depth body's `site.timezone`; if any depth read is refused, UTC + " · UTC (Site time zone
    unavailable)". Hourly domains (fuel, service, backup) read the local noon hour of the local day.
11. MG-1 and MG-5 need all four depth reads (B-Q6 literal). MG-2 needs dispatch; MG-7 readiness not UNKNOWN/None.
12. Limitation plain text: leading code, else a code named in the detail, through `ALTERNATIVE_LABELS`; else generic.
13. Work window `[day_end - 31 d, day_end)` for Finding index, Action index, estate, work and plans.
14. Verified results: one contributor per mini Action by code. Earlier CHECKED entry: "... checked as safeguards
    in {code}". Generator-use confidence: the lead in-window open Finding's placement confidence.
15. An Action whose estate row is missing reads the NOT_LOADED label; `open` then comes from the index resolution.
16. Open question for B4: the estate port needs a thin one-Site method beside `site_readiness` (two estate methods,
    B.6 says one).

## B3 port survey (done, nothing built yet). Resume here: write site_outcomes/cold.py, ev.py and tests
Anchors are relative to backend/assetops_backend.
- **Cold overview**: `analytics/cold_site_reads.py:314` `overview(t, s, code, lo, hi, known_at)`.
  - Body: the envelope (`site_id`, `window{from,to,known_at}`, `currentness{state,...}`, `limitations`) plus `status`, `objective`, `needs_attention`, `cooling`, `maintenance`, `temperature_summary`, `backup_summary`, `causal_strip`, `findings`, `consequence_summary` and `links`.
  - `objective{policy_low_deg_c, policy_high_deg_c, room_asset_id}` (:369).
  - `backup_summary{attempts, observed_success, observed_failure, unknown}`. Success means `observed_success > 0`.
  - `cooling{state, text, limitation}`. The state is CONTRADICTORY, LIMITED or UNAVAILABLE. It is LIMITED whenever any chain exists, and no state means "restarted".
  - `causal_strip` is a list of `{step, state}` with state OBSERVED, MISSING or CONTRADICTORY. MISSING marks a gap step. The list is `[]` when there is no chain.
  - `needs_attention` is a list of `{code, text, link}`. The codes are COLD_RECOMPUTE_PENDING, COLD_PROBE_GAP, COLD_START_FAILURE, COLD_TRANSFER_UNKNOWN and COLD_POLICY_MISSING.
  - The overview's `findings.items` carry no lifecycle and no mechanism. `consequence_summary.amount` is always null for cold.
  - **The body has no Site time zone.**
- **Cold findings**: `postgres_assessment_store.py:2361` `findings(t, s, code, lo, hi, known_at, cursor, limit)` returns `{items, next_cursor}`.
  - Item keys: `finding_id`, `kind` (EXCURSION→COLD_EXCURSION, START_RESPONSE→COLD_START_FAILURE), `subject_asset_id`, `revision_id`, `lifecycle`, `title`, `claim`, `episode_bounds{start{earliest,latest}, end{earliest,latest}}` and `links.finding`.
  - The EXCURSION claim carries `peak_observed`.
- **EV overview**: `ev_site_reads.py:595` `overview(t, s, code, lo, hi, known_at)`.
  - `energy{complete_kwh,...}`. `denominator` holds `_EV_COUNT_KEYS`; whether `completed` is among them is unconfirmed.
  - `site_power{observed_peak_kw, configured_limit_kw}`.
  - `findings.items{finding_id, revision_id, session_id, title}`.
  - `needs_attention` is a list of `{code, text, link}` with codes PENDING, FAULT_ABORT, INCOMPLETE_SESSION, METER_OR_SOURCE_GAP and TARIFF_MISSING. **It carries no counts.**
  - `consequence_summary{state, amount, currency}`.
  - **The body has no time zone.**
- **EV findings**: `postgres_assessment_store.py:3342` `{items, next_cursor}`.
  - Items are SUPPORTED only. Keys: `finding_id`, `revision_id`, `title`, `lifecycle` and `links`.
  - There is one mechanism, EV_INTERRUPTION (`analytics/ev.py:32`).
- **EV depth**: `analytics/ev_depth.py` `EvDepthReadService.availability|energy|health(t, s, code, lo, hi, known_at)`.
  - Health rows: `{kind, label, asset_code, condition_state, observation}`. The CONNECTOR_FAULT row has `condition_state` NEEDS_INVESTIGATION (:21-23).
  - Availability `connectors[]`: `{label, known_unavailable_seconds, unknown_seconds, spans[{from, to, state}]}`, where an unknown span has state UNKNOWN.
- **Domain action index**: `work/domain_action_index.py:375` `index(t, s, code, IndexRequest(start, end, limit, known_at, cursor))`.
  - Row keys: `action_id`, `action_code`, `domain`, `title`, `origin{finding_id, finding_revision_id, href}`, `state` (always "OPEN" for domain rows) and `links.action`. W1 rows have `title=None` and must be ignored (B-Q21).
- **Refusals**: cold raises ColdReadUnavailable; EV raises EvReadUnavailable or EvReadRefused; work raises WorkRefused or WorkStoreUnavailable.
- **Mismatches to raise with the coordinator before building B3:**
  - (a) Cold "Cooling recovery": no restarted state exists. Proposal: on LIMITED, render "Restarted with power; comparison incomplete", with confidence "Medium".
  - (b) There is no cold or EV zone in either body. Proposal: use the route Site record's `timezone`, as mini does, or else fall back to UTC.
  - (c) EV session counts: `needs_attention` has none. Proposal: count via `denominator`'s keys, which the builder confirms first.
  - (d) The EV findings list is SUPPORTED-only, so closed Findings linked by cases cannot be supplied. They fall under the "outside this view" rule.

## B2 fix round landed (7615977e; sent to coordinator for check, no verdict received yet)
- M1 (addendum 3): `board.finding_moved_outcomes(domain)` (mini MG-2, cold CC-1/CC-6, EV EV-1/EV-3) are unsettled when the
  Finding source is; `SiteFacts.findings_settled` -> `board.NOT_LOADED_LINK_SUFFIX`. Mini: finding_index refused/failed, or
  any page `status` in FAILED/STALE/PENDING (UNASSESSED ok) -> "finding_index" in failed (PARTIAL). Tests beside
  `test_degrade_only_ports_never_set_unknown`; proven non-vacuous.
- L3 missing estate row -> "estate" in failed + `(action_id, mini.ESTATE_ROW_MISSING)` in diagnostics. L5 assertion in
  b1_board. L7 `mini.plural` everywhere (reading: "1 of 1 well-observed day", noun follows assessed_days; board plan label
  "Due at 1 operating hour"). L1 public `estate/portfolio.py` `action_for` alias + local `mini.SOURCE_TEXT` (equality test).
  L2 `mini_depth/inputs` helpers. L4 vocab scan translates `\p{L}`/`\p{N}` and raises on others. L6 `mini.price_text`.

## B3 landed (a740b6c6)
- `site_outcomes/cold.py` (`ColdPorts`, `compose(ports, site_code, lo, hi, site_timezone)`) and `site_outcomes/ev.py`
  (`EvPorts` incl. single `finding(fid, lo, hi)`, `health`, `availability`). Both return `mini.MiniComposition`.
  Shared helpers now public in mini.py: `Reads` (pages(key=...)), `case_fact`, `plan_fact`, `utc`, `site_zone`, `num`,
  `plural`, `day_month`, `not_available`. `cold.domain_action` builds domain ActionFacts (title None rows ignored, B-Q21).
- Tests `tests/test_out_b3_cold_ev.py` (16); vocab scan covers cold/EV COPY and compositions (plant proven).
- Focused run (b1_board, b1_status, b2_mini, b2_vocabulary, b3_cold_ev, a1_outcome_map): 116 passed.

## Packet notes added in B3 (readings)
17. Cold/EV settled base: overview `currentness.state` in (CURRENT, HISTORICAL) - a pinned read is settled. Evidence
    outcome (CC-7/EV-7) also needs readiness not UNKNOWN; Finding-moved outcomes need the Finding source (M1).
18. Cold and EV Finding lists are read over the board window [lo, hi) (the selected assessment); EV single reads use the
    same window. Work, domain Actions and plans use the 31-day work window ending at hi. Cold `in_window` from
    `episode_bounds`; EV list items are in window.
19. Cold: empty `causal_strip` -> chain contributor "Not available yet · no power interruption in this window" and the
    Assure headline "No verified result yet" (neither "fully" nor "partly" reconstructed is true without a chain).
    Cooling state missing -> UNAVAILABLE text. Plan match: `asset_label` type part GENERATOR / COMPRESSOR
    (`sites/cold_foundation.py:34-42`); RUN_HOURS plan without date -> "due at {h} operating hours".
    Excursion headline minutes: shortest = end.earliest - start.latest, longest = end.latest - start.earliest.
20. EV: fault = health row kind CONNECTOR with condition_state NEEDS_INVESTIGATION (`ev_depth.py:173-205`; no
    CONNECTOR_FAULT kind exists); payloads are under body["health"]["rows"] and body["availability"]["connectors"].
    Durations "{h} h {m} min". Status gap stamps "d MMM HH:MM" local. Site power with null peak and a limit:
    "{limit} kW import limit declared; peak not read", Declared chip. "Investigate connector {label}": faulted connector,
    else the first out connector; href the linked domain Action, else the lead Finding; omitted without a label.
    A refused single read sets ev_findings failed and unsettles (M1); None -> outside-this-view.
    Cold/EV contributors carry no href except EV Assure energy billed (spec gives no href column).

## B4 next (resume here)
- `site_outcomes/read.py` SiteOutcomeBoardService binding MiniPorts/ColdPorts/EvPorts per §B.3; `composition.py`;
  `outcome_api.py` (board route + estate summary); `main.py:569`; `EstateEvidenceService.site_readiness`;
  `EstatePortfolioService.site_work_rows` (addendum 3 item 16, conditions 1-2); `tests/test_out_b4_imports.py`;
  `tests/test_out_b4_board_postgres.py` (assert real estate rows match the b2 fake keys incl. `_raw._selected_recorded_at`,
  and the Kobo Cost Must-not-harm line on the real fixture). Cold findings store signature
  `findings(t, s, code, lo, hi, known_at, cursor, limit)`; EV single `finding(t, s, code, finding_id: UUID, lo, hi,
  known_at)`; `EvDepthReadService.availability|health(t, s, code, lo, hi, known_at)`; domain index
  `index(t, s, code, IndexRequest(start, end, limit, known_at, cursor))`. B4 gets a per-unit review.
- Then B5, B6 (R529 resolved when B6 fills Portfolio site dots; register rows R540-R551), packet, closeout.

## B4 landed so far (cd6b2e62, 6efe8da5) - NOT yet sent for per-unit review (Postgres test missing)
- `site_outcomes/read.py`: `SiteRef` (from `registry.imported`: tenant_id, id, site_code, name, site_type, timezone),
  `BoardServices` (every service optional; missing -> `PortUnavailable` -> PARTIAL), `SiteOutcomeBoardService`
  `.mini_ports/.cold_ports/.ev_ports` (bind services; all bodies `jsonable_encoder`ed except estate rows),
  `.compose`, `.board` (wire §B.1; private `_short_values` stripped by the route), `.summary` (serial, caller order,
  failure -> UNAVAILABLE + 4 UNKNOWN rows, `short_value` only on GROW led by MG-1 in OPPORTUNITY), `mini_summary_day`.
  Requests are built with the routes' own parsers from wire strings (finding index domain "mini-grid-dispatch",
  limit None = default page, cursor from `next_cursor`). Cold/EV with no from/to: one overview read with (None, None),
  its `window{from,to}` is used. Gates: dispatch port needs `performance_gate` open, finding index needs
  `basis_aware_gate` open (else port fails); mini overview port uses composition.overview_source (empty-legacy basis
  or S2 `imported_reads.scope`, then gate + `basis_reason`, as site_overview/route.py:139-158).
- `site_outcomes/composition.py` `build_outcome_board_service(url, **instances) -> (service, dispose)`; opens only
  `build_global_work_read(url)` (preventive plans via `select_preventive` in its `snapshot`, filtered to the Site).
- `outcome_api.py` `build_outcome_router(service, registry, estate=, tenant=, access=development_access)`: board route
  (401/403, 503 SITE_STORE_UNAVAILABLE, 404 SITE_NOT_FOUND incl. no-board Site type, mini `selected_day` + pin
  422s, cold/EV PARTIAL_WINDOW/INVALID_WINDOW ≤31 d, `known_at`), summary route (estate authenticate, `parse_request
  ("scope")`, `estate.scope(...)["sites"]` order, estate refusal bodies).
- `main.py`: hoisted `imported_reads`, `cold_site_reads`, `finding_index`, `finding_index_gate`, `action_index`,
  `estate_portfolio`, `work_lists`, `domain_action_reads` (walrus), `assumption_reads`; router included after the
  financial read router (assumption service is built there) - record in packet ("next to the estate router" moved).
- `estate/evidence_money.py` `site_readiness(t, site_code, from, to, known_at=None)`; `estate/portfolio.py`
  `site_work_rows(...)` (kind "findings", so no Portfolio cursor key needed) - both admit only that site_code.
- `mini.MiniComposition.short_values` (default {}), mini sets GROW "{lo}–{hi} kW unused".
- Tests: test_out_b4_imports.py (3, non-vacuous probe built in), test_out_b4_read.py (4). Focused b1-b4: all pass.
- Smoke: `TestClient(create_app())` without DB -> board 503 SITE_STORE_UNAVAILABLE, summary 503 ESTATE_STORE_UNAVAILABLE.

## B4 resume: `tests/test_out_b4_board_postgres.py` (then message coordinator for B4 review)
- Kobo: reuse `tools/s602b_test_scoped_cases.py` `build()` steps (test-module builders: `test_s4_finding_store_postgres`
  CaseRunner/run_case, `test_s6_action_store_postgres.CASES` F01/F02, `test_s6_verification_plan_postgres.verifying`,
  `test_s6_verification_evaluator_postgres` complete_windows/bound_plan/evaluate) for `guardrail` and `estate`; serve via
  its `pinned_app(spec)` pattern (patch `main.build_action_service` clock + `_pin_read_clock`, `_cursor_key()`, then
  `TestClient(lab_app.app)`); GET `/api/sites/KOBO-001/outcome-board?date=...`.
  - F01 episode 2026-10-06 08:00Z; Action accepted ~2026-11-01, plan/eval to 2026-11-02 (CLOSED 11:00). Action index
    membership = created_at in window; work window [day_end-31d, day_end). Board day 2026-10-06 sees F01 in window but
    not the Action (created later); a Nov day sees the Action but F01 is out of `in_window` (no issue/signal). Pick the
    day per B.7 #3 by tracing; record actual states (B.7 #2 rule: never silently change expectations).
  - Assert real `site_work_rows` keys ⊇ fake (`test_out_b2_mini.py:44-49`): findings `finding_id, finding_revision_id,
    lifecycle, source_provenance, consequence, _episode_end, _mechanism`; actions `action_id, source_finding_id,
    source_finding_revision_id, application_state, resolution_state, verification_outcome, _raw._selected_recorded_at,
    _raw._verification_window` (index.py:168 wraps coverage row as `_raw`; coverage.py:324 has `_selected_recorded_at`).
  - Assert Cost Must-not-harm "Reliable service and battery and generator life ..." + verification href (guardrail).
- Cold w502 `positive` (`tools/w502_cold_work_walkthrough.py`), EV w504 `positive` (`tools/w504_ev_work_cases.py`,
  `_declare(URL, "positive", ...)` used by test_w504_ev_work_producer_postgres.py:70). Expected states in B.7 #2.
- Cost check: time the mini board (finding index runs dispatch.window per day over 31 days); record in packet.
- DBs `assetops_out_b_<x>_test` only; run via `toolsun-host-tests.ps1 -- backend/tests/test_out_b4_board_postgres.py`.

## B4 addendum 4 landed (f8012282) - resume the Postgres test below
- `outcome_api.build_outcome_router(..., work_access=development_access, cold_disclosure=, ev_disclosure=)`
  (`allow_disclosure` defaults from `cold_assessment_api`). `admitted()` = `access or work_access` (first refusal,
  401/403 before lookup); `disclosed(ref)` after the 503 service check -> 403 `COLD_SOURCE_DISCLOSURE_FORBIDDEN` /
  `EV_SOURCE_DISCLOSURE_FORBIDDEN` (the gates' own codes); summary admit = `admitted(...) is None`, refused-disclosure
  Sites dropped after `registry.imported`. `main.py:626` passes `work_access=site_read_access` (comment: cold/EV
  routers get no disclosure arg, so defaults).
- `read.py`: `BoardServices.clock` and the composition clock wiring removed; price `recorded_at=known_at` (#4).
  `compose` wraps cold/EV `ports.overview` (dataclasses.replace) to capture body `window.known_at`; window
  `known_at` = request's, else overview's (cold/EV), mini null (#5). Overview still never gets the resolved cutoff.
- Tests: `test_out_b4_route.py` (5; non-vacuity shown: reverting `admitted`/`disclosed` -> 3 failed), read tests +2.
  Focused b4 route/read/imports: 14 passed.
- Packet: gate list (#6): overview = S2 source + perf gate + basis_reason (as route); dispatch = performance_gate;
  finding index = basis_aware_gate (route 409 -> port PartUnavailable); action detail/verification/action index/
  assumption series/mini depth: routes pass no gate flag (`source_open` is only on recommendation/accept, which the
  board does not read); work lists / domain index / global work: WorkGate read_scope only (= work_access at the
  board); cold/EV reads: gate = access + window + Site type + disclosure (board route does access, window, disclosure).

## B4 Postgres test WIP (aaebaa7f) - `backend/tests/test_out_b4_board_postgres.py`
- Runner: `tools/run-host-tests.ps1` is blocked by execution policy (no override). Equivalent sh wrapper: PYTHONPATH
  = worktree backend;contracts;simulator;gateway;host;field, ASSETOPS_TEST_DATABASE_URL default
  `.../55432/assetops_test`, `plan2/.venv/Scripts/python.exe -m pytest <file> -q -s -p no:cacheprovider`.
- Kobo: `app_env` re-clones (`pg_harness.fresh_database`), child `-c` calls `s602b_test_scoped_cases.build(URL, tmp,
  'guardrail')` (its `main` refuses `*_test`; record in packet), then in-process `performance_migration` with
  `json_evidence_store.EVIDENCE_STORE_ROOT` monkeypatched to tmp (never the worktree var/evidence - a stray
  var/evidence I created was deleted). `_pin_kobo` = pinned_app via monkeypatch. `FAILURES` prints port errors.
- CURRENT RESULT: both days PARTIAL, all four rows UNKNOWN. Port failures:
  1. `mini_overview: AwaitingComparison` (no S2 legacy comparison record; the s602b walkthrough never ran
     evidence_migration either). Options: run `evidence_migration` in process with BOTH
     `json_evidence_store.EVIDENCE_STORE_ROOT` and `legacy_comparison_file.EVIDENCE_STORE_ROOT` patched (empty legacy
     set may not PASS against a non-empty ledger), or a NO_LEGACY_EVIDENCE basis (`site_overview/route.py:138-145`,
     `no_legacy_basis`), or w403/s502 pattern (`create_app(legacy_documents=kobo_documents())`, test_w403 :60-65).
     Unsettled overview -> all UNKNOWN, which breaks the day-A Cost NEEDS_ATTENTION assertion -> may need an
     Architect question if no honest way to open S2 on this fixture.
  2. `estate: the Site is not in the estate scope` on one day; the other day's `site_work_rows` had 0 findings,
     1 action. Trace `estate/portfolio.py:505` admit (Site/evidence scope for that window) before asking.
- Not yet run: cold (`-c w502.BUILD positive <dir>` child, window = doc["window"]) and EV (in-process
  native_replay + _declare, window = evidence_window_E). Mini timing so far: day-B board 2.0 s (PARTIAL).
- Then: message coordinator for B4 per-unit review; B5/B6 (B5 measure-mock-panels needs go), packet, closeout.

## B4 addendum 5 applied (ebc89c7b + this commit) - Postgres test runs; 4 of 5 fail on fixture currency (questions sent)
- `site_work_rows(tenant, site_code, day_from, day_to, work_from, work_to, known_at=None)` (`estate/portfolio.py:505`):
  Findings + `site_cov` over the board day, Actions over the work window, one `self._read`; None when the Site is not
  in the board-day scope. Mini port `estate(day_lo, day_hi, work_lo, work_hi)` (`mini.py:99`, call `:245`), board
  binding `read.py:198`; fakes updated (`test_out_b2_mini.py:97`, `:172` asserts the split; `test_out_b4_read.py:66`).
  Focused b2 mini / b4 read / b4 route: 35 passed.
- Test (`test_out_b4_board_postgres.py`): per-case DBs `assetops_out_b_{guardrail,estate,cold,ev}_test` (clone of the
  run template when routed, dropped FORCE after); S2 stand-in = `test_s5_overview_postgres.Imported.scope` patched onto
  `ImportedEvidenceReads.scope` (docstring says so); evidence roots patched to tmp (both `json_evidence_store` and
  `legacy_comparison_file`); EV build in a child (`EV_BUILD`) so the registered replay binds the case DB; `ev.URL`
  patched in `_pin_kobo`. Each board read prints `OUT-B4 record <key>` with states, `failed`, port errors, a summary of
  each port body (`PORTS`) and seconds. Runner as above; 103 s for the file.
- RESULTS (run 3, head after this commit):
  - imported_at KOBO (both s602b cases) = 2026-10-07 10:00Z > Day A `to` 10-07 00:00Z -> Day A `failed` has
    "estate" (fixture artefact, addendum 5 #2 ii). Day B and estate 10-21: estate admitted.
  - closed S2 (no stand-in): PARTIAL, rows all UNKNOWN, outcomes UNKNOWN/NOT_MEASURED, failed [mini_overview, estate]. PASS.
  - With the stand-in, every Kobo read (guardrail 10-06, 11-02; estate 10-21): mini overview `freshness.state` =
    STALE_PROJECTION (assessment CURRENT) -> mini `base` false (`mini.py:266`) -> all four rows UNKNOWN; mini depth
    all four domains status UNKNOWN 0 rows; Finding index status UNASSESSED, 0 rows over the 31-day window (so no F01
    issue on Day A, assertion `moves` fails). Day B: action_index 1 row (ACT-048), readiness FULL, read_state
    AVAILABLE, still UNKNOWN (stale base). Estate 10-21: readiness NONE. Timings: 2.4 s / 2.0 s / 3.0 s.
  - Cold w502 positive (window = doc["window"] 10-29..10-31): AVAILABLE, [NOT_MEASURED, NOT_MEASURED, UNKNOWN,
    UNKNOWN]; cold_overview currentness UNKNOWN, cooling UNAVAILABLE; cold_findings 0 rows; readiness NONE; 0.98 s.
  - EV w504 positive (E 10-06 08:00-09:00): PARTIAL, [WATCH, NOT_MEASURED, NEEDS_ATTENTION, UNKNOWN]; readiness
    refused `EstateRefusal: ESTATE_SELECTION_INCONSISTENT`; ev_overview CURRENT; 1 Finding; 1.2 s.
- OPEN (asked of the coordinator, nothing changed to make them pass): (1) the s602b fixtures' overview is
  STALE_PROJECTION and the Finding index UNASSESSED/empty on every board day, so B.7 #2 and #3's mini assertions cannot
  hold on them; (2) cold: is `doc["window"]` the right board window (no Findings, currentness UNKNOWN) - the cold
  Finding's evidence window may be another key; (3) EV readiness ESTATE_SELECTION_INCONSISTENT over a 1-hour E window.
- Resume: after the ruling, adjust fixtures/windows, rerun this file, then B4 per-unit review, then B5.

## Next (partial handoff, context limit): apply addendum 6 to `test_out_b4_board_postgres.py`
- Read only addendum 6 and the amended B.7 #2-#4 in plan2 `.agent/build-spec-outcome-sprint-2026-10-29.md`.
- Coordinator's summary of the ruling:
  - Kobo: assert the honest states (4 rows in order, measured outcomes UNKNOWN, read_state/failed as recorded,
    Day A failed ["estate"]). Day B: the Action index returns ACT-048, keep the Action-row key check, no "outside
    this view". Parity: same app, GET `/api/sites/KOBO-001/overview?date=...`; its `freshness.state` equals the
    board's overview body (PORTS["mini_overview"]["freshness"]). Drop Day A NEEDS_ATTENTION/F01, Day B Must-not-harm,
    and the estate Finding-row key check (moved to the combined-dataset task).
  - Cold: board on `doc["w501"]["window"]`, no known_at; assert Protect NEEDS_ATTENTION, Grow/Cost NOT_MEASURED,
    record Assure; B.7 #4 only if the completed request is in the work window, else record it absent.
  - EV: same app GET `/api/estate/evidence` over the E window; if it is also 409 ESTATE_SELECTION_INCONSISTENT, assert
    Assure UNKNOWN and record it; if it succeeds, `site_readiness` is bound wrongly: fix it before review.
- Then: all 5 tests pass, commit, handoff, message the coordinator (B4 review), then B5 (measure-mock-panels needs go).

## Addendum 6 applied to test_out_b4_board_postgres.py - 5/5 pass (110 s); focused b1-b4 non-Postgres 123 passed
- Run needs PYTHONPATH = worktree backend;contracts;tools (PowerShell), else the venv resolves another tree's contracts.
- Kobo (3 reads): 4 rows in canonical order, measured outcomes UNKNOWN. Day A PARTIAL failed ["estate"]; Day B AVAILABLE
  failed []; estate 10-21 AVAILABLE failed []. Overview route freshness = STALE_PROJECTION = board's mini_overview freshness
  (parity asserted both days). Day B ACT-048 returned, Action-row keys checked, no "outside this view". Withdrawn
  assertions left as comments (combined-dataset acceptance).
- Cold (window = doc["w501"]["window"] 10-29T16:00..17:05Z, a [from,to] list): AVAILABLE, [NOT_MEASURED, NOT_MEASURED,
  NEEDS_ATTENTION, WATCH]; Assure WATCH (readiness NONE). B.7 #4 "Not yet verified": ABSENT (recorded, not asserted).
- EV: PARTIAL, [WATCH, NOT_MEASURED, NEEDS_ATTENTION, UNKNOWN]; board readiness ESTATE_SELECTION_INCONSISTENT.
  /api/estate/evidence refuses a non-midnight window (422 INVALID_WINDOW, scope.py:120), so the check used the UTC day
  containing E (10-06): 409 ESTATE_SELECTION_INCONSISTENT -> fixture's, not a binding bug. Assure UNKNOWN asserted.
- Next: coordinator B4 per-unit review, then B5/B6.

## B4 fix round (addendum 7 + review OUT-B4-review.md M1-M3, L1-L4)
- M3 / addendum 7: `estate/scope.py` `check_window` (the one window rule, now used by `parse_request`) and
  `estate_request(kind, from, to, known_at)`; `site_readiness` (`evidence_money.py`) and `site_work_rows`
  (`portfolio.py`) build requests through it, so a misaligned or over-31-day window is `EstateRefusal("INVALID_WINDOW")`.
  The estate methods never widen. `site_outcomes/read.py` `covering_days(lo, hi)` = `[floor_utc_day, ceil_utc_day)`;
  `_shared(widen=True)` is used by `cold_ports` and `ev_ports` only (mini unchanged). Over 31 covering days: the estate
  refuses, `evidence_readiness` is a failed port, Assure UNKNOWN, board PARTIAL; board `window` stays the board window.
- Tests: `test_out_b4_window.py` (10: covering days, misaligned/over-31 refusal on both methods, widening forwarded for
  cold and EV, over-31 board PARTIAL with unwidened `window`); `test_out_b4_main_binding.py` (M1: `create_app(site_read_access=
  Grant("COLD-LAB-001"))` -> KOBO board 403 SITE_SCOPE_FORBIDDEN; non-vacuity: removing `work_access=site_read_access` in
  `main.py` -> 503, test fails; reverted); `test_out_b4_route.py` L3 (registry call counter is 0 on 401/403).
- Postgres test: M2 `_assert_readiness_equals_portfolio` compares the board's `evidence_readiness` port with the EVIDENCE
  cell from `GET /api/estate/portfolio` (and `/api/estate/evidence` agreeing) over the covering UTC day; L1 asserts
  ACT-048's id on the `action_index` port; L2 evaluates B.7 #4 (`present == completed requests in work window and
  no later related request`).
- RE-RECORDED: cold w501 window 10-29 16:00-17:05Z -> covering day 10-29: Portfolio cell NONE, board port NONE, states
  [NOT_MEASURED, NOT_MEASURED, NEEDS_ATTENTION, WATCH] (Assure WATCH unchanged); B.7 #4 absent, 0 completed requests in
  the work window (consistent). EV w504 E 10-06 08:00-09:00Z -> covering day 10-06: Portfolio route 409
  ESTATE_SELECTION_INCONSISTENT on both `/api/estate/portfolio` and `/api/estate/evidence`; board port refused the
  same way -> Assure UNKNOWN, PARTIAL, states [WATCH, NOT_MEASURED, NEEDS_ATTENTION, UNKNOWN]. The refusal is the
  fixture's (whole-day also refuses): honest UNKNOWN, carried to the combined dataset.
- Preexisting, unrelated: `test_w301_estate_index_postgres.py` 2 tests (`..._without_mock_seed`, `..._only_exact_eligible_
  current_rows`) fail with NoResultFound also at d37a2cbd (checked one).
- L4, packet notes, per-read gate handling (addendum 4 #6; checked by the B4 review against the routes): overview =
  `site_overview/route.py:137-158` (S2 source + performance gate + basis_reason); dispatch = `performance_gate`; Finding
  index = `basis_aware_gate` (route 409 -> PortUnavailable); mini depth = no gate (`mini_depth_api.py:6`); Action detail,
  verification, Action index, assumption series = no gate flag on GET (`action_api.py:212-221`; `source_open` is only on
  recommendation/accept, which the board never reads); work lists, domain index, global work = `site_read_access`
  (WorkGate read_scope = board `work_access`); cold/EV reads = access, window, Site type, disclosure (`cold_site_api.py:60-102`,
  `ev_assessment_api.py:85-118`). Readiness chips describe the covering day(s), which can be wider than a sub-day window.

## B5 partial (2026-10-30, context limit). Resume at "B5 next" below
- Step 1 done: `.agent/OUT-mock-measurements.md` (7a501d2d, force-added). Closed-board caps: 1440 -> 450 px, 390 -> 800 px
  (calculation in the file). Chrome closed by the tool; no 9488 process remained.
- Landed (baad3f5d, then the tests commit):
  - `frontend/src/sites/outcomeBoardClient.ts` (wire types, `createOutcomeBoardClient`, `outcomeBoardSearch`; refusal code
    from `detail.code`).
  - `frontend/src/sites/OutcomeBoard.tsx` (`OutcomeBoard({client, siteCode, query})`, `boardMoneyText` = the mini money
    slot text "{low} to {high} {currency}", one amount when equal; `countsText`; local `<dialog>` explainer with
    showModal fallback, Tab wrap, Escape, focus return). Board CSS + matrix/key/dots CSS appended to `sites/outcomes.css`
    (tokens; blue = accent pair; class `.oc-hidden` for visually hidden text).
  - Plumbing: `App.tsx` prop `outcomeBoard` (default real client) -> `SiteDetailFrame` -> `SiteOverview` ->
    `SiteWindowOverview` (query `{date: utc_date, finding_id/revision from known_finding}` = the served selection) and
    -> `coldSiteScreen` -> `ColdSiteFrame` (`p.outcomeBoard`, query `p.window`); `SiteEvFrame` -> `EvSiteFrame` (same).
    Views render no board when the prop is undefined (direct renders).
  - Removed: mini `ObjectiveCards` + `MiniObjectiveCard`/`serviceWords`/`fuelWords`/`renewableWords` and helpers (the
    mini depth reads stay: `DayStatus` uses `overviewReadable(miniState)`); cold `OverviewCards`; EV `OverviewCards`,
    `sessionWord`. R540.
  - Tests: `sites/__tests__/outcomeBoard.test.tsx` (13 pass), fixture `test/outcomeBoardFixture.ts`
    (`boardBody`, `boardRows`, `fakeOutcomeBoard`); `test/settled.ts` LOADING gains "how this site is doing" and
    "outcomes across the estate". Note: "load" is a w1 forbidden word (mock subline text trips it).
- B5 next: 25 old-card tests fail (log: `.agent/OUT-B5-old-card-test-failures.log`, git-ignored): s5SiteWindowOverview
  12 (W4-02 mini cards H3 etc., W1-a Q2/R157/Q48 card tones), coldSiteViews 10 (Run-7 Evidence status chip x4, five
  cards, v69 panel structure, r254 links, w2f copy), evSiteMoneyRoutes 3 (all_five_routes, unknown_pending, R254 cards).
  coldRoutes and evAssessmentRoutes passed. For each: pass `outcomeBoard={fakeOutcomeBoard().client}` to `<App>`,
  assert the board present (region "Outcomes at this site", 4 rows) and old cards absent; keep every non-card assertion;
  where a test's subject was only card content, replace it with the board equivalent and list it in the packet
  (no weakening). Check whether the Run-7 Evidence chip logic is still rendered elsewhere before rewriting those 4.
- Then B6 (not started): `getOutcomeSummary` optional on `EstateClient` (`estate/estateClient.ts`; schema
  `estate-outcome-summary-1`; GET `/api/estate/outcome-summary` with from/to/known_at; rows carry `short_value`,
  `lead_outcome` may be null), `OutcomeMatrix` in `PortfolioOutcomes.tsx` replacing `ObjectivesPanel` body
  (`EstatePortfolio.tsx:305`), panel title "Outcomes across the estate", note "How each site is doing on what matters",
  loading "Loading outcomes across the estate…", failure alert "Outcome status is not available right now"; dots in
  `CategoryCards` (`.oc-sitedots` at PortfolioOutcomes.tsx ~173; CSS `:empty{display:none}` in estatePortfolio.css:174);
  Grow card value = first Site's `short_value`, tone green, else the MissingClaim. Register: R529 resolved, R521
  resolved, add R535 and R540-R552 (descriptions in spec §0.3/B rulings Q4 and addenda 2-4; R553-R554 free).

## B5 old-card tests landed (23ba5b0a, 5d?, 074751e8). Packet notes for B5
- Run-7 Evidence chip check: the chip (`evidenceAggregate`, "Evidence limited/contradictory/unknown/supported") still
  renders in the cold Evidence route status strip; the 4 Run-7 tests keep their strip assertions (lines ~501-503) and
  only the Overview Evidence-card word read moved to "board present, cards absent". Not a lost feature.
- Panel guard (`test/panelStructure.ts`): `section.ob-board` admitted as a leading element on screens mini, cold, ev only
  (`OUTCOME_BOARD_SCREENS`), its h2 kept out of panel titles and firstPanel, flagged by strayBetweenPanels after a panel.
  Proven: dropping "cold" from the set fails `stocked: cold` (leading intruder); dropping `precededByPanel` fails the
  new unit test. Two unit tests added in `test/__tests__/panelStructure.test.ts`.
- Helper `expectOutcomeBoardReplacesCards(selectors)` in `test/outcomeBoardFixture.ts`; fixture subline changed to the
  backend-shaped "The generator may have operated longer than needed." (default vocab set flags "ran").
- Changed tests (card assertions -> board present + old cards absent; all non-card assertions kept):
  cold: Run-7 chip x4 (overview half), "renders the ledger's strip, five cards..." (card list/cooling/maintenance/R437/
  temperature/backup card text removed), "a null attention destination..." (temperature/backup card text), w2f
  (cooling card text -> no "Cooling resumed" on the page), r254 (rewritten: no card links; board gets the window from/to).
  Cold/EV renders use a moneyless board so the no-amount assertions stay about the domain reads.
  EV: unknown_pending (card values), all_five_routes (power card), R254 (rewritten as cold r254).
  mini: W1-UX-02 stale day (Dispatch card line), W1-a Q2/R157/Q48 (rewritten: board gets `date`), W1-a Q2 gray/none
  (board on both assessment variants), W4-02 x5 card-value tests (shared cutoff/known_at kept; now assert no card value
  text on the Overview), W4-02 H3 x3 (waits on the reads + strip, not card text). Card-value formatting tests have no
  subject left (the helpers were deleted in baad3f5d).
- Removed dead `OVERVIEW_MINI_LOADING`, `OVERVIEW_MINI_UNAVAILABLE` (SiteWindowOverview.tsx).
- Open copy question: the mini strip still says "Reads on this Overview: ... Each card shows what its selected period
  supports." (`SiteWindowOverview.tsx` `overviewReadsStrip`, H3 ruling copy) though the cards are gone. Not changed.
- Register: R437 (cold maintenance card deviation) is moot with the card removed; close it with R540 in B6.

## B6 landed (2026-10-30; 8a?..be4596bd). Step 3 (heavy runs) waits for the coordinator's go
- `estate/estateClient.ts`: `OUTCOME_SUMMARY_SCHEMA`, `EstateOutcomeSummary{Row,Site,Category,Body}`, optional
  `EstateClient.getOutcomeSummary({from,to,known_at})` -> `/api/estate/outcome-summary` (real client implements it).
- `estate/PortfolioOutcomes.tsx`: `OutcomeMatrix`, `OutcomeMatrixBody` (loading role=status "Loading outcomes across the
  estate…", failure/absent method role=alert "Outcome status is not available right now"), `OUTCOME_KEY` (six states,
  mock order), `SiteDots` (`[data-portfolio-card-dots]`, title + hidden ": {state_label}"), `growShortValue` (first
  Site's Grow `short_value`, tone green; else the A6 MissingClaim).
- `estate/EstatePortfolio.tsx`: `ObjectivesPanel({summary})` renders the matrix (old body deleted; `objectives` wire
  unrendered); page fetches the summary in parallel keyed on the window (not re-read on Load more).
  Dead words removed from `portfolioWords.ts` (OBJECTIVES_PANEL/SUBTITLE/FOOTNOTE, NO_CONFIGURED_OBJECTIVE,
  OBJECTIVE_DETAIL_UNAVAILABLE). `.objective-matrix` CSS left in estatePortfolio.css (dead, harmless).
- Panel title map: `test/v69PanelTitles.ts` `"portfolio:2": "Outcomes across the estate"`.
- Tests: `estate/__tests__/portfolioFixtures.ts` `outcomeSummaryBody`, `withOutcomeSummary`. estatePortfolio.test.tsx:
  4 changed (rendersFiveObjectiveRows... now asserts the 4xN outcome matrix, cell text/tone/href, key order, no codes,
  summary window; appendsOnlyFindingRowsOnLoadMore 16 outcome cells + summary read once; rendersMeasuredPanelHierarchy
  `.oc-matrix` in the objectives scroll; objectiveCellsLink... outcome cells open overview_href, old destinations gone),
  2 new (dots match matrix + Grow short value; Grow fallback + unavailable/absent-method alert). Mutation: dot tone
  hard-coded gray fails the dots test.
- Register: R521, R529 resolved; R437 closed (card removed); R535, R540-R552 added (R541, R535, R552 open; R552
  carried to the combined dataset task per addendum 6). R553-R554 free.
- B5 fix: explainer table goes through `DataTable` (check-all shell-overflow guard caught the bare table).
- Checks: focused vitest 12 files 361 passed; tsc clean; check-all 11/11 (ASSETOPS_GUARD_PYTHON=plan2 venv).
- Next: full vitest, then backend `-Tier all`, then captures 1440/390 (each needs a go), then step 4 closeout.

## Full vitest (coordinator go), head 6a706db2, 15:01-15:05 (218.6 s)
- `npx vitest run` (frontend): 143 files, 3500 tests: 3496 passed, 4 failed.
- 3 failures are the gate-ignored w1f4 tests (`w1f4VerificationStructure.test.tsx`: historical selection; stocked;
  planted extra panel before panel 1).
- 1 not on the ignore list: `coldWorkCases.test.tsx` "W5-02 K3b: every long case cell replaces its preview while
  open > Incident What happened" (AssertionError: expected <span …> to be null). It passes alone (36/36) and with the
  cold neighbours (166/166). This slice changes no work-case file, so I read it as a load-timing flake; needs a
  coordinator ruling before merge.
- Coordinator: the "Each card shows what its selected period supports." strip copy goes to the Architect; left as
  is; record in the packet.
