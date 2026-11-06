# CH-6b3 pre-flight (coherence, proofs and the packet; size 1.0)

Branch `task/CH-6b3-coherence-proofs`, head 9b1c53ae3. No code written. **Result: rulings needed on Q1-Q4; stopped.**
Q5-Q9 need no ruling and are recorded so they can be overruled. Recommendation for all four: accept as written.

## Rulings needed

**Q1. COH-17: which fields on which bodies? (design choice; the sheet names claims and screens, no field table)**
Today COH-17 compares only three `count.*` keys: `/estate/chain` against Portfolio and Findings (`chain_coherence.py:1094-1137`). Code facts:
- `/estate/chain` and the summary share `portfolio_parts` and `portfolio_cards` (`site_outcomes/read.py:631,647,665`; `chain_api.py:338,352`).
- Board `rows` are read over the board window. The summary then replaces `nodes` with nodes over `window_days` (`read.py:507,613`). So a mini board (one day) and its summary nodes (the whole window) differ by design (CH6b1-R Q1, Q4).
- COH-7b already compares `(state, headline_money)` of summary and board (`:646`).

Recommended table, all per estate window (week, S, month), under the existing equal-Site-set rule:

| Claim | Compared |
|---|---|
| Count | Existing three keys. Add: `cards.PROTECT.claim` = `counts[count.sites_disrupted]`; `cards.ASSURE.claim` = `counts[count.verified_results]`, on both chain and summary (value, basis, text) |
| Money | chain `money_total` = summary `money_total` = `cards.GROW.claim`. `value.amount` = sum of `money2(amount)` over `sites[].earnings[INCOME_LABELS]` with an amount, in one currency (the Q5b rounding). More than one currency: value null. A Site claim with no amount is named in `lines` and excluded. Per-Site `earnings` chain = summary |
| Verdict | `(state, state_label, lead)` chain rows = summary rows = `board_summary.{w}.{code}` rows, every Site. `nodes` chain = summary, every Site. `nodes` board = summary only where the Site's board window names the same days: PERIOD Sites, and a mini Site on the one-day S window. Mini on week and month is not compared, by design |
| Why | See Q2 |

A finding from this table on the polish clone is reported, not adapted. In particular, the PERIOD board nodes have never been compared to summary nodes, so this comparison may produce a real finding.

**Q2. COH-17 "why": the route is not in the bundle, and what is compared? (design choice + collector scope)**
Packet CH-6b2 says "The Why? route is not in the coherence bundle".
- Why carries no claim objects. It carries text and `nodes` (`chain/why.py:73`, `:262`; `chain_api.py:385-390`).
- `text.say` is the board row's `headline or state_label` (`why.py:262`).
- PROTECT `comes_from` carries one "{Site}: ..." line per counted thread, then the early-warning line (`why.py:303`).

Recommendation:
- Collect `why_estate.{w}.{category}`: 4 categories x 3 windows = 12 reads, estate windows only, under a new manifest stamp `why: true`, so older fixtures are not judged.
- **W1:** per Site, `text.say` = the summary row's `headline or state_label`.
- **W2:** for PROTECT, when the claim has a value, the number of distinct Sites named in `comes_from` = `count.sites_disrupted.value`.
- The "{kWh} kWh x {price}" line is not compared. It is the board day's on a mini Site and carries no total (Known Deviation).

**Q3. COH-18: which claim, and how are the day bodies collected? (sheet/code mismatch)**
CH-5a `:681` says "the claim's `days`" against "the collected `/sites/{c}/chain` day bodies".
- The collector reads `chain_site` only for the named days (`chain_coherence.py:199-203`), not every window day, so the sum cannot be done from today's bundle.
- The `/sites/{c}/chain?from&to` form is not usable as one read. The per-date form is what names a `window_days` day (`days_of`, `chain/site_chain.py:32`).

