# DDR mid-build questions

Questions raised during the build about something the spec did not fix. Count: 3 (MB1 answered; MB2 and MB3 open, defaults applied) (reset at spec rev 2,
2026-11-20).

## MB1 (Medium) `source_profile admit` does not print `admitted_by`

- **Evidence.** Spec §1 S2 and §6 say S2's output line holds `admitted_by` (R10, I5 cite `source_profile.py:60-66,124`).
  On `main` 3e77a8575, `admit` prints `_report(state, row)` (`backend/assetops_backend/source_profile.py:96-99`):
  `state, reader, version, sample_rows, profile_sha256, sample_sha256, expected_sha256`; no `admitted_by`. Only
  `source_profile list` prints it (`:124`). DDR may not change product code (§0), so the analyst has no way to fill
  `ADMITTED_BY` from the twelve listed commands.
- **Default applied (reversible, one line each).** Runbook section 6 runs `source_profile list --tenant lakeside-power`
  after `admit` and says to copy the `ddr-board-budget` line's `admitted_by`; ON1's `EXPECTED` holds thirteen commands
  (`"source_profile list"` after `"source_profile admit"`). Alternatives for the Architect: (a) keep this; (b) a
  one-key product change in `_report` (adds `admitted_by` to the admit line), outside DDR's file list.
- **Answer (coordinator, 2026-11-21): default accepted.** Runbook section 6 runs `source_profile list` after `admit`;
  ON1's `EXPECTED` keeps its thirteen entries. No product change.

## MB2 (Low) The admitted profile's stored status is `ILLUSTRATIVE`, not `ADMITTED`

- **Evidence.** Spec §2.2 G2 says the latest profile "is ADMITTED". `ADMITTED` is the `admit` command's output state
  (`source_profile.py` `_report`, 3A6 spec §2.8); the stored row's `status` is the profile file's own status, which
  3A6 requires to follow the database (`commercial/profiles.py:195`: `PINNED` with real data, else `ILLUSTRATIVE`;
  `ddr-board-budget.profile.json` says `ILLUSTRATIVE`). A row in `source_profile_latest` is the admission.
- **Default applied (one literal).** G2 checks the row exists (`PROFILE_MISSING`), then `status` equals the expectation
  file's `profile.status`, `"ILLUSTRATIVE"`, and version 1 (`PROFILE_STATE`). On an operator database the profile
  would be `PINNED` and the file would say so. No product change.

## MB3 (Medium) Tariff arrives with the emulated billing export, so four screen literals lose "tariff"

- **Evidence.** §3.4's not-available rows and Revenue texts come from 5c's World A, whose records have no tariff. The
  rehearsal loads 3A3's emulated billing export, which carries each line's tariff, so on the rehearsed database
  (test 1, S10's body) Tariff is filled and is not named as missing: the three Revenue drawer texts end "budget lines
  for energy delivered and productive-use price."; the billing row fills "Billing adjustments and Energy on unmapped
  meters"; the budget-lines row needs "budget lines for energy delivered and productive-use price" and fills "Energy
  delivered and Productive-use price". Every other compared key equals the transcription.
- **Default applied (reversible: four literals in `lakeside-2026-10.expect.json`).** The expectation file follows the
  rehearsed data for these four literals, written by hand from the rule (Tariff received, so not missing), not pasted
  from the body. Alternative: keep World A's wording and let G9 fail, which would make the rehearsal fail on a
  correct screen. No product change; the one-figure reading (D-WK.12) is unaffected.
