## DD1b2-R4: R3's kill conditions, whether the figure stands beside the mill, the owner question (Architect, Claude, 2026-11-07)

Input: R3, `.agent/DD-1b2a-m2.json`, `.agent/DD-1b2a-probe-3.json`, and my own read-only queries on `assetops_demo3_dd1b2q_test` (`default_transaction_read_only=on`; nothing written, no code changed). **MEASURED** = stored rows or my queries; **ARITHMETIC** = sums on them; **READ** = code. **(b) lives on R3's words, but my recommendation moves to (a).**

### 1. R3's kill conditions: neither fires

- **"A figure of zero": not met.** It meant a figure that says zero, or no figure. R3 listed it beside "not SUPPORTED" as "nothing to show". The stored high is 2, and `rules.py:370` (q2 ruling 8) defines positive headroom by the upper bound: "0-1 kW stays eligible, low 0". A low bound of 0 is that rule working. So the owner is asked, not told.
- **"If they differ, (b) is dead": not met.** It meant the fields that could show the runs were set up differently. `run_identity_sha256` hashes `run_id`, `created_at`, `deterministic_identity` and `registered_basis` (READ, `runs/source_publication.py:24-33`), so two runs can never share it, and R3's own list also named run ID, which differs by definition. Reading it as a basis field would make (b) impossible from the start, which is not what R3 proposed.
- **Field list if (b) is chosen.** All evidence `REGISTERED_SIMULATION`; one tenant and Site; equal `snapshot_sha256`, `foundation_revision_id`, `binding_set_revision_id` (all MEASURED equal over the 10 runs); `MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS` the only reason, so `RUN_IDENTITY_CONFLICT` (two digests within one run) still limits. Excluded by name: `run_id`, `run_identity_sha256`, `deterministic_identity`, `created_at`. Scenario differs on purpose (day and night pieces), so it is not a basis field.

### 2. The figure is not defensible beside the mill result as a size of spare solar

**What the study computes.** MEASURED hour rows, S-15 (2026-10-21), kW. Other study days have the same day totals. Margin 5 and uncertainty ±3 are derived from these rows.

| Hour | Solar available / delivered | Load (mill) | Room, low-high | Decision |
|---|---|---|---|---|
| 06, 07 | 9 / 9 | 13 (0) | 0-0 | Excluded, `HEADROOM_NON_POSITIVE` |
| 08, 09 | 33 / 33 | 12 (0) | 13-19 | Excluded, `CHARGE_OBLIGATION_ACTIVE` |
| 10, 11 | 50 / 42 | 12 (0) | 30-36 | Excluded, same |
| 12 | 50 / 14.6 | 13 (0) | 29-35 | Excluded, same |
| **13** | 50 / 13 | 13 (0) | **29-35** | **Eligible** |
| **14, 15** | 36 / 32 | 32 (18) | **0-2** | **Eligible** |
| 16, 17 | 9 / 9 | 22 (3) | 0-0 | Excluded, `HEADROOM_NON_POSITIVE` |

- `frozen_result` takes the lowest low and the lowest high over eligible hours (READ, `headroom_on_every_eligible_day`), so **0-2 is hours 14 and 15 alone.** Hour 13's 29-35 does not enter.
- **Hours 14 and 15 are tight because the old mill run sits in them** (18 of 32 kW). The study measures room beside the load the Action then moves. After the change the same hours read 2-8 (MEASURED, S-5).
- **The two codes do not lower the number.** They remove 9 of 12 hours. The 8,880 IDs per code are the same set: 1,776 × 5 days, the day-level union of each day's hours (READ, `_fold_day`; 8,935 less the 55 boundary IDs). They do not locate the hours.
- **The 06:00 restart does not cause 0-2.** Hours 14 and 15 have no charge request. The restart affects only when charging ends. The cause is the authored afternoon mill run plus the rule. **No number is to be tuned.**

**What supplied the extra energy.** MEASURED day totals, identical on S-8, S-6, S-5:

| kWh a day | S-13..S-11 | S-8, S-6, S-5 | Change |
|---|---|---|---|
| Solar available | 374.0 | 374.0 | 0 |
| Solar delivered | 277.6 | 351.6 | **+74.0** |
| **Solar unused (ARITHMETIC)** | **96.4** | **22.4** | **-74.0** |
| Mill | 42.0 | 110.0 | +68.0 |
| Other load, 06:00-18:00 | 166.0 | 166.0 | 0 |
| Battery charged / discharged (15-min rows) | 102.0 / 143.8 | 99.3 / 138.0 | net 3.1 less drawn |
| Generator | 3.24 (15 min, in the 05:00 hour), **0 on S-13** | 0 | none during mill hours, before or after |

- **The extra came from unused solar.** 74.0 less 3.1 less 3.24 is about 67.7 against +68 (ARITHMETIC; losses and sampling not separated). Unused solar before the change, by hour: 8, 8, 35.4, 37, 4, 4 kW over hours 10-15. **So the answer to "where did the other 62 kWh come from" is good, and it is the study's figure that looks wrong, not the mill.**
- **The battery still fills:** 100% at 14:00 on both, later than before (12:00 reads 99.2 before, 75.5 after).
- **It is more milling, not the same milling moved.** Mill hours went from 14:00-18:00 to 08:00-16:00; the whole day's mill energy rose 42 → 110, and nothing else fell. Earnings 10.50 → 27.50 USD (MEASURED, P6). That extra work is authored.
- **"Do not claim a litre" stands, and is stronger:** S-13 ran the old mill pattern with 0 generator, so the drop is not the mill's. There are 0 `fuel_level` rows at the Site.
- **"About 3 usable hours" needs correcting.** 3 is the count of hours the rule calls free. Solar was unused in 6 hours and the mill ran 8.

**A new limit the script must carry.** SOC jumps at 06:00 every day, from 30.3 or 31.5 to 55 (MEASURED). Battery discharged minus charged is 41.8 kWh a day before and 38.7 after (ARITHMETIC): that gap is what the restart covers. After the change only 22.4 kWh of unused solar remains, so about 16 kWh a day may be uncovered on continuous days (ARITHMETIC, ignoring losses). **Continuous behaviour is UNKNOWN and not run.** R3's c1 stays refused. So the demo cannot say the mill could run like this every day without the generator.

**Ruling.** The figure is true under its own rule, and it is not a size of spare solar. Beside the mill it is 0-6 kWh (ARITHMETIC) against 68 kWh used and 96.4 unused. Worse, the board line (READ, `vocabulary.py:276-277`, `outcomes.py:229`; not captured) would read **"0–2 kW of daytime solar unused"** and **"0.00–0.50 USD per hour of use, at the declared price"**, and "unused" is contradicted by the hours above. The served money is per hour; 1.50 USD a day is arithmetic, not a line. R3's reason for (b), that the potential is the opportunity's only size, fails when the size misleads. **(a) sits well beside the mill:** the system saw spare solar, declined to size it, and the trial then measured the result.

**Third options.**
- **Summing the eligible hours** (the stored day `opportunity_kwh`): 29-39 kWh a day, 7.25-9.75 USD (ARITHMETIC). It needs (b) plus a new line and claim, 0.75+ est., and still does not reach 68. **Refused under SCOPE-1; backlog.**
- **(a) plus script: accepted, +0.** It is what I recommend.

