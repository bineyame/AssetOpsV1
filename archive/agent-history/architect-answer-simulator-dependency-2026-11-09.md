# Architect answer: how far ingestion and intelligence depend on the simulator (2026-11-09)

Owner question (verbatim, `.agent/owner-question-simulator-dependency-2026-11-09.md`): "how much is the canonical data
ingestion and subsequent intelligence  tied/or not to the simulator in terms of dependency .let architect answer based
on actual implemented code"

Produced by the Architect (Claude, per `.ai/ROLE_CONFIG.md:9`). Read-only audit of plan2 `main` at `7f6d6cdfc`. Every
claim in Part B cites the code. Part A is the plain-language summary.

---

## Part A — Plain-language answer

**Short answer: the product does not depend on the simulator. The demo depends on the product, not the other way
round.** The part that receives readings and the part that works out what is going on (problems found, diesel nights
checked, the links between cause and result, the four-goal board) never call the simulator, never look for a
particular demo site, and never read the demo story's dates. A real gateway that has been given a key would be handled
the same way as the demo one.

**Where the demo does take short cuts.** To build the demo quickly, with weeks of history in about two and a half
hours, the demo tools do three things a real customer could not do:

1. **They hand readings straight to the receiving code** instead of sending them over the network with a key. The
   readings still pass every content check, but the key check is skipped.
2. **They back-date records.** The tools tell the system "this arrived on 3 November" when it is really 9 November.
   A real gateway always gets today's real time stamped on what it sends.
3. **They switch sites on with a direct database change** instead of using the proper "enable gateway" command that
   already exists.

None of these changes the product's rules. They are short cuts in how the demo data gets in.

**What a real customer site would get today**, if its gateway were given a key and started sending readings:

- **Works without any demo tool:** receiving readings, checking them, showing them, the automatic analysis that runs
  on a schedule, problems found, diesel night checks, the cause-and-result links, and the four-goal board.
- **Works, but less well than the demo:** the system cannot yet accept proof that a real device's clock is
  accurate. Only the demo can prove its clock. Without that proof the system still orders readings by their sequence
  number, but readings that arrive late and out of order are set aside instead of fitted in. For a steady real
  gateway that is a small loss. For one that drops off and catches up often, more blocks would show as "not usable".
- **Does not work yet for a real person:** agreeing a fix, recording work, checking whether a fix worked, and
  choosing between options. Nobody can sign in yet, so the product refuses these from the screen by default. The demo
  fills them in by calling the code directly. This is the missing sign-in, not a simulator link, but it does mean
  that the "what to do about it" half is only demonstrated today.
- **Setting up a new site is manual.** There are commands for every step (register the site from a description file,
  map its signals, issue the gateway key, set prices, add it to the schedule, set targets), but no screen, and two of
  the commands still have demo-looking names. Nothing in setup can only be produced by the demo tools.
- **Nothing runs the schedule on its own yet.** The analysis step exists as a command, but no timer is installed.
  Today only the demo tool runs it every two minutes. A real install needs one ordinary scheduled task.

**Small leftovers that read as "demo" on screen:** the "Demonstration · example sites and records" strip is shown on
every page whatever the data, and the targets explainer says targets were "set for this demonstration". Both are
wording, not logic, and both would be wrong for a real customer.

**Recommendation.** Nothing here blocks the demo, and nothing should be changed before it. After the demo, in order:
(1) a real-device clock proof, (2) sign-in, so the decision screens work for real people, (3) one scheduled task
for the analysis, (4) show the demonstration strip only when the data really is demonstration data, (5) send the demo's
readings over the network with a key, the way a real gateway would, and enable sites with the existing command, and
(6) rename the two demo-named setup commands and the tenant called "demo".

---

## Part B — Technical detail with citations

### B1. Inventory: what generates or injects data

