# W5-03 build contract — EV depth

Architect/Planner, 2026-10-22. Task: [`tasks/W5-03-ev-depth.md`](../tasks/W5-03-ev-depth.md). Sources: `.ai/ROLE_CONFIG.md` readiness gate and 13 lessons, `.agent/post-W2-sequence.md` W5-03, v6.9 `availability`, `energy`, `ev-health`, `ev-scenarios`, merged W2-06/07 and W2-F code. Unit cards E1a, E1b, E2–E6 are the only builder instructions; each has this shared contract plus at most three named sections to read. W4-01 frozen work-case identity is consumed unchanged.

Each card is one reviewed unit; E3 is split into page/chart and closeout builder runs under the 2026-10-23 pre-flight ruling. Each run makes one commit and handoff. Its final commit includes its tests and, for page cards, the named 1440/390 captures; the builder then hands off for the stated review before dependent work.

## Gate, order and strict boundaries

W2 gate **satisfied**: W2-F merged `2df2a3da`, independent re-audit closed all 14 structural findings. W5-03a (E1a–E3) is read-only, two new pages, no migration. W5-03b (E4–E6) has two pages and the authored scenario pipeline. It owns Alembic `0034_w5_ev_scenarios`, **exact** `down_revision="0033_w5_cold_work"`; W5-02 must publish that named sole head before W5-03b integration. W5-04 takes `0035`. E1a, E1b and E5 are per-unit review gates for shared code/schema; E2–E4 and E6 also get independent review before their sub-slice merge because each mounts a shared Site frame/tab. Do not change `ev-session/1`, W2-07 money rules or W4-01 case semantics.

W2-07 already admits `SERVICE_STATE` only up to `LIMITED` and says `Availability is not assessed.` (`ev_site_reads.CLAIMS`); its `STATUS_GAP` action is `Recover connector status history`. The new availability denominator is a distinct W5 selected calculation, not the W2 session attempt denominator. A W2 `SESSION_OUTCOME`, `DELIVERED_ENERGY` or configured schedule does not prove any available second. Charger Health is a separate condition claim: status and fault events can prompt investigation, but no physical fault-part diagnosis or healthy verdict follows.

