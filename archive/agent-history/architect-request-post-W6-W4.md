# Architect request: W4-mini pre-flight questions

You are the AssetOps Architect. A builder pre-flighted the post-W6 W4-mini card against main ba971d96: `.agent/post-W6-W4-preflight.md` (build plan per D3 item; 22 numbered questions with recommended defaults). Verify code claims yourself as needed. Rule on all 22 with exact, implementable answers.

Apply the owner's standing UI bar (`.agent/owner-ui-ux-guidance-2026-10-25.md`): state-of-the-art UI/UX within demo speed; ground UI rulings in current guidance (WCAG 2.2, Material 3/HIG/GOV.UK/Carbon, NN/g, responsive data-table patterns) and name the pattern. The v6.9 mock stays the layout spec; layout changes it implies become labelled D2 proposals.

Decide explicitly: ownership of R309/R322 widening and cold-action B15-04 (vs W5-cold); the app-wide Site tab rule at 390 (R333, W6 Q9/Q21 reuse) and who lands it given merge order shell → W1-a → W1-b → W2-EV → W2-cold → W4 and W6 in parallel; the refusal-copy-by-code fix (R311/R321, Q4/Q5); R313 page frame on refusal and cold strip lift (Q7/Q11); R320 Site-time routing; R325 inner scroll removal and the D1 row (Q13/Q14); R328 remainder; caps per Lesson 15 (worst case, all-open exemption, fallback; Q18 formula) ; register numbering (main ends R395; W6 has R396 on its unmerged branch; W2-EV/W2-cold may add rows — reserve a W4 block that cannot collide).

Amend the W4 card in `.agent/post-W6-audit/fix-slices.md` if scope changes. Write numbered rulings to `.agent/post-W6-W4-rulings.md`. Do not edit product code or `.gitignore`.
