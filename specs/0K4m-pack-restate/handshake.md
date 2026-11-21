# 0K4m handshake (rev 1 spec; reviewer and implementer pre-flight)

Fresh Claude reviewer, 2026-11-21, on `main` at `e19713a9f`. Read: `spec.md`, `reviewer-guide.md`, D-0K4.31 to
D-0K4.37 (`rulings-2.md`), owner-away rows 71-74, `owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`,
0K4d's packet §1 and review, both `study.json` files, and the code below. All paths under the pack are relative to
`Docs/demo-sprint/product-direction-layer4/` ("the pack"); `M` is its manifest.

**Checked and found as the spec says.** `view.py:17-20` allowlist; `world_history.py view` (`tools/world_history.py:121-147`);
both study sha256 (`c52e4755…eccc78b61`, `69a7b9bd…a5a2707d`) and `history.json` (`9cb1b6bf…173fd4c9`) on disk; study
`commit` `6fd0d6bb6` is an ancestor of `main` (0K4d commit 2; only `host/tests/test_0k4d_v8_study.py` differs to the merge
`03c665012`, so the model code is the merged code); every K8/M8 field §2.1 names exists, and the K8 `baseline` block holds
all five baseline fields, so the "no-action case" fallback (spec:98) is never used; `H8_*`, `H10_*`, `H9_BASELINE = 4502`
(`check_manifest.py:1198-1212`), H11 (:1466-1468), `main()` order and the excluded-key list (:1974-2004); `stated()`'s
protect-effects branch (:256-262); `gen_fixtures.py:116-154`; `REPLAY_OPTS` (`loop-core.js:288`); `DVTEXT`/`dvTag`
(`loop-portfolio.js:269-270`); `loop-core.js:243, 425`; `loop-protect.js:88`; `hand_typed_scan.py:124`;
`audit.mjs:127-132`; `ux_interaction_check.cjs:231, 420`. Document lines 5, 21, 205, 209, 428, 576-581, 614-618, 755 of
`domain-and-decision-models.md`, `phase-plan-and-acceptance.md:144, 295`, `worked-portfolios.md:166-167`,
`economic-metric-and-effect-contracts.md:78, 227` (`:245` is the unexplained row; the candidate row is `:243`),
`layer4-transformation-design.md:489`, `decision-loop-specification.md:241`, `delivery-plan.md:172` hold what the spec
says. `check_alignment.py`: 114 passed, 0 failed, 69 C4 words. Doc pointer: spec:7 and reviewer-guide:4 cite
`rulings.md` for D-0K4.31 to D-0K4.37; they are in `rulings-2.md`.

## Reviewer questions (R)

**R1. The world-view boundary is testable, but not as the guide writes it** (`reviewer-guide.md:22-24`; spec §1.2,
§2.3). The guide's "no hunk inside a site's `site`, `code`, `physical`, `tariff` or `period`" fails by design: the
bridge rows and `variance` the spec rewrites (`M:110-115`) sit under `period:` but outside `PERIOD_KEYS`. The guide also
omits the tenant keys the view copies (`vertical`, `prices`, `energy_model`, `capacity_crates_per_room`; `view.py:18`)
and the top-level `history` block. And the view hash is semantic (parsed YAML), not bytes: a reformatted number or a
comment inside `physical` passes it.
*Default:* three proofs at every commit (`for c in $(git rev-list --reverse main..HEAD)`):
(a) `world_history.py view` sha256 equals the pre-flight hash;
(b) `world_history.py check --manifest M --history history.json` exits 0 (`tools/world_history.py:131-160`), a byte
proof that the history regenerates;
(c) a scratch script maps each `git diff -U0 main` line of `M` to its key path with `yaml.compose` marks, and asserts
that no line, comment lines included, falls in a node the allowlist copies.
Fix guide check 3 to "`period.plan`, `period.actual`, `period.coverage`, and the TOP/TENANT/SITE keys". Only commit 2
touches `M`, so the loop is cheap.

