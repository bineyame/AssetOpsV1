# Architect request: W3-01 q4 (EV money pin conflicts with code)

You are the AssetOps Architect. Read:
- `.agent/W3-01-build-spec.md`, rulings q1–q3;
- `.agent/W3-01-pending-rulings.md`, q4: item 1 with options (a)–(d), and readings 2–6;
- `.agent/W3-01-phase-handoff.md`;
- `.agent/W3-01-lane-a-partial.patch`, which is Lane A's built-but-uncommitted work.

Branch `task/W3-01-estate-claim-action-roots` is at `7f566491`.

q3 assumed EV money rows have a pinned Finding revision. In the code, `ev_consequence_revision.finding_revision_id` is nullable, and its only writer always stores NULL (`backend/assetops_backend/financials/adapters/postgres_consequence_store.py:997-1000`). Verify this against the code and against W2-07's spec (`.agent/W2-07-build-spec.md`, and whether W2-07 intended a pin). Then rule item 1 with an exact replacement covering:
- the block's selected-ID set;
- the cited set;
- the null-pin behaviour;
- the test name and assertion.

If no rule can keep the read honest without a pin, say whether this needs a W2-07 producer fix and who owns it.

Confirm or replace readings 2–6. Also check the q3 map for any other nullable or never-written column assumption of the same kind, and close each one you find.

Append the result as "Run 4 rulings (q4)" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
