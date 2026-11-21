# 1a handshake, implementer side

Implementer (Claude), 2026-11-21, pre-flight against `main` `0ead104e9`. No product code written.

Checked and as the spec says:
- `summary_window` (`site_outcomes/read.py:675-683`) and `_summary` (:685-745); `_optimize_card` (:901-923) returns
  exactly the seven keys P4 lists. `portfolio_cards` (:926) has one product call site (:738).
- `window_day` and `window_days` (`chain/read.py:138-170`): 1 Oct to 31 Oct UTC gives 30 Oct and 30 days, and
  30 Oct to 31 Oct gives one day. `lead_finding(heads, lo, hi, *, source_open, ...)` (:183) and `FindingHead` (:234).
- The `KOBO` `SiteRef` and the recording fake board (`test_out_w2_summary_window.py:21`, `:48-65`). `_site` and
  `_claim` in `test_ch5d1_optimize_card.py:16-24`.
- The SC-1 types `state`, `name`, `day` and `count`, the slot field `absent` and the operators
  `present`/`reason`/`is`/`all` (`i18n/schema.py:10-45`).
- `PortfolioOutcomes.tsx` `content()` (:90-110) and the value/detail markup (:277-284); `EstatePortfolioCard`
  (`estateClient.ts:706`); `.ob-days` (`sites/outcomes.css:167`).
- v70 `PFDAYS` (:415) and `pfCard` (:494).
- The new code in `read.py` adds no ratchet hit: docstrings are skipped, and the strings are code-form.

## Implementer questions (I)

**I1 (blocks commit 2). The statement as written fails the catalogue load.** I loaded §3.2's literal in a scratch copy
of the package, with `noun.day` added, and it stops at `CatalogueError('LITERAL_NUMBER_WORD',
'portfolio_card.cost_scope', 'one_day')`. "One" is a number word (`i18n/catalogue.py:131-134`,
`schema.number_words`), and so is "single". It is in all six variants. With only "One issue's cost" reworded, the rest
of the statement (slots, `absent`, `requires`, `reason`, `noun.day`) loads, and all six variants render from S1-S5's
facts. **Default wording, tested:**
- `one_day`: "Cost of {site}'s lead issue on {day}"
- `one_range`: "Cost of {site}'s lead issue on {day}, the last of the {days} shown, not their total"
- `one_latest`: "Cost of {site}'s latest issue in the {days} shown, not their total"
- `each_one_day`: "Cost at each Site of its lead issue on {day}"
- `each_range`: "Cost at each Site of its lead issue on {day}, the last of the {days} shown, not their total"
- `each_differ`: "Cost at each Site of its lead issue on the last day it shows, not a total"

These render as, for example, "Cost of Kobo's lead issue on 30 October 2026, the last of the 30 days shown, not their
total". §1's gate sentence, S1-S5, the case module and the F fixtures would take these texts. The wording is
owner-level (row 52), so the Architect rules it.

**I2. An existing test pins the card face to five hooks.** `frontend/src/estate/__tests__/estatePortfolio.test.tsx:1384-1396`
pins every card's face hooks to exactly five (`onCard`, the UQ-FI rule). Its fixture has no `scope_text`, so it stays
green, but D-1A.3 amends that rule for Optimize. **Default:** leave that test's fixture as it is. F1 asserts that, with
`scope_text`, the Optimize face hooks are `onCard` plus `data-portfolio-card-scope`. F3 asserts the other three cards
keep `onCard` exactly.

**I3. Two minor points.**
- S9: `coh17_optimize` takes `(w, summary, files, tally)` (`tools/checks/chain_coherence.py:1259`), not a summary
  alone.
- S7: "digit run" is not defined. S1's claim value "3.31 USD" has the runs "3" and "31", and its scope has "30" and
  "2026", so a substring test would fail where a whole-run test would not.

**Default:** call `coh17_optimize("1a", summary, [], {})` and assert `[]`. S7 compares whole maximal runs
(`re.findall(r"\d+", ...)`), not substrings.
