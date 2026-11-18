# W4-02 final independent review: mini-grid depth

- **Branch:** `task/W4-02-mini-grid-depth`, head `7f3a0ab6`. The captures are at `b065ee8d`; the only change after that is the packet and evidence commit.
- **Reviewer:** a fresh Claude reviewer, not the author. I read everything through git and my own worktrees, and did not modify review5.

## Verdict: REVISE

The backend is sound. The rules, reads and API conform to the q2–q6 and q9 rulings, the tests are non-vacuous, and the positive states carry the authored-demonstration source class through genuine publication. I could not finish the backend infrastructure part of the review: the migration, store, worker and tick-stage checks are not verified (see "Not verified").

Four High findings block acceptance: one is repository hygiene, and three are user-visible mismatches with the mock or honesty contradictions.

## High

**H1. `frontend/node_modules`, `frontend/dist` and `frontend/tsconfig.tsbuildinfo` are committed.**
- Commit `a82c7a6a` (q10) added 5,293 files, about 1.46M lines, even though `.gitignore` lists `node_modules/` and `dist/`. Later commits keep updating `node_modules/.vite/vitest/results.json`.
- **Why it matters:**
  - The merge would put the whole dependency tree into main.
  - On this machine, `git worktree add` under a long path fails with "Filename too long" (`jest-dom/.../accessible-name-and-description.d.ts.map`) and aborts the checkout. It only works with `core.longpaths=true`.
- **Fix:** `git rm -r --cached frontend/node_modules frontend/dist frontend/tsconfig.tsbuildinfo` on the branch. Squashing the history would be better, so that main never takes in the blobs.

**H2. A raw system word appears in every page's status strip.**
- `MiniPerformance.tsx:366-371` renders `Selected sources: ${classification.toLowerCase()}`. The captures show `Selected sources: authored_demonstration` on all four pages at both widths, 32 times in `evidence.json`.
- The tests lock this in, for example `miniRenewableRoutes.test.tsx:161` and `:271`, `miniServiceRoutes.test.tsx:155` and `miniFuelRoutes.test.tsx:162`.
- The plain label already exists in `ui/productWords.ts:220` ("Prepared example data, not field readings"). The shared `sites/sourceProvenance.tsx` component also renders it, and the Overview already uses it ("Prepared example data.").
- This breaks the owner's rule against system vocabulary and the W3-01 shared provenance presentation.
- **Fix:** render both the selected and pending labels through the shared provenance words, and update the tests to assert the plain words.

**H3. The served MINIGRID Overview contradicts its own cards.**
- `SiteWindowOverview.tsx:361` still shows "Assessed for this day: dispatch only · the other objectives have no read on this Overview".
- `SiteWindowOverview.tsx:380` shows "Objective: nothing here is a current answer."
- In the same capture (`mini-positive-1440-app.png`), the Service card shows `Delivered 20 kW` and the Fuel card shows `Expected use 0–2.39 L`, both read from the new mini endpoints.
- W4-02 added those three card reads (B3) but did not update the strip and objective copy.
- **Fix:** make that copy aware of the mini reads. For example, name the objectives that have a read on this Overview and keep "dispatch only" for non-MINIGRID Sites. Add a test for it.

**H4. The Backup readiness table at 1440 hides the "Witnessed outcome / Readiness remains unverified" row.**
- In `backup-positive-1440-app.png`, only three of the four required-step rows are visible. The fourth row, which carries the main honesty statement, sits below the fold of the bounded inner scroller.
- The mock shows all four rows, and a reader sees "Observed · chain result Pass" three times with no visible unverified row.
- This passed the q12-7 height budget only because the panel scrolls.
- **Fix:** put `{N} cited records · Inspect IDs` on one line so each row stays about mock height and all four rows fit within 316 px. The opened ID list can still scroll inside the panel. Add a capture check that the fourth row is visible when the panel is closed.

## Medium

**M1. Native, unstyled buttons where the mock has link styling.**
- The class `v69-claim-button` has no CSS anywhere in the tree. As a result, "Inspect opportunity constraints", "Inspect fuel basis", the drawer "Close" buttons and the 503 retry render as browser-default black-bordered buttons (see the renewable and fuel captures at 1440 and 390).
- The mock shows "Inspect opportunity constraints ↗" and "Inspect fuel basis ↗" as links.
- This is a user-visible mismatch with the mock. I place it as Medium only because it is pure styling, and the Architect may raise it to High under the rule that every mock mismatch is High.
- **Fix:** use the existing link-button or claim-control style.

