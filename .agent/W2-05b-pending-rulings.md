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
