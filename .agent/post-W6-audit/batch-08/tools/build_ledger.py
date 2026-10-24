"""Post-W6 audit batch 08 ledger builder (reads capture evidence.json files only; writes batch-08.json,
differences.json, batch-08.md and index.html). Derived from batch-06 build_ledger.py. Every disposition is a
PROPOSAL for the Architect."""
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SOURCES = [("interrupted", "evidence-part1.json"), ("interrupted", "evidence-part2.json"), ("complete", "evidence.json"),
           ("missing-meter", "evidence.json"), ("fault", "evidence.json"), ("contradictory", "evidence.json"),
           ("inventory", "evidence.json")]
SEED = ".agent/W2-F-evidence/seed.py ev {} (unmodified; W2-05b EV replay -> EV worker -> authored tariff -> EV consequence worker)"
PRODUCER = {"interrupted": SEED.format("interrupted"), "complete": SEED.format("complete") + ", reseeded in place",
            "missing-meter": SEED.format("missing-meter") + ", reseeded in place", "fault": SEED.format("fault") + ", reseeded in place",
            "contradictory": SEED.format("contradictory") + ", reseeded in place",
            "inventory": SEED.format("interrupted") + ", reseeded in place (inventory check only)"}
REP = {("ev-foundation", "stocked"), ("ev-readiness", "stocked"), ("ev-sld", "stocked"), ("sessions", "interrupted"),
       ("ev-finding", "interrupted")}
GAP = ("no-version", "refused", "no-selection", "unknown-id", "evidence-child")
FND = ["ev-foundation", "ev-readiness", "ev-sld"]
ALL = FND + ["sessions", "ev-finding"]

