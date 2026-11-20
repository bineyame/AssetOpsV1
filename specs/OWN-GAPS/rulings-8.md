## D-SR.74 Lane G: SR-12b Q1-Q3 and WARM-1 gate refusals (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Source: `AssetOpsV1-sr4` `task/SR-12-warm-routes`, `.agent/SR-12b-packet.md` (f978798bb) and `.agent/WARM-1-packet.md`.

### Q1: the ranged copy. Confirmed, with one correction.
- "Meets" is system vocabulary, and "those in the selected date range" is wrong for a window that only overlaps the range.
- Statement: "...the coverage of its active assessments that overlap the selected date range."
- Scope: "Only assessments that overlap the selected date range are counted. Whether each required input has a usable record is checked against all of this site's accepted records. It is not a rating of the site's health and not permission to act."
- The unranged words are unchanged.

### Q2: the edge. Corrected: half-open, as everywhere else (D-SR.9 windows, the 0029 hour rule, D-SR.71).
- `analytics/declaration.py` `in_window`, for a stated `assessed_window` `[start, end)`: count it when `start < hi and end > lo`. A window ending exactly at `from` belongs to the period before and is **not** counted.
  - A zero-length window counts when `lo <= start < hi`.
- The running-bounds fallback (`first_running_observed` / `last_running_observed`) is a pair of observed instants, so it stays closed: `first < hi and last >= lo`. An observation at `from` is inside the range.
- Pin the four edges: end = from (out), start = to (out), an instant at from (in), last observed = from (in).

### Q3: SR-12b closes as built, plus one copy fix. It is not deferred.
- The change is small, correct and tested for every Site the file-backed declaration serves. Merging it costs nothing.
- **The refusal as shown is not honest enough for a client page.**
  - On an imported Site, `/analytics` answers 409 `AWAITING_EVIDENCE_MIGRATION`. `evidenceRead` makes that `unavailable` and carries the server message, and `CapabilityReadiness` `Unavailable` prints it.
  - Read from code; confirm it on the live page. The demo Evidence page would then say "legacy file-backed surface is awaiting evidence migration" about a Site whose evidence is migrated. That breaks the D-SR.67 gate (no "Awaiting evidence migration" panel on a client-visible page) and the plain-language rule.
- **Fix (about 0.05, lane G, before merge).**
  - In `frontend/src/sites/CapabilityReadiness.tsx` (`served` / `Unavailable`): when `awaitingMigration(declaration)` is true, show the fixed words "What can be assessed from these records is not available yet for this site." Never show the server message.
  - Add one vitest.
  - Live check: the Kobo and Kisiwa Evidence pages carry no "migration" or "legacy" word.

### WARM-1: 409 gate refusals and the Kisiwa nights read.
- **The plan stores only what can be stored.**
  - The warm planner sends `claim-limit-range` only for Sites whose Performance gate is open at plan time. It uses the route's own gate predicate, not a copy.
  - It lists the others in `warm-report.json` / `warm-verify.json` under `excluded_closed_gate: [{site, route}]`.
  - `--verify` replays the same plan, so the 100% hit gate is over stored requests only.
  - Any 409 on a request **in** the plan fails `--verify`. Nothing passes silently.
- **A closed gate on a demo Site is itself a prepare failure.** D-SR.67 runs `performance_migration` wherever the Site has that surface. On the final DB, a non-empty `excluded_closed_gate` stops the session check and goes to the Architect; the warm and verify do not hide it.
- **Kisiwa `/fuel-balance/nights` stays unstored for the demo** (D-WARM.2: measured, not gated).
  - It must still read in 2 s or less on the VPS verify run.
  - If it does not, report it. Storing it then needs a ruling; do not store it now.
- Size: about 0.05 (planner filter, report key, two tests).

Decisions logged for owner review: **D-SR.74**.

## D-SR.75 AP-1 analytics readiness port sized; database stays PostgreSQL (Architect, Claude, 2026-11-13, owner request, for the Sat 14 Nov 12:00 reassessment)

- Source: `.agent/owner-analytics-port-and-db-choice-2026-11-13.md`; detail `.agent/architect-analytics-port-and-db-choice-2026-11-13.html`.
- **AP-1** = `/api/sites/{id}/analytics` on stored mini-grid Sites (Kobo, Kisiwa): a `registry.ledger_scope` stored branch with the Performance gate; new `analytics/stored_declaration.py` (fail-closed role map, role presence query, dispatch-3.2 coverage adapter over `claim_limit_read.role_coverage`), feeding `score_readiness` unchanged; same JSON, no frontend change; cold/EV answer `analytics: []` (mock `cold-evidence`/`ev-evidence` carry no CapabilityReadiness).
- Siblings (`/dispatch`, `/findings`, `/assessments/...`, `/api/findings`) stay gated: stored Sites have their own Performance and Finding routes.
- Size about 1.3 units (1.1-1.6), after SR-12b. No data rebuild or migration. Kobo parity: per-requirement `available` must match; level differences classified (dispatch-2 vs 3.2). Kisiwa: fixture + live read.
- Deferral order: AP-1 enters D-SR.38's list **first** (ahead of DATA-10/13). Owner options: defer (recommended), build if a lane is free with the freeze moved to Sun 20:00, or promote over another candidate.
- Mock: `SITE_EVIDENCE.mini.caps` has five rows; the backend declares only Dispatch on every Site. That pre-existing gap is outside AP-1.
- Database: stay on PostgreSQL; no change before 17 Nov. Later: measure, then time partitions on readings, then a TimescaleDB trial on a clone. No document or wide-column store.

Decisions logged for owner review: **D-SR.75**.

## D-SR.76 Lane K SR-8/SR-10 page questions (Architect, Claude, 2026-11-14, owner-delegated, logged for owner review)

- Source: `AssetOpsV1-sr8` `task/SR-8-10-pages`, `.agent/SR-8-packet.md`, `.agent/SR-10-packet.md`.
- **Q1 Yes.** Any shared range longer than one Site-local day opens the whole-range Renewable view, 2-5 days included (range in, range out). Exactly one Site-local day, for example a UTC Site's midnight-to-midnight range, keeps the one-day page. As built.
- **Q2 Keep the title "Usable headroom".** It is the mock's card title (`index.html:446` `metric('Usable headroom', ...)`). "Range across eligible hours" goes in the card's note, as built. That is what D-SR.48's "worded" means. No relabel.
- **Q3 Yes.** "Partial: n hours missing" (singular "1 hour") is the shared wording on the range row and the one-day page. For a day with no missing hours but limited hours, use "Partial: some hours have too few readings", not "some hours limited" ("limited" alone says nothing to a client).
- **Q4 Back link: yes, the same pattern as Fuel** ("Back to the whole range", only when the page was opened from the range). **No Opportunity detail link** in SR-8: it is a single record (D-SR.44 N) and new scope. Existing Finding links stay.
- **Q5 Acceptable for the demo**, because the walkthrough clicks from the range. Backlog (not demo-critical): derive the back link from the shared range already in the URL.
- **Q6 No total card now.** It is not in 10b.2's page list, and a sum over partial days needs an "n of m days" qualifier and a ruling. The per-day modelled bands stay. Backlog.
- Size: Q3 copy and Q4 back link, about 0.05 together, lane K.

