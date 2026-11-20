# DS1 rulings

Architect (Claude), 2026-11-20. Each ruling has its reason. Index lines are in `.ai/decisions/index-rulings-6.md`. The owner
took D-DS1.6 and every queue default (Q1 to Q5, `spec.md` §11) on 20 Nov: "merge wave 2c, and defaults for DS1"
(`owner/owner-merge-wave2c-ds1-defaults-2026-11-20.md`).

## D-DS1.1 `2a` is not built; DS1 is cut so it does not need it

- **What `2a` is.** "Canonical format version 1 per source type, and the leaf factor IDs, as code the store and the
  registry share" (`delivery-plan.md:65` in the pack; Lane 2, 1.5 units, no dependency, phase P2).
- **Is it built?** No. There is no canonical-format or leaf-factor module in `backend/`, `contracts/` or `simulator/`,
  no branch, and no `.ai/state` entry.
- **What DS1 needs from it.** Only the record- and envelope-level writers need `2a`'s format. The history is month
  grain, keyed by the manifest's own leaf keys, which are what the evaluator reads.
- **Ruling.**
  - DS1 is built now with no dependency (§3: DS1a, DS1p, DS1m).
  - **DS1b** (1 unit, after `2a`) adds the canonical record and envelope writers. It unblocks `DS3` and `3A3`.
  - `world/leaves.py` is the single mapping point `2a` replaces.
  - Recommendation for `2a`'s spec: put the format in `assetops_contracts`, so that the store (backend) and the
    generator (simulator) share it without crossing the import seam.
- **Estimate.** DS1 is **3 units** (1.5 + 1 + 0.5), against the strategy's 2.5. The strategy counted the history as "one
  more scope", but the evaluator, independent-model and mock-up work it needs is real. DS1b adds 1 unit. Strategy §9 row
  amendment, for the coordinator on `task/data-build-strategy`: "`DS1` | generator core at month grain and the July to
  September history | 3 | none | `DS1b`, `DS2`, history on screen" and "`DS1b` | canonical record and envelope writers
  | 1 | `2a`, `DS1` | `3A3`'s values, `DS3`".
- **Day-7 re-cut.** `plan_model.py` must add `DS1`, `DS1b`, `3B7a` and `3B7b`. None of them is in it or in the two-week
  plan today (placeholder audit item 3).

## D-DS1.2 The generator lives in `simulator/assetops_simulator/world/`

- **Pushback on "product code".** The generator writes inputs that stand in for sources. RULES §1 keeps the simulator out
  of the product, and the dependency-direction guard (`tools/checks/dependency-direction.ps1`) already bans imports in
  both directions between `assetops_backend` and the simulator.
- **Effect.** Placing the generator under the simulator gives it tests and guards, and makes the product unable to
  import it. The only YAML reader is `tools/world_history.py`.

## D-DS1.3 Three branches; nothing generated is merged from two sides (amended rev 2: see D-DS1.13)

- **Rev 1.1:** wave 2c merged to `main` (`76022d3c8`), bringing the pack and the mock-up with it. All three tasks are
  now based on `main`: DS1a, then DS1p, then DS1m after DS1p merges (after the Decision-page branch, if it lands first).
  The pack files DS1p edits are blob-identical on `main` and at `d9329b582`, so P8 and P10 keep that reference.
- **Why there is no conflict.** No other lane edits DS1p's pack files. The generated mock-up files are rebuilt by
  whichever branch merges last, never hand-merged.
- The tag `pack-freeze-2026-11-19` is never touched. U9 is the owner's authority for this one pack change.

## D-DS1.4 History inputs are rules, not values; leaves are generated; totals are evaluated

- The manifest's `history:` block holds seasons, day classes, family weights and per-leaf rules. It holds no leaf, node
  or total figure.