| Item | What it does | Cite |
|---|---|---|
| `simulator/assetops_simulator` | Kernel that generates readings; no backend import | `simulator/` package; backend has no import of it (grep of `backend/assetops_backend` for `assetops_simulator`, `assetops_gateway`, `lab_app`, `host` modules: no hits) |
| `gateway/assetops_gateway` | "The durable simulated gateway" (seals, outbox, uploader); supports `SIMULATED` and `LIVE` source modes | `gateway/assetops_gateway/__init__.py:1`, `ledger.py:41` |
| `field/assetops_field` | **Real-device adapters**: read-only Modbus TCP poller and CSV export collector feeding the same gateway over IPC | `field/pyproject.toml:4-9`, `field/assetops_field/modbus_poller.py:1-17` |
| `host/lab_app.py` | The composed app with the Lab kernel wired; also the only place that injects the operational-entry principal | `host/lab_app.py:1-8`, `:60`, `:77-85`, `:88-119` |
| `host/ev_publication.py`, `host/cold_publication.py`, `host/gateway_publication.py` | Simulated EV charger, cold publication, registered gateway publisher | prior audit §7.1 E; `host/lab_app.py:68` |
| `backend/assetops_backend/simulator_lab_api.py` | Gated Lab router (create Site, runs, commit, execution); mounted only when `simulator_lab.enabled` | `main.py:4-6`, `:682`, `:696`; `simulator_lab_api.py:229`, `:2560` |
| `sites/ev_lab.py`, `sites/cold_lab.py`, `sites/w402_demo.py`, `sites/demo_configuration.py` | Product-package CLIs that install Lab or demo Sites through `import_site` / `FoundationService` | `sites/ev_lab.py:62`, `sites/cold_lab.py:63`, `sites/w402_demo.py:59`, `sites/demo_configuration.py:1-24`, `:87-88` |
| `scenarios/ev_parsing.py` | EV scenario pins `EV-LAB-001`, seed 20517, window 2026-10-06 | `scenarios/ev_parsing.py:25-32` |
| `config/operational-actions/kisiwa-001-operational-actions-v1.yaml` | Scripted refuelling log, read only by the gated Lab router | `runs/composition.py:30-32`; `main.py:715`; `simulator_lab_api.py:2434` |
| `tools/demo_combined.py` + children `_kobo`, `_kisiwa`, `_cold`, `_ev`, `_mill`, `_finish`, `_after`, `_drain`, `_ex1`, `_rows` | The combined demo prepare, add-day, serve loop | `tools/demo_combined.py:1-22`, `:739-820`, `:949` |
| `tools/demo_story_clock.py` | Story clocks for work/domain stores (monkey-patches composition) | `tools/demo_story_clock.py:46-72` |
| `tools/demo_story_days.py`, `backend/conversions/demo-story-days-v3.json` | S-relative story calendar | prior audit §7.1 F |
| `tools/demo_declare_objectives.py`, `tools/w601_seed.py` | Objective declaration, W6 seed (direct service calls) | `tools/demo_declare_objectives.py:15-16`; `tools/w601_seed.py:51-57` |
| Older walkthrough tools (`s2_demo_walkthrough.py`, `s3_dispatch_cases.py`, `s402b_power_cases.py`) | Post batches over HTTPS with the registered credential (the public path) | `tools/s2_demo_walkthrough.py:540-575`; `tools/s3_dispatch_cases.py:431`; `tools/s402b_power_cases.py:8` |
| Clock seams in product stores | Constructor-only overrides of DB time | `evidence/adapters/postgres_evidence_ledger.py:141-146`, `:525-528`; `work/adapters/postgres_work_store.py:287-315`; `work/adapters/postgres_domain_intent.py:231-260`; `fuel_balance/adapters/postgres_fuel_balance_store.py:188-215`; `financials/adapters/postgres_assumption_store.py:63-68`; `mini_decisions/store.py:119-130`; `objectives/adapters/postgres_objective_store.py:48-60` |

### B2. The canonical path

1. **Gateway upload.** `POST /api/ingestion/batches` (`evidence_api.py:156`, `:295`). The principal comes only from
   the bearer credential (`evidence_api.py:272-276`). Credentials are issued by the product CLI
   `evidence/provision_gateway.py` (`:1-36`; steps `issue`, `enable-gateway`, `enable-source`, `:59`).
2. **Batch V2 decision.** `BatchIngestionService.submit` (`evidence/ledger_service.py:99`). Order: size, strict parse,
   claims vs principal (site, mode, gateway registered/enabled, source affiliated/enabled; `:194-214`), batch-id
   conflict, the binding set and pinned snapshot must be registered for this Site and gateway (`:123-145`), then
   chunked ordinal decisions. `received_at` is server real UTC (`:22-23`); the ledger stamps `decided_at` with DB
   `clock_timestamp()` unless a test override is set (`postgres_evidence_ledger.py:525-528`).
   Mode is only compared, never required to be `SIMULATED` (`ledger_service.py:200-204`).
3. **Operational records.** Work records (fuel deliveries, dips) are written through the Work service; the screen
   entry route needs an injected principal, which only `host/lab_app.py` supplies when `ASSETOPS_OPERATIONAL_ENTRY=on`
   (`main.py:614-616`; `host/lab_app.py:77-97`). Fuel-balance reads them through `build_fuel_records_reader`
   (`fuel_balance/composition.py:17-25`).
