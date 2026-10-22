# W5-01 cold depth — build contract

Architect/Planner, 2026-10-22. Packet: [`tasks/W5-01-cold-depth.md`](../tasks/W5-01-cold-depth.md). Authority: `.ai/ROLE_CONFIG.md` readiness gate and all 13 W3/W4 lessons, `.agent/post-W2-sequence.md` W5-01, v6.9 `cooling`, `cold-health`, `cold-scenarios`, merged W2-03/04 selected reads and W4-01 frozen case model. Cards C1–C5 are complete builder instructions. Each card needs this shared section, its own card and at most two linked existing code sections.

Each card is one builder run and one to three commits. Its final commit includes its tests and, for page cards, the named 1440/390 captures; the builder then hands off for the stated review before dependent work.

## Gate, merge and immutable boundaries

**W2 gate satisfied:** W2-F merged as `2df2a3da`; the independent re-audit closed all 14 structural findings. W2-F Low L1 is fixed in C5: the refused cold Finding displays `Finding state` / `Unknown` / `Confidence: Unknown` above `PageRefusal`. Its L2 is capture-manifest provenance and changes no product semantics. W5-01a (C1–C3) is read-only selected depth with two pages and no migration. W5-01b (C4–C5) adds the authored scenario pipeline and one page. It owns `0032_w5_cold_scenarios`, exact `down_revision="0030_w4_mini_decisions"`; W3-03's reserved `0031` is unused. W5-01b merges before W5-02 `0033`. C1 and C4 touch shared read/router/schema; C2/C3/C5 mount shared Site frames, navigation or registry. **Every unit receives per-unit independent review** before its dependent unit. No W4-01 Incident/Maintenance/WorkEvent identity, lifecycle or refusal code changes.

`cold-findings`, `cold-work`, Incident, work verification, cold Recommendation and Action belong to W5-02. A W5-01 cue to an unbuilt W5-02 destination is plain text with no `href`, click handler or tab stop. Existing Temperature, Backup, Evidence, Foundation and Financials routes remain real destinations.

