"""DD-1a1 (build sheet DD-1 R2, DD1a1-R Q1/Q3): the steady scenarios, derived from their parents with no value changed.

`python tools/derive_steady_scenarios.py` writes `config/scenarios/<id>.yaml` for every entry of `STEADY`;
`--check` exits 1 if a committed file differs from the derivation (the L0 test runs the same comparison).

What a derivation may change (DD1a1-R Q1): `scenario_id`, `display_name`, `purpose`, the label and the source
lines. Structural changes, each needed for a parent window to sit in a shorter or combined interval: `version`
restarts at 1; a window's `offset_minutes` is re-based on the segment start; `sequence` is renumbered along the
document; a window taken from `kobo-mini-grid-evening` has its `event_id` / `parameter_id` prefixed `evening-` so it
cannot collide with the `kobo-daytime` window of the same number. Every value (irradiance, demand, starting state),
unit, role, state key and description is the parent's. Cold drops only the GRID_LOSS / GRID_RESTORE forcings (R2).

The Kobo night (20:00-06:00 local) is not derived from a parent: the repeated-evening night is withdrawn (owner,
2026-11-06). DD1a1-R2 defines the night profile: `NIGHT_WINDOWS` holds its values with their stated bases, each
night window copies the event structure of the evening parent's 18-20 window, and each night file's run-start state
is the measured handover in `backend/conversions/kobo-night-handover-v1.json` (`tools/probe_kobo_nights.py`).
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "config" / "scenarios"
SERIES = ("irradiance", "residential-demand", "clinic-demand", "mill-demand")
LABEL = "example data, steady day (derived from {parents})"

#: id -> (display name, local hours, the parent windows per series in order, the parent whose run-start state is used).
#: A window is (parent scenario, window number); the parent's windows are two hours long.
#: DD1a1-R2 "Shape, files and kinds": steady-day 06-18 is kobo-daytime verbatim; the afternoon (14-20) and dusk (18-20)
#: complements are the evening parent's windows verbatim and stop at 20:00, where the night files take over.
STEADY = {
    "kobo-steady-day": ("Kobo steady day (06:00-18:00)", "06:00-18:00",
                        [("kobo-daytime", n) for n in range(1, 7)], "kobo-daytime"),
    "kobo-steady-afternoon": ("Kobo steady afternoon (14:00-20:00)", "14:00-20:00",
                              [("kobo-mini-grid-evening", n) for n in (2, 3, 4)], "kobo-mini-grid-evening"),
    "kobo-steady-dusk": ("Kobo steady dusk (18:00-20:00)", "18:00-20:00",
                         [("kobo-mini-grid-evening", 4)], "kobo-mini-grid-evening"),
}
#: DD1a1-R4: the mill story day (`mill-midday`, kobo-daytime v2) is BLOCKED on mini-grid v6 for the same reason as the
#: steady day, and kobo-daytime is not edited. The derived file copies kobo-daytime v2's windows and state of charge
#: verbatim and adds the dawn fuel and generator state; only the v2 `mill-midday` kind points at it.
MILL = {"kobo-mill-midday": ("Kobo mill midday (sunny day, 06:00-18:00)", "06:00-18:00",
                             [("kobo-daytime", n) for n in range(1, 7)], "kobo-daytime")}
MILL_LABEL = "example data, derived from kobo-daytime v2, the mill story day"
COLD = {"cold-steady": "cold-normal"}
PREFIX = {"kobo-daytime": "", "kobo-mini-grid-evening": "evening-"}


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _source_line(parent: str, event_id: str) -> int:
    for n, line in enumerate(_lines(SCENARIOS / f"{parent}.yaml"), 1):
        if line.strip() == f"- event_id: {event_id}":
            return n
    raise SystemExit(f"{parent}: no event {event_id}")


def _parent_event(doc: dict, event_id: str) -> dict:
    return next(e for e in doc["timeline"] if e["event_id"] == event_id)


#: DD1a1-R3 Q2: `kobo-daytime` is written for the daytime-mini-grid profile (no generator or tank) and declares only
#: the state of charge. On mini-grid v6 the derived steady day must also declare the fuel and generator start states.
#: These are the dawn state every mini-grid Kobo parent declares (checked uniform below); the parameter structure is
#: the evening parent's.
DAWN_PARENTS = ("kobo-mini-grid-evening", "kobo-mini-grid-degraded-evidence", "kobo-mini-grid-prolonged",
                "kobo-mini-grid-reserve-matters", "kobo-mini-grid-reserve-trial", "kobo-mini-grid-stop-60",
                "kobo-s3-dispatch-degraded-reporting", "kobo-s3-dispatch-necessary-run")
DAWN_STATE = ("starting-fuel", "starting-generator-state")
NEEDS_DAWN_STATE = {"kobo-steady-day", "kobo-mill-midday"}


def dawn_state() -> tuple[list[dict], str]:
    """The fuel and generator run-start parameters every mini-grid Kobo parent declares, and their source line.
    Refuses (SystemExit) if any parent declares a different value: the values are uniform, never chosen."""
    params, cites, values = None, [], {}
    for parent in DAWN_PARENTS:
        doc = yaml.safe_load((SCENARIOS / f"{parent}.yaml").read_text(encoding="utf-8"))
        found = [p for p in doc["public_parameters"] if p["parameter_id"] in DAWN_STATE]
        for p in found:
            values.setdefault(p["parameter_id"], set()).add(p["value"])
            line = next(n for n, l in enumerate(_lines(SCENARIOS / f"{parent}.yaml"), 1)
                        if l.strip() == f"- parameter_id: {p['parameter_id']}")
            cites.append(f"{parent}.yaml:{line}")
        if params is None:
            params = copy.deepcopy(found)
    if sorted(values) != sorted(DAWN_STATE) or any(len(v) != 1 for v in values.values()):
        raise SystemExit(f"dawn state not uniform across the mini-grid Kobo parents: {values}")
    shown = ", ".join(f"{p['value']} {p['unit']}".replace(" state", "") for p in params)
    return params, (f"# starting-fuel and starting-generator-state ({shown}): not declared by kobo-daytime "
                    "(daytime-mini-grid profile, no generator); the dawn state every mini-grid Kobo parent declares "
                    f"({', '.join('config/scenarios/' + c for c in cites)}); STOPPED is the only state setup accepts "
                    "at run start (DD1a1-R3 Q2).")


def kobo(sid: str) -> str:
    display, hours, windows, state_parent = (STEADY | MILL)[sid]
    docs = {p: yaml.safe_load((SCENARIOS / f"{p}.yaml").read_text(encoding="utf-8")) for p, _ in windows}
    docs.setdefault(state_parent, yaml.safe_load((SCENARIOS / f"{state_parent}.yaml").read_text(encoding="utf-8")))
    parents = sorted({p for p, _ in windows})
    label = MILL_LABEL if sid in MILL else LABEL.format(parents=" and ".join(parents))
    dawn, dawn_line = dawn_state() if sid in NEEDS_DAWN_STATE else ([], None)
    head = {
        "scenario_id": sid, "display_name": display,
        "purpose": (f"{label[0].upper()}{label[1:]}. The declared healthy reference windows of "
                    f"{' and '.join(parents)} for {hours} local time, unchanged; no fault forcing. The run-start "
                    f"state is {state_parent}'s, declared at that parent's own start; it is not carried from another "
                    "run, so the battery state of charge can jump at a segment edge."),
        "version": {"scenario_version": 1, "version_valid_from": "2026-10-01T00:00:00Z"},
        "site_contract": copy.deepcopy(docs[state_parent]["site_contract"]),
        "observation_sources": [],
        "public_parameters": copy.deepcopy(docs[state_parent]["public_parameters"]) + dawn,
    }
    state_note = (f"# Run-start state (public_parameters): {state_parent}.yaml, unchanged"
                  + (", plus the fuel and generator start states below." if dawn else "."))
    out = [f"# DD-1a1 steady scenario, generated by tools/derive_steady_scenarios.py; do not edit by hand.",
           f"# label: {label}",
           f"# Local hours {hours} (Kobo local time, UTC+3). Two-hour windows, offsets re-based on the segment start.",
           state_note, *([dawn_line] if dawn_line else []),
           yaml.safe_dump(head, sort_keys=False, width=1000, allow_unicode=True).rstrip(), "timeline:"]
    for comment, event in window_events([(parent, n, 120 * slot) for slot, (parent, n) in enumerate(windows)], docs):
        out.append(f"  # {comment}")
        body = yaml.safe_dump([event], sort_keys=False, width=1000, allow_unicode=True).rstrip()
        out.extend("  " + line for line in body.splitlines())
    return "\n".join(out) + "\n"


def window_events(windows: list[tuple[str, int, int]], docs: dict | None = None, first_seq: int = 1):
    """(source comment, event) for each parent window `(parent, n, offset)`, per series in `SERIES` order, values
    unchanged; `sequence` numbered from `first_seq`. Shared by the steady files and the night probes."""
    docs = docs if docs is not None else {}
    for parent, _, _ in windows:
        if parent not in docs:
            docs[parent] = yaml.safe_load((SCENARIOS / f"{parent}.yaml").read_text(encoding="utf-8"))
    seq = first_seq - 1
    for series in SERIES:
        for parent, n, offset in windows:
            eid = f"{series}-{n}"
            event = copy.deepcopy(_parent_event(docs[parent], eid))
            seq += 1
            event["event_id"] = PREFIX[parent] + eid
            event["sequence"] = seq
            event["offset_minutes"] = offset
            for p in event.get("parameters", []):
                p["parameter_id"] = PREFIX[parent] + p["parameter_id"]
            yield f"source: config/scenarios/{parent}.yaml:{_source_line(parent, eid)} ({eid})", event


# --- DD1a1-R2: the Kobo night profile -------------------------------------------------------------------------------

NIGHT_LABEL = "example data, night profile"
HANDOVER = ROOT / "backend" / "conversions" / "kobo-night-handover-v1.json"
#: The night's state keys and the evening parent's window whose event structure each night window copies.
NIGHT_TEMPLATE = ("kobo-mini-grid-evening", 4)
_TYPICAL = "typical rural East African mini-grid pattern (DD1a1-R2 grounding), not a Kobo measurement"
_NO_SUN = ("no sun: every Kobo parent declares 0 W/m2 from 18:00; at about 9 N sunset is about 18:30 and sunrise "
           "about 06:15 (DD1a1-R2 site facts)")
_NO_MILL = "the grain mill does not run at night (DD1a1-R2 grounding)"
_CLINIC_NIGHT = ("night base: vaccine and medicine refrigeration, security and ward lighting, on-call care, "
                 "roughly 1.5-3 kW")
#: Local window -> (start minute from the file start, minutes, residential kW and basis, clinic kW and basis).
#: The values and bases are DD1a1-R2's night input table, unchanged.
NIGHT_WINDOWS = {
    "late": (("20:00", "22:00", 0, 120, 9, "evening peak tapering, about 65% of the parent's 14 kW at 18-20",
              4, "the parent's 5 kW at 18-20, with evening activity ending"),
             ("22:00", "24:00", 120, 120, 5, "most homes asleep", 2, _CLINIC_NIGHT)),
    "early": (("00:00", "02:00", 0, 120, 3, "night base, about 21% of the 14 kW evening peak", 2, _CLINIC_NIGHT),
              ("02:00", "04:00", 120, 120, 3, "night base, about 21% of the 14 kW evening peak", 2, _CLINIC_NIGHT),
              ("04:00", "05:00", 240, 60, 3, "night base, about 21% of the 14 kW evening peak", 2, _CLINIC_NIGHT),
              ("05:00", "06:00", 300, 60, 5, "pre-dawn rise, ending at the 06-08 daytime parent's lower values",
               2, _CLINIC_NIGHT)),
}
#: DD1a1-R7: part B of the night split at the reserve change (local 03:00): `kobo-night-early`'s windows from 03:00,
#: values and bases verbatim. 03-04 is the second hour of the 02-04 window.
NIGHT_WINDOWS["early-from-0300"] = (
    ("03:00", "04:00", 0, 60) + NIGHT_WINDOWS["early"][1][4:],
    ("04:00", "05:00", 60, 60) + NIGHT_WINDOWS["early"][2][4:],
    ("05:00", "06:00", 120, 60) + NIGHT_WINDOWS["early"][3][4:])
#: DD1a1-R7a: part A of the same split: `kobo-night-early`'s first 3 h, 00-02 verbatim and 02-03 (the first hour of
#: the 02-04 window), values and bases verbatim. It ends before the 05:00 generator start, so it carries no disclosure.
NIGHT_WINDOWS["early-until-0300"] = (
    NIGHT_WINDOWS["early"][0],
    ("02:00", "03:00", 120, 60) + NIGHT_WINDOWS["early"][1][4:])
#: DD1a1-R7b: the file part A really runs, `kobo-night-early-until-0300` with its last window trimmed to 02:00-02:55
#: (175 min), so the run ends at 23:55Z, one step before the reserve change at 00:00Z. The 180 min file stays as the
#: probe that measures part B's start state.
NIGHT_WINDOWS["early-until-0255"] = (
    NIGHT_WINDOWS["early-until-0300"][0],
    ("02:00", "02:55", 120, 55) + NIGHT_WINDOWS["early"][1][4:])
#: The offset (minutes from the file start) from which a window carries the R3 Q1 disclosure in its basis comment.
DISCLOSED_FROM = {"late": 0, "early": 240, "early-from-0300": 60, "early-until-0300": 10**6, "early-until-0255": 10**6}
#: id -> (display name, half, probe chain). Chain "S" = after the steady day, "O" = after the overcast story day.
NIGHTS = {
    "kobo-night-late": ("Kobo night (20:00-24:00)", "late", "S"),
    "kobo-night-early": ("Kobo night (00:00-06:00)", "early", "S"),
    "kobo-night-late-after-overcast": ("Kobo night after an overcast day (20:00-24:00)", "late", "O"),
    "kobo-night-early-after-overcast": ("Kobo night after an overcast day (00:00-06:00)", "early", "O"),
    "kobo-night-early-from-0300": ("Kobo night (03:00-06:00)", "early-from-0300", "S"),
}
NIGHTS["kobo-night-early-until-0300"] = ("Kobo night (00:00-03:00)", "early-until-0300", "S")
NIGHTS["kobo-night-early-until-0255"] = ("Kobo night (00:00-02:55)", "early-until-0255", "S")
SPLIT_LABELS = {
    "kobo-night-early-until-0255": ("Kobo night 00:00-03:00, before the reserve change; ends 5 minutes before the "
                                    "reserve change"),
    "kobo-night-early-until-0300": "Kobo night 00:00-03:00, before the reserve change",
    "kobo-night-early-from-0300": ("Kobo night 03:00-06:00, after the reserve change took effect at 03:00; start state "
                                   "measured at that instant"),
}
#: DD1a1-R3 Q1 required disclosure, verbatim: the label of each steady night file and the 04-06 source lines.
STEADY_NIGHT_DISCLOSURE = (
    "Example data, night profile. At about 05:00 the battery reaches the 35 % generator start level and the site "
    "starts the generator. The battery is still above its reserve and serves first, so the generator delivers almost "
    "no energy before 06:00. Fuel is counted per kWh delivered; idle fuel is not modelled, so this hour shows no fuel.")
_STATE = (("starting-state-of-charge", "soc"), ("starting-fuel", "fuel"), ("starting-generator-state", "generator"))


def night_document(sid: str, start: dict) -> tuple[dict, list[str]]:
    """The night scenario document for `sid` from the start state `{soc, fuel, generator}`, and one basis comment per
    timeline event (same order). Only the R2 values change; every key, unit, role and state key is the evening
    parent's window-4 event and run-start parameter structure."""
    display, half, chain = NIGHTS[sid]
    parent, n = NIGHT_TEMPLATE
    doc = yaml.safe_load((SCENARIOS / f"{parent}.yaml").read_text(encoding="utf-8"))
    windows = NIGHT_WINDOWS[half]
    hours = f"{windows[0][0]}-{windows[-1][1]}"
    cause = ("after the overcast story day (kobo-s3-dispatch-necessary-run): the start state is what that day leaves"
             if chain == "O" else "after a steady sunny day (kobo-daytime): the start state is what that day leaves")
    params = copy.deepcopy(doc["public_parameters"])
    for item in params:
        key = dict(_STATE).get(item["parameter_id"])
        if key:
            item["value"] = start[key]
    head = {
        "scenario_id": sid, "display_name": display,
        "purpose": ((STEADY_NIGHT_DISCLOSURE + " " if chain == "S" and half not in ("early-until-0300", "early-until-0255") else f"{NIGHT_LABEL[0].upper()}{NIGHT_LABEL[1:]}. ")
                    + "A typical night at a rural mini-grid like Kobo, "
                    f"{hours} local time, no sun, {cause}. The loads follow a typical pattern, not a Kobo measurement; "
                    "the run-start state was measured by one probe run (kobo-night-handover-v1.json), never chosen."),
        "version": {"scenario_version": 1, "version_valid_from": "2026-10-01T00:00:00Z"},
        "site_contract": copy.deepcopy(doc["site_contract"]),
        "observation_sources": [],
        "public_parameters": params,
    }
    events, comments, seq = [], [], 0
    for series in SERIES:
        template = _parent_event(doc, f"{series}-{n}")
        for k, (lo, hi, offset, minutes, res, res_basis, clinic, clinic_basis) in enumerate(windows, 1):
            value, basis = {
                "irradiance": (0, _NO_SUN), "mill-demand": (0, _NO_MILL),
                "residential-demand": (res, f"{res_basis}; {_TYPICAL}"),
                "clinic-demand": (clinic, f"{clinic_basis}; {_TYPICAL}"),
            }[series]
            event = copy.deepcopy(template)
            seq += 1
            event["event_id"] = f"night-{series}-{k}"
            event["sequence"] = seq
            event["offset_minutes"] = offset
            event["timing"]["duration_minutes"] = minutes
            event["description"] = event["description"].replace("18:00 to 20:00", f"{lo} to {hi}")
            for p in event["parameters"]:
                p["parameter_id"] = f"night-{series}-{k}-level"
                p["value"] = value
            events.append(event)
            comments.append(f"basis: {value} {template['parameters'][0]['unit']}, {basis}. Structure: "
                            f"config/scenarios/{parent}.yaml:{_source_line(parent, f'{series}-{n}')} ({series}-{n})"
                            + (f". {STEADY_NIGHT_DISCLOSURE}" if chain == "S" and offset >= DISCLOSED_FROM[half] else ""))
    head["timeline"] = events
    return head, comments


