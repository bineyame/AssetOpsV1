# Review F0 (DIESEL-F0 / F0r, Kisiwa fuel-events probe)

Reviewer: fresh Claude (Opus), independent of the builder. Branch `task/DIESEL-F0-kisiwa-fuel-probe` at
`64de3003a` (worktree `AssetOpsV1-f0`); merge-base with main = main = `840d5dade`. Judged against
`.agent/build-sheet-DIESEL-1.md` §8.3, §8.2a, §9.1-§9.4, §9a, §9b.

## Verdict: ACCEPT

No High or Medium findings. Three Low findings, none blocking; they are notes for K0 and K3.

## Checks I ran (results as observed)

| Check | Result |
|---|---|
| `tools/probe_kisiwa_fuel.py --check` (fresh process, PYTHONPATH pinned to the f0 worktree, plan2 venv) | `probe result current`, exit 0, 35 s |
| `tools/probe_kisiwa_nights.py --check` (D0, F10) | `probe result current (G6 pass)`, exit 0 |
| `pytest host/tests/test_probe_kisiwa_fuel_band.py -q` | 7 passed |
| Probe-local v7 vs K1a branch (`AssetOpsV1-k1a` @ `1a4d3b5c5`), `repr` of sim model and product profile, addresses scrubbed, `PYTHONHASHSEED=0` | byte-identical sha256 for both (sim `61a2df31…`, profile `722b13c6…`). Without a fixed hash seed the hashes differ only because frozenset repr order is hash-randomised |
| `seeded_uuid4()` restore, in-process | inside: `uuid.uuid4` and `foundation_service.uuid4` patched; after exit: both are the original; no module left holding the fake |
| `git diff main HEAD --stat` | exactly 6 files: `.agent/DIESEL-F0-probe-results.md`, `.agent/DIESEL-F0/{bindings draft, action log draft, probe-result.json}`, `host/tests/test_probe_kisiwa_fuel_band.py`, `tools/probe_kisiwa_fuel.py`. No product file, no `backend/tests` file, no D0 file (`tools/probe_kisiwa_nights.py`, `.agent/DIESEL-D0/`) differs |

Not run (per dispatch): no DB, no suites, no frontend. The coordinator's §9b (a)-(d) mechanical checks were not
repeated beyond the single `--check` above and the 6-line JSON diff (confirmed: `snapshot_sha256`, the four
binding ids, and `example_fuel_level_report_text`).

## 1. Integrity (pre-registration and order)

- `54ef019e1` (19:50) commits the action log and the expected outcome before the tool exists (`8370a0689`, 19:53).
- The action log has been touched by no later commit (`git log` on the file: only `54ef019e1`).
- The "Pre-registered expectation" section of the evidence file is unchanged after `54ef019e1` (the diff starts
  below line 27); later sections are appended.
- `fuel-balance-1` constants and `balance()` are unchanged from `8370a0689` to HEAD (no `-`/`+` line touches
  ACCURACY, MARGIN, TOLERANCE, FACTOR, MATERIALITY, EDGE_SEARCH, GAP_LONGER, START_FUEL, RUN1_START or the residual
  lines).
- F0r addendum `3a147f96e` precedes the (c) code `bf70fd180`; R3a fixture `77ad11f17` and addendum `77958a20c`
  precede the run code `ab33768d7` and the result `9e5fad4e1`. The F8 failure was reported and left in place at
  `9e5fad4e1`; the fix came only after the R3b ruling.
- The 105-min gap was the builder's own pre-run expectation (lines 26-27), not a retrofit.

## 2. Operational-action path (F0a)

- `execute_day` builds every run from D0's `day_document` unchanged (`tools/probe_kisiwa_fuel.py:392`), and
  `scenario_is_weather_and_loads_only` (`:369-380`) rejects any non-EVENT, non-WEATHER/LOAD, non-FORCING_INPUT entry,
  any mention of `fuel-tank`, `reporting`, `CAUSAL_INPUT`, `INTERVENTION` or `REPORTED_OBSERVATION`, and any
  `observation_sources`. Gate result: empty list on all 10 runs.
