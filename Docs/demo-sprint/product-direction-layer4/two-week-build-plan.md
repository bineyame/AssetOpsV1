# The first fortnight's build: as far along Figure 10 as fourteen days can go

**AssetEcon · Layer 4 pack document 6b · AssetOps Architect (Claude) · 19 Nov 2026 · derived from design rev 16.7 and `delivery-plan.md`; re-cut for rev 16.8 (sign-in and roles added to step 3C, OD-13, OD-14; structure of steps 1 and 3C approved with the pack, OD-20); checked against `rev 16.9` to `rev 16.12` (step 3C no longer waits for step 1; the day table corrected); **re-cut 20 Nov** for the non-screen build start (the day-7 re-cut brought forward: data slices added, two build lanes, screen slices held; rulings D-BW1.1 to D-BW1.6 in `specs/BW1-build-wave1/rulings.md`); **re-cut 2, 20 Nov: the deep-dive path first (§0 governs where it differs; D-BW1.8 to D-BW1.12)**

**The owner's direction** (`.agent/owner-recreate-document-packs-2026-11-19.md`): the fortnight is to be recreated "focussed on advancing as much as possible towarfs the new features, not the markting element". So this is a build schedule and nothing else. It has no selling track, no demo days and no offer kit. Day 1 is 20 Nov 2026, when the owner started the non-screen build (`owner/owner-start-non-screen-build-2026-11-20.md`: "yes, start the non-screen build work now"). The pack merged to `main` the same day.

**How to read it.** Every table marked *(computed)* is produced by `plan_model.py`, and `python3 plan_model.py --check` fails if any table or headline figure here differs from the model. The slices are `delivery-plan.md`'s, cited by ID. Their gates are stated there and not restated here.

*Serves the objective:* every day of the fortnight moves a feature that executives will see onto the screen sooner: Findings on their factors, money from records, a decision against no action, and the plan's approval.

## 0. Re-cut 2 (20 Nov): the deep-dive path first
<!--derives: §2.9; Figure 10; plan_model-->
<!--re-cut 2: Architect, by hand; not computed. plan_model.py is re-run once the owner accepts (decision RC1). Rulings D-BW1.8 to D-BW1.12-->

**Why.** The owner (`owner/owner-recut-fortnight-deep-dive-2026-11-20.md`): re-cut the fortnight around the deep-dive, an operator executive's own gap explained in money from their own exports, on one screen. It serves the demo objective directly: monitoring tools show readings; only this shows an executive why their month is short of target, in their money. **What stays:** everything merged (`T1`, `T1-F1`, `T2`, `2a`, `DS1a`, `DS1p`, `DS1b`, `3C0a`, `3B1`, `3A1`, `3C1a`, the UI branch), the three in-flight units (`3B3`, `IA-1a`, `DS1m`), the gates in `delivery-plan.md` §3, the slot pool and the machine rules (§4). **What changes:** the order of days 2 to 14, five new units, three dependency cuts, and sitting 1 split (§0.6). §1, §4, §5 and §6 below are the day-1 schedule; where they differ, this section governs.

### 0.1 The path, unit by unit

The deep-dive works when a person in the Analyst role can take a mini-grid operator's exports (billing or vending, payment settlements, expense or fuel invoices, the monthly budget, and the EMS export where they have one), load them with no code change, and show the executive one screen: the month's contribution against their own target, the gap split by heading, every figure with its evidence word, and every gap in the data named as "Not available yet". **New** marks a unit not in `delivery-plan.md` §2.

