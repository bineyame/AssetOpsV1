## 9f. Ruling DIESEL-1-R3f: K0 pre-flight (Q1–Q10)

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `1fc354bee` (K1 merged). K0 worktree `C:\Users\assef\Bineyame\AssetOpsV1-k0`, branch `task/DIESEL-K0-action-bridge`, read clean at `1fc354bee`.
- **K0's card is §9.3 + §9c.3 items 1 and 4 + this section. Where they differ, §9f wins.** The main amendment: the origin fields live on the backend frozen records only. The kernel-facing contract, the host and the trajectory identity are **not** edited (Q1, Q2, Q4).
- Owner decision in force, verbatim: `.agent/owner-scenario-data-2026-11-07.md` ("these are injected through operational actions").

**Code facts the Architect verified on the K0 worktree:**
- `B/runs/source_publication.py:27-33`: `run_identity_sha256` hashes `render_run_document(run)`'s `run_id`, `created_at`, `deterministic_identity` and `registered_basis`. Any render change to the identity moves the Postgres `evidence_publication` digest, so the omit rule is load-bearing there too.
- `B/runs/parsing.py:773-777` (`FrozenForcing.issued_by`) and `:874-888` (`signal_resolutions`, with its parse at `:1427-1442` refusing a stored empty list) are the two omit-when-default precedents. §9f uses both.
- `contracts/assetops_contracts/trajectory.py:570-589`: causes are hashed as 11-tuples, `intervention_history` is hashed, and reporting conditions are not (`IDENTITY_FIELDS_READ` at `:639-662` is per `FrozenWorldInputs` field).
- `contracts/assetops_contracts/observation.py:475-493`: `ReportingPathWindow` is a per-signal projection of a condition, not its counterpart.
- `B/runs/provenance.py:434-536`: provenance reads only the `DeterministicIdentity`, with every cause and condition row hard-coded `answered_by="SCENARIO"`.
- `B/runs/models.py:193-201` `FROZEN_INPUT_ANSWERERS` has no `OPERATIONAL_ACTION` member.
- `B/runs/service.py:464-491`: `_freeze`, then `signal_resolutions`, then `_decide`. `_decide` (`:1824-1870`) reads causes and conditions from the scenario, not the identity. `_cadence_reasons` and `_publication_reasons` ignore causes and conditions.
- `B/runs/refusals.py:111-154` holds the kinds. `backend/tests/test_run_setup.py:2091` asserts `produced == RUN_SETUP_REFUSAL_KINDS`, so every new kind needs a producer in that test. `F/shell/RunSetupFrame.tsx:1387` returns `null` for an unknown kind, which shows the backend message, so no frontend edit is needed.
- `backend/tests/test_run_setup.py:1600-1760` classifies every frozen-record field as rendered or `not_rendered` (with a reason). New fields must be classified there.
- `B/simulator_lab_api.py:2460-2467` composes `RunSetupService`, and the Lab identity wire at `:2250-2305` carries no causes. Neither the wire nor the frontend changes.
- `.agent/DIESEL-F0/probe-result.json:8` has `actions_sha256 = 77777c82d82298ffba77a130f8d9ea2c6bb9a80c491ba4b2ac5248c4b735b634`. At `:2852-2858`, run 2's non-generator step is `step 227, offset 1135, -300`.

### 9f.1 Rulings

**Q1. Approved: no contract class change for conditions.**
- `ReportingPathWindow` stays as it is.
- `origin` and `action_ref` go on `B/runs/models.py` `FrozenReportingPathCondition` only.

**Q2. Corrected: `DeclaredCause` is not changed either, and the host is not edited.** This amends §9.3 item 1, which listed `DeclaredCause`, and confirms §9.3 item 6, "host: no change".
- Origin is provenance. The kernel boundary carries physics.
- The world identity already tells an action cause apart from a scenario cause by two hashed facts:
  - its `event_id` (`"{action_id}/{effect}"`);
  - its `intervention_history` entry, which carries the action's content hash.
- Adding the fields to `DeclaredCause` would either be dead weight (the host does not pass them) or change `frozen_inputs_identity` (the host does pass them). It buys no test and adds a hash risk.
- Files therefore **not** edited: `contracts/assetops_contracts/world_inputs.py`, `contracts/assetops_contracts/trajectory.py`, `contracts/assetops_contracts/observation.py`, `host/execution_adapter.py`, `S/**`. Any need to edit one of them is stop S2.

**Q3. Approved, with the shape below.**
- The identity freezes the log and the effect-bearing actions' display facts.
- Provenance reads only the frozen identity, never the live log.
- Shape: §9f.2 (2).

**Q4. Approved: not in the trajectory hash.**
- The log identity and the per-action tuple are in the run document. So they are in `run_identity_sha256` and in the stored bytes.
- They are not in `frozen_inputs_identity`.
- Same world means the same trajectory identity:
  - Two logs with identical effect-bearing actions give the same world.
  - Any change to an action's content changes its `content_sha256`, so it changes `intervention_history` and the trajectory identity.

**Q5. Approved.**
- `intervention_history` and `operational_action_log.actions` hold the **effect-bearing** actions only: `FUEL_DELIVERY`, and `FUEL_REMOVAL_UNRECORDED`.
- They hold only actions selected for this run (`at` in `[start_time, end_time)`).
- Order: by parsed `at` instant, then `action_id` (code-point order).
- The two lists correspond 1:1 in the same order.
- `TANK_DIP`, `TANK_SEALED` and `SENSOR_POWER_PROTECTED` are validated (§9f.3) but freeze nothing.

**Q6. Approved: refuse, never clip.**
- Code: `OPERATIONAL_ACTION_SPAN_OUTSIDE_RUN`.
- It applies to any selected action whose physical span does not lie wholly inside `[start_time, end_time)`:
  - the removal window `[at, at + duration_minutes)`;
  - the sensor span `[sensor_disconnected.at, sensor_disconnected.at + duration_minutes)`.
- The sensor span may start before the action's `at`, as in F0 (`21:50Z` against `22:00Z`), but it must start at or after `start_time`.
- Offsets must also meet the alignment rule the existing setup applies to scenario entries (`_refuse_entries_outside_the_interval`). The builder mirrors that rule exactly, under this code.
- An `at` with non-zero seconds is refused under this code too.

**Q7. Approved, narrowed to the registered timeline path.**
- `operational_actions` is accepted only on the timeline `_freeze` path **with a registered selection** (`selection is not None`).
- It is refused with `OPERATIONAL_ACTIONS_UNSUPPORTED_PATH` in three places:
  - on the cold document draft (`_create_cold_draft`);
  - on the EV document draft (`_create_ev_draft`);
  - on a legacy YAML Site (no selection).
- Refusal happens before any freeze work. Nothing is allocated.
- The key is added to the shared `REQUEST_KEYS` (`B/runs/parsing.py:109`). The text of the `REQUEST_INVALID` message that lists the keys grows by one name. Tests that pin that whole message are updated, and this is the only permitted change to existing test expectations.

