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

**Ruling CC-R1-Q1 (Architect, Claude, 2026-10-27).** Option (a). The guard stays unchanged: no new gloss, no new exemption reason, and no edit to `productVocabulary.json`.
- `CLAIM_LABEL.VERIFIED_SIMULATED_TECHNICAL` = `"Technical result verified on test data"` (exact text, no trailing punctuation). The rendered line is `Technical result verified on test data · benefits: mini-grid operator`.
- Why: customer screens already name non-equipment sources as test data. Examples are `SOURCE_WORDS.REGISTERED_SIMULATION` "Generated test data" and the verification page's own "Policy trial on Lab or authored test data" (`SiteActionVerification.tsx:545`). The new text covers both the generated and the authored (prepared example) sources, so it never overstates the source. It keeps the claim ladder's rung: a verified technical result, not a realized benefit, and it contains neither "saving" nor "saved".
- The enum key `VERIFIED_SIMULATED_TECHNICAL` is a code and stays unchanged. It appears only in `data-claim-level`.
- Same root cause, ruled now so CC-R2 does not hit it: the `VERIFIED_WATCH_RETURN` reason text (spec CC-R2 table) becomes `"Change verified on test data; watch for a return"`.
- Gating is unchanged (Q-C16). Wire the label now. The 5 tests in `siteActionVerification.test.tsx` must pass unchanged.

## Q2. The fallback "Claim not stated" contains a guarded word (no test fails today)

`productVocabulary.json` also lists `"claim"` (row "assessment states"). `ClaimLabel` shows "Claim not stated" only for an unknown level or beneficiary, and no fixture reaches that path on a scanned page. If a server ever sends an unknown value on a scanned page, the guard would flag it.

Confirm the wording stands, or give a replacement.

**Ruling CC-R1-Q2 (Architect, Claude, 2026-10-27).** Replace it. `"claim"` is guarded, and only the exact glosses "Claim boundary" and "Inspect temperature claim" are allowed. A fallback must not depend on never being scanned.
- Fallback text = `"Evidence level and beneficiary not stated"` (exact text, no trailing punctuation). It renders on its own, with no " · benefits:" suffix. It shows for an unknown level, an unknown beneficiary, or both. It never throws, and `data-claim-level` / `data-beneficiary` still carry the raw values.
- Why: it follows the existing "… not stated" / "Not declared" missing-state pattern and names what is missing in customer words. Add one unit test that renders the fallback through the vocabulary scan and expects `[]`.
