# W2-05b pending rulings (run 1, 2026-10-19) - commits 1 and 2 blocked

Builder stopped before writing code: spec commits 1 (strict catalog, frozen identity, Lab choice) and 2
(pack, six-case tests) both depend on the items below, which neither `.agent/W2-05b-build-spec.md`
(including the dry-read and Run 8 amendment) nor `.agent/W2-technical-design-ev.md` §3/§8 fixes.
Each question names the code precedent found, so the Architect can rule in one pass. Batch with any
pre-review sweep of commits 3-5.

## Document shape (`ev-scenario/1`, commit 1; changes scenario SHA pinned later in manifests)

- **Q1 `window` value shape.** Spec: "window is strict UTC `[2026-10-06T08:00:00Z,09:00:00Z)`". Is the
  YAML value `{start, end}`, a two-item list `[start, end]`, or the cold manifest shape
  `{start, end, end_exclusive: true}` (`contract-fixtures/w2/cold/*.json`)? Cold documents use top-level
  `start`/`end` keys, which the EV key list excludes.
- **Q2 forcing row order and the same-minute kind rank.** Spec: apply forcing "sorted `(time,connector,kind)`,
  with PLUG before FAULT at equal time" and refuse "unordered" documents. Alphabetical kind order puts
  `AUTHORIZE` before `PLUG` at `(08:00,c1)` in `complete`/`interrupted`/`fault`(c2), i.e. authorize an
  unplugged connector. Give the exact total kind rank used for both parser order check and pack
  application (e.g. PLUG < AUTHORIZE < REQUEST_KW < FAULT < CLEAR < UNPLUG?), and whether rows within one
  minute are sorted connector-first (c1 before c2) as written.
- **Q3 closed forcing vocabulary and value types.** Table kinds/values: `PLUG/session-1|session-2`,
  `AUTHORIZE/ACCEPT` (and `DENY`?), `REQUEST_KW/60`, `UNPLUG/END`, `FAULT/LATCH`, `CLEAR/CLEAR`.
  (a) Is `REQUEST_KW` value the canonical decimal string `"60"` (the dry-read says "decimal strings")
  or a YAML number? (b) Is `PLUG` value required to equal `session-<n>` in plug order, and is it the
  private label the "deterministic scoped session ID" is derived from, or ignored? (c) Grid interruption
  is in the model ("pauses allocation") but no case uses it: exact kind/value names (cold uses
  `GRID_LOSS/LOST`, `GRID_RESTORE/AVAILABLE` on `grid-1`), and which asset field value (`connector`
  null? `feed-1`?) - or is it excluded from the closed `ev-scenario/1` vocabulary for 05b?
- **Q4 observation rows `{time,kind,connector,action,release_at}`.** (a) `missing-meter` drop of slot
  `[08:10,08:15)`: is `time` the slot start `08:10` or the interval end / source time `08:15`?
  (b) Action names: `DROP` (missing-meter), `HOLD` with `release_at 09:05` (late-record), and for
  `contradictory` the added GOOD `EV_SESSION_END` at 08:30 - action `ADD`? (EV rows have no `outcome`
  key, unlike cold.) (c) Closed observation kind set: exactly `ENERGY_REPORT`, `EV_SESSION_END`? Which
  kinds admit which actions? (d) Observation sort key and duplicate rule (cold: `(at,kind,device_id)`).
- **Q5 `scenario_id` and file grammar.** Confirm `scenario_id = ev-<case>` matching the file name
  (`ev-complete` ... `ev-contradictory`), pattern `ev-[a-z][a-z0-9-]*` as cold.
- **Q6 `FrozenScenarioBinding.scenario_version`.** The EV key list has no `version` (cold has
  `version: 1`). What integer is frozen in `scenario_version` for EV runs (1?), and what does the
  catalog row report as `scenario_version`?
- **Q7 `observation_sha256` canonical row form.** Spec: SHA-256 of canonical JSON
  `["ev-observation/1", ordered observations]`. Is each row the object with keys
  `{time,kind,connector,action,release_at}` (nulls included), and is the leading literal the string
  `"ev-observation/1"` (not the `{profile_id,profile_version}` object)?

