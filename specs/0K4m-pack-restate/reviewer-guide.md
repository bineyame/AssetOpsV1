# 0K4m reviewer guide

Architect (Claude), 2026-11-21, rev 2 (handshake answered, `handshake.md`). Discovery review (W5): new evaluator
semantics and money figures. Read `spec.md` (rev 2), then D-0K4.9, D-0K4.11, D-0K4.13 and D-0K4.27 to D-0K4.29 in
`specs/0K4-dispatch-model-review/rulings.md` and D-0K4.31 to D-0K4.39 in `specs/0K4-dispatch-model-review/rulings-2.md`,
then the diff and `/opt/assetecon/evidence/0K4m/`. **Done** means every
question in spec §5 is answered yes with evidence, every plant in §6 fails its named check, and the sweep is complete.
Review units 1-2 together. Review unit 3 on its own, after units 1-2.

## What to check, and how

1. **Checker first, and independent (W2).**
   - Commit 1a must touch only `check_manifest.py` and print main's count line. Commit 1b must touch only
     `extract_replay_studies.py`, `replay-studies.json`, `independent_model.py` and `check_manifest.py`, and must fail
     on the unrestated manifest.
   - `independent_model.py` and `evaluate_structure.py` must share no helper or list, and no expected figure. Compare
     the two N1 implementations side by side. A shared import or a copied block is High.
2. **The extract is the study.**
   - Run `python3 extract_replay_studies.py --kobo /opt/assetecon/evidence/0K4d/kobo-61d/study.json --mto
     /opt/assetecon/evidence/0K4d/mto-61d/study.json --check`.
   - Pick three fields by hand (KOB-STOPSOC `avoided_l`, MTO-HULLER `litres_per_customer_kwh`, KOB-RESERVE
     `dawn_days_below`), read each in `study.json` yourself, and compare it with the manifest's value rounded per N2.
3. **The world is untouched (D-0K4.35).**
   - Rerun the boundary proof (spec §0 item 3) at every commit: (a) the view hash equals the pre-flight hash;
     (b) `world_history.py check` exits 0; (c) no changed line of the manifest, comment lines included, maps to
     `period.plan`, `period.actual`, `period.coverage` or a TOP, TENANT or SITE key the view copies (`view.py:17-20`).
     Lines under `period:` outside those three (bridge rows, `variance`) are expected.
     (rev 3, D-0K4.40) A comment line in no root entry's span maps to `<root>` and is allowed; P20 and P21 show
     the class is scoped.
   - `VIEW_HELD` lists exactly the four view paths in spec §1.2, K1 exempts only its string entry, and K11's skip of
     the `MANIFEST` literal is guarded by its equality check.
   - Run the simulator world tests (`simulator/tests/world/`) through the slot pool. Any failure is High.
4. **Every number is one of four kinds.** Walk the manifest diff place by place against spec §2.3. Each changed number
   should be one of:
   - a declared fact;
   - a `source:` value;
   - `unavailable(...)` words;
   - the admission line or `information`.
   A typed money figure left on a replay option is High.
5. **Money by hand.**
   - KOB-STOPSOC and KOB-RESERVE: `value` null with their words, never chosen, and no K8 amount (`scaled_to_30_days.*`)
     read by any `changes` expression (K12; spec §1.3).
   - Recompute MTO-HULLER's monthly change by hand: `litres_per_kwh x 1,650 kWh x price`, revenue, collection, one-off.
   - Compare both with `derived-values.json`. Reproduce one Lakeside plan figure from the option values. Do not check
     against any figure in this guide or the spec: there is none (figures are outputs).
6. **Not available, not zero (R4).**
   - Kobo's `candidate_l` and `necessary_l` are `null` with their words on the October side and the history months.
     Kobo's contribution, variance and `GENERATOR_RUNNING` row still evaluate, and the fuel group still adds to its line.
   - KIS-BATT60 has `value: null` and `not_available`, is never chosen, and is listed under the plan's `not_available`.
   - Each null is a present key, never an absent one (P16), and `unavailable("x") | 0` is not 0 (P17).
   - `missing-records.json` holds the `MODEL_PENDING` entries, each naming slice `0K4f` (rev 3, D-0K4.44).
7. **H9 is earned, not set.**
   - Read the ledger from 4502 and add it up. Run commit 1a's `check_manifest.py` with `CHECK_LABELS` on main's
     manifest and the branch's on the branch, and take the per-section multiset diff: each added or removed check is
     in the ledger.
   - H11 passes with the digest unchanged.
   - (rev 3, D-0K4.43) Commit 2 fails only in `anchors()`, `documents()` and K11 on files units 2 and 3 restate;
     `0 failed` and `H9_BASELINE` are judged at the branch head (commit 6). The branch merges once, held for the owner.
   - (rev 3, D-0K4.41, D-0K4.42) Read N5 and N6 in each model against the spec text, not against each other: candidacy
     never depends on `money_changes`; params at six places, money at cents from the unrounded value.
8. **Plants.** Read the builder's plant evidence (§6). Make two plants of your own on a scratch copy, never in the
   worktree:
   - N1 propagation broken in the evaluator, so that a node reading a not-available factor yields 0;
   - one `{fig:}` anchor in `domain-and-decision-models.md` pointing at the wrong path.
   Both must fail.
9. **The sweep (W6).** Re-run spec §3's three regexes yourself, and check each remaining hit against the packet's list.
   An unlisted hit is Medium. A design value in a current document is High.
10. **The mock (unit 3).**
   - Rebuild with the README commands, and check that `fixtures.js` is regenerated byte-equal.
   - `vocab_check`, `copy_check`, `hand_typed_scan.py` (exit 0) and `run-audit.sh` pass.
   - Look at the Kobo, Mto, Embakasi and Kisiwa option cards, the overview tile and one drawer. The chip reads
     Simulated, each gap names its record, the dawn reads as information, and there is no "†" and no
     "Design estimate".
   - Check the copy against spec §4 word for word, and the layout against the mock before the change (no element moved
     or lost; D4 content only).
11. **Packet.**
    - The figures are the evaluator's, and the reconciliation table is the only two-figure table.
    - The mid-build question count is recorded.
    - Nothing cites the night table. Where a per-step figure appears, its unit is kWh per 5-minute step.

## Severity

High: an edit inside the world view; shared checker and evaluator logic; a design value or "Design estimate" left on a
current page; a figure with no source; H9 set without a ledger that sums. Medium: an unlisted sweep hit; a missing
`{fig:}` anchor on an evaluated figure; a plant that does not fail. Low: wording, ordering.