Decisions logged for owner review: **D-SR.76**.

### D-SR.76 (continued) Lane I SR-12a Q7-Q9 (`AssetOpsV1-sr6` `task/SR-6-12a-pages`, `.agent/SR-12a-packet.md`)
- **Q7 Confirmed: nothing to filter.** `/evidence/rejections` has no recompute-job list (its lists are rejections, conflicts and duplicates). The spec line in 10b.4 is an error and is withdrawn. No other list was meant.
- **Q8 Source time is right. Align the list to it.** Range means telemetry (D-SR.39), so "rejections in this range" means readings describing this period that were not accepted. That matches the overview count line (S2 Q19).
  - Postgres and file-backed lists, conflicts and duplicates filter on the reading's source time in `[from, to)`. `total` follows the same rule, so the line and the list agree at the edges.
  - A rejection with no source time is placed by its batch receipt time in `[from, to)`, on **both** sides: the list and the count line's untimed note. Its row says "no reading time; received in this date range".
  - Heading: "Readings not accepted (from this date range)". Empty line: "No reading from this date range was refused or repeated."
  - Tests: pin the edges on both sides (source time = `to` is out, = `from` is in) and an untimed row received inside the range. Add one line-equals-list check on the Postgres fixture. Size about 0.1, lane I, before merge.
- **Q9 Confirmed.** The file-backed path is filtered too, by the Q8 rule (source time; receipt only when there is no source time). The page must not list all dates beside a range.

Decisions logged for owner review: **D-SR.76** (Q1-Q9).

### D-SR.76 (continued) Lane J SR-7/SR-11 Q10-Q11 and the hour addresses (`AssetOpsV1-sr7` `task/SR-7-11-pages`)
- **Q10 (Q-J6) Confirmed as built.** The table has only the fields the stored day rows carry: When, Outcome for service, Recovery, Result. A step column with "No accepted record" in every row would be false.
  - 10b.3's "existing backup chain table" line is withdrawn. Record this table under MOCK DEVIATION R728 (stored day rows carry no step records; alternatives: the step table, rejected as dishonest, or new step rows, out of scope).
  - Each row's one-day link keeps the full step chain.
- **Q11 (Q-J7) Confirmed.** A 503 on the one-day claim-limit read keeps its existing plain sentence with no retry.
  - **Hide** the claim-limit section on Cold/EV Evidence pages instead of showing "...read for mini-grid sites only". The mock's `cold-evidence`/`ev-evidence` carry no claim-limit section (`SiteEvidenceMatrix`, `AcceptedEvidenceIndex`), so hiding it keeps the mock.
  - The not-applicable string stays only as a guard for an unexpected 404. Size about 0.05, one vitest.
- **Hour addresses: confirmed.** Only an address that is exactly one clock hour opens the hour page. Any other address, including one hour off the clock hour or two hours, is a range and opens the day table. Never a refusal.
  - The frame must say "Whole days that include the selected time" so a short range is not read as a full-day claim. This supersedes D-SR.40's interim "two hours reads the 12:00 hour" test; update that test to the new behaviour, never delete it.

Decisions logged for owner review: **D-SR.76** (Q1-Q11 and the hour addresses).

## D-SR.77 Lane H SR-5 questions; AP-1 size corrected (Architect, Claude, 2026-11-14, owner-delegated, logged for owner review)

- Source: `AssetOpsV1-sr5` `task/SR-5-pages`, `.agent/SR-5-packet.md` (deviations 2-4).
- **1 Confirmed.** A 404 from `range-overview` keeps the one-day page, a safe reading. The bar declares the one day it shows, never the range. Only a 404 falls back. A 503 or 422 keeps its own refusal; it never falls back.
- **2 Declare before the read.** The page's period comes from the page type, not from the data. Opportunity, Action, Verification and fuel Finding pages declare "Range not used · this record's own period" (D-SR.64 words) from the first render, also when every read is refused. Drop `declaresOnLoad`. About 0.05.
- **3 Not as the only check.** The real answer on an imported mini Site is 409 `AWAITING_EVIDENCE_MIGRATION`, and `SitePerformance.tsx:130` then takes the stored Dispatch reads.
  - The matrix fixture must give `/analytics` that 409, so the row checks the stored path's D/R class (R once SR-5c lands).
  - Keep `blockedBy` only for a legacy-fixture row, if any.
- **4 Confirmed R.** D-SR.66 corrects D-SR.44: the view declares what the same Site's Financials declares.
- **AP-1 correction (D-SR.75).** `SitePerformance.tsx` and the other `/analytics` readers (`SiteAnalyticsFrames`, `FindingsIndexes`, `FindingDetail`, `SiteEvidenceFrame`) use the 409 as the "imported Site" signal. AP-1 must switch them to branch on the Site's store before its 200 ships. +0.25, so AP-1 is about 1.55 (1.3-1.9). The HTML was corrected in the same commit. The deferral place is unchanged.

Decisions logged for owner review: **D-SR.77**.

## D-UQFI.6-10 UQ-FI builder questions (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Source: `AssetOpsV1-uqfi` `task/UQ-FI-1-2`, `.agent/UQ-FI-packet.md` (questions 1-4 and the merge note). Spec: rev 6 (6.1-6.4, D-UQFI.1-5) in `architect-sequence-client-scope-2026-11-11.md`; owner go `owner-proceed-waiting-items-2026-11-13.md` (provisional).
- **D-UQFI.6 Cold board: the panel rule wins; no collapse there.**
  - Rev 6's "no layout restructure, no panel moves" and the mock-fidelity rule outrank the Cold board example in D-UQFI.4. That example was a factual error: the six "No cold assessment for this window" lines sit in six separate v6.9 `Panel`s (`coldSiteViews.tsx` what-happened, temperature, needs attention, what we can conclude, sources, most useful next evidence), not in blocks of one section.
  - Shown: all six panels stay, each with its heading and its own one `Gap` line "No cold assessment for this window", with its id unchanged. A one-subject group renders as today, so no `GapGroup` is needed there. No banner, no new words, no `details` element.
  - The v7.2 sheet's EmptyState with "Not shown yet, and why" is not in the 6.2 approved list. It is a stage-1 (BL-69) component, after 17 Nov, and needs its own ruling then.
  - Remove the Cold board from the collapse targets. The packet's collapse list says "Cold board: none (D-UQFI.6)". `measure.json` records its gap-line count, which stays the same before and after.
- **D-UQFI.7 Figures: 20 px confirmed for UQ-FI-1/2; 30 px is UQ-FI-3's, on its card only.**
  - Today's figure classes (`.v69-metric__value`, `.v69-money`, `.v69-panel-value`, `.window-money__amount`, Portfolio `.value-number`, `.opportunity-quantity`) use `--font-size-600` (20). The D-UQFI.4 headline rule stands for them, and a smaller figure cannot break a fit (risk 1).
  - UQ-FI-1 defines `--text-figure: var(--font-size-800)` (30) as a token, used by nothing yet. UQ-FI-3 applies it to the one-figure Portfolio card only, the sheet element that carries it (sheet `.card .fig`, portfolio-hifi `.kpi .fig`/`.bigfig`). There it is the stated exception to "nothing at page-title size or larger".
  - The Site board's 30 px tiles (site-overview-hifi `.tile-k .fig`) are after 17 Nov (BL-69). If UQ-FI-3 is held, figures stay at 20 px. No MOCK DEVIATION label is needed: the sheet replaces the v6.9 type scale, and the 30 px element ships with its card.
