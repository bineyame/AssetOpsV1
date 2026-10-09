# S2-01b phase 3a questions (fail-closed defaults built)

None of these blocks phase 3b. Each one is built at its fail-closed default.

## Q1. Selecting `registered-kobo-publication` for a legacy YAML Site (minor)

The profile states its resolution in registered binding source units, and a legacy Site has no binding to check them against.

**Built.** Setup refuses with `PUBLICATION_PROFILE_REQUIRES_REGISTERED_SITE`. The rule actually applies to any profile that declares a resolution, not to this id alone.

**Alternative.** Allow the profile and skip the unit check. **Recommendation:** keep the refusal, because the decision names registered Drafts only.

## Q2. Unit check scope (minor)

**Built.** All 8 numeric resolutions of the profile are frozen. The unit is compared only for signals that the registered binding set binds. A declared signal with no binding is not a reporting path of the run (`reporting_inputs` already drops it), so it has no source unit to disagree with.

**Alternative.** Refuse whenever a declared signal is unbound. That would refuse KOBO-001 for `fuel-level-sensor/fuel-level` if it is unbound, so it is not recommended.

## Q3. Delay-window regression shape (minor)

No publication profile that a registered Draft can select declares a delay state: v3 and the new v1 do not. So no real registered Draft can carry a delay window today.

**Built.** The focused regression `host/tests/test_registered_kobo_resolution.py::test_a_registered_run_with_a_delay_window_stages_nothing_and_says_so` injects a `PublicationDelayWindow` through a `_reporting_for` override on the real new-profile Draft and a real gateway process. It shows the note, no `activate`/`admit`/`seal`, an empty ledger and no file Stage. I proved it non-vacuous by disabling the refusal branch, which made the test fail.

A delay-capable registered profile belongs to S2-01c.

## Q4. Lab "true value = reported - bias" wording (3b note)

`contracts/assetops_contracts/lab_projection.py` (~l.253) tells a reader to subtract the bias from the reported value to recover the gap-hidden quantity. For a quantized signal that recovers the value only to within half a quantum (0.0000005).

**Built.** The docstring is not changed. 3b should not render an exact "reported - bias" equality claim for runs with a frozen resolution.
