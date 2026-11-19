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