- **A side October states only as a total stays stated** (Ruiru's plan). That stated total is the operator's plan
  record, built by the rule `sum` from its stated lines. It is not an evaluated figure. Every other total, and every
  series point, comes from the evaluator.

## D-DS1.5 `history.json` carries `meta` plus `tenants`, money in integer cents

- **Pushback on A2's top-level `{tenant: …}`.** The labels, generator version, digests and money unit must travel with
  the data, and they would collide with tenant keys at the top level.
- **Money in integer cents** keeps the file free of floats and decimal text. The evaluator converts on load to
  `Decimal`.

## D-DS1.6 History months carry no bridge rows (decided by the owner, 20 Nov)

- **Pushback on A2's "plus `coverage` and `bridge`".** A bridge row attributes a variance to a driver. October's rows are
  declared inputs that `check_manifest` verifies. For history they would have to be typed by hand, which A2 forbids, or
  computed by an attribution engine, which is `5c`.
- No screen reads a history bridge, and the gap trend needs only the variance, which is evaluated.

## D-DS1.7 What history may and may not show

See `spec.md` §6.3. In short:
- **May show:** seasonal and seeded variation, the declared story trends, and chronic patterns at October's rate.
- **May not show:** an October-dated incident, a missing record, a Protect deviation, a fuel residual above tolerance, a
  bridge, or any Finding, option, decision, plan item, Action or right.
- Each "may not" is a check (P2, P4, P5, P7, P10) or is impossible by construction (the view drops observations,
  incidents and entitlements; the evaluator runs only M2 on history).

## D-DS1.8 The series is July to October, keyed by manifest Site name

- Four points, so the tile's "against <previous month>" reads "against Sep". The October point is copied from the
  evaluated October output, never re-evaluated, so it equals the October figure on every screen.
- **Site keys are the manifest names**, as in `DERIVED.sites`. The mock-up maps through `siteM(sk).site`. This answers
  the audit's request to map Site keys: the mapping stays where the screens already do it.

## D-DS1.9 Harvest Cold's after-recalculation figures go to `3B7b`

- **Why not DS1.** They revise October in response to a new record, while DS1's acceptance is "October byte-identical".
  They depend on the snapshot pair (before and after) that `3B7a` and `3B7b` define. And their input exists nowhere:
  there is no Thika invoice amount at manifest lines 472, 1570 or 1577.
- **Ruling for `3B7b`:**
  - add the invoice as the first manifest `rolling:` entry (the section `DS6` later extends), in story time:
    `{at: "2026-11-06T09:40:00+03:00", kind: EXPENSE, site: "Room B · Thika", period: "2026-10", leaf: maint, amount: <Q5>}`;
  - the evaluator emits an `after_recalculation` block for that portfolio, with `as_of` set to the request time in story
    time;
  - the request time is 2026-11-06T10:00:00+03:00, the time the mock-up already ships (`UX_RECALC_TIME`);
  - the mock-up's *Recalculate now* reads that block instead of saying the figures are unchanged;
  - `ux_interaction_check.cjs:218` changes with it. That is `3B7b`'s gate.
- Amount 96.00 and request time 10:00 are decided (owner, 20 Nov, Q5).

## D-DS1.10 Evidence words; coverage `RECORDED` is not one (amended rev 2: every history leaf is *Simulated*, R8)

- **Rev 2.** Every history leaf and series is *Simulated* (`demo-simulated`). A month total generated by rule is not a
  source record, so *Emulated* would claim too much. *Emulated* arrives with DS1b's source-shaped records.
  (Rev 1 labelled money leaves *Emulated*; that is withdrawn.)
- *Recorded* never appears as an evidence word.
- `RECORDED` in `coverage` keeps October's meaning, "the record exists". It is not an evidence class.

## D-DS1.11 Where the product reads the history

- The product's series read is `3B7a`'s: `structure_snapshot` at period kind month, read as a series.
- Loading the generated history into the input stores is `DS3`, after `DS1b`.
- DS1 does not depend on the audit's gap 1 (`missing: {record_kind, source_family, blocks[]}`), because no history
  record is missing. `3B7a` does need it.

## D-DS1.12 History nodes carry the `missing` record; no unknown reads as zero (rev 2; R7, P14, the empty-state ruling in pack commit `46b62c92b`)

- **Ruling.** In history, a leaf whose own record October takes from observations is not generated by DS1. It is
  *missing*, never 0:
  - its cause is `NOT_IN_HISTORY`, declared in `history.missing_cause`;
  - the nodes resting on it are left out of `periods.nodes` and listed as `not_observed`;
  - each side carries `missing` entries in the rev 16.13 shape (`record_kind`, `source_family`, `cause`, `carried_as`,
    `blocks[]`).
- **Why.** Strategy §8 and RULES §1 say unknown stays unknown. The design Architect ruled that a history month's node
  carries `missing` the way the snapshot node does. Check H4 can fail, which the old P4 could not.
- **What this rejects.** Pre-flight P14's "accept the zero" is rejected, because it would publish 0 of 0 asset-days as
  if observed. R7's option (b), generating observations, is also rejected: it claims what DS1 does not generate.
- **Limit.** No outcome rests on these leaves in today's structures. If one ever would, the evaluator refuses
  (`HISTORY_OUTCOME_UNOBSERVED`).
- **New cause value.** `NOT_IN_HISTORY` extends the rev 16.13 vocabulary without editing `empty_states`. The default is
  applied, and the design Architect is to confirm it.

## D-DS1.13 DS1p is based on the pack branch, after `46b62c92b`, with `main` merged in (rev 2)

- **Why the pack branch.** `46b62c92b` (rev 16.13) edits the manifest, the evaluator and `check_manifest.py`, and DS1p
  needs its `empty_states` (D-DS1.12). Basing DS1p on `main` would create a three-way conflict in those three files, and
  would lose `empty_states`.
- **Why the hunks don't collide.** DS1p's are disjoint: a manifest append after `checks:`, `observe_side` in the M2
  loop, and new functions.
- **Why merge `main` first.** It brings `main`'s check fixes (`7e53f2ede`, `d58c6d2e1`), so a fresh worktree has the
  untracked brief path and starts at 0 failed. It touches hunks other than `46b62c92b`'s.
- **Merge target.** DS1p merges into `task/pack-recreate-integrate`. DS1m follows the pack merge to `main`, which waits
  on the owner's pack review. **Consequence:** the trend appears on the `main` mock-up only after that review. DS1a and
  DS1p do not wait.

## D-DS1.14 Units and estimate (rev 2)

- Month-grain leaves are in integer units, and money in cents. Milli-units start with DS2's day split (R9).
- **DS1 is 4 units:** DS1a 1.5, DS1p 2 (R7 and D-DS1.12 add the `missing` work), DS1m 0.5. DS1b adds 1. That is up from
  the strategy's 2.5 and rev 1's 3.
- **Strategy §9 amendment text, for the coordinator:**
  - "`DS1` | generator core at month grain and the July to September history; month leaves generated by declared rule
    and labelled Simulated; integer units at month grain, milli-units from DS2 | 4 | none | `DS1b`, `DS2`, history on
    screen";
  - "`DS1b` | canonical record and envelope writers | 1 | `2a`, `DS1` | `3A3`, `DS3`".

## Handshake answers (round 1)

Answered once, 2026-11-20, and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. "Adopted" means the
proposed answer is the ruling.

**Implementer pre-flight (P1-P16)**

- **P1 (High): adopted.** Check H2 counts the first-present alternative. Check H5 uses the evaluated `diesel_l` node.
  There is no new rule.
- **P2 (High): adopted.** A float becomes `repr(x)` as a string. An int stays an int. Any other type is refused with
  `VIEW_TYPE <path>`.
- **P3 (High): adopted.** Absent keys are omitted, never `null`. T3(c) checks allowlist ∩ the source's keys.
- **P4 (High): adopted.** Rules are keyed by the tenant's own `vertical` (`EV_DEPOT`). The generator holds no mapping.
- **P5 (High): adopted, with R10.** There are two shapes: `R` for volumes and `S` (length-free) for intensities. `level`
  is new. Numeric `cold_kwh` takes no shape factor; `anchor` takes `S`. `base_kwh` stays monthly and unscaled.
- **P6: adopted.** `observe_side` returns `(result, ctx, factors)` and takes `incident` and `entitlement` (R2).
- **P7: adopted** (`generate_scope`, `jitter=False`).
- **P8: adopted** (a `.json` view is accepted).
- **P9: adopted.** The fixture comes from a scratch copy of the manifest at DS1p's base, plus §5.
- **P10: adopted** (`PY` with `PYTHONPATH`, and `sys.path` set in the CLI).
- **P11: adopted, amended by D-DS1.13.** DS1m is on `main`, which has the slot. The register is in DS1m's file list. The
  capture commands are in spec §9.4.
- **P12: adopted** (the actual side).
- **P13: adopted.** (b) is `HISTORY_RULE_REF` (R13). (c) is `HISTORY_RULE_UNKNOWN`. (d) is `HISTORY_MONEY_LEAVES`. (e)
  is the signature in spec §4.4.
- **P14: rejected** (D-DS1.12).
- **P15: adopted.**
- **P16: adopted, raised further.** DS1p is 2 units and DS1 is 4 (D-DS1.14).

**Reviewer (R1-R25)**

- **R1 (High): resolved.** `main` is green at `d58c6d2e1` (4487/0). DS1p merges `main` before its first commit. Check H9
  requires 0 failed against a baseline taken in place and recorded in the packet.
- **R2: adopted** (`incident` and `entitlement` parameters; `HISTORY_NOT_EVALUATED`).
- **R3: adopted** (`HISTORY_ANCHOR_ZERO`).
- **R4: adopted** (T3a).
- **R5: adopted** (spec §6.1, "Which rules carry season and jitter").
- **R6: adopted.**
- **R7 (High): adopted as option (a), extended.** The design Architect's `missing` record is added (D-DS1.12).
  - **The disagreement with P14 is ruled for R7.**
- **R8 (High): adopted.** Every history leaf is *Simulated*; *Emulated* comes with DS1b (D-DS1.10 amended).
- **R9: adopted** (D-DS1.14 text).
- **R10: adopted.** Numeric `e` is exact, so the owner-decided +5/+10/+17% are what is shown. The `generator` season is
  retuned to cool_dry 0.98, warm_dry 0.93, short_rains 1.00, so October's rainy month needs the most fuel, matching its
  bridge. These weights were Architect parameters, not owner-decided figures.
- **R11: adopted** (no prices or tariff in `scope_input`; T4 adds the price case).
- **R12: adopted** (`compute_history`; `documents()` skips `history`).
- **R13: adopted.**
- **R14: adopted** (count line; H8 and H10 lifetime rule; H10 mechanism).
- **R15: adopted** as check H11 (an independent view digest) plus `HISTORY_STALE` in `load_history`.
- **R16: adopted** (check H6 against the independent model).
- **R17: adopted** (`git diff --exit-code` in spec §9.1).
- **R18: adopted, with the coordinator's ruling.** Every browser-driven gate goes through `heavy-slot.sh`; the commands
  are named in spec §9.4. The inventory regex is a T1 follow-up.
- **R19: adopted** (routes, states, pass criteria in spec §9.4).
- **R20: adopted.** One assertion in `ux_interaction_check.cjs` is gate tooling, not screen code.
- **R21: adopted** (keep; packet note; no register row).
- **R22: adopted** (set semantics).
- **R23: adopted.** Exact greps. `calendar.py` is renamed `months.py`.
- **R24: adopted** (`.gitattributes` in DS1a and DS1p).
- **R25: adopted** (`d₀`, the literal month table, the W2 order).

**Open after round 1:** none that blocks code. One question is for the design Architect, with the default applied: the
cause value `NOT_IN_HISTORY` (D-DS1.12).

## Mid-build answers (DS1a, 2026-11-20)

**MB1: the built default is adopted.**
- For a month outside `history.months`, a three-value list is read only when its three entries are equal. Otherwise it
  is refused with `HISTORY_MONTHS <scope_key> <leaf>`.
- **Reason.** Only T9's October run reaches this path. Any rule naming one entry for the anchor month would invent a
  value the manifest does not declare, whereas equal entries make every choice give the same value.
- T9 as built (`trend 1 1 1`, `level 1 1 1`, the other lists `anchor`) is what spec §10 meant.

**MB2: every built default is adopted as the specified text.**
- **Validation refusals, found before any scope**, put `history` in the scope position and the field in the leaf
  position:
  - `HISTORY_MONTHS history <month|anchor_period|seasons|day_classes>`;
  - `HISTORY_MONEY_LEAVES history money_leaves`;
  - `HISTORY_FAMILY_UNKNOWN history <family>`.
- **An override for an unknown Site:** `HISTORY_RULE_UNKNOWN <tenant/site> sites`.
- **A missing vertical table:** `HISTORY_RULE_UNKNOWN <scope_key> <vertical>`.
- **A missing season or day-class weight:** `HISTORY_FAMILY_UNKNOWN`.
- **A date with no day class, or a month with no season:** `HISTORY_MONTHS`.
- **A `share` fraction outside [0, 1]:** `HISTORY_BOUND`. The rule's bound is checked before `allocate`, so the code
  names the manifest defect rather than the helper's input.
- **A rule reading an absent or non-numeric value** (`energy_model`, `physical`, or an October leaf named by an
  `anchor`): `HISTORY_RULE_REF`.

**Effect.**
- No generated byte, test outcome or done criterion changes, and DS1a needs no change.
- Spec §6.1 now cites this section. T8 covers the listed codes. Planting these extra cases is welcome but not required.

## Review round 1 answers (DS1a, 2026-11-20; review `.agent/review-DS1a-r1.md`, ACCEPT with Lows)

**L3: adopted. `history.months` must hold exactly three months.**
- The three-value lists are read by position, so a set of two months would silently shift August onto July's value.
- Any other count is refused with `HISTORY_MONTHS history months`.
- This sits with MB1: lists are positional over the three sorted months, and are read for a month outside the set only
  when their entries are equal.

**L4: the codes.**
- **A number that is not a finite decimal** (NaN, Infinity, or text that is not a decimal), in a weight, a rule token or
  a leaf: `HISTORY_NUMBER <scope_key|history> <field>`. This is a new code.
  - The view also refuses a non-finite float with `VIEW_TYPE <path>`.
- **An absent input** (room capacity, `energy_model`, `physical`, or an October leaf an `anchor` names):
  `HISTORY_RULE_REF`, in every case. `HISTORY_ANCHOR_ZERO` is only for a value that is present and zero. This makes the
  missing-capacity case consistent with the missing-energy-model case.
- **An absent required `history` field** (`version`, `months`, `anchor_period`, `shape_source`, `money_leaves`, `label`,
  `missing_cause`, `seasons`, `day_classes`, `families`, `rules`): `HISTORY_FIELD history <field>`. This is a new code.
- **`generate_scope` on its own** runs the same validation as `generate_history`, except month-set membership. A family
  without `jitter` is then `HISTORY_FAMILY_UNKNOWN history <family>`, as MB2 already says.
- There must be no bare `KeyError`, `ValueError` or `OverflowError` from user input. T8 asserts the full text.

**Item 3 (DS1p risk): checked against `46b62c92b`. No change to §5, and the golden file is unchanged.**
- **What the evaluator reads from a history side.** It reads only the factor map's `record.*` names, plus
  `record.get("contribution", record.get("total"))` for a side that is not decomposed.
  - Mini-grid: none of `collected` or `metered_kwh` is read. Both are structure nodes.
  - EV: none of `departures_required` or `departures_met` is read. `departures_required` and `departures_met` are nodes.
    `nights` falls back to `period_days`. `failed_chargers` and `short_nights_from` take the same defaults as in
    October.
- **The only record read of `departures_required`** is in `main()`'s October portfolio composition
  (`evaluate_structure.py`, "portfolio composition and O2"). It reads the manifest's `period` and never a history side.
  Ruiru's plan carries it anyway, as a stated record.
- **Consequence for DS1p.** H2 and `observe_side` will not refuse on these keys.
  - H2's set is "first-present `record.*` alternatives". It therefore excludes `collected`, `metered_kwh`, `departures_*`
    and `peak_share` by definition. That is intended.

**No ruling needed:** L1, L2, L5, and pinning scope and leaf in T8 are in the fix round.

## Fix-round interpretations (DS1a, 2026-11-20; `packet-DS1a.md` "Review round 1 fixes")

1. **Confirmed.** A value that is **present** but not a finite decimal (an October leaf, a `physical` or an `energy_model`
   value) gives `HISTORY_NUMBER`. An **absent** one gives `HISTORY_RULE_REF`. The L4 ruling supersedes MB2's
   "non-numeric" wording.
2. **Confirmed.** A token in a numeric position that is neither a decimal nor (where the rule allows it) `anchor` gives
   `HISTORY_NUMBER`. That includes `anchor` in a rule that does not take it. An unknown rule *word* (the first token)
   stays `HISTORY_RULE_UNKNOWN`.
3. **Amended.** A missing `history` block gives `HISTORY_FIELD history history`. This is the L4 rule for an absent
   required field, applied to the block itself.
4. **Ruled: a magnitude bound.**
   - Every number the engine reads, from the view or from a rule token, is parsed first as `Decimal(text)`. That parse is
     cheap, because it holds the exponent symbolically.
   - The number is refused with `HISTORY_NUMBER <scope_key|history> <field>` unless it is finite, its `adjusted()`
     exponent is within [-12, 12], and its text is at most 32 characters.
   - Only then is it converted to `Fraction`.
   - The largest legitimate value in the world is about 2.3 × 10⁶ cents, far inside the bound.
   - T8 plants `1e999999999` and `1e-999999999`; each must refuse within one second.

**DS1a follow-up commit needed:** items 3 and 4, with their T8 plants. It is small: about two code lines and two tests.
No generated byte changes, and the golden file must stay `9cb1b6bf…84fd4c9`. Items 1 and 2 need no change.

## DS1p mid-build answers (MB3-MB5, 2026-11-20) and the cause vocabulary

**MB3: the built exemption is adopted, and H2's wording is amended.**
- New wording: history keys == the first-present `record.*` alternative of each factor-map leaf, **plus every key that a
  declared `share` or `rest` rule reads as its base** for a leaf the side generates, among the keys of October's
  `period` side.
- **Reason.** `kwh` is a generated input that the rules read, not an evaluator read. Every other key stays compared
  exactly.

**MB4: confirmed.**
- The observation-fed leaves leave `nodes` too.
- Each is named by its own `NOT_IN_HISTORY` entry's `leaf`. They are not listed in `not_observed`, which lists nodes.
- H4 asserts both. A leaf at a fallback 0 would be the unknown-as-zero R7 forbids.

**MB5: (a) on both sides is confirmed. Amended: (b) also applies to the plan side, as `missing_records()`'s
target-side logic.**
- **Reason.** Ruiru's history plan is stated only as a bill total, exactly as October's is. October's plan carries the
  target-side entry (`carried_as: RESIDUAL`). Dropping it in history would claim a decomposition the record does not
  have, and the Metro gap trend includes that residual every month.
- **Rule.** Each history plan side gets the entries October's target side would get, computed on the history records
  by the same helper: `RESIDUAL` when not decomposed, `ASSUMPTION` where its split rule applies. Each history actual side
  gets the observed-side entries, as built.

**Cause vocabulary: closed.** The design Architect confirmed `NOT_IN_HISTORY` as a demo-only cause that the product's
read never emits (`integration-source-to-canonical-design.md` §6.2, pack `4371f8b52`).
- A history entry's `cause` must be in the main causes ∪ {`history.missing_cause`}.
- `missing-records.json` (October) stays restricted to the main causes.

**DS1p must change** (one fix round; `history.json` and October's bytes are unchanged; only `derived["history"]` gains
plan-side entries):
1. Extend the shared helper so that it also yields the target-side entries. Apply them to each history plan side in
   `evaluate_history`, and in the independent model's `compute_history`, which computes them its own way.
2. Add to H4, or as H4b: each history plan side's target-side entries equal the independent model's, and Ruiru's plan
   carries `carried_as: RESIDUAL` in each of the three months. Show it failing on a planted removal.
3. Add H12: every history `missing` entry's `cause` is in `CAUSES ∪ {history.missing_cause}`, and every
   `missing-records.json` cause stays in `CAUSES`. Show it failing on a planted `NOT_IN_HISTORY` in
   `missing-records.json`.
4. Update H2's text in `check_manifest.py` to the MB3 wording; the logic is as built.
5. Re-run the evaluator and the checks: 0 failed. H8 (October) and H10 (manifest) still pass, and `history.json` is
   unchanged.

## DS1p review round 1 answers (2026-11-20; `.agent/review-DS1p-r1.md`, ACCEPT with Lows)

**M1: confirmed for both sides.** Every history month carries the `missing` entries October gives for the same side,
computed on the history records by the same helper. The only exclusions are the kinds a history month cannot hold.
- **Plan side.** The target-side entries: `RESIDUAL` where the plan is not decomposed, and `ASSUMPTION` for leaves with
  no target line of their own. Kobo's `technical_loss_kwh`, `candidate_l` and `unexplained_l` carry their label. This is
  MB5.
- **Actual side.** These are carried:
  - the observed-side `NOT_RECEIVED` leaves;
  - the record-field assumptions (`empty_states.assumptions`; Embakasi's tariff applicability, under `energy_cost`);
  - the deferred stages;
  - the `NOT_IN_HISTORY` entries.
- **Excluded, because they are October events:**
  - the coverage-`ESTIMATED` (`carried_as: TARGET`) entries, since every history coverage is `RECORDED`;
  - the rights-condition entries, since history runs no rights.
- **New check H13 (completeness).** For every Site and month, the history side's entries, keyed by (subject,
  `record_kind`, `cause`, `carried_as`), equal October's same-side entries in `missing-records.json`, minus the two
  excluded kinds, plus the `NOT_IN_HISTORY` entries. It is shown failing on a planted dropped assumption.

**L2: one shape.** Every history entry uses the `missing-records.json` entry shape:
`{side, <subject: leaf | leaves | field | stage>, record_kind, source_family, cause, carried_as, blocks, slice, …extras}`.
- `NOT_IN_HISTORY` entries take `side` and `slice` from `empty_states.leaf_sources`, with `carried_as: null`.
- H4 and H12 read this shape.

**L3 (Ruiru's September gap): accepted as realistic.**
- Ruiru's plan is a bill total only. Holding a "fixed demand part" of it would invent a split the record does not have,
  which is the very residual that the `RESIDUAL` entry declares.
- A flat daily budget against a fixed monthly demand charge is exactly what such a plan does in a 30-day month.
- No change to §5, and the golden is unchanged. The demo script names it.

**Kasarani's gap of 0.00 in every month: honest, kept.**
- October's plan equals October's actual. The tariff is flat and the fleet is fixed, so the rules (`per_day` and
  `fleet_kwh`) give an equal plan and actual every month.
- Adding variation would be invented. It carries the same *Simulated* label as everything else. The demo script presents
  Kasarani as the Site on plan.

**L4 (DS1a, a separate tiny commit on `main`).** The magnitude-bound test runs each planted call (`1e999999999`,
`1e-999999999`) in a child process (`subprocess.run([sys.executable, "-c", …], timeout=1)`).
- It passes only if the child exits within 1 s and prints the `HISTORY_NUMBER` refusal.
- A timeout fails the test. The test is shown to fail, not hang, with the bound removed.

**L1:** fix the stale comment.

**The story wording** in spec §1 now reads "new, building or chronic", with the per-operator story the demo script
should follow:
- Lakeside: a chronic gap with a seasonal swing, worst in July.
- Harvest Cold: building at Mwea and Kirinyaga.
- Metro Bus: building at Embakasi, on plan at Kasarani, and a September dip at Ruiru.

## MB6 (DS1p fix round 1, 2026-11-20): the plan-side `ASSUMPTION` leaf list

- **The month's own list is correct.**
  - The `ASSUMPTION` entry names the plan leaves with no target line whose actual value differs from the plan's.
  - Mto's `unmapped_kwh` qualifies in October only because of October's meter swap (MAP-1). In history it is `zero`, as
    is the plan's default, so no assumption is in play.
  - Carrying October's list would label an assumption that the month does not make.
- **H13's key: the built default, tightened.** A `leaves` subject matches by kind (`record_kind`, `cause`,
  `carried_as`), **and the history list must be a subset of October's list**. No leaf may appear that October's target
  side does not name.
  - Every other subject matches whole.
  - H4b keeps the exact per-month comparison of the full list against the independent model. Together the two checks
    give completeness of kind, no stray leaves, and exactness.
  - H13 does not re-derive the list itself: that would duplicate the helper's rule inside the check, which H4b already
    covers independently.
- **DS1p change:** add the subset condition to H13's `leaves` match, and plant a stray leaf (for example, add `om` to one
  history plan list) to show it fails. No figure or file other than `check_manifest.py` changes. Then send DS1p to the
  verification re-review.