**R2. Kobo's avoided litres stand on a season that burns more than the world's October.** This is the owner's
"loyal to the operating world" test (spec:171; `study.json` `baseline.fuel_l` 18770999/6400 L over 61 days, so
1,442.4 L per 30 days). KOB-STOPSOC subtracts K8's absolute 212.751 L a month from October's `generator_l`, which is
1,180 − 120 = 1,060 L (`M:107`). The study's month is also 30 days, against the pack's 31-day period and `months: 12`.
*Default:* judge against the absolute form D-0K4.32 rules. Add a K2 sibling check that each `avoided_l` ≤ the site's
`generator_l`. The packet's residual-risk section names the basis gap (season baseline against record), and the share
form (`avoided_l / baseline fuel × generator_l`) is queued with 0K4f, whose world rebuild aligns the two. No second
figure is shown on screen.

**R3. Mto: which study case, and what the inverter reason may claim** (spec:190-193; `mto-61d/study.json`
`demand[2..3]`, `capacity`). The study also holds `reduced-mto-huller` (0.251 L/kWh) and `reduced-mto-welder` (0.352).
The huller is gated on the restore (`requires_restore`, `M:1013`), so FULL is right for it. The welder has no gate and
runs from `as_of` on the reduced inverter until the restore. The reason text "the battery refills by mid-afternoon on
every day the 25 kW limit binds" is not a study field: the study gives only `extra_fuel_l_per_day`,
`extra_generator_kwh` and `extra_unserved_kwh`, all 0.
*Default:* the welder uses `mto-welder` (FULL), because every admitted restore path restores within 6 days, and the
packet says so. The reason reads "over the 61 replayed days the 25 kW limit adds no generator energy and no unserved
energy", with `extra_generator_kwh` and `extra_unserved_kwh` as sourced `information` fields that K6 checks.

**R4. "Missing is never 0" has two holes in the checker** (spec N1, K4, P10).
(a) `evaluator()` (`check_manifest.py:129-143`) cannot tell a null from an absent key: `get()` returns `None` for both,
and `got == r` passes when `r` is `None`. An evaluator that silently drops `candidate_l` therefore passes, so the mirror
of P10 is not caught.
(b) Both evaluators' `|` falls through on a missing record (`evaluate_structure.py:107-111`; `independent_model.py:248`).
If not-available is built as a `Missing`/`Unresolved` subclass, `unavailable(…) | 0`, or any leaf of the form
`record.x | 0` fed by it, becomes 0.
*Default:* N1 states that not-available is not a missing record: `|` never falls through it, and BIN, FUNCS and
`money()` propagate it. K4 asserts, per reached path, that the key is present with value `null` and has its
`not_available` entry. Two plants: P16, the evaluator omits a null key (fails K4); P17, a scratch factor
`unavailable("x") | 0` in K9's self-test (must yield null).

**R5. The H9 ledger cannot be diffed by name today** (spec:229-233; guide:45-46). `check()` and `eq()` keep no label
for a pass (`check_manifest.py:72-91`). `evaluator()` adds one check per leaf path of the independent tree, so the new
`information` dicts, the `not_available` maps, `replay_sources`, `generator_l`, `admission_parts_failed` and the
removed node rows move H9 by far more than the spec's listed reasons (anchors, homes rows, stated copies). Labels embed
values ("(got 2916.0)"), so a raw label diff shows every moved figure as one removal plus one addition.
*Default:* commit 1 adds `CHECK_LABELS=<file>`, which writes each pass label with its section function, values
stripped by one regex. The ledger is the per-section multiset diff of main against the branch, saved to evidence. The
H9 comment sums it by section, starting at 4502 − 6. The reviewer reruns the same diff.

