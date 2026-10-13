# S4-03 registry closeout review

Reviewer: a fresh Claude reviewer who did not write this change. Branch `closeout/S4-03-registry` @ e872714, against main a32d4bb. The diff is `e5492b2` (S4-03 closeout) plus `e872714` (I-G-01 resolution and the regenerated report). It is metadata only: 4 files, and no product code, tests or fixtures changed.

## Verdict: ACCEPT. No blocking findings. Four low-severity carries.

## Verified
- **Structural diff of the registry.** I compared the registry JSON key by key against a32d4bb, not only as text. The only changes are these:
  - Six nodes moved from open to resolved and gained evidence: `I-S4-03`, `I-finding-evidence-read`, `I-finding-evidence-ui`, `I-finding-history-read`, `I-finding-history-ui` and `I-G-01`.
  - Two `acceptance_target` texts were reworded: `I-S4-03` and `I-finding-history-read`.
  - Three claim portions moved from `open` to `delivered`, with `delivered_by ["I-S4-03"]`, evidence and anchors: `finding-evidence:1#a`, `finding-evidence:2#a` and `finding-history:1#a`.
  - Three panels moved from `gap` to `partial`.
  - One boundary was reworded: `finding-history:1#a`.
  - Two gap `review_trigger` texts were rewritten.

  Nothing else moved. No `core`, `variant`, `technical_requires`, `reviewed_mapping`, `mapping_review`, W1 core gate, scoring parameter or product (`P-*`) node changed. Nothing was marked Real.
- **Only the proven core portions are delivered.** Each of the three panels has exactly one claim portion (`#a`), and all three remain `partial`. Coverage and Use stay open as `G-finding-evidence-coverage` and `-use`, and the G-04 content (ActionEvent, Alternatives, Recommendation and the illustrative device rows) is named as remaining.
- **Evidence and anchors.** All 17 cited evidence files exist and are tracked. These include:
  - the task files;
  - the S4-03 plan, phase 1, 2 and 3 reviews and the fix re-reviews;
  - the packet;
  - Architect answers 1 and 2;
  - both owner records;
  - the G-01 review, re-review, packet and answers.

  Both decision IDs are in `.ai/DECISIONS.md` (lines 4095 and 4097). Commits 6ac76f3, c4ea8f4, 3dc9806, 65cc5c7, 66d001f and d9eb9ca are ancestors of HEAD with matching subjects. The anchors resolve:
  - `SiteFindingEvidence.tsx`: `:325` Lineage, `:383` Bundle, `:458` InputsByMeasurement, `:520` Assessments, `:606` Records and `:704` RecordLineage.
  - `SiteFindingHistory.tsx`: `:238` Versions and `:295` VersionRow.
  - `finding_api.py:142-209` contains the helpers plus the `/evidence` and `/history` routes, up to `return router`.
  - `finding_read.py` contains `evidence()` (line 446) and `history()` (line 557).
- **Knowledge-cutoff rewording.** The three new texts match the packet's proposal table (`S4-03-review-packet.md:98-104`) word for word. They agree with D-2026-10-11 (no knowledge_at replay) and with the S4-03 decision ("no arbitrary window or knowledge-at replay"). No "knowledge cutoff" text is left in the registry or the ledger.

  On the reviewed mapping: the `finding-history:1#a` boundary changed while `reviewed_mapping: true` and its `mapping_review` record, which points to the earlier W1 mapping review, were kept. The edit narrows the claim: it removes a replay promise that was never built. It does not widen the claim, and it is backed by both decisions. I accept it, with carry 1.
- **Gap review_trigger corrections.** Both texts now say that the by-role aggregate (`provenance.cited_evidence_by_role`) already exists and cannot close the gap. Each gap needs its own reviewed source, read and UI contract: per-input coverage for one, analytic use for the other. Both cite Architect Q4. This matches the Architect's ruling in `architect-S4-03-answers-2.md`. Both gaps stay open.
- **Ledger rows.**
  - `finding-history`: coverage changed from deferred to bounded, task is `S4-03`, `follow_on` is null and `to_candidate` is null. The null `to_candidate` is correct. `check_v69_ledger.py:121-133` requires a full candidate gate only while coverage is `deferred`, and raises "S-task screen should have null candidate gate" for any other coverage. `to_real.unresolved_panels` keeps "Revision history", as `panel_gaps` requires.
  - `finding-evidence`: the claim, interaction and caveat were updated, and the gap IDs are kept.
  - The claim, interaction and empty-state texts for both rows match the packet's ledger proposal. The appended caveats say "accepted conditionally ... named gaps stay open", which matches the owner record.
