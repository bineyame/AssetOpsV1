# BW1 rulings: the non-screen build start and the fortnight's re-cut

Architect (Claude), 2026-11-20. The owner, 20 Nov: "yes, start the non-screen build work now"
(`owner/owner-start-non-screen-build-2026-11-20.md`). Each ruling has its reason. Index lines:
`.ai/decisions/index-rulings-7.md`. The re-cut is in `Docs/demo-sprint/product-direction-layer4/plan_model.py`,
`two-week-build-plan.md` and `delivery-plan.md` (branch `task/build-wave1-specs`).

## D-BW1.1 The first wave: lane A `3C0a`, lane B `2a`

- **Ruling.** Lane A (W4 lanes 1 and 3) starts `3C0a`, operator accounts and roles behind the API
  (`specs/3C0a-operator-accounts/`). Lane B (W4 lanes 2 and 4) starts `2a`, the canonical format and leaf factor IDs
  (`specs/2a-canonical-format/`). Next in each lane, by the model: lane A `3C1`, then `3A1` to `3A4`; lane B `3B1`,
  `3B3`, `3B2`, then step 1 once the screens are released.
- **Why these.** The re-cut model ranks the must-keep set first on two lanes (D-BW1.6), then delivery order. Among
  must-keep slices that are non-screen and released on day 1, `2a` (step 2) is the root of both build lanes: it
  unblocks `3A1`, `3B1` and `DS1b`, so `3A3` and `DS3`. `3C0a` is the only other must-keep slice released on day 1,
  because step 3C's structure was approved with the pack (OD-20). `3A1` and `3B1` wait for `2a` and for pages P3A and
  P3B.
- **P2 condition.** `2a` needs its structure page approved (W1). The page is written as `specs/2a-canonical-format/spec.md`
  §2 and asked of the owner with this ruling. The model schedules it as approved on day 1. If it is not approved when
  `2a`'s handshake ends, lane B builds `DS2` (shapes, 3 units, non-screen, no gate) first and `2a` follows. `DS2`'s
  spec is then the next to write.
- **The candidate set checked against the code.** Step 1 is not non-screen (D-BW1.2): `1a` corrects the figure the
  Portfolio's Optimize card shows (`backend/assetops_backend/site_outcomes/read.py:675` `summary_window`: a
  mini-grid Site reads one day, `WINDOW_BASIS_DAY`, over a period range; the card renders it through
  `frontend/src/estate/estateClient.ts`), and `1b` only renders fields on the Portfolio and the site board. Both
  change what a person sees, on pages the UI review is rebuilding. So step 1 waits. `2a` exists nowhere in
  `backend/`, `contracts/` or `simulator/` (D-DS1.1); `world/leaves.py` is its one placeholder. No account, session
  or role table exists: today's principals are injected per route (`create_app`: `mini_decision_principal`,
  `domain_work_principal`, `operational_entry_principal`), and every human write is refused (`financial_api.py:55`).

## D-BW1.2 Screen and non-screen

- **Ruling.** A slice is *screen* when it adds or changes anything a person sees, including a figure an existing
  screen renders. Otherwise it is *non-screen*. Screen slices: `1a`, `1b`, `3A5`, `3B5`, `3B7b`, `3C0b`, `3C3`, `5c`,
  `5d`, `6f`, `7e`, `7f`, `7g`, `8c`, `9a` (15 of 62). They build only after the Decision page, the Site page and the
  plan screen pass UI review (owner, 20 Nov); D7's walkthrough rule applies to them. The model assumes the release at
  the start of day 6 and is re-run when it happens.
- **Why the figure counts.** Changing a figure an executive reads is a screen change even with no frontend diff. The
  UI review is rebuilding those pages, so a figure change merged now would be reviewed twice.
- **Mixed slices.** `3B7b` (the worker and *Recalculate now*) and `9a` (rights rows and the person approving each)
  stay whole and held: their non-screen parts unblock nothing scheduled in the fortnight. `3C0` is split (D-BW1.3).

## D-BW1.3 `3C0` is split, and its API part is inside "non-screen"

