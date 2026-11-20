# DS1 mid-build questions (RULES §4 item 7)

Raised during the build, after the handshake closed. Each one stops only the affected part. The Architect rules in
`rulings.md`. Count: **6**. MB1 and MB2 (DS1a) and MB3 to MB5 (DS1p) are ruled (`rulings.md`). MB6 (DS1p fix round) is open,
built to the default it states. None changes `history.json` or any October byte.

## MB1 (DS1a): which entry of a Jul/Aug/Sep list a month outside `history.months` reads

- **Gap.** §6.1 says three-value lists are Jul, Aug, Sep. §4.6 lets `generate_scope` run a month outside the set (T9
  generates `2026-10`). The spec does not say which entry October reads for `trend`, `level`, `occupancy`, `cold_kwh`
  or `share`.
- **What was built (no choice made).** Outside the set, a list is read only when its three entries are equal (then
  every choice gives the same value). A list whose entries differ is refused with
  `HISTORY_MONTHS <scope_key> <leaf>`. T9 sets trends and levels to `1 1 1` and the other lists to `anchor`, as its
  text ("`trend 1`, `level 1` and `anchor`") implies.
- **Stopped.** Only `generate_scope` for an out-of-set month with an unequal list. The history months are unaffected.
- **Question.** Keep the refusal, or name the entry (for example: the anchor month reads 1 for `trend`/`level` and
  `anchor` for the others)?

## MB2 (DS1a): refusal text and codes the spec does not list

- **Gap.** §6.1 fixes `ValueError("<CODE> <scope_key> <leaf>")` and ten codes, but some refusals have no scope or leaf,
  and some defects match no listed code.
- **Applied, pending a ruling** (each is one line in `world/history.py`):
  - refusals found before any scope put `history` in the scope position and the field in the leaf position:
    `HISTORY_MONTHS history <month | anchor_period | seasons | day_classes>`,
    `HISTORY_MONEY_LEAVES history money_leaves`, `HISTORY_FAMILY_UNKNOWN history <family>` (a family whose weights
    are not numbers, or no `jitter`);
  - an override for an unknown Site: `HISTORY_RULE_UNKNOWN <tenant/site> sites`; a missing vertical table:
    `HISTORY_RULE_UNKNOWN <scope_key> <vertical>`;
  - a family lacking the weight for the season or day class it is asked for: `HISTORY_FAMILY_UNKNOWN`; a date no day
    class names, or a month with no season: `HISTORY_MONTHS`;
  - a `share` fraction outside [0, 1]: `HISTORY_BOUND` (instead of `allocate`'s `ALLOCATE_BAD_INPUT`);
  - a rule reading a value that is absent or not a number (`energy_model`, `physical`, an October leaf such as
    `crate_days` named by `occupancy … anchor`): `HISTORY_RULE_REF`.
- **Stopped.** Nothing in the generated history; only the wording of these refusals may change.
- **Question.** Confirm these, or name the code and text for each.

## MB3 (DS1p): H2's key set and the EV `kwh` rule base

- **Gap.** H2 says history keys == the first-present `record.*` alternative of each factor-map leaf. For EV, `kwh_2200_2400`
  reads `record.kwh_2200_2400 | record.offpeak_kwh | record.kwh`, so where `offpeak_kwh` is present, `kwh` is never
  first-present. But §5's EV rules generate `kwh` (plan `per_day`, actual `fleet_kwh`) as the base that `share kwh …` and
  `rest kwh peak_kwh` read, and the golden `history.json` (`9cb1b6bf…`) carries it. Literal H2 fails on six sides:
  Embakasi plan and actual and Ruiru actual, in each of the three months (the extra key is `kwh`).
- **What was built (pending a ruling).** H2 leaves out a key that is the base of a `share` or `rest` rule for a leaf the
  side generates (`check_manifest.H_RULE_BASES`), but only when it is a key of October's side and not already
  first-present. Every other key is compared exactly. Kasarani's `kwh` is first-present and stays compared.
- **Stopped.** Only the comparison of that one key. Nothing generated depends on it.
- **Question.** Adopt this exemption, or amend H2's wording (for example, "first-present alternatives plus the keys a
  declared rule reads")?

## MB4 (DS1p): do the observation leaves themselves leave `nodes`?

- **Gap.** §8.1 step 4 removes the nodes named in an (a) entry's `blocks`. But `periods.<side>.nodes` also holds every
  factor value, as October's does. So the (a) leaves (`major_assets`, `field_visits`, `reduced_days`,
  `cooling_minutes_unavailable`, `excursion_*`, `backup_unproven_days`, `charger_out_days`, …) would stay in `nodes` at
  their fallback 0. Some, such as `field_visits`, block no node (`blocks: []`). R7 and D-DS1.12 say none reads as zero.
- **What was built (pending a ruling).** The (a) leaves are dropped from `nodes` as well. They are not added to
  `not_observed`, which lists the nodes, and each is named by its own `missing` entry's `leaf`. The independent model
  does the same, and H4 also asserts that no observation leaf is in `nodes` and that each has its `NOT_IN_HISTORY` entry.
- **Stopped.** Only whether these leaves are listed. No outcome or series value depends on them.
- **Question.** Confirm, or list the leaves under `not_observed` (H4's "names it in `blocks`" would then need a
  leaf-level form)?