- `apply_actions` (`:170-212`) adds the delivery (INCREASE POINT), the removal (DECREASE WINDOW) and the unplugged
  sensor (a `FrozenReportingPathCondition` on `fuel-level-reporting-availability@fuel-tank`) to the frozen run with
  `dataclasses.replace`, after setup returned READY. Origin and content hash ride in the event id prefix and in
  `intervention_history`, the carrier §9.4 item 3 accepts.
- `:510-517` asserts the added causes appear in the host's frozen world inputs (`execution.inputs`) with matching
  history entries, so they reached the kernel. F2 shows the kernel applied them: 40/3 L at run 4 steps 120-128
  (sum 120) and -300 L at run 2 step 227. No other step departs from the tank law.
- The sensor span reached the reporting inputs: F5 shows offsets 600-675 `SUPPRESSED_BY_GAP` and no reading in
  [590, 680), with readings at 570/585 and 690/705.
- I checked every action instant against the declared table: delivery run 2 offset 1140 (10:00 local), removal
  run 4 offset 600 (01:00), sensor 590 for 90 min, dip 960 (07:00), seal and sensor fix at the run 6 start, dips
  at offsets 180 and 900 in runs 6-10. All match §8.3.

## 3. Registered path (c)

- `register_kisiwa` (`:250-268`) calls the product's `import_site` (tenant "demo", clock 09:00Z) and
  `convert(store, BindingService(store, clock 09:30Z), tenant, site, fixture)` over `foundation_fakes`'
  `InMemoryFoundationStore`, as `backend/tests/test_s1_bindings.py` does.
- `Registered.draft` (`:325-347`) builds `RunSetupService(FakeRuns(), FakeSites(()), FakeScenarios(...),
  model_profiles=..., publication_profiles=..., now=..., registered_bases=RegisteredLabBasis(ImportedSiteRegistry(
  FoundationService(store, "demo", clock))))`. This is the same construction as `setup_service` in
  `backend/tests/test_s2_registered_basis.py:83-93`; only the store and the profiles differ. No hand-built
  selection; `FakeSites` is empty. Every run asserts READY and a non-null `registered_basis` (`:394-395`).
- Fixture: 12 rows, `minigrid-roles-2`, `declare_signals: []`, the ruled note verbatim. `generator-status` carries
  `legacy_mapping_id: "generator-status"` with the ENUM map; the two capability rows are kW->kW IDENTITY with their
  legacy ids. Matches §9a.
- Foundation version 1 is reported and explained (no later revision, as R3b confirms).

## 4. Probe-local v7

- `probe_v7` (`:289-306`) is §9.2's content: version 7, V6 statement + V7_SENTENCE, stock handler restated with the
  ruled sentence, `fuel.SAMPLE_HANDLER` reused, product supported roles `{CAUSAL_INPUT, REPORTED_OBSERVATION}` with
  the restated statement. My repr comparison against the K1a branch's real `MINI_GRID_V7_MODEL` (sim and product)
  is byte-identical.
- The required line is in the JSON (`assumptions.probe_local_v7`) and bold in the evidence file (line 95).

## 5. Fuel-balance maths

- `balance` (`:106-134`) is §8.3 term for term: margin 2a = 20, delivery tolerance 1 %, use_low = 9/10 loaded,
  use_high = 11/10 (loaded + idle_h x r), exact Fractions; state order UNEXPLAINED, EXCESS, WITHIN_MARGIN,
  BELOW_MATERIALITY gives the ruled partitions. The opening/closing rule (`:618-619`) and the gap (`:100-103`,
  window edges as points, spans > 60) match.
- By hand, with night use 26057/600 = 43.428 and 0 idle minutes (true on every night in the JSON):
  incident low = 163.428 - 47.771 - 20 = 95.657, high = 163.428 - 39.085 + 20 = 144.343; clean nights
  ±24.343; delivery night -256.572 + 300 ∓ 3 ... = ±27.343. The JSON's exact values (573943/6000, 866057/6000,
  ±146057/6000, ±164057/6000) agree.
- Night 4 is UNEXPLAINED from both sources with gap 105; nights 1-3 and 5-10 are WITHIN_MARGIN with gap 0 from
  both; none NOT_ASSESSED. The readings band equals the true band because the -0.5 L bias cancels and every
  opening/closing sample arrived.
