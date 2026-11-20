### 9l.3 K7 card: the Kisiwa story days in the demo prepare, 2.4 (range 2.15–2.7), in two phases, K7-D and K7-F

**What K7 delivers.**
- Kisiwa (KISIWA-001) as the fourth Site of `T/demo_combined.py`, built after EV by `T/demo_combined_kisiwa.py build`. The build covers:
  - the registration;
  - ten day-runs on the story calendar, with F0's operational actions entering through K0;
  - the delivery, dip and site-visit records, through K2's Work API;
  - the ten nightly fuel checks (K3);
  - the unexplained-fuel Finding (K4a);
  - the threads;
  - the Action, with its maintenance request;
  - in K7-F, the plan freeze and the evaluation (K6).
- One Kisiwa-only scratch prepare per phase, with its gate rows.
- **Unchanged:**
  - every Kobo, Cold and EV child, day, instant and step;
  - a three-Site prepare's `story.json` (byte-equal, pinned);
  - the shipped v1 log, the probe files and `probe-result.json`;
  - every product module: K7 edits tools and conversions only.

**Phases.**
- **K7-D (data), 1.9, starts now** (K0, K1, K2, K3 are merged).
  - Everything up to the Action, except the Finding raise and the Action itself, can be built and tested before K4a merges.
  - After K4a merges: `git merge main`, then the raise and Action steps, then the K7-D scratch prepare.
  - **K7-D merges on review ACCEPT with Kisiwa opt-in** (`--sites kobo,cold,ev,kisiwa`). The default prepare stays three Sites.
- **K7-F (freeze), 0.5, after K6 merges** (see "The freeze step" below). It flips the default to four Sites.

**The story calendar: `V/demo-kisiwa-story-v1.json` (new).** Offsets use the existing form `S[+-]<days>d HH:MM` (UTC) and resolve against the prepare's one `S`.
```json
{
  "schema": {"id": "assetops.demo-kisiwa-story", "version": 1},
  "label": "Kisiwa diesel-hybrid example Site: the F0 world (DIESEL-1 §8.3) placed on the story calendar by a whole-day move",
  "base_log": {"log_id": "kisiwa-001-operational-actions", "log_version": 1,
               "sha256": "77777c82d82298ffba77a130f8d9ea2c6bb9a80c491ba4b2ac5248c4b735b634"},
  "base_run1_start": "2026-10-01T12:00:00Z",
  "run1_start": "S-9d 12:00",
  "runs": 10,
  "import_at": "S-11d 09:00",
  "install_at": "S-11d 09:30",
  "setup_at": "S-11d 11:00",
  "received_after_run_end_minutes": 10,
  "assess_after_run_end_minutes": 30,
  "raise_after_run_end_minutes": 31,
  "dip_recorded_after_minutes": 15,
  "site_visit_recorded_after_minutes": 15,
  "story_log_id_prefix": "kisiwa-001-story-",
  "action": {
    "raised_at": "S-5d 13:00",
    "title": "Seal the tank cap, sign the dip log at every shift change, and put the tank sensor on its own protected power supply",
    "owner_label": "Site lead",
    "request": {"occurred_at": "S-5d 13:10",
                "title": "Seal the tank cap and put the tank sensor on its own protected power supply.",
                "narrative": "Seal the tank cap and put the tank sensor on its own protected power supply. Sign the dip log at every shift change."},
    "request_recorded_from": "S-5d 13:10",
    "assign_at": "S-5d 13:20",
    "record": {"occurred_at": "S-4d 12:00",
               "activity": "Tank cap sealed; tank sensor moved to its own protected supply. The dip log is now signed at every shift change."},
    "complete_at": "S-4d 12:05",
    "change_recorded_from": "S-4d 12:10",
    "site_visit": {"occurred_at": "S-4d 12:00",
                   "body": "Tank cap sealed; tank sensor moved to its own protected supply."},
    "case_link_at": "S-4d 12:20",
    "effective_at": "S-4d 12:00"
  },
  "plan": {"freeze_at": "S-4d 12:30"},
  "evaluate_at": "S-1d 13:00"
}
```
- **Derived values:**
  - `delta_days = (resolve(run1_start) − base_run1_start) / 1 day`. A non-integer is stop **S-1** (`STORY_SHIFT_NOT_WHOLE_DAYS`).
  - Run k = `[run1_start + (k−1) d, run1_start + k d)`.
  - Night k = the Site-local date of run k's start.
- **The resulting story (night 1 = `S−9d`):**