D = [
 ("B8-01", FND, "Status strip carries the W1 state-line items: 'Configuration v1' chip, 'Effective 2026-10-01 00:00 UTC to no end date', version select 'In effect now', a cross-link ('Configuration readiness →' / 'Single line diagram →' / 'Site evidence →'), 'How this was worked out'; readiness adds 'Set up to report', SLD adds 'Configured site'. Mock: 'Configuration v1 · Effective 6 Oct 2026 · illustrative baseline' (readiness 'Needs review · Configuration readiness is distinct from claim readiness'). Panels close with a note line and a disclosure.", "interrupted/ev-foundation-stocked-1440-{app,mock}.png", "Cite B6-01 / B1-05 (candidate D2 W1 state-line pattern); UTC part B2-21/B3-04."),
 ("B8-02", ["ev-foundation"], "Physical site: same 5 row labels; values 'Not declared' (Stationary storage; mock 'Not installed') and 'Charger session events · 2 of 2 connectors' (mock 'Charger transaction records'), plus a topology footnote and disclosure. Operating interpretation: green 'Configured'/'Mapped' chips where the mock has plain text; 'Transaction completeness: Not assessed' (mock 'Limited'); Connector status adds 'Configured clock error bound: 30 s; not an observed clock check'; 'Revenue assumption: No tariff set for estimates' (mock '$0.30/kWh · scenario'). Ratio 1.22 at 1440; 1.34 / 1.50 at 390.", "interrupted/ev-foundation-stocked-{1440,390}-{app,mock}.png", "(b) candidate D4 (selected Foundation values replace illustrative ones) + B1-05 notes; the 390 1.34x/1.50x needs a measured-cap ruling (chips + clock line + footnote + disclosure)."),
 ("B8-03", ["ev-foundation", "ev-readiness"], "Tariff statement: Foundation 'Revenue assumption: No tariff set for estimates' and Readiness Tariff row 'No tariff set for estimates · Not assessed', while the same producer authors a golden tariff through the W2-07 store path (seed log: tariff 00000502-...-025d, EV consequence revision ...025f) that EV Financials uses.", "interrupted/ev-foundation-stocked-1440-app.png; interrupted/ev-readiness-stocked-1440-app.png; logs/seed-ev-interrupted.log", "Architect check (cf. B6-14): if the Foundation revenue assumption is intentionally distinct from the authored Financials tariff, a D4 copy note ('not part of this configuration'); otherwise (c) D3 candidate (cross-screen contradiction)."),
 ("B8-04", ALL, "h1/badge/subtitle are record-derived: 'EV charging lab', 'Demonstration data · EV-LAB-001' (purple), subtitles 'EV charging · stored configuration for the period shown', 'Definition, commissioning and gateway readiness' (matches mock), 'EV charging · single line diagram', 'Performance · charging sessions and delivered service' (matches), Finding h1 'Observed EV charging interruption' / subtitle 'EV charging lab · EV charging finding' vs mock 'Depot Charging Hub', '2 × 60 kW connectors · 80 kW site limit · no stationary battery', 'Connector 2 charging session interrupted'.", "interrupted/*-1440-{app,mock}.png", "(b) candidate D4 (cite B6-03); the stored-name part is R111 (D4, ev-work screens): register correction to extend R111's screen list to these five screens."),
 ("B8-05", FND, "Closing note renders as an unboxed 14 px paragraph; mock has a bordered 11 px info callout with an icon.", "interrupted/ev-readiness-stocked-1440-{app,mock}.png", "Cite B6-04 / B1-06 / B1-07."),
 ("B8-06", ["ev-readiness"], "Readiness table: 4 rows, labels match; Confirmed is 'Unconfirmed' / 'Unconfirmed' / 'Not connected' / 'Not assessed' (mock Published / Configured / Not connected / Scenario); Declared 'Mapped' is a chip. W2 M2 stays closed ('Commissioning record' / 'Payment records feed' / 'Confirmed tariff'). Next step shows 'Financials · Not available yet' and 'Assumptions · Not available yet', but EV Financials (`/sites/:siteId/ev/financials`) and Assumptions (`/ev/financial-assumptions`) are mounted and produced since W2-07. Source: EvFoundationViews.tsx:624 and :635 (W2-05a M1 ruling, which predates W2-07).", "interrupted/ev-readiness-stocked-1440-{app,mock}.png", "Rows/Confirmed: (b) candidate D4. Stale unavailable entries: (c) D3 candidate (the destinations are built; same class as W2 M8). Not covered by R40 (Availability/Energy only)."),
 ("B8-07", ["ev-readiness"], "Gateway panel: title 'Gateway status · edge-ev-lab-001' (raw gateway id); subtitle 'configuration selected 2026-10-24 16:14 UTC' (request time); tiles 'No gateway contact recorded' / 'Not assessed' x3 (mock Online / 100% / 93.8% / +0.1 s synced); hatched 'No history to draw' bar with a 4-item legend; Connected sources lists 16 per-role reading chips (two per role per connector, plus Site import power and Billing system) with no reporting state, vs mock 4 device chips with Reporting / Stale / Never reported; Effect panel has two generic 'Not assessed' items and 'Investigation action · Not available yet'; header link 'Evidence › Data sources →' (mock 'Health › Data sources →').", "interrupted/ev-readiness-stocked-1440-{app,mock}.png", "Cite B6-06: title B1-30 + B1-53; tiles/bar/chips B1-32 candidate D1. Investigation action: (a) R36 D1 built, verified. Link target: (a) R60 verified (points to EV evidence)."),
 ("B8-08", ["ev-readiness"], "Console defect: 5 React 'Encountered two children with the same key' warnings on every readiness load (1440 and 390), keys 'Allocated power limit source', 'Energy metering source', 'Fault events source', 'Connector power source', 'Connector status source'. The Connected sources 'How this was worked out' references are built with label `${evRoleLabel(b.role)} source` (EvFoundationViews.tsx:724), and two connectors share each role label; the list keys by label.", "interrupted/ev-readiness-stocked-1440-app.png; interrupted/evidence-part1.json (consoleErrors)", "(c) D3 candidate (defect: unique key per binding, e.g. role|device|signal as the chip list already does at :701). Same class as the B4-19 duplicate-key console error."),
 ("B8-09", ["ev-readiness", "ev-sld"], "Breadcrumb adds the sub-tab leaf ('Sites / EV charging lab / Foundation / Readiness', '... / Single line diagram'); mock trail ends at Foundation.", "interrupted/ev-sld-stocked-1440-{app,mock}.png", "Cite B6-07 (candidate D2, one ruling for W1+W2)."),
 ("B8-10", ["ev-sld"], "Diagram: Grid supply is an empty 'Not declared' slot (mock icon + 'Depot connection'); 'Main CB not declared'; feeder kWh meters 'Not declared'; 'Charger 2 · Not declared · Rating not declared · No connector declared'; 'Depot auxiliary · Not declared'; bus label 'SITE FEED · Import limit 80 kW' (mock '400 / 230 V AC BUS'); Connector c1/c2 chips under Charger 1; every reporting dot 'not assessed' (legend adds 'Reporting not assessed'); title 'EV charging lab' with 'Topology type not stated in this version' (mock 'Depot Charging Hub · Depot charging hub'); italic footnote. Ratio 0.98 / 1.20.", "interrupted/ev-sld-stocked-1440-{app,mock}.png", "Undeclared slots: (a) R36 D1 built, verified. Topology/reporting: cite B6-08 / B1-40 / B1-41 (candidate D4 + D1)."),
 ("B8-11", ["ev-sld"], "'What each part does': 4 rows with mock part names; roles are configuration strings ('Site feed · Site import limit 80 kW; Load manager · Not declared', 'Charger 1 · 60 kW / 2 connectors · service hours set · 7 mapped source roles' + 'Connector details' disclosure) vs mock descriptive roles; 'What it reports' '7 configured source roles' / 'Not declared'; footnote + disclosure. W2 M14 stays CLOSED: row 3 Part reads 'Charger 2 · Not declared' (named), mock 'Charger 2 · CHG-002'. Ratio 1.29 / 1.28.", "interrupted/ev-sld-stocked-1440-{app,mock}.png", "Cite B6-09 / B1-42 (candidate D1: no function description on the record; D4 for configured values)."),
 ("B8-12", ["sessions"], "Strip: 'Sessions observed' + 'Generated test data' + 'These records came from a registered simulation, not a live charger.' vs mock 'Service needs attention · 12 attempts · keep incomplete records separate...'; contradictory case 'Records disagree' + conflict sentence (strip wraps to two lines). The mock's live 'Inspect session lineage ↗' is 'Inspect session lineage · Not available yet'.", "interrupted/sessions-interrupted-1440-{app,mock}.png; contradictory/sessions-contradictory-1440-app.png", "Chip wording: candidate D2. Lineage entry: Architect to name the destination; if it is the built EV evidence analysis (`/ev/evidence/analysis`, W2-07) then (c) D3 candidate (renderable link, as B6-10), otherwise (b) D1."),
 ("B8-13", ["sessions"], "Session service records: 1 row in every producer case (one session per replay case) vs mock 4; session cell 'Session ev-9ada0e59… · Connector c1' (truncated raw external session id) vs 'SES-011 · connector 2'; period '08:01 UTC – 08:16 UTC'; energy '15.000 kWh · complete' (three decimals; mock '3.6 kWh'); Evidence completeness is chips 'Start / Terminal / Meter / Clock' (+ 'Meter gap: 300 s', 'Competing end records', 'Meter coverage unknown') vs a plain sentence; Next step 'Open Finding →' (interrupted) but 'Not available yet' on Delivered / partial / contradictory rows (mock 'Inspect records ↗' / 'Inspect missingness ↗'); 'Energy summary →' link sits under the title where the mock has the summed-energy sentence; disclosure. The fault case renders identically to complete (one Delivered row; the c1 FAULT/CLEAR window context is not shown). Ratio 0.54 / 0.46 (fewer rows).", "interrupted/sessions-interrupted-1440-{app,mock}.png; complete/sessions-complete-1440-app.png", "Rows/values: (b) candidate D4. Raw id: B1-53 (no public session code: candidate D1, cf. R74). Next-step gaps: candidate D1. UTC: B2-21/B3-04."),
 ("B8-14", ["sessions"], "KPI tiles do not account for every attempt: missing-meter ('Completed · energy partial') and contradictory cases show Attempts 1 but Confirmed delivery 0 / Fault-aborted 0 / Incomplete 0; only the denominator line ('1 completed' / '1 contradictory') carries the attempt. The mock's tiles add up (10 + 1 + 1 = 12).", "missing-meter/sessions-missing-meter-1440-app.png; contradictory/sessions-contradictory-1440-app.png", "Architect check: tile set is the mock's four; either (c) D3 candidate (caption/qualifier that partial and contradictory attempts are outside the three outcome tiles) or a ruling that the denominator line suffices."),
 ("B8-15", ["sessions"], "Layout defect (missing-meter case, 1440): the Outcome chip 'Completed · energy partial' is wider than its column and is overpainted by the Evidence-completeness chips; the visible text ends 'energy partia' against the 'Start' chip. Not caught by the clipped-text measure (overflow visible). At 390 the table scrolls (640/318).", "missing-meter/sessions-missing-meter-1440-app.png", "(c) D3 candidate (chip wrap or column min-width)."),
 ("B8-16", ["sessions"], "'How to read the denominator' is a bold count line + 'Orphan end records: 0' + 'Unknown is separate from failure.' + disclosure at 14 px (.prose) vs mock one 12 px sentence with the equation; 'Cause remains bounded' sentence is state-specific ('A fault record and abort establish an interruption...' / 'Cause not established from accepted records.') + disclosure. Ratio 1.18 / 1.15.", "interrupted/sessions-interrupted-1440-{app,mock}.png", "Content: candidate D4 + B1-05 disclosures; 14 px: B1-07."),
 ("B8-17", ["sessions", "ev-finding"], "Refused window (from > to): Sessions keeps the strip and four 'Unknown' tiles (the cold B6-13 drop does not recur) and each panel shows one italic gap line; the Finding keeps strip + three panels. The copy 'Choose a valid UTC start and end, up to 31 days.' is the same for an inverted window as for an over-long one; the refused Sessions strip drops the lineage entry.", "interrupted/sessions-refused-1440-app.png; interrupted/ev-finding-refused-1440-app.png", "Generic copy: analogue of the domainActionClient window-error item (cite B6-13 copy part); otherwise honest refusal, no Rxx."),
 ("B8-18", ["ev-finding"], "Finding chrome: rail selects Sites (mock Findings); breadcrumb is Site-rooted 'Sites / EV charging lab / Findings / Finding' (mock 'Findings › F-130 › Overview · site: Depot Charging Hub'); the Site tab row sits above the Finding sub-tabs (390: scrolls 521/358, cut-off 'W'); the mock 'Open site' button is absent.", "interrupted/ev-finding-interrupted-{1440,390}-{app,mock}.png", "Cite B4-01 (rail), B4-03 (breadcrumb origin), B4-04 (extra Site tab row), B4-05 (Open site)."),
 ("B8-19", ["ev-finding"], "Strip: Finding code chip is the full raw UUID 'F 00000502-0000-4000-8000-00000000025b', then 'Open', 'Confidence: Observed', 'Observed interruption', 'EV charging lab' (no separator between the two), 'Generated test data' + simulation sentence; no window text (the cold Finding strip shows its window). Mock 'F-130 · Depot Charging Hub · Open · confidence Medium ⓘ · evidence limited'. W2 M13 stays CLOSED (Open + confidence present). W2 M10 stays CLOSED as written (no truncated look-alike IDs), but full UUIDs are now on screen.", "interrupted/ev-finding-interrupted-1440-{app,mock}.png", "UUID: B1-53; public code candidate D1 (EV analogue of R65/R74: no public F-code). Confidence wording 'Observed' vs 'Medium': candidate D2. Missing separator and missing window: (c) D3 candidate (minor; align with the cold Finding strip)."),
 ("B8-20", ["ev-finding"], "Bounded conclusion: lead 'A connector fault and session abort were observed; component cause and unmet demand remain unknown.' + '15.000 kWh delivered before abort · complete meter coverage' + limit sentence (14 px) + 'REC 00000502-0000-4000-8000-00000000013f · No analysis link' (raw UUID) + disclosure. The mock's 'Inspect claim evidence ↗' is absent although EV Evidence and Evidence analysis are mounted and produced (W2-07). Ratio 1.20 / 1.30.", "interrupted/ev-finding-interrupted-1440-{app,mock}.png", "Lead/values: candidate D4 + B1-05. Missing claim link: (c) D3 candidate (renderable, as B6-10). Raw REC id: B1-53. 14 px: B1-07."),
 ("B8-21", ["ev-finding"], "Operational context: Session value is the full 64-character external id 'SES ev-9ada0e5946…afa8e9' wrapping to 2 lines at 1440 and 3 at 390 (mock 'SES-011'); Connector 'Connector c1' (mock 'CHG-002'); 'Energy delta 15.000 kWh'; Outcome 'Observed abort' (mock 'Interrupted · fault event'); disclosure. Ratio 1.18 / 1.25.", "interrupted/ev-finding-interrupted-{1440,390}-{app,mock}.png", "Values: candidate D4. Session id: B1-53 (candidate D1: no public session code)."),
 ("B8-22", ["ev-finding"], "Sub-tab 'Recommendation · Not available yet' and 'Review recommendation · Not available yet' under the recorded next-step sentence, where the mock has a live 'Review recommendation' button.", "interrupted/ev-finding-interrupted-1440-{app,mock}.png", "Register R40 lists ev-finding's Recommendation as D5 'built' (W5-03), but `ev-recommendation` is still unimplemented (spec 'Outside W1-W6'): Architect to correct R40 for ev-finding to D1 or name the resolving unit (same as B6-19)."),
 ("B8-23", ["ev-finding"], "Unknown ID and refused window: generic h1 'Finding', strip 'Unknown · Confidence: Unknown' + reason ('This EV Site or record was not found.' / window copy) with no site name, three panels with one italic gap line each, unavailable Recommendation entry. No mock state. 390 dark band 146 px.", "interrupted/ev-finding-unknown-id-1440-app.png; interrupted/ev-finding-refused-390-app.png", "Cite B6-22 (shared error-state pattern, cf. B4-24); header B1-02."),
 ("B8-24", ["ev-finding"], "Mounted address variants (inventory): `/findings/:id/recommendation` renders the identical Overview with 'Overview' selected and 'Recommendation · Not available yet' (address and selected tab disagree); `/findings/:id/evidence` (likewise history, alternatives) renders generic h1 'Finding', subtitle 'EV charging lab · finding', no Finding sub-tabs, one panel 'Finding section unavailable for this site. Open Finding overview' (the gap is per Finding kind, not per site), 390 dark band 325 px. Neither is a separately counted EV mock screen: `ev-recommendation` stays unbuilt and `finding-evidence`/`finding-history` are W1 mini screens. The only other EV Finding state, the NO_LONGER_SUPPORTED withdrawn revision, is produced only inside `test_w206_ev_store_postgres._withdrawal`, not by any capture producer.", "interrupted/ev-finding-recommendation-address-1440-app.png; interrupted/ev-finding-evidence-child-{1440,390}-app.png", "Inventory: no EV Finding variant is mounted, produced and uncounted (unlike B6-23). Copy 'for this site': (c) D3 candidate (minor). Recommendation address: Architect note (redirect or select-state ruling). Tall header: B1-02."),
 ("B8-25", ["ev-findings (inventory check)"], "The EV Site's Findings tab (`/sites/EV-LAB-001/findings`, mock `#/ev-findings`) renders the W1 generic Site Findings closed state: 'Findings list closed for this Site · Not released for this Site', 'Mini-grid dispatch Findings at this site', 'No Performance comparison report exists for this Site; the file-backed comparison must run.' It does not list the produced EV Finding (reachable only from Sessions 'Open Finding'). Mock: one EV Finding row with Domain/Priority/Confidence/State/Main consequence/Lens.", "inventory/ev-findings-inventory-check-window-1440-{app,mock}.png", "Inventory: `ev-findings` correctly stays outside the target (no EV producer lists it). The mini-grid copy on an EV Site is a (c) D3 candidate for the sitefindings owner (batch 3) / Architect; no Rxx found."),
 ("B8-27", ["sessions"], "Count-noun plural with a count of 1 on the denominator line: '1 accepted starts', '1 observed aborts' (interrupted), '1 accepted starts' (complete, missing-meter, contradictory). Same class as the mandatory '1 incidents' item.", "interrupted/sessions-interrupted-1440-app.png", "(c) D3 candidate (minor copy), batched with the '1 incidents' fix."),
 ("B8-26", FND, "No-version (?at=2026-09-01): h1 keeps the display name; every panel is one gap sentence (0.17-0.49x); 390 dark band 134 px (Foundation) and 118 px (SLD), 92 px on Readiness.", "interrupted/ev-foundation-no-version-390-app.png", "Gap state: cite B6-24 (candidate D1). Header: B1-02 on ev-foundation no-version 390 only (>120 px)."),
]

