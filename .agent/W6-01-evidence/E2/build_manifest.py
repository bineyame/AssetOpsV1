"""W6-01e E2: assemble manifest.json from the seed outputs and the app-<state>.json capture results."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHOTS = HERE / "screenshots"
W = "from=2026-10-14T00:00:00Z&to=2026-10-21T00:00:00Z"
SEED = "python tools/w601_seed.py --db {db} --fixture {fx} --clock {clock}"
DBS = {
    "assetops_w601_e2op_test": ("operational", "2026-10-21T12:00:00Z", "seed-e2op.json"),
    "assetops_w601_e2zero_test": ("zero", "2026-10-21T12:00:00Z", "seed-e2zero.json"),
    "assetops_w601_e2stress_test": ("stress", "2026-10-21T12:00:00Z", "seed-e2stress.json"),
    "assetops_w601_e2detail_test": ("detail", "2026-10-20T12:00:00Z", "seed-e2detail.json"),
}
STATES = [
    ("positive", "assetops_w601_e2op_test", "all kinds, page one of seven (five rows)"),
    ("positive-page2", "assetops_w601_e2op_test", "page two (two rows) via Next"),
    ("kind-OPERATOR_LOG", "assetops_w601_e2op_test", "filtered: 2 current"),
    ("kind-MANUAL_READING", "assetops_w601_e2op_test", "filtered: 2"),
    ("kind-SHIFT_NOTE", "assetops_w601_e2op_test", "filtered: 3 current (includes the corrected head)"),
    ("kind-SITE_VISIT", "assetops_w601_e2op_test", "exact filtered zero in the standard window"),
    ("broad-site-visit", "assetops_w601_e2op_test", "[2026-10-13,2026-10-21): the KOBO-002 SITE_VISIT"),
    ("historical", "assetops_w601_e2op_test", "known_at=2026-10-21T12:00:00Z: REC-000003 head is the original OPERATOR_LOG"),
    ("historical-OPERATOR_LOG", "assetops_w601_e2op_test", "historical filtered: 3"),
    ("zero", "assetops_w601_e2zero_test", "exact all-zero"),
    ("empty_scope", "assetops_w601_e2op_test", "TEST-ONLY api_empty_scope:app (deny_every_site), never a production grant"),
    ("invalid-kind", "assetops_w601_e2op_test", "kind=BOGUS: no fetch"),
    ("repeated-kind", "assetops_w601_e2op_test", "kind repeated: no fetch"),
    ("invalid-window", "assetops_w601_e2op_test", "one bound missing: no fetch"),
    ("refused-503", "assetops_w601_e2absent_test (never created: unavailable store)", "read 503"),
    ("cursor-kind-409", "assetops_w601_e2op_test", "page-one cursor reused with kind=OPERATOR_LOG: 409"),
    ("stress", "assetops_w601_e2stress_test", "4000-character OPERATOR_LOG body, collapsed then expanded"),
    ("evidence-root", "assetops_w601_e2op_test", "Evidence root: Operational records example link"),
    ("wr-record-current", "assetops_w601_e2detail_test", "C3 REC link, no cutoff"),
    ("wr-record-historical", "assetops_w601_e2detail_test", "C3 REC link, explicit known_at=2026-10-20T12:00:00Z kept"),
    ("rec-target", "assetops_w601_e2detail_test", "the REC link's target day/kind lands on REC-000003"),
]


def stored(db):
    if db not in DBS:
        return None
    _, _, name = DBS[db]
    seed = json.loads((HERE / name).read_text(encoding="utf-8"))
    out = {"sites": seed.get("sites"), "written": seed.get("written")}
    if "operational_records" in seed:
        out["operational_records"] = seed["operational_records"]
    else:
        out["operational_records"] = [c for c in seed.get("commands", []) if "operational_record_id" in c]
    return out


states = []
for state, db, note in STATES:
    app = json.loads((SHOTS / f"app-{state}.json").read_text(encoding="utf-8"))
    fx = DBS.get(db)
    states.append({
        "state": state, "note": note, "database": db,
        "fixture_command": None if fx is None else SEED.format(db=db, fx=fx[0], clock=fx[1]),
        "stored": stored(db), "captured_at": app["captured_at"],
        "results": [{k: r[k] for k in ("width", "route", "image", "ready", "api", "heights", "panels", "row_heights",
                                        "collapsed_details_max_h", "open_details", "table_scroll", "document_width",
                                        "page_height", "text") if k in r} | ({"note": r["note"]} if "note" in r else {})
                    for r in app["results"]],
    })

mock = json.loads((SHOTS / "mock-oprecords.json").read_text(encoding="utf-8"))
manifest = {
    "unit": "W6-01e E2", "spec": ".agent/W6-01-build-spec.md section 2, 3.1, E1-E2 pre-flight rulings P-E2-1..12",
    "server": "vite dev (ASSETOPS_API_PORT=8791, port 5191) + uvicorn assetops_backend.main:app per state, one at a time",
    "clock": "operational/zero/stress --clock 2026-10-21T12:00:00Z; detail --clock 2026-10-20T12:00:00Z; real DB reads on 2026-10-23",
    "window": W, "caps_px_1440_390": {"cards": [150, 330], "chips": [40, 80], "Operational records": [650, 780],
                                      "Record a manual reading": [180, 230], "How records are used": [330, 300]},
    "r8_note": "Record the actual requests and identify the response rendered by this capture; duplicate development reads do not prove a second stored result.",
    "mock_reference": "frontend/mockups/v69/index.html#/oprecords (mock-oprecords-1440.png / -390.png)", "mock_measure": mock,
    "states": states,
}
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(len(states), "states")
