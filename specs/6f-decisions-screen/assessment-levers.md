# 6f Q1 assessment: why only mini-grid has decisions, and the fix at the source

Architect (Claude), 22 Nov 2026. Answers the owner's challenge to 6f handshake Q1
(`owner/owner-6f-q1-levers-2026-11-22.md`): "why are these sites fundametally different, is the architect proposing a
code solution to a data issue?" Code read on `main` at `ecd0bfb5a` (6a and 6c merged). **Status: proposal for owner
alignment. Nothing here changes a ruling on `main` until the owner agrees the direction.**

## 1. Short answer

- **The Sites are not different.** Cold rooms and EV depots have the same structure as mini-grids: a registry of factors
  (`structure/rows_cold_chain.py`, `rows_ev_depot.py`), Findings pinned to factors (`structure/pins.py`), and the same
  valuation core. 6c's evaluator already values a cold-room option (fixture C1) and an EV schedule option (fixture E1)
  with no vertical branch (`specs/6c-option-evaluator/spec.md` §6, Done question 6).
- **The gap is in the model, not in the Sites.** Two things were built for one case only:
  1. **The lever catalogue has one row.** `structure/levers.py` `LEVERS` holds only `generator_stop_reserve` (Kobo's
     generator stop setting). No cold-chain or EV lever is declared, and no other mini-grid lever either: Kisiwa and
     Mto have no lever today, so 2 of 3 mini-grid Sites are in the same position as cold and EV.
  2. **The option generator has one kind.** A lever's options can only be a settings grid (`SETTING_GRID`), valued from a
     replay of the mini-grid's dispatch (the study file and its service checks). The design's decisions are mostly
     named alternatives (repair, replace, contract, stopgap-and-claim, schedule), which the grid cannot express. The
     database check (`decision_option.generator IN ('NO_ACTION','SETTING_GRID')`) and the evaluator's branch
     (D-P6.38) hold that limit.
- **Yes, the union (D-P6.43) is a code workaround for this model gap.** It fills the cold and EV rows with Findings
  instead of decisions. It should have been called a workaround. The ruling's own "reverse" trigger ("once every Site
  type has a lever (6g, 9c)") is also wrong: in the delivery plan 6g is Mto only and 9c adds remedy paths only, so no
  slice ever declared the Mwea, Kirinyaga, Embakasi or Ruiru levers. The union would have stayed indefinitely.

## 2. What exists today, and what it already gives

The decision mechanism is general. Only its catalogue and one generator are particular.

```
Finding ──pinned to──▶ factor ──lists──▶ lever ──generates──▶ options (doing nothing first)
 (pins.py)            (registry row)    (levers.py)            │
                                                               ▼
                         choice ◀── recommendation ◀── each option valued against doing nothing
                       (6a, by name)    (6c rules)       (structure difference, 6c core: general)
```

| Piece | Built | General? |
|---|---|---|
| Registries for all three Site types (factors, homes, sources, option-only leaves) | 3B6, 3B3 | Yes. Cold and EV already declare option-only leaves for exactly these decisions: `contract_crate_days`, `contract_rate`, `model_factor`, `handling` (cold); `covered_bus_nights`, `extra_missed_departures` (EV) |
| Pins: Finding mechanism to factor | 3B2, 3B6 | Yes. Five pins; three are cold or EV (`COLD_START_FAILURE`, `COLD_EXCURSION`, `EV_INTERRUPTION`) |
| Decision, option, one-off, run and choice records | 6a | Yes, except `generator` limited to two values |
| `prepare`: lever must match the Site type; a Finding must sit on a factor that lists the lever | 6a | Yes |
| Valuation core (`evaluate_options`, the structure difference, recommendation rules) | 6c | Yes, tested on cold and EV |
| Option effects from a dispatch replay study (`option_inputs`, `SETTING_GRID_CHANGES`, admission, dawn) | 6c | **Mini-grid only** |
| Lever catalogue `LEVERS` | 6a | **One row** |

The design pack already holds the general answer. The scenario manifest
(`Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml`, decision table near line 1613) and the
vNEXT mock (`interactive-mockup-vNEXT/loop-decisions.js`, `DEC`) give **every Finding a decision anchored on the factor
its options change**, on all nine Sites, each with doing nothing as an option. 6f's own register already labels the gap
(MD-6F-7, "cold-chain and EV decisions not valued").

## 3. The fix at the source

Three changes, all inside the existing constructs. No new screen, no new route, no vertical branch.

