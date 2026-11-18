# Architect request: W3-01 q6 (estate core blocked) — final closure of W3-01

You are the AssetOps Architect. Read:
- `.agent/W3-01-build-spec.md`, including all rulings and amendments;
- `.agent/W3-01-pending-rulings.md` (q6: 2 blockers with options (a)–(d), and 7 readings);
- `.agent/W3-01-phase-handoff.md`;
- `.agent/W3-02-build-spec.md`, commits `0a`/`0b`;
- `.agent/W3-01-commit2-prereq-rereview.md` (one Low on reason text).

Branch `task/W3-01-estate-claim-action-roots` is at `55367000`.

1. Blocker 1. Cold reads match a run only by a covering window (`postgres_assessment_store.py:1728`), EV only by an exact one (`:2311`). Fixture runs are hour-scale, so a whole-day estate window selects nothing. Pick an option and give the exact read contract (function, predicate, tests). It must not change the merged cold/EV Site semantics unless you record that as an amendment.
2. Blocker 2. The mini-grid selected consequence, money eligibility and money source gate are W3-02 `0a`/`0b`. Pick an option: pull them forward with an exact contract and a W3-02 amendment, or rule an honest W3-01 limitation with its copy (Cost lens and consequence column).
3. Confirm or replace the 7 readings, and rule the Low.

This is the sixth question round on W3-01. Finish with a FULL implementer dry-read of every remaining W3-01 commit (estate core, Lane A integration, UI and captures) against the code now on the branch. Check every seam, read, window, enum and copy string, and answer every remaining question now.

Append the result as "Run 6 rulings (q6) and final dry-read" to `.agent/W3-01-build-spec.md`, plus any W3-02 amendment. Write nothing else. Do not commit.