## DS1m mid-build answers (MB7, MB8), deferrals and merge order (2026-11-20)

**MB7 (G3 at the compact sizes): G3 is amended. The compact rule stays the UI lane's call.**
- The compact rules (`ux.css` `.ux-kpi-s+.ux-kpi-s{display:none}`, at max-width 600 px and at 1024+ wide by 820 px or
  less tall) are the mock-up's own overview budget (UI/UX guide §2.2a). DS1m must not change them, and a gate must not
  require what the governing mock hides by design.
- **G3, amended:**
  - at 1440×900, each overview `.ux-kpi .ux-trend` is visible and not clipped;
  - at 1280×720 and 390×844, the trend slot is present in the DOM with its series, hidden only by the compact rule, and
    nothing is clipped;
  - page errors are 0 in all 18 shots.
  - The 6/18 already measured, plus the presence check on the other 12, satisfy it.
- **Recommendation to the UI lane** (not blocking; under RULES §6, "strong 390 px behaviour" and plain copy):
  - on a phone, show the change in words ("−$X against Sep") as the tile's one sub-line, and drop the sparkline. A
    64×16 line carries little at 390 px; the words carry the decision-relevant fact.
  - at 1280×720, keep the sparkline if the overview budget allows.
  - That is a UI-lane change with its own G3, not a DS1 condition.