Readiness review ran `tools/check-all.ps1`: all 11 guards passed, including the estate self-test. Builders rerun it after E2/E3/E6 navigation and registry changes. E2/E3/E6 remove exactly one unavailable multiset occurrence each; registry panel titles below are copied from `v69-rendered-panels.json`. No new UI literal asserts physical health, collections, loss or an unproved full-schedule availability value. **Shared guard files (A1Q W5S-11; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** Lane A edits to `tools/checks/configuration-persistence.ps1` and `tools/writer_guard_probes.py` are additive blocks anchored on the mini-decision lines. A unit that merges after another rebases and keeps both blocks. The W6-01a `$pgReaders` line and the W5 writer blocks do not overlap.

## Selected read, calculation and wire guard

New `GET /api/sites/{site_code}/ev/availability`, `/ev/energy`, `/ev/health` reuse `ev_assessment_api.ev_gate`: authentication before Site lookup; repeated/unknown query keys 422 `EV_PARAMETER_UNKNOWN`; paired UTC `from,to` (at most 31 days), optional `known_at`; existing refusal wrapper `{error:{code,message}}`, disclosure and single read-only REPEATABLE READ snapshot. Response `schema_version:"ev-depth-1"`, `site_id`, `window:{from,to,known_at,committed_watermark}`, `selection:{state,assessment_revision_id,session_revision_ids,accepted_evidence_ids,source_provenance}`, page payload and `links`. Use unchanged `analytics/ev_reads.STATES`: `CURRENT`, `PENDING_RECOMPUTE`, `STALE_SOURCE`, `HISTORICAL`, `UNKNOWN`; EV `currentness_state` puts `HISTORICAL` before pending, unlike cold. If selection absent all denominators/numerators are null (not zero). Pending, stale and historical never present a current positive. Exact accepted-ID set comes from the selected session/evidence rows and relevant status/import/meter intervals in the same snapshot, deduplicated before `evidence/public_provenance.py`; empty/broken/foreign is `UNKNOWN`, crossed classes/bases `MIXED`.

Availability calculation version `ev-availability/1`: resolve each selected enabled connector's effective Foundation service schedule over the requested half-open UTC window, clipping to both. If no schedule is selected or time validity is ambiguous, `scheduled_seconds=null` and all rates null. A selected time-valid `weekly: []` declares zero service seconds: `scheduled_seconds=0`, all three second counts are 0, and all ratios and bounds are null, never 0% availability. For each scheduled connector-second, accepted trustworthy `ev_connector_state` transitions from the bound connector determine `AVAILABLE` for `AVAILABLE` or `UNPLUGGED`, `UNAVAILABLE` for `FAULTED` or `DISABLED`, and `UNKNOWN` for `PLUGGED`, `AUTHORIZING`, `CHARGING`, gaps, conflicting/stale/unattested state, and intervals after last valid state without proven hold duration. A **charging** state alone does not prove that the connector was available for a new session. A transition can classify only its own accepted observation interval, clipped to `[event_time, min(next accepted transition time, event_time + effective Foundation `ev-status-cadence`, window.to))`. There is no declared state-validity end. Missing cadence, conflicting same-time states, a gap or cadence-expired observation yields Unknown; never carry a state indefinitely to `to`; a zero-length or conflict is Unknown. Adjacent intervals union before counting; `known_available_seconds + known_unavailable_seconds + unknown_seconds = scheduled_seconds`. `known_time_ratio = available/(available+unavailable)` only if known seconds >0; `full_lower=available/scheduled`, `full_upper=(available+unknown)/scheduled` only if scheduled >0. Fractions are decimals, known-time percentages round once to one decimal and bound percentages to two decimals; the exact rational counts remain in DTO. Connector-level and Site-level rows share the same classified spans, never sum overlapping pages. A status observation outside the selected assessment's accepted set cannot classify any second. This is a bounded observed-state proxy, explicitly labelled `Observed connector state`, not physical availability certification.
Energy reuses W2-06 `supported_kwh`, `energy_complete`, W2-07 `overview.energy.complete_kwh/partial_kwh/unknown_seconds`, the selected import intervals and `financials` consequence basis; it does not resummarize session pages. `metered_complete_kwh` excludes incomplete session meter gaps, `partial_kwh` is separate, `observed_peak_import_kw` is the maximum of this depth response's selected GOOD interval-mean kW `import_samples` (labelled sample peak), and `configured_import_limit_kw` comes from the effective Foundation revision. There is no `limit_caused_interruption` true from a sub-limit peak; `power_constraint_state` remains `UNKNOWN` unless independent requested and allocated limit accepted observations support a typed comparison. Existing gross tariff amount is shown only through W2-07 eligible consequence revision with exact source and currency; it is never cash collected or lost sales. `health` returns connector assets from effective Foundation, selected observed fault events and condition `NEEDS_INVESTIGATION` or `UNKNOWN`; `stationary_battery` is always `UNKNOWN` in W5-03 because merged EV Foundation has no battery component or explicit absence declaration. The UI says `Unknown` / `Battery configuration is not established by this Foundation.`; no `Not applicable` or `Not configured` literal is emitted. No charger state is `HEALTHY`.

Exact existing refusals come from `ev_gate`: `UNAUTHENTICATED`, `SITE_SCOPE_FORBIDDEN`, `EV_PARAMETER_UNKNOWN`, `EV_TIME_INVALID`, `EV_WINDOW_INVALID`, `EV_WINDOW_TOO_LONG`, `SITE_NOT_FOUND`, `EV_SOURCE_DISCLOSURE_FORBIDDEN`, `EV_READ_UNAVAILABLE`. Cursorless depth routes introduce no basis-change 409. API `links` use `/api/sites/{site_code}/ev/...` with keys `sessions`, `evidence_analysis`, `financials`; the UI translates them to `evSiteRoutes`/`operatorSiteRoutes` paths and retains `from,to,known_at`. The shell Site token is imported `site_code`, never internal Site UUID. Session/Finding/evidence links use IDs from W2 selected rows and selected revision IDs, not mock `SES-011`, `F-130` or `CHG-002` strings; keep `from`, `to`, `known_at` from the read. Frontend clients reject malformed 200 DTOs as a visible refusal.

### Literal, link and state ledger

Site title is the shell's imported name (`Depot Charging Hub` only in fixture). The first-column asset labels use effective Foundation asset names; long IDs are not substituted by mock codes. Shared state notice strings are: `New evidence is being assessed. Earlier selected results may change.` (new W5 literal, intentionally distinct from merged `ev_reads.PENDING_NOTE`) for `PENDING_RECOMPUTE`; `This result reflects records known at the selected cutoff.` for `HISTORICAL` (the merged W2-06 `HISTORICAL_NOTE`); `Selected source records are stale for this window.` for `STALE_SOURCE`; `No selected EV session assessment covers this window yet.` for `UNKNOWN` (merged `NO_SELECTION_NOTE`). `Retry` repeats the same URL only after refusal. An unauthorized or failed response never produces `No records`.

| Surface | Exact visible literals and route |
| --- | --- |
| Availability | The Site-name heading, `Sites › {Site} › Performance` breadcrumb and mock subtitle are fixed in the W5-03a pre-flight E2 ruling below. Status `Evidence limited`; cards `Known available`, `Known unavailable`, `Unknown`, `Known-time availability`; values derive solely from `ev-availability/1`, null is `Unknown`. Mock card notes use selected facts as ruled below. |
| Availability panels | `Connector states over the service schedule`, legend `Available`, `Unavailable`, `Unknown`, per connector bars; no bars if schedule absent, with `Service schedule not established for this window.` when absent; for selected `weekly: []`, no bars and `No service hours are declared in this window.`; `Full-schedule availability bound` with lower/upper only if denominator exists, else `Unknown`; `Most useful next evidence`: `Recover connector status history for unknown scheduled time. A telemetry gap does not prove physical unavailability.` Link `Inspect connector-state lineage →` to selected EV Evidence Analysis, preserving query. |
| Energy | The Site-name heading, `Sites › {Site} › Performance` breadcrumb and mock subtitle are fixed in the W5-03a pre-flight E3 ruling below. `Energy basis: measured` requires selected complete meter evidence; otherwise `Energy basis: limited`. Cards: `Metered session energy`, `Observed peak import`, `Declared site limit`, `Gross tariff estimate`. Null values are `Unknown`; consequence withheld is `Unpriced`. The `Inspect meter basis ↗` action stays in the mock status line. |
| Energy panels | `Import power and configured limit` from accepted samples plus time-valid constant; empty `No accepted site-import samples in this window.`; `What can be concluded` rows `Observed peak below limit` (`Yes`, `No`, `Unknown` from samples/limit), `Site limit caused interruption` = `Not established` unless independent requested/allocated proof, `Requested vehicle power` = `Incomplete evidence` until supported, `Stationary battery` = `Unknown` until a battery declaration exists, `Billing settlement` = `Not connected`; `Technical-to-financial bridge` columns `Quantity`, `Assumption`, `Result`, `Limit`, showing exact W2-07 consequence basis or `No eligible gross tariff scenario.` No invented lost revenue. |
| EV Health | Site-name h1; `Health` breadcrumb/tab. Cards `Connector 1`, `Connector 2`, `Stationary battery` use selected Foundation labels in those positions. Connector state is `Unknown` gray or `Needs attention` amber on a selected fault stop; no completed session proves hardware health (R57 D4). Battery is `Not applicable` / `None installed` only if configured; otherwise `Unknown` with an honest gap (R56 D1). Connector cards link to Sessions with the selected paired window. Sole panel `Condition and evidence` has mock columns `Asset`, `Supported assessment`, `Next evidence`; selected fault row says `Session interruption; hardware fault not established` / `Diagnostic event + witnessed session`; selected Site meter row says `Power limit respected in observed samples` only if proved, otherwise the R59 gap / `Continuous coverage for interval-wide claims`; optional other-connector row is R58 D2. Source-reference session ID is plain text beside the Sessions-list link, never a fabricated detail route. |
| Shared empty/refusal | Availability `No trustworthy connector-state spans in the selected schedule.`; Energy `No complete metered delivery is established for this window.`; Health `No charger condition observation is available for this window.`; refused heading `EV depth unavailable`, server message, `Retry`. No empty success on 401/403/503 or malformed response. |

### Mock measurement and rendering limits

Measured 2026-10-22 from v6.9 `index.html` with `tools/measure-mock-panels.mjs` at 1440×1000 and 390×900. Temporary Chrome launch added `--no-sandbox` for this sandbox, then the temporary script was removed. Mock DOM content width 1161px / 360px; page scroll width 1425/390 equals viewport client width. Test the app with 36-character UUIDs, 160-character limitations, a long connector label, pending/historical/refusal and a three-row table. Caps include those worst cases. **Table and chart primitives (A1Q W5S-10; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** Every table renders through `DataTable` (`frontend/src/ui/DataTable.tsx`; `tools/checks/shell-overflow.ps1` rule 4 refuses a bare `<table`). Every `<svg` is drawn only in the existing diagram, chart, timeline or graphics modules that rule 5 names. No page module draws its own svg.

| Screen / width | Mock page px | Mock blocks px | App caps px |
| --- | ---: | --- | --- |
| availability 1440 / 390 | 1055 / 1714 | status 44/71; cards 113/264; state panel 245/277; bounds 180/176; next 180/180 | status ≤90/125; cards ≤180/350; state ≤340/390; bounds/next ≤260/280; page ≤1300/1950 |
| energy 1440 / 390 | 1230 / 2051 | status 44/113; cards 113/248; import panel 356/235; conclusion 356/308; bridge 243/401 | status ≤90/155; cards ≤180/340; each paired panel ≤440/430; bridge ≤350/520; page ≤1500/2320 |
| ev-health 1440 / 390 | 1001 / 1227 | cards 134/300; panel 198/286 | cards ≤200/380; panel ≤330/440; page ≤1200/1550 |
| ev-scenarios 1440 / 390 | 1001 / 1125 | panel 316/355; notice 42/78 | panel ≤430/560 for one row/empty; notice ≤90/135; page ≤1250/1500 |

At 390, cards wrap two columns; charts fit 360px and retain axis labels. Tables scroll inside their panel only, with a sticky first column; long IDs break inside the cell and full value is accessible. Status, source, unknown and refusal text wraps without ellipsis. Long optional narrative after 160 characters may have a `Read full basis` disclosure but the exact full text remains present. No document horizontal overflow. Use `expectV69Panels` and `expectPlantedPanelRejected` for titled panels plus measured page caps in each page-owning unit.

Worst-content mock pass: the measurement script was rerun at both widths after replacing the first metric note, first panel prose and first notice with a 166-character missing-evidence sentence including a 36-character UUID. Result (1440/390 page height, 390 cards): availability 1103/1816, 344; energy 1278/2131, 328; ev-health 1001/1307, 380; ev-scenarios 1001/1127, no cards. All four retained zero document overflow (1425/1425 and 390/390). The mock has no refusal overlay; that cap must be checked on the app capture.

### Capture producer method, loading and unavailable copy (readiness pass 3; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively)

Every W5-03 page capture follows the W2-04 capture method:
- **Seed.** A throwaway, uncommitted seed test runs `Chain` from `test_w205b_ev_replay_postgres.py` through E1a's `ev_depth_cases.py` wrapper on a private `assetops_w503cap_test` DB with `ASSETOPS_TEST_TEMPLATE=0`.
- **Serve.** Serve the API through the `lab_app` host. Stop the servers and drop the DB before reporting.
- **Clock.** The clock is the returned `window.committed_watermark`: 09:00, then 09:05 after `advance_late()`. Historical captures pass the saved `known_at=2026-10-06T09:00:00.000000Z`.
- **Refused captures.** Every `*-refused` capture is the live route with `from` later than `to`, giving 422 `EV_WINDOW_INVALID`. The 403 path is proved in E1/E5 tests.
- **Unavailable copy.** Network failure → `The EV depth read could not be reached.` (EV scenarios: `The EV scenarios read could not be reached.`). Malformed 200 → `The EV depth read answered in an unexpected shape.` (EV scenarios: `The EV scenarios read answered in an unexpected shape.`).
- **Loading copy** (a `<p className="prose">` while pending): Availability `Loading the site's connector availability.`, Energy `Loading the site's charging energy.`, Health `Loading the site's charger condition read.`, Scenarios `Loading the site's EV scenarios.`
- **Currentness.** On every W5-03 page, a non-`CURRENT` `selection.state` renders an amber `Notice` directly below the status line (or above the first cards on a page without one), using exactly the shared-ledger state sentence. `CURRENT` renders none, and status badges and subtitles are unchanged. Exception: EV Scenarios `PENDING_RECOMPUTE` uses its own pending notice.
- **Graphics.** Availability uses ordered `div` spans matching the mock. Energy restores the mock chart through the registered `evDepthGraphics.tsx` module and retains the `Measure`/`Value` detail in a disclosure. Its empty copy is `No accepted site-import samples in this window.` Exact marks, axes and guard registration are in the pre-flight E3 ruling below.
- **Duration format** (Availability cards and bars): `{h} h {m} min`, omitting a zero hour; `0 min` for zero; seconds are floored to whole minutes only in display, while the DTO keeps the exact seconds.

## Unit E1a — observed availability calculation, W5-03a; per-unit review

One builder run and independent review before E1b. Producer command: `pytest backend/tests/test_w205b_ev_replay_postgres.py backend/tests/test_w503_ev_availability_postgres.py -q` on a private `*_test` DB. Selected window `[2026-10-06T08:00:00Z,2026-10-06T09:00:00Z)`; `Chain.decision_clock()` gives the first 09:00 clock and `advance_late()` advances to 09:05. Current reads omit `known_at`; historical passes saved first watermark `2026-10-06T09:00:00.000000Z`. Persisted producer details are in the pre-flight E1a ruling.
**E1a file list and tests.** E1a owns `backend/assetops_backend/analytics/ev_availability.py`, `backend/tests/test_w503_ev_availability_postgres.py`, `backend/tests/ev_depth_cases.py`; shared Lane A `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py` and `backend/assetops_backend/ev_site_reads.py`. Its tests prove selected-ID intersection, per-connector schedule clipping, cadence bounds, same-time conflict, conservation, a removed-row status gap, and newly assessed `weekly: []`. The producer uses `Chain` and existing complete/fault vectors as ruled in the 2026-10-23 pre-flight section.
**E1a/E1b wire payloads (closure 2, closes RP3-E1; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** All three routes share these top-level keys, in order: `schema_version` (`"ev-depth-1"`), `site_id`, `window`, `selection`, then `availability`, `energy` or `health`, then `links`.

**Shared keys.**
- `window`: `{from, to, known_at, committed_watermark}`. `committed_watermark` = `snap["watermark"]`; the other three = `body["window"]`.
- `selection`: `{state, assessment_revision_id, session_revision_ids, accepted_evidence_ids, source_provenance}`.
  - `state` = `snap["state"]`.
  - `assessment_revision_id` = the selected revision ID, or null.
  - `session_revision_ids` = the sorted selected `result["session_revision_ids"]`.
  - `accepted_evidence_ids` = the sorted lowercase selected `evidence_ids` (the cited set, as in cold C1q Q5); `[]` with no selection.
  - `source_provenance` = `body["source_provenance"]` from `EvReadService.open_on`.
- `links`: `{sessions, evidence_analysis, financials}`. These are `/api/sites/{quoted site_code}/ev/sessions`, `/ev/evidence/analysis` and `/ev/financials`, each followed by `?from=&to=&known_at=` when the window resolves, else bare.
- **UI links.** The UI does not parse these paths. It builds `evSiteRoutes(site_code).analysis` / `.financials` with the read window query, and `${sitePerformanceHref(site_code, "sessions")}${coldWindowSearch(window)}` for Sessions.

**Durations and ratios.**
- Every seconds value is `ev_site_reads._seconds` (an int when whole, otherwise a float).
- Ratios are decimal strings: `Decimal(num) / Decimal(den)` quantized to 6 places with ROUND_HALF_EVEN.

**`availability`** (pure `analytics/ev_availability.availability(foundation, assets, accepted, lo, hi) -> dict` over `EvReadService.foundation_on`, `assets_on` and `accepted_on` on one snapshot connection):

| Key | Type | Rule |
| --- | --- | --- |
| `calculation_version` | string | `"ev-availability/1"` |
| `schedule_state` | string | `SCHEDULED` when every enabled connector has a selected time-valid schedule and at least one has non-empty `weekly`, even if no occurrence intersects this window (then the denominator is zero); `DECLARED_EMPTY` only when all enabled connectors have selected time-valid `weekly: []`; otherwise `NOT_ESTABLISHED`. |
| `scheduled_seconds`, `known_available_seconds`, `known_unavailable_seconds`, `unknown_seconds` | number or null | Site totals: the sums of the connector rows. Null when `NOT_ESTABLISHED`; all 0 when `DECLARED_EMPTY`. |
| `known_time_ratio`, `full_lower`, `full_upper` | decimal string or null | The calculation rules above; null whenever the denominator is 0 or null. |
| `connectors` | array | One row per enabled `EV_CONNECTOR` component that has an asset, sorted `(label, asset_id)`. Each row has exactly `{asset_id, label, scheduled_seconds, known_available_seconds, known_unavailable_seconds, unknown_seconds, spans}`. `label` = the component `display_name`, else its `asset_code`. `spans` = `[{from, to, state, evidence_ids}]` in time order, where `state` is `AVAILABLE`, `UNAVAILABLE` or `UNKNOWN` and `evidence_ids` are the accepted `ev_connector_state` IDs that classify the span (`[]` for `UNKNOWN`). |

**`energy`** (composed from the W2-07 overview computation, which E1b extracts into the shared private helper `EvSiteReads._energy(ctx)`; it returns the overview `energy` and `site_power` dicts and is used unchanged by `overview`. `ev_site_reads.py` is added to E1b's Lane A list):

| Key | Type | Source |
| --- | --- | --- |
| `metered_complete_kwh` | decimal string or null | overview `energy.complete_kwh` |
| `partial_kwh` | decimal string or null | overview `energy.partial_kwh` |
| `unknown_seconds` | int or null | overview `energy.unknown_seconds` |
| `energy_limitation` | string or null | overview `energy.limitation` |
| `import_sample_count` | int | Length of this depth response's selected, GOOD, interval-mean, kW `import_samples` array. |
| `import_samples` | array of `{source_time,import_kw,evidence_id}` | Selected GOOD, non-`EXCLUDED` `ev_site_import` interval-mean rows overlapping the window, sorted by `(source_time,evidence_id)`; exact predicate and unit are in the pre-flight E1b ruling. |
| `observed_peak_import_kw` | decimal string or null | Maximum `import_kw` in this response's selected `import_samples`; null for an empty array. Never use overview `site_power.observed_peak_kw` for this depth field. |
| `peak_sample_at` | ISO string or null | `source_time` of the max-value sample; ties go to the earliest `(source_time, evidence_id)`. |
| `configured_import_limit_kw` | decimal string or null | overview `site_power.configured_limit_kw` |
| `peak_below_limit` | string | `YES` if peak and limit are both non-null and peak < limit; `NO` if peak ≥ limit; otherwise `UNKNOWN`. |
| `power_constraint_state` | string | Always `UNKNOWN` in W5-03. |
| `consequence` | object or null | `EvSiteReads._consequence(ctx)` exactly (the W2-07 `_revision` dict or the WITHHELD guard dict); null when it returns None. |

**`health`** (`EvReadService.foundation_on`, `assets_on`, `sessions_on`, `accepted_on`):
- `health` has exactly `{foundation_revision_id, rows, battery}`.
- `battery` = `{"condition_state": "UNKNOWN", "limitation": "Battery configuration is not established by this Foundation."}`.
- `rows` lists every `EV_CONNECTOR` component that has an asset, sorted by `asset_code`, then every `METER` component that has an asset, sorted by `asset_code`. When no Foundation resolves, `rows` is `[]` and `foundation_revision_id` is null; no meter row is fabricated.
- Each row has exactly `{kind, label, asset_id, asset_code, condition_state, observation, limitation, next_evidence, session_id, evidence_ids}`. `label` = `display_name`, else `asset_code`.

| `kind` | Predicate → `condition_state` / `observation` / `limitation` / `next_evidence` / `session_id` / `evidence_ids` |
| --- | --- |
| `CONNECTOR` | If any selected session has `connector_asset_id == asset_id` and a non-null `fault_evidence_id`: `NEEDS_INVESTIGATION` / `Session interruption observed` / `Fault-stopped session observed; cause not diagnosed` / `Retrieve diagnostic log and witness a complete session` / the `session_id` of the earliest such session by `(start_at, session_id)` / the sorted `fault_evidence_id`s of all such sessions. Otherwise `UNKNOWN` / `Condition unknown` / `No charger condition assessment` / `Record diagnostic and covered operation` / null / `[]`. |
| `SITE_METER` | `UNKNOWN` / `Sampled import only` / null / `Record continuous import and request/limit evidence` / null / the sorted accepted non-`EXCLUDED` `ev_site_import` IDs that overlap the window. |
| `UNKNOWN` | For a `METER` component with no selected Site-import role: `UNKNOWN` / `Meter role not established` / `No selected Site-import binding for this meter` / `Confirm meter topology and source binding` / null / `[]`. Never label an unbound connector meter as `SITE_METER`. |

**Tests.** `test_w503_ev_availability_postgres.py::test_status_gap_and_empty_schedule` and `test_w503_ev_depth_postgres.py::test_energy_health_selected_snapshot` assert the exact key sets and orders above.

**E1a read placement (A1Q W5S-5; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** Accepted `ev_connector_state` rows come only from the existing caller-connection `EvReadService.accepted_on(c, snap)` (`analytics/adapters/postgres_assessment_store.py:3050`; fields `role`, `value`, `source_time`, `connector_id`, `asset_id`, `quality`). The Foundation comes from `EvReadService.foundation_on(c, snap)` (`:3028`). Both run on the selected snapshot connection. `analytics/ev_availability.py` holds no SQL text; no `sqlalchemy`, `psycopg`, `alembic`, `yaml`, `pathlib` or `sqlite3` import; no text matching `open\(` in any letter case (so no identifier such as `is_open(`); no `import_module(`; and no module-level `ANALYTIC_ID` (rules 2 and 8 of `tools/checks/configuration-persistence.ps1`, rule 1 of `tools/checks/analytic-declaration.ps1`). The version constant is `CALCULATION_VERSION = "ev-availability/1"`. No `$pgReaders` edit. E1a/E1b add the caller-connection Foundation revision and selected-provenance methods specified in the 2026-10-23 pre-flight ruling.

## Unit E1b — selected Energy and Health depth API, W5-03a; per-unit review

One builder run, one to three commits and independent review before E2. Three depth routes compose on one REPEATABLE READ snapshot; selected energy and health rows cannot be re-read at another cutoff. The E1a decision clock/window applies to all E1b captures. Run `pytest backend/tests/test_w503_ev_depth_postgres.py -q` on a private `*_test` DB.

**E1b file list and tests.** E1b owns `backend/assetops_backend/analytics/ev_depth.py`, `backend/assetops_backend/ev_depth_api.py`, `backend/tests/test_w503_ev_depth_postgres.py`; shared **Lane A** `backend/assetops_backend/main.py` and `backend/assetops_backend/financials/composition.py` (A1Q W5S-6) , `backend/assetops_backend/ev_site_reads.py` and `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py` (closure 2: extract `_energy(ctx)` from `overview`, no behaviour change). It composes E1a availability with energy/Health from W2-06/07 selected rows on one read-only REPEATABLE READ connection and mounts the three cursorless routes. `test_w503_ev_depth_postgres.py::test_energy_health_selected_snapshot`, `::test_router_refusals_and_links` prove selected IDs, null semantics, malformed params and Site-code API links. E1b reviews before E2. No E1 run is allowed to span both algorithm and all three DTO implementations. EV `STALE_SOURCE` is an allowed wire enum but `analytics/ev_reads.currentness_state` never produces it; test its visible notice with a pure component fixture only, and do not claim a persisted stale capture.
**E1b composition (A1Q W5S-6/W5S-9; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** E1b composes W2-07 money through `EvMoneyReads`. Rule 1 lets only `financials/composition.py` import that adapter; the precedent is `build_ev_site_read_service`.

E1b appends to `financials/composition.py`:

```python
def build_ev_depth_read_service(database_url: str):
    """W5-03a E1b: EV Availability, Energy and Health depth over W2-06's `EvReadService` and the SELECT-only EV money
    reads, both on the one read connection (W2-07's shared selector)."""
    from assetops_backend.analytics.composition import build_ev_read_service
    from assetops_backend.analytics.ev_depth import EvDepthReadService
    from assetops_backend.ev_site_reads import EvSiteReads
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.financials.adapters.postgres_consequence_store import EvMoneyReads

    reads = build_ev_read_service(database_url)
    return EvDepthReadService(reads, EvSiteReads(reads, EvMoneyReads(build_link_rows_reader())))
```

`EvDepthReadService` exposes `dispose()` delegating to `reads.dispose()`. In `main.py`, directly after the `build_ev_site_router` include, add:

```python
    # W5-03a E1b (Lane A): selected EV Availability, Energy and Health depth; typed 503 without a database.
    ev_depth_reads = build_ev_depth_read_service(database_url()) if database_url() else None
    if ev_depth_reads is not None:
        app.router.on_shutdown.append(ev_depth_reads.dispose)
    app.include_router(build_ev_depth_router(registry, ev_depth_reads))
```

`analytics/ev_depth.py` obeys the same rule-2, rule-8 and analytic-declaration limits as W5S-5.

`ev_depth_api.py` contains none of `register_publication`, `register_authored`, `register_run`, `authored_record`, `simulation_records`, `publish_source`, `evidence_publication`, `batch_publication_link`, `run_attestation`, `evidence.publication`, `runs.source_publication` (`authored_basis` is allowed; `configuration-persistence.ps1` HTTP scan, A1Q W5S-9).

## Unit E2 — Availability page, W5-03a; per-unit review

Read: E2, literal ledger, measurements, E1 DTO. Files: new `frontend/src/sites/EvAvailability.tsx`, `frontend/src/sites/evDepthClient.ts`, `frontend/src/sites/__tests__/evDepth.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/shell/SiteAnalyticsFrames.tsx`, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/src/sites/EvAssessmentViews.tsx`, `frontend/src/sites/EvSiteViews.tsx`, `frontend/src/ui/V69Layout.tsx` (`SITE_SCREEN_DESCRIPTIONS.availability = "Performance · connector availability and unknown time"`), `tools/checks/navigation-truthfulness.ps1`, `tools/checks/navigation-rail-fixtures.ps1`. Replace only the EV unavailable `Availability` occurrence when route `/sites/{site_code}/performance/availability` renders. E2 creates `evDepthClient.ts` with validated Availability, Energy and Health reads and all three DTO types; E3/E4 may edit it for wiring while preserving all validators. Tests prove schedule only never shows a ratio, session-only never proves availability, accepted transition coverage conserves the three denominators, exact link/cutoff, pending/historical/unknown/refusal, and no dead link. Captures at 1440/390: `availability-observed` from E1a's persisted accepted UNPLUGGED/FAULTED state fixture, `availability-status-gap` from E1a's persisted accepted-state fixture with an intentional cadence-sized status gap, `availability-declared-empty-schedule` from E1a's persisted Foundation schedule fixture with an empty weekly list, `availability-pending`, `availability-historical`, `availability-refused`. All use the E1 producer window `[08:00,09:00)` and returned 09:00/09:05 watermarks; historical passes the saved 09:00 cutoff. E1a asserts the accepted status rows, ID set and nonzero classified spans before this capture. No fabricated screenshot snapshot. Run navigation guard fixtures; independent review before E3. E2 also owns `frontend/src/shell/evSiteRoutes.tsx`, `frontend/src/sites/__tests__/evAssessmentRoutes.test.tsx`, `frontend/src/test/settled.ts`, `frontend/src/ui/DataTable.tsx` and `frontend/src/ui/primitives.css`.
**E2 readiness pass 3 (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `evDepth.test.tsx::availability_states_bars_loading`).**

**E2 statuses and formats (closure 2; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).**
- **Status.** The status badge is always `Evidence limited`, for every `schedule_state` and selection state, because the page is an observed-state proxy that never certifies availability. The subtitle is the ledger constant.
- **Durations.** Card values for the three seconds keys use the shared duration format, or `Unknown` when null.
- **`Known-time availability`.** `(Math.round(Number(known_time_ratio) * 1000) / 10).toFixed(1) + "%"` (`0.933333` → `93.3%`), or `Unknown` when null.
- **`Full-schedule availability bound`.** Format each bound to two decimals and append one percent sign after the range; null stays `Unknown`. The exact DTO values remain unchanged.
- **Bound prose.** The mock lower/upper form uses selected available, unknown and scheduled durations; see the pre-flight E2 ruling.
- **Schedule panel copy.** `schedule_state` `NOT_ESTABLISHED` → `Service schedule not established for this window.`; `DECLARED_EMPTY` → `No service hours are declared in this window.`
- **Test.** `evDepth.test.tsx::availability_states_bars_loading` asserts all of the above.
- **Bars.** Div bars per connector contain ordered, window-aligned classified spans with blank unscheduled gaps, start/mid/end UTC labels, mock badge legend and a right-hand service period. Totals are accessible adjacent text. See the pre-flight E2 ruling.
- **Copy.** Loading, unavailable, refusal and currentness follow the shared capture-method section.
- **Captures.** Producers follow the shared method.
- **Depends on.** E1a/E1b merged reviews and the E1a/E1b wire payloads.

## Unit E3 — Energy page and W5-03a close; per-unit review

Read: E3, literal ledger, measurements, E1 DTO. Files: new `frontend/src/sites/EvEnergy.tsx`, `frontend/src/sites/__tests__/evEnergy.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/shell/SiteAnalyticsFrames.tsx`, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/src/sites/EvAssessmentViews.tsx`, `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `frontend/docs/architecture/v69-screen-ledger.json`, `frontend/src/sites/evDepthClient.ts`, `frontend/src/ui/V69Layout.tsx` (`SITE_SCREEN_DESCRIPTIONS.energy = "Performance · charging energy and site-power context"`), `tools/checks/navigation-truthfulness.ps1`, `tools/checks/navigation-rail-fixtures.ps1`. Replace only `Energy / site power` unavailable occurrence. Titled registry panels `(availability,1) Connector states over the service schedule`, `(availability,2) Full-schedule availability bound`, `(availability,3) Most useful next evidence`, `(energy,1) Import power and configured limit`, `(energy,2) What can be concluded`, `(energy,3) Technical-to-financial bridge`; map reviewed E1 and W2-07 fields, leave unsupported physical-limit and billing nodes unresolved. Tests assert complete versus partial energy, separate money consequence, sample peak wording, no below-limit exoneration and no unpriced-as-zero. Captures: `energy-complete`, `energy-missing-meter`, `energy-pending`, `energy-historical`, `energy-refused`, at 1440/390; producers are E1's existing complete/missing-meter/late vector builders and ev_gate refusal. Clock and historical cutoff as E1; route `/sites/{site_code}/performance/energy`. Run `tools/check-all.ps1`, one same-revision real-Postgres full suite, independent W5-03a review and merge. E3 also owns `frontend/src/sites/evDepthGraphics.tsx`, `frontend/src/ui/primitives.css`, `frontend/src/ui/DataTable.tsx`, `frontend/src/sites/__tests__/evAssessmentRoutes.test.tsx`, `frontend/src/test/settled.ts` and `tools/checks/shell-overflow.ps1`; its existing list is supplemented by these mandatory files.
**E3 readiness pass 3 (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `evEnergy.test.tsx::energy_states_table_loading`).**

**E3 cells and formats (closure 2; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `evEnergy.test.tsx::energy_states_table_loading`).**
- **Formats.** kW = the decimal string verbatim followed by ` kW`; kWh the same with ` kWh`. `Peak sample time (UTC)` = `HH:MM:SS UTC` of `peak_sample_at`, or `Unknown`. Money = `{amount} {currency}` with the amount verbatim.
- **Cards.**
  - `Metered session energy`: `metered_complete_kwh`, or `Unknown`.
  - `Observed peak import`: `observed_peak_import_kw`, or `Unknown`.
  - `Declared site limit`: `configured_import_limit_kw`, or `Unknown`.
  - `Gross tariff estimate`: when `consequence.state == "ESTIMATED"`, the money format; when `UNPRICED` or `WITHHELD`, `Unpriced`; when `consequence` is null, `Unknown`.
- **Status.** `Energy basis: measured` iff `metered_complete_kwh` is non-null and `unknown_seconds == 0`; otherwise `Energy basis: limited`.
- **Disclosures** (`<p className="prose">` lines directly below the cards):
  - when `partial_kwh` is non-null and `Number(partial_kwh) > 0`: `{partial_kwh} kWh from incomplete sessions is shown separately and not included.`
  - when `unknown_seconds > 0`: `Meter coverage is unknown for {duration} of session time.`
  - when `unknown_seconds` is null: `Meter coverage cannot be calculated for this window.`
  - otherwise no line.
- **`What can be concluded` answers.** Use the five mock key-value labels and tones. `Observed peak below limit` maps YES/NO/UNKNOWN to Yes/No/Unknown. `Site limit caused interruption` is amber `Not established`; `Requested vehicle power` is `Incomplete evidence`; `Stationary battery` is `Unknown` with the Foundation gap; `Billing settlement` is `Not connected`.
- **`Technical-to-financial bridge`.** A `DataTable` with columns `Quantity`, `Assumption`, `Result`, `Limit`.
  - **Row 1, when `consequence` is non-null:** `{consequence.quantity_kwh} kWh complete-record delivery` (or `Unknown`) / `{tariff_value} {currency}/kWh gross tariff scenario` when `ESTIMATED`, else `No eligible tariff applied` / `{amount} {currency} gross estimate` when `ESTIMATED`, else `Unpriced` / `consequence.limitation` verbatim, or `No collections or profit claim` when null.
  - **Row 1, when `consequence` is null:** `{metered_complete_kwh} kWh complete-record delivery` (or `Unknown`) / `No eligible gross tariff scenario.` / `Unpriced` / `No collections or profit claim`.
  - **Row 2, always:** retain mock `Incomplete session` / `No complete meter interval` / `Unavailable` / `No extrapolated energy silently added` when no selected partial amount; when partial kWh exists, use selected `{partial_kwh} kWh incomplete-session delivery` / `No complete meter interval` / `Not priced` / the same limit.
  - **Row 3, always:** `Interrupted service` / `No demand/sales baseline` / `Unpriced exposure` / `No invented lost revenue`.
- **`Import power and configured limit`.** The registered selected-sample chart specified in the pre-flight E3 ruling, followed by a `Measure`/`Value` disclosure.
- **`What can be concluded`.** The mock's heading-less key-value list with green/amber answer tones; see the pre-flight E3 ruling.
- **Copy.** Loading, unavailable, refusal and currentness follow the shared section.
- **Captures.** Producers follow the shared method.
- **Depends on.** E2 review and the E1a/E1b wire payloads.

**E3 exact route and energy rows.** Mount `/sites/{site_code}/performance/energy` in `App.tsx`/`operatorSiteRoutes.ts` and replace the `Energy / site power` unavailable entry in `EvAssessmentViews.tsx`; update `$expectedTabs` and the positive/negative `navigation-rail-fixtures.ps1` anchors. `test_w503_ev_depth_postgres.py::test_energy_baseline_rows` asserts this mapping before E3 captures:

| UI field | Merged source | Exclusion / null |
| --- | --- | --- |
| `Metered session energy` | selected W2-07 `overview.energy.complete_kwh` backed by complete `ev_session_revision.supported_kwh` | `partial_kwh` never added; absent complete sessions → `Unknown` |
| partial disclosure | selected `overview.energy.partial_kwh` | separate from complete; never silently zero |
| unknown coverage | selected `overview.energy.unknown_seconds` | retain null versus zero |
| `Observed peak import` | max accepted selected `ev_site_import` sample kW in window | no accepted sample → `Unknown` |
| `Declared site limit` | effective Foundation `ev-site-import-limit` | no selected property → `Unknown` |
| `Gross tariff estimate` | eligible selected `ev_consequence_revision` with exact tariff/currency basis | `UNPRICED`/`WITHHELD` → `Unpriced`, never zero or cash |

No below-limit sample proves no power constraint. The following E3 table is a summary; executable JSON and ledger values below are authoritative. E3 registry rows are summarized below; add new `I-W5-ev-depth-read` and `I-W5-ev-depth-ui` implementation nodes (`area:ev`, `status:open`, task W5-03a) with the rows in the same registry change. Status stays `gap` until reviewed:

| screen_id, panel_index, title | area | requires | status | reason |
| --- | --- | --- | --- | --- |
| `availability`, 1, `Connector states over the service schedule` | `ev` | `I-W5-ev-depth-read`, `I-W5-ev-depth-ui` | `gap` | `Selected connector states cover only cadence-bounded scheduled spans; gaps remain Unknown.` |
| `availability`, 2, `Full-schedule availability bound` | `ev` | `I-W5-ev-depth-read`, `I-W5-ev-depth-ui` | `gap` | `Bounds require a selected schedule and accepted state coverage; missing status remains Unknown.` |
| `availability`, 3, `Most useful next evidence` | `ev` | `I-W5-ev-depth-read`, `I-W5-ev-depth-ui` | `gap` | `The selected status gap identifies needed source history, not physical availability.` |
| `energy`, 1, `Import power and configured limit` | `ev` | `I-W5-ev-depth-read`, `I-W5-ev-depth-ui` | `gap` | `Accepted import samples and configuration do not establish a causal site-power limit.` |
| `energy`, 2, `What can be concluded` | `ev` | `I-W5-ev-depth-read`, `I-W5-ev-depth-ui` | `gap` | `Requested and allocated power evidence is absent; limit causation remains Unknown.` |
| `energy`, 3, `Technical-to-financial bridge` | `ev` | `I-W5-ev-depth-read`, `I-W5-ev-depth-ui` | `gap` | `Gross tariff consequence is bounded; billing settlement and lost sales are unsupported.` |

## Unit E4 — EV Health page, W5-03b; per-unit review

Read: E4, literal ledger, measurements, E1 DTO and the W5-03b pre-flight rulings below. Files: new `frontend/src/sites/EvHealthDepth.tsx`, `frontend/src/sites/__tests__/evHealthDepth.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/shell/SiteHealthFrames.tsx`, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `frontend/docs/architecture/v69-screen-ledger.json`, `frontend/src/sites/evDepthClient.ts`, `frontend/src/sites/EvFoundationViews.tsx`, `frontend/src/sites/__tests__/siteHealthBoundary.test.tsx`, `frontend/src/sites/__tests__/evFoundation.test.tsx`; run `frontend/docs/architecture/check_v69_dependency_registry.cjs`. Render the v69 EV Health composition: EV condition cards then the sole `Condition and evidence` panel; do not mount S7 `Data sources` or its battery Condition panel. SiteHealthFrames selects EV depth for EV Sites. `(ev-health,1) Condition and evidence` maps only observed selected fault and exact configuration; physical charger condition remains open. Captures: `ev-health-fault`, `ev-health-unknown`, `ev-health-pending`, `ev-health-historical`, `ev-health-refused`, 1440/390. Producer: E1's verified W2 fault/complete/late builders and ev_gate refusal; E1 window `[08:00,09:00)` and returned selection watermark; historical passes saved first cutoff. Assert no healthy charger from completed sessions. Independent review before E5.

**E4 Health composition and registry.** `SiteHealthFrames.tsx` renders three EV condition cards, the sole `Condition and evidence` panel, then the R16 notice. The existing EV Evidence `Data sources · data quality, not equipment condition` panel is the live source destination. In `EvFoundationViews.tsx` slots 631 and 688, use the existing Evidence href helper plus its existing source-panel fragment; preserve `from,to,known_at` only when all are present and valid, and preserve no `gateway` query. The link text is `Evidence › Data sources →`; assert destination and fragment in `siteHealthBoundary.test.tsx` and `evFoundation.test.tsx`. Preserve S7 acceptance without editing `SiteHealth.tsx`. Keep the mock 1200/1550px page cap and 330/440px condition panel cap at 1440/390; measure worst-case IDs, copy and notices. The two mock table rows are connector with a selected fault and Site meter; an additional non-fault connector row is R58 (D2), conditionally present. Use v69 `Supported assessment` and `Next evidence` headings. Source IDs are shown beside selected Foundation labels, not mock codes. Add `I-W5-ev-health-ui` (`kind:implementation`, `area:ev`, `status:open`, task W5-03b) and the existing JSON's `D-ev-domain` dependency to the `(ev-health,1)` row. Test `evHealthDepth.test.tsx::health_copy_and_sessions_destination` and exact `expectV69Panels("ev-health")` without changing the helper.

**E4 readiness pass 3 (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `evHealthDepth.test.tsx::health_states_loading`).**

**E4 cells, notice and links (closure 2; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `evHealthDepth.test.tsx::health_copy_and_sessions_destination`).**
- **Cards.** The three v69 card slots are connector 1, connector 2 and stationary battery. Connector `NEEDS_INVESTIGATION` displays `Needs attention` amber with selected fault count and no-diagnosis copy; `UNKNOWN` displays `Unknown` gray with an honest no-assessment note (R57 D4). Each connector has a separate `Sessions →` link. Battery displays `Not applicable` / `None installed` only when selected Foundation proves none installed; otherwise `Unknown` and the configuration gap (R56 D1). Selected server state and evidence determine the text; do not infer hardware health from a completed session.
- **`Condition and evidence`.** A `DataTable` with one row per `rows[]` entry.
  - `Asset` = selected Foundation `label`, then `asset_id` in a `data-vocabulary-exempt="source-reference"` span.
  - `Supported assessment` = `Session interruption; hardware fault not established` for a selected fault connector; `Power limit respected in observed samples` for Site meter only when selected samples prove it; otherwise the honest R59 gap. An optional non-fault connector gets the R58 no-assessment row.
  - `Next evidence` = `Diagnostic event + witnessed session` for connector; `Continuous coverage for interval-wide claims` for Site meter.
  - When `session_id` is non-null, the cell appends `Session {session_id}` (source-reference text) and a link `Open Sessions →`. Its href is `${sitePerformanceHref(site_code, "sessions")}${coldWindowSearch(window)}`, both existing helpers (`shell/operatorSiteRoutes.ts`, `sites/coldAssessmentClient.ts`), where `window` is the read's `{from, to, known_at}`.
- **Notice.** Directly below `Condition and evidence`, an amber `Notice` with exactly `Session and fault records show what was observed at each connector. They do not establish charger condition or diagnose a fault's cause.`
- **Validation.** `evDepthClient.ts` validates each row's `(kind, condition_state, observation, limitation, next_evidence)` against the E1b table; any other tuple renders the unavailable state.
- **Fragment.** Use the existing EV Evidence source-panel fragment, confirmed in the E4 test; do not link to `#site-health-sources-heading`.
- **Copy.** Loading, unavailable, refusal and the R15 currentness notice follow the shared section. Currentness sits above the cards; R16 condition notice sits directly below the table.
- **Captures.** Producers follow the shared method, with `ev-health-unknown` read on a window with no selection.
- **Depends on.** E3 merge and the E1a/E1b wire payloads.

## Unit E5 — authored EV scenario store, W5-03b; per-unit review

Allowed authored what-if contract `ev-scenario-authored/1`: the only `kind` is `GROSS_TARIFF_CONTEXT`; the assumption object is exactly `{tariff_per_kwh,currency}` with positive decimal string at most 8 fractional digits and uppercase three-letter ISO 4217 currency. The baseline is the selected W2-07 `ev_session_revision` rows for which `ev_reads.energy_complete(state,supported_kwh,unknown_meter_seconds) is True`, with their exact accepted meter evidence IDs. Persist those session revision IDs and the selected `ev_consequence_revision.id`/tariff revision ID only when a priced consequence exists; no metered-energy table exists. A zero-row complete-meter selection refuses `EV_SCENARIO_INVALID`. There is no computed money amount, collected revenue, lost sales, comparison delta or observed outcome in this contract. Formula version is `AUTHORED_ONLY/1`; scope is one authorized EV Site and one selected half-open UTC period at most 31 days. Cross-Site, currency conversion and a scenario with no exact selected complete `ev_session_revision` are refused as `EV_SCENARIO_INVALID`. This keeps the Scenario tab an authored-basis list while W2-07 continues to own measured energy and eligible gross tariff consequence.

Read: E5, selected contract, merged W4-03 `mini_decisions/scenarios.py` command/actor pattern. Files: **Lane A only** `backend/migrations/versions/0034_w5_ev_scenarios.py`, new `backend/assetops_backend/ev_scenarios/{rules,store,service}.py`, `ev_scenarios_api.py`, `backend/tests/test_w503_ev_scenarios_postgres.py`; shared `backend/assetops_backend/main.py`, `tools/checks/configuration-persistence.ps1` and `tools/writer_guard_probes.py` (A1Q W5S-7). Migration creates scoped `ev_scenario` and append-only `ev_scenario_revision` with the identity/actor/idempotency/prior/correction/check/composite-Site-FK shape of W5-01 C4. It carries `basis_sha256`, selected session/assessment/accepted evidence/Foundation/tariff revision IDs and assumptions. There is no observed-outcome column, field, enum or status. Unique `(scenario_id,revision_no)` and `(scenario_id,idempotency_key)`; correction appends only. Existing decision principal protects `POST /api/sites/{code}/ev/financials/scenarios` and `POST .../{scenario_id}/revisions`; ordinary viewers have `GET ...?from=&to=&known_at=&scenario_at=&limit=&cursor=`. DTO `ev-scenarios-1`: watermarked scoped list with separate `scenario_at`, immutable revision IDs, `DEFINED` or read-only `HISTORICAL`; default 50/max 100, cursor binds Site/window/evidence cutoff/scenario_at/watermark/last `(recorded_at,id)`. New typed codes: `EV_SCENARIO_INVALID` 422, `EV_SCENARIO_CURSOR_INVALID` 422, `EV_SCENARIO_CURSOR_BASIS_CHANGED` 409, `EV_SCENARIO_IDEMPOTENCY_CONFLICT` 409, `EV_SCENARIO_REVISION_CONFLICT` 409; existing EV access/unavailable codes remain. No default row, inferred tariff, collections, lost revenue, verified outcome or mutable measured consequence. Test migration upgrade/downgrade/sole head after exact `0033_w5_cold_work`, actor scope, idempotency, foreign ID, cutoff/cursor, empty/failed and a real persisted POST. The positive producer for E6 is this POST proved by `test_w503_ev_scenarios_postgres.py` with E1's exact selected IDs; it must pass review before E6. The EV selection uses the E1 09:00/09:05 decision watermark; server scenario `recorded_at` and default `scenario_at` are DB wall time. Save `scenario_at` after first POST, append correction later, and pass saved `scenario_at` to read the prior authored revision. Do not use 16:05/16:07 as a selected evidence cutoff. Independent review gates E6.

**E5 exact persisted schema and wire contract.** Migration `0034_w5_ev_scenarios` first creates `ev_scenario_public_no_seq`, then `ev_scenario` with `id uuid PK`, `tenant_id uuid NOT NULL`, `site_id uuid NOT NULL`, `public_no bigint NOT NULL DEFAULT nextval('ev_scenario_public_no_seq')`, `create_key text NOT NULL`, `create_payload_sha256 text NOT NULL`, `create_actor_id text NOT NULL`, `created_at timestamptz NOT NULL DEFAULT clock_timestamp()`, `actor_kind text NOT NULL`, `actor_id text NOT NULL`; named `ev_scenario_scope_uk(tenant_id,site_id,id)`, `ev_scenario_public_no_uk(tenant_id,public_no)`, `ev_scenario_create_key_uk(tenant_id,site_id,create_key)` and `ev_scenario_site_fk(tenant_id,site_id)` to `site(tenant_id,id)`. Root checks `ev_scenario_create_key_check` length 8..128, `ev_scenario_create_payload_sha256_check` 64 lowercase hex, `ev_scenario_create_actor_id_check` trimmed length 1..128. `ev_scenario_revision` columns: `id uuid PK`, `tenant_id uuid NOT NULL`, `site_id uuid NOT NULL`, `scenario_id uuid NOT NULL`, `revision_no integer NOT NULL`, `supersedes_revision_id uuid NULL`, `name text NOT NULL`, `kind text NOT NULL`, `assumptions jsonb NOT NULL`, `authored_basis jsonb NOT NULL`, `basis_sha256 text NOT NULL`, `formula_version text NOT NULL`, `correction_reason text NULL`, `actor_kind text NOT NULL`, `actor_id text NOT NULL`, `authorization_basis text NOT NULL`, `attestation text NOT NULL`, `idempotency_key text NOT NULL`, `payload_sha256 text NOT NULL`, `recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()`. Named checks `ev_scenario_revision_revision_no_check` (>0), `ev_scenario_revision_name_check` (trimmed 1..160), `ev_scenario_revision_kind_check` (`GROSS_TARIFF_CONTEXT`), `ev_scenario_revision_formula_check` (`AUTHORED_ONLY/1`), `ev_scenario_revision_chain_check` (same first/later rule C4), `ev_scenario_revision_basis_sha256_check` and `ev_scenario_revision_payload_sha256_check` (each 64 lowercase hex), `ev_scenario_revision_idempotency_key_check` (length 8..128), `ev_scenario_revision_actor_check` (nonempty actor kind/id/authorization basis/attestation). Named composite scoped FKs are `ev_scenario_revision_scenario_fk(tenant_id,site_id,scenario_id)` and `ev_scenario_revision_previous_fk(tenant_id,site_id,supersedes_revision_id)`; unique constraints are `ev_scenario_revision_scope_uk(tenant_id,site_id,id)`, `ev_scenario_revision_no_uk(scenario_id,revision_no)`, `ev_scenario_revision_previous_uk(scenario_id,supersedes_revision_id)`, `ev_scenario_revision_key_uk(scenario_id,idempotency_key)`. Index `ev_scenario_site_order(tenant_id,site_id,recorded_at DESC,id)`. Downgrade removes index, revision, root, then sequence. `0033_w5_cold_work` is a W5-02 naming obligation; W5-02's task must adopt that exact ID before E5 migration runs.

POST root and correction take gate query `from,to,known_at`; `from,to` are required, paired strict UTC and at most 31 days. Optional `known_at` selects evidence within the write snapshot. Unknown/repeated query keys use `EV_PARAMETER_UNKNOWN` 422. No body pin can override selected Site or window. Server-resolved `authored_basis` JSON has closed keys `{from,to,cutoff,assessment_revision_id,session_revision_ids,accepted_evidence_ids,foundation_revision_id,consequence_revision_id,tariff_revision_id,source_provenance}`; last two IDs are nullable, and all selected UUID lists are sorted/deduplicated. SQL checks require assumptions/basis to be JSON objects; exact key grammar and selected-ID membership are service rules. Root `create_payload_sha256` hashes canonical command and query/window for same-key replay.

**Metered-energy baseline table (test `test_w503_ev_scenarios_postgres.py::test_complete_session_baseline`).**

| Stored basis field | Exact merged source | Refusal / null rule |
| --- | --- | --- |
| `session_revision_ids` | selected `ev_session_revision.id` where `ev_reads.energy_complete(state,supported_kwh,unknown_meter_seconds) is True` | empty → 422 `EV_SCENARIO_INVALID`; never use an incomplete meter row |
| `accepted_evidence_ids` | accepted meter evidence IDs cited by those selected session revisions | empty/foreign → 422 `EV_SCENARIO_INVALID` |
| `assessment_revision_id` | selected W2-06 EV assessment revision | absent → 422 `EV_SCENARIO_INVALID` |
| `foundation_revision_id` | effective selected EV Foundation | absent/foreign → 422 `EV_SCENARIO_INVALID` |
| `consequence_revision_id`, `tariff_revision_id` | selected W2-07 `ev_consequence_revision` and its cited tariff revision if eligible | nullable; no priced consequence is invented |
| `cutoff` | selected snapshot's returned `known`/`committed_watermark` (09:00/09:05 only in the fixed E1 fixture) | later than current watermark → 422 `EV_TIME_INVALID` |

POST root closed body `{schema_version:"ev-scenario-command-1",idempotency_key:string,actor:{kind:"SERVICE",id:string,attestation:string},name:string,kind:"GROSS_TARIFF_CONTEXT",assumptions:{tariff_per_kwh:string,currency:string}}`; correction adds `supersedes_revision_id` UUID and `correction_reason` 1..2000. Server resolves exact complete `ev_session_revision` rows and selected IDs within the write snapshot. No client pin/basis field. Missing/non-SERVICE principal or wrong scope/grant → 403 `DECISION_WRITE_FORBIDDEN`; USER actor → 403 `DECISION_USER_AUTH_REQUIRED`; bad attestation → 422 `DECISION_ATTESTATION_INVALID` (merged `mini_decisions/model.py:34`); missing exact complete sessions or invalid assumptions/basis → 422 `EV_SCENARIO_INVALID`; same key/different body → 409 `EV_SCENARIO_IDEMPOTENCY_CONFLICT`; stale prior → 409 `EV_SCENARIO_REVISION_CONFLICT`; store unavailable → 503 `DECISION_STORE_UNAVAILABLE` or `EV_READ_UNAVAILABLE`; read gate retains `UNAUTHENTICATED`, `SITE_SCOPE_FORBIDDEN`, `SITE_NOT_FOUND`, `EV_SOURCE_DISCLOSURE_FORBIDDEN`. New write returns 201 `{schema_version:"ev-scenario-write-1",id,code:"ESCN-000001",revision_id,revision_no}`; exact replay returns 200 same body. Public number uses global `ev_scenario_public_no_seq`, `ESCN-` plus six minimum zero-padded decimal digits.

| E5 refusal | HTTP | Trigger |
| --- | ---: | --- |
| `UNAUTHENTICATED` | 401 | Missing authenticated request |
| `SITE_SCOPE_FORBIDDEN`, `EV_SOURCE_DISCLOSURE_FORBIDDEN` | 403 | Site or source disclosure denied |
| `DECISION_WRITE_FORBIDDEN`, `DECISION_USER_AUTH_REQUIRED` | 403 | Service principal or actor rejected |
| `DECISION_ATTESTATION_INVALID` | 422 | Malformed service attestation |
| `SITE_NOT_FOUND` | 404 | No authorized EV Site |
| `EV_PARAMETER_UNKNOWN`, `EV_TIME_INVALID`, `EV_WINDOW_INVALID`, `EV_WINDOW_TOO_LONG`, `EV_SCENARIO_INVALID`, `EV_SCENARIO_CURSOR_INVALID` | 422 | Query, time, body, basis or cursor invalid |
| `EV_SCENARIO_CURSOR_BASIS_CHANGED`, `EV_SCENARIO_IDEMPOTENCY_CONFLICT`, `EV_SCENARIO_REVISION_CONFLICT` | 409 | Changed selection, replay body or predecessor |
| `EV_READ_UNAVAILABLE`, `DECISION_STORE_UNAVAILABLE` | 503 | Selected read or authored store unavailable |

GET list `ev-scenarios-1` is `{schema_version,site_id,window:{from,to,known_at,committed_watermark},scenario_at,selection:{state,assessment_revision_id,session_revision_ids,accepted_evidence_ids,source_provenance},items:[{id,code,revision_id,revision_no,name,kind,assumptions,authored_basis,recorded_at,scenario_state}],next_cursor}`. Pending comes from the selected W2 EV assessment `selection.state`; historical follows the EV precedence of `ev_reads.currentness_state`. Revision 1 `authored_basis.from,to` fixes each root window. A correction resolves its query `from,to` and must equal revision 1 exactly; mismatch returns 422 `EV_SCENARIO_INVALID` before append. Test same-window correction and cross-window refusal. Include only roots whose revision 1 `authored_basis.from,to` equals requested period; choose latest revision where `recorded_at <= scenario_at` and `authored_basis.cutoff <= window.known_at`. `scenario_state=HISTORICAL` iff superseded at current authored DB time or caller `scenario_at` precedes the latest stored revision or `known_at` precedes the current evidence watermark; else `DEFINED`. If `scenario_at` is omitted, resolve DB `clock_timestamp()` in the read snapshot; explicit UTC `scenario_at` after DB now refuses 422 `EV_TIME_INVALID`. The 09:00/09:05 evidence clock is independent of DB authored time; current authored rows remain visible even when the selected evidence watermark is 09:00. Cursor binds Site/window/evidence cutoff/scenario_at/watermark/last row and returns 422 invalid or 409 changed basis. Tests `test_w503_ev_scenarios_postgres.py::test_command_refusals_and_replay`, `::test_pending_historical_list_and_cursor`, `::test_schema_constraints`.

**E5 guard and composition ownership (A1Q W5S-7/W5S-8/W5S-9; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** `ev_scenarios/store.py` is a new product database writer. Apply the rule-8 policy text from W5-01 C4 "C4 guard and composition ownership" (`.agent/W5-01-build-spec.md`, steps 1–9) to `configuration-persistence.ps1` and `writer_guard_probes.py`, with exactly these substitutions:

| W5-01 C4 text | E5 text |
| --- | --- |
| `W5-01b C4 (migration 0032)` | `W5-03b E5 (migration 0034)` |
| `$coldScenarioWriter` | `$evScenarioWriter` |
| `$coldScenarioTables` | `$evScenarioTables` |
| `$coldScenarioInsertsSeen` | `$evScenarioInsertsSeen` |
| `cold_scenarios/store.py` | `ev_scenarios/store.py` |
| `'cold_scenario', 'cold_scenario_revision'` | `'ev_scenario', 'ev_scenario_revision'` |
| message words `cold scenario` / `Cold scenario` | `EV scenario` / `EV scenario` |
| probe prefix `cold-scenario` | `ev-scenario` |
| `COLD_SCENARIO` | `EV_SCENARIO` |
| `_cold_scenario_only` / `_cold_scenario_unseen` | `_ev_scenario_only` / `_ev_scenario_unseen` |
| truncate probe `"TRUNCATE cold_scenario"` | `"TRUNCATE ev_scenario"` |

Insert every E5 block directly after the corresponding C4 block. If W5-01b has not merged when E5 runs, insert after the mini-decision block instead. `ev_scenarios_api.py` contains none of `register_publication`, `register_authored`, `register_run`, `authored_record`, `simulation_records`, `publish_source`, `evidence_publication`, `batch_publication_link`, `run_attestation`, `evidence.publication`, `runs.source_publication` (`authored_basis` is allowed; `configuration-persistence.ps1` HTTP scan, A1Q W5S-9).

Lane A wiring in `main.py`: add the imports `EvScenarioService`, `PostgresEvScenarioStore` and `build_ev_scenarios_router`, and after the E1b mount add:

```python
    # W5-03b E5: authored EV scenarios. Writes need the two explicit decision injections; reads use the EV gate.
    ev_scenario_store = PostgresEvScenarioStore.from_url(database_url()) if ev_reads is not None else None
    if ev_scenario_store is not None:
        app.router.on_shutdown.append(ev_scenario_store.dispose)
    app.include_router(build_ev_scenarios_router(
        registry, None if ev_scenario_store is None else EvScenarioService(ev_scenario_store, ev_reads),
        command_access=mini_decision_command_access, principal=mini_decision_principal))
```

The service resolves eligible `ev_consequence_revision` and tariff IDs through the new public caller-connection `EvSiteReads` method inside the store's write snapshot. That method reuses W2-07 selection and guard policy; the E5 store does not duplicate the money predicate or import a `financials` adapter. Add `backend/assetops_backend/ev_site_reads.py` and `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py` to E5 Lane A ownership, together with the 18 sole-head tests in the pre-flight section below.

## Unit E6 — EV Scenarios page and W5-03b close; per-unit review

Read: E6, measurement table, E5 DTO and literal page copy below. Files: new `frontend/src/sites/EvScenarios.tsx`, `frontend/src/sites/evScenariosClient.ts`, `frontend/src/sites/__tests__/evScenarios.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/sites/EvSiteViews.tsx`, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `frontend/docs/architecture/v69-screen-ledger.json`, `frontend/src/shell/evSiteRoutes.tsx`, `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx`, `tools/checks/navigation-truthfulness.ps1`, `tools/checks/navigation-rail-fixtures.ps1`. Replace the EV `<UnavailableTab label="Scenarios" />` in `EvSiteViews.tsx` after `/sites/{site_code}/ev/financials/scenarios` is live; leave the shared non-EV fallback without editing `SiteAnalyticsFrames.tsx`. Preserve `from,to,known_at` throughout Financials and `scenario_at` on the Scenarios entry only. Registry `(ev-scenarios,1) Financial scenarios` maps E5 authored list/empty; add no observed-outcome technical node. Captures are in E6, the page-owning unit.

Page literals: h1 is the selected Site name; subtitle `Financials · scenarios (placeholder)`; panel `Financial scenarios` with icon/meta `Placeholder · to be designed with the owner`; empty title `No scenario defined yet`; body `A scenario compares a declared what-if with the measured case, for example a different stop setting, stock value or tariff. None has been defined for this site.`; blue notice `Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.` Persisted rows replace only the empty block (R27 D2). Row labels are `Authored scenario`, `Assumptions`, `Basis`, `Defined at`; `Defined` or `Historical`; `Review assumptions →` expands the stored basis. Pending notice `Underlying evidence is being reassessed; the authored scenario remains separate.` Refusal heading `EV scenarios unavailable`, exact server error and `Retry`. No create control for ordinary viewer.

**E6 readiness pass 3 (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `evScenarios.test.tsx::routes_states_loading`).**

**E6 scenario row, page and client (closure 2; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `evScenarios.test.tsx::row_disclosure_and_client`).**
- **Page frame.** Breadcrumb `Sites › {Site name} › Financials › Scenarios`; h1 `{Site name}`. Use a screen-scoped description override `Financials · scenarios (placeholder)` without changing shared `SITE_SCREEN_DESCRIPTIONS.scenarios` or `V69Layout.tsx`.
- **Item table.** Items render in one `DataTable` inside `Financial scenarios`, with columns `Authored scenario`, `Assumptions`, `Basis`, `Defined at`, `State` and one row per `items[]` entry in DTO order.
  - `Authored scenario`: `name`, then on a second line `code` and `revision {revision_no}`, the code inside `data-vocabulary-exempt="source-reference"`.
  - `Assumptions`: `{tariff_per_kwh} {currency}/kWh gross tariff`. Decimal strings are printed verbatim.
  - `Basis`: `Selected evidence through {cutoff}`, with `cutoff` formatted `YYYY-MM-DD HH:MM UTC`, then a `<button type="button" aria-expanded>` labelled `Review assumptions →`.
  - `Defined at`: `recorded_at` as `YYYY-MM-DD HH:MM UTC`.
  - `State`: a neutral `Badge` whose text comes from `scenario_state`: `DEFINED` → `Defined`, `HISTORICAL` → `Historical`.
- **`Review assumptions →` expansion.** A full-width row directly below its item, scrolled internally at 390 (360px cap). It is a `<dl>` with these terms in order, every ID in a `data-vocabulary-exempt="source-reference"` span with character breaks and one ID per line:
  - `Kind` → `GROSS_TARIFF_CONTEXT`
  - `Assumptions` → each key and value, one per line: tariff_per_kwh,currency
  - `Window` → `authored_basis.from` – `authored_basis.to` (ISO, verbatim)
  - `Evidence cutoff` → `authored_basis.cutoff`
  - `Assessment revision` → `authored_basis.assessment_revision_id`
  - `Session revisions` → `authored_basis.session_revision_ids`
  - `Accepted evidence` → `{n} records`, then each `authored_basis.accepted_evidence_ids` entry
  - `Foundation revision` → `authored_basis.foundation_revision_id`
  - `Consequence revision` → `authored_basis.consequence_revision_id`
  - `Tariff revision` → `authored_basis.tariff_revision_id`
  - `Source classification` → `authored_basis.source_provenance.classification`
  - `Revision` → `revision_id`
  A null ID prints `None`.
- **Client.** `frontend/src/sites/evScenariosClient.ts` validation; any violation is the unavailable state.
  - Top level: exact keys `schema_version` (`"ev-scenarios-1"`), `site_id`, `window` (exact `from,to,known_at,committed_watermark`), `scenario_at`, `selection` (exact `state,assessment_revision_id,session_revision_ids,accepted_evidence_ids,source_provenance`), `items`, `next_cursor` (string or null).
  - Item: exact keys `id`, `code` (matches `^ESCN-\d{6,}$`), `revision_id`, `revision_no` (integer ≥ 1), `name` (string of 1–160 characters), `kind` (`"GROSS_TARIFF_CONTEXT"`), `assumptions` (exact keys `tariff_per_kwh,currency`, all strings, `currency` matching `^[A-Z]{3}$`), `authored_basis` (exact keys `from,to,cutoff,assessment_revision_id,session_revision_ids,accepted_evidence_ids,foundation_revision_id,consequence_revision_id,tariff_revision_id,source_provenance`), `recorded_at` (string), `scenario_state` (`DEFINED` or `HISTORICAL`).
  - `selection.state` is one of the five STATES.
- **Refusal heading.** `EV scenarios unavailable`.
- **Routes.** `operatorSiteRoutes.ts`: `SITE_EV_SUFFIX` gains `scenarios: "/financials/scenarios"`.
  - `EvSiteViews.tsx`: `EvSiteRoutes` gains `scenarios: string`; `EvSiteView` gains `"scenarios"`. The Financials subtab list replaces `<UnavailableTab label="Scenarios" />` with a live `["scenarios", "Scenarios", sel(routes.scenarios, window)]` entry, carrying `scenario_at` when present.
  - `shell/evSiteRoutes.tsx`: add `scenarios: siteEvHref(siteId, "scenarios"),` and `CURRENT_TAB.scenarios = "Financials"`.
- **Currentness.** The EV ledger state sentences apply, except `PENDING_RECOMPUTE`, which keeps the E6 pending notice.
- **Copy.** Loading, unavailable and refusal follow the shared section.
- **Captures.** `ev-scenarios-refused` is the shared 422 `from>to` refusal.
- **Depends on.** E5 merged review.

E6 adds registry node `I-W5-ev-scenario-read` and `I-W5-ev-scenario-ui` (`kind:implementation`, `area:ev`, `status:open`, task W5-03b) and summary row `screen_id:ev-scenarios`, `panel_index:1`, `title:Financial scenarios`, `area:ev`, `requires:[I-W5-ev-scenario-read,I-W5-ev-scenario-ui]`, `status:gap`, `reason:Authored tariff context is listed separately from selected metered energy and any observed outcome.` Exact basis disclosure is internally scrolled at 390; the one-row panel cap does not cap unlimited expanded text. Test `evScenarios.test.tsx::basis_disclosure_and_pending_historical`.

Captures: `ev-scenarios-empty` (GET before POST), `ev-scenarios-authored` (new POST), `ev-scenarios-historical` (correction and saved pre-correction `scenario_at`), `ev-scenarios-pending` (late-record builder with authored row), `ev-scenarios-refused` (gate), at 1440/390. Positive producer is the new persisted command path proved by `test_w503_ev_scenarios_postgres.py`; its seed uses E1's exact selected EV IDs. Use the E1 09:00/09:05 evidence watermark and the saved pre-correction `scenario_at`; no 16:05 pin. Expanded basis has a 360px internal scroller, exact full IDs with character breaks, and its own 390 capture. Run the W1 vocabulary scan, exempt raw IDs using `data-vocabulary-exempt="source-reference"`; do not apply T028 vocabulary to a page whose title is `Scenarios`. UI tests assert empty, authored, historical, pending and refused copy, exact basis disclosure, no invented outcome and no dead links. Run focused tests, `tools/check-all.ps1`, one W5-03b full real-Postgres suite, 1440/390 caps, independent review/merge before W5-04.

### Executable registry and ledger amendment

Apply these exact JSON objects to the registry in the named unit only. Insert each node once; append each panel once. For the four EV screens, set `registry_dependencies.product_node_id` to `P-ev-area` and `registry_dependencies.node_ids` to the ordered unique concatenation of that screen’s panel `requires` arrays. E3 owns availability and energy ledger edits; E4 owns ev-health; E6 owns ev-scenarios. Status remains `gap` and nodes remain `open` until independent review.

**E3 — registry nodes**

```json
[
  {
    "id": "I-W5-ev-depth-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "ev",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-ev-site-projections"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W5-03a",
    "acceptance_target": "Reviewed selected read with exact evidence lineage and bounded unknown states."
  },
  {
    "id": "I-W5-ev-depth-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "ev",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-ev-site-projections",
      "I-W5-ev-depth-read"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-03a",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps, 1440/390 captures and preserved gateway panel where applicable."
  }
]
```

**E3 — panel rows**

```json
[
  {
    "screen_id": "availability",
    "panel_index": 1,
    "title": "Connector states over the service schedule",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Selected connector states cover only cadence-bounded scheduled spans; gaps remain Unknown."
  },
  {
    "screen_id": "availability",
    "panel_index": 2,
    "title": "Full-schedule availability bound",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Bounds require a selected schedule and accepted state coverage; missing status remains Unknown."
  },
  {
    "screen_id": "availability",
    "panel_index": 3,
    "title": "Most useful next evidence",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "The selected status gap identifies needed source history, not physical availability."
  },
  {
    "screen_id": "energy",
    "panel_index": 1,
    "title": "Import power and configured limit",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Accepted import samples and configuration do not establish a causal site-power limit."
  },
  {
    "screen_id": "energy",
    "panel_index": 2,
    "title": "What can be concluded",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Requested and allocated power evidence is absent; limit causation remains Unknown."
  },
  {
    "screen_id": "energy",
    "panel_index": 3,
    "title": "Technical-to-financial bridge",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Gross tariff consequence is bounded; billing settlement and lost sales are unsupported."
  }
]
```

E3 ledger `availability`: `registry_dependencies` = {"product_node_id": "P-ev-area", "node_ids": ["I-W5-ev-depth-read", "I-W5-ev-depth-ui", "D-ev-domain"]}.

E3 ledger `energy`: `registry_dependencies` = {"product_node_id": "P-ev-area", "node_ids": ["I-W5-ev-depth-read", "I-W5-ev-depth-ui", "D-ev-domain"]}.

**E4 — registry nodes**

```json
[
  {
    "id": "I-W5-ev-health-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "ev",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-ev-site-projections"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-03b",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps, 1440/390 captures and preserved gateway panel where applicable."
  }
]
```

**E4 — panel rows**

```json
[
  {
    "screen_id": "ev-health",
    "panel_index": 1,
    "title": "Condition and evidence",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-health-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Selected faults warrant investigation but do not diagnose charger condition."
  }
]
```

E4 ledger `ev-health`: `registry_dependencies` = {"product_node_id": "P-ev-area", "node_ids": ["I-W5-ev-depth-read", "I-W5-ev-health-ui", "D-ev-domain"]}.

**E6 — registry nodes**

```json
[
  {
    "id": "I-W5-ev-scenario-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "ev",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-ev-site-projections"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W5-03b",
    "acceptance_target": "Reviewed selected read with exact evidence lineage and bounded unknown states."
  },
  {
    "id": "I-W5-ev-scenario-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "ev",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-ev-site-projections",
      "I-W5-ev-scenario-read"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-03b",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps, 1440/390 captures and preserved gateway panel where applicable."
  }
]
```

**E6 — panel rows**

```json
[
  {
    "screen_id": "ev-scenarios",
    "panel_index": 1,
    "title": "Financial scenarios",
    "area": "ev",
    "requires": [
      "I-W5-ev-scenario-read",
      "I-W5-ev-scenario-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Authored tariff context is listed separately from selected metered energy and any observed outcome."
  }
]
```

E6 ledger `ev-scenarios`: `registry_dependencies` = {"product_node_id": "P-ev-area", "node_ids": ["I-W5-ev-scenario-read", "I-W5-ev-scenario-ui", "D-ev-domain"]}.

## Readiness closure

| Review item | Closing artifact location |
| --- | --- |
| 28 | E1a producer clock |
| 29 | E2/E3/E6 file lists |
| 30 | E2/E3/E6 routes and E4 Sessions link |
| 31 | E3/E4/E6 registry rows |
| 32 | Shared availability calculation |
| 33 | Shared EV Health battery state |
| 34 | E1a/E1b fixed regression vector; W5-03b P-34 generic-cutoff and 422 tests; W5-04 V1a owns and must verify the generated EV producer and wall-clock K2 mapping. Not closed until V1a proof. |
| 35 | E1b STALE fixture rule |
| 36 | Shared API links |
| 37 | E1a persisted fixtures and E2 captures |
| 38 | Shared literal ledger |
| 39 | E3 metered-energy table |
| 40 | E4 Health composition |
| 41 | E5 baseline entity |
| 42 | E5 persisted schema, POST and list |
| 43 | E5 migration and W5-02 packet |
| 44 | E6 page and disclosure |
| 45 | Gate and E1a/E1b sizing |
| 46 | Gate and guards |
| V1 (review 31) | E3/E4/E6 executable node, panel and ledger JSON below; applied together to a scratch registry and the dependency checker passed on 2026-10-22. |
| V2 | Superseded by W5-03b pre-flight: E4 removes the S7 gateway panel as D3 R60, points EV Foundation at EV Evidence sources, and restores mock page caps. |
| V3 | E5 POST and refusal table use merged 422. |
| V4 | E5 revision-1 window rule and cross-window correction refusal. |
| V5 | Availability calculation and E2 literal distinguish absent schedule from declared empty `weekly: []`. |
| V6 | E2/E3/E4 client ownership and validator scope. |
| A1Q-W5S-5 | E1a read placement: `EvReadService.accepted_on`, `foundation_revision_on` and selected provenance; `CALCULATION_VERSION`; the rule-2, rule-8 and declaration limits. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
| A1Q-W5S-6 | E1b composition: the `financials/composition.py` builder `build_ev_depth_read_service` and the `main.py` mount; the file is in the E1b list. |
| A1Q-W5S-7 | E5 guard and composition ownership: the W5-01 C4 rule-8 policy with the EV substitution table; both guard files are in the E5 list. |
| A1Q-W5S-8 | E5 `main.py` store and router wiring with the decision injections. |
| A1Q-W5S-9/10/11 | HTTP-scan token sentences in E1b and E5; the DataTable/svg sentence in "Mock measurement and rendering limits" (applies to E2, E3, E4 and E6); shared guard-file serialization in the gate section. |
| RP3-E2 (5) | E2 readiness pass 3: `V69Layout.tsx` description, div bars, loading/unavailable, currentness notice, capture method; depends on the E1a/E1b wire payloads. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
| RP3-E3 (5) | E3 readiness pass 3: `V69Layout.tsx` description, restored import chart and mock conclusion list under the later pre-flight ruling, loading/currentness and capture method. |
| RP3-E4 (4) | E4 readiness pass 3: fragment literal, loading/currentness, unknown/refused producers, DTO dependency. |
| RP3-E6 (4) | E6 readiness pass 3: `evSiteRoutes.tsx` and route-key literals, currentness, loading/unavailable, refused capture. |
| RP3-E1 (1, closed in closure 2) | "E1a/E1b wire payloads" tables for availability, energy and health. |
| RP3-shared | "Capture producer method, loading and unavailable copy" section before E1a. |
| CL2-E1 | E1a/E1b wire payloads: shared envelope, `availability`, `energy` and `health` key tables (`ev_site_reads.py` added to E1b). *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
| CL2-1 (E4) | E4 notice literal. |
| CL2-2/3 (E6) | E6 scenario row, page and client: DataTable, pill source, expansion, `evScenariosClient` validator, breadcrumb and existing description. |
| CL2-4 (E2) | E2 status rule, percentage and bound formats, bound prose. |
| CL2-5 (E3) | E3 bridge cells with wire fields, partial/unknown disclosures, kW/kWh/time/money formats, status rule. |
| CL2-6 (E4) | E4 Asset cell, server-owned observation/next-evidence strings, Sessions link helpers. |

## Codex retrospective of Claude Architect rulings (2026-10-22)

Checked `availability`, `energy`, `ev-health` and `ev-scenarios` against v6.9 `index.html` and `screen-manifest.json`, the W2 EV read code and the technical design. These decisions supersede conflicting E2/E3 rendering sentences above.

| Ruling | Verdict and reason | Alternative / exact correction |
| --- | --- | --- |
| E2 `div` connector bars, no SVG | **KEEP — MOCK DEVIATION (D4) only for selected data and missing states; the graphic form matches the mock.** The mock draws `bar-row`/`track` with colored `div` segments, legend and time-axis labels. Its percentages and eight-hour example are illustrative. An SVG chart in a registered graphics module was considered, but would add no fidelity. | In `EvAvailability.tsx`, draw one colored segment per ordered `availability.connectors[].spans` entry, using its `from/to` duration for width and its `state` for color. Do not collapse alternating spans into three category totals on a time axis; the three totals stay in the adjacent text. Align the track to the selected UTC window and show start/midpoint/end UTC labels derived from that window, never the mock's fixed 08:00/12:00/16:00. Do not color unscheduled gaps as available; leave them blank and label them outside the scheduled denominator. Unknown or declared-empty schedule keeps the truthful no-bar state. `evDepth.test.tsx::availability_states_bars_loading` asserts order, widths, blank gaps and labels; recapture the E2 observed/status-gap/empty cases at 1440/390. |
| E3 `Import power and configured limit` with no SVG | **RESTORE TO MOCK.** The mock renders `lineChart('ev')`; the rule-5 allowlist is an implementation constraint, not a reason to erase the graphic. | Add `frontend/src/sites/evDepthGraphics.tsx`, `frontend/src/ui/primitives.css` and `tools/checks/shell-overflow.ps1` to E3's Lane A file list. In rule 5 register `evDepthGraphics.tsx` as the sole owner of its `<svg>`, require an actual `.ev-depth-graphic__scroll` wrapper in that module, and verify that selector declares horizontal overflow containment in `primitives.css`, as the existing assessment graphic check does; retain all existing allowlist checks. `EvEnergy.tsx` renders a chart of accepted selected import samples at their UTC timestamps and the time-valid declared limit as a labelled horizontal line only when configured; retain the `Measure / Value` `DataTable` as accessible detail. A lone peak cannot become an invented series: E1b must include the accepted sample timestamps and values in the E3 read on the same snapshot, or E3 shows the empty plot frame and `No accepted site-import samples in this window.` until that wire exists. No interpolated coverage, continuous-limit finding or mock 76/80-kW values. Update `evEnergy.test.tsx::energy_states_table_loading` for real points, null limit, sparse/empty states and no fabricated line; recapture `energy-complete`, `energy-missing-meter`, `energy-pending`, `energy-historical` at 1440/390 with measured caps; run `tools/check-all.ps1` and E3 review. E1b is the in-flight upstream DTO unit affected. |
| E4 condition notice | **KEEP — MOCK DEVIATION (D2).** The mock has no Health notice; selected session/fault rows could otherwise be mistaken for a charger diagnosis. | A table footnote is the closer visual alternative. Keep the exact amber sentence and E4 test/capture because the claim ceiling needs prominence. |

**E1b/E3 chart wire correction.** Add `import_samples` to the exact `energy` key table and to E1b's `evDepth` response validation: an ordered array of `{source_time:string, import_kw:string, evidence_id:string}` from accepted non-`EXCLUDED` `ev_site_import` rows overlapping the requested window, selected on E1b's existing read connection, sorted `(source_time,evidence_id)`. Deduplicate only identical evidence IDs, not equal-time samples. `import_sample_count` equals this array's length. E3 uses only these rows for plotted marks; equal-time points remain separate, and a connecting line is permitted only across consecutive time-ordered accepted samples with established coverage between them. The current source has no such continuous-coverage proof, so E3 draws marks without a connecting path. The limit line is declared configuration, visually distinct from observations. Add this field to E1b's backend focused test and E3's frontend validator/test before declaring the chart complete.

**Correctness disposition.** Confirm E1a cadence-bounded accepted-state conservation, empty `weekly: []` giving zero seconds and null rates, E1b complete versus partial energy and gross-tariff separation, E2 percentage/bound rounding, E3 financial table and no limit-causation inference, E4 unknown physical condition, E5/E6 authored revision/cutoff rules and the A1Q adapter/guard ownership. E2's availability status remains a proxy, never a physical certification. The E3 chart requires the selected sample series correction above; its present peak/count DTO alone cannot render the mock graphic honestly. E2/E3/E4 currentness and E6 pending notices are **KEEP — MOCK DEVIATION (D2)** because the mock has no live pending/stale/historical selection; an inline status note is an alternative, but the amber notice makes the cutoff visible. E6 authored scenario rows depart from illustrative mock values to show stored facts; **KEEP — MOCK DEVIATION (D4)**, with no false observed outcome.

## W5-03a pre-flight rulings (2026-10-23; controlling E1a–E3 cards)

This section folds the 49 P-ID dry-read findings into E1a–E3. It supersedes earlier contradictory sentences in those cards. The builder uses the corrected file lists and literals here, not the former table-only E3 or three-total E2 bars. Every screen departure below has a register row; D3 omissions are restored before merge.

### Gate, ownership and run size (P-G-1–3)

W5-03a may start **after W5-02a core K1a–K1c is independently reviewed and merged with sole Alembic head `0033_w5_cold_work`**. It need not await W5-02 K2a/K2b screen work: W5-03a has no migration and does not consume those screens. W5-03b still requires reviewed W5-03a and the merged exact `0033` head. Serialize shared UI edits: merge W5-02a core (`main.py`, backend composition) first; then W5-03a E1b (`main.py`), E2 (`SiteAnalyticsFrames.tsx`, `operatorSiteRoutes.ts`, `evSiteRoutes.tsx`, navigation guards), E3 (same files and guards); then W5-02 K2a/K2b rebases those shared UI files and keeps both cold and EV route/fixture changes. Do not run simultaneous builders on those files. E3 remains one reviewed unit, but make its page/chart and registry/capture closeout separate builder runs, each one commit and a handoff; E3 review covers both. The quiet-machine full backend suite occurs after E3 on the same revision, after builders, vitest, browser and captures stop.

### E1a literal reader and producer contract (P-E1a-1–11)

`EvReadService` begins at `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py:2640`; use its caller-connection `within` :2994, `open_on` :2998, `foundation_on` :3028, `assets_on` :3044 and `accepted_on` :3050. The :2470/:2517 methods belong to `ColdReadService`. `accepted_on` returns **all** accepted rows in the window at `snap['known']`; E1a first intersects their lowercase `evidence_id` with `set(snap['selected']['evidence_ids'])`. With no selected head, all observed counts/rates are null. No pending-only or post-selection row classifies a second. Keep `use=None` rows: the W2 session-span linker often leaves valid connector-state rows unlinked. Reject `use='EXCLUDED'`, `quality != 'GOOD'`, and `reason='CLOCK_UNATTESTED'`; also reject an observation whose `source_time`, `sent_at` or `received_at` is missing or non-UTC/ambiguous, or whose source-to-receipt ordering violates the W2 accepted clock checks. A late selected GOOD row is usable at its own source time; lateness alone is not a fabricated stale flag. Define **stale** solely as time after its per-connector cadence horizon, not as an unstored row field. A row with no usable attestation is Unknown, never an inferred state. Bind by `asset_id` to the enabled connector's scoped asset UUID and require `connector_id` to match that Foundation component; ambiguous binding stays Unknown.

Use `foundation_on(c,snap)` content and `valid_from`; it has no revision ID or `valid_to`. Add the caller-connection method `foundation_revision_on(c,snap)` in `postgres_assessment_store.py` returning `{id,content,valid_from,valid_to}` using the *same selected-ID/effective-at-cutoff predicate* as `foundation_on`; make `foundation_on` delegate to it so the two cannot disagree. Add that file to E1a/E1b ownership and focused tests. A selected head with zero/multiple `foundation_ids`, a revision absent at the selected ID, or a selected revision whose `[valid_from,valid_to)` does not cover the requested window yields `NOT_ESTABLISHED`, null denominators and null `health.foundation_revision_id`; never fall back to a later effective revision for a selected head. With no selected head, no positive availability. `valid_to=null` means open ended. E1b obtains the exact ID from this new method, not a guessed `sel['foundation_ids'][0]` alone.

Read `content.components`, `ev-connector-enabled` and `content.connector_enable_schedules` via `ev_site_reads.enabled_connectors` and a **new** `connector_service_windows(foundation,assets,lo,hi)` helper in `ev_site_reads.py`. Add `ev_site_reads.py` to E1a's edit list. The helper returns one row per enabled scoped connector with its asset ID and clipped, sorted, unioned `[from,to)` occurrences. It must preserve a declared `weekly: []` as an empty row so E1a can distinguish `DECLARED_EMPTY` from missing schedule; the existing `service_windows` merges connectors, is unclipped and drops empty weeks, so it is unsuitable as the E1a denominator. Reject malformed/overlapping ambiguous declarations rather than invent hours. `ev-status-cadence` is a connector property in **minutes**; parse it as Decimal and multiply by 60 for seconds, without binary-float rounding. Missing/invalid cadence leaves scheduled seconds intact but every affected observed second Unknown, never positive classified time.

Sort state rows by `(source_time,evidence_id)` for deterministic processing. Equal-time equal-value duplicates form one transition; equal-time different values conflict and the entire cadence-sized interval beginning there is Unknown. A later valid transition may resume classification; do not rely on evidence-ID order to choose a winner. Clip each observation at the next transition, its own cadence horizon, the scheduled occurrence and window end. Unscheduled gaps stay outside the denominator. Conservation is asserted at connector and Site levels.

The producer is `class Chain` in `backend/tests/test_w205b_ev_replay_postgres.py:214`, `decision_clock()` :235, `advance_late()` :367, fixture `chain(case)` :418, `CASES` :100, vectors `backend/tests/fixtures/w2/ev-w206-vectors.json`; no `EvReplayBuilder` exists. New `ev_depth_cases.py` may wrap `Chain` and its public fixture methods, without importing private simulator truth into a product read. Use `complete` for observed and historical; `late-record` plus `advance_late()` for pending; `missing-meter` for partial energy; `fault`/`interrupted` for faulted status. Existing vectors already contain UNPLUGGED/FAULTED states. For the status-gap case, remove/omit consecutive accepted state source events **before publication**, creating a gap longer than cadence, then rerun assessment at the returned decision clock; assert that the selected `evidence_ids` includes only the remaining events. For `weekly: []`, publish a test-scoped time-valid Foundation revision as in `test_w501_cold_depth_postgres.py`, run a *new* assessment selecting that revision, then assert its single `foundation_id` and zero schedule seconds. A pre-assessment Foundation insert alone does not select it. Capture historical at the saved first 09:00 watermark and current after the 09:05 replay.

### E1b literal snapshot, energy and Health contract (P-E1b-1–8)

`ev_gate(...).opened(request,site_code,keys)` authenticates/parses/resolves and returns `(tenant_id,site_id,{lo,hi,known_at})`; it opens **no** transaction. In `ev_depth_api.py` call it, then `EvDepthReadService` runs `reads.within(lambda c: ...)` once and `reads.open_on(c,t,s,code,lo,hi,known_at)` once. Reuse the resulting `snap,body` and one `EvSiteReads` money selector on `c`; do not call the private `_ctx` outside `EvSiteReads`. Expose a public `context_on(c,...)` forwarding to `_ctx` in `ev_site_reads.py` and a public `energy_on(ctx)` extracted from `overview`'s existing inline energy/site-power block. `overview` calls that same helper; E1b projects only the named depth keys, dropping overview-only `supported_kwh`, `as_of`, `coverage`, `claim_limit`. This preserves W2-07 semantics and one transaction.

The `energy.import_samples` array contains selected accepted non-EXCLUDED GOOD `ev_site_import` `INTERVAL_MEAN` records whose interval overlaps `[lo,hi)`, with `{source_time,import_kw,evidence_id}`. Require `evidence_id` in the selected set. `source_time` is the sample's interval-end timestamp and is the plotted x coordinate; `import_kw` is the stored kW decimal value verbatim after validating `unit='kW'`, finite and nonnegative. Sort `(source_time,evidence_id)`; deduplicate identical evidence IDs only. `peak_sample_at` and `observed_peak_import_kw` use the same maximum sample, ties earliest `(source_time,evidence_id)`; `import_sample_count` equals the array length. `peak_below_limit` compares only that selected peak with the time-valid declared limit. W2 overview `_site_import` keeps its existing broader coverage/peak rule for W2 compatibility; do not substitute its peak into the W5 depth DTO. E1b backend tests assert the array and a higher unselected or otherwise unusable row that changes the overview peak but not the depth peak, peak time or below-limit answer, including `PENDING_RECOMPUTE`. E2 creates and validates `evDepthClient.ts`, including this field; E3 tests the rendered chart. The source-provenance field is `body['selected_source_provenance']` while pending (and the selected block on other states), never `body['source_provenance']` when that alias points at pending. Remove the unused W5-03a `EvReadService.selected_provenance_on` method: E1a–E3 expose no depth-specific citation-provenance DTO field. Preserve `selection.source_provenance` and test it on Energy and Health while pending. E5 must add and test a caller-connection provenance method when its authored-basis field is built; it must normalize selected and cited IDs to lowercase and intersect them before `cited_set`.

For Health, `kind='CONNECTOR'` only for `EV_CONNECTOR`; `kind='SITE_METER'` only for a `METER` component whose topology node has role `METERING` and is fed directly by a `BUS` node. A connector-level meter must not be called a Site meter. The fixture's `METER` is the Site import meter; `AC_BUS` and `EV_CHARGER` are neither row. An unresolved meter role remains an honest `UNKNOWN` kind/observation, with a test, rather than a fabricated Site role.

### E2 route, bars, copy and files (P-E2-1–14)

E2 adds `frontend/src/shell/evSiteRoutes.tsx`, `frontend/src/sites/__tests__/evAssessmentRoutes.test.tsx`, `frontend/src/test/settled.ts`, `frontend/src/ui/DataTable.tsx` and `frontend/src/ui/primitives.css` to its file list. E3 retains route/guard ownership and adds its own `evAssessmentRoutes.test.tsx` and `settled.ts` edits. `evSiteRoutes.tsx` owns EV depth route keys and URL preservation; `operatorSiteRoutes.ts` exposes the Site path; `SiteAnalyticsFrames.tsx` chooses availability/energy via a typed `view` prop to `EvSessionsFrame`, which sets `aria-current` only on the selected subtab. `EvSiteViews.tsx` changes the mock Overview Availability and Site power card actions to the new routes, preserving `from,to,known_at`; the Availability value remains `Not assessed` until the depth result is actually selected. Promote the Sessions `Energy summary →` and Readiness `Review availability →` links when their destinations are proved; no dead links. Update `evAssessmentRoutes.test.tsx` unavailable count/tuple and live href/selection assertions. Extend the settled-screen LOADING regex for the two new loading sentences and add a focused assertion. `DataTable` gains an opt-in `stickyFirstColumn` prop and scoped CSS on its scroll region/first `th` and `td`; only tables that need it set the prop. Test keyboard scroll and that the first column remains visible at 390.

Restore the mock's `availability` and `energy` heading as the Site's imported name, breadcrumb `Sites › {Site} › Performance` (Performance links to the live Performance landing), and subtitles from `SITE_SCREEN_DESCRIPTIONS`: `Performance · connector availability and unknown time` and `Performance · charging energy and site-power context`. Remove the contradictory ledger headings/subtitles. The mock's status muted text is derived as `{connector_count} connectors × {scheduled_duration} scheduled hours = {total connector-hours} connector-hours` only when all enabled connectors share the same schedule; otherwise say `{scheduled_total} scheduled connector-hours across {connector_count} connectors`; absent schedule uses `Scheduled connector-hours unknown`. Maintain mock status/bar/panel order. For E2, restore card notes `State-supported service time`, `Faulted or unavailable state evidenced`, `No trustworthy state coverage`, `14 / 15 known hours; coverage 93.75%` as dynamic numerators/denominators without fixed numbers. The known-time value rounds one decimal as before; the note's coverage uses two decimals from the exact ratio. The bound value uses two decimals (`87.50–93.75%` when appropriate) to preserve the mock's `93.75`; its prose uses the mock structure with dynamic values: `Lower bound: {available} / {scheduled}. Upper bound: ({available} + {unknown} unknown) / {scheduled}. Unknown time is not silently included as available.` Restore next-evidence prose structure with the actual unknown duration and the mock sentence `A telemetry outage does not prove the charging connector was physically unavailable.` Restore `Inspect connector-state lineage ↗` in its mock position. The chart-note remains under the bars: `Connector {label}: {available} available, {unavailable} observed unavailable and {unknown} unknown. Spans use accepted transition timestamps.` Use an honest no-data sentence when no selected connector exists. These variable substitutions are **MOCK DEVIATION (D4)**, register R26/R43–R45.

E2 track spans the requested window. Render a segment for each ordered classified span, not category totals; blank intervals outside each connector's configured schedule have `aria-label='Outside scheduled service hours'` and no category color. Derive start/mid/end labels in `HH:mm UTC`; legend uses the mock's green/red/outline badges; CSS tokens use mock green `#8bc5b3`, red `#df9b94`, unknown `#cdd5e1`. Right text is the connector's configured local service period if exactly one occurrence (`HH:mm–HH:mm`); otherwise the selected UTC window range. Add a screen-reader span summary for all three totals. Update navigation guards: remove exactly one EV unavailable `Availability` in E2 and `Energy / site power` in E3 from `$expectedTabs`; add live-page assertions analogous to the cold block at `navigation-truthfulness.ps1:838–844`; replace `navigation-rail-fixtures.ps1:198–208` anchors on `<UnavailableTab ...>` with live `href`/selected-state fixtures, retaining cold fixtures. The E2/E3 unit tests assert both positive route and former inert tab absent.

### E3 chart, copy, files and close (P-E3-1–13)

E3 adds `frontend/src/sites/evDepthGraphics.tsx`, `frontend/src/ui/primitives.css`, `frontend/src/ui/DataTable.tsx`, `frontend/src/sites/__tests__/evAssessmentRoutes.test.tsx`, `frontend/src/test/settled.ts` and `tools/checks/shell-overflow.ps1` to its file list. The existing `EvPowerChart` in `assessmentGraphics.tsx:993` reads analysis intervals and connector energy, so it cannot render the selected depth DTO without conflating two read models; leave it for Overview. Register the new graphics module in rule 5. Mirror the cold graphic registration: add module/selector variables beside lines 77–78, verify `.ev-depth-graphic__scroll` has `overflow-x:auto` in `primitives.css` beside lines 317–331, count a real wrapper and SVG in the region scan beside lines 368–403, and fail on zero wrapper or zero SVG beside lines 477–488. Keep every existing registered module and rejection test. The four manual non-vacuity mutations and clean reverts recorded in the phase handoff satisfy the guard-fixture requirement for W5-03a; no committed mutation fixture is needed. `EvEnergy.tsx` calls the graphics component and contains no `<svg>`.

`EvDepthPowerChart` uses `viewBox='0 0 640 220'`, responsive width 100%, height at most 220px, a horizontally contained `.ev-depth-graphic__scroll` wrapper and `role='img' aria-label='Site import and power limit'`. Plot area left 48, right 12, top 12, bottom 32. X ticks are seven equally spaced UTC instants from window start to end, labelled `HH:mm`; ticks are derived, never fixed 08:00–16:00. Y maximum is `max(100, ceil(max(sample kW, limit kW)/25)*25)`; draw five evenly spaced ticks 0, 25, 50, 75, 100 when max=100, or 0/25/50/75/100% of a larger max as bare numeric tick labels, with one `kW` unit label above the Y axis as in the mock. Draw accepted import samples as 5px circles at `source_time`, one per ID; equal-time samples remain separate marks. Draw no connecting path. Draw a dashed horizontal configured-limit line (`stroke-dasharray='6 4'`) only when the time-valid limit is non-null, with end label `{limit_kw} kW limit`. Legend labels `Site import` and `Site power limit` remain in that order below the SVG even when the limit is absent; absent limit has no line and a muted legend swatch. Empty samples retain axes and show `No accepted site-import samples in this window.` in the plot area; a plot-frame rectangle appears only in this empty state. The mock's `Observed import is not proof of vehicle-requested power` is the `Import power and configured limit` Panel description directly under the heading, not a chart note below the figure (`index.html:183,595`). The `Measure`/`Value` DataTable follows in a disclosure below the chart, within the same 440/430px panel cap: **MOCK DEVIATION (D2)** R46, because accessible exact sample facts are additionally exposed; an always-open table was considered and would exceed the measured mobile cap. Tests assert 0/1/many marks, equal-time marks, no path, seven X ticks, Y scale, dashed/no limit, accessible empty state, description position, width/height and planted-graphic guard failures.

Restore mock energy status text `Complete session meter records · incomplete session energy excluded` only when the selected records support it; otherwise `Complete session meter records not established · incomplete session energy kept separate` (**MOCK DEVIATION (D4)** R47). Keep `Inspect meter basis ↗` in the status line and preserve the selected Evidence Analysis query. Restore the four card notes to the mock's forms, substituting the selected facts: `Includes {aborted_kwh} kWh from aborted session` when that selected value is established, else `Complete metered sessions only`; `Selected {window_duration} window`; `Time-valid configuration`; `Scenario tariff: {tariff}/kWh` when eligible, else `Scenario tariff not established`. Fallback card notes are **MOCK DEVIATION (D4)** R48. The separate partial/unknown disclosures are **MOCK DEVIATION (D2)** R49. The `Energy basis: limited` badge is **MOCK DEVIATION (D4)** R50 when measured basis is unsupported. Restore `What can be concluded` as a heading-less key-value list, with green `Yes` and amber `Not established` badges; `Stationary battery` shows `Unknown` with the existing Foundation limitation because `Not configured` is unproved (**MOCK DEVIATION (D1)** R51). Put the mock conclusion chart-note below that list: `Revenue is an estimate from metered kWh and the declared tariff, not payment evidence.` only for an eligible estimate; otherwise `No eligible revenue estimate is established; no payment evidence is connected` (**MOCK DEVIATION (D4)** R52).

Keep the bridge's mock columns and row order. Row 1 uses selected complete kWh and eligible tariff/amount; null consequence becomes an honest unpriced gap (**MOCK DEVIATION (D4)** R53). Row 2 keeps mock `Incomplete session` and `Unavailable` unless selected partial kWh can be shown, in which case show `{partial_kwh} kWh incomplete-session delivery` and `Not priced` (**MOCK DEVIATION (D4)** R54). Row 3 keeps exact mock `No demand/sales baseline`. R06 covers the unconnected sample marks; R55 covers all energy example numbers and chart axis values replaced by selected data. Keep selected `Energy basis: limited` and existing disclosure only in the cases named above, never on complete evidence.

E3 captures use the `chain(case)` fixture (or the E1a wrapper with the same `Chain(case,tmp_path / case).open()` construction) for `complete`, `missing-meter` and `late-record`; historical is the saved 09:00 cutoff of the complete run. The registry must add all six panel rows and both implementation nodes together, with ledger `coverage='partial'`, `task='W5-03a'`, `proposed_fidelity_tier='Real with honest gaps'`, and matching `registry_dependencies`; no `gap` row becomes `built` before review. `check_v69_dependency_registry.cjs` is under `frontend/docs/architecture/`, and is run in E3 closeout. E3 also owns the six matching `v69-panel-contracts.json` tier changes and the ledger `to_candidate:null` for `availability` and `energy`: the tier/coverage validators require them. Replace stale deferred-gap fields in those six contracts as specified in the W5-03a review rulings below, and set `promotion_dependencies.to_real.unresolved_panels: []` on both screen-ledger rows after the six panel mappings are present; `tier_approval` remains `pending owner review`. The scoped regression includes all changed package tests, importers of shared modules, full frontend vitest and `tools/check-all.ps1`; the full real-Postgres backend suite is required because E1b edits `main.py`/composition and E3 edits a guard. Run it once on a quiet machine before merge.

### W5-03a review correction (2026-10-23; controls the E1a–E3 fix round)

The numbered Architect rulings are in `.agent/W5-03a-review-rulings.md`; this paragraph and table amend the earlier cards and pre-flight text where they conflict. H1 uses `v69-chart-note` for the connector and conclusion notes; the import sentence moves to `Panel.description`. H2 uses `v69-panel-value` for the full-schedule bound. H3 moves the import legend below the SVG/scroll wrapper. M3 renders energy card number and `<small>kWh</small>` or `<small>kW</small>` separately, as the mock does (`index.html:594`). These are fidelity corrections, not mock departures.

| Review M2 item | Exact copy, tone and placement for the fix round |
| --- | --- |
| Energy limit card fallback | `No time-valid site limit declared`, muted card note under `Declared site limit`; keep `Time-valid configuration` only with a selected limit. This is the honest R48 D4 fallback to mock `index.html:594`. |
| Energy peak window note | `Selected {H}-hour window`, muted note under `Observed peak import`; `H` is exact selected duration in hours with up to two decimals, without trailing zeroes. Remove `No selected window`: the paired window is required; a missing window is a refused/malformed read, never a card fallback. Mock `Selected 8-hour window`, `index.html:594`; R48 D4. |
| Import detail disclosure | Summary `Measure and value detail` below the graphic; hidden table heading `Import measures`. Neutral technical disclosure, R46 D2. The table header is `Measure` / `Value`, mock `index.html:595` has the chart only. |
| Import detail rows | In this order: `Accepted import samples`; `Observed peak import (sample peak)`; `Peak sample time (UTC)`; `Declared site limit`; then `Sample {HH:mm:ss UTC}` for each accepted sample. All are neutral table row labels inside the disclosure; counts and values come from the selected DTO. R46 D2. |
| Conclusion `No` | Red `No` badge for an observed sample peak at or above the declared limit; green `Yes` strictly below; amber `Not established` only for causation; neutral `Unknown` if peak or limit is missing. Key-value position follows mock `index.html:595`. `No` is not an interruption-causation claim. The example's green `Yes` is **MOCK DEVIATION (D4)** R87 when selected facts change it. |
| Complete-energy empty sentence | `No complete metered delivery is established for this window.` as a neutral empty notice after the coverage disclosures and before the two panels; do not replace either mock panel. The literal is in the shared empty ledger. |
| Energy accessible group names | `Charging energy` on the status bar and metric-card group, screen-reader label only. These group the mock status/cards at `index.html:594`. |
| Limit line end label | `{limit_kw} kW limit`, muted at the right end of the dashed limit line when a time-valid limit exists. No label or line when absent. |
| Y-axis units | Bare numeric labels at all five Y ticks; one `kW` label above the Y axis, matching mock `lineChart`, `index.html:228-233`. |
| Sample mark title | `Site import {import_kw} kW · {HH:mm:ss} UTC`, one SVG `<title>` per selected mark; accessible detail, not printed chart prose. |
| Legend without limit | Keep both mock labels `Site import` and `Site power limit` below the chart in that order (`lineChart`, `index.html:233`). When the declared limit is null, show the latter with a muted swatch and no line; selected limit card supplies the gap explanation. |
| Plot frame | No rectangle with plotted samples, as in the mock. An empty frame and `No accepted site-import samples in this window.` appear only with zero marks. |
| Availability missing coverage | `Known hours and coverage unknown` in the Known-time availability card note when denominator inputs are null. With declared zero service hours, show `0 / 0 known hours; coverage not applicable` there; never a numeric percentage. Mock dynamic note `index.html:588`; R44 D4. |
| Availability hours | Up to two decimal hours with trailing zeroes removed for the status, card notes, chart notes, bound prose and next-evidence missing duration. Use decimal hours, not `durationText`, in those three prose fields. Chart notes use `{H} h`; bound prose uses hour numbers in the mock form `Lower bound: {available} / {scheduled} hours. Upper bound: ({available} + {unknown} unknown) / {scheduled}. Unknown time is not silently included as available.` Preserve exact seconds in the DTO and calculate percentages and bounds from exact seconds. Mock chart/bound copy `index.html:588-590`; R43–R45 D4. |
| Availability next evidence | With unknown scheduled time: `Recover the connector status/heartbeat history for the missing {H} hour(s). A telemetry outage does not prove the charging connector was physically unavailable.` Here `{H}` is the displayed decimal-hour number, `hour` is singular only when that number is exactly 1, and `hours` is used otherwise. With a SCHEDULED window and zero unknown seconds: show only `A telemetry outage does not prove the charging connector was physically unavailable.` With zero declared service hours: `Declare service hours before assessing connector availability. A telemetry outage does not prove the charging connector was physically unavailable.` With absent schedule: `Establish the connector service schedule before assessing availability. A telemetry outage does not prove the charging connector was physically unavailable.` Use neutral prose in `Most useful next evidence`, ahead of the lineage link, as mock `index.html:590`; R45 D4. Do not print `any unknown scheduled time` when none is scheduled. |
| Availability unbounded panel | Value `Unknown` in panel-value typography. Prose `Lower bound: Unknown. Upper bound: Unknown. Unknown time is not silently included as available.` in the same panel position as mock `index.html:590`; no invented denominator. |
| No connector | `No selected connector has a service schedule in this window.` as a muted chart note after the legend/time axis inside `Connector states over the service schedule`, only when the selected connector list is empty. This is the honest R45 D4 no-data form. |
| Connector label | Use the selected Foundation label verbatim; prepend `Connector ` only if it is not already the first word (case insensitive). This prevents `Connector Connector 1`; chart note and left bar label use the same displayed name. Mock `Connector 1/2`, `index.html:588`. |
| Right-hand service period | For exactly one scheduled occurrence, show its `HH:mm–HH:mm UTC` interval; for multiple occurrences show selected window `HH:mm–HH:mm UTC`. The DTO has UTC instants and no Site-local offset. This is **MOCK DEVIATION (D1)** R86 from mock local `08:00–16:00` at `index.html:588`; do not imply local time. |
| Time-axis placement | Start/mid/end UTC labels span the entire bar row, under the tracks, matching mock `segment-times` at `index.html:588`; keep selected-time labels. R26 D4 covers changed values. |
| Availability accessible group names | `Connector availability` on the status bar and metric-card group, screen-reader label only. These group the mock status/cards at `index.html:588`. |

For E1a, a selected state row with null `connector_id` binds through its scoped `asset_id` to the enabled Foundation component; a non-null mismatched ID is unusable. Every selected transition timestamp, including an unusable row, ends the preceding observation's hold; the unusable interval is Unknown until a later valid transition. For E1b Health, `SITE_METER` requires a `METER` component at a `METERING` topology node fed directly by a `BUS` node. Test null binding, a mismatched/unusable transition after a known span, and a connector-level meter respectively. The manual four rule-5 non-vacuity probes in the phase handoff are accepted in place of committed mutation fixtures; retain the recorded failure outputs and clean baseline.

### Pre-flight closure map

| IDs | Closed by | Residual |
| --- | --- | --- |
| P-G-1, P-G-2, P-G-3 | Gate/ownership/run-size paragraph above; W5-03 task gate | W5-02a core merge and reviews are execution gates |
| P-E1a-1, P-E1a-2, P-E1a-3, P-E1a-4, P-E1a-5, P-E1a-6, P-E1a-7, P-E1a-8, P-E1a-9, P-E1a-10, P-E1a-11 | E1a literal reader and producer contract above | Implementation and focused review |
| P-E1b-1, P-E1b-2, P-E1b-3, P-E1b-4, P-E1b-5, P-E1b-6, P-E1b-7, P-E1b-8 | E1b snapshot, energy and Health contract above | Implementation and focused review |
| P-E2-1, P-E2-2, P-E2-3, P-E2-4, P-E2-5, P-E2-6, P-E2-7, P-E2-8, P-E2-9, P-E2-10, P-E2-11, P-E2-12, P-E2-13, P-E2-14 | E2 route, bars, copy and files above; register R26/R43–R45 | Captures and owner departure walkthrough |
| P-E3-1, P-E3-2, P-E3-3, P-E3-4, P-E3-5, P-E3-6, P-E3-7, P-E3-8, P-E3-9, P-E3-10, P-E3-11, P-E3-12, P-E3-13 | E3 chart, copy, files and close above; register R06/R46–R55 | Captures, quiet suite, independent review and owner departure walkthrough |

## W5-03b pre-flight rulings (2026-10-23; controlling E4–E6 cards)

These rulings replace conflicting E4–E6 sentences above. Builders use the current unit card plus this section; the earlier S7 panel, 1900/2350 Health cap, literal 09:00/09:05 cutoff, and E6 `Scenarios` h1 instructions are withdrawn.

### Gate and item 34

- **P-G-1.** E4–E6 start from main only after independently reviewed W5-02a core K1a–K1c (`0033_w5_cold_work`, sole head) and W5-03a E1a–E3 merge. E5 cannot start against the W5-02a branch alone: its E1b mount, selected ID read and `foundation_revision_on` are predecessors; E5 owns the new provenance method for its authored-basis field. `0034_w5_ev_scenarios.down_revision` is exactly `0033_w5_cold_work`.
- **P-G-2.** Serialize the shared Site files in this order: W5-03a E2/E3, then rebased W5-02 K2a/K2b, then rebased W5-03b E4/E6. E5's backend work may proceed after the two predecessor merges; its `main.py` edit follows the E1b mount. Resolve overlapping nav guards and tests on the rebased W5-03b branch.
- **P-G-3.** Before the one full backend suite, use the lesson-14 field-2 `eol=lf`/`w/crlf` check and re-checkout any listed LF-pinned fixture. After captures stop only PIDs the unit started, drop private `assetops_w503cap_test`, and keep `frontend/tsconfig.tsbuildinfo` untracked. These are execution checks, not new files.

**K2 review lane override (Codex Architect, 2026-10-23; supersedes P-G-2 and any earlier E4/E5/E6 start-order sentence):** current main `b21478e0` has the reviewed `0033_w5_cold_work` sole head and W5-03a E1a-E3, including the E1b mount, selected ID read and `foundation_revision_on`. Lane 2 may branch from current main now for **E5 backend only**: `0034_w5_ev_scenarios` with parent exactly `0033`, EV scenario rules/store/service/API, caller-connection EV basis/provenance/money reads, `main.py` mount after E1b, rule-8 guards/probes, sole-head assertion updates and backend tests. It may complete independent backend review and merge before K2/K3. Recheck sole head on rebase. Shared Site files serialize W5-03a E2/E3, then W5-02 K2a/K2b, then K3a/K3b, then W5-03b E4 Health UI and E6 Scenarios UI. E4/E6 routes, nav, registry, captures and every frontend file wait for reviewed K2 and K3 merges; E6 also waits for reviewed E5. The early E5 branch owns no frontend file. W5-04 V1a's generated producer remains later work.
- **P-34-1.** W5-03b builds no generated EV producer. Its fixed E1 regression vector is enough for E4–E6. W5-04 V1a owns `tools/w504_ev_work_cases.py` and the generated, test-only shifted source/Foundation producer. Item 34's production path closes only after V1a verifies it.
- **P-34-2.** Every E5 selection and authored-basis cutoff comes from the selected snapshot's returned `known`/`committed_watermark`; 09:00/09:05 are fixture examples, never source literals or a generic selector limit. The same code accepts a shifted fixture's returned cutoff.
- **P-34-3.** E5 tests 422 `EV_TIME_INVALID` for `known_at` later than that fixture's committed watermark, and a read at the returned watermark that preserves selected session IDs. W5-04 V1a separately proves its wall-clock K2 mapping to the last returned watermark no later than K2. Never pass K2 itself as a W5-03 evidence cutoff when beyond the watermark.

### E4 consolidated correction

- **P-E4-1/2/9.** Remove the extra EV Health S7 Data sources panel as D3, the same correction as cold R22. Do not edit `SiteHealth.tsx` or `frontend/src/test/panelStructure.ts`; `expectV69Panels("ev-health")` must see exactly the mock's sole `Condition and evidence` panel. Put R16 notice after that panel, not between two panels. E4's actual file list is the first E4 paragraph above; it excludes `SiteHealth.tsx` and the panel helper. Change both Foundation slots from unavailable Health links to `Evidence › Data sources →`, destination `siteEvidenceHref(site_code)` with valid existing window query when present, then `#ev-site-sources-heading` (existing `EvSiteViews.tsx` panel). Do not propagate `gateway`.
- **P-E4-3/10.** The currentness R15 notice goes above the cards; the R16 condition notice goes directly below the table. The h1 remains the Site name (`Depot Charging Hub` in the mock); `Health` is the breadcrumb/tab.
- **P-E4-4.** A bare EV Health route with no paired `from,to` shows the typed `EV_WINDOW_INVALID` 422 refusal in the mock's Health structure. Never silently default a period. `ev-health-unknown` uses a valid paired window with no selected assessment; it is not the bare-route case.
- **P-E4-5/6.** `SiteHealthFrame` gains `evDepth?: EvDepthClient`; `App.tsx` injects the E2 client as `evDepth`, with EV_CHARGING branch before the S7 fallback. The Foundation link test expects two live destinations, not two unavailable entries; window query is carried only if valid and paired. The href points at Evidence, so neither source-panel extraction nor Health fragment is needed.
- **P-E4-7.** Preserve the three mock card positions, labels and tones: Connector 1 `Unknown` gray; Connector 2 `Needs attention` amber on selected fault-stop, otherwise `Unknown` gray; Stationary battery `Not applicable` neutral when Foundation states none installed, otherwise `Unknown` with an honest configuration gap (R56 D4). Use `Operating normally; no condition assessment` only if selected source supports the first clause; otherwise `No charger condition assessment` (R57 D4). Fault card note is `One fault-stopped session; cause not diagnosed` when exactly one selected fault-stop, otherwise a selected count and the same no-diagnosis ending (R57 D4). Battery note is `None installed` only with selected Foundation support. Connector cards retain separate `Sessions →` links, carrying paired read window; no fake session-detail route. The DTO remains the source of selected state; map it to these display literals without claiming healthy hardware.
- **P-E4-8/12.** Preserve table order and headings. Fault connector row shows selected Foundation label plus ID; assessment `Session interruption; hardware fault not established`; next evidence `Diagnostic event + witnessed session`. Site meter row shows its selected label plus ID; assessment `Power limit respected in observed samples` only if selected accepted samples and declared limit prove every shown sample within it, otherwise `Power limit not assessed from selected samples` (R59 D4); next evidence `Continuous coverage for interval-wide claims`. A selected non-fault connector gets a third row with `No connector condition assessment` / `Diagnostic event + witnessed session` (R58 D2). A `METER` with `kind:UNKNOWN` has no claim row or card: it cannot be called a Site meter. The three-row/worst-case 36-character ID cap applies when the optional connector row is present. Fix old prose: the optional connector is the addition; the Site meter is in the mock.
- **P-E4-11.** The executable registry JSON governs: `(ev-health,1)` requires `D-ev-domain,I-W5-ev-depth-read,I-W5-ev-health-ui`; serialize in the file's compact one-line style. E3 must have supplied `I-W5-ev-depth-read` before E4.

### E5 consolidated correction

- **P-E5-1.** Add the 18 sole-head-pinning files to E5's Lane A file list: `backend/tests/mini_depth_probe.py`, `test_s1_bindings_postgres.py`, `test_s2_evidence_ledger_postgres.py`, `test_s405_publication_postgres.py`, `test_s4_consequence_store_postgres.py`, `test_s4_evidence_consequence_work_postgres.py`, `test_w200_source_events_postgres.py`, `test_w201_cold_foundation_postgres.py`, `test_w203_cold_migration_postgres.py`, `test_w204_cold_migration.py`, `test_w205a_ev_migration.py`, `test_w206_ev_migration_postgres.py`, `test_w207_ev_money_postgres.py`, `test_w401_migration_postgres.py`, `test_w402_migration_postgres.py`, `test_w403_migration_postgres.py`, `test_w501_cold_scenarios_postgres.py`, `test_w502_domain_intent_postgres.py` (all under `backend/tests/` except the first). Update only assertions for sole current head from 0033 to 0034; downgrade-chain targets remain 0033.
- **P-E5-2.** Reuse `EvSiteReads` money selection on the E5 write connection, through a public caller-connection method on `backend/assetops_backend/ev_site_reads.py` (add this file to E5 ownership). That method returns selected consequence and cited tariff ID using the existing `_select`/`_select_as_of` and `_consequence` policy: window and derived basis match, as-of head recorded by cutoff, `HISTORICAL_CURRENT_CLAIM` labelled history, `WITHHELD` has null revision. Persist IDs only when the returned consequence is an eligible current priced row (`revision_id` non-null, no guard, amount and tariff revision present); historical or withheld yields null IDs. `EvScenarioService` takes this reader alongside `ev_reads`; the store does not duplicate the W2-07 eligibility SQL or import `financials`.
- **P-E5-3/4.** `selection.accepted_evidence_ids` reports the selected read's complete cited accepted set (`ev_session_evidence` union `ev_meter_interval`). `authored_basis.accepted_evidence_ids` is only the accepted meter interval evidence cited by the selected complete session revisions, sorted/deduplicated. E5 adds a caller-connection `selected_provenance_on(c,snap,ids)` method and computes `authored_basis.source_provenance` inside the same write snapshot with that method. It lowercases selected and cited IDs before intersection and tests mixed-case, empty, foreign and mixed-class sets; never accept a body value or copy the open response's broader provenance. Pending or unknown selections cannot be authored.
- **P-E5-5/6.** POST/correction requires `selection.state == CURRENT`, a selected assessment and at least one complete metered session; `PENDING_RECOMPUTE`, `STALE_SOURCE`, `HISTORICAL` and `UNKNOWN` return 422 `EV_SCENARIO_INVALID`. GET continues to show an earlier authored row under pending/historical selection. Add a public `EvReadService.scenario_basis_on(c,...)` caller-connection method in `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py` (E5 file ownership), composing `_snapshot`, `sessions_on`, `accepted_on`, `foundation_revision_on` and provenance on the store's repeatable-read write connection. `PostgresEvScenarioStore.reading` wraps that whole selection and append; map serialization conflicts to 503 per the existing C4 pattern.
- **P-E5-7/8.** Before E5's first schema commit, run the E1 persisted `Chain` producer and assert at least one selected `energy_complete` revision. If it yields zero, amend that test-only input through ordinary W2 ingestion until it yields a real complete meter interval; never seed a scenario row or bypass `energy_complete`. Use C4's principal grant as `authorization_basis` and actor attestation verbatim from authenticated command context; no new literals.
- **P-E5-9/10.** Insert each rule-8 writer/probe block after its C4 peer in `configuration-persistence.ps1` (declaration 824–830, writer list 838, resets 890/893, forbidden DML 951, INSERT-only 1109–1122, unseen 1350, self-test 1527) and `writer_guard_probes.py` (doc 49, constant 79, probes 801–825, controls 928). No `$pgReaders` addition. Prove each probe non-vacuous by mutating a representative forbidden write and observing guard failure. In `main.py`, place the E5 mount after the merged E1b EV depth mount, not after the cold scenario mount.

### E6 consolidated correction

- **P-E6-1/2.** Add `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx` to E6 ownership; replace unavailable Scenarios assertions at 466, 524, 561 and 803–811 with live route/link and zero unavailable-slot assertions. At `navigation-rail-fixtures.ps1:204`, mutate the live `Scenarios` subtab tuple to absent (not `<UnavailableTab>`), and assert the inventory guard rejects it. Remove one EV `Scenarios` from `$expectedTabs` and update the stale comment at `navigation-truthfulness.ps1:748`; add a live branch assertion matching the cold pattern at 848–863.
- **P-E6-3/4/5.** Add `SITE_EV_SCENARIOS_ROUTE_PATH` and `SITE_EV_SUFFIX.scenarios = "/financials/scenarios"` in `operatorSiteRoutes.ts`, plus `[SITE_EV_SCENARIOS_ROUTE_PATH,"scenarios"]` in `App.tsx`. `App.tsx` injects `evScenarios?: EvScenariosClient` into `SiteEvFrame`/`EvSiteFrame`; the `EvSiteFrame` scenarios branch renders `EvScenarios` and skips the unrelated `EvSiteClient` read. Parse `scenario_at` from the URL separately from `EvWindowQuery`; only the Scenarios subtab carries it. Overview/Assumptions retain `from,to,known_at` and drop `scenario_at`; the `financial` group includes `view === "scenarios"`.
- **P-E6-6/9/10.** Remove `SiteAnalyticsFrames.tsx` and `evDepthClient.ts` from E6's edit list: no changes are required. Build `EvScenarios.tsx` with the same panel/table/expansion primitives as cold; do not extract a shared component or edit `ColdScenarios.tsx` during E6. Import shared window types without editing the source module.
- **P-E6-7.** Restore mock h1 = selected Site name, subtitle `Financials · scenarios (placeholder)`, panel meta `Placeholder · to be designed with the owner` with its icon, exact empty title and paragraph (`A scenario compares a declared what-if with the measured case, for example a different stop setting, stock value or tariff. None has been defined for this site.`), and blue closing notice. Use the current Site-page description override scoped to this EV screen; do not change the shared `SITE_SCREEN_DESCRIPTIONS.scenarios`. A populated authored table replaces the empty illustration only when persisted items exist (R27 corrected to D2); place pending/historical notice above the mock panel (R15 D2). Keep the mock `Financial scenarios` panel title and Site-name header. Do not use the old E6 new empty body or `Scenarios` h1.
- **P-E6-8/11.** There is no named observed-outcome implementation node: add none and make no unresolved node reference. `(ev-scenarios,1)` JSON requires `D-ev-domain,I-W5-ev-scenario-read,I-W5-ev-scenario-ui`; compact one-line file format governs.

### W5-03b pre-flight closure map

| P-ID | Closing artifact | Proof still required |
| --- | --- | --- |
| P-G-1, P-G-2, P-G-3 | Gate and item 34 above | Predecessor merges, clean suite/process handoff |
| P-34-1, P-34-2, P-34-3 | Gate and item 34 above; W5-04 V1a | E5 focused clock test; V1a generated producer |
| P-E4-1, P-E4-2, P-E4-3, P-E4-4, P-E4-5, P-E4-6 | E4 consolidated correction | E4 route, panel and links tests |
| P-E4-7, P-E4-8, P-E4-9, P-E4-10, P-E4-11, P-E4-12 | E4 consolidated correction; register R56–R59 and R22 precedent | E4 worst-case captures and mock panel assertion |
| P-E5-1, P-E5-2, P-E5-3, P-E5-4, P-E5-5 | E5 consolidated correction | Head-pin, selection, money and refusal tests |
| P-E5-6, P-E5-7, P-E5-8, P-E5-9, P-E5-10 | E5 consolidated correction | Write-snapshot producer and non-vacuous guard tests |
| P-E6-1, P-E6-2, P-E6-3, P-E6-4, P-E6-5, P-E6-6 | E6 consolidated correction | Route/nav/fixture and query tests |
| P-E6-7, P-E6-8, P-E6-9, P-E6-10, P-E6-11 | E6 consolidated correction; corrected R27 | Mock copy, populated/empty captures, registry check |
