"""Post-W6 audit batch 04 ledger builder (reads capture evidence.json files; writes batch-04.json, batch-04.md, index.html).
Reviewer aid only: it reads the capture output and the hand-written difference list below; it touches no product state."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
RUNS = {
    "s601b": "tools/s601b_action_walkthrough.py --db assetops_s601b_audit --work var/s601b_audit_b4 prepare; serve --port 18401 --web-port 5184",
    "s602b": "tools/s602b_verification_walkthrough.py --db assetops_s602b_audit --work var/s602b_audit_b4 prepare; serve --case guardrail --port 18401 --web-port 5184 (replay API 18401)",
    "s602b-guardrail": "tools/s602b_verification_walkthrough.py ... serve --case guardrail --port 18401 (TEST-SCOPED guardrail case API on 18402; Vite restarted with ASSETOPS_API_PORT=18402)",
}
SELECTED = {
    "s601b": "Site KOBO-001; Action ACT-000001 b1fd7cef-3c52-4fb7-91bb-a70e00fa0a11 (F01 a13f1fe5-5ec8-49cd-92db-3cb022ce9467, origin rev 673e6a4e-594a-45e6-b2a0-e3acb78534a5); ACT-000002 8741979f-b243-40e0-8360-87a331d3435d (F02, failed no-change, pending); Finding 8cf723d2-9843-4cfd-99f9-d67e8f07a838; change dc31d0bb-5414-4bc0-a171-2c48edaf810e",
    "s602b": "Site KOBO-001; replayed VERIFIED Action ACT-000001 7f678c85-0f11-4634-8fab-aa61c09a57ff (Finding bd96cfc9-a2b0-4e6c-b987-1ac36a7366f4 rev 8ae175fc-a00c-479d-a0e6-78dc44463365; plan rev 504af0fd-35a7-402e-8671-e0e9d8220d55; outcome 51851f5b-ed1f-45b1-b8f1-4aa983dc972e)",
    "s602b-guardrail": "TEST-SCOPED guardrail case: Action 05d42afb-5c52-4054-adb9-be1d1439be75; hold Finding fee50247-6779-4dda-9d3b-38902951ff11 rev c7bf62bc-c3ea-4d7f-9fd6-1a2206d25911",
}
WINDOW = {
    "s601b": "fixture clock 2026-10-29..2026-11-01 (builder); served API real clock",
    "s602b": "replay windows earlier 2026-10-13 06:00-07:00 / later 2026-10-15 06:00-07:00 UTC; plan fixed 2026-10-14 03:00 UTC",
    "s602b-guardrail": "case Action clock pinned to the case's recorded end (producer wrapper)",
}
REP = {("recommendation", "accepted"), ("action-overview", "recorded"), ("action-execution", "applied"),
       ("action-history", "all"), ("action-plan", "pass"), ("action-evidence", "pass")}

# Cross-cutting IDs carried from batches 01/02 (cited, not re-described).
XC_ALL = ["B1-01", "B1-04", "B4-03", "B4-04", "B4-05", "B4-06", "B4-11"]
XC_390 = ["B1-03"]
DIFF_BY = {
    "recommendation": ["B4-01", "B4-08", "B4-09", "B4-10", "B4-12", "B4-13", "B4-14", "B4-15", "B1-53", "B1-07"],
    "action-overview": ["B4-07", "B4-16", "R69-verified"],
    "action-execution": ["B4-07", "B4-17", "B1-53", "R69-verified"],
    "action-history": ["B4-07", "B4-18", "B4-20", "B1-53", "R69-verified"],
    "action-plan": ["B4-07", "B4-21", "R69-verified"],
    "action-evidence": ["B4-07", "B4-22", "R69-verified"],
}
CASE_EXTRA = {
    ("action-history", "verified-replay"): ["B4-19"],
    ("action-overview", "unknown-section"): ["B4-24", "B1-07"],
    ("action-plan", "pre-plan-s601b"): ["B4-23"],
    ("action-evidence", "pre-plan-s601b"): ["B4-23"],
    ("recommendation", "unavailable"): ["B4-25"],
    ("action-execution", "failed-pending"): ["B1-53"],
}

DIFFERENCES = [
    {"id": "B4-01", "screens": "recommendation", "observed": "Rail selects 'Sites' on every Recommendation case; the mock selects 'Findings' (Finding-rooted page).",
     "evidence": "s601b/recommendation-accepted-1440-{app,mock}.png", "proposed_disposition": "(c) D3 candidate: renderable with the pathname-scoped rail override R69 already uses for Action paths. Overlaps batch 03 Finding pages; one shared shell fix."},
    {"id": "R69-verified", "screens": "action-overview, action-execution, action-history, action-plan, action-evidence", "observed": "Rail selects 'Actions' on every W1 Action detail path and state, as the mock does.",
     "evidence": "s601b/action-overview-recorded-1440-app.png", "proposed_disposition": "(a) R69 D5, status 'resolved: W5-02c K4a (merge f8137643)' verified at fddf5cad. No difference."},
    {"id": "B4-03", "screens": "action-* (all five)", "observed": "Breadcrumb is Finding-rooted 'Sites / Kobo mini-grid / Findings / Action [/ section]' with a generic 'Action' crumb; mock is Action-rooted 'Actions > ACT-048 > <section> · site: Kobo Mini-grid'. The rail (R69) says Actions while the breadcrumb says Findings.",
     "evidence": "s601b/action-overview-recorded-1440-{app,mock}.png", "proposed_disposition": "(c) D3 candidate: /actions (W3-01) and the Action code are both available, so the mock trail is renderable."},
    {"id": "B4-04", "screens": "all six", "observed": "An extra Site tab row (Overview ... Evidence, Findings current) sits above the page sub-tabs. The mock shows only the page sub-tab row on these screens. At 390 the row overflows (521 px in 358 px) with a visible grey scroll bar and a cut-off 'W...' item.",
     "evidence": "s601b/action-overview-recorded-390-{app,mock}.png; s601b/recommendation-accepted-1440-{app,mock}.png", "proposed_disposition": "(c) D3 candidate (faithful alternative: drop the row, keep breadcrumb/Open site), or (b) candidate D2 if the Architect keeps Site navigation. There is no Rxx today."},
    {"id": "B4-05", "screens": "all six", "observed": "The mock's header 'Open site' button is absent.", "evidence": "s601b/action-plan-pre-plan-s601b-1440-mock.png vs app",
     "proposed_disposition": "(c) D3 candidate (minor; the Site route exists)."},
    {"id": "B4-06", "screens": "all six", "observed": "Subtitle: Action reads 'Kobo mini-grid · an action raised from a finding' where the mock has 'What is the current intervention and outcome state?'. Recommendation reads 'Kobo mini-grid · generator support finding' where the mock has 'F-104 · proposed policy intervention and declared success criterion'. h1 values are from the selected records.",
     "evidence": "s601b/*-1440-{app,mock}.png", "proposed_disposition": "(b) candidate D4 (record-derived title/subtitle replaces illustrative copy)."},
    {"id": "B4-07", "screens": "action-* (all five)", "observed": "Sub-tab 'Application' vs mock 'Execution'. It is deliberate: SiteAction.tsx:81 'the label is the operator's word', and the URL segment stays /execution. There is no register row.",
     "evidence": "s601b/action-execution-applied-1440-{app,mock}.png", "proposed_disposition": "(b) candidate D2 (plain-language label); needs a register row and the owner's note."},
    {"id": "B4-08", "screens": "recommendation", "observed": "Finding sub-tab 'Analysis · Not available yet' is non-interactive; the mock has a live 'Analysis'.", "evidence": "s601b/recommendation-accepted-1440-app.png",
     "proposed_disposition": "(a) R21 D2, status 'built', verified (visible, noninteractive, mock order kept)."},
    {"id": "B4-09", "screens": "recommendation", "observed": "Breadcrumb reads 'Findings / Finding code unavailable / Recommendation' where the mock has F-104. The h1 'Generator support review' comes from the record (mock: 'Generator support merits review').",
     "evidence": "s601b/recommendation-accepted-1440-{app,mock}.png", "proposed_disposition": "Code: (b) candidate D1 (no public W1 Finding code; analogue of R65/R74 for cold/EV). Title: candidate D4."},
    {"id": "B4-10", "screens": "recommendation", "observed": "An extra unboxed page line, 'Analysis unavailable for this Finding section; use the Finding overview and evidence.', sits above the state strip on every case. It is not in the mock, and the Analysis sub-tab already says Not available yet (R21).",
     "evidence": "s601b/recommendation-*-1440-app.png", "proposed_disposition": "(c) D3 candidate (redundant extra line; R21 already states the gap)."},
    {"id": "B4-11", "screens": "all six", "observed": "W1 state-line pattern: Recommendation, Plan and Evidence carry a page-level status strip (badge, current-state chip, sentence, As of, Open Verification, 'How this was worked out'), and Overview, Application and History carry an in-panel badge line, note sentences and a closing disclosure. On Action pages the mock has none of these; on Recommendation it has a one-line context strip.",
     "evidence": "s602b/action-plan-pass-1440-{app,mock}.png", "proposed_disposition": "Cite B1-05: candidate D2 shell pattern (W1-UX provenance/state line). It drives part of every >1.3x ratio below."},
    {"id": "B4-12", "screens": "recommendation", "observed": "Proposed intervention adds a 'Trial only' paragraph, a Source row, accepted-note lines and a disclosure. When held, the Accept button is a disabled 'Accept trial (SYSTEM demonstration)' with an amber hold callout; when accepted, no button shows. Ratio 1.28-1.39 at 1440 and 1.32-1.55 at 390 (worst: guardrail-hold 710/457).",
     "evidence": "s601b/recommendation-*.png; s602b-guardrail/recommendation-guardrail-hold-390-app.png", "proposed_disposition": "(b) candidate D2 (honest trial caveat and hold) plus D4 values. The >1.3x needs a reviewed ruling (W1-F5b reason carried). '(SYSTEM demonstration)' and the monospace 'battery' asset code: B1-53."},
    {"id": "B4-13", "screens": "recommendation", "observed": "Declare success adds the lead 'How the trial will be judged' and a footer note. Role 'Limit' vs mock 'Guardrail'. Held, unavailable and guardrail-hold cases show no criteria table, only the gap sentence (139 px vs 367 px at 390).",
     "evidence": "s601b/recommendation-unavailable-1440-app.png", "proposed_disposition": "Wording: candidate D2. Empty state: candidate D1 (criteria exist only with an accepted trial). Honest missing state."},
    {"id": "B4-14", "screens": "recommendation", "observed": "The closing notice 'Accepting creates managed work...' is a left-bar callout at about 14 px; the mock has an 11 px info callout with an icon.",
     "evidence": "s601b/recommendation-accepted-1440-{app,mock}.png", "proposed_disposition": "Cite B1-06/B1-07 (shared callout/typography D3 candidate)."},
    {"id": "B4-15", "screens": "recommendation", "observed": "Evidence needed to verify: items 'Applied change record' / 'Later operating readings' vs mock 'Applied configuration record' / 'Later operating evidence'. The app adds a verification chip and an 'Open verification' line. Held cases show only a gap sentence (123 px vs 234 px).",
     "evidence": "s601b/recommendation-accepted-1440-{app,mock}.png", "proposed_disposition": "Wording: candidate D2. Gap state: candidate D1."},
    {"id": "B4-16", "screens": "action-overview", "observed": "Action scope has 6 rows vs 5 (adds Application). Source carries multiple links. Outcome is a chip plus a Verification link. Two note lines and a disclosure follow. Owner reads 'Not recorded'. Ratio 1.37-1.43 at 1440 and 2.05-2.40 at 390, where long values wrap in the right column.",
     "evidence": "s601b/action-overview-recorded-{1440,390}-{app,mock}.png", "proposed_disposition": "Rows/notes: candidate D2 (with B4-11). Owner: candidate D1 (no owner field). The 390 ratio >2x needs a measured cap ruling."},
    {"id": "B4-17", "screens": "action-execution", "observed": "Activity log has 5 columns vs 3 (adds Recorded, and Acted by = 'SYSTEM demonstration'), plus a state badge line, a note, a 'Show all N steps' footer and a disclosure. The failed-pending case adds the real Apply form (date input plus 'Apply trial (SYSTEM demonstration)'). Ratio 1.53-1.73 at 1440 and 2.69-2.90 at 390: rows wrap in narrow columns and Acted by sits in an inner scroller (383-428 px in 318 px).",
     "evidence": "s601b/action-execution-{applied,failed-pending}-{1440,390}-*.png", "proposed_disposition": "(b) candidate D2 (extra columns, apply control). It needs a 390 cap ruling (e.g. hide Recorded/Acted by below a breakpoint) or D3 if the Architect caps at the mock columns. Actor string: B1-53."},
    {"id": "B4-18", "screens": "action-history", "observed": "Action history has 4 columns vs 2 (adds Recorded, and Select with adjacent 'This event' / 'Through this time' links and no separator). Meaning shows raw failure codes (ACTION_VALUE_INVALID, ACTION_EFFECTIVE_TIME_INVALID, ACTION_FOUNDATION_STALE) and monospace UUIDs ellipsized to 86 px of 257 px. Ratio 1.46-1.49 at 1440 and 1.74-2.42 at 390.",
     "evidence": "s601b/action-history-all-1440-{app,mock}.png", "proposed_disposition": "Columns: candidate D2. Codes and UUIDs: B1-53 (D3 candidate). Adjacent links: minor D3 candidate (separator)."},
    {"id": "B4-19", "screens": "action-history (s602b verified-replay)", "observed": "DEFECT. Console 'Encountered two children with the same key' (key af604653-..., both widths). The API returns 3 events (ACCEPTED, APPLIED, RESOLVED af604653). The app renders a first row 'RESOLVED' (raw kind) with meaning 'Trial accepted; nothing on the Site changed.', which is wrong: the event-meaning function falls through to the ACCEPTED sentence at SiteAction.tsx:1338. That row sits beside the resolution record 'Resolved' with the same id. The footnote 'Latest at read time: 3 of 3 events' contradicts the button 'Show all 5 events'.",
     "evidence": "s602b/action-history-verified-replay-1440-app.png; s602b/evidence.json consoleErrors", "proposed_disposition": "(c) D3 defect: map the RESOLVED/RESOLUTION_WITHDRAWN Action event kinds (label and meaning), de-duplicate against resolution_events or key by source+id, and make the counts consistent. W1 mini/Action fix slice."},
    {"id": "B4-20", "screens": "action-history", "observed": "The chip 'Every recorded event' and the sentence 'everything recorded ... 6 of 6 events' sit beside a table showing the latest 3 rows with 'Show all 6 events'.",
     "evidence": "s601b/action-history-all-1440-app.png", "proposed_disposition": "(c) D3 candidate (copy contradicts the visible rows; minor)."},
    {"id": "B4-21", "screens": "action-plan", "observed": "Success criteria has 5 rows vs 4 (adds 'Windows (UTC)'). The criterion column renders as bold row headers (mock: regular td); line-height is 16.5 px vs 17.6 px. The app adds a 'Fixed ... the current plan · Open the applied change' line, a 'Dig deeper' disclosure and a footer note; guardrail adds a failed-limit line. Ratio 1.28-1.37 at 1440 and 1.44-1.60 at 390.",
     "evidence": "s602b/action-plan-pass-1440-{app,mock}.png; s602b-guardrail/action-plan-guardrail-390-app.png", "proposed_disposition": "Rows/notes: candidate D2. Bold row headers and line-height: (c) minor D3 candidate typography."},
    {"id": "B4-22", "screens": "action-evidence", "observed": "Evidence requirements has 4 rows vs 3, with status cells holding a chip plus detail text. 'Available' is a green success-tone chip where the mock uses the blue info tone. Row headers are bold. The app adds a readings note, a disclosure (slot tables, closed by default) and a footer. Text is duplicated: 'Registered Lab trial data / Registered Lab trial data'. Ratio 1.32-1.42 at 1440 and 2.00-2.35 at 390.",
     "evidence": "s602b/action-evidence-pass-1440-{app,mock}.png", "proposed_disposition": "Tone: (c) D3 candidate (status token mismatch; cf. B1-14). Rows/detail: candidate D2. Duplicated source text: D3 candidate copy. 390 >2x needs a cap ruling."},
    {"id": "B4-23", "screens": "action-plan, action-evidence (s601b pre-plan)", "observed": "Before a frozen plan, the panels show gap sentences only ('No success criteria recorded...', no table): 0.43-0.53x.",
     "evidence": "s601b/action-plan-pre-plan-s601b-390-app.png", "proposed_disposition": "(b) candidate D1 honest missing state (no plan before application). Accept as state."},
    {"id": "B4-24", "screens": "action-overview (unknown section /nosuch)", "observed": "'No such Action section' panel with a generic h1 'Action'. The Action sub-tab row is removed. The sentence is at 14 px. At 390 the dark header is 325 px. There is no mock state. Note: an explicit '/overview' segment also resolves to this state (SiteAnalyticsFrames.tsx:1622); the in-app Overview link uses the bare path.",
     "evidence": "s601b/action-overview-unknown-section-390-app.png", "proposed_disposition": "Error state: Architect to confirm the W1 pattern (no Rxx). 14 px: B1-07. Header: B1-02. '/overview' alias: minor D3 candidate if the canonical sub-tab name should resolve."},
    {"id": "B4-25", "screens": "recommendation (s601b 'unavailable' link)", "observed": "The producer labels Finding 8cf723d2 'unavailable (SOC at headroom)', but the page renders the battery hold 'Held: an earlier trial is still open' (hold takes precedence). The SOC-headroom unavailable state cannot be observed from this producer.",
     "evidence": "s601b/recommendation-unavailable-1440-app.png", "proposed_disposition": "Coverage note, not a visual difference. Architect to confirm precedence; no register row."},
]
XC_390_HEADER = {}


def load(run):
    return json.load(open(HERE / run / "evidence.json", encoding="utf-8"))


def pairs():
    out = []
    for run in ("s601b", "s602b", "s602b-guardrail"):
        for p in load(run)["pairs"]:
            a, m = p["app"], p["mock"]
            width = p["viewport"].split("x")[0]
            panels = []
            for i, ap in enumerate(a["panels"]):
                mp = m["panels"][i] if i < len(m["panels"]) else None
                ratio = round(ap["h"] / mp["h"], 2) if mp and mp["h"] else None
                panels.append({"title": ap["title"], "app_h": ap["h"], "mock_title": mp["title"] if mp else None, "mock_h": mp["h"] if mp else None,
                               "ratio": ratio, "over_limit": bool(ratio and ratio > 1.3), "app_rows": ap["rows"], "mock_rows": mp["rows"] if mp else None,
                               "app_columns": ap["columns"], "mock_columns": mp["columns"] if mp else [], "app_chips": ap["chips"], "mock_chips": mp["chips"] if mp else [],
                               "app_links": ap["links"], "mock_links": mp["links"] if mp else None, "app_details": ap["details"]})
            dark = (a.get("dark") or [{}])[0]
            band = dark.get("h") if width == "390" and dark.get("w") == 390 else None
            diffs = list(XC_ALL) + (XC_390 if width == "390" else []) + DIFF_BY[p["screen"]] + CASE_EXTRA.get((p["screen"], p["case"]), [])
            if band and band > 92:
                diffs.append("B1-02")
            clipped = [c for c in a["clipped"] if "visually-hidden" not in c["cls"] and "caption" not in c["cls"]]
            mr = max([x["ratio"] for x in panels if x["ratio"]] or [0])
            out.append({
                "screen": p["screen"], "case": p["case"], "width": width, "representative": (p["screen"], p["case"]) in REP,
                "route": p["app_url"].split("5184")[1], "app_url": p["app_url"], "mock_hash": p["mock_hash"],
                "producer": RUNS[run], "producer_run": run, "selected": SELECTED[run], "window": WINDOW[run],
                "app_titles": a["titles"], "mock_titles": m["titles"], "panel_count_match": len(a["titles"]) == len(m["titles"]),
                "panel_order_match": a["titles"] == m["titles"], "panels": panels, "max_ratio": mr,
                "over_limit_panels": [x["title"] for x in panels if x["over_limit"]],
                "typography": {"h1": {"app": a["h1"], "mock": m["h1"]}, "fonts_app": a["fonts"], "fonts_mock": m["fonts"], "panel_text_sizes_app": a["pSizes"], "panel_text_sizes_mock": m["pSizes"]},
                "colour": {"panel_app": [a["panels"][0]["background"], a["panels"][0]["border"]] if a["panels"] else None,
                           "panel_mock": [m["panels"][0]["background"], m["panels"][0]["border"]] if m["panels"] else None},
                "header_390_dark_band": band, "overflow_x": a["overflowX"], "clipped_material": clipped,
                "inner_scroll": a["hscroll"], "tab_rows_app": [t["items"] for t in a["tabRows"]], "tab_rows_mock": [t["items"] for t in m["tabRows"]],
                "console_errors": a.get("consoleErrors", []),
                "app_image": f"{run}/{p['app_image']}", "mock_image": f"{run}/{p['mock_image']}",
                "findings": list(dict.fromkeys(diffs)), "reviewer_verdict": "pending Architect classification",
            })
    return out


P = pairs()
doc = {
    "batch": "04", "name": "W1 Action/work",
    "ids": ["recommendation", "action-overview", "action-execution", "action-history", "action-plan", "action-evidence"],
    "frozen": {
        "main_sha": "d66f57e6 (product code identical to frozen fddf5cad; `git diff fddf5cad d66f57e6 -- frontend/src backend host` is empty)",
        "branch": "audit/batch-04", "worktree": "AssetOpsV1-review5",
        "manifest_sha256": "f19aa2a30e2a5dcbc8683d04cb88c41ef75b9a95194ca2e4fc6650b9511c64af",
        "mock_index_sha256": "bf8f6723fb8c223f5207bfc7d422d5c927f587aa8da511fa8fb64be6091f8e35",
        "inventory_check": "spec 87 + 23 = 110 (verified by batch 01 on the same manifest hash); all 6 batch-04 IDs mounted",
        "clock": "server real UTC, captured 2026-10-24 ~15:30-15:50 UTC; producer fixture clocks as recorded per pair",
        "api": "http://127.0.0.1:18401 (s601b, then s602b replay); 18402 (s602b TEST-SCOPED guardrail case)",
        "frontend": "http://localhost:5184 Vite dev (ASSETOPS_API_PORT=18401, restarted with 18402 for the case run); mock /mockups/v69/index.html#/<id>",
        "viewports": ["1440x1000 full-page", "390x900 mobile emulation full-page"],
        "capture_tool": ".agent/post-W6-audit/batch-04/tools/capture-b4.mjs (batch-02 capture-b2.mjs with CDP port 9524; capture-only: navigate, wait, screenshot, measure DOM, record console errors)",
    },
    "routes_reconciled": {
        "recommendation": "SITE_FINDING_VIEW_ROUTE_PATH /sites/:siteId/findings/:findingId/:findingView (recommendation in FINDING_CHILD_VIEWS) mounted",
        "action-overview": "SITE_ACTION_ROUTE_PATH /sites/:siteId/actions/:actionId mounted (SiteActionFrame)",
        "action-execution": "SITE_ACTION_VIEW_ROUTE_PATH /sites/:siteId/actions/:actionId/:actionView (execution) mounted",
        "action-history": "same, history mounted",
        "action-plan": "same, plan mounted",
        "action-evidence": "same, evidence mounted",
        "spec_route_table": "Correct for all six. Note: the explicit /actions/:id/overview segment renders 'No such Action section' (only the bare path is Overview), B4-24.",
    },
    "pair_count": len(P), "representative_pairs": sum(1 for p in P if p["representative"]),
    "register_d3_closure": {"R22": "cold-health; not on batch-04 screens", "R23": "cold-work-incidents; not on batch-04 screens", "R24": "ev-work-incidents; not on batch-04 screens",
                            "R37": "cold-performance; not on batch-04 screens", "R38": "cold-evidence-analysis; not on batch-04 screens", "R60": "ev-health; not on batch-04 screens"},
    "register_rows_verified": {"R21": "built; Recommendation 'Analysis · Not available yet' visible and noninteractive (B4-08)",
                               "R69": "resolved (W5-02c K4a f8137643); Actions rail active on all W1 Action detail pairs"},
    "ui_pass_checks": {
        "prose_14_vs_12": "Observed: the Recommendation closing notice is about 14 px (mock 11 px callout); the unknown-section sentence is 14 px. In-panel text is 10-12 px (B1-07, B4-14, B4-24).",
        "tall_dark_header_390": "Observed: dark band 325 px (unknown section), 197 (pre-plan Plan), 189 (pre-plan Evidence), 182 (history selector conflict), 146 (history recorded_at), 142 (history all), 137 (history event), against 92 px on taller pages (B1-02).",
        "plural_1_incidents": "Not applicable: no count+noun incident/maintenance copy. Attempt counts read correctly ('1 recorded, 1 failed', '3 failed attempts').",
        "raw_EV_CONNECTOR_label": "Not applicable (mini Site). Related raw vocabulary observed: B1-53.",
        "domainActionClient_generic_window_error": "Not applicable: W1 battery Actions use actionClient.ts, not domainActionClient.ts; no window inputs.",
        "R88_R112_window_control": "Not applicable: no Window control on these screens (B2-02 not present).",
    },
    "cross_cutting_cited": {"B1-01": "all 50 pairs", "B1-03": "all 25 pairs at 390", "B1-04/B2-36": "all pairs (rail Assets/Settings Not available yet)",
                            "B1-02/B2-04": "7 pairs at 390 (see ui_pass_checks)", "B1-07/B2-03": "recommendation (all cases), action-overview unknown-section",
                            "B1-53": "recommendation (SYSTEM demonstration, monospace 'battery'), action-execution (Acted by / Apply button), action-history (failure codes, UUIDs, 'RESOLVED')",
                            "B1-05": "all six (state line), via B4-11", "B2-02": "not present"},
    "blockers": ["None. The s601b and s602b _audit DBs (plus the 4 s602b case DBs) were created and dropped by the producers' own prepare/drop modes; batch 3's s404/s405/s408 DBs were untouched."],
    "differences": DIFFERENCES, "pairs": P,
}
(HERE / "batch-04.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")

# Human ledger
L = ["# Post-W6 audit batch 04: W1 Action/work (human ledger)", "",
     "Every disposition is a **PROPOSAL** for the Architect. This batch added no rows to `.agent/mock-departure-register.md`. Machine record: `batch-04.json`; side-by-side: `index.html`.", "",
     "## Frozen run", ""]
L += [f"- **{k}**: {v}" for k, v in doc["frozen"].items()]
L += ["", "Producers (reviewed, run unmodified, owner scratch-DB authorization 2026-10-24):",
      "- `s601b_action_walkthrough.py --db assetops_s601b_audit --work var/s601b_audit_b4` prepare / links / serve --port 18401 / drop.",
      "- `s602b_verification_walkthrough.py --db assetops_s602b_audit --work var/s602b_audit_b4` prepare (replay + 4 TEST-SCOPED case DBs) / links / serve --case guardrail --port 18401 (case API 18402) / drop.",
      "- No seeding, no API fabrication, no product edit. Every spawned PID was stopped by PID. All `_audit` DBs and work folders were dropped by the producers' drop modes. Logs are in `logs/`.", "",
      "## Route reconciliation", ""]
L += [f"- `{k}`: {v}" for k, v in doc["routes_reconciled"].items()]
L += ["", "## Blockers", ""] + [f"- {b}" for b in doc["blockers"]]
L += ["", f"## Pairs ({len(P)}, {doc['representative_pairs']} representative)", "",
      "| Screen | Case | Width | Rep | Order match | Max ratio | >1.3 panels | Dark band 390 | Console | Differences | App | Mock |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for p in P:
    L.append(f"| {p['screen']} | {p['case']} | {p['width']} | {'yes' if p['representative'] else ''} | {p['panel_order_match']} | {p['max_ratio']} | {', '.join(p['over_limit_panels'])} | {p['header_390_dark_band'] or ''} | {'ERROR' if p['console_errors'] else ''} | {', '.join(p['findings'])} | [app]({p['app_image']}) | [mock]({p['mock_image']}) |")
L += ["", "Panel titles and order match the mock on every pair, except the deliberate unknown-section error state (B4-24). App page horizontal overflow is 0 on all 50 pairs. Inner scrollers: Site tab row at 390 (B4-04), and the Activity log/History tables at 390 (readable scroll).", "",
      "## Differences and proposed dispositions", ""]
for d in DIFFERENCES:
    L += [f"### {d['id']} ({d['screens']})", "", f"- Observed: {d['observed']}", f"- Evidence: {d['evidence']}", f"- Proposed: {d['proposed_disposition']}", ""]
L += ["## Cross-cutting findings cited (not re-described)", ""] + [f"- {k}: {v}" for k, v in doc["cross_cutting_cited"].items()]
L += ["", "## Register checks", ""] + [f"- {k}: {v}" for k, v in {**doc["register_rows_verified"], **doc["register_d3_closure"]}.items()]
L += ["", "## Mandatory UI-pass checks", ""] + [f"- {k}: {v}" for k, v in doc["ui_pass_checks"].items()]
L += ["", "## Panels over 1.3x (measured reasons; each needs a reviewed ruling, none is an automatic pass)", "",
      "- recommendation P1 (B4-12): extra trial caveat, Source row, notes, disclosure and hold callout. P3 at 390 1.40x: verification chip line.",
      "- action-overview (B4-16): +1 row, multi-link Source, note lines and disclosure; at 390 long values wrap (2.05-2.40x).",
      "- action-execution (B4-17): +2 columns, state line, footer and disclosure; failed adds the apply form; at 390 narrow-column wrapping (2.69-2.90x).",
      "- action-history (B4-18): +2 columns, a code/UUID second line per row, state line and disclosure (1.46-2.42x).",
      "- action-plan (B4-21): +1 row, fixed-at line, disclosure and footer; guardrail failed-limit line (1.28-1.60x).",
      "- action-evidence (B4-22): +1 row, chip+detail cells, readings note, disclosure and footer (1.32-2.35x).", ""]
(HERE / "batch-04.md").write_text("\n".join(L), encoding="utf-8")

# HTML index
rows = []
for p in P:
    pan = "".join(f"<li>{x['title']}: {x['app_h']}/{x['mock_h']} = {x['ratio']}{' <b>&gt;1.3</b>' if x['over_limit'] else ''}</li>" for x in p["panels"])
    rows.append(f"<section id='{p['screen']}-{p['case']}-{p['width']}'><h2>{p['screen']} · {p['case']} · {p['width']}{' · representative' if p['representative'] else ''}</h2>"
                f"<p class='meta'>Route <code>{p['route']}</code> · producer {p['producer_run']} · findings: {', '.join(p['findings'])}{' · <b>console error</b>' if p['console_errors'] else ''}{' · dark band ' + str(p['header_390_dark_band']) + ' px' if p['header_390_dark_band'] else ''}</p>"
                f"<ul>{pan}</ul><div class='pair'><figure><figcaption>App</figcaption><img loading='lazy' src='{p['app_image']}'></figure>"
                f"<figure><figcaption>Mock {p['mock_hash']}</figcaption><img loading='lazy' src='{p['mock_image']}'></figure></div></section>")
diffs = "".join(f"<tr><td>{d['id']}</td><td>{d['screens']}</td><td>{d['observed']}</td><td>{d['proposed_disposition']}</td></tr>" for d in DIFFERENCES)
toc = "".join(f"<li><a href='#{p['screen']}-{p['case']}-{p['width']}'>{p['screen']} · {p['case']} · {p['width']}</a></li>" for p in P)
html = f"""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Audit batch 04</title>
<style>body{{font:13px system-ui;margin:16px;color:#17243b;background:#fff}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}}img{{width:100%;border:1px solid #ccd}}figure{{margin:0}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #dde;padding:4px;vertical-align:top;text-align:left}}.meta{{color:#456}}section{{border-top:2px solid #e0e6ef;margin-top:24px}}ul.toc{{columns:3}}</style>
<h1>Post-W6 audit batch 04 · W1 Action/work</h1><p>Frozen product code fddf5cad (branch head d66f57e6) · {len(P)} pairs · all dispositions are proposals for the Architect.</p>
<h2>Differences</h2><table><tr><th>ID</th><th>Screens</th><th>Observed</th><th>Proposed disposition</th></tr>{diffs}</table>
<h2>Pairs</h2><ul class="toc">{toc}</ul>{''.join(rows)}</html>"""
(HERE / "index.html").write_text(html, encoding="utf-8")
print(len(P), doc["representative_pairs"])
