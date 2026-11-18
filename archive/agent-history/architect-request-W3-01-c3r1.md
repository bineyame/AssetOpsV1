# Architect request: W3-01 commit-3 review (r1)

Read:
- `.agent/W3-01-build-spec.md`, rulings q6 and q8–q13;
- `.agent/W3-01-commit3-review.md`, which has M1 and L1–L4;
- the v69 `actions` and `findings` mocks.

Code: branch `task/W3-01-estate-claim-action-roots` at `b59575c0`.

Rule with exact artifacts, so a Sonnet fixer decides nothing:
- L1. The Actions Site cell is not linked, unlike the mock, which makes it a user-visible mock mismatch. Give the exact href rule for each domain and its test.
- L2. While loading or refused, the date bar reads "latest (latest at read time)". Give the literal copy for each state.
- M1. Confirm the exact list of the roughly 15 rendered strings that need assertions. List each string and the test file it belongs in.
- L3 and L4: delete the dead `FindingsFrame`, and add the Actions-link assertion.

Append the result as "Commit-3 review r1 rulings" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
