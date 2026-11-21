# 5c handoff (PARTIAL; unit 1 not finished)

Builder (Claude), 2026-11-21, branch `task/5c-deep-dive-screen`. Stopped at the context limit before tests.

## Unit 1

### Done (committed, untested)
- `backend/assetops_backend/i18n/statements/en/deep_dive.py`: every 2.5 sentence as statements. headline, compared,
  share and status_disagreement are copied exactly from SC-1 5.2/5.4. Figure-bearing statements are `served`; the
  payload carries the evidence word beside each figure. The catalogue loads (checked with a direct load).
- `i18n/statements/en/vocabulary.py`: `record` per D-4A.12/.20/.24 (METER_READS and LOSS_BAND added,
  TARIFF_SHEET and BILLING_ADJUSTMENTS removed); `headline_subject` gains a `label` form (the bridge title's
  "Cost and efficiency explain"); `noun` gains `month` (PF5, "12 months").
- `deep_dive/tables.py` (PF9 constants, outside ADOPTED), `deep_dive/words.py` (fact builders) and
  `deep_dive/view.py` (`month_view`, `AgreedAction(s)`). Never run against a world.

### Not done (next)
1. Tests 1-7 in `backend/tests/test_5c_deep_dive_view.py`, the cases in `backend/tests/statement_cases/deep_dive.py`
   (one per variant; T9 renders them), and the hand fixture `backend/tests/fixtures/5c/deep_dive_lakeside_2026-10.json`.
   The order was meant to be tests first. Because the code landed first, show the failing run by hiding
   `deep_dive/` (ImportError) or by running against the pre-code commit a864f186f.
2. Add `deep_dive/words.py` and `deep_dive/view.py` to `ADOPTED` in `tools/checks/statement_catalogue.py`, run
   the guard and fix its hits (expected: `"-"` split constants, `str(...)` on the bar, and IfExp lines).
3. Worlds: A = `test_5b_attribution.load_lakeside(new_world(), True)`, then `test_3b7a_structure_snapshot.setup(w)`,
   `builder.build(w["tid"], refs(w)[:3], OCT, built_by=BY)`, `reader(s).portfolio(...)`. D: `with_mto=False`.
   G: `refs(w)` (adds THIKA). E: `ingest_late`, read at 2026-11-21T10:00Z. H: `setup(w, fb=LitreLeafSource(
   test_4d_litre_split.LakesideInputs(), fallback(), lambda: AS_OF))`. F: another month; for the format-0 row,
   replace the store row.
4. Plants P1, P2, P4, P9, P11, P13-P17, with outcomes in `/opt/assetecon/evidence/5c/unit1/plants.txt`.
5. Packet, state entry, `Status: in_review`.

### Literals that differ from spec 3.5 (planned; check each against a run)
- `headline` is `{"text", "evidence"}` (PF8/D-SC1.18). A's evidence is ["Estimated"]: R is Estimated, and the
  weakest of Optimize's steps is Estimated.
- Revenue stop text (A) by D-4A.12: "Not split further until the billing export, a feeder meter export, a meter
  register with change dates, the customer meter reads for the month, the expected technical loss of each feeder,
  declared in the Site's setup, the productive-use tariff and budget lines for energy delivered, tariff and
  productive-use price." This is derived by hand from A's leaves. 4a may have changed which leaves are unobserved,
  so check it against a run.
- `not_available.rows` (A), in RECORDS order:
  - BILLING: Billing adjustments, Energy on unmapped meters and Tariff.
  - FEEDER_METER: Energy delivered, Technical losses and Unexplained losses.
  - METER_REGISTER: Unexplained losses and Energy on unmapped meters.
  - METER_READS: the same as METER_REGISTER.
  - LOSS_BAND: Technical losses and Unexplained losses.
  - PRODUCTIVE_TARIFF; EMS; FUEL_CURVE; TANK_DIPS; FUEL_DELIVERIES; OM_INVOICES (Kisiwa); then the budget-lines row.
  - TARIFF_SHEET and BILLING_ADJUSTMENTS rows are gone.
- tile4 line: "once" becomes "when" (PF5).
- A2: "...so they cannot be compared." ("two" is a number word, D-SC1.21; a new rewording, not in PF5).
- H: SITE_SETUP words per PF12 (already in the vocabulary).
- `standing` gains `details` (D-3A7.16). A's literal: text "Not yet reconciled: October 2026 (the organisation)
  does not match the management accounts within 1%."; details ["Fuel cost (Recorded and Emulated): the accounts
  say $5,100.00 and the records say $4,995.00, $105.00 less (2.06%), beyond the $51.00 allowed (1%)."] (SC-1 form).

### Questions (default applied)
- Q-U1.1: drawer `sites` and `by_site.rows` hold every Site in the JSON; the screen caps at 10 (unit 3). There is
  no "more" key.
- Q-U1.2: several stop sentences in one drawer cell are joined by a space through `tables.spaced()`, outside
  ADOPTED. Each part is a rendered statement.
- Q-U1.3: the untracked line lists each entry ("{factor} ({sites})", its own statement) as a `Name` inside
  `deep_dive.untracked`'s items.
- Q-U1.4: `share` and the other served figure statements put only `text` in the payload; the step's `word`
  carries the evidence.

### Owner rule 2026-11-21 (one figure, loyal to the operating world): not yet applied
Check it while writing tests 3-4. Candidates where it could change what the spec shows:
- The driver "Actual X · Target Y" details (World H litres: 730 L against 700 L, 330 L against 0 L). The targets
  are budget lines, not design values; keep them unless a target is a pack value.
- The carried O&M "$0.00 (estimate)". It is taken at its budget line; the owner rule may want "Not available
  yet" naming OM_INVOICES instead.
- World H's candidate litres (330 L). 0K4 says Kobo's stop-70 option reads "Not available yet" until the corrected
  model lands; that is 3C2's option value, not a 5c figure, but confirm.
Raise these with the coordinator before the fixture is fixed.

### Risks
- The view has never run; expect key or shape errors (`portfolio_lines.lines`, `Unit.exponents` names, Price units).
- `money_word` takes a `MoneyStanding`; a duck-typed Standing works because only `.reconciled` is read.
- Running the code needs the host venv: `tools/heavy-slot.sh --wait-seconds 3000 -- ...` per `backend/TESTING.md`.
