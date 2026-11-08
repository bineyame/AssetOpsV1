# Architect answers to the owner: adding days, and retaking screenshots (2026-11-08)

Claude Architect (binding: Claude, `.ai/ROLE_CONFIG.md:9`). Read-only on code, main `b9320136c`. Owner text:
`.agent/owner-questions-ingest-captures-2026-11-08.md`. This file stands beside Part D.3 and Part E of
`.agent/architect-combined-pass-2026-11-08.md`. It corrects them where noted. It does not edit them.

## Plain-language answers

### 1. Why can't the demo just keep taking in new days, for every Site?

You were right to push back. **The product can take in a new day of diesel-site data.** That part works for Kisiwa
in the same way it works for the other Sites. The meter data arrives through the same gateway connection. Fuel
deliveries and tank dips are saved as operational records. The demo itself loads Kisiwa that way.

What does not exist is a **demo shortcut that adds a Kisiwa day.** The helper that adds a day to a prepared demo
was built for the first three Sites. Kisiwa joined later, and nobody extended the helper. That is a gap in our demo
tool. It is not a gap in what the product accepts.

There are **two real product gaps** for a diesel Site. You should know them before you speak to finance or
operations buyers:

- **Nothing checks a new diesel night by itself.** When a new night's data arrives, it is stored. But the
  "was fuel lost tonight?" check, and the problem it raises, run only when someone starts them by hand. The
  regular background refresh does not run them. In the demo they look automatic only because the preparation
  runs them. **In a demo, nobody should say that diesel nights are checked automatically.**
- **Nobody can type in a fuel delivery or a tank dip on screen.** The Operational records page lists them. Its
  entry form is a picture only and saves nothing. Records come in only through the system's data connection.

**Your idea: one demo build, kept fresh by adding each new day.** It is sound, and better than I first judged.
Here is what it fixes:

- The story's dates never move. So the script, its dates and its screenshots are written once.
- "This week" views fill with real, fully checked days, instead of going empty.

Here is what it does not fix:

- **A Site page still opens on today.** A day can be added only after it ends, so today has no readings yet. The
  presenter keeps using the dated links. (In real life, readings for today stream in.)
- **The story keeps getting older.** Some reads only look back 30 days, for example "verified recently". If one
  build is kept from 10 Nov to 20 Nov, the story is almost two weeks old by the end. We have not measured whether
  anything changes at that age.
- **Adding days can honestly change a story result.** The tool already blocks one known case: a full Kobo day
  right after the trial would take the fix off "Verified". This is the product working as designed. It means each
  added day must be followed by the same daily check.

**My recommendation, for you to decide:**

- **10 Nov:** as planned. One build on 9 Nov, then a short check on the morning of the 10th.
- **16–20 Nov:** **one** fresh build on Sun 15 Nov, then roll it forward. Each evening, add that day for Kobo, and
  for Cold and EV on their weekly day. Then run the usual check (about 20–30 minutes in total).
  - This replaces the second build planned for Wed 18 Nov.
  - The script and screenshots are done once, for that build.
  - If any check fails, we fall back to a fresh build, as now.
- **Kisiwa:** for these demos it stays on its story week. Its fuel story is judged night by night on dated pages, so
  that is honest. Adding Kisiwa days to the demo tool is about **1 unit of work plus review**, with medium risk.
  It does not fix the "not automatic" gap above. That gap is a product change of about **1.5–2 units**. I recommend
  that both wait until after the demos, unless you want to say "automatic diesel monitoring" to buyers. In that case
  the product change comes first.

### 2. Why were the screens retaken, if the screen only displays checked data?

Your reasoning is right. The screen adds no logic, so one layout check is enough. **The retake was caused by our
own mistake, not by any real need.** The first set of screenshots was taken from a server started in the wrong
folder. That server could not see the build's comparison files, so the pages showed "Awaiting evidence migration".
The data and the screens were fine. The retake repairs a bad capture. It is not a second check.

Screenshots are taken for two different reasons:

