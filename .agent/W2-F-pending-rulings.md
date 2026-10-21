# W2-F pending rulings

Questions for the Architect. Builders record; they do not decide.

## 1b-q1 — vocabulary glosses (RESOLVED)

Resolved by `.agent/W2-F-build-spec.md` "Copy rulings (q1)" and applied in W2-F commit 4a: only the exact
`Claim boundary` gloss kept; the `Ordered compressor running after the interruption` gloss reverted; the cooling
limitation (backend DTO and frontend) and the Evidence footer (refused, loaded, null-target) use the ruled plain copy;
the required assertions are added.

Commit `f3ccb41c` added exact-phrase glosses in `productVocabulary.json` for 'Claim boundary' and 'Ordered compressor running after the interruption', because the vocabulary guard forbids 'claim' and 'running'. The Architect must confirm the gloss, or give replacement copy that avoids system vocabulary.

Unit 2 addition (same item, no new gloss added): closure M3 mandates the refused Evidence footer
`Record-level detail and claim limits cannot be read for this window.`, which contains the W1 term `claim limits`.
Unit 2 renders it verbatim (`coldSiteViews.tsx`, `data-cold-evidence-footer="refused"`); no gloss or test exemption was
added. The current vocabulary tests do not scan the refused Evidence state, so nothing fails today. The Architect must
confirm this copy, or give replacement copy, together with the two 1b phrases.
