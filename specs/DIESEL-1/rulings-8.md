## 9k. Ruling DIESEL-1-R3k: K4a pre-flight stop (two unfiltered Finding readers)

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude. Main at `662b2cf91` (R3j). K4a stopped at pre-flight with no code written (worktree `AssetOpsV1-k4a` clean).
- READ = the Architect read the code at `662b2cf91`; nothing was run or measured.
- **This ruling amends §9j.1(2), §9j.8 and §9j.9 for K4a.** Read it alongside §9j.1–§9j.9. Everything not named here stands.

### 9k.1 What the stop found (READ, confirmed)

1. `PostgresFindingStore.findings_over` (`B/analytics/adapters/postgres_finding_store.py:460-474`) reads every `finding_revision` of a Site, with no domain or analytic filter. Its three callers are all dispatch reads:
   - `scheduling/upstream.py:139`. It feeds the served mini Site overview (`site_overview/read.py:159-181`), where a fuel Finding could become the DISCOVERED Finding and add a CONSEQUENCE_PENDING blocker.
   - `analytics/finding_read.py:630` `window_state`, which serves `GET /api/sites/{code}/finding-windows/{day}` (`finding_api.py:102`). The fuel Finding cites no dispatch window, so `:650-653` would read FINDING_MATCH_PENDING.
   - `scheduling/health.py:254`, which supplies `stale_no_work`'s input.
   - There is also a defect that exists today: an open cold Finding (`episode_end` NULL, as `cold_apply` writes it) makes `:467` compare None with a datetime and raise. This is the same defect FIX-S4-DOMAIN fixed in `episodes` (`:133-146`, `backend/tests/test_s4_finding_domain_filter_postgres.py`).
2. `PostgresConsequenceStore.latest_revisions_overlapping` (`B/financials/adapters/postgres_consequence_store.py:386-397`) is unfiltered. It supplies the targets for `ASSUMPTION_PUBLISHED` work (`B/financials/recompute.py:230-232`). That work is written by `financial_consequence_dirty_on_assumption` (`0011:338-350`) on every `financial_assumption_revision` insert: diesel, EV tariff and productive price, on every Site, with no domain test. The mini consequence drain runs on **every** Site (`scheduling/tick.py:492-497`, no site-type gate). `derive()` (`recompute.py:169-177`) would run fc2 on the fuel Finding and append a `financial_consequence_revision` that cites it (an S2 breach), or fail the work. **§9j.1(2) was incomplete:** it closed only the Finding-revision trigger.
3. **The third path is safe, and this ruling adds a test to keep it that way.** `financial_consequence_dirty_on_evidence` (`0012:102-130`) enqueues `EVIDENCE_ACCEPTED` work for the latest revision of **every** Finding whose episode overlaps an accepted `generator_power` reading, and the fuel Finding is one of them. Kisiwa's night runs overlap its episode, so such work will exist. The worker no-ops it before `derive()`: `evidence_no_op` (`recompute.py:102-103`) returns `NO_OP_ASSET` because the fuel Finding's `generator_asset_id` is NULL (§9j.4), which never equals the reading's asset. So no row is written. The work row is still enqueued and drained as a SUCCEEDED no-op. That is acceptable, and 0012 is not edited.

### 9k.2 Decision: filter both readers in SQL, positively, to the dispatch domain

**Options weighed:**
- **(A) A positive domain filter in both readers. Chosen.**
  - It puts the fix where the wrong set is produced, and it follows the precedent: FIX-S4-DOMAIN's `episodes(..., domain=DOMAIN, analytic_id=DISPATCH_ANALYTIC_ID)`, and the 0022 trigger's `WHEN (NEW.domain = 'mini_grid')`.
  - No caller or test fake changes: the new parameters are keyword defaults, and the fakes in `test_s4_schedule_upstream_unit.py:28,136`, `test_s4_evidence_drain.py:83` and `test_s4_consequence_cause_dispatch.py:22` keep their signatures.
  - It also protects the next domain. A deny-list (`domain <> 'fuel_balance'`) is rejected for that reason.
- **(B) The recompute worker skips non-`mini_grid` targets.** Rejected. It changes the `(finding_id, revision_id)` target tuple and the `ConsequenceStore` protocol, so the test fakes would break (S5). It leaves `findings_over` unfixed. And it moves a storage predicate into the worker.
- **(C) A `WHEN` clause on the assumption trigger in 0056.** Not possible. A `financial_assumption_revision` row has no Finding domain. Narrowing by `assumption_key` would not help either, because Kisiwa's diesel price is exactly what must still re-price its dispatch Findings.
- **(D) Defence in depth in `load_input_on` (`postgres_consequence_store.py:96-110`).** Not now. It has other `known_at` callers (W3-01 Run 6, Trial comparison), and with (A) in place plus §9k.1(3) every target path is closed. This goes on the after-the-demo list: "fc2 `load_input_on` refuses a non-`mini_grid` revision".

**Literal changes (K4a):**
1. `B/analytics/adapters/postgres_finding_store.py` `findings_over`:
   - The signature becomes `findings_over(self, tenant_id, site_id, lo, hi, domain: str = DOMAIN, analytic_id: str = DISPATCH_ANALYTIC_ID)`.
   - The SQL gains `AND r.domain = :d AND r.analytic_id = :a`, bound to those two parameters. The docstring gains: "FIX-K4a (DIESEL-1-R3k): one domain's and analytic's Findings only (the `episodes` predicate); a Site's fuel-balance, cold or EV Findings never reach the dispatch readers."
   - Nothing else in the method changes. The Python-side overlap filter at `:467` stays as it is; it now sees only dispatch rows, whose `episode_end` is never NULL.
   - The `finding_read.py:239` `FindingReadStore` port signature gains the same two keyword defaults. That is a type-only line.
