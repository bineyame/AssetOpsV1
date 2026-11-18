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

## D-SR.19-30 SR-5 and SR-6/7/8 pre-flight rulings (Architect, Claude, 2026-11-12, owner-delegated, logged for owner review)

- Detail and evidence: sequence doc **Revision 10a**. Inputs: `.agent/SR-678-preflight.md` (4db92b874), `.agent/SR-5-packet.md` (7ae69039b).

### D-SR.19 SR-6 reading cutoff is the disposition time.
- Accepted readings join `ingestion_disposition` (ACCEPTED, `accepted_evidence_id = e.id`, `decided_at <= k`) with `tenant_id`, bucketed on `COALESCE(interval_start, source_time)`, as the dispatch read does. Diagnostics stay on `received_at <= k`.

### D-SR.20 READINGS_ONLY contact state; no demo diagnostics work.
- A gateway with no diagnostics on a day but readings through it reads "Readings received; no status reports". NOT_EXPECTED applies only when nothing arrived. Parity reports diagnostic counts per Site.

### D-SR.21 Dead SR-6 branches dropped.
- No file-import text, no null-cadence rule (gateway ids and cadence are NOT NULL).

### D-SR.22 One day-state rule in `estate/range_days.py`.
- Lane H extracts `range_day_states` (SR-5a precedence + coverage-wins, step 6 = ANALYSED). SR-5a maps ANALYSED to FINDINGS/CLEAR; SR-6 shows ANALYSED and calls `select_finding_scope` only for coverage. If SR-5 core is held, the module merges with SR-6.

### D-SR.23 SR-6 read shape and late router wiring.
- One `read_snapshot`; `_health_registration(snap._c, ...)` called; new adapter for the two grouped queries; source NOT_EXPECTED from the day state. New range routers are new builder functions included after `responses` and `estate_portfolio` in `main.py`.

### D-SR.24 SR-7b reuses the evidence-money claim-day pattern; no `claim_days`.

### D-SR.25 SR-7b day row is `reduce_day`; link `/sites/{code}/evidence?day=&revision=`.
- No invented day ceiling; null revision → NO_SELECTION. The table lives in Site Evidence's claim-limit section.

### D-SR.26 SR-7a hours from row seconds; NO_CRITICAL_LOAD dropped; NO_VALUE state.

### D-SR.27 SR-8 shows the low–high band.
- States COUNTED/EXCLUDED/CONFLICT/LIMITED/MISSING_HOUR; averages of low and high separately over ELIGIBLE days; hours over operating hours.

### D-SR.28 SR-5 safe readings.
- Confirmed: evidence scope in the snapshot, `actions.open` (import `CLOSED_LABELS`), local→UTC day mapping, unmatched = STILL_PROCESSING, coverage-wins → FINDINGS/CLEAR (logged, counted in parity), route tests in one file. Corrected: `findings.count` follows the Portfolio's `finding_known` null rule.

### D-SR.29 Demo Sites and parity windows.
- KOBO-001, KISIWA-001; windows end at the last complete UTC day with accepted readings after the VPS prepare; 7/14/31 days; recorded in each parity JSON.

### D-SR.30 Route classes.
- N: opportunity, action, verification, fuel-verification, fuel-finding, foundation change and maintenance-request detail pages. Work subtabs covered by the Work row (matrix test proves; else SR-9). Cold/EV performance subtabs R. Mini-grid Fuel and Backup subtabs D with honest tag; range form is an owner item (Fuel ~0.5 via `avoidable_gen_min`; Backup needs chain work). Cold/EV asset pages pending the SR-4 route list.
- Sizes: SR-5 2.1, SR-6 1.1, SR-7 0.75, SR-8 0.5; package about 15.8.

Decisions logged for owner review: **D-SR.19-30**.


## D-SR.31-38 Every tab follows the range; SR-10 to SR-14 (Architect, Claude, 2026-11-12 night, owner-directed, logged for owner review)

- Owner, verbatim (`.agent/owner-all-tabs-respect-range-2026-11-12.md`): "all tabs should respect the date range without exception"; "we have to work on the items and reassess on saturday and not limit what is in or not now". Detail: sequence doc **Revision 10b**.

### D-SR.31 Fuel and Backup ranges come from stored day rows, not a chain measure.
- Correction to 10a: `avoidable_gen_min` is dispatch minutes, not fuel. A new MINIGRID measure would change every day grade, so it is ruled out. Two `site_period_read` kinds, `mini_depth.fuel_day` and `mini_depth.backup_day` (local_day grain, every Site-local hour through `MiniDepthRead._hour`), with the existing register, tick and `period_backfill` CLI. There is no migration and no builder-version bump. An absent row reads STILL_PROCESSING.

### D-SR.32 SR-10 Fuel range (Kobo, 0.9 with the core).
- `fuel-range` route, `site-fuel-range-1`, a modelled expected-use band per day, and residual never summed. Page `MiniFuelRange.tsx`. MOCK DEVIATION R727.

### D-SR.33 SR-11 Backup range (0.6).
- `backup-range` route, `site-backup-range-1`, backup start sequences per day de-duplicated by chain, never an outage count. Page `MiniBackupRange.tsx`. MOCK DEVIATION R728.

### D-SR.34 Sweep result.
- Data tabs that still had a label instead of range output: Kisiwa fuel-check nights (SR-10k, 0.25), Evidence rejections (SR-12a, 0.3), Evidence analytics readiness (SR-12b, 0.25), Foundation changes list (SR-13, 0.2), price and EV assumption history (SR-14, 0.3, R729).

### D-SR.35 What stays N (not a period).
- Foundation and its views and SLD (configuration), battery/asset configuration pages (pending the SR-4 asset list; readings mean SR-9), the Sites index, and single-record detail pages. The owner confirms this on Saturday.

### D-SR.36 Demo backfill.
- `period_backfill build` for the two kinds on KOBO-001 and KISIWA-001 after the VPS prepare. If the head-count pre-flight shows missing fuel/backup heads, stop and ask; no reconcile without a ruling.

### D-SR.37 Lanes and order.
- G: SR-4, then SR-12a, SR-12b, SR-13. H: SR-5, then SR-5c, SR-5d, SR-14. I: SR-6, then SR-10k. J: SR-7, then SR-11. K: SR-8, then SR-10. The non-range items follow in priority order, with AR-4 and WARM-1 first if unmerged.
- Merge order: SR-4, 5 core, 6, 7, 8, 5c, 5d, 10, 11, 10k, 12a, 12b, 13, 14, then the rest.
- Package about 18.6 units (was 15.8). The freeze tail is at risk; nothing is dropped now.

