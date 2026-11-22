# 0K4m unit 1 handoff (PARTIAL: commits 1a, 1b done; commit 2 `75c9b7e0c` built, not green; builder, Claude, 2026-11-22)

Worktree `/opt/assetecon/AssetOpsV1-0k4m`, branch `task/0K4m-pack-restate` off `main` at `6bfbcf2c7`.
`frontend/node_modules` is a symlink to the main checkout. Never switch branches or commit in `/opt/assetecon/AssetOpsV1`.
Pack = `Docs/demo-sprint/product-direction-layer4/`; M = its `demo-site-scenario-manifest.yaml`.
Scratch: `/tmp/claude-1001/-opt-assetecon-AssetOpsV1/b41e22f5-3892-40aa-b0a6-08516de67e3b/scratchpad/0k4m-u1/` ("S").
Evidence: `/opt/assetecon/evidence/0K4m/`.

## Handshake

Every R1-R6 and I1-I6 question has an answer row in `handshake.md` (Answers table); all folded into spec rev 2.
Mid-build questions to the Architect so far: 0.

## Done

- Pre-flight (on the branch before any edit), outputs in S:
  - `check_manifest.py`: `7565 checks passed (2868 history checks), 1 failed`, the failure `H9 baseline: 4496 checks
    passed before the history checks == 4502, with 0 failed` (S/pre-cm.txt).
  - `check_alignment.py`: `alignment: 114 checks passed, 0 failed`, `C4 words for the reviewer: 69` (S/pre-ca.txt).
  - `hand_typed_scan.py`: exit 0 (S/pre-hts.txt).
  - sha256: kobo study `c52e4755…eccc78b61`, mto study `69a7b9bd…a5a2707d` (both equal the spec), `history.json`
    `9cb1b6bf…173fd4c9` (equal), world view (`tools/world_history.py view --manifest M --out S/view.json`)
    **`7ed4a7207f9dfe2c3abf4c291ccaaad49bb8012319a741c30e8c6286012941bb`** (the boundary base).
- **Commit 1a `b10354db7`**: `check_manifest.py` `CHECK_LABELS=<file>` only. Labels are buffered in `_PASSED`, the
  section is the frame directly under `main()`, `homes_selftest` truncates `_PASSED` when it restores `passes`
  (`check_manifest.py:~829`), and `_write_labels()` asserts `len(_PASSED) == passes`. Count unchanged (7565, H9 4496).
  Main's label file: S/labels-main.tsv (7565 lines; per-section counts: evaluator 2095, stated 332, rights_terms 3,
  narratives 177, anchors 1295, documents 4, workflow 76, homes 376, homes_selftest 1502, factor_map 9, empty_states 11,
  alignment 114, history_checks 2868, reconciliation 91, option_basis 93, operations 17). H9 base = sum of the sections
  before history_checks.
- **Boundary script** S/boundary.py: `python3 S/boundary.py /opt/assetecon/AssetOpsV1-0k4m <base view sha> [--worktree]`
  prints (a) view sha, (b) `world_history.py check` exit, (c) changed manifest lines mapped by `yaml.compose` marks, for
  every commit in main..HEAD (and the working tree). Proven: a comment added inside Kobo `physical` leaves (a) equal and
  is caught by (c) as `tenants.0.sites.0.physical [SITE key physical]`; a comment on `period.variance` is allowed.
- **Commit 1b `d3fea789b`**: the checker (below). Extract committed with it: and its output `replay-studies.json` (both new,
  in the pack). `--check` passes; a file with one extra byte is refused with exit 2. Case fields are nested
  (`cases.<id>.scaled_to_30_days.avoided_l`, `cases.<id>.admission.admitted`, `cases.<id>.admission_parts_failed`).
  List fields `new_dawn_days_below` and M8 `days_without_headroom` are stored as their length. M8 `month_basis` reads
  "rates only (litres per customer kWh, litres per day); no window figure is scaled" (the study has no window scaling
  for M8; spec says "same identity keys"). Each study's `basis` = `{fuel_l, days}`.

## Commit 1b: what the checker holds (for the commit-2 builder)

N1 output shapes (the evaluator must mirror these paths in commit 2; written from the spec, no code shared):

