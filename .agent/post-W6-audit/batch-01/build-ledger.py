"""Post-W6 audit batch 01: builds batch-01.json and index.html from the capture evidence
(populated/evidence.json, empty/evidence.json) plus the reviewed difference list below.
Read-only over the evidence; writes only files in this folder.  python build-ledger.py
"""
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = {
    "main_sha": "fddf5cad",
    "branch": "audit/batch-01",
    "manifest_sha256": "f19aa2a30e2a5dcbc8683d04cb88c41ef75b9a95194ca2e4fc6650b9511c64af",
    "mock_index_sha256": "bf8f6723fb8c223f5207bfc7d422d5c927f587aa8da511fa8fb64be6091f8e35",
    "inventory_check": "spec table 87 + outside 23 = 110 = manifest IDs; no missing, extra or overlap",
    "clock": "server real UTC; captured 2026-10-24 ~12:55-13:10 UTC (Foundation v13, effective 2026-10-21, is the period in effect)",
    "api": "http://127.0.0.1:18101 (one API at a time: populated, then empty)",
    "frontend": "http://localhost:5181 (Vite dev, ASSETOPS_API_PORT=18101); mock at /mockups/v69/index.html#/<id>",
    "viewports": ["1440x1000 (full-page capture)", "390x900 mobile emulation (full-page capture)"],
    "capture_tool": ".agent/post-W6-audit/batch-01/capture-b1.mjs (copy of tools/w1-fidelity-evidence.mjs @fddf5cad + DOM-only measurements; CDP port 9481)",
    "launcher": ".agent/post-W6-audit/batch-01/serve-one.py (starts ONE API of v01a serve mode with the tool's own env/tree; no writes)",
}
PRODUCER = {
    "s601b": "tools/s601b_action_walkthrough.py --db assetops_s601b_audit --work var/s601b_audit prepare; serve --port 18101 --web-port 5181 (unmodified; owner authorization 2026-10-24); dropped by its drop mode",
    "s701": "tools/s701_health_walkthrough.py --db assetops_s701_owner_audit --work var/s701_owner_audit prepare; serve --port 18101 --web-port 5181; deliver (unmodified; owner authorization 2026-10-24); dropped by its drop mode",
    "populated": "tools/v01a_foundation_walkthrough.py --db assetops_audit_b1_walk_test --empty-db assetops_audit_b1_empty_test "
                 "--work-name audit-b1-v01a prepare  (copy of assetops_s4cases, KOBO-001; then serve-one.py --which populated --port 18101)",
    "empty": "same prepare; serve-one.py --which empty --port 18101 (migrated DB, no Site)",
}
SELECTED = {
    "s601b": "KOBO-001; Action d23ec457-3aa6-4a7e-8dca-7f8f76393c81; applied change f272ee05-9239-4a66-b63f-d2108e9d6ca4 (D-action-records builder, fixture clock 2026-10-29..11-01)",
    "s701": "KOBO-001 battery asset 2661fe42-55be-4ad4-bb96-9e653d18231a (condition Unknown); KOBO-002 (no battery) refusal with asset 00000000-0000-4000-8000-000000000000",
    "populated": "Site KOBO-001 (site_uuid 194c2aeb-9b2a-415e-9cd8-6df7292356eb), Foundation v13 rev ecd48de2-e29e-4251-9089-fe117ba36210, "
                 "binding set v12 rev 96eae0e1-bb25-413e-98f4-7b8ad169dd79; battery asset 9f7a0a29-c36f-46a0-8203-46a69ccde612",
    "empty": "no Site stored",
}
REPRESENTATIVE = {("sites", "stocked"), ("foundation", "now"), ("readiness", "now"), ("sld", "now"),
                  ("changes", "applied"), ("asset", "kobo001-battery")}
LIMIT = 1.3