### 3.1 A second option generator: named options (`STATED_OPTIONS`)

- A `Lever` gains `options: tuple[LeverOption, ...]` (used when `generator == "STATED_OPTIONS"`; empty for
  `SETTING_GRID`). `LeverOption(key, kind, changes)`: `key` matches 6a's option-key pattern; `kind` is one of the
  manifest's option kinds (`REPAIR`, `CAPEX`, `SUPPLIER_REMEDY`, `SCHEDULE`, `DEMAND_CONTRACT`, `CAPACITY_USE`,
  `DEMAND_CONNECTION`, `INVESTIGATION`); `changes` is the subset of `Lever.changes` this option moves.
- A `Lever` gains `change_sources: Mapping[str, ChangeSource]`, one per changed leaf: where the option's change will
  come from. `ChangeSource(kind, words)` with `kind` in `STUDY` (a replay of the Site's own month, as D-P6.2),
  `RECORD` (a stated document: a contract, a quote, a rota) and `words` the record's name for the "Not available yet"
  line.
- `prepare` (6a): for `STATED_OPTIONS`, `current` must be `{}`; the options are doing nothing, then the catalogue's
  options in order, each with `settings {}`.
- Migration 0073 widens `decision_option.generator` to `('NO_ACTION','SETTING_GRID','STATED_OPTIONS')`.
- `check_levers` gains the branches for the new fields (keys unique and well formed, each option's changes within
  `Lever.changes`, a source for every changed leaf, `SETTING_GRID` has no options and `STATED_OPTIONS` no axes).

### 3.2 The evaluator values named options honestly (6c branch, D-P6.38's "6g or 6b adds its branch")

- `STATED_OPTIONS` needs no study. Each option's changed leaf is valued from its source when that source is held, and
  is otherwise missing: `MissingInput("OPTION_RECORD", <source kind>, <leaf>)`.
- In 6h no source is read yet, so every named option is "Not available yet", naming its record, and the run is
  `RANKING_INCOMPLETE` (D-P6.17). Doing nothing stays the comparison. No figure is invented: one figure per quantity,
  computed by the model once its record exists.
- Named options carry no admission (as fixture C1). Hard and costed bounds (must-do, cover kept) are 6b's.
- D-P6.46's closed map gains `OPTION_RECORD` → "Not available yet: needs {words}" (for example "needs the draft
  storage contract's crates and rate", "needs a charging-schedule replay of Embakasi's own October").

### 3.3 The catalogue as data, by lever class (general over particular)

Levers are classes that any Site of the type can use, not Site-named rows. A Site gets a decision when the analyst (or
DD's walk) prepares one, or when a placed Finding sits on a factor that lists the lever.

| Structure | Lever | Purpose factor (home) | Listed also on (pin) | Changes | Options (kinds) | Change sources | Manifest decisions it serves |
|---|---|---|---|---|---|---|---|
| COLD_CHAIN | `backup_cover` | `nights_without_backup_cover` (Protect P1) | `uncovered_nights` (COLD_START_FAILURE), `excursion_crates` (COLD_EXCURSION) | `uncovered_nights`, `backup_unproven_days` | wait for supplier, stopgap and claim, self repair | RECORD: the supplier's restore date; the stopgap's rota | thika-backup |
| COLD_CHAIN | `chamber_efficiency` | `excess_kwh` (Optimize O1) | none | `excess_kwh`, `model_factor` | repair, replace | RECORD: the repair quote and its expected recovery; the replacement's rated efficiency | kirinyaga-energy |
| COLD_CHAIN | `storage_contract` | `contract_crate_days` (Grow G3) | none | `contract_crate_days`, `contract_rate`, `model_factor` | aggregator contract, compressor replacement | RECORD: the draft storage contract; the compressor quote | mwea-occupancy |
| EV_DEPOT_CAPTIVE | `charging_schedule` | `peak_kwh` (Optimize O1) | none | `peak_kwh`, `kwh_2200_2400`, `kwh_0000_0500`, `max_kw`, `extra_missed_departures` | deadline-aware, cheapest window | STUDY: a charging-schedule replay of the Site's own month | embakasi-schedule |
| EV_DEPOT_CAPTIVE | `charger_restore` | `departures_missed` (Protect P1) | `chargers_in_service` (EV_INTERRUPTION) | `covered_bus_nights`, `extra_missed_departures` | wait for supplier, stopgap and claim, local repair, reschedule | RECORD: the supplier's restore date; the cover cost a bus-night | kasarani-charger, ruiru-connector |
| EV_DEPOT_CAPTIVE | `fleet_capacity_use` | `buses` (Grow G2) | none | `buses` | absorb part of the offer, absorb all, add chargers | RECORD: the route offer; the charger quote | ruiru-expansion |
| MINI_GRID | `generator_redundancy` | `obligation_hours_without_redundancy` (Protect P1) | none | `reduced_days` | repair, replace, add storage | RECORD: the repair quote and restore date; the replacement quote | kisiwa-genset |
| MINI_GRID | `productive_demand` | `productive_kwh` (Grow G3) | none | `productive_kwh` | new connection | RECORD: the signed letter of intent; the connection quote | mto-demand (6g values it) |
| MINI_GRID | `fuel_reconciliation` | `unexplained_l` (Optimize O1) | `unexplained_l` (UNEXPLAINED_FUEL) | `unexplained_l` | investigate | RECORD: the investigation's finding | Kobo's unexplained fuel |

`generator_stop_reserve` stays as it is (`SETTING_GRID`, the dispatch replay).

**The class rule (W6), enforced at start-up.** Every pinned Finding mechanism's factor lists at least one lever, or the
mechanism is named in a `PENDING_LEVERS` map with the slice that closes it (the pattern of `PENDING_PINS`). With the
table above all five pins list a lever, so the map starts empty. Decisions anchored on a right (Kobo battery warranty,
Mto inverter notice) cannot be catalogued yet: the structure has no rights row (`cover_not_claimable` is not a row,
D-3B1.5). They wait for the rights register (9a0) and remedy paths (9c), and their Findings say so (§4).

### 3.4 What is still missing after the fix (named, not hidden)

| Missing | Effect on screen | Closed by |
|---|---|---|
| Each named option's record (contract, quote, restore date, rota cost) | the option reads "Not available yet: needs {record}" | per lever model: 6g (quotes, Mto), 9c (remedy records), a stated option record (queue Q3) |
| A charging-schedule replay of an EV Site's own month | Embakasi's options read "needs a charging-schedule replay of Embakasi's own October" | an EV replay study (queue Q4) |
| Kobo's own-month dispatch replay | Kobo's litres and value read "Not available yet" (unchanged, D-P6.2) | 0K4f |
| A rights row | Kobo battery and Mto inverter decisions not prepared; their Findings say "Its decision: not available yet: needs the warranty's terms" | 9a0, 9c |
| Bounds (must-do, cover kept) | "Limits and cover" shows none for named options (MD-6F-6 widens) | 6b |

So on the demo every Site shows a decision in the same shape: the question, doing nothing first, the named options,
who decides, the state, and for each option what record would value it. Values appear Site by Site as their records
land. That is the same honesty Kobo already has (its values also wait for 0K4f).

## 4. Effect on 6f: the swap D-P6.8 asked for

With records on every Site type, the Decisions list becomes the decision records, as D-P6.8 said and as the mock shows.
- **6f1 unit 2** loses the union: no merge order, no `DecisionCoverage` port, no partial-read rule for two sources. E0's
  "Waiting for a choice" counts records in `NOT_VALUED` or `WAITING`. The Findings list's "Its decision" joins on
  `finding_id`; a Finding with no decision reads "Its decision: not available yet: needs {lever class or rights
  record}".
- **6f1 words** gain the named-option forms ("option" where the statements say "setting tried"; the limits line reads
  "No service checks for these options" when no option has an admission).
- **MD-6F-7 is withdrawn** (its decisions exist; their values wait for named records, already "Not available yet").
- **6f2** unchanged in structure; choosing works the same for named options.

## 5. Cost

| Item | Union (D-P6.43, current) | Source fix |
|---|---|---|
| New slice 6h: lever model and migration (1.0), evaluator branch (0.75), catalogue data, registry `levers`, pins rule and fixtures for the three Site types (1.0) | 0 | **2.75 u** |
| 6f1 | 4.0 u (unit 2 builds the union, 1.0) | **3.75 u** (unit 2 0.5; words +0.25) |
| Later swap back to records once levers exist | about 0.5 u rework of unit 2 and its consumers | 0 |
| DD6.2 walk `prepare` | 8 of 9 decisions listed "pending" | +0.25 u: nine Sites get records; only the two rights decisions stay pending |
| 6g (Mto demand and repair) | 4 u, would have to build the named-option generator for itself | about 3.25 u: adds quotes and Mto's option records only |
| 9c (remedy paths) | 3.5 u | about 3.0 u: remedy options already exist as decisions |
| **Programme net** | union code 1.0 u built then thrown away, plus 0.5 u rework | **+1.5 u net**, none of it thrown away |

Sequencing: 6c is merged, so 6h can start now in the decisions lane. 6f1 waits for IA-P1 and IA-P2 anyway; 6f1's
unit 1 (server read, page view) does not need 6h, and unit 2 gains the gate "6h merged". The demo critical path is not
lengthened if 6h starts this lane's next slot.

## 6. Recommendation

**Fix it at the source: build 6h, withdraw D-P6.43, and keep D-P6.8's swap.** It is general (one mechanism, every Site
type), it removes a workaround rather than adding one, it matches the mock and the design pack, and over the programme
it costs about the same as the union while leaving nothing to throw away. For the demo audience (operator executives in
all three verticals), every Site shows a real decision the executive owns, with doing nothing as the comparison and the
missing record named, instead of cold and EV showing a different kind of row.

