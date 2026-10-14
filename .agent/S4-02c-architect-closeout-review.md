# S4-02c Architect rulings and registry closeout review

Reviewer: fresh Claude reviewer (did not author the rulings, the registry edit or the report).
Reviewed: commit `56324b09` on `plan/S4-02c-architect` against its first parent `8d0c6edd`
(merge of main `68106bac` into the branch). Files: `.agent/architect-S4-02c-answers.md`,
`.agent/architect-S4-02c-log.txt`, `.agent/next-work-2026-10-14i.json`, `.ai/DECISIONS.md` (+2 lines),
`frontend/docs/architecture/v69-dependency-registry-pilot.json` (4 lines changed, 2 nodes added).
The working tree was clean when checked; uncommitted Planner edits, if any appeared later, were not reviewed.

## Verdict: ACCEPT with carries

The rulings answer every question in `.agent/architect-S4-02c-request.md` (Q1-Q3, R1, S4-02c acceptance),
match the S4-02c review's F1 facts and registry closeout notes, and are consistent with the prior decisions.
No money becomes silent: the new rule is strictly more conservative than `D-2026-10-14-s5-selected-window-overview`.
History is not rewritten: old `dispatch-3.1` revisions and the 7.5625 / 15.8125 USD consequences are explicitly
preserved. S4-02c acceptance is explicitly unchanged. The registry is well-formed, the checker passes, the report
verifies against current inputs, and the selection reproduces. The findings below are wording and handoff gaps,
none of which changes the selection or the safety rule. They are carries for the Planners of the two new nodes and
of S5-01, not reasons to return the commit.

## Checks (as observed)

| Check | Result |
|---|---|
| `git show HEAD --stat`, diff vs first parent | 5 files, as listed above. DECISIONS diff is only the appended entry (no edits to history). Registry diff: `real_pilot_requires`, `queue_baseline_nodes`, S4-02c node closeout, two new nodes, `I-site-overview-read.requires`. |
| `node frontend/docs/architecture/check_v69_dependency_registry.cjs` | exit 0; `Registry valid: 224 nodes, 11 linked pilot panels`. |
| `... --verify-report .agent/next-work-2026-10-14i.json` | exit 0 (fingerprints unchanged; the tool exits 3 on any input change). Decision line: select `I-analytic-finding-worker-schedule` 2.198 vs `I-action-store` 2.016, gap 0.083, tie-break with owner notice. |
| Gap arithmetic | (2.198 - 2.016) / 2.198 = 8.28%: inside 5-10%, so select with notice; not a <=5% owner contest. Third: `I-late-reading-series-and-money-limit` 1.998 (same reach, E=3 vs 1). |
| `.ai/DECISIONS.md` UTF-8 | working tree and `HEAD:` blob both decode as UTF-8. New lines are CRLF like their neighbours (the file already had 18 LF-only lines before this commit; not introduced here). |
| Node shapes | Both new nodes carry the same key set as the sibling follow-on `I-price-equal-start-succession` (`id, kind, layer, area, owner, status, requires, effort, evidence, task, acceptance_target`). Efforts M and S match the answers (Q3, R1). |
| `requires` | late-reading: `I-S2-02, I-S3-01, I-S4-01, I-S4-02b` (all resolved; matches Q3). worker-schedule: `I-S3-01, I-S4-01, I-evidence-acceptance-consequence-work` (all resolved after closeout; matches R1). Both are therefore eligible, as the report shows. |
| Gating | `I-site-overview-read.requires` adds both nodes; they are its only open prerequisites. Only `I-site-overview-read` requires either node (no stray dependants). S5-01 reaches them through `I-site-overview-ui -> I-site-overview-read`. |
| `queue_baseline_nodes` | Both new IDs appended before `I-stored-demo-provenance`; no other change. |
| Real-pilot gate | `real_pilot_requires` now lists `I-stored-demo-provenance`, `I-late-reading-series-and-money-limit`, `I-analytic-finding-worker-schedule`, matching the decision's "both also gate real-Site readiness". |
| S4-02c node closeout | `status: resolved`; every `../../../` path in its evidence resolves from `frontend/docs/architecture` (task file, plan review, plan fix re-review, phase 1/2 reviews, final review, packet, walkthrough, Architect answers), plus `0012_evidence_consequence_work.py`, `financials/recompute.py` (`ConsequenceRecomputeWorker` :216, `run` :294), `recompute_consequences.py` (`run` CLI), `tools/s402c_late_power_walkthrough.py`. `68106bac` is a commit contained in `main`. Cited verdicts match the files: plan review RETURN, fix re-review ACCEPT, phase 1, phase 2 and final review ACCEPT with carries; walkthrough 21 checks, two legs. Acceptance target text is unchanged. |
| Consistency with prior decisions | `D-2026-10-09-s2-simulated-publication-clock`: the ruling relies on its "no envelope or sequence until release" rule, correctly. `D-2026-10-14-s5-selected-window-overview`: S5 money remains only a CURRENT PRICED same-basis consequence, now with an added stricter gate; S4 currentness semantics untouched. `D-2026-10-14-s402-post-review-follow-ons`: enqueue rule and stored-demo-provenance real-pilot gate preserved. S3 dispatch decisions: change requires a new model version and reassessment with old revisions kept as history. |

Not run: `check-all` scan guards (no `node_modules` in this worktree, per dispatch), backend and frontend suites
(no code changed in this commit).

## Findings

