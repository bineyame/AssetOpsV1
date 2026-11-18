# T026 phase 1 handoff (contract and gateway, AC1-AC9, AC11-AC12)

Branch `task/T026-dispatch-capable-evidence`, on top of `5fed927`. Commits:
`ff01f22` (envelope schema 2, parser carries), `fe51513` (profile 5, mini-grid
v3, template v3, records, holds, degraded scenario), `b571b05` (suite
expectations), the R3 test hardening, and this handoff. No named stop was hit.

## Contract-version reading: still 9

`EXECUTION_CONTRACT_VERSION = 9` (`contracts/assetops_contracts/execution_contract.py:400`).
`git diff main -- host/tests/contract9_gate contracts/assetops_contracts/execution_contract.py`
is empty, and the full host suite (gate included) passes. Every change reaches
new Drafts only: publication profile 5, `mini-grid` v3, template v3 and the new
scenario id are added beside what existed. Profiles 3/4 still stage through the
fuel-only schema-1 mapping (`gateway_mapping_for`), no existing model's
trajectory gained state, no reporting-path cause changed meaning, nothing was
added to `FrozenWorldInputs` or the frozen run record, and no new refusal or
block reaches an existing document.

## Stage size and per-step write cost at the 8 h window

Method: `.agent/T026-stage-measure.py` (run from `host/`). Prolonged world,
03:00-11:00Z, 5-min step (97 boundaries), stepped one boundary per control on
the in-process Kobo v3 Site; times `HostLabExecution._stage` per control with
`time.process_time` (15.6 ms resolution on Windows; the machine was loaded, so
wall time was not usable). Two runs each:

| | envelopes | final stage | bytes written per run | `_stage` CPU, last 10 mean | p95 all steps |
| --- | --- | --- | --- | --- | --- |
| `mini-grid` v2 / profile 4 (baseline) | 0 | 674 B | 66 KB | 17 ms | 31 ms |
| `mini-grid` v3 / profile 5 | 333 | 267 KB | 13.5 MB | 39-45 ms | 47 ms |

First measurement before tuning was ~155 ms (wall) per step: profiling showed
re-verifying the persisted stage and rebuilding/validating every envelope
(`strptime`) dominated, not the write. Applied, without any format change:
verified-text cache in `JsonSourceStages` (`host/source_stages.py:59`, bytes
still re-read and compared every time), a conversion memo in `publish`
(`memo=`, `host/lab_execution.py:526`), slice-based instant parsing, and an
equality fast path before the canonical-bytes comparison in `admit`. No stated
budget is exceeded (the nearest stated server budget is T025e's 50 ms p95,
which is the history-delta read, not the stage); the "fewer writes" fallback
and append-only were NOT taken. Stage is still written once per control,
whole, as T023 left it. Phase 3 must re-measure AC15 (step totals grew).

## AC status (evidence: `host/tests/test_t026_dispatch_evidence.py` = H,
## `simulator/tests/test_t026_schema2.py` = S)

- **AC1 met.** Envelope schema 2 (`source_envelope.py:101`, families `:117`,
  per-family key sets, enum members as text); schema 1 read unchanged
  (`READABLE_ENVELOPE_SCHEMA_VERSIONS`, schema-1 mapping persists without the
  new key: S `test_a_schema_one_mapping_persists_exactly_as_before`; all T023
  staging tests green). Stage schema stays 2; its `envelope_schema` states the
  frozen mapping's version. Profile 5 `profiles.py:1600`; dispatch mapping
  `gateway/mappings.py:93`.
- **AC2 met.** `pv-inverter-controller/available-power`,
  `battery-pcs-controller/discharge-capability` measured by `mini-grid` v3
  (`packs/mini_grid.py:1040`, product `profiles.py:1265`); under v2 they are
  no reporting path (H `test_a_model_that_measures_no_capability_publishes_none`).
- **AC3 met.** POLICY records: version = Foundation version, effective start =
  Foundation valid-from, source `FOUNDATION`, control + component (none for Site
  Controls, published as `site-controller`). H `test_policy_records_carry_...`.
- **AC4 met.** OVERRIDE_COMMAND records (occurrence = `source_time`,
  effective interval, actor `OPERATOR`) from frozen CONTROL override windows;
  present, missing (`override-record-reporting-availability`) and delayed
  (`override-record-publication-delay`) cases: H tests `..._present_...`,
  `..._missing_override_record_is_none_observed...`, `..._own_delayed_case`.