ONLY = {"B8-14": ("missing-meter", "contradictory", "missing-meter-default-window", "contradictory-default-window"),
        "B8-15": ("missing-meter", "missing-meter-default-window"), "B8-17": ("refused",),
        "B8-23": ("unknown-id", "refused"), "B8-24": ("recommendation-address", "evidence-child"),
        "B8-26": ("no-version",), "B8-27": ("interrupted", "default-window", "complete", "complete-default-window", "missing-meter", "missing-meter-default-window", "contradictory", "contradictory-default-window", "fault", "fault-default-window"), "B8-25": ("inventory-check", "inventory-check-window")}
CONTENT = ("B8-02", "B8-03", "B8-06", "B8-07", "B8-08", "B8-10", "B8-11", "B8-13", "B8-16", "B8-19", "B8-20", "B8-21", "B8-12")


def load():
    seen, pairs = set(), []
    part2 = json.loads((HERE / "interrupted" / "evidence-part2.json").read_text(encoding="utf-8"))
    rerun = {(p["screen"], p["case"]) for p in part2["pairs"]}
    for ph, fn in SOURCES:
        ev = json.loads((HERE / ph / fn).read_text(encoding="utf-8"))
        for p in ev["pairs"]:
            if fn == "evidence-part1.json" and (p["screen"], p["case"]) in rerun:
                continue  # first run lost Vite mid-way; these pairs were recaptured in part 2
            key = (ph, p["screen"], p["case"], p["viewport"])
            if key in seen:
                continue
            seen.add(key)
            p["phase"] = ph
            pairs.append(p)
    return pairs


