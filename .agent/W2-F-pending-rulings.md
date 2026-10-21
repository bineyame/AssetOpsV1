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

## 4-q1 — M12 EV Scenarios slot held for W4-03 (OPEN, sequencing)

Unit 4's M12/S11/N4 (one literal `<UnavailableTab label="Scenarios" />` in EV Financials/Assumptions, the
`navigation-rail-fixtures.ps1` EvSiteViews fixture, and the guard's final `$expectedTabs`) is NOT built. The dispatch
forbids editing `tools/checks/navigation-truthfulness.ps1` and the unavailable-tab multiset until W4-03 merges, and the
build-spec amendment requires the guard change to be atomic with the tab (adding the tab alone fails the closed
multiset). Branch guard still reads the pre-W4-03 `$expectedTabs` (`Alternatives`, `Scenarios`, ...). Request: confirm
M12 lands as a separate unit-4b commit after W4-03 is on main (with `w2f_ev_scenarios_slot_unavailable`).