- **Ruling.** `3C0` (3 units) becomes `3C0a` (accounts and roles behind the API, 2 units, non-screen) and `3C0b` (the
  sign-in page and Organisation settings' roles, 1 unit, screen). `3C1` depends on `3C0a`. `3C1` records the person
  on every command when one is signed in; the refusal of a command with no signed-in person switches on in the same
  merge as `3C0b`, so today's screens never lose their commands.
- **Why split.** `3C0a` unblocks `3C1`, `3C2`, and through them `5a`, `6a` and `7a`; holding it behind a sign-in
  screen would hold steps 5 to 7.
- **Owner's words.** The owner named "data, the calculation engine, integrations". `3C0a` is none of those, but it is
  non-screen and must-keep, and the pack approved its structure (OD-20). Default: inside the start. If the owner
  meant only those three, lane A starts spike `0K1` instead (decision queue, `two-week-build-plan.md` §7, item 9).

## D-BW1.4 Spike `0K` is split; slices over six units are a class

- **Ruling.** `0K` (7 units) becomes `0K1`, the forward-replay port method and its host adapter proven by replaying a
  recorded run to the kernel's own trajectory (3 units), and `0K2`, Kobo's stop-threshold and reserve replays through
  the port (4 units). `0M`, `0E` and `6c` depend on `0K1`, since they need the port, not Kobo's replay (the review's
  GM2 ruling: the evaluator only wires to the port).
- **The class (W6).** A slice over 6 units is split before it is built (W4). The sweep of the slice list finds three:
  `0K` (split now), `9d` (6.5) and `9e` (7.5). `9d` and `9e` are in step 9, outside the fortnight; they are split
  when their structure page P9 is written.

## D-BW1.5 The data slices' places, and the queued list

- **Ruling.** The data and build strategy's slices enter the model with D-DS1.1 and D-DS1.14's units: `DS1` 4 (done;
  DS1m finishing on its own lane), `DS1b` 1 (after `2a`, `DS1`), `DS2` 3, `DS3` 3 (after `DS1b`, `3A2`), `DS4` 2.5,
  `3B7a` 2.5 and `3B7b` 3 (step 3B, after `3B3`, page P3B), and `DS6` 2.5 on the stretch line. They form step D
  ("Data"), ranked after step 2 as the strategy orders them ("right after `2a`"); `DS1b` and `DS3` sit in lane A
  (they write sources), `DS2`, `DS4` and `DS6` in lane B (tooling). `4c` and `DS7` are queued, not scheduled, each
  with its trigger: `4c` when a lane is free after the must-keep set or a pilot pins a register profile
  (`decisions-register.md` call 23); `DS7` only if `DS4` measures the L2 build above 45 minutes.
- **Why.** The strategy's §10 question 8 (owner: "default is fine") put `DS1` to `DS4`, `3B7a` and `3B7b` in the
  fortnight, `DS6` on the stretch line and `DS7` conditional.

## D-BW1.6 The model's inputs for the re-cut

- **Ruling.**
  - Day 1 is 20 Nov.
  - Two build lanes plan the fortnight (coordinator, 20 Nov), with three- and four-lane cases shown beside them.
  - Each slice carries 0.1 lane-days for the spec handshake (assumption).
  - On short lanes the must-keep set goes first, then delivery order, then the work a slice unlocks.
  - `T1` and `DS1` count as done before day 1.
- **Why must-keep first.** Under delivery order alone, on two lanes `3B2` and `3C2` missed day 12 and the check
  failed. Ranking must-keep first lands them all by day 12, at no cost in units (64 against 63.5 before `3C0a` became 2.5 units). Calibration (step
  0) was ranked first only because it had a lane of its own; on two lanes it is gap work.
- **Why the handshake time.** It is the pack's decision 6, the optimistic bias to correct at the re-cut. The value is
  an assumption, to be measured from `2a` and `3C0a`.
- **Result.** At the planning pace the fortnight lands 64.5 units in 24 slices (with `3C0a` at 2.5 units, 3C0a P14) and completes step 3A (it was 111.5 units
  and step 5 with four lanes and no data slices). Four lanes would land 115 and complete step 4; a third lane, once
  DS1m frees one, lands 91.5. The screen hold costs nothing on two lanes.

## D-BW1.7 The third lane, and P2 approved (owner, 20 Nov)

- **What the owner decided** (`owner/owner-answers-eight-open-questions-2026-11-20.md`). Item 2: "approved", so step
  2's page P2 is approved and D-BW1.1's DS2 fallback is not needed. Item 3: "accept", three build lanes now and four
  later.
- **Ruling.** `plan_model.py` plans on three lanes:
  - lane A: sources and money (W4 lane 1);
  - lane B: structure, the plan's records, data tools and screens (lanes 2 and 4);
  - lane C: the person, decisions and calibration (lane 3; the lane that built `3C0a` continues with `3C1` and `3C2`).
- **The new lane's first unit is `DS1b`**, the generator's canonical writers (`specs/DS1b-canonical-writers/`). Its
  handshake runs while `2a` is built, and its code starts when `2a` merges.
