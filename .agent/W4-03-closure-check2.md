# W4-03 closure check 2 (2026-10-20)
Main 7395f5c3 (Merge plan/W4-03-closure2). Read-only check of "Review closure 2" in .agent/W4-03-build-spec.md.

- Q1 CLOSED (create_app injection args, DecisionPrincipal, tools/w403_mini_decisions_walkthrough.py prepare|serve|replay|capture|drop, bearer is transport-only).
- Q4 CLOSED (worker scan, exact SQL, zero triggers/DDL, count stays 10).
- Q11/Q6 residue CLOSED (diff patches both lines, replacement test named, supersession entries added).
- Q24 CLOSED (literal $expectedTabs with Scenarios x2, Opportunities once in chips).
- N1 CLOSED (USD/kWh, KES/kWh; 'ISO4217/kWh' rejected; prefix vs currency 422).
- N2 CLOSED (registry file and five (screen_id,panel_index) keys named).

## Breadcrumb root point: OPEN, spec needs a rule
- W3-01 (step 1, a stated prerequisite of W4-03, "consumed after merge") replaces the global /findings element with the estate All page. So on W4-03 build, the global Findings root will exist on main. The spec ties the disabled text to "until a reviewed global index exists" but names no condition or target, so the implementer must decide.
- Needed rule, canonical Alternatives: once W3-01's /findings is on main, the `Findings` root is a link to `/findings` (the estate All page, no lens); the disabled text "Global Findings unavailable; open Site Findings." is used only if that route is not mounted. Test both states. Keep the Site suffix link and the Site Findings route unchanged.
- Opportunity: keep the root disabled even after W3-01. A typed opportunity is not a W1 Finding, the estate Opportunities lens is deferred, and the estate All page does not list opportunities, so a link would land on a page that does not contain the object. Current copy is right; state it is unconditional (not "until a reviewed global index exists") and add a test that it stays disabled with W3-01 merged.

## New questions
- N3: after the root links to /findings on the Alternatives breadcrumb, does it carry the estate window/known_at tokens (estate-selection/2) or the bare route? Rule: bare /findings, no window state is inferred from the Finding.
