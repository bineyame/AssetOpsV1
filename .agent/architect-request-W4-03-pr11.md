# Architect request: W4-03 PR-11, the unit-9a readings and the 9b–12 open items (u9)

Read:
- `.agent/W4-03-build-spec.md`, through u8;
- `.agent/W4-03-pending-rulings.md`, PR-11;
- the unit-9a readings 1–6 and the 9b list in `git show 1801ed13:.agent/W4-03-phase-handoff.md`;
- `frontend/docs/architecture/v69-dependency-registry*` and the existing W4-02 registry entries, for format.

Code: `37122434` (9a: the fixture `w403-mini-decisions.json`, `tools/w403_mini_decisions_walkthrough.py` and the replay test) and `6915ae31` (u8).

Rule with literals and tests:
1. **PR-11.**
   - The KOBO Alternative POST at wall-clock time gets 409, because the F02 fixture times (29 Oct) are later than DB time. Give the exact fix (fixture clock or pinned now), or confirm it and say how the walkthrough performs the POST.
   - The late branch reads STALE_SOURCE, not PENDING_RECOMPUTE. Confirm this, or give the fixture change.
   - The missing-day branch uses a second reconcile window. Confirm.
2. **Readings.** Confirm or replace each of the six 9a readings.
3. **9b registry.** Does "five entries" include the Opportunity page's three panels? List the exact registry entries (screen IDs, panel IDs, order) and the panel tests.
4. **9b–12 open items.** Dry-read 9b–12 against the code at `1801ed13` for anything a builder would still have to choose:
   - capture states and viewports;
   - height caps;
   - packet contents;
   - the unit-12 closeout.

   Give literals.

Append the result as "Unit-9 rulings (u9)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