4. **Scheduled tick.** `python -m assetops_backend.scheduling.run tick|enrol|health` (`scheduling/run.py:1-15`);
   stages `discover, s3, cold_assess, ev_assess, mini, fuel_night, opportunity, s4, chain_threads, chain_snapshots,
   consequence` (`scheduling/tick.py:13-23`, `scheduling/stages.py:100-102`). Sites come from the persisted inventory;
   the only Site-type branch is `site.site_type != "MINIGRID"` (`stages.py:316-320`).
5. **fuel_night.** `fuel_balance/scheduled.py` `run_site` picks due nights from tank readings and fuel records
   (`:1-16`, `:114-155`); window rule from versioned `fuel-balance-1` (prior audit cites `fuel_balance/rules.py:30-57`).
   Eligibility is data-driven (a Site with no tank `fuel_level` gets no row, `scheduled.py:9-10`).
6. **Chain, threads, outcomes.** `chain_threads` and `chain_snapshots` stages (`stages.py:204-313`); outcome board and
   estate routes mounted in `main.py:594-658`.
7. **Screens.** Frontend reads the product routes; default windows from the browser clock
   (`frontend/src/sites/PerformanceDispatch.tsx:87`, UTC today).

### B3. Dependency direction

**Product → simulator/demo: none on the monitoring path.**
- No import of simulator, gateway, host or tools from `backend/assetops_backend` (grep, non-test: no hits). The rule is
  structural: `main.py:12-17` ("nothing may import `host/`"), enforced by `tools/checks/dependency-direction.ps1`;
  `field/pyproject.toml:6-9` states the same for the field adapters.
- Site codes in backend non-test code appear only in docstrings/CLI usage (`chain/snapshots.py:3-5`,
  `declare_objective.py:8-10`, `evidence/provision_gateway.py:4`, `publish_assumption.py:7-10`,
  `recompute_consequences.py:3-27`, `main.py:311`), plus the Lab-only EV pin (`scenarios/ev_parsing.py:25-32`,
  `simulator_lab_api.py:2750`) and the profile names `REGISTERED_KOBO_PUBLICATION_PROFILE*` (`runs/profiles.py:1871-2212`,
  simulator publication profiles).
- Frontend: Site codes only in tests/fixtures (`frontend/src/estate/__tests__/portfolioFixtures.ts`), plus a comment
  (`shell/evScenarioChoiceClient.ts:6`). Data provenance words come from data mode, not site
  (`sites/LedgerSiteEvidence.tsx:135`, `sites/findingWords.ts:207`).
- "Story time" in `chain/` means effective time (`chain/lifecycle.py:134-155`, `chain/lookup.py:3`); naming only.

**Mode-specific branches that matter for a real Site:**
- `analytics/clock_attestation.py:14-16`, `:32-33`: "LR-01 has no real-source path: the only proof class is
  `SIMULATED`". The store refuses an attestation for a non-simulated Site (`analytics/adapters/postgres_assessment_store.py:689-691`),
  and the cohort refuses simulated proof for a live reading (`analytics/cohort.py:183-184`). Without proof the cohort
  "keeps the sequence rule" (`cohort.py:29-33`): late out-of-order readings mark spans `SEQUENCE_ORDER_INVERTED`.
- `postgres_evidence_ledger.py:392-397` (`GATEWAY_NOT_SIMULATED`) applies to the Lab *source publication* lane only,
  not Batch V2. Legitimate.

**Demo-only gates: legitimate product features (configuration).**
| Gate | Why legitimate | Cite |
|---|---|---|
| `simulator_lab.enabled` | Lab router not mounted when off | `main.py:4-6`, `:682` |
| `ASSETOPS_OPERATIONAL_ENTRY` | Off by default (403); refuses any value but `on` | `host/lab_app.py:77-85`; `main.py:614-616` |
| `ASSETOPS_ACTION_DEMO_GRANTS` | Absent grants nothing; labelled SYSTEM demonstration | `actions/adapters/demo_grants_file.py:1-20`; `actions/capability.py:1-20` |
| `ASSETOPS_DEMO_FIXTURE_MANIFEST` / `ASSETOPS_FINDING_CASES_MANIFEST` | Annotates exact IDs only | `analytics/composition.py:37-40`; `main.py:401`, `:550-551` |
| Story clocks in mini-decisions and objectives | Refused unless DB is `assetops_polish_*` or `*_test` | `prepare_clock.py:13-24`; `mini_decisions/store.py:126-130`; `objectives/adapters/postgres_objective_store.py:60` |
| Write principals (decisions, domain Actions, work) | Default deny; injected only by tests/host | `main.py:241-245`; `mini_decisions_api.py:58-63`; `work_api.py:59`; `main.py:607-623` |

