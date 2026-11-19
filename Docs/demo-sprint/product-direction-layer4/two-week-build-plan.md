# The first fortnight's build: as far along Figure 10 as fourteen days can go

**AssetEcon · Layer 4 pack document 6b · AssetOps Architect (Claude) · 19 Nov 2026 · derived from design rev 16.7 and `delivery-plan.md`**

**The owner's direction** (`.agent/owner-recreate-document-packs-2026-11-19.md`): the fortnight is to be recreated "focussed on advancing as much as possible towarfs the new features, not the markting element". So this is a build schedule and nothing else. It has no selling track, no demo days and no offer kit. Day 1 is the first build day after the owner approves the recreated pack.

**How to read it.** Every table marked *(computed)* is produced by `plan_model.py`, and `python3 plan_model.py --check` fails if any table or headline figure here differs from the model. The slices are `delivery-plan.md`'s, cited by ID. Their gates are stated there and not restated here.

*Serves the objective:* every day of the fortnight moves a feature that executives will see onto the screen sooner: Findings on their factors, money from records, a decision against no action, and the plan's approval.

## 1. The aim, and the headline
<!--derives: §2.9; Figure 10; OD-9; plan_model-->

**The aim** is the furthest point on Figure 10 that capacity allows, built in delivery order. That means step 1, then step 2's format and leaf IDs, then lanes 3A, 3B and 3C together, then the join, and then as far towards steps 5–8 as the lanes can reach.

**The headline, at the planning pace:**
- **4 build lanes** run from day 1. The heavy-tool slot pool (`T1`, numbered `B03` in `two-week-conversion-plan.md`) merges first, so lanes 3 and 4 open as soon as it lands.
- By day 14, 111.5 units land in 37 slices, of which 32 slices committed land by day 12.
- **Figure 10 is complete through step 4.** Steps 1, 2, 3A, 3B, 3C and the join are all built.
- **Step 6 is also complete,** because cost-side decisions start before the join (design §2.9). That means the Kobo decision view, with options against no action, and Mto's demand and repair decisions.
- **Steps 5, 7 and 8 are partly built.** Targets, attribution, the plan's records, release and spend steps, and the economic and causal verdicts land; their screens are stretch.
- **Calibration:** replays K and M land, and E is stretch.
- **At the observed pace,** the stretch line reaches step 8: the bridge on screen, Act first with the plan, and the three verdicts on What changed.
- **Step 9 waits** for the next fortnight in every case.

## 2. Capacity: the machine, the lanes and the people
<!--derives: plan_model; D11-->

**Capacity** (computed):

<!--table:capacity-->
| Resource | Basis | Figure |
|---|---|---|
| Machine | measured, 18 Nov | 14 GB available of 22 GB with the walkthrough server, lab_app, Postgres and the coordinator running; no swap |
| Memory budget for agents and tools | available less 2 GB headroom (assumption) | 12 GB |
| One heavy database job | assumption, not measured; measured on the first live build before lanes 3 and 4 open | 1.5 GB (pessimistic case 3.1 GB) |
| Worst case, 4 build lanes, heavy tools pooled | every agent resident; the two heavy slots full | 11 GB: margin 1 GB to the budget (0.6 GB in the pessimistic case) |
| Worst case, 3 build lanes, not pooled | check-all's two slots full, the database job beside them, every other agent running tsc | 13.22 GB: does not fit |
| **Build lanes** | the largest count that fits, capped by W4 as amended | **4** with the slot pool (lanes 3 and 4 open when it merges); 2 without |
| Observed pace | 237 task merges in 26.29 days, 1.88 branches open on average | 4.8 units per lane-day |
| Planning pace | about 0.6 of observed: new schema and money, discovery reviews, checks first, four lanes merging | 3 units per lane-day (slip case 2) |
| Rework allowance | explicit, on top of the pace | every unit takes 1.15 units of lane time |
| Reviewer stream | one fresh-review slot, 14 h a day; 59 in 100 units need a discovery review | 18.1 units a day; 66 in 100 busy at the planning pace |
| Build capacity in 14 days | 4 lanes at the planning pace, less rework | about 146 units |
<!--/table-->

