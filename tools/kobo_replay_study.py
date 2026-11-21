"""0K2: the replay study on the declared simulated Kobo season (spec §4 "The 61-day study"). In memory, no database.

    python tools/kobo_replay_study.py --time-one [--days 61]
    python tools/kobo_replay_study.py --days 61 --out /opt/assetecon/evidence/0K2/<run>/study.json

Builds the season (`host/tests/kobo_season.py`), runs it on the kernel as the site, publishes its series, and runs
`replay_study` through `HostForwardReplay` with the default frame and `KOBO_GRID`. Every figure is SIMULATED input and
MODELLED evidence; CALIBRATED on SIMULATED input is adapter fidelity (the replay path follows the kernel run that made
the series), not a match of the model to a Site. Every printed line carries both labels.

The tool, never `replay_study.py`, adds: per case, each dawn below the limit with its date, SOC, generator state and
class (`window-start`, `after-overcast`, `other`, from the fixture calendar), the least reading at or above the limit,
and each window figure x 30 / 61 marked "scaled to 30 days" (D-0K2.17, D-0K2.21).

`--time-one` builds the site run and one baseline replay, prints the wall seconds of each and exits 0 (D-0K2.24).
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

from assetops_backend.runs.replay_study import (  # noqa: E402
    KOBO_GRID,
    StudyFrame,
    StudyRefused,
    replay_study,
    start_state,
)
from assetops_contracts.forward_replay import ForwardReplayRefused, ForwardReplayRequest  # noqa: E402
from assetops_simulator.kernel.execute import execute  # noqa: E402

from execution_adapter import model_for  # noqa: E402
from forward_replay import HostForwardReplay  # noqa: E402
from kobo_season import TIMEZONE, base_run, observed_series, overcast_v1, season_inputs  # noqa: E402

LABELS = "input_class=SIMULATED evidence_class=MODELLED"
NOTE = ("CALIBRATED on SIMULATED input is adapter fidelity: the replay path follows the kernel run that made the "
        "series; it is not a match of the model to a Site")
CAPACITY = Fraction(200)  # the template's battery-energy-capacity (D-0K2.21)


def say(text: str) -> None:
    print(f"{LABELS} {text}", flush=True)


def number(value: Fraction) -> dict:
    return {"exact": f"{value.numerator}/{value.denominator}", "reading": f"{float(value):.3f}"}


def site(days: int):
    run = base_run(days)
    if run.execution_status != "READY":
        raise SystemExit(f"the season run is {run.execution_status}")
    trajectory = execute(season_inputs(run, days), model_for(run))
    if trajectory.outcome != "COMPLETED":
        raise SystemExit(f"the site run ended {trajectory.outcome}: {trajectory.failure}")
    return run, trajectory


def dawn_class(index: int) -> str:
    if index == 0:
        return "window-start"
    return "after-overcast" if overcast_v1(index - 1) else "other"


def outcome_json(outcome, days: int, frame: StudyFrame) -> dict:
    dates = [r.local_date for r in outcome.dawn]
    below = [
        {"date": r.local_date, "soc_pct": number(r.soc_pct), "generator_state": r.generator_state,
         "class": dawn_class(dates.index(r.local_date))}
        for r in outcome.dawn if r.soc_pct < frame.dawn_min_soc_pct
    ]
    passing = [r for r in outcome.dawn if r.soc_pct >= frame.dawn_min_soc_pct]
    least = min(passing, key=lambda r: r.soc_pct) if passing else None

    def months(figures):
        return [{"month": m.month, "days": m.days, "value": number(m.value)} for m in figures]

    scale = Fraction(30, days)
    return {
        "case_id": outcome.case_id,
        "input_class": outcome.input_class, "evidence_class": outcome.evidence_class,
        "stop_soc_pct": number(outcome.stop_soc_pct), "stop_source": outcome.stop_source,
        "reserve_soc_pct": number(outcome.reserve_soc_pct), "reserve_source": outcome.reserve_source,
        "fuel_l": number(outcome.fuel_l), "avoided_l": number(outcome.avoided_l),
        "avoided_l_by_month": months(outcome.avoided_l_by_month),
        "generator_kwh": number(outcome.generator_kwh), "running_steps": outcome.running_steps,
        "starts": outcome.starts, "unserved_kwh": number(outcome.unserved_kwh),
        "added_starts": outcome.added_starts, "added_running_steps": outcome.added_running_steps,
        "added_throughput_kwh": number(outcome.added_throughput_kwh),
        "added_starts_by_month": months(outcome.added_starts_by_month),
        "added_throughput_kwh_by_month": months(outcome.added_throughput_kwh_by_month),
        "throughput_kwh": number(outcome.throughput_kwh), "min_soc_pct": number(outcome.min_soc_pct),
        "dawn_days_below": outcome.dawn_days_below, "dawn_days": len(outcome.dawn),
        "worst_dawn_soc_pct": number(outcome.worst_dawn_soc_pct), "dawn_verdict": outcome.dawn_verdict,
        "new_dawn_days_below": list(outcome.new_dawn_days_below),
        "cleared_dawn_days_below": list(outcome.cleared_dawn_days_below),
        "dawn_below": below,
        "least_dawn_at_or_above_limit": None if least is None else {
            "date": least.local_date, "soc_pct": number(least.soc_pct),
            "margin_points": number(least.soc_pct - frame.dawn_min_soc_pct)},
        "dawn": [{"date": r.local_date, "soc_pct": number(r.soc_pct), "generator_state": r.generator_state}
                 for r in outcome.dawn],
        "clipped_steps": outcome.clipped_steps,
        "scaled_to_30_days": {
            "basis": f"window figure x 30 / {days}, scaled to 30 days",
            "avoided_l": number(outcome.avoided_l * scale),
            "added_throughput_kwh": number(outcome.added_throughput_kwh * scale),
            "added_starts": number(outcome.added_starts * scale),
        },
    }


def time_one(days: int) -> int:
    began = time.monotonic()
    run, trajectory = site(days)
    site_seconds = time.monotonic() - began
    observed = observed_series(trajectory, len(trajectory.boundaries) - 1)
    began = time.monotonic()
    HostForwardReplay().forward_replay(run, ForwardReplayRequest(
        "baseline", observed.pv_available_kw, observed.loads, start_state(observed)))
    replay_seconds = time.monotonic() - began
    say(f"days={days} steps={len(observed.pv_available_kw)} site_seconds={site_seconds:.1f} "
        f"replay_seconds={replay_seconds:.1f}")
    return 0


def study(days: int, out: Path) -> int:
    frame = StudyFrame(timezone=TIMEZONE, battery_capacity_kwh=CAPACITY)
    say(NOTE)
    began = time.monotonic()
    run, trajectory = site(days)
    observed = observed_series(trajectory, len(trajectory.boundaries) - 1)
    site_seconds = time.monotonic() - began
    began = time.monotonic()
    try:
        result = replay_study(HostForwardReplay(), run, observed, frame, KOBO_GRID)
    except (StudyRefused, ForwardReplayRefused) as refused:
        print(f"{refused.code} {refused.subject}", file=sys.stderr)
        return 2
    replay_seconds = time.monotonic() - began
    calibration = result.calibration
    document = {
        "input_class": result.input_class, "evidence_class": result.evidence_class, "note": NOTE,
        "study": "0K2 replay study on the declared simulated Kobo season (host/tests/kobo_season.py)",
        "base_run_id": result.base_run_id, "status": result.status, "window_start": result.window_start,
        "days": result.days, "clipped_days": list(result.clipped_days),
        "kernel_runs": 1 + len(result.projections), "steps": len(observed.pv_available_kw),
        "site_seconds": round(site_seconds, 1), "replay_seconds": round(replay_seconds, 1),
        "calibration": None if calibration is None else {
            "admissible_days": len(calibration.admissible_days),
            "generator_kwh_site": number(calibration.generator_kwh_site),
            "generator_kwh_replayed": number(calibration.generator_kwh_replayed),
            "starts_site": calibration.starts_site, "starts_replayed": calibration.starts_replayed,
            "soc_mae_points": number(calibration.soc_mae_points), "failed": list(calibration.failed),
            "input_class": calibration.input_class, "evidence_class": calibration.evidence_class,
        },
        "baseline": None if result.baseline is None else outcome_json(result.baseline, result.days, frame),
        "cases": [outcome_json(case, result.days, frame) for case in result.cases],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, indent=1), encoding="utf-8")
    say(f"status={result.status} days={result.days} kernel_runs={document['kernel_runs']} "
        f"site_seconds={site_seconds:.1f} replay_seconds={replay_seconds:.1f} out={out}")
    if calibration is not None:
        say(f"calibration generator_kwh site={float(calibration.generator_kwh_site):.3f} "
            f"replayed={float(calibration.generator_kwh_replayed):.3f} starts site={calibration.starts_site} "
            f"replayed={calibration.starts_replayed} soc_mae={float(calibration.soc_mae_points):.4f} "
            f"failed={','.join(calibration.failed) or '-'}")
    for case in ((result.baseline,) if result.baseline else ()) + result.cases:
        say(f"case={case.case_id} fuel_l={float(case.fuel_l):.1f} avoided_l={float(case.avoided_l):.1f} "
            f"starts={case.starts} running_steps={case.running_steps} "
            f"throughput_kwh={float(case.throughput_kwh):.1f} min_soc={float(case.min_soc_pct):.2f} "
            f"unserved_kwh={float(case.unserved_kwh):.3f} dawn_below={case.dawn_days_below}/{len(case.dawn)} "
            f"worst_dawn={float(case.worst_dawn_soc_pct):.2f} verdict={case.dawn_verdict} "
            f"new={len(case.new_dawn_days_below)} cleared={len(case.cleared_dawn_days_below)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=61)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--time-one", action="store_true")
    args = parser.parse_args(argv)
    if args.time_one:
        return time_one(args.days)
    if args.out is None:
        parser.error("--out is required for a study run")
    return study(args.days, args.out)


if __name__ == "__main__":
    sys.exit(main())
