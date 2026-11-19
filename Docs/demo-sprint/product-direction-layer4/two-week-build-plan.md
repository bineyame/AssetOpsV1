# The first fortnight's build: as far along Figure 10 as fourteen days can go

**AssetEcon · Layer 4 pack document 6b · AssetOps Architect (Claude) · 19 Nov 2026 · derived from design rev 16.7 and `delivery-plan.md`; re-cut for rev 16.8 (sign-in and roles added to step 3C, OD-13, OD-14; structure of steps 1 and 3C approved with the pack, OD-20)**

**The owner's direction** (`.agent/owner-recreate-document-packs-2026-11-19.md`): the fortnight is to be recreated "focussed on advancing as much as possible towarfs the new features, not the markting element". So this is a build schedule and nothing else. It has no selling track, no demo days and no offer kit. Day 1 is the first build day after the owner approves the recreated pack.

**How to read it.** Every table marked *(computed)* is produced by `plan_model.py`, and `python3 plan_model.py --check` fails if any table or headline figure here differs from the model. The slices are `delivery-plan.md`'s, cited by ID. Their gates are stated there and not restated here.

*Serves the objective:* every day of the fortnight moves a feature that executives will see onto the screen sooner: Findings on their factors, money from records, a decision against no action, and the plan's approval.

## 1. The aim, and the headline
<!--derives: §2.9; Figure 10; OD-9; plan_model-->

**The aim** is the furthest point on Figure 10 that capacity allows, built in delivery order. That means step 1, then step 2's format and leaf IDs, then lanes 3A, 3B and 3C together, then the join, and then as far towards steps 5–8 as the lanes can reach.

**The headline, at the planning pace:**
- **4 build lanes** run from day 1. The heavy-tool slot pool (`T1`, numbered `B03` in `two-week-conversion-plan.md`) merges first, so lanes 3 and 4 open as soon as it lands.
- By day 14, 111.5 units land in 37 slices, of which 30 slices committed land by day 12.
- **Figure 10 is complete through step 5.** Steps 1, 2, 3A, 3B and 3C, the join, and targets and the bridge are all built, with the bridge on screen. Step 3C now starts with sign-in and roles (`3C0`, OD-13, OD-14).
- **Step 6 is built except its screen,** because cost-side decisions start before the join (design §2.9): the decision records, bounds, the evaluator, the stop-threshold carrier and its verification family, and Mto's demand and repair decisions. The Kobo decision view (`6f`) is stretch.
- **Step 7 starts:** the plan's records (`7a`) land; release, the proposal and their screens are stretch. **Step 8** is stretch.
- **Calibration:** replays K, M and E all land.
- **Rights rows** (`9a`, step 9) fill a lane-1 gap on days 10 to 13, while that lane waits for the evaluator.
- **At the observed pace,** the stretch line reaches step 6: the Kobo decision view completes it. Beyond it come the plan's release, proposal, spend steps, Portfolio cards and period close (step 7), the economic and causal verdicts with field evidence (step 8), and the claim case and remedy paths (step 9).
- **Cold rooms and EV depots** (step 9) wait for the next fortnight in every case.

**What changed in this re-cut.** Sign-in and roles (`3C0`, 3 units) now come before the person is recorded on every command (`3C1`). The model then moves sitting 2 from day 4 to day 8. The same 111.5 units land, and the furthest complete step moves from step 4 to step 5. The Kobo decision view moves to the stretch line, and the bridge comes onto the screen.

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
| 0 Calibration replays K, M, E | 3 | 15 | day 10 | 70 in 100 units · yes · yes |
| 1 Correct the last-day figure | 2 | 6.5 | day 4 | yes · yes · yes |
| 2 Canonical format and leaf factor IDs | 1 | 1.5 | day 3 | yes · yes · yes |
| 3A Sources | 5 | 13.5 | day 8 | yes · yes · yes |
| 3B Structure | 6 | 17.5 | day 9 | yes · yes · yes |
| 3C Recorded person | 4 | 12.5 | day 10 | yes · yes · yes |
| 4 Join at the money leaves | 2 | 5 | day 10 | yes · yes · yes |
| 5 Targets and the bridge | 4 | 10 | day 14 | 30 in 100 units · yes · yes |
| 6 Decisions and options | 7 | 21.5 | after day 14 | 14 in 100 units · 81 in 100 units · yes |
| 7 The plan and the Portfolio | 8 | 27 | after day 14 | 0 in 100 units · 19 in 100 units · 76 in 100 units |
| 8 Three verdicts | 3 | 8.5 | after day 14 | 0 in 100 units · 0 in 100 units · 71 in 100 units |
| 9 Rights, cold then EV, pilot onboarding at scale | 5 | 24.5 | after day 14 | 0 in 100 units · 16 in 100 units · 43 in 100 units |
| The day-14 walkthrough database | 1 | 1 | day 13 | yes · yes · yes |
<!--/table-->

