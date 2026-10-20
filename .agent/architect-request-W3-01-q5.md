# Architect request: W3-01 q5 (commit 2 blocked)

You are the AssetOps Architect. Read:
- `.agent/W3-01-build-spec.md`, including all rulings and amendments;
- `.agent/W3-01-pending-rulings.md` (q5: 3 questions plus readings 4–9);
- `.agent/W3-01-lane-a-requests.md`;
- `.agent/post-W2-sequence.md` (ownership);
- `.agent/W3-02-build-spec.md`, commit `0a` and the `select_dispatch_days_on` details.

Lane A is currently building W4-01 commit 2 in another worktree, on `task/W4-01-work-case-core`.

Rule with exact artifacts:
1. Who adds the connection-taking W1 read variants, and when: the Finding index, the S3 day selection and the Action window. Give exact function signatures and files. If Lane A owns them, give the sequential handoff order on the W3-01 branch, the way ruling 1 did, so neither lane edits concurrently. Say whether moving them to Lane B for this one commit is cleaner.
2. The mini-grid `known_at` cutoff. Either pull W3-02 `0a`'s `select_dispatch_days_on` forward into W3-01, with its exact contract and test and an amendment to W3-02, or rule the honest limitation for W3-01.
3. The `$pgReaders` guard allowance: the exact line, and who adds it when.

Confirm or replace readings 4–9.

Append the result as "Run 5 rulings (q5)" to `.agent/W3-01-build-spec.md`, plus a W3-02 amendment if one is needed. Write nothing else. Do not commit.
