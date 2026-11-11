# Architect: one sequenced view of walkthrough comments and backlog, for the client-demo scope (2026-11-11)

## Client demo Tue 17 Nov: cut and start order (Architect, Claude, 2026-11-11 ~06:30; supersedes the dates in sections 0-5, keeps their scope rationale)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude since 2026-10-27. Fresh instance.
- Owner, verbatim (`.agent/owner-tag-optionb-client-date-2026-11-11.md`): "yes tag it and add the backlog item, lets go with option B for now. Also, lets proceed with the items for today right away, and i want my walkthrough comment items to start building. THe client demo will be on 17-Nov"
- Owner, verbatim (`.agent/owner-units-by-friday-2026-11-11.md`): "let it not say which would land by Friday, we wait until Thursday morning for re-assessment". This section sets the cut and the order. Thursday morning re-assesses against real merges and applies the cut order in C.4.

### C.1 Backwards schedule from Tue 17 Nov

| When | What | Machine |
|---|---|---|
| Tue 17 | Client demo. Morning: 30-min smoke check on the serve. | serve only |
| Mon 16 | **Final demo build** (prepare ~2 h 45, S = Mon 16, so "yesterday arrives" works live), finish checks, live checks (~1.5 h), figures quoted into both scripts, tag `demo/2026-11-16-final`. Only a blocking frontend fix may land (serve restart, no prepare). | one heavy job |
| Sun 15 | **Owner walkthrough** on the rehearsal build (morning). One Sonnet fix round in the afternoon, targeted tests, merged by 22:00. | light |
| Sat 14 noon -> Sun 15 morning | **Freeze at 12:00 Sat (last feature merge).** Full suites + check-all + fixes (~6 h, lanes stopped). Rehearsal demo build overnight (~2 h 45), live checks, recapture (light theme only), script refresh with PILOT-1 (0.25). | quiet machine, one heavy job at a time |

- **End work needs 2.5 days** (Sat noon to Mon evening). It cannot shrink: the rehearsal build is the only place DATA-12's CO-6/WK-GAP proof, PB-1 and the new Portfolio run together on real data, and the walkthrough needs a build.
- **Real build window: now (Wed 06:30) to Sat 12:00, about 3.2 days.**
  - Wed 06:30 -> Thu 12:00: 2 lanes; Wednesday's fixed work (E5b, retakes, script pass, DS-1f/DS-1b merge, the owner's afternoon walkthrough) uses the coordinator and part of a lane. About 1.7 lane-days.
  - Thu 12:00 -> Sat 12:00: 3 lanes (lane C only while free RAM allows). About 5.5 lane-days.
  - **About 7.2 lane-days, so 10.8 units at 1.5 per lane-day, 12.6 at the measured 1.75.** The cut below is 10.55 units, plus PILOT-1 in the script refresh.

### C.2 The cut, in plain language

**IN for 17 Nov (10.55 units).** Chosen by: what the client sees first, what reads as untrue or broken, and what the owner raised in the walkthrough.
1. **Coverage counts the Site's own local days (DATA-12, 1.0).** The "checked" honesty fix: the Portfolio stops calling Kobo fully checked when its 4 Nov has no readings. Removes the D-E5.40 known-defect marker.
2. **Days never analysed stop saying "nothing to report" (PB-4, 0.5); coverage counts from when a Site's readings began (PB-7, 0.25).** Same honesty theme as DATA-12.
3. **The new coverage words (PF-W, 0.75)**: complete / partial / too few / no readings received / still processing / not analysed yet. Owner items 3 and 5.3.
4. **Portfolio tabs with coverage shown once (PF-T 1.0, PF-C 0.5).** The opening page; owner item 2. PF-T also moves the Portfolio's date bar to the top (owner item 4; left menu unchanged).
5. **Scalable "Outcomes across the estate" (PF-O2 0.5, PF-O1 1.0).** Owner item 9, design approved; default view by outcome group.
6. **Cold and EV pages show their analysed periods on any day or week (PB-1a 1.0, PB-1b 1.0, PB-1c 0.25).** Owner item 11: today they read "Unknown" off-script.
7. **Unbuilt integrations read as a short roadmap (RM-1 0.5; RM-2 0.1 if approved).** Owner item 11: 16 error-looking values.
8. **Small screen fixes (PB-5 legend names, PB-6 copy, PB-8 Fuel tab loading; 0.6).** Owner item 11, already specified.
9. **"Why?" sees the same issues as the board (BL-50, 0.25); Kisiwa finish check covers days without a selection (DATA-1 L2, 0.1); Kisiwa targets (DATA-6, 0.25, if approved).**
10. **FR-B test fix round (1.0).** Invisible, but Saturday's full suites are only readable with it.
11. PILOT-1 "how a client starts" page in the script (0.25, with the script refresh).

**Stretch, in this order, only if Thursday's re-assessment shows room:** UQ quick wins (0.75: larger type floor, thousands separators, one empty/loading style, no ISO dates in link text); then PB-3 + DATA-11 if the client runs EV or cold rooms; then BeagleBone TEL-08 if the evaluator is technical.

**After 17 Nov (in this order):** any-range speed ANY-1/ANY-2 (~7 units, with UQ-6a first; the presenter stays on the pre-built ranges, which already cover the script and the lens variants); one shared date range on every page (SR-1..3, 1.75; the Portfolio already gets its date at the top); the design foundation (v7.2 sheet, Inter, light/dark themes, states, formats; ~4); FCF-1; price-it first step; DATA-4/5/7/8/10/13; French and Swahili; region, PF-O3, AR-5/7; BL-70; the rest of section 2.
- **Why ANY and SR go after:** ANY-1 alone is 3.0 units with a migration whose tests need a quiet machine, and its parity baseline must wait for PB-1/PB-4/PB-7; it cannot land safely by Saturday. SR touches every page frontend and would collide with PF and PB-1c in the same week.
- **Id note:** DATA-12 here is D-E5.38's coverage fix. The older backlog item "DATA-12 longer Cold failure window" (non-Kobo answer) is renamed **DATA-14**.

### C.3 Order and lanes

| Lane | Order (each merges on review ACCEPT; only High/Medium block) |
|---|---|
| **A, server and data** (starts now) | DATA-12 -> PB-4 + PB-7 + BL-50 + L2 (+ DATA-6 if approved) -> PB-1a -> PB-1b |
| **B, Portfolio screens** (starts now) | PF-T -> PF-C + PF-W (after DATA-12 merges) -> PF-O2 + PF-O1 |
| **C, fixes** (from Thu ~12:00, memory permitting) | PB-5/6/8 + RM-1 (+ RM-2) -> PB-1c (after PB-1a/b and PF-T) -> FR-B -> stretch |

