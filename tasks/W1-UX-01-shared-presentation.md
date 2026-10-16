# W1-UX-01 — shared product presentation

Status: implementation-ready. Branch `task/W1-UX-01` from merged W1 UI baseline. Frontend only. This slice precedes W1-UX-02–05. Read [umbrella](W1-UX-mockup-fidelity.md), owner notes named there, `frontend/mockups/v69/index.html`, screen manifest and current `frontend/src/test/productVocabulary.ts` / `.json`. USER_REVIEW_REQUIRED: one combined W1 walkthrough after all slices; independent slice review is the merge gate.

## Result and contract

Build one shared `ProductStatus`/`ProductLimitation` presentation map, `DigDeeper` disclosure and `HeadlineVisualCard` (names are suggestions) in `frontend/src/ui/`. Components accept semantic **already-read** state and explicit evidence, never derive currentness, outcome, amount, zero, completeness or source health. Use the mock's hierarchy: one answer headline, one small visual (timeline, comparison, status bar or causal steps), then “What this means / What to do”; show scope and limit near the headline. Empty/unknown remain visible first-class states. Accessible labels, textual graphic equivalents, native keyboard disclosure, 390 px no overflow. Exact record IDs, raw enums, rule IDs, model versions, digests and decision basis belong in a closed disclosure labelled “How this was worked out”; exact source/user-owned names in the default reading are permitted only where their identity is the subject, never as unexplained prose. Keep existing URL selectors and source links.

Single vocabulary map (examples; final entries must be reviewed against each typed source, not guessed): `UNASSESSED` → “We have not checked this period”; `PENDING_REASSESSMENT` → “New readings are being checked”; `STALE`/upstream out of date → “This result may miss newer readings”; `UNKNOWN`/not configured → “We cannot judge this yet” / “This part has not been set up”; `CURRENT` → “Using the latest checked readings” **only when the read proves it**; `INCONCLUSIVE` → “We could not tell whether the change worked”; `INEFFECTIVE` → “The trial did not meet its goal”; `VERIFIED` → “The measured trial met its goal and safety limits” with scope. Reason-code families map to a cause sentence plus next useful step: missing report, incomplete period, stale source, pending computation, incompatible comparison, missing configuration, refused read. Unknown codes fall back to neutral “We cannot explain the limit from this record” plus closed technical code, never print the code in headline. Money has distinct “No current amount can be shown” and “No price recorded”; no `$0` substitution. Read refusal differs from proved empty.

Extend `frontend/src/test/productVocabulary.ts` and `.json` from T028 to scan the default reading of every W1 product route, including rendered API text, SVG labels/titles, badges and accessibility attributes. Add terms for known leaked enums/reason-code shapes, “rule ID”, “model version”, internal analytics phrases and raw IDs where they are authored prose. Scope exemptions narrowly to exact source-owned reference values and disclosure content, retaining the current single-value exemption rule. Do not exempt a whole screen, card or response. Keep a fixture matrix showing one populated, one missing and one refused state per presentation family; assert the scan saw nonzero text and rejects deliberate leaked terms outside detail. Inspect the existing `Advanced`/`Disclosure` primitives before adding a new one; adapt or wrap instead of duplicating behavior.

## Phases and proof

| Phase | Deliverable | Focused proof |
| --- | --- | --- |
| 1 | Reviewed semantic vocabulary table and shared status/limitation renderer; no app-wide rollout yet | Matrix tests for current/pending/stale/unknown/refused/zero, unknown code fallback, money withheld, no status promotion. |
| 2 | Shared disclosure/card/visual tokens and scan extension; migrate one representative Overview, Evidence and Action card only | Product-vocabulary mutation tests, keyboard/focus and accessible visual text, 1440/390 served screenshots against the three v69 screens, selected URL/link retention. |

Run focused tests and `npm.cmd test` from `frontend/` on final revision; type check; registry checker and `tools/check-all.ps1` relevant guards; fresh independent review of semantics, screenshots and fail-closed behavior. Record path:line anchors of every migrated call site in review packet. Do not modify backend schema or contract.

## Architect questions

Recommend keeping raw codes visible inside the closed disclosure for expert support and exact diagnostics, while banning them from default text and accessible labels of the collapsed card. If a code is itself the user-facing subject, require a labelled exact-reference field rather than a vocabulary exemption over prose.