def dark390(p):
    d = [x for x in p["app"]["dark"] if x["cls"].startswith("app-frame__side") and x["w"] < 500]
    return d[0]["h"] if d and p["viewport"].startswith("390") else None


def diffs_for(p):
    s, c, w = p["screen"], p["case"], p["viewport"][:3]
    if s == "ev-findings":
        return ["B1-01", "B1-04", "B8-25"] + (["B1-03"] if w == "390" else [])
    out = ["B1-01", "B1-04"] + (["B1-03"] if w == "390" else [])
    for i, screens, *_ in D:
        if s not in screens:
            continue
        if i in ONLY and c not in ONLY[i]:
            continue
        if i in CONTENT and c in GAP + ("recommendation-address",):
            continue
        out.append(i)
    if s == "ev-finding" and c == "evidence-child":
        out = [x for x in out if x not in ("B8-22", "B8-19")]
    if dark390(p) and dark390(p) > 120:
        out.append("B1-02")
    live = c not in GAP
    if live and (s in FND or s == "sessions" or (s == "ev-finding" and c != "evidence-child")):
        out.append("B1-07")
    if live and s in ("ev-readiness", "sessions", "ev-finding"):
        out.append("B1-53")
    if s in FND or s == "sessions" or (s == "ev-finding" and c == "refused"):
        out.append("B2-21")
    return list(dict.fromkeys(out))