Recommendation:
- Collector: for each Site in the summary, read `/sites/{c}/chain?date=d` once per date, for every `window_days` date of week, S and month (deduplicated `chain_day.{code}.{d}`). This adds about 31 dates x 3 Sites = about 93 reads on polish and about 90 s of collect, under a new stamp `day_bodies: true`. All three windows are UTC midnights, so `window_days` names dates with no time zone needed (`estate_windows`, `:59-69`).
- Claim judged: `chain_estate.{w}.sites[].days` (the Site's `days`, shown on every card days line) field by field, plus `counts[*].days` = their `sum_days`. Node `days` (per measure, or per span) are out. Day windows are out.
- Grades come from the body's `days[0].grade`. An unbuilt day already grades NO_DATA by the rule (`chain/read.py:80`, `reader.py:70`). Both rules treat a NOT_EXPECTED day as outside `expected`.

**Q4. `gap_days`, the CHECKED_DAYS assertion and the legacy fields (sheet/code mismatches)**
- **(a) L3m wording.** The sheet says CHECKED_DAYS forms appear "only in windows containing GAP-K7, GAP-C3 or GAP-E2". On the real L3m DB:
  - it is Kobo only (MD0-S2), so GAP-C3 and GAP-E2 cannot occur;
  - the `states` set has no D6-D9 (KD-3, `test_ch6b_estate_postgres.py:143-145`), so a window holding D8 or D9 reads CHECKED_DAYS for that reason, even without D7.
  
  Recommendation, following CH-5a handoff `:392` ("a declared gap or outside the built set"):
  - `expected-mechanism.json` gets `gap_days: [{site_code: KOBO-001, day: <D7 date>, gap: GAP-K7}]`.
  - A built day is one whose body grade is not NO_DATA or NOT_EXPECTED; every built day not listed must be COMPLETE.
  - The assertion becomes part of COH-18 when `gap_days` is given: a `CHECKED_DAYS` Site `days` or count claim only in a window that includes a listed gap or a NO_DATA (unbuilt) day.
  - Limit: a day built with no readings cannot be told from an unbuilt one. The MD-0 tests own that case.
- **(b) Legacy fields: added scope, Architect classifies.** CH-5a `:686-691` and handoff `:395` say "when CH-6b retires the legacy fields" the S/week text moves from "1 confirmed" to "1 open", and the packet lists it. No CH-6 ruling retires them, and they are still rendered on the same Portfolio page as the claims:
  - `EstatePortfolio.tsx:460,537` "Fixes confirmed · {verified_resolution_count}";
  - `:796` "{priority_site_count} priority sites";
  - served from `estate/portfolio.py:615,643-644,838,856`.
  
  So the Assure card can read "None confirmed" beside "Fixes confirmed · 1" (the CH-5a-recorded clone values were 1 against 0, and 0 against 1). Options:
  - **A (recommended; demo-critical, about +0.1):** both frontend spots render `summary.claims` (`count.verified_results`, `count.open_threads`) with one test. The packet lists the change and confirms the cause from thread events. Backend fields stay.
  - **B:** leave them, COH-17 does not compare them, the packet states the contradiction as a Known Deviation and the listed text change does not happen. Backlog.
  - I have not added this.

## No ruling needed (recorded)

**Q5. L1 (`pipeline.md:109`) is closed in code.** CH-5a2b made `origin_selected` per Finding row at that row's cutoff (`estate/portfolio.py:595-598`, `action_segment_for` `:176`). `:126` records that the fix has no revert-failing test, owner CH-6b. Plan: one test in `test_w303_portfolio_workflow_labels.py` (two rows with different `_thread_cutoff` and a `_segment_at` map), then the revert proof.

**Q6. L5 (`:130`).** COH-17 and COH-18 report `{compared, skipped}` per rule in the report and the print-out, in the `lifecycle_pairs` manner (`:1140`). A stamped bundle with zero compared on either rule is a finding, so a vacuous pass cannot look clean.

**Q7. L2m.** Add to `test_ch6b_estate_postgres.py`: MG-1 judged on >= 3 COMPLETE days (`judge_month` over stored rows, recomputed) and the Optimize row on D13 reads the ACT-K1 verdict. No `late_fill` + `known_at` work (BL-08). **Template:** `mechanism_dataset.py status` reports `usable: false` for both variants on this checkout, so this test and L3m both need the one allowed rebuild (about 11 min). I run both straight after it, once, at the end. No guard M retirement (BL-08).

**Q8. Register and packet.** Add MD-CH6-5 as R707 only (R705 and R706 are MD-CH6-4 and MD-CH6-6). The packet lists MD-CH6-4/5/6 and closes `review-CH-6b2.md:78`. That review file exists only in the `AssetOpsV1-plan2` checkout, not on this branch; I read it there. Check for the inline MD-CH6-5 label at `vocabulary.py:286`; add it if missing.

**Q9. Old → new table and §B6.**
- Old = the values the CH-6b2 packet took from the bundle's `category_counts` (browser rules), re-read from this bundle. New = `cards` on this head, all windows.
- §B6 line: CH-9 was merged first (CH-9b3 `7a89f58f0`; CH-6b not yet complete), so the Kobo Potential part reads CH-9's study. To be confirmed from the L3 values at build.

## Sizing note

Q1-Q3 as recommended cost about 0.6 of the 1.0. Together with L2m, the L1 test and the packet this stays near 1.0. Q4 option A adds about 0.1.
