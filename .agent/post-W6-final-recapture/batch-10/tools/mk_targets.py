"""Writes targets-<phase>.json (capture URLs only). Windows match .agent/W3-01-evidence app-*.json (W3-01 commit 4)."""
import json, sys
B = "http://localhost:5180"
DAY = "from=2026-10-06T00:00:00Z&to=2026-10-07T00:00:00Z"
ACT = "from=2026-11-01T00:00:00Z&to=2026-11-03T00:00:00Z"
WIDE = "from=2026-10-01T00:00:00Z&to=2026-11-03T00:00:00Z"
BAD = "from=2026-10-01T00:00:00Z&to=2026-11-03T00:00:00Z"  # 33 days -> 422 INVALID_WINDOW (W3-01 packet)
F = [("findings", "/findings"), ("findings-cost", "/findings/cost"), ("findings-risks", "/findings/risks"),
     ("findings-opportunities", "/findings/opportunities")]
u = lambda p, q: B + p + (("?" + q) if q else "")
phase = sys.argv[1]; extra = sys.argv[2] if len(sys.argv) > 2 else ""
t = []
if phase == "positive":
    t += [dict(id=i, case="positive", url=u(p, DAY)) for i, p in F] + [dict(id="actions", case="positive", url=u("/actions", ACT))]
    t += [dict(id=i, case="no-window", url=u(p, None)) for i, p in F] + [dict(id="actions", case="no-window", url=u("/actions", None))]
    t += [dict(id="findings", case="state-merged-empty", url=u("/findings", DAY + "&state=merged")),
          dict(id="actions", case="empty-day", url=u("/actions", DAY)),
          dict(id="findings", case="refused-33d", url=u("/findings", BAD)),
          dict(id="actions", case="refused-33d", url=u("/actions", BAD))]
elif phase == "historical":  # extra = known_at before the late delivery
    t += [dict(id=i, case="historical", url=u(p, DAY + "&known_at=" + extra)) for i, p in F]
    t += [dict(id="actions", case="historical", url=u("/actions", ACT + "&known_at=" + extra))]
elif phase == "pending":  # extra = page-two cursor
    t += [dict(id=i, case="pending", url=u(p, DAY)) for i, p in F] + [dict(id="actions", case="pending", url=u("/actions", ACT))]
    if extra:
        t += [dict(id="findings", case="page-two-pending", url=u("/findings", DAY + "&cursor=" + extra))]
elif phase == "partial":
    t += [dict(id=i, case="partial", url=u(p, DAY)) for i, p in F] + [dict(id="actions", case="partial", url=u("/actions", ACT))]
    t += [dict(id="findings", case="partial-wide", url=u("/findings", WIDE))]
elif phase == "links":  # extra = file with one href per line (from positive rows); app-only cross-check, not pairs
    for i, h in enumerate(l.strip() for l in open(extra) if l.strip()):
        t.append(dict(id="link-check", case=f"l{i:02d}", url=B + h, mock="finding"))
json.dump(t, open(f"targets-{phase}.json", "w"), indent=1)
print(phase, len(t))
