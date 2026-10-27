# Architect rulings D4, D10, D5, D6 for the telemetry plan (2026-10-27)

Architect: Claude. `.ai/ROLE_CONFIG.md` line 9 and "Architect Is Claude By Default" (line 39) bind this role to Claude, so these rulings are made directly.

- Plan: `Docs/demo-sprint/telemetry-integration-plan-claude.html`, revision 3. Sections used: §1, §4, §6.1, §6.1.1, §10, §11.1 and §14.
- Owner feedback (verbatim): `.agent/owner-telemetry-plan-feedback-2026-10-27.md`.
- Code read in `AssetOpsV1-demo-plan`, branch `plan/commercial-capability-assessment` at eaf8a43c. That commit is an ancestor of main 5174657c and the tree diff is empty, so the code facts below hold on main.
- Scope: rulings only. No HTML, product code or commit. No new research, and the architecture is not broadened.

Probe run for these rulings: a scratch, non-DB pytest file against the real `GatewayService`, using the `gateway/tests/conftest.py` fixtures. It produced 5 passed and confirmed:
- (a) `UNAVAILABLE`/`NO_MEASUREMENT` with an interval span is admitted;
- (b) `UNAVAILABLE`/`NO_COMPLETED_INTERVAL` is admitted only with a span; without one it is held as `INVALID_TIMING` at `payload.interval_start`;
- (c) a non-terminating mean (`10/3`) is held as `INVALID_VALUE`, and the same mean quantized with `quantize_half_even` to `0.001` is admitted;
- (d) an `UNAVAILABLE` report still records source contact (`OBSERVED_SIMULATED_REPORT`).

`backend/tests/test_s405_resolver.py` also ran: 13 passed.

## Summary

| # | Ruling | Change to the plan |
|---|---|---|
| D4 | Accepted, with an adjusted import rule and an explicit IPC op set. The rules in the pinned profile are specified below. | Adjusted. The plan's "admit only" op set cannot upload (see the IPC finding). Field tests may not reach the simulator, so the emulator is fed from a pinned JSONL fixture. |
| D10 | Every expected poll must be answered GOOD; otherwise the interval is not published as GOOD. | Adjusted. An interval with missing polls is `UNAVAILABLE`/`NO_MEASUREMENT` **with its span**, not `NO_COMPLETED_INTERVAL`. `NO_COMPLETED_INTERVAL` is only for an interval the poller did not observe from its start. |
| D5 | Accepted: `battery_power` stays unbound on GX profiles; no DC quantity under any AC role; no new DC role in October. Site-total consumption is also left unbound. | Tightened. The financial gate is restated against the money gate that already exists. |
| D6 | Accepted: the indicator set, with no identical-readings rule. | Adjusted. A transport failure publishes **nothing**; only "the device answered but gave no value" becomes `UNAVAILABLE`. The informational identical-run count is not built. |

---

## D4: the `field/` module root, its import rule and the rules held in the pinned profile

### Decision

1. **New module root `field/`.** It holds the package `field/assetops_field/` and a `field/pyproject.toml` with:
   - `requires-python = ">=3.12"`;
   - `dependencies = []`;
   - extras `dev = ["pytest>=8.0", "pymodbus==3.16.1"]` and `serial = ["pyserial"]`.

   Adapters run as separate processes and are IPC clients of an unchanged gateway.
2. **Import rule for non-test `field/` modules.** They may import:
   - the standard library;
   - `assetops_contracts.*`;
   - `assetops_gateway.ipc`;
   - `serial` (pyserial), and only in a later RTU module.

   They may not import `assetops_backend`, `assetops_simulator`, `host`, any other `assetops_gateway.*` module, or `pymodbus`.