| Place | Shape |
|---|---|
| side | `sites.<t>/<s>.<side>.nodes.<node>: null` and `sites.<t>/<s>.<side>.not_available: {<node>: "<words>"}`; the map only when non-empty; leaves and nodes alike |
| option | `value: null`, `value_if_admissible: null`, `valued_in_money: false`, `not_available: "<words>"`; `money_changes` false (model only); `admissible` from the hard bounds that are available (KOB settings: true), `null` if a hard bound is over a not-available node; a not-available bound's `violations.<id>: null`; sensitivities null; params null |
| option words | the first not-available param's (params order), else the value's, else the first not-available bound's |
| plan | `plans.<tid>.not_available: {<option>: "<words>"}` for every not-available option in the plan's decisions (declaration order); only when non-empty; never chosen in any case |
| history month | `history.<tid>.sites.<s>.periods.<mo>.<side>.nodes.<leaf>: null` plus `...<side>.not_available: {<leaf>: words}`; missing entry per not-available leaf and side: `{side, leaf, record_kind and source_family from empty_states.leaf_sources, cause: MODEL_PENDING, carried_as: null, blocks: <nodes reaching it>, slice: 0K4e}`; never `own`, never in the plan split |
| options | `information` copied verbatim when declared; `replay_sources` on **every** option (sorted study ids of `source:` params and `information.source`; `[]` when none) |

Semantics: `NotAvailable` is a value (not an exception). Operands are evaluated both sides; a not-available operand wins
over a missing record on either side; `|` runs its right side only on a missing record. `unavailable()` takes exactly
one non-empty string constant; a string constant argument to any FUNCS call is a ValueError.

check_manifest.py:
- `evaluator()` presence: failure lines only (`evaluator presence <path>.<key>: ...`), so a clean state adds no count.
  Forward: every independent key (less `SCHEMA_ONLY_IN_MODEL`, through `RENAME`; `NOT_COMPARED` keys too, which is
  what catches P16). Reverse: evaluator keys `not_available`, `information`, `replay_sources` and null-valued keys,
  less a new naming list `SCHEMA_ONLY_IN_EVALUATOR = {covered_by, right_eligibility, claim_state, restore_basis}`
  (measured on main: the only null-valued evaluator keys the model does not compute).
