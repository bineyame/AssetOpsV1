## Revision 2 — pre-flight rulings 2026-11-08

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9` on the live main checkout `AssetOpsV1-plan2`). Read-only on
code; no Postgres or heavy run. Owner, verbatim (`.agent/owner-proceed-own-gaps-2026-11-08.md`): "the thing is that
these estiamtes are done based on human elivery speend. just proceed the the implementation of my request and we'll
reassess where are tomorrow". Question files: `AssetOpsV1-g3a/.agent/preflight-G3a.md`, `AssetOpsV1-g2/.agent/preflight-G2.md`,
`AssetOpsV1-g3b/.agent/preflight-G3b.md`, `AssetOpsV1-g1/.agent/preflight-G1.md`, and the DS-1a packet
`AssetOpsV1-ds1a/.agent/review-packet-DS-1a.md` (Spec vs screen 5 and 6; forbidden-word scan).

**Where this revision and Revision 1 or the sections below differ, this revision wins.** Each ruling is numbered after
the builder's question. "Accepted" means the builder's proposal is the spec, exactly as written in the question file.
**Merge order stays G3a → G2 → G3b → G1.** The DS-1a refresh (R1.4, extended in R2-DS1a) follows G1.

### R2-G3a (Lane B)

1. **Accepted.** The order is `gate.open_scope(request, code, True)` (read access, 404, write grant 401/403), then entry
   principal absent → 403 `WORK_WRITE_FORBIDDEN`, then 503 `WORK_STORE_UNAVAILABLE` when `service is None` or
   `site_context is None`, then shape 422, then tank and timezone, then the service. The write grant step stays in.
   §3.2's refusal order is to be read with this step 1b inserted.
2. **Accepted.** `site_context=None` is the keyword default (503 after the principal check). `main.py` builds one
   `fuel_store = build_fuel_balance_store(database_url())`, passes it to `FuelNightRead` as today (which keeps disposal),
   and composes `site_context` from `fuel_store.night_context`: the instant is dropped, and `SQLAlchemyError` (and the
   no-URL `RuntimeError`) map to `WorkStoreUnavailable` → 503 `WORK_STORE_UNAVAILABLE`. No second store.
3. **Accepted.** `{value}` in the body, in the ticket digest text and in `quantity` is `m.decimal_text(Decimal(value))`.
   Example: typed `198.50` stores `198.5` and the body reads "… 198.5 L.". §3.5 G3a gains one unit: `198`, `198.0` and
   `0198` compose identical bodies and digests.
4. **Accepted.** All five keys are required. `ticket_reference` must be present, and null is allowed. A missing key →
   422 `OPREC_ENTRY_INVALID`. For `FUEL_DELIVERY`, `null` → `OPREC_ENTRY_TICKET_REQUIRED`, and `""` or a pattern miss →
   `OPREC_ENTRY_INVALID`. Validation stops at the first failing step in §3.2's order.
5. **Accepted.** These are the `MESSAGES` literals. `OPREC_ENTRY_INVALID`: "The entry, value, time taken, ticket
   reference or key is not valid." `OPREC_ENTRY_TICKET_REQUIRED`: "A fuel delivery needs its ticket reference."
6. **Accepted.** The helper goes in `host/lab_app.py`: `OPERATIONAL_ENTRY_ENV = "ASSETOPS_OPERATIONAL_ENTRY"`, and
   `operational_entry_from_environment() -> Principal | None` raises `ConfigurationError("ASSETOPS_OPERATIONAL_ENTRY must
   be 'on' or unset")` for any other non-empty value. `build_app` calls it before `create_app`, and
   `overrides.setdefault("operational_entry_principal", …)` is set only when the variable is on. Its tests (`on`, unset,
   empty, `yes`) go in the new `host/tests/test_own_g3_entry_env.py`, and §3.5's startup-refusal case moves there.
   G1 depends on this: G1's in-process `app_client` must set the variable in `os.environ` before `lab_app` is first
   imported (see the R2-G1 header).
7. **FYI for G1, ruled in R2-G1 Q8 and the R2-G1 "late delivery" header.** G3a does not change. The 30-day refusal
   stays.
8. **FYI for G3b, ruled in R2-G3b Q2.** G3a does not change. The record-kind filter keeps no fuel chip; fuel records list
   under "All". A fuel kind chip is an after-the-demo item.

### R2-G2 (Lane A)

1. **Accepted.** `scheduled.py` exports `bucket_bounds() -> (time, time)` (from `rules.NIGHT_START/NIGHT_END` and `EDGE`,
   computed through `datetime.combine`) and the pure `night_of(local_dt) -> date | None`, which mirrors the SQL `CASE`.
   No-DB case 1 tests `night_of`. The Rev 1 pin monkeypatches `rules.NIGHT_START` and asserts that both functions move.
   The Postgres file adds one case: readings at local 17:29, 17:30, 12:29 and 12:30, and `schedule_inputs(...).reading_nights`
   must agree with `night_of`.
2. **Accepted.** `ScheduleInputs` (a frozen dataclass) and `DuePlan` live in `fuel_balance/model.py`. `schedule_inputs` is
   added to the `FuelBalanceReadPort` Protocol. §2.6's "`ScheduleInputs` in the adapter" is replaced.
3. **Accepted.** A `_windows_on(c, …)` helper is shared by `windows()` and `schedule_inputs`, in the same transaction.
   The `latest` nights are `[local date of (known_at − record_lookback − 1 day), local date of known_at]` inclusive.
   `schedule_inputs(tenant_id, site_id, record_lookback)` drops the `base_nights` parameter; `due_nights` uses
   `BASE_NIGHTS`.
4. **Accepted.** The signature is `run_site(…, deadline: Callable[[], bool] | None)`, with the `chain_threads` idiom
   before each night.
5. **Accepted**, as proposed: one module-scoped Kisiwa Site through K1's path, registered at DB now − 12 d. Its runs
   end at the last three real-night ends and are accepted with the decision clock at DB now − 10 min. P2 is a night with
   no run. P3 imports Kobo. P5's old night is a fourth run about 10 nights back. P6 runs the CLI at a virtual instant
   before the ticks. The children are real `StageRunner` children. If the file's measured runtime is over 120 s, mark it
   with the repo's existing slow-tier marker; E2 runs it explicitly either way (R1.3).
6. **Accepted: the builder is right, and §2.7 P4 was backwards.** A recorded delivery raises the residual
   (`rules.py:225-227`), and a dip only adds a limitation (`rules.limitations`, "never changes the state"). P4 now reads:
   - (a) DIP_SENSOR_CONFLICT, as written.
   - (b) A `FUEL_DELIVERY`, posted on a WITHIN_MARGIN night, that the sensor does not show. Its quantity is chosen so
     that `rules.balance` gives UNEXPLAINED, and the test asserts the state. The next tick appends a revision that is
     UNEXPLAINED, and the raise is `OPENED`.
   - (c) A work-service **correction** of that record that moves `occurred_at` out of the night. The next tick appends a
     WITHIN_MARGIN revision, and the raise is `WITHDRAWN`.
7. **Accepted, the cheaper form.** The 40-day record is posted through the work store on a `VirtualDbClock` set to
   occurred + 29 d. The test asserts that `schedule_inputs(...).records` excludes it. The no-row proof stays on the
   10-day case only.
8. **Accepted.** The five tick-wiring units go in the new no-DB `backend/tests/test_own_g2_fuel_night_tick.py`, with the
   `FakeStore` and fake runner pattern of `test_fix_cold_drain_stage.py`.
9. **Accepted (a)–(d), with one addition (changed).**
   - (a) A pure `demo_rows.kis11(…)` with 2–3 no-DB cases.
   - (b) KIS-11 is registered right after KIS-9.
   - (c) `Demo.tick` writes `<work>/last-tick.json` from the last stdout line that parses as a JSON object, and removes
     a stale file when no line parses. It also **returns** the parsed report, for G1's per-date check.
   - (d) KIS-11 reads the last-written file.
   - **Addition:** a serve loop running beside the tool can claim the Site, so a tick report can lack a visited
     KISIWA-001 (absent, `SKIPPED_CLAIMED`, or retry back-off). When the report from `Demo.finish`'s closing tick has
     no `fuel_night` stage entry for KISIWA-001, `Demo.finish` runs up to two more ticks, 30 s apart. KIS-11 then fails
     with "KISIWA-001 was not visited by the last tick" only if none visited it. The same retry rule serves G1
     (R2-G1 Q6). One no-DB test covers the retry count.
10. **Accepted.** `schedule_inputs` honours `test_db_clock_override`. The stage composes no override, so P7 stands.
11. **Accepted.** An OPEN night is `{"assess": "OPEN", "revision": None, "state": None, "raise": None}`. It makes no
    raise call and counts as processed, so `processed + deferred == len(due)` always holds.
12. **Accepted.** No-DB: for 0 tanks or 2 generators, `run_site` makes exactly one store call and no assess or raise
    call. Postgres: a Cold-like Site gets empty `reading_nights`, `records` and `latest`.

**Crossing G1:** G1's step 6 quiet rule (`decided_at + 5 min`) is G2's `QUIET`, and G1 reads Demo.tick's returned
report (Q9 c). Added Kisiwa nights are later than S, so KIS-11's story-night `revision = 1` and its one-Finding facts
are unaffected by G1.

### R2-G3b (Lane B)

1. **Accepted.** The client reads `public_code`. A 2xx whose body is not an object with
   `schema_version === "operational-record-1"` and a string `public_code` takes the "could not be confirmed" row, and the
   key is kept.
2. **Changed: neither (a) nor (b).** The success line makes no claim about where the record appears. First line:
   **"Saved as {displayCode(public_code)}, status Submitted."** The fuel second line is unchanged. The list still
   re-reads. Why: the list is newest-recorded-first (`operational_index.py:96`) over a 7-day window, so the demo beat
   shows the dip at the top anyway, and the line stays true for a back-dated or filtered entry. §3.3's outcome row and
   §3.5's test literal change to this text. R1.4's beat still shows the row in the list.
3. **Accepted.** The form is enabled wherever `shown` is true.
4. **Accepted.** The form keeps its selected Site code across the re-read. While the options are empty it shows the
   placeholder and the button is disabled. The kept code is re-selected if present, otherwise the first option. The
   result line survives the re-read.
5. **Accepted.** `SITE_WORK_API_PATH = "/api/sites"`; `createGlobalWorkClient(basePath, sitesPath = SITE_WORK_API_PATH)`;
   an optional `submitOperationalEntry` with the `saved | refused | unconfirmed` union. A client without the method shows
   the 403 row.
6. **Accepted, and required.** The owner may present from another device over plain http on a LAN address, which is not
   a secure context. Use `crypto.randomUUID` when it is a function; otherwise use 16 bytes from
   `crypto.getRandomValues` as 32 lowercase hex. One vitest stubs `randomUUID` as undefined and asserts the
   `oprec-entry-<32 hex>` form.
7. **Accepted.** These fold into MD-OWN-G3-1: "Fuel delivery option, its Ticket row, and the per-reading unit suffix and
   placeholder".
8. **Accepted.** MD-OWN-G3-1..4 appear in code comments and the register only. The visible `MOCK DEVIATION D4 (R362)`
   label stays. The R362 row gets the note "Taken at superseded by MD-OWN-G3-2". R12 is closed by G3b.
9. **Accepted.** The new sentence is a third `<p>`.
10. **Accepted, with one change.** The timing is as proposed (messages appear after the first Submit and then update
    live), and Value and Ticket are trimmed. **Change:** the client also checks the ticket against the server's pattern
    `^[A-Za-z0-9][A-Za-z0-9 /._-]{0,39}$`, and a miss shows **"Use letters, digits, spaces and / . _ - only, up to 40
    characters, starting with a letter or digit."** under the field. Empty still shows "Enter the delivery ticket
    reference.". Why: a typo should get a precise message, not "Check the values and try again." during a live demo.
    §3.5 gains this message in its validation list.
11. **Accepted.** The key is made at the first valid submit. It is cleared on any field edit and on success. It is kept
    after a network error, a 5xx and a 4xx.
12. **Accepted (fields stay enabled).** An edit made while a save is in flight clears the key. On success, Value, Ticket
    and Taken at are cleared.
13. **Accepted.** Taken at is empty on load and after a success. Reading defaults to "Fuel tank dip". Site defaults to
    the first option.
14. **Accepted** as proposed: one `role="status"` `aria-live="polite"` region; the second line for TANK_DIP and
    FUEL_DELIVERY only; the "other 4xx" list; the duplicate row matched on the code; 503 takes the 5xx row.
15. **Accepted.** Only the Operational records By column changes. `WorkRequestHistory` and `SiteActionVerification` are
    after-the-demo items: G1 nights and the live dip are later than every story Action's verification window, so the
    raw id does not reach a demo screen.
16. **New item, from R2-DS1a 3 (G3b owns it, +0.05 unit).** `frontend/src/shell/OperatorShellLayout.tsx:9`
    `DEMONSTRATION_BANNER` becomes **"Demonstration · example sites and records"**. Tests that pin the literal are
    updated. The register row R651 gets the note "OWN-G3b: 'prepared for this walkthrough' dropped (client-facing
    wording, owner rule)". No layout change.

