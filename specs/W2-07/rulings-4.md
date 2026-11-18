## Review r1 rulings (2026-10-20)

This amends `D-2026-10-18-w2-06-07-buildspec` and supersedes conflicting copy or test examples above. Apply these literal fixes to the existing W2-07 branch; retain the mock's panel order and the selected-read truth rules. The review's Low labels combine two copy questions under L1; the request below rules each question explicitly.

### M1 — priced browser proof and tariff words

In `.agent/W2-07-evidence/seed.py`, replace the default `publish(built.tenant_id, built.site_id, idem="w207-capture-tariff-1")` with `golden_tariff(built, idem="w207-capture-tariff-1")` from `backend/tests/test_w207_ev_money_postgres.py`. Keep the selected replay window `[2026-10-06T08:00:00Z, 2026-10-06T09:05:00Z)` and the golden tariff validity `[2026-10-06T08:00:00Z, 2026-10-06T09:00:00Z)`. The interrupted replay's four eligible pre-abort intervals lie within tariff validity: `15.000 kWh × 0.27775 KES/kWh = 4.16625000 KES` exact, displayed `KES 4.17`. Re-run the existing capture command on the seeded priced Site, capture the four money-bearing routes (`ev`, `ev-evidence`, `ev-financials`, `ev-assumptions`) at 1440 and 390, and replace the height table with measured priced values against the same-width mock ceilings. The Financials bridge, card, tariff/currency keys, and Assumptions tariff row must be visible in that proof.

Map tariff `basis` `AUTHORED_ESTIMATE` to the literal UI phrase `Authored estimate`; the row value is `0.27775 KES/kWh · Authored estimate` on Financials and Assumptions. `Assumption details` uses the same phrase. No `AUTHORED_ESTIMATE` text appears outside an explicitly marked technical ID/code field. Extend `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx::financial_tabs_and_price_gate` with a fixture whose `tariff.basis` is the real stored `AUTHORED_ESTIMATE`, asserting the row on both routes and that neither row contains `AUTHORED_ESTIMATE`.

### M2 — exact display rounding

Keep half-even in `money2`; storage, SHA inputs and the unrounded Basis details keep their exact Decimal strings. Round the absolute decimal to two places: if the discarded fraction exceeds one half, increment; if it equals one half exactly, increment only when the retained cent integer is odd; then restore the sign. Inspect every discarded digit, not only the third. Add to `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx::financial_tabs_and_price_gate` the discriminating assertions `money2("8.325") === "8.32"`, `money2("8.335") === "8.34"`, `money2("8.32500001") === "8.33"`, and `money2("-8.325") === "-8.32"`.

### M3 — Analysis plain-language vocabulary

In `backend/assetops_backend/ev_site_reads.py::analysis`, construct `source_label` from the selected Foundation display name and the role table below, separated by ` · `. Keep `role` as the existing machine value for exact provenance; the visible first cell and Record details use the plain `source_label`. `value_display` uses the event/state table below; numeric readings retain the exact numeric string and `unit` returned by the accepted record. `record_kind` and accepted IDs remain exact. These are all eight roles in `EV_ROLES_1`, including the optional connector-power channel; do not fall back to a raw role/code. For an accepted role outside this set, use `EV reading` as the visible label and keep the raw code only in the technical record field.

| Accepted binding role / public role | Visible source suffix |
| --- | --- |
| `ev_session_event` / `session_event` | `session` |
| `ev_connector_fault` / `fault_event` | `connector fault` |
| `ev_connector_state` / `connector_status` | `connector status` |
| `ev_connector_energy` / `connector_meter_delta` | `energy` |
| `ev_connector_power` / `connector_power` | `connector power` |
| `ev_site_import` / `site_import` | `site import` |
| `ev_requested_power` / `requested_power` | `requested power` |
| `ev_allocated_limit` / `allocated_limit` | `allocated power limit` |

| Accepted `record_kind` or connector-state `value` | Visible `value_display` |
| --- | --- |
| `EV_SESSION_START` | `Session started` |
| `EV_SESSION_END` | `Session ended` |
| `EV_SESSION_ABORT` | `Session aborted` |
| `EV_CONNECTOR_FAULT` | `Connector fault` |
| `EV_CONNECTOR_CLEAR` | `Connector fault cleared` |
| `AVAILABLE` | `Available` |
| `UNPLUGGED` | `Unplugged` |
| `PLUGGED` | `Plugged in` |
| `AUTHORIZING` | `Authorizing` |
| `CHARGING` | `Charging` |
| `FAULTED` | `Faulted` |
| `DISABLED` | `Disabled` |

