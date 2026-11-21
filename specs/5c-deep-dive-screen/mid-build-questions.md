# 5c mid-build questions

Questions raised during the build about something the spec did not fix. Count: 0 (reset at spec rev 2,
2026-11-20).

## Pre-flight batch (implementer, 2026-11-21, before code; none blocking, each proceeds on its default)

Every point below comes from the amendments that landed after rev 2 (SC-1a, 3A7 and 4a all merged). They are
code-reality reconciliations the amendments already direct, not open spec questions, so they do not count toward
the mid-build count. The Architect confirms them at review.

| # | Point | Default applied |
|---|---|---|
| PF1 | §2.2 `HEADINGS` key `ASSURE_RETURNS`; `CATEGORIES` has `ASSURE_PERFORMANCE` | Key `ASSURE_PERFORMANCE` (§2.2's own rename rule; handshake P2). The words come from SC-1 vocabulary `heading`. |
| PF2 | §2.3 `RECORDS` predates 4a. D-4A.12/.20/.24 say the 5c builder takes the change if 5c has not merged | Applied: METER_READS and LOSS_BAND are added after METER_REGISTER. TARIFF_SHEET and BILLING_ADJUSTMENTS are removed. RECORD_KEYS and NOTE_KEYS follow D-4A.12/.24. SC-1 vocabulary `record` is edited to match (a shared file outside §0's list, named by D-4A.12). §3.5's expected stop and not-available strings change by these rules only, and the packet lists each changed literal. |
| PF3 | §2.1's format functions vs SC-1's private `formats.py` (identical by D-SC1.10, plus D-SC1.24's "less than $0.01") | SC-1's slot formats. No World value hits the less-than rule. |
| PF4 | "Not available yet" without a period, as a cell or figure value (`common.not_available` has a period; `Evidence` refuses NOT_AVAILABLE) | A 5c statement for the bare value form. A NOT_AVAILABLE row is never made into an `Evidence` fact. |
| PF5 | D-SC1.21's digit and number-word ban hits §2.5: tile4 "Plan value, 12 months", "once decisions are recorded", "{n} budget disagreement(s)", BAD_MONTH "like 2026-10" | Same words on screen through slots: a `Count` with a new `month` noun (one/other) gives "12 months"; "once" becomes "when" ("…against doing nothing when decisions are recorded"; the only wording change); the disagreements use `Count` with noun `budget_disagreement`; BAD_MONTH uses an `example` slot, as 3A7's refusal does. |
| PF6 | Refusal body: §4.2 says `{"code","text"}`; the commercial router sends `{code, message, words, params}` | §4.2's `{"code","text"}` (the spec governs; the screen reads `text`). |
| PF7 | §3 "the snapshot's structure key and version": `PortfolioMonthSnapshot` has neither | `SITE_TYPE_TO_STRUCTURE["MINIGRID"]` and `REGISTRIES[key].version`, as `structure_snapshot/model.py:79-82` does. |
| PF8 | D-SC1.18/.26: `headline` becomes `{"text","evidence"}`, and the screen shows the evidence beside it | Done. MOCK DEVIATION MD10 (category: honesty rule, every figure carries its evidence class) gets a register row. |
| PF9 | The ADOPTED scan fails on lower-case value strings outside key context (`STEPS` "revenue", "om", "staff"; JSON values) in `words.py` and `view.py` | Code constants that are data, not prose, go in key context or in one constants module, `deep_dive/tables.py`, outside ADOPTED (one file added to §0's list). Every served string is a statement. |
| PF10 | World H's 4d helper is `LakesideInputs` (`test_4d_litre_split.py:560`), not `FakeInputs` | Use `LakesideInputs` (KOBO-OCT `kobo()`, V11 `v10(kobo())`). |
| PF11 | `MoneyStanding.text`/`details` and 3C2's `state_words` arrive already rendered by SC-1 | Passed through as given strings. |
| PF12 | SITE_SETUP words: §2.3 "one … one of each"; D-SC1.21 rewording | "a generator and a fuel tank declared in the Site's setup (litres are worked out for each)" (World H). |