Causal reasons: DATA-12 changes what the coverage line says, so PF-C and PF-W build on it. PB-4 lands before PF-W because both touch the Site Findings words. PB-1a and PB-1b share `postgres_assessment_store.py`, so one lane. DATA-12 and DATA-6 both edit CO-6 in `tools/demo_combined_finish.py`, so one lane.

### C.4 Cut order if Thursday shows lag (first cut first)
1. Stretch items. 2. FR-B (its known failures are listed as known in Saturday's suite run). 3. PF-O1/PF-O2 (today's outcomes grid fits 4 Sites). 4. PB-1b (EV stays on its analysed-period story link, D-E5.36).
Never cut: DATA-12, PB-4, PB-7, PF-W, PF-T, PF-C, PB-1a, RM-1, PB-5/6/8.

### C.5 Machine rules for every brief
- 16 GB, ~3.5 GB free with the demo app up; Docker's VM crashed once last night. **One heavy job at a time.** Builders run only the named test files; no full suites, no prepares, no recaptures, no Playwright captures until Saturday.
- Until Thursday's demo ends: never touch wt `AssetOpsV1-e3d`, DB `assetops_polish_client6_test`, ports 8990/5490; no Docker restarts; Postgres tests only on the builder's own `*_test` DB. The coordinator checks free RAM before each dispatch and pauses lane C first.
- Builders: Write/Edit only, no subagents, PYTHONPATH absolute under the worktree (incl. `contracts`, `simulator`), commits end with the Co-Authored-By line, never push, `git add -f` for `.agent`.

### C.6 Start-now briefs (no pending owner approval)

**A1 DATA-12 coverage on Site-local graded days.** Sonnet (precise spec). Wt `AssetOpsV1-data12`, branch `task/DATA-12-coverage-local-days`. 1.0 unit. **Start now.**
- Goal: Portfolio coverage counts the Site's local days from the stored chain day grades; one day definition on the screen.
- Spec: D-E5.38 in `.agent/build-sheet-OWN-GAPS-2026-11-08.md` (the "Spec for the fix" bullet is the card); D-E5.40.
- Files: `backend/assetops_backend/estate/coverage.py` (`site_coverage`, `_mini_grid`: keyword `day_grades: Mapping[date, str] | None = None`); callers `estate/index.py:148`, `estate/evidence_money.py:463`, `estate/financials.py:417` pass grades from the same memoised `req.day(site_id, site_type, window_days(...))` read the claims use; `tools/demo_combined_finish.py`: remove `KNOWN_DEFECTS` and set CO-6/WK-GAP to expect Kobo PARTIAL with the local gap.
- States: NO_DATA -> gap (`UNASSESSED`, `NO_READINGS`); PENDING -> Site PENDING_RECOMPUTE; COMPLETE/PARTIAL/LOW -> checked. `None` keeps today's behaviour.
- Tests that pin it: in `backend/tests/test_w301_estate_coverage.py` (or a new `test_estate_coverage_local_days.py`), a UTC+3 Site whose local day D is NO_DATA while both UTC windows touching D have selections -> PARTIAL, `gaps == [D]`, requested 7, checked 6, `text` set; `None` path unchanged; `backend/tests/test_demo_combined_finish_rows.py` CO-6/WK-GAP rows. CO-6/WK-GAP on a real build are proven at Saturday's rehearsal build, not now.

**B1 PF-T Portfolio section tabs.** Opus. Wt `AssetOpsV1-pft`, branch `task/PF-T-portfolio-tabs`. 1.0 unit. **Start now.**
- Goal: Overview (four cards, counts strip, top 3 act-first) plus Act first, Outcomes by site, Opportunity, What changed, Scope & coverage tabs; date bar at the top; left menu unchanged.
- Spec: `.agent/architect-proposal-portfolio-layout-2026-11-10.md` §6, §11; layout `frontend/mockups/v71/portfolio-tabs.html` (label any MOCK DEVIATION in a header comment). Tab names owner-approved (walkthrough item 5.1).
- Files: `frontend/src/estate/EstatePortfolio.tsx`, `estatePortfolio.css`, `portfolioWords.ts`, the router entry for `/portfolio/:tab?`.
- Rules: one mounted route (tab switch = no refetch); tab links carry `from`/`to`/`known_at`; `lens` only on Act first; `/portfolio?lens=X` -> `/portfolio/act-first?lens=X`; unknown tab -> Overview; unknown count = no badge, never "0"; `<nav aria-label="Portfolio sections">` with `aria-current`; focus to panel heading; wrap at <=760 px. Do not touch the coverage line (PF-C).
- Tests: `frontend/src/estate/__tests__/estatePortfolio.test.tsx`, `estatePortfolioRoutes.test.tsx` (each rule above one assertion). Vitest on those files only; no captures.

**A2 PB-4 + PB-7 + BL-50 + DATA-1 L2.** Opus. Wt `AssetOpsV1-pb4`, branch `task/PB-4-honest-days`. 1.1 units. After A1 merges.
- Spec: PB-4, PB-7 cards in `.agent/architect-answer-non-kobo-sites-2026-11-10.md` (Cards, "Before the client session"); BL-50 row in `.agent/backlog-post-demo.md`; L2 in the DATA-1 re-review (`KISIWA-COHORT` also fails a Kisiwa day with readings and no dispatch selection).
- Files: Site Findings list-state builder (pre-flight names it, behind `sfi2` and the Overview list); `site_outcomes/mini.py:362-392`; `chain/why.py:282-285`, `site_outcomes/read.py:455-457`; `tools/demo_combined_finish.py`.
- Literals: "not analysed yet"; `since readings began on {d}: {g} of {n} days …`.
- Tests: a list-state test with an AMBIGUOUS day (never CURRENT or "Checked: nothing to report"); `frontend/src/shell/__tests__/s404SiteFindingIndex.test.tsx`; mini outcome tests + golden rows; `backend/tests/test_ch5b_why.py` (Cold failure-day Protect "Why?" names both threads); `test_demo_combined_finish_rows.py` L2 row.

**A3 PB-1a Cold analysed periods.** Opus. Wt `AssetOpsV1-pb1`, branch `task/PB-1a-cold-periods`. 1.0 unit. After A2.
- Spec: D-E5.31; PB-1a card (same answer file). Files: `postgres_assessment_store.py:2168-2240` `_snapshot` default mode; `analytics/cold_site_reads.py` adds `analysed_periods: [{from,to,href}]`, `shown_period`.
- Tests: day window over one period; week over four (failure day wins, open Finding); window with none; pinned unchanged; Site read + API tests. Named Cold store test files only.

