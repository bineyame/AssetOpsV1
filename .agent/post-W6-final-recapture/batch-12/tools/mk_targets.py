"""Writes targets-<phase>.json (capture URLs only). Windows match .agent/W4-02-evidence/capture.mjs (W4-02 unit 7);
MG-W402-001 is Africa/Nairobi (UTC+3), so 09:00Z-10:00Z is the site-local 12:00-13:00 hour."""
import json, sys
B = "http://localhost:5182"
S = "/sites/MG-W402-001"
HOUR = lambda d: f"from=2026-10-{d}T09:00:00Z&to=2026-10-{d}T10:00:00Z"
REN_POS = "from=2026-10-05T21:00:00Z&to=2026-10-10T21:00:00Z"
REN_GAP = "from=2026-10-07T21:00:00Z&to=2026-10-12T21:00:00Z"
REN_BAD = "from=2026-10-04T21:00:00Z&to=2026-10-10T21:00:00Z"  # six local days -> 422 INVALID_WINDOW
HOUR_BAD = "from=2026-10-06T09:00:00Z&to=2026-10-06T11:00:00Z"  # two hours -> 422 INVALID_WINDOW
EARLY = "&known_at=2026-10-01T00:00:00Z"  # before any accepted evidence was known
IDS = ["renewable", "service", "fuel", "backup"]
u = lambda i, q: f"{B}{S}/performance/{i}" + (("?" + q) if q else "")
pos = lambda i: REN_POS if i == "renewable" else HOUR("06")
t = []
phase = sys.argv[1]
if phase == "main":
    t += [dict(id=i, case="positive", url=u(i, pos(i))) for i in IDS]
    t += [dict(id=i, case="gap-limited", url=u(i, REN_GAP if i == "renewable" else HOUR("12"))) for i in IDS]
    t += [dict(id=i, case="no-window", url=u(i, None)) for i in IDS]
    t += [dict(id=i, case="refused-invalid", url=u(i, REN_BAD if i == "renewable" else HOUR_BAD)) for i in IDS]
    t += [dict(id=i, case="known-before-evidence", url=u(i, pos(i) + EARLY)) for i in IDS]
elif phase == "links":  # app-only Overview link check, not pairs
    t += [dict(id="link-check", case=f"mini-{d}", url=f"{B}{S}?date=2026-10-{d}", mock="mini") for d in ("06", "08", "12")]
json.dump(t, open(f"targets-{phase}.json", "w"), indent=1)
print(phase, len(t))
