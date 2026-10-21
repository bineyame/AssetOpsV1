# Architect request: W2-F closure (post-merge seam re-check)

You are the AssetOps Architect. Read:
- `.ai/ROLE_CONFIG.md`: "Mockup drives the design; implementers never decide";
- `tasks/W2-F-structural-fixes.md` and `.agent/W2-F-build-spec.md`;
- `.agent/W2-F-seam-recheck.md`: 24 items (2 Blocker, 12 Should, 10 Nit), plus the proposed split of unit 1 into 1a and 1b;
- `.agent/W2-structural-audit.md`;
- `.agent/W4-03-build-spec.md`, closures 4–5, for the navigation guard tab multiset.

Close all 24 with exact artifacts verified against main.
- B1 (H1). The stored cold chain keeps only the first compressor reading and the first probe, with no values (`cold.py:616-620`), so the "Full recovery" rule cannot see a later running record. Rule the honest source: either the exact read that supplies it, or the honest single-rule copy across the three screens that removes the contradiction without claiming data we lack.
- B2 (M8). `routes.sld` does not exist, and the diagram page takes only `?at=`. Rule the exact link: `at=window.to`, or another literal form.
- S11 (M12). W2-F adds a second unavailable Scenarios tab, while W4-03's final guard list has one. Name the merge order between W2-F and W4-03 and the exact final `$expectedTabs` multiset. Amend W4-03 closure 5 if needed.

Adopt the 1a/1b split, or give your own. Each commit must fit one builder run and have a "read only these sections" index.

Append the result as "Review closure (2026-10-21)" to `.agent/W2-F-build-spec.md`, plus any W4-03 amendment. Write nothing else. Do not commit.