2. `B/financials/adapters/postgres_consequence_store.py` `latest_revisions_overlapping`:
   - The SQL gains `AND r.domain = 'mini_grid'` (a literal, mirroring the 0022 trigger's `WHEN`; no analytic filter and no new import).
   - The docstring gains: "FIX-K4a (DIESEL-1-R3k): `mini_grid` revisions only, the domain the fuel-cost work triggers cover (0022); the dispatch fuel-cost model is never derived for another domain's Finding."
   - The signature does not change.
3. **No caller, no worker and no migration changes** for this ruling. 0056 stays as §9j.3 specifies.

### 9k.3 Effect on Kobo, Cold and EV (READ)

- **Kobo:** it holds only `mini_grid` dispatch Findings, so both readers return byte-equal results. No Kobo board, overview, Finding-window, golden or capture changes.
- **Cold and EV Sites:**
  - `findings_over` on a cold or EV Site now returns `[]` instead of that Site's cold or EV Findings (and no longer raises on an open cold Finding). Its consumers are dispatch-only:
    - the mini overview (`site_overview/read.py:136-138`, which reads `dispatch_read.window`);
    - `finding-windows`, whose only frontend callers are `F/sites/PerformanceDispatch.tsx:564` and `F/sites/SiteFindingEvidence.tsx:1176`, both dispatch pages;
    - health's `stale_no_work`, where the narrower input can only remove alarms. The builder found that none fire today.
  - The Cold and EV overviews are separate routes (`coldSiteClient.ts:256`, `evSiteClient.ts:259`). The board reads domain-filtered heads (`postgres_chain_read.py:27-45`). **No served Cold or EV output or golden reads either function.**
  - `latest_revisions_overlapping` on an EV Site (EV tariff publications fire the 0011 trigger) no longer offers EV Findings to `derive()`. Today that work runs the dispatch fuel-cost model on a non-dispatch Finding. Removing it fixes a defect that exists today, outside the served EV reads (EV money reads `ev_consequence_*`).
  - **Deviation recorded, K4a-DEV-1:** "dispatch readers and the fuel-cost recompute target read are filtered to their domain; cold/EV Sites no longer offer their Findings to them". The packet lists it with this paragraph. This is **not** stop S6, because S6 covers served bytes.
- **If the narrower set shows up in any served output, it is a stop (S8, below).** That applies whether it shows up in an existing test, a Cold or EV golden, or K8's all-26 recapture.

### 9k.4 Extra files and memberships (approved)

- `B/chain/threads.py:31` `SUBJECT_COLUMN` gains `"fuel_balance": "subject_asset_id"`. This is already §9j.4 and §9j.9 item 6, and is confirmed here.
- `T/checks/configuration-persistence.ps1`, membership only:
  - `$consequenceTables` (`:746-748`) gains `'fuel_residual_consequence_revision'`.
  - A `$fuelTransactionOwner = 'backend/assetops_backend/fuel_balance/findings_service.py'` is declared beside `$coldTransactionOwner`. It is added to every list in which `$coldTransactionOwner` is an allowed transaction owner, and to the owner-existence loop at `:1841`.
  - No new probe is added in `tools/writer_guard_probes.py`. If the guard demands one, that is stop S-g (below).
- **Scope of §9j.9 widened:** item 3 now also covers `findings_over` and its docstring. Item 4 now also covers `latest_revisions_overlapping` and its docstring. `B/analytics/finding_read.py` (the `:239` port line only) is added. Nothing else changes.

### 9k.5 Tests (added to §9j.8 B; no new test file)

Each "must fail" names the mutation that the reviewer applies to a scratch copy.

- **B7. `findings_over` excludes the fuel Finding.**
  - Setup: on the K4 test Site, one dispatch Finding (from the Kobo import already used by B) and one fuel Finding raised through `raise_night`, with overlapping episodes.
  - `findings_over(t, s, lo, hi)` over the overlap returns only the dispatch Finding's id. Called with `domain="fuel_balance", analytic_id="fuel-balance-1"`, it returns only the fuel Finding (this makes the test non-vacuous).
  - `FindingReadService.window_state` for a day the fuel Finding overlaps lists no fuel Finding id in `findings`.
  - Must fail if the `r.domain`/`r.analytic_id` predicate is removed.
- **B8. Recompute never derives on the fuel Finding.**
  - Setup: after B7's fuel Finding exists, publish a diesel price revision on that Site through the assumption store. This fires `ASSUMPTION_PUBLISHED` over the night.
  - Run `build_recompute_worker(url).run(t, s, limit, now=...)`.
  - Expected: the work is SUCCEEDED; the dispatch Finding gets its consequence as before; **no** `financial_consequence_revision` row has the fuel Finding's id; `latest_revisions_overlapping` over the night returns no fuel id.
  - Must fail if `AND r.domain = 'mini_grid'` is removed: then a row cites the fuel Finding, or the work fails.
- **B9. The evidence path no-ops.**
  - Setup: accept one `generator_power` reading that overlaps the fuel Finding's episode.
  - The enqueued `EVIDENCE_ACCEPTED` work for the fuel revision finishes SUCCEEDED with `no_op_reason` = `NO_OP_ASSET`, and no `financial_consequence_revision` cites the fuel Finding.
  - Must fail if `fuel_apply` writes a non-NULL `generator_asset_id`. The subject CHECK refuses that write, so for a scratch mutation the reviewer may instead assert directly on `evidence_no_op` with a fuel-shaped target: `generator_asset_id None` gives `NO_OP_ASSET`.
- **A9 (L0, `test_k4a_fuel_finding_rules.py`).** `evidence_no_op` on a fuel-shaped target (`generator_asset_id None`, a `generator_power` reading on the generator) returns `NO_OP_ASSET`.
- **These must stay green unchanged**, in addition to §9j.8's list:
  - `test_s4_finding_domain_filter.py` and `test_s4_finding_domain_filter_postgres.py`;
  - `test_s4_schedule_upstream_unit.py`;
  - `test_s4_finding_api.py` and `test_s4_finding_read_postgres.py`;
  - `test_s4_consequence_recompute_postgres.py`, `test_s4_consequence_cause_dispatch.py` and `test_s4_evidence_drain.py`;
  - the scheduling health tests (`git grep -l "stale_no_work" backend/tests`).
  - A behaviour edit to any of them is S5.
- DB: only `assetops_k4_test`, as §9j.9 says. No suite.

### 9k.6 Stops (added to §9j.9)

- **S8:** a test listed in §9k.5 needs a behaviour change, or a Cold, EV or Kobo served byte or golden changes because of the filter. Report the diff. Never widen the filter to fix it.
- **S9:** a fourth path writes or derives money for a `fuel_balance` revision: any other reader of `finding_revision` that feeds `derive()`, the fuel-cost reads or the board's money head without a domain predicate. The builder runs `git grep -n "FROM finding_revision" backend/assetops_backend/financials backend/assetops_backend/scheduling` and lists each hit with the predicate it has, or why it is safe, in the packet's pre-flight answer. One `r.domain` predicate per hit is in scope for K4a **only** after this Architect approves it. Otherwise it is a stop.
- **S-g:** the guard requires a new writer probe or a list other than those in §9k.4.
- S1–S7 stand. **S7's ceiling is now 1.7.**

### 9k.7 Size, critical path, tripwire

- **K4a: 1.4 to 1.5** (range 1.3–1.7). That is +0.1: two predicates and docstrings 0.02; B7–B9 and A9 0.07; the S9 grep 0.01.
- **Kisiwa total: 17.6 to 17.7.** The increase is reported, not absorbed.
- **Critical path:** about 8.3–8.4 plus 0.1, so **about 8.4–8.5 lane-units**. That is below the 9.75 tripwire, with 1.25 of headroom. No cut is needed, no owner question arises, and the demo date is unchanged at about +3.25 working days.
- **Plan HTML (coordinator):** K4a becomes 1.5 and DIESEL-1-R3 becomes 17.7. The rulings table gains "DIESEL-1-R3k: dispatch Finding readers and the fuel-cost recompute target read filtered to their domain (FIX-S4-DOMAIN pattern); evidence path no-ops on the fuel Finding (`NO_OP_ASSET`); K4a 1.5". The after-the-demo list gains "fc2 `load_input_on` refuses a non-`mini_grid` revision".

### 9k.8 Owner questions

None. For the owner's information, in plain words: before building, the builder found two places where the system would have mixed the new "unexplained fuel" finding into the generator's fuel-cost checks. That could have given it a fuel-cost figure it must never have, or made the Kisiwa overview look out of date. Both places now look only at generator findings, as one similar place already does. This also closes a small existing gap on the cold-room and EV sites. Nothing on their screens changes. The work grows by a tenth of a unit, and the demo date does not move.

---

## 9l. Ruling DIESEL-1-R3l: the K5 and K7 consolidated cards

- Architect: Claude, 2026-11-08. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `0c4aa7310` (K0 merged `a268b3ff6`; K1, K1a, K2, K3, F0/F0e merged; K4a in build in `AssetOpsV1-k4a`; A3 in pre-flight in `AssetOpsV1-a3`).
- Owner decisions in force, verbatim: `.agent/owner-scenario-data-2026-11-07.md` ("dont be limited by existing data, data that is reasonable and can reflect a situation can be legitmately added via a scneario for days that are not covered today"; "this is not true, these are injected through operational actions"); `.agent/owner-missing-fuel-2026-11-07.md` ("'Unexplained fuel', never 'theft'"); `.agent/owner-kisiwa-scope-2026-11-07.md` ("Build it, with the action link (Recommended)"); `.agent/owner-diesel-night-window-2026-11-07.md` (a night runs "6 pm to noon").
- **These two cards replace** the K5 and K7 rows of §8.4 and §9.5, §8.6's Action time, §8.4's "Wording (K5)" block (K4a owns those two strings now, §9j.7) and §9j.14's K5 and K7 bullets. Builders read only their own card. Paths use the header's short forms; `T/` = `tools/`. READ = the Architect read the code at `0c4aa7310`; nothing was run.
- **Honesty rules H1–H5 (§8.2) bind both cards.** Client copy never says theft, stolen, stole, siphon or pilfer, and never implies them. Every client literal below was checked by hand against guard V's whole-word terms (`F/test/productVocabulary.json`): none uses run, runs, ran, running, load, claim, candidate, necessary, analytic, scenario, simulation, binding, mapping, stage or fixture. "Modelled use" replaces "running" (K4a's precedent). Guard V's own run is the builder's acceptance (stop S-a).