**MB8 (the Lakeside sentence): accepted with DS1m.** The sentence changes because the regenerated fixtures carry the
owner-approved pack wording (the empty-state ruling: never blame an export). It is generated, and it changes no figure.
The packet records it as the one non-trend text change.

**Deferrals confirmed.**
- **The Site tiles keep "Trend not available yet" in DS1m** (D5, register R742). R742 closes when the UI lane's Site
  wiring (`583bdd7c8`, Decision-page branch) and DS1's `history.sites` are both on `main`, that is, at the merge of the
  Decision-page branch after DS1m. That merger regenerates the fixtures, checks with G3 at 1440×900 that the Site tiles
  show "against Sep", and closes R742 in the same commit.
- **The period menu keeps earlier months "not available yet"** (R21). Choosing September as the period needs the
  product's month-series read (`3B7a`). It is not a departure, and there is no register row.

**Merge order: DS1m first, after merging `main` into it.**
1. Merge `main` into `task/DS1-mockup-trends`.
2. Regenerate (`gen_fixtures.py`, `build.mjs`), never hand-merging a generated file.
3. Rerun G1, G1+ and G2, and the amended G3.
4. Diff `rendered-text.json` against `main`'s regenerated output: only the trend slots may differ.
5. A verification reviewer checks those results; then merge to `main`.
6. The Decision-page branch then merges `main` and regenerates. It receives DS1m's `ux_interaction_check.cjs` assertion
   by an ordinary merge, as a source file.