**Script, under either option.**
- **Say:** "On these example days the extra came from solar that was going unused: about 96 kWh a day before, about 22 after. The generator didn't run during mill hours, before or after, and the battery still reached full by 2pm. In this example the mill also ran longer, not just earlier."
- **If asked about the limited-evidence line:** "We generated these example days in separate runs, and the system won't size across those. A real site reports continuously."
- **Do not say:** the change saves fuel; the mill could run like this every day on solar; the mill's same work was simply moved.
- **Correct** line 944's "from about 4am": MEASURED, the generator runs in the 05:00 hour only, 15 minutes. Say "shortly before 6am".
- **DD-1b2b adds one report-only row, no product code, +0:** recompute unused solar and mill kWh on S-13..S-11 and S-8, S-6, S-5 from stored rows. The script may quote 96 and 22 only if that row matches. No screen is claimed to show them (the curtailed panel is in the Lab run frame, READ).

### 3. The owner question replaces R3 §2's. Send as written

"One short choice on the Grow row, with both results first.

The mill check passed. On the example days, midday use went from 42 to 110 kWh a day against a 10% target, and the stored result is target met. I haven't yet seen that wording on screen; the full rehearsal will show it.

The extra came from solar that was going unused: about 96 kWh a day before the change, about 22 after. The generator didn't run during mill hours, before or after, and the battery still reached full by 2pm. In this example the mill also ran longer, not just earlier: 4 hours in the afternoon became 8 hours from 8am.

The choice: the system saw spare solar on all 5 example days before the change, but won't size it, because those days were generated in separate runs and it reads that as 'mixed sources'. We can lift that for this one study. We measured what it would then say: 0–2 kW over 3 daylight hours, worth at most 0.50 USD per hour used, or about 1.50 USD a day by our arithmetic. That is correct by its own rule, but it counts only the room left in all 3 hours when the battery isn't charging, and the old mill run filled two of those. So it reads as if almost no solar was spare, right beside a result that used 68 kWh more a day.