def night(sid: str) -> str:
    import json

    handover = json.loads(HANDOVER.read_text(encoding="utf-8"))
    entry = handover["handover"][sid]
    doc, comments = night_document(sid, entry["start"])
    timeline = doc.pop("timeline")
    label = (SPLIT_LABELS[sid] if sid in SPLIT_LABELS else
             STEADY_NIGHT_DISCLOSURE if NIGHTS[sid][2] == "S" else NIGHT_LABEL)
    out = [f"# DD1a1-R2 night scenario, generated by tools/derive_steady_scenarios.py; do not edit by hand.",
           f"# label: {label}",
           f"# Run-start state (public_parameters): measured by probe {entry['probe_id']} at {entry['at_local']} local "
           f"({HANDOVER.relative_to(ROOT).as_posix()}); {entry['rounding']}",
           yaml.safe_dump(doc, sort_keys=False, width=1000, allow_unicode=True).rstrip(), "timeline:"]
    for comment, event in zip(comments, timeline):
        out.append(f"  # {comment}")
        body = yaml.safe_dump([event], sort_keys=False, width=1000, allow_unicode=True).rstrip()
        out.extend("  " + line for line in body.splitlines())
    return "\n".join(out) + "\n"


def cold(sid: str) -> str:
    parent = COLD[sid]
    lines = _lines(SCENARIOS / f"{parent}.yaml")
    doc = yaml.safe_load("\n".join(lines))
    dropped = [f"{r['kind']} at {r['at']}" for r in doc["forcings"]]
    doc["scenario_id"] = sid
    doc["forcings"] = []
    first = next(n for n, l in enumerate(lines, 1) if l.startswith("forcings:"))
    head = [f"# DD-1a1 steady scenario, generated by tools/derive_steady_scenarios.py; do not edit by hand.",
            f"# label: {LABEL.format(parents=parent)}",
            f"# source: config/scenarios/{parent}.yaml:1-{len(lines)}; every key and value unchanged except",
            f"#   scenario_id and forcings (config/scenarios/{parent}.yaml:{first}-{len(lines) - 1}: removed "
            f"{'; '.join(dropped)}).",
            "# The strict cold-scenario/1 key set admits no label key, so the label is this comment."]
    return "\n".join(head) + "\n" + yaml.safe_dump(doc, sort_keys=False, width=1000)


def derive() -> dict[str, str]:
    out = {sid: kobo(sid) for sid in STEADY | MILL}
    out.update({sid: cold(sid) for sid in COLD})
    if HANDOVER.exists():
        out.update({sid: night(sid) for sid in NIGHTS})
    return out


def main(argv: list[str]) -> int:
    stale = []
    for sid, text in derive().items():
        path = SCENARIOS / f"{sid}.yaml"
        if "--check" in argv:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                stale.append(sid)
        else:
            path.write_text(text, encoding="utf-8", newline="\n")
    if stale:
        print("stale steady scenarios:", ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