| Night (local date) | Run k (UTC) | What happens (the F0 world, moved) |
|---|---|---|
| 1 `S−9d` | `S−9d 12:00` → `S−8d 12:00` | clean |
| 2 `S−8d` | `S−8d` → `S−7d` | delivery of 300 L at `S−7d 07:00` (10:00 local), recorded `07:30` |
| 3 `S−7d` | | clean |
| 4 `S−6d` | `S−6d` → `S−5d` | removal of 120 L at `S−6d 22:00–22:45` (01:00–01:45 local), sensor unplugged `21:50–23:20`; dip at `S−5d 04:00` (07:00 local), recorded `04:15`; nothing records the removal |
| 5 `S−5d` | | run 4 received `S−5d 12:10`; night 4 assessed `12:30` and raised `12:31`; **Action at `13:00` (16:00 local)**; request `13:10`, assigned `13:20` |
| 6 `S−4d` | `S−4d` → `S−3d` | the change at `S−4d 12:00` (15:00 local, run 6's start): seal, sensor power, site visit, maintenance record; COMPLETE `12:05`, link `12:20`; **plan frozen `12:30`**, before night 6 opens at `15:00`; dips at 18:00 and 06:00 local from here on |
| 7 `S−3d`, 8 `S−2d` | | after-nights; night 8 assessed `S−1d 12:30` |
| — | | **evaluation at `S−1d 13:00`** |
| 9 `S−1d`, 10 `S+0d` | run 10 ends `S+1d 12:00` | after-nights; night 10 assessed `S+1d 12:30`, at least 11.5 h before any prepare's DB now (`S+2d 00:00` or later) |

- What the calendar guarantees:
  - Night 4's window `[S−6d 15:00, S−5d 09:00)` lies inside the story week `[S−6d, S+1d)`, so the Portfolio Protect line (K4b, KIS-8a) can show it.
  - Night 8 closes before the S+0 board. The S+0 board's night D−1 is night 9 (WITHIN_MARGIN).
  - Kisiwa's install, `S−11d 09:30`, is distinct from Kobo `S−29d 11:00`, Cold `S−26d 06:00` and EV `S−26d 06:30`. It is later than all three, so Kisiwa builds last, and it is more than `install_min_lead_hours` before run 1.
  - The records' 30-day backdate window (`B/work/model.py:36-37`) holds: the earliest Kisiwa record occurs at `S−7d 07:00`.
- **Order check** (stop S-2, `STORY_CLOCK_ORDER`, the mill's `instants_in_order` pattern). Each instant must come before the next:
  1. the night-4 raise;
  2. `raised_at`;
  3. `request.occurred_at` (≤ `request_recorded_from`);
  4. `assign_at`;
  5. `record.occurred_at`, which equals `effective_at` and run 6's start;
  6. `complete_at`;
  7. `change_recorded_from`;
  8. the site visit's recorded instant;
  9. `case_link_at`;
  10. `plan.freeze_at`;
  11. night 6's window start;
  12. night 8 assessed;
  13. `evaluate_at`;
  14. run 10 received.

**The derived log, written for each prepare: `<work>/operational-actions/kisiwa-001-story-{yyyymmdd}-v1.yaml`,** where `yyyymmdd` is night 1's local date.
- Read `C/operational-actions/kisiwa-001-operational-actions-v1.yaml` from the prepare tree. Assert that its LF sha256 equals `base_log.sha256` (else stop S-3).
- Parse it with `B/runs/adapters/yaml_run_documents.load_yaml_text`.
- Set `log_id` to the story id. Keep `log_version: 1`, `site_code` and `timezone`, and keep every action mapping, in order, with every key.
- Add `delta_days` to each `at` and each `sensor_disconnected.at`, in the same `YYYY-MM-DDTHH:MM:SSZ` form. Nothing else changes.
- Write the file as:
  - four `#` comment lines: "Kisiwa story operational-action log (DIESEL-1-R3l). Derived by tools/demo_combined_kisiwa.py from config/operational-actions/kisiwa-001-operational-actions-v1.yaml (sha256 77777c82…b634) by a move of {N} whole days; no other change. Lab-private: the product never reads this file. Never edit by hand.";
  - then `json.dumps(doc, indent=2, ensure_ascii=True)`, with LF line endings and a trailing newline.

  JSON is valid YAML, so K0's loader reads it unchanged.
- Run setup gets `KisiwaRegistered(store, setup_at, actions=YamlOperationalActionLog(root=<work>/operational-actions))`, and `draft(..., operational_actions={"log_id": <story id>, "log_version": 1})` on **every** Kisiwa run. A run with no effect-bearing action freezes the log with `actions: []` (§9f.2 (2)).
- **Straddle check (K0's residual):** before any run is drafted, every action's span must lie inside exactly one run's `[start, end)`. The span is `[at, at]` for a point action, and `[at, at + duration)` for a removal and for its sensor span. Otherwise it is stop S-4. An L0 test runs the same check on the base log against F0's run list.

**The handover: `V/kisiwa-day-handover-v1.json` (new), written by `T/probe_kisiwa_fuel.py --handover`.** It is needed because the prepare tree is a `git archive` of `backend, gateway, host, simulator, contracts, config, contract-fixtures, tools` (`T/demo_combined.py:397`), so `.agent/DIESEL-F0/probe-result.json` is not available there.
- **Content:** a pure projection of the committed `probe-result.json`:
  ```
  {"schema": {"id": "assetops.kisiwa-day-handover", "version": 1},
   "source": {"probe_result_sha256": <LF sha256 of probe-result.json>, "actions_sha256": "77777c82…b634"},
   "base_run1_start": "2026-10-01T12:00:00Z",
   "runs": [{"k", "start": {"soc", "fuel"}, "end": {"soc", "fuel"}, "intervention_history"}] (10),
   "dips": [{"action_id", "at", "dip_l"}] (11),
   "nights": [{"k", "night_date", "readings": {"state", "gap_minutes", "opening_exact", "closing_exact",
               "deliveries_exact", "delivery_tolerance_exact", "loaded_litres_exact", "use_low_exact",
               "use_high_exact", "residual_low_exact", "residual_high_exact"}}] (10)}
  ```
  Keys are sorted, indent 2, LF. Exact values are F0's text, verbatim.
- `--handover` writes it from the committed result.
- `--check` also asserts that the handover equals the projection of a fresh run, and exits 1 otherwise.
- `--write` is unchanged, `probe-result.json` stays byte-equal, and `--check` still prints "probe result current". `T/probe_kisiwa_nights.py` is not edited.

**The Kisiwa child: `T/demo_combined_kisiwa.py build <url> <work>`.** This is a new subcommand; `register` is unchanged. It refuses any database that `require_prepare_database` (`B/prepare_clock.py`, as the mill tool uses it) does not accept. Steps:
1. **Read and check the inputs.** Read `<work>/story.json` (its `story["kisiwa"]` block, written by the parent, below) and the handover. Write the derived log and run the straddle check.
2. **Register.** `register(url, work, import_at, install_at)` (K1, unchanged; diesel price v1 at install + 1 h).
3. **Build one event timeline,** sorted by instant. Ties go in this order: record posts, then publish, then assess, then raise.
   - **Record posts** go through `build_work_service(url)` (`B/work/composition.py`, the Work API's service, as in `T/demo_combined_mill.py:131-134`). For each post, the store clock is set to the record's recorded instant (`_store.test_db_clock_override`). Bodies are built with `test_w401_work_service_postgres.oprec` and `PRINCIPAL`, exactly as in K3's parity test (`host/tests/test_k3_fuel_balance_parity.py:76-94`).
     - **The `FUEL_DELIVERY`,** from the log:
       - body `f"Fuel delivery of {volume_l} L received, ticket {ticket.reference}."` ("Fuel delivery of 300 L received, ticket KIS-DT-0001.");
       - `occurred_at` = the moved `at`, recorded `recorded_after_minutes` (30) later;
       - quantity `str(volume_l)`, unit L;
       - `source_document_sha256` = the sha256 of the ASCII text `f"Fuel delivery ticket {reference}, {volume_l} L"`;
       - `asset_id` = the tank; key `kisiwa-kis-delivery-1`.
     - **Each `TANK_DIP`:**
       - body `f"Tank dip at the {HH:MM local} round: {dip_l} L."`;
       - `occurred_at` = the moved `at`, recorded 15 min later;
       - quantity = the handover's `dip_l` for that `action_id`;
       - key `f"kisiwa-{action_id}"`.
     - **One `SITE_VISIT`,** covering `TANK_SEALED` and `SENSOR_POWER_PROTECTED` together:
       - body `action.site_visit.body`;
       - `occurred_at` `S−4d 12:00`, recorded `S−4d 12:15`;
       - `case_id` = the Action's maintenance request (step 5); no quantity;
       - key `kisiwa-kis-sealed-1`.
     - `FUEL_REMOVAL_UNRECORDED` posts **nothing**.
   - **Publish run k** at run end + 10 min:
     - the start state comes from the handover's `runs[k−1].start` (the probe's own chaining);
     - the document is `probe_kisiwa_nights.day_document(soc, fuel)`;
     - draft through `host/tests/kisiwa.py` `KisiwaRegistered(store, setup_at, actions=…)`, with the request key;
     - assert READY and that `registered_basis` is present;
     - then call `test_s6_verification_replay._publish_and_accept(<work>/kisiwa-replay/r{k:02d}, run, f"epoch-{k}", run_end + 10 min)` (K3's call).

     Guards. Each failure is stop S-5, reported with both values:
     - the frozen `intervention_history` holds exactly the run's effect-bearing actions (run 2 the delivery, run 4 the removal, the others none), and the frozen log `sha256` equals the derived file's LF hash;
     - **physics:** the last boundary of `run_to_end(run, reg.sim("v7"))` has tank and SOC exactly equal to the handover's `runs[k−1].end`;
     - **dips:** for each dip in run k, the trajectory's tank at the dip instant, rounded half-even to 1 L, equals the handover's `dip_l`.
   - **Assess night k** at run end + 30 min. Call `fuel_balance.worker.main(["assess", "--site", "KISIWA-001", "--from", night_k, "--to", night_k + 1 d], store=<build_fuel_balance_store(url, test_db_clock_override=clock)>)`, with `clock` set to that instant. This is the K3 CLI entry point, in process (§9l.1 item 5). The printed line must be `APPENDED`, revision 1.
   - **Raise night k** at run end + 31 min: `build_fuel_finding_service(url, test_db_clock_override=clock).raise_night(tenant, site, night_k)` (K4a). Night 4 must give `OPENED`, and every other night `NO_FINDING`. Anything else is stop S-6.
4. **Threads, Kisiwa only.** Run `python -m assetops_backend.chain.backfill --site KISIWA-001 --steps a,b,c,d` as a child process in the tree, after the timeline and after the Action (step 5). It never runs for another Site, and the Kisiwa child runs no tick (§9l.1 item 7).
5. **The Action and its change.** These run after the timeline, and every stamp is its story instant. They follow the mill's `record_change` pattern (`T/demo_combined_mill.py:126-184`) with Kisiwa's literals:
   - **The Action:** `build_domain_intent_service(url).create_action(tenant, site, "KISIWA-001", {"domain": "MINI", "origin_finding_id": <night-4 Finding>, "origin_finding_revision_id": <its revision>, "title": action.title, "owner_label": "Site lead", "due_at": None, "raised_at": "S−5d 13:00", "actor": ACTOR, "idempotency_key": "kisiwa-fuel-action"}, PRINCIPAL)`, with the domain store's clock at `raised_at`. PRE-FLIGHT (b) names the two origin keys. A refusal of a `fuel_balance` origin is stop S-7 (K6 rules on the Action path, §9j.14).
   - **The maintenance request:** kind `MAINTENANCE_REQUEST`, `asset_id` None, the request's title and narrative, key `kisiwa-fuel-request`, recorded from `request_recorded_from`. Then `ASSIGN` to "Site lead" at `assign_at` (key `kisiwa-fuel-assign`).
   - **The change:** the maintenance record (`activity`, `occurred_at` `S−4d 12:00`, key `kisiwa-fuel-record`) and `COMPLETE` at `complete_at` (key `kisiwa-fuel-complete`). Both are recorded from `change_recorded_from`, using a second `StepClock`, so nothing is recorded before it occurred. Then the `SITE_VISIT` record of step 3.
   - **The link:** `post_case_link` at `case_link_at` (key `kisiwa-fuel-link`).
6. **Checks in the child: the CLI calls, as known now.**
   - `worker.main(["assess", "--site", "KISIWA-001", "--from", night 1, "--to", night 11], store=<store with the DB clock>)` must print 10 lines, all `REUSED`, revision 1.
   - K4a's `worker.main(["raise", …])` must give night 4 `UNCHANGED` and the others `NO_FINDING`. If that entry point takes no injected service, call `raise_night` per night instead (PRE-FLIGHT (c)).
   - Anything else is stop S-6.
7. **Write `<work>/kisiwa.json`.** It holds:
   - the register result;
   - `delta_days`, and the derived log's path, id and sha256;
   - per run: `run_id`, start, end, received, history, the physics and dip checks, seconds;
   - per record: code, kind, occurred, recorded, quantity;
   - per night: the window id, revision, state, band, gap and stamps;
   - the Finding: id, revision, consequence id, thread id;
   - the Action: id, code, case id, link;
   - the CLI lines;
   - K7-F's plan and verdict.

**`T/demo_combined.py` changes (exact; the three-Site path stays byte-equal):**
- **Constants:**
  - `CORE_SITES = ("kobo", "cold", "ev")`;
  - `SITES = CORE_SITES + ("kisiwa",)`;
  - `SITE_CODE["kisiwa"] = "KISIWA-001"`;
  - `EXPECTED_SECONDS["kisiwa"] = 2520`: 10 days at about 240 s each (K1's and K3's 3–5 min per gateway day), plus 120 s for the register;
  - `KISIWA_STORY_FILE = REPO / "backend" / "conversions" / "demo-kisiwa-story-v1.json"`.
- **`objectives_instants`** iterates `CORE_SITES`. Kisiwa declares no objectives in K7; K8 rules on Kisiwa objectives with the four-Site estate.
- **`resolve_story(db_now, doc=None, days_doc=None, kisiwa=False)`:**
  - every existing loop over `SITES` iterates `CORE_SITES`;
  - only when `kisiwa` is true:
    - `story["kisiwa"] = demo_combined_kisiwa.resolve(S, kisiwa_doc)`, imported inside the function (the module imports `at` and `iso` from `demo_combined`);
    - the four installs are asserted distinct, with Kisiwa's after all three (else `INSTALL_CLOCK_CONFLICT`);
    - Kisiwa's install plus the lead must precede run 1;
    - `"kisiwa"` is appended to `install_order`;
  - `story["installs"]` stays the three core Sites;
  - **with `kisiwa=False` the output equals today's** (pinned, test L0-1).
- **`prepare`** passes `kisiwa="kisiwa" in sites`.
- **`finish_build` and `finish`:** each `set(story["sites"]) == set(SITES)` becomes `set(CORE_SITES) <= set(story["sites"])`. The mini-depth drain in `finish` runs when `{"kobo", "kisiwa"} & set(story["sites"])` is non-empty.
- **`story_links`:** when `"kisiwa"` is in `story["sites"]` and `<work>/kisiwa.json` exists, add these rows:
  - "KISIWA-001 board, morning after the unexplained-fuel night (S-5d)": `/sites/KISIWA-001?date={S−5d}`;
  - "KISIWA-001 board, day S": `/sites/KISIWA-001?date={S}`;
  - "KISIWA-001 Fuel, night S-6d": `/sites/KISIWA-001/performance/fuel?night={S−6d}`;
  - "KISIWA-001 unexplained-fuel finding": `/sites/KISIWA-001/fuel-findings/{id}`.

  `LINK_FORMS` gains `"/sites/KISIWA-001?date="`, `"/sites/KISIWA-001/performance/fuel?night="` and `"/sites/KISIWA-001/fuel-findings/"`. K7-F adds the verification form that K6 names.
- **`--sites` default:** `",".join(CORE_SITES)` in K7-D; `",".join(SITES)` in K7-F.
- **`add-day`** for KISIWA-001 keeps today's refusal (there are no Kisiwa day kinds). Nothing else changes.
- **Not edited:** the Kobo, Cold and EV children, `demo_story_days.py`, `demo-combined-story-v1.json` and `demo-story-days-v3.json`.

**The freeze step (K7-F, after K6 merges).** K6's card is not written yet. K7-F's exact calls are folded into this card at K6's card round. What is fixed now:
- **When:**
  - The plan freezes at `plan.freeze_at` (`S−4d 12:30`): after the case link, and before night 6's window opens.
  - The evaluation runs at `evaluate_at` (`S−1d 13:00`), after night 8 is assessed.
  - Both are story instants, set through K6's service with the test-only clock seam, as the mill step does (`T/demo_combined_mill.py:282-293`).
- **The effective instant** is `S−4d 12:00` (15:00 local, run 6's start). K6's card names the field that carries it: the Action, the case COMPLETE or the plan. If K6 pins a different mechanism, K7-F follows K6's card.
- **The verdict:** K7-F records it **as computed** (VERIFIED, INEFFECTIVE or INCONCLUSIVE) in `kisiwa.json`. It never asserts a verdict. KIS-5 (K9) reads it.
- **What else K7-F does:**
  - it flips the default `--sites`;
  - it adds the verification link form;
  - it extends KIS-9 (e);
  - it runs the second scratch prepare.

**Finish rows** (pure logic in `T/demo_combined_rows.py`, wired in `T/demo_combined_finish.py` after KIS-4; each has L0 self-tests with pass and fail bodies).
- **KIS-3 (moved from K9 to K7, because it checks K7's data).** For nights 1–10, take the latest stored window, as known now:
  - **Exact:** `state`, `reason` (None), `gap_minutes`, opening, closing, D and D_tol equal the handover's night exactly.
  - **Within 1/100000 L:** `loaded_litres`, `use_low`, `use_high`, `residual_low`, `residual_high`. This is K3's parity rule (§9d.6 C): power is published at 0.000001 kW, so §8.4's "exact" is corrected for these five terms.
  - **Reproduced:** the band re-computed by `B/fuel_balance/rules.balance` from the stored terms equals the stored band exactly.
  - **Night 4:** `UNEXPLAINED`; `gap_spans` = F0's `[21:45, 23:30)` UTC (K3's literal) moved by `delta_days`; limitations `("REPORTING_GAP",)`.
  - **Every other night:** `WITHIN_MARGIN`, gap 0, no limitation.
  - **All ten nights:** `idle_seconds` 0.
- **KIS-9 (new): Kisiwa story coherence.**
  - (a) **Records:**
    - exactly one `FUEL_DELIVERY` (300 L, the ticket digest), recorded 30 min after it occurred;
    - eleven `TANK_DIP`s, one per log dip, each recorded 15 min after it occurred;
    - one `SITE_VISIT`, with `action.site_visit.body`;
    - **no** operational record of the Site occurs inside the removal's span or names the removal.
  - (b) Each dip's stored quantity equals the handover's `dip_l` and the build's trajectory check in `kisiwa.json`.
  - (c) Every action of the derived log lies inside exactly one run's `[start, end)` (the K0 residual).
  - (d) **The Finding:** exactly one fuel Finding, SUPPORTED, citing night 4's window revision 1, on one `UNEXPLAINED_FUEL` thread. Its consequence is PRICED at Kisiwa diesel v1. No other night has a fuel Finding.
  - (e) **The Action:** its origin is that Finding; its case is COMPLETE and linked; the site-visit record cites the case. K7-F adds: the plan is frozen at `plan.freeze_at`, and a verdict is stored at `evaluate_at`.
  - (f) Every Kisiwa run's frozen identity names the derived log (its id, version 1, its sha256), and its history holds exactly that run's effect-bearing actions.
  - (g) **Stamps are story instants:**
    - each window's `recorded_at` = run end + 30 min;
    - night 4's Finding revision `created_at` = run end + 31 min;
    - every record's `recorded_at` is as the calendar says.
- KIS-1, KIS-2, KIS-5, KIS-6, KIS-7 and KIS-8 stay K9's (with K4b's KIS-8a). K9's size is unchanged.

**The Kisiwa-only scratch prepare (one per phase).**
- **Command:** `python tools/demo_combined.py --db assetops_demo3_kisiwa_test --work var/demo3_kisiwa prepare --sites kisiwa --cap-seconds 5400`. The database name matches `^assetops_(demo3|polish)_[a-z0-9]{1,20}_test$` (`T/demo_combined.py:53`) and the authorized `*_test` rule.
- **When:**
  - K7-D: after its L0 tests are green and committed, and after K4a has merged into the branch.
  - K7-F: after K6 has merged into the branch.
- **Gate before starting (all required):**
  - **Only one heavy job** on the machine: no other prepare, suite, L2 run or template rebuild. The coordinator confirms the other lanes are idle.
  - **RAM gate:** at least 2.5 GB free for 2 consecutive minutes, sampled every 30 s. The samples go in the packet.
  - `tools/keep-awake-during-tests.ps1` is running (no `-ExecutionPolicy`).
- **During:**
  - Sample free RAM and the prepare's peak working set every 60 s, and record the peak.
  - If free RAM drops below 1.0 GB: stop, drop the DB and the work folder, and report (S-8).
  - **Cap 5400 s:** the tool's 2× rule over about 42 min, enforced by the tool.
  - A stall with no output for 10 min is reported, not retried.
- **Reads:** `T/demo_combined_kisiwa.py check <url> <work>` runs KIS-3, KIS-4 and KIS-9 against the scratch DB and prints one JSON line per row. Every row must pass. The packet records:
  - seconds per Kisiwa day;
  - the register, assess and raise times;
  - the whole wall time (K9's E3 figure).
- **Afterwards:**
  - K7-D **keeps** the database and work folder, for K5's captures (read-only `serve`).
  - K7-F's prepare replaces them: the tool drops and recreates a database whose marker it owns.
  - K7-F runs `drop` after its packet evidence is recorded.

**Tests (localised; no full suite).**
- **L0 `backend/tests/test_k7_kisiwa_story.py` (no DB; it imports the tools as K3's tests do).** Every "must fail" names its mutation.
  1. **The three-Site story stays byte-equal.** `resolve_story(db_now)` with `kisiwa=False`, for two fixed `db_now` values, equals pins taken on main **as the branch's first commit**, before any production edit (the K0 precedent). Must fail if any core loop iterates `SITES`.
  2. **Kisiwa resolve:**
     - the table above, for a fixed `S`;
     - `delta_days` integral, and `STORY_SHIFT_NOT_WHOLE_DAYS` for a half-day `run1_start`;
     - install order, distinctness and lead;
     - `STORY_CLOCK_ORDER` for each adjacent pair swapped.
  3. **The derived log:**
     - its parsed actions, minus `at` and `sensor_disconnected.at`, equal v1's;
     - each moved instant differs by exactly `delta_days`;
     - the header lines, and LF;
     - K0's `freeze_operational_actions` accepts it for runs 2 and 4 with a matching id, and refuses `OPERATIONAL_ACTION_LOG_MISMATCH` if the id is left as v1's.
  4. **Straddle:** the base log against F0's run list passes. A synthetic dip at a run's end instant fails, and so does a removal that crosses a run start.
  5. **Injector bodies:** the delivery, the night-4 dip and the site visit match their literals; the removal yields no body.
  6. **Timeline order,** for a fixed `S`: records come before the publishes they precede, and assess comes before raise.
  7. **Handover:** `--handover`'s output equals the projection of the committed result; `--check` exits 0; a one-character change in the handover makes `--check` exit 1.
  8. **Prepare paths:**
     - `finish_build` takes the after-children path for `{kobo, cold, ev}` and for all four Sites, and not for `{kisiwa}` alone;
     - `objectives_instants` never sees KISIWA-001;
     - `LINK_FORMS` covers every printed Kisiwa link.
  9. **Row self-tests:** KIS-3 and KIS-9 (one pass body, and one fail body per item).
- **Must stay green unchanged:**
  - every existing `T/demo_combined*` test;
  - both probe `--check`s ("probe result current");
  - K0's, K1's, K2's, K3's and K4a's tests;
  - `test_out_b2_vocabulary.py`, which gains only the Action, request and record literals.
- **Guards:** `tools\check-all.ps1`, `tools\check-architecture.ps1` and `tools\check-agent-workflow.ps1`, run directly, with no `-ExecutionPolicy`.

**PRE-FLIGHT (no code first; batch every question in one message).**
- (a) Confirm, with file:line, that `YamlOperationalActionLog(root=…)` reads a work-folder root, and that `host/tests/kisiwa.py` `draft(..., operational_actions=…)` forwards the key.
- (b) The `create_action` body keys for a Finding origin (file:line in the domain intent service), and whether it checks the origin's domain.
- (c) K4a's merged `raise` entry point: does `worker.main` take an injected service or store?
- (d) Confirm that `_publish_and_accept` accepts a K0-frozen run (causes with `origin` and `action_ref`) unchanged. K3 proved it for F0's carrier.
- (e) Where the existing `T/demo_combined*` L0 tests live, so that `test_k7_kisiwa_story.py` follows them.
- (f) `require_prepare_database`'s rule, and confirmation that `assetops_demo3_kisiwa_test` passes it.

**Stops (report to the Architect and the coordinator; never design around them).**
- **S-1** a day move that is not a whole number of days.
- **S-2** a break in the story-clock order.
- **S-3** the shipped v1 log's hash differs from `77777c82…b634`.
- **S-4** an action straddles a run start, or lies in no run.
- **S-5** a run guard fails (history, log hash, physics or dip). Report the run and both values. **Never** change a start state, an action, the seed, the calendar move or the handover.
- **S-6** an assess or raise status differs from this card, or KIS-3 fails. Never edit K3's parameters, the tolerance, the probe or its result.
- **S-7** `create_action` refuses a `fuel_balance` origin (K6 rules).
- **S-8** the RAM floor or the cap is reached.
- **S-9** for a three-Site prepare, a Kobo, Cold or EV step, instant or `story.json` field changes (L0-1); or a need to edit their children, the day list or the shared story file.
- **S-10** a need to edit product code under `B/`, `F/`, `contracts/` or `S/`, or `host/execution_adapter.py`, or the shipped log.
- **S-11** more than 2.2 units in K7-D, or more than 0.7 in K7-F.

**Files (approved list):**
- New: `V/demo-kisiwa-story-v1.json`, `V/kisiwa-day-handover-v1.json`.
- `T/demo_combined_kisiwa.py`: `resolve`, `build`, `check`, the derived log and the injector.
- `T/demo_combined.py`: the changes above only.
- `T/probe_kisiwa_fuel.py`: `--handover` and its `--check`.
- `T/demo_combined_rows.py` and `T/demo_combined_finish.py`: KIS-3 and KIS-9.
- `backend/tests/test_k7_kisiwa_story.py`, and its pins module (the first commit).
- `backend/tests/test_out_b2_vocabulary.py`: literals added to the scan list.

**Dependencies, start, branch, DB, size.**
- **Dependencies:**
  - K7-D depends on K0, K1, K2 and K3 merged (all yes). Its raise and Action steps need K4a merged, and its scratch prepare needs both.
  - K7-F depends on K7-D merged and K6 merged.
- **Lanes:**
  - K7-D: lane 2 after A3, or any builder free now. Its first ~1.2 units need nothing from K4a.
  - K7-F: lane 3, straight after K6 (critical path).
- **Branches:**
  - K7-D: `task/DIESEL-K7-kisiwa-story`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k7`, from main at or after `0c4aa7310`.
  - K7-F: a fresh branch `task/DIESEL-K7F-kisiwa-freeze`, from main after K6 merges, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k7f`.
  - `git merge main`, never rebase. Opus does the first build and the first review in each phase. Commit with `git add -f` of explicit paths.
- **DB:**
  - only `assetops_demo3_kisiwa_test` with `var/demo3_kisiwa` (the scratch prepare); K7 has no other L2 test;
  - never `assetops_demo3_full_test` or any other DB;
  - no tick, no suite, and no `serve` except K5's read-only captures on the kept K7-D DB.
- **Size 2.4** (range 2.15–2.7), +0.15 against §9.5's 2.25.

  K7-D, 1.9:

  | Item | Units |
  |---|---|
  | Calendar, resolver, `demo_combined` changes and pins | 0.35 |
  | Handover | 0.15 |
  | Derived log and straddle check | 0.1 |
  | Build child, runs through K0, and guards | 0.35 |
  | Injector | 0.15 |
  | Assess, raise, threads and CLI checks | 0.15 |
  | Action and change | 0.15 |
  | KIS-3 and KIS-9 | 0.2 |
  | L0 tests | 0.15 |
  | Scratch prepare and evidence | 0.15 |

  K7-F, 0.5:

  | Item | Units |
  |---|---|
  | K6 wiring | 0.15 |
  | Default, links, KIS-9 (e) | 0.1 |
  | Second scratch prepare and evidence | 0.2 |
  | Packet | 0.05 |

  The +0.15 pays for the whole-day move (§9l.1 items 1–3) and for the story-instant stamping (item 5), neither of which §8.4 foresaw.
- **Reading budget:**
  - this §9l.1 and §9l.3;
  - §8.3's declared world; §9f.2 (5)–(6); §9d.4 (store, CLI); §9j.6;
  - `T/demo_combined.py:1-200`, `:360-560`;
  - `T/demo_combined_kisiwa.py`;
  - `host/tests/kisiwa.py`;
  - `host/tests/test_k3_fuel_balance_parity.py`;
  - `T/demo_combined_mill.py:120-300`;
  - `T/demo_combined_kobo.py:355-480`;
  - `T/probe_kisiwa_fuel.py:1-60`, `:200-260`, `:700-804`;
  - `C/operational-actions/kisiwa-001-operational-actions-v1.yaml`;
  - `V/demo-combined-story-v1.json`.

### 9l.4 Effects on other cards

- **K4b:**
  - the board issue links with `refs.fuel_finding_ref(c, finding_id)` (K5), not `refs.finding_ref`;
  - `FUEL_REASON_WORDS` is imported from `B/fuel_balance/night_text.py` (K5), not retyped;
  - K4b starts after K5's phase B build;
  - everything else in §9j.10–§9j.13 stands.
- **K6:**
  - its verification page links the origin Finding with `fuel_finding_ref`;
  - its card names the effective-instant field, and the freeze and evaluate calls K7-F makes, with K7's instants (`effective_at` `S−4d 12:00`, `freeze_at` `S−4d 12:30`, `evaluate_at` `S−1d 13:00`);
  - its pre-flight confirms that `create_action` accepts a `fuel_balance` origin. If K7-D has already stopped on S-7, K6 rules on it.
- **K8:**
  - gains the fuel Finding's entry in the estate Findings lists (+0.15; K8 is now 1.0, range 1.0–1.25 with §9c.4's device-copy risk);
  - rules on Kisiwa objectives;
  - its all-26 recapture adds the Kisiwa pages K5 built.
- **K9:**
  - KIS-3 has moved to K7;
  - the DS-1 beat's dates come from `links`;
  - the E3 Kisiwa figure is K7-F's measured wall time.
- **§8.6 is superseded** for the Action's time: 16:00 local on day 5 (§9l.1 item 6). Its title, effective instant, night 5 and the after-nights stand.

### 9l.5 Order, lanes, critical path, tripwire, size and date

**Remaining Kisiwa order** (lane-units; about 3 per lane-day including review):
```
now (t=0):    K4a (lane 3, in build, 1.5) | A3 (lane 2, pre-flight, 0.91) | K5 phase A (lane 1, 0.75)
              K7-D phase 1 (any free builder; else lane 2 after A3)
t≈0.9:        A3 merged -> K7-D (lane 2, if not started)
t≈1.5:        K4a merged -> K6 (lane 3, 1.5) | K5 phase B (lane 1) | K7-D raise + Action
t≈1.95:       K5 build done -> K4b (lane 1, 1.0)
t≈2.6–2.8:    K7-D scratch prepare (about 45 min machine time) -> K5 captures -> K5 merged; K7-D merged
t≈2.95:       K4b merged -> K8 code (lane 1, 1.0–1.25)
t≈3.0:        K6 merged -> K7-F (lane 3, 0.5, incl. its scratch prepare)
t≈3.5:        K7-F merged -> K8 captures (0.25)
t≈3.75–4.75:  K9 (finish rows, guard, rehearsal prepare)
then:         DS-1 -> E1–E6
```
- **Critical path:** spent 3.65 (F0r, K1, K3) → K4a 1.5 → K6 1.5 → K7-F 0.5 → K8 captures 0.25 → K9 1.0 ≈ **8.4 lane-units**. K6's size is §9.5's figure; its card is not yet written. **That is below the 9.75 tripwire, with about 1.35 of headroom. No cut.**
- **K7-D stays off the critical path** if it merges before K6 does (t≈3.0).
  - Started on lane 2 at t≈0.9, it ends at about 2.8: about 0.2 of float.
  - Started now, it has about 1.0 of float.
  - **Recommendation to the coordinator: start K7-D now, on a free builder.**
- **Lane 1** (K5 1.3 → K4b 1.0 → K8 ≤ 1.25) ends at about 3.55, beside K7-F, and joins at the captures.
- **Sizes:**

  | Unit | Before | Now |
  |---|---|---|
  | K5 | 1.0 | **1.3** |
  | K7 | 2.25 | **2.4** |
  | K8 | 0.85 | **1.0** (the estate Findings entry) |

  Net **+0.6**, reported, not absorbed (the contingency is spent, §9h.8). **Kisiwa total: 17.7 → 18.3.**
- **Demo date: unchanged** at about +3.25 working days (range 2.75–5.25). The extra 0.6 sits on lanes 1 and 2, beside the critical path.
- **Machine time:** two Kisiwa-only scratch prepares of about 45 min each (K7-D and K7-F).
- **E3:**
  - Kisiwa's share is now about 45–50 min, not R2's 25–35. That covers 10 gateway days at 3–5 min each, the register, assess, raise, threads and its mini-depth drain.
  - So **E3 ≈ 1.45–1.65 h of the 3 h cap.**
  - K9 restates the figure from K7-F's measured time. If the rehearsal exceeds 2.5 h, the Architect rules before E3.
- **Plan HTML rows (for the coordinator):**
  - **Build-units table:** the DIESEL-1-R3 row becomes 18.3, with "K5 1.3, K7 2.4 (K7-D 1.9, K7-F 0.5), K8 1.0".
  - **Lanes figure:** K7-D on lane 2 (or on a fourth builder now); K7-F on lane 3 after K6.
  - **Rulings table:** add "DIESEL-1-R3l: K5 and K7 cards; Kisiwa story = F0 world moved by whole days into the story week (derived log per prepare, never editing v1); stamps at story instants through the K3/K4a test-only clocks; Action at 16:00 local (after night 4's data arrive); fuel Finding at its own address (FUEL_FINDING ref); Fuel page night mode; KIS-3 to K7, KIS-9 new".
  - **E3 row:** "Kisiwa: 10 day-runs, about 45–50 min; E3 ≈ 1.45–1.65 h of the 3 h cap".
  - **Machine-time note:** two 45-min Kisiwa scratch prepares.

### 9l.6 Owner questions

None.

For the owner's information, in plain words:
- **The dates move, nothing else does.** The Kisiwa example days are the same ten days we already tested, moved onto the demo calendar so that the missing-fuel night falls in the week the demo shows. The fuel, the readings and the result are identical.
- **The fix is now agreed in the afternoon after the bad night.** Before, it was agreed at lunchtime, before that night's readings could have arrived. Now it comes once they have.
- **New screens for Kisiwa only.** The fuel page gets a night-by-night view for Kisiwa, and the finding gets its own page. Kobo's fuel page stays as it is.
- **The demo date does not move.** The work is about 0.6 unit bigger, all of it outside the longest chain of dependent steps.
- **Preparing the demo takes a little longer.** The full demo preparation takes about 15 minutes more than first estimated. That is still well inside its 3-hour limit.

---

## 9m. Ruling DIESEL-1-R3m: K7-D stop S-7 (the fuel Finding as an Action origin) and the K6 consolidated card, split K6a / K6b

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `4f6a5cae4`. K4a read on `task/DIESEL-K4a-unexplained-fuel-finding` at `ee86b5dea` (review packet; migration `0056_unexplained_fuel_finding`; `fuel_balance/finding_text.py`, `model.py` `FuelFinding`/`FuelFindingReadPort`, `composition.build_fuel_finding_service`).
- Owner decisions in force, verbatim: `.agent/owner-missing-fuel-2026-11-07.md` ("'Unexplained fuel', never 'theft'"); `.agent/owner-scenario-data-2026-11-07.md` ("these are injected through operational actions"); `.agent/owner-kisiwa-scope-2026-11-07.md` ("Build it, with the action link (Recommended)").
- **This ruling replaces** the K6 rows of §8.4 and §9.5, §8.5 (folded in below; its decisions stand except where named) and §9l.4's K6 bullets. It amends one line of §9l.3 (K7-D step 5) and fixes K7-F's freeze calls. Builders read only their part: K6a = §9m.1–§9m.3; K6b = §9m.1, §9m.4; K7 = §9m.5.
- **H1–H5 (§8.2) bind every literal below.** Each client literal was checked by hand against guard V (`F/test/productVocabulary.json`: run/runs/ran/running, load, claim, candidate, necessary, analytic, scenario, simulat*, draft, commit, fixture, stage, mapping, binding, payload, replay, digest, UUID and the closed upper-case codes) and against H4 (theft, stolen, stole, siphon, pilfer). None contains a money figure, a currency or a price. "Modelled use" replaces "running" (K4a's precedent). Guard V's own run is the builder's acceptance (stops S-a6 / S-a6b).
- READ = the Architect read the code at `4f6a5cae4` (and K4a at `ee86b5dea`); nothing was run.

### 9m.1 Code reality: why S-7 fires, and the decisions it forces (READ)

1. **Three independent refusals, not one.**
   - `work/domain_action.py:118` `MINI_SPEC` has `origin=ORIGIN_OPPORTUNITY`, so `_action_body` (`:283-294`) demands the opportunity pair and refuses `origin_finding_*` keys.
   - `work/domain_intent.py:102-109`: a Finding origin needs `revision["domain"] == spec.finding_domain` (no spec has `fuel_balance`), then `tx.selected_pin(revision)`. That is `work/adapters/postgres_work_read.py:299-309` `_pin`, which returns None for any domain other than `mini_grid`, `cold_chain`, `ev_charging`. So even a `fuel_balance` spec would be refused at the pin.
   - **The database refuses it too.** `0051_action_opportunity_origin.py:78-79` `domain_action_mini_origin CHECK ((domain = 'MINI') = (origin_opportunity_id IS NOT NULL))`: a `MINI` Action with a Finding origin cannot be stored.
2. **Options weighed.**
   - **(A) A new Action domain `FUEL_BALANCE`, Finding origin. Chosen.** It follows the Cold/EV pattern (`COLDCHAIN`/`cold_chain`, `EV_CHARGING`/`ev_charging`). `domain_action_mini_origin` stays exactly as it is and, unchanged, forces `FUEL_BALANCE` to carry a Finding origin. The mill's `MINI` contract and every MINI reader stay byte-equal. One DDL line widens `domain_action_domain_chk`.
   - **(B) Let `MINI` take either origin.** Rejected. It relaxes `domain_action_mini_origin`, and several readers treat `MINI` as "the mill" (`actions/verification.py:387`, `verification_families.py:137`, the MB-1 board path). Each would need a second test. It mixes two levers under one literal.
   - **(C) A W1 `action` (the reserve-trial table).** Rejected: its plan columns are reserve-shaped (Foundation change, battery asset, 60-minute windows; 0019, 0052's reserve arm).
   - **(D) Let K7-D write the Action with SQL.** Rejected: it bypasses the sole writer and K7's S-10.
3. **The fuel selection check.** A fuel Finding has no dispatch, cold or EV selection to pin. Its "selected" revision is simply the Finding's latest revision as known, if it is SUPPORTED (K4a's lifecycle, §9j.4). K6a adds that check to the domain-intent transaction and skips `selected_pin` for the fuel domain. `_pin` is not edited.
4. **Readers keyed by Action domain** (`git grep "FROM domain_action"`, READ):
   - `work/adapters/postgres_domain_action_index.py:66-79`: the Cold/EV Action surface. It excludes the mill by `origin_opportunity_id IS NULL`, so a fuel Action would appear there, where the page dispatches by `spec_of` and Cold/EV criteria. **Decision:** both predicates become the positive `domain IN ('COLDCHAIN', 'EV_CHARGING')`. Today this is the same set: 0051 ties `MINI` to the opportunity pair, so `origin_opportunity_id IS NULL` holds exactly for those two domains. The R3k precedent applies (a positive filter, never a deny-list).
   - `work/adapters/postgres_work_read.py:93` `_FINDING_DOMAIN_OF` (the maintenance request's domain-link lineage, `:275`). Without an entry the request page would show the fuel Action's link with broken lineage. **Decision:** one entry, `"FUEL_BALANCE": "fuel_balance"`. The row then reads like the mill's: lineage true, pin None. `backend/tests/test_w504_ev_intent_postgres.py:154` pins the map; it gains that one key (an approved assertion edit; the Cold and EV values are unchanged).
   - Safe as they are: `actions/adapters/postgres_action_store.py:298` (the code collision check) and `:748` (the mill context, which refuses non-MINI); `chain/adapters/postgres_chain_read.py:89`; `chain/adapters/postgres_thread_sources.py:73`, `:185`; `chain/lookup.py:44`; `work/adapters/postgres_work_read.py:52` (codes).
5. **The chain links the Action to the fuel thread with no new code.** `postgres_thread_sources.py:44-56` links a `DOMAIN_INTENT` by `origin_finding_id`, and K4a's thread (`UNEXPLAINED_FUEL`, ASSET, tank) holds the Finding. K7's Kisiwa-only backfill (`--steps a,b,c,d`, §9l.3 step 4) runs after the Action.
6. **But the chain's Action Ref would be wrong.** `chain/site_chain.py:147-152` `action_wire_ref` gives every Finding-origin `DOMAIN_INTENT` an `ACTION` Ref (`/sites/{site}/actions/{id}`, the W1 Action page). The fuel Action has no W1 row, so the link would show "not found". `_SITE_ACTIONS` (`postgres_chain_read.py:83-101`) does not carry the Action domain. **Decision (K6b):** `_SITE_ACTIONS` gains an `action_domain` column (a scalar subquery, like `accepted_at`; no view or DDL change), and `action_wire_ref` sends a `FUEL_BALANCE` Action to its verdict page, as DD1b2-R6 O1 did for the mill.
7. **The verification store is domain-ready but mill-hardwired.**
   - 0052 already made `verification_plan`, `verification_evaluation_request` and `verification_outcome` domain-Action-capable (`domain_action_id`, the three one-of CHECKs). Only the family CHECK (`verification_plan_family`) and the `rule_id`/`plan_version` CHECKs name the families. 0057 adds the fuel arm.
   - `VerificationService.freeze_domain_plan`/`evaluate_domain_plan`/`domain_summary` (`actions/verification.py:356-397`) call `FAMILIES[MIDDAY]` directly, and `domain_summary` refuses non-MINI. **Decision:** the mill methods stay byte-equal. K6b adds three fuel methods beside them, and a separate store context and freeze for the fuel plan, so the mill's `DOMAIN_PLAN_COLUMNS`, `domain_plan_context` and plan wire stay byte-equal. The outcome writer, the outcome read and `example_source_class` are shared unchanged.
8. **Why split.** The origin fix (K6a, about 0.6) unblocks K7-D's Action step and is small enough to merge fast. The verification family, verdict page and board entry (K6b, about 1.4) follow. **One migration (0057), owned by K6a, carries both DDL parts.** K6b then needs no migration, and the family columns are pinned now, in §9m.2.

### 9m.2 Migration `backend/migrations/versions/0057_fuel_verification.py` (owned by K6a)

`revision = "0057_fuel_verification"`, `down_revision = "0056_unexplained_fuel_finding"`. The renumber rule (§8.4) stands: if another migration lands first, K6a takes the next number. The head-agnostic single-head test (§9j.8 B6) catches a miss.

1. **Action domain.** `ALTER TABLE domain_action DROP CONSTRAINT domain_action_domain_chk, ADD CONSTRAINT domain_action_domain_chk CHECK (domain IN ('COLDCHAIN', 'EV_CHARGING', 'MINI', 'FUEL_BALANCE'));` `domain_action_mini_origin`, `domain_action_one_origin`, the FKs and the code-collision trigger are **not** touched. Unchanged, they force a `FUEL_BALANCE` row to carry the Finding pair.
2. **Verification families.** In one `ALTER TABLE verification_plan`, drop and re-add, by the same names:
   - `verification_plan_plan_version_check CHECK (plan_version IN ('reserve-trial-verification-1', 'midday-productive-shift-verification-1', 'fuel-residual-verification-1'))`;
   - `verification_plan_rule_id_check CHECK (rule_id IN ('reserve-trial-1', 'midday-productive-shift-1', 'fuel-residual-within-band-1'))`;
   - `verification_plan_family CHECK (` 0052's `_FAMILY` text verbatim (both arms) `OR (rule_id = 'fuel-residual-within-band-1' AND plan_version = 'fuel-residual-verification-1' AND action_id IS NULL AND applied_event_id IS NULL AND change_id IS NULL AND old_foundation_revision_id IS NULL AND new_foundation_revision_id IS NULL AND battery_asset_id IS NULL AND field IS NULL AND baseline_candidate_seconds IS NULL AND domain_action_id IS NOT NULL AND origin_finding_revision_id IS NOT NULL AND applied_work_event_id IS NOT NULL AND origin_opportunity_revision_id IS NULL AND supersedes_plan_id IS NULL AND triggering_fixture = 'fuel-seal-dip-sensor-power@1' AND baseline_start < baseline_end AND later_end - later_start = interval '14 days' AND baseline_end <= later_start))`.
   - Build the fuel arm with 0052's `_all` helper and copy 0052's `_FAMILY` as `FAMILY_0052` (used by the downgrade). The reserve arm keeps every reserve column NOT NULL, so a fuel row (reserve columns NULL except `origin_finding_revision_id`) can only match the fuel arm.
   - `origin_finding_revision_id` keeps its 0019 FK to `finding_revision`, which is how the plan cites the fuel Finding revision. 0019's `verification_plan_window_order` (`baseline_end <= effective_from AND later_start >= effective_from`) applies unchanged.
   - Nothing changes on `verification_evaluation_request`, `verification_outcome`, `verification_metric` or the 0044 producer (0052 made them domain-capable).
3. **Downgrade.** `LOCK TABLE verification_metric, verification_outcome, verification_evaluation_request, verification_plan, domain_action_case_link, domain_action_intent, domain_action IN ACCESS EXCLUSIVE MODE`. Refuse with `RuntimeError("0057 downgrade requires no fuel-balance Actions or fuel verification plans")` if any `domain_action.domain = 'FUEL_BALANCE'` or `verification_plan.rule_id = 'fuel-residual-within-band-1'` row exists. Otherwise restore 0052's three CHECKs and 0051's domain CHECK (constants `..._0052`, `DOMAIN_CHK_0051`).
4. No other object changes.

### 9m.3 K6a card: the fuel Finding as a domain-Action origin (0057), 0.6 (range 0.5–0.75)

**What K6a delivers.** Migration 0057 (§9m.2); the `FUEL_BALANCE` domain-Action contract; the fuel selection check; the Cold/EV index filter; the request-lineage map entry. **No verification code, no Ref kind, no page, no board edit** (K6b).

**Exact specification.**
1. `B/work/domain_action.py`, beside `MINI_SPEC`:
   ```python
   #: DIESEL-1-R3m: an Action raised from an unexplained-fuel Finding (lever `fuel-seal-dip-sensor-power@1`: seal the
   #: tank cap, sign the dip log at every shift change, put the tank sensor on its own protected supply). Finding
   #: origin (the 0051 CHECK forces it); no declared intent (`DOMAINS` stays the intent-capable Cold/EV set);
   #: APPLIED is its linked case's COMPLETE.
   FUEL_DOMAIN = "FUEL_BALANCE"
   FUEL_FINDING_DOMAIN = "fuel_balance"
   FUEL_MESSAGES = {
       "DOMAIN_INTENT_INVALID": "The fuel Action declaration is incomplete or invalid.",
       "DOMAIN_INTENT_LINK_INVALID": "The declared unexplained-fuel Finding is not its current supported version at this site and time.",
       "DOMAIN_INTENT_CONFLICT": "This Action declaration has a newer version; reload it.",
       "DOMAIN_INTENT_BASIS_CHANGED": "The selected fuel work basis changed; reload the Action.",
       "ACTION_NOT_FOUND": "Action was not found at this site.",
   }
   FUEL_SPEC = DomainSpec(FUEL_DOMAIN, FUEL_FINDING_DOMAIN, (), "Seal the tank cap, sign the dip log, protect the tank sensor's power",
                          (), FUEL_MESSAGES, (), origin=ORIGIN_FINDING, site_type="MINIGRID")
   ACTION_DOMAINS: Mapping[str, DomainSpec] = {**DOMAINS, MINI_DOMAIN: MINI_SPEC, FUEL_DOMAIN: FUEL_SPEC}
   ```
   - `DOMAINS`, `BY_FINDING_DOMAIN`, `_COMMON_BASIS` and `_ANY_BASIS` are unchanged (pinned by test A2). `_action_body` needs no edit: `origin=ORIGIN_FINDING` selects the Finding pair.
2. `B/work/domain_intent.py` `create_action`, the Finding branch (`:101-110`) becomes:
   ```python
   revision = tx.finding_revision(normalized["origin_finding_id"], normalized["origin_finding_revision_id"])
   if revision is None or revision["domain"] != spec.finding_domain:
       raise spec.refuse("DOMAIN_INTENT_LINK_INVALID")
   if spec.domain == d.FUEL_DOMAIN:
       # DIESEL-1-R3m: a fuel Finding has no analytic selection to pin; its selected revision is its latest as known,
       # when SUPPORTED (K4a lifecycle).
       if not tx.fuel_finding_selected(revision["finding_id"], revision["id"]):
           raise spec.refuse("DOMAIN_INTENT_LINK_INVALID")
   else:
       pin = tx.selected_pin(revision)
       if pin is None or (spec.domain == d.EV_DOMAIN and selected_ev_finding(tx, pin, revision["id"]) is None):
           raise spec.refuse("DOMAIN_INTENT_LINK_INVALID")
   origin = {k: normalized[k] for k in ("origin_finding_id", "origin_finding_revision_id")}
   ```
   - The site-type gate (`:94`) already refuses a non-MINIGRID Site, because `FUEL_SPEC.site_type == "MINIGRID"`.
   - `post_intent` already refuses (`:152-153`, no criteria). `post_case_link` already works (domain-independent; `_spec` finds `FUEL_SPEC`).
   - `_check_basis` is never reached for the fuel domain (there is no intent).
3. `B/work/adapters/postgres_domain_intent.py` `_DomainTx` gains:
   ```python
   def fuel_finding_selected(self, finding_id: str, revision_id: str) -> bool:
       """DIESEL-1-R3m: this revision is its Finding's latest by `command_now`, of the fuel domain and analytic, and
       SUPPORTED."""
       return self._c.execute(text(
           "SELECT EXISTS (SELECT 1 FROM finding_revision fr WHERE fr.tenant_id = :t AND fr.site_id = :s "
           "AND fr.finding_id = :f AND fr.id = :r AND fr.domain = 'fuel_balance' AND fr.analytic_id = 'fuel-balance-1' "
           "AND fr.lifecycle = 'SUPPORTED' AND fr.created_at <= :now AND fr.revision_no = (SELECT max(x.revision_no) "
           "FROM finding_revision x WHERE x.tenant_id = :t AND x.site_id = :s AND x.finding_id = :f "
           "AND x.created_at <= :now))"), self._p(f=finding_id, r=revision_id)).scalar_one()
   ```
   `insert_action`'s Finding-pair INSERT (`:139-144`) already writes it. No other store change.
4. `B/work/adapters/postgres_domain_action_index.py:69-79`: in both `action` and `actions_in_window`, `AND origin_opportunity_id IS NULL` becomes `AND domain IN ('COLDCHAIN', 'EV_CHARGING')`. The comment at `:66-67` gains: "DIESEL-1-R3m: positive Cold/EV filter (the same set under 0051's MINI tie); a fuel Action is read through the chain and its verdict page."
5. `B/work/adapters/postgres_work_read.py:93`: `_FINDING_DOMAIN_OF = {**{name: spec.finding_domain for name, spec in DOMAINS.items()}, FUEL_DOMAIN: FUEL_FINDING_DOMAIN}` (import the two names).

**Client wording (K6a):** only the five `FUEL_MESSAGES` (API refusal texts) and `FUEL_SPEC.summary`. They are added to `test_out_b2_vocabulary.py`'s scan list.

**Tests (localised; no full suite).** Each "must fail" names the mutation the reviewer applies to a scratch copy.
- **L0 `backend/tests/test_k6a_fuel_action_origin.py` (no DB, fake tx):**
  1. `action_body` for `FUEL_BALANCE` with the Finding pair normalizes; with the opportunity pair (or both pairs) → 422 with `FUEL_MESSAGES["DOMAIN_INTENT_INVALID"]`. Must fail if `FUEL_SPEC.origin` is `ORIGIN_OPPORTUNITY`.
  2. `set(ACTION_DOMAINS) == {COLDCHAIN, EV_CHARGING, MINI, FUEL_BALANCE}`; `DOMAINS` and `BY_FINDING_DOMAIN` equal their pinned values. Must fail if `FUEL_SPEC` is added to `DOMAINS` (that would make an intent possible).
  3. `create_action` with a fake tx: a `mini_grid` revision → LINK_INVALID; `fuel_finding_selected` False → LINK_INVALID; site type `COLDCHAIN` → LINK_INVALID; selected → 201 with `domain = FUEL_BALANCE` and the Finding pair. The fake's `selected_pin` raises if called. Must fail if the fuel branch falls through to `selected_pin`.
  4. `post_intent` on a stored `FUEL_BALANCE` Action → 422 with the fuel literal.
  5. The five messages and the summary pass guard V's terms and the H4 words.
- **L2 `backend/tests/test_k6a_fuel_action_origin_postgres.py`, own `assetops_k6_test`.** A fuel Finding is raised the K4a way (synthetic windows through `PostgresFuelBalanceStore.append` with the test clock, then `build_fuel_finding_service(…).raise_night`, as §9j.8 B3):
  1. **0057** up/down/up on empty tables. The domain CHECK and the three family CHECKs as pg prints them. Downgrade refused with a `FUEL_BALANCE` Action and with a fuel plan row. Raw inserts: `MINI` + Finding pair, and `FUEL_BALANCE` + opportunity pair, both refused (`domain_action_mini_origin`). A fuel plan row with a reserve column set, or a different `triggering_fixture`, or `later_end − later_start ≠ 14 days`, refused (`verification_plan_family`). Single alembic head, head-agnostic.
  2. **Create:** 201 with an `ACT-` code; an identical retry → 200; another body under the same key → 409.
     - The Finding's later NO_LONGER_SUPPORTED revision → LINK_INVALID. Must fail if `fr.lifecycle = 'SUPPORTED'` is dropped.
     - An older SUPPORTED revision while a newer one exists → LINK_INVALID. Must fail if the `max(revision_no)` predicate is dropped.
     - A revision created after `command_now` → LINK_INVALID.
  3. **Case:** create a `MAINTENANCE_REQUEST`, post a record, `ASSIGN`, `COMPLETE`, then `post_case_link` on the head → 201.
  4. **Index:** `PostgresDomainActionRead` `action(id)` is None and `actions_in_window` omits the fuel Action, while the K6a test's Cold Action (built as `test_w502_*` does) is still listed. Must fail if the predicate reverts to `origin_opportunity_id IS NULL`.
  5. **Request lineage:** the request detail's domain-link row for the fuel Action has `lineage` true and `pin` None.
  6. **Thread link:** after `run_threads` (`chain/backfill.py:33`), one `chain_action_thread` row joins the Action to the fuel Finding's thread.
- **Must stay green unchanged:** `test_w502_*`, `test_w504_*` (except the one pin line, item 5 above), `test_ch9b1_*`, `test_ch9b2_*`, `test_ch9b3_*`, the `test_s4_*` domain-action tests, K4a's tests. Any behaviour edit is stop S-a5.
- **Guards:** `tools\check-all.ps1`, `tools\check-architecture.ps1`, `tools\check-agent-workflow.ps1`, run directly, with no `-ExecutionPolicy`.

**Files (approved list; anything else is stop S-a4).** `backend/migrations/versions/0057_fuel_verification.py`; `B/work/domain_action.py`; `B/work/domain_intent.py`; `B/work/adapters/postgres_domain_intent.py`; `B/work/adapters/postgres_domain_action_index.py`; `B/work/adapters/postgres_work_read.py` (`:93` only); the two test files; `backend/tests/test_w504_ev_intent_postgres.py:154`; `backend/tests/test_out_b2_vocabulary.py`; the K3/K4a head tests only if they still name a fixed head (head bookkeeping, §9j.8 B6).

**PRE-FLIGHT (no code first; batch every question in one message).**
- (a) Every reader of `domain_action` or of `chain_action` rows that dispatches on the Action domain (`git grep -n "spec_of\|ACTION_DOMAINS\|\.domain\b" backend/assetops_backend/work backend/assetops_backend/chain`), with file:line, and what each does with `FUEL_BALANCE`. A reader that raises or mis-renders and is not fixed by this card is stop S-a3.
- (b) The frontend text the maintenance request page shows for a domain link with `lineage` true and `pin` None (the mill's case), with file:line.
- (c) Whether any golden or test asserts the exact `actions_in_window` SQL text.
- (d) That K4a's `raise_night` gives a `finding_revision.lifecycle = 'SUPPORTED'` row with `analytic_id = 'fuel-balance-1'` (READ on the K4a branch).

**Stops (report to the Architect; never design around them).**
- **S-a1** 0057 needs any object beyond §9m.2.
- **S-a2** `domain_action_mini_origin` or `domain_action_one_origin` would need relaxing.
- **S-a3** a PRE-FLIGHT (a) reader fails on `FUEL_BALANCE`.
- **S-a4** a file outside the list, or any Cold, EV or mill served byte changes.
- **S-a5** an existing test needs a behaviour change (head bookkeeping and the one pin line excepted).
- **S-a6** guard V or the H4 scan flags a K6a literal.
- **S-a7** more than 0.8 units.

**Dependencies, start, branch, DB, size.**
- **Before K4a merges:** pre-flight, the migration text (with `down_revision` 0056), the spec, the service branch, the store method and the L0 tests can all be written and run.
- **After K4a merges:** `git merge main`, then L2. **K6a merges before K6b starts its L2 and before K7-D's Action step.**
- Branch `task/DIESEL-K6a-fuel-action-origin`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k6a`, from main at or after this ruling's commit. Opus does the first build and the first review. `git add -f` of explicit paths; `git merge main`, never rebase.
- **DB: only `assetops_k6_test`** (and its harness clones). Never `assetops_demo3_full_test` or any other DB. No prepare, tick, `serve` or suite.
- **Size 0.6** (range 0.5–0.75): migration 0.2; spec, branch, store method, index, map 0.12; L0 0.08; L2 0.15; pre-flight and packet 0.05.
- **Reading budget:** §9m.1–§9m.3; `work/domain_action.py`; `work/domain_intent.py`; `work/adapters/postgres_domain_intent.py:30-145`; `work/adapters/postgres_domain_action_index.py:55-95`; `work/adapters/postgres_work_read.py:50-95`, `:240-298`; `0051_action_opportunity_origin.py:60-100`; `0052_verification_plan_domain.py`; `0019_verification_core.py:40-110`; K4a's `0056_unexplained_fuel_finding.py` and `backend/tests/test_k4a_fuel_finding_postgres.py` (the raise helpers).