**Leave it (recommended; this changes what I'd have recommended before measuring):** no extra work, 4.0 units left on this lane. The Grow row says 'Limited evidence: readings come from mixed sources, so the size is not worked out yet', with no figure or money. The presenter explains that the example days were generated separately.

**Allow it for this one study:** half a unit more, 4.5 left, and it isn't proved until the full rehearsal. The client sees the 0–2 kW figure and its money beside the mill result, and the presenter has to explain the gap every time.

Either way, the presenter won't say the change saves fuel, or that the mill could run like this every day on solar. Each example day restarts the battery at a set level at 6am, which covers about 40 kWh a day, only about 22 kWh of unused solar is left after the change, and we haven't tested consecutive days. This also corrects my earlier 'about 3 usable hours': 3 is what that rule counts, while solar was going unused for 6 hours and the mill ran for 8.

A size that fits better would be new work, and it still wouldn't reach 68 kWh, so it goes on the after-demo list unless you say otherwise."

### 4. "Seen again" (R2 Q7): dead under both

- **(a): dead, MEASURED.** No recurrence. Later studies are UNKNOWN with 0 eligible, none ends on S-8, S-6 or S-5, and Portfolio counts "1 verified result". Q7's "does not recur" column applies. Q7's COH-17 entry is owed only if the check fires, which is now not expected. BL-40 stays in the backlog, not needed for the demo.
- **(b): dead, READ; proved in the rehearsal.** (b) changes only the source-class limit. It adds no study, and those later studies have 0 eligible days regardless of class.
- **Not measured under either:** "Checked and working" and the Assure and Action lines on S-8, S-5, S-1 (the probe sampled only Grow rows). DD-1b2b captures them. R3 §2's "Seen on 5 of 5" is corrected: S-11 measured "Spare solar on 4 of 4 well-observed days · 1 of the last 5 days not checked".

### 5. Does anything stop the review? **No**

- P2-P5 and P7 pass, with no P4 or P5 failure. Under (a), DD-1b2a goes to its own fresh review once the owner answers. Under (b), it goes after the build (R3: L0, L2, `test_ch9*`, MD-0 study tests).
- **P2 is closed from the evidence:** `origin_opportunity_id` is non-null in `samples.before-ticks.action_link` of the probe file; the packet's "not read" was the builder's ad hoc query.
- **Carried, not stopping:** the probe's stray `prebuild` `FAILED` on EV-LAB-001 board URLs on a Kobo-only clone; DD-1b2b's rehearsal must show those URLs 200. Guards and scoped tests still run before the review, as the packet says.
- **Under (a),** R3 §2's rewording of WK-2c, F-THREADS and ST-3 stands and belongs to DD-1b2b.

### 6. Units and backlog

(a): 4.0, DD-1b2a 1.5. (b): 4.5, DD-1b2a 2.0, DD-1b2 3.5. Unchanged from R3. BL-43 and BL-44 are free (grepped); the coordinator records them when the owner answers.
- **(a) chosen:** BL-43 = the narrow study rule with this field list, 0.5. BL-44 = a size for the potential that matches what a change can use, e.g. summing eligible hours; not sized beyond 0.25+ for the line, and it needs BL-43.
- **(b) chosen:** BL-43 = the compatible-run-basis record for all readers (R3). BL-44 as above, 0.25+.
- **Either:** continuous-day battery recovery with the mill schedule is unrun; R3's c1 already records the cost, and it joins BL-44's note rather than a new row.

Handoff: the coordinator sends §3 as written. Stops come back to this Architect.

## DD1b2-R5: review H1 and M1 (Architect, Claude, 2026-11-07)

Input: `.agent/review-DD-1b2a.md` (`3443e7a3b`), the packet and `.agent/DD-1b2a-m3.json` (`7cfe2f7be`), owner "Leave it" (`.agent/owner-grow-size-2026-11-07.md`). I also ran read-only queries on `assetops_demo3_dd1b2r_test`. **The last ruling from this Architect; a fresh one takes what follows.**

### H1. R4 §4 is withdrawn: "Seen again" is open, not dead

- **M3 does not test recurrence. MEASURED by me on `dd1b2r`:** the tick wrote `backup`, `fuel` and `service` selections for the added days 11-02 and 11-04 (29-33 and 24 each), and **0 `renewable` selections**. A study with no renewable heads cannot be queued (`renewable_scan_heads`), so nothing could recur. The earlier days got renewable heads from the prepare's `drain_mini` day pass.
- **Cause: not found.** A candidate (READ, unconfirmed): renewable runs only for "measured daylight hours" known at the cutoff (`mini_depth/worker.py:118-121`, `store.daylight_hours`, `received_at <= cutoff`). The added days were received in real time on 11-07.
- **Q7's two columns are restored.** The reviewer's in-memory table (S-3 study: 2 eligible; S-1 study: 1 eligible) and the READ chain (eligible 1 or more is a Source, so RESOLVED_MONITORING goes to RECURRED) stand as the expectation.
- **Is the gap worth a cheap read now? Yes, +0.25, before DD-1b2b builds.**
  - **Who:** a read-only Sonnet diagnosis on `dd1b2r`, with no code.
  - **Why:** the presenter's live S+2 add uses this path. If renewable is never assessed there, the live day's Grow row has no spare-solar reading and its study never forms.
  - **Then:** a defect found comes back as a ruling with a size. A whole-list prepare need not share the cause.

**What the rehearsal must measure, in order:**
1. Renewable selections for every daylight hour of S-3, S-1 and the live S+2 add.
2. The studies ending S-3 and S-1 (and S+2): queued, status, eligible days.
3. The mill thread's events after the ticks: RECURRED or not, and its effective day.
4. Boards S-5, S-1, S+0, S+1 (Grow and Assure rows) and the thread page.
5. Portfolio week and month counts.
6. COH-17's output for the mill thread.

| Outcome | Script | COH-17 | Portfolio |
|---|---|---|---|
| **Recurs** | Q7's "recurs" column. "Seen again" lines are true and stay: "after the change, sunny afternoons still leave solar unused" (MEASURED in R4: 2-8 kW of room at 14:00-16:00 after the change). No kW figure, since the study is UNKNOWN | Entry owed only if it fires, per `:1559` | Grow counts the mill thread as open. Assure is unchanged, because Assure never counted the mill (M1) |
| **Studies queued with 1 or more eligible days, no RECURRED** | Stop: this contradicts READ `lifecycle.py:55`. Back to the Architect | n/a | n/a |
| **Studies not queued (no renewable heads)** | Stop: the H1 gap reached the build. Back to the Architect with the diagnosis | n/a | n/a |
| **Queued with 0 eligible** | Q7's "does not recur" column; "Seen again" sentences removed | None | Mill thread is not counted as open |

The packet keeps "no recurrence" for the 18-entry list only, as corrected.

### M1. The mill is missing from the boards: owner question, recommend (i) plus the link fix

**MEASURED by the reviewer:** ACT-000002 is on no board. The Assure "1 verified result" at S+0 is ACT-001. The thread page's Action link returns 404. The verdict page (200, VERIFIED 42.00 → 110.00) is reached from Work → Maintenance. Cause (READ): Finding-only reads in `site_outcomes/mini.py:416,475` and `board.py:691-765`. This is pre-existing (CH-9b) and not this diff.

**What the client sees on the script's days, under each option:**

| | (i) Script route through Work, plus the link fixed | (ii) Opportunity-origin Actions wired into boards, Assure and thread |
|---|---|---|
| S-11 | Grow: limit line, thread open (both) | Same |
| S-8 | Grow: "Not available yet · no completed work or checked change for this outcome" | Thread line, "Checked and working" (as-known: the case is complete, the verdict comes later) |
| S-5 | Assure: "No verified result yet". True as known: the verdict was recorded 10-31 23:00Z, after that local day | Same; the verdict is not yet known |
| S+0 | Assure: "1 verified result" (ACT-001 only). The presenter says the mill's check is on its own page | "2 verified results", the mill among them |
| Path | Thread page → working link → verdict page "Target met", 42.00 → 110.00; or Work → Maintenance → the same page | Board → Action → verdict |
| Size | **+0.25** (link only; avoiding it in the script is +0, but fragile) | **1.0-1.5 est.** Shared composer and board code; Portfolio counts move; recaptures and COH re-expectations; Cold and EV boards share `board.py`; full fast tier |

**Recommendation: (i) with the link fixed.**
- **The dead link is demo-critical on its own under SCOPE-1.** The thread page is the one place the mill's "Checked and working" shows, and a 404 from the headline story cannot be presented. The fix is to route the domain-Action `ref` to the existing verdict page, so no new page or claim is needed.
- **(ii) is right for a product but a new shared change at the sprint's end.** It goes to backlog **BL-45** (free), unless the owner says otherwise.

**Owner question, send as written:**

"The mill result is real and passes, but it only shows on its own page, not on the Site's daily board. The board's 'verified results' count at the end of the story counts an earlier maintenance check, not the mill. The link from the mill's story page to it is also broken.

**Fix the link and present it as a route (recommended):** a quarter unit, 4.5 left with the check below. You'd go from the mill's story page, or from Work, to the result page showing 42 to 110 kWh a day and target met. The board would still say '1 verified result', and the presenter would say the mill's check sits on its own page.

**Put the mill on the boards:** about 1 to 1.5 units more, about 5.25 to 5.75 left, touching screens shared with cold rooms and EV, with re-checks to match. The board would show the mill's change and count it as a second verified result.

Separately, a quarter unit now to find out why days added during a demo don't get their spare-solar check, because the live day you add in the demo uses that same path."

### Merge, owed list, units

- **DD-1b2a merges after the packet corrections, with no re-review.** The corrections are paper: R4 §4 is withdrawn here, H1 and M1 point to this section, and the code is unchanged and found sound. The coordinator verifies against this list.
- **Conditions:** the 2 guards that could not run here (missing-claim scan and its fixtures, `MODULE_NOT_FOUND`) run on main right after the merge, and a failure is traced to it. The owner's M1 answer is not needed to merge.
- **Into DD-1b2b's owed list:**
  - The H1 measurements and the outcome table above.
  - The add-path renewable diagnosis (+0.25; before the build).
  - The M1 option chosen; under (i), the link fix and the script route.
  - L1: tick until dirty is 0. L4: EV and COLD 404s, from the log. L5: `Demo.delivered_days`. L6: contributor beside "No potential found yet".
  - R4's script lines and its report-only unused-solar row.
  - R3's WK-2c, F-THREADS and ST-3 rewording.
  - The "Target met" label in a browser.
  - A mill stop means a clone, not a rerun.
- **Units: 4.0 before this stop.**
  - (i) with the link: 4.25. Plus the diagnosis: **4.5**.
  - (ii): 5.25-5.75 including the diagnosis.
  - A defect the diagnosis finds is sized then.
- **Backlog, recorded on the owner's answer:** BL-45 = opportunity-origin Actions on boards, the Assure count and thread lines; 1.0-1.5 est.

## DD1b2-R6: DD-1b2b consolidated owed list (Architect, Claude, 2026-11-07)

Binding checked: Claude (`.ai/ROLE_CONFIG.md`, 2026-10-27). Inputs: `DD-1b2-preflight.md` (28 items), DD1b1-R "Owed", DD1b1-R3 §6, DD1b1-R4, DD1b2-R to R5, `review-DD-1b2a.md`, the packet's fix round and verification, `DD-1b2-addday-renewable-diagnosis.md`, and the three owner answers (whole-list run; "Leave it"; "Fix link, use route"). **This section is the DD-1b2b builder's single card.** It replaces the scattered "owed" lists; earlier rulings are cited only for reasons. I ran nothing. **READ** = code; **MEASURED** = the stored evidence named. Branch `task/DD-1b2-finish-rehearsal` at main `29efab1d0`.

### 1. Two corrections from my reads (READ; the builder confirms them in step 1)

- **No screen renders the mill thread's Action link.** The frontend reads only `/chain/why` (`sites/chainClient.ts:72,81`), and a THREAD ref has no screen (`routeFor` returns null). Nothing renders `actions[].ref` from `/api/sites/{s}/chain` or `/threads/{id}` (`chain/site_chain.py:143`). The why trace uses only the id and code (`chain/why.py:241-246`). So the 404 is a wrong `ref` on the API wire, not a dead link on a screen. **The fix still goes in:** the owner chose it, the wire is the contract the next screen will render, and F-THREADS checks it. **The script route is Work → Maintenance → the mill row → verdict page**, not "from the story page". The owner is informed (§5); no decision is needed.
- **S-3's study is probably not queued on a daytime rehearsal.** The scan's lower bound is wall now − 5 d (`worker.py:156`), and S = today − 2. S-3's PV hours (05:00-10:00Z on today − 5) fall before that bound once the ticks run after about 10:00Z. **The S-1 study decides recurrence.** S-3 is reported and is never a stop.

### 2. The owed list (one row per item; "#" is the pre-flight checklist number)

| ID | Item | Source | Class | Pass condition |
|---|---|---|---|---|
| O1 | **Link fix.** `chain/refs.py`: add kind `DOMAIN_VERDICT {site, id}` to `KINDS`, plus `domain_verdict_ref(site, id)`; `href_for` → `/sites/{site}/domain-actions/{id}/verification`, no query. `chain/site_chain.py:143`: use `domain_verdict_ref` when `a["kind"] == "DOMAIN_INTENT" and a.get("origin_opportunity_id") is not None`, otherwise `action_ref` as today. Frontend: add the kind to the `sites/chainRef.ts` Ref union; in `shell/operatorSiteRoutes.ts` `routeFor`, add a case → `siteMillVerificationHref(r.site, r.id)`; add one row to `shell/__fixtures__/route-refs.json` | R5 M1; owner "Fix link" | BUILD | L0: `test_ch5a2_refs.py` (the fixture covers the kind), `routeRefs.test.ts` (the kind list at `:15` gains it), and new `backend/tests/test_dd1b2b_action_ref.py`: MINI_TRIAL + finding → ACTION; DOMAIN_INTENT + finding (Cold/EV) → ACTION, byte-equal to today; DOMAIN_INTENT + opportunity → DOMAIN_VERDICT. Rehearsal: the mill ref's href serves 200 in the browser and reads "Target met"; Cold and EV thread refs stay ACTION (F-THREADS lists them) |
| O1b | O1's blast radius (READ) | O1 | REPORT-ONLY | Cold/EV domain Actions carry `origin_finding_id`, so their refs do not change. ACT-001 does not change. No screen changes. Only Kobo's `/chain` and `/threads` bodies change, so the rehearsal builds **after** the commit |
| O2 | **R8 drain** `Demo.drain()`. Tick once, then N = ceil((dirty + pending `snapshots`)/200) + 2. Done when dirty is 0, pending is 0 (subscribed types) **and Kobo mini `deferred` is 0** (`stages.py:151-156`). Between N and 2N with counts still falling: continue and log `over_n`. Past 2N, or two flat ticks: fail with the counts. It reads the tick's stdout and return code itself. It runs at step 6 (after `b,c,d`) and again after the finish ticks. New CLI `tick --until-drained` calls it | DD1b2-R Q4, Q8; review L1; diagnosis §1 | BUILD | L0: the formula and the stop logic. L2 on a seeded backlog: stops at 0, reports `over_n`, fails on a flat count. Rehearsal: F-DRAIN 0/0/0 after the second drain. The same stuck ids on two ticks: **stop** |
| O3 | `prepare --cap-seconds` (10800 for the rehearsal). An elapsed field on each child line and in `manifest.json`. Separate timings for mini-depth, backfill, mill, drain, finish rows, F-PERF and EX-1 | DD1b2-R Q1, Q14; # 23 | BUILD | The manifest holds every timing. The wall time is measured, not projected |
| O4 | F-DRAIN; F-COH (threads generated from `kobo/cold/ev.json` into the manifest's `expected_threads`, then `check` with no `--expect`); F-PERF (`perf_budget.py --story`, `--report`, 3 runs); F-CAL (Q11, every local day); F-COH3, non-vacuous | DD1b2-R Q9, Q11; # 2, 17 | BUILD | Any COH finding is a fault, with one exception: COH-17 on the mill thread on week and month windows, **if and only if** the thread recurs (entry text at `:1559`). An F-PERF breach is a packet line only |
| O5 | F-THREADS per Q10, plus: MILL-3 (outcome count 1, VERIFIED, recomputed 42.00 → 110.00, `origin_opportunity_id`, CHANGE_APPLIED, not SHORT); earnings, ONE-SOURCE and the "Why?" price line, recomputed; the MG-1 verdict and the days it reads; the MG-2 line; every `story_links` board and every bare board on the 3 Sites (fail on PRODUCER_NOT_SETTLED or PARTIAL); the links that carry an explicit `known_at`, listed; `domain_action_index` not a failed read on Cold/EV day and week boards; the Portfolio's plain landing for Cold/EV, stated; Cold/EV "No action agreed yet", reported; the Protect "Why?" naming both Cold threads; ACT-002/003 "Action agreed" | DD1b2-R Q10; # 4-7, 12-16, 18, 20-22 | BUILD | Each row passes or is listed as a fault. **No row is edited to pass.** A change to what a row asserts comes back here. A tool bug is fixed in place and declared |
| O6 | **WK-2b, restated** (DD1b2-R Q10). On S: no headline money; the headline does **not** match the kW pattern; the sales contributor starts "0 kWh used by Grain mill"; the potential reads "No potential found yet". **WK-2c** on S-11 (R3's wording under "Leave it"): the potential line equals "Limited evidence: readings come from mixed sources, so the size is not worked out yet", with no kW, no `value_line` and no money; status LIMITED, reported. F-THREADS' SUPPORTED row becomes: the pinned study is LIMITED with 5 eligible days, reported | DD1b2-R Q10; R3 §2-3; R4 §5 | BUILD | WK-2c **fails** if any kW figure or money shows for the potential |
| O7 | Reword ST-3 in `docs/demo-sprint/client-demo-plan.html:588`: "…the headroom opportunity is a thread; on the example data its potential reads as limited evidence with no size or money (owner, 'Leave it'; BL-43/44). The mill change is verified before/after on its own result page, reached from Work (BL-45)." | R3 §2; R5 M1 | SCRIPT-LINE (doc) | Text as given |
| O8 | **H1 measurements**, on `dd1b2` after the build and before EX-1: (1) renewable selections for every PV hour of S-3 and S-1; (2) the studies ending S-3 and S-1: queued or not, status, eligible days; (3) the mill thread's events after the drain; (4) Grow and Assure rows on boards S-5, S-1, S+0, S+1; (5) Portfolio week and month counts; (6) COH-17 on the mill thread. The same six on the clone after the S+2 add, for S+2 | R5 H1 | MEASURE | R5's outcome table (end of §3) |
| O9 | **EX-1**, `tools/demo_combined_ex1.py`, on the clone: read the boards; run `add-day --site KOBO-001 --kind normal --assess-now` (S+2) and time it; run `tick --until-drained` and count the ticks; read again. Compare the Assure count, the trial line, the Action's words and any new Findings | DD1a2-R3; DD1b2-R Q13; # 10, 19, 28; §3 | BUILD + MEASURE | The Assure count, trial line and Action words are unchanged; no new Finding; renewable selections for S+2's PV hours exist **before** the first tick; the add and tick seconds are recorded for DS-1. `DAY_NOT_IN_PAST` is not a fault: rerun after 11:00Z on the same clone |
| O10 | **L5**, `Demo.delivered_days`: measured on the real build in place of R2's seeded L2 (this amends R2 §2's test) | review L5 | MEASURE | On `dd1b2`, S-10 and S-4 are absent from the set and every built day is present; EX-1's add is not refused on it |
| O11 | **L4**, the prebuild 404s | review L4; R4 §5 | MEASURE | The rehearsal's `prebuild` logs show 0 non-200 responses for COLD-LAB-001 and EV-LAB-001. Any 404: **stop**, with the URLs |
| O12 | **L6**, capture the Grow contributor beside "No potential found yet" on S-8 and S-5 | review L6 | MEASURE + SCRIPT-LINE | Captured; the line is in §4 |
| O13 | **"Target met" in a browser.** Serve `dd1b2`, open Work → Maintenance → the mill row's link, and open O1's href directly | R5 M1; review "unproved" | MEASURE | Both paths show the headline "Target met" and 42.00 → 110.00; screenshots in the packet |
| O14 | R4's unused-solar row: recompute solar available, delivered and unused, and mill kWh, on S-13..S-11 and S-8, S-6, S-5 from stored rows | R4 §2 | REPORT-ONLY | The script may quote "about 96 / about 22" only if unused reads 96.4 and 22.4 (±0.5). Otherwise DS-1 drops those numbers. No screen claims them |
| O15 | **Litre recompute** (MONEY-B/G1) on the `steady-before` nights after R2's seam fix | R2 §2; R3 §6; # 8 | MEASURE | Old and new reported. The owner line (§5) goes **only if** it differs from the accepted figure at one decimal |
| O16 | MONEY-B: each fuel row traces to a story-day Finding and none sits on a steady day; S-14 and S-7 PRICED with quantity 0; a Cost headline on one `steady-before` and one `steady` day; WK-2a 42.08 | DD1a2-R2, R3; # 8 | BUILD (finish row) | As written. A different figure goes to the owner before E3 |
| O17 | Time and memory: a scratchpad sampler every 30 s (free RAM, python working sets, `docker stats`); R11 from the `assetops.perf` line, otherwise "not measured" | DD1b2-R Q14; # 23-25 | MEASURE | Wall ≤ 10800 s and free RAM ≥ 2 GB throughout. Over 3 h: the **B-16 projection goes to the owner** before E3. Under 2 GB: **stop** |
| O18 | `EXPECTED_SECONDS` gains `mill` and `drain` from the measured figures, untuned | DD1b2-R Q14 | BUILD (after the run) | Equal to the manifest's values, rounded up to 10 s |
| O19 | Q12: how E2 runs `test_demo_combined_postgres` (on the E3 build's clone, with the DB named by env) | DD1b2-R Q12; # 9 | REPORT-ONLY | Stated in the packet; no branch written |
| O20 | Not owed: item 3 (M2 and F-FILL are backlogged), item 27 (not pinned), the EV "twice" item (dropped), a seeded `delivered_days` L2 (replaced by O10) | rulings named | n/a | Each listed in the packet as not done, with its reason |

### 3. Rulings on the add-day diagnosis

- **Option A is ruled.** The live S+2 add uses `--assess-now`. Kind `normal` is allowed (`demo_combined.py:581` refuses only `late`). The run is set to `assess: build`, and `drain_mini()` drains Kobo's mini jobs with no bound (`:598-613`, READ). So the renewable heads exist before any tick. A tick is still needed to queue the study and place threads, so **the presenter runs `tick --until-drained`** (O2) and then shows the board. O9 measures this.
- **B is not number tuning in the barred sense:** it changes when the work happens, not any measured or shown value. **It is refused under SCOPE-1.** It changes a lease-budget constant pinned by `test_w402_mini_stage.py:97`, it lengthens every Site's tick, and A reaches the same state at +0. With B, two adds in a row (68 jobs) would still not finish in one tick.
- **C is refused.** It reorders the lease without draining it, and it changes shared lease SQL.
- **Backlog BL-46** (free; I grepped `.agent` and `docs`): "One serve tick finishes an added day's mini jobs, by a larger bound or renewable-first leasing, so a live add needs no `--assess-now`." Source: the diagnosis §4 and this section. Nothing shown is false without it. 0.1-0.2 est.
- **The standing DS-1 line is replaced.** Old (`coordinator-handoff.md:24`): "Tick right after the add, before showing the board, or it reads REASSESSMENT_PENDING". New: **"Add the live day with `add-day --site KOBO-001 --kind normal --assess-now`, after 11:00Z. Then run `tick --until-drained`, and show the board only when it returns. Until then the board can read REASSESSMENT_PENDING, and the day has no spare-solar check yet. It takes about [O9's add + tick seconds]."**

**R5's outcome table, restated with §1's S-3 note (applies to O8):**

| S-1 study after the drain | Result | Then |
|---|---|---|
| Queued, eligible ≥ 1, thread RECURRED, effective day after S-9 | **Recurs** | Q7's "recurs" column; the COH-17 entry only if it fires; Portfolio Grow counts the mill thread as open; Assure unchanged |
| Queued, eligible 0 | Does not recur | Q7's "does not recur" column; the "Seen again" lines leave DS-1 |
| Queued, eligible ≥ 1, no RECURRED | **Stop** | Contradicts `lifecycle.py:55` |
| Not queued (no renewable heads for S-1) | **Stop** | The add-path gap reached the build: the diagnosis plus counts |
| RECURRED effective on or before S-9, or WITHDRAWN, or CLOSED | **Stop** | Q7's stop |

### 4. Script lines owed to DS-1 (the coordinator carries them; +0)

- **Mill route:** Work → Maintenance → the mill row → "Target met", midday use 42 → 110 kWh a day. "The board's '1 verified result' is the earlier maintenance check. The mill's check sits on its own page." (R5 M1)
- **R4. Say:** "On these example days the extra came from solar that was going unused: about 96 kWh a day before, about 22 after [only if O14 matches]. The generator didn't run during mill hours, before or after, and the battery still reached full by 2pm. In this example the mill also ran longer, not just earlier." **If asked about limited evidence:** "We generated these example days in separate runs, and the system won't size across those. A real site reports continuously." **Do not say** that the change saves fuel, that the mill could run like this every day on solar, or that the same work was simply moved.
- **Q7:** the "recurs" or the "does not recur" sentence, per O8's outcome.
- **L6:** "Spare solar was seen on the well-observed days. The opportunity's size isn't repeated while the change is being checked."
- **Generator, correcting `:944`:** "On the days before the mill change, the evening ends with the battery a little lower, so the generator comes on shortly before 6am for about 15 minutes, using [O15's litre]. It was needed, so no problem is raised and no extra cost is estimated."
- **Add-day:** §3's replacement line. "Do not add a Cold or EV day live" stands (DD1b1-R4 §2).

### 5. Owner

- **Now (for information, no decision):** "One correction on the mill link: it was wrong in the data behind the screens, but no screen shows that link yet, so nothing a client could click was broken. We're fixing it anyway, as you chose. The demo reaches the mill result from Work, which shows 'Target met' and 42 to 110 kWh a day. The size doesn't change."
- **After the rehearsal, only if triggered:** B-16, if the wall time is over 3 h (O17). The litre line, if O15 differs at one decimal: "The generator's early-morning run on the days before the mill change now reads [X] L, not [old]; nothing else changes." The recurrence result (O8), stated as measured: "Seen again" either shows or it doesn't.

### 6. Order

| Step | What | DB / folder | Relative to the build |
|---|---|---|---|
| 0 | Pre-flight: read this section and the code named in O1-O9. Batch every question, then stop | none | before |
| 1 | Confirm §1 in code (no screen renders `actions[].ref`; the scan bound). Drop the spent DBs and folders: whichever of `assetops_demo3_dd1b2{m,n,p,q,r}_test` exist in `pg_database`, and `var/demo3_dd1b2{m,n,p,q,r}`. Their evidence is committed. Run `npm ci` in `frontend` (the guards need it) | drops only | before |
| 2 | O1 with its L0s. Commit | none | before |
| 3 | O2, O3 and `tick --until-drained`, with the L0 and the L2 (own `*_test` base, dropped after). Commit | L2 base only | before |
| 4 | O4-O6, O9 and O14-O16 rows and tools, with their L0s. The O7 text. Commit. **Prepare archives git HEAD, so everything is committed before step 6** | none | before |
| 5 | Guards A, W, N, V, M, and the missing-claim scan with its fixtures. Scoped pytest: `tools/checks/test_chain_coherence.py`, `test_ch9b*`, the `test_demo_combined_*` L0s, `test_ch5a2_refs.py`, `test_dd1b2b_action_ref.py`, O2's tests. `tsc --noEmit`. Vitest: `routeRefs.test.ts`, `millVerification.test.tsx`. **No full suite** | none | before |
| 6 | **The rehearsal, once:** `demo_combined.py prepare` on the whole v3 list, no `--days`, no `--sites`, `--cap-seconds 10800`. Machine idle, keep-awake on, sampler and stall monitor on, one heavy job | `assetops_demo3_dd1b2_test`, `var/demo3_dd1b2` | the build |
| 7 | On `dd1b2`, mostly reads: O8, O10, O11, O13, O14, O15, O17. For a finish-row fault, fix the row's tool and rerun `demo_combined_finish.py check` on the same DB. **Never rebuild for a row** | `dd1b2` | after |
| 8 | Clone (`CREATE DATABASE … TEMPLATE` with no open sessions; copy the folder). Then EX-1 (O9), and O8's six for S+2 | `assetops_demo3_dd1b2c_test`, `var/demo3_dd1b2c` | after |
| 9 | Commit O18; write the packet; fresh Claude review. Keep both DBs until the review verdict, then drop them | both | after |

**The mill step is never rerun on a DB where it has already run** (`STUDY_NOT_ONE`, review residual). If the mill step fails inside the prepare, recovery is a new build, which would be a second whole-list run: **ask the owner first**. No pre-mill clone is added, because it would be new, unrun code inside the one run.

**Barred throughout:** the full backend suite; any demo prepare or baseline build other than step 6; `test_demo_combined_postgres`; any DB other than `*_test` and `<prefix>_audit*`; `assetops_demo3_full_test`; the polish DBs; tuning any number.

### 7. Stop conditions (back to this Architect, with the evidence)

- Any stop in §3's table. MILL-3 differs from 42.00 → 110.00, or the outcome count is not 1.
- A crash anywhere in the prepare (for the mill step, see §6).
- R8 past 2N, two flat ticks, or the same stuck event ids.
- The cap is reached (stop, with per-step timings and the Q14 projection), or free RAM falls under 2 GB.
- A COH finding other than the named COH-17 entry; a prebuild non-200 (O11); O1's href not 200, or a changed Cold/EV ref.
- A finish row whose fix would change what it asserts.

### 8. Review packet (DD-1b2b)

- Each O-row marked MEASURED or READ, with its evidence path.
- The manifest timings, the wall time against 10800 s, and the minimum free RAM.
- F-DRAIN's counts for each drain.
- The S-1 and S-3 studies and the mill thread's events.
- The board and Portfolio captures (O8, O12).
- EX-1's before and after reads, its add and tick seconds, and its tick count.
- O13's screenshots; O14's and O15's numbers.
- Every link, listed with its `known_at`.
- Every failed or fixed row, with its cause.
- O20's not-done list.
- The DS-1 lines in §4, with the measured numbers filled in.
- The scoped test and guard results.

Evidence file: `.agent/DD-1b2b-rehearsal.json`.

### 9. Size

DD-1b2b is 1.5 + 0.25 (O1) + 0.25 (the diagnosis, already spent) = **2.0, of which 1.75 remains.** Option A, O2's extra condition, `tick --until-drained` and O10 add nothing (+0). **Lane 2 remaining: 1.75 + CH-5d1's 1.0 = 2.75.** BL-46 is new in the backlog and not counted. One fresh builder fits 1.75; it may hand over at step 5's commit, with a handoff that names this section.

## DD1b2-R7: rulings on the DD-1b2b pre-flight (Architect, Claude, 2026-11-07)

Input: `.agent/DD-1b2b-preflight.md` (`5c05dd0a3`), plus the coordinator's facts for Q7 and Q8: free RAM 3.3 GB MEASURED at 09:41Z with nothing heavy running, and `check-all` 17/17 on `29efab1d0`. Both R6 §1 corrections are confirmed. The builder's sharpening of the S-3 point stands. I ran nothing. **Every recommendation is accepted except where this table changes it.** The amendments in the second half of this section edit R6's O-rows in place: read R6 with them applied.

| Q | Ruling |
|---|---|
| **Q1** | **Accepted.** O2's done condition adds two counts from the DB: live opportunity jobs (PENDING or LEASED) = 0, and `threads` pending = 0. Both use the same N/2N logic and are logged per Site. O8 reads only after a drain that met every condition |
| **Q2** | **Accepted.** O8(2) measures every queued study (ending S-3, S-1, S+0, S+1, and S+2 on the clone). **"Recurs" means any study places RECURRED with its effective day after S-9;** the packet names the source study. §3's table is replaced below |
| **Q3** | **Accepted.** Each R8 iteration runs the raw `TICK --no-prebuild` and parses its JSON. After each drain completes, performance runs once and `prebuild` runs once. `finish` keeps objectives, S2, `drain_mini`, `tick(2)`, R8 drain 2, then the self-check; F-DRAIN reads after drain 2. `tick --until-drained` takes the same path |
| **Q4** | **Per Site: N = the maximum over Sites of the per-Site formula.** This follows the tick's per-Site bound and is not tuning |
| **Q5** | **Accepted.** `--cap-seconds` bounds `prepare` only. **B-16 is triggered by the prepare's wall time alone, if it is over 10800 s.** F-PERF (step 7) and EX-1 are timed and reported beside it, with no cap |
| Q6 | Noted (information). If the cap is hit, §7 applies |
| **Q7** | **Start condition:** no other `check-all`, pytest, prepare or build running (process list, PIDs in the packet), and free RAM ≥ **2.5 GB** for 2 minutes. The coordinator holds other heavy jobs off for the run. **During the run:** free RAM under 2 GB is **recorded, not a stop**: the minimum, the duration and the step go in the packet, and the owner is told with the result, since E3 runs the same build. **Stop** (end the prepare and keep the DB) only if free RAM is under **1 GB** on two consecutive samples, or the stall monitor sees no child or tick output for 15 min. A stop counts as the one run: any second run needs the owner. This amends R6 O17 and §7 |
| **Q8** | **Crossing Kobo's local midnight (21:00Z) is not a fault and needs no waiver** (READ): S is fixed in `story.json` when the prepare starts, and every read is relative to S. Only "today" moves, so F-CAL's day set, computed at check time, gains S+3 as NO_DATA, which its rule already expects. Every reading on `story.json`'s S is valid. **Preferred start: by 17:30Z.** If steps 1-5 overrun, start the next morning at or after 05:00Z: S moves a day, which is harmless, and EX-1 runs after 11:00Z that day. If the run does cross midnight, the packet says so and names the steps after 21:00Z |
| **Q9** | **L2s included.** `test_ch9b*` means all of them, `*_postgres.py` included, through `tools\run-host-tests.ps1` on base `assetops_dd1b2b_test`, dropped after. They run only when no other heavy job is running |
| **Q10** | **The mapping is correct.** Add `tools/checks/test_perf_budget.py` |
| Q11 | **Accepted:** a scratchpad CDP script, serving on ports 8991/5491. If Chrome is unavailable, O13 is recorded as not run, and the Work → Maintenance → verdict API reads (200, VERIFIED, 42.00 → 110.00) stand in |
| Q12 | **Accepted** as proposed |
| Q13 | No objection (information) |
| Q14 | **Confirmed**, as R6 §6 states it |

**Amendments to R6:**
- **O2:** add Q1's two counts, plus Q3's tick path and Q4's N.
- **O8(2):** every queued study (Q2).
- **O17 and §7:** Q7's start condition, the recording rule below 2 GB, and the stop below 1 GB. "Wall ≤ 10800 s" refers to the prepare (Q5).
- **Step 6:** Q8's start window.

**R6 §3's outcome table is replaced by:**

| After drain 2 (all of Q1's counts at 0) | Result | Then |
|---|---|---|
| Any queued study placed RECURRED, effective after S-9 (source study named) | **Recurs** | Q7's "recurs" column. The COH-17 entry is owed only if it fires. Portfolio Grow counts the mill thread as open; Assure is unchanged |
| No study with eligible ≥ 1, and no RECURRED | Does not recur | Q7's "does not recur" column; the "Seen again" lines leave DS-1 |
| A study with eligible ≥ 1 and no RECURRED on the thread | **Stop** | Contradicts `lifecycle.py:55` |
| S-1's study not queued (S-1 has no renewable heads) | **Stop** | The add-path gap reached the build |
| RECURRED effective on or before S-9, or WITHDRAWN, or CLOSED | **Stop** | Q7's stop |

S-3's study, queued or not, is reported only (R6 §1).

**Owner:** nothing new now. After the run, the R6 §5 triggers apply, plus Q7's line if free RAM went under 2 GB: "During the full rehearsal the machine's free memory went down to [X] GB during [step]. The build finished. The final build on the demo machine needs [Y] free to be safe." **Size unchanged:** DD-1b2b has 1.75 left; lane 2 has 2.75.

## DD1b2-R8: gaps before the one rehearsal (Architect, Claude, 2026-11-07)

Binding checked: Claude (`.ai/ROLE_CONFIG.md:9`). Inputs: R6, R7, `.agent/DD-1b2b-handoff.md` (`9faf45ce4`), `tools/demo_combined{,_finish,_rows,_drain,_ex1}.py`, commits `d2f53caa0` and `d837b539c`. **READ** = code, cited. **MEASURED** = a read-only query or a stored log, named. I ran no build and wrote no code.

### A. The unbuilt items: before or after the rehearsal

Rule used: an item goes **before** only if it needs something only the build moment produces, or it runs inside the prepare. Nothing below does. Every item reads stored rows or served bodies on the kept `dd1b2` DB, and no tick runs on `dd1b2` after the prepare. So **all of them go after**, in one new step-7 tool, `tools/demo_combined_after.py` (reads only; report rows, plus the assertions named). **None of them is added to `CHECKS`.** The prepare archives HEAD at its start (`demo_combined.py:390-396`), so this tool may be written while the rehearsal runs. Its L0 runs after the prepare ends.

| Item | When | SCOPE-1 | Pass, or what happens if it is not built |
|---|---|---|---|
| O14, unused-solar recompute | After (step 7) | Kept, timeboxed to 0.1 | As R6 O14. **If not built, "about 96 / about 22" leaves DS-1** (R6 §4's own fallback). The line keeps "solar that was going unused", without numbers |
| O15, litre recompute | After (step 7) | Kept | As R6 O15. If not built, DS-1's generator line says "for about 15 minutes" with no litre figure, and no owner line goes |
| O16, fuel-row trace and S-14/S-7 PRICED quantity 0 | After (step 7), stored rows | Kept (money is shown to clients) | As R6 O16. MONEY-B in the self-check stays as built. A different figure goes to the owner before E3 |
| F-THREADS: earnings, ONE-SOURCE, "Why?" price line recompute | After, served reads | Kept (figures on screen) | Recomputed and asserted equal to the shown figures |
| F-THREADS: MG-2 line | After | Report only | Recorded as shown |
| F-THREADS: links with an explicit `known_at` | After (from `links`) | Report only | Listed in the packet |
| F-THREADS: Portfolio plain landing for Cold/EV | After | Report only | Stated |
| F-THREADS: Protect "Why?" names both Cold threads | After | Kept | Asserted |
| F-THREADS: "Action agreed" / "No action agreed yet" | After | Kept | Asserted on ACT-002/003, from the `state_label`s that `check.json` already records |
| EX-1: S+2 renewable selections exist before the first tick | After, before step 8 | Kept | Built into `demo_combined_ex1.py` between the add and the first tick (stored-row count for S+2's PV hours). **EX-1 can be repeated:** the clone is remade from `dd1b2` by `TEMPLATE`. Must exist before step 8 runs |

Nothing is dropped. Two items are simplified by fallback (O14, O15) only if not built.

### B. The four ambiguities

| # | Fact (cited) | Ruling |
|---|---|---|
| 1 | A board row's `state` is one of eight states (`outcomes/status.py:18-20, 34`; `site_outcomes/board.py:790`). **PARTIAL is never a row state**, so `r.get("state") == "PARTIAL"` (`tools/demo_combined_rows.py:140`) can never fire: the check is empty, not too strict. The board-level PARTIAL is `read_state`, set when a producer port fails (`site_outcomes/read.py:472`; `mini.py:5-7, 545-547`; `cold.py:210`; `ev.py:282`). "Partly checked" on S is the day grade (`chain/grading.py:24`), a different field | **Change the check to the field R6 O5 meant: the board's `read_state != "AVAILABLE"` is a fault**, listing `failed` if the wire carries it. Keep the `PRODUCER_NOT_SETTLED` scan (`status.py:72`). A must-fail L0 with a `read_state: PARTIAL` board. This sharpens what the row asserts; this ruling authorizes it. S reading `read_state: PARTIAL` is a real fault (a failed producer read), not a property of a partly checked day |
| 2 | Grade string: `NO_DATA = "NO_DATA"` (`chain/grading.py:26`). `days[].grade` is `day_grade` (`chain/site_chain.py:39`). A measure with no stored row reads NO_DATA (`chain/read.py:53-60`), and the weakest grade wins (`read.py:85-88`). Exception: a stored PENDING row wins over NO_DATA (`read.py:85`) | **The string is right. The built rule (`has_run` and kind ≠ `missing`) is right** (S-4 and S-2 are absent from `days.json`, so they are NO_DATA). One change: **assert NO_DATA only on local days before the Site-local today; record today without asserting it**, because today's open day can legitimately hold a PENDING row |
| 3 | `ev.json` records no Finding ids, so EV's expectation is derived from the Portfolio rows it then checks. COH-10 is circular for EV. Separately, `build_expected_threads` skips any Kobo/Cold id that is on no Portfolio row (`demo_combined_rows.py:46-48`), which hides what COH-10 exists to catch | **Accepted for the rehearsal as a declared limit, with two additions:** (a) F-COH fails if the EV group is empty (the fault Tuesday must yield at least one thread); (b) the skipped Kobo/Cold ids are returned as `unplaced` in the row's output and listed in the packet. A non-empty `unplaced` is not a row failure: the reviewer and I rule each listed id. BL item, not now: record EV Finding ids in `ev.json` |
| 4 | **Both columns exist, MEASURED and READ.** `domain_action.origin_opportunity_id`: `backend/migrations/versions/0051_action_opportunity_origin.py:70`. `verification_outcome.domain_action_id`: `0052_verification_plan_domain.py:121-122`. The DROPs in both files are downgrade SQL only (`0051:124-129`, `0052:149-173`; upgrade at `0051:138`, `0052:183`). 0052 is head. Read-only `information_schema` on `assetops_test` (alembic `0052_verification_plan_domain`) returns both columns. The mill outcome is written through `DOMAIN_OUTCOME_COLUMNS`, which uses `domain_action_id` (`actions/adapters/postgres_action_store.py:79-81, 802`). The page route exists (`action_api.py:315`) | **MILL-3 stands as written.** No change |

### C. Risk control for the one-shot run

**Can a wrong row or a drain error lose the run? (READ)**

- **A finish row: no data is lost, but the timings are.** `run()` catches each row, runs all of them, and writes `check.json` before it returns 1 (`demo_combined_finish.py:831-845`). The prepare raises only after that (`demo_combined.py:539-540`). Nothing drops the DB on failure: drops happen only at a prepare's start (`:413-414`) and in `drop` (`:776-778`). **But `manifest.json` is written only after `finish_build` returns (`:448-456`),** so a self-check failure loses O3's timings and the wall time.
- **The drain: yes, it can cost the run.** `drain-1` runs right after the mill (`:501-505`). `Demo.drain` raises on (a) any non-zero tick (`:596-598`), (b) a `counts` child crash (`check=True`, `:578`) or no JSON line (`IndexError`, `:580`), and (c) a fail verdict (`:606-607`). A real tick exits 1 when any Site is FAILED (`scheduling/run.py:94`). **MEASURED:** `AssetOpsV1-demo3/var/demo3_full/logs/59-tick.log` shows KOBO-001 FAILED with `["MINI", "TIMEOUT", "stage mini exceeded 120 s and was killed"]`. That is a load timeout, which a 2-3 h run can hit. An abort at drain-1 leaves a DB where the mill has run and objectives, S2, ticks, drain-2 and the self-check have not. The mill never reruns (R6 §6), so recovery would be a second build, which needs the owner.
- Note: the drain does not parse tick stdout at all. Its only real-path parse is the `counts` JSON line. The `counts` SQL ran against Postgres in L2 (`test_dd1b2b_drain.py:113-139`). What has never run is the subprocess path and a real tick's return code.

**Rulings (BUILD before the rehearsal, with L0s; commit; then P0):**

- **C1. The drain never ends the prepare.** Inside `prepare`, a drain failure of any kind ((a)-(c) above) writes `drain-N.json` with `verdict: "fail"`, the reason, the history and the log. Then the prepare continues: objectives, S2, ticks, drain-2, self-check. After the self-check, the prepare exits non-zero with `DRAIN FAILED (deferred)`, and F-DRAIN fails on the record. **A non-zero tick is recorded, not fatal:** the log entry carries each Site's `failure` triple, parsed from the tick JSON or the last line if it does not parse, and the 2N and flat-tick rules still decide. This amends DD1b2-R Q8's "Exit 1 on a FAILED Site stops the prepare" (`:1592`). The CLI `tick --until-drained` keeps exit 1 on a fail verdict, so the presenter and EX-1 still see it. **After the run:** any FAILED tick is listed in the packet. A failure other than a stage TIMEOUT is an R6 §7 stop back to me, with the DB kept.
- **C2. The manifest is always written.** The manifest write moves into a `finally` that records `failed_at` (step name) and the error, with the timings gathered so far.
- **C3. A self-check failure is a step-7 fix, not a lost run.** R6 §6 step 7 stands: fix the row's tool, then rerun `python tools/demo_combined_finish.py check <url> var/demo3_dd1b2`. If the wall cap fires inside the self-check, the data is complete, and `check` reruns the same way.
- **Unchanged:** a failure in the mill step, or a crash before it, is a stop, and a rerun needs the owner.

**C4. Pre-run proof P0 (one partial build, own DB, dropped after).**

The DD-1b2a probe list is not used: it is 18 of v3's 22 Kobo days, so it is close to a whole build. P0 copies the M0 precedent instead (DD1b2-R2 §1: a 4-day partial prepare, about 7 min).

- **Days:** `.agent/DD-1b2b-p0-days.json`, v3 entries unchanged. Kobo S-13 `steady-before-first`, S-12 `steady-before`, S+0 `trial-before`, S+1 `trial-after` (M0's set). Cold S+0 `failure`. EV S+0 `fault`. If a join guard refuses, add only the ruled day it names, and say so.
- **Runs, in order, after C1, C2 and the B fixes are committed:**
  1. `prepare --sites kobo,cold,ev --no-finish --days .agent/DD-1b2b-p0-days.json --cap-seconds 2400`, on DB `assetops_demo3_dd1b2t_test` and work `var/demo3_dd1b2t`. With `--no-finish`, no mill step runs (`:466-467`).
  2. `tick --until-drained`. This is the real `Demo.drain`: real tick children, real `counts` children, and the record.
  3. `python tools/demo_combined_finish.py check <url> var/demo3_dd1b2t`. Every row runs on real served bodies. Each failure is classed as **absent data** (it names `mill.json`, a drain record, a day, a thread or an objective that P0 does not build) or as a **tool fault** (a KeyError on a wire shape, a 404 route, SQL, the F-COH `InProcess` collect, F-CAL's `chain?date=` shape). DD1b1-R4's rule applies (`:1439`): only absent data is excused, and each excused row is listed.
  4. After 11:00Z: `tools/demo_combined_ex1.py` straight on the P0 DB (it is disposable, so no clone).
  5. Fix each tool fault in place, with its L0, and commit. Rerun only step 3 (and step 4 if EX-1 changed). Never rerun the prepare. Then drop the DB and the folder. Evidence goes to `.agent/DD-1b2b-p0.json`, committed.
- **Time:** an estimated 30-45 min (prepare 12-20, drain 3-5, check 5-10, EX-1 5-10). Cap 60 min for steps 1-4. Same start conditions as R7 Q7. One heavy job at a time.
- **Permission:** the owner's standing rule bars a full data build. The owner's exception covers the one whole-list rehearsal. P0 is a 6-day partial build, the same class as M0 and the DD-1b2a probe. **This amends R6 §6's bar ("any demo prepare other than step 6") for P0 alone.** The owner is informed and is not asked.
- **P0 does not prove** the mill's place in the drain order, the full-list values or the timings. C1 and C2 cover those risks.
- **Freeze:** after P0's last fix commits, nothing the prepare archives changes until step 6 starts.
- **Timeline:** fixes about 60 min, P0 about 45, P0 fixes about 30. That puts the rehearsal start at about 12:30-13:30Z, inside R7 Q8's window. If a P0 fault needs a ruling, the 17:30Z latest start still holds. Otherwise the run starts the next morning at or after 05:00Z.

### D. Process slips (for the record)

A `cat >>` heredoc appended to `test_demo_combined_finish_rows.py`, and a `sed -i` edited `test_ch9b1_origin_readers.py`. Both broke the Write/Edit-only rule. Both edits are committed, and the scoped tests cover them (303 passed; the allowlist count is checked by its own test). **No rework.** The builder declared both, which is what we want. The next builder's brief repeats the rule. A third slip goes to the coordinator as a process fault.

### E. Size

The unbuilt rows were already inside the 1.75, so moving them to step 7 adds nothing. New in this ruling: C1, C2, the B fixes and P0 together cost **+0.25**. **DD-1b2b now has 1.0 left:** step 6, the step-7 after tool and reads, step 8, step 9, and this ruling's 0.25. Its total is 2.25. **Lane 2 remaining: 1.0 + CH-5d1's 1.0 = 2.0.**

### Owner

- **Now (information, no decision):** "Before the full rehearsal we run one small test build (6 example days, about 40 minutes) to prove the new parts on real data. It is the same kind of small build as before, not a second full run. We also made sure a late check failure can't throw away the rehearsal's data."
- **After the run:** R6 §5 and R7's triggers, unchanged.

