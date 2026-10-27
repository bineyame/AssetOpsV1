# CC-R1 questions for the Architect (2026-10-27)

Builder: Lane C, branch `task/CC-R1-claim-links-beneficiary`. Everything else in CC-R1 is built; the item below is held, not decided.

## Q1. The verdict label wording is rejected by the product-vocabulary guard

Spec §0.4 fixes `CLAIM_LABEL.VERIFIED_SIMULATED_TECHNICAL = "Technical result verified on simulated data"`, and CC-R1 "Labels" puts it under the Verification verdict for a VERIFIED or INEFFECTIVE displayed outcome.

When wired, 5 existing tests in `frontend/src/sites/__tests__/siteActionVerification.test.tsx` fail. Example failure text: `verification:1-3: "simulated" in text: Technical result verified on simulated data · benefits: mini-grid operator: expected [ { page: 'verification:1-3', …(3) } ] to deeply equal []`.

The cause is `frontend/src/test/productVocabulary.json:36`, `{ "phrase": "simulated", "row": "development workflow" }` (decision D-2026-10-04-plain-language-analysis-views). The exemption attribute only accepts a closed set of reasons: a source-owned reference, a user-owned name, or a Lab entry. None of them fits a product claim label.

The two ways forward both need an Architect decision, which the builder may not make:
- (a) Change the label wording so it avoids "simulated". For comparison, the cold surface uses "generated test data" (`coldRoutes.test.tsx:479`).
- (b) Amend the vocabulary decision, or add an exemption reason. This loosens a guard, so the builder will not do it.

State now: `CLAIM_LABEL` keeps the spec text verbatim. The verdict label is **not wired**: `SiteActionVerification.tsx` is unchanged, and register R500 covers `scenarios` only. Once the wording is ruled, wiring it is one conditional; its gating is already settled by Q-C16.

## Q2. The fallback "Claim not stated" contains a guarded word (no test fails today)

`productVocabulary.json` also lists `"claim"` (row "assessment states"). `ClaimLabel` shows "Claim not stated" only for an unknown level or beneficiary, and no fixture reaches that path on a scanned page. If a server ever sends an unknown value on a scanned page, the guard would flag it.

Confirm the wording stands, or give a replacement.
