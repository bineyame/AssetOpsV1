# W2-05a re-review (Run 8 fix round)

Reviewer: fresh Claude reviewer. Branch `task/W2-05a-ev-foundation`, head `164a1d1a`; scope is the r1 findings, judged against build spec "Run 8 rulings" and `git diff 3992b6e1..164a1d1a`.

## Verdict: ACCEPT

No High or Medium finding is open. Three points are PENDING-ARCHITECT and are not findings.

| Finding | Status | Evidence |
|---|---|---|
| H1 diagram and rail | CLOSED | `SiteSingleLineDiagram.tsx:1539-1660`: `feeders = 3`, slots Feeder 1/2/3 CB; slot 2 reads `Charger 2 · Not declared`, `Rating not declared · No connector declared`; extra chargers fold into slot 2 as "Additional chargers" with names; rail fixed Connector 1, Connector 2, Site meter, Billing system, ordered by charger/connector declaration index then asset id (no role or UUID order). Stocked 1440 capture matches the mock: three feeder slots, four-position rail, nothing clipped. 390 capture shows the same geometry scaled down (small but not clipped). Tests cover stocked, missing-feed, zero-charger, three-charger and reversed bindings. |
| M1 unavailable destinations | CLOSED | `EvFoundationViews.tsx:590,601,625,683`: Financials, Assumptions and Health > Data sources (header and footer) use `UnavailableLinkEntry`; no `Link` to those routes. Site model, Evidence and Single line diagram links stay live. Readiness capture shows "Financials · Not available yet" in the Next step cell, in the mock position. |
| M2 connector-free refusal | CLOSED | `binding_service.py:309-320`: code, empty binding index and exact message per ruling. Tests (`test_w205a_ev_foundation_postgres.py` after line 200) cover empty, Site-import-only and overlap with a connector-free revision, assert the specific code, empty `binding` and an unchanged `binding_sets` list; a valid set still publishes. Mutation was not run (blocked). Judged by reading: without the check, the empty and import-only requests would be refused for other reasons, so the code assertion fails; the overlap case with a complete set would publish, so `pytest.raises` fails. The tests are non-vacuous. |
| M3 v4 correlation | CLOSED | `source_envelope_v4.py:666-670`: docstring corrected; parser, 0020 and 0024 unchanged (diff confirms). Parser tests added in `test_source_envelope_v4.py`. |
| M4 no future publication | CLOSED | `ev_lab.py:61-63`: install clock used, `timedelta` removed; fixed-clock test asserts `recorded_at`, immediate read, later revision allowed, idempotent reinstall. |
| L1 | CLOSED | Panel 1 now 1.15x; 390 captures viewed, no clipping. |
| L2 | CLOSED | `missing-claim-scan.mjs:67-68` names the W2-05a placements; the exemption is not widened. |
| L3 | CLOSED | `foundation_parsing.py:198-201` `s` 0..86400, `kWh` 0..1e8; boundary and out-of-range tests, and a Postgres `EV_CONFIGURATION_INVALID` test for 1e300. |
| L4 | CLOSED subject to P2 | `EvFoundationViews.tsx:772`: ends `Load manager · Not declared`; `power sharing` deleted. Capture confirms. |
| L5 | CLOSED | Recorded in Run 8 M3 ruling. |

## PENDING-ARCHITECT (not findings)
1. `UnavailableLinkEntry` is a non-focusable `<li aria-label>` (`UnavailableEntry.tsx:46-53`); the ruling says "focusable". The builder kept the component and its existing contract.
2. Missing-feed L4 string is `Not declared; Load manager · Not declared`.
3. ev-sld viewBox widened 1000 to 1090. It fixed the clipping seen in the capture and is visually fine at 1440; the 390 diagram is small but legible as the previous one was.

## New unruled decisions
None beyond the three pending points. The builder reported each openly.

## Checks I ran
- `npm.cmd test -- src/sites/__tests__/evFoundation.test.tsx`: 24 passed.
- `npx.cmd tsc --noEmit`: exit 0.
- `tools/check-all.ps1` (plan2 venv Python): 10/10 guards passed.
- Not rerun: full backend (builder 2960 passed, 0 failed, 0 skipped), full frontend (builder 2252), Postgres EV tests (not rerun; read only).
