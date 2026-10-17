# W1-F4 fix round 3 re-review (0c5cd6e0)

Verdict: ACCEPT

Checks run: vitest w1f4VerificationStructure + siteActionVerification: 2 files, 40 passed, 0 failed. `npx.cmd tsc --noEmit`: exit 0. Full suite (2020 passed) not rerun; cited from the implementer.

Prior findings
1. Medium (Success criterion cell contradiction): resolved. The cell reads "At least 25% lower" when the target_reduction metric was read or a plan was read (`plan !== null`); "Not available" when a plan id is known (current/shown) but no plan was read; null (no claim) when there is no plan. All three cases are correct, and no false negative claim remains.
2. Low (trial limit stated twice): resolved. The demonstration branch now replaces TrialNotice with one demonstration-specific note and the duplicate span in the chart note was removed. The limit appears once per panel (confirmed in the 1440 and 390 captures).
3. Low (packet claim): not re-litigated; no blocker.

Other checks
- New test (plan opened, no outcome, expects "At least 25% lower") would fail if the plan-read branch regressed to the old metric-only logic. Asserts were only added; none weakened; S6-02b fail-closed checks untouched (diff touches only the criterion cell, the trial note and one test).
- Captures s602b verification-guardrail at 1440 and 390: state line said once, one disclosure per panel, no raw IDs, no contradictions. At 390 the guardrail table's RESULT column is clipped at the right edge (table overflow), cosmetic and pre-existing, Low, non-blocking.

Findings: none High or Medium. Unverified: layout script not rerun, full suite not rerun.
