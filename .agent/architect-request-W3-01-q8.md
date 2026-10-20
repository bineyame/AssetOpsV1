# Architect request: W3-01 q8 (estate core readings)

Read:
- `.agent/W3-01-build-spec.md`, all rulings q1–q7;
- `.agent/W3-01-pending-rulings.md`, q8: 11 readings;
- `.agent/W3-01-phase-handoff.md`, including the fixture workarounds.

Code: branch `task/W3-01-estate-claim-action-roots` at `4cc54fb8`, covering `estate/*` and `estate_api.py`.

Confirm or replace each of the 11 readings with exact artifacts. These include:
- the cursor cutoff rule;
- the extra `amount_low`/`amount_high` keys on priced rows. Say whether they belong in the frozen wire, and if they do, record a versioned amendment.
- the cold/EV pending-work check at estate level.

Also rule the fixture workarounds:
- mutating `site_import.imported_at` inside tests;
- the EV q7 check comparing rows and IDs without the watermark;
- splitting the cold and EV tests into separate files.

Each is either acceptable or needs a named alternative.

Append the result as "Run 8 rulings (q8)" to `.agent/W3-01-build-spec.md`. Write nothing else. Do not commit.