The seven state codes are exactly `sites/binding_roles.py::EV_CONNECTOR_STATES`; the five event kinds are exactly the session/fault kinds in `EV_ROLES_1`. A null value remains `Not recorded`. An unexpected state must display `State not recognised`, retaining its original value only in technical details; never concatenate a raw enum with ` state`. Extend `backend/tests/test_w207_ev_site_reads_postgres.py::test_analysis_intervals_and_publication_note` to assert the complete mapping table through accepted role/state/event records (a pure mapping test may supplement the persisted fixture), including `Connector c1 · connector status` plus `Authorizing`, `Connector c2 · session` and `Connector c2 · energy`. Extend `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx::ev_evidence_tabs_and_record_limit` to assert those plain first-cell/value strings and the absence of `connector_status`, `session_event`, `AUTHORIZING`, and `EV_SESSION_START` in visible table cells. Keep existing exact numeric value/unit assertions.

The same Analysis screen's `claim_rules` list may render all seven capability codes. Use this complete claim/state table in its visible Claim details (the four-row Evidence overview still shows only its four mock rows):

| `claim` | Visible capability |
| --- | --- |
| `SESSION_OUTCOME` | `Session outcomes` |
| `SERVICE_STATE` | `Connector availability` |
| `DELIVERED_ENERGY` | `Delivered energy` |
| `FAULT_ASSOCIATION` | `Cause of interruption` |
| `SITE_POWER_CONTEXT` | `Site power context` |
| `POWER_CONSTRAINT` | `Site power constraint` |
| `GROSS_TARIFF_SCENARIO` | `Gross tariff scenario` |

| `result` | Visible chip |
| --- | --- |
| `SUPPORTED` | `Full` |
| `LIMITED` | `Limited` |
| `UNAVAILABLE` | `None` |
| `CONTRADICTORY` | `Contradictory` |

The state mapping is independent of claim: each of the seven claims can use any state its selected evidence permits. Assert all seven labels and all four chip words in `ev_evidence_tabs_and_record_limit`; never expose a claim or state code as table copy.

### M4 — the two clocks in Financials

Use the existing Assumptions response field `publication_note`. Its exact non-null sentence is `Tariff published {YYYY-MM-DD HH:MM} UTC; applied as a scenario to the selected delivery window. Evidence through {YYYY-MM-DD HH:MM} UTC.` from selected `tariff.recorded_at` and `window.known_at`, only when the former is later. Render it inside the **Financials → Assumptions in use → Assumption details** disclosure, immediately after the tariff revision/validity facts. Keep the Assumptions route's currently visible note; also include the same sentence inside its `Assumption details` disclosure so opening that detail exposes the two clocks. No sentence when `publication_note` is null. In the frontend `assumptions()` fixture for `financial_tabs_and_price_gate`, set `recorded_at="2026-10-06T09:30:00.000000Z"`, keep `KNOWN="2026-10-06T09:00:00.000000Z"`, and set `publication_note="Tariff published 2026-10-06 09:30 UTC; applied as a scenario to the selected delivery window. Evidence through 2026-10-06 09:00 UTC."`. Assert that exact sentence in the Financials `data-disclosure="ev-site-assumption-details"` and in the Assumptions route's disclosure, and assert it absent for an otherwise identical null-note fixture. This is scenario publication after the evidence cutoff; it must never imply that the tariff was known at `known_at`.

### L1–L5 — remaining rulings