### D-SR.38 Saturday reassessment replaces the drop order.
- Sat 14 Nov 12:00. Inputs: merged and ACCEPTed units, High/Medium findings, the parity/timing JSONs, the rehearsal check, and units left per lane. Candidates to the owner, in deferral order: DATA-10/13, FR-B, UQ-FI-3, DATA-5/4/8, MB-1, UP-1, SR-14, SR-13, SR-12b. The options are after the freeze, or the freeze moved to Sun 15 Nov 20:00.

Decisions logged for owner review: **D-SR.31-38**.

### D-WARM.7 WARM-1 review L2: warm the Findings state chips and Portfolio `scope-ids` (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)
- They are one-click stored routes, so they are warmed, like D-WARM.5's lens pages. Per warmed range: `/api/estate/findings` per chip `state=` value (`findingIndex.tsx:275-290`), and `/api/estate/portfolio/scope-ids` for the first page (`EstatePortfolio.tsx:623`), each with exactly the frontend's query. `--verify` covers them, and a URL-equality test pins them.
- Outside the claim (added to D-WARM.5): lens × state combinations, and `scope-ids` page 2 and later. Detail: sequence doc 10b.6. Size about 0.05, lane A fix round.


### D-SR.39 Range means telemetry and its consequences (owner principle, 2026-11-12 night).
- IN: SR-10, SR-11, SR-10k, SR-12a, SR-12b (readiness only).
- OUT, as N (configuration or assumption facts): SR-13 (Foundation changes) and SR-14 (prices/EV assumption history). MOCK DEVIATION R729 is withdrawn.
- Unaffected: STILL_PROCESSING, and per-day money at each day's price.
- Package about 18.1 units. Lane G: SR-4, SR-12a, SR-12b. Lane H: SR-5, SR-5c, SR-5d, then non-range items. Detail: sequence doc rev 10c. Logged for owner review.

## D-SR.40-46 and D-WARM.8: SR-4 tests and builder calls, unlisted routes, SR-7 Q-J1-5, WARM-1 lens scope-ids (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Detail: sequence doc **Revision 10d**.

### D-SR.40 SR-4's 31 superseded App-level tests.
- 26 tests are updated to positive tests of the new behaviour (10d.1 rows 1-12): Site links carry the range, also from global Work; a bare address opens on the entry range; on a refused read, tabs carry the valid address range, never the refused body's window, and none for an invalid address (R347 kept in purpose); EV Health and Scenarios reads get the range; Site Work opens on the shared range; "two hours" Backup/Fuel reads the 12:00 hour of `pageDay`, and the refused frame is pinned with a reversed window. Never delete a case.

### D-SR.41 SR-4 changes (5 tests).
- (a) An address whose `from` instant is not before its `to` instant is invalid in `readSharedRange` (compare instants before rounding to days).
- (b) The Cold and EV R244 correction link reads "Open with the default date range". `evDepth:338` compares the exact href.
- (c) Site Maintenance's list read sends the range's `from`/`to`. If the call is proven to be unwindowed by design, stop and ask.

### D-SR.42 Builder calls confirmed.
- (a) The Backup/Fuel span tag, until SR-10/11. (b) Spoken "the present state". (c) The SiteAnalyticsFrames ratchet shrink (27→26, 31→30). (d) A target's own `from`/`to`/`known_at` win per key.

### D-SR.43 Assets list and battery page are N (configuration) on every Site type.
- No readings, condition UNKNOWN, no SR-9. Both frames declare "current settings".

### D-SR.44 Unlisted routes.
- R: mini Backup/Fuel (via SR-11/SR-10/SR-10k; D tag until then), EV evidence and analysis (a request without from/to becomes SR-9), Cold/EV scenarios.
- N, one record: fuel finding, Mill/Fuel verification, Opportunity detail, Action pages.
- N, "prices valid now": Cold/EV financial assumptions.

### D-SR.45 SR-7 Q-J1-5.
- J1: `window_days` is confirmed, for every new range read (SR-6/7a/8/10b/11; corrects 10b.2).
- J2: LOW is never counted; PARTIAL with a value is counted, with `partial: true`; a missing row reads NO_DATA, by the chain rule, and parity reports days with readings but no row.
- J3: the codes and the 409 gate are confirmed.
- J4: compare to `reduce_day(claim_limit_on)`, plus a 200 drill-in check per row link.
- J5: `estate_request("evidence")` is confirmed.

### D-SR.46 Build sheet restored.
- Commits d7288e5d6, ef18dad9d and 23459a1f9 overwrote this sheet. Revision 10d restores it, and rulings are appended only.

### D-WARM.8 Portfolio scope-ids under each lens are warmed.
- `scope-ids` with `lens=cost|risks|opportunities` is added for every warmed range, using the client's exact query. It is covered by the URL-equality test and `--verify`. Page 2 and later, and lens × state, stay outside the claim. About 0.02 units.

Decisions logged for owner review: **D-SR.40-46, D-WARM.8**.

## D-SR.47 SR-8 Q2-Q5 (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Detail: sequence doc 10d.7.
- Q2: NO_VALUE is confirmed ("No headroom figure for this day"; never counted).
- Q3: rounding to 0.01 kW, half-up, applies to the two averages only; daily values are stored, unrounded.
- Q4 is corrected: LOW → NOT_ENOUGH_READINGS, never counted (as D-SR.45). PENDING, NO_DATA and NOT_EXPECTED win. A PARTIAL ELIGIBLE day is counted, with `partial: true`.
- Q5: the codes and the optional `known_at` (in the stored key) are confirmed.

Decisions logged for owner review: **D-SR.47**.

## D-SR.48 SR-8 Q6: the range shows the stored "every eligible hour" headroom; the day page adds the same figure (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Detail: sequence doc 10d.8.
- Range page: the stored `daylight_headroom_kw` (min low, min high), worded "Headroom available in every eligible hour". The chain measure is unchanged.
- One-day page: the envelope adds `all_hours_headroom_kw` (min low, min high over ELIGIBLE hours), shown as one line with the same words. The existing card keeps its envelope, worded "Range across eligible hours" (inside R726).
- Parity: the stored day value equals `all_hours_headroom_kw` exactly, and the card high is at least the stored high. About +0.1 units.