**Q8. Approved, all four items.**
- An `operational_actions` port on `RunSetupService`.
- `build_simulator_lab_router` and `main.py` pass the file adapter.
- The `host/tests/kisiwa.py` port.
- The default path constant lives in the adapter module only.
- Signatures: §9f.2 (6). The `LabRunner` harness named in §9.3 item 5 is replaced by `host/tests/kisiwa.py`, which K7 uses.

**Q9. Approved.**
- `.gitattributes` gets `config/operational-actions/* text eol=lf` (block in §9f.2 (7)).
- The frozen `sha256` is the LF hash, and it must equal F0's `actions_sha256` (`77777c82…b634`). Inequality is stop S4.
- The stale header comment stays verbatim. It says "DRAFT" and "promotes it verbatim to `config/operational-actions/kisiwa-001-v1.yaml`". The adapter module docstring and the packet each state, in one sentence, that the file is F0's pre-registered draft promoted byte-for-byte and that its header predates §9c.3 L1's file name.

**Q10. Approved, with one addition.**
- The pins are committed **as the branch's first commit**, before any production edit. Git history then proves they predate the change.
- Pins are a new test-data module `backend/tests/k0_byte_equal_pins.py` with literal hex strings, taken from the existing no-DB fixtures:
  - the Kobo draft (`host/tests/kobo.py:108`);
  - one Cold lab draft and one EV lab draft;
  - every shipped scenario's frozen-cause render.
