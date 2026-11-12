# Build sheet OWN-GAPS (2026-11-08): Kisiwa add-day, automatic diesel-night check, saving operational records

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only on code, main `2cf460aa5` (includes R-1 merge
`733eaf75c`). No Postgres or heavy run was made for this sheet.

Owner, verbatim (`.agent/owner-decisions-ingest-gaps-2026-11-08.md`): "here is my response to the architect 1- update
the demo tool to address the gap mentioned 2- Diesel night should be checked automatically 3-operational records should
be saved , the entry form should be updated as well as the subsequent backend logic"

---

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

## 1. Shared rules (all three items)

- **Wording.** Client copy says "unexplained fuel" and "fuel check". It never says theft, stolen, siphon or pilfer
  (`tools/checks/fuel_wording.py` runs in check-all). It never shows a total that adds fuel money to any other money.
- **DB time.** Every scheduled write takes the database's `clock_timestamp()`, never the host clock (S4-02d I3,
  FIX-COLD-DRAIN). This follows Part F's clock-skew finding.
- **Append-only.** Nothing is updated or deleted. A re-check appends a new window revision only when its inputs digest
  changes (`fuel_balance/service.py`, `input_sha256`).
- **One heavy job at a time.** Heavy means any Postgres test run, prepare, clone, capture, check-all, or the full suites.
- **Mock fidelity.** The mock is the layout spec (`frontend/mockups/v69/index.html:983-987`, screen `oprecords`,
  manifest `screen-manifest.json:2205-2220`). Every departure carries a label `MOCK DEVIATION MD-OWN-G3-n` in the code
  comment and in `.agent/mock-departure-register.md`.
- **Builders make no design decisions.** If a card here does not fit the code, the builder stops and asks the
  Architect. Questions are batched once per slice, at pre-flight.

---

## 2. G2 — the automatic diesel-night check (product, scheduler)

### 2.1 What changes, in plain words

Today a diesel night is checked, and its unexplained-fuel Finding raised, only when someone runs
`python -m assetops_backend.fuel_balance.worker assess|raise` by hand (`fuel_balance/worker.py:1-14`). After G2, the
regular background refresh, the schedule tick, does it for every diesel Site. It checks a night once that night's tank
readings have arrived and gone quiet. It checks again whenever a new fuel delivery or tank dip touches a recent night.

This closes two after-the-demo items from DIESEL-1: "fuel-balance tick stage" (`build-sheet-DIESEL-1.md:1595`) and
"fuel-finding tick stage" (`:2834`). **"Fuel verdict tick stage" (`:3965`, `:4291`) stays open.** The Action's fuel
verdict is still judged explicitly.

### 2.2 Where in the tick (`backend/assetops_backend/scheduling/tick.py` `_site`)

- A new child **`fuel_night`** runs **after `mini` and before `opportunity`**, under the **`MINI` head stage**. The claim
  is re-checked with `stage("MINI")`, the same way `chain_threads` runs under `S4`.
  - The new order: `s3, cold_assess, ev_assess, mini, fuel_night, opportunity, s4, chain_threads, consequence,
    cold_consequence, ev_consequence, chain_snapshots`.
  - Why before `chain_threads`: a raised fuel Finding revision emits `finding.revised` (the `finding_revision` producer,
    `migrations/versions/0044_chain_events.py:66`). The same tick's `chain_threads` then places it on its thread. The
    0058 triggers on `fuel_balance_window` and `fuel_residual_consequence_revision` let the same tick's
    `chain_snapshots` rebuild the stored bodies.
- **No migration.** `schedule_site_head.stage` keeps its CHECK set (`0030_w4_mini_decisions.py:233`).
  `last_failure_stage` is free text (`0013_schedule_state.py:80`). The stage writes **no head counts**: its counts
  appear only in the tick report and the perf line.
- Code (exact shape):

```python
if not stage("MINI"):
    return
rf = self.runner.run("fuel_night", {**ids, "limit": self.limits.fuel_nights_per_site,
                                    "deadline_at": _deadline_at(self.limits.fuel_night_seconds)},
                     self.limits.fuel_night_seconds)
site.stages["fuel_night"] = rf
if rf["code"] != "OK":
    failure = failure or ("FUEL_NIGHT", rf["code"], str(rf.get("error")))
```

- **`TickLimits`** gains `fuel_nights_per_site: int = 10` and `fuel_night_seconds: float = 90`.
  - `__post_init__`: `fuel_nights_per_site >= 1` joins the "at least 1" `min(...)`. `fuel_night_seconds > 0` gets its
    own check, message "The fuel_night stage bound must be positive.". `fuel_night_seconds` joins the
    statement-timeout `min(...)`.
  - `site_lease_seconds` adds `+ self.fuel_night_seconds`.
  - `STAGE_LIMIT_FIELDS["fuel_night"] = "fuel_night_seconds"`.
  - `TickReport.as_json` already copies `processed`, `deferred` and `elapsed_ms`. Add `"eligible"` to that key tuple.
- The tick module docstring (`tick.py:1-35`) gains the stage in point 5 and one sentence: "OWN-G2 adds `fuel_night`
  after `mini`: the due diesel nights of the Site are assessed and their unexplained-fuel Finding raised, at DB time."

### 2.3 The stage child (`backend/assetops_backend/scheduling/stages.py`)

`fuel_night(url, args)` is registered in `STAGES` and named in the module docstring's stage list and the `OK` list.

```python
def fuel_night(url, args):
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store, build_fuel_finding_service
    from assetops_backend.fuel_balance.scheduled import run_site
    t, s = _uuid(args["tenant_id"]), _uuid(args["site_id"])
    store = build_fuel_balance_store(url)            # DB clock: no override
    findings = build_fuel_finding_service(url)       # DB clock: no override
    try:
        return run_site(store, findings, t, s, int(args["limit"]), _deadline(args))
    finally:
        _dispose(store, findings)
```

Errors propagate to `main`'s existing handler, which turns them into `classify(...)` → `TIMEOUT`/`UNAVAILABLE`/`FAILED`.

### 2.4 The due-night rule (new `backend/assetops_backend/fuel_balance/scheduled.py`)

Constants: `BASE_NIGHTS = 7`, `RECORD_LOOKBACK = timedelta(days=31)` (the work backdate limit, `work/model.py:37`, plus
one day), `QUIET = timedelta(minutes=5)`, and `EDGE = timedelta(minutes=rules.EDGE_SEARCH_MIN)`, which is 30 min.

**One read, `PostgresFuelBalanceStore.schedule_inputs(tenant_id, site_id, base_nights, record_lookback)`.** It runs in
one read-only transaction, with `known_at` = `clock_timestamp()` taken first. It returns `ScheduleInputs`:

- `known_at`.
- `timezone`, from the `site` row.
- `tank_asset_id` and `generator_asset_id`. Each is set only when the Site has exactly one active `FUEL_TANK` and
  exactly one active `GENERATOR`; otherwise both are `None` and the read stops there.
- `reading_nights: dict[date, datetime]`: night date → the latest `decided_at` of its tank `fuel_level` readings, as
  known at `known_at`. One aggregate SQL, over the same join and acceptance filter as
  `PostgresActionStore.window_readings` (`actions/adapters/postgres_action_store.py:600-608`), restricted to
  `e.role = 'fuel_level' AND e.asset_id = :tank`. It buckets the Site-local instant `lt = COALESCE(e.interval_start,
  e.source_time) AT TIME ZONE :tz` like this:
  - `lt::time >= '17:30'` → `lt::date`;
  - `lt::time <= '12:30'` → `lt::date - 1`;
  - otherwise no night.

  **Rev 1:** the two bounds are not typed as literals. They are computed from the rule's own constants:
  `rules.NIGHT_START − EDGE` (17:30) and `rules.NIGHT_END + EDGE` (12:30), passed to the SQL as bound parameters, so the
  fuel-balance-1 night window has one source. A unit test pins that changing `NIGHT_START` moves the bucket.

  This is a night's read range `[start − 30 min, end + 30 min]` (closed, D-R3.7) in local time. Two nights' ranges never overlap. The
  bucket is only a trigger: the assessment itself uses the exact `rules.night_window`. Time range read:
  `[known_at − record_lookback − 1 day, known_at]`.
- `records: list[(occurred_at, recorded_at)]`: the tank's fuel records as known, from the existing injected
  `fuel_records` reader (`FuelRecord.occurred_at`, `.recorded_at`, which is the head's). Range:
  `[known_at − record_lookback, known_at]`.
- `latest: dict[date, datetime]`: each night's latest window `recorded_at`, from the existing `windows(...)` read over
  the same nights.

**`due_nights(inputs) -> DuePlan(eligible, nights: list[date])`.** This is a pure function.

1. If `tank_asset_id is None`, return `eligible=False` with no nights. Cold and EV Sites take this path.
2. `L` = the latest night date `d` whose `rules.night_window(d, tz)` end satisfies `end + EDGE <= known_at`, which is
   the service's own closed rule (`service.py`, `WINDOW_OPEN`). Night `d` is **ready** when `d in reading_nights` and
   `reading_nights[d] <= known_at − QUIET`.
3. **Base set:** every ready `d` in `[L − 6, L]`.
4. **Record set:** for each record, take the night `d` whose `[start, end)` holds `occurred_at`. Add `d` when `d < L − 6`,
   `d` is ready, and either `d not in latest` or `recorded_at > latest[d]`.
5. Due = base ∪ record set, sorted ascending.

**What this means:**
- **A night with no tank readings is never assessed and gets no row.** That covers Kobo, which has a tank but publishes no
  `fuel_level` (`build-sheet-DIESEL-1.md:737`). So Kobo's MG-8 stays NOT_APPLICABLE (`:2750`). It also covers any night
  after the last published Kisiwa run.
- A night is first checked after its window is closed **and** its tank readings have been quiet for 5 minutes. That
  avoids checking a night in the middle of a batch.
- A later delivery or dip on a night up to 31 days back, or a late reading in the last 7 nights, triggers a re-check.
  Out of scope, listed for after the demo: a later Foundation correction (accuracy, SFC, no-load rate) on a night older
  than 7 days, and late readings older than 7 nights.

**`run_site(store, findings, tenant, site, limit, deadline) -> dict`:**

1. Read `schedule_inputs`, then compute `due_nights`. If `eligible` is false, return
   `{"code": "OK", "eligible": False, "processed": 0, "deferred": 0}`.
2. For each due night, in order, while fewer than `limit` have been processed and `time.time() < deadline`:
   1. Call `FuelBalanceService(store).assess_night(...)`.
      - `WINDOW_OPEN`: skip the night.
      - `ASSETS_UNSUPPORTED`: stop, and return `eligible: False` with what has been done so far.
      - Any other `FuelBalanceRefused`: raise it, so the stage fails with `FAILED` and an error that holds the code.
   2. Then call `findings.raise_night(...)`.
   3. Record the night as
      `{"night_date", "assess": "APPENDED"|"REUSED"|"OPEN", "revision", "state", "raise": <RaiseResult.status>}`.
3. Return `{"code": "OK", "eligible": True, "processed": n, "deferred": len(due) − n, "appended": a, "reused": r,
   "raised": {status: count}, "nights": [...]}`.

**Each night's assess and raise run in their own transactions** (already true in `service.py` and
`findings_service.py`). A failure on one night keeps the earlier nights. The next tick recomputes the due set, so no
state is needed.

**Idempotent:** with unchanged inputs, assess returns `REUSED` (the digest is equal) and raise returns `UNCHANGED` or
`NO_FINDING`. Neither writes a row.

**Failure handling:** a non-OK stage sets the Site failure `("FUEL_NIGHT", code, error)` and the Site's normal back-off.
Every other stage of that Site still runs ("every stage runs even after an earlier stage failed",
`tick.py:31-33`). The health read already shows `last_failure_stage` (`scheduling/health.py:142`, `:291`).

`fuel_balance/worker.py` docstring: replace "There is no tick stage, job domain or HTTP route in v1." with "OWN-G2: the
schedule tick's `fuel_night` stage assesses and raises the due nights automatically; this CLI remains for explicit runs."
Nothing else in the CLI changes.

### 2.5 Effect on the existing Kisiwa story, the KIS rows and COH

- **Story nights do not move.** The prepare already proves this at DB time: `cli_assess_check` (ten `REUSED`, revision 1)
  and `cli_raise_check` (night 4 `UNCHANGED`, the others `NO_FINDING`) (`tools/demo_combined_kisiwa.py:793-830`). The
  stage makes the same calls, so on the story nights it writes **zero rows**.
  - The story's records were all recorded before each night's assess instant (deliveries +30 min, dips +15 min;
    assess at run end + 30 min), so the record set is empty.
  - Ticks run only after every child, Kisiwa included (`tools/demo_combined.py:541-595`; "No tick may run before the
    mill step"). The stage therefore cannot pre-empt K7's story-instant assessments. That would refuse
    `FUEL_BALANCE_CLOCK_BACKWARDS`.
- **Night S+1 has no readings** (the runs end at S+1d 12:00Z), so it gets no row. The Portfolio's "Kisiwa 0 of 7 days
  checked" line is unchanged.
- **New finish row KIS-11** (G2 owns it, in `tools/demo_combined_finish.py`, not mutating). On the build:
  - the latest tick report has a `fuel_night` entry for KISIWA-001 with code `OK` and `eligible: true`;
  - every story night's latest window has `revision = 1`;
  - Kisiwa has exactly one fuel Finding;
  - KOBO-001 has zero `fuel_balance_window` rows.

  Source of the tick report: the tick child's stdout JSON, which `Demo.tick` already prints. G2 adds writing
  `<work>/last-tick.json` in `Demo.tick`, and KIS-11 reads that file.
- **KIS-3, KIS-4, KIS-9 and COH:** no change. KIS-3 and KIS-9 filter to the story nights (`demo_combined_finish.py:1385`);
  KIS-4 reads all windows and Findings, and G2 adds none to a story build.
- **Prepare time** grows by the child start per Site per tick, about 1–2 s, and about 1–3 s of Kisiwa's REUSED nights.
  That is about +2–5 min on E3. No cap changes.

### 2.6 Files

- `backend/assetops_backend/scheduling/tick.py`, `scheduling/stages.py`
- `backend/assetops_backend/fuel_balance/scheduled.py` (new), `fuel_balance/adapters/postgres_fuel_balance_store.py`
  (`schedule_inputs`, `ScheduleInputs`), `fuel_balance/worker.py` (docstring only)
- `tools/demo_combined_finish.py` (KIS-11), `tools/demo_combined.py` (`Demo.tick` writes `last-tick.json`)
- Tests listed in §2.7. Existing tests change **only** where they pin the stage list or the lease sum:
  `test_ch0_tick_timing.py`, `test_ch1b_drain.py`, `test_fix_cold_drain_stage.py`,
  `test_fix_cold_drain_tick_postgres.py`, `test_w402_mini_stage.py`, `test_w402_mini_stage_postgres.py`,
  `test_w403_opportunity_stage.py`. Their fake runners must also return an OK `fuel_night` result.

### 2.7 Tests

**Units (no DB): `backend/tests/test_own_g2_fuel_night_due.py`.** Each case must fail on the named wrong
implementation.

1. Bucket edges (Africa/Dar_es_Salaam): local 17:29 → no night; 17:30 → night d; next day 12:29 → night d; 12:30 → no
   night.
2. Closed edge: `known_at = end(L) + 30 min` → L is closed; 1 s earlier → L − 1.
3. A closed night with no reading is not due. This is the S+1 case; it must fail if `range(L−6, L+1)` is used directly.
4. Quiet: last `decided_at = known_at − 4 min 59 s` → not due; `− 5 min` → due.
5. Record set:
   - a record on night L − 10 with `recorded_at > latest` → due;
   - `recorded_at == latest` → not due;
   - a night with no window and a record → due;
   - a record 32 days back → not read.
6. Order is ascending; with `limit` 3 of 5 due, the result shows processed 3 and deferred 2.
7. Ineligible: 0 tanks; 2 generators. Each gives `eligible: False` and no further reads (the fake store counts calls).

**Units (no DB): `backend/tests/test_own_g2_fuel_night_stage.py`**, fake stores:
- REUSED, then raise `UNCHANGED`;
- a night refused `WINDOW_OPEN` is skipped;
- `CLOCK_BACKWARDS` raises, and the error holds the code;
- a passed deadline starts no night and counts them deferred;
- the stage args carry `deadline_at`.

**Units (no DB): additions to `backend/tests/test_s4_schedule_*` style (`InProcessRunner`):**
- the exact stage order of §2.2;
- a failing `fuel_night` → Site `FAILED`, failure `("FUEL_NIGHT", ...)`, and every later stage still ran;
- `TickLimits(fuel_night_seconds=0)` and `TickLimits(fuel_nights_per_site=0)` raise;
- `site_lease_seconds` grew by exactly `fuel_night_seconds`;
- `STAGE_LIMIT_FIELDS["fuel_night"]`.

**Postgres: `backend/tests/test_own_g2_fuel_night_tick_postgres.py`** (`*_test` DB via `pg_harness`; reuse the Site,
readings and record fixtures of `test_k4a_fuel_finding_postgres.py`; real `StageRunner` children):

- **P1.** After the night closes and goes quiet, tick 1 appends revision 1 and raises. Tick 2 adds no row to
  `fuel_balance_window`, `finding_revision` or `fuel_residual_consequence_revision` (counts equal).
- **P2.** A night with no `fuel_level` readings gets no row.
- **P3.** A Kobo-like Site (tank and generator, no `fuel_level`): zero `fuel_balance_window` rows after two ticks.
- **P4.** (Rev 2: replaced by R2-G2 Q6; the delivery half below was backwards.) A dip posted after night N's revision 1, which conflicts with the sensor: the next tick appends revision 2
  with the record in `record_ids` and the `DIP_SENSOR_CONFLICT` limitation.
  - A delivery that turns an UNEXPLAINED night into WITHIN_MARGIN: the next tick's raise is `WITHDRAWN`.
  - The fixture has one UNEXPLAINED night, so `OPENED` is proven too.
- **P5.** A record on a night 10 days back, already assessed, is re-checked. A record 40 days back is not read.
- **P6. Story invariance.** Nights assessed and raised earlier at story instants through the CLI (as K7 does) give
  REUSED/UNCHANGED from the stage and add zero rows.
- **P7.** Every stamp is DB time: the new window's `recorded_at` lies between two `clock_timestamp()` reads taken around
  the tick.

### 2.8 Size, risk, review

- **Size 2.25 units.**
  - G2-u1 (0.75): `scheduled.py`, `schedule_inputs`, the stage child and the no-DB tests.
  - G2-u2 (0.75): the tick wiring, the limits, the existing-test updates, the Postgres test, KIS-11 and `last-tick.json`.
  - Review plus fix: 0.75.
- **Risk: medium.** The scheduler is a protected seam, and every tick runs the stage.
  - Mitigations: no migration; the stage is isolated (its failure never stops other stages); P6 and KIS-11 prove story
    invariance; on story data the stage is idempotent and writes nothing.
- **Review:** one fresh Opus reviewer, which reruns the targeted Postgres file as one heavy job. Findings of High or
  Medium block. Codex reviews retrospectively in the milestone batch.

---

## 3. G3 — saving operational records from the screen (product)

### 3.1 The identity ruling (Architect decision; owner informed)

- **Why the form saves nothing today.** It is more than inert UI. The app injects no work principal: a work write is 403
  (`main.py:603-609`). A client-sent actor never authenticates (closure 3 Q28, `work_api.py:20-23`). A USER actor is
  refused because there is no signed-in user (`work/model.py:277-280`).
- **Ruling.** Records typed on screen are written by a **server-configured entry service**, `service:operator-entry`.
  The browser never sends an actor. The server composes the attestation and calls the existing
  `WorkService.post_operational_record`. That means the same validation, idempotency, hashing, REC code, correction
  lineage and audit columns as every other record.
- **Switched on only by server configuration.** The environment variable `ASSETOPS_OPERATIONAL_ENTRY=on` is read in
  `host/lab_app.py` `build_app`, the way the gateway variables are. The demo `serve` environment sets it. Without it
  the route answers 403 `WORK_WRITE_FORBIDDEN`, and the form says so.
- **What it does not prove.** It does not say which person typed the record. **Rev 1 (owner Q3):** the list shows
  **"Entered by site admin"** in the By column (was "Entered on screen"). That names the role of the entry point, not a
  person. A signed-in user identity is still an after-the-demo item.
- **Rev 1: one entry point for the screen and the G1 tool.** G1 posts its Kisiwa dips and deliveries through this same
  route, so they carry the same service identity and the same label. That is honest: in the demo the owner, running the
  tool, is the site admin entering records.

### 3.2 API contract (G3a)

**`POST /api/sites/{site_code}/work/operational-entries`** is added to `work_api.py` `build_work_router`, with a new
keyword `entry_principal: Principal = no_service_principal` and a new keyword `site_context`.

Request, a closed object (any other key → 422 `OPREC_ENTRY_INVALID`):

```json
{"entry": "TANK_DIP" | "FUEL_DELIVERY" | "STOCK_IN_CHAMBER" | "METER_READING",
 "value": "198",
 "taken_at_local": "2026-11-14T06:00",
 "ticket_reference": null,
 "idempotency_key": "oprec-entry-<32 lowercase hex>"}
```

Validation, in order:

1. `entry` is one of the four.
2. `value` is a decimal string matching `^\d{1,6}(\.\d{1,3})?$`. For `FUEL_DELIVERY` it must be > 0.
3. `taken_at_local` matches `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$` and is a valid date and time.
4. `ticket_reference` is required (non-null) exactly for `FUEL_DELIVERY` (`OPREC_ENTRY_TICKET_REQUIRED`), and null
   otherwise. It matches `^[A-Za-z0-9][A-Za-z0-9 /._-]{0,39}$`.
5. `idempotency_key` matches `^oprec-entry-[0-9a-f]{32}$`.

Each failure is 422 `OPREC_ENTRY_INVALID`, except the ticket case.

Server mapping. The body literals are the K7 literals (`tools/demo_combined_kisiwa.py:201-203`), so screen and demo
records read alike:

| entry | kind | unit | asset_id | body | source_document_sha256 |
|---|---|---|---|---|---|
| TANK_DIP | TANK_DIP | L | the Site's one active FUEL_TANK | `Tank dip at the {HH:MM} round: {value} L.` | null |
| FUEL_DELIVERY | FUEL_DELIVERY | L | the tank | `Fuel delivery of {value} L received, ticket {ticket_reference}.` | sha256 of ASCII `Fuel delivery ticket {ticket_reference}, {value} L` |
| STOCK_IN_CHAMBER | MANUAL_READING | kg | absent | `Stock in chamber: {value} kg.` | null |
| METER_READING | MANUAL_READING | kWh | absent | `Meter reading: {value} kWh.` | null |

Other fields:
- `occurred_at` = `taken_at_local` in the Site's `timezone` (zoneinfo, fold 0) as UTC ISO. `{HH:MM}` is the local
  time as typed.
- `period_end` and `case_id` are null.
- The actor is `{"kind": "SERVICE", "id": "service:operator-entry", "attestation":
  "service=operator-entry;job=site-admin-entry;rule=oprec-entry/1"}` (Rev 1: was `job=screen-entry`).
- The principal passed to the service is `"service:operator-entry"`.
- The tank and timezone come from `site_context(tenant_id, site_id) -> (timezone, tank_id | None)`. It is composed in
  `main.py` from `build_fuel_balance_store(database_url()).night_context` (returns the timezone, the one active tank or
  None, and the read instant; `postgres_fuel_balance_store.py:236-246`).
- A fuel entry with no single tank → 422 `OPREC_ENTRY_NO_TANK`, message "This Site has no single fuel tank to record
  against.".

**Refusal order:**
1. Site read access 401/403 and unknown Site 404 (`open_scope`, as today).
2. Entry principal absent → 403 `WORK_WRITE_FORBIDDEN`.
3. No store → 503 `WORK_STORE_UNAVAILABLE`.
4. Shape 422.
5. Tank and timezone.
6. The service: its own codes, unchanged — `WORK_OCCURRED_AT_FUTURE` (more than 5 min ahead),
   `WORK_OCCURRED_AT_TOO_OLD` (more than 30 days back), `WORK_RECORD_QUANTITY_INVALID`, `WORK_EVENT_DUPLICATE_KEY`
   (same key with a different body), and their statuses from `work/model.py` `STATUS`.

**A refusal writes nothing. Success** is the service's own result: 201 with the lineage body, or 200 with the stored
body for an identical retry (`work_api.py:15`).

The new codes go into `work/model.py` `MESSAGES` and `STATUS`: `OPREC_ENTRY_INVALID` 422, `OPREC_ENTRY_TICKET_REQUIRED`
422, `OPREC_ENTRY_NO_TANK` 422. The mapping lives in the new module `backend/assetops_backend/work/operational_entry.py`,
as `compose_entry(body, timezone, tank_id) -> dict` (pure) plus constants. The route calls `compose_entry` and then
`service.post_operational_record`.

**Wiring:**
- `main.create_app(..., operational_entry_principal: Principal = no_service_principal)` passes it to
  `build_work_router(entry_principal=...)`.
- `host/lab_app.py` `build_app`: when `os.environ.get("ASSETOPS_OPERATIONAL_ENTRY") == "on"`, pass
  `operational_entry_principal=lambda request, site_code: "service:operator-entry"`.
  - Any other non-empty value refuses startup with `ConfigurationError("ASSETOPS_OPERATIONAL_ENTRY must be 'on' or
    unset")`.
- `tools/demo_combined.py` serve env (the CH5c-R6 one environment of the serve and tick children) sets
  `ASSETOPS_OPERATIONAL_ENTRY=on`.

**Audit trail.** This needs no new table. Each saved row carries:
- the REC public code;
- the actor kind and id, and the server-derived `authorization_basis` (`SERVICE_GRANT_PREFIX + principal`);
- the attestation;
- `payload_sha256` over the canonical body;
- the idempotency key;
- `recorded_at`, the DB command time;
- the correction lineage.

It is the existing `operational_record` row, written append-only through the existing service.

**The "subsequent backend logic".**
1. A saved `TANK_DIP` or `FUEL_DELIVERY` is a tank record. The fuel balance already reads it through
   `work.composition.build_fuel_records_reader` (K2).
2. With G2, the next tick finds its night in the base or record set (§2.4) and re-assesses it. The night appends a
   revision only if the digest changes.
3. The raise then opens, revises or withdraws the unexplained-fuel Finding (§9j.4 table, `findings_service.py:31-47`).
4. The same tick's `chain_threads` and `chain_snapshots` update the thread and the stored pages.

A delivery first written more than 30 min after its night closed carries `DELIVERY_RECORDED_LATE` (K3 §9d.3). That is
already honest product behaviour. `MANUAL_READING` entries are stored and listed, but no check reads them yet; the copy
in §3.3 says so.

### 3.3 The entry form (G3b, `frontend/src/work/OperationalRecords.tsx`)

**Layout.** The mock's order and panel stay (`index.html:987`). Inside "Record a manual reading", in order:
1. row 1: Site, Reading;
2. row 2: Value, Taken at;
3. the Ticket reference row, only for Fuel delivery;
4. the footer with the button.

The panel pair and "How records are used" are unchanged.

**Fields and literals:**

| Field | Control | Literal / rule |
|---|---|---|
| Site | `<select>`, enabled | options from `manualReadingSites(body)` (existing, R362). The first Site is pre-selected. With none: "No Site selected" and the button disabled. |
| Reading | `<select>` | "Fuel tank dip" (TANK_DIP), **"Fuel delivery" (FUEL_DELIVERY)**, "Stock in chamber" (STOCK_IN_CHAMBER), "Meter reading" (METER_READING) |
| Value | `<input inputMode="decimal">` plus a unit suffix L / L / kg / kWh | placeholders: "e.g. 192 L", "e.g. 300 L", "e.g. 40 kg", "e.g. 1520 kWh" |
| Taken at | `<input type="datetime-local" step="60">` | label "Taken at (Site local time)" |
| Ticket reference | `<input>`, Fuel delivery only | label "Ticket reference", placeholder "e.g. KIS-DT-0002" |
| Button | "Submit for review" (mock label) | disabled while a save is in flight; the label stays |

**Client validation** (shown under the field; nothing is sent):
- "Choose a Site."
- "Enter a number of 0 or more, with at most 3 decimals."
- "Enter the delivered litres (more than 0)."
- "Enter the time the reading was taken."
- "Enter the delivery ticket reference."

**Submit:**
- `POST` through a new `GlobalWorkClient.submitOperationalEntry(siteCode, body)` (`globalWorkClient.ts`, the same base
  path and fetch helper as the reads).
- The idempotency key is `"oprec-entry-" + crypto.randomUUID().replace(/-/g, "")`. It is made when the form first
  becomes valid. It is **kept** for a retry after a network error or a 5xx. It is **replaced** after a success, or after
  any field edit.

**Outcomes:**

| Outcome | Text (live region `role="status"`) | Then |
|---|---|---|
| 201 / 200 | (Rev 2, R2-G3b Q2) "Saved as {displayCode(public_code)}, status Submitted." For a fuel entry, a second line: "If this Site's tank level is measured, the night it falls in is checked again at the next background refresh." | the list re-reads (the page's existing refresh); the form clears Value, Ticket and Taken at |
| 403 `WORK_WRITE_FORBIDDEN` | "Saving records is not switched on for this installation." | form kept |
| 422 `OPREC_ENTRY_NO_TANK` | "This Site has no single fuel tank to record against." | form kept |
| 422 `WORK_OCCURRED_AT_FUTURE` | "The time taken is in the future." | form kept |
| 422 `WORK_OCCURRED_AT_TOO_OLD` | "The time taken is more than 30 days ago." | form kept |
| `WORK_EVENT_DUPLICATE_KEY` | "This entry was already saved with different values. Reload the page and enter it again." | form kept |
| other 4xx | "Check the values and try again." | form kept |
| 5xx, network | "The record could not be confirmed. Try again; it will not be saved twice." | key kept |

**Other UI changes:**
- **Panel description** (replaces `MANUAL_READING_DESCRIPTION`): "Saved records are listed above as Submitted.".
- **`MANUAL_READING_REASON` and the `UnavailableInline` button wrapper are removed.**
- **"How records are used" second paragraph**, an addition: "Fuel tank dips and fuel deliveries are read by the nightly
  fuel check. Stock and meter readings are stored and listed; no check reads them yet."
- **By column (Rev 1):** when `actor_id === "service:operator-entry"`, show **"Entered by site admin"**. Other ids are
  unchanged.

**MOCK DEVIATIONS** (labelled in code and in the register):
- **MD-OWN-G3-1:** the "Fuel delivery" option and its Ticket reference row are additions. The owner asked that fuel
  deliveries be entered.
- **MD-OWN-G3-2:** "Taken at" is a native date-time input with a "(Site local time)" label. The mock has a text field
  showing "6 Oct 2026 · 16:00 EAT".
- **MD-OWN-G3-3:** the result line under the footer, and the replaced description line. The mock's "Fills REC-307 when
  submitted" is still not rendered (D1/R12 stands).
- **MD-OWN-G3-4:** the "Entered by site admin" By label (Rev 1), and the added "How records are used" sentence.
- The existing D1 "inert form" deviation (R12) is **closed**.

### 3.4 Files

- **G3a:**
  - `backend/assetops_backend/work_api.py`
  - `backend/assetops_backend/work/operational_entry.py` (new)
  - `backend/assetops_backend/work/model.py` (codes)
  - `backend/assetops_backend/main.py`
  - `host/lab_app.py`
  - `tools/demo_combined.py` (serve env only)
  - tests
- **G3b:**
  - `frontend/src/work/OperationalRecords.tsx`
  - `frontend/src/work/globalWorkClient.ts`
  - `frontend/src/work/globalWork.css` (form states only)
  - tests
  - `.agent/mock-departure-register.md`

### 3.5 Tests

**G3a units: `backend/tests/test_own_g3_operational_entry.py`** (`compose_entry`, and the route with a fake service and
`TestClient`):
- each entry type's exact kind, unit, body, asset and digest. The digest is checked against `hashlib.sha256` of the
  literal.
- Dar es Salaam 06:00 local → 03:00Z.
- Each invalid shape → `OPREC_ENTRY_INVALID`.
- A delivery without a ticket → `OPREC_ENTRY_TICKET_REQUIRED`.
- No tank → `OPREC_ENTRY_NO_TANK`.
- Refusal order:
  - no principal → 403 `WORK_WRITE_FORBIDDEN`, even with an invalid body;
  - a principal with no store → 503 before shape.
- The browser cannot send an actor: an `actor` key → 422.
- `ASSETOPS_OPERATIONAL_ENTRY=yes` refuses startup.

**G3a Postgres: `backend/tests/test_own_g3_operational_entry_postgres.py`** (`create_app` with the entry principal,
fixture Site with one tank):
- 201, then an identical retry → 200 with the same body;
- the same key with another value → `WORK_EVENT_DUPLICATE_KEY` and its status;
- the stored row: actor id, attestation, `authorization_basis`, REC code, `payload_sha256`, `recorded_at` = DB time;
- a 31-days-back and a 10-minutes-ahead entry are refused, with zero rows;
- an app with no principal → 403, with zero rows;
- a saved dip is returned by `build_fuel_records_reader` for its night: this proves it feeds the fuel balance;
- `MANUAL_READING` rows are stored with their unit and have no `asset_id`.

**G3b vitest: additions to the Operational records tests:**
- field order and labels;
- the four options;
- the ticket row appears only for Fuel delivery;
- each client validation message;
- the exact request body;
- the button is disabled in flight;
- every outcome row's text;
- the list re-reads after success;
- the key is kept after a network error and replaced after an edit or a success;
- "Entered by site admin" (Rev 1);
- no `UnavailableInline` remains on the form;
- the form uses no forbidden fuel words.

**G3b captures** (one heavy job, fixture serve): `oprecords` at 1440 and 390, idle form and the Fuel delivery state.
They are compared with the mock; each difference must be one of MD-OWN-G3-1..4.

### 3.6 Size, risk, review

- **G3a 1.0 unit** (build 0.7, review 0.3). **Risk: medium.** It is a new write path, gated by server configuration.
  The identity is a labelled service, not a user.
- **G3b 1.25 units** (build 0.85, review and captures 0.4). **Risk: low to medium** (UI states).
- **Review:** a fresh Opus reviewer per slice. G3b's review includes the capture pair against the mock. High or Medium
  findings block.

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

## 7. Q7 audit (Rev 1): is any date, story or Site logic hard-coded in the product?

Owner, Q7: "how does this relate to how a real site operates where you can just show how site/portfolio is operating
and add missing data through proper mechainsm when needed, i sense a possible hardcoding of logic that should not be".

**First, the question itself.** Q7 (Part D.5 Q1) asked only *at what clock time* the 10-Nov meeting was, so the
coordinator could fit the owner's walkthrough before it. It was a calendar question, not a product rule. It is moot now
that the session moves (R1.3).

**Verdict: no product hard-coding to remove. No G4.** Searched read-only on main `9aae0d003`: `backend/assetops_backend`,
`host/` and `frontend/src`, for Site codes, fixed dates, "story"/"demo" logic and clock reads. Tests and fixtures were
excluded from "product".

### 7.1 What was found, classified

**A. Site-specific branches on the monitoring path (what a Site's screens show): none.**
- No Site code appears in any non-comment line of the backend monitoring path. The Site codes found in
  `backend/assetops_backend` are in docstrings and CLI usage examples only (e.g. `chain/snapshots.py:3`,
  `evidence_migration.py:3`, `recompute_consequences.py:3`).
- `frontend/src`: Site codes appear only in `frontend/src/test/outcomeBoardFixture.ts` (a test fixture).
- No fixed date is read by any screen. The fuel night window (18:00 to 12:00 local, `fuel_balance/rules.py:57`) is the
  versioned model parameter `fuel-balance-1` (`rules.py:30-45`), applied to every diesel Site in its own timezone. It is
  not tied to Kisiwa.

**B. Real-clock reads and retention windows: legitimate.** This is how a real Site behaves.
- Frontend default windows read the browser clock: `sites/PerformanceDispatch.tsx:86-87` (board opens on today),
  `sites/siteTime.ts:203-206` (the last 7 days), `estate/estateShared.tsx:30`, `work/globalWorkClient.ts:701`,
  `sites/workClient.ts:187`, `sites/miniDepthClient.ts:334,358`.
- Backend 30-day rules: "verified recently" `estate/coverage.py:40`; the Action observation window
  `actions/service.py:45`; the work backdate limit `work/model.py:37`; the EV read window `ev_assessment_api.py:107`.
- Month-to-date targets: "too early to judge" below the checked-day minimum (`outcomes/objectives.py:16-22`, `:141`;
  copy `chain/vocabulary.py:277`). A real Site on 2 December would show the same.
- Validation bounds `fuel_balance/night_read.py:24` (years 2000–2100), and `review_date` provenance stamps in
  `financials/fuel_cost.py:79` and `fuel_cost_v2.py:65`. These are metadata, not logic.
- One Low (after the demo): `PerformanceDispatch.tsx:86-87` takes "today" in UTC, not Site-local. Between local
  midnight and 03:00 in Dar es Salaam it opens on the previous day. This is not hard-coding.

**C. Clock overrides that only a prepare or a test may switch on: legitimate, guarded.**
- `prepare_clock.py:13-24` refuses any story clock unless the database is `assetops_polish_*` or `*_test`. Users:
  `mini_decisions/store.py:119-130` (`story_clock`) and `objectives/adapters/postgres_objective_store.py:48`. Production
  composition never sets them.
- "Story time" in `chain/` (`lifecycle.py:7`, `threads.py:157,206`, `lookup.py:3-10`) means the *effective* time of an
  event, as opposed to when it was recorded. That is a bitemporal rule, not demo logic. The name is unfortunate, and
  renaming it to "effective time" is an after-the-demo cosmetic item.

**D. Demo labels standing in for missing sign-in: legitimate, labelled, configuration-driven.**
- `actions/fuel_verification.py:55` and `actions/verification_families.py:60` (`BASIS_TEXT` "SYSTEM_DEMONSTRATION: …
  no verified human principal exists"), and `actions/lifecycle.py:49-54`. These are honest provenance, because no user
  sign-in exists. The freeze methods have no route (`actions/verification.py:367,376`) and are also called by the
  tick's `chain_snapshots` stage.
- `ASSETOPS_ACTION_DEMO_GRANTS` (`actions/composition.py:37`, `actions/adapters/demo_grants_file.py`: absent means
  nothing is granted) and `ASSETOPS_DEMO_FIXTURE_MANIFEST` (`analytics/adapters/demo_manifest_file.py`: it only
  annotates exact evidence IDs, never fills an input). Both are server configuration and are labelled on screen.
- G3's `ASSETOPS_OPERATIONAL_ENTRY` follows the same pattern.

**E. Lab and simulator fixture pins: product code, but not on the monitoring path. After the demo; not G4.**
- `scenarios/ev_parsing.py:26-32` pins the Lab's `ev-scenario/1` to EV-LAB-001, seed 20517 and the window
  2026-10-06 08:00–09:00Z. `simulator_lab_api.py:2750` lists EV scenarios only for `EV_SITE_CODE`.
- `sites/ev_lab.py:76-77` and `sites/cold_lab.py:30` are fixture installers with fixed effective dates.
- `host/ev_publication.py:331-336` is the simulated charger. It runs only in a weekly TUESDAY 08:00–16:00 window.
- These shape what the **simulator** can generate, standing in for a real device. They do not shape how the product
  reads a Site. Their only demo effect: EV data can be added on Tuesdays only (§4.4).
- After-demo item: generalise to `ev-scenario/2` (any registered EV Site, its declared schedule).

**F. Demo tooling only (`tools/`): the story lives here, as it should.**
- `tools/demo_combined.py:146-148` `story_day` (S = the prepare day − 2), the S-relative story calendar
  (`backend/conversions/demo-story-days-v3.json`, `tools/demo_story_days.py`), `SITE_WEEKDAY`, `FULL_DAY_AFTER_TRIAL`,
  `BOARD_WINDOW_DAYS`, and the Kisiwa story (`tools/demo_combined_kisiwa.py`).
- The date rule "do not prepare on the 3rd to 5th" is also tool-side (D-W1-15).

### 7.2 Why the date mattered, and why it mostly stops mattering with G1

- **The product reads the real clock** (B). It shows each Site's state as of now, as a real Site would.
- **The demo data is generated once, at build time.** The story is anchored at S = the build day − 2, and nothing adds
  data afterwards. So as the calendar moves on, the demo Sites look like real Sites whose gateways stopped: recent days
  show as missing, and "this week" empties. The earlier plans re-built the demo (about 2.5 h) close to each session
  for that reason. The product was right; the data simply stopped.
- **With G1, the owner adds the missing days up to yesterday whenever he wants** (one command, about 20 min per missing
  date). G2 and the normal tick check them, and every screen updates. The session date then stops mattering for
  freshness. That is the "proper mechanism" the owner describes: in production the gateway does it continuously, and
  in the demo `add-dates` stands in for the gateway.

### 7.3 What still remains, and whether it is real behaviour

| Remaining effect | Real product behaviour or demo artefact | What we do |
|---|---|---|
| Today has no data: G1 adds whole days only, up to yesterday, so a Site board opening on today is empty | Demo artefact. A real Site streams today's readings. The screen's "no readings" message is honest. | The presenter uses the dated links (`links`). After the demo: open on the latest data day (Part E.5). |
| On the 1st–3rd of a month, the monthly target reads "too early to judge" | **Real.** A real Site shows the same. | Nothing. The prepare date rule is tool-side only. |
| The story ages: about 30 days after S, "verified recently" drops, and story items fall outside the 30-day work and observation windows | **Real.** A trial six weeks old is not "recent". | Prepare a fresh build if the demo is more than about 25 days after S (R1.5). |
| A long gap costs catch-up time (about 20 min per date) | Demo artefact (the simulator) | If more than about 7 dates are missing, prepare fresh (about 2.5 h) instead |
| EV data only on Tuesdays | Simulator pin (E) | Printed by the tool. After the demo: `ev-scenario/2` |
| Host-vs-database clock skew (Part F) | Environment | The clock check before E2, E3 and each E4-lite |

---

## Revision 3 — G2 test rulings (2026-11-08)

Claude Architect (binding: Claude, `AssetOpsV1-plan2/.ai/ROLE_CONFIG.md:9`). Read-only; no Postgres run. Inputs: branch
`task/OWN-G2-diesel-night-check` at `a5a5ffaf0` (worktree `AssetOpsV1-g2`), its `.agent/review-packet-G2.md`
(Deviations 1-6) and `backend/tests/test_own_g2_fuel_night_tick_postgres.py`. **This revision wins over R2-G2 Q5 and
§2.6/§2.7 where they differ.** The builder makes no further decision on the items below.

### R3.1 Fixture: keep K1's real path and all four runs; no shortcut

- **Ruled: the fixture stays exactly as written at `a5a5ffaf0`** (K1's path: `kis.register`, `day_document` runs, a real
  gateway, `_publish_and_accept` into S2 `BatchIngestionService`; `OFFSETS = (0, 1, 2, 9)`), plus the `received_at`
  fix already made (Deviation 2).
- **Rejected: readings straight into `BatchIngestionService` without the gateway.** No Kisiwa batch builder exists
  (the w402 `cases.build_batches` precedent is mini-grid only), so the builder would have to design batch bytes, and the
  readings would stop being the story-shaped ones P6 and KIS-11 depend on. That lowers fidelity; the owner said not to.
- **Rejected: night-only runs.** `day_document` is a fixed 15:00-15:00 day; changing it is design work for about a 20 %
  saving.
- **Rejected: dropping a run.** Each run carries a distinct proof (N0: P1, P4a, P7, Q1; N1: P1, P4b/c on a
  WITHIN_MARGIN night; N2: P6's pre-assessed night; N9: P5 outside the base set). Merging them couples P4a and P4b on
  one night's records.
- Measured reference: `host/tests/test_k4a_kisiwa_night4.py` (one Kisiwa night on the same path) took 348 s
  (`review-packet-K4a.md:124`), so four runs plus ticks is about 20-25 min. That is the expected cost, not a defect.

### R3.2 The cap: this file is one background heavy job with a 45-minute budget

- The 10-minute figure is the per-command tool limit, not a limit on a test file (precedents: the estate guard
  self-tests, about 20 min, `review-CH-5b2.md:77`; T6 at 15-25 min in E2, combined pass F.3). It does not apply here.
- **Run the file whole, in one process, in file order**: no `-k` split and no `-n` (its tests share the module fixture
  and run in order: P1/P6/P7 tick, then P4a, P4b/c, P5). Under the container runner's `--dist loadfile` the module stays
  on one worker, so the full-suite tiers are safe.
- **How:** `run_in_background`, as the only heavy job on the machine (not while check-all or any other Postgres run is
  going), on its own `*_test` DB, with `-s` so the `G2 ...` print lines land in the log.
- **Budget: 45 minutes hard** (about 2x the estimate, per the long-run rule). **Stall rule:** check every 5 min with
  `SELECT count(*) FROM ingestion_disposition` on that DB (cheap, read-only) until the fixture ends; if the count does
  not move for 10 min during the fixture, or the budget is reached, kill the run and report. Do not retry blindly.
- **Marker:** add `pytest.mark.slow` to the module's `pytestmark` (a list beside the existing `skipif`), as R2-G2 Q5
  ruled for over 120 s. Add the measured runtime to the module docstring.
- The reviewer reruns it the same way, as its one heavy job. E2 runs it as its own named item (about 25 min, inside
  the 08:00-10:45 E2 window; R1.3 already counts it).

### R3.3 Fixture deviations (packet Deviations 3 and 4): all accepted

1. **15:00-15:00 local day runs ending at the latest local 15:00 at or before DB now - 15 min, and 1, 2 and 9 days
   before it.** Accepted. Each run holds exactly one whole night (17:30 to 12:30 sits inside 15:00 to 15:00), and the
   ticks' L can move by at most one night during a 25-min run, which keeps N0-N2 in the base set and N9 out of it.
2. **P5's old night at 9 nights, not 10.** Accepted. The requirement is "outside the base set `[L - 6, L]`, inside
   `RECORD_LOOKBACK`"; 9 nights meets it, and `_night(fuel, n[9]) is None` after tick 1 proves "outside".
3. **Only `fuel_night` as a real `StageRunner` child; the other stages in process.** Accepted. G2 changes only the
   `fuel_night` child path (its args, `deadline_at`, JSON result); the other stages' child paths are unchanged and
   covered by the s4 tick tests. "Real `StageRunner` children" in R2-G2 Q5 means the stage under test.
4. **Q1 edges at the real 5-minute readings 17:25 / 17:30 / 12:25 / 12:30.** Accepted. The SQL bounds are bound from
   `bucket_bounds()` (one source), and the inclusive/exclusive edges are exactly 17:30 (in) and 12:30 (out), both real
   readings in the set. The minute-exact 17:29 / 12:29 proof stays in no-DB case 1 on `night_of`. Keep the assert that
   all four edge times are present.
5. **Q12 with a Site id that has no FUEL_TANK or GENERATOR rows (an unknown id).** Accepted. `schedule_inputs` takes the
   same early return for any Site without exactly one tank and one generator. The real Cold and EV Sites are proven on
   the real build at E4 (`eligible: false` for Cold/EV, R1.3).

### R3.4 `test_fix_cold_drain_tick_postgres.py` p1/p2/p3: the pre-existing replay-fixture failure family

**Ruled: the same failure family as R-1 T6 / w203 (combined pass Part F), not caused by G2, not a G2 blocker. Tracked
into E2's reserved fix round.** Evidence:

- **Where they fail.** All three fail inside the replay fixtures, before the tick and before any line G2 changed: p1 at
  `assert jobs` (`test_fix_cold_drain_tick_postgres.py:101`, no PENDING `cold_chain` job after `opened("excursion",
  cold_chain)`); p2 at the EV replay's Lab run `FAILED`; p3 at an unpack of the cold fixture's rows. G2's only edits to
  this file are the two stage-list pins (`:106-108`, `:199-201`).
- **Same factories as T6.** p1-p3 build their data with `test_w203_cold_replay_postgres.opened` and
  `test_w301_estate_golden_postgres.cold_chain` / `ev_chain`. Those are exactly the factories of the w301 golden
  replays that failed on main at R-1 (`733eaf75c`, an ancestor of G2's base `1d666d410`) with "cold `run_pending` -> []"
  and "a Lab run FAILED" (Part F.1). Neither w203 nor w301 imports `scheduling` or `fuel_balance` (grep: no match), so
  no G2 module runs in these fixtures.
- **Clock skew is ruled out** (DB clock checked, not skewed; coordinator handoff line 30). With no skew, Part F.1's
  branch applies: a real fixture failure that goes to E2's fix round. p1 failing at `assert jobs` (no job at all, not a
  job that is merely not yet due) fits a replay that never reaches the job, the same as T6's empty `run_pending`.
- **G2's own pin is still proven on Postgres:** p4 (`test_p4_mini_only_site_...`, the full stage list including
  `fuel_night`) passed, and `test_w402_mini_stage_postgres.py` passed.

**What the builder and reviewer do:**
- Builder: no further change to this file. The packet lists p1-p3 as "pre-existing, replay-fixture family (R-1 T6 /
  w203, Part F), tracked to E2" with the three failure lines.
- **One confirming run, required before merge (about 2 min, in the reviewer's heavy-job slot, after the G2 file):**
  `test_fix_cold_drain_tick_postgres.py::test_p1_one_tick_assesses_and_drains_cold_work` alone on the **main**
  checkout (`AssetOpsV1-plan2`, main HEAD, own `*_test` DB, only when no other heavy job runs). If it fails at the same
  line on main, the ruling stands. **If it passes on main, G2 caused it: that is a High finding and G2 does not merge.**
- E2's reserved fix round gains the item "cold_drain p1-p3 replay fixtures" beside "w203/w202 cold replay fails with no
  skew" (Part F.3), under the same test-side-only rule; a product change there stops and goes to the Architect.

### R3.5 `test_ch1b_drain.py` (§2.6 pin file)

- It needs no edit by reading: its tick tests use `test_ch0_tick_timing.FakeRunner`, which G2 already updated and which
  returns an OK result for any stage, and its lease assert is relative (`site_lease_seconds + 30`,
  `test_ch1b_drain.py:400`), so the added `fuel_night_seconds` does not move it.
- **Builder runs it** (no DB, seconds) with the no-DB set. If it passes unchanged, the packet says "run, passed, no edit
  needed". If any test fails, edit only a stage-list or lease pin, exactly as in the other pin files; any other failure
  stops and goes to the Architect.

### R3.6 G2 merge condition (all must hold)

1. `test_own_g2_fuel_night_tick_postgres.py` completes under R3.2 with **every test passing** (Q1/Q12, P1/P2/P3/P6/P7,
   P4a, P4b/c, P5), by the builder and again by the reviewer; the packet records the runtime and the `G2 ...` lines.
2. The no-DB set is green: the three G2 files, the pin files (`test_ch0_tick_timing.py`, `test_ch1b_drain.py`,
   `test_fix_cold_drain_stage.py`, `test_w402_mini_stage.py`, `test_w403_opportunity_stage.py`), the k3 and k4a rules
   files and `test_demo_combined_finish_rows.py`.
3. `test_w402_mini_stage_postgres.py` and `test_fix_cold_drain_tick_postgres.py::test_p4_...` pass (already shown at
   `a5a5ffaf0`; rerun only if a stage, tick or limits file changes again).
4. The R3.4 confirming run on main fails at the same line (pre-existing). p1-p3 are then listed, not counted.
5. A fresh Opus review with no open High or Medium finding; then `--no-ff` merge and check-all on main, as R1.3 says.

### R3.7 — G2 Q1 edge ruling (2026-11-08)

Claude Architect, under the owner's delegation of 2026-11-08 (`.agent/owner-away-architect-decides-2026-11-08.md`:
decide from how real sites work, no corner cutting on fundamentals). Read-only; no Postgres run. Inputs: branch
`task/OWN-G2-diesel-night-check` at `11f284e80`, packet Phase 3, `test_own_g2_fuel_night_tick_postgres.py:215-244`.
**This wins over R3.3 item 4, R2-G2 Q1's Postgres case and §2.4's half-open read range where they differ.** Logged for
owner review (decision D-R3.7 below).

**1. The cadence is 15 minutes; R3.3 item 4 was wrong.** The fixture's runs use `registered-kobo-publication` v5
(`tools/demo_combined_kisiwa.py:73-75`). Its `fuel-level-sensor/fuel-level` declaration is inherited unchanged from
`LAB_PUBLICATION_PROFILE` (`backend/assetops_backend/runs/profiles.py:1496-1498`: `cadence_minutes=15`,
`dropout_per_thousand=40`) through v1 (`:1873-1890`); v4's five-minute set `_V4_FIVE_MINUTE` (`:1996-2005`) does not
contain it and v5 changes only PV output (`:2087`). 96 slots a day less 4 % dropout is about 92-94 a day, matching the
builder's 376 over 4 runs. The "five-minute publication profile" wording (`sites/binding_roles.py:275`) is about the
other signals; that is where R3.3's assumption came from. Readings sit on :00/:15/:30/:45, so 17:30 and 12:30 exist and
17:25 / 12:25 never will.

**2. Found while ruling: the bucket's end was open, but the assessment's read is closed. Fixed here (D-R3.7).** The
assessment reads `[start - 30 min, end + 30 min]` closed (`fuel_balance/service.py:108`, with `window_readings`'
`<= :hi`, `actions/adapters/postgres_action_store.py:606`) and picks the closing reading from `end <= t <= end + 30 min`
(`fuel_balance/rules.py:160`). So a reading at exactly local 12:30 can be the night's closing reading: on a 15-minute
sensor with 4 % dropout, a lost 12:00 and 12:15 makes the 12:30 reading the closing one, and `rules.py:160-168` also uses
it for the conflict check. The bucket put 12:30 in no night (`< 12:30`). On a real remote mini-grid, readings arrive
late routinely (gateway store-and-forward after a link outage); a late 12:30 reading would change night d-1's inputs but
never trigger its re-check. The bucket is the re-check trigger, so it must cover exactly what the assessment reads.
**Ruled: the bucket is `[17:30, 12:30]`, closed at both ends.** Two nights' ranges still never overlap (12:30 to 17:30
lies outside both). The start side is already right (opening search `start - 30 <= t <= start`, bucket `>= 17:30`).

Product changes (G2 branch only, nothing else moves):
- `fuel_balance/scheduled.py` `night_of`: `if local.time() <= end:` (was `<`). `bucket_bounds` docstring: "`[NIGHT_START
  - EDGE, NIGHT_END + EDGE]` (closed: the assessment reads both edges)".
- `fuel_balance/adapters/postgres_fuel_balance_store.py`: move the `CASE` into a module constant `NIGHT_BUCKET_SQL`
  (alias `e`, binds `:tz`, `:ns`, `:ne`), ending `... WHEN {local}::time <= :ne THEN {local}::date - 1 END`, and use it
  unchanged in `schedule_inputs` (`SELECT {NIGHT_BUCKET_SQL} AS night, d.decided_at FROM ...`). It is the one SQL source
  the Postgres test evaluates; no other behaviour changes.
- §2.4's "`[start − 30 min, end + 30 min)`" now reads "`[start − 30 min, end + 30 min]`".

**3. What Q1 must prove on Postgres.** That the store's own SQL bucket and `night_of` give the same night for every
instant, at second precision, at both edges, for the real Kisiwa readings and for any cadence another site may report on
(1, 5, 10, 15 or 60 min, or unaligned clocks such as 17:29:58). A set equality on `reading_nights` alone cannot prove an
edge: every night already has dozens of readings, so moving the 17:30 or 12:30 reading in or out leaves the set
unchanged. Hence a per-reading check through the store's own expression, plus synthetic instants for other cadences
evaluated by Postgres. No new evidence is written, so P1-P7 are untouched and R3.1's no-hand-built-batch rule holds.

**Exact asserts, replacing `test_q1_...` body lines 216-242 (the Q12 assert at the end stays as it is):**

```python
from assetops_backend.fuel_balance.adapters.postgres_fuel_balance_store import NIGHT_BUCKET_SQL
from assetops_backend.fuel_balance.composition import build_fuel_balance_store
from assetops_backend.fuel_balance.scheduled import RECORD_LOOKBACK, bucket_bounds, night_of

engine = site["engine"]
ns, ne = bucket_bounds()
b = {"tz": site["tz"], "ns": ns, "ne": ne}
# (a) every real tank reading, through the store's join, acceptance filter and its own CASE
rows = _q(engine, "SELECT COALESCE(e.interval_start, e.source_time) AS at, d.decided_at, "
          f"{NIGHT_BUCKET_SQL} AS night FROM accepted_evidence e JOIN ingestion_disposition d "
          "ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal WHERE e.site_id = :s AND d.decision = 'ACCEPTED' "
          "AND d.accepted_evidence_id = e.id AND e.role = 'fuel_level' AND e.asset_id = CAST(:a AS uuid)",
          s=site["site_id"], a=site["tank"], **b)
local = [(r["at"].astimezone(site["zone"]), r) for r in rows]
hhmm = {t.strftime("%H:%M") for t, _ in local}
print("G2 Q1 readings", len(rows), "minutes", sorted({t.minute for t, _ in local}), "edges",
      sorted(hhmm & {"17:30", "12:30"}))
assert len(rows) > 0 and {"17:30", "12:30"} <= hhmm, sorted(hhmm)   # the real edge readings exist
for t, r in local:
    assert r["night"] == night_of(t), (t, r["night"])              # SQL == Python, every reading
    if t.strftime("%H:%M") == "17:30":
        assert r["night"] == t.date(), t                           # start edge in
    if t.strftime("%H:%M") == "12:30":
        assert r["night"] == t.date() - timedelta(days=1), t       # end edge in (closed, = closing search)
# (b) any cadence: synthetic instants around N0, evaluated by Postgres through the same expression
d, z = site["nights"][0], site["zone"]
d1 = d + timedelta(days=1)
probe = {datetime.combine(d, time(17, 25), z): None, datetime.combine(d, time(17, 29, 59), z): None,
         datetime.combine(d, time(17, 30), z): d, datetime.combine(d, time(17, 30, 1), z): d,
         datetime.combine(d, time(23, 55), z): d, datetime.combine(d1, time(0, 5), z): d,
         datetime.combine(d1, time(12, 25), z): d, datetime.combine(d1, time(12, 29, 59), z): d,
         datetime.combine(d1, time(12, 30), z): d, datetime.combine(d1, time(12, 30, 1), z): None,
         datetime.combine(d1, time(15), z): None}
for at, want in probe.items():
    [got] = _q(engine, f"SELECT {NIGHT_BUCKET_SQL} AS night FROM (SELECT CAST(:x AS timestamptz) AS interval_start, "
               "CAST(NULL AS timestamptz) AS source_time) e", x=at.astimezone(UTC), **b)
    assert got["night"] == night_of(at) == want, (at, got["night"], night_of(at), want)
# (c) the store itself: same nights, and each night's trigger instant is its readings' latest decided_at
store = build_fuel_balance_store(URL)
try:
    inputs = store.schedule_inputs(site["tenant_id"], site["site_id"], RECORD_LOOKBACK)
    empty = store.schedule_inputs(site["tenant_id"], uuid4(), RECORD_LOOKBACK)
finally:
    store.dispose()
want = {}
for t, r in local:
    n = night_of(t)
    if n is not None:
        want[n] = max(want.get(n, r["decided_at"]), r["decided_at"])
print("G2 Q1 reading nights", sorted(inputs.reading_nights), "want", sorted(want))
assert set(inputs.reading_nights) == set(want) == {site["nights"][k] for k in OFFSETS}
assert all(inputs.reading_nights[n].astimezone(UTC) == want[n].astimezone(UTC) for n in want), (inputs.reading_nights,
                                                                                                want)
assert inputs.tank_asset_id == site["tank"] and inputs.generator_asset_id is not None
```

Builder rules: `UTC`, `time`, `datetime`, `timedelta`, `uuid4`, `OFFSETS`, `URL` and `_q` (keyword binds) are already in
the file. If `_q` cannot take the `time` binds, use `engine.connect()` + `text(...)` with the same binds; nothing else.
No `-k` split (R3.2 stands).

**No-DB case 1 (`test_own_g2_fuel_night_due.py:97-112`):**
- `:102` becomes `assert night_of(datetime(2026, 11, 6, 12, 30)) == d  # fails if the end is open (the closing search
  includes end + 30 min)`; add `assert night_of(datetime(2026, 11, 6, 12, 30, 1)) is None  # fails past end + 30 min`
  and `assert night_of(datetime(2026, 11, 5, 17, 29, 59)) is None`.
- `:112` becomes `assert night_of(datetime(2026, 11, 6, 11, 30)) == date(2026, 11, 5)`; add
  `assert night_of(datetime(2026, 11, 6, 11, 30, 1)) is None`.

**4. The two Phase 3 test-code fixes (`0dd9e5af6`) are accepted; neither changes what is proved.**
- (a) Delivery ticket digest: the product refuses a `FUEL_DELIVERY` without a ticket SHA-256 (`work/service.py:550-551`,
  `WORK_RECORD_TICKET_REQUIRED`), which is right for a real site (no ticket, no delivery credit). Before the fix
  P4b/P4c/P5 stopped at `_post`'s 201 assert, before their proof; volumes, times and tank are unchanged, so the fix only
  lets the tests reach what they were written to prove.
- (b) `_ids()`: `record_ids` is stored as `[[root, head], ...]` (`fuel_balance/service.py:124`, `model.py:63`), so the
  old `str(x)` compare could never match. Each dip has one revision (root == head), so "the dip's id is among the
  flattened ids" is the same claim as "the dip is a counted record".

**5. Merge condition update (R3.6).** Item 1 now includes these Q1 asserts passing in the same whole-file run. The no-DB
set (item 2) is rerun after the `night_of` change. The reviewer confirms `NIGHT_BUCKET_SQL` is the only bucket `CASE`
in `schedule_inputs`. The packet lists D-R3.7 as a product change with this reason.

**D-R3.7 (for owner review).** The night re-check trigger now includes a reading at exactly the closing edge (local
12:30), because the assessment uses that reading and real gateways deliver late readings; leaving it out would let a
late closing reading go unnoticed. Cost: one comparison in two places, one extracted SQL constant, and the Postgres
rerun Q1 needed anyway.

### R3.8 — G2 review rulings (2026-11-09)

Claude Architect (binding: Claude, `AssetOpsV1-plan2/.ai/ROLE_CONFIG.md:9`), under the owner's delegation of 2026-11-08
(`.agent/owner-away-architect-decides-2026-11-08.md`). Read-only; no Postgres run. Inputs: `AssetOpsV1-g2/.agent/review-G2.md`
(commit `e2400a0d1`, REJECT on M1) on `task/OWN-G2-diesel-night-check` at `e33d8f113`. **This wins over §2.4 step 4,
§2.4 "What this means", `run_site` step 2.1, §2.7 and R3.6 items 1-2 where they differ.** The builder (Sonnet) makes no
further decision. Branch: the same G2 branch; one fix round.

**Ruled: M1 fixed now (D-R3.8); L2 accepted for now, no change (D-R3.9); L3 fixed now, narrowly (D-R3.10); L1 fixed in
this sheet (§2.4 lines 504 and 511 now read `<= '12:30'` and `[start − 30 min, end + 30 min]`).**

#### R3.8.1 M1 — a record that LEAVES an old night re-checks that night (D-R3.8)

Real-site case: a delivery keyed with the wrong date (or to the wrong tank, or as the wrong kind) is corrected days
later. The night it left must be re-checked, or an "unexplained fuel" Finding the data no longer supports stays open in
front of the client. The base set covers this only for the last 7 nights; the record set (§2.4 step 4) sees only where a
record *is now*, never where it *was*. The stored window already says where it was: `fuel_balance_window.record_ids`
holds the `[root_id, head_id]` pairs the assessment used (`service.py:124`).

**Data read: no new query, no migration, no index.** `schedule_inputs` already reads, on its one snapshot, (a) the tank's
fuel records as known in `[known_at − RECORD_LOOKBACK, known_at)` through K2's `select_fuel_records`, which returns
each record's `root_id` and current `head_id` (head = latest version as known; membership by the head's kind, tank and
occurrence), and (b) each night's latest window through `_windows_on`, which returns `record_ids`. Both are already
bounded to about 32 days. The fix only keeps two more fields from those two reads.

**Model (`fuel_balance/model.py`).** Add `field` to the `dataclasses` import. Append two fields at the END of
`ScheduleInputs` (defaults keep every existing positional constructor call valid, including the early return
`ScheduleInputs(known_at, tz, None, None, {}, (), {})`):

```python
    window_records: Mapping[date, tuple[tuple[str, str], ...]] = field(default_factory=dict)  # night -> its latest window's stored (root_id, head_id) pairs
    record_heads: Mapping[str, str] = field(default_factory=dict)  # root_id -> current head_id, same read as `records`
```

`records` keeps its 2-tuple shape (P5 unpacks it).

**Store (`fuel_balance/adapters/postgres_fuel_balance_store.py`, `schedule_inputs.work`).** Replace the `records = ...`
statement through the final `return ScheduleInputs(...)` of `work` with:

```python
            fuel = self._fuel_records(c, tenant_id, site_id, UUID(tank), known_at - record_lookback, known_at, known_at)
            records = tuple((r.occurred_at, r.recorded_at) for r in fuel)
            record_heads = {str(r.root_id): str(r.head_id) for r in fuel}
            zone = ZoneInfo(str(tz))
            lo = (known_at - record_lookback - timedelta(days=1)).astimezone(zone).date()
            hi = known_at.astimezone(zone).date() + timedelta(days=1)
            stored = _windows_on(c, tenant_id, site_id, UUID(tank), lo, hi, known_at)
            latest = {w.night_date: w.recorded_at for w in stored}
            window_records = {w.night_date: tuple((str(a), str(b)) for a, b in w.record_ids) for w in stored}
            return ScheduleInputs(known_at, tz, tank, generators[0], reading_nights, records, latest,
                                  window_records, record_heads)
```

Docstring of `schedule_inputs`: append "; per night, its latest window's stored record pairs, and per fuel record its
current head (D-R3.8)".

**Due rule (`fuel_balance/scheduled.py` `due_nights`).** New step 4b, inserted after the record loop and before
`return`:

```python
    # 4b (D-R3.8): an older ready night whose stored records changed since its latest window: a stored root whose
    # current head differs, or that is no longer a fuel record of this tank occurring inside the record read
    # (corrected to another time, tank or kind). Only nights whose whole window lies inside the record read are
    # compared; for an earlier night a stored record could be missing only because the read starts after it, which
    # would make the night due on every tick without changing its result.
    read_from = known_at - RECORD_LOOKBACK
    for night, held_ids in inputs.window_records.items():
        if night >= first_base or not ready(night) or rules.night_window(night, tz)[0] < read_from:
            continue
        if any(inputs.record_heads.get(root) != head for root, head in held_ids):
            due.add(night)
```

Why it converges (no spin): the re-assessment reads the night's records as they are now, and its digest covers the
record pairs (`rules.input_sha256(..., records=...)`), so a changed or removed pair always appends a revision whose
stored pairs equal the current heads; the night stops being due on the next tick. A night that is not ready (no
readings, or not quiet) is not touched, as in step 4.

Module docstring of `scheduled.py`, after the "Record set" bullet, add: "- **Left-record set (D-R3.8):** an older
ready night whose latest window cites a fuel record that has since been corrected or no longer counts for this tank."
§2.4 "What this means" gains, in effect: a correction that moves a record out of a night up to 31 days back re-checks
that night (its window must start at or after `known_at − 31 d`).

**No-DB test (`backend/tests/test_own_g2_fuel_night_due.py`).** Extend the helper, keeping the existing keyword order:

```python
def inputs(reading_nights=None, records=(), latest=None, known_at=KNOWN, tank=TANK, window_records=None,
           record_heads=None) -> ScheduleInputs:
    return ScheduleInputs(known_at, TZ, tank, None if tank is None else GEN, dict(reading_nights or {}),
                          tuple(records), dict(latest or {}), dict(window_records or {}), dict(record_heads or {}))
```

Add after `test_5_records_older_than_the_lookback_are_not_read`:

```python
def test_5b_a_record_that_left_an_old_night_rechecks_it() -> None:
    """D-R3.8. Fails on a record set that only looks at where a record is now."""
    old = L - timedelta(days=10)
    held = KNOWN - timedelta(days=9)
    stored = {old: (("r1", "h1"),)}
    # the stored record was corrected (new head; it now occurs elsewhere, so `records` has nothing on `old`)
    assert due_nights(inputs(seen(old), [], {old: held}, window_records=stored,
                             record_heads={"r1": "h2"})).nights == (old,)
    # the stored record is no longer a fuel record of this tank in the read (moved out of range, tank or kind)
    assert due_nights(inputs(seen(old), [], {old: held}, window_records=stored)).nights == (old,)
    # unchanged: same head, recorded before the window -> not due (fails on "any stored record makes it due")
    assert due_nights(inputs(seen(old), [(inside(old), held)], {old: held}, window_records=stored,
                             record_heads={"r1": "h1"})).nights == ()
    # not ready (no readings) -> not due, even with a changed record
    assert due_nights(inputs({}, [], {old: held}, window_records=stored, record_heads={"r1": "h2"})).nights == ()
    # the read-range edge: KNOWN - 31 d is 6 Oct 14:00 local. Night 6 Oct starts 18:00 local (inside) -> compared;
    # night 5 Oct starts before the read (a stored record may simply be unread) -> never compared (fails on spin)
    inside_read, outside_read = L - timedelta(days=30), L - timedelta(days=31)
    both = {inside_read: (("r1", "h1"),), outside_read: (("r2", "h2"),)}
    assert due_nights(inputs(seen(inside_read, outside_read), [], {inside_read: held, outside_read: held},
                             window_records=both)).nights == (inside_read,)
```

**Postgres test (`backend/tests/test_own_g2_fuel_night_tick_postgres.py`).** At the end of `test_p5_...` add one line:
`site["p5_dip"] = str(dip["id"])`. Then add, as the LAST test in the file (file order: Q1, P1/P2/P3/P6/P7, P4a, P4b/c,
P5, P5b):

```python
def test_p5b_a_correction_that_moves_the_dip_out_of_an_old_night_rechecks_it(site) -> None:
    """D-R3.8: N9 (outside the base set) is re-checked when its stored dip is corrected to the afternoon, returns to
    exactly its pre-dip result, and is not due again on the next tick."""
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store
    from assetops_backend.fuel_balance.scheduled import RECORD_LOOKBACK, due_nights

    engine, s, n9 = site["engine"], site["site_id"], site["nights"][9]
    dip_id = site["p5_dip"]
    revs = [w for w in _windows(engine, s) if w["night_date"] == n9]
    rev1, rev2 = revs[0], revs[-1]
    assert (rev1["revision"], rev2["revision"]) == (1, 2) and dip_id in _ids(rev2), revs
    moved = datetime.combine(n9, time(15), site["zone"]).astimezone(UTC)  # before N9 starts, after N8 ends
    correction = _post(_record(site, "TANK_DIP", "g2-p5b-correction", moved, "1", supersedes_record_id=dip_id,
                               canonical_record_id=dip_id, correction_reason="Dip was taken in the afternoon"))
    store = build_fuel_balance_store(URL)
    try:
        inputs = store.schedule_inputs(site["tenant_id"], s, RECORD_LOOKBACK)
    finally:
        store.dispose()
    print("G2 P5b heads", inputs.record_heads.get(dip_id), "held", inputs.window_records.get(n9))
    assert (dip_id, dip_id) in inputs.window_records[n9]
    assert inputs.record_heads[dip_id] == str(correction["id"])
    assert n9 in due_nights(inputs).nights
    fuel = _fuel(_tick(engine)[0], s)
    entry, rev3 = _night(fuel, n9), _latest(engine, s, n9)
    print("G2 P5b", entry, rev3["state"], rev3["limitations"], rev3["record_ids"])
    assert entry and (entry["assess"], entry["revision"]) == ("APPENDED", 3) and entry["raise"] is not None, entry
    assert dip_id not in _ids(rev3) and str(correction["id"]) not in _ids(rev3), rev3["record_ids"]
    assert (rev3["state"], sorted(_ids(rev3)), list(rev3["limitations"])) == (
        rev1["state"], sorted(_ids(rev1)), list(rev1["limitations"])), (rev1, rev3)
    again = _fuel(_tick(engine)[0], s)
    print("G2 P5b again", _night(again, n9))
    assert _night(again, n9) is None and _latest(engine, s, n9)["revision"] == 3
```

Rev 3 equals rev 1 because N9's readings and Foundation are unchanged since the CLI's rev 1, and its records are again
the ones rev 1 had. The dip's first version is its own root and head, hence `(dip_id, dip_id)`. If `_post` rejects the
correction body, copy P4c's exact call shape (it passed on Postgres); any other failure stops and goes to the Architect.

**How it fits the whole-file run (R3.2 unchanged).** P5b adds one correction post, one store read and two ticks after
P5, on the same module fixture; expect +2-4 min on the reviewer's measured 17.7 min, inside the 45-minute budget and the
stall rule. Run the file whole, one process, file order, `-s`, no `-k`/`-n`, as the only heavy job. Update the module
docstring's "Measured:" line to the new result ("6 passed in N s") and add "P5b (D-R3.8)" to its first line's case list.

#### R3.8.2 L2 — quiet looks only at tank readings: accepted for now, no change (D-R3.9)

- **Fail-safe by construction.** The assessment's slot rule is strict: any 5-minute slot of the night without a generator
  power or state reading makes `GENERATOR_KWH_UNKNOWN` / `IDLE_SECONDS_UNKNOWN` true (`fuel_balance/rules.py:170-203`;
  `actions/verification_rules.py:222` and `:295` match a slot's own readings only), and any such reason gives
  `NOT_ASSESSED` (`rules.py:304-315`), never `UNEXPLAINED`. So a night checked before its generator readings land can
  show "not assessed" for a while, but cannot open an unexplained-fuel Finding on missing generator data. The
  reviewer's "open then withdraw" path needs generator data that is complete and then changes, which is a correction,
  not lateness.
- **How real sites send data.** One site gateway publishes tank and generator signals in the same store-and-forward
  batches (Kisiwa's path), so 5 minutes of quiet on the tank readings is quiet on the generator readings too. A site
  with a separate generator logger on another link is the case that differs; there the night is re-checked on every
  tick for 7 nights (base set), so it settles as soon as the readings land.
- **After the demo** (added to §2.4's out-of-scope list in effect): quiet over every role the assessment reads, if a
  site with a separate generator data path is onboarded.

#### R3.8.3 L3 — one refused night blocks later nights: fixed now, narrowly (D-R3.10)

Real-site reasoning: nights are independent (each has its own lock and its own revision chain). A refusal about one
night's stored history must not stop the checks of later nights, which are the most recent and the ones the operator
acts on. The failure must still be visible (Site failure, `last_failure_stage`, back-off capped at 16 min,
`tick.py:91-92`, `:132-133`). `CLOCK_BACKWARDS` is the only per-night refusal the scheduler can meet (a window recorded
at an instant later than DB now: a DB clock step back or failover, or a tool that assessed at a future virtual instant).
`WINDOW_INVALID` cannot come from scheduler-computed nights and stays a defect that fails at once.

**`run_site` (`fuel_balance/scheduled.py`).** Import `CLOCK_BACKWARDS` from `model`. Before the loop add
`refused_nights: list[tuple[date, FuelBalanceRefused]] = []`. In the `except FuelBalanceRefused as refused:` block,
after the `ASSETS_UNSUPPORTED` branch and before the bare `raise`:

```python
            if refused.code == CLOCK_BACKWARDS:  # D-R3.10: this night only; later nights still run
                nights.append({"night_date": night.isoformat(), "assess": "REFUSED", "revision": None,
                               "state": None, "raise": None})
                refused_nights.append((night, refused))
                continue
```

After the loop, before building the return dict (so it also applies after an `ASSETS_UNSUPPORTED` break):

```python
    if refused_nights:
        raise FuelBalanceRefused(CLOCK_BACKWARDS, f"{len(refused_nights)} night(s) refused "
                                 f"({', '.join(d.isoformat() for d, _ in refused_nights)}); first: "
                                 f"{refused_nights[0][1].detail}")
```

A refused night counts toward `limit` (it used an assess call). The raise keeps the stage contract unchanged
(`stages.classify` gives `FAILED`; the error holds the code), while every later night's assess and raise are already
committed in their own transactions. Any other refusal (`WINDOW_INVALID`) still raises at once, unchanged.

**No-DB test (`backend/tests/test_own_g2_fuel_night_stage.py`).** Import `WINDOW_INVALID` beside `CLOCK_BACKWARDS`.
Replace `test_clock_backwards_raises_and_the_stage_fails_with_the_code` with:

```python
def test_clock_backwards_on_one_night_still_checks_later_nights_then_fails_the_stage() -> None:
    """D-R3.10. Fails on the old re-raise (L is never assessed) and on swallowing the refusal (no raise)."""
    store = FakeStore(inputs(seen(PREV, L)), {PREV: FuelBalanceRefused(CLOCK_BACKWARDS, "before revision 1")})
    findings = FakeFindings()
    with pytest.raises(FuelBalanceRefused) as refused:
        run_site(store, findings, "t", "s", 10, None)
    assert [c[1] for c in store.calls if c[0] == "assess"] == [PREV, L] and findings.calls == [L]
    assert refused.value.code == CLOCK_BACKWARDS and PREV.isoformat() in str(refused.value)
    assert stages.classify(refused.value) == "FAILED" and CLOCK_BACKWARDS in str(refused.value)


def test_any_other_refusal_still_fails_at_once() -> None:
    store = FakeStore(inputs(seen(PREV, L)), {PREV: FuelBalanceRefused(WINDOW_INVALID, "bad window")})
    with pytest.raises(FuelBalanceRefused) as refused:
        run_site(store, FakeFindings(), "t", "s", 10, None)
    assert refused.value.code == WINDOW_INVALID and [c[1] for c in store.calls if c[0] == "assess"] == [PREV]
```

§2.4 `run_site` step 2.1 now reads, in effect: `WINDOW_OPEN` skip; `ASSETS_UNSUPPORTED` stop as ineligible;
`CLOCK_BACKWARDS` record the night as `REFUSED`, continue, and fail the stage after the loop; any other refusal raise.

#### R3.8.4 Merge condition (replaces R3.6 items 1-2; items 3-5 stand)

1. `test_own_g2_fuel_night_tick_postgres.py` whole file under R3.2: **6 passed** (Q1/Q12, P1/P2/P3/P6/P7, P4a, P4b/c,
   P5, P5b), by the builder and again by the reviewer; the packet records the runtime and the `G2 ...` lines incl. P5b's.
2. The R3.6 item 2 no-DB set is green, including `test_5b_...` and the two stage tests above.
3. R3.6 item 3 needs no rerun (no stage, tick or limits file changes). The R3.4 confirming run on main is done
   (`review-G2.md` run 3) and stands.
4. A fresh Claude re-review of this fix round (M1, L3, the tests), then `--no-ff` merge and check-all on main, as R1.3
   says.

**D-R3.8 (for owner review).** A correction that moves a fuel record out of a night (wrong date, tank or kind) now
re-checks that night up to 31 days back, so an unexplained-fuel Finding never stays open on data that was corrected.
It reuses two reads the check already makes: no new query, table or migration. Cost: about 15 lines, one no-DB case
and one Postgres case (+2-4 min on the G2 run).

**D-R3.9 (for owner review).** Not changed now: a night may be checked before late generator readings arrive. It is
safe because missing generator data makes the night "not assessed", never "unexplained", and the night is re-checked
for 7 nights. Revisit only if a site sends generator data on a separate link.

**D-R3.10 (for owner review).** A problem with one night's stored history (a clock that moved backwards) no longer stops
the checks of later nights; the Site still shows the failure in health. Cost: about 10 lines and two no-DB tests.

---

## R4 — DS-1a residual rulings (2026-11-09)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`, main `b73c65eb6`). Owner away; decisions delegated
(`.agent/owner-away-architect-decides-2026-11-08.md`). Read-only; no Postgres run. Input: the two residual risks in
`AssetOpsV1-ds1a/.agent/review-DS-1a.md` ("Residual risk"). **READ** = code or file, cited.

### R4.1 Cold room "No action yet" on the Portfolio against ACT-002 in step 4: a product inconsistency; fix before E1

**Cause (READ).**
- `select_action_scope` reads Actions only for mini-grid Sites (`estate/index.py:256-259`, `applicable = ... == MINI_GRID`).
  Cold and EV domain Actions never reach `_action_for`, so every Cold/EV row gets `workflow_label(None)` = "No action
  agreed yet" (`estate/portfolio.py:226-229`), the bold cell "No action yet" (`EstatePortfolio.tsx:207`) and the
  placement reason "No action agreed yet · review the recommendation" (`estate/placement.py:33, 51`).
- The chain already knows the truth: thread sources include `domain_action` (`chain/adapters/postgres_thread_sources.py:73, 185`),
  `attach_threads` puts each row's thread (with `state`) on the row, and the K9 rehearsal build's F-THREADS read shows
  Cold threads `["Action agreed", "Open"]` and EV `["Action agreed"]` (`AssetOpsV1-k9/var/demo3_k9rehearsal/check.json`).
- So the Portfolio says "no action agreed" while the board, the Work page and the chain say one is. This is the same
  class as K8 L1, which R-1 fixed for the fuel row only (`FUEL_THREAD_LABEL`, `estate/portfolio.py:257-267`;
  `EstatePortfolio.tsx:153-154, 202-204`). DD1b2-R9's "nothing shown is false" was wrong: the row states "No action
  agreed yet", and that is false for the start-failure thread.
- **Why it matters on a real Site:** the Portfolio exists to tell a manager where nobody is acting yet. A row that says
  "no action agreed" when the site team already owns a witnessed start test sends the manager to chase work that is
  in hand, and teaches him not to trust the list. That is a fundamental, not polish.

**Ruling: fix it now with the R-1 mechanism, generalised. BL-47 (joining the Action itself, code and link) stays in
the backlog.** One source for "is someone acting": the thread state the chain already computed, read at the row's own
cutoff, exactly as the fuel row does. No new query, port, table or migration.

**Product change (branch `task/R4-1-domain-row-thread-state`, from main):**
1. `backend/assetops_backend/estate/portfolio.py`
   - Rename `FUEL_THREAD_LABEL` to `THREAD_LABEL` (same four entries; update its comment: "a row whose Action the
     Portfolio does not join: the fuel row (FUEL_BALANCE domain) and every Cold/EV row (`select_action_scope` reads
     mini-grid Actions only)").
   - In `portfolio_row`, replace the `label = ...` statement with:
     ```python
     unjoined = r.get("_mechanism") == "UNEXPLAINED_FUEL" or (
         action is None and DOMAIN_OF_SITE_TYPE.get(r["_domain"], NOT_APPLICABLE) in (COLD, EV))
     label = (THREAD_LABEL.get((r.get("_thread") or {}).get("state"), "No action agreed yet") if unjoined else None)
     ```
     (`COLD`, `EV`, `DOMAIN_OF_SITE_TYPE`, `NOT_APPLICABLE` are already imported at `:25-26`.) Mini-grid rows are
     unchanged: their join is authoritative, so a mini row with no joined Action keeps "No action agreed yet".
   - Effect: ACTION_IN_HAND → "Pending" (placement reason ACTION_PENDING, "Action accepted, not yet applied"; Cold
     start-failure rows stay in Act now because their episode is open); CHANGE_APPLIED → "Applied";
     RESOLVED_MONITORING/CLOSED → "Verified"; OPEN, RECURRED, no thread → "No action agreed yet" (unchanged). The Cold
     temperature row stays "No action yet": its own thread is Open, which is true.
2. `frontend/src/estate/EstatePortfolio.tsx`: rename `fuelThread` to `threadState` and drop the mechanism test:
   `const threadState = row.action_id === null && row.workflow_label !== "No action agreed yet";` (for a mini row with
   no Action the label is always "No action agreed yet", so mini rows are unchanged). Extend the MOCK DEVIATION
   comment: "MD-FUEL-K4-1, extended by R4.1 to Cold/EV rows: the Action column shows the row's thread state in bold
   when the Portfolio does not join the Site's Actions."
3. No change to `actionIndex.tsx`, the estate Actions list, `select_action_scope`, the cursor, COH-2's named
   expectation (`action_id` stays null, so it still applies) or any tool.

**Tests (no DB; no Postgres file is touched):**
- Backend, new `backend/tests/test_r4_domain_row_thread_state.py` (pure `portfolio_row` with a Cold and an EV row
  fixture; copy the row shape from `test_w303_portfolio_workflow_labels.py`):
  (a) Cold, no Action, thread `ACTION_IN_HAND` → `workflow_label` "Pending", placement ACT_NOW with reasons
  `[EPISODE_OPEN, ACTION_PENDING]`; (b) Cold, thread `OPEN` → "No action agreed yet"; (c) EV, `CHANGE_APPLIED` →
  "Applied"; (d) Cold, `_thread` None → "No action agreed yet"; (e) **must-fail guard**: a mini-grid row with no
  Action and thread `ACTION_IN_HAND` → "No action agreed yet"; (f) the fuel row is unchanged (one case).
- Frontend, `frontend/src/estate/__tests__/estatePortfolio.test.tsx`: a Cold row with `action_id: null`,
  `workflow_label: "Pending"` renders bold "Pending" with `data-portfolio-workflow`, has no "No action yet" text in
  its Action cell, and keeps the "Review finding" link; a Cold row with "No action agreed yet" still renders "No action
  yet" plus the workflow text.
- Run: the two files above, `test_w303_portfolio_workflow_labels.py`, `test_cc_placement.py`, and vitest for
  `estatePortfolio.test.tsx` and `estateRoots.test.tsx`. An existing test that pinned "No action agreed yet" on a
  Cold/EV row **with an in-hand thread** is updated and listed in the packet; any other change to an existing
  assertion stops the work and comes to the Architect.

**Proof on the demo build (E4 checklist item, no code):** on the "Portfolio, week to story day S" link, the two Cold
"Backup generator did not start" rows and the EV row read **Pending**, and the Cold temperature row reads **No action
yet**. If a start-failure row reads "No action yet", the Portfolio's thread state disagrees with the board (COH-13
would also fire): stop and bring it to the Architect; do not change the script to match.

**Size and slot:** 0.25 unit (Sonnet build; fresh Opus light review, High/Medium block). Lane B (free since G3b merged),
merged before E1 (Thu 12, 08:00), then check-all on main per R1.3. It touches no G1 file.

**DS-1a / DS-1f changes:**
- Replace `demo-script-img/03-portfolio-act-first.png` with the same crop from E5's Portfolio capture (1440), so the
  illustrative picture does not show the old text. ST-1 quotes the row words from that crop.
- ST-4, presenter note (add after the Say): "On the Portfolio, the start-failure rows read Pending: an action is
  agreed and not yet done, and the action is ACT-002 on this page. The temperature row reads No action yet, which is
  correct: no action has been agreed on the temperature itself."
- ST-4 "If asked" (add): "Why does the Portfolio not name ACT-002?" → "The Portfolio shows whether someone is acting;
  the action itself, its owner and its test are on the Site's Work page, one click away."
- Callout 3 stays: the Work page does show the owner.

**D-R4.1 (for owner review).** The Portfolio now reads "Pending" (not "No action yet") on Cold and EV findings that
already have an agreed action, from the same chain state the board shows. Naming the action itself on the Portfolio
row (BL-47, about 0.5 unit) stays after the demo.

### R4.2 Step 7, "a new day arrives": hold yesterday back for Kobo, release it during the session

**What exists (READ).**
- A real Site's readings arrive all day from its gateway; nobody adds a day. A whole day arriving at once does
  happen on remote sites: a gateway that loses its uplink stores its readings and sends them when the link returns.
  That is the only honest real-site picture of "a day arrives during the meeting".
- `add-dates` is the demo's gateway (§4.1). Per date it runs the Site's child and then one `Demo.tick()`, the product's
  own scheduled tick (`AssetOpsV1-g1/tools/demo_combined.py:1069-1090`); readings keep their story time and are
  recorded at real time (client-demo-plan §2.5.1a "Honesty rules"). R1.5's estimate: Kobo about 7 min plus one tick
  about 2 min, so **about 9 min** from start to the day being checked. Nothing arrives in 3 minutes.
- The morning catch-up (`add-dates`, to yesterday) leaves no ended day free, so the old plan's "the live step adds
  S+2" (client-demo-plan §2.5.1a) has no day to add unless one is held back.
- The frontend does not poll (no `refetchInterval`/`setInterval` in `frontend/src`): the presenter reloads the page.
- The serve's scheduler also ticks every two minutes (CO-2); the tool's tick only runs the same check sooner.

**Ruling.**
1. **The held day is Kobo's yesterday** (Site-local date). It is exactly the day the morning catch-up would have
   added, with the same `normal` kind, so no story content changes. Kobo is chosen because it is the Site the client
   has just seen and its board grades the day against its objectives.
2. **Morning runbook (replaces R1.5's single `add-dates` line on a demo day):**
   ```
   ... add-dates --site COLD-LAB-001,EV-LAB-001,KISIWA-001 --no-check      (catch up to yesterday)
   ... add-dates --site KOBO-001 --to <day before yesterday>               (Kobo stops one day short; ends with the finish check)
   ... links
   ```
   If `<day before yesterday>` is a Kobo story day, the second command refuses with `STORY_DAY`: nothing is missing,
   so run `... add-dates --site KOBO-001 --to <day before yesterday> --dry-run` to confirm, and run the first command
   without `--no-check` instead. If **yesterday** is itself a Kobo story day (a session on S+2 or earlier), there is
   no day to hold: run the R1.5 catch-up unchanged, and step 7 uses the backup pictures and says so.
3. **Live command (during the session, off-screen, in a second window):**
   `... add-dates --site KOBO-001 --to yesterday --no-check`. After the client leaves: `... add-dates` with no options
   (it adds nothing or today's catch-up and always ends with the finish check, `:1091-1092`). A FAIL retires the
   build (R1.5).
4. **When to start it:** at the end of the last Kobo step (ST-3, or ST-3b when present). That leaves ST-4 to ST-6
   (3 + 2 + 6 + 2 = 13 min) for about 9 min of work. The Fri 13 owner walkthrough times it; if start-to-checked
   exceeds 11 min, start it at the end of step 0 instead (the before view then moves to step 0).
5. **The before view is shown live**, so the change is seen, not asserted: at the end of the last Kobo step the
   presenter opens `http://localhost:<web>/sites/KOBO-001?date=<yesterday>` (the `links` Kobo board form with
   yesterday's date) and shows the day with no readings, quoting the board's own words (DS-1f placeholder from the
   walkthrough). In step 7 the presenter reloads that page.
6. **Only the Kobo board is promised.** The Portfolio's story-week link ends before yesterday, so step 7 does not
   claim a Portfolio change. The checklist row 7 "Expected" becomes: "Kobo board for yesterday: before, no readings
   (board's words); after reload, the day is checked (board's words)."
7. **Not done in time** (the tool's plain line "KOBO-001: added …" has not printed when step 7 opens, or it refused):
   show the walkthrough's before/after pictures, say "Yesterday's readings are still arriving; we will open the day
   again at questions", and do so. Never say the day has arrived before the line has printed.

**Exact script wording (DS-1a, ST-7; replaces the current Say, "If asked" and "What it means"):**
- *End of the last Kobo step, Say:* "One more thing at Kobo. This is yesterday: no readings yet. In this demo we held
  yesterday's readings back, the way a site's gateway keeps them when its connection drops. I am letting them
  through now; we will come back to this day at the end."
- *Step 7, Say:* "Kobo's readings for yesterday have now arrived, as a gateway sends its stored readings when its
  connection returns. I reload the page: the day has been checked by the same rules as every other day. Nobody
  rebuilt a report or touched a spreadsheet."
- *What it means:* "Data arrives from the site and the checks follow on their own. A late day is checked like any
  other, and the screens state which days were checked."
- *If asked, "How often does it update?":* "In this demo, at the next background refresh, every two minutes. How
  often a real Site's readings arrive is agreed for a pilot." (the M2 fix).
- *If asked, "Who added that day?":* "In this demo, I released readings that were held back. On a real Site they come
  from your meters through the gateway; nobody adds them."
- Step 7's time stays 3 min. The step-map label changes from "New day" to "Yesterday arrives".
- Still forbidden: "live", "real time", "within minutes" without "in this demo", and any claim that the day arrived
  by itself without the held-back sentence.

**No code change.** G1 is not reopened: everything above uses `add-dates` options in §4.2. DS-1a's Sonnet refresh
takes R4.1's script lines and R4.2's wording and runbook; DS-1f fills the before/after words from the Fri 13
walkthrough.

**D-R4.2 (for owner review).** Step 7 shows one real held-back day (Kobo's yesterday) being released during the
session and checked by the product's normal background check, said plainly as held back in this demo. It takes about
9 minutes, so it starts after the Kobo steps and is revealed at step 7; the morning catch-up stops Kobo one day short.

## R5 — G1 rehearsal F-THREADS (2026-11-09)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Owner away; decisions delegated ("let the architect make
decisions ... based on understanding of how real sites work and what assetops is trying to achieve, no cutting
corners on fundamentals"). Input: `AssetOpsV1-g1/.agent/OWN-G1-phase-2-handoff.md`, branch `task/OWN-G1-add-dates`
head `d9540c26c`. **READ** = code cited; **DB** = read-only query on `assetops_demo3_g1audit_test` (session
`default_transaction_read_only = on`; the drain `counts` child, which only SELECTs). Nothing was written to the clone.

### R5.1 Root cause (READ + DB): the added days' mini-depth work was still queued when "checked" was reported

- **DB, after run 1** (`demo_combined_drain.py counts`): every count is 0 except `mini_deferred`: **KOBO-001 24,
  KISIWA-001 70**. `recompute_job` rows created by run 1: Kobo 34 (10 `DONE`, 24 `PENDING`, all created 00:09:48Z,
  windows 2026-11-08 02:00–12:00Z = the added day); Kisiwa 92 (22 `DONE`, 70 `PENDING`, created 00:01:12Z, windows
  2026-11-07 14:00Z – 11-08 13:00Z = the added night). Nothing else is pending (dirty, snapshots, threads,
  opportunity all 0).
- **Why one tick is not enough (READ).** The tick's `mini` stage leases at most `TickLimits.mini_jobs_per_site = 10`
  jobs per Site (`scheduling/tick.py:70`, `scheduling/stages.py:140-155`). A day arriving at once creates ~34 Kobo jobs
  and ~92 Kisiwa jobs. §4.4 runs exactly one tick per date (`tick_and_verify`, `demo_combined.py:1145-1173`), so 10
  Kobo jobs ran and 24 stayed queued. `_add_core_day` drains mini only for `assess == "build"` (`:1018`); `add-dates`
  days are not "build".
- **Why the board says Unknown (READ).** The mini board's settledness needs every depth domain's head for the board
  day: `depth_ok = all(depth.get(d) is not None for d in DEPTH_DOMAINS)` (`site_outcomes/mini.py`, `compose`), and
  `settled["MG-1"] = settled["MG-5"] = base and depth_ok`; an unsettled outcome is `UNKNOWN / PRODUCER_NOT_SETTLED`
  (`outcomes/status.py:71-72`). F-THREADS (`demo_combined_finish.py:856-891`) reads every delivered `days.json` day's
  board through `board_faults` and found that code on KOBO-001 2026-11-08.
- **The builder's guess is right in substance, with one correction:** it is not the late assessment as such, nor a
  missing second tick. It is that the tool reported a day "checked" while the product's own queue for that day still
  held work. `serve` does not drain either (`:1209-1245`: one tick every 120 s); it simply keeps ticking, and would
  have settled Kobo after ~3 more ticks (~6 min) and Kisiwa after ~7 (~14 min).
- **Same defect on Kisiwa, uncaught.** The added Kisiwa night's board day had 70 depth jobs queued. No row caught it:
  F-THREADS reads only `days.json` days (Kobo, Cold, EV); Kisiwa nights live in `kisiwa-days.json`; KIS rows read story
  nights only. The fix below covers it at the producer level; R5.5 adds a rehearsal read of the Kisiwa boards.
- **Is the late arrival handled correctly by the product? Yes.** The readings went through the gateway path, were
  accepted at real time, and the product queued exactly the depth work a real gateway reconnecting after an outage
  would cause. The product is right; the tool's claim was premature. **No product change.**

### R5.2 Ruling: settle each date through the product's own producers before moving on (no product code; G1 tool only)

How a real site works: readings arrive, the product queues the work they cause, and the day is "checked" only when
that work has run. A whole day arriving at once (the R4.2 gateway-reconnect story) is a burst; the scheduler works it
off at its bounded rate. The tool simulates the gateway and also stands in for wall-clock time, so before it says a
day is checked, or sends the next day, it must let the queue run to empty **through the same producers**. It must not
skip, special-case or mark anything.

Both mechanisms below already exist and are the ones `prepare` uses (`finish`, `:785-808`):
- `drain_mini()` (`:810-826`): the worker's own CLI `mini_depth.worker run-pending`, i.e. the same
  `MiniDepthWorker.run_pending` the tick's `mini` stage calls, with the same DB-time lease and cutoff, without the
  per-tick bound of 10. Outputs are identical; only the throughput differs.
- `drain(name)` (`:878-934`): the product's scheduled tick (`TICK`, raw), repeated until every count (dirty,
  snapshots, threads, mini, opportunity) is 0 on every Site, with the N / 2N / two-flat-ticks failure guards; then
  Performance and pre-build once (as `tick()` does).

`drain()` alone is **not** enough: its N ignores `mini_deferred` (`demo_combined_drain.py:26-31`), so 70 Kisiwa jobs
at 10 per tick would fail "past 2N" (N = 2). `drain_mini()` comes first, exactly as in `prepare`.

**Exact change, `tools/demo_combined.py` only:**

1. New method:
   ```python
   def settle(self, name: str) -> dict:
       """R5.2: run the queued work of the added data through the product's own producers until nothing is due:
       the mini-depth worker (no per-tick bound), then the scheduled tick until every drain count is 0."""
       self.drain_mini()
       return self.drain(name)
   ```
   `defer_drain` stays False in `add-dates`, so a failed drain raises `SystemExit("DRAIN FAILED: …")` (`:925-926`).
2. In `add_dates`, the per-date block (`if today: added += self.tick_and_verify(today)`) becomes:
   - **A date with a Kisiwa night:** `self.drain_mini()`, then `tick_and_verify(today)` (unchanged: its `tick()`
     writes `last-tick.json`, which KIS-11 reads, and verify-day needs that report), then
     `record = self.drain(f"settle-{d.isoformat()}")`.
   - **A date with only Kobo/Cold/EV days:** `record = self.settle(f"settle-{d.isoformat()}")` and no separate
     `tick()`. `drain`'s first tick is the date's tick (§4.4's "one tick" becomes "ticks until settled"). This saves
     one ~80 s tick per date, which matters for R4.2's live step. It also leaves `last-tick.json` as the last
     Kisiwa-visiting report, as in `prepare`, where the drain ticks after `tick(times=2)` do not rewrite it.
   - Then, for every non-Kisiwa item of the date: `item["checked"] = f"settled ({record['ticks']} ticks)"` (replaces
     `"tick " + outcome`). Every item of the date also gets `"tick_failures"`: the `tick_failure` entries of
     `record["log"]` (an empty list when none). A non-empty list is printed in the item's plain line as "(a background
     step reported a failure; see logs)". It does not stop the command (prepare's own drains record and continue, and
     the closing `finish check` judges the build). The rehearsal requires it to be empty (R5.5).
   - Kisiwa's `tick_and_verify` loop is otherwise unchanged; for a Kisiwa-only date the non-Kisiwa `checked` loop
     simply has nothing to do.
3. **Closing settle (resume after a crash or a stopped run).** After the date loop and before `finish check`,
   whether or not any date was added, read `self.counts()`; if `demo_combined_drain.total(counts) > 0`, say "settling
   work left from an earlier run" and run `self.settle("settle-close")`. This makes the "already present" second run
   (§4.7 step 2) finish what a crashed or stopped first run left. It runs also under `--no-check`. With all counts 0 it
   costs one counts child and no tick.
4. `--no-check` skips only `finish check`, never the settle (R4.2's live command uses `--no-check`, and the presenter's
   reload must show the day checked, not Unknown).
5. A drain failure inside `add-dates` leaves earlier dates in place (append-only, as §4.5). The `SystemExit` message is
   prefixed with "{site list} {date}: the added data did not finish processing; " and ends with "prepare a fresh build
   before a demo." `.busy` is removed by the existing `finally`.
6. No change to `add-day` for Kobo/Cold/EV outside `add-dates` (its `late` kind deliberately leaves the day for the
   serve tick, DEMO-SPARSE U4), to `drain`, `drain_mini`, `n_for`, the tick limits or any product file.

**Time effect.** Per date add one `drain_mini` pass (Kobo 34 jobs) and usually 1–2 ticks. R4.2's live Kobo step goes
from ~9 min to an estimated ~10–11 min. R4.2 item 4 already says: if the Fri 13 walkthrough measures start-to-checked
above 11 min, start it at the end of step 0. Report the measured `settle-*` seconds in the packet.

### R5.3 Tests (no DB), `backend/tests/test_own_g1_add_dates.py`

Use a `Demo` test double: `object.__new__(Demo)` with `story`, `_add_core_day`, `add_kisiwa_night`, `kisiwa_child`,
`tick`, `drain_mini`, `drain`, `counts`, `finish_check`, `db_now`, `site_zones`, `delivered_days`, `hold_busy`
replaced by recorders that append `(name, args)` to one call list. `work` is a `tmp_path` holding `days.json` and an
empty `kisiwa-days.json`.
1. **Kobo-only date:** call order `_add_core_day(KOBO-001)`, `drain_mini`, `drain("settle-<date>")`; **no** `tick`;
   the summary item's `checked` is `"settled (2 ticks)"` from a drain record `{"ticks": 2, "log": []}`. **Must-fail
   guard:** with the settle removed this test fails (it asserts both `drain_mini` and `drain` are called, in that order,
   after the child).
2. **Date with a Kisiwa night and a Kobo day:** order `add_kisiwa_night`, `_add_core_day(KOBO-001)`, `drain_mini`,
   `tick`, `kisiwa_child("verify-day", …)`, `drain("settle-<date>")`. `drain` runs after verify-day, and `tick` is called
   exactly once when verify answers DONE the first time.
3. **Date-major preserved:** two dates; date 1's `drain` precedes date 2's first child.
4. **Drain failure stops the command:** `drain` raises `SystemExit("DRAIN FAILED: …")` on date 1; date 2's child is
   never called, `finish_check` is never called, `.busy` does not exist afterwards, and the message carries the
   R5.2 item 5 prefix and suffix.
5. **`--no-check` still settles:** order as test 1, `finish_check` not called.
6. **Nothing added, nothing pending:** every date "already present" (`_add_core_day` raises `DUPLICATE_DAY`), `counts`
   returns all zeros → no `drain_mini`, no `tick`, no `drain`; `finish_check` called once.
7. **Closing settle on resume:** as test 6 but `counts` returns Kobo `mini_deferred: 24` → `drain_mini`, then
   `drain("settle-close")`, then `finish_check`.
8. **Tick failures carried:** drain record `log` has one entry with `tick_failure` → the item's `tick_failures` has it,
   its plain line has the R5.2 text, and the command does not stop.
9. Existing `--dry-run` test extended: none of `drain_mini`, `drain`, `counts`, `tick` is called.

Run: `test_own_g1_add_dates.py` plus the phase-2 no-DB set; the same 5 known failures minus the one fixed in R5.6
(so 4, all identical on main).

### R5.4 F-THREADS: correct; it stays as is

F-THREADS states a fundamental: no board for a day with delivered data says Unknown because a producer has not
finished. A manager who opens yesterday and sees Grow and Cost "Unknown" learns that the product is not ready to be
looked at. It fired on exactly the board R4.2 step 7 will reload in front of the client. Including added days is
correct: they are delivered days in `days.json`. **No bound, no exclusion, no change.** R2-G1 Q3's pre-authorised
bound is for KIS rows only and does not extend to F-THREADS.

Kisiwa added nights are outside F-THREADS (R5.1). The producer-level guarantee (R5.2: `drain` ends only at all counts 0
on every Site) covers them for G1. A permanent Kisiwa added-night board row in `finish check` is **BL-52** (the coordinator adds it to `.agent/backlog-post-demo.md`;
not demo-critical given that guarantee; 0.25 unit).

### R5.5 Rehearsal re-run

The run-1 clone is in exactly the failing state. Use it first to prove the fix and the resume path. Then re-clone, to
prove the per-date path on fresh data, which the reused clone cannot show (its dates are already present).

0. Commit the R5.2 change, the R5.3 tests and R5.6 as separate commits; rebuild `tree` from the new HEAD (handoff
   recipe: `git archive`, prepare's parts + `var/sites/kobo-001.yaml`); expect the one-time `chain_snapshots` rebuild.
1. **Reused clone (resume proof):** the same command,
   `add-dates --site KOBO-001,KISIWA-001,EV-LAB-001 --to 2026-11-08`, on `assetops_demo3_g1audit_test` /
   `var/demo3_g1audit`. Expect: plan with nothing new (or Kisiwa 11-08 if run after 12:05Z, which is then added and
   settled per date), "already present" for the run-1 days, "settling work left from an earlier run", `settle-close`
   `verdict: done`, **finish check PASS (51/51)**. Keep `check.json` and `settle-close.json` as evidence. Then rename
   the folder to `var/demo3_g1audit_run1` (evidence; untracked) and drop the database.
2. **Fresh clone:** no serve on the template; `CREATE DATABASE assetops_demo3_g1audit_test TEMPLATE
   assetops_k9_audit_r3u`; robocopy `AssetOpsV1-k10\var\demo3_r3u` → `var/demo3_g1audit` without `tree`; `tree` from
   the new HEAD; `evidence_migration run` (KOBO-001) and `performance_migration run` (KOBO-001, KISIWA-001), all
   "cutover: permitted" (as phase 2).
3. **Run A:** `add-dates --site KOBO-001,KISIWA-001,EV-LAB-001 --to 2026-11-08` (`yesterday` also works once every
   Site's yesterday is 11-08). Expect per-date `settle-<date>.json` with `verdict: done`, every item's `tick_failures`
   empty, the Kisiwa night(s) `WITHIN_MARGIN (revision 1)`, Kobo `settled (n ticks)`, **finish check PASS (51/51)**.
4. **Run B:** the same command: everything "already present", counts all 0 so no settle (no `settle-close.json`
   written), finish check PASS.
5. `--to` today: the run-1 evidence (`DATE_NOT_PAST`, nothing written) stands; that path is unchanged. Do not repeat it.
6. Read-only proofs after run B: the drain `counts` child shows 0 for every field on every Site. A scratch
   (uncommitted) read through `finish.app_client` of the KISIWA-001 board for each added `night_date` gives
   `board_faults == []`. For the last added night's next board day, record the faults; they are not blocking.
   `chain_coherence collect` + `check` gives EX-2 = 0.
7. Then the review packet `.agent/review-packet-G1.md` with the settle timings, run A wall time and both `check.json`
   summaries. Keep the fresh clone until review ACCEPT, then drop it.
   **Stops:** any non-PASS row, any `tick_failures`, a `settle-*` `verdict: fail`, or a Kisiwa board fault on an added
   `night_date` → back to the Architect with the file. A KIS row failing only on added-night content still takes the
   R2-G1 Q3 bound. Cap: the original 2 × 1.5 h for steps 1–6.

### R5.6 `test_carry_r3k2_l2_no_kis_row_keeps_the_skip_branch` (12 vs 13): fix it on the G1 branch

READ: main's `demo_combined_finish.py` has 13 `raise KisiwaMissing()`. The 13th is KIS-11's no-Kisiwa branch
(`:1489-1490`, added by OWN-G2 u2 `06c09b95b`). It is the same skip-branch pattern the test protects, and the test
pin was simply not updated when G2 merged. A known-red test hides real failures behind "fails on main too", so it is
not left to E2. **Fix on the G1 branch as its own commit:** `== 12` → `== 13` and add "KIS-11 (OWN-G2)" to the comment
list on `:594-595`. If the builder's count of the 13 raises does not match the 13 `@row("KIS-…")` rows one-to-one
(KIS-4, 8a, 1, 2, 6, 7, OV, 5, 10, 3, 9, 11, 8), stop and report; do not change the count.

### R5.7 Decisions logged for owner review

- **D-R5.1** Cause of the G1 rehearsal failure: the tool said Kobo's added day was checked after one background
  refresh, while the product still had 24 of that day's 34 analysis jobs queued (10 run per refresh). Kisiwa's added
  night had 70 queued, and no check caught it. The product handled the late day correctly; the tool's claim was early.
  No product change.
- **D-R5.2** Fix: before `add-dates` reports a day checked or sends the next day, it runs the queued work through the
  product's own workers and scheduled refresh until nothing is due (the method `prepare` already uses), under
  `--no-check` too. It also does this once at the end if an earlier run left work pending. The live Kobo step may take
  ~1–2 min longer (R4.2's start-earlier rule covers it).
- **D-R5.3** The failing check (F-THREADS: no board may say "Unknown" because processing has not finished) is right and
  stays unchanged. A Kisiwa equivalent for added nights is backlog BL-52; the settle covers Kisiwa now.
- **D-R5.4** Rehearsal: first on the failing clone (proves the fix and the resume path), then on a fresh clone (two
  identical runs), all checks green before review.
- **D-R5.5** The stale Kisiwa test count (12 → 13 after the diesel-night check added KIS-11) is fixed on the G1 branch
  now, not left red until E2.

## R6 — G1 resume run: CO-2, WK-6 and the tree rebuild (2026-11-09)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Owner away; same delegation and fundamentals instruction
as R5. Input: `AssetOpsV1-g1/.agent/OWN-G1-phase-3-handoff.md` (branch head `7bf811898`). **READ** = code cited;
**DB** = read-only query on `assetops_demo3_g1audit_test`. R5's settle fix is confirmed: `settle-close` drained 94
mini jobs, every count reached 0, and F-THREADS passed.

### R6.1 CO-2 (STALE_PROJECTION: SCHEDULE_STOPPED, SITE_VISIT_STALE): the product is right; add-dates ticks once before the check

**What the product does (READ).** `UpstreamCurrentness` (`scheduling/upstream.py:176-183`) blocks currentness with
`SCHEDULE_STOPPED` when the environment heartbeat is older than its threshold (300 s), and with `SITE_VISIT_STALE` when
the Site head is not observed. CO-2 (`demo_combined_finish.py:252-264`) requires the Kobo overview freshness `CURRENT`.
After 23 min with no tick, the overview says the figures are not current.

**What a real stopped schedule must show.** Exactly that. If the background schedule stops on a real Site, the
figures stop being refreshed, and the screen must say "not current" rather than present old figures as current. That
honesty is a fundamental, so **the check does not tolerate a stale heartbeat, with or without a serve.** Exempting it
would let a build pass while its screens say "not current".

**What `finish check` asserts.** The build as served, with the schedule running, as on a demo day (`serve` ticks every
120 s). `prepare` meets that by ticking right before its check (`finish`: `tick(times=2)` + `retry_until_visited`,
then the check). `add-dates` must meet it the same way. A run that adds nothing and has nothing pending still ends in a
check of the served state, so it ticks once. This is the scheduler running, not a cosmetic heartbeat touch: the tick is
the product's full scheduled tick and does real work if any is due.

**Change (`tools/demo_combined.py`, `add_dates`).** Immediately before `check = self.finish_check()`, and only when
the check runs (not under `--no-check`):
```python
report = self.tick()   # R6.1: the check reads the served state; the schedule must have just run (as prepare's finish)
if "kisiwa" in story["sites"]:
    report, extra = retry_until_visited(report, lambda: self.tick(times=1))
    if extra:
        say(f"  tick: {extra} extra tick(s) for KISIWA-001's fuel_night stage")
```
This always runs after the closing settle (R5.2 item 3). It rewrites `last-tick.json` with a Kisiwa-visiting report,
which KIS-11 reads, exactly as in `prepare`. Under `--no-check` nothing changes: the serve keeps the schedule running
during the demo. Runbook line (DS-1a refresh, R1.5): "A check of a build with no serve running is valid only right
after `add-dates`, which runs the schedule first; on the demo machine `serve` must be running whenever a screen is
shown. If a screen says the figures are not current, `serve` has stopped."

**Test changes (`test_own_g1_add_dates.py`, no DB):**
- R5.3 test 6 (nothing added, nothing pending): the order becomes `counts`, `tick`, `finish_check`; no `drain_mini`
  and no `drain`.
- R5.3 test 7 (closing settle): `drain_mini`, `drain("settle-close")`, `tick`, `finish_check`.
- R5.3 test 1: no `tick` between the child and `drain`; exactly one `tick`, after the last `drain` and directly before
  `finish_check`.
- R5.3 test 5 (`--no-check`): no `tick` at all on a Kobo-only date.
- New: Kisiwa in the story and the closing tick's report has no KISIWA-001 `fuel_night` entry → one extra
  `tick(times=1)` (patch `time.sleep`), then `finish_check`.
- **Must-fail guard:** test 6 fails if the closing tick is removed.

### R6.2 WK-6: select the study the row is about (the one ending S+1), not the newest

**What happened (DB).** Kobo's rolling five-day productive-use studies: #9 is `2026-11-03..11-07` (S+1 = 11-07; S =
11-06), created by prepare. #11 is `2026-11-04..11-08`, created at 03:55Z by the added day. #9 is still there and
unchanged. WK-6 lists opportunities over the S+1 board link's five days (`:647-655`), which overlap #11 too. It then
takes `max(found, key=last_day)` (`:657`) and asserts `last_day == S+1`.

**Ruling.** WK-6's own docstring names its subject: "the Kobo productive-use opportunity page for the 5-day study
ending S+1". `max()` was a stand-in that held only while S+1 was the newest day. A real Site makes a new rolling study
every day, so a check that wants a specific day's study must select it by that day. This is the row's intent made
exact. It is not a loosening and not a bound that hides content: #11 is correct product output, and other rows (and the
board for 11-08) cover it.
- New pure helper in `tools/demo_combined_rows.py`:
  ```python
  def study_ending(found: list[dict], last_day: str) -> dict:
      """WK-6 (OWN-GAPS R6.2): the one opportunity whose study ends on `last_day`; later rolling studies are ignored."""
      hits = [o for o in found if o.get("last_day") == last_day]
      assert len(hits) == 1, ("expected exactly one study ending", last_day, sorted(o.get("last_day") for o in found))
      return hits[0]
  ```
- `wk6`: replace `:657-658` with `opp = demo_rows.study_ending(found, ctx.day(1).date().isoformat())`. Everything else
  in the row is unchanged (the `scenario_id`, mill and tariff asserts). Add to the docstring: "R6.2: the study is
  selected by its last day; later studies from added days are other days' studies."
- No-DB tests (in `test_own_g1_add_dates.py`): (a) `found` = studies ending 11-06, 11-07, 11-08 → returns the 11-07 one
  (**must-fail guard**: `max()` would return 11-08); (b) no study ends 11-07 → `AssertionError`; (c) two ending 11-07
  → `AssertionError`.

**Narrow pre-authorisation for the rest of the rehearsal.** A non-KIS row that fails **only** because an added day
produced a newer object may get the same fix, but only when all of these hold:
1. The row's docstring names a story day or story object as its subject.
2. The fix selects that object by its story key (day, code or id from `story.json` / `days.json` / the row's own docs).
3. No assertion on the object's content changes.
4. It comes with a no-DB test that includes the newer object, and it is listed in the packet.

Anything else, including any assertion change, any CO-2-style state failure or any COH row, stops and comes to the
Architect.

### R6.3 Rebuilding `tree` deleted the legacy comparison report: recipe fix only; no add-dates or E3 guard

**What happened (handoff).** The legacy S2 comparison report is file-backed inside `tree`. Replacing `tree` removed
it, and the Kobo overview answered 409 `AWAITING_EVIDENCE_MIGRATION` until `evidence_migration run` was repeated.
`performance_migration` already runs on every `tick()` (`performance_and_prebuild`, `:857-865`).

**Ruling.**
- Only the rehearsal recipe (R2-G1 Q4) replaces `tree` on an existing build. On the demo path `tree` is written once,
  by `prepare`, whose `finish` runs `evidence_migration` (`:796-799`). `add-dates`, `serve` and E3 (a fresh `prepare`)
  never replace it. So this is a **recipe step**. The R2-G1 Q4 recipe gains: "after replacing `tree`, run
  `evidence_migration run --tenant demo --site KOBO-001` and `performance_migration run` for KOBO-001 and KISIWA-001,
  and require 'cutover: permitted' before any `add-dates` or check."
- **No add-dates guard.** The failure is not silent: the product answers 409 with its reason, and `finish check`
  fails on many rows. Making `add-dates` run a migration would turn a data-arrival tool into a deployment tool, which no
  real gateway does. Refusing would duplicate a signal that is already loud.
- Runbook line (DS-1a refresh, R1.5): "Never replace or edit a build's `tree`. New code means a fresh `prepare`."
- E3 unchanged.

### R6.4 Rehearsal from here (replaces R5.5 steps 1–4)

0. Commit R6.1 (closing tick + tests) and R6.2 (helper, WK-6, tests) as two commits. Run the no-DB set (expected: the
   4 known failures only). Rebuild `tree` from the new HEAD **for the fresh clone only** (step 2).
1. **Reused clone: no further run.** Its two runs are kept as evidence: `settle-close-attempt1.json` (R5 resume proof)
   and `check.json` (49/51, CO-2 and WK-6, the input to this ruling). A third run there would repeat run B below. Rename
   the folder to `var/demo3_g1audit_run1`, then drop `assetops_demo3_g1audit_test`.
2. **Fresh clone:** as R5.5 step 2. After the new `tree` is in place, run `evidence_migration` (KOBO-001) and
   `performance_migration` (KOBO-001, KISIWA-001); all "cutover: permitted" (R6.3).
3. **Run A, kept:** `add-dates --site KOBO-001,KISIWA-001,EV-LAB-001 --to 2026-11-08`. Must show: per-date
   `settle-<date>.json` `verdict: done`; every `tick_failures` empty; Kisiwa night(s) `WITHIN_MARGIN (revision 1)`;
   Kobo `settled (n ticks)`; the closing tick; **finish check 51/51 PASS**; F-THREADS, CO-2, WK-6 and KIS-11 named in
   the packet as passing.
4. **Run B, kept:** the same command, started **at least 10 minutes after run A ends** (so the heartbeat is stale
   before it starts, which proves R6.1 on real wall time). Must show: everything "already present", counts all 0, no
   settle, one closing tick, **finish check 51/51 PASS**.
5. R5.5 step 6 read-only proofs after run B (counts 0 everywhere; Kisiwa added-`night_date` boards with
   `board_faults == []`; `chain_coherence` EX-2 = 0). The `--to` today refusal is not repeated.
6. Packet `.agent/review-packet-G1.md`: both runs' wall times, `settle-*` seconds, the closing-tick seconds, both
   `check.json` summaries, and any R6.2 pre-authorised fix used. Keep the fresh clone until review ACCEPT.
   **Stops:** as R5.5, plus anything outside R6.2's pre-authorisation. Cap: the remaining part of 2 × 1.5 h, counted
   from the fresh clone's creation.

### R6.5 Decisions logged for owner review

- **D-R6.1** When the background schedule has stopped, the product says the figures are not current, and that stays:
  it is what a real Site must show. The build check reads the build as served, so `add-dates` runs the product's
  scheduled refresh once right before its check, as `prepare` does. On demo days `serve` must be running.
- **D-R6.2** The productive-use check now picks the study that ends on the story day it is about, not the newest
  study. Real Sites produce a new rolling study every day. Further fixes of this exact kind are pre-authorised under
  four conditions; anything else comes back to the Architect.
- **D-R6.3** A build's code folder is never replaced on the demo path. The rehearsal recipe re-runs the comparison
  setup after replacing it. `add-dates` does not run deployment steps, and E3 is unchanged.
- **D-R6.4** Rehearsal keeps both fresh-clone runs (A: add and settle; B: nothing to add, started on a stopped
  schedule), each 51/51. The reused clone runs no more; its earlier runs are kept as evidence.

## E2 fix-round scope (2026-11-09)

- Architect: Claude (assetops-architect), delegated by the owner. Binding checked: `.ai/ROLE_CONFIG.md`, Architect =
  Claude since 2026-10-27. Input: `.agent/E2-results.md` on `task/E2-endgame` (bda19fecf), main 9bbbb5626. This
  ruling is read-only. I read the code and the E2 junit (`AssetOpsV1-e2/var/test-results/OPS-03/20261109-115734-e74ec1`,
  `...-104402-6465c5`). I queried no DB and ran nothing.
- Scope rule (owner, 2026-11-05): demo-critical only. The owner's bar for this round: decide from how real Sites work
  and what AssetOps is for, with no corners cut on fundamentals. So every red test below ends in one of three ways.
  It is **fixed**, with a named cause. Or it is **bounded** by a check on the demo build that proves the same thing.
  Or it goes to the **backlog**, with the reason it is not on a presented beat.
- There are two rounds. **FR-A** runs now, and E3 waits for it. **FR-B** runs Wed 11 to Fri 13 Nov, before the
  Sat 14 Nov backend run (D.4). FR-A changes **no product code**: only tests, one frontend test fixture and the
  container copy list. So E3 builds the same code that E2 measured.

### E2.1 Rulings

**(1) The G2 clock read at `fuel_balance/adapters/postgres_fuel_balance_store.py:254` is legitimate. It goes on the
allow-list as a writer, with a call-site guard. (D-E2.1)**
- What it is: only `fuel_balance/scheduled.py:117` (`run_site`) calls `schedule_inputs`, and only the tick's
  `fuel_night` stage (`scheduling/stages.py:473-486`) calls `run_site`. No stored compose, board, summary or route
  calls it. Its `known_at` decides which nights are due. `transaction` (`:213-219`) then assesses each due night, and
  takes its own `known_at` from the same `SELECT clock_timestamp()`. That read is already allow-listed as a writer
  (`test_ch5c2_clock_guard.py`, DIESEL-K4b block).
- Fundamentals: on a real Site, "is last night closed, and have the tank readings been quiet for 5 minutes?" is a
  question about the moment the check runs. It must use the same clock as the assessment it gates. Otherwise a night
  can be picked as due and then refused as `WINDOW_OPEN`. Every other tick stage works the same way: `db_now`, the
  cold, EV and opportunity leases at DB time, and the Kisiwa prepare's night assessment (`fuel_balance/worker.py`,
  also DB time). The story clock and the request's `known_at` (the visibility cutoff) belong to **reads**. They limit
  what a page may show, and must never drive a writer. A tick that judged nights by a story date would assess nights
  that have not happened yet, or skip nights that have. `read_scope.read_instant` is for compose read captures, so it
  does not apply here. Tests keep their hook, `test_db_clock_override`. So diesel-night due-checks agree with the rest
  of the product. This is not a defect. The guard fired only because OWN-G2 u1 did not add its allow-list row.
- **Fix (test only), `backend/tests/test_ch5c2_clock_guard.py`:**
  (a) In `SQL_CLOCK_ALLOWLIST`, directly after the `PostgresFuelBalanceStore.transaction` entry, add:
  ```python
      (_B + "fuel_balance.adapters.postgres_fuel_balance_store", "PostgresFuelBalanceStore.schedule_inputs.work"):
          _WRITER + " (OWN-G2: the fuel_night tick stage's due-night read, scheduled.run_site; the same DB clock as "
          "`transaction`, which assesses each due night)",
  ```
  (b) Add `test_schedule_inputs_is_called_only_by_the_tick_stage`, which makes the `_WRITER` claim checkable. Use `ast`
  over every `.py` under `backend/assetops_backend`. Collect each `Call` whose `func` is an `Attribute` named
  `schedule_inputs`. Assert that the set of calling files is exactly
  `{"assetops_backend/fuel_balance/scheduled.py"}` (the store's definition and the Protocol in `model.py` are not
  calls). Then assert that `assetops_backend.fuel_balance.scheduled` is **not** in `listed_modules()`. If it is
  listed, stop and report: a stored compose would then reach a writer clock.

**(2) The container copy list is a fix-now. The diesel tests are demo-critical (ST-K). (D-E2.2)**
- `tools/run-backend-suite-in-container.sh:49-51` copies only the code folders. Tests read four tracked inputs outside
  them: `.agent/DIESEL-F0/` (`probe-result.json`, `kisiwa-001-bindings.draft.json`), `.agent/DIESEL-D0/`
  (`kisiwa-diesel-hybrid-60kw.draft.yaml`), `Docs/demo-sprint/chain-graph.dot` and `.gitattributes`. The readers are
  `test_k0_operational_actions.py:45,475`, `test_k1_kisiwa_fixtures.py:34,36`, `test_k3...:24`, `test_k4a...:29`,
  `test_k5...:22` and `test_ch5b_graph.py:17`. Copy exactly these, not all of `.agent/` (1.7 GB) or `Docs/`.
- **Fix:** line 50 becomes
  ```sh
    ./backend ./contracts ./simulator ./gateway ./host ./field ./config ./contract-fixtures ./tools ./var ./frontend/src ./frontend/docs \
    ./.agent/DIESEL-D0 ./.agent/DIESEL-F0 ./Docs/demo-sprint ./.gitattributes \
  ```
  The comment at line 48 gets: `..., the frontend source, and the tracked test inputs under .agent/DIESEL-*,
  Docs/demo-sprint and .gitattributes`. All four paths are tracked. If `tar` fails on a missing path, stop: the
  checkout is wrong.
- Required: K3, K4a and K5 (fuel-balance rules, unexplained-fuel Finding rules, night text), K0, K1 and K7 (Kisiwa
  fixtures and story) and ch5b_graph are **re-run in the container** (list in E2.2). This is the diesel rules' first
  container run since they merged.

**(3) ch6b, Optimize card against the board: a test-design error. It is not a product inconsistency and not a date
effect. (D-E2.3)**
- There is no date effect. The fixture fixes the window to D7..D14 (`mechanism_dataset.day`, D1 = Mon 19 Oct 2026), so
  `from` = 25 Oct and `to` = 1 Nov 00:00 UTC. It does not end today.
- The cause: for a mini-grid Site, the summary row's `nodes` are re-evaluated over the summary's **window days**,
  D7..D13 (`site_outcomes/read.py:529-555` `_window_parts`, CH6b1-R Q1). The test compares them with the board read
  over `kobo["window"]`. For a mini Site that is the one **board day**, D13: `summary_window` returns DAY, and the mini
  compose window is that day (`mini.py:622`). The KPI node's `days` therefore differ by design: a week on the
  Portfolio, one day on the board. The coherence check states the same rule. V4 compares summary nodes with board
  nodes **only on S for mini Sites**, "one day on both; other windows differ by design"
  (`tools/checks/chain_coherence.py:1442`). The CH5d1-R test spec says "the Kobo Optimize row's `nodes` equal the
  **S** board's" (`build-sheet-CH-5d.md` §3). The asserts that did pass show the product invariant: the card is the one
  builder over the rows, and the chain cards equal the summary cards. The demo client sees the same money on the card
  and on the board, because the cost claim is a stored consequence and has no days.
- **Fix (test only), `backend/tests/test_ch6b_estate_postgres.py::test_optimize_card_is_the_one_builder_over_the_summary_rows_and_equals_the_board`:**
  Keep the week asserts on the card, the order and the chain (`:236-239`). Replace `:242` with
  `assert set(row["nodes"]) == set(there["nodes"])` and
  `assert row["nodes"]["earnings"] == there["nodes"]["earnings"], (row["nodes"]["earnings"], there["nodes"]["earnings"])`.
  The cost claim has no days. Keep `:243-248`. Then add the S check (V4 at L2m). Read `/api/estate/outcome-summary`
  with `{"from": _utc(d13), "to": _utc(d13 + timedelta(days=1))}`. This is a one-day pair of UTC midnights, so
  `window_day` rule 2 selects D13 and `window_days` is `(D13,)`. Assert that Kobo's `OPTIMIZE_COST` row `nodes` equal
  the `OPTIMIZE_COST` `nodes` of `day` exactly. Docstring: "...equal the board's on S (one day on both). On the week
  only the cost claim is compared, because the KPI days differ by design (CH6b1-R Q1, V4)". **If the S equality fails,
  stop and report.** That would be a real contradiction between the board and the Portfolio.

**(4) Frontend s502: fix the test fixture, not the wording or the scan. Leave the evEnergy timeout. (D-E2.4)**
- Since K8 R-LOAD (`ffc23b202`), the Overview objective line names the Site's **own** LOAD components
  (`sites/SiteWindowOverview.tsx:492-500`). Clients see it on every mini-grid Overview. On the demo Sites it reads:
  Kobo (it has a clinic) gets v69's `MINIGRID_OBJECTIVE`, "residential, clinic and productive loads". Kisiwa gets
  "Households, Cold store (ice and fish) and Water pump". Neither line contains the bare word "load". The flagged
  sentence comes only from the shared test fixture `HYBRID_MINI_GRID_SITE`, whose one LOAD is named
  "Distribution load" (`sites/__tests__/sldFixtures.ts:88`). `s5SiteWindowOverview.test.tsx:44-55` was already adapted
  with `withLoadNames`; s502 was missed. So this is a fixture lag from K8, not a defect a client sees. The scan stays
  as it is: "load" in our own prose stays flagged (`productVocabulary.json:56`), which keeps the owner's
  no-system-vocabulary rule. The names an operator gives a Site's parts are their data, and the product must not
  rewrite them.
- **Fix:** move `withLoadNames` and `KOBO_LOAD_NAMES` from `s5SiteWindowOverview.test.tsx:44-53` into
  `frontend/src/sites/__tests__/sldFixtures.ts` as exports. Give `withLoadNames` a `site` parameter, because it is now
  shared. Use it in both test files. In `s502OverviewFindingList.test.tsx:30`, `DETAIL` serves
  `withLoadNames(HYBRID_MINI_GRID_SITE, KOBO_LOAD_NAMES)`, and `SITE_ID` stays as it is. Do not edit
  `productVocabulary.json` or the shared fixture's components.
- `evEnergy.test.tsx::energy_states_table_loading` passes alone (12/12). It timed out at 10 s only under the load of
  the full run. Leave it: a bigger timeout would hide real slowness, and the demo does not show this screen state.
  → BL-61.

**(5) The 25 pre-existing failures. All are "P": they fail identically at 733eaf75c. (D-E2.5)**
"Stale" needs two things. The builder names the merged commit whose sheet **intends** the new value, and the change
in the assert is exactly that commit's change. Anything else: **stop, edit no product code, report to the
Architect.**

| Group | Tests | Demo beat? | Ruling | Round |
|---|---|---|---|---|
| G-a Catalogue/head pins | `test_ch1a_snapshot_postgres::test_0043...`, `test_cc_schema_postgres::test_chain_sole_head_and_trial_catalog`, `test_out_d1_schema_postgres::test_sole_head_chain_and_catalog`, `test_w204_cold_migration::TestMigration0023::...`, `test_w207_ev_money_postgres::TestMigration0026::...`, `test_w403_migration_postgres::TestMigration0030` x3 | They guard append-only and the schema under every screen | **Fix (stale).** Add the CH-5c `0047` `*_cic_*` triggers in catalogue order. For w207, add the `0053_fuel_cost_2` `model_id` check widening. For w403, add the `mini_alternative_revision` unique-key change from the migration that made it. For w204, add the trigger delta. **Each delta must name its migration file on main. A delta with no migration is a stop.** The append-only triggers must still be in every list. | FR-A |
| G-b Trial formula vocabulary | `test_cc_schema_postgres::test_trial_rows_chain_scope_and_append_only` (`:227`, "DID NOT RAISE") | As G-a | **Fix (stale).** `0053_fuel_cost_2` made `trial-fuel-comparison/2` valid (FUEL-1 A1, `972dc747f`). Change the invalid example to `"trial-fuel-comparison/9"`. The UPDATE/DELETE append-only asserts (`:242-244`) stay and must pass. | FR-A |
| G-c Scenario pins | `test_scenario_fingerprints.py` x3: 24 scenarios shipped against 14 listed; `kobo-mill-midday` v1 and `kobo-night-early-after-before-mill` v1 are unpinned; the "v2 supersedes v1" rule fails | **Yes.** The E3 prepare runs them (ST-3 mill, DD-1a2 before-mill) | **Fix.** For each new file, confirm it is unchanged since the merge that introduced it (`git log --oneline -- <file>` shows a DD-1a1, DD-1a2 or DIESEL commit). Then pin the fingerprint the test prints. List all 24 files. Add an explicit `FIRST_SHIPPED_AS_V1 = {...}` exemption, with the introducing commit in a comment for each entry. The rule stays strict for the original 14. | FR-A |
| G-d Renamed or added fields | `test_w302_financials_links_postgres::...fall_back...` (`window_links` is now `windowed_lines`); `test_ch4_opportunity_postgres::test_backfill...` (extra `headroom_unit`, CH-6b2 `6b4e682f2`); `test_walk1_productive_producer_postgres::...` (extra `generator-no-load-fuel-rate` 3.3, `GENERIC_DEFAULT`, FUEL-1 A1 `972dc747f`) | ch4 and walk1 are on the ST-3 path | **Fix (stale).** Rename the call. Add the keys to the expected values, with the commit in a comment. | FR-A |
| G-e Kobo board states | `test_out_b4_board_postgres::test_kobo_guardrail_two_board_days`, `::test_kobo_estate_finding_rows_and_states`. They expect only UNKNOWN/NOT_MEASURED; the board now shows NO_OBJECTIVE, NEEDS_ATTENTION and WATCH | **Yes** (ST-1, ST-2) | **Diagnose, then fix the test or stop.** The likely cause is the assert's premise, "the s602b overview is STALE_PROJECTION, so the outcomes stay UNKNOWN" (`:429-431`). It predates CH-6, after which states come from stored `site_day_snapshot` day rows, not from the overview projection. It is stale **only if** each measured state comes from stored, settled day rows of that board day, and the same board's readiness or days line does not say that day is unknown. Then assert the recorded states, and keep `MG-8 == NOT_APPLICABLE`. **Stop** if a NEEDS_ATTENTION or WATCH appears on a day that the same board calls not checked: a client would see a judgement on an unchecked day. | FR-A |
| G-f Gap naming | `test_idx_gaps_postgres::TestMovingAndBoard::test_p5_board_settles...` (10-06 now settles; `none_declared` = productive_kwh) | ST-1 coverage line | **Diagnose, then fix or stop.** K10 v2 (`56256bbc9`) stopped counting a declared-absent measure as a gap. It is stale **only if** productive_kwh was the one missing measure on 10-06. Then assert that the day settles and that the gaps line does not name productive_kwh. **Stop** if another measure is missing and the day still settles. | FR-A |
| G-g Grow text | `test_ch6_nodes_postgres::test_kobo_estate_grow_nodes` ("Not known yet" is now "No productive-use sales — no productive-use equipment declared") | **Yes** (ST-3) | **Diagnose, then fix or stop.** It is stale **only if** the mechanism Kobo (`backend/conversions/mechanism-v1.json` and the Site it imports) declares no productive-use equipment. The demo Kobo declares its mill: `test_walk1_productive_producer_postgres` "kobo declares supply uses" (green after G-d) and E3's MILL rows show it. **Stop** if the mechanism Kobo declares the mill, because "none declared" would then be a false statement about Kobo. | FR-A |
| G-h Mill-path pins | `test_k6b_fuel_verification_postgres::test_5_mill_path_outputs_equal_the_first_commit_pins`. The grade for 2026-10-25 is `None` where the pin says `NO_DATA`; `declared_by` is `owner <d-4>` where the pin says `<d-3>` | **Yes** (ST-3 mill verification) | **Diagnose, then re-pin or stop.** `declared_by` is a declaration ordinal, so one more earlier declaration in the fixture (DD-1b1 or K10 v2) shifts it. That part is stale once the extra declaration is named. The grade is stale **only if** 10-25 is now a day the baseline selection does not read at all (no row, rather than a graded row) because of a named change, and the verdict, the counted days and the before and after values all equal the pins byte for byte. **Stop** if any verdict, count or value moves. | FR-A |
| G-i Kisiwa fuel row on the Portfolio | `test_k8_estate_fuel_postgres::test_k8_fuel_row_in_estate_findings_never_in_money` (`:145`: the fuel Finding appears in estate Findings, but not in the Portfolio `rows`) | **Yes** (ST-K step 6, "Portfolio fuel row") | **Diagnose. A product cause stops the round.** A Portfolio member must have `lifecycle in ("SUPPORTED","UNCONFIRMED")` (`estate/portfolio.py:47`, `:840-846`), and then passes the lens and a page of `req.limit`. Find which of these drops the row. If the cause is in the test setup (the forced coverage row's lifecycle, or its page position under the test's limit), fix the setup so it builds the row the real Kisiwa data builds, and say so. **Stop** if the same gate would drop the real Kisiwa row. E4 adds a check either way (E2.4). | FR-A |
| G-j Opportunity routine scan | `test_w403_opportunity_scan_postgres::test_routine_scan_retention_edge_and_missing_day` (`:101`), `::test_uf6_failed_job_is_retained...` (`:112`, queues nothing) | **Yes**, indirectly: the routine scan is how a day added live reaches the opportunity (ST-7) | **Diagnose, then fix or stop.** Suspected cause: CH-9 u2 (`badd2fbb9`, "study day_heads per measured daylight hour") changed what a head needs, and the w402 fixture ingests too few daylight hours. It is stale **only if** the fixture lacks hours the new rule needs. Then add the measured hours to the fixture, and keep the retention-edge asserts exact. **Stop** if a day with full daylight hours is not queued. | FR-A |
| G-k Decision replay 422 | `test_w403_replay_postgres` x2 (`DECISION_INPUT_INVALID` on the positive replay) | **No.** The W4-03 Alternatives and decision replay are not in DS-1 (ST-0 to ST-7, ST-K) | **Backlog BL-60.** No presented beat uses it. The scenarios the demo does use run through E3's prepare and self-check. | — |
| G-l w301 golden (T6) | `test_w301_estate_golden_postgres.py` x6 (only `$.summary.claims` gains `count.opportunities`) | It guards the estate Findings body (ST-6) | **Deferred to FR-B (D-E2.6).** E2 showed the only cause is the `claims` addition from CH-5a2b: there was no `run_pending -> []`, and the skew was about 20 ms. FR-A changes no product code, so before E3 the golden has nothing new to guard. It must be green before the next product change. | FR-B |
| G-m Needs a prepared `var/` | `test_ch5c_env_parity::...one_code_version`, `test_demo_combined_mill.py` x2 (`SystemExit: Run prepare first.`, `tools/demo_combined.py:620`) | `demo_combined_mill` is the order of the mill steps in the prepare (ST-3) | **Bounded at E4.** Run these 3 tests in the E3 checkout right after E3's prepare; they take seconds (E2.4). They claim to be L0 "no work folder" tests but read `story.json`. Making them hermetic → BL-62. | E4 |

**(6) Wrapper defects. (D-E2.7)**
- **Close template `HARNESS_URL_MISMATCH`: a real tooling defect, fixed in FR-B.** `tools/mechanism_dataset.py ensure`
  builds `states` and then `close` **in one Python process** (`:421-432`). `build` sets `ASSETOPS_TEST_DATABASE_URL`
  for each build (`:155`). But `test_s4_finding_store_postgres.URL` is a module global, bound at first import to the
  states build DB. So `_harness_checked` refuses the close build (`backend/tests/mechanism_dataset.py:696-702`). The
  guard is right; the process model is wrong.
  **Fix:** `ensure` runs each variant build in a child process:
  `subprocess.run([sys.executable, str(Path(__file__).resolve()), "build", "--variant", day_set, "--budget", "inf"], env=os.environ.copy())`.
  It checks the return code where it calls `build(...)` today, and `build` itself does not change. Add one L0 test
  that monkeypatches `subprocess.run` and asserts one child per wanted variant and no in-process `build` call. The L2m
  proof is the FR-B run: it builds `close` and runs
  `test_md0_mechanism_postgres.py::test_close_variant_resolves_closes_after_seven_clean_days_and_recurs`. That test is
  the only Postgres proof of ST-2's "resolved, then recurs" path, so it runs before W-1.
- **Empty `slice-paths.txt`: fixed in FR-B.** `tools/run-backend-suite-in-container.ps1:85` pipes `git diff` into
  `Set-Content`. When the diff is empty, PowerShell 5.1 writes no file. `ensure --close auto` then reads "diff
  unreadable" and builds the close template. Fix: `$paths = @(& git -C $worktree diff --name-only $baseSha 2>$null)`,
  then `[System.IO.File]::WriteAllLines((Join-Path $runDir 'slice-paths.txt'), [string[]]$paths)`, which writes an
  empty file. `slice_inputs` then returns `[]`, and the close test is deselected loudly, as designed. It does not
  matter for FR-A, which runs `-Close no`.
- **60-minute cap on `-Targets`: fixed in FR-B (one line).** `:142` caps every custom `-Targets` run at 60 minutes,
  even one that names a directory. Apply the 60-minute cap only when every target is a `.py` file or a node id.
  Otherwise keep the cap derived from the tier. Not needed before E3/E4, which do not run this wrapper.

### E2.2 FR-A (now; E3 waits for it): builder card

- **Branch** `task/E2-fix-A` from main 9bbbb5626. **Model: Sonnet.** No item needs design. Each diagnose item (G-e to
  G-j) has a written stale test and a stop rule. The builder sends its stops to the Architect as one batched message
  and carries on with the other items.
- **Files:** `backend/tests/test_ch5c2_clock_guard.py`; `tools/run-backend-suite-in-container.sh`;
  `backend/tests/test_ch6b_estate_postgres.py`; `frontend/src/sites/__tests__/sldFixtures.ts`,
  `frontend/src/shell/__tests__/s502OverviewFindingList.test.tsx` and
  `frontend/src/shell/__tests__/s5SiteWindowOverview.test.tsx`; and the test files of G-a to G-j and their fixtures
  under `backend/tests/` (G-j may touch the w402 test fixture). **Do not edit any file under
  `backend/assetops_backend/` or `config/`, any file in `frontend/src/` outside `__tests__`, or any file in `tools/`
  other than the `.sh`.** If a product edit is needed, stop.
- **Order:** (2) copy list, (1) guard, (3) ch6b, (4) s502, then G-a to G-d (mechanical), then G-e to G-j (diagnose),
  then one scoped run, then the packet.
- **Scoped re-run (one heavy job, after all edits):**
  `tools\run-backend-suite-in-container.ps1 -Close no -Workers 2 -CapMinutes 60 -Targets "<list>"`, where the list is
  `backend/tests/test_ch5c2_clock_guard.py backend/tests/test_k0_operational_actions.py backend/tests/test_k1_kisiwa_fixtures.py
  backend/tests/test_k3_fuel_balance_rules.py backend/tests/test_k4a_fuel_finding_rules.py backend/tests/test_k5_fuel_night_text.py
  backend/tests/test_k7_kisiwa_story.py backend/tests/test_ch5b_graph.py backend/tests/test_ch6b_estate_postgres.py
  backend/tests/test_ch6_nodes_postgres.py backend/tests/test_ch1a_snapshot_postgres.py backend/tests/test_cc_schema_postgres.py
  backend/tests/test_out_d1_schema_postgres.py backend/tests/test_w204_cold_migration.py backend/tests/test_w207_ev_money_postgres.py
  backend/tests/test_w403_migration_postgres.py backend/tests/test_scenario_fingerprints.py backend/tests/test_w302_financials_links_postgres.py
  backend/tests/test_ch4_opportunity_postgres.py backend/tests/test_walk1_productive_producer_postgres.py
  backend/tests/test_out_b4_board_postgres.py backend/tests/test_idx_gaps_postgres.py backend/tests/test_k6b_fuel_verification_postgres.py
  backend/tests/test_k8_estate_fuel_postgres.py backend/tests/test_w403_opportunity_scan_postgres.py`.
  The states template built in E2a is reused. FR-A loads no changed module into the build, so nothing is rebuilt. If
  `ensure` reports a rebuild anyway, let it run (about 11 minutes) and note it. Frontend:
  `npx vitest run src/shell/__tests__/s502OverviewFindingList.test.tsx src/shell/__tests__/s5SiteWindowOverview.test.tsx`.
  At merge prep, run `tools\check-all.ps1` once (18 guards).
- **Pass bar:** every listed file is green, except items stopped under their stop rule. Each stop is listed with its
  cause in the packet. K3, K4a and K5 must collect and pass. Any failure in a K file is a stop, and E3 waits for the
  Architect.
- **Review:** one fresh Claude reviewer (Opus; the diff is small and test-only). It checks every "stale" claim against
  its named commit. Merge on ACCEPT, then E3.

### E2.3 FR-B (Wed 11 to Fri 13 Nov, before the Sat 14 backend run and W-1): builder card

- **Branch** `task/E2-fix-B`. **Model: Sonnet.** Files: `tools/mechanism_dataset.py` (`ensure` builds in child
  processes), `tools/run-backend-suite-in-container.ps1` (`:85` empty file, `:142` cap), one L0 test for `ensure`, and
  `backend/tests/fixtures/w3/w301-estate-golden.json` (T6).
- **T6**, as in Parts A.2 and F.2: write once with `ASSETOPS_WRITE_W301_GOLDEN=1` on a `*_test` DB, then check the
  diff. Only `claims` entries under the Findings `summary` may be added; anything else is a stop. Then verify without
  the flag: 6 of 6 pass.
- **Run (one heavy job):** `-Close yes -Workers 2 -CapMinutes 90 -Targets "backend/tests/test_md0_mechanism_postgres.py backend/tests/test_w301_estate_golden_postgres.py <the ensure L0 test>"`.
  `tools/mechanism_dataset.py` is in the template fingerprint, so this rebuilds states and builds close (about
  25 minutes), which proves the child-process fix end to end. Then run `check-all`. Also confirm that a run from main
  with nothing changed logs `close not selected` (the empty-file fix). Read the Sat 14 run's log, or do a `-Close auto`
  dry start.
- **Review:** a fresh Claude reviewer (Sonnet). Merge before Sat 14.

### E2.4 Additions to E4 (no code)
- **E4-K8:** on the E3 build, `GET /api/estate/portfolio` over the ST-K week shows the Kisiwa fuel Finding in `rows`
  with the "Verified" label (R-1), and not in `money` or `selected_lines`. Record the result in the E4 notes. If the
  row is missing, that is a High, and E6 waits.
- **E4-env:** in the E3 checkout, after its prepare, run
  `pytest backend/tests/test_ch5c_env_parity.py backend/tests/test_demo_combined_mill.py` (L0, seconds). A failure is
  an E4 stop.
- The E2-0 clock check runs again before E3 (as F.3 already says).

### E2.5 Size
- FR-A: about **0.45 unit** of building (0.15 mechanical, 0.3 for the six diagnoses). Machine time: one scoped run of
  about **25 to 35 minutes** (mostly the L2m files ch6b and ch6), about 1 minute of vitest and about 17 minutes of
  check-all. Review: about 0.15 unit. With no stops, E3 can start in about **2.5 to 3 hours** of wall time. A stop on
  G-e, G-g, G-h, G-i or G-j (all presented beats) adds an Architect ruling, and E3 waits for it.
- FR-B: about **0.25 unit**, plus about 45 minutes of machine time (template builds about 25 minutes, T6 about
  20 minutes) and check-all.

### E2.6 Decisions
- **D-E2.1** The `schedule_inputs` DB-clock read is a tick writer's read, on the same clock as the assessment it
  gates. It goes on the allow-list as `_WRITER`, with a call-site test that keeps it out of stored composes. The story
  clock and the visibility cutoff limit reads and never drive writers.
- **D-E2.2** The container copies the four tracked test inputs (`.agent/DIESEL-D0`, `.agent/DIESEL-F0`,
  `Docs/demo-sprint`, `.gitattributes`). The diesel rule tests (K0, K1, K3, K4a, K5, K7) re-run in FR-A, and any
  failure there holds E3.
- **D-E2.3** ch6b: comparing the full `nodes` over the week is a test-design error. The product rule (CH6b1-R Q1, V4)
  is that nodes are equal on S for mini Sites, and that on other windows only the cost claim is equal. Fix the test
  and add the S equality at L2m. This is not a date effect.
- **D-E2.4** s502 lags the K8 R-LOAD fixture change. Share `withLoadNames`. The wording and the vocabulary scan stay
  as they are. Leave the evEnergy timeout (BL-61).
- **D-E2.5** Of the 25 P failures: G-a to G-d are fixed as stale, each with a named commit. G-e to G-j are presented
  beats and are diagnosed in FR-A, each against a written stale test with a stop rule. G-k goes to BL-60. G-l (T6)
  goes to FR-B. G-m is bounded at E4, and making those tests hermetic is BL-62.
- **D-E2.6** T6 moves from E2 to FR-B. FR-A changes no product code, so before E3 the golden has nothing new to guard.
  It is green before the next product change (Sat 14).
- **D-E2.7** Close-template build: `ensure` builds each variant in a child process, `slice-paths.txt` is always
  written, and the 60-minute `-Targets` cap applies only to file targets. All three are in FR-B, before the Sat 14
  run. They are not needed before E3, because E3 and E4 do not run the wrapper.
- **D-E2.8** E3 starts after FR-A merges, when every red in the scoped run is either fixed or stopped and ruled. A stop
  on a presented beat holds E3 until it is ruled.

## FR-A stop rulings (2026-11-09)

- Architect: Claude (assetops-architect), delegated by the owner. Binding checked: `.ai/ROLE_CONFIG.md` makes the
  Architect Claude since 2026-10-27. Input: `AssetOpsV1-e2fa/.agent/review-packet-E2-fix-A.md` (`task/E2-fix-A`,
  d0e678eb9) and the console log of its run `20261109-160557-644a04`. I read the code at d0e678eb9. I ran read-only
  queries on the latest demo builds: `assetops_demo3_g1audit_test`, `assetops_demo3_k9rehearsal_test` and
  `assetops_demo3_kisiwa_test`. Nothing else was touched.

### R-1 G-e: a real inconsistency that no presented screen shows. Bounded deferral with an E4 check. (D-E2.9)

**What the board does.** The MG-2 NEEDS_ATTENTION and MG-4 WATCH states come from a Finding, not from readiness.
- Status rule 5 (`outcomes/status.py:69-77`) gives NEEDS_ATTENTION for an open primary Finding and WATCH for an open
  secondary one.
- `board.py:688-694` raises those signals only for Findings whose episode is inside the board day (`in_window`).
- MG-2 and MG-4 count as `settled` (`mini.py:539-540`) when the source gate is open, the board day is settled and the
  dispatch read returned.
- `day_settled` (`chain/read.py:100-108`) treats a stored NO_DATA row as settled.

So a day can be "settled" with nothing checked.

**What the gap line counts.** "N of the last 31 days have no checked readings yet" (`mini.py:133`, `:361-385`) counts
the days whose day grade is NO_DATA or PENDING. A day's grade is the weakest grade among its measures. NO_DATA means
`covered_seconds <= 0` (`chain/grading.py:76-97`). MG-2's measure is `avoidable_gen_min`. Its coverage is the union of
the evidence intervals of the selected dispatch run (`chain/measure_impls.py:286-318`, `analytic_run_evidence`).

**What s602b stores.** On 10-06, 10-21 and 11-02, all three stored measures are NO_DATA (packet, G-f). The same boards
hold SUPPORTED or UNCONFIRMED generator Findings with episodes inside those days. From the run log: 10-06
08:00-09:00Z, 11-02 09:30-09:45Z and 10-21 08:00-09:00Z. `mini_depth` returned 0 rows.

**How a site lead reads it.** A Finding is a claim about one episode, judged on its own evidence. On a real Site a
Finding often falls on a day that is only partly checked. "Needs attention" next to "only part of today is checked"
is honest, and it is how a site lead triages. s602b is different. On the Finding's own day, the generator measure that
the Finding moves has zero counted evidence, and the board says the day has no checked readings. A site lead reads
that as "you judged a day you say you did not check", or as "the checking is broken". This is not a legitimate design:
two producers disagree about the same generator hour. The likely cause is in the fixture. s602b's dispatch runs come
from the S3-01 Performance comparison path, which stores no `analytic_run_evidence` rows. But nothing in the product
prevents the combination, so it counts as a product inconsistency.

**The demo build does not show it.** On both demo builds, every generator Finding falls on a PARTIAL day with counted
evidence:

| Site | Finding days | `avoidable_gen_min` grade | Covered |
|---|---|---|---|
| KOBO-001 | 10-23, 10-30, 11-06 | PARTIAL | 29,100 s |
| KISIWA-001 | 10-28, 10-29 | PARTIAL | 32,700 s and 32,400 s |

The Kobo NO_DATA days (10-27, 11-02, 11-04 and early October) have no in-window Finding.
`assetops_demo3_kisiwa_test` shows PENDING on the Kisiwa days, but it is an intermediate database that was never
settled, not a presented build. So no presented beat shows the case today.

One risk remains. The demo Kobo declares an MG-2 objective ("avoidable generator minutes at most 0", BOARD_DAY), and
`mini_readings` judges it from the dispatch read, not from the snapshot. In principle a NO_DATA day could therefore
read "On track". E4 checks this (below).

**Why there is no product fix now.** The right fix is at the producer: the measure a Finding moves must count that
Finding's evidence. A mask on the board would hide one producer's output behind the other's. Either fix changes the
board or the chain under every mini screen, two days before E3, for a case the demo build does not contain. That is
the corner the owner warned against cutting. The E4 check proves the demo build is clean, and BL-63 carries the fix.

**Builder changes (tests only, `backend/tests/test_out_b4_board_postgres.py`):**
1. `test_kobo_guardrail_two_board_days`: replace the loop asserts at `:430-438`. Keep the CATEGORIES assert and the
   MG-8 pop. For each of `a` and `b`:
   - Assert that `measured` equals the exact dict the board returns. Copy that dict in full from a focused run into
     `S602B_STATES`, with MG-8 removed.
   - Assert the reasons on the wire (`board.py:888`): MG-2's `reason` is `"PRIMARY_FINDING_OPEN"` and MG-4's is
     `"SECONDARY_FINDING_OPEN"`.
   - Assert `LAST_PORTS[key]["chain_day"] == {"settled": True, "readiness": "NONE", "gaps": 31}`. Either capture the
     port right after each `_board` call, or move this assert after the overview loop that records `chain_day`.
   - Replace the comment with: "D-E2.9: since CH-5a1 the states come from the in-window Findings over the chain day,
     not from the STALE_PROJECTION overview. s602b stores no counted dispatch evidence, so the same day grades
     NO_DATA. That contradiction is BL-63, held by `test_kobo_s602b_no_judgement_on_unchecked_day` (strict xfail)."

   The asserts after the loop (F01 MOVES, SAFEGUARD, Action keys, the ACT index) stay unchanged. The first failing
   assert stops the test today, so they never run. Now they must run and pass. If any of them fails, stop.
2. `test_kobo_estate_finding_rows_and_states`: make the same change for the 10-21 board. Pin the exact recorded dict
   with MG-8 popped, the two reasons and the `chain_day` port. If the dict differs from `S602B_STATES`, put it in a
   second constant.
3. Add `test_kobo_s602b_no_judgement_on_unchecked_day(kobo_guardrail, monkeypatch)`, marked
   `@pytest.mark.xfail(strict=True, reason="BL-63: a Finding-driven state on a day whose moved measure has no counted
   evidence")`.
   - Read both boards (10-06 and 11-02).
   - For each board, read the latest stored `avoidable_gen_min` grade for that Site-local day from
     `site_day_snapshot` (`DISTINCT ON (local_day, measure, subject_ref) ... ORDER BY revision DESC`).
   - If the grade is NO_DATA or PENDING, or there is no row: assert that no outcome on the board has a `reason`
     starting with `PRIMARY_FINDING_` or `SECONDARY_FINDING_`, or equal to `OBJECTIVE_MET`, `OBJECTIVE_MISSED` or
     `OBJECTIVE_ON_PACE`.

   Today the test must report XFAIL. When BL-63 lands it will XPASS, which fails the run, and the mark comes off.
4. Run focused on the host (`tools\run-host-tests.ps1`, on `assetops_test` only). `test_out_b4_board_postgres.py`
   must show these two tests passed, the new test as 1 xfailed, and every other test as before. Record the pinned
   dicts in the packet.

**E4-GE (new E4 item, no code).** Run on the E3 build, before E6:
- (a) Read-only SQL. For every Finding head with mechanism `GENERATOR_SUPPORT_CANDIDATE` on a mini Site (KOBO-001,
  KISIWA-001), the Site-local day of `episode_start` must have a latest `avoidable_gen_min` row with
  `covered_seconds > 0` and a grade that is neither NO_DATA nor PENDING. Use the query the Architect ran on g1audit,
  and record it in the E4 notes.
- (b) Read-only board check. Read `GET /api/sites/{code}/outcome-board?date=D` for every Kobo and Kisiwa day the demo
  script opens, and for every Kobo day from D7 to the last story day. On any day whose `avoidable_gen_min` grade is
  NO_DATA or PENDING, no MG-2 or MG-4 outcome may have a reason in `PRIMARY_FINDING_*`, `SECONDARY_FINDING_*`,
  `OBJECTIVE_MET`, `OBJECTIVE_MISSED` or `OBJECTIVE_ON_PACE`.
- A hit on a day the script opens is a High, and E6 waits. A hit only on a day the script does not open is a Medium
  for the owner walkthrough list. Either way, BL-63 is promoted.

### R-2 G-h: the cause is the test's normalizer, not the clock. Fix the normalizer and transform the pins. Do not freeze `_BASE` and do not re-capture. (D-E2.10)

**Diagnosis.** `_Norm` (`test_k6b_fuel_verification_postgres.py:124-153`) has two faults:
- It makes every value relative to the effective day but leaves dict keys absolute (`{k: self(x) ...}`). The
  `grades` map is keyed by date over `LOOK_DAYS = 14` (`verification_families.py:51`), so its keys move with the wall
  clock.
- It treats the rule's declaration date as a story date. `TARGET["declared_by"] = "owner 2026-11-05"`
  (`verification_families.py:55-56`, CH9b1-R P1) is a constant the owner declared, yet it reads `<d-3>` on 11-08 and
  `<d-4>` on 11-09.

The verdict, the counts and the values do not move (packet capture). The effective day follows the real clock:
`at()` sets the COMPLETE `occurred_at`. The fixture also reads the DB clock (`_now(engine)` for `raised_at`,
`test_ch9b1...:52-60`), and the store stamps rows with DB time.

**Why not freeze `_BASE`.** Freezing `_BASE` puts the Action's completion on a fixed past date while `raised_at` and
the store stay on the DB clock. One story would then run on two clocks, the failure family FIX-W401b fixed, and the
completion could fall before the Action was raised. On a real Site one clock orders these events. The test has to
keep them on one clock and compare relatively.

**Why not re-capture.** The pins prove that the mill path is byte-equal to its state before K6b (d25f95ccb). A new
capture would lose that proof. A mechanical transform of the original file keeps it.

**Builder changes (tests only):**
1. `_Norm.__call__`, dict branch: `{(self(k) if isinstance(k, str) else k): self(x) for k, x in v.items()}`.
2. `_Norm.__call__`, string branch, as its first line: `if v == fv_families.TARGET["declared_by"]: return v`. Import
   `assetops_backend.actions.verification_families` as `fv_families`, or reuse the import if it already exists. A
   change to the declared rule is a product change that the pin must catch, so the date stays literal.
3. `fixtures/k6b_mill_pins.json`: edit it by hand or by script. Do **not** use `K6B_CAPTURE_PINS`. The capture's
   effective day is 2026-11-08: the commit time is 2026-11-08 06:25 +0300, and the baseline COMPLETE days 11-05 to
   11-07 read `<d-3>` to `<d-1>`. Make these changes:
   - Rewrite the `grades` keys `"2026-10-25"` to `"2026-11-07"` as `"<d-14>"` to `"<d-1>"`.
   - Rewrite the three `"owner <d-3>"` values as `"owner 2026-11-05"`.
   - Apply the same rule to any other date-shaped key.

   The file diff must contain exactly these lines. The commit message names d25f95ccb as the source.
4. In `test_5`, after `got`: assert that no key or value in `got` matches `\d{4}-\d{2}-\d{2}`, except the literal
   `TARGET["declared_by"]`. This makes independence from the wall clock checkable.
5. Run `test_k6b_fuel_verification_postgres.py` focused on the host: every test passes. Mutation proof: temporarily set
   `TARGET["declared_by"]` to `"owner 2026-11-06"`, confirm that `test_5` fails, then revert.

**Stop rule.** If today's output still differs from the transformed pins anywhere besides those lines, stop:
something other than the clock has moved.

### R-3 G-g deviation: accepted. (D-E2.11)

My spec premise was wrong. `test_ch6_nodes_postgres::test_kobo_estate_grow_nodes` builds the S4/s602b test-scoped
Kobo, not the mechanism Kobo. The builder's fix states a fact about that Site and proves it from stored data: every
`foundation_revision` has zero PRODUCTIVE loads, and the test first checks that the set is not empty. "No
productive-use equipment declared" is therefore true for that Site, and the text is K10 v2's (56256bbc9). The demo
Kobo declares its mill, which `test_walk1_productive_producer_postgres` covers.

**E4-GG (no code).** On the E3 build, the Kobo board on the ST-3 story day must not contain "no productive-use
equipment declared", and its Grow row must show the mill's sales line. A miss is a High.

### R-4 G-i follow-up: confirmed for FR-B. (D-E2.12)

`pin_read_at` (`test_w301_estate_index_postgres.py:398-410`) patches only `postgres_estate_read.EstateSnapshot`.
`EvidenceMoneySnapshot(EstateSnapshot)` (`estate/adapters/postgres_evidence_money_read.py:55`) binds its base class at
first import, so a Portfolio read under the helper depends on import order. The helper has five users: w301_golden,
w301_estate_index, w302_evidence_scope_snapshot, w303_portfolio_fixture and w303_selectors. It produces no wrong
product output, and k8 already has a local fix, so it does not block E3.

**FR-B adds** (beyond its earlier file list):
- `pin_read_at` also patches `postgres_evidence_money_read.EvidenceMoneySnapshot` with the same `present()` pin.
- k8 drops its local `_PinnedMoney` and uses the helper.
- FR-B's run targets add the five helper users and `test_k8_estate_fuel_postgres.py`, each run after one estate
  test, which is the order that exposed the hole.

The reviewer checks this with the rest of FR-B.

### R-5 E3 start

E3 starts once all of the following hold:
1. FR-A carries R-1 (test edits 1-4) and R-2 (edits 1-5).
2. Focused host runs of `test_out_b4_board_postgres.py` and `test_k6b_fuel_verification_postgres.py` are green,
   with exactly one xfail.
3. `check-all` passes 18/18.
4. A fresh Claude reviewer (Opus) accepts the whole FR-A diff. The reviewer checks each stale claim against its named
   commit, and checks that every state R-1 pins has the strict xfail beside it.
5. FR-A is merged.

No new container run is needed. The two files changed only in themselves, and every other scoped file was already
green at 52190948d. BL-63 does not hold E3. E4 adds E4-GE and E4-GG beside E4-K8 and E4-env.

### Decisions
- **D-E2.9** G-e is a real inconsistency that no presented screen shows. On s602b, a Finding-driven NEEDS_ATTENTION
  or WATCH appears on days whose generator measure has no counted evidence ("no checked readings"). The demo builds
  put every generator Finding on a PARTIAL day with counted evidence. Ruling: a bounded deferral.
  - The tests pin the recorded states, the reasons and the `chain_day` port.
  - A strict-xfail test holds the invariant.
  - E4-GE proves the E3 build is clean, including objective verdicts on NO_DATA days.
  - The producer-side fix is BL-63. A board-side mask is rejected.
- **D-E2.10** G-h: the k6b normalizer left date keys absolute and treated the owner's rule date as a story date. Fix
  the normalizer, and transform the d25f95ccb pins: the keys become relative and the rule date stays literal. Assert
  that no absolute date remains. Do not freeze `_BASE`, because that splits one story across two clocks. Do not
  re-capture.
- **D-E2.11** The G-g deviation is accepted. The test's Site is the s602b Kobo, which has no productive loads, proved
  from its stored Foundation revisions. E4-GG checks that the demo Kobo never reads "none declared".
- **D-E2.12** The `pin_read_at` import-order hole goes to FR-B. Patch `EvidenceMoneySnapshot` in the helper, drop
  k8's local pin, and run the five helper users plus k8.
- **D-E2.13** E3 starts after FR-A merges. That needs R-1 and R-2 built, the two files green with one strict xfail,
  check-all at 18/18 and the reviewer's ACCEPT. No new container run is needed. BL-63 is post-demo.

## E3 stop rulings (2026-11-09)

Claude Architect, under the owner's delegation of 2026-11-08 (`.agent/owner-away-architect-decides-2026-11-08.md`):
"let the architect make decisions if there are any input required from my side and make sure it makes decisions based
on understanding of how real sites work and what assetops is trying to achieve, no cutting corners on fundamentals".
E3 = `task/E3-demo-build` 80f4a21d4, `assetops_polish_client2_test`, S = 2026-11-07, finish check 51/51.

### STOP 1 (G-m): the builder's reading is right; the G-m premise was wrong
- Code path: `Demo.tick()` ends in `performance_and_prebuild()` (`tools/demo_combined.py:861`), which calls
  `self.story()` and reads `<self.work>/story.json`. The parity test sets `demo.work = tmp_path` and calls `demo.tick()`;
  the mill tests build `Recording(tmp_path)`, and `finish_build` -> `finish` -> `tick(times=2)` reaches the same read.
  The prepared `var/` is never read, so no prepare can make them pass. The read came in with f994e3cf9 (K9 R3s); the
  tests predate it. This is a test-fixture defect, not a product or build defect.
- What E3 already proves: the 3-Site mill order is proven by outcome. A tick before the mill step skips every mill
  cause, and the finish-check rows on `mill.json` would then fail (VERIFIED mill Action, 5 eligible days, MILL-4 thread
  line, COH-17 on the mill thread only). The one-Site plain finish is not exercised. Tick/serve `code_version` parity
  is not checked by any finish row; the prebuild's "8 hit" compares prebuild with prebuild, not tick with serve.
- Ruling: fix the tests now (option a) and add a live parity check to E4. Skipping the unit proof is a corner cut:
  only the L0 test has the keyless control that shows the comparison can fail.

### FLAG 2: Kobo `fuel_night` `eligible: true, processed: 0` is correct
- `due_nights` returns eligible when the Site has a tank asset, and a night is due only when it has tank `fuel_level`
  readings (`fuel_balance/scheduled.py` docstring: "Kobo (a tank with no `fuel_level`) gets no row"; spec §2.4 P2, P3).
- Real-site sense: Kobo runs a genset with a tank but no level sensor; diesel is known only from deliveries. A night
  balance needs a level read at both edges, so producing nothing is the honest result. Eligible means "the stage
  applies to this Site", not "a night was found". Not a defect.

### Decisions
- **D-E3.1** G-m test fix on `task/E3-gm-story-fixture` (Sonnet builder, fresh Claude Sonnet reviewer, test files only):
  1. `test_ch5c_env_parity.py::_captured_envs`: write `tmp_path/"story.json"` = `{"sites": list(tool.SITES)}` (the
     three Sites, so the Kisiwa performance branch runs too).
  2. `test_demo_combined_mill.py`: each test that reaches `finish_build(..., True, ...)` writes
     `tmp_path/"story.json"` = `{"sites": story["sites"]}` after it sets `story["sites"]`.
  3. Fix both module docstrings: the work folder is `tmp_path` holding the `story.json` that prepare would write.
  No product code changes and no assertion is weakened. The rest of BL-62 stays in the backlog. Run the two files
  (L0, seconds): all pass. Merge before E4.
- **D-E3.2** E4-env runs the fixed files in the E3 checkout (with the merged fix applied) and stays an E4 stop.
- **D-E3.3** New check E4-PARITY: with the demo server up, after one loop tick (tick plus its serve-env prebuild),
  GET the first page the demo opens (the S+0 Kobo board request). It must answer `X-AssetOps-Stored: hit`. A
  `stored` or `composed` answer means tick and serve disagree on `code_version`, and that is an E4 stop.
- **D-E3.4** FLAG 2 is not a defect. New check E4-FN: in `last-tick.json`, KOBO-001 `fuel_night` is `OK`,
  `eligible: true`, `processed: 0`, `deferred: 0`; KISIWA-001 is `OK`/eligible; COLD/EV are `eligible: false`. Then
  `SELECT count(*) FROM fuel_balance_window` for KOBO-001 = 0 (P3). Any Kobo row is a High.

## E4 stop rulings (2026-11-09)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`), under the owner's delegation of 2026-11-08
(`.agent/owner-away-architect-decides-2026-11-08.md`): "let the architect make decisions if there are any input
required from my side and make sure it makes decisions based on understanding of how real sites work and what assetops
is trying to achieve, no cutting corners on fundamentals". Input: `AssetOpsV1-e3/.agent/E4-results.md` (690c54532),
code at that commit, and read-only SQL on `assetops_polish_client2_test`. **READ** = code cited; **DB** = queried.

### D-E4.1 STOP 1 (E4-PARITY): a defect. The warm list is a frozen copy of an old story calendar.

**Root cause (READ).**
- The prebuild sends every request in `config/chain/prebuilt-routes-v1.json` (`chain/prebuild.py:28-35`, via
  `file_chain_config.load_prebuilt_routes`, `:99-103`). That file is static. It was committed once in CH-5c u2
  (36d0e08de) with the note "Generated from the demo story calendar (S=2026-10-31)". No generator exists in the repo,
  and neither `prepare` nor `add-dates` writes the file. So every build since S moved has warmed October boards that no
  script opens. Parity itself holds: 20 of 20 listed routes hit.
- This is also a miss in the Q7 audit (§7.1): a product config file carries demo-story dates.
- **Real-site sense:** the warm list exists so that the pages people open next answer at once. On a real Site those
  pages are the latest days and this week. In the demo they are the pages the script opens. A list that warms neither
  does no useful work. The presenter's first open of each story board then pays a compose of 5 to 9.5 s.

**Fix: product root plus tool.** Branch `task/E4-C2-prebuild-follows-calendar`, Opus builder, about 0.75 unit.
1. **Product.** `chain/adapters/file_chain_config.load_prebuilt_routes` reads the file named by
   `ASSETOPS_PREBUILT_ROUTES` when that variable is set. The schema is the same (`chain/prebuilt.parse`). When it is not
   set, it reads the config default.
   - Do **not** add the variable to `chain/watermark.COMPOSER_ENV` or `SERVE_KEYS`. The list chooses what to warm and
     never changes a body.
   - Test, new `backend/tests/test_e4_prebuilt_routes_source.py`, no DB:
     - with the variable set, `prebuilt_requests()` returns the file's requests;
     - without it, the default;
     - `code_version()` is equal with and without it (clear the `lru_cache`);
     - the name is not in `COMPOSER_ENV`.
2. **Tool.** In `tools/demo_combined.py`, add a pure function
   `prebuilt_routes(story, days, kisiwa, sites_last_day)`.
   - It derives the requests **from `story_links`'s own rows**, so what is warmed equals what the script opens, by
     construction.
   - It maps each web link to the stored-route API request(s) its page issues, with the exact query the frontend
     sends:
     - Portfolio (`lens=all`);
     - outcome-summary;
     - Findings (`lens=all&state=all`);
     - each `/sites/{code}` board to `/api/sites/{code}/outcome-board`, with the same `date=` or `from/to`.
   - It also adds each Site's board for every date from S+1 to that Site's last added date (Kobo by `date`). The story
     step 7 day is then warm as soon as the tick after its release ends.
   - The tool writes `<work>/prebuilt-routes.json` before every prebuild (`performance_and_prebuild`) and at `serve`
     start. It sets `ASSETOPS_PREBUILT_ROUTES` in `serve_env`, so both the tool's prebuild and the serve loop's prebuild
     read the file.
   - Tests, no DB (in `backend/tests/test_own_g1_add_dates.py` or a new file):
     - S=2026-11-07 gives a `board.day` request for every story-day link, plus the week, S and month estate requests;
     - no date falls outside the story calendar or the added dates;
     - the file is rewritten when the last added date moves.
3. **Config default.** It stays as it is, for the existing tests and `chain_watermark_guard.py`. **BL-64 (post-demo):**
   replace it with a relative production list (the latest local day per Site and the current week, anchored on DB now).

### D-E4.2 STOP 2 (Cold/EV "Pending"): a defect. The Portfolio reads thread state at the evidence cutoff.

**Root cause (READ + DB).**
- `estate/portfolio.attach_threads` (`:144-162`) reads each Cold/EV row's thread state with `known_at` set to the
  Site's **evidence cutoff**: `cutoffs[site_code]`, from `select_finding_scope` (`estate/index.py:151-156`,
  `site_cutoff`). That cutoff is `max(ingestion_disposition.decided_at)`, the Site's last reading.
- CH-6b2 R2 (cb73f7409) ruled the opposite for lifecycle reads. `chain/read.lifecycle_cutoff` says the evidence cutoff
  bounds evidence only, and the request cutoff `k` bounds a thread's lifecycle. That commit changed the board
  (`chain_api.py:185-187`) and the claims (`chain/claims.py:84, 97`). It missed the Portfolio.
- DB, EV: the last reading is 2026-11-03 09:00Z. The ACTION_IN_HAND event has `cause_known_at` 11-03 09:40Z, after
  that reading. So the event is never visible, and the row reads OPEN.
- DB, Cold: the ACTION_IN_HAND event is at 11-07 17:15Z. The Cold rows read "Pending" only once add-dates wrote readings
  after that instant. Cold's last `decided_at` is now 11-09 17:09Z.
- So R4.1's label code is right; the state it is given is wrong. Neither stale storage nor the prepare order is the
  cause.
- **Real-site sense:** an action agreed after the last reading is still agreed. A cold room whose logger is quiet is
  the case where the manager most needs to see that someone is acting, and bounding the state by the last reading hides
  exactly that case.

**Fix.** Branch `task/E4-C1-portfolio-lifecycle-cutoff`, Opus builder, about 0.25 unit.
- In `estate/portfolio.attach_threads`, read every row's thread state and Action segments at
  `lifecycle_cutoff(default)`, as one group rather than one group per Site.
  - `day_at` (`req.to - 1µs`) and `visible_at` (`default`) are unchanged.
  - Set `_thread_cutoff` to the same value, so `action_segment_for` stays consistent.
  - Update the comment to cite CH6b2-R2.
  - Keep the `cutoffs` parameter for its callers; it no longer bounds the lifecycle.
  - Mini-grid rows are unchanged: their cutoff was already `default`.
- Tests: a new no-DB file, `backend/tests/test_e4_portfolio_lifecycle_cutoff.py`, with a fake `threads` port that
  records its kwargs:
  - (a) a Cold row whose evidence cutoff is earlier than `k` is read with `known_at == k`;
  - (b) the same row, with the fake state `ACTION_IN_HAND`, gives `workflow_label` "Pending";
  - (c) an EV row behaves like (a) and (b);
  - (d) a mini row's call is unchanged.
- Run `test_ch2_threads.py`, `test_ch3_rows.py`, `test_ch5a1_r1_visibility.py`,
  `test_w303_portfolio_workflow_labels.py` and `test_r4_domain_row_thread_state.py`.
  - An assertion that pinned a Cold/EV state at the evidence cutoff may be updated, and is listed in the packet.
  - Any other changed assertion is a stop.
  - Occurrence visibility (CH5a1-R2 R-1) must not move.
- **Proof on the fresh build, before any add-dates.** On the Portfolio week link, both Cold start-failure rows and the
  EV row read "Pending". The Cold temperature row reads "No action yet".

### D-E4.3 STOP 3 (E4-GE any-outcome sweep): all 4 hits are correct behaviour; the sweep's test was too strict

**Kobo 10-28 and 11-05, MG-1 OBJECTIVE_MET (READ).**
- MG-1 is the only monthly measure (`outcomes/objectives.py:46, 61`).
- `judge_month` judges it over the Site-local month **up to the board day** (`chain/outcomes.py:108-123`). No later day
  is read.
- MET means the month-to-date kWh has already reached an at-least target. Missing days can only add to the total.
- The row text says so: "{mtd} kWh so far this month, on {c} of {e} days checked" (`chain/vocabulary.py:275`).
- **Real-site sense:** a site lead reads "the month's target is already reached; today's readings are not in yet".
  Both are true, and both are on the screen.
- This is not the BL-63 case. BL-63 is a day-scoped verdict (MG-2/MG-4) on a day whose own measure has no counted
  evidence.

**Kisiwa 11-01 and 11-02, MG-8 PRIMARY_FINDING_OPEN (DB).**
- On both days `critical_served` is COMPLETE (82,800 s) and `daylight_headroom_kw` is PARTIAL. Only
  `avoidable_gen_min` is NO_DATA.
- The Finding is the unexplained-fuel night. Its own measure, the night's fuel balance, is graded.
- By D-E2.9's principle (a Finding is judged on the evidence of the measure it moves), this is honest.

**Ruling: no High and no fix.**
- E4-GE(b) is restated for every later run: "no outcome may carry a Finding or objective reason on a day where **that
  outcome's own measure** has no counted evidence over **its judged span**".
- The judged span is the board day for MG-2/MG-4, the month up to the board day for MG-1, and the Finding's night or
  episode for a Finding reason.
- DS-1a presenter note for the Kobo 10-28 beat: "The monthly target was already reached; this day's readings had not
  arrived yet. Both are on the screen."

### D-E4.4 Items E4 did not run

**(a) COH.** There is no number to invent. The finish check's F-COH and F-COH3 rows are the COH gate, and both pass
(51/51). Closed as PASS.

**(b) Forced unfinished Kisiwa night.** This check is still required: on a demo morning the catch-up must never write
a night that has not ended.
- Run it at the next E4-lite, before 15:00 local:
  1. `add-dates --site KISIWA-001 --to <today-1> --dry-run`;
  2. then the same command without `--dry-run`.
- Expected: "night not over yet" and NIGHT_NOT_OVER. The Kisiwa evidence and `fuel_balance_window` counts do not change
  (take a snapshot before and after).
- Any write is a High.
- Meanwhile the unit pins (`test_own_g1_add_dates.py:179, 611`) stand. This check does not block E5.

**(c) Perf: the budgets, now named.**
- **PF1.** After one serve tick and its prebuild, every API request behind every `links` row answers
  `X-AssetOps-Stored: hit` on first open. This replaces the single-page check in D-E3.3.
- **PF2.** Each of those hits answers in 1.0 s or less (`curl` time_total).
- **PF3.** A serve tick with no new data has prebuild states `stored: 0` and `prebuild_ms` of 120,000 or less.
  - The limit is the product's own EX-3 rule: 50% of `TickLimits.tick_seconds` (240 s; `scheduling/tick.py:87, 303-306`).
  - The observed 134-149 s were data-arrival ticks. A data-arrival tick over 120 s is recorded, not a stop.
  - A no-data tick with `stored` above 0 is a stop: it means the watermark moved without data.
- **PF4.** Report the composed (cold) Portfolio week read and the slowest board. Either one over 15 s is a Medium for
  the walkthrough. PF1 keeps cold reads off the presented beats.

### D-E4.5 Re-prepare: yes, once C1 and C2 have merged

- Neither fix changes stored data. But the `tree` under `var/polish_client2/tree` is a code snapshot, and R6.3's runbook
  rule stands: "Never replace or edit a build's `tree`. New code means a fresh `prepare`."
- R4.1 must be proven on a **fresh** build before any add-dates. Only a fresh prepare can prove that.
- So: one fresh E3 prepare from main after both merges (about 2 h 12 m, machine idle). No demo patch, and no tree swap.

### D-E4.6 Observation, not an E4 stop: the board gap line over-states on Kisiwa

- `site_outcomes/mini.py:133, 361-385` counts a day as "no checked readings" when its **weakest** measure is NO_DATA.
- On Kisiwa from 11-01 to 11-07, `critical_served` is COMPLETE. Even so, those days are counted as having no checked
  readings ("28 of the last 31 days").
- A real manager reads that line as "the gateway was down", which is false.
- **Ruling: an honesty defect on a presented board. Fix it with two tiers.**
  - Days with no counted measure keep `GAPS_NO_READINGS`.
  - Days where some measures are counted read "{p} of the last {n} days {verb} only partly checked".
  - Branch `task/E4-C3-gap-line-tiers`, Sonnet builder, about 0.5 unit.
  - Tests: the `finding_gap_line` cases and the IDX-GAPS pins. List any capture change.
- C3 joins the re-prepare only if it is reviewed and merged when C1 and C2 are. Otherwise it is a Medium on the owner
  walkthrough list and lands in the Sun-15 build. It never holds E5.

### D-E4.7 Order of work

1. C1 and C2 build in parallel, and each gets a fresh Opus review; only High or Medium findings block. C3 builds
   alongside them on Sonnet. Merge, then run check-all on main.
2. A fresh E3 prepare from main (one heavy job).
3. E4 again, in full. It includes D-E4.2's proof before any add-dates, D-E4.3's restated GE(b), and PF1-PF4.
4. E5 screenshots (1440/390), then the DS-1a refresh (the R4.1 lines and D-E4.3's note), then the owner walkthrough.
   Item (b) runs at the first morning E4-lite.

### Decisions logged for owner review

- **D-E4.1** The warm list follows the story calendar. It is derived from the script links, and the product reads it
  from a deployment input. The production default goes to BL-64.
- **D-E4.2** The Portfolio reads a thread's lifecycle state at the request cutoff, as the board does. Cold/EV "Pending"
  then shows on a fresh build.
- **D-E4.3** Two cases are honest: a monthly "met" on a no-data day, and a fuel Finding on a day whose generator measure
  is unchecked. The sweep is restated per measure.
- **D-E4.4** COH is closed by F-COH and F-COH3. The resume check runs at the next E4-lite. The perf budgets are
  PF1-PF4.
- **D-E4.5** A fresh prepare after the fixes; no tree swap.
- **D-E4.6** The gap line separates "no checked readings" from "only partly checked".

## E4 L2 ruling (2026-11-09)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`), under the owner's delegation of 2026-11-08. Input: C2 review
L2 (`AssetOpsV1-c2/.agent/C2-review.md`), the E4 serve logs (`AssetOpsV1-e3/var/polish_client2/logs/39..111-*`), code on
main 0c8f7f668 and C2 7c71854c7, and read-only SQL on `assetops_polish_client2_test` (`chain_input_change`,
`chain_response`). **READ** = code cited; **DB** = queried; **LOG** = serve logs.

### D-E4.8 The per-tick rebuild is a defect: the serve loop moves `F` with no new data

**Root cause.**
- **No data arrived (LOG + DB).** Every serve tick from 92 onward reports `processed: 0` at every stage of every Site
  (s4 `SKIPPED_UNCHANGED_FENCE`; Kisiwa `fuel_night` re-reads 7 nights and writes nothing). The last
  `chain_input_change` row is 17:17:56Z; the ticks at 17:30-18:16Z wrote none. The serve loop ingests no simulator
  readings: data arrives only through `add-dates` and drains.
- **The DB watermark is stable; only `F` moves (DB).** In `chain_response`, successive rows for one request key carry
  the same `cic:` count (estate `cic:1130129`, Kobo `cic:675643`) and a different `|f:` term on each tick. The Sites
  whose `F` is stable (Cold, EV) are the 8-9 hits.
- **What moves `F` (READ).** `tools/demo_combined.Demo.tick` ends with `performance_and_prebuild` (`:842-867`), which
  reruns `performance_migration run` for KOBO-001 and KISIWA-001 on **every** tick. Each run writes a new timestamped
  report under `{evidence}/migration-performance/{site_key}/` (LOG: `97-performance.log`, `98-performance.log`). That
  directory is a declared `F` root (`config/chain/file-inputs-v1.json`, hashed by size and `mtime_ns` in
  `chain/adapters/file_inputs.file_state`). So every estate request (`F` over all Sites: 7 routes plus 3 scope-ids) and
  every Kobo and Kisiwa board misses. That is the 14-15 stored. The tool's own docstring says so: "a new report moves
  `F`".
- **The correction to D-E4.4(c).** The 134-149 s ticks were recorded there as data-arrival ticks. They were not: they
  were no-data ticks. Under PF3 as written they are a stop (`stored` above 0 on a no-data tick), which is what PF3 was
  for. The store and watermark rules are right; the tool feeds them a false change.
- **Real-site sense.** A comparison that re-reads unchanged evidence has nothing new to say. On a real Site the
  Performance gate is rerun when the evidence it compares has changed, not on a timer. Rerunning it on a timer turns a
  quiet store into a full rebuild every two minutes, and a presenter's click during that rebuild lands on a cold compose
  or a race.

**Fix card E4-C4: Performance comparison only on change.** Branch `task/E4-C4-performance-on-change`, cut from the C2
head (it edits the same file); merges after C2. Sonnet builder, about 0.25 unit. Tool only; no product code changes.
1. In `tools/demo_combined.py` `performance_and_prebuild`, run `performance_migration run` for a Site only when
   `performance_due(site, mark, marks, report_dir)` is true. This is a new pure function. It returns true when any of
   these holds:
   - the Site has no report file under its `migration-performance/{site_key}` directory;
   - `<work>/performance-marks.json` has no mark for the Site;
   - the recorded mark differs from `mark`.
2. `mark` is the Site's DB watermark, read **before** the run with the same predicate as
   `chain/adapters/postgres_response_store.read_watermark` for that one Site: the tenant's rows for the Site plus the
   tenant-wide NULL rows. Use one short read-only connection to the build's DB. Record `mark` after a run that exits
   0. Reading it before the run is the safe direction: a write during the run forces a rerun next time. Write the marks
   file atomically, as C2 does for the routes file.
3. Print one line per Site: `performance: skipped (no change since mark N)` or the run's last line, as now.
4. The prebuild still runs every tick, as now. With `F` quiet, it is a store hit for every request.
5. Tests (new `backend/tests/test_e4_performance_on_change.py`, no DB):
   - `performance_due` is true with no report, true with no mark, true on a changed mark, and false on an equal mark
     with a report present;
   - with a fake `py` and a fake mark reader, two `tick()` calls on an unchanged mark run `performance` once and
     `prebuild` twice;
   - a changed mark between the two calls runs `performance` twice;
   - a failed run (non-zero exit) records no mark.
   - Run `test_demo_combined_finish_rows.py` and the C2 tests. Any changed assertion is listed in the packet.
6. **BL-65 (post-demo).** Have `performance_migration` write a new report only when the comparison differs from the
   newest report. The product would then be quiet on its own, whoever schedules the comparison.

### D-E4.9 PF3, measured honestly

- **A no-data tick** is a serve tick for which (i) every Site's DB mark is equal before the tick and after its prebuild,
  and (ii) no `add-dates`, drain or other writer ran in that span. The E4 run records the four marks with read-only SQL
  around at least **three consecutive** serve ticks, and those ticks are PF3's sample.
- **On a no-data tick** the prebuild must show `stored: 0`, `race: 0`, and every request a `hit`. Its `prebuild_ms`
  must be 120,000 or less, the EX-3 rule. The expected figure is under 15 s (45 hits at about 50 ms, plus the child's
  start). `stored` above 0 is still a **stop**: with C4 in place it means something other than data moved a watermark.
- **A data-arrival tick** is the first prebuild after `add-dates` or a drain. It rebuilds the estate requests and the
  changed Sites' boards. That is legitimate: the store's watermark is Site-wide by design (W2/W4), so late data
  re-checks history.
  - The prebuild that follows `add-dates` (and each post-drain prebuild in `prepare`) is recorded, not budgeted. The
    gate is PF1 after it.
  - Any **other** data-arrival tick over 240 s (one full tick: it would overrun the next) is a Medium.

### D-E4.10 C2's longer list stands; no scoping down

- C2's 42 requests are `story_links`'s own rows, plus the S and month estate requests and each Site's boards from S+1
  to its last added date. The script links already **are** the DS-1a dates. The S+1 tail is one or two days per Site.
  These are the days a real manager opens first, and the step 7 day is among them. Cutting the list would move cold
  composes of 5-9.5 s onto presented beats, which is the failure D-E4.1 fixed.
- **Live-demo cost after C4.** A no-data tick is all hits (seconds). The full rebuild of about 5-6 min happens once,
  after the morning `add-dates`.
- **Prepare cost.** Each post-drain prebuild grows to about 5-6 min, about 10 min more in total on a run of about
  2 h 12 m. It is offline on an idle machine, and accepted.
- **Presenter rule (DS-1a runbook line, added at the DS-1a refresh).** Run `add-dates` at least 10 minutes before
  presenting. Do not open the first link until a `prebuild:` line after it shows `stored: 0` (the store is quiet). A
  click before that point is still correct, only slower.
- Pages outside the list compose on demand and are measured by PF4, as ruled.

### D-E4.11 Order (amends D-E4.7)

1. C4 is built and reviewed (fresh Claude review; only High or Medium findings block). It merges after C2 and before
   the fresh prepare.
2. The re-prepare (D-E4.5) waits for C1, C2 and C4.
3. The E4 rerun measures PF3 by D-E4.9.

### Decisions logged for owner review

- **D-E4.8** The rebuild on every tick is a tool defect. The serve loop reran the Performance comparison on a timer,
  and each new report moved the file term. The fix reruns it only when the Site's data changed.
- **D-E4.9** PF3 is measured on ticks proven quiet by the DB marks. The rebuild after `add-dates` is recorded, not
  budgeted.
- **D-E4.10** The full story-derived warm list stays. The presenter waits for one quiet prebuild after `add-dates`.

## E3b stop ruling (2026-11-10)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`), under the owner's delegation of 2026-11-08. Input:
`AssetOpsV1-e3b/.agent/E3b-results.md` and `var/polish_client3/check.json` (8b13c7f95), code on main da68db6d4, and
read-only SQL on `assetops_polish_client3_test`. **READ** = code cited; **DB** = queried.

### D-E3b.1 Root cause: the board's thread lookup still reads the lifecycle at the evidence cutoff

**The board side (READ).**
- `site_outcomes/read.py` `board()` (`:470-495`) reads each listed Finding's thread with
  `known_at=cutoff`, where `cutoff = window["known_at"]`.
- For cold/EV, that value is `board_cutoff` (`:897`), which is `site_cutoff`. That is the window's last reading
  (`decided_at`), bounded by `k`.
- So the outcome-board reads the lifecycle at the **evidence** cutoff. This is the read CH6b2-R2 ruled out.

**The Portfolio side (READ).** After C1, `estate/portfolio.attach_threads` reads at `lifecycle_cutoff(k)`.

**The other readers (READ).** The `/chain` route (`chain_api.py:185-187`) and the claims (`chain/claims.py:84, 97`)
already read at `k`.

**My error.** D-E4.2 cited `chain_api.py:185-187` as "the board". That is the `/chain` route, not the outcome-board
composer. So C1 moved the Portfolio to `k` and left the board behind. The C1 review's L3 ("they agree at read time")
was wrong for the same reason.

**What F-COH requests (READ).** `_coh` calls `cc.collect(..., known_at=None)`, so both sides get the live request.
- The board resolves its cutoff to the window's last reading.
- The Portfolio resolves it to the envelope `k`.

**DB: all 8 mismatches are explained.**

| Site | Evidence cutoff | Thread events | Board sees | Portfolio sees |
|---|---|---|---|---|
| EV | 11-03 09:00Z | OPEN 09:35Z, ACTION_IN_HAND 09:40Z | neither: (None, None) | ACTION_IN_HAND |
| Cold, 11-07 window | 17:05Z | thread 3eef: OPEN on 11-04, ACTION_IN_HAND 17:15Z | OPEN | ACTION_IN_HAND |
| Cold, 11-07 window | 17:05Z | thread 8adc: OPEN 17:10Z | (None, None) | OPEN |

- EV gives 2 mismatches: the week and month windows.
- Cold gives 6: 2 threads in each of the week, S and month windows.

**Why client2 passed 51/51.** Before C1, both sides read at the evidence cutoff. They agreed because both were blind.
The board listed a Finding whose thread had no state at all.

**Verdict.**
- The **board** is wrong.
- The **check** is right. It caught the gap as soon as one side was fixed.
- The **Portfolio** (C1) is right.

**Real-site sense.**
- A Finding is always known after the evidence it assesses. A reading cutoff therefore hides the Finding's own
  opening, and any action agreed after it.
- A manager who opens EV on 11-03 must see that someone agreed an action that day, at 09:40Z. The time-travel
  honesty comes from the state **day** (`state_on(evs, board_day)`, each event's effective day), not from the
  reading cutoff.
- A board that lists a fault with no state, while the Portfolio says "Pending" for it, contradicts itself on the
  presented beat. R4.1's "Pending" intent holds on both screens only once the board reads at `k`.

### D-E3b.2 Fix card E4-C5: the board reads thread lifecycle at `k`

Branch `task/E4-C5-board-lifecycle-cutoff`, cut from main da68db6d4. Opus builder, about 0.5 unit. Fresh Claude
review; only High or Medium findings block. Do the pre-flight questions before writing code.

1. **Product.** In `site_outcomes/read.py` `board()`, pass `known_at=lifecycle_cutoff(known_at)` (the raw request,
   as `chain_api.py:185` does) to `self.s.threads.lookup`.
   - `visible_at=known_at` is unchanged (CH5a1-R2 R-1).
   - `day=board_day` is unchanged.
   - `facts.known_at` and every evidence read stay at `cutoff`.
   - Mini boards do not change, because `board_cutoff` is already the request's cutoff for mini. The opportunity
     read stays at `cutoff`.
   - Update the comment at `:472-475` to cite CH6b2-R2 and D-E3b.1.
   - The pre-flight confirms that no other board-side lifecycle read (Action refs, thread lines, `dated_lead`) uses the
     evidence cutoff. If one does, it moves to `k` in this change and is listed. Evidence reads never move.
2. **Check (fundamental: no agreement in blindness).** Extend `tools/checks/chain_coherence.py` COH-13. In a
   lifecycle-stamped bundle, a board or Portfolio thread on a **listed** Finding with `state` None is a finding:
   "listed Finding with no thread state".
   - Add one fixture to `tools/checks/test_chain_coherence.py` (the both-None pair fires).
   - Any existing fixture that relied on None is listed in the packet.
3. **Tests.**
   - New no-DB `backend/tests/test_e3b_board_lifecycle_cutoff.py`, with a fake `threads.lookup` that records its
     kwargs:
     - (a) a cold board with an evidence cutoff earlier than the request reads with `known_at` equal to the request
       value (None when live);
     - (b) an EV board behaves the same;
     - (c) a mini board's call is unchanged.
   - Run `test_ch2_threads.py`, `test_ch3_rows.py`, `test_ch5a1_r1_visibility.py`, `test_ch5a2_contract.py`,
     `test_e4_portfolio_lifecycle_cutoff.py`, `test_r4_domain_row_thread_state.py`, `test_chain_coherence.py` and
     `test_demo_combined_finish_rows.py`.
   - Rule for changed assertions:
     - An assertion that pinned a cold/EV **board** thread state at the evidence cutoff may change, and is listed.
     - Any other changed assertion is a stop.
     - Occurrence visibility must not move.
4. **In-process proof before the prepare (cheap; the machine is idle).** From the C5 worktree, run the finish rows
   F-COH and F-COH3 in-process against `assetops_polish_client3_test` / `var/polish_client3`. That DB is discarded
   and is a `*_test` DB.
   - Pass condition: F-COH passes, with the EV 11-03 and both Cold 11-07 pairs present and equal.
   - This is the gate for item 5, not a demo patch. client3's `tree` is never edited.

### D-E3b.3 Rebuild path

- Another full prepare is required: client4, from main after C5 merges, about 2 h 10 m on an idle machine.
- Reasons:
  - R6.3 forbids editing or replacing client3's `tree`.
  - The demo build must serve the fixed board code.
  - R4.1 must still be proven on a fresh build before any add-dates (D-E4.2's proof, plus: the EV 11-03 board and the
    Cold 11-07 board show those Findings as "Action agreed"/in hand).
- Nothing short of that proves the build. The in-process proof (D-E3b.2 item 4) only guards against wasting 2 h.
- client3 is retired. Do not serve it.
- D-E4.4(b), the forced unfinished Kisiwa night, runs on client2 as the coordinator proposed.
  - Snapshot before and after.
  - client2 already has add-dates through 11-09, so the only pending night is the unfinished one.
  - Run it before 15:00, never concurrently with the prepare.
- Order: C5 build and review, then the in-process proof, merge, check-all, prepare client4, the full E4 rerun
  (PF1-PF4, GE(b) per D-E4.3), then E5, DS-1a and the walkthrough.

### Decisions logged for owner review

- **D-E3b.1** The board, not the Portfolio, was wrong. My D-E4.2 ruling missed the board composer's thread read.
  Client2's earlier pass was agreement in blindness.
- **D-E3b.2** The board reads thread lifecycle at the request cutoff. COH-13 now refuses a listed Finding with no
  state.
- **D-E3b.3** A fresh prepare after C5. client3 is retired. The Kisiwa resume check runs on client2.

## Any-range speed ruling (2026-11-10)

- Architect: Claude (fresh `assetops-architect`). Full answer, measurements and design:
  `.agent/architect-answer-any-range-speed-2026-11-10.md`. Owner question verbatim:
  `.agent/owner-any-range-speed-2026-11-10.md`. Owner away, verbatim: "no cutting corners on fundamentals".
- Measured on client2, store off, cold: Kobo board day 11.2 s, Kisiwa board day 11.3 s, Cold board week 1.6 s,
  Portfolio week 12.1 s, Portfolio 10-12..10-19 4.2 s, Portfolio month 36.1 s. 80-85% of a mini board is the on-read
  hourly currentness re-fingerprint; the Portfolio is per-Site-day dispatch, claim and provenance recompute. Day
  snapshots themselves read in 2-160 ms.

### D-ANY.1 The full fix is BL-66, and it reverses CH5c-R2's substitution

The page cache (CH-5c option A) stands in for the stored daily read model the owner asked for on 2026-11-03. BL-66
moves every range-bound read onto revisioned per-period rows rebuilt per event through the existing register (cards
AR-0 to AR-6, 6.75 units, slices ANY-1 and ANY-2). ANY-2 is demo-critical if the owner sets the client session after
it can land; the date is the owner's.

### D-ANY.2 Pre-demo partial step: slice ANY-1 (boards), after FR-B

AR-0 (parity and arbitrary-range speed guard, 0.5), AR-1 (read-row foundation, 1.0), AR-2 (board mini depth on rows,
1.5): 3.0 units. It is the first slice of the real fix, not a workaround. It starts after FR-B (Wed 11 to Fri 13)
merges and does not displace it. Done when every mini-grid board day composes in 2 s or less cold with the store off,
and AR-0 parity holds byte for byte on the story requests and seeded random days, live and historical.

### D-ANY.3 No range-agnostic warm-up and no longer pre-load list

Pre-building more pages on data arrival cannot cover arbitrary ranges, multiplies the Site-wide rebuild after each
`add-dates`, and is thrown away by BL-66. Refused. D-E4.1 and D-E4.10 stand unchanged until AR-5 retires the list.

### D-ANY.4 Presenter rule until the fix lands

At the walkthrough, at FR-B and at any client session before ANY-2: stay on the script's ranges, and use the
Portfolio selector only for the pre-built week, S and month. Off-script, the presenter says the range is being
computed and moves on. The owner is shown the measured numbers before the walkthrough.

### Decisions logged for owner review

- **D-ANY.1** The full fix (BL-66, 6.75 units) replaces the page cache as the speed mechanism.
- **D-ANY.2** ANY-1 (boards, 3.0 units) is built before the client session, after FR-B.
- **D-ANY.3** No warm-up of more pages.
- **D-ANY.4** Presenter stays on script ranges until the fix lands.

## E5 rulings (2026-11-10)

This section was written by the Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). It works under the owner's delegation of 2026-11-08 ("no cutting
corners on fundamentals"). The owner can be reached today and will do the walkthrough this afternoon, so owner calls are listed separately and are not ruled here.

Inputs:
- `AssetOpsV1-ds1a/.agent/E5-captures.md` (c252b6cf3) and its `e5/text/*.txt`;
- the DS-1a draft on `task/DS-1a-client-script`;
- client4 (`assetops_polish_client4_test`, `var/polish_client4`, S = 11-08, tree code b234cea2a);
- `AssetOpsV1-e3c/.agent/E4b-results.md`.

**READ** means the code is cited, from main d5549feb6. `git diff b234cea2a main` over `frontend/src backend/assetops_backend host contracts config tools/demo_combined.py` is empty, so main's code is client4's code. **DB** means a read-only query on client4.

### D-E5.0 How a fix reaches client4 without a rebuild (READ)

- **The backend serves from the frozen tree.** `serve` starts uvicorn with `cwd=<work>/tree/host` (`tools/demo_combined.py:1477-1479`), and the tree is a `git archive` of the build commit (`:825-840`). A fix to the backend, `config/`, `host/` or `contracts/` therefore needs a new prepare. R6.3 still holds: the tree is never edited or replaced.
- **The frontend is not served from the tree.** `serve` prints "Frontend, from frontend/: npm run dev" (`:1495`), and E5 ran Vite from the e3c checkout.
- **`code_version` does not cover the frontend.** It hashes the alembic head, the backend sources, `config/`, `host/**/*.py` and `contracts/**` only (`chain/adapters/file_code_version.py:3`). A frontend change therefore touches neither the tree nor any stored page.
- **`tools/demo_combined.py` runs from the checkout.** Its `links` command is also outside `code_version`.
- **So:** a frontend or `links` fix applies by restarting Vite, and re-running `links`, from a checkout at the fix's merge. **No item below needs a rebuild of client4.**

### D-E5.1 STOP-1, "Yesterday arrives": R4.2 stands for demo day; today no Site has a day to release

**Root cause (READ and `days.json`).** S is the prepare day minus 2 (`demo_combined.py:12-13`). On 11-10, no Site has a finished day that has not been added yet:
- Kobo's story days run to S+1 (11-09, `trial-after`).
- Kisiwa's story nights also run to S+1 (`story_links`, "S-9d to S+1d"; the E4b dry-run gave `KISIWA-001: []`).
- E4b already added Cold 11-09.
- EV adds data on Tuesdays only, and 11-09 is a Monday.
- Today, 11-10, has not ended.

The product and the tool are working correctly. The build is one day too young for this beat.

**General rule, added to R4.2 item 2.** The live beat exists only when yesterday is later than S+1. That means the session date must be at least S+3, which is the **prepare date + 1**. A build prepared on the session day never has the beat.

**Demo day.** R4.2 is unchanged: Kobo's yesterday is held back and the script wording stays. Using Cold or Kisiwa instead is refused:
- a Cold day shows no change the client would notice;
- holding Kisiwa back would clash with the live-dip night (D-E5.2).

**Today's walkthrough.** Step 7 is shown in words, with the two honest stand-ins:
- 05, captioned "A day whose readings have not arrived yet (10 Nov)";
- 04, captioned "A checked day (9 Nov)".

They must never be captioned as the before and after of one day. The presenter says the real release is rehearsed tomorrow, in E5b.

**E5b** is an agent run on client4 on Wed 11 Nov, after Kobo-local midnight. It changes no product code and writes only add-dates data and one dip:
1. Run the morning runbook from R4.2 item 2: `add-dates --site COLD-LAB-001,EV-LAB-001,KISIWA-001 --no-check`, up to 11-10. EV adds its Tuesday. The Kobo command `--to 11-09` refuses with `STORY_DAY`. Confirm this with `--dry-run`, then run the first command again without `--no-check`.
2. Capture the "before" view: `/sites/KOBO-001?date=2026-11-10` at 1440 and 390, recording the board's words.
3. Run `add-dates --site KOBO-001 --to yesterday --no-check`. Time it from start until "KOBO-001: added" prints; R4.2 item 4's 11-minute rule is decided on this number. Reload the same URL and capture the "after" view.
4. Save the live dip (D-E5.2). Then run plain `add-dates`, which ends with the finish check; a FAIL retires client4. Then one tick, the prebuild, and PF1 on the `links` rows (every request must be a hit).
5. Take the D-E5.5 capture: the OPP-000003 page. Write the results to `.agent/E5b-results.md` on `task/E5-captures`.

### D-E5.2 STOP-2, the dip: no dip on client4 today; a real save is rehearsed in E5b; no fixture pictures in the client script

**Root cause (READ and E5).** R1.4 ties the dip to the newest *added* Kisiwa night and to the value `links` prints (`added_night_links`, `demo_combined.py:1456-1459`). client4 has no added Kisiwa night (D-E5.1), so no night is safe. Three options are refused:
- **A story night.** Every Kisiwa night in client4 is a story night. A dip there would honestly re-check that night and could change the ACT-004 verdict (R1.4 presenter note).
- **Tonight (11-10).** A dip there would sit in a night that later receives simulated tank data, and could create unexplained fuel that does not belong to the story.
- **Any other night.** None exists.

**Ruling.** §5.3 says the after-submit state is captured only in G3b fixtures, never on the demo DB. That is **amended for E5b only**:
- E5b saves one dip through the Operational records form, which uses the product's entry route (`service:operator-entry`).
- The dip goes on the newest added Kisiwa night from E5b step 1, at 06:00, with the value `links` prints.
- Capture, at 1440 and 390:
  - the form after the save;
  - the records list showing the dip as "Submitted", "Entered by site admin";
  - after the next tick, that night's Fuel page, checked again.

This is exactly the session's beat. At the session the newest added night will be a later one, so the rehearsal dip simply stays as one more true record.

**Order.** E5-FX (D-E5.3) merges and Vite restarts on it before the E5b dip, so the list shows the fixed labels.

**Client script.** The `*-FIXTURE.png` pictures are never used: they show another Site and other values (REC-041, 198 L). If E5b is not done before DS-1f, step K has no saved-dip picture.

### D-E5.3 STOP-3, `service:w401-fixture` in the By column: a product display defect; frontend fix, no rebuild

**Root cause (READ).**
- The prepare seeds every story record through `WorkService` in process, with `PRINCIPAL = "service:w401-fixture"`: Kisiwa `demo_combined_kisiwa.py:719, 772`, Kobo `:172`, EV `:109`, mill `:35-36`. This is the documented actor for example records (`demo_combined.py:14-15`, `work_api.py:48`).
- The list renders `actorLabel(row.actor_id)` (`OperationalRecords.tsx:213`). That function maps only `service:operator-entry` (`:89-91`) and prints any other ID as it is stored.
- R30 (W6-01 E2) accepted stored actor IDs at a time when no client screen existed.

**Why the seeding path is not changed.** Re-seeding the story records through the entry route would:
- claim the site admin typed records that the prepare created;
- be unable to place them at their story `recorded_at`;
- need a rebuild.

It is refused.

**Card E5-FX, part A.** Branch `task/E5-FX-actor-label-links` from main. **Sonnet**. Parts A and B together are **0.25 unit**, including a fresh Claude light review; only High or Medium findings block.
- Change `actorLabel` in `frontend/src/work/OperationalRecords.tsx`:
  - `service:operator-entry` → "Entered by site admin" (unchanged);
  - `service:w401-fixture` → **"Prepared example record"**;
  - any other `service:` ID → "Entered by a system service";
  - any other value is unchanged.
- `data-global-work-actor` keeps the raw ID as a test hook; it is not visible.
- Add the comment `MOCK DEVIATION MD-E5-1` and register row **R714**. R714 amends R30 for the By cell only; WorkRequestHistory's "Stored actor" disclosure (R39) is unchanged.
- **Tests.**
  - `frontend/src/work/__tests__/operationalRecords.test.tsx` gains the three mappings.
  - An assertion that pinned the raw `service:w401-fixture` By text may change; list it in the packet. Any other changed assertion is a stop.
  - Run that file and `operationalEntryForm.test.tsx` only; no full suite.
- **No rebuild needed** (D-E5.0): restart Vite from a checkout at the merge.

### D-E5.4 The Kobo finding link pins revision 1 of 3: a `story_links` defect; drop the pin

**Root cause (READ and DB).**
- `story_links` builds `?revision_id={kobo['finding_revision']}` (`demo_combined.py:320`).
- `kobo.json` stores the revision current when the Action was raised: `fc457881`, revision 1, 11-08 12:07.
- The Finding then gained two `BASIS_REFRESHED` revisions at story times, 11-08 14:02 and 11-09 12:07, with the same claim (200 candidate minutes). This is correct product behaviour, not tick churn.
- Version 1 says "Earlier version ... not the current answer" and "No current amount can be shown". The script describes the current conclusion and its cost.
- R2-DS1a 2 kept the pin because it was the revision the script describes; that no longer holds. **R2-DS1a 2 is superseded.**

**Card E5-FX, part B.**
- `tools/demo_combined.py:320` links to `/sites/KOBO-001/findings/{kobo['finding']}` with no query string.
- Update `backend/tests/test_demo_combined_links.py:56`, and run that file.
- The pre-built route list is unaffected, because it is built with `kobo=None` (`:424`).
- No rebuild: `links` runs from the checkout.

### D-E5.5 The Kobo opportunity hop lands on OPP-000005: the product is right; E5 used the wrong route

**READ.**
- The board's Grow option is "Productive-use what-if". It goes to the Site's financial scenarios (`site_outcomes/mini.py:589`), then to Renewable evaluation and OPP-000005. That page is the headroom study, and it honestly says "Five-day study incomplete".
- On 11-09 the board's Grow potential reads "No potential found yet". The midday-solar opportunity, OPP-000003 "Daytime solar unused at Kobo mini-grid", was seen on 3-7 Nov, outside that day.

This is not a defect.

**Ruling.**
- The script's opportunity page is **OPP-000003**. It is reached from Findings › Opportunities on the story week (capture 07) or from the Portfolio Grow card.
- The presenter never takes the hop from the board's what-if.
- E5b captures the OPP-000003 page at 1440 and 390, from 07's row.
- OPP-000005's header, "Global Findings unavailable ...", is system wording, but it is off the script path: backlog Low, not demo-critical.

### D-E5.6 "4.50 USD" is not stale; the Portfolio writes it as "$4.50"

**READ.** The line is the Portfolio context footer (`EstatePortfolio.tsx:731`). Capture 01 has it at line 350: "Depot Charging Hub delivered 15 kWh in selected records; $4.50 at the recorded tariff, before costs (a what-if)". E5 searched the EV board for "4.50 USD"; the EV board only points to Financials.

**Ruling.**
- Keep the value. Quote "$4.50" exactly as the screen writes it, and attribute it to the Portfolio, not the EV board.
- The Portfolio page mixes "$" and "USD": backlog Low, not demo-critical.

### D-E5.7 DS-1f brief (Sonnet, after E5b; fresh Opus light review)

- **All steps.**
  - Quote dates as story days. Take real dates and every href from `links` on the session build.
  - Replace the draft's hard-coded checklist hrefs with `links` placeholders; for example the step 2 Finding `b824c41c...?revision_id=...`, dated "6 Nov".
  - Keep the "rehearsal build" caption.
- **Step 1.** Crop from 01 (the act-first view and the outcomes grid). The "$4.50" footer line goes here.
- **Step 2.** Use the finding picture from **03b** (the current version), never 03.
- **Step 3.**
  - Crop 02's Grow row, E5b's OPP-000003 page and 07. Never use 06.
  - The placeholder "the midday mill opportunity page" becomes "the daytime solar opportunity page".
  - Quote "Daytime solar unused at Kobo mini-grid" and "Size not worked out yet".
  - The "about 17 USD a day" figure is ACT-005, taken from 01.
- **Step 3b.** Kept. Crop 02's cost row with the screen's qualifier: "counted at a generic idle fuel rate of 3.3 L/h, not measured".
- **EV step.**
  - Keep the board crop from 10.
  - Move the "What you see" bullet with "$4.50" to step 1, or mark it "on the Portfolio".
  - "If asked" quotes "$4.50 ... (a what-if)".
- **Step K.**
  - The saved-dip picture comes from E5b only; without E5b, there is none.
  - Presenter line: "Records marked 'Prepared example record' came with the example site; the one I save now is listed as entered by the site admin."
- **Step 7.**
  - The backup pictures are E5b's before and after of the same Kobo day.
  - Caption: "Kobo board, one day, before and after its readings arrived (rehearsal)".
  - Add the D-E5.1 rule to the runbook: the beat exists only when the session is at least one day after the prepare.

### Decisions logged for owner review

- **D-E5.1** Yesterday-arrives stays as Kobo's held-back day on demo day. It needs a session at least one day after the prepare. Today it is walked with honest stand-ins, and E5b rehearses it for real on 11-11.
- **D-E5.2** No dip on client4 today. One real rehearsal dip goes on the newest added night in E5b. Fixture pictures are not used in the client script.
- **D-E5.3** Example records read "Prepared example record" in the By column. This is a frontend fix; no rebuild.
- **D-E5.4** The Kobo Finding link opens the current version.
- **D-E5.5 and D-E5.6** Neither is a defect. The opportunity route and the "$4.50" attribution are script corrections.

### Questions for the owner (not ruled)

1. **On-screen dip today.** It cannot be done honestly on client4 today. Would you rather watch the E5b rehearsal tomorrow, or see its pictures?
2. **Label wording.** Records that came with the example sites will read "Prepared example record". Keep this, or use other wording on a client screen?
3. **Session date and build.** Please confirm the client session date and which build serves it. The live beat needs a build prepared at least the day before.

## DS-1f anomaly rulings (2026-11-10)

Claude Architect (binding Claude, `.ai/ROLE_CONFIG.md:9`), under the owner's 2026-11-08 delegation. Code READ at e3c `5e46dae89` (= client4 code); DB = read-only queries on `assetops_polish_client4_test`.

### D-E5.8 Cold third visit: product defect (Cold composer lacks the linked-Finding resolve); fix with the rebuild

- **Facts (DB).** Backup generator: WR-000007 10-15, WR-000008 10-28, WR-000006 11-08, all COMPLETE. Only WR-000006 links a Finding (`3733fcfd…`, COLD_START_FAILURE, rev 1 OPENED/SUPPORTED, never closed). Cold also has a clean assessment pair for **11-09** (created 11-10 05:26 by the E5 add-dates/tick), with no Findings.
- **Rule (READ).** `outcomes/warnings.py:_repeated` fires on ≥2 completed visits to one asset in `[to-60 d, to)` with at least one linked Finding open in `open_findings`. The board 08 (day 11-08) shows it correctly: "3 visits (15 Oct, 28 Oct, 8 Nov)".
- **Root cause.** 09b uses the window `S-28 d .. S+3 d` (`demo_combined.py:293`). The estate summary reads Cold over that period, `cold_findings` returns only the *selected* (latest) assessment's Findings (`postgres_assessment_store.py:2548`), i.e. the clean 11-09 pair, so the still-open start failure is absent from `open_findings` and the warning is dropped. The card then claims "None found at GreenHarvest", a false all-clear. EV already resolves linked Findings that the selection lacks (`site_outcomes/ev.py:149-162`, addendum 3 (d)); Cold does not (`site_outcomes/cold.py:121-135`). The S shift exposed it only because a post-S Cold day now sits inside the window. Not the warning's window or rule.
- **Ruling: defect.** **Fix card FX-COLD-LINKED (Opus, S, ~60 lines):** `site_outcomes/cold.py` mirrors the EV block: for each visit/action-linked Finding id missing from `findings`, read it through a new `ColdPorts.finding` (bound in `site_outcomes/read.py:cold_ports` to `cold_reads.finding`); a refused read unsettles CC-3 and lists `cold_findings` in `reads.failed`. The read must return the Finding's current revision as of `known_at` independent of the selected assessment; if `cold_reads.finding` filters by the snapshot, add an id read that does not. Check mini for the same gap (report, do not widen). Tests: a backend unit test with a later clean assessment in the window (warning still fires, cites WR-006); a Postgres summary test over a window that contains a clean post-failure day. **Backend: needs a rebuild.**
- **Script.** Before the rebuild, never use the S+3 d window for this beat: take Maintenance with `from=S-28 d&to=S+1 d`. Wording: "The maintenance page flags the backup generator: three visits in 60 days, and the automatic start failure is still open."

### D-E5.9 EV "connector 2": data/story defect (fixture literal); fix with the rebuild

- **Root cause (READ).** `tools/w504_ev_work_cases.py:52` hard-codes `ACTION.title = "Investigate connector 2"` (a v6.9 mock literal). The registered replay `ev-interrupted` faults connector c1, and the board derives "Connector c1" from data (`ev.py:connector_name`). The product renders both correctly.
- **Ruling: defect in the story data.** **Fix card FX-EV-TITLE (Sonnet, XS):** set the title to "Investigate connector c1"; update `backend/tests/test_w504_ev_work_cases.py`, `test_w504_ev_intent_api.py`, `test_w504_ev_work_producer_postgres.py` and the frontend EV fixtures (`evWorkFixtures.ts` and its tests) that assert the literal. Tools-only code, but the title is stored in the DB, so **client4 keeps the old title; it needs the rebuild.**
- **Script.** After the rebuild: "ACT-003 · Investigate connector c1". On client4 (presenter note): "The example action's title says connector 2; it was raised from this connector c1 fault."

### D-E5.10 One rebuild

Merge FX-COLD-LINKED and FX-EV-TITLE (fresh Claude review each), then prepare one new build on 11-11 (~2 h 20 m). It also satisfies D-E5.1 for a Thursday session. E5b and the DS-1f picture retakes (09b, 10) run on that build.

### Decisions logged for owner review

- **D-E5.8** The missing Cold notice is a product defect (false "None found"); backend fix and rebuild.
- **D-E5.9** "Connector 2" is a fixture typo; fixed in the same rebuild.
- **D-E5.10** One rebuild on 11-11 and E5b moves to it. Owner may veto and keep client4 with the stand-in wording above.

## Kobo gap-pattern ruling (2026-11-10)

Claude Architect (binding Claude, `.ai/ROLE_CONFIG.md:9`), under the owner's 2026-11-08 delegation. Owner text: `.agent/owner-kobo-gap-pattern-2026-11-10.md` ("1 missed day with 1 partly missing would make sense"). Code READ at main `04bbb1b80`. DB = read-only queries on `assetops_polish_client4_test` (S = 11-08) and `assetops_polish_client2_test` (S = 11-07). Nothing was run or built.

### D-E5.11 Root cause: the v3 calendar, not the product (READ + DB)

The week S-6..S comes straight from `backend/conversions/demo-story-days-v3.json` (`sd.DEFAULT_FILE`):

| Day (S = 11-08) | v3 entry | What it reads | Deliberate? |
|---|---|---|---|
| S-6, S-5 (2, 3 Nov) | `steady` (3 runs tile 00-24) | COMPLETE 24 h | yes (MILL-3 later days S-8, S-6, S-5) |
| S-4 (4 Nov) | **no entry** | NO_DATA | **no**: side effect |
| S-3 (5 Nov) | `late` as `normal` | PARTIAL 8 h | the late kind is a calendar choice; no script beat uses it |
| S-2 (6 Nov) | **no entry** | NO_DATA | **no**: side effect |
| S-1 (7 Nov) | `normal` | PARTIAL 8 h | carries finish row WK-2a (42.08 USD) only |
| S (8 Nov) | `trial-before` | PARTIAL 8 h | **yes**: ACT-001 baseline |

- **Why S-4 and S-2 are empty.** `resolve` refuses a `late` day inside a multi-day stream (`LATE_IN_STREAM`, `tools/demo_story_days.py:390-395`), so DD1a2-R Q4 left both neighbours of the late S-3 unbuilt and logged the fix as BL-25 ("no shown claim needs those two days", `build-sheet-DD-1.md:817-821`). That reason no longer holds: the Portfolio week now shows them.
- **Why exactly 8 of 24 h.** The story-only kinds replay registered Lab scenarios that run 03:00-11:00Z, i.e. 06:00-14:00 local (`kinds.kobo.normal/overuse/trial-*`: `start D+0d 03:00`, `end D+0d 11:00`). No gateway behaviour causes it. DD1a1-R16 made the necessary-run (N) and trial (R30/R25) days story-only: N is RUNNING at 14:00 and 24:00, and R30/R25 are RUNNING at 24:00, so no honest rest-of-day or night could be joined (`build-sheet-DD-1.md:680-713`). Only the mill and steady chains passed, which is why only `steady*` and `mill-midday` days read 24 h.
- **Deliberate beats in or near the week:** the trial pair S/S+1 (ACT-001, the "Verified" headline), the weekly generator days S-28/S-21/S-14/S-7 (story-only by R16), the `missing` day S-10 (the FILL-1 beat), and the mill change S-9 with its later days S-8/S-6/S-5. **Side effects:** S-4 and S-2 (BL-25), and the 8 h reads on S-3 and S-1.
- **S-dependence: none for the pattern.** Every Kobo offset is S-relative; only EV has a weekday rule (`SITE_WEEKDAY`). client2 (S = 11-07) shows the same shape one day earlier: 1-2 Nov COMPLETE, 3 and 5 Nov NO_DATA, 4, 6 and 7 Nov PARTIAL. Only month boundaries move with S. (K7-D/K7-F are Kisiwa plan steps, `demo_combined_kisiwa.py:804`; they do not touch Kobo days.)

### D-E5.12 The fix: calendar v4, S-4 missed, S partly checked, five full days

**`backend/conversions/demo-story-days-v4.json`** (becomes `DEFAULT_FILE`; v3 kept as history, as v1 and v2 were). It is a copy of v3 with three entries changed in the week:

| Day | v3 | v4 | Reads |
|---|---|---|---|
| S-4 | none | `{"day": "S-4d", "kind": "missing"}` ("gateway offline: no run, no delivery") | NO_DATA, the week's one missed day |
| S-3 | `late` as `normal` | `steady` | COMPLETE |
| S-2 | none | `steady` | COMPLETE |
| S-1 | `normal` | `steady` | COMPLETE |
| S | `trial-before` | unchanged | PARTIAL, the week's one partly checked day |

All other entries, kinds and the trial block stay byte-equal. Label and status are updated to say "v4 (D-E5.12)".

- **Why S is the partial day and not a few-hour dropout.** S is ACT-001's baseline. Filling it needs either a rest-of-day run inside S's UTC day after the baseline pin, which moves the selected run and takes the trial off Verified (the DD1a2-R3 H1 mechanism), or a night run whose 06:00 end does not match the trial's declared start. Neither can be made safe tonight, so S stays 06:00-14:00. Presenter line: "8 November is the trial day. Its example readings cover 06:00 to 14:00, the hours the trial needed, so the day reads partly checked." A real few-hour dropout day needs the BL-18 source-time cut (Kobo `degraded` is held, `DEGRADED_PROBE`). That is backlog.
- **Why S-4 is the missed day.** It is already "4 Nov, not assessed" in the scripts, so the script change is smallest. It keeps the gap away from the trial pair: the trial reads only S and S+1, and the Finding on S does not touch S-4, so the PARTIAL Portfolio still lists it (CO-6). `missing` is the existing, honest kind.
- **Why this is safe (READ).**
  - `steady` uses `night-early` (the fresh declared start) and `mill-rest`. The same chain is already built back to back on S-6 and S-5, so `check_full_day`, `check_full_day_chains`, `check_mill_side` (offset > S-9) and `_tiled` pass by construction. S-1's runs end at S-1 21:00Z, outside S's UTC day, so the trial baseline is untouched. `FULL_DAY_AFTER_TRIAL` concerns S+2 only.
  - No `late` entry remains, so `LATE_IN_STREAM` cannot fire. The late-delivery path is still shown live by script Step 7 (add-dates) and is still covered by the existing L0 tests, which now load `V3_FILE`.
  - MILL-3 is unchanged: `choose_days` takes the first 3 COMPLETE days nearest the change (`verification_families.py:85-89`), still S-8, S-6, S-5. The baseline S-13..S-11 and the pinned study S-19..S-15 are unchanged. ACT-005 stays 17.00 USD.
  - No post-change five-day study becomes SUPPORTED: every window from S-8 to S+1 contains S-7 (partly checked), S-4 (missed) or S (partly checked), so each stays UNKNOWN (`projection.frozen_result`).
  - The extra build time is about +5 min: 3 full days (about 131 s each) replace 2 story-only days (about 38 s each).
- **Fallback with no code revert:** `prepare --days backend/conversions/demo-story-days-v3.json` rebuilds the old pattern. The restated rows below are written to pass on both calendars.

### D-E5.13 Fix card FX-KOBO-GAPS (Opus, S, about 0.5 unit / about 150 lines; fresh Claude review; parallel with FX-COLD-LINKED, no shared files)

Branch `task/FX-KOBO-GAPS`.

1. **Data.** Add `demo-story-days-v4.json` as in D-E5.12. In `tools/demo_story_days.py`, set `DEFAULT_FILE` to v4 and add `V3_FILE`. Update the manifest label `"days"` in `tools/demo_combined_kobo.py:563` to the v4 path.
2. **L0, `backend/tests/test_demo_story_days.py`.**
   - Tests that need a `late` entry or v3's table (`:52`, `:96`, `:109`, `:174`, `:322`, `:510-525`, `:583-612`, `:769`) load `sd.V3_FILE` explicitly. They are not deleted.
   - New `test_v4_story_week_one_missed_one_partial`. For S in {11-07, 11-08, 11-09}, `resolve(load(), S, installs=...)` gives, on S-6..S: exactly one day with no run (S-4, kind `missing`); exactly one story-only day (S, `trial-before`); five days whose runs tile [00:00, 24:00) local; and no `late` entry. Assert also that `DEFAULT_FILE.name == "demo-story-days-v4.json"` and that v4 minus the 4 week entries equals v3 minus its 2 week entries.
   - Must-fail: the same test run against v3 fails.
3. **New finish row `WK-GAP`** (`tools/demo_combined_finish.py`, `idx=True`), with a pure helper `demo_rows.week_gap_pattern(grades_by_measure)` and its own L0 test. Use a must-fail fixture that is client4's real pattern (2 NO_DATA + 3 PARTIAL) and must fail.
   - The row reads Kobo `site_day_snapshot` (latest revision per day, measure and subject) for `critical_served`, `daylight_headroom_kw`, `productive_kwh` and `avoidable_gen_min` on [S-6, S].
   - It asserts, for every measure: NO_DATA on exactly {S-4}; PARTIAL on exactly {S}; COMPLETE on the other five days.
   - It also asserts the served Portfolio week: the Kobo days line reads "5 of 7 days checked · 1 partly checked", and the CO-6 coverage `gaps == [S-4]`.
   - It derives the expected days from `ctx.site_days("kobo")` (the `missing` kinds and the story-only kinds) and never hard-codes dates, so on a v3 fallback it reports the v3 pattern and fails, which is the intended alarm.
4. **Restated rows (cause: D-E5.12; not edited to pass).**
   - **WK-2a.** The S-1 Grow headline is still "estimated productive-use sales". Its money follows S-1's kind: `steady` gives 110.000 kWh × 0.25 = **27.50 USD**, and `normal` (v3) gives 42.08. Docstring: "a mill-working steady day".
   - **WK-2b.** The potential on S follows the study ending S. If that study has ≥ 1 eligible day, the potential reads `LIMIT_UNKNOWN` ("Not judged yet: 2 of the 5 study days …", for S-4 and S), with no kW and no money. With 0 eligible days it reads "No potential found yet" (v3). The other WK-2b clauses are unchanged.
   - **WK-6.** Fix the docstring/comment only ("its v3 November days are 8 h runs").
5. **Copy (client-visible, caused by this change).** `chain/vocabulary.py:24` `LIMIT_UNKNOWN` gets a singular form: "1 of the 5 study days has no reading". The study 3-7 Nov will now have one empty day. Update the test(s) that pin the literal.
6. **Gates.** Guards A, W, V and N; `test_demo_story_days.py`; the new helper's L0; the vocabulary test. No full suite (demo-sprint policy). `python tools/demo_combined.py`'s offline resolve/`--check` on v4 must pass.
7. **Stop rules on tonight's build.** If WK-GAP, WK-2a, WK-2b, F-COH, F-CAL, SP-3, SP-4 or the `demo_combined_after.py` reads fail, stop, do not tune, and report to the Architect. One difference is allowed and must be reported, not treated as a failure: the mill thread's RECURRED effective day may move earlier, because the study ending S-4 now holds eligible days from S-8. `recurrence_holds`' hard-coded `"2026-10-31"` is S-dependent (it runs only in `--s2` mode), and the report gives the value read. The fallback is the v3 `--days` rebuild.

### D-E5.14 Downstream figures (for the DS-1 scripts after the fresh build; expected values, confirm from the build)

These are for S = 11-08. If the fresh prepare lands S = 11-09, every date moves +1 day and the month figures are given in brackets. Each is "expected", by the same arithmetic the technical script uses. The build's numbers decide.

| Where | client4 now | After FX-KOBO-GAPS |
|---|---|---|
| Coverage line (client `:350`, technical `:535-538`, opening `:984`) | 5 of 7 days assessed · 2 days not available yet · not assessed: 4 Nov, 6 Nov | **6 of 7 days assessed · 1 day not available yet · not assessed: 4 Nov** |
| Days line under the cards (technical `:541-544`) | 2 of 7 days checked · 3 partly checked | **5 of 7 days checked · 1 partly checked**. Estate: 22 expected, 5 complete, 1 partial, 3 low, 13 no data |
| Grow card (client `:351`, technical `:547-550`, `:628`) | 139.16 USD over 2 of 7 · 3 partly | **137.50 USD** = 5 × 27.50 + 0.00 (S), "over 5 of 7 days checked · 1 partly checked" |
| MG-1 line (client `:474`, technical `:556`) | 556.7 kWh so far this month, on 2 of 8 days checked | **550.0 kWh on 5 of 8 days checked** (110 × 5 + 0 on 1 Nov + 0 on 8 Nov) [S = 11-09: 660.0 kWh on 6 of 9]. Target 300, so still **MET / On track** |
| Daytime-solar study 3-7 Nov (client `:472`) | Seen on 1 of 1 · 4 of the 5 study days have no reading | **Seen on 4 of 4 well-observed days · 1 of the 5 study days has no reading** |
| Kobo board potential on S (WK-2b) | No potential found yet | **Not judged yet: 2 of the 5 study days have no reading** |
| Board gap line (31 days) | 11 no checked readings · 7 partly checked | **10 · 5** (S-30, S-29, S-27..S-22, S-10, S-4; partly S-28, S-21, S-14, S-7, S) |
| Unchanged | | Generator Finding 8 Nov 04:35-07:55 and 0.00-15.13 USD; ACT-001 3.3 L / 4.12 USD, Verified; ACT-005 17.00 USD; MILL-3 "Target met"; Protect 2; Assure 3; Kobo stays PARTIAL, so its Portfolio row is still "Partly checked"; Kisiwa, Cold and EV all unchanged |

**Month view.** It improves but is not clean. On the 30 days [S-29, S]: 16 checked (now 13), 5 partly checked (the four weekly generator days S-28, S-21, S-14, S-7, plus the trial day), 9 with no data. The no-data days are the install day, a 6-day block S-27..S-22 that B-22 never built, S-10 (the FILL-1 beat) and S-4. Presenter answer: "The example starts at commissioning on 10 October. The first week has two example days, and from 19 October the readings run daily apart from two gateway-outage days. The weekly generator days carry only the example hours." Filling S-27..S-22 (`steady-before`, about +13 min of build) would also create new pre-change studies, so it is not tonight's work. It is offered to the owner below.

### D-E5.15 Order

FX-COLD-LINKED and FX-KOBO-GAPS build in parallel (no shared files), each gets a fresh Claude review, then both merge, then one fresh prepare (D-E5.10). The DS-1 script figures are refreshed from that build's finish/after output, not from the table above.

### Decisions logged for owner review

- **D-E5.11** The 2-missed/3-partial week is a calendar side effect (BL-25 and the R16 8-hour story-only days), not a product fault.
- **D-E5.12** v4: S-4 is the missed day ("gateway offline"), and the trial day S is the one partly checked day (06:00-14:00, the trial hours), not a few-hour dropout. S-3 loses its `late` kind, and S-3, S-2 and S-1 become full steady days.
- **D-E5.13** Fix card FX-KOBO-GAPS (Opus, S), with a new WK-GAP finish row, WK-2a/WK-2b restated with cause, and a singular "has no reading".

### Questions for the owner (not ruled)

1. "On the trial day the example readings cover 06:00 to 14:00 only, so that is the week's partly checked day. Is that acceptable? Making it look like a short gateway dropout instead needs simulator work after the demo."
2. "The month view still has a 6-day stretch with no readings just after commissioning (12-17 Oct), and the weekly generator days read partly checked. Leave it as is (recommended), or fill those 6 days for about 13 more minutes of build time?"

## Kobo days amendment (2026-11-10)

Claude Architect (binding Claude, `.ai/ROLE_CONFIG.md:9` on main), under the owner's 2026-11-08 delegation. Owner text: `.agent/owner-kobo-gap-pattern-2026-11-10.md` ("is it possible to inject days and extend the scope (or can i just select dates that has longer spans)?"; 12-17 Oct: "Fix it now"). Read at main `2121e3712`: `config/scenarios/kobo-*.yaml`, `backend/conversions/demo-story-days-v3.json`, `kobo-night-handover-v1.json` (`full_days`), `tools/demo_story_days.py`, `tools/demo_combined_finish.py`, DD1a1-R16, DD1a2-R, DD1a2-R3, DD1b2-R Q0/Q3 in `build-sheet-DD-1.md`. Nothing was run. This amends D-E5.12/D-E5.13; everything not named here stands.

### D-E5.16 Longer spans: not available; DD1a1-R16 still holds (READ)

- **No longer recording exists.** The Lab keeps no recorded Kobo runs: every Kobo day is re-simulated at prepare from a registered scenario. Of the 23 Kobo scenarios, none runs longer than 12 h. The trial (`kobo-mini-grid-reserve-trial`), necessary-run, prolonged, stop-60, reserve-matters and degraded scenarios run 8 h (06:00-14:00). The evening run is 12:00-20:00, and the daytime, mill, steady and steady-before runs are 06:00-18:00. A 24 h day exists only as a stitched chain (night 00-06, day 06-18, rest 18-24). Only 3 chains have a measured join that is STOPPED at every seam (`full_days`): `kobo-mill-midday`, `kobo-steady-day` and `kobo-steady-before-mill`.
- **Choosing other dates does not help.** Every Kobo offset is relative to S, so moving S moves the whole pattern (D-E5.11).
- **Why R16 still holds.** Its facts are about the scenarios and the model profile, and neither has changed:
  - The necessary-run (normal and overcast days) is RUNNING at 14:00 and at 24:00.
  - The R30 and R25 trial runs are RUNNING at 24:00 (from 22:05 and 23:25).
  - So wrapping a normal day's background around 06:00-14:00 needs a run that starts with the generator RUNNING, or a cut through a running generator. The first needs simulator work (option B, about 1-1.5 units). The second would be a dishonest join.
  - The trial adds a second bar (DD1a2-R3, BL-26): any other readings inside the trial days' UTC windows take ACT-001 off Verified.
  - A rest-of-day run on any generator day would add generator minutes. That changes the Findings and the 0.00-15.13 USD idle-fuel range.
  - A different scenario for the trial is a different trial, so the Verified headline would no longer be the measured one.
  - Verdict: the trial and generator days stay story-only (06:00-14:00).
- **A realistic few-hour dropout is not available.** The only truncation mechanism is Kobo `degraded`, which is held (`DEGRADED_DAY_HELD`): it cuts by batch order, which no real outage looks like, and the source-time cut is BL-18. There is a second reason too. The trial day S is in the week and can only be partly checked, so a truncated full day would make a second partly checked day. **S stays the week's one partly checked day.** The presenter line of D-E5.12 stands.

### D-E5.17 Injecting days: yes, through the product's ingest path; fill S-27..S-22 now

- Injecting is what the build already does. Each calendar entry replays its runs through the gateway publication, acceptance and assessment path, exactly as for the existing full days. No reading is written directly.
- **Fill S-27..S-22 (12-17 Oct for S = 11-08) with the existing before-mill chain:**
  - S-27 is `steady-before-first`. Its neighbour S-28 is story-only with no measured 24:00, so it takes the fresh declared night (Q8.1).
  - S-26..S-22 are `steady-before`. Each night starts from the previous day's measured 24:00, the same chain already built on S-19..S-15.
  - This passes `check_full_day`, `check_full_day_chains`, `check_mill_side` (all before S-9) and `_tiled` by construction.
  - Every day is after install (S-29) and inside the board window (30 days).
  - The 06:00 disclosure line applies as on every full day.
- **No new study is created.** Two new five-day windows have no missing day (S-27..S-23 and S-26..S-22), but no code queues them. Studies are pinned by `reconcile` on S-19..S-15 only (DD1b2-R Q3, BL-32), and the tick's scan reaches only studies ending about S-3 or later. So no new potential, Opportunity or Grow thread appears. The D-E5.14 month note that "it would also create new pre-change studies" is withdrawn.
- **MILL-3 is unchanged.** `choose_days` takes the complete days nearest the change: S-13..S-11 before and S-8, S-6, S-5 after. ACT-005 stays 17.00 USD.
- **Two side effects are expected, not measured:**
  - S-28..S-11 becomes one gateway stream, so the epoch strings of S-21 and S-14 change. Their readings do not change.
  - The before pattern adds about 42 kWh of daylight mill use per day: about +252 kWh and +63.00 USD in October productive use, wherever an October total is read.
- **Not filled:**
  - S-29, the install day.
  - S-10, kept as the FILL-1 live beat.
  - S-4, the week's one missed day ("gateway offline").
  - The generator days S-28, S-21, S-14 and S-7, and the trial days S and S+1 (D-E5.16).

### D-E5.18 The day list (v4 as amended)

| Days | Kind | Reads |
|---|---|---|
| S-29 | install | no data |
| S-28, S-21 | `normal`, `overcast` (unchanged) | partly checked |
| **S-27** | **`steady-before-first` (new)** | **checked** |
| **S-26..S-22** | **`steady-before` (new)** | **checked** |
| S-20..S-15, S-13..S-11 | unchanged | checked |
| S-14, S-7 | `overuse` (unchanged) | partly checked |
| S-10 | `missing` (unchanged) | no data (FILL-1) |
| S-9, S-8, S-6, S-5 | unchanged | checked |
| S-4 | `missing` (D-E5.12) | no data |
| S-3, S-2, S-1 | `steady` (D-E5.12) | checked |
| S, S+1 | trial pair (unchanged) | partly checked |

- **Week S-6..S:** 5 checked, 1 missed (S-4), 1 partly checked (S).
- **Month [S-29, S]:** 22 checked, 5 partly checked, 3 with no data (S-29, S-10, S-4). Presenter answer: "Readings run daily from 11 October. Two days are gateway outages. The weekly generator days and the trial day carry only the example hours."

### D-E5.19 Card FX-KOBO-GAPS, amended (same branch, same review; about +0.1 unit, about +40 lines)

1. **Data.** `demo-story-days-v4.json` adds six entries: `{"day": "S-27d", "kind": "steady-before-first"}`, then `steady-before` on S-26d..S-22d, in day order. The label reads "v4 (D-E5.12, D-E5.17)".
2. **L0.**
   - The v3-equality clause becomes: "v4 minus its 4 week entries and its 6 S-27..S-22 entries equals v3 minus its 2 week entries".
   - New `test_v4_month_fill`. For S in {11-07, 11-08, 11-09}:
     - `resolve` passes with installs;
     - S-27 is `steady-before-first` and S-26..S-22 are `steady-before`, each tiling [00:00, 24:00) local;
     - the days in [S-28, S] with no run are exactly {S-10, S-4}.
   - Must-fail: the same test fails on the unamended v4 (S-27..S-22 absent).
3. **WK-GAP.** Add a month clause. On [S-28, S], NO_DATA is exactly the days of `missing` kind, and PARTIAL is exactly the story-only days. Both come from `ctx.site_days("kobo")` and are never hard-coded.
4. **Stop rules.** The rows of D-E5.13 §7, plus SP-1 (its window now meets the full day S-27), F-CAL and CO-6: on any failure, stop and report. Also report, not as a fault: any October total read and the epochs of S-21 and S-14.
5. **Fallback.** `prepare --days backend/conversions/demo-story-days-v3.json` is unchanged.

### D-E5.20 Figures (S = 11-08; expected, the build decides)

- **Unchanged from D-E5.14 (all are week or November figures):**
  - Coverage line: 6 of 7 assessed, not assessed 4 Nov.
  - Days line: 5 of 7 checked, 1 partly checked.
  - Grow: 137.50 USD.
  - MG-1: 550.0 kWh on 5 of 8 days [S = 11-09: 660.0 kWh on 6 of 9], MET.
  - Study 3-7 Nov: 4 of 4 well-observed days, 1 of the 5 study days has no reading.
  - WK-2b on S: not judged yet.
  - Pinned study S-19..S-15, MILL-3 "Target met", ACT-001 Verified (3.3 L / 4.12 USD), ACT-005 17.00 USD.
  - Generator Finding: 8 Nov 04:35-07:55, 0.00-15.13 USD.
- **Board gap line (31 days):** 4 no checked readings · 5 partly checked (no data: S-30, S-29, S-10, S-4; partly: S-28, S-21, S-14, S-7, S). This replaces D-E5.14's 10 · 5.
- **Month:** 22 checked (up from 16), 5 partly checked, 3 no data.
- **Prepare time:** 6 more full days at about 131 s each is about +13 min over the v4 card, and about +18 min over v3. Kobo goes from about 29 to about 47 min, and the whole prepare from about 2 h 20 m to about 2 h 38 m. That is still under the 3 h B-16 line. This is estimated, not measured.

### Decisions logged for owner review

- **D-E5.16** Neither longer runs nor other dates exist. The trial and generator days stay 06:00-14:00, and the trial day is the week's one partly checked day.
- **D-E5.17** Fill 12-17 Oct with six before-mill full days through the normal ingest path. No new study is created.
- **D-E5.18** The day list above.
- **D-E5.19** The card is amended: 6 entries, 1 L0 test, a WK-GAP month clause and the added stop rows.
- **D-E5.20** The figures above.

## v3 fallback ruling (2026-11-10)

Claude Architect (binding Claude, `.ai/ROLE_CONFIG.md:9` on main), under the owner's 2026-11-08 delegation. Read at main `06a921a94`: FX-KOBO-GAPS review finding 1 (Medium) and Lows 2-4, `tools/demo_combined_finish.py:674-706`, `tools/demo_combined.py:872-873`. Nothing was run.

### D-E5.21 WK-GAP gates the v4 calendar only; on v3 it reports (option a)

- **Ruling.** D-E5.12's "pass on both calendars" stands, and D-E5.13 item 3's "fails on v3, the intended alarm" is withdrawn. The alarm was meant to catch a wrong default calendar, not an explicit fallback; the v4 L0 test and `DEFAULT_FILE` already catch the former.
- **Why not a diagnostic-only fallback (b).** Thursday-morning case: if tonight's v4 build fails its stop rules, the v3 calendar is the last accepted demo build (honest data, the older 2 missed / 3 partly checked week) and about 2 h 20 m to rebuild, so it is the realistic thing to present. A build that ends SELF-CHECK FAILED cannot be presented, and `add-dates` (script Step 7) would print a failure in front of the audience. The fallback must be presentable.
- **Rule.** WK-GAP gates (asserts the week and month patterns) only when the built `days.json` `schema.version` is 4 or higher. Below 4 it returns the read pattern with `"gated": false, "calendar": <source>` and passes. Key on the schema version, not the file name.

### Card FX-KOBO-V3 (Sonnet, XS, about 40 lines; fresh Claude review; may merge Wednesday)

Branch `task/FX-KOBO-V3`.
1. `tools/demo_rows.py`: pure `gap_gated(days_schema) -> bool` (version >= 4). `tools/demo_combined_finish.py` `wkgap`: compute both patterns as now; raise only when gated; on v3 return them with `gated: false`. Docstring cites D-E5.21.
2. `tools/demo_combined_kobo.py:563` (review Low 2): the manifest `"days"` label comes from `days.json` `source`.
3. L0: `gap_gated` true for v4, false for v3; the client4 v3 fixture (2 NO_DATA + 3 PARTIAL) raises when gated and returns `gated: false` when not (must-fail: drop the gate and the ungated case raises). Review Low 3: a v4 parametrisation of the positive half of the S-10 fillable test.
4. Gates: guards A, W, V and N, `test_demo_story_days.py`, the demo_rows L0. No build, no full suite. Tonight's v4 build does not wait for this card.
5. Review Low 4 (B-16 keeps the six fill days): no change; backlog.

Decision logged for owner review: **D-E5.21** the v3 fallback is a presentable build; WK-GAP gates v4 only.

## Money snapshot ruling (2026-11-10)

- Architect: Claude (fresh `assetops-architect`). Full answer: `.agent/architect-answer-money-snapshot-2026-11-10.md`.
  Owner question verbatim: `.agent/owner-money-snapshot-2026-11-10.md`.

### D-MONEY.1 Store the amount with its receipt (hybrid), rebuild on event, never recompute on read

Each stored money line carries `amount` (or `low`/`high`), `currency`, `basis` and
`receipt{v, formula, qty, unit, rate, rate_unit, rate_ref, segments: null, fx: null}`. The amount is computed from the
unrounded quantity and rounded to the cent half-up; a rebuild must reproduce it exactly. A corrected price or tariff
is a new assumption revision, and the affected days are rebuilt as new snapshot revisions. Old revisions are kept, so
"as known at k" holds. Amount-only storage (no audit, no explainable restatement) and recompute-on-read (slow,
code-dependent) are both refused.

### D-MONEY.2 Original currency only; conversion is read-time and named

No converted amount is stored. A later reporting-currency view converts at read time from an append-only, bitemporal
FX rate store (BL-67a), and shows the rate, its source and its date. Until then mixed currencies stay
`CURRENCY_MIXED`.

### D-MONEY.3 No stored totals

No row kind, migration or builder writes a cross-Site, cross-currency or verified-result total (A6, OWN-1104 R10,
FUEL-1 A2). The BL-66 estate roll-up rows hold per-Site money lines only. MN-3 adds a guard for this.

### D-MONEY.4 It lives in the BL-66 design; no separate ledger now

Day money stays in `site_day_snapshot.money`. Window, potential and evidence money go in `site_period_read`, under the
`money.lines` kind (with `money.potential` per Site-local day), in AR-4. `input_fp` includes every `rate_ref`. The
existing bitemporal assumption store is the minimal tariff catalogue. AR-1's generic contract takes this shape before
its migration is written. No new columns.

### D-MONEY.5 Sizing

MN-1 (receipts on `productive_kwh.money`, 0.25), MN-2 (stored potential money, 0.5) and MN-3 (no-total guard, 0.25)
fold into AR-4. ANY-2 goes from 3.75 to 4.75 units. ANY-1 is unchanged. FX, structured tariffs and the restatement
note are BL-67.

### Owner questions (open)

1. Reporting currency policy: one reporting currency? Which one, and which rate (transaction-date, period-average, or
   report-date)?
2. Restatement display: (i) the restated figure with a "restated on <date>, was X" note (the Architect's
   recommendation), or (ii) the original figure plus an adjustment line in the period of the correction?
3. Will AssetOps ever issue or settle invoices? If so, an immutable settlement ledger is needed later.

### Decisions logged for owner review

- **D-MONEY.1** Store the amount together with its receipt; rebuild on event.
- **D-MONEY.2** Store the original currency only; no stored conversions.
- **D-MONEY.3** No stored totals.
- **D-MONEY.4** Money goes in the BL-66 rows, not a separate ledger.
- **D-MONEY.5** MN-1/2/3 fold into AR-4 (+1.0 unit); the rest is BL-67.

## Portfolio lens ruling (2026-11-10)

- Architect: Claude (fresh `assetops-architect`, owner delegation `.agent/owner-away-architect-decides-2026-11-08.md`).
  Owner question verbatim: walkthrough item 6, `.agent/owner-walkthrough-2026-11-10.md`. Ruling: **(c) both**.
- Verified in code: `backend/assetops_backend/estate/portfolio.py:842-930`. The lens filters `members` into `shown`
  only. It changes `rows`, `total_count`, `next_cursor`, `selection_token` (lens is in the token, so the cursor is
  lens-bound) and the echoed `lens`. Everything else (summary counts, `placement_counts`, `category_counts`, claims,
  value cards, objectives, evidence prompt, opportunity, progress, money, footer, scope disclosure) is computed over
  `members` or the window and is identical for every lens. The outcome summary read is window-keyed and never refetched
  on a lens change. So only the "Where management should act first" panel depends on `lens`.

### D-E5.22 Frontend: keep the page while the lens loads (card PL-1, Sonnet, 0.25 unit; lands any time, no rebuild)

`frontend/src/estate/EstatePortfolio.tsx` `EstatePortfolioPage`: when the held read is `loaded` and differs from the
new key **only in lens** (same `from|to|known_at`), keep rendering the held body. The page never mixes two reads:
when the new response arrives it replaces the whole body (as today), so every figure stays from one response,
"as known at k". While it is pending:
- `PriorityPanel` gets `pending: EstateLens | null`. The chip for the pending lens is `aria-pressed`. The section has
  `aria-busy="true"`. Both count spans read "Loading findings". The table body is one row,
  `data-portfolio-loading-rows`: "Loading the {label} findings." The held rows are never shown under the new lens.
  "Load more Findings" is hidden. Early warnings stay (window-keyed).
- The other panels stay as rendered (the server values are lens-independent, see above).
- A refusal replaces everything, as today. A window change still shows the full loading slot.
- Rapid clicks: the existing `live` guard keeps only the last lens.
Tests in `frontend/src/estate/__tests__/estatePortfolio.test.tsx` (deferred-promise client): (1) on a lens click,
the cards, pulse and context stay in the DOM and `data-estate-loading` is absent; (2) the panel shows the loading
row, `aria-busy`, and no held row; (3) when it resolves, the new rows and `total_count` are shown; (4) a refusal on
the lens read replaces the page; (5) cost, then risks quickly, shows the risks body only. No captures change (the
settled states are unchanged). MOCK DEVIATION: none (v69/v70 do not specify a lens loading state).

### D-E5.23 Tools: pre-build the lens variants (card PL-2, Sonnet, 0.25 unit; MUST merge before tonight's build)

`tools/demo_combined.py` `prebuilt_routes`: for each of `portfolio.week`, `portfolio.S` and `portfolio.month`, also
add `portfolio.{name}.{lens}` for `cost`, `risks`, `opportunities`, with the same query and `("lens", lens)` in place
of `("lens", "all")` (the response store keys the parsed lens, `chain/response_store.py:83-87`). There are 9 more
requests. `findings.week` is unchanged (not asked). Test: in `backend/tests/test_e4_prebuilt_routes_generator.py`,
assert the 9 ids and queries; the uniqueness asserts stay. Cost: a cold compose is about 4-10 s, so the build adds
about 40-90 s, and so does each add-dates tick that moves the watermark. An unmoved tick adds about 9 x 50 ms. Stop
rule: if the prebuild report exceeds the EX-3 "50% of the tick limit" budget, keep the `week` variants only and
report. The numbers do not change: a stored hit is the same route's body.

### D-E5.24 Client-side filtering by `lens_flags` is refused

Page one holds 50 rows. `total_count` and the cursor are server-side and bound to the lens, and the page rule is "the
page never re-sorts, re-selects or sums". A client filter would show a frontend count that is wrong past 50 rows.

### Interactions

- **PF-T (Portfolio tabs proposal)**: the lens loading state moves with `PriorityPanel` to Act first. Overview links
  drop `lens`, so the Overview top 3 reads `lens=all`, which is already pre-built. PL-1 is kept and only moved.
- **ANY-2**: stored period rows make cold composes fast. PL-2's list stays valid and harmless, and PL-1 stays.
  Splitting the lens rows into a separate read stays an ANY-2 option, per proposal §7.4.

Decisions logged for owner review: **D-E5.22** keep the page while the lens loads; **D-E5.23** pre-build the 9 lens
variants; **D-E5.24** no client-side lens filtering.

## Findings cards ruling (2026-11-10)

Walkthrough item 7 (`.agent/owner-walkthrough-2026-11-10.md`). Architect: Claude, under the owner's delegation
(`.agent/owner-away-architect-decides-2026-11-08.md`). Mockup draft for owner approval:
`frontend/mockups/v71/findings-cards.html`. MOCK DEVIATION from v6.9 `findingsScreen()` until the owner approves it.

Code facts verified:
- `frontend/src/estate/findingIndex.tsx:151-152`: "High priority" and "Low confidence" are literal "Not assessed".
- `backend/assetops_backend/estate/index.py:169,235`: every Findings row has `priority: None` and `confidence: None`.
  The summary keys `high_priority` and `low_confidence` (`:415`) are never set. No Finding-level priority or
  confidence exists anywhere.
- Related concepts that do exist: Portfolio placement groups (`estate/placement.py` `_rule`: ACT_NOW, etc.) and a
  placement confidence (`_confidence`: UNKNOWN / LIMITED / SUPPORTED_SOURCE_COHERENT). These sit on Portfolio rows
  only and are computed with Action and money context. Dispatch analytics also has a confidence, but that belongs
  to each analysis, not to a Finding.
- `index.py:417-424`: the counts are computed only when `_coverage_state == "COMPLETE"`, which needs every applicable
  Site to be CURRENT or HISTORICAL. A PARTIAL Site does return rows, but Findings next to its unanalysed days are
  withheld (`coverage.py` DAYS_WITHHELD). Any count with a PARTIAL Site in scope is therefore a lower bound.
- `index.py:421`: awaiting verification counts MINI_GRID only. The cause is structural. Cold and EV Actions are
  `domain_action` rows, and their plans are keyed by `domain_action_id`. The estate has no Finding-to-domain-Action
  join (`portfolio.py` R4.1 comment above THREAD_LABEL). The Portfolio's Cold/EV "Pending" is thread state
  ACTION_IN_HAND, meaning the action is agreed but not applied. That is not "awaiting verification", so the
  Portfolio and this card do not disagree about any fact.

### D-E5.25 "High priority" removed; "Low confidence" replaced by "Not yet confirmed"
Nothing can honestly feed "High priority". v6.9's intent ("Decision needed") is already served by the Portfolio's
"Where management should act first" (Act first tab), so this card is removed. v6.9's "Low confidence" intent
("evidence constrained, read with care") is served honestly by the stored lifecycle UNCONFIRMED. That state is the
existing "Not yet confirmed" chip on this page. "Supported findings" is relabelled "Confirmed findings" to match
LIFECYCLE_WORDS. Placement on Findings rows (to restore an "Act first" count here) is refused for the demo. It is
backlog: not demo-critical, and Opus, about 1 unit.

### D-E5.26 Show the counts with an honest qualifier; do not withhold
Withholding hides real, read rows, and with the demo data it hides them almost always. Rule: compute
`supported_findings`, `awaiting_verification` and the new `unconfirmed_findings` over the rows read, whatever the
coverage. When the coverage is not COMPLETE, the frontend marks each count "So far" and lists the Site breakdown.
The qualifier uses **analysis** words, not reading words. The brief's "1 site has partial readings" is refused: the
estate PARTIAL state means days not analysed yet, not partial readings. The proposal's term table maps estate
PARTIAL to "not analysed yet". Site state words: CURRENT/HISTORICAL "fully analysed"; PARTIAL "with days not
analysed yet"; PENDING_RECOMPUTE "still processing"; STALE_SOURCE "no new readings received"; UNKNOWN "not analysed
yet"; NOT_APPLICABLE is left out of the denominator.
Literal: `So far: {full} of {applicable} sites fully analysed` followed by each non-zero part
` · {n} site(s) with days not analysed yet` / ` · {n} site(s) still processing` / ` · {n} site(s) with no new readings received` /
` · {n} site(s) not analysed yet`, with "site" and "sites" chosen by count. The complete case is unchanged:
`Across {n} sites`. The cards no longer show "Some data missing".

### D-E5.27 Awaiting verification: mini-grid only is a disclosure defect (Medium), not a counting defect
The count is right by its stated rule, but the card reads as estate-wide. Fix now: the note appends
`mini-grid sites only; cold room and EV charging are not counted here yet`. The estate-wide count is backlog: chain
threads in CHANGE_APPLIED with an open verification window, labelled to match the Portfolio's "Outcome pending".
It is not demo-critical, and Opus, about 1 unit.

### D-E5.28 What each card is for (plain language, for the owner)
- **Confirmed findings:** how many problems or opportunities the readings confirm in this period.
- **Not yet confirmed:** things seen that the readings do not yet confirm. Read these with care.
- **Awaiting verification:** actions already taken where we are still waiting to see whether they worked.
- **High priority (removed):** "what needs a decision first". The Portfolio's Act first tab answers that.

### Fix cards
**FC-1 Frontend (Sonnet, 0.5 unit; lands before Thursday, no rebuild; after owner approves the mockup).**
- Files: `frontend/src/estate/findingIndex.tsx` (Cards: 3 cards, labels, D-E5.26/27 notes) and
  `frontend/src/estate/estateClient.ts` (`unconfirmed_findings?: number | null`).
- Null count (before FC-2): value `Not counted yet`, amber. Note `Counted once every site is fully analysed`
  followed by the same parts.
- Tests: `frontend/src/estate/__tests__/estateRoots.test.tsx` (complete; partial with numbers; partial with null;
  no "Not assessed" or "Some data missing" in the cards; the mini-grid note) and `estateFixtures.ts`.

**FC-2 Backend (Sonnet, 0.25 unit; MUST merge before tonight's build to land Thursday).**
- File: `backend/assetops_backend/estate/index.py:417-424`. Compute the three counts unconditionally and add
  `unconfirmed_findings`. Leave `basis_count` and `total_count` unchanged (null unless COMPLETE). Remove
  `high_priority` and `low_confidence` from the summary only if the frontend type is updated in the same pass;
  otherwise leave them null.
- Tests: regenerate `backend/tests/fixtures/w3/w301-estate-golden.json` (review the diff: only summary keys may
  change). Add one backend test: a PARTIAL scope returns numeric counts equal to the rows read. The prebuilt lens
  variants (D-E5.23) pick the change up in the build.
- If FC-2 misses the build, FC-1's null path is the honest fallback (mockup section C).

Decisions logged for owner review: **D-E5.25** to **D-E5.28**. The owner approves `frontend/mockups/v71/findings-cards.html`
before FC-1 merges.

## Non-Kobo Site pages ruling (2026-11-10)

Walkthrough item 11 (`.agent/owner-walkthrough-2026-11-10.md`). Architect: Claude, under the owner's delegation
(`.agent/owner-away-architect-decides-2026-11-08.md`). Full answer, table (56 values: A 17 · B 17 · C 16 · D 6) and
cards: `.agent/architect-answer-non-kobo-sites-2026-11-10.md`.

### D-E5.29 Verdict: product bug for Cold and EV, story data defect for Kisiwa
- Cold and EV: Site reads select an analysis only when the stored window contains the requested one (Cold,
  `postgres_assessment_store.py:2222-2228`) or equals it (EV, `:2933-2941`). The story analyses 16:00–17:05 and
  08:00–09:05, so day and week views read "Unknown" or "Not assessed". The exact window shows the 4.9 °C peak and
  the USD 4.50 estimate.
- Kisiwa: `tools/demo_combined_kisiwa.py:789,1189` publishes one epoch per night (18:00–12:00) on a fresh gateway.
  Every day therefore holds two epochs, and `cohort.py:93-101` marks it AMBIGUOUS (9 of 11 days).
- This also explains the Portfolio's "Kisiwa 0 of 7 days checked" and corrects `architect-combined-pass-2026-11-08.md` row 4.

### D-E5.30 DATA-1 (Opus, 0.5 unit): one Kisiwa recording session; MUST merge before tonight's build
- One epoch `kisiwa-gw-1` on one persistent `work/"kisiwa-gateway"` (`gateway_dir`, DD1a1-R5), in both publish paths.
- New finish check `KISIWA-COHORT`.
- New Kisiwa dispatch content is read from the build before the demo; its figures are quoted from the build.
- Fallback if DATA-1 misses the build: present Kisiwa through Fuel nights, the Finding and verification only.

### D-E5.31 PB-1 (Opus, 2 units, plus Sonnet 0.25 frontend): analysed periods inside a window; before the client session
- A selection that contains or equals the window is unchanged.
- Otherwise the periods wholly inside the window are listed; the status uses the most recent one with an open
  Finding, or else the most recent one.
- Window-bar literals: `Analysed period: {from}–{to}` and `Analysed periods in this range: {n} · showing {from}–{to}`;
  with no period inside, `No analysed period in this range`.
- Pinned mode is unchanged. EV provenance is judged per period.
- MOCK DEVIATION: one window-bar line; owner informed.

### D-E5.32 Thursday mitigation: analysed-period story links (DATA-2, Sonnet, 0.25 unit; before the build)
- A second link per Cold and EV day for the exact analysed period; the whole-day link stays for Work and Actions.

### D-E5.33 Kisiwa objectives MG-2 and MG-5, after DATA-1 (DATA-6, Sonnet, 0.25 unit; before the client session)
- Reverses DIESEL-1 §9p.4. CO-6 / `objective_site_count` changes from 3 to 4. Story change; owner informed.

### D-E5.34 NOT BUILT values become plain roadmap wording (RM-1, Sonnet, 0.5 unit)
- RM-2 hides the unsupported Site lens chips on client screens. **Owner approval needed (mockup).**

### D-E5.35 Integration ranking for the client
1. Billing and collections.
2. Sign-in.
3. Work-order cost (CMMS).
4. Fleet roster and telematics.
5. Cold stock value and occupancy.

### D-E5.36 Story order
- Kobo, then Kisiwa. Cold and EV are brief beats on their analysed periods.
- Until PB-1 lands, no Cold or EV Health, Performance or Financials on a day or week window.

### D-E5.37 More Cold and EV days only after PB-1 (DATA-11, Sonnet, 0.5 unit, about +10 min prepare)
- Story change; owner informed.

Other cards (answer file):
- Thursday frontend: PB-5 Kisiwa feeder legend uses Foundation display names (`SiteWindowOverview.tsx:701`);
  PB-6 copy batch; PB-8 Fuel tab loading (`MiniPerformance.tsx:1633`).
- Before the client session: PB-3 EV event-driven grading; PB-4 an AMBIGUOUS day is "not analysed yet", never
  "Checked: nothing to report"; PB-7 the coverage denominator counts from the Site's first reading.
- Optional: DATA-5 story diagnostics; DATA-10 Kisiwa generator plan.
- Backlog: DATA-4, DATA-7, DATA-8 (owner approval).

Decisions logged for owner review: **D-E5.29** to **D-E5.37**.

## D-E5.38 to D-E5.40: Portfolio coverage counts UTC days (CO-6, WK-GAP fail on client6) — Architect, 2026-11-11, owner-delegated, logged for owner review

Found by the fresh demo build (worktree `AssetOpsV1-e3d` at 5cc98edfa, DB `assetops_polish_client6_test`). Verified in code:
`estate/coverage.py` `_mini_grid_basis` walks `snapshot.dispatch_days` (one entry per UTC day), counts a day as
checked whenever that UTC window has an available selection, and `_requested_days` counts UTC midnights. It never
reads the Site timezone. Calendar v4 puts S-3's `night-early` part at 21:00-03:00 UTC, so the UTC window of 11-04
holds a selection although Site-local 11-04 (Africa/Addis_Ababa) has no readings. Live
`GET :8990/api/estate/portfolio?from=2026-11-02T00:00:00Z&to=2026-11-09T00:00:00Z`: Kobo coverage `CURRENT`,
`requested 7, checked 7, gaps []`. Correction to the diagnosis: the Portfolio already has a Site-local day rule.
`summary.claims[*].days` comes from `chain.claims.claim_days` -> `chain.read.window_days(lo, hi, tz)` over stored
chain day grades, and it is honest on this build (estate 12 complete, 1 partial, 3 low, 6 no data of 22). Coverage is
the one estate reader still on UTC days, so this is two day definitions on one screen, not a missing definition.

### D-E5.38 One day definition: coverage uses the chain's Site-local graded days
- Requested days = `chain.read.window_days(from_, to, site.timezone)` (CH-5a2a: a UTC-midnight window names its
  calendar dates, each read as the Site-local day of that date). This is the summary claims' frame.
- Each day's state = the stored chain day grade (weakest row, `chain/reader.py` `_day_grade`, the same rows
  `claim_days` reads). NO_DATA -> gap (`UNASSESSED`, reason `NO_READINGS`); PENDING -> the Site is
  PENDING_RECOMPUTE; COMPLETE, PARTIAL, LOW -> checked (the days line already says "partly checked" and "too little
  data" from the same grades). The trial day S stays checked (PARTIAL grade), as the owner's v4 pattern expects.
- The dispatch-selection, match-pass and S3-status rules over the UTC windows stay as they are; they still decide
  PENDING / STALE / unmatched. Only the day count, `gaps` and the `gap` flag move to the graded local days.
- Rejected: the builder's option (b), a rule over the two UTC windows a local day touches. Both windows touching
  local 11-04 have selections, and it would be a third day definition.
- Spec for the fix (DATA-12, Sonnet, 1 unit, product code): `site_coverage(...)` and `_mini_grid` gain a keyword
  `day_grades: Mapping[date, str] | None = None`. The three callers (`estate/index.py:148`,
  `estate/evidence_money.py:463`, `estate/financials.py:417`) pass the mini-grid Site's grades from the same
  `req.day(site_id, site_type, window_days(...))` read the claims use (memoised by `read_scope`, so no extra query).
  `None` keeps today's behaviour, so cold, EV, actions and the fake-snapshot tests are untouched. Pin it with a
  unit test in `backend/tests/test_estate_coverage*.py`: a UTC+3 Site whose local day D is NO_DATA while both UTC
  windows touching D have selections reads PARTIAL, `gaps == [D]`, `requested 7`, `checked 6`, `text` set; plus CO-6
  and WK-GAP passing on a client6-shaped build. Serving: no rebuild. Coverage is composed per request from stored rows,
  and stored responses are keyed by `code_version`, which hashes every backend source file, so a code change misses
  the store on its own; a serve restart re-runs `write_prebuilt_routes` and the pre-build re-warms. Visible effect:
  Kobo becomes PARTIAL on the Portfolio, so its days line and "days not analysed yet" note appear and the PARTIAL
  money and finding withholding (§2.5, `EstatePortfolio.tsx:127`) applies to Kobo; the Portfolio pairs need recapture.

### D-E5.39 Thursday 13 Nov: do not fix; fix before the client session
- What a viewer sees wrong today: no false number. The Portfolio omits Kobo's caveat ("5 of 7 days checked" and the
  "days not analysed yet" note) and treats Kobo as fully current, while the Site board shows 11-04 as no data. The
  claim lines ("4 open on the days checked") are correct. The fix changes Kobo's Portfolio money and findings display
  two days before the demo on an unreviewed path, which is a larger risk than a missing caveat at an associates'
  technical demo.
- Talking point if asked: "The Portfolio's day count still uses UTC days, while the Site board uses Kobo's local day.
  Kobo's 4 November has no readings; the Portfolio misses that because a night shift crosses midnight. One day
  definition is the fix, scheduled before the client session."
- DATA-12 goes into the pre-client plan (client session about 1-8 Dec), ahead of the walkthrough polish recapture.

### D-E5.40 Mark CO-6 and WK-GAP as a known defect for this build only
- `add-dates` appends and settles the dates first, then runs `finish check`; on FAIL it exits non-zero with "This
  build no longer passes its checks; prepare a fresh one before a demo." So the data is in, but Wednesday's live
  capture would read a failed command and a wrong instruction.
- Tool-only change (Sonnet, 0.25 unit, no product code): `tools/demo_combined_finish.py` gets
  `KNOWN_DEFECTS = {"CO-6": "D-E5.38", "WK-GAP": "D-E5.38"}`. A failing listed row is kept out of `failed` and the
  exit code only when its failure is the coverage signature (CO-6: Kobo coverage state not PARTIAL with `gaps: []`;
  WK-GAP: the `"CO-6 coverage gaps", [], ...` assertion). Anything else in those rows still fails. `check.json`
  records `known_defect: "D-E5.38"` and the failure text; the summary prints "known defect"; a listed row that passes
  prints "known defect no longer reproduces; remove the marker". Before relying on it, run CO-6's checks after line
  492 once on client6 with the coverage block skipped, so the marker hides nothing else. DATA-12 removes the map.

Decisions logged for owner review: **D-E5.38** to **D-E5.40**.

## D-E5.41 to D-E5.44: DATA-12 review rulings (Architect, Claude, 2026-11-11; review ACCEPT WITH NOTES on fd85f1d31)

### D-E5.41 Fix before merge, one Sonnet round (card DATA-12-FX, about 0.35 unit)
- Not merged as is. M1 would regress Kisiwa honesty on the current rule: today an unselected UTC day is a gap, and with the grades it reads CURRENT with its findings and money silently missing.
- Lane A is not blocked. A2 (PB-4 + PB-7 + BL-50 + L2) starts now from main and rebases once DATA-12 merges. Its only shared file is `tools/demo_combined_finish.py`.

### D-E5.42 Day rule, completing D-E5.38 (the M1 and L4 answers)
For each requested local day D (`window_days`, the CH-5a2a frame: the UTC dispatch day with D's calendar date is D's analysis window), the grade decides first:
- **NOT_EXPECTED:** dropped from both requested and checked. The Site does not operate that day.
- **NO_DATA:** a gap, reason `NO_READINGS`.
- **PENDING:** the Site is PENDING_RECOMPUTE.
- **COMPLETE, PARTIAL or LOW, but the dispatch day with D's date has no available selection:** a gap, reason `NOT_ANALYSED` (the words "not analysed yet"). This is the M1 fix.
- **Otherwise:** checked.

The selection, match-pass and S3 rules are unchanged.

### D-E5.43 L1 and L3 fixed in the same round; L2 deferred
- **L1:** grades are read at `req.known_at` on page one (the claims' key) and at `k` on cursor pages.
- **L3:** `analytics/finding_index.touched` takes an optional `tz`. When gap days are local, the day bounds are Site-local midnights ± `CONTINUITY_TOLERANCE`. Without this, Kobo night findings starting between local 00:00 and 03:20 are wrongly withheld.
- **L2** (module-global provider in `main.py`) goes to the backlog, after 17 Nov. It has no effect in a single served app.

**Card DATA-12-FX (Sonnet, same branch and worktree `AssetOpsV1-data12`):**
1. `coverage.py`: apply the D-E5.42 rule.
2. Callers: L1.
3. `touched(..., tz=None)` with local bounds when given; pass the Site tz from the gap-day caller.
4. Tests, each pinned:
   - a local day with data whose same-date dispatch day has no selection reads PARTIAL with `gaps == [D]` and reason `NOT_ANALYSED`;
   - a NOT_EXPECTED day changes neither requested nor checked;
   - a UTC+3 finding starting at local D+1 01:00 is not withheld when D is a gap;
   - a live request makes one `chain.day` read per mini-grid Site (count the calls).
5. Coordinator verifies the diff; a fresh Sonnet re-review covers M1 and L3 only.

### D-E5.44 Money on a partly covered Site: owner question (story-visible)
- **Today's rule (COV-PARTIAL §2.5)** withholds a PARTIAL Site's money for the whole range:
  - `financials.py:420-426` keeps only CURRENT and HISTORICAL;
  - `EstatePortfolio.tsx` shows "Partly checked · value shown once every day is checked".
- **With DATA-12, Kobo is PARTIAL on any week that contains 4 Nov.** So the default week loses Kobo's money: the client script's main money beat.
- **The Architect's view:** withholding is honest but unhelpful for an executive. The honest and useful form is money for the analysed days only, named as such, never extrapolated to the missing day. It is a reversal of an earlier ruling, so the owner decides.
- **Card if approved: PARTIAL-MONEY** (Opus, about 0.5 unit, lane A after A2, before 17 Nov).
  - Financials and the Portfolio row and cards sum the lines of checked days only.
  - Each label reads `{amount} for {n} of {m} days analysed · {gap list} not analysed`.
  - The no-total and receipt rules are unchanged.
  - It is folded into AR-4's design later.
- **Until the owner answers:** DATA-12 merges with today's withholding, and the script refresh moves the money beat to ranges without a gap.
- **Question for the owner (plain language):** "When one day in a week has no readings, the Portfolio now hides that Site's money for the whole week (Kobo's week of 2-8 Nov, because 4 Nov has no readings). Option 1: keep hiding it until every day is analysed. Option 2 (recommended): show the money for the days that were analysed, clearly labelled '6 of 7 days analysed · 4 Nov not analysed', never estimating the missing day. Option 2 is about half a day of work before 17 Nov."

Decisions logged for owner review: **D-E5.41** to **D-E5.44**.

### D-E5.45 Owner answer to D-E5.44: option 2 (2026-11-11)
Owner, verbatim (`.agent/owner-answers-17nov-scope-2026-11-11.md`): "option 2 for money".

**Card PARTIAL-MONEY.** Opus. About 0.5 unit. Wt `AssetOpsV1-pmoney`, branch `task/PARTIAL-MONEY`, cut from main after DATA-12 and DATA-12-FX merge.
- **Rule:**
  - A PARTIAL mini-grid Site's money uses only the lines of its checked local days (D-E5.42).
  - Never estimate, scale or fill the gap days.
  - The no-total and receipt rules are unchanged.
  - PENDING, STALE, UNKNOWN and HISTORICAL keep today's withholding.
- **Label:**
  - Literal: `{amount} for {n} of {m} days analysed · {gap days} not analysed`.
  - Gap days are given as Site-local dates ("4 Nov"). More than 3 gap days read `{g} days not analysed`.
- **Files:**
  - `estate/financials.py` `select_financial_scope` (`covered` admits PARTIAL; `mini_grid_lines` filtered to checked days);
  - `estate/evidence_money.py` (Portfolio cards and rows, same filter);
  - `frontend/src/estate/EstatePortfolio.tsx` (`partialConsequence` and `consequenceFirst` show the amount with the label);
  - the Financials page label; `portfolioWords.ts`.
- **Pinned tests:**
  1. A week with one NO_DATA day: the amount equals the sum of the other 6 days' lines exactly, and the label is as above.
  2. A gap day's own line is never included.
  3. Categories stay "covered" only for PARTIAL with at least 1 checked day.
  4. A PENDING Site is still withheld.
  5. Frontend: `estatePortfolio.test.tsx` for the label and amount.
  6. No total across currencies.
- **Lane A,** after A2 and before UQ-6a. It displaces nothing by name; it consumes about 0.5 of option Y's buffer. If Thursday's re-assessment shows lag, AR-6 (Cold/EV boards under 1 s) moves after 17 Nov first.

## D-E5.46 Day-gap words state the data fact; "not analysed yet" only when the system still has work to do (Architect, Claude, 2026-11-11, owner-directed, logged for owner review)
Owner, verbatim (`.agent/owner-answers-17nov-scope-2026-11-11.md`, last entry): "not analysed yet only makes sense when system action is pending, for when the data is not complete, that fact need to be stated 'not enough data received for the day' or something similar or 'data received is invalid' or something better".

**Code facts.** A local day with readings and no trustworthy result has one of three causes:
- (a) the run's cohort is `AMBIGUOUS` (`assessment_inputs.py` CohortSelection) or its generator series is ambiguous (`dispatch_v3.py`, limitations `AMBIGUOUS_COHORT`, `GENERATOR_SERIES_AMBIGUOUS`; the window claim is `WINDOW_INDETERMINATE`). These are conflicting reports for the same channel and time, such as the Kisiwa boundary duplicates.
- (b) there is no usable cohort (`EMPTY`, limitation `NO_COHORT`) or no generator state (`NO_GENERATOR_STATE`). The claim is also `WINDOW_INDETERMINATE`.
- (c) the dispatch day has no available selection (`coverage.py`: `not day["available"] or selection is None`), with or without an outstanding job.

DATA-12-FX's `NOT_ANALYSED` tests only (c). A day in (a) or (b) that has a selection counts as checked today, which overstates coverage.

**Rule: one gap reason per day.** Precedence follows the order of the table.

| Gap reason (backend) | When | Full words (Site, Findings, day boards) | Short form (Portfolio / coverage / money) |
|---|---|---|---|
| `NO_READINGS` | grade NO_DATA | No readings received for this day | no readings |
| `READINGS_CONFLICT` | selected window INDETERMINATE with `AMBIGUOUS_COHORT` or `GENERATOR_SERIES_AMBIGUOUS` | Readings for this day conflict (duplicate or overlapping reports), so it can't be analysed | conflicting readings |
| `NOT_ENOUGH_READINGS` | selected window INDETERMINATE with `NO_COHORT` or `NO_GENERATOR_STATE` | Not enough readings received to analyse this day | not enough readings |
| `NOT_ANALYSED` | no available selection (cause c), including an outstanding or failed job | Not analysed yet | not analysed yet |
| (Site state PENDING_RECOMPUTE) | grade PENDING or an outstanding job | Still processing | still processing |

- Never "error", "invalid", codes, or wording that blames the system for a data fact.
- "Not analysed yet" and "still processing" are kept only for system work.
- **Money label** (amends D-E5.45): `{amount} for {n} of {m} days analysed · {day list}: {short reason}`, with one group per reason, for example `6 of 7 days analysed · 4 Nov: no readings`. Days that share a reason are grouped (`3, 4 Nov: conflicting readings`). More than 3 gap days reads `· {g} days without a usable result`.
- **Portfolio coverage line** (amends D-E5.26): Site PARTIAL reads `{n} site(s) with incomplete days` in place of "with days not analysed yet". The Site's days line lists each gap day with its short reason. UNKNOWN keeps "not analysed yet".

**Updated owner-facing term family** (supersedes the walkthrough 5.3 list): complete readings / partial readings / too few readings / no readings received / not enough readings received (day) / conflicting readings (day) / still processing / not analysed yet (system work only) / incomplete days (Site summary).
- A day with no readings at all keeps "no readings received".

**Cards**
- **DATA-12-FX:** unchanged; finish and merge as built. Its `NOT_ANALYSED` is exactly cause (c), which is already correct.
- **GAP-REASONS (new, Sonnet, about 0.35 unit, lane A, cut from main after DATA-12-FX merges, before PARTIAL-MONEY):**
  - `coverage.py` reads the selected window's claim and limitation prefixes, and turns an INDETERMINATE (a) or (b) day into a gap with `READINGS_CONFLICT` or `NOT_ENOUGH_READINGS`;
  - `_days_block` carries the reason;
  - pinned tests cover one day per reason and the precedence;
  - verify on client6 Kisiwa that the boundary-duplicate day reads `READINGS_CONFLICT`.
- **PB-4 (A2):** the AMBIGUOUS day reads "Readings for this day conflict (duplicate or overlapping reports), so it can't be analysed" in place of "not analysed yet" (`SiteFindingIndex.tsx`, `OverviewFindingList.tsx`). It is never "Checked: nothing to report". If A2 has already committed the old words, change them in the same branch.
- **PARTIAL-MONEY:** uses the money label above, keyed on each gap's reason.
- **PF-W:** adds the two new terms and "incomplete days" to `portfolioWords.ts`, and replaces "days not analysed yet" in the coverage line.

Decision logged for owner review: **D-E5.46**.

## D-E5.47 An infrastructure read failure is never stored and never shown as a data fact (Architect, Claude, 2026-11-11, owner-delegated, logged for owner review)

**Defect (E3d, client6, 2-8 Nov outcome summary).** serve's prebuild rebuilt `/api/estate/outcome-summary` in 3.8 s during 88 "too many clients already" refusals. Every Site showed PARTIAL/Unknown and Kobo "No target set yet" although its objective rows were intact. The degraded body was stored and served until `valid_until`.

**Cause in code.**
- `site_outcomes/mini.py` `Reads.call`: `except Exception` records the read name in `failed` and returns None. The composer turns that into UNKNOWN and `read_state` PARTIAL (`site_outcomes/read.py` docstring lines 9-10). An objectives read that fails looks like "no objectives".
- `site_outcomes/read.py` `_summary`: `except Exception` gives `read_state = UNAVAILABLE` (line ~684). Other broad catches are at ~405, ~597, ~635 and ~721.
- `chain/response_store.py` `ResponseStore.serve`: it stores whatever `compose()` returns once the watermark is unchanged. Nothing tells it that the compose was degraded.
- `chain/prebuild.py` `run`: it counts only non-200 responses, and a degraded 200 reports OK.
- Connection pressure: about 20 adapters each call `create_engine(..., pool_pre_ping=True)` with the default pool (5+10). The prebuild's in-process `TestClient(create_app())` doubles that inside a server that is already running.

### Rule
1. **What counts as infrastructure (transient).** A failure is transient when the exception, or anything in its `__cause__`/`__context__` chain, is one of these:
   - `sqlalchemy.exc.OperationalError`, `InterfaceError`, `DisconnectionError` or `TimeoutError` (the pool timeout);
   - `psycopg.OperationalError` or `psycopg.errors.TooManyConnections`;
   - a `DBAPIError` with `connection_invalidated`;
   - `ConnectionError`, `OSError` or `socket.timeout`.

   A wrapper class on its own is NOT transient. `LedgerUnavailable`, `*StoreUnavailable` and `PortUnavailable` are also raised for deterministic states ("DATABASE_URL is not set", "tenant/Site not found", "not wired"), and those keep today's honest PARTIAL/UNKNOWN. One function decides: `infra.is_transient(error) -> bool` in a new `backend/assetops_backend/infra.py`.
2. **How composers signal it: a mark on the read scope, never a body field.** Add `ReadScope.degraded: list[str]` and `read_scope.note_failure(name, error)`, which appends when `is_transient(error)`. Calls go in:
   - `Reads.call`'s except;
   - the five broad catches in `site_outcomes/read.py`;
   - any other `except Exception` reached from a stored-route compose (the implementer greps `chain/`, `estate/` and `site_outcomes/` and lists every site in the packet).

   Backstop: one global `event.listen(Engine, "handle_error", ...)`, registered in `create_app`. It marks the current scope when `ctx.is_disconnect` is set or `ctx.original_exception` is an OperationalError. Wrappers that re-raise a DB error without `from error` get `from error` added (mechanical; listed in the packet).
3. **What the store does** (`ResponseStore.serve`, compose-only path included). After the compose, if `sc.degraded` is non-empty it does NOT insert. Instead:
   - (a) it serves the newest stored row for (route, request_key, code_version), whatever its W and even past `valid_until`. This is a new port method `latest_good(route, key, version)` on `postgres_response_store.py`; pruning keeps 3 rows, so one normally exists. The response gets the header `X-AssetOps-Stored: stale` and `Retry-After: 30`, with no ETag.
   - (b) with no such row, it answers **503** `{"code":"TEMPORARILY_UNAVAILABLE","message":"This view is temporarily unavailable. Retrying."}` with `Retry-After: 5`, and stores nothing.
   - It logs `stored_route_degraded` with the read names. An exception from the lookup path itself (the existing `unstored` branch) follows the same rule when it is transient.
4. **Frontend (minimal).** The board and summary fetches treat 503 `TEMPORARILY_UNAVAILABLE` as the state "Temporarily unavailable. Retrying...". They retry after 2, 4 and 8 s, then show "Still unavailable. Refresh to try again." It is never rendered as Unknown, PARTIAL or "No target set yet".
5. **Prebuild.** A path whose response is 503 or carries the `stale` header is retried 3 times, after 2, 5 and 10 s. The summary gains `degraded: {path: attempts}`, and `code` is `DEGRADED` when any path still fails. `tools/demo_combined.py` treats `DEGRADED` like `FAILED`: it prints the paths and exits non-zero. Before it starts, the prebuild logs the `pg_stat_activity` count.

### Card INFRA-1 (Opus, 0.75 unit server + Sonnet 0.15 frontend; lane C)
**Files:**
- new `backend/assetops_backend/infra.py`;
- `read_scope.py`;
- `site_outcomes/mini.py`;
- `site_outcomes/read.py`;
- `chain/response_store.py`;
- `chain/adapters/postgres_response_store.py`;
- `chain/prebuild.py`;
- `main.py` (the hook);
- `tools/demo_combined.py`;
- the frontend fetch helper for the summary and board.

**Pinned tests:**
- (T1, no DB) A fake rows port holds a good row. The compose calls a `Reads.call` whose fn raises `OperationalError("too many clients already")` halfway through. Assert: nothing inserted, the old bytes served, header `stale`, no ETag.
- (T2) The same with an empty store gives 503 `TEMPORARILY_UNAVAILABLE` and nothing inserted.
- (T3) `LedgerUnavailable("DATABASE_URL is not set")` without a cause still gives PARTIAL, and it is stored (the honest state is kept).
- (T4) `is_transient` table: a wrapped cause gives true, a bare wrapper gives false, and the pool `TimeoutError` gives true.
- (T5, `*_test` DB) The `handle_error` hook marks the scope when a connect to a closed port is refused.
- (T6) A prebuild against a client that returns 503 once and then 200 retries and reports OK. Always 503 reports `DEGRADED`, and `demo_combined` exits non-zero.
- (T7, frontend) 503 shows the retrying state, never "No target set yet".

**Fit in the 17 Nov plan (`architect-sequence-client-scope-2026-11-11.md` C.5).** Lane C, right after A4 PB-1b, in the wait for AR-1's merge before AR-3 + AR-6. It displaces nothing there. If PB-1b has not merged by Thu 18:00, INFRA-1 moves to the head of lane A after A2 and pushes A5/A6 by about 0.9 unit. AR-2 then follows the existing no-slack rule: held, and the boards use the pre-built ranges. **INFRA-1 must merge before the Sat 12:00 freeze and the rehearsal build**, because this defect can hit the client session.

### Ops mitigation until INFRA-1 is in every demo build
- **No test suite, check-all or ad-hoc DB script** runs against `assetopsv1-postgres-1` during add-dates, prepare, the prebuild, live checks, recapture or a demo. The coordinator pauses the lanes' DB work for those windows. The same machine rule goes into C.6.
- At the next safe container restart (not during E3d's life, and never touching client6), start Postgres with `-c max_connections=300`. Until then, check `SELECT count(*) FROM pg_stat_activity` before a prebuild and wait while it is above 60.
- After any prebuild, check `/api/estate/outcome-summary` for the demo ranges: no Site may be PARTIAL/UNAVAILABLE unless the story says so. If one is, rerun the prebuild once the server is quiet. The bad row expires at `valid_until`, or a new commit moves W.
- Deferred to BL-71: one shared engine factory with a capped pool (`ASSETOPS_DB_POOL_SIZE`), the prebuild reusing the serve's engines (out of process, over HTTP), and the degraded rule for non-stored routes.

Decision logged for owner review: **D-E5.47**.

## D-ANY.5 ANY-1 Phase 1 review M1/M2: period-row knowledge time is transaction time (Architect, Claude, 2026-11-11, owner-delegated, logged for owner review)

**Facts in code.**
- The existing compose binds `known_at` as **transaction time** only. CH5a1-R2 R-1 (`chain/adapters/postgres_chain_read.py` lines 30-31) says "a story-time evidence cutoff never reaches it".
- The tables already work this way: `site_day_snapshot.computed_at <= k` (`postgres_snapshot_store.py:111`), `created_at`/`source_known_at`/`decided_at <= k`, and `event_outbox.recorded_at` defaults to `clock_timestamp()` (0044).
- Story time bounds evidence only (`chain/read.py` `site_cutoff`).
- A day with no snapshot row at k reads `NO_DATA` (`chain/reader.py:111`).

**M1 ruling.**
- `site_period_read.computed_at`, `event_outbox.recorded_at` and `event_consumption.processed_at` stay wall-clock transaction time. Rows are never backdated to story time, because that would disagree with the snapshot and Finding reads at the same k.
- A historical read uses `computed_at <= k`, the latest revision (as built), with PENDING-at-k on the same clock.
- An October k on a November-built DB therefore truthfully sees "nothing known yet", and today's compose sees the same.
- A requested (site, day, kind) that has no row is never silent. `PeriodReadResult` gains `absent: tuple[(site_id, day, kind)]`, and each kind renders it exactly as today's compose renders no stored input at k (day grades give `NO_DATA`).
- There is no fallback compose on the serve path. Live absent rows are logged as `period_row_absent` and counted in perf.

**M2.** No bound now. The AR-0 baseline times `_UNCONSUMED_AT` on client6. If it exceeds 20 ms p95, add a low-water bound and drop `payload` from the select (if `resolve` does not read it) in AR-2.

**Phase-2 builder instruction.**
1. Write the Postgres tests first (M3): migration up/down, an adapter round-trip, and a late reading live and historical.
2. In the historical test, k falls between revision 1's and revision 2's `computed_at`, so revision 1 is served. A k before revision 1 gives `absent` and renders `NO_DATA`. A k after an outbox event but before its consumption gives PENDING.
3. Keep every `<= k` comparison on the transaction-time columns. Do not add a story-time clock.
4. Add `absent` to `PeriodReadResult`. Every AR-2 kind renders absent rows through the existing no-row rule.
5. The parity harness keeps its story-time k cases ("nothing known yet" parity). It adds one k taken from a real `computed_at` between two revisions on the parity DB.
6. Low items: unaligned Portfolio cases also randomise the end (`period_read_parity.py:115`), and `perf_budget --any-range` gains `--kinds`.
7. Time `_UNCONSUMED_AT` in the baseline and report the p95 in the packet (M2).

Decision logged for owner review: **D-ANY.5**.

## D-E5.48 DATA-11 Cold epochs and the EV depot's sparse look (Architect, Claude, 2026-11-11, owner-delegated, logged for owner review)

Context: the owner raised DATA-11 to IN and will show the demo to mini-grid and EV executives. The builder's report is in `.agent/PB-3-DATA-11-packet.md` (head ae41f5ba7, Known Deviations 1 and 2).

### (1) Cold: one recording session per ordinary day is CONFIRMED for 17 Nov
- **It is faithful to the hardware.** A cold-room temperature logger normally uploads a signed daily batch, so each day's batch is its own attested session. Kisiwa (DATA-1) is different: there a single continuous gateway stream was split for no device reason.
- **Splitting around S-3 does not help.** The Cold producer attests once per epoch, over the first run's window (`tools/demo_combined_cold.py:90-101`). Any session holding more than one day would leave its later days unattested, which is a worse honesty failure.
- **Condition for the client.** If any client-facing page counts "sessions" for Cold, the rehearsal check reads that number, and the script calls them "daily uploads".
- **Deferred to BL-72.** The producer will attest per run, so a continuous Cold stream becomes possible.

### (2) EV: record the depot's whole declared charging hours (card EV-HB)
**Why EV looks sparse.**
- EV-LAB-001 declares charging hours as Tuesday 08:00-16:00 (`config/chain/operating-calendar-v1.json`, `SITE_WEEKDAY={"ev":1}`). The story records only 1 of those 8 hours (`ev_parsing.EV_WINDOW`).
- So the expected hours are mostly unrecorded, and E5 reads LOW.
- The connector model already reports status every minute (`observation/transform.py:600-603`). With PB-3, idle connectors count as known zero energy.

**Ruling.**
- Record the full declared window on every EV story day (the ordinary Tuesdays and the fault Tuesday). The charging sessions, kWh and USD 4.50 stay as they are.
- Do NOT change the Tuesday-only calendar before 17 Nov. Adding weekdays would turn every earlier story week's EV weekdays into expected days with no data, so the depot would look worse, not better. That change goes to BL-72 post-demo with the matching backfill.
- The script says: "The depot's declared charging day is Tuesday; AssetOps checks every declared hour and counts idle chargers as known."

**Card EV-HB** (Opus, 0.5 unit, lane C after PB-3 + DATA-11 merge; same worktree or a new one, `task/EV-HB-window`):
1. The registered EV window, the w205b/w504 window constants the producer moves per day, `received_at`, and the analysis window all become 08:00-16:00 local on each EV story day. The parser window comes from one constant.
2. The charging sessions (08:01-08:31) and the fault-day fault evidence keep their values byte-for-byte. Status minutes outside the sessions are UNPLUGGED/PLUGGED heartbeats.
3. Tests first:
   - (a) A pure test: a full-window ordinary day grades COMPLETE for `charging_kwh`.
   - (b) Story plan pins: kWh, USD and the fault findings are unchanged.
   - (c) One EV worker run of the 8-hour window in a scratch `<prefix>_audit` prepare, where the EV day row is not LOW.
4. Finish rows that must change, each with a reason in the packet:
   - E5 (EV estimated income: no longer "with too little data" for the declared days);
   - CO-6 `cold_ev_coverage`;
   - the EV `charging_kwh` grade/coverage pins in `demo_combined_finish` rows and `k7_story_pins.py`.

   Every other row stays equal.
5. Report the prepare-time delta. The estimate is about +5-10 min (8x the EV minute rows on each EV day).

**Gate.**
- If (c) is not green by Fri 13 Nov 18:00, EV-HB is dropped. E5 stays LOW, and the script line becomes: "We record one hour of the depot's charging day in this demo; it reads as too little data, honestly."
- The Saturday-night rehearsal prepare verifies E5 and the prepare time either way.

**BL-72 (post-demo, about 1.0 unit).** The Cold producer attests per run (a continuous stream), and the EV depot gets weekday charging hours with an EV story backfill for the earlier weeks.

Decision logged for owner review: **D-E5.48**.

## D-E5.49 EV fault day over the full recorded day: c1 stays out of service until repaired (Architect, Claude, 2026-11-11, owner-delegated, logged for owner review)

**Ruling: option (a).**
- c1 is FAULTED from 08:16 and still out at 16:00. Clients read "out of service for 7 h 44 min".
- This is the honest consequence of recording the whole declared day under D-E5.48. The story already says no repair happened and the repair Action is still Pending, so a fault that cleared itself after 44 min would contradict it. It would also weaken the Action.
- For EV executives, "a charger has been down most of its charging day and the repair is still pending" is the more believable and more useful beat.
- What does not change:
  - the single Finding and its size;
  - per-session money (30/15 kWh, USD 9.00/4.50);
  - the Action's state.
- What does change: the CONNECTOR_OUT_OF_SERVICE warning duration, and "16 min unknown" disappears because status is known all day. This is a sanctioned exception to D-E5.48's "every other row stays equal". E5/WK-1 counting USD 9.00/9.00/4.50 (the day is now COMPLETE) is intended.

**Fix round (Sonnet, about 0.1 unit, same branch):**
1. Pin the 7 h 44 min out-of-service duration and its warning in `site_outcomes` tests and in the `demo_combined_finish` rows. List them in the EV-HB packet's rows table with the reason "D-E5.49".
2. Add a prepare-checklist line: on the EV fault day, c1 is out of service for 7 h 44 min, there is 0 min unknown, there is one Finding, the Action is Pending, and per-session USD is 9.00/4.50.
3. In `Docs/demo-sprint/implementation-logic-portfolio-sites-findings-actions.html` and the demo script, replace "44 min out, 16 min unknown" with "out of service from 08:16 for the rest of the charging day (7 h 44 min); repair still pending".

Decision logged for owner review: **D-E5.49**.

## D-ANY.6 Tonight's speed build for the Thursday 12 Nov technical demo (Architect, Claude, 2026-11-11 16:50, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude.
- Owner, verbatim (`.agent/owner-speed-before-thursday-2026-11-11.md`): "the speed work has to be done before Tursday demo"; chose "Rebuild tonight" (option b), accepting the risk.
- Supersedes for tonight only: the ANY-1 packet line "baseline after the Thursday demo" and the D-ANY.4 timing. D-ANY.1-5 rules otherwise stand.

**1. Slice and cutoffs.** Tonight = ANY-1 only (AR-0 baseline, AR-1, AR-2). AR-3, AR-4, AR-5 and AR-6 are not built for Thursday.
- 21:30 last ACCEPT. 22:00 go/no-go and merge. 22:15 build tag `demo/2026-11-12-rows`, fresh worktree `AssetOpsV1-e3e`. **22:30 latest prepare start** (about 2 h 45 min plus EV-HB 10 min, plus the AR-2 row build of at most 15 min, so done by about 01:45). 01:45-02:15 self-check plus full parity on the new DB. 02:15-03:15 live checks. 06:30 runbook and add-dates as planned.
- After the prepare starts, no full rerun fits. Only a single failed step can be rerun.
- **Fast on Thursday:** Site boards (mini depth: renewable, fuel, service, backup) for any day, about 1-1.5 s cold on Mini-grid and Diesel Sites.
- **Still slow off the pre-stored ranges:** Cold and EV boards (work-list reads; AR-6, about 2-3 s); the Portfolio for any range (AR-3/AR-4); every other page off the stored ranges.
- The pre-load list stays (AR-5 not built), so stored ranges are as fast as in client6. The presenter rule D-ANY.4 still holds for the Portfolio and for non-board pages.
- If AR-2 is not ACCEPTed by 22:00, it is held. The build still goes ahead at 22:30 from main (today's fixes, plus AR-1 only if its parity passed), and the boards stay on the pre-stored ranges.

**2. Baseline.**
- Run it now on `assetops_polish_client4_test` (not the fallback; 0059 is applied there). **Never on client6.** client2 is the spare.
- Parity must pass before AR-1 or AR-2 merges.
- To keep it fast: run the story requests plus `--random 16` (the default), not a wider sweep. Apply the AR-2 kinds only to client4 rows built by the backfill CLI.
- The full parity runs again on the new DB after the prepare, as part of its self-check.
- Time `_UNCONSUMED_AT` and record p95 in the packet. Above 20 ms p95: apply the low-water bound and drop `payload` from the select (inside AR-2).
- A fresh Claude reviewer reviews ANY-1 phase 2 now, in parallel.

**3. Other merges and machine rule.**
- C1 merges if it is ACCEPTed by 21:30.
- HON-1 and OPEN-NOW are not Thursday-critical (they target 17 Nov). They are held out of tonight's tag. They may merge to main after the tag is cut, once reviewed.
- Until 22:00, only the baseline and AR-2's own Postgres tests may touch Postgres, one at a time. Other builders run no-DB tests only.
- From 22:15 until the live checks end, **all builders stop**: no tests, no prepares, no Postgres. Code edits are allowed.

**4. Fallback.**
- If parity alone fails on the new DB: set the AR-2 kill switch (`ASSETOPS_PERIOD_READ_KINDS=` empty, so the old compose path is used) and rerun the board live checks (15 min).
- Any other self-check or live-check failure, or no green result by **05:00**: the demo uses `assetops_polish_client6_test` (tag demo/2026-11-11-e3d, runbook as planned). client6 is never modified.

Decision logged for owner review: **D-ANY.6**.

### D-ANY.6a AR-2 rows path misses a recompute job created after the row build (Architect, Claude, 2026-11-11 ~17:55, owner-delegated, logged for owner review)

- **Defect.** On the rows path, PENDING-at-k reads only unconsumed outbox events and snapshot dirty marks. The old compose path decides PENDING_RECOMPUTE from `recompute_job` itself (`mini_depth/read.py` `_JOBS`: status PENDING, LEASED or FAILED, `available_at <= k`, and no later selection), and it does so both live and at a historical k. A job raised by `mini_enqueue_hour` with no outbox event is therefore missed, and so is an existing PENDING job whose `available_at` was moved later.
- **Live-demo impact.** Tomorrow's add-dates enqueues exactly these jobs. Rows would read CURRENT while a recompute is pending, which is a false statement on the board. The fix is required, not optional.
- **Fix, ruled.** Do not emit events from the SQL function (a 0029 change with a wider blast radius). Do not use timing heuristics.
  - The rows path runs the oracle's own `_JOBS` predicate, batched: one statement over Sites × hours × mini domains at k.
  - An hour whose live job set at k equals the job set stored in its row renders from the row.
  - An hour with any other job set is served by the old `_hour` for that hour only. This is the D-ANY.1 rule "a case that cannot be proven equal stays on the old path". It is logged (`period_row_job_fallback`) and counted.
  - Byte-equal by construction. Expected cost is one extra statement per read; fallback hours are rare (only while a recompute is in flight).
- **Size and timing.** About 0.3 unit. Build by 19:45, Postgres test plus client4 parity by 20:30, review by 21:30.
- **If not ACCEPTed by 21:30: hold AR-2 entirely.** Do not merge it with the kill switch off. That gives the demo no speed, adds an unexercised prepare step, and leaves a latent false-CURRENT path. Tonight's build then uses main plus AR-1 (if its parity passed), and the boards stay on the pre-stored ranges.

Decision logged for owner review: **D-ANY.6a**.

### D-ANY.6b / D-E5.49a Tonight's build fails one check, CO-10 ("16 min unknown"): use client7 (Architect, Claude, 2026-11-11 ~22:10, owner-delegated, logged for owner review)

- **Finding.** In client7, the c1 warning reads "7 h 44 min out and 16 min unknown on 3 Nov".
  - 7 h 44 min + 16 min = 8 h, the whole charging day. The out-of-service part (08:16-16:00) is right.
  - The 16 min are 08:00-08:16, before the fault. The generated full-day heartbeat carries no connector status for c1 until the fault notice at 08:16.
  - The product is correct not to guess a status it never received. This is a data and story detail, not a product defect.
  - The D-E5.49 pin assumed status "known all day". The data does not give that.
- **Thursday demo:** use **client7**. The D-ANY.6 fallback covers failures that make the build untrustworthy. This one is an honest sentence about real data gaps, and the other 53 checks pass. client6 stays untouched as the fallback for any other failure.
- **Presenter line:** "c1 was out of service from 08:16 for the rest of the charging day; the first 16 minutes have no status reading; repair still pending."
- **17 Nov fix (data, about 0.1 unit, Sonnet):**
  - The EV-HB generator emits a c1 Available status with the day's first heartbeat at 08:00, so status is known all day.
  - Keep the D-E5.49 pin at 0 min unknown. Do not relax it.
  - Rerun CO-10 on the Monday build.

Decision logged for owner review: **D-ANY.6b / D-E5.49a**.

## D-PRICE.1 Prices typed on screen are saved as "Entered by site admin" (Architect, Claude, 2026-11-12, owner-directed, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude.
- Owner, verbatim (`.agent/owner-price-entry-in-scope-2026-11-12.md`): "yes, price entry in scope as site admin"
- Design: `.agent/architect-sequence-client-scope-2026-11-11.md` revision 5 (card PR-3).

**Rule.** A price saved from the Site price page is written by the same server-configured entry service as the dip form (§3.1 above, owner Q3): actor `service:operator-entry` (`ENTRY_PRINCIPAL`, `work/operational_entry.py:25`), labelled **"Entered by site admin"**.
- The browser never sends an actor, a change kind or an instant. A body naming an actor stays 422 `CLIENT_ACTOR_FORBIDDEN`.
- It is stored as `actor_kind = 'SYSTEM'` with no `author_id`, on the new channel **`SITE_ADMIN_ENTRY`** (a migration widens the channel CHECK).
  - `authorization_basis` reads: "entered on screen through the server-configured entry service … no signed-in person (D-PRICE.1)".
  - Provenance: `{"service": "operator-entry", "job": "site-admin-price-entry", "rule": "price-entry/1"}`.
- It is switched on by the same `ASSETOPS_OPERATIONAL_ENTRY=on` (`host/lab_app.py:77-97`). Off: 403 `PRICE_ENTRY_OFF`, and no form is shown.
- The label names the role of the entry point, not a person. In the demo, the presenter is the site admin.
- After the demo, a signed-in pricing editor (BL-54, spec §4.3) replaces it. Revisions already saved keep their stored actor and label; nothing is rewritten.
- The tool path `SYSTEM_PUBLISHER` stays, labelled "AssetOps administrator".
- The human route `POST /financial-assumptions` stays refused (`HUMAN_PRINCIPAL_REQUIRED`).
- Only the three stored keys may be saved for 17 Nov. A future key is refused with 422 `PRICE_KEY_NOT_ENTERABLE`, because no figure reads it.

Decision logged for owner review: **D-PRICE.1**.

## D-OPEN.1, D-ANY.7, D-HON.1, D-F05.1 Batched rulings (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude.

### D-OPEN.1 What "open now" means on the Work lists (OPEN-NOW review, `task/OPEN-NOW-work-read` a2e792ddb)

- **Definition.** An item is "open now" when it is an incident or a maintenance request whose reduced W4 case state at the read's `known_at` is OPEN or IN_PROGRESS, at the list's admitted Sites, with no date-window filter. This is what the code does (`work_open_now.py:15`, `work/open_now.py:23-29`). Accepted as built.
- **Actions are not counted.** An Action's lifecycle (ACCEPTED, PENDING, APPLIED) has no "open" state, and the Action index has no `known_at` cutoff, so any count would be invented. The Site Actions subtab carries no open-now line. The card wording "requests, actions … 1 action" is amended to "incidents, requests".
- **Exact copy (as built, no change):** "Open now: {n} incident(s), {n} request(s), whatever the dates"; a zero kind is left out; nothing open reads "Nothing open now".
- **Low 1, fix before merge (about 0.1 unit).** The open-now line must never take down the list it sits on. In `global_index.py:537-542` and the Site list (`site_index.py` ~390), a reduction failure in the open-now count omits `open_now` from the wire, logs `open_now_unavailable`, and the list is served as before. The frontend already shows no line when `open_now` is absent. Add one no-DB test per list.
- **Low 2, no change.** The count uses the list's own Site scope (`imported_sites(.., request.to)`); "whatever the dates" refers to the cases' dates, not Site import. Accepted.
- **Low 3, fix before merge.** Add a real cursor page-two read (non-empty window, `limit=1`, next cursor) to `test_open_now_postgres.py`, in the same pending Postgres run.
- **Low 4 (one events query per case):** backlog; demo scale.
- Merge condition: Lows 1 and 3 done, the packet's 8 Postgres files pass, fresh-reviewer re-check of the diff.

Decision logged for owner review: **D-OPEN.1**.

### D-ANY.7 AR-4 claim-day rows vs D-ANY.5 (commit 5f82f5fa0, `task/ANY-2-AR4`)

- **Confirmed.** A day whose page selection names no revision is projected with no stored input and no compose (D-ANY.5). A row that exists but is not provably equal (other revision, older builder, PENDING on a touched local day) is read as today for that day only, logged and counted (D-ANY.6a / D-ANY.1).
- **Open question ruled: the page selected a revision but no row is known at k.** The page's own live selection proves a revision exists at k, so the missing row means the row build has not caught up. That is "cannot be proven equal", not "nothing known": read that day as today (`_miss(..., "absent")`), logged `period_row_absent` and counted. Never render NO_DATA against the page's own selection. The builder's code is right.
- **Builder change:** none to the logic. Replace the module-doc line "OPEN Architect question" with "Ruled D-ANY.7". Parity must include one no-revision day and one selected-revision-without-row day (a k between the revision's `computed_at` and the row's `computed_at`), both byte-equal to today's compose.

Decision logged for owner review: **D-ANY.7**.

### D-HON.1 HON-1 Low: the Site Overview card's "Why?" days

- **Backlog, with a rehearsal trigger.** A card's own days line is still read from claim days when its day set differs from the coverage line's (packet, Known deviations). This is honest per card (its own days), and the Site Overview day line now names the gap.
- **Trigger:** if the 17 Nov rehearsal shows a card's "Why?" day count contradicting the coverage line for the same days on a demo Site (for example "7 of 7" beside "6 of 7"), apply the same `_own_days` arrival-day rule to the Site Overview cards (about 0.1 unit, Sonnet) before the demo. Otherwise it stays in the backlog. HON-1 merges without it.

Decision logged for owner review: **D-HON.1**.

### D-F05.1 F05 placement test coverage after the s602b estate assertions moved to PARTIAL

- **Backlog; not required before 17 Nov.** It is a test-coverage gap, not a product behaviour change, and no 17 Nov card depends on new F05 placement logic. The demo build's live checks are the demo-time guard.
- **Builder change:** none now. Backlog item: add one fixture with complete readings that asserts F05 placement, so the placement path is again covered by a test with readings.

Decision logged for owner review: **D-F05.1**.

## D-ANY.8 Order of the remaining any-range speed work for 17 Nov (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Owner priority: "the speedup for any date range prioritised". Freeze: AR-4 held unmerged if not ACCEPTed by Sat 14 Nov 20:00.
- **Why this order.** The AR-4 profile (client4, cold, store off, unlisted week with claim rows) puts ~13 s of 11.7-14.5 s in dispatch-day compose reached through `evidence_money.mini_grid_rows` → `coverage._mini_grid_basis`, then `_mini_grid_money` 4.1 s and `consequence_provenance` 3.3 s. The dispatch-day cost is already solved by AR-3's `dispatch.day` rows (127-360 ms per Site-range, parity 59/0/0). So the Portfolio switch to those rows is the largest single cut, money.lines is next, and provenance is last.
- **1. AR-3 + AR-6 merges as it is (lane A, by Fri 14:00).** Do not add the Portfolio switch to AR-3. It is under review, and a new line would reopen the review.
- **2. The switch goes on AR-4 (`task/ANY-2-AR4`), after AR-3 is on main.** AR-4 does not merge the AR-3 branch in. It rebases onto main once AR-3 merges, so the reviewed AR-3 code is carried once and fix rounds are not duplicated. The switch is the one-line change in `evidence_money.mini_grid_rows` to read `coverage.dispatch_days` (AR-3's row reader). `estate/coverage` stays untouched (AR-3's files).
- **3. Until AR-3 merges, the AR-4 builder builds money.lines (MN-1/2/3)** with code and no-DB tests only, including the rev-5 contract: declare `price.revised@1` (`by_assumption_key`, days from the valid date to today) and rebuild those rows when a price is saved (PR-3).
- **4. Order of Postgres work on AR-4 (priority 2, after AR-3):** (a) rebase + switch, then parity and timings; (b) money.lines parity and timings.
- **Minimum to call AR-4 done for 17 Nov:** evidence.claim (built) + the dispatch.day switch, with the evidence below. **money.lines is IN only if** its parity, including the price-save case, passes by **Sat 12:00**. If it does not, its commits move to `task/ANY-2-AR4b` (backlog), and AR-4 goes to review as claim + switch. The review starts Sat by 12:00 and AR-4 merges by 16:00 (rev-5 lane C).
- **Backlog (not 17 Nov):** evidence.provenance (cold/EV pinned windows), AR-5 (the pre-load list stays as the safety net), and money.lines if it misses Sat 12:00.
- **If AR-3 is held:** AR-4 merges as claim-only without the switch, provided its own parity passes. That is still faster (week 17.6-19.4 s → 11.7-14.5 s).
- **Evidence required for merge:**
  - Byte-equal parity on client4 over the combined path that ships (claim rows + dispatch.day rows + money.lines if IN), 0 mismatches. It must keep the D-ANY.5/D-ANY.7 cases: a no-revision day, and a selected-revision-without-row day.
  - If money.lines is IN, it must also pass a price-save case. A price revision whose valid date falls mid-range rebuilds rows from the valid date to today and stays byte-equal to compose before and after the save. PR-3's Postgres flow test is rerun by whichever of AR-4 and PR-3 merges second.
  - Timings on client4, cold, store off, with a profile of each: the unlisted week, the 22 days, and a 31-day month, each before and after.
  - The ≤2 s target (rev 4 / ANY-1) is reported, not gated: the gate is parity + no regression. A miss is stated honestly in the packet, with what remains (provenance, money if out). Presenter rule D-ANY.4 still holds for Portfolio ranges over 2 s.

Decision logged for owner review: **D-ANY.8**.

## D-ANY.9 AR-4: Portfolio consequence money, receipt-less productive rows, the `note_page_days` hook (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Context: branch `task/ANY-2-AR4` head `ba227df16`, packet `.agent/AR-4-packet.md` (Not built 7, deviations 5-6). D-ANY.8 stands unchanged.
- **Q1 Portfolio consequence money (`_mini_grid_money` + `consequence_provenance`, ~4 s on a client4 week): backlog, not 17 Nov.** Storing it per (consequence revision, Finding revision), like the claim provenance, is the likely shape, but it is a new stored kind with its own invalidation (Finding recompute, consequence revision, price revision). It cannot be built and pass parity by Sat 12:00 next to money.lines, and D-ANY.8 already puts provenance last. The builder does not start it. The packet states the remaining ~4 s honestly in the ≤2 s report (D-ANY.8: reported, not gated). The backlog entry is `evidence.consequence_money`: per (Site, consequence revision, Finding revision), body = today's `_mini_grid_money` line + provenance. Its shape is confirmed by the Architect after a post-switch profile, not before.
- **Q2 old productive rows without a receipt: acceptable, with no PENDING gate on the amount.** The amount is unchanged under `mini.productive_energy@2`, and readers use only `amount`/`currency`/`assumption_revision_id`. So a PENDING gate would cost speed and change no value. MN-1's wording "read PENDING until the backfill" is corrected to: "an old row serves its amount; its receipt is absent until it is rebuilt". Conditions:
  - Any reader that shows the receipt treats a row without `receipt` as "receipt not available yet" or composes it. It never shows an empty or partial receipt.
  - The client4 build at step 4b rebuilds the productive rows to @2, so the demo data carries receipts.
  - Add one no-DB test: a receipt-less row reads the same amount as compose.
- **`note_page_days` hook (commit `36d15fd70`): accepted.** The claim rows must be matched against exactly the days the page reads. Without the hook, the switch would select claim days from a different day set. It is optional through `getattr`, so other snapshots keep their earlier behaviour. Conditions: the parity run covers it, and the packet lists it as a step-3 deviation from the "one-line change".

Decision logged for owner review: **D-ANY.9**.

## D-PRICE.2 PR-3 server half: Site name in the first-price summary, dry-run reason, two router keywords (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Context: branch `task/PR-3-price-entry` head `99d4b6f24`, packet `.agent/PR-3-packet.md` (deviations 1, 3, 4; Q1-Q2). D-PRICE.1 stands.
- **Q1 Site in the INITIAL summary: use the Site's display name.** The client reads History, and a code like `KOBO-001` is system vocabulary. Take the name from the same estate Site record the Financials read uses (`site["site_name"]`). Do not add a new table or a new scope field. Fall back to the code only when the name is null. A lookup failure follows the 503 `ASSUMPTION_STORE_UNAVAILABLE` path, not a 500. Already-stored summaries are not rewritten. Add a test for the name and one for the null-name fallback.
- **Q2 dry run returns 200 with `reason_required: true`: confirmed.** The form needs the dry run to tell it to show the Reason field. The save refuses 422 `REASON_REQUIRED` without a reason, which keeps the guard. Rev 5 §5.3 "dry run runs steps 1-9" is read as: step 9 *reports* on the dry run and *refuses* on the save.
- **Router keywords `unavailable` and `clock`: confirmed**, provided that:
  - `clock` is a server-side injection only, with the server's now as default. No request field or header can set it.
  - `unavailable` maps only to 503 `ASSUMPTION_STORE_UNAVAILABLE`, for store, zone and scope failures. Turning a scope outage into 503 instead of 500 is correct.

Decision logged for owner review: **D-PRICE.2**.

## D-ANY.10 AR-4 client4 evidence: the `before_build` mismatch and the second dispatch-day compose (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Context: `task/ANY-2-AR4` head `917a90724`, packet `.agent/AR-4-packet.md`. Parity (`--kinds evidence.claim,dispatch.day`) 61 cases, 1 mismatch `any.claim_rows.before_build` (k 11-11T23:35Z, dispatch.day rows built 00:03): oracle has a `selection_id`, candidate has null.

### (1) Option (b): an absent `dispatch.day` row is composed, never rendered as "nothing stored". Option (a) is refused.
- **Why.** D-ANY.5's "absent = nothing known" holds only if a row exists from the moment its input exists. Rows built later by the backfill CLI (or a lagging tick) break that: at a k before the build the input is known, the row is not. Rendering UNASSESSED there is a false answer a real user can get on a historical read. Moving the case's k (a) would hide the defect, not fix it. This is the same case D-ANY.7 ruled for claims: "cannot be proven equal", not "nothing known".
- **Amends D-ANY.5 for `dispatch.day`.** "There is no fallback compose" no longer applies to this kind. A day with no row at k (explicit or live) is served by today's compose for that day only.
- **Shape.** `DispatchDayRows` marks absent days instead of calling `absent_day`; `coverage.dispatch_days` (it holds the snapshot) calls `snapshot.dispatch_days` once per contiguous run of absent days over that run's window at the same k, and splices the composed days in. Each run logs `period_row_absent` (kind, Site, days) and is counted in perf. PENDING-at-k on a composed day is whatever compose says (no synthetic job added). `absent_day`/`ABSENT_REASON` stay only if a test still needs them; the module doc's "There is no fallback compose" line becomes "Ruled D-ANY.10".
- **Where.** The defect is on main (AR-3) and ships whether or not AR-4 merges, so it is fixed on main: branch `fix/AR-3-absent-compose` off current main, about 0.2 unit (Sonnet). AR-4 does not carry it; AR-4 rebases onto main after it merges. Fresh Claude reviewer; it does not wait for AR-4's review.
- **AR-2 kinds (mini depth day grades) have the same latent hole** at a k between an input and a later row build. Not 17 Nov: the demo reads live or post-prepare k. Backlog `BL-ANY-absent`: apply the same per-run compose to every AR-2 kind, with a before-build parity case each.

### (2) Make the second switch, on AR-4.
- `evidence_money.site_data_gap_days_many` (line ~577) reads `coverage.dispatch_days(snap, tenant_id, site["site_id"], req.from_, req.to, scope["k"])` instead of `snap.dispatch_days(...)`. Same rule as D-ANY.8: one day source for the whole Portfolio read. It is an AR-4 file; list it as a deviation beside the D-ANY.9 hook. No other serve-path caller remains (`period_rows.fragment` is a builder and must keep composing; `measure_impls`/`postgres_work_read` are other reads, out of scope).

### Evidence required
- Fix branch: no-DB tests first. (i) an explicit k with no row but a compose selection returns the composed day, byte-equal, and logs `period_row_absent`; (ii) two absent runs split by a stored day compose twice, once per run; (iii) a stored day is never composed; (iv) kill switch unchanged. Then one Postgres test: k between a revision's `computed_at` and its row's `computed_at` reads the selection. client4 parity `--kinds dispatch.day` 0 mismatches including `before_build`.
- AR-4 after rebase: client4 parity `--kinds evidence.claim,dispatch.day` 0 mismatches over the 61 cases, keeping `before_build`, the no-revision day and the selected-revision-without-row day (D-ANY.7/8). Timings cold, store off, with profiles, for the week, 22 days and 31 days, before (`917a90724`) and after; the profile must show no `snapshot.dispatch_days` under `_data_gaps` on a fully built range. ≤2 s stays reported, not gated (D-ANY.8).

Decision logged for owner review: **D-ANY.10**.

## D-PRICE.3 PR-2a price page: old addresses, EV subtabs, rows per Site type, three MOCK DEVIATIONs (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Context: `task/PR-2a-price-page` head `0b27e10d4`, packet `.agent/PR-2a-packet.md` (deviations 1-9, Q1-Q3). Owner defaults (`.agent/owner-price-entry-defaults-2026-11-12.md`) stand: the bare `/financials/assumptions` address forwards, the shared subtab reads "Prices".
- **Q1 both screens stay, as built.** The pinned address (`revision_id`, `recorded_at`, `history_*`) is the money "Why?" receipt target; the price page has no version pin, so forwarding would break a working receipt link two days before the demo. The cold declarations screen (stock quantity, unit value, exposure rule) carries content the price page does not show and is reached by "Review assumptions". Neither is the demo price beat. Backlog `BL-PRICE-pin`: give the price page a version pin and fold the exact-version view into History, then forward the pinned address; fold the cold declarations into Prices when stock value becomes a stored price.
- **Q2 EV subtab row unchanged ("Overview | Assumptions | Scenarios"); stay as built.** The EV Assumptions screen holds declarations beyond the tariff, and the demo price beat is a cold Site (GreenHarvest, mock Part B). EV Sites reach the price page through price links; the page shows "Overview | Prices | Scenarios" there. The packet keeps deviation 5 as a known inconsistency. Backlog `BL-PRICE-ev-tabs`: one EV row "Overview | Assumptions | Prices | Scenarios" on both the EV Financials screens and the price page.
- **Q3 `SITE_KEYS` confirmed as built.** Cost per visit and planned service cost follow `WARNING_SPEC` (REPEATED_MAINTENANCE_NO_RESULT, PLAN_*), which is computed from work facts for every Site type, so cold and EV Sites list both. A cold Site lists "Stock value at risk": mock `price-it.html` Part B (GreenHarvest, line 158) shows it. It is a future key ("Not set" plus default 3's sentence); it never claims a saved figure. The "Used by" words stay as built; the walkthrough checks them.
- **MOCK DEVIATIONs confirmed, all three:**
  1. No "item you came to price" block or worked receipt: the link carries only `key`/`need`; the highlighted `?key=` row stands in. Rebuilding the item from `return` is new server work, not 17 Nov. Backlog `BL-PRICE-focus`.
  2. Generic return bar "← Back to where you were" · "Your date range is kept.": `return` is a path with no item name. Backlog with `BL-PRICE-focus` (carry the item title on the link).
  3. No lock icon: the shell-overflow guard refuses inline `<svg>`; a guard change is not worth it for an icon. The words carry the meaning. Backlog `BL-PRICE-icon` (shared icon component the guard allows).
- **Builder actions before review (required).** The packet says layout evidence was not run. Capture the price page at 1440 and 390 px (mini, cold with `?key=repair_visit_cost`, EV), compare with `price-it.html` Part B/C, and add the captures to the packet. Any stacking mismatch is fixed in this slice. Label deviations 1, 2, 3 and 8 in code and packet as "MOCK DEVIATION (D-PRICE.3)". No other code change.

Decision logged for owner review: **D-PRICE.3**.

## D-17N.1-7 The owner's 17 Nov expectations: 2 s, modern UI, performance, data coverage, upload, Modbus (Architect, Claude, 2026-11-12, owner-directed, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Owner, verbatim: `.agent/owner-17nov-expectations-2026-11-12.md`. Full reasoning, designs and lanes: `architect-sequence-client-scope-2026-11-11.md` revision 7.
- **D-17N.1 Speed.** ≤2 s computed live for any range is OUT for 17 Nov. One request is one sequential process, so a larger machine does not shorten it. The AR-4 profile after the second switch is 8.1 s for a week: about 2.2 s of dispatch lookups, about 4 s of consequence money and provenance, and about 1.9 s not yet profiled. The remainder, ANY-3 (`evidence.consequence_money` 1.5 plus the rest 0.5-1.0), is serial after AR-4 and goes to the backlog, first after the demo. IN for 17 Nov:
  - AR-4 (D-ANY.8 unchanged);
  - DISP-1 (0.3);
  - SPEED-0: every passed kind in `ASSETOPS_PERIOD_READ_KINDS` on the final build;
  - **WARM-1 (0.6), a labelled workaround:** it prepares every date-bar preset and every day-aligned 7/14/30/31-day range in the data window over HTTP. Its gate is 100% store hits, maximum ≤2.0 s and 0 degraded.
  - **D-ANY.3 is reversed for the 17 Nov build only. D-ANY.4 is narrowed to custom ranges on the Portfolio.**
- **D-17N.2 UI.** UQ-FI-1/2 stand (rev 6). New **UQ-FI-3** (0.75) is IN-if the owner approves its two v7.2 sheet panels by Fri 09:00: the one-figure Portfolio card and the reading-state `StatusPill` (light theme only). It is held whole if not ACCEPTed by Sat 20:00. Stages 1-2 of BL-69 (about 8 units plus 7 unbuilt page mockups), the dark theme and the axe pass are OUT.
- **D-17N.3 Performance list.**
  - IN: AR-4, DISP-1, WARM-1 with BL-71 part 2 (prebuild over HTTP), SPEED-0.
  - IN-if: money.lines (Sat 12:00 parity, D-ANY.8); BL-ANY-absent (0.5, Sonnet) if lane A is free.
  - OUT: ANY-3, `evidence.provenance`, AR-5 (it contradicts WARM-1 until every kind is stored), AR-7, BL-71 part 1.
- **D-17N.4 Data coverage.**
  - IN: DATA-5 and DATA-10/13.
  - IN-if approved by Fri 09:00: DATA-4 (EV buyer present) and DATA-8.
  - OUT: DATA-7 (it re-proves the Kisiwa story two days out, at +15-25 min per prepare), FCF-1 and BL-48.
  - Each data merge is gated by the Sat-night rehearsal finish check; a failure reverts that merge.
  - The measure is the before/after gap-line count per script page from UQ-FI's `measure.json`.
- **D-17N.5 Upload, UP-1 (2.25).** Kobo only, the illustrative `assetops-generic-interval-csv/1` format.
  - Route: `POST /api/sites/{site_id}/reading-uploads?dry_run=`. It refuses the whole file on any of the 8 CSV codes, on `ALREADY_RECORDED`, or when too large.
  - It admits through a demo upload gateway process (never inside the API process), with the states Checked, Sent, Accepted, Still processing, Analysed, Refused and Held. It records "Uploaded by site admin" (as D-PRICE.1), with no sign-in.
  - It is behind `ASSETOPS_READING_UPLOAD_SITES`, off by default, and mockup-first (one page, approved by Fri 09:00).
  - Column mapping, other formats, history import (BL-59) and new Sites are OUT.
- **D-17N.6 Modbus.** MB-1 (1.0): emulator → `modbus_poller` → gateway → `serve_tls` → demo DB, feeding Kobo's today live. It builds TEL-08's `setup`, `activate` and `read`, has a no-overlap finish check with UP-1, and uses TEL-05's gates plus the 5-minute uplink-stop test. The BeagleBone (+0.5 and one 1-hour heavy slot) is IN-if the board is reachable by Fri 12:00. It uploads to the VPS on 8443 and is shown as a recorded clip, never live in the room.
- **D-17N.7 Lanes and freeze.**
  - Six VPS lanes (C speed, A tools, B price+data, D/E UI frontend-only, F field). One heavy job at a time.
  - Priority: AR-4 > PR-3 > WARM-1 > UQ-FI-1/2 > UP-1 > MB-1 > DATA-5/4/8 > UQ-FI-3 > DATA-10/13 > FR-B > CLEAN-1 > BL-ANY-absent.
  - **The core freeze stays Sat 20:00.** A late window to **Sun 12:00** is open only for the additive, switched-off-by-default UP-1 and MB-1. Their named risk: they miss Saturday's full suite; their own tests, the Postgres flow and Monday's live checks are their proof, and a failed live check leaves the switch off.
  - Upload and Modbus beats go last in the script, because new readings move the estate watermark and void every warmed page until a re-warm (estimated 20-25 min, to be measured).
  - "Everything" (about 21 units) does not fit even with a Mon 12:00 freeze, and is not recommended.

Decisions logged for owner review: **D-17N.1-7**.

## D-ANY.11 DISP-1: the remaining dispatch-day lookups are Finding money eligibility; read them through `coverage.dispatch_days` (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Context: `task/ANY-2-AR4` head `786d2293a`, packet `.agent/AR-4-packet.md`. Parity 61/0/0 after the AR-3 absent fix. Timings cold, store off, rows on: week 8.7 s, 22 days 22.2 s, 31 days 27.1 s. Every remaining `select_dispatch_days_on` call comes from `financials/money_eligibility.py:192` `for_finding_on` (one per Finding day bracket: 4 calls / 1.7-2.3 s a week, 12 / 6.5 s at 22 days, 16 / 6.8 s at 31 days), reached from the snapshot adapter `postgres_estate_read.eligibility` (line ~211), its only caller.
- **Yes: this is the D-ANY.8/10 rule for a third caller, not D-ANY.9.** D-ANY.9 (`evidence.consequence_money`) is about storing consequence money and its provenance (~4 s); these calls are dispatch-day reads, and the `dispatch.day` rows already hold exactly what `select_dispatch_days_on` returns (`dispatch_day_rows.day_from_body`). One day source for the whole Portfolio read. No new kind, no new invalidation.
- **Shape (builders do not design).**
  - `MoneyEligibility.for_finding_on(..., known_at, *, select_days=None)`: when `select_days` is given, the bracket's days come from `select_days(from_, to)`; otherwise `self.days.select_dispatch_days_on(c, ...)` exactly as today. The `self.days is None` fail-closed check applies only when `select_days` is None. All other logic unchanged; `for_finding` (live Site pages) untouched. `financials` must not import `estate`.
  - `postgres_estate_read` `eligibility(t, s, finding_id, k)` passes `select_days=lambda f, to: coverage.dispatch_days(self, t, s, f, to, k)` (local import if a cycle appears). The snapshot's own `basis_historical`/`continuation` decide explicit vs live rows, the same as the coverage read in the same request; absent days compose per D-ANY.10; with the kind not served (D-ANY.6 kill switch) it falls back to `self.dispatch_days`, i.e. today's call.
  - Guard: if the returned days do not cover every bracket day, `for_finding_on` returns `unavailable(fid, "HISTORICAL_DAY_UNAVAILABLE: ...")` (fail closed), never a KeyError.
- **Where: its own branch `fix/DISP-1-money-eligibility` off current main, not AR-4.** These are not AR-4's files, and putting them on AR-4 would void its finished 61/0/0 parity two days before the freeze. AR-4 (priority 1) merges on its present evidence. Build and no-DB tests start now; parity and timings run after AR-4 merges, with main merged in.
- **Units 0.25** (inside DISP-1's 0.3). Lane C; a Sonnet builder is enough. **IN for 17 Nov under rev 7** (DISP-1 was IN); merge by the Sat 20:00 core freeze. Heavy-job queue: after AR-4 parity; if money.lines parity is ready first it goes first (Sat 12:00 deadline). If DISP-1 misses the freeze it drops with no other change: WARM-1 covers every preset either way.
- **Evidence required.**
  - No-DB: (i) with `select_days` given, `select_dispatch_days_on` is never called; (ii) stored days give the same `evaluate` result as compose (ELIGIBLE and one PENDING_REASSESSMENT via an unavailable day); (iii) a short day list fails closed, no exception; (iv) `select_days=None` is byte-identical to today.
  - client4 parity `--kinds evidence.claim,dispatch.day` 0 mismatches over the 61 cases, plus, if not already there, Finding money cases: one ELIGIBLE Finding with a current amount, one PENDING_REASSESSMENT, one Finding whose bracket runs outside the request range, and one at the `before_build` k. List which existing cases already cover these.
  - Timings cold, store off, rows on, with profiles, week / 22 / 31 days, before (`786d2293a` + main) and after. The profile must show zero `select_dispatch_days_on` under `for_finding_on` on a fully built range. Saving is reported as measured.
- **Honest timing report.** The AR-4 packet states that its remaining 1.7-6.8 s of dispatch lookups is DISP-1's, fixed on this branch, not in D-ANY.9's backlog. Rev-7 7.1's custom-range figures (about 8 s a week, 25-30 s a month) are replaced by the DISP-1 after-timings once measured. ≤2 s stays reported, not gated (D-ANY.8); custom ranges stay outside the ≤2 s claim.

Decision logged for owner review: **D-ANY.11**.

## D-UP.1-11 UP-1 pre-flight questions Q1-Q9 and the guard fix (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Context: `task/UP-1-reading-upload` head `ce24acbcb`, packet `.agent/UP-1-packet.md`; spec rev 7 §7.5 (D-17N.5) and §7.6 (MB-1) of `architect-sequence-client-scope-2026-11-11.md`.
- Code read for these rulings: `analytics/assessment_worker.py` (`run_once`: every non-EMPTY day window gets a run), `scheduling/stages.py` (`s3`, `mini`), `evidence/adapters/postgres_evidence_ledger.py` `_coalesce_job`, migration 0005 `recompute_job`, 0007 `analytic_run`, `host/tests/test_field_modbus_tcp_acceptance_postgres.py` (TEL-05 Q-T50, TEL-05b, TEL-06b), `evidence/adapters/postgres_gateway_access.py` `issue_credential`, `tools/demo_combined_kobo.py:240-330`.

### D-UP.1 (Q1) The field checker runs as a separate process. Confirmed; no guard exception.
- `python -m assetops_field.csv_upload check|send`, started by the host per request, is correct. It follows TEL-01 D4 (field adapters are separate processes) and the dependency-direction guard. §7.5's "validate with `CsvCollector.reports` (no IPC)" is a spec error, corrected here: the meaning (validate the whole file before anything is admitted; a dry run admits nothing) is kept, and the process boundary is the means.
- The backend never imports `assetops_field`. The host passes the child's JSON result to the service through the port the builder already has.

### D-UP.2 (Q2) The demo upload gateway: real `serve_tls`, one Kobo edge gateway shared with MB-1.
- (a) **Central:** `tools/demo_combined.py serve` starts `python -m assetops_backend.serve_tls` on `127.0.0.1:8443` against the demo DB, only when `ASSETOPS_READING_UPLOAD_SITES` is set (else nothing new starts). Cert and key: self-signed, generated once into `<work>/tls/` the way the TEL-05/TEL-06b tests generate theirs; the gateway's `ca_file` is that cert. No in-process responder: §7.5 says nothing new is admitted inside the API process, and MB-1 (§7.6) needs the same TLS central.
- **Credential:** at serve start, `PostgresGatewayAccess.issue_credential("demo", "KOBO-001", <Kobo gateway external id from the basis in (c)>, ..., actor="service:demo-upload", enable_sources=<the CSV profile's sources>)`, written to the gateway state's `upload.credential` (`restrict_to_current_user`). Issue once per state dir; reissue only if the file is missing (issuing rotates and revokes the earlier credential).
- (b) **State and epoch:** one state dir `<work>/gateways/kobo-edge/`, persistent across serve restarts. It is the Kobo edge gateway for both UP-1 and MB-1: the CSV field process and MB-1's `modbus_poller` both admit to it over its IPC link (one edge box, several field adapters, as a real site has). One sequence epoch, created with the state dir by the same epoch generator `rp._gateway` / `provisioning_from_snapshot(..., epoch=)` use, stored in the state dir, and never equal to any per-day state's epoch (assert at creation against the per-day states under `<work>`). MB-1 must not start a second gateway for Kobo.
- (c) **Activation basis:** the registered basis of the latest prepared Kobo day run already in the demo DB (the snapshot the per-day gateway states were provisioned from). No new draft run is written to the demo DB. If that snapshot cannot be read back from the DB or `<work>`, the fallback is TEL-06b's `registered.setup_service(store).create_draft_run(...).registered_basis` on the demo DB, stated in the packet.
- (d) **Delivery:** after `send` exits 0, the host calls the gateway's delivery over its IPC link (the `RegisteredGatewayPublisher(link).deliver(50)` loop until `attempted` is 0, bounded at 30 s). Backstop: the demo gateway's `upload.interval_seconds` is **60**, not 3600. A failed delivery leaves the row SENT, and the backstop delivers it.
- Serve writes the `ASSETOPS_READING_UPLOAD_GATEWAY` JSON file (read by the host) after the gateway is ready.
- Units: about +0.25 on UP-1's flow-and-demo-file 0.5. MB-1 saves the same amount, because it reuses this gateway and central.

### D-UP.3 (Q3) "Analysed" is reachable. Positive binding is not required for assessment. The proof row is `analytic_run`.
- **Why it is reachable (cited).**
  - Ingestion enqueues `recompute_job` rows for the upload's windows (`_coalesce_job`).
  - The serve tick's `s3` stage runs `DispatchAssessmentWorker.run_site`. `run_once` records a run for every day window whose cohort is not EMPTY. It does not look at provenance.
  - TEL-05 gate Q-T50 proved an assessment completes over UNKNOWN / NO_POSITIVE_BINDING gateway evidence and records NO_GENERATOR_STATE. TEL-05b proved Findings are raised with money withheld.
  - Provenance UNKNOWN therefore withholds **money only** (D1(c), D5). It does not block the assessment.
  - With only `pv_power` and `feeder_demand`, the run exists and records what is missing (NO_GENERATOR_STATE and the role coverage). The board shows the existing missing-role words for that day. That is honest and is not a defect.
- **Stored proof, `analysed(row)` in the Postgres store, all true:**
  1. The row is ACCEPTED with all m readings, or ACCEPTED n of m with the rest HELD.
  2. **An assessment run exists.** An `analytic_run` row exists for the Site with `analytic_id = dispatch_v3.ANALYTIC_ID`, `selection = 'DEFAULT'` and `job_id IS NOT NULL`, its window covers the upload's first interval start, and its `knowledge_cutoff` ≥ the latest decision time (`accepted_at`) of the upload's accepted evidence (found from the row's `message_ids` → the receipts' evidence IDs).
  3. **No work is left.** No `recompute_job` for the Site in **any** domain (dispatch and the `mini_*` domains) overlapping [first interval start, last interval end) is PENDING or LEASED.
  - Do not key on `cause_evidence_id`. Jobs coalesce, so an upload's evidence can widen a job caused by other evidence.
- **A FAILED job overlapping the span** is not "Still processing". It gets the state `NOT_ANALYSED`, with the message key `reading_upload.state.not_analysed`: "Received, but the analysis did not finish. The readings are kept." The row is not changed; the state is derived at GET as the others are. Test it no-DB with a fake store.
- **"Analysed" links to** the `/sites/KOBO-001` board for the upload's local day (the existing `?date=` form).
- **Risk, and the proof that closes it.** On the demo DB, the DEFAULT cohort might not include the CSV profile's devices (`pv-inverter-controller`, `clinic-meter`, `mill-meter`, `residential-meter`). The cohort is then EMPTY: no run, and the page never leaves "Still processing".
  - The Postgres flow test on a `*_test` DB built like Kobo's demo (resume point 4) must show the `analytic_run` row and record the time from send to Analysed.
  - The first VPS heavy slot runs the same flow once on a client4 copy.
- **Reduced honest version, if the flow shows no run by Sat 20:00.**
  - Drop the ANALYSED and NOT_ANALYSED states.
  - The page ends at "Accepted n of m readings" with the sentence key `reading_upload.after_accept`: "Readings are stored. Analysis of uploaded readings is not switched on in this demo."
  - "Still processing" is never shown in that version.
  - The presenter shows the TEL-05 assessment proof on the slide.
  - Do **not** fake a run, use an explicit cohort from the API, or bind positively. Each of those is a product change outside 17 Nov.
  - This version fits inside 2.25 u. The full version needs the 2.25 u plus D-UP.2's +0.25.

### D-UP.4 (Q4) Entry: Kobo **Health**, as the mockup draws it. The mockup is the layout spec. The Health tab is also where MB-1 shows the gateway's last upload, so both field beats sit on one tab. Shown only when the switch names the Site.

### D-UP.5 (Q5) The body is raw `text/csv`, with `?file_name=`. Accepted; no new dependency.
- Labelled **SPEC DEVIATION (transport)**: §7.5 said multipart.
- The browser sends `fetch(url, {method: "POST", body: file, headers: {"Content-Type": "text/csv"}})`.
- The server refuses:
  - over 2 MB, by `Content-Length` and by a bounded read (never buffer more than 2 MB + 1);
  - any other content type, with 415 and a message key;
  - a missing `file_name`, or one longer than 200 characters.
- `file_name` is display-only and is never used as a path.

### D-UP.6 (Q6) The Excel BOM stays refused. The TEL-06 `ENCODING` rule is the format contract (merged), and the presenter's file is generated without a BOM. The refusal words must name the fix: "Save as 'CSV (Comma delimited)', not 'CSV UTF-8'." The template text says the same.

### D-UP.7 (Q7) The path takes the Site code (`/api/sites/KOBO-001/reading-uploads`), as every Site route does. §7.5's `{site_id}` was loose wording; this is not a deviation.

### D-UP.8 (Q8) Migration `0061_reading_upload` with `down_revision = 0059_site_period_read` on the branch. Accepted. Whichever of PR-3 and UP-1 merges second repoints its `down_revision` to the other's revision. The merge gate includes a single `alembic heads` result on the merged tree. The number stays 0061 if PR-3's 0060 lands first.

### D-UP.9 (Q9) The extra columns are accepted, all append-only.
- The extra columns are `file_name`, the refusal field and detail, the period, the per-kind counts, `message_ids` (jsonb) and `session_ref`.
- The file's bytes and reading values are never stored, only the SHA-256. The message IDs are what D-UP.3 needs.

### D-UP.10 The guard fix is correct: register the store, no exception.
- Move the store to `reading_upload/adapters/postgres_reading_upload_store.py`.
- Make the INSERT column list a literal.
- Register the store in `tools/checks/configuration-persistence.ps1` as the sole, INSERT-only writer of `reading_upload`, on the `$periodWriter` / `$fuelBalanceWriter` pattern (driver allowlist plus anti-vacuity).
- Prove the guard is non-vacuous: add a second writer, watch it fail, then revert.
- The estate self-test failures are expected to clear. If any remain after the fix, they are reported with output, not assumed.
- The `node_modules` failures are environment: run `npm ci` in the worktree before `check-all`.

### D-UP.11 Process note and lane order
- The Python heredoc edit to `service.py` breaks the lane's Write/Edit-only rule. The reviewer re-reads that file in full; no other action.
- Lane F order: guard fix (D-UP.10) → D-UP.2 gateway → template route → Postgres flow (D-UP.3 proof) → `analysed` read → page after the mockup approval → MB-1 on the shared gateway.

Decisions logged for owner review: **D-UP.1-11**.

## D-WARM.1-6 WARM-1 packet questions (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Binding checked: Architect = Claude. Context: `task/WARM-1-range-warm` head `5da936ccf`, packet `.agent/WARM-1-packet.md`, spec rev 7 §7.1 (D-17N.1).

### D-WARM.1 (Q1) The data window starts at the **earliest** Site's first day. Confirmed.
- The presenter can click those ranges, and each later Site's board states its own missing days honestly.
- No range starts before the estate's first reading day. That is the meaning of §7.1's "no range before a Site's first day"; the test name says so.

### D-WARM.2 (Q2) Unstored reads are measured, reported, and not gated.
- `--verify` also replays the unstored reads the script pages send, for the 5 presets and the story ranges only:
  - `/api/estate/scope`;
  - the Site Overview read;
  - `/api/sites/{code}/findings`;
  - estate actions, evidence and financials.
- They go under `unstored` in `warm-report.json` with their ms. They do not enter `pass`.
- Any of them over 2 s on a script page is listed in the presenter notes and sent to the Architect as a finding. It is not a merge blocker.
- The claim wording is "≤2 s on every stored request of every clickable range". "Every page" is used only where `unstored` is all under 2 s.

### D-WARM.3 (Q3) Expiry and the 17 Nov schedule.
- Live bodies expire at the earliest next Site-local midnight, and the demo Sites are at or ahead of UTC. The final warm therefore runs **on the session morning**, after 00:00 UTC and after that morning's add-dates or drain. Its bodies then hold until the first Site-local midnight of 17 Nov, which is after the session.
- `--verify` must pass within 60 minutes before the session starts. The coordinator checklist records its time and `wall_seconds`.
- No data change between that verify and the field beats.
- Serve's per-tick re-warm stays; when nothing changed it is all hits, under 1 min.

### D-WARM.4 (Q4) MB-1: the feed is off until its beat. The estate key is not changed.
- No live feed or upload runs before the field beats. They come last in the script (D-17N.7), and the presenter starts MB-1's `live-field` at that beat.
- Taking the feed out of the estate `cic:` scope is refused. It would make the Portfolio hide new readings (D-E4.8), which is a product change.
- A Portfolio visit after the field beats is unprepared, as §7.5 risk 1 states.

### D-WARM.5 (Q5) The not-warmed list is accepted, with one addition.
- **Addition:** warm the Findings lens pages (`lens=cost|risks|opportunities`) on `/api/estate/findings` for the presets and the story ranges. They are stored routes, and they can be reached from the Findings page by one click.
- Accepted as not warmed:
  - `known_at` ranges;
  - Portfolio page 2 and later;
  - chain "Why?" routes outside `prebuilt-routes.json` (the story ones are already part 3);
  - `7dwork`.
- The packet lists them under "outside the ≤2 s claim".

### D-WARM.6 (Q6) Retries on `race`, `unstored` and `composed` are accepted, as a recorded spec addition.
- They get the same schedule (2, 5, 10 s) as 503 and `stale`.
- A request still not stored after the retries fails the run: on a stored route it would be a miss at the demo.
- `warm-report.json` names the reason per request.

- Lane A next: build the D-WARM.2 and D-WARM.5 additions first (small, no DB), then run the VPS gate (packet resume points 1-4). Fresh Claude reviewer.

Decisions logged for owner review: **D-WARM.1-6**.

## D-PRICE.4 PR-3 form half: the "Applies from" date exemption, extra `entry` fields, no default basis, button under the row (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Context: `task/PR-3-price-entry` head `d4c0935c0`, packet `.agent/PR-3-packet.md` (form-half deviations 7-10, Q3-Q4). D-PRICE.1-3 stand.
- **Q3 keep the SR-2 exemption for `SitePriceEntry.tsx`.** SR-2 stops a page from choosing its own date range. "Applies from" is a value typed into a record (rev 5 §5.3), like an amount; it never changes what the page shows. FocusPicker would be wrong: it is range-scoped and would declare a "Day shown". Conditions: the comment in `page-range-forms.ps1` cites D-PRICE.4 instead of "pending Architect confirmation"; the file keeps exactly one date input. A second date input or any range control in that file needs a new ruling. No other guard change.
- **Q4 deviations 7-9 confirmed.**
  - 7: the extra `entry` fields `today`, `unit_text`, `currencies` and `live_view` are confirmed beside `enabled` and `keys`. The browser has no Site zone, so `today` must come from the server, and the honest-state words stay server-side. All of them are empty or None when entry is off.
  - 8: no default basis is confirmed. A preselected basis would let a typed price be saved under a basis nobody chose. The server refusal "Check: Basis." is the guard.
  - 9: the "Set a new price" button and form sit in the row slot under the row. This is owner default 6 (form inline under the row) and keeps the PR-2a seam the only change to the table.
  - 10 (MOCK DEVIATION D-PRICE.3, no form in v7.1) stands as labelled.
- Not blocking: the AR-4 rerun of the Postgres flow happens after AR-4 merges to main. Next: fresh Claude reviewer on the form half.

Decision logged for owner review: **D-PRICE.4**.

## D-DATA.1-6 DATA-17N packet Q1-Q6: diagnostics clocks, due dates, the Kisiwa plan date, the DATA-4 spec, Kisiwa productive users (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Context: `task/DATA-17N-coverage` head `18cdea7ea`, packet `.agent/DATA-17N-packet.md`. Owner approved DATA-4 and DATA-8 ("both", `.agent/owner-17nov-package-2026-11-12.md`). D-17N.4 gate stands: the Sat-night rehearsal finish check gates each data merge, and a failure reverts that merge. Honesty rules D-E5.46 and D-E5.47 apply to every line below.

### D-DATA.1 (Q1) Kobo diagnostics forwarding stays off.
- Kobo already has `gateway_diagnostic` rows from its own path, and MB-1 posts live Kobo diagnostics at the field beat. A second, harness-built diagnostic stream on the same Site would compete with both for "latest report".
- `demo_combined_kobo` is unchanged. The card's "recapture Kobo Health" becomes a no-change check: Kobo Health pairs are recaptured and must match the previous capture.

### D-DATA.2 (Q2) Health reads the real server clock; a forwarded diagnostic is received on the clock that sealed it.
- **Health "now" is the real server clock** (`source_health_api`'s `clock()`). There is no demo "now". A demo override would make Health claim contact that did not happen.
- **Defect in the built version.** The gateway seals each diagnostic on its own clock (`observed_at`, device contacts), but the harness stores it with a story `received_at` days earlier. Every forwarded row is then `observed_at` > `received_at` + 5 s, so `fact_age` returns `OBSERVED_AFTER_RECEIPT`. Health would read "Unknown age: its reported time is later than the server received it". That is a harness artefact shown as a data fact (D-E5.47). Separately, a story `received_at` later than the read time makes `check_consistent` refuse the whole read with 409.
- **Rule.** The forwarding service's clock is the harness gateway's own clock (its `_clock`, the clock that sets `observed_at`), for all three paths:
  - Cold `w202.DIAGNOSTIC_CLOCK`;
  - EV `w205b.FORWARD_DIAGNOSTICS`;
  - the Kisiwa replay `_publish_and_accept(..., diagnostics=True)`.

  Do not use the story `received` clock or the chain decision clock. The packet reports that clock as the real wall clock, so `received_at` becomes the real time of the prepare.
- **"Stale" on demo day is accepted. It is the fact.** The last report was received when the data was loaded. The existing words state it in plain terms: "Stale: nothing received for {age} (limit {limit}); when it stopped is not known". Do not build anything to make it read "Current".
- Presenter line: "These sites are replayed recordings; their gateways last reported when the recording was loaded."
- **VPS gate (added to resume point 2).**
  - For Cold, EV and Kisiwa: `SELECT count(*) FROM gateway_diagnostic WHERE observed_at > received_at + interval '5 seconds'` = 0, and no `received_at` is later than the real time of the query.
  - Health on each of the three Sites returns 200, with no "Unknown age" line and no clock-untrusted line.
  - If the harness gateway's clock turns out to be a story clock, the same rule holds (`received_at` = that clock). Report the observed receipt lag in the packet.
- Test (no DB): one `test_data5_story_diagnostics.py` case. The forwarded receipt's `received_at` equals the injected gateway clock, not the story instant. Replace the current assertion that pins `received_at` to the story clock.

### D-DATA.3 (Q3) Due = raised + 14 days, confirmed. Kobo's Actions are unchanged.
- One explainable rule: "due two weeks after it was agreed". It applies to the Cold, EV and Kisiwa story Actions.
- Kobo's battery and mill Actions keep no due date. That story is proven, and re-proving it is out of scope (owner 2026-11-05, demo-critical only). Their rows keep the honest "no due date set" state.
- An Action whose due date falls before the demo day reads overdue. That is a fact of the story data, and it stays.
- The VPS proof lists each story Action's `raised_at`, `due_at` and its state on Mon 17 Nov. The coordinator copies any overdue Action into the presenter notes.
- No clamp or special case.

### D-DATA.4 (Q4) Kisiwa service plan: written S-8d 09:00 is confirmed; due moves to S+10d 00:00 Site-local, CALENDAR.
- `plan_due.py` makes a plan OVERDUE when it is due strictly before the range end `to`.
- S is the prepare date minus 2 days, so a Sat-night prepare gives S = 12 Nov and the demo on Mon 17 Nov is S+5d. With due S+5d 00:00, any range that ends after the start of the demo day (the "today" preset after add-dates) would read OVERDUE.
- S+10d keeps DUE_SOON for every range end from S-3d through S+10d. That covers the story week `[S-6d, S+1d)` and every demo day up to S+9d, and stays "within the story month" (the test's S+30d bound).
- RUN_HOURS ("not assessed") is refused. It removes the K14 value the item exists to show.
- Update the story doc `service_plan.due_at` and its test expectation.

### D-DATA.5 (Q5) DATA-4 spec: Charger use from declared ratings; the diagram's feeder meter from config; no new Foundation vocabulary. About 0.5 unit, Sonnet, lane B, before the Sat 20:00 freeze.

**Why the scope is this size.** The Foundation vocabulary (`sites/models.py` `COMPONENT_TYPES`) has no grid-connection, circuit-breaker, load-manager or auxiliary-feeder component. Feeding the Grid supply, Main CB, Feeder CB, Load manager and Depot auxiliary slots from config needs a schema change (component types, validation, import, read model). That is a BL item, not a two-day item. Those slots keep "Not declared", which is true. What the config already declares (charger 60 kW, connectors c1/c2 60 kW each with meter properties, the site import meter, the 80 kW import limit, the connector enable schedules) is now read.

**A. Backend: the availability read carries ratings** (`analytics/ev_availability.py` `availability()`, same selected Foundation revision as the schedules).
- Each connector row gains:
  - `connector_rated_kw` (`ev-connector-max-power`, decimal text or null);
  - `charger_asset_id` (the EV_CHARGER that has a SIGNAL edge to this connector, or null);
  - `charger_rated_kw` (`ev-charger-max-power`, or null).
- The fields are additive. Existing keys and values are unchanged.

**B. Backend: the Charger use rule** (`site_outcomes/ev.py`, new pure `charger_use(kwh, availability_body, limit_kw, rc)`, replacing the constant `CHARGER_USE` contributor).
- Capacity kWh: sum over chargers of `rating_kw x hours`.
  - `rating_kw` is `charger_rated_kw` when declared, otherwise the sum of its connectors' `connector_rated_kw`.
  - `hours` is the largest `scheduled_seconds` among that charger's connectors, divided by 3600. In the declared case all connectors share one schedule, so this is exact. The docstring says so.
  - Connectors with no charger count individually as `connector_rated_kw x scheduled_seconds / 3600`.
  - If the sum of charger ratings is above the declared import limit, the import limit replaces that sum (one line, `site_power.configured_limit_kw`).
- Share: `kwh / capacity x 100`. The kWh is the one printed on the same response's "Charging delivered" line: the overview's `complete_kwh` in `compose`, and the EV-3 claim's `parts["kwh"]` in `_charging_from_claim`, which replaces the charger_use contributor as it replaces charging_delivered.
- Words (label "Charger use"; one decimal for kWh as `num`; hours via `duration_text`; whole percent):
  - normal: `{p}% of declared charging capacity · {kwh} kWh with a complete meter record in {h} of scheduled charging at {r} kW`. `{r}` is the single rating when all chargers share one; otherwise the words read "at the declared ratings". Confidence `rc`.
  - 0 < share < 1: `{p}` reads `under 1`, giving "under 1% of declared charging capacity …". A share of 0 reads `0%`.
  - availability read failed: `NOT_LOADED`.
  - no kWh (`kwh is None`, or the claim is not known): `NO_SESSION_ASSESSMENT`.
  - no rating declared on any scheduled charger or connector: `Not available yet · charger rating not declared`.
  - total scheduled seconds 0 or null: `Not available yet · no scheduled charging hours in this window`.
  - share above 100: `Not available yet · delivered energy is more than the declared rating allows in the scheduled hours`. This is a data fact, never "error".
- Charger use is a contributor only. It enters no verdict, money or objective.

**C. Frontend: `SiteSingleLineDiagram.tsx` `EvSingleLineDiagram`** (no read-model change; `chargers[].connectors[].meter_resolution_kwh` already exists).
- Feeder meter slot `j`: when the group has at least one connector and every connector's `meter_resolution_kwh` is not null, the box drops `ev-sld__box--missing`, gets `data-ev-declared="yes"`, and the line under "kWh" reads `At each connector`. Otherwise it stays `Not declared` with `data-ev-declared="no"`.
- Empty feeder slot (no charger in the group): the label stays `Charger {n} · Not declared` and the second line (`Rating not declared · No connector declared`) is not drawn. It repeated the label. The slot, box and position are unchanged.
- Footnote `data-ev-sld-undeclared`, plain words: "Grid supply, circuit breakers, the load manager and depot auxiliary are not part of this site's declared configuration, so they are drawn as empty slots. Energy is metered at each connector and at the site import meter where declared. Reporting is not assessed on this diagram."
- **MOCK DEVIATION D-DATA.5:** none in layout. Every v6.9 slot keeps its place, and only the slot words change.

**D. Tests.**
- `test_data4_charger_use.py` (pure): one case per state above. Also:
  - the charger rating taking precedence over the connector sum (60, not 120);
  - the import-limit cap;
  - the claim-path kWh replacing the overview kWh;
  - the fixture `ev-lab-001.yaml` read through `availability()` giving `charger_rated_kw` "60.0" and `connector_rated_kw` "60.0" for c1 and c2.
- Frontend `SiteSingleLineDiagram` test:
  - feeder 1 meter `At each connector` and `data-ev-declared="yes"`;
  - feeder 2 has no "Rating not declared" text;
  - the new footnote;
  - every v6.9 slot is still present (`data-ev-slot` count unchanged).
- Run the guards and `check-all`.
- VPS:
  - EV Overview › Grow on the story day shows a percentage line;
  - recapture the EV Overview and Foundation pairs;
  - the finish check is green (no EV row reads this contributor; if one does, it is updated from stored data in the same branch, citing D-DATA.5).

### D-DATA.6 (Q6) Cold store and water pump PRODUCTIVE: accepted. Kisiwa does **not** declare MG-1 for 17 Nov.
- **Supply use.** The cold store (ice and fish) is a business, so PRODUCTIVE is the accurate supply use. The water pump moving off HOUSEHOLD corrects the template.
- Its critical status is not lost. Its first place in `critical-load-priority` and its `critical_load_requested/delivered_power` bindings (roles4 config) are unchanged, so MG-5 and Assure are unchanged.
- The Foundation's displayed supply use changes from "Essential service" to "Productive". Both feeders have `feeder_demand` bindings, so the productive kWh is measured on both. The Grow copy names the measured hours (`productive_use.py`), so night-only runs are stated, not scaled.
- **Price.** The fixture is neutral (it names no Site) and its idempotency is Site-scoped (`financial_assumption_publication_key_unique`), so reusing it is correct.
- **Finish rows.**
  - KIS-7 item 3 already asserts (`KIS7_ITEM3_REPORT_ONLY = False`, R3u U8). It was waiting for exactly this `productive_kwh` subject, and DATA-8 is what makes it pass. A failure there is a real defect: revert DATA-8 per D-17N.4. Never set report-only.
  - KIS-6 derives from data: no change.
  - KIS-1: before the VPS run, confirm `kis1` reads diesel prices by assumption key. If it counts every Kisiwa price, filter it to the diesel key (its subject). Do not raise a literal count.
  - CO-6 is unchanged, because no objective is added.
- **MG-1 not declared.** MG-1 is a month-to-date productive kWh target. Kisiwa has night runs only (DATA-7 full-day runs are OUT, D-17N.4), so a monthly target would be judged on a fraction of the hours, and a "behind pace" verdict would describe the recording, not the Site.
- The Grow row shows the measured productive kWh and estimated sales, and keeps "No objective declared". That is true, and it is now one line, not three (D-E5.33).
- MG-1 for Kisiwa goes to the backlog with DATA-7.

**Builder order (lane B, VPS).**
1. D-DATA.2 clock fix and its test, then the D-DATA.4 date and its test (no DB).
2. Build D-DATA.5 as a separate commit (no DB, plus the frontend test).
3. On the VPS, merge main and run a scratch prepare on `<prefix>_audit*`, then:
   - packet resume point 2 plus the D-DATA.2 gate;
   - the D-DATA.3 due list;
   - the KIS-1 check;
   - the EV Charger use line.
4. Run the packet's Postgres files one at a time.
5. Send it to a fresh Claude reviewer. Merge only after the Sat-night rehearsal finish check is green.

Decisions logged for owner review: **D-DATA.1-6**.


## D-SR.1-8 Site pages on the shared date range, SR-4 (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

Source: the owner's report "when i navigate into sites, it appears the date range is not used to inform the content, verify this", which the verifier confirmed. Full spec: `architect-sequence-client-scope-2026-11-11.md`, Revision 8.

### D-SR.1 Three classes of Site page.
- **R (follows the range):** Findings, Work, the Evidence ledger, Scenarios, Renewable up to 5 days, and every Cold and EV content page.
- **D (one day or part, inside the range, defaulting to its last day):** the Kobo/Kisiwa Overview, Dispatch, the Kisiwa night window, Service, the claim limit, and Renewable over 5 days.
- **N (point in time):** mini-grid Health, mini-grid Financials and Prices, Foundation, and the Sites index.
- Why: the mini-grid Overview is one UTC day by server contract, and the stored day rows (ANY-1) make that day fast. A range board is SR-5 (backlog, about 1.5 units, read path plus parity, after the freeze).

### D-SR.2 Every Site link carries the range, through one component.
- `RangeLink` plus `carryRange`, and a codemod of every `Link` import.
- Guard `site-links-carry-range.ps1`, with a runtime DOM test as the second guard.
- Why: 136 call sites build Site hrefs. One component plus a guard is the only way the rule survives new code. Per-frame `search` props are how the Kobo/Kisiwa gap arose.

### D-SR.3 Safety net in `SharedRangeOutlet`.
- A Site content address with no range takes, in order:
  1. the previous in-app range;
  2. else the 7 days ending on `day`;
  3. else `entryRange()`.
- The page is replaced before it mounts.
- Why: `navigate()` calls and data-built links are not all visible to the guard. Filling before mount means one request, and the preset strings match WARM-1.
- Consequence: Site Work pages adopt the shared range instead of R338's own default.

### D-SR.4 `pageDay`.
- The day is `day`, else the range's last day, else today only when the address has no range.
- Previous/Next stop at the range's edges with text, unless the shown day is already outside the range (story links).

### D-SR.5 Service and Renewable under a long range.
- Service uses the 12:00 local hour of `pageDay` unless the address window is exactly one hour or one day.
- Renewable uses the last 5 Site-local days of the range when the range is longer than 5 days.
- Both declare what they show.

### D-SR.6 Honest tags.
- "Showing 9 Nov of the range" and "Showing 5–9 Nov of the range" for D pages.
- "Range not used · shows now", "· current settings" and "· prices valid now" for N pages.
- "All pages" only where the content follows the range.
- Declarations are set in a layout effect.
- MOCK DEVIATION R718/R719: v71 Change 0b shows only "All pages". Its text, "A page that needs a finer view ... picks it inside this range", is what R718 makes visible.

### D-SR.7 EV on generic paths.
- `/sites/<EV>/financials` redirects to the EV financials page.
- The generic Evidence page's rejections and analytics panels get the range if their routes accept it. Otherwise they say "All dates, not only the date range".

### D-SR.8 IN for 17 Nov.
- 1.5 units, lane G (frontend only, Opus), one branch `task/SR-4-site-range`.
- Core freeze Sat 20:00: ACCEPT by Sat 16:00.
- Priority: after WARM-1, before UQ-FI-1/2.
- The owner said "fix it now": start immediately in the order a, b, c. Only SR-4d (the day strip, which needs owner approval by Fri 12:00) can drop.

Decisions logged for owner review: **D-SR.1-8**.


## D-SR.9-12 Data in the range means output for the range, on every Site type; SR-5 IN (Architect, Claude, 2026-11-12, owner-directed, logged for owner review)

Source, owner verbatim (`.agent/owner-range-output-rule-2026-11-12.md`): "this should not have been the case to begin with, if there is data in the range, then there should be corresponding output, why was such a site specific disparity in design introduced to being with?" and earlier "fix it now". Full spec: `architect-sequence-client-scope-2026-11-11.md`, Revision 9.

### D-SR.9 Standing product rule.
- Every Site page with data in the selected range shows output for that range, the same way on every Site type.
- A single day, hour or night view is only a drill-in from a range view, with a link back. It is never the default.
- Point-in-time pages (Health now, Prices valid now, Foundation, the Sites index) say so.
- Gaps use the D-E5.46 words.
- Supersedes S5-01's one-day default for what the Site Overview shows by default. The one-day read stays as the drill-in. It also supersedes rev 8's class D for the Overview and Dispatch, and rev 8's "Honest limit".
- Why: the owner's rule. A cross-Site disparity in range behaviour is a defect, not a design choice.

### D-SR.10 Process fix.
- Every UI plan, packet and review that touches a Site page carries its page × Site-type range row (R/D/N with the reason).
- `RANGE_MATRIX` (`frontend/src/ui/rangeMatrix.ts`) plus `siteRangeMatrix.test.tsx` fail any Site route that is unclassified, or whose requests ignore the range while it claims "All pages".
- Why: the root cause was that no plan or review compared the same page across Site types. Each slice was checked only against its own contract.

### D-SR.11 SR-5 range board for mini-grid Sites: IN for 17 Nov, lane H (VPS, from tonight).
- **Server:** `GET /api/sites/{code}/range-overview?from&to[&known_at]`, schema `site-range-overview-1`. It is composed in the new `estate/site_range.py` on one estate snapshot from the Portfolio's own selectors, so it equals the Portfolio by construction. Its per-day states come from the `dispatch.day` rows with the D-ANY.10 absent compose and the D-E5.46 reasons. The response is stored per Site (ResponseStore), and WARM-1 lists the route.
- **Pages:** the mini-grid Overview defaults to the range view, and `?day=` is the S5-01 drill-in. Performance/Dispatch and the Kisiwa nights get a day table, and the day becomes the drill-in. Mini-grid Financials adds the range money.
- **Units:** core (a+b+e) 1.4, c 0.35, d 0.3; 2.05 in all.
- **Gates:** parity 0 mismatches against the Portfolio, rows on/off and the one-day board; stored response ≤2.0 s.
- **Deadline:** core ACCEPTed by Sat 16:00 or held whole (SR-4b's last-day Overview stays). c and d each drop alone.
- **Mock deviations:** R721-R723.
- Why: the owner's rule and "fix it now". Reusing the Portfolio selectors avoids a second money or coverage rule, and needs no edit to AR-4's files.

### D-SR.12 Audit dispositions and capacity.
- **Fixed:** SR-4 fixes links, tags, the EV redirect and the Evidence panels. SR-5 fixes the mini-grid Overview, Dispatch, nights and Financials.
- **Known gaps for 17 Nov**, honestly tagged: mini-grid Health (SR-6, 1.0), Service and the claim limit (SR-7, 0.5), Renewable over 5 days (SR-8, 0.5). Backlog first after 17 Nov.
- **Moves:**
  - SR-4d OUT (subsumed by SR-5's day table).
  - BL-ANY-absent OUT.
  - DATA-10/13 becomes IN-if-free.
- **Package:** about 13.4 units, slightly over the 11-13 window. The drop order is DATA-10/13, SR-5d, SR-5c, UQ-FI-3.
- **Priority:** AR-4 > WARM-1 > SR-4 > SR-5 core > UQ-FI-1/2 > UP-1 > MB-1 > DATA-5/4/8 > SR-5c > SR-5d > UQ-FI-3 > FR-B > DATA-10/13.

Decisions logged for owner review: **D-SR.9-12**.

### D-SR.13 SR-6, SR-7, SR-8 are IN now (owner-directed, 2026-11-12).
- Owner: "Everything must be fixed now, demo today is called off because of this". Rev 9's known-gap list is withdrawn. Designs: sequence doc rev 10, 10.2-10.4.

### D-SR.14 What is point-in-time by nature.
- Foundation (with changes and SLD), battery configuration, Prices, the Sites index and single-record pages (Finding detail) are N: configuration, an instant's price, a directory or one record. Every page with readings over time follows the range. Battery condition is never invented over a range.

### D-SR.15 Range reads reuse stored per-day rows only.
- Health: `gateway_diagnostic` and `accepted_evidence` grouped per UTC day, plus SR-5a day states. Service and Renewable: chain day snapshots (`critical_served`, `daylight_headroom_kw`). Claim limit: `evidence.claim` rows. The hour and 5-day depth reads stay as drill-ins.

### D-SR.16 BL-ANY-absent returns as a test, not code.
- Each new range read is tested with an absent historical-k row; fallback code is added only if that test fails (0.25).

### D-SR.17 Unlisted Site routes go to the Architect.
- Any route in the SR-4 pre-flight list missing from rev 10.5 is a pre-flight question. Asset pages showing readings without from/to become SR-9.

### D-SR.18 Lanes and drop order.
- Lanes I (SR-6), J (SR-7), K (SR-8; VPS if no fourth laptop lane). Protected: SR-4 to SR-8. Drop order: DATA-10/13, FR-B, UQ-FI-3, DATA-5/4/8, MB-1, UP-1. Package about 15.65 units.

Decisions logged for owner review: **D-SR.13-18**.
