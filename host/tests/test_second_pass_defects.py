"""The four gaps T021's second independent pass found, through the real path.

The first four defects that review returned were about a kernel reinterpreting or
omitting things. These four are about the boundary a run is frozen at: a number
that survives it wrongly, a record that may omit what its version exists to carry,
a refusal that escaped as a 500, and an exclusion one notch too wide.

`.agent/T021-guard-probes.py` reverts each fix and asserts the matching test
fails. `.agent/T021-codex-second-pass-probes-rerun.py` runs the reviewer's own
reproductions against the corrected build.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from fixtures import (
    HYBRID_TEMPLATE,
    FakeRuns,
    FakeScenarios,
    FakeSites,
    draft,
    scenario,
    shipped_document,
    site_from_template,
)

from assetops_backend.runs.parsing import (
    parse_run_document,
    render_run_document,
)
from assetops_backend.runs.ports import RunConfigurationInvalid
from assetops_backend.runs.profiles import (
    LAB_PUBLICATION_PROFILE,
    MINIMAL_FUEL_TANK_MODEL,
)
from assetops_backend.runs.service import RunSetupService
from assetops_contracts.execution_contract import (
    EXECUTION_CONTRACT_VERSION,
    CanonicalValueNotRepresentable,
    canonical_fraction,
    frozen_canonical_value,
)

from execution_adapter import run_to_end

TANK = "fuel-tank-volume@fuel-tank"
PROJECTION_FIELDS = (
    "causes",
    "forcings",
    "declared_bounds",
    "reporting_path_conditions",
)


def _rate_document(rate: float, minutes: int = 60) -> dict:
    """The shipped removal, declared as a rate over a window.

    The one path where an authored number is multiplied after conversion, which is
    where the double normalization was.
    """
    document = shipped_document()
    for entry in document["timeline"]:
        if entry["event_id"] != "unaccounted-fuel-removal":
            continue
        entry["timing"]["duration_minutes"] = minutes
        entry["state_effect"] = {
            "direction": "DECREASE",
            "rate_parameter_id": "removal-rate",
        }
        entry["parameters"] = [
            {
                "parameter_id": "removal-rate",
                "display_name": "Rate fuel leaves the tank",
                "value": rate,
                "unit": "L/h",
                "execution_role": "CAUSAL_INPUT",
                "state_key": TANK,
                "execution_requirement": "REQUIRED",
                "ownership": {"owner": "SCENARIO_INPUT", "initializes": False},
            }
        ]
    return document


class TestARateIsNormalizedOnceAndOnlyOnce:
    """The numeric policy allows exactly one approximation, at the input boundary.

    The projection called a conversion that normalizes and returns a float, then
    normalized THAT float again before multiplying by the window's length. A
    millionth of a litre an hour became 1.67e-08, which normalizes to zero, and a
    valid removal reported COMPLETED having moved nothing.
    """

    @pytest.mark.parametrize(
        "rate",
        [0.000001, 1.000001, 14, 0.5, 123.456789],
    )
    def test_the_frozen_quantity_is_the_exact_integral(self, rate) -> None:
        definition = scenario(_rate_document(rate))
        executed = run_to_end(draft(definition=definition))

        cause = next(
            item
            for item in executed.inputs.causes
            if item.event_id == "unaccounted-fuel-removal"
        )
        expected = canonical_fraction(rate, "L/h")[0] * 60
        assert cause.quantity == expected, rate
        assert cause.quantity != 0

    def test_a_millionth_of_a_litre_an_hour_is_not_zero(self) -> None:
        """The reported case, pinned on its own.

        A millionth of a litre an hour over an hour is a millionth of a litre. It
        was zero, and the run said COMPLETED.
        """
        definition = scenario(_rate_document(0.000001))
        executed = run_to_end(draft(definition=definition))

        cause = next(
            item
            for item in executed.inputs.causes
            if item.event_id == "unaccounted-fuel-removal"
        )
        assert cause.quantity == Fraction(1, 1000000)

    def test_the_contract_helper_refuses_what_the_float_cannot_carry(
        self,
    ) -> None:
        """The residual, refused rather than frozen approximately.

        A frozen record stores a `float`. For every number this product freezes
        the round trip recovers the rational, because `limit_denominator` recovers
        any denominator within its limit. One outside it is refused: the
        alternative is a run carrying a number the document did not declare.
        """
        assert frozen_canonical_value(14, "L/h", times=Fraction(240))[0] == 56.0

        with pytest.raises(CanonicalValueNotRepresentable) as raised:
            # A millionth of a litre an hour over ONE minute is 1/60000000.
            frozen_canonical_value(0.000001, "L/h", times=Fraction(1))
        assert "1/60000000" in str(raised.value)
        assert "may not carry a number that is not the number" in str(
            raised.value
        )

    def test_a_quantity_effect_is_unaffected(self) -> None:
        """The control: the ordinary shipped removal still moves 120 L."""
        executed = run_to_end(draft())
        cause = next(
            item
            for item in executed.inputs.causes
            if item.event_id == "unaccounted-fuel-removal"
        )
        assert cause.quantity == Fraction(120)


class TestAVersionSixRecordCarriesTheProjection:
    """A record at this version carries what this version exists to carry.

    Absence used to mean empty for every run, on the reasoning that the contract
    version guard refuses an earlier one anyway. A run frozen AT the current
    version with `causes` deleted parsed, was READY, executed, and reported
    COMPLETED with the removal never happening; deleting `declared_bounds`
    overfilled the tank past its capacity. The version guard cannot help when the
    version is the current one.
    """

    @pytest.mark.parametrize("field", PROJECTION_FIELDS)
    @pytest.mark.parametrize("how", ["absent", "null"])
    def test_a_missing_projection_collection_is_refused(self, field, how) -> None:
        document = render_run_document(draft())
        if how == "absent":
            del document["deterministic_identity"][field]
        else:
            document["deterministic_identity"][field] = None

        with pytest.raises(RunConfigurationInvalid) as raised:
            parse_run_document(document, source="a hand-edited run")
        assert field in str(raised.value)
        assert f"version {EXECUTION_CONTRACT_VERSION}" in str(raised.value)
        assert "declare an empty list" in str(raised.value)

    def test_an_empty_list_is_still_a_real_answer(self) -> None:
        """A document declaring no causes is not a document that does not say.

        Without this the refusal above would be read as "the projection must be
        non-empty", which would refuse a legitimate scenario.
        """
        document = render_run_document(draft())
        document["deterministic_identity"]["reporting_path_conditions"] = []
        reloaded = parse_run_document(document, source="a run with no gap")
        assert reloaded.deterministic_identity.reporting_path_conditions == ()
        assert reloaded.execution_status == "READY"

    def test_a_run_below_this_version_may_carry_none_of_it(self) -> None:
        """Readback of an earlier run is preserved, which is the other half.

        Such a run is refused execution by the version guard, which is what makes
        an empty projection safe there and not here.
        """
        document = render_run_document(draft())
        for field in PROJECTION_FIELDS:
            del document["deterministic_identity"][field]
        document["deterministic_identity"]["profiles"][
            "execution_contract_version"
        ] = EXECUTION_CONTRACT_VERSION - 1

        earlier = parse_run_document(document, source="an earlier run")
        assert earlier.deterministic_identity.causes == ()
        assert earlier.execution_status == "READY"

    def test_a_zero_length_window_is_refused_at_the_parser(self) -> None:
        """The same class: an unclassified `ValueError` escaping mid-execution.

        The contract's span helper refuses a zero-length window, correctly, and a
        hand-edited record reached it during the run. It is refused where a
        document is read.
        """
        document = render_run_document(draft())
        document["deterministic_identity"]["causes"][0]["duration_minutes"] = 0
        with pytest.raises(RunConfigurationInvalid) as raised:
            parse_run_document(document, source="a hand-edited run")
        assert "zero or negative length is not a window" in str(raised.value)


class TestAnUnansweredMagnitudeBlocksRatherThanRaising:
    """A declared effect whose owner did not answer is a blocked run.

    The product has always blocked such a run - a different profile may answer -
    and the review's own control confirmed it by disabling the projection and
    getting `INITIAL_VALUE_NOT_RESOLVED`. Raising from the projection turned that
    into an HTTP 500 with nothing written.
    """

    def _unanswered(self) -> dict:
        """A `MODEL_RULE` magnitude the selected profile declares no rule for."""
        document = shipped_document()
        document["public_parameters"] = [
            parameter
            for parameter in document["public_parameters"]
            if parameter["parameter_id"] != "starting-fuel-level"
        ]
        removal = next(
            entry
            for entry in document["timeline"]
            if entry["event_id"] == "unaccounted-fuel-removal"
        )
        removal["parameters"][0]["ownership"]["initializes"] = True
        removal["parameters"][0]["ownership"]["owner"] = "MODEL_RULE"
        return document

    def test_the_run_is_blocked_and_names_the_address(self) -> None:
        record = draft(definition=scenario(self._unanswered()))

        assert record.execution_status == "BLOCKED"
        assert ("INITIAL_VALUE_NOT_RESOLVED", TANK) in [
            (reason.kind, reason.subject) for reason in record.blocking_reasons
        ]

    def test_the_cause_is_frozen_absent_rather_than_dropped(self) -> None:
        """Absent with the reason beside it, which is the established pattern.

        Dropping it would be the disappearance defect; raising was the 500. The
        record says a cause was declared and says nobody supplied its magnitude.
        """
        record = draft(definition=scenario(self._unanswered()))
        cause = next(
            item
            for item in record.deterministic_identity.causes
            if item.event_id == "unaccounted-fuel-removal"
        )
        assert cause.canonical_value is None
        assert cause.addressed_key == TANK
        assert cause.canonical_unit == "L"

    def test_an_absent_magnitude_with_no_reason_cannot_be_constructed(
        self,
    ) -> None:
        """The invariant, not the message.

        `SimulationRun` enforces for a cause what it has always enforced for an
        absent initial value: the thing that made it absent is on the run beside
        it, naming the same address.
        """
        from dataclasses import replace

        from assetops_backend.runs.models import SimulationRun

        record = draft(definition=scenario(self._unanswered()))
        with pytest.raises(ValueError) as raised:
            SimulationRun(
                run_id=record.run_id,
                lifecycle_status=record.lifecycle_status,
                execution_status="READY",
                created_at=record.created_at,
                deterministic_identity=replace(
                    record.deterministic_identity,
                    initialization_inputs=tuple(
                        replace(item, value=1.0, canonical_value=1.0)
                        for item in record.deterministic_identity.initialization_inputs
                    ),
                ),
                blocking_reasons=(),
                unsupported_optional_inputs=(),
            )
        assert "never converted into silence" in str(raised.value)

    def test_the_route_persists_a_blocked_run_rather_than_failing(self) -> None:
        """End to end, because a 500 is what a reader actually met.

        The setup service is driven directly rather than over HTTP: what the
        review measured was a 500 and zero records written, and what has to be
        true is a persisted BLOCKED run. The store is the evidence either way.
        """
        definition = scenario(self._unanswered())
        site = site_from_template(HYBRID_TEMPLATE, site_id="MG-001")
        store = FakeRuns()
        setup = RunSetupService(
            store,
            FakeSites((site,)),
            FakeScenarios((definition,)),
            model_profiles=(MINIMAL_FUEL_TANK_MODEL,),
            publication_profiles=(LAB_PUBLICATION_PROFILE,),
            now=lambda: "2026-09-27T09:00:00Z",
        )
        record = setup.create_draft_run(
            {
                "site_id": site.site_id,
                "foundation_version": site.foundation.version,
                "scenario_id": definition.scenario_id,
                "scenario_version": definition.version.scenario_version,
                "interval": {
                    "start_time": "2026-09-21T00:00:00Z",
                    "end_time": "2026-09-22T17:00:00Z",
                },
                "timestep_minutes": 15,
                "seed": 20260927,
                "model_profile": {
                    "profile_id": "minimal-fuel-tank",
                    "profile_version": 1,
                },
                "publication_profile": {
                    "profile_id": "simulator-lab-publication",
                    "profile_version": 1,
                },
                "run_inputs": [],
            }
        )

        assert record.execution_status == "BLOCKED"
        assert len(store.written) == 1
        # And it round-trips, because an absent magnitude has to persist.
        reloaded = parse_run_document(
            render_run_document(record), source="a stored blocked run"
        )
        assert reloaded.deterministic_identity == record.deterministic_identity


class TestExclusionIsAtTheAddressAndRoleGrain:
    """A model may model a state without modelling every role of it.

    This model moves a tank's stored volume and cannot have one FORCED, so a
    scenario forcing `fuel-tank-volume@fuel-tank` is correctly recorded unsupported
    at that role. Excluding the ADDRESS then suppressed the `CAUSAL_INPUT` role the
    model does support, and execution failed `INITIAL_STATE_UNANSWERED` for a stock
    the run genuinely carried.
    """

    def _mixed_roles(self) -> dict:
        document = shipped_document()
        document["timeline"].append(
            {
                "event_id": "optional-tank-forcing",
                "sequence": 9,
                "offset_minutes": 0,
                "entry_kind": "EVENT",
                "category": "EQUIPMENT",
                "description": "An optional forcing of a state this model can "
                "only cause.",
                "execution_role": "FORCING_INPUT",
                "state_key": TANK,
                "execution_requirement": "OPTIONAL",
                "timing": {"shape": "INTERVAL_WIDE"},
                "parameters": [
                    {
                        "parameter_id": "optional-forcing-value",
                        "display_name": "Optional tank forcing",
                        "value": 2,
                        "unit": "L",
                        "execution_role": "FORCING_INPUT",
                        "state_key": TANK,
                        "execution_requirement": "OPTIONAL",
                        "ownership": {
                            "owner": "SCENARIO_INPUT",
                            "initializes": False,
                        },
                    }
                ],
            }
        )
        document["timeline"].sort(key=lambda entry: entry["offset_minutes"])
        for index, entry in enumerate(document["timeline"], 1):
            entry["sequence"] = index
        return document

    def test_the_run_records_the_role_and_not_only_the_address(self) -> None:
        """The non-empty control: the exclusion really is recorded, at a role."""
        record = draft(definition=scenario(self._mixed_roles()))
        assert record.execution_status == "READY", record.blocking_reasons
        assert (TANK, "FORCING_INPUT") in [
            (item.addressed_key, item.execution_role)
            for item in record.unsupported_optional_inputs
        ]
        assert (TANK, "CAUSAL_INPUT") not in [
            (item.addressed_key, item.execution_role)
            for item in record.unsupported_optional_inputs
        ]

    def test_the_supported_role_at_the_same_address_still_executes(self) -> None:
        executed = run_to_end(draft(definition=scenario(self._mixed_roles())))
        trajectory = executed.trajectory

        assert trajectory.outcome == "COMPLETED", trajectory.failure
        assert trajectory.boundary_at(0).stock(TANK) == Fraction(430)
        assert trajectory.boundary_at(1545).stock(TANK) == Fraction("254.02")
        assert trajectory.final.stock(TANK) == Fraction(500)

    def test_the_unsupported_role_is_not_consumed(self) -> None:
        """The other half: excluded means excluded, in that role.

        The forcing declares 2 L over the whole interval. Nothing may read it - no
        exposure at any boundary, and a note saying which role was skipped.
        """
        executed = run_to_end(draft(definition=scenario(self._mixed_roles())))
        trajectory = executed.trajectory

        assert all(
            boundary.exposures_of(TANK) == () for boundary in trajectory.boundaries
        )
        assert any(
            TANK in note and "FORCING_INPUT" in note for note in trajectory.notes
        )

    def test_an_address_excluded_in_every_role_contributes_no_machine(
        self,
    ) -> None:
        """Topology asks a different question, and this is it.

        An address excluded in every role it appears in is not a machine this model
        works with, so it must not resolve a component. A site-scoped optional
        input is the case, and it is the R5 reproduction - it stays fixed.
        """
        document = shipped_document()
        document["public_parameters"].append(
            {
                "parameter_id": "an-optional-site-wide-value",
                "display_name": "An optional site-wide value",
                "value": 0.9,
                "unit": "L/kWh",
                "execution_role": "CAUSAL_INPUT",
                "state_key": "site:generator-specific-fuel-consumption",
                "execution_requirement": "OPTIONAL",
                "ownership": {"owner": "SCENARIO_INPUT", "initializes": True},
            }
        )
        executed = run_to_end(draft(definition=scenario(document)))
        assert executed.trajectory.outcome == "COMPLETED", (
            executed.trajectory.failure
        )