**L1, null consequence.** When the selected `consequence` is JSON null, the `/ev` money card, Financials `Gross tariff estimate` card, Financials bridge Consequence cell and any `consequenceWord(null)` return `No gross tariff scenario assessed` (with the UI's usual punctuation outside the value). This is the same UNKNOWN or pending-with-no-prior empty state, distinct from a stored `UNPRICED` consequence (`Unpriced`) or `WITHHELD` guard (`Withheld`). The bridge's explanatory row remains `No eligible delivered-energy consequence`. In `financial_tabs_and_price_gate`, assert the null fixture's card and bridge cell equal that literal and the stored `UNPRICED` fixture still says `Unpriced`.

**L2, aggregate and strip.** The shared Evidence chip and strip count use the same four mock-visible capabilities, in this order: `SESSION_OUTCOME`, `SERVICE_STATE`, `DELIVERED_ENERGY`, `FAULT_ASSOCIATION`. The other three (`SITE_POWER_CONTEXT`, `POWER_CONSTRAINT`, `GROSS_TARIFF_SCENARIO`) remain in Analysis claim details; they do not change the four-row Evidence chip. Apply the existing precedence to those four: no rows/all `UNAVAILABLE` → `Evidence unknown`; any `CONTRADICTORY` → `Evidence contradictory`; all four `SUPPORTED` → `Evidence supported`; otherwise `Evidence limited`. Strip text is `4 capabilities · {full} full · {limited} limited · {none} none · no single score`, counting only those four (`CONTRADICTORY` gets its own count if present). Never count seven while displaying four. In `ev_evidence_tabs_and_record_limit`, assert four visible rows, count 4, the corresponding counts, and a fixture with four `SUPPORTED` plus `POWER_CONSTRAINT=LIMITED` still has `Evidence supported`.

**L3, ranked next evidence.** Build candidates once, deduplicate by code, and take the first three in this exact rank: (1) `TERMINAL_GAP` when `session_terminal` is missing; (2) `METER_GAP` when `connector_meter_delta` is missing or any selected session has positive `unknown_meter_seconds`; (3) `STATUS_GAP` when `connector_status` is missing; (4) `INDEPENDENT_POWER_GAP` when `POWER_CONSTRAINT.missing_roles` contains `requested_power` or `allocated_limit`, with text `Record requested and allocated power`, why `Independent requested and allocated readings are needed before a power constraint can be assessed.`, selected Analysis link; (5) `SITE_IMPORT_GAP` when `site_import` is missing; (6) `TARIFF_GAP` when the published tariff role is missing; (7) `BILLING_GAP` always as the final candidate. This resolves the earlier shorthand `independent diagnostic/request/limit`: no declared load manager means no diagnostic is expected or invented; the independent request and allocation channels are the actionable gap. If both request and limit are present, do not emit rank 4 even when the claim remains limited for another reason. Extend `backend/tests/test_w207_ev_site_reads_postgres.py::test_five_routes_reuse_w206_envelope_and_exact_selection` with candidate-list assertions before the first-three slice: terminal/meter/status outrank independent power; independent power outranks Site import/tariff/billing; no rank-4 item when both roles are observed; exactly three returned rows in a many-gap fixture. The Evidence panel's existing three slots use these returned rows unchanged.

**L4, same-instant chronology.** For the Overview chronology only, sort accepted non-excluded events by `(source_time, kind_rank, evidence_id)` where `EV_SESSION_START=0`, `EV_CONNECTOR_FAULT=1`, `EV_SESSION_ABORT=2`, `EV_SESSION_END=3`; thus the interrupted 08:16 fault precedes the 08:16 abort. The Analysis table and cursor keep their mandated `(source_time,evidence_id)` order. Add a frontend assertion in `all_five_routes_keep_mock_panels_and_truthful_tabs` (or a named `same_instant_fault_precedes_abort_in_chronology` test) with reversed IDs for same-time fault and abort: the chronology text/DOM order is `Connector fault` then `Session aborted`, while Analysis order remains ID order.

**L5, downgrade probe.** Keep the spec's no-delete rule. In `backend/tests/test_w207_ev_money_postgres.py::test_r4_ev_currency_and_value_validation_is_ev_only`, exercise refused downgrade after tariff publication, then perform the successful empty downgrade on a separate fresh 0026 database/Site before any EV tariff, assignment, consequence, work or attempt row is inserted. Assert each of the seven guarded row counts is zero immediately before that downgrade, assert it reaches `0025_w2_ev_session`, and assert the pre-existing diesel/fuel rows and checks survive. Do not call `remove_money`, use replica-role DELETE, or bypass append-only triggers to manufacture the empty state. Existing refusal probes still assert that populated state is preserved on refusal.