**How to read it.**
- **Memory sets the lane count, not CPU.** The machine has no swap, so the build is sized to the worst case: every agent resident and both heavy slots full. Four lanes fit only with the slot pool. That is why the pool is the first slice and lanes 3 and 4 open when it merges, as W4 is amended (owner, sitting 1, item 7: "yes").
- **The pace is measured, then cut, then rework is added.** 237 task merges in about 26 days, with fewer than two branches open on average, is 4.8 units per lane-day. That is an upper bound, because it starts at each branch's first commit.
- **This fortnight is new schema and money work,** with discovery reviews and checks written first, so the schedule uses 3 units per lane-day. On top, every unit carries a 15 in 100 rework allowance.
- **The reviewer stream is the next limit.** One review slot is busy about two thirds of the day at the planning pace. Above that pace a builder pauses rather than skip a review (W5).

**People.**
- **The Architect** writes the structure pages (§4) and answers the builders' batched questions.
- **The coordinator** merges, and runs check-all on `main` after each merge.
- **The owner** approves the structure pages at two sittings and walks the built screens on day 14 (§4).

## 3. Scope, ranked by step
<!--derives: §2.9; Figure 10; OD-9; plan_model-->

**Ranked in delivery order.** Every slice is ranked by its Figure 10 step first, then by the work it unlocks. The slot pool comes first of all, and the walkthrough database goes to the first free lane on day 13. Nothing is ranked by how it would look in a demo. The slices, their units and their dependencies are in `delivery-plan.md` §2.

**Where each step stands on day 14** (computed):

<!--table:steps-->
| Step | Slices | Units | Done by day (planning pace) | Done by day 14 at slip · planning · observed pace |
|---|---:|---:|---|---|
| Tooling: the heavy-tool slot pool | 1 | 2.5 | day 1 | yes · yes · yes |
| 0 Calibration replays K, M, E | 3 | 15 | after day 14 | 70 in 100 units · 70 in 100 units · yes |
| 1 Correct the last-day figure | 2 | 6.5 | day 4 | yes · yes · yes |
| 2 Canonical format and leaf factor IDs | 1 | 1.5 | day 3 | yes · yes · yes |
| 3A Sources | 5 | 13.5 | day 8 | yes · yes · yes |
| 3B Structure | 6 | 17.5 | day 9 | yes · yes · yes |
| 3C Recorded person | 3 | 9.5 | day 10 | yes · yes · yes |
| 4 Join at the money leaves | 2 | 5 | day 10 | yes · yes · yes |
| 5 Targets and the bridge | 4 | 10 | after day 14 | 0 in 100 units · 70 in 100 units · yes |
| 6 Decisions and options | 7 | 21.5 | day 14 | 37 in 100 units · yes · yes |
| 7 The plan and the Portfolio | 8 | 27 | after day 14 | 19 in 100 units · 43 in 100 units · yes |
| 8 Three verdicts | 3 | 8.5 | after day 14 | 0 in 100 units · 47 in 100 units · yes |
| 9 Rights, cold then EV, pilot onboarding | 5 | 24.5 | after day 14 | 0 in 100 units · 0 in 100 units · 0 in 100 units |
| The day-14 walkthrough database | 1 | 1 | day 13 | yes · yes · yes |
<!--/table-->

**What is not in the fortnight, and why.**
- **Step 9,** rights, then cold rooms and EV depots, follows proof and the plan (Figure 10).
- **Pilot onboarding** waits for an operator's consent and data.
- The **selling work** is out of scope by the owner's direction.

## 4. The fourteen days
<!--derives: D11; Figure 10; plan_model-->