Decisions logged for owner review: **D-SR.48**.

## D-SR.49 SR-6a Q1-Q5 and guard policy (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Detail: sequence doc 10d.9.
- Q1: corrected. `days_without_readings` = expected days with zero accepted readings, whatever the SR-5a state. `days_not_expected` and `days_after_cutoff` are added, and the four sum to `days_requested`. The status line counts readings.
- Q2: confirmed, over expected days only (NOT_EXPECTED and AFTER_CUTOFF are skipped).
- Q3: confirmed: the dispatch-row count. It can differ from the per-source sum, so the labels are "Readings used for analysis" and "Readings received".
- Q4: new state AFTER_CUTOFF ("Not reached yet") for gateway and source days wholly after `min(to, k)`. `days[].state` is unchanged.
- Q5: `battery` is dropped from the body. The page uses the existing `/battery` read. There is no Foundation 409 on the route.
- Guard: the one read-only adapter in `$pgReaders`, with the write refusal kept and reads through the compositions, is the sanctioned pattern.

Decisions logged for owner review: **D-SR.49**.

## D-SR.50 SR-5: the range names retired Findings; Postgres cases without a world (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Detail: sequence doc 10d.10.
- 1: the member count (Portfolio parity) and the S5-01 drill-in are both kept. Each day adds `retired_finding_count` (non-member latest revisions intersecting the day, from the same Finding read; stop and ask if that read lacks lifecycles). The wording is "Checked: no current findings · 1 finding no longer supported". The state stays CLEAR. The test pins agreement: board = members + retired. About 0.1 units.
- 2a NOT_EXPECTED: covered by the no-DB precedence pin and the parity report.
- 2b: the MD-0 states template is not built now. It is covered by the F08 coverage-wins pin, no-DB tests and the parity gaps == coverage gate; the template is backlog after the freeze.
- 2c: no-DB stubs for SUMMED/OVERLAPPING are required. Parity checks money == Portfolio and reports the OVERLAPPING count; 0 is recorded as stub-only.

Decisions logged for owner review: **D-SR.50**.

## D-SR.51-54 SR-10 builder interpretations, the kill switch, the rebuild test, and the day-kind build time (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Detail: sequence doc 10d.11. Branch `task/SR-10-fuel-range` (core 7f928edb2, route 3fc8c4c23, Postgres pins 3ed855559).

### D-SR.51 Interpretations 1-4.
- 1 confirmed: pending = `PENDING_RECOMPUTE` or a live job (PENDING/LEASED); every sum, count, limitation and sequence covers assessed hours only.
- 2 confirmed: `slowest_recovery` = the largest `critical_recovery.seconds` over the de-duplicated sequences; a null is skipped; `target_seconds` comes from the same sequence; a tie goes to the earliest `outage_start`.
- 3 corrected: an absent row is unknown, not zero. Its entry has `stored: false`, and its hour counts, `status_counts`, `expected_use_l` / `sequence_counts` / `start_success_count` / `slowest_recovery` are null (`hours_expected: 0` is removed). Stored rows carry `stored: true` and never null counts. The page shows "Still being prepared" for the whole row, never "0 of 0 hours".
- 4 confirmed, plus one fix: totals `sequence_counts` and `start_success_count` de-duplicate sequences by `chain_id` across the window (latest day wins), so a sequence that crosses local midnight counts once. Backup `days_counted` counts its four states; fuel counts ASSESSED.

### D-SR.52 The kill switch (interpretation 5).
- Accepted. `ASSETOPS_PERIOD_READ_KINDS` selects stored rows over a compose; the day kinds have no compose (D-SR.31), so honouring it would only blank the range. The safety behaviour is the honest STILL_PROCESSING row plus the hour drill-in, which composes live when the switch is empty.
- Required: a stub test pins that the fuel range reads rows with the switch empty, and a code comment names D-SR.52. The prepare's failure line for the day kinds names the rerun command, not the switch (D-SR.54).

### D-SR.53 The rebuild test (interpretation 6).
- Enough, as AR-1's precedent: ingest-to-event is pinned elsewhere, and the parity run (3 days x 24 hours per Site) checks real readings. Two additions: the event is built with the ingest path's own event helper if one exists (otherwise named as hand-built in the test docstring); and one boundary case: a reading at Site-local 00:30 (UTC the previous day for Nairobi) dirties the local day, not the UTC day. If the register keys the dirty day another way, stop and ask.

### D-SR.54 Day-kind build time in the prepare and the D-SR.36 backfill.
- A timing check is needed. Estimate from AR-2 (KOBO 128 periods 69.1 s, KISIWA 52 periods 38.7 s, about 0.55-0.75 s per hour read): about 1,500 hour reads for KOBO and 600 for KISIWA, so about 15-20 minutes, which would breach the shared 15-minute cap and push the board rows out.
- `build_period_rows` builds the board kinds first with an explicit `--kind` list, unchanged under the 15-minute cap, then the two day kinds in a separate step with their own cap: **30 minutes for both Sites** (twice the 15-minute estimate). `period-rows.json` records each step's seconds and the seconds per hour read. The prepare's wall cap adds the step's expected 900 s.
- Over the cap or on failure: "Fuel/Backup range rows incomplete: rerun `period_backfill build --kind mini_depth.fuel_day --kind mini_depth.backup_day`"; the prepare goes on and the board kinds are unaffected.
- D-SR.36 on the VPS: run the head-count pre-flight first, then time per Site. If KOBO's first 3 days run over 1.0 s per hour read, stop before the whole window and ask.
- Tick: the parity JSON records one dirty-day rebuild (both kinds, one Site-day). If it takes over 60 s, report it; it does not gate.
- SR-10 fix round about 0.1 units (51.3, 51.4, 52, 53, 54 prepare split), on a Sonnet builder. Package about 18.3 units.

Decisions logged for owner review: **D-SR.51-54**.

