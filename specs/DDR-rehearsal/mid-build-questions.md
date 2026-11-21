# DDR mid-build questions

Questions raised during the build about something the spec did not fix. Count: 1, answered (reset at spec rev 2,
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