- **D-UQFI.8 P3 headline: yes, build it only after SR-5 and SR-8 merge.**
  - The `SiteAnalyticsFrames.tsx` frame change (the h1 is the Finding title, then the first sentence, with the status strip under them) is made on a rebase onto main that has both. The `SiteFinding.tsx` side may be prepared now.
  - If either SR branch has not merged by Sat 15:00, P3's headline is held alone. UQ-FI merges without it, and the packet lists P3 headline as held. This is not a reason to hold UQ-FI whole.
- **D-UQFI.9 `primitives.css` spacing: no, not for 17 Nov.**
  - Rev 6 snaps the demo-path files only. `primitives.css` styles every page, and SR-8-10 is editing it now, so a whole-file snap means merge conflicts and uncaptured changes on non-demo pages.
  - Its type pass (done) stays, and so do the tabular-figure selectors. Spacing snap of `primitives.css` goes to BL-69 stage 1. The packet's "Known deviations" line stands as a ruling, not a deviation.
- **D-UQFI.10 Merge order: confirmed, with two additions.**
  - UQ-FI merges after the SR range pages (SR-5, SR-8-10 and any lane touching frontend CSS that is ACCEPTed by then), UQ-FI-1 then UQ-FI-2, by Sat 18:00 (rev 6.4). The rev 6 PR-3 rule stands: PR-3 first if ACCEPTed by 15:00.
  - Any branch merging after UQ-FI reruns `node tools/uqfi-type-codemod.mjs` (type pass) and `tools/checks/style-ratchet.mjs` and passes the ratchet. It uses `--spacing` only on the 14 demo-path files it touches, never on others.
  - UQ-FI, rebased onto the SR merges, reruns both itself and retakes the after captures of any P-page those branches changed.
- Accepted from the packet, no change: the GapGroup line is a `div` (inline form `span`), because `<ul>` cannot sit inside `<p>`. The page title is 20 px below 760 px.

Decisions logged for owner review: **D-UQFI.6-10**.

## D-SR.78 AP-1 builder questions (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Source: `AssetOpsV1-ap1` `task/AP-1-analytics-port`, `.agent/AP-1-packet.md` (questions 1-4). Design: `architect-analytics-port-and-db-choice-2026-11-13.html` Part A; D-SR.75, D-SR.77.
- **Q1 Acceptable as built; no count.**
  - Design A3 asks only for presence (EXISTS, latest), not a count. A count over the whole Kobo ledger adds read cost against the 2 s budget and adds nothing to readiness.
  - "Usable records received, latest …" is true when a latest GOOD accepted reading exists. With no such reading, the row stays not available with its gap words.
  - The TS type stays `number | null`. The file path keeps its count. Never show 0 or a dash for null.
- **Q2 Show "Not bound", not the file-era ids.**
  - A file-era device/signal id beside an unbound role names a reference that the stored configuration does not have, which is a false source.
  - On the stored path, a row's `device_id`/`signal_id` are filled only from a stored binding, and are null otherwise.
  - `CapabilityReadiness`/`SiteEvidence` render "Not bound" (the existing `FoundationBindingsPanel` word for `UNBOUND`) where the reference sits, for an unbound role. Policy rows and not-stored rows with null ids show no reference; their gap words stay. Availability stays false.
  - The file path is unchanged. Tests: one backend test (unbound role gives null ids) and one vitest test ("Not bound" shown, no file-era id in the DOM). Size about 0.1, before merge.
- **Q3 Confirmed: a whole-read 422, fail closed.**
  - This matches `claim_limit_read.SUPPORTED_MODELS`, which refuses the same revision in the claim-limit section on the same page. Skipping would let the panel and that section disagree (design risk "Panel disagrees with the claim-limit section").
  - The page shows its existing refusal sentence, with no retry.
  - The Kobo parity probe records whether any demo Site's selected revisions trip it. If one does, that is a finding for the coordinator, not a reason to skip.
- **Q4 Confirmed.** A closed gate returns the existing 409 `AWAITING_EVIDENCE_MIGRATION`, so SR-12b's "not available yet" line applies unchanged. No new code, and no `PERFORMANCE_CUTOVER_CLOSED`. The gate reason stays in the message for logs; the page does not render it as raw text. D-SR.77's store branch is unchanged: the 409 is the imported-Site signal only when the store is unstated.

Decisions logged for owner review: **D-SR.78**.

## D-UP.12 UP-1 review L2: a stale FAILED job must not pin "Not analysed" (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Source: `AssetOpsV1-up1` `.agent/UP-1-review.md` L2; code `reading_upload/adapters/postgres_reading_upload_store.py` `_ANALYSIS` and `progress`. This refines D-UP.3; it does not replace it.
- **Yes: a later successful run supersedes a FAILED job for the same period.** The proof in D-UP.3 is the run itself. A run whose `knowledge_cutoff` is at or after the upload's decision time has read the upload, whatever failed before or beside it.
- **State order at GET:** Still processing > Analysed > Not analysed > Still processing (fallback).
  1. **Still processing** if any `recompute_job` for the Site, in any domain, overlapping [first interval start, last interval end) is PENDING or LEASED. This is unchanged: D-UP.3's "no work is left" holds.
  2. **Analysed** if the qualifying run exists (D-UP.3 item 2, unchanged).
     - It is an `analytic_run` for the Site with `analytic_id = dispatch_v3.ANALYTIC_ID`, `selection = 'DEFAULT'` and `job_id IS NOT NULL`, its window covers the first interval start, and its `knowledge_cutoff` ≥ `decided`.
     - `decided` = max `ingestion_disposition.decided_at` over the upload's ACCEPTED dispositions.
     - No FAILED job overrides it.
  3. **Not analysed** only if no qualifying run exists and a **relevant** FAILED job overlaps the span.
     - A FAILED job is relevant when `created_at ≥ decided`, or `lease_until ≥ decided` when that column is set. Either way it was created or still leased after the upload was decided, so it could have carried the upload.
     - Jobs coalesce, so `created_at` alone would miss an older job that was widened to take the upload. Never key on `cause_evidence_id` (D-UP.3).
     - A FAILED job created and last leased before `decided` is ignored.
  4. Otherwise **Still processing**. This is the existing state when no run and no relevant failure exist.
- **What is compared:** each FAILED job's `created_at`/`lease_until` with the upload's `decided` time (the same database clock, S4-07). The run is compared with `decided` through `knowledge_cutoff`. A job is never compared with a run.
- **Wording is right, unchanged:** `reading_upload.state.not_analysed` "Received, but the analysis did not finish. The readings are kept." It is now shown only for a relevant failure, where it is true.
- **Tests, no-DB fake store plus one Postgres flow case:**
  - an old FAILED job and a later qualifying run gives Analysed;
  - an old FAILED job (created and leased before `decided`) and no run gives Still processing;
  - a FAILED job created after `decided` and no run gives Not analysed;
  - an older job with `lease_until ≥ decided` that is FAILED, and no run, gives Not analysed;
  - PENDING beside a qualifying run gives Still processing.