## D-SR.55 SR-10k Q1-Q4 (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Branch `task/SR-10k-kisiwa-fuel-nights` (server 931c4b783, page bf9ca80e6), packet `.agent/SR-10k-packet.md`.
- Q1: **keep both forms.** The K5 night-date form (`FUEL_BALANCE_RANGE_INVALID`, pinned by K5 B2) stays for its existing callers. The instant form is the range form. The route docstring names both and the rule that tells them apart (a `T` in either value). A mix of the two forms is refused with 422 `INVALID_WINDOW`, and a stub test pins this.
- Q2: **confirmed.** `INVALID_WINDOW` uses the nights sentence ("Choose up to 31 nights, with the first night before the last.").
- Q3: **both send `known_at` when the range has one**, through `rangeParams` as every other range read does (SR-6/7a/8/10b keep `known_at` in the stored key). Without one, the request is unchanged. The server already accepts `known_at` on the list and on the detail, so this is a page change only. Add a vitest pin that the list and detail URLs carry the same `known_at`.
- Q4: **corrected.** A `?night=` link names one record (N, D-SR.44), so it opens that night and never swaps it silently. The list stays filtered to the range. Above the detail, one line reads "This night (4 Nov) is outside the selected date range", without widening the range. A night that does not exist keeps the existing NIGHT_NOT_FOUND refusal. Add a vitest pin.
- Size about +0.05 units (page only). Package about 18.35 units.

Decisions logged for owner review: **D-SR.55**.

## D-SR.56 SR-6 review M2 and L1: the local-day grade on UTC days, and Health's watermark (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Source: `.agent/SR-6-review-server.md` (04e468a60), M2 and L1.
- **M2: the mapping stays as ruled.** `estate/range_days.py` gives a UTC dispatch day the chain grade of the Site-local day with the same date. That is coverage's D-E5.42 rule (`estate/coverage.py:194-211`). The range Overview's whole job is to equal the Portfolio day by day (D-SR.22, SR-5 parity), so changing the mapping in `range_days` alone would break that parity. Changing it estate-wide is a coverage change, which is out of scope for the freeze. So there is no code change to the mapping.
- **Where it can show.** NOT_EXPECTED is a grade only for local days before readings began. For a UTC+3 Site, the UTC day whose date is the last local NOT_EXPECTED day holds at most the 3 hours `[21:00, 24:00) UTC` of the next local day. So **at most one day per Site** is affected: the day readings began, and only if they began between local 00:00 and 03:00. At 5-minute cadence that day has at most about 36 accepted readings. The review probe's 288 readings cannot occur on real data. The SR-6 fix ("readings above 0 win" in the cell and the summary) stays, because Health counts readings (D-SR.49 Q1).
- **SR-5 change (wording only, about 0.02 units).** The state stays NOT_EXPECTED, so the Portfolio parity holds. When the day's dispatch row has `accepted_reading_count > 0`, the Overview day cell reads "Readings began late this day · not counted", not "Before readings began". Add one no-DB test.
- **Parity must catch it.** The SR-5 and SR-6 parity JSONs gain `not_expected_with_readings: [{site, day, accepted_readings, readings_began_local, readings_began_utc}]`.
  - **Gate:** at most one such day per Site, and it must be the UTC day whose date is the last local day before `readings_began`. Any other day, or more than `12 x UTC offset hours` readings on it (36 for UTC+3), fails the gate: that would mean the mapping is wrong beyond the zone edge.
  - The existing comparisons stay as they are. They are the gap set == coverage gaps and members == Portfolio (SR-5), and the per-day `accepted_readings` == the SR-5a dispatch row (SR-6). They cannot detect this, because both sides use the same mapping. That is why the new check is added.
- **L1: accepted as a known limit for the demo.** The demo windows are historical (D-SR.29), and diagnostics do not change after the prepare, so no stale contact can show in the demo. The "Contact now" panel stays the point-in-time view.
  - The packet and the Health range code name the limit. Without `known_at`, contact and registration flags refresh at `valid_until` (the next local midnight) or on the next readings arrival.
  - Backlog, after the freeze: add `gateway_diagnostic` (and `gateway` and `source` for registration flags) to the watermark input tables. That is a migration-level change to 0047's inputs plus a watermark test.

Decisions logged for owner review: **D-SR.56**.

## D-SR.57 SR-4c review L2, L3 and the two-declarer risk (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Source: `.agent/SR-4c-review.md` (5b1eba3b1, `/opt/assetecon/AssetOpsV1-sr4`).
- **L2: intended. S15's cutoff pin gives way to the shared range.**
  - Scenarios reads under the shared range's `known_at` when the address has one. Otherwise it reads live, like every other range page.
  - It does **not** adopt the server's `known_at` into the address. An adopted `known_at` would travel on the rail to every other tab (D-SR.2) and silently turn the whole Site historical.
  - Cursor pages keep the body's bound, as now. `miniDecisions.test.tsx:309-311` ("no adoption") stays.
  - Fix: rewrite the header at `MiniScenarios.tsx:4-7` to say this. The adoption branch stays only for the address-free case, which happens outside the shell. Cite D-SR.57.
- **L3: corrected to per key.** `withRange` adds the address `known_at` to a target that names `from`/`to` but no `known_at`. The target's own `from`, `to` and `known_at` still win.
  - Reason: a drill-in from a range pinned to a cutoff must read at the same cutoff. The SR-10/11 `hour_link` and the SR-5/6/7 day links name `from`/`to` only, so otherwise they would read live and could disagree with the row the user clicked.
  - Change `sharedRange.ts:160`: keep the target's `from`/`to`, and when the target has no `known_at`, append the address `known_at` if the address has one. Update `rangeLink.test.tsx:67-72` to the new expectation; do not delete the case. Add one case: a target with its own `known_at` keeps it.
  - Size about 0.03 units; SR-4 fix round.
- **Two declarers: one declarer per view.**
  - In the hour view of Service, Backup and Fuel, FocusPicker is the only declarer. `WindowSpan` keeps its visible text but stops declaring into the focus slot.
  - Its range-without-hour declaration (D-SR.42a) is removed when that page's range view lands: SR-10c for Fuel, SR-11 for Backup, SR-7's page for Service. The range view then declares nothing (rev 10b.2).
  - Each of those slices adds one vitest that the focus slot is declared once in the hour view.

Decisions logged for owner review: **D-SR.57**.