**A4 PB-1b EV analysed periods.** Opus. Same wt, branch `task/PB-1b-ev-periods` from main after A3 merges. 1.0 unit.
- Spec: PB-1b card. `postgres_assessment_store.py:2895-2945`; same start -> widest wins (08:00-09:05); `ev_site_reads.py` provenance per period.
- Tests: as A3 plus E4 provenance, in `backend/tests/test_w206_ev_store_postgres.py` and the EV read tests.

**B2 PF-C + PF-W coverage once and the new words.** Opus. Wt `AssetOpsV1-pft` (new branch `task/PF-CW-coverage-words` from main). 1.25 units. After B1 and A1 merge (A2 too if it has merged; else rebase).
- Spec: proposal §4 (PF-C), §10 incl. the §10 inventory (PF-W); term family owner-accepted (item 5.3).
- Files: server `coverage_line` from `counted.days` + exception-only card `days_line` (`site_outcomes/read.py` portfolio cards); backend vocabulary and frontend words files per §10; R620/R622 register rows.
- Tests: expected strings in the affected backend and frontend tests; one test that "checked" never appears in a coverage sentence; "7 of 8 hours" form replaced per §10.3.

**B3 PF-O2 + PF-O1 scalable outcomes.** Opus. Branch `task/PF-O-outcomes-scale`. 1.5 units. After B2.
- Spec: proposal §9.4-9.6 and §9.8; layout `frontend/mockups/v71/estate-outcomes-scale.html` (approved, item 12.1); default view "By outcome group". No region, no PF-O3, no AR-7.
- Files: `outcome-sites` route in memory over `summary()` (`outcomes[]` kept, facets, need-for-attention order, cursor); `frontend/src/estate/PortfolioOutcomes.tsx`, `useOutcomeSummary.ts`.
- Tests: route contract incl. the never-total test; frontend sort, grouping, paging, empty/loading states.

**C1 PB-5/6/8 + RM-1 screen fixes.** Sonnet. Wt `AssetOpsV1-pbfix`, branch `task/PB-fixes-RM-1`. 1.1 units. From Thu ~12:00.
- Spec: PB-5, PB-6, PB-8, RM-1 cards and the C rows of the table in the non-Kobo answer; D-E5.34 (each literal names what is missing; none reads as an error).
- Tests: `s5SiteWindowOverview.test.tsx` (Kisiwa "Households meter", "Cold store meter", "Water pump meter"); MiniPerformance (no "Fuel balance: Unknown" before nights resolve); `dispatchWords` split; EV Financials row and empty total; ColdHealthDepth id in Technical details; one test per RM-1 literal.

**C2 PB-1c analysed-period line.** Sonnet. Branch `task/PB-1c-window-line`. 0.25 unit. After A4 and B1 merge, and the owner's nod.
- D-E5.31 literals in the Cold and EV window bars with period links; MOCK DEVIATION header comment; Cold and EV view tests.

**C3 FR-B test fix round.** Sonnet. Branch `task/FR-B`. ~1.0 unit. After C1.
- Scope: the "Carry to FR-B" list in `.agent/coordinator-handoff.md` (wrapper fixes, T6 w301 golden, `pin_read_at` patches `EvidenceMoneySnapshot`, FR-A Lows L1-L3, I1, `OBJECTIVE_BEHIND_PACE` in the xfail tuple). Only the named test files.

### C.7 Owner approvals to ask today (one message)
1. **Move any-range speed (ANY-1/ANY-2, ~7 units) to after 17 Nov; the presenter stays on the pre-built ranges.** Recommend yes: it cannot land safely by Saturday.
2. **Move the shared date range on every page (SR) and the design foundation (Inter, light/dark themes, v7.2 sheet) to after 17 Nov.** Recommend yes; the Portfolio still gets its date bar at the top, and the UI quick wins stay first stretch.
3. **Confirm `portfolio-tabs.html` as the approved layout spec** (its header still says "Draft"). Recommend yes.
4. **Hide the lens chips on Cold, EV and Kisiwa (RM-2).** Recommend yes.
5. **Add the "Analysed period" line under the date bar on Cold and EV (PB-1c).** Recommend yes.
6. **Kisiwa targets set to 0 for avoidable generator minutes and unserved critical supply (DATA-6).** Recommend yes.
7. **What does the client operate (mini-grids, diesel, cold rooms, EV depots), and is the evaluator technical?** Recommend answering by Thu morning; it decides the stretch order and BeagleBone.
8. **Schedule: last merge Sat 14 noon, your walkthrough Sun 15 morning, final build Mon 16.** Recommend yes; tell us your Sunday time.

- Architect: Claude (`assetops-architect`). Binding checked in `.ai/ROLE_CONFIG.md`: Architect = Claude since 2026-10-27.
- Owner, verbatim (`.agent/owner-client-scope-sequencing-2026-11-11.md`): "the architect need to sequence the walkthough comment implementations as well as overall backlog so i can see what is worth putting in scope of client demo"
- Inputs: `owner-walkthrough-2026-11-10.md` (items 1-13), `backlog-post-demo.md` (BL-01..69), `architect-plan-pre-client-2026-11-10.md` (the ~26-unit plan), `architect-answer-non-kobo-sites-2026-11-10.md` (item 11 audit), the 2026-11-10 answers on speed, money, layout, price-it and UI quality, `coordinator-handoff.md`.
- **Status:** a recommendation. Nothing is scheduled until you decide (section 4). No code changes.
- Already merged, so not in the table: Kobo gap pattern, lens keeps the page and pre-built lens pages, Findings cards, Cold/EV analysed-period story links, Kisiwa one recording session, the E5 fixes, C1-C5. The Wednesday frontend fixes (Kisiwa chart legend, copy batch, Fuel tab loading; 0.6 units) are planned before Thursday; if any slips, it goes first in lane B on Mon 16.

## 0. Agent-pace plan, re-assess Thu 12 Nov morning (added 2026-11-11; replaces the working-day calendar in sections 1 and 3.2; scope, order and decisions stay)

Owner, verbatim (`.agent/owner-units-by-friday-2026-11-11.md`): "the time estimates are for human developement, we should be able to do the indicated units in time for Friday" and then "let it not say which would land by Friday, we wait until Thursday morning for re-assessment".

- **You are right that my calendar was too slow.** I sized lanes at 1.5 units per *working* day. Agents run most of the 24 hours, every day of the week.
- **This section therefore sets the lanes and the order at agent pace, starting now.** It does not forecast what lands by Friday. Progress is re-assessed Thursday morning against the actual merges.

