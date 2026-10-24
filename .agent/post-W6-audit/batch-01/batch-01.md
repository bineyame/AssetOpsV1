# Post-W6 audit batch 01: W1 shell/Foundation (human ledger)

Every disposition below is a **PROPOSAL**. The Architect classifies each one and assigns register IDs; this batch added no rows to `.agent/mock-departure-register.md`.

## Frozen run

- **main_sha**: fddf5cad
- **branch**: audit/batch-01
- **manifest_sha256**: f19aa2a30e2a5dcbc8683d04cb88c41ef75b9a95194ca2e4fc6650b9511c64af
- **mock_index_sha256**: bf8f6723fb8c223f5207bfc7d422d5c927f587aa8da511fa8fb64be6091f8e35
- **inventory_check**: spec table 87 + outside 23 = 110 = manifest IDs; no missing, extra or overlap
- **clock**: server real UTC; captured 2026-10-24 ~12:55-13:10 UTC (Foundation v13, effective 2026-10-21, is the period in effect)
- **api**: http://127.0.0.1:18101 (one API at a time: populated, then empty)
- **frontend**: http://localhost:5181 (Vite dev, ASSETOPS_API_PORT=18101); mock at /mockups/v69/index.html#/<id>
- **viewports**: 1440x1000 (full-page capture); 390x900 mobile emulation (full-page capture)
- **capture_tool**: .agent/post-W6-audit/batch-01/capture-b1.mjs (copy of tools/w1-fidelity-evidence.mjs @fddf5cad + DOM-only measurements; CDP port 9481)
- **launcher**: .agent/post-W6-audit/batch-01/serve-one.py (starts ONE API of v01a serve mode with the tool's own env/tree; no writes)

Producers, all reviewed and run unmodified:
- `v01a_foundation_walkthrough.py` prepare (a copy of `assetops_s4cases`, DBs `assetops_audit_b1_*_test`). Its APIs were started one at a time by `serve-one.py` with the tool's own env, because v01a's serve always starts two APIs.
- `s601b_action_walkthrough.py` (`assetops_s601b_audit`), serve on 18101.
- `s602b_verification_walkthrough.py` (`assetops_s602b_audit` plus its four case DBs), serve on 18101, with its TEST-SCOPED case API on the authorised 18102.
- `s701_health_walkthrough.py` (`assetops_s701_owner_audit`), serve on 18101 plus deliver.

The `_audit` DB names follow the owner's producer scratch-DB authorization (2026-10-24). Each DB was dropped by its producer's drop mode. There was no seeding, no API fabrication and no product edit; every spawned PID was stopped by PID.

## Route reconciliation

- `sites`: /sites (SITES_PATH) mounted
- `foundation`: /sites/:siteId/foundation mounted
- `readiness`: /sites/:siteId/foundation/:foundationView (readiness) mounted
- `sld`: /sites/:siteId/foundation/:foundationView (sld) mounted
- `changes`: /sites/:siteId/foundation/changes and /changes/:changeId mounted
- `asset`: /sites/:siteId/assets/:assetId mounted
- `note`: /sites/:siteId/assets (SiteAssetsFrame, the 'Battery' list) is also mounted; it is the intermediate breadcrumb of `asset`, not the manifest `assets` register. Architect to confirm it stays out of the denominator.

## Blockers / gaps

- None. B1-50 fully resolved (s601b applied, s602b effect captured).

## Pairs (40, 12 representative)

| Screen | Case | Width | Rep | Count match | Max ratio | >1.3 panels | Dark band 390 | Differences | App | Mock |
|---|---|---|---|---|---|---|---|---|---|---|
| sites | stocked | 1440 | yes | True | 0.92 |  |  | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-10, B1-11, B1-12, B1-13, B1-14, B1-15, B1-16 | [app](populated/sites-stocked-1440-app.png) | [mock](populated/sites-stocked-1440-mock.png) |
| sites | stocked | 390 | yes | True | 1.22 |  | 92 | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-10, B1-11, B1-12, B1-13, B1-14, B1-15, B1-16 | [app](populated/sites-stocked-390-app.png) | [mock](populated/sites-stocked-390-mock.png) |
| foundation | now | 1440 | yes | True | 2.64 | Configured topology, Identity and operating obligations, Time-valid control configuration |  | B1-01, B1-03, B1-04, B1-05, B1-07, B1-14, B1-20, B1-21, B1-22, B1-23, B1-24, B1-25 | [app](populated/foundation-now-1440-app.png) | [mock](populated/foundation-now-1440-mock.png) |
| foundation | now | 390 | yes | True | 2.93 | Identity and operating obligations, Time-valid control configuration | 92 | B1-01, B1-03, B1-04, B1-05, B1-07, B1-14, B1-20, B1-21, B1-22, B1-23, B1-24, B1-25 | [app](populated/foundation-now-390-app.png) | [mock](populated/foundation-now-390-mock.png) |
| foundation | no-version | 1440 |  | True | 0.35 |  |  | B1-01, B1-03, B1-04, B1-05, B1-07, B1-14, B1-20, B1-21, B1-22, B1-23, B1-24, B1-25 | [app](populated/foundation-no-version-1440-app.png) | [mock](populated/foundation-no-version-1440-mock.png) |
| foundation | no-version | 390 |  | True | 0.36 |  | 92 | B1-01, B1-03, B1-04, B1-05, B1-07, B1-14, B1-20, B1-21, B1-22, B1-23, B1-24, B1-25 | [app](populated/foundation-no-version-390-app.png) | [mock](populated/foundation-no-version-390-mock.png) |
| foundation | imported-period | 1440 |  | True | 2.64 | Configured topology, Identity and operating obligations, Time-valid control configuration |  | B1-01, B1-03, B1-04, B1-05, B1-07, B1-14, B1-20, B1-21, B1-22, B1-23, B1-24, B1-25 | [app](populated/foundation-imported-period-1440-app.png) | [mock](populated/foundation-imported-period-1440-mock.png) |
| foundation | imported-period | 390 |  | True | 2.93 | Identity and operating obligations, Time-valid control configuration | 92 | B1-01, B1-03, B1-04, B1-05, B1-07, B1-14, B1-20, B1-21, B1-22, B1-23, B1-24, B1-25 | [app](populated/foundation-imported-period-390-app.png) | [mock](populated/foundation-imported-period-390-mock.png) |
| readiness | now | 1440 | yes | True | 1.63 | Readiness and commissioning evidence, Gateway status · edge-kobo-001 |  | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-25, B1-30, B1-31, B1-32 | [app](populated/readiness-now-1440-app.png) | [mock](populated/readiness-now-1440-mock.png) |
| readiness | now | 390 | yes | True | 1.99 | Readiness and commissioning evidence, Gateway status · edge-kobo-001 | 92 | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-25, B1-30, B1-31, B1-32 | [app](populated/readiness-now-390-app.png) | [mock](populated/readiness-now-390-mock.png) |
| readiness | no-version | 1440 |  | True | 0.42 |  |  | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-25, B1-30, B1-31, B1-32 | [app](populated/readiness-no-version-1440-app.png) | [mock](populated/readiness-no-version-1440-mock.png) |
| readiness | no-version | 390 |  | True | 0.36 |  | 92 | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-25, B1-30, B1-31, B1-32 | [app](populated/readiness-no-version-390-app.png) | [mock](populated/readiness-no-version-390-mock.png) |
| sld | now | 1440 | yes | True | 2.23 | Kobo mini-grid, What each part does |  | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-40, B1-41, B1-42, B1-43 | [app](populated/sld-now-1440-app.png) | [mock](populated/sld-now-1440-mock.png) |
| sld | now | 390 | yes | True | 3.84 | Kobo mini-grid, What each part does | 92 | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-40, B1-41, B1-42, B1-43 | [app](populated/sld-now-390-app.png) | [mock](populated/sld-now-390-mock.png) |
| sld | battery | 1440 |  | True | 2.23 | Kobo mini-grid, What each part does |  | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-40, B1-41, B1-42, B1-43 | [app](populated/sld-battery-1440-app.png) | [mock](populated/sld-battery-1440-mock.png) |
| sld | battery | 390 |  | True | 4.51 | Kobo mini-grid, What each part does | 92 | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-40, B1-41, B1-42, B1-43 | [app](populated/sld-battery-390-app.png) | [mock](populated/sld-battery-390-mock.png) |
| sld | unknown-part | 1440 |  | True | 2.23 | Kobo mini-grid, What each part does |  | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-40, B1-41, B1-42, B1-43 | [app](populated/sld-unknown-part-1440-app.png) | [mock](populated/sld-unknown-part-1440-mock.png) |
| sld | unknown-part | 390 |  | True | 3.84 | Kobo mini-grid, What each part does | 92 | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-40, B1-41, B1-42, B1-43 | [app](populated/sld-unknown-part-390-app.png) | [mock](populated/sld-unknown-part-390-mock.png) |
| changes | no-selection | 1440 |  | True | 0.3 |  |  | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-50, B1-55, B1-51, B1-52, B1-53, B1-54 | [app](populated/changes-no-selection-1440-app.png) | [mock](populated/changes-no-selection-1440-mock.png) |
| changes | no-selection | 390 |  | True | 0.27 |  | 165 | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-50, B1-55, B1-51, B1-52, B1-53, B1-54 | [app](populated/changes-no-selection-390-app.png) | [mock](populated/changes-no-selection-390-mock.png) |
| changes | unknown-id | 1440 |  | True | 0.3 |  |  | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-50, B1-55, B1-51, B1-52, B1-53, B1-54 | [app](populated/changes-unknown-id-1440-app.png) | [mock](populated/changes-unknown-id-1440-mock.png) |
| changes | unknown-id | 390 |  | True | 0.27 |  | 157 | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-50, B1-55, B1-51, B1-52, B1-53, B1-54 | [app](populated/changes-unknown-id-390-app.png) | [mock](populated/changes-unknown-id-390-mock.png) |
| asset | kobo001-battery | 1440 | yes | True | 1.25 |  |  | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-07, B1-60, B1-61, B1-62, B1-63, B1-64, B1-65, B1-66 | [app](populated/asset-kobo001-battery-1440-app.png) | [mock](populated/asset-kobo001-battery-1440-mock.png) |
| asset | kobo001-battery | 390 | yes | True | 1.31 | Interpretation and next evidence | 92 | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-07, B1-60, B1-61, B1-62, B1-63, B1-64, B1-65, B1-66 | [app](populated/asset-kobo001-battery-390-app.png) | [mock](populated/asset-kobo001-battery-390-mock.png) |
| asset | unknown-asset | 1440 |  | True | 0.4 |  |  | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-07, B1-60, B1-61, B1-62, B1-63, B1-64, B1-65, B1-66 | [app](populated/asset-unknown-asset-1440-app.png) | [mock](populated/asset-unknown-asset-1440-mock.png) |
| asset | unknown-asset | 390 |  | True | 0.46 |  | 92 | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-07, B1-60, B1-61, B1-62, B1-63, B1-64, B1-65, B1-66 | [app](populated/asset-unknown-asset-390-app.png) | [mock](populated/asset-unknown-asset-390-mock.png) |
| asset | unknown-site | 1440 |  | False | 0.33 |  |  | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-07, B1-60, B1-61, B1-62, B1-63, B1-64, B1-65, B1-66 | [app](populated/asset-unknown-site-1440-app.png) | [mock](populated/asset-unknown-site-1440-mock.png) |
| asset | unknown-site | 390 |  | False | 0.54 |  | 369 | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-07, B1-60, B1-61, B1-62, B1-63, B1-64, B1-65, B1-66 | [app](populated/asset-unknown-site-390-app.png) | [mock](populated/asset-unknown-site-390-mock.png) |
| sites | empty | 1440 |  | True | 0.9 |  |  | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-10, B1-11, B1-12, B1-13, B1-14, B1-15, B1-16 | [app](empty/sites-empty-1440-app.png) | [mock](empty/sites-empty-1440-mock.png) |
| sites | empty | 390 |  | True | 1.02 |  | 92 | B1-01, B1-03, B1-04, B1-05, B1-06, B1-07, B1-10, B1-11, B1-12, B1-13, B1-14, B1-15, B1-16 | [app](empty/sites-empty-390-app.png) | [mock](empty/sites-empty-390-mock.png) |
| changes | applied | 1440 | yes | True | 1.26 |  |  | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-50, B1-55, B1-51, B1-52, B1-53, B1-54 | [app](s601b/changes-applied-1440-app.png) | [mock](s601b/changes-applied-1440-mock.png) |
| changes | applied | 390 | yes | True | 1.34 | Change and effect | 92 | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-50, B1-55, B1-51, B1-52, B1-53, B1-54 | [app](s601b/changes-applied-390-app.png) | [mock](s601b/changes-applied-390-mock.png) |
| changes | no-selection-s601b | 1440 |  | True | 0.3 |  |  | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-50, B1-55, B1-51, B1-52, B1-53, B1-54 | [app](s601b/changes-no-selection-s601b-1440-app.png) | [mock](s601b/changes-no-selection-s601b-1440-mock.png) |
| changes | no-selection-s601b | 390 |  | True | 0.27 |  | 165 | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-50, B1-55, B1-51, B1-52, B1-53, B1-54 | [app](s601b/changes-no-selection-s601b-390-app.png) | [mock](s601b/changes-no-selection-s601b-390-mock.png) |
| asset | kobo001-s701 | 1440 |  | True | 1.25 |  |  | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-07, B1-60, B1-61, B1-62, B1-63, B1-64, B1-65, B1-66 | [app](s701/asset-kobo001-s701-1440-app.png) | [mock](s701/asset-kobo001-s701-1440-mock.png) |
| asset | kobo001-s701 | 390 |  | True | 1.31 | Interpretation and next evidence | 92 | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-07, B1-60, B1-61, B1-62, B1-63, B1-64, B1-65, B1-66 | [app](s701/asset-kobo001-s701-390-app.png) | [mock](s701/asset-kobo001-s701-390-mock.png) |
| asset | refusal-kobo002 | 1440 |  | True | 0.4 |  |  | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-07, B1-60, B1-61, B1-62, B1-63, B1-64, B1-65, B1-66 | [app](s701/asset-refusal-kobo002-1440-app.png) | [mock](s701/asset-refusal-kobo002-1440-mock.png) |
| asset | refusal-kobo002 | 390 |  | True | 0.46 |  | 92 | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-07, B1-60, B1-61, B1-62, B1-63, B1-64, B1-65, B1-66 | [app](s701/asset-refusal-kobo002-390-app.png) | [mock](s701/asset-refusal-kobo002-390-mock.png) |
| changes | effect | 1440 |  | True | 1.2 |  |  | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-50, B1-55, B1-51, B1-52, B1-53, B1-54 | [app](s602b/changes-effect-1440-app.png) | [mock](s602b/changes-effect-1440-mock.png) |
| changes | effect | 390 |  | True | 1.22 |  | 92 | B1-01, B1-02, B1-03, B1-04, B1-05, B1-06, B1-50, B1-55, B1-51, B1-52, B1-53, B1-54 | [app](s602b/changes-effect-390-app.png) | [mock](s602b/changes-effect-390-mock.png) |

## Differences and proposed dispositions

- **B1-01** (*): Mock topbar (org path 'Bineyame Operations / Demo estate', Find a screen, Site picker, Window picker, avatar) is absent on every screen at 1440 and 390.
  - PROPOSED: (b) candidate D1 shell row: no global search, user menu or shared topbar slot. R88/R112 cover only the Work-page Window control (cold/EV Work) and do not extend to these screens.
- **B1-02** (changes,asset): Short 390 pages: the dark mobile header band stretches to 165 px (changes no-selection), 157 px (changes unknown-id) and 369 px (asset unknown-site refusal), against 92 px on normal pages and no dark band in the mock (white topbar).
  - PROPOSED: (c) D3 shell defect = carried UI-pass item 'tall dark shell header on short 390 pages'. Shared shell fix owner.
- **B1-03** (*): At 390 the app shows a 92 px dark brand band with a Menu button where the mock shows a white topbar (org path, Site picker, Window, avatar) and hides the rail.
  - PROPOSED: (b) candidate D2 shell row (W1-F5a carry 5 phone Menu); no register row exists.
- **B1-04** (*): Rail: Assets and Settings show 'Not available yet' (mock live); mock rail footer 'Demo workspace / 3 sites - illustrative records' absent; 'Open Simulator Lab' vs mock 'Simulator Lab'.
  - PROPOSED: (b) candidate D1 for unmounted global Assets/Settings (relate to R09, which is maintenance-preventive only); footer = candidate D4 (illustrative count).
- **B1-05** (foundation,readiness,sld,changes,asset,sites): W1 state-line pattern: status strip carries version select, 'As of', 'How this was worked out', and panels close with 'Advanced details'/'Technical details' disclosures; mock strips are one line with no disclosures.
  - PROPOSED: (b) candidate D2 shell-pattern row (W1-UX provenance/state line, owner-accepted conditionally in W1); no Rxx exists.
- **B1-06** (readiness,sites,sld,changes,asset): Mock closes each page with a bordered info callout (11 px). App: readiness renders its closing note as an unboxed 14 px paragraph; sites, sld and changes have none; asset has a different callout ('Unknown here means...').
  - PROPOSED: readiness 14 px unboxed note: (c) D3 typography/structure (callout primitive exists). Missing sites/sld/changes callouts: (b) candidate D4 (mock texts assert illustrative facts: reporting dots, illustrative proposal). Asset: see B1-64.
- **B1-07** (sites,foundation,sld,asset,readiness): Body sentences render at 14 px against mock 11-12 px: sites empty (5 paragraphs at 14 px), foundation reserve-form intro, sld unknown-part notice, asset unknown-asset refusal text, readiness closing note. These screens use no `.prose` class; the one mock `.prose` (asset Interpretation lead, 12 px) is matched at 12 px.
  - PROPOSED: (c) D3 shared typography = carried UI-pass '.prose 14 px vs 12 px' item; shared typography fix owner.
- **B1-10** (sites): Sub-tab row Directory / Add site - form / From template / Batch upload / Setup history is absent; app shows a 'Create a site in the Simulator Lab' button instead, with no 'Not available yet' label.
  - PROPOSED: (b) candidate D1 (site-create-form/-template/-batch-upload/-setup-history are outside W1-W6). Unlabelled today, so it needs the visible label.
- **B1-11** (sites): Type chips: All sites, Mini-grid only (mock adds Cold-chain, EV charging).
  - PROPOSED: Value/data: the fixture stores only a mini-grid Site. If the chips are derived from stored types, there is no disposition. Architect to verify that they are data-derived; if they are fixed, candidate D4.
- **B1-12** (sites): Metric cards Needs attention and Evidence limited read 'Not available' with a reason, where the mock shows counts.
  - PROPOSED: (b) candidate D1 (no cross-site assessment/aggregation contract).
- **B1-13** (sites): Site inventory columns: mock Assessment / Top issue / Evidence / Last analysed are collapsed into one 'Operating view: Not available yet' column; app adds Setup details (disclosure) and Actions (View) columns and a footnote line.
  - PROPOSED: (b) candidate D1 for the four missing columns, plus candidate D2 for the added Setup details/Actions columns.
- **B1-14** (sites,foundation): Mode chip: app shows green 'Demonstration data' where the mock shows a neutral/purple 'Simulated' provenance chip. Green is the healthy/success tone.
  - PROPOSED: Wording: candidate D4. Tone: (c) D3 candidate (a provenance label uses a status-success tone; a neutral token exists).
- **B1-15** (sites): In setup: header buttons (+ Form, From template, Batch upload) absent; columns Created by / State / Next step / Created replaced by Lifecycle; closing 'Setup progress not available' line.
  - PROPOSED: (b) candidate D1 (no setup-progress read or create flows).
- **B1-16** (sites): Subtitle 'Every site configured in this build.' vs mock 'Find and compare sites across the operating estate'; mock root breadcrumb 'Sites >' above the h1 is absent.
  - PROPOSED: Subtitle: candidate D4. Breadcrumb: (c) minor D3 candidate (faithfully renderable).
- **B1-20** (foundation): Panel title 'Identity and operating obligations' vs mock 'Identity & operating obligations'. Approved in W1-F1, but there is no register row.
  - PROPOSED: (b) candidate D2 row (plain-language 'and').
- **B1-21** (foundation): Topology cards use paired icons and underlined part links where the mock has a single centred icon; the AC bus rule is blue in the app and green/teal in the mock.
  - PROPOSED: Links/icons: candidate D2 (part selection carries ?component to SLD/readiness). Bus colour: (c) D3 candidate (colour token mismatch).
- **B1-22** (foundation): Identity panel: 10 rows vs 6; values sit in a left-aligned second column without row rules (mock: right-aligned values with rules); monospace 'KOBO-001' wraps to 'KOBO-/001'. Topology panel is stretched to the same row height (1.50x at 1440).
  - PROPOSED: Rows: data (W1-F5b overage reason carried; needs a register ruling for >1.3x). KV alignment and code wrap: (c) D3 candidate.
- **B1-23** (foundation): Control table: 5 rows vs 4 (adds Critical service order); Evidence/change cells are plain text where the mock has links (Published policy, Review proposed change, Constraint evidence, See actual operation); one 'Open Dispatch' link exists.
  - PROPOSED: Extra row: data. Missing links: candidate D1 (no change list or constraint-evidence target).
- **B1-24** (foundation): The working 'Change the battery reserve' form (intro, two fields, Publish) and 'Advanced details' sit inside Time-valid control configuration, which is not drawn in the mock. Panel is 2.64x (1440) and 2.93x (390).
  - PROPOSED: (b) candidate D2 (S6 publish capability placed on Foundation) with a measured >1.3x reason. Needs a reviewed ruling.
- **B1-25** (foundation,readiness): No-version state (?at=2026-09-01): h1 shows the Site code 'KOBO-001' instead of the stored display name 'Kobo mini-grid', although the Site read returns display_name.
  - PROPOSED: (c) D3 candidate, pending an Architect check of whether the name must come from the Foundation version (then D1).
- **B1-30** (readiness): Panel title 'Gateway status - edge-kobo-001' vs mock 'GW-MG-01' (dynamic from the selected read; approved in W1-F1). No-version title 'Gateway status - No gateway selected'.
  - PROPOSED: (b) candidate D4 (illustrative gateway id replaced by the selected record).
- **B1-31** (readiness): Readiness table: last column 'Next step' vs mock 'Owner'; 6 areas vs 5, with different area names; three note lines and a disclosure under the table (1.63x/1.99x).
  - PROPOSED: 'Owner': candidate D1 (no owner field). Next step and notes: candidate D2. >1.3x carried W1-F5b reason needs a ruling.
- **B1-32** (readiness): Gateway panel: the contact timeline bar and legend are absent; Availability and Data completeness read 'Not available'; app adds a Registered gateway/Registration/Central contact block and a diagnostic disclosure (1.47x/1.55x).
  - PROPOSED: (b) candidate D1 (no uptime/completeness source) plus candidate D2 for the added block. Needs a ruling for >1.3x.
- **B1-40** (sld): Panel title 'Kobo mini-grid' with no '- AC-coupled mini-grid' suffix; the subtitle says 'Topology type not stated in this version'. The W1-F1 packet recorded the title '{site name} - {site type}'.
  - PROPOSED: (b) candidate D1 (topology type not declared in Foundation). Architect to check this against the W1-F1 approved title: if the type suffix regressed, it is a D3.
- **B1-41** (sld): Protection (CBs), feeder kWh meters, the Monitoring & communication row and reporting-status dots are absent; each part reads 'Readings not assessed here'; legend DC/AC/Fuel vs mock AC/DC/Monitoring/Circuit breaker/Reporting/Gap/Not connected.
  - PROPOSED: (b) candidate D1 for mini SLD (R36 is the EV-only analogue).
- **B1-42** (sld): 'What each part does' columns are Part / Type / Declared rating / Channels with 10 per-part rows, against mock Part / Role at this site / What it reports with 4 grouped rows.
  - PROPOSED: (b) candidate D1 (no role/reporting description stored) plus candidate D2 (per-part rows). Panel 2.23x at 1440, 1.95x at 390: measured reason is the 10 rows plus the intro and disclosure; needs a ruling.
- **B1-43** (sld): Diagram panel is 1.63x/1.84x at 1440 and 3.84x/4.51x at 390. At 390 the app keeps the drawing full size in an inner horizontal scroller (952 px in 316 px), while the mock scales the diagram down to 318 px tall.
  - PROPOSED: Needs a reviewed ruling: candidate D2 (readability) or, if scale-to-fit is the faithful alternative, (c) D3. Measured reason: 9 parts in 4 rows plus a selected-part box and notes.
- **B1-50** (changes): RESOLVED (fully) under the owner's producer scratch-DB authorization (2026-10-24): the unmodified s601b producer (assetops_s601b_audit) gave changes:applied, and the unmodified s602b producer (assetops_s602b_audit; replay API on 18101, its TEST-SCOPED API on the authorised 18102) gave changes:effect, each at 1440 and 390.
  - PROPOSED: Resolved; no blocker remains.
- **B1-55** (changes): Effect state: the Target and Guardrails cards read 'Set in the plan' (with 'Frozen before the later window is judged' / 'Service, reserve and stored-energy limits') where the mock shows the values ('>=25% lower', '3 required'), although a frozen plan exists (step 1 links 'Inspect plan'). The 'Battery <uuid>' raw ID (B1-53) also appears here; there are no failed-attempt codes. Panel 1.20x/1.22x.
  - PROPOSED: (c) D3 candidate if the change read carries the frozen plan target/guardrail count; otherwise candidate D1 (plan values are not on the change DTO). Architect to check the DTO.
- **B1-51** (changes): No-selection and unknown-ID states: an amber notice 'No change selected... no list of Foundation changes yet' and two panels with one-line gap statements; the mock has a strip, 4 KPI cards, a before/proposed table, decision steps and a callout. Panel titles and order match (2/2).
  - PROPOSED: (b) candidate D1 (no Foundation change list); honest missing state.
- **B1-60** (asset): Asset-rooted chrome absent: the mock has the Assets rail entry active, breadcrumb Assets > BAT-001 > Health, asset tabs (Overview, Health, Performance, Configuration, Work, Evidence, Warranty) and an 'Open site' button. The app is Site-rooted (Sites active, Site tabs, breadcrumb Sites / Kobo mini-grid / Health / Battery).
  - PROPOSED: (b) candidate D1 (asset-* screens are outside W1-W6).
- **B1-61** (asset): Panel 3 title 'Condition evidence and its limits' vs mock 'Condition evidence and claim boundary'.
  - PROPOSED: (b) candidate D2 (client-facing plain language); no register row.
- **B1-62** (asset): Reserve exposure and Power stress read 'Not available'; the weekly breach bars are absent (a KV list stands in); KPI top-border tones are absent.
  - PROPOSED: (b) candidate D1 (no accepted SOC/power history on this page).
- **B1-63** (asset): Interpretation: 3 numbered missing inputs vs 2 actions; 'Create test action' and 'Review capability gap' links absent (capacity-test action stated unavailable). 1.31x at 390.
  - PROPOSED: (b) candidate D1. The ~1.31x carries the W1-F5b reason and needs a ruling.
- **B1-64** (asset): Warranty callout replaced by 'Unknown here means not yet measurable... Back to Health'; 'Technical details' disclosure added.
  - PROPOSED: Warranty: candidate D1. Disclosure: covered by B1-05 D2.
- **B1-65** (asset): h1 'Battery energy storage' (Foundation display name) vs 'Kobo battery'; subtitle has no asset code (mock BAT-001).
  - PROPOSED: (b) candidate D4 (illustrative name/code).
- **B1-66** (asset): Refusals: the W1-F5b 3-slot refusal (s701, stored KOBO-002 with no battery) is now captured. The three panel titles match the mock, with one-sentence gap statements at 14 px (B1-07) and the generic h1 'Battery'. Unknown asset on KOBO-001 gives the same 3-slot pattern. Unknown Site gives 'Site not found' / 'No such site' (1 panel vs mock 3) with the 369 px band at 390 (B1-02). The s701 battery capture equals the v01a one (same panel heights).
  - PROPOSED: Refusal structure: existing W1-F5b accepted pattern (no Rxx). Architect to confirm or register it. Generic h1 'Battery' on refusal: candidate D4.
- **B1-52** (changes): Applied state: table header 'After' vs mock 'Proposed'; 2 rows (Battery reserve, Foundation version) vs 4; the Target and Guardrails cards read 'Not recorded yet' and Outcome reads 'No verification plan yet'; Decision path step 1 has no 'Inspect plan' link ('Not recorded yet') and step 2 adds 'Application record'. Panel 1.26x (1440) and 1.34x (390).
  - PROPOSED: Header: candidate D4 (state-correct label for an applied change). Cards/links: candidate D1 (no frozen plan in this record). 1.34x at 390: carried W1-F5b reason (outcome/applied-by rows, failed attempts, disclosure); needs a ruling.
- **B1-53** (changes): Applied state shows raw system vocabulary: a battery asset UUID in monospace ('Battery 2deeca26-...') and failure codes ACTION_FOUNDATION_STALE, ACTION_VALUE_INVALID and ACTION_EFFECTIVE_TIME_INVALID in the 'earlier attempts' line.
  - PROPOSED: (c) D3 candidate (client-facing copy: no system vocabulary; the plain-language mapping is renderable). Shared copy fix owner, like the carried raw 'c1 - EV_CONNECTOR' label.
- **B1-54** (changes): Breadcrumb leaf is 'Change' on the applied state and 'Change & effect' on the bare page; mock 'Sites > Kobo Mini-grid > Foundation'. The page-end note is a left-bar 13 px note against the mock's boxed 11 px info callout.
  - PROPOSED: Breadcrumb: (c) minor D3 candidate (inconsistent leaf). Note style/size: part of B1-06/B1-07.

## Carried checks

- prose_14_vs_12: Observed: 14 px body sentences on sites-empty, foundation form intro, sld unknown-part, asset unknown-asset, readiness closing note (B1-07). Asset `.prose` lead matches at 12 px.
- tall_dark_header_390: Observed: 165/157 px (changes), 369 px (asset unknown-site refusal) vs 92 normal (B1-02).
- plural_1_incidents: Not applicable: no count+noun copy on these screens.
- raw_EV_CONNECTOR_label: Not applicable: mini Site only.
- domainActionClient_generic_window_error: Not applicable: no domain-action window inputs on these screens; the Foundation reserve form was not submitted (capture-only).
- R88_R112_window_control: Not applicable: no Window control on these screens.

## Existing D3 rows (R22/R23/R24/R37/R38/R60)

- R22: cold-health; not on batch-01 screens
- R23: cold-work-incidents; not on batch-01 screens
- R24: ev-work-incidents; not on batch-01 screens
- R37: cold-performance; not on batch-01 screens
- R38: cold-evidence-analysis; not on batch-01 screens
- R60: ev-health; not on batch-01 screens

## Notes

- Typography and colour samples (h1/h2/td/th/body family, size, weight, line-height, colour; panel bg/border/radius; rail colour) are equal between app and mock on all pairs: h1 27/23 px, weight 650; h2 15 px, weight 650, rgb(23,36,59); td 11 px system-ui; rail rgb(22,35,63). The differences are listed above.
- Page overflow-x is 0 on all pairs. Inner scrollers at 390: the Site tab list (521 in 358), data tables, and the SLD drawing (952 in 316).
- Clipped-text candidates are visually-hidden labels and select text only, not clipped material text.
- W1-F5b overage reasons (`.agent/W1-F5b-evidence/overages.json`) still describe the >1.3x panels, but no register row rules on them. The spec requires a reviewed ruling.
- The time-dependent label in `v01a_foundation_walkthrough.py` ('Scheduled period v13 ... not in effect yet') is stale: since 21 Oct 2026, v13 is the period in effect. That is why the scheduled case was replaced by `imported-period` (?at=2026-09-30).