### R2-G1 (Lane A, after G2 and G3a merge)

**Header rulings (crossing items):**
- **Timezones.** The tool reads each Site's timezone from the build, never assuming UTC+3: the `site` row, or the same
  source `delivered_days` uses. **EV-LAB-001 is `Etc/UTC`**, so its dates, `yesterday` and the Tuesday 08:00–16:00
  window are UTC. One §4.7 test: at 22:30Z on a Monday, EV's yesterday is Sunday's UTC date and Kisiwa's local date is
  already Tuesday.
- **Entry env.** As in R2-G3a 6, the child sets `ASSETOPS_OPERATIONAL_ENTRY=on` in `os.environ` before the first
  `lab_app` import, and runs with `serve_env=True`.
- **Late delivery (from G3a Q7).** A back-filled `FUEL_DELIVERY` is recorded at DB now, more than 30 min after its night
  closed, so its window carries `DELIVERY_RECORDED_LATE`. That limitation is information only and never changes the
  state (`rules.limitations`). It is honest: the record really was entered after the night. Step 7 checks the state
  only and allows any limitation set. The tool's plain line for a delivery night adds "(delivery entered after the
  night)".
- **New in G1, from R2-DS1a 1:** two `story_links` rows (spec in R2-DS1a 1), with a no-DB test in
  `test_own_g1_add_dates.py`.

