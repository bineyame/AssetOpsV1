# W4-03 review packet - mini-grid decisions and work connection

Task: `tasks/W4-03-mini-decisions-work.md` (Lane A, step 2; USER_REVIEW_REQUIRED: true at the W4 owner checkpoint).
Spec: `.agent/W4-03-build-spec.md` (closures 1-5, u1-u9c). Branch `task/W4-03-mini-decisions-work`, 67+ commits over
`main`, ~87 files. Build log and file anchors: `.agent/W4-03-phase-handoff.md`. Questions: `.agent/W4-03-pending-rulings.md`.
Checkpoint (u9b "Remaining units"): unit 10 packet = this file; 11 final independent review; 12 owner closeout.

## Outcome delivered
- `0030_w4_mini_decisions` (ten append-only decision tables, OPPORTUNITY stage + three `schedule_site_head` counters,
  guarded downgrade), Rule-8 writer registration and probes.
- Scenario rules/store/API (authored what-if, scenario labels, never writes W1/W2 consequence or measured tables).
- Canonical Finding Alternatives API + tab (exact Finding revision, accepted/missing-evidence basis, bounded disposition).
- Opportunity enqueue/worker/projection, read/history/currentness/provenance; typed Opportunity detail page and the exact
  five-day Renewable CTA (with `known_at` address and wire, PR-12.6).
- Work decision-context overlay on the frozen W4-01 Incidents/Maintenance lists (one panel-level refusal line for
  Incidents, row-level for Maintenance).
- Private two-Site walkthrough (`tools/w403_mini_decisions_walkthrough.py`: prepare/serve/replay-positive/replay-late/
  capture/drop), capture harness `tools/w403-mini-decisions-evidence.mjs`, registry nodes and `panels[]` keys.

## Files materially changed (groups)
- Backend: `backend/migrations/versions/0030_w4_mini_decisions.py`; `backend/assetops_backend/mini_decisions/`
  (model, scenario_rules, store, services, routers, worker); `tests/test_w403_*` (migration, scenario rules, opportunity
  job isolation/links/read/scan/worker, work links, replay).
- Frontend: `src/sites/MiniScenarios.tsx`, `MiniAlternatives.tsx`, `MiniOpportunity.tsx`, `siteWorkCases.tsx`,
  `w4-mini-decisions.css`, `w4-work-cases.css`, `miniDecisionsClient`, `operatorSiteRoutes`, `App.tsx` route;
  tests `miniDecisions.test.tsx` (26), `siteWorkCases.test.tsx` (9).
- Guards/tools: `tools/checks/configuration-persistence.ps1`, `tools/writer_guard_probes.py`, dependency registry and
  screen ledger entries, the two walkthrough/capture tools.

## Acceptance criteria (task "Observable exit")
1. Scenarios honest empty + persisted authored what-if after reload, labelled scenario, no consequence writes - MET
   (API/store tests; replay fresh-reload equality; captures scenarios-empty/populated/refused 1440/390).
2. Alternatives exact explanations with basis and bounded disposition, no absence-as-proof - MET for read, empty and 503
   states (captures alternatives-db-time and alternatives-read-503 with asserted intercept hit). A stocked Alternative is
   proved by API/component tests only (u9b PR-12.4: not manufactured by shifting W1 times).
3. Opportunity detail backed by five selected days, headroom, denominator, IDs, optional linked scenario, explicit gaps;
   Renewable CTA links to it; no opportunity rows on Finding lenses; late evidence creates a new revision - MET
   (worker/read/replay tests; captures supported-current (positive phase), k_before_late, current-late-settled, missing).
4. Work lists keep W4-01 IDs/counts and show exact linked context; missing links/unverified maintenance visible; no mock
   IDs seeded - MET (work-links tests; captures incidents linked/refused, maintenance).