## Lab choice (commit 1, user-visible / API)

- **Q8 frame placement.** Spec says both "Follow `ColdRunSetupFrame.tsx`... route through the existing Lab
  Site-first setup" and "In `RunSetupFrame` after Site selection, offer the six returned EV choices".
  Cold has its own route/frame (`simulatorLabRoutes.tsx:113` `COLD_RUN_SETUP_PATH`, frame at :392-405,
  linked from `SimulatorLabFrame.tsx:92-100`); `RunSetupFrame.tsx` has no cold logic and no Site type.
  Which: (a) a new `EvRunSetupFrame` + `EV_RUN_SETUP_PATH` + link beside cold, or (b) an EV branch inside
  `RunSetupFrame`? If (b), how does `RunSetupFrame` learn the Site is `EV_CHARGING`?
- **Q9 user-visible copy.** Needed exact strings: the six choice labels (cold has
  `COLD_SCENARIO_LABELS` "Normal", "Excursion"...); the frame title/link text if Q8(a); the 403 scoped
  refusal sentence; the 404 unknown-Site sentence; the retry button label for 503. (Empty and 503 copy
  are ruled.)
- **Q10 `GET /api/simulator-lab/ev-scenarios` refusals.** Cold route has no 403 and returns 200 empty for
  an unregistered/other Site. Spec: 403 scoped refusal, 404 unknown Site, empty list, 503. (a) What
  principal/role check produces 403 on this route (the Lab router has no owner gate today; replay uses
  owner Lab role + `SITE_SCOPE_FORBIDDEN`)? (b) Exact refusal codes for 404 (`SITE_NOT_FOUND`?) and 503
  (`REFUSAL_SCENARIO_STORE_UNAVAILABLE` / `REFUSAL_STORE_UNAVAILABLE` as cold, or a new EV code)?
  (c) When is the list empty versus 404: registered non-EV Site -> 200 empty, unknown Site -> 404?
- **Q11 catalog row shape.** Cold rows have exactly 10 keys
  (`scenario_id,scenario_version,display_name,schema,model_profile,publication_profile,observation_profile,start,end,seed`,
  client check `coldScenarioChoiceClient.ts:49`). For EV: same keys with `window` in place of
  `start/end`, profile strings `ev-charger/1` or `{profile_id,profile_version}` objects, plus timestep?
- **Q12 profile registry copy.** `runs/profiles.py` needs `EV_CHARGER_MODEL` (`ev-charger`,1) and
  `EV_PUBLICATION_PROFILE` (`ev-publication`,1) with `display_name`/`statement` and publication
  fields (`device_signal_cadence_minutes`, `simulator_source_id`, `gateway_id`, `record_channels`,
  `publication_clock`). Exact display names/statements and field values (gateway `GW-EV-LAB-01`?
  source id from registration per dry-read - what literal goes in the profile?).

## Pack semantics (commit 2)

- **Q13 states not exercised by the six cases** (unit tests must cover the guards): (a) state and
  session after `AUTHORIZE DENY` (PLUGGED with session kept/cleared? AUTHORIZING->?); (b) after `CLEAR`
  of a pre-START fault, does c1 keep its plug-assigned session token (still unstarted) or hold none
  while PLUGGED - the "state with no valid session" guard depends on it; (c) `UNPLUG` from PLUGGED /
  AUTHORIZING / FAULTED (no END emitted - which state, is it legal?); (d) `REQUEST_KW` before CHARGING:
  stored for later or refused; requested kW before any `REQUEST_KW` while CHARGING = 0?
- **Q14 public state vocabulary vs model.** Model states `UNPLUGGED|PLUGGED|AUTHORIZING|CHARGING|FAULTED`;
  does a CHARGING connector paused by grid interruption (or allocated 0) stay `CHARGING`?

No commits contain product code; branch head is the handoff/rulings commit only.

## Run 2 (2026-10-19): Q1-Q14 ruled and built. Non-blocking interpretation notes

Commits 1 and 2 follow the nearest precedent where the rulings are silent. Each note says what was built,
so the Architect can confirm or reverse it. None blocks commit 3. N8 should be settled before commit 5 pins
manifests.