1. **Accepted.** The default `--to` for KISIWA-001 alone is the latest night whose run end + 5 min ≤ DB now (yesterday
   after about 15:05 local, otherwise the day before). An explicit `--to` naming an unfinished Kisiwa night prints
   "KISIWA-001 {date}: the night is not over yet (it ends {15:00 local})", lists it under `skipped` with reason
   `NIGHT_NOT_OVER`, and is not a refusal. The other Sites keep yesterday. R1.5's runbook text gains: "Kisiwa's last
   night is added once it is over, after 15:05 local; a morning run adds it up to the night before."
2. **Accepted.**
   - The child `add-day` does steps 1–6 and exits with the entry `PUBLISHED`.
   - The parent runs `Demo.tick()` (which returns the report, R2-G2 Q9 c).
   - The new child verb `demo_combined_kisiwa.py verify-day <url> <work> <json>` does steps 7–8.
   - Resume covers a crash between the two.
   - The parent ticks only on a date where at least one Site added something.
3. **Changed (broadened).** The pre-authorised bound covers **every KIS-n row that fails only because of added-night
   content** (KIS-1, KIS-2, KIS-4, KIS-6, KIS-9, and any other KIS row the rehearsal shows), not just KIS-2 and KIS-6.
   Each such row's window, dispatch and record queries are bounded to the story calendar: nights in
   `story["kisiwa"]["runs"]` and `occurred_at` in `[run1_start, runs[-1].end)` from `story.json`. KIS-11 is already
   story-scoped. Each bounded row gets a no-DB case with one added night present. A COH row or a non-KIS failure still
   stops the work and goes to the Architect.
4. **Accepted.** After the copy to `var/g1_audit`, `tree` is replaced with a `git archive` of the G1 branch HEAD (G2 and
   G3a merged), with the same parts as `prepare`. `keys.json`, `story.json`, `days.json`, `kisiwa.json` and
   `operational-actions/` are kept. The clone name stays `assetops_k9_audit_g1` (inside the owner's authorised `_audit*`
   scratch names), and no `require_prepare_database` call is added. Expect a one-time `chain_snapshots` rebuild,
   because the tree's code version changes. The rehearsal is capped at 2× its 1.5 h estimate.
5. **Accepted.** Last story day per Site = the max of `weekday_offset(site, S, day_offset(e["day"]))` over
   `days.json["doc"]["sites"][site]`. The default `--from` = the day after the max offset in `days.json["days"]` for that
   Site (EV: the next Tuesday). Kisiwa: last story night = `story["kisiwa"]["runs"][-1]["night_date"]`; last night = the
   max of that and the last `DONE`/`PUBLISHED` `kisiwa-days.json` entry.
6. **Accepted, aligned with R2-G2 Q9.** The pass condition is the night's window (revision ≥ 1, `WITHIN_MARGIN`, no fuel
   Finding for that night). The tick's `fuel_night` code must be `OK` only when the tick visited KISIWA-001. If the
   window is absent, up to two more ticks run, 30 s apart, before `ADD_NIGHT_UNEXPECTED`.
7. **Accepted, with exact codes (changed).** A new tree child `demo_combined_kisiwa.py preflight <url> <work>`
   (`serve_env=True`) prints `{fuel_stage, entry_status, entry_code}`. The rules, in order:
   - The child is missing or exits non-zero → `BUILD_TOO_OLD`, "This build predates add-dates; prepare a fresh build
     from current main.".
   - `fuel_stage` is false → `FUEL_STAGE_MISSING` (§4.3).
   - 403 `WORK_WRITE_FORBIDDEN` → `ENTRY_DISABLED` (§4.3 message).
   - Anything else other than 422 `OPREC_ENTRY_INVALID` → `ENTRY_DISABLED`, with the message "This build's code has no
     working record entry (G3a); prepare a fresh build from current main.".
   - All of these are whole-command refusals, checked only when Kisiwa is selected (except `BUILD_TOO_OLD`, which is
     always checked).
8. **Accepted.** `DATE_TOO_OLD` (Kisiwa only, whole-command): the first planned night's 18:00 dip is more than 30 days −
   1 hour before DB now. Message: "Kisiwa {date} is too old to add records for; prepare a fresh build." It joins the
   §4.3 table.
9. **Changed in (a) and (b); (c) and (d) accepted.**
   - (a) A `--site` not in `story["sites"]` → **`SITE_NOT_IN_BUILD`**, "{site} is not in this build."; `--site all` = the
     build's Sites.
   - (b) `add-day --site KISIWA-001` with `--as` or `--assess-now` → **`OPTION_NOT_FOR_KISIWA`**, "--as and
     --assess-now do not apply to Kisiwa nights.".
   - (c) Accepted: `story["S"]`'s date as written, a new header constant, and the shipped log's fields.
   - (d) Accepted: one `add-dates` line in `serve`.

### R2-DS1a (folded into R1.4; Sonnet refresh after G1 merges)

1. **The two missing links are added to `story_links` (`tools/demo_combined.py:270`) by G1, not hand-built.** Inside the
   existing Kisiwa block:
   - `("KISIWA-001 Findings, story nights S-9d to S+1d", f"{base}/sites/KISIWA-001/findings?from={iso(S - timedelta(days=9))}&to={iso(S + timedelta(days=2))}")`
   - `("KISIWA-001 Service, story hour S-3d 09:00-10:00Z", f"{base}/sites/KISIWA-001/performance/service?from={iso(S - timedelta(days=3) + timedelta(hours=9))}&to={iso(S - timedelta(days=3) + timedelta(hours=10))}")`

   These are the windows of the K5 Findings capture and the K8 story-hour capture
   (`captures-kisiwa-service-feeders-story.json`), re-expressed relative to S. The no-DB test asserts both URLs for a
   fixed S. DS-1a takes them from `links` like every other link.
2. **`revision_id` is kept.** The href is `story_links`' verbatim URL. It pins the Finding revision the script
   describes, and it is not visible copy. The owner's vocabulary rule governs what the presentation says on screen and
   in text, not query strings. The forbidden-word scan excludes `href` values.
