"""D-DD.75: the kernel's forcing index changes no trajectory (parity golden from main's kernel).

`host/tests/fixtures/kernel_forcing_index_parity.json` maps each case id to the `PrivateTrajectory.content_digest` the
kernel produced BEFORE the index (written on `task/DD3a-mini-reality` while `simulator/assetops_simulator/kernel`
equalled main's). Every case runs here through today's kernel and must give the same digest.

Cases (D-DD.75): K1-K8 `kobo_season.base_run(2, version=N)` through `frozen_world_inputs` (by `season_inputs`) and `model_for`; D1 the first
run of `test_daytime_mini_grid.py`; F1 the first run of `simulator/tests/test_fuel_trajectory.py`; X1 the
`FORCING_VALUE_AMBIGUOUS` case of `simulator/tests/test_execution_failures.py`; W1 the DD3 writer's Kobo 7 days from
2026-07-01 with the tank set to 2500 L here; S1 K8 advanced one boundary at a time.

Regenerating a golden digest (only when a case's INPUTS move, never for a kernel change) runs main's kernel:
`python host/tests/test_kernel_forcing_index_parity.py --reference main [CASE ...]` loads `kernel/execute.py` from that
revision as a separate module and rewrites the named entries.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPOSITORY = HERE.parents[1]
if __name__ == "__main__":  # the same paths `host/conftest.py` gives pytest
    for extra in (HERE, HERE.parent, REPOSITORY / "simulator", REPOSITORY / "contracts", REPOSITORY / "backend"):
        sys.path.insert(0, str(extra))

from assetops_contracts.world_inputs import ForcingInput  # noqa: E402
from assetops_simulator.kernel import execute as current_kernel  # noqa: E402
from assetops_simulator.packs.fuel import MINIMAL_FUEL_MODEL  # noqa: E402
from assetops_simulator.packs.mini_grid import MINI_GRID_V8_MODEL  # noqa: E402

GOLDEN = HERE / "fixtures" / "kernel_forcing_index_parity.json"
KERNEL_PATH = "simulator/assetops_simulator/kernel/execute.py"
ONBOARDING = REPOSITORY / "backend/tests/fixtures/on1/lakeside-power.onboarding.json"
BINDINGS = REPOSITORY / "backend/conversions/world"


def _simulator_conftest():
    spec = importlib.util.spec_from_file_location("_parity_simulator_conftest", REPOSITORY / "simulator/tests/conftest.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _kobo_case(version: int):
    from execution_adapter import model_for
    from kobo_assumed import assumed_site
    from kobo_season import base_run, season_inputs, season_site

    def site(document) -> None:  # v8 needs the assumed rows (`test_0k4a_dispatch_v8.site`), as 0K4a runs it
        season_site(document)
        if version == 8:
            assumed_site(document)

    run = base_run(2, version=version, site_edit=site)
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    # `season_inputs` is `frozen_world_inputs` plus the season's two days of forcings (as 0K4a runs it); the bare
    # frozen inputs carry the scenario's first 8 hours only and every version fails at 480 min on the sun.
    return season_inputs(run, 2), model_for(run)


def _daytime_case():
    from execution_adapter import frozen_world_inputs, model_for
    from kobo import kobo_draft

    run = kobo_draft("kobo-daytime")
    assert run.execution_status == "READY"
    return frozen_world_inputs(run), model_for(run)


def _fuel_case():
    return _simulator_conftest().world_inputs(), MINIMAL_FUEL_MODEL


def _ambiguous_case():
    conftest = _simulator_conftest()
    inputs = conftest.world_inputs()
    second = ForcingInput(
        event_id="generator-run-window", address=conftest.GENERATOR, state_key="generator-output-power",
        parameter_id="second-declared-output", value=Fraction(18), canonical_unit="kW", dimension="POWER",
        shape="WINDOW", offset_minutes=1080, duration_minutes=240, requirement="REQUIRED")
    return replace(inputs, forcings=inputs.forcings + (second,)), MINIMAL_FUEL_MODEL


#: W1's books, fixed here so that the case moves only with the writer's own rules: July as `history.json` states it
#: for Kobo at DD3a's start, and two 400 L notes inside the 7 days.
W1_BOOKS = {
    "months": {"2026-07": {"delivered_kwh": 8592, "unexplained_l": 12}},
    "fuel_notes": [{"at": "2026-07-01T10:00:00+03:00", "litres": 400},
                   {"at": "2026-07-05T10:00:00+03:00", "litres": 400}],
    "day_weights": {"classes": {"WD": [1, 2, 3, 4, 5], "SA": [6], "SU": [7]}, "WD": "1.00", "SA": "0.97", "SU": "0.90"},
}

#: W1's Kobo equipment rows, set here (replacing any the /2 file carries), so commit 2's data-sheet write does not
#: move the case: tank 2500 L (D-DD.76) and the three curve properties at the slot's values.
W1_ROWS = {
    "FUEL_TANK": [("tank-capacity", "2500", "L")],
    "GENERATOR": [("generator-no-load-fuel-rate", "0.62", "L/h"), ("generator-minimum-load", "30", "%")],
    "BATTERY": [("battery-charge-taper-start", "95", "%")],
}


def _writer_case():
    from assetops_simulator.world import telemetry as tel

    onboarding = json.loads(ONBOARDING.read_text(encoding="utf-8"))
    bindings = {code: json.loads((BINDINGS / f"{code}-bindings.json").read_text(encoding="utf-8"))
                for code in ("KISIWA-001", "KOBO-001", "MTO-001")}
    kobo = copy.deepcopy(next(s for s in tel.site_inputs(onboarding, bindings)["sites"] if s["code"] == "KOBO-001"))
    for component in kobo["foundation"]["components"]:
        for key, value, unit in W1_ROWS.get(component["type"], ()):
            component["properties"] = [p for p in component["properties"] if p["property_key"] != key]
            component["properties"].append({"property_key": key, "value": value, "unit": unit})
    return tel.frozen_inputs(kobo, W1_BOOKS, "2026-07-01", "2026-07-07"), MINI_GRID_V8_MODEL


RUN_ID = "run-" + "0" * 32  # a draft's run id is random; the digest covers it, so every case pins it


def _pinned(builder):
    def build():
        inputs, model = builder()
        return replace(inputs, run_id=RUN_ID), model
    return build


BUILDERS = {
    **{f"K{n}": _pinned(lambda n=n: _kobo_case(n)) for n in range(1, 9)},
    "D1": _pinned(_daytime_case),
    "F1": _pinned(_fuel_case),
    "X1": _pinned(_ambiguous_case),
    "W1": _pinned(_writer_case),
}
CASES = (*BUILDERS, "S1")


def digest(case: str, kernel=current_kernel) -> str:
    if case == "S1":  # K8, one boundary at a time
        inputs, model = BUILDERS["K8"]()
        execution = kernel.start(inputs, model)
        while not execution.is_terminal:
            execution.advance(1)
        return execution.trajectory().content_digest
    inputs, model = BUILDERS[case]()
    return kernel.execute(inputs, model).content_digest


def _golden() -> dict[str, str]:
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES)
def test_every_case_gives_main_kernels_digest(case: str) -> None:
    assert digest(case) == _golden()[case]


def test_s1_stepped_equals_k8_batched() -> None:
    golden = _golden()
    assert golden["S1"] == golden["K8"]


def _reference_kernel(revision: str):
    source = subprocess.run(["git", "show", f"{revision}:{KERNEL_PATH}"], cwd=REPOSITORY, check=True,
                            capture_output=True, text=True).stdout
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
        handle.write(source)
    spec = importlib.util.spec_from_file_location("assetops_simulator.kernel._parity_reference", handle.name)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their module by name
    spec.loader.exec_module(module)
    Path(handle.name).unlink()
    return module


if __name__ == "__main__":
    arguments = sys.argv[1:]
    if len(arguments) < 2 or arguments[0] != "--reference":
        raise SystemExit("usage: --reference REVISION [CASE ...]")
    reference = _reference_kernel(arguments[1])
    names = arguments[2:] or list(CASES)
    table = _golden() if GOLDEN.exists() else {}
    for name in names:
        table[name] = digest(name, reference)
        print(name, table[name])
    GOLDEN.write_text(json.dumps(dict(sorted(table.items())), indent=2) + "\n", encoding="utf-8")
