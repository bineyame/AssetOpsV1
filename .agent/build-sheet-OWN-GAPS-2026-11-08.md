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
