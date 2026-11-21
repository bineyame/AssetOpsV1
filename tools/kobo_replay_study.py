"""0K2: the replay study on the declared simulated Kobo season (spec §4 "The 61-day study"). In memory, no database.

    python tools/kobo_replay_study.py --time-one [--days 61] [--model-version 8 --season v2]
    python tools/kobo_replay_study.py --days 61 --out /opt/assetecon/evidence/0K2/<run>/study.json
    python tools/kobo_replay_study.py --model-version 8 --season v2 --days 61 --out .../0K4d/<run>/study.json

Builds the season (`host/tests/kobo_season.py`), runs it on the kernel as the site, publishes its series, and runs
`replay_study` through `HostForwardReplay` with the default frame and `KOBO_GRID`. Every figure is SIMULATED input and
MODELLED evidence; CALIBRATED on SIMULATED input is adapter fidelity (the replay path follows the kernel run that made
the series), not a match of the model to a Site. Every printed line carries both labels.

The tool, never `replay_study.py`, adds: per case, each dawn below the limit with its date, SOC, generator state and
class (`window-start`, `after-overcast`, `other`, from the fixture calendar), the least reading at or above the limit,
and each window figure x 30 / 61 marked "scaled to 30 days" (D-0K2.17, D-0K2.21).

`--time-one` builds the site run and one baseline replay, prints the wall seconds of each and exits 0 (D-0K2.24).

0K4d: `--model-version {7,8}` and `--season {v1,v2}` (defaults 7 and v1, so 0K2's recorded commands reproduce); only
(7, v1) and (8, v2) run, a mixed pair exits 2 with `STUDY_FLAGS_INVALID model=<v> season=<s>`. On v8 the site is
`season_site_v2` and the frame carries the four assumption strings of D-0K4.27. Every line and the JSON header carry
the model and season; the header also holds the commit, the season's inputs digest (S9's form, on the v7 base), the
site run's trajectory digest and, on v8, `admission_rule` (D-0K4.28). Each case of a CALIBRATED study is judged by
`runs/admission.py`; the dawn is information beside it and never decides. No design value is read or written.
Exit 0 done, 2 refused (`<CODE> <subject>` on stderr).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for part in ("host", "host/tests", "backend", "contracts", "simulator"):
    sys.path.insert(0, str(ROOT / part))

from assetops_backend.runs.admission import AdmissionRule, admit  # noqa: E402
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
from kobo_assumed import ASSUMED_DERIVATION  # noqa: E402
from kobo_season import (  # noqa: E402
    TIMEZONE,
    base_run,
    inputs_digest,
    observed_series,
    overcast_v1,
    overcast_v2,
    season_inputs,
    season_site,
    season_site_v2,
)
from trajectory_digest import trajectory_digest  # noqa: E402

LABELS = "input_class=SIMULATED evidence_class=MODELLED"
NOTE = ("CALIBRATED on SIMULATED input is adapter fidelity: the replay path follows the kernel run that made the "
        "series; it is not a match of the model to a Site")
CAPACITY = Fraction(200)  # the template's battery-energy-capacity (D-0K2.21)
#: The only (model version, season) pairs that run; each season's site edit and overcast calendar.
PAIRS = {(7, "v1"): (season_site, overcast_v1), (8, "v2"): (season_site_v2, overcast_v2)}
#: D-0K4.27's order of the assumption strings.
ASSUMPTION_KEYS = ("generator-no-load-fuel-rate", "generator-minimum-load", "battery-charge-taper-start",
                   "specific-fuel-consumption")
_IDENTITY = {"model": 7, "season": "v1"}


def say(text: str) -> None:
    print(f"{LABELS} model=mini-grid/{_IDENTITY['model']} season={_IDENTITY['season']} {text}", flush=True)


def authored(value) -> str:
    return f"{value:g}"


def assumption_lines(run, derivation=None) -> tuple[str, ...]:
    """D-0K4.27: `<key> <value> <unit> (<label>, <BASIS>: <derivation>)` per key, value and unit from the run's frozen
    `model_needs` (authored form); a key with no need or no derivation entry is `KeyError`."""
    derivation = ASSUMED_DERIVATION if derivation is None else derivation
    needs = {need.property_key: need for need in run.deterministic_identity.model_needs}
    lines = []
    for key in ASSUMPTION_KEYS:
        if key not in needs:
            raise KeyError(key)
        label, basis, words = derivation[key]
        lines.append(f"{key} {authored(needs[key].value)} {needs[key].unit} ({label}, {basis}: {words})")
    return tuple(lines)


def admission_rule_lines(rule: AdmissionRule) -> tuple[str, str]:
    """D-0K4.27: the rule's two limits as assumed values; the words live here, never in `admission.py`."""
    return (f"max-starts-per-day {rule.max_starts_per_day} per day (assumed, {rule.basis}: a typical maker's limit, "
            "until Kobo's generator sheet)",
            f"full-charge-every-days {rule.full_charge_every_days} days (assumed, {rule.basis}: lithium iron "
            "phosphate, until Kobo's battery sheet)")


def commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout.strip()


def number(value: Fraction) -> dict:
    return {"exact": f"{value.numerator}/{value.denominator}", "reading": f"{float(value):.3f}"}


def site(days: int, version: int = 7, season: str = "v1"):
    run = base_run(days, version=version, site_edit=PAIRS[(version, season)][0])
    if run.execution_status != "READY":
        raise SystemExit(f"the season run is {run.execution_status}")
    trajectory = execute(season_inputs(run, days, season=season), model_for(run))
    if trajectory.outcome != "COMPLETED":
        raise SystemExit(f"the site run ended {trajectory.outcome}: {trajectory.failure}")
    return run, trajectory


def dawn_class(index: int, overcast=overcast_v1) -> str:
    if index == 0:
        return "window-start"
    return "after-overcast" if overcast(index - 1) else "other"


def number_or_none(value) -> dict | None:
    return None if value is None else number(value)


def admission_json(a) -> dict:
    return {
        "admitted": a.admitted,
        "first_failing_part": next((part.name for part in a.parts if not part.passed), None),
        "parts": [{"name": part.name, "case_value": number(part.case_value),
                   "baseline_value": number(part.baseline_value), "limit": number_or_none(part.limit),
                   "judged": part.judged, "passed": part.passed} for part in a.parts],
        "dawn_information": {"worst_soc_pct": number(a.dawn.worst_soc_pct),
                             "margin_points": number(a.dawn.margin_points), "days_below": a.dawn.days_below,
                             "dates_below": list(a.dawn.dates_below)},
        "input_class": a.input_class, "evidence_class": a.evidence_class,
    }


def outcome_json(outcome, days: int, frame: StudyFrame, overcast=overcast_v1) -> dict:
    dates = [r.local_date for r in outcome.dawn]
    below = [
        {"date": r.local_date, "soc_pct": number(r.soc_pct), "generator_state": r.generator_state,
         "class": dawn_class(dates.index(r.local_date), overcast)}
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
        "reserve_breach_steps": outcome.reserve_breach_steps, "max_starts_in_a_day": outcome.max_starts_in_a_day,
        "full_charge_dates": list(outcome.full_charge_dates),
        "longest_days_without_full_charge": outcome.longest_days_without_full_charge,
        "scaled_to_30_days": {
            "basis": f"window figure x 30 / {days}, scaled to 30 days",
            "avoided_l": number(outcome.avoided_l * scale),
            "added_throughput_kwh": number(outcome.added_throughput_kwh * scale),
            "added_starts": number(outcome.added_starts * scale),
        },
    }


