# 1a rulings (D-1A.1 to D-1A.8)

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-stands-in-2026-11-21b.md`).
Owner-level calls are logged in `specs/OWNER-AWAY/decisions-2026-11-21.md` row 52.

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
