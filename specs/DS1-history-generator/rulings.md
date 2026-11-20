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
