# 1a handshake

## Reviewer questions (R)

Fresh Claude reviewer, 2026-11-21, on `main` `0ead104e9`. Read: `spec.md`, `reviewer-guide.md`, `rulings.md`
(D-1A.1 to D-1A.8), the owner's one-figure file, and the cited code: `chain/read.py:138-215`,
`site_outcomes/read.py:670-985`, `i18n/facts.py`, `tools/checks/chain_coherence.py:1259`, `chain_api.py:354` and the
v70 `pfCard` (`index.html:415, 494`). I checked P1 and S8 by hand. `window_day(1 Oct, 31 Oct UTC)` is 30 Oct by rule 3,
`window_days` gives 30 days, and 30 Oct to 31 Oct UTC is one day by rule 2. Both pins are right as written.

**R1. S7 can fail on honest text and pass on dishonest text (a rule a test can't decide).** "No digit run that also
appears in any claim's `value`" does not say whether a match is a whole digit run or a substring. As a substring
match, "3" from "3.31" is found inside "30 October". As a whole-run match, it still collides on real data: the
Kobo week golden's claim is "3.31 to 3.97 USD", and its scope day is "31 October 2026", so "31" matches. The test then
depends on which fixture values were chosen.
*Default:* S7 asserts that the scope text contains neither the claim's `text` nor any of its amounts as a whole decimal
token. The amounts are `value.low`, `value.high` or the single amount, each matched as
`(?<![\d.])<amount>(?![\d.])`. Add a case with a claim of "3.31 to 3.97 USD" on 31 Oct that must pass. PL3 still
fails S7.

**R2. A byte-equal wire golden will break and is not in the Files list.** `/api/estate/chain` returns
`summary["cards"]` (`chain_api.py:354`), and `test_ch5a2_contract.py::test_chain_body_equals_its_golden` compares it
byte for byte with `backend/tests/fixtures/ch5a2_chain_contract/estate_week_2026-10-25.json`. That golden holds Kobo's
priced Optimize card. The §3.5 sweep says "update only exact-equality expectations of the card dict", which does not
say clearly whether a contract golden may be regenerated.
*Default:* regenerate that golden. Its diff must be exactly one added key: `"scope_text": "One issue's cost: Kobo's
lead issue on 31 October 2026, the last of the 7 days shown, not their total"`. The window is 25 Oct to 1 Nov UTC, so
`window_day` gives 31 Oct and there are 7 days. The packet lists the golden with its one-line diff, and the reviewer
checks that nothing else moved.

**R3. `each_differ` makes a false statement for a PERIOD-basis Site, and no test covers that case.** D-1A.5 says a
cold-chain or EV claim is the latest event in the window, not the issue on a last day. Under §3.3 step 4, any
several-Site card that includes a PERIOD Site over a range has a `None` in `d`, so the card reads `each_differ`: "its
lead issue on the last day it shows". That is false for the PERIOD Site. No S case has several PERIOD Sites or a
mixed DAY and PERIOD set.
*Default:* `each_differ` reads "One issue's cost at each Site: one issue in the days it shows, not their total". Add
**S5b** (two priced Sites, `day None` for both, `days 7`) and **S5c** (one DAY Site on 30 Oct and one PERIOD Site),
both expecting that text, plus the matching statement case. If the Architect prefers other wording, the cases still
apply.

**R4. S9 runs on objects the tests do not build.** S9 runs `coh17_optimize` on "S1's and S4's summaries". S1 and S4
build cards with `_optimize_card`, not summaries, and `coh17_optimize` reads a summary dict
(`sites[].rows[OPTIMIZE_COST].nodes.earnings` plus `cards`).
*Default:* S9 runs on S8's two summaries (one priced Site, 30 days and 1 day). It also runs on a third summary from the
same recording fake board with two priced Sites. All three return `[]`.