- **N1 production 403.** `main.py` composes the EV choice route with `development_access` +
  `no_owner_principal`, like the cold replay. The running app therefore answers 403, and the Lab shows
  `EV test runs are not available for this Site`, until an owner principal exists. Should the owner
  walkthrough have a dev owner composition?
- **N2 envelope and order.** EV catalog refusals use the Lab router's `{detail:{code,message}}`, not the
  replay's `{error:{...}}`. Check order: 401, then 422 (`site_id`), then 403, then 404/registration.
- **N3 Lab link placement.** `Set up an EV charging run` sits inside the existing `Cold-chain run setup`
  panel, under the cold link, because no EV panel heading or description is ruled.
- **N4 client states.** For a Site whose detail is not `EV_CHARGING`, the screen shows the empty copy and
  makes no API call. Site detail `not_found` uses the 404 copy, and `unavailable` uses the 503 copy with
  Retry. API 401/422/other non-OK answers map to the unavailable copy.
- **N5 model profile.** `EV_CHARGER_MODEL.supported_states=()`, as for cold. The five Q12 state strings are
  `EV_CONNECTOR_STATES`, because `SupportedState` declares world-state keys, not values.
- **N6 parser literals.** The window and seed must equal the Q1/Q5 literals exactly. Forcing and observation
  `time` must fall on a minute boundary. REQUEST_KW is bounded by a 60 kW parser constant.
- **N7 pack schedule.** Outside the 08:00-16:00 UTC enable schedule, allocation pauses at 0 (no terminal),
  like a grid pause.
- **N8 private digest shape (pinned later).** The closing boundary (09:00) is a snapshot only: no forcing,
  transition or allocation. A 1 kW quantum is cut to `min(1, headroom, remaining)`, so fractional
  requests/limits are fully allocated. Private exact kWh renders as an integer or `p/q`. `forcing_ordinal`
  is the zero-based ordinal of the last forcing row applied at or before the boundary (null before any).

## Run 3 (2026-10-19): commit 3 question (blocks the admitted-Stage proof)

- **Q15 public UNPLUGGED state vs the 05a ENUM map.** Q12/Q14 and the commit 3 closure say the public
  connector `STATE_AT_INSTANT` value is one of `UNPLUGGED|PLUGGED|AUTHORIZING|CHARGING|FAULTED`. The
  published 05a binding (`backend/conversions/ev-lab-001-bindings.json`, rows `c1/c2-connector-controller/
  state`) has ENUM map labels `AVAILABLE, PLUGGED, AUTHORIZING, CHARGING, FAULTED, DISABLED`, matching
  `sites/binding_roles.py:43` `EV_CONNECTOR_STATES`. Gateway admission (`gateway/assetops_gateway/
  service.py:931-934` `_check_report_v2`) holds any value not in the map as `INVALID_ENUM`, so every run's
  08:00 c1/c2 `UNPLUGGED` state report would refuse Stage (`PUBLICATION_REFUSED`). 05b may not change the
  05a fixture/binding. Which: (a) the public transform reports the pack's `UNPLUGGED` as `AVAILABLE`
  (pack and private documents keep `UNPLUGGED`); (b) a new 05a binding revision adding an `UNPLUGGED`
  label; or (c) another rule?
- **Q16 fault/clear correlation without a scoped session.** v4 `_validate_event` requires `correlation_id` on
  every event; commit 3 says FAULT/CLEAR carry "S only if one is active" and "no session inference from a
  fault without S". A FAULT from UNPLUGGED, or the CLEAR after a started-session fault (S cleared), has no S.
  What `correlation_id` do those reports carry (e.g. `ev-` + SHA-256 of `[scenario_sha256,"fault",
  connector, ordinal]`)? None of the six documents reaches this; the transform refuses it for now
  (`ValueError`, `test_a_fault_without_a_scoped_session_is_not_published_pending_q16`).