def time_one(days: int, version: int = 7, season: str = "v1") -> int:
    began = time.monotonic()
    run, trajectory = site(days, version, season)
    site_seconds = time.monotonic() - began
    observed = observed_series(trajectory, len(trajectory.boundaries) - 1)
    began = time.monotonic()
    HostForwardReplay().forward_replay(run, ForwardReplayRequest(
        "baseline", observed.pv_available_kw, observed.loads, start_state(observed)))
    replay_seconds = time.monotonic() - began
    say(f"days={days} steps={len(observed.pv_available_kw)} site_seconds={site_seconds:.1f} "
        f"replay_seconds={replay_seconds:.1f}")
    return 0


def study(days: int, out: Path, version: int = 7, season: str = "v1") -> int:
    say(NOTE)
    began = time.monotonic()
    run, trajectory = site(days, version, season)
    observed = observed_series(trajectory, len(trajectory.boundaries) - 1)
    site_seconds = time.monotonic() - began
    assumptions = assumption_lines(run) if version == 8 else ()
    frame = StudyFrame(timezone=TIMEZONE, battery_capacity_kwh=CAPACITY, assumptions=assumptions)
    overcast = PAIRS[(version, season)][1]
    rule = AdmissionRule()
    began = time.monotonic()
    try:
        result = replay_study(HostForwardReplay(), run, observed, frame, KOBO_GRID)
    except (StudyRefused, ForwardReplayRefused) as refused:
        print(f"{refused.code} {refused.subject}", file=sys.stderr)
        return 2
    replay_seconds = time.monotonic() - began
    calibration = result.calibration
    admissions = ({case.case_id: admit(result.baseline, case, rule) for case in result.cases}
                  if result.status == "CALIBRATED" else None)
    document = {
        "input_class": result.input_class, "evidence_class": result.evidence_class, "note": NOTE,
        "study": "0K2 replay study on the declared simulated Kobo season (host/tests/kobo_season.py)",
        "commit": commit(), "model": f"mini-grid/{version}", "season": season,
        # S9's form: the season's inputs on the v7 base run (D-0K4.26), the same digest for either model version
        "season_inputs_digest": inputs_digest(season_inputs(base_run(days), days, season=season)),
        "trajectory_digests": {"site": trajectory_digest(trajectory)},
        "assumptions": list(result.assumptions),
        **({"admission_rule": list(admission_rule_lines(rule))} if version == 8 else {}),
        "admission": (f"admission not available ({result.status})" if admissions is None
                      else "runs/admission.py admit(baseline, case); the dawn is information, never a gate"),
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
        "baseline": None if result.baseline is None else outcome_json(result.baseline, result.days, frame, overcast),
        "cases": [{**outcome_json(case, result.days, frame, overcast),
                   **({} if admissions is None else {"admission": admission_json(admissions[case.case_id])})}
                  for case in result.cases],
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
    if admissions is None:
        say(f"admission not available ({result.status})")
        return 0
    for case in result.cases:
        a = admissions[case.case_id]
        failing = next((part.name for part in a.parts if not part.passed), "-")
        by_month = ",".join(f"{m.month}:{float(m.value):.3f}" for m in case.avoided_l_by_month)
        say(f"case={case.case_id} avoided_l_by_month={by_month} admitted={'yes' if a.admitted else 'no'} "
            f"first_failing_part={failing} dawn_worst={float(a.dawn.worst_soc_pct):.2f} "
            f"dawn_margin_points={float(a.dawn.margin_points):.2f} dawn_days_below={a.dawn.days_below} (information)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--days", type=int, default=61)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--time-one", action="store_true")
    parser.add_argument("--model-version", type=int, choices=(7, 8), default=7)
    parser.add_argument("--season", choices=("v1", "v2"), default="v1")
    args = parser.parse_args(argv)
    if (args.model_version, args.season) not in PAIRS:
        print(f"STUDY_FLAGS_INVALID model={args.model_version} season={args.season}", file=sys.stderr)
        return 2
    _IDENTITY.update(model=args.model_version, season=args.season)
    if args.time_one:
        return time_one(args.days, args.model_version, args.season)
    if args.out is None:
        parser.error("--out is required for a study run")
    return study(args.days, args.out, args.model_version, args.season)


if __name__ == "__main__":
    sys.exit(main())
