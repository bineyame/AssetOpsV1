# Owner review 3 of the delivery-strategy proposal (verbatim, 2026-10-09)

Owner's message: "Here is a follow-up feedback to the airtchtect regarding the delivery strategy, which is close to complete [text below]"

---

This version is ready to confirm. Every point from both of my reviews is addressed, and I re-checked the arithmetic. All the scores are correct, and the new allocation totals 110.

What changed, and whether it works

┌─────────────────┬──────────────────────────────────────────┬───────────────────────────┐
│   My comment    │                   Fix                    │           View            │
├─────────────────┼──────────────────────────────────────────┼───────────────────────────┤
│                 │ All downstream panels now count, using P │ Good. 40 panels now score │
│ 5-panel cap     │  = 5×(1−e^(−B/10))                       │  +0.88 over 5, and the    │
│                 │                                          │ score stays bounded       │
├─────────────────┼──────────────────────────────────────────┼───────────────────────────┤
│                 │ Planning-only drafts allowed during      │ A good balance, and it    │
│ Pause before S3 │ S2-02. Changes to tracked files wait for │ keeps the single S2 Codex │
│                 │  its closeout                            │  review                   │
├─────────────────┼──────────────────────────────────────────┼───────────────────────────┤
│ W2 not thin     │ Scenario screens and availability moved  │ Good                      │
│                 │ to W5. W2 is now 22 screens              │                           │
├─────────────────┼──────────────────────────────────────────┼───────────────────────────┤
│ One huge W4+    │ Split into W4/W5/W6, each with an owner  │ Good                      │
│                 │ exit review                              │                           │
├─────────────────┼──────────────────────────────────────────┼───────────────────────────┤
│ Shared          │ The pre-S3 shared contracts are          │ Good, and honest about    │
│ contracts       │ mandatory, outside ranking. Optional     │ what the score can't see  │
│ undervalued     │ ones get flagged at each wave start      │                           │
└─────────────────┴──────────────────────────────────────────┴───────────────────────────┘

Three things to calibrate before confirming

These are small, but each affects how the loop behaves day to day.

1. The 10% contested-ranking rule may stop the loop often. The scores bunch up: the example candidates fall between 2.09 and 2.88, and the main three differ by under 0.35. A 10% margin is about 0.27, so many selections would come back to you as "contested." Options:
   - tighten it to 5%
   - let the coordinator apply the tie-break rules and only notify you, rather than stopping
2. Effort barely affects the score. S versus L moves it by only 0.4, less than the gap between demo values 4 and 5. Large tasks get almost no penalty. That's acceptable if you value unblocking over speed. If you want quick wins to surface more, raise the effort weight to about −0.2.
3. Saturation point of the panel score. The /10 constant means P reaches about 63% of its maximum when B=10. W1 has 58 panels in total, and probably fewer core panels, so this fits W1. Ask that it be re-checked at each wave start, since waves differ in size.

A content note, no change needed

W3 builds the Risks and Opportunities lenses. However, the main mini-grid Opportunity Finding (opportunity-finding, the productive-use headroom) is in W4. So in W3, the Opportunities lens shows only what W1/W2 produce, possibly nothing, with an honest empty state. If the Opportunities lens matters to the demo, move opportunity-finding to W3. That only works if its renewable analytic is ready; otherwise accept the temporary gap.