# Every observed difference. disposition = PROPOSAL only; the Architect assigns register IDs.
D = [
    # shell / all six screens
    ("B1-01", "*", "Mock topbar (org path 'Bineyame Operations / Demo estate', Find a screen, Site picker, Window picker, avatar) is absent on every screen at 1440 and 390.",
     "(b) candidate D1 shell row: no global search, user menu or shared topbar slot. R88/R112 cover only the Work-page Window control (cold/EV Work) and do not extend to these screens."),
    ("B1-02", "changes,asset", "Short 390 pages: the dark mobile header band stretches to 165 px (changes no-selection), 157 px (changes unknown-id) and 369 px (asset unknown-site refusal), against 92 px on normal pages and no dark band in the mock (white topbar).",
     "(c) D3 shell defect = carried UI-pass item 'tall dark shell header on short 390 pages'. Shared shell fix owner."),
    ("B1-03", "*", "At 390 the app shows a 92 px dark brand band with a Menu button where the mock shows a white topbar (org path, Site picker, Window, avatar) and hides the rail.",
     "(b) candidate D2 shell row (W1-F5a carry 5 phone Menu); no register row exists."),
    ("B1-04", "*", "Rail: Assets and Settings show 'Not available yet' (mock live); mock rail footer 'Demo workspace / 3 sites - illustrative records' absent; 'Open Simulator Lab' vs mock 'Simulator Lab'.",
     "(b) candidate D1 for unmounted global Assets/Settings (relate to R09, which is maintenance-preventive only); footer = candidate D4 (illustrative count)."),
    ("B1-05", "foundation,readiness,sld,changes,asset,sites", "W1 state-line pattern: status strip carries version select, 'As of', 'How this was worked out', and panels close with 'Advanced details'/'Technical details' disclosures; mock strips are one line with no disclosures.",
     "(b) candidate D2 shell-pattern row (W1-UX provenance/state line, owner-accepted conditionally in W1); no Rxx exists."),
    ("B1-06", "readiness,sites,sld,changes,asset", "Mock closes each page with a bordered info callout (11 px). App: readiness renders its closing note as an unboxed 14 px paragraph; sites, sld and changes have none; asset has a different callout ('Unknown here means...').",
     "readiness 14 px unboxed note: (c) D3 typography/structure (callout primitive exists). Missing sites/sld/changes callouts: (b) candidate D4 (mock texts assert illustrative facts: reporting dots, illustrative proposal). Asset: see B1-64."),
    ("B1-07", "sites,foundation,sld,asset,readiness", "Body sentences render at 14 px against mock 11-12 px: sites empty (5 paragraphs at 14 px), foundation reserve-form intro, sld unknown-part notice, asset unknown-asset refusal text, readiness closing note. These screens use no `.prose` class; the one mock `.prose` (asset Interpretation lead, 12 px) is matched at 12 px.",
     "(c) D3 shared typography = carried UI-pass '.prose 14 px vs 12 px' item; shared typography fix owner."),
    # sites
    ("B1-10", "sites", "Sub-tab row Directory / Add site - form / From template / Batch upload / Setup history is absent; app shows a 'Create a site in the Simulator Lab' button instead, with no 'Not available yet' label.",
     "(b) candidate D1 (site-create-form/-template/-batch-upload/-setup-history are outside W1-W6). Unlabelled today, so it needs the visible label."),
    ("B1-11", "sites", "Type chips: All sites, Mini-grid only (mock adds Cold-chain, EV charging).",
     "Value/data: the fixture stores only a mini-grid Site. If the chips are derived from stored types, there is no disposition. Architect to verify that they are data-derived; if they are fixed, candidate D4."),
    ("B1-12", "sites", "Metric cards Needs attention and Evidence limited read 'Not available' with a reason, where the mock shows counts.",
     "(b) candidate D1 (no cross-site assessment/aggregation contract)."),
    ("B1-13", "sites", "Site inventory columns: mock Assessment / Top issue / Evidence / Last analysed are collapsed into one 'Operating view: Not available yet' column; app adds Setup details (disclosure) and Actions (View) columns and a footnote line.",
     "(b) candidate D1 for the four missing columns, plus candidate D2 for the added Setup details/Actions columns."),
    ("B1-14", "sites,foundation", "Mode chip: app shows green 'Demonstration data' where the mock shows a neutral/purple 'Simulated' provenance chip. Green is the healthy/success tone.",
     "Wording: candidate D4. Tone: (c) D3 candidate (a provenance label uses a status-success tone; a neutral token exists)."),
    ("B1-15", "sites", "In setup: header buttons (+ Form, From template, Batch upload) absent; columns Created by / State / Next step / Created replaced by Lifecycle; closing 'Setup progress not available' line.",
     "(b) candidate D1 (no setup-progress read or create flows)."),
    ("B1-16", "sites", "Subtitle 'Every site configured in this build.' vs mock 'Find and compare sites across the operating estate'; mock root breadcrumb 'Sites >' above the h1 is absent.",
     "Subtitle: candidate D4. Breadcrumb: (c) minor D3 candidate (faithfully renderable)."),
    # foundation
    ("B1-20", "foundation", "Panel title 'Identity and operating obligations' vs mock 'Identity & operating obligations'. Approved in W1-F1, but there is no register row.",
     "(b) candidate D2 row (plain-language 'and')."),
    ("B1-21", "foundation", "Topology cards use paired icons and underlined part links where the mock has a single centred icon; the AC bus rule is blue in the app and green/teal in the mock.",
     "Links/icons: candidate D2 (part selection carries ?component to SLD/readiness). Bus colour: (c) D3 candidate (colour token mismatch)."),
    ("B1-22", "foundation", "Identity panel: 10 rows vs 6; values sit in a left-aligned second column without row rules (mock: right-aligned values with rules); monospace 'KOBO-001' wraps to 'KOBO-/001'. Topology panel is stretched to the same row height (1.50x at 1440).",
     "Rows: data (W1-F5b overage reason carried; needs a register ruling for >1.3x). KV alignment and code wrap: (c) D3 candidate."),
    ("B1-23", "foundation", "Control table: 5 rows vs 4 (adds Critical service order); Evidence/change cells are plain text where the mock has links (Published policy, Review proposed change, Constraint evidence, See actual operation); one 'Open Dispatch' link exists.",
     "Extra row: data. Missing links: candidate D1 (no change list or constraint-evidence target)."),
    ("B1-24", "foundation", "The working 'Change the battery reserve' form (intro, two fields, Publish) and 'Advanced details' sit inside Time-valid control configuration, which is not drawn in the mock. Panel is 2.64x (1440) and 2.93x (390).",
     "(b) candidate D2 (S6 publish capability placed on Foundation) with a measured >1.3x reason. Needs a reviewed ruling."),
    ("B1-25", "foundation,readiness", "No-version state (?at=2026-09-01): h1 shows the Site code 'KOBO-001' instead of the stored display name 'Kobo mini-grid', although the Site read returns display_name.",
     "(c) D3 candidate, pending an Architect check of whether the name must come from the Foundation version (then D1)."),
    # readiness
    ("B1-30", "readiness", "Panel title 'Gateway status - edge-kobo-001' vs mock 'GW-MG-01' (dynamic from the selected read; approved in W1-F1). No-version title 'Gateway status - No gateway selected'.",
     "(b) candidate D4 (illustrative gateway id replaced by the selected record)."),
    ("B1-31", "readiness", "Readiness table: last column 'Next step' vs mock 'Owner'; 6 areas vs 5, with different area names; three note lines and a disclosure under the table (1.63x/1.99x).",
     "'Owner': candidate D1 (no owner field). Next step and notes: candidate D2. >1.3x carried W1-F5b reason needs a ruling."),
    ("B1-32", "readiness", "Gateway panel: the contact timeline bar and legend are absent; Availability and Data completeness read 'Not available'; app adds a Registered gateway/Registration/Central contact block and a diagnostic disclosure (1.47x/1.55x).",
     "(b) candidate D1 (no uptime/completeness source) plus candidate D2 for the added block. Needs a ruling for >1.3x."),
    # sld
    ("B1-40", "sld", "Panel title 'Kobo mini-grid' with no '- AC-coupled mini-grid' suffix; the subtitle says 'Topology type not stated in this version'. The W1-F1 packet recorded the title '{site name} - {site type}'.",
     "(b) candidate D1 (topology type not declared in Foundation). Architect to check this against the W1-F1 approved title: if the type suffix regressed, it is a D3."),
    ("B1-41", "sld", "Protection (CBs), feeder kWh meters, the Monitoring & communication row and reporting-status dots are absent; each part reads 'Readings not assessed here'; legend DC/AC/Fuel vs mock AC/DC/Monitoring/Circuit breaker/Reporting/Gap/Not connected.",
     "(b) candidate D1 for mini SLD (R36 is the EV-only analogue)."),
    ("B1-42", "sld", "'What each part does' columns are Part / Type / Declared rating / Channels with 10 per-part rows, against mock Part / Role at this site / What it reports with 4 grouped rows.",
     "(b) candidate D1 (no role/reporting description stored) plus candidate D2 (per-part rows). Panel 2.23x at 1440, 1.95x at 390: measured reason is the 10 rows plus the intro and disclosure; needs a ruling."),
    ("B1-43", "sld", "Diagram panel is 1.63x/1.84x at 1440 and 3.84x/4.51x at 390. At 390 the app keeps the drawing full size in an inner horizontal scroller (952 px in 316 px), while the mock scales the diagram down to 318 px tall.",
     "Needs a reviewed ruling: candidate D2 (readability) or, if scale-to-fit is the faithful alternative, (c) D3. Measured reason: 9 parts in 4 rows plus a selected-part box and notes."),
    # changes
    ("B1-50", "changes", "RESOLVED by the owner's producer scratch-DB authorization (2026-10-24, main 1db7360c): the unmodified s601b producer (assetops_s601b_audit) gave the applied change, captured as changes:applied at 1440/390. The s602b 'later effect' state is still not captured: s602b `serve`/`capture` always start a second, TEST-SCOPED API on --port+1 (18102), outside this batch's port allocation (18101/5181).",
     "Resolved for applied. Effect state: needs a second API port (or a coordinator ruling), then rerun s602b unmodified."),
    ("B1-51", "changes", "No-selection and unknown-ID states: an amber notice 'No change selected... no list of Foundation changes yet' and two panels with one-line gap statements; the mock has a strip, 4 KPI cards, a before/proposed table, decision steps and a callout. Panel titles and order match (2/2).",
     "(b) candidate D1 (no Foundation change list); honest missing state."),
    # asset
    ("B1-60", "asset", "Asset-rooted chrome absent: the mock has the Assets rail entry active, breadcrumb Assets > BAT-001 > Health, asset tabs (Overview, Health, Performance, Configuration, Work, Evidence, Warranty) and an 'Open site' button. The app is Site-rooted (Sites active, Site tabs, breadcrumb Sites / Kobo mini-grid / Health / Battery).",
     "(b) candidate D1 (asset-* screens are outside W1-W6)."),
    ("B1-61", "asset", "Panel 3 title 'Condition evidence and its limits' vs mock 'Condition evidence and claim boundary'.",
     "(b) candidate D2 (client-facing plain language); no register row."),
    ("B1-62", "asset", "Reserve exposure and Power stress read 'Not available'; the weekly breach bars are absent (a KV list stands in); KPI top-border tones are absent.",
     "(b) candidate D1 (no accepted SOC/power history on this page)."),
    ("B1-63", "asset", "Interpretation: 3 numbered missing inputs vs 2 actions; 'Create test action' and 'Review capability gap' links absent (capacity-test action stated unavailable). 1.31x at 390.",
     "(b) candidate D1. The ~1.31x carries the W1-F5b reason and needs a ruling."),
    ("B1-64", "asset", "Warranty callout replaced by 'Unknown here means not yet measurable... Back to Health'; 'Technical details' disclosure added.",
     "Warranty: candidate D1. Disclosure: covered by B1-05 D2."),
    ("B1-65", "asset", "h1 'Battery energy storage' (Foundation display name) vs 'Kobo battery'; subtitle has no asset code (mock BAT-001).",
     "(b) candidate D4 (illustrative name/code)."),
    ("B1-66", "asset", "Refusals: the W1-F5b 3-slot refusal (s701, stored KOBO-002 with no battery) is now captured. The three panel titles match the mock, with one-sentence gap statements at 14 px (B1-07) and the generic h1 'Battery'. Unknown asset on KOBO-001 gives the same 3-slot pattern. Unknown Site gives 'Site not found' / 'No such site' (1 panel vs mock 3) with the 369 px band at 390 (B1-02). The s701 battery capture equals the v01a one (same panel heights).",
     "Refusal structure: existing W1-F5b accepted pattern (no Rxx). Architect to confirm or register it. Generic h1 'Battery' on refusal: candidate D4."),
    ("B1-52", "changes", "Applied state: table header 'After' vs mock 'Proposed'; 2 rows (Battery reserve, Foundation version) vs 4; the Target and Guardrails cards read 'Not recorded yet' and Outcome reads 'No verification plan yet'; Decision path step 1 has no 'Inspect plan' link ('Not recorded yet') and step 2 adds 'Application record'. Panel 1.26x (1440) and 1.34x (390).",
     "Header: candidate D4 (state-correct label for an applied change). Cards/links: candidate D1 (no frozen plan in this record). 1.34x at 390: carried W1-F5b reason (outcome/applied-by rows, failed attempts, disclosure); needs a ruling."),
    ("B1-53", "changes", "Applied state shows raw system vocabulary: a battery asset UUID in monospace ('Battery 2deeca26-...') and failure codes ACTION_FOUNDATION_STALE, ACTION_VALUE_INVALID and ACTION_EFFECTIVE_TIME_INVALID in the 'earlier attempts' line.",
     "(c) D3 candidate (client-facing copy: no system vocabulary; the plain-language mapping is renderable). Shared copy fix owner, like the carried raw 'c1 - EV_CONNECTOR' label."),
    ("B1-54", "changes", "Breadcrumb leaf is 'Change' on the applied state and 'Change & effect' on the bare page; mock 'Sites > Kobo Mini-grid > Foundation'. The page-end note is a left-bar 13 px note against the mock's boxed 11 px info callout.",
     "Breadcrumb: (c) minor D3 candidate (inconsistent leaf). Note style/size: part of B1-06/B1-07."),
]
SCREEN_DIFFS = {}
for did, screens, *_ in D:
    for s in (["sites", "foundation", "readiness", "sld", "changes", "asset"] if screens == "*" else screens.split(",")):
        SCREEN_DIFFS.setdefault(s, []).append(did)


