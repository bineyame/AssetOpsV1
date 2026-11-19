# CH-5a: split map

`.agent/build-sheet-CH-5a.md` (79 KB, 691 lines, sha256 `6e0c4c12a11cec90`) moved here on 2026-11-18 (declutter step 4) and was split by its own headings, verbatim and in order, into `spec.md` 36 KB, `rulings.md` 43 KB. Open the part a citation names; an old `file:line` citation maps through the table (old lines -> part lines). Proof: `python tools/declutter/split_specs.py --verify`.

| # | Old lines | Part | Part lines | Section |
| --- | --- | --- | --- | --- |
| 1 | 1-11 | `spec.md` | 1-11 | Build sheet CH-5a: ChainReader, the chain endpoints and the single ... |
| 2 | 12-26 | `rulings.md` | 1-15 | Why it is split (sizing ruling, CH5a-R S1) |
| 3 | 27-32 | `spec.md` | 12-17 | Part A — CH-5a1: ChainReader and the board read path (lane 1, 6 units) |
| 4 | 33-45 | `spec.md` | 18-30 | A0. Result and boundary |
| 5 | 46-58 | `rulings.md` | 16-28 | A1. Rulings (CH5a-R) |
| 6 | 59-70 | `spec.md` | 31-42 | A2. Module layout |
| 7 | 71-109 | `spec.md` | 43-81 | A3. ChainReader ports (each one indexed query, memoised per request) |
| 8 | 110-126 | `spec.md` | 82-98 | A4. The board inputs, field by field (mini `compose`, `B/site_outco... |
| 9 | 127-132 | `spec.md` | 99-104 | A5. Deletions and moves in this slice |
| 10 | 133-152 | `spec.md` | 105-124 | A6. Acceptance: the A/B diff and its allowed changes |
| 11 | 153-163 | `spec.md` | 125-135 | A7. Performance (EX-3: report, never relax) |
| 12 | 164-178 | `rulings.md` | 29-43 | A8. DS-R1 and OL-1 |
| 13 | 179-225 | `spec.md` | 136-182 | A9. Localised test ladder |
| 14 | 226-240 | `rulings.md` | 44-58 | A10. Pre-flight items (answer from code and the clone, batch them, ... |
| 15 | 241-247 | `spec.md` | 183-189 | A11. Review focus |
| 16 | 248-285 | `rulings.md` | 59-96 | A12. Pre-flight rulings (CH5a1-R, Architect: Claude, 2026-11-04) |
| 17 | 286-292 | `spec.md` | 190-196 | Part B — CH-5a2: chain endpoints, refs, routeFor and the carried ch... |
| 18 | 293-310 | `spec.md` | 197-214 | B0. Result and boundary |
| 19 | 311-354 | `spec.md` | 215-258 | B1. The contract (`outcome-chain-1`, additive; frontend parsers acc... |
| 20 | 355-367 | `spec.md` | 259-271 | B2. Refs on the legacy bodies and routeFor on the client |
| 21 | 368-377 | `spec.md` | 272-281 | B3. The board off the estate snapshot; old joins removed |
| 22 | 378-389 | `spec.md` | 282-293 | B4. Structured `thread_lines` (replacing copy-only lines) |
| 23 | 390-400 | `spec.md` | 294-304 | B5. Lens from the chain (I-21, COH-5) |
| 24 | 401-406 | `spec.md` | 305-310 | B6. Progress rows from threads (COH-8 / I-01) |
| 25 | 407-413 | `rulings.md` | 97-103 | B7. "Verified on example data" from provenance (DS-R1; COH-12) |
| 26 | 414-421 | `spec.md` | 311-318 | B8. Structural AST guard (design §13) |
| 27 | 422-434 | `rulings.md` | 104-116 | B9. DS-R1 and OL-1 |
| 28 | 435-472 | `spec.md` | 319-356 | B10. Localised test ladder |
| 29 | 473-480 | `rulings.md` | 117-124 | B11. Pre-flight items (answer from code, batch them, then stop) |
| 30 | 481-487 | `spec.md` | 357-363 | B12. Review focus |
| 31 | 488-508 | `rulings.md` | 125-145 | A13. Build rulings CH5a1-R2 (Architect 6, Claude, 2026-11-04; packe... |
| 32 | 509-521 | `rulings.md` | 146-158 | A14. Review-time rulings CH5a1-R3 (Architect 6, Claude, 2026-11-04) |
| 33 | 522-630 | `rulings.md` | 159-267 | B13. Pre-flight rulings CH5a2-R (Architect 7, Claude, 2026-11-04; p... |
| 34 | 631-652 | `rulings.md` | 268-289 | B14. Pre-flight rulings CH5a2b-R (Architect 8, Claude, 2026-11-05; ... |
| 35 | 653-691 | `rulings.md` | 290-328 | B15. Review-time ruling CH5a2b-R2 (Architect 9, Claude, 2026-11-05;... |