## D-SR.58 SR-11 Q1-Q3 (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Source: `.agent/SR-11-packet.md` (`task/SR-11-backup-range` 713bbf7d8).
- **Q1: yes.** On an absent day (`stored: false`) `sequences` is null, like every other D-SR.51.3 figure. A stored day with no sequence has `[]`. Pin both cases in the pure test.
- **Q2: count start successes from the sequences, not from the hour cards.**
  - Why: the hour card (`mini_depth/rules.py:1072`) counts SUCCEEDED `start_pair`s over that hour's chains. A sequence that spans hours is counted in every hour, so the sum double-counts within a day as well as across midnight.
  - Change (shared `day_summary.py`):
    - Each `sequences` entry gains `start_pair`, copied from the head's chain.
    - The day `start_success_count` is the number of de-duplicated sequences with `start_pair == "SUCCEEDED"`. It is null when every sequence's `start_pair` is null or there is no sequence.
    - The window total counts the same thing over the sequences de-duplicated across the window (D-SR.51.4).
  - If the stored head result does not carry a per-chain `start_pair`, stop and ask; do not recompute.
  - Tests:
    - one sequence over two hours gives 1;
    - one sequence over midnight gives 1 in the window total, while each day's own count still shows it;
    - the null rule.
  - The UI wording stays "backup starts". About 0.05 units, SR-11 fix round.
- **Q3: acceptable.** The grade order is pure and pinned in the stubs. The day rows in the Postgres test are real. The real grade path is closed by parity:
  - the SR-10 and SR-11 parity runs call each live range route (real `PostgresChainRead`) for KOBO-001 and KISIWA-001;
  - they compare every `days[].state` NOT_EXPECTED / grade-derived outcome with `chain.read.day_grade` for the same day;
  - the gate is 0 mismatches.

Decisions logged for owner review: **D-SR.58**.

## D-SR.59 SR-4a+b review H-1, L-1, L-4: short ranges on the mini depth tabs (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Source: `.agent/SR-4ab-review.md` (7f9a0bd9e, REJECT). Rev 8 §8.2's "pass the address window through" is withdrawn for these tabs. It is an Architect spec defect, not a builder one.
- **H-1: the fix is in the client. The server stays strict.**
  - The one-hour and one-to-five-day reads (`mini_depth/read.py:112-138` `hour_windows`) are point reads. The SR-10/11 `hour_link` and the FocusPicker send them exact Site-local windows, and every range view gets its days on the server by D-SR.45 `window_days` (SR-7a/8/10b/11). So the client turns the range into the Site-local window the server takes, by the same `window_days` rule: **a range of UTC dates names the Site-local days of those same dates.**
  - Do not loosen `hour_windows`. It is the contract that refuses a malformed drill-in.
- **Change: `frontend/src/sites/miniDepthClient.ts`.**
  - **Renewable** (`renewableWindowFromParams`, `:342`):
    1. Pass the address through only when both bounds are exact Site-local midnights 1-5 days apart (as `hour_windows` checks).
    2. Otherwise take the range from `addressRange(params)` (the `readSharedRange` result). If it spans 5 days or fewer, send `localDaysWindow(tz, range.from, n)`, where `range.from` is the date string itself, not `localDateOf` of an instant, so a negative-offset zone gets the same dates.
    3. A longer range keeps the existing "last 5 local days" rule.
    4. No range: as now.
  - **Service, Backup and Fuel** (`serviceWindowFromParams`, `:384`):
    1. Pass the address through only when it is exactly one Site-local clock hour (span 1 h and the local minute, second and millisecond are 0).
    2. The `DAY_MS` pass-through is removed. A one-day range, "Yesterday" included, gives the 12:00 local hour of `pageDay`, like a longer range.
    3. The reversed or unparseable pass-through stays, so the page still names why it is refused.
  - `known_at` is carried unchanged.
- **L-4: fix now, in the same lines.** Both functions measure the range through `addressRange` / `readSharedRange`, never raw `from`/`to` strings. The only raw-instant parses left are the two exact pass-through checks above. A hand-typed day-form `from=2026-11-08&to=2026-11-08` then reads as one day and gets 12:00 (Service) or that local day (Renewable).
- **L-1: yes, per key.** The safety net (`SharedRangeBar.tsx:124-132`) applies the D-SR.42(d)/D-SR.57 rule: an address key wins over the copied previous range per key (`from`, `to`, `known_at`), and the result never holds a key twice. Test: a bare Site address with its own `known_at` plus a previous range with another `known_at` gives exactly one `known_at`, the address's.
- **Tests that stop this class from coming back.**
  1. **Vitest, pure** (`sharedRange.test.tsx` cases re-pinned, not deleted), for zones Africa/Addis_Ababa (+3) and America/Bogota (−5).
     - Every bar preset (Yesterday, Last 7 days, Last 30 days), custom 2- and 5-day ranges, a one-hour story address, and a day-form address.
     - The renewable window is exact local midnights covering the same dates. The service window is one local clock hour.
  2. **Shared fixture contract.**
     - The vitest writes nothing. A checked-in `frontend/src/sites/__tests__/fixtures/mini-windows-contract.json` lists those inputs and the expected `{from, to}`, and vitest asserts the functions equal it.
     - A new no-DB `backend/tests/test_sr4_mini_windows_contract.py` feeds every expected window to `hour_windows` (and the `fuel`/`backup`/`service` domains) and asserts none is `INVALID_WINDOW`.
     - So a client or server change that breaks the pair fails one side.
  3. **App level** (`sr2RequestUrls.test.tsx`): Kobo Renewable and Kobo Service under the "Yesterday" preset each send one request with the pinned local bounds, and render no refusal.
- Size about 0.15 units, in the SR-4 fix round, then a fresh review. SR-4 stays first in the merge order.

Decisions logged for owner review: **D-SR.59**.

## D-SR.60 SR-11: start successes stay the hour-card sum; D-SR.58 Q2's change is withdrawn (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- The SR-11 builder stopped correctly: stored backup rows have no per-chain `start_pair` (`mini_depth/projection.py:181-188`).
- **D-SR.58 Q2 rested on a wrong premise and is withdrawn.**
  - `rules.assess_backup_hour` (`rules.py:1029-1043`) opens a chain only for a LOST transition **inside** the hour.
  - It bounds that chain at `min(restoration, hour end)`.
  - So every chain belongs to exactly one hour, the hour that holds its LOSS. No chain spans hours or crosses midnight.
  - The hour-card `start_success_count` (`rules.py:1072`) therefore counts each chain's witnessed start once. Summing the cards over a day or a window is exact, so there is no double count to label.
