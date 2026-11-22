# 0K4m review

## Unit 1 review (fresh Claude reviewer, 2026-11-22; head `7e461e491`)

**Verdict: REVISE.** Most of unit 1 checks out:
- the boundary holds at every commit;
- the restated figures reproduce, and I recomputed them by hand;
- the 331 `check_manifest.py` failures are all inside D-0K4.43's allowance;
- every plant that can run now fails as it should.

One problem is outside `check_manifest.py`: the restated pack breaks product parity tests. 54 backend tests fail, plus 1 simulator world test, and all of them pass on main. Spec §7 forbids changing tests or product code, so units 2 and 3 cannot clear them. That needs an Architect ruling before commit 6 (H1).

One Medium: the evaluator's allocator still has a must-take filter, so it does not implement N5 as D-0K4.41 words it. This is latent; no current figure moves.

The Lows are records and cleanup.

Discovery depth (W5): I read the spec rev 3, the reviewer guide, the handoff, and D-0K4.38 to .44 with Q15-Q18, plus the full diff of the evaluator, the independent model's N1/N5/N6 paths, the manifest, and the checker fixes.

### Findings

| # | Sev | Where | What is wrong | Why it matters | Fix |
|---|---|---|---|---|---|
| H1 | High (acceptance gap; spec gap) | `simulator/tests/world/test_records.py:574`; `backend/tests/test_3b1_structure_registry.py`, `test_3b3_structure_evaluate.py`, `test_3b4_observer.py`, `test_2a_canonical_manifest_parity.py`, `test_5a_targets.py` | These product tests read the pack's manifest (`structures.MINI_GRID`, `factor_map`, `leaf_sources`), `derived-values.json` and `missing-records.json`, and assert that the product's registry, evaluator, observer and targets match them. At head, `test_t9_no_budget_line_for_an_assumption` fails: Kobo's plan ASSUMPTION entry no longer lists `necessary_l`. The 9 backend files that read pack files and need no database show `56 failed, 429 passed`; main (`b10354db7`, pack identical to main) shows `2 failed, 483 passed`, so 54 failures are new. Examples: `diesel_l` reads `necessary_l + candidate_l + …` in the product against `generator_l + …` in the pack; `generator_l` and `admission_parts_failed` are new leaves; `replayed_dawn_days_below_safeguard` is gone; `Decimal(None)` hits Kobo's null leaves; there is a `KeyError: 'necessary_l'`. `tools/select-tests.py:63` selects these tests from the manifest. | The reviewer guide (item 3) says any world-test failure is High. D-0K4.35 protected only the world view, but the product also has parity with the pack's structures and derived files. Neither the spec, the rulings nor the handoff names this surface, and nothing in units 2-3 (documents and mock only) clears it. Merged as specced, commit 6 would turn main red. | Architect ruling before commit 6. The choice is whether 0K4m: (a) keeps the parity surfaces unchanged; (b) takes in the product registry and tests, against spec §7; or (c) pins those tests to the pre-0K4m pack, with 0K4f as the owner. Then re-scope and resize. The packet should list this class. |
| M1 | Medium (acceptance gap, latent) | `evaluate_structure.py:565` | Line 552 adds "take none" when a decision has no candidate (N5). Line 565 then drops every combination in which an `optional: false` valued decision takes nothing, so that case becomes infeasible. D-0K4.41 says the evaluator "drops its must clause". Probe on a scratch copy, with all four MTO-INV `extra_l_per_day` set to `unavailable("probe")`: the evaluator returns `infeasible`; the independent model takes none (items KIS-REPAIR and BAT-EVIDENCE, spend 2,230.00). | The evaluator departs from the stated rule. No figure moves today, but the first manifest that hits the case will see the two models disagree. | Remove the filter at :565, or apply it only when the decision has a candidate. Add the probe as a K9-style plant. |
| L1 | Low (spec gap) | `independent_model.py:1047-1049`; `evaluate_structure.py:552, 587` | For a protective decision with no candidate, the model returns an infeasible plan. The evaluator adds "take none", and then `next(...)` at :587 raises `StopIteration`. N5 says "or with no candidate" whatever the decision's kind. | Neither model follows N5 here (unexercised today). | Architect to say whether N5's no-candidate clause covers protective decisions; both models then follow it. |
| L2 | Low (W2 record) | `evaluate_structure.py:443-444` against `handoff.md:51`; `evaluate_structure.py:50-66` against `independent_model.py:100-119` | The evaluator was written from the spec plus the 1b handoff's N1 table. Its comment repeats the handoff's option-words rule word for word ("the first not-available param's (params order), else the value's, else the first not-available bound's"). That rule is not in the spec. Neither is "admissible from the available bounds", and the spec only implies that not-available wins over a missing record. The two `NotAvailable` classes share an idiom (`_same`, one dunder chain) but differ in body. I found no shared import, helper or list, and no copied logic block. The N5 divergence above shows the two models are independent. N5 itself is now stated by D-0K4.41, and both models implement it from that text, apart from M1 and L1. N6: params at six places in both (`evaluate_structure.py:458`; `independent_model.py:985`). Money is computed once from the unrounded value at option level in both. The checker fixes `bcf9f48c0`/`09b6a8757` were made from the evaluator side. I read them: they are scoped to D-0K4.42 and they tighten the check. | Where the spec is silent, both models carry one builder's choice, so an error there would pass the checker. | Fold the option-words precedence and the bound-null rule into spec N1. Record in the packet that the checker fixes came from the evaluator side. |
| L3 | Low (N6, latent) | `evaluate_structure.py:573` against `independent_model.py:1093, 1121` | The evaluator's plan value sums option values that are already rounded. The model sums unrounded values and rounds once. | N6 says money is rounded once, at output. A plan with two or more valued options could differ by a cent. All equal today. | Sum the unrounded option values (`_value`) and round once. |
| L4 | Low (sweep, unit 2) | `demo-site-scenario-manifest.yaml:310, 952`; `:195, :251` | The comments at :310 and :952 still describe design values as allowed provenance. The Kisiwa and Mto bridge bases at :195 and :251 hand-type "80 L" and "20 L" ("Necessary … by dispatch classification"); their drivers now map to `generator_l`, a re-mapping spec §2.3 does not list (the handoff records it). | Stale words, and hand-typed figures beside a model mapping. | Unit 2: fix the comments; put `{fig:}` placeholders in the bridge bases, or list them in the sweep with a reason. Name the re-mapping in the packet. |
| L5 | Low (record) | `/opt/assetecon/evidence/0K4m/h9-ledger.txt` | The provisional ledger is at `75c9b7e0c`. At head: evaluator 2095→2153 (+160 −102), empty_states 11→11, base 4211; history_checks 2868→2886 (+51 −33); section 15 +184. | The provisional ledger is not the head's. | Rebuild it at commit 6, as planned. |
| L6 | Low (residual risk, units 2-3) | `derived-values.json`, `options.MTO-INV-CLAIM` / `-BUYNOW` `.sensitivities.diesel_minus_20pct` | These options are not valued in money (value null) but still carry −230.00 and −2,910.00 under diesel −20 %. | A screen could show a money figure for an option the plan lists as not valued in money. | Units 2 and 3 should not render it, or the Architect rules sensitivities null when `money_changes` is false. |