3. **Import rule for `field/tests`.** The tests are scanned too, as the gateway's tests are. They may import `pymodbus` and `assetops_gateway.ipc`. They may not import `assetops_backend`, `assetops_simulator`, `host` or other gateway modules. Any test that needs the simulator, backend or real gateway process lives in `host/tests` (the composition leaf) or `backend/tests`, as TEL-04 and TEL-05 already do.
4. **Reverse direction.** Nothing imports `assetops_field` except `host/tests`, `backend/tests` and `field/` itself. That excludes backend, gateway, simulator and contracts code, and host product code.
5. **IPC op set for October adapters.** The poller and the CSV collector call only these ops:
   - `identity`;
   - `admit` (the `GATEWAY_UTC` clock);
   - `seal`;
   - `release_run`, with the adapter's own run reference;
   - `diagnostics`.

   They never call `activate`, `admit_at_run_clock`, `advance_publication_clock`, `inject_fault`, `run_stage`, `run_delivery` or `deliver`. Snapshot activation is a provisioning act: it belongs to the test harness, or to a one-shot runbook command, and never to the polling loop. Upload is left to the gateway's own background uploader (`serve` attaches it with `background=True`).
6. **Run reference.** Each adapter session uses `lab_run_ref = "field:<profile_id>:<profile_version>:<session start UTC>"`. The reference stays local to the gateway and never reaches central ingestion. In October each gateway instance serves **one** adapter.

### Rules held in the pinned profile (R4, made concrete)

The profile is a JSON document whose canonical SHA-256 (key-order independent) is recorded with every raw capture and in the claim record. Its `status` is `PINNED`, `UNPINNED` or `ILLUSTRATIVE`. Each row states:

**Identity and meaning**
- `device_id`, `signal_id`, the `role` it is meant to feed, and its `source_unit`.
- Physical quantity and measurement point: AC or DC, which bus, which side of the converter.
- Sign convention.
- Phase aggregation: for example, an exact sum of L1, L2 and L3 per poll.
- Source document and version.

**Scaling**
- The decode type (`int16`, `uint16`, `int32` or `uint32`), the word order, the sentinel(s), and a scale exponent `e`. The value is `raw × 10^e`.
- Arithmetic is exact (`fractions.Fraction`). Unit conversion (W to kW) is a declared power of ten.
- No float is used anywhere, and no multiplier that is not a power of ten (it could produce non-decimal values).

**Output resolution**
- An `output_resolution`, a finite decimal such as `"0.001"`. Every published value is `quantize_half_even(value, device_resolution(output_resolution))`, applied **once**, after aggregation.
- The value text comes from `exact_decimal_text`. Reuse both helpers from `assetops_contracts.observation`; do not write a second rounding.
- Without this, a mean over 3 polls is a non-terminating rational, and the gateway holds it as `INVALID_VALUE` (probe c).

**Timing**
- `reading_class`, which is `STATE_SIGNAL` or `INTERVAL_SIGNAL`.
- `span_seconds`, the interval a mean covers, and `cadence_seconds`, how often it is published. These are separate fields: the Kobo profile publishes the generator every 60 min about the last 15 min (`profiles.py:501-506`, `:1465-1480`).
- `poll_period_seconds`, which must divide `span_seconds` exactly; otherwise the profile is refused.
- Interval boundaries are aligned to whole multiples of `span_seconds` from 00:00:00Z.
- A mean covers `[source_time - span, source_time)`. Its `interval_start` is `source_time - span`, and the V3 envelope requires that span on every `INTERVAL_MEAN`, `UNAVAILABLE` included (`source_envelope_v3.py:281-289`).

**State reads**
- `source_time` is the boundary instant at which the first read was sent.
- One retry is allowed only within `state_skew_max_seconds`, default 2. Otherwise there is no state sample for that boundary.
- No sample is moved to another instant. `ReportingResolutionUnrepresentable` (`observation.py`) calls that a lie.

