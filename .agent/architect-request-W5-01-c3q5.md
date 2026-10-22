# Architect request: W5-01a C3 Q-C3-5 and mock differences

You are the AssetOps Architect (Codex). Read the `.ai/ROLE_CONFIG.md` rules on mock fidelity ("Mockup drives the design" and "Both Architects ... against the v69 mock"), the C3 card in `.agent/W5-01-build-spec.md` (including "C3 rulings (Q-C3-1..4)" and your retrospective), and the v69 `cold-health` screen in `frontend/mockups/v69/index.html`. Read the C3 build on branch `task/W5-01a-cold-selected-depth` (code `56231727`, evidence and handoff `f3bf7c6c`). Use `MSYS_NO_PATHCONV=1 git show task/W5-01a-cold-selected-depth:.agent/W5-01a-phase-handoff.md`; the captures are in `.agent/W5-01a-C3-evidence/` on that branch.

Rule with literals:
1. **Q-C3-5.** At 390 the `Condition and evidence` panel is 556–591 px against its 430 cap, because each asset UUID wraps to 4 lines in the narrow Asset column. The builder's options are (a) add `frontend/src/ui/primitives.css` for a scoped no-wrap, sticky-first-column rule; (b) raise the cap; (c) something else. Choose by mock fidelity: what does the mock show in the Asset cell at 390? Give the exact CSS, file list and cap.
2. **Mock differences the builder reported:**
   - the Backup card colours its value amber instead of the mock's amber top border;
   - the card label is the link instead of `View detail →`;
   - values use the smaller word size.
   For each, either restore it to the mock (with the literal change) or KEEP it with a `MOCK DEVIATION` label.
3. **Registry reasons.** The builder wrote the `cooling:1` and `cooling:2` registry reasons in its own words, which is an implementer decision. Give the literal reasons.

Append the result as "C3 rulings (Q-C3-5, mock differences)" to the C3 card, amending `D-2026-10-22-w5-01-w5-03-buildspec`. Write nothing else. Do not commit.