- **Ruling (option c, without a label):**
  - Keep the hour-card sum for the day and the window, with its null rule (null when every counted hour is null).
  - No `start_pair` field, no projection or `BUILDER_VERSION` bump, and no re-backfill.
  - The 30-minute day-kinds step (D-SR.54) and parity are unaffected.
  - Option (a) would have meant a projection change plus re-running every backup head, with no gain.
  - Option (b) cannot work: `start_pair` comes from observation outcomes, which are not stored.
- **Pin the premise:**
  - a pure test that one stored day's `rows[].chain_id`s are unique across its hours;
  - the SR-11 parity JSON reports `duplicate_chain_ids` per Site and window, gate 0.
  - If it is ever non-zero, the hour rule has changed: stop and ask.
  - The D-SR.51.4 chain_id de-duplication of `sequence_counts` stays, as a harmless guard.
- Size: the 0.05 from D-SR.58 Q2 becomes about 0.01, for the pin.

Decisions logged for owner review: **D-SR.60**.

## D-SR.61 SR-4: negative-offset zones use the range's date strings everywhere (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Source: `.agent/SR-4ab-review.md` re-review (f039e5d56).
- **Confirmed: this is a D-SR.59 implementation defect.** The rule is that a UTC date names the Site-local day of the same date. So no path may take `localDateOf(tz, <UTC midnight>)`, because west of UTC that lands one local day early.
- **The fix:** the long-range Renewable rule (the last 5 local days) and the Service/Backup/Fuel default hour (12:00 local of `pageDay`) use the date string itself, `range.to` / `pageDay`, as the short-range Renewable path already does.
- **The fixture:** re-pin the Bogota windows deliberately. For example, Bogota "Yesterday" = 11 Nov gives 12:00 local on 11 Nov (17:00Z on 11 Nov). The +3 rows are unchanged, so the vitest and the backend contract test stay green on them.
- **Before SR-4 merges: yes.** The demo Sites (+3) are unaffected. But the change is a few lines, and merging would put a wrong expectation into the contract fixture that is meant to stop this class of defect.

Decisions logged for owner review: **D-SR.61**.

## D-SR.62 SR-8 parity: the one-day read follows the stored measure's missing-hour rule (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Detail: sequence doc 10e.1. Evidence: `AssetOpsV1-sr8` 26fd97b7a `SR-8-parity.json`; `assetops_polish_vps1_test`, read only.
- **Cause.** The Kobo Finding days (27 Oct, 3 and 10 Nov) have 7 headed daylight hours, 2 of them ELIGIBLE at 25-31 kW, and 16 missing hours with no PV coverage.
  - The stored `daylight_headroom_kw` (`measure_impls.RenewableHeadroom`) counts the daylight hours and grades the day PARTIAL.
  - `read.compose_renewable` treats any headless window as a missing day, so it returns UNKNOWN and null cards. It cannot tell a missing hour from a daylight hour with no revision.
  - The parity note "all 7 rows EXCLUDED" is a harness error: 09:00Z and 10:00Z are ELIGIBLE (seq 1081, 1094).
- **Ruling: the stored side is right** (D-SR.9, D-SR.47 Q4; the chain measure is unchanged, 10b).
  - `_Hour.missing` is set from `daylight_hours(...).missing`, and stored in `hour_json`. `BUILDER_VERSION` becomes `mini-depth-rows-2`.
  - `compose_renewable(..., missing=)` leaves missing hours out. A day is missing only when a non-missing hour has no head.
  - `summarize_renewable(partial_days=)`: a partial day never establishes recurrence.
  - The envelope gains `missing_hours`. The one-day page shows the D-E5.45 PARTIAL label with the range row's words (inside R726). D-SR.48's null rule holds.
- **Tests.**
  - Pure: the Finding-day shape gives SUPPORTED with both cards 25-31; a headless daylight hour still gives UNKNOWN; a partial day gives no recurrence.
  - A shared-rule pin against `RenewableHeadroom.measure`, plus the row round-trip and the Postgres sampled partial day.
  - Parity rerun: gate 0, `missing_hours` equal, and the harness reads `rows[].decision`.
- **Board.** The Grow board uses the same compose. Its fixtures are unchanged. Any change to a real-data pin is recorded as expected.
- **Rebuild.**
  - `site_day_snapshot`: none.
  - `mini_depth.*` period rows: rebuild with `period_backfill build --site KOBO-001`, then `--site KISIWA-001`, then rerun the parity.
- Size about 0.3 (Sonnet fix round, fresh Claude re-review). SR-8 merges only after the parity passes.

Decisions logged for owner review: **D-SR.62**.

## D-SR.63 The rows-on switch for the 17 Nov build (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Detail: sequence doc 10e.2. Basis: rev 7 (AR-2 to AR-4): a kind is switched on only on a DB whose rows are built, and only after parity.
- **Code, now (about 0.05).**
  - `demo_combined.serve_env()` sets the six kinds (`dispatch.day`, `evidence.claim`, `mini_depth.renewable/fuel/service/backup`) only when `period-rows.json` reads `ok: true`. Otherwise it stays empty, with the existing failure line.
  - An operator's override wins.
  - A stub test pins all three cases.
- **Current demo DB.**
  - `dispatch.day` and `evidence.claim` may go on now: rows built, parity passed, and the SR-8 fix does not touch them.
  - The `mini_depth.*` kinds go on only after the D-SR.62 merge, the rebuild, and a parity rerun with 0 differences.
- **17 Nov build: all six on**, after SR-8, SR-10 and SR-11 merge, the final prepare's row steps are ok, and one final six-kind parity run on the final DB gives 0 differences.
  - SR-10/11 parity does not gate the six kinds: their day kinds read rows regardless (D-SR.52).
  - Their merge changes the prepare, so the one final parity run comes after it.
  - A kind that fails parity is left out alone, logged and reported. Nothing falls back silently.

Decisions logged for owner review: **D-SR.63**.

## D-SR.64-68 SR-4 live check (F1-F3, the migration 409) and the SR-8 empty day (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Detail: sequence doc 10e.3. Source: `AssetOpsV1-sr4` 01f4d3981 `SR-4-live-check.md`; SR-8 223783035.

