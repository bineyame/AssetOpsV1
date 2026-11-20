# L4-OPS rulings: operations inside the structure

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines are in `.ai/decisions/index-rulings-7.md`.
Source: the owner's answers to the eight open questions, verbatim in `owner/owner-answers-eight-open-questions-2026-11-20.md`
(item 1 option B, item 5, item 7); the independent UX audit, C4 (`.agent/ux-audit-2026-11-20.md`); the shell drill-down review,
H3, H4 and item 3 (`.agent/REVIEW-shell-drilldown-r1.md`). Pack: `Docs/demo-sprint/product-direction-layer4/`, design `rev 16.16`
§2.10 and Figure 11; owner decisions OD-26 to OD-28; register calls 29 to 36. The design section is the structure; these rulings
are what the build and the UI lane follow.

## D-L4OPS.1 The Site Operations tab, the asset page, drawers and one rail entry

- **Ruling.** The Site page has three tabs: Overview, Operations, Financials. Operations is the same on all 9 Sites:
  - *Glance:* one line, the assets in service out of all, open incidents with their repeats, the nearest deadline on a right.
  - *What needs action:* open incidents, repeat Findings, overdue or due-soon schedules, notice deadlines; each row with its
    owner, due date and the Action or decision it opens; at most 7 rows, then "Show all".
  - *Measures against target* for the period chip: the Protect measures (obligation hours without backup, asset-days or
    charger-days out of service, repeat failures, overdue schedules, days or nights without backup cover) and the operations
    measures (availability, field visits, kWh per visit, scheduled share). The Overview's "Operations measures at this site"
    moves here; the Overview keeps the four headings' strip (uiux guide §2.2a budget).
  - *Assets:* one row per asset: what it serves, its state since when (in service, reduced, out of service), its cover word,
    its last incident with a repeat mark, its next maintenance. A row opens the asset page.
  - *Records behind these figures:* collapsed; operational records and evidence by source, with coverage; opens the source drawer.
- The **asset is a page** (an object with identity). An **incident, a maintenance record and a right open in drawers** from any
  list, each linking to its asset page and to its Finding, Action or decision.
- The five earlier rail items (Assets with warranty, Incidents, Maintenance, Operational records, Evidence) become **one rail entry,
  Operations**, with four views: incidents, maintenance, assets and cover, records. Each view shows one row per Site (counts,
  repeats, overdue, deadlines; capped, "Show all") and opens to its items. Evidence's coverage view is the Portfolio's Scope tab.
- **Scope by data:** every row carries its Site key; a list filters on the key, never on rendered text (review H3). A Site with
  no source shows "not available yet" inside the same structure; no stub tab is reachable (audit C4).
- **Mock.** Governing elements: vNEXT `#/site/<site>` Overview, its "Operations measures at this site" section and the
  "obligations and rights" in its description; the v7.0 lists `#/incidents`, `#/maintenance`, `#/assets`, `#/assets-warranty`,
  `#/oprecords`, `#/globalevidence`. `MOCK DEVIATION` category D2 (improvement, flagged to the owner): five rail items become
  one, and the Site gains a tab the mock-up does not draw. The UI lane adds the row to `.agent/mock-departure-register.md` when it
  builds the mock-up change.
- **Reason.** The review's item 3: with only Overview and Financials a Site has no operating view, and an executive judges
  "beyond monitoring" against the tools they run. One grammar (uiux guide §8) and one row per Site keep it usable at 300 Sites.

## D-L4OPS.2 Incidents: consequences counted once; cost as a cut