Allowed and noted, not a finding: K11's guard fails on `interactive-mockup-vNEXT/index.html` because its embedded MANIFEST literal is stale (fixtures.js was regenerated; `build.mjs` was not run). That is a unit 3 file, so it is inside D-0K4.43.

### The 331 failures against D-0K4.43

All 331 are inside the allowance:
- **anchors() (308):** 280 anchored, 17 computed, 7 record-tagged and 4 untagged. The files are 16 pack documents, `../../go-to-market/website-content.md` (5) and `commercial-plan.md` (4), which are unit 2's class, and `interactive-mockup-vNEXT/walkthroughs.md` (3), which is unit 3's.
- **documents() (4):** main Parts 1-2, worked portfolios, walkthroughs, roadmap.
- **K11 (18):** pack documents and four mock files.
- **H9 (1):** `4211 … == 4502, with 312 failed`.

No other check fails. H4b is gone at head, and the param failures (P22's class) are gone.

### Restated figures (`derived-values.json`, reproduced)

- **Lakeside:** spend 3,660.00; value 2,213.33; downside 0.00; diesel −20 % 2,682.66. Items: KIS-REPAIR, BAT-EVIDENCE, MTO-INV-CLAIM, MTO-HULLER. `not_available` lists KOB-STOPSOC, KOB-RESERVE and KIS-BATT60.
- **MTO-HULLER by hand:** 0.094815 L/kWh (68267/720000) × 1,650 kWh = 156.445 L a month. 495 − 195.556 − 15 = 284.444 a month; × 12 − 1,200 = 2,213.33. At diesel −20 %: 323.555 × 12 − 1,200 = 2,682.66. The money is computed once, from the unrounded value.
- **Kobo's settings:** `value` null, economics "Not available yet (a dispatch replay on Kobo's October as recorded; 0K4f)"; admitted; never chosen.
- **Kobo's October:** `candidate_l` and `necessary_l` null with "(0K4f)" words on plan and actual. `generator_l` 700 against 1,060; the bridge row is −450.00, which is (1,060 − 700) × 1.25.
- **Mto:** valued on M8. MTO-WELDING −48.19 from 0.324868 L/kWh; `break_even_tariff_usd_per_kwh` is gone from the manifest.
- **Spot checks:** KOB-STOPSOC `min_soc_pct` 33.141398 = 2014997/60800; KOB-RESERVE `dawn_days_below` 11; MTO-HULLER "16 of 61 replayed days" = 16 dates.
- **One-figure rule:** I found no design value beside a model figure in the manifest. The only ones left are the four `VIEW_HELD` view values, which nothing reads.

