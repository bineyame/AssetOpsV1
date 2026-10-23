"""W6-01d C4: build manifest.json from the per-state capture files (screenshots/app-*.json) and the seed outputs."""
import json
from pathlib import Path

HERE = Path(__file__).parent
SEED = "python tools/w601_seed.py --db {db} --fixture {fx} --clock 2026-10-20T12:00:00Z"
MAIN = "uvicorn assetops_backend.main:app"
D, L, S = "assetops_w601_c4_test", "assetops_w601_c4linked_test", "assetops_w601_c4stress_test"
STATES = {
    "page1": (D, "detail", MAIN, "WR-000001 current: six authored rows (revision 1 omitted), page 1 of 2"),
    "page2": (D, "detail", MAIN, "WR-000001 current after Next: row 6 (Correction) then the two in-table gaps"),
    "occurred-expanded": (D, "detail", MAIN, "WR-000001 page 1 with the first row's Occurrence time disclosure opened"),
    "cancel": (D, "detail", MAIN, "WR-000002: persisted CANCEL"),
    "historical": (D, "detail", MAIN, "WR-000001 at known_at=2026-10-20T11:59:04Z: four rows, revision 1, COMPLETED"),
    "linked-source": (L, "detail-linked", MAIN, "WR-000005 incident-sourced: Raised from INC-000004 with its authorized href"),
    "stress": (S, "stress", MAIN, "WR-000007: CREATED, ASSIGN (128-character assignee), Correction (500-character reason); no pager"),
    "stress-full-expanded": (S, "stress", MAIN, "WR-000007 with the Correction Full event text disclosure opened"),
    "forbidden-403": (D, "detail", "uvicorn api_403:app --app-dir .agent/W6-01-evidence/C4",
                      "TEST-ONLY composition api_403.py (copied from C2): access callback deny_fixture_site returns 403 for KOBO-001; not a production grant outcome; no browser interceptor"),
    "not-found-404": (D, "detail", MAIN, "no site_id: the page does not fetch and states the 404 sentence"),
    "unavailable-503": (D, "detail", "uvicorn api_503:app --app-dir .agent/W6-01-evidence/C4",
                        "TEST-ONLY composition api_503.py: the C1 outage Site scope raises SiteStoreUnavailable; route answers 503; not a missing-CREATED producer (that is the typed browser test and the C1 rollback-scoped server test)"),
}


def main() -> None:
    seeds = {fx: json.loads((HERE / f"seed-{fx}.json").read_text(encoding="utf-8-sig")) for fx in ("detail", "detail-linked", "stress")}
    states = []
    for state, (db, fx, server, note) in STATES.items():
        cap = json.loads((HERE / "screenshots" / f"app-{state}.json").read_text(encoding="utf-8"))
        ids = {w["code"]: w["case_id"] for w in seeds[fx]["written"] if w.get("case_id")}
        results = []
        for r in cap["results"]:
            results.append({
                "width": r["width"], "route": r["route"], "action": r["action"], "image": f"screenshots/{r['image']}", "ready": r["ready"],
                "api": r["api"], "rendered_rows": [[x["kind"], x["id"], x["time"]] for x in r["text"]["rows"]],
                "gaps": r["text"]["gaps"], "pager": r["text"]["pager"], "refusal": r["text"]["refusal"],
                "date_bar": r["text"]["date_bar"], "breadcrumb": r["text"]["breadcrumb"], "tabs": r["text"]["tabs"],
                "tab_links": r["text"]["tab_links"], "open_details": r["open_details"],
                "heights": {k: (v["h"] if v else None) for k, v in r["heights"].items()},
                "collapsed_details_max_h": r["collapsed_details_max_h"], "table_scroll": r["table_scroll"],
                "column_widths": r["column_widths"], "document_width": r["document_width"],
            })
        states.append({"state": state, "note": note, "fixture_command": SEED.format(db=db, fx=fx), "server": server,
                       "stored_ids": ids, "captured_at": cap["captured_at"], "results": results})
    manifest = {
        "unit": "W6-01d C4",
        "spec": ".agent/W6-01-build-spec.md C4 pre-flight rulings P-C4-1..22 (supersede earlier C4 wording); section 2 history row",
        "server": "uvicorn on 8084 per state (DATABASE_URL per state); Vite dev server --port 5284 with ASSETOPS_API_PORT=8084; driver run_state.sh; capture.mjs (CDP 9774)",
        "clock": "--clock 2026-10-20T12:00:00Z (B1/C1 fixtures); current reads at real DB time; historical cutoff known_at=2026-10-20T11:59:04Z (inclusive)",
        "historical_comparison": {"current": {"selected_revision": 2, "state": "IN_PROGRESS", "authored_rows": 6},
                                  "historical_11_59_04Z": {"selected_revision": 1, "state": "COMPLETED", "authored_rows": 4}},
        "r8_note": "the dev server's StrictMode issues each read twice; the built app issues one. Each capture records both identical GET responses; the page rendered the single stored result shown in rendered_rows. Duplicate dev reads are not a second stored result.",
        "caps_px_1440_390": {"history_panel": [600, 690], "new_disclosure_or_pager": [180, 300]},
        "caps_note": "history_panel is measured collapsed except in occurred-expanded and stress-full-expanded (expanded-disclosure exemption, section 2)",
        "mock_reference": "screenshots/mock-wr-history-1440.png, mock-wr-history-390.png (B2/mock_capture.mjs wr-history)",
        "states": states,
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