- **Checking the layout against the design mock.** This is needed once per screen design. It is needed again only if
  screen code changes. The full set already exists (168 pairs on test data). After tonight's corrected retake, the
  four-Site set exists too. **No more layout captures are needed before the demos.**
- **Pictures in the client script.** These show dates and figures from one specific build. A new build moves the
  story dates, so the pictures go out of date. **Rolling one build forward (answer 1) stops that.** The pictures are
  then taken once per demo week, not once per build.

**Minimum plan:**

- **10 Nov:** one set of script pictures from the 9-Nov build (about 10 minutes of machine time), dropped into the
  script once.
- **16–20 Nov:** one set from the 15-Nov build, and none after that.
- **Every demo morning:** no screenshots. Instead, an automatic check that the demo pages load and do not show
  "Awaiting evidence migration" or "not released". That is the same check that would have caught tonight's mistake
  before any picture was taken.

**What this saves:** compared with the current plan for 16–20 Nov, one full rebuild (about 2.5 h of machine time),
one picture set, and one script refresh (about 0.1 unit). If the script names days as "story day" and "five days
before", and labels its pictures "from the rehearsal build", even the 15-Nov picture set becomes optional.

### Decisions for you

1. **For 16–20 Nov: one build rolled forward daily (recommended), or two builds as in Part D.3?**
2. **Do you want to say "automatic diesel monitoring" to buyers?** If yes, the automatic diesel-night check
   (about 1.5–2 units) must be built and reviewed before those demos. If no, it waits until after the demos, and the
   script must not imply it.
3. **Script pictures:** exact pictures from the demo build (one set per demo week), or labelled illustrative
   pictures taken once?

---

## Technical detail

### T1. Real ingestion paths, and what a Kisiwa-type Site uses

| Path | Code | Kisiwa today |
|---|---|---|
| Gateway telemetry (Batch V2, authenticated registered gateway) | `POST /api/ingestion/batches`, `backend/assetops_backend/evidence_api.py:156`, `:317-333` (V2 needs a gateway credential), `BatchIngestionService` | **Works.** The demo's Kisiwa runs go through a real gateway process into `BatchIngestionService.submit` (`host/tests/test_s6_verification_replay.py:195-225`, called from `tools/demo_combined_kisiwa.py:779-780`). Only the clock is set to a story instant. |
| Operational records (fuel delivery, tank dip, site visit) | `POST /api/sites/{site_code}/work/operational-records`, `backend/assetops_backend/work_api.py:185` | **Works through the API.** The demo posts FUEL_DELIVERY and TANK_DIP through `work_service.post_operational_record` (`tools/demo_combined_kisiwa.py:393-412`, `:760-770`). **No UI entry:** the Operational records form is inert, with "no POST" (`frontend/src/work/OperationalRecords.tsx:300`, MOCK DEVIATION D1). |
| Scheduled assessment (tick) | `backend/assetops_backend/scheduling/tick.py:1-25`: s3, cold_assess, ev_assess, mini, opportunity, s4, chain_threads, consequence, cold_consequence, ev_consequence | Kisiwa's mini-grid board domains are covered (a Site with accepted evidence is selected, `:13-15`). **The fuel-night assessment and raise have no stage.** |
| Fuel-night assess and raise | `backend/assetops_backend/fuel_balance/worker.py:1-14`: "There is no tick stage, job domain or HTTP route in v1" | **Manual CLI only.** The prepare calls it in-process at story instants (`tools/demo_combined_kisiwa.py:513-544`). |
| CSV or file upload of readings | none found in `backend/assetops_backend` (the only `csv` hits are gateway diagnostics) | n/a for every Site |

Correction to what you were told: "add-day supports only Kobo, Cold and EV" is accurate for the tool
(`tools/demo_combined.py:919-920`, `choices=…CORE_SITES`, "no Kisiwa day kinds"; Kisiwa has no `add-day` child in
`tools/demo_combined_kisiwa.py:874+`). But the reason is tool scope. It is not ingestion. The product gaps are the two
rows marked in bold above.

### T2. What ages on a build, and what rolling forward changes

