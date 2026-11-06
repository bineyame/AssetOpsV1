"""DD1a1-R2 probes S and O: the measured run-start state of each Kobo night file. In memory, no database.

`python tools/probe_kobo_nights.py` writes `backend/conversions/kobo-night-handover-v1.json`; `--check` exits 1 if
the committed file differs from a fresh measurement. Then `tools/derive_steady_scenarios.py` renders the night files.

A run cannot start mid-scenario and state is not carried between runs (DD1a1-R Q3), so each night's start state is
read from one continuous probe run that ends where the night begins. Nothing here is chosen:

- Probe S, the steady day: `kobo-daytime` windows 1-6 plus `kobo-mini-grid-evening` window 4 (06:00-20:00 local),
  from DD1a1-R2's stated start: `kobo-daytime`'s declared 55 % with 300 L and STOPPED (kobo-daytime itself declares
  no fuel or generator start; see `probe_s`). Its 20:00 state starts `kobo-night-late`.
- Probe O, after the overcast story day: `kobo-s3-dispatch-necessary-run`'s own events (06:00-14:00, its declared
  start 40 %, 300 L, STOPPED) plus `kobo-mini-grid-evening` windows 2-4 (14:00-20:00). Its 20:00 state starts
  `kobo-night-late-after-overcast`.
- Each `-late` night is then run from that state; its measured 24:00 state starts the matching `-early` night, and
  the `-early` night is run too, so every night's generator use is measured here (the steady-night gate's in-memory
  half; the L2 run reads Findings, threads and money).

Handover rounding (DD1a1-R2): state of charge to a whole %, fuel to 0.1 L. A generator RUNNING at a handover becomes
STOPPED, because run setup refuses a RUNNING start; the file reports it. The probe site is the template Site
(`host/tests/kobo.py` `kobo_site`, `config/site-templates/kobo-mini-grid-60kw.yaml`) on mini-grid v6 at 5 minutes.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host" / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

import yaml  # noqa: E402

import derive_steady_scenarios as derive  # noqa: E402

SOC, FUEL, GEN = "battery-state-of-charge@battery", "fuel-tank-volume@fuel-tank", "generator-state@generator"
DAY, NEXT = "2026-09-22", "2026-09-23"  # any day: the scenarios carry no date; 03:00Z is 06:00 local (UTC+3)
PROFILE = {"model_profile": "mini-grid", "model_profile_version": 6, "timestep_minutes": 5}
ROUNDING = "state of charge rounded to a whole % (DD1a1-R2), fuel to 0.1 L"


def _load(sid: str) -> dict:
    return yaml.safe_load((derive.SCENARIOS / f"{sid}.yaml").read_text(encoding="utf-8"))


def probe_s() -> dict:
    doc = _load("kobo-daytime")
    doc["scenario_id"], doc["display_name"] = "kobo-probe-s", "DD1a1-R2 probe S (06:00-20:00)"
    windows = [("kobo-daytime", n, 120 * (n - 1)) for n in range(1, 7)] + [("kobo-mini-grid-evening", 4, 720)]
    doc["timeline"] = [event for _, event in derive.window_events(windows)]
    # kobo-daytime declares only its 55 % state of charge (its own profile models no generator). DD1a1-R2 states
    # probe S's start as 55 %, 300 L and STOPPED, the fuel and generator start every other Kobo parent declares; the
    # two parameters take kobo-mini-grid-evening's structure with those R2 values.
    # DD1a1-R3 Q2: the same declaration as kobo-steady-day (derive.dawn_state(), uniform across the parents).
    dawn, _ = derive.dawn_state()
    assert not {p["parameter_id"] for p in dawn} & {p["parameter_id"] for p in doc["public_parameters"]}
    doc["public_parameters"] += dawn
    return doc


def probe_o() -> dict:
    doc = _load("kobo-s3-dispatch-necessary-run")
    doc["scenario_id"], doc["display_name"] = "kobo-probe-o", "DD1a1-R2 probe O (06:00-20:00)"
    windows = [("kobo-mini-grid-evening", n, 480 + 120 * (n - 2)) for n in (2, 3, 4)]
    doc["timeline"] += [e for _, e in derive.window_events(windows, first_seq=len(doc["timeline"]) + 1)]
    return doc


def _probe_id(name: str, doc: dict, start: str, end: str) -> str:
    canonical = json.dumps({"document": doc, "interval": [start, end], **PROFILE}, sort_keys=True, default=str)
    return f"probe-{name}-{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:12]}"


def template_draft(doc: dict, start: str, end: str):
    """The template-Site draft (`host/tests/kobo.py`, mini-grid v6, 5 min). DD1a1-R3: the registered-Site drafter
    (`host/tests/test_dd1a1_registered_kobo.py`) has the same signature."""
    from kobo import kobo_draft

    return kobo_draft(document=copy.deepcopy(doc), start_time=start, end_time=end, **PROFILE)


def measure(name: str, doc: dict, start: str, end: str, draft=template_draft) -> dict:
    from execution_adapter import model_for, run_to_end

    run = draft(doc, start, end)
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    trajectory = run_to_end(run, model_for(run)).trajectory
    stocks = [dict(b.stocks) for b in trajectory.boundaries]
    gens = [dict(b.discrete_for_step).get(GEN) for b in trajectory.boundaries if b.discrete_for_step is not None]
    starts = sum(1 for a, b in zip(["STOPPED"] + gens, gens) if a != "RUNNING" and b == "RUNNING")
    last = trajectory.boundaries[-1]  # the end boundary has no step, so its state is `discrete`, not `_for_step`
    end_state = {"soc": float(stocks[-1][SOC]), "fuel": float(stocks[-1][FUEL]),
                 "generator": dict(last.discrete or {}).get(GEN, gens[-1])}
    return {
        "probe_id": _probe_id(name, doc, start, end),
        "scenario_sha256": run.deterministic_identity.scenario.scenario_sha256,
        "interval": [start, end],
        "start": {p["parameter_id"]: p["value"] for p in doc["public_parameters"]},
        "measured_end": end_state,
        "generator_starts": starts,
        "generator_running_minutes": PROFILE["timestep_minutes"] * sum(1 for g in gens if g == "RUNNING"),
        "fuel_used_l": round(float(stocks[0][FUEL]) - end_state["fuel"], 3),
        "min_soc": round(min(float(s[SOC]) for s in stocks), 3),
    }


def _handover(end: dict) -> dict:
    return {"soc": round(end["soc"]), "fuel": round(end["fuel"], 1), "generator": "STOPPED"}


def chain(name: str, day_doc: dict, late: str, early: str, draft=template_draft) -> tuple[dict, dict]:
    probes, handover = {}, {}
    probes[name] = measure(name, day_doc, f"{DAY}T03:00:00Z", f"{DAY}T17:00:00Z", draft)
    for sid, frm, (lo, hi), at in ((late, name, (f"{DAY}T17:00:00Z", f"{DAY}T21:00:00Z"), "20:00"),
                                   (early, f"{name}-late", (f"{DAY}T21:00:00Z", f"{NEXT}T03:00:00Z"), "00:00")):
        end = probes[frm]["measured_end"]
        start = _handover(end)
        handover[sid] = {
            "probe_id": probes[frm]["probe_id"], "at_local": at, "start": start, "rounding": ROUNDING + (
                "; the generator was RUNNING at the handover and starts STOPPED (run setup refuses RUNNING)"
                if end["generator"] == "RUNNING" else "; the generator was STOPPED at the handover")}
        doc, _ = derive.night_document(sid, start)
        key = f"{name}-late" if sid == late else f"{name}-early"
        probes[key] = measure(key, doc, lo, hi, draft)
    return probes, handover


SPLIT = "kobo-night-early-from-0300"
SPLIT_A = "kobo-night-early-until-0300"  # the 180 min probe file (R7a)
PART_A = "kobo-night-early-until-0255"  # the 175 min file part A runs (R7b)


def parent_state_at_0300(start: dict, draft=template_draft) -> dict:
    """`kobo-night-early` (the whole 6 h, same start state) as it stands at 03:00 local, 36 steps in: the state part
    B's start must equal (DD1a1-R7a)."""
    from execution_adapter import model_for, run_to_end

    doc, _ = derive.night_document("kobo-night-early", start)
    run = draft(doc, f"{DAY}T21:00:00Z", f"{NEXT}T03:00:00Z")
    assert run.execution_status == "READY", [(r.kind, r.subject) for r in run.blocking_reasons]
    boundary = run_to_end(run, model_for(run)).trajectory.boundaries[180 // PROFILE["timestep_minutes"]]
    return {"soc": float(dict(boundary.stocks)[SOC]), "fuel": float(dict(boundary.stocks)[FUEL]),
            "generator": dict(boundary.discrete or {}).get(GEN)}


def split(s_probes: dict, s_handover: dict, draft=template_draft) -> tuple[dict, dict]:
    """DD1a1-R7/R7a: part A is `kobo-night-early-until-0300` (the parent's first 3 h, same start state) on
    [21:00Z, 00:00Z); part B's start state is what part A measures at 00:00Z (full precision, so the seam has no jump;
    never chosen) and must equal `kobo-night-early`'s own state at 03:00 local. Part B is then run too, so its
    generator use is measured."""
    a_start = s_handover["kobo-night-early"]["start"]
    probe_doc, _ = derive.night_document(SPLIT_A, a_start)
    probe = measure("S-early-probe", probe_doc, f"{DAY}T21:00:00Z", f"{NEXT}T00:00:00Z", draft)
    parent = parent_state_at_0300(a_start, draft)
    end = probe["measured_end"]
    assert {k: end[k] for k in ("soc", "fuel", "generator")} == parent, (end, parent)
    # R7b: part A runs 175 min and ends at 23:55Z; its state there must equal the probe's at that step.
    a_doc, _ = derive.night_document(PART_A, a_start)
    a = measure("S-early-a", a_doc, f"{DAY}T21:00:00Z", f"{DAY}T23:55:00Z", draft)
    at_2355 = probe_state_at(probe_doc, 175, draft)
    assert {k: a["measured_end"][k] for k in ("soc", "fuel", "generator")} == at_2355, (a["measured_end"], at_2355)
    start = {"soc": end["soc"], "fuel": end["fuel"], "generator": "STOPPED"}
    b_doc, _ = derive.night_document(SPLIT, start)
    b = measure("S-early-b", b_doc, f"{NEXT}T00:00:00Z", f"{NEXT}T03:00:00Z", draft)
    shared = {**s_handover["kobo-night-early"]}
    return ({"S-early-probe": probe, "S-early-a": a, "S-early-b": b},
            {SPLIT_A: {**shared, "rounding": shared["rounding"] + "; the same start state as kobo-night-early "
                       "(DD1a1-R7a); the 180 min probe file: its end equals kobo-night-early's state at 03:00 local "
                       "and it measures part B's start state"},
             PART_A: {**shared, "rounding": shared["rounding"] + "; the same start state as kobo-night-early "
                      "(DD1a1-R7b); the 175 min file part A runs, ending at 23:55Z"},
             SPLIT: {"probe_id": probe["probe_id"], "at_local": "03:00", "start": start,
                     "rounding": "full precision, no rounding, so part B starts exactly where the probe ended" + (
                         "; the generator was RUNNING at the seam and starts STOPPED (run setup refuses RUNNING)"
                         if end["generator"] == "RUNNING" else "; the generator was STOPPED at the seam")}})


def probe_state_at(doc: dict, minutes: int, draft=template_draft) -> dict:
    """The probe file's state `minutes` after the night's 21:00Z start."""
    from execution_adapter import model_for, run_to_end

    run = draft(doc, f"{DAY}T21:00:00Z", f"{NEXT}T00:00:00Z")
    boundary = run_to_end(run, model_for(run)).trajectory.boundaries[minutes // PROFILE["timestep_minutes"]]
    return {"soc": float(dict(boundary.stocks)[SOC]), "fuel": float(dict(boundary.stocks)[FUEL]),
            "generator": dict(boundary.discrete or {}).get(GEN)}


#: DD1a1-R3 Q2: the same probes re-run on the registered demo Kobo Site (L2, own *_test DB) must measure the same
#: values; the test fails if they differ, and then this file is rewritten from the registered measurement.
REGISTERED = {"site_code": "KOBO-001", "checked_by": "host/tests/test_dd1a1_registered_kobo.py",
              "configuration": "demo prepare order: import, convert, configure_at (tools/demo_combined_kobo.py)",
              "result": "every probe and handover equal to the template-Site measurement"}


def build(draft=template_draft) -> dict:
    s_probes, s_handover = chain("S", probe_s(), "kobo-night-late", "kobo-night-early", draft)
    o_probes, o_handover = chain("O", probe_o(), "kobo-night-late-after-overcast", "kobo-night-early-after-overcast",
                                 draft)
    split_probes, split_handover = split(s_probes, s_handover, draft)
    return {
        "schema": {"id": "assetops.kobo-night-handover", "version": 1},
        "label": derive.NIGHT_LABEL,
        "method": __doc__.strip().split("\n\n")[1].replace("\n", " "),
        "site": "template Site kobo_site (config/site-templates/kobo-mini-grid-60kw.yaml), host/tests/kobo.py",
        "registered_site": REGISTERED,
        "profile": PROFILE,
        "rounding": ROUNDING,
        "probes": {**s_probes, **o_probes, **split_probes},
        "handover": {**s_handover, **o_handover, **split_handover},
    }


def main(argv: list[str]) -> int:
    text = json.dumps(build(), indent=1) + "\n"
    if "--check" in argv:
        same = derive.HANDOVER.exists() and derive.HANDOVER.read_text(encoding="utf-8") == text
        print("handover current" if same else "handover stale")
        return 0 if same else 1
    derive.HANDOVER.write_text(text, encoding="utf-8", newline="\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