**Structure first (W1).** No slice builds before the owner approves its structure page. The pages are written from the recreated pack, so most take a quarter or half of a day.
- **Steps 1 and 3C are approved with the pack.** Their structure is already the pack's: design CH5 and CH2, and `plan-and-action-workflow.md`. So their slices start on day 1. This is an Architect's call for the owner (§7, question 1).
- **The sitting days are searched by the model.** It picks the days that land the most work by day 14, then the furthest step, then the fewest sittings. The result is sittings on days 2 and 4.

**Structure pages** (computed):

<!--table:pages-->
| Page | Covers | Architect lane-days | Approved |
|---|---|---:|---|
| P1 | Steps 1 and 3C: the corrected figure; the person on every command (pack #2, #12) | 0 | with the pack, before day 1 |
| P2 | Step 2: canonical format version 1 and the leaf factor IDs | 0.5 | sitting 1, day 2 |
| P3A | Step 3A: record kinds, intake, emulator rules, the contract test | 0.25 | sitting 1, day 2 |
| P3B | Step 3B: registry rows, parity, the structure read and observer | 0.25 | sitting 1, day 2 |
| P5 | Step 5: target declaration and the attribution rules | 0.5 | sitting 2, day 4 |
| P6 | Step 6: decision records, bounds, the evaluator and the carrier | 0.5 | sitting 2, day 4 |
| P7 | Step 7: plan records, release, versions, the proposal (pack #12) | 0.5 | sitting 2, day 4 |
| P8 | Step 8: economic and causal verdicts | 0.25 | sitting 2, day 4 |
| P9 | Step 9: rights rows and the claim case; cold and EV records | 0.75 | after day 14 |
<!--/table-->

**Day by day, at the planning pace** (computed; ✓ marks the day a slice merges):

<!--table:days-->
| Day | Lane 1 · sources and money | Lane 2 · structure and the plan's records | Lane 3 · person, decisions and proof | Lane 4 · screens and tooling | Owner |
|---|---|---|---|---|---|
| 1 | — | — | — | `T1` ✓, `1a`, `1b` | reads 3 pages for sitting 1 |
| 2 | — | `2a`, `3B1` | `0K` | `1a` ✓, `1b` | sitting 1 |
| 3 | `3A1` | `2a` ✓, `3B1` | `0K` | `1b` | reads 4 pages for sitting 2 |
| 4 | `3A1`, `3A2` | `3B1`, `3B3` | `0K`, `3C1` | `1b` ✓, `3A5` | sitting 2 |
| 5 | `3A1` ✓, `3A2`, `3A3` | `3B1` ✓, `3B3`, `3B6`, `3B2` | `0K` ✓, `3C1`, `3C2` | `3A5`, `0M` | — |
| 6 | `3A2` ✓, `3A3`, `3A4` | `3B3` ✓, `3B6` ✓, `3B2`, `3B4` | `3C1` ✓, `3C2`, `6a` | `3A5` ✓, `0M`, `3B5` | — |
| 7 | `3A3` ✓, `3A4`, `4b` | `3B2` ✓, `3B4`, `7a` | `3C2` ✓, `6a`, `6d` | `0M` ✓, `3B5` | — |
| 8 | `3A4` ✓, `4b`, `4a` | `3B4` ✓, `7a` | `6a` ✓, `6d`, `6e` | `3B5`, `3C3` | — |
| 9 | `4b` ✓, `4a`, `5a` | `7a`, `7b` | `6d` ✓, `6e`, `6c` | `3B5` ✓, `3C3` | — |
| 10 | `4a` ✓, `5a`, `7d` | `7a` ✓, `7b` | `6e` ✓, `6c` | `3C3` ✓, `5d` | — |
| 11 | `5a` ✓, `7d`, `6g` | `7b`, `5b` | `6c`, `6b`, `8a` | `5d`, `6f` | — |
| 12 | `7d` ✓, `6g` | `7b` ✓, `5b`, `WK`, `7c` | `6c` ✓, `6b` ✓, `8a` | `5d` ✓, `6f` | — |
| 13 | `6g`, `0E` | `5b` ✓, `WK` ✓, `7c` | `8a`, `8b` | `6f`, `5c` | reads the day-14 pack |
| 14 | `6g` ✓, `0E` | `7c`, `7h` | `8a` ✓, `8b` | `6f` ✓, `5c`, `7e` | walkthrough of the built screens and the next ranked list |
<!--/table-->

**The fortnight on one chart** (computed). Bars marked critical are committed: they land by day 12.

<!--diagram:fortnight-->

<!--table:gantt-->
```mermaid
gantt
  title The fortnight at the planning pace (days from day 1)
  dateFormat X
  axisFormat %s
  section Sources and money
  3A1 B3 :crit, g3A1, 3.45, 4.6
  3A2 B3 :crit, g3A2, 4.6, 5.75
  3A3 B3 :crit, g3A3, 5.75, 6.9
  3A4 B3 :crit, g3A4, 6.9, 7.67
  4b B1 :crit, g4b, 7.67, 8.62
  4a B1 :crit, g4a, 8.62, 9.58
  5a B2 :crit, g5a, 9.58, 10.73
  7d P :crit, g7d, 10.73, 11.69
  6g CH3 :g6g, 11.69, 13.23
  0E CH3 :g0E, 13.23, 14.0
  section Structure and the plan's records
  2a B3 :crit, g2a, 2.0, 2.58
  3B1 B1 :crit, g3B1, 2.58, 4.11
  3B3 B1 :crit, g3B3, 4.11, 5.26
  3B6 B1 :crit, g3B6, 5.26, 5.83
  3B2 CH1 :crit, g3B2, 5.83, 6.79
  3B4 CH1 :crit, g3B4, 6.79, 7.75
  7a P :crit, g7a, 7.94, 9.86
  7b P :crit, g7b, 9.86, 11.39
  5b B2 :g5b, 11.39, 12.54
  WK tooling :gWK, 12.54, 12.92
  7c P :g7c, 12.92, 14.0
  section Person, decisions and proof
  0K CH3 :crit, g0K, 2.0, 4.68
  3C1 CH2 :crit, g3C1, 4.68, 5.83
  3C2 CH2 :crit, g3C2, 5.83, 6.79
  6a CH3 :crit, g6a, 6.79, 7.94
  6d CH3 :crit, g6d, 7.94, 8.9
  6e CH4 :crit, g6e, 8.9, 9.86
  6c CH3 :crit, g6c, 9.86, 11.01
  6b CH3 :crit, g6b, 11.01, 11.97
  8a CH4 :g8a, 11.97, 13.5
  8b CH4 :g8b, 13.5, 14.0
  section Screens and tooling
  T1 tooling :crit, gT1, 0.0, 0.96
  1a CH5 :crit, g1a, 0.96, 1.92
  1b CH5 :crit, g1b, 1.92, 3.45
  3A5 B3 :crit, g3A5, 4.6, 5.56
  0M CH3 :crit, g0M, 5.56, 6.9
  3B5 B1 :crit, g3B5, 6.9, 8.43
  3C3 CH2 :crit, g3C3, 8.43, 9.97
  5d CH5 :crit, g5d, 10.73, 11.12
  6f CH3 :g6f, 11.97, 13.5
  5c B2 :g5c, 13.5, 14.0
  section Owner
  Sitting 1 :milestone, s1, 1, 1
  Sitting 2 :milestone, s2, 3, 3
  Walkthrough :milestone, s9, 13.5, 13.5
```
<!--/table-->

**The owner's time** (computed; TW11: 240 minutes a day, `owner/owner-sitting1-answers-2026-11-18.md` on `main`). The fortnight asks for 455 owner minutes in all:

<!--table:owner-->
| Day | Owner minutes | What |
|---:|---:|---|
| 1 | 60 | reads 3 pages for sitting 1 |
| 2 | 75 | sitting 1 |
| 3 | 80 | reads 4 pages for sitting 2 |
| 4 | 90 | sitting 2 |
| 13 | 30 | reads the day-14 pack |
| 14 | 120 | walkthrough of the built screens and the next ranked list |
| **14 days** | **455** | busiest day 120 minutes, within the 240-minute day |
<!--/table-->

**Rules each lane follows** (`.ai/RULES.md` §7; owner rules):
- **One unit at a time.** Each lane has one unit in build and one in review. A unit that touches shared code is reviewed and merged before the next unit builds on it.
- **Heavy work goes through the slot pool,** and one heavy database job runs at a time. Heavy work is check-all, tsc, vitest, Postgres test files, browser captures and database jobs.
- **Databases:** only `*_test` and `<prefix>_audit*` databases, and no full suite unless the owner asks.
- **Hands off:** never ports 5490 or 8990, never Docker during task work.
- **The day-14 walkthrough** runs only on a clean, good database. The owner accepted a verified clone as one (sitting 1, item 8).

## 5. Pace, the stretch line and the drop order
<!--derives: plan_model; Figure 10-->

**What lands at each pace** (computed):

<!--table:pace-->
| Case | Units landed by day 14 | Furthest step complete | Slices landed |
|---|---:|---|---:|
| slip pace (2 units a lane-day) | 80.5 | 4 Join at the money leaves | 27 of 51 |
| **planning pace (3)** | 111.5 | 4 Join at the money leaves | 37 of 51 |
| observed pace (4.8) | 139 | 8 Three verdicts | 46 of 51 |
| planning pace, 2 lanes (no slot pool) | 70 | 4 Join at the money leaves | 24 of 51 |
| planning pace, no rework allowance | 127.5 | 6 Decisions and options | 42 of 51 |
<!--/table-->

**Reading.**
- **Lanes matter more than pace here.** At the slip pace the fortnight still completes step 4. Without the slot pool, two lanes reach only the same step with far fewer units. The pool is therefore worth more than any single slice.
- **The rework allowance is worth two steps.** Without it, the furthest complete step moves from step 4 to step 6. The allowance stays, because this fortnight's work is new schema and money.

**The stretch line** (computed): what lands by day 14 at the observed pace but not at the planning pace. If the first week runs at the observed pace, these are next, in delivery order:

<!--table:stretch-->
| Slice | Step | Lands at the observed pace on day |
|---|---|---:|
| `0E` Spike E | 0 | 11 |
| `5c` The bridge on screen, factor by factor, labelled Emulated until the operator's exports replace the emulators | 5 | 9 |
| `7c` Proposal | 7 | 10 |
| `7e` Act first | 7 | 12 |
| `7f` Switches beside the proposal (budget; the letter of intent), recomputed visibly | 7 | 13 |
| `7g` Portfolio cards read from their factors against target, with their evidence class | 7 | 11 |
| `7h` Period close | 7 | 11 |
| `8b` Field evidence admitted with its label; the option's cost replaces 0 | 8 | 11 |
| `8c` Three verdicts on What changed, with Actions' owners and the plan review | 8 | 13 |
<!--/table-->

**If it slips, what drops first** (computed): slices that land at the planning pace but not at the slip pace, latest step first. The must-keep slices never drop: the slot pool, steps 1, 2 and 3A's store, intake, emulators and amounts, the registry, the pinned Findings, the structure read, the recorded person, and the walkthrough database.

<!--table:drop-->
| Order | Slice | Step | Lands at the planning pace on day |
|---:|---|---|---:|
| 1 | `8a` Economic and causal verdicts beside the operational one | 8 | 14 |
| 2 | `7d` Spend steps on the item | 7 | 12 |
| 3 | `7b` Release | 7 | 12 |
| 4 | `6f` Decision view from What can be done | 6 | 14 |
| 5 | `6g` Mto demand and repair decisions (revenue side, after the join), with the quotes emulator | 6 | 14 |
| 6 | `6b` Bounds as rows | 6 | 12 |
| 7 | `6c` Evaluator | 6 | 12 |
| 8 | `5b` Attribution | 5 | 13 |
| 9 | `5d` Relabel the Assure line to Actual against target (OD-6) | 5 | 12 |
| 10 | `5a` Targets and budget lines at factor level, declared by the operator with the declarer recorded; objectives become factor targets | 5 | 11 |
<!--/table-->

## 6. What day 14 shows on screen
<!--derives: §2.1; §2.3; §2.4; §2.6; §2.8; Rules; D14; plan_model-->

Only built features are shown, each with how it is known (design Rules). At the planning pace:

| Screen | What it shows on day 14 | How each figure is known |
|---|---|---|
| Portfolio Optimize card (step 1) | the period's figure, or its day and scope stated; fields the API computed and the screen hid | as today's wording |
| Site board (3B) | driver lines as factor rows from the registry; today's Findings on the factors they observe, such as Kobo's 330<!--fig:sites.lakeside-power/Kobo.actual.nodes.candidate_l--> L candidate and 120<!--fig:sites.lakeside-power/Kobo.actual.nodes.unexplained_l--> L unexplained litres | *Recorded* or *Measured* from telemetry and fuel records |
| Money leaves (3A, join) | billed, collected and outstanding at each Site, such as Kobo's 278.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.outstanding--> outstanding | *Emulated* (D14): never *Recorded*, never benefit |
| Work (3C) | every Action with its creator, owner and due date, overdue when late; work raised, assigned and closed under the person's name | recorded under the person |
| Kobo decision view (step 6) | the stop-threshold change against no action, +250.50<!--fig:options.KOB-STOPSOC.monthly_or_horizon_change--> a month; the reserve change rejected by the dawn bound | *Modelled*, and a design value until replay K runs on the Site's recorded data |
| Mto decisions (step 6) | the huller against the welder; the repair paths | *Modelled* and *Quoted*, as their inputs are labelled (WP §1.1) |
| Assure line (step 5) | "Actual against target" (OD-6) | — |

Built without a screen yet, and so not shown:
- targets and attribution (step 5);
- the plan's records, release and spend steps (step 7);
- the economic and causal verdicts (step 8).

Their screens are on the stretch line (§5). The walkthrough says so plainly rather than show a mock-up in their place.

## 7. Decisions for the owner at the pack approval
<!--derives: D11; Decisions; plan_model; Figure 10-->

| # | Decision | Context | Default, applied until the owner answers |
|---|---|---|---|
| 1 | Does approving the recreated pack also approve the structure of steps 1 and 3C? | Their structure is the pack's own (design CH5 and CH2; `plan-and-action-workflow.md`). Without this, lanes 3 and 4 wait for sitting 1 | Yes. Architect's call |
| 2 | Hold the two sittings on days 2 and 4 | Computed: a third sitting adds nothing by day 14. Step 9's page waits for the next fortnight | Yes |
| 3 | The planning pace, with a rework allowance | 3 units per lane-day, against 4.8 units per lane-day observed, plus 15 in 100 for rework | Yes |
| 4 | The heavy-tool slot pool first | W4 as amended (sitting 1, item 7) | Already decided by the owner |
| 5 | Re-cut after the first week | If week 1 runs at the observed pace, the stretch line (§5) comes in. If it slips, the drop order applies | Re-run `plan_model.py` at the end of day 7 and bring the result to the owner |

**Pushback, for the owner.** The owner asked to advance "as much as possible". The model's answer is that the binding limits are memory and the structure sittings, not effort. So the most valuable single choice is decision 1. It puts lanes 3 and 4 to work on day 1, at no cost to the owner's time.