3. **The Sites-list wording is not acceptable in client pictures.**
   - (a) Drop `01-sites-list` from the script. The opening is now the Portfolio (R1.4, owner Q6), and no other crop
     shows the sidebar footer.
   - (b) **Banner:** the app-wide note becomes "Demonstration · example sites and records" (R2-G3b 16, a product
     change). It still says honestly that the data is example data, but drops the internal "prepared for this
     walkthrough".
   - (c) **"Simulator Lab"** stays as the workspace footer entry for this build. It is gated by
     `config/app-config.json` `simulator_lab.enabled`, which also gates the backend Lab execution. Switching it off is
     not on the demo path and is not proven safe for the demo tool. Crops exclude the footer. The presenter-only "Be
     ready for" box adds: "If asked about 'Simulator Lab': it is where this demonstration's example data is generated;
     on a real Site the data comes from your meters and gateway." Hiding the entry from a client build is an
     after-the-demo item; see the owner note.
4. **Kobo idle fuel.** E5 adds one capture: the Kobo board on day S, cost row (1440 and 390). DS-1f quotes the idle-fuel
   figure from that capture, with the screen's own qualifier. If the E5 board shows no idle-fuel line, **ST-3b is
   removed** from the script and from the story-map minutes. It is not filled by hand.
5. **Added nights (from the R2-G1 late-delivery header).** Presenter note: an added Kisiwa delivery night shows that
   the delivery was entered after the night. That is true, because records are entered later in the demo. Keep the
   live-dip beat on a dip (R1.4); a dip carries no late flag.

**Owner, for information (no decision needed for the build):** the banner wording change (R2-G3b 16) and the choice to
keep the "Simulator Lab" footer entry for this demo. If you would rather hide the Lab entry from the client build, say
so; it needs a separate check that the demo tool does not depend on the Lab gate.

---

## Revision 1 — owner answers 2026-11-08

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only on code, main `9aae0d003`. No Postgres or heavy
run. Owner, verbatim (`.agent/owner-answers-own-gaps-2026-11-08.md`): "i want all the fixes i asked for done now, with
the option for me to add dates so it can automatically udpate, see if this is clear to the architect. My reponse to the
open points 1. I'll add the data as i need it via the tool, nothing has to be done now, just ensuring the capcity for me
to do it 2.yes 3. "entered by site admin" 4.we are relaxing thte time, both are needed for the demo 5.illustrative is
fine 6.yes 7.Again , i don't know why this question is relevant, how does this relate to how a real site operates where
you can just show how site/portfolio is operating and add missing data through proper mechainsm when needed, i sense a
possible hardcoding of logic that should not be"

**This revision overrides the rest of this sheet where they differ.** §4 (G1) is replaced; §2.4, §3.1–§3.3 carry edits
marked "Rev 1"; §5 and §6 are superseded and kept only as history; §7 is the Q7 audit.

### R1.1 What the owner wants, in plain words (the Architect's understanding)

- **Build everything now.** G2 (diesel nights checked automatically), G3a and G3b (saving operational records from the
  screen, backend and form) and G1 (adding data days) are all built, reviewed and merged **before** the demo build. No
  item is cut and there is no cut order. The demo date gives way to this; 10 Nov is no longer fixed.
- **G1 is the owner's tool, not our daily chore.** The owner runs one command whenever he wants the demo Sites to be
  current: it adds the missing days, for any of the four Sites (Kobo, Cold, EV, Kisiwa), for any date or range of dates
  up to yesterday. The product then updates itself the way it would for a real Site: the background refresh checks the
  new days (G2 makes that include diesel nights) and every screen reads the new results. We schedule no roll-forward
  work; "nothing has to be done now" means the tool must exist and work, not that we pre-fill dates.
- **Q1 → one build, kept current by the owner with the tool.** The two-build plan (Part D.3) and the nightly add-day rows
  of old §5.2 are dropped.
- **Q2 yes:** the presenter may save a tank dip on screen during a client demo. It is a real, append-only write into the
  demo build, followed by the automatic re-check.
- **Q3:** records saved through the entry route are labelled **"Entered by site admin"** (replaces "Entered on screen").
  No person's name is recorded or claimed.