### 9l.1 Code reality and the decisions it forces (READ)

1. **The F0 world sits at absolute dates, but the demo story moves with the database clock.** The promoted log `C/operational-actions/kisiwa-001-operational-actions-v1.yaml` holds UTC instants from `2026-10-01` to `2026-10-11`. The combined prepare places every story day relative to `S = floor_utc_day(DB now) − 2 d` (`T/demo_combined.py:139-142`). The Portfolio and Findings week runs from `S−6d` to `S+1d` (`:202-205`). Today `S` is about 6 November, so:
   - the October nights would fall outside the week;
   - the Protect line (K4b, KIS-8a) would never show night 4;
   - the Work API's 30-day backdate rule (`B/work/model.py:36-37`) would soon refuse the records.

   **Decision: the Kisiwa story is the F0 world moved by a whole number of days.** This is the EV pattern (`base_e_start` plus `day_delta_days`, `T/demo_combined.py:161-163`).
2. **A whole-day move changes no physics and no published reading.**
   - The day document is date-free (`T/probe_kisiwa_nights.py` `day_document(soc, fuel)`).
   - The publication draw is keyed by seed, stream and **step index** (`S/observation/transform.py:189-201`), not by instant.
   - Kisiwa's zone (`Africa/Dar_es_Salaam`, UTC+3) has no daylight saving.

   So run k at `start + N days` gives F0's trajectory, readings, dropouts, gap and dips exactly. K7 proves this for each run (the physics guard) and each night (KIS-3). Any difference is a stop, never a retune.
3. **The log is named by version and never edited, so a moved log is a new log.** K0 reads `{root}/{log_id}-v{log_version}.yaml` and freezes its sha256 (§9f.2 (5)).
   - K7 therefore writes a derived log for each prepare, into the work folder. Its own id is `kisiwa-001-story-{yyyymmdd of night 1}`, version 1.
   - K7 hands `YamlOperationalActionLog(root=<work>/operational-actions)` to run setup.
   - The derived log's content is v1 with every `at` (and `sensor_disconnected.at`) moved by N days. Nothing else changes.
   - The shipped v1 file, its hash `77777c82…b634` and K0's pins are untouched.
