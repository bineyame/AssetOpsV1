# 0K4m unit 1 handoff (partial: commits 1a and 1b done, commit 2 next; builder, Claude, 2026-11-22)

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