- An incident (today's work case of kind incident) gains a **failure mode** and an **out-of-service interval** (from, restored).
- Its consequences are links to the nodes it moved, each with its quantity or amount: obligation hours, asset- or charger-days,
  cooling minutes, unproven days (Protect); compensation, penalties, extra fuel, invoiced repair (Optimize). Each is counted once,
  in its node. Counting rule (manifest `operations.counting`): each calendar day from the out-of-service day to the day before
  restoration; an open incident counts to the period end.
- The incident's **cost** is the sum of its money links, all of one evidence class or shown at the weakest, as a cut across the
  leaves: never a new leaf and never added to them.
- **Reason.** The money a failure caused is already in cost to serve; a second total would count it twice (Rules 2 and 4).

## D-L4OPS.3 Repeats become a Protect measure and a Finding

- A **repeat** is an incident on the same asset with the same failure mode inside the repeat window after an earlier one.
- Measure `repeat_failures`: P2, Protect, target 0, derived. Under OD-3 its tolerance defaults to 0, so every repeat raises a
  Finding pinned to it (structure observer, slice `OPS2`), reusing the Finding's recurrence history. The Finding carries the
  repeat set's cost (D-L4OPS.2) and links to the decision on the asset; it keeps its own heading (OD-25), so no decision changes
  heading. Demonstration: Kisiwa GEN-KS-01 (14 Aug, 30 Oct, alternator; linked to `kisiwa-genset`) and Kasarani CH-K2 (22 Aug,
  1 Nov, contactor weld; linked to `kasarani-charger`). The cold rooms have none: Thika's controller fault is a first occurrence
  (its quarterly tests are logged, 3 of 3); the checker's planted copies prove the rule on every vertical.
- **Reason.** The owner: "Incidents impact operating bottomline, especially repeated ones."

## D-L4OPS.4 The repeat window is an operator setting

- Default 90 days, set per operator in Organisation settings, recorded with who set it. The tolerance of `repeat_failures`
  follows OD-3. **Reason:** 90 days spans a quarterly service cycle; operators differ, so it is a setting, not a constant.

## D-L4OPS.5 Maintenance: scheduled or responsive; the leaf reconciles

- A maintenance record gains **kind** (scheduled, responsive), **visit** (yes or no; feeds the O2 field-visit measure) and
  **cost basis**: in a contract's fee, invoiced (with its amount), or under a right's cover (citing the right).
- *Scheduled:* a schedule occurrence that uses a crew visit or spends becomes a proactive plan item naming the right or Protect
  measure it keeps, or "no factor (upkeep or compliance)" (OD-5). *Responsive:* an Action on a Finding; a work case's origin
  stays the Finding or plan item (call 4).
- The Site's O&M or maintenance leaf, each month = the monthly fees of the Site-scope contracts in force + the invoiced records.
  Work under cover adds nothing. Checked in the pack for every Site-month, July to October (OP6).
- **Reason.** Crew visits are the plan's limited resource (OD-12), and a money leaf must reconcile to its records.

## D-L4OPS.6 The rights register comes before extraction

- A right is a row on an asset (or a list of assets) or on a Site: type (equipment or workmanship warranty, insurance, O&M or
  service contract), counterparty, term, conditions, exclusions, notice period, remedy, fee. A row may point at a manifest
  entitlement (`from`) instead of restating its terms.
- Its state is derived as of the read: expired (term ended); otherwise for a contract or policy, in cover; for a warranty, claim
  open (notified, acknowledged or accepted), notice due (an occurrence with a notice deadline), conditions incomplete
  (insufficient evidence), else in cover. Rights with an open deadline (notice due, or a claim open with a running SLA clock)
  must equal each portfolio's `rights_with_open_deadline` (OP8).
- New slice `9a0` (the register, typed or loaded) comes before `9a` (AI-assisted extraction into it, a person approving each row).
- **Reason.** The registry is the home of cover; the Operations tab needs rights before extraction exists.

## D-L4OPS.7 Slices: queued, in order, after the must-keep set

- Ten slices, 26 units (`delivery-plan.md` §2, queued table): `DS8` 2.5, `OPS1` 3, `9a0` 2, `OPS2` 2.5, `OPS3a` 2.5, `OPS3b`
  1.5, `OPSR` 2.5 (non-screen); `OPS4` 4, `OPS5` 2.5, `OPS6` 3 (screen). Pulled in that order when a lane is free after the
  must-keep set; the screen slices also wait for the Site page's UI review.
- `check_manifest.py` `operations()` runs after the history checks, so H9's baseline is unchanged.
- **Reason.** Put on the schedule, they displaced a committed slice of the approved fortnight (`plan_model.py` run, 20 Nov). The
  owner's queue rule pulls them as soon as a lane is free.

## D-L4OPS.8 Kasarani's service fee is its maintenance leaf

- The Ampere service contract's fee is the maintenance leaf, 300 a month. The SLA's text "5% of monthly service fee (400)" is
  corrected to 300 by the data lane, which regenerates the mock-up fixtures (`fixtures.js`) and updates the hand-typed scan's row.
- **Reason.** A fee must be the leaf it books to; 400 has no leaf, so the leaf would not reconcile. No evaluated figure reads it.

## D-L4OPS.9 The tie line reads "Unbilled energy" (OD-28)

- The crossing's screen words, everywhere ("of which unbilled energy"), held in one UI constant; the rows stay named: "meters not
  yet mapped to a customer" and "authorised adjustments". Replaces D-RECON.2's "Metered but not billed" (words only; the rule
  stands).
- **Basis.** Utility energy accounting calls energy recorded at the customer's meter but not billed "unbilled" energy or
  consumption. The IWA water balance, the most formal published utility balance, files it as "unbilled metered consumption" and
  keeps it apart from losses. The wider terms do not fit: "non-technical losses" also covers theft and metering error before
  the meter, and authorised adjustments are not losses (owner rule: never "theft"); AT&C "commercial losses" include the
  collection shortfall, which here is cash outside contribution; "billing efficiency" (energy billed ÷ energy input, India's
  National Power Portal glossary; Nigeria's regulator reports it quarterly) also absorbs technical losses. "Service-to-charge"
  stays the brief's internal name for O3.
- **Reason.** The owner: "use whichever is the industry standard term".