5. Refusal/migration/1440-390/fixtures/named proof per spec; UI reload and app-vs-mock capture both widths - MET except the
   one same-revision full real-Postgres backend suite, which is left to the coordinator (see below).

## Ruling rounds
- Review closures 1-5 (spec sections "Review closure 1".."5"), then builder rulings u1, u2, u2b, u2c, u3, u4, u4b, u5,
  u5b, u6, u6b, u7, u8, u9, u9b, u9c.
- PR-1 counters persisted in 0030 (u1/u4). PR-2 narrative column (u2). PR-3 CHECK count 45 (u2b). PR-4 decimal strings,
  UNKNOWN currentness (u2c). PR-5 (u3). PR-6 job methods/coalesce (u4). PR-7 opportunity read/association (u5).
  PR-8 Scenarios/Alternatives pages (u6). PR-9 Opportunity breadcrumb/CTA (u7). PR-10 work links (u8). PR-11 replay
  409 against DB time (u9). PR-12 panel caps, fixture path, cutoff wire (u9b). PR-13 Scenarios/Incidents caps (u9c).
  All thirteen are marked RESOLVED in the pending-rulings file; none is open.

## Builder readings (handoff sections; reviewer may overturn)
- Unit 1 (handoff l.24): 1 field bounds from W4-01 0027; 2 unnamed CHECK names; 3 model_version is a store constant;
  4 `_check_job` tenant/Site/domain only; 5 downgrade lock/refusal order; 6 S18 current-head updates.
- Unit 2a (l.69): 7 decimals are plain JSON strings; 8 OTHER value/unit shape; 9 assumption source 1-500; 10 calculation
  reason codes, per-window energy/gross.
- Unit 4 (l.243): producer_id `mini-opportunity/1`; missing-day `selected_hours` handling.
- Unit 5 (l.287): 1 non-MINIGRID UNKNOWN envelope; 2 SOURCE_STALE on STALE_SOURCE; 3 literal window overlap; 4 linked gross
  withheld unless CURRENT/HISTORICAL; 5 body/path id mismatch 422; 6 no detail `window`; 7 closed-gate body; 8 page-two
  cutoff from cursor. u5b (l.327): MIXED/UNKNOWN via monkeypatched classification.
- Unit 6a (l.345): 1 raw six-digit read time; 2 address replace after first read; 3 `{n} of {total}` pager; 4 declared
  change/basis format (basis later replaced by count + disclosure, PR-12.1); 5 non-MINIGRID panel text; 6 breadcrumb.
- Unit 6b (l.384): 1-9 Overview tab id, Analysis declared unavailable, helper placement, breadcrumb, loading/refused
  slots, sibling revision, same-Site exact match, no W1 re-read, body states. u6b (l.473): sibling gap labels.
- Unit 7 (l.431): 1 breadcrumb; 2 proposed-load card notes (shortened under PR-12.2); 3 multiple roots copy; 4 tone;
  5 headroom display; 6 positive claim rule; 7 gross-sales gap words; 8 bounded evidence drawer.
- Unit 8 (l.496): 1 duplicate pair 409; 2 refused overlay copy; 3 scenario label; 4 POST refusal order; 5 hash path;
  6 contexts `known_at`; 7 visible selected revision; 8 public site code in URL; 9 layout deferred to 9b.
- Unit 9a (l.545): 1 KOBO Alternative POST 409; 2 late STALE_SOURCE; 3 second reconcile window; 4 `--db/--work` guards;
  5 work-link window; 6 authored-field reload equality.
- Unit 9b (l.593): 1-8 (I-mini-depth-read in requires; capture-owned stock; 7-day window; Scenarios bounds; two-phase
  Opportunity states; jsdom vs browser geometry; `mobile:false`; Alternatives 503) - confirmed or replaced by u9b.
- u9b (l.638): 1-4 - confirmed by u9c.

