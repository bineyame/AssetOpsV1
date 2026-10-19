# Architect request: W2-05a Run 8 fix-round confirmations (r2)

You are the AssetOps Architect. Read the "Run 8 rulings (review r1)" section of `.agent/W2-05a-build-spec.md`. The code is on `task/W2-05a-ev-foundation` at head `164a1d1a`; use `git show task/W2-05a-ev-foundation:<path>`. The v69 EV mock is authoritative.

The fix-round builder raised three points. Give an exact ruling for each:

1. The M1 ruling says the unavailable entries are "focusable", but the existing shared `UnavailableLinkEntry` is deliberately not a tab stop. The builder left it unchanged. Rule one of two options:
   - keep the shared component as it is, and amend the ruling;
   - make the EV entries focusable, giving the exact mechanism and the accessible name.
2. For a missing feed, the L4 part cell reads "Not declared; Load manager · Not declared". Confirm the string, or give the exact replacement.
3. The H1 three feeder slots clipped text in the capture, so the builder widened the ev-sld SVG viewBox. Ratify the exact viewBox value now in the code, or rule a different one. The diagram is now 0.98x the mock height.

Append "Run 8 confirmations (r2)" to `.agent/W2-05a-build-spec.md`. Write nothing else. Do not commit.