- H3 (history): a null independent node is checked as null with equal `not_available` words (same count as before).
- `stated()` protect_effects: a `source` is accepted only where `k6_protect_cell` (K6's comparison) holds; the
  `design_value` branch stays (K1 forbids the key anyway), so the base count did not move.
- RECORDS exclusions: `calibration_spikes` replaced by `replay_studies` (strings only there; no count moved).
- Section 15 `replay_sources()` after `operations()`: K1-K12 and `VIEW_HELD` (four paths, `until: 0K4f`: per entry
  inside `view_object()`, and the view strings matching K1's words == its string entries). `view_digest()` was split
  into `view_object()` + hash (H11 unchanged). K7 covers the manifest's sections and every `interactive-mockup-vNEXT/*.js`
  plus `tools/gen_fixtures.py`; K11 scans `*.md`/`*.html` at the pack's and the mock's top level plus `fixtures.js`. Both
  skip the `const MANIFEST = …;` literal only after it parses equal to the manifest less `oracle` (dates ISO).
- K11 register rows: the two decision registers (by name, I4) and `CHANGE-REGISTER.md` are exempt only for the rows
  they held at 1b (`K11_BASE_ROWS`, sha256[:16] of each stripped line with the words); a new or edited row obeys.
- K6 information keys resolve as `<key>`, else `admission.<key>`, else `baseline_<x>` from the baseline case; a string
  without a field is free words (unchecked); a string against an integer field must read `"<n> of <days> replayed days"`.
- K9 self-tests: a plant passes only if it adds a failing item (label not failing unplanted) naming its marker.
  On the unrestated manifest the K2 plant cannot show (no `replay_studies`), so K9 fails once there; it passes on the
  scratch restated copy.

Anchors at `d3fea789b`: `independent_model.py` `NotAvailable` :100, `_ev` :273, `evaluate_option` :917, `side_out`
:1320, `_history_missing` :1444; `check_manifest.py` `SCHEMA_ONLY_IN_EVALUATOR` :150, `evaluator` :166, `CAUSES` :1064,
`H8_DERIVED_SHA` :1263, `H9_BASELINE` :1277, section 15 from `VIEW_HELD` :2062 (`K11_BASE_ROWS` :2082, `k9` :2518,
`replay_sources` :2552).

## Commit 1b evidence (scratch S)

- `check_manifest.py` on the unrestated manifest (S/1b-cm.txt, labels S/labels-1b.tsv): **`7610 checks passed (2868
  history checks), 114 failed`** (2m18 wall). By check id: evaluator 28 (`options.<id>.replay_sources = independent []
  (got None)`, all 28 options), evaluator presence 28 (the same key), K3 29 (no `replay_studies`), K11 17 files,
  K12 4 (both Kobo settings' `avoided_l`, `added_throughput_kwh`), K5 3, K1 1 (9 `design_value` keys), K7 1
  (`evaluation`: MTO-INV-CLAIM/BUYNOW/NOACT `extra_l_per_day`), K10 1 (Kobo), K9 1 (K2 plant, as above), H9 1
  (`4496 ... == 4502, with 56 failed`: the 56 are the evaluator lines).
- Base sections: the per-section label multisets equal 1a's on main exactly (`diff` empty); H9's base stays 4496; the
  only new passes are section 15's 44. R4 presence and MODEL_PENDING added no counted checks.
- P16 (S/p16/pack: derived-values.json with KOB-STOPSOC `value` dropped): adds
  `FAIL evaluator presence options.KOB-STOPSOC.value: the independent tree holds the key, the evaluator's dict lacks it`
  (S/p16-cm.txt; the other new lines are the copy's location: alignment A1 cannot reach `.agent/` owner files from
  scratch, and H8 sees the edited file). K4's half: on the scratch restated copy with the model's output as stand-in
  derived values (S/k_smoke.py), dropping the key gives `FAIL K4 options.KOB-STOPSOC: present in derived-values.json,
  null, with not_available "a dispatch replay on Kobo's October as recorded (`; unplanted 113 items, 0 failed.
- P17 (S/p17/pack: the model reads `unavailable` as a missing record): adds `FAIL K9 self-test (P17): unavailable("x")
  | 0 is not available, never 0 (side node 0.0, words None; direct Decimal('0'))` (S/p17-cm.txt).
- Model unchanged on the unrestated manifest except `replay_sources: []` on every option (S/cmp_im.py against main's
  model, sites, plans, history included). Scratch restated copy (S/mk_smoke.py, not the commit-2 manifest): Kobo
  plan/actual/history `candidate_l`, `necessary_l` null with words; KOB-STOPSOC/RESERVE and KIS-BATT60 not available
  and listed under Lakeside's plan; MTO-HULLER valued on M8.
- `extract_replay_studies.py --check`: matches. Boundary at 1b: `b10354db7` and worktree `7ed4a720… == base`, exit 0,
  0 lines; BOUNDARY PASS.

## Commit placement

The dispatch says commit 2 carries `replay-studies.json`; spec §2.1 ("Commit 1, part a: the extract") and the reviewer
guide (commit 1b "must touch only `extract_replay_studies.py`, `replay-studies.json`, `independent_model.py` and
`check_manifest.py`") put it in commit 1. It went in **1b** (spec binds); the packet records this under Known
Deviations.

## Next

1. Commit 2: manifest place by place (spec §2.3 tables), `evaluate_structure.py` N1-N4 (no code shared with the
   checker), regenerate (`evaluate_structure.py`, `regenerate_traceability_columns.py`), re-base H8/H9/H10 with the
   per-section label diff ledger from 4502, plants P1-P10, P13, P16-P19, `check_manifest.py` 0 failed,
   `check_alignment.py`, boundary at every commit, fast check-all, packet. P16's K4 half and P17 rerun on the real
   restated head (P16: drop KOB-STOPSOC `value` from a scratch derived-values.json; P17: the model reads
   `unavailable` as a missing record).

## Risks and open points for commit 2

- **Slice `0K4e` is not a plan slice id** (`plan_model.py` has no `("0K4e", …)` row). `empty_state_problems()`
  (`check_manifest.py` missing-records entry check, `e.get("slice") not in ok_slices`) will reject the evaluator's
  MODEL_PENDING entries unless commit 2 adds the slice row (a pack file) or the Architect rules otherwise. Not changed in 1b.
- H2 `first_present_keys()` reads `factor_sources` too: once Kobo's `necessary_l`/`candidate_l` are `unavailable(...)`,
  the history record keys must still be named by `generator_l`'s second alternative (`record.necessary_l +
  record.candidate_l`). Check H2 at commit 2.
- `empty_states.leaf_sources.MINI_GRID` needs `generator_l` and `admission_parts_failed` (the model's history missing
  entries read `kind`/`family` there; a missing row is a KeyError).
- Spec §2.2 K11 names "the history header lines named in §3"; §3 names none (only the two registers by name). 1b
  exempts the registers' base rows by hash (above). Known Deviation for the packet.

- `homes_selftest`-style save/restore of `passes` elsewhere would desync `_PASSED`; the assert in `_write_labels()`
  catches it.
- `hand_typed_scan.py` and `check_manifest.py` are slow; run through `tools/heavy-slot.sh`.


## Commit 2 (`75c9b7e0c`, partial): what was built

Scripts that made the manifest edits (reproducible, scratch): S/c2/edit1.py (inputs, §2.3 place by place) and S/c2/edit2.py
(stated copies from derived-values.json), plus a small inline step (demo_workflow, bridge_drivers, vertical-factor-map.md).

- **Manifest** (outside the view; view sha `7ed4a720…` unchanged at the commit, `world_history.py check` exit 0): rev 16.17 line;
  `diesel_l = generator_l + unexplained_l + extra_l`; factors `generator_l` (I2 expression verbatim) and `admission_parts_failed: "0"`;
  Kobo `factor_sources` necessary_l/candidate_l `unavailable("dispatch-3.3 ... (0K4e, 4d)")`; `replayed_dawn_days_below_safeguard`
  node gone (structures, protect_nodes, home_categories); `admission` bound; KOB-STOPSOC/RESERVE params per D-0K4.38 with
  `admission_parts_failed_option` from K8 and `information` (baseline_* from K8's baseline case); `feasible_fuel_160l` gone; MTO-HULLER
  and MTO-WELDING `litres_per_kwh` (M8 huller / welder FULL; every admitted restore path restores within 6 days), the four MTO-INV
  `extra_l_per_day` from M8 reduced (0) with `information`; KIS-BATT60 `unavailable("a Kisiwa battery replay (queue Q7)")` on
  `generator_l`; EMB-DEADLINE loses `feasible_nights`, `bus_short_on_infeasible_night`, `extra_missed_departures`; `replay_studies`
  (K8, M8 identity keys from the extract; E NOT_RUN); home_categories (generator_l, admission_parts_failed, GENERATOR_RUNNING,
  KOB-RESERVE money factors, lever generator_l); leaf_sources rows; MODEL_PENDING in the empty_states comment vocabulary.
- **Stated copies**: Kobo bridge one row GENERATOR_RUNNING −450.00 ((1,060 − 700) L × 1.25; bridge still sums to −562.00); findings,
  KOB-NOACT note, both Kobo rows (`disposition: NOT_AVAILABLE_YET`, reasons with `{fig:}`), service obligation, verification target,
  protect effects (Kobo sourced from K8: 4/4/11; Embakasi DERIVED), Kisiwa row, Mto rows (residual_cost 230.00 / 2,910.00), Lakeside
  allocation, oracle OR-MG-1/OR-MG-3. Metro's plan figures did not move.
- **demo_workflow**: KOB-STOPSOC item and its two Actions removed from version 1 (the block's rule: version 1 = the evaluator's
  default items; workflow() failed otherwise). The mock and worked-portfolios.md still tell the Kobo trial story (unit 2/3).
- **bridge_drivers**: SOLAR_SHORTFALL_NECESSARY_GEN and EVENING_NECESSARY_GEN (Kisiwa, Mto) now map to `generator_l` (RC1-RC5
  failed: necessary_l no longer sits on a statement line). CANDIDATE_RUNNING and EVENING_LOAD_GROWTH removed.
- **evaluate_structure.py**: `NotAvailable` (own class; arithmetic dunders return it), `unavailable()` reserved before FUNCS (one
  non-empty string constant, else ValueError; a string argument elsewhere is a ValueError), BinOp/FUNCS evaluate every operand and a
  not-available one wins over Missing, `|` falls through only on Missing; sides `nodes: null` + `not_available`; options, plans,
  history months, MODEL_PENDING missing entries (slice `0K4e`), `information`, `replay_sources`; portfolio sums leave out a
  not-available node. Two allocator changes beyond N1 (see Known Deviations 2 and 3).
- **Regenerated**: derived-values.json, missing-records.json (`evaluate_structure.py`), `regenerate_traceability_columns.py` (CSV
  unchanged: it holds no row for the removed node), `interactive-mockup-vNEXT/fixtures.js` (`tools/gen_fixtures.py`; K7 and K11's
  literal check failed on the stale literal).
- **check_manifest.py**: H8 (both) and H10 re-based with the comment line; **H9 not re-based** (cannot be measured green, below).
- `0K4e` declared in `empty_states.queued_slices` (the manifest's existing mechanism for slices outside the fortnight, which
  `empty_state_problems()` accepts). `plan_model.py` SLICES is the scheduled fortnight (its own note: adding a row there displaces a
  committed slice), so it is more than a data line and was not touched.
- `motivation_figures.py`: no unit-1 check runs it (only render_design_html.py imports it); its fix stays in unit 2.

## Commit 2 evidence

- `check_manifest.py` at `75c9b7e0c` (S/c2/cm4.txt, labels S/c2/labels-head.tsv): **`7466 checks passed (2874 history checks), 346 failed`**.
  K1-K10 and K12 pass; K8 passes (history.json `9cb1b6bf…` unchanged); H11 passes unchanged. Failures:
  - documents (unit 2): 297 anchored/computed-figure lines (domain-and-decision-models 94, worked-portfolios 76, phase-plan 34,
    layer4-transformation-design 20, economic-metric 14, design-questions 13, decision-loop 12, delivery-plan 9, walkthroughs 5,
    integration-source 4, plan-and-action 3, demo-build-cost 2, two-week-build-plan 1, roadmap 1; plus `../../go-to-market/website-content.md` 5
    and `commercial-plan.md` 4, outside the pack), record-tagged/untagged/untraced figure lines, K11 on 18 pack/mock documents
    (incl. `interactive-mockup-vNEXT/index.html` x2, fixture-mapping.md, browser-audit.md, walkthroughs.md);
  - checker defects (not the evaluator's to fix; see Known Deviations 4-6): params rounding x2, empty-states stale rule x1, H2 x12;
  - H9 (base 4208 with 315 failed).
- `check_alignment.py`: `alignment: 114 checks passed, 0 failed`.
- `extract_replay_studies.py --kobo … --mto … --check`: `replay-studies.json matches the two study files` (exit 0).
- `regenerate_traceability_columns.py --check`: exit 0.
- Boundary (`/opt/assetecon/evidence/0K4m/boundary.txt`): 1a, 1b, handoff commits PASS; `75c9b7e0c` view `7ed4a720… == base`,
  `world_history.py check` exit 0, 238 lines changed, **1 forbidden: `+2 [top-level (outside any key)]` = the spec-mandated rev
  line under the header (a comment)**. So it prints BOUNDARY FAIL. The proof script was not edited (an edit to allow header
  comments was refused by the permission layer as weakening the proof); the coordinator rules (Known Deviation 1).
- H9 ledger (PROVISIONAL): `/opt/assetecon/evidence/0K4m/h9-ledger.txt`. Base sections main 4496 (= 4502 − 6) → head 4208:
  evaluator 2095→2151 (+158 −102), stated 332→317 (−15), narratives 177→171 (+12 −18), anchors 1295→987 (−308), documents 4→0
  (−4), workflow 76→67 (−9), homes 376→375 (+13 −14), empty_states 11→10 (−1); rights_terms, homes_selftest, factor_map,
  alignment unchanged. 4496 + 56 − 15 − 6 − 308 − 4 − 9 − 1 − 1 = 4208. Final only after unit 2 turns the documents green.
- Kobo `candidate_l`/`necessary_l` null with words on plan, October and Jul-Sep plan/actual (two MODEL_PENDING entries each);
  contribution 1,445.00 / 883.00, variance −562.00 and the GENERATOR_RUNNING row evaluate.

## For the packet (record)

**Reconciliation table (Lakeside; Metro and Harvest unchanged)**

| Figure | Was | Now | Cause |
|---|---|---|---|
| default items | KIS-REPAIR, BAT-EVIDENCE, KOB-STOPSOC, MTO-INV-CLAIM, MTO-HULLER | KIS-REPAIR, BAT-EVIDENCE, MTO-INV-CLAIM, MTO-HULLER | both Kobo settings not available (D-0K4.38); `kobo_generator` has no valued setting, both under `plans.lakeside-power.not_available` (with KIS-BATT60) |
| spend | 3,750.00 | 3,660.00 | KOB-STOPSOC's 90 leaves |
| value (modelled 12 m) | 6,088.50 | 2,213.33 | KOB-STOPSOC 2,916 leaves; MTO-HULLER 3,540 → 2,213.33 (M8 0.094815 L/kWh x 1,650 kWh = 156.4 L a month, was 68 L); MTO-INV-CLAIM −367.50 → not valued in money (M8: 0 extra litres a day, was 5) |
| valued option costs | 1,520.00 | 1,200.00 | KOB-STOPSOC leaves; the claim's 230 is spend not valued in money |
| not valued in money | 2,230.00 | 2,460.00 | + MTO-INV-CLAIM 230 |
| downside (co-op does not sign) | 2,548.50 | 0.00 | no valued option remains without the huller |
| diesel −20 % | 5,690.00 | 2,682.66 | only the huller buys diesel among valued options |
| feasible_fuel_160l | 5,338.50 | removed | sensitivity removed with KOB-STOPSOC's design value |
| case 5000/no | 2,550.00 / 2,548.50 | 2,460.00 / 0.00 | as above |
| case 6500/no | 6,430.00 / 3,508.50 | 6,340.00 / 2,213.33 | BUYNOW 2,947.50 → 2,910.00 (no extra fuel); KOB-STOPSOC leaves |
| cases 5000/yes, 6500/yes | 3,750.00 / 6,088.50 | 3,660.00 / 2,213.33 | as default |
| MTO-WELDING value | (−8.25 a month) | −48.19 (−4.02 a month) | M8 welder 0.324868 L/kWh (was sfc 0.30 plus) |
| Kobo bridge | −412.50 + −37.50 | −450.00 GENERATOR_RUNNING | one row on the recorded generator litres; split Not available yet |

**K8 baseline fields**: all five read from the study's `baseline` block (`extract_replay_studies.py:94`, `K8_BASELINE_FIELDS`); none from the no-action case.

**Basis print (residual risk; never on screen)**: K8 season generator fuel 2,932.969 L over 61 days (1,442.4 L per 30 days) beside
Kobo's recorded October generator litres 1,060 (diesel 1,180); M8 season 646.180 L over 61 days (317.8 L per 30 days) beside Mto's
recorded 320 L.

**Welder**: `mto-welder` (FULL inverter case), because every admitted restore path restores within 6 days.

**Not restated, stale typed figure**: MTO-WELDING row `break_even_tariff_usd_per_kwh: 0.42` (computed from the old fuel rate; read by
loop-decisions.js, loop-portfolio.js, index.html, fixture-mapping.md, derivation-register.md). Spec §2.3 does not list it; unit 2/3 or a ruling.

## Known Deviations and open points (for the coordinator / Architect)

1. **Boundary vs the rev line.** Spec §2.3 puts the rev line under the header; boundary.py classes any changed line outside every
   key as forbidden. View hash equal; the line is a comment. Ruling needed: accept, or move the rev line.
2. **Allocator: a decision that must take one may take an option not valued in money** (`candidates()`). With M8's 0 extra litres
   the four MTO-INV paths change no money node, so `mto_inverter` (valued, optional: false) had no candidate and the Lakeside
   plan was infeasible. The independent model already takes MTO-INV-CLAIM there (its failure lines showed items
   [KIS-REPAIR, BAT-EVIDENCE, MTO-INV-CLAIM, MTO-HULLER], spend 3,660); the evaluator now agrees. The spec does not define the
   case; the rule was matched to the model's output, so W2 independence is weaker on this point: Architect to confirm the rule.
3. **Sensitivities from the unrounded value**: the evaluator rounded the monthly change to cents before x 12 (HULLER diesel −20 %
   2,682.72 vs the model's 2,682.66); now computed as the value is.
4. **Checker defect (model): params rounded to cents** — `evaluator options.MTO-HULLER.params.litres_per_kwh: 0.094815 != 0.09`
   (and welder 0.324868 != 0.32). The model writes params through money(); a rate below a cent cannot be compared. Fix in
   independent_model.py (not opened by this builder).
5. **Checker defect: `empty_state_problems()` stale rule** (`check_manifest.py:1221`) reads a leaf entry with `carried_as: null` on an
   evaluated side as stale; N1's MODEL_PENDING entries are exactly that (spec §2.4 shape). Needs a MODEL_PENDING exemption.
6. **Checker defect: H2 `first_present_keys()`** takes `generator_l`'s first alternative `record.diesel_l - (record.unexplained_l | 0)`
   as present among October's keys and so expects `diesel_l` on history actual months (12 failures: Kobo, Kisiwa, Mto actual
   Jul-Sep; Kobo plan Jul-Sep, where Kobo's overridden necessary_l no longer names `diesel_l`). The handoff's risk 2. H2 needs to
   read alternatives by the record they need on that month (or the Architect re-words I2).
7. **0 failed is not reachable in commit 2 as specced**: the documents' anchors and K11 (unit 2, commit 3) fail as soon as the
   manifest is restated, and H9 needs 0 base failures to be re-based. Either unit 2 lands before H9 is set, or commit 2 and 3 are
   judged together.
8. Slice `0K4e` declared in `empty_states.queued_slices`, not plan_model.py (above).
9. `replay-studies.json` committed in 1b, not 2 (above).

## Next (exact)

1. Rulings on 1, 2 and 7; fixes for checker defects 4-6 (a checker-side change, independent of this evaluator).
2. Unit 2 (documents, spec §3), including `vertical-factor-map.md` (lever cell already set to `generator_l`) and the go-to-market
   anchors; then rerun `CHECK_LABELS=<file> check_manifest.py`, rebuild the ledger with the same script logic (S/c2 has none saved;
   the ledger header in evidence names the method), set `H9_BASELINE` with its by-section comment, and confirm 0 failed.
3. Boundary rerun for every commit; plants, fast check-all, packet, state entry (later step).

## Rulings applied (rev 3; head after `d346ddd36`)

- Merged main (`d5530f84e`, rulings 1d4713cc8) and `task/0K4m-model-rounding` (`cd9582d26`, N6 on the model side; file not opened).
- Checker fixes 2 and 3 (`bcf9f48c0`): MODEL_PENDING entries checked against the side's `not_available` words; H2 reads nested
  alternatives over October's keys the history generator emits. Plants: dropped words fail; a history month without `necessary_l` fails.
- D-0K4.40: boundary.py (scratch) maps a comment or blank line outside every root entry to `<root>`, allowed. P20 (comment inside
  Kobo `physical`, scratch clone) FAILS: `FORBIDDEN +90 tenants.0.sites.0.physical [SITE key physical]`; P21 (comment above the
  first key) PASSES (`/opt/assetecon/evidence/0K4m/boundary-plants-p20-p21.txt`). Every commit main..HEAD: BOUNDARY PASS.
- `d346ddd36`: N5 (no money clause; "take none" when optional or no candidate), N6 (params half-even 6 places, money half-even once
  at output), Q15 (MTO-WELDING break-even removed), D-0K4.44 (slice 0K4f in the evaluator, Kobo's words "(0K4f)" in factor_sources,
  bridge basis and finding; `queued_slices` row `0K4f` as §2.4, no `0K4e` row). Plan figures unchanged by N5. H8/H10 re-based again.
- `check_manifest.py` at `d346ddd36`: `7475 checks passed (2880 history checks), 337 failed`: anchors() 308, documents() 4, K11 18
  (units 2-3); outside them: **H4b x6** (Kobo Jul-Sep plan/actual: the independent model still writes MODEL_PENDING slice `0K4e`,
  the evaluator `0K4f` per D-0K4.44: a model-side fix) and H9 (set in closing commit 6, D-0K4.43). Param failures gone.

## Commit 2b, evaluator side (rev 4; `c15e10d0d`, K13 `e96751d0b`)

- Seam as main's (§2.3a): structures, factor_map, leaf_sources, home_categories.nodes, bridge_drivers, Kobo bridge rows and
  finding from main; Kobo factor_sources, MODEL_PENDING and the 0K4f queued row out; `forward_baseline.MINI_GRID`
  `admission_parts_failed: "0"`; KOB changes on `candidate_l`, KIS-BATT60 on `necessary_l`; money factors and lever as main;
  Kobo/Kisiwa/Mto hand-typed bridge litres replaced by `{fig:}` actual/plan placeholders; OR-MG-1 rev 4 words;
  vertical-factor-map.md lever back. My own comparison: all 11 K13 parts equal main's canonical hashes.
- Evaluator: D-0K4.46 (protective no-candidate takes none; entry `{chosen: null, admissible: [], how: "no candidate: ..."}`;
  P24 probe on Kisiwa PASS, evidence 2b/plant_p24.py), D-0K4.48 (sensitivity null when not available or money_changes false),
  MODEL_PENDING code removed. D-0K4.47 already held. Plan figures unchanged (3,660.00 / 2,213.33).
- K13 added in check_manifest.py as `product_parity()` after `replay_sources()` (not inside section 15; literals from main at
  1d4713cc8). P23 (`generator_l: "record.diesel_l | 0"` plus its leaf_sources row) fails K13 factor_map and leaf_sources;
  P26 as specified (nulling candidate_l) crashes BOTH models in history (Kobo's contribution becomes not available; the
  evaluator at `evaluate_history` series, the model `Unresolved: not a number: None`) before K13 runs; variant P26b
  (`candidate_l: "0"` override) fails K13 on dv sites, portfolio, history and mr sites. P23 with `record.diesel_l` alone also
  crashes the model (history has no diesel_l). Evidence /opt/assetecon/evidence/0K4m/2b/.
- check_manifest at `e96751d0b` (after merging model side 036b880ae): `7488 checks passed (2868 history checks), 303 failed`.
  Outside anchors()/documents()/K11: H9; K10 (left, coordinator); `evaluator options.MTO-INV-CLAIM/BUYNOW.sensitivities.
  diesel_minus_20pct: None != -230.0 / -2910.0` (spec ambiguity: D-0K4.48 says those read null; the model nulls only on value null).
- Product-parity run (8 files, DB URL unreachable): fails exactly `test_3b1_structure_registry.py::test_t1_leaf_sources_absence_and_words_equal_the_manifest`
  and `test_3b3_structure_evaluate.py::test_t6_each_state_yields_its_leaf_value_on_its_own_record`; the other six files pass.

## Unit 2 (commit 3; branch `task/0K4m-u2-docs` off 2b `ba2da1c4e`, main merged at `c215cb167` for rev 5)

- Commits: `68189f828` domain-and-decision-models; `4547b4daf` worked-portfolios, plan-and-action-workflow, decision
  history; `21a5512ca` layer4 design (+html), roadmap (+html), phase plan, contracts, decision loop, delivery plan;
  `f6c181672` derivation register, integration, reuse matrices, build plans, structure spec :27, go-to-market
  (+html twins by their renderers); `86169d45a` checker REQUIRED and the website H3 rule. Manifest, history and
  derived files untouched.
- Anchored numbers were rewritten from `derived-values.json` by a scratch script (number before each `<!--fig:-->`),
  null anchors removed with their figures and replaced by the gap's words; new figures carry `fig`/`figx`/`rec`.
- `check_manifest.py` at head: `7791 checks passed (2868 history checks), 11 failed`: 9 on `interactive-mockup-vNEXT/`
  (walkthroughs.md anchors x3 and documents(), K11 on browser-audit.md, fixture-mapping.md, index.html x2,
  walkthroughs.md), H9 (`4532 ... == 4502, with 4 failed`), K10. `check_alignment.py` 114 passed, 0 failed. K13 passes.
- Boundary (a)(b)(c) PASS at every unit 2 commit (`/opt/assetecon/evidence/0K4m/u2/boundary.txt`); the manifest and
  history are byte-equal to 2b's, so (d) K13 holds at each. extract `--check`, `motivation_figures.py --check`,
  `regenerate_traceability_columns.py --check` pass; all four html twins regenerate equal.
- Checker edits (section 5 only): REQUIRED headline `options.KOB-STOPSOC.value` -> `options.MTO-HULLER.value` for the
  design and roadmap (KOB-STOPSOC has no value); the 17 Nov Q15 history row requires no anchor (D-0K4.49). No
  documents() history exclusion was needed.
- `render_website_content_html.py` `design_values()` read the retired `design_values` key, so H3 had gone empty; it
  reads `replay_sources` now. Plant: a copy block with 2,213.33 fails the lint (the old rule passed it).
- Sweep: `/opt/assetecon/evidence/0K4m/u2/sweep-1-2.txt`, `sweep-3.txt`. Remaining hits are the world's record
  (330, 730, 412.50, 37.50, 11 of 31; §2.3a), declared litres (Kisiwa 20 L), Metro's anchored 95,634, code line
  references, K8 information in the replay frame (4 of 61), the K8 test vectors in domain §4.2 (season v2 frame),
  dated snapshots in derivation-register §7 quoting the 17 Nov mock code (unit 3 restates the mock), and the two
  decision registers (excluded by name).
- Not covered by `hand_typed_scan.py` (it scans `loop-*.js` and rendered manifest strings only): the documents'
  hand-typed "61" day counts (one anchored, `rec:replay_studies.K8.days`, in website-content.md).
