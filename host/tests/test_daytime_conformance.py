"""T024 criterion 14 and the Lab surface for the daytime mini-grid.

The profile conformance half: the daytime model's advertised states are derived
from executable handlers, equal the product profile's declaration, and every
advertised pair is reached by a real run. The fuel profile's recorded
limitations stay limitations.

The Lab half: a Kobo Draft starts, steps and finishes through the composed
execution port, the projection carries the electrical world, and the artifact
round-trips at schema 3 while a schema-2 record still reads as what it
recorded.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from assetops_backend.runs.profiles import (
    DAYTIME_MINI_GRID_MODEL as DAYTIME_PROFILE,
    MINIMAL_FUEL_TANK_MODEL,
)
from assetops_simulator.packs.minigrid import DAYTIME_MINI_GRID_MODEL

from execution_adapter import model_for, run_to_end
from fixtures import draft
from kobo import kobo_draft
from lab_execution import (
    EXECUTION_ARTIFACT_SCHEMA_VERSION,
    HostLabExecution,
    YamlExecutionArtifacts,
)
from source_stages import JsonSourceStages

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class TestTheDaytimeProfileConforms:
    def test_the_derived_set_equals_the_product_profile_s_declaration(
        self,
    ) -> None:
        derived = {
            (state.state_key, state.scope, state.supported_roles)
            for state in DAYTIME_MINI_GRID_MODEL.advertised_supported_states()
        }
        declared = {
            (state.state_key, state.scope, state.supported_roles)
            for state in DAYTIME_PROFILE.supported_states
        }
        assert derived == declared
        assert len(derived) == 10
        assert (
            DAYTIME_MINI_GRID_MODEL.model_profile_id,
            DAYTIME_MINI_GRID_MODEL.model_profile_version,
        ) == (DAYTIME_PROFILE.model_profile_id, DAYTIME_PROFILE.model_profile_version)

    def test_every_advertised_pair_is_reached_by_a_real_run(self) -> None:
        # The overcast document carries the reserve override, which is the
        # only scenario entry that reaches the reserve's FORCING_INPUT role.
        run = kobo_draft("kobo-daytime-overcast")
        trajectory = run_to_end(run, model_for(run)).trajectory
        reached = {
            (
                DAYTIME_MINI_GRID_MODEL.handler_by_id(handler_id).state_key,
                DAYTIME_MINI_GRID_MODEL.handler_by_id(handler_id).role,
            )
            for handler_id in trajectory.handlers_exercised
        }
        assert reached == DAYTIME_MINI_GRID_MODEL.advertised_pairs()

    def test_the_model_needs_are_the_profile_s_bound_states(self) -> None:
        for need in DAYTIME_PROFILE.foundation_needs:
            state = DAYTIME_PROFILE.supported(need)
            assert state is not None and state.foundation_binding is not None


class TestFuelLimitationsDoNotBecomeElectricalSupport:
    def test_the_fuel_profile_still_models_no_demand_and_no_irradiance(
        self,
    ) -> None:
        for state_key in (
            "site-load-demand",
            "plane-of-array-irradiance",
            "load-demand",
            "battery-state-of-charge",
        ):
            assert MINIMAL_FUEL_TANK_MODEL.supported(state_key) is None
        assert MINIMAL_FUEL_TANK_MODEL.foundation_needs == ()
        assert MINIMAL_FUEL_TANK_MODEL.site_control_needs == ()

    def test_a_fuel_run_still_records_them_as_unsupported_optional_inputs(
        self,
    ) -> None:
        run = draft()
        recorded = {item.addressed_key for item in run.unsupported_optional_inputs}
        assert recorded == {
            "site:site-load-demand",
            "site:plane-of-array-irradiance",
        }
        assert run.deterministic_identity.model_needs == ()
        assert run.deterministic_identity.site_controls == ()

    def test_a_fuel_run_executes_the_fuel_model(self) -> None:
        run = draft()
        assert model_for(run).model_profile_id == "minimal-fuel-tank"
        trajectory = run_to_end(run, model_for(run)).trajectory
        assert trajectory.outcome == "COMPLETED"
        assert all(boundary.control_step is None for boundary in trajectory.boundaries)


def lab(tmp_path: Path) -> HostLabExecution:
    return HostLabExecution(
        artifacts=YamlExecutionArtifacts(tmp_path),
        stages=JsonSourceStages(tmp_path / "stages"),
    )


class TestTheLabShowsTheElectricalWorld:
    def test_a_kobo_draft_starts_steps_and_projects_the_electrical_world(
        self, tmp_path: Path
    ) -> None:
        run = kobo_draft("kobo-daytime-overcast")
        port = lab(tmp_path)
        started = port.start(run)
        assert started.electrical is None or started.electrical.steps == ()
        stepped = port.step(run, boundaries=10, from_boundary=0)
        electrical = stepped.electrical
        assert electrical is not None
        assert len(electrical.steps) == 10
        latest = electrical.latest
        assert latest.from_offset == 135
        assert {item.address for item in electrical.latest_loads} == {
            "load-demand@load-res",
            "load-demand@load-clinic",
            "load-demand@load-mill",
        }
        assert electrical.latest_requests[0].quantity == "battery-power"
        assert electrical.latest_controls[0].accepted == latest.battery_power
        assert "site-sources-and-sinks" in electrical.latest_balances

    def test_the_artifact_round_trips_at_schema_three(self, tmp_path: Path) -> None:
        run = kobo_draft("kobo-daytime-overcast")
        port = lab(tmp_path)
        port.start(run)
        finished = port.run_to_end(run)
        port.forget(run.run_id)
        reloaded = lab(tmp_path).projection(run)
        assert reloaded.status == "COMPLETED"
        assert reloaded.electrical == finished.electrical
        document = yaml.safe_load(
            (tmp_path / f"{run.run_id}.yaml").read_text(encoding="utf-8")
        )
        assert document["artifact_schema_version"] == EXECUTION_ARTIFACT_SCHEMA_VERSION == 3
        assert len(document["electrical"]["steps"]) == 48

    def test_a_schema_two_record_reads_as_what_it_recorded(
        self, tmp_path: Path
    ) -> None:
        """The previous build's layout: no electrical key, marker 2. Built by
        executing a real run and removing exactly what that build never wrote."""
        run = draft()
        port = lab(tmp_path)
        port.start(run)
        port.run_to_end(run)
        port.forget(run.run_id)
        path = tmp_path / f"{run.run_id}.yaml"
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert "electrical" in document
        del document["electrical"]
        document["artifact_schema_version"] = 2
        path.write_text(yaml.safe_dump(document), encoding="utf-8")

        reloaded = lab(tmp_path).projection(run)
        assert reloaded.status == "COMPLETED"
        assert reloaded.electrical is None

    def test_a_schema_three_record_missing_its_electrical_key_is_unreadable(
        self, tmp_path: Path
    ) -> None:
        run = draft()
        port = lab(tmp_path)
        port.start(run)
        port.run_to_end(run)
        port.forget(run.run_id)
        path = tmp_path / f"{run.run_id}.yaml"
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        del document["electrical"]
        path.write_text(yaml.safe_dump(document), encoding="utf-8")

        reloaded = lab(tmp_path).projection(run)
        assert reloaded.status == "ARTIFACT_UNREADABLE"
        assert "electrical" in " ".join(reloaded.notes)


class TestTheKernelKnowsNoPack:
    @pytest.mark.parametrize(
        "relative", ["kernel/execute.py", "kernel/model.py"]
    )
    def test_the_shared_kernel_names_no_electrical_pack_or_profile(
        self, relative: str
    ) -> None:
        source = (
            REPOSITORY_ROOT
            / "simulator"
            / "assetops_simulator"
            / relative
        ).read_text(encoding="utf-8")
        assert source, "nothing was read, so this proves nothing"
        for forbidden in (
            "packs.minigrid",
            "daytime-mini-grid",
            "model_profile_id ==",
            "battery",
            "load-demand",
        ):
            assert forbidden not in source, (relative, forbidden)
