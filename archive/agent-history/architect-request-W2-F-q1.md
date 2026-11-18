# Architect request: W2-F 1b-q1 (copy blocked by the plain-language guard)

Read:
- `.agent/W2-F-build-spec.md`, all closures;
- `.agent/W2-F-pending-rulings.md`, 1b-q1;
- the vocabulary guard config: `productVocabulary.json` and the guard that enforces it (find them with grep);
- the owner rule in `.agent/owner-fidelity-and-design-ownership-2026-10-18.md` and memory: client screens use plain language and no system vocabulary.

Your W2-F rulings mandate copy containing guard-forbidden words. A builder added exact-phrase glosses to `productVocabulary.json` (commit `f3ccb41c`) for "Claim boundary" and "Ordered compressor running after the interruption". The refused Evidence footer copy also contains "claim limits".

Rule each phrase:
- either replacement plain-language copy that passes the guard without any gloss, keeping the v69 mock wording where the mock itself uses the phrase (check `screens.js`);
- or, if the mock literally shows the phrase, a justified gloss with its exact entry.

Say whether the `f3ccb41c` glosses are kept or reverted. Give the final literal strings and the test assertions.

Append the result as "Copy rulings (q1)" to `.agent/W2-F-build-spec.md`. Write nothing else. Do not commit.
