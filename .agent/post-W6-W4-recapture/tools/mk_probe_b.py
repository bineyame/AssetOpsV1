"""mk_probe_b.py <phase>: probe targets (inspect.mjs) from targets-<phase>.json with W4 panel caps."""
import json, sys, os
here = os.path.dirname(os.path.abspath(__file__))
phase = sys.argv[1]
T = json.load(open(os.path.join(here, f"targets-{phase}.json")))
INC = ["[data-work-case-title]", "[data-work-mini-long^='work-mini-narrative']"]
MNT = ["[data-work-case-title]", "[data-work-asset], td:nth-child(2) .muted", "[data-work-activity]", "[data-work-outcome-note]", "[data-work-mini-long^='work-mini-next']"]
SCN = ["[data-scenario-name]", "[data-scenario-declared]"]
caps = {
    "sitework-incidents": [dict(panel="Incidents at this site", kind="fields", fields=INC)],
    "sitework-maintenance": [dict(panel="Maintenance at this site", kind="fields", fields=MNT)],
    "scenarios": [dict(panel="Financial scenarios", kind="fields", fields=SCN)],
    "opportunity-finding": [dict(panel=p, kind="none") for p in ("Bounded opportunity", "Next decision", "Consequence basis")],
}
out = [dict(t, caps=caps.get(t["id"], [])) for t in T]
json.dump(out, open(os.path.join(here, f"targets-probe-b-{phase}.json"), "w"), indent=1)
print(phase, len(out))