- Size about 0.1, before merge. Also run the review's `SELECT status, count(*) FROM recompute_job` check for KOBO-001 on the client4 copy in the first heavy slot, as planned.

Decisions logged for owner review: **D-UP.12**.

## D-UQFI.11-12 UQ-FI-3 builder questions (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Source: `AssetOpsV1-uqfi3` `task/UQ-FI-3`, `.agent/UQ-FI-3-packet.md` (questions 1-2). Spec: rev 7 UQ-FI-3 row and its `StatusPill` line ("maps the six existing state codes").
- **D-UQFI.11 State set: the outcome state codes, as built. Looks for the undrawn ones are below.**
  - Rev 7's "six reading states" was loose wording. Its own design line says "the six existing state codes", and the codes both call sites show are the outcome states (Portfolio key, board outcome rows). The eight readings-coverage words on the sheet are not shown at either call site, so they are not mapped in UQ-FI-3. Confirmed as built, including NO_OBJECTIVE and NOT_APPLICABLE, which the board can carry.
  - Drawn in portfolio-hifi, kept exactly, with no added symbol: NEEDS_ATTENTION `s-partial` look; OPPORTUNITY `s-accent`; WATCH `s-neutral`; NOT_MEASURED `s-notanalysed` (dashed).
  - Not drawn, ruled:
    - **ON_TRACK** takes the sheet's Complete chip look and symbol (`s-complete`, filled circle). It is the one positive state, and that is the sheet's positive look.
    - **UNKNOWN**, **NO_OBJECTIVE** and **NOT_APPLICABLE** take `s-neutral` with no symbol. The word tells them apart.
  - Reasons:
    - Do not use `s-noreadings` for Unknown. That look means "No readings received", a readings fact the outcome state does not claim.
    - Do not use the dashed `s-notanalysed` for N/A. Dashed means "not yet", and not applicable is not pending.
    - Unrecognised codes stay neutral.
  - The packet lists these four as "undrawn on the sheet, ruled by D-UQFI.11", for the owner's sheet review. `statusPill.test.tsx` pins them.
- **D-UQFI.12 Portfolio card foot pill: leave it out for 17 Nov. MOCK DEVIATION.**
  - Mock element: the portfolio-hifi `.kpi` card foot state chip.
  - Reason: `EstatePortfolioCard` carries a tone, not a state code. An estate-level state needs a server roll-up rule: which Site state wins, and with what words. That is new semantics needing an owner decision, not a field copy.
  - Alternatives considered:
    - Derive it in the client from the tone or the per-Site states. Rejected: it invents semantics, and colour would be read as a claim.
    - Add a server `state`/`state_label` with a roll-up rule. This is about 0.3 unit, backend, contract and tests. It goes to BL-69 after 17 Nov, and only once the owner rules the roll-up.
  - The per-Site states stay behind "Why?" as built, so nothing is hidden. Record the label in code beside the card foot and in the packet, citing D-UQFI.12.

Decisions logged for owner review: **D-UQFI.11-12**.

## D-SR.79 AP-1 review H1 and Lows: where the stored readiness table goes (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Source: `AssetOpsV1-ap1` `.agent/AP-1-review.md` (`ae4a34eaf`, REJECT on H1).
- The gap is in the design premise of D-SR.75 Part A1, which assumed `SiteEvidence` renders the panel for stored Sites. It is not a builder error. The backend stands as reviewed.
- **(a) Placement: the ledger Overview's existing "What we can conclude now" panel.**
  - Mock: v69 `siteEvidenceScreen('mini')`, `panel('What we can conclude now', table([...], SITE_EVIDENCE.mini.caps))`. `LedgerSiteEvidence` `OverviewBody` already renders that panel (`site-evidence-state-heading`).
  - How:
    - `SiteEvidence.tsx` passes `declaration={loaded.declaration}` and `profile={profile}` to `LedgerSiteEvidence`, which hands them to `OverviewBody`.
    - When `capabilityTableShown(declaration, profile)` is true, `CapabilityReadinessTable` renders **in place of** the `NotAvailableYet name="capability-conclusions"` line, the honest placeholder for exactly this table. Everything else in the panel stays as it is.
    - In that case only, the status bar badge "No capability conclusion yet" becomes "Evidence · Overview", the Analysis view's existing badge form, because the old words would be false. Otherwise both stay unchanged.
    - On any non-200 (409 closed gate, 422, 503) or `analytics: []` (cold/EV), the existing `NotAvailableYet` line and badge stay. No other words are added.
  - Analysis view: no change. Its "How each limit is set" panel already shows the stored claim-limit section from the same revisions. Adding `CapabilityReadinessAnalysis` would duplicate it.
  - The other four mock rows stay the pre-existing gap recorded in D-SR.75, outside AP-1.
- **(b) No skip.** The fix makes the read displayed, so there is nothing to skip. H1 and this fix land together, and main keeps the cheap 409 until then.
  - The page still waits for all three reads (`Promise.all`), so the parity probe's unwarmed timing now gates the Evidence page. If the read takes over 2 s, it gets one warm entry before merge (D-SR.75 pass rule). Do not restructure the effect for 17 Nov.
- **(c) Size and what the client sees.**
  - The fix round is about +0.25: prop pass-through, the swap and badge, the vitest and the Lows. AP-1 becomes about 1.8 units (1.55 + 0.25). Its deferral place is unchanged.
  - 17 Nov, Kobo and Kisiwa (stored mini-grids), with the Performance gate open and a selected dispatch-3.2 revision in the period: one row in "What we can conclude now", the Dispatch requirement with Full, Limited or None and what is missing, in the existing table form.
  - With the gate closed, the read refused, or no revision: today's "Not available yet" line.
  - The probe's Kobo result and the Kisiwa live read decide which of the two the client sees. Cold room and EV hub are unchanged.
- **Test: the ledger shape.**
  - Replace the impossible fixture in `ap1StoredAnalytics.test.tsx` with `LedgerEvidence` (store `POSTGRES`) through `SiteEvidence`.
  - A stored 200 gives the table inside `site-evidence-state-heading`, no `capability-conclusions` line, and the badge "Evidence · Overview".
  - A 409 gives the line and "No capability conclusion yet".
  - A 422 gives the line, with no revision UUID or model id in the DOM.
  - Cold `analytics: []` gives the line.
- **(d) Lows, all fixed in this round.**
  - **L1:** `stored_site_declaration` raises a dedicated `StoredSiteNotFound` when `site_type_on` is None. The route catches only that for 404 `SITE_NOT_FOUND`; any `KeyError`/`IndexError` stays a 500. One test.
  - **L2:** resolved by (a). The ledger page never renders a refusal message; the UUID message stays for logs. The file path is unchanged, because 422 comes only from the stored branch.
  - **L3:**
    - The probe uses `build_assessment_store(persistent=False)` and writes nothing under `var/`.
    - `available` is compared by role, and by feeder for Load. Id differences, including D-SR.78 null ids, are listed separately and are not a mismatch.
    - `UnsupportedModel` is caught and emitted as `{"refused": "UNSUPPORTED_RULE_VERSION", "revision": …, "model": …}` (D-SR.78 Q3). The pass rule becomes: role-keyed `available_mismatch` empty.
  - **N1:** "(Not bound)" replaces the whole "(reference …)" suffix. D-SR.78 Q2 is amended to this wording.