**R6. Is `replay-studies.json` tied to 0K4d, or only to itself?** (spec:17, §2.1, K3). Today the chain is
manifest → extract (K2, K3) → study file (`--check`). Nothing ties it to 0K4d's recorded identity
(`specs/0K4d-rerun-restate/packet.md:20-25`). 0K4d recorded no file sha256 anywhere in the repo; spec:17 has only
truncated hashes. K3 omits `days`, `status`, `input_class`, `evidence_class`, `month_basis` and `source_file`, yet the
mock reads `replay_studies.K8.days` (spec:303), so an unchecked 61 would reach the screen.
*Default:* spec §0 writes both full sha256 literals, and the extract refuses a file that differs. K3 covers every
identity key §2.1 lists. The packet prints one three-column table (0K4d packet §1, `study.json`,
`replay-studies.json`) for commit, model, season, season digest and site trajectory digest. The reviewer compares it
by hand.

## Implementer questions (I)

**I1. K1 and K11 cannot pass while the view is frozen** (spec:129-130, :148-152). `M:239`, Mto's
`physical.extra_l_basis`, reads `"design value from calibration spike M …"`, and it is inside the view that 0K4m may
not edit (D-0K4.35). The build also embeds the whole manifest in `index.html:3065` and `fixtures.js`, so K11's raw
`*.html` scan hits it too.
*Default:* add `VIEW_HELD` to `check_manifest.py`, listing the view paths that keep a design value for 0K4f:
- Mto's `extra_l_basis` and `extra_l_per_day_at_half_inverter_capacity`;
- Kobo's `period.actual.necessary_l` and `candidate_l`.

K1 exempts exactly those paths and checks that the list equals what it finds. K11 skips the `const MANIFEST = …;`
literal inside `index.html` and `fixtures.js`, and `vocab_check.cjs` proves the string never renders.

**I2. `generator_l` breaks the history months, and the override reaches Kobo's plan** (spec:166-167, :153-154).
- History `actual` records carry `necessary_l`, `candidate_l` and `unexplained_l` but no `diesel_l` (`history.json`,
  e.g. Kobo 2026-07; rules `M:2111-2114`). So `record.diesel_l - (record.unexplained_l | 0)` is missing on all 9
  MINI_GRID history months, and `evaluate_history` raises `HISTORY_NOT_EVALUATED` (`evaluate_structure.py:801-802`).
- `factor_sources` applies to both sides (`evaluate_structure.py:166`; `independent_model.py:503-507`). Kobo's plan
  `necessary_l` (700, by the `| record.diesel_l` fallback, `M:881`) therefore turns null too.
- `motivation_figures.py:153, 162-164, 199-202` does arithmetic on `KP`/`KA` `necessary_l` and `candidate_l` and will
  raise `TypeError`.

*Default:*
- `generator_l: "record.diesel_l - (record.unexplained_l | 0) | record.necessary_l + record.candidate_l"`. On a history
  month the sum is the recorded generator litres; Kobo's split stays null through `factor_sources`.
- The override stays side-free. Kobo's plan split is null with `MODEL_PENDING` on the plan side too, and spec §2.4's
  "on the actual side" is amended.
- `motivation_figures.py` shows "Generator running" from `generator_l`, and "Not available yet" in the split boxes.
- Figures 2-3 of `layer4-transformation-design.md` are regenerated (unit 2), and its `--check` passes.

**I3. Manifest places the spec does not list, which homes(), workflow() and empty_states() will fail on** (spec §2.3).
- `home_categories.option_money_factors`: `KOB-STOPSOC: [candidate_l, …]` (`M:1584`) and `KIS-BATT60: [necessary_l]`
  (`M:1587`). Both must name factors their `changes` name, which become `generator_l`. KOB-RESERVE has no row.
- `decisions` kobo-generator: `lever: candidate_l` (`M:1609`).
- `findings` kobo-candidate: `factor: candidate_l` (`M:1557`).
- The `bridge_drivers` row `EVENING_LOAD_GROWTH` (`M:1513`).
- `CAUSES` (`check_manifest.py:999`, read at :1149, :1302, :1372) lacks `MODEL_PENDING`.

*Default:*
- Both `option_money_factors` rows and the kobo-generator lever become `generator_l`. Its home is `[optimize, O1]`, the
  same as `candidate_l`'s, so homes()' rule holds.
