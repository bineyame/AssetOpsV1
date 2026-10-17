"""W2-02: the host dispatches the frozen cold pair explicitly (`D-2026-10-17-w2-02-buildspec`).

A run that froze `cold-thermal/1` + `cold-publication/1` never resolves a ModelSpec, injected or not; a
half-cold pair is refused rather than resolved to either path; every older pair is unchanged.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from fixtures import draft

from execution_adapter import (
    FrozenRunNotReconstructible,
    execution_path,
    model_for,
    publication_profile_for,
)
from lab_execution import HostLabExecution, LabControlRefused
from source_stages import JsonSourceStages
from assetops_simulator.packs.fuel import MINIMAL_FUEL_MODEL


def with_pair(run, model: tuple[str, int], publication: tuple[str, int]):
    identity = run.deterministic_identity
    profiles = replace(
        identity.profiles,
        model_profile_id=model[0], model_profile_version=model[1],
        publication_profile_id=publication[0], publication_profile_version=publication[1],
    )
    return replace(run, deterministic_identity=replace(identity, profiles=profiles))


COLD = (("cold-thermal", 1), ("cold-publication", 1))


def test_cold_pair_never_resolves_a_model_spec() -> None:
    run = with_pair(draft(), *COLD)
    assert execution_path(run) == "COLD"
    with pytest.raises(FrozenRunNotReconstructible):
        model_for(run)
    assert publication_profile_for(run).publication_profile_id == "cold-publication"


@pytest.mark.parametrize(
    "pair",
    [
        (("cold-thermal", 1), ("lab-publication", 3)),
        (("minimal-fuel-tank", 1), ("cold-publication", 1)),
        (("cold-thermal", 2), ("cold-publication", 1)),
    ],
)
def test_half_cold_pair_is_refused(pair) -> None:
    run = with_pair(draft(), *pair)
    with pytest.raises(FrozenRunNotReconstructible):
        execution_path(run)
    with pytest.raises(FrozenRunNotReconstructible):
        model_for(run)
    with pytest.raises(FrozenRunNotReconstructible):
        publication_profile_for(run)


def test_older_pair_still_resolves_its_model() -> None:
    run = draft()
    assert execution_path(run) == "MODEL_SPEC"
    assert model_for(run).model_profile_id == run.deterministic_identity.profiles.model_profile_id


def test_lab_never_uses_an_injected_model_for_a_cold_run(tmp_path: Path) -> None:
    lab = HostLabExecution(model=MINIMAL_FUEL_MODEL, stages=JsonSourceStages(tmp_path / "stages"))
    with pytest.raises(LabControlRefused):
        lab._model_for(with_pair(draft(), *COLD))
    assert lab._model_for(draft()) is MINIMAL_FUEL_MODEL