- Re-review by a fresh Claude reviewer on the fix-round diff, plus the probe JSON once the DB slot runs.

Decisions logged for owner review: **D-SR.79**.

## D-MB.1-2 MB-1 packet questions (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Source: `AssetOpsV1-mb1` `task/MB-1-modbus`, `.agent/MB-1-packet.md` (questions 2 and 4). Spec: rev 7 section 7.6 / D-17N.6, D-UP.2.
- **D-MB.1 (Q2) Acceptable: the live window comes from the prolonged dispatch scenario, generated in memory.**
  - The beat's claim is "a field device's readings arrive live through the gateway and are accepted". It is not "the live readings continue the uploaded file". UP-1's file and MB-1's window are separate periods, and the overlap rule plus `live-field check` prove no reading is doubled.
  - A step in battery charge or feeder levels where the file ends and the live window starts is what the two sources recorded. Do not smooth, seed or splice it; that would fabricate continuity.
  - The demo script and presenter notes must not say or imply continuity. The live beat is described as a simulated field device (illustrative values), as rev 7 7.6 states.
  - Seeding the scenario from the file's last values is out of scope for 17 Nov. It goes to the backlog if the owner asks.
- **D-MB.2 (Q4) No delivery loop; keep the gateway's 60 s backstop.**
  - The backstop is the product's real delivery behaviour. A per-instant `deliver` loop would demo a path the field gateway does not run, and it adds scope and VPS load.
  - The script line reads "readings arrive within about two minutes", with the presenter waiting on the Kobo board's "today".
  - The demo-copy bench run records the time from the emulator's source time to its first appearance on the board. If that exceeds 3 min, report it to the coordinator; do not add a loop.

Decisions logged for owner review: **D-MB.1-2**.

## D-UQFI.13-18 UQ-FI-2 session-2 questions (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Source: `AssetOpsV1-uqfi` `task/UQ-FI-1-2`, `.agent/UQ-FI-packet.md` (session 2, questions 1-6). Main is at b514c02c1, with every range page merged, including SR-8, so D-UQFI.8's hold on P3 is lifted. These rulings correct rev 6's 6.1 page table where it named text the pages do not have. The rev 6 rule stands: existing text moved first, nothing new.
- **D-UQFI.13 (P5) Keep the page's own title, "Productive-use headroom at {site}", as the h1.**
  - "Daytime solar unused at Kobo mini-grid" belongs to the estate opportunities read. Adding that read to the opportunity page would be a new read and new words on the page, which rev 6 excludes.
  - The 6.1 P5 row now reads "the page's own title".
- **D-UQFI.14 (P2) The h1 is the Site name; the subtitle stays as it is.**
  - "The board's day line" referred to no existing element; it is withdrawn. Do not add or move any date text into the header.
- **D-UQFI.15 (P6) Keep the h1 "Findings".** The All-lens panel keeps its title "Findings across the estate".
  - Moving it would strip a v69 panel heading (a mock element) and make the h1 change by lens.
  - The 6.1 P6 row now reads "Findings" / the Site Findings title.
- **D-UQFI.16 (P7) Keep the Site name as the h1** on Fuel and Service, as the v69 Site heading. The tab names the page. The 6.1 P7 row now reads "the page's h1 as today".
- **D-UQFI.17 (P1) No Portfolio card collapse for 17 Nov, in either lane.**
  - UQ-FI-3 (D-UQFI.11-12) already moves the card's qualifiers and per-Site lines behind "Why?", so the card face has no repeated gap lines left to group.
  - Grouping inside "Why?" is not needed for 17 Nov. It can be revisited after the owner's sheet review.
  - UQ-FI-2 does not touch the card. Its P1 test asserts only the one h1.
- **D-UQFI.18 (P3) Remove the body copy: it is a move.**
  - Once the Finding's first sentence sits under the title in the header, `LifecycleSentence` must not repeat that sentence in the body on any version, so the fact is said once (D-UQFI.4: moved, nothing removed).
  - If `LifecycleSentence` carries any words beyond that one sentence (for example the "earlier version n of m" wording), those words stay where they are.
  - The P3 test asserts that the sentence appears exactly once, and that the page's gap-id and gap-fact set is unchanged, on a SUPPORTED version and a non-SUPPORTED one.
  - Wire P3 now on a rebase onto b514c02c1, then rerun the codemod and ratchet (D-UQFI.10).

Decisions logged for owner review: **D-UQFI.13-18**.

## D-SR.80 AP-1 parity: what replaces it, the Kisiwa 409, merge timing (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Source: `AssetOpsV1-ap1` `task/AP-1-analytics-port` (c03a8eeb2, re-review ACCEPT), `.agent/AP-1-parity.md`/`.json`. Rulings D-SR.67, D-SR.75, D-SR.78, D-SR.79; owner 2026-11-13 (`owner-clean-walkthrough-over-time-2026-11-13.md`); D-SR.9.
- **Q1 The clone parity is not met and cannot be met. A live consistency check on walk1113 replaces it.**
  - On a migrated DB the legacy Kobo readings live only in PostgreSQL, so the file side is empty (NONE, 0 intervals). All 10 mismatches are "record in one store only". A file-vs-stored parity has no baseline on any migrated tree. It is withdrawn as an AP-1 gate, and it is not a defect.
  - **Replacement (the AP-1 merge gate).** Run it after the walk1113 build passes its self-check. Use AP-1 HEAD code over the walk1113 DB and the build tree's store roots, served as the walkthrough serves, with the scheduler off. The check is read-only HTTP; no DB writes.
    - For KOBO-001 and KISIWA-001, on every story day that has a selected dispatch-3.2 revision:
      - `/analytics` returns 200, never 409/422/503;
      - the panel's not-available role set (Load per feeder) equals the claim-limit section's `missing_role` gap set (`claim_limit_on` -> `reduce_day`) for the same day and revisions, with no role available where the section names a gap;
      - the Evidence page shows `CapabilityReadinessTable` in "What we can conclude now", not the `capability-conclusions` line (D-SR.9).
    - Cold room and EV hub: `analytics: []`, with the existing line.
    - The first unwarmed read of each Site is under 2 s.
    - No Site shows "Awaiting evidence migration" (D-SR.67 gate).
  - **Pass rule:** every item holds on every listed day. Any miss holds AP-1 and comes to the Architect; it is not accepted as ruled. AP-1's fixture test (panel gaps equal claim-limit gaps) stays, but it is not a substitute for this check.
- **Q2 The Kisiwa 409 is an artefact of the clone, not a defect, and not AP-1's.**
  - `permits_cutover` binds each report to `environment_identity`, which is the DB host, port and name, and to `store_root`. The clone's DB name differs from the one the report was made on, so every Site is closed by design, Kobo included, as the probe saw.
  - Separately, vps1 never ran the comparison for Kisiwa; that is the D-SR.67 prepare gap. `tools/demo_combined.py` on main now runs it for every imported story Site.
  - On walk1113, served from its own build tree, the gate is open. If Kisiwa still returns 409 there, it is a prepare failure (D-SR.67), not an AP-1 change. No code fix.
