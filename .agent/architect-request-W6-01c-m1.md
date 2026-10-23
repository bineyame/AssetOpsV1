# Architect request: W6-01c review M1, L1, L2

You are the AssetOps Architect (Codex). Read the review with `MSYS_NO_PATHCONV=1 git show task/W6-01c-request-overview:.agent/W6-01c-review.md`, then the C1–C4 rulings in `.agent/W6-01-build-spec.md`, the mock-fidelity rules in `.ai/ROLE_CONFIG.md`, and the v69 `wr-overview` and `wr-record` mocks.

1. **M1.** Two styling choices differ from the mock. The builder labelled them, but no ruling covers them:
   - Lifecycle is no longer equal height to Work done, because of a §2 cap conflict;
   - `Recorded` uses a neutral badge where the mock's `Captured` is green.
   Prefer RESTORE TO MOCK, with literal CSS or markup, and resolve the cap conflict, for example by adjusting the cap from the mock's measurement. KEEP either one only with a `MOCK DEVIATION` label, the reason and the alternatives.
2. **L1.** Correct the CREATED-check sentence in the spec: the shared reducer throws before it returns, so `global_detail.py` catches the error and checks in the same snapshot.
3. **L2.** Change the ruled tab-list `<div>` to `<ol className="site-tabs__list">`, because the unavailable tabs render `li`.

Append "W6-01c review rulings (M1, L1, L2)" to `.agent/W6-01-build-spec.md`. Write nothing else. Do not commit. End your output with one line per item, saying whether code must change.
