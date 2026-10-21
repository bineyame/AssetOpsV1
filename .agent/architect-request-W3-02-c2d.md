# Architect request: W3-02 c2d (two Evidence wording gaps)

Read `.agent/W3-02-build-spec.md` (c2 to c2c and the commit-2 r1 rulings), the "commit-2 fix r1" notes in `git show e45f4219:.agent/W3-02-phase-handoff.md` on branch `task/W3-02-estate-evidence-money-basis`, and the v69 `globalevidence` mock.

Rule with literal copy:
1. EV roles have no reviewed plain words, so they show the fallback "Description not available". Give the literal plain-language words for every EV role that can appear, and where they live (`estateEvidenceWords.ts`).
2. Cold claims map to their row label, so two different claims share one label. Give distinct literal labels for each cold claim.

Append the result as "Commit-2 rulings (c2d)" to `.agent/W3-02-build-spec.md`. Write nothing else. Do not commit.