## Accepted limitations
- **`Alternatives unavailable` departs from the v69 mock**: a bold panel label shown only for an Alternatives GET 503 or
  transport failure, above the exact 503 copy. The mock shows a populated table and has no such label; u9c confirms it
  as the reviewed honest refusal state, not a mock quotation.
- No stocked Alternative capture (F02 revision future-dated vs DB time; POST stays 409 `DECISION_BASIS_CHANGED`).
- A completed replay cannot yield SUPPORTED/CURRENT (fixed late receipt, PR-11); the supported/current capture is the
  positive phase before late ingestion. `k_before_late` is historical, not current.
- Scenarios populated table scrolls at 144 px (1440) / 188 px (390): at 1440 the second authored row is partly below the
  fold of the inner box and is reached by scrolling (u9c supersedes the header-plus-three-rows viewport).
- Refused overlay: one panel-level Incidents line; Maintenance keeps row-level copy (u9c reading 2).
- Duplicate/invalid `known_at` in the address is sent unchanged so the server refusal shows (u9c reading 3).

## Test evidence (this revision unless noted)
- Frontend at `de919d91`: 103 files / 2464 tests passed; `tsc -b --noEmit` 0; `npm run build` 0; `tools/check-all.ps1`
  all 11 guards passed (includes architecture seams and agent workflow).
- u9c focused: `miniDecisions.test.tsx` + `siteWorkCases.test.tsx` 35 passed. Non-vacuity: with the parent CSS restored,
  `narrow_mock_panel_budgets` and `u9b_incident_linked_and_refused_overlay_panels` both failed; CSS restored from HEAD.
- Backend focused (per unit, private `w403*_test` DBs, all dropped): migration 9-11, scenario rules 26/61/53, scan,
  worker 5, isolation 4, read 9 + links 1, work links 3 (+ w401 API 15), replay 2 passed (449 s, `w403q_test`), S18 head
  files 168 passed. Counts per unit in the handoff "Checks" sections.
- **Full real-Postgres backend suite: not run here - left for the coordinator** (one same-revision run with JUnit
  zero-skip check per `backend/TESTING.md`). Record: command, revision, wall time, JUnit counts.

## Captures (`var/w403r/capture/`, gitignored; code `87595bdd`, harness `de919d91`, DB `w403r_test` dropped)
- `evidence.json` **359/359 passed** (`evidence-positive.json` 44/44 merged). Panel set and order match v69 on every state.
- Scenarios populated: 1160x328 <= 348 (1440), 343x372 <= 391 (390); inner box 144/188 px with vertical scroll
  (scrollH 197 > 144; 288 > 173). Empty 325/325; refused 160/160. Notice unchanged.
- Incidents linked 425 (1440) / 430 (390); refused overlay 445 / 456 <= 460, five rows, one `Decision context
  unavailable` line, inner vertical scroll.
- Opportunity supported-current (positive phase) cards 95 (1440) / 227 (390) within 137/273.
- Viewed: `scenarios-populated-1440-app.png`, `scenarios-populated-390-app.png`, `incidents-refused-overlay-390-app.png`
  (earlier rounds: opportunity-supported-current 1440/390, alternatives-read-503 1440, incidents-linked-stocked 390).
- Prior runs for history: `var/w403p` 240/265 (pre-PR-12), `var/w403q` 356/359 (pre-u9c).

## Known deviations
- None against the rulings. The capture harness check for the Scenarios scroll box was updated in place from the retired
  252 px value to the u9c 144/188 px limits plus `scrollH > clientH` (total stays 359).

## Residual risk
- Full backend suite not yet run on the final revision.
- Capture geometry depends on the walkthrough fixture (two authored scenarios, five incidents); other row counts are
  covered only by jsdom structure/stylesheet tests.

## User-review focus
- Owner walkthrough (unit 12): Scenarios inner scroll at 1440 (second row partly hidden until scrolled), the
  `Alternatives unavailable` mock departure, the honest no-stocked-Alternative state, and Opportunity state wording.