4. **Every action already sits inside one run's day.** Run k runs from 15:00 local on day k to 15:00 local on day k+1. In those terms:
   - the delivery is in run 2;
   - the removal and the sensor span are in run 4, and so is the night-4 dip;
   - the seal and sensor-power actions are at run 6's start, which is inside `[start, end)`;
   - each after-change dip is in its own run, 6 to 10.

   No v2 action is needed: the story uses exactly F0's actions. K0's residual (an action that straddles a run start is silently dropped) is closed by a mechanical check (KIS-9 (c) and an L0 test), not by trust.
5. **The boards read as known at story cutoffs, so every stamp must be a story instant.**
   - K3's CLI stamps the database's wall clock (`B/fuel_balance/worker.py`). That clock is after every story cutoff, so boards for story days would not see the windows.
   - K3's and K4a's stores take a test-only clock override. It is constructor-only (§9d.4); K4a's form is `build_fuel_finding_service(…, test_db_clock_override=)`.
   - K3's `worker.main(argv, store=…)` takes an injected store (`host/tests/test_k3_fuel_balance_parity.py:263`).

   **Decision:** K7 calls the K3 CLI entry point in process, with an injected store whose clock is the story instant. It calls K4a's service the same way. Tools already set this seam for story stamps (`T/demo_combined_mill.py:138`, `:146`).