def load(folder):
    ev = json.loads((HERE / folder / "evidence.json").read_text(encoding="utf-8"))
    return folder, ev


pairs = []
for folder, ev in (load("populated"), load("empty"), load("s601b"), load("s701")):
    for p in ev["pairs"]:
        a, m = p["app"], p["mock"]
        width = p["viewport"].split("x")[0]
        panels = []
        for i, ap in enumerate(a["panels"]):
            mp = m["panels"][i] if i < len(m["panels"]) else None
            ratio = round(ap["h"] / mp["h"], 2) if mp and mp["h"] else None
            panels.append({"title": ap["title"], "app_h": ap["h"], "mock_title": mp and mp["title"], "mock_h": mp and mp["h"],
                           "ratio": ratio, "over_limit": bool(ratio and ratio > LIMIT),
                           "app_rows": ap["rows"], "mock_rows": mp and mp["rows"], "app_columns": ap["columns"],
                           "mock_columns": mp and mp["columns"], "app_links": ap["links"], "mock_links": mp and mp["links"],
                           "app_chips": ap["chips"], "mock_chips": mp and mp["chips"], "app_disclosures": ap["disclosures"]})
        case = p["case"]
        refusal = case in ("unknown-site",)
        diffs = SCREEN_DIFFS.get(p["screen"], [])
        over = [x["title"] for x in panels if x["over_limit"]]
        if a["titles"] != m["titles"] and not refusal:
            verdict_note = "titles differ in text only (see differences)" if len(a["titles"]) == len(m["titles"]) else "panel count differs"
        else:
            verdict_note = "panel count and order match" if not refusal else "refusal state (1 panel by design)"
        pairs.append({
            "screen": p["screen"], "case": case, "width": width, "representative": (p["screen"], case) in REPRESENTATIVE,
            "route": p["app_url"].replace("http://localhost:5181", ""), "app_url": p["app_url"], "mock_hash": p["mock_hash"],
            "producer": PRODUCER[folder], "selected": SELECTED[folder], "window": "none (Foundation views use ?at= or now)",
            "app_titles": a["titles"], "mock_titles": m["titles"], "panel_count_match": len(a["titles"]) == len(m["titles"]),
            "panels": panels, "max_ratio": max([x["ratio"] for x in panels if x["ratio"]] or [None]) if panels else None,
            "over_limit_panels": over,
            "typography": {k: {"app": a.get(k), "mock": m.get(k)} for k in ("h1", "h2", "prose", "td", "th", "body")}
            | {"panel_paragraph_sizes": {"app": a["panelP"]["sizes"], "mock": m["panelP"]["sizes"]},
               "page_end_note": {"app": a["pageEndNote"], "mock": m["pageEndNote"]},
               "prose_class_count": {"app": a["proseCount"], "mock": m["proseCount"]}},
            "colours": {"body_bg": {"app": a["bodyBg"], "mock": m["bodyBg"]}, "panel": {"app": a["panelStyle"], "mock": m["panelStyle"]},
                        "rail": {"app": a["side"], "mock": m["side"]}},
            "shell": {"first_panel_y": {"app": a["firstPanelY"], "mock": m["firstPanelY"]},
                      "dark_band_390_px": a["side"]["h"] if width == "390" and a["side"] else None,
                      "page_height": {"app": a["pageHeight"], "mock": m["pageHeight"]}},
            "tabs": {"app": a["tabs"], "mock": m["tabs"]},
            "overflow_x": a["overflowX"], "clipped_text_candidates": a["clipped"],
            "clipped_note": "the listed leaves are visually-hidden labels/select text (sr-only clip), not clipped material text" if a["clipped"] else None,
            "inner_scrollers": a["innerScroll"],
            "app_image": f"{folder}/{p['app_image']}", "mock_image": f"{folder}/{p['mock_image']}",
            "findings": diffs, "structure_note": verdict_note,
            "reviewer_verdict": "PROPOSED: needs Architect classification. "
                                + ("Structural D3 candidate present. " if any(x in diffs for x in ("B1-02", "B1-06", "B1-07", "B1-14", "B1-21", "B1-22", "B1-25", "B1-53", "B1-54")) else "")
                                + (f"Panels >1.3x without a register ruling: {over}." if over else "No panel >1.3x."),
        })

