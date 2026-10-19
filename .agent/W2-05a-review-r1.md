# W2-05a review (EV Foundation): independent first review

Reviewer: fresh Claude reviewer (not the author). Branch `task/W2-05a-ev-foundation`, head `c1d45bbf`. Code head `334c7c70`; `c1d45bbf` adds only the packet, which I verified with `git diff 334c7c70..HEAD`. Judged against `.agent/W2-05a-build-spec.md` (`D-2026-10-18-w2-05-buildspec`, including QA-QP, the Run-5 and Run-7 rulings), `.agent/W2-technical-design-ev.md` §0024, `D-2026-10-18-w2-mockup-authority`, `.agent/architect-W1-fidelity.md`, and `.ai/ROLE_CONFIG.md` ("Mockup drives the design; implementers never decide").

## Verdict: CHANGES

There is one High finding and four Medium findings. The backend core holds up well: vocabulary, typed state property, schedule validator, QC/QD topology, `ev-roles-1`, QG source ownership, the profile-scoped EV v4 table, QF legacy-tuple exclusion, the selected API, the QE cadence, the QH-QL fields and migration 0024. `ev-foundation` and `ev-readiness` match the mock structurally. The `ev-sld` diagram does not.

## Findings

### H1. The `ev-sld` diagram drops the mock's Charger 2 feeder slot, so the three-feeder geometry is lost
`frontend/src/sites/SiteSingleLineDiagram.tsx:1543`, `:1598`, `:1636`

- **What is wrong.** The code draws one feeder row per *declared* charger (`feeders = read.chargers.length + 1`), followed by the auxiliary feeder. EV-LAB-001 declares one charger, so the stocked capture `.agent/W2-05a-evidence/ev-sld-stocked-1440-app.png` shows only two feeder breakers: Charger 1 and Depot auxiliary. The mock has Feeder 1 CB → kWh → Charger 1, Feeder 2 CB → kWh → Charger 2, and Feeder 3 CB → Depot auxiliary. The empty selection, with zero chargers, would draw only the auxiliary feeder.
- **Why it matters.** Spec QN requires "Preserve the main and three feeder breaker slots and depot auxiliary as **Not declared**/unknown when absent." The parts table keeps its Charger 2 row as `Not declared`, so the diagram and the table also disagree with each other. Structural drift is High under the binding layout contract.
- **Secondary issue in the same panel.** The monitoring rail order comes from bindings sorted by role and then by asset UUID (`:1551`). The capture shows "Connector c2, Connector c1, Site import meter", where the mock has Connector 1, Connector 2, Site meter, Billing. The order depends on the UUIDs, so it can differ from one install to the next.
- **Fix.** Always draw the mock's two charger-feeder slots, plus the auxiliary slot. A slot with no declared charger shows a `Not declared`/unknown breaker, kWh box and charger glyph. More than two declared chargers fold into slot 2, as in the QP table rule. Order the rail by the declared connector order, then the Site meter, then Billing. Recapture `ev-sld` stocked, missing-role and empty at 1440 and 390.

### M1. Billing, tariff and Health links on `ev-readiness` are live links to routes no EV screen has
`frontend/src/sites/EvFoundationViews.tsx:590`, `:601`, `:625`, `:682`

- **What is wrong.** The spec (§ev-readiness) says billing and tariff "links are accessible unavailable entries until those routes exist". It also says that navigation links to unbuilt routes "remain accessible, noninteractive `Not available yet`". The build renders `Financials →`, `Assumptions →` and `Health › Data sources →` as live links (twice for Health).
- **Why it matters.** `SiteAnalyticsFrames.tsx:671` and the Health frames branch only on `COLDCHAIN`. An EV Site therefore lands on the mini-grid Financials, Assumptions and Health frames, which shows an EV user mini-grid-shaped screens. This is an unruled, user-visible deviation from the spec.
- **Fix.** Render these entries through the unavailable-entry pattern in their mock positions. Keep `Evidence →` and the Site model and Single line diagram links, because those routes exist.

### M2. An EV binding set can be published for a Site with no declared connector
`backend/assetops_backend/sites/binding_service.py:245-400` (`validate_bindings`, `publish`); `backend/assetops_backend/sites/ev_foundation.py:556`

- **What is wrong.** Spec Q3 and QE say: "A Site with no declared connector cannot publish a binding set." QE builds on that: Site import cadence "is never null on a published binding". No EV check refuses such a publication. A request carrying only `ev_site_import` on a declared METER passes the role, asset, ONE and v4 checks. `ev_foundation_document` then serves `cadence_seconds: null`, a state QE rules impossible.
- **Evidence.** This comes from reading the code. I did not reproduce it at runtime, and no test covers the case.
- **Fix.** In `validate_bindings`, for `ev-roles-1`, refuse when the covering Foundation declares no `EV_CONNECTOR`. Add a Postgres test that the refusal writes no revision.

