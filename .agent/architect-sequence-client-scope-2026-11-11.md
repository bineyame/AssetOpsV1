# Architect: one sequenced view of walkthrough comments and backlog, for the client-demo scope (2026-11-11)

- Architect: Claude (`assetops-architect`). Binding checked in `.ai/ROLE_CONFIG.md`: Architect = Claude since 2026-10-27.
- Owner, verbatim (`.agent/owner-client-scope-sequencing-2026-11-11.md`): "the architect need to sequence the walkthough comment implementations as well as overall backlog so i can see what is worth putting in scope of client demo"
- Inputs: `owner-walkthrough-2026-11-10.md` (items 1-13), `backlog-post-demo.md` (BL-01..69), `architect-plan-pre-client-2026-11-10.md` (the ~26-unit plan), `architect-answer-non-kobo-sites-2026-11-10.md` (item 11 audit), the 2026-11-10 answers on speed, money, layout, price-it and UI quality, `coordinator-handoff.md`.
- **Status:** a recommendation. Nothing is scheduled until you decide (section 4). No code changes.
- Already merged, so not in the table: Kobo gap pattern, lens keeps the page and pre-built lens pages, Findings cards, Cold/EV analysed-period story links, Kisiwa one recording session, the E5 fixes, C1-C5. The Wednesday frontend fixes (Kisiwa chart legend, copy batch, Fuel tab loading; 0.6 units) are planned before Thursday; if any slips, it goes first in lane B on Mon 16.

## 0. By Friday 13 Nov (added 2026-11-11 after your reply; it replaces the calendar in sections 1 and 3.2, the scope and order stay)

Owner, verbatim (`.agent/owner-units-by-friday-2026-11-11.md`): "the time estimates are for human developement, we should be able to do the indicated units in time for Friday"

**Short answer: you are right that my calendar was too slow, and wrong that 22.7 units fit by Friday.** I sized lanes at 1.5 units per *working* day; agents run most of the 24 hours and every day of the week. On the evidence below, all IN items can be built by about **Tue 17 to Thu 19 Nov**, not 25-26 Nov. **By Friday 13, about 8.5 IN units plus FR-B land**, not 22.7.

### 0.1 What agents actually delivered (git log on main, 8-11 Nov)

| Day | Merged slices (unit sizes from the build sheets; a few estimated) | Units merged | What else that day used |
|---|---|---|---|
| Sun 8 | Kisiwa K4b, K5, K6a, K6b, K6c, K7-D/F, K8, K9, K10; G3a; R-1; idle fuel A3 | about 7 | four lanes, owner away, specs already closed |
| Mon 9 | G1 1.75, G2 2.25, G3b 1.25, R4.1, POLISH-1, E2 fix A, C1-C4 (about 2.0) | about 8 | G1-G3b were built mostly on Sun 8; E2 suites and E3 build |
| Tue 10 | C5, E5-FX, FX-EV-TITLE, FX-COLD-LINKED, FX-KOBO-GAPS 0.6, V3, PL-1, PL-2, DATA-2, FC 0.75 | about 3.8 | E3c/E4 checks, your walkthrough, six Architect answers |
| Wed 11 (to 05:00) | DATA-1 0.5 | 0.5 | E3d demo build |

- **Average: about 6 units per calendar day across 3-4 lanes, about 1.75 per lane per day, and only about 4 on a day with a build and a walkthrough.** 110 review commits and 34 fix commits in four days: most slices get one fix round, and DATA-1, PL-1 and FX-COLD-LINKED were each rejected once first.
- **Those were small fixes to closed specs.** The IN list is heavier: ANY-1/2 is a new migration with byte-for-byte parity proofs; the design tokens and dark theme touch 35 CSS files and ~19 SVGs and need recaptures; the Portfolio is a new tab layout. Expect the lower end of the rate.
- **What bounds it:**
  - **Your approvals.** Mockup first: SR and PF need the final v7.1 mockup approved; UQ-1 to UQ-3 need the v7.2 sheet, which does not exist yet (0.5 to draw); PB-1c and RM-2 need your nod. No approval, no build.
  - **Review gates.** One Opus review per slice; only High and Medium findings block.
  - **This machine.** 16 GB. Free RAM fell to 1.71 GB with one build plus serve, and Docker's VM crashed once at 02:05. Safe limit: **3 builder lanes on targeted tests**, and one heavy job at a time. Thursday morning the e3d serve and `assetops_polish_client6_test` must not be disturbed: 2 lanes until the demo ends.
  - **Wednesday's fixed work** (add-dates and live dip capture, retakes, script pass and DS-1f/DS-1b merge, D-E5.29-37 frontend fixes, E4-RESUME (b), KD-COVERAGE, your afternoon walkthrough) takes the coordinator and 1-2 lanes all day.
  - **The end check** (full suites, check-all, a fresh demo build of about 2 h 45 min, live checks) needs about 6-8 hours of a quiet machine.