- **Why `DS1b`.**
  - It is lane A's first slice in the 3-lane schedule. `3A1` waits for both `2a` and structure page P3A, which is
    not yet approved.
  - `DS2` is lane B's, after `2a`.
  - `0K1` is lane C's, after `3C2`.
  - Taking `0K1` or `DS2` into lane A instead would delay the must-keep `3A` chain behind a slice of 3 units.
- **Effect.** 91.5 units land in 33 slices by day 14, through step 3A, with step 4 also complete by day 10. On two
  lanes it was 64.5 units in 24 slices.
- **Item 6** ("accept default": a driver with no target line reads as a labelled assumption) needs nothing in the
  build specs. `DS1b` writes budget lines only where the operator's plan record holds them (D-DS1B.4), and the leaves
  without one are what item 6 labels.

## D-BW1.8 Re-cut 2: the deep-dive path first (owner, 20 Nov)

- **Ruling.** Days 2 to 14 are re-ordered around the deep-dive path (`two-week-build-plan.md` §0.1): `3B3`, `3A2`,
  `3A4`, `3A3`, `3A6`, `ON1`, `3A7`, `4b`, `5a`, `3B7a`, `5b`, `4d`, `5c`, `DDR`; 31.5 units, landing day 11 at the
  planning pace and day 13 at the slip pace on four agents. Steps 6 and 9, `3B5`, `1b`, `DS2`, `3B7b`, `3C0b` and
  IA-2c to IA-2e move to the next fortnight. Page P5 is asked of the owner alone on day 3; P6 to P9 move to the day-14
  sitting. Applied by default until the owner answers RC1.
- **Why.** The owner: re-cut "around the deep-dive path" (`owner/owner-recut-fortnight-deep-dive-2026-11-20.md`). On
  the day-1 ordering step 5 was not complete by day 14, so no executive could see their own gap in money in the
  fortnight. `DS3` is not on the path: real exports go through `3A2` (D-3A1 Q2).

## D-BW1.9 `5c` is the one deep-dive screen

- **Ruling.** `5c` shows the month's contribution against target, the gap by heading, the bridge factor by factor and
  cash apart, citing vNEXT `#/portfolio` "the month in one line" and Assure's "Contribution's bridge by heading"
  (`walkthroughs.md` §2, steps 1 to 3) in the hub shape after the IA-1 stop. It applies `3A5`'s label rule on its own
  figures. Its dependencies on `3B5` and `3A5` are cut.
- **Why.** The board and the labels on every other screen add no money to the deep-dive, and those screens are being
  rebuilt by shape; building them now would be reviewed twice.

## D-BW1.10 Two dependency cuts on the money chain

- **Ruling.** `4b` depends on `3A4` and `3B3`, not `3A3`: its tests use `DS1b`'s canonical records as fixtures. `5a`
  depends on `3A4`, `3B3`, `3C1a` and P5, not `4b`: targets are declared on `2a`'s leaf IDs and read from stored
  budget lines.
- **Why.** Neither slice reads what the cut slice builds. The cuts shorten the critical chain by about two days.

## D-BW1.11 Five new units; the HELD_NOT_CALCULATED sweep

- **Ruling.** New: `3A6` (source profiles as data, pinned against the operator's sample, admitted by the contract test;
  2.5), `ON1` (deep-dive tenant from one onboarding file; 1.5), `3A7` (a closed month reconciled against management
  accounts before money reads *Recorded*; 1.5), `4d` (monthly litre split; 3), `DDR` (end-to-end rehearsal, including
  an export of an unseen shape through a new profile with no code change; 1).
- **Why.** Without `3A6` an operator's own export cannot be read without hand reshaping. Without `ON1` there is no
  tenant for it. Without `3A7` the screen could show their money as recorded while it disagrees with their accounts
  (integration design §7.2's pilot validation gate). Without `DDR` the path is not proven end to end.
- **Class (W6).** Every leaf `3B3` lists as HELD_NOT_CALCULATED needs a named slice. The sweep: `delivered_kwh` is `4a`;
  `necessary_l`, `candidate_l` and `unexplained_l` had none and are `4d`; `dawn_days_below` is `6b`;
  `reduced_days`, `hours_per_day`, `customer_hours_interrupted` and `field_visits` had none and are `OPS2` and `OPSR`
  (queued). Default until the owner says otherwise.

## D-BW1.12 The UI lane after the IA-1 stop

- **Ruling.** IA-1 finishes to its owner stop (day 5). The UI lane then builds `5c`, and IA-2 resumes on day 11.
- **Why.** The shape rebuild changes the mock-up, not the live product; no operator's own data reaches a screen through
  it. `5c` is the screen that converts, and it cites the hub shape, so it follows the stop and comes before IA-2.