def summarize(p):
    a, m = p["app"], p["mock"]
    rows = []
    for i, ap in enumerate(a["panels"]):
        mp = m["panels"][i] if i < len(m["panels"]) else None
        rows.append({"title": ap["title"], "app_h": ap["h"], "mock_h": mp["h"] if mp else None,
                     "ratio": round(ap["h"] / mp["h"], 2) if mp and mp["h"] else None,
                     "app_rows": ap["rows"], "mock_rows": mp["rows"] if mp else None,
                     "app_cols": ap["columns"], "mock_cols": mp["columns"] if mp else None})
    return {"screen": p["screen"], "case": p["case"], "width": int(p["viewport"].split("x")[0]),
            "representative": (p["screen"], p["case"]) in REP, "phase": p["phase"], "producer": PRODUCER[p["phase"]],
            "route": p["app_url"], "mock": p["mock_hash"],
            "app_image": f"{p['phase']}/{p['app_image']}", "mock_image": f"{p['phase']}/{p['mock_image']}",
            "titles_app": a["titles"], "titles_mock": m["titles"], "order_match": a["titles"] == m["titles"],
            "panels": rows, "max_ratio": max([r["ratio"] for r in rows if r["ratio"]] or [0]),
            "over_1_3": [r["title"] for r in rows if r["ratio"] and r["ratio"] > 1.3],
            "overflowX": a["overflowX"], "clipped": a["clipped"], "inner_scroll": a["hscroll"],
            "dark_band_390": dark390(p),
            "fonts": {"prose_app": a["fonts"]["proseSizes"], "prose_mock": m["fonts"]["proseSizes"],
                      "h2": [(a["fonts"]["h2"] or {}).get("size"), (m["fonts"]["h2"] or {}).get("size")],
                      "td": [(a["fonts"]["td"] or {}).get("size"), (m["fonts"]["td"] or {}).get("size")]},
            "console_errors": a.get("consoleErrors", []), "differences": diffs_for(p),
            "verdict": "differences recorded; dispositions proposed"}