**Why this order.** DS1's gate stays with DS1's review, rather than being absorbed into another lane's review where it
could be lost.

## DS1m round 3 answers (2026-11-20; packet `packet-DS1m.md` "Round 3", head `5a57d7f31`) — D-DS1.15

**Verified, not taken as given.** Both reds come from `main`'s accepted UI branch (`25b3ae88b`, r5 ACCEPT), not from the
DS1 data. Checked at `5a57d7f31`:
- `loop-ux.js` `uxTrendCost` (review Site H1, `786e1f905`) renders a cost operator's tile-1 trend as words only
  (`data-measure="monthly-cost"`, no `svg.ux-spark`), on the Portfolio and the Site tiles. Block 8's `sparks === 2` and
  `sep === 2` cannot hold for Metro by design.
- `ux.css:363` (1024+ by 820 or less): `.ux-kpi-s+.ux-kpi-s:not(.has-trend){display:none}`, so a trend is shortened
  (nowrap, ellipsis), never hidden (review r4 L6). `ux.css:709` and `:717` (600 px or less): the sparkline is hidden and
  the trend sub-line is shown as words. That is the MB7 recommendation, now built. MB7's "hidden by the compact rule"
  clause demands the old state.
- `uxSiteTiles` passes the Site key to `uxHistory`, and the Site wiring (`583bdd7c8`) is an ancestor of the head. All 9
  Sites' series end on their headlines (Site tile 1 = the Site's evaluated actual; tile 2 = `siteM(sk).period.variance`;
  for example Ruiru 13080.32 / 19.68, Kobo 883 / −562). The data is honest. The Site clause and R742 are stale.