### 0.2 The by-Friday plan (3 lanes at most, each in its own worktree)

| Lane | Wed 11 | Thu 12 (2 lanes until the demo ends) | Fri 13 | Lands by Fri 13 |
|---|---|---|---|---|
| A, server | PB-1a Cold analysed periods (1.0) | PB-1b EV (1.0) | PB-4, PB-7, DATA-6 + L2, BL-50 (1.35); UQ-6a (0.25) | 3.6 |
| B, screens | UQ-0 v7.2 sheet (0.5), for your approval by Thu noon | UQ-1 tokens, type, Inter (1.25); SR-1 shared bar (0.5) after v7.1 approval | UQ-3 states (0.5); PF-C + PF-W coverage once and new words (1.25) | 4.0 |
| C, fixes | FR-B starts (about 1.0) | FR-B ends; RM-1 roadmap words (0.5) + RM-2 (0.1) | review and fix rounds for A and B | FR-B + 0.6 |
| **Total** | | | | **about 8.2 IN units (8.5 with PILOT-1 in the script pass) + FR-B** |

**Does not land by Friday, and why:**
- **ANY-1 (3.0):** its parity baseline must be taken after PB-1, PB-4 and PB-7 merge (Fri). AR-1 is a migration that needs a quiet machine for its Postgres tests. Earliest finish Sun 15.
- **ANY-2 core (4.0):** needs ANY-1's stored rows and the Portfolio server parts. Earliest finish Tue 17.
- **UQ-2 dark theme, UQ-4 formats, PF-T tabs, PF-O outcomes list, SR-2/3, PB-1c (about 6.0):** they queue behind UQ-1, SR-1 and your approvals in the one screens lane. A second screens lane would collide in the same files (the shell, tokens and Portfolio). Earliest finish Mon 16 to Tue 17.
- **E-final (1.5):** must be last, once.

### 0.3 When the end check runs

- **Recommended: once, after all IN items merge, about Wed 18 Nov**: full suites, check-all, one fresh demo build, live checks, recapture and script refresh. Your full walkthrough is then about **Thu 19 Nov**, a fix round Fri 20, and **a client session from about Mon 23 Nov** is credible. **Tue 1 Dec is now safe with every IN item and most OPTIONAL items**, and 8 Dec is no longer needed for scope.
- **A Friday end check is not recommended.** It would test a half-built Portfolio and repeat the 6-8 heavy hours next week, which goes against your overnight instruction to batch heavy work at the end. On Friday night only check-all runs, on main.

### 0.4 Approvals needed today to keep this pace

1. **The final v7.1 Portfolio mockup** (`frontend/mockups/v71/portfolio-tabs.html` with the shared date range, Change 0b). It gates SR-1 Thursday and PF Friday.
2. **The v7.2 foundation sheet, by Thu noon** (drawn Wednesday), with **Inter** and **theme follows the computer's setting**. It gates UQ-1.
3. **The item 11 changes:** RM-2 hide lens chips, the "Analysed period" line (PB-1c), Kisiwa targets (DATA-6), extra Cold and EV days (DATA-11).
4. **Present in English** (French and Swahili stay OPTIONAL).
5. **Three lanes and weekend agent runs**, so ANY-1 runs Sat-Sun; the coordinator holds heavy jobs to one at a time.

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