FROZEN = {
    "main_sha": "3be7629c (product code identical to frozen fddf5cad)",
    "branch": "audit/batch-08", "worktree": "AssetOpsV1-review5", "capture_revision": "3be7629c",
    "api": "http://127.0.0.1:18801 (host/lab_app.py via uvicorn, DATABASE_URL=assetops_audit_b08_test, PYTHONPATH = this worktree's backend/contracts/gateway/simulator/host because the shared .venv's editable installs point at the main checkout)",
    "frontend": "http://localhost:5188 Vite dev (ASSETOPS_API_PORT=18801); mock /mockups/v69/index.html#/<id>",
    "cdp": 9528, "viewports": ["1440x1000 full-page", "390x900 mobile emulation full-page"],
    "db": "assetops_audit_b08_test (created, reseeded in place per phase by the producer, dropped at the end)",
    "window": "2026-10-06T08:00Z..09:05Z, known_at 09:00Z (selected, as W2-F); 2026-10-05 same hours (no-selection); inverted (refused); no query (default-window)",
    "capture_tool": "tools/capture-b8.mjs (batch-06 capture-b6.mjs with CDP 9528; capture-only)",
}
CROSS = {
    "B1-01": "all pairs (no shell top bar)",
    "B1-03": "all 390 pairs",
    "B1-04/B2-36": "all pairs (rail 'Not available yet' on Assets/Settings)",
    "B1-02/B2-04": "ev-foundation no-version 390 (134 px), ev-finding refused/unknown-id 390 (146 px), ev-finding evidence-child 390 (325 px); all other 390 pairs 92-118 px",
    "B1-07/B2-03": "sessions '.prose' 14 px vs mock 12 px (denominator, cause); ev-finding conclusion/limit sentences 14 px; Foundation/Readiness/SLD closing lines 14 px (B8-05)",
    "B1-53": "readiness gateway id 'edge-ev-lab-001'; sessions 'ev-9ada0e59…'; ev-finding full UUIDs (F chip, REC line) and the 64-char session id (B8-19/20/21)",
    "B2-02": "not present (no page-local Window control on batch-08 screens; window only via URL)",
    "B3-01": "not present",
    "B2-21/B3-04": "Foundation effective dates, readiness gateway timestamps, sessions period column, ev-finding window refusal copy",
    "B4-01 / B4-03 / B4-04 / B4-05": "ev-finding only (B8-18). Foundation and Performance mock pages carry the same Site tab row (scrolls 521/358 at 390 in both), so B4-04 does not apply there",
    "B4-19": "no raw event-kind fall-through: outcome/evidence chips are mapped words (Fault-aborted, Delivered, Completed · energy partial, Contradictory; Start/Terminal/Meter/Clock). The duplicate-key console defect class recurs on ev-readiness (B8-08)",
}
W2F = [
    ("M2 ev-readiness blank 'What is needed'", "stays CLOSED: 'Commissioning record' / 'Commissioning record' / 'Payment records feed' / 'Confirmed tariff'"),
    ("M10 shortened record IDs on ev-finding", "stays CLOSED as written (no 'Finding 00000502' / 'Record 00000502' look-alikes); the fix shows full UUIDs and a 64-char session id instead (B1-53, B8-19/20/21)"),
    ("M13 ev-finding strip lifecycle + confidence", "stays CLOSED: 'Open' and 'Confidence: Observed' (refused/unknown: 'Unknown · Confidence: Unknown')"),
    ("M14 ev-sld parts row lost its name", "stays CLOSED: row 3 Part 'Charger 2 · Not declared', matching the diagram slot"),
    ("ev-foundation, sessions (W2 'OK')", "no regression in panel set/order; new differences are B8-01..05, B8-12..17"),
]
REG = {
    "R22": "cold-health; not on batch-08 screens",
    "R23": "cold-work-incidents; not on batch-08 screens",
    "R24": "ev-work-incidents; not on batch-08 screens",
    "R37": "cold-performance; not on batch-08 screens",
    "R38": "cold-evidence-analysis; not on batch-08 screens (EV analogue: the Finding shows 'No analysis link' rather than an unproved anchor, B8-20)",
    "R60": "ev-health extra panel not shipped (not on these screens); the readiness 'Evidence › Data sources →' link follows its EV-evidence destination (verified, B8-07)",
    "R36": "D1 built: undeclared load manager / breakers / feeder meters drawn as unknown slots on ev-sld and 'Investigation action · Not available yet' on ev-readiness: verified",
    "R40": "D5 'built': sessions Availability and Energy / site power subtabs are live (verified); ev-finding Recommendation still 'Not available yet' (B8-22), so the ev-finding part is not expired",
    "R74": "D1 planned on ev-work for 'Finding {id8}'; ev-finding itself shows the full UUID instead (B8-19)",
    "R111": "D4 stored EV-LAB-001 name, screen list is ev-work*/ev-action; the same name appears on all batch-08 screens (B8-04: extend the screen list)",
}
UI = {
    "prose_14_vs_12": "Observed (B1-07): .prose 14 px vs mock 12 px on sessions and ev-finding; Foundation closing lines 14 px.",
    "tall_dark_header_390": "Observed on ev-foundation no-version (134 px), ev-finding refused/unknown (146 px) and the ev-finding evidence child (325 px).",
    "plural_1_incidents": "Not applicable (no count+noun incident copy). Count copy reads '1 accepted starts' and '1 observed aborts' on the sessions denominator line: the same plural defect class (count of 1 with a plural noun). Proposed (c) D3 candidate together with the '1 incidents' item (B8-27).",
    "raw_EV_CONNECTOR_label": "Not observed: connector labels read 'Connector c1' / 'Connector c2' and role chips 'Connector status · Connector c1'; no 'c1 · EV_CONNECTOR' on batch-08 screens.",
    "domainActionClient_generic_window_error": "Not applicable to the client (no Action inputs). Analogue observed: the read refusal 'Choose a valid UTC start and end, up to 31 days.' is identical for inverted and over-long windows (B8-17).",
    "R88_R112_window_control": "Not applicable: no page-local Window control on these screens.",
}
OVER = [
    "ev-foundation Physical site 1.34x and Operating interpretation 1.50x at 390 (B8-02): clock-bound line, chips, footnote and disclosure.",
    "ev-finding Bounded conclusion 1.30x at 390 is at the threshold (B8-20): extra delivered-energy line, REC line and disclosure.",
]


