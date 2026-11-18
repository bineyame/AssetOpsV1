# W4-03 closure 4 check (main 449e48e1, read-only)

Verdict: 34 of 35 CLOSED, 1 OPEN (B4, minor). 1 new question.

## Spot checks against main (all match the spec's claims)
- B1: `w4-mini-depth-cases-v1.json` site_code MG-W402-001; `mg-w402-001.yaml` MG-only; `w401-work.json` KOBO site_codes. Fixture/site split is consistent.
- B2: `create_app` (main.py:177) has no work principal parameter; `build_work_router` mounted at main.py:491 with the default principal. Ruling (in-process WorkService seed plus separate `mini_decision_*` injection) is implementable.
- B3: both literals exist exactly as cited (postgres_finding_store.py:112-115, postgres_evidence_ledger.py:810-818); adding `mini_opportunity` is a one-token edit.
- B4: guard literal today is `Alternatives, Scenarios, Cooling, Recommendation x2, Availability, Energy / site power` (navigation-truthfulness.ps1:742-749); only one UnavailableTab Scenarios (SiteAnalyticsFrames.tsx:746).
- B5: screens.js:948 Overview-only for opportunity-finding; :959 six-tab mini row; :969 F-109 / F-104. Matches.

## Items
B1 CLOSED. B2 CLOSED. B3 CLOSED. B5 CLOSED.
B4 OPEN: new literal drops `Alternatives`, but S12 leaves cold/EV Finding child views in the shared frame; the current "Alternatives" unavailable slot is rendered dynamically (SiteFindingEvidence.tsx:80 / SiteAnalyticsFrames.tsx ~612 `unavailable: true`). Spec does not say whether cold/EV keep an unavailable Alternatives slot (then the literal keeps `Alternatives`, and Analysis exists only if the dynamic owner counts it) or drop it. A builder must guess the multiset.
S1-S10 CLOSED. S11-S21 CLOSED (S11, S12 and S13 depend on the B4 answer only for the guard literal).
N1-N9 CLOSED.

## Split index
All 12 units (1, 2a, 2b, 3, 4, 5, 6a, 6b, 7, 8, 9a, 9b) have a "Read only these sections/files" column citing named original sections, closure 1/2/3 paragraph groups and closure 4 B/S/N ids plus files. Usable. Weak spots: references like "closure 1 Q1-Q3" and "Original API/error table" are by name, not line number, so the builder must locate them (spec lines 1-420); not a decision gap. Note unit 6b and 6a both touch SiteAnalyticsFrames.tsx and the guard; 6a lands first.

## New question
Q-new-1 (B4): after W4-03, do cold and EV Finding child views still show an unavailable `Alternatives` slot, and which source file counts toward the guard multiset? Architect to state the final `$expectedTabs` including Alternatives and Analysis counts.