## 7. Draft rulings (applied only after owner agreement)

### D-P6.51 The lever model gains named options; the catalogue covers every pinned Finding (new slice 6h, 2.75 u)

- **Ruling.** §3.1 to §3.3 above. 6h is three units: 6h1 lever model, `check_levers` branches and migration 0073 (1.0);
  6h2 the `STATED_OPTIONS` evaluator branch and `OPTION_RECORD` (0.75); 6h3 the catalogue of §3.3, registry `levers`
  entries, the `PENDING_LEVERS` start-up rule, and one prepared-and-evaluated fixture per Site type (1.0). Registry
  versions unchanged (levers change no value, as 6a). 6h is specced as `specs/6h-lever-catalogue/spec.md` after
  owner agreement.
- **Why.** The owner's challenge: the Sites are not different; one lever and one generator were modelled. A model
  fault is fixed in the model ("fundamental mechanics first", "fix model faults in the model").
- **Reverse:** keep the union (D-P6.43) as a labelled WORKAROUND until 6g and 9c, with the cold and EV non-remedy
  levers still unowned.

### D-P6.52 D-P6.43 is withdrawn; D-P6.8's swap stands (amends D-P6.44)

- **Ruling.** The Decisions list is the decision records of the range. E0's waiting count is records in `NOT_VALUED` or
  `WAITING` (D-P6.44's coverage port is dropped). A placed Finding with no decision appears on the Findings list, its
  "Its decision" cell naming what is missing. 6f1 unit 2 is gated on 6h merged and resized to 0.5 u; 6f1 is 3.75 u.
  MD-6F-7 is withdrawn.
- **Why.** The union was a code bridge over a model gap (§1). Once every Site type has levers, the swap is the model's
  own reading and the mock's.

### D-P6.53 Every pinned factor lists a lever, or names the slice that will (class rule)

- **Ruling.** `check_levers` refuses `STRUCTURE_LEVER <structure>/<mechanism>` when a `PINS` mechanism's factor lists
  no lever and the mechanism is not in `PENDING_LEVERS`. Starts empty.
- **Why.** The class behind this gap is "a Finding whose factor has no decision path". A start-up rule stops it
  recurring silently for the next mechanism.

## 8. Decision queue (W3; defaults applied once the owner agrees direction)

| # | Question | Default | Alternative |
|---|---|---|---|
| Q1 | Source fix (6h) or keep the union | Source fix, D-P6.51 to D-P6.53 | Union kept, labelled WORKAROUND, removed by 6h when scheduled |
| Q2 | Catalogue scope in 6h | The nine levers of §3.3 (every Site in the demo has at least one, every pin has one) | Cold and EV only (six levers, about 0.25 u less); Kisiwa and Kobo's unexplained fuel stay without decisions |
| Q3 | Value named options in the demo | Not in 6h: values arrive with each lever's records (6g, 9c, later) and read "Not available yet" until then | 6h4 (+1.0 u): a stated option record (a document with its basis, as the one-off) fills the option-only leaves; lights Mwea's contract and the two stopgaps from real records |
| Q4 | Embakasi's schedule options | Change source STUDY: a charging-schedule replay of the Site's own month, queued as its own slice | A stated record of the schedule's kWh by window (weaker: a typed figure) |
| Q5 | Who prepares a decision | The analyst, or DD's walk, as 6a today | A placed Finding on a lever's factor prepares its decision automatically (after 7a) |