### 0.1 What agents actually delivered (git log on main, 8-11 Nov)

| Day | Merged slices (unit sizes from the build sheets; a few estimated) | Units merged | What else that day used |
|---|---|---|---|
| Sun 8 | Kisiwa K4b, K5, K6a, K6b, K6c, K7-D/F, K8, K9, K10; G3a; R-1; idle fuel A3 | about 7 | four lanes, owner away, specs already closed |
| Mon 9 | G1 1.75, G2 2.25, G3b 1.25, R4.1, POLISH-1, E2 fix A, C1-C4 (about 2.0) | about 8 | G1-G3b built mostly on Sun 8; E2 suites and E3 build |
| Tue 10 | C5, E5-FX, FX-EV-TITLE, FX-COLD-LINKED, FX-KOBO-GAPS 0.6, V3, PL-1, PL-2, DATA-2, FC 0.75 | about 3.8 | E3c/E4 checks, your walkthrough, six Architect answers |
| Wed 11 (to 05:00) | DATA-1 0.5 | 0.5 | E3d demo build |

- **Average: about 6 units per calendar day across 3-4 lanes, about 1.75 per lane per day.** It fell to about 4 on a day with a demo build and a walkthrough.
- **Review and fix rounds are part of that rate.** The four days had 110 review commits and 34 fix commits. Most slices take one fix round, and DATA-1, PL-1 and FX-COLD-LINKED were each rejected once first.
- **Those were small fixes to closed specs. The IN list is heavier, so expect the lower end of the rate:**
  - ANY-1/2 is a new migration with byte-for-byte parity proofs;
  - the tokens and dark theme touch 35 CSS files and about 19 SVGs, and need recaptures;
  - the Portfolio is a new tab layout.
- **At that rate the 22.7 IN units are several calendar days of agent work, not hours.** Thursday's re-assessment measures the real rate on this work.

**What bounds the pace:**
- **Your approvals.** Mockup first:
  - SR and PF need the final v7.1 mockup approved.
  - UQ-1 to UQ-3 need the v7.2 sheet, which does not exist yet (0.5 units to draw).
  - PB-1c and RM-2 need your nod.
  - No approval, no build.
- **Review gates.** One Opus review per slice; only High and Medium findings block a merge.
- **This machine (16 GB):**
  - Free RAM fell to 1.71 GB with one build plus serve, and Docker's VM crashed once at 02:05.
  - Safe limit: **3 builder lanes on targeted tests only**, and one heavy job at a time.
  - Until the Thursday demo ends, **2 lanes**, so the e3d serve and `assetops_polish_client6_test` are not disturbed.
- **Wednesday's fixed work** takes the coordinator and 1-2 lanes:
  - add-dates and the live dip capture, retakes;
  - the script pass and the DS-1f/DS-1b merge;
  - the D-E5.29-37 frontend fixes, E4-RESUME (b), KD-COVERAGE;
  - your afternoon walkthrough.
- **The end check** needs about 6-8 hours of a quiet machine: full suites, check-all, a fresh demo build (about 2 h 45 min) and live checks.

### 0.2 Lane setup and order, starting now

- **Lanes.** Three lanes at most, each in its own worktree and branch. Every lane runs targeted tests only. No full suites, no demo prepares and no recaptures until the end check.
- **Lanes A and B always run.** Lane C runs only while memory allows: the coordinator checks free RAM before each dispatch and pauses C first.
- **Lane C runs FR-B first.** FR-B was planned Wed 11-Fri 13 beside the IN work, and Wednesday's fixed work comes before both.

| Lane | Order (each item merges on review ACCEPT before the next one that depends on it starts) |
|---|---|
| **A, server and data** | PB-1a Cold analysed periods (1.0) → PB-1b EV (1.0) → PB-4, PB-7, DATA-6 + DATA-1 L2, BL-50 (1.35) → UQ-6a message seam (0.25) → ANY-1: AR-0 parity baseline, AR-1 stored rows, AR-2 board depth (3.0) → ANY-2: AR-3, AR-6 (1.5) → AR-4 money and evidence rows (2.5, after PF-C and PF-O2 merge) |
| **B, screens** | UQ-0 v7.2 sheet (0.5, then your approval) → UQ-1 tokens, type, Inter (1.25) → SR-1 shared bar (0.5, after v7.1 approval) → UQ-2 themes, UQ-3 states (1.5) → PF-C, PF-W, PF-T, PF-O2, PF-O1 (3.75) → SR-2/3, PB-1c (1.5) → UQ-4 formats (0.75) |
| **C, fixes (memory permitting)** | FR-B (about 1.0) → RM-1 roadmap words + RM-2 (0.6) → then OPTIONAL items in the section 3.3 order. Before Thursday's demo ends, lane C waits. |

**Why only one screens lane:** a second one would collide in the same files (the shell, the tokens and the Portfolio). Lane C takes the screens work that does not touch them.

**Rules that keep it safe at speed:**
1. **ANY-1's parity baseline (AR-0) is taken only after PB-1, PB-4 and PB-7 merge.** Otherwise its proofs are redone.
2. **AR-1's migration tests run in a quiet window,** never beside a build or serve.
3. **Builder briefs stay small** (code and tests first, captures last). The end check does every recapture once.
4. **Small fix rounds go to Sonnet,** and the coordinator verifies mechanical closures from the diff.

### 0.3 The end check: once, at the end

- **It runs once, after every IN item has merged:** full suites, check-all, one fresh demo build, live checks, recapture in both themes, and the PILOT-1 page with the script refresh. Your full walkthrough follows it.
- **Check-all alone runs on main after each batch of merges** (it is light).
- **No mid-way demo build.** It would test a half-built Portfolio and repeat the 6-8 heavy hours, which goes against your overnight instruction to batch heavy work at the end.
- **On Thursday morning I re-assess from the merges and the measured rate:** the order, the session date (sections 3.2 and 5), and whether any OPTIONAL items fit.

### 0.4 Approvals needed today to unblock this