- S = prepare day − 2 and is fixed (`tools/demo_combined.py:146-148`). `add-day` appends days at the build's S,
  received at DB now (`tools/demo_story_days.py:512-528`). It refuses a day that has not ended
  (`DAY_NOT_IN_PAST`, `PAST_MARGIN` 5 min, `:38`, `:502`, `:525`) and a day before S−board-window (`:485`). Cold and
  EV step weekly (`:476`). There is no multi-day command: one call per Site-day. Calling it daily is the supported
  shape, but a run of 5 or more consecutive adds has not been tested.
- Clock reads that do not move with S:
  - The Site board defaults to today (`frontend/src/sites/PerformanceDispatch.tsx:87`). Rolling forward still leaves
    today empty. This needs the after-demo fix in Part E.5.
  - The 30-day lookbacks: "verified recently" (`estate/coverage.py:40`, `:412`), the action observation window
    (`actions/service.py:45`), and the work backdate limit (`work/model.py:37`). These two windows affect **live
    writes** made during a demo against story-dated items. `finish check` skips write rows
    (`tools/demo_combined_finish.py:1538-1539`), so it does not prove them.
  - Month-to-date reads (D-W1-15). 16–20 Nov stays inside November, so they are fine.
- Adding full days can change story states honestly. One case is refused because of this: `FULL_DAY_AFTER_TRIAL`
  (`tools/demo_story_days.py:488-492`). Every add is followed by a tick and `finish check`.
- Cost per added day, from the measured baseline: Kobo about 429 s; Cold about 260 s and EV about 213 s, only on
  their weekly day (`Docs/demo-sprint/client-demo-plan.html:157`, `:858`). That is about 10–15 min a day plus E4-lite.
  A re-prepare costs about 2.5 h.
- Recommended rolling window: from S to about S+7 (prepare 15 Nov, S = 13 Nov, demos to 20 Nov). Daily `finish check`
  is the gate, and a failed check means re-prepare. Do not carry the 10-Nov build (S = 7 Nov) into 16–20 Nov; that
  age is unmeasured.

### T3. Sizes, if the owner wants them

- **Kisiwa `add-day`** (demo tool only): about 1.0 unit plus review, medium risk.
  - Draft a day run from the previous run's end state of charge and fuel. The handover holds start states for story
    runs only (`tools/demo_combined_kisiwa.py:773`).
  - Publish it through the gateway helper.
  - Optionally post a dip record.
  - Then call assess and raise for that night. These are the same calls as `:513-544`, but on the DB clock.
- **Fuel-night tick stage** (product): about 1.5–2 units plus review, medium risk. It changes the scheduler, a
  protected seam. It adds a `fuel_balance` stage that assesses and raises the closed nights per diesel Site,
  idempotently. Revisions are `APPENDED` or `REUSED` (`fuel_balance/worker.py:4-8`).
- **Operational-record entry form** (product): this is the inert form in the mock. Not demo-critical.

### T4. Captures

- **Cause of the K8c retake.** The process error is confirmed in Part E.1. The serve ran from the main checkout,
  without `<work>/tree/var/evidence`, so the gate was closed (`analytics/performance_comparison.py:223-224`). The
  data and the UI were correct.
- **Layout fidelity** is a property of UI code. The fixture index (W1-F5b, 168 pairs) and the K8c-r four-Site index
  together cover it. Recapture only after a UI code change.
- **Script pictures** depend on the build's S. With one rolled build per demo week, this is one E5 per week. DS-1f
  runs once per week, not once per build.
- **Daily gate without captures.** The K8c-r probe set (Part E.3 step 4) asserts:
  - a 200 from the Kisiwa `finding-index`;
  - no "Awaiting evidence migration" on the Kobo board;
  - no "not released" on the Kobo Finding.

  Together with `finish check`, it becomes the morning check. It runs as a scripted HTTP and text check, not
  screenshots. Writing it is about 0.1 unit. Alternatively, run the three probes by hand from E.3 step 4.
- **Superseded by this answer, if the owner accepts decision 1:** Part D.3 points 4–5 (W-2 on 18 Nov and the
  per-build DS-1a refresh for W-2). Part D.4's Wed 18 row becomes "add-day plus E4-lite".
