# CH-9 pre-flight (measured daylight + full-day MG-5)

Implementer: Claude, 2026-11-05. Branch `task/CH-9-measured-daylight` from main `692e4d57e`.
Sheet: plan2 `.agent/build-sheet-CH-9.md` (§9 OWN-1104 supersedes R1-R3, R6). `B/` = `backend/assetops_backend/`.
Line numbers are to `692e4d57e`. **Result: questions Q1-Q8 below; STOP until ruled.**

## Facts from code

- **P1 (pv_available bound and emitted).** Role `pv_available_power` is in MINIGRID_ROLES_4
  (`B/sites/binding_roles.py:106,267,291`) and bound on Kobo in every Kobo roles-4 config
  (`backend/conversions/kobo-001-minigrid-roles-4-demo-config.json:26`, `kobo-001-s3-dispatch-demo-config.json:26`,
  `kobo-001-s6-verification-demo-config.json:28`; MG-W402 `mg-w402-001-minigrid-roles-4.json:155`). No roles-2/3
  Kobo config carries it (roles-3 only in `d-verification-window-v*.json`). Emitted by every Lab run through the
  gateway mapping `simulator/assetops_simulator/gateway/mappings.py:123` (`available-power`, INTERVAL_MEAN), value
  `min(rated*irr/STC, inverter_limit)` (`simulator/.../packs/minigrid.py:546-548`). MD-0 emits it as channel `pv`
  (`backend/conversions/mechanism-v1.json` reading_rules.signals.pv): 0 kW 00-06 and 18-24, 40 kW 06-18 local.
- **P2/P4:** no writer/table any more (§9 R2); no estate-guard registration needed.
- **P3 (R7 scenario).** `config/scenarios/kobo-daytime.yaml` already has the mill inside daylight:
  irradiance 150/550/900/950/600/150 over 2 h blocks from offset 0 (06:00 local), mill 0/15/18/10/12/0 kW
  (`:492-628`), i.e. mill 08:00-16:00. No new scenario needed. But every current Kobo story kind
  (`backend/conversions/demo-story-days-v1.json` kinds.kobo) runs **03:00-11:00 UTC = 06:00-14:00 local**
  (Africa/Addis_Ababa), on `kobo-s3-dispatch-necessary-run` / `kobo-mini-grid-reserve-trial`. See Q2, Q6.
- **P5 readers.**
  - `RENEWABLE_LOCAL_HOUR`: `B/mini_depth/worker.py:35,117` only.
  - noon hour SQL: `M/0029_w4_mini_depth.py:190` (refuse), `:257` (accepted trigger), `:295` (publication).
  - `local_noon`: `B/mini_depth/read.py:114` (`hour_windows`), `:510` (`read_selected_renewable_basis`, the study
    basis reader, not named in the sheet), `B/mini_decisions/projection.py:82` (`day_heads`),
    `B/site_outcomes/mini.py:561` (`_depth`: fuel/service/backup read the noon hour; MG-5 reads
    `depth["service"]["cards"]["unserved_kwh"]` at `:583-586`).
  - `renewable_noon_heads`: `B/mini_decisions/store.py:337`, caller `projection.py:84` only.
  - `noon_headroom_kw`: `B/chain/measures.py:48-49`, `config/chain/event-register-v1.yaml:24`,
    `tools/checks/test_event_register.py:139,161`, and tests (ch1a, ch1b, ch5a1 board contract, md0, ch5a2 fixtures).
  - `VALUE_LINE`: `B/chain/vocabulary.py:17-18,45`. `window_hours` is hard-coded 1 at
    `B/chain/opportunities.py:120` and `B/mini_decisions/opportunities.py:395`; typed in
    `frontend/src/estate/estateClient.ts:133`.
- **P7 cost.** Daylight hours per Kobo day: MD-0 12 (06-17); kobo-daytime 12; current story kinds at most 8
  (06-13, run ends 14:00). Renewable jobs per day 1 -> n (n = hours with a positive pv reading, incl. dawn/dusk).
  Mini jobs per fully delivered day 3x24+1 = 73 -> 84 (+15 %); per 8-h story day 3x8+1 = 25 -> 32 (+28 %).
  Each renewable job is one `load_hour_inputs` + `assess_renewable_hour`, same cost as a fuel hour. Measured
  tick growth will be reported from the polish clone; no CH-1b bound is changed.
- **P8 (MG-5).** Critical roles: `critical_load_requested_power`, `critical_load_delivered_power`
  (`B/mini_depth/rules.py:69`); per-hour served/unserved already exists in the service domain
  (`ServiceHour.critical_delivered_kw`, `unserved_kwh`, `critical_delivered_coverage`, `rules.py:468-488,541-588`),
  enqueued for every hour. Coverage threshold: MINIGRID measures use 0.8 (`B/chain/measures.py:43-61`), bands
  complete 0.80 / partial 0.25 (`config/chain/coverage-policy-v1.json`). Noon MG-5 path:
  `B/site_outcomes/mini.py:561,583-586` (`mini_readings`), reached from the board composition. MD-0 emits both
  critical channels all day (`mechanism-v1.json` derived_channels critical_requested/critical_delivered).