**Leakage (product code or wording that assumes a demo).**
| ID | Finding | Severity | Cite |
|---|---|---|---|
| L1 | No real-device clock proof class; live Sites get sequence-only ordering | Medium (post-demo) | `analytics/clock_attestation.py:14-16`, `:32-33`; `postgres_assessment_store.py:689-691` |
| L2 | "Demonstration · example sites and records" banner is unconditional on every page | Low (post-demo; wrong for a live tenant) | `frontend/src/shell/OperatorShellLayout.tsx:12`, `:135-137` |
| L3 | Outcome Board explainer says objectives are "set for this demonstration" unconditionally | Low | `frontend/src/sites/OutcomeBoard.tsx:71-72` |
| L4 | Operational-entry principal composes only in `host/lab_app.py`, so the non-Lab entry point (`assetops_backend.main:app`) can never save operator records | Medium (post-demo) | `host/lab_app.py:71-97`; `main.py:245`, `:614-616` |
| L5 | Single tenant hard-coded as slug `"demo"` | Low (post-demo, with sign-in) | `config.py:101-105`; `main.py:330-336` |
| L6 | Generic setup CLIs carry demo names: `sites/import_kobo.py` (takes any `--source`), `sites/convert_kobo_bindings.py` (any `--fixture`); `sites/demo_configuration.py` insists on a "SIMULATED DEMO CONFIGURATION" label | Low (cosmetic) | `sites/import_kobo.py:1-14`, `:155-157`; `sites/convert_kobo_bindings.py:1-14`; `sites/demo_configuration.py:87-88` |
| L7 | EV scenario pin to `EV-LAB-001` + fixed window (Lab only, not monitoring) | Low (post-demo `ev-scenario/2`) | `scenarios/ev_parsing.py:25-32`; `simulator_lab_api.py:2750` |
| L8 | UTC "today" on the dispatch board instead of Site-local | Low | `frontend/src/sites/PerformanceDispatch.tsx:87` |

**Back doors used by the demo tools (tool-side, not product leakage, but they are not the public interface).**
| ID | Back door | Effect | Cite |
|---|---|---|---|
| B1 | In-process `BatchIngestionService.submit` with a `GatewayPrincipal` built from the snapshot, behind a `FakeCentral`; the gateway's token is random and never verified | Skips HTTP + credential auth; content validation still runs | `tools/demo_combined_kobo.py:258-289`; Cold patches the W2-02 harness the same way, `tools/demo_combined_cold.py:69-82` |
| B2 | Back-dated decision/received clock via `test_decision_clock_override` and a fixed `received_at` | Records "arrive" on story days | `tools/demo_combined_kobo.py:273-274`; `tools/demo_combined_cold.py:79-82`; seam `postgres_evidence_ledger.py:20-21`, `:525-528` (not guarded by `require_prepare_database`) |
| B3 | Direct SQL `UPDATE gateway/source SET disabled_at = NULL` | Bypasses `provision_gateway enable-gateway/enable-source` and its `gateway_access_event` audit | `tools/demo_combined_kisiwa.py:175-177`; `tools/demo_combined_kobo.py:424-426`; proper path `evidence/provision_gateway.py:33-35` |
| B4 | Story clocks monkey-patched onto work and domain stores; fuel Finding service and assumption store with test clocks | Back-dated work, Actions, Findings, prices | `tools/demo_story_clock.py:46-72`; `tools/demo_combined_kisiwa.py:144-157`, `:527-545`; seams `work/adapters/postgres_work_store.py:287-315`, `fuel_balance/composition.py:33-43`, `financials/adapters/postgres_assumption_store.py:63-68` |
| B5 | In-process service calls for writes with no product route or a denied route (fuel verification, mill verification, mini decisions worker, chain snapshot stage, work service) | Fills the "what to do" layers without a principal | `tools/demo_combined_kisiwa.py:555`, `:643`, `:714-718`; `tools/demo_combined_mill.py:80-92`, `:189-221`; `tools/w601_seed.py:51-57` |
| B6 | Demo prepare imports test harness modules (`test_s6_verification_publication`, `fake_central`, `pg_harness`) | Tooling depends on tests, not product | `tools/demo_combined_kobo.py:258-268`; `tools/demo_combined_kisiwa.py:148`, `:162` |

