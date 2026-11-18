# W1-UX-05 handoff (complete, both phases; in_review)

Branch `task/W1-UX-05` at the closeout commit after `af9b6406` (base main `815888f0`). Not merged. Packet: `.agent/W1-UX-05-review-packet.md`. Combined walkthrough draft: `.agent/W1-UX-combined-owner-walkthrough.md` (UX-05 rows captured; other rows owned by UX-02..04, refresh after the last UX merge).

- Cards: `frontend/src/sites/foundationHeadlines.tsx` (model/readiness/SLD + `foundationPeriodWords`, `setupReadinessWords`), `frontend/src/sites/healthHeadlines.tsx` (Health, battery + contact/condition words, `factAgeUnknown`).
- Vocabulary helpers for single values: `frontend/src/sites/exactValues.tsx` (`UserName`, `ExactRef`).
- Evidence: `tools/w1-ux-05-evidence.mjs` (card map for the five screens). Its 390 px overflow measurement inherits a UX-01 script timing issue (measures 1425 px); fix in the shared script pattern if relied on.
- Open: S7-01b L2 (backend negative receipt lag); shared `expectStateLineVisible` vs `asOfText(null)`; backend "binding" statements replaced in UI only when no link set (see packet Known Deviations).
- Next: fresh independent review (diff S7-01b fail-closed tests), then merge; owner sees it in the combined W1 walkthrough.
