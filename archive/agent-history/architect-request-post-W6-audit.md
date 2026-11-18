# Architect request: plan the post-W6 structural app-vs-mock audit (all W1-W6 screens)

You are the AssetOps Architect. W1 through W6 are complete on main. Before the owner's single walkthrough, the owner has asked for a structural audit of every implemented W1-W6 screen against the v69 mockup, followed by fixes, and then a walkthrough index grouped by departure category D1-D6.

Read these first:
- .ai/ROLE_CONFIG.md: "Mock fidelity", "Departure categories and register", and lessons 14 and 15.
- tasks/README.md, for the full list of slices and screens.
- .agent/mock-departure-register.md: about 113 rows.
- .ai/MILESTONE_REVIEW_BACKLOG.md: the carried UI-pass items and Lows.
- The precedents: .agent/W1-F5b-* (all-26 audit index, 168 pairs) and .agent/W2-F-build-spec.md with .agent/W2-F-closure-check.md (the W2 structural re-audit).
- The v69 mock: frontend/mockups/v69/index.html, render-reference.ps1 and browser-review.json.
- The existing capture and producer tools under tools/ (w502*, w504*, and the W1/W2/W3 capture tools).

Write .agent/post-W6-audit-spec.md. It must define:
1. Scope. List every v69 screen that W1-W6 implement, each with its route, owning slice, and the producer or walkthrough mode that provides real data. Also list the screens that are deliberately out of scope or unavailable.
2. Method. For each screen, compare panel order and titles, layout, typography, colour tokens, states, and 1440/390 behaviour against the v69 reference render. Reuse the existing producers and capture tools, keeping them capture-only. Give one index format, with a pair per screen per width.
3. Classification. Every difference becomes one of three things: (a) already registered, with its row cited; (b) a new real departure, with a D1-D6 label and a register row; (c) a D3 defect to fix. Include the backlog UI-pass items: the .prose 14 vs 12 px typography, the tall dark 390 header on short pages, "1 incidents" grammar, raw asset labels, and the window error copy.
4. Split. Divide the audit into reviewable agent batches of at most about 6 screens each, grouped by shared code, with an order and a maximum parallelism of 2.
5. Fix plan. Specify how D3 fixes are batched into fix slices. Apply lesson 15 to caps.
6. Walkthrough index. Define its format, grouped by D1-D6, so the owner can walk the app screen by screen with each departure flagged in plain language.
7. Gates. State what counts as done before the owner is called.

Do not touch product code. Do not commit.