- **Q3 Merge AP-1 before the walkthrough, gated on the Q1 check.**
  - AP-1 adds no migration, so walk1113 needs no rebuild; only the serve restarts on the merged code.
  - The owner then walks what 17 Nov shows.
  - If the check fails, hold AP-1. Main keeps the honest "Not available yet" line, and the walkthrough does not wait for AP-1.

Decisions logged for owner review: **D-SR.80**.

## D-SR.81 CO-10 "16 min unknown": a reported charging state is known in-service time (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Sources: `AssetOpsV1-co10/.agent/CO-10-fix-packet.md`; `backend/assetops_backend/analytics/ev_availability.py:29-31`; `.agent/W5-03-build-spec.md:19`; mock `frontend/mockups/v69/index.html:587-591` (availability screen); owner 2026-11-13 (`owner-clean-walkthrough-over-time-2026-11-13.md`). Supersedes the data fix in D-ANY.6b / D-E5.49a (its premise was wrong: EV-HB emits c1 every minute, 08:00 AUTHORIZING, 08:01-08:15 CHARGING, 08:16 FAULTED). The D-E5.49 pin (0 min unknown) stands.
- **Ruling: option 1, a product correction.** Option 2 rejected: it would rewrite a true story (a session starting at 08:00) to hide a classification defect, and every other session minute on every EV day would still read "unknown". Option 3 is forbidden.
- **Why.** "Unknown" means "No trustworthy state coverage" (mock :589) and drives the client sentence "N min of connector status is missing". A trustworthy CHARGING report is coverage, so today's screens say status is missing when it was received: a false statement on every EV day with a session. The product's own definition of "Known available" is "State-supported service time" (mock :589), and the mock's Connector 1 is 100 % Available across a day of sessions (mock :590). OCPP StatusNotification treats Preparing/Charging/SuspendedEV/SuspendedEVSE/Finishing/Reserved as operative and only Unavailable/Faulted as inoperative; uptime rules for public chargers count charging time as up. W5-03 spec :19 ("a charging state alone does not prove that the connector was available for a new session") measured "free for a new session", which is not what any screen labels or the mock shows; that sentence is superseded. Sessions, faults or the schedule alone still never fill the numerator; only a reported state does.
- **Exact mapping (`CATEGORY`, ev_availability.py).** The closed vocabulary is `sites/binding_roles.EV_CONNECTOR_STATES` (seven values); nothing else reaches the classifier.
  - AVAILABLE (in service): `AVAILABLE`, `UNPLUGGED` (idle), `PLUGGED`, `AUTHORIZING`, `CHARGING` (occupied, operating). OCPP equivalents if the vocabulary is ever widened: Available; Preparing, Finishing, SuspendedEV, SuspendedEVSE, Reserved, Occupied -> AVAILABLE.
  - UNAVAILABLE (out of service): `FAULTED`, `DISABLED`. OCPP Faulted, Unavailable.
  - UNKNOWN: any other value, an unusable or conflicting report, gaps, cadence-expired time. Unchanged.
  - No fourth "Occupied" category: the mock has three states and three legend badges; adding one would change the DTO, legend and cards.
- **Fix (Sonnet, about 0.2 unit, branch `task/CO-10-availability-mapping`).**
  1. `CATEGORY` as above; rewrite the comment at :28-30 to cite D-SR.81. Bump `CALCULATION_VERSION` to `ev-availability/2` (the numbers change meaning) and the module docstring; `frontend/src/sites/evDepthClient.ts:79,284` and the `EvAvailability.tsx:5` comment accept exactly `/2`; update test literals that name `/1`.
  2. Tests that must change, only where a PLUGGED/AUTHORIZING/CHARGING interval moves Unknown -> Available: `test_w503_ev_availability_postgres.py:91-110` (CHARGING at 08:30 now classifies 08:30-08:31 Available: available 180 s, unknown 3600-240, a fifth span, ratios recomputed; replace the "CHARGING proves nothing" comment); `test_evhb_ev_window.py:156-158` (assert the full seven-value map). Add one pure test: a minute-by-minute AUTHORIZING -> CHARGING -> FAULTED day classifies 08:00-08:16 Available and 08:16-16:00 Unavailable with 0 unknown (the CO-10 shape).
  3. Must NOT change: `REPORTED_STATES`, `status_spans`, `grading.status_known_spans` and every `test_pb3_ev_status_grading.py` assertion (the `charging_kwh` measure grades on `connector_status_known` via REPORTED_STATES, `config/chain/coverage-policy-v1.json:5`, so chain snapshot rows are unaffected); `test_out_b3_cold_ev.py`, `test_out_c4_mini_ev.py`, `test_out_c_rules.py` (synthetic bodies, text rule only); `test_data4_charger_use.py`; the frontend "session-only selection never proves availability" test; the CO-10 row in `tools/demo_combined_finish.py:422-431` (it now passes as written). Any other test or self-check row that changes is a defect: stop and report.
  4. Correct the stale "16 min unknown" lines in `.agent/demo-script-thursday-client7.md` (historical script; add a one-line D-SR.81 note rather than rewriting it).
- **Client-visible effect.** Changes only availability-derived figures, and only on days with a session: Availability page (Known available up, Unknown down, Known-time availability and the two bounds, green bar over session minutes); EV board "Connector availability" contributor and Assure "... of connector status is missing" subline (session minutes no longer counted as missing); the CONNECTOR_OUT_OF_SERVICE warning ("7 h 44 min out on 10 Nov", no unknown part) wherever it is shown, Portfolio attention rows included; the Evidence page status-gap span. Unchanged: DATA-4 "3% of declared charging capacity" (uses `scheduled_seconds` and kWh, not the classification), sessions, kWh, money (9.00/4.50 USD), Findings, Actions, threads, chain grades, Portfolio money and counts.
- **No re-prepare.** Availability is computed at read time from accepted rows. No period-row kind is EV (`config/chain/event-register-v1.yaml`: all kinds are MINIGRID or money/evidence and none reads `ev_availability`). Stored route responses (`chain_response`) key on `code_version`, which hashes every backend source file, so they are invalidated automatically. On walk1113: fast-forward the build tree to the merged commit, rebuild the frontend bundle, restart the serve, rerun the prebuild and `tools/warm_ranges.py`, then rerun the full self-check (pass = 54/54, no "accepted as ruled") and the parity. Merge gate: fresh Claude review ACCEPT plus the tests above; no full suite (test-suite policy).

Decisions logged for owner review: **D-SR.81** (a product-definition change to every EV availability figure; the owner may overrule to option 2).

