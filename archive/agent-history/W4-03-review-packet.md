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
2. Alternatives exact explanations with basis and bounded disposition, no absence-as-proof - exact-basis refusal proved;
   successful empty at current DB time unproved (uF 1). Captures alternatives-db-time (409 `DECISION_BASIS_CHANGED`,
   `The evidence changed. Reload this page.`, after Site/Finding 200) and alternatives-read-503 (scoped intercept), both
   1440/390. Stocked Alternatives are API/component proof only.
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
- Omitted earlier, now listed (L12): unit 4 cited-ID subset and deferred count; unit 5 reading 9; u5b `EMPTY_CITATION_SET`
  (ruled uF 5: the empty UNKNOWN six-key DTO, asserted exactly); 6b readings 10-14; u6b domain-unavailable copy and First
  page; unit 7 readings 9-12; the PR-2, PR-4 and PR-5 readings.
- Overturned: 6b readings 3, 6, 9 and unit 7 readings 1, 10 (controlling: u6b/u7 rulings and uF 3/M7 for the crumb and
  Site-tab treatment); unit 1 reading 1 for `reason`/`correction_reason` (uF 4: 1-2000); u3 PR-5 reading 7 for a
  same-Finding future revision (uF 1: 409).

## Final review (`.agent/W4-03-final-review.md`) disposition
| Finding | Fix / ruling | Commit | Proof |
|---|---|---|---|
| H1 chip tone | compound `.badge.mini-opportunity-tone--*` | 056ae517 | CSS test; computed backgrounds green/amber/blue in captures (blue = new `opportunity-supported-historical`) |
| H2 big claim | `BigClaim` | 056ae517 | capture: `.v69-big-claim` 19px (= v69 `.big-claim`) > prose 14px, cap held |
| H3 Open site | header action | 056ae517 | test + capture `[["Open site","/sites/KOBO-001"]]` |
| M1 DB-time 404 | uF 1: same-Finding future revision/root -> 409 basis refusal | 38552dbf | `test_alternative_r1_r2_...` (two 409 vectors, unknown 404 kept); route shape test; capture 409 + copy 1440/390 |
| M2 gate | Performance gate on unpinned GET | 4880cb37 | `test_alternative_routes_refusal_order` |
| M3 reasons | 1-2000 in `0030` + parser | 4880cb37 | `test_final_review_m3_alternative_reason_bounds_2000` |
| M4 stage test | mixed PENDING/LEASED/FAILED + foreign Site | 4880cb37 | stage Postgres test, `deferred=2` |
| M5 scenario context | SCENARIO link via POST, contexts at W4-01 `known_at` | 38552dbf, f545fbec | replay asserts `label:"SCN-000002 · ..."`, `url:null`; capture literal, no link/focus, `OPPORTUNITY,SCENARIO`, 5 rows, 1440/390 |
| M6 Site tabs | uF 3: removed on canonical mini Alternatives only | 38552dbf | component test (absent there, present on History); capture both widths |
| M7 crumb | inline run, no leading separator | 056ae517, 38552dbf | test + capture line-start checks |
| L1-L7, L9 | literal fixes | 4880cb37, e482f7c2 | focused vectors (`test_w403_final_review_writes.py` et al.) |
| L8 | plain key labels + plain UTC cutoff (`<time datetime>` keeps the token) | 38552dbf | `miniDecisions.test.tsx` |
| L10 | uF 6: FAILED retained for unchanged input; delayed PENDING stays pending | 38552dbf | `test_uf6_failed_job_is_retained...`, `test_uf6_delayed_pending_job...` |
| L11 | uF 5 rulings: monkeypatch acceptable (unit vector, not live mixed fixture); `EMPTY_CITATION_SET` DTO; predecessor 422/409; retry-once | 38552dbf, e482f7c2 | `test_u_f5_*`, scenarios correction test |
| L12 | packet/ledger corrections (this section, criterion 2, PR-1 heading) | this commit | - |

Scoped W1 shell departure (uF 3): the canonical mini Finding Alternatives page has no Site tab row; every other W1
Finding view and Site page keeps it.

## Accepted limitations
- **`Alternatives unavailable` departs from the v69 mock**: a bold panel label shown only for an Alternatives GET 503 or
  transport failure, above the exact 503 copy. The mock shows a populated table and has no such label; u9c confirms it
  as the reviewed honest refusal state, not a mock quotation.
