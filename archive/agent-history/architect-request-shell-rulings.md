# Architect request: shell-typography-copy pre-flight rulings, and card repair

You are the AssetOps Architect. Read `.agent/post-W6-shell-preflight.md`: the builder's 26 questions, with defaults, for the card "shell-typography-copy" in `.agent/post-W6-audit/fix-slices.md`. Also read the register rows and audit ledgers it cites, and lesson 15 in `.ai/ROLE_CONFIG.md`.

1. Write `.agent/post-W6-shell-rulings.md` with one numbered ruling per question (Q1–Q26). Each ruling either accepts the default or states an alternative, with exact files, copy, behaviour, tests and recapture set. Cover in particular:
   - Q3: mixed D3/D1/D2/D4 IDs. Give the exact D3 part for each, and say what gets a label or register row.
   - Q13: SLD scale-to-fit at 390.
   - Q14: R141, whether it reads the VerificationPlan or becomes D1.
   - Q23: explicit caps for mini evidence-analysis records and the Foundation Identity panel, sized from the worst case per lesson 15, with the all-open exemption and the fallback.
   - Q24: the recapture set. The 1,414-pair full rerun or the builder's 174 + 230 plan.
2. **Card repair, all ten cards.** The builder found that the shell card's "Panels and order" and "Files" lists were auto-generated and wrong: screens missing (R203 action screens, R319 cold/EV Work), and four files serving none of its IDs. Check every other card in `fix-slices.md` the same way (W1-mini-Action-a/b, W2-cold, W2-EV, W3-estate, W4-mini, W5-cold-Work, W5-EV-Work, W6-global-Work). For each card, from its exact D3 IDs, the register rows and the current code, correct:
   - the affected screens;
   - panels and order;
   - files actually touched;
   - the tests likely to break;
   - the recapture set, using the same rule you set for Q24.

   Recheck the shared-file and parallelism notes in "Sequencing and shared files" after the correction. Say which cards can now run in parallel, and fold in the R373 carve-out: it is being built separately on `task/post-W6-R373-request-access`, per `.agent/post-W6-R373-rulings.md`, so remove it from the W6 card's build scope while keeping the B19 recapture.
3. Edit `fix-slices.md` in place. Do not edit product code. Keep it tight.