**M2. The Service critical card and the clinic row contradict each other.**
- In the gap capture (`service-gap-1440-app.png`), the card "Health clinic (critical): Unknown — Critical delivered power is not measured for the whole hour" sits beside the bar and table row "Health clinic 4 kW · measured 60 of 60 minutes".
- The cause is that the card reads the separate `CRITICAL_DELIVERED` series (`rules.py:535,569`), while the row reads the clinic's `feeder_demand` series.
- On the positive day, the card shows 3.87 kW next to a 4 kW bar for the same load. Its note, "Measured 60 of 60 minutes", comes from the row's coverage (`MiniPerformance.tsx:865`), not from the critical series.
- **Fix:**
  - Name the card's source in its note, for example "Critical-service delivered power record".
  - Take its coverage from the critical series. This needs that coverage on the wire, so route it as an Architect question.
  - Alternatively, ask the Architect to rule which series the card shows.

**M3. q12-1 is not fully met on the served route.**
- The ruling requires "the numeric/gap branches on the served Overview route, not only jsdom".
- Served captures show the Service and Fuel number branches and all the gap branches. The Renewable `Headroom {low}–{high} kW` branch has never been served:
  - 06 Oct is the excluded day and 12 Oct is limited.
  - The packet itself notes that 07–10 Oct would show it.
- **Fix:** add a served Overview capture for one of 07–10 Oct, with a check that the Renewable card shows a value.

**M4. A newly reachable Overview shows a misleading comparison message.**
- Since q12-6, MG-W402-001 reaches the S5 Overview. Its Needs-attention panel now says "No Performance comparison report exists for this Site; the file-backed comparison must run." (`analytics/performance_comparison.py:189`).
- That is false for a Site whose cutover basis is NO_LEGACY_EVIDENCE, and "file-backed comparison" is system vocabulary.
- The same panel also prints the sentence "The Findings list is closed…" twice.
- **Fix:** give the NO_LEGACY_EVIDENCE basis its own plain reason.

## Low

- **L1. "not known" instead of the mock and ruling's "Unknown".** It appears in hatched bars ("What was needed", "Retained margin", and the fuel bars). It comes from the shared `ui/ProductStatus.tsx` ValueBars convention on main, so this is a deviation from the mock wording that predates this slice.
- **L2. Self-contradictory fuel limitation (found by the rules fork).** "Closing tank reading missing" (q3, `rules.py:716`; `MiniPerformance.tsx:151`) is shown while the bridge cites an accepted closing reading. Route a wording change to the Architect, for example "No bounded closing tank reading".
- **L3. No backend test for the positive source class.** Nothing proves that genuine publication makes the public classification `AUTHORED_DEMONSTRATION` and keeps SUPPORTED or Watch. `test_w402_reads_postgres.py:94-98` accepts either outcome, so `seed.py` and the captures are the only proof. Add one Postgres test that publishes, then reads.
- **L4. A single bar fills the whole fuel chart.** The single modelled-use bar (0–2.39 L) fills the full width because every other term is unknown. Consider an unscaled marker.
- **L5. The packet's readings table is stale.** It still lists q11-5 and q12-1..8 as **open**, although Run 12 rules them. Update the status column.

## Builder readings to classify

| Reading | Classification |
| --- | --- |
| q13-1, `site_cutover_basis` added to unmerged 0029 | **Accept.** 0030 is reserved for W4-03, and q8 set the precedent for amending 0029. Any non-test DB already at 0029 must be downgraded and upgraded again; record that in the merge note. The table, CHECK and downgrade themselves are not verified here (see below). |
| q13-2, `Limited by {N} condition(s)` strip disclosure; source chip before currentness | **Accept.** It matches q12-7's "one short limitation summary". This is subject to H2's label fix. |
| q13-3, gap words at the existing word size | **Accept.** |
| q13-4, ≥60 s shown as `{s/60} min` (2 decimals), <60 s shown as `{s} s` | **Accept.** It is accurate per q12-5. Prefer whole or one-decimal minutes. |
| q13-5, service note `{obs/60} of {req/60} min covered` | **Accept.** It matches q12-1's "actual observed/required coverage". |
| q11-5 and q12-1..8 | **Ruled by Run 12.** q12-1 is partly unmet (M3); q12-2..8 are applied as ruled. |