None of B1–B6 is reachable from a running server: the seams are constructor-only and production composition never
passes them (`postgres_evidence_ledger.py:20-21`; `prepare_clock.py:3-5`; `tools/demo_story_clock.py:12`). The guard
`require_prepare_database` protects only the mini-decision and objective seams and the tool's own story clocks; the
evidence, work, fuel and assumption seams rely on "only tools construct them".

### B4. Real-gateway test

A real gateway (the in-repo gateway fed by `field/assetops_field` Modbus or CSV adapters, or any client speaking
Batch V2) with a registered credential would be ingested exactly as the demo's would, minus B1/B2. Onboarding steps and
their producers:

| Step | Product producer | Demo-only? |
|---|---|---|
| Site description YAML (`var/sites/*.yaml`) | Hand-written; imported by `python -m assetops_backend.sites.import_kobo --source ... --tenant demo` | No (misnamed, L6). Lab `POST /sites` also creates Sites but is gated (`main.py:9-10`) |
| Signal bindings | `sites/convert_kobo_bindings.py` CLI or `POST /api/sites/{id}/foundation/bindings` (`foundation_api.py:81`, `:588`) | No |
| Component properties (supply-use, no-load rate, generator values) | `POST /api/sites/{id}/foundation/revisions` (`foundation_api.py:80`, `:492`) | No (demo uses `apply_demo_configuration`, labelled) |
| Gateway credential, enable gateway and sources | `evidence/provision_gateway.py` | No |
| Clock proof | None for real sources (L1) | Only `SIMULATED` exists |
| Tariffs, diesel price | `POST /api/sites/{code}/financial-assumptions` (`financial_api.py:59`) or `publish_assumption` CLI | No |
| Objectives | `python -m assetops_backend.declare_objective` (`declare_objective.py:8-10`) | No |
| Schedule enrolment and a timer | `scheduling.run enrol` (`scheduling/run.py:5`, `:45`, `:61`); "no timer is installed" (`run.py:1`); today only the demo serve loop ticks (`tools/demo_combined.py:21`) | Timer: tooling-only today |
| Operator records from the screen | Needs `ASSETOPS_OPERATIONAL_ENTRY=on` and the `host/lab_app.py` entry point (L4) | Lab-host composition only |
| Agree/apply/verify an Action, decisions, Work writes | Denied by default (`main.py:241-245`, `:607-623`); Action commands only for fixture-listed records (`actions/capability.py:3-7`) | Demo writes them in-process (B5) |

Result: every **automatic** layer (ingestion, evidence reads, S3 dispatch, cold/EV assessment, mini, fuel_night,
opportunity, S4 Findings, chain threads/snapshots, consequence, outcome and estate boards) runs for a new real Site with
no simulator or demo tool present, once the configuration steps above are done and something runs the tick. The
**human-decision** layers are write-locked until sign-in exists; that is the absence of authentication, not a
simulator dependency.

### B5. Verdict per layer

| Layer | Dependency on simulator/demo |
|---|---|
| Batch V2 ingestion and evidence ledger | **None** (demo bypasses auth and clock via B1/B2, tool-side) |
| Site/foundation/bindings configuration | **Config-only** (CLIs and routes are generic; demo names L6) |
| Clock-ordered analytics (cohort) | **Product leakage, Medium (L1)**: only simulated clock proof exists |
| Scheduled tick and its stages, fuel_night | **None** in logic; **tooling-only** for running it continuously (no timer) |
| Findings, chain, threads, outcomes, estate | **None** |
| Operator records entry | **Config-only**, but composed only in the Lab host (L4, Medium) |
| Actions, verification, decisions, Work writes | **Tooling-only** today (no principal in product; demo writes in-process, B5) |
| Frontend | **Product leakage, Low** (L2, L3, L8) |
| Lab, EV/Cold scenario pins | **Simulator by design** (gated; L7) |

**Demo-critical:** nothing. Do not change any of this before the demo (`demo-critical-scope-only`).

**Post-demo, in order:** (1) a real-source clock proof class (L1); (2) sign-in and real principals, which unlocks the
decision layers and lets operational entry compose in `assetops_backend.main` (L4, L5, B5); (3) a scheduled-task unit
for `scheduling.run tick` and a runbook for onboarding; (4) make the banner and the objectives sentence data-driven
(L2, L3); (5) move the demo prepare onto the public path, with HTTPS upload, a real credential and `provision_gateway`
enablement, keeping back-dating only behind `require_prepare_database` on every seam (B1–B4); (6) cosmetic renames
(L6, chain "story time" to "effective time") and `ev-scenario/2` (L7).

This confirms build sheet §7's "no product hard-coding on the monitoring path" and extends it with L1, L2, L4 and the
B-series back doors, which §7 did not cover.