- **AC5 met.** Strict validation per family; R3 (`fullmatch`), R2 (`1/0`,
  non-UTF-8 stage) fixed: S `TestParserCarries`, H `test_a_corrupt_stage_...`.
- **AC6/AC7 met.** Degraded scenario `config/scenarios/kobo-mini-grid-degraded-evidence.yaml`
  (v1, pinned, names no site): one hour discharge-capability gap, one SOC
  publication held 07:00:00Z -> published 07:10:03Z, override record missing.
  H `test_the_gap_...`, `test_the_delay_moves_publication_time_only`,
  `test_gap_and_delay_change_publication_only`, `..._reading_series_identical`.
- **AC8 met.** Status staged as a member (`STOPPED/STARTING/RUNNING/FAILED`,
  mapping-declared, unknown member refused); T025b gap/stale untouched; carry
  "enum check before skip" with all-dropped and all-suppressed (S
  `TestTheEnumCheckPrecedesTheSkip`).
- **AC9 met.** Canonical text and the frozen mapping (with its schema version)
  persist byte for byte (H `test_each_world_stages_...`); T023 rules unchanged.
- **AC11 met.** Healthy (evening, 09:00-17:00Z), prolonged and degraded each
  stage ELIGIBLE, reconstructible datasets with every C signal and unit; real
  `INTERVAL_MEAN` and `UNAVAILABLE` envelopes in a shipped run.
- **AC12 met.** Only allowlisted channels cross (irradiance stays off); no
  write path to Site history was added.
- Checks: simulator 244 passed; backend 1375 passed; host 551 passed (after
  the one T025g lineage expectation 2->3); `check-architecture` and
  `check-agent-workflow` passed. Guard probes `.agent/T026-guard-probes.py`:
  10 of 10 CAUGHT (R3 x2, R2 x2, enum order, member allowlist, delay, hold
  refusal, record gap, profile-to-mapping).

## Decisions taken inside the rulings (reviewer attention)

1. **The delay is the hold window.** The scenario parser refuses any duration
   parameter (deliberate rule), so a delay entry carries no magnitude: a
   publication due inside its window is released at the window's end
   (`PublicationDelayWindow`, `observation.py:603`). No frozen-run field added.
2. **Reorder bound** read per path: a hold longer than the path's cadence (or
   holding two override occurrences) would batch releases -> refused at setup,
   new refusal kind `PUBLICATION_DELAY_REFUSED` (`service.py:3352`).
3. **Override records** are the scenario CONTROL overrides (stop threshold,
   reserve) executed as operator commands. The stop-60 header says its override
   is "not operator evidence"; under profile 5 it now publishes a record.
4. **No shipped world curtails PV**, so available PV equals PV output in every
   shipped run; the capability/output distinction shows on the battery.
5. Healthy world runs on `mini-grid` v3 although its header still says v1; the
   scenario was not bumped (comments are not content).
6. API stage rows (phase 3 to refine): records show `measurement` = family and
   `quality` = `RECORDED`; rows and mapping entries gained `family`/`members`;
   member values are text. The frontend guard accepts these.

## What phase 2 needs

- Record source: `generate_records(boundaries, session.records)`
  (`simulator/assetops_simulator/observation/records.py:39`); `RecordObservation`
  (`contracts/assetops_contracts/operational_records.py`) carries outcome
  `REPORTED`/`SUPPRESSED_BY_GAP` and `event_id` (Lab-only).
- Delays: `session.reporting.delays` + `session.records.delays`;
  `publication_delay_minutes` (`observation.py:644`). The reading series and
  its digest are unchanged by a delay; only envelopes' `published_at` move.
- Families to classify for history: reading attempts for the two capability
  signals and status (append), policy records (static, at boundary 0),
  override records (append at occurrence; a late one is a new row at its
  publication boundary).
- Session wiring: `host/lab_execution.py` start (`:2076`), `_stage` (`:2254`).

## Open risks

- Step server time grew with profile 5 (more readings projected); AC15 is phase 3.
- `var/` Sites from template v2 read BEHIND and cannot show capability; the
  owner reviews on a Site created from template v3 (no agent created one).