### M3. Q8's v4 connector rule for the power and controller channels is not implemented, and the docstring claims behaviour the parser refuses
`contracts/assetops_contracts/source_envelope_v4.py:666-679` (docstring at `:667-668`); parser at `:269-270`

- **What is wrong.** Q8 says the power and controller interval channels "require connector and carry session when a session exists". The `_ev_connector` docstring says those channels "carry a session when one exists". The W2-00 parser does the opposite: it calls `_no_correlation` on `session_id` and `connector_id` for every non-delta measurement. The 0020 `accepted_evidence_measurement_ids` CHECK also forbids both IDs on non-`INTERVAL_DELTA` rows.
- **Why it matters.** A 05b producer that follows Q8 will have connector power, requested power and allocated limit rejected. The conflict between the spec and the existing contract was resolved silently in favour of the contract, with no Architect question raised.
- **Fix.** Raise this to the Architect. Either amend Q8 to "explicit-null session/connector; the binding supplies the connector", or authorise a profile-scoped parser change, which needs a CHECK change in 0024. Then correct the docstring and add a test pinning the ruled behaviour.

### M4. The ev-lab binding set is recorded five minutes in the future, but the spec does not require it
`backend/assetops_backend/sites/ev_lab.py:61`

- **What is wrong.** `install_ev_lab` publishes with `clock() + timedelta(minutes=5)`. I searched the build spec, the EV design and the task file: none mentions a future timestamp. The spec requires only `effective_from` = the Foundation's `valid_from` (Q6), which `publish_complete_bindings` does correctly.
- **Where it comes from.** The offset copies the `cold_lab.py:63` precedent from W2-02, so the dispatch's "as the spec requires" is not supported.
- **Observable effect.**
  - For five minutes after an operator install, the current read shows zero bindings and "Needs a source". The handoff confirms this ("wait 5 minutes before capture").
  - Any configuration change in that window is refused `FOUNDATION_CLOCK_BEHIND`.
- **Why it matters.** It is an implementer choice the spec did not fix, which is Medium under the owner's rule.
- **Fix.** Get an Architect ruling: either ratify the precedent in the spec, or publish at the import clock.

### L1. `ev-readiness` missing-role panel 1 is at 1.31x mock height
- I compared `ev-readiness-missing-role-1440-app.png` with the mock. The table has exactly the four QO rows and five columns, and each row is one line. The excess comes from the spec-required commissioning note and the "How this was worked out" disclosure under the table.
- The packet's phrase "extra Site-import row" is inaccurate: it is a detail line in row 1, not a row.
- This is within measurement noise of 1.30x, with no structural drift. I accept it, non-blocking.

### L2. The new attention-row "Not available yet" relies on an exemption whose recorded scope is tabs and chips
`frontend/src/ui/UnavailableEntry.tsx:46-53`; `tools/checks/missing-claim-scan.mjs:62-68`

- The only EV "Not available yet" is `UnavailableLinkEntry` ("Investigation action"). It is not a `<MissingClaim>` / `mock_gaps` placement. It passes the scan because it reuses the exempt const `IN_PAGE_UNAVAILABLE_STATUS`.
- That exemption's recorded reason names only "an unbuilt v69 in-page tab or lens chip". The spec says to extend "the declared guard only for entries actually present on these three mock screens", and the guard entry was not updated.
- The semantics fit the exemption, since this is an unbuilt destination rather than a missing Site claim.
- Fix: update the exemption's `reason`/`decision` to name the W2-05a attention-row entry.

### L3. No parser-wide range for the new `s` unit, and no `kWh` range
`backend/assetops_backend/sites/foundation_parsing.py:190`

- The spec says to extend `UNIT_RANGES`, but it was not changed.
- The EV validator enforces positivity and the cadence ceilings, but `ev-clock-error-bound: 1e300` would publish.
- Fix: add finite bounds for `s` and `kWh`.

### L4. Unruled wording in the `ev-sld` feed row
`frontend/src/sites/EvFoundationViews.tsx:774`

- The row reads "power sharing: Not declared". QM/QP rule the load-manager function as **Not declared**.
- This wording is harmless, but it was not ruled. The Architect should confirm it or give the exact text.

### L5. Migration 0024 interpretation should be recorded (no code change)
See the confirmation below. The Architect should write "EV measurement = `measurement='INTERVAL_DELTA'`" into the spec so 05b inherits it.

## Specific checks requested