- For each, pin three sha256 values:
  - (a) `json.dumps(render_run_document(run), sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)`;
  - (b) `run_identity_sha256(run)`;
  - (c) the trajectory identity digest (`frozen_inputs_identity` over the host's `frozen_world_inputs(run)`), for each run the host can build world inputs for.
- `run_id` and `created_at` are fixed by the fixtures' seeded and clocked setup. If a fixture is not deterministic across two fresh processes, pin it after removing exactly `run_id` and `created_at`, and say so in the packet.
- Cold and EV have no timeline world inputs, so for them (c) is "not applicable", stated.

**Builder-resolved items, ruled:**
- `CAUSE_ORIGIN_INVALID` for both causes and conditions: **confirmed**. Mechanism in §9f.2 (1).
- `OPERATIONAL_ACTION_LOG_MISMATCH` for an inner id or version that differs from the file name: **confirmed**. It also covers an inner `site_code` that differs from the request's `site_id`.
- In-memory tank parity: **confirmed, read from evidence, not literals.**
  - Run 4 is steps 120–128, 40/3 L each (120 L over 45 min).
  - For run 2, the expected step, offset and litres are read from `probe-result.json` `non_generator_steps`. That is step 227 at offset 1135, −300 in the evidence's sign. It is not typed into the test.
- DB tests on `assetops_k0_test` only: **confirmed.**

### 9f.2 Exact specification

**(1) Frozen records (`B/runs/models.py`).**
- `FrozenCause` and `FrozenReportingPathCondition` each gain two fields, after their existing fields and with defaults:
  - `origin: str = "SCENARIO"`;
  - `action_ref: str | None = None`.
- `CAUSE_ORIGINS = frozenset({"SCENARIO", "OPERATIONAL_ACTION"})`.
- `ACTION_REF_PATTERN = r"^[a-z0-9][a-z0-9-]{0,63}:[0-9a-f]{64}$"`, which is `"{action_id}:{content_sha256}"`.
- `__post_init__` raises `ValueError` with a message starting `"CAUSE_ORIGIN_INVALID: "` in these cases:
  - origin not in `CAUSE_ORIGINS`;
  - `OPERATIONAL_ACTION` with `action_ref` None;
  - `SCENARIO` with `action_ref` not None;
  - an `action_ref` that does not match the pattern.
- New `FrozenOperationalAction(action_id: str, kind: str, actor: str, at: str, content_sha256: str)`.
  - `kind` is one of `FUEL_DELIVERY` or `FUEL_REMOVAL_UNRECORDED`.
  - `at` is the log's text, verbatim.
- New `FrozenOperationalActionLog(log_id: str, log_version: int, sha256: str, actions: tuple[FrozenOperationalAction, ...])`. `actions` may be empty: a requested log with no effect-bearing action in the interval.
- `DeterministicIdentity` gains `operational_action_log: FrozenOperationalActionLog | None = None`, last, with a default.
- `FROZEN_INPUT_ANSWERERS` gains `"OPERATIONAL_ACTION"`.
- Update the `DeterministicIdentity` docstring sentence that says `intervention_history` is always empty: it is empty unless the run names an operational-action log.

**(2) Render (`B/runs/parsing.py` `render_run_document`).**
- **Cause.** Append `"origin": "OPERATIONAL_ACTION", "action_ref": item.action_ref` to the existing cause dict **only when** `item.origin == "OPERATIONAL_ACTION"`. Use the `**({…} if … else {})` pattern from `:773-777`. A scenario cause renders exactly today's keys.
- **Condition.** The same, for each reporting-path condition.
- **Identity.** Append `"operational_action_log"` only when it is not None:
  `{"log_id", "log_version", "sha256", "actions": [{"action_id", "kind", "actor", "at", "content_sha256"}, …]}`.
  Use the `signal_resolutions` pattern (`:874-888`). Here, unlike there, an empty `actions` list **is** written, because the log was requested.

**(3) Parse (`B/runs/parsing.py`).**
- Strict, mirroring render. Every error is `RunConfigurationInvalid`, and an origin-family error message starts `"CAUSE_ORIGIN_INVALID: "`.
- Cause or condition:
  - `origin` absent means `SCENARIO` with `action_ref` None.
  - `origin` present must be exactly `"OPERATIONAL_ACTION"` and must have `action_ref`. An explicitly written `"SCENARIO"` is refused, because the writer never writes it. That keeps one stored form per record.
  - `action_ref` without `origin` is refused.
- `operational_action_log`: absent means None. Present means every key is required with the right type, and unknown keys are refused.
- **Cross-check, after the whole identity is parsed.** These must hold together:
  - the `intervention_history` entries starting `"OPERATIONAL_ACTION:"` equal, in order, `["OPERATIONAL_ACTION:" + a.action_id + ":" + a.content_sha256 for a in log.actions]`, and there are none when the log is absent;
  - every `action_ref` on a cause or condition names an action in `log.actions`;
  - every action in `log.actions` is named by at least one cause.
- Any break of the cross-check is `CAUSE_ORIGIN_INVALID`.
- The same cross-check runs in `operational_actions.py` before setup returns, as a self-check. Its failure is a defect (assert), not a refusal.

**(4) Provenance (`B/runs/provenance.py`).**
- **Cause or condition row with `origin == "OPERATIONAL_ACTION"`:**
  - `answered_by="OPERATIONAL_ACTION"`;
  - `answered_by_detail = f"Operational action {a.action_id} ({a.kind}, by {a.actor}), log {log.log_id} v{log.log_version}"`, where `a` is looked up in `identity.operational_action_log.actions` by `action_ref`'s action id.
  - `field` and `value` are built exactly as today.
- Scenario rows stay byte-equal.
- **Log row.** When the log is present, add one row after the reporting-path rows:
  - `identity_field="operational_action_log"`, `field="Operational action log"`;
  - `value=f"{log.log_id} v{log.log_version}, sha256 {log.sha256}"`;
  - `answered_by="OPERATIONAL_ACTION"`;
  - `answered_by_detail=f"{len(log.actions)} actions with a physical effect in this run"`.
  - When the log is absent there is no row, so provenance is byte-equal.
- **Field classification in `test_run_setup.py`:**
  - rendered: `FrozenCause.origin`, `FrozenReportingPathCondition.origin`, and the log's `log_id`, `log_version`, `sha256`, and `actions` (through the log row), plus `FrozenOperationalAction.action_id`, `.kind` and `.actor` (through the detail);
  - `not_rendered`, with these reasons:
    - both `action_ref` fields: "the action id reaches the row's detail; the content hash is on the intervention-history row";
    - `FrozenOperationalAction.content_sha256`: "on the intervention-history row";
    - `FrozenOperationalAction.at`: "the cause row's span states when, as an offset".

**(5) Request, port, adapter and loader.**
- **Request key** (`parsing.py` `parse_run_setup_request`): `operational_actions`, optional.
  - When present it must be an object with exactly `log_id` (str matching `^[a-z0-9][a-z0-9-]{0,63}$`) and `log_version` (int ≥ 1, not bool). Anything else is `REQUEST_INVALID`.
  - `RunSetupRequest` gains `operational_actions: OperationalActionsRequest | None = None` (a frozen dataclass with `log_id` and `log_version`).
- **Port** (`B/runs/ports.py`):
  - `class OperationalActionLogPort(Protocol): def read_log(self, log_id: str, log_version: int) -> OperationalActionLogSource`;
  - `OperationalActionLogSource(sha256: str, document: Mapping[str, Any])`;
  - `class OperationalActionLogUnavailable(Exception)`.
- **Adapter** (new `B/runs/adapters/yaml_operational_action_log.py`):
  - `DEFAULT_OPERATIONAL_ACTIONS_ROOT` is the repo's `config/operational-actions`, resolved the way `yaml_run_store.py` resolves its config root. This is the only place in `B/` that names the path.
  - `class YamlOperationalActionLog(root: Path = DEFAULT_OPERATIONAL_ACTIONS_ROOT)`.
  - It reads `{root}/{log_id}-v{log_version}.yaml`:
    - `text = read_text(encoding="utf-8")`;
    - `sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()` (LF-normalised, the F0e rule);
    - `document = yaml.safe_load(text)`.
  - A missing or unreadable file, a YAML error, or a non-mapping document raises `OperationalActionLogUnavailable`.
- **Loader and freeze** (new `B/runs/operational_actions.py`, pure, with no I/O): `freeze_operational_actions(request, identity, log_source, *, model, start, end) -> DeterministicIdentity`. In order:
  1. Validate the document. Top-level keys are exactly `log_id`, `log_version`, `site_code`, `timezone` and `actions`. Each action has `action_id` (the pattern above, unique in the log), `kind` (one of the five), `at` (`YYYY-MM-DDTHH:MM:SSZ`), `actor` (non-empty str) and `component_id`. Kind-specific keys:
     - `FUEL_DELIVERY`: `volume_l > 0`, `ticket`, `recorded_after_minutes`;
     - `FUEL_REMOVAL_UNRECORDED`: `volume_l > 0`, `duration_minutes > 0`, optional `sensor_disconnected {at, duration_minutes > 0}`;
     - `TANK_SEALED` and `SENSOR_POWER_PROTECTED`: optional `note`.

     Any other key, or a bad type, is `OPERATIONAL_ACTION_LOG_INVALID`.
  2. Inner `log_id` or `log_version` differs from the request, or `site_code` differs from `request.site_id`: `OPERATIONAL_ACTION_LOG_MISMATCH`.
  3. `content_sha256 = sha256(json.dumps(action, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii"))` over the parsed action mapping (F0 `load_actions`).
  4. Select the actions with `at` in `[start, end)`.
  5. For each selected action, run §9.3 item 2's checks, in log order:
     - `OPERATIONAL_ACTION_COMPONENT_UNKNOWN`;
     - `OPERATIONAL_ACTION_STATE_NOT_CAUSAL`, which also covers a frozen identity with no initial `fuel-tank-volume` value or no `fuel-tank-capacity` value, since no bound can then be computed;
     - `OPERATIONAL_ACTION_UNIT`;
     - `OPERATIONAL_ACTION_SPAN_OUTSIDE_RUN` (Q6).

     Then `OPERATIONAL_ACTION_OVER_CAPACITY` and `OPERATIONAL_ACTION_OVER_STOCK`, in exact `Fraction` arithmetic, over the effect-bearing actions in (`at`, `action_id`) order. Effect-free kinds get only the component and interval checks.
  6. Build the effects:
     - `FUEL_DELIVERY` is a `FrozenCause`: `event_id=f"{id}/tank-increase"`, `direction="INCREASE"`, `parameter_id=f"{id}-volume"`, `canonical_value=float(volume_l)`, the model stock's `canonical_unit` and `dimension`, `timing_shape="POINT"`, `offset_minutes` from `at`, `duration_minutes=None`.
     - `FUEL_REMOVAL_UNRECORDED` is the same with `"/tank-decrease"`, `"DECREASE"`, `"WINDOW"` and `duration_minutes`. With `sensor_disconnected`, add a `FrozenReportingPathCondition` with `event_id=f"{id}/sensor-disconnected"`, state `fuel-level-reporting-availability@fuel-tank`, `"WINDOW"`, and the span's offset and duration.
     - Every one of these has `origin="OPERATIONAL_ACTION"` and `action_ref=f"{id}:{content_sha256}"`.
  7. Any new `event_id` equal to a cause, forcing or condition `event_id` already in the identity: `OPERATIONAL_ACTION_EVENT_ID_CONFLICT`.
  8. Return `replace(identity, …)`:
     - `causes` = scenario causes then action causes, in (`at`, `action_id`) order;
     - the same for `reporting_path_conditions`;
     - `intervention_history` extended;
     - `operational_action_log` set.
- **Where it runs** (`B/runs/service.py` `create_draft_run`):
  - After the `signal_resolutions` replace (`:477-482`) and before `_decide`. The two placements are equivalent today (verified above). This one keeps the identity complete before any decision.
  - When `request.operational_actions` is None, nothing is called and nothing changes.
  - When it is set and the port is None, or the port raises `OperationalActionLogUnavailable`: `OPERATIONAL_ACTION_LOG_UNAVAILABLE`.

**(6) Composition.**
- `RunSetupService.__init__` gains keyword `operational_actions: OperationalActionLogPort | None = None`.
- `build_simulator_lab_router(…, operational_actions: OperationalActionLogPort | None = None)` passes it through.
- `B/main.py:677-697` passes `operational_actions=YamlOperationalActionLog()`.
- `host/tests/kisiwa.py`:
  - `KisiwaRegistered.__init__(store, setup_at, actions: OperationalActionLogPort | None = None)` hands `actions` to `RunSetupService`;
  - `draft(document, start, end, model="v7", operational_actions: dict | None = None)` adds the request key only when it is not None;
  - `draft_day` gains the same two optional arguments.
- Every other `RunSetupService(...)` caller is untouched, because the default is None.

**(7) `.gitattributes`**, appended after the R3e block:
```
# DIESEL-1-R3f: operational-action logs are hashed as LF on every host
config/operational-actions/* text eol=lf
```
- `C/operational-actions/kisiwa-001-operational-actions-v1.yaml` is a byte copy of `.agent/DIESEL-F0/kisiwa-001-operational-actions.draft.yaml`'s blob (`git show main:<path> > <new>`).

**(8) New refusal kinds** (`B/runs/refusals.py`, each with a one-line meaning comment, each produced in `test_run_setup.py`'s `produced` set):
- `OPERATIONAL_ACTIONS_UNSUPPORTED_PATH`
- `OPERATIONAL_ACTION_LOG_UNAVAILABLE`
- `OPERATIONAL_ACTION_LOG_INVALID`
- `OPERATIONAL_ACTION_LOG_MISMATCH`
- `OPERATIONAL_ACTION_COMPONENT_UNKNOWN`
- `OPERATIONAL_ACTION_STATE_NOT_CAUSAL`
- `OPERATIONAL_ACTION_UNIT`
- `OPERATIONAL_ACTION_SPAN_OUTSIDE_RUN`
- `OPERATIONAL_ACTION_OVER_CAPACITY`
- `OPERATIONAL_ACTION_OVER_STOCK`
- `OPERATIONAL_ACTION_EVENT_ID_CONFLICT`

`CAUSE_ORIGIN_INVALID` is **not** a setup refusal kind. Setup never builds an invalid origin. It is the message prefix of the model and parse errors in (1) and (3).

### 9f.3 Files (approved list; anything else is stop S5)

- **Edited:**
  - `B/runs/models.py`
  - `B/runs/parsing.py`
  - `B/runs/service.py`
  - `B/runs/ports.py`
  - `B/runs/refusals.py`
  - `B/runs/provenance.py`
  - `B/simulator_lab_api.py` (router signature and pass-through only)
  - `B/main.py`
  - `host/tests/kisiwa.py`
  - `.gitattributes`
  - `backend/tests/test_run_setup.py` (classification, `produced` set, and the REQUEST_KEYS message pin only)
  - any other existing test that pins the full REQUEST_KEYS message text (that line only)
- **New:**
  - `B/runs/operational_actions.py`
  - `B/runs/adapters/yaml_operational_action_log.py`
  - `config/operational-actions/kisiwa-001-operational-actions-v1.yaml`
  - `backend/tests/k0_byte_equal_pins.py` (first commit)
  - `backend/tests/test_k0_operational_actions.py` (L0 and L1)
  - `host/tests/test_k0_kisiwa_actions.py` (parity and L2)
- **Not edited:** `contracts/**`, `host/execution_adapter.py`, `S/**`, `F/**`, `.agent/DIESEL-F0/**`, `T/probe_kisiwa_fuel.py`, M2, M3, `record_channels`, and the envelope schema.

### 9f.4 Tests (localised only; no full suite; DB tests on `assetops_k0_test` only, machine idle)

**L0, no DB.**
1. **Byte-equal, against the first-commit pins** (Q10): all fixtures, all three digests. In addition, `"origin"` and `"action_ref"` appear in no rendered scenario-only run and no stored YAML file. This is §9c.3 (b).
2. **Model and parse refusals:** every `CAUSE_ORIGIN_INVALID` case in (1) and (3), including:
   - a stored `origin: SCENARIO`;
   - a history and log mismatch;
   - a dangling `action_ref`;
   - an orphan log action.
3. **Round-trip** on `YamlRunStore` (render, write, read, equality) and on each in-memory fake run store. An action cause and condition keep both fields and the log. A scenario cause keeps neither. This is §9c.3 (c).
4. **Setup** with an in-memory port over the promoted file's parsed content, for runs 2 and 4. The harness is the in-memory registered Kisiwa used by K1's tests if it runs without a DB; otherwise this test moves to L2. Checks:
   - origin is the field, `action_ref` is `"{id}:{sha}"`, and the `event_id` is `"{id}/{effect}"` with no `OPERATIONAL_ACTION/` prefix (§9c.3 (a));
   - the history equals `["OPERATIONAL_ACTION:" + ref]` and its content hashes equal those in `probe-result.json` `runs[k-1].intervention_history`;
   - the frozen log `sha256` equals `actions_sha256`.
5. **Each new setup refusal kind.** Nothing is written to the run store, and `create_run` is never called.
6. **Provenance rows** for an action cause, an action condition and the log row. Scenario rows are byte-equal.
7. **The no-reader test:**
   - `operational-actions` appears in no file under `B/` except `B/runs/adapters/yaml_operational_action_log.py`;
   - it appears in no file under `F/`;
   - `config/operational-actions` appears only in that adapter and `.gitattributes`.
8. **Adapter.** A CRLF copy of the file in a tmp dir gives the same `sha256` as the LF copy, and the hash equals `77777c82…b634`. A wrong file name gives `OPERATIONAL_ACTION_LOG_MISMATCH`, and a missing file gives `OPERATIONAL_ACTION_LOG_UNAVAILABLE`.

**L2 (`assetops_k0_test`):**
9. **Registered setup and kernel parity** for Kisiwa runs 2 and 4 through `host/tests/kisiwa.py` with `actions=YamlOperationalActionLog()`:
   - the per-step tank account equals F0r's (§9c.3 (d)): run 4 steps 120–128 at 40/3 L, and run 2 per `non_generator_steps`;
   - every other step's non-generator change is 0.
10. **Readback through the Lab API composition** (`main.py` app with the adapter): `POST` a Kisiwa run with the key, then `GET` it. The frozen inputs show `answered_by="OPERATIONAL_ACTION"` rows.

**Checks:** `ruff` and `mypy` on the touched backend files, and `git diff --check`.

### 9f.5 Stops (report to the Architect; never design around them)

- **S1.** Any pinned digest or byte changes for a run with no actions.
- **S2.** A need to edit `contracts/**`, `host/execution_adapter.py` or `S/**`, or M2, M3, `record_channels` or the envelope schema.
- **S3.** Kernel parity (test 9) differs from F0r's evidence by any amount.
- **S4.** The frozen log `sha256` ≠ `77777c82d82298ffba77a130f8d9ea2c6bb9a80c491ba4b2ac5248c4b735b634`, or a K0 content hash ≠ F0's history hash.
- **S5.** A file outside §9f.3.
- **S6.** A fixture is not reproducible across two fresh processes even after removing `run_id` and `created_at`.
- **S7.** More than 3.0 units spent.

### 9f.6 Size, path and date

- **K0 stays 2.5** (range now 2.25–3.0, narrowed from 2.0–3.25).
- What Q2 and Q4 save:
  - no contract, host or trajectory edit, about −0.2 from the "contract and models origin" item;
  - the host and kernel reserve of 0.25, released to the range.
- What Q3, Q7, Q8 and Q10 add:
  - frozen log record, parse cross-check and log row, +0.15;
  - path refusals and the 11-kind producer set, +0.05;
  - harness port, +0.05;
  - first-commit pins, +0.05.
- Net about −0.05 at the centre, so the size stays 2.5.
- **Critical path unchanged.** K0 is off it, on lane 2, with about 2.3 units of float (§9.5). The path is still about **8.75 lane-units**, below the **9.75 tripwire**, and is not crossed.
- **Demo date unchanged** at about +3.25 working days. Contingency is unchanged at 0.05.
- After-the-demo list: none.

### 9f.7 Owner questions

None. For the owner, in plain words: the fuel delivery and the unrecorded removal now enter the simulated world as logged operator actions, stamped with who did what and from which log. Runs that have no actions stay exactly as they were, to the byte.

---

## 9g. Ruling DIESEL-1-R3g: K3 stop S4 (K2's fuel-records reader in the composition)

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27).
- Read on `task/DIESEL-K3-fuel-balance` at `7ded13f1c` (phase A `202535b81`, rule-8 reorder `f864e9e1a`, main merged `3843c82e2`). Read: `tools/checks/configuration-persistence.ps1` rule 1 (`:223-274`), `B/work/composition.py`, `B/evidence/composition.py:89-98`, `B/fuel_balance/composition.py`, `B/fuel_balance/worker.py:38-73`, `B/fuel_balance/adapters/postgres_fuel_balance_store.py:160-190`, `B/work/adapters/postgres_fuel_records.py:40-46`.

### 9g.1 Decision 1: allow the exposure in `B/work/composition.py` (a named, narrow exception to §9d.9 S4)

- **Allowed.** It is the established pattern: `evidence/composition.py:89 build_link_rows_reader()` hands a caller-connection reader across domains in the same way, and `work/composition.py` already uses it. Rule 1 is kept as written: the only `work.adapters` import stays inside `work/composition.py`.
- **Routes rejected:**
  - a second fuel-records query in `fuel_balance/adapters/` would duplicate K2's correction semantics, the very rows K2 L1 and §9d.3 test;
  - moving `select_fuel_records` out of `work/adapters/` changes K2's layout for no gain;
  - widening rule 1 is never done.
- **The exception is these lines only.** It covers no other `B/work/` edit and no behaviour change. S4 stays in force for everything else.

### 9g.2 Exact change

1. **`B/work/composition.py`**: add after `build_work_service`, with a lazy import like `build_link_rows_reader`:
   ```python
   def build_fuel_records_reader():
       """DIESEL-K3 (DIESEL-1-R3g): K2's fuel-records read on a caller's connection, for the fuel-balance store."""
       from assetops_backend.work.adapters.postgres_fuel_records import select_fuel_records
       return select_fuel_records
   ```
   - Add `"build_fuel_records_reader"` to `__all__`, in alphabetical position.
   - The name is `build_fuel_records_reader`, not `fuel_records_on_connection`, to match the `build_*_reader` precedent.
2. **`B/fuel_balance/composition.py`**:
   - The default branch becomes `from assetops_backend.work.composition import build_fuel_records_reader` and `fuel_records = build_fuel_records_reader()`.
   - Remove the `type: ignore` and the "K3 STOP S4" comment.
   - Keep the docstring, which names `work/composition.py`.
3. No other file changes for this item. The adapter, K2's tests and the rule-1 script stay untouched.

### 9g.3 Tests that the production path composes

- **A13 (L0, append to `backend/tests/test_k3_fuel_balance_rules.py`, no DB):**
  - (a) `work.composition.build_fuel_records_reader() is work.adapters.postgres_fuel_records.select_fuel_records`.
  - (b) `store = fuel_balance.composition.build_fuel_balance_store("postgresql://unused@127.0.0.1:1/none")`. Assert `store._fuel_records is select_fuel_records`, `isinstance(store._actions, PostgresActionStore)`, `store._engine is None` (nothing connects) and `store.test_db_clock_override is None`.
  - (c) **The worker's own branch.**
    - Spy on `fuel_balance.composition.build_fuel_balance_store` with a wrapper that delegates to the real function and keeps the store it returns.
    - With `DATABASE_URL` unset (monkeypatch `delenv`), run `worker.main(["assess", "--site", "KISIWA-001", "--from", "2026-10-06", "--to", "2026-10-07"])` with no `store=`. It must raise `RuntimeError` matching `"DATABASE_URL is not set"`.
    - The spy must record exactly one call with `None`, and the kept store's `_fuel_records is select_fuel_records`.
    - This test fails today with the `ImportError` the builder reported.
- **C (parity, `host/tests/test_k3_fuel_balance_parity.py`):**
  - Build the module's `kisiwa["fb"]` with `build_fuel_balance_store(URL, test_db_clock_override=<the existing virtual clock>)` instead of constructing `PostgresFuelBalanceStore` by hand with an adapter import.
  - Every C assertion, the CLI `REUSED` step included, then runs through the production composition against a real DB. The virtual clock is the composition's own test-only parameter (§9d.4).
  - Part B may keep its direct injection: its K2 L1 tests are about the reader, not the wiring.
- No other test changes. A13 is L0. C runs as already planned for phase B (machine idle, `assetops_k3_test` only).

### 9g.4 Who does it

- **The planned Sonnet round on `task/DIESEL-K3-fuel-balance` (worktree `C:\Users\assef\Bineyame\AssetOpsV1-k3`)**, in the same round that verifies and finishes phase B. Order:
  1. §9g.2 and A13;
  2. switch C's fixture to the composition;
  3. run phase B's part C;
  4. write the packet.
- One commit for §9g.2 + A13, then phase-B commits. Use `git add -f` of explicit paths.
- The packet lists the `work/composition.py` diff under "S4 exception, DIESEL-1-R3g".
- K3's first review (Opus, §9d.10) reviews the whole branch, this item included.
- Size: about 0.05, inside K3's 1.6. **Critical path, tripwire and date are unchanged.**

### 9g.5 Builder calls confirmed

- **K2 L2 single-head assertions made head-agnostic** (`backend/tests/test_k2_fuel_records_postgres.py:137-138, 168, 184, 186`, in `202535b81`): **confirmed**. This is a head-bookkeeping edit, not a behaviour change (not S5). It is the same allowance §9d.6 gives catalogue-count tests and K2 took for 0054.
  - The single-head property is still asserted (`get_heads() == [alembic_head()]`), and 0054's `down_revision == PREVIOUS` is kept.
  - The up/down/up and refused-downgrade tests still pass through 0054. Downgrading to `PREVIOUS` now also takes 0055 down first, on its empty table.
  - Condition: the packet states that these lines changed and why, and the reviewer re-reads them.
- **`$fuelBalanceWriter` moved before `$trialComparisonWriter` in rule 8's `$pgWriters`** (`f864e9e1a`, one line): **confirmed**.
  - The list membership is identical, so the rule is not loosened.
  - The order keeps `tools/checks/test_estate_guard.py:148`'s anchor `", $trialComparisonWriter)"`, which that self-test edits.
  - The packet lists it with that reason.

### 9g.6 Owner questions

None.

---

## 9h. Ruling DIESEL-1-R3h: K3 stop S1 (600 idle seconds on every Kisiwa night)

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27).
- Read on `task/DIESEL-K3-fuel-balance` at `3c239ad2c`: `B/fuel_balance/rules.py:171-201` (`use_from_readings`), `B/actions/verification_rules.py:222-330` (`_power_slot`, `_instant`), `:372-373`, `:478-491` (A2's idle count), `B/analytics/dispatch.py:97-98`, `:242-300` (run reconstruction, `_off_after`), `simulator/assetops_simulator/packs/mini_grid.py:29-33` (lifecycle timing), `backend/tests/test_tfc2.py:146-177`, `backend/tests/test_k3_fuel_balance_rules.py:155-230`.
- Evidence: read-only SQL on `assetops_k3_test` (the stored windows of the failing run and their `accepted_evidence`).

### 9h.1 The stop

On nights 2, 4 and 6, `idle_seconds = 600` where the card and F0 expect 0. `use_high` and `residual_low` each differ from F0 by `539/600` L = `600/3600 h × 49/10 L/h × 11/10`. Every other term and all three states match F0.

### 9h.2 Cause, with evidence

**The idle slots are the two generator stop slots of each night.**
- The SQL pairs each accepted `generator_state` sample at `t` with the `generator_power` mean over `[t, t + 5 min)`, the pairing that `use_from_readings` and A2 both use. In each window it finds exactly two slots that are RUNNING at 0 kW. In UTC, the same instants each night:

  | Slot start (UTC) | Local | State at `t` | Mean kW over `[t, t+5)` | Mean kW over `[t−5, t)` | State at `t + 5` |
  |---|---|---|---|---|---|
  | 19:05 | 22:05 | RUNNING | 0 | 38 | STOPPED |
  | 00:15 (next day) | 03:15 | RUNNING | 0 | 27 | STOPPED |

- 2 × 300 s = 600 s on every night. No other slot is RUNNING at 0 kW.
- Starts give no idle slot. Example: STOPPED at 17:05 with 0 kW over `[17:05, 17:10)`, then RUNNING at 17:10 with positive kW from 17:10.

**Why the stop and the start differ.** The simulator's lifecycle timing (`mini_grid.py:29-33`) works like this:
- A request emitted at `T` changes the state in phase F, after the sample at `T`. So the sample at the stop instant still says RUNNING, and the slot that follows carries 0 kW: the generator is already STOPPED for the whole slot and burns nothing.
- At a start, the elapsed start delay moves STARTING to RUNNING in phase A, before the sample. So the STARTING step is published as STOPPED at 0 kW, and the first RUNNING sample opens a loaded slot.
- The result is that every stop publishes one "RUNNING at the slot start, 0 kW over the slot" pair. That is an artefact of the sampling order, not idle running.

**This is the shared slot rule, not a K3 bug.** K3 applies A2's rule exactly as §9d.2 ordered: `state_t ∈ RUNNING_STATES and kwh_t == 0` (`verification_rules.py:490`, mirrored at `rules.py:196`). A2's `generator_idle_seconds` would score the same two slots per night as 600 s, as K3 does; test A6 already pins that they are equal.

**The product disagrees with itself here.** The dispatch analytic, whose Candidate time drives fuel-cost-2, ends a run at its last RUNNING sample when a 0 kW interval starts there (`dispatch.py:292-300`, `_off_after`). So the product's own run reconstruction reads the stop slot as stopped, while A2's slot rule reads it as idle.

**F0's 0 is right.** L2 predicted that F0's true-trajectory terms could differ from the readings. Here the trajectory has 0 idle fuel, and the published evidence, read the way dispatch reads it, also has 0 idle.

### 9h.3 Decision: (c), a shared slot-rule defect. Fix the rule once, in `verification_rules.py`; parity expectations stay as the card wrote them.

- **Not (a).** Accepting 600 s would book about 0.9 L of "idle" fuel per Kisiwa night that the evidence does not show. The generator was published RUNNING only at the stop instant, and the product's own dispatch reading calls the following slot stopped. It would also make §9c.3 L2 (c) false ("Kisiwa has 0 idle minutes"), and it would put an artefact into A2's money wherever a trial window contains a stop.
- **Not (b).** K3 followed the card.
- **The rule (A2's, shared):** a slot is idle iff
  - the sample at `t` is RUNNING, and
  - the slot kWh is exactly 0, and
  - the accepted sample at `t + 5 min` is **not** one of the not-running states (`STOPPED`, `STARTING`, `FAILED`, i.e. `dispatch.NOT_RUNNING_STATES`).

  A missing, conflicting or non-GOOD sample at `t + 5 min` leaves the slot idle, exactly as today. The lookahead only removes a slot when there is a **positive** stop marker; it never makes a slot unknown. So no window's `None` or its problems change.
- **Why that rule.** It is dispatch's `_off_after` boundary, stated per slot. It removes only the stop slot. A generator that idles unloaded for the whole slot and stops at the next boundary is still counted, because the sample at that boundary is still RUNNING (phase F order). The cost: a real engine that idled part of the slot and then stopped is not counted for that part. That undercounts by at most one slot per stop, the same treatment the start slot already gets. In the fuel balance this is at most 0.45 L of `use_high` per stop, against a 2a = 20 L margin.
- **Tolerances are unchanged.** C keeps every exact item, 1/100000 L on the toleranced terms, and `idle_seconds == 0` on all three nights. No restatement is needed, because with the fix K3 equals F0.

### 9h.4 Exactly what changes

**1. `B/actions/verification_rules.py`** (named, narrow S4 exception, like R3g; nothing else in the file changes). Next to `RUNNING_STATES` (`:372-373`):
```python
#: DIESEL-1-R3h: the sampled values that end a run (`analytics.dispatch.NOT_RUNNING_STATES`)
NOT_RUNNING_STATES = frozenset({"STOPPED", "STARTING", "FAILED"})


def idle_slot(slot_start: datetime, state_value: Any, slot_kwh: Fraction | None,
              state_readings: Iterable[Reading]) -> bool:
    """A2's idle slot: sampled RUNNING at the slot start and exactly 0 kWh over the slot, unless the accepted sample at
    the slot end is a not-running state. That slot is the stop slot: the sample precedes the stop, and dispatch's
    `_off_after` ends the run there (DIESEL-1-R3h). A missing or unknown end sample keeps the slot idle."""
    if state_value not in RUNNING_STATES or slot_kwh is None or slot_kwh != 0:
        return False
    return _instant(slot_start + SLOT, state_readings, numeric=False)[1] not in NOT_RUNNING_STATES
```
- In `window_evidence`, `:490` becomes `elif idle_slot(t, gen_value, slot_gen_kwh, state_readings):`.
- The lookahead's payload is **discarded**: no `note(...)` and no `evidence.update(...)`. The window's problems, evidence ids, `plan_sha256` and stored details are therefore byte-equal. `generator_idle_seconds` is already outside `plan_sha256` and the details (`:435-436`, `test_out_e3_trial_comparison_postgres.py:52`).

**2. `B/fuel_balance/rules.py`**:
- `use_from_readings` imports `idle_slot` and replaces `value in RUNNING_STATES and kwh == 0` (`:196`) with `idle_slot(t, value, kwh, state)`. The unknown handling stays as it is.
- The docstring says "A2's slot rule (`verification_rules.idle_slot`)".

**3. Tests**
- **`backend/tests/test_tfc2.py`**: add `test_window_idle_seconds_exclude_the_stop_slot`:
  - gen 0 kW; RUNNING at slots 0–5, STOPPED at 6–11 → `generator_idle_seconds == 1500`, not 1800;
  - RUNNING at 0–11 with STOPPED at the window end (`T0 + 60 min`, an extra point) → 3300;
  - RUNNING at 0–11 with no end sample → 3600 (unchanged);
  - RUNNING at 0–5, then a non-GOOD sample at slot 6 → 1800 (no positive stop marker).
  - Each case must fail if the lookahead is removed or inverted.
  - **The existing tests stay byte-unchanged.** Line 169's `three` case keeps 900, because the sample after slot 2 is `"ON"`, which is not a not-running state.
- **`backend/tests/test_k3_fuel_balance_rules.py`**:
  - **A3 fixture:** `running = set(range(25))`. The idle night has 25 RUNNING samples (slot starts 0–24) and STOPPED from 25, so 24 idle slots. All of A3's expected numbers stay as the card wrote them (7200 s, `539/50`, `1711/50`, BELOW_MATERIALITY, the r = 33/10 rerun).
  - **New A14:** the Kisiwa stop shape. Slot `k` loaded at 38 kW, then RUNNING at `k+1` with 0 kW and STOPPED at `k+2` → `idle_seconds == 0`. Converse: RUNNING at `k+1` and `k+2`, 0 kW over both slots, STOPPED at `k+3` → 300 (slot `k+1` idle, slot `k+2` the stop slot).
  - **A6 extended** with one stop slot inside the hour: K3's idle seconds equal `window_evidence(...)["generator_idle_seconds"]`.
- **`host/tests/test_k3_fuel_balance_parity.py`**: no change. C is re-run as written, on `assetops_k3_test`, with the machine idle and free RAM checked. Expected: all three nights pass, with `idle_seconds == 0`.
- **Must stay green unchanged** (localised runs, no full suite):
  - `test_tfc2.py` (the existing cases);
  - `test_s6_verification_rules.py`;
  - `test_out_e3*` cost-check tests;
  - `test_ch9b2_reserve_byte_equal_postgres.py` and `test_s6_verification_evaluator_postgres.py` (their goldens hold `generator_idle_seconds: 0`, and a rule that only removes slots cannot change a 0);
  - K3's A1–A13 and B1–B6.

  If any of them needs a behaviour edit, stop under S5.

**4. What does not change:** `probe-result.json`, the probe, `PARAMETERS`, every C tolerance, `dispatch.py`, `fuel_cost_v2.py`, `trial_fuel_comparison.py`, and every Kobo, Cold and EV file.

### 9h.5 Who does it

- **A Sonnet fix round on `task/DIESEL-K3-fuel-balance`** (worktree `C:\Users\assef\Bineyame\AssetOpsV1-k3`). Order:
  1. §9h.4 items 1–3 in one commit;
  2. the localised runs;
  3. part C, re-run;
  4. the packet.
- The packet lists the `verification_rules.py` diff under "S4 exception, DIESEL-1-R3h" and quotes this section's SQL table as the cause.
- `git add -f` of explicit paths.
- **K3's first review (Opus)** covers it. The reviewer applies two mutations to a scratch copy:
  - delete the lookahead: the new tfc2 test, A14 and C must fail;
  - replace `NOT_RUNNING_STATES` with `{"STOPPED"}`: the tfc2 non-GOOD case must still pass, which shows that only positive markers act.
- **K6** merges main before its own `verification_rules.py` edit. The R3d note that K6 owns the next edit now reads "the next edit after R3h".

### 9h.6 Kobo impact (A2, stated plainly)

- **Kobo's idle-fuel money in the demo does not change.**
  - A2 changes only in a verification window that contains a stop slot: a RUNNING sample, then 0 kWh, then a not-running sample.
  - Kobo's trial baseline hour (09:00–10:00 local) sits inside a run that idles from 07:05 to 10:55 (`.agent/fuel-story-design-2026-11-07.md:66`, `:137`). Its later hour has no run. Neither hour contains a stop, so both keep 3600 s and 0 s.
- **fuel-cost-2** (Kobo's three idle mornings) counts idle inside dispatch's Candidate time, which already ends at the last RUNNING sample. It is unaffected.
- **The defect is real for Kobo in general.** Without the fix, any trial window that contains a generator stop would gain 300 s per stop: 0.275 L nominal, 0.3025 L upper at 3.3 L/h, about 0.34–0.38 USD at 1.25 USD/L. In a baseline window that inflates the claimed saving; in a later window it understates it. None of the demo's windows contains one.
- **A3's check stands as the backstop.** If the stored trial-hour idle differs from 12 slots, it is a data finding (`build-sheet-FUEL-1.md:425`). A3 needs no edit.

### 9h.7 Effect on the demo story

- With the fix, every Kisiwa night shows **0 idle minutes and no idle fuel**. That is honest: the generator runs loaded and stops, and both the simulator and the product's dispatch reading say it never idles.
- Night 4's band, and so K4's UNEXPLAINED figure, equals F0's exactly. Nights 2 and 6 stay WITHIN_MARGIN.
- **The alternative is not honest.** Without the fix every night would carry about 0.9 L of idle fuel (2 × 5 min at 4.9 L/h × 1.1) that never happened, and night 4's lower residual would sit about 0.9 L below F0.
- K4 and K5 add **no** idle line on Kisiwa (`idle_seconds` is 0). The idle term stays exercised only by A3, as §9c.3 L2 (c) says.

### 9h.8 Size

- About **0.15**: rule and helper 0.05, tests 0.05, part C re-run and packet 0.05. K3 goes from 1.6 to about 1.75, inside S7's 1.9.
- It is paid from the remaining contingency (0.15 → 0), so the Kisiwa total stays **17.25**.
- **Critical path:** about 8.9 lane-units (8.75 before). That is **below the 9.75 tripwire; no cut.**
- **Demo date:** unchanged at about +3.25 working days.
- **Contingency is now spent.** The next overrun on the Kisiwa lane is reported against the tripwire, not absorbed.

### 9h.9 Owner questions

None.

---

## 9i. Ruling DIESEL-1-R3i: K0's two S5 stops, five deviations, and a main-drift failure

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `bd15b0ca8`.
- K0 was read on `task/DIESEL-K0-action-bridge`:
  - `d782fc09f` holds the pins;
  - `dd4a3874f` holds the bridge;
  - `2b8ab3ab9` holds the packet `.agent/review-packet-K0.md`.

**Code facts the Architect verified on the K0 worktree:**
- `B/runs/composition.py` docstring: "the one place in the product allowed to import `assetops_backend.runs.adapters.*`".
- `tools/checks/configuration-persistence.ps1:580-640`, rule 7:
  - the run adapters hold exactly one `= yaml.load(..., Loader=CSafeLoader)`;
  - `safe_load` is banned anywhere in the run adapters;
  - the stated reason is one loader policy for the run domain (`D-2026-09-29-run-store-libyaml`).
- `yaml_run_documents.py:150` is that one load point today.
- `git diff d782fc09f 2b8ab3ab9 -- backend/tests/k0_byte_equal_pins.py` is empty. The pins have not moved since the first commit, and `seeded_uuid4()` was already in that commit.
- `backend/tests/test_run_binds_scenario_to_site.py` was last edited at `aeb53fb86` (2026-10-31). `config/scenarios/kobo-rest-mill.yaml` was added at `8b68aaa14` (2026-11-06, DD1a1-R16). The test's set equality (`:242-245`) cannot hold for scenarios added after it.

### 9i.1 Rulings

**S5-a. Approved: `B/runs/composition.py` joins §9f.3's file list.**
- Add `build_operational_action_log() -> OperationalActionLogPort`, which returns `YamlOperationalActionLog()`, beside `build_run_repository`. The docstring is one line.
- `B/main.py` imports it from `runs.composition` and passes `operational_actions=build_operational_action_log()`. It never imports the adapter.
- §9f.2 (6) is amended to read "through the composition".
- **Test.** §9f.4 test 10, on `assetops_k0_test`, must exercise this composed path: the `main.py` app, not an injected router.
  - It sets up Kisiwa run 4 with the named log.
  - It gets no `OPERATIONAL_ACTION_LOG_UNAVAILABLE`.
  - On readback it shows `answered_by="OPERATIONAL_ACTION"` rows.

**S5-b. Option (i): a shared text-load function in `B/runs/adapters/yaml_run_documents.py`. That file joins §9f.3. The guard is not changed.**
- In `yaml_run_documents.py`, add `def load_yaml_text(text: str) -> object: return yaml.load(text, Loader=CSafeLoader)`. It holds the one guarded line, and `yaml.YAMLError` propagates.
- `read_run_record` calls `load_yaml_text(text)` inside its existing `try`. Its behaviour and messages are unchanged.
- `yaml_operational_action_log.py` imports and calls `load_yaml_text`, and maps `yaml.YAMLError` to `OperationalActionLogUnavailable`. It no longer imports `CSafeLoader` or calls `yaml.load`.
- This is rule 7's own intent: one loader policy at one load point in the run adapters.
- §9f.2 (5)'s `yaml.safe_load` was the Architect's slip. The run domain's policy is libyaml `CSafeLoader`, and stop S4's hash and content-hash checks prove that the promoted log parses the same.
- Acceptance:
  - the architecture check and the estate-guard self-tests pass with **no** change to `configuration-persistence.ps1`;
  - `rg "yaml\.load\(" backend/assetops_backend/runs/adapters` gives exactly one hit.
- Option (ii) is refused. A guard is never loosened to fit a spec slip.

**Deviation 1, EV pin under `seeded_uuid4()`: accepted, not an S6 stop.**
- S6 exists so a pin cannot be meaningless. A render that varies only by random mapping ids would be meaningless.
- Under a fixed seed, the pin is deterministic and still covers every byte K0 could move. K0 produces no mapping id.
- The seeding has been in the first commit, unchanged since.
- Condition: the pin's docstring states that the seeding fixes only identifiers K0 does not produce. The packet's S6 note cites this ruling.

**Deviation 2, test 1 in `host/tests/test_k0_kisiwa_actions.py`: accepted.**
Digest (c) needs `host/`'s `frozen_world_inputs`, and `backend/tests` does not import `host/`.

**Deviation 3, the loader's `component_ids` keyword: accepted.**
The pure loader receives the Site's component ids instead of a Site record, so it stays I/O-free. §9f.2 (5)'s signature is amended to `freeze_operational_actions(request, identity, log_source, *, model, start, end, component_ids)`.

**Deviation 4, the coverage test excludes `operational_action_log`: accepted, with one tightening.**
- The exclusion is right for a run that names no log: the field is None, and it has no row so the run stays byte-equal.
- Add one K0 test assertion: for a run that **names** a log, the same coverage holds with **no** exclusion (`covered == declared`).
- This turns the exclusion into a tested conditional.

**Deviation 5, UNIT and EVENT_ID_CONFLICT reachable only by a direct loader call: accepted, kept as kinds.**
- Both have live producers that guard real input combinations:
  - UNIT: a selectable model profile whose `fuel-tank-volume` stock is not in L;
  - EVENT_ID_CONFLICT: a scenario event-id grammar that admits `{id}/{effect}`.
- Neither combination is shipped today. This is not the retired-kind case in `refusals.py:83-89`, where the producer had been deleted.
- Add a comment to each kind in `refusals.py`: "reachable only by a model profile (or scenario id grammar) not shipped today; tested by a direct loader call".
- The `produced` set keeps them, through those direct calls.

**Main drift, `test_run_binds_scenario_to_site.py` (12 failures, `KeyError 'kobo-rest-mill'`): confirmed main drift, not K0.**
- The test predates about 10 shipped Kobo scenarios added in the DD-1a1 and DD-1a2 rounds (up to 2026-11-06). K0 touches no scenario and not that test.
- **Who fixes it:** a separate Sonnet fix unit, **DRIFT-RB1**.
  - Branch `task/DRIFT-RB1-scenario-site-sample`, from main.
  - It edits that one test file only.
  - It does not block K0's review or merge, and K0 must not fix it.
- **Rule for the fix.** `FROZEN_V1_SAMPLE` is the frozen v1 sample and gets no new entries with invented dates. Each new stem goes into `NEVER_SHIPPED_AS_V1`, or a sibling set with a one-line reason if that set's meaning does not fit.
- **Verification:** that test file passes. `git diff --stat` shows one file. The coordinator verifies.
- **Cost:** about 0.05. It is charged to the DD (Kobo-day) lane's follow-ups, not to Kisiwa.

### 9i.2 Order

1. **K0 Sonnet fix round** on the K0 branch:
   - S5-a;
   - S5-b;
   - the deviation 1 docstring;
   - the deviation 4 assertion;
   - the deviation 5 comments;
   - a packet update citing R3i.

   It re-runs only the K0 tests (with test 10 on `assetops_k0_test`), the architecture check and the guard self-tests. There is no suite.
2. **Then K0's Opus first review, straight after**, on the final tree. No review happens before the fix round: both S5 items change wiring the reviewer must see.
3. **DRIFT-RB1** runs in parallel. It is independent.

### 9i.3 Size, path, date

- **K0: 2.5 → 2.6** (range 2.25–3.0, unchanged). The +0.1 covers the two S5 fixes and the EV-pin seeding.
- The contingency is spent (§9h.8). So this is **reported, not absorbed**: the Kisiwa total goes **17.25 → 17.35**.
- **Critical path unchanged at about 8.9 lane-units.** K0 is off it, and its float of about 2.3 absorbs the 0.1.
- **Below the 9.75 tripwire; no cut.** The demo date is unchanged at about +3.25 working days.
- DRIFT-RB1 (0.05) is outside the Kisiwa total.

### 9i.4 Owner questions

None.

---