- Pinning: `test_probe_kisiwa_fuel_band.py` pins the incident band exactly, the delivery-night low edge exactly
  (so the tolerance sign and the 20 L margin), the 40 L edge, EXCESS, missing edges, and 60/61-min gaps. The
  actual per-night results are pinned by `--check` against the committed JSON. A broken margin, factor, tolerance
  or materiality would fail. Gaps in the pinning are in L2 below.

## 6. F8 fix

- `seeded_uuid4` (`:740-769`) is local to the probe, patches `uuid.uuid4` and every module-level `uuid4` binding
  (including ones bound lazily during the run, swept on exit), and restores in `finally`. My in-process check
  confirmed the restore. No product or `backend/tests` file is touched. See L3 on scope.

## Findings

### L1 (Low): the action log's `log_id` does not match the K0 file-naming rule
- `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml:18` says `log_id: kisiwa-001-operational-actions`.
  §9.3 item 2 says the request key is `{"log_id": "kisiwa-001", "log_version": 1}` and the file is
  `{log_id}-v{log_version}.yaml` = `kisiwa-001-v1.yaml`, and K0 is to promote this file verbatim.
- Failure scenario: if K0's loader checks the file's internal `log_id` against the request key (a natural
  validation), the verbatim-promoted file is refused or K0 quietly edits a pre-registered file.
- Not an F0 defect (the file was pre-registered before §9.3 existed and §9.4 forbids editing it). Fix: the
  Architect rules in K0's pre-flight whether the internal id is kept, changed at promotion, or not validated.

### L2 (Low): the "readings" source uses true-trajectory use terms, and two band edges are not pinned by tests
- `tools/probe_kisiwa_fuel.py:620-625`: `loaded_litres` and `idle_hours` come from D0's `measure_night` on the
  true trajectory (accepted generator energy) for both sources. §8.3 defines use "from the generator readings per
  5-minute slot". F9(ii) only names opening and closing as read from F5, so the gate as written is met, but the
  evidence file does not say plainly that use is not read from published generator readings.
  Failure scenario: K3 computes use from generator-power readings with dropouts or noise; its night bands differ
  from F0's, and someone treats F0's ±24.343 as a guarantee for K3.
- `host/tests/test_probe_kisiwa_fuel_band.py` always uses `idle_hours=0`, so the `idle_h x r` term of `use_high`
  is untested; and no test sits on `residual_low == 0` (WITHIN_MARGIN vs BELOW_MATERIALITY) or asserts the
  delivery night's `residual_high`. Failure scenario: dropping the idle term or using `<` for `<=` would leave
  the tests green (Kisiwa has 0 idle minutes, so `--check` would also stay green).
- Fix (for K3, not F0): K3's own tests cover the idle term and the zero edge; K3's evidence states which source
  each term comes from.

### L3 (Low): the seeded-uuid4 scope is wider than ruled, disclosed only in part
- `tools/probe_kisiwa_fuel.py:776-777` wraps all of `build()`, not just the import and conversion
  (§9b item 1). So run ids (`backend/assetops_backend/runs/identity.py:61`, `uuid.uuid4().hex`) are seeded too.
  That is needed for byte-equality (the report key hashes the run id) and harmless (probe-only, restored).
- The evidence file says "wraps `build()`", but the commit message says "for the in-memory import and conversion"
  and the patched-name list doesn't name run-id allocation as a beneficiary.
- Failure scenario: none at run time; a later reader may think run ids are naturally deterministic. Fix: none
  needed for merge. Optionally, add one sentence to the evidence file.

## Residual risk not named in the packet

- F0 proves the bridge only with the origin carried in the event id. K0's real origin field and omit rule are
  unproven until K0's byte-equal tests run.
- The band has margin only because night use is a steady 43.4 L with zero idle. Kisiwa nights with idle running
  would widen `use_high` by 11/10 x 4.9 L/h, which F0 never exercised.
- F5's cadence check covers run 1 only. Other runs are covered indirectly by bias_ok, F6 counts and F9 edges.
