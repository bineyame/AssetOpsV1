"""W6-01c C3: assemble manifest.json from the seed outputs and the app-<state>.json captures (copied from C2)."""
import json
from pathlib import Path

HERE = Path(__file__).parent
SHOTS = HERE / "screenshots"
CLOCK = "2026-10-20T12:00:00Z"
CAPS = {  # section 2 caps (1440, 390), C2 header caps, and the provisional new-element cap
    "page_header": [380, 860], "mheader": [150, 400], "tabs": [90, 150], "record_panel": [650, 780],
    "record_notice": [100, 150], "date_bar_slot": [180, 300], "state_block": [180, 300],
}
STATES = [
    ("positive", "detail", "assetops_w601_c3detail_test",
     "WR-000001: one selected record head with an outcome note; REC-000003 OPERATOR_LOG names the case (plain-text code)"),
    ("empty-rec", "detail", "assetops_w601_c3detail_test",
     "WR-000002 (CANCEL request): no record -> No maintenance activity recorded; no REC -> No linked Operational record."),
    ("not-found-404", "detail", "assetops_w601_c3detail_test", "absent case UUID 00000000-0000-4000-8000-000000000404"),
    ("historical", "detail-history", "assetops_w601_c3hist_test",
     "known_at=2026-10-20T12:00:01Z selects revision 2 (h1); both live tabs carry the cutoff; the record table is unchanged "
     "because no record is written after 11:59:03"),
    ("historical-current", "detail-history", "assetops_w601_c3hist_test", "same request, no cutoff: revision 3 h1"),
    ("stress", "stress", "assetops_w601_c3stress_test", "B1 stress WR-000007: 200-char title, 4000-char activity in Technician notes"),
]


def heights(result):
    return {k: v["h"] for k, v in (result.get("heights") or {}).items() if v}


states = []
for state, fixture, db, note in STATES:
    app = json.loads((SHOTS / f"app-{state}.json").read_text(encoding="utf-8"))
    states.append({
        "state": state, "note": note,
        "fixture_command": f"python tools/w601_seed.py --db {db} --fixture {fixture} --clock {CLOCK}",
        "stored_ids": {w["code"]: w["case_id"] for w in json.loads((HERE / f"seed-{fixture}.json").read_text(encoding="utf-8"))["written"]
                       if str(w.get("code", "")).startswith("WR-")},
        "server": "uvicorn assetops_backend.main:app",
        "captured_at": app["captured_at"],
        "results": [{"width": r["width"], "route": r["route"], "image": f"screenshots/{r['image']}", "ready": r["ready"],
                     "api": r["api"], "document_width": r["document_width"], "heights": heights(r), "text": r["text"]}
                    for r in app["results"]],
    })

by = {s["state"]: s for s in states}
hist, cur = by["historical"]["results"][0]["text"], by["historical-current"]["results"][0]["text"]
assert hist["h1"] != cur["h1"], "historical capture must select a different revision than current"
assert all("known_at=" in href for _, href in hist["tab_links"]), "the explicit cutoff stays on both live tabs"
for s in states:
    for r in s["results"]:
        assert r["document_width"]["scroll"] <= r["document_width"]["client"], (s["state"], r["width"])
        assert r["text"]["oprecords_anchors"] == 0, "no /operational-records anchor before E2"
        for key, (c1440, c390) in CAPS.items():
            h = r["heights"].get(key)
            if h is not None:
                assert h <= (c1440 if r["width"] == 1440 else c390), (s["state"], r["width"], key, h)

manifest = {
    "unit": "W6-01c C3",
    "spec": ".agent/W6-01-build-spec.md C1-C3 pre-flight rulings P-C3-1..5, P-X-1..3; section 2 record rows (superseded where ruled); "
            "section 3.1 F3-F6/A2Q6/A2Q7/X2-X7/CL3-1/CL3-3",
    "server": "uvicorn on 8083 (DATABASE_URL per state; ASSETOPS_WORK_CURSOR_KEY_HEX generated per start, never printed); "
              "Vite dev server --port 5283 with ASSETOPS_API_PORT=8083; driver run_state.sh; capture.mjs (CDP 9773)",
    "clock": f"--clock {CLOCK} (C1 fixtures); reads at real DB time; the historical cutoff is 2026-10-20T12:00:01Z (P-C2-11).",
    "r8_note": "Record the actual requests and identify the response rendered by this capture; duplicate development reads "
               "do not prove a second stored result.",
    "r8_observed": "each capture recorded two identical GET responses (dev-server effect repeat); the page rendered the "
                   "single stored result shown in `text`",
    "caps_px_1440_390": CAPS,
    "caps_note": "page_header excludes the mheader (C2 measured them separately); record_panel is collapsed (details closed)",
    "mock_reference": "screenshots/mock-wr-record-1440.png, mock-wr-record-390.png (B2/mock_capture.mjs wr-record)",
    "mock_comparison": json.loads((HERE / "mock_comparison.json").read_text(encoding="utf-8")),
    "states": states,
}
(HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("manifest states:", [s["state"] for s in states])