out = {"batch": "01", "name": "W1 shell/Foundation", "ids": ["sites", "foundation", "readiness", "sld", "changes", "asset"],
       "frozen": FROZEN, "routes_reconciled": {
           "sites": "/sites (SITES_PATH) mounted", "foundation": "/sites/:siteId/foundation mounted",
           "readiness": "/sites/:siteId/foundation/:foundationView (readiness) mounted",
           "sld": "/sites/:siteId/foundation/:foundationView (sld) mounted",
           "changes": "/sites/:siteId/foundation/changes and /changes/:changeId mounted",
           "asset": "/sites/:siteId/assets/:assetId mounted",
           "note": "/sites/:siteId/assets (SiteAssetsFrame, the 'Battery' list) is also mounted; it is the intermediate breadcrumb of `asset`, not the manifest `assets` register. Architect to confirm it stays out of the denominator."},
       "pair_count": len(pairs), "representative_pairs": sum(1 for p in pairs if p["representative"]),
       "register_d3_closure": {"R22": "cold-health; not on batch-01 screens", "R23": "cold-work-incidents; not on batch-01 screens",
                               "R24": "ev-work-incidents; not on batch-01 screens", "R37": "cold-performance; not on batch-01 screens",
                               "R38": "cold-evidence-analysis; not on batch-01 screens", "R60": "ev-health; not on batch-01 screens"},
       "ui_pass_checks": {
           "prose_14_vs_12": "Observed: 14 px body sentences on sites-empty, foundation form intro, sld unknown-part, asset unknown-asset, readiness closing note (B1-07). Asset `.prose` lead matches at 12 px.",
           "tall_dark_header_390": "Observed: 165/157 px (changes), 369 px (asset unknown-site refusal) vs 92 normal (B1-02).",
           "plural_1_incidents": "Not applicable: no count+noun copy on these screens.",
           "raw_EV_CONNECTOR_label": "Not applicable: mini Site only.",
           "domainActionClient_generic_window_error": "Not applicable: no domain-action window inputs on these screens; the Foundation reserve form was not submitted (capture-only).",
           "R88_R112_window_control": "Not applicable: no Window control on these screens.",
       },
       "blockers": ["B1-50 resolved for the applied state (owner scratch-DB authorization). Remaining gap: the s602b 'later effect' change state needs a second API port (s602b serve/capture bind --port+1); not captured."],
       "differences": [{"id": d[0], "screens": d[1], "observed": d[2], "proposed_disposition": d[3]} for d in D],
       "pairs": pairs}