- **Q17 `IDENTITY_KWH` is not a gateway or ledger conversion.** The 05a energy rows publish conversion
  `IDENTITY_KWH`; `gateway/assetops_gateway/snapshot.py:32` `SUPPORTED_CONVERSIONS={IDENTITY,ENUM}` refuses the
  whole snapshot at activation (`UNSUPPORTED_CONVERSION at bindings[n].conversion.kind`), and
  `evidence/ledger.py:309` names only IDENTITY/ENUM. So no real EV snapshot can activate, and commit 4's
  registered Stage cannot run. Is 05b to add `IDENTITY_KWH` (exact kWh decimal passthrough, no counter
  interpretation, design section 3) to the gateway snapshot reader and S2 ledger conversion, keeping v1/v3/cold
  bytes unchanged? Tests offer the energy rows as `IDENTITY` meanwhile and pin the refusal
  (`test_the_published_energy_conversion_is_refused_at_activation_pending_q17`).

Run 3 non-blocking notes (commit 3 built where the rulings are silent):
- **N9 closing-boundary state.** State reports cover all 61 boundaries per connector (09:00 included, as cold
  publishes its closing boundary): 122 per run.
- **N10 split means.** Connector power/requested/allocated means split at that connector's START/END/ABORT
  instants inside a slot; Site import splits at any connector's. Connector power and allocated limit both
  report the allocated kW. A mean without a finite decimal refuses.
- **N11 Site import order.** At equal source time Site import sorts after both connectors (connector key c1,
  c2, then Site), then channel rank, then per-channel ordinal.
- **N12 component and connector IDs** are the binding row `asset_code` (`c1`/`c2`), matching S2's
  `EV_CONNECTOR_MISMATCH` comparison with `binding.asset_code`.

## Run 5 (2026-10-19): q3 applied; open questions from Q15 (do not block commit 4)

- **Q18 Draft refusal against an old selected state map.** q3 Q15: "Refuse Draft or Stage against an old
  selected map that lacks `UNPLUGGED`". Stage refuses already (gateway holds `UNPLUGGED` as `INVALID_ENUM` ->
  FAILED/`PUBLICATION_REFUSED`; `gateway/tests/test_ev_v4_admission.py::test_unplugged_is_held_under_the_old_map_that_lacks_it`).
  The Draft check is not built because its shape is unruled: (a) which refusal kind (`VERSION_UNAVAILABLE`,
  `REQUEST_INVALID`, or a `BLOCKED` Draft with a blocking reason as `_publication_reasons` does) and the exact
  message; (b) the check reads the selected basis `snapshot_canonical` c1/c2 `ev_connector_state` maps in
  `runs/service.py:_create_ev_draft` and requires all five Q12 pack states as labels - confirm "lacks
  `UNPLUGGED`" means "lacks any of the five" or exactly `UNPLUGGED`.
- **Q19 upgrade of an already installed EV-LAB-001.** `sites/ev_lab.py:install_ev_lab` publishes only when no
  binding set exists, so a database installed with the first 05a map keeps it. q3 says it "needs a new normal
  binding publication, effective before the 6 October run window". Which: (a) `install_ev_lab` publishes the
  corrected map when the selected revision's state maps lack `UNPLUGGED`, or (b) a separate operator command;
  and which `effective_from` (the original `valid_from` 2026-10-01T00:00:00Z, or another instant before
  2026-10-06T08:00:00Z) and note text. Tests use 2026-10-05T00:00:00Z only as a test value.

## Run 5: commit 4 questions (block commit 4; run stopped after `W2-05b q3 fixes`)

Commit 4's spec leaves these shapes and sources to the builder; each is a design choice.

- **Q20 schema-7 artifact keys.** Cold schema 6 is the exact 28-key tuple `host/cold_lab.py:_COLD_KEYS`
  plus a second document after `HISTORY_MARKER` (`cold-private/1` minute records). For EV give the exact
  ordered key tuple of the schema-7 document: which of the cold keys stay (all 28?), the names/types of the
  added "frozen IDs/SHAs" (e.g. `foundation_revision_id`, `foundation_content_sha256`,
  `binding_set_revision_id`, `snapshot_sha256`), the private digest key (reuse `content_digest`?), and the
  "canonical public report texts/keys" (key name; element shape e.g. `{report_key,report_text}`; series order;
  held END included?). Is there a second document after `HISTORY_MARKER` (spec: private documents are not
  persisted), or none?