**Timezone**
- Every instant the adapter emits is whole-second UTC `...Z` (the gateway's `_INSTANT`, `service.py:75`).
- In October the only accepted profile value is `source_timestamps: "UTC_Z_REQUIRED"`. Modbus has no source timestamp, so the poller's clock is the sample clock. CSV rows without `Z` are refused `INVALID_TIMING`.
- Interpreting local time (likely in real vendor exports) is a later ruling, made with a genuine sample (TEL-10).
- Site-local windows remain central's job, from the Site's pinned IANA zone (`mini_depth/inputs.py:57`). The adapter never shifts time.

**Coverage**
- `coverage: "ALL_EXPECTED_POLLS"` is the only accepted value in October (D10). The field exists so that a later rule is a profile-schema version that shows in the SHA.

**Report key**
- `report_key = "<profile_id>:<profile_version>:<device_id>:<signal_id>:<source_time>"`. It must match the contract's key pattern (`gateway_report.py:47`, at most 192 characters).
- The profile SHA is deliberately **not** in the key. A corrected profile that changes a value then surfaces as `CONFLICTING_REPORT` and is not silently admitted twice.

### Code evidence

- The gateway declares `dependencies = []` and its check allows it to import contracts only (`gateway/pyproject.toml`; `dependency-direction.ps1:176-200`, tests included).
- `assetops_gateway.ipc` uses only the standard library on the client side. `GatewayLink` (`ipc.py:158-190`) needs only an address and a credential file. The server half imports the service lazily, inside `_dispatch` (`ipc.py:301-303`), so a client never loads the ledger.
- **IPC finding (load-bearing).** The IPC `admit` op passes no `initial_state`. `GatewayService.admit_texts` defaults to `"STAGED"` (`service.py:603-610`), and a STAGED batch uploads only after `release_run` (`service.py:1383-1410`). `serve` never seals by itself (`__main__.py:102-120`); the Lab publisher calls `seal` and then `release_run` (`host/gateway_publication.py:192`, `:225`).
  - Consequence: an adapter limited to `identity`, `admit` and `diagnostics`, as §1 G8 proposes, would never upload, and TEL-04's "every admitted envelope is acknowledged with a 200 receipt" could not pass.
  - `_str` makes `lab_run_ref` a mandatory non-empty string (`ipc.py:379-383`).
  - `release_run` skips a batch that carries another reference's items (`service.py:1397-1399`). That is why each gateway has one adapter.
- Current checks:
  - `module-roots.ps1` lists required roots and marker files. A `field/` root breaks nothing, but the rules about it are vacuous unless the root is required.
  - `dependency-direction.ps1` has no rule that mentions `assetops_field`, so today nothing stops the gateway or the backend from importing it.
  - `Get-ScannedModules` skips `tests/` by default (`_common.ps1:62-83`). `Get-SourceFiles` does not skip them.
  - The other checks (configuration persistence, simulator gate, run setup and the frontend checks) scan only `backend/` and `frontend/` roots, so they need no change.
- The public observations come from `simulator/assetops_simulator/observation/transform.py:224` (`generate_observations`), which host re-exports through `lab_execution`. Field code cannot reach it.

### What must change in `tools/checks` (TEL-01, additive only)

1. `module-roots.ps1`:
   - add `field` and `field/assetops_field` to `$requiredDirectories`;
   - add `field/pyproject.toml` and `field/assetops_field/__init__.py` to `$requiredFiles`.
2. `dependency-direction.ps1`, a new section, "The field adapters are IPC clients":
   - **Non-test `field/` modules** (`Get-ScannedModules -Root "field"`):
     - fail on `^\s*(?:from|import)\s+[^\s]*assetops_backend`, `...assetops_simulator`, bare `backend|simulator|host`;
     - fail on `^\s*(?:from|import)\s+pymodbus`;
     - fail on any `assetops_gateway` import whose module group is not `ipc`, reusing the `$hostGatewayImport` regex shape;
     - fail on the matching `import_module(` forms.
   - **`field/tests`** (`Get-SourceFiles -Root "field/tests"`): the same rules, except that `pymodbus` is allowed.
   - **Anti-vacuity:**
     - at least one non-test field module must be scanned;
     - at least one must import `assetops_gateway.ipc` (that is `publish.py`).
   - **Reverse rule:**
     - fail on `^\s*(?:from|import)\s+assetops_field` in `backend/` (tests included, matching the product-to-gateway rule);
     - fail on it in `gateway/` and `simulator/` (Get-SourceFiles);
     - fail on it in `contracts/`;
     - fail on it in non-test `host/` modules.
   - Add `field` to `$mayNotImportHost`.
3. Do not edit, loosen or reorder any existing rule.
   - If a field rule cannot be expressed without changing an existing gateway or host rule, stop (TEL-01's existing stop condition).
   - `tools/checks/test_estate_guard.py` copies `tools/`, `backend/`, `config/` and `contracts/` and runs only the configuration seam, so it needs no change.

### The implementer must

- Run tests with `PYTHONPATH="backend;contracts;simulator;gateway;host;field;."`.
- Put no `conftest.py` in `field/tests`. A second `conftest` module name breaks mixed collection, as noted in §1. Shared helpers go in a uniquely named module, for example `field_fixtures.py`.
- Feed the TEL-03 emulator from a **pinned public-observation JSONL** under `contract-fixtures/telemetry/kobo-public-observations-v1/`, with a `manifest.json` that gives the SHA-256 and the generating command.
  - The generator and a freshness test live in `host/tests`, which may call `generate_observations` on the registered Kobo draft, exactly as `host/tests/test_registered_gateway_publication.py:143` does.
  - `field/tests` reads only the JSONL. This is what §6.1 already says ("pinned public-observation JSONL"). TEL-03's "Inputs" line, which obtains observations in-test, is replaced by it.
- Build `DeviceReport` through `assetops_contracts.gateway_report.device_report_text`, and round-trip every text through `parse_device_report_text` in tests.
- Have the poller check, through `identity`, that the gateway's active snapshot SHA equals its configured one before it admits anything. On a mismatch it stops; it does not admit.

### The implementer must not

- Change `gateway/`, `backend/` or `contracts/` product code. That includes the IPC op table, the `DeviceReport` schema and the snapshot conversions.
  - The schema ID still reads `assetops.simulated-device-report`. That is accurate in October, because the bench gateway is SIMULATED. Renaming it is a TEL-09 contract matter.
- Put scaling, aggregation or time logic into the snapshot or binding. The snapshot keeps `IDENTITY`, `ENUM` and `IDENTITY_KWH` (`snapshot.py:32`).
- Write envelopes, batches or ledger rows directly (R1).
- Run two adapters against one gateway instance.

---

## D10: the interval coverage rule

### Decision

For an adapter-computed interval mean over `[start, end)`, the expected polls are those at `start + k × poll_period` for `k = 0 … N−1`, where `N = span / poll_period`.

| Situation in the interval | What the adapter publishes at `end` |
|---|---|
| All N expected polls answered with a decodable, non-sentinel value | `GOOD`: the exact mean of the N values, quantized once to `output_resolution` |
| The poller was observing from `start`, at least one poll was answered, and at least one expected poll was missing, failed or returned a sentinel or "no value" exception | `UNAVAILABLE` / `NO_MEASUREMENT`, with `interval_start = start` |
| The poller (or its session) began after `start`: its first boundary, or after any poller restart or loss of its own schedule | `UNAVAILABLE` / `NO_COMPLETED_INTERVAL`, with `interval_start = start` (V3 requires the span) |
| No expected poll was answered at all (transport down for the whole interval) | **Nothing.** No envelope is published (D6). |

- Nothing is interpolated, carried forward or computed as a partial mean. Coverage is not a tunable parameter in October.
- **Export rows (TEL-06).** D10 does not re-aggregate them. A row's own declared interval must equal the profile's `span_seconds` and end at its `source_time`. A row that does not match is refused, not resampled.

### Reasoning, and why the plan's proposal changes

- **The 100% threshold is accepted.** A mean of the answered polls is biased whenever loss correlates with the quantity (a busy controller at peak load, for example). 100% is exact, simple and testable against an emulator whose faults are controlled. Relaxing it needs real poll-loss data, at TEL-11 at the earliest, and becomes a profile version.
- **The reason code changes.** The plan said missing polls should give `NO_COMPLETED_INTERVAL`. In this codebase that reason means "there was no preceding interval": the simulator maps `NO_PRECEDING_INTERVAL` to it (`gateway_report.py:38-41`, `simulator/assetops_simulator/gateway/publish.py:64-67`). `NO_MEASUREMENT` is "a device that was publishing sent no value". An interval the poller watched end to end, with a missing poll, is the second case.
- **No downstream consumer branches on the reason** (grep over `backend/assetops_backend`), so the honest code costs nothing.
- **The span is always required.** The V3 envelope demands a span on every `INTERVAL_MEAN` (`source_envelope_v3.py:281-289`), and `report_from_observation` always sets `interval_start` (`gateway_report.py:159-162`). Probe (b) confirms that a span-less `NO_COMPLETED_INTERVAL` is held as `INVALID_TIMING`.
  - The older V1 `source_envelope.py:969-975` says the opposite. It is not the gateway path; do not follow it.

### The implementer must

- Change the TEL-01 done-when item to: "an interval missing one expected poll yields `UNAVAILABLE`/`NO_MEASUREMENT` with its span; the interval in which the poller started yields `UNAVAILABLE`/`NO_COMPLETED_INTERVAL` with its span; a fully failed interval yields no report; nothing is interpolated."
- Add a test with N = 3 polls and a mean that does not terminate, to prove the single quantization.

### The implementer must not

- Publish a GOOD mean of fewer than N polls.
- Emit an interval mean without `interval_start`.
- Treat the export collector as an aggregator.

---

## D5: battery DC/AC binding and the financial-finding gate

### Decision

1. **No DC quantity is ever bound to `battery_power`,** or to any other role whose meaning is AC or converter-side.
2. **GX profiles leave `battery_power` unbound.** Register 842 (DC battery power) is not in the October profile, and no row maps it anywhere.
3. **No new DC role in October.** §6.1.1(3) proposed an unconsumed `battery_dc_power` role. It is deferred: a new role is a `minigrid-roles-N` version (`binding_roles.py:124-126`, "Immutable: a change is a new named version") with migration and guard reach, and nothing consumes it. It is decided with TEL-12, if ever.
4. **No DC-to-AC efficiency conversion, ever.** It would invent data.
5. **Same rule for consumption.** Site-total consumption (GX 817–819) is **not** bound in October. The only consumption role is `feeder_demand` (`PER_ASSET`, `binding_roles.py:93`), and Kobo has three feeders (`residential-meter`, `clinic-meter`, `mill-meter`; `profiles.py:1532-1560`). A site total under one feeder's role is the same category error as DC under AC. The October GX profile is therefore PV on AC output (808–810, exact phase sum) and SoC (843), nothing else.
6. **PV scope is stated in the profile.** The `pv_power` row says it covers AC-coupled PV on the AC output only. DC-coupled MPPT PV is not included, so the row is not a complete PV figure. That is a stated limitation, not a binding to fix in October.

### What must be true before any money result may come from GX or edge telemetry

A money amount whose Finding cites accepted evidence that arrived through a `field/` adapter (GX, any edge poller, or a customer export) may be **shown as current** only when **all** of the following hold. Until then the Finding may show, and the amount reads as not available with its reason.

- **(a) The profile states what each role means.** Every role the Finding and its consequence cite (for fuel-cost: generator state and power, the feeders, SoC, PV, and any battery role used) has a **PINNED** profile row stating:
  - its physical quantity (AC or DC) and measurement point;
  - its sign convention and phase aggregation;
  - its span and cadence;
  - its source document and version, from the vendor's own register sheet or a genuine sample, not a third-party summary.
- **(b) The profile matches the roles.** A test asserts each row against the role table and the Site's Kobo-equivalent device declaration:
  - unit and value kind;
  - AC versus DC against the role's asset type, so that `POWER_CONVERSION_SYSTEM` `battery_power` is AC at the converter, positive when discharging to the bus (`profiles.py:1502-1515`);
  - sign;
  - span.
- **(c) Values were checked against an independent reading.** Sign and magnitude were compared with an independent reading on a named device model and firmware, for example the GX display plus a clamp meter, and recorded at R3 with a §10.0 claim record.
- **(d) A real-source provenance class exists and the evidence resolves to it.** "Positive" is not enough: today the positive classes are `AUTHORED_DEMONSTRATION` and `REGISTERED_SIMULATION` (`provenance_read.py:27`), and both mean "not real". Money from real telemetry therefore needs a contract-ruled real-source class (ATTESTED_REAL_SOURCE, R5, the pilot gate), and the evidence must resolve to it. Emulator or export-proof evidence must never be given an `AUTHORED_DEMONSTRATION` or `REGISTERED_SIMULATION` publication to make the money gate pass.
- **(e) The existing gates pass, unchanged.** The money composition must still pass `money-eligibility-1`, the CURRENT PRICED head consequence and `source_gate`. None of these is bypassed or special-cased for field sources.

In October, gate (d) fails by construction: there is no publication, so the class reads UNKNOWN (D1). The existing source half of the money gate then withholds any current amount (`consequence_read.py:236-240`; `provenance_read.py:30-39`). In addition, the October GX profile binds no generator role, so `dispatch-3.1` records `NO_GENERATOR_STATE` (`dispatch_v3.py:537`) and no dispatch Finding or fuel-cost consequence can arise. TEL-05's "no consequence or money row" is therefore expected, and it is a real assertion, not a skip.

### Code evidence

- `battery_power`: "Battery converter power", `POWER_CONVERSION_SYSTEM`, kW, optional (`binding_roles.py:101`). Kobo's source for it is `battery-pcs-controller/ac-power`, the mean AC power, positive when discharging (`profiles.py:1502-1515`).
- `dispatch-3.1` no longer infers Candidate time from `battery_power`. That was `dispatch-2`'s behaviour, named only in a documented delta (`performance_comparison.py:46-52`); dispatch-3.1 uses `pcs_discharge_capability` (`dispatch.py:79`). `battery_power` is still a selected input of mini-depth (`mini_depth/inputs.py:33-37`), which imports `fuel_cost`. A DC value bound there could still move a money-adjacent read, so the rule stands.
- Money already requires a positive source class: cold (`cold_consequence.py:96`), EV (`ev_money.py:33`) and mini-grid (`consequence_read.py:236-240`).
- A SIMULATED bench gateway could technically accept a source publication (`postgres_evidence_ledger.py:395-397` refuses only non-SIMULATED gateways). That is why (d) forbids attaching one.

### The implementer must

- Ship `gx-system-illustrative-1.json` with rows 808, 809 and 810 (PV, exact phase sum) and 843 (SoC) only, each with the (a) fields filled. For the UNPINNED status, source = "third-party summary".
- Keep TEL-05's assertions that no consequence or money row exists and that provenance is UNKNOWN / `NO_POSITIVE_BINDING`.

### The implementer must not

- Add 842, 817–819, or any new role.
- Attach a publication to bench evidence.
- Add any field-source special case in `financials/`, `analytics/` or `evidence/`.

---

## D6: freshness and quality indicators

### Decision

The identical-readings rule is rejected (owner adjustment 4). No count of identical values is built in October, informational or not: it has no consumer and it invites the rejected use. Freshness and quality come only from the indicators below.

| Indicator | Built in October | Where it lives | Effect |
|---|---|---|---|
| **Transport outcome per read** | Yes (TEL-02, TEL-04) | Poller raw-capture log (SHA-256 per frame) and local counters | See the mapping below |
| **Source contact age** | Exists (`last_device_contact_by_source`) | Gateway diagnostics, unchanged | Grows when the poller publishes nothing |
| **Interval coverage** | Yes (D10) | Aggregator | GOOD only at full coverage |
| **Source-time lag against cadence** | No | Later, for B2 and APIs | Only meaningful where the source has its own clock; Modbus has none |
| **Device-published status register** | No | Per pinned profile only | None claimed for GX until it is pinned |
| **Vendor quality flags** | No | Per genuine-sample profile (TEL-10) | None |

**Mapping from transport outcome to what is published.** This is the load-bearing part of the ruling.

| Read outcome | What is published |
|---|---|
| **Device answered and stated "no value"**: a documented sentinel (for example 0x7FFF), or Modbus exception 02 (illegal data address, the service is absent) | That read is `UNAVAILABLE`/`NO_MEASUREMENT`. For a state signal it is the boundary's report; for an interval it makes the interval `NO_MEASUREMENT` (D10). |
| **Device answered busy or failing**: 04 or 06, after the one allowed retry | Counts as a failed poll: no value. For a state boundary this means no sample; for an interval it means `NO_MEASUREMENT` if other polls in the interval were answered. |
| **No answer**: timeout, connection refused or reset, server pause, exception 0A or 0B (a gateway or bridge path to the target failed), Unit ID or transaction-ID mismatch | **Nothing is published** for that read. If no poll in an interval is answered, the interval publishes nothing. Contact age then grows. |
| **Configuration error**: exception 01 or 03, or a decode or type mismatch against the profile | Nothing is published. The poller records a profile fault and stops polling that row; this is not a data-quality state. |

The poller never emits `STALE`. The contract reserves it for consumers (`source_envelope.py:133-135`, `ENVELOPE_QUALITIES = {GOOD, UNAVAILABLE}`).

### Reasoning, and why the plan's proposal changes

- **What "contact" means in the gateway.** The gateway records source contact whenever a report resolving to a permitted source arrives, `UNAVAILABLE` included (`service.py:1103-1116`; probe d). On the poller path, "contact" therefore means the adapter reached the gateway, not that the device answered.
- **Why a failed read must publish nothing.** If the poller published `UNAVAILABLE` on a timeout or server pause, which §6.1's "Key fault tests" line implies, contact age would reset every boundary and could never show an outage. TEL-04's "a paused emulator raises contact age" would then fail.
- **Consistency with the contract.** Publishing nothing on no-answer also matches the contract: a reporting path that is down produces no envelope, while `NO_MEASUREMENT` is for a device that answered without a value.
- **Contact age stays a coarse indicator.** It is an adapter-to-gateway signal with `OBSERVED_SIMULATED_REPORT` provenance on the bench (`service.py:1110`). It is not a device-contact proof, and claim records must not describe it as one. A measured device-contact or clock probe is G5 and TEL-13, after October.

### The implementer must

- Change §6.1's "Key fault tests" for the cards. Server pause or wrong Unit ID gives **no report** and a growing contact age, not "UNAVAILABLE and a growing contact age". TEL-04's done-when list already has the right sentinel and exception-02 item and the right contact-age item. Add: "a server pause produces no admitted report for the paused boundaries".
- Expose the transport-outcome counters on the poller's local output (stdout or a JSON status file). TEL-04 asserts them.
- Classify exceptions exactly as in the table above (TEL-02 maps 01, 02, 03, 04, 06, 0A and 0B).

### The implementer must not

- Add fields to `GatewayDiagnosticsV1`, the envelopes or the central API.
- Make any value repetition affect quality, holds or analytics.
- Publish `UNAVAILABLE` for an unanswered read.

---

## Protected seams (October)

1. **The gateway boundary.** Every field source enters as `DeviceReport` text over the authenticated IPC `admit`. Nothing under `field/` writes the ledger, envelopes, batches or central rows. Gateway code is unchanged, including the IPC op table, `_check_report`, holds and the uploader.
2. **The snapshot.** It stays SIMULATED-only, with conversions `IDENTITY`, `ENUM` and `IDENTITY_KWH` (`snapshot.py:32`, `:263-264`). Scaling and time rules live only in the field profile.
3. **The contracts.** `DeviceReport` V1 (including its schema ID), SourceEnvelope V3 timing rules, `ENVELOPE_QUALITIES` and `ENVELOPE_UNAVAILABLE_REASONS` are not changed.
4. **Provenance.** No publication is attached to field evidence. UNKNOWN / `NO_POSITIVE_BINDING` is the expected October result. A real-source class is a contract ruling (TEL-09 or the pilot).
5. **Money.** `money-eligibility-1`, the CURRENT PRICED head, `source_gate` and the per-domain permitted classes are unchanged. No field-source special case is added.
6. **Roles.** `MINIGRID_ROLES*` are unchanged. No DC role and no site-total role are added.
7. **Dependency direction.** The new field rules are additive. No existing check is loosened or reordered.

## Card corrections TEL-00 must apply before TEL-01

TEL-00's stop condition applies: "any ruling contradicts a card: revise the card first."

- **TEL-01:**
  - the done-when item changes as given in D10;
  - add `output_resolution` and the `quantize_half_even` reuse;
  - the check changes are listed in D4;
  - `publish.py` uses the op set in D4;
  - `field/tests` has no `conftest.py`.
- **TEL-03:**
  - observations come from the pinned JSONL (D4);
  - profile rows are 808, 809, 810 and 843 only, so consumption is dropped (D5);
  - the emulator's per-phase split must be exact and stated, for example the whole value on L1 and 0 on L2 and L3;
  - **new stop condition:** if any bound observation value is not exactly representable at the register resolution through the profile's `e`, stop and report. Do not round in the emulator.
- **TEL-04:**
  - the poller calls `seal` and then `release_run` (its own reference) after admitting;
  - activation is done by the harness;
  - "server pause produces no admitted report" is added (D6).
- **TEL-06:**
  - the collector uses the same op set;
  - rows whose interval differs from the profile span are refused (D10).
- **§1 G8 / TEL-13.** The least-privilege adapter scope later becomes {`identity`, `admit`, `seal`, `release_run`, `diagnostics`}, not {`identity`, `admit`, `diagnostics`}.

## Owner decisions (with recommended defaults)

- **D1: labelling of October evidence.** Recommended: **option (c)**.
  - No publication; provenance reads UNKNOWN; every demo surface and claim record says "emulated interface" or "illustrative format", and says that the values come from a simulator run.
  - The positive alternative today, `REGISTERED_SIMULATION`, would wrongly make field evidence money-eligible (D5(d)).
  - A per-route class comes later (TEL-09).
- **D2: Sites for the October proofs.** Recommended: **the authorised `*_test` database only**, with one Kobo-derived Site per proof created by the tests, and no product demo-database Site in October. This keeps within the test-database authorisation and keeps emulated evidence away from demo screens.
- **N1 (new): what 30 October can show.** Recommended: **accept** that the telemetry path shows accepted evidence, a provenance read and fault outcomes, but **no Finding and no money**. The GX profile binds no generator role, so dispatch records `NO_GENERATOR_STATE`. Adding generator rows to an unpinned, third-party layout to get a Finding on screen would trade credibility for visuals, against the owner's stated priority.
- **Unchanged:** D7 (no hardware spend; choose O1 after TEL-05), D8 and D9 as in §14. D3 (EV normaliser placement) remains an Architect ruling that is not needed before proof C.