(HERE / "batch-01.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

e = html.escape
rows = []
for p in pairs:
    pan = "".join(f"<li>{e(x['title'])}: {x['app_h']} / {x['mock_h']} = {x['ratio']}{' <b>&gt;1.3</b>' if x['over_limit'] else ''}</li>" for x in p["panels"])
    rows.append(f"""<section id="{e(p['screen'])}-{e(p['case'])}-{p['width']}"><h2>{e(p['screen'])} - {e(p['case'])} - {p['width']}{' (representative)' if p['representative'] else ''}</h2>
<p><code>{e(p['route'])}</code> vs mock <code>{e(p['mock_hash'])}</code>. {e(p['structure_note'])}. Overflow-x {p['overflow_x']}. Differences: {', '.join(f'<a href="#{d}">{d}</a>' for d in p['findings'])}</p>
<p>App: {e(' | '.join(p['app_titles']))}<br>Mock: {e(' | '.join(p['mock_titles']))}</p><ul>{pan}</ul>
<div class="pair"><figure><figcaption>App</figcaption><img loading="lazy" src="{e(p['app_image'])}"></figure><figure><figcaption>Mock</figcaption><img loading="lazy" src="{e(p['mock_image'])}"></figure></div></section>""")
diffs = "".join(f"<tr id='{d[0]}'><td>{d[0]}</td><td>{e(d[1])}</td><td>{e(d[2])}</td><td>{e(d[3])}</td></tr>" for d in D)
(HERE / "index.html").write_text(f"""<!doctype html><meta charset="utf-8"><title>Post-W6 audit batch 01</title>
<style>body{{font:13px system-ui;margin:16px;max-width:1600px}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}}img{{width:100%;border:1px solid #ccc}}figure{{margin:0}}table{{border-collapse:collapse}}td{{border:1px solid #ddd;padding:4px;vertical-align:top}}</style>
<h1>Post-W6 audit batch 01: W1 shell/Foundation</h1><p>Main {FROZEN['main_sha']} - {len(pairs)} pairs - dispositions are PROPOSALS for the Architect.</p>
<h2>Differences</h2><table><tr><td>ID</td><td>Screens</td><td>Observed</td><td>Proposed disposition</td></tr>{diffs}</table>
{''.join(rows)}""", encoding="utf-8")
print(f"{len(pairs)} pairs; {len(D)} differences")
