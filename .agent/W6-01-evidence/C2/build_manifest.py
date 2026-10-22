"""W6-01c C2: assemble manifest.json from the seed outputs and the app-<state>.json captures."""
import json
from pathlib import Path

HERE = Path(__file__).parent
SHOTS = HERE / "screenshots"
CLOCK = "2026-10-20T12:00:00Z"
CAPS = {  # section 2 caps (1440, 390) and the provisional new-element cap
    "request_header_h1_subtitle_mheader": [380, 860], "tabs": [90, 150], "mheader": [150, 400],
    "work_done": [430, 510], "lifecycle": [350, 300], "date_bar_slot": [180, 300], "state_block": [180, 300],
}
STATES = [
    ("positive", "detail", "assetops_w601_c2detail_test", "WR-000001 IN_PROGRESS after COMPLETE+REOPEN, 2 revisions, one record"),
    ("historical", "detail-history", "assetops_w601_c2hist_test",
     "known_at=2026-10-20T12:00:01Z selects revision 2; revision 3 recorded 2026-10-20T12:00:02Z"),
    ("historical-current", "detail-history", "assetops_w601_c2hist_test", "same request, no cutoff: revision 3"),
    ("forbidden-403", "detail", "assetops_w601_c2detail_test",
     "TEST-ONLY composition api_403.py: access callback deny_fixture_site returns 403 for KOBO-001; not a production "
     "grant outcome; no browser interceptor"),
    ("not-found-404", "detail", "assetops_w601_c2detail_test", "absent case UUID 00000000-0000-4000-8000-000000000404"),
    ("stress", "stress", "assetops_w601_c2stress_test", "B1 stress WR-000007: 200-char title, 128-char owner, 4000-char narrative and activity"),
    ("linked-source", "detail-linked", "assetops_w601_c2linked_test", "WR-000005 incident-sourced, lineage-true Finding and Action"),
    ("maintenance-list-link", "detail", "assetops_w601_c2detail_test", "post-C2 list rows open the exact request (links.detail)"),
]


def heights(result):
    h = result.get("heights") or {}
    return {k: v["h"] for k, v in h.items() if v}


states = []
for state, fixture, db, note in STATES:
    app = json.loads((SHOTS / f"app-{state}.json").read_text(encoding="utf-8"))
    states.append({
        "state": state, "note": note,
        "fixture_command": f"python tools/w601_seed.py --db {db} --fixture {fixture} --clock {CLOCK}",
        "server": "uvicorn api_403:app --app-dir .agent/W6-01-evidence/C2" if state == "forbidden-403"
        else "uvicorn assetops_backend.main:app",
        "captured_at": app["captured_at"],
        "results": [{"width": r["width"], "route": r["route"], "image": f"screenshots/{r['image']}", "ready": r["ready"],
                     "api": r["api"], "document_width": r["document_width"], "heights": heights(r), "text": r["text"]}
                    for r in app["results"]],
    })

by = {s["state"]: s for s in states}
hist, cur = by["historical"]["results"][0]["text"], by["historical-current"]["results"][0]["text"]
assert hist["h1"] != cur["h1"], "historical capture must select a different revision than current"

manifest = {
    "unit": "W6-01c C2",
    "spec": ".agent/W6-01-build-spec.md section 2, section 3.1 F3-F6/A2Q6/X2-X6/CL3, C1-C3 pre-flight rulings P-C2-1..14, P-X-1..3",
    "server": "uvicorn on 8081 (DATABASE_URL per state; ASSETOPS_WORK_CURSOR_KEY_HEX generated per start, never printed); "
              "Vite dev server --port 5281 with ASSETOPS_API_PORT=8081; driver run_state.sh; capture.mjs",
    "clock": f"--clock {CLOCK} (C1 fixtures); list window from=2026-10-14T00:00:00Z&to=2026-10-21T00:00:00Z; reads at real DB time. "
             "The detail historical cutoff is 2026-10-20T12:00:01Z (P-C2-11), not the A2Q3 list cutoff.",
    "r8_note": "Record the actual requests and identify the response rendered by this capture; duplicate development reads "
               "do not prove a second stored result.",
    "caps_px_1440_390": CAPS,
    "historical_assertion": {"historical_h1": hist["h1"], "current_h1": cur["h1"],
                             "historical_date_bar": hist["date_bar"], "current_date_bar": cur["date_bar"],
                             "changed_selected_revision": True},
    "mock_reference": "screenshots/mock-wr-overview-1440.png, mock-wr-overview-390.png (B2/mock_capture.mjs wr-overview)",
    "mock_comparison": json.loads((HERE / "mock_comparison.json").read_text(encoding="utf-8")),
    "states": states,
}
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
print("states", len(states))