1. **The final v7.1 Portfolio mockup** (`frontend/mockups/v71/portfolio-tabs.html`, with the shared date range in Change 0b). It gates SR-1 and all of PF.
2. **The v7.2 foundation sheet** as soon as it is drawn (lane B's first item). Also **Inter** as the font, and **the theme follows the computer's setting**. They gate UQ-1, which every later screens item builds on.
3. **The item 11 changes:** hide the lens chips (RM-2), the "Analysed period" line (PB-1c), the Kisiwa targets (DATA-6), and the extra Cold and EV days (DATA-11, for OPTIONAL #1).
4. **Present the session in English.** French and Swahili stay OPTIONAL, so lane B does not carry 3.25 units of catalogue work.
5. **Three lanes, with agents running overnight and at the weekend.** The coordinator keeps heavy jobs to one at a time and pauses lane C when memory is short.

### 0.5 BeagleBone (TEL-08): OPTIONAL for the client demo, after the IN items in lane C

Owner, verbatim (same file): "on a side note, i have also obtained SD card and will get the beaglebone ready by EOD today"

**Where it stands.** The spec is `.agent/build-spec-telemetry-2026-10-27.md` §TEL-08; the board ruling is `.agent/architect-beaglebone-wheezy-2026-10-29.md`.
- The field poller (`field/assetops_field`), the GX-shaped emulator and the gateway are built and proven on the laptop (TEL-01 to TEL-06).
- TEL-08 itself was never built. `host/tests/field_bench.py` has helpers only; its `setup`, `activate` and `read` commands do not exist yet.
- The board's own OS (Debian 7, Python 2.7) cannot run the code (requires Python 3.12+). Hence the SD card.

**What you do (about 30-40 min, no code):**
1. **Flash the card.** Write the official BeagleBone Black **Debian 13 IoT** microSD image (kernel 6.x, Python 3.13) from beagleboard.org to the card with Balena Etcher or Raspberry Pi Imager. If only an "eMMC flasher" image is offered, do not use it.
2. **Boot from the card.** Hold the **S2 button** while you power on (5 V 2 A barrel, or USB power). The board's own memory is left untouched, so this is reversible.
3. **Network.** Connect the board by **Ethernet to the same router as the laptop**, with internet through it (for `apt` and time sync). Do not use USB networking.
4. **Access.** Log in once (default user `debian`) and add the coordinator's SSH public key to `~/.ssh/authorized_keys`. No passwords are shared in chat. The coordinator then creates the non-root `assetops` user.
5. **Laptop firewall (admin).** Allow inbound TCP **8443** (upload server) and **5020** (device emulator) on the Private/LAN profile.
6. **Report:** the board's IP, `uname -r`, `python3 --version`, and `timedatectl show -p NTPSynchronized` (must be `yes`).

You create no upload credentials. The bench `setup` command issues the gateway's upload credential and a 7-day self-signed TLS certificate, and they are copied to the board.

**What we build and verify once it is up (about 0.75 units, plus one heavy run slot of about 1 hour):**
- **Build** `field_bench.py` `setup`, `activate` and `read`, per §TEL-08. They use their own test database, `assetops_tel_bbb_test`, never the demo database.
- **Copy** the code to `/opt/assetops/src` and record matching tree hashes on the laptop and the board. Nothing is pip-installed on the board.
- **Run** gateway and poller on the board, with the emulator and the TLS upload server on the laptop. The replay is the Kobo GX-shaped window at rate 12.
- **Gates (TEL-05):** every upload receipt COMPLETED, accepted evidence for every role, and the assessment completes.
- **Uplink fault test:** stop the laptop upload server for 5 min. The board's queue must rise and drain back to 0, with no gap in the evidence.
- **Clock:** offsets within ±50 ms on the board and the laptop.
- **Record:** a claim line, "BeagleBone Black · Debian 13 IoT · kernel … · Python … · commit … · tree …".
- **Stop and report** if Linux needs any code change, or if the clock offset cannot be met.

**Where it sits.**
- Lane C, after FR-B and RM-1/RM-2, ahead of the other OPTIONAL items.
- Its 1-hour run takes the single heavy-job slot, never beside a build, a serve or AR-1's migration tests.
- It must finish before the end check. It never touches the Thursday e3d build.
- The code copy and the clock setup can be done as soon as you report the IP. They are light.

**Why OPTIONAL, not IN:**
- **For a business buyer the value is Low-Med.** The story screens already show the readings arriving.
- **For a technical buyer, or a client asking "what hardware sits on site?", the value is Med-High.** It turns "the gateway was tested on a laptop" into "it runs on a $60 edge box and survives a 5-minute uplink loss without losing data".
- **Best use:** one slide or a 2-minute live clip in the technical script, and a pilot-readiness line in PILOT-1 ("tested on BeagleBone Black"). It is not a beat in the client story.
- **Not shown live in the session.** A live board adds a network and clock dependency to the room.
- **It moves to IN** if you tell me the client's evaluator is technical or asks about on-site hardware.

## 1. In plain words

- **The test I used:** would a client deciding whether to buy notice it, and would leaving it out make something on screen look broken, contradictory or untrue? Speed, honesty and the first impression score high. Things that only matter at 100+ Sites, in a second language nobody has reviewed, or behind sign-in score low for this session.
- **IN for the client demo: about 22.7 units** (plus FR-B this week). That is **3.3 units less than my 26-unit plan**, even though the non-Kobo fixes turned out 2.7 units bigger than the placeholder (section 3).
- **OPTIONAL, if time: about 10 units**, ranked. **AFTER the client demo:** everything else, including sign-in, multi-currency, the full UI uplift and the engineering clean-up.
- **Dates (working days from Mon 16 Nov, weekends not assumed):** the IN build work finishes **Wed 25 to Thu 26 Nov**. With 5 working days for the final build, checks, your walkthrough and the script refresh:
  - **Tue 8 Dec: all IN items fit, plus about 6-7 units of OPTIONAL items, plus a 1-unit reserve for Thursday's feedback.** Recommended.
  - **Tue 1 Dec: fits only with two cuts** (Portfolio money/evidence speed AR-4, and the dark theme), so about 19.2 units, no reserve, and the Portfolio stays on its pre-built ranges in the session.
- **Pushback, honestly:** French and Swahili (3.25 units) show nothing in an English session and cannot be switched on without reviewers you have not named yet; scale features (region, 100-Site rows, condensed dots; 1.25 units) are invisible with 4 demo Sites. I moved them out of IN. Your approvals of them stand; only the timing changes.

## 2. Every open item

Value = what a converting client would notice. Rec = IN client demo / OPTIONAL (if time, ranked in section 3.3) / AFTER. Source: W-n = your 2026-11-10 walkthrough item n; BL = backlog; owner dates as given. Sizes in build units (about half a lane-day each at today's pace).

### 2.1 Walkthrough comments not yet built

| Id | What it is | Source | Size | Depends on | Value to a converting client | Risk if left out | Rec |
|---|---|---|---|---|---|---|---|
| PB-1a | Cold room pages show their analysed periods on any day or week | W-11 | 1.0 | - | **High:** today a day or week reads "Unknown" everywhere; after, the 4.9 °C event and stock risk show | Cold pages look broken the moment anyone leaves the script | IN |
| PB-1b | The same for the EV depot (source judged per period) | W-11 | 1.0 | - | **High:** same as PB-1a | EV pages look broken off-script | IN |
| PB-1c | "Analysed period" line with links under the date bar | W-11 | 0.25 | PB-1a/b, SR-1; your nod | Med: says which hours the figures cover | figures without their period | IN |
| PB-4 | Days never analysed stop saying "Checked: nothing to report" | W-11 | 0.5 | - | Med: removes an over-claim a sharp client can catch | honesty defect on real Sites | IN |
| PB-7 | Coverage counts start when a Site's readings began, not 31 days back | W-11 | 0.25 | - | Med: "20 of the last 31 days have no readings" on a new Site reads as failure | Kisiwa looks unreliable | IN |
| DATA-6 | Kisiwa targets: avoidable generator minutes 0, unserved critical supply 0 | W-11 (story change) | 0.25 | DATA-1 (done) | Med: removes three "No objective declared" lines on the diesel story | the board looks unconfigured | IN |
| RM-1 | Unbuilt integrations read as a short roadmap ("Billing records are not connected yet") | W-11 | 0.5 | - | **High:** 16 error-looking values become a credible roadmap | pages read as broken, not as "coming" | IN |
| RM-2 | Hide the Findings lens chips on Cold, EV and Kisiwa | W-11 (needs approval) | 0.1 | your approval | Low-Med: removes dead "Not available yet" chips | a small dead end | IN if approved |
| PB-3 + DATA-11 | EV charging graded by charger status, plus an ordinary story week for Cold and EV | W-11 | 1.25 | PB-1 | Med (**High if the client runs EV or cold rooms**): the EV income card stops saying "Not known yet" beside USD 4.50; weeks show more than one event | one contradiction on the EV Grow card; presenter avoids it (D-E5.36) | OPTIONAL #1 |
| DATA-8 | Kisiwa productive loads (pump, cold store) and a price per kWh | W-11 (needs approval) | 0.5 | your approval | Med: Kisiwa's Grow card gains a figure | Grow empty on the diesel Site | OPTIONAL #4 |
| DATA-5 | Gateway health records for Cold, EV and Kisiwa | W-11 | 0.5 | Kobo Health recapture | Low-Med: Health tab shows "Unknown" x8 | Health tab not shown | OPTIONAL #5 |
| DATA-4 | EV site diagram: connector rating, grid meter | W-11 (needs approval) | 0.5 | your approval | Med for an EV client, else Low | "connector capacity not read" | OPTIONAL #6 |
| DATA-10, DATA-13, BL-48 | Kisiwa generator service plan; due dates on story Actions; Grow lines on days with no complete readings | W-11, BL | 0.65 | - | Low-Med: three small "not set" lines | minor gaps a client may ask about | OPTIONAL #7 |
| DATA-7 | Kisiwa simulated over whole days, not only 6 pm to noon | W-11 (needs approval) | 1.5 | your approval; +prepare time | Med: today every Kisiwa day is "partly" covered, the pattern you rejected for Kobo | a client asks why every day is partial | OPTIONAL #8 (decision 6) |
| DATA-12; EV revenue measure; work-record cost | Longer Cold failure window; EV revenue target; repair costs on work records | W-11 | ~0.25; ~1; ~1 (est.) | billing / work-order integration | Low: RM-1 wording covers them | none | AFTER |
| PF-C | Evidence coverage shown once on the Portfolio | W-2 | 0.5 | SR-1 | **High:** the opening page reads cleaner | repetition on the first page | IN |
| PF-T | Portfolio tabs (Overview, Act first, Outcomes by site, Opportunity, What changed, Scope & coverage) | W-2, W-5.1/5.2 | 1.0 | SR-1, UQ-3, v7.1 approval | **High:** the opening page | crowded first page | IN |
| PF-W | "Checked" becomes complete / partial / too few / no readings received / still processing / not analysed yet | W-3, W-5.3 | 0.75 | - | **High:** "7 of 8 hours checked" stops implying the system failed to look | the main coverage words confuse | IN |
| SR-1..3 | One shared date range at the top of every page; left menu unchanged | W-4, W-12.5 | 1.75 | v7.1 approval, UQ-1 | **High:** one control, any page, any range | each page keeps its own date form | IN |
| PF-O1, PF-O2 | Scalable "Outcomes across the estate", grouped by outcome | W-9, W-12.1/12.3 | 1.5 | PF-T | Med-High: the list shows it will handle a large estate | grid looks cramped as Sites grow | IN |
| PF-O3 | Overview card dots condense above 8 Sites | W-9 | 0.25 | PF-O1 | Low: invisible with 4 Sites | none in the demo | AFTER |
| PF-R | Region attribute on Sites, with filter and grouping | W-12.2 | 0.25 | region values | Low: the control is hidden until Sites have regions | none with 4 Sites | AFTER (IN if the client asks about regions) |
| AR-7 | Outcome rows from stored rows (for 100+ Sites) | W-9 | 0.75 | ANY-2 | Low: invisible under about 25 Sites | none in the demo | AFTER |
| T-5.4 | "Complete readings" threshold per portfolio (80% today, one global file) | W-5.4 | ~0.5 (est.) | tenant settings | Low | none | AFTER |
| T-5.5 | Outcome map as a config file (today a reviewed code table) | W-5.5 | ~0.75 (est.) | - | Low: the client never sees it | none | AFTER |
| FCF-1 | Findings card counts Cold/EV "awaiting verification"; Portfolio Cold/EV rows read "Action agreed" (with BL-47) | W-7 | 1.0 | FC (done) | Med: removes the "mini-grid Sites only" note and a gap between screens | the note stays, which is honest | OPTIONAL #2 |
| D-E5.25 | An "Act first" count on the Findings page | W-7 | 1.0 | - | Low | none | AFTER |
| PR-1/2a | Price-it, first step: "Set a price" / "What is needed" on every unpriced item, and a read-only price page with history | W-10, W-12.4 | 0.75 | mockup first | Med-High for a commercial buyer: answers "how would I price this?" on screen | presenter answers verbally; the admin tool exists | OPTIONAL #3 |
| PR-2b..5 | Price-it editing: sign-in write path, recalculation, model blocks | W-10 | 2.0 | BL-54 sign-in | Med | - | AFTER |
| UQ-0..4 | Design foundation: v7.2 sheet, tokens, 12/14 px type, Inter, light and dark themes, empty/loading states, number and date formats | W-12.1, W-13 | 4.0 | v7.2 approval | **High:** first impression, "modern" | the app looks dated next to the story | IN (dark theme cut on 1 Dec) |
| UQ-6a | Server words stored as message keys, not sentences | W-13 | 0.25 | - | none visible | stored speed rows rebuilt later (~1-2 units) | IN |
| UQ-5, 6b, 7, 8 | French and Swahili: all words into catalogues, drafts, long-text guard | W-13 | 3.25 | reviewers named | Low unless the client works in French or Swahili; nothing changes in English | none in an English session | OPTIONAL #9 (decision 2) |
| BL-69 rest | Component library, chart standard, page-by-page uplift, accessibility pass | W-12.1 | ~7.25-8.0 | UQ | Med, long term | - | AFTER (first focused work after) |
| BL-67 | Several currencies, structured tariffs, restatement notes | W-1 | 3.0-3.5 | your currency answers | Low now: demo Sites use one flat price each | - | AFTER |

### 2.2 Backlog items

| Id | What it is | Source | Size | Depends on | Value to a converting client | Risk if left out | Rec |
|---|---|---|---|---|---|---|---|
| ANY-1 (BL-66) | Site boards fast for any range (under 2 s) | owner 11-03, 11-10 | 3.0 | PB-1, PB-4, PB-7, UQ-6a | **High:** off-script boards take 10-36 s today | "try another week" stalls live | IN |
| ANY-2 core (BL-66: AR-3, AR-6, AR-4 with money receipts) | Portfolio fast for any range; Cold/EV boards under 1 s | owner 11-10 | 4.0 | ANY-1, PF-C, PF-O2 | **High:** the Portfolio is the opening page | presenter stays on pre-built ranges | IN (AR-4 cut on 1 Dec) |
| AR-5 (BL-66, with BL-64/65) | Retire pre-loading | - | 0.75 | ANY-2 | none visible | - | AFTER |
| BL-50 | Site "Why?" sees the same issues as the board | BL | 0.25 | - | Med: "Why?" is a presented beat; on the Cold failure day it misses one issue | "why" gets an incomplete answer | IN |
| DATA-1 L2 | Kisiwa finish check covers windows without a selection | DATA-1 review | 0.1 | - | none; protects the build | a bad Kisiwa day slips into the build | IN |
| PILOT-1 (new) | One page in the client script: how a client starts (onboarding steps, integration ranking D-E5.35, what sign-in adds) | Architect | 0.25 | RM-1 | **High:** a converting client asks "what happens next?" | no path to pilot on paper | IN |
| BL-54 | Sign-in, named users and roles | BL | not sized (~3-5) | - | Med: asked about, answered by PILOT-1 | - | AFTER (pilot-critical) |
| BL-53, 55, 57, 59 | Real-source clock proof; production scheduler and onboarding runbook; public upload path for the demo build; historical data import | BL | not sized | BL-54 for some | Med as questions; PILOT-1 answers them | - | AFTER (pilot-critical) |
| BL-31, BL-45 | A real later "Change made" for Cold/EV; mill Actions on the Site boards | BL | 0.5; 1.0-1.5 | - | Low-Med: the script uses Kobo and the mill route | - | AFTER |
| BL-13, BL-16, BL-56 | Days line under board rows; idle fuel in the Kobo generator law (disclosed); demo banner only on demo data | BL | 0.25; 1.0; ~0.1 | - | Low | - | AFTER |
| BL-01..05, 08, 11, 12, 15, 22, 35, 51, 58 | Clean-up, refactors, renames and internal guards | BL | ~4.0 | - | none visible | - | AFTER |
| BL-06, 07, 09, 10, 14, 17, 18, 20, 21, 23-26, 32-34, 36-44 | Story-depth edge cases not on the script (each has a presenter rule) | BL | ~5+ (several unsized) | - | Low: only off-script | covered by "present less" rules | AFTER |
| BL-30, 46, 49, 52, 60-63 | Demo tooling and test debt (BL-63 is a producer fix the build check already covers) | BL | ~1.5 | - | none visible | - | AFTER |

## 3. Sequence of the IN items

### 3.1 Two lanes (pace about 1.5 units per lane per working day, including review and one fix round; 1.25 when slow)

Lane A, server and data (10.6 units):

| # | Item | Size | Cum. | Done by (1.5/day) |
|---|---|---|---|---|
| A1 | PB-1a Cold analysed periods | 1.0 | 1.0 | Mon 16 |
| A2 | PB-1b EV analysed periods | 1.0 | 2.0 | Tue 17 |
| A3 | PB-4, PB-7, DATA-6 + DATA-1 L2, BL-50 | 1.35 | 3.35 | Wed 18 |
| A4 | UQ-6a server message seam | 0.25 | 3.6 | Wed 18 |
| A5 | ANY-1: AR-0 parity baseline, AR-1 stored rows, AR-2 board depth | 3.0 | 6.6 | Fri 20 |
| A6 | ANY-2: AR-3 coverage rows, AR-6 work lists | 1.5 | 8.1 | Mon 23 |
| A7 | ANY-2: AR-4 evidence and money rows with receipts (MN-1/2/3) | 2.5 | 10.6 | Wed 25 (Thu 26 slow) |

Lane B, screens (10.35 units; UQ-0 this week):

| # | Item | Size | Cum. | Done by (1.5/day) |
|---|---|---|---|---|
| B0 | UQ-0 v7.2 foundation sheet (you approve it by Mon 16) | 0.5 | 0.5 | Fri 13 |
| B1 | UQ-1 tokens, type, Inter, style ratchet | 1.25 | 1.75 | Mon 16 |
| B2 | SR-1 shared date bar (v7.1 approved by Tue 17) | 0.5 | 2.25 | Tue 17 |
| B3 | UQ-2 light and dark themes; UQ-3 empty and loading states | 1.5 | 3.75 | Wed 18 |
| B4 | PF-C, PF-W, PF-T, PF-O2, PF-O1 (Portfolio tabs, words, outcomes list) | 3.75 | 7.5 | Fri 20 |
| B5 | SR-2/3 every page on the shared range; PB-1c analysed-period line | 1.5 | 9.0 | Mon 23 |
| B6 | UQ-4 formats; RM-1 roadmap words; RM-2 | 1.35 | 10.35 | Tue 24 (Wed 25 slow) |

Shared: PILOT-1 0.25 (with the script refresh) and E-final 1.5 (one demo build, end-game suites, live checks, recapture in both themes, both scripts refreshed). **IN total: 10.6 + 10.35 + 0.25 + 1.5 = 22.7 units.**

Why this order (causal, not convenient):
1. PB-1, PB-4 and PB-7 change what boards compose, so they land before AR-0 takes its byte-for-byte baseline; otherwise ANY-1's proofs are redone.
2. UQ-6a lands before AR-1 freezes the stored-row shape (words as keys from day one).
3. **Changed from the 26-unit plan:** lane B now builds the Portfolio (B4) before moving every page to the shared range (B5), so PF-C and PF-O2 are merged by Fri 20 and AR-4 (which touches the same Portfolio read) never waits.
4. SR-1 before PB-1c, UQ-2 and UQ-4: the top bar is laid out once. SR-2 after PB-1: Cold and EV "latest event inside the range" uses PB-1's rule.
5. UQ-1 and UQ-3 before the Portfolio, so it is written on the new tokens and states and never restyled.
6. OPTIONAL items fill gaps: lane A after A7, lane B after B6.

### 3.2 Date cut-offs (working calendar; no demo build is prepared on the 3rd-5th of a month)

E-final needs **5 working days**: (1) freeze, end-game suites, fixes; (2) demo build and live checks; (3) recapture and script refresh with PILOT-1; (4) your walkthrough; (5) one fix round and rebuild, or buffer. The final build is prepared the day before the session so "yesterday arrives" can be shown live.

| Session | Build freeze | E-final days | What fits |
|---|---|---|---|
| **Tue 1 Dec** | Tue 24 Nov | Wed 25, Thu 26, Fri 27, Mon 30 (prepare Mon 30) - only 4 days, no buffer | IN minus AR-4 (2.5) and UQ-2 dark theme (1.0) = **about 19.2 units**. Portfolio money and evidence stay computed on request: presenter stays on pre-built Portfolio ranges. No OPTIONAL items, no reserve for Thursday's feedback. You approve v7.2 and v7.1 by Mon 16. |
| **Tue 8 Dec (recommended)** | Mon 30 Nov | Tue 1, Wed 2 (rehearsal build allowed on the 2nd), Thu 3, Fri 4 (walkthrough, script), Mon 7 (final prepare) | **All IN (22.7)**, plus about 6-7 OPTIONAL units in the 3 spare lane-days (Wed 25 to Mon 30), plus a 1-unit reserve for Thursday's associates' feedback. |

A session on Thu 3 or Fri 4 Dec is possible only with the final build on Wed 2 and no slip at all; I do not recommend it.

### 3.3 OPTIONAL ranking (what to add, in order, if the 8 Dec date is set)

1. PB-3 + DATA-11 (1.25, lane A): first if the client runs EV or cold rooms.
2. FCF-1 with BL-47 (1.0, lane A).
3. PR-1/2a price-it first step (0.75, lane B; mockup first).
4. DATA-8 Kisiwa productive use and price (0.5; needs approval).
5. DATA-5 health records (0.5). 6. DATA-4 EV diagram (0.5; approval). 7. DATA-10, DATA-13, BL-48 (0.65).
8. DATA-7 Kisiwa whole days (1.5; approval; adds prepare time).
9. French and Swahili (3.25): only if a reviewer is named by Fri 20 Nov and the client prefers that language.

With 8 Dec, items 1-7 fit (about 5.2 units, at the slower pace) plus the 1-unit reserve; 8 and 9 fit only if the build runs at the faster pace and the reserve is unused.

## 4. Where the 26-unit plan changes, and why

| Change | Units | Why |
|---|---|---|
| Non-Kobo fixes: placeholder 1.5 becomes 4.2 (PB-1a/b/c, PB-4, PB-7, DATA-6, RM-1, RM-2, BL-50, L2) | +2.7 | The audit reported. PB-3 goes to OPTIONAL with DATA-11: alone it shows nothing, because the EV story has only 16 min of charger status. |
| French and Swahili catalogue work (UQ-5, 6b, 7, 8) to OPTIONAL | -3.25 | Nothing changes on screen in English, no reviewer is named, and the release rule keeps both languages off until reviewed. The seam (UQ-6a) and formats (UQ-4) stay IN, so nothing is redone later. |
| AR-5 and AR-7 to AFTER | -1.5 | Invisible with 4 Sites; the in-memory outcomes route is correct up to about 25 Sites. |
| FCF-1 to OPTIONAL | -1.0 | It was already cut #2; the card's "mini-grid Sites only" note is honest. |
| PF-O3 and region to AFTER | -0.5 | Invisible with 4 demo Sites. |
| PILOT-1 added | +0.25 | A converting client needs a path to a pilot; RM-1 and the integration ranking make one page cheap. |
| Lane B order: Portfolio before SR-2 | 0 | AR-4 no longer waits for the Portfolio. |
| Calendar | - | Earlier "earliest credible Mon 30 Nov" is withdrawn: full IN needs Tue 8 Dec; 1 Dec only with the section 3.2 cut. |
| **Net** | **26.0 to 22.7** | |

## 5. Your decisions that change the scope (my recommendation in bold)

1. **Client session date. Recommend Tue 8 Dec.** 1 Dec drops Portfolio any-range speed (AR-4) and the dark theme, with no buffer and no room for Thursday's feedback.
2. **French and Swahili before the session? Recommend no: present in English.** Keep the approval; build the catalogues after the session, or as OPTIONAL #9 only if you name a native Swahili and a fluent French reviewer by Fri 20 Nov and the client prefers that language.
3. **What does the client operate (diesel or solar mini-grids, cold rooms, EV depots)? Recommend telling me before Mon 23.** If EV or cold rooms, PB-3 + DATA-11 and DATA-4 move up to IN; if mini-grids, Kobo and Kisiwa lead (D-E5.36) and DATA-8 moves up.
4. **Approve the v7.2 foundation sheet and Inter by Mon 16, and the final v7.1 Portfolio mockup by Tue 17. Recommend yes, theme follows the computer's setting.** Each day of delay moves lane B and the date by a day.
5. **Approve the item 11 story and screen changes: RM-2 hide lens chips, the "Analysed period" line, Kisiwa targets, extra Cold and EV days. Recommend yes to all.**
6. **Kisiwa whole-day simulation (DATA-7, 1.5) and productive use (DATA-8, 0.5). Recommend DATA-8 yes (OPTIONAL #4), DATA-7 after the session**, with a presenter line: "Kisiwa's recorder in this story runs 6 pm to noon, so each day is partly covered." If you find that as indefensible as the Kobo pattern, DATA-7 moves into the reserve.
7. **Scale and region (PF-O3, region, AR-7). Recommend after**, unless the client has more than about 8 Sites or asks about regions; the demo data has no large estate to show it on.
8. **Per-portfolio threshold and outcome-map config file. Recommend after**; neither is visible to a client.
