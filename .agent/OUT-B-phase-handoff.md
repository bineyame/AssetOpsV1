# OUT-B handoff (partial, 2026-10-30): B1 accepted; B2 fix round landed (awaiting coordinator check); B3 landed. Resume at B4

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