| # | Unit | What it builds | Units | Depends on | Lane | Lands (planning · slip pace) |
|---:|---|---|---:|---|---|---|
| 1 | `3B3` (in flight) | Structure read: bottom-up, coverage, evidence class, missing never 0 | 3 | `3B1` | B | day 2 · 3 |
| 2 | `3A2` | File intake on the signed-in, Site-bound path: dry run, plain refusals, customer IDs pseudonymised, late records revise their month | 3 | `3A1` | A | 3 · 4 |
| 3 | `3A4` | Amounts by recognition month; a late record marks dependent reads out of date | 2 | `3A1` | B | 3 · 4 |
| 4 | `3A3` | Emulated native exports (billing, collections, fuel purchases, budget) and the contract test every real export passes | 3 | `3A2` | A | 4 · 6 |
| 5 | **`3A6` new** | Source profiles as data: columns, units, date format, timezone, currency and personal-data fields for one operator's export, pinned against their sample and admitted only through 3A3's contract test (integration design §7.2: "only transport and profile change"). CSV and single-sheet XLSX | 2.5 | `3A2`, `3A3` | A | 5 · 8 |
| 6 | **`ON1` new** | Deep-dive tenant: the operator, its Sites (vertical, timezone, currency, declared tariff and loss band) and its accounts, from one onboarding file the analyst fills; non-screen command | 1.5 | `3C0a`, `3B1` | A | 6 · 9 |
| 7 | **`3A7` new** | One closed month reconciled: the finance lead records the management-accounts totals (revenue; fuel or energy cost); money reads *Recorded* only for a month inside the tolerance, otherwise *Recorded, not yet reconciled* (integration design §7.2's pilot validation gate) | 1.5 | `3A4` | A | 6 · 9 |
| 8 | `4b` | Money leaves from records into the structure read: revenue, collections, O&M, staff, fuel purchases | 2.5 | `3A4`, `3B3` (**cut:** not `3A3`, D-BW1.10) | B | 4 · 5 |
| 9 | `5a` | Targets and budget lines at factor level, declarer recorded; a driver with no target line is a labelled assumption (owner item 6) | 3 | `3A4`, `3B3`, `3C1a`, page P5 (**cut:** not `4b`, D-BW1.10) | C | 5 · 7 |
| 10 | `3B7a` | Snapshot store: the read served with its "as of" (OD-23); rebuilt on command after an accepted import | 2.5 | `3B3` | B | 5 · 7 |
| 11 | `5b` | Attribution: exact for sums, declared rule for products, residual only beside an unobserved leaf | 3 | `5a`, `4b` | B | 6 · 9 |
| 12 | **`4d` new** | The monthly litre split: necessary, candidate and unexplained litres from dispatch minutes, the generator's fuel curve and the fuel balance (`3B3` holds them as HELD_NOT_CALCULATED; no slice owned them, D-BW1.11) | 3 | `3B3` | B | 8 · 11 |
| 13 | `5c` (**re-scoped**) | **The one screen:** the month's contribution against target and the gap by heading, the bridge factor by factor, cash apart, each figure with its evidence word, gaps as "Not available yet". Cites vNEXT `#/portfolio` "the month in one line" and Assure's "Contribution's bridge by heading" (`walkthroughs.md` §2, steps 1 to 3), in the hub shape after the IA-1 stop. Carries 3A5's label rule on this screen only (**cut:** not `3B5`, not all of `3A5`, D-BW1.9) | 3 | `5b`, `3B7a`, the IA-1 stop | UI | built 8, owner walkthrough 11 · 13 |
| 14 | **`DDR` new** | Rehearsal, end to end: Lakeside's emulated exports through 3A6, 3A2 and the read must meet step 5's gate (Kobo's 120.50<!--figx:{sites.lakeside-power/Kobo.actual.nodes.contribution}-{sites.lakeside-power/Kobo.plan.nodes.contribution}--> split to the cent); then one export of a shape never seen before goes through a new profile with no code change; the analyst's runbook | 1 | 3A6, ON1, 3A7, 5b, 4d | B | 10 · 13 |
| | **Path total** | 13 units to build (and `3B3` finishing) | **31.5** | | | **day 11 · day 13** |

**Critical chain:** `3B3` → `3A4` → `4b` and `5a` → `5b` → `5c` → owner walkthrough. Planning pace: day 11 with three days' buffer. Slip pace (2 units a lane-day): day 13. The buffer is for screen review rounds (the UI branch needed five).

**Not on the path (pushback):**
- `DS3` (bulk loader) loads the *generated* world. A real operator's exports are small and go through `3A2` (D-3A1 Q2: "demo and pilot volumes are small; DS3's bulk path is separate"). `DS3` stays in the fortnight, after the path, for the walkthrough database.
- `4a` (energy to cash) explains *where* kWh leaked, not the money gap; its lines read "Not available yet" on the screen until it lands (day 10, off the path).

### 0.2 Days 2 to 14, four agents

Four build agents at once (lanes A, B, C and the UI lane); the reviewer stream and the slot pool as in §2; one heavy database job at a time. ✓ marks the day a unit merges (planning pace). Bold is the path.

| Day | Lane A · sources | Lane B · structure and money | Lane C · targets, the person, decisions | UI lane · mock-up, then the one screen | Owner |
|---|---|---|---|---|---|
| 2 | **`3A2`** | **`3B3` ✓**, **`3A4`** | `DS1m` ✓ | `IA-1a` | decisions RC1 to RC8 (§0.6) |
| 3 | **`3A2` ✓**, **`3A3`** | **`3A4` ✓**, **`4b`** | **`5a`** (P5 written day 2) | `IA-1a` ✓, `IA-1b` | approves P5 (30 min) |
| 4 | **`3A3` ✓**, **`3A6`** | **`4b` ✓**, **`3B7a`** | **`5a`** | `IA-1b` ✓, `IA-1c` | — |
| 5 | **`3A6` ✓**, **`ON1`** | **`3B7a` ✓**, **`5b`** | **`5a` ✓**, `3C2` | `IA-1c` ✓; **`5c`** handshake | the IA-1 stop: sees the hub and decision shapes |
| 6 | **`ON1` ✓**, **`3A7` ✓**, `DS3` | **`5b` ✓**, **`4d`** | `3C2` ✓, `0K1` | **`5c`** | — |
| 7 | `DS3` ✓, `DS4` | **`4d`** | `0K1` | **`5c`** | — |
| 8 | `DS4` ✓, `4a` | **`4d` ✓**, `3B2` | `0K1` ✓, `0K2` | **`5c`** built, in review | — |
| 9 | `4a` | `3B2` ✓, **`DDR`** | `0K2` | **`5c`** review fixes | — |
| 10 | `4a` ✓, `1a` | **`DDR` ✓**, `3B6` | `0K2` ✓, `0M` | **`5c`** ACCEPT | — |
| 11 | `1a` | `3B6` ✓, `3B4` | `0M` | `IA-2a` (with the owner's IA-1 input) | **walks `5c` on the rehearsed data; merge** |
| 12 | `1a` ✓ | `3B4` | `0M` ✓, `3C1b` | `IA-2a` | — |
| 13 | `WK` ✓ | `3B4` ✓ | `3C1b` ✓ | `IA-2b` | reads the day-14 pack |
| 14 | — | — | `6a` starts | `IA-2b` | walkthrough; sitting for P6 to P9 |

The tail of each lane after the path is a pull order, not a commitment. A path unit that slips takes the next free lane before any tail unit.

### 0.3 What lands by day 14, and what moves out

**Lands:** the whole deep-dive path (§0.1), proven on the rehearsal; `DS3`, `DS4` and the walkthrough database `WK`; `4a`; `3B2`, `3B4`, `3B6`; `3C2`, `3C1b`; spikes `0K1`, `0K2`, `0M`; `1a`; IA-1 to its stop, and `IA-2a`, `IA-2b` begun.

**Moves out** (next fortnight, in this order), each for a reason:

| Unit | Reason |
|---|---|
| `6a`, `6c`, `6d`, `6e`, `6b` (decisions, evaluator, carrier) | The deep-dive explains the gap; valuing the fix against doing nothing is the next step, and it needs spike K's replay (`0K2`, day 10) first. Their page P6 moves to the day-14 sitting |
| `9a`, `9b` (rights, claim case) | Step 9; not on the path; page P9 not approved |
| `3B5` (Site board), `3A5` on every other screen, `1b` | The one screen carries its own labels; the other screens are being rebuilt by shape (IA-2), so changing them now would be reviewed twice |
| `DS2` (shapes) | The walkthrough database builds from `DS3` and `DS4` without day shapes; shapes add realism, not money |
| `3B7b` (recalculation triggers) | The analyst rebuilds the snapshot after each accepted import (`3B7a`); automatic triggers follow |
| `3C0b` (sign-in page) | The owner presents the deep-dive (RC7) |
| `IA-2c` to `IA-2e` | After `5c`: the UI lane builds the screen that converts first |

### 0.4 The honest limit: "Not available yet" on a typical operator's exports

A typical mini-grid operator sends billing or vending, mobile-money settlements, fuel and service invoices, a monthly budget in money, and sometimes an EMS export. On those, the screen shows contribution against target and the gap split by revenue, fuel cost, O&M and staff, and cash collected against billed. These still read "Not available yet", each naming the record that would fill it:
- **Where the kWh went:** delivered and metered kWh, technical against unexplained loss, unmapped kWh. They need a feeder meter and a meter register with change dates, which few operators keep.
- **Why the fuel was spent:** the necessary, candidate and unexplained litres (`4d`). They need the EMS interval export (generator state, solar available power, battery charge) and tank dips. Without dips there is no unexplained figure; without solar available power there is no candidate figure. Fuel *cost* from invoices is still shown.
- **Price against volume:** kWh × tariff and litres × price splits appear only where the budget states volumes. Otherwise the driver's target is a labelled assumption (owner item 6), never presented as the operator's.
- **A cost line not sent** (payroll is often withheld) reads "Not available yet", or *Estimated* where the operator states an estimate, never 0.
- **Recorded money** reads *not yet reconciled* until one closed month matches their management accounts (`3A7`).
- **Not built this fortnight, stated on the screen:** what each fix is worth against doing nothing, the Protect limits, warranties and rights.
- **Cold-chain and EV operators:** their records (`9d`, `9e`) are not built, so the first deep-dive is mini-grid only (RC5).

### 0.5 The rebuild by shape, and what it offers the objective (the owner's question)

**What it is.** IA-1 and IA-2 rebuild the **vNEXT mock-up, not the live product**: every screen is drawn from one of eight shapes (frame, hub, decision, the plan screen, list, asset, drawer and record page, statement), with gates on click depth and "nothing rewritten after it renders". IA-1 (3 units: the frame, the Portfolio hub, the decision) stops for the owner; IA-2 (5 units) is the rest.
**What it offers.** It settles how every executive moves through the product, so each live screen is later built once per shape rather than once per page. It is also the reference the deep-dive screen cites: `5c` takes the hub's money line and the Assure bridge.
**What it does not offer.** No operator's own data reaches a screen through it. Measured against the objective, the deep-dive path converts and the shape rebuild makes it read coherently. **So:** finish IA-1 to its stop (in flight, day 5), then the UI lane builds `5c`; IA-2 resumes on day 11.

### 0.6 Risks, and decisions for the owner

**Risks.**
1. **No real export yet.** The path is proven on emulated exports plus one stranger-shaped sample (`DDR`). A real file in a shape `3A6` cannot read (several sheets, merged headers) is reshaped by the analyst into our template. That is a workaround, timed in the runbook.
2. **Reconciliation fails.** Most operators' exports will not match their management accounts the first time. The screen then says so; the conversation must expect it.
3. **Screen review rounds.** `5c` is the only screen on the path; three days' buffer; scope held to one screen.
4. **P5 late.** `5a` and `5b` slip day for day after day 3.
5. **`3B3` slips.** It is the root of the chain; it takes priority over every tail unit for the reviewer.
6. **The owner's IA-1 input changes the hub shape.** `5c`'s spec cites the shape after the stop, so it is written on day 5, not earlier.
7. **Real operator data on this machine.** It needs its own database, which no agent may create today (RC4).

**Decisions, each with its default (applied until the owner answers).**

| # | Decision | Default |
|---|---|---|
| RC1 | Accept this re-cut: deep-dive path first; decisions and rights move to the next fortnight | Yes. The model is re-run after acceptance |
| RC2 | Read real exports through profiles as data (`3A6`, 2.5 units), or have the analyst reshape each export into our template (a workaround, no build) | `3A6`; the template stays the fallback |
| RC3 | Approve page P5 (targets and attribution) alone on day 3, not at the day-9 sitting | Yes. P6 to P9 at the day-14 sitting |
| RC4 | Where a real operator's data lives | Its own database on this server, created by the coordinator only after a signed data-processing agreement; customer IDs pseudonymised at intake; deleted at the agreed retention. No real data before the agreement |
| RC5 | The first deep-dive is mini-grid only | Yes (integration design §7.3: the first replacement is a mini-grid deep-dive); cold and EV next fortnight |
| RC6 | After the IA-1 stop, the UI lane builds `5c` before IA-2 | Yes |
| RC7 | The executive does not sign in at the deep-dive; the owner presents it | Yes. `3C0b` next fortnight |
| RC8 | Reconciliation tolerance | 1 in 100 of the month's revenue and of its fuel or energy cost; the owner may set it per operator |
| RC9 | D15 (the first change agreed at the end of the deep-dive) | Agreed by people and recorded as an Action with its owner and due date (`3C2`, day 6). The product does not value it this fortnight |


## 1. The aim, and the headline
<!--derives: §2.9; Figure 10; OD-9; plan_model-->
*Re-cut 2: the day-1 schedule, kept as the model's record; §0 governs where it differs.*

**The aim** is the furthest point on Figure 10 that capacity allows, built in delivery order. That means step 1, then step 2's format and leaf IDs, then lanes 3A, 3B and 3C together, then the join, and then as far towards steps 5–8 as the lanes can reach.

**The headline, at the planning pace:**
- **3 build lanes**, four later (owner, 20 Nov, item 3: "accept"; `owner/owner-answers-eight-open-questions-2026-11-20.md`). The UI Architect's mock-up work holds the fourth. Lane A carries W4 lane 1's slices (sources and money); lane B lanes 2 and 4's (structure, the plan's records, data tools, screens); lane C lane 3's (the person, decisions, calibration).
- **Non-screen first.** Screen slices wait until the Decision page, the Site page and the plan screen pass UI review (owner, 20 Nov), assumed here at the start of day 6. On three lanes the hold costs nothing: the lanes are full of non-screen work until then (§5).
- **Day 1:** lane C builds `3C0a`, operator accounts and roles behind the API; lane B starts `2a`, the canonical format and the leaf factor IDs (its page `P2` approved by the owner, 20 Nov), which unblocks sources, structure and the data slices. Lane A opens with `DS1b`, the generator's canonical writers, as soon as `2a` lands (D-BW1.7).
- By day 14, 90.5 units land in 33 slices, of which 28 slices committed land by day 12. Every must-keep slice lands by day 12.
- **Figure 10 is complete through step 3A.** Steps 1 (day 9), 2 (day 1) and 3A (day 11) are built, and the join (step 4) by day 10. Step 3B is built except the observer and the daily snapshot; step 3C except its two screens. Targets (`5a`) land; spike K lands in two parts (`0K1`, `0K2`); the decision records, the carrier, its verification family, the evaluator and bounds (`6a` to `6e`) land, and the economic and causal verdicts (`8a`).
- **The data slices land:** the shapes (`DS2`), the canonical writers (`DS1b`), the bulk loader (`DS3`) and the template ladder (`DS4`) with its re-benchmark, so the walkthrough database is built from templates.
- **At the observed pace,** the stretch line reaches step 4: the structure observer, the daily snapshot and its recalculation, the sign-in page, the work controls, attribution, spikes M and E, Mto's decisions, and the claim case and remedy paths.
- **The bridge, the decision view, the plan's records and proof on screen** wait for the next fortnight at the planning pace.

**What changed in this re-cut** (20 Nov; the pack's decisions 5 and 6, brought forward to the build start):
- **Added:** the data and build strategy's slices, 19 units (`DS1` done, `DS1b`, `DS2` to `DS4`, `3B7a`, `3B7b`; `DS6` on the stretch line; `DS7` and `4c` queued with their triggers). Each slice is marked screen or non-screen in `delivery-plan.md` §2.
- **Corrected:** the handshake's time, 0.1 lane-days a slice, which the model left out (decision 6's optimistic bias). The pessimistic bias is gone, because `T1` merged before day 1.
- **Cut:** `3C0` into `3C0a` and `3C0b`, and `0K` into `0K1` and `0K2`, so non-screen work is not held behind a screen and no slice is over 6 units.
- **Ranked:** on short lanes the must-keep set goes first (D-BW1.6). Under delivery order alone, `3B2` and `3C2` missed day 12 on two lanes.
- **Effect:** 111.5 units and step 5 became 64.5 units and step 3A on two lanes. The owner's third lane (20 Nov, item 3) brings it to 90.5 units, still through step 3A; all four building would land 116 units, through step 4 (§5). The rest of the loss against the pack is the data slices and the snapshot the old model did not count.
- **Since the first re-cut** (20 Nov, later): three lanes (owner, item 3); `P2`, `P3A` and `P3B` approved; `3C0a` at 2.5 units (its handshake, P14); `3C1` split into `3C1a` (3 units) and `3C1b` (2 units), 5 units against 3 (its handshake, P10; D-3C1.13).

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
| Build lanes the machine allows | the largest count that fits, capped by W4 as amended | 4 with the slot pool (merged, T1); 2 without |
| **Build lanes now** | owner, 20 Nov: three now, four later; the fourth runs the UI Architect's mock-up work | **3** |
| Screen hold | screen slices wait until the Decision page, the Site page and the plan screen pass UI review (owner, 20 Nov) | assumed released at the start of day 6 (assumption; re-run when it passes) |
| Spec handshake | one combined Reviewer and Implementer round per slice before its code (RULES §4) | 0.1 lane-days a slice (assumption) |
| Observed pace | 237 task merges in 26.29 days, 1.88 branches open on average | 4.8 units per lane-day |
| Planning pace | about 0.6 of observed: new schema and money, discovery reviews, checks first, four lanes merging | 3 units per lane-day (slip case 2) |
| Rework allowance | explicit, on top of the pace | every unit takes 1.15 units of lane time |
| Reviewer stream | one fresh-review slot, 14 h a day; 57 in 100 units need a discovery review | 18.2 units a day; 66 in 100 busy at the planning pace |
| Build capacity in 14 days | 3 lanes at the planning pace, less rework and the handshake | about 102 units |
<!--/table-->

**How to read it.**
- **Memory sets the lane count, not CPU.** The machine has no swap, so the build is sized to the worst case: every agent resident and both heavy slots full. Four lanes fit only with the slot pool. That is why the pool is the first slice and lanes 3 and 4 open when it merges, as W4 is amended (owner, sitting 1, item 7: "yes").
- **The pace is measured, then cut, then rework is added.** 237 task merges in about 26 days, with fewer than two branches open on average, is 4.8 units per lane-day. That is an upper bound, because it starts at each branch's first commit.
- **This fortnight is new schema and money work,** with discovery reviews and checks written first, so the schedule uses 3 units per lane-day. On top, every unit carries a 15 in 100 rework allowance.
- **The reviewer stream is the next limit.** One review slot is busy about two thirds of the day at the planning pace. Above that pace a builder pauses rather than skip a review (W5).

**People.**
- **The Architect** writes the structure pages (§4) and answers the builders' batched questions.
- **The coordinator** merges, and runs check-all on `main` after each merge.
- **The owner** approved steps 2, 3A and 3B's pages on 20 Nov, approves the rest at one sitting and walks the built screens on day 14 (§4).

## 3. Scope, ranked by step
<!--derives: §2.9; Figure 10; OD-9; plan_model-->

**Ranked in delivery order.** Every slice is ranked by its Figure 10 step first, then by the work it unlocks. The slot pool comes first of all, and the walkthrough database goes to the first free lane on day 13. Nothing is ranked by how it would look in a demo. The slices, their units and their dependencies are in `delivery-plan.md` §2.

**Where each step stands on day 14** (computed):

<!--table:steps-->
| Step | Slices | Units | Done by day (planning pace) | Done by day 14 at slip · planning · observed pace |
|---|---:|---:|---|---|
| Tooling: the heavy-tool slot pool | 1 | 2.5 | day 1 | yes · yes · yes |
| 0 Calibration replays K, M, E | 4 | 15 | after day 14 | 47 in 100 units · 70 in 100 units · yes |
| 1 Correct the last-day figure | 2 | 6.5 | day 9 | yes · yes · yes |
| 2 Canonical format and leaf factor IDs | 1 | 1.5 | day 1 | yes · yes · yes |
| D Data: the generated world, its loader and templates | 6 | 16 | after day 14 | 69 in 100 units · 84 in 100 units · 84 in 100 units |
| 3A Sources | 5 | 13.5 | day 11 | 81 in 100 units · yes · yes |
| 3B Structure | 8 | 23 | after day 14 | 41 in 100 units · 65 in 100 units · yes |
| 3C Recorded person | 6 | 15 | after day 14 | 67 in 100 units · 67 in 100 units · yes |
| 4 Join at the money leaves | 2 | 5 | day 10 | yes · yes · yes |
| 5 Targets and the bridge | 4 | 10 | after day 14 | 0 in 100 units · 30 in 100 units · 90 in 100 units |
| 6 Decisions and options | 7 | 21.5 | after day 14 | 14 in 100 units · 37 in 100 units · 81 in 100 units |
| 7 The plan and the Portfolio | 8 | 27 | after day 14 | 0 in 100 units · 0 in 100 units · 0 in 100 units |
| 8 Three verdicts | 3 | 8.5 | after day 14 | 0 in 100 units · 0 in 100 units · 47 in 100 units |
| 9 Rights, cold then EV, pilot onboarding at scale | 5 | 24.5 | after day 14 | 0 in 100 units · 29 in 100 units · 29 in 100 units |
| The day-14 walkthrough database | 1 | 1 | day 13 | yes · yes · yes |
<!--/table-->

**What is not in the fortnight, and why.**
- **The rest of step 9:** the claim case, remedy paths, and cold rooms and EV depots follow proof and the plan (Figure 10).
- **Pilot onboarding at scale** (step 9) waits for an operator's consent and data. The first deep-dive needs none of it: its sources are onboarded by the Analyst role through step 3A's intake, which lands by day 10 (design §2.9).
- **The deep-dive safeguard,** the operator's own target against actual within weeks, needs steps 3A, 4 and 5 live (design §2.9). At the planning pace on three lanes, step 4 is complete by day 10 but step 5 is not by day 14 (table above).
- **The EMS API and the edge gateway on hardware** (OD-22) are step-9 work: the deep-dive needs only files, which upload today, and no operator hardware exists yet.
- **The daily snapshot** (OD-23) is now two slices, `3B7a` and `3B7b`. At the planning pace on three lanes `3B7a` starts on day 14 and both are on the stretch line.
- **Usable capacity** (`4c`) and **pipeline speed** (`DS7`) are queued, not scheduled. Each is pulled by its trigger:

<!--table:queued-->
| Slice | Step | Construct | What it builds | Lane | Units | Depends on | Trigger |
|---|---|---|---|---|---:|---|---|
| `4c` | 4 | B1 | Mini-grid usable capacity by time window, the value chain's first stage | Lane 2 | 2.5 | `3B3`, `0M` | pulled when a lane is free after the must-keep set, at the latest when a pilot pins a real register profile (decisions-register call 23, rev 16.13) |
| `DS7` | D | B3 | Pipeline speed: matcher watermark, skipping idle stages, parallel Sites, larger batches | Lane 1 | up to 4 | `DS4` | only if DS4's re-benchmark measures the L2 template build above 45 minutes (data and build strategy §4, §9); up to 4 units |
| `DS8` | O | B3 | Non-screen. Operations history in the generated world: registry, rights, schedules, incidents with their repeats and maintenance records for all 9 Sites, July to October and November to date, from manifest operations, through the canonical writers and the bulk loader into today's stores | Lane 1 | 2.5 | `DS1b`, `DS3` | pulled in order when a lane is free after the must-keep set (D-L4OPS.7) |
| `OPS1` | O | B1 | Non-screen. Registry rows and fields: what each asset serves; failure mode and out-of-service interval on incidents; kind, visit and cost basis on maintenance records; the measures repeat failures, overdue schedules and scheduled share | Lane 2 | 3 | `3B1` | pulled in order when a lane is free after the must-keep set (D-L4OPS.7) |
| `9a0` | O | B3 | Non-screen. Rights register: a right on an asset or a Site (warranty, insurance, O&M or service contract) with its terms, its state derived from terms and claims; typed or loaded, no extraction (9a then adds extraction) | Lane 1 | 2 | `3A1`, `OPS1` | pulled in order when a lane is free after the must-keep set (D-L4OPS.7) |
| `OPS2` | O | CH1 | Non-screen. Repeat observer: same asset and failure mode inside the operator's window raises a Finding on repeat failures through the structure observer; incident consequences counted once on their nodes; the incident's cost as a cut | Lane 2 | 2.5 | `OPS1`, `3B4` | pulled in order when a lane is free after the must-keep set (D-L4OPS.7) |
| `OPS3a` | O | B1 | Non-screen. Maintenance money: the O&M or maintenance leaf as the fees in force plus invoices, reconciled each month; work under a right's cover carries no operator cost | Lane 1 | 2.5 | `OPS1`, `9a0`, `3A4` | pulled in order when a lane is free after the must-keep set (D-L4OPS.7) |
| `OPS3b` | O | P | Non-screen. A schedule occurrence that uses a crew visit or spends becomes a proactive plan item; responsive work stays an Action on a Finding | Lane 2 | 1.5 | `OPS3a`, `7a` | pulled in order when a lane is free after the must-keep set (D-L4OPS.7) |
| `OPSR` | O | B1 | Non-screen. Operations read, Site and portfolio: assets with state and cover, incidents and repeats, schedules with due state, measures against target, records coverage; scoped by Site key; served through the daily snapshot | Lane 2 | 2.5 | `OPS2`, `OPS3a`, `9a0`, `3B7a` | pulled in order when a lane is free after the must-keep set (D-L4OPS.7) |
| `OPS4` | O | CH5 | Screen. Site Operations tab on all 9 Sites: glance line, what needs action, measures against target, the asset table, the incident, maintenance and right drawers, the records behind the figures | Lane 4 | 4 | `OPSR`, `3B5` | screen: pulled after OPSR, once the Site page passes UI review (D-L4OPS.7) |
| `OPS5` | O | CH5 | Screen. Asset page: state, rights, incidents and repeats on one timeline, maintenance done and due, measures | Lane 4 | 2.5 | `OPS4` | screen: pulled after OPSR, once the Site page passes UI review (D-L4OPS.7) |
| `OPS6` | O | CH5 | Screen. Portfolio Operations entry in place of the five earlier lists: incidents, maintenance, assets and cover, records; one row per Site opening to its items | Lane 4 | 3 | `OPS4` | screen: pulled after OPSR, once the Site page passes UI review (D-L4OPS.7) |
<!--/table-->
- The **selling work** is out of scope by the owner's direction.

## 4. The fourteen days
<!--derives: D11; Figure 10; plan_model-->
*Re-cut 2: the day-1 schedule, kept as the model's record; §0 governs where it differs.*

**Structure first (W1).** No slice builds before the owner approves its structure page. The pages are written from the recreated pack, so most take a quarter or half of a day.
- **Steps 1 and 3C are approved with the pack** (owner, OD-20). Their structure is already the pack's: design CH5 and CH2, `decision-loop-specification.md` §8 (sign-in and roles) and `plan-and-action-workflow.md`. So their slices need no sitting. `3C0a` starts on day 1 on lane C. Step 1 changes what the Portfolio and the site board show, so it is screen work and starts once the UI review passes (day 6 in the model).
- **Step 2's page (`P2`)** is `specs/2a-canonical-format/spec.md` §2, approved by the owner on 20 Nov (item 2: "approved"). `2a` builds on day 1.
- **The sitting days are searched by the model.** It picks the days that land the most work by day 14, then the furthest step, then the fewest sittings. The result is a sitting on day 9, for steps 5 to 9's pages; steps 2, 3A and 3B's pages were approved by the owner on 20 Nov (P2: item 2, "approved"; P3A and P3B: "approve both", `owner/owner-approve-p3a-p3b-2026-11-20.md`).

**Structure pages** (computed):

<!--table:pages-->
| Page | Covers | Architect lane-days | Approved |
|---|---|---:|---|
| P1 | Steps 1 and 3C: the corrected figure; sign-in, roles and the person on every command (pack #2, #12; OD-20) | 0 | with the pack, before day 1 |
| P2 | Step 2: canonical format version 1 and the leaf factor IDs (written 20 Nov: specs/2a-canonical-format/spec.md §2) | 0 | approved by the owner, 20 Nov |
| P3A | Step 3A: record kinds, intake, emulator rules, the contract test (written 20 Nov: specs/3A1-commercial-record-store/structure-page-P3A.md) | 0 | approved by the owner, 20 Nov |
| P3B | Step 3B: registry rows, parity, the structure read and observer (written 20 Nov: specs/3B1-structure-registry/structure-page-P3B.md) | 0 | approved by the owner, 20 Nov |
| P5 | Step 5: target declaration and the attribution rules | 0.5 | sitting 1, day 9 |
| P6 | Step 6: decision records, bounds, the evaluator and the carrier | 0.5 | sitting 1, day 9 |
| P7 | Step 7: plan records, release, versions, the proposal (pack #12) | 0.5 | sitting 1, day 9 |
| P8 | Step 8: economic and causal verdicts | 0.25 | sitting 1, day 9 |
| P9 | Step 9: rights rows and the claim case; cold and EV records | 0.75 | sitting 1, day 9 |
<!--/table-->

**Day by day, at the planning pace** (computed; ✓ marks the day a slice merges):

<!--table:days-->
| Day | Lane A · sources and money | Lane B · structure, the plan's records, data tools, screens | Lane C · the person, decisions, calibration | Owner |
|---|---|---|---|---|
| 1 | — | `2a` ✓, `3B1` | `3C0a` | reads and approves P2, P3A, P3B (approved by the owner, 20 Nov) |
| 2 | `3A1` | `3B1` | `3C0a` ✓, `3C1a` | — |
| 3 | `3A1` ✓, `3A2` | `3B1` ✓, `3B3` | `3C1a` ✓, `3C2` | — |
| 4 | `3A2` ✓, `3A3` | `3B3` ✓, `3B2` | `3C2` ✓, `3C1b` | — |
| 5 | `3A3` ✓, `3A4` | `3B2` ✓, `DS2` | `3C1b` ✓, `0K1` | — |
| 6 | `3A4` ✓, `DS1b` | `DS2` ✓, `1a` | `0K1` ✓, `0K2` | — |
| 7 | `DS1b` ✓, `DS3` | `1a` ✓, `1b` | `0K2` | — |
| 8 | `DS3` ✓, `4b` | `1b` | `0K2` ✓, `0M` | reads 5 pages for sitting 1 |
| 9 | `4b` ✓, `4a` | `1b` ✓, `DS4` | `0M` ✓ | sitting 1 |
| 10 | `4a` ✓, `5a` | `DS4` ✓, `3A5` | `6a` | — |
| 11 | `5a` ✓, `9a` | `3A5` ✓, `3B6` | `6a` ✓, `6d` | — |
| 12 | `9a` | `3B6` ✓, `3B5` | `6d` ✓, `6e` | — |
| 13 | `9a` ✓, `9b` | `3B5` ✓, `3B7a` | `6e` ✓, `WK` ✓, `6c` | reads the day-14 pack |
| 14 | `9b` ✓ | `3B7a` | `6c` | walkthrough of the built screens and the next ranked list |
<!--/table-->

**The fortnight on one chart** (computed). Bars marked critical are committed: they land by day 12.

<!--diagram:fortnight-->

<!--table:gantt-->
```mermaid
gantt
  title The fortnight at the planning pace (days from day 1)
  dateFormat X
  axisFormat %s
  section Lane A
  3A1 B3 :crit, g3A1, 1.06, 2.31
  3A2 B3 :crit, g3A2, 2.31, 3.56
  3A3 B3 :crit, g3A3, 3.56, 4.81
  3A4 B3 :crit, g3A4, 4.81, 5.67
  DS1b B3 :crit, gDS1b, 5.67, 6.16
  DS3 B3 :crit, gDS3, 6.16, 7.41
  4b B1 :crit, g4b, 7.41, 8.47
  4a B1 :crit, g4a, 8.47, 9.53
  5a B2 :crit, g5a, 9.53, 10.78
  9a B3 :g9a, 10.78, 12.41
  9b B3 :g9b, 12.41, 13.66
  section Lane B
  2a B3 :crit, g2a, 0.0, 0.67
  3B1 B1 :crit, g3B1, 0.67, 2.31
  3B3 B1 :crit, g3B3, 2.31, 3.56
  3B2 CH1 :crit, g3B2, 3.56, 4.62
  DS2 B3 :crit, gDS2, 4.62, 5.87
  1a CH5 :crit, g1a, 5.87, 6.92
  1b CH5 :crit, g1b, 6.92, 8.56
  DS4 B3 :crit, gDS4, 8.56, 9.62
  3A5 B3 :crit, g3A5, 9.62, 10.68
  3B6 B1 :crit, g3B6, 10.68, 11.35
  3B5 B1 :g3B5, 11.35, 12.98
  3B7a B1 :g3B7a, 12.98, 14.0
  section Lane C
  3C0a CH2 :crit, g3C0a, 0.0, 1.06
  3C1a CH2 :crit, g3C1a, 1.06, 2.31
  3C2 CH2 :crit, g3C2, 2.31, 3.37
  3C1b CH2 :crit, g3C1b, 3.37, 4.23
  0K1 CH3 :crit, g0K1, 4.23, 5.48
  0K2 CH3 :crit, g0K2, 5.48, 7.12
  0M CH3 :crit, g0M, 7.12, 8.56
  6a CH3 :crit, g6a, 9.0, 10.25
  6d CH3 :crit, g6d, 10.25, 11.31
  6e CH4 :g6e, 11.31, 12.37
  WK tooling :gWK, 12.37, 12.85
  6c CH3 :g6c, 12.85, 14.0
  section Owner
  Sitting 1 :milestone, s1, 8, 8
  Walkthrough :milestone, s9, 13.5, 13.5
```
<!--/table-->

**The owner's time** (computed; TW11: 240 minutes a day, `owner/owner-sitting1-answers-2026-11-18.md` on `main`). The fortnight asks for 460 owner minutes in all:

<!--table:owner-->
| Day | Owner minutes | What |
|---:|---:|---|
| 1 | 105 | reads and approves P2, P3A, P3B (approved by the owner, 20 Nov) |
| 8 | 100 | reads 5 pages for sitting 1 |
| 9 | 105 | sitting 1 |
| 13 | 30 | reads the day-14 pack |
| 14 | 120 | walkthrough of the built screens and the next ranked list |
| **14 days** | **460** | busiest day 120 minutes, within the 240-minute day |
<!--/table-->

**Rules each lane follows** (`.ai/RULES.md` §7; owner rules):
- **One unit at a time.** Each lane has one unit in build and one in review. A unit that touches shared code is reviewed and merged before the next unit builds on it.
- **Heavy work goes through the slot pool,** and one heavy database job runs at a time. Heavy work is check-all, tsc, vitest, Postgres test files, browser captures and database jobs.
- **Databases:** only `*_test` and `<prefix>_audit*` databases, and no full suite unless the owner asks.
- **Hands off:** never ports 5490 or 8990, never Docker during task work.
- **The day-14 walkthrough** runs only on a clean, good database. The owner accepted a verified clone as one (sitting 1, item 8).

## 5. Pace, the stretch line and the drop order
<!--derives: plan_model; Figure 10-->
*Re-cut 2: the day-1 schedule, kept as the model's record; §0 governs where it differs.*

**What lands at each pace** (computed):

<!--table:pace-->
| Case | Units landed by day 14 | Furthest step complete | Slices landed |
|---|---:|---|---:|
| slip pace (2 units a lane-day) | 61.5 | 2 Canonical format and leaf factor IDs | 23 of 61 |
| **planning pace (3), 3 lanes** | 90.5 | 3A Sources | 33 of 61 |
| observed pace (4.8) | 127.5 | 4 Join at the money leaves | 45 of 61 |
| planning pace, 2 lanes (the first re-cut) | 64 | 3A Sources | 24 of 61 |
| planning pace, all 4 lanes building | 116 | 4 Join at the money leaves | 41 of 61 |
| planning pace, no screen hold | 83.5 | 3A Sources | 31 of 61 |
| planning pace, no rework allowance | 101.5 | 3A Sources | 37 of 61 |
<!--/table-->

**Reading.**
- **Lanes matter more than pace here.** The third lane lands 90.5 units against 64 on two; all four lanes building would land 116 and complete step 4. At the slip pace the fortnight still completes step 2.
- **The screen hold costs nothing on three lanes.** With no hold 83.5 units land, 7 fewer: until day 6 every lane has non-screen work ready, and screen slices taken earlier only push must-keep work later. With more lanes the hold starts to bind, so the model is re-run the day the UI review passes.
- **The rework allowance costs no complete step here.** Without it, the furthest complete step stays at step 3A, though 11 more units land (101.5 against 90.5). The allowance stays, because this fortnight's work is new schema and money.

**The stretch line** (computed): what lands by day 14 at the observed pace but not at the planning pace. If the first week runs at the observed pace, these are next, in delivery order:

<!--table:stretch-->
| Slice | Step | Lands at the observed pace on day |
|---|---|---:|
| `0E` Spike E | 0 | 7 |
| `3B4` Structure observer | 3B | 11 |
| `3B7a` Structure snapshot store (OD-23), the structure read served from it with its as of, and the rebuild check | 3B | 6 |
| `3B7b` structure_dirty and triggers 1 to 6; recalculation pending; the worker at the daily run and on demand; Recalculate now on the pending note | 3B | 11 |
| `3C0b` The sign-in page and Organisation settings' roles on screen | 3C | 13 |
| `3C3` UI controls for the work routes that exist only in the API | 3C | 12 |
| `5b` Attribution | 5 | 13 |
| `5c` The bridge on screen, factor by factor, labelled Emulated until the operator's exports replace the emulators | 5 | 14 |
| `6b` Bounds as rows | 6 | 13 |
| `6c` Evaluator | 6 | 13 |
| `6g` Mto demand and repair decisions (revenue side, after the join), with the quotes emulator | 6 | 14 |
| `8a` Economic and causal verdicts beside the operational one | 8 | 14 |
<!--/table-->

**If it slips, what drops first** (computed): slices that land at the planning pace but not at the slip pace, latest step first. The must-keep slices never drop: the slot pool, steps 1, 2 and 3A's store, intake, emulators and amounts, the registry, the pinned Findings, the structure read, the recorded person (`3C0a`, `3C1`, `3C2`), and the walkthrough database. On two lanes they also go first (D-BW1.6).

<!--table:drop-->
| Order | Slice | Step | Lands at the planning pace on day |
|---:|---|---|---:|
| 1 | `9b` Supplier-claim case and its states | 9 | 14 |
| 2 | `9a` Rights rows from contract documents, AI-assisted, a person approving each row; contract-document emulator | 9 | 13 |
| 3 | `6e` Stop-setting verification family (an unknown rule fails closed today) | 6 | 13 |
| 4 | `6d` Stop-threshold carrier as a domain-action apply path, linked to its decision option | 6 | 12 |
| 5 | `5a` Targets and budget lines at factor level, declared by the operator with the declarer recorded; objectives become factor targets | 5 | 11 |
| 6 | `3B5` Site board | 3B | 13 |
| 7 | `3B6` Cold-room and captive-EV structures declared and tested from the start (revenue not applicable, never zero) | 3B | 12 |
| 8 | `3A5` Evidence labels | 3A | 11 |
| 9 | `DS4` Template ladder, the world commands and the build manifest; the stage-by-stage re-benchmark of the build cost (delivery §5) | D | 10 |
| 10 | `0M` Spike M | 0 | 9 |
<!--/table-->

## 6. What day 14 shows on screen
<!--derives: §2.1; §2.3; §2.4; §2.6; §2.8; Rules; D14; plan_model-->
*Re-cut 2: the day-1 schedule, kept as the model's record; §0 governs where it differs.*

Only built features are shown, each with how it is known (design Rules). At the planning pace on three lanes, with the screen slices built from day 6 and merged only after the owner's walkthrough of them (D7):

| Screen | What it shows on day 14 | How each figure is known |
|---|---|---|
| Portfolio Optimize card (step 1) | the period's figure, or its day and scope stated; fields the API computed and the screen hid | as today's wording |
| Site board (3B) | driver lines as factor rows from the registry; today's Findings on the factors they observe, such as Kobo's 25<!--fig:sites.lakeside-power/Kobo.actual.nodes.candidate_l--> L candidate (as the simulated world records it, dispatch-3.2; dispatch-3.3 re-classifies it in 0K4f) and 120<!--fig:sites.lakeside-power/Kobo.actual.nodes.unexplained_l--> L unexplained litres | *Recorded* or *Measured* from telemetry and fuel records |
| Evidence labels (3A) | *Emulated* beside *Recorded* on every figure; no total above its weakest part | from the record's own label (D14) |

Built without a screen yet, and so not shown:
- operator accounts and roles, and the person recorded on every command, with each Action's creator, owner and due date (step 3C; the sign-in page `3C0b` and the work controls `3C3` are stretch);
- the money leaves from emulated records (`4b`, day 14), until the bridge or the site board reads them;
- the data slices: the shapes, the loader and the template ladder, which build the walkthrough database (`WK`, day 13);
- spike K's replays (`0K1`, `0K2`).
- targets and budget lines at factor level (`5a`) and the energy-to-cash observer (`4a`);
- the decision records, bounds, evaluator, stop-threshold carrier and its verification family (`6a` to `6e`), and the economic and causal verdicts (`8a`): their screens (`6f`, `8c`) are next fortnight's.

The walkthrough says so plainly rather than show a mock-up in their place.

## 7. Decisions for the owner at the pack approval
<!--derives: D11; Decisions; plan_model; Figure 10-->
*Re-cut 2: the day-1 schedule, kept as the model's record; §0 governs where it differs.*

| # | Decision | Context | Default, applied until the owner answers |
|---|---|---|---|
| 1 | Does approving the recreated pack also approve the structure of steps 1 and 3C? | Their structure is the pack's own (design CH5 and CH2; `plan-and-action-workflow.md`). Without this, steps 1 and 3C wait for sitting 1. With it, step 1 starts on day 1 and step 3C on day 5, after spike `0K` | **Decided by the owner, 19 Nov (OD-20): yes** |
| 2 | Hold one sitting, on day 9 | Computed (re-cut 20 Nov, after P3A and P3B were approved): the model's search picks the day. It approves steps 5 to 9's pages | Yes. **P3A and P3B approved by the owner, 20 Nov** ("approve both"); the default stands that a person's own change recalculates on demand, by the button |
| 3 | The planning pace, with a rework allowance | 3 units per lane-day, against 4.8 units per lane-day observed, plus 15 in 100 for rework | Yes |
| 4 | The heavy-tool slot pool first | W4 as amended (sitting 1, item 7) | Already decided by the owner |
| 5 | Re-cut after the first week | If week 1 runs at the observed pace, the stretch line (§5) comes in. If it slips, the drop order applies | **Done early, 20 Nov,** at the non-screen build start, because its inputs changed (data slices, two lanes, the screen hold). Re-run again when the UI review passes and when a lane opens |
| 6 | Two known biases of the model, corrected together at the day-7 re-cut | *Pessimistic:* a lane waiting for the slot pool idled. *Optimistic:* the spec handshake and the snapshot slice had no time in the model | **Done 20 Nov:** the pessimism is gone (`T1` merged before day 1); the handshake carries 0.1 lane-days a slice (assumption) and the snapshot is `3B7a` and `3B7b`. `commercial-plan.md` is re-checked by the coordinator |
| 7 | Which mock governs the fortnight's screen slices (`3B5`, `3C3`, `5c`, `5d`; review H, M6) | The recreated mock-up vNEXT has not had the owner's inspection | **Decided by the owner, 20 Nov: "D7- yes, default"** (`decisions-register.md` D7; `owner/owner-answers-uiux-datastrat-d7-2026-11-20.md`): once the owner has approved the pack and inspected vNEXT, vNEXT governs these slices, each spec citing the element D7 names. Until then a screen slice may build, but it does not merge without the owner's walkthrough of it. Since 20 Nov screen slices also wait for the UI review of the Decision page, the Site page and the plan screen (owner: "yes, start the non-screen build work now") |
| 8 | Approve step 2's structure page (`P2`) | Written 20 Nov as `specs/2a-canonical-format/spec.md` §2: one page, the canonical format version 1 and the leaf factor IDs, from `integration-design.md` §3. W1 needs the owner's approval before `2a` builds | **Approved by the owner, 20 Nov** (item 2: "approved"; `owner/owner-answers-eight-open-questions-2026-11-20.md`) |
| 9 | Does "non-screen" include the person step's API (`3C0a`, `3C1`, `3C2`)? | The owner named "data, the calculation engine, integrations". `3C0a` is non-screen and must-keep, and steps 5 to 7 need the recorded person, but it is neither data nor the engine | **Yes** (D-BW1.3): `3C0a` is built (lane C). If the owner meant only those three, step 3C's next slices wait for the screens |

**Pushback, for the owner.** The owner asked to advance "as much as possible". On 20 Nov the binding limit is lanes, not effort, memory or sittings. The third lane (owner, item 3) is worth 26.5 units in the fortnight; the fourth would add about 25.5 more and complete step 4. The screen hold costs nothing on three lanes, so it needs no change.
