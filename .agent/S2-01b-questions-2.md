# S2-01b phase-2 questions for the Architect

Branch `task/S2-01b-durable-simulated-gateway`, phase-2 commits `79fbbf2`, `a8bd895` and the guard commit after them. Each question has a fail-closed default that is already built, and phase 3 can proceed on it.

## Q1. Non-terminating simulated readings versus V3 canonical decimals (material)

**Finding.** Phase 2 ran the real S2-01a registered KOBO-001 daytime Draft through the gateway.

- The run produced 293 public reports. 41 of them carry exact values that are non-terminating ratios.
  - 39 are `battery-pcs-controller/state-of-charge`, for example `1035/19`.
  - One is `battery-pcs-controller/ac-power`.
  - One is `pv-inverter-controller/ac-power`.
- `report_from_observation` passes `exact_decimal_text(Fraction)` through. The v1/v2 envelopes accept a ratio, but V3 forbids one (phase-1 Q-defaults, confirmed in `D-2026-10-08-s2-v3-source-payload-and-period-reference`). The gateway therefore holds each of these reports as `INVALID_VALUE` at `value`, and no sequence is allocated.
- The other 252 reports become envelopes in five source-specific batches.

**Options.**

1. **Keep holding them (built default).** This is truthful and fail-closed. The cost is that most SOC readings appear as holds in the Lab Stage.
2. **Quantize at the simulated device.** The public adapter publishes a finite decimal at a declared device resolution, for example a per-signal resolution in the publication profile or a fixed rule such as round-half-even to 6 places. The envelope still carries the device-published value; the device is the one that rounds. This needs the rule to be versioned, which means a publication-profile or adapter version and adapter vectors. The kernel/world value stays exact and private.
3. **Amend V3 to allow `n/d`.** This contradicts the confirmed V3 vectors, and real devices do not publish ratios.

**Recommendation.** Option 2, with the resolution declared per signal in the publication profile, so the "device published" claim is honest. It needs a decision on where the resolution lives and on whether it is S2-01b scope or an S2-01c/S2-02 carry. Until then phase 2 keeps option 1. Option 1 is pinned in `host/tests/test_registered_gateway_publication.py::test_a_registered_run_stages_source_specific_v3_batches_from_the_real_snapshot`, which asserts that the hold set is non-empty, is all `INVALID_VALUE/value`, and covers only ratio values.

## Q2. The registered daytime run does not report Kobo generator status

**Finding.**

- The registered request uses publication profile 3 (`simulator-lab-publication` v3). Profile 3 does not declare `generator-controller/status`.
- Profile 4 declares it but is not selectable in this build: `RunSetupRefused: No publication profile 'simulator-lab-publication' at version 4 exists in this build`.
- Fuel and irradiance are not reporting paths of the daytime model either.

So the run produces no ENUM report, although the snapshot binds status with the ENUM map (`FAILED/RUNNING/STARTING/STOPPED`).

**Built default.** The Architect asked phase 2 to prove an end-to-end Kobo ENUM report. `test_a_kobo_enum_report_travels_end_to_end_under_the_real_map` does this with public `DeviceObservation`s for `generator-controller/status`, adapted by `report_from_observation`, sent over the authenticated channel and admitted under the real registered snapshot:

- `RUNNING` and `STOPPED` become V3 MEASUREMENT envelopes with unit `state`.
- `running` is held as `INVALID_ENUM` at `value` and is not renamed.

The Lab run itself does not emit the report.

**Question.** Is that sufficient for S2-01b? The alternative is to make profile 4 (or a registered-Kobo profile) selectable for registered Drafts. That would change run setup, which is S2-01a's seam, and so it is not done here. **Recommendation:** accept the built default and carry the selectable status path to S2-02's demo configuration, which the packet already gives to S2-02.

## Q3. Publication-delay windows on a registered run (minor)

The legacy publisher models T026 publication-delay windows. The gateway path does not. A registered run whose reporting has delay windows is refused with a staging note, and nothing is staged early. Kobo daytime has none. **Recommendation:** keep the refusal and let S2-01c, which owns fault scenarios, add delayed admission.