## D-SR.82 A range before the Site was imported reads its days, not 404 (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Sources: `outcome_api.py:259-260`, `source_health_api.py:147-148`, `claim_limit_api.py:158-159`; builders `estate/site_range.py:98-110`, `sites/site_health_range.py:81-91`, `estate/claim_limit_range.py:57-66`; `estate/index.py:310-346` (`_scope`); `postgres_estate_read.py:120-128`; GETs on the walk1113 serve (8990, read only). Owner rules: range output on every page for every Site type; missing data stated, not hidden; clean DB over time.
- **Root cause (corrects the finding).** The trigger is the Site's import time, not its first reading. All three builders admit the Site through `service._scope`, whose `imported_sites(t, req.to)` keeps a Site only when `site_import.imported_at < to`. walk1113: KISIWA imported 2026-10-31 09:00, KOBO 2026-10-13 10:00, COLD/EV 2026-10-16. So Kisiwa 24-31 Oct is 404, but Kobo 7-14 Oct (before its first reading, after its import) is already 200 with NO_READINGS days.
- **Q1: what to return.** 200 with the existing body (`site-range-overview-1`, `site-health-range-1`, `site-claim-limit-range-1`) and no new DTO. Every day reads exactly what a pre-data day reads today: NO_READINGS on the overview and health, NO_SELECTION on the claim limit. Checked live: the partial-overlap range Kisiwa 28 Oct to 4 Nov is 200 on all three. The days 28 Oct to 1 Nov, three of them before the import, read NO_READINGS and NO_SELECTION, and 2-3 Nov are analysed. A wholly pre-import range is that same case with zero analysed days.
- **What each page shows (no frontend change).** The Overview renders its range form (the `Loaded` path), so the one-day fallback no longer fires: the date bar and body agree. The status and the day strip state the gap with the existing D-E5.46/D-SR.70 words ("7 days without a usable result"). Health shows "Readings on 0 of 7 days · 7 days with no readings". The claim limit shows 7 days without a selection. It no longer says "This site was not found."
- **Q2.** Kobo: the same bug for ranges ending at or before 13 Oct 10:00; ranges from then to its 14 Oct first reading already work. Cold/EV: not affected. `/cold/*` and `/ev/*` answered 200 with `currentness UNKNOWN` and a stated limitation for 6-13 Oct, before their import. The four other mini routes (service, renewable, fuel, backup) do not use `_scope` and already answer 200 (D-SR.70).
- **Q3: the fix (Sonnet, about 0.3 unit, branch `fix/SR82-preimport-range`, backend only).**
  1. `estate/range_days.py`: add `one_site_scope(service, snap, tenant_id, req, site_code) -> dict | None`. It calls `service._scope(snap, tenant_id, req, admit)`. If `scope["sites"]` is empty, it reads `snap.imported_sites(tenant_id, scope["k"])`, keeps the entry whose `site_code == site_code`, and returns `{**scope, "sites": [it], "ids": [str(it["site_id"])], "access_basis": access_basis(tenant_id, ids)}` (import `access_basis` from `estate.scope`, as `index.py` does). It returns None only when the Site was not imported by the cutoff k. Docstring cites D-SR.82: the one-Site range routes admit a Site imported by the cutoff, while the Portfolio's estate admission (`imported_at < to`) is unchanged.
  2. Replace the `service._scope(...)` call with `one_site_scope(...)` in `site_range_body`, `health_range_body` and `claim_limit_range_body`. Leave the `if not scope... return None` and the routes' 404 `SITE_NOT_FOUND` branches unchanged. Update the three docstrings ("None when the Site was not imported by the cutoff").
  3. Do not change `estate/index.py`, the adapters, the Portfolio, the routes, `warm_ranges.py` or any frontend file.
- **Tests.** Stubs: in each of `test_sr5_range_overview.py`, `test_sr6_health_range_route.py` and `test_sr7_claim_limit_range.py`, add one case where the fake `imported_sites` keeps the Site only for a bound later than `req.to`. Each case asserts 200 and that every day is NO_READINGS (claim limit: NO_SELECTION), with `days_requested == 7`. In the same files, add one case for an unknown code (overview: a Site never imported) that still asserts 404 `SITE_NOT_FOUND`. Postgres: in `test_sr5_range_overview_postgres.py`, add one case for a range wholly before the fixture's `site_import.imported_at`, asserting 200 with all days NO_READINGS. Run only the six files (test-suite policy).
- **Q4.** `tools/warm_ranges.py`: no change. Its 45 failures are this bug, and after the fix those targets answer 200 and store. A genuinely unknown Site still 404s at the route (`ref`/`site` resolution happens before the builder). A Site not yet imported at an explicit `known_at` also still 404s `SITE_NOT_FOUND`: at that cutoff the product did not know the Site. The Overview's one-day fallback stays right for that case and for `RANGE_OVERVIEW_NOT_APPLICABLE`.
- **Parity (D-SR.11).** For a pre-import range the Portfolio leaves the Site out, and the Site page shows no analysed day and no money, so no figure contradicts the Portfolio.
- **Merge gate and walk1113.** Fresh Claude review ACCEPT plus the six test files. Then fast-forward the walk1113 build tree, restart the serve and rerun `tools/warm_ranges.py`; pass = 0 failed. Then GET the three routes for Kisiwa 24-31 Oct and Kobo 6-13 Oct: all 200. No re-prepare and no DB write: the bodies are composed at read time, and stored responses key on `code_version`.

Decisions logged for owner review: **D-SR.82**.

## D-SR.83 Kisiwa/Kobo Overview and Finding-index reads become stored, prebuilt routes (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Sources: `site_overview/route.py:121-170`, `site_overview/read.py:128-241,398`, `scheduling/upstream.py:89-200`, `analytics/dispatch_read.py:136-183`, `analytics/finding_index.py:347-376`, `finding_index_api.py`, `evidence_api.py:393`, `estate_api.py:52-77`, `outcome_api.py:195-225` (the board's stored-route pattern), `chain/prebuild.py`, `tools/demo_combined.py:447-523,847`; walk1113 `api-8990.log`, `smoke-check.md`.
- **Q1: where the time goes.** The root cause of "slow when warm" is that `/overview`, `/finding-index` and `/api/estate/scope` are not CH-5c stored routes. They have no `perf.route` and no `StoredRoute`, so every GET recomposes and WARM-1 never warmed them. Because neither route has perf spans, the split below comes from reading the code, calibrated on the same-day Kisiwa board (`read.dispatch` 0.95-1.02 s per `dispatch_read.window`, `read.money_head` 0.69-0.87 s per consequence read).
  - Overview `read()`: two accepted-evidence fingerprints over a 36 h bracket; `upstream.window` (one `dispatch_read.window`, then `consequence_read.read` for every Finding in the bracket, plus match, jobs and schedule); a second `dispatch_read.window` for the same day; the context records page; `finding_detail` for each intersecting Finding; and `_money`. Kisiwa has several night Findings per bracket, which accounts for about 12.5 s. Kobo has fewer, at 3-4.7 s.
  - Finding index: one `dispatch_read.window` (about 1 s on Kisiwa) per day read. `discover` and `gap_days` also read edge-reach days, so even a one-day `limit=2` request reads several days (5.7-7.5 s).
  - `dispatch_read.window` is slow because `window_snapshot` re-derives the input basis from the day's accepted evidence on every call.