- No stocked Alternative capture (F02 revision future-dated vs DB time; POST stays 409 `DECISION_BASIS_CHANGED`).
- A completed replay cannot yield SUPPORTED/CURRENT (fixed late receipt, PR-11); the supported/current capture is the
  positive phase before late ingestion. `k_before_late` is historical, not current.
- Scenarios populated table scrolls at 144 px (1440) / 188 px (390): at 1440 the second authored row is partly below the
  fold of the inner box and is reached by scrolling (u9c supersedes the header-plus-three-rows viewport).
- Refused overlay: one panel-level Incidents line; Maintenance keeps row-level copy (u9b reading 2).
- Duplicate/invalid `known_at` in the address is sent unchanged so the server refusal shows (u9b reading 3).

## Test evidence (this revision unless noted)
- uF round (code 38552dbf, harness f545fbec): frontend 103 files / 2465 tests passed; `tsc -b --noEmit` 0; `npm run
  build` 0; `tools/check-all.ps1` all 11 guards passed. Backend focused (`w403s_test`, dropped): alternative + final-review
  writes + opportunity read + scan 25 passed (1730 s); job isolation (M4 stage) + worker + links + stage + work links +
  scenarios 32 passed (2568 s). Old-code failures: M1 vectors expected 404 before, L10 scan/read vectors, M6/L8
  component assertions.
- Frontend at `de919d91`: 103 files / 2464 tests passed; `tsc -b --noEmit` 0; `npm run build` 0; `tools/check-all.ps1`
  all 11 guards passed (includes architecture seams and agent workflow).
- u9c focused: `miniDecisions.test.tsx` + `siteWorkCases.test.tsx` 35 passed. Non-vacuity: with the parent CSS restored,
  `narrow_mock_panel_budgets` and `u9b_incident_linked_and_refused_overlay_panels` both failed; CSS restored from HEAD.
- Backend focused (per unit, private `w403*_test` DBs, all dropped): migration 9-11, scenario rules 26/61/53, scan,
  worker 5, isolation 4, read 9 + links 1, work links 3 (+ w401 API 15), replay 2 passed (449 s, `w403q_test`), S18 head
  files 168 passed. Counts per unit in the handoff "Checks" sections.
- **Full real-Postgres backend suite: not run here - left for the coordinator** (one same-revision run with JUnit
  zero-skip check per `backend/TESTING.md`). Record: command, revision, wall time, JUnit counts.

## Captures (`var/w403s/capture/`, gitignored; code 38552dbf + harness f545fbec, DB `w403s_test` dropped)
- `evidence.json` **459/459 passed** (`evidence-positive.json` 98/98 merged); unproved: `alternatives-stocked`,
  `alternatives-empty-current` (uF 1). Commands: walkthrough `prepare`, `serve`, `replay-positive` (exit 0), `capture
  --phase positive` (exit 0), `replay-late` (exit 0), `capture` (exit 0); vite 6147 -> API 9761.
- M1: pinned Alternatives GET 409 after Site 200 and Finding 200; panel 99 <= 268 (1440) / 99 <= 365 (390), notice
  43 <= 66 / 61 <= 84; no Site tab row; Finding row of six incl. `Analysis · Not available yet`.
- M5: contexts GET at `known_at` 2026-10-21T21:52:18.523211Z -> OPPORTUNITY then SCENARIO `SCN-000002 · Grain mill
  one-hour trial (corrected narrative)`, `url:null`; images `incidents-linked-stocked-{1440,390}-app.png`.
- Viewed: `opportunity-supported-current-1440/390-app.png`, `alternatives-db-time-1440-app.png`.

## Known deviations
- None against the rulings. The capture harness check for the Scenarios scroll box was updated in place from the retired
  252 px value to the u9c 144/188 px limits plus `scrollH > clientH` (total stays 359).

## Residual risk
- Full backend suite (coordinator, in-container OPS-03 run 20261022-042009-71c07f on cfd1510a, main merged): 3818 passed, 0 failed, 1:10:55. An earlier run on 60a69552 had 10 failures: 8 stale CRLF working copies (environment), plus the missing w403 fixture eol rule and a stale replay assertion, both fixed in cfd1510a. Frontend on cfd1510a: 2480/2480 (one earlier run had 1 load-timing failure that passed on rerun).
- Capture geometry depends on the walkthrough fixture (two authored scenarios, five incidents); other row counts are
  covered only by jsdom structure/stylesheet tests.

## User-review focus
- Owner walkthrough (unit 12): Scenarios inner scroll at 1440 (second row partly hidden until scrolled), the
  `Alternatives unavailable` mock departure, the honest no-stocked-Alternative state, and Opportunity state wording.
