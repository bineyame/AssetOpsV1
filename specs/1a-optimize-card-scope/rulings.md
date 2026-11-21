# 1a rulings (D-1A.1 to D-1A.11)

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-stands-in-2026-11-21b.md`).
Owner-level calls are logged in `specs/OWNER-AWAY/decisions-2026-11-21.md` rows 52 and 58.

## D-1A.1 Today's figure is one lead issue's stored cost, chosen on the window's last day; pinned first

- **Code reality (21 Nov, `main`).** The Portfolio Optimize card (`site_outcomes/read.py` `_optimize_card`) shows each
  priced Site's `OPTIMIZE_COST` earnings claim, `avoided_cost@1` over `money_head` (`chain/strategies/avoided_cost.py`).
  The money head is the stored consequence of one Finding: `lead_finding` over the board day (`site_outcomes/mini.py`
  `compose`, `board_day(day)`), and in the summary a mini-grid Site's board day is `window_day(lo, hi)`, the last day of
  a multi-day window (`summary_window`, `chain/read.py` rule 3). `_window_parts` re-evaluates nodes over the window's
  days but keeps the same `money_heads`, so the figure stays that one Finding's. The claim carries no days
  (`money_claim(..., days=None)`), so `days_line` is None and nothing on the card names the day.
- **Ruling.** Commit 1 pins this in tests (P1 to P4) before any product change, as the design's PR 1a says. The pack's
  citations (`site_outcomes/read.py:602-606`, `:676-682`) moved; the spec cites today's lines.

## D-1A.2 Correct by stating the day and scope, not by a period figure (owner-level, row 52)

- **Options.** (a) Replace the figure with the period's avoidable cost; (b) keep the figure and state its day and scope.
- **Ruling: (b).** A period figure from Findings would add stored consequences across days. Episodes span days and
  overlap, and the design forbids presenting the sum as a period cost (N12) and summing across Sites (A6). The period's
  cost is a factor of the structure read, and it reaches the Portfolio with `7g` (through 3B7a), from records. Until then
  the one figure stays, and the card says what it is. The amount is not repeated inside the scope sentence, so the card
  still holds one figure per quantity (owner, `owner-one-figure-loyal-to-operating-world-2026-11-21.md`).
- **Reverse by:** a `7g` period figure replaces the value; the scope line then goes.

## D-1A.3 The scope sits on the card face, in v70's days slot (owner-level, row 52; amends D-UQFI.7 for this card)

- v70 `pfCard` (`frontend/mockups/v70/index.html:494`) puts a days line (`oc-pfdays`) directly under the figure, and
  `PFDAYS.cost` names a day ("Kobo: 6 Oct partly checked"). UQ-FI-3 later moved every days line behind "Why?" (one
  figure, one sentence, the basis; D-UQFI.7). For this card the day is part of the figure's meaning: behind "Why?" the
  figure still misleads. So the Optimize card's scope line stays on the face in v70's slot. Every other card is
  unchanged.
- **Reverse by:** moving the `<small>` into `CardQualifiers` (one line).

## D-1A.4 The words are one SC-1 statement; no legacy text and no guard changes

- New served words are SC-1 statements (D-SC1.28). `portfolio_card.cost_scope` holds all of them. The legacy texts
  (`cost.detail.*`, `cost.sites`, `cost.site`, `cost.basis.*`, the value) are unchanged. So COH-17 O1
  (`tools/checks/chain_coherence.py`), the demo prepare's `optimize_card` self-check (`tools/demo_combined_rows.py`) and
  the legacy and hand-built baselines need no edit. A guard change would need the owner (row 5).
- `site_outcomes/read.py` stays in the ratchet scope. The new code uses only code-form strings. It is not moved to
  `ADOPTED`, because the rest of the file is legacy.

## D-1A.5 The class, swept (W6)

- Every Optimize claim is one lead issue's cost, whatever the Site type. On the DAY basis (mini-grid) it is the issue on
  the board day. On the PERIOD basis (cold-chain, EV) it is the latest event in the window (`summary_window`,
  CH6b1-R3). Today only mini-grid Sites are priced (cold-chain maintenance has no money value; EV Optimize is not
  measured). The statement covers both bases (`one_latest`, `each_differ`), so a priced cold-chain Site never reads
  as a period total either.
- The site board's own Optimize row names its board day already (the board is one day). Rendering the hidden API
  fields is `1b`, out of 1a.

## D-1A.6 The date reads SC-1's one day format (MOCK DEVIATION MD-1A-1, format)

"30 October 2026" (`day`, D-SC1.10), not v70's "6 Oct". One format per type, and a second date form would be a new
format branch.

## D-1A.7 Size and shape

1.75 units, two commits: the pin (0.25) and the correction (1.5). This is below the plan's 2.5 because the card's
claim, its single source and the face slot already exist (CH5d1). The added cost is the SC-1 statement and its six
cases. Screen unit: reviewed when built; the merge is held for the owner's walkthrough (delegation terms). Standard
review.

## D-1A.8 One noun added to the vocabulary

`noun.day` (`one` "day", `other` "days"), appended to the noun order. It is shared data, and later units reuse it.

## Handshake answers (rev 2; 2026-11-21)

The questions are in `handshake.md` (R1-R4) and `handshake-I.md` (I1-I3). Each is answered once:

| Question | Answer |
|---|---|
| I1 | D-1A.9 (owner-level, row 58) |
| R1 = I3 (S7 part) | D-1A.10: R1's whole-decimal-token rule; I3's whole-run rule is not enough |
| R2 | default accepted (D-1A.10): regenerate the golden, exactly one added key |
| R3 | D-1A.10: S5b and S5c added, with D-1A.9's `each_differ` wording |
| R4 = I3 (S9 part) | default accepted (D-1A.10), with the real signature |
| I2 | default accepted (D-1A.10) |

## D-1A.9 The wording: "Cost of {site}'s lead issue on {day}" (owner-level, row 58; amends row 52's example)

- **Question (I1).** The catalogue refuses "One issue's cost" (`LITERAL_NUMBER_WORD`: "one" and "single" are number
  words, `schema.number_words`). That phrase appears in all six variants.
- **Ruling.** The six variants read:

| Variant | Text |
|---|---|
| `one_day` | Cost of {site}'s lead issue on {day} |
| `one_range` | Cost of {site}'s lead issue on {day}, the last of the {days} shown, not their total |
| `one_latest` | Cost of {site}'s latest issue in the {days} shown, not their total |
| `each_one_day` | Cost at each Site of its lead issue on {day} |
| `each_range` | Cost at each Site of its lead issue on {day}, the last of the {days} shown, not their total |
| `each_differ` | Cost at each Site of its lead issue in the days it shows, not their total |

  For example: "Cost of Kobo's lead issue on 30 October 2026, the last of the 30 days shown, not their total".
- **Checked.** The statement, with `noun.day`, was loaded in a scratch copy of `i18n` and rendered from S1-S5's facts.
  All six variants render with these exact texts.
- **Why.**
  - The figure above the line already says what it is ("possible extra fuel cost"). "Cost of ... lead issue" ties
    that figure to the issue, which is the line's whole job, and keeps "issue" singular without a number word.
  - "The last of the 30 days shown, not their total" says which day the figure belongs to and that it is not the
    period's total: the misreading 1a corrects.
  - `each_differ` drops rev 1's "the last day it shows", which is false for a PERIOD-basis Site (its claim is the
    latest event in the window, D-1A.5; R3). "In the days it shows" is true on both bases.
  - The owner's one-figure rule holds: no amount is in the line.
- **Reverse by:** rewording the six variant texts. The slots, facts and cases do not change.

## D-1A.10 The tests the handshake fixed

- **S7 (R1 over I3).** A whole maximal digit run still collides on real data: the Kobo week golden's claim is "3.31
  to 3.97 USD" on 31 October, and "31" matches. So S7 asserts that the scope text contains neither the claim's `text`
  nor any of its amounts (`value.low`, `value.high` or the single amount) as a whole decimal token, matched as
  `(?<![\d.])<amount>(?![\d.])`. A case with "3.31 to 3.97 USD" on 31 October must pass. PL3 still fails it.
- **S5b and S5c (R3).** S5b: two PERIOD Sites with `day None` and 7 days each. S5c: one DAY Site and one PERIOD Site.
  Both read `each_differ`, and each gets a matching statement case.
- **S9 (R4, I3).** `coh17_optimize("1a", summary, [], {})` (`tools/checks/chain_coherence.py:1259`) returns `[]` on
  S8's two summaries, and on a third summary from the same recording fake board with two priced Sites.
- **The contract golden (R2).** `backend/tests/fixtures/ch5a2_chain_contract/estate_week_2026-10-25.json` is
  regenerated. Its diff is exactly one added key on Kobo's Optimize card: `"scope_text": "Cost of Kobo's lead issue on
  31 October 2026, the last of the 7 days shown, not their total"`. The packet shows that diff, and the reviewer checks
  that nothing else moved. The file is added to §0 Files.
- **Face hooks (I2).** The five-hook test (`estatePortfolio.test.tsx:1384-1396`) keeps its fixture. F1 asserts that the
  Optimize face hooks are `onCard` plus `data-portfolio-card-scope`, and F3 that the other three cards keep `onCard`
  exactly.

## D-1A.11 Size unchanged: 1.75 units

S5b, S5c, the golden and S9's third summary are test lines inside commit 2's 1.5 units. 1a is build-ready. The merge is
held for the owner's walkthrough (D-1A.7).

