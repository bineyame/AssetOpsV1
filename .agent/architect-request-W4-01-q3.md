# Architect request: W4-01 q3 (commit 3 blocked)

You are the AssetOps Architect. Read:
- `.agent/W4-01-build-spec.md`, all rulings;
- `.agent/W4-01-pending-rulings.md`: questions 6–10 and 6 readings;
- `.agent/W4-01-phase-handoff.md`;
- `.agent/W3-01-build-spec.md` "Run 6 rulings (q6)", Blocker 1.

Code: W4 is on branch `task/W4-01-work-case-core` at `d34d6441`.

Conflict. W4-01 commit 3's ruling extracts the cold/EV `_snapshot` helpers from `analytics/adapters/postgres_assessment_store.py`. Right now a Lane A W3-01 prerequisite run is adding the q6 estate-only, connection-taking cold/EV selection mode to that same file, on branch `task/W3-01-estate-claim-action-roots`. The two branches must not both reshape `_snapshot`.

Rule:
1. One owner and one shape for the connection-taking cold/EV snapshot API that serves both W4 link coverage and the W3 estate. Say which branch lands it, and how the other consumes it: cherry-pick of the reviewed commit, or merge order. Follow the ruling-1 pattern.
2. Questions 6–10, each with exact artifacts:
   - where the link-coverage and detail SQL live;
   - the detail `known_at` rules and refusal shape;
   - whether the list-refusal test moves to commit 4;
   - confirm that development has no SERVICE principal, and how dev and the fixture write.
3. Confirm or replace the 6 readings.

Append the result as "Run 3 rulings (q3)" to `.agent/W4-01-build-spec.md`, plus any matching note in `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