- **Q21 schedule location on restart.** Spec says both "Use the existing `PublicationSchedule` serializer, not
  separate EV storage" and "Restart reads terminal status and schedule from artifact". Cold keeps the schedule
  in `JsonPublicationSchedules` (`host/publication_schedule.py`) beside the schema-6 artifact. Does EV do the
  same (schedule file, artifact holds status only), or embed the serialized schedule inside the schema-7
  artifact (under which key)?
- **Q22 Foundation -> `EvParameters`.** `simulator/.../packs/ev_charger.py:EvParameters` has one
  `site_limit_kw`, `base_load_kw`, `connector_rating_kw`, `charger_rating_kw`, `enabled_from/enabled_to`
  (UTC time of day). The fixture has `feed-1 ev-site-import-limit 80.0 kW`, `charger-1 ev-charger-max-power
  60.0`, per-connector `ev-connector-max-power 60.0`, `connector_enable_schedules` per connector with a weekly
  TUESDAY 08:00-16:00 `Etc/UTC` row, and no base-load property. Rule: the property-to-field map; the base
  load source (constant 0 or refuse when absent); what to do when c1/c2 ratings or schedules differ or a
  connector is disabled (refuse FROZEN_RUN_NOT_RECONSTRUCTIBLE?); whether the weekday must match the run date;
  and the float-to-exact conversion (`Fraction(str(80.0))`).
- **Q23 binding rows for `ev_channels`.** Read `(device_id, signal_id, role, asset_code)` from the frozen
  basis `snapshot_canonical` (hash-verified), or re-read the binding revision rows from the Foundation store by
  `binding_set_revision_id` and compare its `snapshot_sha256`? Snapshot rows carry `asset_id`, so the
  `asset_code` lookup source (frozen Foundation revision components vs registrations) also needs naming.
- **Q24 EV projection copy and history.** Cold projections carry `COLD_NOTES` (user-visible, cold-specific
  sentence) and `read_history` answers `HISTORY_UNAVAILABLE` for cold. Give the exact EV notes tuple (or
  `()`), and confirm EV history is `HISTORY_UNAVAILABLE`.
- **Q25 delayed-report ID prefix.** Commit 3 uses `cold_lab.delay_event_id` (`cold-delay-` + SHA-256 of the
  report key) for the held EV END. Keep that for EV, or an `ev-delay-` prefix? It is persisted in the
  schedule and pinned by commit 5 manifests only indirectly.

## Run 6 (2026-10-19): q4 Q18-Q25 applied; commit 4 built. Non-blocking notes (built where the ruling is silent)

- **N13 swapped frozen mapping.** `_snapshot_rows` derives `asset_code` from the run's frozen `signal_mappings`
  and cross-checks existence/type in the frozen Foundation and asset/code one-to-one. A run whose c1/c2 mappings
  were swapped consistently passes those checks (only the run identity would differ). The Foundation `devices`
  device->component declaration could be cross-checked too; not built because unruled.
- **N14 schedule mismatch code.** q4 Q21 says verify schedule run/snapshot/held key/text/source time/state
  against run and artifact "before release" without a code; a mismatch refuses `PUBLICATION_SCHEDULE_UNREADABLE`
  (the existing closed-refusal kind), an unreadable artifact `ARTIFACT_UNREADABLE`. Only `advance_publication`
  verifies; `publication_schedule` reads as cold does.
- **N15 Q19 "independent later publication".** Refuses when any current binding revision starting after the
  selected one has rows that differ from it; Foundation-aligned unchanged copies are allowed (BindingService
  reaches through them). Also refuses a selected revision starting after 2026-10-05.
- **N16 Q18 c1/c2 identity.** A state row's connector is the frozen `signal_mappings` component of its
  `binding_revision_id`; its `(device_id, signal_id)` must be the closed table's state tuple whose device
  prefix is that connector, with the closed entry's v4 metadata.
- **N17 Commit proof in commit 4.** Host tests prove the COMPLETED readiness gate reaches `gateway.release` and
  FAILED refuses `COMMIT_NOT_READY` (fake gateway); the real seal/outbox/Batch V2/receipt path is proven by the
  commit 5 manifest generation as the spec orders.