### D-SR.64 F2: Cold/EV Finding detail reads its own episode.
- The page sends only `known_at` to `getFinding`. The range stays in the address, for onward links.
- With no `from`/`to`, the detail reader takes the window of the analytic run that wrote the latest revision known at k, as `linked_finding` (D-E5.8) does. An explicit window keeps the anchor rule.
- A new tag note: "Range not used · this record's own period", on Finding detail for every Site type.
- Tests: Postgres for Cold and EV, plus vitest. About 0.2, inside SR-4 before it merges. If EV runs store no window, stop and ask.

### D-SR.65 F1: Kisiwa Fuel nights.
- SR-4 declares the day of the night shown: "Showing 10 Nov · range not used", never "All pages" (about 0.02).
- SR-10k is the next merge after SR-4, with nothing between them.

### D-SR.66 F3: Cold/EV financial assumptions. Corrects the D-SR.44 row.
- Remove the `RangeNotUsed "prices valid now"` declaration. The view declares what the same Site's Financials declares.
- The price values keep their in-page wording. Two tag pins (about 0.03, inside SR-4).

### D-SR.67 The evidence-migration 409.
- **This is a prepare gap.** `finish()` runs `evidence_migration` for Kobo only. The Kisiwa and EV ledgers therefore stay closed (`permits_cutover`), and the laptop builds were the same; that is from code, not seen.
- `/analytics` is the legacy surface and is 409 for every imported Site by design.
- **17 Nov.** The prepare runs `evidence_migration` for every imported story Site, then `performance_migration` where the Site has that surface. An exit 2 stops the prepare and goes to the Architect.
- **Serve** from the build tree, or rerun the comparison in any other serve tree first.
- **Gate:** no "Awaiting evidence migration" panel on any client-visible page (live check). About 0.1.

### D-SR.68 SR-8: a day with no solar reading at all.
- The builder (1a4d94dd5) is confirmed: the day stays a missing day in the one-day read (UNKNOWN, null cards).
- The stored measure has no headed hour, so the range row is NO_DATA and the day is not counted.
- D-SR.62 is clarified: missing hours are left out only when the day has at least one stored hour result. Add a pure pin.

Decisions logged for owner review: **D-SR.64-68**.

## D-SR.69 KOBO-001 10-31: a story gap; the SR-10/11 head gate on NO_DATA days (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Detail: sequence doc 10e.4.
- **10-31 and 11-06 are both story `missing` days** (gateway offline; `days.json` entries 49 and 68). Chain grades are NO_DATA on both, for every measure.
- **11-06's heads have no cause.** Its jobs were created at 2026-11-10 14:00Z, when the Kobo Action was APPLIED: a configuration re-enqueue over no readings. 10-31 was never re-enqueued.
- **Not a build defect.** No heads are built (D-SR.36 stands).
- **SR-10/11 gate:**
  - a NO_DATA day expects 0 heads, is listed under `no_data_days`, and must read NO_DATA, never STILL_PROCESSING;
  - the head check is: no live or FAILED job, and no hour holding the domain's evidence without a head.
  - The partial days are expected.
- SR-5/6/7/8 range pages show both days as NO_DATA, which is honest.
- The one-day wording difference between 10-31 (not assessed) and 11-06 (assessed with no readings) is Low and goes to the backlog.

Decisions logged for owner review: **D-SR.69**.

## D-SR.70-72 SR-10/11 parity findings: pre-data days, the precise head gate, one NO_DATA state (Architect, Claude, 2026-11-12 night, owner-delegated, logged for owner review)

- Detail: sequence doc 10e.5. Evidence: `AssetOpsV1-sr10` 2dac39de2 `SR-10-parity.json`, `AssetOpsV1-sr11` 75abd816a `SR-11-parity.json`; `assetops_polish_vps1_test`, read only.

### D-SR.70 A day with no readings reads NO_DATA, stored row or not (finding 1: option b).
- **Option (b), not (a) or (c).** A real client Site has days before its first reading in almost any range, and no backfill can build rows for every past day. The route must be honest without a row. A prepare that builds from the window start would only hide the demo case.
- **The test of "no readings": the Site's chain day, not one measure.** No mini measure maps to fuel or backup alone, so D-SR.69's "the domain's measure" is refined. A day has no readings when every applicable mini measure grade of the day is NO_DATA (`days_of` entry `measures`, minus `none_declared` and NOT_EXPECTED, at least one left). A missing snapshot counts as NO_DATA (Q9), so a day before the first reading qualifies. A day with only one weak measure does not.
- **File and function.** `backend/assetops_backend/mini_depth/day_summary.py`:
  - new `no_reading_days(facts) -> frozenset[date]` beside `day_grades`, from the same `days_of` read (no second chain read);
  - `day_state(domain, summary, grade, *, no_readings: bool, pending: bool)`, first match wins:
    1. `NOT_EXPECTED`: the day grade is NOT_EXPECTED.
    2. `STILL_PROCESSING`: the row is pending at k (`read.pending` or `result.is_pending`) or `hours_pending > 0`. A day being reprocessed may just have received readings.
    3. **`NO_DATA`** (new): `no_readings`, whether the row is stored or absent.
    4. `STILL_PROCESSING`: the row is absent (D-SR.51.3 unchanged for every other day).
    5. `NO_ASSESSMENT`, then the fuel/backup states, as 10b.1.
  - `range_days` passes both flags. A NO_DATA entry is `absent_day(domain, d)` with `stored` set to whether a row exists; every count and figure is null, `partial` is false, and `hour_link` stays. D-SR.51.3's "stored rows never carry null counts" is amended for this one state.
  - `NO_DATA` is not in `COUNTED_STATES`, so the day never enters a total and `totals.partial` turns true.
- **Words (SR-10c/SR-11 pages).** State words "No readings this day", spanning the row like "Still being prepared". Status line: "Fuel use modelled on 5 of 7 days · 31 Oct: no readings" (backup alike). One wording for a gateway-offline day and a day before readings began: both are true as "no readings".
- **Tests.**
  - Pure (`test_sr10_day_summary.py`): NO_DATA beats an absent row and a stored row with 0 or 24 heads; pending beats NO_DATA; one NO_DATA measure among PARTIAL ones is not NO_DATA; `none_declared` and NOT_EXPECTED measures are left out; a NO_DATA day is not counted and nulls its figures.
  - Postgres (`test_sr10_day_kinds_postgres.py`): a Site-local day before the Site's first accepted reading, with no row built, reads NO_DATA on both routes.
  - Route stubs (`test_sr10_fuel_range_route.py`, `test_sr11_backup_range_route.py`): the state string and null figures in the body.