- **Q2: the fix (Sonnet, about 0.6 unit, branch `fix/SR83-stored-overview-index`, backend and tool only, no frontend). A targeted query fix is rejected before 17 Nov.** De-duplicating the dispatch read or the fingerprint touches the `SELECTION_MOVED`/`ACCEPTED_SOURCE_MOVED` fences, which is correctness-sensitive. Storing the response is proven machinery that the board already uses.
  1. `site_overview/route.py` `SiteOverviewRoute`: add `responses: Any = None` (wired in `main.py:445` from the same `responses` that `build_outcome_router` gets). In `serve`, after every refusal and after `day` is resolved (with `db_today()` when no date is given), wrap the `self.read.read(...)` compose in `responses.serve(StoredRoute("/api/sites/{site_id}/overview", tenant_id, {"site": site_id, "day": day, "pin": [fid, rid] or None}, sites=(site,), watermark_sites=(site,)), compose)`. Copy the board's pattern (`outcome_api.py:209-225`). The compose raises the same typed 404/503, so nothing that refuses is ever stored. In `evidence_api.py:394`, put the call under `perf.route(SITE_OVERVIEW_ROUTE, response)` with `finish(...)`. The legacy branch is unchanged.
  2. `finding_index_api.py`: add `responses=None` and wrap `index.read(...)` the same way, keyed on `{"site", "domain", "from", "to", "limit"}`. A request with a `cursor` is never stored (Q11, page 1 only). Add `perf.route`. Wire it in `main.py`.
  3. `estate_api.py:75-77`: `estate_scope` passes route `"/api/estate/scope"` to `serve(...)` under `perf.route`, as `estate_findings` already does.
  4. Spans for evidence after the demo: put `perf.timed` around `fingerprint`, `upstream.window`, `dispatch`, `context`, `money` and `finding_detail` in `read.py`, and around `dispatch.window` in `finding_index.py`. These are timing only and change no semantics.
  5. `tools/demo_combined.py` `prebuilt_routes`: for each `DATE_BOARD_SITES` Site (Kobo and Kisiwa), for every day the board gets, also add `overview.day:{site}:{d}` → `/api/sites/{code}/overview?date=d` and `index.day:{site}:{d}` → the one-day `finding-index?domain=mini-grid-dispatch&from=dT00:00:00Z&to=(d+1)T00:00:00Z&limit=2`. Each story `/sites/{code}/findings` link adds its `finding-index` range query, so the exact walk1113 smoke-check strings come out. Add `/api/estate/scope?{q}` beside each `estate/findings` request.
  6. `chain/prebuild.py` `run`: after a 200 `/overview` with a `known_finding`, also GET `/api/sites/{code}/outcome-board?date=d&finding_id=..&finding_revision_id=..`, the pinned board that the Overview page then opens (Kobo first hit today: 4.7-5.5 s).
- **Stop-and-ask guard.** Add the overview, finding-index and scope paths to `PATHS` in `tests/test_ch5c2_real_composers_postgres.py`. The `f4_no_unlisted_read` and `c4` sweeps must stay green. If any read is untracked by the watermark (`chain_input_change`), stop and ask. That fix needs a migration on the walk DB, which this ruling does not authorise.
- **Tests.** `test_e4_prebuilt_routes_generator.py`: overview and index ids for every board day of Kobo and Kisiwa, and the exact query strings. `test_s5_overview_read.py` (or the route test beside it): 2nd identical GET is `stored`, a pin 404 is not stored, an undated request keys on the resolved day. `test_s4_finding_index_reach.py`: a cursor request is not stored. `test_ch5c_store_off.py`: store off composes as before.
- **Q3: yes, every reachable day, the same for both Sites.** Range output must be the same on every page and Site (owner rule), so the overview and index follow the board's day set rather than only the linked days. Extend that set from S+1..last to the date bar's span: add `sites_first_day` beside `sites_last_day` (the earliest day in `days.json` or the Kisiwa entries, or the earliest story-link day if that is earlier). The board, overview and day index are then prebuilt over that span for Kobo and Kisiwa alike. Cold and EV are unchanged: their own routes are already stored or fast. Estimated prebuild: about 10 min. A day outside the span stays a first-hit compose, and is stored after that hit.
- **No DB rebuild.** Only `chain_response` cache rows are written, by the serve itself, as WARM-1 already does. The changed code moves `code_version`, so every stored row misses until it is rebuilt. Merge gate: a fresh Claude review ACCEPT plus the five test files. Then the coordinator fast-forwards the walk1113 tree, restarts the serve (`write_prebuilt_routes` runs at start), runs the full prebuild and `tools/warm_ranges.py` (0 failed), and re-runs the smoke check. Pass: every row reads under 2 s on first hit after prebuild, and there are still 388 × 200.

Decisions logged for owner review: **D-SR.83**.

## D-SR.83a The Overview's wall-clock fields go through the read-instant seam (Architect, Claude, 2026-11-13, owner-delegated, logged for owner review)

- Blocker (WIP `9ffd7416b`): the C4 sweep finds that the stored Overview differs from a compose at t0. The cause is in `scheduling/upstream.py:100`: `now = self.schedule.db_now()` is the one uncaptured DB clock read. Every wall-clock field in the Overview comes from that `now`: `db_now` and `built_at` (`read.py:211`), `consequence_work[*].age_seconds` (`upstream.py:174`), and the ages and states in `environment_health`/`site_observation` (`HEARTBEAT_STALE`, `SITE_VISIT_STALE`, `*_age_seconds`).
- **Ruling: (a), at that single capture.**
  - In `upstream.py:100`, replace the line with `now = read_scope.read_instant(_utc(self.schedule.db_now()))`, the same form as `site_overview/read.py:115`. All the fields above then derive from one instant that the store and the sweep both see. The compose's liveness floor counts that instant (`response_store.valid_until`, M-A).
  - Also add, in `upstream.py` right after `env`/`observation` are computed, `read_scope.within(None, X, now)` for each `X` that is not None:
    - `tick.heartbeat_at + th.stop_after_seconds` and `tick.lease_until`;
    - `tick.retry_due_at`;
    - `max(visits) + th.site_stop_after_seconds`, `head.last_completed_at + th.site_stop_after_seconds` and `head.lease_until`.
  - Reason for the boundaries: a schedule that stops writes nothing, so the watermark never moves. Without these boundaries a stored body could keep reading "running" after the threshold has passed. `health.py` stays pure.
  - About 0.1 unit, on the same branch.
- **Rejected options.**
  - (b) Masking would hide a real stale-state bug and make the sweep stop guarding these fields.
  - (c) Dropping the fields would remove the Overview's "Updated" time and the `asOf` of `ProductStatus`: `SiteWindowOverview.tsx:243-244,965,1091` read `db_now`. Recomputing at serve time would break the "ETag = stored body bytes" contract (`response_store.py`).
- **What the viewer sees.** A stored `db_now` is the instant of the compose, which is when the read was made: "Updated 14:02" stays true. Other stored routes already carry their `read_at` this way. No frontend renders `consequence_work.age_seconds` or the schedule ages from the Overview (checked `siteOverviewClient.ts` and `SiteWindowOverview.tsx`), so a frozen age misleads no one, and the boundaries above end the body before any state they encode flips.
- **Finding index and estate scope:** no change is expected. Their only wall-clock reads already go through the seam: `read_at` in `postgres_assessment_store.py:966`, which feeds `finding_index.py:342,426`, and `postgres_estate_read.py:96`, which `estate/findings` shares and which already passes C4. Both stay in `PATHS`. If the sweep flags either one, apply the same rule (capture through `read_instant` and register the boundary) and never use the WALL mask.
- Tests: the C4 and F4 sweeps go green with the overview, index and scope in `PATHS`. In addition, one stub test in `test_s5_overview_read.py` checks that a `heartbeat_at` near the threshold registers `heartbeat_at + stop_after` as a boundary.

Decisions logged for owner review: **D-SR.83a**.