**What is not in the fortnight, and why.**
- **The rest of step 9:** the claim case, remedy paths, and cold rooms and EV depots follow proof and the plan (Figure 10).
- **Pilot onboarding at scale** (step 9) waits for an operator's consent and data. The first deep-dive needs none of it: its sources are onboarded by the Analyst role through step 3A's intake, which lands by day 8 (design §2.9).
- **The deep-dive safeguard,** the operator's own target against actual within weeks, needs steps 3A, 4 and 5 live (design §2.9). At the planning pace all three are complete by day 14 (table above).
- The **selling work** is out of scope by the owner's direction.

## 4. The fourteen days
<!--derives: D11; Figure 10; plan_model-->

**Structure first (W1).** No slice builds before the owner approves its structure page. The pages are written from the recreated pack, so most take a quarter or half of a day.
- **Steps 1 and 3C are approved with the pack** (owner, OD-20). Their structure is already the pack's: design CH5 and CH2, `decision-loop-specification.md` §8 (sign-in and roles) and `plan-and-action-workflow.md`. So their slices start on day 1.
- **The sitting days are searched by the model.** It picks the days that land the most work by day 14, then the furthest step, then the fewest sittings. The result is sittings on days 2 and 8.

**Structure pages** (computed):

<!--table:pages-->
| Page | Covers | Architect lane-days | Approved |
|---|---|---:|---|
| P1 | Steps 1 and 3C: the corrected figure; sign-in, roles and the person on every command (pack #2, #12; OD-20) | 0 | with the pack, before day 1 |
| P2 | Step 2: canonical format version 1 and the leaf factor IDs | 0.5 | sitting 1, day 2 |
| P3A | Step 3A: record kinds, intake, emulator rules, the contract test | 0.25 | sitting 1, day 2 |
| P3B | Step 3B: registry rows, parity, the structure read and observer | 0.25 | sitting 1, day 2 |
| P5 | Step 5: target declaration and the attribution rules | 0.5 | sitting 2, day 8 |
| P6 | Step 6: decision records, bounds, the evaluator and the carrier | 0.5 | sitting 2, day 8 |
| P7 | Step 7: plan records, release, versions, the proposal (pack #12) | 0.5 | sitting 2, day 8 |
| P8 | Step 8: economic and causal verdicts | 0.25 | sitting 2, day 8 |
| P9 | Step 9: rights rows and the claim case; cold and EV records | 0.75 | sitting 2, day 8 |
<!--/table-->

**Day by day, at the planning pace** (computed; ✓ marks the day a slice merges):

<!--table:days-->
| Day | Lane 1 · sources and money | Lane 2 · structure and the plan's records | Lane 3 · person, decisions and proof | Lane 4 · screens and tooling | Owner |
|---|---|---|---|---|---|
| 1 | — | — | — | `T1` ✓, `1a`, `1b` | reads 3 pages for sitting 1 |
| 2 | — | `2a`, `3B1` | `0K` | `1a` ✓, `1b` | sitting 1 |
| 3 | `3A1` | `2a` ✓, `3B1` | `0K` | `1b` | — |
| 4 | `3A1`, `3A2` | `3B1`, `3B3` | `0K`, `3C0` | `1b` ✓, `3A5` | — |
| 5 | `3A1` ✓, `3A2`, `3A3` | `3B1` ✓, `3B3`, `3B6`, `3B2` | `0K` ✓, `3C0`, `3C1` | `3A5`, `0M` | — |
| 6 | `3A2` ✓, `3A3`, `3A4` | `3B3` ✓, `3B6` ✓, `3B2`, `3B4` | `3C0` ✓, `3C1`, `3C2` | `3A5` ✓, `0M`, `3B5` | — |
| 7 | `3A3` ✓, `3A4`, `4b` | `3B2` ✓, `3B4`, `0E` | `3C1` ✓, `3C2` | `0M` ✓, `3B5` | reads 5 pages for sitting 2 |
| 8 | `3A4` ✓, `4b`, `4a` | `3B4` ✓, `0E` | `3C2` ✓, `6a` | `3B5`, `3C3` | sitting 2 |
| 9 | `4b` ✓, `4a`, `5a` | `0E`, `7a` | `6a`, `6d` | `3B5` ✓, `3C3` | — |
| 10 | `4a` ✓, `5a`, `9a` | `0E` ✓, `7a` | `6a` ✓, `6d`, `6e` | `3C3` ✓, `5d` | — |
| 11 | `5a` ✓, `9a` | `7a`, `5b` | `6d` ✓, `6e`, `6c` | `5d` | — |
| 12 | `9a`, `6g` | `7a` ✓, `5b`, `7b` | `6e` ✓, `6c`, `6b` | `5d` ✓, `WK`, `5c` | — |
| 13 | `9a` ✓, `6g`, `7d` | `5b` ✓, `7b` | `6c` ✓, `6b`, `8a` | `WK` ✓, `5c`, `6f` | reads the day-14 pack |
| 14 | `6g` ✓, `7d`, `9b` | `7b`, `7c` | `6b` ✓, `8a`, `8b` | `5c` ✓, `6f` | walkthrough of the built screens and the next ranked list |
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
  9a B3 :g9a, 10.73, 12.27
  6g CH3 :g6g, 12.27, 13.8
  7d P :g7d, 13.8, 14.0
  section Structure and the plan's records
  2a B3 :crit, g2a, 2.0, 2.58
  3B1 B1 :crit, g3B1, 2.58, 4.11
  3B3 B1 :crit, g3B3, 4.11, 5.26
  3B6 B1 :crit, g3B6, 5.26, 5.83
  3B2 CH1 :crit, g3B2, 5.83, 6.79
  3B4 CH1 :crit, g3B4, 6.98, 7.94
  0E CH3 :crit, g0E, 7.94, 9.67
  7a P :crit, g7a, 9.67, 11.58
  5b B2 :g5b, 11.58, 12.73
  7b P :g7b, 12.73, 14.0
  section Person, decisions and proof
  0K CH3 :crit, g0K, 2.0, 4.68
  3C0 CH2 :crit, g3C0, 4.68, 5.83
  3C1 CH2 :crit, g3C1, 5.83, 6.98
  3C2 CH2 :crit, g3C2, 6.98, 7.94
  6a CH3 :crit, g6a, 8.0, 9.15
  6d CH3 :crit, g6d, 9.15, 10.11
  6e CH4 :crit, g6e, 10.11, 11.07
  6c CH3 :g6c, 11.07, 12.22
  6b CH3 :g6b, 12.22, 13.18
  8a CH4 :g8a, 13.18, 14.0
  section Screens and tooling
  T1 tooling :crit, gT1, 0.0, 0.96
  1a CH5 :crit, g1a, 0.96, 1.92
  1b CH5 :crit, g1b, 1.92, 3.45
  3A5 B3 :crit, g3A5, 4.6, 5.56
  0M CH3 :crit, g0M, 5.56, 6.9
  3B5 B1 :crit, g3B5, 6.9, 8.43
  3C3 CH2 :crit, g3C3, 8.43, 9.97
  5d CH5 :crit, g5d, 10.73, 11.12
  WK tooling :gWK, 12.0, 12.38
  5c B2 :g5c, 12.73, 13.88
  6f CH3 :g6f, 13.88, 14.0
  section Owner
  Sitting 1 :milestone, s1, 1, 1
  Sitting 2 :milestone, s2, 7, 7
  Walkthrough :milestone, s9, 13.5, 13.5
```
<!--/table-->

**The owner's time** (computed; TW11: 240 minutes a day, `owner/owner-sitting1-answers-2026-11-18.md` on `main`). The fortnight asks for 490 owner minutes in all:

<!--table:owner-->
| Day | Owner minutes | What |
|---:|---:|---|
| 1 | 60 | reads 3 pages for sitting 1 |
| 2 | 75 | sitting 1 |
| 7 | 100 | reads 5 pages for sitting 2 |
| 8 | 105 | sitting 2 |
| 13 | 30 | reads the day-14 pack |
| 14 | 120 | walkthrough of the built screens and the next ranked list |
| **14 days** | **490** | busiest day 120 minutes, within the 240-minute day |
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
| slip pace (2 units a lane-day) | 76.5 | 4 Join at the money leaves | 26 of 52 |
| **planning pace (3)** | 111.5 | 5 Targets and the bridge | 37 of 52 |
| observed pace (4.8) | 143.5 | 6 Decisions and options | 47 of 52 |
| planning pace, 2 lanes (no slot pool) | 70 | 4 Join at the money leaves | 24 of 52 |
| planning pace, no rework allowance | 125 | 5 Targets and the bridge | 41 of 52 |
<!--/table-->

**Reading.**
- **Lanes matter more than pace here.** At the slip pace the fortnight still completes step 4. Without the slot pool, two lanes reach only the same step with far fewer units. The pool is therefore worth more than any single slice.
- **The rework allowance costs no complete step here.** Without it, the furthest complete step moves from step 5 to step 5, though 13.5 more units land (125 against 111.5). The allowance stays, because this fortnight's work is new schema and money.

**The stretch line** (computed): what lands by day 14 at the observed pace but not at the planning pace. If the first week runs at the observed pace, these are next, in delivery order:

<!--table:stretch-->
| Slice | Step | Lands at the observed pace on day |
|---|---|---:|
| `6f` Decision view from What can be done | 6 | 13 |
| `7b` Release | 7 | 12 |
| `7c` Proposal | 7 | 13 |
| `7d` Spend steps on the item | 7 | 13 |
| `7g` Portfolio cards read from their factors against target, with their evidence class | 7 | 11 |
| `7h` Period close | 7 | 14 |
| `8a` Economic and causal verdicts beside the operational one | 8 | 13 |
| `8b` Field evidence admitted with its label; the option's cost replaces 0 | 8 | 14 |
| `9b` Supplier-claim case and its states | 9 | 11 |
| `9c` Remedy paths inside decisions, with notice deadlines | 9 | 14 |
<!--/table-->

**If it slips, what drops first** (computed): slices that land at the planning pace but not at the slip pace, latest step first. The must-keep slices never drop: the slot pool, steps 1, 2 and 3A's store, intake, emulators and amounts, the registry, the pinned Findings, the structure read, the recorded person, and the walkthrough database.

<!--table:drop-->
| Order | Slice | Step | Lands at the planning pace on day |
|---:|---|---|---:|
| 1 | `9a` Rights rows from contract documents, AI-assisted, a person approving each row; contract-document emulator | 9 | 13 |
| 2 | `7a` Plan records (portfolio_plan) | 7 | 12 |
| 3 | `6g` Mto demand and repair decisions (revenue side, after the join), with the quotes emulator | 6 | 14 |
| 4 | `6b` Bounds as rows | 6 | 14 |
| 5 | `6c` Evaluator | 6 | 13 |
| 6 | `6e` Stop-setting verification family (an unknown rule fails closed today) | 6 | 12 |
| 7 | `6d` Stop-threshold carrier as a domain-action apply path, linked to its decision option | 6 | 11 |
| 8 | `5c` The bridge on screen, factor by factor, labelled Emulated until the operator's exports replace the emulators | 5 | 14 |
| 9 | `5b` Attribution | 5 | 13 |
| 10 | `5d` Relabel the Assure line to Actual against target (OD-6) | 5 | 12 |
| 11 | `0E` Spike E | 0 | 10 |
<!--/table-->

## 6. What day 14 shows on screen
<!--derives: §2.1; §2.3; §2.4; §2.6; §2.8; Rules; D14; plan_model-->

Only built features are shown, each with how it is known (design Rules). At the planning pace:

| Screen | What it shows on day 14 | How each figure is known |
|---|---|---|
| Portfolio Optimize card (step 1) | the period's figure, or its day and scope stated; fields the API computed and the screen hid | as today's wording |
| Site board (3B) | driver lines as factor rows from the registry; today's Findings on the factors they observe, such as Kobo's 330<!--fig:sites.lakeside-power/Kobo.actual.nodes.candidate_l--> L candidate and 120<!--fig:sites.lakeside-power/Kobo.actual.nodes.unexplained_l--> L unexplained litres | *Recorded* or *Measured* from telemetry and fuel records |
| Money leaves (3A, join) | billed, collected and outstanding at each Site, such as Kobo's 278.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.outstanding--> outstanding | *Emulated* (D14): never *Recorded*, never benefit |
| Sign-in and Organisation settings (3C) | each person signs in with email and password; the executive grants and removes roles, each change on record (OD-13, OD-14) | recorded under the person |
| Work (3C) | every Action with its creator, owner and due date, overdue when late; work raised, assigned and closed under the person's name | recorded under the person |
| The bridge (step 5) | Kobo's October gap to target, −562.00<!--figx:{sites.lakeside-power/Kobo.actual.nodes.contribution}-{sites.lakeside-power/Kobo.plan.nodes.contribution}-->, built up factor by factor (design Figure 3) | *Emulated* money leaves (D14) beside *Recorded* telemetry and fuel |
| Assure line (step 5) | "Actual against target" (OD-6) | — |

Built without a screen yet, and so not shown:
- the decisions and options, including Kobo's stop-threshold change and Mto's demand and repair decisions (step 6; the decision view `6f` is stretch);
- the plan's records (step 7);
- the rights rows (step 9).

Their screens are on the stretch line (§5). The walkthrough says so plainly rather than show a mock-up in their place.

## 7. Decisions for the owner at the pack approval
<!--derives: D11; Decisions; plan_model; Figure 10-->

| # | Decision | Context | Default, applied until the owner answers |
|---|---|---|---|
| 1 | Does approving the recreated pack also approve the structure of steps 1 and 3C? | Their structure is the pack's own (design CH5 and CH2; `plan-and-action-workflow.md`). Without this, lanes 3 and 4 wait for sitting 1 | **Decided by the owner, 19 Nov (OD-20): yes** |
| 2 | Hold the two sittings on days 2 and 8 | Computed: the model's search picks these days. Sitting 2 approves steps 5 to 9's pages together | Yes |
| 3 | The planning pace, with a rework allowance | 3 units per lane-day, against 4.8 units per lane-day observed, plus 15 in 100 for rework | Yes |
| 4 | The heavy-tool slot pool first | W4 as amended (sitting 1, item 7) | Already decided by the owner |
| 5 | Re-cut after the first week | If week 1 runs at the observed pace, the stretch line (§5) comes in. If it slips, the drop order applies | Re-run `plan_model.py` at the end of day 7 and bring the result to the owner |

**Pushback, for the owner.** The owner asked to advance "as much as possible". The model's answer is that the binding limits are memory and the structure sittings, not effort. Decision 1, now decided (OD-20), puts lanes 3 and 4 to work on day 1. The next lever is sitting 2: on day 8 it lands the bridge but leaves the Kobo decision view as stretch. Re-running the model at day 7 (decision 5) is where to revisit it.