- **The owner record is not overstated.** The owner said "S4-03 walkthrough passed, accepted conditionally". Every citation says CONDITIONAL, and all panels stay partial. For G-01, the owner said "G-01 walkthrough passed, accepted conditionally", and the I-G-01 evidence says CONDITIONAL too. Its other claims check out: merged at d9eb9ca; G-01-review is RETURN and G-01-fix-rereview is ACCEPT; `G-01-review-packet.md:94-96` records "113/113 claims passed". The acceptance target "no W1 scoring change" also holds, because I-G-01 is unscored.
- **Scoring.** I compared every candidate in `next-work-2026-10-13b.json` (the last ranked report) with the same candidate in `-13e`. The only candidates that changed are the five S4-03 nodes, which now leave the list as resolved; each had scored 2.187. Every other score and every blocked flag is unchanged, A-S5-overview included at 2.144. A-S5-overview is now second only because `I-finding-evidence-read` and `I-finding-history-read`, which were second and third, are resolved. So the change is explained by the S4-03 closeout alone. The I-G-01 commit changes nothing except `unscored_work`, plus the registry fingerprint.

## Checks run (actual)
- `node frontend/docs/architecture/check_v69_dependency_registry.cjs`: exit 0.
- `python frontend/docs/architecture/check_v69_ledger.py`: "v6.9 ledger valid: 110 screens, 88 distinct models, 258 panels".
- `node frontend/docs/architecture/test_delivery_next_work.cjs`: 35 tests, 35 passed, 0 failed.
- `powershell -ExecutionPolicy Bypass -File tools/check-all.ps1`: "All 9 guards passed".
- `--verify-report .agent/next-work-2026-10-13e.json`: exit 0.
- I regenerated the report with `--next-work` into scratch. Every top-level key equals the committed report.
  - Decision: stop_owner, A-S4-financial 2.215 against A-S5-overview 2.144, gap 0.032 (3.21%, within the 5% limit). The tie-break recommends A-S5-overview.
  - In `unscored_work`, I-G-01 is resolved and I-G-02 has no open prerequisites.

## Carries (low, non-blocking)
1. **The reviewed-mapping edit has no provenance note.** At `finding-history:1`, `mapping_review` still cites only the earlier W1 mapping review, while the boundary text was changed at this closeout. At the next registry touch, add a note naming the S4-03 packet (C1), D-2026-10-11 and this review as the authority for the narrowed boundary.
2. **The closeout packet is stale after e872714.** `S4-03-closeout-packet.md`, in its Checks section, still says "I-G-01 (packet phase done, node still open)" and that I-G-02 has "open prerequisite I-G-01". The regenerated report now says resolved and has no prerequisites. The report is the authority; update the packet if it is touched again.
3. **Portion evidence is narrower than the node evidence.**
   - The portion evidence for `finding-evidence:1#a` and `:2#a` cites only the phase-3 review. The Evidence view was mainly reviewed in phase 2 and its fix re-review, and those appear only in the node evidence.
   - The commit list omits fix commits bc9a602, 91dea16 and 6dd7823. The merge a32d4bb covers them.

   This is completeness only.
4. **Some things are left unchanged that could be tidied.**
   - The `finding-evidence` ledger `to_real.remaining_work` still has its pre-S4-03 wording, "Populate each evidence bundle section ...". It could name the Coverage, Use and G-04 remainder, as `finding-history` now does.
   - Resolving I-G-01 inside the S4-03 closeout branch mixes two closeouts. It is correct and verified here, but noted for traceability.

## Not verified
I did not run the backend pytest suite, the frontend vitest suite or the build, because no code changed. I did not recompute the scoring formula by hand. Instead I relied on regenerating the report, on `--verify-report`, and on the candidate-by-candidate comparison with the 13b report.