def main():
    pairs = [summarize(p) for p in load()]
    diffs = [{"id": i, "screens": s, "observed": o, "evidence": e, "proposed": d,
              "pairs": [f"{p['screen']}/{p['case']}/{p['width']}" for p in pairs if i in p["differences"]]} for i, s, o, e, d in D]
    (HERE / "differences.json").write_text(json.dumps(diffs, indent=1, ensure_ascii=False), encoding="utf-8")
    led = {"batch": "08", "name": "W2 EV Foundation/assessment", "frozen": FROZEN, "pair_count": len(pairs),
           "representative_pairs": sum(p["representative"] for p in pairs), "pairs": pairs, "differences": diffs,
           "cross_cutting": CROSS, "w2_closure": W2F, "ui_pass_checks": UI, "register_checks": REG}
    (HERE / "batch-08.json").write_text(json.dumps(led, indent=1, ensure_ascii=False), encoding="utf-8")
    console = sorted({f"{p['screen']}/{p['case']}" for p in pairs if p["console_errors"]})
    md = ["# Post-W6 audit batch 08: W2 EV Foundation/assessment (human ledger)", "",
          "Every disposition is a **PROPOSAL** for the Architect. No register rows were added. Machine record: `batch-08.json`, `differences.json`; side-by-side: `index.html`.", "",
          "## Frozen run", ""] + [f"- **{k}**: {v}" for k, v in FROZEN.items()] + [
          "- **producer**: `.agent/W2-F-evidence/seed.py ev <case>` (the reviewed W2-F unit-5 capture seed, as batch 06), run unmodified with `ASSETOPS_TEST_DATABASE_URL=.../assetops_audit_b08_test`, `ASSETOPS_TEST_TEMPLATE=0`; phases interrupted, complete, missing-meter, fault, contradictory, then interrupted again for the inventory check. Logs in `logs/`.",
          "- **interruption**: the first Vite process (PID 23692) exited mid-run during `ev-finding/no-window`; its later pairs timed out. Vite was restarted on 5188 (PID 25824) and the five affected targets were recaptured (`logs/capture-interrupted-r2.log`, `interrupted/evidence-part2.json`); the ledger uses part 2 for them.",
          "- **pids**: API 19348, Vite 23692 (exited) and 25824 spawned here, stopped by PID; capture Chrome killed by its own wrapper. No other process or DB touched (batch 7's `assetops_audit_b07_test` left alone).", "",
          "## Route reconciliation and inventory", "",
          "- ev-foundation / ev-readiness / ev-sld: `SITE_FOUNDATION_ROUTE_PATH`, `SITE_FOUNDATION_VIEW_ROUTE_PATH` (readiness, sld) mounted.",
          "- sessions: `SITE_PERFORMANCE_SUBTAB_ROUTE_PATH` (`/performance/:capabilityId`, `sessions`) mounted; Availability and Energy subtabs live (other batches).",
          "- ev-finding: `SITE_FINDING_ROUTE_PATH` and `SITE_FINDING_VIEW_ROUTE_PATH` mounted; `/recommendation` renders the same EV Finding frame, `/evidence|history|alternatives` render a gap panel (B8-24).",
          "- Producer variants: only the `interrupted` case produces an EV Finding (`test_w206_ev_store_postgres`: every other case asserts no Finding). The withdrawn NO_LONGER_SUPPORTED revision exists only inside a test helper.",
          "- Spec table: the five batch-08 rows are correct. No EV Finding variant is mounted, produced and uncounted (contrast B6-23). `ev-findings` is mounted only as the W1 generic closed state and lists no EV Finding, so it correctly stays outside the target (B8-25). `ev-recommendation` stays unbuilt.", "",
          "## Blockers", "", "- None (one Vite exit, recovered and recaptured).", "",
          f"## Pairs ({len(pairs)}, {sum(p['representative'] for p in pairs)} representative)", "",
          "| Screen | Case | Width | Rep | Order match | Max ratio | >1.3 panels | Dark band 390 | Console | Differences | App | Mock |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for p in pairs:
        md.append(f"| {p['screen']} | {p['case']} | {p['width']} | {'yes' if p['representative'] else ''} | {p['order_match']} | {p['max_ratio']} | {', '.join(p['over_1_3'])} | {p['dark_band_390'] or ''} | {len(p['console_errors']) or ''} | {', '.join(p['differences'])} | [app]({p['app_image']}) | [mock]({p['mock_image']}) |")
    md += ["", f"Panel titles and order match the mock on every pair except the ev-finding evidence child (one gap panel; no mock state). App page horizontal overflow is 0 and the clipped-text measure is 0 on all pairs (B8-15 overlap is overflow-visible). Console errors only on: {', '.join(console) or 'none'} (B8-08). Inner scrollers at 390: Site tab row (also in the mock on Foundation/Performance), readiness table 561/318, sessions table 640/318.", "",
           "## Differences and proposed dispositions", ""]
    for d in diffs:
        md += [f"### {d['id']} ({', '.join(d['screens'])})", "", f"- Observed: {d['observed']}", f"- Evidence: {d['evidence']}", f"- Proposed: {d['proposed']}", ""]
    md += ["## Cross-cutting findings cited (not re-described)", ""] + [f"- {k}: {v}" for k, v in CROSS.items()]
    md += ["", "## Earlier W2 findings at this SHA", ""] + [f"- {k}: {v}" for k, v in W2F]
    md += ["", "## Register checks", ""] + [f"- {k}: {v}" for k, v in REG.items()]
    md += ["", "## Mandatory UI-pass checks", ""] + [f"- {k}: {v}" for k, v in UI.items()]
    md += ["", "## Panels over 1.3x (measured reasons; each needs a reviewed ruling)", ""] + [f"- {o}" for o in OVER] + [""]
    (HERE / "batch-08.md").write_text("\n".join(md), encoding="utf-8")
    h = ["<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>Batch 08 Index</title>",
         "<style>body{font:13px system-ui;margin:16px;background:#f6f7f9;color:#111}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:4px;vertical-align:top}img{width:100%;max-width:560px;border:1px solid #999}.d{font-size:11px}</style></head><body>",
         "<h1>Post-W6 audit batch 08: W2 EV Foundation/assessment</h1><p>App (left) beside v69 mock (right). Dispositions are proposals; see batch-08.md.</p><table><tr><th>Pair</th><th>App</th><th>Mock</th></tr>"]
    for p in pairs:
        h.append(f"<tr><td><b>{html.escape(p['screen'])}</b><br>{html.escape(p['case'])} · {p['width']}{' · representative' if p['representative'] else ''}<br><span class='d'>order match {p['order_match']} · max ratio {p['max_ratio']}<br>{html.escape(', '.join(p['differences']))}</span></td>"
                 f"<td><a href='{p['app_image']}'><img loading='lazy' src='{p['app_image']}'></a></td><td><a href='{p['mock_image']}'><img loading='lazy' src='{p['mock_image']}'></a></td></tr>")
    h.append("</table><h2>Differences</h2><ul>" + "".join(f"<li><b>{d['id']}</b> ({html.escape(', '.join(d['screens']))}): {html.escape(d['observed'])}<br><i>Proposed:</i> {html.escape(d['proposed'])}</li>" for d in diffs) + "</ul></body></html>")
    (HERE / "index.html").write_text("\n".join(h), encoding="utf-8")
    print(len(pairs), "pairs;", sum(p["representative"] for p in pairs), "representative;", len(diffs), "differences")


main()