### L1 (Low, handoff gap). The S5 withhold rule lives in a node that precedes the S5 read, and `I-site-overview-read` does not say it.
`frontend/docs/architecture/v69-dependency-registry-pilot.json`, `I-late-reading-series-and-money-limit`
acceptance_target ("S5 refuses a current amount when generator-series ambiguity affects the selected
Finding/window") and `I-site-overview-read` acceptance_target (unchanged: "returns assessment, Finding, bounded
consequence and source/analytic watermarks"). Answers Q2 assigns the withhold to "S5 `I-site-overview-read`/UI";
the registry puts it in the prerequisite node, where no S5 read exists yet to refuse anything. The decision text is
correct, so S5-01's Planner will find the rule in DECISIONS, but the node a Reviewer judges S5-01 against does not
state it. Why it matters: this is the no-silent-money rule; it should not depend on a Planner reading a prose
decision. Fix (carry, no re-review needed): either add to `I-site-overview-read`'s acceptance_target "withholds the
amount, with limitation and exact links, when generator-series ambiguity affects the selected Finding/window
(D-2026-10-14-s402c-late-sequence-and-s5-money)", or have the late-reading Planner define a concrete S3/S4-side
eligibility signal that S5-01 must consume, and name it in both nodes. Not an acceptance gap of this commit.

### L2 (Low, stale prose). `physical_peer_gate` still names only the stored-demo-provenance gate.
Registry line 5: "require resolved I-stored-demo-provenance before pilot activation", while `real_pilot_requires`
(line 6) now lists three nodes. A reader of the prose gate sees one prerequisite. The checker only tests that the
string contains "First real pilot", so this cannot fail a check. Fix: say "require every `real_pilot_requires`
node resolved before pilot activation" on the next registry edit.

### I1 (Info). The real-pilot gate is recorded more strictly than R1 states it.
Answers R1 gates the worker schedule before "a real-Site pilot that claims automatic late-evidence recovery";
the decision and registry make it unconditional. Stricter is the safe reading and matches the decision text. No
action unless the owner later wants a pilot without automatic late recovery, which would need an explicit ruling.

### I2 (Info). S4-02c packet residual items I1-I4 and the pre-0012 `NO_WORK_RECORDED` heads are not named in the closeout evidence.
The S4-02c review listed them under "Stays open". They are reachable through the cited packet
(`.agent/S4-02c-review-packet.md` lines 96-99), so nothing is lost, but no node owns them. See carry W2.

## Carries

For the Planner of `I-analytic-finding-worker-schedule` (selected next, S):
- W1. Decide and record deployment ownership and cadence per environment (answers R1), reusing an existing reliable
  timer if it meets the target; order is S3 `process-jobs` then S4 `match-findings` then the consequence runner, per
  active tenant/Site. State whether the one S4-02c consequence runner schedule is folded in or stays separate.
- W2. "Observable backlog and failure" should absorb S4-02c packet I1 (failing rows accumulate attempts without a
  terminal state or alert) and the repeated-`skipped`-tick hung-runner alarm, or explicitly leave them out with a
  named owner. Say what happens to pre-0012 `NO_WORK_RECORDED` heads (backfill or documented exclusion).
- W3. Prove "stopped workers leave S5 pending/stale, never silently current" with a test that does not need S5-01:
  the S5 read does not exist yet, so the proof must be at the projection inputs (job/work backlog visible and
  consequence not CURRENT while upstream work is pending), and S5-01 must carry the read-side half.
- W4. Late accepted evidence must reach a revised Finding and consequence with no manual Leg B commands: replay
  the S4-02c walkthrough Leg B without its hand-run `process-jobs`/`match-findings` steps.
- W5. Record the 8.28% ranking notice in `.agent/coordinator-handoff.md` as the report instructs.

For the Planner of `I-late-reading-series-and-money-limit` (M):
- L-a. Write the versioned source-time cohort rule as a reviewed contract before code: required source-time and
  clock attestation fields, overlap/duplicate/epoch/impossible-time refusals, and the named series limit when
  attestation is absent. If the rule needs choices the Q1 ruling does not settle, route them to the Architect
  rather than deciding them in the packet.
- L-b. New model version (not an edit of `dispatch-3.1`), reassessment of affected current windows, old revisions
  and exact links kept as history; the 7.5625 and 15.8125 USD consequences are not rewritten.
- L-c. Revised FindingRevision carries `GENERATOR_SERIES_AMBIGUOUS`/`SEQUENCE_ORDER_INVERTED` with an end reason
  naming the series refusal; `OPEN_BOUND` alone fails the run-1 regression.
- L-d. Resolve L1: define the money-eligibility signal S5-01 will consume and update `I-site-overview-read`'s
  acceptance target (or the S5-01 task) to carry the withhold state.
- L-e. Regression replays both run 1 (admission-sequenced delayed admission, via the Lab publication clock) and the
  on-time-sequenced late upload through ingestion and asserts assessment status, Finding limitations and end reason,
  consequence lineage and S5 eligibility; 7.5625 USD never becomes an unqualified current amount.
- L-f. A real gateway without validated source-time/clock semantics stays limited; keep that as a negative case.

For S5-01: its packet carries R1 and F1 explicitly (S4-02c review), the no-amount state is shown at the existing
owner visual checkpoint, and partial limited money from an indeterminate series is out of scope without a new
product decision.

## Residual risk not named in the commit

- Until `I-late-reading-series-and-money-limit` lands, any non-S5 surface that already reads a CURRENT PRICED
  consequence (S4-02b Finding money panel) can still show run 1's 7.5625 USD without a series limit. The ruling
  confines the gate to S5; the S4 Finding surface's exposure is not discussed. The Planner should check whether
  the S4 read shows that figure as current and, if so, whether the revised Finding limit (L-c) is enough.
- The selection tie-break rests on effort alone (same reach as the late-reading node); after the worker schedule
  lands the late-reading node becomes the sole S5-01 gate, so both are on the critical path regardless of order.