Readiness review ran `tools/check-all.ps1`: all 11 guards passed, including the estate self-test. Builders rerun it after shared navigation or registry changes. C2 replaces one `Cooling` unavailable occurrence. C5 makes the shared `Scenarios` tab live for cold only; the unavailable literal remains for other non-mini-grid Sites, so the navigation multiset count is unchanged. Registry titles come from `v69-rendered-panels.json`. **Shared guard files (A1Q W5S-11; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** Lane A edits to `tools/checks/configuration-persistence.ps1` and `tools/writer_guard_probes.py` are additive blocks anchored on the mini-decision lines. A unit that merges after another rebases and keeps both blocks. The W6-01a `$pgReaders` line and the W5 writer blocks do not overlap.

## Shared selected read and guards

`GET /api/sites/{site_code}/cold/cooling` and `/cold/health` reuse the gate factored by C1 from the nested `cold_site_api.build_cold_site_router.opened`: authenticate and Site-scope before lookup; enforce strict paired half-open UTC `from,to` at most 31 days, optional `known_at`, disclosure, one read-only REPEATABLE READ connection, and committed watermark. `schema_version:"cold-depth-1"`; response fields `site_id`, `window:{from,to,known_at,committed_watermark}`, `selection:{state,assessment_revision_ids,accepted_evidence_ids,source_provenance}`, page payload and `links`; top-level keys are exactly, in order, `schema_version, site_id, window, selection, cooling, links` for `/cold/cooling` and `schema_version, site_id, window, selection, health, links` for `/cold/health` (C1 Q1). The state is exactly `cold_reads.STATES`: `CURRENT`, `PENDING_RECOMPUTE`, `STALE_SOURCE`, `HISTORICAL`, `UNKNOWN`, with merged cold precedence (pending before historical). Exact accepted IDs are deduplicated cited IDs from the selected W2-03 assessment, episode/Finding and W2-04 read, never a page or cursor subset: `selection.accepted_evidence_ids` is the sorted lowercase union of the selected revisions' stored `evidence_ids` (merged W2 `_pinned_ids` rule), so it may list a cited ID that is absent from the ledger; every point, context row and Health row `evidence_ids` list is ledger-present only (C1 Q5). Call `ColdReadService.envelope_on(...)["source_provenance"]` for the revision-ID selection; do not pass evidence IDs as revision tokens to `public_provenance`. `evidence/public_provenance.py` classifies the *entire* selected set: empty/broken/foreign is `UNKNOWN`; incompatible classes/runs are `MIXED`. No gateway/run-mode inference and no private Lab truth.

Cooling payload: `recovery_state` (`LIMITED`, `CONTRADICTORY`, `UNKNOWN`), selected accepted compressor/probe points and IDs, `observed_restart_at`, `observed_return_to_policy_at`, nullable `duration_lower_seconds`/`duration_upper_seconds`, `comparison_state` (`CONTEXT_MISSING` for existing W2 producer), and context rows for ambient, continuous power, door, loading and defrost. The W2 selected start chain lacks ordered recovery proof (`cold_site_reads.COOLING_TEXT` and W2-F S2), so all existing W2 replay cases keep duration null and comparison missing even if separate compressor/probe observations exist. Never show mock 36/42 minutes or +17% as measured. The exact Cooling keys are the C1 "Cooling payload" table. Health payload has effective configured `asset_id`, `observation`, `condition_state` (`NEEDS_INVESTIGATION`, `LIMITED`, `UNKNOWN`, `NOT_CONFIGURED`), `limitation`, selected accepted IDs and link; the exact keys, source reads and literals are the C1 "Health read" tables. A selected failed generator start permits `NEEDS_INVESTIGATION`, not failed-part diagnosis. Compressor condition is `UNKNOWN`; one accepted probe permits `Limited` sensing coverage, not room-wide condition. Null is distinct from zero and from an empty array. Malformed 200 responses render refusal, not a fabricated empty state.

Existing refusal codes (copied from `cold_site_api`): `UNAUTHENTICATED` 401, `SITE_SCOPE_FORBIDDEN` 403, `COLD_PARAMETER_UNKNOWN`, `COLD_TIME_INVALID`, `COLD_WINDOW_INVALID`, `COLD_WINDOW_TOO_LONG` 422, `SITE_NOT_FOUND` 404, `COLD_SOURCE_DISCLOSURE_FORBIDDEN` 403, `COLD_READ_UNAVAILABLE` 503. These cursorless routes invent no 409. API `links` use `/api/sites/{site_code}/cold/...` and keys `temperature`, `backup`, `evidence`, `health`; UI translates through `coldUiHref`/`operatorSiteRoutes.ts`. The shell Site token is imported `site_code`, never the internal UUID. Exact selected Finding/assessment UUID and revision ID are carried only as record IDs where applicable. Preserve `from,to,known_at`. Current destinations are `/sites/{site_code}/performance/temperature`, `/sites/{site_code}/performance/backup`, `/sites/{site_code}/evidence`, `/sites/{site_code}/health`; missing ID means text, not a link. Mock F-118 and INC-203 are display examples, never database IDs.

### Visible literal ledger

The Site title comes from imported Site data; `GreenHarvest Cold Room` is a fixture value, not page copy. Dynamic UTC timestamps follow the selected window. All strings below are literal; a server refusal adds its exact `{error:{code,message}}` text below the specified heading and a `Retry` link to the same URL.

| Surface | Exact order, copy and destination |
| --- | --- |
| Cooling header/status | `Sites › {Site name} › Performance › Cooling`; page heading is the frame's existing `SitePageHeader` (imported Site name h1, as v6.9 and the Temperature/Backup siblings), with `Cooling` as breadcrumb end and current subtab (C2 Q-C2-6); `Comparison limited`/`Confidence: Low`/`Observed cooling response is incomplete; ambient, loading and defrost context is missing.` for LIMITED; use C2 state matrix for CONTRADICTORY and UNKNOWN; `Inspect recovery basis →` links to selected Temperature. `Low` describes this comparison, not an assessment enum. |
| Cooling four cards | `Usual time back to 4°C` = `Unknown` / `No matched earlier window`; `This time back to 4°C` = `Not established` / `No ordered compressor-to-policy recovery assessment`; `Difference` = `Unknown` / `A comparison is not supported`; `Comparable?` = `Not yet` / the recovery-state-specific C2 note. If selected policy upper bound differs from 4°C, substitute its configured value; if policy absent use `back to policy` in both labels. |
| Cooling titled panels | `Recovery curves` uses selected accepted points only; if none `No accepted recovery sequence in this window.` `Context normalization` has `Ambient temperature`, `Power availability`, `Door-open duration`, `Loading / batch`, `Defrost`; C1 maps each row to its exact accepted role or always Unknown. The backup-failed door pair is Observed. `Next best evidence` has `Record a comparable recovery` / `Keep load, door, ambient, defrost and cooling-energy records.` (plain text until W5-02), and `Inspect the backup sequence` / `Open Backup →` (live selected Backup). |
| Cooling notice | `These records do not establish cooling degradation or compressor failure. Record loading and door activity and compare a later recovery under similar conditions.` |
| Cold Health | `Sites › {Site name} › Health`; heading `Health`. Cards in order: `Backup generator`, `Cooling plant`, `Temperature sensing` use C3's complete NEEDS_INVESTIGATION/LIMITED/UNKNOWN/NOT_CONFIGURED matrix and state-specific notes. No green physical-condition state. |
| Health panel | `Condition and evidence`; columns `Asset`, `Supported assessment`, `Next evidence`. Effective generator asset: `Automatic start failed`, `Start results conflict`, `Automatic start succeeded`, `No accepted start result` or `Not configured` / `Witness an automatic-start test`; compressor: `Condition unknown` or `Not configured` / `Record matched loading, door and ambient context`; probe: `Single-point observation`, `Multiple probe observations`, `No accepted probe` or `Not configured` / `Add calibrated spatial coverage`. Each observation is the server `health.rows[].observation` string rendered verbatim; the per-state selection is the C1 Health literal table. Asset label/ID from selected Foundation (C1 `foundation_on`; C3 Asset cell rule). Existing Backup/Evidence destinations only. |
| Shared state/empty/refusal | `PENDING_RECOMPUTE`: `New evidence is waiting to be assessed. Earlier selected observations are shown, not a current conclusion.` (new W5 literal, intentionally distinct from `cold_reads.PENDING_NOTE`); `HISTORICAL`: `Read at an earlier evidence cutoff; newer committed evidence exists.` (merged `cold_reads.HISTORICAL_NOTE`); `STALE_SOURCE`: `The selected source is stale for this window.`; `UNKNOWN`: `No selected cold assessment covers this window yet.` Cooling empty `No accepted recovery sequence in this window.` Health empty `No condition observation is available for this window.` Refusal heading `Cold depth unavailable`; button `Retry`. Pending/stale/historical never gain a current positive condition label. |

### Measured mock and content caps

`tools/measure-mock-panels.mjs` measured the seven requested mock screens at 1440×1000 and 390×900 on 2026-10-22; Chrome required a temporary `--no-sandbox` launch adjustment. Temporary script was removed. The mock content region is 1161/360px, document/client scroll widths 1425/1425 and 390/390. A second measured pass inserted a 166-character missing-evidence sentence with a 36-character UUID in the first metric note, first panel prose and first notice at both widths. Its actual worst pass is recorded below. Refusal overlays do not exist in the mock and are capped by app captures.

| Screen | Base page 1440/390; base block heights px | Worst page 1440/390; 390 card height | App caps 1440/390 px |
| --- | --- | --- | --- |
| `cooling` | 1312/2124; status 45/99, cards 113/264, recovery 386/235, context 386/398, notice 42/97, next 234/268 | 1361/2188; cards 344 | status ≤85/140; cards ≤180/360; each panel ≤470/500; notice ≤90/150; next ≤300/360; page ≤1600/2350 |
| `cold-health` | 1001/1244; cards 138/314, condition 198/269 | 1001/1323; cards 393 | cards ≤200/430; condition ≤330/430; page ≤1200/1550 |
| `cold-scenarios` | 1001/1125; panel 316/355, notice 42/78 | 1001/1127; no cards | panel ≤430/560 for one row or empty; notice ≤90/135; page ≤1250/1500 |

At 390, cards wrap two columns and the table scrolls within its panel with sticky first column. UUIDs break at character boundaries. 160-character limitations/source descriptions wrap; longer optional narrative may show the first 160 characters with `Read full basis` disclosing the exact full text. Never ellipsize status, missingness, refusal or source classification. Every capture asserts document `scrollWidth <= clientWidth`, each block cap and refusal overlay cap. **Table and chart primitives (A1Q W5S-10; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** Every table renders through `DataTable` (`frontend/src/ui/DataTable.tsx`; `tools/checks/shell-overflow.ps1` rule 4 refuses a bare `<table`). Every `<svg` is drawn only in the existing diagram, chart, timeline or graphics modules that rule 5 names. No page module draws its own svg.

### Capture producer method, loading and unavailable copy (readiness pass 3; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively)

Every W5-01 page capture follows the W2-04 capture method (`.agent/W2-04-phase-handoff.md`, captures at `019a9e47`):
- **Seed.** A throwaway, uncommitted seed test runs the named C1/C4 producer on a private `assetops_w501cap_test` DB with `ASSETOPS_TEST_TEMPLATE=0`. For C1 this is the W2-02 replay `chain` fixture with `opened(case, chain)` + `run(built)`, which imports the real `COLD-LAB-001` Site; for C4 it is the C4 POST against the same seeded window.
- **Serve.** Serve the API through the `lab_app` host on that DB, with Vite and CDP as in W2-04. Stop both servers and drop the DB before reporting.
- **Clock.** Every current capture omits `known_at`, and its clock is the `window.committed_watermark` returned by the API.
- **Late-reading sequence.** `cooling-*` and `cold-health-*` pending/historical follow one ordered sequence:
  1. Seed `late-reading` and run the worker.
  2. Save the returned watermark `W0`.
  3. Call `advance_late()` without running the worker, then capture `*-pending`.
  4. Run the worker, then capture `*-historical` with `known_at=W0`.
- **Refused captures.** Every `*-refused` capture is the live route with `from` later than `to`, giving 422 `COLD_WINDOW_INVALID`. This is the W2-04 refused-capture precedent: a real served refusal, not a fake client. The 403 disclosure and foreign-Site paths are proved in the C1/C4 Postgres tests and the page tests' stubbed clients.
- **Unavailable copy.** A network failure renders the refusal heading with `The cold depth read could not be reached.` (cold scenarios: `The cold scenarios read could not be reached.`). A malformed 200 renders `The cold depth read answered in an unexpected shape.` (cold scenarios: `The cold scenarios read answered in an unexpected shape.`).
- **Loading copy** (a `<p className="prose">` in the page body while the read is pending): Cooling `Loading the site's cooling read.`, Health `Loading the site's equipment condition read.`, Scenarios `Loading the site's cold scenarios.`
- **Tables.** Every table is a `DataTable`, and no W5-01 page draws an `<svg>` (A1Q W5S-10).

## C1 — selected cold depth read (W5-01a; per-unit review)

**C1 builder delta (A1Q W5-sweep fold; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** The in-flight C1 follow-up is `AssetOpsV1-review2`, head `e7d8afad` on top of `703807cf`. Both commits were checked, and the sweep changes **no code** in it:
- **W5S-1.** `cold_depth._cooling` already reads door events through `ColdReadService.accepted_on`, keeping the rows with `role == cold.DOOR_ROLE`. `analytics/cold_depth.py` has no SQL, driver import, `open(`, `import_module(` or `ANALYTIC_ID`, and must stay that way. `foundation_on` (C1q Q7) stays SELECT-only in `analytics/adapters/postgres_assessment_store.py`, which is already the registered `$assessWriter`. No guard file is edited.
- **W5S-2.** `703807cf` already mounts `build_cold_depth_router(registry, None if cold_reads is None else ColdDepthReadService(cold_reads))` in `main.py`, directly after the `build_cold_site_router` include. Keep that mount and its existing comment; `/cold/health` uses the same router. `analytics/composition.py` is not edited.
- **W5S-9.** `cold_depth_api.py` must still contain none of the HTTP-scan tokens; today it contains none.
- No other sweep finding touches C1.

Read C1, shared contract, merged `analytics/cold_site_reads.py` and `analytics/cold_reads.py`. Files: new `backend/assetops_backend/analytics/cold_depth.py`, `backend/assetops_backend/cold_depth_api.py`, `backend/tests/test_w501_cold_depth_postgres.py`, `backend/tests/test_w501_cold_depth_router.py`; shared **Lane A only** `backend/assetops_backend/main.py`, `backend/assetops_backend/cold_site_api.py` (extract nested `opened` into an importable same-semantics gate), and for the C1 follow-up run (Health + review Lows) `backend/assetops_backend/analytics/cold_site_reads.py` (public `cooling_response_state`, Q6) and `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py` (one new `ColdReadService.foundation_on`, Q7; SQL stays in the adapter because `tools/checks/configuration-persistence.ps1` bans drivers outside `adapters/`). No schema. Compose on `ColdReadService.within` and the W2 selected rows on one connection. Tests prove exact source IDs, first/final cutoff, pending PENDING/LEASED/FAILED job, historical known_at, stale probe, empty, wrong Site, missing selected ID, DB failure and that no W2 case produces a numeric recovery comparison. Existing verified producers: `backend/tests/test_w204_cold_reads.py::test_excursion_five_reads`, `::test_late_reading_pending_then_historical`, `::test_missing_probe_and_empty_window`, `backend/tests/test_w203_cold_reads_postgres.py`, `config/scenarios/cold-backup-failed.yaml`, `backend/tests/fixtures/w2/cold-w203-vectors.json`. Producer command: `pytest backend/tests/test_w204_cold_reads.py::test_late_reading_pending_then_historical backend/tests/test_w202_cold_replay_postgres.py -q` on a private `*_test` DB. Window `[2026-10-06T19:00:00Z,2026-10-06T20:05:00Z)`; current reads omit `known_at` and use the committed DB watermark, whose cold ingestion `decided_at` is wall-clock `clock_timestamp()`/`datetime.now(timezone.utc)` in the merged chain. Save `before["window"]["known_at"]` before `advance_late()`; pass that exact value for the historical read after late advancement. No fixed 2026-10-06 cutoff is valid on a present-day cold replay. The frozen scenario event clock and the wall-clock decision clock are separate facts; pin/read within each fixture by the returned watermark. Review C1 before C2.

**C1 composition and HTTP limits (A1Q W5S-2/W5S-9; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** Lane A wiring in `main.py`, as built in `703807cf`:
- import `ColdDepthReadService` from `assetops_backend.analytics.cold_depth` and `build_cold_depth_router` from `assetops_backend.cold_depth_api`;
- directly after the `app.include_router(build_cold_site_router(...))` call, add `app.include_router(build_cold_depth_router(registry, None if cold_reads is None else ColdDepthReadService(cold_reads)))`.

There is no `analytics/composition.py` edit, because `main.py` already holds `cold_reads`. `cold_depth_api.py` contains none of `register_publication`, `register_authored`, `register_run`, `authored_record`, `simulation_records`, `publish_source`, `evidence_publication`, `batch_publication_link`, `run_attestation`, `evidence.publication`, `runs.source_publication` (`authored_basis` is allowed; `configuration-persistence.ps1` HTTP scan, A1Q W5S-9).

**C1 derivation table (test `test_w501_cold_depth_postgres.py::test_cooling_first_steps_and_context`).** `recovery_state` maps the W2-04 `COOLING_RESPONSE` capability state (`cold_site_reads.py`, the value behind the W2-04 overview `cooling.state`), read through the public `cold_site_reads.cooling_response_state(snap["selected"].get(cold.START_RESPONSE_ANALYTIC))` (Q6): `LIMITED` → `LIMITED`, `CONTRADICTORY` → `CONTRADICTORY`, `UNAVAILABLE` or no selected assessment → `UNKNOWN`. `selected_points` is an ordered list of the selected start-chain `COMPRESSOR` and `PROBE` first observed steps only, each `{role,source_time,evidence_ids}`; it is not a recovery curve. `observed_restart_at` is null because the first compressor step cannot prove a restart after the interruption; `observed_return_to_policy_at` is null because the first probe step cannot prove a later return. Both duration fields are null. No unselected `compressor_state` or probe row may fill them. `comparison_state=CONTEXT_MISSING` for W2. Context rows are exactly: `Ambient temperature` = always `Unknown` (optional `ambient_temperature` exists in `cold-roles-1`, but the W2 assessment does not select it); `Power availability` = `Observed` only from an accepted selected `grid_power_event` row, else `Unknown`; `Door-open duration` = `Observed` only from a matched accepted selected `door_event` OPEN/CLOSE pair with positive elapsed time, else `Unknown`; pairing (`cold_depth.door_pairs`, Q3/L1): sort the accepted door rows by `(source_time, id)`; a `DOOR_OPEN` while no OPEN is held becomes the held OPEN (a further OPEN while one is held is ignored); a `DOOR_CLOSE` with elapsed seconds `> 0` from the held OPEN closes the pair and clears the hold; a `DOOR_CLOSE` with elapsed `<= 0` is skipped and **does not** clear the hold; a CLOSE with no held OPEN is ignored. Several matched pairs give one row whose `duration_seconds` is the integer sum of their elapsed seconds and whose `evidence_ids` are all paired OPEN and CLOSE IDs, sorted; C1 reads the event kind (`record_kind`: `DOOR_OPEN` or `DOOR_CLOSE`) and `source_time` of the exact selected accepted `door_event` evidence IDs. It calls the existing caller-connection `ColdReadService.accepted_on(c, t, s, ids)` (`analytics/adapters/postgres_assessment_store.py`) on the same REPEATABLE READ connection. `analytics/cold_depth.py` holds no SQL text; no `sqlalchemy`, `psycopg`, `alembic`, `yaml`, `pathlib` or `sqlite3` import; no text matching `open\(` in any letter case (so no identifier such as `is_open(`); no `import_module(`; and no module-level `ANALYTIC_ID` (rules 2 and 8 of `tools/checks/configuration-persistence.ps1`, rule 1 of `tools/checks/analytic-declaration.ps1`). C1 makes no `$pgReaders` edit (A1Q W5S-1); CONTEXT links alone do not prove a pair. `Loading / batch` = always `Unknown` (no loading role); `Defrost` = always `Unknown` (no defrost role). The `cold-backup-failed.yaml` producer has `DOOR_OPEN` 19:10 and `DOOR_CLOSE` 19:11, so its door row is `Observed`, duration 60 seconds; loading/ambient/defrost remain Unknown. A door event does not imply a comparable cooling recovery. C1 includes `backend/tests/test_w501_cold_depth_router.py::test_cold_depth_gate_and_links` for the extracted gate and Site-code API links.

Cold selected response `links` is `{temperature,backup,evidence,health}` with API paths by `site_code`; missing selected record IDs remain null. C1's direct stale-source test may use an accepted but stale diagnostic/probe fixture, while the positive replay may not reach it. Every cold persisted capture uses the returned committed watermark, never a guessed event timestamp.

*C1 rulings Q1–Q12 below were produced by Claude Architect under the 2026-10-22 Codex-reset exception; Codex to review retrospectively.* Built commit `703807cf` (Cooling) is accepted with the changes named here; the **C1 follow-up run** builds Health and applies Q2, Q6, Q8–Q12 in one to three commits, then gets per-unit review. C2 does not start until that review accepts.

**C1 Cooling payload (`cooling`, Q1/Q2).** Keys exactly, in order:

| Key | Type | Rule |
| --- | --- | --- |
| `recovery_state` | string | `LIMITED`, `CONTRADICTORY` or `UNKNOWN` per the derivation table. |
| `policy_high_deg_c` | decimal string or null | **New in the follow-up (Q2).** Selected `cold.EXCURSION_ANALYTIC` `result["policy"]["policy_high"]` exactly as stored (already `cold.plain`-normalized, e.g. `"4"`); null when no excursion assessment is selected or the value is absent. Feeds the C2 card labels. |
| `selected_points` | array of `{role,source_time,evidence_ids}` | As built: OBSERVED `COMPRESSOR`/`PROBE` steps whose IDs are all ledger-present, sorted `(source_time, role, evidence_ids)`. |
| `observed_restart_at`, `observed_return_to_policy_at` | null | Always null for W2. |
| `duration_lower_seconds`, `duration_upper_seconds` | null | Always null for W2. |
| `comparison_state` | string | `CONTEXT_MISSING`. |
| `context` | array of exactly five objects | Labels in ledger order. **Every** row has exactly the keys `label`, `state` (`Observed` or `Unknown`), `evidence_ids` (sorted lowercase; `[]` when `Unknown`) and `duration_seconds` (integer only on `Door-open duration` when `Observed`; null on every other row and state). |

**C1 Health read (`GET /api/sites/{site_code}/cold/health`, Q7).** Route in `cold_depth_api.py` beside `/cooling`: same `build_cold_gate`, `WINDOW_KEYS`, `cold_served`, no 409; it calls `ColdDepthReadService.health(t, s, code, lo, hi, known_at)`. On one `ColdReadService.within` connection, in order: `_selected` (shared, including the 422 future `known_at` check), `_head`, `accepted = reads.accepted_on(c, t, s, cited IDs)` (`[]` with no selection), `foundation = reads.foundation_on(c, snap)`, then the pure module function `cold_depth.health_rows(snap, accepted, foundation, links)`. Response `{schema_version, site_id, window, selection, health:{foundation_revision_id, rows}, links}`; `links` is the same four-key object as Cooling.

New adapter method `ColdReadService.foundation_on(c, snap) -> dict | None` in `analytics/adapters/postgres_assessment_store.py` (SELECT-only, caller connection):
1. **With a selection** (`snap["selected"]` non-empty): collect the distinct lowercase IDs `f[0]` of `ColdReadService.basis_revisions_on(c, t, s, snap["selected"][a].revision_id)["foundations"]` over every selected analytic `a`. If the count is not exactly 1, return None. Otherwise read `SELECT id, content FROM foundation_revision WHERE tenant_id = :t AND site_id = :s AND id = :f`; None if absent.
2. **Without a selection:** if `snap["known"]`, `snap["lo"]` or `snap["hi"]` is None, return None. Otherwise `SELECT id, content FROM foundation_revision WHERE tenant_id = :t AND site_id = :s AND {_KNOWN} AND {_OVERLAPS}` with `k=snap["known"]`, `lo`, `hi` (the module's existing `_KNOWN`/`_OVERLAPS`, the `cold_inputs` predicate). Exactly one row is used; zero or several return None.
3. Assets: `SELECT id, asset_code, asset_type FROM asset WHERE tenant_id = :t AND site_id = :s`. Return `{"revision_id": <lowercase id>, "components": [...]}` where each component is a `content["components"]` entry with `component_type` in `GENERATOR`, `COMPRESSOR`, `TEMPERATURE_PROBE` **and** an asset row with `asset_code == component_id` and `asset_type == component_type`, as `{component_type, asset_id (lowercase), asset_code (= component_id), display_name (the component's `display_name`, or null when absent or empty)}`, sorted `(component_type, asset_code)`. A declared component without that matching asset row is omitted. **Q13 (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively):** the returned dict also has a third key, `chamber_probe_asset_id`. To compute it, map each `content["topology"]["nodes"]` `node_id` to its `component_id`. Find the returned `TEMPERATURE_PROBE` components whose `component_id` is the `to_node` component of a `content["topology"]["connections"]` entry that has `medium == "SIGNAL"` and whose `from_node` component has `component_type == "COLD_ROOM"`; this is the Foundation's primary chamber probe edge (`cold_foundation.COLD_EDGE_TYPES`). When exactly one distinct such component exists, `chamber_probe_asset_id` is its lowercase `asset_id`. Otherwise, including when there is no `topology` key, it is null.

`health.foundation_revision_id` is `foundation["revision_id"]`, or null when `foundation` is None. "Foundation resolved" below means `foundation` is not None. `NOT_CONFIGURED` requires a resolved Foundation with no component of that type; an unresolved Foundation never yields `NOT_CONFIGURED`.

`health.rows` has exactly three rows in this order. Each row has exactly the keys, in order, `kind, label, asset_id, assets, observation, condition_state, limitation, next_evidence, evidence_ids, link`. `assets` is that type's resolved components as `{asset_id, asset_code, display_name}` (`[]` when none or unresolved). `evidence_ids` are sorted lowercase and always ledger-present (IDs returned by `accepted`). `link` is null when `condition_state` is `NOT_CONFIGURED`.

| `kind` / `label` / component type / `next_evidence` / `link` | Precedence: condition → `observation` / `limitation` / `evidence_ids` | `asset_id` |
| --- | --- | --- |
| `BACKUP_GENERATOR` / `Backup generator` / `GENERATOR` / `Witness an automatic-start test` / `links.backup` | Let `chains` = selected START `result["chains"]` (or `[]`). 1. Foundation resolved and no generator → `NOT_CONFIGURED`: `Not configured` / `No backup generator is declared in the selected Foundation` / `[]`. 2. Any chain `result == "CONTRADICTORY"` or any step `state == "CONTRADICTORY"` → `UNKNOWN`: `Start results conflict` / `Selected start results conflict; no condition is assessed` / ledger-present IDs of every `START_RESULT` step. 3. Ledger-present IDs of `OBSERVED` steps `START_REQUEST`, `START_RESULT`, `GENERATOR` in chains with `result == "OBSERVED_FAILURE"` are non-empty → `NEEDS_INVESTIGATION`: `Automatic start failed` / `Failed automatic start observed; part not diagnosed` / those IDs. 4. The same IDs from chains with `result == "OBSERVED_SUCCESS"` are non-empty → `UNKNOWN`: `Automatic start succeeded` / `A successful start does not establish generator condition` / those IDs. 5. Else `UNKNOWN`: `No accepted start result` / `No accepted automatic-start result in this window` / `[]`. | Null for `NOT_CONFIGURED`. Else the selected START `result["policy"]["generator_asset_id"]` (lowercase) when it equals an `assets[].asset_id`; else the only asset when `len(assets) == 1`; else null. |
| `COOLING_PLANT` / `Cooling plant` / `COMPRESSOR` / `Record matched loading, door and ambient context` / `/api/sites/{quoted site_code}/cold/cooling` plus the same `from,to,known_at` query as `links` | 1. Foundation resolved and no compressor → `NOT_CONFIGURED`: `Not configured` / `No cooling plant is declared in the selected Foundation` / `[]`. 2. Else `UNKNOWN`: `Condition unknown` / `Comparable recovery and condition evidence absent` / ledger-present IDs of every `OBSERVED` `COMPRESSOR` step in `chains`. | Null for `NOT_CONFIGURED`; else the only asset when `len(assets) == 1`; else null. |
| `TEMPERATURE_SENSING` / `Temperature sensing` / `TEMPERATURE_PROBE` / `Add calibrated spatial coverage` / `links.evidence` | Probe IDs = ledger-present IDs whose ledger `role == "chamber_temperature"`, taken from the selected excursion `result["links"]` entries with `use == "SUPPORT"` (`evidence_id`) together with every `OBSERVED` `PROBE` step ID in `chains`; `n` = the number of distinct ledger `source_id` values among them. 1. Foundation resolved and no probe → `NOT_CONFIGURED`: `Not configured` / `No temperature probe is declared in the selected Foundation` / `[]`. 2. `n == 1` → `LIMITED`: `Single-point observation` / `One accepted probe does not establish room-wide coverage` / probe IDs. 3. `n == 0` → `UNKNOWN`: `No accepted probe` / `No accepted probe observation in this window` / `[]`. 4. `n >= 2` → `UNKNOWN`: `Multiple probe observations` / `Multiple selected probes do not establish room-wide condition` / probe IDs. | Null for `NOT_CONFIGURED`. Else the selected excursion `result["policy"]["probe_asset_id"]` when it equals an `assets[].asset_id`; else the selected START `result["policy"]["probe_asset_id"]` under the same test; else (Q13) `foundation["chamber_probe_asset_id"]` when it is non-null and equals an `assets[].asset_id`; else the only asset when `len(assets) == 1`; else null. `assets` still lists every declared probe, including a non-chamber probe such as `ambient-1`. |

The merged W2 assessment refuses unless exactly one generator, one room and one bound probe exist (`cold_inputs`), so two selected probe sources and a selected `NOT_CONFIGURED` row cannot come from a W2 replay; they are proved on the pure `health_rows` function and on the test-scoped Foundation below.

**C1 public W2 helper (Q6, closes review L4).** Add the module-level pure function `cooling_response_state(start) -> str` to `analytics/cold_site_reads.py`: `chains = (start.result.get("chains") or []) if start else []`; return `"CONTRADICTORY"` if any chain `result == "CONTRADICTORY"` or any step `state == "CONTRADICTORY"`, else `"LIMITED"` if `chains`, else `"UNAVAILABLE"`. `ColdSiteReadService._capabilities` sets `states["COOLING_RESPONSE"] = cooling_response_state(st)` with no other change. `cold_depth._recovery_state` returns `RECOVERY_FROM_W2[cooling_response_state(snap["selected"].get(START))]` and stops importing `ColdSiteReadService`. The existing W2-04 tests pass unchanged.

**C1 follow-up fixes (Q8–Q12).**
- **Q8 (L1).** Change `door_pairs` to the pairing rule in the derivation table: a CLOSE with elapsed `<= 0` is skipped and keeps the held OPEN. Update its docstring to the same words. `test_door_pairs` adds: `[OPEN 19:10, CLOSE 19:10, CLOSE 19:11]` → (OPEN and 19:11 CLOSE IDs, `60`); `[OPEN 19:10, OPEN 19:10:30, CLOSE 19:11]` → (first OPEN and CLOSE IDs, `60`); `[OPEN 19:10, CLOSE 19:11, OPEN 19:20, CLOSE 19:20:30]` → (all four IDs sorted, `90`). The existing zero-elapsed assertion `[OPEN 19:10, CLOSE 19:10]` → `([], None)` stays.
- **Q9 (L2).** In `test_cooling_first_steps_and_context`, replace `state in STATES` with `body["selection"]["state"] == "CURRENT"`. If the replay returns another state, the builder stops and reports it to the Architect; it does not change the expected value.
- **Q10 (L3).** No Postgres missing-ID case is added. `accepted_evidence_append_only` and `assessment_revision_append_only` make a cited-but-absent ID unreachable without disabling triggers. The point drop is proved by the in-memory `_Reads` block of `test_w501_cold_depth_router.py::test_cold_depth_gate_and_links` (`COMPRESSOR_MISSING`). The provenance half (a missing ID is `UNKNOWN` with `EVIDENCE_NOT_FOUND`) is the merged `backend/tests/test_w301_provenance_dto_postgres.py::test_empty_foreign_broken_and_mixed_precedence`, which C1 reruns.
- **Q11 (I1).** `links.health` resolves once `/cold/health` is mounted. `test_cooling_first_steps_and_context` GETs the returned `links.health` path and asserts 200 with `schema_version == "cold-depth-1"`.
- **Q12 (I2).** Delete the vacuous `"36" not in json.dumps([...nulls])` assertion in `test_no_w2_case_has_numeric_comparison`, and extend that six-case test: GET `/cold/health` on the same window and assert that no row is `NOT_CONFIGURED` and that `health.foundation_revision_id` equals `built.run.registered_basis.foundation_revision_id`.

**C1 follow-up tests (exact names).**
- `test_w501_cold_depth_router.py::test_cooling_response_state`: `None` → `UNAVAILABLE`; one LIMITED chain; one chain with a CONTRADICTORY step → `CONTRADICTORY`.
- `test_w501_cold_depth_router.py::test_health_rows` (Q13 adds three cases; every case has two probe assets and no policy match unless stated): `chamber_probe_asset_id` set gives that asset; `chamber_probe_asset_id` null gives `asset_id` null; a selected excursion policy probe that differs from `chamber_probe_asset_id` wins. It is a pure `health_rows` test over in-memory snapshots, one assertion group per table cell. That covers each generator branch 1–5 (precedence: contradictory beats failure, and a failure with no ledger-present ID falls through); the compressor branches; the probe branches with `n` = 0, 1 and 2 distinct `source_id`s; `foundation=None` giving no `NOT_CONFIGURED`; a policy asset not in `assets` falling back to the single asset; two assets with no policy match giving `asset_id` null; `link` null for `NOT_CONFIGURED`; and the exact row key order.
- `test_w501_cold_depth_postgres.py::test_health_failed_start_and_probe` (backup-failed replay, `run(built)`, window `W`): exact top-level and row key order; `foundation_revision_id` equals the run's registered Foundation revision; generator `NEEDS_INVESTIGATION` / `Automatic start failed`, `asset_id` equal to the selected START `result["policy"]["generator_asset_id"]`, and `evidence_ids` recomputed in the test from the stored START result and the ledger; cooling plant `UNKNOWN` / `Condition unknown` with the single compressor asset; temperature sensing `LIMITED` / `Single-point observation` with one distinct ledger `source_id`; Site-code links preserving `from,to,known_at`; wrong Site 404; foreign tenant gives `foundation_revision_id` null and every row `UNKNOWN` with `asset_id` null and `evidence_ids` `[]`; disclosure 403, down store 503, future `known_at` 422.
- `test_w501_cold_depth_postgres.py::test_health_not_configured`: `opened("normal", chain)` **without** `run(built)` (no selection). The first GET of `W` gives all three rows `UNKNOWN` (Q13: the Temperature sensing `asset_id` equals `SELECT id FROM asset WHERE site_id = :s AND asset_code = 'probe-1'`, and its `assets` codes are exactly `['ambient-1', 'probe-1']`), with `asset_id`s equal to the scoped `asset` rows of the Foundation's generator, compressor and probe codes, and `foundation_revision_id` = the original revision. Then, in one transaction on the private test DB, with `at = original.recorded_at + interval '1 microsecond'` (which must be `<=` the response watermark; assert it): `UPDATE foundation_revision SET superseded_at = :at WHERE id = :orig`, and `INSERT` a revision with `version = max(version) + 1`, the same `tenant_id, site_id, valid_from, valid_to, schema_version`, `recorded_at = :at`, `superseded_at` null, content equal to the original with every `GENERATOR`, `COMPRESSOR` and `TEMPERATURE_PROBE` component removed and the `topology` key removed, `content_sha256` = SHA-256 hex of `canonical_json(content)`, `origin = 'PUBLISH'`, `derived_from_revision_id = :orig`, `change_note = 'W5-01 C1 test-scoped Foundation without health assets'`. The second GET (no `known_at`) gives `foundation_revision_id` = the new ID and all three rows `NOT_CONFIGURED` with the table literals, `asset_id` null, `assets` `[]`, `evidence_ids` `[]` and `link` null.

Focused command for the follow-up: `pytest tests/test_w501_cold_depth_router.py tests/test_w501_cold_depth_postgres.py tests/test_w204_cold_reads.py tests/test_w203_cold_reads_postgres.py tests/test_w202_cold_replay_postgres.py tests/test_w301_provenance_dto_postgres.py -q` on a private `*_test` DB, plus `tools/check-all.ps1`.

## C2 — Cooling page (W5-01a; per-unit review)

Read C2, literal ledger, mock caps, C1 DTO. Files: new `frontend/src/sites/ColdDepthClient.ts`, `frontend/src/sites/ColdCooling.tsx`, `frontend/src/sites/__tests__/coldDepth.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/shell/SiteAnalyticsFrames.tsx`, `operatorSiteRoutes.ts`, `frontend/src/sites/coldSiteViews.tsx`, `frontend/src/sites/ColdAssessmentViews.tsx`, `frontend/src/shell/coldSiteRoutes.tsx` (Q-C2-1), `frontend/src/ui/V69Layout.tsx` (one `SITE_SCREEN_DESCRIPTIONS` key), `frontend/src/sites/__tests__/coldRoutes.test.tsx` (Q-C2-5 only), `tools/checks/navigation-truthfulness.ps1`, `tools/checks/navigation-rail-fixtures.ps1`. Replace the single unavailable `Cooling` occurrence only after its truthful route `/sites/{site_code}/performance/cooling` is live. C2 creates `ColdDepthClient.ts` with validated cooling and Health reads and both DTO types; C3 may edit this client for Health wiring while preserving cooling validation. Tests assert exact four cards/five context rows, W2 null comparison, no 36/42/+17% measured claim, state/refusal copy and query-preserving links. Captures owned here at 1440/390: `cooling-limited` (C1 backup-failed producer), `cooling-empty` (C1 missing-probe seed read on the empty window `[2026-10-05T19:00:00Z,2026-10-05T20:05:00Z)`, `UNKNOWN`; at the main window missing-probe has two points, C2 Q-C2-7), `cooling-pending` and `cooling-historical` (C1 late-reading producer), `cooling-refused` (the live C1 route with `from` later than `to`: assert 422 `COLD_WINDOW_INVALID` and the rendered refusal; see the shared capture method). The window and returned watermark are C1's; save the before-late watermark for historical. Replace `$expectedTabs` one `Cooling` occurrence and re-anchor `navigation-rail-fixtures.ps1` negative case to the live `<ColdCooling`/route branch: deleting that live branch must fail. Breadcrumb intentionally ends `Performance › Cooling`; Temperature and Backup siblings remain at `Performance`. At 390, use actual `Not established`, `Unknown` and the 51-character ordered-recovery note in the two-column cap test; wrap values/notes without ellipsis. Run navigation positive/negative fixtures and review C2 before C3.

**C2 literal state matrix (test `coldDepth.test.tsx::cooling_state_copy`).** `LIMITED`: status `Comparison limited`, confidence `Low`, subtitle `Observed cooling response is incomplete; ambient, loading and defrost context is missing.` `CONTRADICTORY`: status `Comparison contradictory`, confidence `Unknown`, subtitle `Selected cooling observations conflict; no recovery comparison is supported.` `UNKNOWN`: status `Comparison unknown`, confidence `Unknown`, subtitle `No selected cooling assessment establishes a recovery comparison for this window.` The four card labels and values in the shared ledger apply to all three states; the fourth note is `Ambient, loading and defrost records missing` only in LIMITED, `Conflicting selected observations prevent a comparison` in CONTRADICTORY, and `No selected comparison basis` in UNKNOWN. The door row uses C1's observed pair, so no visible string says door context is missing in the backup-failed fixture. `CURRENT` leaves the recovery state label intact; pending/historical/stale show their state notice and suppress a current-positive comparison label. The live refusal capture (422, shared capture method) keeps the same URL on Retry.

**C2 DTO, label and link sources (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `coldDepth.test.tsx::cooling_dto_and_labels`).** `ColdDepthClient.ts` validates the exact C1 top-level and `cooling` key sets, order-insensitive. It also validates the value sets in the C1 "Cooling payload" table and the five context labels in order. Any missing, extra or ill-typed key is malformed and renders the `Cold depth unavailable` refusal. The Health DTO type follows the C1 "Health read" tables; C3 adds its validation. Card labels use `cooling.policy_high_deg_c`: null gives `Usual time back to policy` / `This time back to policy`; otherwise `Usual time back to {value}°C` / `This time back to {value}°C`, with the string inserted verbatim (`"4"` gives `4°C`). `Inspect recovery basis →` is `coldUiHref(links.temperature)`, `Open Backup →` is `coldUiHref(links.backup)`, and a null href renders text. C2 adds `cooling` to the `ColdSiteRoutes` type and `cooling: routes.cooling` to the `bases` map in `coldUiHref` (`coldSiteViews.tsx`), with `routes.cooling` = `/sites/{site_code}/performance/cooling`. `links.health` stays unmapped (text) until C3.

**C2 readiness pass 3 (Q-C2-1..4 and dry-read; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; tests `coldDepth.test.tsx::cooling_state_copy`, `::cooling_panels`, `::cooling_nav_and_routes`).**
- **Q-C2-1 (routes).** `shell/coldSiteRoutes.tsx` is on C2's list. Add `cooling: sitePerformanceHref(siteId, "cooling"),` directly after the `backup` entry, add `cooling: string` to `ColdSiteRoutes`, and add `cooling: routes.cooling` to the `coldUiHref` `bases` map. C3 adds `health: siteHealthHref(siteId),` the same way.
- **Frame and navigation.** `SiteAnalyticsFrames.tsx`: `COLD_PERFORMANCE_VIEWS` gains `cooling: "cooling"`, and its value type becomes `"temperature" | "backup" | "cooling"`.
  - `ColdAssessmentViews.tsx`: replace `<UnavailableTab label="Cooling" />` with `<li className="site-tabs__item"><Link className="site-tabs__link" to={props.subtabHref("cooling")} data-performance-subtab="cooling" aria-current={view === "cooling" ? "page" : undefined}>Cooling</Link></li>`. When `view === "cooling"`, the frame body renders `<ColdCooling` (and not the Temperature/Backup body).
  - Page description: `SITE_SCREEN_DESCRIPTIONS.cooling = "Performance · recovery under comparable conditions"` (the v6.9 subtitle).
  - `navigation-truthfulness.ps1`: drop one `"Cooling"` from `$expectedTabs`. Add a positive check that `frontend/src/sites/ColdAssessmentViews.tsx` contains both `data-performance-subtab="cooling"` and `<ColdCooling`, otherwise failing with `The live cold Cooling subtab or page branch is missing`.
  - `navigation-rail-fixtures.ps1`: replace the fixture `the cold Cooling entry is dropped` with two negative fixtures that both expect that message: `the live cold Cooling subtab is dropped` (`Set-ModuleLines $modules $cold 'data-performance-subtab="cooling"' ''`) and `the live cold Cooling page branch is dropped` (`Set-ModuleLines $modules $cold '<ColdCooling' '<Missing'`).
- **Q-C2-2 (`Context normalization`).** One `DataTable` with columns `Factor`, `Evidence`, `Status`. The v6.9 `Match` heading is deliberately not used, because no comparison is matched.
  - `Status` is a neutral `Badge` with the row `state` verbatim (`Observed` or `Unknown`).
  - `Evidence` cells: Ambient temperature → `Not selected by the cooling assessment`. Power availability Observed → `1 accepted grid power record` or `{n} accepted grid power records` (`n` = `evidence_ids.length`); Unknown → `No accepted grid power record`. Door-open duration Observed → `Door open for {d}`; Unknown → `No matched door open/close pair`. Loading / batch → `No loading record role`. Defrost → `No defrost record role`.
  - `{d}`: under 60 s → `{s} s`; otherwise `{m} min`, or `{m} min {r} s` when `r = s % 60` is non-zero. The backup-failed row reads `Door open for 1 min`.
  - No evidence IDs are printed in this table.
- **Q-C2-3 (`Recovery curves`).** No chart and no `<svg>` (rule 5 of `shell-overflow.ps1` admits svg only in `SiteSingleLineDiagram.tsx`, `HistoryCharts.tsx`, `SiteOverview.tsx`, `assessmentGraphics.tsx` and the icon modules). This is a deliberate deviation from the v6.9 `lineChart('recovery')`, which the registry reason already records.
  - Panel description `Selected first observations only; not a recovery curve.`
  - Non-empty: a `DataTable` with columns `Step`, `Time (UTC)`, `Evidence`, one row per `selected_points` entry in DTO order. `Step` = the existing `recordLabel(role)` (`compressor_state` → `Compressor running`, `chamber_temperature` → `Chamber temperature`). `Time (UTC)` = the existing `utcClock(source_time)` (`HH:MM:SS`). `Evidence` = the evidence IDs joined with `, ` inside `data-vocabulary-exempt="source-reference"`.
  - C2 adds `export` to `recordLabel`, `utcClock`, `SelectedWindowBar` and `RequestedWindowBar` in `coldSiteViews.tsx` and reuses them, with no copies.
  - Empty: `No accepted recovery sequence in this window.`
- **Q-C2-4 (currentness).** **Currentness (no other placement).** The status line keeps the state matrix badge, `Confidence:` badge and subtitle for every `selection.state`; no label in these pages is a current positive, so nothing is replaced. When `selection.state` is not `CURRENT`, an amber `Notice` (`ui/V69Layout.tsx`) directly below the status line (or, on a page without a status line, directly above the first cards/panel) renders exactly the shared-ledger sentence for that state; `CURRENT` renders no notice. The `StatusBar` has `label="Cooling comparison"`, renders the two neutral badges (the matrix status, then `Confidence: {Low|Unknown}`) followed by the subtitle, and takes the action `Inspect recovery basis →`. `SelectedWindowBar` renders above it; a refusal shows `RequestedWindowBar` and the refusal block.
- **Next best evidence.** `Record a comparable recovery` is plain text with no link. `Open Backup →` links to `coldUiHref(links.backup)`.

**C2 build rulings Q-C2-5..7 (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).**
- **Q-C2-5.** `frontend/src/sites/__tests__/coldRoutes.test.tsx` is on C2's list for this edit only, in the `W2-03 q3: unavailable entries, wording and provenance` `it.each`:
  - delete the two `["Performance sections", ROUTES[0][1] ...]` and `["Performance sections", ROUTES[1][1] ...]` rows;
  - replace `expect(nav.querySelectorAll("a")).toHaveLength(aria === "Performance sections" ? 2 : 0);` with `expect(nav.querySelectorAll("a")).toHaveLength(0);`;
  - replace the selector `'a[href*="cooling"], a[href*="recommendation"]'` with `'a[href*="recommendation"]'`.
  Live Cooling navigation is proved by `coldDepth.test.tsx::cooling_nav_and_routes` and the rail fixtures.
- **Q-C2-6.** Confirmed: the h1 is the frame's `SitePageHeader` (the Site name), and `Cooling` is the breadcrumb end and current subtab. The ledger row is corrected.
- **Q-C2-7.** Confirmed: `cooling-empty` is the missing-probe seed read on the 2026-10-05 window.

## C3 — cold Health and W5-01a close (per-unit review)

Read C3, literal ledger, mock caps, C1 DTO. Files: new `frontend/src/sites/ColdHealthDepth.tsx`, `frontend/src/sites/__tests__/coldHealthDepth.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/shell/SiteHealthFrames.tsx`, `operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `frontend/docs/architecture/v69-screen-ledger.json`, `frontend/src/sites/ColdDepthClient.ts`, `frontend/src/sites/ColdFoundationViews.tsx`, `frontend/src/sites/coldSiteViews.tsx` (adds `health` to `coldUiHref`), `frontend/src/shell/coldSiteRoutes.tsx` (adds `health: siteHealthHref(siteId)`), `frontend/src/sites/__tests__/siteHealthBoundary.test.tsx`, `frontend/src/sites/__tests__/coldSiteViews.test.tsx`; run `frontend/docs/architecture/check_v69_dependency_registry.cjs`. Keep S7 two-clock gateway contact separate from equipment condition. Registry titled panels `(cooling,1) Recovery curves`, `(cooling,2) Context normalization`, `(cooling,3) Next best evidence`, `(cold-health,1) Condition and evidence` map only exact C1 selected read/gap paths; unresolved comparator and physical-condition nodes stay unresolved. Captures at 1440/390: `cold-health-failed-start`, `cold-health-unknown`, `cold-health-pending`, `cold-health-historical`, `cold-health-refused`, using C1 backup-failed/empty/late/refusal producers and clock equal to the C1 response watermark; historical uses the before-late watermark, not a fixed 2026 instant. Tests assert no physical health from gateway contact/configuration. Run `tools/check-all.ps1`, focused tests and one real-Postgres full suite, then review/merge W5-01a.

**C3 Health composition and state copy (test `coldHealthDepth.test.tsx::condition_matrix`).** For COLDCHAIN, `SiteHealthFrames.tsx` renders the v69 condition cards, then `Condition and evidence`, then the bounded condition notice. It retains the shared S7 `Data sources · data quality, not equipment condition` panel below `Condition and evidence` using the existing `SiteHealth.tsx` gateway read and independent server-receipt clock. The live `Health › Data sources →` link in `ColdFoundationViews.tsx:646` targets this panel through the existing heading ID: `{healthHref}#site-health-sources-heading` (no new ID). Cold Evidence source analysis is a different read. Preserve S7 acceptance and update `siteHealthBoundary.test.tsx` and `coldSiteViews.test.tsx` for the composition and link. The 1200/1550px mock page cap measured the condition-only composition. C3 keeps the S7 panel and checks a composed app page cap of 1900/2350px at 1440/390, a gateway panel cap of 700/800px, and no horizontal document overflow in each Health capture; record actual measurements before review. The table deliberately uses v69 column `Supported assessment`; the third probe row is a deliberate W5 addition, measured under the 330/430px cap. Card notes are conditional: backup `NEEDS_INVESTIGATION` → `Failed automatic start observed; part not diagnosed`; backup `UNKNOWN` → `No accepted automatic-start result in this window`; backup `NOT_CONFIGURED` → value `Not configured`, note `No backup generator is declared in the selected Foundation`. Cooling plant `UNKNOWN` → `Comparable recovery and condition evidence absent`; cooling plant `NOT_CONFIGURED` → value `Not configured`, note `No cooling plant is declared in the selected Foundation`. Temperature sensing `LIMITED` (exactly one accepted selected probe) → `One accepted probe does not establish room-wide coverage`; `UNKNOWN` → `No accepted probe observation in this window` when none is selected, or `Multiple selected probes do not establish room-wide condition` when two or more are selected; `NOT_CONFIGURED` → value `Not configured`, note `No temperature probe is declared in the selected Foundation`. No other positive condition value is allowed. Table row observations follow the same state: absent asset → `Not configured`; present without selected observation → `No accepted start result`/`Condition unknown`/`No accepted probe`; selected failed start → `Automatic start failed`; accepted single probe → `Single-point observation`. C1 and C3 also test exactly one versus two accepted selected probes; two remains `UNKNOWN` physical condition. A `NOT_CONFIGURED` state is produced by a test-scoped selected Foundation without that asset and asserted by `test_w501_cold_depth_postgres.py::test_health_not_configured`; no existing cold replay is falsely labelled as that state.

**C3 Health DTO rendering (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `coldHealthDepth.test.tsx::health_dto_rendering`).** The server owns every condition string. The UI chooses none of them and renders the C1 `health.rows` verbatim.

**C3 readiness pass 3 (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `coldHealthDepth.test.tsx::health_states_and_loading`).**

**C3 condition notice (closure 2; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** Directly below `Condition and evidence` (above the S7 Data sources panel), render one amber `Notice` with exactly: `These records show what was observed at the selected assets. They do not establish physical equipment condition or diagnose a failed part.` The v6.9 mock has no Health notice; this is a bounded W5 literal. Test: `coldHealthDepth.test.tsx::condition_matrix` asserts the sentence.
- **Routes.** `shell/coldSiteRoutes.tsx` is on C3's list: add `health: siteHealthHref(siteId),` and `health: string` to `ColdSiteRoutes`.
- **Currentness.** **Currentness (no other placement).** The status line keeps the state matrix badge, `Confidence:` badge and subtitle for every `selection.state`; no label in these pages is a current positive, so nothing is replaced. When `selection.state` is not `CURRENT`, an amber `Notice` (`ui/V69Layout.tsx`) directly below the status line (or, on a page without a status line, directly above the first cards/panel) renders exactly the shared-ledger sentence for that state; `CURRENT` renders no notice. The cold Health page has no status line, so the notice sits directly above the condition cards, under `SelectedWindowBar`.
- **Copy.** Loading, unavailable and refusal copy follow the shared capture-method section.
- **Captures.** `cold-health-unknown` is the backup-failed seed read on the empty window `[2026-10-05T19:00:00Z,2026-10-05T20:05:00Z)` (no selection; rows `UNKNOWN`). `cold-health-refused` is the shared 422 `from>to` refusal.
- **Data sources link.** The `Health › Data sources →` link uses `#site-health-sources-heading`.
- **Validation.** `ColdDepthClient.ts` validates the exact top-level, `health` and row key sets and the three rows' `kind` order. Each row's `(kind, condition_state, observation, limitation)` must be one of the tuples in the C1 Health literal table, and `next_evidence` must equal that kind's literal. Anything else is malformed and renders the `Cold depth unavailable` refusal.
- **Cards** (in row order). Label = `label`. Value by `condition_state`: `NEEDS_INVESTIGATION` → `Needs attention` (the v6.9 `cold-health` card word), `LIMITED` → `Limited`, `UNKNOWN` → `Unknown`, `NOT_CONFIGURED` → `Not configured`. Note = `limitation`. Card link = `coldUiHref(row.link)`; null renders no link. `coldUiHref` gains `health: routes.health` (`/sites/{site_code}/health`), and the cooling-plant link maps through C2's `cooling` entry.
- **`Condition and evidence` table**, one row per `health.rows` entry. The `Asset` cell, in order of precedence: (1) when `asset_id` is non-null, the matching `assets[]` entry's `display_name`, or its `asset_code` when `display_name` is null, followed by the `asset_id` as a `data-vocabulary-exempt="source-reference"` record ID; (2) when `asset_id` is null and `assets` is non-empty, each entry's `display_name` (else `asset_code`), joined with `, `; (3) when `assets` is empty, `label`. `Supported assessment` = `observation`. `Next evidence` = `next_evidence`.
- **Empty sentence.** `No condition observation is available for this window.` renders above the table if and only if every row has `evidence_ids` `[]` and no row is `NOT_CONFIGURED`.
- **Notes.** The card notes listed above are this table's `limitation` strings. Three new literals extend them: `Selected start results conflict; no condition is assessed` (generator conflict), `A successful start does not establish generator condition` (generator success) and `Multiple selected probes do not establish room-wide condition` (two or more probe sources). The same tuple applies to the table observations `Start results conflict`, `Automatic start succeeded` and `Multiple probe observations`.

**Registry rows written by C3** in `v69-dependency-registry-pilot.json` (C3 creates only `I-W5-cold-depth-read` and `I-W5-cold-depth-ui`; C5 alone creates the scenario nodes). The following table summarizes the rows; the executable JSON and ledger values below are authoritative. Each panel row has `status` stays `gap` until implementation review accepts the node evidence:

| screen_id, panel_index, title | area | requires | status | reason |
| --- | --- | --- | --- | --- |
| `cooling`, 1, `Recovery curves` | `cold-chain` | `I-W5-cold-depth-read`, `I-W5-cold-depth-ui` | `gap` | `W5-01a selected first steps do not establish an ordered recovery curve.` |
| `cooling`, 2, `Context normalization` | `cold-chain` | `I-W5-cold-depth-read`, `I-W5-cold-depth-ui` | `gap` | `Ambient is not selected by the W2 cooling assessment; loading and defrost roles are absent, so those context rows show Unknown.` |
| `cooling`, 3, `Next best evidence` | `cold-chain` | `I-W5-cold-depth-read`, `I-W5-cold-depth-ui` | `gap` | `Evidence actions are bounded to existing Backup and Temperature destinations.` |
| `cold-health`, 1, `Condition and evidence` | `cold-chain` | `I-W5-cold-depth-read`, `I-W5-cold-depth-ui` | `gap` | `Selected start and probe observations do not establish physical equipment health.` |

C3 inserts only its depth rows and nodes together; `node` IDs in `requires` must exist before `check-all`. C5 adds its scenario nodes and row in W5-01b.

## C4 — authored cold scenario store (W5-01b; per-unit review)

Allowed authored what-if contract `cold-scenario-authored/1`: the only `kind` is `STOCK_VALUE_CONTEXT`; the only assumption object is `{stock_quantity,stock_unit,unit_value,currency}` with quantity and value decimal strings greater than zero and at most 8 fractional digits, `stock_unit` a nonempty 1–32 character label, and `currency` a three-letter uppercase ISO 4217 code. The baseline is the selected observed W2 cold window and its accepted IDs, **not** a matched counterfactual; there is no calculated amount, spoilage rule, comparison delta or outcome. Scenario scope is exactly one authorized Site and selected half-open UTC period of at most 31 days; cross-Site scenarios and currency conversion are refused as `COLD_SCENARIO_INVALID`. Formula version is `AUTHORED_ONLY/1` and must be stored. This deliberately implements a reviewable authored scenario list without claiming a financial translation that the selected evidence cannot support.

Read C4, shared contract, merged `mini_decisions/scenarios.py` command/actor pattern. Files: **Lane A only** `backend/migrations/versions/0032_w5_cold_scenarios.py`, new `backend/assetops_backend/cold_scenarios/{rules,store,service}.py`, `cold_scenarios_api.py`, `backend/tests/test_w501_cold_scenarios_postgres.py`; shared `backend/assetops_backend/main.py`, `backend/assetops_backend/analytics/cold_depth.py` (adds `basis_on` only), `tools/checks/configuration-persistence.ps1` and `tools/writer_guard_probes.py` (rule-8 writer policy below). Migration creates scoped `cold_scenario` (tenant/site/id, public_no, actor, created_at) and append-only `cold_scenario_revision` (id, scenario, revision_no, prior, recorded_at, actor, idempotency_key, name max 160, assumptions JSON, authored basis JSON, basis_sha256, correction reason). Composite Site FK, unique `(scenario_id,revision_no)` and `(scenario_id,idempotency_key)`; never rewrite a revision. Authored basis includes half-open window, exact selected W2 assessment revision IDs, accepted evidence IDs, Foundation revision ID, cutoff and source class. No observed-outcome column, enum, field or status. Correction appends. Same key/body returns same ID; same key/different body is 409 `COLD_SCENARIO_IDEMPOTENCY_CONFLICT`; stale predecessor 409 `COLD_SCENARIO_REVISION_CONFLICT`; invalid input 422 `COLD_SCENARIO_INVALID`; existing cold access/503 codes apply. Ordinary viewer has `GET /api/sites/{site_code}/cold/financials/scenarios?from=&to=&known_at=&scenario_at=&limit=&cursor=`; POST same path and `POST .../{scenario_id}/revisions` require existing decision principal/actor policy. List DTO `cold-scenarios-1` has window/watermark, scenario_at, selection, items, next_cursor; row fields `id`, `revision_id`, `name`, `assumptions`, `authored_basis`, `recorded_at`, `scenario_state` (`DEFINED` or read-only `HISTORICAL`) and exact source IDs. No observed outcome field. Default 50/max 100; cursor binds tenant/Site/window/evidence cutoff/scenario_at/watermark/last `(recorded_at,id)`; invalid 422 `COLD_SCENARIO_CURSOR_INVALID`, changed basis 409 `COLD_SCENARIO_CURSOR_BASIS_CHANGED`. Watermarked empty means no authored row in scope, not failed read. Tests prove migration/downgrade/sole head, auth, replay, foreign IDs, cutoff, cursor, store failure and no revenue/spoilage/savings claim. Persisted positive producer is this new POST exercised by `test_w501_cold_scenarios_postgres.py` with exact C1 selected IDs; it must exist and pass at C4 review before C5 captures. Use the C1 returned evidence watermark for basis selection, and DB `clock_timestamp()` for authored `recorded_at`/default `scenario_at`. The new POST producer saves `scenario_at` after first write, then appends correction at a later DB instant; historical list passes saved `scenario_at`. The clocks remain distinct response fields. Never compare a 2026 evidence event timestamp to a present-day authored row. Review C4 before C5.

**C4 exact persisted schema and wire contract.** Migration `0032_w5_cold_scenarios` first creates `cold_scenario_public_no_seq`, then `cold_scenario`: `id uuid PK`, `tenant_id uuid NOT NULL`, `site_id uuid NOT NULL`, `public_no bigint NOT NULL DEFAULT nextval('cold_scenario_public_no_seq')`, `create_key text NOT NULL`, `create_payload_sha256 text NOT NULL`, `create_actor_id text NOT NULL`, `created_at timestamptz NOT NULL DEFAULT clock_timestamp()`, `actor_kind text NOT NULL`, `actor_id text NOT NULL`; named constraints `cold_scenario_scope_uk UNIQUE(tenant_id,site_id,id)`, `cold_scenario_public_uk UNIQUE(tenant_id,public_no)`, `cold_scenario_create_key_uk UNIQUE(tenant_id,site_id,create_key)`, and named `cold_scenario_site_fk` on `(tenant_id,site_id)` to `site(tenant_id,id)`. Root checks `cold_scenario_create_key_check` length 8..128, `cold_scenario_create_payload_sha256_check` 64 lowercase hex, `cold_scenario_create_actor_id_check` trimmed length 1..128. `cold_scenario_revision`: `id uuid PK`, `tenant_id uuid NOT NULL`, `site_id uuid NOT NULL`, `scenario_id uuid NOT NULL`, `revision_no integer NOT NULL`, `supersedes_revision_id uuid NULL`, `name text NOT NULL`, `kind text NOT NULL`, `assumptions jsonb NOT NULL`, `authored_basis jsonb NOT NULL`, `basis_sha256 text NOT NULL`, `formula_version text NOT NULL`, `correction_reason text NULL`, `actor_kind text NOT NULL`, `actor_id text NOT NULL`, `authorization_basis text NOT NULL`, `attestation text NOT NULL`, `idempotency_key text NOT NULL`, `payload_sha256 text NOT NULL`, `recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()`. Checks: `cold_scenario_revision_revision_no_check` (>0), `cold_scenario_revision_name_check` (trimmed length 1..160), `cold_scenario_revision_kind_check` (`STOCK_VALUE_CONTEXT`), `cold_scenario_revision_formula_check` (`AUTHORED_ONLY/1`), `cold_scenario_revision_chain_check` (revision 1 has null prior/reason; later revision has nonnull prior and trimmed reason length 1..2000), `cold_scenario_revision_basis_sha256_check` and `cold_scenario_revision_payload_sha256_check` (each 64 lowercase hexadecimal characters), `cold_scenario_revision_idempotency_key_check` (length 8..128), `cold_scenario_revision_actor_check` (nonempty actor kind/id/authorization basis/attestation). Named FKs `cold_scenario_revision_scenario_fk` `(tenant_id,site_id,scenario_id)` to scoped root, `cold_scenario_revision_previous_fk` `(tenant_id,site_id,supersedes_revision_id)` to scoped revision; named unique `cold_scenario_revision_scope_uk(tenant_id,site_id,id)`, `cold_scenario_revision_no_uk(scenario_id,revision_no)`, `cold_scenario_revision_previous_uk(scenario_id,supersedes_revision_id)`, `cold_scenario_revision_key_uk(scenario_id,idempotency_key)`. Index `cold_scenario_site_order(tenant_id,site_id,recorded_at DESC,id)`. Downgrade removes index, revision, root, then sequence. Basis JSON is server-resolved inside the write snapshot; client cannot choose IDs or cutoff. **Basis source read (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** C4 adds the public method `ColdDepthReadService.basis_on(c, t, s, code, lo, hi, known_at) -> dict` to `backend/assetops_backend/analytics/cold_depth.py`, a shared file added to the C4 file list. It composes only C1 pieces on the caller's connection `c`: `_selected` (including the 422 future `known_at` check), `_head`, and `ColdReadService.foundation_on(c, snap)`. It returns `{"window": head["window"], "selection": head["selection"], "authored_basis": {"from": window.from, "to": window.to, "cutoff": window.known_at, "assessment_revision_ids": selection.assessment_revision_ids, "accepted_evidence_ids": selection.accepted_evidence_ids, "foundation_revision_id": foundation["revision_id"] or null, "source_provenance": selection.source_provenance}}`. `cold_scenarios/store.py` calls it with its own write-transaction connection for POST, and with its read connection for the GET list's `window` and `selection`. POST returns 422 `COLD_SCENARIO_INVALID` when `assessment_revision_ids` is `[]` or `foundation_revision_id` is null. Test: `test_w501_cold_scenarios_postgres.py::test_command_schema_refusals_and_replay` asserts that the stored `authored_basis` equals `basis_on` on the backup-failed replay window.

POST root and correction both take gate query `from,to,known_at`; `from,to` are required, strict UTC, paired and at most 31 days; optional `known_at` selects the evidence basis within the write snapshot. Unknown/repeated query keys use `COLD_PARAMETER_UNKNOWN` 422. No body field may override the Site or selected window. Server-resolved `authored_basis` JSON has closed keys `{from,to,cutoff,assessment_revision_ids,accepted_evidence_ids,foundation_revision_id,source_provenance}`; UUID arrays are sorted/deduplicated and every ID belongs to this selected Site/window. SQL JSON checks require `jsonb_typeof(assumptions)='object'` and `jsonb_typeof(authored_basis)='object'`; exact keys, decimal grammar, ISO currency and selected-ID membership are service rules. The root stores `create_payload_sha256` of canonical command plus the selected query/window; exact-key replay compares it with the first revision payload hash.

POST root body, closed keys: `{schema_version:"cold-scenario-command-1",idempotency_key:string,actor:{kind:"SERVICE",id:string,attestation:string},name:string,kind:"STOCK_VALUE_CONTEXT",assumptions:{stock_quantity:string,stock_unit:string,unit_value:string,currency:string}}`. Correction POST adds `supersedes_revision_id` UUID and `correction_reason` 1..2000 characters; all other keys identical. Reuse `mini_decisions.scenarios.admit`/`authorize`: missing/non-SERVICE principal or wrong scope/grant → 403 `DECISION_WRITE_FORBIDDEN`; USER actor → 403 `DECISION_USER_AUTH_REQUIRED`; malformed service attestation → 422 `DECISION_ATTESTATION_INVALID` (merged `mini_decisions/model.py:34`). Gate/read failures retain `UNAUTHENTICATED` 401, `SITE_SCOPE_FORBIDDEN` 403, `SITE_NOT_FOUND` 404, `COLD_SOURCE_DISCLOSURE_FORBIDDEN` 403, `COLD_READ_UNAVAILABLE` or `DECISION_STORE_UNAVAILABLE` 503. Invalid body, nonselected/foreign basis, no selected cold assessment, cross-Site/currency conversion → 422 `COLD_SCENARIO_INVALID`; same key/different canonical body → 409 `COLD_SCENARIO_IDEMPOTENCY_CONFLICT`; stale prior → 409 `COLD_SCENARIO_REVISION_CONFLICT`. New root/correction → 201 `{schema_version:"cold-scenario-write-1",id,code:"CSCN-000001",revision_id,revision_no}`; exact replay → 200 same body. Public number uses the global `cold_scenario_public_no_seq` with `CSCN-` plus six minimum zero-padded decimal digits.

| C4 refusal | HTTP | Trigger |
| --- | ---: | --- |
| `UNAUTHENTICATED` | 401 | Missing authenticated request |
| `SITE_SCOPE_FORBIDDEN`, `COLD_SOURCE_DISCLOSURE_FORBIDDEN` | 403 | Site or source disclosure denied |
| `DECISION_WRITE_FORBIDDEN`, `DECISION_USER_AUTH_REQUIRED` | 403 | Service principal or actor rejected |
| `DECISION_ATTESTATION_INVALID` | 422 | Malformed service attestation |
| `SITE_NOT_FOUND` | 404 | No authorized cold Site |
| `COLD_PARAMETER_UNKNOWN`, `COLD_TIME_INVALID`, `COLD_WINDOW_INVALID`, `COLD_WINDOW_TOO_LONG`, `COLD_SCENARIO_INVALID`, `COLD_SCENARIO_CURSOR_INVALID` | 422 | Query, time, body, basis or cursor invalid |
| `COLD_SCENARIO_CURSOR_BASIS_CHANGED`, `COLD_SCENARIO_IDEMPOTENCY_CONFLICT`, `COLD_SCENARIO_REVISION_CONFLICT` | 409 | Changed selection, replay body or predecessor |
| `COLD_READ_UNAVAILABLE`, `DECISION_STORE_UNAVAILABLE` | 503 | Selected read or authored store unavailable |

GET list `cold-scenarios-1`: `{schema_version,site_id,window:{from,to,known_at,committed_watermark},scenario_at,selection:{state,assessment_revision_ids,accepted_evidence_ids,source_provenance},items:[{id,code,revision_id,revision_no,name,kind,assumptions,authored_basis,recorded_at,scenario_state}],next_cursor}`. `selection.state` comes from C1's selected cold read and drives C5 pending notice. Revision 1 `authored_basis.from,to` fixes each root window. A correction resolves its query `from,to` and must equal revision 1 exactly; mismatch returns 422 `COLD_SCENARIO_INVALID` before append. Test same-window correction and cross-window refusal. List only roots whose revision 1 `authored_basis.from,to` equals the requested period; select each latest revision with `recorded_at <= scenario_at` and `authored_basis.cutoff <= window.known_at`. `scenario_state=HISTORICAL` iff the selected revision is superseded at current authored DB time or the caller passed `scenario_at` before the latest stored revision or `known_at` before the current evidence watermark; otherwise `DEFINED`. A revision written after `scenario_at` is absent, never backdated. If `scenario_at` is omitted, resolve it from `clock_timestamp()` within the read snapshot; validate explicit `scenario_at` as UTC and no later than that DB time, returning `COLD_TIME_INVALID` 422 otherwise. Keep the evidence `known_at` independent: it is the selected assessment cutoff, not the authored write clock. Cursor binds the exact selection and last `(recorded_at,id)`; 422 cursor invalid, 409 basis changed. Tests `test_w501_cold_scenarios_postgres.py::test_command_schema_refusals_and_replay`, `::test_pending_historical_list_and_cursor`, `::test_migration_constraints` prove every branch.

**C4 guard and composition ownership (A1Q W5S-3/W5S-4/W5S-9; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** `cold_scenarios/store.py` is a new product database writer. Without the policy below, rule 8 fails with "Database driver imported outside" and "A second product database writer". `cold_scenarios_api.py` contains none of `register_publication`, `register_authored`, `register_run`, `authored_record`, `simulation_records`, `publish_source`, `evidence_publication`, `batch_publication_link`, `run_attestation`, `evidence.publication`, `runs.source_publication` (`authored_basis` is allowed; `configuration-persistence.ps1` HTTP scan, A1Q W5S-9).

**C4 rule-8 writer policy (literal).**

1. **Writer and tables.** In `tools/checks/configuration-persistence.ps1`, after line 823 (`foreach ($table in $decisionTables) { $decisionInsertsSeen[$table] = 0 }`), insert:

   ```powershell
   # W5-01b C4 (migration 0032): the authored cold scenario store is the sole runtime writer of the two 0032 tables,
   # INSERT-only (no UPDATE, DELETE, upsert, TRUNCATE, MERGE, COPY or DDL), and it writes no other table. Each table
   # keeps at least one owner INSERT in the store (anti-vacuity below).
   $coldScenarioWriter = "$backendRoot/cold_scenarios/store.py"
   $coldScenarioTables = @('cold_scenario', 'cold_scenario_revision')
   $coldScenarioInsertsSeen = @{}
   foreach ($table in $coldScenarioTables) { $coldScenarioInsertsSeen[$table] = 0 }
   ```

2. **Writer tallies.** Append `$coldScenarioWriter` as the last element of `$pgWriters`. Append `; $coldScenarioWriter = 0` inside the `$pgWritesSeen` literal and `; $coldScenarioWriter = $false` inside the `$pgDriverSeen` literal.

3. **Forbidden-line check.** After the mini-decision forbidden-line block (`:938-941`), insert:

   ```powershell
               if ($module.Path -eq $coldScenarioWriter -and $line -match $actionForbidden) {
                   $failures.Add("The cold scenario store never updates, deletes, truncates, upserts or runs DDL; " +
                       "$($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
               }
   ```

4. **Statement check.** After the mini-decision statement block (`:1080-1095`), insert:

   ```powershell
                   if ($module.Path -eq $coldScenarioWriter -and -not (
                           $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)\s*\(' -and $coldScenarioTables -contains $Matches[1].ToLowerInvariant())) {
                       $failures.Add(("The cold scenario store only inserts into $($coldScenarioTables -join ', ') " +
                           "(append-only); $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                   }
                   if ($null -ne $target -and $coldScenarioTables -contains $target) {
                       if ($module.Path -ne $coldScenarioWriter) {
                           $failures.Add(("Only $coldScenarioWriter writes cold scenario table '$target'; " +
                               "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                       } elseif ($line -notmatch '(?i)^INSERT\s+INTO\b' -or $line -match '(?i)\bON\s+CONFLICT\b') {
                           $failures.Add(("Cold scenario table '$target' is insert-only: no UPDATE, DELETE, TRUNCATE, " +
                               "MERGE, COPY or upsert from any module; $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                       } else {
                           $coldScenarioInsertsSeen[$target]++
                       }
                   }
   ```

5. **Anti-vacuity.** After the mini-decision anti-vacuity loop (`:1315-1320`), insert:

   ```powershell
       foreach ($table in $coldScenarioTables) {
           if ($extractorRan -and $coldScenarioInsertsSeen[$table] -lt 1) {
               $failures.Add(("Rule 8 found no INSERT INTO $table in $coldScenarioWriter, so the cold scenario insert-only " +
                   "check is vacuous. Update the check, do not delete it.")) | Out-Null
           }
       }
   ```

6. **Probe names.** After the mini-decision probe names (`:1486-1491`), insert:

   ```powershell
       # W5-01b C4: the cold scenario writer policy fails closed the same way.
       foreach ($table in $coldScenarioTables) {
           $workProbeNames += @("controls cold-scenario $table insert", "cold-scenario $table foreign insert",
               "cold-scenario $table update", "cold-scenario $table delete", "cold-scenario $table upsert",
               "cold-scenario $table owner insert unseen")
       }
       $workProbeNames += @('cold-scenario truncate')
   ```

7. **Probe corpus.** In `tools/writer_guard_probes.py`:

   - after `DECISION = f"{B}/mini_decisions/store.py"`, add `COLD_SCENARIO = f"{B}/cold_scenarios/store.py"`;
   - add one docstring `Sets:` bullet: ``- `cold-scenario <table> ...`: W5-01b C4 (migration 0032) two cold scenario tables, the same family as `decision`, owned by `cold_scenarios/store.py`; `cold-scenario truncate`; `controls cold-scenario <table> insert` must pass.``;
   - after the `decision truncate` entry, add the block below.

   The guard searches for each literal `("<name>"`, so every name is written out, never formatted.

   ```python
   # W5-01b C4 (migration 0032): the cold scenario store alone INSERTs both cold scenario tables, which no module
   # updates, deletes, upserts, truncates, merges or copies; each table keeps at least one owner INSERT.

   def _cold_scenario_only(table: str) -> str:
       return f"Cold scenario table '{table}' is insert-only"


   def _cold_scenario_unseen(table: str) -> tuple:
       return (COLD_SCENARIO, ("replace", f'"INSERT INTO {table} (', f'"SELECT * FROM {table} WHERE ('),
               f"Rule 8 found no INSERT INTO {table} in ")


   NEGATIVE += [
       ("cold-scenario cold_scenario foreign insert", FINDING, _work_foreign("cold_scenario"), "writes cold scenario table 'cold_scenario'"),
       ("cold-scenario cold_scenario update", COLD_SCENARIO, split("cold_scenario", "site_id = :s WHERE tenant_id = :i"), _cold_scenario_only("cold_scenario")),
       ("cold-scenario cold_scenario delete", COLD_SCENARIO, _work_delete("cold_scenario"), _cold_scenario_only("cold_scenario")),
       ("cold-scenario cold_scenario upsert", COLD_SCENARIO, _work_upsert("cold_scenario"), _cold_scenario_only("cold_scenario")),
       ("cold-scenario cold_scenario owner insert unseen", *_cold_scenario_unseen("cold_scenario")),
       ("cold-scenario cold_scenario_revision foreign insert", FINDING, _work_foreign("cold_scenario_revision"), "writes cold scenario table 'cold_scenario_revision'"),
       ("cold-scenario cold_scenario_revision update", COLD_SCENARIO, split("cold_scenario_revision", "site_id = :s WHERE tenant_id = :i"), _cold_scenario_only("cold_scenario_revision")),
       ("cold-scenario cold_scenario_revision delete", COLD_SCENARIO, _work_delete("cold_scenario_revision"), _cold_scenario_only("cold_scenario_revision")),
       ("cold-scenario cold_scenario_revision upsert", COLD_SCENARIO, _work_upsert("cold_scenario_revision"), _cold_scenario_only("cold_scenario_revision")),
       ("cold-scenario cold_scenario_revision owner insert unseen", *_cold_scenario_unseen("cold_scenario_revision")),
       ("cold-scenario truncate", COLD_SCENARIO, '_OPS02 = "TRUNCATE cold_scenario"\n',
        "The cold scenario store never updates, deletes, truncates, upserts or runs DDL"),
   ]
   WRITER_CONTROLS += [
       ("controls cold-scenario cold_scenario insert", COLD_SCENARIO, _work_control("cold_scenario")),
       ("controls cold-scenario cold_scenario_revision insert", COLD_SCENARIO, _work_control("cold_scenario_revision")),
   ]
   ```

8. **Store style.** Every store INSERT is one string literal beginning `"INSERT INTO <table> (`, so the owner-insert-unseen probe can find it. The store has no `ON CONFLICT` anywhere: the `$actionForbidden` line check refuses it, so idempotent replay is a SELECT followed by a caught unique violation, as in `mini_decisions/store.py`.

9. **Checks.** C4 runs `tools/check-all.ps1` and `python tools/writer_guard_probes.py --seam` on the names starting `cold-scenario` and `controls cold-scenario`, on a clean committed tree.

Lane A wiring in `main.py`:

- add `from assetops_backend.cold_scenarios.service import ColdScenarioService`, `from assetops_backend.cold_scenarios.store import PostgresColdScenarioStore` and `from assetops_backend.cold_scenarios_api import build_cold_scenarios_router`;
- after the C1 mount, add:

  ```python
      # W5-01b C4: authored cold scenarios. Writes need the two explicit decision injections; reads use the cold gate.
      cold_scenario_store = PostgresColdScenarioStore.from_url(database_url()) if cold_reads is not None else None
      if cold_scenario_store is not None:
          app.router.on_shutdown.append(cold_scenario_store.dispose)
      app.include_router(build_cold_scenarios_router(
          registry, None if cold_scenario_store is None else ColdScenarioService(cold_scenario_store, cold_reads),
          command_access=mini_decision_command_access, principal=mini_decision_principal))
  ```

`cold_scenarios` is a top-level package like `mini_decisions`, not a `$domains` entry and not an adapter layer, so `main.py` may import its store directly.

**Reconciliation with C1q (C4 basis source).**
- `ColdScenarioService(cold_scenario_store, cold_reads)` builds `ColdDepthReadService(cold_reads)`.
- It resolves the basis by calling `basis_on(c, ...)` with the `Connection` that `cold_scenario_store.transaction()` yields (the `PostgresMiniDecisionStore.transaction` pattern), inside the same transaction as the INSERTs.
- The store imports no `analytics` module and holds only its own INSERT and SELECT SQL.

## C5 — cold Scenarios, navigation and W2-F L1 (per-unit review)

Read C5, mock caps, C4 DTO, literal ledger. Files: new `frontend/src/sites/ColdScenarios.tsx`, `frontend/src/sites/coldScenariosClient.ts`, `frontend/src/sites/__tests__/coldScenarios.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/shell/SiteAnalyticsFrames.tsx`, `operatorSiteRoutes.ts`, `frontend/src/sites/ColdAssessmentViews.tsx`, `frontend/src/sites/__tests__/coldRoutes.test.tsx`, `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `frontend/docs/architecture/v69-screen-ledger.json`, `tools/checks/navigation-truthfulness.ps1`, `tools/checks/navigation-rail-fixtures.ps1`. Page: heading `Scenarios`; panel `Financial scenarios`; empty title `No scenario defined yet`; body `A scenario needs declared assumptions and an authored basis. None has been defined for this site and window.`; notice `Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.` One-row labels `Authored scenario`, `Assumptions`, `Basis`, `Defined at`, pill `Defined` or `Historical`; `Review assumptions →` expands exact basis locally. Pending notice `Underlying evidence is being reassessed; the authored scenario remains separate.` Refusal `Cold scenarios unavailable`, exact server message and `Retry`. No observed-outcome status/label and no ordinary-viewer create control. In `SiteAnalyticsFrames.FinancialsSections`, render the live cold Scenarios tab when `site_type === COLDCHAIN`; retain `<UnavailableTab label="Scenarios" />` for every other non-mini-grid Site. Replace the cold-only `Scenarios are read for mini-grid sites only.` branch with `ColdScenarios` at `/sites/{site_code}/financials/scenarios`. `siteFinancialScenariosHref` must accept/preserve `from,to,known_at,scenario_at` for cold. `$expectedTabs` retains two `Scenarios`; re-anchor the positive and negative `navigation-rail-fixtures.ps1` checks to both the live cold branch and retained fallback. Registry `(cold-scenarios,1) Financial scenarios` maps C4 list/empty; no observed-outcome technical node is resolved.

**C5 registry row.** C5 alone adds `I-W5-cold-scenario-read` and `I-W5-cold-scenario-ui` nodes (`kind:implementation`, `area:cold-chain`, `status:open`, task W5-01b). The summary panel row is `screen_id:cold-scenarios`, `panel_index:1`, `title:Financial scenarios`, `area:cold-chain`, `requires:[I-W5-cold-scenario-read,I-W5-cold-scenario-ui]`, `status:gap`, `reason:Authored stock-value context is listed without observed loss or an outcome claim.` Test `coldScenarios.test.tsx::authored_pending_historical_basis` verifies the UI and registry guard checks this row.

Fix W2-F L1 in refused cold Finding branch: `StatusBar label="Finding state"` with `Unknown` / `Confidence: Unknown` directly above `PageRefusal`; assert in `coldRoutes.test.tsx::w2f_finding_strip_confidence`. Captures at 1440/390, owned here: `cold-scenarios-empty` (C4 GET before POST), `cold-scenarios-authored` (C4 POST), `cold-scenarios-historical` (C4 correction fixture and saved pre-correction `scenario_at`), `cold-scenarios-pending` (C1 late-reading fixture plus authored row), `cold-scenarios-refused` (C4 GET with `from` later than `to`: 422 `COLD_WINDOW_INVALID`, shared capture method), `cold-finding-refused-unknown` (merged W2-F refusal test). Clocks are C4's returned watermarks; historical uses the saved pre-correction `scenario_at` and/or before-late evidence `known_at`. Expand basis in a capped 390px internal scroller (max 560px panel for one row, separate disclosure cap 360px); long UUIDs break at character boundaries and exact full values remain available. Run the W1 vocabulary scan; wrap raw source IDs with `data-vocabulary-exempt="source-reference"`. Do not run T028 vocabulary over this intentionally named `Scenarios` page. Run `tools/check-all.ps1`, focused tests, mock/app cap pairs, one W5-01b real-Postgres suite, final independent review and merge before W5-02.

**C5 readiness pass 3 (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `coldScenarios.test.tsx::states_loading_and_refusal`).**

**C5 scenario row, page and client (closure 2; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `coldScenarios.test.tsx::row_disclosure_and_client`).**
- **Page frame.** Breadcrumb `Sites › {Site name} › Financials › Scenarios`; heading `Scenarios`. The description is the existing `SITE_SCREEN_DESCRIPTIONS.scenarios` (`Financials · scenarios`), so `V69Layout.tsx` is not edited.
- **Item table.** Items render in one `DataTable` inside `Financial scenarios`, with columns `Authored scenario`, `Assumptions`, `Basis`, `Defined at`, `State` and one row per `items[]` entry in DTO order.
  - `Authored scenario`: `name`, then on a second line `code` and `revision {revision_no}`, the code inside `data-vocabulary-exempt="source-reference"`.
  - `Assumptions`: `{stock_quantity} {stock_unit} at {unit_value} {currency} per {stock_unit}`. Decimal strings are printed verbatim.
  - `Basis`: `Selected evidence through {cutoff}`, with `cutoff` formatted `YYYY-MM-DD HH:MM UTC`, then a `<button type="button" aria-expanded>` labelled `Review assumptions →`.
  - `Defined at`: `recorded_at` as `YYYY-MM-DD HH:MM UTC`.
  - `State`: a neutral `Badge` whose text comes from `scenario_state`: `DEFINED` → `Defined`, `HISTORICAL` → `Historical`.
- **`Review assumptions →` expansion.** A full-width row directly below its item, scrolled internally at 390 (360px cap). It is a `<dl>` with these terms in order, every ID in a `data-vocabulary-exempt="source-reference"` span with character breaks and one ID per line:
  - `Kind` → `STOCK_VALUE_CONTEXT`
  - `Assumptions` → each key and value, one per line: stock_quantity,stock_unit,unit_value,currency
  - `Window` → `authored_basis.from` – `authored_basis.to` (ISO, verbatim)
  - `Evidence cutoff` → `authored_basis.cutoff`
  - `Assessment revisions` → `authored_basis.assessment_revision_ids`
  - `Accepted evidence` → `{n} records`, then each `authored_basis.accepted_evidence_ids` entry
  - `Foundation revision` → `authored_basis.foundation_revision_id`
  - `Source classification` → `authored_basis.source_provenance.classification`
  - `Revision` → `revision_id`
  A null ID prints `None`.
- **Client.** `frontend/src/sites/coldScenariosClient.ts` validation; any violation is the unavailable state.
  - Top level: exact keys `schema_version` (`"cold-scenarios-1"`), `site_id`, `window` (exact `from,to,known_at,committed_watermark`), `scenario_at`, `selection` (exact `state,assessment_revision_ids,accepted_evidence_ids,source_provenance`), `items`, `next_cursor` (string or null).
  - Item: exact keys `id`, `code` (matches `^CSCN-\d{6,}$`), `revision_id`, `revision_no` (integer ≥ 1), `name` (string of 1–160 characters), `kind` (`"STOCK_VALUE_CONTEXT"`), `assumptions` (exact keys `stock_quantity,stock_unit,unit_value,currency`, all strings, `currency` matching `^[A-Z]{3}$`), `authored_basis` (exact keys `from,to,cutoff,assessment_revision_ids,accepted_evidence_ids,foundation_revision_id,source_provenance`), `recorded_at` (string), `scenario_state` (`DEFINED` or `HISTORICAL`).
  - `selection.state` is one of the five STATES.
- **Refusal heading.** `Cold scenarios unavailable`.
- **Currentness.** `selection.state` from the C4 list drives an amber `Notice` above the `Financial scenarios` panel:
  - `PENDING_RECOMPUTE` → `Underlying evidence is being reassessed; the authored scenario remains separate.`
  - `HISTORICAL` → `Read at an earlier evidence cutoff; newer committed evidence exists.`
  - `STALE_SOURCE` → `The selected source is stale for this window.`
  - `UNKNOWN` → `No selected cold assessment covers this window yet.`
  - `CURRENT` → no notice.
  The row pill stays `Defined` or `Historical` from `scenario_state`.
- **Copy.** Loading, unavailable and refusal copy follow the shared capture-method section.
- **Captures.** Producers follow the shared method, with `cold-scenarios-pending` using the late-reading sequence (`advance_late()` without running the worker, after one authored POST).
- **Depends on.** C4 merged review and C1 (selection).


## W5-01b C4/C5 pre-flight rulings (Codex Architect, 2026-10-22)

These rulings supersede conflicting C4/C5 text above and close every item in `task/W5-01b-cold-scenarios:.agent/W5-01b-phase-handoff.md`. They are design instructions, not implementation or acceptance. **Base:** W5-01a must merge to main first. Recreate/reset the no-code W5-01b branch from that merged main head, preserving its handoff, before implementation. Do not merge unmerged W5-01a into the old branch. For W6-01a Lane B overlap in `main.py`, `App.tsx`, `operatorSiteRoutes.ts`, `navigation-truthfulness.ps1` and `navigation-rail-fixtures.ps1`, rebase and preserve both domain-specific additions; run focused tests and guards. (P-G-1/2)

### C4 store and API closure

**P-C4-1: existing test ownership.** Add all 16 files below to C4. Change only a latest-head/rollback assertion from `0030_w4_mini_decisions` to `0032_w5_cold_scenarios`; retain references to 0030 as the migration under test, predecessor, filename and refusal message. Every downgrade from `head` crosses an **empty** 0032 before reaching older revisions, and rollback assertions name the actual starting head.

| File(s) | Exact edit |
| --- | --- |
| `backend/tests/mini_depth_probe.py` | `MINI_HEAD` becomes 0032; prepare empty 0032 and traverse it before 0029. |
| `backend/tests/test_s1_bindings_postgres.py`, `test_s2_evidence_ledger_postgres.py`, `test_s405_publication_postgres.py`, `test_s4_consequence_store_postgres.py`, `test_s4_evidence_consequence_work_postgres.py` | Change latest-head assertions (including evidence/consequence/work rollback lines 537 and 568) to 0032. |
| `backend/tests/test_w200_source_events_postgres.py`, `test_w201_cold_foundation_postgres.py` | Change respectively three and two latest-head/rollback assertions to 0032. |
| `backend/tests/test_w203_cold_migration_postgres.py`, `test_w204_cold_migration.py`, `test_w205a_ev_migration.py`, `test_w206_ev_migration_postgres.py`, `test_w207_ev_money_postgres.py`, `test_w401_migration_postgres.py`, `test_w402_migration_postgres.py` | Change latest-head constants `HEAD`/`UPGRADED_HEAD` to 0032; keep each older migration's target/predecessor and downgrade assertions. |
| `backend/tests/test_w403_migration_postgres.py` | Keep `HEAD = "0030_w4_mini_decisions"` for the W4 migration under test; add `LATEST_HEAD = "0032_w5_cold_scenarios"`; assert `script.get_heads() == [LATEST_HEAD]`, `script.get_revision(HEAD).down_revision == PREVIOUS`. For 0030 downgrade tests starting at head, downgrade empty 0032 to `HEAD` first; retain the 0030 catalog/refusal expectations. |

**P-C4-2/3/4/5/6.** In `tools/writer_guard_probes.py`, add `COLD_SCENARIO` beside `DECISION`; put `_cold_scenario_only`, `_cold_scenario_unseen` and the `NEGATIVE += [...]` block after `decision truncate` at ~794; put the two `WRITER_CONTROLS += [...]` entries **after** `WRITER_CONTROLS` at ~798 and `_work_control` at ~860 (after existing decision controls at ~885). The earlier step 7 whole-block placement is revoked; run `python tools/writer_guard_probes.py --seam` and prove import has no NameError. In 0032 add `cold_scenario_immutable` and `cold_scenario_revision_immutable` `BEFORE UPDATE OR DELETE` triggers using `ledger_append_only()` as 0030 does. `cold_scenario_site_order` belongs to `cold_scenario_revision(tenant_id,site_id,recorded_at DESC,id DESC)`, not the root; tie-break by `scenario_id`. Downgrade locks/counts both new tables, refuses nonempty history with `Downgrade of 0032_w5_cold_scenarios refused: cold scenario history exists`, then on empty drops triggers, index, revision, root, sequence. `test_migration_constraints` covers catalog, triggers, nonempty refusal and empty downgrade/re-upgrade. C4 writer transactions start `REPEATABLE READ` before `basis_on`; `snapshot()` starts `REPEATABLE READ READ ONLY` and obtains default `scenario_at=clock_timestamp()` once there. Retry a unique insert race by rereading the key; final serialization/store failure is 503 `DECISION_STORE_UNAVAILABLE`, never a fabricated 409.

**P-C4-7 through 14, 21.** Every C4 refusal is `{error:{code,message}}`; `cold_scenarios_api.py` owns a local mapper, including `DecisionRefused`, rather than importing private cold router helpers. Reuse `mini_decisions.model.MESSAGES` for `DECISION_*`. New message literals: `COLD_SCENARIO_INVALID` → `The cold scenario request or selected basis is invalid.`; `COLD_SCENARIO_CURSOR_INVALID` → `The cold scenario cursor is invalid.`; `COLD_SCENARIO_CURSOR_BASIS_CHANGED` → `The selected cold scenario basis changed. Start at the first page.`; `COLD_SCENARIO_IDEMPOTENCY_CONFLICT` → `This idempotency key belongs to a different cold scenario request.`; `COLD_SCENARIO_REVISION_CONFLICT` → `The cold scenario has a newer revision. Reload it before correcting.`; `COLD_LIMIT_INVALID` → `Limit must be an integer from 1 to 100.`. Add `DECISION_NOT_FOUND` 404 for unknown/malformed correction root and `DECISION_LINK_SCOPE_INVALID` 422 for a well-formed foreign predecessor. Order: authenticate, Site scope, reject unknown/duplicate query keys (`query_params.multi_items()` in this router), validate window, find Site, check disclosure; POST then requires both `from,to` (`COLD_WINDOW_INVALID` 422 if absent), checks `command_access`, service, principal/actor, body, basis, write. GET may omit both bounds and uses the gate's latest selection; one bound refuses. GET keys are exactly `from,to,known_at,scenario_at,limit,cursor`, POST `from,to,known_at`; invalid limit is `COLD_LIMIT_INVALID` 422. Add `access=` and `disclosure=` kwargs with cold-route defaults alongside `command_access=` and `principal=`. GET selection failure and POST `basis_on` read failure → `COLD_READ_UNAVAILABLE`; store snapshot/write failure and missing C4 service (GET or POST) → `DECISION_STORE_UNAVAILABLE`. Router tests cover all statuses, duplicate keys and the error envelope.

**P-C4-15 through 20, 22/23.** Trim/store `name` (1..160 Unicode characters), `stock_unit` (1..64 printable non-control characters). Decimal regex `^(?:0|[1-9][0-9]{0,17})(?:\.[0-9]{1,8})?$` and numeric >0; preserve valid input strings verbatim, reject signs, exponent, `.5`, `5.`, leading zeros and excessive digits. `currency` is `^[A-Z]{3}$` and an ISO 4217 code-list member; no coercion. One body currency requests no conversion, and the Site currency is undeclared; the earlier conversion-refusal sentence authorizes no conversion and has no C4 trigger. POST may save a nonempty selected basis in `PENDING_RECOMPUTE`, `STALE_SOURCE` or `HISTORICAL` with its actual state/cutoff; no assessment or Foundation still refuses. Use `work.canonical_json` and SHA-256. Create hash input is `{command:<validated body excluding idempotency_key>,site_id:<UUID>,window:{from:<resolved>,to:<resolved>,cutoff:<resolved>}}`; revision-1 `payload_sha256` equals it. Correction hash includes corrected body, root ID and resolved same root window/cutoff. `basis_sha256=sha256(canonical_json(authored_basis))`. Key replay reads stored canonical input and prior resolved cutoff **before** resolving a new basis, returns 200 even if that basis no longer resolves; changed explicit cutoff/body conflicts. Omitted `known_at` on a new request resolves to the selected watermark. A C4 in-process seed test injects `DecisionPrincipal`/`GRANT_PREFIX`; the served `lab_app` host remains read-only. It GETs the list after first POST and saves that response's `scenario_at`, then corrects later; no write DTO clock is invented. List orders selected revisions by `(recorded_at DESC,id DESC,scenario_id)` and filters root window plus `authored_basis.cutoff <= known_at` in parameterized SQL; malformed persisted basis is 503. Reuse mini cursor codec with C4 code translation; bind tenant/Site, selected window and digest, `known_at`, `scenario_at`, limit and last tuple. Omitted page-two clocks inherit cursor clocks; explicit mismatch is 409 basis changed. Test replay after evidence advance, hashes, 51-row paging, historical correction and malformed basis.

### C5 mock and UI closure

**P-C5-1 through 5.** The `cold-scenarios` mock (`frontend/mockups/v69/index.html:859,861`) controls the Site-name h1, `Financials · scenarios (placeholder)` description, `Financial scenarios` panel with subtitle `Placeholder · to be designed with the owner`, evidence-icon empty block with h3 `No scenario defined yet` and paragraph `A scenario compares a declared what-if with the measured case, for example a different stop setting, stock value or tariff. None has been defined for this site.`, then the existing exact `Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.` notice in **blue**. Add `frontend/src/ui/V69Layout.tsx` to C5 and restore its scenario description. `Scenarios` is breadcrumb/tab, never h1. Amber currentness notice comes before the panel when needed; blue notice after it. Restore exact empty form/copy; no extra status strip. **MOCK DEVIATION — authored rows:** the mock panel has only an empty block; real C4 definitions replace that block with the card's table, disclosure and pager inside the same titled/subtitled panel. Retaining only the empty mock hides real definitions; inventing comparison values misstates evidence. **MOCK DEVIATION — currentness notice:** the mock only has its blue closing notice; pending/stale/historical selection adds the amber notice above the panel so an old basis is visible. Hiding currentness or burying it in empty copy would mislead on populated rows. The earlier authored-row/pending deviations are consolidated here; no other mock departure is authorized.

**P-C5-6/7/8.** Add `frontend/src/test/productVocabulary.json`, `frontend/src/test/productVocabulary.ts` and `frontend/src/sites/__tests__/coldSiteViews.test.tsx` to C5. The generic W1 set includes T028's `scenario`/`scenarios`, so merely skipping T028 does not work. Extend the JSON with `screenGlosses` entries keyed by screen ID and exact string, and update `scanProductVocabulary` in `productVocabulary.ts` to remove only exact gloss matches for its supplied screen ID before applying the existing T028+W1 scan; keep existing global glosses and T028 terms unchanged. The allowed screen IDs are `cold-scenarios`, `cold-financials`, `cold-assumptions`, and their allowed texts are `Scenarios`, `Financial scenarios`, `No scenario defined yet`, the exact mock empty paragraph and blue notice, `Authored scenario`, `Cold scenarios unavailable`, the loading/network/malformed-200 C5 strings. Do not filter violations in tests or exempt whole panels. The stocked `coldSiteViews.test.tsx` W1 scan must accept the now-live Scenarios link using that screen glossary and still fail on an unglossed banned word; assert its live href. `coldScenarios.test.tsx` scans the full page with `set:"w1"`. Print `STOCK_VALUE_CONTEXT` as `Stock value context`, source classifications as plain words (`Unknown`, `Mixed`, etc.), and assumption keys as `Stock quantity`, `Stock unit`, `Unit value`, `Currency`. Only actual UUIDs/codes as source IDs use `data-vocabulary-exempt="source-reference"`.

**P-C5-9 through 16.** Add `frontend/src/sites/coldScenarios.css` for scoped mock empty icon, expansion row, wrapping and 390 scroller; import it from `ColdScenarios.tsx`. Keep `App.tsx` Lab `coldScenarios?: ColdScenarioChoiceClient`; Site list prop is `coldScenarioList?: ColdScenariosClient`, default `HttpColdScenariosClient` from `sites/coldScenariosClient.ts`. `siteFinancialScenariosHref(siteId, query?: {from?:string;to?:string;known_at?:string;scenario_at?:string})` adds defined encoded keys in that order, leaving one-argument mini callers intact. Cold Overview/Assumptions pass `scenarios="live"` and carry `from,to,known_at` to Scenarios; Scenarios back-links carry those three and drop authored-only `scenario_at`. Non-cold/non-mini fallback `Scenarios are read for mini-grid sites only.` stays; EV's unavailable slot stays. Guard anchors in `navigation-truthfulness.ps1`: cold branch `site_type === "COLDCHAIN"`, `scenarios="live"`, `<ColdScenarios`; non-cold fallback `<UnavailableTab label="Scenarios" />`. In `navigation-rail-fixtures.ps1`, positive fixture removes `<ColdScenarios` and expects `the cold Financials Scenarios destination is live`; negative fixture removes fallback unavailable literal and expects `the W1-plus-W2 inventory is exactly`; anchor to branches so another occurrence cannot pass. Keep `$expectedTabs`' two Scenarios. Show `SelectedWindowBar` (`from,to,known_at`) and `Scenarios created through {scenario_at UTC}`; refused query uses `RequestedWindowBar`. Validator requires lowercase UUIDs for Site/item/revision/selected arrays/nullable Foundation, UTC ISO instants for window/cutoff/scenario/recorded clocks, exact provenance object with C1 keys and string classification, sorted/deduped arrays, and closed keys throughout. `known_at`/cutoff may be null only on an unavailable selection; do not format null as a date. Malformed 200 is unavailable. Add client tests for each type.

**P-C5-12/19/20/22 detail.** Render `<nav aria-label="Scenario pages">` after the table: `First page`, `Next`, `{page} of {total pages}`; `Next` uses `next_cursor`, `First page` clears it, absent next disables it. Test 51 rows. Expansion lines are `Stock quantity: {value}` etc.; `Accepted evidence` is `1 record` or `{n} records`; `Window` is `{from} – {to}`. UUIDs wrap, exact values stay accessible. Internal disclosure scroll max-height 360px **at 390 only**; closed one-row/empty panel cap stays 430/560px (1440/390), expanded 1440 one-row cap 650px. Capture expanded authored and historical at both widths and check no document overflow. `Retry` is a button that refetches the same URL, matching cold siblings; the ledger's word "link" describes its action.

**P-C5-17/18/21.** In refused Finding branch of `ColdAssessmentViews.tsx`, insert `<StatusBar label="Finding state"><Badge tone="neutral">Unknown</Badge><span>Confidence: Unknown</span><span>{siteName}</span></StatusBar>` directly above `PageRefusal`; use `RequestedWindowBar` for the invalid period. `coldRoutes.test.tsx::w2f_finding_strip_confidence` asserts order and no invented loaded state. `cold-finding-refused-unknown` capture is served GET of a real imported W2 Finding detail for `COLD-LAB-001` with `from=2026-10-06T20:05:00Z&to=2026-10-06T19:00:00Z`, returning 422 `COLD_WINDOW_INVALID`; the merged jsdom test alone is not a producer. `coldScenarios.test.tsx::authored_pending_historical_basis` tests UI, while `check_v69_dependency_registry.cjs` and `check_v69_ledger.py` check registry/ledger; vitest need not parse JSON. C5 focused proof is those tests, `coldSiteViews.test.tsx`, `coldRoutes.test.tsx`, both navigation guards and 1440/390 captures.

### P-ID closure table

| IDs | Closing paragraph above |
| --- | --- |
| P-G-1, P-G-2 | Base and Lane B opening paragraph. |
| P-C4-1 | Existing test table (all 16 files and downgrade paths). |
| P-C4-2, P-C4-3, P-C4-4, P-C4-5, P-C4-6 | C4 guard/migration/snapshot paragraph. |
| P-C4-7, P-C4-8, P-C4-9, P-C4-10, P-C4-11, P-C4-12, P-C4-13, P-C4-14, P-C4-21 | C4 refusal, messages, access, keys and 503 paragraph. |
| P-C4-15, P-C4-16, P-C4-17, P-C4-18, P-C4-19, P-C4-20, P-C4-22, P-C4-23 | C4 canonical command/list/producer paragraph. |
| P-C5-1, P-C5-2, P-C5-3, P-C5-4, P-C5-5 | C5 mock paragraph. |
| P-C5-6, P-C5-7, P-C5-8 | C5 vocabulary paragraph. |
| P-C5-9, P-C5-10, P-C5-11, P-C5-13, P-C5-14, P-C5-15, P-C5-16 | C5 route/guard/client paragraph. |
| P-C5-12, P-C5-19, P-C5-20, P-C5-22 | C5 pager/capture paragraph. |
| P-C5-17, P-C5-18, P-C5-21 | C5 W2-F/registry paragraph. |

No P-ID remains open. C4/C5 code, per-unit review, captures and owner acceptance remain future work under the task gates.

### Executable registry and ledger amendment

Apply these exact JSON objects to the registry in the named unit only. Insert each node once; append each panel once. For the three cold screens, set `registry_dependencies.product_node_id` to `P-cold-area` and `registry_dependencies.node_ids` to the ordered unique concatenation of that screen’s panel `requires` arrays. C3 owns cooling and cold-health ledger edits; C5 owns cold-scenarios. Status remains `gap` and nodes remain `open` until independent review.

**C3 — registry nodes**

```json
[
  {
    "id": "I-W5-cold-depth-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W5-01a",
    "acceptance_target": "Reviewed selected read with exact evidence lineage and bounded unknown states."
  },
  {
    "id": "I-W5-cold-depth-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections",
      "I-W5-cold-depth-read"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-01a",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps, 1440/390 captures and preserved gateway panel where applicable."
  }
]
```

**C3 — panel rows**

```json
[
  {
    "screen_id": "cooling",
    "panel_index": 1,
    "title": "Recovery curves",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "W5-01a selected first steps do not establish an ordered recovery curve."
  },
  {
    "screen_id": "cooling",
    "panel_index": 2,
    "title": "Context normalization",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Ambient is not selected by the W2 cooling assessment; loading and defrost roles are absent, so those context rows show Unknown."
  },
  {
    "screen_id": "cooling",
    "panel_index": 3,
    "title": "Next best evidence",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Evidence actions are bounded to existing Backup and Temperature destinations."
  },
  {
    "screen_id": "cold-health",
    "panel_index": 1,
    "title": "Condition and evidence",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Selected start and probe observations do not establish physical equipment health."
  }
]
```

C3 ledger `cooling`: `registry_dependencies` = {"product_node_id": "P-cold-area", "node_ids": ["I-W5-cold-depth-read", "I-W5-cold-depth-ui", "D-cold-domain"]}.

C3 ledger `cold-health`: `registry_dependencies` = {"product_node_id": "P-cold-area", "node_ids": ["I-W5-cold-depth-read", "I-W5-cold-depth-ui", "D-cold-domain"]}.

**C5 — registry nodes**

```json
[
  {
    "id": "I-W5-cold-scenario-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W5-01b",
    "acceptance_target": "Reviewed selected read with exact evidence lineage and bounded unknown states."
  },
  {
    "id": "I-W5-cold-scenario-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections",
      "I-W5-cold-scenario-read"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-01b",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps, 1440/390 captures and preserved gateway panel where applicable."
  }
]
```

**C5 — panel rows**

```json
[
  {
    "screen_id": "cold-scenarios",
    "panel_index": 1,
    "title": "Financial scenarios",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-scenario-read",
      "I-W5-cold-scenario-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Authored stock-value context is listed without observed loss or an outcome claim."
  }
]
```

C5 ledger `cold-scenarios`: `registry_dependencies` = {"product_node_id": "P-cold-area", "node_ids": ["I-W5-cold-scenario-read", "I-W5-cold-scenario-ui", "D-cold-domain"]}.

## Readiness closure

| Review item | Closing artifact location |
| --- | --- |
| 1 | C1 producer clock |
| 2 | Shared selected read and C1 links |
| 3 | C1/C2 file lists |
| 4 | C3/C5 registry rows |
| 5 | C1 context table |
| 6 | C1 derivation table |
| 7 | Shared selected read provenance |
| 8 | C2 state matrix |
| 9 | C2 breadcrumb rule |
| 10 | C2 live refusal capture |
| 11 | C2 worst-content cap |
| 12 | C2 navigation fixture |
| 13 | C3 condition matrix |
| 14 | C3 Health composition |
| 15 | C3 table deviation |
| 16 | C4 persisted schema |
| 17 | C4 POST and refusals |
| 18 | C4 list and historical predicate |
| 19 | C5 cold Scenarios branch |
| 20 | C5 query preservation |
| 21 | C5 fixture anchors |
| 22 | C5 vocabulary rule |
| 23 | C5 expanded-basis cap |
| 24 | C5 Finding strip test |
| 25 | C4 one-run card |
| 26 | Shared literal ledger |
| 27 | Gate and guards |
| R1 (review 4) | C3/C5 executable node, panel and ledger JSON below; applied together to a scratch registry and the dependency checker passed on 2026-10-22. |
| R2 | C3 keeps the S7 gateway panel and live Foundation link, names tests and composed page caps. |
| R3 | C4 POST and refusal table use merged 422. |
| R4 | C4 revision-1 window rule and cross-window correction refusal. |
| R5 | C1 accepted door-event ledger read and optional ambient-role distinction. |
| R6 | Health enum includes LIMITED; C3 covers zero, one and two selected probes. |
| R7 | C2/C3 client edit ownership and C3/C5 single node creation. |
| C1q-Q1 (payload keys) | Shared selected read top-level key order; C1 Cooling payload key `cooling`, Health key `health`. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively (rows C1q-\*).* |
| C1q-Q2 (context row keys) | C1 Cooling payload table: `label/state/evidence_ids/duration_seconds` on every row; new `policy_high_deg_c`. |
| C1q-Q3 (several door pairs) | C1 derivation table pairing rule: integer sum, all paired IDs. |
| C1q-Q4 (missing point dropped) | Decided by spec lines 19/53; confirmed, no change. |
| C1q-Q5 (cited IDs) | Shared selected read: `accepted_evidence_ids` = cited union, may include a ledger-absent ID; row/point IDs ledger-present. |
| C1q-Q6 (`cooling_recovery.state`; L4) | C1 derivation table wording and "C1 public W2 helper" `cold_site_reads.cooling_response_state`. |
| C1q-Q7 (Health read) | C1 Health read: `ColdReadService.foundation_on`, asset/component literals, three-row literal table, `NOT_CONFIGURED` predicate. |
| C1q-Q8–Q12 (L1, L2, L3, I1, I2) | C1 follow-up fixes and exact test names. |
| C1q-C2 | C2 DTO, label and link sources (`policy_high_deg_c`, `coldUiHref` `cooling`). |
| C1q-C3 | C3 Health DTO rendering, card values, Asset cell, empty rule, `#site-health-sources-heading`, `coldSiteViews.tsx` in file list. |
| C1q-C4 | C4 basis source read `ColdDepthReadService.basis_on`; `cold_depth.py` in C4 file list. |
| C1q-C5 | Checked: C5 consumes the literal C4 list DTO and existing `siteFinancialScenariosHref`; no unnamed read, role selection, key or guard file found; no change. |
| A1Q-W5S-1 | C1 builder delta and derivation table: door events read through `ColdReadService.accepted_on` (already so in `703807cf`), and the rule-2, rule-8 and declaration limits on `cold_depth.py`. C1q Q7 already covers the `foundation_on` adapter placement. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
| A1Q-W5S-2 | C1 composition paragraph: the `main.py` mount in `703807cf` is the literal wiring; no change. |
| A1Q-W5S-3 | C4 guard and composition ownership: rule-8 blocks in `configuration-persistence.ps1` and the probe corpus in `writer_guard_probes.py`; both files are in the C4 list. |
| A1Q-W5S-4 | C4 `main.py` store and router wiring with the decision injections, reconciled with C1q `basis_on` through `cold_scenario_store.transaction()`. |
| A1Q-W5S-9/10/11 | HTTP-scan token sentences in C1 and C4; the DataTable/svg sentence in "Measured mock and content caps" (applies to C2, C3 and C5); shared guard-file serialization in the gate section. |
| A1Q-W5S-5..8 | W5-03 only; folded into `.agent/W5-03-build-spec.md`. |
| C1q2-Q13 (two declared probes, no selection) | C1 `foundation_on` `chamber_probe_asset_id` (topology SIGNAL edge from `COLD_ROOM`) and the Temperature sensing `asset_id` fallback order; assertions in `test_health_not_configured` and `test_health_rows`. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
| RP3-C2 (7) | C2 readiness pass 3: Q-C2-1 routes file, Q-C2-2 context table, Q-C2-3 no-svg recovery table, Q-C2-4 currentness notice, frame/nav/guard literals, `V69Layout.tsx` description, refused capture 422. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
| RP3-C3 (4) | C3 readiness pass 3: `coldSiteRoutes.tsx` `health`, currentness notice, unknown/refused capture producers, loading/unavailable copy. |
| RP3-C5 (3) | C5 readiness pass 3: currentness notices for all five states, refused/pending capture producers, loading/unavailable copy. |
| RP3-shared | "Capture producer method, loading and unavailable copy" section before C1. |
| CL2-1 (C3) | C3 condition notice literal. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
| CL2-2/3 (C5) | C5 scenario row, page and client: DataTable columns and cells, pill source, expansion content, `coldScenariosClient` validator, breadcrumb and existing `SITE_SCREEN_DESCRIPTIONS.scenarios`. |
| CL3-C2 (Q-C2-5..7) | C2 build rulings: `coldRoutes.test.tsx` literal edit and file-list entry, Site-name heading (ledger corrected), empty-capture window. *Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively.* |
## Codex retrospective of Claude Architect rulings (2026-10-22)

Checked against `frontend/mockups/v69/index.html` (`cooling`, `cold-health`, `cold-scenarios`), `screen-manifest.json`, the selected-read code and the technical design. These rulings supersede conflicting Claude C2/C3 rendering instructions above; the evidence and claim limits remain binding.

| Ruling | Verdict and reason | Alternative / exact correction |
| --- | --- | --- |
| C2 Q-C2-2 `Match` to `Status` | **RESTORE TO MOCK.** The mock's `Context normalization` table has `Factor / Evidence / Match`. The heading can remain even when no match has been established; the cells carry the claim limit. | In C2 `frontend/src/sites/ColdCooling.tsx`, render the third `DataTable` heading as literal `Match`, replacing `Status`. With `comparison_state=CONTEXT_MISSING`, every Match cell reads `Not established`, regardless of that factor's `Observed` or `Unknown` evidence state; the Evidence column still reports the selected observation. Never render mock `Matched` without a supported comparator. Update `frontend/src/sites/__tests__/coldDepth.test.tsx::cooling_panels` to assert the heading, all five `Not established` cells and no unsupported `Matched`; recapture C2 limited/empty/pending/historical at 1440/390 and rerun the focused/navigation tests. No guard registration or C1 wire change is needed for this heading. |
| C2 Q-C2-3 Recovery curves to `DataTable` | **RESTORE TO MOCK**, subject to the selected-data limit. The mock gives this panel a chart; rule 5 constrains the module drawing `<svg>`, not whether a chart may exist. A table as the sole graphic loses the screen's visual structure. | Rebuild delta for C2 at `2812d7aa`: add `frontend/src/sites/coldDepthGraphics.tsx`, `frontend/src/ui/primitives.css` and `tools/checks/shell-overflow.ps1` to C2's Lane A file list. In rule 5 register `coldDepthGraphics.tsx` as the sole owner of its `<svg>`, require an actual `.cold-depth-graphic__scroll` wrapper in that module, and verify that selector declares horizontal overflow containment in `primitives.css`, as the existing assessment graphic check does; retain all existing allowlist checks. `ColdCooling.tsx` renders `Recovery curves` with the new graphic and the existing selected-point table as its accessible source detail. The present C1 `selected_points` have time and role but no temperature values: place their unconnected, labelled marks on categorical compressor/probe lanes, never on a numeric °C axis. Draw temperature curves only when a future selected read provides ordered accepted numeric recovery series. The current W2 producer therefore shows the chart frame and selected marks with `No accepted recovery sequence in this window.` and no mock 36/42-minute or +17% values; the no-point case has an empty frame. Keep `DataTable` for the evidence detail and `Context normalization`. Update `coldDepth.test.tsx::cooling_panels` to assert graphic, mark labels, empty state and no connecting path for the W2 fixture; update C2 `cooling-limited`, `cooling-empty`, `cooling-pending`, `cooling-historical` and 1440/390 captures and cap measurements. C3's registry `cooling:1` reason must describe selected marks and absent comparable curve, not a table-only panel. Re-run `tools/check-all.ps1` and the C2 focused/navigation tests before C2 re-review. |
| C3 condition notice | **KEEP — MOCK DEVIATION.** The mock has condition cards and a table but no explicit condition ceiling; selected fault/start observations otherwise read as physical diagnoses. | A panel footnote would be closer in placement but less visible beside the S7 gateway panel. Keep the exact amber sentence in C3 and its test/capture. |

**Correctness disposition.** Confirm C1 Q1–Q13 and review-Low fixes: selected IDs, null recovery duration, public `cooling_response_state`, single effective Foundation and `foundation_on` adapter preserve the technical design's selected-evidence and snapshot boundaries. Confirm C2 Q-C2-1, Q-C2-4 through Q-C2-7, C3 state/fragment, C4 `basis_on`, C5 root-window/cutoff semantics and the A1Q guard/composition sweep. The chart correction above is the only C2 rebuild; do not synthesize a recovery curve from isolated points. The C2 currentness notice is a **KEEP — MOCK DEVIATION** for pending/stale/historical/unknown selection, because the mock has no live cutoff states; alternative is a small inline status note, but the visible amber notice is consistent with selected-read semantics. The same applies to C3 currentness. C5 authored scenario row and notice copy are **KEEP — MOCK DEVIATION** where no mock literal covers a selected pending state; replacing them with illustrative mock values would misstate stored authorship. No other W5-01 Claude ruling needs a code correction.

## C3 rulings (Q-C3-1..4)

These rulings amend `D-2026-10-22-w5-01-w5-03-buildspec` and supersede conflicting C3 composition and file-list wording above. Mock check: `frontend/mockups/v69/index.html` renders the `cold-health` branch with three `Backup generator` / `Cooling plant` / `Temperature sensing` cards and the single `Condition and evidence` panel (`Asset` / `Supported assessment` / `Next evidence`). `screen-manifest.json` gives `cold-health` the Site name as title and `Health` as section. The mock's separate `health` (mini-grid) screen has `Physical asset condition`, `Data sources · data quality, not equipment condition`, and a blue notice; those are not the cold screen's panel set.

1. **Q-C3-1 — extract only the S7 source panel.** Add `frontend/src/sites/SiteHealth.tsx` to C3's **Lane A** file list. Its exact export is `SiteHealthSources({ siteId, client, selectedGateway }: { siteId: string; client: HealthClient; selectedGateway: string | null })`. It calls the existing `client.getSourceHealth(siteId)` through `useRead` with the same `health:${siteId}` key and renders only the existing `Data sources · data quality, not equipment condition` `Panel`, with heading ID `site-health-sources-heading`, existing description, `SourcesBody` and `HealthGap` refusal (including the same `HEALTH_TEXTS` and exact references). On loading, keep that titled panel and show `Loading the site's gateway contact.` within it; a source refusal stays in that panel. Extract a private source-panel renderer receiving the read so `SiteHealth` can keep its current source and battery reads, loading behavior, strip, battery panel and blue notice unchanged on non-cold Sites. In `SiteHealthFrames.tsx`, route only COLDCHAIN to `ColdHealthDepth` followed immediately by this `SiteHealthSources` after the amber condition notice, inside the existing `HealthLinksContext.Provider`; pass the same `health` client and `gateway` search value. Do not mount `SiteHealth` for COLDCHAIN. The cold page therefore has **no** S7 battery `ConditionStrip`, `Physical asset condition` panel, or blue battery/gateway notice. It does retain the S7 source read's independent server-receipt clock and the exact `#site-health-sources-heading` target. Preserve existing non-cold S7 tests, and assert the cold panel order and absence of those three battery-specific elements in `siteHealthBoundary.test.tsx` or `coldHealthDepth.test.tsx`.

   **MOCK DEVIATION — added Data sources panel.** The cold mock ends after `Condition and evidence`; its Data sources panel belongs to `cold-evidence`, while mini-grid `health` has a separate source panel. The C3 contract retains S7 source health here to satisfy the live cold Foundation `Health › Data sources →` destination and keep gateway contact visibly separate from physical condition. A link to cold Evidence would preserve the cold Health panel set but would lead to a different selected-evidence read; rendering the entire S7 `SiteHealth` would add a battery strip/panel and blue battery notice with no cold condition basis. Keep the source panel alone as this explicit addition. The pre-existing amber condition notice and currentness notice remain the separately labelled C3 mock deviations in the retrospective.

2. **Q-C3-2 — heading.** Confirm the frame's `SitePageHeader` Site-name h1, matching the `cold-health` mock title `GreenHarvest Cold Room` (runtime: the selected Site's `display_name`). `Health` is the breadcrumb end and active Site tab, matching the manifest's section. The shared ledger's `heading Health` names the section, not an instruction to replace the Site-name h1. No `Health` h1 is added.

3. **Q-C3-3 — live Health route assertion.** Add `frontend/src/sites/__tests__/coldDepth.test.tsx` to C3's **Lane A** list. In `cooling_nav_and_routes`, replace the old test name with `coldUiHref maps the cooling and Health API links with their exact queries`, and replace its last assertion literally with:

   ```tsx
   expect(coldUiHref(`/api/sites/${SITE_CODE}/cold/health?${Q}`, routes)).toBe(`/sites/${SITE_CODE}/health?${Q}`);
   ```

   Keep the existing Cooling assertions and their query-preservation check.

4. **Q-C3-4 — cold Foundation link assertion.** Add `frontend/src/sites/__tests__/coldFoundation.test.tsx` to C3's **Lane A** list. Its existing `renderCold` fixture actually renders the gateway panel; add this literal test inside the existing cold Foundation route suite:

   ```tsx
   it("links the cold gateway panel to Health Data sources", async () => {
     renderCold(`${BASE}/readiness`, loaded(STOCKED));
     await settledScreen();
     const link = Array.from(panelTitled("Gateway status · edge-cold-001").querySelectorAll("a"))
       .find((a) => a.textContent === "Health › Data sources →");
     expect(link?.getAttribute("href")).toBe("/sites/COLD-001/health#site-health-sources-heading");
   });
   ```

   This checks the actual readiness link and existing source heading ID. `coldSiteViews.test.tsx` remains on C3's list for its own route and composition assertions.

## C3 rulings (Q-C3-5, mock differences)

These rulings amend `D-2026-10-22-w5-01-w5-03-buildspec` and supersede conflicting C3 mobile Asset-cell and card wording. Mock check: `frontend/mockups/v69/index.html`, `cold-health`, shows compact `GEN-CR-01` and `CMP-003` Asset cells in `Condition and evidence`, not four-line UUIDs. Its Backup generator card has an amber top border, a body-colour value and a separate `View detail →` link. Mock CSS `.assessment .metric-value` sets the value to 17 px at 1440 and 390.

1. **Q-C3-5 — RESTORE TO MOCK.** Keep the condition-panel cap at **330/430 px (1440/390)**. Add `frontend/src/ui/primitives.css` to C3's Lane A file list. In `frontend/src/sites/ColdHealthDepth.tsx`, set `className="cold-health-condition"` on the `Condition and evidence` `Panel`. Keep `DataTable` and the complete selected Foundation Asset label and source-reference UUID. Put the UUID on its own line without truncation. Add this scoped CSS to `primitives.css`:

   ```css
   @media (max-width: 480px) {
     .cold-health-condition .data-table { min-width: 840px; }
     .cold-health-condition .data-table th:first-child { position: sticky; left: 0; z-index: 1; min-width: 240px; background: var(--surface-raised); }
     .cold-health-condition .data-table thead th:first-child { z-index: 2; background: var(--surface-sunken); }
     .cold-health-condition [data-health-asset-id] { display: block; white-space: nowrap; overflow-wrap: normal; word-break: normal; font-size: 10px; }
   }
   ```

   The existing `.data-table__scroll` owns horizontal overflow; the Asset column stays visible while the other columns scroll. This replaces the earlier instruction to break Asset UUIDs at character boundaries. Raising the cap to fit four-line UUIDs would retain the mock difference. Recheck all five 390 captures, including the three-row unknown case, against **≤430 px**, with no document overflow or clipped ID; retain the 1440 **≤330 px** cap. Assert the panel class and complete ID in `frontend/src/sites/__tests__/coldHealthDepth.test.tsx`.

2. **Backup border and value — RESTORE TO MOCK.** In `ColdHealthDepth.tsx`, replace the card's `word` prop with `assessment`, keeping `tone={row.condition_state === "NEEDS_INVESTIGATION" ? "amber" : undefined}`. The existing `.v69-metric--assessment.v69-metric--amber` gives the Backup card a 3 px amber top border, and `.v69-metric--assessment .v69-metric__value` keeps its value body-coloured. Apply `assessment` to all three cards so the neutral cards have the mock's neutral assessment border.

3. **Card link — RESTORE TO MOCK.** The `cold-health` mock has a plain card label and a separate `View detail →` link below the note. Add `frontend/src/ui/V69Layout.tsx` and `frontend/src/ui/primitives.css` to C3's Lane A file list. Extend `MetricCardProps` with optional `link?: ReactNode`; render it after the note as `<div className="v69-metric__link">{link}</div>` when provided. Add `.v69-metric__link { font-size: 10px; margin-top: 10px; }` to `primitives.css`. In `ColdHealthDepth.tsx` pass `label={row.label}` and `link={href === null ? undefined : <Link to={href}>View detail →</Link>}`. A null destination has no link. Keep `coldUiHref` query preservation and assert the label is not an anchor while the detail link has the mapped destination.

4. **Value size — RESTORE TO MOCK.** The mock's assessment state word is **17 px**; a 24/27 px value would depart from the actual `.assessment .metric-value` rule. The `assessment` prop above implies the shared 17 px word rule. Remove standalone `word`, do not enlarge the state words, and assert all three cards use `v69-metric--assessment` without a C3 size override.

5. **Registry reasons — literal Architect copy.** In `frontend/docs/architecture/v69-dependency-registry-pilot.json`, the exact `reason` for `(cooling,1) Recovery curves` is `Selected compressor and probe observations are drawn as unconnected marks on categorical lanes; no ordered accepted recovery series exists, so no comparable recovery curve is drawn.` The exact `reason` for `(cooling,2) Context normalization` is `Ambient is not selected by the W2 cooling assessment and loading and defrost roles are absent; with no supported comparator every Match cell reads Not established.` The builder's current strings match these literals; retain them verbatim. Neither reason claims a physical condition or a measured comparison.

## C3 rulings (Q-C3-6, review H1/M1)

These rulings amend `D-2026-10-22-w5-01-w5-03-buildspec` and supersede Q-C3-5 rulings 1, 2 and 4 where they conflict. The checked mock is `frontend/mockups/v69/index.html`: `metric()` adds `assessment` only for a nonempty tone; the `cold-health` call gives `amber` only to `Backup generator`. Its `Condition and evidence` table has the three visible headings `Asset`, `Supported assessment`, `Next evidence` and compact Asset codes `GEN-CR-01` and `CMP-003`.

1. **H1 — RESTORE TO MOCK.** In `frontend/src/sites/ColdHealthDepth.tsx`, replace the unconditional `assessment` prop with `assessment={row.condition_state === "NEEDS_INVESTIGATION"}`. Keep the existing `tone={row.condition_state === "NEEDS_INVESTIGATION" ? "amber" : undefined}` and omit `word` on every card. The predicate follows the selected row's condition state: the backed failed-start row is `NEEDS_INVESTIGATION`, while `UNKNOWN`, `LIMITED` and `NOT_CONFIGURED` carry no tone. The shared `MetricCard` then gives the Backup card its 3 px amber border and 17 px body-colour value; Cooling plant and Temperature sensing remain plain cards with no top border and a 27 px value. This also applies when a different row is `NEEDS_INVESTIGATION`: styling follows the state, not the asset kind. No new CSS or `MetricCard` API is needed. In `frontend/src/sites/__tests__/coldHealthDepth.test.tsx` `condition_matrix`, replace the all-three assessment assertion: assert Backup has `v69-metric--assessment v69-metric--amber`; assert Cooling and Sensing lack `v69-metric--assessment` and every tone class; retain the no-inline-style assertion. In the state matrix, assert an `UNKNOWN` or `NOT_CONFIGURED` Backup lacks assessment, and any `NEEDS_INVESTIGATION` row has assessment. The existing shared CSS is the 17/27 px source; a rendered 1440/390 measurement must confirm it.

2. **M1 — RESTORE TO MOCK.** The Q-C3-5 `min-width: 840px`, sticky 240 px Asset column and one-line UUID contradict the 390 mock because they put the two claim columns off-screen. Replace that mobile rule in `frontend/src/ui/primitives.css`; keep the `DataTable`, its three headings, the selected Foundation asset code and the complete source-reference UUID. In `ColdHealthDepth.tsx` `AssetCell`, for a matching `row.asset_id` render the current desktop name and UUID in `<span className="cold-health-asset__desktop">`, plus `<span className="cold-health-asset__mobile"><span data-health-asset-code>{match.asset_code}</span><details><summary>Full ID</summary><code data-vocabulary-exempt="source-reference" data-health-asset-id>{row.asset_id}</code></details></span>`. Use the actual selected `asset_code`, never an inferred code from the UUID; for a missing match, show the full ID as the mobile primary text with wrapping, and for null `asset_id` use the existing asset-name or row-label fallback with wrapping. Keep the desktop UUID `data-health-asset-id` as well. The mobile disclosure is keyboard operable and exposes the full ID on demand. Add this literal scoped mobile CSS, replacing Q-C3-5's mobile block:

   ```css
   .cold-health-asset__mobile { display: none; }
   @media (max-width: 480px) {
     .cold-health-condition .data-table { min-width: 0; width: 100%; table-layout: fixed; }
     .cold-health-condition .data-table th,
     .cold-health-condition .data-table td { padding: 7px 5px; overflow-wrap: anywhere; word-break: normal; }
     .cold-health-condition .data-table thead th { white-space: normal; font-size: 9px; }
     .cold-health-condition .data-table tr > :first-child { width: 27%; position: static; min-width: 0; }
     .cold-health-condition .data-table tr > :nth-child(2) { width: 36.5%; }
     .cold-health-condition .data-table tr > :nth-child(3) { width: 36.5%; }
     .cold-health-asset__desktop { display: none; }
     .cold-health-asset__mobile { display: block; }
     .cold-health-asset__mobile [data-health-asset-code] { font-size: 10px; font-weight: 650; }
     .cold-health-asset__mobile details { margin-top: 4px; font-size: 10px; font-weight: 400; }
     .cold-health-asset__mobile code { display: block; white-space: normal; overflow-wrap: anywhere; font-size: 10px; }
   }
   ```

   In `coldHealthDepth.test.tsx`, change the Asset-cell assertion to check the selected code and both full-ID copies, open `Full ID` and assert its code equals the UUID; cover the missing-match and null-ID fallbacks. Assert the CSS no longer has the 840/240 px mobile rule. At 390, a browser layout assertion must show all three header boxes and each row's assessment and next-evidence boxes intersect the table's visible viewport without horizontal scrolling, with the disclosure closed. Recapture all five C3 app states at 1440 and 390 after H1/M1. Compare them with the mock and remeasure cards **≤200/430 px**, Condition and evidence **≤330/430 px**, Data sources **≤700/800 px**, page **≤1900/2350 px** (1440/390); verify no document overflow, clipping or ellipsis. If the three claim columns or caps fail, revise the scoped layout and recapture before C3 re-review. The disclosure-open view may grow beyond the closed-state cap because the user explicitly requested the full identifier.
