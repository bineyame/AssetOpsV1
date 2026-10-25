# Architect request: W4-mini build choices to confirm

You are the AssetOps Architect. The W4-mini builder (worktree `../AssetOpsV1-review9`, branch `task/post-W6-W4-mini`; handoff `.agent/post-W6-W4-handoff.md` there) built units 1-4 under `.agent/post-W6-W4-rulings.md` and made these choices where rulings were silent. Confirm or correct each with exact copy/values, applying the owner's standing UI bar (`.agent/owner-ui-ux-guidance-2026-10-25.md`; name the pattern for UI calls):

1. **R328:** the mini Finding read has no public code field, so the crumb says "Finding" in every state (incl. resolved). Per Q15 R328 cannot close until a public code exists. Rule: close-as-D1/keep open/needed backend field (and who owns it).
2. **Work 422 copy:** over-31-day window → "Choose a window of 31 days or fewer."; expired cursor → strip "Counts not shown: this page of results expired." (builder's sentences); other codes reuse Q4 wording.
3. **"Lens: Opportunity"** chip kept green as in the mock, treated as a fixed page label like the Q3 series colours; CONFLICT decisions amber.
4. **Bar colours** darkened from mock series colours to reach 3:1 non-text contrast (WCAG 1.4.11): PV #a87a2c, margin #77839a, headroom #3a8f7c, critical #b65252.
5. **Refused frame** applied to 422 only; 401/403/404/503 keep their existing refusal. Confidence chip on all four refused strips (Q7). The reason sits in the first panel; other panels say "Not assessed".
6. **Q11:** mini keeps its own copy of the refused frame for now; cold's `RefusedStrip` not lifted into a shared module because W2-cold has not merged — confirm the lift happens on W4's rebase after W2-cold (or not at all).
7. **Window end dates:** Scenarios Window uses an exclusive "To" (DomainWorkWindow pattern); the mini Work form keeps its inclusive "to (included)" and now shows the zone label. Accept the inconsistency or unify (which way).

Write numbered rulings to `.agent/post-W6-W4-build-rulings.md`. Do not edit product code or `.gitignore`.