- `results.json` (m-r3): 0 page errors, 0 clipped, no sideways scroll in all 30. The only fails are the clauses above.

**Ruling: the expectations follow the screen's accepted form. The check moves from "how it is drawn" to "what it says,
and that it is true".** Spec §9.2's "64×16 sparkline" and §9.3 (D5 "Trend not available yet") and MB7's amended G3 are
superseded by this ruling. The class is "a gate that asserts a drawing form fails when the UI lane changes the form", so
every clause below asserts the trend's figure, its source and its visibility, and asserts the form only by the measure.

**Trend slot (both gates).** A trend slot is each `.ux-kpi .ux-trend` in KPI tiles 1 and 2. It has one of two forms:
- *signed:* no `data-measure`, exactly one `svg.ux-spark`, text `<signed change> against Sep`;
- *measure-named:* `data-measure="monthly-cost"`, no `svg.ux-spark`, text `Monthly cost (up $X|down $X|unchanged) against Sep`.
Any other content, including "Trend not available yet", fails.

**G1+ block 8, amended (`tools/ux_interaction_check.cjs`).** Sweep: the 3 Portfolio overviews and all 9 Site pages
(each operator's `OPS[op].sites`). A Site whose tiles do not render fails; nothing is skipped. For each page:
- **8a, form:** exactly 2 trend slots, each in one of the two forms. Tile 1 is measure-named iff `OPS[op].kind === 'cost'`;
  tile 2 is always signed. So the sparkline count is 1 for Metro and 2 otherwise, computed, never a literal.
- **8b, source and headline:** the series is `uxHistory(op, k1[, sk])` with `k1 = cost|contribution` by kind, and
  `uxHistory(op, 'gap'[, sk])`. Last points equal the headline within 0.005:
  - Portfolio: `opTotals(op).actual` and `.variance` (as now);
  - Site: `ov(DERIVED.sites[`${OPS[op].t.tenant}/${siteM(sk).site}`].actual)`, where `ov` is `opTotals`' rule
    (`cost_to_serve` or `contribution` node if evaluated, else `stated_total`), and `siteM(sk).period.variance`.
- **8c, stated change:** the figure in the text equals `last − Sep` of that series: signed `usdW(ch, true)`; measure-named
  `Math.round(ch)` with "up" if > 0, "down" (absolute value) if < 0, "unchanged" if 0. "Sep" is the series' second-last `m`.
- Page errors 0.

**G3, amended (the capture script).** Grid: Portfolio and Site (Kobo, Thika, Ruiru) × 1440×900, 1280×720, 390×844 ×
light, dark = 36 shots (Site at 1280×720 is added: `ux.css:377` makes it a distinct state). Every shot: theme attribute
matches, page errors 0, no clipped element outside its `.ux-kpi`, no sideways scroll, 2 trend slots in the 8a forms.
Per slot, "the figure" is the change figure (`[−+]?\$[\d,]+` in the slot's text), measured with a `Range` over its text:
- **1440×900:** the slot is visible, inside its tile and in the first viewport; a signed slot's sparkline has
  width > 0; the whole slot text is unclipped (its sub-line's `scrollWidth <= clientWidth`).
- **1280×720:** the sub-line is displayed; a signed slot's sparkline has width > 0; the figure's rect lies inside the
  sub-line's rect (±0.5 px). "against Sep" may be ellipsised: shortened, never hidden.
- **390×844:** the sub-line is displayed; the sparkline's width is 0 (words, not a line); the figure lies inside the
  sub-line, and the text ends "against Sep" (unclipped, as at 1440).

**Plants (each amended clause must fail; evidence `/opt/assetecon/evidence/DS1/m-r4-plant/`).** Each plant is a copy of
`index.html`; the generated file is never edited. Each records the FAIL lines that it must produce.
| Plant | Change in the copy | Must fail |
| --- | --- | --- |
| P1 | delete `DERIVED.history` (as now) | 8a on all 12 pages; G3 form on all 36 |
| P2 | a script after the fixtures adds 100 to the Oct point of Ruiru's `cost` and Kobo's `gap` | 8b on Ruiru and Kobo only |
| P3 | in `uxTrend` and `uxTrendCost`, compare against the first point (`vs[0]`, `s[0].v`) instead of the second-last | 8c on every page |
| P4 | remove `data-measure="monthly-cost"` from `uxTrendCost`'s output | 8a on the 4 Metro pages (Portfolio and 3 Sites) |
| P5 | CSS `.ux-kpi .ux-trend{visibility:hidden}` | G3 1440 |
| P6 | CSS `@media (min-width:1024px) and (max-height:820px){.ux-kpi-s.has-trend{max-width:40px}}` | G3 1280 (figure cut) |
| P7 | CSS `@media (min-width:1024px) and (max-height:820px){.ux-kpi-s+.ux-kpi-s{display:none!important}}` (MB7's old state) | G3 1280 |
| P8 | CSS `@media (max-width:600px){.ux-kpi .ux-spark{display:inline-block!important}}` | G3 390 |
| P9 | CSS `@media (max-width:600px){.ux-kpi-s.has-trend{display:none!important}}` | G3 390 |
A plant that does not produce its FAIL lines is a gate defect: fix the gate, not the plant.

**R742 closes in DS1m's round 4 commit.** Its closing condition (MB7: the Site wiring and `history.sites` both on one
branch, G3 at 1440 showing "against Sep" on the Site tiles) is met on this branch, so the closure moves from the
Decision-page merge to DS1m. Status: `closed (DS1m r4: Site wiring 583bdd7c8 via 25b3ae88b; history.sites from DS1;
G1+ 8a-8c on 9 Sites, G3 Site clauses)`. The D5 header count goes from 2 open to 1 open in the same edit. MB7's
"Decision-page branch closes R742" step is void.

**Not a DS1m condition (recommendation to the UI lane, non-blocking).** On the Portfolio, Metro's tile-1 headline is the
monthly cost itself, so H1's reason (a per-departure headline) does not apply there; a sparkline would be the same
measure. The UI lane may restore it on that one tile. If it does, 8a's form rule still holds unchanged, because the
form follows `data-measure`, not the operator.

**Builder's round 4.** Amend block 8 and the G3 script as above, run the 9 plants, close R742, rerun G1, G1+, G2, G3 and
`plan_switch_check`, and record the results in the packet's "Round 4". `check_manifest.py`'s 3 fails are `main`'s (the
packet shows them on a clean checkout); they are out of DS1m's scope and go to the coordinator.