## MB5 (DS1p): which history sides get (a) and (b)

- **Gap.** Step 4 is "per side". (a) is conditioned per Site ("October's actual takes from `observations.october`"),
  while (b) is "every other entry `missing_records()` would give for an observed side". The spec does not say whether the
  plan side gets (a), or whether it gets (b).
- **What was built (pending a ruling), following the wording.**
  - (a) applies to both sides, so the plan side's Protect and O2 nodes on those leaves are also `not_observed`. This
    matches R6 ("no `asset_days_*` … in `periods` … nodes").
  - (b) applies to the actual side only, as in `missing_records()` (`sides[1:]`). Ruiru's plan, a stated total as in
    October, therefore carries only its (a) entry (`charger_out_days`), not the target-side `RESIDUAL` entry October
    gives.
  - Today (b) yields no entry on any history side.
- **Stopped.** Only the plan side's `missing` list.
- **Question.** Confirm, or name the plan side's entries (for example, October's target-side entry carried over)?

## MB6 (DS1p fix round): H13's key for a target-side `leaves` subject

- **Gap.** H13 keys by (subject, `record_kind`, `cause`, `carried_as`) and requires equality with October's same-side
  entries. The review M1 ruling also says entries are "computed on the history records by the same helper". For a
  target-side `ASSUMPTION`, the subject is the list of split leaves, and the helper computes it from each month's
  records. Mto's October list includes `unmapped_kwh` because October's actual has the incident's
  `unbilled_mapping_kwh`. History has none (a `zero` rule), so the helper leaves `unmapped_kwh` out. With list keys, H13
  fails on Mto's plan in all three months. This was shown by a plant that keys the lists: 3 failures, all Mto plan.
- **What was built (pending a ruling).** H13 keys a `leaves` subject by its kind only
  (`check_manifest.entry_key13`). The list itself is compared in full against the independent model by H4b. Every
  other subject is keyed whole.
- **Stopped.** Only H13's comparison of the leaf list. Nothing generated depends on it.
- **Question.** Keep this key, or should the history month carry October's leaf list instead of its own? The second
  would contradict "computed on the history records".

## MB7 (DS1m): G3 asks for the trend to be visible where the mock-up's own CSS hides it

- **Gap.** Spec §9.4 G3 passes a shot only if each `.ux-kpi .ux-trend` on the overview is visible and not clipped, at
  1280×720 and 390×844 as well as 1440×900. The mock-up's existing compact rules hide every KPI sub-line after the
  first, and the trend is the second sub-line of tiles 1 and 2:
  - `ux.css:246` (inside `@media (max-width:600px)`): `.ux-kpi-s+.ux-kpi-s{display:none}`;
  - `ux.css:360` (inside `@media (min-width:1024px) and (max-height:820px)`, which 1280×720 meets): the same rule.
- **Measured** (commit `160fed3b6`, `/opt/assetecon/evidence/DS1/m-g3-160fed3b6/results.json`): 6 of 18 Portfolio
  states pass (all 1440×900, light and dark, three operators). The 12 at 1280×720 and 390×844 render the trend with
  `display:none` (0×0 box). Page errors are 0 in all 18. The pre-existing Site tiles behave the same way at 390×844.
- **Why it is not built.** Making the trend visible there is a change to `ux.css` (screen code). Spec §9.2 says no screen
  code changes, and `ux.css` is not in §3's DS1m file list. The UI Architect is editing these source files on
  `task/uiux-design-model`.
- **Stopped.** Only G3's pass at 1280×720 and 390×844. The trend wiring, G1, G1+, G2 and the 1440×900 shots are done.
- **Question.** Is the hidden trend at the compact sizes the intended design (amend G3 to "visible at 1440×900; at
  1280×720 and 390×844 the slot is present in the DOM and hidden by the compact rule"), or should the UI lane change the
  compact rule so that the trend line survives (then G3 stands, and DS1m's shots are retaken after that change)?

## MB8 (DS1m): the regenerated fixtures carry one non-trend text change, from the pack merge

- **Observed.** Regenerating `fixtures.js` from `main`'s manifest also brings the manifest changes the pack merge
  (`54808af06`) made: `MANIFEST` gains `empty_states` and `history`, and `home_categories` changes (one `shown` text
  replaced by `deferred: usable_capacity`, plus the RECON-1 `reconciliation` block). `DERIVED` gains only `history`;
  `REPLAY_PATTERNS` and `REPLAY_VALUES` are unchanged.
- **Rendered effect** (jsdom, all 205 renders, `tools/rendered-text.json` before and after): the only change outside
  the three Portfolio overviews' trend slots and sparkline names is one Lakeside Portfolio sentence:
  - before: "room with no customer: not available yet until the energy management export by time window";
  - after: "room with no customer: not available yet".
  No figure changes on any screen; no drawer text changes; no other operator or route changes.
- **Not decided.** It is the pack's own (owner-approved) wording reaching the screen. A generated file is never
  hand-edited, so DS1m cannot keep the old sentence. Built: regenerated as the spec says.
- **Question.** Confirm this carried wording change is accepted with DS1m (it is not a trend figure, so it is outside
  §9.2's expected change).