## Checks I ran

- **`tsc --noEmit`** (my worktree): exit 0.
- **Focused vitest** (four mini route files plus `s5SiteWindowOverview`): 5 files, **74 passed**.
- **Full vitest:** 98 files, **2402 passed, 2 failed** (2 files), 401 s, run while a backend suite was also running on the machine.
  - One failing file was `siteFindingEvidence.test.tsx:582`. A rerun of it alone gave 45/45 passed.
  - The second failing file was not identified.
  - I treat both as load flakes, but that is unconfirmed.
- **`npm run build`:** built in 17 s, with only the chunk-size warning.
- **Backend, pure tests** (rules fork): `test_w402_rules`, `projection`, `reads`, `inputs`, `mini_stage`, `roles_properties`: **62 passed**.
- **Backend, Postgres tests** (rules fork, private `w402rr_test` created and dropped): `reads_postgres`, `replay_selection_postgres`, `inputs_postgres`, `authored_v4_postgres`: **10 passed**, 1700 s under contention.
- **Captures:** `evidence.json` has 424/424 ok at `b065ee8d`. They cover region kind and title order, heights (closed and opened), page width and the five-card order.
  - They do not check vocabulary, copy, or whether rows inside bounded panels are visible, which is how H2 and H4 got through.
  - I viewed renewable +, service + and gap, fuel +, backup + and the 390 gap, renewable gap at 390 and Overview +, each against its mock.
- **Full backend suite:** not run by me; the coordinator is running it from review5.

## Not verified

The backend infrastructure fork had not returned before this hand-back, so none of the following is independently verified:
- migration 0029: the `site_cutover_basis` table, the CHECK and counters, the downgrade with its `LOCK TABLE`, and a single head;
- the enqueue trigger and its Site-type and roles-4 whole-hour gate;
- the store as sole writer, with the guards and probes;
- the worker's cutoff, lease and retry;
- the tick stage and q8's FAILED-only Site handling;
- the q12-6 409 retention for a legacy-import MINIGRID;
- the architecture and workflow guards.

The packet's own run reports `check-all` 11/11 and the overview-basis tests passing (3 plus 110 adjacent); I cite those numbers but did not reproduce them. Treat these areas as open until that fork or the full suite confirms them.

## Residual risk

- Any non-test DB already migrated to the earlier 0029 lacks `site_cutover_basis`.
- The Overview mini cards fix `known_at` when the reads start, so each re-render can produce a different cutoff (low impact).

## Backend infra fork result (reviewer sub-review, merged by coordinator)
Checks: 61 focused tests passed (0 skipped); check-all 11/11. Verified: single head, spec DDL, the q7 CHECK and counters, downgrade order, the enqueue gate and recheck, the sole INSERT-only writer with probes, the worker cutoff and settle, q8 scheduling, and non-vacuity.
- **B-M1 (Medium):** the 0029 downgrade drops the q12-6 `site_cutover_basis` table (0029:342) without locking it or refusing when rows exist (0029:303-315). That contradicts "no cascade, no deletion". It is also untested, because the catalog test covers only the mini tables. Fix: lock it and refuse when rows exist, and add it to the catalog and downgrade tests.
- **B-L1:** `site_cutover_basis` has no writer rule or probe in `configuration-persistence.ps1`. Fix: sole writer `postgres_foundation_store.py`, INSERT-only, with probes.
- **B-L2:** `record_no_legacy_evidence_basis` (`postgres_foundation_store.py:231`) is unconditional, and the test for the legacy-import 409 case uses `legacy_documents=()`. Fix: guard the caller, and use real legacy documents in the 409 test.
- **B-L3:** the 0029 docstring catalog is stale.
- **B-L4:** the spec-named `test_w402_api.py` and `test_missing_assessment_unknown_body` do not exist. Coverage is in `test_w402_reads.py`; confirm whether anything is missing.