### Checks run (outputs in my scratch, deleted at the end)

- `check_manifest.py` at head (`CHECK_LABELS` set): `7481 checks passed (2886 history checks), 331 failed`.
- Commit 1a's checker on main (a detached `b10354db7`): `7565 passed, 1 failed` (H9 4496). Its label file is byte-equal to the builder's `labels-main.tsv`. The per-section diff is as in L5.
- `check_alignment.py`: `114 checks passed, 0 failed`.
- `world_history.py check` at head: exit 0.
- `extract_replay_studies.py --check`: matches. Both study sha256 values equal the spec's.
- `regenerate_traceability_columns.py --check`: exit 0.
- `evaluate_structure.py` and `gen_fixtures.py` rerun on a scratch copy: `derived-values.json`, `missing-records.json` and `fixtures.js` come out byte-equal.
- **Boundary at all 15 commits in main..HEAD,** with the builder's `boundary.py`: (a) `7ed4a720…` equals the base, which I recomputed from main; (b) exit 0; (c) 0 forbidden; BOUNDARY PASS.
- **Independent (c):** my own check compares the raw text of each of the 70 view nodes (key line up to the next sibling) between main and each commit. Equal at every commit. It catches P20.
- **Plants on a scratch copy:**
  - P16 fails K4 and evaluator presence.
  - P17 (the model's `|` falls through on not available) fails K9 (P17). Read as a missing record instead, it crashes the model.
  - P20 fails (c); P21 passes.
  - P22 fails evaluator() (0.094815 against 0.09; 0.324868 against 0.32).
  - My own: evaluator N1 propagation broken fails evaluator() (KOB-STOPSOC, KOB-RESERVE and KIS-BATT60: null against 0.0). One `{fig:}` anchor at the wrong path fails anchors() (95,484.00 against 8082.0).
  - The M1 probe, as above.
- **World tests,** host runner, per file: `1 failed, 147 passed` (H1). On main, `test_records.py` gives 29 passed.
- **Backend pack-parity files** (no database, `DATABASE_URL` unset): head 56 failed, main 2 failed.

### Not verified

- `test_ds4_world.py`, `test_wk_walk_world.py` and `test_ddr_rehearsal_postgres.py` also read the pack but need a database, which the brief rules out; they may fail too.
- I did not run check-all, per the brief.
- I did not run the units 2-3 plants (they need a green head).

### Residual risk the packet does not name

- The product-parity surface (H1).
- Decision history documents (`design-questions-and-decisions.md`) hold 13 live `{fig:}` anchors to the restated plan. Unit 2 has to change history rows, or the checker has to treat them as history. The spec does not say which.

## Units 2-3 review (fresh Claude reviewer, 2026-11-22; head `ac298594c`)

**Verdict: ACCEPT WITH FIXES.** The checks the dispatch names hold:
- `check_manifest.py` fails only H9, H10 and K10; `check_alignment.py` passes 114 of 114;
- the DB-free product-parity run fails exactly main's two node ids;
- the boundary passes at every commit from main to head, and K13 passes;
- the mock rebuilds byte-equal and renders with 0 script errors; vocab, copy and hand-typed scans are clean;
- the repaired audit's failing measures are equal on main.

Four findings need fixing on the branch before commit 6:
- H1: on Act first / plan, the mock renders the manifest's `excluded` reasons, so "0K4f" and "queue Q7" show on screen. D-0K4.54 forbids this, and `vocab_check` cannot catch it.
- H2: `derivation-register.md` §3.1 still lists manifest leaves that 0K4m removed, KIS-BATT60's 150 among them.
- M1: the Simulated chip renders without its pill styling ("+$2,213Simulated" on the overview tile).
- M2: `browser-audit.md` reports two audit checks as passing that did not run.

The Lows are optional.

Discovery depth (W5): I read spec rev 5 §2.3a-§8, the reviewer guide, the handoff (2b and unit 2), `packet-unit3.md`, D-0K4.46 to .56, the unit 2 checker and lint diff, the unit 3 mock diff where findings led, and the whole audit repair commit. I spot-checked the shots.

### Findings

| # | Sev | Where | What is wrong | Why it matters | Fix |
|---|---|---|---|---|---|
| H1 | High (acceptance gap: D-0K4.54, D-0K4.51) | `interactive-mockup-vNEXT/loop-portfolio.js:515` (the "Left out of the plan, and why" table); manifest `demo-site-scenario-manifest.yaml:404-406` | The table renders `allocation.excluded[].reason` after the mock's word filter (`loop-core.js:372`). At `portfolio/act-first/plan` (Lakeside) the screen reads: "Buy battery storage to cut generator hours · Kisiwa · Value Not available yet (a Kisiwa battery simulation; queue Q7)" and, twice, "Admitted on the simulation; litres and value Not available yet (a dispatch simulation on Kobo's October as recorded; 0K4f)". The source is `tools/rendered-text.json` at head; on main the same table read the old reasons. These are the three reason strings D-0K4.54 names (`:404-406`). That ruling says the mock "never renders" them and shows the D-0K4.50 strings instead. `vocab_check.cjs:16` has no pattern for slice codes (`0K4f`) or queue codes (`Q7`), so its 0 hits are not evidence for this class. | Codes on screen go against the owner's rule (2026-10-04; UI guidance 2026-10-25). The gap words also differ from the strings the cards show for the same options ("needs a simulation of Kobo's own October"). | For an excluded option that has `not_available`, render the reason through `naText()` (NA_KOBO / NA_KIS), with the admission line for Kobo's settings where the layout has a note. Add a `vocab_check.cjs` rule for slice and queue codes (e.g. `\b\d[A-Z]\d+[a-z]?\b`, `\bqueue Q\d+\b`, `\bQ\d{1,2}\b`), plant it, and sweep every reader of a manifest `reason` (W6). |
| H2 | High (by the reviewer guide: a design value in a current document; also an unlisted sweep hit) | `derivation-register.md:94-96` (M23-M25), `:129` (M58), `:136` (M65), `:213-214` (M142-M143), `:235-236`, `:245-246` (M164-M165, M174-M175), `:257` (M186), `:404` (M333) | §3.1 still lists manifest leaves that 0K4m removed, as live inputs that "move evaluated values in 5 of 5 worlds": the `dawn_adequacy` bound (acceptance 4: the dawn is bounded nowhere); EMB-DEADLINE `extra_missed_departures` and `bus_short_on_infeasible_night`, with the "21-bus night … 406 kW" basis that spec §2.3 removes; **KIS-BATT60 `shifted_fuel_l.value` 150 "(b) assumption"**, now `unavailable(...)`; KOB `changes` reading `avoided_candidate_l` and `dawn_days_below_35pct`; KOB-STOPSOC's `feasible_fuel_160l` sensitivity (160); and the dawn node in `protect_nodes.MINI_GRID`, removed in 2b. Found by resolving every `evaluation.*` path in §3.1 rows against the head manifest. The §3 sweep regexes miss these because they need "L" after 150 and do not cover 160 or 406. | A current register states retired design values and removed checks as current inputs, which is what 0K4m exists to remove. | Restate the class, not the rows: re-resolve every §3.1 path against the manifest. For each removed leaf, mark it "removed (0K4m, D-0K4.xx)" as M66/M67 already do. Then add the path check (each row's path exists, or the row says removed) to the sweep evidence. |
| M1 | Medium (UI defect; the spec's markup) | `loop-portfolio.js:284` (`srcTag`); `loop-ux.js:341` (overview tile), `:710`, `:728`; `ux.css:101, 105` | The chip is `<span class="ux-chip is-neutral">`, but the pill layout (padding, radius, `font-size: var(--fs-xs)`, inline-flex) sits on `.ux-chip.attn-k` (`ux.css:101`). `is-neutral` only sets colours. On screen, "Simulated" renders as a grey text run in its parent's font. On the overview's 12-month tile it renders at the tile's display size with no space: "+$2,213Simulated" (`/opt/assetecon/evidence/0K4m/u3/lakeside-portfolio-1440-light.png`; also on the Mto demand cards, `lakeside-decision_mto-demand-1440-light.png`). The "Modelled" mark beside it is a proper pill. The builder followed spec §4's literal markup, which omits `attn-k`. | It is the headline figure on the first screen, and it breaks the one-component grammar of the UI standing brief. | Render `class="ux-chip attn-k is-neutral"` (as `loop-ux.js:42`), with a space before it in the tile. Re-shoot the overview at 1440 and 390. Architect: errata on spec §4's markup. |
| M2 | Medium (the audit repair weakens a report) | `tools/gen_docs.cjs:261` and `:271` → `browser-audit.md:18`; `tools/audit.mjs:118`, `:163-165` | The repair records `reviewNotesNoDrawer` (71 routes whose review-notes drawer never opens) and `focusTargetsGone` (2 selectors) in `audit-results.json`. That is honest in the JSON. But the regenerated `browser-audit.md` still says the role-word check covered "review-notes drawers" (0 hits), and focus "5/5", without saying that 71 drawers and 2 targets were not checked. I confirmed the same 71 and 2 on main's mock with the repaired audit, so neither is a 0K4m regression. The underlying mock fault (the review-notes handler throws on screens without `.models`, per the comment at `:118`) is pre-existing. | A reader of the audit document takes a skipped check for a passed one. | Print both counts in `gen_docs.cjs` rows (e.g. "0 hits; review-notes drawer did not open on 71 routes"; "focus 5/5; 2 selectors have no target on the landed frame"). Queue the throwing review-notes handler as a mock defect. |
| L1 | Low (0K4m regression in an audit measure; from unit 1) | manifest `:135`, `:144` (introduced at `75c9b7e0c`); `loop-core.js:11-19`; `browser-audit.md:33` | `{fig:options.KOB-*.information.admitted}` points at a boolean. `tplFmt` formats only strings and numbers, so the mock's manifest-string walk lists both as unresolved and replaces each with "not available". The audit reports "unresolved 2" (main: 0). The comment at `loop-core.js:11` says "the audit fails on it", but it does not. The two option `reason` strings are not on screen (D-0K4.54), so no reader sees this today. | A placeholder that cannot resolve is a latent "not available" for a figure that exists. The audit's stated gate is not enforced. | Word the admission in the reason (or point at a numeric field). Make `audit.mjs` fail when `unresolved.length > 0`. |
| L2 | Low (residual coverage) | `tools/audit.mjs:171` | The contrast sample fell from 26 elements to 21 (main against head, same selector list, because `.dv` tags left), and the new Simulated chip is in no contrast set. | The chip's text-2 on surface-2 contrast is unmeasured. | Add `.ux-chip.is-neutral` to the contrast selectors. |
| L3 | Low (preference) | `tools/hand_typed_scan.py:125-126`; manifest `:140` `one_off_detail` | The two new allow entries (60, 30) are justified. The string quotes the vendor quote, record text in the KAS-OEM-STOPGAP detail's class, and the same amounts exist as `cost_lines` (`:996`). | None today. | Optional: write the detail with `{rec:}` placeholders onto `cost_lines`, so that no allow entry is needed. |
| L4 | Low (pre-existing copy) | `Docs/go-to-market/website-content.md` (the Lakeside "Today" card, "Kobo burned half that …") | "330 litres, as October's records classify them, went on running its solar and battery could have carried" is missing words ("…running the generator while solar and battery could have carried the load"). The garble is on main as well. Unit 2 edited this sentence. | Public copy. | Fix the sentence while the file is open. |

### Checks run (at `ac298594c`, in a detached review worktree)

- `python3 check_manifest.py`: `7798 checks passed (2867 history checks), 3 failed`, namely H10 (prefix `96acfb22b6f3`), H9 (`4535 … == 4502, with 0 failed`) and K10. This is the expected state.
- `python3 check_alignment.py`: `alignment: 114 checks passed, 0 failed`.
- Rebuild (`evaluate_structure.py`, `gen_fixtures.py`, `build.mjs`): "evaluator vs stated fields: 0 differences", `fixtures.js` sha `7cf283865afc`. `git status` stayed clean, so the rebuild is byte-equal.
- `render_text.cjs`: 237 renders, 0 script errors. `vocab_check`: 0 hits (224 earlier-view hits not failing, as before). `copy_check`: 0. `hand_typed_scan.py`: exit 0, count 0, allow 48 of 48 used.
- Product parity (8 files, each alone; `DATABASE_URL` unset, `ASSETOPS_TEST_DATABASE_URL` unreachable; `heavy-slot.sh` + `run-host-tests.ps1`): `test_3b1` 1 failed / 78 passed (`test_t1_leaf_sources_absence_and_words_equal_the_manifest`); `test_3b3` 1 failed / 71 (`test_t6_each_state_yields_its_leaf_value_on_its_own_record`). `test_2a` 5, `test_3b4` 93, `test_5a` 39, `test_ds4_world` 65, `test_wk_walk_world` 103 and `simulator/tests/world/test_records.py` 29 all passed. These are exactly main's two failing ids.
- Boundary on main..HEAD, with the builder's script (read first) plus my own (a) and (b): the view sha `7ed4a7207f9d…` is equal on main and head; `world_history.py check` exit 0; `history.json` equal to main; (c) 0 forbidden lines at every commit, including `f560d3f9e`, `5c8697f17` and `ac298594c`. BOUNDARY PASS. (d): K13 has no failure at head.
- 2b: D-0K4.48. Every option whose value is null has a null sensitivity (or none) in `derived-values.json`. The evaluator nulls them through the value; the model nulls them at `independent_model.py:986`. D-0K4.46: the evaluator (`evaluate_structure.py:589-593`) and the model (`independent_model.py:1047-1053`) both take none, with the spec's `how`. `plant_p24.py` at head: PASS. The K9 self-tests P24 and P25 pass inside `check_manifest.py`. The P23 and P26b evidence (`/opt/assetecon/evidence/0K4m/2b/`) fails K13 on the named parts. I accept D-0K4.47 as a record ruling and did not re-derive it.
- Unit 2 lint: on main, `derived-values.json` has 4 options with `design_values`; at 2b and head it has 0. So `design_values()` returned an empty set at 2b, and H3 was silently empty. At head it reads `replay_sources` and gives `[284.44, 2213.33]`. `--fixtures`: 94 planted violations caught; `--lint-only website-content.md`: ok. The REQUIRED edits are sound: KOB-STOPSOC has no value; the Q15 history row is dated 17 Nov (D-0K4.49). No current document loses a required anchor.
- No sensitivity appears for a valueless option: `domain-and-decision-models.md:747` reads "none (no value …)" for Kobo, and every document anchor to `sensitivities.*` is MTO-HULLER or KIRI-REPAIR. My plant B (below) shows the class is checked.
- Kobo wording: the website reads "as October's records classify them/it" (`8ad1bf12b`), the same as the mock's on-screen words. The code is absent there, which is right for public copy.
- Unit 3 copy: every D-0K4.50 and D-0K4.55 exact string is in the source (`loop-portfolio.js:277`, `loop-core.js` popover, `loop-decisions.js:185` wear row, `:283` verify line with "14 matched days before and after"). The Kobo split carries the D-0K4.51 words on 13 rendered screens, and its 0K4f line is in the reviewer block only. The rendered text has 0 "Design estimate", 0 "†" and 0 "replay". "0K4f" appears twice, both under H1.
- Shots: I viewed the Kobo decision, the overview and the Mto demand page (1440, light). The Kobo cards read "Not available yet: needs a simulation of Kobo's own October", with the admission and dawn lines, and no litres or money figure. The Mto figures reconcile by hand: 495 − 195.56 − 15 = 284.44 a month. The chip defect is M1.
- Audit against main: I ran head's `audit.mjs` on main's mock in a scratch copy (one rename, `SOURCE_PATTERNS` → `REPLAY_PATTERNS`). These measures are identical on main: badLinkRoutes 87, vocabHits 38, identifierHitsPreservedV70 133, switchCasesOk 2/8, preservedIdentical 0/80, rev6TabOrder false, rev7EvMeasure false, rev6DesignValueLabels false, reviewNotesNoDrawer 71 and focusTargetsGone 2. So these are not 0K4m regressions. Three measures differ: designValueScan (expected), contrast 26 → 21 (L2) and unresolvedPlaceholders 0 → 2 (L1). On main, all routes are ok with 0 console errors. The five crashes came from 2b's fixtures, and the head fixes them (207 of 207 ok, `consoleErrorRoutes: 0`).
- Audit helpers: `evClick` either opens the drawer's visible opener, or records the button in `dvScan.unreachable` and skips it (0 at head). It does not skip silently. A hidden button outside both cases would throw, and the run would fail loudly. `setOp` writes the `l4-op` key that the control writes and reloads. Overflow at 390 px is 0 for all three operators, with operator-specific routes. The `rendered_strings.cjs` visibility skip is equivalent to the old 1 s timeout.
- `gen_docs.cjs` OE-6 and N-M2: the reverted text ("Design value: the replay has not yet been run on site data") appears only in `CHANGE-REGISTER.md`. `loop-site.js:71` only names the file, so it is never on screen. Main's committed register already has this exact text, and main's `gen_docs.cjs` had drifted from it. These are rows dated before 21 Nov, and K11 exempts them by hash, so restoring the committed history text is right.
- My plants (on a scratch copy; none in a worktree):
  - A. Website `Spend: 3,660` → `3,650` with its anchor kept: `FAIL anchored figure in ../../go-to-market/website-content.md: 3,650 … 3650 != 3660.0`.
  - B. A sensitivity line for MTO-INV-CLAIM (`−230.00<!--fig:…MTO-INV-CLAIM.sensitivities.diesel_minus_20pct-->`) added to `worked-portfolios.md`: `FAIL anchored figure in worked-portfolios.md: 230.00 -> … is independently computed`.
  - C. A reader of a removed field (`DOPT('KOB-STOPSOC').forward_replay.avoidable_fuel_l`) in `loop-decisions.js:185`: `render_text.cjs` reports 3 script errors (recommendation, alternatives, decision/kobo-generator) and exits 1.

  All three fail as they should.

### Not verified

- I did not run `run-audit.sh` on head itself. I read head's committed `audit-results.json` and ran the repaired audit on main for the comparison.
- I did not run the simulator world tests (`simulator/tests/world/`) beyond `test_records.py`.
- I did not rebuild the H9 ledger; that is commit 6.
- I did not render the drawers beyond `render_text`'s sample. Another reader of a manifest `reason` may exist in an unsampled drawer, so H1's sweep must be done from the source, not from the rendered sample.

### Residual risk the packet does not name

- The mock's word filter (`loop-core.js:372`, replay → simulation) hides manifest wording from `vocab_check`. So the guard sees the filtered text, and any manifest string that reaches the screen bypasses D-0K4.54's intent unless its reader is mapped. H1 is one instance of this.
- `naText()` chooses NA_KOBO or NA_KIS by matching "Kobo" or "Kisiwa" in the words. The next gap whose words name a site will take the wrong copy.

## Verification review (fresh Claude reviewer, 2026-11-22; head `b70dac25e`)

**Verdict: ACCEPT.** Every named finding is closed; no new finding.
- Checks at head, run by me: `check_manifest.py` 7798 passed, 0 failed (2869 history checks); `check_alignment.py` 114/114; `check_register_paths.py` 852 rows in §3.1, 835 resolve, 17 marked removed, 0 failed; `hand_typed_scan.py` ok; `render_text.cjs` 237 renders, 0 script errors; `vocab_check` 0 hits, and with `VOCAB_PLANT=1` the new code rule catches the planted `0K4f`, `queue Q7`, `dispatch-3.2` (3 hits). Cited from the builder, not rerun: `ia_gates` 52 runs 0 BAD; audit 207/207 ok, 0 console errors, `unresolved` empty, contrast 22/22 (committed `audit-results.json`).
- H1 closed: `NA_BY_ID` plus `naText` fallback strips bracketed remarks; every reader of an option `reason` goes through `optReason`. Rendered text has no "0K4"/"queue Q" string; the plan's "Left out" table reads "Not available yet: needs a simulation with a Kisiwa battery" and the Kobo admission line plus the Kobo words. `vocab_check.cjs:27` adds the slice/queue/dispatch rule and its plant.
- H2 closed: §3.1 re-resolved by the new `check_register_paths.py` (17 rows marked removed, 0 unresolved); the check is repeatable and exits non-zero on a dead path.
- M1 closed: no `ux-chip is-neutral` without `attn-k` remains in any source; the tile and the decision-page spots have a space before the chip.
- M2 closed: `browser-audit.md:18` and `:28` now say 71 drawers and 2 selectors were not checked.
- L1 closed: the two `admitted` placeholders are worded into the reason; `audit.mjs` exits 1 on unresolved placeholders. L2 closed: `.ux-chip.is-neutral` is in the contrast set. L4 closed: the Lakeside "Today" sentence is whole in the md (and its html twin). L3 skipped, optional.
- L5 and commit 6: I rebuilt the H9 ledger from `CHECK_LABELS` at head. It equals `h9-ledger-final.txt` except the one H9 meta label that appears now that H9 passes (+1, total 7798). Arithmetic: 4496 +50 (evaluator) -15 (stated) +2 (narratives) +9 (anchors) -9 (workflow) +0 (homes) = 4533 = `H9_BASELINE`. `replay_sources` (184) and `product_parity` (11) run after H9, as the comment says. K10 and `k10()` are gone with D-0K4.56 (owner-approved, index-rulings-23:46); H10 is `4cf82719a7a6` and passes.
- `run-audit.sh`: the `LD_LIBRARY_PATH` export now precedes `ia_gates.cjs` (Chromium in `count_check` needs libatk); logic otherwise unchanged. Correct.

Not verified: I did not rerun `run-audit.sh` or `ia_gates.cjs` in full, and the Docs-side `spec.md` M1 correction still says "pending Architect line". Residual: `naText`'s fallback strips only bracketed remarks, so a gap worded with unbracketed codes would reach the screen, but `vocab_check` now fails on it.