- **Q4:** the timing is relaxed; G1 and G3b are both required.
- **Q5:** the client script uses **illustrative pictures, taken once**, labelled as such. They are not retaken per build.
- **Q6:** the client script **opens on the Portfolio**.
- **Q7:** answered in §7. Short version: the question was only about the clock time of the 10-Nov meeting (to place
  the owner's walkthrough before it); it was not a product rule. The audit finds **no hard-coded story, date or Site
  logic in the product's monitoring path**. The dates mattered only because the demo data is generated once, at build
  time; with G1 the owner can bring the data up to yesterday at any time, which is how a real Site behaves.

### R1.2 What changed in this sheet

| Item | Change | Size (units, review included) |
|---|---|---|
| G1 | Rewritten (§4): owner-run `add-dates`, any Site, a date or a range up to yesterday, one command, prints what it added | **1.75** (was 1.25) |
| G2 | §2.4: the night buckets are derived from `rules.NIGHT_START/NIGHT_END` and `EDGE`, not typed as 17:30/12:30 (no second copy of the rule) | 2.25 (unchanged) |
| G3a | §3.2: attestation `job=site-admin-entry` (it serves both the screen and the G1 tool) | 1.0 (unchanged) |
| G3b | §3.3: By column reads "Entered by site admin" | 1.25 (unchanged) |
| DS-1a refresh | illustrative pictures, Portfolio opening, "checked automatically" wording, live dip beat, "Entered by site admin" | **0.5** (new step) |
| DS-1b | add short G1/G2/G3 sections and the owner's `add-dates` runbook | +0.25 on DS-1b |
| **Total build (G1–G3)** | | **6.25** (about 2 lane-days) |

### R1.3 New dated plan, starting now (Sun 8 Nov, evening)

Two lanes; **one heavy job at a time** (any Postgres test run, clone, capture, check-all, suite, prepare). Each slice
starts with an Opus pre-flight that sends **one batched question list**; the Architect folds the rulings into the
card. A fresh Opus reviewer per slice; High or Medium findings block; Sonnet fix rounds; merge `--no-ff`, then
check-all on main.

| When | Lane A | Lane B | Heavy job (in this order) |
|---|---|---|---|
| **Sun 8, evening** | G2 pre-flight (read-only) | G3a pre-flight (read-only) | K8c merge check-all, only if K8c is not merged yet |
| Sun 8, late | One batched question list (G2 + G3a) to the Architect; rulings folded into §2 / §3 | | — |
| **Mon 9** | G2-u1 (am), G2-u2 (pm) | G3a build (am), review (early pm), fix, merge; G3b build starts (pm) | ~12:30 G3a Postgres; ~15:00 G3a merge check-all; ~17:00 G2 Postgres (builder) |
| **Tue 10** | G2 review (am, reruns its Postgres file), fix, merge; then G1 pre-flight (batched questions) and G1 build, no-DB tests first | G3b build finish, fixture captures, review (pm), fix, merge | ~09:30 G2 review Postgres; ~11:30 G3b captures; ~13:30 G2 merge check-all; ~17:30 G3b merge check-all |
| **Wed 11** | G1 build finish (am); G1 rehearsal (§4.3); G1 review (pm), fix, merge | **DS-1a refresh** (Sonnet, 0.5 unit with its review); DS-1b drafting incl. G sections (trails; not on the demo path) | ~12:00–13:30 G1 rehearsal; ~17:30 G1 merge check-all |
| **Thu 12** | **E1** 08:00 code freeze, tag main. **E2** (Part F.3: clock check, template rebuild, T6, `-Tier fast`, slow pair plus the G2 Postgres file if slow-marked, vitest, check-all), about 08:00–10:45; reserved fix round to ~12:00. **E3** into `assetops_polish_client_test`, about 12:00–14:30 (cap 15:00); prepare day 12 Nov, so S = 10 Nov (date rule passes). **E4** with live ticks, plus: KIS-11, `fuel_night` OK for KISIWA-001 and `eligible: false` for Cold/EV, entry switched on. **First owner-tool run**: `add-dates --to yesterday`, then `finish check`. **E5** (adds `oprecords` 1440/390). **DS-1f** (figures checked against `check.json`; dated links from `links`). DS-1a merge, check-all ~17:30 | | E2, E3, E4, add-dates, E5, check-all — in sequence |
| **Fri 13, 09:00–10:30** | **Owner walkthrough** with DS-1a on the build, including one `add-dates` run and one on-screen tank dip | | the walkthrough's own catch-up |
| Fri 13, rest | High notes only: one fix round, then E3–E5 again (Fri prepare, S = 11 Nov, legal); other notes go to one batched round before 16 Nov or to after the demo | | E3–E5 if needed |
| Each demo day | **Owner**, at least 3 h before: `add-dates` (catch-up to yesterday), which ends with `finish check`; then E4-lite (serve with ticks, one completed tick, prewarm, the three K8c-r probes) | | one at a time |

- **The 10-Nov session moves.** All four items cannot be built, proven and walked through by 10 Nov.
- **Earliest demo-ready: Fri 13 Nov, about midday** (walkthrough with no High note). **With one High fix round: Sat 14
  Nov.** The 16–20 Nov week is safe either way. Recommendation: hold the first client session on **Mon 16 Nov**, or on
  Fri 13 afternoon if the owner wants it sooner and accepts no slack.
- **Capacity.** Lane A: G2 2.25 + G1 1.75 = 4.0 units over Mon–Wed (about 9 available). Lane B: G3a 1.0 + G3b 1.25 +
  DS-1a refresh 0.5 = 2.75. The binding constraint is the heavy-job queue; the times above do not overlap.
- **Dependencies.** G3b needs G3a; G1 needs G2 and G3a merged; E1 needs all four merged plus DS-1a refresh drafted.
  G2 and G3a share only `tools/demo_combined.py` (different functions) and merge one after the other.
- **If a slice needs a second fix round,** the slip goes into Thu morning before E1; past Thu noon, E1–E5 move one day
  and demo-ready becomes Sat 14 (no High) or Sun 15 (with one).

### R1.4 DS-1a client script refresh (branch `task/DS-1a-client-script`) — size 0.5 unit

Rev 2: also R2-DS1a 1–5 (story links from G1, `revision_id` kept, `01-sites-list` dropped, Kobo idle-fuel capture or
ST-3b removed, late-delivery presenter note).

Sonnet build, 0.3; fresh Opus light review (forbidden words, no cross-Site sums, claims the screen supports), 0.2.
Wed 11, before E1; finalised in DS-1f on Thu.
- **Pictures:** keep the existing crops as **illustrative** pictures, with one caption under the first: "Pictures are
  from a rehearsal build. Dates and some figures on your screen will differ." Add two: the Operational records form
  (from G3b's fixture captures) and a Kisiwa week with checked nights (from E5). The script quotes dates as story days
  ("the night five days before"); the presenter takes real dates from `links`.
- **Opening:** step 1 is the Portfolio. With G1 run up to yesterday, Kisiwa's week shows checked nights; any still
  unchecked days are named, and the presenter line says so plainly.
- **Wording now allowed:** "Each night's fuel is checked automatically once that night's tank readings have come in.
  In this demo the background refresh runs every two minutes." "Records typed here are entered by the site admin."
- **New beat (Q2):** on Operational records, save a tank dip for the newest added Kisiwa night at 06:00 with the
  value `links` prints; show it listed as Submitted, "Entered by site admin"; after the next refresh, open that night
  and show it re-checked. Presenter note: use only the night and value `links` prints; a dip on a story night would
  honestly re-check that night and can change the story.
- **Still forbidden:** theft words; any combined money total; "real time"; a production cadence claim; naming a person
  as the one who typed a record.

### R1.5 The owner's runbook (goes into DS-1b and the presenter checklist)

```
python tools/demo_combined.py --db assetops_polish_client_test --work var/polish_client serve      (if not running)
python tools/demo_combined.py --db assetops_polish_client_test --work var/polish_client add-dates   (catch up to yesterday)
python tools/demo_combined.py --db assetops_polish_client_test --work var/polish_client links       (today's dated links)
```

`add-dates` ends with `finish check` and prints one line per Site and date. About 20 min per missing date for all four
Sites (Kobo ~7, Cold ~4.5, Kisiwa ~3–8 incl. its 5-min quiet wait, EV ~3.5 on Tuesdays only, one tick ~2), plus ~5 min
for the check. `add-dates --dry-run` runs the read-only preflight: the build's DB and serve environment must be
reachable, and it writes only the child's log under `<work>/logs` (nothing is added). If more than about 7 dates are missing, a fresh prepare (~2.5 h) costs the same; if the demo is more than
about 25 days after S, prepare fresh (§7.3).

### R1.6 Remaining owner question

1. **When is the first client session now?** Earliest Fri 13 Nov afternoon (no slack); recommended Mon 16 Nov.

---

Background: `.agent/architect-answers-owner-ingest-captures-2026-11-08.md` (T1, T3) and
`.agent/architect-combined-pass-2026-11-08.md` Parts C–F. Fuel rulings carried from `.agent/build-sheet-DIESEL-1.md`:
the wording is "unexplained fuel", never theft; fuel money is never summed with any other amount.

| Item | What | Size (units, review included) | Lane |
|---|---|---|---|
| **G2** | Automatic diesel-night check: a `fuel_night` stage in the schedule tick | **2.25** (two build units) | A |
| **G3a** | Saving operational records: backend entry route and server identity | **1.0** | B |
| **G3b** | Saving operational records: the live entry form | **1.25** | B |
| **G1** | (Rev 1) Owner-run `add-dates` in the demo tool: any of the four Sites, a date or a range up to yesterday, fed through the product's real paths | **1.75** | A, after G2 and G3a |
| | **Total** | **6.25** (about 2 lane-days) | |

~~Ruling on timing (§5): none of G1–G3 goes into the 10-Nov build.~~ **Superseded by Revision 1 (R1.3):** all four are
built Mon 9 to Wed 11 Nov and go into one demo build on Thu 12 Nov. No migration is needed: the head stays
`0058_fuel_watermark_inputs`, and `0059` stays unused.

---

## 4. G1 — the owner's `add-dates` tool (demo tool) — Rev 1, replaces the earlier Kisiwa `add-day` card

### 4.1 What it is, in plain words

A real Site gets its data from its gateway, all day, without anyone doing anything. The demo Sites have a simulated
gateway that runs only when the demo tool tells it to. `add-dates` is that instruction: the owner names the Sites and
the dates (or just runs it with no options to catch everything up to yesterday). The tool generates each missing day's
readings, sends them through the real gateway path, posts Kisiwa's tank dips and deliveries through the real entry
route (G3a), and then lets the product's normal background refresh check them (G2 for diesel nights). Nothing in the
product knows the tool exists.

### 4.2 Command

```
python tools/demo_combined.py --db <db> --work <work> add-dates
    [--site all | KOBO-001,COLD-LAB-001,EV-LAB-001,KISIWA-001]     default: all
    [--from YYYY-MM-DD]     default per Site: the day after that Site's last day (story or added)
    [--to YYYY-MM-DD | yesterday]     default: yesterday
    [--kind <kind>]     only with one Site and one date; default per Site below
    [--dry-run]     print the plan and the refusals, write nothing
    [--no-check]     skip the closing finish check (not for demo days)
```

- Dates are **calendar dates in the Site's own timezone**. The tool converts each to the story offset (`date − S`)
  internally; the owner never types S-offsets. `yesterday` is the day before DB now (`clock_timestamp()`) in each
  Site's timezone.
- The existing single-day `add-day` stays (variety kinds, `--as`, `--assess-now`); `add-dates` calls the same planning
  and children per date. `add-day`'s `--site` choices gain `KISIWA-001`, and its "no Kisiwa day kinds" comment goes.

### 4.3 Whole-command refusals (checked first; nothing is written; `StoryDaysError` codes)

Rev 2 adds `BUILD_TOO_OLD`, `DATE_TOO_OLD`, `SITE_NOT_IN_BUILD`, `OPTION_NOT_FOR_KISIWA` and the second `ENTRY_DISABLED`
message (R2-G1 Q7–Q9); a Kisiwa night that is not over is skipped, not refused (R2-G1 Q1).

| Code | When | Message |
|---|---|---|
| `DATE_NOT_PAST` | `--to` is today or later in any selected Site's timezone | "Data can be added only up to yesterday ({date})." |
| `STORY_DAY` | `--from` or `--to` falls on or before a selected Site's last **story** day | "{site} {date} is part of the prepared story and cannot be changed." |
| `GAP_NOT_ALLOWED` | Kisiwa only: `--from` is later than the day after its last night (each night's tank level starts from the night before) | "Kisiwa nights must follow on from {last}; start at {last+1}." |
| `FUEL_STAGE_MISSING` | Kisiwa selected and `"fuel_night" not in STAGE_LIMIT_FIELDS` | "This build's code has no automatic diesel-night check (G2)." |
| `ENTRY_DISABLED` | Kisiwa selected and a probe `POST` with an invalid body answers 403 `WORK_WRITE_FORBIDDEN` | "Saving records is not switched on for this build (ASSETOPS_OPERATIONAL_ENTRY)." |
| `BUSY` | `<work>/.busy` held | the existing "another prepare/add-day holds …" line |
| `FROM_AFTER_TO` | `--from` > `--to` | "--from is after --to." |
| `KIND_NEEDS_ONE_DATE` | `--kind` with several Sites or dates | "--kind needs exactly one Site and one date." |

For Kobo, Cold and EV a later `--from` than the default is allowed: the skipped days stay empty and the screens show
them as missing, which is what a real Site with a gateway outage shows. The tool prints "left empty: {dates}".

### 4.4 Per-date behaviour (date-major: every selected Site advances one date, then one tick, then the next date)

| Site | Default kind | Per-date rule |
|---|---|---|
| KOBO-001 | `normal` | `sd.plan_add_runs` as today (including `FULL_DAY_AFTER_TRIAL`, which `normal` passes) |
| COLD-LAB-001 | `normal` | `sd.plan_add_runs` as today |
| EV-LAB-001 | `normal` | **Tuesdays only.** The simulated charger model admits one weekly TUESDAY 08:00–16:00 window (`host/ev_publication.py:331-336`, `tools/demo_story_days.py` `SITE_WEEKDAY`). Other dates print "EV-LAB-001 {date}: no charging session (the simulated charger runs on Tuesdays)" and are not refusals. |
| KISIWA-001 | `normal`, or `delivery` when the start tank level is below 250 L | the Kisiwa child in §4.5 |

- A date that already holds that Site's data from an earlier `add-dates` (`DUPLICATE_DAY` or `DAY_HAS_EVIDENCE`) is
  **skipped** with "already present". So running the command twice is safe.
- After each date: one `Demo.tick()` (the product's own scheduled tick; with G2 it runs `fuel_night`), then the next
  date.
- After the last date: `finish check` (unless `--no-check`), then a summary:

```
{"added": [{"site", "date", "kind", "records": [REC codes], "checked": "<tick result / Kisiwa window state>"}],
 "skipped": [{"site", "date", "reason"}], "left_empty": [...], "finish_check": "PASS" | "FAIL <rows>"}
```

  and one plain line per Site, e.g. "KISIWA-001: added 13 Nov (normal), 14 Nov (delivery, ticket KIS-DT-20261114);
  both nights checked: within margin." A failed `finish check` prints "This build no longer passes its checks; prepare a
  fresh one before a demo." (R1.5: a failed check retires the build).

### 4.5 The Kisiwa child (`tools/demo_combined_kisiwa.py add-day <url> <work> <json>`)

**Day kinds** (unchanged from the first card):

| Kind | Night d carries | Records |
|---|---|---|
| `normal` | one v7 run `[d 12:00Z, d+1 12:00Z)` from the previous run's end state, with the story's no-removal behaviour | two tank dips, at d 18:00 local and d+1 06:00 local |
| `delivery` | as `normal`, plus a 300 L delivery at d+1 10:00 local (effect-bearing, in the run's log) | the two dips plus one FUEL_DELIVERY, 300 L, ticket `KIS-DT-{yyyymmdd of d}` |

No kind creates unexplained fuel, an Action or a Finding (those are prepare-only, as for Kobo, Cold and EV).

**Per-night refusals** (stop the command at that date; earlier dates stay; codes as before): `UNKNOWN_KIND`,
`NOT_NEXT_NIGHT`, `DUPLICATE_DAY` (story nights), `DAY_NOT_IN_PAST` (run end > DB now − 5 min), `FUEL_LOW_USE_DELIVERY`
(explicit `--kind normal` below 250 L), `DELIVERY_TANK_FULL` (start + 300 > 950 L), `RUN_NOT_READY`,
`ADD_NIGHT_UNEXPECTED`.

**Steps** (the product's real paths; unchanged from the first card except where marked):
1. **Start state.** The last `DONE` or `PUBLISHED` entry of `<work>/kisiwa-days.json` `end_state`, else `kisiwa.json`
   `runs[-1].physics` (`soc`, `fuel` as exact fractions).
2. **Log.** Write `<work>/operational-actions/kisiwa-001-story-{S yyyymmdd}-add-{d yyyymmdd}-v1.yaml` (header shape of
   the shipped log, this day's actions only; ids `kis-add-{yyyymmdd}-dip-1800`, `kis-add-{yyyymmdd}-dip-0600`,
   `kis-add-{yyyymmdd}-delivery`). Read back through `YamlOperationalActionLog`; keep its sha.
3. **Run.** `story_registered(...)`, `reg.draft(nights.day_document(soc, fuel), start, end, "v7", {"log_id": ...,
   "log_version": 1})`; must be `READY` with a registered basis, else `RUN_NOT_READY`. `run_to_end` gives the trajectory,
   the end state and each dip's litres (offsets 180 and 900 min, `probe._round_litre`; delivery at 1140 min).
4. **Readings.** `rp._publish_and_accept(work / "kisiwa-replay" / f"add-{yyyymmdd}", run, f"epoch-add-{yyyymmdd}",
   db_now)`: the gateway path, Batch V2, received at DB now. **Rev 1:** then append the night to `kisiwa-days.json` with
   `status: "PUBLISHED"` and its `end_state`, so a crash after this point can resume.
5. **Records.** Post through the G3a entry route, `POST /api/sites/KISIWA-001/work/operational-entries`, via
   `finish.app_client(url, work)` with `ASSETOPS_OPERATIONAL_ENTRY=on`. Idempotency key `oprec-entry-` + the first 32 hex
   of `sha256("kisiwa-add|{S}|{d}|{action_id}")`; a re-post answers 200. They list as "Entered by site admin".
6. **Wait for the check.** Poll DB now every 30 s until `now >= night end + 30 min` and `now >= last reading decided_at
   + 5 min` (cap 8 min); the date-major tick (§4.4) then checks it. A running `serve` may check it first; idempotent.
7. **Verify.** The night's latest window: revision ≥ 1, state `WITHIN_MARGIN`, no fuel Finding for that night, the
   tick's `fuel_night` code `OK`. Otherwise stop with `ADD_NIGHT_UNEXPECTED` and the window line (append-only: nothing
   rolled back).
8. **Save.** Set the entry to `status: "DONE"` with `{night_date, kind, run_id, start, end, received_at, end_state, log:
   {id, sha256}, records: [{code, kind, quantity, taken_at_local}], window: {revision, state}}`.
9. **Resume (Rev 1).** On a re-run, a `PUBLISHED` entry for the next night resumes at step 5 (keys are deterministic;
   readings are not re-sent). Any other partial state stops with `PARTIAL_NIGHT` and goes to the Architect.

**`links`** prints each added night's dated Kisiwa link and the **live-dip line**: the newest added night, 06:00 local,
with the dip litres from step 3, for the on-screen beat (owner Q2 yes).

**Rev 2:** steps 6–8 are split between the child, the parent's tick and `verify-day` (R2-G1 Q2, Q6); the pre-authorised
bound below covers every KIS row (R2-G1 Q3).

**Guards for the story verdicts:** story nights cannot be touched (`STORY_DAY`, `DUPLICATE_DAY`); no kind can raise a
Finding; every command ends with `finish check` (KIS rows read story nights only; KIS-11 pins revision 1 on them). If
the rehearsal shows KIS-2 or KIS-6 failing **only** because of added-night dispatch content, the fix is pre-authorised:
bound that row's query to the story calendar's run range `[run1_start, runs[-1].end)` from `story.json`. Any other
failure stops and goes to the Architect.

### 4.6 Files

- `tools/demo_combined.py` (`add-dates` parser, range planner, date-major loop, summary; `add-day` choices and Kisiwa
  routing; `links`)
- `tools/demo_story_days.py` (only a pure `date → offset` helper and the per-Site `yesterday`, if not already there)
- `tools/demo_combined_kisiwa.py` (`add-day` child, plan, refusals, resume)
- `tools/demo_combined_finish.py` (only the pre-authorised bound, if needed)
- `backend/tests/test_own_g1_add_dates.py` (no DB)

### 4.7 Tests

**No DB:**
- range planning: defaults per Site; calendar date ↔ offset both ways; `yesterday` per Site timezone across a UTC
  midnight (Dar es Salaam at 22:00Z is the next local day); date-major order;
- every whole-command refusal at its edge (`--to` = yesterday passes, today refuses; `--from` = last story day refuses,
  +1 passes; Kisiwa gap of one day refuses);
- EV: a Tuesday is planned, a Wednesday prints the no-session line and is not a refusal;
- already-present dates are skipped, so a second identical run plans nothing;
- Kisiwa kind auto-choice at 249.999 L vs 250 L; `DELIVERY_TANK_FULL` at 650 L vs 651 L; run end = now − 5 min vs
  − 4 min 59 s;
- start state chains `DONE`/`PUBLISHED` entries over `kisiwa.json`; resume from `PUBLISHED` posts records only;
- action ids, instants, log text and sha stability, idempotency keys;
- `FUEL_STAGE_MISSING`; `--dry-run` writes nothing (no file, no call).

**Rehearsal** (one heavy job, about 1.5 h, Wed 11): clone the K9/K10 four-Site build,
`CREATE DATABASE assetops_k9_audit_g1 TEMPLATE assetops_k9_audit_r3u` (its serve stopped), copy
`AssetOpsV1-k10\var\demo3_r3u` to `var/g1_audit`, and run the product's own `evidence_migration run` and
`performance_migration run` on the clone (coordinator lesson 3). Then:
1. `add-dates --site KOBO-001,KISIWA-001,EV-LAB-001 --to <the clone's last Kisiwa night + 2>` (covers a normal night, the
   auto-delivery choice if the tank is low, and EV's Tuesday rule);
2. run the same command again: everything "already present";
3. `--to` today: `DATE_NOT_PAST`, nothing written;
4. `finish check` all green (KIS-11 included) and `chain_coherence.py` (EX-2 = 0);
5. drop the clone.

### 4.8 Size, risk, review

- **Size 1.75 units:** build 1.1 (Kisiwa child 0.6, the range command over four Sites 0.5), rehearsal 0.25 (machine),
  review and fix 0.4.
- **Risk: medium.** Physics continuity, a low tank, a crash mid-night, and a race with the serve loop. The tool guards
  each (start-state chain, auto-delivery, `PUBLISHED` resume, G2 idempotency).
- **Review:** a fresh Opus reviewer reads the code and the rehearsal output. High or Medium findings block.

---

## 5. Sequencing ruling — SUPERSEDED by Revision 1 (R1.3); kept as history

> Rev 1: the timing, the nightly add-day rows, the two-build option and the cut order below no longer apply. The
> plan is R1.3; one build is kept current by the owner with `add-dates` (§4).

### 5.1 Before 10 Nov: none

- **Monday is full.** The 10-Nov plan has no slack (Part D.2: "Yes, with no slack"). The code freeze E1 is Mon 08:00.
- **G2 is the main reason.** It changes the scheduler, so E2 and E3 would have to be re-run.
- **G3 and G1 do not fit either.** Even the smallest item (G3a, 1.0 unit, about 2.5 h, plus check-all) would have to be
  built and reviewed before 08:00 Monday. It would also change the served app inside the freeze.
- **Nothing changes in E2–E6 for 10 Nov.** DS-1a for 10 Nov must still **not** say or imply that diesel nights are
  checked automatically, and must not show anyone typing a record on screen.

### 5.2 After 10 Nov, before the 16–20 Nov demos (two lanes, one heavy job at a time)

| When | Lane A | Lane B | Heavy job (one at a time) |
|---|---|---|---|
| Tue 10, after the session | G2 pre-flight (Opus, read-only) | G3a pre-flight (Opus, read-only) | — |
| Tue 10, evening | One batched question list to the Architect; rulings folded into this sheet's cards | | — |
| Wed 11 | G2-u1 (am), G2-u2 (pm) | G3a build (am); review (early pm); fix; merge | 08:00 `finish check` on the 10-Nov build; ~12:30 G3a Postgres; ~15:30 G3a merge check-all; ~17:00 G2 Postgres |
| Thu 12 | G2 review (am, reruns Postgres); Sonnet fix; merge; then G1 pre-flight and build (unit tests only) | E6 non-High fix round (am, from the 10-Nov walkthrough, ≤ 1.5 units); G3b build (pm) | 08:00 finish check; ~10:00 G2 review Postgres; ~13:30 G2 merge check-all; ~17:30 G3b captures |
| Fri 13 | G1 build finish (am); G1 rehearsal (§4.3, ~13:30–14:30); review; merge | G3b review (am); fix; merge; DS-1a/b text revisions drafted (no serve) | 08:00 finish check; ~12:00 G3b merge check-all; ~13:30 G1 rehearsal; ~18:00 G1 merge check-all |
| Sat 14 | **E2-lite**: clock check (Part F.3 step 0); `-Tier fast`, then `-Tier slow` on the two schedule files plus `test_own_g2_fuel_night_tick_postgres.py` if slow-marked; vitest; check-all (about 1.5–2 h); reserved 0.5-unit fix round | | the suites, in sequence |
| Sun 15 | **E3** into `assetops_polish_client2_test` (S = 13 Nov; the date rule passes), about 2.0–2.4 h; then **E4** (live ticks; KIS-11; `fuel_night` OK in the tick report), then **E5** (adds `oprecords` 1440/390); DS-1a refresh (Sonnet) | | E3, E4, E5 in sequence |
| Sun 15, evening | add-day: Kobo S+1 (14 Nov) and **Kisiwa night 14 Nov**; tick; `finish check` | | yes |
| Mon 16–Fri 20 | Each evening: Kobo add-day; Kisiwa add-day (`normal`, or `delivery` when the tool says the tank is low); Cold/EV on their weekly day; tick; `finish check`. Each demo morning, ≥ 3 h before: E4-lite. | | one at a time |

- **Capacity.**
  - Lane A carries 3.5 units over Wed–Fri, against about 9 available.
  - Lane B carries about 3.75 units (G3a, E6 fixes, G3b).
  - The slack covers one extra fix round per item.
  - The real constraint is the heavy-job queue, so the times above are placed so that no two heavy jobs overlap.
- **Dependencies:**
  - G1 needs G2 merged (for `FUEL_STAGE_MISSING`) and G3a merged (records go through the entry route).
  - G3b needs G3a.
  - G2 and G3a are independent. Their only shared file is `tools/demo_combined.py`, in different functions, and they
    merge one after the other.
- **If the 10-Nov session moves to Wed 11, or the E6 fix round passes 1.5 units:** everything shifts one day. **G1 is
  then cut first** (it is built last, and Kisiwa stays judged on its story week, which is honest). G2 and G3 still land
  by Fri.

### 5.3 What changes in E2–E5 and in the scripts, for the 15-Nov build

- **E2-lite (Sat 14):**
  - the new no-DB tests run in the fast tier;
  - the G2 Postgres file runs in the fast tier, unless it is slow-marked;
  - the G3a Postgres file runs in the fast tier.
- **E3:** the command does not change. The prepare's ticks now run `fuel_night` (about +2–5 min). The in-prepare
  self-check now includes KIS-11.
- **E4:** check that each tick report has `fuel_night` `OK` for KISIWA-001 and `eligible: false` for COLD and EV. KIS-11
  passes. The serve env has `ASSETOPS_OPERATIONAL_ENTRY=on`. No live write is made in E4.
- **E5:** add `oprecords` at 1440 and 390 (the idle form). The after-submit state is captured only in G3b's fixture
  captures, never on the demo DB.
- **DS-1a (client) refresh on Sun 15.** It **may now say**: "Each night's fuel is checked automatically once that
  night's tank readings have come in; the background refresh in this demo runs every two minutes." It **may show**
  saving a tank dip from Operational records, only if the owner says yes (Q2), and then only on the newest added night,
  with the `links` live-dip value. Still forbidden:
  - theft words;
  - a combined money total;
  - "real time";
  - a production cadence claim;
  - saying who typed a record, because the record shows "Entered on screen".
- **DS-1b (technical):** a short section on `fuel_night` (the due rule, idempotency, DB time, the failure marker), the
  entry route and its server identity, and Kisiwa `add-day`.
- **The daily morning check** stays E4-lite: serve with ticks, one completed tick, `finish check`, prewarm. Plus the
  three K8c-r probes (Part E.3 step 4).

### 5.4 Rolling forward (from the colleague's recommendation, now with Kisiwa)

- One build, prepared Sun 15 (S = 13 Nov), rolled forward each evening.
- **G1 means Kisiwa rolls forward with the others.** "This week" views show checked diesel nights after S, instead of
  "0 of 7".
- A failed `finish check` retires the build. The fallback is a fresh E3, about 2.5 h, so the check runs at least 3 h
  before a demo.
- The 10-Nov build is kept as the fallback until the 15-Nov build passes E4.

---

## 6. Owner questions — ANSWERED 2026-11-08 (Revision 1, R1.1); kept as history

> Rev 1 answers: 1 → one build, owner adds dates with the tool; 2 → yes; 3 → "Entered by site admin"; 4 → no cuts,
> time relaxed; 5 → illustrative pictures taken once; 6 → Portfolio first; 7 → §7.

1. **16–20 Nov: one build rolled forward (recommended, and what G1 is for), or two builds (Part D.3)?** This was not
   answered yet. With two builds, G1 is still useful but not needed.
2. **May the presenter save a tank dip on screen during client demos?** It writes into the demo build. Recommended:
   yes, on the newest added Kisiwa night only, with the value `links` prints. That shows "record → automatic re-check"
   without changing any story result. If no, the entry form is shown but not used.
3. **For information (the Architect has decided; say if you disagree):** records saved from the screen are signed by a
   server-configured entry service, shown as "Entered on screen". Who typed them is not recorded until sign-in exists.
   - Option, +0.25 unit: add an unverified "Entered by" name field. That is a mock deviation, and it would be labelled
     "not verified".
4. **Cut order if time runs short:** G1 first (recommended), then G3b. G2 is never cut once DS-1a says "checked
   automatically": if G2 is not in the 15-Nov build, the script keeps today's wording.
5. **Still open from the earlier answer:** script pictures — exact pictures from each demo build, or labelled
   illustrative pictures taken once.

---

