# G-activation fresh Claude review (2026-10-13)

Produced by a fresh Claude reviewer on `planning/G-01-activation-rule` (eb084eb vs main).

Verdict: ACCEPT. Ready to merge. No blocking findings.

## Checks run
- check_v69_dependency_registry.cjs: pass (exit 0).
- test_delivery_next_work.cjs (node --test): 33/33 pass.
- tools/check-all.ps1 -Python python: all 6 guards passed.
- next-work + verify-report to scratch: status ranked, V-01b selected (2.47 vs A-S4-financial 2.215, gap 0.103). Candidates and decision are byte-identical to .agent/next-work-gap-planning.json. Only the registry and queue fingerprints differ, as expected because registry outside_ranking and tasks/README changed.

## Code review
- delivery_next_work.cjs adds only a read-only `unscored_work` list built from plan.outside_ranking entries matching I-G-01..05. It sits on the report object before the refusal branch, so it appears in ranked and refused reports. It never touches candidate construction, scoring, K, the contest logic or the single-active stop. Confirmed by diff and by identical scores.
- The new test is discriminating. Without the change, `unscored_work` is undefined and the deepEqual fails. It also asserts decision, eligible, candidate id/score pairs and absence of a candidate I-G-01, so a leak into ranking would fail.
- open_prerequisites show I-G-01 for G-02 and I-G-02 for G-03..05, which fits the ordering.
- F3 fixture (catalogue present => decision/scores unchanged) is required in G-01 acceptance. It is not yet implemented, correctly, since the catalogue does not exist yet.
- COORDINATOR_LOOP, README, DECISIONS (D-2026-10-13-g-gap-packet-activation), registry outside_ranking reasons, and G-01/G-02/G-03 edits (F2 gap_enrolled_screens, F4 round-3 addendum, F5 V-01b merge) are consistent with the answers file and the owner confirmation. Ranking stays deferred to W1 exit. Rule: G-01 after V-01b merge and stops clear, G-02 after merged G-01, G-03 after merged V-01b.

## Findings (all carry, non-blocking)
1. Activation order is coordinator-enforced text, not machine-enforced. The checker lists G packets but does not know whether V-01b has merged. Residual risk is a coordinator skipping the rule. Acceptable given the single-active protocol.
2. `unscored_work` regex `/^I-G-0[1-5]$/` is hard-coded, so a later I-G-06 would silently not appear. Carry: widen to /^I-G-\d+$/ when a G-06 is added.
3. G-03's "V-01b merged" prerequisite is not represented in open_prerequisites (only I-G-02 shown). Carry: coordinator must verify V-01b merge manually, as the rule says.
4. The new test covers only the ranked path, not the refused path. Not verified for the text (non-JSON) report output, and unscored_work was observed only in JSON.