6. **The Finding cannot exist at 12:30 local on day 5.** Night 4's data arrive with run 4, which ends at 15:00 local on day 5 (§8.3: day-runs run 15:00–15:00). §8.6's "12:30 local … after the closing reading" came before that reading was delivered. **Corrected:** the Action is raised at **16:00 local on day 5**. By then run 4 has been received (+10 min), assessed (+30 min) and raised (+31 min). The effective instant (15:00 local, run 6's start) and the partition of nights are unchanged.
7. **Kobo's prepare must not move.**
   - `T/demo_combined.py` treats "all Sites" as exactly three in several places (`:100`, `:151`, `:176-182`, `:487`, `:533`, `:551`).
   - No tick may run before Kobo's mill step (`:498-501`).
   - The chain backfill takes `--site` (`B/chain/backfill.py:4`, `:33`), so a Kisiwa-scoped threads step touches no Kobo thread.
   - The S3 dispatch worker (`host/tests/test_s6_verification_replay.py:112-115`) drains every pending job, so K7 never calls it. Kisiwa's dispatch windows are assessed by the prepare's existing ticks and drains, as Kobo's `tick` days are.
8. **The Site Finding page is dispatch-shaped and has no domain filter.** `GET /api/sites/{code}/findings/{id}` reads `finding_detail` with no domain predicate (`B/analytics/finding_read.py:359-372`). It renders dispatch currentness and windows (`B/finding_api.py:111-143`), so a fuel Finding there would read wrongly. **Decision:** the fuel Finding gets its own address, as the mill verdict did (`DOMAIN_VERDICT`, `F/shell/operatorSiteRoutes.ts:593-594`). That means a new Ref kind `FUEL_FINDING` and the route `/sites/{site}/fuel-findings/{id}`. The dispatch route is not edited.
9. **The Kobo Fuel page is an hour read** (`F/sites/MiniPerformance.tsx:1574-1622`, `GET …/mini-depth/fuel`), but Kisiwa's night check is K3's stored window. **Decision:** the Fuel page has two modes:
   - **night mode** iff the Site has at least one stored fuel-balance window as known;
   - **hour mode** otherwise, exactly as today and byte-equal (Kobo).

### 9l.2 K5 card: the Fuel page night mode, the fuel Finding page and the Site Findings fuel panel, 1.3 (range 1.15–1.5)

**What K5 delivers.**
- **Site › Performance › Fuel in night mode,** on a Site with stored windows:
  - a night selector;
  - the v69 `fuel` cards, waterfall and bridge, filled from the stored window;
  - a "Deliveries and tank dips" table;
  - the reworded notice (K4a's constant, imported);
  - a "Finding for this night" panel.
- The **fuel Finding page** at its own address, with K4a's server lines.
- A **"Fuel checks" panel** on the Site Findings index, only when the Site has a fuel Finding.
- The read routes for all three. All text is formatted on the server; the browser formats no number.
- The `FUEL_FINDING` Ref kind.
- **Unchanged:**
  - Kobo's Fuel page in hour mode: every byte except K4a's two reworded strings. K5 does **not** edit those two lines (`FUEL_NOTICE` and the RESIDUAL row at `F/sites/MiniPerformance.tsx:1310-1311`, `:1343`).
  - every dispatch Finding page and route;
  - every Cold and EV byte;
  - K3's and K4a's write paths.
- **Moved out of K5:** the fuel Finding's entry in the **estate** Findings lists goes to K8 (+0.15 there), with the four-Site lists K8 already owns.

**Phases (K5 can start before K4a merges).**
- **Phase A, now (about 0.75):**
  - the pre-flight;
  - the nights routes and the night text below, except the two K4a lines;
  - night mode and the records table;
  - tests A1–A5, B1–B3 and F1–F4.
- **Phase B, after K4a merges (about 0.45):**
  - `git merge main`;
  - the margin and gap lines, imported from K4a's `B/fuel_balance/finding_text.py`;
  - the fuel Finding route and page, and the Ref kind;
  - the Site Findings panel, and the night page's Finding panel;
  - tests A6–A7, B4–B5 and F5–F8.
- **Captures (about 0.1):** taken after K7-D's Kisiwa scratch prepare has run (§9l.3), against its kept database. K5 merges after the captures.
- K4b may start after K5's phase B build, before K5's captures (lane-1 order).

**Backend: `B/fuel_balance/night_text.py` (new, pure, no I/O).**
- Litres: one decimal, half-even on the exact Fraction (K4a's rule). Phase A copies K4a's one-line helper; phase B replaces it with the import from `finding_text`.
- kWh: one decimal. SFC: as stored. Times: Site-local `HH:MM`. `{date}` = `f"{d.day} {d:%b}"`.
```python
NIGHT_LABEL = "Night of {date} · 6 pm to noon"
STATUS = {
    "UNEXPLAINED": "Fuel balance: unexplained fuel",
    "WITHIN_MARGIN": "Fuel balance: accounted for within the margin",
    "BELOW_MATERIALITY": "Fuel balance: a small difference, below the 40 L the check flags",
    "EXCESS": "Fuel balance: more fuel than recorded",
    "NOT_ASSESSED": "Fuel balance: not checked",
}
STATUS_TONE = {"UNEXPLAINED": "amber", "WITHIN_MARGIN": "neutral", "BELOW_MATERIALITY": "neutral",
               "EXCESS": "amber", "NOT_ASSESSED": "neutral"}
FUEL_REASON_WORDS = {  # K4b imports these (amended, §9l.4); §9j.11's literals, with "no-load" made guard-V safe
    "NO_SENSOR_ACCURACY": "no tank sensor accuracy declared",
    "SFC_MISSING": "no generator fuel rate declared",
    "NO_LOAD_RATE_MISSING": "no generator idle fuel rate declared",
    "MISSING_OPENING": "no tank reading at 6 pm",
    "MISSING_CLOSING": "no tank reading at noon",
    "FUEL_LEVEL_CONFLICT": "two different tank readings at the same time",
    "GENERATOR_KWH_UNKNOWN": "generator power readings incomplete",
    "IDLE_SECONDS_UNKNOWN": "generator state readings incomplete",
}
NOT_CHECKED = "Not checked: {why}"
# cards (label, value, note); labels are the existing ones (MiniPerformance.tsx:1417-1444)
OPENING_NOTE = "Tank reading at {hh_mm}"
DELIVERIES_NONE = "None recorded"
DELIVERIES_NOTE_ONE = "1 delivery record"
DELIVERIES_NOTE_MANY = "{n} delivery records"
DELIVERIES_NOTE_NONE = "Absence of record does not prove none occurred"          # v69 :625, verbatim
USE_NOTE = "Modelled: {kwh} kWh × {sfc} L/kWh, 10 % either way"
USE_NOTE_IDLE = "Modelled: {kwh} kWh × {sfc} L/kWh plus {m} min idle at {r} L/h, 10 % either way"
RESIDUAL_NOTE = {"UNEXPLAINED": "Above the 40 L the check flags", "WITHIN_MARGIN": "Zero lies inside this range",
                 "BELOW_MATERIALITY": "Below the 40 L the check flags", "EXCESS": "More fuel than recorded"}
CANNOT_COMPUTE = "Cannot compute"                                                  # v69 :626
UNKNOWN_VALUE = "Unknown"
# bridge rows: (term, label, evidence basis, treatment); the row shows "{label} · {value}"
BRIDGE = (
    ("OPENING", "Opening inventory", "Tank reading at {hh_mm}", "Declared sensor accuracy ±{a} L"),
    ("DELIVERIES", "Plus deliveries", "{deliveries_basis}", "1 % allowance on each ticket"),
    ("USE", "Less generator consumption", "Generator output × declared fuel coefficient",
     "Modelled range, not a fuel-meter reading"),
    ("CLOSING", "Less closing inventory", "Tank reading at {hh_mm}", "Declared sensor accuracy ±{a} L"),
    ("RESIDUAL", "Unexplained residual", "Opening + deliveries − use − closing",
     "Compared with the combined margin; never says why fuel left"),
)
DELIVERIES_BASIS_NONE = "No delivery record"     # else DELIVERIES_NOTE_ONE / _MANY
# records table
RECORD_KIND = {"FUEL_DELIVERY": "Fuel delivery", "TANK_DIP": "Tank dip"}           # K2's labels
RECORD_WHEN = "{hh_mm}, {date}"
RECORDS_EMPTY = "No delivery or tank dip recorded this night"
DIP_CONFLICT = "A tank dip differs from the nearest tank reading by more than the declared accuracy plus 10 L."
DELIVERY_LATE = "A delivery was first recorded after the night could be checked."
# Finding panel on the night page
FINDING_NONE_WITHIN = "No finding: the fuel was accounted for within the margin."
FINDING_NONE = "No finding for this night."
FINDING_NOT_RAISED = "Not available yet · the finding for this night has not been raised"
FUEL_NIGHT_LINK = "Open this night on the Fuel page"
# fuel Finding page and the Site Findings panel
LIFECYCLE = {"SUPPORTED": "Supported by the latest check", "NO_LONGER_SUPPORTED": "No longer supported"}
VERSION_ROW = "Version {n} · {lifecycle} · {hh_mm}, {date}"
FUEL_CHECKS_ROW = "{title} · {date} · about {lo}–{hi} L"
```
- Placeholder formats:
  - `{a}` is the stored `accuracy_l`, to 0.1, without a trailing ".0" for whole litres ("10");
  - `{m}` is whole minutes;
  - `{r}` is the rate as stored.
- In phase B, the night page's margin note is K4a's `finding_text.margin_line(accuracy_l)`. Its gap line is K4a's `finding_text.gap_line(spans, tz)`, shown when `gap_minutes > 0`. In phase A both are absent, and the chart note is only the existing sentence "A residual is shown only when every term has a supported range."

**Backend: `B/fuel_balance/night_read.py` (new) and `B/fuel_balance_api.py` (a new router), registered in `B/main.py`.**
- Scope, Site resolution and refusals copy `B/finding_api.py:46-100`: `open_scope`, development access, and 404 for a Site outside the configured tenant.
- Reads go through:
  - K3's `PostgresFuelBalanceStore` (`windows`, `window`);
  - K2's `select_fuel_records`;
  - K4a's `fuel_findings` and `fuel_finding` (phase B);
  - one new read-only store method, `has_windows(tenant_id, site_id, known_at) -> bool` (`SELECT EXISTS … recorded_at <= :k`).
- The provenance block is the one the mini-depth fuel read already returns. PRE-FLIGHT (a) names its builder. It is reused, never re-derived.

The four routes:
1. `GET /api/sites/{site_code}/fuel-balance/nights?from=YYYY-MM-DD&to=YYYY-MM-DD[&known_at=ISO]`
   - Body: `{"site_code", "mode": "NIGHTS"|"NONE", "time_zone", "known_at", "nights": [{"night_date", "label", "state", "status", "tone", "revision"}], "provenance"}`.
   - `mode` is `NONE` iff `has_windows` is false (Kobo); `nights` is then `[]`.
   - Without `from`/`to`, the range is the 14 nights ending with the latest stored night as known.
   - A span over 31 nights, `from >= to`, or a malformed date gives 422 `FUEL_BALANCE_RANGE_INVALID`, with the message "Choose up to 31 nights, with the first night before the last."
2. `GET /api/sites/{site_code}/fuel-balance/nights/{night_date}[?known_at=ISO]`
   - Body: `{"site_code", "night_date", "label", "time_zone", "known_at", "state", "status", "tone", "revision", "window_start", "window_end", "cards": [{"key", "label", "value", "note", "word"}] (4), "bars": [{"key", "label", "value_l", "text"}] (5), "bridge": [{"term", "label", "value", "basis", "treatment", "evidence_count"}] (5), "notes": [...], "records": [{"code", "kind", "when", "volume", "occurred_at"}], "finding": null | {"finding_id", "title", "text", "href"}, "finding_note": str | null, "provenance", "links": {"evidence", "fuel_page"}}`.
   - Card labels are the existing ones (`MiniPerformance.tsx:1417-1444`): "Opening evidence", "Recorded deliveries", "Modelled expected use", "Residual". Bar labels are the existing ones (`:1458-1462`).
   - `value_l` is a float used only to scale a bar. Every visible number is in `text` or `value`.
   - `notes`, in this fixed order:
     - the gap line (phase B);
     - `DIP_CONFLICT`, iff that limitation is set;
     - `DELIVERY_LATE`, iff that limitation is set;
     - `NOT_CHECKED`, iff the night is NOT_ASSESSED.
   - `records`: the K2 fuel records with occurrence in `[window_start, window_end)` as known, ordered by occurrence. `volume` = "{q} L" (whole litres when integral).
   - `finding` (phase B): the fuel Finding whose latest revision, as known, cites this night's window. `title` = K4a's `TITLE`, `text` = its `claim` line, `href` = `/sites/{code}/fuel-findings/{id}`.
   - If there is no such Finding, `finding_note` is `FINDING_NONE_WITHIN` for WITHIN_MARGIN, `FINDING_NOT_RAISED` for UNEXPLAINED, and `FINDING_NONE` otherwise.
   - In phase A, `finding` and `finding_note` are both null.
   - No window as known gives 404 `FUEL_BALANCE_NIGHT_NOT_FOUND`, "No fuel check is stored for this night."
3. `GET /api/sites/{site_code}/fuel-findings?from=ISO&to=ISO[&known_at=ISO]` (phase B)
   - Body: `{"site_code", "rows": [{"finding_id", "night_date", "lifecycle", "text", "href"}]}`. `text` is `FUEL_CHECKS_ROW` with K4a's title.
4. `GET /api/sites/{site_code}/fuel-findings/{finding_id}[?revision_id=]` (phase B)
   - Body: `{"site_code", "finding_id", "revision_id", "revision_no", "lifecycle", "lifecycle_text", "night_date", "label", "lines": finding_text.finding_lines(...), "night": <route 2's body for the cited window revision, without its finding block>, "revisions": [{"revision_id", "revision_no", "text"}], "provenance", "links": {"canonical", "fuel_night"}}`.
   - An unknown id, another Site's id, or a revision not of this Finding gives 404 `FUEL_FINDING_NOT_FOUND`, "No such fuel finding for this Site."

**Ref kind** (`B/chain/refs.py`): `fuel_finding_ref(site, finding_id, revision=None) -> _ref("FUEL_FINDING", site=…, id=…, revision=…)`. The kind joins the kinds list and every validator that list feeds (PRE-FLIGHT (c)).

**Frontend.**
- `F/sites/fuelBalanceClient.ts` (new): `getNights`, `getNight`, `getFuelFindings`, `getFuelFinding`. Bodies are typed as above, with the existing `MiniRead` result shape.
- `F/sites/MiniFuelNights.tsx` (new): `MiniFuelNightsPage`, composed of existing components only:
  - `StatusBar`;
  - `MetricCards` and `MetricCard`;
  - `Panel`, `ValueBars` and `ChartNote`;
  - `BoundedPanel` and `DataTable`;
  - `Notice`, with the imported `FUEL_NOTICE`.

  No new CSS, unless PRE-FLIGHT (d) shows a mock budget the existing classes miss.
  - **Night selector** (in place of `MiniHourBar`):
    - a `<nav aria-label="Nights">` holding a select of nights. Each option's text is the server `label` + " · " + the server `status`;
    - two buttons, "Previous night" and "Next night", disabled at the ends;
    - the address carries `?night=YYYY-MM-DD`. Without it, the page opens the latest listed night. A reload reopens the same night.
  - **Order** (v69 `:623-630`, MD-FUEL-K-1):
    1. the status bar: the badge (`status`, `tone`), provenance chips, and `notes` as strip items;
    2. the cards;
    3. "Fuel balance at a glance": the bars and the chart note;
    4. "Balance bridge": five rows, with `evidence_count` and the Evidence link as today's bridge has them;
    5. **"Deliveries and tank dips"**: columns "Time", "Record", "Volume", "Reference"; `RECORDS_EMPTY` when there are none;
    6. the notice;
    7. **"Finding for this night"**: the Finding's title as a link and its `text`, or `finding_note`. In phase A this panel is absent.
- `F/sites/MiniPerformance.tsx`: `MiniFuel` gains an optional prop, `fuelBalance?: FuelBalanceClient`.
  - With the prop, it first calls `getNights(siteCode)`. `mode === "NIGHTS"` renders `MiniFuelNightsPage`, with no hour bar.
  - `mode === "NONE"`, a failed read, or an absent prop renders today's hour-mode branch, unchanged.
  - **No other line of `MiniPerformance.tsx` changes.** The two K4a lines are not touched.
- `F/shell/SiteAnalyticsFrames.tsx` passes `fuelBalance` to `MiniFuel` (one prop).
- `F/sites/SiteFuelFinding.tsx` (new) at `SITE_FUEL_FINDING_ROUTE_PATH = ${SITE_DETAIL_ROUTE_PATH}/fuel-findings/:findingId`. The route and `siteFuelFindingHref(site, id, revision?)` live in `F/shell/operatorSiteRoutes.ts`; `?revision_id=` works as it does on the dispatch page. Layout, in order:
  1. `SitePageHeader`, and `OperatorSiteTabs current="Findings"`;
  2. a status bar: the badge `lifecycle_text`, the `label`, provenance chips;
  3. `BigClaim` with `lines.claim` (or `lines.no_longer`);
  4. a fact list of `lines.gap`, `lines.money`, `lines.margin` and `lines.not_why`, each only when present;
  5. the panel "How the night was checked": the bridge table component shared with the Fuel page, plus the `FUEL_NIGHT_LINK` link to `/sites/{code}/performance/fuel?night=…`;
  6. the panel "Deliveries and tank dips" (the shared component);
  7. the panel "Versions" (`revisions[].text`).
- `F/sites/chainRef.ts` gains `{ kind: "FUEL_FINDING"; site: string; id: string; revision?: string }`.
- `routeFor` gains `case "FUEL_FINDING": return siteFuelFindingHref(r.site, r.id, r.revision)`.
- `F/test/linkRefs.ts` parses the new path back to the Ref.
- `F/App.tsx` registers the route beside `SITE_FINDING_ROUTE_PATH`.
- The Site Findings index (`F/sites/SiteFindingIndex.tsx` or its frame; PRE-FLIGHT (e) names the component): on a MINIGRID Site, a panel "Fuel checks" after the dispatch table, with one link row per `rows[]`. It renders **only when `rows` is non-empty**, so Kobo stays byte-equal.

**MOCK DEVIATIONs (a header comment at each render, and one packet row each).**
- **MD-FUEL-K-1** (kept): a night window (6 pm to noon) with a night selector, instead of v69's hour bar (`:623-630` shows Kobo's selected hour).
- **MD-FUEL-K5-1:** the "Deliveries and tank dips" table. v69's `fuel` screen has no record list; its bridge names "Delivery / operator records" (`:627`).
- **MD-FUEL-K5-2:** in night mode, "Finding for this night" replaces v69's "Inspect existing generator fuel interpretation" (`:629`), which is about the dispatch consequence of a Kobo hour. Hour mode keeps v69's panel.
- **MD-FUEL-K5-3:** the "Fuel checks" panel on the Site Findings index. v69's Findings index lists dispatch Findings only.
- **MD-FUEL-K4-1** (K4a's, cited): the fuel Finding page itself. v69 has no unexplained-fuel Finding and defers "theft detection" (`:630`).

**Tests (localised; no full suite).** Every "must fail" names the mutation the reviewer applies to a scratch copy.
- **A. L0 `backend/tests/test_k5_fuel_night_text.py` (no DB).**
  1. Night 4, from `.agent/DIESEL-F0/probe-result.json` `nights[3].readings` (exact), with a = 10 and SFC 0.355, gives:
     - the residual value "95.7–144.3 L";
     - the status `STATUS["UNEXPLAINED"]` and its `RESIDUAL_NOTE`;
     - the use card's `USE_NOTE` with its kWh and SFC.

     Must fail if litres round half-up: the synthetic band [1.25, 2.35] must give "1.2–2.4".
  2. Night 2: the deliveries value "300 L", the note `DELIVERIES_NOTE_ONE`, the basis "1 delivery record". Night 1: `DELIVERIES_NONE`, with v69's note.
  3. Each state's status, tone and residual note. NOT_ASSESSED gives the value `CANNOT_COMPUTE` and `NOT_CHECKED` with each reason word.
  4. The idle note appears only when `idle_seconds > 0`.
  5. **Wording (local):**
     - every literal in `night_text.py`, lower-cased, holds none of theft, stolen, stole, siphon or pilfer;
     - guard V's `_patterns` (`backend/tests/test_out_b2_vocabulary.py`) pass on each one;
     - the K5 literals join that test's scan list.
  6. (phase B) The margin and gap lines equal K4a's `finding_text` output (imported, not retyped).
  7. (phase B) `FUEL_CHECKS_ROW` for night 4 = "Unexplained fuel overnight · 4 Oct · about 95.7–144.3 L".
- **B. L2 `backend/tests/test_k5_fuel_night_api_postgres.py`, on its own `assetops_k5_test`.** Kobo is imported as in K3's B tests; synthetic windows go through `PostgresFuelBalanceStore.append` with the test clock; records go through K2.
  1. Kobo with no window: nights gives `mode == "NONE"` and `nights == []`. The hour read is unchanged.
  2. With windows:
     - the list is as known (a revision recorded after `known_at` is absent);
     - the default range;
     - the 422 cases;
     - 404 for an unknown night and for another tenant's Site.
  3. The night body:
     - cards, bars and bridge;
     - records ordered, and half-open at both window edges;
     - the order of `notes`;
     - no number left for the browser: every `value` and `text` is a string.
  4. (phase B) With a Finding raised by `raise_night`:
     - the night body's `finding`;
     - the fuel-findings list;
     - the fuel Finding body (lines, `night`, revisions);
     - 404 for another Site's Finding id, and for a dispatch Finding's id. Must fail if the route reads `finding_detail` without the `fuel_balance` domain.
  5. (phase B) `fuel_finding_ref` resolves through the Ref validator.
- **F. Frontend** (`F/sites/__tests__/miniFuelNights.test.tsx`, `siteFuelFinding.test.tsx`, plus the existing route and ref tests):
  1. Night mode renders the server strings verbatim. A static test checks that `MiniFuelNights.tsx` and `SiteFuelFinding.tsx` call no `toFixed`, `Intl.NumberFormat` or `NUMBER.format`.
  2. The selector: with `?night=` absent it opens the latest night; Previous and Next change the address; both are disabled at the ends.
  3. The records table, and its empty text.
  4. Hour mode: with `mode: "NONE"`, with a failed nights read, and with no `fuelBalance` prop, the rendered DOM equals today's. The existing `miniFuelRoutes.test.tsx` passes unchanged except for K4a's two literals. Must fail if night mode renders on `NONE`.
  5. (phase B) The Finding panel: the link, `FINDING_NONE_WITHIN`, `FINDING_NOT_RAISED`.
  6. (phase B) The fuel Finding page: the SUPPORTED lines, the NO_LONGER_SUPPORTED lines, the night link, and `?revision_id=` pinning.
  7. (phase B) `routeFor({kind: "FUEL_FINDING", …})`, and the `linkRefs` round-trip.
  8. (phase B) The "Fuel checks" panel is present with rows and absent with none.
- **Must stay green unchanged:**
  - every existing mini page test;
  - `siteFinding*.test.tsx` and the Findings index tests;
  - K3's and K4a's tests;
  - `test_out_b2_vocabulary.py` (it gains literals only);
  - `tsc`.
- **Guards:** run directly, with no `-ExecutionPolicy`:
  - `tools\check-all.ps1`;
  - `tools\check-architecture.ps1` (with `ASSETOPS_GUARD_PYTHON` if there is no venv);
  - `tools\check-agent-workflow.ps1`;
  - `tools\check-navigation-truthfulness.ps1`;
  - `node tools/checks/frontend-hardwiring.mjs` (no rise);
  - mock-deviation-labels;
  - guards A, W, N, V and M.

  Allowlist joins (rule-8 readers for the new router's reads, the Ref kind lists) are membership only, and the packet lists them.

**Layout evidence at 1440 and 390.** Taken with `node tools/layout-evidence.mjs` against `T/demo_combined.py … serve` on K7-D's kept `assetops_demo3_kisiwa_test`, or the coordinator-run equivalent.
- Pages to capture:
  - Kisiwa Fuel, night 4 (UNEXPLAINED, the gap note, one dip) and night 6 (WITHIN_MARGIN, two dips);
  - the night-2 delivery night, at 1440 only;
  - the fuel Finding page for night 4;
  - Kisiwa Site Findings with the "Fuel checks" panel;
  - Kobo's Fuel page in hour mode, at both widths, compared with main's capture of the same page: only K4a's two strings may differ.
- Before the build, `node tools/measure-mock-panels.mjs .agent/K5-mock-measurements fuel` is run and committed as `.agent/K5-mock-measurements.md`.
- The night page meets those panel budgets. The records table's height cap is sized for 10 rows; the worst case today is 2 dips plus at most 1 delivery a night. `ShowAll` applies after 6 rows.
- There is no horizontal scroll at 390, and every table scrolls inside its own panel.

**PRE-FLIGHT (no code first; batch every question in one message).**
- (a) The mini-depth fuel read's provenance builder (file:line) and its body key.
- (b) Where `B/main.py` registers `build_finding_router`, and confirmation that `host/lab_app.py` serves the same app (so `serve` exposes the new routes).
- (c) Every list or validator a new Ref kind must join, file:line: the backend refs, the chain-coherence link checks, the frontend `Ref` union and its exhaustive switches.
- (d) The `.agent/K5-mock-measurements.md` budgets, and whether the existing mini classes meet them.
- (e) The Site Findings index component and its MINIGRID branch.
- (f) Whether K4a's merged `finding_text.finding_lines` signature matches §9j.7 (phase B).

**Stops (report to the Architect; never design around them).**
- **S-a** guard V or N rejects a literal. Report the message; never reword silently.
- **S-b** any of these changes: a Kobo Fuel-page byte other than K4a's two strings; any Cold or EV byte; any dispatch Finding page or route.
- **S-c** a need to edit any of: K4a's two lines; K3's or K4a's write paths; `B/finding_api.py`; `B/analytics/`; `B/work/` (K2's read is called, not edited); any migration.
- **S-d** the provenance block cannot be reused (PRE-FLIGHT (a)).
- **S-e** the new Ref kind needs any change beyond list membership and one `routeFor` case.
- **S-f** more than 1.5 units.

**Files (approved list):**
- New: `B/fuel_balance/night_text.py`, `B/fuel_balance/night_read.py`, `B/fuel_balance_api.py`; `F/sites/fuelBalanceClient.ts`, `F/sites/MiniFuelNights.tsx`, `F/sites/SiteFuelFinding.tsx`; `.agent/K5-mock-measurements.md`.
- Edited:
  - `B/fuel_balance/adapters/postgres_fuel_balance_store.py` (`has_windows` only);
  - `B/main.py` (router registration);
  - `B/chain/refs.py` (`fuel_finding_ref` and the kind);
  - `F/sites/MiniPerformance.tsx` (the `MiniFuel` prop and branch only);
  - `F/shell/SiteAnalyticsFrames.tsx` (one prop);
  - `F/shell/operatorSiteRoutes.ts`, `F/sites/chainRef.ts`, `F/App.tsx`;
  - the Site Findings index component (PRE-FLIGHT (e));
  - `F/test/linkRefs.ts`.
- Also: the tests above, and guard allowlists (membership only).

**Dependencies, start, branch, DB, size.**
- **Depends on:** K3 merged (yes). Phase B needs K4a merged. The captures need K7-D's scratch prepare.
- **Lane:** lane 1. K5 starts now if lane 1 is free; otherwise the next free builder takes it.
- **Branch:** `task/DIESEL-K5-fuel-screens`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-k5`, from main at or after `0c4aa7310`.
  - `git merge main` (never rebase) before phase B and again before the packet.
  - Opus does the first build and the first review.
  - Commit with `git add -f` of explicit paths.
- **DB:**
  - only `assetops_k5_test` (and its harness clones);
  - the captures read K7-D's `assetops_demo3_kisiwa_test` through `serve` and never write to it;
  - never `assetops_demo3_full_test`;
  - no prepare, tick or suite.
- **Size 1.3** (range 1.15–1.5):

  | Item | Units |
  |---|---|
  | Night routes and text | 0.25 |
  | Night mode and records table | 0.3 |
  | Fuel Finding route and page | 0.25 |
  | Ref kind and Site Findings panel | 0.15 |
  | Tests | 0.2 |
  | Captures and pre-flight | 0.15 |

  That is +0.3 against §9.5's 1.0. The increase covers the Finding's own address and route (§9l.1 item 8), the records table and the Site panel, less the estate-list entry moved to K8.
- **Reading budget:**
  - this §9l.1–§9l.2;
  - §9d.2 (result terms) and §9d.5;
  - §9j.5 (read types) and §9j.7;
  - `F/sites/MiniPerformance.tsx:1308-1622`;
  - `F/shell/SiteAnalyticsFrames.tsx:330-380`;
  - `F/shell/operatorSiteRoutes.ts:150-170`, `:575-600`;
  - `F/sites/chainRef.ts`;
  - `B/finding_api.py:1-145`;
  - `B/chain/refs.py:1-200`;
  - `B/fuel_balance/model.py`;
  - `B/fuel_balance/adapters/postgres_fuel_balance_store.py`;
  - `B/work/adapters/postgres_fuel_records.py`;
  - v69 `frontend/mockups/v69/index.html:623-630`.