- KOB-RESERVE gains `[generator_l, battery_throughput_kwh]`.
- The Finding keeps `candidate_l`: it observes candidate running, which is now Not available yet.
- `EVENING_LOAD_GROWTH` and `CANDIDATE_RUNNING` leave `bridge_drivers` once no row uses them.
- `MODEL_PENDING` joins `CAUSES` with the spec's definition, in commit 1.

**I4. The unit 2 and unit 3 place lists are incomplete** (spec §3, §4).
- Sweep and anchor hits outside §3:
  - `product-transition-and-roadmap.md:46` and its `.html` (an anchored 2,916);
  - `structure-specification.md:27`;
  - `two-week-build-plan.md`, `reuse-and-gap-matrix.md`, `plan-and-action-workflow.md`;
  - `layer4-transformation-design.md:56, 353, 498`;
  - `design-questions-and-decisions.md:58, 92` and `decisions-register.md:77, 166`, which are decision registers that
    K11 would fail on.
- Mock:
  - `tools/replay_values.py`, the audit's independent replay set (`audit.mjs:16`), still keys on `forward_replay` and
    `design_value`.
  - `.ux-prov` is the page's "About these figures" popover (`loop-core.js:425`, `ux.css:464-467`), not a per-figure
    chip. The per-figure chip is `.ux-chip` (`loop-ux.js:42, 710`).
  - `SIMTEXT` hand-types "61-day" (spec:281), against spec:303.

*Default:*
- Every file with a failing anchor or a sweep hit is in scope for unit 2.
- The two registers join the K11 and sweep exclusions by name, as decision history.
- `replay_values.py` is rewritten to `source:`, `information:` and `replay_studies`, sharing nothing with
  `gen_fixtures.py`.
- `srcTag` renders `<span class="ux-chip is-neutral" title="…">Simulated</span>`, and `.ux-prov` keeps its role with
  spec:300's copy.
- `SIMTEXT` takes its day count from the fixtures.

**I5. Protect effects have no checked source** (spec:182, `M:326-332`, `M:718-724`). Spec:182 says
`check_manifest.py:259` accepts a `source` "that K6 checks", but K6 checks only option `information`. KOB-NOACT, whose
baseline count of 4 the row states, has no study param at all. EMB's row becomes `class: DERIVED`, and its measure
`departures_missed` is a node, so `eq()` already covers it.
*Default:* the Kobo row carries
`source: {study: K8, field: dawn_days_below, cases: {KOB-NOACT: baseline, KOB-STOPSOC: stop-70-reserve-30, KOB-RESERVE: stop-90-reserve-25}}`.
K6 is extended to it (a planted 0 fails), and `stated()` accepts `source` only when K6 has checked it.

**I6. N1's parser and placeholder details.**
- `unavailable("…")` reaches `Env.ev`'s `FUNCS[node.func.id]` (`evaluate_structure.py:115-122`) with a string
  argument, which `num()` refuses.
- Kobo's record words hold a comma ("generator, solar and battery readings"), which D-5C.25's no-comma rule for record
  words would flag if it is applied to these.
- `admission.first_failing_part` is `null` on both K8 cases, and K6 compares only numbers, booleans and strings.
- The EMB placeholders are elided at spec:203-204.

*Default:*
- `unavailable` is a reserved call, handled before `FUNCS` in both evaluators, and a string argument is legal only
  there.
- The words keep the comma (D-5C.25 governs product vocabulary, not pack expressions).
- K6 compares `null` to `null`.
- The placeholders are `{fig:options.EMB-DEADLINE.bound.supplied_kwh_night}` and `…bound.required_kwh_night`. Both
  paths exist in `derived-values.json` today.

## Pre-flight as run here

`check_manifest.py` on `main` (pooled): `7565 checks passed (2868 history checks), 1 failed`, the one failure
`H9 baseline: 4496 checks passed before the history checks == 4502, with 0 failed`, as spec §0 expects.
`hand_typed_scan.py` ran past 100 s unpooled and was stopped. The builder runs it through `tools/heavy-slot.sh`.