1. **Spec conformance.**
   - Vocabulary, carriers and kinds match QB. Of the units, only `s` is new; `state`, `kWh` and `min` already existed.
   - The schedule shape, the shared `FOUNDATION_CONTENT_KEYS` and the open/bounded offset validation match Q5.
   - QC/QD topology refusals are implemented.
   - `ev-roles-1` has 8 roles with the Q2 required set. `IDENTITY_KWH` is closed to `ev_connector_energy`.
   - The EV v4 table has exactly 15 tuples. The legacy tuples carry role labels but are excluded from `simulator-lab-gateway-ev/1`, and the cold profile is unchanged.
   - The QG check compares UUIDs.
   - The selected API shape, the 401/403/404/422/503 refusals, `checked_at`, the QE minimum cadence and the QJ feed object are as specified.
   - The fixture values match the spec: 80 kW feed, 60 kW ratings, 0.001 kWh resolution and error bound, 1 min status and 5 min meter cadence, 30 s clock bound, `Etc/UTC`, Tuesday 08:00-16:00.
   - The gaps are H1, M1-M3 and L3.
2. **Five-minute timestamp.** Confirmed in code at `ev_lab.py:61`. It is not in the spec (M4). The fixture JSON carries only `effective_from: FOUNDATION_ORIGINAL_VALID_FROM`.
3. **Migration 0024.**
   - The predicate `family='MEASUREMENT' AND measurement='INTERVAL_DELTA'` is correct. Under the 0020 CHECKs, only `INTERVAL_DELTA` measurement rows carry `session_id`/`connector_id`, so this is exactly the set where the `(site_id, session_id, connector_id, source_time, id)` key is meaningful. `family='MEASUREMENT'` is redundant but harmless.
   - The downgrade filter on `measurement` alone is equivalent, because `accepted_evidence_ev_delta_shape` forces `family='MEASUREMENT'` for `INTERVAL_DELTA`. EV-site `INTERVAL_MEAN` rows (Site import) are not counted, but downgrade drops only an index, so nothing is lost. Accepted.
   - `down_revision` is `0023_w2_cold_consequence`. There is no configuration table. The 0020 CHECKs are untouched.
4. **Heights.** Foundation, readiness table, gateway and parts table are within 1.30x. The missing-role readiness table at 1.31x is accepted (L1). The SLD diagram's 0.87x hides the missing feeder slot (H1).
5. **"Not available yet" copy.** It is not routed through `<MissingClaim>`; see L2. No other new missing-capability copy appeared, and the scan passes.
6. **Numeric property bytes.** Confirmed. The numeric parse path is unchanged and `ev-connector-enabled` branches before it. `render_component_properties` is unchanged. `connector_enable_schedules` renders only when declared, so older Foundation bytes and digests are unchanged.

## Checks I ran (worktree `AssetOpsV1-review5`, code head `334c7c70`)

- **Focused backend tests.** Private DB `w205arev_test`, dropped afterwards; `PYTHONPATH` pointed at this worktree's `contracts`, because the venv's `assetops_contracts` resolves to the main checkout.
  - Files: `test_w205a_ev_migration.py`, `test_runs_api.py`, `test_w205a_ev_vocabulary.py`, `test_w205a_ev_roles.py`, `test_w205a_ev_foundation_postgres.py`, `test_w205a_ev_foundation_api_postgres.py`.
  - Result: **149 passed**, 0 skipped. `test_runs_api.py` passes because `var/sites/mg-001.yaml` is now present.
- **Adjacent tests.** `test_w200_source_events_postgres`, `test_w203_cold_migration_postgres`, `test_w204_cold_migration`, `test_w201_cold_vocabulary`, `test_w201_cold_foundation_postgres`, `test_s1_bindings_postgres`, `test_w202_cold_replay_postgres`, `gateway/tests/test_source_envelope_v4.py`: **167 passed** in 238 s.
- **`npx.cmd tsc --noEmit`:** exit 0.
- **`npx.cmd vitest run src/sites/__tests__/evFoundation.test.tsx`:** **22 passed**. It ran under this session. I did not run the full vitest suite or the build.
- **`tools/check-all.ps1`** with the plan2 venv Python: **10/10 passed**. The missing-claim scan reports 39 tagged placements and 10 baselined.
- **Not rerun, per the dispatch:** the full backend suite (builder: 2944, 1 environmental failure, then 28/28 for `test_runs_api`) and the host suite (builder: 708).

## Writer-guard probes

The incomplete `tools/writer_guard_probes.py` run should **not block**. It is a mutation corpus for the rule-8 guard itself, and this branch changes no guard code (`git diff main...HEAD -- tools/` is empty). 05a also adds no SQL writer or table: EV configuration goes through the existing Foundation and binding store, and the architecture guard passes in check-all. Record the full run as a follow-up for a quiet window, or have the Architect waive it for this slice.

## Residual risk not named in the packet

- The M3 conflict will surface in 05b as rejected connector-power, requested-power and allocated-limit envelopes if Q8 is followed literally.
- `ev-sld-missing-role` captures were not retaken after the run-6/7 compaction, and all `ev-sld` captures need retaking after H1.
- The 403/503 states are proved only in jsdom.
