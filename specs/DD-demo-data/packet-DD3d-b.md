# DD3d-b review packet

Branch `task/DD3d-b-fuel-cost`. Scope and acceptance are in [DD3d](cards/DD3d.md) and D-DD.177–188. This packet supplements [the handoff](DD3d-b-handoff.md), which records the earlier runs.

## What changed

- Fuel used and invoiced fuel bought are separate figures. The Portfolio cost line describes the portion taken at budget and reconciliation names the amounts the accounts actually compare. Missing readings keep fuel and contribution unavailable. The Sites endpoint now handles a served period with no usable comparisons in the catalogue, API and UI.
- October run-rate plan litres are 295 for Kobo, 1,180 for Kisiwa and zero for Mto. Calculated from the prior quarter's tank and deliveries, with 10% contingency and one half-even rounding. The October board workbook, emulated budgets, manifest, derived values and demo fixtures follow that plan.
- The rehearsal served $4,431.60 contribution against $4,632.25, a $200.65 shortfall. Fuel used cost $2,006.40 against $1,902.75. The finance statement checks $1,540.00 of invoices. Kisiwa's fuel split moved five litres from candidate to necessary, with total use still 903 L.

## Acceptance evidence

- The no-readings rehearsal exercises Portfolio Month, Period and Sites against Postgres. All three return 200. Single-period and range tests cover unavailable money, preserved rows and missing-data reasons. Frontend estate suite passed 222 tests.
- The initial generated history and the history after the manifest update differ at 16 paths, all allowed by D-DD.187. The scope digests and jitter agree. All three notes checks and all three leaves checks passed. Final plan representation keeps the split derived, with unchanged pure run inputs. Two final history generations match byte for byte. Cold-chain and EV exports and their unwritten entries match. Evidence, including SHA-256 and path-level diff, is under `/opt/assetecon/evidence/DD3d/b/run6-codex/`.
- 305 affected simulator tests passed, with five pure replay cases deselected after the direct replay checks. The backend runs passed 342 focused tests and another 574 across the affected modules. The 53-test Postgres run passed 52, then the single stale 5c split fixture was repinned and passed on rerun. The DS4 database build and check passed.
- The statement catalogue, decision index and agent workflow passed. The design checker passed the updated anchors and data hashes. It still reports the walkthrough alignment findings and H9 baseline count from that check. No walkthrough was prepared.

## First review fixes

- The 5a and 5b comparisons use a separate October run-rate budget with independently stated inputs. The historical scenarios retain their original exact assertions. The real Postgres bridge test now confirms that books alone serve revenue and leave fuel and contribution unavailable under D-DD.177.
- G4 validates estimated evidence, the assumption marker and the declared diesel-price wording on a Site with no invoices. Four focused tests failed before the fix and passed afterward. A passing G4 logs the declared-price diagnostic in its facts. Both copies of the operator runbook describe the behavior.
- Verification after the fixes: 603 pure tests passed, one skipped. Six Postgres target and attribution tests and three Postgres rehearsal tests passed. Decision index, workflow, statement catalogue and architecture checks passed.