- **Prepare: unchanged.** `period_backfill build` keeps its first-evidence-day start. The pre-data rows the runner built on the test DB with `--from 2026-10-11` are harmless; parity shows stored and absent pre-data days read the same.

### D-SR.71 The head gate follows the enqueue rule exactly (finding 2: expected, not a gap).
- **Seen in the DB.** The KOBO-001 Tuesday partial days run from local 06:00 to 14:00. The flagged hours hold only boundary rows:
  - local 00:00 (21:00Z): 11 interval rows of the previous run, `[20:55Z, 21:00Z)`. They end at the hour's start and cover none of it.
  - local 14:00 (11:00Z): interval rows `[10:55Z, 11:00Z)` plus instants stamped 11:00:00 (`generator_state`, `battery_soc`). Fuel's roles are `generator_power` and `fuel_level` only (no instant), so fuel has no job. Backup's roles include `generator_state`, so backup has a job and a head (`recompute_job`: `mini_backup` 11:00-12:00 DONE; no `mini_fuel`).
- **The enqueue rule** (`0029_w4_mini_depth.py`, accepted-row trigger): each row whose role maps to the domain (`DOMAIN_ROLES`) enqueues every Site-local hour that intersects `[coalesce(interval_start, source_time), coalesce(interval_end, source_time + 1 µs))`. Heads exist exactly where this rule says. **No head is missing.**
- **Precise gate** (parity harness, `hours_with_evidence_no_head`, **gated at 0**). An hour expects a head when an accepted row:
  - has a role in the 0029 `DOMAIN_ROLES` entry for `mini_fuel` / `mini_backup`; load it from the migration file, do not retype it;
  - satisfies `coalesce(interval_start, source_time) < hour_end AND coalesce(interval_end, source_time + interval '1 microsecond') > hour_start`;
  - and the hour is not on a day in `no_data_days`.
- An hour that matches but has no `minigrid-roles-4` binding set in force for the whole hour (the trigger's no-op) goes to `ineligible_hours`: reported, not gated.
- Report `heads_without_evidence` (for example 11-06's configuration re-enqueue): reported, not gated. D-SR.70 reads such days NO_DATA.
- Cross-check, gated at 0: no day in `no_data_days` has an hour matching the precise predicate.

### D-SR.72 NO_DATA days read one state (finding 3).
- **Today they read three ways, and two are not honest.**
  - 10-31: NO_ASSESSMENT, an empty stored row.
  - 11-06 backup: NO_SEQUENCE, "No backup start recorded" over a gateway-offline day. That is a claim of nothing happening, from no readings. It is counted in `days_counted`.
  - 11-06 fuel: ASSESSED, also counted.
- **Ruling: one state, `NO_DATA`, by D-SR.70's rule ahead of any row content.** This matches SR-5/6/7/8, which show both days as NO_DATA (D-SR.69). D-SR.47 Q4's "the grade wins first" now holds on Fuel and Backup too.
- NO_ASSESSMENT stays only for a day with readings but no assessed hour, which the D-SR.71 gate keeps at 0 on the demo DB.
- The one-hour pages are unchanged: the D-SR.69 wording difference stays Low, backlog.

### Sequencing
- One Sonnet fix round on `task/SR-10-fuel-range` (about 0.15), then merged into `task/SR-11-backup-range`, with a fresh Claude re-review.
- Then a parity rerun of both JSONs with the D-SR.71 harness. The gates:
  - `no_data_days` read NO_DATA: Kobo 10-11, 10-12, 10-31 and 11-06; Kisiwa every day before 11-01;
  - `hours_with_evidence_no_head` = 0;
  - the cross-check = 0;
  - every earlier gate unchanged.
- The pages (SR-10c/SR-11 page) use the D-SR.70 words. SR-10/11 merge only after this passes.

Decisions logged for owner review: **D-SR.70-72**.

## D-SR.73 Estate "Current view" label after SR-4; R339 / ruling 71 / R350 tests now carry the range (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- **Today.** The server sets one constant, `CURRENT_VIEW = "Current view"` (`estate/evidence_money.py:47`). It is written into `links.current_view_label` (`estate/financials.py` `money_link_refs`) and `site_readiness_label` (`evidence_money.window_link_refs`, `_row`). `EstateFinancials.tsx` shows it beside the source link.
  - Since D-SR.2, every Site link carries the page's range.
  - For a Site home that follows the range (SR-5), such as the Kobo Overview, the label is now wrong.
- **Ruling: the label follows the destination, and the server produces it** (closure 5 B5: the server owns links and their words). Replace the constant with `view_label(ref)` in `evidence_money.py`. It is chosen from the destination's D-SR.30/D-SR.44 route class:
  - destination follows the range (Site home/Overview, Evidence): **"Opens this range"**;
  - destination does not use the range (mini-grid Financials bridge, and every other destination that declares "Range not used"): **"Current view · range not used"**. These are the same words the destination's own tag shows (D-SR.44, D-SR.66).
- **Unchanged.**
  - The field names stay as they are.
  - The label is null when the link carries the row's own proven window. `portfolio.py:706` (r1b2 R12) keeps that meaning.
  - The frontend renders the label and never makes up its own words.
  - Fix the docstring "Opens current Site view" to match.
- **Tests.** Add a backend pin per destination class: mini Financials, mini home, cold home, EV home `/sites/{code}/ev`, and the proven-window null. Add a vitest render of both words in `EstateFinancials`. About 0.1, Sonnet.
- **Recorded: test updates on the SR-4 estate-link fix branch.**
  - The R339 (mini bare tabs), ruling 71 (cold case-row Action link) and R350 (cold `/plan`, `/history` verification link) pins now expect `from`/`to` to be carried.
  - This is D-SR.2 superseding the earlier "keeps only `known_at`" clauses. It is not a regression. Their register rows stay closed, with a note naming D-SR.2/D-SR.73.
- **R350 confirmed right.** The verification link carries `from`/`to` for onward navigation only. The Action/verification record read stays on its own period, with no re-cut by the range (as D-SR.64). Where the page shows the range, it declares "Range not used · this record's own period". One pin: the record body is the same with and without `from`/`to`.

Decisions logged for owner review: **D-SR.73**.

