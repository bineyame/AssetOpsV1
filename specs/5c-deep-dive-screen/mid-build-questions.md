# 5c mid-build questions

Questions raised during the build about something the spec did not fix. Count: 1 (reset at spec rev 2,
2026-11-20; MBQ1 at unit 2).

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

## Mid-build (implementer, unit 2, 2026-11-21)

| # | Point | Default applied |
|---|---|---|
| MBQ1 | Spec 3.5 World A's standing text ends "within 1%." (unit 1's injected `NOT_MATCHED`, the fixture's `standing.text` and Assure drawer line). 3A7's `CommercialReconciliation.standing` on the Postgres world words the organisation standing with the statement's evidence: "... within 1% (Recorded)." (and "Reconciled: ... within 1% (Recorded)." for B). | The view passes 3A7's words through (PF11); nothing in 5c rewords them. Test 9 asserts 3A7's real literal and compares the rest of the payload with the fixture after that one substitution (`test_5c_deep_dive_postgres.py` `A_TEXT`). Unit 1's fixture and test 8 keep the spec literal, since their standing is injected. The Architect decides whether spec 3.5 and the fixture take "(Recorded)"; no screen code depends on it. |

## Mid-build (implementer, unit 3, 2026-11-21)

Each proceeds on its default; none blocks the screen. Count raised by these to 7 (MBQ2 to MBQ7 below, with MBQ1).

| # | Point | Default applied |
|---|---|---|
| MBQ2 | §5.2's 401 sentence "Sign in to see this operator's figures." against the served refusal text "Sign in to continue." (`person.person_required`) | The spec's sentence (screen copy, §5.2 binds); the served `text` is shown for every other refusal (503, 422). |
| MBQ3 | G3 asks for dark captures; the live product has no dark theme (`ui/tokens.css` defines none) | No page-local dark theme (one theme across the shell); the dark shots show the live light theme. A product dark theme is a token change for the UI lane. |
| MBQ4 | The guide's KPI size is 32 px; the live token for figures is 30 px (`--text-figure`, off the gate's scale) | KPI values at 24 px (`--font-size-700`, the mock's own size at 1280). |
| MBQ5 | vNEXT draws each step as a bar on the gap's scale; the JSON serves no plain decimals for steps (D-5C.2) | Rows without bars; the totals bar only. MD11 (R767), open for the Architect: a served position per step. |
| MBQ6 | The brief asks to serve from a `*_test` database built by the fixture path; the spec's gates answer the API from the fixture (`page.route`) | Gates and G3 captures from the World A fixture (gates through `page.route` on `vite preview` port 5571; `measure_screen.cjs` and the drawer shot through a scratch fixture server on 5572). A served backend on a `_test` database: not run (reason: unit 2's test 9 builds World A in a run-owned clone that is dropped after the test; no script keeps it for serving). |
| MBQ7 | Coordinator notes L2 (driver hierarchy) and L3 (where the 10-Site cap applies), Architect rulings pending | L2: `DeepDiveDriver.depth` (optional); a deeper driver nests inside the row above (`driverTree`), never beside its parent; absent depth is flat, as today's JSON. L3: the cap is on screen (`SITE_CAP` 10, `NOT_AVAILABLE_CAP` 8; the JSON holds all, spec §3.4); moving it to the JSON changes `Capped` only. |
