# Architect request: W4-03 PR-12 (9b capture failures) and closeout (u9b)

Read:
- `.agent/W4-03-build-spec.md`, through u9;
- `.agent/W4-03-pending-rulings.md`, PR-12;
- the eight 9b readings in `git show 68982c19:.agent/W4-03-phase-handoff.md`;
- the v69 mocks for Scenarios, Opportunity, Incidents and Alternatives.

Code: head `68982c19` on `task/W4-03-mini-decisions-work`.

25 of 265 capture checks fail. Panel set and order match the mock wherever a state could be produced. For each failure, give the exact fix (CSS or layout literal, a content change matching the mock, fixture or replay steps, or a cap amendment justified by the mock) and the test:

1. **Scenarios panel over its height cap.** It measures 645/436 against caps of 348/391, because each row lists five full revision IDs. The empty state is 450/490.
2. **Opportunity cards over their cap.** They measure 162 against 137 at 1440, and up to 350 against 273 at 390.
3. **Incidents at 390 over its cap.** It measures 482, and 571 with the refused overlay, against 460.
4. **Alternatives not capturable.** KOBO-001 returns 503, because the worktree's `var/sites/kobo-001.yaml` differs from what was imported. The KOBO Finding read is closed, because the replay runs the Performance comparison only for MG-W402-001. Give the exact walkthrough or replay steps.
5. **Opportunity supported/current not producible.** It does not appear at any cutoff after the replay. Give the exact fixture or replay path to produce it honestly.
6. **The detail route has no `known_at`.** The `k_before_late` capture works only because the script adds `known_at` to the detail request. Should the detail route accept `known_at`? If so, give the wire; if not, give the capture path.

Confirm or replace each of the eight 9b readings.

u9 calls 9b the last build unit. State exactly what units 10–12 now contain (packet, final review, closeout), so nothing is open.

Append the result as "Unit-9b rulings (u9b)" to `.agent/W4-03-build-spec.md`. Write nothing else. Do not commit.