- **CH-6a is not on main** (no `B/chain/outcomes.py`, no `outcomes/outcome_map.py` CONTRIBUTIONS); per §9 R9 the
  MG-5 `kpi` record is noted for CH-6a.

## Overlap with lane 1 (CH-5a2b: `chain/*`, `estate/*`, `site_outcomes/*`, `tools/checks/chain_coherence.py`)

The sheet requires: `B/chain/measures.py`, `measure_impls.py`, `policy.py`, `vocabulary.py`, `opportunities.py`
(`window_hours`), `B/chain/adapters/postgres_chain_inputs.py` + `ports.py` (renewable_hour -> daylight hours,
critical_served inputs), and `B/site_outcomes/mini.py:561,583-586` (delete the noon MG-5 read). `estate/*` and
`chain_coherence.py` are not touched. Expect merge conflicts in `chain/vocabulary.py` (CH-5a2b count claims) and
`site_outcomes/mini.py`; edits are kept local to the named functions.

## Questions (proposed default for each)

- **Q1. MD-0 busy days become ELIGIBLE.** MD-0's busy noon is a charge request in 12:00-13:00 only
  (`mechanism-v1.json` noon.busy_noon); the other 11 daylight hours (06-11, 13-17) have no request, so under R4
  ("ELIGIBLE if any hour is ELIGIBLE") every delivered busy day becomes ELIGIBLE, contradicting the L2m line
  "the busy days are not". *Default:* fixture change, MD-0 new example content: the busy charge request spans the
  whole 06:00-18:00 solar block (`window_local` for busy_noon only), so busy days stay EXCLUDED; spare-solar D12/D13
  unchanged. This rebuilds the MD-0 template (fingerprinted input). Alternative: keep the fixture, list the flips.
- **Q2. "Missing hour" vs hours with no readings at all.** R1 makes an hour with missing pv readings a missing
  hour, and R4 makes one missing hour a missing day. Taken literally, every story day (data 06:00-14:00 local only)
  and every night hour without readings is missing, so every study is UNKNOWN. *Default:* a day's candidate hours
  run from its first to its last hour holding any accepted pv_available reading; inside that span an hour with
  incomplete coverage, or with no reading, is missing; outside it nothing is assessed. A day with no pv reading at
  all is a missing day (GAP-K7). Daylight hours = candidate hours fully covered with every value > 0. The cost:
  a run that stops mid-afternoon reads as a shorter window, not as a gap; the line states `{h}` hours.
- **Q3. Hour membership and "expected readings".** *Default:* an INTERVAL_MEAN reading belongs to the hour holding
  its interval `[start, end)`; "expected readings" = the union of the hour's pv_available intervals covers the
  whole hour (the existing `rules._coverage` union, no gap), at the cutoff `received_at <= k`.
- **Q4. Who applies the daylight rule.** *Default:* the enqueue (0046) is a coarse filter (any positive reading);
  the worker stores a revision for every enqueued hour as today (job semantics unchanged); `daylight_hours(site,
  day, cutoff)` is computed from stored readings at the reader's cutoff and used by `reconcile`, `hour_windows`,
  `read_selected_renewable_basis` (read.py:510), the study `day_heads`, and the measure. A dawn hour's revision
  exists but is never read as daylight. The enqueue trigger enqueues renewable work for an hour when any
  renewable-role reading lands in an hour that already holds a positive pv_available reading (so a late feeder
  reading still recomputes), and for noon when the Site has no in-force pv_available binding.
- **Q5. `mini-opportunity/2` stored shape.** *Default:* each `day_rows` entry keeps today's keys (day decision per
  R4, `opportunity_kwh` = min-low/min-high over its eligible hours) and adds `window_hours` (eligible hours) and
  `hours: [{from, to, decision, opportunity_kwh, constraints, evidence_ids}]`; `selected_hours` pins become one
  per daylight hour; the result adds `window_hours` (min over eligible days). `/1` rows stay readable through the
  existing path; readers branch on `model_version`.
- **Q6. MG-5 on current story days.** `critical_served` over Kobo's 24 h period: an 8-hour run covers 0.33 < 0.8,
  so MG-5 is PARTIAL on every current story day and the board loses its MG-5 number until DD-1 delivers full
  days. *Default:* accept (honest "not measured over the whole day"), report it in the packet; the partial
  prepare proof uses `kobo-daytime` 12-h runs and still shows PARTIAL. Alternative: the period is the hours
  actually run (rejected by me: it would hide undelivered hours).
- **Q7. `critical_served` source.** *Default:* sum the stored per-hour `mini_service` heads over the period
  (served = `critical_delivered_kw` x 1 h, unserved = `unserved_kwh`, demand = served + unserved); coverage = the
  covered share of the period from each hour's `critical_delivered_coverage`; no new reading query.
- **Q8. R7 story kind and the §4.4 prepare.** *Default:* kind `mill-midday` on scenario `kobo-daytime` v1,
  `start D+0d 03:00`, `end D+0d 15:00` (06:00-18:00 local, the scenario's 12 h), received D+0d 16:00, no new
  scenario; the domain Action ("Run the grain mill at midday on sunny days") is recorded at story time on the
  headroom thread and its case completed (ACTION_ACCEPTED -> ACTION_APPLIED). The partial prepare proves the
  kind, the daylight hours and the study class; R8 is reported as found.
