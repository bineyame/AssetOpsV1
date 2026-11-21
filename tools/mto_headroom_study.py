"""0M: the demand-on-headroom study on the declared simulated Mto season (spec §4 "The 61-day study"). No database.

    python tools/mto_headroom_study.py --days 61 --out /opt/assetecon/evidence/0M/<run>/study.json

Builds the Mto season (`host/tests/mto.py` on `host/tests/kobo_season.py`), runs it on the kernel as the site,
publishes its series, freezes the reduced run at 25 kW, and runs `headroom_study` through `HostForwardReplay` with
(HULLER, WELDER), the reduced capacity and the default `min_days`. Every figure is SIMULATED input and MODELLED
evidence; CALIBRATED on SIMULATED input is adapter fidelity (the replay path follows the kernel run that made the
series), not a match of the model to a Site. Every printed line carries both labels; the JSON header carries both and
the plant note. Nothing here is a price, and no design value is changed (owner-away row 37).

Exit 0 done, 2 refused (`<CODE> <subject>` on stderr).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for part in ("host", "host/tests", "backend", "contracts", "simulator"):
    sys.path.insert(0, str(ROOT / part))

from assetops_backend.runs.headroom_replay import HeadroomRefused, ReducedCapacity, headroom_study  # noqa: E402
from assetops_backend.runs.replay_study import (  # noqa: E402
    StudyRefused,
    dates_below,
    dawn_outcome,
    step_local_times,
    study_days,
)
from assetops_contracts.forward_replay import ForwardReplayRefused  # noqa: E402
from assetops_simulator.kernel.execute import execute  # noqa: E402

from execution_adapter import model_for  # noqa: E402
from forward_replay import HostForwardReplay  # noqa: E402
from kobo_season import observed_series  # noqa: E402
from mto import (  # noqa: E402
    HULLER,
    MTO_FRAME,
    MTO_PLANT_NOTE,
    MTO_REDUCED_INVERTER_KW,
    WELDER,
    mto_base_run,
    mto_season,
)

LABELS = "input_class=SIMULATED evidence_class=MODELLED"
NOTE = ("CALIBRATED on SIMULATED input is adapter fidelity: the replay path follows the kernel run that made the "
        "series; it is not a match of the model to a Site")


def say(text: str) -> None:
    print(f"{LABELS} {text}", flush=True)


def number(value: Fraction | None) -> dict | None:
    if value is None:
        return None
    return {"exact": f"{value.numerator}/{value.denominator}", "reading": f"{float(value):.3f}"}


def months(figures) -> list[dict]:
    return [{"month": m.month, "days": m.days, "value": number(m.value)} for m in figures]


def dawn_json(outcome) -> dict:
    return {"dawn_days_below": outcome.dawn_days_below, "worst_dawn_soc_pct": number(outcome.worst_dawn_soc_pct),
            "dawn_verdict": outcome.dawn_verdict, "new_dawn_days_below": list(outcome.new_dawn_days_below),
            "cleared_dawn_days_below": list(outcome.cleared_dawn_days_below)}


def demand_json(d) -> dict:
    return {
        "case_id": d.case_id, "customer_id": d.customer_id, "evidence": d.evidence, "capacity": d.capacity,
        "input_class": d.input_class, "evidence_class": d.evidence_class,
        "customer_days": len(d.customer_days), "customer_kwh": number(d.customer_kwh),
        "customer_kwh_by_month": months(d.customer_kwh_by_month),
        "days_without_headroom": list(d.days_without_headroom),
        "days_without_headroom_by_month": months(d.days_without_headroom_by_month),
        "kwh_beyond_headroom": number(d.kwh_beyond_headroom),
        "kwh_beyond_headroom_by_month": months(d.kwh_beyond_headroom_by_month),
        "extra_fuel_l": number(d.extra_fuel_l), "extra_fuel_l_by_month": months(d.extra_fuel_l_by_month),
        "extra_generator_kwh": number(d.extra_generator_kwh), "extra_unserved_kwh": number(d.extra_unserved_kwh),
        "extra_starts": d.extra_starts, "extra_running_steps": d.extra_running_steps,
        "litres_per_customer_kwh": number(d.litres_per_customer_kwh),
        **dawn_json(d),
    }


def capacity_json(c) -> dict:
    return {
        "case_id": c.case_id, "input_class": c.input_class, "evidence_class": c.evidence_class,
        "inverter_limit_kw": number(c.inverter_limit_kw),
        "extra_fuel_l": number(c.extra_fuel_l), "extra_fuel_l_per_day": number(c.extra_fuel_l_per_day),
        "extra_fuel_l_by_month": months(c.extra_fuel_l_by_month),
        "extra_generator_kwh": number(c.extra_generator_kwh), "extra_unserved_kwh": number(c.extra_unserved_kwh),
        **dawn_json(c),
    }


def baseline_dawn(result, observed) -> dict | None:
    """The no-action dawn readings (0K2's helpers), beside which every case's new and cleared dates are read."""
    if result.status != "CALIBRATED":
        return None
    readings, below, worst, verdict = dawn_outcome(result.projections[0], study_days(observed, MTO_FRAME),
                                                   step_local_times(observed, MTO_FRAME), MTO_FRAME)
    return {"dawn_days_below": below, "worst_dawn_soc_pct": number(worst), "dawn_verdict": verdict,
            "dates_below": list(dates_below(readings, MTO_FRAME)),
            "below": [{"date": r.local_date, "soc_pct": number(r.soc_pct), "generator_state": r.generator_state}
                      for r in readings if r.soc_pct < MTO_FRAME.dawn_min_soc_pct]}


def study(days: int, out: Path) -> int:
    say(NOTE)
    say(f"plant={MTO_PLANT_NOTE!r}")
    began = time.monotonic()
    run = mto_base_run(days)
    reduced_run = mto_base_run(days, inverter_limit_kw=MTO_REDUCED_INVERTER_KW)
    for name, item in (("full", run), ("reduced", reduced_run)):
        if item.execution_status != "READY":
            raise SystemExit(f"the {name} Mto run is {item.execution_status}")
    trajectory = execute(mto_season(run, days), model_for(run))
    if trajectory.outcome != "COMPLETED":
        raise SystemExit(f"the site run ended {trajectory.outcome}: {trajectory.failure}")
    observed = observed_series(trajectory, len(trajectory.boundaries) - 1)
    site_seconds = time.monotonic() - began
    began = time.monotonic()
    try:
        result = headroom_study(HostForwardReplay(), run, observed, (HULLER, WELDER), MTO_FRAME,
                                reduced=ReducedCapacity(reduced_run, MTO_REDUCED_INVERTER_KW))
    except (HeadroomRefused, StudyRefused, ForwardReplayRefused) as refused:
        print(f"{refused.code} {refused.subject}", file=sys.stderr)
        return 2
    replay_seconds = time.monotonic() - began
    calibration = result.calibration
    document = {
        "input_class": result.input_class, "evidence_class": result.evidence_class, "plant": MTO_PLANT_NOTE,
        "note": NOTE,
        "study": "0M demand-on-headroom study on the declared simulated Mto season (host/tests/mto.py)",
        "base_run_id": result.base_run_id, "status": result.status, "window_start": result.window_start,
        "days": result.days, "steps": len(observed.pv_available_kw),
        "site_runs": 1, "replays": len(result.projections),
        "site_seconds": round(site_seconds, 1), "replay_seconds": round(replay_seconds, 1),
        "baseline_fuel_l": number(result.baseline_fuel_l),
        "site_fuel_l": number(observed.start_fuel_l - trajectory.boundaries[-1].stock("fuel-tank-volume@fuel-tank")),
        "baseline_dawn": baseline_dawn(result, observed),
        "calibration": None if calibration is None else {
            "admissible_days": len(calibration.admissible_days),
            "generator_kwh_site": number(calibration.generator_kwh_site),
            "generator_kwh_replayed": number(calibration.generator_kwh_replayed),
            "starts_site": calibration.starts_site, "starts_replayed": calibration.starts_replayed,
            "soc_mae_points": number(calibration.soc_mae_points), "failed": list(calibration.failed),
            "input_class": calibration.input_class, "evidence_class": calibration.evidence_class,
        },
        "demand": [demand_json(d) for d in result.demand],
        "capacity": None if result.capacity is None else capacity_json(result.capacity),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, indent=1), encoding="utf-8")
    say(f"status={result.status} days={result.days} replays={len(result.projections)} "
        f"site_seconds={site_seconds:.1f} replay_seconds={replay_seconds:.1f} out={out}")
    if result.baseline_fuel_l is not None:
        say(f"case=baseline fuel_l={float(result.baseline_fuel_l):.3f}")
    if calibration is not None:
        say(f"calibration generator_kwh site={float(calibration.generator_kwh_site):.3f} "
            f"replayed={float(calibration.generator_kwh_replayed):.3f} starts site={calibration.starts_site} "
            f"replayed={calibration.starts_replayed} soc_mae={float(calibration.soc_mae_points):.4f} "
            f"failed={','.join(calibration.failed) or '-'}")
    for d in result.demand:
        by = {m.month: m.value for m in d.extra_fuel_l_by_month}
        say(f"case={d.case_id} evidence={d.evidence} customer_days={len(d.customer_days)} "
            f"customer_kwh={float(d.customer_kwh):.3f} days_without_headroom={len(d.days_without_headroom)} "
            f"kwh_beyond_headroom={float(d.kwh_beyond_headroom):.3f} extra_fuel_l={float(d.extra_fuel_l):.3f} "
            f"extra_fuel_l_by_month={','.join(f'{m}:{float(v):.3f}' for m, v in sorted(by.items()))} "
            f"extra_generator_kwh={float(d.extra_generator_kwh):.3f} "
            f"extra_unserved_kwh={float(d.extra_unserved_kwh):.3f} extra_starts={d.extra_starts} "
            f"dawn_below={d.dawn_days_below} verdict={d.dawn_verdict} new={len(d.new_dawn_days_below)} "
            f"cleared={len(d.cleared_dawn_days_below)}")
    if result.capacity is not None:
        c = result.capacity
        say(f"case={c.case_id} inverter_limit_kw={float(c.inverter_limit_kw):.0f} "
            f"extra_fuel_l={float(c.extra_fuel_l):.3f} extra_fuel_l_per_day={float(c.extra_fuel_l_per_day):.3f} "
            f"extra_generator_kwh={float(c.extra_generator_kwh):.3f} "
            f"extra_unserved_kwh={float(c.extra_unserved_kwh):.3f} dawn_below={c.dawn_days_below} "
            f"verdict={c.dawn_verdict} new={len(c.new_dawn_days_below)} cleared={len(c.cleared_dawn_days_below)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=61)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    return study(args.days, args.out)


if __name__ == "__main__":
    sys.exit(main())
